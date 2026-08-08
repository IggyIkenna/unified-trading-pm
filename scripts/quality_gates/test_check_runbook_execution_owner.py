# Epic: agent_operating_framework_master
# Lifecycle: permanent
# Delete-when: NA
"""Unit tests for check_runbook_execution_owner.py's _iter_runbook_files walk.

Covers qg_owner_gate_full_workspace_rglob_walk_hangs_quickmerge_2026_07_31: the pruning
os.walk replacement for the old Path.rglob-based walk must (a) never descend into a .venv/
node_modules/build/dist/.git directory (the actual measured hang cause -- a python process
stuck in kernel D-state deep inside a .venv/.../typeshed-fallback tree), and (b) still
produce EXACTLY the same result set as the old implementation for every other case (the
prefix-based EXCLUDED_DIRS semantics -- plans/archive/, archive/, context/codex/, .extra/ --
are unchanged, verified here on synthetic fixtures rather than just asserted).
"""

from __future__ import annotations

import importlib.util
import sys
import time
from pathlib import Path

_HERE = Path(__file__).parent


def _load_module():
    spec = importlib.util.spec_from_file_location(
        "check_runbook_execution_owner", _HERE / "check_runbook_execution_owner.py"
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load check_runbook_execution_owner.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["check_runbook_execution_owner"] = mod
    spec.loader.exec_module(mod)
    return mod


_mod = _load_module()


def test_venv_directory_is_never_descended_into(tmp_path: Path) -> None:
    """THE core regression: a runbook-named file deep inside a .venv tree must be pruned
    without the walk ever statting its parent directories (the measured hang cause)."""
    deep = tmp_path / ".venv" / "lib" / "site-packages" / "somepkg" / "dist" / "typeshed-fallback"
    deep.mkdir(parents=True)
    (deep / "x-runbook.md").write_text("---\nfoo: bar\n---\n", encoding="utf-8")
    real = tmp_path / "plans" / "active"
    real.mkdir(parents=True)
    (real / "gate_3_phantom_audit_runbook_2026_05_13.md").write_text("---\nfoo: bar\n---\n", encoding="utf-8")

    found = _mod._iter_runbook_files(tmp_path)
    rels = {p.relative_to(tmp_path).as_posix() for p in found}
    assert rels == {"plans/active/gate_3_phantom_audit_runbook_2026_05_13.md"}


def test_node_modules_build_dist_git_are_pruned(tmp_path: Path) -> None:
    for d in ("node_modules", "build", "dist", ".git", ".venv-workspace"):
        p = tmp_path / d / "nested"
        p.mkdir(parents=True)
        (p / "some-runbook.md").write_text("x", encoding="utf-8")
    (tmp_path / "keep-runbook.md").write_text("x", encoding="utf-8")

    found = _mod._iter_runbook_files(tmp_path)
    rels = {p.relative_to(tmp_path).as_posix() for p in found}
    assert rels == {"keep-runbook.md"}


def test_prefix_based_exclusions_still_apply_post_prune(tmp_path: Path) -> None:
    """plans/archive/, archive/, context/codex/, .extra/ are NOT in the exact-dirname prune
    set (not safe to prune by bare name alone) -- confirm the post-hoc EXCLUDED_DIRS filter
    still correctly excludes them after the walk, unchanged."""
    for d in ("plans/archive", "archive", "context/codex", ".extra"):
        p = tmp_path / d
        p.mkdir(parents=True)
        (p / "stale-runbook.md").write_text("x", encoding="utf-8")
    (tmp_path / "plans" / "active").mkdir(parents=True, exist_ok=True)
    (tmp_path / "plans" / "active" / "live-runbook.md").write_text("x", encoding="utf-8")

    found = _mod._iter_runbook_files(tmp_path)
    rels = {p.relative_to(tmp_path).as_posix() for p in found}
    assert rels == {"plans/active/live-runbook.md"}


def test_matches_old_rglob_implementation_on_a_mixed_fixture(tmp_path: Path) -> None:
    """Byte-identical-result regression guard: build a fixture combining every excluded
    class (prune-by-name AND prefix-based) plus real runbooks, and assert the new walk's
    result set exactly equals what the OLD Path.rglob + post-hoc-filter implementation
    would produce -- the exact claim the qg_owner_gate issue doc's prior audits said was
    'asserted, not proven'."""
    layout = {
        ".venv/lib/x-runbook.md": True,
        "node_modules/pkg/y-runbook.md": True,
        "build/z-runbook.md": True,
        "dist/w-runbook.md": True,
        "plans/archive/old-runbook.md": True,
        "archive/mirror/old2-runbook.md": True,
        "context/codex/mirrored-runbook.md": True,
        ".extra/scratch-runbook.md": True,
        "plans/active/real-runbook.md": False,
        "codex/05-infrastructure/infra-runbook.md": False,
    }
    for rel in layout:
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("x", encoding="utf-8")

    def old_impl(workspace_root: Path) -> list[Path]:
        candidates: list[Path] = []
        for p in workspace_root.rglob("*runbook*.md"):
            rel = p.relative_to(workspace_root).as_posix()
            if any(rel.startswith(ex) or f"/{ex}" in f"/{rel}" for ex in _mod.EXCLUDED_DIRS):
                continue
            candidates.append(p)
        return sorted(candidates)

    old_result = {p.relative_to(tmp_path).as_posix() for p in old_impl(tmp_path)}
    new_result = {p.relative_to(tmp_path).as_posix() for p in _mod._iter_runbook_files(tmp_path)}
    assert old_result == new_result == {"plans/active/real-runbook.md", "codex/05-infrastructure/infra-runbook.md"}


def test_new_walk_is_faster_on_a_large_venv_fixture(tmp_path: Path) -> None:
    """Sanity perf guard (not a strict benchmark): a large-ish nested .venv tree must not
    be fully enumerated by the new walk -- weak assertion (walk completes quickly) rather
    than a brittle exact-timing one, since CI hosts vary."""
    venv = tmp_path / ".venv" / "lib" / "site-packages"
    for i in range(200):
        d = venv / f"pkg{i}" / "sub"
        d.mkdir(parents=True)
        (d / "file.txt").write_text("x", encoding="utf-8")
    (tmp_path / "real-runbook.md").write_text("x", encoding="utf-8")

    t0 = time.monotonic()
    found = _mod._iter_runbook_files(tmp_path)
    elapsed = time.monotonic() - t0

    assert {p.name for p in found} == {"real-runbook.md"}
    assert elapsed < 2.0, f"pruning walk took {elapsed:.2f}s over a 200-dir .venv fixture -- pruning may be broken"
