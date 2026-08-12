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
import hashlib
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

# Mirrors detect_breaking_change.py's _NON_FUNCTIONAL_PATH_RE exactly (2026-08-09) — the two
# scripts run in different execution contexts (this one has no local clone of every fleet
# repo, so it uses the GitHub compare API's file list instead of `git diff`) and so cannot
# literally share the function, but the RULE — what counts as "nothing shippable changed" —
# must not silently diverge between semver-agent's bump decision and this stall-alert
# decision, or exactly the false-positive-STALL / silent-non-bump split measured 2026-08-09
# (7 repos, one alert) recurs in a new shape. If you change one, change both.
_NON_FUNCTIONAL_PATH_RE = re.compile(
    r"^(\.github/|docs/|\.gitleaks\.toml$|\.gitignore$|README\.md$|CHANGELOG\.md$|"
    r"uv\.lock$|poetry\.lock$|package-lock\.json$|pyproject\.toml$)"
)

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


def _reconcile_dynamic_repo(owner: str, repo: str) -> tuple[str, str, str]:
    """Classify one tag-derived (hatch-vcs) repo. Returns ``(bucket, tag_ref, detail)``:

    * ``bucket="unresolved"`` — ``highest``/``ahead``/``age`` unmeasurable this run (API miss);
      ``tag_ref`` is the ref used in the diagnostic print, ``detail`` unused.
    * ``bucket="stalled"`` — genuinely stale; ``detail`` is the alarm message.
    * ``bucket="quiet"`` — ahead + old tag, but confirmed nothing non-metadata changed; ``detail``
      is the summary line.
    * ``bucket="ok"`` — releasing normally; ``detail`` is the ``repo:tag`` summary.

    Extracted from ``reconcile()`` (2026-08-09) purely to keep that function's own branch count
    under the complexity ceiling — no behavior change from inlining it back would occur.
    """
    highest, fetch_ok = _highest_existing_tag(owner, repo)
    if not fetch_ok:
        return "unresolved", "", ""
    if highest is None:
        return "stalled", "", "dynamic versioning but NO v* tag exists at all"
    tag = f"v{'.'.join(map(str, highest))}"
    ahead = _commits_ahead_of_tag(owner, repo, tag)
    age = _newest_tag_age_days(owner, repo, tag)
    if ahead is None or age is None:
        return "unresolved", tag, ""
    if ahead > 0 and age > _STALL_DAYS:
        # Content-check before alarming (2026-08-09): measured live — 6 of 7 repos flagged by
        # this exact condition on 2026-08-09 had zero non-metadata files changed (a fleet-wide
        # workflow-template rollout window), always correctly non-release, never a broken
        # minter, yet paged CRITICAL regardless. See `_stall_message`'s docstring for the
        # fail-toward-paging bias on an API miss.
        msg = _stall_message(owner, repo, tag, ahead, age)
        if msg is None:
            return "quiet", tag, f"{repo}:{tag} ({ahead} commit(s), all CI/docs/lockfile-only)"
        return "stalled", tag, msg
    return "ok", tag, f"{repo}:{tag}"


def _stall_message(owner: str, repo: str, tag: str, ahead: int, age: float) -> str | None:
    """Verdict for a tag-derived repo that's ahead of its tag past ``_STALL_DAYS``.

    Returns a stall message, or None if a content-check confirms nothing beyond CI/docs/
    lockfile noise changed (correctly not a stall — see ``_source_touched``'s docstring for
    why "commits ahead + tag is old" alone is not sufficient). ``touched=None`` (API miss)
    still returns a message — fail toward paging, same bias as the caller's ahead/age None
    check; only a CONFIRMED ``touched is False`` clears it.
    """
    if _source_touched(owner, repo, tag) is False:
        return None
    return f"{ahead} unreleased commit(s) on main; newest tag {tag} is {age:.1f}d old"


def _source_touched(owner: str, repo: str, tag: str) -> bool | None:
    """True if ``main`` changed anything past ``tag`` beyond pure CI/docs/lockfile noise.

    Same compare endpoint as ``_commits_ahead_of_tag`` (one extra `--jq` field, no extra
    call) — GitHub's compare API caps ``files`` at 300 entries; a repo genuinely batching
    more file-level changes than that past a single tag is not the case this exists to
    catch, so an over-cap response is treated as touched (fail toward alerting, never
    toward silently clearing a real stall). Returns None only on an unresolvable API call
    (never on an empty/over-cap file list), so the caller can distinguish "checked, nothing
    real changed" from "could not check" the same way the other _-prefixed helpers do.
    """
    rc, out = _gh([f"repos/{owner}/{repo}/compare/{tag}...main", "--jq", "[.files[]?.filename]"])
    if rc != 0:
        return None
    try:
        files = cast("list[object]", _loads(out.strip() or "[]"))
    except (json.JSONDecodeError, ValueError):
        return None
    names = [f for f in files if isinstance(f, str)]
    return any(not _NON_FUNCTIONAL_PATH_RE.match(n) for n in names)


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


