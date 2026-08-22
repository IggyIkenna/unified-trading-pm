#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Profile quality-gates.sh step wall-times by instrumenting QG output.

Runs quality-gates.sh on a target repo, intercepts output line-by-line,
timestamps each log_section header, and produces a per-step timing report.

Usage
-----
    python3 scripts/quality_gates/profile_qg_steps.py --repo execution-service
    python3 scripts/quality_gates/profile_qg_steps.py --repo unified-trading-library --json
    python3 scripts/quality_gates/profile_qg_steps.py --all   # all 15 service repos (slow)

Output
------
Per-step wall-time table sorted by duration (slowest first). Includes:
  - Section name (e.g. "[3/6] TESTS", "STEP 5.17")
  - Duration in seconds
  - % of total QG time
  - Pass/fail/warn status (parsed from log_success/log_fail/log_warn output)

Optimization proposals are printed for steps that take >20% of total time.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final, cast

# ── Constants ─────────────────────────────────────────────────────────────────

SCRIPT_DIR: Final[Path] = Path(__file__).resolve().parent
PM_ROOT: Final[Path] = SCRIPT_DIR.parent.parent
WORKSPACE_ROOT_DEFAULT: Final[Path] = PM_ROOT.parent
MANIFEST_PATH: Final[Path] = PM_ROOT / "workspace-manifest.json"

# Patterns that mark the start of a new section in QG output
SECTION_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"(?:\[(?:[0-9]+(?:\.[0-9]+)?|ACT)/6\]"  # [N/6] or [N.M/6] section headers
    r"|STEP [0-9]+\.[0-9]+"  # STEP N.M
    r"|\[ACT\])"  # [ACT] section
)

PASS_PATTERN: Final[re.Pattern[str]] = re.compile(r"✅|✓|log_success|PASS")
FAIL_PATTERN: Final[re.Pattern[str]] = re.compile(r"❌|✗|log_fail|FAIL|ERROR")
WARN_PATTERN: Final[re.Pattern[str]] = re.compile(r"⚠|WARN|warning")

# Known slow steps with optimization notes
OPTIMIZATION_NOTES: Final[dict[str, str]] = {
    "[3/6] TESTS": (
        "Tests are usually the slowest step. Optimizations: (1) pytest-xdist already enabled "
        "via PYTEST_WORKERS — verify worker count matches CPU cores; (2) use `--dist worksteal` "
        "instead of `--dist load` for better balancing; (3) mark slow tests with @pytest.mark.slow "
        "and skip in quick mode."
    ),
    "[4/6] TYPE CHECK": (
        "basedpyright can be slow on large codebases. Optimizations: (1) ensure BASEDPYRIGHT_CACHE_DIR "
        "is set and writable (cache reuse halves re-check time); (2) use incremental mode (enabled by "
        "default in basedpyright); (3) exclude large generated files from pyrightconfig.json."
    ),
    "[5/6] CODEX COMPLIANCE": (
        "CODEX compliance has 60+ STEP checks. Optimizations: (1) most STEPs use `rg` — already fast; "
        "(2) STEPs that run on the full source tree for every commit could be batched; (3) STEP 5.17 "
        "(cloudbuild.yaml schema validation) runs yamllint + jq — consider caching schema."
    ),
    "[2/6] LINT": (
        "Ruff format+check is usually fast (<5s). If slow: (1) check if auto-fix is rewriting many files "
        "(indicates pre-existing formatting debt); (2) ruff caches by default — verify .ruff_cache is "
        "not cleared between runs."
    ),
}


# ── Data model ────────────────────────────────────────────────────────────────


@dataclass
class StepTiming:
    name: str
    start: float
    end: float = 0.0
    status: str = "unknown"  # "pass" | "fail" | "warn" | "unknown"
    lines_seen: int = 0

    @property
    def duration_s(self) -> float:
        return max(0.0, self.end - self.start)

    @property
    def duration_ms(self) -> int:
        return int(self.duration_s * 1000)


@dataclass
class ProfileReport:
    repo_name: str
    total_duration_s: float
    exit_code: int
    steps: list[StepTiming] = field(default_factory=list[StepTiming])

    @property
    def slowest_steps(self) -> list[StepTiming]:
        return sorted(self.steps, key=lambda s: s.duration_s, reverse=True)

    def to_table(self) -> str:
        lines = [
            f"\nQG Step Profile — {self.repo_name}",
            f"Total: {self.total_duration_s:.1f}s  Exit: {self.exit_code}",
            "",
            f"{'Step':<40} {'Duration':>10} {'% Total':>8} {'Status':<8}",
            "-" * 70,
        ]
        for step in self.slowest_steps:
            pct = (step.duration_s / self.total_duration_s * 100) if self.total_duration_s > 0 else 0.0
            icon = (
                "✅"
                if step.status == "pass"
                else ("❌" if step.status == "fail" else ("⚠️ " if step.status == "warn" else "  "))
            )
            lines.append(f"{step.name:<40} {step.duration_s:>8.1f}s {pct:>7.1f}% {icon}")
        return "\n".join(lines)

    def optimization_hints(self) -> list[str]:
        hints = []
        for step in self.slowest_steps[:3]:
            pct = (step.duration_s / self.total_duration_s * 100) if self.total_duration_s > 0 else 0.0
            if pct > 20:
                for key, note in OPTIMIZATION_NOTES.items():
                    if key in step.name:
                        hints.append(f"\n[{step.name} — {pct:.0f}% of total]\n  {note}")
                        break
        return hints


