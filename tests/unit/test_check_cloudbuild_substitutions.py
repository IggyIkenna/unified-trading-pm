"""Unit tests for scripts/quality_gates/check_cloudbuild_substitutions.py (QG STEP 5.19).

Regression fixtures for the 2026-06-10 silent-rejection incident class
(plans/active/issues/cloudbuild_silent_failures_no_alerting_no_validation_2026_06_10.md
Gap 3): unescaped $VAR flagged · $$-escaped clean · Cloud Build builtins clean ·
_-prefixed user substitutions clean · bash COMMENT-line dollars inside step args
flagged (Cloud Build scans the whole arg string, comments included).
"""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path


def _load_module() -> types.ModuleType:
    repo_root = Path(__file__).resolve().parents[2]
    path = repo_root / "scripts" / "quality_gates" / "check_cloudbuild_substitutions.py"
    spec = importlib.util.spec_from_file_location("check_cloudbuild_substitutions", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    # Register BEFORE exec — the @dataclass machinery resolves string annotations
    # via sys.modules[cls.__module__].
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


MOD = _load_module()


def _cloudbuild(bash_block: str, step_id: str = "build") -> str:
    indented = "\n".join(f"        {line}" for line in bash_block.splitlines())
    return (
        "steps:\n"
        '  - name: "gcr.io/cloud-builders/git"\n'
        f'    id: "{step_id}"\n'
        '    entrypoint: "bash"\n'
        "    args:\n"
        '      - "-c"\n'
        "      - |\n"
        f"{indented}\n"
    )


class TestFlagged:
    def test_unescaped_var_flagged(self) -> None:
        violations = MOD.scan_cloudbuild_text(_cloudbuild('PIN="abc"\necho "$PIN"'), label="x.yaml")
        assert [(v.step_id, v.varname) for v in violations] == [("build", "PIN")]

    def test_unescaped_braced_var_flagged(self) -> None:
        violations = MOD.scan_cloudbuild_text(_cloudbuild('echo "${DIGEST}"'), label="x.yaml")
        assert [(v.step_id, v.varname) for v in violations] == [("build", "DIGEST")]

    def test_comment_line_dollars_inside_args_flagged(self) -> None:
        # The SECOND rejection class from the incident: a bash comment inside the
        # arg string mentioning a shell var with a single dollar. Cloud Build
        # scans the whole step string, comments included.
        violations = MOD.scan_cloudbuild_text(
            _cloudbuild("# pre-pull pinned by $PIN to avoid a stale layer\necho ok"), label="x.yaml"
        )
        assert [(v.step_id, v.varname) for v in violations] == [("build", "PIN")]

    def test_bare_command_substitution_is_clean(self) -> None:
        # GCB only substitutes word-keys; bare `$(cmd)` passes through to bash as a literal
        # (verified live 2026-06-10: 17 fleet configs carry it and build fine) — NOT flagged.
        violations = MOD.scan_cloudbuild_text(_cloudbuild("VERSION=$(grep version pyproject.toml)"), label="x.yaml")
        assert violations == []

    def test_script_and_env_values_scanned(self) -> None:
        text = (
            "steps:\n"
            '  - name: "bash"\n'
            '    id: "scripted"\n'
            '    script: "echo $LOOSE"\n'
            "    env:\n"
            '      - "FOO=$BARVALUE"\n'
        )
        violations = MOD.scan_cloudbuild_text(text, label="x.yaml")
        assert {(v.step_id, v.varname) for v in violations} == {("scripted", "LOOSE"), ("scripted", "BARVALUE")}

    def test_main_exits_1_and_renders_file_step_var(self, tmp_path: Path, capsys: object) -> None:
        cb = tmp_path / "cloudbuild.yaml"
        _ = cb.write_text(_cloudbuild('echo "$PIN"'), encoding="utf-8")
        assert MOD.main([str(cb)]) == 1


class TestClean:
    def test_dollar_dollar_escapes_clean(self) -> None:
        block = 'VERSION=$$(grep version pyproject.toml)\necho "$$VERSION"\n# comment about $$PIN too'
        assert MOD.scan_cloudbuild_text(_cloudbuild(block), label="x.yaml") == []

    def test_builtins_clean(self) -> None:
        block = 'echo "$PROJECT_ID ${SHORT_SHA} $COMMIT_SHA ${BRANCH_NAME} $TRIGGER_NAME"'
        assert MOD.scan_cloudbuild_text(_cloudbuild(block), label="x.yaml") == []

    def test_underscore_user_substitutions_clean(self) -> None:
        block = 'docker build -t "$_REGISTRY_REPO/${_SERVICE_NAME}:$SHORT_SHA" .'
        assert MOD.scan_cloudbuild_text(_cloudbuild(block), label="x.yaml") == []

    def test_yaml_file_comments_not_scanned(self) -> None:
        # YAML `#` comments OUTSIDE step strings are stripped by the parser —
        # Cloud Build never sees them, so neither do we.
        text = "# header mentions $VERSION freely\n" + _cloudbuild("echo ok")
        assert MOD.scan_cloudbuild_text(text, label="x.yaml") == []

    def test_main_exits_0_on_clean_file(self, tmp_path: Path) -> None:
        cb = tmp_path / "cloudbuild.yaml"
        _ = cb.write_text(_cloudbuild('echo "$PROJECT_ID $$SHELLVAR $_USER_SUB"'), encoding="utf-8")
        assert MOD.main([str(cb)]) == 0
