#!/bin/bash

# Test script for RIFT Healing Agent
# Usage: ./test-agent.sh

echo "🚀 Testing RIFT Healing Agent..."
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if backend is running
echo "📡 Checking backend..."
if curl -s http://localhost:8000 > /dev/null; then
    echo -e "${GREEN}✓ Backend is running${NC}"
else
    echo -e "${RED}✗ Backend is not running${NC}"
    echo "Start it with: cd backend && uvicorn main:app --reload"
    exit 1
fi

# Check if frontend is running
echo "📡 Checking frontend..."
if curl -s http://localhost:3000 > /dev/null || curl -s http://localhost:5173 > /dev/null; then
    echo -e "${GREEN}✓ Frontend is running${NC}"
else
    echo -e "${YELLOW}⚠ Frontend might not be running${NC}"
    echo "Start it with: cd frontend && npm run dev"
fi

echo ""
echo "🧪 Running test job..."
echo ""

# Test with a sample repository (replace with your test repo)
RESPONSE=$(curl -s -X POST http://localhost:8000/api/run-agent \
  -H "Content-Type: application/json" \
  -d '{
    "github_url": "https://github.com/octocat/Hello-World",
    "team_name": "Test Team",
    "leader_name": "Test Leader",
    "github_token": "'"$GITHUB_TOKEN"'"
  }')

# Extract job_id
JOB_ID=$(echo $RESPONSE | grep -o '"job_id":"[^"]*"' | cut -d'"' -f4)

if [ -z "$JOB_ID" ]; then
    echo -e "${RED}✗ Failed to start job${NC}"
    echo "Response: $RESPONSE"
    exit 1
fi

echo -e "${GREEN}✓ Job started successfully${NC}"
echo "Job ID: $JOB_ID"
echo ""
echo "📊 Monitor progress at:"
echo "  - Dashboard: http://localhost:3000"
echo "  - Status API: http://localhost:8000/api/status/$JOB_ID"
echo "  - Stream: http://localhost:8000/api/stream/$JOB_ID"
echo ""
echo "⏳ Waiting for job to complete..."

# Poll status
for i in {1..60}; do
    sleep 2
    STATUS=$(curl -s http://localhost:8000/api/status/$JOB_ID | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
    PROGRESS=$(curl -s http://localhost:8000/api/status/$JOB_ID | grep -o '"progress":[0-9]*' | cut -d':' -f2)
    
    echo -ne "\rProgress: $PROGRESS% | Status: $STATUS     "
    
    if [ "$STATUS" = "done" ] || [ "$STATUS" = "failed" ]; then
        echo ""
        break
    fi
done

echo ""
if [ "$STATUS" = "done" ]; then
    echo -e "${GREEN}✓ Job completed successfully!${NC}"
    echo ""
    echo "📄 View results:"
    echo "  curl http://localhost:8000/api/results/$JOB_ID | jq"
elif [ "$STATUS" = "failed" ]; then
    echo -e "${RED}✗ Job failed${NC}"
else
    echo -e "${YELLOW}⚠ Job still running after 2 minutes${NC}"
fi

echo ""
echo "🎉 Test complete!"
