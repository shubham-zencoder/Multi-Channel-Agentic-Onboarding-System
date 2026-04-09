from agents.ingestion_agent import ingest_leads
from agents.channel_agent import extract_info
from agents.reconciliation_agent import reconcile_lead
from agents.qualification_agent import qualify_and_sync_lead
from agents.response_agent import generate_and_sync_response
from agents.sync_agent import sync_to_db
from database.db_init import initialize_db
from config import LEADS_CSV_PATH

def run_pipeline():
    # Step 0: Initialize DB
    initialize_db()

    # Step 1: Ingest leads
    ingest_leads(LEADS_CSV_PATH)


def process_new_communication(channel, raw_text, contact_info):
    """
    The central workflow orchestrator[cite: 20].
    """
    print(f"\n--- Processing {channel} message ---")

    # Step 2: Extract Intent [cite: 24, 26]
    extracted = extract_info(raw_text)

    # Step 3: Reconcile with DB [cite: 27, 28]
    # We use contact_info (phone/email) to find the Lead ID in the DB
    current_state = reconcile_lead(contact_info, extracted, channel, raw_text)
    
    if not current_state:
        print(f"Lead not found for {contact_info}. Ignoring.")
        return

    # Step 4: Qualify Lead [cite: 29, 30]
    qual_results = qualify_and_sync_lead(current_state['lead_id'])

    # Step 5: Generate Responses [cite: 31, 32]
    responses = generate_and_sync_response(current_state['lead_id'], qual_results)

    # Step 6: Sync Everything [cite: 33, 35]
    sync_to_db(current_state['lead_id'], qual_results, responses)

    # Print Mandatory Output for the console/logs [cite: 36]
    print(f"Lead Score: {qual_results['lead_score']}/100")
    print(f"Next Best Action: {qual_results['next_best_action']}")

if __name__ == "__main__":
    # 1. First, initialize and ingest 
    run_pipeline()

    # 2. Simulate multi-channel updates 
    process_new_communication("whatsapp", "My bank is verified", "9876543210")
    process_new_communication("email", "I have 3 mini trucks", "ishani@email.com")
