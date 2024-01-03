import time
import requests
import json



class SHT3X:

    def init(self):
        return True

    def readSample(self):
        return True

    def getTemperature(self):
        return 22.3

class VL53L0X:

    def init(self):
        return True

    def readRangeSingleMillimeters(self):
        return 5

    def setTimeout(self, duration):
        pass

    def timeoutOccurred(self):
        return False

def millis():
    return time.time() * 1000

LOW = False
HIGH = True

def digitalWrite(pin, state):
    if state:
        print("[Pin", pin, "set HIGH]")
    else:
        print("[Pin", pin, "set LOW]")

def delay(duration):
    time.sleep(duration / 1000)



class Status:
    
    def __init__(self):
        self.temperature = None
        self.userPresent = None
        self.fanRunning = None

class Settings:
    
    def __init__(self):
        self.targetTemperature = None
        self.fanEnabled = None



class Schedule:
    
    def __init(self):
        self.period = None
        self.lastTime = None

    def setPeriod(self, period):
        self.period = period
        self.lastTime = millis() / 1000.0

    def poll(self):
        currentTime = millis() / 1000.0
        if currentTime >= self.lastTime + self.period:
            self.lastTime = currentTime + self.period
            return True
        else:
            return False



sht30 = SHT3X() # temperature sensor
vl53l0x = VL53L0X() # time of flight sensor

settings = Settings()
status = Status()

statusUpdateSchedule = Schedule()
controlSchedule = Schedule()
networkSyncSchedule = Schedule()
wifiCheckSchedule = Schedule()



# API settings
API_BASE_URL = "http://lair.pythonanywhere.com/feri-is/smart-fan/";
API_STATUS_ENDPOINT = "device/";
API_SETTINGS_ENDPOINT = "device/configure/";
API_AUTH_KEY = "abcd";

# device settings
RELAY_PIN = 26;

# app setings
TARGET_TEMPERATURE_HYSTERESIS = 0.2;
USER_PRESENT_THRESHOLD_DISTANCE = 0.3;
MAIN_LOOP_PERIOD = 0.1;
STATUS_UPDATE_PERIOD = 1.0;
CONTROL_PERIOD = 1.0;
NETWORK_SYNC_PERIOD = 1.0;
WIFI_CHECK_PERIOD = 5.0;



def makeHttpPostRequest(url, payload):
    headers = {}
    headers["Content-Type"] = "application/x-www-form-urlencoded"
    headers["X-Api-Key"] = API_AUTH_KEY
    responseCode = requests.post(url, headers=headers, data=payload).status_code
  
    if responseCode != 200:
        print("HTTP request error")
    elif False:
        print("Connection error")

def makeHttpGetRequest(url):
    payload = ""
    
    headers = {}
    headers["Content-Type"] = "application/x-www-form-urlencoded"
    headers["X-Api-Key"] = API_AUTH_KEY
    response = requests.get(url, headers=headers)
    responseCode = response.status_code

    if responseCode == 200:
        payload = response.text
    elif responseCode != 200:
        print("HTTP request error")
    elif False:
        print("Connection error")

    return payload

def networkSendStatus(status, settings):
    url = API_BASE_URL + API_STATUS_ENDPOINT
  
    doc = {}
    doc["temperature"] = status.temperature
    doc["fan_active"] = status.fanRunning
    doc["configuration"] = {}
    doc["configuration"]["target_temperature"] = settings.targetTemperature
    doc["configuration"]["fan_enabled"] = settings.fanEnabled
    payload = json.dumps(doc)

    makeHttpPostRequest(url, payload)

def networkReceiveSettings(settings):
    url = API_BASE_URL + API_SETTINGS_ENDPOINT

    payload = makeHttpGetRequest(url)

    if len(payload) > 0:
        doc = json.loads(payload)
        settings.targetTemperature = doc["target_temperature"]
        settings.fanEnabled = doc["fan_enabled"]



def updateStatusTemperature(status):
    if sht30.readSample():
        status.temperature = sht30.getTemperature()
    else:
        print("Temperature sensor read error")

def updateStatusUserPresent(status):
    distance = vl53l0x.readRangeSingleMillimeters() / 1000.0
  
    if vl53l0x.timeoutOccurred():
        print("Time of flight sensor read timeout")
        return

    if status.userPresent:
        if distance > USER_PRESENT_THRESHOLD_DISTANCE:
            status.userPresent = False
    else:
        if distance < USER_PRESENT_THRESHOLD_DISTANCE:
            status.userPresent = True;

def updateDeviceRelay(status):
    if status.fanRunning:
        digitalWrite(RELAY_PIN, HIGH)
    else:
        digitalWrite(RELAY_PIN, LOW)

def updateLogicFan(status, settings):
    if settings.fanEnabled:
        if status.userPresent:
            if status.fanRunning:
                if status.temperature < settings.targetTemperature - TARGET_TEMPERATURE_HYSTERESIS / 2:
                    status.fanRunning = False
            else:
                if status.temperature > settings.targetTemperature + TARGET_TEMPERATURE_HYSTERESIS / 2:
                    status.fanRunning = True
        else:
            status.fanRunning = False
    else:
        status.fanRunning = False



def setup():
    # initialize temperature sensor
    if not sht30.init():
        print("Temperature sensor initialization error")

    # initialize time of flight sensor
    vl53l0x.setTimeout(500)
    if not vl53l0x.init():
        print("Time of flight sensor initialization error")

    # initialize settings
    settings.targetTemperature = 21.0
    settings.fanEnabled = True

    # initialize status
    status.fanRunning = False
    updateStatusTemperature(status)
    updateStatusUserPresent(status)

    # Connect to wifi
    wifiCheckSchedule.setPeriod(WIFI_CHECK_PERIOD)
    print("Connecting to WiFi ...")
    print("Connection successful")

    # Sync device state with API
    networkReceiveSettings(settings)
    networkSendStatus(status, settings)

    # schedule tasks
    statusUpdateSchedule.setPeriod(STATUS_UPDATE_PERIOD)
    controlSchedule.setPeriod(CONTROL_PERIOD)
    networkSyncSchedule.setPeriod(NETWORK_SYNC_PERIOD)

def loop():
    if statusUpdateSchedule.poll():
        updateStatusTemperature(status)
        updateStatusUserPresent(status)

    if controlSchedule.poll():
        updateLogicFan(status, settings)
        updateDeviceRelay(status)

    if networkSyncSchedule.poll():
        networkReceiveSettings(settings)
        networkSendStatus(status, settings)

    wifiCheckSchedule.poll()
  
    delay(MAIN_LOOP_PERIOD * 1000)

setup()
while True:
    loop()
