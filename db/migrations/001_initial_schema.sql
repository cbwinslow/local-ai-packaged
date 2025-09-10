-- Database schema for government data pipeline
-- Migration: 001_initial_schema

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- API Keys table
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    api_key TEXT NOT NULL UNIQUE,
    service_name TEXT NOT NULL, -- e.g., 'congress_gov', 'govinfo'
    rate_limit_per_hour INTEGER DEFAULT 1000,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT,
    notes TEXT
);

-- API Call Logs
CREATE TABLE api_call_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    api_key_id UUID REFERENCES api_keys(id) ON DELETE SET NULL,
    service_name TEXT NOT NULL,
    endpoint TEXT NOT NULL,
    method TEXT NOT NULL,
    status_code INTEGER,
    response_time_ms INTEGER,
    success BOOLEAN,
    error_message TEXT,
    request_headers JSONB,
    response_headers JSONB,
    request_body TEXT,
    response_body TEXT,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Congress.gov Bills
CREATE TABLE congress_bills (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    bill_id TEXT NOT NULL UNIQUE,
    bill_type TEXT NOT NULL,
    number TEXT NOT NULL,
    congress INTEGER NOT NULL,
    title TEXT,
    short_title TEXT,
    popular_title TEXT,
    sponsor_id TEXT,
    sponsor_name TEXT,
    sponsor_state TEXT,
    sponsor_party TEXT,
    introduced_date DATE,
    latest_major_action TEXT,
    latest_major_action_date TIMESTAMP WITH TIME ZONE,
    govtrack_url TEXT,
    congressdotgov_url TEXT,
    gpo_pdf_url TEXT,
    congressdotgov_title TEXT,
    active BOOLEAN,
    enacted BOOLEAN,
    vetoed BOOLEAN,
    primary_subject TEXT,
    summary TEXT,
    summary_short TEXT,
    latest_summary TEXT,
    latest_summary_date TIMESTAMP WITH TIME ZONE,
    raw_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_fetched_at TIMESTAMP WITH TIME ZONE
);

-- Congress.gov Bill Actions
CREATE TABLE congress_bill_actions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    bill_id UUID REFERENCES congress_bills(id) ON DELETE CASCADE,
    action_date TIMESTAMP WITH TIME ZONE NOT NULL,
    action_text TEXT NOT NULL,
    action_code TEXT,
    action_type TEXT,
    action_committee TEXT,
    acted_by TEXT,
    acted_by_chamber TEXT,
    acted_by_party TEXT,
    acted_by_state TEXT,
    acted_by_district TEXT,
    acted_by_title TEXT,
    raw_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(bill_id, action_date, action_text)
);

-- Congress.gov Bill Subjects
CREATE TABLE congress_bill_subjects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    bill_id UUID REFERENCES congress_bills(id) ON DELETE CASCADE,
    subject TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(bill_id, subject)
);

-- Congress.gov Bill Cosponsors
CREATE TABLE congress_bill_cosponsors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    bill_id UUID REFERENCES congress_bills(id) ON DELETE CASCADE,
    bioguide_id TEXT,
    thomas_id TEXT,
    govtrack_id TEXT,
    name TEXT NOT NULL,
    state TEXT,
    district TEXT,
    party TEXT,
    date_cosponsored DATE,
    is_original_cosponsor BOOLEAN,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(bill_id, name, date_cosponsored)
);

-- Congress.gov Members
CREATE TABLE congress_members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    member_id TEXT NOT NULL UNIQUE,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    middle_name TEXT,
    suffix TEXT,
    date_of_birth DATE,
    gender TEXT,
    party TEXT,
    leadership_role TEXT,
    twitter_account TEXT,
    facebook_account TEXT,
    youtube_account TEXT,
    govtrack_id TEXT,
    cspan_id TEXT,
    votesmart_id TEXT,
    icpsr_id TEXT,
    crp_id TEXT,
    google_entity_id TEXT,
    fec_candidate_id TEXT,
    url TEXT,
    rss_url TEXT,
    contact_form TEXT,
    in_office BOOLEAN,
    cook_pvi TEXT,
    dw_nominate FLOAT,
    ideal_point FLOAT,
    seniority INTEGER,
    next_election TEXT,
    total_votes INTEGER,
    missed_votes INTEGER,
    total_present INTEGER,
    last_updated TIMESTAMP WITH TIME ZONE,
    ocd_id TEXT,
    office TEXT,
    phone TEXT,
    fax TEXT,
    state_rank TEXT,
    senate_class TEXT,
    state_name TEXT,
    lis_id TEXT,
    missed_votes_pct FLOAT,
    votes_with_party_pct FLOAT,
    votes_against_party_pct FLOAT,
    raw_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Congress.gov Member Roles
