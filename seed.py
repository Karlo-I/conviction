# seed.py
# Conviction: seeds the database structure (lenses, issues, indicators, forces).
# Run via web route: /seed-data
# AI assistance: Both Claude (Anthropic) and Qwen.ai (3.7-Plus) assisted with query structure and error handling patterns.
# Logic, decisions, and direction are the author's own

import json
import os
import psycopg2
import sqlite3
from datetime import datetime, timezone


# Create the Data Archive system user if it doesn't exist
def create_system_user(db, use_postgresql):
    if use_postgresql:
        cursor = db.conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = %s", ('Data Archive',))
        user = cursor.fetchone()
        
        if not user:
            cursor.execute(
                "INSERT INTO users (username, password_hash) VALUES (%s, %s) RETURNING id",
                ('Data Archive', 'dummy_hash_for_system_user')
            )
            system_user_id = cursor.fetchone()[0]
            db.conn.commit()
            print(f'Created Data Archive user with ID: {system_user_id}')
        else:
            system_user_id = user[0]
            print(f'Data Archive user already exists with ID: {system_user_id}')
        cursor.close()
    else:
        user = db.execute("SELECT id FROM users WHERE username = 'Data Archive'").fetchone()
        
        if not user:
            db.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", 
                       ('Data Archive', 'dummy_hash_for_system_user'))
            db.commit()
            user = db.execute("SELECT id FROM users WHERE username = 'Data Archive'").fetchone()
            system_user_id = user['id']
            print(f'Created Data Archive user with ID: {system_user_id}')
        else:
            system_user_id = user['id']
            print(f'Data Archive user already exists with ID: {system_user_id}')
    
    return system_user_id


# Seed the food lens, its issues, indicators and initial evidence
def seed_food_lens(db, system_user_id, use_postgresql):
    if use_postgresql:
        cursor = db.conn.cursor()
        cursor.execute(
            "INSERT INTO lenses (slug, title, description) VALUES (%s, %s, %s) ON CONFLICT (slug) DO NOTHING",
            ('food', 'Food', 'How the global food system shapes what people eat, who profits, and who bears the cost.')
        )
        db.conn.commit()
        cursor.execute("SELECT id FROM lenses WHERE slug = 'food'")
        lens_id = cursor.fetchone()[0]
        
        cursor.execute(
            "INSERT INTO issues (lens_id, slug, title, description, context) VALUES (%s, %s, %s, %s, %s) ON CONFLICT (slug) DO NOTHING",
            (lens_id, 'ultra-processed-food', 'Ultra-Processed-Food', 'Industrial food products engineered for overconsumption, dominant in supply global chains.', 'High obesity rates are not merely individual choices, but a direct consequence of food environments saturated with cheap, ultra-processed products. This reveals how global supply chains prioritize profit over human health, disproportionately impacting communities with limited access to whole foods.')
        )
        db.conn.commit()
        cursor.execute("SELECT id FROM issues WHERE slug = 'ultra-processed-food'")
        upf_issue_id = cursor.fetchone()[0]
        
        cursor.execute(
            "INSERT INTO indicators (issue_id, name, source, unit) VALUES (%s, %s, %s, %s) ON CONFLICT (issue_id, name) DO NOTHING",
            (upf_issue_id, 'Adult obesity rate', 'WHO Global Health Observation', '%')
        )
        db.conn.commit()
        
        # Fetch the indicator ID so we can link the evidence to it
        cursor.execute("SELECT id FROM indicators WHERE name = 'Adult obesity rate' AND issue_id = %s", (upf_issue_id,))
        indicator_id = cursor.fetchone()[0]
        
        # Evidence seed
        cursor.execute(
            "INSERT INTO contributions (user_id, indicator_id, country_code, note, source_url, status, created_at) VALUES (%s, %s, %s, %s, %s, %s, NOW()) RETURNING id",
            (system_user_id, indicator_id, 'MEX', 'In Mexico, the prevalence of obesity among adults has reached critical levels, driven largely by the dominance of ultra-processed food products in the national diet and limited access to fresh, nutritious alternatives in marginalized areas.', 'https://www.who.int/mexico/news/detail/obesity-report-mexico', 'approved')
        )
        contrib_id = cursor.fetchone()[0]
        cursor.execute(
            "INSERT INTO contribution_lens_links (contribution_id, issue_id) VALUES (%s, %s)",
            (contrib_id, upf_issue_id)
        )
        db.conn.commit()
        cursor.close()
        
    else:
        db.execute(
            'INSERT OR IGNORE INTO lenses (slug, title, description) VALUES (?, ?, ?)',
            ('food', 'Food', 'How the global food system shapes what people eat, who profits, and who bears the cost.')
        )
        db.commit()
        lens = db.execute("SELECT id FROM lenses WHERE slug = 'food'").fetchone()
        lens_id = lens['id']
        
        db.execute(
            'INSERT OR IGNORE INTO issues (lens_id, slug, title, description, context) VALUES (?, ?, ?, ?, ?)',
            (lens_id, 'ultra-processed-food', 'Ultra-Processed-Food', 'Industrial food products engineered for overconsumption, dominant in supply global chains.', 'High obesity rates are not merely individual choices, but a direct consequence of food environments saturated with cheap, ultra-processed products. This reveals how global supply chains prioritize profit over human health, disproportionately impacting communities with limited access to whole foods.')
        )
        db.commit()
        upf_issue = db.execute("SELECT id FROM issues WHERE slug = 'ultra-processed-food'").fetchone()
        upf_issue_id = upf_issue['id']
        
        db.execute(
            'INSERT OR IGNORE INTO indicators (issue_id, name, source, unit) VALUES (?, ?, ?, ?)',
            (upf_issue_id, 'Adult obesity rate', 'WHO Global Health Observation', '%')
        )
        db.commit()
        
        # Fetch the indicator ID so we can link the evidence to it
        indicator = db.execute("SELECT id FROM indicators WHERE name = 'Adult obesity rate' AND issue_id = ?", (upf_issue_id,)).fetchone()
        indicator_id = indicator['id']
        
        # Evidence seed
        db.execute(
            'INSERT INTO contributions (user_id, indicator_id, country_code, note, source_url, status, created_at) VALUES (?, ?, ?, ?, ?, ?, datetime(\'now\'))',
            (system_user_id, indicator_id, 'MEX', 'In Mexico, the prevalence of obesity among adults has reached critical levels, driven largely by the dominance of ultra-processed food products in the national diet and limited access to fresh, nutritious alternatives in marginalized areas.', 'https://www.who.int/mexico/news/detail/obesity-report-mexico', 'approved')
        )
        contrib = db.execute("SELECT last_insert_rowid() as id").fetchone()
        db.execute('INSERT INTO contribution_lens_links (contribution_id, issue_id) VALUES (?, ?)', (contrib['id'], upf_issue_id))
        db.commit()
    
    print('  Seeded Food lens structure and initial evidence.')


