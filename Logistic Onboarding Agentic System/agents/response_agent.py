import sqlite3
import os
import sys

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from config import DB_PATH

def generate_whatsapp(data):
    stage = data.get("onboarding_stage")
    missing = data.get("missing_fields", "")
    
    if stage == "ready_for_activation":
        return "Great news! Your profile is complete. We will activate your account shortly."
    elif "aadhaar" in missing or "bank" in missing or "rc" in missing:
        return f"Hi! We need your {missing} to finish onboarding. Can you share them here?"
    elif "vehicle" in missing:
        return "Hi! Please share your vehicle details so we can proceed with onboarding."
    else:
        return "Hi! Just checking in. Let us know if you need any help with onboarding."

def generate_email(data):
    stage = data.get("onboarding_stage")
    missing = data.get("missing_fields", "")
    
    subject = "Update on your Onboarding"
    if stage == "ready_for_activation":
        subject = "Onboarding Complete!"
        body = "Your onboarding process is complete. We will activate your account shortly."
    else:
        body = f"We noticed some fields are still pending: {missing}. Please provide these to proceed."

    return f"Subject: {subject}\n\nDear Customer,\n\n{body}\n\nBest regards,\nTeam"

def generate_and_sync_response(lead_id, qualification_results):
    """
    Generates all mandatory communication drafts and updates the 
    database to maintain the single source of truth.
    """
    # 1. Generate Drafts
    whatsapp_draft = generate_whatsapp(qualification_results)
    email_draft = generate_email(qualification_results)
    
    # Callback logic (Requirement: Callback required with reason and priority)
    callback_needed = "Yes" if "ready" not in qualification_results.get("onboarding_stage", "") else "No"
    callback_reason = f"Follow up on missing: {qualification_results.get('missing_fields')}"
    
    # 2. Sync to Database [Requirement: Step 6 Sync Agent]
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE leads 
        SET whatsapp_draft = ?, 
            email_draft = ?, 
            remarks = ?
        WHERE lead_id = ?
    """, (whatsapp_draft, email_draft, f"Callback: {callback_needed} | Reason: {callback_reason}", lead_id))
    
    conn.commit()
    conn.close()
    
    print(f"[MAIL] Communication drafts synced for Lead: {lead_id}")
    
    return {
        "whatsapp_draft": whatsapp_draft,
        "email_draft": email_draft,
        "callback_details": {"required": callback_needed, "reason": callback_reason}
    }

if __name__ == "__main__":
    # Example input from your Qualification Agent
    sample_input = {
        "onboarding_stage": "documentation_phase",
        "missing_fields": "aadhaar_status, bank_status"
    }
    generate_and_sync_response("L001", sample_input)