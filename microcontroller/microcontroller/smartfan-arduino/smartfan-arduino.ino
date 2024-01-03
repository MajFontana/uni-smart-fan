#include <M5Stack.h>
#include <WiFi.h>
#include "SHTSensor.h"
#include <VL53L0X.h>
#include <ArduinoJson.h>
#include <HTTPClient.h>



struct Status{
  float temperature;
  bool userPresent;
  bool fanRunning;
};

struct Settings{
  float targetTemperature;
  bool fanEnabled;
};



class Schedule{
  public:
    double period;
    double lastTime;

    void setPeriod(double period){
      this->period = period;
      lastTime = millis() / 1000.0;
    }

    bool poll(){
      double currentTime = millis() / 1000.0;
      if (currentTime >= lastTime + period){
        lastTime = currentTime + period;
        return true;
      }
      else{
        return false;
      }
    }
};



HTTPClient httpClient;

SHTSensor sht30(SHTSensor::SHT3X); // temperature sensor
VL53L0X vl53l0x; // time of flight sensor

struct Settings* settings = new Settings{};
struct Status* status = new Status{};

Schedule statusUpdateSchedule;
Schedule controlSchedule;
Schedule networkSyncSchedule;
Schedule wifiCheckSchedule;



// WiFi settings 
char * WIFI_SSID = "SSID";
char * WIFI_PASSWORD = "PASS";

// API settings
String API_BASE_URL = "http://lair.pythonanywhere.com/feri-is/smart-fan/";
String API_STATUS_ENDPOINT = "device/";
String API_SETTINGS_ENDPOINT = "device/configure/";
String API_AUTH_KEY = "efgh";

// device settings
int RELAY_PIN = 26;

// app setings
double TARGET_TEMPERATURE_HYSTERESIS = 0.2;
double USER_PRESENT_THRESHOLD_DISTANCE = 0.3;
double MAIN_LOOP_PERIOD = 0.1;
double STATUS_UPDATE_PERIOD = 1.0;
double CONTROL_PERIOD = 1.0;
double NETWORK_SYNC_PERIOD = 1.0;
double WIFI_CHECK_PERIOD = 5.0;



void makeHttpPostRequest(String url, String payload){
  httpClient.begin(url);
  httpClient.addHeader("Content-Type", "application/x-www-form-urlencoded");
  httpClient.addHeader("X-Api-Key", API_AUTH_KEY);
  int responseCode = httpClient.POST(payload);
  
  if(responseCode != 200 and responseCode > 0) {
      Serial.println("HTTP request error");
  }
  else if (responseCode <= 0){
    Serial.println("Connection error");
  }

  httpClient.end();
}

String makeHttpGetRequest(String url){
  String payload = "";
  
  httpClient.begin(url);
  httpClient.addHeader("Content-Type", "application/x-www-form-urlencoded");
  httpClient.addHeader("X-Api-Key", API_AUTH_KEY);
  int responseCode = httpClient.GET();
  
  if(responseCode == 200) {
    payload = httpClient.getString();
  }
  else if(responseCode != 200 and responseCode > 0) {
      Serial.println("HTTP request error");
  }
  else if (responseCode <= 0){
    Serial.println("Connection error");
  }

  httpClient.end();

  return payload;
}

int networkSendStatus(struct Status* status, struct Settings* settings){
  String url = API_BASE_URL + API_STATUS_ENDPOINT;
  
  String payload;
  DynamicJsonDocument doc(1024);
  doc["temperature"] = status->temperature;
  doc["fan_active"] = status->fanRunning;
  doc["configuration"]["target_temperature"] = settings->targetTemperature;
  doc["configuration"]["fan_enabled"] = settings->fanEnabled;
  serializeJson(doc, payload);

  makeHttpPostRequest(url, payload);
}

