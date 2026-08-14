#!/usr/bin/env bash
#
# Codex Compliance Phase for quality-gates.sh
#
# INSERT THIS BEFORE "FINAL SUMMARY" section
# Add CODEX_STATUS=0 to the "Track overall status" section at the top
#

# ============================================================================
# STEP 4: CODEX COMPLIANCE (Coding Standards)
# ============================================================================
echo -e "\n${BLUE}[4/4] CODEX COMPLIANCE (Coding Standards)${NC}"
echo "----------------------------------------------------------------------"

CODEX_VIOLATIONS=0

# Check: ripgrep (rg) availability
if ! command -v rg &> /dev/null; then
    echo -e "${YELLOW}⚠️  ripgrep (rg) not found - skipping some checks${NC}"
    echo -e "${YELLOW}   Install with: brew install ripgrep (macOS) or apt install ripgrep (Linux)${NC}"
    USE_RG=false
else
    USE_RG=true
fi

# Check 1: print() statements in production code
if [ "$USE_RG" = true ]; then
    echo -n "Checking for print() statements... "
    if rg "print\(" --type py --glob "!tests/**" --glob "!scripts/**" . >/dev/null 2>&1; then
        echo -e "${RED}FAIL${NC}"
        echo -e "${YELLOW}Found print() in production code (use logger.info() instead):${NC}"
        rg "print\(" --type py --glob "!tests/**" --glob "!scripts/**" . | head -5
        CODEX_VIOLATIONS=$((CODEX_VIOLATIONS + 1))
    else
        echo -e "${GREEN}PASS${NC}"
    fi
fi

# Check 2: os.getenv() / os.environ usage (all forms banned — use UnifiedCloudConfig or get_secret_client)
#
# Lines containing `# config-bootstrap:` are intentional exceptions: workspace-
# root discovery, log-level bootstrap, factory selection, and similar early-
# init code paths that MUST run BEFORE UnifiedCloudConfig is loadable. Same
# annotation honored by check_security.py + check_env_canon.py + alerting-
# service main.py + UTL config_interface/_env_bootstrap.py. Files that
# violate without an annotation still fail the gate.
if [ "$USE_RG" = true ]; then
    echo -n "Checking for os.getenv() / os.environ usage... "
    _OS_ENV_HITS=$(rg "os\.getenv|os\.environ" --type py --glob "!tests/**" --glob "!scripts/**" . 2>/dev/null \
        | grep -v "# config-bootstrap:" || true)
    if [ -n "$_OS_ENV_HITS" ]; then
        echo -e "${RED}FAIL${NC}"
        echo -e "${YELLOW}Found os.getenv()/os.environ (use UnifiedCloudConfig for config; get_secret_client() for secrets):${NC}"
        echo "$_OS_ENV_HITS" | head -5
        echo -e "${YELLOW}(annotated lines with '# config-bootstrap: <reason>' are skipped — see precedent in features-*-service/engine/mock_data_provider.py)${NC}"
        CODEX_VIOLATIONS=$((CODEX_VIOLATIONS + 1))
    else
        echo -e "${GREEN}PASS${NC}"
    fi
fi

# Check 3: datetime.now() without UTC
if [ "$USE_RG" = true ]; then
    echo -n "Checking for datetime.now() without UTC... "
    if rg "datetime\.now\(\)" --type py . >/dev/null 2>&1; then
        echo -e "${RED}FAIL${NC}"
        echo -e "${YELLOW}Found datetime.now() (use datetime.now(timezone.utc) instead):${NC}"
        rg "datetime\.now\(\)" --type py . | head -5
        CODEX_VIOLATIONS=$((CODEX_VIOLATIONS + 1))
    else
        echo -e "${GREEN}PASS${NC}"
    fi
fi

# Check 4: Bare except clauses
if [ "$USE_RG" = true ]; then
    echo -n "Checking for bare except clauses... "
    if rg "except:" --type py --glob "!tests/**" . >/dev/null 2>&1; then
        echo -e "${RED}FAIL${NC}"
        echo -e "${YELLOW}Found bare except: (use specific exceptions or @handle_api_errors):${NC}"
        rg "except:" --type py --glob "!tests/**" . | head -5
        CODEX_VIOLATIONS=$((CODEX_VIOLATIONS + 1))
    else
        echo -e "${GREEN}PASS${NC}"
    fi
fi

