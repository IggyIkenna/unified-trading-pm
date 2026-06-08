#!/usr/bin/env python3
"""Strict-quickmerge guard — reject a CODE commit on the integration branch that bypassed quickmerge.

HARD RULE (codified 2026-06-08, CLAUDE.md + SUB_AGENT + codex/08-workflows/ci-cd-flow.md §
strict-quickmerge): CODE reaches `live-defi-rollout`/`staging`/`main` ONLY via
`quickmerge --agent --files`. A direct `git push` of code dodges the dep gates and silently
piles behind main with no staging PR. This guard catches the bypass: quickmerge stamps a
`Quickmerge:` trailer on its commits; a commit that changes SOURCE (`*.py`/`*.ts`/`*.tsx`
outside scripts/tests/.github) without that trailer, and is not a carve-out, is a violation.

**Closed carve-out set** (the only sanctioned direct pushes — allowed without the trailer):
  - docs / plans / codex / markdown / config: `*.md`, `*.mdc`, `plans/**`, `codex/**`, `docs/**`,
    `*.yaml|yml|json|toml` (non-source)
  - CI/infra: `.github/**`, `scripts/**`  (PM scripts + any repo's workflow files — the
    chicken-and-egg: a corrected gate can't pass through the gate it is fixing)
  - merge/reconcile commits + `[skip ci]` automation (ci_status / manifest writes) + bot authors

WARN by default; set `STRICT_QUICKMERGE_BLOCK=1` (or `--block`) to hard-fail (exit 1). Intended
as a `pre-push` hook on the integration branch + an ad-hoc audit tool.

Usage:
    check_strict_quickmerge.py --range origin/live-defi-rollout..HEAD [--block]
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from typing import cast

SOURCE_EXT = (".py", ".ts", ".tsx")
CARVE_PREFIX = (".github/", "scripts/", "plans/", "codex/", "docs/")
CARVE_EXT = (".md", ".mdc", ".yaml", ".yml", ".json", ".toml", ".txt", ".cfg", ".ini", ".lock")
NONSOURCE_DIR = ("scripts/", "tests/", "test/", ".github/")


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True).stdout


def _is_source(path: str) -> bool:
    if not path.endswith(SOURCE_EXT):
        return False
    return not any(seg in path for seg in NONSOURCE_DIR)


def _is_carveout_file(path: str) -> bool:
    return path.startswith(CARVE_PREFIX) or path.endswith(CARVE_EXT)


def commit_violates(sha: str) -> tuple[bool, str]:
    msg = _git("show", "-s", "--format=%B", sha)
    author = _git("show", "-s", "--format=%an", sha).strip()
    parents = _git("show", "-s", "--format=%P", sha).split()
    if len(parents) > 1:
        return False, "merge/reconcile commit"
    if "[skip ci]" in msg or "github-actions" in author.lower() or "[bot]" in author.lower():
        return False, "automation/[skip ci]/bot"
    if "Quickmerge:" in msg:
        return False, "passed through quickmerge"
    files = [f for f in _git("show", "--name-only", "--format=", sha).splitlines() if f.strip()]
    source = [f for f in files if _is_source(f)]
    if not source:
        return False, "carve-out (no source changed)"
    # a source change WITHOUT a quickmerge trailer and not a carve-out-only commit
    return True, f"source changed without quickmerge: {source[:5]}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--range", default="origin/live-defi-rollout..HEAD")
    ap.add_argument("--block", action="store_true")
    args = ap.parse_args()
    rng = cast(str, args.range)
    block = cast(bool, args.block) or os.environ.get("STRICT_QUICKMERGE_BLOCK") == "1"

    shas = [s for s in _git("rev-list", rng).splitlines() if s.strip()]
    violations: list[str] = []
    for sha in shas:
        bad, why = commit_violates(sha)
        if bad:
            subj = _git("show", "-s", "--format=%h %s", sha).strip()
            violations.append(f"{subj}  [{why}]")

    if not violations:
        print(f"✅ strict-quickmerge: no bypassed code commits in {rng}")
        return 0
    print(f"{'❌' if block else '⚠️ '} strict-quickmerge: {len(violations)} code commit(s) bypassed quickmerge:")
    for v in violations:
        print(f"  - {v}")
    print("   Ship code via `quickmerge --agent --files '<paths>'` (NOT a direct push). Carve-out: dirty-deps,")
    print("   FF-pull-in + PM docs(plans) flip, PM scripts/.github + any .github/workflows that must reach main.")
    if block:
        return 1
    print("   (WARN only — set STRICT_QUICKMERGE_BLOCK=1 to enforce.)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
