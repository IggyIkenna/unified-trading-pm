#!/bin/bash
# Script to add basedpyright timeout to all Python repositories
# CRITICAL: This fixes the hanging basedpyright issue across all repos

set -e

# List of Python repositories to update
PYTHON_REPOS=(
    "alerting-system"
    "api-contracts"
    "execution-algo-library"
    "execution-services"
    "features-calendar-service"
    "features-delta-one-service"
    "features-onchain-service"
    "features-volatility-service"
    "market-tick-data-handler"
    "matching-engine-library"
    "ml-inference-service"
    "ml-training-service"
    "mr_report"
    "pnl-attribution-service"
    "position-balance-monitor-service"
    "risk-and-exposure-service"
    "strategy-service"
    "unified-trading-services"
    "unified-config-interface"
    "unified-defi-execution-interface"
    "unified-domain-client"
    "unified-events-interface"
    "unified-market-interface"
    "unified-ml-interface"
    "unified-trade-execution-interface"
    "unified-trading-codex"
    "unified-trading-deployment-v3"
)

echo "Updating basedpyright timeout in Python repositories..."
echo "CRITICAL: This prevents hanging CI builds"
echo ""

for repo in "${PYTHON_REPOS[@]}"; do
    workflow_file="$repo/.github/workflows/quality-gates.yml"
    
    if [ ! -f "$workflow_file" ]; then
        echo "⚠️  Skipping $repo - no quality-gates.yml found"
        continue
    fi
    
    echo "Processing $repo..."
    
    # Check if basedpyright exists in the workflow
    if ! grep -q "basedpyright" "$workflow_file"; then
        echo "⚠️  Skipping $repo - no basedpyright found in workflow"
        continue
    fi
    
    # Check if timeout is already implemented
    if grep -q "timeout.*basedpyright" "$workflow_file"; then
        echo "✅ $repo - timeout already implemented"
        continue
    fi
    
    # Find the source directory name from the workflow
    source_dir=$(grep -o "basedpyright [^/]*/" "$workflow_file" | head -1 | sed 's/basedpyright //' | sed 's|/$||')
    
    if [ -z "$source_dir" ]; then
        echo "❌ $repo - could not determine source directory"
        continue
    fi
    
    # Create backup
    cp "$workflow_file" "$workflow_file.backup"
    
    # Replace the basedpyright section with timeout version
    sed -i.tmp -e '
        /# TYPE CHECK (basedpyright/,/echo "✅ Type check passed"/{
            /# TYPE CHECK (basedpyright/c\
      # ========================================================================\
      # TYPE CHECK (basedpyright - matches IDE strict mode) with TIMEOUT\
      # ========================================================================
            /- name: Type check (basedpyright)/c\
      - name: Type check (basedpyright with timeout)
            /run: |/,/echo "✅ Type check passed"/c\
        run: |\
          # CRITICAL: Use timeout to prevent hangs - basedpyright can hang without it\
          timeout 60 basedpyright '"$source_dir"'/ --level warning || exit_code=$?\
          if [ "${exit_code:-0}" -eq 124 ]; then\
            echo "::error::Basedpyright timed out after 60 seconds"\
            exit 1\
          elif [ "${exit_code:-0}" -ne 0 ]; then\
            echo "::error::Basedpyright failed with exit code $exit_code"\
            exit $exit_code\
          fi\
          echo "✅ Type check passed"
        }
    ' "$workflow_file"
    
    # Remove temporary file
    rm -f "$workflow_file.tmp"
    
    # Verify the change was made
    if grep -q "timeout.*basedpyright" "$workflow_file"; then
        echo "✅ $repo - basedpyright timeout added successfully"
        rm "$workflow_file.backup"
    else
        echo "❌ $repo - failed to add timeout, restoring backup"
        mv "$workflow_file.backup" "$workflow_file"
    fi
done

echo ""
echo "✅ Basedpyright timeout update completed!"
echo ""
echo "CRITICAL CHANGES MADE:"
echo "- Added 60-second timeout to basedpyright in all Python workflows"
echo "- Added proper exit code handling (124 = timeout)"
echo "- Added error messages for timeout and failure cases"
echo ""
echo "This prevents hanging CI builds as required by the audit."