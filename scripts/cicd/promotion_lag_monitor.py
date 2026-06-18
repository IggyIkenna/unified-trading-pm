#!/usr/bin/env python3
"""Promotion-lag monitor — alert when LDR↔staging↔main fall out of sync for > N hours.

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
PM is treated main-direct (Option B) — its staging direction is skipped.

Stdlib + `gh` only. Prints a human report; with `--slack` prints a Slack-formatted block (the
workflow posts it). Exit 1 if any lag exceeds the threshold (so a required-check/alert can gate).

Usage:
    promotion_lag_monitor.py [--threshold-min 60] [--now-iso 2026-06-09T07:00:00Z] [--slack]
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
from typing import cast

OWNER = "IggyIkenna"

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


def _lag(
    repo: str, base: str, head: str, now: dt.datetime, thresh_s: float, skip_ci_counts: bool
) -> tuple[int, float, str] | None:
    """Return (n_commits, oldest_age_s, oldest_msg) for head-commits-not-on-base, or None."""
    d = _gh_json(f"repos/{OWNER}/{repo}/compare/{base}...{head}")
    if not isinstance(d, dict):
        return None
    # Squash-skew guard: a squash-merge keeps `head` ahead-by-commit-count of `base` even when the
    # tree content is byte-identical (the squashed commit on `base` is a new SHA, so the original
    # head commits stay "ahead"). The compare `files` array is the NET diff — empty means the
    # content already promoted, so there is NOTHING to page on regardless of how old the oldest
    # squashed commit is. Gate on real content here, mirroring the dashboard's files_changed gate.
    files = cast("dict[str, object]", d).get("files")
    if isinstance(files, list) and len(files) == 0:
        return None
    commits = cast("list[object]", cast("dict[str, object]", d).get("commits") or [])
    relevant: list[tuple[dt.datetime, str]] = []
    for c in commits:
        if not isinstance(c, dict):
            continue
        cd = cast("dict[str, object]", c)
        commit = cast("dict[str, object]", cd.get("commit") or {})
        msg = str(commit.get("message") or "").splitlines()[0] if commit.get("message") else ""
        if not skip_ci_counts and "[skip ci]" in str(commit.get("message") or ""):
            continue  # automation commit not meant to promote forward
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


def _lock_dangle(now: dt.datetime, dangle_min: int = 30) -> str | None:
    """Flag a DANGLING staging lock: `locked` held with `locked_since` older than dangle_min.

    A staging lock should clear within one SIT cycle (~15 min); a longer hold means the
    unlock mechanism (`sit-debounce-trigger`) stalled — the exact liveness gap behind the
    2026-06-10 ~1.5h dangle (the `*/5` cron is GitHub-throttled to ~75 min and was being
    displaced out of the `manifest-update` concurrency group). This check runs independently
    of that workflow, so it pages even when the unlock path is wedged. Returns a finding
    string (which triggers the Slack alert + non-zero exit) or None.
    """
    here = os.path.dirname(os.path.abspath(__file__))
    mpath = os.path.join(here, "..", "..", "workspace-manifest.json")
    try:
        with open(mpath) as _mf:
            m = cast("dict[str, object]", json.load(_mf))
    except (OSError, json.JSONDecodeError):
        return None
    ss = cast("dict[str, object]", m.get("staging_status") or {})
    if not ss.get("locked"):
        return None
    reason = str(ss.get("locked_reason") or "?")
    pending = cast("list[object]", ss.get("pending_repos") or [])
    since = ss.get("locked_since")
    if not since:
        return f"staging lock HELD with NO locked_since timestamp (reason: {reason}; pending={pending})"
    try:
        when = dt.datetime.fromisoformat(str(since).replace("Z", "+00:00"))
    except ValueError:
        return None
    age_min = (now - when).total_seconds() / 60.0
    if age_min < dangle_min:
        return None
    return (
        f"staging lock DANGLING {int(age_min)}m (> {dangle_min}m) — reason: {reason}; "
        f"pending_repos={pending}. Unlock mechanism (sit-debounce-trigger) likely stalled; "
        "recover via `gh workflow run sit-debounce-trigger.yml -f drain_pending=true`."
    )


_PROMOTION_BASES = ("staging", "main")


def _is_promotion_pr(base_ref: str, head_ref: str) -> bool:
    """A promote / dep-update PR worth watching for a conflict wall: into staging/main, the
    standing LDR→main drain, or a dependency-update fan-out branch."""
    return base_ref in _PROMOTION_BASES or head_ref == "live-defi-rollout" or head_ref.startswith("dep-update/")


def _classify_stuck_pr(repo: str, pr: dict[str, object], now: dt.datetime, thresh_s: float) -> str | None:
    """Pure: a finding string if this PR is a CONFLICT WALL (mergeable_state=='dirty') parked
    longer than thresh_s, else None.

    Closes the "lack alerts" gap (promotion_queue_conflict_wall_pileup_2026_06_17.md): a promote /
    dep-update PR that goes `dirty` (CONFLICTING) sits invisibly for hours — the promote bots treat
    it as a conflict to (maybe) resolve, the orchestrator backlog is plan-driven (never ingests open
    PRs), and the existing lag monitor only watches branch-pair propagation, not PR mergeability. We
    alert on `dirty` (the conflict-wall signal), NOT `blocked` (which is normally checks-in-progress).
    """
    if str(pr.get("mergeable_state") or "") != "dirty":
        return None
    base = cast("dict[str, object]", pr.get("base") or {})
    head = cast("dict[str, object]", pr.get("head") or {})
    base_ref = str(base.get("ref") or "")
    head_ref = str(head.get("ref") or "")
    if not _is_promotion_pr(base_ref, head_ref):
        return None
    ds = str(pr.get("updated_at") or pr.get("created_at") or "")
    if not ds:
        return None
    try:
        when = dt.datetime.fromisoformat(ds.replace("Z", "+00:00"))
    except ValueError:
        return None
    age = (now - when).total_seconds()
    if age < thresh_s:
        return None
    num = pr.get("number")
    title = str(pr.get("title") or "")[:50]
    return f'{repo} #{num} {head_ref}→{base_ref} CONFLICT-WALL {int(age // 60)}m — "{title}"'


def _stuck_prs(repo: str, now: dt.datetime, thresh_s: float) -> list[str]:
    """Open promote/dep-update PRs for `repo` stuck on a conflict wall beyond thresh_s.

    Bounds API cost: ONE list call per repo (ETag-cached), then a single-PR GET only for promotion
    PRs already older than the threshold (the list endpoint's mergeable_state is unreliable, so we
    fetch the authoritative value per candidate — usually 0-2 per repo)."""
    listing = _gh_json(f"repos/{OWNER}/{repo}/pulls?state=open&per_page=50")
    if not isinstance(listing, list):
        return []
    findings: list[str] = []
    for raw in cast("list[object]", listing):
        if not isinstance(raw, dict):
            continue
        pr = cast("dict[str, object]", raw)
        base_ref = str(cast("dict[str, object]", pr.get("base") or {}).get("ref") or "")
        head_ref = str(cast("dict[str, object]", pr.get("head") or {}).get("ref") or "")
        if not _is_promotion_pr(base_ref, head_ref):
            continue
        ds = str(pr.get("updated_at") or pr.get("created_at") or "")
        try:
            when = dt.datetime.fromisoformat(ds.replace("Z", "+00:00"))
        except ValueError:
            continue
        if (now - when).total_seconds() < thresh_s:
            continue  # not old enough — skip the per-PR GET
        full = _gh_json(f"repos/{OWNER}/{repo}/pulls/{pr.get('number')}")
        if isinstance(full, dict):
            f = _classify_stuck_pr(repo, cast("dict[str, object]", full), now, thresh_s)
            if f:
                findings.append(f)
    return findings


def _write_firestore_promotion_lag(
    repo_lags: dict[str, dict[str, object]],
    now_iso: str,
    project_id: str,
) -> None:
    try:
        from google.cloud import firestore  # noqa: TID251, RUF100, I001  # noqa: imports-inside-functions  # noqa: cloud-sdk-direct

        client = firestore.Client(project=project_id)
        for repo, lags in repo_lags.items():
            doc_ref = client.collection("repo_state").document(repo)
            doc_ref.set({"promotion_lag": {"lags": lags, "checked_at": now_iso}}, merge=True)
    except Exception:  # Firestore unavailable → best-effort write
        pass


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--threshold-min", type=int, default=60)
    ap.add_argument(
        "--stuck-pr-threshold-min",
        type=int,
        default=120,
        help="alert on a promote/dep-update PR sitting CONFLICTING (dirty) longer than this (default 120m)",
    )
    ap.add_argument("--now-iso", default="", help="UTC now (no wallclock in CI sandbox); else uses gh server time")
    ap.add_argument("--slack", action="store_true")
    args = ap.parse_args()
    thresh_s = cast(int, args.threshold_min) * 60.0
    stuck_thresh_s = cast(int, args.stuck_pr_threshold_min) * 60.0
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
    for repo in _repos():
        repo_lags[repo] = {}
        directions = [
            ("LDR→main", "main", "live-defi-rollout", False),
            ("LDR→staging", "staging", "live-defi-rollout", False),
            ("main→LDR", "live-defi-rollout", "main", True),
            ("staging→LDR", "live-defi-rollout", "staging", True),
        ]
        for label, base, head, skip_ci_counts in directions:
            if repo == "unified-trading-pm" and "staging" in label:
                continue  # PM is Option-B (no staging)
            res = _lag(repo, base, head, now, thresh_s, skip_ci_counts)
            if res:
                n, age, omsg = res
                findings.append(f'{repo} {label}: {n} commit(s), oldest {int(age // 60)}m old — "{omsg[:60]}"')
                repo_lags[repo][label] = {"n_commits": n, "age_s": age, "oldest_msg": omsg, "lag": True}
            else:
                repo_lags[repo][label] = {"lag": False}

        # Gap 6 P2: staging-backmerge-to-ldr.yml MUST exist on the STAGING branch (push:[staging]
        # only fires from staging's own copy). A missing copy = the documented Tier-C runaway cause
        # → page proactively (before it strands a repo), not just react via the runaway breaker.
        if repo != "unified-trading-pm" and _branch_exists(repo, "staging"):
            present = _workflow_present_on_ref(repo, "staging-backmerge-to-ldr.yml", "staging")
            repo_lags[repo]["staging_backmerge_present"] = {"present": present}
            if present is False:
                findings.append(
                    f"{repo} staging-backmerge-to-ldr.yml MISSING on the staging branch — "
                    f"staging→LDR back-merge will never fire (Tier-C runaway risk); roll out the "
                    f"template + promote it to staging"
                )

        # Stuck-conflict-wall check: a promote / dep-update PR parked CONFLICTING beyond the SLA is
        # invisible today (the orchestrator backlog is plan-driven, never ingests open PRs; the
        # promote bots only act on LDR→staging drains). Surface it here so it pages.
        # SSOT: plans/active/issues/promotion_queue_conflict_wall_pileup_2026_06_17.md.
        stuck = _stuck_prs(repo, now, stuck_thresh_s)
        if stuck:
            findings.extend(stuck)
            repo_lags[repo]["conflict_wall_prs"] = {"count": len(stuck), "prs": stuck}

    # Persist the warmed ETag cache so the next run's unchanged compares are free 304s.
    if cache_file:
        save_etag_cache(cache_file)

    # Dangling staging-lock check — defense-in-depth for unlock liveness, independent of the
    # cron-throttled/displaceable sit-debounce workflow. A lock held past one SIT cycle is an incident.
    dangle = _lock_dangle(now)
    if dangle:
        findings.append("🔒 " + dangle)

    # Firestore write-through — best-effort; never blocks the monitor on SDK/credential absence.
    gcp_project = os.environ.get("GCP_PROJECT_ID")
    if gcp_project:
        _write_firestore_promotion_lag(repo_lags, now.isoformat(), gcp_project)

    if not findings:
        print(f"✅ promotion-lag: all branches in sync within {int(thresh_s // 60)}m")
        return 0

    if as_slack:
        _m = int(thresh_s // 60)
        header = f":hourglass_flowing_sand: PROMOTION LAG > {_m}m ({len(findings)} branch-pair(s) out of sync):"
        print(header + "\\n" + "\\n".join(f"  • {f}" for f in findings))
    else:
        print(f"⚠️  promotion lag > {int(thresh_s // 60)}m ({len(findings)}):")
        for f in findings:
            print(f"  - {f}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
