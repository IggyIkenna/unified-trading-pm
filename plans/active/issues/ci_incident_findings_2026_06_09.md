---
title:
  "CI incident findings 2026-06-09 — readiness-verifier missing script + dirty-skip not alerted + orchestrator headroom"
created: 2026-06-09
author: ikennaigboaka [slot-1·laptop]
locked_by: live-defi-rollout
priority: P2
status: active
---

## What I found (during the 2026-06-09 PM-RED incident)

The PM-RED root cause (parity_watchdog empty-string fallback) is FIXED (PM@512626fe7); these are the adjacent findings
surfaced while triaging the Slack #ci-failures burst:

1. **Readiness Verifier is hard-broken** — `.github/workflows/readiness-verifier.yml:45` calls
   `scripts/workspace/setup-workspace-from-manifest.sh`, which **does not exist** (the dir has
   `setup-workspace-root.sh`, `setup-dev-environment.sh`, … but no `…-from-manifest.sh`) → exit 127 every run, then
   `cat readiness-report.txt` → exit 1. Pre-existing (not a regression). Fix: point the workflow at the real
   provisioning script (likely `setup-workspace-root.sh` + a tier filter) or create the intended script; otherwise make
   the step non-fatal so it stops reddening the fleet.

2. **slot-cron-ff-pull dirty-skip is silent** — the FF-pull cron correctly skips a worktree with uncommitted changes
   (`[skip:dirty]`), but `verify-slot-host-symmetry.sh --alert` only alerts when the cron **didn't run**, not when it
   ran-but-skipped-everything. A slot left dirty for hours therefore never FF-syncs AND never alerts. Fix: have the
   symmetry verify (or a new check) alert when a slot has been `[skip:dirty]` for > N consecutive ticks. (This incident:
   the dirtiness was transient Path-B migration churn + a hook `chmod`; both cleared/fixed.)

3. **Orchestrator headroom, not down** — `api.agent-orchestrator.odum-research.com/health` = 200, but
   `Escalate to Orchestrator` returned no `escalation_id` ("no free slot / headroom account") and the Overnight Dead Man
   Switch reported the orchestrator "did not complete". Capacity / overnight-run issue on vm-0, not an unreachable VM —
   needs an operator look at slot headroom + the overnight job.

## Why it matters

(1) keeps a required-ish check red (noise + can gate). (2) is a real observability gap (silent no-sync). (3) means stuck
promotion PRs don't get auto-escalated workers — they wait on a human.
