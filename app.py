import os.path as op
import threading
import json

import requests
from flask import Flask, redirect, render_template, request, session, flash, url_for, jsonify
from flask_marshmallow import Marshmallow
from flask_restful import Api, Resource, reqparse
from flask_login import login_user, logout_user

from werkzeug.security import check_password_hash, generate_password_hash

import flask_admin as admin
from flask_admin import expose
from flask_admin.base import AdminIndexView, BaseView
from flask_admin.menu import MenuLink
from flask_admin.base import AdminIndexView, BaseView

from flask_admin.contrib.sqla import ModelView

from models import User, db, Super, Telemarie, Switch, Recipient

UPLOAD_FOLDER = './upload'
app = Flask(__name__)
path = op.join(op.dirname(__file__), 'statics')
images = op.join(op.dirname(__file__), 'images')
app.config['SECRET_KEY'] = '5791628bb0b13ce0c676dfde280ba245'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///main.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'

api = Api(app)
db.init_app(app)
ma = Marshmallow()

db.create_all(app=app)


class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        # Fields to expose
        fields = ("email", "phone")


class RecipientResource(Resource):
    def get(self):
        emails = []
        phones = []
        parser = reqparse.RequestParser(bundle_errors=True)
        parser.add_argument('switch', type=str, help='Switch no', required=True)
        args = parser.parse_args()
        users = Recipient.query.filter_by(switch_id=args['switch']).all()
        # schema = UserSchema(many=True)
        # return schema.dump(users)
        for user in users:
            emails.append(user.email)
            phones.append(user.phone)
        return {'emails': emails,
                'phones': phones}, 200


@app.route('/message')
def messege():
    return render_template('message.html')


@app.route('/power_ops')
def power_ops():
    return render_template('power_ops.html')


@app.route('/send', methods=['POST'])
def send():
    message = request.form['password']
    _send_push(message)
    flash("Message Sent", 'info')
    return render_template('message.html')


@app.route('/power', methods=['POST'])
def power():
    command = request.form['password']
    requests.post("http://codebase.pk:9002/call",
                  json={"procedure": "org.deskconn.power",
                        "args": [command]})
    flash("Command Sent", 'success')
    return redirect('/user')


def _send_push(message):
    requests.post("http://codebase.pk:9002/call",
                  json={"procedure": "org.deskconn.message",
                        "args": [message]})


def send_push():
    thread = threading.Thread(target=_send_push)
    thread.start()


@app.route('/user/<uid>')
def get_user(uid):
    print(uid)
    user = User.query.filter_by(uid=uid).first()
    if user:
        return user
        print(user.username)
    return "", 404


# @app.route('/login', methods=['Get', 'POST'])
# def login():
#     if request.form.get('username') == 'admin' and request.form.get('password') == 'password':
#         session['logged_in'] = True
#         if 'user' in session:
#             session.pop('user')
#         return redirect('/recipients')
#         # return redirect('/user')
#     super = Super.query.filter_by(email=request.form.get('username')).first()
#     if super:
#         if check_password_hash(super.password, request.form.get('password')):
#             session['logged_in'] = True
#             return redirect('/user')
#         error = 'Invalid Credentials. Please try again.'
#         return render_template('login.html', error=error)
#     user = User.query.filter_by(email=request.form.get('username')).first()
#     if user:
#         if not user.active:
#             return render_template('otp.html', username=user.username)
#         if check_password_hash(user.password, request.form.get('password')):
#             session['logged_in'] = True
#             login_user(user)
#             return redirect('/user')
#         error = 'Invalid Credentials. Please try again.'
#         return render_template('login.html', error=error)
#     return render_template('login.html')

@app.route('/', methods=['GET', 'POST'])
def main():
    user = User.query.all()
    telemarie = Telemarie.query.all()
    switch = Switch.query.all()
    recipient = Recipient.query.all()

    return render_template('index2.html', title='Home', recipients=recipient,
                           telemaries=telemarie, switches=switch)


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != 'admin' or request.form['password'] != 'password':
            error = 'Invalid Credentials. Please try again.'
        user = User.query.filter_by(email=request.form.get('username')).first()
        if user:
            # if not user.active:
            #     return render_template('otp.html', username=user.username)
            if check_password_hash(user.password, request.form.get('password')):
                session['logged_in'] = True
                # login_user(user)
                # return redirect('/user')
                return redirect(url_for('telemarie', username=user.uid))
            error = 'Invalid Credentials. Please try again.'
        else:
            session['logged_in'] = True
            return redirect(url_for('username'))
            # return redirect('/user')
    return render_template('login.html', error=error)


@app.route('/register', methods=['Get', 'POST'])
def register():
    user = User.query.filter_by(email=request.form.get('username')).first()
    if user:
        error = 'Already registered, Redirected to login'
        return render_template('login', error=error)
    return render_template('register.html')


@app.route('/verify', methods=['Get', 'POST'])
def verify():
    user = User.query.filter_by(username=request.form.get('username')).first()
    if user:
        print(user.username)
        if user.otp == request.form.get('otp'):
            user.active = True
            db.session.commit()
            return render_template('login.html')
    error = 'invalid otp'
    return render_template('otp.html', error=error)


@app.route('/logout')
def logout():
    session['logged_in'] = False
    return redirect(url_for('login'))


