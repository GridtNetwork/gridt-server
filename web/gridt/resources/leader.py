from flask import request
from flask_restful import Resource, abort
from flask_jwt_extended import jwt_required, get_jwt_identity

from marshmallow import ValidationError

from gridt.schemas import LeaderSchema
from gridt.models.movement import Movement
from gridt.models.user import User
from gridt.models.signal import Signal

from .helpers import schema_loader, get_movement, get_user


class LeaderResource(Resource):
    schema = LeaderSchema()

    @jwt_required
    def get(self, movement_id, leader_id):
        current_identity = User.query.get(get_jwt_identity())

        self.schema.context["user"] = current_identity
        data = schema_loader(
            self.schema, {"movement_id": movement_id, "leader_id": leader_id}
        )
        movement = data["movement"]
        leader = data["leader"]

        leader_dict = leader.dictify()
        leader_dict["message_history"] = [
            signal.dictify()
            for signal in Signal.get_signal_history(leader, movement, 3)
        ]
        return leader_dict

    @jwt_required
    def post(self, movement_id, leader_id):
        current_identity = User.query.get(get_jwt_identity())
        movement = get_movement(movement_id)

        self.schema.context["user"] = current_identity
        data = schema_loader(
            self.schema, {"movement_id": movement_id, "leader_id": leader_id}
        )
        movement = data["movement"]
        leader = data["leader"]

        new_leader = movement.swap_leader(current_identity, leader)
        if not new_leader:
            return {"message": "Could not find leader to replace the current one."}

        time_stamp = None
        if Signal.find_last(new_leader, movement):
            time_stamp = str(Signal.find_last(new_leader, movement).time_stamp)

        leader_dict = new_leader.dictify()
        leader_dict["last_signal"] = time_stamp

        return (
            leader_dict,
            200,
        )
