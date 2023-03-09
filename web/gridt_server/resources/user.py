from flask import request, current_app
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity

from gridt_server.schemas import (
    BioSchema,
    ChangeEmailSchema,
    RequestEmailChangeSchema,
    ChangePasswordSchema,
    RequestPasswordResetSchema,
    ResetPasswordSchema,
)


from .helpers import schema_loader

from gridtlib.controllers.user import (
    update_user_bio,
    change_password,
    request_email_change,
    change_email,
    request_password_reset,
    reset_password
)


class BioResource(Resource):
    schema = BioSchema()

    @jwt_required()
    def put(self):
        data = schema_loader(self.schema, request.get_json())
        update_user_bio(get_jwt_identity(), data["bio"])
        return {"message": "Bio successfully changed."}


class ChangePasswordResource(Resource):
    schema = ChangePasswordSchema()

    @jwt_required()
    def post(self):
        self.schema.context["user_id"] = get_jwt_identity()
        data = schema_loader(self.schema, request.get_json())
        change_password(get_jwt_identity(), data["new_password"])
        return {"message": "Successfully changed password."}


class RequestEmailChangeResource(Resource):
    schema = RequestEmailChangeSchema()

    @jwt_required()
    def post(self):
        self.schema.context = {"user_id": get_jwt_identity()}
        data = schema_loader(self.schema, request.get_json())
        request_email_change(
            get_jwt_identity(), data["new_email"], current_app.config["SECRET_KEY"],
        )
        return {
            "message": "Successfully sent verification e-mail. Check your inbox."
        }  # noqa


class ChangeEmailResource(Resource):
    schema = ChangeEmailSchema()

    def post(self):
        data = schema_loader(self.schema, request.get_json())
        secret_key = current_app.config["SECRET_KEY"]
        change_email(get_jwt_identity(), data["token"], secret_key)
        return ({"message": "Successfully changed e-mail."}, 200)


class RequestPasswordResetResource(Resource):
    schema = RequestPasswordResetSchema()

    def post(self):
        data = schema_loader(self.schema, request.get_json())

        if not current_app.config["EMAIL_API_KEY"]:
            return (
                {"message": "Could not send e-mail; API key not available."},
                500,
            )

        secret_key = current_app.config["SECRET_KEY"]
        request_password_reset(data["email"], secret_key)
        return {"message": "Recovery e-mail successfully sent."}


class ResetPasswordResource(Resource):
    schema = ResetPasswordSchema()

    def post(self):
        secret_key = current_app.config["SECRET_KEY"]
        data = schema_loader(self.schema, request.get_json())

        reset_password(token=data['token'], password=data['password'], secret_key=secret_key)

        return ({"message": "Successfully changed password."}, 200)
