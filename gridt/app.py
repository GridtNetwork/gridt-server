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
from datetime import timedelta

from flask import Flask, jsonify
from flask.cli import FlaskGroup
from flask_sqlalchemy import SQLAlchemy
from flask_jwt import JWT, jwt_required, current_identity
from flask_restful import Api

from gridt.db import db

from gridt.models.movement import Movement

from gridt.auth.security import authenticate, identify
from gridt.resources.register import LoggedInResource, RegisterResource
from gridt.resources.movements import (
    MovementsResource,
    SubscriptionsResource,
    SingleMovementResource,
    SubscribeResource,
    SwapLeaderResource,
    FindLeaderResource,
    NewUpdateResource,
)


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

    app.logger.info(f"Starting flask with {config_name} config.")

    db.init_app(app)
    if app.config.get("FLASK_DEBUG", True):
        with app.app_context():
            db.create_all()

    api = Api(app)
    api.add_resource(LoggedInResource, "/logged_in")
    api.add_resource(RegisterResource, "/register")
    api.add_resource(MovementsResource, "/movements")
    api.add_resource(SingleMovementResource, "/movements/<identifier>")
    api.add_resource(SubscriptionsResource, "/movements/subscriptions")
    api.add_resource(SubscribeResource, "/movements/<movement_id>/subscriber")
    # TODO: Remove when implementing #22
    api.add_resource(FindLeaderResource, "/movements/<movement_id>/leader")
    api.add_resource(SwapLeaderResource, "/movements/<movement_id>/leader/<leader_id>")
    api.add_resource(NewUpdateResource, "/movements/<movement_id>/update")

    JWT(app, authenticate, identify)

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
        movement = Movement("test", timedelta(days=2))
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

    return app


if __name__ == "__main__":
    cli()
