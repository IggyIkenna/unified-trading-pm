#!/usr/bin/env python3
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
"""Promotion-lag monitor — a PURE BRANCH-PAIR lag monitor (LDR↔staging↔main out of sync > N min).

Under the Path-B / LDR-SSOT model the IDE's local-vs-upstream is ~always 0 (a slot is on
live-defi-rollout and pushes immediately). The diff that actually matters is a PIPELINE
property: commits sitting on one branch that haven't propagated to another. This monitor makes
that visible as a Slack alert.

Per repo it checks four directions and flags any whose OLDEST un-propagated commit is older
than the threshold (default 60 min):

  * LDR → main      : LDR commits not promoted to main      (forward promotion lag)
  * LDR → staging   : LDR commits not promoted to staging   (forward promotion lag)
  * main → LDR      : main commits not back-merged to LDR   (backmerge lag — the drift-tick
                      sweeps these every 20 min, so > 60 min means the drift-tick is wedged)
  * staging → LDR   : staging commits not back-merged to LDR

`[skip ci]` automation commits (ci_status / manifest writes) are EXCLUDED from forward lag
(they're not meant to promote) but COUNTED in backmerge lag (they should sweep back to LDR).
Main-direct repos — PM (Option B) PLUS every repo flagged `promotion_model == "ldr_main"` (the WS-L
cutover where LDR promotes straight to main and staging is toggled OFF) — have their staging
directions SKIPPED: the bypassed staging path is intentionally dormant, not stuck. Staging is
retained + the toggle is reversible (a major/breaking bump or operator decision still routes through
staging, which clears `ldr_main` and re-enables its staging monitoring). See `_main_direct_repos()`.
Repos flagged `promotion_model == "ldr_terminal"` have BOTH main-facing directions skipped (`main` is
a frozen ref nothing deploys from — see `_ldr_terminal_repos()`); repos flagged `"single_branch"` are
skipped ENTIRELY (no LDR/staging pipeline exists at all — see `_single_branch_repos()`).

SCOPE (alert_quality_audit_2026_06_18 — collapse the duplicate detectors): this monitor is the
SSOT for branch-pair PROPAGATION lag ONLY. It deliberately does NOT detect stuck/conflict
promotion PRs — `ci-failure-watcher` (scripts/repo-management/ci_failure_watcher.py) is the
SSOT for those (it also auto-recovers + escalates them) — nor a dangling staging lock, which
`sit-starvation-detector.yml` owns. A single event must page ONCE, not from three detectors.

The Slack message is demoted to TRANSITION-ONLY at the EMIT layer: the workflow passes a stable
`dedup_key` (`promotion-lag:<threshold>m`) + a `cooldown_min` to the notify-slack carrier, so a
standing lag pages on the 60m-CROSSING and is suppressed thereafter until it clears + recrosses
— it no longer re-pages every tick (the operator's "branch behind" repeat complaint).

Stdlib + `gh` only. Prints a human report; with `--slack` prints a Slack-formatted block (the
workflow posts it). Exit 1 if any lag exceeds the threshold (so a required-check/alert can gate).

Usage:
    promotion_lag_monitor.py [--threshold-min 60] [--now-iso 2026-06-09T07:00:00Z] [--slack]
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import sys
from typing import cast
from urllib.parse import quote

OWNER = "IggyIkenna"

# Stable marker the LDR→main fleet bot puts on a promote PR it REFUSED to arm because the promote
# range carries code that bypassed quickmerge (its D1 provenance gate). KEEP IN SYNC with
# ldr-to-main-promote-fleet.yml. A provenance block is a DELIBERATE refusal with a specific remedy
# (re-ship via quickmerge), not a stuck pipeline — but it used to surface only as an anonymous
# "PROMOTION LAG > 60m" line, indistinguishable from a wedged promote. Measured 2026-07-16:
# market-tick-data-service sat blocked ~23h that way, and the misreading ("the bot forgot to arm
# auto-merge") led to the gate being hand-overridden — promoting 33 bypassed commits and laundering
# them past the provenance baseline. Naming the block in the alert is what prevents that repeat.
_PROVENANCE_MARKER = "<!-- promote:provenance-blocked -->"

# The fleet-shared SIT commit-status context `ldr_to_main_fleet_promote.sh` posts on an
# `ldr_main` repo's promote-PR head sha (`scripts/repo-management/pin_branch_protection_rulesets.py`
# `SIT_FLEET_CONTEXT` is the ruleset-side twin of this constant — keep both in sync).
_SIT_FLEET_CONTEXT = "sit-gate/fleet-green"

# Cap on per-file last-touch lookups in _content_delta_age. The oldest last-touch over a
# 25-file sample is a sound floor for "how long has the delta been waiting" — and the age
# only has to beat a 60m threshold, not be exact. Bounded so a huge delta cannot fan out
# into hundreds of PAT calls per tick. A cap HIT is logged, never silent.
_MAX_DELTA_FILES = 25

# ETag cache for conditional requests: api-path -> (etag, body_text). GitHub does
# NOT count a `304 Not Modified` against the rate limit, and most branch-pairs are
# unchanged between 20-min runs, so this collapses ~300 PAT calls/hr (25 repos x 4
# directions x 3 runs) to mostly free 304s. Persisted across CI runs via
# actions/cache (see promotion-lag-monitor.yml); in-memory only when unset.
_ETAG_CACHE: dict[str, tuple[str, str]] = {}


def _parse_gh_api_i(raw: str) -> tuple[int | None, str | None, str | None]:
    """Parse a `gh api -i` response → (http_status, etag, body_text). Pure (testable).

    `gh api -i` exits non-zero on a 304, so callers read the parsed status line
    here, never the subprocess return code.
    """
    if not raw:
        return None, None, None
    first = raw.split("\n", 1)[0].strip()
    m = re.match(r"HTTP/[\d.]+\s+(\d{3})", first)
    status = int(m.group(1)) if m else None
    em = re.search(r"(?im)^etag:\s*(.+?)\s*$", raw)
    etag = em.group(1).strip() if em else None
    if status == 304:
        return 304, etag, None
    parts = re.split(r"\r?\n\r?\n", raw, maxsplit=1)
    body = parts[1] if len(parts) > 1 else ""
    return status, etag, body


def load_etag_cache(path: str) -> None:
    """Restore the persisted ETag cache (`{path: [etag, body]}`). Best-effort."""
    try:
        with open(path) as f:
            raw = cast("object", json.load(f))
    except (OSError, ValueError):
        return
    if isinstance(raw, dict):
        for k, v in cast("dict[str, object]", raw).items():
            if isinstance(v, list):
                vl = cast("list[object]", v)
                if len(vl) == 2 and all(isinstance(x, str) for x in vl):
                    _ETAG_CACHE[k] = (cast("str", vl[0]), cast("str", vl[1]))


def save_etag_cache(path: str) -> None:
    """Persist the ETag cache as `{path: [etag, body]}`. Best-effort."""
    try:
        with open(path, "w") as f:
            json.dump({k: [e, b] for k, (e, b) in _ETAG_CACHE.items()}, f)
    except OSError:
        pass


def _gh_json(path: str) -> object:
    """GET an api.github.com path as JSON, behind an ETag conditional request.

    A cached ETag → `If-None-Match`; a `304` reuses the cached body for **free**
    (no rate cost). Returns None on any non-200/304 (preserves prior behaviour).
    """
    cached = _ETAG_CACHE.get(path)
    cmd = ["gh", "api", "-i", path]
    if cached:
        cmd += ["-H", f"If-None-Match: {cached[0]}"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    status, etag, body = _parse_gh_api_i(r.stdout)
    if status == 304 and cached:
        body = cached[1]  # free: not counted against the rate limit
    elif status != 200:
        return None
    elif etag and body:
        _ETAG_CACHE[path] = (etag, body)
    if not body:
        return None
    try:
        return cast("object", json.loads(body))
    except json.JSONDecodeError:
        return None


def _repos() -> list[str]:
    here = os.path.dirname(os.path.abspath(__file__))
    mpath = os.path.join(here, "..", "..", "workspace-manifest.json")
    with open(mpath) as _mf:
        m = cast("dict[str, object]", json.load(_mf))
    topo = cast("dict[str, object]", m.get("topologicalOrder") or {})
    out: list[str] = []
    levels = topo.get("levels")
    if isinstance(levels, list):
        for lv in cast("list[object]", levels):
            if isinstance(lv, dict):
                for r in cast("list[object]", cast("dict[str, object]", lv).get("repos") or []):
                    out.append(str(r))
    return out


def _main_direct_repos(manifest_path: str | None = None) -> set[str]:
    """Repos that promote LDR→main DIRECTLY (staging toggled OFF) — their LDR↔staging directions are
    intentionally DORMANT, not stuck, so the lag monitor must skip them (else the bypassed staging path
    shows as a perpetual "stuck" lag on the deployment-ui /repos tab + Slack). This is PM (Option-B)
    PLUS every repo flagged `promotion_model == "ldr_main"` in the manifest (the WS-L cutover).

    Staging is RETAINED + the toggle is REVERSIBLE: a major/breaking version bump or an operator
    decision can still route a repo through staging — at that point its `promotion_model` is not
    `ldr_main`, so it drops out of this set and its staging lag is monitored again.
    """
    if manifest_path is None:
        here = os.path.dirname(os.path.abspath(__file__))
        manifest_path = os.path.join(here, "..", "..", "workspace-manifest.json")
    out: set[str] = {"unified-trading-pm"}
    try:
        with open(manifest_path) as _mf:
            m = cast("dict[str, object]", json.load(_mf))
        repos = m.get("repositories")
        # WS-L staging-dormant toggle (top-level `staging_dormant_mode`): when on, EVERY repo promotes
        # LDR→main directly and staging is dormant — treat all repos as main-direct so the lag monitor
        # + Slack skip every staging direction (the operator's "we don't care about staging" mode).
        # Reversible: flip the flag off to resume staging monitoring fleet-wide.
        dormant = bool(m.get("staging_dormant_mode"))
        if isinstance(repos, dict):
            for name, cfg in cast("dict[str, object]", repos).items():
                if dormant or (
                    isinstance(cfg, dict) and cast("dict[str, object]", cfg).get("promotion_model") == "ldr_main"
                ):
                    out.add(str(name))
    except (OSError, json.JSONDecodeError, ValueError):
        pass  # manifest unreadable → fall back to PM-only (prior behavior)
    return out


def _ldr_terminal_repos(manifest_path: str | None = None) -> set[str]:
    """Repos flagged `promotion_model == "ldr_terminal"` in the manifest — `main` is a FROZEN
    historical ref for these (deploy reads straight from live-defi-rollout; nothing consumes `main`
    at all), so BOTH `LDR→main` and `main→LDR` are intentionally dormant, not stuck. Without this
    exemption the monitor perpetually flags a repo like agent-orchestrator (promotion_model flipped
    2026-08-05, see agent_orchestrator_ldr_terminal_promotion_2026_08_05) as lagging on a direction
    it will never clear by design — an alert-accuracy false positive, not a real pipeline problem.
    Mirrors `_main_direct_repos()`'s manifest-driven pattern (no hardcoded repo names beyond the
    fallback-empty case, so a future `ldr_terminal` repo picks this up automatically).
    """
    if manifest_path is None:
        here = os.path.dirname(os.path.abspath(__file__))
        manifest_path = os.path.join(here, "..", "..", "workspace-manifest.json")
    out: set[str] = set()
    try:
        with open(manifest_path) as _mf:
            m = cast("dict[str, object]", json.load(_mf))
        repos = m.get("repositories")
        if isinstance(repos, dict):
            for name, cfg in cast("dict[str, object]", repos).items():
                if isinstance(cfg, dict) and cast("dict[str, object]", cfg).get("promotion_model") == "ldr_terminal":
                    out.add(str(name))
    except (OSError, json.JSONDecodeError, ValueError):
        pass  # manifest unreadable → fall back to empty (prior behavior: no exemption)
    return out


def _single_branch_repos(manifest_path: str | None = None) -> set[str]:
    """Repos flagged `promotion_model == "single_branch"` in the manifest — there is no LDR/staging
    promotion pipeline AT ALL (one branch of record, `main`; any other branch present in the repo,
    e.g. a leftover `live-defi-rollout`, is not a live target and nothing should push to it). Skip
    the repo ENTIRELY — all four directions (LDR→main, LDR→staging, main→LDR, staging→LDR) are
    dormant-by-design here, not stuck, so paging on any of them is a pure alert-accuracy false
    positive (there is no promote-PR mechanism to clear it through in the first place).

    First repo: unified-trading-ci (extracted from PM 2026-08-06 as "single-branch, main only", but
    both `main` and `live-defi-rollout` existed in practice and genuinely diverged — reconciled once
    2026-08-07, see unified_trading_ci_no_promotion_tiers_divergence_2026_08_07.md). Mirrors
    `_main_direct_repos()`/`_ldr_terminal_repos()`'s manifest-driven pattern (no hardcoded repo names
    beyond the fallback-empty case, so a future single-branch repo picks this up automatically).
    """
    if manifest_path is None:
        here = os.path.dirname(os.path.abspath(__file__))
        manifest_path = os.path.join(here, "..", "..", "workspace-manifest.json")
    out: set[str] = set()
    try:
        with open(manifest_path) as _mf:
            m = cast("dict[str, object]", json.load(_mf))
        repos = m.get("repositories")
        if isinstance(repos, dict):
            for name, cfg in cast("dict[str, object]", repos).items():
                if isinstance(cfg, dict) and cast("dict[str, object]", cfg).get("promotion_model") == "single_branch":
                    out.add(str(name))
    except (OSError, json.JSONDecodeError, ValueError):
        pass  # manifest unreadable → fall back to empty (prior behavior: no exemption)
    return out


def _branch_exists(repo: str, branch: str) -> bool:
    """True if origin/<branch> exists for the repo (404/error → False)."""
    return isinstance(_gh_json(f"repos/{OWNER}/{repo}/branches/{branch}"), dict)


def _workflow_present_on_ref(repo: str, name: str, ref: str) -> bool | None:
    """True/False if .github/workflows/<name> exists on <ref>; None on an unknown error.

    Gap 6 P2 (ci_pipeline_self_healing §Gap 6): a missing staging-backmerge-to-ldr.yml on the
    STAGING BRANCH is the documented Tier-C runaway cause — `push:[staging]` only fires from
    staging's own copy, so a file present on LDR but absent on staging silently never back-merges.
    Returns None (not False) on a non-200/404 status so a transient error never false-pages.
    """
    r = subprocess.run(
        ["gh", "api", "-i", f"repos/{OWNER}/{repo}/contents/.github/workflows/{name}?ref={ref}"],
        capture_output=True,
        text=True,
    )
    status = _parse_gh_api_i(r.stdout)[0]
    if status == 200:
        return True
    if status == 404:
        return False
    return None


class _Unmeasured:
    """Sentinel: the compare API call could not be evaluated this run (a transient/systemic `gh` error
    made `_gh_json` return None). This is DISTINCT from a measured `None` ("genuinely in sync"). The
    clear-diff must never treat an unmeasured pair as cleared — see `_emit_clear_diff`. A single
    module-level instance (`UNMEASURED`) so `is`-identity narrows cleanly."""


UNMEASURED = _Unmeasured()


def _lag(
    repo: str, base: str, head: str, now: dt.datetime, thresh_s: float, skip_ci_counts: bool
) -> tuple[int, float, str] | _Unmeasured | None:
    """Return (n_commits, oldest_age_s, oldest_msg) if lagging; None if measured-in-sync; UNMEASURED
    if the compare API call could not be evaluated (so callers never conflate error with in-sync)."""
    d = _gh_json(f"repos/{OWNER}/{repo}/compare/{base}...{head}")
    if not isinstance(d, dict):
        return UNMEASURED  # compare call failed (403/5xx/network) — UNKNOWN, not "in sync"
    # Squash-skew guard: a squash-merge keeps `head` ahead-by-commit-count of `base` even when the
    # tree content is byte-identical (the squashed commit on `base` is a new SHA, so the original
    # head commits stay "ahead"). The compare `files` array is the NET diff — empty means the
    # content already promoted, so there is NOTHING to page on regardless of how old the oldest
    # squashed commit is. Gate on real content here, mirroring the dashboard's files_changed gate.
    files = cast("dict[str, object]", d).get("files")
    if not isinstance(files, list):
        # `files` is inlined by the compare API only up to 300 files. Absent = a delta far too
        # big to be a squash artefact, so fall back to the raw window rather than go silent.
        # stderr, NOT stdout: branch-health.yml does REPORT=$(… --slack) and posts stdout
        # VERBATIM as the Slack message, so a diagnostic printed here lands in the alert body.
        print(
            f"   … {repo} {base}...{head}: compare omitted `files` (>300?) — aging the raw commit window",
            file=sys.stderr,
        )
        return _commit_window_age(cast("dict[str, object]", d), now, thresh_s, skip_ci_counts)
    if len(files) == 0:
        return None
    # Squash-WINDOW guard (forward LDR→staging ONLY): the Tier-C drain squash-merges the WHOLE
    # marker..LDR range atomically every ~15 min, so the net diff (`files`) is non-empty only
    # during the IN-FLIGHT window between a fresh LDR commit and its next drain tick. In that
    # window `compare.commits` still carries the ancient squash-skew commits (original LDR shas
    # the squash never replays), so `oldest`-age below is meaningless — it dates the already-
    # promoted-by-content tail, not the genuine delta. staging is advanced ONLY by the drain (a
    # real promotion), so a staging HEAD younger than the threshold PROVES the drain is live →
    # the delta is transient, not a stuck promotion. RESTRICTED to LDR→staging: `main` is also
    # advanced by `[skip ci]` ci-status/manifest writes (so its HEAD recency is NOT a promotion
    # signal — base-staleness there would false-negative a genuinely stuck staging→main), and the
    # two →LDR backmerge directions have base=live-defi-rollout which is ~always fresh.
    if base == "staging" and head == "live-defi-rollout":
        base_c = cast("dict[str, object]", cast("dict[str, object]", d).get("base_commit") or {})
        base_commit = cast("dict[str, object]", base_c.get("commit") or {})
        base_committer = cast("dict[str, object]", base_commit.get("committer") or {})
        base_ds = str(base_committer.get("date") or "")
        if base_ds:
            try:
                base_when = dt.datetime.fromisoformat(base_ds.replace("Z", "+00:00"))
            except ValueError:
                base_when = None
            if base_when is not None and (now - base_when).total_seconds() < thresh_s:
                return None  # staging advanced within threshold → drain live → transient in-flight delta
    return _content_delta_age(repo, head, files, now, thresh_s, skip_ci_counts)


def _excluded_from_forward(commit: dict[str, object], parents_n: int, skip_ci_counts: bool) -> bool:
    """True when a commit is not forward-promotable content (see _lag's two exclusions)."""
    if skip_ci_counts:
        return False
    if "[skip ci]" in str(commit.get("message") or ""):
        return True  # automation commit not meant to promote forward
    return parents_n > 1  # a merge commit is never forward-promotable content


def _last_touch(repo: str, head: str, fn: str, skip_ci_counts: bool) -> tuple[str, dt.datetime, str] | None:
    """Return (sha, when, subject) of the commit that LAST touched `fn` on `head`."""
    q = f"repos/{OWNER}/{repo}/commits?sha={quote(head, safe='')}&path={quote(fn, safe='')}&per_page=1"
    d = _gh_json(q)
    if not isinstance(d, list) or not d or not isinstance(d[0], dict):
        return None
    cd = cast("dict[str, object]", d[0])
    commit = cast("dict[str, object]", cd.get("commit") or {})
    sha = str(cd.get("sha") or "")
    parents = cast("list[object]", cd.get("parents") or [])
    if not sha or _excluded_from_forward(commit, len(parents), skip_ci_counts):
        return None
    author = cast("dict[str, object]", commit.get("author") or {})
    ds = str(author.get("date") or "")
    if not ds:
        return None
    try:
        when = dt.datetime.fromisoformat(ds.replace("Z", "+00:00"))
    except ValueError:
        return None
    full = str(commit.get("message") or "")
    return sha, when, (full.splitlines()[0] if full else "")


def _content_delta_age(
    repo: str, head: str, files: list[object], now: dt.datetime, thresh_s: float, skip_ci_counts: bool
) -> tuple[int, float, str] | None:
    """Age the REAL content delta, not the squash-skew commit window.

    `compare(base...head).commits` spans the ENTIRE squash window: an LDR→main promote is a
    SQUASH, so the original LDR shas are never replayed onto main and stay "ahead" forever even
    though their content IS promoted. Aging over that window dates a GHOST — and a ghost never
    gets younger, so the `age < thresh_s` test below could never clear and the pair paged every
    cooldown, permanently. Measured 2026-07-16: unified-trading-library reported "144 commits,
    oldest 28403m old" (20 days) when its real net diff was 7 files last touched 25 MINUTES
    earlier; 7 of 8 alert lines were this artefact, and the noise buried the one true finding
    (mtds main→LDR, genuinely stuck 18.5h behind a CONFLICTING PR).

    The honest question is not "how old is the oldest commit still listed as ahead" but "how
    long has the still-unpromoted CONTENT been waiting" — so age the commits that last touched
    each file in the NET diff (`files`), which by construction excludes promoted ghosts.

    SSOT this restores: codex/08-workflows/ci-cd-flow.md ("trust a content/path check, not
    `ahead_by`") + codex/03-observability/monitoring-control-plane.md ("content delta = changed
    -file count, NEVER squash-skewed commit counts").
    """
    names = [
        fn for f in files if isinstance(f, dict) and (fn := str(cast("dict[str, object]", f).get("filename") or ""))
    ]
    if not names:
        return None
    if len(names) > _MAX_DELTA_FILES:
        # stderr, NOT stdout — branch-health.yml posts this script's stdout verbatim as the
        # Slack message body (REPORT=$(… --slack)). Keep the cap disclosure in the workflow log
        # (so the bound is never silent) without leaking it into the alert.
        print(
            f"   … {repo} {head}: sampling {_MAX_DELTA_FILES} of {len(names)} changed files for delta age",
            file=sys.stderr,
        )
        names = names[:_MAX_DELTA_FILES]
    seen: dict[str, tuple[dt.datetime, str]] = {}
    for fn in names:
        lt = _last_touch(repo, head, fn, skip_ci_counts)
        if lt is not None:
            sha, when, subject = lt
            seen[sha] = (when, subject)
    # Every last-touch excluded (all [skip ci] / merge commits) → no promotable delta.
    if not seen:
        return None
    oldest_sha = min(seen, key=lambda s: seen[s][0])
    when, omsg = seen[oldest_sha]
    age = (now - when).total_seconds()
    if age < thresh_s:
        return None
    return len(seen), age, omsg


def _commit_window_age(
    d: dict[str, object], now: dt.datetime, thresh_s: float, skip_ci_counts: bool
) -> tuple[int, float, str] | None:
    """Age over the raw compare window — ONLY for a diff too large for `files` to be inlined.

    Squash-ghost-prone by construction (see _content_delta_age), so it is deliberately NOT the
    default path: a >300-file delta is never a ghost artefact, it is a genuinely enormous
    un-promoted change, and paging on it beats going silent.
    """
    commits = cast("list[object]", d.get("commits") or [])
    relevant: list[tuple[dt.datetime, str]] = []
    for c in commits:
        if not isinstance(c, dict):
            continue
        cd = cast("dict[str, object]", c)
        commit = cast("dict[str, object]", cd.get("commit") or {})
        msg = str(commit.get("message") or "").splitlines()[0] if commit.get("message") else ""
        if not skip_ci_counts and "[skip ci]" in str(commit.get("message") or ""):
            continue  # automation commit not meant to promote forward
        # Backmerge MERGE-commit exclusion (forward directions only). `compare/<base>...LDR` for a
        # forward pair is DOMINATED by the drift-tick's backmerge merge-commits ("Merge
        # remote-tracking branch 'origin/main'/'origin/staging' into _backmerge") — these live on LDR
        # ONLY (never promote forward; the already-promoted content they carry is on main/staging by
        # sha, so it is NOT in this compare). Aging over them makes the oldest "un-propagated" commit
        # the ancient first backmerge → a perpetual false page (incident 2026-06-24: alerting/mtds/
        # greeks LDR->main, oldest 67m-18580m, ALL "into _backmerge"). A merge commit (parents>1) is
        # never forward-promotable content, so skip it; the genuine forward delta is the non-merge
        # commits that remain.
        parents = cast("list[object]", cd.get("parents") or [])
        if not skip_ci_counts and len(parents) > 1:
            continue
        author = cast("dict[str, object]", commit.get("author") or {})
        ds = str(author.get("date") or "")
        if not ds:
            continue
        try:
            when = dt.datetime.fromisoformat(ds.replace("Z", "+00:00"))
        except ValueError:
            continue
        relevant.append((when, msg))
    if not relevant:
        return None
    oldest, omsg = min(relevant, key=lambda x: x[0])
    age = (now - oldest).total_seconds()
    if age < thresh_s:
        return None
    return len(relevant), age, omsg


def _open_promote_pr(repo: str) -> dict[str, object] | None:
    """The OPEN `chore(promote)`-titled PR to `main` for this repo, or None if none exists.

    Shared lookup for `_provenance_blocked` and `_promote_pr_cause` — one PR-list fetch serves
    both cause checks for the same lagging LDR→main pair instead of two independent calls.

    HYDRATED via a single-PR GET (2026-08-10). GitHub's PR *list* endpoint does NOT return
    `mergeable` / `mergeable_state` — only `GET /pulls/{number}` does, because mergeability is
    computed on demand. `_promote_pr_cause`'s `blocked_conflicting` branch keys on
    `mergeable_state`, so fed a list-derived dict that branch was DEAD CODE: every genuinely
    BLOCKED promote PR fell through to "cause unknown — investigate directly" instead of the
    actionable "🚧 BLOCKED/CONFLICTING — resolve the failing required check". Measured live on
    market-tick-data-service PR #939 (248m lag, 14 commits): list → `mergeable_state` ABSENT,
    single GET → `"blocked"`. That is the recurring "PROMOTION LAG cause unknown" alert class.
    Its unit tests missed it because they hand-build the PR dict WITH `mergeable_state` set, a
    shape the production path never produces — see the hydration test in
    `test_promotion_lag_monitor_promote_pr_cause.py`.

    Costs one extra API call per LAGGING repo per run: this is only reached for a pair that is
    already going to page, so a healthy fleet still pays nothing. Falls back to the list entry if
    the GET fails, so a hydration failure can never regress behaviour below today's. Note GitHub
    computes mergeability asynchronously — a cold PR can answer `mergeable_state: "unknown"`,
    which correctly matches no branch and leaves the existing SIT/unknown dispatch intact.
    """
    prs = _gh_json(f"repos/{OWNER}/{repo}/pulls?state=open&base=main&per_page=20")
    if not isinstance(prs, list):
        return None
    for pr in prs:
        if isinstance(pr, dict) and str(cast("dict[str, object]", pr).get("title") or "").startswith("chore(promote)"):
            listed = cast("dict[str, object]", pr)
            num = listed.get("number")
            if isinstance(num, int):
                full = _gh_json(f"repos/{OWNER}/{repo}/pulls/{num}")
                if isinstance(full, dict):
                    return cast("dict[str, object]", full)
            return listed
    return None


def _provenance_blocked(repo: str, pr: dict[str, object] | None = None) -> bool:
    """True when this repo has an OPEN promote PR the fleet bot refused to arm on provenance.

    Cheap + only called for a pair that is ALREADY going to page, so a healthy fleet pays nothing.
    Fail-CLOSED to False: if the lookup fails we report the ordinary lag line rather than claim a
    block that may not exist. `pr` lets the caller pass an already-fetched `_open_promote_pr`
    result (avoids a second identical PR-list fetch); omitted/None fetches it here (back-compat
    with the pre-refactor single-arg call).
    """
    p = pr if pr is not None else _open_promote_pr(repo)
    if p is None:
        return False
    num = p.get("number")
    if not isinstance(num, int):
        return False
    comments = _gh_json(f"repos/{OWNER}/{repo}/issues/{num}/comments?per_page=30")
    if not isinstance(comments, list):
        return False
    for c in comments:
        if isinstance(c, dict) and _PROVENANCE_MARKER in str(cast("dict[str, object]", c).get("body") or ""):
            return True
    return False


def _sit_fleet_status(repo: str, sha: str) -> str | None:
    """The `sit-gate/fleet-green` commit-status `state` on `sha` ("pending"/"success"/"failure"/
    "error"), or None if the status was never posted (non-`ldr_main` repo, or not reached yet) or
    the lookup failed."""
    d = _gh_json(f"repos/{OWNER}/{repo}/commits/{sha}/status")
    if not isinstance(d, dict):
        return None
    statuses = cast("list[object]", cast("dict[str, object]", d).get("statuses") or [])
    for s in statuses:
        if isinstance(s, dict) and cast("dict[str, object]", s).get("context") == _SIT_FLEET_CONTEXT:
            state = cast("dict[str, object]", s).get("state")
            return state if isinstance(state, str) else None
    return None


def _promote_pr_cause(repo: str, pr: dict[str, object] | None) -> tuple[str, int | None]:
    """Classify WHY an LDR→main pair is lagging, given the (possibly None) open promote PR.

    Returns (cause, pr_number). cause is one of "no_promote_pr", "blocked_conflicting",
    "sit_gated_inflight", "unknown" — the four causes `silent_failures_surfacing_as_generic_
    promotion_lag_2026_07_17.md` P2 names (the provenance block is a FIFTH, checked separately by
    the caller via `_provenance_blocked` — a deliberate bot refusal is never "unknown", so it takes
    priority and this function is not even called for it). Restricted to LDR→main by the caller —
    the only direction with a promote-PR mechanism at all (mirrors `_provenance_blocked`'s scope).
    """
    if pr is None:
        return "no_promote_pr", None
    num = pr.get("number")
    pr_num = num if isinstance(num, int) else None
    mergeable_state = str(pr.get("mergeable_state") or "")
    if mergeable_state in ("dirty", "blocked"):
        return "blocked_conflicting", pr_num
    head = cast("dict[str, object]", pr.get("head") or {})
    sha = head.get("sha")
    if isinstance(sha, str) and sha and _sit_fleet_status(repo, sha) == "pending":
        return "sit_gated_inflight", pr_num
    return "unknown", pr_num


def _ldr_main_finding(repo: str, label: str, n: int, age: float, omsg: str) -> tuple[str, bool, str | None]:
    """Build the LDR→main finding line + its (blocked, cause) classification.

    Isolated from `main()`'s loop to keep the loop's cyclomatic complexity under the ruff cap — a
    provenance/SIT-gated/no-PR/blocked-conflicting/unknown 5-way dispatch reads better as one
    function than folded into the per-direction loop. Returns (finding_line, provenance_blocked,
    cause) — `cause` is None when provenance-blocked (a deliberate bot refusal, not one of the P2
    causes) and otherwise one of `_promote_pr_cause`'s four values.
    """
    age_m = int(age // 60)
    pr = _open_promote_pr(repo)
    # A provenance-blocked forward pair is NOT a wedged pipeline — the bot deliberately refused to
    # arm it and the remedy is specific. Say so, so nobody "unblocks" it by hand-arming auto-merge
    # (which promotes the bypassed code AND launders it past the baseline — 2026-07-16).
    if _provenance_blocked(repo, pr):
        return (
            f"{repo} {label}: ⛔ BLOCKED by the provenance gate — non-quickmerge CODE on LDR "
            f"({n} change(s), oldest {age_m}m). NOT a stuck pipeline. If the bypass is the "
            f"LDR tip: `quickmerge --agent --files` it. If it is MID-HISTORY (a later commit landed on "
            f"top): `scripts/cicd/reprovenance_bypass.sh <sha> --push` (re-ship/revert canNOT clear a "
            f"mid-history bypass — the sha stays in-range). Do NOT hand-arm auto-merge.",
            True,
            None,
        )
    # P2 (silent_failures_surfacing_as_generic_promotion_lag_2026_07_17.md line 165): name a cause
    # per line instead of implying "just slow". A line that cannot name a cause says so explicitly
    # ("cause unknown"), never silently falls back to the old generic wording.
    cause, pr_num = _promote_pr_cause(repo, pr)
    if cause == "sit_gated_inflight":
        line = (
            f"{repo} {label}: 🕒 SIT-gated in-flight — promote PR #{pr_num} awaiting "
            f"`sit-gate/fleet-green` ({n} change(s), oldest {age_m}m). Full SIT round-trip "
            f"is ~156m; no action needed unless this exceeds that."
        )
    elif cause == "no_promote_pr":
        line = (
            f"{repo} {label}: ❓ no promote PR open — a promote has not been dispatched yet "
            f"({n} change(s), oldest {age_m}m). Check `ldr-to-main-promote-fleet.yml`'s "
            f"latest tick for this repo."
        )
    elif cause == "blocked_conflicting":
        line = (
            f"{repo} {label}: 🚧 promote PR #{pr_num} BLOCKED/CONFLICTING "
            f"({n} change(s), oldest {age_m}m). Resolve the merge conflict or failing "
            f"required check on the PR."
        )
    else:
        line = (
            f"{repo} {label}: cause unknown — {n} commit(s), oldest {age_m}m old — "
            f'"{omsg[:60]}" (promote PR #{pr_num} state matched none of the known causes; '
            f"investigate directly)"
        )
    return line, False, cause


def _write_firestore_promotion_lag(
    repo_lags: dict[str, dict[str, object]],
    now_iso: str,
    project_id: str,
) -> None:
    try:
        from google.api_core.exceptions import GoogleAPICallError  # noqa: imports-inside-functions
        from google.cloud import (  # noqa: TID251, RUF100, I001  # noqa: imports-inside-functions  # noqa: cloud-sdk-direct
            firestore,
        )

        client = firestore.Client(project=project_id)
        for repo, lags in repo_lags.items():
            doc_ref = client.collection("repo_state").document(repo)
            doc_ref.set({"promotion_lag": {"lags": lags, "checked_at": now_iso}}, merge=True)
    except (ImportError, GoogleAPICallError):  # Firestore unavailable → best-effort write
        pass


# ── Per-pair clear-diff (name WHICH pair cleared, as it clears) ───────────────────────────
# The fleet-wide "any-lag → no-lag" edge announced only "all branch-pairs back in sync" and only
# when the WHOLE fleet went green — so a single repo clearing while another still lagged was never
# announced, and the all-clear never named the repair. These helpers persist the set of currently-
# lagging pairs across runs and diff prev→current: a pair present last run and absent this run is a
# CLEAR, named individually. Pure + stdlib so they unit-test without `gh`.
# SSOT: codex/04-architecture/ci-alerting.md (recovery-gated all-clears, per-condition dedup).


def _lagging_summaries(repo_lags: dict[str, dict[str, object]]) -> dict[str, str]:
    """Map every CURRENTLY-lagging branch-pair to `{"repo|label": one-line summary}`.

    The summary is what a later CLEAR announces ("was N commit(s), oldest Mm"). Only per-direction
    entries with `lag is True` are included — the non-pair bookkeeping entries (e.g.
    `staging_backmerge_present`, whose value has no `lag` key) are skipped.
    """
    out: dict[str, str] = {}
    for repo, labels in repo_lags.items():
        for label, info in labels.items():
            if not isinstance(info, dict):
                continue
            d = cast("dict[str, object]", info)
            if d.get("lag") is not True:
                continue
            n = d.get("n_commits")
            age_s = d.get("age_s")
            n_i = n if isinstance(n, int) else 0
            age_m = int(age_s // 60) if isinstance(age_s, (int, float)) else 0
            blocked = " (was provenance-blocked)" if d.get("provenance_blocked") is True else ""
            out[f"{repo}|{label}"] = f"{repo} {label} — was {n_i} commit(s), oldest {age_m}m{blocked}"
    return out


def _evaluated_keys(repo_lags: dict[str, dict[str, object]]) -> set[str]:
    """Every branch-pair actually PROBED this run — any per-direction entry carrying a `lag` verdict
    (True or False, incl. unmeasured which is `lag: False, unmeasured: True`). Excludes the non-pair
    bookkeeping entries (`staging_backmerge_present`, no `lag` key) and any pair that was `continue`d
    (main-direct/staging-dormant) so never got an entry — those are 'no longer monitored', not cleared.
    """
    out: set[str] = set()
    for repo, labels in repo_lags.items():
        for label, info in labels.items():
            if isinstance(info, dict) and "lag" in cast("dict[str, object]", info):
                out.add(f"{repo}|{label}")
    return out


def _unmeasured_keys(repo_lags: dict[str, dict[str, object]]) -> set[str]:
    """Pairs whose compare probe FAILED this run (`unmeasured is True`) — status unknown, never a clear."""
    out: set[str] = set()
    for repo, labels in repo_lags.items():
        for label, info in labels.items():
            if isinstance(info, dict) and cast("dict[str, object]", info).get("unmeasured") is True:
                out.add(f"{repo}|{label}")
    return out


def _cleared_keys(prev: dict[str, str], evaluated: set[str], lagging: set[str], unmeasured: set[str]) -> list[str]:
    """Pairs that just cleared: lagging last run (`prev`) AND this run POSITIVELY measured in sync.

    A pair clears ONLY when it was AFFIRMATIVELY re-checked and found not-lagging — i.e. it is in
    `evaluated`, not in `lagging`, and not in `unmeasured`. This deliberately excludes two false-clear
    classes the fleet-wide edge never hit: (1) a transient compare-API error (`unmeasured` — carried
    forward, not cleared) and (2) a pair no longer monitored because its repo toggled main-direct /
    staging-dormant (absent from `evaluated` — dropped, not announced as "back in sync").
    """
    return [k for k in sorted(prev) if k in evaluated and k not in lagging and k not in unmeasured]


def _load_lag_state(path: str) -> dict[str, str]:
    """Load the previous run's lagging map ({key: summary}).

    Tolerates absent / corrupt / OLD-SCHEMA (`{"lag": bool}`, pre per-pair) files → returns {} so a
    first run after deploy never false-fires a CLEAR. Only a well-formed `{"lagging": {str: str}}` is
    honoured.
    """
    try:
        with open(path) as f:
            raw = cast("object", json.load(f))
    except (OSError, ValueError):
        return {}
    if not isinstance(raw, dict):
        return {}
    lagging = cast("dict[str, object]", raw).get("lagging")
    if not isinstance(lagging, dict):
        return {}
    out: dict[str, str] = {}
    for k, v in cast("dict[str, object]", lagging).items():
        if isinstance(k, str) and isinstance(v, str):
            out[k] = v
    return out


def _write_lag_state(path: str, curr: dict[str, str]) -> None:
    """Persist the current lagging map for the next run's clear-diff. Best-effort."""
    try:
        with open(path, "w") as f:
            json.dump({"lagging": curr}, f)
    except OSError:
        pass


def _cleared_dedup_key(cleared_keys: list[str]) -> str:
    """A per-cleared-SET dedup key so two distinct clears each post once.

    notify-slack dedups on `dedup_key` ALONE (not key+message), so a static key would let the first
    clear swallow a second repo's clear within the cooldown. A short stable digest of the cleared set
    gives each distinct set its own lane; the SAME pair re-clearing within the cooldown is (correctly)
    flap-suppressed. sha256 (not md5/sha1) to avoid the weak-hash lint; this is an identity, not a
    security boundary.
    """
    joined = ",".join(sorted(cleared_keys))
    digest = hashlib.sha256(joined.encode("utf-8")).hexdigest()[:12]
    return f"promotion-lag-cleared:{digest}"


def _build_cleared_block(cleared_keys: list[str], prev: dict[str, str], still_lagging: int) -> str:
    """The CLEARED payload written to --cleared-out: line 1 = dedup key, line 2 = Slack message.

    Empty string when nothing cleared (the workflow reads a 0-byte file as cleared=false). The
    message uses literal ``\\n`` line breaks to match the lag report — branch-health.yml passes it
    VERBATIM to notify-slack, which renders ``\\n`` as Slack line breaks.
    """
    if not cleared_keys:
        return ""
    key = _cleared_dedup_key(cleared_keys)
    header = f":ballot_box_with_check: *PROMOTION LAG CLEARED* — {len(cleared_keys)} branch-pair(s) back in sync"
    body = "\\n".join(f"  • {prev[k]}" for k in cleared_keys)
    tail = f"\\n({still_lagging} pair(s) still lagging)" if still_lagging else "\\n— all branch-pairs now in sync"
    message = header + "\\n" + body + tail
    return key + "\n" + message + "\n"


def _emit_clear_diff(repo_lags: dict[str, dict[str, object]], state_in: str, state_out: str, cleared_out: str) -> None:
    """Diff prev→current per branch-pair and (opt-in) persist state + write the named CLEARED block.

    Three run-states per pair drive the diff (see `_cleared_keys`): affirmatively LAGGING, affirmatively
    IN-SYNC (the only state that clears), and UNMEASURED (compare probe failed). A prev-lagging pair that
    is UNMEASURED this run is carried FORWARD into the persisted set (not cleared, not forgotten) so it
    re-decides on the next successful probe; a prev pair that is no longer monitored (absent from
    `evaluated`) is simply dropped.
    """
    lagging = _lagging_summaries(repo_lags)  # affirmatively lagging → {key: summary}
    prev = _load_lag_state(state_in) if state_in else {}
    unmeasured = _unmeasured_keys(repo_lags)
    # Carry a prev-lagging pair forward when this run could not measure it (transient gh error).
    carried = {k: prev[k] for k in unmeasured if k in prev}
    new_state = {**lagging, **carried}
    if cleared_out:
        cleared_keys = _cleared_keys(prev, _evaluated_keys(repo_lags), set(lagging), unmeasured)
        block = _build_cleared_block(cleared_keys, prev, still_lagging=len(new_state))
        try:
            with open(cleared_out, "w") as f:
                f.write(block)
        except OSError:
            pass
    if state_out:
        _write_lag_state(state_out, new_state)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--threshold-min", type=int, default=60)
    ap.add_argument(
        "--ldr-main-threshold-min",
        type=int,
        default=120,
        help="LDR→main lag threshold (ALL repos). The forward-promote floor is a ~40-min throttled "
        "promote cadence — plus a full SIT round-trip (~156m) for SIT-gated repos — so the base 60m "
        "self-clears on a healthy promote. Backmerge/staging directions keep --threshold-min.",
    )
    ap.add_argument("--now-iso", default="", help="UTC now (no wallclock in CI sandbox); else uses gh server time")
    ap.add_argument("--slack", action="store_true")
    ap.add_argument(
        "--state-in",
        default="",
        help="Path to the PREVIOUS run's lagging-state JSON — the clear-diff baseline (missing/old-schema → none).",
    )
    ap.add_argument(
        "--state-out",
        default="",
        help="Write the CURRENT lagging-state JSON here for the next run's clear-diff.",
    )
    ap.add_argument(
        "--cleared-out",
        default="",
        help="Write the named CLEARED Slack block here (line 1 = dedup key, line 2 = message); empty if none cleared.",
    )
    args = ap.parse_args()
    thresh_s = cast(int, args.threshold_min) * 60.0
    ldr_main_thresh_s = cast(int, args.ldr_main_threshold_min) * 60.0
    now_iso = cast(str, args.now_iso)
    as_slack = cast(bool, args.slack)

    # Persisted ETag cache (CI: a path under actions/cache; else in-memory only).
    cache_file = os.environ.get("GH_ETAG_CACHE_FILE")
    if cache_file:
        load_etag_cache(cache_file)

    if now_iso:
        now = dt.datetime.fromisoformat(now_iso.replace("Z", "+00:00"))
    else:
        # GitHub server time from a HEAD request header avoids relying on a wallclock
        r = subprocess.run(["gh", "api", "-i", "rate_limit"], capture_output=True, text=True)
        now = None
        for line in r.stdout.splitlines():
            if line.lower().startswith("date:"):
                try:
                    now = dt.datetime.strptime(line[5:].strip(), "%a, %d %b %Y %H:%M:%S GMT").replace(tzinfo=dt.UTC)
                except ValueError:
                    now = None
                break
        if now is None:
            print("could not resolve server time; pass --now-iso")
            return 0

    findings: list[str] = []
    repo_lags: dict[str, dict[str, object]] = {}  # structured data for Firestore write-through
    # Main-direct repos (PM + ldr_main cutover): staging is toggled off, so their LDR↔staging
    # directions are intentionally dormant — skip them so the bypassed staging path never shows
    # as "stuck" on /repos or in Slack.
    main_direct = _main_direct_repos()
    # ldr_terminal repos (agent-orchestrator, 2026-08-05): `main` is a frozen historical ref that
    # nothing deploys from, so BOTH main-facing directions are intentionally dormant too.
    ldr_terminal = _ldr_terminal_repos()
    # single_branch repos (unified-trading-ci, 2026-08-07): no LDR/staging promotion pipeline at
    # all — skip the repo ENTIRELY (all four directions + the staging-backmerge-workflow-presence
    # check below), not just one axis. See _single_branch_repos().
    single_branch = _single_branch_repos()
    for repo in _repos():
        if repo in single_branch:
            continue  # no promotion pipeline exists for this repo — nothing to monitor
        repo_lags[repo] = {}
        directions = [
            ("LDR→main", "main", "live-defi-rollout", False),
            ("LDR→staging", "staging", "live-defi-rollout", False),
            ("main→LDR", "live-defi-rollout", "main", True),
            ("staging→LDR", "live-defi-rollout", "staging", True),
        ]
        for label, base, head, skip_ci_counts in directions:
            if repo in main_direct and "staging" in label:
                continue  # main-direct (PM Option-B + ldr_main cutover): staging toggled off, not stuck
            if repo in ldr_terminal and "main" in label:
                continue  # ldr_terminal: `main` is frozen/unconsumed, both main-facing directions dormant
            # LDR→main gets a longer threshold for ALL repos (120m default): the forward-promote
            # floor is a ~40-min throttled promote cadence — plus a full SIT round-trip (~156m) for
            # SIT-gated repos — so the base 60m self-clears on a healthy promote. Backmerge/staging
            # directions keep the base --threshold-min (60m).
            eff_thresh = ldr_main_thresh_s if label == "LDR→main" else thresh_s
            res = _lag(repo, base, head, now, eff_thresh, skip_ci_counts)
            if res is UNMEASURED:
                # The compare call failed this run — status UNKNOWN, NOT a clear. Record it distinctly
                # so the clear-diff carries a prev-lagging pair FORWARD instead of false-announcing it
                # cleared (a transient 403/5xx must never post a "back in sync" for a still-stuck pair).
                repo_lags[repo][label] = {"lag": False, "unmeasured": True}
            elif isinstance(res, tuple):
                n, age, omsg = res
                # LDR→main is the only direction with a promote-PR mechanism, so it's the only one
                # that can name a cause (provenance-blocked / SIT-gated-in-flight / no-promote-PR /
                # blocked-conflicting / unknown — see `_ldr_main_finding`). The other 3 directions
                # (staging squash-merge, both backmerges) are automation-driven with no PR to
                # inspect, so they keep the plain "N commit(s), oldest Xm old" line.
                if label == "LDR→main":
                    line, blocked, cause = _ldr_main_finding(repo, label, n, age, omsg)
                else:
                    line = f'{repo} {label}: {n} commit(s), oldest {int(age // 60)}m old — "{omsg[:60]}"'
                    blocked, cause = False, None
                findings.append(line)
                repo_lags[repo][label] = {
                    "n_commits": n,
                    "age_s": age,
                    "oldest_msg": omsg,
                    "lag": True,
                    "provenance_blocked": blocked,
                    "cause": cause,
                }
            else:
                repo_lags[repo][label] = {"lag": False}

        # Gap 6 P2: staging-backmerge-to-ldr.yml MUST exist on the STAGING branch (push:[staging]
        # only fires from staging's own copy). A missing copy = the documented Tier-C runaway cause
        # → page proactively (before it strands a repo), not just react via the runaway breaker.
        if repo not in main_direct and _branch_exists(repo, "staging"):
            present = _workflow_present_on_ref(repo, "staging-backmerge-to-ldr.yml", "staging")
            repo_lags[repo]["staging_backmerge_present"] = {"present": present}
            if present is False:
                findings.append(
                    f"{repo} staging-backmerge-to-ldr.yml MISSING on the staging branch — "
                    f"staging→LDR back-merge will never fire (Tier-C runaway risk); roll out the "
                    f"template + promote it to staging"
                )

        # NOTE: stuck/conflict promotion PRs are NOT detected here — `ci-failure-watcher` is the
        # SSOT for those (it also auto-recovers + escalates them); a dangling staging lock is owned
        # by `sit-starvation-detector.yml`. Both were stripped from this monitor 2026-06-18 to stop
        # one event paging from three detectors (alert_quality_audit_2026_06_18). This stays a PURE
        # branch-pair lag monitor.

    # Persist the warmed ETag cache so the next run's unchanged compares are free 304s.
    if cache_file:
        save_etag_cache(cache_file)

    # Firestore write-through — best-effort; never blocks the monitor on SDK/credential absence.
    gcp_project = os.environ.get("GCP_PROJECT_ID")
    if gcp_project:
        _write_firestore_promotion_lag(repo_lags, now.isoformat(), gcp_project)

    # Per-pair clear-diff (opt-in via the state/cleared paths). MUST run before the all-green
    # early-return: a pair clearing is exactly when `findings` shrinks (possibly to empty), so the
    # diff has to see both the lagging and the fully-synced case.
    state_in = cast(str, args.state_in)
    state_out = cast(str, args.state_out)
    cleared_out = cast(str, args.cleared_out)
    if state_in or state_out or cleared_out:
        _emit_clear_diff(repo_lags, state_in, state_out, cleared_out)

    if not findings:
        print(
            f"✅ promotion-lag: all branches in sync "
            f"(LDR→main within {int(ldr_main_thresh_s // 60)}m, backmerge/staging within {int(thresh_s // 60)}m)"
        )
        return 0

    if as_slack:
        # ── ERROR-POINTER MESSAGE STANDARD (alert_quality_audit_2026_06_18) ──────────
        # header = WHAT + the number(s); ≤N lines of load-bearing facts (CAPPED — NOT an
        # audit dump); exactly ONE deep-link to the AUTHORITATIVE surface; CLI hint secondary.
        # Surface routing (monitoring_control_plane_master § Division-of-surfaces): a CI/CD
        # pipeline condition routes to the deployment-ui CI/CD Repos page (`/repos`), the
        # roll-up surface where per-repo promotion state lives. (deployment-ui has no stable
        # public domain yet — Cloud-Run hosted — so we name the ROUTE, not a fabricated host;
        # a worker opens deployment-ui then `/repos`.) Promotion lag is fundamentally a
        # branch-pair compare → also GitHub-authoritative, so the secondary pointer is the
        # exact `gh api compare` the operator runs to inspect a specific pair.
        # Transition-only firing is handled at the EMIT layer: the workflow passes a stable
        # dedup_key + cooldown to notify-slack, so a standing lag pages on the 60m-CROSSING
        # and is suppressed until it clears + recrosses.
        _m = int(thresh_s // 60)
        _max_lines = 6
        repos_affected = sorted({f.split()[0] for f in findings})
        header = (
            f":hourglass_flowing_sand: *PROMOTION LAG > {_m}m* — "
            f"{len(findings)} branch-pair(s) across {len(repos_affected)} repo(s) un-propagated"
        )
        body_lines = [f"  • {f}" for f in findings[:_max_lines]]
        if len(findings) > _max_lines:
            body_lines.append(f"  • … +{len(findings) - _max_lines} more (full list on the surface below)")
        pointer = "→ open *deployment-ui* → CI/CD Repos page (`/repos`) for per-repo promotion state"
        cli_hint = "  (CLI: `gh api repos/IggyIkenna/<repo>/compare/<base>...<head>` to inspect a specific pair)"
        print(header + "\\n" + "\\n".join(body_lines) + "\\n" + pointer + "\\n" + cli_hint)
    else:
        print(f"⚠️  promotion lag > {int(thresh_s // 60)}m ({len(findings)}):")
        for f in findings:
            print(f"  - {f}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
