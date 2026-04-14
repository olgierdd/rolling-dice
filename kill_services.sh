#!/usr/bin/env bash

# 3) Kill services on common web ports

normalize_pids() {
  tr ' ' '\n' | tr -d '\r' | grep -E '^[0-9]+$' | sort -u
}

get_pids_unix() {
  local port="$1"

  if command -v lsof >/dev/null 2>&1; then
    lsof -tiTCP:"$port" -sTCP:LISTEN 2>/dev/null
    return
  fi

  if command -v ss >/dev/null 2>&1; then
    ss -lntp 2>/dev/null | awk -v p=":$port" '$4 ~ p"$" {print $NF}' | sed -n 's/.*pid=\([0-9]\+\).*/\1/p'
  fi
}

get_pids_windows() {
  local port="$1"
  local pids=""

  if command -v powershell.exe >/dev/null 2>&1; then
    pids=$(powershell.exe -NoProfile -Command "Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique" 2>/dev/null | tr -d '\r')
  fi

  if [ -z "$pids" ] && command -v netstat >/dev/null 2>&1; then
    pids=$(netstat -ano -p tcp 2>/dev/null | awk -v p=":$port" '$1=="TCP" && $2 ~ p"$" && $4=="LISTENING" {print $5}')
  fi

  printf "%s\n" "$pids"
}

kill_pid_windows() {
  local pid="$1"
  local output=""

  # Git Bash may rewrite /PID-style args; disable conversion for native Windows tools.
  output=$(MSYS2_ARG_CONV_EXCL='*' taskkill.exe /PID "$pid" /T /F 2>&1)
  if [ $? -eq 0 ]; then
    return 0
  fi

  # Fallback path if taskkill is unavailable in PATH for this shell.
  if command -v powershell.exe >/dev/null 2>&1; then
    output=$(powershell.exe -NoProfile -Command "Stop-Process -Id $pid -Force -ErrorAction Stop" 2>&1)
    if [ $? -eq 0 ]; then
      return 0
    fi
  fi

  echo "Failed to kill PID $pid: $(echo "$output" | tr -d '\r' | tail -n 1)"
  return 1
}

is_windows="false"
case "$(uname -s 2>/dev/null | tr '[:upper:]' '[:lower:]')" in
  msys*|mingw*|cygwin*) is_windows="true" ;;
esac

for port in 8000 8001 8002; do
  if [ "$is_windows" = "true" ]; then
    pids=$(get_pids_windows "$port" | normalize_pids)
  else
    pids=$(get_pids_unix "$port" | normalize_pids)
  fi

  if [ -n "$pids" ]; then
    echo "Killing service running on port $port with PID(s): $pids"

    if [ "$is_windows" = "true" ]; then
      for pid in $pids; do
        kill_pid_windows "$pid"
      done
    else
      kill -TERM $pids 2>/dev/null || true
    fi
  else
    echo "No listening service found on port $port"
  fi
done