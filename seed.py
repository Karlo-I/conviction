# seed.py
# Conviction: seeds the database with real data from WHO and other sources
# Run after flask --app app init-db: python seed.py
# AI assistance: Claude (Anthropic) assisted with API query structure and data parsing
# Logic, decisions, and direction are the author's own

import sqlite3
import requests
from datetime import datetime, timezone


DATABASE = 'conviction.db'

# Open a direct SQLite connection to connection.db for use within seed.py only
# Independent of app.py's get_db - seed.py runs outside Flask's request context
def get_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db


# Create the "Data Archive" system user for all seeded contributions
def create_system_user(db):
    """Create the Data Archive system user if it doesn't exist."""
    user = db.execute("SELECT id FROM users WHERE username = 'Data Archive'").fetchone()
    
    if not user:
        db.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", 
                   ('Data Archive', 'dummy_hash_for_system_user'))
        db.commit()
        user = db.execute("SELECT id FROM users WHERE username = 'Data Archive'").fetchone()
        print(f'Created Data Archive user with ID: {user["id"]}')
    
    return user['id']


# Seed the food lens, issues, and indicators into the database, then triggers the data fetch
# Calls fetch_who_obesity; writes to lenses, issues, and indicators in schema.sql
def seed_food_lens(db, system_user_id):
    """Seed the food lens, its issues, indicators and WHO data points"""

    # --- LENS ---
    db.execute(
        '''
        INSERT OR IGNORE INTO lenses (slug, title, description)
        VALUES (?, ?, ?)
        ''',
        (
            'food',
            'Food',
            'How the global food system shapes what people eat, who profits, and who bears the cost.'
        )
    )
    db.commit()

    lens = db.execute("SELECT id FROM lenses WHERE slug = 'food'").fetchone()
    lens_id = lens['id']

    # --- ISSUES ---
    issues = [
        (
            lens_id,
            'ultra-processed-food',
            'Ultra-Processed-food',
            'Industrial food products engineered for overconsumption, dominant in supply global chains.'
        ),
    ]

    for issue in issues:
        db.execute(
            '''
            INSERT OR IGNORE INTO issues (lens_id, slug, title, description)
            VALUES (?, ?, ?, ?)
            ''',
            issue
        )
    db.commit()

    # upf = ultra-processed-food
    upf_issue = db.execute("SELECT id FROM issues WHERE slug = 'ultra-processed-food'").fetchone()
    upf_issue_id = upf_issue['id']

    # --- INDICATORS ---

    indicators = [
        (upf_issue_id, 'Adult obesity rate', 'WHO Global Health Observation', '%'),
    ]

    for indicator in indicators:
        db.execute(
            '''
            INSERT OR IGNORE INTO indicators (issue_id, name, source, unit)
            VALUES (?, ?, ?, ?)
            ''',
            indicator
        )
    db.commit()

    obesity_indicator = db.execute("SELECT id FROM indicators WHERE name = 'Adult obesity rate'").fetchone()
    indicator_id = obesity_indicator['id']

    # --- DATA POINTS FROM WHO API ---
    fetch_who_obesity(db, indicator_id, upf_issue_id, system_user_id)


# Fetch adult obesity rates from the WHO GHO API and inserts as community contributions
# Called by seed_food_lenses(); writes to contributions table and contribution_lens_links
def fetch_who_obesity(db, indicator_id, issue_id, system_user_id):
    """Fetch adult obesity rates from WHO GHO API and insert as contributions."""

    # Countries selected for geographic diversity - not OECD-only
    # WHO API uses ISO 3166-1 alpha-3 codes — conversion to alpha-2 handled in heatmap layer (Week 3)
    target_countries = ['CAN', 'BRA']

    # WHO GHO API source info: https://www.who.int/data/gho/info/gho-odata-api
    url = 'https://ghoapi.azureedge.net/api/NCD_BMI_30C'
    country_filter = " or ".join([f"SpatialDim eq '{c}'" for c in target_countries])
    params = {
        '$filter': f"Dim1 eq 'SEX_BTSX' and ({country_filter})",  # both sexes combined
        '$select': 'SpatialDim,TimeDim,NumericValue',
    }

    print('Fetching WHO obesity data...')

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        print(f'WHO API request failed: {e}')
        return
    
    records = data.get('value', [])
    print(f'  {len(records)} records returned from WHO API')

    # Keep only most recent year per target country
    latest = {}
    for record in records:
        country = record.get('SpatialDim')
        year = record.get('TimeDim')
        value = record.get('NumericValue')

        if country not in target_countries:
            continue
        if value is None:
            continue
        if country not in latest or year > latest[country]['year']:
            latest[country] = {'year': year, 'value': value}

    inserted = 0
    for country_code, point in latest.items():
        # Create standardized note for the contribution card
        note_text = f"Official record: {point['value']}% in {country_code} for {point['year']}."
        source_url = "https://www.who.int/data"
        
        # Insert into contributions table
        db.execute(
            '''
            INSERT INTO contributions 
            (user_id, contribution_type, country_code, value, note, source_url, status, created_at, indicator_id)
            VALUES (?, 'data_point', ?, ?, ?, ?, 'approved', datetime('now'), ?)
            ''',
            (system_user_id, country_code, point['value'], note_text, source_url, indicator_id)
        )
        
        # Get the newly created contribution ID
        contribution = db.execute("SELECT last_insert_rowid() as id").fetchone()
        contribution_id = contribution['id']
        
        # Link to the issue
        db.execute(
            '''
            INSERT INTO contribution_lens_links (contribution_id, issue_id)
            VALUES (?, ?)
            ''',
            (contribution_id, issue_id)
        )
        
        inserted += 1

    db.commit()
    print(f'  {inserted} new contributions inserted.')


