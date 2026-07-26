#!/usr/bin/env python3
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
"""Glue-pool starvation monitor — the cheapest HONEST signal that the self-hosted `glue` runner
pool has stopped accepting jobs.

Root incident (2026-07-16/17, `issues/silent_failures_surfacing_as_generic_promotion_lag_2026_07_17.md`):
the `glue` pool went fully dead for 16h (all 5 runners crash-looping on a missing IAM grant,
swallowed by a `|| true`), and NOTHING paged — the only visible symptom was a generic
`PROMOTION LAG > 60m` warning that read exactly like routine latency. A naive "is the host up"
check would ALSO have missed it: the sibling `glue-writer` pool lives on the same host and stayed
healthy throughout, so host-level liveness cannot distinguish "the box is up" from "the `glue`
pool specifically stopped picking up jobs".

The unambiguous signal that needs no VM access: a `glue`-labelled job has been sitting `queued`
for more than `--threshold-min` minutes while ZERO `glue`-labelled jobs are `in_progress` anywhere
in the repo. A busy-but-alive pool (jobs queued behind an in-progress job) is NOT starvation — it
is normal backlog. Only "queued AND nothing running" means the pool stopped consuming its queue.

Scope: the `glue`/`glue-writer` self-hosted pools are `unified-trading-pm`-only (every
`runs-on: [self-hosted, ..., glue]` caller lives in this repo's own `.github/workflows/` — see
`scripts/self-hosted-runners/setup-glue-runners.sh`), so this monitor never needs to query another
repo. `glue-writer` jobs are deliberately EXCLUDED (disjoint label, its own pool, out of scope —
see setup-glue-runners.sh's "labels are DISJOINT on purpose" note); job label lists are matched by
EXACT string membership so "glue-writer" never satisfies a "glue" check.

MUST run on a GitHub-hosted runner, never `glue` itself — a dead-man-switch that ran on the pool
it watches would go dark exactly when it is needed (the same failure-independence rule already
applied to `branch-health.yml` / `ci-health.yml` — see
`scripts/self-hosted-runners/classify-glue-workflows.sh` KEEP_MONITORS).

Stdlib + `gh` only. Prints a human report; with `--slack` prints it Slack-ready and writes
`starved=true|false` to `$GITHUB_OUTPUT` (if set) for the calling workflow to gate on. Exit 1 if
starved (so a required-check/alert can gate), else exit 0.

Usage:
    glue_pool_starvation_monitor.py [--repo IggyIkenna/unified-trading-pm] [--threshold-min 20]
                                     [--now-iso 2026-07-26T12:00:00Z] [--slack]
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import sys
from typing import cast

GLUE_LABEL = "glue"

# Bound on how many queued/in-progress runs we'll fan out job-lookups for in one tick. The `glue`
# pool serves ~37 low-frequency movers (setup-glue-runners.sh), so real backlogs are small; this
# is a safety cap against a pathological burst, not an expected ceiling. A cap HIT is logged, never
# silent (single-walk-discipline sibling: bound the fan-out, don't hide the truncation).
MAX_RUNS_PER_STATUS = 100


def _run_gh_json(args: list[str]) -> object:
    """Run `gh api <args>` and parse the JSON response. Raises on a non-zero exit."""
    proc = subprocess.run(["gh", "api", *args], capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"gh api {' '.join(args)} failed (rc={proc.returncode}): {proc.stderr.strip()}")
    return cast("object", json.loads(proc.stdout))


def fetch_runs(repo: str, status: str) -> list[dict[str, object]]:
    """Fetch up to MAX_RUNS_PER_STATUS workflow runs in the given `status` for `repo`."""
    body = _run_gh_json([f"repos/{repo}/actions/runs?status={status}&per_page={MAX_RUNS_PER_STATUS}"])
    if not isinstance(body, dict):
        return []
    runs = cast("object", body.get("workflow_runs") or [])
    if not isinstance(runs, list):
        return []
    out: list[dict[str, object]] = [r for r in cast("list[object]", runs) if isinstance(r, dict)]
    total = body.get("total_count")
    if isinstance(total, int) and total > len(out):
        print(f"::warning::glue_pool_starvation_monitor: {status} runs capped at {len(out)}/{total}")
    return out


def fetch_jobs(repo: str, run_id: object) -> list[dict[str, object]]:
    """Fetch the jobs for one workflow run."""
    body = _run_gh_json([f"repos/{repo}/actions/runs/{run_id}/jobs?per_page=100"])
    if not isinstance(body, dict):
        return []
    jobs = cast("object", body.get("jobs") or [])
    if not isinstance(jobs, list):
        return []
    return [j for j in cast("list[object]", jobs) if isinstance(j, dict)]


def is_glue_job(labels: object) -> bool:
    """True iff the job's requested `runs-on` labels include exactly `glue` (never `glue-writer`)."""
    if not isinstance(labels, list):
        return False
    return GLUE_LABEL in cast("list[object]", labels)


