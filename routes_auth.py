# routes_auth.py
from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_db
import models

# Create a Blueprint named 'auth'
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    # If already logged in, kick them to the home page
    if 'user_id' in session:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        consent = request.form.get('consent')

        if not username or not password:
            flash('Username and password are required.', 'error')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Password do not match. Please try again.', 'error')
            return render_template('register.html')
        
        if len(password) < 8:
            flash('Password must be at least 8 characters.', 'error')
            return render_template('register.html')
        
        if not consent:
            flash('You must accept the terms to register.', 'error')
            return render_template('register.html')
        
        password_hash = generate_password_hash(password)
        user = models.create_user(get_db(), username, password_hash)

        if user is None:
            flash('Username is already taken.', 'error')
            return render_template('register.html')
        
        session['user_id'] = user['id']
        session['username'] = user['username']

        # Fetch the starting balance so the navbar updates instantly
        session['token_balance'] = models.get_token_balance(get_db(), user['id'])

        return redirect(url_for('main.index'))

    return render_template('register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # If already logged in, kick them to the home page
    if 'user_id' in session:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            flash('Username and password are required.', 'error')
            return render_template('login.html')
        
        user = models.get_user_by_username(get_db(), username)

        if user is None or not check_password_hash(user['password_hash'], password):
            flash('Incorrect username or password.', 'error')
            return render_template('login.html')
        
        session['user_id'] = user['id']
        session['username'] = user['username']

        # Fetch and save the token balance to the session
        session['token_balance'] = models.get_token_balance(get_db(), user['id'])

        return redirect(url_for('main.index'))
    
    return render_template('login.html')


@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.index'))