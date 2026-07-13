# models.py
# Conviction: database interaction functions.
# All SQL queries live here. app.py calls these functions; it never writes SQL directly.
# AI assistance: Claude (Anthropic) assisted with query structure and error handling patterns.
# Logic, decisions, and direction are the author's own.

import agent
import datetime
import json
import os
import re
import sqlite3
from datetime import datetime, timezone


## HELPER FUNCTIONS TO READ BETWEEN SQLITE AND POSTGRES SYNTAX ##

# Global flag to detect database type
USE_POSTGRESQL = os.environ.get('DATABASE_URL') is not None

def convert_query_for_db(query):
    """Convert SQLite ? placeholders to PostgreSQL %s placeholders if needed."""
    if USE_POSTGRESQL:
        return query.replace('?', '%s')
    return query

def execute_query(db, query, params=None):
    """Execute a query with automatic placeholder conversion."""
    converted_query = convert_query_for_db(query)
    return db.execute(converted_query, params)

def commit_changes(db):
    """Commit changes with database-specific method."""
    if USE_POSTGRESQL:
        db.conn.commit()
    else:
        db.commit()

def rollback_changes(db):
    """Rollback changes with database-specific method."""
    if USE_POSTGRESQL:
        db.conn.rollback()
    else:
        db.rollback()

def get_last_insert_id(db):
    """Get last inserted ID with database-specific method."""
    if USE_POSTGRESQL:
        # PostgreSQL uses RETURNING clause, so we handle it differently
        return None
    else:
        return db.execute('SELECT last_insert_rowid()').fetchone()[0]
    