def _highest_existing_tag(owner: str, repo: str) -> tuple[Version | None, bool]:
    """Returns ``(highest, fetch_ok)``.

    ``fetch_ok=False`` means the API call itself failed or returned unparseable content — the
    caller must NOT read ``highest is None`` in that case as "confirmed zero tags exist" (2026-08-12,
    deployment_api_release_tag_stall_false_positive_2026_08_12.md): a transient `gh api` failure
    (rate limit / network blip) was misreported as "dynamic versioning but NO v* tag exists at all"
    for a repo that in fact had a brand-new tag pushed 32 minutes earlier — only a genuinely
    successful fetch that finds zero matching tag names is a real "stalled" verdict.
    """
    rc, out = _gh([f"repos/{owner}/{repo}/tags", "--paginate"])
    if rc != 0:
        return None, False
    try:
        payload: object = _loads(out)
    except (json.JSONDecodeError, ValueError):
        return None, False
    if not isinstance(payload, list):
        return None, False
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
    return highest, True


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


# ── Slack routing for the STALL alarm (2026-08-02) ──────────────────────────────────────
# Before this, a STALL only ever emitted a `::warning::` GH annotation — visible in the run
# log, invisible everywhere else. These helpers route it through the reusable notify-slack.yml
# carrier the rest of the fleet uses (SSOT: codex/04-architecture/ci-alerting.md): a STALL is a
# STANDING CONDITION (dedup_key + cooldown_min — page on the false->true transition, re-remind
# on cooldown, never every tick) and its resolution gets an explicit RESOLVED bookend, mirroring
# branch-health.yml's lag-monitor / lag-notify / lag-notify-resolved trio (same file's
# `_emit_clear_diff` is the direct model for `_emit_stall_clear_diff` below).
_STALL_DEDUP_KEY = "release-tag-stall"


def _build_stall_block(stalled: dict[str, str]) -> str:
    """The STALL payload written to --stall-out: line 1 = dedup key, line 2+ = Slack message.

    Empty string when nothing is stalled (the workflow reads a 0-byte file as stalled=false).
    ONE alert names every currently-stalled repo — never one alert per repo — so a synthetic
    multi-repo stall still produces exactly one Slack post.
    """
    if not stalled:
        return ""
    header = f":rotating_light: *RELEASE TAG STALL* — {len(stalled)} repo(s) not advancing"
    body = "\\n".join(f"  • {repo}: {msg}" for repo, msg in sorted(stalled.items()))
    tail = (
        "\\n→ Tag minter is semver-agent (fires on a push to the repo's promotion branch) — "
        "check it is enabled and targeting the branch this repo actually promotes to."
    )
    message = header + "\\n" + body + tail
    return _STALL_DEDUP_KEY + "\n" + message + "\n"


def _cleared_dedup_key(cleared_repos: list[str]) -> str:
    """A per-cleared-SET dedup key so two distinct clears each post once (see
    promotion_lag_monitor.py's identically-named helper — notify-slack dedups on `dedup_key`
    ALONE, so a static key would let the first clear swallow a second repo's clear)."""
    joined = ",".join(sorted(cleared_repos))
    digest = hashlib.sha256(joined.encode("utf-8")).hexdigest()[:12]
    return f"{_STALL_DEDUP_KEY}-cleared:{digest}"


def _build_cleared_block(cleared_repos: list[str], prev: dict[str, str], still_stalled: int) -> str:
    """The CLEARED payload written to --cleared-out: line 1 = dedup key, line 2+ = Slack message.

    Empty string when nothing cleared (the workflow reads a 0-byte file as cleared=false).
    """
    if not cleared_repos:
        return ""
    key = _cleared_dedup_key(cleared_repos)
    header = f":ballot_box_with_check: *RELEASE TAG STALL CLEARED* — {len(cleared_repos)} repo(s) tagging again"
    body = "\\n".join(f"  • {repo}: was {prev[repo]}" for repo in cleared_repos)
    tail = f"\\n({still_stalled} repo(s) still stalled)" if still_stalled else "\\n— no repos currently stalled"
    return key + "\n" + header + "\\n" + body + tail + "\n"


