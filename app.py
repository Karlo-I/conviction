# app.py
# Conviction: Flask application entry point and route definitions.
# AI assistance: Claude (Anthropic) assisted with Flask structure and route scaffolding.
# Logic, decisions, and direction are the author's own.

import click
import os
import sqlite3
from flask import current_app, Flask, render_template, redirect, url_for, session, g


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


# runs automatically after every request to close the database connection if one was opened
@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        db.close()


# CLI command to initialise the database by executing schema.sql
# Run with 'flask --app app init-db' in terminal (noted in notes_app.py.md as reference)
@app.cli.command('init-db')
def init_db():
    db = get_db()
    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))
    click.echo('Database initialised.')


# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


# IMPORTANT: Delete these two lines when the project moves to PROD
if __name__ == '__main__':
    app.run(debug=True)
