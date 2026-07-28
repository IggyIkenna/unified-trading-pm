#!/usr/bin/env python3
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
"""Build-dispatch staleness monitor — pages when an `ldr_main` repo's `main`
HEAD has sat un-built longer than the expected build+dispatch latency.

WHY: `cloud-build-router.yml`'s `repository_dispatch` can be silently
cancelled/dropped under merge-pileup load (several repos' promote PRs merging
within the same few-minute window race each other's freeze-check/build runs)
— see
`plans/active/issues/cloud_build_router_concurrency_drops_dispatch_2026_07_27.md`.
The only symptom is a stale deployed image with every CI signal green (PR
merged, quality-gates-v2 passed, no error anywhere). This monitor closes the
"did the build I expect to have happened, actually happen" gap: for every
image-building `ldr_main` repo, compare `main`'s HEAD commit timestamp against
its `:latest` Artifact Registry image's most recent push timestamp, and page
if the gap exceeds the expected build+dispatch latency.

REPO ENUMERATION IS SELF-UPDATING, not a hand-maintained array:
`digest-drift-sweep.yml`'s `IMAGE_REPOS` array was found STALE during this
investigation (missing several real image-building repos — e.g.
client-reporting-api, ibkr-gateway-infra, unified-trading-system-ui,
deployment-ui — that DO have a `cloudbuild.yaml`). So every
`promotion_model: ldr_main` repo in `workspace-manifest.json` is probed for a
`cloudbuild.yaml` on its `main` branch via the GitHub contents API instead: a
genuine 404 excludes it (not image-building — e.g. a pure-library/test-harness
repo); any OTHER non-200 status FAILS LOUD (mirrors digest-drift-sweep.yml's
anti-silent-noop discipline — an auth/scope regression reading as "0
image-building repos found" would silently disable this whole monitor, the
exact failure class it exists to catch).

Stdlib + `gh` + `gcloud` only. Prints a human report; with `--slack` prints a
Slack-formatted block for the calling workflow to post via notify-slack.yml's
`dedup_key` + `cooldown_min` (transition-only paging, not a re-page every
tick). Exit 1 if any repo is stale (so a required-check/alert can gate).

Usage:
    build_dispatch_staleness_monitor.py [--threshold-min 45] [--now-iso 2026-07-28T00:00:00Z] [--slack]
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
from typing import cast

OWNER = "IggyIkenna"
AR_HOST = "asia-northeast1-docker.pkg.dev"
AR_REPO = "unified-trading"
DEFAULT_PROJECT_ID = "central-element-323112"

# Expected build+dispatch latency ceiling: a Cloud Build run for these images
# typically completes within a few minutes of dispatch, plus the router's own
# freeze-check hop — 45m is a generous floor that self-clears on any healthy
# build while still catching a genuinely dropped dispatch (which never clears
# on its own). Mirrors DEFAULT_STALE_IMAGE_GRACE_MIN (30m) in
# deployment-service's stale_image_watcher.py (DP-VM-007), the sibling
# Cloud-Run-freshness check this monitor complements.
DEFAULT_THRESHOLD_MIN = 45


def _gh_json(path: str) -> object:
    """GET an api.github.com path as JSON. None on any non-200 (fail-toward-unmeasured)."""
    r = subprocess.run(["gh", "api", path], capture_output=True, text=True)
    if r.returncode != 0 or not r.stdout:
        return None
    try:
        return cast("object", json.loads(r.stdout))
    except json.JSONDecodeError:
        return None


def _gh_status(path: str) -> int | None:
    """HTTP status of a GET (`gh api` exits non-zero on 4xx, so read the status line)."""
    r = subprocess.run(["gh", "api", "-i", path], capture_output=True, text=True)
    first = r.stdout.split("\n", 1)[0].strip() if r.stdout else ""
    m = re.match(r"HTTP/[\d.]+\s+(\d{3})", first)
    return int(m.group(1)) if m else None


def _ldr_main_repos(manifest_path: str) -> list[str]:
    with open(manifest_path) as f:
        m = cast("dict[str, object]", json.load(f))
    repos = cast("dict[str, object]", m.get("repositories") or {})
    out: list[str] = []
    for name, cfg in repos.items():
        if isinstance(cfg, dict) and cast("dict[str, object]", cfg).get("promotion_model") == "ldr_main":
            out.append(str(name))
    return sorted(out)


def _is_image_building(repo: str) -> bool:
    """True iff `repo` has a `cloudbuild.yaml` on `main` (probed via contents API).

    A genuine 404 excludes the repo (not image-building). Any OTHER non-200
    status is a LOUD failure — see module docstring.
    """
    status = _gh_status(f"repos/{OWNER}/{repo}/contents/cloudbuild.yaml?ref=main")
    if status == 200:
        return True
    if status == 404:
        return False
    raise RuntimeError(f"{repo}: unexpected HTTP {status} probing cloudbuild.yaml@main — auth/scope failure?")


def _main_head(repo: str) -> tuple[str, dt.datetime] | None:
    """Return (sha, committer_date) of `repo`'s `main` HEAD, or None if unmeasured."""
    d = _gh_json(f"repos/{OWNER}/{repo}/commits/main")
    if not isinstance(d, dict):
        return None
    dd = cast("dict[str, object]", d)
    sha = str(dd.get("sha") or "")
    commit = cast("dict[str, object]", dd.get("commit") or {})
    committer = cast("dict[str, object]", commit.get("committer") or {})
    ds = str(committer.get("date") or "")
    if not sha or not ds:
        return None
    try:
        when = dt.datetime.fromisoformat(ds.replace("Z", "+00:00"))
    except ValueError:
        return None
    return sha, when


