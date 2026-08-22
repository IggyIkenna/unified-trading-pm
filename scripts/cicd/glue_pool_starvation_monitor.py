#!/usr/bin/env python3
# Epic: ci_master
# Lifecycle: permanent
# Delete-when: NA
"""Glue-pool starvation monitor — the cheapest HONEST signal that the self-hosted `glue` runner
pool has stopped accepting jobs, or is oversubscribed serving a single job while others queue.

Root incident (2026-07-16/17, `issues/silent_failures_surfacing_as_generic_promotion_lag_2026_07_17.md`):
the `glue` pool went fully dead for 16h (all 5 runners crash-looping on a missing IAM grant,
swallowed by a `|| true`), and NOTHING paged — the only visible symptom was a generic
`PROMOTION LAG > 60m` warning that read exactly like routine latency. A naive "is the host up"
check would ALSO have missed it: the sibling `glue-writer` pool lives on the same host and stayed
healthy throughout, so host-level liveness cannot distinguish "the box is up" from "the `glue`
pool specifically stopped picking up jobs".

Two detection modes (2026-08-08 addition of mode 2):

Mode 1 — STARVED (pool dead, --threshold-min default 20 min):
  A `glue`-labelled job has been sitting `queued` for more than `--threshold-min` minutes while
  ZERO `glue`-labelled jobs are `in_progress` anywhere. A busy-but-alive pool (jobs queued behind
  an in-progress job) is NOT starvation — it is normal backlog. Only "queued AND nothing running"
  means the pool stopped consuming its queue.

Mode 2 — STALLED (pool oversubscribed, --busy-queued-min default 120 min):
  A `quality-gates-v2` (or other) run is `in_progress` at the workflow level (upstream jobs
  completed) but has individual QG-slice jobs still `queued` behind a single busy glue runner for
  more than `--busy-queued-min` minutes. Root incident (2026-08-03, instruments-service run
  30800087100): the run sat `in_progress` for 1h45m with both QG-slice jobs `queued`, the pool's
  lone runner reporting `online, busy=true` — invisible to mode 1 because `in_progress_glue_count
  > 0` (mode 1 treats that as healthy backlog). The fix: scan `in_progress` runs too and alert
  when their individual `queued` glue jobs exceed the higher threshold. Source:
  `issues/fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md` ## Follow-up [SCRIPT] P1.

Scope: after the 2026-08-05 runner-fleet split, each service repo has its own glue pool on the
dedicated escalation VM. `--repos-file` accepts a file of short repo names (one per line,
owner-prefixed if they contain `/`, otherwise `IggyIkenna/<name>` assumed) so the monitor can
sweep the full `self-hosted-qg-repos.txt` fleet, not just a single repo. `glue-writer` jobs are
deliberately EXCLUDED (disjoint label, its own pool, out of scope — see setup-glue-runners.sh's
"labels are DISJOINT on purpose" note).

MUST run on a GitHub-hosted runner, never `glue` itself — a dead-man-switch that ran on the pool
it watches would go dark exactly when it is needed.

Stdlib + `gh` only. Prints a human report; with `--slack` prints it Slack-ready and writes
`starved=true|false` to `$GITHUB_OUTPUT` (if set) for the calling workflow to gate on. Exit 1 if
any alert (starved OR stalled), else exit 0.

Usage:
    glue_pool_starvation_monitor.py [--repo IggyIkenna/unified-trading-pm]
                                     [--repos-file scripts/workflow-templates/self-hosted-qg-repos.txt]
                                     [--threshold-min 20] [--busy-queued-min 120]
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


def find_stalled_glue_jobs(
    in_progress_runs_with_queued_glue_jobs: list[tuple[dict[str, object], list[dict[str, object]]]],
    busy_queued_min: float,
    now: dt.datetime,
) -> list[dict[str, object]]:
    """Mode 2 — pool-oversubscribed detection.

    Fires when an `in_progress` workflow run has `glue`-labelled jobs still individually `queued`
    past `busy_queued_min`. Unlike mode 1 (starved), this fires even when `in_progress_glue_count >
    0` — the point is that the pool's lone busy runner cannot serve a new job fast enough.

    Uses run `created_at` as the age proxy (the earliest moment a queued glue job could have been
    waiting); job-level `started_at` is null for queued jobs.
    """
    stalled: list[dict[str, object]] = []
    for run, glue_jobs in in_progress_runs_with_queued_glue_jobs:
        run_started = parse_iso(run.get("created_at"))
        if run_started is None:
            continue
        age_min = (now - run_started).total_seconds() / 60.0
        if age_min <= busy_queued_min:
            continue
        for job in glue_jobs:
            if job.get("status") != "queued":
                continue
            stalled.append(
                {
                    "run_id": run.get("id"),
                    "run_name": run.get("name"),
                    "job_name": job.get("name"),
                    "html_url": run.get("html_url"),
                    "age_min": round(age_min, 1),
                }
            )
    return stalled


def build_report(
    starved: list[dict[str, object]],
    stalled: list[dict[str, object]],
    threshold_min: float,
    busy_queued_min: float,
) -> str:
    def _fmt_jobs(jobs: list[dict[str, object]]) -> list[str]:
        lines = []
        for job in jobs[:10]:
            url = job.get("html_url")
            name = job.get("job_name") or job.get("run_name") or job.get("run_id")
            link = f"<{url}|{name}>" if url else str(name)
            lines.append(f"  • {link} — queued {job.get('age_min')}m")
        if len(jobs) > 10:
            lines.append(f"  … and {len(jobs) - 10} more")
        return lines

    sections: list[str] = []

    if starved:
        lines = [
            f":rotating_light: *glue pool STARVED* — {len(starved)} `glue`-labelled job(s) queued "
            f"> {threshold_min:g}m with ZERO glue jobs in progress (the pool has stopped consuming its queue):"
        ]
        lines.extend(_fmt_jobs(starved))
        sections.append("\n".join(lines))

    if stalled:
        lines = [
            f":hourglass_flowing_sand: *glue pool STALLED* — {len(stalled)} `glue`-labelled job(s) "
            f"queued > {busy_queued_min:g}m behind a busy runner (pool oversubscribed — the lone "
            f"running job is blocking new dispatches):"
        ]
        lines.extend(_fmt_jobs(stalled))
        sections.append("\n".join(lines))

    if not sections:
        return (
            f"glue pool healthy: no starvation (>{threshold_min:g}m idle-pool) or "
            f"stall (>{busy_queued_min:g}m busy-pool) detected."
        )
    return "\n\n".join(sections)


def _write_github_output(name: str, value: str) -> None:
    path = os.environ.get("GITHUB_OUTPUT")
    if not path:
        return
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(f"{name}={value}\n")


def _load_repos(repo_arg: str, repos_file: str | None) -> list[str]:
    """Return the list of `owner/repo` strings to scan.

    If `--repos-file` is given, read one short name per line (comments + blanks skipped). Names
    that already contain `/` are used as-is; bare names get the `IggyIkenna/` prefix. The
    `--repo` default is always included as the anchor so PM-self is never dropped.
    """
    if repos_file is None:
        return [repo_arg]
    repos: list[str] = []
    seen: set[str] = set()

    def _add(name: str) -> None:
        if name and name not in seen:
            repos.append(name)
            seen.add(name)

    _add(repo_arg)
    with open(repos_file, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.split("#")[0].strip()
            if not line:
                continue
            full = line if "/" in line else f"IggyIkenna/{line}"
            _add(full)
    return repos


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default="IggyIkenna/unified-trading-pm")
    parser.add_argument(
        "--repos-file",
        default=None,
        help="File of short repo names (one per line) to sweep; adds org prefix if bare",
    )
    parser.add_argument("--threshold-min", type=float, default=20.0)
    parser.add_argument(
        "--busy-queued-min",
        type=float,
        default=120.0,
        help="Minutes a glue job may be queued behind a BUSY runner before alerting (mode 2)",
    )
    parser.add_argument("--now-iso", default=None, help="Override 'now' (testing/determinism)")
    parser.add_argument("--slack", action="store_true", help="Print a Slack-ready report block")
    args = parser.parse_args()

    now = parse_iso(args.now_iso) if args.now_iso else dt.datetime.now(dt.UTC)
    if now is None:
        print(f"invalid --now-iso: {args.now_iso!r}", file=sys.stderr)
        return 2

    repos = _load_repos(args.repo, args.repos_file)

    all_starved: list[dict[str, object]] = []
    all_stalled: list[dict[str, object]] = []

    for repo in repos:
        queued_runs = fetch_runs(repo, "queued")
        in_progress_runs = fetch_runs(repo, "in_progress")

        queued_runs_with_glue_jobs = [
            (run, [j for j in fetch_jobs(repo, run.get("id")) if is_glue_job(j.get("labels"))]) for run in queued_runs
        ]

        in_progress_glue_count = 0
        in_progress_runs_with_queued_glue_jobs: list[tuple[dict[str, object], list[dict[str, object]]]] = []
        for run in in_progress_runs:
            jobs = fetch_jobs(repo, run.get("id"))
            glue_jobs = [j for j in jobs if is_glue_job(j.get("labels"))]
            for job in glue_jobs:
                if job.get("status") == "in_progress":
                    in_progress_glue_count += 1
            queued_glue_jobs = [j for j in glue_jobs if j.get("status") == "queued"]
            if queued_glue_jobs:
                in_progress_runs_with_queued_glue_jobs.append((run, queued_glue_jobs))

        all_starved.extend(
            find_starved_glue_jobs(queued_runs_with_glue_jobs, in_progress_glue_count, args.threshold_min, now)
        )
        all_stalled.extend(find_stalled_glue_jobs(in_progress_runs_with_queued_glue_jobs, args.busy_queued_min, now))

    report = build_report(all_starved, all_stalled, args.threshold_min, args.busy_queued_min)
    print(report)

    alerted = bool(all_starved or all_stalled)
    _write_github_output("starved", "true" if alerted else "false")
    if args.slack:
        print("---SLACK---")
        print(report)

    return 1 if alerted else 0


if __name__ == "__main__":
    sys.exit(main())
