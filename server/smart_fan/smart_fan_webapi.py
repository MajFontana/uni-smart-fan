import flask
import flask_cors
from feri_is import authorization

class SmartFanWebApi:
    def __init__(self, status, configuration):

        self.blueprint = flask.Blueprint('smart_fan_webapi', __name__)

        @self.blueprint.route("/feri-is/smart-fan/device/", methods=["GET", "POST"])
        @flask_cors.cross_origin()
        def feriIs_smartFan_device():
            auth = flask.request.headers.get("X-Api-Key")
            if flask.request.method == "GET":
                if authorization.AUTH_READ_STATUS in authorization.getAuthorization(auth):
                    return status.toJson(), 200
                else:
                    return "", 401
            elif flask.request.method == "POST":
                if authorization.AUTH_MODIFY_STATUS in authorization.getAuthorization(auth):
                    status.loadJson(flask.request.get_data(as_text=True))
                    return "", 200
                else:
                    return "", 401

        @self.blueprint.route("/feri-is/smart-fan/device/configure/", methods=["GET", "POST"])
        @flask_cors.cross_origin()
        def feriIs_smartFan_device_configure():
            auth = flask.request.headers.get("X-Api-Key")
            if flask.request.method == "GET":
                if authorization.AUTH_READ_CONFIG in authorization.getAuthorization(auth):
                    return configuration.toJson(), 200
                else:
                    return "", 401
            elif flask.request.method == "POST":
                if authorization.AUTH_MODIFY_CONFIG in authorization.getAuthorization(auth):
                    configuration.loadJson(flask.request.get_data(as_text=True))
                    return "", 200
                else:
                    return "", 401
