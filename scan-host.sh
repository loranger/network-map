#!/usr/bin/env bash
set -euo pipefail
API="${1:-http://localhost:8000/api/scan/import}"
echo "Running arp -a on the host..."
OUTPUT=$(arp -a 2>&1)
echo "Sending to $API ..."
PAYLOAD=$(python3 -c "import json,sys; print(json.dumps({'raw': sys.stdin.read()}))" <<< "$OUTPUT")
curl -s -X POST "$API" -H "Content-Type: application/json" -d "$PAYLOAD" | python3 -m json.tool
