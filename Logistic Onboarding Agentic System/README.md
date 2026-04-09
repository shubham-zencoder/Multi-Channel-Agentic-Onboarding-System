
# 🚚 Logistics Onboarding Agentic System

Multi-agent system for automating logistics partner onboarding. Processes leads from CSV, extracts intent from WhatsApp/Email/Voice, scores leads, and generates personalized responses—all stored in SQLite.

---

## ⚡ Quick Start

**Setup:**
```bash
pip install -r requirements.txt
sqlite3 leads.db < database/schema.sql
```

**Run:**
```bash
python main.py
```

---

## 🛠️ Architecture

6-stage agent pipeline:

```
CSV → Ingestion → Channel → Reconciliation → Qualification → Response → Sync → DB
```

| Agent | Role |
|-------|------|
| **Ingestion** | Load leads from CSV |
| **Channel** | Extract intent from messages |
| **Reconciliation** | Match to existing leads |
| **Qualification** | Score lead (0-100) |
| **Response** | Generate personalized msg |
| **Sync** | Save to database |

---

## 📊 Database Schema

**Table: `leads`**
```sql
CREATE TABLE leads (
    lead_id, name, phone, email, city, vehicle_type, vehicle_count,
    aadhaar_status, bank_status, rc_status, app_installed,
    preferred_channel, onboarding_stage, lead_score,
    latest_update_source, missing_fields, next_best_action,
    remarks, last_updated, whatsapp_draft, email_draft
);
```

**Table: `channel_history`**
```sql
CREATE TABLE channel_history (
    id, lead_id, channel, raw_input,
    extracted_info, action_taken, timestamp
);
```

---

## 📥 Sample Data

**CSV Input** (`leads.csv`):
- 10 leads with name, phone, email, vehicle info, document status

**Email Input** (`sample_email.txt`):
```
From: ishani@email.com
"My Aadhaar status is now verified. I will update my vehicle count to 2 mini trucks."
```

**WhatsApp Input** (`sample_whatsapp.txt`):
```
Hi, I'm Aarav (9876543210). I've uploaded my bank details.
Please mark as verified.
```

**Voice Transcript** (`sample_transcript.txt`):
```
Call: Rahul Verma (9988776655) confirmed 5 trucks. All docs verified. Ready to onboard.
```

**System Output**:
```json
{
  "lead_id": "L001",
  "lead_score": 75,
  "onboarding_stage": "Documents Pending",
  "missing_fields": ["rc_status"],
  "next_best_action": "Request RC document",
  "whatsapp_draft": "Thanks! Bank verified. Just need your RC now.",
  "email_draft": "Your bank is verified. Upload RC to complete onboarding."
}
```

---

## 📁 Project Structure

```
agents/
  ├── ingestion_agent.py
  ├── channel_agent.py
  ├── reconciliation_agent.py
  ├── qualification_agent.py
  ├── response_agent.py
  └── sync_agent.py
database/
  └── schema.sql
samples/
  ├── leads.csv
  ├── sample_email.txt
  ├── sample_whatsapp.txt
  └── sample_transcript.txt
main.py
app.py
config.py
requirements.txt
```

---

## 🐛 Troubleshooting

| Issue | Fix |
|-------|-----|
| Database not found | `sqlite3 leads.db < database/schema.sql` |
| CSV not found | Check path in `ingestion_agent.py` |
| Import errors | `pip install -r requirements.txt` |

## ⚙️ Configuration

Optional environment variables:

- `DB_PATH` (default: `leads.db`)
- `SCHEMA_PATH` (default: `database/schema.sql`)
- `LEADS_CSV_PATH` (default: `samples/leads.csv`)
- `FLASK_SECRET_KEY` (default fallback exists for local dev)