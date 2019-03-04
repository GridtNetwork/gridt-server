import logging

from flask import g
from flask_httpauth import HTTPBasicAuth

from models.user import User

auth = HTTPBasicAuth()

@auth.verify_password
def verify_password(username, password):
    user = User.find_by_name(username)

    if not user or not user.verify_password(password):
        return False

    g.user = user

    return True
