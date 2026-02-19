#!/bin/bash

# RIFT 2026 Backend Test Script
# Tests the backend API endpoints

echo "🧪 Testing RIFT 2026 Backend API"
echo "================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if backend is running
echo "1️⃣  Checking if backend is running..."
if curl -s http://localhost:8000/api/health > /dev/null; then
    echo -e "${GREEN}✓ Backend is running${NC}"
else
    echo -e "${RED}✗ Backend is not running${NC}"
    echo "   Start it with: docker-compose up -d backend"
    exit 1
fi

echo ""

# Test health endpoint
echo "2️⃣  Testing /api/health endpoint..."
HEALTH=$(curl -s http://localhost:8000/api/health)
echo "   Response: $HEALTH"
if echo "$HEALTH" | grep -q "ok"; then
    echo -e "${GREEN}✓ Health check passed${NC}"
else
    echo -e "${RED}✗ Health check failed${NC}"
fi

echo ""

# Test stats endpoint
echo "3️⃣  Testing /api/stats endpoint..."
STATS=$(curl -s http://localhost:8000/api/stats)
if echo "$STATS" | grep -q "successRate"; then
    echo -e "${GREEN}✓ Stats endpoint working${NC}"
    echo "   Stats: $STATS"
else
    echo -e "${RED}✗ Stats endpoint failed${NC}"
fi

echo ""

# Test runs endpoint
echo "4️⃣  Testing /api/runs endpoint..."
RUNS=$(curl -s http://localhost:8000/api/runs)
if [ "$RUNS" = "[]" ] || echo "$RUNS" | grep -q "job_id"; then
    echo -e "${GREEN}✓ Runs endpoint working${NC}"
    echo "   Runs: $RUNS"
else
    echo -e "${RED}✗ Runs endpoint failed${NC}"
fi

echo ""

# Check environment variables
echo "5️⃣  Checking environment variables..."
if [ -f "backend/.env" ]; then
    if grep -q "OPENAI_API_KEY=sk-" backend/.env; then
        echo -e "${GREEN}✓ OPENAI_API_KEY is set${NC}"
    else
        echo -e "${RED}✗ OPENAI_API_KEY is missing${NC}"
    fi
    
    if grep -q "GITHUB_TOKEN=ghp_" backend/.env; then
        echo -e "${GREEN}✓ GITHUB_TOKEN is set${NC}"
    else
        echo -e "${RED}✗ GITHUB_TOKEN is missing${NC}"
    fi
else
    echo -e "${RED}✗ backend/.env file not found${NC}"
fi

echo ""
echo "================================"
echo "✅ Backend test complete!"
echo ""
echo "Next steps:"
echo "  1. Open http://localhost:3000 in your browser"
echo "  2. Click '+ new run'"
echo "  3. Test with a buggy repository"
echo ""
