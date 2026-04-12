# 3) Kill services on common web ports
for port in 8000 8001 8002; do
  pids=$(lsof -tiTCP:$port -sTCP:LISTEN)

  if [ -n "$pids" ]; then
    echo "Killing service running on port $port with PID(s): $pids"
    kill -TERM $pids
  fi
done