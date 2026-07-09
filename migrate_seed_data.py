import sqlite3
import os

# Adjust path if your db is located elsewhere
DB_PATH = 'conviction.db'

def migrate():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    db = conn.cursor()

    # 1. Create the "Data Archive" user if they don't exist
    db.execute("SELECT id FROM users WHERE username = 'Data Archive'")
    user = db.fetchone()
    
    if not user:
        # We use a dummy password hash since no one will log in as this user
        db.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", 
                   ('Data Archive', 'dummy_hash_for_system_user'))
        system_user_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
    else:
        system_user_id = user['id']

    print(f"Using System User ID: {system_user_id}")

    # 2. Fetch all seed data
    db.execute('''
        SELECT dp.id, dp.country_code, dp.year, dp.value, 
               i.id as issue_id, i.name as indicator_name, i.unit, l.slug as lens_slug
        FROM data_points dp
        JOIN indicators i ON dp.indicator_id = i.id
        JOIN issues iss ON i.issue_id = iss.id
        JOIN lenses l ON iss.lens_id = l.id
    ''')
    data_points = db.fetchall()

    print(f"Migrating {len(data_points)} seed data points...")

    for dp in data_points:
        # Create a standardized note for the card
        note_text = f"Official record: {dp['value']} {dp['unit']} in {dp['country_code']} for {dp['year']}."
        source_url = "https://www.who.int/data" # Generic source for seed data

        # Insert into contributions
        db.execute('''
            INSERT INTO contributions (user_id, contribution_type, country_code, value, note, source_url, status, created_at)
            VALUES (?, 'data_point', ?, ?, ?, ?, 'approved', datetime('now'))
        ''', (system_user_id, dp['country_code'], dp['value'], note_text, source_url))
        
        new_contrib_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]

        # Link to the issue/lens
        db.execute('''
            INSERT INTO contribution_lens_links (contribution_id, issue_id)
            VALUES (?, ?)
        ''', (new_contrib_id, dp['issue_id']))

    # 3. Empty the old data_points table
    db.execute("DELETE FROM data_points")
    
    conn.commit()
    print("Migration complete! Seed data is now in the contributions table.")
    conn.close()

if __name__ == '__main__':
    migrate()