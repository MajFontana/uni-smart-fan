import json
import datetime

class SmartFanStatus:
    def __init__(self):
        self.temperature = 21
        self.fan_active = False
        self.last_connected = datetime.datetime.now()
        self.configuration = SmartFanConfiguration()
    def getData(self):
        seconds_since_last_connection = (datetime.datetime.now() - self.last_connected).total_seconds()
        data = {
            "temperature": self.temperature,
            "fan_active": self.fan_active,
            "seconds_since_last_connection": seconds_since_last_connection,
            "configuration": self.configuration.getData()}
        return data
    def loadData(self, data):
        self.last_connected = datetime.datetime.now()
        self.temperature = data["temperature"]
        self.fan_active = data["fan_active"]
        self.configuration.loadData(data["configuration"])
    def toJson(self):
        return json.dumps(self.getData())
    def loadJson(self, raw):
        data = json.loads(raw)
        self.loadData(data)

class SmartFanConfiguration:
    def __init__(self):
        self.target_temperature = 21
        self.fan_enabled = False
    def getData(self):
        data = {
            "target_temperature": self.target_temperature,
            "fan_enabled": self.fan_enabled
            }
        return data
    def loadData(self, data):
        self.target_temperature = data["target_temperature"]
        self.fan_enabled = data["fan_enabled"]
    def toJson(self):
        return json.dumps(self.getData())
    def loadJson(self, raw):
        data = json.loads(raw)
        self.loadData(data)