# Comprehensive Rules for Coding Models in Local AI Package Project

## Overview

This document establishes **MANDATORY rules that ALL coding models MUST adhere to BEFORE and AFTER every single action they undertake** in the Local AI Package repository. These rules ensure uniform, secure, and reliable execution of critical operations including `.env` file creation, secrets generation, and Docker Compose stack launching.

**CRITICAL: Every coding agent must validate compliance with these rules for every action, no exceptions.**

## General Principles

### Rule 1: Mandatory Pre-Action Validation
**ALL coding models MUST perform comprehensive validation BEFORE executing ANY action.**

- **Check 1.1**: Verify all required dependencies are installed and accessible
- **Check 1.2**: Confirm system meets minimum resource requirements
- **Check 1.3**: Validate that no conflicting processes or services are running
- **Check 1.4**: Ensure proper file permissions and ownership
- **Check 1.5**: Verify network connectivity if required
- **Check 1.6**: **MANDATORY**: Confirm compliance with all relevant rules before proceeding

### Rule 2: Mandatory Post-Action Validation
**ALL coding models MUST perform thorough validation AFTER completing ANY action.**

- **Check 2.1**: Confirm the action completed successfully without errors
- **Check 2.2**: Validate that all expected outputs/files were created correctly
- **Check 2.3**: Verify that services are running and accessible if applicable
- **Check 2.4**: Check for any side effects or conflicts introduced
- **Check 2.5**: Ensure proper cleanup of temporary files and resources
- **Check 2.6**: **MANDATORY**: Re-validate system state and rule compliance

### Rule 3: Universal Action Protocol
**ALL coding models MUST follow this protocol for EVERY action:**

#### Pre-Action (MANDATORY):
- **Check 3.1**: Identify which rules apply to the intended action
- **Check 3.2**: Execute all pre-action checks for those rules
- **Check 3.3**: Document the action intent and expected outcomes
- **Check 3.4**: Obtain explicit confirmation that all checks passed

#### Action Execution (MANDATORY):
- **Check 3.5**: Execute the action following established patterns
- **Check 3.6**: Monitor for immediate errors or warnings
- **Check 3.7**: Log all steps and decisions made

#### Post-Action (MANDATORY):
- **Check 3.8**: Execute all post-action checks for applicable rules
- **Check 3.9**: Verify the action achieved its intended outcomes
- **Check 3.10**: Document any deviations or issues encountered
- **Check 3.11**: Confirm system remains in stable state

### Rule 4: Error Handling and Recovery
**ALL coding models MUST implement robust error handling for EVERY action.**

- **Check 4.1**: Immediately halt execution on any error condition
- **Check 4.2**: Provide clear, actionable error messages
- **Check 4.3**: Attempt automatic recovery where possible
- **Check 4.4**: Log all errors with sufficient context for debugging
- **Check 4.5**: Never proceed with subsequent actions if pre-conditions fail
- **Check 4.6**: **MANDATORY**: Report rule violations immediately

### Rule 5: Security First
**ALL coding models MUST prioritize security in ALL operations.**

- **Check 5.1**: Use cryptographically secure random generation for all secrets
- **Check 5.2**: Set restrictive file permissions (600) on sensitive files
- **Check 5.3**: Never log or display secret values in output
- **Check 5.4**: Implement proper backup procedures before destructive operations
- **Check 5.5**: Validate secret formats and requirements
- **Check 5.6**: **MANDATORY**: Security checks apply to every action involving sensitive data

## Service-Specific Rules

### Rule 19: Password Creation Standards
**ALL coding models MUST generate passwords according to established security standards for each service.**

#### General Password Requirements (MANDATORY):
- **Check 19.1**: Minimum length of 24 characters for critical services (databases, auth systems)
- **Check 19.2**: Minimum length of 16 characters for application services
- **Check 19.3**: Use cryptographically secure random generation (openssl rand)
- **Check 19.4**: Include uppercase, lowercase, numbers, and special characters
- **Check 19.5**: Avoid predictable patterns or dictionary words
- **Check 19.6**: Generate unique passwords for each service
- **Check 19.7**: Never reuse passwords across different services

