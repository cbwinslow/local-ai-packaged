#!/bin/bash
# This script is a wrapper around the new Python-based secret population script.
# It ensures backward compatibility while centralizing the logic in populate_secrets.py.

set -e

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"

# Construct the full path to the Python script
PYTHON_SCRIPT_PATH="$SCRIPT_DIR/populate_secrets.py"

# Check if the Python script exists
if [ ! -f "$PYTHON_SCRIPT_PATH" ]; then
    echo "❌ Error: The script 'populate_secrets.py' was not found in the same directory."
    exit 1
fi

# Execute the Python script, passing along all command-line arguments
echo "Redirecting to the new populate_secrets.py script..."
"$PYTHON_SCRIPT_PATH" "$@"

exit_code=$?
if [ $exit_code -ne 0 ]; then
    echo "❌ The populate_secrets.py script failed with exit code $exit_code."
    exit $exit_code
fi

echo "✅ Wrapper script finished successfully."