from flask import flash, make_response, redirect, render_template, request, url_for
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity, jwt_refresh_token_required, set_access_cookies, set_refresh_cookies, unset_jwt_cookies

from app import app, bcrypt, db, jwt_required
from models import User

@app.route('/register', methods=('GET', 'POST'))
def register():
    if get_jwt_identity():
        return redirect(url_for('index'))
    if request.method == 'POST':
        error = None
        email = request.form['email']
        password = request.form['password']
        if not email:
            error = 'Email is required'
        elif not password:
            error = 'Password is required'
        else:
            user = User.query.filter_by(email=email).first()
            if user:
                error = 'User is already registered'
        if error is None:
            try:
                user = User(email=email, password=password)
                db.session.add(user)
                db.session.commit()
                return redirect(url_for('login'))
            except Exception:
                error = 'Failed to register user'
        flash(error)
        return redirect(url_for('register'))
    else:
        return render_template('auth/register.html')

@app.route('/login', methods=('GET', 'POST'))
def login():
    if get_jwt_identity():
        return redirect(url_for('index'))
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, request.form['password']):
            response = redirect(url_for('index'))
            set_access_cookies(response, create_access_token(identity=email))
            set_refresh_cookies(response, create_refresh_token(identity=email))
            return response
        else:
            flash('Incorrect email or password')
            return redirect(url_for('login'))
    else:
        return render_template('auth/login.html')

@app.route('/logout', methods=('GET',))
def logout():
    response = redirect(url_for('index'))
    unset_jwt_cookies(response)
    return response

@app.route('/refresh', methods=('GET',))
@jwt_refresh_token_required
def refresh():
    email = get_jwt_identity()
    response = redirect(url_for('index'))
    set_access_cookies(response, create_access_token(identity=email))
    return response

@app.route('/')
@jwt_required
def index():
    email = get_jwt_identity()
    if email:
        return render_template('index.html', email=email)
    else:
        return redirect(url_for('login'))