def _latest_image_push_time(repo: str, gcp_project: str) -> dt.datetime | None:
    """The `:latest`-tagged image's most recent push time in Artifact Registry.

    None when the image/tag is absent or the query errors — fail toward NO
    false alert; an unresolvable image is reported as "no image found" by the
    caller, not silently treated as fresh.
    """
    image_path = f"{AR_HOST}/{gcp_project}/{AR_REPO}/{repo}"
    r = subprocess.run(
        [
            "gcloud",
            "artifacts",
            "docker",
            "images",
            "list",
            image_path,
            "--include-tags",
            "--filter=tags:latest",
            "--sort-by=~UPDATE_TIME",
            "--limit=1",
            "--format=value(update_time)",
        ],
        capture_output=True,
        text=True,
    )
    out = r.stdout.strip()
    if r.returncode != 0 or not out:
        return None
    try:
        return dt.datetime.fromisoformat(out.replace("Z", "+00:00"))
    except ValueError:
        return None


def _stale(
    main_when: dt.datetime, image_when: dt.datetime | None, now: dt.datetime, thresh_s: float
) -> tuple[bool, str]:
    """Pure decision: is this repo's `main` HEAD un-built beyond the threshold?

    Grace window: a `main` HEAD younger than the threshold is NEVER stale (a
    build genuinely in flight looks identical to a dropped one for the first
    few minutes).
    """
    age = (now - main_when).total_seconds()
    if age < thresh_s:
        return False, f"main HEAD is only {int(age // 60)}m old — within the build+dispatch grace window"
    if image_when is None:
        return True, f"main HEAD {int(age // 60)}m old with NO `:latest` image found in Artifact Registry"
    if image_when >= main_when:
        return False, "`:latest` image was pushed at/after main HEAD — build is current"
    lag = (main_when - image_when).total_seconds()
    if lag < thresh_s:
        return False, f"`:latest` image is only {int(lag // 60)}m behind main HEAD — within grace window"
    return True, f"`:latest` image is {int(lag // 60)}m behind main HEAD (main HEAD itself {int(age // 60)}m old)"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--threshold-min", type=int, default=DEFAULT_THRESHOLD_MIN)
    ap.add_argument("--now-iso", default="", help="UTC now (no wallclock in CI sandbox); else uses gh server time")
    ap.add_argument("--slack", action="store_true")
    ap.add_argument(
        "--manifest",
        default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "workspace-manifest.json"),
    )
    args = ap.parse_args()
    thresh_s = cast(int, args.threshold_min) * 60.0
    project_id = os.environ.get("GCP_PROJECT_ID") or DEFAULT_PROJECT_ID

    now_iso = cast(str, args.now_iso)
    if now_iso:
        now = dt.datetime.fromisoformat(now_iso.replace("Z", "+00:00"))
    else:
        r = subprocess.run(["gh", "api", "-i", "rate_limit"], capture_output=True, text=True)
        now = None
        for line in r.stdout.splitlines():
            if line.lower().startswith("date:"):
                try:
                    now = dt.datetime.strptime(line[5:].strip(), "%a, %d %b %Y %H:%M:%S GMT").replace(tzinfo=dt.UTC)
                except ValueError:
                    now = None
                break
        if now is None:
            print("could not resolve server time; pass --now-iso")
            return 0

    repos = _ldr_main_repos(cast(str, args.manifest))
    findings: list[str] = []
    checked = 0
    for repo in repos:
        image_building = _is_image_building(repo)
        if not image_building:
            continue
        head = _main_head(repo)
        if head is None:
            continue  # unmeasured (transient gh error) — never a false page
        _sha, main_when = head
        image_when = _latest_image_push_time(repo, project_id)
        checked += 1
        stale, reason = _stale(main_when, image_when, now, thresh_s)
        if stale:
            findings.append(f"{repo}: {reason}")

    if not findings:
        print(
            f"✅ build-dispatch staleness: {checked} image-building repo(s) checked, "
            f"all current (within {int(thresh_s // 60)}m)"
        )
        return 0

    if cast(bool, args.slack):
        # ── ERROR-POINTER MESSAGE STANDARD (alert_quality_audit_2026_06_18) ──────────
        _m = int(thresh_s // 60)
        _max_lines = 6
        header = f":rotating_light: *BUILD DISPATCH STALE > {_m}m* — {len(findings)} repo(s) un-built on `main`"
        body_lines = [f"  • {f}" for f in findings[:_max_lines]]
        if len(findings) > _max_lines:
            body_lines.append(f"  • … +{len(findings) - _max_lines} more")
        pointer = (
            "→ re-trigger via `gcloud builds triggers run <repo>-prod --branch=main "
            "--substitutions=..._SHA=<main-head-sha>...` "
            "(see cloud_build_router_concurrency_drops_dispatch_2026_07_27.md)"
        )
        print(header + "\\n" + "\\n".join(body_lines) + "\\n" + pointer)
    else:
        print(f"⚠️  build-dispatch stale ({len(findings)}):")
        for f in findings:
            print(f"  - {f}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
