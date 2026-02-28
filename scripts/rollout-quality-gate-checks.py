#!/usr/bin/env python3
"""
rollout-quality-gate-checks.py

Adds missing coding-standard and security checks to quality-gates.sh
across all service and library repos. Safe to re-run (idempotent).

Usage:
    python3 scripts/rollout-quality-gate-checks.py [--dry-run] [--repo <name>]
"""

import argparse
from pathlib import Path

WORKSPACE = Path(__file__).parent.parent.parent

# ── Repos to update ───────────────────────────────────────────────────────────
SERVICE_REPOS = [
    "instruments-service",
    "market-tick-data-handler",
    "market-data-processing-service",
    "features-calendar-service",
    "features-delta-one-service",
    "features-volatility-service",
    "features-onchain-service",
    "ml-training-service",
    "ml-inference-service",
    "strategy-service",
    "execution-service",
    "alerting-service",
    "pnl-attribution-service",
    "position-balance-monitor-service",
    "risk-and-exposure-service",
]

LIBRARY_REPOS = [
    "unified-trading-services",
    "unified-config-interface",
    "unified-events-interface",
    "unified-domain-client",
    "unified-market-interface",
    "unified-trade-execution-interface",
    "unified-ml-interface",
    "unified-defi-execution-interface",
    "unified-feature-calculator-library",
    "execution-algo-library",
    "matching-engine-library",
]

INFRA_REPOS = [
    "api-contracts",
    "alerting-service",
]

ALL_REPOS = SERVICE_REPOS + LIBRARY_REPOS + INFRA_REPOS

# ── Checks to add ─────────────────────────────────────────────────────────────
# Each entry: (sentinel string to detect presence, anchor to insert after, code to insert)
# Insertion happens AFTER the line matching `anchor`.

