import json

def get_sunburst_data(db):
    """
    Hierarchical structure:
    Systemic Conviction → Category → Force → Lens → Issue → Country
    """
    rows = db.execute('''
        SELECT 
            COALESCE(f.category, 'Uncategorized') as category,
            f.id as force_id,
            f.title as force_title,
            COALESCE(l.title, 'Unlinked') as lens_title,
            COALESCE(i.title, 'Unlinked') as issue_title,
            COALESCE(c.country_code, 'Unknown') as country_name,
            COALESCE(SUM(ABS(tt.amount)), 0) as total_spend
        FROM forces f
        LEFT JOIN force_issue_links fil ON f.id = fil.force_id
        LEFT JOIN issues i ON fil.issue_id = i.id
        LEFT JOIN lenses l ON i.lens_id = l.id
        LEFT JOIN contribution_lens_links cll ON cll.issue_id = i.id
        LEFT JOIN contributions c ON c.id = cll.contribution_id
        LEFT JOIN token_transactions tt ON c.id = tt.contribution_id AND tt.reason = 'spend'
        GROUP BY f.category, f.title, l.title, i.title, c.country_code
        ORDER BY total_spend DESC
    ''').fetchall()

    # Direct force-level spend (from /spend-force), separate from evidence-level spend above
    force_spend_rows = db.execute('''
        SELECT force_id, COALESCE(SUM(ABS(amount)), 0) as direct_spend
        FROM token_transactions
        WHERE reason = 'spend' AND force_id IS NOT NULL
        GROUP BY force_id
    ''').fetchall()
    direct_force_spend = {r['force_id']: r['direct_spend'] for r in force_spend_rows}

    sunburst_data = {
        "name": "Mechanisms",
        "children": []
    }

    categories_map = {}

    for row in rows:
        category = row['category']
        force_id = row['force_id']
        force_name = row['force_title']
        lens_name = row['lens_title']
        issue_name = row['issue_title']
        country_name = row['country_name']
        spend = row['total_spend']

        # Layer 1: Category
        if category not in categories_map:
            categories_map[category] = {
                "name": category,
                "children": [],
                "forces_map": {}
            }
            sunburst_data["children"].append(categories_map[category])

        cat_data = categories_map[category]

        # Layer 2: Force
        if force_name not in cat_data["forces_map"]:
            force_data = {
                "name": force_name,
                "value": direct_force_spend.get(force_id, 0), # direct endorsement, separate from evidence-chain spend
                "children": [],
                "lenses_map": {}
            }
            cat_data["children"].append(force_data)
            cat_data["forces_map"][force_name] = force_data

        force_data = cat_data["forces_map"][force_name]

        # Layer 3: Lens
        if lens_name not in force_data["lenses_map"]:
            lens_data = {
                "name": lens_name,
                "children": [],
                "issues_map": {}
            }
            force_data["children"].append(lens_data)
            force_data["lenses_map"][lens_name] = lens_data

        lens_data = force_data["lenses_map"][lens_name]

        # Layer 4: Issue
        if issue_name not in lens_data["issues_map"]:
            issue_data = {
                "name": issue_name,
                "children": [],
                "countries_map": {}
            }
            lens_data["children"].append(issue_data)
            lens_data["issues_map"][issue_name] = issue_data

        issue_data = lens_data["issues_map"][issue_name]

        # Layer 5: Country
        if country_name not in issue_data["countries_map"]:
            country_data = {"name": country_name, "value": 0}
            issue_data["children"].append(country_data)
            issue_data["countries_map"][country_name] = country_data

        issue_data["countries_map"][country_name]["value"] += spend

    # Clean up temporary mapping dictionaries before returning JSON
    def cleanup(obj):
        for key in ["forces_map", "lenses_map", "issues_map", "countries_map"]:
            if key in obj:
                del obj[key]
        for child in obj.get("children", []):
            cleanup(child)

    for cat in sunburst_data["children"]:
        cleanup(cat)

    return json.dumps(sunburst_data)