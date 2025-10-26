-- ============================================================================
-- CLIENT & CASE MANAGEMENT SCHEMA
-- Core business entities: clients, cases, attorneys, case parties
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS case_management;

-- ============================================================================
-- CLIENTS
-- ============================================================================

-- Table for storing client information
CREATE TABLE IF NOT EXISTS case_management.clients (
    id SERIAL PRIMARY KEY,
    client_id VARCHAR(255) UNIQUE NOT NULL, -- External client ID
    first_name VARCHAR(255) NOT NULL,
    last_name VARCHAR(255) NOT NULL,
    middle_name VARCHAR(255),
    preferred_name VARCHAR(255),
    date_of_birth DATE,
    ssn_encrypted VARCHAR(255), -- Encrypted SSN
    email VARCHAR(255),
    phone_primary VARCHAR(50),
    phone_secondary VARCHAR(50),
    phone_mobile VARCHAR(50),
    address_street VARCHAR(500),
    address_city VARCHAR(255),
    address_state VARCHAR(100),
    address_zip VARCHAR(20),
    address_country VARCHAR(100) DEFAULT 'USA',
    emergency_contact_name VARCHAR(255),
    emergency_contact_phone VARCHAR(50),
    emergency_contact_relationship VARCHAR(100),
    preferred_language VARCHAR(50) DEFAULT 'English',
    preferred_contact_method VARCHAR(50), -- 'email', 'phone', 'sms', 'mail'
    client_status VARCHAR(50) DEFAULT 'active', -- 'active', 'inactive', 'potential', 'former'
    client_source VARCHAR(100), -- 'referral', 'advertisement', 'website', 'walk-in'
    referral_source VARCHAR(255), -- Who referred them
    intake_date DATE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    metadata JSONB -- Flexible additional data
);

-- ============================================================================
-- CASES
-- ============================================================================

-- Table for storing legal cases
CREATE TABLE IF NOT EXISTS case_management.cases (
    id SERIAL PRIMARY KEY,
    case_id VARCHAR(255) UNIQUE NOT NULL, -- Case number
    client_id VARCHAR(255) REFERENCES case_management.clients(client_id) ON DELETE CASCADE,
    case_name VARCHAR(500), -- E.g., "Smith v. Acme Corp"
    case_type VARCHAR(100) NOT NULL, -- 'personal_injury', 'workers_comp', 'medical_malpractice', etc.
    case_subtype VARCHAR(100), -- 'car_accident', 'slip_and_fall', 'dog_bite', etc.
    case_status VARCHAR(50) DEFAULT 'open', -- 'open', 'active', 'pending', 'settled', 'closed', 'dismissed'
    priority VARCHAR(20) DEFAULT 'medium', -- 'low', 'medium', 'high', 'urgent'
    
    -- Case dates
    incident_date DATE, -- When the incident occurred
    filing_date DATE, -- When case was filed in court
    statute_of_limitations_date DATE, -- Deadline to file
    case_opened_date DATE NOT NULL,
    case_closed_date DATE,
    settlement_date DATE,
    trial_date DATE,
    
    -- Jurisdiction & Court
    jurisdiction VARCHAR(100), -- 'Federal', 'State: Florida', etc.
    court_name VARCHAR(255),
    court_case_number VARCHAR(255),
    judge_name VARCHAR(255),
    
    -- Parties
    opposing_party_name VARCHAR(500), -- Defendant/opposing party
    opposing_counsel_name VARCHAR(255),
    opposing_counsel_firm VARCHAR(500),
    
    -- Financial
    damages_claimed DECIMAL(15,2),
    settlement_amount DECIMAL(15,2),
    attorney_fees DECIMAL(15,2),
    contingency_percentage DECIMAL(5,2), -- E.g., 33.33 for 33.33%
    
    -- Assignments
    primary_attorney VARCHAR(255), -- Attorney ID or name
    assigned_paralegal VARCHAR(255),
    case_manager VARCHAR(255),
    
    -- Case details
    incident_description TEXT,
    legal_theory TEXT, -- Negligence, breach of contract, etc.
    injuries_description TEXT,
    medical_treatment_summary TEXT,
    liability_assessment TEXT,
    case_strengths TEXT,
    case_weaknesses TEXT,
    settlement_recommendation TEXT,
    
    -- Metadata
    tags TEXT[], -- Array of tags: ['high_value', 'strong_liability', etc.]
    case_phase VARCHAR(100), -- 'discovery', 'negotiation', 'litigation', 'appeal'
    next_action VARCHAR(500), -- What needs to happen next
    next_deadline DATE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    metadata JSONB
);

