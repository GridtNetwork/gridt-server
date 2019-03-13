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
import logging
import pathlib
import click

from flask import Flask, jsonify
from flask.cli import FlaskGroup
from flask_sqlalchemy import SQLAlchemy
from flask_jwt import JWT, jwt_required, current_identity
from flask_restful import Api

from gridt.db import db

from gridt.auth.security import authenticate, identify
from gridt.resources.register import LoggedInResource, RegisterResource


def create_app(overwrite_conf=None):
    """
    :param overwrite_conf: default None, argument should be the name (excluding the .conf suffix) of the conf file in conf/ that you want to use.

    Example: ::

        gridt/
            app.py
            conf/
                default.conf
                your_file.conf

    Then you can run ``create_app('your_file')`` to overwrite whatever is in the ``FLASK_CONFIGURATION`` bash variable in that moment.

    """
    app = Flask(__name__)
    config_name = os.getenv("FLASK_CONFIGURATION", "default")

    if overwrite_conf:
        config_name = overwrite_conf

    try:
        path = (
            os.path.dirname(os.path.realpath(__file__))
            / pathlib.Path("conf/")
            / (config_name + ".conf")
        )
        app.config.from_pyfile(str(path))
    except FileNotFoundError:
        app.logger.error(f"Could not find file conf/{config_name}.conf, exiting.")
        sys.exit(1)

    app.logger.setLevel(logging.INFO)
    app.logger.debug(f"Starting flask with {config_name} config.")

    db.init_app(app)

    api = Api(app)
    api.add_resource(LoggedInResource, "/logged_in")
    api.add_resource(RegisterResource, "/register")

    JWT(app, authenticate, identify)

    @app.cli.command()
    def initdb():
        app.logger.info(
            f"Writing to database '{app.config['SQLALCHEMY_DATABASE_URI']}'."
        )
        db.create_all()

    return app


if __name__ == "__main__":
    cli()
