#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# Kill zombie basedpyright processes (running > 2 hours)
# Safe: Only kills CLI basedpyright, NOT Cursor's built-in pyright extension

set -e

MAX_HOURS=${1:-2} # Default: 2 hours

echo "🔍 Checking for zombie basedpyright processes (> ${MAX_HOURS} hours old)..."

# Find and kill basedpyright processes older than MAX_HOURS
killed=0

while read pid etime _cmd; do
  # Parse etime format: [[dd-]hh:]mm:ss
  if echo "$etime" | grep -q '-'; then
    # Format: dd-hh:mm:ss
    days=$(echo "$etime" | cut -d'-' -f1)
    rest=$(echo "$etime" | cut -d'-' -f2)
    hours=$(echo "$rest" | cut -d':' -f1)
    total_hours=$((days * 24 + hours))
  elif [ "$(echo "$etime" | tr ':' '\n' | wc -l)" -eq 3 ]; then
    # Format: hh:mm:ss
    total_hours=$(echo "$etime" | cut -d':' -f1)
  else
    # Format: mm:ss
    total_hours=0
  fi

  if [ "$total_hours" -ge "$MAX_HOURS" ]; then
    echo "⚠️  Killing zombie basedpyright (PID: $pid, running: $etime)"
    kill -9 "$pid" 2>/dev/null && killed=$((killed + 1)) || true
  fi
done < <(ps -eo pid,etime,command 2>/dev/null | grep -E 'basedpyright.*index\.js' | grep -v grep)

# Also kill any that are using excessive memory (> 4GB)
# shellcheck disable=SC2034
while read _user pid _cpu _mem _vsz rss _tty _stat _start _time _cmd; do
  # rss is in KB, 4GB = 4194304 KB
  if [ "$rss" -gt 4194304 ]; then
    echo "⚠️  Killing memory-hungry basedpyright (PID: $pid, MEM: $((rss / 1024))MB)"
    kill -9 "$pid" 2>/dev/null && killed=$((killed + 1)) || true
  fi
done < <(ps aux 2>/dev/null | grep -E 'basedpyright.*index\.js' | grep -v grep)

if [ "$killed" -gt 0 ]; then
  echo "✅ Killed $killed zombie process(es)"
else
  echo "✅ No zombie processes found"
fi

# Show current basedpyright processes (for reference)
current=$(ps aux 2>/dev/null | grep -E 'basedpyright.*index\.js' | grep -v grep | wc -l | tr -d ' ')
if [ "$current" -gt 0 ]; then
  echo ""
  echo "📊 Current basedpyright processes ($current):"
  ps aux | grep -E 'basedpyright.*index\.js' | grep -v grep | awk '{printf "  PID: %s, CPU: %s%%, MEM: %s%%, TIME: %s\n", $2, $3, $4, $10}'
fi
