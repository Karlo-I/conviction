# app.py
# Conviction: Flask application entry point and route definitions.
# AI assistance: Claude (Anthropic) assisted with Flask structure and route scaffolding.
# Logic, decisions, and direction are the author's own.

import click
import models
import os
import sqlite3
from flask import current_app, flash, Flask, g, render_template, redirect, request, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
DATABASE = 'conviction.db'


# open db connection and store in g
# if db connection don't already exist, create one and store in g
def get_db(): 
    if 'db' not in g:
        g.db = sqlite3.connect(
            DATABASE,
            # TIMESTAMP values come back as Python datetime object rather than raw string
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        # without this line, SQLite simply returns rows as plain tuples: row[0], row[1], instead of dictinaries: row['username'], row['token_balance']
        g.db.row_factory = sqlite3.Row
    return g.db


# Runs automatically after every request to close the database connection if one was opened
# Registered via @app.teardown_appcontext; connects to get_db and Flask's rquest lifecycle
@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        db.close()


# CLI command to initialise the database by executing schema.sql
# Run once with 'flask --app app init-db' in terminal; connects to schema.sql and get_db
@app.cli.command('init-db')
def init_db():
    db = get_db()
    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))
    click.echo('Database initialised.')


## ROUTES ##

# Renders the landing page
# Passes no data to the template - index.html extends layout.html directly
@app.route('/')
def index():
    return render_template('index.html')


# Registers a new user: validates from input, hashes password, creates user and session
# Calls models.create_user and get_db; on success writes to session and redirects to index
@app.route('/register', methods=['GET', 'POST'])
def register():
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
        return redirect(url_for('index'))

    return render_template('register.html')


# Authenticates an existing user: checks username and password agaisnt the database
# Calls models.get_user_by_username and get_db; on success writes to session and redirects to index
@app.route('/login', methods=['GET', 'POST'])
def login():
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
        session['userame'] = user['username']
        return redirect(url_for('index'))
    
    return render_template('login.html')


# Clears the session cookie, effectively logging the user out
# No database interaction - session state lives in the cookie, not the database
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


# Renders the lens for a given slug (food, housing, mobility)
# Calls models.get_lens_by_slug and models.get_issues_by_lens; passes data to lens.html
@app.route('/lens/<slug>')
def lens(slug):
    db = get_db()
    lens = models.get_lens_by_slug(db, slug)

    if lens is None:
        return redirect(url_for('index'))
    
    rows = models.get_issues_by_lens(db, lens['id'])

    # Group data points by issue
    issues = {}
    for row in rows:
        issue_slug = row['slug']
        if issue_slug not in issues:
            issues[issue_slug] = {
                'issue_id': row['id'],
                'title': row['title'],
                'description': row['description'],
                'indicator_name': row['indicator_name'],
                'unit': row['unit'],
                'data_points': []
            }
        if row['country_code']:
            issues[issue_slug]['data_points'].append({
                'country': row['country_code'],
                'year': row['year'],
                'value': round(row['value'], 1)
            })
    
    return render_template('lens.html', lens=lens, issues=issues)
    

# Handles token spend on an issue - checks balance, writes ledger, redirects to lens
# Calls models.get_token_balance, models.add_token_transactions; requires login
@app.route('/spend', methods=['POST'])
def spend():
    if 'user_id' not in session:
        flash('You need to be logged in to spend tokens.', 'error')
        return redirect(url_for('login'))
    
    db = get_db()
    user_id = session['user_id']
    issue_id = request.form.get('issue_id', type=int)
    lens_slug = request.form.get('lens_slug', '')

    if not issue_id or not lens_slug:
        flash('Invalid request.', 'error')
        return redirect(url_for('index'))
    
    balance = models.get_token_balance(db, user_id)

    if balance < 1:
        flash('Insufficient tokens', 'error')
        return redirect(url_for('lens', slug=lens_slug))
    
    models.add_token_transactions(db, user_id, -1, 'spend', issue_id=issue_id)
    flash('Token spent.', 'success')
    return redirect(url_for('lens', slug=lens_slug))

# IMPORTANT: Delete these two lines when the project moves to PROD
if __name__ == '__main__':
    app.run(debug=True)
