from flask_restful import Resource
from flask_jwt_extended import jwt_required

from gridt_server.schemas import SingleMovementSchema
from .helpers import schema_loader

from gridt.controllers.network import (
    get_network_data,
)


class NetworkResource(Resource):
    schema = SingleMovementSchema()

    @jwt_required()
    def get(self, movement_id):
        data = schema_loader(self.schema, {'movement_id': movement_id})
        return get_network_data(int(data['movement_id']))
