"""Unit tests for scripts/quality_gates/check_no_new_urdi_refs.py.

Positive (fires on a NEW URDI ref) + negative (clean code / escape / tests
excluded passes) + baseline-ratchet semantics, mirroring
test_check_no_fallback_imports.py. Guard SSOT:
plans/active/codex_vs_repo_docs_ssot_audit_2026_06_01.md (finding 369).
"""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path


def _load_module() -> types.ModuleType:
    repo_root = Path(__file__).resolve().parents[2]
    path = repo_root / "scripts" / "quality_gates" / "check_no_new_urdi_refs.py"
    spec = importlib.util.spec_from_file_location("check_no_new_urdi_refs", path)
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


# ── find_urdi_refs (positive) ────────────────────────────────────────────────


class TestPositive:
    def test_urdi_line_flagged(self, tmp_path: Path) -> None:
        f = _write(tmp_path / "mod.py", "value = 1\nresult = URDI_provider.fetch()\n")
        hits = MOD.find_urdi_refs(f)
        assert len(hits) == 1
        assert hits[0][0] == 2
        assert "URDI" in hits[0][1]

    def test_multiple_urdi_lines_each_counted(self, tmp_path: Path) -> None:
        f = _write(tmp_path / "mod.py", "# URDI header\nfrom x import URDI_SUPPORTED_VENUES\nURDI = 1\n")
        assert len(MOD.find_urdi_refs(f)) == 3

    def test_urdi_in_comment_flagged(self, tmp_path: Path) -> None:
        # Substring match, exactly like `rg URDI` — comments count too.
        f = _write(tmp_path / "mod.py", "x = 1  # routes via the URDI factory\n")
        assert len(MOD.find_urdi_refs(f)) == 1


# ── find_urdi_refs (negative) ────────────────────────────────────────────────


class TestNegative:
    def test_clean_file_passes(self, tmp_path: Path) -> None:
        f = _write(tmp_path / "mod.py", "import json\nfrom pathlib import Path\n")
        assert MOD.find_urdi_refs(f) == []

    def test_qg_allow_escape_skipped(self, tmp_path: Path) -> None:
        f = _write(
            tmp_path / "mod.py",
            "value = URDI_provider.fetch()  # QG-allow: urdi-legacy - new adapter wiring\n",
        )
        assert MOD.find_urdi_refs(f) == []

    def test_case_sensitive_no_lowercase_match(self, tmp_path: Path) -> None:
        # The acronym is case-sensitive; `urdi` (module/var casing) must not trip
        # the count on its own unless it carries the uppercase token.
        f = _write(tmp_path / "mod.py", "from x import urdi_helper\nurdi = 1\n")
        assert MOD.find_urdi_refs(f) == []

    def test_missing_file_returns_empty(self, tmp_path: Path) -> None:
        assert MOD.find_urdi_refs(tmp_path / "nope.py") == []


# ── baseline-ratchet semantics via main() ────────────────────────────────────

_URDI_SOURCE = "result = URDI_provider.fetch()\n"


class TestBaselineRatchet:
    def test_over_baseline_fails(self, tmp_path: Path) -> None:
        repo = _make_repo(tmp_path, "instruments-service")
        _write(repo / "pkg" / "mod.py", _URDI_SOURCE)
        baseline = tmp_path / "bl.yaml"
        rc = MOD.main(
            ["--workspace-root", str(tmp_path), "--scope", "instruments-service", "--baseline-file", str(baseline)]
        )
        assert rc == 1

    def test_at_baseline_passes(self, tmp_path: Path) -> None:
        repo = _make_repo(tmp_path, "instruments-service")
        _write(repo / "pkg" / "mod.py", _URDI_SOURCE)
        baseline = tmp_path / "bl.yaml"
        baseline.write_text("repos:\n  instruments-service:\n    count: 1\n", encoding="utf-8")
        rc = MOD.main(
            ["--workspace-root", str(tmp_path), "--scope", "instruments-service", "--baseline-file", str(baseline)]
        )
        assert rc == 0

    def test_clean_repo_passes_at_zero_default(self, tmp_path: Path) -> None:
        repo = _make_repo(tmp_path, "instruments-service")
        _write(repo / "pkg" / "mod.py", "import json\n")
        baseline = tmp_path / "bl.yaml"
        rc = MOD.main(
            ["--workspace-root", str(tmp_path), "--scope", "instruments-service", "--baseline-file", str(baseline)]
        )
        assert rc == 0

    def test_update_baseline_writes_then_passes(self, tmp_path: Path) -> None:
        repo = _make_repo(tmp_path, "instruments-service")
        _write(repo / "pkg" / "mod.py", _URDI_SOURCE)
        baseline = tmp_path / "bl.yaml"
        rc = MOD.main(
            [
                "--workspace-root",
                str(tmp_path),
                "--scope",
                "instruments-service",
                "--baseline-file",
                str(baseline),
                "--update-baseline",
            ]
        )
        assert rc == 0
        assert "instruments-service" in baseline.read_text(encoding="utf-8")
        rc = MOD.main(
            ["--workspace-root", str(tmp_path), "--scope", "instruments-service", "--baseline-file", str(baseline)]
        )
        assert rc == 0

    def test_update_baseline_clamps_down_never_up(self, tmp_path: Path) -> None:
        repo = _make_repo(tmp_path, "instruments-service")
        _write(repo / "pkg" / "mod.py", _URDI_SOURCE * 2)  # 2 URDI lines
        baseline = tmp_path / "bl.yaml"
        baseline.write_text("repos:\n  instruments-service:\n    count: 1\n", encoding="utf-8")
        rc = MOD.main(
            [
                "--workspace-root",
                str(tmp_path),
                "--scope",
                "instruments-service",
                "--baseline-file",
                str(baseline),
                "--update-baseline",
            ]
        )
        assert rc == 0
        reloaded = MOD.load_baseline(baseline)
        assert reloaded.allowed("instruments-service") == 1  # clamped to prior, not raised to 2

    def test_tests_dir_excluded(self, tmp_path: Path) -> None:
        repo = _make_repo(tmp_path, "instruments-service")
        _write(repo / "tests" / "conftest.py", _URDI_SOURCE)
        _write(repo / "pkg" / "test_helper.py", _URDI_SOURCE)  # test_* prefix
        baseline = tmp_path / "bl.yaml"
        rc = MOD.main(
            ["--workspace-root", str(tmp_path), "--scope", "instruments-service", "--baseline-file", str(baseline)]
        )
        assert rc == 0

    def test_scope_confines_to_named_repo(self, tmp_path: Path) -> None:
        repo_a = _make_repo(tmp_path, "instruments-service")
        _write(repo_a / "pkg" / "mod.py", _URDI_SOURCE)
        repo_b = _make_repo(tmp_path, "execution-service")
        _write(repo_b / "pkg" / "mod.py", _URDI_SOURCE)  # legit URDI ref elsewhere
        baseline = tmp_path / "bl.yaml"
        # execution-service is out of the IS-scoped guard → not checked at all here.
        rc = MOD.main(
            ["--workspace-root", str(tmp_path), "--scope", "execution-service", "--baseline-file", str(baseline)]
        )
        assert rc == 1  # (only because we scoped it; the real wiring never scopes exec-service)
        rc = MOD.main(
            ["--workspace-root", str(tmp_path), "--scope", "instruments-service", "--baseline-file", str(baseline)]
        )
        assert rc == 1
