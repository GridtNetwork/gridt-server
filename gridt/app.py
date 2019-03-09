'''
App module
**********

This module provides ``create_app()``, it is the main entry point for the
application. When executing the commmand `flask run` it will find this module
and search for create_app and run it. BaseTest also uses this file to provide a
test environment.
'''

import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def create_app(overwrite_conf=None):
    '''
    :param overwrite_conf: default None, argument should be one of the files in `conf/`.
    '''
    app = Flask(__name__)
    config = {
        'development': 'conf/development.cfg',
        'testing': 'conf/testing.cfg',
        'default': 'conf/default.cfg',
    }
    config_name = os.getenv('FLASK_CONFIGURATION', 'default')

    if overwrite_conf:
        config_name = overwrite_conf

    app.logger.info(f'Starting flask with {config_name} config.')
    app.config.from_pyfile(config[config_name])

    return app
