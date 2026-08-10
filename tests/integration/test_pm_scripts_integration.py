"""Integration tests verifying a repo correctly integrates with unified-trading-pm scripts.

Run from any repo (with PM as sibling) to verify:
- quality-gates.sh sources PM base script
- Required PM scripts exist and are compatible
- generate_workspace_dag.py produces valid SVG
- Manifest contains the repo and version aligns

When PM scripts change, these tests fail until repos update — single source of truth in PM.

Usage:
  # From a repo (PM must be sibling at ../unified-trading-pm):
  PROJECT_ROOT=/path/to/repo pytest unified-trading-pm/tests/integration/test_pm_scripts_integration.py -v

  # From base-service.sh (invoked during quality gates):
  PROJECT_ROOT="${PROJECT_ROOT}" pytest \
    "${WORKSPACE_ROOT}/unified-trading-pm/tests/integration/test_pm_scripts_integration.py" -v
"""

from __future__ import annotations

import json
import os
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest


def _get_repo_path() -> Path:
    """Resolve repo under test from PROJECT_ROOT env (set by base-service) or cwd."""
    raw = os.environ.get("PROJECT_ROOT", "")
    if raw:
        return Path(raw).resolve()
    return Path.cwd().resolve()


def _get_pm_root(repo_path: Path) -> Path:
    """PM is sibling of workspace root; repo parent is workspace root."""
    workspace_root = repo_path.parent
    return workspace_root / "unified-trading-pm"


def _get_repo_name(repo_path: Path) -> str:
    """Derive the canonical repo name from the git remote origin URL.

    A worktree checkout's directory basename need not match its canonical
    manifest-registered name (e.g. an ad hoc `git worktree add` under a
    scratch dir name). Deriving identity from the remote URL instead of
    `repo_path.name` makes this check invariant to directory naming, which
    removes the only reason an operator previously needed to override
    PROJECT_ROOT to a different tree than the actual invoking worktree to
    satisfy this test (see
    utl_shared_clone_commits_repeatedly_reset_2026_07_22.md todo 5 — that
    override was also silently redirecting where QG's sentinel files got
    written and what tree they verified, since PROJECT_ROOT drives both).
    Falls back to the directory basename if there is no git remote
    (e.g. a bare/non-git path) or git is unavailable.
    """
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_path), "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return repo_path.name
    if result.returncode != 0 or not result.stdout.strip():
        return repo_path.name
    url = result.stdout.strip()
    name = url.rstrip("/").removesuffix(".git").rsplit("/", 1)[-1]
    return name or repo_path.name


def test_get_repo_name_uses_remote_url_not_directory_basename(tmp_path: Path) -> None:
    """A worktree checked out under a mismatched dir name must still resolve
    to its canonical repo name via the git remote, not the dir basename."""
    repo_dir = tmp_path / "some-repo-scratch-worktree-dir"
    repo_dir.mkdir()
    subprocess.run(["git", "init", "--quiet"], cwd=str(repo_dir), check=True)
    subprocess.run(
        ["git", "remote", "add", "origin", "git@github.com:org/instruments-service.git"],
        cwd=str(repo_dir),
        check=True,
    )
    assert _get_repo_name(repo_dir) == "instruments-service"


def test_get_repo_name_falls_back_to_basename_without_remote(tmp_path: Path) -> None:
    repo_dir = tmp_path / "no-remote-repo"
    repo_dir.mkdir()
    subprocess.run(["git", "init", "--quiet"], cwd=str(repo_dir), check=True)
    assert _get_repo_name(repo_dir) == "no-remote-repo"


@pytest.fixture
def repo_path() -> Path:
    return _get_repo_path()


@pytest.fixture
def pm_root(repo_path: Path) -> Path:
    return _get_pm_root(repo_path)


@pytest.fixture
def repo_name(repo_path: Path) -> str:
    return _get_repo_name(repo_path)


@pytest.fixture
def manifest_path(pm_root: Path) -> Path:
    return pm_root / "workspace-manifest.json"


@pytest.mark.integration
def test_pm_is_sibling(repo_path: Path, pm_root: Path) -> None:
    """PM must exist as sibling for integration."""
    assert pm_root.is_dir(), f"PM not found at {pm_root}"


@pytest.mark.integration
def test_quality_gates_sources_pm(repo_path: Path, pm_root: Path) -> None:
    """quality-gates.sh must source PM base-service.sh."""
    qg = repo_path / "scripts" / "quality-gates.sh"
    if not qg.exists():
        pytest.skip(f"{repo_path.name} has no scripts/quality-gates.sh")
    text = qg.read_text()
    base = pm_root / "scripts" / "quality-gates-base" / "base-service.sh"
    assert base.exists(), "PM base-service.sh missing"
    assert "base-service.sh" in text or "quality-gates-base" in text
    assert "unified-trading-pm" in text or "WORKSPACE_ROOT" in text


@pytest.mark.integration
def test_required_pm_scripts_exist(pm_root: Path) -> None:
    """Required PM scripts used by repos must exist."""
    required = [
        "scripts/quality-gates-base/base-service.sh",
        "scripts/manifest/generate_workspace_dag.py",
        "workspace-manifest.json",
    ]
    for rel in required:
        assert (pm_root / rel).exists(), f"Required PM script missing: {rel}"


@pytest.mark.integration
def test_generate_workspace_dag_produces_valid_svg(pm_root: Path) -> None:
    """generate_workspace_dag.py must produce valid SVG."""
    script = pm_root / "scripts" / "manifest" / "generate_workspace_dag.py"
    manifest = pm_root / "workspace-manifest.json"
    if not script.exists() or not manifest.exists():
        pytest.skip("generate_workspace_dag or manifest missing")
    result = subprocess.run(
        [os.environ.get("PYTHON_CMD", "python3"), str(script)],
        cwd=str(pm_root),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, f"generate_workspace_dag failed: {result.stderr}"
    output_svg = pm_root / "WORKSPACE_MANIFEST_DAG.svg"
    assert output_svg.exists()
    tree = ET.parse(output_svg)
    root = tree.getroot()
    assert root.tag.endswith("svg") or "svg" in root.tag


@pytest.mark.integration
def test_repo_in_manifest(repo_name: str, manifest_path: Path) -> None:
    """Repo must be listed in workspace-manifest.json."""
    if not manifest_path.exists():
        pytest.skip("Manifest not found")
    with open(manifest_path) as f:
        data = json.load(f)
    repos = data.get("repositories", {})
    assert repo_name in repos, f"{repo_name} not in workspace-manifest.json"


@pytest.mark.integration
def test_setup_sh_exists_or_exempt(repo_path: Path, repo_name: str, manifest_path: Path) -> None:
    """Repos should have setup.sh unless exempt."""
    setup = repo_path / "scripts" / "setup.sh"
    if setup.exists():
        return
    exempt = {"unified-trading-codex", "unified-trading-pm", "ibkr-gateway-infra"}
    if repo_name in exempt:
        pytest.skip(f"{repo_name} is exempt from setup.sh")
    if manifest_path.exists():
        with open(manifest_path) as f:
            data = json.load(f)
        cfg = data.get("repositories", {}).get(repo_name, {})
        if cfg.get("type") == "infrastructure" and "codex" in repo_name.lower():
            pytest.skip("Infrastructure/codex repo exempt")
    pytest.fail(f"{repo_name} missing scripts/setup.sh")