# Seed the housing lens with its issues and indicators
def seed_housing_lens(db, system_user_id, use_postgresql):
    if use_postgresql:
        cursor = db.conn.cursor()
        cursor.execute(
            "INSERT INTO lenses (slug, title, description) VALUES (%s, %s, %s) ON CONFLICT (slug) DO NOTHING",
            ('housing', 'Housing', 'How housing systems around the world fail to provide adequate shelter for urban populations.')
        )
        db.conn.commit()
        cursor.execute("SELECT id FROM lenses WHERE slug = 'housing'")
        lens_id = cursor.fetchone()[0]
        
        cursor.execute(
            "INSERT INTO issues (lens_id, slug, title, description, context) VALUES (%s, %s, %s, %s, %s) ON CONFLICT (slug) DO NOTHING",
            (lens_id, 'urban-housing-inadequacy', 'Urban Housing Inadequacy', 'The percentage of urban residents living in slum conditions without access to adequate shelter.', 'The prevalence of urban slum conditions highlights a systemic failure to treat housing as a fundamental human right rather than a speculative asset. This exposes how rapid urbanization and inadequate public investment force marginalized populations into environments lacking basic sanitation and security.')
        )
        db.conn.commit()
        cursor.execute("SELECT id FROM issues WHERE slug = 'urban-housing-inadequacy'")
        issue_id = cursor.fetchone()[0]
        
        cursor.execute(
            "INSERT INTO indicators (issue_id, name, source, unit) VALUES (%s, %s, %s, %s) ON CONFLICT (issue_id, name) DO NOTHING",
            (issue_id, 'Urban slum population', 'World Bank', '% of urban population')
        )
        db.conn.commit()
        cursor.close()
    else:
        db.execute(
            'INSERT OR IGNORE INTO lenses (slug, title, description) VALUES (?, ?, ?)',
            ('housing', 'Housing', 'How housing systems around the world fail to provide adequate shelter for urban populations.')
        )
        db.commit()
        lens = db.execute("SELECT id FROM lenses WHERE slug = 'housing'").fetchone()
        lens_id = lens['id']
        
        db.execute(
            'INSERT OR IGNORE INTO issues (lens_id, slug, title, description, context) VALUES (?, ?, ?, ?, ?)',
            (lens_id, 'urban-housing-inadequacy', 'Urban Housing Inadequacy', 'The percentage of urban residents living in slum conditions without access to adequate shelter.', 'The prevalence of urban slum conditions highlights a systemic failure to treat housing as a fundamental human right rather than a speculative asset. This exposes how rapid urbanization and inadequate public investment force marginalized populations into environments lacking basic sanitation and security.')
        )
        db.commit()
        issue = db.execute("SELECT id FROM issues WHERE slug = 'urban-housing-inadequacy'").fetchone()
        issue_id = issue['id']
        
        db.execute(
            'INSERT OR IGNORE INTO indicators (issue_id, name, source, unit) VALUES (?, ?, ?, ?)',
            (issue_id, 'Urban slum population', 'World Bank', '% of urban population')
        )
        db.commit()
    
    print('  Seeded Housing lens structure.')


