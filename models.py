# models.py
# Conviction: database interaction functions.
# All SQL queries live here. app.py calls these functions; it never writes SQL directly.
# AI assistance: Claude (Anthropic) assisted with query structure and error handling patterns.
# Logic, decisions, and direction are the author's own.

import json
import re
import sqlite3
from datetime import datetime, timezone


## USER FUNCTIONS ##

def create_user(db, username, password_hash):
    try:
        db.execute(
            'INSERT INTO users (username, password_hash) VALUES (?, ?)',
            (username, password_hash)
        )
        user = db.execute(
            'SELECT * FROM users WHERE username = ?', (username,)
        ).fetchone()
        db.execute(
            'INSERT INTO token_transactions (user_id, amount, reason) VALUES (?, ?, ?)',
            (user['id'], 10, 'registration')
        )
        db.commit()
        return user
    except sqlite3.IntegrityError:
        db.rollback()
        return None


def get_user_by_username(db, username):
    return db.execute(
        'SELECT * FROM users WHERE username = ?',
        (username,)
    ).fetchone()


def get_user_by_id(db, user_id):
    return db.execute(
        'SELECT * FROM users WHERE id = ?',
        (user_id,)
    ).fetchone()


## TOKEN FUNCTIONS ##

def get_token_balance(db, user_id):
    result = db.execute(
        'SELECT token_balance FROM users WHERE id = ?', (user_id,)
    ).fetchone()
    return result['token_balance'] if result else 0


def reconcile_token_balance(db, user_id):
    result = db.execute(
        'SELECT SUM(amount) as balance FROM token_transactions WHERE user_id = ?',
        (user_id,)
    ).fetchone()
    return result['balance'] or 0


def add_token_transactions(db, user_id, amount, reason, issue_id=None):
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

def get_pending_contributions(db):
    return db.execute(
        '''
        SELECT c.*, u.username, cd.summary, cd.confidence
        FROM contributions c
        JOIN users u ON c.user_id = u.id
        LEFT JOIN contribution_digests cd ON cd.contribution_id = c.id
        WHERE c.status = 'pending'
        ORDER BY c.created_at DESC
        '''
    ).fetchall()


# Fetch all approved contributions linked to any issue in this lens
# Include username and all fields needed for display
def get_approved_contributions_for_lens(db, lens_id):
    return db.execute(
        '''
        SELECT 
            c.*,
            u.username,
            i.title AS issue_title,
            ind.name AS indicator_name
        FROM contributions c
        JOIN users u ON c.user_id = u.id
        JOIN contribution_lens_links cll ON cll.contribution_id = c.id
        JOIN issues i ON i.id = cll.issue_id
        LEFT JOIN indicators ind ON ind.id = c.indicator_id
        WHERE c.status = 'approved'
          AND i.lens_id = ?
        ORDER BY c.created_at DESC
        ''',
        (lens_id,)
    ).fetchall()


def get_contribution_by_id(db, contribution_id):
    return db.execute(
        '''
        SELECT c.*, u.username
        FROM contributions c
        JOIN users u ON c.user_id = u.id
        WHERE c.id = ?''',
        (contribution_id,)
    ).fetchone()


def get_contribution_with_digest(db, contribution_id):
    return db.execute(
        '''
        SELECT c.*, cd.summary, cd.confidence, cd.sources
        FROM contributions c
        LEFT JOIN contribution_digests cd ON cd.contribution_id = c.id
        WHERE c.id = ?
        ''',
        (contribution_id,)
    ).fetchone()


def get_pending_force_claims_by_category(db, category):
    rows = db.execute(
        '''
        SELECT id, note FROM contributions
        WHERE contribution_type = 'force_claim' AND status = 'pending' AND category = ?
        ''',
        (category,)
    ).fetchall()
    return [dict(r) for r in rows]


# Append a source to an existing pending contribution instead of creating a new row
# Called by create_contribution below when agent.check_force_claim_match finds a match
def merge_into_contribution(db, contribution_id, note, source_url, source_excerpt, contributor_user_id, issue_id):
    
    db.execute(
        '''
        INSERT INTO contribution_sources (contribution_id, note, source_url, source_excerpt, contributor_user_id)
        VALUES (?, ?, ?, ?, ?)
        ''',
        (contribution_id, note, source_url, source_excerpt, contributor_user_id)
    )
    if issue_id:
        db.execute(
            '''
            INSERT OR IGNORE INTO contribution_lens_links (contribution_id, issue_id)
            VALUES (?, ?)
            ''',
            (contribution_id, issue_id)
        )
    db.commit()
    return contribution_id


