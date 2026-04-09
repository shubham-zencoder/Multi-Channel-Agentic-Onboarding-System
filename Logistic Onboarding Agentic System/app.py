from flask import Flask, render_template, redirect, url_for, flash
import sqlite3
import os
from main import run_pipeline, process_new_communication
from database.db_init import initialize_db
from config import DB_PATH

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "logistic_secret_key")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    initialize_db() # Ensure DB exists
    conn = get_db_connection()
    leads = conn.execute('SELECT * FROM leads ORDER BY last_updated DESC').fetchall()
    
    # Stats
    total = len(leads)
    ready = len([l for l in leads if l['onboarding_stage'] == 'ready_for_activation'])
    docs_pending = len([l for l in leads if l['onboarding_stage'] == 'documentation_phase'])
    
    conn.close()
    return render_template('index.html', leads=leads, stats={
        'total': total,
        'ready': ready,
        'docs_pending': docs_pending
    })

@app.route('/run-pipeline')
def trigger_pipeline():
    try:
        run_pipeline()
        flash("Main pipeline executed successfully!", "success")
    except Exception as e:
        flash(f"Error running pipeline: {e}", "error")
    return redirect(url_for('index'))

@app.route('/simulate-chats')
def simulate_chats():
    try:
        process_new_communication("whatsapp", "My bank is verified", "9876543210")
        process_new_communication("email", "I have 3 mini trucks", "ishani@email.com")
        flash("Chat simulation completed!", "success")
    except Exception as e:
        flash(f"Error simulating chats: {e}", "error")
    return redirect(url_for('index'))

if __name__ == '__main__':
    initialize_db()
    app.run(debug=True, port=5000)
