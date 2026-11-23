#!/bin/sh
cd "$(dirname "$0")"
export DIALED_LAN=1
echo "Starting Dialed in phone mode..."
exec python3 serve.py
