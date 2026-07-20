# routes_forces.py
from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from db import get_db
import models

# Create a Blueprint named 'forces'
forces_bp = Blueprint('forces', __name__)


@forces_bp.route('/forces')
def forces():
    db = get_db()
    all_forces = models.get_all_forces(db)

    grouped = {}
    for f in all_forces:
        grouped.setdefault(f['category'], []).append(f)

    return render_template('forces.html', grouped_forces=grouped)


@forces_bp.route('/force/<slug>')
def force_detail(slug):
    db = get_db()
    force = models.get_force_by_slug(db, slug)

    if force is None:
        return redirect(url_for('forces.forces'))
    
    return render_template('force.html', force=force)

# Handles token spend on a Force - mirrors the /spend route for issues
@forces_bp.route('/spend-force', methods=['POST'])
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
        return redirect(url_for('forces.forces'))
    
    # First check
    balance = models.get_token_balance(db, user_id)
    if balance < 1:
        flash('Insufficient tokens', 'error')
        return redirect(url_for('forces.force_detail', slug=force_slug))
    
    # Verify the force exists
    force = db.execute(
        'SELECT id FROM forces WHERE id = ? AND slug = ?',
        (force_id, force_slug)
    ).fetchone()

    if force is None:
        flash('Invalid force.', 'error')
        return redirect(url_for('forces.forces'))
    
    # Double-check balance right before transaction
    current_balance = models.get_token_balance(db, user_id)
    if current_balance < 1:
        flash('Insufficient tokens', 'error')
        return redirect(url_for('forces.force_detail', slug=force_slug))
    
    models.add_token_transactions(db, user_id, -1, 'spend', force_id=force_id)

    # Re-sync the session with the actual database ledger
    session['token_balance'] = models.reconcile_token_balance(db, user_id)
    
    flash('Token spent.', 'success')
    return redirect(url_for('forces.force_detail', slug=force_slug))