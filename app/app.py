from flask import Flask
from flask_restx import Api

from config import SQLALCHEMY_DATABASE_URI, SQLALCHEMY_TRACK_MODIFICATIONS
from src.auth.rbac import ns_perm
from src.auth.user import AuthApiNs
from src.dbHandler.db import db
from src.issues.issues import IssuesApiNs
from src.notification.notification import socketio

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = SQLALCHEMY_TRACK_MODIFICATIONS
api = Api(
    app,
    version="1.0",
    title="Sample API",
    description="A simple demonstration of Swagger with Flask-RESTX",
)
api.add_namespace(AuthApiNs, "/auth")
api.add_namespace(IssuesApiNs, "/issues")
api.add_namespace(ns_perm, "/auth/permissions")
db.init_app(app)
socketio.init_app(app)


@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"


if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    # 👇 This replaces app.run()
    socketio.run(app, debug=True, host="0.0.0.0", port=5000)
