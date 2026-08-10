"""Unit tests for scripts/validation/check-template-yaml.py (parser; no prettier).

The prettier simulation (resolve_prettier / subprocess) hits the local toolchain
and is exercised by the rollout pre-flight + the manual scratch verification, not
here. These tests pin the substitution + YAML-parse lint core — the part that
catches the prettier-mangled placeholder class regardless of prettier's presence.
"""

from __future__ import annotations

import importlib.util
import types
from pathlib import Path


def _load_module() -> types.ModuleType:
    repo_root = Path(__file__).resolve().parents[2]
    path = repo_root / "scripts" / "validation" / "check-template-yaml.py"
    spec = importlib.util.spec_from_file_location("check_template_yaml", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


MOD = _load_module()


class TestLintYaml:
    def test_valid_flat_workflow_parses(self) -> None:
        body = "name: ci\non:\n  push:\n    branches: [main]\n"
        assert MOD.lint_yaml(body) == []

    def test_github_expression_scalar_parses(self) -> None:
        body = "concurrency:\n  group: quality-gates-v2-${{ github.ref }}\n"
        assert MOD.lint_yaml(body) == []

    def test_mangled_placeholder_is_caught(self) -> None:
        body = "jobs:\n  a:\n    runs-on: { { RUNS_ON } }\n"
        assert MOD.lint_yaml(body) != []

    def test_bare_placeholder_is_caught(self) -> None:
        body = "jobs:\n  a:\n    runs-on: {{PLACEHOLDER}}\n"
        assert MOD.lint_yaml(body) != []


class TestSubstituteTmpl:
    def test_all_known_tokens_are_replaced(self) -> None:
        text = (
            "{{DEP_REPOS}} __REPO_NAME__ __SOURCE_DIR__ __VERSION_SOURCE__ "
            "{{CI_TRIGGER_BRANCH}} {{QG_RUNNER_LABELS}} __RUNS_ON__"
        )
        out = MOD.substitute_tmpl(text)
        assert "{{" not in out
        assert "__RUNS_ON__" not in out

    def test_unknown_token_survives_substitution(self) -> None:
        assert "{{MYSTERY}}" in MOD.substitute_tmpl("{{MYSTERY}}")

    def test_fully_substituted_tmpl_parses(self) -> None:
        # Mirrors the placeholder surface of the real quality-gates-v2.yml.tmpl.
        body = (
            "name: qg\n"
            "on:\n"
            "  push:\n"
            "    branches: [{{CI_TRIGGER_BRANCH}}]\n"
            "jobs:\n"
            "  qg:\n"
            "    name: Quality Gates (__REPO_NAME__)\n"
            "    runs-on: __RUNS_ON__\n"
            "    uses: IggyIkenna/unified-trading-ci/.github/workflows/python-quality-gates-v2.yml@main\n"
            "    with:\n"
            '      dep_repos: "{{DEP_REPOS}}"\n'
            "      self_hosted_runner_labels: '{{QG_RUNNER_LABELS}}'\n"
        )
        assert MOD.lint_yaml(MOD.substitute_tmpl(body)) == []

    def test_unknown_placeholder_in_tmpl_is_caught(self) -> None:
        body = "jobs:\n  a:\n    runs-on: {{NOT_A_REAL_TOKEN}}\n"
        # Unknown token is not in the substitution set -> survives -> caught.
        assert MOD.lint_yaml(MOD.substitute_tmpl(body)) != []


class TestLintTemplateFileNoPrettier:
    def test_flat_valid(self, tmp_path: Path) -> None:
        f = tmp_path / "wf.yml"
        f.write_text("name: ci\non: [push]\n", encoding="utf-8")
        assert MOD.lint_template_file(f, None) == []

    def test_flat_mangled_is_reported(self, tmp_path: Path) -> None:
        f = tmp_path / "wf.yml"
        f.write_text("jobs:\n  a:\n    runs-on: { { RUNS_ON } }\n", encoding="utf-8")
        problems = MOD.lint_template_file(f, None)
        assert len(problems) == 1
        assert "wf.yml" in problems[0]

    def test_tmpl_valid_via_substitution(self, tmp_path: Path) -> None:
        f = tmp_path / "qg.yml.tmpl"
        f.write_text(
            'jobs:\n  a:\n    runs-on: __RUNS_ON__\n    with:\n      dep_repos: "{{DEP_REPOS}}"\n',
            encoding="utf-8",
        )
        assert MOD.lint_template_file(f, None) == []

    def test_tmpl_with_unknown_token_is_reported(self, tmp_path: Path) -> None:
        f = tmp_path / "qg.yml.tmpl"
        f.write_text("jobs:\n  a:\n    runs-on: {{BROKEN}}\n", encoding="utf-8")
        assert MOD.lint_template_file(f, None) != []
