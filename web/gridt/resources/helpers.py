from gridt.models.movement import Movement
from gridt.models.user import User

from flask_restful import abort


def get_movement(identifier):
    try:
        identifier = int(identifier)
        movement = Movement.find_by_id(identifier)
    except ValueError:
        movement = Movement.find_by_name(identifier)

    if not movement:
        abort(404, message="This movement does not exist.")

    return movement


def get_user(identifier):
    try:
        identifier = int(identifier)
        user = User.find_by_id(identifier)
    except ValueError:
        user = User.find_by_name(identifier)

    return user