def create_contribution(db, user_id, country_code, note, contribution_type='data_point',
                        indicator_id=None, value=None, source_url=None, source_excerpt=None,
                        title=None, category=None):
    """Insert a new contribution, or merge into an existing pending force_claim if matched.
    Called by app.py contribute route. For force_claim type, checks get_pending_force_claims_by_category
    and agent.check_force_claim_match before deciding to insert vs merge."""
    issue_id = None
    if indicator_id:
        indicator = db.execute(
            'SELECT issue_id FROM indicators WHERE id = ?', (indicator_id,)
        ).fetchone()
        if indicator:
            issue_id = indicator['issue_id']

    if contribution_type == 'force_claim' and category:
        candidates = get_pending_force_claims_by_category(db, category)
        import agent
        match_id = agent.check_force_claim_match(note, candidates)
        if match_id:
            merge_into_contribution(db, match_id, note, source_url, source_excerpt, user_id, issue_id)
            return db.execute('SELECT * FROM contributions WHERE id = ?', (match_id,)).fetchone()

    db.execute(
        '''
        INSERT INTO contributions (user_id, indicator_id, country_code, value, note, source_url, source_excerpt, contribution_type, title, category)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''',
        (user_id, indicator_id, country_code, value, note, source_url, source_excerpt,
         contribution_type, title, category)
    )
    db.commit()

    contribution = db.execute(
        'SELECT * FROM contributions WHERE user_id = ? ORDER BY created_at DESC LIMIT 1',
        (user_id,)
    ).fetchone()

    if issue_id:
        db.execute(
            'INSERT OR IGNORE INTO contribution_lens_links (contribution_id, issue_id) VALUES (?, ?)',
            (contribution['id'], issue_id)
        )
        db.commit()

    return contribution


# Check whether a user contributed a merged source to this contribution
# Called by app.py contribute_confirm to extend view access beyond the original submitter
def is_contribution_source(db, contribution_id, user_id):
    result = db.execute(
        'SELECT 1 FROM contribution_sources WHERE contribution_id = ? AND contributor_user_id = ?',
        (contribution_id, user_id)
    ).fetchone()
    return result is not None


# Return a specific user's own submitted source for a contribution they merged into
# Called by app.py contribute_confirm when the viewer is a merged contributor, not the owner
def get_contributor_source(db, contribution_id, user_id):
    return db.execute(
        'SELECT source_url, source_excerpt, added_at FROM contribution_sources WHERE contribution_id = ? AND contributor_user_id = ?',
        (contribution_id, user_id)
    ).fetchone()


def slugify(text):
    """Convert text into a URL-safe slug. Used only by elevate_force_claim below."""
    text = text.lower().strip()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-')


def elevate_force_claim(db, contribution_id):
    """Insert an approved force_claim into forces and force_issue_links, if it meets
    the structural quality bar (2+ sources, 2+ distinct lenses) and mechanism refinement succeeds.
    Called by app.py cast_vote when a force_claim crosses force_approval_threshold."""
    source_count = db.execute(
        'SELECT COUNT(*) as n FROM contribution_sources WHERE contribution_id = ?',
        (contribution_id,)
    ).fetchone()['n'] + 1

    lens_count = db.execute(
        '''SELECT COUNT(DISTINCT i.lens_id) as n
           FROM contribution_lens_links cll
           JOIN issues i ON cll.issue_id = i.id
           WHERE cll.contribution_id = ?''',
        (contribution_id,)
    ).fetchone()['n']

    if source_count < 2 or lens_count < 2:
        return False

    contribution = db.execute(
        'SELECT * FROM contributions WHERE id = ?', (contribution_id,)
    ).fetchone()

    additional_sources = db.execute(
        'SELECT note, source_url, source_excerpt FROM contribution_sources WHERE contribution_id = ?',
        (contribution_id,)
    ).fetchall()

    all_claims = [contribution['title'] or contribution['note']]
    all_claims += [s['note'] or '' for s in additional_sources if s['note']]

    import agent
    refined_title = agent.refine_mechanism(all_claims)

    if refined_title is None:
        return False

    evidence_chain = []
    for s in additional_sources:
        evidence_chain.append({
            'claim': s['note'] or contribution['note'],
            'source_url': s['source_url'],
            'data_summary': s['source_excerpt']
        })

    category = contribution['category'] or 'information_asymmetry'
    slug = f"{slugify(refined_title)}-{contribution_id}"

    db.execute(
        'INSERT INTO forces (slug, title, category, mechanism, evidence_chain) VALUES (?, ?, ?, ?, ?)',
        (slug, refined_title, category, refined_title, json.dumps(evidence_chain))
    )
    force = db.execute('SELECT id FROM forces WHERE slug = ?', (slug,)).fetchone()

    linked_issues = db.execute(
        'SELECT DISTINCT issue_id FROM contribution_lens_links WHERE contribution_id = ?',
        (contribution_id,)
    ).fetchall()
    for li in linked_issues:
        db.execute(
            'INSERT OR IGNORE INTO force_issue_links (force_id, issue_id, explanation) VALUES (?, ?, ?)',
            (force['id'], li['issue_id'], refined_title)
        )

    db.commit()
    return True


