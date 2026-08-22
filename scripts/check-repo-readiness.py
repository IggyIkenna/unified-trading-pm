#!/usr/bin/env python3.13
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# SCHEMA_PROVENANCE_EXEMPT — PM-internal tooling models, not domain schemas
"""
Repo Readiness Verifier

Reads declared CR/DR/BR state from codex/10-audit/repos/{repo}.yaml,
runs automated verification checks, and reports mismatches.

Usage:
  python scripts/check-repo-readiness.py --repo unified-events-interface
  python scripts/check-repo-readiness.py --tier T0
  python scripts/check-repo-readiness.py --all

Environment:
  WORKSPACE_ROOT: path to workspace root (default: parent of this script's grandparent)
  CODEX_PATH: path to codex root (default: unified-trading-pm/codex/ derived from script location)
"""

from __future__ import annotations

import argparse
import contextlib
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, cast

# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------

_SCRIPT_DIR = Path(__file__).resolve().parent
_PM_ROOT = _SCRIPT_DIR.parent
_DEFAULT_WORKSPACE_ROOT = _PM_ROOT.parent

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TIER_ALIASES: dict[str, list[str]] = {
    "T0": ["0"],
    "T1": ["1"],
    "T2": ["2"],
    "T3": ["3"],
    "T4": ["service"],
    "T5": ["api"],
    "T6": ["ui"],
    "infra": ["devops", "infrastructure", "integration"],
}

StatusLiteral = Literal["PASS", "FAIL", "MISMATCH", "UNVERIFIED", "SKIP"]


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class GateResult:
    gate: str
    declared: str
    verified: StatusLiteral
    detail: str = ""


@dataclass
class RepoReadinessResult:
    repo_name: str
    declared_stage: str
    gates: list[GateResult] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# YAML / manifest loading
# ---------------------------------------------------------------------------


def _load_yaml_simple(path: Path) -> dict[str, object]:
    """
    Load a YAML file.  Tries pyyaml first; falls back to a minimal
    line-by-line parser for simple flat schemas (key: value only).
    """
    try:
        import yaml  # type: ignore[import-untyped]

        with path.open() as fh:
            loaded: object = cast(object, yaml.safe_load(fh))
        if isinstance(loaded, dict):
            return cast(dict[str, object], loaded)
        return {}
    except ModuleNotFoundError:
        pass

    result: dict[str, object] = {}
    with path.open() as fh:
        for line in fh:
            line = line.rstrip()
            if not line or line.startswith("#") or line.startswith(" ") or line.startswith("\t"):
                continue
            if ":" not in line:
                continue
            key, _, raw_value = line.partition(":")
            value = raw_value.strip().strip('"').strip("'")
            result[key.strip()] = value
    return result


def _load_manifest(workspace_root: Path) -> dict[str, dict[str, object]]:
    manifest_path = workspace_root / "unified-trading-pm" / "workspace-manifest.json"
    if not manifest_path.exists():
        return {}
    try:
        raw: object = cast(object, json.loads(manifest_path.read_text()))
        if not isinstance(raw, dict):
            return {}
        raw_dict = cast(dict[str, object], raw)
        # Check canonical key first: "repositories"
        inner_repos = raw_dict.get("repositories")
        if isinstance(inner_repos, dict):
            return cast(dict[str, dict[str, object]], inner_repos)
        # Fallback: "repos"
        inner_repos = raw_dict.get("repos")
        if isinstance(inner_repos, dict):
            return cast(dict[str, dict[str, object]], inner_repos)
        # Last resort: detect if top-level values are repo dicts (have arch_tier key)
        first_val = next(iter(raw_dict.values()), None)
        if isinstance(first_val, dict) and "arch_tier" in first_val:
            return cast(dict[str, dict[str, object]], raw_dict)
    except (OSError, json.JSONDecodeError):
        pass
    return {}


# ---------------------------------------------------------------------------
# Declared-state helpers
# ---------------------------------------------------------------------------


