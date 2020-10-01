import os.path as op
import threading

import requests
from flask import Flask, redirect, render_template, request, session, flash
from flask_restful import Api

from werkzeug.security import check_password_hash

import flask_admin as admin
from flask_admin import expose
from flask_admin.base import AdminIndexView
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


@app.route('/login', methods=['POST'])
def login():
    if request.form['username'] == 'admin' and request.form['password'] == 'password':
        session['logged_in'] = True
        if 'user' in session:
            session.pop('user')
        return redirect('/user')
    super = Super.query.filter_by(email=request.form['username']).first()
    if super:
        if check_password_hash(super.password, request.form['password']):
            session['logged_in'] = True
            return redirect('/user')
        if 'super' in session:
            session.pop('super')
            return redirect('/user')
        error = 'Invalid Credentials. Please try again.'
        return render_template('login.html', error=error)
    error = 'Invalid Credentials. Please try again.'
    return render_template('login.html', error=error)


@app.route('/logout', methods=['GET'])
def logout():
    session['logged_in'] = False
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


if __name__ == '__main__':
    admin = admin.Admin(app, name='Telemarie Recipients', index_view=MyAdminIndexView(name=' '), url='/admin')
    admin.add_view(UserModelView(User, db.session, url='/user'))
    admin.add_view(SuperModelView(Super, db.session, url='/super'))
    admin.add_link(MenuLink(name='Send Message', category='', url="/message"))
    admin.add_link(MenuLink(name='Power-Ops', category='', url="/power_ops"))
    admin.add_link(MenuLink(name='Logout', category='', url="/logout"))

    api.add_resource(Applogin, '/api/login/')
    app.run(host='0.0.0.0', port=7778, debug=True)
