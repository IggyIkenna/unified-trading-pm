#!/usr/bin/env python3
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
"""Fleet sweep: assert no repo has an ungated `tests/<family>/unit/` dir.

Origin: `market-tick-data-service/scripts/quality-gates.sh` never set
`PYTEST_UNIT_DIR`, so it silently inherited the `base-service.sh` default of
`tests/unit/` — the entire `tests/market_interface/` family (49 unit modules)
never ran in the gate or in CI (see
`plans/active/issues/mtds_ungated_test_families_2026_07_17.md` todo 5, folded
into `plans/active/ci_satellite_ao_dispatch_batch2_2026_07_29.md` todo 12).
This checker is the fleet-wide guard so the next per-family repo doesn't slip
into the same gap unnoticed.

For every sibling repo under `--workspace-root` whose `scripts/quality-gates.sh`
sources the shared `base-service.sh`/`base-library.sh` (i.e. actually uses the
`PYTEST_UNIT_DIR` contract), this:

1. Finds every `tests/<family>/unit/` directory (one level of family nesting —
   the exact shape the source finding names; NOT the top-level `tests/unit/`
   default, which is always gated).
2. Resolves that repo's EFFECTIVE `PYTEST_UNIT_DIR` coverage:
   - a literal `PYTEST_UNIT_DIR="..."` assignment (last one wins, matching bash
     execution order) → its space-separated entries;
   - a **self-discovering** repo (its script computes `PYTEST_UNIT_DIR` via
     `find tests ... -name 'unit'`, e.g. `features-service`) → every unit/ dir
     is covered by construction, skip;
   - no assignment at all → the `base-service.sh`/`base-library.sh` default,
     `tests/unit/` (covers nothing per-family — exactly the original MTDS bug
     shape, reproduced if a repo ever grows a family dir without opting in).
3. Flags a family dir as UNGATED if no effective entry names it, an ancestor of
   it, or a file inside it.

This is a **shrinking-ratchet baseline** (`pytest_unit_dir_coverage_baseline.yaml`)
— existing fleet debt this todo doesn't fix stays baselined (does not fail the
gate); a NEW ungated family anywhere in the fleet fails.

Usage::

    # fleet sweep (PM-only wiring — this is a cross-repo check, not per-repo):
    python check_pytest_unit_dir_coverage.py --workspace-root <ws>

    # ratchet the baseline DOWN after gating a family:
    python check_pytest_unit_dir_coverage.py --workspace-root <ws> --update-baseline

Exit codes: 0 = at-or-below baseline; 1 = new ungated family/families; 2 = arg/IO error.
"""

from __future__ import annotations

import argparse
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


# ── Repo scan ────────────────────────────────────────────────────────────────


def find_family_unit_dirs(repo_root: Path) -> list[str]:
    """Every `tests/<family>/unit/` dir (one level of family nesting), repo-relative POSIX."""
    tests_dir = repo_root / "tests"
    if not tests_dir.is_dir():
        return []
    out: list[str] = []
    for child in sorted(tests_dir.iterdir()):
        if not child.is_dir():
            continue
        unit_dir = child / "unit"
        if unit_dir.is_dir():
            out.append(unit_dir.relative_to(repo_root).as_posix())
    return out


def resolve_effective_entries(qg_text: str) -> tuple[str, ...] | None:
    """Return the repo's effective PYTEST_UNIT_DIR entries, or None if self-discovering."""
    if _SELF_DISCOVERY_RE.search(qg_text):
        return None
    literal_matches = _LITERAL_ASSIGN_RE.findall(qg_text)
    if literal_matches:
        # bash: a later assignment in file order wins over an earlier one.
        return tuple(literal_matches[-1].split())
    return (BASE_DEFAULT_ENTRY,)


def _covers(entry: str, family_dir: str) -> bool:
    """True if `entry` (a PYTEST_UNIT_DIR token) gates anything inside `family_dir`."""
    entry_n = entry.rstrip("/")
    dir_n = family_dir.rstrip("/")
    if entry_n == dir_n:
        return True
    if dir_n.startswith(entry_n + "/"):
        return True  # entry is an ancestor of the family dir (e.g. "tests/" or "tests/<family>/")
    # entry names a specific file/subdir inside the family dir
    return entry_n.startswith(dir_n + "/")


def ungated_families(family_dirs: list[str], entries: tuple[str, ...] | None) -> list[str]:
    """Family dirs with zero overlap against `entries` (None = self-discovering, always covered)."""
    if entries is None:
        return []
    return sorted(d for d in family_dirs if not any(_covers(e, d) for e in entries))


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
        "# repos[<repo>] is the number of `tests/<family>/unit/` dirs this checker\n"
        "# tolerates as UNGATED (not reachable via that repo's PYTEST_UNIT_DIR) in\n"
        "# that repo. A repo whose live ungated-family count EXCEEDS its baseline\n"
        "# fails the gate — a NEW per-family test dir landed without being wired\n"
        "# into PYTEST_UNIT_DIR (the exact MTDS bug this checker exists to catch).\n"
        "# Fix by adding the family dir (or its parent) to that repo's\n"
        "# `PYTEST_UNIT_DIR=` in scripts/quality-gates.sh, proving the widened gate\n"
        "# is still GREEN (rule 11a), then re-run `--update-baseline`.\n"
        "#\n"
        "# LOWER counts as families get gated. NEVER raise a count. Repos not\n"
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

        family_dirs = find_family_unit_dirs(repo_root)
        entries = resolve_effective_entries(qg_text)
        ungated = ungated_families(family_dirs, entries)
        observed[repo_name] = len(ungated)
        allowed = baseline.allowed(repo_name)
        if len(ungated) > allowed:
            over = ungated[allowed:] if allowed < len(ungated) else ungated
            failures.append(
                f"[FAIL] {repo_name}: {len(ungated)} ungated family/families > baseline {allowed}. "
                f"New: {', '.join(over)}"
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
            "\n→ A tests/<family>/unit/ dir isn't reachable via that repo's PYTEST_UNIT_DIR — add it (or its "
            "parent) to scripts/quality-gates.sh's PYTEST_UNIT_DIR=, proving the widened gate is still GREEN "
            "(rule 11a). Baseline: unified-trading-pm/scripts/quality_gates/pytest_unit_dir_coverage_baseline.yaml "
            "(NEVER raise a count). SSOT: plans/active/issues/mtds_ungated_test_families_2026_07_17.md.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
