#!/usr/bin/env python3
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
"""QG STEP 5.71 — service emission-policy paired-callsite enforcement.

Enforces CLAUDE.md "Service-output emission policy (writegate slice b/c)":
every ``record_captured()`` callsite inside a service whose output data_types
appear in UAC ``SERVICE_OUTPUT_POLICIES`` MUST also have a paired
``publish_with_policy()`` / ``publish_with_manifest_lookup()`` call within the
same function body.

Background
----------
Phase 6.3-6.8 wired the per-service emission-policy helpers at every existing
``record_captured()`` boundary. Phase 6.9 introduces this static check so that
future developers who add a NEW derived-output adapter are caught at CI time if
they write a ``record_captured()`` without wiring the companion emission-policy
call.

Algorithm
---------
1. Load ``emission_policy_paired_callsites_baseline.yaml`` (initially 0
   violations — ratchet shape mirrors STEP 5.70).
2. For each service repo in scope whose name appears as a key in UAC
   ``SERVICE_OUTPUT_POLICIES`` (left-join on first tuple element), AST-walk
   every ``.py`` source file.
3. For each ``ast.FunctionDef`` / ``ast.AsyncFunctionDef`` node, collect:
   a. all ``record_captured(...)`` call names,
   b. all ``publish_with_policy(...)`` / ``publish_with_manifest_lookup(...)``
      call names.
4. If a function has at least one ``record_captured`` call BUT zero
   ``publish_with_policy`` / ``publish_with_manifest_lookup`` calls → flag as
   a violation (file:line + function name).
5. Apply baseline tolerance.  New violations above baseline → exit 1.

Escape hatch
------------
Add a trailing ``# QG-allow: emission-policy-not-applicable`` comment on the
same line as the ``record_captured(...)`` call to mark callsites that are
genuinely input-data captures (not derived-output boundaries).  The check
skips any function where ALL ``record_captured`` calls carry this marker.

Baseline ratchet
----------------
``emission_policy_paired_callsites_baseline.yaml`` records (repo, file, function)
triples that are known pre-existing violations during rollout.  Once Phase 6.3-6.8
is complete the baseline should be empty.  NEVER raise a baseline count — fix the
callsite instead.

SSOT
----
* Plan: ``plans/active/writegate_honest_coverage_endtoend_2026_05_06.md``
  Phase 6.9 QG item.
* CLAUDE.md "Service-output emission policy (writegate slice b/c)".
* UAC ``SERVICE_OUTPUT_POLICIES`` at
  ``unified_api_contracts/canonical/crosscutting/service_emission_policy.py``.

Usage::

    # per-repo (from base-service.sh STEP 5.71):
    python check_emission_policy_paired_callsites.py \\
        --workspace-root <ws> --scope <repo-dir>

    # workspace-wide sweep:
    python check_emission_policy_paired_callsites.py --workspace-root <ws>

    # dry-run to see all violations regardless of baseline:
    python check_emission_policy_paired_callsites.py --workspace-root <ws> --scope <repo> --dry-run
"""

from __future__ import annotations

import argparse
import ast
import sys
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

import yaml

# ── Constants ────────────────────────────────────────────────────────────────

#: Names of calls that record a manifest shard as "captured".
RECORD_CAPTURED_NAMES: Final[frozenset[str]] = frozenset(
    {
        "record_captured",
        "record_captured_from_counts",
    }
)

#: Names of calls that invoke the emission-policy helper.
PUBLISH_POLICY_NAMES: Final[frozenset[str]] = frozenset(
    {
        "publish_with_policy",
        "publish_with_manifest_lookup",
    }
)

#: Inline exemption marker.  A ``record_captured(...)`` call with this on the
#: same source line is treated as an input-data capture (not a derived-output
#: boundary) and skipped by the check.
NOQA_MARKER: Final[str] = "QG-allow: emission-policy-not-applicable"

#: Directory names to skip when walking.
EXCLUDE_DIR_NAMES: Final[frozenset[str]] = frozenset(
    {
        ".venv",
        ".venv-workspace",
        "venv",
        "node_modules",
        "build",
        "dist",
        "__pycache__",
        ".git",
        ".mypy_cache",
        ".ruff_cache",
        ".pytest_cache",
        "htmlcov",
        ".tox",
        "site-packages",
    }
)

#: Path fragments indicating archived / generated trees.
EXCLUDE_PATH_FRAGMENTS: Final[tuple[str, ...]] = (
    "/archive/",
    "/.archive/",
    "/_archived/",
    ".egg-info",
)

