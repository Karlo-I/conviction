# db.py
import os
import sqlite3
import psycopg2
import click
from flask import current_app, g
from psycopg2.extras import RealDictCursor

# Database configuration between SQLite (local) and PostgreSQL (Render)
DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    # Production: PostgreSQL on Render
    DATABASE = DATABASE_URL
    USE_POSTGRESQL = True
else:
    # Development: SQLite locally
    DATABASE = 'conviction.db'
    USE_POSTGRESQL = False


# Wrapper class to make psycopg2 behave like sqlite3
class Psycopg2Wrapper:
    def __init__(self, conn):
        self.conn = conn
        
    def execute(self, query, params=None):
        # Auto-convert SQLite ? placeholders to PostgreSQL %s
        query = query.replace('?', '%s')
        # Auto-convert SQLite datetime function to PostgreSQL NOW()
        query = query.replace("datetime('now')", "NOW()")
        
        # CRITICAL FIX: Use RealDictCursor so fetchone() returns a dictionary
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        return cursor
        
    def commit(self):
        self.conn.commit()
        
    def rollback(self):
        self.conn.rollback()
        
    def close(self):
        self.conn.close()
        
    def cursor(self):
        return self.conn.cursor(cursor_factory=RealDictCursor)


def get_db(): 
    if 'db' not in g:
        if USE_POSTGRESQL:
            conn = psycopg2.connect(DATABASE)
            g.db = Psycopg2Wrapper(conn)
        else:
            g.db = sqlite3.connect(
                DATABASE,
                detect_types=sqlite3.PARSE_DECLTYPES,
                timeout=10
            )
            g.db.row_factory = sqlite3.Row
    return g.db


# Runs automatically after every request to close the database connection
def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        db.close()


# CLI command to initialise the database by executing schema.sql
@click.command('init-db')
def init_db():
    db = get_db()
    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))
    click.echo('Database initialised.')