#!/usr/bin/env python3
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
"""Reconcile release tags, and ALARM when a tag-derived repo stops releasing.

Two populations, opposite treatments (split 2026-07-23):

* **Tag-derived repos** (``dynamic = ["version"]`` + hatch-vcs ``source = "vcs"``) — every repo in
  the fleet today. **The git tag IS the package version**, so "read the version, mint the matching
  tag" is circular and this script must NOT create tags for them. What it does instead is assert the
  invariant it exists to protect: ``main`` must not accumulate commits past the newest ``v*`` tag.
  Unreleased commits + a tag older than ``_STALL_DAYS`` ⇒ **STALL**, reported as a ``::warning::``
  (and a non-zero exit under ``--fail-on-stall``).

  *Why this alarm exists:* on 2026-06-27 the LDR→main cutover made ``staging`` dormant, which
  orphaned ``semver-agent`` — the only thing that mints tags — on a branch nobody pushes to. Tagging
  stopped fleet-wide for ~4 weeks. This script ran 246 times across that window and reported
  ``created 0 tag(s); 24 repo(s) had no main version`` **as a success**, because the old
  ``_VERSION_RE`` could not match a dynamic version and the miss was counted as "nothing to do"
  rather than "cannot tell". Silence on an empty input set is what made a 4-week outage invisible.

* **Legacy static-version repos** (a literal ``version = "X.Y.Z"`` in ``pyproject.toml``) — the
  original behaviour below, unchanged.

Closes the release-machinery tag-creation gap (codified 2026-06-11). The legacy release flow is:

  semver-agent → pushes ``chore(release): bump version to X`` to ``staging`` + dispatches the bump to PM
  update-repo-version → records the version in ``workspace-manifest.json``
  publish-package → triggers on ``push: tags: v*`` / ``release: created`` → publishes the package

…but **nothing creates the git tag**. Tags were created MANUALLY every time (``v0.4.0`` by slot-1 on
2026-06-09 "reconcile UTL source…to match manifest"; ``v0.6.0``/``v0.6.1`` during the 2026-06-11 keystone
recovery). So a non-automated staging→main promotion (and even the automated one) leaves ``main`` at the new
version with **no tag** → ``publish-package`` never fires and consumers' version-aware dep-clone keeps
resolving the stale tag (the exact dep-floor class that jammed the fleet 2026-06-11). A fleet dry-run on
2026-06-11 found **20 repos** in this state.

This reconciler is the missing link: for every manifest repo it compares ``main``'s ``pyproject.toml``
version to the existing ``v*`` tags and creates the matching tag on ``main`` HEAD when absent — idempotent,
path-independent (catches the automated drain AND a manual ``gh pr create`` promote), and frugal.

Guards (never create a wrong/old tag):
  * the version must be a clean ``X.Y.Z`` release (no pre-release / local suffix);
  * the tag ``vX.Y.Z`` must not already exist (idempotent);
  * ``X.Y.Z`` must be ``>=`` the highest existing ``v*`` tag (never backfill an ancient/reverted version) —
    a stdlib tuple compare, sound because release tags are plain 3-part semver;
  * ``--max-creates`` caps creations per run so a large backlog drains over a few scheduled ticks instead of
    firing N ``publish-package`` runs at once (shared-rate-limit safe).

SSOT: ``codex/08-workflows/ci-cd-flow.md`` § "Release tag reconciler".

Usage (from PM repo root, with ``GH_TOKEN``/``GH_PAT`` exported):
    python3 scripts/cicd/reconcile_release_tags.py [--dry-run] [--max-creates N] [--owner IggyIkenna]
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

# Plain 3-part release version only — pre-release / local suffixes are deliberately NOT auto-tagged.
_VERSION_RE = re.compile(r'^\s*version\s*=\s*["\']([0-9]+\.[0-9]+\.[0-9]+)["\']', re.MULTILINE)
_TAG_RE = re.compile(r"^v([0-9]+)\.([0-9]+)\.([0-9]+)$")
# hatch-vcs / setuptools-scm marker: the version is DERIVED FROM THE TAG, so there is no
# static `version = "X.Y.Z"` line and _VERSION_RE cannot match by construction. Detecting
# this is what turns "0 tags created" from a silent success into an explicit N/A verdict.
_DYNAMIC_RE = re.compile(r"^\s*dynamic\s*=\s*\[[^\]]*[\"']version[\"']", re.MULTILINE)
_VCS_SOURCE_RE = re.compile(r"^\s*source\s*=\s*[\"']vcs[\"']", re.MULTILINE)

# A dynamic repo with commits on main past its newest tag, and no new tag for this long,
# is in the exact silent-stall state that went unnoticed 2026-06-27..07-23 (~4 weeks).
_STALL_DAYS = 3

Version = tuple[int, int, int]


def _gh(args: list[str]) -> tuple[int, str]:
    """Run ``gh api <args>`` → (returncode, stdout)."""
    proc = subprocess.run(["gh", "api", *args], capture_output=True, text=True)
    return proc.returncode, proc.stdout


def _loads(text: str) -> object:
    """``json.loads`` typed as ``object`` (json.loads is ``Any``; consume it at the boundary once)."""
    return cast("object", json.loads(text))


def _ver_tuple(v: str) -> Version:
    a, b, c = v.split(".")
    return (int(a), int(b), int(c))


def _main_pyproject(owner: str, repo: str) -> str | None:
    """Return the decoded text of the repo's ``main`` pyproject.toml, or None."""
    # Query-in-path form (subprocess passes it verbatim — no shell globbing on '?'); unambiguous for the GET.
    rc, out = _gh([f"repos/{owner}/{repo}/contents/pyproject.toml?ref=main"])
    if rc != 0:
        return None
    try:
        payload: object = _loads(out)
    except (json.JSONDecodeError, ValueError):
        return None
    if not isinstance(payload, dict):
        return None
    content_b64 = cast("dict[str, object]", payload).get("content")
    if not isinstance(content_b64, str):
        return None
    try:
        return base64.b64decode(content_b64).decode("utf-8")
    except (ValueError, UnicodeDecodeError):
        return None


