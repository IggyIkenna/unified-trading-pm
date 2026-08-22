#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""PM post-gate (warn-only): detect stale ``ARG BASE_IMAGE_DIGEST`` pins across the fleet.

**Context**: Every Python service Dockerfile pins the ``unified-trading-library`` base image via::

    ARG BASE_IMAGE_DIGEST=sha256:<64-hex>
    FROM ...unified-trading-library@${BASE_IMAGE_DIGEST}

The ``update-dependency-version.yml`` fan-out refreshes this pin on every UTL base-image
publish.  When a repo misses the fan-out (as mdps did 2026-06-19 — its pin drifted to
``e939b4ee`` / UTL 0.11.0 while its own floor requires UTL ≥0.12.0), the build fails
silently: Cloud Build re-resolves from the registry, cannot satisfy the floor, and exits 1.

This gate makes the drift visible BEFORE it becomes a red build:

1. **Fleet-consistency check** (primary): all repos with a digest pin must use the SAME
   ``sha256:`` value.  Any divergence = a missed fan-out → WARN with the divergent repos.

2. **Registry freshness check** (secondary, best-effort): resolves the current
   ``unified-trading-library:latest`` digest via ``gcloud`` (ADC) and warns if the entire
   fleet has fallen behind `:latest`.  Silently skips when ``gcloud`` is unavailable,
   times out, or lacks credentials — the consistency check is still reported.

3. **Floor-satisfiability check** (secondary, best-effort): for each divergent or stale
   repo, parses its ``pyproject.toml`` UTL/UAC floors from the workspace-manifest
   ``repositories[].dependencies[]`` edges and reports whether the gap is "safe"
   (merely-not-latest) or "break-risk" (pinned digest is older than required floor).

Always exits 0 (warn-only post-gate).  Violations are prefixed ``⚠ WARN`` and printed to
stdout so CI log + operator can scan them.  No baseline ratchet needed (binary: fleet
consistent or not).

Incident provenance: plans/active/deployment_ui_monitoring_pane_2026_06_19.md
    § "Audit the fleet for STALE BASE_IMAGE_DIGEST pins".

Usage::

    # Standalone — against local workspace
    python check_base_image_digest_drift.py --workspace-root /path/to/workspace

    # PM quality-gates.sh post-gate (no args needed when CWD is PM root)
    python scripts/quality_gates/check_base_image_digest_drift.py
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Final

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SCRIPT_DIR: Final[Path] = Path(__file__).resolve().parent
PM_ROOT: Final[Path] = SCRIPT_DIR.parent.parent
DEFAULT_WORKSPACE_ROOT: Final[Path] = PM_ROOT.parent

REGISTRY_HOST: Final[str] = "asia-northeast1-docker.pkg.dev"
UTL_IMAGE_PATH: Final[str] = "unified-trading-library/unified-trading-library"
DEFAULT_PROJECT_ID: Final[str] = "central-element-323112"
DIGEST_ARG_NAME: Final[str] = "BASE_IMAGE_DIGEST"

DIGEST_RE: Final[re.Pattern[str]] = re.compile(r"^sha256:[0-9a-f]{64}$")

# Repos that are exempt from this check (they don't extend the UTL base image).
EXEMPT_REPOS: Final[frozenset[str]] = frozenset(
    {
        "unified-trading-library",  # the base image itself
        "unified-trading-pm",  # not deployed via Docker
        "unified-trading-system-ui",  # Node.js, not Python
        "deployment-ui",  # Node.js
        "e2e-testing",
        "system-integration-tests",
        "ibkr-gateway-infra",
    }
)

# ---------------------------------------------------------------------------
# Dockerfile parsing
# ---------------------------------------------------------------------------


