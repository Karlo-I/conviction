# seed.py
# Conviction: seeds the database with real data from WHO and other sources
# Run after flask --app app init-db: python seed.py
# AI assistance: Claude (Anthropic) assisted with API query structure and data parsing
# Logic, decisions, and direction are the author's own

import sqlite3
import requests
import json
from datetime import datetime, timezone


DATABASE = 'conviction.db'

def get_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db


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


def seed_food_lens(db, system_user_id):
    """Seed the food lens, its issues, indicators and WHO data points"""

    db.execute(
        'INSERT OR IGNORE INTO lenses (slug, title, description) VALUES (?, ?, ?)',
        (
            'food',
            'Food',
            'How the global food system shapes what people eat, who profits, and who bears the cost.'
        )
    )
    db.commit()

    lens = db.execute("SELECT id FROM lenses WHERE slug = 'food'").fetchone()
    lens_id = lens['id']

    db.execute(
        'INSERT OR IGNORE INTO issues (lens_id, slug, title, description) VALUES (?, ?, ?, ?)',
        (
            lens_id,
            'ultra-processed-food',
            'Ultra-Processed-Food',
            'Industrial food products engineered for overconsumption, dominant in supply global chains.'
        )
    )
    db.commit()

    upf_issue = db.execute("SELECT id FROM issues WHERE slug = 'ultra-processed-food'").fetchone()
    upf_issue_id = upf_issue['id']

    db.execute(
        'INSERT OR IGNORE INTO indicators (issue_id, name, source, unit) VALUES (?, ?, ?, ?)',
        (upf_issue_id, 'Adult obesity rate', 'WHO Global Health Observation', '%')
    )
    db.commit()

    obesity_indicator = db.execute("SELECT id FROM indicators WHERE name = 'Adult obesity rate'").fetchone()
    indicator_id = obesity_indicator['id']

    fetch_who_obesity(db, indicator_id, upf_issue_id, system_user_id)


