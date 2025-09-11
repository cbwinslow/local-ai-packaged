# Government Data Analysis Queries

This document contains SQL queries for analyzing government data, including individual politician level analysis, government level analysis, time range analysis, and membership tracking.

## Individual Politician Level Analysis

### Query 1: Find all bills sponsored by a specific politician
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

### Query 2: Find all votes by a specific politician
```sql
SELECT 
    cb.bill_id,
    cb.title,
    cbc.position,
    cbc.date
FROM congress_bill_cosponsors cbc
JOIN congress_bills cb ON cbc.bill_id = cb.id
WHERE cbc.bioguide_id = :politician_id
ORDER BY cbc.date DESC;
```

### Query 3: Get detailed information about a politician's roles
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

## Government Level Analysis

### Query 1: Count bills by congress and chamber
```sql
SELECT 
    congress,
    bill_type,
    COUNT(*) as bill_count
FROM congress_bills
GROUP BY congress, bill_type
ORDER BY congress DESC, bill_type;
```

### Query 2: Find the most active sponsors
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

### Query 3: Analyze bill subjects across congresses
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

## Time Range Analysis

### Query 1: Bills introduced in a specific time range
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

### Query 2: Legislative activity by year
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

### Query 3: Politician tenure by decade
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

## Membership Tracking

### Query 1: Track a politician's membership over time
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

### Query 2: Find all politicians who served in a specific congress
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

### Query 3: Analyze party composition over time
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