# Return forces linked to any issue within a given lens, deduplicated by force id
# Called by app.py lens route; feeds the 'related forces' section in lens.html
def get_forces_for_lens(db, lens_id):
    rows = db.execute(
        '''
        SELECT DISTINCT f.id, f.slug, f.title, f.category, fil.issue_id
        FROM forces f
        JOIN force_issue_links fil ON fil.force_id = f.id
        JOIN issues i ON fil.issue_id = i.id
        WHERE i.lens_id = ?
        ''',
        (lens_id,)
    ).fetchall()
    return [dict(r) for r in rows]


# Return every force, ordered by category then newest first
# Called by app.py forces route; feeds force.html index, grouped by category in the template
def get_all_forces(db):
    return db.execute(
        'SELECT * FROM forces ORDER BY category, created_at DESC'
    ).fetchall()


# Return a single force with its evidence_chain parsed and cross-lens issue links attached
# Called by app.py force route; slug comes from the URL parameter
def get_force_by_slug(db, slug):
    force = db.execute(
        'SELECT * FROM forces WHERE slug = ?', (slug,)
    ).fetchone()

    if force is None:
        return None
    
    force = dict(force)
    force['evidence_chain'] = json.loads(force['evidence_chain']) if force['evidence_chain'] else []

    linked_issues = db.execute(
        '''
        SELECT i.title as issue_title, i.slug as issue_slug, l.title as lens_title, l.slug as lens_slug
        FROM force_issue_links fil
        JOIN issues i ON fil.issue_id = i.id
        JOIN lenses l ON i.lens_id = l.id
        WHERE fil.force_id = ?
        ''',
        (force['id'],)
    ).fetchall()
    force['linked_issues'] = [dict(li) for li in linked_issues]

    return force


def get_source_count(db, contribution_id):
    result = db.execute(
        'SELECT COUNT(*) as n FROM contribution_sources WHERE contribution_id = ?',
        (contribution_id,)
    ).fetchone()
    return result['n'] + 1  # +1 for original source on the contribution row itself


## QUIZ FUNCTIONS ##

def save_quiz_response(db, user_id, responses, recommend_lens_id, session_id=None):
    db.execute(
        '''
        INSERT INTO quiz_responses (user_id, session_id, responses, recommended_lens_id)
        VALUES (?, ?, ?, ?)
        ''',
        (user_id, session_id, json.dumps(responses), recommend_lens_id)
    )
    db.commit()


def get_last_quiz_response(db, user_id):
    return db.execute(
        '''
        SELECT * FROM quiz_responses
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT 1
        ''',
        (user_id,)
    ).fetchone()


def can_retake_quiz(db, user_id, retake_days=90):
    last = get_last_quiz_response(db, user_id)
    if not last:
        return True
    last_date = last['created_at']
    if isinstance(last_date, str):
        last_date = datetime.fromisoformat(last_date)
    last_date = last_date.replace(tzinfo=timezone.utc)
    delta = datetime.now(timezone.utc) - last_date
    return delta.days >= retake_days


## PLATFORM CONFIG ##

def get_config(db, key):
    result = db.execute(
        'SELECT value FROM platform_config WHERE key = ?', (key,)
    ).fetchone()
    return result['value'] if result else None


## LENS ##

def get_lens_by_slug(db, slug):
    return db.execute(
        'SELECT * FROM lenses WHERE slug = ?', (slug,)
    ).fetchone()


def get_issues_by_lens(db, lens_id):
    return db.execute(
        '''
        SELECT i.*, ind.name as indicator_name, ind.unit,
            dp.country_code, dp.year, dp.value
        FROM issues i
        LEFT JOIN indicators ind ON ind.issue_id = i.id
        LEFT JOIN data_points dp ON dp.indicator_id = ind.id
        WHERE i.lens_id = ?
        ORDER BY i.id, dp.value DESC
        ''',
        (lens_id,)
    ).fetchall()


