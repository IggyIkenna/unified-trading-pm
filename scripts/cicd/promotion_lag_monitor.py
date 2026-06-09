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
import os.path
import subprocess
import sys
from typing import cast

OWNER = "IggyIkenna"


def _gh_json(path: str) -> object:
    r = subprocess.run(["gh", "api", path], capture_output=True, text=True)
    if r.returncode != 0:
        return None
    try:
        return cast("object", json.loads(r.stdout))
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


def _lag(
    repo: str, base: str, head: str, now: dt.datetime, thresh_s: float, skip_ci_counts: bool
) -> tuple[int, float, str] | None:
    """Return (n_commits, oldest_age_s, oldest_msg) for head-commits-not-on-base, or None."""
    d = _gh_json(f"repos/{OWNER}/{repo}/compare/{base}...{head}")
    if not isinstance(d, dict):
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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--threshold-min", type=int, default=60)
    ap.add_argument("--now-iso", default="", help="UTC now (no wallclock in CI sandbox); else uses gh server time")
    ap.add_argument("--slack", action="store_true")
    args = ap.parse_args()
    thresh_s = cast(int, args.threshold_min) * 60.0
    now_iso = cast(str, args.now_iso)
    as_slack = cast(bool, args.slack)

    if now_iso:
        now = dt.datetime.fromisoformat(now_iso.replace("Z", "+00:00"))
    else:
        # GitHub server time from a HEAD request header avoids relying on a wallclock
        r = subprocess.run(["gh", "api", "-i", "rate_limit"], capture_output=True, text=True)
        now = None
        for line in r.stdout.splitlines():
            if line.lower().startswith("date:"):
                try:
                    now = dt.datetime.strptime(
                        line[5:].strip(), "%a, %d %b %Y %H:%M:%S GMT"
                    ).replace(tzinfo=dt.UTC)
                except ValueError:
                    now = None
                break
        if now is None:
            print("could not resolve server time; pass --now-iso")
            return 0

    findings: list[str] = []
    for repo in _repos():
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
                findings.append(f"{repo} {label}: {n} commit(s), oldest {int(age // 60)}m old — “{omsg[:60]}”")

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
