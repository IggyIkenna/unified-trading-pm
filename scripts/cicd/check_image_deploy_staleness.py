#!/usr/bin/env python3
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
"""Fleet-wide LOUD failure signal for a cancelled/dropped cloud-build-router dispatch.

Ref: plans/active/issues/cloud_build_router_concurrency_drops_dispatch_2026_07_27.md § P2.

WHY this exists: `cloud-build-router.yml` fires a Cloud Build per `main`-branch merge via a
`repository_dispatch` chain (quality-gates-v2 → repository_dispatch → cloud-build-router →
`gcloud builds triggers run`). A cancelled/dropped hop in that chain (a shared GitHub Actions
concurrency group cancelling a sibling dispatch — the exact root cause this issue doc diagnosed
and fixed on 2026-07-27, see P1 above) is SILENT: no error, no Slack alert, no PR comment. The
only externally-observable symptom is "the deployed `:latest` image is older than it should be
given main's HEAD" — which nobody notices without independently diffing image-push-time against
merge-time, exactly what the P1 investigation had to do by hand.

WHAT this does: for every fleet repo that publishes a Docker image via cloud-build-router, compare
its `main` HEAD commit timestamp against its `:latest` image's push timestamp in Artifact Registry.
A HEAD newer than the image by more than the expected build+dispatch latency means a dispatch was
dropped (or the build/trigger is broken) — flagged as STALE, surfaced as a `::warning::` annotation
and (via the calling workflow) a Slack post, so this specific silent-failure class stops being
silent.

FAIL-OPEN on uncertainty (mirrors reconcile_release_tags.py / assert_deps_published_to_ar.py): a
`gh`/`gcloud` query miss for one repo is UNKNOWN, never counted as either healthy or stale. But
per the documented "silence on an empty input set is itself the outage" lesson (see
reconcile_release_tags.py's docstring — a ~4-week silent tag-mint outage read as "success" because
every repo happened to look like a no-op), this script explicitly distinguishes "N repos checked,
0 stale" from "N repos UNKNOWN (cannot tell)" and treats the latter as its own alarm — an
all-UNKNOWN run is a broken check, not a healthy fleet, and `--fail-on-stale` also fails on it.

Usage (from PM repo root, with `GH_TOKEN`/`GH_PAT` exported and `gcloud` authenticated):
    python3 scripts/cicd/check_image_deploy_staleness.py [--json] [--fail-on-stale]
                                                          [--stale-threshold-min N] [--owner OWNER]
                                                          [--project PROJECT]
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from datetime import datetime
from typing import cast

AR_HOST = "asia-northeast1-docker.pkg.dev"
# The single shared Docker AR repo every service image actually lands in (VERIFIED live against
# GCP 2026-07-28 — NOT the `_AR_REPO=unified-trading` substitution name in cloud-build-router.yml's
# comments, which does not correspond to a real AR repository; the live one is
# `unified-trading-system`, package name == service/repo name).
AR_REGISTRY_REPO = "unified-trading-system"

# The fleet repos that publish a service Docker image to AR_REGISTRY_REPO. NOT manifest-derived —
# `repo_type != 'library'` alone is not a reliable proxy (e.g. ibkr-gateway-infra is
# type=infrastructure like deployment-service, but does not build a Cloud Build image). Cross-
# checked live against `gcloud artifacts packages list --repository=unified-trading-system` on
# 2026-07-28: every name below has a matching package. NOTE this deliberately DROPS
# "agent-orchestrator" from digest-drift-sweep.yml's otherwise-similar `IMAGE_REPOS` array — it has
# no package in this AR repo at all (it runs as a VM process, not a Cloud Run image; see
# runtime-deployment-topology.md), so including it would make every run report a permanent false
# UNKNOWN. digest-drift-sweep.yml's own inclusion of it is for a different, narrower check
# (Dockerfile ARG presence) and is out of this task's scope to fix.
IMAGE_REPOS = [
    "alerting-service",
    "batch-live-reconciliation-service",
    "client-reporting-api",
    "deployment-api",
    "deployment-service",
    "execution-service",
    "features-service",
    "fund-administration-service",
    "greeks-service",
    "instruments-service",
    "market-data-processing-service",
    "market-tick-data-service",
    "ml-service",
    "strategy-service",
    "trading-agent-service",
]

# unified-trading-library is the one documented exception (cloud-build-router.yml): a
# `type: library` repo that still publishes a Docker base image (every service Dockerfile FROMs
# it), to its OWN dedicated AR repo rather than the shared `unified-trading` one.
UTL_REPO = "unified-trading-library"
UTL_AR_REGISTRY_REPO = "unified-trading-library"

# Expected build+dispatch latency: repository_dispatch fan-out + Cloud Build (~5-10 min) + the
# ldr-to-main-promote-fleet */15 cron cadence + a safety margin. A gap beyond this after main HEAD
# advances means the dispatch was dropped or the trigger is broken — not "still building".
DEFAULT_STALE_THRESHOLD_MIN = 45


def _gh(args: list[str]) -> tuple[int, str]:
    """Run ``gh api <args>`` → (returncode, stdout)."""
    proc = subprocess.run(["gh", "api", *args], capture_output=True, text=True)
    return proc.returncode, proc.stdout


def _loads(text: str) -> object:
    """``json.loads`` typed as ``object`` (json.loads is ``Any``; consume it at the boundary once)."""
    return cast("object", json.loads(text))


def _parse_iso(raw: str) -> datetime | None:
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def _main_head_commit_time(owner: str, repo: str) -> datetime | None:
    """UTC timestamp of `repo`'s `main` HEAD commit, or None if unresolvable (fail-open)."""
    rc, out = _gh([f"repos/{owner}/{repo}/commits/main", "--jq", ".commit.committer.date"])
    if rc != 0 or not out.strip():
        return None
    return _parse_iso(out.strip())


