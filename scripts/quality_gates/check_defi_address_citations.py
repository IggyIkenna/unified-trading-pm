#!/usr/bin/env python3
"""QG STEP 5.97 — DeFi contract-address citation ratchet.

Enforces that any new Ethereum contract address (``0x`` + 40 hex chars) added
to ``unified_api_contracts/registry/`` carries a ``# DERIVED <date> from
<source>`` citation comment on the same line, so the address is traceable to
an on-chain source.  Existing uncited addresses are grandfathered via a
per-repo SHRINKING ratchet (``defi_address_citation_baseline.yaml``).

Background: AAVE_V3 ETHEREUM launch date was 49 days wrong (corrected
2026-05-08 via subgraph evidence).  A systematic audit of Category-A
immutable on-chain values surfaced dozens of contract addresses that lack
provenance citations — an ops risk when addresses need audit or correction.
This gate ensures NEW additions always carry a citation so the next auditor
can trace them. (The ``defi_onchain_derivable_values_and_date_drift_2026_06_20``
plan Phase 1 covers deriving PROTOCOL_LAUNCH_DATES from on-chain; this gate
enforces the citation FORM for all addresses across the registry.)

Shape — **baseline ratchet** (NOT zero-tolerance from day 1):

  1. Load ``defi_address_citation_baseline.yaml`` — per-repo count of the
     currently-known uncited contract addresses in ``unified_api_contracts/
     registry/`` source (excluding lines carrying a
     ``# QG-allow: defi-citation`` marker — the explicit, audited exemption).
  2. Scan every ``.py`` file under the given source dir(s) (skipping venvs /
     build artefacts / ``tests/``).
  3. If a repo's count is ``<=`` its baseline → OK (warn if below so the
     operator knows to ratchet DOWN). If count ``>`` baseline → ERROR — a NEW
     uncited address landed; add ``# DERIVED <date> from <source>`` on the
     same line, or add ``# QG-allow: defi-citation`` with a one-line reason.

The baseline ONLY shrinks: as citations are back-filled, re-run with
``--update-baseline`` to lower the counts.  NEVER raise a baseline entry.

Exemption marker (per-line): ``# QG-allow: defi-citation`` followed by a
reason (e.g. ``# QG-allow: defi-citation — pool address auto-deployed by factory``).

Citation format (per-line): ``# DERIVED <YYYY-MM-DD> from <chain> <source>``
(e.g. ``# DERIVED 2026-05-08 from ethereum etherscan tx 0xabc...``).  Any
comment containing the word ``DERIVED`` (case-sensitive) on the same line as
the address is accepted.

Usage::

    # per-repo (run by base-service.sh STEP 5.97):
    python check_defi_address_citations.py --workspace-root <ws> --scope <repo-dir>

    # workspace-wide sweep:
    python check_defi_address_citations.py --workspace-root <ws>

    # ratchet the baseline DOWN after back-filling citations:
    python check_defi_address_citations.py --workspace-root <ws> --update-baseline
"""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

import yaml

# ── Constants ────────────────────────────────────────────────────────────────

#: Matches an Ethereum-style contract address: ``0x`` followed by exactly 40
#: hexadecimal characters (upper or lower).  Word-boundary anchored so we
#: don't match partial strings like ``0x1234567890abcdef1234567890abcdef12345678XX``.
ADDR_RE: Final[re.Pattern[str]] = re.compile(
    r"\b0x[0-9a-fA-F]{40}\b"
)

#: Exemption marker.  A line carrying this token (after ``# QG-allow:``) is
#: skipped — the address is explicitly audited and grandfathered.
ALLOW_MARKER: Final[str] = "QG-allow: defi-citation"

#: Citation marker.  A line with ``# DERIVED`` anywhere after the address is
#: considered cited.  The full intended format is:
#: ``# DERIVED <YYYY-MM-DD> from <chain> <source>`` but we accept any
#: same-line occurrence of the word DERIVED in a comment to be flexible
#: about whitespace and to avoid false failures on minor formatting variation.
DERIVED_MARKER: Final[str] = "DERIVED"

#: Directories to skip when walking.
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
        "tests",
        "mocks",
        "audits",
        "external",
    }
)

#: Path fragments that indicate archived / generated / mock trees.
EXCLUDE_PATH_FRAGMENTS: Final[tuple[str, ...]] = (
    "/archive/",
    "/.archive/",
    "/_archived/",
    ".egg-info",
    "/mocks/",
    "/external/",
    "/testing/",
    "/audits/",
)

#: Sub-directories under ``unified_api_contracts/`` to scan for addresses.
#: We only gate the REGISTRY module — that's where protocol-level constants
#: (token addresses, factory addresses, WETH/WBTC, router addresses) live.
#: ``external/``, ``mocks/``, ``testing/`` are excluded from the ratchet.
REGISTRY_SUBDIR: Final[str] = "registry"

#: File name prefixes that indicate test files.
TEST_FILE_PREFIXES: Final[tuple[str, ...]] = ("test_",)
TEST_FILE_SUFFIXES: Final[tuple[str, ...]] = ("_test.py",)


