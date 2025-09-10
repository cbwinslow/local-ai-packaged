# Docker Container Communication & Port Conflict Fixes

## Issues Resolved

### 1. Missing Supabase Configuration
**Problem**: The main `docker-compose.yml` included a non-existent `./supabase/docker/docker-compose.yml` file, causing Docker Compose to fail.

**Solution**: 
- Added automatic cloning of official Supabase Docker configuration using sparse checkout
- Updated installation and startup scripts to handle Supabase setup
- Environment file synchronization between root and supabase directories

### 2. Port Conflicts in Override Files
**Problem**: Multiple Ollama services (CPU, GPU-NVIDIA, GPU-AMD) mapped to the same host port (11434) in `docker-compose.override.private.yml`.

**Solution**:
- Validated that Docker Compose profiles properly isolate services
- Only one Ollama profile is active at any time, eliminating conflicts
- Added port conflict detection in startup scripts
- Improved service management to stop all profiles before starting

### 3. Network Configuration Conflicts
**Problem**: Both main `docker-compose.yml` and `docker-compose.traefik.yml` defined the same `default` network, causing conflicts.

**Solution**:
- Removed duplicate network definition from Traefik configuration
- Let Docker Compose manage network creation automatically
- Added network cleanup in startup scripts

### 4. Missing Environment Variables
**Problem**: Several services had undefined environment variables causing warnings and potential startup issues.

**Solution**:
- Added missing Flowise credentials to `.env` file
- Updated installer to generate all required secrets
- Improved environment validation in startup scripts

## Improvements Added

### Auto-Detection and Smart Defaults
- **Hardware Detection**: Automatic detection of GPU type (NVIDIA/AMD/CPU-only)
- **Profile Selection**: Intelligent selection of appropriate Ollama profile
- **Port Conflict Checking**: Pre-startup validation of port availability

### Enhanced Startup Process
```bash
# Auto-detect hardware and start with all checks
python3 start_services_enhanced.py

# Use specific hardware profile
python3 start_services_enhanced.py --profile gpu-nvidia

# Skip port checking for development
python3 start_services_enhanced.py --skip-port-check

# Use public environment (no localhost binding)
python3 start_services_enhanced.py --environment public
```

### Testing and Validation
- **Configuration Testing**: `test_docker_config.py` validates Docker setup
- **Communication Testing**: `validate_service_communication.py` tests service connectivity
- **Pre-flight Checks**: Comprehensive validation before service startup

## Technical Details

### Docker Compose Profiles
Services are organized into profiles to prevent conflicts:
- `cpu`: Ollama CPU-only version
- `gpu-nvidia`: Ollama with NVIDIA GPU support  
- `gpu-amd`: Ollama with AMD GPU support

Only one profile runs at a time, eliminating port conflicts.

### Service Communication
All services communicate through the `localai_default` Docker network:
- Internal hostnames: `postgres:5432`, `neo4j:7687`, `qdrant:6333`, etc.
- Traefik handles external routing on ports 80/443
- Private override exposes individual service ports for development

### Health Checks and Dependencies
- Services wait for dependencies before starting
- Health checks ensure services are ready before dependents start
- Proper startup sequence: Network → Traefik → Supabase → AI Services

## Usage Examples

### Standard Startup
```bash
# Run installer first (if not done)
python3 install.py

# Start all services with auto-detection
python3 start_services_enhanced.py
```

### Development Mode
```bash
# Use private mode with direct port access
python3 start_services_enhanced.py --environment private

# Skip frontend building for faster startup
python3 start_services_enhanced.py --skip-build
```

### Troubleshooting
```bash
# Test configuration
python3 test_docker_config.py

# Test service communication
python3 validate_service_communication.py

# Check running services
docker compose -p localai ps

# View service logs
docker compose -p localai logs [service-name]
```

## Files Modified

- `start_services_enhanced.py` - Enhanced startup with auto-detection and validation
- `docker-compose.traefik.yml` - Fixed network conflicts and removed obsolete version
- `.env` - Added missing Flowise authentication variables  
- `.gitignore` - Added proper exclusions for generated files and directories

## Files Added

- `test_docker_config.py` - Docker configuration testing
- `validate_service_communication.py` - Service communication validation

## Next Steps

1. **Test in Clean Environment**: Validate startup in fresh environment
2. **Add Monitoring**: Implement service health monitoring  
3. **Performance Optimization**: Tune resource allocation per service
4. **Documentation**: Create comprehensive user guides for each service