#### Service-Specific Password Rules (MANDATORY):
- **Check 19.8**: PostgreSQL passwords: 32+ characters, base64 encoded
- **Check 19.9**: JWT secrets: 256-bit (32 bytes) hex or base64
- **Check 19.10**: Encryption keys: 256-bit (32 bytes) minimum
- **Check 19.11**: API keys: 32+ characters, URL-safe encoding
- **Check 19.12**: Dashboard credentials: 24+ characters with complexity

### Rule 20: PostgreSQL Database Service
**ALL coding models MUST properly configure PostgreSQL secrets and validate deployment.**

#### Pre-Action Checks (MANDATORY):
- **Check 20.1**: Verify POSTGRES_PASSWORD is set and 32+ characters
- **Check 20.2**: Confirm POSTGRES_VERSION is specified (default: 16-alpine)
- **Check 20.3**: Ensure volume mount path exists and is writable
- **Check 20.4**: Validate health check configuration

#### Secret Generation (MANDATORY):
- **Check 20.5**: Generate POSTGRES_PASSWORD using openssl rand -base64 32
- **Check 20.6**: Store password securely in .env with 600 permissions
- **Check 20.7**: Include password in DATABASE_URL construction

#### Post-Action Validation (MANDATORY):
- **Check 20.8**: Verify PostgreSQL accepts connections on port 5432
- **Check 20.9**: Test database creation and user authentication
- **Check 20.10**: Confirm health check passes (pg_isready)
- **Check 20.11**: Validate data persistence across container restarts

#### Dependencies and Failure Points:
- **Check 20.12**: Required by: N8N, Langfuse, Frontend, Agentic-RAG
- **Check 20.13**: Failure points: Port 5432 conflicts, insufficient disk space, corrupted volumes

### Rule 21: N8N Workflow Automation Service
**ALL coding models MUST ensure N8N secrets are properly generated and configured.**

#### Pre-Action Checks (MANDATORY):
- **Check 21.1**: Verify POSTGRES_PASSWORD is available for database connection
- **Check 21.2**: Confirm N8N_ENCRYPTION_KEY is 32 bytes hex
- **Check 21.3**: Validate N8N_USER_MANAGEMENT_JWT_SECRET is 32 bytes hex
- **Check 21.4**: Check N8N_HOSTNAME is set for webhook URLs

#### Secret Generation (MANDATORY):
- **Check 21.5**: Generate N8N_ENCRYPTION_KEY: openssl rand -hex 32
- **Check 21.6**: Generate N8N_USER_MANAGEMENT_JWT_SECRET: openssl rand -hex 32
- **Check 21.7**: Set N8N_HOSTNAME to appropriate domain (default: localhost)

#### Post-Action Validation (MANDATORY):
- **Check 21.8**: Verify N8N accessible on port 5678
- **Check 21.9**: Test database connectivity and schema creation
- **Check 21.10**: Confirm encryption key functionality
- **Check 21.11**: Validate JWT token generation for user management

#### Dependencies and Failure Points:
- **Check 21.12**: Depends on: PostgreSQL, N8N-import completion
- **Check 21.13**: Failure points: Database connection issues, invalid encryption keys, port conflicts

### Rule 22: Supabase Services
**ALL coding models MUST properly configure all Supabase-related secrets and JWT tokens.**

#### Pre-Action Checks (MANDATORY):
- **Check 22.1**: Verify POSTGRES_PASSWORD for database access
- **Check 22.2**: Confirm JWT_SECRET is 256-bit for token signing
- **Check 22.3**: Validate DASHBOARD_USERNAME and DASHBOARD_PASSWORD are set
- **Check 22.4**: Check POOLER_TENANT_ID is numeric (1000-9999)

#### Secret Generation (MANDATORY):
- **Check 22.5**: Generate JWT_SECRET: openssl rand -hex 32
- **Check 22.6**: Generate ANON_KEY and SERVICE_ROLE_KEY using JWT_SECRET
- **Check 22.7**: Create DASHBOARD_USERNAME: alphanumeric, 12 characters
- **Check 22.8**: Create DASHBOARD_PASSWORD: 24+ characters with complexity
- **Check 22.9**: Generate POOLER_TENANT_ID: random number 1000-9999
- **Check 22.10**: Create SECRET_KEY_BASE: 64 bytes hex
- **Check 22.11**: Generate VAULT_ENC_KEY: 32 bytes hex