COUNTRY_NAMES = {
    'AFG': 'Afghanistan', 'ALB': 'Albania', 'DZA': 'Algeria', 'AND': 'Andorra', 'AGO': 'Angola',
    'ARG': 'Argentina', 'ARM': 'Armenia', 'AUS': 'Australia', 'AUT': 'Austria', 'AZE': 'Azerbaijan',
    'BHS': 'Bahamas', 'BHR': 'Bahrain', 'BGD': 'Bangladesh', 'BLR': 'Belarus', 'BEL': 'Belgium',
    'BLZ': 'Belize', 'BEN': 'Benin', 'BTN': 'Bhutan', 'BOL': 'Bolivia', 'BIH': 'Bosnia and Herzegovina',
    'BWA': 'Botswana', 'BRA': 'Brazil', 'BRN': 'Brunei', 'BGR': 'Bulgaria', 'BFA': 'Burkina Faso',
    'BDI': 'Burundi', 'CPV': 'Cabo Verde', 'KHM': 'Cambodia', 'CMR': 'Cameroon', 'CAN': 'Canada',
    'CAF': 'Central African Republic', 'TCD': 'Chad', 'CHL': 'Chile', 'CHN': 'China', 'COL': 'Colombia',
    'COM': 'Comoros', 'COD': 'Congo, Dem. Rep.', 'COG': 'Congo, Rep.', 'CRI': 'Costa Rica', 'CIV': "Côte d'Ivoire",
    'HRV': 'Croatia', 'CUB': 'Cuba', 'CYP': 'Cyprus', 'CZE': 'Czech Republic', 'DNK': 'Denmark',
    'DJI': 'Djibouti', 'DOM': 'Dominican Republic', 'ECU': 'Ecuador', 'EGY': 'Egypt', 'SLV': 'El Salvador',
    'GNQ': 'Equatorial Guinea', 'ERI': 'Eritrea', 'EST': 'Estonia', 'SWZ': 'Eswatini', 'ETH': 'Ethiopia',
    'FJI': 'Fiji', 'FIN': 'Finland', 'FRA': 'France', 'GAB': 'Gabon', 'GMB': 'Gambia', 'GEO': 'Georgia',
    'DEU': 'Germany', 'GHA': 'Ghana', 'GRC': 'Greece', 'GTM': 'Guatemala', 'GIN': 'Guinea',
    'GNB': 'Guinea-Bissau', 'GUY': 'Guyana', 'HTI': 'Haiti', 'HND': 'Honduras', 'HUN': 'Hungary',
    'ISL': 'Iceland', 'IND': 'India', 'IDN': 'Indonesia', 'IRN': 'Iran', 'IRQ': 'Iraq', 'IRL': 'Ireland',
    'ISR': 'Israel', 'ITA': 'Italy', 'JAM': 'Jamaica', 'JPN': 'Japan', 'JOR': 'Jordan', 'KAZ': 'Kazakhstan',
    'KEN': 'Kenya', 'PRK': 'Korea, North', 'KOR': 'Korea, South', 'KWT': 'Kuwait', 'KGZ': 'Kyrgyzstan',
    'LAO': 'Laos', 'LVA': 'Latvia', 'LBN': 'Lebanon', 'LSO': 'Lesotho', 'LBR': 'Liberia', 'LBY': 'Libya',
    'LIE': 'Liechtenstein', 'LTU': 'Lithuania', 'LUX': 'Luxembourg', 'MDG': 'Madagascar', 'MWI': 'Malawi',
    'MYS': 'Malaysia', 'MDV': 'Maldives', 'MLI': 'Mali', 'MLT': 'Malta', 'MRT': 'Mauritania', 'MUS': 'Mauritius',
    'MEX': 'Mexico', 'MDA': 'Moldova', 'MCO': 'Monaco', 'MNG': 'Mongolia', 'MNE': 'Montenegro', 'MAR': 'Morocco',
    'MOZ': 'Mozambique', 'MMR': 'Myanmar', 'NAM': 'Namibia', 'NPL': 'Nepal', 'NLD': 'Netherlands',
    'NZL': 'New Zealand', 'NIC': 'Nicaragua', 'NER': 'Niger', 'NGA': 'Nigeria', 'MKD': 'North Macedonia',
    'NOR': 'Norway', 'OMN': 'Oman', 'PAK': 'Pakistan', 'PSE': 'Palestine', 'PAN': 'Panama', 'PNG': 'Papua New Guinea',
    'PRY': 'Paraguay', 'PER': 'Peru', 'PHL': 'Philippines', 'POL': 'Poland', 'PRT': 'Portugal', 'QAT': 'Qatar',
    'ROU': 'Romania', 'RUS': 'Russia', 'RWA': 'Rwanda', 'SAU': 'Saudi Arabia', 'SEN': 'Senegal', 'SRB': 'Serbia',
    'SLE': 'Sierra Leone', 'SGP': 'Singapore', 'SVK': 'Slovakia', 'SVN': 'Slovenia', 'SOM': 'Somalia',
    'ZAF': 'South Africa', 'SSD': 'South Sudan', 'ESP': 'Spain', 'LKA': 'Sri Lanka', 'SDN': 'Sudan',
    'SUR': 'Suriname', 'SWE': 'Sweden', 'CHE': 'Switzerland', 'SYR': 'Syria', 'TWN': 'Taiwan', 'TJK': 'Tajikistan',
    'TZA': 'Tanzania', 'THA': 'Thailand', 'TLS': 'Timor-Leste', 'TGO': 'Togo', 'TTO': 'Trinidad and Tobago',
    'TUN': 'Tunisia', 'TUR': 'Turkey', 'TKM': 'Turkmenistan', 'UGA': 'Uganda', 'UKR': 'Ukraine',
    'ARE': 'United Arab Emirates', 'GBR': 'United Kingdom', 'USA': 'United States', 'URY': 'Uruguay',
    'UZB': 'Uzbekistan', 'VEN': 'Venezuela', 'VNM': 'Vietnam', 'YEM': 'Yemen', 'ZMB': 'Zambia', 'ZWE': 'Zimbabwe'
}


## USER FUNCTIONS ##

def create_user(db, username, password_hash):
    import os
    
    # Safely check if we are using PostgreSQL or SQLite
    use_postgresql = os.environ.get('DATABASE_URL') is not None
    
    try:
        if use_postgresql:
            # PostgreSQL uses %s for placeholders
            db.execute(
                'INSERT INTO users (username, password_hash) VALUES (%s, %s)',
                (username, password_hash)
            )
            user = db.execute(
                'SELECT * FROM users WHERE username = %s', (username,)
            ).fetchone()
            db.execute(
                'INSERT INTO token_transactions (user_id, amount, reason) VALUES (%s, %s, %s)',
                (user['id'], 10, 'registration')
            )
            db.conn.commit()
        else:
            # SQLite uses ? for placeholders
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
        
    except Exception as e:
        print(e)  # For debug only

        if use_postgresql:
            db.conn.rollback()
        else:
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