# ── Baseline ─────────────────────────────────────────────────────────────────


def _baseline_path() -> Path:
    return Path(__file__).resolve().parent / "defi_address_citation_baseline.yaml"


@dataclass(frozen=True)
class Baseline:
    """Per-repo allowed count of uncited Ethereum contract addresses."""

    counts: dict[str, int] = field(default_factory=dict)
    note: str = ""

    def allowed(self, repo: str) -> int:
        return int(self.counts.get(repo, 0))


def load_baseline() -> Baseline:
    path = _baseline_path()
    if not path.exists():
        return Baseline()
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    repos_raw = raw.get("repos") or {}
    counts: dict[str, int] = {}
    for repo, val in repos_raw.items():
        if isinstance(val, dict):
            counts[str(repo)] = int(val.get("count", 0))
        else:
            counts[str(repo)] = int(val)
    return Baseline(counts=counts, note=str(raw.get("note") or ""))


def write_baseline(counts: dict[str, int], existing: Baseline) -> None:
    """Persist a new baseline.  Counts are clamped DOWN — never raised above
    the existing baseline (a higher count means a new uncited address landed;
    fix it, don't bake it in)."""
    path = _baseline_path()
    merged: dict[str, dict[str, int]] = {}
    all_repos = set(counts) | set(existing.counts)
    for repo in sorted(all_repos):
        observed = int(counts.get(repo, 0))
        prior = existing.allowed(repo)
        merged[repo] = {"count": min(observed, prior) if repo in existing.counts else observed}
    header = (
        "# Baseline for QG STEP 5.97 — DeFi contract-address citation ratchet.\n"
        "#\n"
        "# This is a SHRINKING ratchet. `repos[<repo>].count` is the number of\n"
        "# Ethereum contract addresses (0x + 40 hex) in `unified_api_contracts/\n"
        "# registry/` WITHOUT a `# DERIVED <date> from <source>` citation comment\n"
        "# (and without a `# QG-allow: defi-citation` exemption) that CI tolerates.\n"
        "# A repo whose live count EXCEEDS its baseline fails CI — a NEW uncited\n"
        "# address landed; add `# DERIVED <YYYY-MM-DD> from <chain> <source>` on\n"
        "# the same line, or add `# QG-allow: defi-citation — <reason>` if it is\n"
        "# a deliberate, audited address that doesn't fit the derivation model\n"
        "# (e.g. a Uniswap pool address auto-deployed by the factory).\n"
        "#\n"
        "# LOWER a count (re-run `--update-baseline`) after back-filling citations.\n"
        "# NEVER raise a count.\n"
        "#\n"
        "# Repos not listed default to count=0 (zero tolerance).\n"
        "#\n"
        "# SSOT: defi_onchain_derivable_values_and_date_drift_2026_06_20.md Phase 5.\n"
    )
    body = yaml.safe_dump(
        {
            "note": existing.note
            or "Seeded 2026-06-16 (slot 4) — defi_onchain_derivable_values Phase 5 (QG STEP 5.97).",
            "repos": merged,
        },
        sort_keys=True,
        default_flow_style=False,
        allow_unicode=True,
    )
    _ = path.write_text(header + body, encoding="utf-8")


# ── Scanning ─────────────────────────────────────────────────────────────────


def _is_excluded_path(path: Path) -> bool:
    if any(part in EXCLUDE_DIR_NAMES for part in path.parts):
        return True
    posix = path.as_posix()
    if any(frag in posix for frag in EXCLUDE_PATH_FRAGMENTS):
        return True
    name = path.name
    if any(name.startswith(p) for p in TEST_FILE_PREFIXES):
        return True
    return bool(any(name.endswith(s) for s in TEST_FILE_SUFFIXES))


def _iter_py_files(root: Path) -> Iterator[Path]:
    if root.is_file() and root.suffix == ".py" and not _is_excluded_path(root):
        yield root
        return
    for path in root.rglob("*.py"):
        if _is_excluded_path(path.relative_to(root) if path.is_relative_to(root) else path):
            continue
        if _is_excluded_path(path):
            continue
        yield path


def _line_is_uncited(line: str) -> bool:
    """Return True if the line contains an Ethereum address that lacks a
    ``# DERIVED`` citation AND lacks a ``# QG-allow: defi-citation`` exemption.

    Skips:
    - Pure comment lines (``# ...``)
    - Lines with the ALLOW_MARKER
    - Lines with the DERIVED_MARKER in a comment
    """
    stripped = line.lstrip()
    if stripped.startswith("#"):
        return False  # pure comment — not a live value
    if not ADDR_RE.search(line):
        return False  # no address on this line
    if ALLOW_MARKER in line:
        return False  # explicitly exempted
    # Check if a comment on this line contains DERIVED
    comment_idx = line.find("#")
    return not (comment_idx != -1 and DERIVED_MARKER in line[comment_idx:])


def count_uncited_in_file(path: Path) -> list[int]:
    """Return 1-based line numbers of uncited Ethereum addresses in ``path``."""
    hits: list[int] = []
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return hits
    for lineno, line in enumerate(source.splitlines(), start=1):
        if _line_is_uncited(line):
            hits.append(lineno)
    return hits