def _latest_image_push_time(project: str, registry_repo: str, service: str) -> datetime | None:
    """Push/update timestamp of ``<registry_repo>/<service>:latest`` in AR, or None (fail-open).

    Uses ``gcloud artifacts docker images list`` (NOT ``describe`` — verified live 2026-07-28 that
    ``describe`` returns only ``image_summary.{digest,fully_qualified_digest,registry,repository,
    slsa_build_level}``, no timestamp field at all; ``list --format=json`` is the one that actually
    carries ``updateTime``/``createTime``/``metadata.buildTime`` per entry).
    """
    image_path = f"{AR_HOST}/{project}/{registry_repo}/{service}"
    proc = subprocess.run(
        [
            "gcloud",
            "artifacts",
            "docker",
            "images",
            "list",
            image_path,
            "--project",
            project,
            "--include-tags",
            "--filter=tags:latest",
            "--format=json",
        ],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0 or not proc.stdout.strip():
        return None
    try:
        payload = _loads(proc.stdout)
    except (json.JSONDecodeError, ValueError):
        return None
    if not isinstance(payload, list) or not payload:
        return None
    entry = cast("dict[str, object]", payload[0])
    for key in ("updateTime", "createTime"):
        raw = entry.get(key)
        if isinstance(raw, str) and raw:
            parsed = _parse_iso(raw)
            if parsed is not None:
                return parsed
    metadata = entry.get("metadata")
    if isinstance(metadata, dict):
        raw_build = cast("dict[str, object]", metadata).get("buildTime")
        if isinstance(raw_build, str) and raw_build:
            return _parse_iso(raw_build)
    return None


def check(owner: str, project: str, stale_threshold_min: float) -> dict[str, object]:
    """Return {stale: [...], healthy: [...], unknown: [...], all_unknown: bool}."""
    repos_and_ar = [(repo, AR_REGISTRY_REPO) for repo in IMAGE_REPOS] + [(UTL_REPO, UTL_AR_REGISTRY_REPO)]

    stale: list[dict[str, object]] = []
    healthy: list[str] = []
    unknown: list[str] = []

    for repo, registry_repo in repos_and_ar:
        head_time = _main_head_commit_time(owner, repo)
        image_time = _latest_image_push_time(project, registry_repo, repo)
        if head_time is None or image_time is None:
            unknown.append(repo)
            continue
        gap_min = (head_time - image_time).total_seconds() / 60.0
        if gap_min > stale_threshold_min:
            stale.append(
                {
                    "repo": repo,
                    "main_head_time": head_time.isoformat(),
                    "latest_image_push_time": image_time.isoformat(),
                    "gap_minutes": round(gap_min, 1),
                }
            )
        else:
            healthy.append(repo)

    all_unknown = len(unknown) == len(repos_and_ar)
    return {"stale": stale, "healthy": healthy, "unknown": unknown, "all_unknown": all_unknown}


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Alarm when a fleet repo's deployed :latest image is stale vs its main HEAD "
        "(the loud failure signal for a cancelled/dropped cloud-build-router dispatch)."
    )
    _ = ap.add_argument("--owner", default="IggyIkenna")
    # No hardcoded project-id fallback (codex: no hardcoded prod project id) — empty when unset
    # → the AR query fails → the check reports UNKNOWN for that repo, the safe fail-open default
    # (mirrors assert_deps_published_to_ar.py's AR_PROJECT convention).
    _ = ap.add_argument("--project", default=os.environ.get("GCP_PROJECT_ID") or "")
    _ = ap.add_argument("--stale-threshold-min", type=float, default=DEFAULT_STALE_THRESHOLD_MIN)
    _ = ap.add_argument(
        "--fail-on-stale",
        action="store_true",
        help="exit non-zero when ≥1 repo is stale OR the check itself came back all-UNKNOWN "
        "(default: warn only, so a routine schedule tick doesn't hard-fail on a transient API miss)",
    )
    _ = ap.add_argument("--json", action="store_true", help="machine-readable output")
    ns = ap.parse_args()
    owner = cast(str, ns.owner)
    project = cast(str, ns.project)
    stale_threshold_min = cast(float, ns.stale_threshold_min)
    fail_on_stale = cast(bool, ns.fail_on_stale)
    as_json = cast(bool, ns.json)

    result = check(owner, project, stale_threshold_min)
    stale = cast("list[dict[str, object]]", result["stale"])
    healthy = cast("list[str]", result["healthy"])
    unknown = cast("list[str]", result["unknown"])
    all_unknown = cast(bool, result["all_unknown"])

    if as_json:
        print(json.dumps(result))
    else:
        print(
            f"Image-deploy staleness: {len(healthy)} healthy, {len(stale)} STALE, "
            f"{len(unknown)} UNKNOWN (of {len(healthy) + len(stale) + len(unknown)} checked)."
        )
        if stale:
            print(f"\n::warning::Image-deploy staleness: {len(stale)} repo(s) have a stale :latest image.")
            for s in stale:
                print(
                    f"  STALE {s['repo']}: main HEAD @ {s['main_head_time']}, "
                    f":latest pushed @ {s['latest_image_push_time']} "
                    f"(gap {s['gap_minutes']}min > {stale_threshold_min}min threshold)"
                )
            print(
                "  → the post-merge cloud-build-router dispatch for this repo was likely cancelled/dropped "
                "or its Cloud Build trigger is broken. Check `gh run list --workflow=cloud-build-router.yml` "
                "for a cancelled run in the merge window, and `gcloud builds list` for the repo's trigger.\n"
                "    SSOT: codex/08-workflows/ci-cd-flow.md § 'Image-deploy staleness check'; "
                "plans/active/issues/cloud_build_router_concurrency_drops_dispatch_2026_07_27.md."
            )
        if all_unknown:
            print(
                "\n::error::Image-deploy staleness check came back ALL-UNKNOWN "
                f"({len(unknown)} of {len(unknown)} repos) — this is the check itself failing "
                "(gh/gcloud auth broken, or every AR/GitHub query erroring), NOT a healthy fleet. "
                "Do not read this as '0 stale'."
            )
        elif unknown:
            print(f"  UNKNOWN (could not verify): {', '.join(unknown)}")

    if fail_on_stale and (stale or all_unknown):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
