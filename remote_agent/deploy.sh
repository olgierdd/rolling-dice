#!/bin/bash

# Define variables
REMOTE_HOST="root@montecarlo.com"
REMOTE_DIR="/opt/check_winning_agent"

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Navigate to the project root directory (parent of deploy folder)
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT" || exit

echo "Deploying from: $PROJECT_ROOT"

# Sync local changes to the remote server
rsync -avz \
  --exclude '__pycache__' \
  --exclude '.git' \
  --exclude '*.pyc' \
  --exclude '.DS_Store' \
  remote_agent \
  ./requirements.txt \
  "$REMOTE_HOST:$REMOTE_DIR/"

# SSH into the remote server and deploy changes
ssh "$REMOTE_HOST" << 'EOF'

echo "Starting deployment script"

# Navigate to the application directory
cd /opt/check_winning_agent || exit

# Activate the virtual environment
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi
source .venv/bin/activate

# Install any new dependencies (if requirements.txt exists)
if [ -f requirements.txt ]; then
    pip install -r requirements.txt
fi

# Restart the FastAPI service
systemctl restart fastapi-server

echo "Deployment complete. The FastAPI server has been updated and restarted."
EOF

echo "Local deployment script finished."