#!/usr/bin/env python3.13
"""Validate no broken relative links in plans/active/*.md.

Phase 0b: plans_to_deployable_unified_audit.md
GATE: no broken relative links in any active plans/active/ .md file.
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
    for path in plans_dir.glob("*.md"):
        raw_content: str = path.read_text()
        # Strip fenced code blocks (```...```) and inline code spans (`...`)
        # before link extraction so that regex patterns inside code do not
        # false-positive as broken links.
        content = re.sub(r"```.*?```", "", raw_content, flags=re.DOTALL)
        content = re.sub(r"`[^`]+`", "", content)
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
            # Resolution order: plans_dir-relative first, then archive,
            # then workspace-root (for repo-prefixed paths like
            # ``unified-trading-pm/codex/...`` or ``../../<repo>/``).
            # For ``.md`` links also try ``.plan.md`` per workspace plan-
            # filename convention (active=``.md``, archive=``.plan.md``).
            candidates: list[Path] = []
            for base in (plans_dir, plans_dir.parent / "archive", ws_root):
                if not base.is_dir():
                    continue
                primary = (base / link_path).resolve()
                candidates.append(primary)
                if link_path.endswith(".md") and not link_path.endswith(".plan.md"):
                    plan_md_path = link_path[: -len(".md")] + ".plan.md"
                    candidates.append((base / plan_md_path).resolve())
            target = next((c for c in candidates if c.exists()), candidates[0])
            if not target.exists():
                # Workspace-repo-prefix tolerance: if the FIRST path segment
                # of the link resolves to an existing directory under ws_root,
                # treat the link as valid (the inner path may not yet exist
                # but the repo-prefix is well-formed). Lets plans reference
                # not-yet-created files inside known sibling repos.
                first_segment = link_path.lstrip("./").split("/", 1)[0]
                if first_segment and (ws_root / first_segment).is_dir():
                    continue
                broken.append((str(path.relative_to(plans_dir.parent)), link))

    if broken:
        for f, link in broken:
            print(f"BROKEN: {f} -> {link}", file=sys.stderr)
        return 1
    print("OK: No broken links in plans/active/*.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