CREATE TABLE congress_member_roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    member_id UUID REFERENCES congress_members(id) ON DELETE CASCADE,
    congress INTEGER NOT NULL,
    chamber TEXT NOT NULL,
    title TEXT,
    short_title TEXT,
    state TEXT,
    party TEXT,
    leadership_role TEXT,
    fec_candidate_id TEXT,
    seniority INTEGER,
    district TEXT,
    at_large BOOLEAN,
    ocd_id TEXT,
    start_date DATE,
    end_date DATE,
    office TEXT,
    phone TEXT,
    fax TEXT,
    contact_form TEXT,
    cook_pvi TEXT,
    dw_nominate FLOAT,
    ideal_point FLOAT,
    next_election TEXT,
    total_votes INTEGER,
    missed_votes INTEGER,
    total_present INTEGER,
    senate_class TEXT,
    state_rank TEXT,
    lis_id TEXT,
    bills_sponsored INTEGER,
    bills_cosponsored INTEGER,
    missed_votes_pct FLOAT,
    votes_with_party_pct FLOAT,
    votes_against_party_pct FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(member_id, congress, chamber)
);

-- GovInfo Collections
CREATE TABLE govinfo_collections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    collection_code TEXT NOT NULL UNIQUE,
    collection_name TEXT NOT NULL,
    category TEXT,
    description TEXT,
    package_count INTEGER,
    package_last_modified TIMESTAMP WITH TIME ZONE,
    download_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_checked_at TIMESTAMP WITH TIME ZONE
);

-- GovInfo Packages
CREATE TABLE govinfo_packages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    package_id TEXT NOT NULL UNIQUE,
    collection_id UUID REFERENCES govinfo_collections(id) ON DELETE CASCADE,
    last_modified TIMESTAMP WITH TIME ZONE NOT NULL,
    package_link TEXT,
    doc_class TEXT,
    title TEXT,
    branch TEXT,
    pages INTEGER,
    government_author1 TEXT,
    government_author2 TEXT,
    document_type TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_checked_at TIMESTAMP WITH TIME ZONE,
    raw_metadata JSONB,
    content TEXT
);

-- GovInfo Download Queue
CREATE TABLE govinfo_download_queue (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    package_id TEXT NOT NULL UNIQUE,
    collection_id UUID REFERENCES govinfo_collections(id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'pending', -- pending, downloading, completed, failed
    priority INTEGER DEFAULT 0,
    retry_count INTEGER DEFAULT 0,
    last_error TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Create indexes for better query performance
CREATE INDEX idx_congress_bills_congress ON congress_bills(congress);
CREATE INDEX idx_congress_bills_bill_type ON congress_bills(bill_type);
CREATE INDEX idx_congress_bills_sponsor_id ON congress_bills(sponsor_id);
CREATE INDEX idx_congress_bills_introduced_date ON congress_bills(introduced_date);
CREATE INDEX idx_congress_bill_actions_bill_id ON congress_bill_actions(bill_id);
CREATE INDEX idx_congress_bill_actions_action_date ON congress_bill_actions(action_date);
CREATE INDEX idx_congress_members_state ON congress_members(state);
CREATE INDEX idx_congress_members_party ON congress_members(party);
CREATE INDEX idx_govinfo_packages_collection_id ON govinfo_packages(collection_id);
CREATE INDEX idx_govinfo_packages_last_modified ON govinfo_packages(last_modified);
CREATE INDEX idx_govinfo_download_queue_status ON govinfo_download_queue(status);
CREATE INDEX idx_govinfo_download_queue_priority ON govinfo_download_queue(priority);

-- Create a function to update the updated_at column
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers to update updated_at columns
CREATE TRIGGER update_congress_bills_modtime
    BEFORE UPDATE ON congress_bills
    FOR EACH ROW EXECUTE FUNCTION update_modified_column();

CREATE TRIGGER update_congress_members_modtime
    BEFORE UPDATE ON congress_members
    FOR EACH ROW EXECUTE FUNCTION update_modified_column();

CREATE TRIGGER update_govinfo_collections_modtime
    BEFORE UPDATE ON govinfo_collections
    FOR EACH ROW EXECUTE FUNCTION update_modified_column();

CREATE TRIGGER update_govinfo_packages_modtime
    BEFORE UPDATE ON govinfo_packages
    FOR EACH ROW EXECUTE FUNCTION update_modified_column();

-- Create a function to log API calls
CREATE OR REPLACE FUNCTION log_api_call(
    p_api_key_id UUID,
    p_service_name TEXT,
    p_endpoint TEXT,
    p_method TEXT,
    p_status_code INTEGER,
    p_response_time_ms INTEGER,
    p_success BOOLEAN,
    p_error_message TEXT,
    p_request_headers JSONB,
    p_response_headers JSONB,
    p_request_body TEXT,
    p_response_body TEXT,
    p_ip_address INET,
    p_user_agent TEXT
) RETURNS UUID AS $$
DECLARE
    v_log_id UUID;
BEGIN
    INSERT INTO api_call_logs (
        api_key_id,
        service_name,
        endpoint,
        method,
        status_code,
        response_time_ms,
        success,
        error_message,
        request_headers,
        response_headers,
        request_body,
        response_body,
        ip_address,
        user_agent
    ) VALUES (
        p_api_key_id,
        p_service_name,
        p_endpoint,
        p_method,
        p_status_code,
        p_response_time_ms,
        p_success,
        p_error_message,
        p_request_headers,
        p_response_headers,
        p_request_body,
        p_response_body,
        p_ip_address,
        p_user_agent
    )
    RETURNING id INTO v_log_id;
    
    RETURN v_log_id;
END;
$$ LANGUAGE plpgsql;