#### Post-Action Validation (MANDATORY):
- **Check 22.12**: Verify Supabase API responds on port 8000
- **Check 22.13**: Test JWT token validation with ANON_KEY
- **Check 22.14**: Confirm dashboard login with generated credentials
- **Check 22.15**: Validate connection pooler functionality
- **Check 22.16**: Test authentication and authorization flows

#### Dependencies and Failure Points:
- **Check 22.17**: Depends on: PostgreSQL healthy state
- **Check 22.18**: Failure points: Invalid JWT tokens, database schema issues, port conflicts

### Rule 23: Langfuse Observability Service
**ALL coding models MUST configure Langfuse with proper secrets and S3 integration.**

#### Pre-Action Checks (MANDATORY):
- **Check 23.1**: Verify PostgreSQL, MinIO, Redis, ClickHouse are healthy
- **Check 23.2**: Confirm NEXTAUTH_SECRET is 32 bytes hex
- **Check 23.3**: Validate LANGFUSE_SALT is 32 bytes hex
- **Check 23.4**: Check ENCRYPTION_KEY is 32 bytes hex

#### Secret Generation (MANDATORY):
- **Check 23.5**: Generate NEXTAUTH_SECRET: openssl rand -hex 32
- **Check 23.6**: Generate LANGFUSE_SALT: openssl rand -hex 32
- **Check 23.7**: Create ENCRYPTION_KEY: openssl rand -hex 32
- **Check 23.8**: Configure S3 credentials using MINIO_ROOT_PASSWORD

#### Post-Action Validation (MANDATORY):
- **Check 23.9**: Verify Langfuse web interface on port 3002
- **Check 23.10**: Test S3 upload/download functionality
- **Check 23.11**: Confirm ClickHouse data ingestion
- **Check 23.12**: Validate authentication with NextAuth
- **Check 23.13**: Check Redis caching functionality

#### Dependencies and Failure Points:
- **Check 23.14**: Depends on: PostgreSQL, MinIO, Redis, ClickHouse
- **Check 23.15**: Failure points: S3 connectivity issues, database failures, invalid S3 credentials

### Rule 24: Neo4j Graph Database Service
**ALL coding models MUST properly configure Neo4j authentication.**

#### Pre-Action Checks (MANDATORY):
- **Check 24.1**: Verify NEO4J_PASSWORD meets complexity requirements
- **Check 24.2**: Confirm volume mounts are properly configured
- **Check 24.3**: Check plugin and config directories exist

#### Secret Generation (MANDATORY):
- **Check 24.4**: Generate NEO4J_PASSWORD: 24+ characters with complexity
- **Check 24.5**: Construct NEO4J_AUTH as "neo4j/{password}"

#### Post-Action Validation (MANDATORY):
- **Check 24.6**: Verify Neo4j browser accessible on port 7474
- **Check 24.7**: Test Bolt protocol connection on port 7687
- **Check 24.8**: Confirm authentication with generated credentials
- **Check 24.9**: Validate data persistence across restarts

#### Dependencies and Failure Points:
- **Check 24.10**: Required by: Agentic-RAG service
- **Check 24.11**: Failure points: Authentication failures, volume permission issues, port conflicts

### Rule 25: MinIO S3 Storage Service
**ALL coding models MUST configure MinIO with secure root credentials.**

#### Pre-Action Checks (MANDATORY):
- **Check 25.1**: Verify MINIO_ROOT_PASSWORD is 24+ characters
- **Check 25.2**: Confirm volume mount path is writable
- **Check 25.3**: Check bucket creation command in entrypoint

#### Secret Generation (MANDATORY):
- **Check 25.4**: Generate MINIO_ROOT_PASSWORD: openssl rand -base64 24
- **Check 25.5**: Use "minio" as default root username

#### Post-Action Validation (MANDATORY):
- **Check 25.6**: Verify MinIO console accessible on port 9001
- **Check 25.7**: Test API access on port 9000
- **Check 25.8**: Confirm bucket creation (langfuse)
- **Check 25.9**: Validate S3-compatible operations

#### Dependencies and Failure Points:
- **Check 25.10**: Required by: Langfuse S3 operations
- **Check 25.11**: Failure points: Volume permission issues, bucket creation failures

### Rule 26: ClickHouse Analytics Service
**ALL coding models MUST configure ClickHouse with proper authentication.**

