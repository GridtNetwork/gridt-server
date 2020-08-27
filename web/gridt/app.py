"""
App module
**********

This module provides ``create_app()``, it is the main entry point for the application. When executing the commmand `flask run` it will find this module and search for create_app and run it. BaseTest also uses this file to provide a
test environment.
"""

import os
import sys
import logging
import pathlib
import click
from functools import reduce

from sqlalchemy_utils import database_exists, create_database

from flask import Flask, jsonify
from flask.cli import FlaskGroup
from flask_sqlalchemy import SQLAlchemy
from flask_jwt import JWT, jwt_required, current_identity
from flask_restful import Api

from gridt.db import db

from gridt.models.movement import Movement

from gridt.auth.security import authenticate, identify
from gridt.resources.register import IdentityResource, RegisterResource
from gridt.resources.user import BioResource, ChangePasswordResource
from gridt.resources.leader import LeaderResource
from gridt.resources.movements import (
    MovementsResource,
    SubscriptionsResource,
    SingleMovementResource,
    SubscribeResource,
    NewSignalResource,
)

from prometheus_flask_exporter.multiprocess import GunicornPrometheusMetrics


def load_config(app, overwrite_conf):
    config_file = os.getenv("FLASK_CONFIGURATION", "conf/default.conf")

    if overwrite_conf:
        config_file = overwrite_conf

    try:
        app.config.from_pyfile(config_file)
    except FileNotFoundError:
        app.logger.error(f"Could not find file {config_file}, exiting.")
        sys.exit(1)

    if not app.config.get("SECRET_KEY"):
        try:
            path = app.config.get("SECRET_KEY_FILE")
            if not path:
                app.logger.critical("No secret key or secret key file specified.")
                sys.exit(1)

            with open(path, "r") as secret_file:
                secret = [
                    l.rstrip("\n") for l in secret_file
                ]  # Remove '\n' from the end of the line.
                if not secret:
                    app.logger.critical("No secret provided in secrets file.")
                    sys.exit(1)
                if len(secret) > 1:
                    app.logger.critical("Secret file has more than 1 line.")
                    sys.exit(1)
                app.config["SECRET_KEY"] = secret[0]
        except FileNotFoundError:
            app.logger.critical("Could not load secret key file.")
            sys.exit(1)
    app.logger.info(f"Starting flask with {config_file} config.")


def construct_database_url(app):
    if not app.config.get("SQLALCHEMY_DATABASE_URI"):
        if not app.config.get("DB_DIALECT"):
            app.logger.critical(
                "Neither SQLALCHEMY_DATABASE_URI or DB_DIALECT has been specified in the configuration file, exiting."
            )
            sys.exit()
        protocol = app.config["DB_DIALECT"]
        protocol += "+" + app.config["DB_DRIVER"] if app.config.get("DB_DRIVER") else ""
        identification = app.config["DB_USER"] + ":" + app.config["DB_PASSWORD"]
        uri = app.config["DB_HOST"] + "/" + app.config["DB_DATABASE"]
        url = protocol + "://" + identification + "@" + uri
        app.config["SQLALCHEMY_DATABASE_URI"] = url
        app.logger.info(f"Connecting to db at {app.config['SQLALCHEMY_DATABASE_URI']}")


def register_api_endpoints(api):
    """
    Connect all resources with an appropriate url.
    """
    api.add_resource(IdentityResource, "/identity")
    api.add_resource(RegisterResource, "/register")
    api.add_resource(MovementsResource, "/movements")
    api.add_resource(SingleMovementResource, "/movements/<identifier>")
    api.add_resource(SubscriptionsResource, "/movements/subscriptions")
    api.add_resource(SubscribeResource, "/movements/<movement_id>/subscriber")
    api.add_resource(LeaderResource, "/movements/<movement_id>/leader/<leader_id>")
    api.add_resource(NewSignalResource, "/movements/<movement_id>/signal")
    api.add_resource(BioResource, "/bio")
    api.add_resource(ChangePasswordResource, "/change_password")


def add_cli_commands(app, db):
    @app.cli.command("initdb")
    def initialize_database():
        """
        Initialize the database.

        Mainly consists of creating the tables.
        """
        app.logger.info(
            f"Writing to database '{app.config['SQLALCHEMY_DATABASE_URI']}'."
        )
        db.create_all()

    @app.cli.command("insert-test-data")
    def insert_test_data():
        """
        Insert test data into the database.

        Current dataset is very limited.
        """
        movement = Movement("test", "daily")
        movement.save_to_db()

    @app.cli.command("delete-movement")
    @click.argument("movement_name")
    def delete_movement(movement_name):
        """ Delete a movement from the database. """
        movement = Movement.find_by_name(movement_name)
        if not movement:
            app.logger.error(f"Could not find movement with name '{movement_name}.'")
            return 1

        q = "neither"
        while not q in ["", "y", "n", "Y", "N", "yes", "no"]:
            q = input(
                f"Do you really want to delete the movement with name '{movement_name}'? [y/N]"
            )
        if q in ["", "n", "N", "no"]:
            return

        movement.delete_from_db()


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
    metrics = GunicornPrometheusMetrics(app)

    load_config(app, overwrite_conf)
    construct_database_url(app)
    try:
        db.init_app(app)
    except ConnectionRefusedError:
        print("Connection was refused, exiting.")
        sys.exit(1)
    except pymysql.err.ProgrammingError:
        print("Programming error, exiting.")
        sys.exit(1)

    try:
        if not database_exists(app.config["SQLALCHEMY_DATABASE_URI"]):
            create_database(app.config["SQLALCHEMY_DATABASE_URI"])
    except sqlalchemy.exc.OperationalError:
        print("Could not connect to database.")
        sys.exit(1)

    if app.config.get("FLASK_DEBUG", True):
        with app.app_context():
            db.create_all()

    api = Api(app)
    register_api_endpoints(api)

    JWT(app, authenticate, identify)

    add_cli_commands(app, db)

    return app


if __name__ == "__main__":
    cli()
