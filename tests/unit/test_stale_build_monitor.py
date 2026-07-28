"""Unit tests for scripts/cicd/stale_build_monitor.py's pure helpers.

This is the loud-failure-signal for cloud_build_router_concurrency_drops_dispatch_2026_07_27.md
todo #2 — a repo's `main` merge goes CI-green while its deployed `:latest` image silently stays
on the previous build. These tests cover the parsing/decision logic (cloudbuild.yaml `images:` /
`substitutions:` extraction, AR-entry matching, the staleness gap decision) without touching
`gh`/`gcloud`.
"""

from __future__ import annotations

import datetime as dt
import importlib.util
import types
from pathlib import Path


def _load_module() -> types.ModuleType:
    repo_root = Path(__file__).resolve().parents[2]
    path = repo_root / "scripts" / "cicd" / "stale_build_monitor.py"
    spec = importlib.util.spec_from_file_location("stale_build_monitor", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


SBM = _load_module()

# A trimmed but structurally faithful excerpt of instruments-service/cloudbuild.yaml's shape —
# a `substitutions:` block feeding `${_VAR}` tokens into an `images:` list. Real-world case with
# the common `_REGISTRY_REPO`/`_SERVICE_NAME` pair.
_SUBSTITUTED_CLOUDBUILD = """\
steps:
  - name: gcr.io/cloud-builders/docker
    args: ["build", "-t", "x", "."]

substitutions:
  _SERVICE_NAME: "instruments-service"
  _REGISTRY_REPO: "unified-trading-system"
  _PKG_NAME: "instruments_service"
  _IN_IMAGE_QG: "true"

images:
  - "asia-northeast1-docker.pkg.dev/$PROJECT_ID/${_REGISTRY_REPO}/${_SERVICE_NAME}:latest"
"""

# deployment-service's shape: TWO images share the same substitutions, one via a hardcoded literal
# service name embedded directly in the second image entry (sports-scheduler).
_MULTI_IMAGE_CLOUDBUILD = """\
substitutions:
  _SERVICE_NAME: deployment-dashboard
  _ARTIFACT_REPO: deployment-dashboard

images:
  - "asia-northeast1-docker.pkg.dev/$PROJECT_ID/${_ARTIFACT_REPO}/${_SERVICE_NAME}:latest"
  - "asia-northeast1-docker.pkg.dev/$PROJECT_ID/${_ARTIFACT_REPO}/sports-scheduler:latest"
"""

# unified-trading-library's shape: no `substitutions:` block at all — every token is already
# a literal in the `images:` list.
_LITERAL_CLOUDBUILD = """\
images:
  - "asia-northeast1-docker.pkg.dev/$PROJECT_ID/unified-trading-library/unified-trading-library:latest"
"""

# A repo with no `images:` block at all (e.g. a library that only publishes a wheel, not a
# runtime image) — must resolve to zero images, not an error.
_NO_IMAGE_CLOUDBUILD = """\
substitutions:
  _PKG_NAME: "some_lib"

steps:
  - name: gcr.io/cloud-builders/docker
    args: ["build", "-t", "x", "."]
"""

# A repo whose `images:` entry references a substitution key the file never declares (a genuinely
# unresolvable template) — must be skipped, not crash or silently emit the raw `${_VAR}` string.
_UNRESOLVABLE_CLOUDBUILD = """\
images:
  - "asia-northeast1-docker.pkg.dev/$PROJECT_ID/${_UNDECLARED_REPO}/svc:latest"
"""

_PROJECT = "test-project-1"


# ── extract_latest_images ──────────────────────────────────────────────────────────────────


def test_resolves_substituted_image() -> None:
    got = SBM.extract_latest_images(_SUBSTITUTED_CLOUDBUILD, _PROJECT)
    assert got == [f"asia-northeast1-docker.pkg.dev/{_PROJECT}/unified-trading-system/instruments-service:latest"]


def test_resolves_multiple_images_sharing_substitutions() -> None:
    got = SBM.extract_latest_images(_MULTI_IMAGE_CLOUDBUILD, _PROJECT)
    assert got == [
        f"asia-northeast1-docker.pkg.dev/{_PROJECT}/deployment-dashboard/deployment-dashboard:latest",
        f"asia-northeast1-docker.pkg.dev/{_PROJECT}/deployment-dashboard/sports-scheduler:latest",
    ]


def test_resolves_fully_literal_image_with_no_substitutions_block() -> None:
    got = SBM.extract_latest_images(_LITERAL_CLOUDBUILD, _PROJECT)
    assert got == [f"asia-northeast1-docker.pkg.dev/{_PROJECT}/unified-trading-library/unified-trading-library:latest"]


def test_no_images_block_resolves_empty() -> None:
    assert SBM.extract_latest_images(_NO_IMAGE_CLOUDBUILD, _PROJECT) == []


def test_undeclared_substitution_is_skipped_not_raised() -> None:
    """A template referencing a var the file never declares must be dropped (fail-open), never
    emit the raw unresolved `${_VAR}` string as if it were a real image path."""
    assert SBM.extract_latest_images(_UNRESOLVABLE_CLOUDBUILD, _PROJECT) == []


def test_non_latest_tag_is_ignored() -> None:
    text = 'images:\n  - "asia-northeast1-docker.pkg.dev/$PROJECT_ID/repo/svc:v1.2.3"\n'
    assert SBM.extract_latest_images(text, _PROJECT) == []


# ── split_image_ref ─────────────────────────────────────────────────────────────────────────


def test_split_image_ref_common_shape() -> None:
    got = SBM.split_image_ref("asia-northeast1-docker.pkg.dev/proj/unified-trading-system/instruments-service:latest")
    assert got == ("asia-northeast1-docker.pkg.dev/proj/unified-trading-system", "instruments-service")


def test_split_image_ref_rejects_non_latest() -> None:
    assert SBM.split_image_ref("asia-northeast1-docker.pkg.dev/proj/repo/svc:v1") is None


def test_split_image_ref_rejects_too_short_path() -> None:
    assert SBM.split_image_ref("proj/repo:latest") is None


# ── latest_push_time ────────────────────────────────────────────────────────────────────────


def test_latest_push_time_matches_by_package_tail_and_latest_tag() -> None:
    other = {
        "package": ".../unified-trading-system/other-service",
        "tags": ["latest"],
        "updateTime": "2026-07-27T10:00:00Z",
    }
    older = {
        "package": ".../unified-trading-system/instruments-service",
        "tags": ["v1.2.3"],
        "updateTime": "2026-07-27T09:00:00Z",
    }
    newer = {
        "package": ".../unified-trading-system/instruments-service",
        "tags": ["latest"],
        "updateTime": "2026-07-27T13:02:30Z",
    }
    images = [other, older, newer]
    got = SBM.latest_push_time(images, "instruments-service")
    assert got == dt.datetime(2026, 7, 27, 13, 2, 30, tzinfo=dt.UTC)


def test_latest_push_time_none_when_no_matching_tagged_entry() -> None:
    images = [{"package": ".../repo/other-service", "tags": ["latest"], "updateTime": "2026-07-27T10:00:00Z"}]
    assert SBM.latest_push_time(images, "instruments-service") is None


def test_latest_push_time_none_on_empty_list() -> None:
    assert SBM.latest_push_time([], "instruments-service") is None


# ── ldr_main_repos ───────────────────────────────────────────────────────────────────────────


def test_ldr_main_repos_reads_real_manifest() -> None:
    """Cross-check against the actual workspace-manifest.json — this is the same population the
    fleet's other cicd monitors (promotion_lag_monitor._main_direct_repos) already derive from,
    just filtered to promotion_model=='ldr_main' directly (no PM, no staging_dormant_mode
    expansion — see the module docstring for why this check intentionally reads the literal flag)."""
    repo_root = Path(__file__).resolve().parents[2]
    manifest_path = repo_root / "workspace-manifest.json"
    got = SBM.ldr_main_repos(manifest_path)
    assert "instruments-service" in got
    assert "unified-trading-pm" not in got  # PM doesn't declare promotion_model: ldr_main itself
    assert got == sorted(got)


def test_ldr_main_repos_missing_manifest_returns_empty(tmp_path: Path) -> None:
    assert SBM.ldr_main_repos(tmp_path / "does_not_exist.json") == []