# Seed the mobility lens with its issues, indicators, and initial evidence
def seed_mobility_lens(db, system_user_id, use_postgresql):
    if use_postgresql:
        cursor = db.conn.cursor()
        cursor.execute(
            "INSERT INTO lenses (slug, title, description) VALUES (%s, %s, %s) ON CONFLICT (slug) DO NOTHING",
            ('mobility', 'Mobility', 'How transport infrastructure decisions shape who lives, who dies, and who can move freely.')
        )
        db.conn.commit()
        cursor.execute("SELECT id FROM lenses WHERE slug = 'mobility'")
        lens_id = cursor.fetchone()[0]
        
        cursor.execute(
            "INSERT INTO issues (lens_id, slug, title, description, context) VALUES (%s, %s, %s, %s, %s) ON CONFLICT (slug) DO NOTHING",
            (lens_id, 'road-traffic-mortality', 'Road Traffic Mortality', 'Deaths per 100,000 population caused by road traffic crashes — a direct measure of transport system safety.', 'Traffic mortality rates are a stark measure of how transport infrastructure prioritizes vehicle throughput over human life. This reveals the hidden costs of car-centric urban planning, which disproportionately endangers pedestrians, cyclists, and lower-income neighborhoods.')
        )
        db.conn.commit()
        cursor.execute("SELECT id FROM issues WHERE slug = 'road-traffic-mortality'")
        issue_id = cursor.fetchone()[0]
        
        cursor.execute(
            "INSERT INTO indicators (issue_id, name, source, unit) VALUES (%s, %s, %s, %s) ON CONFLICT (issue_id, name) DO NOTHING",
            (issue_id, 'Road traffic mortality rate', 'World Bank / WHO', 'per 100,000 population')
        )
        db.conn.commit()
        
        # Fetch the indicator ID
        cursor.execute("SELECT id FROM indicators WHERE name = 'Road traffic mortality rate' AND issue_id = %s", (issue_id,))
        indicator_id = cursor.fetchone()[0]
        
        # Seed evidence
        cursor.execute(
            "INSERT INTO contributions (user_id, indicator_id, country_code, note, source_url, status, created_at) VALUES (%s, %s, %s, %s, %s, %s, NOW()) RETURNING id",
            (system_user_id, indicator_id, 'MEX', 'Mexico faces a severe road traffic mortality crisis, with vulnerable road users—particularly pedestrians and cyclists—bearing the brunt of traffic fatalities. Inadequate street design, lack of protected infrastructure, and weak enforcement of traffic laws contribute to disproportionately high death rates in urban areas.', 'https://www.who.int/news-room/fact-sheets/detail/road-traffic-injuries', 'approved')
        )
        contrib_id = cursor.fetchone()[0]
        cursor.execute(
            "INSERT INTO contribution_lens_links (contribution_id, issue_id) VALUES (%s, %s)",
            (contrib_id, issue_id)
        )
        db.conn.commit()
        cursor.close()
        
    else:
        db.execute(
            'INSERT OR IGNORE INTO lenses (slug, title, description) VALUES (?, ?, ?)',
            ('mobility', 'Mobility', 'How transport infrastructure decisions shape who lives, who dies, and who can move freely.')
        )
        db.commit()
        lens = db.execute("SELECT id FROM lenses WHERE slug = 'mobility'").fetchone()
        lens_id = lens['id']
        
        db.execute(
            'INSERT OR IGNORE INTO issues (lens_id, slug, title, description, context) VALUES (?, ?, ?, ?, ?)',
            (lens_id, 'road-traffic-mortality', 'Road Traffic Mortality', 'Deaths per 100,000 population caused by road traffic crashes — a direct measure of transport system safety.', 'Traffic mortality rates are a stark measure of how transport infrastructure prioritizes vehicle throughput over human life. This reveals the hidden costs of car-centric urban planning, which disproportionately endangers pedestrians, cyclists, and lower-income neighborhoods.')
        )
        db.commit()
        issue = db.execute("SELECT id FROM issues WHERE slug = 'road-traffic-mortality'").fetchone()
        issue_id = issue['id']
        
        db.execute(
            'INSERT OR IGNORE INTO indicators (issue_id, name, source, unit) VALUES (?, ?, ?, ?)',
            (issue_id, 'Road traffic mortality rate', 'World Bank / WHO', 'per 100,000 population')
        )
        db.commit()
        
        # Fetch the indicator ID
        indicator = db.execute("SELECT id FROM indicators WHERE name = 'Road traffic mortality rate' AND issue_id = ?", (issue_id,)).fetchone()
        indicator_id = indicator['id']
        
        # Seed evidence
        db.execute(
            'INSERT INTO contributions (user_id, indicator_id, country_code, note, source_url, status, created_at) VALUES (?, ?, ?, ?, ?, ?, datetime(\'now\'))',
            (system_user_id, indicator_id, 'MEX', 'Mexico faces a severe road traffic mortality crisis, with vulnerable road users—particularly pedestrians and cyclists—bearing the brunt of traffic fatalities. Inadequate street design, lack of protected infrastructure, and weak enforcement of traffic laws contribute to disproportionately high death rates in urban areas.', 'https://www.who.int/news-room/fact-sheets/detail/road-traffic-injuries', 'approved')
        )
        contrib = db.execute("SELECT last_insert_rowid() as id").fetchone()
        db.execute('INSERT INTO contribution_lens_links (contribution_id, issue_id) VALUES (?, ?)', (contrib['id'], issue_id))
        db.commit()
    
    print('  Seeded Mobility lens structure and initial evidence.')


