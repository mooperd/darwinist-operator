from flask import Flask
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required, current_user
from utilities import get_job_status
import model

app = Flask(__name__)
app.secret_key = 'super secret key'
# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Route to redirect users who are not logged in

@login_manager.user_loader
def load_user(user_id):
    return model.Session.query(model.User).get(int(user_id))

@app.context_processor
def inject_get_job_status():
    return dict(get_job_status=get_job_status)