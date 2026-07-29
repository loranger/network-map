#!/usr/bin/env bash
set -euo pipefail
API="${1:-http://localhost:8000/api/scan/import}"

# Ping sweep to populate ARP cache before reading it
echo "Ping sweep du sous-réseau pour peupler le cache ARP..."
SUBNET=$(arp -a 2>/dev/null | head -5 | grep -oE '\d+\.\d+\.\d+\.' | head -1 || echo "192.168.1.")
for i in $(seq 1 254); do
    ping -c 1 -t 1 "${SUBNET}${i}" &>/dev/null &
done
wait 2>/dev/null || true
sleep 0.5

echo "Running arp -a on the host..."
OUTPUT=$(arp -a 2>&1)
echo "Sending to $API ..."
PAYLOAD=$(python3 -c "import json,sys; print(json.dumps({'raw': sys.stdin.read()}))" <<< "$OUTPUT")
curl -s -X POST "$API" -H "Content-Type: application/json" -d "$PAYLOAD" | python3 -m json.tool