void networkReceiveSettings(struct Settings* settings){
  String url = API_BASE_URL + API_SETTINGS_ENDPOINT;

  String payload = makeHttpGetRequest(url);

  if (payload.length() > 0){
    DynamicJsonDocument doc(1024);
    deserializeJson(doc, payload);
    settings->targetTemperature = doc["target_temperature"];
    settings->fanEnabled = doc["fan_enabled"];
  }
}



void updateStatusTemperature(struct Status* status){
  if (sht30.readSample()){
    status->temperature = sht30.getTemperature();
  }
  else{
    Serial.println("Temperature sensor read error");
    return;
  }
}

void updateStatusUserPresent(struct Status* status){
  double distance = vl53l0x.readRangeSingleMillimeters() / 1000.0;
  
  if (vl53l0x.timeoutOccurred()){
    Serial.println("Time of flight sensor read timeout");
    return;
  }

  if (status->userPresent){
    if (distance > USER_PRESENT_THRESHOLD_DISTANCE){
      status->userPresent = false;
    }
  }
  else{
    if (distance < USER_PRESENT_THRESHOLD_DISTANCE){
      status->userPresent = true;
    }
  }
  
}

void updateDeviceRelay(struct Status* status){
  if (status->fanRunning){
    digitalWrite(RELAY_PIN, HIGH);
  }
  else{
    digitalWrite(RELAY_PIN, LOW);
  }
}

void updateLogicFan(struct Status* status, struct Settings* settings){
  if (settings->fanEnabled){
    if (status->userPresent){
      if (status->fanRunning){
        if (status->temperature < settings->targetTemperature - TARGET_TEMPERATURE_HYSTERESIS / 2){
          status->fanRunning = false;
        }
      }
      else{
        if (status->temperature > settings->targetTemperature + TARGET_TEMPERATURE_HYSTERESIS / 2){
          status->fanRunning = true;
        }
      }
    }
    else{
      status->fanRunning = false;
    }
  }
  else{
    status->fanRunning = false;
  }
}



void setup() {
  // initialize M5 stack
  M5.begin();
  M5.Power.begin();

  // initialize relay
  pinMode(RELAY_PIN, OUTPUT);

  // initialize temperature sensor
  if (!sht30.init()){
    Serial.print("Temperature sensor initialization error");
  }

  // initialize time of flight sensor
  vl53l0x.setTimeout(500);
  if (!vl53l0x.init())
  {
    Serial.println("Time of flight sensor initialization error");
  }

  // initialize settings
  settings->targetTemperature = 21.0;
  settings->fanEnabled = true;

  // initialize status
  status->fanRunning = false;
  updateStatusTemperature(status);
  updateStatusUserPresent(status);

  // Connect to wifi
  wifiCheckSchedule.setPeriod(WIFI_CHECK_PERIOD);
  Serial.println("Connecting to WiFi ...");
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  while (WiFi.status() != WL_CONNECTED) 
  {
    if (wifiCheckSchedule.poll()){
      WiFi.disconnect();
      WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    }
    delay(MAIN_LOOP_PERIOD * 1000);
  }
  Serial.println("Connection successful");

  // Sync device state with API
  networkReceiveSettings(settings);
  networkSendStatus(status, settings);

  // schedule tasks
  statusUpdateSchedule.setPeriod(STATUS_UPDATE_PERIOD);
  controlSchedule.setPeriod(CONTROL_PERIOD);
  networkSyncSchedule.setPeriod(NETWORK_SYNC_PERIOD);
}

void loop(void) {
  if (statusUpdateSchedule.poll()){
    updateStatusTemperature(status);
    updateStatusUserPresent(status);
  }

  if (controlSchedule.poll()){
    updateLogicFan(status, settings);
    updateDeviceRelay(status);
  }

  if (networkSyncSchedule.poll()){
    networkReceiveSettings(settings);
    networkSendStatus(status, settings);
  }

  if (wifiCheckSchedule.poll()){
    if (WiFi.status() != WL_CONNECTED){
      WiFi.reconnect();
    }
  }
  
  delay(MAIN_LOOP_PERIOD * 1000);
}
