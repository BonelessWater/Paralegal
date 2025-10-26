-- ============================================================================
-- CLIENT COMMUNICATIONS SCHEMA
-- Stores call recordings, transcripts, SMS messages, and emails
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS client_comms;

-- ============================================================================
-- CALL RECORDINGS & TRANSCRIPTS
-- ============================================================================

-- Table for storing call recordings metadata
CREATE TABLE IF NOT EXISTS client_comms.call_recordings (
    id SERIAL PRIMARY KEY,
    call_id VARCHAR(255) UNIQUE NOT NULL,
    client_id VARCHAR(255),  -- Links to client management system
    case_id VARCHAR(255),    -- Links to case in legal_data
    phone_number VARCHAR(50),
    call_direction VARCHAR(20), -- 'inbound', 'outbound'
    call_duration_seconds INTEGER,
    call_date TIMESTAMP NOT NULL,
    recording_file_path TEXT,
    recording_url TEXT,
    storage_location VARCHAR(100), -- 's3', 'local', 'azure', etc.
    file_size_bytes BIGINT,
    audio_format VARCHAR(20), -- 'mp3', 'm4a', 'wav', etc.
    call_status VARCHAR(50), -- 'completed', 'missed', 'voicemail'
    caller_name VARCHAR(255),
    agent_name VARCHAR(255), -- Law firm employee who handled call
    department VARCHAR(100), -- 'intake', 'case_management', 'billing', etc.
    priority VARCHAR(20), -- 'low', 'medium', 'high', 'urgent'
    tags TEXT[], -- Array of tags: ['new_client', 'settlement_discussion', etc.]
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB -- Additional flexible metadata
);

-- Table for storing call transcripts
CREATE TABLE IF NOT EXISTS client_comms.call_transcripts (
    id SERIAL PRIMARY KEY,
    call_id VARCHAR(255) REFERENCES client_comms.call_recordings(call_id) ON DELETE CASCADE,
    transcript_text TEXT NOT NULL,
    transcription_service VARCHAR(50), -- 'whisper', 'openai', 'aws', 'google', etc.
    transcription_model VARCHAR(100), -- 'whisper-large-v3', 'gpt-4-audio', etc.
    confidence_score DECIMAL(3,2), -- 0.00 to 1.00
    language VARCHAR(10), -- 'en', 'es', etc.
    speaker_diarization BOOLEAN DEFAULT FALSE, -- True if speakers were identified
    num_speakers INTEGER,
    processing_time_seconds DECIMAL(8,2),
    transcript_segments JSONB, -- Detailed segments with timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(call_id, transcription_service)
);

-- Table for speaker segments (if diarization is used)
CREATE TABLE IF NOT EXISTS client_comms.transcript_speakers (
    id SERIAL PRIMARY KEY,
    transcript_id INTEGER REFERENCES client_comms.call_transcripts(id) ON DELETE CASCADE,
    speaker_label VARCHAR(50), -- 'Speaker 1', 'Speaker 2', 'Client', 'Agent'
    speaker_role VARCHAR(50), -- 'client', 'attorney', 'paralegal', 'receptionist'
    start_time DECIMAL(10,2), -- Seconds from start
    end_time DECIMAL(10,2),
    text TEXT NOT NULL,
    confidence DECIMAL(3,2)
);

-- ============================================================================
-- SMS/TEXT MESSAGES
-- ============================================================================