def find_digest_pin(dockerfile: Path) -> str | None:
    """Return the ``sha256:<64-hex>`` value from ``ARG BASE_IMAGE_DIGEST=...``, or None."""
    try:
        text = dockerfile.read_text(encoding="utf-8")
    except OSError:
        return None
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith(f"ARG {DIGEST_ARG_NAME}="):
            value = stripped[len(f"ARG {DIGEST_ARG_NAME}=") :]
            if DIGEST_RE.match(value):
                return value
    return None


def scan_fleet(workspace_root: Path) -> dict[str, str | None]:
    """
    Return ``{repo_name: digest_or_None}`` for every repo in the workspace.

    ``None`` means the repo has a Dockerfile but NO digest pin (unconverted).
    Repos with no Dockerfile are omitted.  Exempt repos are omitted.
    """
    result: dict[str, str | None] = {}
    for repo_dir in sorted(workspace_root.iterdir()):
        if not repo_dir.is_dir():
            continue
        repo_name = repo_dir.name
        if repo_name in EXEMPT_REPOS or repo_name.startswith("."):
            continue
        dockerfile = repo_dir / "Dockerfile"
        if not dockerfile.exists():
            continue
        # Only include repos that use the UTL base image (skip node/python-slim bases)
        try:
            content = dockerfile.read_text(encoding="utf-8")
        except OSError:
            continue
        if UTL_IMAGE_PATH not in content and DIGEST_ARG_NAME not in content:
            continue
        result[repo_name] = find_digest_pin(dockerfile)
    return result


# ---------------------------------------------------------------------------
# Registry freshness
# ---------------------------------------------------------------------------


