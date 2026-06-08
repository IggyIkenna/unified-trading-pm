#!/usr/bin/env python3
"""Dependency-order local QG sweep — the pre-promotion staging oracle.

Runs `quality-gates.sh --no-fix` across the workspace in TOPOLOGICAL dependency order
(T0 = unified-api-contracts → unified-trading-library → instruments → core services →
… → leaves) on the current local checkout of `live-defi-rollout`, ≤2 concurrent (the
host governor floor), so that "local QG green in dep order on an LDR checkout" is a
reliable predictor of staging-`quality-gates-v2` green.

Principle (operator, 2026-06-08): once QG has run everywhere in dep order on a local LDR
checkout, staging should work too; if it doesn't, that divergence is a *bug to audit* (CI
vs local QG have diverged in structure) — see `ci_local_qg_parity_2026_06_08.md`. The one
documented residual gap is the assembled-SIT cross-repo invariant layer, which per-repo QG
DEFERS (it has a partial dep set) rather than runs — so a green sweep is "staging-confident",
not "SIT-confident".

Each repo's editable deps are content-sync-gated by `check_dep_content_sync.py` (run as part
of `quality-gates.sh`), so a green sweep means green vs the shared LDR base, not vs invisible
local dep edits.

Usage:
    local_qg_sweep.py [--workspace-root PATH] [--concurrency 2] [--only repo1,repo2] [--dry-run]
Exit 0 = every repo green (staging-confidence: HIGH). Exit 1 = ≥1 repo red.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import subprocess
import sys
from pathlib import Path
from typing import cast


def _dep_levels(manifest: Path) -> list[list[str]]:
    data = cast("dict[str, object]", json.loads(manifest.read_text()))
    topo = data.get("topologicalOrder")
    levels: list[list[str]] = []
    if isinstance(topo, dict):
        raw = cast("dict[str, object]", topo).get("levels")
        if isinstance(raw, list):
            for lvl in cast("list[object]", raw):
                if isinstance(lvl, dict):
                    repos = cast("dict[str, object]", lvl).get("repos")
                    if isinstance(repos, list):
                        levels.append([str(r) for r in cast("list[object]", repos)])
    return levels


def _run_qg(repo_dir: Path) -> tuple[str, bool, str]:
    """Run quality-gates.sh --no-fix in repo_dir; return (repo, ok, tail)."""
    qg = repo_dir / "scripts" / "quality-gates.sh"
    if not qg.exists():
        return repo_dir.name, True, "no quality-gates.sh (skipped)"
    proc = subprocess.run(
        ["bash", str(qg), "--no-fix"],
        cwd=str(repo_dir),
        capture_output=True,
        text=True,
    )
    tail = "\n".join((proc.stdout + proc.stderr).splitlines()[-3:])
    return repo_dir.name, proc.returncode == 0, tail


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace-root", default=None)
    ap.add_argument("--concurrency", type=int, default=2)
    ap.add_argument("--only", default="")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    pm_root = Path(__file__).resolve().parents[2]
    ws_arg = cast("str | None", args.workspace_root)
    ws = Path(ws_arg) if ws_arg else pm_root.parent
    concurrency = max(1, min(2, cast(int, args.concurrency)))  # host-governor floor
    only = {r for r in cast(str, args.only).split(",") if r}
    dry = cast(bool, args.dry_run)

    levels = _dep_levels(pm_root / "workspace-manifest.json")
    if not levels:
        print("❌ could not read topologicalOrder.levels from workspace-manifest.json")
        return 1

    results: dict[str, tuple[bool, str]] = {}
    overall_ok = True
    for li, repos in enumerate(levels):
        tier = [r for r in repos if (not only or r in only) and (ws / r).exists()]
        if not tier:
            continue
        print(f"\n── dep-tier {li}: {', '.join(tier)} ──")
        if dry:
            for r in tier:
                print(f"  (dry-run) would QG {r}")
            continue
        # within a tier repos are independent → run ≤concurrency at a time; a tier must be
        # green before the next (dependents build on it).
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as ex:
            def _qg_one(r: str) -> tuple[str, bool, str]:
                return _run_qg(ws / r)

            for repo, ok, tail in ex.map(_qg_one, tier):
                results[repo] = (ok, tail)
                print(f"  {'✅' if ok else '❌'} {repo}{'' if ok else ' — ' + tail.splitlines()[-1] if tail else ''}")
                if not ok:
                    overall_ok = False
        if not overall_ok:
            print(f"\n⚠️  dep-tier {li} has a RED repo — dependents in later tiers build on it; "
                  "fix this tier before trusting downstream greens.")
            break

    green = sum(1 for ok, _ in results.values() if ok)
    print(f"\n=== sweep: {green}/{len(results)} repos green ===")
    print(
        "staging-confidence: "
        + ("HIGH (local LDR-checkout QG green in dep order ⇒ expect staging-v2 green; "
           "residual gap = assembled-SIT cross-repo layer)" if overall_ok else "LOW — fix red repos first")
    )
    return 0 if overall_ok else 1


if __name__ == "__main__":
    sys.exit(main())
