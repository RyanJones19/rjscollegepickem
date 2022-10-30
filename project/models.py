from flask_login import UserMixin
from . import db

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True) # primary keys are required by SQLAlchemy
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))
    admin = db.Column(db.Integer, default=0, nullable=False)

class Adminselections(UserMixin, db.Model):
    year = db.Column(db.Integer, primary_key=True)
    week1 = db.Column(db.String(255))
    week2 = db.Column(db.String(255))
    week3 = db.Column(db.String(255))
    week4 = db.Column(db.String(255))
    week5 = db.Column(db.String(255))
    week6 = db.Column(db.String(255))
    week7 = db.Column(db.String(255))
    week8 = db.Column(db.String(255))
    week9 = db.Column(db.String(255))
    week10 = db.Column(db.String(255))
    week11 = db.Column(db.String(255))
    week12 = db.Column(db.String(255))

class Scores(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    week1picks = db.Column(db.String(255))
    week1score = db.Column(db.Integer)
    week2picks = db.Column(db.String(255))
    week2score = db.Column(db.Integer)
    week3picks = db.Column(db.String(255))
    week3score = db.Column(db.Integer)
    week4picks = db.Column(db.String(255))
    week4score = db.Column(db.Integer)
    week5picks = db.Column(db.String(255))
    week5score = db.Column(db.Integer)
    week6picks = db.Column(db.String(255))
    week6score = db.Column(db.Integer)
    week7picks = db.Column(db.String(255))
    week7score = db.Column(db.Integer)
    week8picks = db.Column(db.String(255))
    week8score = db.Column(db.Integer)
    week9picks = db.Column(db.String(255))
    week9score = db.Column(db.Integer)
    week10picks = db.Column(db.String(255))
    week10score = db.Column(db.Integer)
    week11picks = db.Column(db.String(255))
    week11score = db.Column(db.Integer)
    week12picks = db.Column(db.String(255))
    week12score = db.Column(db.Integer)

