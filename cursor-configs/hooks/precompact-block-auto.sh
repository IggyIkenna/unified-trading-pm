#!/usr/bin/env bash
# PreCompact hook (matcher: auto): hard safety-net backstop. Unconditionally
# blocks automatic compaction so it can never proceed silently. Manual /compact
# is unaffected -- this only runs when compaction_reason == "auto".
set -euo pipefail

INPUT="$(cat)"
REASON="$(printf '%s' "$INPUT" | jq -r '.compaction_reason // empty')"

if [ "$REASON" = "auto" ]; then
  echo "Automatic compaction blocked (safety-net hook). Run the /pre-compact skill to checkpoint in-flight work, then run /compact manually." >&2
  exit 2
fi

exit 0
