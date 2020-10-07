from flask import request, current_app
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity

from marshmallow import ValidationError


from gridt_server.models.user import User
from gridt_server.schemas import (
    BioSchema,
    ChangeEmailSchema,
    RequestEmailChangeSchema,
    ChangePasswordSchema,
    RequestPasswordResetSchema,
    ResetPasswordSchema,
)

import jwt
from util.email_templates import (
    send_password_reset_email,
    send_password_change_notification,
    send_email_change_email,
    send_email_change_notification,
)

from .helpers import schema_loader


class BioResource(Resource):
    schema = BioSchema()

    @jwt_required
    def put(self):
        current_identity = User.query.get(get_jwt_identity())

        data = request.get_json()
        bio = None
        try:
            bio = self.schema.load(data)["bio"]
        except ValidationError as error:
            return {"message": "Bad request."}, 400

        current_identity.bio = bio
        current_identity.save_to_db()

        return {"message": "Bio successfully changed."}


class ChangePasswordResource(Resource):
    schema = ChangePasswordSchema()

    @jwt_required
    def post(self):
        current_identity = User.query.get(get_jwt_identity())

        try:
            res = self.schema.load(request.get_json())
        except ValidationError as error:
            field = list(error.messages.keys())[0]
            return ({"message": f"{field}: {error.messages[field][0]}"}, 400)

        if not current_identity.verify_password(res["old_password"]):
            return ({"message": "Failed to identify user with given password."}, 400)

        if current_identity.verify_password(res["old_password"]):
            current_identity.hash_and_store_password(res["new_password"])

            send_password_change_notification(current_identity.email)
            return ({"message": "Successfully changed password."}, 200)


class RequestEmailChangeResource(Resource):
    schema = RequestEmailChangeSchema()

    @jwt_required
    def post(self):
        current_identity = User.query.get(get_jwt_identity())

        self.schema.context = {"user": current_identity}
        data = schema_loader(self.schema, request.get_json())

        new_email = data["new_email"]
        if User.find_by_email(new_email):
            # We cannot give a malicious user information about the e-mails in
            # our database.
            return (
                {"message": "Successfully sent verification e-mail. Check your inbox."},
                200,
            )

        token = current_identity.get_email_change_token(new_email)
        send_email_change_email(new_email, current_identity.username, token)
        return (
            {"message": "Successfully sent verification e-mail. Check your inbox."},
            200,
        )


class ChangeEmailResource(Resource):
    schema = ChangeEmailSchema()

    def post(self):
        data = schema_loader(self.schema, request.get_json())

        secret_key = current_app.config["SECRET_KEY"]
        token_decoded = jwt.decode(data["token"], secret_key, algorithms=["HS256"])
        user_id = token_decoded["user_id"]
        new_email = token_decoded["new_email"]

        user = User.find_by_id(user_id)
        user.email = new_email

        send_email_change_notification(user.email, user.username)
        return ({"message": "Successfully changed e-mail."}, 200)


class RequestPasswordResetResource(Resource):
    schema = RequestPasswordResetSchema()

    def post(self):
        data = schema_loader(self.schema, request.get_json())

        if not current_app.config["EMAIL_API_KEY"]:
            return ({"message": "Could not send e-mail; API key not available."}, 500)

        user = User.find_by_email(data["email"])
        if not user:
            # We don't want malicious users to know whether or not an e-mail is in our database.
            return ({"message": "Recovery e-mail successfully sent."}, 200)

        token = user.get_password_reset_token()
        send_password_reset_email(user.email, token)
        return ({"message": "Recovery e-mail successfully sent."}, 200)


class ResetPasswordResource(Resource):
    schema = ResetPasswordSchema()

    def post(self):
        secret_key = current_app.config["SECRET_KEY"]
        data = schema_loader(self.schema, request.get_json())

        token_decoded = jwt.decode(data["token"], secret_key, algorithms=["HS256"])
        user_id = token_decoded["user_id"]
        password = data["password"]

        user = User.find_by_id(user_id)
        user.hash_and_store_password(password)

        send_password_change_notification(user.email)
        return ({"message": "Successfully changed password."}, 200)
