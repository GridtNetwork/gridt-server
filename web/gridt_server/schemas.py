from marshmallow import (
    Schema,
    fields,
    validates,
    validates_schema,
    ValidationError,
    post_load,
)
from marshmallow.validate import Length, OneOf
from flask import current_app
import jwt

from gridt_server.models import Movement
from gridt_server.resources.helpers import get_movement, get_user
from gridt.controllers.movements import movement_exists, user_in_movement
from gridt.controllers.user import user_exists


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
        existing_movement = Movement.find_by_name(value)
        if existing_movement:
            raise ValidationError("Movement name already in use.")


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

    @validates("password")
    def validate_password(self, value):
        if not self.context["user"].verify_password(value):
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
    leader_id = IdField(required=True)
    _leader = None
    _movement = None

    @validates_schema
    def validate(self, data, **kwargs):
        # Separate functions instead of directly validating as one relies
        # on the other and order needs to be preserved.
        self.ensure_subscribed(data["movement_id"])
        self.ensure_following(data["leader_id"])

    def ensure_subscribed(self, movement_id):
        movement = get_movement(movement_id)

        if self.context["user"] not in movement.current_users:
            raise ValidationError("User is not subscribed to this movement.")

        self._movement = movement

    def ensure_following(self, value):
        leader = get_user(value)
        # This prevents a malicious user from finding user ids.
        # Returning a 404 for a nonexistant user would give them more
        # information than we want to share.
        if not leader or leader not in self.context["user"].leaders(self._movement):
            raise ValidationError("User is not following this leader.")
        self._leader = leader

    @post_load
    def return_queries(self, data, *args, **kwargs):
        return {"movement": self._movement, "leader": self._leader}


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
        if not user_in_movement(data["leader_id"], data["movement_id"]):
            raise ValidationError("User not subscribed to movement")
