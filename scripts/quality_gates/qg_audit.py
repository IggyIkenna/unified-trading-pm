#!/usr/bin/env python3
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
"""qg_audit.py — sequential per-repo QG audit (peak RAM / time / violations / test stats).

Runs quality-gates.sh on each Python service repo SEQUENTIALLY (never parallel)
and captures:
  - Peak RSS (resident set size) via /usr/bin/time -v
  - Wall-clock duration
  - ruff format violations (lines/files needing reformatting)
  - ruff check (lint) violations
  - basedpyright errors + warnings
  - pytest pass/fail/skipped/error counts, grouped by test category (unit/integration/e2e/etc.)
  - Coverage percentage if reported

Output as JSON or YAML for parsing.

Usage
-----
    python3 scripts/quality_gates/qg_audit.py                          # all repos → qg_audit.json
    python3 scripts/quality_gates/qg_audit.py --output audit.yaml      # YAML format
    python3 scripts/quality_gates/qg_audit.py --repo execution-service # single repo
    python3 scripts/quality_gates/qg_audit.py --limit 3                # first 3 repos only
    python3 scripts/quality_gates/qg_audit.py --quick                  # QG --quick mode

Design notes
------------
- PYTEST_WORKERS=1 forced (single worker for clean memory measurement).
- QG_MEM_CAP=0 forced (don't cap; we WANT to see peak RAM unconstrained).
- Does NOT push, does NOT revert anything in the repo. Working tree is left as-is.
- Sequential — only one QG runs at a time.
- Per-repo timeout default 30 min (configurable).
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Final

SCRIPT_DIR: Final[Path] = Path(__file__).resolve().parent
PM_ROOT: Final[Path] = SCRIPT_DIR.parent.parent
WORKSPACE_ROOT: Final[Path] = PM_ROOT.parent
MANIFEST_PATH: Final[Path] = PM_ROOT / "workspace-manifest.json"
AUDITS_DIR: Final[Path] = PM_ROOT / "audits"

# Strip ANSI escape sequences (color codes) from QG output before storing.
ANSI_RE: Final[re.Pattern[str]] = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


def _strip_ansi(text: str) -> str:
    return ANSI_RE.sub("", text)


@dataclass
class RepoAudit:
    repo: str
    branch: str = ""
    qg_passed: bool = False
    duration_sec: float = 0.0
    peak_rss_mb: float = 0.0
    exit_code: int = -1
    timed_out: bool = False
    # ruff format
    ruff_format_files_changed: int = 0  # files reformatted
    # ruff lint
    ruff_lint_violations: int = 0
    # basedpyright
    basedpyright_errors: int = 0
    basedpyright_warnings: int = 0
    # pytest aggregate
    tests_passed: int = 0
    tests_failed: int = 0
    tests_skipped: int = 0
    tests_errors: int = 0
    tests_total: int = 0
    test_duration_sec: float = 0.0
    coverage_pct: float | None = None
    # per-category test breakdown (paths like tests/unit/, tests/integration/, etc.)
    tests_by_category: dict[str, dict[str, int]] = field(default_factory=dict)
    # QG step that failed (if any)
    failed_step: str = ""
    # Notable warnings / errors from output
    notes: list[str] = field(default_factory=list)
    # Stdout snippet (last 100 lines for failures)
    stdout_tail: str = ""


def _python_repos_with_qg() -> list[str]:
    """Return list of repo names that have scripts/quality-gates.sh."""
    repos: list[str] = []
    for child in sorted(WORKSPACE_ROOT.iterdir()):
        if not child.is_dir() or child.name.startswith("."):
            continue
        if child.name == "unified-trading-pm":
            continue  # PM has its own gates, skip
        if (child / "scripts" / "quality-gates.sh").exists():
            repos.append(child.name)
    return repos


def _current_branch(repo_path: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "branch", "--show-current"],
            cwd=repo_path,
            text=True,
            timeout=5,
        ).strip()
    except (subprocess.SubprocessError, OSError):
        return "(unknown)"


def _parse_ruff_format_count(line: str) -> int | None:
    """Match: '12 files would be reformatted' or 'X files reformatted, Y files left unchanged'."""
    m = re.search(r"(\d+)\s+file[s]?\s+(?:would be )?reformatted", line)
    if m:
        return int(m.group(1))
    return None


def _parse_ruff_lint_count(line: str) -> int | None:
    """Match: 'Found 13 errors' (ruff check)."""
    m = re.search(r"Found\s+(\d+)\s+error", line)
    if m:
        return int(m.group(1))
    return None


def _parse_basedpyright(line: str) -> tuple[int, int] | None:
    """Match: '13 errors, 0 warnings, 0 informations'."""
    m = re.search(r"(\d+)\s+error[s]?,\s+(\d+)\s+warning[s]?", line)
    if m:
        return int(m.group(1)), int(m.group(2))
    return None


def _parse_pytest_summary(line: str) -> dict[str, int] | None:
    """Match pytest summary line: '147 passed, 3 failed, 2 skipped, 1 error in 12.34s'.

    Must include 'in <N>s' suffix to disambiguate from other tools' output
    (e.g. ruff's 'Found 1 error' would otherwise match).
    """
    # Require "in NNN.NNs" suffix that pytest always emits in its summary line
    if not re.search(r"\bin\s+[\d.]+s\b", line):
        return None
    result: dict[str, int] = {}
    for kw in ("passed", "failed", "skipped", "error"):
        m = re.search(rf"\b(\d+)\s+{kw}\b", line)
        if m:
            # normalize "error"/"errors" to "errors"
            key = "errors" if kw == "error" else kw
            result[key] = int(m.group(1))
    return result if result else None


def _parse_coverage(line: str) -> float | None:
    """Match: 'TOTAL ... 78%' from pytest-cov output."""
    m = re.search(r"^TOTAL\s+.*?(\d+(?:\.\d+)?)%\s*$", line)
    if m:
        return float(m.group(1))
    # Alt format: 'coverage: ... 78.5%'
    m = re.search(r"coverage[:\s]+\d+\s+statements.*?(\d+(?:\.\d+)?)%", line)
    if m:
        return float(m.group(1))
    return None


def _parse_failed_step(stdout: str) -> str:
    """Find the [N/6] step or STEP X.Y that failed (last log_fail before exit)."""
    last_section = ""
    for line in stdout.splitlines():
        # Section header
        m = re.search(r"^\[(\d+(?:\.\d+)?)/6\]\s+(.+)|^STEP\s+(\d+\.\d+)\s+(.+)", line)
        if m:
            last_section = line.strip()
        # Failure indicator (after last section seen)
        if "❌" in line or re.search(r"\bFAIL\b|\bFAILED\b", line, re.IGNORECASE):
            return last_section or line.strip()[:100]
    return ""


def _categorize_tests(stdout: str) -> dict[str, dict[str, int]]:
    """Group pytest stats by test category (unit / integration / e2e) based on path collected."""
    categories: dict[str, dict[str, int]] = defaultdict(lambda: {"passed": 0, "failed": 0, "skipped": 0})
    # pytest dot-notation per-line: tests/unit/test_x.py::TestFoo::test_bar PASSED
    test_line_re = re.compile(r"tests/(\w+)/[^\s]+\s+(PASSED|FAILED|SKIPPED|ERROR)")
    for line in stdout.splitlines():
        m = test_line_re.search(line)
        if m:
            cat, outcome = m.group(1), m.group(2).lower()
            if outcome == "error":
                outcome = "errors"
            categories[cat][outcome] = categories[cat].get(outcome, 0) + 1
    # Trim categories not actually tested
    return {k: dict(v) for k, v in categories.items() if any(v.values())}


def audit_repo(
    repo: str,
    *,
    workspace_root: Path,
    quick: bool = False,
    timeout_sec: int = 1800,
    pytest_workers: int = 1,
) -> RepoAudit:
    """Run QG on one repo, parse output, return audit dataclass."""
    repo_path = workspace_root / repo
    audit = RepoAudit(repo=repo, branch=_current_branch(repo_path))

    qg_script = repo_path / "scripts" / "quality-gates.sh"
    if not qg_script.exists():
        audit.notes.append("no scripts/quality-gates.sh present — skipped")
        return audit

    # Build the command
    cmd = ["/usr/bin/time", "-v", "bash", str(qg_script), "--no-fix"]
    if quick:
        cmd.append("--quick")

    env = {
        **dict(__import__("os").environ),
        "PYTEST_WORKERS": str(pytest_workers),
        "QG_MEM_CAP": "0",  # no cap during audit — we want true peak
        "CLOUD_MOCK_MODE": "true",
        "CLOUD_PROVIDER": "local",
        "GCP_PROJECT_ID": "test-project",
    }

    started = time.time()
    try:
        proc = subprocess.run(
            cmd,
            cwd=repo_path,
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout_sec,
        )
        audit.exit_code = proc.returncode
        audit.qg_passed = proc.returncode == 0
    except subprocess.TimeoutExpired as e:
        audit.timed_out = True
        audit.exit_code = -1
        audit.notes.append(f"timed out after {timeout_sec}s")
        # e.stdout/stderr can be bytes|str|None; normalize to str
        timeout_stdout = e.stdout.decode("utf-8", errors="replace") if isinstance(e.stdout, bytes) else (e.stdout or "")
        timeout_stderr = e.stderr.decode("utf-8", errors="replace") if isinstance(e.stderr, bytes) else (e.stderr or "")
        proc = subprocess.CompletedProcess(args=cmd, returncode=-1, stdout=timeout_stdout, stderr=timeout_stderr)
    audit.duration_sec = round(time.time() - started, 2)

    # Strip ANSI color codes so JSON/YAML stays clean + grep-friendly
    stdout: str = _strip_ansi(proc.stdout or "")
    stderr: str = _strip_ansi(proc.stderr or "")
    combined = stdout + "\n" + stderr

    # Peak RSS from /usr/bin/time -v output
    for line in stderr.splitlines():
        m = re.search(r"Maximum resident set size \(kbytes\):\s+(\d+)", line)
        if m:
            audit.peak_rss_mb = round(int(m.group(1)) / 1024, 1)
            break

    # Parse violations + pytest from combined output
    for line in combined.splitlines():
        if (count := _parse_ruff_format_count(line)) is not None:
            audit.ruff_format_files_changed = count
        if (count := _parse_ruff_lint_count(line)) is not None:
            audit.ruff_lint_violations = count
        if (bp := _parse_basedpyright(line)) is not None:
            audit.basedpyright_errors, audit.basedpyright_warnings = bp
        if (pt := _parse_pytest_summary(line)) is not None:
            # Take the LAST pytest summary line (most authoritative)
            audit.tests_passed = pt.get("passed", audit.tests_passed)
            audit.tests_failed = pt.get("failed", audit.tests_failed)
            audit.tests_skipped = pt.get("skipped", audit.tests_skipped)
            audit.tests_errors = pt.get("errors", audit.tests_errors)
        if (cov := _parse_coverage(line)) is not None:
            audit.coverage_pct = cov

    audit.tests_total = audit.tests_passed + audit.tests_failed + audit.tests_skipped + audit.tests_errors
    audit.tests_by_category = _categorize_tests(stdout)

    # Test wall-time from pytest summary
    m = re.search(r"in\s+([\d.]+)s\b", stdout)
    if m:
        audit.test_duration_sec = float(m.group(1))

    if not audit.qg_passed:
        audit.failed_step = _parse_failed_step(combined)
        # Tail of stdout for context (last 100 lines)
        tail_lines = stdout.splitlines()[-100:]
        audit.stdout_tail = "\n".join(tail_lines)

    return audit


def write_output(audits: list[RepoAudit], output_path: Path, fmt: str, *, verbose: bool = True) -> None:
    payload = {
        "audit_run_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "workspace_root": str(WORKSPACE_ROOT),
        "total_repos": len(audits),
        "passed": sum(1 for a in audits if a.qg_passed),
        "failed": sum(1 for a in audits if not a.qg_passed and not a.timed_out),
        "timed_out": sum(1 for a in audits if a.timed_out),
        "total_duration_sec": round(sum(a.duration_sec for a in audits), 2),
        "peak_rss_max_mb": round(max((a.peak_rss_mb for a in audits), default=0), 1),
        "repos": [asdict(a) for a in audits],
    }

    if fmt == "yaml":
        try:
            import yaml  # type: ignore[import-untyped]

            with open(output_path, "w", encoding="utf-8") as f:
                yaml.safe_dump(payload, f, default_flow_style=False, sort_keys=False)
        except ImportError:
            print("PyYAML not available, falling back to JSON", file=sys.stderr)
            output_path = output_path.with_suffix(".json")
            fmt = "json"

    if fmt == "json":
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, default=str)
    if verbose:
        print(f"\nAudit written to: {output_path}")


def print_running_summary(audit: RepoAudit) -> None:
    status = "✅ PASS" if audit.qg_passed else ("⏱ TIMEOUT" if audit.timed_out else "❌ FAIL")
    print(
        f"  {status}  {audit.repo:<40} "
        f"{audit.duration_sec:>6.1f}s  "
        f"{audit.peak_rss_mb:>6.0f} MB  "
        f"tests={audit.tests_total}({audit.tests_failed}f/{audit.tests_errors}e)  "
        f"ruff={audit.ruff_lint_violations}  "
        f"bp={audit.basedpyright_errors}e/{audit.basedpyright_warnings}w"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        "-o",
        default=None,
        help=("Output path (.json or .yaml). Default: <pm>/audits/qg_audit_<YYYYMMDD_HHMMSS>.json"),
    )
    parser.add_argument("--repo", help="Audit a single repo (instead of all)")
    parser.add_argument(
        "--repos",
        help="Audit a comma-separated list of repos (e.g. 'foo,bar,baz')",
    )
    parser.add_argument("--limit", type=int, help="Only audit first N repos (for testing)")
    parser.add_argument("--quick", action="store_true", help="QG --quick mode (skip integration tests)")
    parser.add_argument("--timeout", type=int, default=1800, help="Per-repo timeout in seconds (default 1800)")
    parser.add_argument("--workers", type=int, default=1, help="PYTEST_WORKERS (default 1; sequential single-worker)")
    args = parser.parse_args()

    if args.repo:
        repos = [args.repo]
    elif args.repos:
        repos = [r.strip() for r in args.repos.split(",") if r.strip()]
    else:
        repos = _python_repos_with_qg()
        if args.limit:
            repos = repos[: args.limit]

    # Default output: <pm>/audits/qg_audit_<UTC_timestamp>.json
    if args.output is None:
        AUDITS_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S", time.gmtime())
        output_path = AUDITS_DIR / f"qg_audit_{timestamp}.json"
        output_fmt = "json"
    else:
        output_fmt = "yaml" if args.output.endswith((".yml", ".yaml")) else "json"
        output_path = Path(args.output).resolve()
        # If user passed a relative path with no slash, drop it in audits/
        if not Path(args.output).is_absolute() and "/" not in args.output:
            AUDITS_DIR.mkdir(parents=True, exist_ok=True)
            output_path = AUDITS_DIR / args.output

    print(f"QG audit — {len(repos)} repos, sequential, workers={args.workers}, quick={args.quick}")
    print(f"Output: {output_path} (format={output_fmt})")
    print()

    audits: list[RepoAudit] = []
    for i, repo in enumerate(repos, 1):
        print(f"[{i}/{len(repos)}] {repo} ...", flush=True)
        audit = audit_repo(
            repo,
            workspace_root=WORKSPACE_ROOT,
            quick=args.quick,
            timeout_sec=args.timeout,
            pytest_workers=args.workers,
        )
        audits.append(audit)
        print_running_summary(audit)
        # Incremental write — flush after EACH repo so partial results survive
        # a crash / Ctrl+C. Quiet mode so log isn't spammed.
        write_output(audits, output_path, output_fmt, verbose=False)

    # Final write with verbose=True for the closing log line
    write_output(audits, output_path, output_fmt, verbose=True)

    # Exit non-zero if any failures (so CI can pick it up)
    fail_count = sum(1 for a in audits if not a.qg_passed)
    print(f"\n{len(audits) - fail_count}/{len(audits)} passed.")
    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
