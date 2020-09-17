from marshmallow import Schema, fields, validates, validates_schema, ValidationError
from marshmallow.validate import Length, OneOf, Equal
from flask import current_app
import jwt

from gridt.models.movement import Movement
from gridt.models.user import User


class BioSchema(Schema):
    bio = fields.Str(required=True)


class NewUserSchema(Schema):
    username = fields.Str(required=True, validate=Length(max=32))
    email = fields.Email(required=True, validate=Length(max=40))
    password = fields.Str(required=True, validate=Length(max=32))

    @validates("username")
    def validate_username(self, value):
        if User.find_by_name(value):
            raise ValidationError("Could not create user, because username is already in use.")
    
    @validates("email")
    def validate_email(self, value):
        if User.find_by_email(value):
            # Cannot give malicious users information on the
            # e-mail addresses in our database.
            # Otherwise we should find a way to block malicious 
            # attempts at creating accounts.
            raise ValidationError("Could not create user.")

class MovementSchema(Schema):
    name = fields.Str(required=True, validate=Length(min=4, max=50))
    short_description = fields.Str(required=True, validate=Length(min=10, max=100))
    description = fields.Str(validate=Length(max=1000))
    interval = fields.Str(
        required=True, validate=OneOf(["daily", "twice daily", "weekly"])
    )

    @validates("name")
    def validate_name(self, value):
        if Movement.find_by_name(value):
            raise ValidationError("Could not create movement, because movement name is already in use.")


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
            token_decoded = jwt.decode(value, secret_key, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            raise ValidationError("Signature has expired.")
        except jwt.InvalidTokenError:
            raise ValidationError("Invalid token.")

            
class ChangeEmailSchema(Schema):
    password = fields.Str(required=True)
    new_email = fields.Email(required=True)