#: Sub-directories to exclude from the scan (scripts + tests are not
#: production service code; migration scripts may have raw record calls).
EXCLUDE_SUBDIR_NAMES: Final[frozenset[str]] = frozenset({"scripts", "tests"})


# ── Data shapes ──────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Violation:
    """A single function-level callsite violation."""

    repo: str
    file_path: Path
    line: int  # line of the function def
    func_name: str
    record_captured_lines: tuple[int, ...]

    def baseline_key(self) -> str:
        """Stable string key used for baseline matching."""
        return f"{self.repo}::{self.file_path.as_posix()}::{self.func_name}"


@dataclass
class Baseline:
    """Per-(repo, file, function) allowed violations."""

    entries: set[str] = field(default_factory=set)
    note: str = ""

    def allows(self, violation: Violation) -> bool:
        return violation.baseline_key() in self.entries


# ── Baseline I/O ─────────────────────────────────────────────────────────────


def _baseline_path() -> Path:
    return (
        Path(__file__).resolve().parent.parent.parent / "baselines" / "emission_policy_paired_callsites_baseline.yaml"
    )


def load_baseline() -> Baseline:
    path = _baseline_path()
    if not path.exists():
        return Baseline()
    raw: object = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        return Baseline()
    entries_raw = raw.get("violations") or []
    entries: set[str] = set()
    if isinstance(entries_raw, list):
        for entry in entries_raw:
            if isinstance(entry, str):
                entries.add(entry)
            elif isinstance(entry, dict) and "key" in entry:
                entries.add(str(entry["key"]))
    return Baseline(entries=entries, note=str(raw.get("note") or ""))


# ── File walker ───────────────────────────────────────────────────────────────


def _is_excluded_path(path: Path, root: Path) -> bool:
    try:
        rel = path.relative_to(root)
    except ValueError:
        return True
    parts = rel.parts
    for part in parts:
        if part in EXCLUDE_DIR_NAMES or part.startswith(".venv"):
            return True
        if part in EXCLUDE_SUBDIR_NAMES:
            return True
    rel_str = str(rel).replace("\\", "/")
    for fragment in EXCLUDE_PATH_FRAGMENTS:
        if fragment in f"/{rel_str}/":
            return True
    name = path.name
    # Skip test files.
    return bool(name.startswith("test_") or name.endswith("_test.py"))


def iter_python_files(root: Path) -> Iterator[Path]:
    for path in root.rglob("*.py"):
        if path.is_file() and not _is_excluded_path(path, root):
            yield path


# ── AST analysis ──────────────────────────────────────────────────────────────


