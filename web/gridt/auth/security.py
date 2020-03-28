import logging

from gridt.models import *


def authenticate(email, password):
    user = User.find_by_email(email)

    if user and user.verify_password(password):
        return user


def identify(payload):
    user_id = payload["identity"]
    return User.find_by_id(user_id)
