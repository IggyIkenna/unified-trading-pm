# Epic: plan_hygiene_master
# Lifecycle: permanent
# Delete-when: NA
"""Unit tests for check_repo_docs_ssot.py.

Verifies the live corpus is clean against its seeded baseline (via the CLI, matching how the QG
gate actually invokes it), and that each drift class (archived-mirror ref, hardcoded resolver-owned
literal) is caught — or correctly excluded (PM repo, vendored/archive trees) — on a synthetic
workspace tree.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_HERE = Path(__file__).parent
sys.path.insert(0, str(_HERE))

from check_repo_docs_ssot import (  # type: ignore[import-not-found]
    _build_codex_table_index,
    _extract_tables,
    _iter_repo_docs,
    find_violations,
)

_PM_ROOT = _HERE.parents[1]
_WORKSPACE_ROOT = _PM_ROOT.parent


def test_live_corpus_has_zero_new_drift() -> None:
    """The real corpus must pass its own ratchet right now (baseline absorbs pre-existing debt)."""
    result = subprocess.run(
        [
            sys.executable,
            str(_HERE / "check_repo_docs_ssot.py"),
            "--workspace-root",
            str(_WORKSPACE_ROOT),
            "--quiet",
        ],
        cwd=_PM_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, f"NEW codex-SSOT drift found:\n{result.stdout}\n{result.stderr}"


def _mk_repo_doc(root: Path, repo: str, rel: str, body: str) -> Path:
    doc = root / repo / rel
    doc.parent.mkdir(parents=True, exist_ok=True)
    doc.write_text(body, encoding="utf-8")
    return doc


def test_mirror_ref_is_flagged(tmp_path: Path) -> None:
    doc = _mk_repo_doc(
        tmp_path,
        "execution-service",
        "docs/GCS_PATHS.md",
        "See `unified-trading-codex/02-data/partitioning.md` for the layout.\n",
    )
    violations = find_violations([doc], tmp_path)
    assert violations == {"execution-service/docs/GCS_PATHS.md": [(1, "mirror-ref", "unified-trading-codex/")]}


def test_hardcoded_project_id_is_flagged(tmp_path: Path) -> None:
    doc = _mk_repo_doc(
        tmp_path,
        "deployment-service",
        "docs/DEPLOYMENT_GUIDE.md",
        "Deploy to project central-element-323112.\n",
    )
    violations = find_violations([doc], tmp_path)
    assert violations == {
        "deployment-service/docs/DEPLOYMENT_GUIDE.md": [(1, "hardcoded-literal", "central-element-323112")]
    }


def test_both_rules_on_one_line(tmp_path: Path) -> None:
    doc = _mk_repo_doc(
        tmp_path,
        "market-tick-data-service",
        "docs/ARCHITECTURE.md",
        "old unified-trading-codex/ ref for central-element-323112\n",
    )
    violations = find_violations([doc], tmp_path)
    hits = violations["market-tick-data-service/docs/ARCHITECTURE.md"]
    assert (1, "mirror-ref", "unified-trading-codex/") in hits
    assert (1, "hardcoded-literal", "central-element-323112") in hits


def test_placeholder_forms_are_clean(tmp_path: Path) -> None:
    doc = _mk_repo_doc(
        tmp_path,
        "instruments-service",
        "docs/GCS_PATHS.md",
        "Bucket `gs://instruments-store-cefi-prd-{project_id}`; SSOT "
        "[layout](../../unified-trading-pm/codex/02-data/partitioning.md).\n",
    )
    violations = find_violations([doc], tmp_path)
    assert violations == {}


def test_pm_repo_is_excluded_from_walk(tmp_path: Path) -> None:
    """unified-trading-pm IS the SSOT, not an audit target — its docs must never be scanned."""
    _mk_repo_doc(tmp_path, "unified-trading-pm", "docs/workspace-setup.md", "unified-trading-codex/ mirror\n")
    _mk_repo_doc(tmp_path, "execution-service", "README.md", "clean\n")
    walked = _iter_repo_docs(tmp_path)
    rels = {p.relative_to(tmp_path).as_posix() for p in walked}
    assert "execution-service/README.md" in rels
    assert not any(r.startswith("unified-trading-pm/") for r in rels)


def test_archive_and_vendored_trees_are_excluded(tmp_path: Path) -> None:
    _mk_repo_doc(tmp_path, "execution-service", "docs/archive/OLD.md", "unified-trading-codex/ mirror\n")
    _mk_repo_doc(tmp_path, "execution-service", "docs/.cursor/rules/x.md", "central-element-323112\n")
    _mk_repo_doc(tmp_path, "execution-service", "docs/GCS_PATHS.md", "clean\n")
    walked = _iter_repo_docs(tmp_path)
    rels = {p.relative_to(tmp_path).as_posix() for p in walked}
    assert "execution-service/docs/GCS_PATHS.md" in rels
    assert "execution-service/docs/archive/OLD.md" not in rels
    assert "execution-service/docs/.cursor/rules/x.md" not in rels


# --- table-duplication rule (Phase 5 follow-up, codex_vs_repo_docs_ssot_audit_2026_06_01.md) ---

_BIG_TABLE_MD = (
    "| Repo doc               | Link to codex SSOT (do NOT duplicate)                | Keep in repo doc    |\n"
    "| ----------------------- | ------------------------------------------------------ | --------------------- |\n"
    "| `README.md`            | none — pads the fixture past the significance floor  | purpose/quickstart  |\n"
    "| `docs/ARCHITECTURE.md` | cross-cutting patterns live in the codex arch doc set | this repo's modules |\n"
)


def test_extract_tables_excludes_separator_row() -> None:
    tables = _extract_tables(_BIG_TABLE_MD)
    assert len(tables) == 1
    start_line, rows = tables[0]
    assert start_line == 1
    assert len(rows) == 3  # header + 2 data rows; the `---|---|---` separator is dropped
    assert rows[0][0] == "Repo doc"
    assert rows[1][0] == "`README.md`"


def test_table_duplication_flagged_for_verbatim_codex_table_copy(tmp_path: Path) -> None:
    codex_doc = tmp_path / "codex" / "06-coding-standards" / "documentation-standards.md"
    codex_doc.parent.mkdir(parents=True, exist_ok=True)
    codex_doc.write_text(f"## S5.11\n\n{_BIG_TABLE_MD}", encoding="utf-8")
    codex_index = _build_codex_table_index(tmp_path)
    assert codex_index  # the fixture table clears the significance floor

    doc = _mk_repo_doc(tmp_path, "deployment-service", "docs/ARCHITECTURE.md", f"# Architecture\n\n{_BIG_TABLE_MD}")
    violations = find_violations([doc], tmp_path, codex_index)
    hits = violations["deployment-service/docs/ARCHITECTURE.md"]
    assert any(rule == "table-duplication" for _lineno, rule, _literal in hits)


def test_table_duplication_not_flagged_without_codex_index(tmp_path: Path) -> None:
    """Backward-compat: callers that don't pass codex_index (existing tests/tools) see no table rule."""
    doc = _mk_repo_doc(tmp_path, "deployment-service", "docs/ARCHITECTURE.md", f"# Architecture\n\n{_BIG_TABLE_MD}")
    violations = find_violations([doc], tmp_path)
    assert violations == {}


