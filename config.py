import os

# Centralized runtime configuration.
DB_PATH = os.getenv("DB_PATH", "leads.db")
SCHEMA_PATH = os.getenv("SCHEMA_PATH", "database/schema.sql")
LEADS_CSV_PATH = os.getenv("LEADS_CSV_PATH", "samples/leads.csv")
