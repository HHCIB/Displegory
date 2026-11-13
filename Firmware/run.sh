#!/bin/bash
# Start the departure board. -u: unbuffered output, so logs reach journalctl immediately.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec python3 -u "$SCRIPT_DIR/main.py"