CHECKS = [
    # ── Existing checks already in template (verify idempotently) ────────────
    {
        "id": "GOOGLE_CLOUD_PROJECT",
        "sentinel": "GOOGLE_CLOUD_PROJECT",
        "anchor": 'log_success "No hardcoded project ID in production"',
        "code": '''
# GOOGLE_CLOUD_PROJECT is legacy — only GCP_PROJECT_ID is canonical
rg "GOOGLE_CLOUD_PROJECT" --type py --glob "!tests/**" --glob "!**/config.py" "$SOURCE_DIR/" 2>/dev/null \\
    && { log_fail "Use GCP_PROJECT_ID not GOOGLE_CLOUD_PROJECT (except config.py backward compat)"; ((V++)); } || log_success "No GOOGLE_CLOUD_PROJECT usage"''',
    },
    {
        "id": "EVENT_LOGGING_OLD",
        "sentinel": "unified_trading_services.*log_event|setup_cloud_logging|EL_OLD",
        "anchor": 'log_success "No GOOGLE_CLOUD_PROJECT usage"',
        "code": '''
# Old event logging pattern — must use unified_events_interface directly
EL_OLD=$(rg "from unified_trading_services[. ].*(log_event|setup_events|setup_cloud_logging|observability)" --type py --glob "!tests/**" "$SOURCE_DIR/" 2>/dev/null || true)
[[ -n "$EL_OLD" ]] && { log_fail "Old event logging import — use 'from unified_events_interface import ...'"; echo "$EL_OLD" | head -3; ((V++)); } || log_success "Event logging imports from unified_events_interface"''',
    },
    {
        "id": "PIP_VS_UV",
        "sentinel": "uv pip install.*not.*pip install|pip install.*uv|No bare pip",
        "anchor": 'log_success "Event logging imports from unified_events_interface"',
        "code": '''
# pip install anywhere other than bootstrap (must use uv pip install)
PIP=$(rg "^RUN pip install|^RUN python -m pip| pip install " --glob "**/Dockerfile" --glob "**/*.sh" . 2>/dev/null \\
    | grep -v "pip install uv" | grep -v "#" || true)
[[ -n "$PIP" ]] && { log_fail "Use 'uv pip install' not 'pip install'"; echo "$PIP" | head -3; ((V++)); } || log_success "No bare pip install"''',
    },
    {
        "id": "SWALLOWED_ERRORS",
        "sentinel": "SWALLOWED|Swallowed errors",
        "anchor": 'log_success "No broad except Exception"',
        "code": '''
# Swallowed errors — except that silently passes/returns None
SWALLOWED=$(rg "except Exception:" --type py --glob "!tests/**" "$SOURCE_DIR/" -A 2 2>/dev/null \\
    | grep -E "^[[:space:]]+(pass|return None)$" || true)
[[ -n "$SWALLOWED" ]] && { log_fail "Swallowed errors — use @handle_api_errors or re-raise"; ((V++)); } || log_success "No swallowed errors"''',
    },
    # ── Security checks ───────────────────────────────────────────────────────
    {
        "id": "SERVICE_ACCOUNT_JSON",
        "sentinel": "service_account.*SA_JSON|private_key_id",
        "anchor": 'log_success "No hardcoded project ID in production"',
        "code": '''
# Security: no service account JSON files committed or referenced by path
SA_JSON=$(rg '"type"\\s*:\\s*"service_account"|"private_key_id"' --glob "*.json" . 2>/dev/null \\
    | grep -v ".venv\\|node_modules" || true)
[[ -n "$SA_JSON" ]] && { log_fail "Service account JSON detected — use Secret Manager via UCS"; echo "$SA_JSON" | head -3; ((V++)); } || log_success "No service account JSON"''',
    },
    {
        "id": "PRIVATE_KEY",
        "sentinel": "BEGIN RSA PRIVATE KEY|BEGIN PRIVATE KEY|PRIV_KEY",
        "anchor": 'log_success "No service account JSON"',
        "code": '''
# Security: no private keys embedded in code
PRIV_KEY=$(rg "BEGIN RSA PRIVATE KEY|BEGIN PRIVATE KEY|BEGIN EC PRIVATE KEY" \\
    --type py --type sh --type yaml --glob "!tests/**" . 2>/dev/null || true)
[[ -n "$PRIV_KEY" ]] && { log_fail "Private key in codebase — use Secret Manager"; echo "$PRIV_KEY" | head -3; ((V++)); } || log_success "No embedded private keys"''',
    },
    {
        "id": "DOCKERFILE_ENV_SECRETS",
        "sentinel": "DOCKER_SECRETS|Secrets in Dockerfile ENV",
        "anchor": 'log_success "No embedded private keys"',
        "code": '''
# Security: no secrets in Dockerfile ENV statements
DOCKER_SECRETS=$(rg "^ENV\\s+[A-Z_]*(KEY|SECRET|PASSWORD|TOKEN|CREDENTIAL)[A-Z_]*\\s*=" \\
    --glob "**/Dockerfile*" . 2>/dev/null | grep -v "#" || true)
[[ -n "$DOCKER_SECRETS" ]] && { log_fail "Secrets in Dockerfile ENV — pass at runtime via Secret Manager"; echo "$DOCKER_SECRETS" | head -3; ((V++)); } || log_success "No secrets in Dockerfile ENV"''',
    },
    {
        "id": "GITIGNORE_CREDENTIALS",
        "sentinel": "gitignore.*cred|CRED_EXCLUDED",
        "anchor": 'log_success "No secrets in Dockerfile ENV"',
        "code": """
# Security: .gitignore must exclude credential JSON patterns
if [[ -f ".gitignore" ]]; then
    CRED_EXCLUDED=$(grep -E "credentials.*\\.json|\\*service.account\\*|\\*\\.key\\.json" .gitignore 2>/dev/null | head -1 || true)
    [[ -z "$CRED_EXCLUDED" ]] && { log_warn ".gitignore missing credential exclusion pattern (e.g. *credentials*.json)"; } || log_success ".gitignore excludes credential files"
fi""",
    },
    # ── Test quality checks ───────────────────────────────────────────────────
    {
        "id": "DUPLICATE_TESTS",
        "sentinel": "test_.*extended|DUP.*test|duplicate test",
        "anchor": 'log_success "Required test files present"',
        "code": '''
    # No duplicate test files (test_*_extended.py, test_*_additional.py)
    DUP=$(find tests/ -name "test_*_extended.py" -o -name "test_*_additional.py" 2>/dev/null | head -5 || true)
    [[ -n "$DUP" ]] && { log_fail "Duplicate test files — expand existing files instead:"; echo "$DUP"; exit 1; }
    log_success "No duplicate test files"

    # @pytest.mark.skip must have a reason comment on the preceding line
    SKIP_NO_REASON=$(rg "@pytest\\.mark\\.skip" --type py tests/ -B 1 2>/dev/null \\
        | grep -v "# reason:\\|# noqa\\|^--" | grep "@pytest\\.mark\\.skip" || true)
    [[ -n "$SKIP_NO_REASON" ]] && { log_fail "pytest.mark.skip without reason — add '# reason: ...' above"; echo "$SKIP_NO_REASON" | head -3; exit 1; }
    log_success "All pytest.mark.skip have reason comments"''',
    },
    # ── CI/CD hygiene ─────────────────────────────────────────────────────────
    {
        "id": "BYPASS_TRUE",
        "sentinel": r"\\|\\|true.*bypass|BYPASS.*true",
        "anchor": 'log_success "Codex compliance PASSED"',
        "code": '''
# CI/CD hygiene: ||true bypasses in quality gate scripts
BYPASS=$(rg "\\|\\|true|\\|\\| true" --glob "**/quality-gates.sh" --glob "**/quality-gates.yml" . 2>/dev/null \\
    | grep -v "^#\\|zombies\\|pyright\\|cleanup" || true)
[[ -n "$BYPASS" ]] && { log_fail "||true bypass in quality gates — fix the root cause"; echo "$BYPASS" | head -3; ((V++)); } || log_success "No ||true quality gate bypasses"''',
    },
    # ── id_conventions: must come from unified-config-interface, not UCS ─────
    {
        "id": "ID_CONVENTIONS_UCS",
        "sentinel": "ID_CONVENTIONS_UCS|id_conventions.*unified_trading_services|generate_strategy_id.*from unified_trading_services",
        "anchor": 'log_success "No ||true quality gate bypasses"',
        "code": r'''
# ID conventions (generate_strategy_id, generate_config_id, etc.) live in unified-config-interface
ID_CONV=$(rg 'from unified_trading_services import[^#]*?(generate_strategy_id|generate_config_id|parse_strategy_id|parse_config_id|validate_strategy_id|validate_config_id|get_gcs_config_path|get_execution_bucket|get_strategy_bucket|CATEGORIES|MODES|TIMEFRAMES)' \
    --type py "$SOURCE_DIR/" 2>/dev/null || true)
[[ -n "$ID_CONV" ]] && { log_fail "ID convention functions must come from unified_config_interface, not unified_trading_services"; echo "$ID_CONV" | head -3; ((V++)); } || log_success "ID convention imports from unified_config_interface"''',
    },
    # ── security module: deleted — use UEI log_event instead ─────────────────
    {
        "id": "UCS_SECURITY_IMPORT",
        "sentinel": "UCS_SECURITY|unified_trading_services.*security|security.*unified_trading_services",
        "anchor": 'log_success "ID convention imports from unified_config_interface"',
        "code": r'''
# unified_trading_services.security module was deleted Feb 2026 — use log_event() from unified_events_interface
SEC=$(rg 'from unified_trading_services.*security|from unified_trading_services import.*[Aa]uth[Ff]ailure|SecurityLogger|config_change_logger|secret_access_logger' \
    --type py "$SOURCE_DIR/" 2>/dev/null || true)
[[ -n "$SEC" ]] && { log_fail "unified_trading_services.security is deleted — use log_event('AUTH_FAILURE', ...) from unified_events_interface"; echo "$SEC" | head -3; ((V++)); } || log_success "No deleted security module imports"''',
    },
    # ── Domain layer: Service→UDS→UCS boundary ────────────────────────────────
    {
        "id": "UCS_DOMAIN_IMPORT",
        "sentinel": "UCS_DOMAIN|Domain clients must come from unified_domain_client",
        "anchor": 'log_success "No ||true quality gate bypasses"',
        "code": r'''
# Domain clients must come from unified_domain_client, not unified_trading_services
UCS_DOMAIN=$(rg 'from unified_trading_services import[^#]*?(InstrumentsDomainClient|ExecutionDomainClient|MarketCandleDataDomainClient|MarketTickDataDomainClient|create_instruments_client|create_execution_client|create_features_client|create_market_candle_data_client|create_market_tick_data_client)' \
    --type py --glob "!tests/**" "$SOURCE_DIR/" 2>/dev/null || true)
[[ -n "$UCS_DOMAIN" ]] && { log_fail "Domain clients must come from unified_domain_client, not unified_trading_services"; echo "$UCS_DOMAIN" | head -5; ((V++)); } || log_success "Domain clients imported from unified_domain_client"''',
    },
    # ── GCP auth: ADC pattern enforcement ─────────────────────────────────────
    {
        "id": "GCP_AUTH_CREDENTIAL_FILE_SKIP",
        "sentinel": "BAD_AUTH_SKIP|credential-file skip|No credential-file skip",
        "anchor": 'log_success "No ||true quality gate bypasses"',
        "code": r'''
# GCP auth: tests must use google.auth.default() — never pytest.skip for missing credential file
BAD_AUTH_SKIP=$(rg 'pytest\.skip.*[Cc]redential|pytest\.skip.*GOOGLE_APPLICATION_CREDENTIALS|if not.*gcp_credentials.*pytest\.skip|if not.*cred_file.*pytest\.skip' \
    --type py tests/ 2>/dev/null \
    | grep -v "_skip_integration_without_creds\|No GCP credentials.*skipping integration\|No GCP credentials.*skipping Secret Manager\|Could not create/access" \
    || true)
[[ -n "$BAD_AUTH_SKIP" ]] && { log_fail "Tests skip due to missing credential file — use google.auth.default() + @pytest.mark.integration instead"; echo "$BAD_AUTH_SKIP" | head -5; ((V++)); } || log_success "No credential-file skip patterns in tests"''',
    },
    {
        "id": "GCP_AUTH_ENV_EXAMPLE",
        "sentinel": "GOOGLE_APPLICATION_CREDENTIALS.*\\.env\\.example|No GOOGLE_APPLICATION_CREDENTIALS in .env.example",
        "anchor": 'log_success "No credential-file skip patterns in tests"',
        "code": r'''
# .env.example must not contain GOOGLE_APPLICATION_CREDENTIALS (use ADC / GH token / Cloud SA)
[[ -f ".env.example" ]] && rg "GOOGLE_APPLICATION_CREDENTIALS" .env.example 2>/dev/null \
    && { log_fail ".env.example contains GOOGLE_APPLICATION_CREDENTIALS — remove it (use ADC)"; ((V++)); } || log_success "No GOOGLE_APPLICATION_CREDENTIALS in .env.example"''',
    },
]


