from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Super(db.Model):
    uid = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(50), unique=True, nullable=True)
    password = db.Column(db.String(255), nullable=True)
    role = db.Column(db.String(255), nullable=True, default='super')


class User(db.Model):
    uid = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=True)
    email = db.Column(db.String(50), unique=True, nullable=True)
    password = db.Column(db.String(255), nullable=True)
    admin = db.Column(db.Boolean, default=False)
    otp = db.Column(db.String(255), nullable=True)
    active = db.Column(db.Boolean, default=False)


class Telemarie(db.Model):
    uid = db.Column(db.Integer, primary_key=True)
    identity = db.Column(db.String(50), unique=True, nullable=True)


class Switch(db.Model):
    uid = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=True)


class Recipient(db.Model):
    uid = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=True)
    email = db.Column(db.String(50), unique=True, nullable=True)
    phone = db.Column(db.String(255), nullable=True)
    active = db.Column(db.Boolean, default=False)
