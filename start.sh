#!/bin/sh
cd "$(dirname "$0")"
echo "Dialed is running at http://localhost:8765  (open it in Brave; Ctrl+C to stop)"
exec python3 serve.py