def _load_state(path: str) -> dict[str, str]:
    """Load the previous run's stalled-repo map ({repo: message}). Tolerates absent/corrupt/
    old-schema files -> {} so a first run after deploy never false-fires a CLEAR."""
    try:
        with open(path) as f:
            raw: object = json.load(f)
    except (OSError, ValueError):
        return {}
    if not isinstance(raw, dict):
        return {}
    stalled = cast("dict[str, object]", raw).get("stalled")
    if not isinstance(stalled, dict):
        return {}
    out: dict[str, str] = {}
    for k, v in cast("dict[str, object]", stalled).items():
        if isinstance(k, str) and isinstance(v, str):
            out[k] = v
    return out


def _write_state(path: str, curr: dict[str, str]) -> None:
    """Persist the current stalled-repo map for the next run's clear-diff. Best-effort."""
    try:
        with open(path, "w") as f:
            json.dump({"stalled": curr}, f)
    except OSError:
        pass


def _emit_stall_clear_diff(
    stalled: dict[str, str], unresolved: set[str], state_in: str, state_out: str, cleared_out: str
) -> None:
    """Diff prev->current stalled-repo sets and (opt-in) persist state + write the CLEARED block.

    A repo clears ONLY when it was stalled last run AND is affirmatively NOT stalled this run —
    i.e. NOT in `unresolved` (an API-miss this run must never masquerade as a clear; it is carried
    FORWARD into the persisted set instead, so it re-decides on the next successful probe).
    """
    prev = _load_state(state_in) if state_in else {}
    carried = {repo: prev[repo] for repo in unresolved if repo in prev}
    new_state = {**stalled, **carried}
    if cleared_out:
        cleared_repos = sorted(repo for repo in prev if repo not in stalled and repo not in unresolved)
        block = _build_cleared_block(cleared_repos, prev, still_stalled=len(new_state))
        try:
            with open(cleared_out, "w") as f:
                f.write(block)
        except OSError:
            pass
    if state_out:
        _write_state(state_out, new_state)


