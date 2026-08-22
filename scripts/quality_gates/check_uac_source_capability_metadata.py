#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""QG STEP 5.85: verify every SourceCapability instance has explicit chain= and kind= kwargs.

Scans capability_declarations/_*.py. For each SourceCapability(...) block, checks that
chain= and kind= kwargs appear explicitly. This catches venues where Phase 2 migration
has not been run (new venues added without the structured metadata fields).

Exit 0 — all SourceCapability instances have chain= and kind=.
Exit 1 — one or more instances missing chain= or kind=.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


def find_capability_declarations_dir(repo_root: Path) -> Path | None:
    uac_decl = repo_root / "unified-api-contracts" / "unified_api_contracts" / "registry" / "capability_declarations"
    if uac_decl.exists():
        return uac_decl
    return None


def check_file(filepath: Path) -> list[str]:
    content = filepath.read_text()
    errors: list[str] = []

    # Find each SourceCapability( block: from SourceCapability( to the standalone )
    cap_pattern = re.compile(r"SourceCapability\(.*?\n\)", re.DOTALL)
    for match in cap_pattern.finditer(content):
        block = match.group(0)
        src_match = re.search(r'source="([^"]+)"', block)
        source = src_match.group(1) if src_match else "<unknown>"
        missing = []
        if not re.search(r"\bchain=", block):
            missing.append("chain")
        if not re.search(r"\bkind=", block):
            missing.append("kind")
        if missing:
            errors.append(f"  {filepath.name}: source={source!r} — missing kwarg(s): {', '.join(missing)}")
    return errors


def main() -> int:
    workspace_root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent.parent.parent.parent

    decl_dir = find_capability_declarations_dir(workspace_root)
    if decl_dir is None:
        print("SKIP STEP 5.85: capability_declarations/ not found — repo not UAC")
        return 0

    all_errors: list[str] = []
    for py_file in sorted(decl_dir.glob("_*.py")):
        all_errors.extend(check_file(py_file))

    if all_errors:
        print("FAIL STEP 5.85: SourceCapability instances missing chain= or kind= kwargs:")
        for e in all_errors:
            print(e)
        print("Fix: add chain=... and kind=... to each SourceCapability() call (or None explicitly).")
        print("     Run: python3 scripts/migrate_source_capability_metadata.py")
        return 1

    print("OK STEP 5.85: all SourceCapability instances have explicit chain= and kind= kwargs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
