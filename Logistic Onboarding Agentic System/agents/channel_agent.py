import re
import sqlite3
import json
import os
import sys
from datetime import datetime

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from config import DB_PATH

# --- Logic for extracting info (kept from your original) ---
def normalize_text(text):
    return text.lower().strip()

def extract_info(text):
    text = normalize_text(text)
    data = {}
    
    # Extracting Statuses
    for doc in ['aadhaar', 'bank', 'rc']:
        if doc in text:
            if 'verified' in text or 'upload' in text or 'done' in text:
                data[f'{doc}_status'] = 'verified'
            elif 'pending' in text or 'later' in text:
                data[f'{doc}_status'] = 'pending'

    # Extracting Vehicle Info
    if "truck" in text: data["vehicle_type"] = "truck"
    elif "mini" in text: data["vehicle_type"] = "mini"

    v_count = re.search(r'(\d+)\s*(truck|mini|vehicle)', text)
    if v_count:
        data["vehicle_count"] = int(v_count.group(1))

    # Determining Intent (Requirement: extract structured intent)
    if any(word in text for word in ["ready", "activate", "start"]):
        data["intent"] = "ready_to_onboard"
    elif "not interested" in text or "stop" in text:
        data["intent"] = "drop"
    else:
        data["intent"] = "partial_update"

    return data

# --- NEW: Helper to find Lead ID in DB ---
def find_lead_id(text):
    """Searches text for phone or email to find lead_id in DB."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Look for 10-digit phone or email pattern
    email_match = re.search(r'[\w\.-]+@[\w\.-]+', text)
    phone_match = re.search(r'\d{10}', text)
    
    lead_id = "UNKNOWN"
    if email_match:
        cursor.execute("SELECT lead_id FROM leads WHERE email=?", (email_match.group(0).lower(),))
    elif phone_match:
        cursor.execute("SELECT lead_id FROM leads WHERE phone LIKE ?", (f"%{phone_match.group(0)}",))
    
    row = cursor.fetchone()
    if row:
        lead_id = row[0]
    
    conn.close()
    return lead_id

# --- NEW: Logging to Channel History (Sync Agent Requirement) ---
def log_to_history(lead_id, channel, raw_text, extracted_data):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO channel_history (lead_id, channel, raw_input, extracted_info, timestamp)
        VALUES (?, ?, ?, ?, ?)
    ''', (lead_id, channel, raw_text, json.dumps(extracted_data), datetime.now()))
    conn.commit()
    conn.close()

# --- Process Channel Pipeline ---
def process_channel(file_path, channel_name):
    # (Your existing logic to read files)
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            samples = f.read().strip().split("\n\n")
    except FileNotFoundError:
        print(f"[WARN] File not found: {file_path}")
        return []

    results = []
    for text in samples:
        # 1. Channel Understanding Agent: Extract intent and data
        extracted = extract_info(text)
        
        # 2. Identify the lead
        l_id = find_lead_id(text)
        
        # 3. Build Result Object
        result = {
            "lead_id": l_id,
            "channel": channel_name,
            "raw_text": text.strip(),
            "extracted_data": extracted
        }
        
        # 4. Sync Agent: Log the history
        log_to_history(l_id, channel_name, text.strip(), extracted)
        
        results.append(result)
        print(f"[OK] Processed {channel_name} for Lead: {l_id}")

    return results

def run_all_channels():
    # Update these paths to your actual local paths
    paths = {
        "transcript": "samples/sample_transcript.txt",
        "whatsapp": "samples/sample_whatsapp.txt",
        "email": "samples/sample_email.txt"
    }
    
    all_results = []
    for channel, path in paths.items():
        all_results += process_channel(path, channel)
    
    return all_results

if __name__ == "__main__":
    run_all_channels()