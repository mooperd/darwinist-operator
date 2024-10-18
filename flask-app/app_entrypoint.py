from app import app
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required, current_user
from flask import Flask, request, jsonify, abort, render_template, redirect, url_for, flash
import secrets
import model
import jobs
import approval
import trial
import product
import user

if __name__ == '__main__':
    # Initialize the database engine
    # engine = model.create_engine('postgresql+psycopg2://user:password@hostname/database_name', echo=True)
    model.create_all()
    
    # Create a scoped session
    app.run(debug=True)