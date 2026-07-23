# Epic: agent_operating_framework_master
# Lifecycle: permanent
# Delete-when: NA
"""Unit tests for check_doc_retrieval_layer_parity.py.

Verifies the live corpus is clean (schema<->generator parity + cross-agent doctrine presence),
and that each drift class is actually caught when injected into a fake PM tree.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add the check script directory to sys.path so we can import it.
_HERE = Path(__file__).parent
sys.path.insert(0, str(_HERE))

from check_doc_retrieval_layer_parity import (  # type: ignore[import-not-found]
    check_doctrine_cross_surface_parity,
    check_schema_generator_parity,
)

_PM_ROOT = _HERE.parents[1]

_DOCSPEC_STUB = """
from dataclasses import dataclass, field
from enum import Enum

DOC_TYPES = frozenset({{"plan", "codex-ssot", "cursor-rule"{extra_doc_type}}})


class Req(Enum):
    R = "required"
    O = "optional"


@dataclass(frozen=True)
class FieldSpec:
    name: str
    req: Req
    kind: str = "scalar"


UNIVERSAL_CORE = [FieldSpec("doc_type", Req.R), FieldSpec("title", Req.R)]

PER_TYPE = {{
    "plan": [FieldSpec("parent_epic", Req.R), FieldSpec("assigned_vm", Req.R)],
    "codex-ssot": [FieldSpec("authoritative_for", Req.R)],
    "cursor-rule": [],
}}
"""

_GEN_INDEX_STUB = """
_PER_TYPE_FACETS = {facets}
"""


def _write_fake_pm(tmp_path: Path, *, extra_doc_type: str = "", facets: str) -> Path:
    docs_dir = tmp_path / "scripts" / "docs"
    docs_dir.mkdir(parents=True)
    (docs_dir / "docspec.py").write_text(_DOCSPEC_STUB.format(extra_doc_type=extra_doc_type), encoding="utf-8")
    (docs_dir / "gen_doc_index.py").write_text(_GEN_INDEX_STUB.format(facets=facets), encoding="utf-8")
    return tmp_path


def test_live_corpus_schema_generator_parity_is_clean() -> None:
    """The real docspec.py <-> gen_doc_index.py must be in lockstep right now."""
    violations = check_schema_generator_parity(_PM_ROOT)
    assert not violations, "Live schema<->generator drift found:\n" + "\n".join(f"  - {v}" for v in violations)


def test_live_doctrine_cross_surface_parity_is_clean() -> None:
    """CLAUDE.md + AGENTS.md must both carry the DOC_INDEX grep-first doctrine right now."""
    violations = check_doctrine_cross_surface_parity(_PM_ROOT)
    assert not violations, "Doctrine missing from a surface:\n" + "\n".join(f"  - {v}" for v in violations)


def test_missing_doc_type_entry_is_caught(tmp_path: Path) -> None:
    """A doc_type with no _PER_TYPE_FACETS entry at all must be flagged."""
    pm = _write_fake_pm(
        tmp_path, extra_doc_type=', "issue"', facets='{"plan": ["parent_epic"], "codex-ssot": ["authoritative_for"]}'
    )
    violations = check_schema_generator_parity(pm)
    assert any("issue" in v and "missing an entry" in v for v in violations)


def test_stale_facet_name_is_caught(tmp_path: Path) -> None:
    """A facet name that isn't a real field for that doc_type must be flagged."""
    pm = _write_fake_pm(
        tmp_path,
        facets='{"plan": ["parent_epic", "no_such_field"], "codex-ssot": ["authoritative_for"], "cursor-rule": []}',
    )
    violations = check_schema_generator_parity(pm)
    assert any("no_such_field" in v for v in violations)


def test_stale_doc_type_key_is_caught(tmp_path: Path) -> None:
    """A _PER_TYPE_FACETS key naming a doc_type no longer in docspec.DOC_TYPES must be flagged."""
    pm = _write_fake_pm(
        tmp_path,
        facets=(
            '{"plan": ["parent_epic"], "codex-ssot": ["authoritative_for"], "cursor-rule": [], '
            '"retired-type": ["whatever"]}'
        ),
    )
    violations = check_schema_generator_parity(pm)
    assert any("retired-type" in v and "stale entry" in v for v in violations)


def test_missing_doctrine_mention_is_caught(tmp_path: Path) -> None:
    """A surface with zero DOC_INDEX mentions must be flagged; a clean pair must not."""
    (tmp_path / "cursor-configs").mkdir()
    (tmp_path / "cursor-configs" / "CLAUDE.md").write_text("grep DOC_INDEX.generated.md first", encoding="utf-8")
    (tmp_path / "AGENTS.md").write_text("no mention of the doctrine here", encoding="utf-8")

    violations = check_doctrine_cross_surface_parity(tmp_path)
    # Note: a violation's remedy text references "cursor-configs/CLAUDE.md" as the mirror-from
    # surface regardless of which surface failed, so "CLAUDE.md" alone is not a safe substring
    # to assert absence of — check the violation's OWN surface prefix instead.
    assert any(v.startswith("AGENTS.md") for v in violations)
    assert not any(v.startswith("cursor-configs/CLAUDE.md") for v in violations)


def test_missing_surface_file_is_caught(tmp_path: Path) -> None:
    """A surface that doesn't exist at all must be flagged, not silently skipped."""
    (tmp_path / "cursor-configs").mkdir()
    (tmp_path / "cursor-configs" / "CLAUDE.md").write_text("grep DOC_INDEX.generated.md first", encoding="utf-8")
    # AGENTS.md deliberately absent.

    violations = check_doctrine_cross_surface_parity(tmp_path)
    assert any("AGENTS.md" in v and "does not exist" in v for v in violations)