# Seed the energy lens with climate and access issues
def seed_energy_lens(db, system_user_id, use_postgresql):
    if use_postgresql:
        cursor = db.conn.cursor()
        cursor.execute(
            "INSERT INTO lenses (slug, title, description) VALUES (%s, %s, %s) ON CONFLICT (slug) DO NOTHING",
            ('energy', 'Energy', 'How energy systems determine who thrives, who survives, and who is left in the dark.')
        )
        db.conn.commit()
        cursor.execute("SELECT id FROM lenses WHERE slug = 'energy'")
        lens_id = cursor.fetchone()[0]
        
        issues = [
            (lens_id, 'energy-poverty', 'Energy Poverty', 'Lack of access to affordable, reliable energy services', 'Energy poverty demonstrates how access to modern, reliable power is unevenly distributed, leaving vulnerable populations dependent on expensive or unreliable sources. This highlights the systemic barrier that lack of energy access creates for education, healthcare, and economic mobility.'),
            (lens_id, 'fossil-fuel-dependency', 'Fossil Fuel Dependency', 'Economic and infrastructural lock-in to carbon-intensive energy sources', 'Continued reliance on fossil fuels is sustained by deeply entrenched infrastructure and financial incentives that actively resist decarbonization. This reveals the structural lock-in that delays renewable energy adoption, externalizing the true costs of climate change onto frontline communities.'),
        ]
        
        for issue in issues:
            cursor.execute(
                "INSERT INTO issues (lens_id, slug, title, description, context) VALUES (%s, %s, %s, %s, %s) ON CONFLICT (slug) DO NOTHING",
                issue
            )
        db.conn.commit()
        
        cursor.execute("SELECT id FROM issues WHERE slug = 'energy-poverty'")
        energy_poverty_id = cursor.fetchone()[0]
        cursor.execute("SELECT id FROM issues WHERE slug = 'fossil-fuel-dependency'")
        fossil_fuel_id = cursor.fetchone()[0]
        
        cursor.execute(
            "INSERT INTO indicators (issue_id, name, source, unit) VALUES (%s, %s, %s, %s) ON CONFLICT (issue_id, name) DO NOTHING",
            (energy_poverty_id, 'Energy access rate', 'World Bank', '% of population')
        )
        cursor.execute(
            "INSERT INTO indicators (issue_id, name, source, unit) VALUES (%s, %s, %s, %s) ON CONFLICT (issue_id, name) DO NOTHING",
            (fossil_fuel_id, 'Renewable energy share', 'IEA', '% of total energy')
        )
        db.conn.commit()
        cursor.close()
    else:
        db.execute(
            'INSERT OR IGNORE INTO lenses (slug, title, description) VALUES (?, ?, ?)',
            ('energy', 'Energy', 'How energy systems determine who thrives, who survives, and who is left in the dark.')
        )
        db.commit()
        lens = db.execute("SELECT id FROM lenses WHERE slug = 'energy'").fetchone()
        lens_id = lens['id']
        
        issues = [
            (lens_id, 'energy-poverty', 'Energy Poverty', 'Lack of access to affordable, reliable energy services', 'Energy poverty demonstrates how access to modern, reliable power is unevenly distributed, leaving vulnerable populations dependent on expensive or unreliable sources. This highlights the systemic barrier that lack of energy access creates for education, healthcare, and economic mobility.'),
            (lens_id, 'fossil-fuel-dependency', 'Fossil Fuel Dependency', 'Economic and infrastructural lock-in to carbon-intensive energy sources', 'Continued reliance on fossil fuels is sustained by deeply entrenched infrastructure and financial incentives that actively resist decarbonization. This reveals the structural lock-in that delays renewable energy adoption, externalizing the true costs of climate change onto frontline communities.'),
        ]
        
        for issue in issues:
            db.execute('INSERT OR IGNORE INTO issues (lens_id, slug, title, description, context) VALUES (?, ?, ?, ?, ?)', issue)
        db.commit()
        
        energy_poverty = db.execute("SELECT id FROM issues WHERE slug = 'energy-poverty'").fetchone()
        energy_poverty_id = energy_poverty['id']
        fossil_fuel = db.execute("SELECT id FROM issues WHERE slug = 'fossil-fuel-dependency'").fetchone()
        fossil_fuel_id = fossil_fuel['id']
        
        db.execute(
            'INSERT OR IGNORE INTO indicators (issue_id, name, source, unit) VALUES (?, ?, ?, ?)',
            (energy_poverty_id, 'Energy access rate', 'World Bank', '% of population')
        )
        db.execute(
            'INSERT OR IGNORE INTO indicators (issue_id, name, source, unit) VALUES (?, ?, ?, ?)',
            (fossil_fuel_id, 'Renewable energy share', 'IEA', '% of total energy')
        )
        db.commit()
    
    print('  Seeded Energy lens structure.')


