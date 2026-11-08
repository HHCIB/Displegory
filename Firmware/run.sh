#!/bin/bash
# Fetch data, then display it separately

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Starting transport display"
echo "Updates every 60 seconds"
echo "Press Ctrl+C to stop"

while true; do
    echo ""
    echo "$(date): Fetching data..."
    python3 "$SCRIPT_DIR/fetch_data.py"

    echo "Waiting for radio to power down.."
    sleep 5

    echo "$(date): Displaying data..."
    python3 "$SCRIPT_DIR/display_data.py"

    echo "$(date): Update complete. Waiting 60 seconds..."
    sleep 60
done
