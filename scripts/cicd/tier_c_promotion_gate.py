#!/usr/bin/env python3
"""Tier C — LDR→staging auto-promotion gate (dep-order + Tier-A readiness).

The Tier C promotion bot (`ldr-to-staging-promote.yml`) drains the committed
`live-defi-rollout` backlog onto `staging` per repo. Before it opens a
LDR→staging PR for repo X, this gate decides whether X is *safe* to promote.

It is the **LDR→staging mirror** of quickmerge.sh STAGE 1.7 and
staging-to-main.yml STAGE 1.8 (staging→main). The only axis that changes is
which ci_status values count as "dep is already on the TARGET line":

    quickmerge STAGE 1.7   target = staging  → dep must be STAGING_GREEN+   (same set as here)
    staging-to-main 1.8    target = main     → dep must be MAIN_GREEN / SIT_VALIDATED
    Tier C (this file)     target = staging  → dep must be STAGING_GREEN / SIT_VALIDATED / MAIN_GREEN

ci_status lifecycle (SSOT: ci-status-update.yml):
    NOT_CONFIGURED → LOCAL_PASS → FEATURE_GREEN → STAGING_PENDING
        → STAGING_GREEN → SIT_VALIDATED → MAIN_GREEN   (any → FAILING on QG fail)

A dep is "on staging" once it has reached STAGING_GREEN; everything beyond
(SIT_VALIDATED, MAIN_GREEN) is also on staging by construction.

Two gates, both fail-OPEN on missing data (consistent with STAGE 1.8 / the
readiness gate — never block on absent signal, only on an explicit negative):

  Tier A (LDR CI not red):  repo's own ci_status must not be FAILING.
  Dep-order:                every tracked dep must be on staging (≥ STAGING_GREEN).

Safe-defaults (all PASS):
  - manifest missing / unreadable        → pass (no data)
  - repo not in manifest                 → pass (untracked)
  - dep not in manifest                  → pass (untracked dep)
  - dep ci_status unset / None           → pass (treat as external / not tracked)
  - repo ci_status unset / None          → pass Tier A (not yet assessed)

(Tier B — full-workspace SIT green — is a *workflow-level* gate read from the
system-integration-tests run result; it is not a per-repo manifest signal, so it
lives in the workflow, not here.)

CLI:
    python3 scripts/cicd/tier_c_promotion_gate.py <repo> [--manifest PATH]
    exit 0 = PROMOTE (gate passed), exit 1 = BLOCK (reason on stdout)
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import cast

# ci_status values that mean a dep has reached (or passed) the staging line.
ON_STAGING_STATUSES: frozenset[str] = frozenset({"STAGING_GREEN", "SIT_VALIDATED", "MAIN_GREEN"})

# The only value that means the repo's own LDR CI is red (Tier A block).
LDR_RED_STATUS = "FAILING"

DEFAULT_MANIFEST = "workspace-manifest.json"


@dataclass(frozen=True)
class GateResult:
    """Outcome of evaluating one repo for LDR→staging promotion."""

    repo: str
    promote: bool
    reason: str


def _dep_name(dep: object) -> str:
    """Extract a dependency's repo name from either a dict or a bare string."""
    if isinstance(dep, dict):
        name = cast("dict[str, object]", dep).get("name", "")
        return str(name) if name else ""
    return str(dep)