# Seed the healthcare lens with access and affordability issues
def seed_healthcare_lens(db, system_user_id, use_postgresql):
    if use_postgresql:
        cursor = db.conn.cursor()
        cursor.execute(
            "INSERT INTO lenses (slug, title, description) VALUES (%s, %s, %s) ON CONFLICT (slug) DO NOTHING",
            ('healthcare', 'Healthcare', 'How healthcare systems determine who gets healed, who gets billed, and who gets left behind.')
        )
        db.conn.commit()
        cursor.execute("SELECT id FROM lenses WHERE slug = 'healthcare'")
        lens_id = cursor.fetchone()[0]
        
        issues = [
            (lens_id, 'healthcare-access', 'Healthcare Access', 'Barriers to obtaining timely, affordable, and quality medical care', 'Barriers to healthcare access expose fundamental inequities in systems that treat medical care as a commodity rather than a public good. This reveals how geographic, financial, and administrative hurdles systematically prevent vulnerable populations from receiving timely, life-saving interventions.'),
            (lens_id, 'pharmaceutical-pricing', 'Pharmaceutical Pricing', 'Drug pricing mechanisms that prioritize profit over patient access', 'Pharmaceutical pricing mechanisms often prioritize shareholder returns over patient survival by leveraging patent monopolies to keep essential drug prices artificially high. This highlights the systemic tension between innovation incentives and the moral imperative to make life-saving treatments universally affordable.'),
        ]
        
        for issue in issues:
            cursor.execute(
                "INSERT INTO issues (lens_id, slug, title, description, context) VALUES (%s, %s, %s, %s, %s) ON CONFLICT (slug) DO NOTHING",
                issue
            )
        db.conn.commit()
        
        cursor.execute("SELECT id FROM issues WHERE slug = 'healthcare-access'")
        healthcare_access_id = cursor.fetchone()[0]
        cursor.execute("SELECT id FROM issues WHERE slug = 'pharmaceutical-pricing'")
        pharma_pricing_id = cursor.fetchone()[0]
        
        cursor.execute(
            "INSERT INTO indicators (issue_id, name, source, unit) VALUES (%s, %s, %s, %s) ON CONFLICT (issue_id, name) DO NOTHING",
            (healthcare_access_id, 'Healthcare access index', 'WHO', '0-100 scale')
        )
        cursor.execute(
            "INSERT INTO indicators (issue_id, name, source, unit) VALUES (%s, %s, %s, %s) ON CONFLICT (issue_id, name) DO NOTHING",
            (pharma_pricing_id, 'Medicine affordability', 'WHO', '% of income')
        )
        db.conn.commit()
        cursor.close()
    else:
        db.execute(
            'INSERT OR IGNORE INTO lenses (slug, title, description) VALUES (?, ?, ?)',
            ('healthcare', 'Healthcare', 'How healthcare systems determine who gets healed, who gets billed, and who gets left behind.')
        )
        db.commit()
        lens = db.execute("SELECT id FROM lenses WHERE slug = 'healthcare'").fetchone()
        lens_id = lens['id']
        
        issues = [
            (lens_id, 'healthcare-access', 'Healthcare Access', 'Barriers to obtaining timely, affordable, and quality medical care', 'Barriers to healthcare access expose fundamental inequities in systems that treat medical care as a commodity rather than a public good. This reveals how geographic, financial, and administrative hurdles systematically prevent vulnerable populations from receiving timely, life-saving interventions.'),
            (lens_id, 'pharmaceutical-pricing', 'Pharmaceutical Pricing', 'Drug pricing mechanisms that prioritize profit over patient access', 'Pharmaceutical pricing mechanisms often prioritize shareholder returns over patient survival by leveraging patent monopolies to keep essential drug prices artificially high. This highlights the systemic tension between innovation incentives and the moral imperative to make life-saving treatments universally affordable.'),
        ]
        
        for issue in issues:
            db.execute('INSERT OR IGNORE INTO issues (lens_id, slug, title, description, context) VALUES (?, ?, ?, ?, ?)', issue)
        db.commit()
        
        healthcare_access = db.execute("SELECT id FROM issues WHERE slug = 'healthcare-access'").fetchone()
        healthcare_access_id = healthcare_access['id']
        pharma_pricing = db.execute("SELECT id FROM issues WHERE slug = 'pharmaceutical-pricing'").fetchone()
        pharma_pricing_id = pharma_pricing['id']
        
        db.execute(
            'INSERT OR IGNORE INTO indicators (issue_id, name, source, unit) VALUES (?, ?, ?, ?)',
            (healthcare_access_id, 'Healthcare access index', 'WHO', '0-100 scale')
        )
        db.execute(
            'INSERT OR IGNORE INTO indicators (issue_id, name, source, unit) VALUES (?, ?, ?, ?)',
            (pharma_pricing_id, 'Medicine affordability', 'WHO', '% of income')
        )
        db.commit()
    
    print('  Seeded Healthcare lens structure.')


