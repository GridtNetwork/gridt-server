from marshmallow import Schema, fields, validates_schema, ValidationError
from marshmallow.validate import Length, OneOf, Equal


class BioSchema(Schema):
    bio = fields.Str(required=True)


class NewUserSchema(Schema):
    username = fields.Str(required=True, validate=Length(max=32))
    email = fields.Str(required=True, validate=Length(max=40))
    password = fields.Str(required=True, validate=Length(max=32))


class MovementSchema(Schema):
    name = fields.Str(required=True, validate=Length(min=4, max=50))
    short_description = fields.Str(required=True, validate=Length(min=10, max=100))
    description = fields.Str(validate=Length(max=1000))
    interval = fields.Str(
        required=True, validate=OneOf(["daily", "twice daily", "weekly"])
    )


class ChangePasswordSchema(Schema):
    old_password = fields.Str(required=True)
    new_password = fields.Str(required=True)


class RequestPasswordResetSchema(Schema):
    email = fields.Email(required=True)

class ResetPasswordSchema(Schema):
    token = fields.Str(required=True)
    password = fields.Str(required=True)
    password2 = fields.Str(required=True, validate=Equal(password))