# Seeds the housing lens, its issues, indicators, and World Bank slum population data
# Calls fetch_worldbank_housing; writes to lenses, issues, indicators, and contributions in schema.sql
def seed_housing_lens(db, system_user_id):
    """Seed the housing lens with World Bank urban slum population data."""

    db.execute(
        '''
        INSERT OR IGNORE INTO lenses (slug, title, description)
        VALUES (?, ?, ?)
        ''',
        (
            'housing',
            'Housing',
            'How housing systems around the world fail to provide adequate shelter for urban populations.'
        )
    )
    db.commit()

    lens = db.execute("SELECT id FROM lenses WHERE slug = 'housing'").fetchone()
    lens_id = lens['id']

    db.execute(
        '''
        INSERT OR IGNORE INTO issues (lens_id, slug, title, description)
        VALUES (?, ?, ?, ?)
        ''',
        (
            lens_id,
            'urban-housing-inadequacy',
            'Urban Housing Inadequacy',
            'The percentage of urban residents living in slum conditions without access to adequate shelter.'
        )
    )
    db.commit()

    issue = db.execute(
        "SELECT id FROM issues WHERE slug = 'urban-housing-inadequacy'"
    ).fetchone()
    issue_id = issue['id']

    db.execute(
        '''
        INSERT OR IGNORE INTO indicators (issue_id, name, source, unit)
        VALUES (?, ?, ?, ?)
        ''',
        (
            issue_id,
            'Urban slum population',
            'World Bank',
            '% of urban population'
        )
    )
    db.commit()

    indicator = db.execute(
        "SELECT id FROM indicators WHERE name = 'Urban slum population'"
    ).fetchone()
    indicator_id = indicator['id']

    fetch_worldbank_housing(db, indicator_id, issue_id, system_user_id)


# Fetches urban slum population data from World Bank API and inserts as contributions
# Called by seed_housing_lens; writes to contributions and contribution_lens_links
def fetch_worldbank_housing(db, indicator_id, issue_id, system_user_id):
    """Fetch urban slum population rates from World Bank API."""

    # ISO alpha-3 codes — World Bank uses alpha-3, consistent with WHO food lens data
    target_countries = 'ZAF;PHL'

    url = f'https://api.worldbank.org/v2/country/{target_countries}/indicator/EN.POP.SLUM.UR.ZS'
    params = {
        'format': 'json',
        'per_page': 100,
        'mrv': 1  # most recent value only
    }

    print('Fetching World Bank housing data...')

    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        print(f'World Bank API request failed: {e}')
        return
    
    if not isinstance(data, list) or len(data) < 2:
        print('  World Bank API returned no data or an error.')
        return

    records = data[1]
    if not records:
        print('  No records returned.')
        return

    print(f'  {len(records)} records returned from World Bank API')

    inserted = 0
    for record in records:
        if record['value'] is None:
            continue
        
        country_code = record['countryiso3code']
        year = int(record['date'])
        value = record['value']
        
        # Create standardized note
        note_text = f"Official record: {value}% of urban population in {country_code} for {year}."
        source_url = "https://data.worldbank.org"
        
        # Insert into contributions
        db.execute(
            '''
            INSERT INTO contributions 
            (user_id, contribution_type, country_code, value, note, source_url, status, created_at, indicator_id)
            VALUES (?, 'data_point', ?, ?, ?, ?, 'approved', datetime('now'), ?)
            ''',
            (system_user_id, country_code, value, note_text, source_url, indicator_id)
        )
        
        # Get contribution ID and link to issue
        contribution = db.execute("SELECT last_insert_rowid() as id").fetchone()
        contribution_id = contribution['id']
        
        db.execute(
            '''
            INSERT INTO contribution_lens_links (contribution_id, issue_id)
            VALUES (?, ?)
            ''',
            (contribution_id, issue_id)
        )
        
        inserted += 1

    db.commit()
    print(f'  {inserted} new contributions inserted.')


