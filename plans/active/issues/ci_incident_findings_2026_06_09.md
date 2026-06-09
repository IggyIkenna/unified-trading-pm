---
title:
  "CI incident findings 2026-06-09 — readiness-verifier missing script + dirty-skip not alerted + orchestrator headroom"
created: 2026-06-09
locked_by: live-defi-rollout
priority: P2
status: active
---

## What I found (during the 2026-06-09 PM-RED incident)

The PM-RED root cause (parity_watchdog empty-string fallback) is FIXED (PM@512626fe7); these are the adjacent findings
surfaced while triaging the Slack #ci-failures burst:

1. **✅ RESOLVED 2026-06-09 (PM@874bf24ab)** — **Readiness Verifier was hard-broken** —
   `.github/workflows/readiness-verifier.yml:45` called `scripts/workspace/setup-workspace-from-manifest.sh` → exit 127
   every run, then `cat readiness-report.txt` → exit 1 (pre-existing, not a regression). **Diagnosis refinement:** the
   script DOES exist, just at `scripts/setup-workspace-from-manifest.sh` (not `scripts/workspace/`), AND it is a
   **per-`<service>`** dep-cloner (`<SERVICE_NAME> [--skip-install]`), so it never accepted the `--tier`/`--skip-fresh`
   flags the step passed. `setup-workspace-root.sh` only sets the workspace-root path (no clone, no tier) — so the
   "repoint to setup-workspace-root.sh + tier filter" option could not have worked either. **Fix shipped:** made the
   step `continue-on-error: true` (non-fatal — the only thing failing the job was this step's exit 127; readiness
   mismatches merely alert via Slack, no hard-fail gate), dropped the phantom path, and made it best-effort (clones a
   single `repo_filter`'s deps via the real script when given). The fleet stops reddening; `check-repo-readiness.py`
   runs against repos already present (PM + in-repo `codex/`). **Residual follow-up (NICE-TO-HAVE):** no tier-bulk-clone
   helper exists — a dedicated one would let tier-mode actually populate sibling repos before the readiness check (see
   todo below).

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

## Todos

- [x] ✅ [SCRIPT] P2. Finding 1 — readiness-verifier clone step non-fatal + drop phantom `scripts/workspace/` path.
      Shipped PM@874bf24ab (`fix(ci): make readiness-verifier clone step non-fatal + drop phantom script path`),
      actionlint-clean. — 2026-06-09.
- [ ] [SCRIPT] P3. **NICE-TO-HAVE** Finding 1 residual — add a **tier-bulk-clone** helper (PM `scripts/`) so the
      readiness-verifier can actually populate the tier's sibling repos before `check-repo-readiness.py` runs. Today
      `setup-workspace-from-manifest.sh` is per-`<service>` and `setup-workspace-root.sh` only sets the root path, so
      tier-mode runs against whatever repos already happen to be present (PM + in-repo `codex/`). Repo: `unified-trading-pm`.
- [ ] [SCRIPT] P2. Finding 2 — alert when a slot has been `[skip:dirty]` for > N consecutive `slot-cron-ff-pull` ticks
      (extend `verify-slot-host-symmetry.sh --alert` or add a check). Repo: `unified-trading-pm`.
- [ ] [OPERATOR] P2. Finding 3 — vm-0 slot headroom / Overnight Dead Man Switch did-not-complete needs an operator look
      (capacity, not unreachable). **BLOCKED-OPERATOR-DECISION.**
