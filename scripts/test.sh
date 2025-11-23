#!/bin/bash
# WhispyrKeep Full Test Suite
# Run all tests for backend and frontend

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=========================================="
echo "  WhispyrKeep Test Suite"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track failures
FAILED=0

# Backend tests
echo -e "\n${YELLOW}[1/3] Running Backend Tests...${NC}"
if [ -d "$PROJECT_ROOT/backend" ]; then
    cd "$PROJECT_ROOT/backend"
    if python -m pytest --cov --cov-report=term-missing -q; then
        echo -e "${GREEN}Backend tests passed!${NC}"
    else
        echo -e "${RED}Backend tests failed!${NC}"
        FAILED=1
    fi
else
    echo -e "${YELLOW}Backend directory not found, skipping...${NC}"
fi

# Frontend tests
echo -e "\n${YELLOW}[2/3] Running Frontend Tests...${NC}"
if [ -d "$PROJECT_ROOT/frontend" ] && [ -f "$PROJECT_ROOT/frontend/package.json" ]; then
    cd "$PROJECT_ROOT/frontend"
    if npm test -- --watch=false --browsers=ChromeHeadless 2>/dev/null; then
        echo -e "${GREEN}Frontend tests passed!${NC}"
    else
        echo -e "${RED}Frontend tests failed!${NC}"
        FAILED=1
    fi
else
    echo -e "${YELLOW}Frontend not initialized, skipping...${NC}"
fi

# Lint checks
echo -e "\n${YELLOW}[3/3] Running Lint Checks...${NC}"
if [ -d "$PROJECT_ROOT/backend" ]; then
    cd "$PROJECT_ROOT/backend"
    if command -v ruff &> /dev/null; then
        if ruff check . --quiet; then
            echo -e "${GREEN}Backend lint passed!${NC}"
        else
            echo -e "${RED}Backend lint failed!${NC}"
            FAILED=1
        fi
    else
        echo -e "${YELLOW}Ruff not installed, skipping backend lint...${NC}"
    fi
fi

if [ -d "$PROJECT_ROOT/frontend" ] && [ -f "$PROJECT_ROOT/frontend/package.json" ]; then
    cd "$PROJECT_ROOT/frontend"
    if npm run lint 2>/dev/null; then
        echo -e "${GREEN}Frontend lint passed!${NC}"
    else
        echo -e "${RED}Frontend lint failed!${NC}"
        FAILED=1
    fi
fi

# Summary
echo -e "\n=========================================="
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed!${NC}"
    exit 1
fi