def test_table_duplication_not_flagged_below_significance_floor(tmp_path: Path) -> None:
    """A trivial 2-row (header + 1 data row) table is common-idiom shaped — excluded by the floor."""
    small_table = "| Level | Behaviour |\n| --- | --- |\n| low | ignore |\n"
    codex_doc = tmp_path / "codex" / "06-coding-standards" / "tiny.md"
    codex_doc.parent.mkdir(parents=True, exist_ok=True)
    codex_doc.write_text(small_table, encoding="utf-8")
    codex_index = _build_codex_table_index(tmp_path)
    assert not codex_index  # below _MIN_TABLE_ROWS / _MIN_TABLE_CHARS, never indexed

    doc = _mk_repo_doc(tmp_path, "deployment-service", "docs/ARCHITECTURE.md", small_table)
    violations = find_violations([doc], tmp_path, codex_index)
    assert violations == {}


def test_table_duplication_not_flagged_on_different_content(tmp_path: Path) -> None:
    codex_doc = tmp_path / "codex" / "06-coding-standards" / "documentation-standards.md"
    codex_doc.parent.mkdir(parents=True, exist_ok=True)
    codex_doc.write_text(_BIG_TABLE_MD, encoding="utf-8")
    codex_index = _build_codex_table_index(tmp_path)

    different_table = _BIG_TABLE_MD.replace("ARCHITECTURE.md", "CONFIGURATION.md").replace(
        "modules", "config-fields-and-defaults"
    )
    doc = _mk_repo_doc(tmp_path, "deployment-service", "docs/CONFIGURATION.md", different_table)
    violations = find_violations([doc], tmp_path, codex_index)
    assert violations == {}


def test_codex_archived_dirs_excluded_from_table_index(tmp_path: Path) -> None:
    archived_doc = tmp_path / "codex" / "10-audit" / "_archive" / "old.md"
    archived_doc.parent.mkdir(parents=True, exist_ok=True)
    archived_doc.write_text(_BIG_TABLE_MD, encoding="utf-8")
    codex_index = _build_codex_table_index(tmp_path)
    assert codex_index == {}
