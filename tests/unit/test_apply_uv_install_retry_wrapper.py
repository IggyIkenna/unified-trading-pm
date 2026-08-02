"""Unit tests for scripts/propagation/apply-uv-install-retry-wrapper.py.

Covers the surgical-edit conversion (`convert_dockerfile`) -- wraps a bare
`uv pip install ... --no-sources` line, preserves surrounding lines + flag order + indentation,
is idempotent on an already-wrapped layer, and skips a layer with no gar_token mount -- plus
`main()`'s dry-run/write/--repo/exempt-repo behavior against a synthetic workspace + manifest.

SSOT: codex/06-coding-standards/dockerfile-standards.md § "uv pip install Retry Wrapper".
"""

from __future__ import annotations

import importlib.util
import json
import sys
import types
from pathlib import Path

import pytest

UNWRAPPED = """\
FROM base
RUN --mount=type=secret,id=gar_token \\
    UV_EXTRA_INDEX_URL="https://oauth2accesstoken:$(cat /run/secrets/gar_token)@example/" \\
    uv pip install --system -e . --no-sources
OTHER LINE
"""

WRAPPED = (
    "FROM base\n"
    "RUN --mount=type=secret,id=gar_token \\\n"
    '    UV_EXTRA_INDEX_URL="https://oauth2accesstoken:$(cat /run/secrets/gar_token)@example/" \\\n'
    '    sh -c \'i=1; until uv pip install --system --no-sources -e .; do [ "$i" -ge 3 ] && '
    '{ echo "uv pip install failed after 3 attempts" >&2; exit 1; }; w=$((15 * i)); echo "uv pip install failed '
    '(attempt $i/3) -- retrying in ${w}s"; sleep "$w"; i=$((i + 1)); done\'\n'
)

NO_MOUNT = """\
FROM base
RUN uv pip install --system --no-sources -e .
"""


def _load_module() -> types.ModuleType:
    repo_root = Path(__file__).resolve().parents[2]
    path = repo_root / "scripts" / "propagation" / "apply-uv-install-retry-wrapper.py"
    spec = importlib.util.spec_from_file_location("apply_uv_install_retry_wrapper", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


MOD = _load_module()


# ── convert_dockerfile — the surgical per-line edit ──────────────────────────


class TestConvertDockerfile:
    def test_wraps_bare_command_preserving_flags_and_order(self) -> None:
        new_content, action = MOD.convert_dockerfile(UNWRAPPED)
        assert action == "convert"
        assert "sh -c 'i=1; until uv pip install --system -e . --no-sources; do" in new_content
        assert new_content.count("uv pip install --system -e . --no-sources") == 1

    def test_preserves_surrounding_lines_untouched(self) -> None:
        new_content, _ = MOD.convert_dockerfile(UNWRAPPED)
        assert 'UV_EXTRA_INDEX_URL="https://oauth2accesstoken:$(cat /run/secrets/gar_token)@example/"' in new_content
        assert "OTHER LINE" in new_content
        assert new_content.startswith("FROM base\n")

    def test_preserves_indentation(self) -> None:
        new_content, _ = MOD.convert_dockerfile(UNWRAPPED)
        for line in new_content.splitlines():
            if "sh -c 'i=1; until uv pip install" in line:
                assert line.startswith("    ")  # same 4-space indent as the original bare line

    def test_idempotent_on_already_wrapped(self) -> None:
        new_content, action = MOD.convert_dockerfile(WRAPPED)
        assert action == "ok"
        assert new_content == WRAPPED

    def test_skip_when_no_gar_token_mount(self) -> None:
        new_content, action = MOD.convert_dockerfile(NO_MOUNT)
        assert action == "skip"
        assert new_content == NO_MOUNT

    def test_reconvert_of_own_output_is_idempotent(self) -> None:
        """Running the propagation twice must not double-wrap (mirrors the digest-arg precedent's
        idempotency contract)."""
        once, action1 = MOD.convert_dockerfile(UNWRAPPED)
        assert action1 == "convert"
        twice, action2 = MOD.convert_dockerfile(once)
        assert action2 == "ok"
        assert twice == once


# ── main() — file I/O, --dry-run, --repo, exempt repos ───────────────────────


def _write_manifest(pm_root: Path, repos: dict) -> Path:
    manifest_path = pm_root / "workspace-manifest.json"
    manifest_path.write_text(json.dumps({"repositories": repos}), encoding="utf-8")
    return manifest_path


def _make_repo(workspace_root: Path, repo_name: str, dockerfile_content: str) -> Path:
    repo_dir = workspace_root / repo_name
    repo_dir.mkdir(parents=True, exist_ok=True)
    (repo_dir / "Dockerfile").write_text(dockerfile_content, encoding="utf-8")
    return repo_dir


@pytest.fixture
def workspace_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    workspace_root = tmp_path / "workspace"
    workspace_root.mkdir()
    pm_root = tmp_path  # workspace-manifest.json lives directly under the (synthetic) PM root
    manifest_path = _write_manifest(pm_root, {"repo-a": {}, "repo-b": {}, "market-tick-data-service": {}})
    monkeypatch.setattr(MOD, "WORKSPACE_ROOT", workspace_root)
    monkeypatch.setattr(MOD, "MANIFEST_PATH", manifest_path)
    return workspace_root


class TestMain:
    def test_dry_run_does_not_write(self, workspace_env: Path, capsys) -> None:
        _make_repo(workspace_env, "repo-a", UNWRAPPED)
        rc = MOD.main(["--dry-run"])
        assert rc == 0
        content_after = (workspace_env / "repo-a" / "Dockerfile").read_text()
        assert content_after == UNWRAPPED  # untouched
        out = capsys.readouterr().out
        assert "CONVERT" in out and "dry-run" in out

    def test_writes_the_wrapped_content(self, workspace_env: Path) -> None:
        _make_repo(workspace_env, "repo-a", UNWRAPPED)
        rc = MOD.main([])
        assert rc == 0
        content_after = (workspace_env / "repo-a" / "Dockerfile").read_text()
        assert "until uv pip install" in content_after

    def test_repo_filter_scopes_to_one_repo(self, workspace_env: Path) -> None:
        _make_repo(workspace_env, "repo-a", UNWRAPPED)
        _make_repo(workspace_env, "repo-b", UNWRAPPED)
        rc = MOD.main(["--repo", "repo-a"])
        assert rc == 0
        assert "until uv pip install" in (workspace_env / "repo-a" / "Dockerfile").read_text()
        assert "until uv pip install" not in (workspace_env / "repo-b" / "Dockerfile").read_text()

    def test_exempt_repo_skipped_even_if_in_manifest(self, workspace_env: Path) -> None:
        _make_repo(workspace_env, "market-tick-data-service", UNWRAPPED)
        rc = MOD.main([])
        assert rc == 0
        # Untouched -- market-tick-data-service is in SKIP_REPOS.
        content_after = (workspace_env / "market-tick-data-service" / "Dockerfile").read_text()
        assert content_after == UNWRAPPED

    def test_unknown_repo_filter_errors(self, workspace_env: Path) -> None:
        rc = MOD.main(["--repo", "does-not-exist"])
        assert rc == 1