# Check 5: requests library in async code
if [ "$USE_RG" = true ]; then
    echo -n "Checking for requests library in async code... "
    HAS_REQUESTS=$(rg "import\s+requests" --type py . 2>/dev/null | wc -l | tr -d ' ')
    HAS_ASYNC=$(rg "async\s+def" --type py . 2>/dev/null | wc -l | tr -d ' ')
    if [ "${HAS_REQUESTS:-0}" -gt 0 ] && [ "${HAS_ASYNC:-0}" -gt 0 ]; then
        echo -e "${RED}FAIL${NC}"
        echo -e "${YELLOW}Found requests library with async code (use aiohttp instead):${NC}"
        rg "import\s+requests" --type py . | head -3
        CODEX_VIOLATIONS=$((CODEX_VIOLATIONS + 1))
    else
        echo -e "${GREEN}PASS${NC}"
    fi
fi

# Check 6: asyncio.run() in loops (simplified check)
#
# Excludes tests/ + scripts/ — these are one-shot entry-points where
# asyncio.run() at the END of main() is the correct pattern (file
# co-existing with `for`/`while` keywords used elsewhere in helper
# functions or imports must NOT be flagged). Service runtime code
# (everything outside tests/ + scripts/) should use asyncio.gather()
# inside an async runtime, not asyncio.run() — those failures still
# fire as before.
if [ "$USE_RG" = true ]; then
    echo -n "Checking for asyncio.run() in loops... "
    FILES_WITH_ASYNCIO_RUN=$(rg "asyncio\.run\(" --type py \
        --glob "!tests/**" --glob "!scripts/**" --glob "!examples/**" --files-with-matches . 2>/dev/null || true)
    if [ -n "$FILES_WITH_ASYNCIO_RUN" ]; then
        _hit=""
        for file in $FILES_WITH_ASYNCIO_RUN; do
            if grep -q "for \|while " "$file" 2>/dev/null; then
                _hit="$file"
                break
            fi
        done
        if [ -n "$_hit" ]; then
            echo -e "${YELLOW}WARN${NC}"
            echo -e "${YELLOW}Found asyncio.run() in file with loops (verify not in loop - use asyncio.gather() instead):${NC}"
            echo "  $_hit"
            CODEX_VIOLATIONS=$((CODEX_VIOLATIONS + 1))
        else
            echo -e "${GREEN}PASS${NC}"
        fi
    else
        echo -e "${GREEN}PASS${NC}"
    fi
fi

# Check 7: time.sleep() in async functions (simplified check)
#
# Same exclusions as asyncio.run() — tests/ + scripts/ + examples/ are
# one-shot entry points where time.sleep() is fine. Service runtime
# (everything else) should use asyncio.sleep() inside async funcs.
if [ "$USE_RG" = true ]; then
    echo -n "Checking for time.sleep() in async code... "
    FILES_WITH_TIME_SLEEP=$(rg "time\.sleep\(" --type py \
        --glob "!tests/**" --glob "!scripts/**" --glob "!examples/**" --files-with-matches . 2>/dev/null || true)
    if [ -n "$FILES_WITH_TIME_SLEEP" ]; then
        _hit=""
        for file in $FILES_WITH_TIME_SLEEP; do
            if grep -q "async def" "$file" 2>/dev/null; then
                _hit="$file"
                break
            fi
        done
        if [ -n "$_hit" ]; then
            echo -e "${YELLOW}WARN${NC}"
            echo -e "${YELLOW}Found time.sleep() in file with async functions (verify not in async - use asyncio.sleep() instead):${NC}"
            echo "  $_hit"
            CODEX_VIOLATIONS=$((CODEX_VIOLATIONS + 1))
        else
            echo -e "${GREEN}PASS${NC}"
        fi
    else
        echo -e "${GREEN}PASS${NC}"
    fi
fi

# Check 8: Domain contracts in service source (must live in UIC domain/<service>/)
# SchemaDefinition/ColumnSchema in output_schemas.py is allowed — it's parquet infra, not a data contract
if [ "$USE_RG" = true ]; then
    echo -n "Checking for domain data contracts defined locally in service source... "
    DOMAIN_LOCAL=$(rg 'class \w+\(BaseModel\)|class \w+\(TypedDict\)' --type py \
        --glob "!tests/**" --glob "!**/output_schemas.py" --glob "!**/__init__.py" \
        . 2>/dev/null | grep -v '\.venv' || true)
    if [ -n "$DOMAIN_LOCAL" ]; then
        echo -e "${YELLOW}WARN${NC}"
        echo -e "${YELLOW}Domain contracts found in service source — should live in unified_api_contracts.internal domain/<service>/${NC}"
        echo -e "${YELLOW}See: 02-data/schema-governance.md, plans/archive/SCHEMA_CONTRACTS_AUDIT.md Section 3b${NC}"
        echo "$DOMAIN_LOCAL" | head -5
        # Warning only until existing violations are remediated per Plan #0c
    else
        echo -e "${GREEN}PASS${NC}"
    fi
fi

