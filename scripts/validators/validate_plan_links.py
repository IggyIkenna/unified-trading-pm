#!/usr/bin/env python3.13
"""Validate no broken relative links in plans/active/*.plan.md.

Phase 0b: plans_to_deployable_unified_audit.plan.md
GATE: no broken relative links in any active plans/active/ .plan.md file.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import cast

# Prose examples use literal `./...` / `../...` after `[...]` — not real filesystem paths.
_PLACEHOLDER_TAIL = frozenset({"...", "./...", "../..."})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--plans-dir", type=Path, default=Path(__file__).resolve().parent.parent.parent / "plans" / "active"
    )
    parser.add_argument("--workspace-root", type=Path, default=Path(__file__).resolve().parent.parent.parent.parent)
    args = parser.parse_args()

    plans_dir: Path = cast(Path, args.plans_dir).resolve()
    ws_root: Path = cast(Path, args.workspace_root).resolve()
    if not plans_dir.is_dir():
        print(f"Skip: {plans_dir} not found", file=sys.stderr)
        return 0

    broken: list[tuple[str, str]] = []
    for path in plans_dir.glob("*.plan.md"):
        content: str = path.read_text()
        for m in re.finditer(r"\]\(([^)]+)\)", content):
            link = m.group(1).strip()
            if link.startswith("http") or link.startswith("#") or " " in link:
                continue
            if link in _PLACEHOLDER_TAIL:
                continue
            # Strip GitHub-style line anchors (#L42, #L42-L51) before path resolution —
            # these are display hints, the file path is what's checked.
            link_path = link.split("#", 1)[0]
            if not link_path:
                # Pure anchor like #section — already filtered above, defensive guard.
                continue
            target: Path
            if link_path.startswith(".cursor/") or link_path.startswith("deployment-service/"):
                target = ws_root / link_path
            elif "/" in link_path and not link_path.startswith("."):
                target = ws_root / link_path.split("/")[0]
            else:
                target = (plans_dir / link_path).resolve()
                if not target.exists():
                    archive_dir: Path = plans_dir.parent / "archive"
                    if archive_dir.is_dir():
                        target = (archive_dir / link_path).resolve()
            if not target.exists():
                broken.append((str(path.relative_to(plans_dir.parent)), link))

    if broken:
        for f, link in broken:
            print(f"BROKEN: {f} -> {link}", file=sys.stderr)
        return 1
    print("OK: No broken links in plans/active/*.plan.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
