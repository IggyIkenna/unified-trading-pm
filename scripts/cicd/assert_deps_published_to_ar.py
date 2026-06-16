#!/usr/bin/env python3
"""Gap 9a — assert a repo's internal dependencies are PUBLISHED to Artifact Registry.

Ref: plans/active/issues/ci_pipeline_self_healing_gaps_2026_06_11.md § Gap 9a.

The recurring-jam root cause: a consumer's internal-dep FLOOR (e.g. UTL's
`unified-api-contracts>=0.10.0`) reached `main` and triggered the consumer's standalone build,
but the producer's matching version was **not yet published to Artifact Registry** → `uv sync`
in the consumer's CI clone could not resolve the floor → the consumer (a T0/T1 lib) went red →
fleet jam. The staging→main dep-order gate checks a dep is *on main* (ci_status ≥ MAIN_GREEN),
but "on main" ≠ "published to AR" (the wheel-publish lags the main-merge).

This check closes that window: for every INTERNAL dependency a repo declares (matched against the
workspace manifest's repo set), it reads the floor from the repo's **pyproject.toml** (the real
floor — the manifest dep-edge floor is a vestigial range-pin per CLAUDE.md § Dependencies) and
asserts Artifact Registry has a published version satisfying it.

IMPORTANT — the `published_packages` manifest field is DEAD (publish-package.yml has never run;
wheels are published by the build pipeline). So AR itself is queried directly (gcloud), which is
the source of truth.

FAIL-OPEN by design (mirrors the dep-order gate): any uncertainty — gcloud absent, AR query error,
pyproject unreadable, no floor, unparseable version — is treated as SATISFIED (exit 0). The check
only ever BLOCKS (exit 1) on a *positive* "AR has no satisfying version" signal, so it can never
freeze promotion on a missing/ambiguous signal.

Usage:
    assert_deps_published_to_ar.py <repo> [--ref main] [--pyproject PATH]
                                          [--manifest PATH] [--json]
    exit 0 = all internal deps published (or fail-open) ; exit 1 = ≥1 dep NOT in AR at its floor
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import cast

AR_REGION = "asia-northeast1"
# Project id is read from the environment (the gate workflow exports GCP_PROJECT_ID /
# GOOGLE_CLOUD_PROJECT) — never hard-coded (codex: no hard-coded prod project id). Empty when
# unset → the AR query fails → the check fails-OPEN (allows), which is the safe default.
AR_PROJECT = os.environ.get("GCP_PROJECT_ID") or os.environ.get("GOOGLE_CLOUD_PROJECT") or ""
AR_REPOSITORY = "unified-libraries"

_VER_RE = re.compile(r"(\d+)(?:\.(\d+))?(?:\.(\d+))?")
_FLOOR_RE = re.compile(r">=\s*([0-9][0-9.]*)")
_CEIL_RE = re.compile(r"<\s*([0-9][0-9.]*)")
# A dependency entry's package name = everything up to the first version/extra/marker char.
_NAME_RE = re.compile(r"^([A-Za-z0-9._-]+)")


def _ver_tuple(v: str) -> tuple[int, int, int] | None:
    """Parse a dotted version to a (major, minor, patch) int tuple; None if unparseable.

    Tuple comparison gives correct semver ordering (0.10.0 > 0.9.0), unlike string sort.
    """
    m = _VER_RE.match(v.strip())
    if not m:
        return None
    return (int(m.group(1)), int(m.group(2) or 0), int(m.group(3) or 0))


def _internal_repos(manifest_path: Path) -> set[str]:
    try:
        with manifest_path.open() as f:
            m = cast("dict[str, object]", json.load(f))
    except (OSError, ValueError):
        return set()
    repos = m.get("repositories")
    if not isinstance(repos, dict):
        return set()
    return {r for r in cast("dict[str, object]", repos) if not r.startswith("_")}


def _load_pyproject(repo: str, ref: str, pyproject_path: str | None) -> dict[str, object] | None:
    """Load the repo's pyproject.toml — from a local path if given, else fetched from GitHub at ref."""
    if pyproject_path:
        try:
            with open(pyproject_path, "rb") as f:
                return tomllib.load(f)
        except (OSError, tomllib.TOMLDecodeError):
            return None
    # Fetch from GitHub (the gate runs in PM, the consumer repo is not checked out).
    proc = subprocess.run(
        ["gh", "api", f"repos/IggyIkenna/{repo}/contents/pyproject.toml?ref={ref}", "--jq", ".content"],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0 or not proc.stdout.strip():
        return None
    try:
        raw = base64.b64decode(proc.stdout.strip())
        return tomllib.loads(raw.decode("utf-8"))
    except (ValueError, tomllib.TOMLDecodeError, UnicodeDecodeError):
        return None


def _internal_dep_floors(
    pyproject: dict[str, object], internal: set[str]
) -> dict[str, tuple[tuple[int, int, int] | None, tuple[int, int, int] | None]]:
    """Map each internal dependency → (floor_tuple, ceiling_tuple) from [project.dependencies]."""
    project = pyproject.get("project")
    deps = cast("dict[str, object]", project).get("dependencies") if isinstance(project, dict) else None
    out: dict[str, tuple[tuple[int, int, int] | None, tuple[int, int, int] | None]] = {}
    if not isinstance(deps, list):
        return out
    for entry in cast("list[object]", deps):
        if not isinstance(entry, str):
            continue
        nm = _NAME_RE.match(entry.strip())
        if not nm:
            continue
        name = nm.group(1)
        if name not in internal:
            continue
        fm = _FLOOR_RE.search(entry)
        cm = _CEIL_RE.search(entry)
        floor = _ver_tuple(fm.group(1)) if fm else None
        ceil = _ver_tuple(cm.group(1)) if cm else None
        out[name] = (floor, ceil)
    return out


def _ar_versions(package: str) -> list[tuple[int, int, int]] | None:
    """Published versions of `package` in AR as version tuples; None on any error (→ fail-open)."""
    proc = subprocess.run(
        [
            "gcloud", "artifacts", "versions", "list",
            f"--repository={AR_REPOSITORY}", f"--location={AR_REGION}", f"--project={AR_PROJECT}",
            f"--package={package}", "--format=value(name)", "--limit=1000",
        ],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return None
    out: list[tuple[int, int, int]] = []
    for line in proc.stdout.splitlines():
        tail = line.strip().rsplit("/", 1)[-1]  # versions are returned as full resource paths
        t = _ver_tuple(tail)
        if t:
            out.append(t)
    return out


def check(repo: str, ref: str, pyproject_path: str | None, manifest_path: Path) -> dict[str, object]:
    """Return {satisfied: bool, unpublished: [...], checked: [...], fail_open_reason: str|None}."""
    internal = _internal_repos(manifest_path)
    if not internal:
        return {"satisfied": True, "unpublished": [], "checked": [], "fail_open_reason": "no manifest repos"}

    pyproject = _load_pyproject(repo, ref, pyproject_path)
    if pyproject is None:
        return {"satisfied": True, "unpublished": [], "checked": [], "fail_open_reason": "pyproject unreadable"}

    floors = _internal_dep_floors(pyproject, internal)
    if not floors:
        return {"satisfied": True, "unpublished": [], "checked": [], "fail_open_reason": "no internal deps"}

    unpublished: list[dict[str, object]] = []
    checked: list[str] = []
    for dep, (floor, ceil) in sorted(floors.items()):
        checked.append(dep)
        if floor is None:
            continue  # no floor declared → nothing to assert (fail-open per-dep)
        versions = _ar_versions(dep)
        if not versions:
            # None (query error) OR empty (query anomaly / brand-new package) → fail-open per-dep.
            # An empty result is ambiguous (anomaly vs never-published); the safe-default is to
            # NEVER block on it (a genuinely-never-built dep fails the consumer build loudly anyway).
            continue
        ok = any(v >= floor and (ceil is None or v < ceil) for v in versions)
        if not ok:
            latest = max(versions) if versions else None
            unpublished.append({
                "dep": dep,
                "floor": ".".join(map(str, floor)),
                "latest_in_ar": ".".join(map(str, latest)) if latest else None,
            })
    return {"satisfied": not unpublished, "unpublished": unpublished, "checked": checked, "fail_open_reason": None}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Assert a repo's internal deps are published to Artifact Registry")
    ap.add_argument("repo", help="consumer repo name (e.g. unified-trading-library)")
    ap.add_argument("--ref", default="main", help="git ref to read the consumer's pyproject.toml from")
    ap.add_argument("--pyproject", default=None, help="local pyproject.toml path (skips the GitHub fetch)")
    ap.add_argument("--manifest", default=None, help="workspace-manifest.json path")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args(argv)
    repo = cast("str", args.repo)
    ref = cast("str", args.ref)
    pyproject_path = cast("str | None", args.pyproject)
    manifest_arg = cast("str | None", args.manifest)
    as_json = cast("bool", args.json)

    manifest_path = (
        Path(manifest_arg)
        if manifest_arg
        else Path(__file__).resolve().parent.parent.parent / "workspace-manifest.json"
    )
    result = check(repo, ref, pyproject_path, manifest_path)

    if as_json:
        print(json.dumps(result))
    elif result["fail_open_reason"]:
        print(f"✅ {repo}: dep-publish check fail-open ({result['fail_open_reason']}) — allowing")
    elif result["satisfied"]:
        n_ok = len(cast("list[object]", result["checked"]))
        print(f"✅ {repo}: all {n_ok} internal dep(s) published to AR at floor")
    else:
        n_bad = len(cast("list[object]", result["unpublished"]))
        print(f"⛔ {repo}: {n_bad} internal dep(s) NOT yet in AR at floor:")
        for u in cast("list[dict[str, object]]", result["unpublished"]):
            print(f"   - {u['dep']} needs >={u['floor']}, latest in AR = {u['latest_in_ar']}")
        print("   → producer not published yet; promotion should wait (retry next run).")
    return 0 if result["satisfied"] else 1


if __name__ == "__main__":
    sys.exit(main())