def _extract_call_name(node: ast.expr) -> str | None:
    """Return the function/method name from a Call's func expression."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _collect_calls_in_func(
    func_node: ast.FunctionDef | ast.AsyncFunctionDef,
    source_lines: list[str],
) -> tuple[list[int], list[int]]:
    """Return (record_captured_lines, publish_policy_lines) within this function.

    ``record_captured_lines`` excludes lines that carry the NOQA_MARKER.
    """
    record_lines: list[int] = []
    publish_lines: list[int] = []

    for node in ast.walk(func_node):
        if not isinstance(node, ast.Call):
            continue
        name = _extract_call_name(node.func)
        if name is None:
            continue
        lineno = node.lineno
        if name in RECORD_CAPTURED_NAMES:
            # Check for inline exemption marker on the same source line.
            line_text = source_lines[lineno - 1] if 1 <= lineno <= len(source_lines) else ""
            if NOQA_MARKER in line_text:
                continue
            record_lines.append(lineno)
        elif name in PUBLISH_POLICY_NAMES:
            publish_lines.append(lineno)

    return record_lines, publish_lines


def scan_file_for_violations(
    file_path: Path,
    repo: str,
    source_text: str,
) -> list[Violation]:
    """Return violations for ONE file (pure function — no side-effects)."""
    try:
        tree = ast.parse(source_text, filename=str(file_path))
    except (SyntaxError, ValueError):
        return []

    source_lines = source_text.splitlines()
    violations: list[Violation] = []

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        record_lines, publish_lines = _collect_calls_in_func(node, source_lines)
        if record_lines and not publish_lines:
            violations.append(
                Violation(
                    repo=repo,
                    file_path=file_path,
                    line=node.lineno,
                    func_name=node.name,
                    record_captured_lines=tuple(record_lines),
                )
            )
    return violations


def scan_repo(repo_root: Path, repo_name: str) -> list[Violation]:
    """Scan a single repo directory and return all violations."""
    violations: list[Violation] = []
    for py in iter_python_files(repo_root):
        try:
            source = py.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        violations.extend(scan_file_for_violations(py, repo_name, source))
    return violations


# ── SERVICE_OUTPUT_POLICIES loader ───────────────────────────────────────────


def load_policy_service_names(workspace_root: Path) -> frozenset[str]:
    """Return the set of service names present in UAC SERVICE_OUTPUT_POLICIES.

    Falls back to a hard-coded set if the UAC module can't be parsed
    (avoids import-time dependency on the UAC package being installed).
    The fallback list matches the 2026-05-13 seed.
    """
    # Try to grep the UAC source file directly (no import needed).
    uac_candidates = [
        workspace_root
        / "unified-api-contracts"
        / "unified_api_contracts"
        / "canonical"
        / "crosscutting"
        / "service_emission_policy.py",
        # Handle per-tab worktree layout where UAC is at sibling path.
        workspace_root.parent
        / "unified-api-contracts"
        / "unified_api_contracts"
        / "canonical"
        / "crosscutting"
        / "service_emission_policy.py",
    ]
    for candidate in uac_candidates:
        if candidate.is_file():
            try:
                services = _parse_service_names_from_uac(candidate)
                if services:
                    return frozenset(services)
            except (OSError, UnicodeDecodeError, SyntaxError):
                pass

    # Hard-coded fallback (stable subset from the 2026-05-12 seed).
    return frozenset(
        {
            "market-data-processing-service",
            "features-volatility-service",
            "features-cross-instrument-service",
            "ml-training-service",
            "ml-inference-service",
            "strategy-service",
            "execution-service",
            "position-balance-monitor-service",
            "risk-and-exposure-service",
            "instruments-service",
            "features-onchain-service",
            "features-sports-service",
            "features-delta-one-service",
            "features-multi-timeframe-service",
            "features-calendar-service",
            "features-commodity-service",
        }
    )


def _parse_service_names_from_uac(uac_path: Path) -> list[str]:
    """AST-parse the UAC file and extract service names from SERVICE_OUTPUT_POLICIES."""
    source = uac_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(uac_path))
    services: list[str] = []
    for node in ast.walk(tree):
        # Look for dict literal assignments to SERVICE_OUTPUT_POLICIES.
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if (
                isinstance(target, ast.Name)
                and target.id == "SERVICE_OUTPUT_POLICIES"
                and isinstance(node.value, ast.Dict)
            ):
                for key_node in node.value.keys:
                    # Keys are tuples: (service_name, data_type)
                    if isinstance(key_node, ast.Tuple) and len(key_node.elts) == 2:
                        svc_node = key_node.elts[0]
                        if isinstance(svc_node, ast.Constant) and isinstance(svc_node.value, str):
                            services.append(svc_node.value)
    return list(set(services))


# ── Scope resolution ──────────────────────────────────────────────────────────


def _repo_name_to_dir(workspace_root: Path, repo_name: str) -> Path | None:
    """Return the directory for a given repo (service) name under workspace_root."""
    candidate = workspace_root / repo_name
    if candidate.is_dir():
        return candidate
    return None


def resolve_scopes(
    workspace_root: Path,
    scope: str | None,
    policy_services: frozenset[str],
) -> list[tuple[str, Path]]:
    """Return [(repo_name, scan_root)] pairs in scope.

    If ``--scope`` is provided, only that repo is scanned (if it's in
    SERVICE_OUTPUT_POLICIES).  Otherwise every known policy-service repo
    that exists under workspace_root is scanned.
    """
    if scope:
        repo_dir = workspace_root / scope
        if not repo_dir.is_dir():
            print(f"[STEP 5.71] --scope {scope!r} not found under {workspace_root}", file=sys.stderr)
            return []
        # Accept the scope even if not in policy_services (extra safety).
        return [(scope, repo_dir)]

    out: list[tuple[str, Path]] = []
    for svc in sorted(policy_services):
        d = _repo_name_to_dir(workspace_root, svc)
        if d is not None:
            out.append((svc, d))
    return out


# ── Reporting ─────────────────────────────────────────────────────────────────


def format_violation(v: Violation, workspace_root: Path) -> str:
    try:
        rel = v.file_path.relative_to(workspace_root)
    except ValueError:
        rel = v.file_path
    lines_str = ", ".join(str(ln) for ln in v.record_captured_lines)
    return (
        f"  [FAIL] {rel}:{v.line}  function={v.func_name!r}\n"
        f"      record_captured() at line(s): {lines_str}\n"
        f"      Missing paired: publish_with_policy() / publish_with_manifest_lookup()\n"
        f"      Fix: add publish_with_policy(service=..., output_data_type=..., ...) in {v.func_name!r},\n"
        f"           OR add '# {NOQA_MARKER}' on each record_captured() line if\n"
        f"           this is an input-data capture (not a derived-output boundary).\n"
    )


# ── main ──────────────────────────────────────────────────────────────────────


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "QG STEP 5.71 — assert every record_captured() callsite in a service "
            "whose outputs are in UAC SERVICE_OUTPUT_POLICIES also has a paired "
            "publish_with_policy() / publish_with_manifest_lookup() in the same function."
        )
    )
    parser.add_argument(
        "--workspace-root",
        required=True,
        type=Path,
        help="Workspace root directory (parent of all repo dirs).",
    )
    parser.add_argument(
        "--scope",
        default=None,
        help="Single repo dir name to scan (per-repo QG mode from base-service.sh).",
    )
    parser.add_argument(
        "--baseline",
        type=Path,
        default=None,
        help="Path to baseline YAML (default: <pm>/baselines/emission_policy_paired_callsites_baseline.yaml).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report all violations ignoring the baseline (exit 1 on any violation).",
    )
    args = parser.parse_args(argv)

    workspace_root: Path = args.workspace_root.resolve()
    dry_run: bool = bool(args.dry_run)

    # Load baseline.
    baseline = load_baseline()

    # Load policy service names (closed-set check).
    policy_services = load_policy_service_names(workspace_root)
    if not policy_services:
        print(
            "[STEP 5.71] WARNING: could not load SERVICE_OUTPUT_POLICIES service list; proceeding with empty set.",
            file=sys.stderr,
        )

    # Resolve scopes.
    scopes = resolve_scopes(workspace_root, args.scope, policy_services)
    if not scopes:
        print("[STEP 5.71] no repos in scope — skipping.", file=sys.stderr)
        return 0

    # Scan.
    all_violations: list[Violation] = []
    for repo_name, repo_dir in scopes:
        violations = scan_repo(repo_dir, repo_name)
        all_violations.extend(violations)

    # Separate baselined vs new violations.
    new_violations = [v for v in all_violations if dry_run or not baseline.allows(v)]
    baselined = [v for v in all_violations if not dry_run and baseline.allows(v)]

    # Report baselined (informational).
    if baselined:
        print(
            f"[STEP 5.71] {len(baselined)} baselined violation(s) "
            f"(grandfathered pending Phase 6.3-6.8 rollout — NOT blocking):",
            file=sys.stderr,
        )
        for v in baselined:
            try:
                rel = v.file_path.relative_to(workspace_root)
            except ValueError:
                rel = v.file_path
            print(f"  [WARN] {rel}:{v.line}  function={v.func_name!r}", file=sys.stderr)

    # Report new violations (blocking).
    if new_violations:
        print("", file=sys.stderr)
        print(
            f"[STEP 5.71] FAIL — {len(new_violations)} new record_captured() callsite(s) "
            "without paired publish_with_policy() / publish_with_manifest_lookup():",
            file=sys.stderr,
        )
        for v in new_violations:
            print(format_violation(v, workspace_root), file=sys.stderr)
        print(
            "[STEP 5.71] Each record_captured() in a service whose output data_types appear\n"
            "  in UAC SERVICE_OUTPUT_POLICIES MUST be paired with publish_with_policy() or\n"
            "  publish_with_manifest_lookup() in the SAME function body.\n"
            "  Exceptions: add '# QG-allow: emission-policy-not-applicable' on the\n"
            "  record_captured() line to mark intentional input-data captures.\n"
            "  SSOT: writegate_honest_coverage_endtoend_2026_05_06.md Phase 6.9 +\n"
            "  CLAUDE.md 'Service-output emission policy (writegate slice b/c)'.",
            file=sys.stderr,
        )
        return 1

    if not all_violations:
        print(
            "[STEP 5.71] OK — all record_captured() callsites in scope have paired emission-policy calls.",
            file=sys.stderr,
        )
    else:
        print(
            f"[STEP 5.71] OK — {len(baselined)} baselined violation(s) (non-blocking); 0 new.",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
