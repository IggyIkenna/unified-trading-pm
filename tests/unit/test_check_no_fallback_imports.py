"""Unit tests for scripts/quality_gates/check_no_fallback_imports.py (QG STEP 5.94).

Positive (fires on the fallback-import shim) + negative (clean code passes) +
baseline-ratchet semantics, per harden_grepable_rules_into_ci_gates_2026_06_02.md
Phase 3 success criteria ("positive + negative + baseline").
"""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path


def _load_module() -> types.ModuleType:
    repo_root = Path(__file__).resolve().parents[2]
    path = repo_root / "scripts" / "quality_gates" / "check_no_fallback_imports.py"
    spec = importlib.util.spec_from_file_location("check_no_fallback_imports", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    # Register BEFORE exec — the @dataclass machinery resolves string annotations
    # via sys.modules[cls.__module__] (fails with KW_ONLY lookup otherwise).
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


MOD = _load_module()


def _write(path: Path, source: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source, encoding="utf-8")
    return path


def _make_repo(ws: Path, repo: str) -> Path:
    repo_root = ws / repo
    (repo_root / ".git").mkdir(parents=True)
    return repo_root


# ── find_fallback_imports (positive) ─────────────────────────────────────────


class TestPositive:
    def test_try_except_importerror_flagged(self, tmp_path: Path) -> None:
        f = _write(
            tmp_path / "mod.py",
            "try:\n    import fancy\nexcept ImportError:\n    fancy = None\n",
        )
        hits = MOD.find_fallback_imports(f)
        assert len(hits) == 1
        assert hits[0][0] == 1
        assert "ImportError" in hits[0][1]

    def test_modulenotfounderror_and_tuple_flagged(self, tmp_path: Path) -> None:
        f = _write(
            tmp_path / "mod.py",
            "try:\n    from fancy import thing\nexcept (ModuleNotFoundError, OSError):\n    thing = None\n",
        )
        assert len(MOD.find_fallback_imports(f)) == 1

    def test_imports_only_body_with_broad_except_flagged(self, tmp_path: Path) -> None:
        f = _write(
            tmp_path / "mod.py",
            "try:\n    import fancy\nexcept Exception:\n    fancy = None\n",
        )
        hits = MOD.find_fallback_imports(f)
        assert len(hits) == 1
        assert "broad except" in hits[0][1]

    def test_imports_only_body_with_bare_except_flagged(self, tmp_path: Path) -> None:
        f = _write(
            tmp_path / "mod.py",
            "try:\n    import fancy\nexcept:\n    fancy = None\n",
        )
        assert len(MOD.find_fallback_imports(f)) == 1

    def test_reraise_wrapper_still_flagged(self, tmp_path: Path) -> None:
        # Even a loud re-raise wrapper is a shim to delete (import directly).
        f = _write(
            tmp_path / "mod.py",
            "try:\n    import fancy\nexcept ImportError as err:\n    raise RuntimeError('no fancy') from err\n",
        )
        assert len(MOD.find_fallback_imports(f)) == 1


# ── find_fallback_imports (negative) ─────────────────────────────────────────


class TestNegative:
    def test_plain_import_clean(self, tmp_path: Path) -> None:
        f = _write(tmp_path / "mod.py", "import json\nfrom pathlib import Path\n")
        assert MOD.find_fallback_imports(f) == []

    def test_mixed_body_broad_except_not_flagged(self, tmp_path: Path) -> None:
        # A runtime guard that happens to contain an import is NOT an import shim.
        f = _write(
            tmp_path / "mod.py",
            "try:\n    import json\n    value = json.loads('{}')\nexcept Exception:\n    value = {}\n",
        )
        assert MOD.find_fallback_imports(f) == []

    def test_try_without_imports_not_flagged(self, tmp_path: Path) -> None:
        f = _write(
            tmp_path / "mod.py",
            "try:\n    x = 1\nexcept ImportError:\n    x = 2\n",
        )
        assert MOD.find_fallback_imports(f) == []

    def test_docstring_mention_not_flagged(self, tmp_path: Path) -> None:
        f = _write(
            tmp_path / "mod.py",
            '"""Example:\n\ntry:\n    import fancy\nexcept ImportError:\n    fancy = None\n"""\nimport json\n',
        )
        assert MOD.find_fallback_imports(f) == []

    def test_noqa_marker_on_try_line_skipped(self, tmp_path: Path) -> None:
        f = _write(
            tmp_path / "mod.py",
            "try:  # noqa: fallback-import - documented optional ML extra\n"
            "    import fancy\nexcept ImportError:\n    fancy = None\n",
        )
        assert MOD.find_fallback_imports(f) == []

    def test_syntax_error_file_skipped(self, tmp_path: Path) -> None:
        f = _write(tmp_path / "mod.py", "def broken(:\n")
        assert MOD.find_fallback_imports(f) == []


# ── baseline-ratchet semantics via main() ────────────────────────────────────

_VIOLATION_SOURCE = "try:\n    import fancy\nexcept ImportError:\n    fancy = None\n"


class TestBaselineRatchet:
    def test_over_baseline_fails(self, tmp_path: Path) -> None:
        repo = _make_repo(tmp_path, "repo-a")
        _write(repo / "pkg" / "mod.py", _VIOLATION_SOURCE)
        baseline = tmp_path / "bl.yaml"
        rc = MOD.main(["--workspace-root", str(tmp_path), "--baseline-file", str(baseline)])
        assert rc == 1

    def test_at_baseline_passes(self, tmp_path: Path) -> None:
        repo = _make_repo(tmp_path, "repo-a")
        _write(repo / "pkg" / "mod.py", _VIOLATION_SOURCE)
        baseline = tmp_path / "bl.yaml"
        baseline.write_text("repos:\n  repo-a:\n    count: 1\n", encoding="utf-8")
        rc = MOD.main(["--workspace-root", str(tmp_path), "--baseline-file", str(baseline)])
        assert rc == 0

    def test_clean_repo_passes_at_zero_default(self, tmp_path: Path) -> None:
        repo = _make_repo(tmp_path, "repo-a")
        _write(repo / "pkg" / "mod.py", "import json\n")
        baseline = tmp_path / "bl.yaml"
        rc = MOD.main(["--workspace-root", str(tmp_path), "--baseline-file", str(baseline)])
        assert rc == 0

    def test_update_baseline_writes_then_passes(self, tmp_path: Path) -> None:
        repo = _make_repo(tmp_path, "repo-a")
        _write(repo / "pkg" / "mod.py", _VIOLATION_SOURCE)
        baseline = tmp_path / "bl.yaml"
        rc = MOD.main(["--workspace-root", str(tmp_path), "--baseline-file", str(baseline), "--update-baseline"])
        assert rc == 0
        assert "repo-a" in baseline.read_text(encoding="utf-8")
        rc = MOD.main(["--workspace-root", str(tmp_path), "--baseline-file", str(baseline)])
        assert rc == 0

    def test_update_baseline_clamps_down_never_up(self, tmp_path: Path) -> None:
        repo = _make_repo(tmp_path, "repo-a")
        _write(repo / "pkg" / "mod.py", _VIOLATION_SOURCE * 2)  # 2 sites
        baseline = tmp_path / "bl.yaml"
        baseline.write_text("repos:\n  repo-a:\n    count: 1\n", encoding="utf-8")
        rc = MOD.main(["--workspace-root", str(tmp_path), "--baseline-file", str(baseline), "--update-baseline"])
        assert rc == 0
        reloaded = MOD.load_baseline(baseline)
        assert reloaded.allowed("repo-a") == 1  # clamped to the prior baseline, not raised to 2

    def test_tests_dir_excluded(self, tmp_path: Path) -> None:
        repo = _make_repo(tmp_path, "repo-a")
        _write(repo / "tests" / "conftest.py", _VIOLATION_SOURCE)
        _write(repo / "pkg" / "test_helper.py", _VIOLATION_SOURCE)  # test_* prefix
        baseline = tmp_path / "bl.yaml"
        rc = MOD.main(["--workspace-root", str(tmp_path), "--baseline-file", str(baseline)])
        assert rc == 0

    def test_scope_mode_single_repo(self, tmp_path: Path) -> None:
        repo_a = _make_repo(tmp_path, "repo-a")
        _write(repo_a / "pkg" / "mod.py", _VIOLATION_SOURCE)
        repo_b = _make_repo(tmp_path, "repo-b")
        _write(repo_b / "pkg" / "mod.py", "import json\n")
        baseline = tmp_path / "bl.yaml"
        rc = MOD.main(["--workspace-root", str(tmp_path), "--scope", "repo-b", "--baseline-file", str(baseline)])
        assert rc == 0  # repo-a's violation is out of scope
        rc = MOD.main(["--workspace-root", str(tmp_path), "--scope", "repo-a", "--baseline-file", str(baseline)])
        assert rc == 1
