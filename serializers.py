from flask_marshmallow import Marshmallow, fields

from models import User

ma = Marshmallow()


class UserSchema(ma.SQLAlchemyAutoSchema):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, exclude=('password',), **kwargs)

    class Meta:
        model = User
