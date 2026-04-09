import sqlite3
import os
import sys

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from config import DB_PATH, SCHEMA_PATH

def _ensure_columns(conn):
    """
    Lightweight migration for additive columns on existing DBs.
    """
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(leads)")
    existing_columns = {row[1] for row in cursor.fetchall()}
    required_columns = {
        "whatsapp_draft": "TEXT",
        "email_draft": "TEXT",
    }
    for column_name, column_type in required_columns.items():
        if column_name not in existing_columns:
            cursor.execute(f"ALTER TABLE leads ADD COLUMN {column_name} {column_type}")
            print(f"[MIGRATE] Added missing column: leads.{column_name}")

def initialize_db(db_path=DB_PATH, schema_path=SCHEMA_PATH):
    """
    Initializes the database using the schema.sql file.
    """
    if os.path.exists(db_path):
        # We check if the table exists to avoid redundant initialization
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='leads'")
        if cursor.fetchone():
            _ensure_columns(conn)
            conn.commit()
            print(f"[OK] Database already initialized at {db_path}.")
            conn.close()
            return
        conn.close()

    print(f"[INIT] Initializing database at {db_path}...")
    try:
        with open(schema_path, 'r') as f:
            schema = f.read()
        
        conn = sqlite3.connect(db_path)
        conn.executescript(schema)
        conn.commit()
        conn.close()
        print("[OK] Schema applied successfully.")
    except Exception as e:
        print(f"[ERROR] Error initializing database: {e}")

if __name__ == "__main__":
    initialize_db()
