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
app = Flask(__name__, static_folder='images')
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
    def post(self):
        emails = []
        phones = []
        parser = reqparse.RequestParser(bundle_errors=True)
        parser.add_argument('switch', type=str, help='Switch no', required=True)
        parser.add_argument('machine', type=str, help='machine id', required=True)
        args = parser.parse_args()
        users = Recipient.query.filter(
            (Recipient.switch_id == args['switch']) & (Recipient.tele_id == args['machine'])).all()
        # users = Recipient.query.filter_by(switch_id=args['switch']).all()
        # schema = UserSchema(many=True)
        # return schema.dump(users)
        for user in users:
            emails.append(user.email)
            phones.append(user.phone)
        return {'emails': emails,
                'phones': phones}, 200


@app.route('/')
def messege():
    return render_template('message.html')


@app.route('/power_ops')
def power_ops():
    return render_template('power_ops.html')


@app.route('/send', methods=['POST'])
def send():
    message = request.form['password']
    machine = request.form['machines']
    _send_push(message, machine)
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


def _send_push(message, machine):
    requests.post("http://94.130.187.90:8080/call",
                  json={"procedure": f"tm.{machine}.message",
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

# @app.route('/', methods=['GET', 'POST'])
# def main():
#     user = User.query.all()
#     telemarie = Telemarie.query.all()
#     switch = Switch.query.all()
#     recipient = Recipient.query.all()
#
#     return render_template('index2.html', title='Home', recipients=recipient,
#                            telemaries=telemarie, switches=switch)


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
        name = None
        # user = User.query.filter_by(username=username).first()
        # if not user:
        #     return {"message": "username not exist"}, 404
        user = User.query.filter_by(uid=int(username)).first()
        if user:
            name = str(user.username).capitalize()
        albums = Telemarie.query.filter_by(user_id=int(username)).all()
        return render_template("telemarie.html", album_dates=albums, name=name, user_uid=username)


@app.route('/switch/<user_uid>/<machine_id>', methods=['GET'])
def switch(user_uid, machine_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    else:
        switch_id = 1
        machine = Telemarie.query.filter_by(uid=int(machine_id)).first()
        albums = Switch.query.filter_by(telemarie_id=int(machine_id)).all()
        return render_template("switch.html", album_dates=albums, user_uid=user_uid, machine_id=machine_id)


@app.route('/recipient/<switch_id>/<user_id>/<machine_id>', methods=['GET'])
def recipient(switch_id, user_id, machine_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    else:
        # user = User.query.filter_by(username=username).first()
        # if not user:
        #     return {"message": "username not exist"}, 404
        recipients = Recipient.query.filter_by(switch_id=int(switch_id)).all()
        return render_template("recipient.html", recipients=recipients, user_uid=user_id, machine_id=machine_id,
                               switch_id=switch_id)


@app.route('/create', methods=['POST', 'GET'])
def create():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    else:
        return render_template("create_user.html")


@app.route('/create/user', methods=['POST', 'GET'])
def create_user():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    else:
        if request.form['password'] != request.form['verify_password']:
            error = "Passwords not matched"
            return render_template("create_user.html", error=error)
        user = User()
        user.username = request.form['username']
        user.email = request.form['email']
        user.password = request.form['password']
        db.session.add(user)
        db.session.commit()
        return redirect('/users')


@app.route('/create_machin/<user_uid>', methods=['POST', 'GET'])
def create_machine(user_uid):
    return render_template("create_machine.html", user_uid=user_uid)


@app.route('/create/machine/<user_uid>', methods=['POST', 'GET'])
def create_machines(user_uid):
    tele = Telemarie()
    tele.identity = request.form['identity']
    tele.type = request.form['type']
    tele.user_id = user_uid
    db.session.add(tele)
    db.session.commit()
    return redirect(f'/telemarie/{user_uid}')


@app.route('/create_swicth/<user_uid>/<machine_id>', methods=['POST', 'GET'])
def create_switch(user_uid, machine_id):
    return render_template("create_switch.html", user_uid=user_uid, machine_id=machine_id)


@app.route('/create/switch/<user_uid>/<machine_id>', methods=['POST', 'GET'])
def create_switches(user_uid, machine_id):
    switch = Switch()
    switch.name = request.form['name']
    switch.telemarie_id = machine_id
    db.session.add(switch)
    db.session.commit()
    return redirect(f'/switch/{user_uid}/{machine_id}')


@app.route('/create_recipient/<user_uid>/<machine_id>/<switch_id>', methods=['POST', 'GET'])
def create_recipient(user_uid, machine_id, switch_id):
    return render_template("create_recipient.html", user_uid=user_uid, machine_id=machine_id, switch_id=switch_id)


@app.route('/create/recipient/<user_uid>/<machine_id>/<switch_id>', methods=['POST', 'GET'])
def create_recipients(user_uid, machine_id, switch_id):
    recipient = Recipient()
    recipient.name = request.form['name']
    recipient.email = request.form['email']
    recipient.phone = request.form['phone']
    recipient.user_id = user_uid
    recipient.tele_id = machine_id
    recipient.switch_id = switch_id
    db.session.add(recipient)
    db.session.commit()
    print(switch_id)
    return redirect(f'/recipient/{switch_id}/{user_uid}/{machine_id}')


@app.route('/get_emails/<switch_id>/<machine_id>', methods=['Get'])
def get_emails(switch_id, machine_id):
    user = Recipient.query.filter((Recipient.switch_id == switch_id) & (Recipient.tele_id == machine_id)).all()
    schema = UserSchema(many=True)
    return schema.dump(user), 200


@app.route('/api/recipients/<switch_id>/<machine_id>', methods=['Get'])
def get_recipients(switch_id, machine_id):
    emails = []
    phones = []
    users = Recipient.query.filter((Recipient.switch_id == switch_id) & (Recipient.tele_id == machine_id)).all()
    for user in users:
        emails.append(user.email)
        phones.append(user.phone)
    return {'emails': emails,
            'phones': phones}, 200


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

    # api.add_resource(RecipientResource, '/api/recipients/')
    app.run(host='0.0.0.0', port=7777, debug=True)
