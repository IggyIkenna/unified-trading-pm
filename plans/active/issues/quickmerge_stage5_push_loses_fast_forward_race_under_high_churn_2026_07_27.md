---
doc_type: issue
title:
  quickmerge Stage 5 push repeatedly loses the non-fast-forward race under sustained high branch churn on
  unified-trading-pm live-defi-rollout
summary: >-
  Shipping a small, fully QG-verified, non-conflicting 4-file change (the runtime abort-monitor fix for
  shared_host_ram_exhaustion_kills_background_qg_2026_07_27.md) took 16 consecutive `quickmerge.sh --agent` attempts and
  well over an hour of pure shipping-mechanics retries, purely because `origin/live-defi-rollout` on unified-trading-pm
  is under such sustained push churn (many concurrent slots landing `docs(plans):` flip commits) that the branch moves
  during quickmerge's own ~45-300s QG re-verification window, so by the time Stage 5 reaches the final push, the remote
  has already moved again — every single time, 16/16. A genuine SEPARATE bug was found and fixed along the way (see
  "What I found" #1), which reduced but did not eliminate the race.
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [quickmerge, ci-infra, branch-drift, shared-host, fleet-wide, blocking]
related:
  [
    /plans/active/issues/shared_host_ram_exhaustion_kills_background_qg_2026_07_27.md,
    /plans/active/qg_host_adaptive_resource_governor_2026_07_14.md,
  ]
created: 2026-07-27
priority: P2
parent_epic: infrastructure_master
source: "slot-5, infra, discovered while shipping shared_host_ram_exhaustion_kills_background_qg-001, 2026-07-27"
assigned_vm: planning
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
resolved_by:
---

# quickmerge Stage 5 push repeatedly loses the fast-forward race under high branch churn

## What I found

1. **Real bug, fixed in this session**: when a `--agent` caller (per the documented worker flow) commits BEFORE calling
   `quickmerge.sh`, and that commit lacks the `Quickmerge: agent` trailer, `quickmerge.sh` Stage 5 does a LATE
   `git commit --amend` to stamp it (`scripts/quickmerge.sh:1632-1639`). That amend re-triggers the `check-branch-drift`
   pre-commit hook — which does its OWN fresh `git fetch` at that exact late moment, AFTER the full ~1-5 min Pass-1 QG
   re-run that Stage 3 just did. Under high churn this pre-commit hook nearly always found new drift and hard-failed the
   whole run. **Workaround applied**: pre-stamp the `Quickmerge: agent` trailer on your own commit BEFORE calling
   quickmerge (`git commit --amend` to append `\nQuickmerge: agent\n`) — this made `_QM_ALREADY_COMMITTED` skip the late
   amend entirely, confirmed via 2 subsequent attempts that reached `Stage 5: Create PR` → "Proceeding to push" with NO
   pre-commit hook re-run in between (vs. every prior attempt hitting the hook).
2. **Residual, structural race (NOT fixed, this doc's actual subject)**: even with the trailer pre-stamped, the FINAL
   `git push` at the end of Stage 5 still lost the non-fast-forward race 3/3 times after the workaround (16/16 overall
   including pre-workaround attempts). Root cause: quickmerge's own STAGE 0.4 rebase runs ONCE, at the very START of the
   invocation; the FULL Pass-1 QG suite then runs for 45-300s (even with the content-sentinel fast-path); by the time
   Stage 5's `git push` executes, minutes have elapsed and — under the churn observed this session (commits landing
   roughly every 20-90s on this branch) — the remote has near-certainly moved again. There is no retry-with-rebase loop
   AROUND the final push itself; the caller (a human or agent) must re-invoke the ENTIRE quickmerge pipeline (including
   the full QG re-run) to get one more attempt at winning the race.
3. Observed drift-per-attempt across the 16 tries: 1, 1, 3, 4, 5, 6, 5(narrower after), 2, 4, 2, 6, 4, 2 — no consistent
   downward trend from retrying faster; the limiting factor is QG wall-clock time vs. push frequency, not anything the
   caller controls.

## Why it matters

- **Not specific to this task or this worker.** ANY agent shipping ANY change to `unified-trading-pm` during a
  sustained-high-churn window (which, per the fleet's `backlog_queued` count observed this session — 700+ — appears to
  be closer to steady-state than a rare spike) hits this. A P1/P0 fix could be blocked from shipping for an hour+ for
  reasons entirely unrelated to its own correctness.
- **Wastes real shared-host QG capacity.** Each failed attempt re-runs the FULL Pass-1 quality-gates.sh (pytest +
  basedpyright + the ~100-step codex-compliance sweep) — 16 wasted full runs on an already-contended host is a
  meaningful contribution to the exact RAM/CPU pressure `shared_host_ram_exhaustion_kills_background_qg_2026_07_27.md`
  and `qg_host_adaptive_resource_governor_2026_07_14.md` are about. This issue and that one are two faces of the same
  underlying capacity problem.
- **The trailer-amend bug (finding #1) is real and independently worth fixing** even though it's not this doc's main
  subject — any `--agent` caller who commits without pre-stamping the trailer pays an extra, avoidable hook-triggered
  QG-adjacent delay on every single quickmerge invocation, not just under high churn.

## Recommended fix path

- [ ] [INFRA] P2. **Stamp the `Quickmerge: <kind>` trailer at COMMIT time, not amend time.** Either (a) have the
      documented `--agent` worker flow always include the trailer in the original commit message (a one-line addition to
      `unified-trading-pm/agents/worker.md`'s ship-loop example), or (b) have quickmerge's own Pass-1 sentinel-write
      step stamp it via a NON-hook-triggering method (`git notes`, or rewriting via `git commit --amend --no-verify` is
      banned per CLAUDE.md, so this needs a real design, not a bypass). Option (a) is the low-risk fix. **Done when**: a
      fresh `--agent` commit without a pre-stamped trailer no longer causes a late pre-commit hook re-invocation at
      Stage 5.
- [ ] [INFRA] P2. **Add a bounded retry-with-rebase loop AROUND the final `git push` in Stage 5** (not around the whole
      pipeline) — e.g. on a non-fast-forward rejection, `git pull --rebase --autostash` + retry the push up to N times
      (N=3-5) before failing, entirely inside quickmerge.sh, without re-running Pass-1 QG (the content hasn't changed,
      only the base commit). This turns "the caller must re-run the whole ~1-5 min pipeline per retry" into "quickmerge
      retries its own few-second push automatically" — directly attacks the root cause (QG wall-clock >> push interval)
      without needing QG to get faster. **Done when**: a simulated high-churn scenario (another process pushing every
      20-30s during a quickmerge run) succeeds within one quickmerge invocation instead of requiring the caller to loop.
- [ ] [INFRA] P3. **Surface push-churn as a named condition** (mirroring the existing repo-blocker mechanism in
      `unified-trading-pm/agents/worker.md` § 4b, which already exists for `qg_red` on a repo) so a worker hitting this
      doesn't have to self-diagnose it as a mystery repeated failure — a `push_race` repo-blocker kind that lets the
      backend own the retry-and-notify loop instead of the calling agent burning its own turns on blind retries. **Done
      when**: a worker hitting 3+ consecutive Stage-5 push failures on the same repo can declare this condition and get
      notified when a push window opens, instead of re-invoking quickmerge manually.

## Progress Log

- 2026-07-27 (slot-5, `infra`): Filed after shipping `shared_host_ram_exhaustion_kills_background_qg-001`'s fix hit 16
  consecutive quickmerge failures (~70+ min) purely on this race — found + worked around the trailer/amend bug (finding
  #1) mid-session, which measurably helped (attempts reliably reach `Stage 5 → Proceeding to push` now, vs. failing
  earlier in the pipeline before), but the residual final-push race (finding #2) persists and is this doc's actual
  scope. Continuing to retry the underlying ship in parallel; not blocking on this doc's own fix path.
