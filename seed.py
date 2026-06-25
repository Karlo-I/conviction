# seed.py
# Conviction: seeds the database with real data from WHO and other sources.
# Run after flask --app app init-db: python seed.py
# AI assistance: Claude (Anthropic) assisted with API query structure and data parsing.
# Logic, decisions, and direction are the author's own.

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


# Seed the food lens, issues, and indicators into the database, then triggers the data fetch
# Calls fetch_who_obesity; writes to lenses, issues, and indicators in schema.sql
def seed_food_lens(db):
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
        (
            lens_id,
            'food-insecurity',
            'Food Insecurity',
            'Systemic lack of reliable access to sufficient, safe, and nutritious food.'
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
    fetch_who_obesity(db, indicator_id)


# Fetch adult obesity rates from the WHO GHO API and inserts data points for target countries
# Called by seed_food_lenses(); writes to data_points table in schema.sql using indicator_id as foreign key
def fetch_who_obesity(db, indicator_id):
    """Fetch adult obesity rates from WHO GHO API and insert as data points."""

    # Countries selected for geographic diversity - not OECD-only
    # WHO API uses ISO 3166-1 alpha-3 codes — conversion to alpha-2 handled in heatmap layer (Week 3)
    target_countries = [
        'KEN', 'NGA', 'ZAF', 'EGY',         # Africa
        'PHL', 'IND', 'BGD', 'THA',         # Asia
        'MEX', 'BRA', 'COL',               # Latin America
        'CAN', 'GBR', 'AUS',               # Western
        'NOR',                           # Nordic
    ]

    # WHO GHO API source info: https://www.who.int/data/gho/info/gho-odata-api
    url = 'https://ghoapi.azureedge.net/api/NCD_BMI_30C'
    params = {
        '$filter': "Dim1 eq 'SEX_BTSX'",  # both sexes combined
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
        db.execute(
            '''
            INSERT OR IGNORE INTO data_points (indicator_id, country_code, year, value)
            VALUES (?, ?, ?, ?)
            ''',
            (indicator_id, country_code, point['year'], point['value'])
        )
        inserted += 1

    db.commit()
    print(f'  {inserted} data points inserted for {len(target_countries)} target countries')


if __name__ == '__main__':
    db = get_db()
    seed_food_lens(db)
    db.close()
    print('Seeding complete.')
