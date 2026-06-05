#!/usr/bin/env python3
"""Unified CI/CD flow-health reporter (plan section G — supersedes E + F).

ONE cron that computes, per repo, the whole promotion-flow health in a single pass
and emits ONE transition alert (red flow-blocked / green flow-recovered) instead of
the scattered point-checks (PR-resolved bookend, SIT-pass, branch-severity,
behind/ahead x3, stuck-PR age, staging-lock) the E/F items each wanted separately.

Per repo it gathers:
  - ci_status      (workspace-manifest.json; FAILING => LDR/main red)
  - behind x3      (main<->staging, staging<->LDR, main<->LDR via `gh api compare`)
  - oldest stuck PR age (open promotion PRs CONFLICTING/DIRTY/BLOCKED)
  - staging lock-state (workspace-manifest.json staging_status)

A repo is an OFFENDER (flow-blocked) on the unambiguous signals only, to avoid
false positives from the *normal* LDR-ahead-of-staging drift:
  - ci_status == FAILING
  - a staging lock older than --lock-stale-min  (the dangling-lock incident class)
  - an open promotion PR stuck longer than --stuck-min
  - main behind staging by >= --promote-stuck-behind  (promotion to main wedged)
The x3 behind/ahead numbers are CONTEXT in the message, not offender triggers.

Anti-spam: mirrors ci-status-update. The fleet verdict (blocked yes/no) is compared
to the prior verdict in a small committed state file; the workflow only alerts +
commits the new state on a TRANSITION, never on steady-state.

The COMPUTE is a pure function (`compute_flow_health`) over already-gathered per-repo
dicts, hermetically unit-tested without gh/network. Exit code is always 0 (alerting is
driven by GITHUB_OUTPUT, never exit status, so a transient gh hiccup never fails it).

SSOT: plans/active/cicd_contract_hardening_2026_06_01.md section G.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import TypedDict, cast

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pin_branch_protection_rulesets import ORG, REPOS

_LDR_RED_STATUS = "FAILING"
_STUCK_PR_STATES = {"CONFLICTING", "DIRTY", "BLOCKED"}
_PROMOTION_HEADS = {"live-defi-rollout", "staging"}


class RepoState(TypedDict):
    repo: str
    ci_status: str
    main_behind_staging: int
    staging_behind_ldr: int
    main_behind_ldr: int
    oldest_stuck_min: int
    staging_locked_min: int


class Offender(TypedDict):
    repo: str
    reasons: list[str]


class Verdict(TypedDict):
    blocked: bool
    offenders: list[Offender]


# ── narrowing helpers (strict-basedpyright clean; mirrors check_workspace_code_workspace_drift) ──


def _as_dict(value: object) -> dict[str, object]:
    return cast("dict[str, object]", value) if isinstance(value, dict) else {}


def _as_list(value: object) -> list[object]:
    return cast("list[object]", value) if isinstance(value, list) else []


def _as_int(value: object, default: int = -1) -> int:
    return value if isinstance(value, int) else default


def _as_str(value: object, default: str = "") -> str:
    return value if isinstance(value, str) else default


# ── pure core (no IO) ────────────────────────────────────────────────────────


def compute_flow_health(
    repo_states: list[RepoState], *, stuck_min: int, lock_stale_min: int, promote_stuck_behind: int
) -> Verdict:
    """Reduce per-repo gathered state to a fleet verdict + offender list. Pure."""
    offenders: list[Offender] = []
    for s in repo_states:
        reasons: list[str] = []
        if s.get("ci_status") == _LDR_RED_STATUS:
            reasons.append("ci_status=FAILING")
        lock_min = _as_int(s.get("staging_locked_min", -1))
        if lock_min >= lock_stale_min:
            reasons.append(f"staging locked {lock_min}m")
        stuck = _as_int(s.get("oldest_stuck_min", -1))
        if stuck >= stuck_min:
            reasons.append(f"stuck PR {stuck}m")
        mbs = _as_int(s.get("main_behind_staging", 0), 0)
        if mbs >= promote_stuck_behind:
            reasons.append(f"main {mbs} behind staging")
        if reasons:
            offenders.append({"repo": _as_str(s.get("repo")), "reasons": reasons})
    return {"blocked": bool(offenders), "offenders": offenders}


def render_message(verdict: Verdict, prev_blocked: bool) -> str:
    """Slack mrkdwn for a flow-health TRANSITION (recovered vs blocked)."""
    if not verdict["blocked"]:
        return (
            ":large_green_circle: *flow-recovered* — all repos clear (ci_status green, no stuck PRs, staging unlocked)."
        )
    lines = [f":red_circle: *flow-blocked* — {len(verdict['offenders'])} repo(s) wedging the promotion flow:"]
    for o in verdict["offenders"]:
        lines.append(f"  • `{o['repo']}` — {', '.join(o['reasons'])}")
    if not prev_blocked:
        lines.append(
            "_(first transition into blocked — fix on live-defi-rollout; escalate agent handles conflicts + RED)_"
        )
    return "\n".join(lines)


# ── IO helpers ──────────────────────────────────────────────────────────────


def _gh_json(args: list[str]) -> object:
    proc = subprocess.run(["gh", *args], capture_output=True, text=True)
    if proc.returncode != 0:
        print(f"  ! gh {' '.join(args)} -> rc={proc.returncode}: {proc.stderr.strip()[:160]}", file=sys.stderr)
        return None
    out = proc.stdout.strip()
    if not out:
        return None
    try:
        return cast("object", json.loads(out))
    except json.JSONDecodeError:
        return None


def _behind(repo: str, base: str, head: str) -> int:
    """How many commits `head` is ahead of `base` (i.e. base-behind-head). -1 on error."""
    data = _as_dict(_gh_json(["api", f"repos/{ORG}/{repo}/compare/{base}...{head}", "--jq", "{ahead:.ahead_by}"]))
    return _as_int(data.get("ahead"))


def _oldest_stuck_min(repo: str, now: _dt.datetime) -> int:
    """Age (min) of the oldest open promotion PR stuck CONFLICTING/DIRTY/BLOCKED; -1 if none."""
    oldest = -1
    for base in ("staging", "main"):
        raw = _gh_json(
            [
                "pr",
                "list",
                "--repo",
                f"{ORG}/{repo}",
                "--base",
                base,
                "--state",
                "open",
                "--limit",
                "30",
                "--json",
                "mergeStateStatus,isDraft,autoMergeRequest,createdAt,headRefName",
            ]
        )
        for pr_obj in _as_list(raw):
            pr = _as_dict(pr_obj)
            if pr.get("isDraft") or pr.get("mergeStateStatus") not in _STUCK_PR_STATES:
                continue
            if pr.get("autoMergeRequest") is None and pr.get("headRefName") not in _PROMOTION_HEADS:
                continue
            created = _dt.datetime.fromisoformat(_as_str(pr.get("createdAt")).replace("Z", "+00:00"))
            oldest = max(oldest, int((now - created).total_seconds() / 60.0))
    return oldest


def _staging_locked_min(staging: dict[str, object], now: _dt.datetime) -> int:
    if not staging.get("locked"):
        return -1
    since = _as_str(staging.get("locked_since"))
    if not since:
        return -1
    try:
        t = _dt.datetime.fromisoformat(since.replace("Z", "+00:00"))
    except ValueError:
        return -1
    return int((now - t).total_seconds() / 60.0)


def gather_repo_states(manifest: dict[str, object], repos: list[str], now: _dt.datetime) -> list[RepoState]:
    repositories = _as_dict(manifest.get("repositories"))
    locked_min = _staging_locked_min(_as_dict(manifest.get("staging_status")), now)
    states: list[RepoState] = []
    for repo in repos:
        meta = _as_dict(repositories.get(repo))
        states.append(
            {
                "repo": repo,
                "ci_status": _as_str(meta.get("ci_status")),
                "main_behind_staging": _behind(repo, "main", "staging"),
                "staging_behind_ldr": _behind(repo, "staging", "live-defi-rollout"),
                "main_behind_ldr": _behind(repo, "main", "live-defi-rollout"),
                "oldest_stuck_min": _oldest_stuck_min(repo, now),
                # staging lock is one workspace-wide PM state, not per-repo; attach to all.
                "staging_locked_min": locked_min,
            }
        )
    return states


def _write_output(blocked: bool, transition: bool, message: str) -> None:
    out_path = os.environ.get("GITHUB_OUTPUT")
    if not out_path:
        return
    with open(out_path, "a", encoding="utf-8") as fh:
        _ = fh.write(f"blocked={'true' if blocked else 'false'}\n")
        _ = fh.write(f"transition={'true' if transition else 'false'}\n")
        _ = fh.write("message<<__FH__\n")
        _ = fh.write(message + "\n")
        _ = fh.write("__FH__\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    _ = parser.add_argument("--repo", help="Single repo (default: full fleet).")
    _ = parser.add_argument("--stuck-min", type=int, default=60)
    _ = parser.add_argument("--lock-stale-min", type=int, default=25, help="Staging lock older than this = dangling.")
    _ = parser.add_argument(
        "--promote-stuck-behind", type=int, default=40, help="main this far behind staging = wedged."
    )
    _ = parser.add_argument("--state-file", default="scripts/repo-management/flow_health_state.json")
    _ = parser.add_argument("--now", help="ISO8601 override for deterministic testing.")
    args = parser.parse_args()

    # argparse Namespace attrs are Any — extract through cast into typed locals once.
    now_arg = cast("str | None", args.now)
    repo_arg = cast("str | None", args.repo)
    stuck_min = cast("int", args.stuck_min)
    lock_stale_min = cast("int", args.lock_stale_min)
    promote_stuck_behind = cast("int", args.promote_stuck_behind)
    state_file = cast("str", args.state_file)

    now = _dt.datetime.fromisoformat(now_arg.replace("Z", "+00:00")) if now_arg else _dt.datetime.now(_dt.UTC)
    repos: list[str] = [repo_arg] if repo_arg else cast("list[str]", REPOS)

    manifest_path = Path(__file__).resolve().parents[2] / "workspace-manifest.json"
    try:
        manifest = _as_dict(cast("object", json.loads(manifest_path.read_text(encoding="utf-8"))))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"  ! cannot read manifest: {exc}", file=sys.stderr)
        return 0  # fail-safe: never fail the cron

    verdict = compute_flow_health(
        gather_repo_states(manifest, repos, now),
        stuck_min=stuck_min,
        lock_stale_min=lock_stale_min,
        promote_stuck_behind=promote_stuck_behind,
    )

    state_path = Path(state_file)
    prev_blocked = False
    if state_path.is_file():
        try:
            prev_blocked = bool(
                _as_dict(cast("object", json.loads(state_path.read_text(encoding="utf-8")))).get("blocked")
            )
        except (OSError, json.JSONDecodeError):
            prev_blocked = False

    transition = verdict["blocked"] != prev_blocked
    message = render_message(verdict, prev_blocked)
    print(message)
    _write_output(verdict["blocked"], transition, message)

    # Persist new verdict ONLY on transition (low-churn; the workflow commits it [skip ci]).
    if transition:
        payload: dict[str, object] = {
            "blocked": verdict["blocked"],
            "offenders": verdict["offenders"],
            "ts": now.isoformat(),
        }
        _ = state_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
