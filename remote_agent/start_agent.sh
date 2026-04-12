#!/bin/bash
# Wrapper script for check-winning-agent with proper logging

# Create log directory if it doesn't exist
mkdir -p /opt/.logs

# Get current date in format YYYYMMDD-HH
LOG_FILE="/opt/.logs/agent_$(date +%Y%m%d-%H).log"

# Run the agent and redirect output to log file
exec /opt/check_winning_agent/.venv/bin/adk api_server --a2a --port 8001 remote_agent --log_level info >> "$LOG_FILE" 2>&1