def file_has_check(content: str, sentinel: str) -> bool:
    """Check if a sentinel pattern already exists in the file."""
    import re

    return bool(re.search(sentinel, content, re.IGNORECASE))


def insert_after_anchor(content: str, anchor: str, code: str) -> str:
    """Insert code after the first line containing anchor string."""
    lines = content.split("\n")
    for i, line in enumerate(lines):
        if anchor in line:
            lines.insert(i + 1, code)
            return "\n".join(lines)
    # Anchor not found — append before final summary
    print(f"    ⚠ anchor not found: '{anchor}' — appending before final block")
    # Find the codex compliance pass line or last V check
    for i, line in enumerate(lines):
        if "Codex compliance PASSED" in line or "CODEX_VIOLATIONS" in line and "PASSED" in line:
            lines.insert(i, code + "\n")
            return "\n".join(lines)
    lines.append(code)
    return "\n".join(lines)


def update_repo(repo_path: Path, dry_run: bool) -> dict:
    """Update quality-gates.sh in a repo. Returns status dict."""
    qg_path = repo_path / "scripts" / "quality-gates.sh"
    if not qg_path.exists():
        return {"repo": repo_path.name, "status": "SKIP", "reason": "no quality-gates.sh"}

    content = qg_path.read_text(encoding="utf-8")
    original = content
    added = []
    skipped = []

    # Normalize V counter variable (some repos use CODEX_VIOLATIONS instead of V)
    uses_codex_violations = "CODEX_VIOLATIONS" in content and "((V++))" not in content

    for check in CHECKS:
        if file_has_check(content, check["sentinel"]):
            skipped.append(check["id"])
            continue

        code = check["code"]
        # Adapt counter variable
        if uses_codex_violations:
            code = code.replace("((V++))", "((CODEX_VIOLATIONS++))")

        # Find anchor — try exact, then fuzzy
        anchor = check["anchor"]
        if anchor not in content:
            # Try stripping log_success wrapper
            alt = anchor.replace('log_success "', "").rstrip('"')
            found = False
            for line in content.split("\n"):
                if alt in line:
                    anchor = line.strip()
                    found = True
                    break
            if not found:
                print(f"    ⚠ {check['id']}: anchor missing, will append")

        content = insert_after_anchor(content, anchor, code)
        added.append(check["id"])

    if content == original:
        return {"repo": repo_path.name, "status": "UP_TO_DATE", "added": [], "skipped": skipped}

    if not dry_run:
        qg_path.write_text(content, encoding="utf-8")

    return {"repo": repo_path.name, "status": "DRY_RUN" if dry_run else "UPDATED", "added": added, "skipped": skipped}


