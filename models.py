from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Super(db.Model):
    uid = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(50), unique=True, nullable=True)
    password = db.Column(db.String(255), nullable=True)
    role = db.Column(db.String(255), nullable=True, default='super')

    # def __str__(self):
    #     return self.name


class User(db.Model):
    __tablename__ = 'users'
    uid = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=True)
    email = db.Column(db.String(50), unique=True, nullable=True)
    password = db.Column(db.String(255), nullable=True)

    telemarie = db.relationship('Telemarie', backref='users', cascade="all, delete")
    us_recipient = db.relationship('Recipient', backref='users', cascade="all, delete")

    def __str__(self):
        return self.username


class Telemarie(db.Model):
    __tablename__ = 'telemaries'
    uid = db.Column(db.Integer, primary_key=True)
    identity = db.Column(db.String(50), nullable=True)
    type = db.Column(db.String(50), nullable=True)

    user_id = db.Column(db.Integer, db.ForeignKey("users.uid"))
    switch = db.relationship('Switch', backref='telemaries', cascade="all, delete")
    tel_recipient = db.relationship('Recipient', backref='telemaries', cascade="all, delete")

    def __str__(self):
        return self.identity


class Switch(db.Model):
    __tablename__ = 'switches'
    uid = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=True)

    telemarie_id = db.Column(db.Integer, db.ForeignKey("telemaries.uid"))
    Recipient = db.relationship('Recipient', backref='switches', cascade="all, delete")

    def __str__(self):
        return self.name


class Recipient(db.Model):
    __tablename__ = 'recipient'
    uid = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=True)
    email = db.Column(db.String(50), nullable=True)
    phone = db.Column(db.String(255), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.uid"))
    tele_id = db.Column(db.Integer, db.ForeignKey("telemaries.uid"))
    switch_id = db.Column(db.Integer, db.ForeignKey("switches.uid"))

    def __str__(self):
        return self.name

    @property
    def store_name(self):
        return User.query.filter_by(id=self.user_id).first().username

    @property
    def brand_name(self):
        return Telemarie.query.filter_by(id=self.tele_id).first().brand

    @property
    def type_name(self):
        return Switch.query.filter_by(id=self.switch_id).first().type
