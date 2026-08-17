#!/bin/bash

###############################################################################
# SOAP Self-Healing Test Agent Launcher
# 
# This script launches the intelligent SOAP testing agent that:
# 1. Runs SOAP tests
# 2. Detects assertion failures
# 3. Analyzes WSDL schema
# 4. Auto-fixes SOAP requests
# 5. Re-runs tests iteratively
###############################################################################

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENT_SCRIPT="${SCRIPT_DIR}/soap-self-healing-agent.py"
AGENT_CONFIG="${SCRIPT_DIR}/agent-config.json"
LOG_FILE="${AGENT_LOG_FILE:-${SCRIPT_DIR}/agent-execution.log}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                                                                      ║${NC}"
echo -e "${BLUE}║           SOAP SELF-HEALING TEST AGENT v1.0                          ║${NC}"
echo -e "${BLUE}║                                                                      ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════════════╝${NC}"
echo ""

mkdir -p "$(dirname "$LOG_FILE")"
touch "$LOG_FILE"
exec > >(tee -a "$LOG_FILE") 2>&1

# Check prerequisites
echo -e "${YELLOW}[*] Checking prerequisites...${NC}"

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[!] Python 3 is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}[✓] Python 3 found${NC}"

if ! command -v mvn &> /dev/null; then
    echo -e "${YELLOW}[!] Maven is not installed; continuing because tests run through the Python agent${NC}"
else
    echo -e "${GREEN}[✓] Maven found${NC}"
fi

if [ ! -f "$AGENT_SCRIPT" ]; then
    echo -e "${RED}[!] Agent script not found: $AGENT_SCRIPT${NC}"
    exit 1
fi
echo -e "${GREEN}[✓] Agent script found${NC}"

if [ ! -f "$AGENT_CONFIG" ]; then
    echo -e "${YELLOW}[!] Config file not found, using defaults${NC}"
else
    echo -e "${GREEN}[✓] Config file found${NC}"
fi

echo ""
echo -e "${YELLOW}[*] Launching SOAP Self-Healing Agent...${NC}"
echo ""

# Run the agent
python3 "$AGENT_SCRIPT" "$@"
EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}[✓] Agent completed successfully${NC}"
else
    echo -e "${RED}[!] Agent exited with code: $EXIT_CODE${NC}"
fi

exit $EXIT_CODE
