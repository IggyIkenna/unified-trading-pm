#!/usr/bin/env python3
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
"""Tier-A live-defi-rollout CI-red monitor.

THE PROBLEM IT SOLVES
=====================
`live-defi-rollout` (LDR) is the workspace integration axis, and BY DESIGN it carries
NO remote CI: the canonical `quality-gates-v2.yml` workflows trigger only on
`push:[main,staging]` + `pull_request:[main,staging]` (LDR was deliberately removed from
the trigger surface — CLAUDE.md § "CI Verification After Every Push"; the gate is enforced
LOCALLY via `quality-gates.sh` before each commit). The hole: a commit that locally skipped
the gate (or whose author never ran it) lands RED on LDR and stays INVISIBLE until weeks
later when someone opens a staging/main promotion PR and the server-enforced
`quality-gates-v2` finally runs. We want a per-repo "is LDR itself green?" signal caught in
HOURS, not weeks.

CHOSEN LDR-RED DETECTION APPROACH (and why)
==========================================
We evaluated three candidate signals (per the task brief):

  (a) workflow_dispatch quality-gates-v2 against the LDR ref per repo, read the conclusion.
  (b) read the latest existing quality-gates-v2 conclusion for the repo's LDR HEAD.
  (c) a bespoke lightweight per-repo LDR check inside the monitor.

We picked **(a), decoupled across two cron ticks** — the cheapest *reliable* signal:

  * (b) is a near-empty signal: LDR has no remote CI, so a quality-gates-v2 run for an LDR
    HEAD almost never exists. Reading it would report "unknown" forever.
  * (c) re-implements the gate. A bespoke lightweight check inevitably DRIFTS from the real
    `quality-gates-v2` (different lint/type/test surface) → false greens that defeat the whole
    point. We refuse to invent a second, weaker definition of "green".
  * (a) reuses the ONE authoritative gate. `quality-gates-v2.yml` already carries
    `workflow_dispatch` and exists on the LDR ref fleet-wide (it's rolled out to every repo's
    LDR), so `gh workflow run quality-gates-v2.yml --ref live-defi-rollout` runs the EXACT
    promotion gate against LDR's code. Its conclusion is the ground truth a staging PR would
    later report — only hours earlier.

To keep a single hourly cron fast (a full QG run takes minutes, far longer than a cron should
block), dispatch and read are DECOUPLED across ticks (the same stateless pattern as
ci_failure_watcher.py — derive state from GitHub's own run history, persist only the
red/green level in the manifest for transition-gating):

  Each tick, per repo:
    1. READ the conclusion of the MOST RECENT prior-tick LDR dispatch run
       (event=workflow_dispatch, headBranch=live-defi-rollout, status=completed) and map it
       to an `ldr_ci_status` level: GREEN | RED | UNKNOWN.
    2. DETECT a transition vs the level persisted in workspace-manifest.json
       (`repositories.<repo>.ldr_ci_status`) and gate the Slack page exactly like
       ci-status-update.yml's `notify_worthy`: page only on a RED transition (→RED) or a
       recovery (RED→GREEN). On a RED transition, ATTRIBUTE the introducing commit(s) (the LDR
       commits between the last-green dispatch sha and the red tip) so the page is actionable.
       Steady-state is silent (anti-spam).
    3. CONDITIONALLY DISPATCH a fresh quality-gates-v2 run against the LDR ref so the NEXT tick
       has a fresh conclusion to read — but ONLY when the LDR tip moved past the last dispatched
       sha (re-running an unchanged tip is the unconditional-x24-repos Actions waste that got
       this monitor disabled in the 2026-06-11 billing wall). At an hourly cadence the prior run
       has long finished.

So a freshly-pushed RED LDR commit is caught within ~2 ticks (~2 hours) of landing.

DEDICATED SIGNAL — NEVER CLOBBER THE PROMOTION ci_status
========================================================
We persist to a DEDICATED `ldr_ci_status` manifest field. The promotion-pipeline `ci_status`
field (FEATURE_GREEN/STAGING_GREEN/MAIN_GREEN/…) is owned by ci-status-update.yml and drives
the dep-on-main promotion gate — writing LDR state into it would corrupt promotion decisions.
`ldr_ci_status` is a separate, monitor-only axis: GREEN | RED | UNKNOWN.

FAIL-OPEN ON THE MONITOR'S OWN MACHINERY
========================================
Like the dep-gate safe-defaults, this monitor NEVER pages on its own bugs. Any gh/network/parse
error for a repo yields `UNKNOWN` (which never pages and never transitions to RED). Exit code is
always 0 — alerting is driven by the `alert` GITHUB_OUTPUT, never by exit status, so a transient
gh hiccup cannot itself wedge or page the monitor.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

# Reuse the canonical fleet list so this stays in lock-step with the rulesets + the rest of
# the CI machinery (pin_branch_protection_rulesets.py is the SSOT for the gated fleet).
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pin_branch_protection_rulesets import ORG, REPOS

# The integration axis we monitor. Mirrors workspace-manifest.json:active_feature_branch.
LDR_BRANCH = "live-defi-rollout"
# The authoritative gate workflow file present on the LDR ref of every repo.
QG_WORKFLOW_FILE = "quality-gates-v2.yml"

# ── ldr_ci_status levels (dedicated axis — NOT the promotion ci_status) ──────────
GREEN = "GREEN"
RED = "RED"
UNKNOWN = "UNKNOWN"  # fail-open default: never pages, never counts as a RED transition

# A completed run with one of these conclusions means LDR is RED for that repo.
_FAIL_CONCLUSIONS = {"failure", "startup_failure", "timed_out"}


def gh_json(args: list[str]) -> list[dict] | dict | None:
    """Run a gh command expecting JSON on stdout; return parsed value or None (fail-open)."""
    try:
        proc = subprocess.run(["gh", *args], capture_output=True, text=True)
    except (OSError, ValueError) as exc:  # gh missing / bad args — fail-open, never raise
        print(f"  ! gh {' '.join(args)} -> exec error: {exc}", file=sys.stderr)
        return None
    if proc.returncode != 0:
        print(f"  ! gh {' '.join(args)} -> rc={proc.returncode}: {proc.stderr.strip()[:200]}", file=sys.stderr)
        return None
    out = proc.stdout.strip()
    if not out:
        return None
    try:
        return json.loads(out)
    except json.JSONDecodeError as exc:
        print(f"  ! JSON parse failed for gh {' '.join(args)}: {exc}", file=sys.stderr)
        return None


def read_ldr_level(repo: str, limit: int) -> tuple[str, str, str]:
    """Read the latest completed LDR quality-gates-v2 dispatch run and map to a level.

    Returns:
        (level, url, sha) where level is GREEN | RED | UNKNOWN. UNKNOWN (fail-open) when no
        prior LDR dispatch run exists yet or gh errors — it never pages and never transitions.
    """
    runs = gh_json(
        [
            "run",
            "list",
            "--repo",
            f"{ORG}/{repo}",
            "--workflow",
            QG_WORKFLOW_FILE,
            "--branch",
            LDR_BRANCH,
            "--event",
            "workflow_dispatch",
            "--limit",
            str(limit),
            "--json",
            "conclusion,status,createdAt,url,headSha,headBranch",
        ]
    )
    if not isinstance(runs, list):
        return (UNKNOWN, "", "")
    # Only completed runs carry a conclusion. The list is newest-first already, but filter
    # defensively to the LDR branch in case gh's --branch filter is ever loosened.
    completed = [
        r for r in runs if isinstance(r, dict) and r.get("status") == "completed" and r.get("headBranch") == LDR_BRANCH
    ]
    if not completed:
        return (UNKNOWN, "", "")
    completed.sort(key=lambda r: r.get("createdAt") or "", reverse=True)
    latest = completed[0]
    level = RED if latest.get("conclusion") in _FAIL_CONCLUSIONS else GREEN
    return (level, latest.get("url") or "", latest.get("headSha") or "")


def dispatch_ldr_run(repo: str) -> bool:
    """Fire a fresh quality-gates-v2 run against the LDR ref for the next tick to read.

    Best-effort: returns True on success. A dispatch failure is non-fatal — the next tick
    simply reads UNKNOWN for this repo (fail-open) and retries the dispatch.
    """
    try:
        proc = subprocess.run(
            [
                "gh",
                "workflow",
                "run",
                QG_WORKFLOW_FILE,
                "--repo",
                f"{ORG}/{repo}",
                "--ref",
                LDR_BRANCH,
            ],
            capture_output=True,
            text=True,
        )
    except (OSError, ValueError) as exc:
        print(f"  ! dispatch {repo} -> exec error: {exc}", file=sys.stderr)
        return False
    if proc.returncode != 0:
        print(f"  ! dispatch {repo} -> rc={proc.returncode}: {proc.stderr.strip()[:200]}", file=sys.stderr)
        return False
    return True


def current_ldr_sha(repo: str) -> str:
    """Current LDR HEAD sha for the repo, or "" (fail-open → caller dispatches anyway).

    Used by the conditional-dispatch cost gate: if the most recent LDR dispatch run already
    targeted this exact tip, re-dispatching it is pure Actions waste (the billing-wall trigger
    that got this monitor disabled 2026-06-11).
    """
    data = gh_json(["api", f"repos/{ORG}/{repo}/commits/{LDR_BRANCH}", "--jq", "{sha: .sha}"])
    if isinstance(data, dict):
        return data.get("sha") or ""
    return ""


def most_recent_dispatch_sha(repo: str, limit: int) -> str:
    """headSha of the most recent LDR quality-gates-v2 dispatch run (ANY status), or "".

    Differs from read_ldr_level (which filters to COMPLETED runs for the conclusion): here we
    want the sha of the last RUN WE FIRED — even if still in-progress — so we never double-fire
    the same tip while a run for it is queued/running.
    """
    runs = gh_json(
        [
            "run",
            "list",
            "--repo",
            f"{ORG}/{repo}",
            "--workflow",
            QG_WORKFLOW_FILE,
            "--branch",
            LDR_BRANCH,
            "--event",
            "workflow_dispatch",
            "--limit",
            str(limit),
            "--json",
            "headSha,createdAt,headBranch",
        ]
    )
    if not isinstance(runs, list):
        return ""
    ldr_runs = [r for r in runs if isinstance(r, dict) and r.get("headBranch") == LDR_BRANCH]
    if not ldr_runs:
        return ""
    ldr_runs.sort(key=lambda r: r.get("createdAt") or "", reverse=True)
    return ldr_runs[0].get("headSha") or ""


def has_in_flight_dispatch(repo: str, limit: int) -> bool:
    """True if the repo's most recent LDR quality-gates-v2 dispatch run is still queued/running.

    Guards the RED-repo unconditional-redispatch path below: that path deliberately bypasses the
    tip-unchanged dedup (`current_ldr_sha == most_recent_dispatch_sha`) so a RED repo whose own tip
    never moves still gets re-tested every tick (2026-07-16 fix for the RED-latching bug). But with
    no in-flight check, a repo stuck RED purely from SHARED-HOST CONTENTION (the qg-governor's fixed
    concurrency pool exhausted, not a real code regression — confirmed 2026-07-27 on
    deployment-service, execution-service, agent-orchestrator, ibkr-gateway-infra all failing/stuck
    simultaneously) gets a FRESH dispatch fired on top of its own still-queued one every tick,
    piling more load onto the very contention causing the redness — a retry-storm amplification, not
    a fix. Fail-open on read error (treat as "not in flight" → dispatch anyway, matching this
    module's existing fail-open convention) since a dispatch failure/skip here is never worse than
    the pre-fix behavior.
    """
    runs = gh_json(
        [
            "run",
            "list",
            "--repo",
            f"{ORG}/{repo}",
            "--workflow",
            QG_WORKFLOW_FILE,
            "--branch",
            LDR_BRANCH,
            "--event",
            "workflow_dispatch",
            "--limit",
            str(limit),
            "--json",
            "status,createdAt,headBranch",
        ]
    )
    if not isinstance(runs, list):
        return False
    ldr_runs = [r for r in runs if isinstance(r, dict) and r.get("headBranch") == LDR_BRANCH]
    if not ldr_runs:
        return False
    ldr_runs.sort(key=lambda r: r.get("createdAt") or "", reverse=True)
    return ldr_runs[0].get("status") not in ("completed", "")


def last_green_sha(repo: str, limit: int) -> str:
    """headSha of the most recent COMPLETED-success LDR dispatch run, or "" (for attribution)."""
    runs = gh_json(
        [
            "run",
            "list",
            "--repo",
            f"{ORG}/{repo}",
            "--workflow",
            QG_WORKFLOW_FILE,
            "--branch",
            LDR_BRANCH,
            "--event",
            "workflow_dispatch",
            "--limit",
            str(limit),
            "--json",
            "conclusion,status,createdAt,headSha,headBranch",
        ]
    )
    if not isinstance(runs, list):
        return ""
    greens = [
        r
        for r in runs
        if isinstance(r, dict)
        and r.get("headBranch") == LDR_BRANCH
        and r.get("status") == "completed"
        and r.get("conclusion") == "success"
    ]
    if not greens:
        return ""
    greens.sort(key=lambda r: r.get("createdAt") or "", reverse=True)
    return greens[0].get("headSha") or ""


def attribute_red(repo: str, red_sha: str, limit: int) -> str:
    """Best-effort: name the LDR commits that introduced the RED, so the page is ACTIONABLE.

    Compares the last known-GREEN dispatch sha → the now-RED sha and lists the commits between
    (author + short subject). Falls back to the latest LDR commit if no prior green is found.
    Fail-open: ANY gh/parse error returns "" (the page still fires, just without attribution).
    """
    green = last_green_sha(repo, limit)
    # SAME-SHA case: this repo's tip did NOT move between the last green and this red, so no LDR
    # commit of its own can have introduced it — a DEPENDENCY changed underneath (CI resolves dep
    # repos from THEIR LDR, so a dep landing reds a consumer whose own code is untouched). Falling
    # through to the tip-commit fallback below actively LIES here. Measured 2026-07-16:
    # market-data-processing-service ran c99adfc4 GREEN (run 29408655322) and, 22h later, RED
    # (29484794768) on that byte-identical sha; the page named the innocent uts-backmerge-bot
    # merge commit, while the real cause was a unified-api-contracts registry landing. Naming the
    # right SUSPECT SET beats naming a precise wrong commit.
    if green and red_sha and green == red_sha:
        return (
            f"      ↳ no LDR commits between the last GREEN and this RED — both are `{red_sha[:8]}`, "
            f"so {repo}'s own code did NOT change.\n"
            f"      ↳ a DEPENDENCY landed on its LDR (CI resolves deps from their LDR). "
            f"Check recent dep-repo commits, NOT this repo's history."
        )
    commits: list[dict] = []
    if green and red_sha and green != red_sha:
        cmp_data = gh_json(["api", f"repos/{ORG}/{repo}/compare/{green}...{red_sha}"])
        if isinstance(cmp_data, dict) and isinstance(cmp_data.get("commits"), list):
            commits = cmp_data["commits"]
    if not commits:
        # Fallback: the tip commit itself (no green baseline to diff against).
        tip = gh_json(["api", f"repos/{ORG}/{repo}/commits/{LDR_BRANCH}"])
        if isinstance(tip, dict):
            commits = [tip]
    if not commits:
        return ""
    lines: list[str] = []
    for c in commits[-5:]:  # at most the 5 newest introducing commits
        if not isinstance(c, dict):
            continue
        sha = (c.get("sha") or "")[:8]
        commit_obj = c.get("commit")
        commit_obj = commit_obj if isinstance(commit_obj, dict) else {}
        author_obj = commit_obj.get("author")
        author = author_obj.get("name", "?") if isinstance(author_obj, dict) else "?"
        subject = (commit_obj.get("message") or "").split("\n", 1)[0][:80]
        lines.append(f"      ↳ `{sha}` {author}: {subject}")
    return "\n".join(lines)


def notify_worthy(prev: str, level: str) -> bool:
    """Transition-gate the page, mirroring ci-status-update.yml's notify_worthy.

    Page ONLY on a RED transition (anything-but-RED → RED) or a recovery (RED → GREEN).
    Steady-state (prev == level), UNKNOWN reads, and GREEN↔UNKNOWN churn are silent
    (anti-spam) — a freshly-seeded repo whose prior level was None never pages on its first
    GREEN read, and an UNKNOWN read never pages or masks a prior RED.
    """
    if level == RED and prev != RED:
        return True
    return level == GREEN and prev == RED


def load_manifest(path: Path) -> dict:
    with open(path) as fh:
        return json.load(fh)


def evaluate_fleet(manifest: dict, repos: list[str], limit: int) -> tuple[list[dict], dict[str, str], dict[str, str]]:
    """Read each repo's LDR level + detect transitions vs the persisted ldr_ci_status.

    Returns:
        (transitions, new_levels, new_shas) — transitions is the list of notify-worthy flips;
        new_levels maps repo -> level for every repo whose level is NOT UNKNOWN (UNKNOWN
        reads are fail-open and never overwrite a known persisted level); new_shas maps the
        SAME repos to the LDR sha each level was read against (see the write below).
    """
    manifest_repos = manifest["repositories"]
    transitions: list[dict] = []
    new_levels: dict[str, str] = {}
    new_shas: dict[str, str] = {}
    for repo in repos:
        if repo not in manifest_repos:
            continue  # not in the manifest registry — skip (fail-open)
        prev = manifest_repos[repo].get("ldr_ci_status") or UNKNOWN
        level, url, sha = read_ldr_level(repo, limit)
        if level == UNKNOWN:
            # Fail-open: a read failure / no-run-yet never overwrites a known level and
            # never pages. Leave the persisted value as-is.
            continue
        new_levels[repo] = level
        # Persist WHICH sha the level was read against (ldr_red_promote_pr_waste_2026_08_10).
        # A bare GREEN/RED is not actionable by a consumer that must decide about a SPECIFIC
        # tree: ldr_to_main_fleet_promote.sh skips cutting a promote PR only when the red level
        # AND this sha both match the tip it is about to promote, so a stale RED (tip has since
        # moved past the failure) can never wedge promotion. Without the sha there is no way to
        # tell "red, and it's THIS tree" from "red, about something already superseded" — and
        # gating on the weaker signal is exactly what caused the unrecoverable deadlock in
        # tier_a_ci_status_gate_unrecoverable_deadlock_2026_08_09.
        new_shas[repo] = sha
        if notify_worthy(prev, level):
            # Attribution is only fetched for a RED transition (a handful per tick at most), so
            # the extra compare/commits gh calls never approach the unconditional-dispatch cost.
            attribution = attribute_red(repo, sha, limit) if level == RED else ""
            transitions.append(
                {
                    "kind": "red" if level == RED else "recovered",
                    "repo": repo,
                    "prev": prev,
                    "level": level,
                    "url": url,
                    "sha": sha,
                    "attribution": attribution,
                }
            )
    return transitions, new_levels, new_shas


def apply_levels(manifest: dict, new_levels: dict[str, str], new_shas: dict[str, str] | None = None) -> bool:
    """Write the dedicated ldr_ci_status field (+ its sha). Returns True if anything changed.

    ``ldr_ci_status_sha`` is written whenever the level is, so the pair is always consistent —
    a consumer must never see a fresh level next to a stale sha, which would let it match a RED
    against the wrong tree. ``new_shas`` is optional so an existing caller that only has levels
    keeps working; it then simply leaves the sha untouched.
    """
    manifest_repos = manifest["repositories"]
    changed = False
    for repo, level in new_levels.items():
        sha = (new_shas or {}).get(repo) or ""
        if manifest_repos[repo].get("ldr_ci_status") != level:
            manifest_repos[repo]["ldr_ci_status"] = level
            changed = True
        # Written even when the LEVEL is unchanged: a repo that stays RED across two different
        # tips must advance its sha, else the promoter would keep matching the stale one and
        # skip promoting a tree the monitor has not actually judged.
        if sha and manifest_repos[repo].get("ldr_ci_status_sha") != sha:
            manifest_repos[repo]["ldr_ci_status_sha"] = sha
            changed = True
    return changed


def build_report(transitions: list[dict]) -> tuple[bool, str, str]:
    """Return (alert, severity, mrkdwn_report) for the wrapping workflow."""
    red = [t for t in transitions if t["kind"] == "red"]
    recovered = [t for t in transitions if t["kind"] == "recovered"]
    lines: list[str] = []
    if red:
        lines.append(f":x: *{len(red)} repo(s) LDR went RED* (live-defi-rollout has no remote CI — caught by Tier-A):")
        for t in red:
            short = (t["sha"] or "")[:8]
            url = f" <{t['url']}|gate run>" if t["url"] else ""
            lines.append(f"  • `{t['repo']}`@`live-defi-rollout` {t['prev']} → *RED* ({short}){url}")
            if t.get("attribution"):
                lines.append(t["attribution"])  # ↳ introducing commit(s): sha author: subject
    if recovered:
        lines.append(f":white_check_mark: *{len(recovered)} repo(s) LDR RECOVERED:*")
        for t in recovered:
            short = (t["sha"] or "")[:8]
            url = f" <{t['url']}|gate run>" if t["url"] else ""
            lines.append(f"  • `{t['repo']}`@`live-defi-rollout` RED → *GREEN* ({short}){url}")
    alert = bool(red or recovered)  # red transitions + recoveries both post; severity differs
    severity = "CRITICAL" if red else "INFO"
    report = "\n".join(lines) if lines else "No LDR CI transitions detected."
    return alert, severity, report


def write_github_output(alert: bool, severity: str, report: str, transitions: list[dict]) -> None:
    out_path = os.environ.get("GITHUB_OUTPUT")
    if not out_path:
        return
    # Escalation matrix input (2026-07-26): escalate-to-orchestrator.yml already exists and
    # explicitly supports wall_type=ldr_qg_failure, but this monitor never called it — a RED
    # transition posted to Slack and stopped there, with no attempt to hand the wall to an
    # orchestrator worker and no failure-to-escalate signal either (found via a real "why didn't
    # this escalate" operator question). Emit just the RED transitions as JSON so the wrapping
    # workflow can fan out a matrix job; a genuinely empty list must still be valid JSON (`[]`)
    # so `fromJson()` in the workflow doesn't choke on an empty string.
    red = [t for t in transitions if t["kind"] == "red"]
    red_entries = [
        {
            "repo": t["repo"],
            "sha": t["sha"] or "",
            "url": t["url"] or "",
            "attribution": t.get("attribution") or "",
        }
        for t in red
    ]
    red_json = json.dumps(red_entries)
    with open(out_path, "a", encoding="utf-8") as fh:
        fh.write(f"alert={'true' if alert else 'false'}\n")
        fh.write(f"severity={severity}\n")
        fh.write("report<<__RPT__\n")
        fh.write(report + "\n")
        fh.write("__RPT__\n")
        fh.write(f"red_transitions_json={red_json}\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", help="Monitor a single repo instead of the full fleet.")
    parser.add_argument("--limit", type=int, default=10, help="Recent LDR dispatch runs to inspect per repo.")
    parser.add_argument(
        "--manifest",
        default="workspace-manifest.json",
        help="Path to workspace-manifest.json (the ldr_ci_status SSOT).",
    )
    parser.add_argument(
        "--no-dispatch",
        action="store_true",
        help="Skip firing fresh LDR quality-gates-v2 runs (read + detect only). For diagnostics.",
    )
    args = parser.parse_args()

    repos = [args.repo] if args.repo else REPOS
    manifest_path = Path(args.manifest)

    # Fail-open: a missing/corrupt manifest must not page or crash the monitor.
    try:
        manifest = load_manifest(manifest_path)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"  ! cannot read manifest {manifest_path}: {exc} — fail-open, no alert", file=sys.stderr)
        write_github_output(False, "INFO", "LDR monitor: manifest unreadable (fail-open, no alert).", [])
        return 0

    transitions, new_levels, new_shas = evaluate_fleet(manifest, repos, args.limit)

    if apply_levels(manifest, new_levels, new_shas):
        try:
            with open(manifest_path, "w", encoding="utf-8") as fh:
                # Canonical manifest form (see check_workspace_manifest_canonical.py).
                json.dump(manifest, fh, indent=2, ensure_ascii=False)
                fh.write("\n")
        except OSError as exc:
            print(f"  ! cannot write manifest {manifest_path}: {exc} (non-fatal)", file=sys.stderr)

    alert, severity, report = build_report(transitions)
    print(report)
    write_github_output(alert, severity, report, transitions)

    # Fire fresh LDR runs so the NEXT tick has a current conclusion to read. Done LAST so a
    # dispatch error can never block the read/detect/persist that already happened.
    #
    # CONDITIONAL DISPATCH (cost control — the fix that re-enables this monitor after the
    # 2026-06-11 billing wall, github_actions_billing_wall_2026_06_11 ▸ "conditional dispatch"):
    # the old code fired a fresh v2 for EVERY repo EVERY tick = ~24 dispatches/hour into a red
    # fleet. We now SKIP a repo whose most-recent LDR dispatch run already targeted the current
    # LDR tip — re-running the same sha is pure Actions waste. Fail-SAFE: when we can't read the
    # current tip OR there is no prior run (either is ""), we DISPATCH (over-fire on uncertainty,
    # never under-fire → never miss a red). In steady state most tips are unchanged → a handful
    # of dispatches/hour instead of 24, while every NEW commit still gets a run within ~2 ticks.
    if not args.no_dispatch:
        fired = 0
        skipped = 0
        for repo in repos:
            # RED repos are re-dispatched even on an UNCHANGED tip. The skip below assumes a
            # repo's own tip is the only input to its CI result — false for this fleet: CI
            # resolves dep repos from THEIR LDR, so a dep landing can flip a consumer red (or
            # green again) while its own tip never moves. Skipping a red repo therefore LATCHES
            # it red forever: no tip movement → no new run → the conclusion the next tick reads
            # never changes → the RED→GREEN recovery page can never fire. Measured 2026-07-16:
            # MDPS sat RED on a UAC registry change with its tip parked at c99adfc4 since
            # 2026-07-15, and its own history held nothing to re-run. Cost stays bounded — this
            # re-fires ONLY the already-red repos (normally 0-2/tick), while the green majority
            # still skips, so the 2026-06-11 billing-wall fix is preserved.
            #
            # IN-FLIGHT GUARD (2026-07-27, retry-storm fix): a repo stuck RED from shared-host
            # contention (qg-governor token pool exhausted, not a code regression) previously got
            # a fresh dispatch piled on top of its own still-queued run EVERY tick — amplifying the
            # exact contention causing the redness. Skip firing if the repo's last dispatch is
            # still queued/in_progress; the next tick re-checks once it actually resolves.
            if new_levels.get(repo) == RED:
                if has_in_flight_dispatch(repo, args.limit):
                    skipped += 1
                    continue
                if dispatch_ldr_run(repo):
                    fired += 1
                continue
            cur = current_ldr_sha(repo)
            last = most_recent_dispatch_sha(repo, args.limit)
            if cur and last and cur == last:
                skipped += 1
                continue  # a run for this exact tip already exists/queued — don't re-burn it
            if dispatch_ldr_run(repo):
                fired += 1
        print(f"Conditional dispatch: fired {fired}, skipped {skipped} unchanged LDR tip(s).")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
