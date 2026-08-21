#!/usr/bin/env bash
# Epic: orchestrator_master (multi_provider_model_capability_bakeoff_2026_08_19)
# Lifecycle: TEMPORARY — delete when that plan archives.
#
# WHY THIS EXISTS: the bake-off needs context/jsonl/token stats sampled every
# <=60s while each model's `claude -p` subprocess runs, per operator instruction
# 2026-08-19. Claude Code's own session transcript (one line per turn, JSON) is
# the only real-time source of turn count / cumulative tokens / tool-call count
# during a still-running attempt — the CLI's own `--output-format json` summary
# only exists after the process exits. `--session-id <uuid>` (passed by the
# caller) makes the transcript path deterministic: all slots under this
# workspace share ONE `~/.claude/projects/<encoded-cwd>/` directory regardless
# of which slot's subdirectory the subprocess actually ran in, so without a
# fixed session id there is no reliable way to tell concurrent attempts' own
# transcript files apart.
#
# Usage: usage-poll.sh <session_uuid> <target_pid> <out_dir> <project_dir_encoded> [interval_s] [context_window_tokens]
# <project_dir_encoded>: the repo's absolute cwd with every "/" and "." replaced by "-"
# (Claude Code's own project-dir naming convention — one dir PER EXACT CWD, not
# per top-level workspace; a slot subdirectory gets its OWN project dir, e.g.
# /active/.../.tabs/24/agent-orchestrator -> -active-...-tabs-24-agent-orchestrator).
set -euo pipefail

SESSION_UUID="$1"
TARGET_PID="$2"
OUT_DIR="$3"
PROJECT_DIR_ENCODED="$4"
INTERVAL="${5:-30}"
# NOTE: there is no safe universal default here — Gemini's real window is 200,000
# (confirmed via a real attempt's own result.json `modelUsage.<model>.contextWindow`
# field, NOT the 1,000,000 this script originally assumed, which understated every
# Gemini context-fill% by 5x until caught 2026-08-19). Always pass the real value
# explicitly per model; this default is a last-resort fallback only.
CONTEXT_WINDOW="${6:-200000}"

mkdir -p "$OUT_DIR"
TRANSCRIPT="$HOME/.claude/projects/${PROJECT_DIR_ENCODED}/${SESSION_UUID}.jsonl"
POLL_LOG="$OUT_DIR/usage_poll.jsonl"
START_TS=$(date -u +%s)

while kill -0 "$TARGET_PID" 2>/dev/null; do
  NOW_TS=$(date -u +%s)
  ELAPSED=$((NOW_TS - START_TS))

  if [[ -f "$TRANSCRIPT" ]]; then
    STATS=$(python3 - "$TRANSCRIPT" "$CONTEXT_WINDOW" <<'PYEOF'
import json, sys
path, ctx_window = sys.argv[1], int(sys.argv[2])
turns = 0
tool_use = 0
tool_error = 0
cum_in = cum_out = cum_cache_read = cum_cache_create = 0
last_in = last_out = 0
try:
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            msg = rec.get("message") or {}
            role = msg.get("role") or rec.get("type")
            if role in ("user", "assistant"):
                turns += 1
            usage = msg.get("usage") or rec.get("usage")
            if usage:
                cum_in += usage.get("input_tokens", 0) or 0
                cum_out += usage.get("output_tokens", 0) or 0
                cum_cache_read += usage.get("cache_read_input_tokens", 0) or 0
                cum_cache_create += usage.get("cache_creation_input_tokens", 0) or 0
                last_in = usage.get("input_tokens", 0) or 0
                last_out = usage.get("output_tokens", 0) or 0
            content = msg.get("content")
            if isinstance(content, list):
                for block in content:
                    if not isinstance(block, dict):
                        continue
                    if block.get("type") == "tool_use":
                        tool_use += 1
                    if block.get("type") == "tool_result" and block.get("is_error"):
                        tool_error += 1
except FileNotFoundError:
    pass

approx_context_used = last_in + last_out
pct = round(100.0 * approx_context_used / ctx_window, 2) if ctx_window else None
print(json.dumps({
    "turns": turns,
    "tool_use_count": tool_use,
    "tool_error_count": tool_error,
    "cumulative_input_tokens": cum_in,
    "cumulative_output_tokens": cum_out,
    "cumulative_cache_read_tokens": cum_cache_read,
    "cumulative_cache_creation_tokens": cum_cache_create,
    "last_turn_input_tokens": last_in,
    "last_turn_output_tokens": last_out,
    "approx_context_used_tokens": approx_context_used,
    "approx_context_used_pct": pct,
}))
PYEOF
)
  else
    STATS='{"note":"transcript not yet created"}'
  fi

  printf '{"ts_utc":"%s","elapsed_s":%d,"stats":%s}\n' \
    "$(date -u -Iseconds)" "$ELAPSED" "$STATS" >> "$POLL_LOG"

  sleep "$INTERVAL"
done

echo "poller: target pid $TARGET_PID exited, stopping (log: $POLL_LOG)" >&2
