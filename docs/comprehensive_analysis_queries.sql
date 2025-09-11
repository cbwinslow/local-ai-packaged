-- ================================================================
-- Government Data Analysis SQL Queries
-- ================================================================
-- Comprehensive SQL queries for analyzing government data ingested
-- from federal, state, local, and international sources
-- ================================================================

-- ================================================================
-- POLITICIAN EFFECTIVENESS ANALYSIS
-- ================================================================

-- Top 50 Most Effective Politicians by Bills Sponsored
SELECT 
    p.name,
    p.party,
    p.state,
    p.chamber,
    COUNT(b.id) AS bills_sponsored,
    COUNT(DISTINCT v.id) AS votes_cast,
    CASE 
        WHEN p.chamber = 'senate' THEN COUNT(b.id) * 1.5 + COUNT(v.id) * 0.1
        ELSE COUNT(b.id) * 1.0 + COUNT(v.id) * 0.1
    END AS effectiveness_score,
    MAX(b.introduced_date) AS last_bill_date,
    ROUND(AVG(
        CASE v.position 
            WHEN 'yes' THEN 1 
            WHEN 'no' THEN 0 
            ELSE NULL 
        END
    ) * 100, 2) AS yes_vote_percentage
FROM politicians p
LEFT JOIN bills b ON b.sponsor_id = p.id::text
LEFT JOIN votes v ON v.politician_id = p.id::text
WHERE p.current_office = true
GROUP BY p.id, p.name, p.party, p.state, p.chamber
HAVING COUNT(b.id) > 0 OR COUNT(v.id) > 0
ORDER BY effectiveness_score DESC
LIMIT 50;

-- Party Leadership Analysis
SELECT 
    p.party,
    p.chamber,
    COUNT(DISTINCT p.id) AS total_members,
    AVG(
        CASE 
            WHEN p.chamber = 'senate' THEN bills_count * 1.5 + votes_count * 0.1
            ELSE bills_count * 1.0 + votes_count * 0.1
        END
    ) AS avg_effectiveness_score,
    SUM(bills_count) AS total_bills_sponsored,
    SUM(votes_count) AS total_votes_cast
FROM politicians p
JOIN (
    SELECT 
        sponsor_id,
        COUNT(*) AS bills_count
    FROM bills 
    WHERE introduced_date >= CURRENT_DATE - INTERVAL '2 years'
    GROUP BY sponsor_id
) b ON b.sponsor_id = p.id::text
JOIN (
    SELECT 
        politician_id,
        COUNT(*) AS votes_count
    FROM votes 
    WHERE vote_date >= CURRENT_DATE - INTERVAL '2 years'
    GROUP BY politician_id
) v ON v.politician_id = p.id::text
WHERE p.current_office = true
GROUP BY p.party, p.chamber
ORDER BY avg_effectiveness_score DESC;

-- Bipartisan Cooperation Score
WITH bipartisan_votes AS (
    SELECT 
        v.politician_id,
        p.party,
        COUNT(*) AS total_votes,
        COUNT(CASE 
            WHEN (p.party = 'Democratic' AND majority_position = 'Republican') OR
                 (p.party = 'Republican' AND majority_position = 'Democratic')
            THEN 1 
        END) AS cross_party_votes
    FROM votes v
    JOIN politicians p ON p.id::text = v.politician_id
    JOIN (
        SELECT 
            vote_id,
            CASE 
                WHEN COUNT(CASE WHEN party = 'Republican' AND position = 'yes' THEN 1 END) >
                     COUNT(CASE WHEN party = 'Democratic' AND position = 'yes' THEN 1 END)
                THEN 'Republican'
                ELSE 'Democratic'
            END AS majority_position
        FROM votes v2
        JOIN politicians p2 ON p2.id::text = v2.politician_id
        WHERE v2.position IN ('yes', 'no')
        GROUP BY vote_id
    ) maj ON maj.vote_id = v.vote_id
    WHERE v.vote_date >= CURRENT_DATE - INTERVAL '1 year'
    AND v.position IN ('yes', 'no')
    GROUP BY v.politician_id, p.party
    HAVING COUNT(*) >= 50  -- Minimum vote threshold
)
SELECT 
    p.name,
    p.party,
    p.state,
    bv.total_votes,
    bv.cross_party_votes,
    ROUND((bv.cross_party_votes::numeric / bv.total_votes * 100), 2) AS bipartisan_score
