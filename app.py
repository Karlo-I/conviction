# app.py
# Conviction: Flask application entry point and route definitions.
# AI assistance: Claude (Anthropic) assisted with Flask structure and route scaffolding.
# Logic, decisions, and direction are the author's own.

import agent
import click
import models
import os
import quiz
import secrets
import sqlite3
import threading
from dotenv import load_dotenv
from flask import abort, current_app, flash, Flask, g, jsonify, render_template, redirect, request, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()

app = Flask(__name__)
app.jinja_env.globals['enumerate'] = enumerate
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
if not app.debug and os.environ.get('SECRET_KEY') is None:
    raise ValueError('SECRET_KEY environment variable is not set in production.')
app.config['SESSION_COOKIE_SECURE'] = not app.debug
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'


COUNTRY_DATA = {
    'KEN': {'name': 'Kenya', 'lat': -1.286389, 'long': 36.817223},
    'NGA': {'name': 'Nigeria', 'lat': 9.057990, 'long': 7.495080},
    'ZAF': {'name': 'South Africa', 'lat': -30.559482, 'long': 22.937506},
    'EGY': {'name': 'Egypt', 'lat': 26.820553, 'long': 30.802498},
    'PHL': {'name': 'Philippines', 'lat': 12.879721, 'long': 121.774017},
    'IND': {'name': 'India', 'lat': 20.593684, 'long': 78.962880},
    'BGD': {'name': 'Bangladesh', 'lat': 23.684994, 'long': 90.356331},
    'THA': {'name': 'Thailand', 'lat': 15.870032, 'long': 100.992541},
    'MEX': {'name': 'Mexico', 'lat': 23.634501, 'long': -102.552784},
    'BRA': {'name': 'Brazil', 'lat': -14.235004, 'long': -51.925280},
    'COL': {'name': 'Colombia', 'lat': 4.570868, 'long': -74.297333},
    'CAN': {'name': 'Canada', 'lat': 56.130366, 'long': -106.346771},
    'GBR': {'name': 'United Kingdom', 'lat': 55.378051, 'long': -3.435973},
    'AUS': {'name': 'Australia', 'lat': -25.274398, 'long': 133.775136},
    'NOR': {'name': 'Norway', 'lat': 60.472024, 'long': 8.468946}
}


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


# open db connection and store in g
# if db connection don't already exist, create one and store in g
DATABASE = 'conviction.db'
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
        session['username'] = user['username']
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
    
    issues = models.get_issues_with_data(db, lens['id'])    
    forces = models.get_forces_for_lens(db, lens['id'])
    return render_template('lens.html', lens=lens, issues=issues, forces=forces)
    

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
    
    # Prevent a malicious user from intercepting POST request and change the issue_id 
    # to an issue in a different lens, or an ID that doesn't exist, corrupting the ledger
    issue = db.execute(
        '''
        SELECT i.id FROM issues i
        JOIN lenses l ON i.lens_id = l.id
        WHERE i.id = ? AND l.slug = ?
        ''',
        (issue_id, lens_slug)
    ).fetchone()

    if issue is None:
        flash('Invalid issue.', 'error')
        return redirect(url_for('index'))
    
    models.add_token_transactions(db, user_id, -1, 'spend', issue_id=issue_id)
    flash('Token spent.', 'success')
    return redirect(url_for('lens', slug=lens_slug))


