# background.py
import os
import sqlite3
import psycopg2
import threading
from psycopg2.extras import RealDictCursor
from db import DATABASE, DATABASE_URL, Psycopg2Wrapper, USE_POSTGRESQL
import agent  # Import your existing agent module


#  Run the AI agent in a background thread to process a contribution
# Creates its own database connection (SQLite/Postgres connections cannot be safely shared across threads)
def run_agent_background(contrib_id):
    
    # 1. Create a new database connection for this specific thread
    if os.environ.get('DATABASE_URL'):
        conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
        # Note: psycopg2 connection objects don't have cursor_factory as a direct attribute, 
        # it's passed to the cursor() method or via a custom connection class. 
        # We'll use the wrapper to handle this cleanly.
        bg_db = Psycopg2Wrapper(conn)
    else:
        bg_db = sqlite3.connect(DATABASE)
        bg_db.row_factory = sqlite3.Row
    
    try:
        # 2. Fetch existing lenses to pass to the AI agent
        existing_lenses = bg_db.execute('SELECT title FROM lenses').fetchall()
        
        # 3. Hand off to the AI agent logic
        agent.run_agent(bg_db, contrib_id, existing_lenses)
    except Exception as e:
        print(f"Background agent failed for contribution {contrib_id}: {e}")
    finally:
        # 4. Always close the thread's connection
        bg_db.close()


# Wrapper to start the background thread from a Flask route
def start_agent_thread(contribution_id):
    thread = threading.Thread(target=run_agent_background, args=(contribution_id,))
    thread.start()
    return thread