def reconcile(
    owner: str,
    manifest_path: Path,
    dry_run: bool,
    max_creates: int,
    fail_on_stall: bool,
    state_in: str = "",
    state_out: str = "",
    cleared_out: str = "",
    stall_out: str = "",
) -> int:
    repos = _manifest_repos(manifest_path)
    if repos is None:
        return 1

    created: list[str] = []
    repo_versions: dict[str, str] = {}  # repo -> latest resolvable main version (for the Firestore write-through)
    dynamic_ok: list[str] = []  # tag-derived repos that are releasing normally
    dynamic_quiet: list[str] = []  # ahead + old tag, but confirmed nothing non-metadata changed — not a stall
    stalled: dict[str, str] = {}  # tag-derived repo -> message — the silent-stall alarm (keyed for clear-diffing)
    unresolved: set[str] = set()  # repos whose stall verdict couldn't be measured this run (API miss) — carried
    # forward across runs (never counted as newly-cleared) rather than silently dropped.
    unreadable = 0  # pyproject genuinely unreachable (archived / UI / transient API miss)
    considered = 0  # repos actually probed (excludes the PM self-skip below) — the self-audit denominator
    for repo in repos:
        # PM itself is Option-B + not a published Python package — its versioning is the manifest, not a tag.
        if repo == "unified-trading-pm":
            continue
        considered += 1
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
            bucket, tag_ref, detail = _reconcile_dynamic_repo(owner, repo)
            if bucket == "unresolved":
                print(f"  UNKNOWN {repo}: cannot compare main against {tag_ref} (API miss) — not asserting healthy")
                unresolved.add(repo)
            elif bucket == "stalled":
                stalled[repo] = detail
            elif bucket == "quiet":
                dynamic_quiet.append(detail)
            else:
                dynamic_ok.append(detail)
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
        highest, _fetch_ok = _highest_existing_tag(owner, repo)
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
        f"{len(dynamic_ok)} tag-derived repo(s) healthy; {len(dynamic_quiet)} ahead-but-benign "
        f"(no non-metadata change); {len(stalled)} STALLED; "
        f"{unreadable} repo(s) with no readable main pyproject."
    )
    if created:
        print("  created: " + ", ".join(created))
    if dynamic_ok:
        print("  tag-derived (nothing to reconcile — the tag IS the version): " + ", ".join(dynamic_ok))
    if dynamic_quiet:
        print(
            "  ahead-but-benign (commits accumulated, none non-metadata — correctly not stalled): "
            + ", ".join(dynamic_quiet)
        )

    # Self-audit (applying the source doc's silent-failure lesson post-repurpose,
    # issues/reconcile_release_tags_dead_since_d13_git_tag_migration_2026_07_17.md § "Also fix the
    # silent-failure class"). The ORIGINAL conflation that hid the 2026-06-27 outage — a dynamic
    # repo's absent version FIELD reading as "no version" — is now handled explicitly by
    # `_is_dynamic_versioned` (bucketed as `dynamic_ok`/`stalled`, never `unreadable`). What's left
    # unresolved in `_main_pyproject` returning None is "repo genuinely has no pyproject.toml"
    # (benign — UI/archived repos) vs "the gh API call itself failed" (a real error) — but neither
    # alone produces a FALSE-HEALTHY read (both land in `unreadable`, distinct from `dynamic_ok`).
    # The one shape that WOULD still be a silent broken-lookup, unchanged from the original doc's
    # concern, is every single considered repo landing in `unreadable` at once — that is not a
    # legitimate fleet state (some repos always have a readable pyproject), it is a broken
    # `GH_TOKEN`/API, and must not report as a quiet "N unreadable" line.
    if considered > 0 and unreadable == considered:
        print(
            f"FATAL: all {considered} considered repo(s) came back unreadable — this is a broken "
            "GH_TOKEN/API lookup, not a legitimate fleet state (some repos always have a readable "
            "main pyproject). Exiting non-zero so this does not silently report as a clean run.",
            file=sys.stderr,
        )
        return 1

    # The alarm this script previously could not raise. A tag-derived repo accumulating
    # unreleased commits means its version minter is not running — exactly the 2026-06-27
    # orphaning. Surface it as a GitHub annotation so it is visible in the run WITHOUT
    # failing 48 scheduled runs/day; --fail-on-stall opts a caller into a hard failure.
    if stalled:
        print(f"\n::warning::Release tagging STALLED for {len(stalled)} repo(s) — versions are not advancing.")
        for repo, msg in sorted(stalled.items()):
            print(f"  STALL {repo}: {msg}")
        print(
            "  → The tag minter is semver-agent (fires on a push to the repo's promotion branch).\n"
            "    Check it is enabled and targeting the branch this repo actually promotes to.\n"
            "    SSOT: codex/08-workflows/ci-cd-flow.md § 'Release tag reconciler'."
        )

    # Route the STALL verdict to a channel someone actually reads (2026-08-02) — see the helpers
    # above. Opt-in via the file paths (empty = skip, unchanged behaviour for any other caller).
    if stall_out:
        try:
            with open(stall_out, "w") as f:
                f.write(_build_stall_block(stalled))
        except OSError:
            pass
    if state_in or state_out or cleared_out:
        _emit_stall_clear_diff(stalled, unresolved, state_in, state_out, cleared_out)

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
    _ = ap.add_argument(
        "--state-in",
        default="",
        help="Path to the PREVIOUS run's stalled-repo-state JSON — the clear-diff baseline "
        "(missing/old-schema -> none).",
    )
    _ = ap.add_argument(
        "--state-out",
        default="",
        help="Write the CURRENT stalled-repo-state JSON here for the next run's clear-diff.",
    )
    _ = ap.add_argument(
        "--cleared-out",
        default="",
        help="Write the named CLEARED Slack block here (line 1 = dedup key, rest = message); empty if none cleared.",
    )
    _ = ap.add_argument(
        "--stall-out",
        default="",
        help="Write the STALL Slack block here (line 1 = dedup key, rest = message); empty if nothing stalled.",
    )
    ns = ap.parse_args()
    owner = cast(str, ns.owner)
    manifest = cast(str, ns.manifest)
    dry_run = cast(bool, ns.dry_run)
    max_creates = cast(int, ns.max_creates)
    fail_on_stall = cast(bool, ns.fail_on_stall)
    state_in = cast(str, ns.state_in)
    state_out = cast(str, ns.state_out)
    cleared_out = cast(str, ns.cleared_out)
    stall_out = cast(str, ns.stall_out)
    return reconcile(
        owner,
        Path(manifest),
        dry_run,
        max_creates,
        fail_on_stall,
        state_in=state_in,
        state_out=state_out,
        cleared_out=cleared_out,
        stall_out=stall_out,
    )


if __name__ == "__main__":
    raise SystemExit(main())
