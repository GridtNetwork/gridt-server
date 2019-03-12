import logging

from models import *

def authenticate(username, password):
    user = User.find_by_name(username)

    if user and user.verify_password(password):
        return user

def identify(payload):
    user_id = payload['identity']
    return User.find_by_id(user_id)
