#!/usr/bin/env python3
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

To keep a single 30-min cron fast (a full QG run takes minutes, far longer than a cron should
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
       recovery (RED→GREEN). Steady-state is silent (anti-spam).
    3. DISPATCH a fresh quality-gates-v2 run against the LDR ref so the NEXT tick has a fresh
       conclusion to read. At a 30-min cadence the prior run has long finished.

So a freshly-pushed RED LDR commit is caught within ~2 ticks (~1 hour) of landing.

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


def evaluate_fleet(
    manifest: dict, repos: list[str], limit: int
) -> tuple[list[dict], dict[str, str]]:
    """Read each repo's LDR level + detect transitions vs the persisted ldr_ci_status.

    Returns:
        (transitions, new_levels) — transitions is the list of notify-worthy flips;
        new_levels maps repo -> level for every repo whose level is NOT UNKNOWN (UNKNOWN
        reads are fail-open and never overwrite a known persisted level).
    """
    manifest_repos = manifest["repositories"]
    transitions: list[dict] = []
    new_levels: dict[str, str] = {}
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
        if notify_worthy(prev, level):
            transitions.append(
                {
                    "kind": "red" if level == RED else "recovered",
                    "repo": repo,
                    "prev": prev,
                    "level": level,
                    "url": url,
                    "sha": sha,
                }
            )
    return transitions, new_levels


def apply_levels(manifest: dict, new_levels: dict[str, str]) -> bool:
    """Write the dedicated ldr_ci_status field. Returns True if anything changed."""
    manifest_repos = manifest["repositories"]
    changed = False
    for repo, level in new_levels.items():
        if manifest_repos[repo].get("ldr_ci_status") != level:
            manifest_repos[repo]["ldr_ci_status"] = level
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


def write_github_output(alert: bool, severity: str, report: str) -> None:
    out_path = os.environ.get("GITHUB_OUTPUT")
    if not out_path:
        return
    with open(out_path, "a", encoding="utf-8") as fh:
        fh.write(f"alert={'true' if alert else 'false'}\n")
        fh.write(f"severity={severity}\n")
        fh.write("report<<__RPT__\n")
        fh.write(report + "\n")
        fh.write("__RPT__\n")


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
        write_github_output(False, "INFO", "LDR monitor: manifest unreadable (fail-open, no alert).")
        return 0

    transitions, new_levels = evaluate_fleet(manifest, repos, args.limit)

    if apply_levels(manifest, new_levels):
        try:
            with open(manifest_path, "w") as fh:
                json.dump(manifest, fh, indent=2)
                fh.write("\n")
        except OSError as exc:
            print(f"  ! cannot write manifest {manifest_path}: {exc} (non-fatal)", file=sys.stderr)

    alert, severity, report = build_report(transitions)
    print(report)
    write_github_output(alert, severity, report)

    # Fire fresh LDR runs so the NEXT tick has a current conclusion to read. Done LAST so a
    # dispatch error can never block the read/detect/persist that already happened.
    if not args.no_dispatch:
        for repo in repos:
            dispatch_ldr_run(repo)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
