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

from gridtlib.controllers.movements import movement_exists, get_movement
from gridtlib.controllers.user import user_exists, verify_password_for_id
from gridtlib.controllers.follower import follows_leader
from gridtlib.controllers.subscription import is_subscribed


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

    @validates("name")
    def unique_name(self, value):
        existing_movement = get_movement(value)
        if existing_movement:
            raise ValidationError("Movement name already in use.")


class ChangePasswordSchema(Schema):
    old_password = fields.Str(required=True)
    new_password = fields.Str(required=True)

    @validates("old_password")
    def old_password_correct(self, value):
        if not verify_password_for_id(self.context["user_id"], value):
            raise ValidationError("Failed to identify user with given password.")


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

    @validates("password")
    def validate_password(self, value):
        if not verify_password_for_id(self.context["user_id"], value):
            raise ValidationError("Failed to identify user with given password.")


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

    @validates("movement_id")
    def movement_exists(self, value):
        if not movement_exists(int(value)):
            raise ValidationError("No movement found for that id.")

    @validates_schema
    def in_movement_and_following(self, data, **kwargs):
        data = {field: int(data[field]) for field in data}
        if not is_subscribed(data['follower_id'], data['movement_id']):
            raise ValidationError("User is not subscribed to this movement.")
        # This prevents a malicious user from finding user ids.
        # Returning a 404 for a nonexistant user would give them more
        # information than we want to share.
        if not user_exists(data["leader_id"]) or not follows_leader(
            data["follower_id"], data["movement_id"], data["leader_id"]
        ):
            raise ValidationError("User is not following this leader.")


class SingleMovementSchema(Schema):
    movement_id = fields.Int(required=True)

    @validates("movement_id")
    def movement_exists(self, value):
        if not movement_exists(value):
            raise ValidationError("No movement found for that id.")


class SignalSchema(Schema):
    movement_id = fields.Int(required=True)
    leader_id = fields.Int(required=True)

    @validates("movement_id")
    def movement_exists(self, value):
        if not movement_exists(value):
            raise ValidationError("No movement found for that id.")

    @validates("leader_id")
    def leader_exists(self, value):
        if not user_exists(value):
            raise ValidationError("No user found for that id.")

    @validates_schema
    def leader_in_movement(self, data, *args, **kwargs):
        if not is_subscribed(data["leader_id"], data["movement_id"]):
            raise ValidationError("User not subscribed to movement")
