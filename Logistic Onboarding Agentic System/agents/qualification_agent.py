import sqlite3
import os
import sys

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from config import DB_PATH

def calculate_score(data):
    # data can be a dictionary or a sqlite3.Row object
    score = 0
    # Values based on priority: Docs (80%) + App/Vehicle (20%)
    if data.get("aadhaar_status") == "verified": score += 30
    if data.get("bank_status") == "verified": score += 30
    if data.get("rc_status") == "verified": score += 20
    if data.get("app_installed") in [1, True, "yes"]: score += 10
    if data.get("vehicle_type"): score += 10
    return score

def detect_missing_fields(data):
    missing = []
    # Doc statuses should be verified to be considered complete.
    doc_fields = ["aadhaar_status", "bank_status", "rc_status"]
    for field in doc_fields:
        if data.get(field) != "verified":
            missing.append(field)
    # Vehicle type is complete if present and valid.
    if data.get("vehicle_type") not in ["truck", "mini"]:
        missing.append("vehicle_type")
    return missing

def determine_stage(score, missing):
    # Logic to satisfy 'decide onboarding stage' [cite: 15]
    if score >= 90 and not missing:
        return "ready_for_activation"
    elif any(x in missing for x in ["aadhaar_status", "bank_status", "rc_status"]):
        return "documentation_phase"
    else:
        return "lead_nurturing"

def determine_next_action(stage, missing):
    # Satisfies 'determine the next best action' [cite: 15, 41]
    if stage == "ready_for_activation":
        return "Move to Operations for Final Activation"
    elif "aadhaar_status" in missing:
        return "Request Aadhaar Photo via WhatsApp"
    elif "bank_status" in missing:
        return "Request Passbook/Cheque via Email"
    return "Follow up for pending vehicle details"

def qualify_and_sync_lead(lead_id):
    """
    Fetches lead from DB, calculates scores/stage, and updates the DB
    to maintain the 'single source of truth'[cite: 6].
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 1. Fetch current data
    cursor.execute("SELECT * FROM leads WHERE lead_id = ?", (lead_id,))
    lead = cursor.fetchone()
    
    if not lead:
        conn.close()
        return None

    lead_data = dict(lead)

    # 2. Run Qualification Logic
    score = calculate_score(lead_data)
    missing = detect_missing_fields(lead_data)
    stage = determine_stage(score, missing)
    action = determine_next_action(stage, missing)

    # 3. Update Database [Requirement: Sync Agent Step]
    # This ensures the 'Updated database state' deliverable [cite: 45]
    cursor.execute("""
        UPDATE leads 
        SET lead_score = ?, 
            onboarding_stage = ?, 
            missing_fields = ?, 
            next_best_action = ?
        WHERE lead_id = ?
    """, (score, stage, ", ".join(missing), action, lead_id))

    conn.commit()
    conn.close()

    print(f"[QUALIFY] Qualification Complete for {lead_id}: Score {score}, Stage: {stage}")
    
    return {
        "lead_score": score,
        "onboarding_stage": stage,
        "missing_fields": missing,
        "next_best_action": action
    }

if __name__ == "__main__":
    # Example usage
    qualify_and_sync_lead("L001")