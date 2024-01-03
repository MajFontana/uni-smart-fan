import flask

class SmartFanWebApp:
    def __init__(self):

        self.blueprint = flask.Blueprint('smart_fan_webapp', __name__, template_folder='templates/')

        @self.blueprint.route("/feri-is/smart-fan/dashboard/", methods=["GET"])
        def feriIs_smartFan_dashboard():
            return flask.render_template("smartFanWebApp.html")