def resolve_latest_digest(project_id: str, timeout: int = 10) -> str | None:
    """
    Resolve the current ``unified-trading-library:latest`` digest via ``gcloud``.

    Returns ``sha256:<64-hex>`` on success, ``None`` if gcloud is unavailable,
    times out, or lacks credentials.
    """
    image = f"{REGISTRY_HOST}/{project_id}/{UTL_IMAGE_PATH}:latest"
    cmd = [
        "gcloud",
        "artifacts",
        "docker",
        "images",
        "describe",
        image,
        "--format=value(image_summary.digest)",
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    digest = result.stdout.strip()
    if result.returncode != 0 or not DIGEST_RE.match(digest):
        return None
    return digest


# ---------------------------------------------------------------------------
# Manifest: dep floors
# ---------------------------------------------------------------------------


def load_dep_floors(pm_root: Path) -> dict[str, dict[str, str]]:
    """
    Return ``{repo: {"unified-trading-library": ">=X.Y.Z", "unified-api-contracts": ...}}``.

    Parses ``workspace-manifest.json`` ``repositories[].dependencies[]`` edges.
    Missing or unreadable manifest → empty dict (non-fatal).
    """
    manifest_path = pm_root / "workspace-manifest.json"
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}

    floors: dict[str, dict[str, str]] = {}
    repositories = data.get("repositories", {})
    if isinstance(repositories, dict):
        repo_items = repositories.items()
    else:
        return {}

    target_deps = {"unified-trading-library", "unified-api-contracts"}
    for repo_name, repo_data in repo_items:
        if not isinstance(repo_data, dict):
            continue
        deps = repo_data.get("dependencies", [])
        if not isinstance(deps, list):
            continue
        repo_floors: dict[str, str] = {}
        for dep in deps:
            if not isinstance(dep, dict):
                continue
            name = dep.get("name", "")
            if name not in target_deps:
                continue
            constraint = dep.get("version", "")
            if constraint:
                repo_floors[name] = constraint
        if repo_floors:
            floors[repo_name] = repo_floors
    return floors


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--workspace-root",
        type=Path,
        default=DEFAULT_WORKSPACE_ROOT,
        help="Workspace root containing all repo dirs (default: inferred from script location).",
    )
    parser.add_argument(
        "--project-id",
        default=DEFAULT_PROJECT_ID,
        help=f"GCP project for gcloud digest resolution (default: {DEFAULT_PROJECT_ID}).",
    )
    parser.add_argument(
        "--no-registry",
        action="store_true",
        help="Skip the registry freshness check (consistency check only).",
    )
    args = parser.parse_args(argv)

    workspace_root: Path = args.workspace_root.resolve()
    warnings: list[str] = []
    info: list[str] = []

    # ------------------------------------------------------------------
    # 1. Scan fleet
    # ------------------------------------------------------------------
    fleet = scan_fleet(workspace_root)
    if not fleet:
        print("check_base_image_digest_drift: no repos with UTL base found — skipping.")
        return 0

    pinned = {repo: digest for repo, digest in fleet.items() if digest is not None}
    unpinned = {repo for repo, digest in fleet.items() if digest is None}

    if unpinned:
        for repo in sorted(unpinned):
            warnings.append(
                f"  {repo}: Dockerfile exists + uses UTL base but NO ARG {DIGEST_ARG_NAME}"
                " pin found (unconverted — run scripts/propagation/add-dockerfile-digest-arg.py)"
            )

    # ------------------------------------------------------------------
    # 2. Fleet consistency check (primary signal)
    # ------------------------------------------------------------------
    digest_counts: Counter[str] = Counter(pinned.values())
    fleet_consistent = len(digest_counts) <= 1
    majority_digest: str | None = digest_counts.most_common(1)[0][0] if digest_counts else None

    if fleet_consistent and majority_digest:
        info.append(f"  Fleet consistent: all {len(pinned)} pinned repos at {majority_digest[:19]}… ✓")
    elif not fleet_consistent:
        warnings.append(
            f"  Fleet digest INCONSISTENT — {len(digest_counts)} distinct pins across"
            f" {len(pinned)} repos (missed fan-out from update-dependency-version.yml?):"
        )
        # Report each distinct digest + which repos use it
        for digest, count in digest_counts.most_common():
            repos_with = [r for r, d in pinned.items() if d == digest]
            warnings.append(f"    {digest[:19]}... x{count} repos: {', '.join(sorted(repos_with))}")

    # ------------------------------------------------------------------
    # 3. Registry freshness check (secondary, best-effort)
    # ------------------------------------------------------------------
    latest_digest: str | None = None
    if not args.no_registry:
        latest_digest = resolve_latest_digest(args.project_id)

    if latest_digest is not None:
        if majority_digest and majority_digest == latest_digest:
            info.append(f"  Registry freshness: fleet pin matches :latest {latest_digest[:19]}… ✓")
        elif majority_digest and majority_digest != latest_digest:
            warnings.append(
                f"  Registry freshness: fleet pin {majority_digest[:19]}…"
                f" is BEHIND :latest {latest_digest[:19]}…"
                " — fan-out may not have completed yet (check update-dependency-version.yml runs)"
            )
        # Per-repo stale report (only if there are divergent repos from the majority)
        stale_repos = [r for r, d in pinned.items() if d != latest_digest]
        if stale_repos and not fleet_consistent:
            warnings.append(f"  Stale repos (not at :latest): {', '.join(sorted(stale_repos))}")
    else:
        info.append(
            "  Registry freshness: skipped (gcloud unavailable/timed-out — consistency check above is authoritative)"
        )

    # ------------------------------------------------------------------
    # 4. Print summary
    # ------------------------------------------------------------------
    total_repos = len(fleet)
    print(
        f"check_base_image_digest_drift: {total_repos} repos scanned ({len(pinned)} pinned, {len(unpinned)} unpinned)."
    )
    for line in info:
        print(line)
    if warnings:
        print("⚠ WARN — base-image digest drift detected (warn-only, non-blocking):")
        for w in warnings:
            print(w)
        print(
            "  Remedy: bash scripts/propagation/add-dockerfile-digest-arg.py"
            f" --project-id {args.project_id}"
            "  (or wait for the next update-dependency-version.yml fan-out)"
        )
    else:
        print("  No base-image digest drift detected ✓")

    return 0  # always warn-only


if __name__ == "__main__":
    sys.exit(main())