def evaluate_repo(manifest: dict[str, object], repo: str) -> GateResult:
    """Decide whether `repo` is safe to promote LDR→staging.

    Pure function of the manifest dict — no I/O, no git. Fail-open on missing
    data so the gate never blocks on an absent signal.
    """
    repos_obj = manifest.get("repositories", {})
    if not isinstance(repos_obj, dict) or repo not in repos_obj:
        return GateResult(repo, True, "PASS: no manifest entry (untracked repo)")
    repos = cast("dict[str, object]", repos_obj)

    repo_info_obj = repos[repo]
    if not isinstance(repo_info_obj, dict):
        return GateResult(repo, True, "PASS: malformed manifest entry (treated as untracked)")
    repo_info = cast("dict[str, object]", repo_info_obj)

    # ── Tier A: LDR CI must not be red ──────────────────────────────────────
    own_status = repo_info.get("ci_status")
    if own_status == LDR_RED_STATUS:
        return GateResult(
            repo,
            False,
            f"BLOCK: Tier A — {repo} LDR CI is {LDR_RED_STATUS}; fix LDR red before promoting to staging",
        )

    # ── Dep-order: every tracked dep must be on staging ─────────────────────
    deps_obj = repo_info.get("dependencies", [])
    deps = cast("list[object]", deps_obj) if isinstance(deps_obj, list) else []
    blocked: list[str] = []
    for dep in deps:
        name = _dep_name(dep)
        if not name or name not in repos:
            continue  # untracked dep → safe-default pass
        dep_info_obj = repos[name]
        if not isinstance(dep_info_obj, dict):
            continue
        dep_status = cast("dict[str, object]", dep_info_obj).get("ci_status")
        if not dep_status:
            # M3 fail-CLOSED: this dep IS tracked in the manifest (it passed the `name not in repos`
            # filter above) but carries no ci_status — a never-written / reset / reconcile-dropped
            # value. Treating it as a pass would promote dependents out of order on a blank status
            # (amplified by C2/H2, which can blank ci_status). A genuinely-untracked dep already
            # `continue`d above; here, unset on a TRACKED dep blocks.
            blocked.append(f"{name}:UNSET")
            continue
        if dep_status not in ON_STAGING_STATUSES:
            blocked.append(f"{name}:{dep_status}")

    if blocked:
        deps_str = ", ".join(blocked)
        return GateResult(
            repo,
            False,
            (
                f"BLOCK: dep-order — {repo} depends on {len(blocked)} dep(s) not yet on staging "
                f"({deps_str}). Promote them to staging first (≥ STAGING_GREEN), then retry."
            ),
        )

    return GateResult(repo, True, "PASS: LDR CI not red + all tracked deps on staging")


def _overlay_firestore_ci_status(manifest: dict[str, object]) -> None:
    """Overlay Firestore-authoritative ci_status values into manifest repos in-place.

    Phase 2 reader migration (ci_status_firestore_side_store plan): the manifest is the
    offline fallback cache; Firestore is the live SSOT. Safe no-op when Firestore is
    unavailable (google-cloud-firestore not installed, no GCP credentials, or network error)
    — the manifest ci_status values are already the fallback for evaluate_repo().
    """
    try:
        from ci_status_store import resolve_ci_status_map  # noqa: imports-inside-functions

        ci_map = resolve_ci_status_map(manifest)
        repos_obj = manifest.get("repositories", {})
        if isinstance(repos_obj, dict):
            for r, s in ci_map.items():
                r_obj = repos_obj.get(r)
                if isinstance(r_obj, dict):
                    cast("dict[str, object]", r_obj)["ci_status"] = s
    except ModuleNotFoundError as exc:
        # Gap 8 (2026-06-16): the SDK being absent is a CI-config regression, not graceful
        # degradation — the gate is now deciding on the STALE manifest cache. Make it LOUD
        # (silent fallback is exactly how mis-gating hid). `::warning::` surfaces in the run UI.
        print(
            f"::warning::tier_c_promotion_gate: Firestore SDK unavailable ({exc}) — "
            "deciding on STALE manifest ci_status cache. Install google-cloud-firestore."
        )
    except Exception as exc:  # Firestore genuinely degraded: warn + fall back to manifest cache.
        print(
            f"::warning::tier_c_promotion_gate: Firestore ci_status read failed "
            f"({type(exc).__name__}: {exc}) — falling back to manifest cache."
        )


def load_manifest(path: str | Path) -> dict[str, object]:
    """Load the workspace manifest; raise FileNotFoundError/JSONDecodeError to caller."""
    with open(path) as fh:
        data = cast("object", json.load(fh))
    if not isinstance(data, dict):
        raise ValueError(f"manifest at {path} is not a JSON object")
    return cast("dict[str, object]", data)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Tier C LDR→staging promotion gate")
    parser.add_argument("repo", help="repo name to evaluate")
    parser.add_argument("--manifest", default=DEFAULT_MANIFEST, help="path to workspace-manifest.json")
    args = parser.parse_args(argv)
    repo = cast("str", args.repo)
    manifest_path = cast("str", args.manifest)

    try:
        manifest = load_manifest(manifest_path)
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as exc:
        # Fail-open: no manifest data → pass (matches STAGE 1.8 safe-default).
        print(f"PASS: manifest unreadable ({exc}) — gate skipped (safe-default)")
        return 0

    _overlay_firestore_ci_status(manifest)

    result = evaluate_repo(manifest, repo)
    print(result.reason)
    return 0 if result.promote else 1


if __name__ == "__main__":
    sys.exit(main())