# Seed the forces layer with pre-approved systemic mechanisms
def seed_forces_layer(db, system_user_id, use_postgresql):
    
    print('Seeding Forces layer...')
    
    issues = {}
    issue_slugs = [
        'ultra-processed-food', 'urban-housing-inadequacy', 'road-traffic-mortality',
        'energy-poverty', 'fossil-fuel-dependency', 'healthcare-access', 'pharmaceutical-pricing'
    ]
    
    if use_postgresql:
        cursor = db.conn.cursor()
        for slug in issue_slugs:
            cursor.execute("SELECT id FROM issues WHERE slug = %s", (slug,))
            issue = cursor.fetchone()
            if issue:
                issues[slug] = issue[0]
        cursor.close()
    else:
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
            'strategic_implication': 'This extraction model destabilizes local healthcare infrastructure, leading to reduced service quality and higher costs for patients, ultimately treating public health needs as financial assets to be stripped.',
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
            'strategic_implication': 'This race to the bottom degrades global ecosystems and exploits vulnerable labor pools, effectively privatizing profits while socializing the catastrophic costs of environmental cleanup and public health crises.',
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
            'strategic_implication': 'This practice artificially extends monopolies on life-saving medications, systematically blocking affordable generic alternatives and prioritizing shareholder returns over global patient survival.',
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
            'strategic_implication': 'These artificial price distortions create an insurmountable barrier to entry for renewable energy, effectively locking global infrastructure into a carbon-intensive trajectory for decades.',
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
        if use_postgresql:
            cursor = db.conn.cursor()
            cursor.execute(
                "INSERT INTO forces (slug, title, category, mechanism, strategic_implication, evidence_chain, created_at) VALUES (%s, %s, %s, %s, %s, %s, NOW()) ON CONFLICT (slug) DO NOTHING",
                (
                    force_data['slug'],
                    force_data['title'],
                    force_data['category'],
                    force_data['mechanism'],
                    force_data['strategic_implication'],
                    json.dumps(force_data['evidence_chain'])
                )
            )
            db.conn.commit()
            cursor.execute("SELECT id FROM forces WHERE slug = %s", (force_data['slug'],))
            force = cursor.fetchone()
            if force:
                force_id = force[0]
                
                for issue_slug in force_data['linked_issues']:
                    if issue_slug in issues:
                        cursor.execute(
                            "INSERT INTO force_issue_links (force_id, issue_id, explanation) VALUES (%s, %s, %s) ON CONFLICT (force_id, issue_id) DO NOTHING",
                            (force_id, issues[issue_slug], force_data['mechanism'])
                        )
                
                inserted_forces += 1
            db.conn.commit()
            cursor.close()
        else:
            db.execute(
                'INSERT OR IGNORE INTO forces (slug, title, category, mechanism, strategic_implication, evidence_chain, created_at) VALUES (?, ?, ?, ?, ?, ?, datetime(\'now\'))',
                (
                    force_data['slug'],
                    force_data['title'],
                    force_data['category'],
                    force_data['mechanism'],
                    force_data['strategic_implication'],
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
    
    if not use_postgresql:
        db.commit()
    print(f'  {inserted_forces} forces inserted with cross-lens links')


# Run all seed functions
def seed_all(db, use_postgresql):
    system_user_id = create_system_user(db, use_postgresql)
    
    seed_food_lens(db, system_user_id, use_postgresql)
    seed_housing_lens(db, system_user_id, use_postgresql)
    seed_mobility_lens(db, system_user_id, use_postgresql)
    seed_energy_lens(db, system_user_id, use_postgresql)
    seed_healthcare_lens(db, system_user_id, use_postgresql)
    seed_forces_layer(db, system_user_id, use_postgresql)
    
    print('\n✅ Seeding complete!')
    print('   - 5 lenses seeded with issues and indicators')
    print('   - 4 forces seeded with evidence chains and cross-lens links')
    print('   - Ready for community contributions!')


if __name__ == '__main__':
    DATABASE_URL = os.environ.get('DATABASE_URL')
    
    if DATABASE_URL:
        print('Using PostgreSQL database...')
        use_postgresql = True
        db = psycopg2.connect(DATABASE_URL)
        db.cursor_factory = psycopg2.extras.RealDictCursor
        
        class DBWrapper:
            def __init__(self, conn):
                self.conn = conn
            def execute(self, query, params=None):
                cursor = self.conn.cursor()
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                return cursor
            def commit(self):
                self.conn.commit()
            def close(self):
                self.conn.close()
        
        db_wrapper = DBWrapper(db)
    else:
        print('Using SQLite database...')
        use_postgresql = False
        db_wrapper = sqlite3.connect('conviction.db')
        db_wrapper.row_factory = sqlite3.Row
    
    seed_all(db_wrapper, use_postgresql)
    db_wrapper.close()