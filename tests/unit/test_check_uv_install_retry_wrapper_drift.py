"""Unit tests for scripts/quality_gates/check_uv_install_retry_wrapper_drift.py.

Positive (an un-wrapped `RUN --mount=type=secret,id=gar_token` install layer is flagged) +
negative (an already-wrapped layer, a layer with no gar_token mount, and the two documented
exempt repos are NOT flagged) + the always-warn-only (exit 0) contract, per
plans/active/issues/cloud_build_unified_api_contracts_publish_ordering_race_2026_07_29.md's
retry-wrapper-drift-checker follow-up todo.
"""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

WRAPPED = (
    "FROM base\n"
    "RUN --mount=type=secret,id=gar_token \\\n"
    '    UV_EXTRA_INDEX_URL="https://oauth2accesstoken:$(cat /run/secrets/gar_token)@example/" \\\n'
    '    sh -c \'i=1; until uv pip install --system --no-sources -e .; do [ "$i" -ge 3 ] && '
    '{ echo "uv pip install failed after 3 attempts" >&2; exit 1; }; w=$((15 * i)); echo "uv pip install failed '
    '(attempt $i/3) -- retrying in ${w}s"; sleep "$w"; i=$((i + 1)); done\'\n'
)

UNWRAPPED = """\
FROM base
RUN --mount=type=secret,id=gar_token \\
    UV_EXTRA_INDEX_URL="https://oauth2accesstoken:$(cat /run/secrets/gar_token)@example/" \\
    uv pip install --system --no-sources -e .
"""

NO_MOUNT = """\
FROM base
RUN uv pip install --system --no-sources -e .
"""

NOT_NO_SOURCES = """\
FROM base
RUN --mount=type=secret,id=gar_token \\
    uv pip install --system --no-cache-dir keyrings.google-artifactregistry-auth
"""


def _load_module() -> types.ModuleType:
    repo_root = Path(__file__).resolve().parents[2]
    path = repo_root / "scripts" / "quality_gates" / "check_uv_install_retry_wrapper_drift.py"
    spec = importlib.util.spec_from_file_location("check_uv_install_retry_wrapper_drift", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


MOD = _load_module()


def _make_repo(workspace_root: Path, repo_name: str, dockerfile_content: str) -> Path:
    repo_dir = workspace_root / repo_name
    repo_dir.mkdir(parents=True, exist_ok=True)
    (repo_dir / "Dockerfile").write_text(dockerfile_content, encoding="utf-8")
    return repo_dir


class TestScanDockerfilePositive:
    def test_unwrapped_layer_flagged(self, tmp_path: Path) -> None:
        dockerfile = tmp_path / "Dockerfile"
        dockerfile.write_text(UNWRAPPED, encoding="utf-8")
        findings = MOD.scan_dockerfile(dockerfile)
        assert len(findings) == 1
        assert findings[0].line_no == 2  # the `RUN --mount=...` line
        assert "RUN --mount=type=secret,id=gar_token" in findings[0].snippet


class TestScanDockerfileNegative:
    def test_already_wrapped_not_flagged(self, tmp_path: Path) -> None:
        dockerfile = tmp_path / "Dockerfile"
        dockerfile.write_text(WRAPPED, encoding="utf-8")
        assert MOD.scan_dockerfile(dockerfile) == []

    def test_no_gar_token_mount_not_flagged(self, tmp_path: Path) -> None:
        dockerfile = tmp_path / "Dockerfile"
        dockerfile.write_text(NO_MOUNT, encoding="utf-8")
        assert MOD.scan_dockerfile(dockerfile) == []

    def test_gar_token_without_no_sources_not_flagged(self, tmp_path: Path) -> None:
        dockerfile = tmp_path / "Dockerfile"
        dockerfile.write_text(NOT_NO_SOURCES, encoding="utf-8")
        assert MOD.scan_dockerfile(dockerfile) == []

    def test_missing_dockerfile_returns_empty(self, tmp_path: Path) -> None:
        assert MOD.scan_dockerfile(tmp_path / "does-not-exist" / "Dockerfile") == []


class TestScanFleet:
    def test_aggregates_drift_across_repos(self, tmp_path: Path) -> None:
        workspace_root = tmp_path / "workspace"
        _make_repo(workspace_root, "repo-a", UNWRAPPED)
        _make_repo(workspace_root, "repo-b", WRAPPED)
        drift = MOD.scan_fleet(workspace_root)
        assert set(drift.keys()) == {"repo-a"}
        assert len(drift["repo-a"]) == 1

    def test_exempt_repos_skipped_even_when_unwrapped(self, tmp_path: Path) -> None:
        workspace_root = tmp_path / "workspace"
        _make_repo(workspace_root, "market-tick-data-service", UNWRAPPED)
        _make_repo(workspace_root, "unified-trading-system-ui", UNWRAPPED)
        drift = MOD.scan_fleet(workspace_root)
        assert drift == {}

    def test_clean_fleet_yields_no_drift(self, tmp_path: Path) -> None:
        workspace_root = tmp_path / "workspace"
        _make_repo(workspace_root, "repo-a", WRAPPED)
        _make_repo(workspace_root, "repo-b", NO_MOUNT)
        assert MOD.scan_fleet(workspace_root) == {}

    def test_repo_with_no_dockerfile_omitted(self, tmp_path: Path) -> None:
        workspace_root = tmp_path / "workspace"
        (workspace_root / "repo-no-docker").mkdir(parents=True)
        assert MOD.scan_fleet(workspace_root) == {}


class TestMainAlwaysWarnOnly:
    def test_main_exits_0_with_drift(self, tmp_path: Path, capsys) -> None:
        workspace_root = tmp_path / "workspace"
        _make_repo(workspace_root, "repo-a", UNWRAPPED)
        rc = MOD.main(["--workspace-root", str(workspace_root)])
        assert rc == 0
        out = capsys.readouterr().out
        assert "WARN" in out
        assert "repo-a" in out

    def test_main_exits_0_when_clean(self, tmp_path: Path, capsys) -> None:
        workspace_root = tmp_path / "workspace"
        _make_repo(workspace_root, "repo-a", WRAPPED)
        rc = MOD.main(["--workspace-root", str(workspace_root)])
        assert rc == 0
        out = capsys.readouterr().out
        assert "No uv pip install retry-wrapper drift detected" in out