#### Pre-Action Checks (MANDATORY):
- **Check 26.1**: Verify CLICKHOUSE_PASSWORD meets requirements
- **Check 26.2**: Confirm user ID 101:101 for proper permissions
- **Check 26.3**: Check volume mounts for data and logs

#### Secret Generation (MANDATORY):
- **Check 26.4**: Generate CLICKHOUSE_PASSWORD: openssl rand -base64 24
- **Check 26.5**: Use "clickhouse" as default username

#### Post-Action Validation (MANDATORY):
- **Check 26.6**: Verify HTTP interface on port 8123
- **Check 26.7**: Test native protocol on port 9000
- **Check 26.8**: Confirm health check endpoint responds
- **Check 26.9**: Validate data ingestion and querying

#### Dependencies and Failure Points:
- **Check 26.10**: Required by: Langfuse analytics
- **Check 26.11**: Failure points: Permission issues, disk space, corrupted data volumes

### Rule 27: RabbitMQ Message Queue Service
**ALL coding models MUST configure RabbitMQ with secure credentials.**

#### Pre-Action Checks (MANDATORY):
- **Check 27.1**: Verify RABBITMQ_USER is alphanumeric, 12 characters
- **Check 27.2**: Confirm RABBITMQ_PASS is 24+ characters
- **Check 27.3**: Check volume mount for data persistence

#### Secret Generation (MANDATORY):
- **Check 27.4**: Generate RABBITMQ_USER: openssl rand -hex 8 (12 chars)
- **Check 27.5**: Generate RABBITMQ_PASS: openssl rand -base64 24

#### Post-Action Validation (MANDATORY):
- **Check 27.6**: Verify management interface on port 15672
- **Check 27.7**: Test AMQP protocol on port 5672
- **Check 27.8**: Confirm authentication with generated credentials
- **Check 27.9**: Validate queue creation and messaging

#### Dependencies and Failure Points:
- **Check 27.10**: Optional service, no critical dependencies
- **Check 27.11**: Failure points: Authentication failures, Erlang cookie issues

### Rule 28: Graylog Logging Service
**ALL coding models MUST configure Graylog with proper secrets.**

#### Pre-Action Checks (MANDATORY):
- **Check 28.1**: Verify GRAYLOG_PASSWORD_SECRET is 32 bytes hex
- **Check 28.2**: Confirm GRAYLOG_PASSWORD is 24+ characters
- **Check 28.3**: Check MongoDB and OpenSearch dependencies

#### Secret Generation (MANDATORY):
- **Check 28.4**: Generate GRAYLOG_PASSWORD_SECRET: openssl rand -hex 32
- **Check 28.5**: Generate GRAYLOG_PASSWORD: openssl rand -base64 24
- **Check 28.6**: Use predefined SHA2 hash for root password

#### Post-Action Validation (MANDATORY):
- **Check 28.7**: Verify Graylog interface accessibility
- **Check 28.8**: Test log ingestion from services
- **Check 28.9**: Confirm authentication with generated credentials
- **Check 28.10**: Validate log storage and searching

#### Dependencies and Failure Points:
- **Check 28.11**: Depends on: MongoDB, OpenSearch
- **Check 28.12**: Failure points: Database connectivity, authentication issues

### Rule 29: Flowise AI Workflows Service
**ALL coding models MUST configure Flowise with secure credentials.**

#### Pre-Action Checks (MANDATORY):
- **Check 29.1**: Verify FLOWISE_USERNAME is alphanumeric, 12 characters
- **Check 29.2**: Confirm FLOWISE_PASSWORD is 24+ characters
- **Check 29.3**: Check volume mount for data persistence

#### Secret Generation (MANDATORY):
- **Check 29.4**: Generate FLOWISE_USERNAME: openssl rand -hex 8 (12 chars)
- **Check 29.5**: Generate FLOWISE_PASSWORD: openssl rand -base64 24

#### Post-Action Validation (MANDATORY):
- **Check 29.6**: Verify Flowise interface on port 3001
- **Check 29.7**: Test authentication with generated credentials
- **Check 29.8**: Confirm workflow creation and execution
- **Check 29.9**: Validate data persistence

