#!/usr/bin/env bash
# Check CLAUDE.md ↔ SUB_AGENT_MANDATORY_RULES.md TOPIC PARITY.
#
# Why: SUB_AGENT_MANDATORY_RULES.md must cover the same TOPICS as CLAUDE.md (one-liner
# density), so a fresh sub-agent always knows a rule exists + where to read it. The two
# files are hand-maintained with no generator linking them, so they drift: a new ##
# topic added to CLAUDE.md silently never reaches sub-agents. This is the deterministic
# tripwire for that drift (the Haiku plan-health agent does the SEMANTIC cross-check —
# CLAUDE.md/SUB_AGENT claims that CONTRADICT an active plan or codex doc).
#
# Heuristic: for every top-level `## ` topic heading in CLAUDE.md, derive its distinctive
# tokens (len ≥5, minus stopwords) and confirm at least one appears in SUB_AGENT. A topic
# with zero token overlap is flagged as MISSING (likely drift). Conservative by design —
# false negatives preferred over noise; the agent catches semantic gaps.
#
# Soft check — exit 0 always (informational); exit 1 only on script error.
# Usage: bash scripts/plan-hygiene/check_claude_subagent_parity.sh [--quiet]

set -euo pipefail
QUIET="${1:-}"
PM_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
CLAUDE="$PM_DIR/cursor-configs/CLAUDE.md"
SUBAGENT="$PM_DIR/cursor-configs/SUB_AGENT_MANDATORY_RULES.md"

if [ ! -f "$CLAUDE" ] || [ ! -f "$SUBAGENT" ]; then
  echo "check_claude_subagent_parity: missing CLAUDE.md or SUB_AGENT_MANDATORY_RULES.md" >&2
  exit 1
fi

# Lowercased sub-agent corpus for membership tests.
SUB_LC="$(tr '[:upper:]' '[:lower:]' < "$SUBAGENT")"

# Container / meta headings that are NOT atomic topics (their children carry the rules),
# plus the file title — excluded so we don't flag umbrellas.
is_excluded() {
  case "$1" in
    "Cross-Cutting Rules"*|"Key Rules"*|"Rules: Read Before Coding"*|"Other key rules"*) return 0;;
    *) return 1;;
  esac
}

STOPWORDS=" the and for with from this that must never always your into over under per via not but are has its before after every each only when then than else only "

MISSING=0
TOTAL=0
MISSING_LIST=""

while IFS= read -r line; do
  # Top-level topics only.
  heading="${line#\#\# }"
  # Strip trailing detail after em-dash / colon / paren to get the key phrase.
  key="${heading%%—*}"; key="${key%%(*}"; key="${key%%:*}"
  key="$(printf '%s' "$key" | tr -d '`*' )"
  [ -z "$key" ] && continue
  is_excluded "$key" && continue
  TOTAL=$(( TOTAL + 1 ))

  # Distinctive tokens: alpha words len ≥5, not stopwords.
  matched=0
  for tok in $(printf '%s' "$key" | tr '[:upper:]' '[:lower:]' | tr -cs 'a-z' ' '); do
    [ "${#tok}" -ge 5 ] || continue
    case "$STOPWORDS" in *" $tok "*) continue;; esac
    case "$SUB_LC" in *"$tok"*) matched=1; break;; esac
  done

  if [ "$matched" -eq 0 ]; then
    MISSING=$(( MISSING + 1 ))
    MISSING_LIST="${MISSING_LIST}  MISSING  ## ${key}"$'\n'
  fi
done < <(grep -E '^## ' "$CLAUDE")

if [ "$QUIET" != "--quiet" ]; then
  echo "CLAUDE.md ↔ SUB_AGENT_MANDATORY_RULES.md topic parity:"
  echo ""
fi

if [ "$MISSING" -gt 0 ]; then
  printf '%s' "$MISSING_LIST"
  echo ""
  echo "⚠️  check_claude_subagent_parity: ${MISSING}/${TOTAL} CLAUDE.md topic(s) have no SUB_AGENT counterpart (drift)"
else
  [ "$QUIET" != "--quiet" ] && echo "✅ check_claude_subagent_parity: all ${TOTAL} CLAUDE.md topics covered in SUB_AGENT (soft check)"
fi

exit 0
