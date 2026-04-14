# Start the remote a2a server that serves the check prime agent on port 8001
LOG_DIR=".logs"
REMOTE_LOG_TS="$(date +"%Y%m%d-%H")"
mkdir -p "$LOG_DIR"
echo "Clearing the logs directory..."
if [ -d "$LOG_DIR" ]; then
  rm -f "$LOG_DIR"/*
fi

case "$OSTYPE" in
  msys* | cygwin*)
    # Windows (Git Bash, MSYS2, or Cygwin)
    source .venv/Scripts/activate
    ;;
  *)
    # Unix/Linux/macOS
    source .venv/bin/activate
    ;;
esac
echo "Virtual environment activated."

echo "Starting remote agent server port 8001"
adk api_server --a2a --port 8001 remote_agent --log_level INFO > "$LOG_DIR/remote_agent_${REMOTE_LOG_TS}.log" 2>&1 &
#adk api_server --a2a --port 8001 remote_agent --log_level INFO > ".logs/remote_agent_$(date +"%Y%m%d-%H").log" 2>&1 &

echo "Starting local main agent port 8002"
adk web main_agent --port 8002 --log_level INFO > "$LOG_DIR/main_agent.log" 2>&1 &

#adk web main_agent --port 8002 --log_level INFO > ".logs/main__agent.log" 2>&1 &
