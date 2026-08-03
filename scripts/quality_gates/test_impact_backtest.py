# Epic: deployment_and_user_management_master
# Lifecycle: permanent
# Delete-when: NA
"""Historical-commit backtest for the test-impact selector.

Operator-directed accelerator (2026-08-03): instead of waiting the full 2-week
live shadow-trial window, replay the already-built `test_impact_selector.py`
against commits that already happened, where the real outcome is already known.

For each target repo: list recent `quality-gates-v2` CI runs (`gh run list`),
keep the ones where the run's own "tests" QG-selector leg genuinely FAILED,
try to attribute the failure to a specific test file from the run's log (real
CI logs are messy — a run killed by an infra-level SIGINT/timeout with no
per-test attribution is EXCLUDED from the sample, never forced in), then
replay the selector against that commit's real diff (from this workspace's
own local clone) and check whether the real failing test falls inside the
selector's narrowed set. A failure outside the narrowed set is a genuine
divergence — same severity as a live-trial divergence, not a lesser finding
because it came from a backtest.

Plan: test_impact_fleet_wide_measurement_and_rollout_2026_08_03.md
(operator decision, 2026-08-03: accelerate validation via historical backtest).
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from test_impact_selector import classify_diff, load_allowlist

_FAILED_NODEID: re.Pattern[str] = re.compile(r"^FAILED (?P<path>[\w./-]+\.py)::(?P<test>\S+)")
_TRACEBACK_TEST_FILE: re.Pattern[str] = re.compile(
    r'File "[^"]*?/(?P<path>tests/[\w./-]+\.py)", line \d+, in (?P<test>\w+)'
)


# ── gh CLI wrappers ───────────────────────────────────────────────────────────


def gh_run_list(repo: str, workflow: str, limit: int) -> list[dict[str, object]]:
    proc = subprocess.run(
        [
            "gh",
            "run",
            "list",
            "--repo",
            f"IggyIkenna/{repo}",
            "--workflow",
            workflow,
            "--limit",
            str(limit),
            "--json",
            "databaseId,conclusion,createdAt,event,headSha",
        ],
        capture_output=True,
        text=True,
        timeout=60,
        check=True,
    )
    result = json.loads(proc.stdout)
    if not isinstance(result, list):
        raise ValueError(f"gh run list returned non-list JSON for {repo}: {type(result)!r}")
    return result


def gh_run_log(repo: str, run_id: int) -> str:
    proc = subprocess.run(
        ["gh", "run", "view", str(run_id), "--repo", f"IggyIkenna/{repo}", "--log"],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    return proc.stdout


# ── Failure attribution ───────────────────────────────────────────────────────


@dataclass(frozen=True)
class AttributedFailure:
    run_id: int
    head_sha: str
    failing_test_files: frozenset[str]
    attribution_method: str


def attribute_failure(run_id: int, head_sha: str, log_text: str) -> AttributedFailure | None:
    """Try to extract which real test file(s) failed. None if unattributable —
    e.g. an infra-level SIGINT/OSError kill with no per-test signal at all."""
    if "QG selector 'tests' FAILED" not in log_text:
        return None  # not a test-content failure (lint/typecheck/other leg)

    failing: set[str] = set()
    for line in log_text.splitlines():
        content = line.split("\t")[-1].strip()
        m = _FAILED_NODEID.match(content)
        if m:
            failing.add(m.group("path"))
    if failing:
        return AttributedFailure(run_id, head_sha, frozenset(failing), "pytest_failed_nodeid")

    # Fallback: a Timeout/crash mid-test — the LAST traceback frame naming a
    # tests/ file is where execution was stuck when it fired.
    last_test_file: str | None = None
    for line in log_text.splitlines():
        content = line.split("\t")[-1]
        m = _TRACEBACK_TEST_FILE.search(content)
        if m:
            last_test_file = m.group("path")
    if last_test_file:
        return AttributedFailure(run_id, head_sha, frozenset({last_test_file}), "traceback_last_test_frame")

    return None


# ── Backtest ───────────────────────────────────────────────────────────────


@dataclass
class Divergence:
    run_id: int
    head_sha: str
    failing_test_file: str
    narrowed_set_size: int


@dataclass
class RepoBacktestResult:
    repo: str
    runs_listed: int
    tests_leg_failures: int
    attributed: int
    unattributable: int
    commit_not_local: int
    no_py_diff: int
    trivially_safe_full_suite: int
    divergences: list[Divergence]


def backtest_repo(repo: str, repo_root: Path, allowlist: dict[str, object], limit: int) -> RepoBacktestResult:
    runs = gh_run_list(repo, "quality-gates-v2.yml", limit)
    failed_runs = [r for r in runs if r.get("conclusion") == "failure"]

    attributed_failures: list[AttributedFailure] = []
    unattributable = 0
    for r in failed_runs:
        run_id = r["databaseId"]
        head_sha = r["headSha"]
        assert isinstance(run_id, int)
        assert isinstance(head_sha, str)
        log_text = gh_run_log(repo, run_id)
        att = attribute_failure(run_id, head_sha, log_text)
        if att is None:
            unattributable += 1
        else:
            attributed_failures.append(att)

    commit_not_local = 0
    no_py_diff = 0
    trivially_safe = 0
    divergences: list[Divergence] = []

    for att in attributed_failures:
        diff_proc = subprocess.run(
            ["git", "diff", "--name-only", f"{att.head_sha}~1", att.head_sha],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if diff_proc.returncode != 0:
            commit_not_local += 1
            continue
        changed = [
            (repo_root / f).resolve()
            for f in diff_proc.stdout.splitlines()
            if f.endswith(".py") and (repo_root / f).is_file()
        ]
        if not changed:
            no_py_diff += 1
            continue

        result = classify_diff(repo_root, repo, changed, allowlist)
        if result.run_full_suite:
            trivially_safe += 1  # full suite would have run everything anyway
            continue

        for failing_file in att.failing_test_files:
            failing_path = (repo_root / failing_file).resolve()
            if failing_path not in result.narrowed_test_files:
                divergences.append(Divergence(att.run_id, att.head_sha, failing_file, len(result.narrowed_test_files)))

    return RepoBacktestResult(
        repo=repo,
        runs_listed=len(runs),
        tests_leg_failures=len(failed_runs),
        attributed=len(attributed_failures),
        unattributable=unattributable,
        commit_not_local=commit_not_local,
        no_py_diff=no_py_diff,
        trivially_safe_full_suite=trivially_safe,
        divergences=divergences,
    )


def format_result(result: RepoBacktestResult) -> str:
    lines = [
        f"=== {result.repo} ===",
        f"  CI runs listed (quality-gates-v2): {result.runs_listed}",
        f"  Runs with conclusion=failure: {result.tests_leg_failures}",
        f"  Attributed to a specific failing test file: {result.attributed}",
        f"  Unattributable (infra-level kill, no per-test signal): {result.unattributable}",
        f"  Attributed but commit not in local clone: {result.commit_not_local}",
        f"  Attributed but no .py diff found: {result.no_py_diff}",
        f"  Trivially safe (selector said RUN_FULL_SUITE=true anyway): {result.trivially_safe_full_suite}",
        f"  USABLE BACKTEST SAMPLE SIZE: "
        f"{result.attributed - result.commit_not_local - result.no_py_diff - result.trivially_safe_full_suite}",
        f"  DIVERGENCES FOUND: {len(result.divergences)}",
    ]
    for d in result.divergences:
        lines.append(
            f"    - run {d.run_id} ({d.head_sha[:10]}): {d.failing_test_file} NOT in narrowed set "
            f"(narrowed set size={d.narrowed_set_size})"
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Historical-commit backtest for the test-impact selector.")
    _ = parser.add_argument("--workspace-root", type=Path, required=True)
    _ = parser.add_argument("--repo", action="append", required=True, dest="repos")
    _ = parser.add_argument("--limit", type=int, default=50, help="CI runs to list per repo (most recent first).")
    default_allowlist = Path(__file__).resolve().parent / "test_impact_allowlist.yaml"
    _ = parser.add_argument("--allowlist", type=Path, default=default_allowlist)
    args = parser.parse_args(argv)

    allowlist = load_allowlist(args.allowlist)
    for repo in args.repos:
        repo_root = (args.workspace_root / repo).resolve()
        if not repo_root.is_dir():
            print(f"SKIP {repo}: not found at {repo_root}", file=sys.stderr)
            continue
        result = backtest_repo(repo, repo_root, allowlist, args.limit)
        print(format_result(result))
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
