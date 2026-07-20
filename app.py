# app.py
# Conviction: Flask application entry point and route definitions.
# AI assistance: Both Claude (Anthropic) and Qwen.ai (3.7-Plus) assisted with query structure and error handling patterns.
# Logic, decisions, and direction are the author's own.

import agent
import json
import models
import os
import psycopg2
import routes_quiz
import secrets
import threading
import viz
from background import start_agent_thread
from db import get_db, close_db, init_db, USE_POSTGRESQL, DATABASE_URL
from dotenv import load_dotenv
from flask import abort, current_app, flash, Flask, g, jsonify, render_template, redirect, request, session, url_for
from routes_auth import auth_bp
from routes_info import info_bp
from routes_lens import lens_bp


load_dotenv()

app = Flask(__name__)
app.jinja_env.globals['enumerate'] = enumerate
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
if not app.debug and os.environ.get('SECRET_KEY') is None:
    raise ValueError('SECRET_KEY environment variable is not set in production.')
app.config['SESSION_COOKIE_SECURE'] = not app.debug
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'


# Load comprehensive country data from JSON file
with open('countries.json', 'r') as f:
    COUNTRY_DATA = json.load(f)


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


# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(info_bp)
app.register_blueprint(lens_bp)


# Register database teardown
app.teardown_appcontext(close_db)


# Register the init-db CLI command
app.cli.add_command(init_db)


## ROUTES ##

# Renders the landing page and quiz during a certain timeframe
# Passes no data to the template - index.html extends layout.html directly
@app.route('/')
def index():
    db = get_db()

    # Fetch all lenses dynamically
    lenses = models.get_all_lenses(db)
    
    show_quiz_prompt = False
    quiz_button_text = "Take the Diagnostic Quiz"
    
    if 'user_id' in session:
        user_id = session['user_id']
        last_quiz = models.get_last_quiz_response(db, user_id)
        
        if last_quiz is None:
            show_quiz_prompt = True
            quiz_button_text = "Take the Diagnostic Quiz"
        else:
            if models.can_retake_quiz(db, user_id):
                show_quiz_prompt = True
                quiz_button_text = "Retake the Diagnostic Quiz"
    
    # Default values for guests
    show_quiz_prompt = False
    quiz_button_text = "Take the Diagnostic Quiz"
    
    if 'user_id' in session:
        user_id = session['user_id']
        last_quiz = models.get_last_quiz_response(db, user_id)
        
        if last_quiz is None:
            # User is logged in but has never taken the quiz
            show_quiz_prompt = True
            quiz_button_text = "Take the Diagnostic Quiz"
        else:
            # User has taken the quiz before; check if 90 days have passed
            if models.can_retake_quiz(db, user_id):
                show_quiz_prompt = True
                quiz_button_text = "Retake the Diagnostic Quiz"
            # If can_retake_quiz is False, show_quiz_prompt remains False (hidden)

    return render_template('index.html',
    lenses=lenses,
    show_quiz_prompt=show_quiz_prompt,
    quiz_button_text=quiz_button_text)


