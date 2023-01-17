from flask_restful import abort
from marshmallow import ValidationError


def schema_loader(schema, inp):
    """
    Helper function that aborts a request if the schema of the resource fails,
    returning the first reason why it failed.
    """
    try:
        data = schema.load(inp)
    except ValidationError as err:
        field = list(err.messages.keys())[0]
        abort(400, message=f"{field}: {err.messages[field][0]}")
    else:
        return data


# def get_movement(identifier):
#     try:
#         identifier = int(identifier)
#         movement = Movement.find_by_id(identifier)
#     except ValueError:
#         movement = Movement.find_by_name(identifier)
#
#     if not movement:
#         abort(404, message="This movement does not exist.")
#
#     return movement
#
#
# def get_user(identifier):
#     try:
#         identifier = int(identifier)
#         user = User.find_by_id(identifier)
#     except ValueError:
#         user = User.find_by_name(identifier)
#
#     return user
