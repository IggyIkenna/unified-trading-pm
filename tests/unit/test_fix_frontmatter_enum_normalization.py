"""Unit tests for the present-but-invalid enum remapping in scripts/plan-hygiene/fix_frontmatter.py.

The fixer historically only ADDED missing fields. A field present with a value outside its docspec
enum (an issue doc with ``nature: test-harness-gap``, or ``stage: foundation``) still red-lined the
corpus frontmatter gate for the WHOLE FLEET (measured 2026-07-20: slot-4 landed three such docs that
blocked PM's LDR gate for every agent). These values are PARSEABLE — valid YAML, wrong vocabulary —
so the fixer's refuse-on-unparseable contract does not apply, and ``normalize_invalid_enums`` maps
them onto valid docspec vocabulary conservatively.

Guards, most-important first:
  * VALID values are NEVER remapped (no false positives that would churn good docs).
  * The remap targets are sourced from docspec (the same SSOT the checker gates on) — not hardcoded.
  * Unknown-invalid values fall back to a NEUTRAL catch-all, never a specific fabricated guess.
"""

from __future__ import annotations

import importlib.util
import types
from pathlib import Path


def _load_module() -> types.ModuleType:
    repo_root = Path(__file__).resolve().parents[2]
    path = repo_root / "scripts" / "plan-hygiene" / "fix_frontmatter.py"
    spec = importlib.util.spec_from_file_location("fix_frontmatter", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


FF = _load_module()


def _run(fm_fields: list[str]) -> tuple[dict[str, str], list[str]]:
    """Run normalize_invalid_enums over a frontmatter field list; return {field: 'field: value'}."""
    lines = [f"{line}\n" for line in fm_fields]
    changes: list[str] = []
    FF.normalize_invalid_enums(lines, changes)
    got: dict[str, str] = {}
    for line in lines:
        for key in ("nature", "stage", "scope"):
            if line.startswith(f"{key}:"):
                got[key] = line.strip()
    return got, changes


def test_enums_loaded_from_docspec() -> None:
    """The remap must be driven by the real docspec vocabularies, not empty/hardcoded sets."""
    assert FF._NATURE and "issue" in FF._NATURE
    assert FF._STAGE and "data" in FF._STAGE and "meta" in FF._STAGE
    assert FF._SCOPE and "engineer" in FF._SCOPE


def test_remaps_the_exact_slot4_violations() -> None:
    got, changes = _run(
        [
            "doc_type: issue",
            "nature: test-harness-gap",
            "stage: foundation",
            "scope: /data-pipeline-check-mtds checker + launch-mtds-backfill-vm.sh",
        ]
    )
    assert got["nature"] == "nature: issue"
    assert got["stage"] == "stage: [data]"
    assert got["scope"] == "scope: [engineer, admin]"
    assert len(changes) == 3  # each remap is logged for the diff


def test_valid_values_are_never_remapped() -> None:
    """The single most important guard: a doc that is already valid must be left byte-untouched."""
    got, changes = _run(
        [
            "doc_type: issue",
            "nature: issue",
            "stage: [data, features]",
            "scope: [engineer]",
        ]
    )
    assert changes == []
    assert got["stage"] == "stage: [data, features]"


def test_partial_valid_list_keeps_valid_drops_invalid() -> None:
    got, _ = _run(["doc_type: issue", "stage: [data, foundation, bogus]"])
    assert got["stage"] == "stage: [data]"


def test_unknown_invalid_falls_back_to_neutral_default_not_a_guess() -> None:
    got, _ = _run(["doc_type: plan", "stage: [wibble]", "nature: nonsense"])
    assert got["stage"] == "stage: [meta]"  # neutral catch-all, not a fabricated specific stage
    assert got["nature"] == "nature: process"  # doc_type=plan → process


def test_unknown_doc_type_leaves_invalid_nature_for_a_human() -> None:
    """No doc_type mapping → the fixer does not fabricate a nature; the corpus gate still catches it."""
    _, changes = _run(["doc_type: some-new-type", "nature: bogus"])
    assert changes == []


def test_bare_scalar_stage_alias_applies() -> None:
    got, _ = _run(["doc_type: issue", "stage: foundation"])
    assert got["stage"] == "stage: [data]"
