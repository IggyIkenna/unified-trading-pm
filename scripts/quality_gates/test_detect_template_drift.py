"""Unit tests for detect_template_drift.py."""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

import pytest
from detect_template_drift import (  # type: ignore[import-not-found]
    CANONICAL_SOURCE_LINE,
    CANONICAL_SSOT_COMMENT,
    _check_repo,
    run,
)

# ── Fixtures ──────────────────────────────────────────────────────────────────

CANONICAL_QG = textwrap.dedent(f"""\
    #!/usr/bin/env bash
    # Repo-specific settings only. Body: unified-trading-pm/scripts/quality-gates-base/base-service.sh
    {CANONICAL_SSOT_COMMENT}
    SERVICE_NAME="test-service"
    SOURCE_DIR="test_service"
    MIN_COVERAGE=70
    RUN_INTEGRATION=false
    PYTEST_WORKERS=${{PYTEST_WORKERS:-2}}
    LOCAL_DEPS=()
    MAX_DURATION=300
    WORKSPACE_ROOT="$(cd "$(git rev-parse --show-toplevel)/.." && pwd)"
    {CANONICAL_SOURCE_LINE}

    log_section "[5.X/6] UEI LIFECYCLE EVENT ENFORCEMENT (STARTED/STOPPED/FAILED)"
    if rg -q 'fastapi_uei_lifespan\\s*\\(' --type py "$SOURCE_DIR" 2>/dev/null; then
        log_success "UEI lifecycle: fastapi_uei_lifespan"
    elif rg -q 'ServiceBootstrap\\s*\\(' --type py "$SOURCE_DIR" 2>/dev/null; then
        log_success "UEI lifecycle: ServiceBootstrap"
    else
        for event in STARTED STOPPED FAILED; do
            run_timeout 30 rg "log_event.*\\"${{event}}\\"" "${{SOURCE_DIR}}" --type py -U -q \\
                || log_warn "Missing log_event"
        done
    fi
""")

OLD_LIFECYCLE_QG = textwrap.dedent(f"""\
    #!/usr/bin/env bash
    {CANONICAL_SSOT_COMMENT}
    SERVICE_NAME="old-service"
    SOURCE_DIR="old_service"
    MIN_COVERAGE=70
    RUN_INTEGRATION=false
    PYTEST_WORKERS=${{PYTEST_WORKERS:-2}}
    LOCAL_DEPS=()
    WORKSPACE_ROOT="$(cd "$(git rev-parse --show-toplevel)/.." && pwd)"
    {CANONICAL_SOURCE_LINE}

    log_section "[5.X/6] UEI LIFECYCLE EVENT ENFORCEMENT (STARTED/STOPPED/FAILED)"
    for event in STARTED STOPPED FAILED; do
        run_timeout 30 rg "log_event.*\\"${{event}}\\"" "${{SOURCE_DIR}}" --type py -q \\
            || log_warn "Missing log_event"
    done
""")


