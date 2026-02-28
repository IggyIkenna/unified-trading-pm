#!/usr/bin/env python3
"""
Enable Codex Compliance as BLOCKING Quality Gate

Currently codex compliance is "warn only" - it can fail but doesn't block merges.
This script makes codex compliance BLOCKING across all services for the cleanup.

Changes:
1. Replace YELLOW "warn only" with RED "FAILED"
2. Add OVERALL_STATUS=1 when codex fails
3. Remove "non-blocking" comment

Usage:
    python enable-codex-compliance-blocking.py
"""

import sys
from pathlib import Path

# Colors
BLUE = "\033[0;34m"
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
RED = "\033[0;31m"
NC = "\033[0m"

WORKSPACE_ROOT = Path(__file__).resolve().parents[5]

REPOS = [
    "execution-services",
    "strategy-service",
    "instruments-service",
    "unified-trading-services",
    "market-data-processing-service",
    "ml-training-service",
    "ml-inference-service",
    "features-delta-one-service",
    "features-volatility-service",
    "features-calendar-service",
    "features-onchain-service",
    "market-tick-data-handler",
    "unified-trading-deployment-v2",
]


def enable_blocking(quality_gates_path: Path) -> bool:
    """Enable codex compliance blocking in quality-gates.sh file."""
    content = quality_gates_path.read_text()

    # Check if already blocking
    if "warn only - not blocking" not in content:
        return False  # Already blocking or not found

    # Create backup
    backup_path = quality_gates_path.with_suffix(".sh.backup")
    backup_path.write_text(content)

    # Replace the problematic section
    old_pattern = '    echo -e "Codex:    ${YELLOW}⚠️  FAILED (warn only - not blocking)${NC}"'
    new_replacement = '    echo -e "Codex:    ${RED}❌ FAILED${NC}"\n    OVERALL_STATUS=1'

    # Replace warn-only message
    new_content = content.replace(old_pattern, new_replacement)

    # Remove the non-blocking comment
    comment_line = "    # Codex violations (print, os.getenv, datetime.now, etc.) are non-blocking for now"
    new_content = new_content.replace(comment_line, "")

    # Write back
    quality_gates_path.write_text(new_content)

    # Verify
    verification = quality_gates_path.read_text()
    if "warn only - not blocking" in verification:
        # Restore backup if failed
        quality_gates_path.write_text(content)
        backup_path.unlink()
        return None  # Failed

    # Success - remove backup
    backup_path.unlink()
    return True  # Updated


def main():
    print(f"{BLUE}{'=' * 60}")
    print("Enable Codex Compliance Blocking")
    print(f"{'=' * 60}{NC}\n")
    print("This will make codex compliance BLOCKING in all quality gates.")
    print("Currently it's 'warn only' - failures don't block merges.\n")
    print("After this change:")
    print("  - Codex violations WILL block merges")
    print("  - Success criteria: full codex compliance")
    print("  - Align with cleanup project goals\n")

    response = input("Continue? (y/n) ")
    if response.lower() != "y":
        print("Aborted.")
        return 0

    print()
    updated = 0
    skipped = 0
    failed = 0

    for repo in REPOS:
        quality_gates = WORKSPACE_ROOT / repo / "scripts" / "quality-gates.sh"

        if not quality_gates.exists():
            print(f"{YELLOW}⏭️  Skipping {repo} (no quality-gates.sh){NC}")
            skipped += 1
            continue

        result = enable_blocking(quality_gates)

        if result is None:
            print(f"{RED}❌ {repo} (failed to update){NC}")
            failed += 1
        elif result is False:
            print(f"{GREEN}✅ {repo} (already blocking){NC}")
            skipped += 1
        else:
            print(f"{GREEN}🔧 {repo} (updated){NC}")
            updated += 1

    print(f"\n{BLUE}{'=' * 60}{NC}")
    print(f"{GREEN}✅ Update Complete{NC}")
    print(f"{BLUE}{'=' * 60}{NC}\n")
    print(f"Updated: {updated} services")
    print(f"Skipped: {skipped} services")
    print(f"Failed:  {failed} services\n")

    if failed > 0:
        print(f"{RED}⚠️  {failed} services failed to update - check manually{NC}\n")
        return 1

    print("Next steps:")
    print("  1. Test locally: cd <service> && bash scripts/quality-gates.sh")
    print("  2. Verify codex failures now block: introduce a print() and re-run")
    print("  3. Changes are local - will be committed by batch-fix when fixing issues\n")

    print("Codex standards: unified-trading-codex/06-coding-standards/README.md\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
