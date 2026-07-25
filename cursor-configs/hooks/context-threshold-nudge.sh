#!/usr/bin/env bash
# UserPromptSubmit hook: nudge Claude to run /pre-compact once estimated context
# usage crosses 65% of a 1M-token budget. Estimate only (transcript bytes / 4)
# -- not a real token count. Fires once per session via a sentinel file.
#
# BUDGET_TOKENS was 200000 until 2026-07-23 -- wrong for this fleet's actual
# sessions (Claude 5 family, 1M context), so the nudge fired at ~50k real
# tokens (transcript-byte estimate hit 65% of the WRONG, 5x-too-small budget)
# instead of anywhere near a real compaction boundary. Corrected per operator
# 2026-07-23. If your session's real context window differs, override via env
# (not yet plumbed through the hook input -- edit this constant for now).
#
# SINCE-LAST-COMPACT windowing (2026-07-25): the transcript file is an
# append-only log of the WHOLE session -- Claude Code keeps appending to the
# SAME file across every /compact (confirmed on a real session: one file
# accumulated 13 "subtype":"compact_boundary" events). Live context resets to
# [compaction summary + turns since] at each /compact, but whole-file-bytes/4
# does NOT reset, so on a long, much-compacted session it runs wildly high
# (measured: whole-file heuristic read ~1475% of budget on a session the
# operator's own reading put at ~15%). Fix: estimate only from the byte
# offset of the LAST compact_boundary event onward (falls back to the whole
# file if the session hasn't compacted yet). Still an approximation, not a
# real token count -- large tool outputs / repeated system-reminder content
# can inflate transcript bytes beyond what actually occupies live context.
set -euo pipefail

INPUT="$(cat)"
SESSION_ID="$(printf '%s' "$INPUT" | jq -r '.session_id // empty')"
TRANSCRIPT_PATH="$(printf '%s' "$INPUT" | jq -r '.transcript_path // empty')"

[ -z "$SESSION_ID" ] && exit 0
[ -z "$TRANSCRIPT_PATH" ] && exit 0
[ ! -f "$TRANSCRIPT_PATH" ] && exit 0

SENTINEL="$(dirname "$TRANSCRIPT_PATH")/.context-nudge-sent-${SESSION_ID}"
[ -f "$SENTINEL" ] && exit 0

TOTAL_BYTES=$(wc -c < "$TRANSCRIPT_PATH" | tr -d ' ')

# Byte offset of the last compaction boundary, if any -- everything before it
# is pre-compaction history no longer in the live context window.
LAST_BOUNDARY_OFFSET=$(grep -abo '"subtype":"compact_boundary"' "$TRANSCRIPT_PATH" 2>/dev/null | tail -1 | cut -d: -f1)

if [ -n "$LAST_BOUNDARY_OFFSET" ]; then
  WINDOW_BYTES=$(( TOTAL_BYTES - LAST_BOUNDARY_OFFSET ))
else
  WINDOW_BYTES=$TOTAL_BYTES
fi

BUDGET_TOKENS=1000000
EST_TOKENS=$(( WINDOW_BYTES / 4 ))
THRESHOLD_TOKENS=$(( BUDGET_TOKENS * 65 / 100 ))

if [ "$EST_TOKENS" -ge "$THRESHOLD_TOKENS" ]; then
  touch "$SENTINEL"
  PCT=$(( EST_TOKENS * 100 / BUDGET_TOKENS ))
  MSG="Context usage is an ESTIMATE of ~${PCT}% (heuristic: transcript bytes since the last compaction boundary / 4 chars-per-token vs a ${BUDGET_TOKENS}-token budget -- not a real token count, no /context call was made). Before continuing with anything else: stop the current task, run the /pre-compact skill now to checkpoint in-flight work (commit/push, convert deferred discoveries into plan todos, write the Deferred work table), then STOP and tell the user to run /compact manually."
  jq -n --arg msg "$MSG" '{hookSpecificOutput: {hookEventName: "UserPromptSubmit", additionalContext: $msg}}'
fi

exit 0
