# routes_lens.py
from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from db import get_db
import models
from models import add_issue_comment

# Create a Blueprint named 'lens'
lens_bp = Blueprint('lens', __name__)


# Renders the lens for a given slug (food, housing, mobility)
# Calls models.get_lens_by_slug and models.get_issues_by_lens; passes data to lens.html
@lens_bp.route('/lens/<slug>')
def lens(slug):
    db = get_db()
    lens_data = models.get_lens_by_slug(db, slug)

    if lens_data is None:
        return redirect(url_for('index'))
    
    issues = models.get_issues_with_data(db, lens_data['id'])    
    forces = models.get_forces_for_lens(db, lens_data['id'])
    approved_contributions = models.get_approved_contributions_for_lens(db, lens_data['id'])

    return render_template('lens.html', lens=lens_data, issues=issues, forces=forces, approved_contributions=approved_contributions)


# Handle comment submissions for issues
@lens_bp.route('/issue/<int:issue_id>/comment', methods=['POST'])
def add_issue_comment_route(issue_id):
    if 'user_id' not in session:
        flash('You must be logged in to comment.', 'error')
        return redirect(url_for('auth.login'))
    
    db = get_db()
    
    # Validate issue exists and get lens_slug for redirect
    issue = db.execute(
        '''
        SELECT i.id, l.slug 
        FROM issues i
        JOIN lenses l ON i.lens_id = l.id
        WHERE i.id = ?
        ''',
        (issue_id,)
    ).fetchone()
    
    if not issue:
        flash('Issue not found.', 'error')
        return redirect(url_for('index'))
    
    lens_slug = issue['slug']
    
    comment = request.form.get('comment', '').strip()
    source_url = request.form.get('source_url', '').strip() or None
    parent_comment_id = request.form.get('parent_comment_id')
    
    # Convert parent_comment_id to int if provided, otherwise None
    if parent_comment_id:
        parent_comment_id = int(parent_comment_id)
    else:
        parent_comment_id = None
    
    if not comment:
        flash('Comment cannot be empty.', 'error')
        return redirect(url_for('lens.lens', slug=lens_slug) + f'#issue-{issue_id}')
    
    # Enforce one-level threading: if replying, verify parent has no parent
    if parent_comment_id:
        parent = db.execute(
            'SELECT parent_comment_id FROM issue_comments WHERE id = ?',
            (parent_comment_id,)
        ).fetchone()
        
        if not parent or parent['parent_comment_id'] is not None:
            flash('Cannot reply to a reply. Please reply to a top-level comment.', 'error')
            return redirect(url_for('lens.lens', slug=lens_slug) + f'#issue-{issue_id}')
    
    add_issue_comment(
        db, 
        issue_id, 
        session['user_id'], 
        comment, 
        source_url, 
        parent_comment_id
    )
        
    return redirect(url_for('lens.lens', slug=lens_slug) + f'#issue-{issue_id}')


# Handles token spend on an issue - checks balance, writes ledger, redirects to lens
# Calls models.get_token_balance, models.add_token_transactions; requires login
@lens_bp.route('/spend', methods=['POST'])
def spend():
    if 'user_id' not in session:
        flash('You need to be logged in to spend tokens.', 'error')
        return redirect(url_for('auth.login'))
    
    db = get_db()
    user_id = session['user_id']
    contribution_id = request.form.get('contribution_id', type=int)
    lens_slug = request.form.get('lens_slug', '')

    if not contribution_id or not lens_slug:
        flash('Invalid request.', 'error')
        return redirect(url_for('index'))
    
    # Check balance
    balance = models.get_token_balance(db, user_id)
    if balance < 1:
        flash('Insufficient tokens', 'error')
        return redirect(url_for('lens.lens', slug=lens_slug))
    
    # Verify the contribution exists, is approved, and belongs to this lens
    contribution = db.execute(
        '''
        SELECT c.id, c.country_code, l.slug as lens_slug
        FROM contributions c
        JOIN contribution_lens_links cll ON c.id = cll.contribution_id
        JOIN issues i ON cll.issue_id = i.id
        JOIN lenses l ON i.lens_id = l.id
        WHERE c.id = ? AND l.slug = ? AND c.status = 'approved'
        ''',
        (contribution_id, lens_slug)
    ).fetchone()

    if contribution is None:
        flash('Invalid contribution.', 'error')
        return redirect(url_for('index'))
    
    # Double-check balance right before transaction to prevent race conditions
    current_balance = models.get_token_balance(db, user_id)
    if current_balance < 1:
        flash('Insufficient tokens', 'error')
        return redirect(url_for('lens.lens', slug=lens_slug))
    
    # Record the spend against the specific contribution
    models.add_token_transactions(db, user_id, -1, 'spend', contribution_id=contribution_id)

    # Re-sync the session with the actual database ledger
    session['token_balance'] = models.reconcile_token_balance(db, user_id)
    
    # Get the issue_id from the contribution
    issue = db.execute(
        '''
        SELECT i.id FROM issues i
        JOIN contribution_lens_links cll ON cll.issue_id = i.id
        WHERE cll.contribution_id = ?
        ''',
        (contribution_id,)
    ).fetchone()
    
    flash('Token spent on this evidence.', 'success')
    return redirect(url_for('lens.lens', slug=lens_slug) + f'?issue_id={issue["id"]}#issue-{issue["id"]}')


# Handles token spend on a Force - mirrors the /spend route for issues
@lens_bp.route('/spend-force', methods=['POST'])
def spend_force():
    if 'user_id' not in session:
        flash('You need to be logged in to spend tokens.', 'error')
        return redirect(url_for('auth.login'))
    
    db = get_db()
    user_id = session['user_id']
    force_id = request.form.get('force_id', type=int)
    force_slug = request.form.get('force_slug', '')

    if not force_id or not force_slug:
        flash('Invalid request.', 'error')
        return redirect(url_for('forces'))
    
    # First check
    balance = models.get_token_balance(db, user_id)
    if balance < 1:
        flash('Insufficient tokens', 'error')
        return redirect(url_for('force_detail', slug=force_slug))
    
    # Verify the force exists
    force = db.execute(
        'SELECT id FROM forces WHERE id = ? AND slug = ?',
        (force_id, force_slug)
    ).fetchone()

    if force is None:
        flash('Invalid force.', 'error')
        return redirect(url_for('forces'))
    
    # Double-check balance right before transaction
    current_balance = models.get_token_balance(db, user_id)
    if current_balance < 1:
        flash('Insufficient tokens', 'error')
        return redirect(url_for('force_detail', slug=force_slug))
    
    models.add_token_transactions(db, user_id, -1, 'spend', force_id=force_id)

    # Re-sync the session with the actual database ledger
    session['token_balance'] = models.reconcile_token_balance(db, user_id)
    
    flash('Token spent.', 'success')
    return redirect(url_for('force_detail', slug=force_slug))