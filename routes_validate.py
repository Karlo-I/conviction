# routes_validate.py
from flask import Blueprint, flash, jsonify, redirect, render_template, request, session, url_for
from db import get_db
import models

# Create a Blueprint named 'validate'
validate_bp = Blueprint('validate', __name__)


# Render the peer validation queue with pending contributions and their digests
# Calls models.get_pending_contributions; requires login
@validate_bp.route('/validate')
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
@validate_bp.route('/validate/<int:contribution_id>', methods=['POST'])
def cast_vote(contribution_id):
    if 'user_id' not in session:
        flash('You need to be logged in to vote.', 'error')
        return redirect(url_for('auth.login'))
    
    db = get_db()
    user_id = session['user_id']
    vote = request.form.get('vote')

    if vote not in ('approve', 'reject'):
        flash('Invalid vote.', 'error')
        return redirect(url_for('validate.validate'))
    
    contribution = db.execute(
        'SELECT * FROM contributions WHERE id = ?', (contribution_id,)
    ).fetchone()

    if contribution is None or contribution['status'] != 'pending':
        flash('This contribution is no longer pending.', 'error')
        return redirect(url_for('validate.validate'))
    
    if contribution['user_id'] == user_id:
        flash('You cannot validate your own contribution.', 'error')
        return redirect(url_for('validate.validate'))
    
    success = models.cast_vote(db, contribution_id, user_id, vote)

    if not success:
        flash('You have already voted on this contribution.', 'error')
        return redirect(url_for('validate.validate'))

    tokens_per_validation = int(models.get_config(db, 'tokens_per_validation') or 1)
    models.add_token_transactions(db, user_id, tokens_per_validation, 'validation')
    
    # Immediately update the session so the UI doesn't lag!
    session['token_balance'] = models.reconcile_token_balance(db, user_id)

    # Delegate all threshold logic to models.py
    message = models.process_vote_logic(db, contribution, user_id, vote)
    flash(message, 'success')

    return redirect(url_for('validate.validate'))


# Return real-time vote counts for a specific contribution
# Called by validate.html JavaScript to update approval/rejection badges
@validate_bp.route('/api/vote-counts/<int:contribution_id>')
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