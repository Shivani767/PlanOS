#!/bin/bash
echo "=== Backend Health ==="
curl -s -m 3 http://localhost:8000/health || echo "Backend unreachable"

echo ""
echo "=== Frontend ==="
curl -s -m 3 http://localhost:5173 | head -5 || echo "Frontend unreachable"

echo ""
echo "=== Processes ==="
ps aux | grep -E 'uvicorn|vite' | grep -v grep | head -5

echo ""
echo "=== Ports ==="
lsof -i :8000 -i :5173 2>/dev/null | grep LISTEN
