#!/usr/bin/env python3
# Epic: instruments_master
# Lifecycle: permanent
# Delete-when: NA
"""AST-based "query-don't-derive" gate: no T2 consumer hardcodes a value the
instruments-service catalogue owns as a MUTABLE field.

Design SSOT: ``unified-trading-pm/plans/active/
instruments_catalogue_definitions_and_field_history_2026_08_17.md`` § "The
query-don't-derive gate":

    A downstream service must query the catalogue for an instrument
    attribute, never derive or hardcode it. Tick size and contract size are
    the specimens: a service computing its own tick size is carrying a stale
    copy of a mutable field.

The catalogue's currently-declared mutable field is ``contract_size``
(``instruments_service/reference_data/catalogue_field_history.py::
MUTABLE_CATALOGUE_FIELDS``). ``tick_size`` is named in the design doc as a
would-be specimen too but does NOT currently survive into the persisted
41-column rolled-up catalogue (a gap the field-history module's own docstring
flags) -- so it is not yet a real field to hardcode-detect against; extend
``DEFAULT_MUTABLE_FIELDS`` below (or pass ``--fields``) the day it lands.

Precedent this discriminator is modelled on: ``scripts/cicd/
detect_breaking_change.py``'s content-based AST differ, and this repo's own
``scripts/qg/no_hardcoded_venue_universe.py`` family of hardcode gates --
same shape (module-level constant / dict / comparison scan for a specific
name class), applied to a different name class.

Shared discriminator note: ``instruments_catalogue_definitions_and_field_
history_2026_08_17.md`` explicitly asks this check to "share one
discriminator" with the reference-data-in-a-code-path rule from
``strategy_service_centralization_fixes_2026_08_16.md`` (the
``MarginModel.AAVE_V3``-hardcoded-regardless-of-protocol class) rather than
inventing a second walker. ``find_hardcoded_reference_literals()`` below is
written generically for exactly that reuse: it takes an arbitrary
``field_names`` set and a source tree, with no catalogue-specific logic
baked into the walk itself -- a future check for a different registry class
(venue eligibility, margin models, ...) can call it directly with a
different name set instead of re-implementing the AST walk.

Usage:
    no_hardcoded_catalogue_attribute.py --repo-root <workspace_root> [--fields contract_size ...] [--json]

Exit code: 0 = no violations, 1 = violations found (or a scan-target repo
directory not found -- see ``main()``: a genuinely absent repo is a config
error worth surfacing, not silently skipped, since a silent skip would let
the whole gate go blind if a repo layout changed).
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from dataclasses import dataclass
from pathlib import Path

# ---------------------------------------------------------------------------
# Declared-mutable field set this gate detects a hardcode of.
#
# SSOT: instruments-service/instruments_service/reference_data/
# catalogue_field_history.py::MUTABLE_CATALOGUE_FIELDS. Kept as an explicit,
# manually-synced constant here rather than importing instruments_service's
# package at runtime -- this script runs from unified-trading-pm's own venv
# against THREE repos (instruments-service, market-tick-data-service,
# market-data-processing-service), none of which this script's own process
# is guaranteed to have installed; a cross-repo runtime import would also be
# exactly the service<->service coupling this workspace's tier rule bans for
# code, and a gate script is not exempt from that principle. ``--fields``
# lets a caller override without editing this file.
# ---------------------------------------------------------------------------
DEFAULT_MUTABLE_FIELDS: frozenset[str] = frozenset({"contract_size"})

# Repo-relative source roots this gate scans, one per T2-owned repo. A repo
# directory absent under --repo-root is a hard error (see main()), not a
# silent skip -- this script is invoked from instruments-service's own
# quality-gates.sh, which always has all three T2 repos as siblings.
_SCAN_TARGETS: tuple[tuple[str, str], ...] = (
    ("instruments-service", "instruments_service"),
    ("market-tick-data-service", "market_tick_data_service"),
    ("market-data-processing-service", "market_data_processing_service"),
)

# instruments-service's OWN catalogue writer/reader modules -- the SSOT for
# these fields is allowed to declare/assign them literally (schema columns,
# adapter-parsed reference data, static per-contract specs for venues whose
# API never returns one). Repo-relative path PREFIXES (posix-style).
_CATALOGUE_OWNER_PREFIXES: tuple[str, ...] = (
    "instruments_service/reference_data/",
    "instruments_service/scripts/",
    "instruments-service/scripts/",
)

# Never scan test fixtures -- constructing a literal instrument record with
# contract_size=100 in a test is not a hardcode-in-a-code-path violation, it
# is test data.
_TEST_PATH_MARKERS: tuple[str, ...] = ("/tests/", "/test_")

# Inline suppression marker, same convention as no_hardcoded_venue_universe.sh's
# "qg-allow: venue-universe-fallback" -- a deliberately-reviewed exception can
# carry this on the offending line with a reason.
SANCTION_MARKER = "qg-allow: catalogue-attribute-hardcode"


@dataclass(frozen=True)
class Violation:
    path: str
    line: int
    field: str
    snippet: str


def _binding_name(node: ast.expr) -> str | None:
    """Return the bare name a literal is being bound to/compared against, or
    None if ``node`` isn't a name-like binding target.

    Handles ``NAME``, ``obj.NAME`` (attribute), and ``obj["NAME"]``
    (string-keyed subscript) -- the three shapes a field name shows up as an
    assignment/comparison target across this codebase's adapters.
    """
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Subscript):
        sl = node.slice
        if isinstance(sl, ast.Constant) and isinstance(sl.value, str):
            return sl.value
    return None


def _is_hardcoded_literal(node: ast.expr) -> bool:
    """True if ``node`` is a plain literal value, or a dict/list/tuple/set
    built entirely out of literal values (a hardcoded lookup table -- the
    ``MarginModel.AAVE_V3``-style "one constant regardless of input" shape).

    Explicitly EXCLUDES ``None`` -- a field declared/defaulted to None is
    "not applicable here" (e.g. a DeFi AMM position's contract_size), not a
    hardcoded VALUE; and excludes bool (``True``/``False`` are never a
    catalogue attribute value in this codebase). A RHS that is a Call,
    Attribute access, Name reference, or comprehension is NEVER flagged --
    those are exactly the "derived/queried" shapes this gate must not
    false-positive on.
    """
    if isinstance(node, ast.Constant):
        v = node.value
        if v is None or isinstance(v, bool):
            return False
        return isinstance(v, (int, float, str))
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
        return _is_hardcoded_literal(node.operand)
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        return bool(node.elts) and all(_is_hardcoded_literal(e) for e in node.elts)
    if isinstance(node, ast.Dict):
        return bool(node.values) and all(v is not None and _is_hardcoded_literal(v) for v in node.values)
    return False


def _snippet(source_lines: list[str], lineno: int) -> str:
    idx = lineno - 1
    return source_lines[idx].strip() if 0 <= idx < len(source_lines) else ""


def find_hardcoded_reference_literals(
    tree: ast.AST,
    source_lines: list[str],
    field_names: frozenset[str],
) -> list[Violation]:
    """Generic discriminator: walk ``tree`` for a hardcoded literal
    assigned to, defaulted to, keyed by, or compared against a name in
    ``field_names`` (case-insensitive). Not catalogue-specific -- see the
    module docstring's "Shared discriminator note".

    Detects three shapes:
      1. Assignment / annotated assignment: ``contract_size = 100`` or
         ``contract_size: float = 100.0`` (module, class, or function scope).
      2. Dict literal entry: ``{"contract_size": 100}`` (a hardcoded
         per-venue/per-instrument lookup table).
      3. Equality comparison: ``if position.contract_size == 100:`` (a
         hardcoded threshold check standing in for a real catalogue read).
    """
    lowered = {f.lower() for f in field_names}
    violations: list[Violation] = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            value = node.value
            if value is None:
                continue
            for tgt in targets:
                name = _binding_name(tgt)
                if name and name.lower() in lowered and _is_hardcoded_literal(value):
                    violations.append(Violation("", node.lineno, name, _snippet(source_lines, node.lineno)))
        elif isinstance(node, ast.Dict):
            for k, v in zip(node.keys, node.values, strict=True):
                if (
                    isinstance(k, ast.Constant)
                    and isinstance(k.value, str)
                    and k.value.lower() in lowered
                    and v is not None
                    and _is_hardcoded_literal(v)
                ):
                    violations.append(Violation("", k.lineno, k.value, _snippet(source_lines, k.lineno)))
        elif isinstance(node, ast.Compare):
            chain: list[ast.expr] = [node.left, *node.comparators]
            for i, op in enumerate(node.ops):
                if not isinstance(op, (ast.Eq, ast.NotEq)):
                    continue
                a, b = chain[i], chain[i + 1]
                for lhs, rhs in ((a, b), (b, a)):
                    name = _binding_name(lhs)
                    if name and name.lower() in lowered and _is_hardcoded_literal(rhs):
                        violations.append(Violation("", node.lineno, name, _snippet(source_lines, node.lineno)))

    return violations


def _is_excluded(rel_path: str) -> bool:
    posix = rel_path.replace("\\", "/")
    if any(m in f"/{posix}" for m in _TEST_PATH_MARKERS):
        return True
    return any(posix.startswith(p) for p in _CATALOGUE_OWNER_PREFIXES)


def scan_file(path: Path, field_names: frozenset[str]) -> list[Violation]:
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    lines = source.splitlines()
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError:
        return []
    raw = find_hardcoded_reference_literals(tree, lines, field_names)
    out: list[Violation] = []
    for v in raw:
        line_text = lines[v.line - 1] if 0 <= v.line - 1 < len(lines) else ""
        if SANCTION_MARKER in line_text:
            continue
        out.append(Violation(str(path), v.line, v.field, v.snippet))
    return out


def scan_repo(repo_root: Path, repo_dir: str, source_dir: str, field_names: frozenset[str]) -> list[Violation]:
    base = repo_root / repo_dir / source_dir
    if not base.is_dir():
        return []
    violations: list[Violation] = []
    for py_file in sorted(base.rglob("*.py")):
        rel = f"{repo_dir}/{py_file.relative_to(repo_root / repo_dir).as_posix()}"
        if _is_excluded(rel):
            continue
        violations.extend(scan_file(py_file, field_names))
    return violations


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo-root", required=True, help="workspace root containing the T2 repo checkouts as siblings")
    ap.add_argument(
        "--fields",
        nargs="*",
        default=None,
        help="mutable catalogue field names to detect (default: DEFAULT_MUTABLE_FIELDS)",
    )
    ap.add_argument("--json", action="store_true", dest="as_json")
    args = ap.parse_args()

    repo_root = Path(args.repo_root)
    field_names = frozenset(args.fields) if args.fields else DEFAULT_MUTABLE_FIELDS

    missing = [repo_dir for repo_dir, _ in _SCAN_TARGETS if not (repo_root / repo_dir).is_dir()]
    if missing:
        print(f"ERROR: expected T2 repo(s) not found under {repo_root}: {missing}", file=sys.stderr)
        return 1

    all_violations: list[Violation] = []
    for repo_dir, source_dir in _SCAN_TARGETS:
        all_violations.extend(scan_repo(repo_root, repo_dir, source_dir, field_names))

    if args.as_json:
        print(
            json.dumps(
                {
                    "violation_count": len(all_violations),
                    "violations": [
                        {"path": v.path, "line": v.line, "field": v.field, "snippet": v.snippet} for v in all_violations
                    ],
                },
                indent=2,
            )
        )
    else:
        if all_violations:
            print(f"HARDCODED CATALOGUE ATTRIBUTE — {len(all_violations)} violation(s):")
            for v in all_violations:
                print(f"  {v.path}:{v.line}: hardcoded '{v.field}' — {v.snippet}")
            print(
                "Query the instruments-service catalogue instead of hardcoding a mutable field "
                "(unified_trading_library.instruments_catalog_reader.read_instruments_catalog_contract_size, "
                "or the venue's own live instrument metadata where the catalogue channel is not yet reliable). "
                "SSOT: /plans/active/instruments_catalogue_definitions_and_field_history_2026_08_17.md "
                '§ "The query-don\'t-derive gate". A deliberately-reviewed exception may carry an inline '
                f'"# {SANCTION_MARKER} <reason>" on the offending line.'
            )
        else:
            print("OK: no_hardcoded_catalogue_attribute — no hardcoded mutable-catalogue-field literals found")

    return 1 if all_violations else 0


if __name__ == "__main__":
    sys.exit(main())
