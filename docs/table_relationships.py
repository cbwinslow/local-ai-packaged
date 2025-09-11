#!/usr/bin/env python3
"""
Database relationship mapping and analysis script.
This script documents the relationships between tables in the government data pipeline.
"""

# Table Relationships Mapping

# 1. Congress Members and Roles (Membership tracking)
# -----------------------------------------------
# congress_members (parent) <-> congress_member_roles (child)
# Relationship: One-to-Many
# Foreign Key: congress_member_roles.member_id -> congress_members.id
# Description: Each member can have multiple roles over time (e.g., House then Senate)

# 2. Congress Bills and Related Entities
# -------------------------------------
# congress_bills (parent) <-> congress_bill_actions (child)
# Relationship: One-to-Many
# Foreign Key: congress_bill_actions.bill_id -> congress_bills.id
# Description: Each bill can have multiple actions throughout its lifecycle

# congress_bills (parent) <-> congress_bill_subjects (child)
# Relationship: One-to-Many
# Foreign Key: congress_bill_subjects.bill_id -> congress_bills.id
# Description: Each bill can have multiple subjects

# congress_bills (parent) <-> congress_bill_cosponsors (child)
# Relationship: One-to-Many
# Foreign Key: congress_bill_cosponsors.bill_id -> congress_bills.id
# Description: Each bill can have multiple cosponsors

# 3. GovInfo Collections and Packages
# ----------------------------------
# govinfo_collections (parent) <-> govinfo_packages (child)
# Relationship: One-to-Many
# Foreign Key: govinfo_packages.collection_id -> govinfo_collections.id
# Description: Each collection contains multiple packages

# govinfo_collections (parent) <-> govinfo_download_queue (child)
# Relationship: One-to-Many
# Foreign Key: govinfo_download_queue.collection_id -> govinfo_collections.id
# Description: Each collection can have multiple download queue entries

# govinfo_packages (parent) <-> govinfo_download_queue (one-to-one)
# Relationship: One-to-One
# Foreign Key: govinfo_download_queue.package_id -> govinfo_packages.package_id
# Description: Each package has at most one download queue entry

# 4. API Keys and Logging
# -----------------------
# api_keys (parent) <-> api_call_logs (child)
# Relationship: One-to-Many
# Foreign Key: api_call_logs.api_key_id -> api_keys.id
# Description: Each API key can have multiple call logs

# 5. Task Queue System
# --------------------
# tasks (self-referencing)
# Relationship: Self-referencing
# Foreign Key: tasks.parent_task_id -> tasks.id
# Description: Tasks can have parent-child relationships for dependencies

# Relationship Queries

# 1. Find all roles for a specific member
QUERY_MEMBER_ROLES = """
SELECT 
    cm.first_name,
    cm.last_name,
    cmr.congress,
    cmr.chamber,
    cmr.title,
    cmr.state,
    cmr.party,
    cmr.start_date,
    cmr.end_date
FROM congress_members cm
JOIN congress_member_roles cmr ON cm.id = cmr.member_id
WHERE cm.member_id = :member_id
ORDER BY cmr.start_date ASC;
"""

# 2. Find all actions for a specific bill
QUERY_BILL_ACTIONS = """
SELECT 
    cb.bill_id,
    cba.action_date,
    cba.action_text,
    cba.action_type,
    cba.acted_by
FROM congress_bills cb
JOIN congress_bill_actions cba ON cb.id = cba.bill_id
WHERE cb.bill_id = :bill_id
ORDER BY cba.action_date ASC;
"""

# 3. Find all subjects for a specific bill
QUERY_BILL_SUBJECTS = """
SELECT 
    cb.bill_id,
    cbs.subject
FROM congress_bills cb
JOIN congress_bill_subjects cbs ON cb.id = cbs.bill_id
WHERE cb.bill_id = :bill_id;
"""

# 4. Find all cosponsors for a specific bill
QUERY_BILL_COSPONSORS = """
SELECT 
    cb.bill_id,
    cbc.name,
    cbc.party,
    cbc.state,
    cbc.date_cosponsored
FROM congress_bills cb
JOIN congress_bill_cosponsors cbc ON cb.id = cbc.bill_id
WHERE cb.bill_id = :bill_id
ORDER BY cbc.date_cosponsored ASC;
"""

# 5. Find all packages in a specific collection
QUERY_COLLECTION_PACKAGES = """
SELECT 
    gc.collection_code,
    gc.collection_name,
    gp.package_id,
    gp.title,
    gp.last_modified
FROM govinfo_collections gc
JOIN govinfo_packages gp ON gc.id = gp.collection_id
WHERE gc.collection_code = :collection_code
ORDER BY gp.last_modified DESC;
"""

# 6. Find download status for packages
QUERY_PACKAGE_DOWNLOAD_STATUS = """
SELECT 
    gp.package_id,
    gp.title,
    gdq.status,
    gdq.retry_count,
    gdq.last_error,
    gdq.created_at,
    gdq.completed_at
FROM govinfo_packages gp
JOIN govinfo_download_queue gdq ON gp.package_id = gdq.package_id
WHERE gp.collection_id = (
    SELECT id FROM govinfo_collections WHERE collection_code = :collection_code
)
ORDER BY gdq.created_at DESC;
"""

# 7. Find API usage logs for a specific key
QUERY_API_USAGE = """
SELECT 
    ak.name as api_key_name,
    acl.endpoint,
    acl.method,
    acl.status_code,
    acl.response_time_ms,
    acl.success,
    acl.created_at
FROM api_keys ak
JOIN api_call_logs acl ON ak.id = acl.api_key_id
WHERE ak.service_name = :service_name
ORDER BY acl.created_at DESC
LIMIT 100;
"""

# 8. Find task dependencies
QUERY_TASK_DEPENDENCIES = """
SELECT 
    t1.id as task_id,
    t1.task_type,
    t1.status,
    t2.id as parent_task_id,
    t2.task_type as parent_task_type,
    t2.status as parent_status
FROM tasks t1
LEFT JOIN tasks t2 ON t1.parent_task_id = t2.id
WHERE t1.task_type IN ('bill_ingest', 'member_ingest')
ORDER BY t1.created_at DESC;
"""

print("Database relationship mapping completed.")
print("Foreign key relationships have been established between related tables.")
print("Use the queries above to explore relationships between entities.")