# Renders quiz on GET, scores responses and redirects to recommend lens on POST
# Calls quiz.get_questions, quiz.score_responses, models.save_quiz_response, models.can_retake_quiz
@app.route('/quiz', methods=['GET', 'POST'])
def quiz_route():
    if 'user_id' not in session:
        flash('You need to be logged in to take the quiz.', 'error')
        return redirect(url_for('auth.login'))
    
    db = get_db()
    user_id = session['user_id']

    retake_days = int(models.get_config(db, 'quiz_retake_days') or 90)
    if not models.can_retake_quiz(db, user_id, retake_days=retake_days):
        flash(f'You can retake the quiz every {retake_days} days.', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        responses = {q['id']: request.form.get(q['id']) for q in routes_quiz.get_questions()}

        if any(v is None for v in responses.values()):
            flash('Please answer all questions.', 'error')
            return render_template('quiz.html', questions=routes_quiz.get_questions())
        
        recommended_slug = routes_quiz.score_response(responses)

        if recommended_slug is None:
            flash('Invalid quiz submission. Please try again.', 'error')
            return render_template('quiz.html', questions=routes_quiz.get_questions())

        lens = models.get_lens_by_slug(db, recommended_slug)
        models.save_quiz_response(db, user_id, responses, lens['id'])

        session['recommended_lens'] = recommended_slug
        flash(f'Based on your answers, we recommend starting with the {lens["title"]} lens.', 'success')
        return redirect(url_for('lens', slug=recommended_slug))
    
    return render_template('quiz.html', questions=routes_quiz.get_questions())


# Serve the heatmap page
# Render heatmap.html - Leaflet.js fetches '/api/heatmap' separately via JavaScript
@app.route('/heatmap')
def heatmap():
    return render_template('heatmap.html', country_data=COUNTRY_DATA)


# Return aggregate token spend or least-heard data as JSON for Leaflet.js
# Calls models.get_heatmap_data or models.get_least_heard_data depending on mode perimeter
@app.route('/api/heatmap')
def heatmap_data():
    db = get_db()
    mode = request.args.get('mode', 'conviction')

    if mode == 'least_heard':
        rows = models.get_least_heard_data(db)
        data = [{'country': r['country_code'],
                 'value': r['data_coverage'],
                 'spend': r['total_spend']} for r in rows]
        
    else:
        # Conviction mode: delegates to the updated models.py function
        rows = models.get_heatmap_data(db)
        data = [{'country': r['country_code'],
                 'value': r['total_spend'],
                 'top_issue': r['top_issue_title']} for r in rows] 
                
    return jsonify({'mode': mode, 'data': data})


# Render contribution form on GET, validate and store submission on POST
# Calls models.get_all_indicators, models.create_contribution; requires login
@app.route('/contribute', methods=['GET', 'POST'])
def contribute():
    if 'user_id' not in session:
        flash('You need to be logged in to contribute.', 'error')
        return redirect(url_for('auth.login'))

    db = get_db()

    if request.method == 'POST':
        user_id = session['user_id']
        country_code = request.form.get('country_code', '').strip()
        title = request.form.get('title', '').strip() or None
        category = request.form.get('category', '').strip() or None
        note = request.form.get('note', '').strip()
        contribution_type = request.form.get('contribution_type', 'data_point')
        indicator_id = request.form.get('indicator_id') or None
        source_url = request.form.get('source_url', '').strip() or None
        source_excerpt = request.form.get('source_excerpt', '').strip() or None

        # Country is only required if it's NOT a lens proposal
        if contribution_type != 'lens_proposal' and not country_code:
            flash('Country is required.', 'error')
            return render_template('contribute.html',
                                   indicators=models.get_all_indicators(db))
            
        # The claim/observation is always required
        if not note:
            flash('Claim or observation is required.', 'error')
            return render_template('contribute.html',
                                   indicators=models.get_all_indicators(db))

        # If it's a lens proposal, we don't have a country code. 
        # The database schema requires a string, so we pass 'GLOBAL'.
        if contribution_type == 'lens_proposal':
            country_code = 'GLOBAL'

        try:
            if indicator_id:
                indicator_id = int(indicator_id)
        except ValueError:
            flash('Invalid indicator submitted.', 'error')
            return render_template('contribute.html',
                                   indicators=models.get_all_indicators(db))

        contribution = models.create_contribution(
            db, user_id, country_code, note,
            contribution_type=contribution_type,
            indicator_id=indicator_id,
            source_url=source_url,
            source_excerpt=source_excerpt,
            title=title,
            category=category
        )

        contribution_id = contribution['id']

        # Start the AI agent in a background thread
        start_agent_thread(contribution_id)

        return redirect(url_for('contribute_confirm', contribution_id=contribution_id))

    return render_template('contribute.html',
                           indicators=models.get_all_indicators(db))


# Renders the contribution confirmation page with the AI digest
# Calls models.get_contribution_with_digest; contribution_id comes from the URL
@app.route('/contribute/confirm/<int:contribution_id>')
def contribute_confirm(contribution_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    db = get_db()
    contribution = models.get_contribution_with_digest(db, contribution_id)

    if contribution is None:
        return redirect(url_for('index'))

    is_owner = contribution['user_id'] == session['user_id']
    my_source = None if is_owner else models.get_contributor_source(db, contribution_id, session['user_id'])

    if not is_owner and my_source is None:
        return redirect(url_for('index'))

    return render_template('contribute_confirm.html', contribution=contribution, is_owner=is_owner, my_source=my_source)


# Render the peer validation queue with pending contributions and their digests
# Calls models.get_pending_contributions; requires login
@app.route('/validate')
def validate():
    if 'user_id' not in session:
        flash('You need to be logged in to validate contributions.', 'error')
        return redirect(url_for('auth.login'))

    db = get_db()
    user_id = session['user_id']
    
    # Only get contributions the user hasn't voted on yet
    contributions = models.get_pending_contributions_for_user(db, user_id)
    
    for c in contributions:
        if c['contribution_type'] == 'force_claim':
            c['source_count'] = models.get_source_count(db, c['id'])
    
    return render_template('validate.html', contributions=contributions)


# Handle a validator's approve/reject vote on a contribution
# Calls models.cast_vote, models.get_vote_count, models.process_vote_logic, models.approve_contribution; checks threshold
@app.route('/validate/<int:contribution_id>', methods=['POST'])
def cast_vote(contribution_id):
    if 'user_id' not in session:
        flash('You need to be logged in to vote.', 'error')
        return redirect(url_for('auth.login'))
    
    db = get_db()
    user_id = session['user_id']
    vote = request.form.get('vote')

    if vote not in ('approve', 'reject'):
        flash('Invalid vote.', 'error')
        return redirect(url_for('validate'))
    
    contribution = db.execute(
        'SELECT * FROM contributions WHERE id = ?', (contribution_id,)
    ).fetchone()

    if contribution is None or contribution['status'] != 'pending':
        flash('This contribution is no longer pending.', 'error')
        return redirect(url_for('validate'))
    
    if contribution['user_id'] == user_id:
        flash('You cannot validate your own contribution.', 'error')
        return redirect(url_for('validate'))
    
    success = models.cast_vote(db, contribution_id, user_id, vote)

    if not success:
        flash('You have already voted on this contribution.', 'error')
        return redirect(url_for('validate'))

    tokens_per_validation = int(models.get_config(db, 'tokens_per_validation') or 1)
    models.add_token_transactions(db, user_id, tokens_per_validation, 'validation')
    
    # Immediately update the session so the UI doesn't lag!
    session['token_balance'] = models.reconcile_token_balance(db, user_id)

    # Delegate all threshold logic to models.py ---
    message = models.process_vote_logic(db, contribution, user_id, vote)
    flash(message, 'success')

    return redirect(url_for('validate'))


# Return real-time vote counts for a specific contribution
# Called by validate.html JavaScript to update approval/rejection badges
@app.route('/api/vote-counts/<int:contribution_id>')
def vote_counts(contribution_id):
    db = get_db()
    
    # Get counts
    approve_count = models.get_vote_count(db, contribution_id, 'approve')
    reject_count = models.get_vote_count(db, contribution_id, 'reject')
    
    # Get the contribution status (in case it was just approved/rejected)
    contribution = db.execute(
        'SELECT status FROM contributions WHERE id = ?', 
        (contribution_id,)
    ).fetchone()
    
    return jsonify({
        'approve': approve_count,
        'reject': reject_count,
        'status': contribution['status'] if contribution else 'unknown'
    })


@app.route('/forces')
def forces():
    db = get_db()
    all_forces = models.get_all_forces(db)

    grouped = {}
    for f in all_forces:
        grouped.setdefault(f['category'], []).append(f)

    return render_template('forces.html', grouped_forces=grouped)


@app.route('/force/<slug>')
def force_detail(slug):
    db = get_db()
    force = models.get_force_by_slug(db, slug)

    if force is None:
        return redirect(url_for('forces'))
    
    return render_template('force.html', force=force)


# Zoomable sunburst
@app.route('/api/sunburst')
def sunburst_data():
    db = get_db()
    # Return a JSON string 
    json_data = viz.get_sunburst_data(db)
    return json_data, 200, {'Content-Type': 'application/json'}


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