---
title: "GitHub Actions BILLING wall — fleet-wide CI outage (every v2 job insta-fails) + spend root-cause & burn-down"
created: 2026-06-11
source:
  - live diagnosis 2026-06-11 ~16:10Z — every quality-gates-v2 job (PM + deployment-api + fleet) fails in ~7s, 0 steps
  - "spend root-cause audit 2026-06-12 (harsh + 2 sub-agents) — 72h run-volume/duration audit + full dispatch-emitter
    trace; operator quote — we have increased the github budget several times already this month and we are just 12 days
    in"
locked_by: live-defi-rollout
priority: P1
status: active
---

# GitHub Actions billing wall — fleet-wide CI outage

## What I found

From ~2026-06-11T16:10Z every `quality-gates-v2` job fleet-wide fails in ~7 s with **zero steps executed**. Run
annotation (`gh run view 27361472099 --repo IggyIkenna/unified-trading-pm`):

> The job was not started because **recent account payments have failed or your spending limit needs to be increased**.
> Please check the 'Billing & plans' section in your settings

This is GitHub-account billing on `IggyIkenna` — not a workflow/code problem (python-quality-gates-v2.yml unchanged +
actionlint-clean; the same signature reproduces on PM, deployment-api, and dispatch + pull_request triggers alike).
deployment-ui#104 merged minutes earlier on a green v2 — the wall began between those runs.

## Why it matters

