from flask import session
from werkzeug.security import generate_password_hash
from flask_admin.contrib.sqla import ModelView

from wtforms.validators import required, Email, DataRequired

from models import db


class MyModeView(ModelView):
    can_edit = True

    def is_accessible(self):
        if session.get('logged_out'):
            return False
        if session.get('logged_in'):
            return True


class SuperModelView(MyModeView):
    can_edit = True
    can_create = True
    can_delete = False
    column_list = ['email', ]
    form_columns = ['email', 'password']

    def on_form_prefill(self, form, id):
        form.password.data = ''

    form_args = {
        'email': {
            'validators': [required()]
        },
        'password': {
            'default': '',
            'validators': [DataRequired(), ]
        }

    }

    def create_model(self, form):
        model = super().create_model(form)
        model.password = generate_password_hash(form.data['password'])
        db.session.add(model)
        db.session.commit()
        return model

    def update_model(self, form, model):
        updated = super().update_model(form, model)
        if updated:
            print(model.password)
            model.password = generate_password_hash(form.data['password'])
            db.session.commit()
        return updated


class UserModelView(MyModeView):
    can_create = True

    column_list = ['name', 'email', 'phone']
    form_columns = ['name', 'email', 'phone']

    form_args = {
        'email': {
            'validators': [Email()]
        }
    }