def add_token_transactions(db, user_id, amount, reason, issue_id=None, force_id=None):
    db.execute(
        '''
        INSERT INTO token_transactions (user_id, amount, reason, issue_id, force_id)
        VALUES (?, ?, ?, ?, ?)
        ''',
        (user_id, amount, reason, issue_id, force_id)
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
    
    # The 'note' passed into this function is ALREADY cleaned by check_force_claim_match_and_clean 
    # inside the create_contribution function. No further cleaning is needed here.

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
            INSERT INTO contribution_lens_links (contribution_id, issue_id) VALUES (%s, %s) ON CONFLICT (contribution_id, issue_id) DO NOTHING
            ''',
            (contribution_id, issue_id)
        )
    db.commit()

    # Check if the target contribution is already approved
    target_status = db.execute(
        'SELECT status FROM contributions WHERE id = ?', 
        (contribution_id,)
    ).fetchone()['status']

    # Reward the contributor immediately if the target claim is already approved
    if target_status == 'approved':
        tokens_per_contribution = int(get_config(db, 'tokens_per_contribution') or 3)
        add_token_transactions(db, contributor_user_id, tokens_per_contribution, 'contribution')

    return contribution_id


# Insert a new contribution, or merge into an existing pending force_claim if matched
# Called by app.py contribute route. For force_claim type, checks get_pending_force_claims_by_category
# and agent.check_force_claim_match before deciding to insert vs merge.
def create_contribution(db, user_id, country_code, note, contribution_type='data_point',
                        indicator_id=None, value=None, source_url=None, source_excerpt=None,
                        title=None, category=None):
    issue_id = None
    if indicator_id:
        indicator = db.execute(
            'SELECT issue_id FROM indicators WHERE id = ?', (indicator_id,)
        ).fetchone()
        if indicator:
            issue_id = indicator['issue_id']

    if contribution_type == 'force_claim' and category:
        candidates = db.execute(
            '''SELECT id, note FROM contributions 
               WHERE contribution_type = 'force_claim' 
               AND category = ? 
               AND status IN ('pending', 'approved')''', 
            (category,)
        ).fetchall()
        
        # Pass source_excerpt to the agent function
        match_id, cleaned_note, cleaned_excerpt = agent.check_force_claim_match_and_clean(note, source_excerpt, candidates)
        
        if match_id:
            # Use cleaned_excerpt if it exists, otherwise fallback to original
            final_excerpt = cleaned_excerpt if cleaned_excerpt else source_excerpt
            merge_into_contribution(db, match_id, cleaned_note, source_url, final_excerpt, user_id, issue_id)
            
            target_status = db.execute('SELECT status FROM contributions WHERE id = ?', (match_id,)).fetchone()['status']
            if target_status == 'approved':
                elevate_force_claim(db, match_id)
                
            return db.execute('SELECT * FROM contributions WHERE id = ?', (match_id,)).fetchone()

    # Clean the title if it's a lens proposal
    if title:
        title = agent.clean_submission_text(title)
    
    # Clean the text before saving (for non-merged claims)
    note = agent.clean_submission_text(note)
    source_excerpt = agent.clean_submission_text(source_excerpt) # Clean excerpt here too!

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
            'INSERT INTO contribution_lens_links (contribution_id, issue_id) VALUES (%s, %s) ON CONFLICT (contribution_id, issue_id) DO NOTHING',
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


# Checks if a force with a similar title already exists in the same category.
# Returns the existing force ID if a duplicate is found, otherwise None.
def find_duplicate_force(db, category, new_title):
    existing_forces = db.execute(
        'SELECT id, title FROM forces WHERE category = ?', 
        (category,)
    ).fetchall()
    
    if not existing_forces:
        return None
        
    new_words = set(new_title.lower().split())
    
    for force in existing_forces:
        existing_words = set(force['title'].lower().split())
        # Calculate word overlap (Jaccard similarity simplified)
        overlap = len(new_words.intersection(existing_words))
        
        # If more than 50% of the words match, it's a duplicate
        if overlap > len(new_words) * 0.5:
            return force['id']
            
    return None


# Insert an approved force_claim into forces and force_issue_links, if it meets
# the structural quality bar (2+ sources, 2+ distinct lenses) and mechanism refinement succeeds
# Called by app.py cast_vote when a force_claim crosses force_approval_threshold
def elevate_force_claim(db, contribution_id):    
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
    
    # --- FIX: Robust Duplicate Prevention ---
    existing_force_id = find_duplicate_force(db, category, refined_title)
    
    if existing_force_id:
        # Duplicate found! Update the existing force's evidence chain and link issues.
        force_id = existing_force_id
        
        # Fetch existing evidence chain
        existing_chain_json = db.execute(
            'SELECT evidence_chain FROM forces WHERE id = ?', (force_id,)
        ).fetchone()['evidence_chain']
        
        existing_chain = json.loads(existing_chain_json) if existing_chain_json else []
        
        # Append new evidence (avoiding exact duplicates)
        for new_evidence in evidence_chain:
            if new_evidence not in existing_chain:
                existing_chain.append(new_evidence)
                
        # Update the force with the merged evidence chain
        db.execute(
            'UPDATE forces SET evidence_chain = ? WHERE id = ?',
            (json.dumps(existing_chain), force_id)
        )
    else:
        # No duplicate, create new force
        slug = f"{slugify(refined_title)}-{contribution_id}"
        db.execute(
            'INSERT INTO forces (slug, title, category, mechanism, evidence_chain) VALUES (?, ?, ?, ?, ?)',
            (slug, refined_title, category, refined_title, json.dumps(evidence_chain))
        )
        force = db.execute('SELECT id FROM forces WHERE slug = ?', (slug,)).fetchone()
        force_id = force['id']
    # ----------------------------------------

    # Link issues to the force (works for both new and existing forces)
    linked_issues = db.execute(
        'SELECT DISTINCT issue_id FROM contribution_lens_links WHERE contribution_id = ?',
        (contribution_id,)
    ).fetchall()
    
    for li in linked_issues:
        db.execute(
            'INSERT INTO force_issue_links (force_id, issue_id, explanation) VALUES (%s, %s, %s) ON CONFLICT (force_id, issue_id) DO NOTHING',
            (force_id, li['issue_id'], refined_title)
        )

    db.commit()
    return True


# Automatically creates a new Lens, Issue, and Catch-All Indicator when a lens proposal is approved
# Called by process_vote_logic in app.py
def elevate_lens_proposal(db, contribution_id):

    # 1. Get the AI-extracted JSON from the digest
    digest = db.execute(
        'SELECT sources FROM contribution_digests WHERE contribution_id = ?',
        (contribution_id,)
    ).fetchone()

    if not digest or not digest['sources']:
        return False # Cannot elevate without AI data

    try:
        data = json.loads(digest['sources'])
    except json.JSONDecodeError:
        return False
    
    proposal_data = data.get('lens_proposal')

    if not proposal_data:
        return False

    lens_title = proposal_data.get('lens_title')
    lens_desc = proposal_data.get('lens_description')
    core_issue = proposal_data.get('core_issue')

    if not lens_title or not core_issue:
        return False

    # 2. Check if the Lens already exists (prevents duplicates)
    lens_slug = slugify(lens_title)
    existing_lens = db.execute(
        'SELECT * FROM lenses WHERE slug = ?', (lens_slug,)
    ).fetchone()

    if existing_lens:
        existing_lens_id = existing_lens['id']
        existing_lens_slug = existing_lens['slug']

        # Fetch title safely to avoid IndexError
        title_row = db.execute('SELECT title FROM lenses WHERE id = ?', (existing_lens_id,)).fetchone()
        existing_lens_title = title_row[0] if title_row else lens_title

        # 1. Try to find the specific issue proposed by the AI
        proposed_issue_slug = slugify(core_issue)
        issue = db.execute(
            'SELECT id FROM issues WHERE lens_id = ? AND slug = ?',
            (existing_lens_id, proposed_issue_slug)
        ).fetchone()

        # 2. If not found, find ANY existing issue for this lens to attach the contribution to
        if not issue:
            issue = db.execute(
                'SELECT id FROM issues WHERE lens_id = ? LIMIT 1',
                (existing_lens_id,)
            ).fetchone()

        # 3. If the lens somehow has NO issues, create a fallback with a UNIQUE slug
        if not issue:
            fallback_slug = f"general-{existing_lens_slug}"
            db.execute(
                'INSERT INTO issues (lens_id, slug, title, description) VALUES (?, ?, ?, ?)',
                (existing_lens_id, fallback_slug, 'General Evidence', f'Community evidence for the {existing_lens_title} lens')
            )
            # We handle this by fetching the issue we just created by its unique slug
            issue = db.execute('SELECT id FROM issues WHERE slug = %s', (fallback_slug,)).fetchone()

        # Link contribution to the existing lens/issue
        db.execute(
            'INSERT INTO contribution_lens_links (contribution_id, issue_id) VALUES (?, ?)',
            (contribution_id, issue['id'])
        )

        db.commit()
        return "merged"

    # 3. Create the Lens (only if it doesn't exist)
    new_lens = db.execute(
        'INSERT INTO lenses (slug, title, description) VALUES (%s, %s, %s) RETURNING id',
        (lens_slug, lens_title, lens_desc)
    ).fetchone()
    new_lens_id = new_lens['id']

    # 4. Create the Core Issue
    # Replace the old INSERT and SELECT lines with this:
    new_issue = db.execute(
        'INSERT INTO issues (lens_id, slug, title, description) VALUES (?, ?, ?, ?) RETURNING id',
        (new_lens_id, issue_slug, core_issue, f'Primary systemic issue tracked under the {lens_title} lens.')
    ).fetchone()
    new_issue_id = new_issue['id']

    # 5. Create the "Catch-All" Indicator with contextual name
    indicator_name = f"General {lens_title.lower()} evidence"
    db.execute(
        'INSERT INTO indicators (issue_id, name, source, unit) VALUES (?, ?, ?, ?)',
        (new_issue_id, indicator_name, 'User Contributed', 'N/A')
    )

    # 6. Link the contribution to the newly created lens/issue
    db.execute(
        'INSERT INTO contribution_lens_links (contribution_id, issue_id) VALUES (?, ?)',
        (contribution_id, new_issue_id)
    )

    db.commit()
    return "created"


# Function required to make the index page dynamic i.e. elevated lens are fetched and shown in the index page
# Called by the index route in app.py
def get_all_lenses(db):
    return db.execute('SELECT * FROM lenses ORDER BY title').fetchall()


# Return forces linked to any issue within a given lens, deduplicated by force id
# Called by app.py lens route; feeds the 'related forces' section in lens.html
def get_forces_for_lens(db, lens_id):
    rows = db.execute(
        '''
        SELECT DISTINCT f.id, f.slug, f.title, f.category
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
        WHERE i.lens_id = ?
        ORDER BY i.id, dp.value DESC
        ''',
        (lens_id,)
    ).fetchall()


# Get issues with their indicators and all approved contributions (unified)
def get_issues_with_data(db, lens_id):
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
        # Get all approved contributions (formerly community + seed data, now unified)
        # Note: We added c.created_at to the SELECT list below
        contributions = db.execute(
            '''
            SELECT DISTINCT
                c.id,
                c.country_code AS country,
                c.created_at,
                c.value,
                c.title,
                c.note,
                c.source_url,
                u.username,
                (SELECT cd.summary FROM contribution_digests cd 
                 WHERE cd.contribution_id = c.id 
                 ORDER BY cd.rowid DESC LIMIT 1) AS ai_summary
            FROM contributions c
            JOIN users u ON c.user_id = u.id
            JOIN contribution_lens_links cll ON cll.contribution_id = c.id
            WHERE c.status = 'approved'
              AND c.indicator_id = ?
              AND cll.issue_id = ?
            ORDER BY c.created_at DESC
            ''',
            (issue['indicator_id'], issue['issue_id'])
        ).fetchall()
        
        # Process contributions to add full country name and formatted date
        processed_contributions = []
        for c in contributions:
            c_dict = dict(c)
            
            # 1. Map country code to full name
            code = c_dict.get('country', '')
            c_dict['country_name'] = COUNTRY_NAMES.get(code, code)
            
            # 2. Format the date (e.g., "July 12, 2026")
            if c_dict.get('created_at'):
                # Handle both string and datetime object formats
                date_obj = c_dict['created_at']
                if isinstance(date_obj, str):
                    date_obj = datetime.fromisoformat(date_obj)
                c_dict['formatted_date'] = date_obj.strftime('%d %B %Y')
            else:
                c_dict['formatted_date'] = 'Unknown Date'
                
            processed_contributions.append(c_dict)
            
        # Assign the processed list to the key used in the template
        issue['community_contributions'] = processed_contributions
    
    return issues


## HEATMAP ##

# Fetch total token spend per country for the 'conviction' heatmap mode
def get_heatmap_data(db):
    return db.execute('''
        SELECT 
            c.country_code, 
            SUM(ABS(tt.amount)) as total_spend
        FROM contributions c
        JOIN contribution_lens_links cll ON c.id = cll.contribution_id
        JOIN token_transactions tt ON cll.issue_id = tt.issue_id
        WHERE c.status = 'approved'
        GROUP BY c.country_code
        ORDER BY total_spend DESC
    ''').fetchall()


# Fetch data coverage vs token spend for the 'least_heard' heatmap mode
def get_least_heard_data(db):
    return db.execute('''
        SELECT 
            c.country_code,
            COUNT(DISTINCT c.id) AS data_coverage,
            COALESCE(SUM(issue_spend.spend), 0) AS total_spend
        FROM contributions c
        JOIN contribution_lens_links cll ON c.id = cll.contribution_id
        LEFT JOIN (
            SELECT issue_id, SUM(amount) as spend 
            FROM token_transactions 
            GROUP BY issue_id
        ) issue_spend ON cll.issue_id = issue_spend.issue_id
        WHERE c.status = 'approved'
        GROUP BY c.country_code
        ORDER BY data_coverage ASC, total_spend ASC
    ''').fetchall()


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
    except Exception:
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
        
        # --- Reward ALL contributors (original + merged sources) ---
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

        # --- ACCURATE FLASH MESSAGES & ELEVATION LOGIC ---
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
        
        elif contribution['contribution_type'] == 'lens_proposal':
            # Fetch the AI-extracted data for the flash message
            # FIX: We must query 'sources' now, as 'extracted_json' was removed from the schema
            digest = db.execute(
                'SELECT sources FROM contribution_digests WHERE contribution_id = ?',
                (contribution_id,)
            ).fetchone()
            
            lens_title = "Lens"
            if digest and digest['sources']:
                try:
                    sources_data = json.loads(digest['sources'])
                    proposal_data = sources_data.get('lens_proposal', {})
                    lens_title = proposal_data.get('lens_title', 'Lens')
                except json.JSONDecodeError:
                    pass
            
            elevated = elevate_lens_proposal(db, contribution_id)
            
            if elevated == "merged":
                if vote == 'approve':
                    return f'Lens proposal approved! This contribution has been merged into the existing "{lens_title}" lens.'
                else:
                    return f'Lens proposal merged into the existing "{lens_title}" lens, despite your reject vote.'
            elif elevated == "created":
                if vote == 'approve':
                    return f'Lens proposal approved! A new "{lens_title}" has been created and added to the platform.'
                else:
                    return f'Lens proposal approved and a new "{lens_title}" lens created, despite your reject vote.'
            else:
                return 'Lens proposal approved, but failed to generate the lens structure automatically.'
        
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
    # 1. Fetch base contributions WITH vote counts and WITHOUT joining the digest table
    contributions = db.execute(
        '''
        SELECT c.*, u.username,
               (SELECT COUNT(*) FROM contribution_votes WHERE contribution_id = c.id AND vote = 'approve') as approve_count,
               (SELECT COUNT(*) FROM contribution_votes WHERE contribution_id = c.id AND vote = 'reject') as reject_count
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