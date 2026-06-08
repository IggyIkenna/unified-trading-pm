#!/usr/bin/env python3
"""Path-B slot drift check — the one invariant left to police after the tab-branch retirement.

Under Path-B (2026-06-08) each slot worktree `.tabs/<N>/<repo>` is a `git clone --reference`
on `live-defi-rollout` (no tab branch, no tab-mirror, no upstream to re-point). The only
remaining invariant: a slot's `HEAD` must be **ancestor-or-equal** of
`origin/live-defi-rollout` — i.e. the slot is either current or behind (FF-able), never
diverged. This replaces the divergence half of the retired `tab-mirror-to-ldr.yml`.

Reports, per slot worktree: OK (==LDR), BEHIND (FF-able — run `git pull --ff-only`), DIRTY
(uncommitted), or DIVERGED (HEAD not an ancestor of LDR — reconcile). Exit 1 if any DIVERGED.

Usage:
    slot_drift_check.py [--tabs-root .tabs] [--fix-ff]   (--fix-ff: auto `pull --ff-only` BEHIND slots)
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import cast


def _git(repo: Path, *args: str) -> tuple[int, str]:
    p = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    return p.returncode, p.stdout.strip()


def classify(repo: Path, fix_ff: bool) -> str:
    _, dirty = _git(repo, "status", "--porcelain")
    if dirty:
        return "DIRTY"
    _git(repo, "fetch", "origin", "live-defi-rollout", "--quiet")
    _, head = _git(repo, "rev-parse", "HEAD")
    ldr_anc = _git(repo, "merge-base", "--is-ancestor", "origin/live-defi-rollout", head)[0] == 0
    head_anc = _git(repo, "merge-base", "--is-ancestor", head, "origin/live-defi-rollout")[0] == 0
    if ldr_anc and head_anc:
        return "OK"
    if head_anc:  # behind → FF-able
        if fix_ff:
            _git(repo, "pull", "--ff-only", "origin", "live-defi-rollout")
            return "OK (fixed: FF-pulled)"
        return "BEHIND"
    return "DIVERGED"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tabs-root", default=".tabs")
    ap.add_argument("--fix-ff", action="store_true")
    args = ap.parse_args()
    tabs = Path(cast(str, args.tabs_root)).resolve()
    fix_ff = cast(bool, args.fix_ff)

    if not tabs.is_dir():
        print(f"no tabs root at {tabs}")
        return 0
    diverged: list[str] = []
    for slot in sorted(os.listdir(tabs)):
        sp = tabs / slot
        if not sp.is_dir() or not slot.isdigit():
            continue
        for repo in sorted(os.listdir(sp)):
            rp = sp / repo
            if not (rp / ".git").exists():
                continue
            verdict = classify(rp, fix_ff)
            if verdict != "OK" and not verdict.startswith("OK"):
                print(f"  slot {slot} {repo}: {verdict}")
            if verdict == "DIVERGED":
                diverged.append(f"{slot}/{repo}")
    if diverged:
        print(f"❌ {len(diverged)} slot worktree(s) DIVERGED from LDR (reconcile): {diverged}")
        return 1
    print("✅ all slot worktrees are ancestor-or-equal of origin/live-defi-rollout")
    return 0


if __name__ == "__main__":
    sys.exit(main())
