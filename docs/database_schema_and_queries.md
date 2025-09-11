# Database Schema and Query Mapping

This document provides a comprehensive overview of the database schema, relationships between tables, and sample queries for analyzing government data.

## Table Relationships

### 1. Congress Members and Roles (Membership Tracking)
- **Relationship**: One-to-Many
- **Foreign Key**: `congress_member_roles.member_id` → `congress_members.id`
- **Description**: Each member can have multiple roles over time (e.g., House then Senate)

### 2. Congress Bills and Related Entities
- **Bills to Actions**: One-to-Many
  - Foreign Key: `congress_bill_actions.bill_id` → `congress_bills.id`
  - Description: Each bill can have multiple actions throughout its lifecycle
  
- **Bills to Subjects**: One-to-Many
  - Foreign Key: `congress_bill_subjects.bill_id` → `congress_bills.id`
  - Description: Each bill can have multiple subjects
  
- **Bills to Cosponsors**: One-to-Many
  - Foreign Key: `congress_bill_cosponsors.bill_id` → `congress_bills.id`
  - Description: Each bill can have multiple cosponsors

### 3. GovInfo Collections and Packages
- **Collections to Packages**: One-to-Many
  - Foreign Key: `govinfo_packages.collection_id` → `govinfo_collections.id`
  - Description: Each collection contains multiple packages

### 4. API Keys and Logging
- **API Keys to Logs**: One-to-Many
  - Foreign Key: `api_call_logs.api_key_id` → `api_keys.id`
  - Description: Each API key can have multiple call logs

## Key Queries

### Individual Politician Level Analysis

#### 1. Find all bills sponsored by a specific politician
```sql
SELECT 
    cb.bill_id,
    cb.title,
    cb.introduced_date,
    cb.sponsor_name,
    cb.sponsor_party,
    cb.sponsor_state
FROM congress_bills cb
WHERE cb.sponsor_id = :politician_id
ORDER BY cb.introduced_date DESC;
```

#### 2. Find all cosponsored bills by a specific politician
```sql
SELECT 
    cb.bill_id,
    cb.title,
    cbc.date_cosponsored,
    cbc.party,
    cbc.state
FROM congress_bill_cosponsors cbc
JOIN congress_bills cb ON cbc.bill_id = cb.id
WHERE cbc.bioguide_id = :politician_id
ORDER BY cbc.date_cosponsored DESC;
```

#### 3. Get detailed information about a politician's roles
```sql
SELECT 
    cm.first_name,
    cm.last_name,
    cm.party,
    cmr.congress,
    cmr.chamber,
    cmr.title,
    cmr.state,
    cmr.start_date,
    cmr.end_date
FROM congress_members cm
JOIN congress_member_roles cmr ON cm.id = cmr.member_id
WHERE cm.member_id = :politician_id
ORDER BY cmr.start_date DESC;
```

### Government Level Analysis

#### 1. Count bills by congress and chamber
```sql
SELECT 
    congress,
    bill_type,
    COUNT(*) as bill_count
FROM congress_bills
GROUP BY congress, bill_type
ORDER BY congress DESC, bill_type;
```

#### 2. Find the most active sponsors
```sql
SELECT 
    sponsor_name,
    sponsor_party,
    sponsor_state,
    COUNT(*) as bills_sponsored
FROM congress_bills
GROUP BY sponsor_name, sponsor_party, sponsor_state
ORDER BY bills_sponsored DESC
LIMIT 20;
```

#### 3. Analyze bill subjects across congresses
```sql
SELECT 
    cbs.subject,
    COUNT(*) as subject_count,
    AVG(cb.congress) as avg_congress
FROM congress_bill_subjects cbs
JOIN congress_bills cb ON cbs.bill_id = cb.id
GROUP BY cbs.subject
ORDER BY subject_count DESC
LIMIT 50;
```

### Time Range Analysis

#### 1. Bills introduced in a specific time range
```sql
SELECT 
    bill_id,
    title,
    introduced_date,
    sponsor_name
FROM congress_bills
WHERE introduced_date BETWEEN :start_date AND :end_date
ORDER BY introduced_date DESC;
```

