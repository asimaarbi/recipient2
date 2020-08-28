import os
import os.path as op

from flask import request
from flask_restful import reqparse, Resource, abort
from werkzeug.security import check_password_hash

from models import User,Super
from serializers import UserSchema



def authenticate():
    token = request.headers.get('Authorization')
    if not token:
        abort(401, description="Unauthorized")
    items = token.split(' ')
    if len(items) != 2:
        abort(401, description="Unauthorized")
    if items[0].lower() != 'token':
        abort(401, description="Unauthorized")
    user = User.query.filter_by(token=items[1]).first()
    if not user:
        abort(401, description="Unauthorized")
    return user


class Applogin(Resource):
    def post(self):
        parser = reqparse.RequestParser(bundle_errors=True)
        parser.add_argument('email', type=str, help='Email', required=True)
        parser.add_argument('password', type=str, help='Password', required=True)
        args = parser.parse_args(strict=True)

        user = Super.query.filter_by(email=args['email']).first()
        if not user:
            user = User.query.filter_by(email=args['email']).first()
        if user:
            if check_password_hash(user.password, args['password']):
                schema = UserSchema()
                return schema.dump(user), 200
        return "Invalid Credentials. Please try again.", 400


