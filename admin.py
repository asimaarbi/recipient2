import requests
from flask import session, redirect
from flask import flash
from flask_admin import BaseView, expose
from werkzeug.security import generate_password_hash
from flask_admin.contrib.sqla import ModelView

from wtforms.validators import required, DataRequired

from models import db


class MyModeView(ModelView):
    can_edit = True

    def is_accessible(self):
        if session.get('logged_out'):
            return False
        if session.get('logged_in'):
            return True


def send_request(uid, email, phone, status):
    result = requests.post("http://codebase.pk:9002/call",
                           json={"procedure": "org.deskconn.recipient",
                                 "args": [uid, email, phone, status]})
    j = result.json()
    if 'error' in j:
        flash('Telemarie not booted')
        return redirect('/user')
    else:
        return redirect('/user')


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

    def create_model(self, form):
        model = super().create_model(form)
        model.password = generate_password_hash(form.data['password'])
        db.session.add(model)
        db.session.commit()
        return model

    def update_model(self, form, model):
        updated = super().update_model(form, model)
        if updated:
            model.password = generate_password_hash(form.data['password'])
            db.session.commit()
        return updated

    def delete_model(self, form):
        deleted = super().delete_model(form)
        return deleted

    column_list = ['username', 'email', 'admin', 'active', 'otp']
    # form_columns = ['name', 'email', 'phone']

    form_args = {
        'email': {
            'validators': [DataRequired()]
        },
        # 'phone': {
        #     'validators': [DataRequired()]
        # }
    }

