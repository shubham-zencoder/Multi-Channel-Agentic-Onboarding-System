# sync_agent.py
import sqlite3
import os
import sys
from datetime import datetime
import json

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from config import DB_PATH

def sync_to_db(lead_id, qualification, response):
    """
    Updates the database with the final intelligence from Qualification 
    and Response agents, maintaining the Single Source of Truth.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # 1. Update main 'leads' table
        # We use 'next_best_action' to match your updated Qualification Agent
        cursor.execute("""
            UPDATE leads
            SET 
                lead_score = ?,
                onboarding_stage = ?,
                next_best_action = ?,
                missing_fields = ?,
                whatsapp_draft = ?,
                email_draft = ?,
                last_updated = ?
            WHERE lead_id = ?
        """, (
            qualification.get("lead_score", 0),
            qualification.get("onboarding_stage", "in_progress"),
            qualification.get("next_best_action", "follow_up"), # Fixes KeyError
            ", ".join(qualification.get("missing_fields", [])),
            response.get("whatsapp_draft", ""),
            response.get("email_draft", ""),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            lead_id
        ))

        # 2. Update 'channel_history' [Requirement: Step 6 Multi-Channel Sync]
        # This records that the system generated a response
        cursor.execute("""
            INSERT INTO channel_history (
                lead_id, channel, raw_input,
                extracted_info, action_taken, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            lead_id,
            "system",
            "automated_qualification",
            json.dumps(qualification), # Store full intelligence as JSON
            "response_generated",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))

        conn.commit()
        conn.close()

        print(f"[SYNC] Sync completed for Lead {lead_id}: Database updated with score and drafts.")

    except Exception as e:
        print(f"[ERROR] Sync Error for Lead {lead_id}: {e}")