-- ============================================================================
-- CASE PARTIES
-- ============================================================================

-- Table for all parties involved in a case (beyond client and defendant)
CREATE TABLE IF NOT EXISTS case_management.case_parties (
    id SERIAL PRIMARY KEY,
    case_id VARCHAR(255) REFERENCES case_management.cases(case_id) ON DELETE CASCADE,
    party_type VARCHAR(50) NOT NULL, -- 'plaintiff', 'defendant', 'witness', 'expert_witness', 'insurance_adjuster'
    party_role VARCHAR(100), -- More specific role
    
    -- Party information
    party_name VARCHAR(500) NOT NULL,
    organization VARCHAR(500), -- If party is a company
    contact_email VARCHAR(255),
    contact_phone VARCHAR(50),
    address TEXT,
    
    -- Additional details
    notes TEXT,
    is_primary BOOLEAN DEFAULT FALSE, -- Primary defendant, primary witness, etc.
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- ============================================================================
-- INJURIES & MEDICAL RECORDS
-- ============================================================================

-- Table for tracking injuries
CREATE TABLE IF NOT EXISTS case_management.injuries (
    id SERIAL PRIMARY KEY,
    case_id VARCHAR(255) REFERENCES case_management.cases(case_id) ON DELETE CASCADE,
    injury_type VARCHAR(100) NOT NULL, -- 'fracture', 'laceration', 'soft_tissue', 'concussion', etc.
    injury_location VARCHAR(100), -- 'left_wrist', 'lower_back', 'head', etc.
    injury_severity VARCHAR(50), -- 'minor', 'moderate', 'severe', 'catastrophic'
    injury_description TEXT,
    icd10_code VARCHAR(20), -- Medical diagnosis code
    injury_date DATE,
    
    -- Medical treatment
    requires_surgery BOOLEAN DEFAULT FALSE,
    surgery_date DATE,
    surgery_type VARCHAR(255),
    requires_ongoing_treatment BOOLEAN DEFAULT FALSE,
    expected_recovery_time_days INTEGER,
    permanent_disability BOOLEAN DEFAULT FALSE,
    disability_percentage DECIMAL(5,2),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- Table for tracking medical providers and treatment
CREATE TABLE IF NOT EXISTS case_management.medical_providers (
    id SERIAL PRIMARY KEY,
    case_id VARCHAR(255) REFERENCES case_management.cases(case_id) ON DELETE CASCADE,
    provider_type VARCHAR(100), -- 'hospital', 'clinic', 'doctor', 'physical_therapy', 'chiropractor'
    provider_name VARCHAR(500) NOT NULL,
    specialty VARCHAR(255),
    
    -- Contact info
    contact_phone VARCHAR(50),
    contact_email VARCHAR(255),
    address TEXT,
    
    -- Treatment details
    first_visit_date DATE,
    last_visit_date DATE,
    total_visits INTEGER,
    total_billed DECIMAL(15,2),
    total_paid DECIMAL(15,2),
    insurance_coverage DECIMAL(15,2),
    
    -- Records
    records_requested BOOLEAN DEFAULT FALSE,
    records_received BOOLEAN DEFAULT FALSE,
    records_request_date DATE,
    records_received_date DATE,
    
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- ============================================================================
-- INSURANCE CLAIMS
-- ============================================================================

-- Table for insurance claims related to cases
CREATE TABLE IF NOT EXISTS case_management.insurance_claims (
    id SERIAL PRIMARY KEY,
    case_id VARCHAR(255) REFERENCES case_management.cases(case_id) ON DELETE CASCADE,
    claim_number VARCHAR(255) UNIQUE NOT NULL,
    insurance_type VARCHAR(100), -- 'auto', 'homeowners', 'workers_comp', 'health', 'umbrella'
    
    -- Insurance company
    insurance_company_name VARCHAR(500) NOT NULL,
    policy_number VARCHAR(255),
    policy_holder_name VARCHAR(255),
    
    -- Claim details
    claim_filed_date DATE,
    claim_status VARCHAR(50), -- 'submitted', 'under_review', 'approved', 'denied', 'settled'
    claim_amount DECIMAL(15,2),
    settlement_offer DECIMAL(15,2),
    settlement_accepted BOOLEAN,
    
    -- Adjuster info
    adjuster_name VARCHAR(255),
    adjuster_phone VARCHAR(50),
    adjuster_email VARCHAR(255),
    
    -- Policy limits
    policy_limit_per_person DECIMAL(15,2),
    policy_limit_per_accident DECIMAL(15,2),
    policy_limit_property_damage DECIMAL(15,2),
    
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- ============================================================================
-- CASE TIMELINE & EVENTS
-- ============================================================================

-- Table for case timeline events
CREATE TABLE IF NOT EXISTS case_management.case_events (
    id SERIAL PRIMARY KEY,
    case_id VARCHAR(255) REFERENCES case_management.cases(case_id) ON DELETE CASCADE,
    event_type VARCHAR(100) NOT NULL, -- 'incident', 'filing', 'discovery', 'deposition', 'motion', 'hearing', 'settlement_offer', 'trial'
    event_date DATE NOT NULL,
    event_time TIME,
    event_description TEXT NOT NULL,
    event_location VARCHAR(500),
    
    -- Participants
    attendees TEXT[], -- Array of attendee names
    responsible_party VARCHAR(255), -- Who is handling this
    
    -- Status
    event_status VARCHAR(50) DEFAULT 'scheduled', -- 'scheduled', 'completed', 'cancelled', 'postponed'
    is_deadline BOOLEAN DEFAULT FALSE,
    is_billable BOOLEAN DEFAULT FALSE,
    hours_spent DECIMAL(5,2),
    
    -- Related items
    related_document_ids TEXT[], -- Links to documents
    related_communication_ids TEXT[], -- Links to calls/emails
    
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    metadata JSONB
);

-- ============================================================================
-- CASE TASKS & DEADLINES
-- ============================================================================

-- Table for case tasks and to-dos
CREATE TABLE IF NOT EXISTS case_management.case_tasks (
    id SERIAL PRIMARY KEY,
    case_id VARCHAR(255) REFERENCES case_management.cases(case_id) ON DELETE CASCADE,
    task_name VARCHAR(500) NOT NULL,
    task_description TEXT,
    task_type VARCHAR(100), -- 'discovery', 'client_contact', 'court_filing', 'research', 'document_review'
    
    -- Assignment
    assigned_to VARCHAR(255) NOT NULL, -- Attorney/staff ID
    assigned_by VARCHAR(255),
    
    -- Scheduling
    due_date DATE,
    due_time TIME,
    reminder_date DATE,
    is_critical_deadline BOOLEAN DEFAULT FALSE,
    
    -- Status
    task_status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'in_progress', 'completed', 'cancelled', 'overdue'
    priority VARCHAR(20) DEFAULT 'medium',
    completed_date DATE,
    completed_by VARCHAR(255),
    
    -- Time tracking
    estimated_hours DECIMAL(5,2),
    actual_hours DECIMAL(5,2),
    is_billable BOOLEAN DEFAULT FALSE,
    
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- ============================================================================
-- CASE NOTES
-- ============================================================================

-- Table for case notes and journal entries
CREATE TABLE IF NOT EXISTS case_management.case_notes (
    id SERIAL PRIMARY KEY,
    case_id VARCHAR(255) REFERENCES case_management.cases(case_id) ON DELETE CASCADE,
    note_type VARCHAR(100), -- 'general', 'client_contact', 'research', 'strategy', 'internal'
    note_title VARCHAR(500),
    note_content TEXT NOT NULL,
    
    -- Visibility
    is_confidential BOOLEAN DEFAULT FALSE,
    is_privileged BOOLEAN DEFAULT FALSE, -- Attorney-client privilege
    
    -- Authorship
    author VARCHAR(255) NOT NULL,
    author_role VARCHAR(100), -- 'attorney', 'paralegal', 'investigator'
    
    -- Related items
    related_communication_id VARCHAR(255), -- Link to call/email/sms
    related_document_ids TEXT[],
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- ============================================================================
-- ATTORNEYS & STAFF
-- ============================================================================

-- Table for law firm attorneys and staff
CREATE TABLE IF NOT EXISTS case_management.attorneys (
    id SERIAL PRIMARY KEY,
    attorney_id VARCHAR(255) UNIQUE NOT NULL,
    first_name VARCHAR(255) NOT NULL,
    last_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(50),
    
    -- Professional info
    bar_number VARCHAR(100),
    bar_state VARCHAR(100),
    bar_admission_date DATE,
    role VARCHAR(100), -- 'partner', 'associate', 'paralegal', 'legal_assistant', 'investigator'
    department VARCHAR(100), -- 'personal_injury', 'workers_comp', 'litigation'
    
    -- Status
    employment_status VARCHAR(50) DEFAULT 'active', -- 'active', 'inactive', 'terminated'
    hire_date DATE,
    termination_date DATE,
    
    -- Specializations
    practice_areas TEXT[], -- Array of specializations
    languages_spoken TEXT[],
    
    -- Contact
    office_location VARCHAR(255),
    extension VARCHAR(20),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Clients indexes
CREATE INDEX IF NOT EXISTS idx_clients_name ON case_management.clients(last_name, first_name);
CREATE INDEX IF NOT EXISTS idx_clients_email ON case_management.clients(email);
CREATE INDEX IF NOT EXISTS idx_clients_phone ON case_management.clients(phone_primary);
CREATE INDEX IF NOT EXISTS idx_clients_status ON case_management.clients(client_status);

-- Cases indexes
CREATE INDEX IF NOT EXISTS idx_cases_client ON case_management.cases(client_id);
CREATE INDEX IF NOT EXISTS idx_cases_status ON case_management.cases(case_status);
CREATE INDEX IF NOT EXISTS idx_cases_type ON case_management.cases(case_type);
CREATE INDEX IF NOT EXISTS idx_cases_attorney ON case_management.cases(primary_attorney);
CREATE INDEX IF NOT EXISTS idx_cases_incident_date ON case_management.cases(incident_date);
CREATE INDEX IF NOT EXISTS idx_cases_opened ON case_management.cases(case_opened_date);
CREATE INDEX IF NOT EXISTS idx_cases_next_deadline ON case_management.cases(next_deadline);

-- Case parties indexes
CREATE INDEX IF NOT EXISTS idx_parties_case ON case_management.case_parties(case_id);
CREATE INDEX IF NOT EXISTS idx_parties_type ON case_management.case_parties(party_type);

-- Injuries indexes
CREATE INDEX IF NOT EXISTS idx_injuries_case ON case_management.injuries(case_id);
CREATE INDEX IF NOT EXISTS idx_injuries_type ON case_management.injuries(injury_type);

-- Medical providers indexes
CREATE INDEX IF NOT EXISTS idx_medical_case ON case_management.medical_providers(case_id);
CREATE INDEX IF NOT EXISTS idx_medical_type ON case_management.medical_providers(provider_type);

-- Insurance claims indexes
CREATE INDEX IF NOT EXISTS idx_insurance_case ON case_management.insurance_claims(case_id);
CREATE INDEX IF NOT EXISTS idx_insurance_status ON case_management.insurance_claims(claim_status);

-- Case events indexes
CREATE INDEX IF NOT EXISTS idx_events_case ON case_management.case_events(case_id);
CREATE INDEX IF NOT EXISTS idx_events_date ON case_management.case_events(event_date);
CREATE INDEX IF NOT EXISTS idx_events_type ON case_management.case_events(event_type);

-- Case tasks indexes
CREATE INDEX IF NOT EXISTS idx_tasks_case ON case_management.case_tasks(case_id);
CREATE INDEX IF NOT EXISTS idx_tasks_assigned ON case_management.case_tasks(assigned_to);
CREATE INDEX IF NOT EXISTS idx_tasks_due ON case_management.case_tasks(due_date);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON case_management.case_tasks(task_status);

-- Case notes indexes
CREATE INDEX IF NOT EXISTS idx_notes_case ON case_management.case_notes(case_id);
CREATE INDEX IF NOT EXISTS idx_notes_author ON case_management.case_notes(author);
CREATE INDEX IF NOT EXISTS idx_notes_content ON case_management.case_notes USING gin(to_tsvector('english', note_content));

-- Attorneys indexes
CREATE INDEX IF NOT EXISTS idx_attorneys_name ON case_management.attorneys(last_name, first_name);
CREATE INDEX IF NOT EXISTS idx_attorneys_status ON case_management.attorneys(employment_status);

-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

-- View: Active cases with client information
CREATE OR REPLACE VIEW case_management.active_cases_summary AS
SELECT 
    c.case_id,
    c.case_name,
    c.case_type,
    c.case_status,
    c.priority,
    c.incident_date,
    c.damages_claimed,
    c.settlement_amount,
    c.primary_attorney,
    cl.first_name || ' ' || cl.last_name as client_name,
    cl.email as client_email,
    cl.phone_primary as client_phone,
    c.next_action,
    c.next_deadline,
    c.created_at,
    c.updated_at
FROM case_management.cases c
JOIN case_management.clients cl ON c.client_id = cl.client_id
WHERE c.case_status IN ('open', 'active', 'pending')
ORDER BY c.next_deadline ASC NULLS LAST, c.priority DESC;

-- View: Case financial summary
CREATE OR REPLACE VIEW case_management.case_financials AS
SELECT 
    c.case_id,
    c.case_name,
    c.damages_claimed,
    c.settlement_amount,
    c.attorney_fees,
    c.contingency_percentage,
    COALESCE(SUM(mp.total_billed), 0) as total_medical_bills,
    COALESCE(SUM(mp.total_paid), 0) as total_medical_paid,
    COALESCE(SUM(ic.claim_amount), 0) as total_insurance_claims
FROM case_management.cases c
LEFT JOIN case_management.medical_providers mp ON c.case_id = mp.case_id
LEFT JOIN case_management.insurance_claims ic ON c.case_id = ic.case_id
GROUP BY c.case_id, c.case_name, c.damages_claimed, c.settlement_amount, 
         c.attorney_fees, c.contingency_percentage;

-- View: Attorney workload
CREATE OR REPLACE VIEW case_management.attorney_workload AS
SELECT 
    primary_attorney,
    COUNT(*) FILTER (WHERE case_status IN ('open', 'active')) as active_cases,
    COUNT(*) FILTER (WHERE case_status = 'pending') as pending_cases,
    COUNT(*) FILTER (WHERE priority = 'urgent') as urgent_cases,
    MIN(next_deadline) as nearest_deadline,
    AVG(EXTRACT(DAY FROM (CURRENT_DATE - case_opened_date))) as avg_case_age_days
FROM case_management.cases
WHERE primary_attorney IS NOT NULL
GROUP BY primary_attorney;

-- ============================================================================
-- GRANT PERMISSIONS
-- ============================================================================

GRANT USAGE ON SCHEMA case_management TO paralegal_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA case_management TO paralegal_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA case_management TO paralegal_user;

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON SCHEMA case_management IS 'Schema for client and case management: clients, cases, injuries, insurance, tasks, notes';
COMMENT ON TABLE case_management.clients IS 'Client personal information and contact details';
COMMENT ON TABLE case_management.cases IS 'Legal cases with details, parties, financials, and status';
COMMENT ON TABLE case_management.injuries IS 'Injuries sustained by clients in their cases';
COMMENT ON TABLE case_management.medical_providers IS 'Medical providers and treatment records for cases';
COMMENT ON TABLE case_management.insurance_claims IS 'Insurance claims related to cases';
COMMENT ON TABLE case_management.case_events IS 'Timeline of events for each case';
COMMENT ON TABLE case_management.case_tasks IS 'Tasks and deadlines for case management';
COMMENT ON TABLE case_management.case_notes IS 'Notes and journal entries for cases';
