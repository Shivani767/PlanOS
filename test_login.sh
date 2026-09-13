#!/bin/bash
echo "=== Login Test ==="
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@acme.com","password":"password123"}')
echo "$LOGIN_RESPONSE"

TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null)

if [ -n "$TOKEN" ]; then
  echo ""
  echo "=== Plans with Auth ==="
  curl -s http://localhost:8000/api/v1/plans \
    -H "Authorization: Bearer $TOKEN" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Total plans: {d[\"total\"]}')"
  
  echo ""
  echo "=== Scenarios ==="
  curl -s http://localhost:8000/api/v1/scenarios \
    -H "Authorization: Bearer $TOKEN" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Total scenarios: {d[\"total\"]}')"
fi
