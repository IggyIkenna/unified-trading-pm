#!/usr/bin/env python3.13
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
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
    parser.add_argument("--quiet", action="store_true", help="Suppress the OK line on success (failures always print)")
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
            # Resolution order: plans_dir-relative first, then archive top-level +
            # all archive subdirs (e.g. archive/2026_05/), then workspace-root.
            # For ``.md`` links also try ``.plan.md`` per workspace plan-
            # filename convention (active=``.md``, archive=``.plan.md``).
            #
            # A leading "/" (e.g. "/codex/04-architecture/x.md") is this repo's PM-repo-root-
            # relative convention, NOT a filesystem-absolute path -- but Path's own `/` operator
            # silently DISCARDS the left operand when the right one is absolute
            # (Path("a") / "/b" == Path("/b")), so every base in the loop below previously
            # collapsed to the same nonexistent OS-root path for any "/"-prefixed link,
            # regardless of `base`. Resolve it explicitly against the PM repo root
            # (plans_dir.parent.parent -- plans/active -> plans -> repo root) first.
            pm_repo_root = plans_dir.parent.parent
            candidates: list[Path] = []
            if link_path.startswith("/") and pm_repo_root.is_dir():
                root_relative = link_path.lstrip("/")
                candidates.append((pm_repo_root / root_relative).resolve())
                if root_relative.endswith(".md") and not root_relative.endswith(".plan.md"):
                    plan_md_path = root_relative[: -len(".md")] + ".plan.md"
                    candidates.append((pm_repo_root / plan_md_path).resolve())
            archive_dir = plans_dir.parent / "archive"
            archive_bases = (
                [archive_dir, *sorted(d for d in archive_dir.iterdir() if d.is_dir())] if archive_dir.is_dir() else []
            )
            for base in (plans_dir, *archive_bases, ws_root):
                if not base.is_dir():
                    continue
                primary = (base / link_path).resolve()
                candidates.append(primary)
                if link_path.endswith(".md") and not link_path.endswith(".plan.md"):
                    plan_md_path = link_path[: -len(".md")] + ".plan.md"
                    candidates.append((base / plan_md_path).resolve())
            target = next((c for c in candidates if c.exists()), candidates[0])
            if not target.exists():
                # Workspace-repo-prefix tolerance: skip links to sibling repos
                # that are either present-but-file-missing OR absent (partial
                # workspace, e.g. GHA only clones PM + dep repos). PM-internal
                # paths (plans/, codex/, scripts/, etc.) are checked strictly.
                _PM_INTERNAL = frozenset(  # noqa: N806
                    {
                        "plans",
                        "codex",
                        "scripts",
                        "cursor-configs",
                        "cursor-rules",
                        ".cursor",
                        ".github",
                        "tests",
                    }
                )
                first_segment = link_path.lstrip("./").split("/", 1)[0]
                # Sibling-repo tolerance: skip if segment resolves as a directory OR looks
                # like a repo name (no dot — repo dirs never have extensions like ".md").
                # Keeps plain-filename links (e.g. "nonexistent.md") strictly checked.
                if first_segment and (
                    (ws_root / first_segment).is_dir()
                    or (first_segment not in _PM_INTERNAL and "." not in first_segment)
                ):
                    continue
                broken.append((str(path.relative_to(plans_dir.parent)), link))

    if broken:
        for f, link in broken:
            print(f"BROKEN: {f} -> {link}", file=sys.stderr)
        return 1
    if not args.quiet:
        print("OK: No broken links in plans/active/*.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