# STEP 5.10 — Block direct cloud SDK imports outside UCI providers
if [ "$USE_RG" = true ]; then
    echo -n "STEP 5.10: Checking for direct cloud SDK imports... "
    CLOUD_SDK_VIOLATIONS=$(rg "^from google\.cloud|^import boto3|^import botocore" \
        --type py \
        --glob '!.venv*' --glob '!**/.venv*/**' \
        --glob '!tests' \
        --glob '!unified_cloud_interface/providers/**' \
        -l . 2>/dev/null || true)
    if [ -n "$CLOUD_SDK_VIOLATIONS" ]; then
        echo -e "${RED}FAIL${NC}"
        echo -e "${YELLOW}Found direct cloud SDK imports (use unified_cloud_interface instead):${NC}"
        echo "$CLOUD_SDK_VIOLATIONS" | head -5
        CODEX_VIOLATIONS=$((CODEX_VIOLATIONS + 1))
    else
        echo -e "${GREEN}PASS${NC}"
    fi
fi

# STEP 5.11 — Block protocol-specific symbols in service code
if [ "$USE_RG" = true ]; then
    echo -n "STEP 5.11: Checking for protocol-specific symbols in service code... "
    PROTOCOL_VIOLATIONS=$(rg "CloudTarget|upload_to_gcs_batch|gcs_bucket|bigquery_dataset|StandardizedDomainCloudService" \
        --type py \
        --glob '!.venv*' --glob '!**/.venv*/**' \
        --glob '!tests' \
        -l . 2>/dev/null || true)
    if [ -n "$PROTOCOL_VIOLATIONS" ]; then
        echo -e "${RED}FAIL${NC}"
        echo -e "${YELLOW}Found protocol-specific symbols. Use get_data_sink() / get_event_bus() from UCI instead:${NC}"
        echo "$PROTOCOL_VIOLATIONS" | head -5
        CODEX_VIOLATIONS=$((CODEX_VIOLATIONS + 1))
    else
        echo -e "${GREEN}PASS${NC}"
    fi
fi

# STEP 5.12 — Services must not hardcode cloud protocol names
if [ "$USE_RG" = true ]; then
    echo -n "STEP 5.12: Checking for hardcoded protocol names in service source... "
    HARDCODED_PROTO=$(rg \
      'gcs_bucket\s*=|bigquery_dataset\s*=|upload_to_gcs|CloudTarget\b|StandardizedDomainCloudService\b' \
      --type py \
      --glob '!.venv*' --glob '!**/.venv*/**' \
      --glob '!tests' \
      --glob '!scripts/**' \
      -l . 2>/dev/null || true)
    if [ -n "$HARDCODED_PROTO" ]; then
        echo -e "${RED}FAIL${NC}"
        echo -e "${YELLOW}Hardcoded protocol/cloud names in service source (use get_data_sink/get_event_bus):${NC}"
        echo "$HARDCODED_PROTO" | head -5
        CODEX_VIOLATIONS=$((CODEX_VIOLATIONS + 1))
    else
        echo -e "${GREEN}PASS${NC}"
    fi
fi

# STEP 5.13 — Schema canonical name collision (advisory)
# CODEX: cursor-rules/core/schema-governance-index.mdc, 02-data/schema-governance.md
if [ "$USE_RG" = true ]; then
    echo -n "STEP 5.13: Checking for Canonical* BaseModel name collisions in service source... "
    SCHEMA_COLLISION=$(rg 'class\s+Canonical[A-Z]\w+\s*\(' \
      --type py \
      --glob '!.venv*' --glob '!**/.venv*/**' \
      --glob '!tests' \
      -l . 2>/dev/null | grep -v 'unified_api_contracts\|unified_internal_contracts' || true)
    if [ -n "$SCHEMA_COLLISION" ]; then
        echo -e "${YELLOW}WARN${NC}"
        echo -e "${YELLOW}Canonical* BaseModel in service source — potential collision with UAC/UIC canonical types:${NC}"
        echo "$SCHEMA_COLLISION" | head -5
        echo -e "${YELLOW}See: cursor-rules/core/schema-governance-index.mdc Rule 5${NC}"
    else
        echo -e "${GREEN}PASS${NC}"
    fi
fi

# Summary
if [ $CODEX_VIOLATIONS -eq 0 ]; then
    echo -e "\n${GREEN}✅ Codex compliance PASSED${NC}"
    CODEX_STATUS=0
else
    echo -e "\n${RED}❌ Codex compliance FAILED: $CODEX_VIOLATIONS violations${NC}"
    echo -e "${YELLOW}See: unified-trading-pm/codex/06-coding-standards/README.md${NC}"
    CODEX_STATUS=1
fi

# Hard-fail: callers that source this snippet must check CODEX_STATUS and exit 1 if non-zero.
# Standalone invocation guard: if this snippet is run directly (not sourced), exit with CODEX_STATUS.
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    exit "$CODEX_STATUS"
fi
