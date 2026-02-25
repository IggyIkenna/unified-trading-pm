#!/bin/bash
set -e

# Cleanup Deprecated UI References
# Created: 2026-02-21
# Purpose: Replace/comment out references to strategy-onboarding-ui and settlement-ui

WORKSPACE_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

echo "Cleanup Deprecated UI References"
echo "=================================="
echo ""
echo "Target UIs:"
echo "  - strategy-onboarding-ui (DEPRECATED - consolidated into onboarding-ui Tab 2)"
echo "  - settlement-ui (PARTIAL - setup workflows moved to onboarding-ui)"
echo ""

# Add deprecation headers to per-service docs
add_deprecation_header() {
  local file="$1"
  local service="$2"
  
  if [ ! -f "$file" ]; then
    echo "  ⚠️  File not found: $file"
    return 1
  fi
  
  # Check if already has deprecation notice
  if head -5 "$file" | grep -q "DEPRECATED\|CONSOLIDATION"; then
    echo "  ✓ Already has deprecation notice"
    return 0
  fi
  
  # Create backup
  cp "$file" "$file.bak"
  
  # Add deprecation notice at top
  if [[ "$service" == "strategy-onboarding-ui" ]]; then
    cat > "$file.tmp" << 'EOF'
> ⚠️ **DEPRECATED (2026-02-21):** This service has been consolidated into `onboarding-ui` Tab 2.  
> See: `11-project-management/epics/onboarding-ui-epic.md`

---

EOF
    cat "$file" >> "$file.tmp"
    mv "$file.tmp" "$file"
    echo "  ✅ Added deprecation notice"
  elif [[ "$service" == "settlement-ui" ]]; then
    cat > "$file.tmp" << 'EOF'
> ⚠️ **PARTIAL CONSOLIDATION (2026-02-21):** Setup workflows moved to `onboarding-ui`.  
> Analysis/reporting features remain in this standalone UI (planned).  
> See: `11-project-management/epics/onboarding-ui-epic.md`

---

EOF
    cat "$file" >> "$file.tmp"
    mv "$file.tmp" "$file"
    echo "  ✅ Added partial consolidation notice"
  fi
}

# Update batch per-service docs
echo "Updating batch per-service docs..."
echo ""

for layer in 01-domain 02-data 03-observability 04-architecture 05-infrastructure; do
  echo "Layer: $layer"
  
  # strategy-onboarding-ui
  file="$WORKSPACE_ROOT/unified-trading-codex/$layer/batch/per-service/strategy-onboarding-ui.md"
  if [ -f "$file" ]; then
    echo "  strategy-onboarding-ui.md"
    add_deprecation_header "$file" "strategy-onboarding-ui"
  fi
  
  # settlement-ui
  file="$WORKSPACE_ROOT/unified-trading-codex/$layer/batch/per-service/settlement-ui.md"
  if [ -f "$file" ]; then
    echo "  settlement-ui.md"
    add_deprecation_header "$file" "settlement-ui"
  fi
  
  echo ""
done

# Update audit files
echo "Updating audit files..."
echo ""

# strategy-onboarding-ui.yaml
audit_file="$WORKSPACE_ROOT/unified-trading-codex/10-audit/batch/strategy-onboarding-ui.yaml"
if [ -f "$audit_file" ] && ! grep -q "status: DEPRECATED" "$audit_file"; then
  echo "  strategy-onboarding-ui.yaml"
  cp "$audit_file" "$audit_file.bak"
  
  # Add deprecated status at top (after service name)
  awk '
    /^service:/ {
      print
      print "status: DEPRECATED  # 2026-02-21 - Consolidated into onboarding-ui Tab 2"
      next
    }
    {print}
  ' "$audit_file.bak" > "$audit_file"
  
  echo "  ✅ Added deprecation status"
fi

# settlement-ui.yaml
audit_file="$WORKSPACE_ROOT/unified-trading-codex/10-audit/batch/settlement-ui.yaml"
if [ -f "$audit_file" ] && ! grep -q "status: PARTIAL_CONSOLIDATION" "$audit_file"; then
  echo "  settlement-ui.yaml"
  cp "$audit_file" "$audit_file.bak"
  
  # Add partial consolidation status
  awk '
    /^service:/ {
      print
      print "status: PARTIAL_CONSOLIDATION  # 2026-02-21 - Setup workflows moved to onboarding-ui"
      next
    }
    {print}
  ' "$audit_file.bak" > "$audit_file"
  
  echo "  ✅ Added partial consolidation status"
fi

echo ""
echo "=================================="
echo "Manual Steps Required:"
echo ""
echo "1. Update .cursorignore (write-protected):"
echo "   Change:"
echo "     !strategy-onboarding-ui"
echo "     !settlement-ui"
echo "   To:"
echo "     # !strategy-onboarding-ui  # DEPRECATED 2026-02-21"
echo "     # !settlement-ui  # PARTIAL CONSOLIDATION 2026-02-21"
echo ""
echo "2. Review updated files:"
echo "   - 10 per-service docs (01-domain through 05-infrastructure)"
echo "   - 2 audit YAML files"
echo ""
echo "3. Backups created as *.bak in each location"
echo ""
echo "Done!"
