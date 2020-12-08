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
