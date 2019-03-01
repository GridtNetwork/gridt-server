import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def create_app(overwrite_conf=None):
    app = Flask(__name__)
    config = {
        "development": "conf/development.cfg",
        "testing": "conf/testing.cfg",
        "default": "conf/default.cfg"
    }
    config_name = os.getenv('FLASK_CONFIGURATION', 'default')

    if overwrite_conf:
        config_name = overwrite_conf

    app.logger.info(f'Starting flask with {config_name} config.')
    app.config.from_pyfile(config[config_name])

    return app