# ── Profiler ──────────────────────────────────────────────────────────────────


def _profile_repo(repo_path: Path) -> ProfileReport:
    qg_script = repo_path / "scripts" / "quality-gates.sh"
    repo_name = repo_path.name

    if not qg_script.exists():
        return ProfileReport(repo_name=repo_name, total_duration_s=0.0, exit_code=-1)

    steps: list[StepTiming] = []
    current: StepTiming | None = None
    wall_start = time.monotonic()

    try:
        proc = subprocess.Popen(
            ["bash", str(qg_script)],
            cwd=repo_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        assert proc.stdout is not None

        for line in proc.stdout:
            now = time.monotonic()
            m = SECTION_PATTERN.search(line)
            if m:
                if current is not None:
                    current.end = now
                    steps.append(current)
                current = StepTiming(name=m.group(0), start=now)
            elif current is not None:
                current.lines_seen += 1
                if FAIL_PATTERN.search(line):
                    current.status = "fail"
                elif WARN_PATTERN.search(line) and current.status == "unknown":
                    current.status = "warn"
                elif PASS_PATTERN.search(line) and current.status == "unknown":
                    current.status = "pass"

        proc.wait()
        exit_code = proc.returncode or 0
    except Exception as e:  # noqa: broad-except — per-repo isolation: one repo's QG-invocation
        # failure must not abort profiling the remaining repos
        print(f"Error running QG for {repo_name}: {e}", file=sys.stderr)
        exit_code = -1

    wall_end = time.monotonic()
    if current is not None:
        current.end = wall_end
        steps.append(current)

    return ProfileReport(
        repo_name=repo_name,
        total_duration_s=wall_end - wall_start,
        exit_code=exit_code,
        steps=steps,
    )


# ── Main ─────────────────────────────────────────────────────────────────────


def run(
    workspace_root: Path,
    repo_name: str | None = None,
    all_repos: bool = False,
    output_json: bool = False,
) -> int:
    if not MANIFEST_PATH.exists():
        print(f"ERROR: manifest not found at {MANIFEST_PATH}", file=sys.stderr)
        return 1

    import json as _json

    manifest_data = cast(dict[str, object], _json.loads(MANIFEST_PATH.read_text()))
    repos_raw = manifest_data.get("repositories", {})  # noqa: qg-empty-fallback
    if not isinstance(repos_raw, dict):
        print("ERROR: unexpected manifest structure", file=sys.stderr)
        return 1
    manifest = cast(dict[str, dict[str, str]], repos_raw)

    target_repos: list[str] = []
    if repo_name:
        target_repos = [repo_name]
    elif all_repos:
        target_repos = [
            r
            for r, meta in manifest.items()
            if not meta.get("archived_into") and meta.get("type") not in {"ui", "devops"}
        ]
    else:
        print("Specify --repo NAME or --all", file=sys.stderr)
        return 1

    reports: list[ProfileReport] = []
    for rname in target_repos:
        repo_path = workspace_root / rname
        if not repo_path.exists():
            print(f"Skipping {rname} (not found at {repo_path})", file=sys.stderr)
            continue
        print(f"Profiling {rname}...", file=sys.stderr)
        report = _profile_repo(repo_path)
        reports.append(report)

    if output_json:
        out = [
            {
                "repo": r.repo_name,
                "total_s": round(r.total_duration_s, 2),
                "exit_code": r.exit_code,
                "steps": [
                    {
                        "name": s.name,
                        "duration_s": round(s.duration_s, 2),
                        "pct": round(s.duration_s / r.total_duration_s * 100, 1) if r.total_duration_s > 0 else 0.0,
                        "status": s.status,
                    }
                    for s in r.slowest_steps
                ],
            }
            for r in reports
        ]
        print(_json.dumps(out, indent=2))
        return 1 if any(r.exit_code != 0 for r in reports) else 0

    for report in reports:
        print(report.to_table())
        hints = report.optimization_hints()
        if hints:
            print("\n**Optimization hints:**")
            for h in hints:
                print(h)
        print()

    return 1 if any(r.exit_code != 0 for r in reports) else 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--workspace-root", type=Path, default=WORKSPACE_ROOT_DEFAULT)
    parser.add_argument("--repo", help="Profile a single repo by name")
    parser.add_argument("--all", action="store_true", dest="all_repos", help="Profile all service repos (slow)")
    parser.add_argument("--json", action="store_true", dest="output_json", help="Machine-readable JSON output")
    args = parser.parse_args()

    workspace_root = cast(Path, args.workspace_root)
    repo_name = cast(str | None, args.repo)
    all_repos = cast(bool, args.all_repos)
    output_json = cast(bool, args.output_json)
    sys.exit(run(workspace_root=workspace_root, repo_name=repo_name, all_repos=all_repos, output_json=output_json))


if __name__ == "__main__":
    main()
