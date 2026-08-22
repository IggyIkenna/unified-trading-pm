#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Fleet sweep: assert no repo has a test_*.py file PYTEST_UNIT_DIR can't reach.

Origin: `market-tick-data-service/scripts/quality-gates.sh` never set
`PYTEST_UNIT_DIR`, so it silently inherited the `base-service.sh` default of
`tests/unit/` — the entire `tests/market_interface/` family (49 unit modules)
never ran in the gate or in CI (see
`plans/active/issues/mtds_ungated_test_families_2026_07_17.md` todo 5, folded
into `plans/active/ci_satellite_ao_dispatch_batch2_2026_07_29.md` todo 12).
This checker is the fleet-wide guard so the next per-family repo doesn't slip
into the same gap unnoticed.

**v1 → v2 (2026-08-15): the shape-specific scan was itself the bug.** v1 only
looked for `tests/<family>/unit/` directories (one level of family nesting) —
the exact MTDS shape. It PASSED green on this repo (unified-trading-pm) while
`scripts/plan-hygiene/` shipped 24 tests across 4 `test_*.py` files that were
never collected (fixed in `4a4716151f`, one dir at a time) — because
`scripts/plan-hygiene/` is a co-located-test-files dir (same pattern as the
already-gated `scripts/quality_gates/`, `scripts/cicd/`, `scripts/docs/`), not
a `tests/<family>/unit/` shape at all, so v1 never even looked at it. The real
invariant was never "no ungated `tests/<family>/unit/` dir" — it was always
"every directory holding a `test_*.py` file is reachable by PYTEST_UNIT_DIR" —
v1 checked a narrower proxy that happened to catch the MTDS incident and
nothing shaped differently. v2 scans for the actual condition.

For every sibling repo under `--workspace-root` whose `scripts/quality-gates.sh`
sources the shared `base-service.sh`/`base-library.sh` (i.e. actually uses the
`PYTEST_UNIT_DIR` contract), this:

1. Finds every directory anywhere in the repo (excluding venvs/caches/build
   output — see `_EXCLUDED_DIR_NAMES`) that directly contains at least one
   `test_*.py` file — regardless of whether it sits under `tests/`, under
   `scripts/<name>/` co-located with source, or anywhere else pytest's default
   `test_*.py` discovery convention would find it.
2. Resolves that repo's EFFECTIVE `PYTEST_UNIT_DIR` coverage. Note: pytest CLI
   path args (what `PYTEST_UNIT_DIR` becomes) OVERRIDE `[tool.pytest.ini_options]
   testpaths` entirely — `testpaths` is only consulted when pytest is invoked
   with NO path args — so a dir absent from the resolved entries below is
   genuinely never collected, `pyproject.toml` cannot rescue it:
   - a literal `PYTEST_UNIT_DIR="..."` assignment (last one wins, matching bash
     execution order) → its space-separated entries;
   - a **self-discovering** repo (its script computes `PYTEST_UNIT_DIR` via
     `find tests ... -name 'unit'`, e.g. `features-service`) → every unit/ dir
     is covered by construction, skip;
   - no assignment at all → the `base-service.sh`/`base-library.sh` default,
     `tests/unit/` (covers nothing outside that one dir — exactly the original
     MTDS bug shape, reproduced if a repo ever grows a test dir elsewhere
     without opting in).
3. Flags a test-containing dir as UNGATED if no effective entry names it, an
   ancestor of it, or a file inside it.

This is a **shrinking-ratchet baseline** (`pytest_unit_dir_coverage_baseline.yaml`)
— existing fleet debt this todo doesn't fix stays baselined (does not fail the
gate); a NEW ungated test dir anywhere in the fleet fails.

Usage::

    # fleet sweep (PM-only wiring — this is a cross-repo check, not per-repo):
    python check_pytest_unit_dir_coverage.py --workspace-root <ws>

    # ratchet the baseline DOWN after gating a family:
    python check_pytest_unit_dir_coverage.py --workspace-root <ws> --update-baseline

Exit codes: 0 = at-or-below baseline; 1 = new ungated family/families; 2 = arg/IO error.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

import yaml

#: Base-script default (`PYTEST_UNIT_DIR="${PYTEST_UNIT_DIR:-tests/unit/}"` in
#: both `base-service.sh` and `base-library.sh`) — what a repo effectively gets
#: when it never sets the override.
BASE_DEFAULT_ENTRY: Final[str] = "tests/unit/"

_BASE_SOURCE_RE: Final[re.Pattern[str]] = re.compile(r"quality-gates-base/base-(service|library)\.sh")
_LITERAL_ASSIGN_RE: Final[re.Pattern[str]] = re.compile(
    r'^\s*PYTEST_UNIT_DIR\s*=\s*"([^"$]*)"\s*(?:#.*)?$', re.MULTILINE
)
_SELF_DISCOVERY_RE: Final[re.Pattern[str]] = re.compile(r"find\s+tests\b[^\n]*-name\s+['\"]unit['\"]")

