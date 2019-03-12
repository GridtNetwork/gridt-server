from flask_jwt import jwt_required
from flask_restful import Resource, reqparse

class Login(Resource):
    parser = reqparse.RequestParser()

    def post(asd):
        pass

class LoggedIn(Resource):
    @jwt_required()
    def get():
        return {'message': f'Hi { current_identity.username }, you are logged in.'}, 200
