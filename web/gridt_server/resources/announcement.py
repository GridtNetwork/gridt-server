from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity

from gridt_server.schemas import (
    AnnouncementSchema,
    UpdateAnnouncementSchema,
    DeleteAnnouncementSchema,
)
import gridt.exc as GridtExpections

from .helpers import schema_loader

from gridt.controllers.announcement import (
    create_announcement,
    update_announcement,
    get_announcements,
    delete_announcement
)


class AnnouncementsResource(Resource):
    schema = AnnouncementSchema()

    @jwt_required()
    def get(self, movement_id):
        return get_announcements(int(movement_id))

    @jwt_required()
    def post(self, movement_id):
        data = schema_loader(self.schema, request.get_json())
        try:
            create_announcement(
                message=data["message"],
                movement_id=data["movement_id"],
                user_id=get_jwt_identity()
            )
        except GridtExpections.UserNotAdmin:
            message = "Insufficient privileges to create an announcement."
            return {"message": message}, 403
        return {"message": "Successfully created announcement."}, 201


class SingleAnnouncementResource(Resource):
    schema_update = UpdateAnnouncementSchema()
    schema_delete = DeleteAnnouncementSchema()

    @jwt_required()
    def put(self, movement_id, announcement_id):
        schema_inp = {"announcement_id": announcement_id, **request.get_json()}
        data = schema_loader(schema=self.schema_update, inp=schema_inp)
        try:
            update_announcement(
                message=data["message"],
                announcement_id=data["announcement_id"],
                user_id=get_jwt_identity()
            )
        except GridtExpections.UserNotAdmin:
            message = "Insufficient privileges to update an announcement."
            return {"message": message}, 403
        except GridtExpections.AnnouncementNotFoundError:
            return {"message": "Announcement dose not exist."}, 404
        return {"message": "Announcement successfully updated."}, 201

    @jwt_required()
    def delete(self, movement_id, announcement_id):
        schema_loader(self.schema_delete, {"announcement_id": announcement_id})
        try:
            delete_announcement(int(announcement_id), get_jwt_identity())
        except GridtExpections.UserNotAdmin:
            message = "Insufficient privileges to delete an announcement."
            return {"message": message}, 403
        except GridtExpections.AnnouncementNotFoundError:
            return {"message": "Announcement dose not exist."}, 404
        return {"message": "Announcement successfully deleted."}, 201
