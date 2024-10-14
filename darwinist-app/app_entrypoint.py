from app import app
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required, current_user
import product
import clinical_trial
from flask import Flask, request, jsonify, abort, render_template, redirect, url_for, flash
import secrets
import model
import jobs

if __name__ == '__main__':
    # Initialize the database engine
    engine = model.create_engine('sqlite:///clinical_ai_products.db', echo=True)
    model.create_all()
    
    # Create a scoped session
    app.run(debug=True)


    """
    # Similar routes can be created for Products, Pathologies, etc.
if __name__ == '__main__':

    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'  # Route to redirect users who are not logged in

    @login_manager.user_loader
    def load_user(user_id):
        return Session.query(User).get(int(user_id))

    # Create a scoped session
    app.run(debug=True)"""