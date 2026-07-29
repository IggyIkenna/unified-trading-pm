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

from check_repo_docs_ssot import _iter_repo_docs, find_violations  # type: ignore[import-not-found]

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