def get_issues_with_data(db, lens_id):
    """Get issues with their indicators and data points, PLUS approved community contributions."""
    issues = db.execute(
        '''
        SELECT DISTINCT 
            i.id AS issue_id,
            i.title,
            i.description,
            ind.id AS indicator_id,
            ind.name AS indicator_name,
            ind.unit
        FROM issues i
        LEFT JOIN indicators ind ON ind.issue_id = i.id
        WHERE i.lens_id = ?
        ORDER BY i.id
        ''',
        (lens_id,)
    ).fetchall()

    # Convert Row objects to dictionaries to add keys to them
    issues = [dict(issue) for issue in issues]
    
    for issue in issues:
        # 1. Get official seed data
        official_data = db.execute(
            '''
            SELECT dp.country_code AS country, dp.year, dp.value
            FROM data_points dp
            WHERE dp.indicator_id = ?
            ORDER BY dp.country_code, dp.year
            ''',
            (issue['indicator_id'],)
        ).fetchall()
        
        # 2. Get approved community contributions
        community_data = db.execute(
            '''
            SELECT 
                c.country_code AS country,
                strftime('%Y', c.created_at) AS year,
                c.value,
                c.title,
                c.note,
                c.source_url,
                u.username,
                cd.summary AS ai_summary
            FROM contributions c
            JOIN users u ON c.user_id = u.id
            JOIN contribution_lens_links cll ON cll.contribution_id = c.id
            LEFT JOIN contribution_digests cd ON cd.contribution_id = c.id
            WHERE c.status = 'approved'
              AND c.indicator_id = ?
              AND cll.issue_id = ?
            ORDER BY c.created_at DESC
            ''',
            (issue['indicator_id'], issue['issue_id'])
        ).fetchall()
        
        # 3. Assign to separate keys for Smart Grouping
        issue['official_data'] = list(official_data)
        issue['community_contributions'] = list(community_data)
    
    return issues


## HEATMAP ##

def get_heatmap_data(db):
    return db.execute(
        '''SELECT dp.country_code, COUNT(DISTINCT tt.id) as total_spend
           FROM token_transactions tt
           JOIN issues i ON tt.issue_id = i.id
           JOIN indicators ind ON ind.issue_id = i.id
           JOIN data_points dp ON dp.indicator_id = ind.id
           WHERE tt.reason = 'spend'
           GROUP BY dp.country_code
           ORDER BY total_spend DESC'''
    ).fetchall()


def get_least_heard_data(db):
    return db.execute(
        '''SELECT dp.country_code, COUNT(dp.id) as data_coverage,
                  COUNT(DISTINCT CASE WHEN tt.reason = 'spend' THEN tt.id ELSE NULL END) as total_spend
           FROM data_points dp
           LEFT JOIN indicators ind ON dp.indicator_id = ind.id
           LEFT JOIN issues i ON ind.issue_id = i.id
           LEFT JOIN token_transactions tt ON tt.issue_id = i.id
           GROUP BY dp.country_code
           ORDER BY total_spend ASC, data_coverage DESC'''
    ).fetchall()


## USER CONTRIBUTION ##

def get_all_indicators(db):
    return db.execute(
        'SELECT id, name, source FROM indicators ORDER BY name'
    ).fetchall()


## CAST AND VALIDATE VOTE ##

def cast_vote(db, contribution_id, user_id, vote):
    try:
        db.execute(
            'INSERT INTO contribution_votes (contribution_id, user_id, vote) VALUES (?, ?, ?)',
            (contribution_id, user_id, vote)
        )
        db.commit()
        return True
    except sqlite3.IntegrityError:
        db.rollback()
        return False


def get_vote_count(db, contribution_id, vote_type):
    result = db.execute(
        'SELECT COUNT(*) as count FROM contribution_votes WHERE contribution_id = ? AND vote = ?',
        (contribution_id, vote_type)
    ).fetchone()
    return result['count']


