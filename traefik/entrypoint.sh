#!/bin/sh
set -e

# Export plugin paths
export TRAEFIK_PLUGINS_DIR="/plugins"

# Start Traefik
exec /entrypoint.sh "$@"