#: Dirs pruned while walking for test_*.py files — venvs/caches/build output/vendored
#: packages, PLUS deliberately-separate, non-"unit" test TIERS this checker is not scoped
#: to. Measured 2026-08-15: an unscoped `test_*.py` walk over the real workspace flags
#: ~60 dirs across the fleet that are NOT the MTDS/plan-hygiene bug class at all — they're
#: a different tier with its OWN dedicated collection mechanism by design (e.g.
#: system-integration-tests' documented Layer 3a/3b `@pytest.mark.smoke` /
#: `@pytest.mark.full_e2e` tiers; execution-service's `tests/e2e/test_defi_execution_e2e.py`
#: is deliberately wired as a single named file, not the whole dir). Flagging those as
#: "ungated" would be wrong: the fix-advice ("add it to PYTEST_UNIT_DIR") is actively bad
#: for a suite that needs live infra / a slow nightly cadence the fast per-commit gate
#: can't accommodate. PM's own `codex/` docs root is excluded for a different reason:
#: `codex/06-coding-standards/test-templates/test_event_logging.py` is a CANONICAL TEMPLATE
#: ("copy to tests/unit/ in each service repo" — its own leading comment) meant to be
#: copied elsewhere, never collected in place.
#: Unlike check_adapter_contract_regression.py's EXCLUDE_DIR_NAMES, this does NOT exclude
#: "scripts" or "tests" themselves — those are exactly where this checker must look
#: (scripts/plan-hygiene/ is the real gap this checker exists to catch post-2026-08-15).
_EXCLUDED_DIR_NAMES: Final[frozenset[str]] = frozenset(
    {
        # venv / cache / build output
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
        # non-unit test tiers — own dedicated collection mechanism, out of
        # PYTEST_UNIT_DIR's scope by design (not this checker's bug class)
        "integration",
        "e2e",
        "full_e2e",
        "layer3a_smoke",
        "layer3b_full_e2e",
        "smoke",
        "perf",
        "performance",
        "benchmark",
        "benchmarks",
        "regression",
        "scenarios",
        "overnight",
        "real_flow",
        "scorecard",
        "abbreviated",
        "architecture",
        "backtest",
        "backtests",
        "load",
        "stress",
        # docs / reference corpus — never executable in place
        "codex",
        # Nested per-agent git worktrees (.claude/worktrees/<id>/) can carry an
        # older/different snapshot of the same repo's source — scanning one
        # produces false violations for code that doesn't exist in the actual
        # checked-out tree (found live 2026-08-06, same class as the
        # check_manifest_import_alignment.py / test_event_logging.py fixes).
        ".claude",
    }
)


# ── Repo scan ────────────────────────────────────────────────────────────────


def find_test_containing_dirs(repo_root: Path) -> list[str]:
    """Every directory anywhere in the repo that directly contains a `test_*.py` file.

    This is pytest's own default discovery convention, applied structurally — not a
    `tests/<family>/unit/`-shaped guess. Hidden dirs (`.claude/worktrees/...`, `.git`, …)
    and `_EXCLUDED_DIR_NAMES` are pruned before descending, so vendored `.venv` test suites
    and agent worktree checkouts never inflate the count.
    """
    out: list[str] = []
    for dirpath, dirnames, filenames in os.walk(repo_root):
        dirnames[:] = [d for d in dirnames if not d.startswith(".") and d not in _EXCLUDED_DIR_NAMES]
        if any(fn.startswith("test_") and fn.endswith(".py") for fn in filenames):
            out.append(Path(dirpath).relative_to(repo_root).as_posix())
    return sorted(out)


def resolve_effective_entries(qg_text: str) -> tuple[str, ...] | None:
    """Return the repo's effective PYTEST_UNIT_DIR entries, or None if self-discovering."""
    if _SELF_DISCOVERY_RE.search(qg_text):
        return None
    literal_matches = _LITERAL_ASSIGN_RE.findall(qg_text)
    if literal_matches:
        # bash: a later assignment in file order wins over an earlier one.
        return tuple(literal_matches[-1].split())
    return (BASE_DEFAULT_ENTRY,)


def _covers(entry: str, test_dir: str) -> bool:
    """True if `entry` (a PYTEST_UNIT_DIR token) gates anything inside `test_dir`."""
    entry_n = entry.rstrip("/")
    dir_n = test_dir.rstrip("/")
    if entry_n == dir_n:
        return True
    if dir_n.startswith(entry_n + "/"):
        return True  # entry is an ancestor of the test dir (e.g. "tests/" or "scripts/")
    # entry names a specific file/subdir inside the test dir
    return entry_n.startswith(dir_n + "/")