FROM bipartisan_votes bv
JOIN politicians p ON p.id::text = bv.politician_id
ORDER BY bipartisan_score DESC
LIMIT 25;

-- ================================================================
-- LEGISLATIVE TRENDS ANALYSIS
-- ================================================================

-- Bills by Congress and Status
SELECT 
    congress_number,
    status,
    COUNT(*) AS bill_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY congress_number), 2) AS percentage
FROM bills
WHERE congress_number IS NOT NULL
GROUP BY congress_number, status
ORDER BY congress_number DESC, bill_count DESC;

-- Monthly Bill Introduction Trends
SELECT 
    DATE_TRUNC('month', introduced_date) AS month,
    COUNT(*) AS bills_introduced,
    COUNT(CASE WHEN bill_type = 'hr' THEN 1 END) AS house_bills,
    COUNT(CASE WHEN bill_type = 's' THEN 1 END) AS senate_bills,
    COUNT(CASE WHEN status ILIKE '%passed%' OR status ILIKE '%enacted%' THEN 1 END) AS bills_passed
FROM bills
WHERE introduced_date >= CURRENT_DATE - INTERVAL '2 years'
GROUP BY DATE_TRUNC('month', introduced_date)
ORDER BY month DESC;

-- Top Legislative Subjects/Topics
SELECT 
    unnest(subjects) AS subject,
    COUNT(*) AS bill_count,
    COUNT(CASE WHEN status ILIKE '%passed%' OR status ILIKE '%enacted%' THEN 1 END) AS passed_count,
    ROUND(
        COUNT(CASE WHEN status ILIKE '%passed%' OR status ILIKE '%enacted%' THEN 1 END) * 100.0 / COUNT(*), 
        2
    ) AS success_rate
FROM bills
WHERE subjects IS NOT NULL 
AND introduced_date >= CURRENT_DATE - INTERVAL '2 years'
GROUP BY subject
HAVING COUNT(*) >= 5
ORDER BY bill_count DESC
LIMIT 50;

-- Legislative Success Rate by Party
SELECT 
    p.party,
    p.chamber,
    COUNT(b.id) AS total_bills,
    COUNT(CASE WHEN b.status ILIKE '%passed%' OR b.status ILIKE '%enacted%' THEN 1 END) AS successful_bills,
    ROUND(
        COUNT(CASE WHEN b.status ILIKE '%passed%' OR b.status ILIKE '%enacted%' THEN 1 END) * 100.0 / COUNT(b.id),
        2
    ) AS success_rate
FROM politicians p
JOIN bills b ON b.sponsor_id = p.id::text
WHERE b.introduced_date >= CURRENT_DATE - INTERVAL '2 years'
GROUP BY p.party, p.chamber
HAVING COUNT(b.id) >= 10
ORDER BY success_rate DESC;

-- ================================================================
-- VOTING PATTERN ANALYSIS
-- ================================================================

-- Party Unity Scores
SELECT 
    p.party,
    p.chamber,
    COUNT(v.id) AS total_votes,
    COUNT(CASE 
        WHEN v.position = party_majority.majority_vote THEN 1 
    END) AS party_line_votes,
    ROUND(
        COUNT(CASE WHEN v.position = party_majority.majority_vote THEN 1 END) * 100.0 / COUNT(v.id),
        2
    ) AS party_unity_score
FROM votes v
JOIN politicians p ON p.id::text = v.politician_id
JOIN (
    SELECT 
        vote_id,
        party,
        MODE() WITHIN GROUP (ORDER BY position) AS majority_vote
    FROM votes v2
    JOIN politicians p2 ON p2.id::text = v2.politician_id
    WHERE v2.position IN ('yes', 'no')
    GROUP BY vote_id, party
) party_majority ON party_majority.vote_id = v.vote_id AND party_majority.party = p.party
WHERE v.vote_date >= CURRENT_DATE - INTERVAL '1 year'
AND v.position IN ('yes', 'no')
GROUP BY p.party, p.chamber
ORDER BY party_unity_score DESC;

-- Most Controversial Votes (Close Split)
SELECT 
    v.vote_id,
    v.description,
    v.vote_date,
    v.chamber,
    COUNT(CASE WHEN position = 'yes' THEN 1 END) AS yes_votes,
    COUNT(CASE WHEN position = 'no' THEN 1 END) AS no_votes,
    ABS(
        COUNT(CASE WHEN position = 'yes' THEN 1 END) - 
        COUNT(CASE WHEN position = 'no' THEN 1 END)
    ) AS vote_margin,
    v.result