**ALL promototion machinery is frozen**: LDR→staging drains, staging→main, semver-agent, SIT, ldr-to-main-promote —
every Actions-backed gate. Armed auto-merge PRs (PM#273, deployment-api#59) sit BLOCKED until Actions runs again.

## Recommended decision

Operator-only (payment instrument): **github.com/settings/billing** → fix the failed payment / raise the Actions
spending limit. No code change needed; on restoration the armed PRs re-run v2 and self-merge. Paged to Slack (#alerts
webhook, direct curl — the notify-slack workflow itself cannot run) + desktop push 2026-06-11.

## Recurrence log

**2026-06-12 ~02:17Z** — billing wall struck again mid-session (escalation agt-35f2b9, slot 1):

- CI succeeded fleet-wide at 01:51Z, then failed starting 02:17Z (window: ~50+ minutes confirmed still failing at
  03:12Z)
- Confirmed private-repo pattern: `unified-trading-system-ui` (public repo) CI succeeded throughout; all private repos
  (MDPS, PM, UTL, UAC, features, strategy, execution, alerting) fail 2-8s with 0 steps
- Local QG for `market-data-processing-service` = GREEN (1867 tests pass); code is correct
- `ldr-to-staging` PR #281 blocked; re-trigger once billing restored:
  `gh workflow run quality-gates-v2.yml --repo IggyIkenna/market-data-processing-service --ref live-defi-rollout`
- Pattern: payment-failed billing wall — operator action required

**2026-06-12 ~03:00Z** — billing wall continuing (escalation agt-6b2b49, slot 5):

- `alerting-service` `quality-gates-v2` flagged as `ldr_qg_failure`; local QG exits 0 on commit 897cd93 (56 gates pass)
- CI run 27391644203 failed at 03:00Z (7s, 0 steps); re-triggered 27393052323 at 03:43Z still failed (7s, 0 steps)
- Diagnosis: billing wall, NOT code — `alerting-service` code is correct
- Re-trigger once billing restored:
  `gh workflow run quality-gates-v2.yml --repo IggyIkenna/alerting-service --ref live-defi-rollout`
- agt-6b2b49 escalation id

**2026-06-12 ~03:52Z** — wall verified LIVE by fresh dispatch (harsh main):
`gh workflow run main-backmerge-to-ldr.yml --repo IggyIkenna/ibkr-gateway-infra` → run 27393331741 killed in **2 s, zero
steps** ("Job is about to start running on the hosted runner…" then nothing). 26/26 PM runs since 02:20Z failed;
githubstatus.com all-operational → account spending limit, not platform. Operator (Ikenna) pinged.

**2026-06-12 ~04:45Z** — wall still active (escalation agt-7060d4, slot 1):

- `alerting-service` `quality-gates-v2` re-escalated as `ldr_qg_failure`; local QG exits 0 on commit 897cd93 (all gates
  pass); code is correct
- Re-trigger attempted: run 27395083894 failed in 6 s, zero steps — billing wall still blocking all private-repo CI
- No code fix needed; blocked on operator billing restore
- Re-trigger once billing restored:
  `gh workflow run quality-gates-v2.yml --repo IggyIkenna/alerting-service --ref live-defi-rollout`
- agt-7060d4 escalation id

**2026-06-12 ~05:08Z** — wall still active (deployment-ui monitoring work, slot 4):

- 3 deployment-ui changes landed on LDR, all locally GREEN (full UI QG + pw:L2 198–199/199), all blocked from promotion
  by the wall: flicker `ef08fd8` + ReadinessTab `074c349` (LDR→staging drains' v2 failed 0-step) +
  promotion-pipeline-viz `6fe7d73` (PR #235 BLOCKED — rollup has only Vercel, no `quality-gates-v2`). PM watchers
  (freeze-deferred-build-replay, cloud-build-failure-watcher) also failing 05:08Z. `unified-trading-system-ui` (public)
  unaffected — consistent with the private-repo-only pattern.
- Re-trigger on restore: `gh workflow run quality-gates-v2.yml --repo IggyIkenna/deployment-ui --ref live-defi-rollout`.
  NB: commit `6fe7d73` carries a literal skip-ci marker in its body (a substring in the feature description, which also
  mis-routed quickmerge to a direct LDR→main PR #235) → its PR head will NOT auto-run v2 even after restore; the manual
  dispatch above is required for it specifically.

**2026-06-12 ~05:46Z** — wall still active (escalation agt-72fb64, slot 5):

- `alerting-service` `quality-gates-v2` re-escalated as `ldr_qg_failure` (4th escalation for this repo today)
- Local QG exits 0 on commit `897cd93` (56 gates pass, 38s); code is correct, no fix needed
- Last CI success: run 27388159503 at 01:18Z; all runs since 02:17Z fail 0-step (billing wall)
- Latest CI failure: run 27396304355 (main-backmerge-to-ldr) at 05:20Z; PM latest: 05:46Z — wall ongoing
- Re-trigger once billing restored:
  `gh workflow run quality-gates-v2.yml --repo IggyIkenna/alerting-service --ref live-defi-rollout`
- agt-72fb64 escalation id — BLOCKED needs operator billing restore

## Root cause — why the budget keeps blowing (audit 2026-06-12)

This is NOT a payment-instrument problem. The fleet's burn rate is **~30,600 billable min/day ≈ $245/day ≈ $7,350/month
pace** (72h audit 06-09→06-12, jobs-API durations, per-job ceil-to-minute). The 3,000 free min/month last ~2.4 h. 24/25
repos are private (only uts-ui is free — why it stayed green through every wall). Every budget raise this month was
eaten by the same four structural problems:

1. **Self-amplifying recovery loops with no fleet-red circuit breaker** (the 06-12 storm: `ci-status-update` 13/hr
   baseline → 145–166/hr from 00:00Z). Mechanism (emitter trace): `ci-status-reconciler.yml` (`*/15`,
   `cancel-in-progress: false`) emits one dispatch per drifted repo with `sleep 70` between → fleet-wide drift = a
   continuous ~51 dispatch/hr stream, runs queue back-to-back; its dispatch is fire-and-forget (`curl … || echo WARN`) —
   it never checks whether the spawned run succeeded, so while CI fails the SAME drift re-fires every tick, forever.
   Compounded by `ldr-to-staging-promote` STALE-CHECK (re-fires v2 per stale-head repo ×4/hr, no per-sha memory),
   `ci_failure_watcher.py --auto-recover` (close+reopen per blocked PR, no cooldown), and `ldr-ci-monitor` (hourly
   unconditional v2 dispatch ×24 repos). Every FAILING v2 run STILL emits a `ci-status-update` dispatch
   (`python-quality-gates-v2.yml:624` `if: always()`). **A fleet-red outage is precisely the state that maximises every
   recovery bot's firing rate.** Volume grew exponentially: ci-status-update 815 → 1,492 → **3,501**/day (06-09→06-11);
   ldr-to-staging-promote 90 → 298 → **1,241**/day (98% repository_dispatch `tier-ab-green`, NOT its `*/15` cron); the
   conflict-resolve pair (`promotion-conflict` ← promote sweep per conflicted repo per tick) 0 → ~2,600/day combined.
2. **The per-job 1-minute round-up tax**: `ci-status-update.yml` does ~23 s of real work but spans 4 jobs → bills **4
   min/run** (10×). At 3,501 runs on 06-11 ≈ 14,000 min ≈ $112 that day, for manifest bookkeeping.
3. **quality-gates-v2 is ~48% of total spend** (~14,700 min/day): ~1,537 runs/day fleet-wide × ~10 billable min
   (features 14.8, UAC ~11, UTL 9.4; failures bill the same as green) — and a large share of those runs are
   bot-RE-TRIGGERED (stale-check / close+reopen / monitor dispatch), not human pushes. **PINNED 2026-06-12 — the
   EMPTY-PROMOTE LOOP (squash-accounting trap) is the #1 QGv2 driver**: post-decoupling QGv2 volume QUINTUPLED (505 →
   918 → **2,857** runs/day, 06-09→06-11) because `ldr-to-staging-promote`'s "ahead?" gate read `compare ahead_by`,
   which after a **squash**-merge NEVER returns to 0 (LDR's commits never literally land on staging; the merge-base
   compare reports the same phantom changed-files forever). Verified on features-service 06-11: **375 drain PRs
   opened+merged in one day, every ~70 s, each squash commit provably EMPTY** (`git show` = zero file changes;
   consecutive staging trees identical; each PR still reporting "7 changed files" — phantom), each PR spawning a full
   ~7-min QGv2 run (450 that day on features alone). The dispatch storm (problem 1) turned the 15-min tick into a ~70 s
   tick, multiplying it 13×. Fleet snapshot 2026-06-12: **15 of 18 staging repos sit tree-IDENTICAL with ahead_by
   1–189** — on billing restore the unfixed gate would resume empty-looping on all 15 simultaneously. FIX SHIPPED (see
   mitigations): TREE-SHA equality gate (identical `commit.tree.sha` == nothing to promote, immune to squash history) in
   BOTH promote bots (`ldr-to-main-promote`'s changed-files-count gate has the same merge-base flaw — it survived only
   because PM's main-backmerge merge-commit advances the merge-base), plus a generic RUNAWAY BREAKER (≥30 drain merges
   per repo per 6 h → refuse + CRITICAL page) that catches ANY future promote-loop shape, not just tree-equal ones.
4. **Zombie/stale schedulers on `main`** (crons fire from the DEFAULT branch; LDR-only workflow edits are INERT —
   codified gotcha 2026-06-09): retired `tab-mirror-to-ldr` was still active-on-main long into the month (18 repos
   hand-disabled at some point; the 19th — agent-orchestrator — found ACTIVE and disabled 2026-06-12, see log below);
   the `ci(spend)` backmerge relaxation `*/20→hourly` (e8003ee2e, 06-11) reached `main` on only 4/25 repos — 21 repos
   still fire `*/20` (1,512 runs/day vs the intended 504) because the rollout landed on LDR and the LDR→main promotion
   is jammed behind this very outage.

PM alone is 53% of fleet run volume (13,868 of 26,188 runs/72h). Audit caveat: `gh run list` caps at 1000 — use
per-workflow REST `total_count` (the cap hid 93% of PM's volume from earlier reads).

## Mitigations applied 2026-06-12 (reversible, `gh workflow disable` — no main push needed)

- `tab-mirror-to-ldr` agent-orchestrator (last ACTIVE zombie; 18 peers were already `disabled_manually`) → disabled.
- `ci-status-reconciler.yml` (PM) + `ldr-ci-monitor.yml` (PM) → **disabled_manually pre-restore** so the storm does not
  instantly resume when the budget is raised (fleet is maximally drifted right now = reconciler's max firing state). NOT
  needed for backlog drain (promote bots + ci-failure-watcher do the unjamming). **Re-enable one at a time ONLY after
  the circuit-breaker todos below land on `main`.**
- `ldr-to-staging-promote.yml` (PM) → **disabled_manually pre-restore** — with 15/18 repos tree-identical-but-ahead_by>0
  it would resume the empty-promote loop on first post-restore tick. **Re-enable IMMEDIATELY after the tree-gate fix
  below reaches PM `main`** (the PM LDR→main drain PR carries it; ldr-to-main-promote stays ENABLED for that).

## Fixes SHIPPED 2026-06-12 (on PM LDR, take effect when promoted to `main`)

- **TREE-SHA equality gate** in `ldr-to-staging-promote.yml` (replaces the bare `ahead_by` gate; also closes phantom
  open drain PRs) and `ldr-to-main-promote.yml` (ahead of the merge-base-flawed changed-files count). Smoke-verified
  against the live fleet: correctly SKIPs all 15 phantom repos (incl. mdps ahead_by=130, ibkr 189) and PROCEEDs on the 3
  real-drift repos (agent-orchestrator/deployment-api/deployment-ui).
- **RUNAWAY BREAKER** in `ldr-to-staging-promote.yml`: ≥30 drain merges per repo per 6 h → refuse + Slack CRITICAL.
  Generic net — catches any future promote-loop regardless of mechanism (healthy max is 24/6h at full cron pace; a 70 s
  loop trips it in ~35 min instead of running all day).

## Remediation plan — burn-down to a sane budget (ranked by $/effort)

Savings estimates against the 06-11 burn (~30.6k min/day). Companion plans:
`ci_status_firestore_side_store_2026_06_10.md` (Phase 2 = the structural ci-status fix),
`gh_rate_budget_reduction_2026_06_10.md` (API-rate sibling), `cicd_workflow_sprawl_audit_2026_06_10.md` (dead
workflows).

- [ ] [CICD] P0. **Reconciler fleet-red circuit breaker + per-tick cap** — `unified-trading-pm`
      `.github/workflows/ci-status-reconciler.yml`: (a) cap dispatches/tick (≤5); (b) if >40% of repos drift in one tick
      → ONE Slack CRITICAL ("systemic CI outage"), dispatch NOTHING; (c) skip repo if last tick dispatched the same
      target status and that run failed. Precondition for re-enabling the reconciler. (~0.5 day)
- [ ] [CICD] P0. **Batch the reconciler's dispatches** — ONE `ci-status-update` dispatch with
      `client_payload.updates[]`; teach `ci-status-update.yml` to apply N statuses in one run/one manifest commit.
      Replaces ≤25 runs + 29 min of `sleep 70` with 1 run/tick. (~0.5 day)
- [ ] [CICD] P0. **Stale-check/auto-recover cooldowns + fleet-red breaker** — `unified-trading-pm`
      `ldr-to-staging-promote.yml` STALE-CHECK +
      `scripts/repo-management/ci_failure_watcher.py::auto_recover_stuck_prs` + the `promotion-conflict` dispatch site
      (`ldr-to-staging-promote.yml:245`): record last-retrigger (sha,time) in a PR label/comment; skip if same sha <2 h
      or ≥3 attempts; if v2 is absent/failing on EVERY checked head → Actions outage, stop + page once. Kills the
      0→2,600/day conflict-pair runaway too. (~1 day)
- [ ] [CICD] P1. **Outage-aware v2 status dispatch** — `python-quality-gates-v2.yml` "Record CI status"
      (`if: always()`): skip the dispatch when the failure is infrastructure-shaped (0-step/cancelled/billing
      annotation) rather than a gate verdict; mirrors `detect_billing_block` in ci_failure_watcher. Stops outage-driven
      FAILING spam at the source. (~0.5 day)
- [ ] [CICD] P1. **Collapse ci-status-update to 1 job + shallow clone** — 4 jobs → 1 (the round-up tax is per-JOB): fold
      build-message/notify/persist into the update job as steps; drop `fetch-depth: 0` (1-file edit + retry-rebase needs
      no history). 4 min → 1 min/run ≈ **~6,100 min/day saved at 06-11 volume** even before volume fixes. (~0.5 day)
- [ ] [CODE] P1. **ci_status Firestore side-store Phase 2 cutover** (existing plan
      `ci_status_firestore_side_store_2026_06_10.md`) — emitters write `scripts/cicd/ci_status_store.py` DIRECTLY (CAS
      no-downgrade already built); readers (`tier_c_promotion_gate.py` et al) read the store; the per-status Actions run
      disappears entirely. Structural elimination of spender #2 (~8,200 min/day). (medium)
- [ ] [CICD] P1. **Promote the stranded `ci(spend)` crons to `main` fleet-wide** — the `*/20→hourly` backmerge
      relaxation is inert on 21/25 repos (LDR-only). Rides the normal LDR→staging→main drain post-restore; VERIFY with
      `for r in …; do git -C $r show origin/main:.github/workflows/main-backmerge-to-ldr.yml | grep cron; done` — worth
      ~1,000 runs/day. Also delete `tab-mirror-to-ldr.yml` from `main` everywhere (currently only disabled-by-API; the
      file deletion is already on LDR). (rides existing promotion)
- [ ] [CICD] P2. **ldr-ci-monitor conditional dispatch** — only re-dispatch a repo's LDR v2 when its conclusion changed
      or >6 h since last; precondition for re-enabling. (~0.5 day)
- [ ] [CICD] P2. **v2 spend trims on the 48% heavyweight** — concurrency `cancel-in-progress: true` on PR-synchronize
      (stale-head runs are pure waste), audit the 6-job slice split for mergeable short jobs (per-job round-up), extend
      content-sentinel HIT skipping (CI-spend ② shipped a7be2d09b) to more paths. (~1 day, saves multiple thousand
      min/day)
- [ ] [CICD] P2. **Un-share `manifest-update` concurrency from sit-gate** — `sit-gate.yml:15-17` still shares the group
      with ci-status-update → a status storm starves SIT locking (same class as the cascade-eviction bug fixed
      PM@b6576fc27). (tiny)
- [ ] [CICD] P2. **Retire stale v1 emitter** — `unified-trading-system-ui/.github/workflows/ui-quality-gates.yml` (v1
      retired 2026-05-29) still live + dispatching ci-status-update; delete from main. Also fix uts-ui
      `Orphan Route Audit` (208/208 failures = pure red noise, public repo so $0 but alert-noise). (tiny)
- [ ] [INFRA] P1. **Run-volume watchdog (backend-driven, agent-orchestrator)** — the generic catch-other-cases net
      (operator ask 2026-06-12: "make sure that we are also going to catch other such cases"): new monitor loop in
      `agent-orchestrator/server/` beside `GhRateLimitMonitor` polling per-workflow run counts (cheap REST `total_count`
      with `created=` windows, ~30 calls/tick, 15-min tick) for the top-N workflows fleet-wide; alert Slack WARN at >3×
      trailing-7-day baseline rate and CRITICAL at >10× or >50 runs/hr for any single workflow. Would have caught the
      06-10 conflict-pair runaway and the 06-11 empty-promote loop ~2 days before the wall. (~1 day, Harsh repo)
- [ ] [INFRA] P3. **Spend telemetry** — extend `GhRateLimitMonitor`/deployment-ui Repos-CI page with a billable-minutes
      tracker (runs×duration from the runs API) + Slack alert at 50/80/95% of monthly budget, so the NEXT runaway is
      caught in hours not at the wall. (~1 day)

**Restore-day runbook (operator raises limit → do in this order):** (1) budget raised; (2) leave
`ci-status-reconciler` + `ldr-ci-monitor` + `ldr-to-staging-promote` DISABLED; (3) `ldr-to-main-promote` (enabled)
merges PM's standing LDR→main PR → the tree-gate + breaker fixes reach `main`; (4) **re-enable
`ldr-to-staging-promote`** (`gh workflow enable ldr-to-staging-promote.yml --repo IggyIkenna/unified-trading-pm`) —
first sweep should log `SKIP … tree == LDR tree` for the ~15 phantom repos and open real PRs for the ~3 drifted ones;
watch one tick to confirm; (5) ci-failure-watcher drains the remaining armed PRs; (6) land the remaining P0
circuit-breaker todos via the normal path; (7) re-enable reconciler, watch `gh run list -w ci-status-update --limit 50`
for an hour (expect <15/hr); (8) re-enable ldr-ci-monitor after its conditional-dispatch fix; (9) verify the stranded
`ci(spend)` crons reached `main` (item above).