def ungated_test_dirs(test_dirs: list[str], entries: tuple[str, ...] | None) -> list[str]:
    """Test-containing dirs with zero overlap against `entries` (None = self-discovering, always covered)."""
    if entries is None:
        return []
    return sorted(d for d in test_dirs if not any(_covers(e, d) for e in entries))


def is_pytest_unit_dir_repo(qg_text: str) -> bool:
    """True if this repo's gate actually uses the PYTEST_UNIT_DIR contract."""
    return bool(_BASE_SOURCE_RE.search(qg_text))


# ── Baseline (shrinking ratchet, per repo) ──────────────────────────────────


def _baseline_path() -> Path:
    return Path(__file__).resolve().parent / "pytest_unit_dir_coverage_baseline.yaml"


@dataclass(frozen=True)
class Baseline:
    counts: dict[str, int] = field(default_factory=dict)
    note: str = ""

    def allowed(self, repo: str) -> int:
        return int(self.counts.get(repo, 0))


def load_baseline(path: Path | None = None) -> Baseline:
    baseline_file = path if path is not None else _baseline_path()
    if not baseline_file.exists():
        return Baseline()
    raw = yaml.safe_load(baseline_file.read_text(encoding="utf-8")) or {}
    repos_raw = raw.get("repos") or {}
    counts = {str(repo): int(count) for repo, count in repos_raw.items()}
    return Baseline(counts=counts, note=str(raw.get("note") or ""))


def write_baseline(observed: dict[str, int], existing: Baseline, path: Path | None = None) -> None:
    """Persist a new baseline, clamping counts DOWN — never raised.

    Mirrors `check_ruff_rule_ratchet.py`'s `write_baseline`: only repos actually
    OBSERVED this run are updated; every other repo's row is carried forward
    verbatim (a scoped/partial run must never zero out unobserved repos).
    """
    baseline_file = path if path is not None else _baseline_path()
    merged: dict[str, int] = {}
    for repo in sorted(set(observed) | set(existing.counts)):
        if repo not in observed:
            merged[repo] = existing.allowed(repo)
            continue
        seen = observed[repo]
        prior = existing.allowed(repo)
        merged[repo] = min(seen, prior) if repo in existing.counts else seen
    header = (
        "# Baseline for the PYTEST_UNIT_DIR coverage fleet sweep — SHRINKING ratchet.\n"
        "#\n"
        "# repos[<repo>] is the number of directories anywhere in that repo holding a\n"
        "# test_*.py file this checker tolerates as UNGATED (not reachable via that\n"
        "# repo's PYTEST_UNIT_DIR) — NOT limited to tests/<family>/unit/ shapes; a\n"
        "# co-located scripts/<name>/test_*.py dir counts too (v2, 2026-08-15 — v1's\n"
        "# tests/<family>/unit/-only scan missed unified-trading-pm's own\n"
        "# scripts/plan-hygiene/ shipping 24 uncollected tests, see check_pytest_unit_\n"
        "# dir_coverage.py's module docstring). A repo whose live ungated-dir count\n"
        "# EXCEEDS its baseline fails the gate — a NEW test dir landed without being\n"
        "# wired into PYTEST_UNIT_DIR (the exact MTDS bug this checker exists to catch).\n"
        "# Fix by adding the test dir (or its parent) to that repo's\n"
        "# `PYTEST_UNIT_DIR=` in scripts/quality-gates.sh, proving the widened gate\n"
        "# is still GREEN (rule 11a), then re-run `--update-baseline`.\n"
        "#\n"
        "# LOWER counts as dirs get gated. NEVER raise a count. Repos not\n"
        "# listed (or not using the PYTEST_UNIT_DIR contract) default to 0.\n"
        "#\n"
        "# SSOT: plans/active/issues/mtds_ungated_test_families_2026_07_17.md\n"
        "# (todo 5) + plans/active/ci_satellite_ao_dispatch_batch2_2026_07_29.md\n"
        "# (todo 12).\n"
    )
    body = yaml.safe_dump(
        {
            "note": existing.note
            or (
                "Seeded 2026-07-31 — ci_satellite_ao_dispatch_batch2 todo 12. Known pre-existing gap: "
                "execution-service tests/sports_execution/unit/ is not named in PYTEST_UNIT_DIR "
                "(scripts/quality-gates.sh only lists trade_execution/unit + defi_execution's one lateral-loader "
                "file) — ratchet down by widening PYTEST_UNIT_DIR there, proving quality-gates.sh stays green."
            ),
            "repos": merged,
        },
        sort_keys=True,
        default_flow_style=False,
        allow_unicode=True,
    )
    _ = baseline_file.write_text(header + body, encoding="utf-8")


# ── Scope resolution (mirrors check_ruff_rule_ratchet.py) ──────────────────


