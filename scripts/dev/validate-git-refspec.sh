#!/usr/bin/env bash
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
#
# validate-git-refspec.sh — refuse a refspec whose local (source) side is empty.
# Defense-in-depth against the "unset variable → git push origin :<branch>" class of bug
# (plans/active/issues/live_defi_rollout_branch_has_no_delete_protection_2026_08_09.md).
#
# Usage — validate then push:
#   REFSPEC=$(bash scripts/dev/validate-git-refspec.sh "${MY_SHA}:refs/heads/${BRANCH}") || exit 1
#   git push origin "$REFSPEC"
#
#   # Standalone ref (no colon) passes through unchanged:
#   REFSPEC=$(bash scripts/dev/validate-git-refspec.sh "my-branch") || exit 1
#   git push origin "$REFSPEC"
#
# Exits 0 and echoes the refspec back if valid.
# Exits 1 if the refspec is empty/unset or has an empty local side (would delete the remote ref).

set -euo pipefail

REFSPEC="${1:-}"

if [ -z "$REFSPEC" ]; then
  echo "validate-git-refspec.sh: FATAL — refspec argument is empty or unset" >&2
  echo "  An empty refspec with \`git push origin :<branch>\` DELETES the remote branch." >&2
  echo "  This is likely an unset variable in the caller. Refusing to proceed." >&2
  echo "  Fix: ensure the variable holding the local side of the refspec is set." >&2
  exit 1
fi

# A refspec that starts with ':' has an empty local side — this is a deletion push.
# e.g. ":refs/heads/live-defi-rollout" or just ":"
if [[ "$REFSPEC" =~ ^: ]]; then
  echo "validate-git-refspec.sh: FATAL — refspec '${REFSPEC}' has an empty local (source) side" >&2
  echo "  \`git push origin ${REFSPEC}\` would DELETE the remote ref." >&2
  echo "  The local-side variable in the caller is likely unset. Refusing to proceed." >&2
  exit 1
fi

echo "$REFSPEC"
