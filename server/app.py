import flask
import flask_cors



app = flask.Flask(__name__)

cors = flask_cors.CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'



from smart_fan import smart_fan_webapi, smart_fan_webapp, smart_fan

configuration = smart_fan.SmartFanConfiguration()
status = smart_fan.SmartFanStatus()
webapi = smart_fan_webapi.SmartFanWebApi(status, configuration)
webapp = smart_fan_webapp.SmartFanWebApp()
app.register_blueprint(webapi.blueprint)
app.register_blueprint(webapp.blueprint)
