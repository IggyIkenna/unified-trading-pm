#!/usr/bin/env bash
# Generate LIBRARY_HARDENING.md in each repo from the template (skip UCS, UCI, UEI).
set -e
WORKSPACE="/Users/ikennaigboaka/Documents/repos/unified-trading-system-repos"
TEMPLATE="$WORKSPACE/.cursor/plans/LIBRARY_PRODUCTION_HARDENING_PROMPT.md"

REPOS=(
  execution-services
  execution-algo-library
  unified-market-interface
  unified-feature-calculator-library
  unified-trade-execution-interface
  unified-trading-deployment-v3
  unified-defi-execution-interface
  unified-domain-services
  matching-engine-library
)

for REPO in "${REPOS[@]}"; do
  DEST="$WORKSPACE/$REPO/LIBRARY_HARDENING.md"
  if [[ ! -d "$WORKSPACE/$REPO" ]]; then
    echo "Skip $REPO (dir not found)"
    continue
  fi
  sed -e "s/{UNIFIED_EVENTS_INTERFACE}/$REPO/g" \
      -e "s/unified cloud servcies/$REPO/g" \
      "$TEMPLATE" > "$DEST"

  # Add new-library note after "## PROMPT TEMPLATE"
  awk '/^## PROMPT TEMPLATE/ { print; print ""; print "**New library:** If this is a new library, document that and any onboarding steps."; print ""; next } 1' "$DEST" > "$DEST.tmp" && mv "$DEST.tmp" "$DEST"

  # UTDv3: add scope note after "## CRITICAL CONTEXT"
  if [[ "$REPO" == "unified-trading-deployment-v3" ]]; then
    awk '/^## CRITICAL CONTEXT: This is a Central Shared Library/ { print; print ""; print "**UTDv3 scope:** This audit is about all deployable services and UIs being represented in configs, terraform, chalice, and data-status. Scope = deployable services and UIs only—libraries (imported as packages) are out of scope."; print ""; next } 1' "$DEST" > "$DEST.tmp" && mv "$DEST.tmp" "$DEST"
  fi
  echo "Wrote $DEST"
done
echo "Done. Generated ${#REPOS[@]} LIBRARY_HARDENING.md files."
