import sqlite3
import json
import os
import sys
from datetime import datetime

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from config import DB_PATH

def reconcile_lead(identifier, new_data, channel, raw_text):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Row lookup (Search by Phone, Email, or Lead ID)
    cursor.execute("""
        SELECT * FROM leads 
        WHERE phone = ? OR email = ? OR lead_id = ?
    """, (identifier, identifier, identifier))
    
    row = cursor.fetchone()

    if not row:
        print(f"[NOT_FOUND] Lead '{identifier}' not found.")
        conn.close()
        return None

    columns = [desc[0] for desc in cursor.description]
    existing_record = dict(zip(columns, row))
    lead_id = existing_record['lead_id']

    # 2. Update logic with "Source Tracking" [Requirement: Step 3 & 6]
    updated_values = {}
    for key, value in new_data.items():
        # Only update if the field exists in your schema and is not empty
        if key in existing_record and value not in [None, "", "missing"]:
            updated_values[key] = value

    # Mandatory Meta-data updates
    updated_values["latest_update_source"] = channel # 
    updated_values["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 3. Dynamic SQL Update
    if updated_values:
        placeholders = ", ".join([f"{k} = ?" for k in updated_values.keys()])
        params = list(updated_values.values()) + [lead_id]
        cursor.execute(f"UPDATE leads SET {placeholders} WHERE lead_id = ?", params)

    # 4. Mandatory Output: Identify Remaining Missing Fields 
    # We re-fetch or check current state to see what is still NULL/missing
    cursor.execute("SELECT * FROM leads WHERE lead_id = ?", (lead_id,))
    current_state = dict(zip(columns, cursor.fetchone()))
    
    mandatory_fields = ['aadhaar_status', 'bank_status', 'rc_status', 'vehicle_type']
    missing = [f for f in mandatory_fields if current_state.get(f) in [None, 'missing', 'pending']]
    
    # Update missing_fields column for the Qualification Agent
    cursor.execute("UPDATE leads SET missing_fields = ? WHERE lead_id = ?", 
                   (", ".join(missing), lead_id))

    # 5. Sync Agent: History Logging [cite: 33, 35]
    cursor.execute("""
        INSERT INTO channel_history (
            lead_id, channel, raw_input, extracted_info, timestamp
        ) VALUES (?, ?, ?, ?, ?)
    """, (lead_id, channel, raw_text, json.dumps(new_data), updated_values["last_updated"]))

    conn.commit()
    conn.close()
    
    print(f"[RECONCILE] Reconciliation complete for {lead_id}. Source: {channel}")
    return current_state