FROM votes v
WHERE v.vote_date >= CURRENT_DATE - INTERVAL '1 year'
AND v.position IN ('yes', 'no')
GROUP BY v.vote_id, v.description, v.vote_date, v.chamber, v.result
HAVING COUNT(CASE WHEN position = 'yes' THEN 1 END) > 0 
   AND COUNT(CASE WHEN position = 'no' THEN 1 END) > 0
ORDER BY vote_margin ASC
LIMIT 20;

-- Individual Politician Voting Attendance
SELECT 
    p.name,
    p.party,
    p.state,
    p.chamber,
    COUNT(v.id) AS votes_recorded,
    COUNT(CASE WHEN v.position IN ('yes', 'no') THEN 1 END) AS substantive_votes,
    COUNT(CASE WHEN v.position = 'not_voting' THEN 1 END) AS missed_votes,
    ROUND(
        COUNT(CASE WHEN v.position IN ('yes', 'no') THEN 1 END) * 100.0 / COUNT(v.id),
        2
    ) AS attendance_rate
FROM politicians p
JOIN votes v ON v.politician_id = p.id::text
WHERE v.vote_date >= CURRENT_DATE - INTERVAL '6 months'
AND p.current_office = true
GROUP BY p.id, p.name, p.party, p.state, p.chamber
HAVING COUNT(v.id) >= 10
ORDER BY attendance_rate ASC
LIMIT 25;

-- ================================================================
-- DATA SOURCE PERFORMANCE ANALYSIS
-- ================================================================

-- Data Source Statistics
SELECT 
    ds.name,
    ds.category,
    ds.source_type,
    ds.status,
    COUNT(d.id) AS documents_collected,
    ds.last_successful_sync,
    EXTRACT(DAYS FROM NOW() - ds.last_successful_sync) AS days_since_sync,
    ds.rate_limit_per_hour,
    ds.api_key_required
FROM data_sources ds
LEFT JOIN documents d ON d.source_id = ds.id
GROUP BY ds.id, ds.name, ds.category, ds.source_type, ds.status, 
         ds.last_successful_sync, ds.rate_limit_per_hour, ds.api_key_required
ORDER BY documents_collected DESC;

-- Document Processing Statistics
SELECT 
    document_type,
    COUNT(*) AS total_documents,
    COUNT(CASE WHEN processed = true THEN 1 END) AS processed_documents,
    COUNT(CASE WHEN embedding_id IS NOT NULL THEN 1 END) AS vectorized_documents,
    AVG(LENGTH(content)) AS avg_content_length,
    MIN(date_ingested) AS first_ingested,
    MAX(date_ingested) AS last_ingested
FROM documents
WHERE content IS NOT NULL
GROUP BY document_type
ORDER BY total_documents DESC;

-- Ingestion Run Performance
SELECT 
    DATE(start_time) AS run_date,
    run_type,
    COUNT(*) AS total_runs,
    COUNT(CASE WHEN status = 'completed' THEN 1 END) AS successful_runs,
    COUNT(CASE WHEN status = 'failed' THEN 1 END) AS failed_runs,
    AVG(records_processed) AS avg_records_processed,
    AVG(EXTRACT(EPOCH FROM (end_time - start_time))/60) AS avg_duration_minutes
FROM ingestion_runs
WHERE start_time >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE(start_time), run_type
ORDER BY run_date DESC;

-- ================================================================
-- COMMITTEE ANALYSIS
-- ================================================================

-- Committee Membership Analysis (requires JSON parsing)
SELECT 
    committee_name,
    COUNT(*) AS member_count,
    COUNT(CASE WHEN party = 'Democratic' THEN 1 END) AS democratic_members,
    COUNT(CASE WHEN party = 'Republican' THEN 1 END) AS republican_members,
    COUNT(CASE WHEN chamber = 'house' THEN 1 END) AS house_members,
    COUNT(CASE WHEN chamber = 'senate' THEN 1 END) AS senate_members
FROM (
    SELECT 
        p.id,
        p.name,
        p.party,
        p.chamber,
        jsonb_array_elements_text(p.committee_memberships) AS committee_name
    FROM politicians p
    WHERE p.committee_memberships IS NOT NULL 
    AND p.current_office = true
) committee_members
GROUP BY committee_name
HAVING COUNT(*) >= 5
ORDER BY member_count DESC;

