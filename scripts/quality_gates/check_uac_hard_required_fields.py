#!/usr/bin/env python3
"""STEP 5.83 — UAC hard-required field validation regression guard.

Two assertions:

  (a) UAC regression guard: the canonical instrument validation functions
      (``validate_instrument_records`` + the key per-rule landmarks) are still
      present in ``unified_api_contracts/internal/reference/``.  This guards
      against accidental deletion of the hard-required enforcement logic shipped
      in uac@37d1ddb (InstrumentRecord model_validator / validate_instrument_records).
      Phase 1 nullable→required field flips are still pending; this check
      ensures the shipped RUNTIME validator is not silently regressed before
      the static flips land.

  (b) Bundled-shard key kwargs: every literal
      ``record_captured(data_type="<bundled_type>", …)`` call in the calling
      repo's source MUST include the required shard-key kwarg.  Complements the
      UTL runtime ``MalformedRowKeyError`` guard (UTL@0caa08e3) with STATIC
      coverage so regressions are caught before they reach the write boundary.

      Bundled types and their required kwargs
      (per CLAUDE.md "shard-granularity SSOT" + UAC MalformedRowKeyError logic):
        options_chain                      → ``options_chain=``
        futures_chain                      → ``chain=``
        prediction_canonical_question_group → ``instrument_id=`` (the cqg, canonical v9 column)
        sports_fixture_bundle              → ``fixture_id=``

      Inline opt-out: ``# QG-allow: shard-key-not-applicable`` on the same line.

Exit codes:
  0 — all assertions pass (or only warned occurrences)
  1 — new violation(s) found (FAIL)
  2 — checker setup error

Plan: hard_schema_enforcement_2026_05_08.md Phase 5.
SSOT: CLAUDE.md "shard-granularity SSOT" + "Manifest + honest absence".
"""

from __future__ import annotations

import argparse
import ast
import sys
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Final

# ──────────────────────────────────────────────────────────────────────────────
# Part (a) — regression-guard landmarks in UAC instrument_validation.py
# ──────────────────────────────────────────────────────────────────────────────

#: Expected function names that MUST exist in the UAC instrument validation module.
UAC_REQUIRED_FUNCTIONS: Final[tuple[str, ...]] = (
    "validate_instrument_records",
    "_check_record",
    "_infer_asset_group",
)

#: String landmarks that MUST appear somewhere in the UAC instrument validation
#: source — each guards one of the 3 closed-set rules shipped in uac@37d1ddb.
#: If any disappears, the hard-required enforcement is silently regressed.
UAC_REQUIRED_LANDMARKS: Final[tuple[tuple[str, str], ...]] = (
    # Rule 1 — quote_asset required for CeFi / TradFi
    ("quote_asset", "quote_asset required check"),
    # Rule 2 — expiry required for futures / options
    ("expiry", "expiry required check"),
    # Rule 3 — DeFi raw_symbol / address format validation
    ("_validate_defi_raw_symbol", "DeFi raw_symbol format validator"),
)

#: Path to the UAC instrument validation module, relative to workspace root.
_UAC_VALIDATION_REL = (
    "unified-api-contracts",
    "unified_api_contracts",
    "internal",
    "reference",
    "instrument_validation.py",
)

# ──────────────────────────────────────────────────────────────────────────────
# Part (b) — bundled-shard key kwargs check
# ──────────────────────────────────────────────────────────────────────────────

#: Bundled data_type literals → required shard-key kwarg name.
#: Source: UAC MalformedRowKeyError guard + CLAUDE.md "shard-granularity SSOT".
#: prediction: the bundled cqg atom's identity is carried in ``instrument_id`` (the canonical v9
#: convention — MTDS ``record_captured_from_counts`` puts cqg in the row_key ``instrument_id`` and
#: deployment-api ``_prediction_venue_detail`` reads ``instrument_id`` first). ``record_captured``
#: has no ``canonical_question_group`` param (the prior required kwarg was unsatisfiable), so the
#: checkable column is ``instrument_id`` (slot-5 2026-06-04, STEP 5.83 reconciliation).
BUNDLED_TYPE_REQUIRED_KWARGS: Final[dict[str, str]] = {
    "options_chain": "options_chain",
    "futures_chain": "chain",
    "prediction_canonical_question_group": "instrument_id",
    "sports_fixture_bundle": "fixture_id",
}

