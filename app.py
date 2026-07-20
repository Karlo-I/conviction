# app.py
# Conviction: Flask application entry point and route definitions.
# AI assistance: Both Claude (Anthropic) and Qwen.ai (3.7-Plus) assisted with query structure and error handling patterns.
# Logic, decisions, and direction are the author's own.
import models
import os
import psycopg2
import secrets
from background import start_agent_thread
from db import get_db, close_db, init_db, USE_POSTGRESQL, DATABASE_URL
from dotenv import load_dotenv
from flask import abort, flash, Flask, g, render_template, redirect, request, session, url_for
from routes_auth import auth_bp
from routes_contribute import contribute_bp
from routes_forces import forces_bp
from routes_info import info_bp
from routes_lens import lens_bp
from routes_main import main_bp
from routes_quiz import quiz_bp
from routes_validate import validate_bp
from routes_visual import visual_bp


load_dotenv()

app = Flask(__name__)
app.jinja_env.globals['enumerate'] = enumerate
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
if not app.debug and os.environ.get('SECRET_KEY') is None:
    raise ValueError('SECRET_KEY environment variable is not set in production.')
app.config['SESSION_COOKIE_SECURE'] = not app.debug
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'


# Ensure application is not vulnerable to Cross-Site Request Forgery 
# or CSRF - a malicious site forcing a logged-in user to spend tokens or upvote a contribution
def generate_csrf_token():
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_hex(16)
    return session['_csrf_token']

app.jinja_env.globals['csrf_token'] = generate_csrf_token

@app.before_request
def csrf_protect():
    if request.method == 'POST':
        token = session.get('_csrf_token', None)
        if not token or token != request.form.get('_csrf_token'):
            abort(403)


# Register blueprints, database teardown, and init-db CLI command
app.register_blueprint(auth_bp)
app.register_blueprint(contribute_bp)
app.register_blueprint(forces_bp)
app.register_blueprint(info_bp)
app.register_blueprint(lens_bp)
app.register_blueprint(main_bp)
app.register_blueprint(quiz_bp)
app.register_blueprint(validate_bp)
app.register_blueprint(visual_bp)
app.teardown_appcontext(close_db)
app.cli.add_command(init_db)


# Prevent browser caching to ensure back button always shows current auth state
# Critical for security after logout
@app.after_request
def add_security_headers(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    response.headers['Surrogate-Control'] = 'no-store'
    return response


# PERMANENT ROUTE TO SEED DATABASE WITH REAL DATA
@app.route('/seed-data')
def seed_data():
    import seed
    import psycopg2
    
    db = get_db()
    
    # Check if tables exist
    tables_exist = False
    try:
        db.execute("SELECT 1 FROM users LIMIT 1")
        db.commit()
        tables_exist = True
    except Exception:
        # Important: Rollback to clear the bad transaction state
        db.rollback()
        
    if not tables_exist:
        schema_file = 'schema_postgres.sql' if USE_POSTGRESQL else 'schema.sql'
        try:
            with open(schema_file) as f:
                sql_script = f.read()
        except FileNotFoundError:
            return f"Error: {schema_file} not found!"

        if USE_POSTGRESQL:
            # Create a fresh connection
            init_conn = psycopg2.connect(DATABASE_URL)
            cursor = init_conn.cursor()
            
            # Split by semicolon and process each statement
            statements = [s.strip() for s in sql_script.split(';') if s.strip()]
            
            for statement in statements:
                # Skip ONLY if the statement is purely comments (no SQL commands)
                has_sql_command = any(keyword in statement.upper() for keyword in ['CREATE', 'INSERT', 'ALTER', 'DROP', 'SELECT'])
                
                if not has_sql_command:
                    continue
                    
                try:
                    cursor.execute(statement)
                except Exception as e:
                    init_conn.rollback()
                    init_conn.close()
                    return f"Error initializing database:<br><br>FAILED: {statement[:100]}...<br><br>Error: {str(e)}"
            
            # Commit all changes
            init_conn.commit()
            init_conn.close()
            print("✅ Database schema auto-initialized")
    
    # Now run the seed
    try:
        seed.seed_all(db, USE_POSTGRESQL)
        return "✅ Seeding complete! Your database is ready for community contributions."
    except Exception as e:
        return f"Error during seeding: {str(e)}"
    

# IMPORTANT: Delete these two lines when the project moves to PROD
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)