def parse_iso(ts: object) -> dt.datetime | None:
    if not isinstance(ts, str) or not ts:
        return None
    try:
        return dt.datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None


def find_starved_glue_jobs(
    queued_runs_with_glue_jobs: list[tuple[dict[str, object], list[dict[str, object]]]],
    in_progress_glue_count: int,
    threshold_min: float,
    now: dt.datetime,
) -> list[dict[str, object]]:
    """Pure decision: which queued `glue` jobs have aged past `threshold_min` while the pool is idle.

    `queued_runs_with_glue_jobs` pairs each queued workflow run with the subset of its jobs that
    requested the `glue` label (already filtered by the caller via `is_glue_job`).

    A queued glue job whose OWN queue age exceeds the threshold is only a real starvation signal
    when `in_progress_glue_count == 0` — otherwise it is normal backlog behind a running job on the
    same (finite) pool.
    """
    if in_progress_glue_count > 0:
        return []
    starved: list[dict[str, object]] = []
    for run, glue_jobs in queued_runs_with_glue_jobs:
        queued_since = parse_iso(run.get("created_at"))
        if queued_since is None:
            continue
        age_min = (now - queued_since).total_seconds() / 60.0
        if age_min <= threshold_min:
            continue
        for job in glue_jobs:
            if job.get("status") != "queued":
                continue
            starved.append(
                {
                    "run_id": run.get("id"),
                    "run_name": run.get("name"),
                    "job_name": job.get("name"),
                    "html_url": run.get("html_url"),
                    "age_min": round(age_min, 1),
                }
            )
    return starved


def build_report(starved: list[dict[str, object]], threshold_min: float) -> str:
    if not starved:
        return f"glue pool healthy: no `glue`-labelled job queued > {threshold_min:g}m while idle."
    lines = [
        f":rotating_light: *glue pool starved* — {len(starved)} `glue`-labelled job(s) queued "
        f"> {threshold_min:g}m with ZERO glue jobs in progress (the pool has stopped consuming its queue):"
    ]
    for job in starved[:10]:
        url = job.get("html_url")
        name = job.get("job_name") or job.get("run_name") or job.get("run_id")
        link = f"<{url}|{name}>" if url else str(name)
        lines.append(f"  • {link} — queued {job.get('age_min')}m")
    if len(starved) > 10:
        lines.append(f"  … and {len(starved) - 10} more")
    return "\n".join(lines)


def _write_github_output(name: str, value: str) -> None:
    path = os.environ.get("GITHUB_OUTPUT")
    if not path:
        return
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(f"{name}={value}\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default="IggyIkenna/unified-trading-pm")
    parser.add_argument("--threshold-min", type=float, default=20.0)
    parser.add_argument("--now-iso", default=None, help="Override 'now' (testing/determinism)")
    parser.add_argument("--slack", action="store_true", help="Print a Slack-ready report block")
    args = parser.parse_args()

    now = parse_iso(args.now_iso) if args.now_iso else dt.datetime.now(dt.UTC)
    if now is None:
        print(f"invalid --now-iso: {args.now_iso!r}", file=sys.stderr)
        return 2

    queued_runs = fetch_runs(args.repo, "queued")
    in_progress_runs = fetch_runs(args.repo, "in_progress")

    queued_runs_with_glue_jobs = [
        (run, [j for j in fetch_jobs(args.repo, run.get("id")) if is_glue_job(j.get("labels"))]) for run in queued_runs
    ]

    in_progress_glue_count = 0
    for run in in_progress_runs:
        for job in fetch_jobs(args.repo, run.get("id")):
            if is_glue_job(job.get("labels")) and job.get("status") == "in_progress":
                in_progress_glue_count += 1

    starved = find_starved_glue_jobs(queued_runs_with_glue_jobs, in_progress_glue_count, args.threshold_min, now)
    report = build_report(starved, args.threshold_min)

    print(report)
    _write_github_output("starved", "true" if starved else "false")
    if args.slack:
        print("---SLACK---")
        print(report)

    return 1 if starved else 0


if __name__ == "__main__":
    sys.exit(main())
