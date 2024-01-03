class SmartFanView{

    constructor(id){
        this.UI = document.getElementById(id);
        var overlay = this.UI.getElementsByClassName("smartfan-ui-overlay")[0];
        this.overlayDefaultDisplay = overlay.style.display;
    }

    setMainControlsEnableState(state){
        var indicatorOn = this.UI.getElementsByClassName("smartfan-ui-main-controls-enable-indicator-on")[0];
        var indicatorOff = this.UI.getElementsByClassName("smartfan-ui-main-controls-enable-indicator-off")[0];
        if (state){
            indicatorOff.style.display = "none";
            indicatorOn.style.display = "block";
        }
        else{
            indicatorOn.style.display = "none";
            indicatorOff.style.display = "block";
        }
    }

    setMainControlsTemperatureDisplayValue(value){
        var text = Math.floor(value).toString().padStart(2, "0");
        var display = this.UI.getElementsByClassName("smartfan-ui-main-controls-temperature-display")[0];
        display.textContent = text;
    }

    setMainStatusFanState(state){
        var iconOn = this.UI.getElementsByClassName("smartfan-ui-main-status-fan-icon-on")[0];
        var iconOff = this.UI.getElementsByClassName("smartfan-ui-main-status-fan-icon-off")[0];
        if (state){
            iconOff.style.display = "none";
            iconOn.style.display = "block";
        }
        else{
            iconOn.style.display = "none";
            iconOff.style.display = "block";
        }
    }

    setMainStatusTemperatureDisplayValue(value){
        var text = (Math.round(value * 10) / 10).toFixed(1)
        var display = this.UI.getElementsByClassName("smartfan-ui-main-status-temperature-display")[0];
        display.textContent = text;
    }

    setOverlayVisible(visible){
        var overlay = this.UI.getElementsByClassName("smartfan-ui-overlay")[0];
        if (visible){
            overlay.style.display = this.overlayDefaultDisplay;
            overlay.classList.remove("smartfan-ui-overlay-fade-out");
            overlay.classList.add("smartfan-ui-overlay-fade-in");
            overlay.onanimationend = function(event){};
        }
        else{
            overlay.classList.remove("smartfan-ui-overlay-fade-in");
            overlay.classList.add("smartfan-ui-overlay-fade-out");
            overlay.onanimationend = function(event){
                overlay.style.display = "none";
            };
        }
    }

    setMainControlsEnableOnClick(func){
        var button = this.UI.getElementsByClassName("smartfan-ui-main-controls-enable")[0];
        button.onclick = func;
    }

    setMainControlsTemperatureButtonsIncreaseOnClick(func){
        var button = this.UI.getElementsByClassName("smartfan-ui-main-controls-temperature-buttons-increase")[0];
        button.onclick = func;
    }

    setMainControlsTemperatureButtonsDecreaseOnClick(func){
        var button = this.UI.getElementsByClassName("smartfan-ui-main-controls-temperature-buttons-decrease")[0];
        button.onclick = func;
    }
}



class SmartFanBlinker{

    constructor(setFunction, frequency){
        this.setFunction = setFunction;
        this.frequency = frequency
        this.interval = null;
        this.state = false;
        this.isBlinking = false;
    }

    start(state){
        this.state = !state;
        this.tick();
        this.interval = setInterval(this.tick.bind(this), 1000 / (this.frequency * 2));
        this.isBlinking = true;
    }

    stop(){
        if(this.interval != null){
            clearInterval(this.interval);
            this.interval = null;
            this.isBlinking = false;
        }
    }

    tick(){
        this.state = !this.state;
        this.setFunction(this.state);
    }

}



class SmartFanData{

    static BASE_URL = "https://lair.pythonanywhere.com/feri-is/smart-fan/";

    constructor(authorizationKey){
        this.authorizationKey = authorizationKey;
        this.configuration = null;
        this.status = null;
        this.onConfigurationUpdate = function(){};
        this.onStatusUpdate = function(){};
    }

    loadConfiguration(){
        var httpRequest = new XMLHttpRequest();
        var url = SmartFanData.BASE_URL + "device/configure/";
        httpRequest.open('GET', url, true);

        httpRequest.setRequestHeader('Content-type', 'application/x-www-form-urlencoded');
        httpRequest.setRequestHeader("X-Api-Key", this.authorizationKey)

        httpRequest.onreadystatechange = (function(){
            if(httpRequest.readyState == 4 && httpRequest.status == 200) {
                var payload = httpRequest.responseText;
                this.configuration = JSON.parse(payload);
                this.onConfigurationUpdate();
            }
        }).bind(this);
        httpRequest.send();
    }

    loadStatus(){
        var httpRequest = new XMLHttpRequest();
        var url = SmartFanData.BASE_URL + "device/";
        httpRequest.open('GET', url, true);

        httpRequest.setRequestHeader('Content-type', 'application/x-www-form-urlencoded');
        httpRequest.setRequestHeader("X-Api-Key", this.authorizationKey)

        httpRequest.onreadystatechange = (function() {
            if(httpRequest.readyState == 4 && httpRequest.status == 200) {
                var payload = httpRequest.responseText;
                this.status = JSON.parse(payload);
                this.onStatusUpdate();
            }
        }).bind(this);
        httpRequest.send();
    }

