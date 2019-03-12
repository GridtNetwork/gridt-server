"""
App module
**********

This module provides ``create_app()``, it is the main entry point for the
application. When executing the commmand `flask run` it will find this module
and search for create_app and run it. BaseTest also uses this file to provide a
test environment.
"""

import os
import sys
import click

sys.path.append('/home/robin/Documents/work/gridt/gridt-server/gridt/')

from flask import Flask, jsonify
from flask.cli import FlaskGroup
from flask_sqlalchemy import SQLAlchemy
from flask_jwt import JWT, jwt_required, current_identity
from flask_restful import Api

from db import db

from auth.security import authenticate, identify
from auth.login import Login, LoggedIn

def create_app(overwrite_conf=None):
    """
    :param overwrite_conf: default None, argument should be one of: development, testing, default.
    """
    app = Flask(__name__)
    config = {
        "development": "conf/development.cfg",
        "testing": "conf/testing.cfg",
        "default": "conf/default.cfg",
    }
    config_name = os.getenv("FLASK_CONFIGURATION", "default")

    if overwrite_conf:
        config_name = overwrite_conf

    app.logger.debug(f"Starting flask with {config_name} config.")
    app.config.from_pyfile(config[config_name])
    db.init_app(app)

    JWT(app, authenticate, identify)
    api = Api(app)

    @app.cli.command()
    def initdb():
        app.logger.debug(f"Writing to database '{app.config['SQLALCHEMY_DATABASE_URI']}'")
        db.create_all()

    return app

if __name__ == '__main__':
    cli()

