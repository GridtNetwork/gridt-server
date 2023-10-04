"""
App module
**********

This module provides ``create_app()``, it is the main entry point for the 
application. When executing the commmand `flask run` it will find this module 
and search for create_app and run it. BaseTest also uses this file to provide 
a test environment.
"""

import os

os.environ["PROMETHEUS_MULTIPROC_DIR"] = "/tmp"
os.environ["prometheus_multiproc_dir"] = '/path/to/metrics/directory'

import sys

from sqlalchemy import create_engine
from sqlalchemy.dialects.mysql import pymysql
from sqlalchemy_utils import database_exists, create_database
from sqlalchemy.exc import OperationalError

from flask import Flask
from flask_jwt_extended import JWTManager
from flask_restful import Api

from gridt.db import Session, Base

from gridt_server.resources.register import IdentityResource, RegisterResource
from gridt_server.resources.user import (
    BioResource,
    RequestEmailChangeResource,
    ChangeEmailResource,
    ChangePasswordResource,
    RequestPasswordResetResource,
    ResetPasswordResource,
)

from gridt_server.resources.announcement import AnnouncementsResource, SingleAnnouncementResource
from gridt_server.resources.network import NetworkResource
from gridt_server.resources.leader import LeaderResource
from gridt_server.resources.movements import (
    MovementsResource,
    SubscriptionsResource,
    SingleMovementResource,
    SubscribeResource,
    NewSignalResource,
)
from gridt_server.resources.login import LoginResource

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
    api.add_resource(LoginResource, "/auth")
    api.add_resource(RegisterResource, "/register")
    api.add_resource(IdentityResource, "/identity")
    api.add_resource(MovementsResource, "/movements")
    api.add_resource(SingleMovementResource, "/movements/<identifier>")
    api.add_resource(SubscriptionsResource, "/movements/subscriptions")
    api.add_resource(SubscribeResource, "/movements/<movement_id>/subscriber")
    api.add_resource(LeaderResource, "/movements/<movement_id>/leader/<leader_id>")
    api.add_resource(NewSignalResource, "/movements/<movement_id>/signal")
    api.add_resource(BioResource, "/bio")
    api.add_resource(ChangePasswordResource, "/user/change_password")
    api.add_resource(RequestPasswordResetResource, "/user/reset_password/request")
    api.add_resource(ResetPasswordResource, "/user/reset_password/confirm")
    api.add_resource(RequestEmailChangeResource, "/user/change_email/request")
    api.add_resource(ChangeEmailResource, "/user/change_email/confirm")
    api.add_resource(AnnouncementsResource, "/movements/<movement_id>/announcements")
    api.add_resource(SingleAnnouncementResource, "/movements/<movement_id>/announcements/<announcement_id>")
    api.add_resource(NetworkResource, "/movements/<movement_id>/data")


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
        if not database_exists(app.config["SQLALCHEMY_DATABASE_URI"]):
            create_database(app.config["SQLALCHEMY_DATABASE_URI"])
    except OperationalError:
        app.logger.critical("Could not connect to database.")
        sys.exit(1)

    api = Api(app)
    register_api_endpoints(api)

    jwt = JWTManager(app)

    # For backwards compatibility with flask-jwt
    app.config["JWT_HEADER_TYPE"] = "JWT"

    try:
        engine = create_engine(app.config["SQLALCHEMY_DATABASE_URI"])
        Session.configure(bind=engine)
        Base.metadata.create_all(engine)
    except ConnectionRefusedError:
        app.logger.critical("Connection was refused, exiting.")
        sys.exit(1)
    except pymysql.err.ProgrammingError:
        app.logger.critical("Programming error, exiting.")
        sys.exit(1)

    return app
