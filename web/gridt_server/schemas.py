from marshmallow import (
    Schema,
    fields,
    validates,
    validates_schema,
    ValidationError,
)
from marshmallow.validate import Length, OneOf
from flask import current_app
import jwt


class LoginSchema(Schema):
    username = fields.Str(required=True)
    password = fields.Str(required=True)


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

    @validates("token")
    def validate_token(self, value):
        secret_key = current_app.config["SECRET_KEY"]
        try:
            jwt.decode(value, secret_key, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            raise ValidationError("Signature has expired.")
        except jwt.InvalidTokenError:
            raise ValidationError("Invalid token.")


class RequestEmailChangeSchema(Schema):
    password = fields.Str(required=True)
    new_email = fields.Email(required=True)


class ChangeEmailSchema(Schema):
    token = fields.Str(required=True)

    @validates("token")
    def validate_token(self, value):
        secret_key = current_app.config["SECRET_KEY"]
        try:
            jwt.decode(value, secret_key, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            raise ValidationError("Signature has expired.")
        except jwt.InvalidTokenError:
            raise ValidationError("Invalid token.")


class IdField(fields.Field):
    def _deserialize(self, value, attr, data, **kwargs):
        if isinstance(value, str) or isinstance(value, int):
            return value
        else:
            raise ValidationError("Id should be string or integer.")


class LeaderSchema(Schema):
    movement_id = IdField(required=True)
    # follower_id could have been made a context instead
    follower_id = fields.Int(required=True)
    leader_id = IdField(required=True)


class SingleMovementSchema(Schema):
    movement_id = fields.Int(required=True)


class SignalSchema(Schema):
    movement_id = fields.Int(required=True)
    leader_id = fields.Int(required=True)
