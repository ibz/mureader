import datetime
from functools import wraps
import os

from flask import Flask, redirect, url_for
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_jwt_extended import JWTManager, verify_jwt_in_request
from flask_sqlalchemy import SQLAlchemy

from flask_jwt_extended.exceptions import NoAuthorizationError
from flask_jwt_extended.utils import verify_token_claims

app = Flask(__name__)

CORS(app)

class BaseConfig:
    SECRET_KEY = os.getenv('SECRET_KEY', 'my_precious')
    DEBUG = False
    BCRYPT_LOG_ROUNDS = 13
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI')
    JWT_TOKEN_LOCATION = 'cookies'
    JWT_ACCESS_TOKEN_EXPIRES = datetime.timedelta(days=1)
    PROPAGATE_EXCEPTIONS = False

app.config.from_object(BaseConfig)

bcrypt = Bcrypt(app)
jwt = JWTManager(app)
db = SQLAlchemy(app)

@jwt.claims_verification_failed_loader
def no_jwt():
    return redirect(url_for('login'))

@jwt.expired_token_loader
def jwt_token_expired():
    return redirect(url_for('refresh'))

def jwt_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
        except NoAuthorizationError:
            return no_jwt()
        return fn(*args, **kwargs)
    return wrapper
