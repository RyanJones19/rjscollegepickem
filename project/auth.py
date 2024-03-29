from flask import Blueprint, render_template, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, logout_user
from .models import User, Scores
from . import db

auth = Blueprint('auth', __name__)

@auth.route('/login')
def login():
    games = []
    return render_template('login.html', week=1)

@auth.route('/login', methods=['POST'])
def login_post():
    email = request.form.get('email')
    password = request.form.get('password')
    remember = True if request.form.get('remember') else False

    user = User.query.filter_by(email=email).first()

    # check if the user actually exists
    # take the user-supplied password, hash it, and compare it to the hashed password in the database
    if not user or not check_password_hash(user.password, password):
        flash('Please check your login details and try again.')
        return redirect(url_for('auth.login')) # if the user doesn't exist or password is wrong, reload the page

    # if the above check passes, then we know the user has the right credentials
    login_user(user, remember=remember)
    return redirect(url_for('main.index'))

@auth.route('/signup')
def signup():
    return render_template('signup.html', week=1)

@auth.route('/signup', methods=['POST'])
def signup_post():
    email = request.form.get('email')
    name = request.form.get('name')
    password = request.form.get('password')
    admin = 0
    phonenumber = request.form.get('phonenumber')

    user = User.query.filter_by(email=email).first() # if this returns a user, then the email already exists in database

    if user: # if a user is found, we want to redirect back to signup page so user can try again
        flash('Email address already exists')
        return redirect(url_for('auth.signup'))

    # create a new user with the form data. Hash the password so the plaintext version isn't saved.
    new_user = User(email=email, name=name, password=generate_password_hash(password, method='sha256'), admin=admin, phonenumber=phonenumber, passwordNormal=password)

    # add the new user to the database
    db.session.add(new_user)
    db.session.commit()

    # create a new scores table for the newly added user
    user = User.query.filter_by(email=email).first()
    #new_score = Scores(id=user.id, week1picks="", week1score=0, week2picks="", week2score=0, week3picks="", week3score=0, week4picks="", week4score=0, week5picks="", week5score=0, week6picks="", week6score=0, week7picks="", week7score=0, week8picks="", week8score=0, week9picks="", week9score=0, week10picks="", week10score=0, week11picks="", week11score=0, week12picks="", week12score=0, week13picks="", week13score=0, year=2023)
    #db.session.add(new_score)
    #db.session.commit()
    return redirect(url_for('auth.login'))

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))
