#!/bin/bash
# Section Guardian Agent
# Checks internal consistency within a Codex section
# Usage: ./section-guardian-agent.sh <section-number>
# Example: ./section-guardian-agent.sh 06

set -e
WORKSPACE_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
CODEX="$WORKSPACE_ROOT/unified-trading-codex"
SECTION="${1:-06}"

echo "Running Section Guardian for section: $SECTION"
echo ""

ERRORS=0

# Find the section directory
SECTION_DIR=$(find "$CODEX" -maxdepth 1 -type d -name "${SECTION}-*" | head -1)
if [ -z "$SECTION_DIR" ]; then
  echo "ERROR: Section $SECTION not found in $CODEX"
  exit 1
fi

SECTION_NAME=$(basename "$SECTION_DIR")
echo "Section: $SECTION_NAME"
echo "Directory: $SECTION_DIR"
echo ""

# Check 1: No summary/status docs in section
echo "=== Check 1: No summary/status docs ==="
JUNK=$(find "$SECTION_DIR" -name "*_SUMMARY.md" -o -name "*_STATUS.md" -o -name "*_COMPLETE.md" -o -name "*_REPORT.md" 2>/dev/null)
if [ -n "$JUNK" ]; then
  echo "  JUNK docs found:"
  echo "$JUNK"
  ERRORS=$((ERRORS + 1))
else
  echo "  ✅ No junk docs"
fi

# Check 2: README exists
echo ""
echo "=== Check 2: README exists ==="
if [ -f "$SECTION_DIR/README.md" ]; then
  echo "  ✅ README.md present"
else
  echo "  MISSING: README.md"
  ERRORS=$((ERRORS + 1))
fi

# Check 3: No broken internal links (simple check)
echo ""
echo "=== Check 3: Internal link sanity ==="
BROKEN=0
while IFS= read -r file; do
  # Find markdown links and check if target files exist
  while IFS= read -r link; do
    target="${link#./}"
    # Skip URLs, anchors, and external refs
    [[ "$target" =~ ^http ]] && continue
    [[ "$target" =~ ^# ]] && continue
    [[ "$target" =~ ^\.\. ]] && continue
    full_path="$(dirname "$file")/$target"
    if [ ! -f "$full_path" ] && [ ! -d "$full_path" ]; then
      echo "  BROKEN link in $(basename "$file"): $target"
      BROKEN=$((BROKEN + 1))
    fi
  done < <(grep -oE '\[.*?\]\(([^)]+)\)' "$file" 2>/dev/null | sed 's/.*(\(.*\))/\1/' | grep -v "^http" | grep -v "^#" | head -5)
done < <(find "$SECTION_DIR" -maxdepth 2 -name "*.md" | head -20)

if [ $BROKEN -eq 0 ]; then
  echo "  ✅ No broken links detected (sampled)"
else
  echo "  Found $BROKEN broken links"
  ERRORS=$((ERRORS + 1))
fi

echo ""
if [ $ERRORS -eq 0 ]; then
  echo "✅ Section $SECTION_NAME passes all guardian checks"
else
  echo "❌ Section $SECTION_NAME has $ERRORS issues"
  exit 1
fi