#: record_* method names where the data_type= kwarg is accepted.
RECORD_METHOD_NAMES: Final[frozenset[str]] = frozenset(
    {
        "record_captured",
        "record_captured_from_counts",
    }
)

#: Top-level directories to skip when walking source trees.
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
        "archive",
        "archived",
    }
)

OPT_OUT_MARKER: Final[str] = "# QG-allow: shard-key-not-applicable"


@dataclass(frozen=True)
class Violation:
    file: Path
    line: int
    message: str


# ──────────────────────────────────────────────────────────────────────────────
# Part (a) helpers
# ──────────────────────────────────────────────────────────────────────────────


def _check_uac_regression(workspace_root: Path) -> list[str] | None:
    """Return list of failure messages if UAC validation landmarks are regressed.

    Returns None when the UAC repo is not present as a workspace sibling — Part (a)
    is a regression guard on UAC's own source and only meaningful when UAC is
    checked out alongside the calling repo. PM (and any other repo without UAC
    as a sibling) treats this as SKIP, not FAIL.
    """
    failures: list[str] = []

    validation_file = workspace_root.joinpath(*_UAC_VALIDATION_REL)
    if not validation_file.exists():
        return None  # SKIP — UAC not present in workspace

    source = validation_file.read_text(encoding="utf-8")

    # Check required functions via AST
    try:
        tree = ast.parse(source, filename=str(validation_file))
    except SyntaxError as exc:
        failures.append(f"UAC instrument_validation.py has a syntax error: {exc}")
        return failures

    defined_functions: set[str] = {
        node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    for fn_name in UAC_REQUIRED_FUNCTIONS:
        if fn_name not in defined_functions:
            failures.append(
                f"UAC regression: function `{fn_name}` missing from instrument_validation.py.\n"
                "  Required for hard-schema-enforcement (uac@37d1ddb / hard_schema_enforcement Phase 5).\n"
                "  Do NOT remove without a successor implementation + plan approval."
            )

    # Check string landmarks
    for landmark, description in UAC_REQUIRED_LANDMARKS:
        if landmark not in source:
            failures.append(
                f"UAC regression: '{landmark}' ({description}) missing from instrument_validation.py.\n"
                "  The hard-required field enforcement has been silently removed.\n"
                "  Restore per hard_schema_enforcement_2026_05_08.md Phase 1 + Phase 5."
            )

    return failures


# ──────────────────────────────────────────────────────────────────────────────
# Part (b) helpers
# ──────────────────────────────────────────────────────────────────────────────


def _iter_python_files(root: Path) -> Iterator[Path]:
    for path in root.rglob("*.py"):
        if any(part in EXCLUDE_DIR_NAMES for part in path.parts):
            continue
        yield path


class _BundledShardKeyVisitor(ast.NodeVisitor):
    """AST visitor that finds record_captured calls with literal bundled data_type
    strings missing the required shard-key kwarg."""

    def __init__(self, source_lines: list[str], file_path: Path) -> None:
        self._lines = source_lines
        self._file = file_path
        self.violations: list[Violation] = []

    def visit_Call(self, node: ast.Call) -> None:
        # Match: <anything>.record_captured(...) or record_captured(...)
        method_name: str | None = None
        if isinstance(node.func, ast.Attribute):
            method_name = node.func.attr
        elif isinstance(node.func, ast.Name):
            method_name = node.func.id

        if method_name in RECORD_METHOD_NAMES:
            self._check_bundled_shard_key(node)

        self.generic_visit(node)

    def _check_bundled_shard_key(self, node: ast.Call) -> None:
        # Find data_type= kwarg with a literal string value
        data_type_value: str | None = None
        for kw in node.keywords:
            if kw.arg == "data_type" and isinstance(kw.value, ast.Constant):
                data_type_value = str(kw.value.value)
                break

        if data_type_value is None or data_type_value not in BUNDLED_TYPE_REQUIRED_KWARGS:
            return

        required_kwarg = BUNDLED_TYPE_REQUIRED_KWARGS[data_type_value]

        # Check for opt-out marker on the same source line
        lineno = node.lineno - 1  # 0-indexed
        if lineno < len(self._lines):
            line_text = self._lines[lineno]
            if OPT_OUT_MARKER in line_text:
                return

        # Check that the required shard-key kwarg is present
        present_kwargs = {kw.arg for kw in node.keywords if kw.arg is not None}
        if required_kwarg not in present_kwargs:
            self.violations.append(
                Violation(
                    file=self._file,
                    line=node.lineno,
                    message=(
                        f"record_captured(data_type={data_type_value!r}, ...) "
                        f"missing required shard-key kwarg `{required_kwarg}=`.\n"
                        f"  Bundled shard atoms require: {BUNDLED_TYPE_REQUIRED_KWARGS}\n"
                        f"  Add `{required_kwarg}=<value>` or "
                        f"add '{OPT_OUT_MARKER}' on the same line."
                    ),
                )
            )


def _check_bundled_shard_keys(source_dirs: list[Path]) -> list[Violation]:
    """Walk source dirs, return violations for bundled-shard-key missing kwargs."""
    violations: list[Violation] = []
    for src_dir in source_dirs:
        if not src_dir.is_dir():
            continue
        for py_file in _iter_python_files(src_dir):
            try:
                source = py_file.read_text(encoding="utf-8")
                tree = ast.parse(source, filename=str(py_file))
            except (OSError, SyntaxError):
                continue

            visitor = _BundledShardKeyVisitor(
                source_lines=source.splitlines(),
                file_path=py_file,
            )
            visitor.visit(tree)
            violations.extend(visitor.violations)

    return violations


# ──────────────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────────────


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="STEP 5.83 — UAC hard-required field validation regression guard")
    p.add_argument(
        "--workspace-root",
        type=Path,
        default=Path("."),
        help="Workspace root (contains unified-api-contracts/ checkout)",
    )
    p.add_argument(
        "--scope",
        default="",
        help="Calling repo name (for log context; does not affect UAC check)",
    )
    p.add_argument(
        "--source-dir",
        type=Path,
        default=None,
        help="Primary source dir for Part (b) bundled-shard-key check",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    workspace_root = args.workspace_root.resolve()
    repo_label = args.scope or workspace_root.name

    fail_count = 0

    # ── Part (a): UAC regression guard ────────────────────────────────────────
    uac_failures = _check_uac_regression(workspace_root)
    if uac_failures is None:
        print(
            f"[SKIP] STEP 5.83 ({repo_label}): UAC repo not present in workspace; "
            "Part (a) regression guard skipped (Part (b) bundled-shard-key check still runs)",
            flush=True,
        )
    elif uac_failures:
        for msg in uac_failures:
            print(f"[FAIL] STEP 5.83 ({repo_label}): {msg}", flush=True)
        fail_count += len(uac_failures)
    else:
        print(
            f"[OK] STEP 5.83 ({repo_label}): UAC instrument validation landmarks present "
            "(validate_instrument_records + 3 closed-set rules)",
            flush=True,
        )

    # ── Part (b): bundled-shard-key kwargs ────────────────────────────────────
    source_dirs: list[Path] = []
    if args.source_dir is not None and args.source_dir.is_dir():
        source_dirs.append(args.source_dir)

    if source_dirs:
        shard_violations = _check_bundled_shard_keys(source_dirs)
        if shard_violations:
            for v in shard_violations:
                print(
                    f"[FAIL] STEP 5.83 ({repo_label}): {v.file}:{v.line}: {v.message}",
                    flush=True,
                )
            fail_count += len(shard_violations)
        else:
            print(
                f"[OK] STEP 5.83 ({repo_label}): All literal record_captured(data_type=<bundled>) "
                "calls include required shard-key kwarg",
                flush=True,
            )
    else:
        print(
            f"[OK] STEP 5.83 ({repo_label}): Part (b) skipped (no --source-dir provided)",
            flush=True,
        )

    return 1 if fail_count > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