def _resolve_scopes(workspace_root: Path, scope: str | None) -> list[tuple[str, Path]]:
    if scope:
        repo_root = workspace_root / scope
        if not repo_root.is_dir():
            print(
                f"[check_pytest_unit_dir_coverage] --scope {scope!r} not a dir under {workspace_root}", file=sys.stderr
            )
            return []
        return [(scope, repo_root)]
    out: list[tuple[str, Path]] = []
    for child in sorted(workspace_root.iterdir()):
        if not child.is_dir() or child.name.startswith("."):
            continue
        # Backup/scratch copies left alongside the real sibling repos carry a `.git` dir too
        # (a rename-aside during a history rewrite, or an agent-work clone) and would
        # otherwise read as a real repo — same incident class as
        # check_repo_docs_ssot.py's `_SCRATCH_CLONE_RE` (2026-07-30 agentwork clones,
        # 2026-08-05 `.stale-pre-history-rewrite-<ts>` backups); no shared helper exists
        # between the checkers yet, so this mirrors that exclusion locally.
        if "-agentwork-" in child.name or "scratch-clone" in child.name or ".stale-" in child.name:
            continue
        if (child / ".git").exists():
            out.append((child.name, child))
    return out


# ── main ─────────────────────────────────────────────────────────────────────


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="PYTEST_UNIT_DIR fleet coverage sweep (shrinking-ratchet baseline).")
    parser.add_argument("--workspace-root", required=True, type=Path)
    parser.add_argument("--scope", default=None, help="Single repo dir name (defaults to the whole fleet).")
    parser.add_argument(
        "--update-baseline",
        action="store_true",
        help="Rewrite the baseline with the observed counts (clamped DOWN — never raised).",
    )
    parser.add_argument(
        "--baseline-file",
        type=Path,
        default=None,
        help="Override the baseline yaml path (unit tests only).",
    )
    args = parser.parse_args(argv)

    workspace_root: Path = args.workspace_root.resolve()
    baseline_file: Path | None = args.baseline_file
    baseline = load_baseline(baseline_file)
    scopes = _resolve_scopes(workspace_root, args.scope)
    if not scopes:
        print("[check_pytest_unit_dir_coverage] no repos in scope.", file=sys.stderr)
        return 0

    observed: dict[str, int] = {}
    failures: list[str] = []
    info_lines: list[str] = []
    for repo_name, repo_root in scopes:
        qg_script = repo_root / "scripts" / "quality-gates.sh"
        if not qg_script.is_file():
            continue
        try:
            qg_text = qg_script.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as err:
            print(f"[check_pytest_unit_dir_coverage] ERROR reading {qg_script}: {err}", file=sys.stderr)
            return 2
        if not is_pytest_unit_dir_repo(qg_text):
            continue  # not a PYTEST_UNIT_DIR repo (e.g. a TS/UI repo)

        test_dirs = find_test_containing_dirs(repo_root)
        entries = resolve_effective_entries(qg_text)
        ungated = ungated_test_dirs(test_dirs, entries)
        observed[repo_name] = len(ungated)
        allowed = baseline.allowed(repo_name)
        if len(ungated) > allowed:
            over = ungated[allowed:] if allowed < len(ungated) else ungated
            failures.append(
                f"[FAIL] {repo_name}: {len(ungated)} ungated test dir(s) > baseline {allowed}. New: {', '.join(over)}"
            )
        elif len(ungated) < allowed:
            info_lines.append(
                f"[WARN] {repo_name}: {len(ungated)} < baseline {allowed} — ratchet DOWN (re-run --update-baseline)."
            )
        else:
            info_lines.append(f"[OK]   {repo_name}: {len(ungated)} (== baseline)")

    if args.update_baseline:
        write_baseline(observed, baseline, baseline_file)
        print(f"[check_pytest_unit_dir_coverage] baseline updated at {baseline_file or _baseline_path()}")
        for repo in sorted(observed):
            print(f"  {repo}: {observed[repo]}")
        return 0

    for line in info_lines:
        print(line)
    for line in failures:
        print(line, file=sys.stderr)
    if failures:
        print(
            "\n→ A dir holding test_*.py file(s) isn't reachable via that repo's PYTEST_UNIT_DIR (pytest CLI path "
            "args override [tool.pytest.ini_options] testpaths entirely — pyproject.toml cannot rescue it) — add it "
            "(or its parent) to scripts/quality-gates.sh's PYTEST_UNIT_DIR=, proving the widened gate is still "
            "GREEN (rule 11a). Baseline: "
            "unified-trading-pm/scripts/quality_gates/pytest_unit_dir_coverage_baseline.yaml "
            "(NEVER raise a count). SSOT: plans/active/issues/mtds_ungated_test_families_2026_07_17.md.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