def _declared_stage_from_plan(repo_name: str, workspace_root: Path) -> str:
    """
    Read declared CR stage from code_readiness_master_plan_2026_03_11.plan.md.
    Returns e.g. "CR4", "CR0", or "unknown" if not found.
    """
    plan_path = (
        workspace_root / "unified-trading-pm" / "plans" / "active" / "code_readiness_master_plan_2026_03_11.plan.md"
    )
    if not plan_path.exists():
        return "unknown"

    content = plan_path.read_text()
    target = f"- repo: {repo_name}"
    idx = content.find(target)
    if idx == -1:
        return "unknown"

    snippet = content[idx : idx + 300]
    for line in snippet.splitlines()[1:]:
        stripped = line.strip()
        if stripped.startswith("code:"):
            _, _, val = stripped.partition(":")
            gate = val.strip()
            if gate.startswith("C") and len(gate) == 2 and gate[1].isdigit():
                n = int(gate[1])
                return f"CR{n}"
    return "unknown"


def _load_declared_state(repo_name: str, codex_path: Path, workspace_root: Path) -> dict[str, object]:
    """
    Load declared readiness YAML from codex/10-audit/repos/{repo}.yaml.
    Falls back to plan-derived stage if the file doesn't exist.
    """
    repo_yaml = codex_path / "10-audit" / "repos" / f"{repo_name}.yaml"
    if not repo_yaml.exists():
        stage = _declared_stage_from_plan(repo_name, workspace_root)
        return {"declared_stage": stage, "_source": "plan_fallback"}
    data = _load_yaml_simple(repo_yaml)
    return data


# ---------------------------------------------------------------------------
# CR check implementations
# ---------------------------------------------------------------------------


