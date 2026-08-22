#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# Delete corrupt files at iCloud per ICLOUD_CORRUPT_FILES_MIGRATION_REPORT.md
# Run BEFORE any rsync/copy — copying corrupt files (0 blocks, size>0) will HANG.
# Usage: ./delete-corrupt-files-at-icloud.sh [ICLOUD_WORKSPACE_ROOT]

set -euo pipefail

ICLOUD_ROOT="${1:-$HOME/Library/Mobile Documents/com~apple~CloudDocs/Documents/Documents - Mac/repos/unified-trading-system-repos}"
REPORT="$ICLOUD_ROOT/unified-trading-pm/ICLOUD_CORRUPT_FILES_MIGRATION_REPORT.md"

if [[ ! -f "$REPORT" ]]; then
  echo "ERROR: Report not found: $REPORT"
  echo "Usage: $0 [ICLOUD_WORKSPACE_ROOT]"
  exit 1
fi

cd "$ICLOUD_ROOT"
echo "Working from: $(pwd)"
echo "Parsing report: $REPORT"

# Extract paths: lines like "- \`./path/to/file\`" — strip "- \`" and trailing "\`"
count=0
deleted=0
while IFS= read -r line; do
  if [[ "$line" =~ ^-\ \`\./(.+)\` ]]; then
    rel="${BASH_REMATCH[1]}"
    ((count++)) || true
    if [[ -e "$rel" ]]; then
      rm -f "$rel"
      ((deleted++)) || true
      echo "Deleted: $rel"
    else
      echo "Skip (not found): $rel"
    fi
  fi
done < <(grep -E '^-\ `\./' "$REPORT" || true)

echo "---"
echo "Parsed: $count paths, deleted: $deleted files"

# Verify: re-run corrupt scan
echo "Verifying (corrupt scan)..."
remaining=$(find . -type f -exec stat -f "%b %z %N" {} \; 2>/dev/null | awk '$1==0 && $2>0 {print $3}' | wc -l | tr -d ' ')
echo "Remaining corrupt files: $remaining"
if [[ "$remaining" -gt 0 ]]; then
  echo "WARNING: $remaining corrupt files still present. Run again or check paths."
  exit 1
fi
echo "SUCCESS: Zero corrupt files remaining."