def _is_dynamic_versioned(pyproject_text: str) -> bool:
    """True when the package version is DERIVED FROM THE GIT TAG (hatch-vcs / setuptools-scm).

    For such a repo the tag is the CAUSE of the version, not a record of it, so this
    reconciler's "read the version, mint the matching tag" model is inverted and must not
    run — there is nothing to reconcile. Detecting it explicitly is the whole point: the
    pre-2026-07-23 code just failed ``_VERSION_RE`` and reported the repo under a bland
    "N repo(s) had no main version" line, which read as SUCCESS for ~4 weeks while the
    real tag minter (semver-agent) sat orphaned on the dormant staging branch.
    """
    return bool(_DYNAMIC_RE.search(pyproject_text)) or bool(_VCS_SOURCE_RE.search(pyproject_text))


def _commits_ahead_of_tag(owner: str, repo: str, tag: str) -> int | None:
    """Commits on ``main`` past ``tag`` (GitHub compare ``ahead_by``), or None if unavailable."""
    rc, out = _gh([f"repos/{owner}/{repo}/compare/{tag}...main", "--jq", ".ahead_by"])
    if rc != 0:
        return None
    raw = out.strip()
    return int(raw) if raw.isdigit() else None


def _newest_tag_age_days(owner: str, repo: str, tag: str) -> float | None:
    """Age in days of ``tag``'s commit, via the tag ref → commit date. None if unresolvable."""
    rc, out = _gh([f"repos/{owner}/{repo}/commits/{tag}", "--jq", ".commit.committer.date"])
    if rc != 0 or not out.strip():
        return None
    try:
        when = datetime.fromisoformat(out.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    return (datetime.now(UTC) - when).total_seconds() / 86400.0


def _highest_existing_tag(owner: str, repo: str) -> Version | None:
    rc, out = _gh([f"repos/{owner}/{repo}/tags", "--paginate"])
    if rc != 0:
        return None
    try:
        payload: object = _loads(out)
    except (json.JSONDecodeError, ValueError):
        return None
    if not isinstance(payload, list):
        return None
    highest: Version | None = None
    for entry in cast("list[object]", payload):
        if not isinstance(entry, dict):
            continue
        name = cast("dict[str, object]", entry).get("name")
        if not isinstance(name, str):
            continue
        tm = _TAG_RE.match(name)
        if not tm:
            continue
        t: Version = (int(tm.group(1)), int(tm.group(2)), int(tm.group(3)))
        if highest is None or t > highest:
            highest = t
    return highest


def _tag_exists(owner: str, repo: str, tag: str) -> bool:
    rc, _ = _gh([f"repos/{owner}/{repo}/git/refs/tags/{tag}"])
    return rc == 0


def _main_sha(owner: str, repo: str) -> str | None:
    rc, out = _gh([f"repos/{owner}/{repo}/commits/main", "--jq", ".sha"])
    sha = out.strip()
    return sha if rc == 0 and sha else None


def _create_tag(owner: str, repo: str, tag: str, sha: str) -> bool:
    proc = subprocess.run(
        [
            "gh",
            "api",
            "--method",
            "POST",
            f"repos/{owner}/{repo}/git/refs",
            "-f",
            f"ref=refs/tags/{tag}",
            "-f",
            f"sha={sha}",
        ],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        print(f"  ERROR creating {tag} on {repo}: {proc.stderr.strip()}", file=sys.stderr)
    return proc.returncode == 0


def _manifest_repos(manifest_path: Path) -> list[str] | None:
    try:
        raw: object = _loads(manifest_path.read_text())
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"FATAL: cannot read {manifest_path}: {exc}", file=sys.stderr)
        return None
    if not isinstance(raw, dict):
        print("FATAL: manifest root is not a mapping", file=sys.stderr)
        return None
    repos = cast("dict[str, object]", raw).get("repositories")
    if not isinstance(repos, dict):
        print("FATAL: manifest 'repositories' is not a mapping", file=sys.stderr)
        return None
    return sorted(str(k) for k in cast("dict[str, object]", repos))


def _write_firestore_release_tags(owner: str, repo_versions: dict[str, str], project_id: str) -> None:
    """Best-effort CAS write-through (the SELF-HEALING BACKSTOP) of the latest release version↔SHA per
    repo to ``repo_state/{repo}.release_tag`` in Firestore, via ``version_registry_store.py`` — the
    SAME store + document the event-driven ``version-registry-update.yml`` writes on a ``push: tags: v*``.
    Routing both through one store gives the backstop the store's **semver-monotonic guard** (so a
    */30 backstop write can never DOWNGRADE the registry below a version the event path already
    recorded — e.g. when main's pyproject momentarily lags the freshest tag) and stamps ``sha`` +
    ``commit_ts``, which the legacy best-effort ``merge=True`` write omitted.

    Per-repo, frugal-but-correct: it resolves each repo's main HEAD sha and shells out to the store
    CLI (which lazily imports the Firestore SDK + runs the per-repo CAS transaction). GCP_PROJECT_ID-
    gated by the caller; any single failure is swallowed so the reconciler's core tag-creation job
    never blocks on the mirror. Downstream tag-readers then query Firestore (free quota, zero GitHub
    REST) instead of the GitHub tags API."""
    store = Path(__file__).resolve().parent / "version_registry_store.py"
    for repo, version in repo_versions.items():
        sha = _main_sha(owner, repo)
        if not sha:
            continue  # cannot record without the SHA the registry doc requires
        _ = subprocess.run(
            ["python3", str(store), "set", repo, version, sha, "--project-id", project_id],
            capture_output=True,
            text=True,
        )


def reconcile(owner: str, manifest_path: Path, dry_run: bool, max_creates: int, fail_on_stall: bool) -> int:
    repos = _manifest_repos(manifest_path)
    if repos is None:
        return 1

    created: list[str] = []
    repo_versions: dict[str, str] = {}  # repo -> latest resolvable main version (for the Firestore write-through)
    dynamic_ok: list[str] = []  # tag-derived repos that are releasing normally
    stalled: list[str] = []  # tag-derived repos with unreleased commits — the silent-stall alarm
    unreadable = 0  # pyproject genuinely unreachable (archived / UI / transient API miss)
    for repo in repos:
        # PM itself is Option-B + not a published Python package — its versioning is the manifest, not a tag.
        if repo == "unified-trading-pm":
            continue
        pyproject = _main_pyproject(owner, repo)
        if pyproject is None:
            unreadable += 1
            continue  # no reachable main pyproject (UI repos, archived, transient API miss)

        # ── Tag-derived (hatch-vcs) repos: NOTHING to reconcile — the tag CAUSES the version.
        # Minting a tag from a version here would be circular. Instead, assert the invariant this
        # reconciler exists to protect: main must not accumulate unreleased commits. That is the
        # condition that silently held for ~4 weeks (semver-agent orphaned on dormant staging)
        # while this script reported a clean "created 0 tag(s)" 246 times.
        if _is_dynamic_versioned(pyproject):
            highest = _highest_existing_tag(owner, repo)
            if highest is None:
                stalled.append(f"{repo}: dynamic versioning but NO v* tag exists at all")
                continue
            tag = f"v{'.'.join(map(str, highest))}"
            ahead = _commits_ahead_of_tag(owner, repo, tag)
            age = _newest_tag_age_days(owner, repo, tag)
            if ahead is None or age is None:
                print(f"  UNKNOWN {repo}: cannot compare main against {tag} (API miss) — not asserting healthy")
                continue
            if ahead > 0 and age > _STALL_DAYS:
                stalled.append(f"{repo}: {ahead} unreleased commit(s) on main; newest tag {tag} is {age:.1f}d old")
            else:
                dynamic_ok.append(f"{repo}:{tag}")
            continue

        # ── Legacy static-version repos: the original read-version → mint-matching-tag path.
        m = _VERSION_RE.search(pyproject)
        if m is None:
            unreadable += 1
            continue
        version = m.group(1)
        repo_versions[repo] = version
        tag = f"v{version}"
        if _tag_exists(owner, repo, tag):
            continue  # idempotent — already released
        highest = _highest_existing_tag(owner, repo)
        if highest is not None and _ver_tuple(version) < highest:
            # main version is BEHIND the latest tag (a revert / clean-start) — do NOT backfill an old tag.
            print(f"  SKIP {repo}: main {version} < latest tag v{'.'.join(map(str, highest))} (no backfill)")
            continue
        sha = _main_sha(owner, repo)
        if sha is None:
            print(f"  ERROR {repo}: cannot resolve main HEAD sha", file=sys.stderr)
            continue
        if dry_run:
            print(f"  WOULD-CREATE {tag} on {repo} @ {sha[:8]} (main version {version}, no existing tag)")
            created.append(f"{repo}:{tag}")
            continue
        # Per-run cap: avoid a thundering herd of simultaneous publish-package runs when draining a backlog.
        if 0 < max_creates <= len(created):
            print(f"  CAP reached ({max_creates}) — deferring {tag} on {repo} to the next scheduled run")
            continue
        if _create_tag(owner, repo, tag, sha):
            print(f"  CREATED {tag} on {repo} @ {sha[:8]} -> triggers publish-package")
            created.append(f"{repo}:{tag}")

    verb = "would create" if dry_run else "created"
    print(
        f"\nRelease-tag reconcile: {verb} {len(created)} tag(s) [legacy static-version path]; "
        f"{len(dynamic_ok)} tag-derived repo(s) healthy; {len(stalled)} STALLED; "
        f"{unreadable} repo(s) with no readable main pyproject."
    )
    if created:
        print("  created: " + ", ".join(created))
    if dynamic_ok:
        print("  tag-derived (nothing to reconcile — the tag IS the version): " + ", ".join(dynamic_ok))

    # The alarm this script previously could not raise. A tag-derived repo accumulating
    # unreleased commits means its version minter is not running — exactly the 2026-06-27
    # orphaning. Surface it as a GitHub annotation so it is visible in the run WITHOUT
    # failing 48 scheduled runs/day; --fail-on-stall opts a caller into a hard failure.
    if stalled:
        print(f"\n::warning::Release tagging STALLED for {len(stalled)} repo(s) — versions are not advancing.")
        for line in stalled:
            print(f"  STALL {line}")
        print(
            "  → The tag minter is semver-agent (fires on a push to the repo's promotion branch).\n"
            "    Check it is enabled and targeting the branch this repo actually promotes to.\n"
            "    SSOT: codex/08-workflows/ci-cd-flow.md § 'Release tag reconciler'."
        )

    # Firestore write-through (self-healing backstop): persist latest version↔SHA per repo via the
    # CAS store so tag-readers query Firestore (free quota, zero GitHub REST) instead of the GitHub
    # tags API. Best-effort, GCP_PROJECT_ID-gated; the store's monotonic guard prevents a backstop
    # downgrade of a version the event path already recorded.
    gcp_project = os.environ.get("GCP_PROJECT_ID")
    if gcp_project and not dry_run and repo_versions:
        _write_firestore_release_tags(owner, repo_versions, gcp_project)
    return 1 if (stalled and fail_on_stall) else 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Reconcile release tags to main pyproject versions.")
    _ = ap.add_argument("--owner", default="IggyIkenna")
    _ = ap.add_argument("--manifest", default="workspace-manifest.json")
    _ = ap.add_argument("--dry-run", action="store_true", help="report what WOULD be tagged without creating")
    _ = ap.add_argument(
        "--max-creates",
        type=int,
        default=0,
        help="cap tags CREATED per run (0 = unlimited); throttles a backlog drain to avoid a publish herd",
    )
    _ = ap.add_argument(
        "--fail-on-stall",
        action="store_true",
        help="exit non-zero when a tag-derived repo has unreleased commits (default: warn only, so the "
        "*/30 schedule does not fail 48x/day; opt in from a lower-frequency health check)",
    )
    ns = ap.parse_args()
    owner = cast(str, ns.owner)
    manifest = cast(str, ns.manifest)
    dry_run = cast(bool, ns.dry_run)
    max_creates = cast(int, ns.max_creates)
    fail_on_stall = cast(bool, ns.fail_on_stall)
    return reconcile(owner, Path(manifest), dry_run, max_creates, fail_on_stall)


if __name__ == "__main__":
    raise SystemExit(main())
