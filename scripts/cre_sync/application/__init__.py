from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from application.config import config

sqla = SQLAlchemy()


def create_app(mode: str='production'):
    app = Flask(__name__)
    app.config.from_object(config[mode])
    config[mode].init_app(app)
    sqla.init_app(app=app)

    from application.web.web_main import app as app_blueprint
    app.register_blueprint(app_blueprint)

    return app