@dataclass(frozen=True)
class RepoScan:
    repo: str
    count: int
    sites: list[tuple[str, int]]  # (repo-relative-file, line)


def scan_repo(repo_root: Path, repo_name: str) -> RepoScan:
    """Scan ``unified_api_contracts/registry/`` under ``repo_root``."""
    sites: list[tuple[str, int]] = []
    # Only scan the registry sub-package where protocol constants live.
    # external/, mocks/, testing/ are excluded by EXCLUDE_DIR_NAMES already,
    # but we also scope to registry/ explicitly to avoid false-positives from
    # generated or mock files elsewhere in the UAC package.
    scan_roots: list[Path] = []
    uac_pkg = repo_root / "unified_api_contracts"
    registry_dir = uac_pkg / REGISTRY_SUBDIR
    if registry_dir.is_dir():
        scan_roots.append(registry_dir)
    else:
        # Fallback: scan the whole repo (other repos have 0 addresses → ratchet
        # at 0 → nothing breaks).
        scan_roots.append(repo_root)

    for scan_root in scan_roots:
        for py in _iter_py_files(scan_root):
            for ln in count_uncited_in_file(py):
                rel = py.relative_to(repo_root).as_posix() if py.is_relative_to(repo_root) else py.as_posix()
                sites.append((rel, ln))
    return RepoScan(repo=repo_name, count=len(sites), sites=sorted(sites))


# ── Scope resolution ─────────────────────────────────────────────────────────


def _resolve_scopes(workspace_root: Path, scope: str | None) -> list[tuple[str, Path]]:
    """Return [(repo_name, repo_root)].  If --scope given → just that repo."""
    if scope:
        repo_root = workspace_root / scope
        if not repo_root.is_dir():
            print(
                f"[check_defi_address_citations] --scope {scope!r} not a dir under {workspace_root}",
                file=sys.stderr,
            )
            return []
        return [(scope, repo_root)]
    out: list[tuple[str, Path]] = []
    for child in sorted(workspace_root.iterdir()):
        if not child.is_dir():
            continue
        if child.name.startswith("."):
            continue
        if (child / ".git").exists() or (child / ".git").is_file():
            out.append((child.name, child))
    return out


# ── main ─────────────────────────────────────────────────────────────────────


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="DeFi contract-address citation ratchet (QG STEP 5.97)."
    )
    parser.add_argument("--workspace-root", required=True, type=Path)
    parser.add_argument("--scope", default=None, help="Single repo dir name (per-repo QG mode).")
    parser.add_argument(
        "--update-baseline",
        action="store_true",
        help="Rewrite the baseline with the observed counts (clamped DOWN — never raised).",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    workspace_root: Path = args.workspace_root.resolve()
    update_baseline_flag = bool(args.update_baseline)
    baseline = load_baseline()
    scopes = _resolve_scopes(workspace_root, args.scope)
    if not scopes:
        print("[check_defi_address_citations] no repos in scope.", file=sys.stderr)
        return 0

    observed: dict[str, int] = {}
    failures: list[str] = []
    warnings: list[str] = []

    for repo_name, repo_root in scopes:
        scan = scan_repo(repo_root, repo_name)
        observed[repo_name] = scan.count
        allowed = baseline.allowed(repo_name)
        if scan.count > allowed:
            new_sites = scan.sites[allowed:] if allowed < len(scan.sites) else scan.sites
            sites_str = "; ".join(f"{f}:{ln}" for f, ln in new_sites[:20])
            failures.append(
                f"[FAIL] {repo_name}: {scan.count} uncited contract address(es) "
                f"> baseline {allowed}. New/over-baseline site(s): {sites_str}"
                + (" ..." if len(new_sites) > 20 else "")
            )
        elif scan.count < allowed:
            warnings.append(
                f"[WARN] {repo_name}: {scan.count} < baseline {allowed} — ratchet "
                f"the baseline DOWN (re-run `--update-baseline`)."
            )
        else:
            warnings.append(f"[OK]   {repo_name}: {scan.count} (== baseline)")

    if update_baseline_flag:
        write_baseline(observed, baseline)
        print(f"[check_defi_address_citations] baseline updated at {_baseline_path()}")
        for line in sorted(f"  {r}: {c}" for r, c in observed.items()):
            print(line)
        return 0

    for w in warnings:
        print(w)
    for f in failures:
        print(f, file=sys.stderr)
    if failures:
        print(
            "\n→ Add `# DERIVED <YYYY-MM-DD> from <chain> <source>` on the same line as the address "
            "(e.g. `\"0x...\"  # DERIVED 2026-05-08 from ethereum etherscan tx 0xabc...`), "
            "OR add `# QG-allow: defi-citation — <reason>` if this is a pool/pair address "
            "auto-deployed by a factory (not a protocol-level SSOT constant). "
            "SSOT: defi_onchain_derivable_values_and_date_drift_2026_06_20.md Phase 5. "
            "Baseline: unified-trading-pm/scripts/quality_gates/defi_address_citation_baseline.yaml "
            "(NEVER raise a count).",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