    updateConfiguration(){
        if (this.configuration != null){
            var payload = JSON.stringify(this.configuration);

            var httpRequest = new XMLHttpRequest();
            var url = SmartFanData.BASE_URL + "device/configure/";
            httpRequest.open('POST', url, true);

            httpRequest.setRequestHeader('Content-type', 'application/x-www-form-urlencoded');
            httpRequest.setRequestHeader("X-Api-Key", this.authorizationKey)

            httpRequest.onreadystatechange = function() {
                if(httpRequest.readyState == 4 && httpRequest.status == 200) {
                }
            }
            httpRequest.send(payload);
        }
    }

}



class SmartFanUI{

    static ENABLE_STATE_BLINKER_FREQUENCY = 1;
    static STATUS_UPDATE_PERIOD = 1;

    constructor(view, data){
        this.view = view;
        this.data = data;
        this.enableStateBlinker = new SmartFanBlinker(this.view.setMainControlsEnableState.bind(view), SmartFanUI.ENABLE_STATE_BLINKER_FREQUENCY);

        this.frozenConfiguration = null;
        this.useFrozenConfiguration = false;
        this.frozenConfigurationTimeout = null;

        this.data.onConfigurationUpdate = (function(){
            var targetTemperature = this.getConfiguration().target_temperature;
            this.view.setMainControlsTemperatureDisplayValue(targetTemperature);

            var enable = this.getConfiguration().fan_enabled;
            if (this.data.status != null){
                var trueEnable = this.data.status.configuration.fan_enabled;
                if (trueEnable == enable){
                    this.enableStateBlinker.stop();
                    this.view.setMainControlsEnableState(enable);
                }
                else{
                    if(!this.enableStateBlinker.isBlinking){
                        this.enableStateBlinker.start(enable);
                    }
                }
            }
            else{
                this.view.setMainControlsEnableState(enable);
            }
        }).bind(this);

        this.data.onStatusUpdate = (function(){
            var temperature = this.data.status.temperature;
            this.view.setMainStatusTemperatureDisplayValue(temperature);

            var active = this.data.status.fan_active;
            this.view.setMainStatusFanState(active);

            var trueEnable = this.data.status.configuration.fan_enabled;
            if (this.getConfiguration() != null){
                var enable = this.getConfiguration().fan_enabled;
                if (trueEnable == enable){
                    this.enableStateBlinker.stop();
                    this.view.setMainControlsEnableState(enable);
                }
                else{
                    if(!this.enableStateBlinker.isBlinking){
                        this.enableStateBlinker.start(enable);
                    }
                }
            }
            else{
                this.view.setMainControlsEnableState(trueEnable);
            }

            var connectionAge = this.data.status.seconds_since_last_connection;
            if (connectionAge > 10 && this.getConfiguration() != null){
                this.view.setOverlayVisible(true);
            }
            else{
                this.view.setOverlayVisible(false);
            }
        }).bind(this);

        this.view.setMainControlsTemperatureButtonsIncreaseOnClick((function(){
            if (this.getConfiguration().target_temperature < 50){
                this.data.configuration.target_temperature = ++this.getConfiguration().target_temperature;
                this.data.onConfigurationUpdate();
                this.data.updateConfiguration();
                this.freezeConfiguration(SmartFanUI.STATUS_UPDATE_PERIOD);
            }
        }).bind(this));

        this.view.setMainControlsTemperatureButtonsDecreaseOnClick((function(){
            if (this.getConfiguration().target_temperature > 0){
                this.data.configuration.target_temperature = --this.getConfiguration().target_temperature;
                this.data.onConfigurationUpdate();
                this.data.updateConfiguration();
                this.freezeConfiguration(SmartFanUI.STATUS_UPDATE_PERIOD);
            }
        }).bind(this));

        this.view.setMainControlsEnableOnClick((function(){
            this.getConfiguration().fan_enabled = !this.getConfiguration().fan_enabled;
            this.data.configuration.fan_enabled = this.getConfiguration().fan_enabled;
            this.data.onConfigurationUpdate();
            this.data.updateConfiguration();
            this.freezeConfiguration(SmartFanUI.STATUS_UPDATE_PERIOD);
        }).bind(this));

        this.data.loadConfiguration();
        this.data.loadStatus();
        setInterval((function(){
            this.data.loadConfiguration();
            this.data.loadStatus();
        }).bind(this), 1000 / SmartFanUI.STATUS_UPDATE_PERIOD);
    }

    freezeConfiguration(duration){
        this.frozenConfiguration = this.data.configuration;
        this.useFrozenConfiguration = true;
        clearTimeout(this.frozenConfigurationTimeout);
        this.frozenConfigurationTimeout = setTimeout((function(){
            this.useFrozenConfiguration = false;
        }).bind(this), duration * 1000);
    }

    getConfiguration(){
        if (this.useFrozenConfiguration){
            return this.frozenConfiguration;
        }
        else{
            return this.data.configuration;
        }
    }

}