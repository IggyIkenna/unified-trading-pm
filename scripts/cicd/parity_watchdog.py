#!/usr/bin/env python3
"""CI/local-QG parity watchdog — turn a local-green/staging-red event into a tracked defect.

Principle (ci_local_qg_parity_2026_06_08.md): a local `quality-gates.sh --no-fix` green on an
LDR checkout, in dep order, content-sync-gated, should predict staging-`quality-gates-v2` green.
The only sanctioned local↔CI gaps are the workflow-drift CI no-op (tag-pinned clones) and the
assembled-SIT cross-repo layer. Any OTHER staging-v2 RED while local QG is green is a PARITY
DEFECT — this watchdog files/refreshes an issue doc naming the diverging gate step + the run,
and emits an orchestrator alert line, so the divergence is audited rather than normalized.

Usage:
    parity_watchdog.py --repo <name> [--local-green] [--issues-dir plans/active/issues] [--date YYYY-MM-DD]
      --local-green  caller asserts local QG (dep-order LDR checkout) is green for <repo>
                     (e.g. from local_qg_sweep.py); without it, the doc is filed as "local-status
                     unconfirmed — run local_qg_sweep to classify".
Exit 0 always (it is a reporter); prints `PARITY_DIVERGENCE <repo>` on a filed defect.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import cast


def _staging_v2(repo: str) -> tuple[str, str, str]:
    """Return (conclusion, run_url, failing_step) for the latest staging quality-gates-v2 run."""
    out = subprocess.run(
        ["gh", "run", "list", "--repo", f"IggyIkenna/{repo}", "--workflow", "quality-gates-v2",
         "--branch", "staging", "--limit", "1", "--json", "databaseId,conclusion,status,url"],
        capture_output=True, text=True,
    ).stdout
    try:
        runs = cast("list[dict[str, object]]", json.loads(out))
    except json.JSONDecodeError:
        return "unknown", "", ""
    if not runs:
        return "none", "", ""
    r = runs[0]
    if r.get("status") != "completed":
        return "in_progress", str(r.get("url", "")), ""
    conclusion = str(r.get("conclusion", "unknown"))
    url = str(r.get("url", ""))
    step = ""
    if conclusion == "failure":
        log = subprocess.run(
            ["gh", "run", "view", str(r.get("databaseId")), "--repo", f"IggyIkenna/{repo}", "--log-failed"],
            capture_output=True, text=True,
        ).stdout
        for line in log.splitlines():
            low = line.lower()
            if "❌" in line or "failed:" in low or "error:" in low:
                step = line.split("Z\t")[-1].strip()[:160]
                break
    return conclusion, url, step


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--local-green", action="store_true")
    ap.add_argument("--issues-dir", default="plans/active/issues")
    ap.add_argument("--date", required=True, help="YYYY-MM-DD (pass in — no wallclock in this env)")
    args = ap.parse_args()
    repo = cast(str, args.repo)
    local_green = cast(bool, args.local_green)
    issues_dir = Path(cast(str, args.issues_dir))
    date = cast(str, args.date)

    conclusion, url, step = _staging_v2(repo)
    print(f"{repo}: staging quality-gates-v2 = {conclusion}")
    if conclusion != "failure":
        print(f"no parity defect ({conclusion})")
        return 0

    local_note = (
        "local QG (dep-order LDR checkout) is GREEN — confirmed parity DEFECT"
        if local_green
        else "local-status UNCONFIRMED — run `scripts/cicd/local_qg_sweep.py --only "
        f"{repo}` to classify (green ⇒ confirmed parity defect; red ⇒ a genuine code regression, not a parity bug)"
    )
    issues_dir.mkdir(parents=True, exist_ok=True)
    doc = issues_dir / f"ci_local_qg_divergence_{repo}_{date}.md"
    body = f"""---
title: "CI/local-QG parity divergence — {repo} staging-v2 RED"
created: {date}
source:
  - "scripts/cicd/parity_watchdog.py"
  - "{url}"
locked_by: live-defi-rollout
priority: P2
status: active
---

## What I found

`{repo}` staging `quality-gates-v2` is **failing** ({url}). Per `ci_local_qg_parity_2026_06_08.md`,
{local_note}.

Diverging gate step (from the staging run log):

    {step or "(failing step not auto-extracted — open the run log)"}

## Why it matters

A local-green/staging-red event means CI and local QG have diverged in STRUCTURE (the parity the reform
guarantees). The only sanctioned gaps are the workflow-drift CI no-op (tag-pinned clones) and the
assembled-SIT cross-repo layer. If the diverging step is neither, fix so the step is byte-identical local vs CI.

## Recommended decision

Audit the diverging step vs the local↔CI parity matrix (`codex/08-workflows/ci-cd-flow.md` § "Local ↔ CI QG
parity matrix"). Close the structural gap (same selection / env / tool versions / ignore-sets) or, if it is a
genuine code regression, fix the code. Archive when staging-v2 is green again.
"""
    doc.write_text(body)
    print(f"PARITY_DIVERGENCE {repo} → {doc}")
    # orchestrator alert line (every alert → orchestrator, not Slack-only)
    print(f"ORCH_ALERT parity-divergence repo={repo} staging_v2=failure doc={doc}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