-- Table for storing SMS/text messages
CREATE TABLE IF NOT EXISTS client_comms.sms_messages (
    id SERIAL PRIMARY KEY,
    message_id VARCHAR(255) UNIQUE NOT NULL,
    client_id VARCHAR(255),
    case_id VARCHAR(255),
    from_phone VARCHAR(50) NOT NULL,
    to_phone VARCHAR(50) NOT NULL,
    message_direction VARCHAR(20), -- 'inbound', 'outbound'
    message_text TEXT NOT NULL,
    message_date TIMESTAMP NOT NULL,
    sender_name VARCHAR(255),
    recipient_name VARCHAR(255),
    message_status VARCHAR(50), -- 'sent', 'delivered', 'read', 'failed'
    delivery_timestamp TIMESTAMP,
    read_timestamp TIMESTAMP,
    platform VARCHAR(50), -- 'twilio', 'vonage', 'native', etc.
    has_media BOOLEAN DEFAULT FALSE,
    media_urls TEXT[], -- Array of media file URLs
    priority VARCHAR(20),
    tags TEXT[],
    sentiment_score DECIMAL(3,2), -- -1.00 to 1.00 (negative to positive)
    sentiment_label VARCHAR(20), -- 'positive', 'neutral', 'negative', 'urgent'
    automated_response BOOLEAN DEFAULT FALSE,
    thread_id VARCHAR(255), -- Groups related messages
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- ============================================================================
-- EMAILS
-- ============================================================================

-- Table for storing emails
CREATE TABLE IF NOT EXISTS client_comms.emails (
    id SERIAL PRIMARY KEY,
    email_id VARCHAR(255) UNIQUE NOT NULL,
    client_id VARCHAR(255),
    case_id VARCHAR(255),
    from_email VARCHAR(255) NOT NULL,
    to_emails TEXT[] NOT NULL, -- Array of recipient emails
    cc_emails TEXT[],
    bcc_emails TEXT[],
    subject TEXT,
    body_text TEXT,
    body_html TEXT,
    email_direction VARCHAR(20), -- 'inbound', 'outbound'
    email_date TIMESTAMP NOT NULL,
    sender_name VARCHAR(255),
    has_attachments BOOLEAN DEFAULT FALSE,
    attachment_count INTEGER DEFAULT 0,
    email_status VARCHAR(50), -- 'sent', 'delivered', 'bounced', 'opened'
    priority VARCHAR(20),
    tags TEXT[],
    sentiment_score DECIMAL(3,2),
    sentiment_label VARCHAR(20),
    category VARCHAR(100), -- 'new_inquiry', 'case_update', 'billing', 'general'
    automated_response BOOLEAN DEFAULT FALSE,
    thread_id VARCHAR(255),
    in_reply_to VARCHAR(255), -- Email ID of parent message
    spam_score DECIMAL(3,2), -- 0.00 to 1.00
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- Table for email attachments
CREATE TABLE IF NOT EXISTS client_comms.email_attachments (
    id SERIAL PRIMARY KEY,
    email_id VARCHAR(255) REFERENCES client_comms.emails(email_id) ON DELETE CASCADE,
    attachment_name VARCHAR(500) NOT NULL,
    file_path TEXT,
    file_url TEXT,
    file_size_bytes BIGINT,
    mime_type VARCHAR(100),
    is_inline BOOLEAN DEFAULT FALSE,
    content_id VARCHAR(255), -- For inline images
    extracted_text TEXT, -- OCR/text extraction from PDFs/images
    document_type VARCHAR(100), -- Classification: 'medical_record', 'police_report', etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- AI ANALYSIS & INSIGHTS
-- ============================================================================

-- Table for storing AI analysis of communications
CREATE TABLE IF NOT EXISTS client_comms.ai_analysis (
    id SERIAL PRIMARY KEY,
    communication_type VARCHAR(20) NOT NULL, -- 'call', 'sms', 'email'
    communication_id VARCHAR(255) NOT NULL, -- ID from respective table
    analysis_type VARCHAR(50) NOT NULL, -- 'summary', 'sentiment', 'action_items', 'classification'
    analysis_result JSONB NOT NULL,
    confidence_score DECIMAL(3,2),
    model_used VARCHAR(100), -- 'gpt-4', 'claude-3', 'llama-70b', etc.
    processing_time_seconds DECIMAL(8,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100) -- 'system', 'user_id', etc.
);

-- Table for extracted action items from communications
CREATE TABLE IF NOT EXISTS client_comms.action_items (
    id SERIAL PRIMARY KEY,
    communication_type VARCHAR(20) NOT NULL,
    communication_id VARCHAR(255) NOT NULL,
    action_description TEXT NOT NULL,
    assigned_to VARCHAR(255), -- Attorney/staff member
    due_date DATE,
    priority VARCHAR(20),
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'in_progress', 'completed', 'cancelled'
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100)
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Call recordings indexes
CREATE INDEX IF NOT EXISTS idx_calls_client ON client_comms.call_recordings(client_id);
CREATE INDEX IF NOT EXISTS idx_calls_case ON client_comms.call_recordings(case_id);
CREATE INDEX IF NOT EXISTS idx_calls_date ON client_comms.call_recordings(call_date);
CREATE INDEX IF NOT EXISTS idx_calls_status ON client_comms.call_recordings(call_status);
CREATE INDEX IF NOT EXISTS idx_calls_agent ON client_comms.call_recordings(agent_name);

-- Transcript indexes
CREATE INDEX IF NOT EXISTS idx_transcripts_call ON client_comms.call_transcripts(call_id);
CREATE INDEX IF NOT EXISTS idx_transcript_text ON client_comms.call_transcripts USING gin(to_tsvector('english', transcript_text));

-- SMS indexes
CREATE INDEX IF NOT EXISTS idx_sms_client ON client_comms.sms_messages(client_id);
CREATE INDEX IF NOT EXISTS idx_sms_case ON client_comms.sms_messages(case_id);
CREATE INDEX IF NOT EXISTS idx_sms_date ON client_comms.sms_messages(message_date);
CREATE INDEX IF NOT EXISTS idx_sms_thread ON client_comms.sms_messages(thread_id);
CREATE INDEX IF NOT EXISTS idx_sms_text ON client_comms.sms_messages USING gin(to_tsvector('english', message_text));

-- Email indexes
CREATE INDEX IF NOT EXISTS idx_emails_client ON client_comms.emails(client_id);
CREATE INDEX IF NOT EXISTS idx_emails_case ON client_comms.emails(case_id);
CREATE INDEX IF NOT EXISTS idx_emails_date ON client_comms.emails(email_date);
CREATE INDEX IF NOT EXISTS idx_emails_thread ON client_comms.emails(thread_id);
CREATE INDEX IF NOT EXISTS idx_emails_category ON client_comms.emails(category);
CREATE INDEX IF NOT EXISTS idx_emails_subject ON client_comms.emails USING gin(to_tsvector('english', subject));
CREATE INDEX IF NOT EXISTS idx_emails_body ON client_comms.emails USING gin(to_tsvector('english', body_text));

-- AI analysis indexes
CREATE INDEX IF NOT EXISTS idx_analysis_comm_type ON client_comms.ai_analysis(communication_type, communication_id);
CREATE INDEX IF NOT EXISTS idx_analysis_type ON client_comms.ai_analysis(analysis_type);

-- Action items indexes
CREATE INDEX IF NOT EXISTS idx_actions_comm ON client_comms.action_items(communication_type, communication_id);
CREATE INDEX IF NOT EXISTS idx_actions_assigned ON client_comms.action_items(assigned_to);
CREATE INDEX IF NOT EXISTS idx_actions_status ON client_comms.action_items(status);
CREATE INDEX IF NOT EXISTS idx_actions_due ON client_comms.action_items(due_date);

-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

-- View: All client communications in chronological order
CREATE OR REPLACE VIEW client_comms.all_communications AS
SELECT 
    'call' as type,
    call_id as id,
    client_id,
    case_id,
    call_date as date,
    caller_name as from_name,
    agent_name as to_name,
    NULL as subject,
    COALESCE(ct.transcript_text, 'No transcript') as content,
    cr.call_status as status,
    cr.priority,
    cr.tags
FROM client_comms.call_recordings cr
LEFT JOIN client_comms.call_transcripts ct ON cr.call_id = ct.call_id

UNION ALL

SELECT 
    'sms' as type,
    message_id as id,
    client_id,
    case_id,
    message_date as date,
    sender_name as from_name,
    recipient_name as to_name,
    NULL as subject,
    message_text as content,
    message_status as status,
    priority,
    tags
FROM client_comms.sms_messages

UNION ALL

SELECT 
    'email' as type,
    email_id as id,
    client_id,
    case_id,
    email_date as date,
    sender_name as from_name,
    array_to_string(to_emails, ', ') as to_name,
    subject,
    body_text as content,
    email_status as status,
    priority,
    tags
FROM client_comms.emails

ORDER BY date DESC;

-- View: Communication summary by case
CREATE OR REPLACE VIEW client_comms.case_communication_summary AS
SELECT 
    case_id,
    COUNT(*) FILTER (WHERE type = 'call') as total_calls,
    COUNT(*) FILTER (WHERE type = 'sms') as total_sms,
    COUNT(*) FILTER (WHERE type = 'email') as total_emails,
    COUNT(*) as total_communications,
    MAX(date) as last_communication_date,
    MIN(date) as first_communication_date
FROM client_comms.all_communications
WHERE case_id IS NOT NULL
GROUP BY case_id;

-- ============================================================================
-- GRANT PERMISSIONS
-- ============================================================================

GRANT USAGE ON SCHEMA client_comms TO paralegal_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA client_comms TO paralegal_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA client_comms TO paralegal_user;

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON SCHEMA client_comms IS 'Schema for storing all client communications: calls, SMS, and emails';
COMMENT ON TABLE client_comms.call_recordings IS 'Metadata for call recordings including file paths and call details';
COMMENT ON TABLE client_comms.call_transcripts IS 'AI-generated transcripts of call recordings';
COMMENT ON TABLE client_comms.sms_messages IS 'SMS/text messages sent and received';
COMMENT ON TABLE client_comms.emails IS 'Email communications with clients';
COMMENT ON TABLE client_comms.ai_analysis IS 'AI-powered analysis of communications (summaries, sentiment, classification)';
COMMENT ON TABLE client_comms.action_items IS 'Action items extracted from communications by AI';
