#!/usr/bin/env python3
"""Dep-content sync gate — every editable dep must be clean and == its LDR ref.

The quickmerge dep gates (STAGE 1.6 version, STAGE 1.7 ci_status tier) are version-typed,
not content-typed: local QG resolves deps via editable path (`tool.uv.sources … path=…,
editable=true`), so it builds against your WORKING-TREE copy of every dep. An uncommitted
or LDR-divergent dep edit (same pinned version) → consumer green locally, red at staging,
and both version gates wave it through because the version never changed.

This gate converts an "invisible local dep edit" into a tracked, committed-to-LDR dep:
for each TRANSITIVE editable dep `D`, it BLOCKS if `D` is dirty or ahead-of-LDR-unpushed,
WARNs if `D` is behind its LDR ref, and PASSes only when `D` is clean and == LDR. At that
point local-green means "green vs the shared base" and the existing 1.6/1.7 + cascade gates
already close the staging gap.

Human-only `--allow-dirty-deps` escape (loud) prints a `DIRTY_DEPS` taint marker that the
caller folds into the QG sentinel so it can NEVER satisfy a quickmerge promotion (mirrors
the `--dep-branch` / `--skip-dep-tier-gate` human-only pattern). Agents are hard-blocked.

Usage (inside a repo checkout):
    check_dep_content_sync.py [--repo .] [--ldr-ref origin/live-defi-rollout] [--allow-dirty-deps]
Exit 0 = all deps clean+==LDR (or only WARNs / allowed). Exit 1 = a BLOCK (dirty / ahead-unpushed).
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import cast


def _sources(pyproject: Path) -> list[tuple[str, Path]]:
    """Return [(dep_name, abs_editable_path)] from a pyproject's tool.uv.sources."""
    try:
        data: dict[str, object] = tomllib.loads(pyproject.read_text())
    except (OSError, tomllib.TOMLDecodeError):
        return []

    def _dig(d: object, key: str) -> dict[str, object]:
        if isinstance(d, dict):
            v = cast("dict[str, object]", d).get(key)
            if isinstance(v, dict):
                return cast("dict[str, object]", v)
        return {}

    srcs = _dig(_dig(_dig(data, "tool"), "uv"), "sources")
    out: list[tuple[str, Path]] = []
    for name, spec in srcs.items():
        if isinstance(spec, dict):
            spec_d = cast("dict[str, object]", spec)
            path = spec_d.get("path")
            if spec_d.get("editable") and isinstance(path, str):
                out.append((name, (pyproject.parent / path).resolve()))
    return out


def transitive_editable_deps(repo: Path) -> dict[str, Path]:
    """Walk the FULL editable-dep DAG (consumer → mtds → utl/uac), not just direct deps."""
    seen: dict[str, Path] = {}
    queue = [repo]
    while queue:
        cur = queue.pop()
        for name, path in _sources(cur / "pyproject.toml"):
            if name in seen or not (path / "pyproject.toml").exists():
                continue
            seen[name] = path
            queue.append(path)
    return seen


def _git(dep: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(dep), *args], capture_output=True, text=True
    ).stdout.strip()


def classify(dep: Path, ldr_ref: str) -> tuple[str, str]:
    """Return (verdict, detail). verdict ∈ {BLOCK, WARN, PASS}."""
    dirty = _git(dep, "status", "--porcelain")
    if dirty:
        return "BLOCK", f"dirty working tree ({len(dirty.splitlines())} files) — commit+push to LDR first"
    head = _git(dep, "rev-parse", "HEAD")
    # ensure we have the LDR ref locally for the ancestor checks
    subprocess.run(
        ["git", "-C", str(dep), "fetch", "origin", ldr_ref.split("/", 1)[-1], "--quiet"],
        capture_output=True,
    )
    head_anc = subprocess.run(
        ["git", "-C", str(dep), "merge-base", "--is-ancestor", head, ldr_ref]
    ).returncode == 0
    ldr_anc = subprocess.run(
        ["git", "-C", str(dep), "merge-base", "--is-ancestor", ldr_ref, head]
    ).returncode == 0
    if head_anc and ldr_anc:
        return "PASS", "clean + == LDR"
    if not head_anc:
        return "BLOCK", (
            "ahead-of-LDR-unpushed — local QG tests dep content staging will never see; push to LDR first"
        )
    return "WARN", "behind its LDR ref (stale base) — pull origin LDR"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--ldr-ref", default="origin/live-defi-rollout")
    ap.add_argument("--allow-dirty-deps", action="store_true")
    args = ap.parse_args()
    repo = Path(cast(str, args.repo)).resolve()
    ldr_ref = cast(str, args.ldr_ref)
    allow_dirty = cast(bool, args.allow_dirty_deps)

    deps = transitive_editable_deps(repo)
    if not deps:
        print("dep-content gate: no editable deps — PASS")
        return 0

    blocks: list[str] = []
    for name in sorted(deps):
        verdict, detail = classify(deps[name], ldr_ref)
        marker = {"PASS": "✅", "WARN": "⚠️ ", "BLOCK": "❌"}[verdict]
        print(f"  {marker} {name}: {verdict} — {detail}")
        if verdict == "BLOCK":
            blocks.append(name)

    if blocks and allow_dirty:
        print(
            f"⚠️  --allow-dirty-deps: {len(blocks)} dirty/divergent dep(s) ALLOWED (human-only). "
            "Sentinel will be tainted DIRTY_DEPS — cannot satisfy a quickmerge promotion."
        )
        print("DIRTY_DEPS")  # taint marker the caller folds into the QG sentinel
        return 0
    if blocks:
        print(
            f"❌ dep-content gate FAILED: {len(blocks)} dep(s) dirty or ahead-of-LDR-unpushed "
            f"({', '.join(blocks)}). Commit+push each to live-defi-rollout, then re-run. "
            "(Human-only escape: --allow-dirty-deps, which taints the sentinel.)"
        )
        return 1
    print("✅ dep-content gate: all editable deps clean + == LDR")
    return 0


if __name__ == "__main__":
    sys.exit(main())