def update_basedpyright(repo_path: Path, dry_run: bool) -> str:
    """Add reportAny + reportUnknown* to [tool.basedpyright] if missing."""
    pyproject = repo_path / "pyproject.toml"
    if not pyproject.exists():
        return "no pyproject.toml"

    content = pyproject.read_text(encoding="utf-8")
    if "reportAny" in content:
        return "already set"

    # Find [tool.basedpyright] section and append settings
    if "[tool.basedpyright]" not in content:
        return "no [tool.basedpyright] section"

    addition = (
        "# Enforce no Any/object — use specific types\n"
        'reportAny = "warning"\n'
        'reportUnknownVariableType = "warning"\n'
        'reportUnknownParameterType = "warning"\n'
        'reportUnknownMemberType = "warning"\n'
    )

    # Insert after [tool.basedpyright] header
    new_content = content.replace(
        "[tool.basedpyright]\n",
        f"[tool.basedpyright]\n{addition}",
        1,
    )
    if not dry_run:
        pyproject.write_text(new_content, encoding="utf-8")
    return "added"


def main() -> None:
    parser = argparse.ArgumentParser(description="Roll out quality gate checks to all repos")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing")
    parser.add_argument("--repo", help="Only update this repo (by name)")
    args = parser.parse_args()

    repos = [WORKSPACE / r for r in ALL_REPOS]
    if args.repo:
        repos = [WORKSPACE / args.repo]

    print(f"\n{'[DRY RUN] ' if args.dry_run else ''}Rolling out quality gate checks to {len(repos)} repos\n")

    results = []
    for repo_path in repos:
        if not repo_path.exists():
            results.append({"repo": repo_path.name, "status": "MISSING"})
            continue

        print(f"  {repo_path.name}...")
        qg_result = update_repo(repo_path, args.dry_run)
        bp_result = update_basedpyright(repo_path, args.dry_run)
        qg_result["basedpyright"] = bp_result
        results.append(qg_result)

        added = qg_result.get("added", [])
        status = qg_result["status"]
        print(f"    quality-gates: {status} ({len(added)} added: {', '.join(added) if added else 'none'})")
        print(f"    basedpyright:  {bp_result}")

    # Summary
    updated = [r for r in results if r["status"] == "UPDATED"]
    up_to_date = [r for r in results if r["status"] == "UP_TO_DATE"]
    skipped = [r for r in results if r["status"] in ("SKIP", "MISSING")]

    print(f"\n{'=' * 60}")
    print(f"Updated:    {len(updated)} repos")
    print(f"Up-to-date: {len(up_to_date)} repos")
    print(f"Skipped:    {len(skipped)} repos ({', '.join(r['repo'] for r in skipped)})")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    main()
