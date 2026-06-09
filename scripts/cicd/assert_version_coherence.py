#!/usr/bin/env python3
"""Version-coherence gate — assert each repo's source ``version`` agrees with the manifest.

The 2026-06-08 LDR-SSOT clean-start force-sync reverted source ``pyproject.version`` fleet-wide
to LDR's (older) value while ``workspace-manifest.json`` kept the semver-agent's computed value.
That split is invisible to the dependency-alignment gate (which compares DEPENDENCY constraints,
not a repo's own version) and is what produced the UTL ``0.4.0`` phantom — the manifest said
``0.4.0`` and 40 downstream PRs pinned ``>=0.4.0`` while no ``0.4.0`` artifact/tag existed.

This is the teeth the Phase-3 "verify no semver bump was reverted" check was missing. For every
repo it compares three numbers and flags any that disagree:

  * ``versions{}[repo]``         — stable (main) version, the SSOT
  * ``staging_versions{}[repo]`` — converging (staging) version
  * source ``pyproject.version`` — what the repo actually declares on ``live-defi-rollout``

With ``--tags`` it also checks that the highest of those has a matching published ``vX.Y.Z`` git
tag (a published, installable artifact) — the exact gap that bit UTL.

Read-only. Stdlib + ``gh`` only. Exit 1 if any split is found (so a force-sync runbook step or a
scheduled check can gate). Run AFTER any force-sync / clean-start.

Usage:
    assert_version_coherence.py                 # report + exit 1 on any split
    assert_version_coherence.py --tags          # also require a matching published tag
    assert_version_coherence.py --warn-only      # report only, always exit 0
"""

from __future__ import annotations

import argparse
import base64
import json
import os.path
import subprocess
import sys
from typing import cast

OWNER = "IggyIkenna"
LDR = "live-defi-rollout"


def _gh_text(path: str) -> str | None:
    r = subprocess.run(["gh", "api", path], capture_output=True, text=True)
    if r.returncode != 0:
        return None
    return r.stdout


def _manifest() -> dict[str, object]:
    here = os.path.dirname(os.path.abspath(__file__))
    mpath = os.path.join(here, "..", "..", "workspace-manifest.json")
    with open(mpath) as _mf:
        return cast("dict[str, object]", json.load(_mf))


def _source_version(repo: str) -> str | None:
    """Source pyproject version on LDR — local worktree first, then gh api fallback."""
    here = os.path.dirname(os.path.abspath(__file__))
    ws = os.path.abspath(os.path.join(here, "..", "..", ".."))
    local = os.path.join(ws, repo, "pyproject.toml")
    text: str | None = None
    if os.path.isfile(local):
        with open(local) as _f:
            text = _f.read()
    else:
        raw = _gh_text(f"repos/{OWNER}/{repo}/contents/pyproject.toml?ref={LDR}")
        if raw:
            try:
                content = cast("dict[str, object]", json.loads(raw)).get("content")
                if isinstance(content, str):
                    text = base64.b64decode(content).decode("utf-8", "replace")
            except (json.JSONDecodeError, ValueError):
                text = None
    if not text:
        return None
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("version") and "=" in s:
            return s.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def _has_tag(repo: str, version: str) -> bool:
    raw = _gh_text(f"repos/{OWNER}/{repo}/git/refs/tags/v{version}")
    return raw is not None and '"ref"' in raw


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tags", action="store_true", help="also require a matching published vX tag")
    ap.add_argument("--warn-only", action="store_true", help="report only; always exit 0")
    args = ap.parse_args()
    want_tags = cast(bool, args.tags)
    warn_only = cast(bool, args.warn_only)

    m = _manifest()
    versions = cast("dict[str, object]", m.get("versions") or {})
    staging = cast("dict[str, object]", m.get("staging_versions") or {})
    repos = sorted(r for r in versions if not r.startswith("_"))

    splits: list[str] = []
    print(f"{'repo':38} {'versions':10} {'staging':10} {'source':10} {'tag?':5}")
    for r in repos:
        v = str(versions.get(r, "-"))
        s = str(staging.get(r, "-")) if r in staging else "-"
        src = _source_version(r) or "?"
        tagcol = ""
        bad = False
        # source must match the stable version (and staging when present)
        if src not in ("?",) and (src != v or (s != "-" and src != s)):
            bad = True
        if want_tags and src != "?":
            top = max([x for x in (v, s, src) if x not in ("-", "?")], default=src)
            ok = _has_tag(r, top)
            tagcol = "ok" if ok else "MISS"
            if not ok:
                bad = True
        flag = "  <-- SPLIT" if bad else ""
        if bad:
            splits.append(r)
        print(f"{r:38} {v:10} {s:10} {src:10} {tagcol:5}{flag}")

    print()
    if splits:
        print(f"❌ {len(splits)} repo(s) with a version split: {', '.join(splits)}")
        print("   Reconcile source pyproject.version FORWARD to the manifest SSOT (never downgrade);")
        print("   for source-ahead repos bump the manifest. A split = a force-sync revert (FIX 4).")
        return 0 if warn_only else 1
    print("✅ All repo versions coherent (source == manifest).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