def fetch_who_obesity(db, indicator_id, issue_id, system_user_id):
    """Fetch adult obesity rates from WHO GHO API and insert as contributions."""

    target_countries = ['CAN', 'BRA']
    url = 'https://ghoapi.azureedge.net/api/NCD_BMI_30C'
    country_filter = " or ".join([f"SpatialDim eq '{c}'" for c in target_countries])
    params = {
        '$filter': f"Dim1 eq 'SEX_BTSX' and ({country_filter})",
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

    latest = {}
    for record in records:
        country = record.get('SpatialDim')
        year = record.get('TimeDim')
        value = record.get('NumericValue')

        if country not in target_countries or value is None:
            continue
        if country not in latest or year > latest[country]['year']:
            latest[country] = {'year': year, 'value': value}

    inserted = 0
    for country_code, point in latest.items():
        note_text = f"Official record: {point['value']}% in {country_code} for {point['year']}."
        source_url = "https://www.who.int/data/gho/data/indicators/indicator-details/GHO/bmi-30-age-standardized-estimate-adults-18-years"
        
        db.execute(
            'INSERT INTO contributions (user_id, contribution_type, country_code, value, note, source_url, status, created_at, indicator_id) VALUES (?, ?, ?, ?, ?, ?, ?, datetime(\'now\'), ?)',
            (system_user_id, 'data_point', country_code, point['value'], note_text, source_url, 'approved', indicator_id)
        )
        
        contribution = db.execute("SELECT last_insert_rowid() as id").fetchone()
        contribution_id = contribution['id']
        
        db.execute('INSERT INTO contribution_lens_links (contribution_id, issue_id) VALUES (?, ?)', (contribution_id, issue_id))
        inserted += 1

    db.commit()
    print(f'  {inserted} new contributions inserted.')


def seed_housing_lens(db, system_user_id):
    """Seed the housing lens with World Bank urban slum population data."""

    db.execute(
        'INSERT OR IGNORE INTO lenses (slug, title, description) VALUES (?, ?, ?)',
        ('housing', 'Housing', 'How housing systems around the world fail to provide adequate shelter for urban populations.')
    )
    db.commit()

    lens = db.execute("SELECT id FROM lenses WHERE slug = 'housing'").fetchone()
    lens_id = lens['id']

    db.execute(
        'INSERT OR IGNORE INTO issues (lens_id, slug, title, description) VALUES (?, ?, ?, ?)',
        (lens_id, 'urban-housing-inadequacy', 'Urban Housing Inadequacy', 'The percentage of urban residents living in slum conditions without access to adequate shelter.')
    )
    db.commit()

    issue = db.execute("SELECT id FROM issues WHERE slug = 'urban-housing-inadequacy'").fetchone()
    issue_id = issue['id']

    db.execute(
        'INSERT OR IGNORE INTO indicators (issue_id, name, source, unit) VALUES (?, ?, ?, ?)',
        (issue_id, 'Urban slum population', 'World Bank', '% of urban population')
    )
    db.commit()

    indicator = db.execute("SELECT id FROM indicators WHERE name = 'Urban slum population'").fetchone()
    indicator_id = indicator['id']

    fetch_worldbank_housing(db, indicator_id, issue_id, system_user_id)


def fetch_worldbank_housing(db, indicator_id, issue_id, system_user_id):
    """Fetch urban slum population rates from World Bank API."""

    target_countries = 'ZAF;PHL'
    url = f'https://api.worldbank.org/v2/country/{target_countries}/indicator/EN.POP.SLUM.UR.ZS'
    params = {'format': 'json', 'per_page': 100, 'mrv': 1}

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
        
        note_text = f"Official record: {value}% of urban population in {country_code} for {year}."
        source_url = "https://data.worldbank.org/indicator/EN.POP.SLUM.UR.ZS"
        
        db.execute(
            'INSERT INTO contributions (user_id, contribution_type, country_code, value, note, source_url, status, created_at, indicator_id) VALUES (?, ?, ?, ?, ?, ?, ?, datetime(\'now\'), ?)',
            (system_user_id, 'data_point', country_code, value, note_text, source_url, 'approved', indicator_id)
        )
        
        contribution = db.execute("SELECT last_insert_rowid() as id").fetchone()
        contribution_id = contribution['id']
        
        db.execute('INSERT INTO contribution_lens_links (contribution_id, issue_id) VALUES (?, ?)', (contribution_id, issue_id))
        inserted += 1

    db.commit()
    print(f'  {inserted} new contributions inserted.')


def seed_mobility_lens(db, system_user_id):
    """Seed the mobility lens with World Bank road traffic mortality data."""

    db.execute(
        'INSERT OR IGNORE INTO lenses (slug, title, description) VALUES (?, ?, ?)',
        ('mobility', 'Mobility', 'How transport infrastructure decisions shape who lives, who dies, and who can move freely.')
    )
    db.commit()

    lens = db.execute("SELECT id FROM lenses WHERE slug = 'mobility'").fetchone()
    lens_id = lens['id']

    db.execute(
        'INSERT OR IGNORE INTO issues (lens_id, slug, title, description) VALUES (?, ?, ?, ?)',
        (lens_id, 'road-traffic-mortality', 'Road Traffic Mortality', 'Deaths per 100,000 population caused by road traffic crashes — a direct measure of transport system safety.')
    )
    db.commit()

    issue = db.execute("SELECT id FROM issues WHERE slug = 'road-traffic-mortality'").fetchone()
    issue_id = issue['id']

    db.execute(
        'INSERT OR IGNORE INTO indicators (issue_id, name, source, unit) VALUES (?, ?, ?, ?)',
        (issue_id, 'Road traffic mortality rate', 'World Bank / WHO', 'per 100,000 population')
    )
    db.commit()

    indicator = db.execute("SELECT id FROM indicators WHERE name = 'Road traffic mortality rate'").fetchone()
    indicator_id = indicator['id']

    fetch_worldbank_mobility(db, indicator_id, issue_id, system_user_id)


def fetch_worldbank_mobility(db, indicator_id, issue_id, system_user_id):
    """Fetch road traffic mortality rates from World Bank API."""

    target_countries = 'AUS;NOR'
    url = f'https://api.worldbank.org/v2/country/{target_countries}/indicator/SH.STA.TRAF.P5'
    params = {'format': 'json', 'per_page': 100, 'mrv': 1}

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
        
        note_text = f"Official record: {value} deaths per 100,000 in {country_code} for {year}."
        source_url = "https://data.worldbank.org/indicator/SH.STA.TRAF.P5"
        
        db.execute(
            'INSERT INTO contributions (user_id, contribution_type, country_code, value, note, source_url, status, created_at, indicator_id) VALUES (?, ?, ?, ?, ?, ?, ?, datetime(\'now\'), ?)',
            (system_user_id, 'data_point', country_code, value, note_text, source_url, 'approved', indicator_id)
        )
        
        contribution = db.execute("SELECT last_insert_rowid() as id").fetchone()
        contribution_id = contribution['id']
        
        db.execute('INSERT INTO contribution_lens_links (contribution_id, issue_id) VALUES (?, ?)', (contribution_id, issue_id))
        inserted += 1

    db.commit()
    print(f'  {inserted} new contributions inserted.')


def seed_energy_lens(db, system_user_id):
    """Seed the energy lens with climate and access issues."""
    
    db.execute(
        'INSERT OR IGNORE INTO lenses (slug, title, description) VALUES (?, ?, ?)',
        ('energy', 'Energy', 'How energy systems determine who thrives, who survives, and who is left in the dark.')
    )
    db.commit()
    
    lens = db.execute("SELECT id FROM lenses WHERE slug = 'energy'").fetchone()
    lens_id = lens['id']
    
    issues = [
        (lens_id, 'energy-poverty', 'Energy Poverty', 'Lack of access to affordable, reliable energy services'),
        (lens_id, 'fossil-fuel-dependency', 'Fossil Fuel Dependency', 'Economic and infrastructural lock-in to carbon-intensive energy sources'),
    ]
    
    for issue in issues:
        db.execute('INSERT OR IGNORE INTO issues (lens_id, slug, title, description) VALUES (?, ?, ?, ?)', issue)
    db.commit()
    
    print('Seeded Energy lens with 2 issues')


def seed_healthcare_lens(db, system_user_id):
    """Seed the healthcare lens with access and affordability issues."""
    
    db.execute(
        'INSERT OR IGNORE INTO lenses (slug, title, description) VALUES (?, ?, ?)',
        ('healthcare', 'Healthcare', 'How healthcare systems determine who gets healed, who gets billed, and who gets left behind.')
    )
    db.commit()
    
    lens = db.execute("SELECT id FROM lenses WHERE slug = 'healthcare'").fetchone()
    lens_id = lens['id']
    
    issues = [
        (lens_id, 'healthcare-access', 'Healthcare Access', 'Barriers to obtaining timely, affordable, and quality medical care'),
        (lens_id, 'pharmaceutical-pricing', 'Pharmaceutical Pricing', 'Drug pricing mechanisms that prioritize profit over patient access'),
    ]
    
    for issue in issues:
        db.execute('INSERT OR IGNORE INTO issues (lens_id, slug, title, description) VALUES (?, ?, ?, ?)', issue)
    db.commit()
    
    print('Seeded Healthcare lens with 2 issues')


def seed_forces_layer(db, system_user_id):
    """Seed the forces layer with pre-approved systemic mechanisms."""
    
    print('Seeding Forces layer...')
    
    issues = {}
    issue_slugs = [
        'ultra-processed-food', 'urban-housing-inadequacy', 'road-traffic-mortality',
        'energy-poverty', 'fossil-fuel-dependency', 'healthcare-access', 'pharmaceutical-pricing'
    ]
    
    for slug in issue_slugs:
        issue = db.execute("SELECT id FROM issues WHERE slug = ?", (slug,)).fetchone()
        if issue:
            issues[slug] = issue['id']
    
    forces_data = [
        {
            'slug': 'private-equity-extraction-healthcare',
            'title': 'Private equity extraction from essential care systems',
            'category': 'financial_capture',
            'mechanism': 'Financial investors acquire healthcare providers, load them with debt, extract fees, and sell assets—prioritizing investor returns over patient care.',
            'evidence_chain': [
                {
                    'claim': 'Private equity firms acquire hospitals and clinics, then charge them management fees and load them with debt.',
                    'source_url': 'https://www.healthaffairs.org/doi/10.1377/hlthaff.2019.00686',
                    'data_summary': 'PE-owned facilities show higher bankruptcy rates and reduced quality of care'
                }
            ],
            'linked_issues': ['healthcare-access', 'pharmaceutical-pricing']
        },
        {
            'slug': 'environmental-externalities-fast-fashion',
            'title': 'Fast fashion externalizes environmental costs onto communities',
            'category': 'externalised_cost',
            'mechanism': 'Clothing brands profit from cheap production while communities bear the costs of pollution, waste, and resource depletion.',
            'evidence_chain': [
                {
                    'claim': 'Textile production is responsible for 10% of global carbon emissions.',
                    'source_url': 'https://www.ellenmacarthurfoundation.org/topics/fashion/overview',
                    'data_summary': 'Fashion industry emits more CO2 than international aviation and shipping combined'
                },
                {
                    'claim': 'Microplastic pollution from synthetic fabrics contaminates water systems.',
                    'source_url': 'https://www.iucn.org/resources/issues-briefs/marine-plastic-pollution',
                    'data_summary': '35% of microplastics in oceans come from synthetic textiles'
                }
            ],
            'linked_issues': ['ultra-processed-food', 'road-traffic-mortality']
        },
        {
            'slug': 'pharmaceutical-patent-evergreening',
            'title': 'Pharmaceutical companies extend monopolies through patent manipulation',
            'category': 'information_asymmetry',
            'mechanism': 'Drug manufacturers make minor modifications to existing medications and file new patents, blocking generic competition and maintaining high prices.',
            'evidence_chain': [
                {
                    'claim': 'Patients pay 4-10x more for branded drugs versus generics.',
                    'source_url': 'https://www.who.int/publications/i/item/9789241515078',
                    'data_summary': 'Life-saving medications remain unaffordable in low-income countries'
                }
            ],
            'linked_issues': ['healthcare-access', 'pharmaceutical-pricing']
        },
        {
            'slug': 'fossil-fuel-subsidy-lock-in',
            'title': 'Fossil fuel subsidies create structural dependency on carbon-intensive energy',
            'category': 'regulatory_capture',
            'mechanism': 'Government subsidies for oil, gas, and coal distort markets, making renewable energy less competitive and locking in climate-damaging infrastructure.',
            'evidence_chain': [
                {
                    'claim': 'Global fossil fuel subsidies exceed $7 trillion annually.',
                    'source_url': 'https://www.imf.org/en/Topics/climate-change/energy-subsidies',
                    'data_summary': 'Subsidies include direct payments and unpriced environmental costs'
                },
                {
                    'claim': 'Renewable energy receives only 10% of fossil fuel subsidy levels.',
                    'source_url': 'https://www.iea.org/reports/world-energy-outlook-2023',
                    'data_summary': 'Market distortion slows clean energy transition'
                }
            ],
            'linked_issues': ['energy-poverty', 'fossil-fuel-dependency']
        }
    ]
    
    inserted_forces = 0
    for force_data in forces_data:
        db.execute(
            'INSERT OR IGNORE INTO forces (slug, title, category, mechanism, evidence_chain, created_at) VALUES (?, ?, ?, ?, ?, datetime(\'now\'))',
            (
                force_data['slug'],
                force_data['title'],
                force_data['category'],
                force_data['mechanism'],
                json.dumps(force_data['evidence_chain'])
            )
        )
        
        force = db.execute("SELECT id FROM forces WHERE slug = ?", (force_data['slug'],)).fetchone()
        if force:
            force_id = force['id']
            
            for issue_slug in force_data['linked_issues']:
                if issue_slug in issues:
                    db.execute(
                        'INSERT OR IGNORE INTO force_issue_links (force_id, issue_id, explanation) VALUES (?, ?, ?)',
                        (force_id, issues[issue_slug], force_data['mechanism'])
                    )
            
            inserted_forces += 1
    
    db.commit()
    print(f'  {inserted_forces} forces inserted with cross-lens links')


if __name__ == '__main__':
    db = get_db()
    system_user_id = create_system_user(db)
    
    seed_food_lens(db, system_user_id)
    seed_housing_lens(db, system_user_id)
    seed_mobility_lens(db, system_user_id)
    
    seed_energy_lens(db, system_user_id)
    seed_healthcare_lens(db, system_user_id)
    
    seed_forces_layer(db, system_user_id)
    
    db.close()
    print('\n✅ Seeding complete!')
    print('   - 5 lenses seeded (3 with API data, 2 structure-only)')
    print('   - 7 forces seeded with evidence chains and cross-lens links')
    print('   - All sources properly deep-linked')
    print('   - Ready for demo!')