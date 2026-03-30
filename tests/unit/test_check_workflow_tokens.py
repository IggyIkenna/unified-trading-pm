"""Unit tests for scripts/validation/check-workflow-tokens.py."""

from __future__ import annotations

import importlib.util
import types
from pathlib import Path


def _load_module() -> types.ModuleType:
    repo_root = Path(__file__).resolve().parents[2]
    path = repo_root / "scripts" / "validation" / "check-workflow-tokens.py"
    spec = importlib.util.spec_from_file_location("check_workflow_tokens", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


MOD = _load_module()


# ── Tests: _find_violations ───────────────────────────────────────────────


class TestFindViolations:
    def test_no_violations_in_clean_workflow(self, tmp_path: Path) -> None:
        wf = tmp_path / "clean.yml"
        wf.write_text(
            "name: CI\n"
            "on: push\n"
            "jobs:\n"
            "  build:\n"
            "    runs-on: ubuntu-latest\n"
            "    steps:\n"
            "      - uses: actions/checkout@v4\n"
        )
        violations = MOD._find_violations(wf)
        assert violations == []

    def test_detects_cross_repo_checkout_with_github_token(self, tmp_path: Path) -> None:
        wf = tmp_path / "bad.yml"
        wf.write_text(
            "steps:\n"
            "  - uses: actions/checkout@v4\n"
            "    with:\n"
            "      repository: IggyIkenna/other-repo\n"
            "      token: ${{ secrets.GITHUB_TOKEN }}\n"
        )
        violations = MOD._find_violations(wf)
        assert len(violations) == 1
        assert "GITHUB_TOKEN" in violations[0]

    def test_no_violation_when_using_gh_pat(self, tmp_path: Path) -> None:
        wf = tmp_path / "good.yml"
        wf.write_text(
            "steps:\n"
            "  - uses: actions/checkout@v4\n"
            "    with:\n"
            "      repository: IggyIkenna/other-repo\n"
            "      token: ${{ secrets.GH_PAT }}\n"
        )
        violations = MOD._find_violations(wf)
        assert violations == []

    def test_no_violation_same_repo(self, tmp_path: Path) -> None:
        wf = tmp_path / "same-repo.yml"
        wf.write_text("steps:\n  - uses: actions/checkout@v4\n    with:\n      token: ${{ secrets.GITHUB_TOKEN }}\n")
        violations = MOD._find_violations(wf)
        assert violations == []

    def test_comment_lines_skipped(self, tmp_path: Path) -> None:
        wf = tmp_path / "comments.yml"
        wf.write_text(
            "steps:\n"
            "  - uses: actions/checkout@v4\n"
            "    with:\n"
            "      # repository: IggyIkenna/other-repo\n"
            "      token: ${{ secrets.GITHUB_TOKEN }}\n"
        )
        violations = MOD._find_violations(wf)
        assert violations == []

    def test_unreadable_file(self, tmp_path: Path) -> None:
        wf = tmp_path / "nonexistent.yml"
        violations = MOD._find_violations(wf)
        assert violations == []

    def test_eof_while_in_with_block(self, tmp_path: Path) -> None:
        wf = tmp_path / "eof.yml"
        wf.write_text(
            "steps:\n"
            "  - uses: actions/checkout@v4\n"
            "    with:\n"
            "      repository: IggyIkenna/other-repo\n"
            "      token: ${{ secrets.GITHUB_TOKEN }}\n"
        )
        violations = MOD._find_violations(wf)
        assert len(violations) == 1

    def test_dynamic_repo_ref(self, tmp_path: Path) -> None:
        wf = tmp_path / "dynamic.yml"
        wf.write_text(
            "steps:\n"
            "  - uses: actions/checkout@v4\n"
            "    with:\n"
            "      repository: ${{ inputs.repo }}\n"
            "      token: ${{ secrets.GITHUB_TOKEN }}\n"
            "  - run: echo done\n"
        )
        violations = MOD._find_violations(wf)
        assert len(violations) == 1


# ── Tests: check_dir ─────────────────────────────────────────────────────


class TestCheckDir:
    def test_empty_dir(self, tmp_path: Path) -> None:
        wf_dir = tmp_path / ".github" / "workflows"
        wf_dir.mkdir(parents=True)
        total = MOD.check_dir(wf_dir)
        assert total == 0

    def test_nonexistent_dir(self, tmp_path: Path) -> None:
        wf_dir = tmp_path / "no-such-dir"
        total = MOD.check_dir(wf_dir)
        assert total == 0

    def test_dir_with_violations(self, tmp_path: Path) -> None:
        wf_dir = tmp_path / ".github" / "workflows"
        wf_dir.mkdir(parents=True)
        (wf_dir / "bad.yml").write_text(
            "steps:\n"
            "  - uses: actions/checkout@v4\n"
            "    with:\n"
            "      repository: IggyIkenna/other-repo\n"
            "      token: ${{ secrets.GITHUB_TOKEN }}\n"
            "  - run: echo done\n"
        )
        total = MOD.check_dir(wf_dir)
        assert total >= 1
