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
#
# REAL USAGE PREFERRED OVER THE BYTE HEURISTIC (2026-08-03): the byte/4
# estimate has no visibility into the harness's own internal context
# management, which can prune/summarize old large tool outputs out of the
# LIVE model context without emitting a compact_boundary event -- so raw
# transcript bytes can run well above real usage on any session with heavy
# tool-output volume. Confirmed live: a session with 8 parallel sub-agent
# reports + repeated large system-reminder dumps false-triggered this nudge
# (byte heuristic read >=65%) when the transcript's OWN recorded
# message.usage fields put real usage at ~29% -- matching the operator's
# independent reading almost exactly. Every assistant-turn transcript line
# already carries message.usage.{input_tokens,cache_creation_input_tokens,
# cache_read_input_tokens} -- the exact token count the API reports for that
# turn's input, ground truth with no estimation needed (sub-agent/Task-tool
# transcripts are NOT a factor -- confirmed they live in entirely separate
# files, never merged into the main transcript: zero "isSidechain":true
# lines on the reproducing session). Use the LAST such value in the
# transcript as EST_TOKENS; fall back to the byte/4 heuristic only when no
# assistant-turn usage data exists yet (e.g. a freshly-started session).
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
# is pre-compaction history no longer in the live context window. `grep` exits
# 1 (not an error -- just "no match") for any session that hasn't compacted
# yet, which is the common case; under `set -o pipefail` that non-zero status
# propagates as the pipeline's exit code and `set -e` would abort the WHOLE
# hook right here on every such prompt submission ("UserPromptSubmit hook
# error", confirmed live 2026-07-26 -- reproduced standalone with a realistic
# uncompacted-session transcript). `|| true` makes "no compaction boundary
# found yet" the expected, non-fatal outcome it actually is.
LAST_BOUNDARY_OFFSET=$(grep -abo '"subtype":"compact_boundary"' "$TRANSCRIPT_PATH" 2>/dev/null | tail -1 | cut -d: -f1 || true)

if [ -n "$LAST_BOUNDARY_OFFSET" ]; then
  WINDOW_BYTES=$(( TOTAL_BYTES - LAST_BOUNDARY_OFFSET ))
else
  WINDOW_BYTES=$TOTAL_BYTES
fi

# Last assistant-turn's real usage, if any turn has completed yet. `grep`
# exits 1 (no match, not an error) on a session with no assistant turn yet --
# `|| true` makes that the expected outcome, same reasoning as the
# compact_boundary grep above.
LAST_USAGE_LINENO=$(grep -n '"cache_read_input_tokens"' "$TRANSCRIPT_PATH" 2>/dev/null | tail -1 | cut -d: -f1 || true)
REAL_TOKENS=""
if [ -n "$LAST_USAGE_LINENO" ]; then
  REAL_TOKENS=$(sed -n "${LAST_USAGE_LINENO}p" "$TRANSCRIPT_PATH" | jq -r '
    (.message.usage // empty) as $u
    | if $u then (($u.input_tokens // 0) + ($u.cache_creation_input_tokens // 0) + ($u.cache_read_input_tokens // 0)) else empty end
  ' 2>/dev/null || true)
fi

BUDGET_TOKENS=1000000
THRESHOLD_TOKENS=$(( BUDGET_TOKENS * 65 / 100 ))

if [ -n "$REAL_TOKENS" ] && [ "$REAL_TOKENS" -gt 0 ] 2>/dev/null; then
  EST_TOKENS="$REAL_TOKENS"
  SOURCE="measured"
else
  EST_TOKENS=$(( WINDOW_BYTES / 4 ))
  SOURCE="estimated"
fi

if [ "$EST_TOKENS" -ge "$THRESHOLD_TOKENS" ]; then
  touch "$SENTINEL"
  PCT=$(( EST_TOKENS * 100 / BUDGET_TOKENS ))
  if [ "$SOURCE" = "measured" ]; then
    MSG="Context usage is MEASURED at ~${PCT}% (real usage.input_tokens+cache_creation_input_tokens+cache_read_input_tokens from the last transcript turn vs a ${BUDGET_TOKENS}-token budget). Before continuing with anything else: stop the current task, run the /pre-compact skill now to checkpoint in-flight work (commit/push, convert deferred discoveries into plan todos, write the Deferred work table), then STOP and tell the user to run /compact manually."
  else
    MSG="Context usage is an ESTIMATE of ~${PCT}% (heuristic: transcript bytes since the last compaction boundary / 4 chars-per-token vs a ${BUDGET_TOKENS}-token budget -- no assistant-turn usage data found yet, so no real token count was available). Before continuing with anything else: stop the current task, run the /pre-compact skill now to checkpoint in-flight work (commit/push, convert deferred discoveries into plan todos, write the Deferred work table), then STOP and tell the user to run /compact manually."
  fi
  jq -n --arg msg "$MSG" '{hookSpecificOutput: {hookEventName: "UserPromptSubmit", additionalContext: $msg}}'
fi

exit 0
