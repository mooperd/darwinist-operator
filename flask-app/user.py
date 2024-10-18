from flask import Flask, request, jsonify, abort, render_template, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date
import secrets
from model import *
from app import app
import traceback
from datetime import datetime

## Root GUI endpoint
@app.route('/')
def index_gui():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        session = Session
        try:
            username = request.form['username']
            email = request.form['email']
            password = request.form['password']

            # Check if the user or email already exists
            existing_user = session.query(User).filter((User.username == username) | (User.email == email)).first()
            if existing_user:
                flash('username or email already exists', 'danger')
                return redirect(url_for('signup'))

            # Create a new user
            user = User(username=username, email=email)
            user.set_password(password)
            session.add(user)
            session.commit()
            flash('Account created successfully!', 'success')
            return redirect(url_for('login'))
        except SQLAlchemyError as e:
            session.rollback()
            flash(f'Error: {str(e)}', 'danger')
    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session = Session
        email = request.form['email']
        password = request.form['password']
        user = session.query(User).filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('index_gui'))
        else:
            flash('Invalid email or password', 'danger')
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully', 'success')
    return redirect(url_for('login'))