-- ================================================================
-- GEOGRAPHIC ANALYSIS
-- ================================================================

-- State Delegation Analysis
SELECT 
    state,
    COUNT(*) AS total_delegation,
    COUNT(CASE WHEN party = 'Democratic' THEN 1 END) AS democratic_members,
    COUNT(CASE WHEN party = 'Republican' THEN 1 END) AS republican_members,
    COUNT(CASE WHEN party = 'Independent' THEN 1 END) AS independent_members,
    COUNT(CASE WHEN chamber = 'house' THEN 1 END) AS house_members,
    COUNT(CASE WHEN chamber = 'senate' THEN 1 END) AS senate_members,
    SUM(
        CASE 
            WHEN chamber = 'senate' THEN bills_sponsored * 1.5 + votes_cast * 0.1
            ELSE bills_sponsored * 1.0 + votes_cast * 0.1
        END
    ) / COUNT(*) AS avg_delegation_effectiveness
FROM (
    SELECT 
        p.*,
        COALESCE(b.bill_count, 0) AS bills_sponsored,
        COALESCE(v.vote_count, 0) AS votes_cast
    FROM politicians p
    LEFT JOIN (
        SELECT sponsor_id, COUNT(*) AS bill_count
        FROM bills 
        WHERE introduced_date >= CURRENT_DATE - INTERVAL '2 years'
        GROUP BY sponsor_id
    ) b ON b.sponsor_id = p.id::text
    LEFT JOIN (
        SELECT politician_id, COUNT(*) AS vote_count
        FROM votes 
        WHERE vote_date >= CURRENT_DATE - INTERVAL '1 year'
        GROUP BY politician_id
    ) v ON v.politician_id = p.id::text
    WHERE p.current_office = true
) delegation_stats
GROUP BY state
ORDER BY avg_delegation_effectiveness DESC;

-- Regional Bill Topics
SELECT 
    p.state,
    unnest(b.subjects) AS subject,
    COUNT(*) AS bill_count
FROM bills b
JOIN politicians p ON p.id::text = b.sponsor_id
WHERE b.introduced_date >= CURRENT_DATE - INTERVAL '1 year'
AND b.subjects IS NOT NULL
GROUP BY p.state, subject
HAVING COUNT(*) >= 2
ORDER BY p.state, bill_count DESC;

-- ================================================================
-- TEMPORAL ANALYSIS
-- ================================================================

-- Legislative Activity by Time of Year
SELECT 
    EXTRACT(MONTH FROM introduced_date) AS month,
    TO_CHAR(introduced_date, 'Month') AS month_name,
    COUNT(*) AS bills_introduced,
    AVG(COUNT(*)) OVER () AS avg_monthly_bills
FROM bills
WHERE introduced_date >= CURRENT_DATE - INTERVAL '5 years'
GROUP BY EXTRACT(MONTH FROM introduced_date), TO_CHAR(introduced_date, 'Month')
ORDER BY month;

-- Voting Activity by Day of Week
SELECT 
    EXTRACT(DOW FROM vote_date) AS day_of_week,
    TO_CHAR(vote_date, 'Day') AS day_name,
    COUNT(*) AS votes_held,
    COUNT(DISTINCT vote_id) AS unique_votes
FROM votes
WHERE vote_date >= CURRENT_DATE - INTERVAL '2 years'
GROUP BY EXTRACT(DOW FROM vote_date), TO_CHAR(vote_date, 'Day')
ORDER BY day_of_week;

-- ================================================================
-- ADVANCED ANALYTICS QUERIES
-- ================================================================

-- Politician Influence Network (based on bill co-sponsorship)
WITH cosponsorship_network AS (
    SELECT 
        b.sponsor_id AS sponsor,
        jsonb_array_elements_text(b.cosponsors) AS cosponsor,
        COUNT(*) AS collaboration_count
    FROM bills b
    WHERE b.cosponsors IS NOT NULL
    AND b.introduced_date >= CURRENT_DATE - INTERVAL '2 years'
    GROUP BY b.sponsor_id, jsonb_array_elements_text(b.cosponsors)
    HAVING COUNT(*) >= 3
)
SELECT 
    p1.name AS sponsor_name,
    p1.party AS sponsor_party,
    p2.name AS cosponsor_name,
    p2.party AS cosponsor_party,
    cn.collaboration_count,
    CASE 
        WHEN p1.party = p2.party THEN 'Same Party'
        ELSE 'Cross Party'
    END AS collaboration_type
