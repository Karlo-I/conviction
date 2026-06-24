# models.py
# Conviction: database interaction functions.
# All SQL queries live here. app.py calls these functions; it never writes SQL directly.
# AI assistance: Claude (Anthropic) assisted with query structure and error handling patterns.
# Logic, decisions, and direction are the author's own.

import sqlite3
import json
from datetime import datetime, timezone


## USER FUNCTIONS ##

# Insert a new user row and log the 10-token registration transaction
# Called by app.py register route; writes to users and token_transactions in schema.sql
def create_user(db, username, password_hash):
    """Insert a new user and award opening token transaction"""
    try:
        db.execute(
            '''
            INSERT INTO users (username, password_hash) 
            VALUES (?, ?)
            ''',
            (username, password_hash)
        )
        db.commit()
        user = get_user_by_username(db, username)
        db.execute(
            '''
            INSERT INTO token_transactions (user_id, amount, reason) 
            VALUES (?, ?, ?)
            ''',
            (user['id'], 10, 'registration')
        )
        db.commit()
        return user
    # if user registers with a username that already exists, the INSERT fails and raises this error
    # except handle the failure gracefully by returning None and without the app crashing
    except sqlite3.IntegrityError:
        return None
    

# Fetch a single user row by username, or None if not found
# Called by create_user above and by app.py login route to verify credentials
def get_user_by_username(db, username):
    """Return a single user row or None"""
    return db.execute(
        'SELECT * FROM users WHERE username = ?', 
        (username,)
    ).fetchone()


# Fetch a single user row by id, or None if not found
# Called by app.py on authenticated requests where session holds user_id, not username
def get_user_by_id(db, user_id):
    """Return a single user row or None"""
    return db.execute(
        'SELECT * FROM users WHERE id = ?', 
        (user_id,)
    ).fetchone()


## TOKEN FUNCTIONS ##

# Recalculate balance by summing the token_transactions ledger for this user
# Used as a reconciliation check; app.py displays token_balance cache from users table
def get_token_balance(db, user_id):
    """Derive balance from ledger - never trust the cached value alone"""
    result = db.execute(
        'SELECT SUM(amount) as balance FROM token_transactions WHERE user_id = ?', 
        (user_id,)
    ).fetchone()
    return result['balance'] or 0


# Append a row to the token_transactions table ledger and update the token_balance cache on users
# Called by app.py whenever tokens are earned or spent; issue_id populated only when reason='spend'
def add_token_transactions(db, user_id, amount, reason, issue_id=None):
    """Append a token movement to the ledger and update the cached balance"""
    db.execute(
        '''
        INSERT INTO token_transactions (user_id, amount, reason, issue_id) 
        VALUES (?, ?, ?, ?)
        ''', 
        (user_id, amount, reason, issue_id)
    )
    db.execute(
        'UPDATE users SET token_balance = token_balance + ? WHERE id = ?', 
        (amount, user_id)
    )
    db.commit()


## CONTRIBUTIONS FUNCTIONS ##

# Insert a new contribution row with status defaulting to 'pending'
# Called by app.py contribute route; contribution_type routes approval logic in future validate flow
def create_contribution(db, user_id, country_code, note, contribution_type='data_point',
                        indicator_id=None, value=None, source_url=None, source_excerpt=None):
    """Insert a new contribution with pending status"""
    db.execute(
        '''
        INSERT INTO contributions 
        (user_id, indicator_id, country_code, value, note, source_url, source_excerpt, contribution_type) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''',
        (user_id, indicator_id, country_code, value, note, source_url, source_excerpt, contribution_type)
    )
    db.commit()


# Return all pending contributions joined with submitter username, newest first
# Called by app.py validate route to populate the peer validation queue in validate.html
def get_pending_contributions(db):
    """Return all contributions awaiting validation, newest first"""
    return db.execute(
        '''
        SELECT c.*, u.username
        FROM contributions c
        JOIN users u ON c.user_id = u.id
        WHERE c.status = 'pending'
        ORDER BY c.created_at DESC
        '''
    ).fetchall()


# Return a single contribution row joined with sumbitter username
# Called by app.py when loading a specific contribution for validation or display
def get_contribution_by_id(db, contribution_id):
    """Return a single contribution with its submitter's username"""
    return db.execute(
        '''
        SELECT c.*, u.username
        FROM contributions c
        JOIN users u ON c.user_id = u.id
        WHERE c.id = ?''',
        (contribution_id,)
    ).fetchone()


## QUIZ FUNCTIONS ##

# Serialize responses dict to JSON and store against user_id or session_id
# Called by app.py quiz route after scoring; feeds can_retake_quiz and lens personalisation
def save_quiz_response(db, user_id, responses, recommend_lens_id, session_id=None):
    """Store quiz result against user or session"""
    db.execute(
        '''
        INSERT INTO quiz_responses (user_id, session_id, responses, recommended_lens_id)
        VALUES (?, ?, ?, ?)
        ''',
        # json.dumps(responses) used since responses is a Python dict that needs to be serialized into a JSON string before storing in SQLite
        (user_id, session_id, json.dumps(responses), recommend_lens_id)
    )
    db.commit()


# Return the most recent quiz_responses row for this user
# Called directly by can_retake_quiz function below; result used to enforce the 90-day retake gate
def get_last_quiz_response(db, user_id):
    """Return the most recent quiz response for a user"""
    return db.execute(
        '''
        SELECT * FROM quiz_responses
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT 1
        ''',
        (user_id,)
    ).fetchone()


# Compare days elapsed since last quiz against retake days threshold, return True if eligible
# Called by app.py quiz route; retake_days should be read from platform_config via get_config function below
def can_retake_quiz(db, user_id, retake_days=90):
    """Return True if enough days have passed since last quiz"""
    last = get_last_quiz_response(db, user_id)
    if not last:
        return True
    last_date = datetime.fromisoformat(last['created_at']).replace(tzinfo=timezone.utc)
    delta = datetime.now(timezone.utc) - last_date
    return delta.days >= retake_days


## PLATFORM CONFIG #

# Return a single value from platform_config by key, or None if not found
# Called throughout app.py and models.py wherever behaviour is governed by platform_config rows as shown in schemas.sql
def get_config(db, key):
    """Retrieve a single config value by key"""
    result = db.execute(
        'SELECT value FROM platform_config WHERE key = ?', (key,)
    ).fetchone()
    return result['value'] if result else None
