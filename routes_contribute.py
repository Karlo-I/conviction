# routes_contribute.py
from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from db import get_db
import models
from background import start_agent_thread


contribute_bp = Blueprint('contribute', __name__)


# Render contribution form on GET, validate and store submission on POST
# Calls models.get_all_indicators, models.create_contribution; requires login
@contribute_bp.route('/contribute', methods=['GET', 'POST'])
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
            return render_template('contribute.html', indicators=models.get_all_indicators(db))
        
        # The claim/observation is always required
        if not note:
            flash('Claim or observation is required.', 'error')
            return render_template('contribute.html', indicators=models.get_all_indicators(db))

        # If it's a lens proposal, we don't have a country code. 
        # The database schema requires a string, so we pass 'GLOBAL'.
        if contribution_type == 'lens_proposal':
            country_code = 'GLOBAL'

        try:
            if indicator_id:
                indicator_id = int(indicator_id)
        except ValueError:
            flash('Invalid indicator submitted.', 'error')
            return render_template('contribute.html', indicators=models.get_all_indicators(db))

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

        return redirect(url_for('contribute.contribute_confirm', contribution_id=contribution_id))

    return render_template('contribute.html', indicators=models.get_all_indicators(db))


# Renders the contribution confirmation page with the AI digest
# Calls models.get_contribution_with_digest; contribution_id comes from the URL
@contribute_bp.route('/contribute/confirm/<int:contribution_id>')
def contribute_confirm(contribution_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    db = get_db()
    contribution = models.get_contribution_with_digest(db, contribution_id)

    if contribution is None:
        return redirect(url_for('main.index')) # Updated to use main blueprint

    is_owner = contribution['user_id'] == session['user_id']
    my_source = None if is_owner else models.get_contributor_source(db, contribution_id, session['user_id'])

    if not is_owner and my_source is None:
        return redirect(url_for('main.index')) # Updated to use main blueprint

    return render_template('contribute_confirm.html', contribution=contribution, is_owner=is_owner, my_source=my_source)