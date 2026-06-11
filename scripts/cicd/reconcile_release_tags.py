#!/usr/bin/env python3
"""Reconcile release tags — ensure a ``v<pyproject.version>`` git tag exists on each repo's ``main``.

Closes the release-machinery tag-creation gap (codified 2026-06-11). The release flow is:

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
import re
import subprocess
import sys
from pathlib import Path
from typing import cast

# Plain 3-part release version only — pre-release / local suffixes are deliberately NOT auto-tagged.
_VERSION_RE = re.compile(r'^\s*version\s*=\s*["\']([0-9]+\.[0-9]+\.[0-9]+)["\']', re.MULTILINE)
_TAG_RE = re.compile(r"^v([0-9]+)\.([0-9]+)\.([0-9]+)$")

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


def _main_version(owner: str, repo: str) -> str | None:
    """Return the ``X.Y.Z`` version string from the repo's ``main`` pyproject.toml, or None."""
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
        text = base64.b64decode(content_b64).decode("utf-8")
    except (ValueError, UnicodeDecodeError):
        return None
    m = _VERSION_RE.search(text)
    return m.group(1) if m else None


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


def reconcile(owner: str, manifest_path: Path, dry_run: bool, max_creates: int) -> int:
    repos = _manifest_repos(manifest_path)
    if repos is None:
        return 1

    created: list[str] = []
    skipped = 0
    for repo in repos:
        # PM itself is Option-B + not a published Python package — its versioning is the manifest, not a tag.
        if repo == "unified-trading-pm":
            continue
        version = _main_version(owner, repo)
        if version is None:
            skipped += 1
            continue  # no resolvable main pyproject version (UI repos, archived, transient API miss)
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
    print(f"\nRelease-tag reconcile: {verb} {len(created)} tag(s); {skipped} repo(s) had no main version.")
    if created:
        print("  " + ", ".join(created))
    return 0


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
    ns = ap.parse_args()
    owner = cast(str, ns.owner)
    manifest = cast(str, ns.manifest)
    dry_run = cast(bool, ns.dry_run)
    max_creates = cast(int, ns.max_creates)
    return reconcile(owner, Path(manifest), dry_run, max_creates)


if __name__ == "__main__":
    raise SystemExit(main())