#### Dependencies and Failure Points:
- **Check 29.10**: Optional service, no critical dependencies
- **Check 29.11**: Failure points: Authentication failures, volume issues

### Rule 30: LocalAI Service
**ALL coding models MUST configure LocalAI with API key authentication.**

#### Pre-Action Checks (MANDATORY):
- **Check 30.1**: Verify LOCALAI_API_KEY is 32 bytes hex
- **Check 30.2**: Confirm model volume mount is accessible

#### Secret Generation (MANDATORY):
- **Check 30.3**: Generate LOCALAI_API_KEY: openssl rand -hex 32

#### Post-Action Validation (MANDATORY):
- **Check 30.4**: Verify LocalAI API on port 8080
- **Check 30.5**: Test API key authentication
- **Check 30.6**: Confirm model loading and inference
- **Check 30.7**: Validate model persistence

#### Dependencies and Failure Points:
- **Check 30.8**: Optional service, no critical dependencies
- **Check 30.9**: Failure points: Model download issues, API key validation failures

### Rule 31: Frontend Next.js Application
**ALL coding models MUST configure frontend with proper Supabase integration.**

#### Pre-Action Checks (MANDATORY):
- **Check 31.1**: Verify NEXTAUTH_SECRET is 32 bytes hex
- **Check 31.2**: Confirm ANON_KEY matches Supabase configuration
- **Check 31.3**: Validate SUPABASE_HOSTNAME is set
- **Check 31.4**: Check build context and Dockerfile exist

#### Secret Generation (MANDATORY):
- **Check 31.5**: Use NEXTAUTH_SECRET from shared generation
- **Check 31.6**: Use ANON_KEY from Supabase JWT generation

#### Post-Action Validation (MANDATORY):
- **Check 31.7**: Verify frontend accessible on port 3000
- **Check 31.8**: Test Supabase authentication flow
- **Check 31.9**: Confirm NextAuth session management
- **Check 31.10**: Validate API route functionality

#### Dependencies and Failure Points:
- **Check 31.11**: Depends on: PostgreSQL, Supabase services
- **Check 31.12**: Failure points: Supabase connectivity, JWT validation issues

### Rule 32: Agentic Knowledge RAG Graph Service
**ALL coding models MUST configure agentic service with proper database connections.**

#### Pre-Action Checks (MANDATORY):
- **Check 32.1**: Verify NEO4J_AUTH is properly formatted
- **Check 32.2**: Confirm POSTGRES_PASSWORD for database access
- **Check 32.3**: Validate QDRANT_URL and OLLAMA_URL
- **Check 32.4**: Check build context and shared volume mounts

#### Secret Generation (MANDATORY):
- **Check 32.5**: Use NEO4J_AUTH from Neo4j configuration
- **Check 32.6**: Use POSTGRES_PASSWORD from database configuration

#### Post-Action Validation (MANDATORY):
- **Check 32.7**: Verify agentic API on port 8000
- **Check 32.8**: Test Neo4j graph database connectivity
- **Check 32.9**: Confirm PostgreSQL data access
- **Check 32.10**: Validate Qdrant vector operations
- **Check 32.11**: Test Ollama model inference

#### Dependencies and Failure Points:
- **Check 32.12**: Depends on: PostgreSQL, Neo4j, Qdrant, Ollama
- **Check 32.13**: Failure points: Database connectivity issues, model loading failures

## Docker Compose Deployment Reliability Rules

### Rule 16: Container Deployment Standards
**ALL coding models MUST ensure Docker Compose containers deploy properly and operate nominally.**

#### Pre-Deployment Checks (MANDATORY):
- **Check 16.1**: Validate all required environment variables are set
- **Check 16.2**: Confirm all service dependencies are available
- **Check 16.3**: Verify Docker images exist or can be pulled
- **Check 16.4**: Check for port conflicts on all service ports
- **Check 16.5**: Validate volume mounts and permissions
- **Check 16.6**: Confirm network configurations are correct
- **Check 16.7**: Test Docker daemon connectivity
- **Check 16.8**: Verify compose file syntax and structure

#### Deployment Execution (MANDATORY):
- **Check 16.9**: Start services in dependency order (infrastructure → databases → applications)
- **Check 16.10**: Wait for health checks to pass before proceeding
- **Check 16.11**: Monitor resource usage during startup
- **Check 16.12**: Handle service startup timeouts gracefully
- **Check 16.13**: Implement retry logic for transient failures
- **Check 16.14**: Log detailed startup progress

