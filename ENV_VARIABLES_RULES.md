# Environment Variables Rules and Validation

This document defines the rules for generating, validating, and managing all environment variables required for the Local AI Package deployment.

## Table of Contents
- [Core Application Configuration](#core-application-configuration)
- [Supabase Configuration](#supabase-configuration)
- [Authentication](#authentication)
- [Database](#database)
- [AI/ML Services](#aiml-services)
- [Vector Databases](#vector-databases)
- [Monitoring & Observability](#monitoring--observability)
- [External Services](#external-services)
- [Security](#security)
- [Feature Flags](#feature-flags)
- [Service-Specific Secrets](#service-specific-secrets)
- [Validation Functions](#validation-functions)

## Core Application Configuration

### NODE_ENV
- **Required**: No (defaults to development)
- **Type**: String
- **Allowed Values**: development, production, test
- **Generation**: Manual or default
- **Validation**: Must be one of allowed values
- **Default**: development

### PORT
- **Required**: No (defaults to 3000)
- **Type**: Integer
- **Range**: 1024-65535
- **Generation**: Manual
- **Validation**: Must be valid port number
- **Default**: 3000

## Supabase Configuration

### NEXT_PUBLIC_SUPABASE_URL
- **Required**: Yes
- **Type**: URL
- **Format**: https://hostname or http://localhost:port
- **Generation**: Manual (based on deployment)
- **Validation**: Must be valid URL format
- **Example**: http://localhost:5432

### NEXT_PUBLIC_SUPABASE_ANON_KEY
- **Required**: Yes
- **Type**: JWT Token
- **Generation**: `openssl rand -hex 32` + JWT signing
- **Validation**: Must be valid JWT format, length >= 32 chars
- **Security**: High - public key for client-side auth

### SUPABASE_SERVICE_ROLE_KEY
- **Required**: Yes
- **Type**: JWT Token
- **Generation**: `openssl rand -hex 32` + JWT signing
- **Validation**: Must be valid JWT format, length >= 32 chars
- **Security**: Critical - server-side admin key

## Authentication

### JWT_SECRET
- **Required**: Yes
- **Type**: Hex String
- **Length**: 32 characters
- **Generation**: `openssl rand -hex 32`
- **Validation**: Must be 64 hex characters (32 bytes)
- **Security**: Critical - used for JWT signing

### NEXTAUTH_SECRET
- **Required**: Yes
- **Type**: Hex String
- **Length**: 32 characters
- **Generation**: `openssl rand -hex 32`
- **Validation**: Must be 64 hex characters (32 bytes)
- **Security**: High - NextAuth.js session encryption

### NEXTAUTH_URL
- **Required**: Yes
- **Type**: URL
- **Format**: http://hostname:port or https://hostname
- **Generation**: Manual
- **Validation**: Must be valid URL
- **Default**: http://localhost:3000

## Database

### DATABASE_URL
- **Required**: No
- **Type**: PostgreSQL Connection String
- **Format**: postgresql://user:password@host:port/database
- **Generation**: Constructed from POSTGRES_* variables
- **Validation**: Must match PostgreSQL URL format
- **Example**: postgresql://user:password@localhost:5432/yourdb

### POSTGRES_PASSWORD
- **Required**: Yes
- **Type**: Base64 String (filtered)
- **Length**: 24+ characters
- **Generation**: `openssl rand -base64 32 | tr -d '/+= '`
- **Validation**: No special characters that break URLs
- **Security**: High - database access

### POSTGRES_VERSION
- **Required**: No
- **Type**: String
- **Allowed Values**: 16-alpine, 15-alpine, etc.
- **Generation**: Manual
- **Validation**: Must be valid PostgreSQL version tag
- **Default**: 16-alpine

### POSTGRES_HOST
- **Required**: No
- **Type**: String
- **Generation**: Manual
- **Validation**: Valid hostname
- **Default**: db

### POSTGRES_DB
- **Required**: No
- **Type**: String
- **Generation**: Manual
- **Validation**: Valid database name
- **Default**: postgres

### POSTGRES_USER
- **Required**: No
- **Type**: String
- **Generation**: Manual
- **Validation**: Valid username
- **Default**: postgres

### POSTGRES_PORT
- **Required**: No
- **Type**: Integer
- **Generation**: Manual
- **Validation**: Valid port
- **Default**: 5432

## AI/ML Services

### OPENAI_API_KEY
- **Required**: No (optional)
- **Type**: String
- **Generation**: Manual (from OpenAI)
- **Validation**: Must start with 'sk-'
- **Security**: High - API access

### ANTHROPIC_API_KEY
- **Required**: No (optional)
- **Type**: String
- **Generation**: Manual (from Anthropic)
- **Validation**: Must start with 'sk-ant-'
- **Security**: High - API access

## Vector Databases

### QDRANT_URL
- **Required**: No
- **Type**: URL
- **Generation**: Manual
- **Validation**: Valid URL
- **Default**: http://localhost:6333

### QDRANT_API_KEY
- **Required**: No
- **Type**: String
- **Generation**: Manual or `openssl rand -hex 32`
- **Validation**: Length >= 32 if provided
- **Security**: Medium

## Monitoring & Observability

### GRAFANA_ADMIN_PASSWORD
- **Required**: No
- **Type**: Base64 String (filtered)
- **Generation**: `openssl rand -base64 24 | tr -d '/+= '`
- **Validation**: Length >= 12
- **Security**: Medium

### PROMETHEUS_PASSWORD
- **Required**: No
- **Type**: Base64 String (filtered)
- **Generation**: `openssl rand -base64 24 | tr -d '/+= '`
- **Validation**: Length >= 12
- **Security**: Medium

## External Services

### LINEAR_API_KEY
- **Required**: No
- **Type**: String
- **Generation**: Manual (from Linear)
- **Validation**: Must start with 'lin_api_'
- **Security**: High

### GITHUB_TOKEN
- **Required**: No
- **Type**: String
- **Generation**: Manual (from GitHub)
- **Validation**: Must start with 'ghp_' or 'github_pat_'
- **Security**: High

## Security

### ENCRYPTION_KEY
- **Required**: Yes
- **Type**: Hex String
- **Length**: 32 characters
- **Generation**: `openssl rand -hex 32`
- **Validation**: Must be 64 hex characters
- **Security**: Critical - general encryption

### CORS_ORIGIN
- **Required**: No
- **Type**: URL or wildcard
- **Generation**: Manual
- **Validation**: Valid URL or '*'
- **Default**: http://localhost:3000

## Feature Flags

### ENABLE_EXPERIMENTAL_FEATURES
- **Required**: No
- **Type**: Boolean
- **Generation**: Manual
- **Validation**: true/false
- **Default**: false

### ENABLE_ANALYTICS
- **Required**: No
- **Type**: Boolean
- **Generation**: Manual
- **Validation**: true/false
- **Default**: false

## Service-Specific Secrets

### N8N_ENCRYPTION_KEY
- **Required**: Yes
- **Type**: Hex String
- **Length**: 32 characters
- **Generation**: `openssl rand -hex 32`
- **Validation**: Must be 64 hex characters
- **Security**: High - N8N workflow encryption

### N8N_USER_MANAGEMENT_JWT_SECRET
- **Required**: Yes
- **Type**: Hex String
- **Length**: 32 characters
- **Generation**: `openssl rand -hex 32`
- **Validation**: Must be 64 hex characters
- **Security**: High - N8N user auth

### N8N_HOSTNAME
- **Required**: No
- **Type**: String
- **Generation**: Manual
- **Validation**: Valid hostname
- **Default**: localhost

### FLOWISE_USERNAME
- **Required**: No
- **Type**: Hex String
- **Length**: 8 characters
- **Generation**: `openssl rand -hex 8`
- **Validation**: Length >= 8
- **Security**: Medium

### FLOWISE_PASSWORD
- **Required**: No
- **Type**: Base64 String (filtered)
- **Generation**: `openssl rand -base64 24 | tr -d '/+= '`
- **Validation**: Length >= 12
- **Security**: Medium

### FLOWISE_HOSTNAME
- **Required**: No
- **Type**: String
- **Generation**: Manual
- **Validation**: Valid hostname
- **Default**: localhost

### WEBUI_HOSTNAME
- **Required**: No
- **Type**: String
- **Generation**: Manual
- **Validation**: Valid hostname
- **Default**: localhost

### LANGFUSE_SALT
- **Required**: Yes (for Langfuse)
- **Type**: Hex String
- **Length**: 32 characters
- **Generation**: `openssl rand -hex 32`
- **Validation**: Must be 64 hex characters
- **Security**: High - Langfuse encryption

### LANGFUSE_HOSTNAME
- **Required**: No
- **Type**: String
- **Generation**: Manual
- **Validation**: Valid hostname
- **Default**: localhost

### CLICKHOUSE_PASSWORD
- **Required**: Yes (for ClickHouse)
- **Type**: Base64 String (filtered)
- **Generation**: `openssl rand -base64 24 | tr -d '/+= '`
- **Validation**: Length >= 12
- **Security**: Medium

### MINIO_ROOT_PASSWORD
- **Required**: Yes (for MinIO)
- **Type**: Base64 String (filtered)
- **Generation**: `openssl rand -base64 24 | tr -d '/+= '`
- **Validation**: Length >= 12
- **Security**: High - MinIO admin

### SEARXNG_HOSTNAME
- **Required**: No
- **Type**: String
- **Generation**: Manual
- **Validation**: Valid hostname
- **Default**: localhost

### SEARXNG_UWSGI_WORKERS
- **Required**: No
- **Type**: Integer
- **Range**: 1-16
- **Generation**: Manual
- **Validation**: Must be positive integer
- **Default**: 4

### SEARXNG_UWSGI_THREADS
- **Required**: No
- **Type**: Integer
- **Range**: 1-16
- **Generation**: Manual
- **Validation**: Must be positive integer
- **Default**: 4

### AGENTIC_HOSTNAME
- **Required**: No
- **Type**: String
- **Generation**: Manual
- **Validation**: Valid hostname
- **Default**: localhost

### NEO4J_URI
- **Required**: No
- **Type**: Neo4j URI
- **Format**: bolt://host:port
- **Generation**: Manual
- **Validation**: Must match bolt:// format
- **Default**: bolt://localhost:7687

### NEO4J_AUTH
- **Required**: Yes (for Neo4j)
- **Type**: Neo4j Auth String
- **Format**: username/password
- **Generation**: neo4j/${NEO4J_PASSWORD}
- **Validation**: Must contain '/'
- **Security**: Medium

### FRONTEND_HOSTNAME
- **Required**: No
- **Type**: String
- **Generation**: Manual
- **Validation**: Valid hostname
- **Default**: localhost

### SUPABASE_HOSTNAME
- **Required**: No
- **Type**: String
- **Generation**: Manual
- **Validation**: Valid hostname
- **Default**: localhost

### ANON_KEY
- **Required**: Yes
- **Type**: JWT Token
- **Generation**: JWT signing with JWT_SECRET
- **Validation**: Valid JWT format
- **Security**: High

### SERVICE_ROLE_KEY
- **Required**: Yes
- **Type**: JWT Token
- **Generation**: JWT signing with JWT_SECRET
- **Validation**: Valid JWT format
- **Security**: Critical

### DASHBOARD_USERNAME
- **Required**: Yes
- **Type**: Hex String
- **Length**: 8 characters
- **Generation**: `openssl rand -hex 8`
- **Validation**: Length >= 8
- **Security**: Medium

### DASHBOARD_PASSWORD
- **Required**: Yes
- **Type**: Base64 String (filtered)
- **Generation**: `openssl rand -base64 24 | tr -d '/+= '`
- **Validation**: Length >= 12
- **Security**: Medium

### POOLER_TENANT_ID
- **Required**: Yes
- **Type**: Integer
- **Range**: 1000-9999
- **Generation**: `shuf -i 1000-9999 -n 1`
- **Validation**: Must be 4-digit number
- **Security**: Low

### SECRET_KEY_BASE
- **Required**: Yes
- **Type**: Hex String
- **Length**: 64 characters
- **Generation**: `openssl rand -hex 64`
- **Validation**: Must be 128 hex characters
- **Security**: Critical

### VAULT_ENC_KEY
- **Required**: Yes
- **Type**: Hex String
- **Length**: 32 characters
- **Generation**: `openssl rand -hex 32`
- **Validation**: Must be 64 hex characters
- **Security**: Critical

### POOLER_DB_POOL_SIZE
- **Required**: Yes
- **Type**: Integer
- **Generation**: Manual
- **Validation**: Must be positive integer
- **Default**: 5

### LOGFLARE_PUBLIC_ACCESS_TOKEN
- **Required**: No
- **Type**: Hex String
- **Length**: 32 characters
- **Generation**: `openssl rand -hex 32`
- **Validation**: Must be 64 hex characters
- **Security**: Medium

### LOGFLARE_PRIVATE_ACCESS_TOKEN
- **Required**: No
- **Type**: Hex String
- **Length**: 32 characters
- **Generation**: `openssl rand -hex 32`
- **Validation**: Must be 64 hex characters
- **Security**: Medium

### GRAYLOG_PASSWORD_SECRET
- **Required**: No
- **Type**: String
- **Generation**: Manual or random
- **Validation**: Length >= 32
- **Security**: Medium

### GRAYLOG_PASSWORD
- **Required**: No
- **Type**: Base64 String (filtered)
- **Generation**: `openssl rand -base64 24 | tr -d '/+= '`
- **Validation**: Length >= 12
- **Security**: Medium

### OPENSEARCH_HOSTS
- **Required**: No
- **Type**: JSON Array
- **Format**: ["http://host:port"]
- **Generation**: Manual
- **Validation**: Valid JSON array of URLs
- **Default**: ["http://opensearch:9200"]

### RABBITMQ_USER
- **Required**: No
- **Type**: Hex String
- **Length**: 8 characters
- **Generation**: `openssl rand -hex 8`
- **Validation**: Length >= 8
- **Security**: Medium

### RABBITMQ_PASS
- **Required**: No
- **Type**: Base64 String (filtered)
- **Generation**: `openssl rand -base64 24 | tr -d '/+= '`
- **Validation**: Length >= 12
- **Security**: Medium

### LOCALAI_API_KEY
- **Required**: No
- **Type**: Hex String
- **Length**: 32 characters
- **Generation**: `openssl rand -hex 32`
- **Validation**: Must be 64 hex characters
- **Security**: Medium

## Validation Functions

### validate_hex_string
```bash
validate_hex_string() {
    local value="$1"
    local min_length="${2:-32}"
    if [[ ! "$value" =~ ^[0-9a-fA-F]+$ ]] || [[ ${#value} -lt $min_length ]]; then
        echo "❌ Invalid hex string: must be at least $min_length hex characters"
        return 1
    fi
    return 0
}
```

### validate_base64_filtered
```bash
validate_base64_filtered() {
    local value="$1"
    local min_length="${2:-12}"
    if [[ ${#value} -lt $min_length ]] || [[ "$value" =~ [/+] ]]; then
        echo "❌ Invalid filtered base64: must be at least $min_length chars, no / or +"
        return 1
    fi
    return 0
}
```

### validate_url
```bash
validate_url() {
    local value="$1"
    if [[ ! "$value" =~ ^https?:// ]]; then
        echo "❌ Invalid URL: must start with http:// or https://"
        return 1
    fi
    return 0
}
```

### validate_jwt
```bash
validate_jwt() {
    local value="$1"
    local parts
    IFS='.' read -ra parts <<< "$value"
    if [[ ${#parts[@]} -ne 3 ]]; then
        echo "❌ Invalid JWT: must have 3 parts separated by dots"
        return 1
    fi
    return 0
}
```

### validate_port
```bash
validate_port() {
    local value="$1"
    if ! [[ "$value" =~ ^[0-9]+$ ]] || [[ "$value" -lt 1024 ]] || [[ "$value" -gt 65535 ]]; then
        echo "❌ Invalid port: must be between 1024 and 65535"
        return 1
    fi
    return 0
}
```

## Generation Priority

1. **Critical Security Keys** (generate first):
   - JWT_SECRET
   - ENCRYPTION_KEY
   - SECRET_KEY_BASE
   - VAULT_ENC_KEY

2. **Service-Specific Keys**:
   - N8N_ENCRYPTION_KEY, N8N_USER_MANAGEMENT_JWT_SECRET
   - LANGFUSE_SALT
   - NEXTAUTH_SECRET

3. **Passwords**:
   - POSTGRES_PASSWORD
   - CLICKHOUSE_PASSWORD
   - MINIO_ROOT_PASSWORD
   - All user passwords

4. **JWT Tokens** (generate last, depend on JWT_SECRET):
   - ANON_KEY
   - SERVICE_ROLE_KEY

## Security Classification

- **Critical**: Keys that can compromise the entire system if leaked
- **High**: Keys that can access sensitive services or data
- **Medium**: Keys for user authentication or service access
- **Low**: Configuration values with minimal security impact</content>