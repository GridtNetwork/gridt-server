from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity

from gridt_server.schemas import LeaderSchema
from gridt.controllers.follower import get_leader, swap_leader
from .helpers import schema_loader


class LeaderResource(Resource):
    schema = LeaderSchema()

    @jwt_required()
    def get(self, movement_id, leader_id):
        schema_loader(
            self.schema,
            {
                "movement_id": movement_id,
                "follower_id": get_jwt_identity(),
                "leader_id": leader_id,
            },
        )
        return get_leader(
            follower_id=get_jwt_identity(),
            movement_id=int(movement_id),
            leader_id=int(leader_id)
        )

    @jwt_required()
    def post(self, movement_id, leader_id):
        schema_loader(
            self.schema,
            {
                "follower_id": get_jwt_identity(),
                "movement_id": movement_id,
                "leader_id": leader_id,
            },
        )

        new_leader = swap_leader(
            follower_id=get_jwt_identity(),
            movement_id=int(movement_id),
            leader_id=int(leader_id)
        )
        if not new_leader:
            return {"message": "Could not find leader to replace the current one."}

        return new_leader