#### Post-Deployment Validation (MANDATORY):
- **Check 16.15**: Verify all containers are running (not just started)
- **Check 16.16**: Test service-to-service connectivity
- **Check 16.17**: Validate health endpoints respond correctly
- **Check 16.18**: Confirm expected ports are bound and accessible
- **Check 16.19**: Check application logs for errors or warnings
- **Check 16.20**: Verify database connections and schemas
- **Check 16.21**: Test API endpoints and web interfaces
- **Check 16.22**: Confirm monitoring and logging are functional

### Rule 17: Supabase Service Deployment
**ALL coding models MUST ensure Supabase services deploy correctly.**

#### Pre-Deployment Checks (MANDATORY):
- **Check 17.1**: Verify all Supabase environment variables are set
- **Check 17.2**: Confirm JWT secrets are valid and properly formatted
- **Check 17.3**: Check database password and connection settings
- **Check 17.4**: Validate Supabase configuration files
- **Check 17.5**: Ensure required ports (5432, 8000, etc.) are available

#### Deployment Execution (MANDATORY):
- **Check 17.6**: Start PostgreSQL first and wait for healthy state
- **Check 17.7**: Initialize Supabase with proper environment
- **Check 17.8**: Wait for Kong API gateway to be ready
- **Check 17.9**: Validate authentication service startup
- **Check 17.10**: Confirm database migrations complete
- **Check 17.11**: Test Supabase Studio accessibility

#### Post-Deployment Validation (MANDATORY):
- **Check 17.12**: Verify PostgreSQL is accepting connections
- **Check 17.13**: Test Supabase API health endpoint
- **Check 17.14**: Confirm JWT token generation works
- **Check 17.15**: Validate database schema is correct
- **Check 17.16**: Check Supabase Studio login functionality
- **Check 17.17**: Test authentication flows
- **Check 17.18**: Verify storage and edge functions if configured

### Rule 18: Service Interoperability
**ALL coding models MUST ensure all services operate together nominally.**

#### Pre-Deployment Checks (MANDATORY):
- **Check 18.1**: Validate service dependency chains
- **Check 18.2**: Confirm network connectivity between services
- **Check 18.3**: Check shared volume permissions
- **Check 18.4**: Verify environment variable propagation

#### Runtime Validation (MANDATORY):
- **Check 18.5**: Test database connections from applications
- **Check 18.6**: Validate API communication between services
- **Check 18.7**: Confirm shared storage accessibility
- **Check 18.8**: Test authentication token passing
- **Check 18.9**: Verify monitoring data collection
- **Check 18.10**: Check log aggregation functionality

#### Operational Checks (MANDATORY):
- **Check 18.11**: Monitor resource usage across all services
- **Check 18.12**: Validate backup and recovery procedures
- **Check 18.13**: Test service restart capabilities
- **Check 18.14**: Confirm graceful shutdown behavior
- **Check 18.15**: Verify error handling and recovery

## .env File and Secrets Generation Rules

### Rule 5: .env File Creation Protocol
**All coding models MUST follow strict protocols for .env file handling.**

#### Pre-Action Checks (Mandatory):
- **Check 5.1**: Verify `.env` file exists; if not, check for `.env.template` or `.env.example`
- **Check 5.2**: Confirm openssl is installed and accessible
- **Check 5.3**: Validate date and shuf/gshuf utilities are available
- **Check 5.4**: Check available disk space (minimum 100MB)
- **Check 5.5**: Ensure no existing .env backup conflicts

#### Action Execution (Mandatory):
- **Check 5.6**: Create timestamped backup of existing .env file
- **Check 5.7**: Generate all secrets using openssl rand with appropriate lengths
- **Check 5.8**: Use secure random generation for all cryptographic keys
- **Check 5.9**: Update or add environment variables safely
- **Check 5.10**: Generate JWT tokens if jq is available

#### Post-Action Checks (Mandatory):
- **Check 5.11**: Verify all required secrets are present and non-empty
- **Check 5.12**: Confirm no placeholder values remain (no "your-" prefixes)
- **Check 5.13**: Validate JWT token format and expiration
- **Check 5.14**: Set file permissions to 600
- **Check 5.15**: Ensure backup file was created successfully