def _check_cr1(repo_path: Path) -> GateResult:
    """
    CR1: Zero NotImplementedError / TODO / FIXME in non-test source code.
    """
    total_hits = 0

    try:
        rg_cmd = [
            "rg",
            "--count-matches",
            "--glob",
            "*.py",
            "--glob",
            "!tests/**",
            "--glob",
            "!.venv/**",
            "--glob",
            "!build/**",
            "--glob",
            "!dist/**",
            "-e",
            "NotImplementedError",
            "-e",
            "TODO",
            "-e",
            "FIXME",
            str(repo_path),
        ]
        result = subprocess.run(rg_cmd, capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            for line in result.stdout.strip().splitlines():
                if ":" in line:
                    _, _, count_str = line.rpartition(":")
                    with contextlib.suppress(ValueError):
                        total_hits += int(count_str.strip())
    except FileNotFoundError:
        # rg not available; fall back to Python glob
        excl_dirs = {"tests", ".venv", "node_modules", "__pycache__", "build", "dist"}
        patterns = ("NotImplementedError", "TODO", "FIXME")
        for py_file in repo_path.rglob("*.py"):
            if any(part in excl_dirs for part in py_file.parts):
                continue
            try:
                text = py_file.read_text(errors="replace")
                for pat in patterns:
                    total_hits += text.count(pat)
            except OSError:
                pass

    if total_hits > 0:
        return GateResult(
            gate="CR1",
            declared="pass",
            verified="MISMATCH",
            detail=f"{total_hits} stub/TODO pattern(s) found",
        )
    return GateResult(gate="CR1", declared="pass", verified="PASS", detail="")


def _check_cr2(repo_path: Path, declared_coverage: str) -> GateResult:
    """
    CR2: Unit test coverage — reads coverage.xml if present.
    """
    coverage_xml = repo_path / "coverage.xml"
    if not coverage_xml.exists():
        return GateResult(
            gate="CR2",
            declared=declared_coverage,
            verified="UNVERIFIED",
            detail="coverage.xml not found — run bash scripts/quality-gates.sh first",
        )

    try:
        tree = ET.parse(str(coverage_xml))  # nosec B314 — coverage.xml from our own QG run, not untrusted  # nosec B314 — coverage.xml from pytest-cov, not untrusted
        root = tree.getroot()
        line_rate_str = root.get("line-rate", "")
        if not line_rate_str:
            return GateResult(
                gate="CR2",
                declared=declared_coverage,
                verified="UNVERIFIED",
                detail="coverage.xml missing line-rate attribute",
            )
        actual_pct = round(float(line_rate_str) * 100, 1)
        actual_str = f"{actual_pct}%"

        declared_num: float | None = None
        clean = declared_coverage.rstrip("%")
        with contextlib.suppress(ValueError):
            declared_num = float(clean)

        if declared_num is not None and actual_pct < declared_num - 1.0:
            return GateResult(
                gate="CR2",
                declared=declared_coverage,
                verified="MISMATCH",
                detail=f"actual {actual_str} < declared {declared_coverage}",
            )
        return GateResult(
            gate="CR2",
            declared=declared_coverage,
            verified="PASS",
            detail=f"actual {actual_str}",
        )
    except ET.ParseError:
        return GateResult(
            gate="CR2",
            declared=declared_coverage,
            verified="UNVERIFIED",
            detail="coverage.xml is malformed",
        )


def _check_cr3(repo_path: Path, manifest_deps: list[str]) -> GateResult:
    """
    CR3: Integration tests exist for every manifest dependency.
    """
    if not manifest_deps:
        return GateResult(
            gate="CR3",
            declared="n/a (zero deps)",
            verified="PASS",
            detail="zero manifest deps — auto-satisfied",
        )

    integration_dir = repo_path / "tests" / "integration"
    if not integration_dir.exists():
        return GateResult(
            gate="CR3",
            declared=f"{len(manifest_deps)} dep(s)",
            verified="MISMATCH",
            detail=f"tests/integration/ missing; deps: {', '.join(manifest_deps)}",
        )

    existing_files = {f.name.lower() for f in integration_dir.rglob("*.py")}
    missing: list[str] = []
    for dep in manifest_deps:
        norm = dep.replace("-", "_").lower()
        candidates = {
            f"test_{norm}_integration.py",
            f"test_{norm}.py",
            f"{norm}_integration.py",
            f"test_{norm}_client.py",
        }
        if not candidates.intersection(existing_files):
            missing.append(dep)

    if missing:
        return GateResult(
            gate="CR3",
            declared=f"{len(manifest_deps)} dep(s)",
            verified="MISMATCH",
            detail=f"missing integration tests for: {', '.join(missing)}",
        )
    return GateResult(
        gate="CR3",
        declared=f"{len(manifest_deps)} dep(s)",
        verified="PASS",
        detail=f"all {len(manifest_deps)} dep(s) covered",
    )


def _check_cr4(repo_path: Path) -> GateResult:
    """
    CR4: Heuristic — check basedpyright baseline error count and ruff suppressions.
    Returns UNVERIFIED (heuristic only; run QG to confirm).
    """
    baseline_file = repo_path / ".basedpyright-baseline.json"
    if baseline_file.exists():
        try:
            raw_baseline: object = cast(object, json.loads(baseline_file.read_text()))
            if isinstance(raw_baseline, dict):
                baseline_dict = cast(dict[str, object], raw_baseline)
                total_errors = sum(len(v) if isinstance(v, list) else 0 for v in baseline_dict.values())
                if total_errors > 0:
                    return GateResult(
                        gate="CR4",
                        declared="pass",
                        verified="UNVERIFIED",
                        detail=f"baseline has {total_errors} suppressed error(s) — run QG to confirm",
                    )
        except (json.JSONDecodeError, OSError):
            pass

    noqa_count = 0
    try:
        rg_cmd = ["rg", "--count-matches", "--glob", "*.py", "# noqa", str(repo_path)]
        result = subprocess.run(rg_cmd, capture_output=True, text=True)
        if result.returncode == 0:
            for line in result.stdout.strip().splitlines():
                if ":" in line:
                    _, _, count_str = line.rpartition(":")
                    with contextlib.suppress(ValueError):
                        noqa_count += int(count_str.strip())
    except FileNotFoundError:
        pass

    if noqa_count > 10:
        return GateResult(
            gate="CR4",
            declared="pass",
            verified="UNVERIFIED",
            detail=f"{noqa_count} # noqa suppression(s) — manual QG verification needed",
        )
    return GateResult(
        gate="CR4",
        declared="pass",
        verified="UNVERIFIED",
        detail="heuristic only — run bash scripts/quality-gates.sh to confirm",
    )


def _check_cr5(repo_name: str) -> GateResult:
    """
    CR5: Check for merged PRs from feat/code-readiness-* branches via gh CLI.
    """
    try:
        result = subprocess.run(
            [
                "gh",
                "pr",
                "list",
                "--repo",
                f"IggyIkenna/{repo_name}",
                "--state",
                "merged",
                "--search",
                "feat/code-readiness",
                "--json",
                "number,title,headRefName",
            ],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode == 0 and result.stdout.strip():
            raw_prs: object = cast(object, json.loads(result.stdout))
            if isinstance(raw_prs, list):
                prs = cast(list[dict[str, object]], raw_prs)
                if prs:
                    pr_nums = [str(pr.get("number", "?")) for pr in prs if isinstance(pr, dict)]
                    return GateResult(
                        gate="CR5",
                        declared="not_assessed",
                        verified="PASS",
                        detail=f"merged readiness PR(s): #{', #'.join(pr_nums)}",
                    )
    except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError):
        pass

    return GateResult(
        gate="CR5",
        declared="not_assessed",
        verified="UNVERIFIED",
        detail="gh CLI unavailable or no merged readiness PRs found",
    )


# ---------------------------------------------------------------------------
# Per-repo verification
# ---------------------------------------------------------------------------


def verify_repo(
    repo_name: str,
    workspace_root: Path,
    codex_path: Path,
    manifest: dict[str, dict[str, object]],
) -> RepoReadinessResult:
    repo_path = workspace_root / repo_name
    result = RepoReadinessResult(repo_name=repo_name, declared_stage="unknown")

    if not repo_path.is_dir():
        result.errors.append(f"Repo directory not found: {repo_path}")
        result.declared_stage = "N/A"
        return result

    declared = _load_declared_state(repo_name, codex_path, workspace_root)
    stage: object = declared.get("declared_stage", "unknown")
    result.declared_stage = str(stage) if stage is not None else "unknown"

    repo_manifest: dict[str, object] = manifest.get(repo_name, {})
    raw_deps: object = repo_manifest.get("dependencies", [])  # noqa: qg-empty-fallback
    dep_list: list[str] = []
    if isinstance(raw_deps, list):
        for d in raw_deps:
            if isinstance(d, str):
                dep_list.append(d)
            elif isinstance(d, dict):
                name_val = d.get("name", "")
                if isinstance(name_val, str) and name_val:
                    dep_list.append(name_val)

    raw_cov: object = declared.get("cr2_coverage_pct", repo_manifest.get("coverage_pct", "unknown"))
    if isinstance(raw_cov, (int, float)):
        declared_cov = f"{raw_cov}%"
    elif isinstance(raw_cov, str):
        declared_cov = raw_cov
    else:
        declared_cov = "unknown"

    result.gates.append(_check_cr1(repo_path))
    result.gates.append(_check_cr2(repo_path, declared_cov))
    result.gates.append(_check_cr3(repo_path, dep_list))
    result.gates.append(_check_cr4(repo_path))
    result.gates.append(_check_cr5(repo_name))

    return result


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------


def _format_verified(gate: GateResult) -> str:
    if gate.detail:
        return f"{gate.verified} ({gate.detail})"
    return gate.verified


def print_report(result: RepoReadinessResult) -> None:
    print(f"\nRepo: {result.repo_name}  (declared stage: {result.declared_stage})")

    if result.errors:
        for err in result.errors:
            print(f"  ERROR: {err}", file=sys.stderr)
        return

    g_w, d_w = 6, 24
    print(f"  {'Gate':<{g_w}} {'Declared':<{d_w}} Verified")
    print(f"  {'-' * g_w} {'-' * d_w} {'-' * 44}")

    counts: dict[str, int] = {"PASS": 0, "MISMATCH": 0, "UNVERIFIED": 0, "FAIL": 0, "SKIP": 0}
    for gate in result.gates:
        verified_str = _format_verified(gate)
        print(f"  {gate.gate:<{g_w}} {gate.declared:<{d_w}} {verified_str}")
        bucket = gate.verified if gate.verified in counts else "UNVERIFIED"
        counts[bucket] += 1

    summary_parts: list[str] = []
    for label in ("MISMATCH", "FAIL", "PASS", "UNVERIFIED", "SKIP"):
        n = counts.get(label, 0)
        if n > 0:
            summary_parts.append(f"{n} {label}")
    print(f"  Overall: {', '.join(summary_parts)}")


# ---------------------------------------------------------------------------
# Repo selection helpers
# ---------------------------------------------------------------------------


def _repos_for_tier(
    tier_arg: str,
    manifest: dict[str, dict[str, object]],
) -> list[str]:
    if tier_arg.lower() == "all":
        return list(manifest.keys())

    wanted_tiers: list[str] = TIER_ALIASES.get(tier_arg, [tier_arg.lower()])

    repos: list[str] = []
    for name, data in manifest.items():
        tier_val: object = data.get("arch_tier", "")
        tier_str = str(tier_val).lower() if tier_val is not None else ""
        if tier_str in wanted_tiers:
            repos.append(name)
    return repos


# ---------------------------------------------------------------------------
# Typed namespace for argparse
# ---------------------------------------------------------------------------


class _ParsedArgs(argparse.Namespace):
    repo: str | None
    tier: str | None
    all: bool
    workspace_root: Path | None
    codex_path: Path | None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Verify declared repo readiness state against automated checks.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--repo", metavar="REPO_NAME", help="Single repo to verify")
    group.add_argument(
        "--tier",
        metavar="TIER",
        help="Tier to verify: T0/T1/T2/T3/T4/T5/T6/infra/all",
    )
    group.add_argument("--all", action="store_true", help="Verify all repos in manifest")
    parser.add_argument(
        "--workspace-root",
        type=Path,
        default=None,
        dest="workspace_root",
        help="Path to workspace root (default: derived from script location)",
    )
    parser.add_argument(
        "--codex-path",
        type=Path,
        default=None,
        dest="codex_path",
        help="Path to codex root (default: unified-trading-pm/codex/ derived from script location)",
    )
    return parser


def main() -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(namespace=_ParsedArgs())

    workspace_root: Path = args.workspace_root if args.workspace_root is not None else _DEFAULT_WORKSPACE_ROOT
    codex_path: Path = args.codex_path if args.codex_path is not None else (_PM_ROOT / "codex")

    if not codex_path.exists():
        print(
            f"WARNING: codex not found at {codex_path}. Declared-state verification will fall back to plan file.",
            file=sys.stderr,
        )

    manifest = _load_manifest(workspace_root)
    if not manifest:
        print(
            "WARNING: workspace-manifest.json not found or empty. CR3 dep-check and tier filtering will be skipped.",
            file=sys.stderr,
        )

    repos_to_check: list[str] = []
    if args.repo is not None:
        repos_to_check = [args.repo]
    elif args.all:
        repos_to_check = list(manifest.keys()) if manifest else []
        if not repos_to_check:
            print("ERROR: --all requires workspace-manifest.json.", file=sys.stderr)
            return 1
    else:
        tier_val: str | None = args.tier
        if tier_val is None:
            print("ERROR: one of --repo, --tier, or --all is required.", file=sys.stderr)
            return 1
        repos_to_check = _repos_for_tier(tier_val, manifest)
        if not repos_to_check:
            print(f"WARNING: No repos found for tier '{tier_val}' in manifest.", file=sys.stderr)
            return 0

    any_mismatch = False
    for repo_name in sorted(repos_to_check):
        result = verify_repo(repo_name, workspace_root, codex_path, manifest)
        print_report(result)
        if any(g.verified in ("MISMATCH", "FAIL") for g in result.gates):
            any_mismatch = True

    if any_mismatch:
        print("\nResult: MISMATCH(ES) FOUND — see above for details.", file=sys.stderr)
        return 1

    print("\nResult: all checks PASS or UNVERIFIED (no mismatches).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