# Seeds the mobility lens, its issues, indicators, and World Bank road mortality data
# Calls fetch_worldbank_mobility; writes to lenses, issues, indicators, and contributions in schema.sql
def seed_mobility_lens(db, system_user_id):
    """Seed the mobility lens with World Bank road traffic mortality data."""

    db.execute(
        '''
        INSERT OR IGNORE INTO lenses (slug, title, description)
        VALUES (?, ?, ?)
        ''',
        (
            'mobility',
            'Mobility',
            'How transport infrastructure decisions shape who lives, who dies, and who can move freely.'
        )
    )
    db.commit()

    lens = db.execute("SELECT id FROM lenses WHERE slug = 'mobility'").fetchone()
    lens_id = lens['id']

    db.execute(
        '''
        INSERT OR IGNORE INTO issues (lens_id, slug, title, description)
        VALUES (?, ?, ?, ?)
        ''',
        (
            lens_id,
            'road-traffic-mortality',
            'Road Traffic Mortality',
            'Deaths per 100,000 population caused by road traffic crashes — a direct measure of transport system safety.'
        )
    )
    db.commit()

    issue = db.execute(
        "SELECT id FROM issues WHERE slug = 'road-traffic-mortality'"
    ).fetchone()
    issue_id = issue['id']

    db.execute(
        '''
        INSERT OR IGNORE INTO indicators (issue_id, name, source, unit)
        VALUES (?, ?, ?, ?)
        ''',
        (
            issue_id,
            'Road traffic mortality rate',
            'World Bank / WHO',
            'per 100,000 population'
        )
    )
    db.commit()

    indicator = db.execute(
        "SELECT id FROM indicators WHERE name = 'Road traffic mortality rate'"
    ).fetchone()
    indicator_id = indicator['id']

    fetch_worldbank_mobility(db, indicator_id, issue_id, system_user_id)


# Fetches road traffic mortality data from World Bank API and inserts as contributions
# Called by seed_mobility_lens; writes to contributions and contribution_lens_links
def fetch_worldbank_mobility(db, indicator_id, issue_id, system_user_id):
    """Fetch road traffic mortality rates from World Bank API."""

    target_countries = 'AUS;NOR'

    url = f'https://api.worldbank.org/v2/country/{target_countries}/indicator/SH.STA.TRAF.P5'
    params = {
        'format': 'json',
        'per_page': 100,
        'mrv': 1
    }

    print('Fetching World Bank mobility data...')

    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        print(f'World Bank API request failed: {e}')
        return
    
    if not isinstance(data, list) or len(data) < 2:
        print('  World Bank API returned no data or an error.')
        return

    records = data[1]
    if not records:
        print('  No records returned.')
        return

    print(f'  {len(records)} records returned from World Bank API')

    inserted = 0
    for record in records:
        if record['value'] is None:
            continue
        
        country_code = record['countryiso3code']
        year = int(record['date'])
        value = record['value']
        
        # Create standardized note
        note_text = f"Official record: {value} deaths per 100,000 in {country_code} for {year}."
        source_url = "https://data.worldbank.org"
        
        # Insert into contributions
        db.execute(
            '''
            INSERT INTO contributions 
            (user_id, contribution_type, country_code, value, note, source_url, status, created_at, indicator_id)
            VALUES (?, 'data_point', ?, ?, ?, ?, 'approved', datetime('now'), ?)
            ''',
            (system_user_id, country_code, value, note_text, source_url, indicator_id)
        )
        
        # Get contribution ID and link to issue
        contribution = db.execute("SELECT last_insert_rowid() as id").fetchone()
        contribution_id = contribution['id']
        
        db.execute(
            '''
            INSERT INTO contribution_lens_links (contribution_id, issue_id)
            VALUES (?, ?)
            ''',
            (contribution_id, issue_id)
        )
        
        inserted += 1

    db.commit()
    print(f'  {inserted} new contributions inserted.')


if __name__ == '__main__':
    db = get_db()
    system_user_id = create_system_user(db)
    seed_food_lens(db, system_user_id)
    seed_housing_lens(db, system_user_id)
    seed_mobility_lens(db, system_user_id)
    db.close()
    print('Seeding complete.')