FROM cosponsorship_network cn
JOIN politicians p1 ON p1.id::text = cn.sponsor
JOIN politicians p2 ON p2.bioguide_id = cn.cosponsor
ORDER BY cn.collaboration_count DESC
LIMIT 100;

-- Legislative Momentum (bills that gain traction)
SELECT 
    b.bill_id,
    b.title,
    b.sponsor_id,
    p.name AS sponsor_name,
    p.party,
    jsonb_array_length(b.cosponsors) AS cosponsor_count,
    COUNT(v.id) AS vote_count,
    b.status,
    CASE 
        WHEN b.status ILIKE '%passed%' OR b.status ILIKE '%enacted%' THEN 'High'
        WHEN jsonb_array_length(b.cosponsors) > 50 THEN 'Medium'
        ELSE 'Low'
    END AS momentum_level
FROM bills b
LEFT JOIN politicians p ON p.id::text = b.sponsor_id
LEFT JOIN votes v ON v.bill_id = b.id::text
WHERE b.introduced_date >= CURRENT_DATE - INTERVAL '2 years'
GROUP BY b.id, b.bill_id, b.title, b.sponsor_id, p.name, p.party, b.cosponsors, b.status
HAVING jsonb_array_length(b.cosponsors) > 10 OR COUNT(v.id) > 0
ORDER BY 
    CASE momentum_level 
        WHEN 'High' THEN 3 
        WHEN 'Medium' THEN 2 
        ELSE 1 
    END DESC,
    jsonb_array_length(b.cosponsors) DESC
LIMIT 50;

-- Data Quality Assessment
SELECT 
    'Politicians' AS table_name,
    COUNT(*) AS total_records,
    COUNT(CASE WHEN name IS NULL OR name = '' THEN 1 END) AS missing_names,
    COUNT(CASE WHEN party IS NULL OR party = '' THEN 1 END) AS missing_party,
    COUNT(CASE WHEN state IS NULL OR state = '' THEN 1 END) AS missing_state,
    ROUND(
        (COUNT(*) - COUNT(CASE WHEN name IS NULL OR name = '' THEN 1 END)) * 100.0 / COUNT(*), 
        2
    ) AS data_completeness_pct
FROM politicians

UNION ALL

SELECT 
    'Bills',
    COUNT(*),
    COUNT(CASE WHEN title IS NULL OR title = '' THEN 1 END),
    COUNT(CASE WHEN sponsor_id IS NULL OR sponsor_id = '' THEN 1 END),
    COUNT(CASE WHEN introduced_date IS NULL THEN 1 END),
    ROUND(
        (COUNT(*) - COUNT(CASE WHEN title IS NULL OR title = '' THEN 1 END)) * 100.0 / COUNT(*), 
        2
    )
FROM bills

UNION ALL

SELECT 
    'Documents',
    COUNT(*),
    COUNT(CASE WHEN title IS NULL OR title = '' THEN 1 END),
    COUNT(CASE WHEN content IS NULL OR content = '' THEN 1 END),
    COUNT(CASE WHEN date_ingested IS NULL THEN 1 END),
    ROUND(
        (COUNT(*) - COUNT(CASE WHEN content IS NULL OR content = '' THEN 1 END)) * 100.0 / COUNT(*), 
        2
    )
FROM documents;

-- ================================================================
-- PERFORMANCE OPTIMIZATION INDICES
-- ================================================================

-- Recommended indices for performance optimization:
/*
CREATE INDEX CONCURRENTLY idx_bills_sponsor_date ON bills(sponsor_id, introduced_date);
CREATE INDEX CONCURRENTLY idx_votes_politician_date ON votes(politician_id, vote_date);
CREATE INDEX CONCURRENTLY idx_votes_vote_id_position ON votes(vote_id, position);
CREATE INDEX CONCURRENTLY idx_politicians_party_state ON politicians(party, state);
CREATE INDEX CONCURRENTLY idx_documents_source_type ON documents(source_id, document_type);
CREATE INDEX CONCURRENTLY idx_documents_date_processed ON documents(date_ingested, processed);
CREATE INDEX CONCURRENTLY idx_bills_subjects_gin ON bills USING gin(subjects);
CREATE INDEX CONCURRENTLY idx_politicians_committees_gin ON politicians USING gin(committee_memberships);
*/