# Handle all threshold checks, approvals, rejections, and force elevations
# Return a flash message string to be displayed to the user
def process_vote_logic(db, contribution, user_id, vote):
    
    contribution_id = contribution['id']
    approve_count = get_vote_count(db, contribution_id, 'approve')
    reject_count = get_vote_count(db, contribution_id, 'reject')
    total_votes = approve_count + reject_count

    type_suffix = 'force_claim' if contribution['contribution_type'] == 'force_claim' else 'data_point'
    minimum_votes = int(get_config(db, f'minimum_total_votes_{type_suffix}') or 3)

    if total_votes < minimum_votes:
        return 'Vote recorded.'

    rejection_threshold = int(get_config(db, f'rejection_threshold_{type_suffix}') or 3)

    if reject_count >= rejection_threshold:
        reject_contribution(db, contribution_id)
        return 'Contribution rejected by peer review.'

    threshold_key = 'force_approval_threshold' if type_suffix == 'force_claim' else 'validation_threshold'
    threshold = int(get_config(db, threshold_key) or 2)

    if approve_count >= threshold:
        approve_contribution(db, contribution_id)
        
        # --- BUG 3 FIX: Reward ALL contributors (original + merged sources) ---
        tokens_per_contribution = int(get_config(db, 'tokens_per_contribution') or 3)
        
        # 1. Reward the original submitter
        add_token_transactions(db, contribution['user_id'], tokens_per_contribution, 'contribution')
        
        # 2. Reward all users who contributed merged sources
        merged_sources = db.execute(
            'SELECT DISTINCT contributor_user_id FROM contribution_sources WHERE contribution_id = ?',
            (contribution_id,)
        ).fetchall()
        
        for source in merged_sources:
            add_token_transactions(db, source['contributor_user_id'], tokens_per_contribution, 'contribution')
        # -----------------------------------------------------------------------

        # --- BUG 1 FIX: Accurate Flash Messages ---
        if contribution['contribution_type'] == 'force_claim':
            elevated = elevate_force_claim(db, contribution_id)
            if elevated:
                if vote == 'approve':
                    return 'Contribution elevated to the Forces layer.'
                else:
                    return 'Contribution elevated to the Forces layer. Your reject vote, combined with a number of approvals, allowed the contribution to reach the minimum voting threshold for elevation.'
            else:
                if vote == 'approve':
                    return 'Contribution reached the minimum voting threshold but requires corroboration from another sector (e.g., Housing or Mobility) before appearing in the Forces layer.'
                else:
                    return 'Your reject vote, together with a number of approvals, allowed the contribution to reach the minimum voting threshold. However, it requires corroboration from another sector before it is elevated to the Forces layer.'
        else:
            if vote == 'approve':
                return 'Contribution approved and added as lens evidence.'
            else:
                return 'Your reject vote, together with a number of approvals, allowed the contribution to reach the minimum voting threshold to be added as lens evidence.'
    else:
        return 'Vote recorded.'


def approve_contribution(db, contribution_id):
    db.execute(
        "UPDATE contributions SET status = 'approved', reviewed_at = CURRENT_TIMESTAMP WHERE id = ?",
        (contribution_id,)
    )
    db.commit()


def reject_contribution(db, contribution_id):
    db.execute(
        "UPDATE contributions SET status = 'rejected', reviewed_at = CURRENT_TIMESTAMP WHERE id = ?",
        (contribution_id,)
    )
    db.commit()


# Check if user has already voted on a contribution
def has_user_voted(db, contribution_id, user_id):
    result = db.execute(
        '''
        SELECT id FROM contribution_votes 
        WHERE contribution_id = ? AND user_id = ?
        ''',
        (contribution_id, user_id)
    ).fetchone()
    return result is not None


# Get pending contributions that the user hasn't voted on yet
def get_pending_contributions_for_user(db, user_id):
    # 1. Fetch base contributions WITHOUT joining the digest table
    contributions = db.execute(
        '''
        SELECT c.*, u.username
        FROM contributions c
        JOIN users u ON c.user_id = u.id
        WHERE c.status = 'pending'
          AND c.user_id != ?
          AND c.id NOT IN (
              SELECT contribution_id 
              FROM contribution_votes 
              WHERE user_id = ?
          )
        ORDER BY c.created_at DESC
        ''',
        (user_id, user_id)
    ).fetchall()
    
    result = []
    for c in contributions:
        c_dict = dict(c)
        
        # 2. Fetch only the LATEST digest for this specific contribution
        # (ORDER BY rowid DESC LIMIT 1 ensures we get the most recent AI summary)
        digest = db.execute(
            '''
            SELECT summary, confidence FROM contribution_digests 
            WHERE contribution_id = ? 
            ORDER BY rowid DESC LIMIT 1
            ''',
            (c_dict['id'],)
        ).fetchone()
        
        if digest:
            c_dict['summary'] = digest['summary']
            c_dict['confidence'] = digest['confidence']
        else:
            c_dict['summary'] = None
            c_dict['confidence'] = None
            
        result.append(c_dict)
        
    return result