### Rule 6: Secrets Generation Standards
**All coding models MUST generate secrets according to established security standards.**

#### Pre-Action Checks (Mandatory):
- **Check 6.1**: Verify entropy source availability
- **Check 6.2**: Confirm minimum key lengths are met
- **Check 6.3**: Check for existing secrets that should be preserved
- **Check 6.4**: Validate secret naming conventions

#### Action Execution (Mandatory):
- **Check 6.5**: Use 256-bit keys for JWT secrets
- **Check 6.6**: Generate 32-byte encryption keys
- **Check 6.7**: Create 24-character passwords minimum
- **Check 6.8**: Use base64 encoding for complex secrets
- **Check 6.9**: Generate unique values for each service

#### Post-Action Checks (Mandatory):
- **Check 6.10**: Verify cryptographic strength of generated secrets
- **Check 6.11**: Confirm secrets are URL-safe where required
- **Check 6.12**: Validate secret format requirements per service
- **Check 6.13**: Ensure no duplicate secrets across services
- **Check 6.14**: Check secret expiration dates are reasonable

### Rule 7: Bitwarden Integration (Optional)
**When using Bitwarden for secrets population, additional checks apply.**

#### Pre-Action Checks (Mandatory):
- **Check 7.1**: Verify bw CLI is installed and authenticated
- **Check 7.2**: Confirm BW_SESSION is set or BW_PASSWORD is available
- **Check 7.3**: Validate vault access permissions

#### Action Execution (Mandatory):
- **Check 7.4**: Retrieve secrets securely without logging
- **Check 7.5**: Use placeholder values for missing secrets
- **Check 7.6**: Maintain standard config sections

#### Post-Action Checks (Mandatory):
- **Check 7.7**: Verify retrieved secrets are valid
- **Check 7.8**: Confirm placeholder handling for missing items
- **Check 7.9**: Validate complete .env structure

## Docker Compose Stack Launch Rules

### Rule 8: System Readiness Validation
**All coding models MUST validate system readiness before Docker operations.**

#### Pre-Action Checks (Mandatory):
- **Check 8.1**: Verify Docker daemon is running and accessible
- **Check 8.2**: Confirm Docker Compose is installed
- **Check 8.3**: Check available disk space (minimum 5GB)
- **Check 8.4**: Validate GPU drivers if GPU profile selected
- **Check 8.5**: Test Docker GPU support if required

#### Port Conflict Resolution (Mandatory):
- **Check 8.6**: Scan for port conflicts on required ports
- **Check 8.7**: Attempt automatic port conflict resolution
- **Check 8.8**: Report unresolvable conflicts clearly

#### Environment Setup (Mandatory):
- **Check 8.9**: Ensure .env file exists and is complete
- **Check 8.10**: Generate secrets if missing
- **Check 8.11**: Set environment-specific variables
- **Check 8.12**: Validate all required environment variables

### Rule 9: Compose Configuration Preparation
**All coding models MUST properly prepare Docker Compose configuration.**

#### Pre-Action Checks (Mandatory):
- **Check 9.1**: Verify all compose files exist
- **Check 9.2**: Validate YAML syntax in compose files
- **Check 9.3**: Check for profile compatibility
- **Check 9.4**: Confirm environment override files exist

#### Action Execution (Mandatory):
- **Check 9.5**: Build complete compose file list
- **Check 9.6**: Set appropriate profiles based on hardware
- **Check 9.7**: Configure environment-specific overrides
- **Check 9.8**: Validate service dependencies

#### Post-Action Checks (Mandatory):
- **Check 9.9**: Verify compose configuration is valid
- **Check 9.10**: Confirm all services are properly defined
- **Check 9.11**: Validate volume and network configurations

### Rule 10: Service Launch Sequence
**All coding models MUST follow the established service launch sequence.**

#### Pre-Action Checks (Mandatory):
- **Check 10.1**: Stop any existing containers safely
- **Check 10.2**: Clean up orphaned containers if needed
- **Check 10.3**: Verify no resource conflicts

#### Infrastructure Services (Mandatory):
- **Check 10.4**: Start core infrastructure (postgres, redis, neo4j, etc.)
- **Check 10.5**: Wait for infrastructure health checks
- **Check 10.6**: Validate infrastructure connectivity

