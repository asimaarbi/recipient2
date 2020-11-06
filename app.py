import os.path as op
import threading

import requests
from flask import Flask, redirect, render_template, request, session, flash, url_for
from flask_restful import Api
from flask_login import LoginManager, current_user, login_user, logout_user

from werkzeug.security import check_password_hash

import flask_admin as admin
from flask_admin import expose
from flask_admin.base import AdminIndexView, BaseView
from flask_admin.menu import MenuLink

from admin import UserModelView, SuperModelView
from models import User, db, Super
from serializers import ma

from resources import Applogin

UPLOAD_FOLDER = './upload'
app = Flask(__name__, static_folder='images')
path = op.join(op.dirname(__file__), 'statics')
images = op.join(op.dirname(__file__), 'images')
app.config['SECRET_KEY'] = '5791628bb0b13ce0c676dfde280ba245'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///main.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'

api = Api(app)
db.init_app(app)
ma.init_app(app)
db.create_all(app=app)

login = LoginManager(app)


@login.user_loader
def load_user(user_id):
    return User.query.get(user_id)


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


@app.route('/login', methods=['Get', 'POST'])
def login():
    if request.form.get('username') == 'admin' and request.form.get('password') == 'password':
        session['logged_in'] = True
        if 'user' in session:
            session.pop('user')
        return redirect('/recipients')
        # return redirect('/user')
    super = Super.query.filter_by(email=request.form.get('username')).first()
    if super:
        if check_password_hash(super.password, request.form.get('password')):
            session['logged_in'] = True
            return redirect('/user')
        error = 'Invalid Credentials. Please try again.'
        return render_template('login.html', error=error)
    user = User.query.filter_by(email=request.form.get('username')).first()
    if user:
        if not user.active:
            return render_template('otp.html', username=user.username)
        if check_password_hash(user.password, request.form.get('password')):
            session['logged_in'] = True
            login_user(user)
            return redirect('/user')
        error = 'Invalid Credentials. Please try again.'
        return render_template('login.html', error=error)
    return render_template('login.html')


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


@app.route('/logout', methods=['GET'])
def logout():
    session['logged_in'] = False
    logout_user()
    return render_template('login.html')


class MyAdminIndexView(AdminIndexView):
    @expose('/')
    def index(self):
        if session.get('logged_in'):
            if request.cookies.get('username'):
                return redirect('/user')
        if not session.get('logged_in'):
            return render_template('login.html')
        return redirect('/user')


class RecipientsView(BaseView):
    @expose('/')
    def index(self):
        error=current_user.is_aunthenticated
        return self.render('admin/recipients.html', error=error)


if __name__ == '__main__':
    admin = admin.Admin(app, template_mode='bootstrap3', name='Telemarie Recipients', index_view=MyAdminIndexView(name=' '), url='/admin')
    admin.add_view(UserModelView(User, db.session, url='/user'))
    admin.add_view(SuperModelView(Super, db.session, url='/super'))
    admin.add_link(MenuLink(name='Send Message', url="/message"))
    admin.add_link(MenuLink(name='Power-Ops', url="/power_ops"))
    admin.add_link(MenuLink(name='Logout', url="/logout"))
    admin.add_view(RecipientsView(name='recipients', endpoint="/recipients", url="/recipients"))

    api.add_resource(Applogin, '/api/login/')
    app.run(host='0.0.0.0', port=7778, debug=True)