# Renders quiz on GET, scores responses and redirects to recommend lens on POST
# Calls quiz.get_questions, quiz.score_responses, models.save_quiz_response, models.can_retake_quiz
@app.route('/quiz', methods=['GET', 'POST'])
def quiz_route():
    if 'user_id' not in session:
        flash('You need to be logged in to take the quiz.', 'error')
        return redirect(url_for('login'))
    
    db = get_db()
    user_id = session['user_id']

    retake_days = int(models.get_config(db, 'quiz_retake_days') or 90)
    if not models.can_retake_quiz(db, user_id, retake_days=retake_days):
        flash(f'You can retake the quiz every {retake_days} days.', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        responses = {q['id']: request.form.get(q['id']) for q in quiz.get_questions()}

        if any(v is None for v in responses.values()):
            flash('Please answer all questions.', 'error')
            return render_template('quiz.html', questions=quiz.get_questions())
        
        recommended_slug = quiz.score_response(responses)

        if recommended_slug is None:
            flash('Invalid quiz submission. Please try again.', 'error')
            return render_template('quiz.html', questions=quiz.get_questions())

        lens = models.get_lens_by_slug(db, recommended_slug)
        models.save_quiz_response(db, user_id, responses, lens['id'])

        session['recommended_lens'] = recommended_slug
        flash(f'Based on your answers, we recommend starting with the {lens["title"]} lens.', 'success')
        return redirect(url_for('lens', slug=recommended_slug))
    
    return render_template('quiz.html', questions=quiz.get_questions())


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
        rows = models.get_heatmap_data(db)
        data = [{'country': r['country_code'],
                 'value': r['total_spend']} for r in rows]
        
    return jsonify({'mode': mode, 'data': data})


# Render contribution form on GET, validate and store submission on POST
# Calls models.get_all_indicators, models.create_contribution; requires login
@app.route('/contribute', methods=['GET', 'POST'])
def contribute():
    if 'user_id' not in session:
        flash('You need to be logged in to contribute.', 'error')
        return redirect(url_for('login'))

    db = get_db()

    if request.method == 'POST':
        user_id = session['user_id']
        country_code = request.form.get('country_code', '').strip()
        title = request.form.get('title', '').strip() or None
        category = request.form.get('category', '').strip() or None
        note = request.form.get('note', '').strip()
        contribution_type = request.form.get('contribution_type', 'data_point')
        indicator_id = request.form.get('indicator_id') or None
        value = request.form.get('value') or None
        source_url = request.form.get('source_url', '').strip() or None
        source_excerpt = request.form.get('source_excerpt', '').strip() or None

        if not country_code or not note:
            flash('Country and claim are required.', 'error')
            return render_template('contribute.html',
                                   indicators=models.get_all_indicators(db))

        try:
            if indicator_id:
                indicator_id = int(indicator_id)
            if value:
                value = float(value)
        except ValueError:
            flash('Invalid value submitted. Please enter a number', 'error')
            return render_template('contribute.html',
                                   indicators=models.get_all_indicators(db))

        contribution = models.create_contribution(
            db, user_id, country_code, note,
            contribution_type=contribution_type,
            indicator_id=indicator_id,
            value=value,
            source_url=source_url,
            source_excerpt=source_excerpt,
            title=title,
            category=category
        )

        contribution_id = contribution['id']

        if contribution['contribution_type'] == 'force_claim' and contribution['status'] == 'approved':
            models.elevate_force_claim(db, contribution['id'])

        def run_agent_background(contrib_id):
            import sqlite3
            # We MUST create a new database connection for the background thread.
            # SQLite connections cannot be safely shared across threads.
            bg_db = sqlite3.connect(DATABASE)
            bg_db.row_factory = sqlite3.Row
            try:
                agent.run_agent(bg_db, contrib_id)
            finally:
                bg_db.close()

        thread = threading.Thread(target=run_agent_background, args=(contribution_id,))
        thread.start()

        return redirect(url_for('contribute_confirm', contribution_id=contribution_id))

    return render_template('contribute.html',
                           indicators=models.get_all_indicators(db))


# Renders the contribution confirmation page with the AI digest
# Calls models.get_contribution_with_digest; contribution_id comes from the URL
@app.route('/contribute/confirm/<int:contribution_id>')
def contribute_confirm(contribution_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

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
        return redirect(url_for('login'))

    db = get_db()
    contributions = [dict(c) for c in models.get_pending_contributions(db)]
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
        return redirect(url_for('login'))
    
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

    # --- NEW: Delegate all threshold logic to models.py ---
    message = models.process_vote_logic(db, contribution, user_id, vote)
    flash(message, 'success')

    return redirect(url_for('validate'))


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


@app.route('/privacy')
def privacy():
    return render_template('privacy.html')


@app.route('/terms')
def terms():
    return render_template('terms.html')


@app.route('/how_it_works')
def how_it_works():
    return render_template('how_it_works.html')


# IMPORTANT: Delete these two lines when the project moves to PROD
if __name__ == '__main__':
    app.run(debug=True)