#### 2. Legislative activity by year
```sql
SELECT 
    EXTRACT(YEAR FROM introduced_date) as year,
    COUNT(*) as bills_introduced,
    COUNT(CASE WHEN enacted = true THEN 1 END) as bills_enacted
FROM congress_bills
WHERE introduced_date IS NOT NULL
GROUP BY EXTRACT(YEAR FROM introduced_date)
ORDER BY year DESC;
```

#### 3. Politician tenure by decade
```sql
SELECT 
    FLOOR(EXTRACT(YEAR FROM cmr.start_date)/10)*10 as decade,
    COUNT(DISTINCT cm.member_id) as politicians,
    COUNT(*) as roles
FROM congress_member_roles cmr
JOIN congress_members cm ON cmr.member_id = cm.id
WHERE cmr.start_date IS NOT NULL
GROUP BY decade
ORDER BY decade DESC;
```

### Membership Tracking

#### 1. Track a politician's membership over time
```sql
SELECT 
    cm.first_name,
    cm.last_name,
    cmr.congress,
    cmr.chamber,
    cmr.title,
    cmr.state,
    cmr.party,
    cmr.start_date,
    cmr.end_date,
    CASE 
        WHEN cmr.end_date IS NULL THEN 'Current'
        ELSE 'Former'
    END as status
FROM congress_members cm
JOIN congress_member_roles cmr ON cm.id = cmr.member_id
WHERE cm.member_id = :politician_id
ORDER BY cmr.start_date ASC;
```

#### 2. Find all politicians who served in a specific congress
```sql
SELECT 
    cm.first_name,
    cm.last_name,
    cmr.chamber,
    cmr.state,
    cmr.party,
    cmr.title,
    cmr.start_date,
    cmr.end_date
FROM congress_member_roles cmr
JOIN congress_members cm ON cmr.member_id = cm.id
WHERE cmr.congress = :congress_number
ORDER BY cmr.chamber, cmr.state, cm.last_name, cm.first_name;
```

#### 3. Analyze party composition over time
```sql
SELECT 
    congress,
    party,
    COUNT(*) as member_count
FROM congress_member_roles
WHERE party IN ('D', 'R')
GROUP BY congress, party
ORDER BY congress, party;
```

### GovInfo Document Analysis

#### 1. Find documents by collection type
```sql
SELECT 
    package_id,
    title,
    collection_code,
    document_type,
    publication_date
FROM govinfo_documents
WHERE collection_code = :collection_code
ORDER BY publication_date DESC;
```

#### 2. Search documents by keyword
```sql
SELECT 
    package_id,
    title,
    collection_code,
    publication_date
FROM govinfo_documents
WHERE title ILIKE '%:keyword%'
   OR content ILIKE '%:keyword%'
ORDER BY publication_date DESC;
```

## Indexing Strategy

The following indexes have been created for improved query performance:

1. **Congress Members**:
   - `idx_congress_members_party` - For filtering by party
   - `idx_congress_members_state` - For filtering by state
   - `idx_congress_members_last_name` - For name-based searches

2. **Congress Member Roles**:
   - `idx_congress_member_roles_party` - For party analysis
   - `idx_congress_member_roles_state` - For state-based analysis
   - `idx_congress_member_roles_congress` - For congress-based queries
   - `idx_congress_member_roles_chamber` - For chamber-based analysis
   - `idx_congress_member_roles_dates` - For date range queries

3. **Congress Bills**:
   - `idx_congress_bills_sponsor_party` - For sponsor party analysis
   - `idx_congress_bills_sponsor_state` - For sponsor state analysis
   - `idx_congress_bills_congress` - For congress-based queries
   - `idx_congress_bills_introduced_date` - For date-based queries
   - `idx_congress_bills_enacted` - For enacted bill queries

4. **GovInfo Documents**:
   - `idx_govinfo_documents_collection` - For collection-based queries
   - `idx_govinfo_documents_branch` - For branch-based queries
   - `idx_govinfo_documents_document_type` - For document type queries
   - `idx_govinfo_documents_publication_date` - For date-based queries

These indexes significantly improve query performance for the most common analysis patterns in government data.