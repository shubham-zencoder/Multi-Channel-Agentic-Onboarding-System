CREATE TABLE leads (
    lead_id TEXT PRIMARY KEY,
    name TEXT,
    phone TEXT,
    email TEXT,
    city TEXT,
    vehicle_type TEXT,
    vehicle_count INTEGER,
    aadhaar_status TEXT DEFAULT 'missing', -- [cite: 18]
    bank_status TEXT DEFAULT 'missing',    -- [cite: 18]
    rc_status TEXT DEFAULT 'missing',      -- [cite: 18]
    app_installed BOOLEAN DEFAULT 0,       -- [cite: 18]
    preferred_channel TEXT,                -- [cite: 18, 39]
    onboarding_stage TEXT,                 -- 
    lead_score INTEGER DEFAULT 0,          -- [cite: 30, 37]
    
    -- Agentic Metadata (Crucial for the "Sync" and "Reconciliation" Agents)
    latest_update_source TEXT,             -- [cite: 40, 61]
    missing_fields TEXT,                   -- 
    next_best_action TEXT,                 -- 
    remarks TEXT,                          -- [cite: 18]
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- 
    whatsapp_draft TEXT,
    email_draft TEXT
);

CREATE TABLE channel_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lead_id TEXT,
    channel TEXT,
    raw_input TEXT,
    extracted_info TEXT,
    action_taken TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