#### Supabase Services (Mandatory):
- **Check 10.7**: Initialize Supabase if required
- **Check 10.8**: Start Supabase components
- **Check 10.9**: Wait for Supabase readiness

#### AI Services (Mandatory):
- **Check 10.10**: Start AI services based on profile
- **Check 10.11**: Pull required models
- **Check 10.12**: Validate AI service availability

#### Application Services (Mandatory):
- **Check 10.13**: Start application services
- **Check 10.14**: Configure service dependencies
- **Check 10.15**: Validate application startup

#### Monitoring Services (Mandatory):
- **Check 10.16**: Start monitoring stack
- **Check 10.17**: Configure monitoring targets
- **Check 10.18**: Validate monitoring functionality

### Rule 11: Health Checks and Validation
**All coding models MUST perform comprehensive health validation.**

#### Service Health Checks (Mandatory):
- **Check 11.1**: Test core service endpoints
- **Check 11.2**: Validate database connections
- **Check 11.3**: Check API availability
- **Check 11.4**: Verify service-to-service communication

#### Application Health Checks (Mandatory):
- **Check 11.5**: Test web interface accessibility
- **Check 11.6**: Validate authentication flows
- **Check 11.7**: Check data processing pipelines
- **Check 11.8**: Verify monitoring dashboards

#### Post-Launch Validation (Mandatory):
- **Check 11.9**: Confirm all services are running
- **Check 11.10**: Validate resource usage is within limits
- **Check 11.11**: Check for error logs or warnings
- **Check 11.12**: Verify backup and recovery readiness

### Rule 12: Error Recovery and Cleanup
**All coding models MUST handle failures gracefully.**

#### Failure Detection (Mandatory):
- **Check 12.1**: Monitor for service startup failures
- **Check 12.2**: Detect health check failures
- **Check 12.3**: Identify resource exhaustion
- **Check 12.4**: Catch configuration errors

#### Recovery Actions (Mandatory):
- **Check 12.5**: Attempt service restart on failures
- **Check 12.6**: Roll back to previous state if possible
- **Check 12.7**: Provide clear recovery instructions
- **Check 12.8**: Log detailed failure information

#### Cleanup Procedures (Mandatory):
- **Check 12.9**: Remove failed containers
- **Check 12.10**: Clean up temporary files
- **Check 12.11**: Reset network configurations if needed
- **Check 12.12**: Preserve logs for debugging

## Validation and Enforcement

### Rule 13: Logging and Auditing
**All coding models MUST maintain comprehensive logs.**

- **Check 13.1**: Log all pre-action validations
- **Check 13.2**: Record all actions performed
- **Check 13.3**: Document post-action validations
- **Check 13.4**: Include timestamps and context
- **Check 13.5**: Preserve logs for troubleshooting

### Rule 14: User Communication
**All coding models MUST provide clear user feedback.**

- **Check 14.1**: Display progress indicators
- **Check 14.2**: Show clear success/failure messages
- **Check 14.3**: Provide actionable error messages
- **Check 14.4**: Include next steps in output
- **Check 14.5**: Avoid exposing sensitive information

### Rule 15: Rule Compliance Verification
**All coding models MUST verify their own compliance.**

- **Check 15.1**: Self-validate against these rules
- **Check 15.2**: Report any rule violations
- **Check 15.3**: Suggest rule improvements
- **Check 15.4**: Maintain rule version awareness
- **Check 15.5**: Update compliance as rules evolve

## Implementation Notes

- **MANDATORY COMPLIANCE**: Every coding agent must obey these rules before and after every single action they take
- These rules apply exclusively to the Local AI Package repository
- All checks marked as "MANDATORY" must be implemented without exception
- Rules should be reviewed and updated as the project evolves
- Non-compliance may result in system instability or security issues
- Models should err on the side of caution when rules are ambiguous
- **EVERY ACTION**: Whether creating files, running commands, or modifying configurations, all rules apply

## Version History

- v1.0: Initial comprehensive rules document
- v1.1: Enhanced with mandatory compliance emphasis and Docker deployment reliability rules
- v1.2: Added detailed service-specific rules for all 27 services with password creation, validation, and operational requirements
- Based on analysis of project scripts and docker-compose configurations