@pytest.fixture()
def tmp_repo(tmp_path: Path) -> Path:
    """Create a minimal workspace + repo structure under tmp_path."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    pm = workspace / "unified-trading-pm"
    pm.mkdir()
    return workspace


def _write_qg(workspace: Path, repo_name: str, content: str) -> Path:
    repo_dir = workspace / repo_name / "scripts"
    repo_dir.mkdir(parents=True, exist_ok=True)
    qg = repo_dir / "quality-gates.sh"
    qg.write_text(content)
    return qg


# ── Tests ─────────────────────────────────────────────────────────────────────


class TestCheckRepo:
    def test_canonical_file_is_clean(self, tmp_repo: Path) -> None:
        _write_qg(tmp_repo, "test-service", CANONICAL_QG)
        report = _check_repo("test-service", "service", tmp_repo)
        assert report.is_clean, f"Expected clean but got: {report.items}"

    def test_missing_file_warns(self, tmp_repo: Path) -> None:
        report = _check_repo("missing-service", "service", tmp_repo)
        assert report.has_warnings
        checks = [i.check for i in report.items]
        assert "missing-file" in checks

    def test_placeholder_service_name_errors(self, tmp_repo: Path) -> None:
        content = CANONICAL_QG.replace('SERVICE_NAME="test-service"', 'SERVICE_NAME="REPLACE_ME"')
        _write_qg(tmp_repo, "test-service", content)
        report = _check_repo("test-service", "service", tmp_repo)
        checks = [i.check for i in report.items]
        assert "placeholder-service-name" in checks
        assert report.has_errors

    def test_old_lifecycle_warns(self, tmp_repo: Path) -> None:
        _write_qg(tmp_repo, "old-service", OLD_LIFECYCLE_QG)
        report = _check_repo("old-service", "service", tmp_repo)
        checks = [i.check for i in report.items]
        assert "stale-lifecycle-block" in checks

    def test_missing_mandatory_var_errors(self, tmp_repo: Path) -> None:
        content = CANONICAL_QG.replace("MIN_COVERAGE=70\n", "")
        _write_qg(tmp_repo, "test-service", content)
        report = _check_repo("test-service", "service", tmp_repo)
        checks = [i.check for i in report.items]
        assert "missing-var-MIN_COVERAGE" in checks

    def test_noncanonical_source_path_warns(self, tmp_repo: Path) -> None:
        bad_source = 'source "${WORKSPACE_ROOT}/old-path/base-service.sh"'
        content = CANONICAL_QG.replace(CANONICAL_SOURCE_LINE, bad_source)
        _write_qg(tmp_repo, "test-service", content)
        report = _check_repo("test-service", "service", tmp_repo)
        checks = [i.check for i in report.items]
        assert "noncanonical-source-path" in checks

    def test_missing_ssot_comment_warns(self, tmp_repo: Path) -> None:
        content = CANONICAL_QG.replace(CANONICAL_SSOT_COMMENT + "\n", "")
        _write_qg(tmp_repo, "test-service", content)
        report = _check_repo("test-service", "service", tmp_repo)
        checks = [i.check for i in report.items]
        assert "ssot-comment" in checks


class TestRunWithManifest:
    def _write_manifest(self, workspace: Path, repos: list[dict[str, object]]) -> None:
        pm = workspace / "unified-trading-pm"
        pm.mkdir(exist_ok=True)
        manifest = pm / "workspace-manifest.json"
        # Manifest uses dict-of-dicts: {repo_name: {type: ..., ...}}
        repo_dict: dict[str, object] = {
            str(r.get("name", "")): {k: v for k, v in r.items() if k != "name"} for r in repos
        }
        manifest.write_text(json.dumps({"repositories": repo_dict}))

    def test_clean_repo_exit_0(self, tmp_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        self._write_manifest(tmp_repo, [{"name": "my-service", "type": "service"}])
        _write_qg(tmp_repo, "my-service", CANONICAL_QG)
        import detect_template_drift as mod  # type: ignore[import-not-found]

        monkeypatch.setattr(mod, "MANIFEST_PATH", tmp_repo / "unified-trading-pm" / "workspace-manifest.json")
        exit_code = run(workspace_root=tmp_repo)
        assert exit_code == 0

    def test_error_repo_exit_1(self, tmp_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        self._write_manifest(tmp_repo, [{"name": "bad-service", "type": "service"}])
        content = CANONICAL_QG.replace('SERVICE_NAME="test-service"', 'SERVICE_NAME="REPLACE_ME"')
        _write_qg(tmp_repo, "bad-service", content)
        import detect_template_drift as mod  # type: ignore[import-not-found]

        monkeypatch.setattr(mod, "MANIFEST_PATH", tmp_repo / "unified-trading-pm" / "workspace-manifest.json")
        exit_code = run(workspace_root=tmp_repo)
        assert exit_code == 1

    def test_ui_repos_are_skipped(self, tmp_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        self._write_manifest(tmp_repo, [{"name": "my-ui", "type": "ui"}])
        import detect_template_drift as mod  # type: ignore[import-not-found]

        monkeypatch.setattr(mod, "MANIFEST_PATH", tmp_repo / "unified-trading-pm" / "workspace-manifest.json")
        exit_code = run(workspace_root=tmp_repo)
        assert exit_code == 0

    def test_archived_repos_are_skipped(self, tmp_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        self._write_manifest(
            tmp_repo, [{"name": "archived-service", "type": "service", "archived_into": "other-service"}]
        )
        import detect_template_drift as mod  # type: ignore[import-not-found]

        monkeypatch.setattr(mod, "MANIFEST_PATH", tmp_repo / "unified-trading-pm" / "workspace-manifest.json")
        exit_code = run(workspace_root=tmp_repo)
        assert exit_code == 0