@app.route('/users', methods=['GET', 'POST'])
def username():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    else:
        session['logged_in'] = True
        test = 'test'
        user = User.query.all()
        telemarie = Telemarie.query.all()
        switch = Switch.query.all()
        return render_template("user.html", title='Home', users=user, telemaries=telemarie, switches=switch)


@app.route('/telemarie/<username>', methods=['GET'])
def telemarie(username):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    else:
        # user = User.query.filter_by(username=username).first()
        # if not user:
        #     return {"message": "username not exist"}, 404
        user = User.query.filter_by(uid=int(username)).first()
        name = str(user.username).capitalize()
        albums = Telemarie.query.filter_by(user_id=int(username)).all()
        return render_template("telemarie.html", album_dates=albums, name=name)


@app.route('/switch/<username>', methods=['GET'])
def switch(username):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    else:
        # user = User.query.filter_by(username=username).first()
        # if not user:
        #     return {"message": "username not exist"}, 404
        telemarie = Telemarie.query.filter_by(user_id=int(username)).first()
        # print(telemarie.identity)
        albums = Switch.query.filter_by(telemarie_id=int(username)).all()
        # for album in albums:
        #     print(album.name)
        return render_template("switch.html", album_dates=albums)


@app.route('/recipient/<username>', methods=['GET'])
def recipient(username):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    else:
        # user = User.query.filter_by(username=username).first()
        # if not user:
        #     return {"message": "username not exist"}, 404
        albums = Recipient.query.filter_by(switch_id=int(username)).all()
        return render_template("recipient.html", album_dates=albums)


class MyAdminIndexView(AdminIndexView):
    @expose('/')
    def index(self):
        if session.get('logged_in'):
            if request.cookies.get('username'):
                return redirect('/user')
        if not session.get('logged_in'):
            return render_template('login.html')
        return redirect('/user')


class MyModeView(ModelView):
    can_edit = True

    def is_accessible(self):
        if session.get('logged_out'):
            return False
        if session.get('logged_in'):
            return True


class UserModelView(MyModeView):
    can_create = True

    # form_choices = {
    #     'switch': [
    #         ('1', '1'),
    #         ('2', '2'),
    #         ('3', '3'),
    #         ('4', '4'),
    #         ('5', '5'),
    #     ],
    #     'group': [
    #         ('admin', 'admin'),
    #         ('recipient', 'recipient'),
    #     ]
    # }

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


class TelemarieView(MyModeView):
    can_edit = True
    can_create = True
    form_choices = {
        'product': [
            ('telemarie', 'telemarie'),
            ('teleclause', 'teleclause'),
        ]
    }


class TelemarieView(MyModeView):
    can_edit = True
    can_create = True


@app.route('/get_emails/<switch_id>', methods=['Get'])
def get_emails(switch_id):
    user = Recipient.query.filter_by(switch_id=switch_id).all()
    print('test' + switch_id)
    schema = UserSchema(many=True)
    return schema.dump(user), 200


@app.route('/delete_user/<uid>')
def delete_user(uid):
    user = User.query.filter_by(uid=uid).first()
    if user:
        db.session.delete(user)
    db.session.commit()
    return '', 204


@app.route('/delete_tele/<uid>')
def delete_tele(uid):
    tele = Telemarie.query.filter_by(uid=uid).first()
    if tele:
        db.session.delete(tele)
    db.session.commit()
    return '', 204


@app.route('/delete_switch/<uid>')
def delete_switch(uid):
    switch = Switch.query.filter_by(uid=uid).first()
    if switch:
        db.session.delete(switch)
    db.session.commit()
    return '', 204


@app.route('/delete_recipient/<uid>')
def delete_recipient(uid):
    recipient = Recipient.query.filter_by(uid=uid).first()
    if recipient:
        db.session.delete(recipient)
    db.session.commit()
    return '', 204


# @app.route('/create/user', methods=['POST', 'GET'])
# def create_user():
#     username = request.form['username']
#     email = request.form['author']
#     password = request.form['admin']
#     admin = request.form['admin']
#     otp = request.form['otp']
#     active = request.form['active']
#     user = User()
#     user.username = username
#     user.email = email
#     user.password = password
#     user.admin = admin
#     user.otp = otp
#     user.active = active
#     db.session.add(user)
#     db.session.commit()
#     return redirect('/quote')


if __name__ == '__main__':
    admin = admin.Admin(app, name='Telemarie Recipients',
                        index_view=MyAdminIndexView(name=' '), url='/admin')
    admin.add_view(UserModelView(User, db.session, url='/user'))
    admin.add_view(TelemarieView(Telemarie, db.session, endpoint="/telemarie", url="/telemarie"))
    admin.add_view(TelemarieView(Switch, db.session, endpoint="/recipeint", url="/recipeint"))
    admin.add_view(TelemarieView(Recipient, db.session, endpoint="/switch", url="/switch"))
    # admin.add_view(SuperModelView(Super, db.session, url='/super'))
    admin.add_link(MenuLink(name='Send Message', url="/message"))
    admin.add_link(MenuLink(name='Power-Ops', url="/power_ops"))
    admin.add_link(MenuLink(name='Logout', url="/logout"))

    api.add_resource(RecipientResource, '/api/recipients/')
    app.run(host='0.0.0.0', port=7778, debug=True)
