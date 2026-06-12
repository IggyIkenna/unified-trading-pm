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

## ⚡ Shift-start handoff (Ikenna, 2026-06-12 morning) — read this first

Compiled by harsh-main 03:30–07:00Z with 2 sub-agent audits (72h run-volume/duration + full dispatch-emitter trace). The
wall is STILL UP (verified live 03:52Z; slots 1/4/5 logged four more escalations through 05:46Z). The budget keeps
blowing because of four structural burn drivers (§ Root cause below, each with data) — **fleet burn ≈ 30,600 billable
min/day ≈ $245/day**; raising the limit without the fixes re-burns it in hours.

**Your decision queue, in order:**

1. **Raise the spending limit** (only you can).
2. **Review harsh's overnight changes** (§ "Changes implemented by harsh-main" below — full rationale + risk register +
   one-line reverts). Headline: a tree-SHA equality gate + runaway breaker in the two promote bots (PM LDR `932d42f4c`,
   NOT yet on main), and 4 workflows `gh workflow disable`d (reconciler, ldr-ci-monitor, ldr-to-staging-promote, ao
   tab-mirror). These were implemented to stop an instant post-restore re-burn — they are YOUR call to keep, amend, or
   revert; nothing is irreversible and the drain stays parked until you re-enable it.
3. **Walk the restore-day runbook** (bottom of doc) — ordering matters: the tree-gate fix must reach PM `main` (via
   ldr-to-main-promote, left ENABLED) before re-enabling ldr-to-staging-promote.
4. **P0 remediation todos** (§ Remediation plan) — the reconciler circuit-breaker/batching + stale-check cooldowns are
   preconditions for re-enabling the monitors you built.

Key context you're missing from yesterday: the 06-10 LDR-trunk decoupling did NOT reduce QGv2 volume — it **quintupled**
it (505 → 918 → 2,857 runs/day, § Appendix A), via the empty-promote loop (§ Root cause #3). 15 of 18 staging repos are
phantom-ahead right now (§ Appendix B) — that's what the unfixed drain would chew on at restore.

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

## Changes implemented by harsh-main 2026-06-12 — REVIEW REQUESTED (Ikenna owns this surface)

> Implemented (rather than only proposed) because every hour post-restore without them re-burns budget — but they are
> **not peer-reviewed** and CI/CD nuance lives with Ikenna. Each entry: what/why/verified/NOT-verified/revert. Nothing
> here is irreversible.

### A. Four workflows disabled via API (state change only — no commits, instantly reversible)

| Workflow                     | Repo               | Why                                                                                                             | Revert                                                                                                 |
| ---------------------------- | ------------------ | --------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| `tab-mirror-to-ldr.yml`      | agent-orchestrator | Retired (Path-B); 18 peer repos already `disabled_manually`, this was the last ACTIVE one (96 runs/day zombie)  | `gh workflow enable tab-mirror-to-ldr.yml -R IggyIkenna/agent-orchestrator` (recommend: keep disabled) |
| `ci-status-reconciler.yml`   | PM                 | Primary storm source (§ Root cause #1): fleet is maximally drifted → its max firing state at restore            | `gh workflow enable ci-status-reconciler.yml -R IggyIkenna/unified-trading-pm`                         |
| `ldr-ci-monitor.yml`         | PM                 | Hourly unconditional v2 dispatch × ~24 repos into a red fleet                                                   | `gh workflow enable ldr-ci-monitor.yml -R IggyIkenna/unified-trading-pm`                               |
| `ldr-to-staging-promote.yml` | PM                 | 15/18 repos phantom-ahead (Appendix B) → unfixed gate resumes the empty-promote loop on first post-restore tick | `gh workflow enable ldr-to-staging-promote.yml -R IggyIkenna/unified-trading-pm`                       |

`ldr-to-main-promote` left ENABLED deliberately — it must carry the fix commit to PM `main` at restore.

### B. Workflow code change: PM LDR `932d42f4c` (NOT on main yet — review the diff before it promotes)

`git show 932d42f4c` — 2 files, +54/−2, both changes additive gates BEFORE existing logic (the PROCEED path is
byte-identical to prior behaviour):

1. **`ldr-to-staging-promote.yml` — tree-SHA equality gate** after the `ahead_by` check: fetch `commit.tree.sha` of
   LDR + staging heads; equal trees → SKIP (+ close any open phantom drain PR with an explanatory comment). **Reason**:
   the `ahead_by`-only gate is the proven empty-promote loop (§ Root cause #3 — 375 empty merges/day on
   features-service; each merged squash `git show` = zero changes). Tree equality is the exact "content, not
   commit-count" signal and is immune to squash history.
2. **`ldr-to-staging-promote.yml` — runaway breaker** before the tier gate: ≥30 `chore(promote)` drain merges on one
   repo within 6 h → refuse + Slack CRITICAL. **Reason**: generic net for ANY future promote-loop shape (operator ask:
   "catch other such cases"). Healthy max is 24/6h (every cron tick); a 70 s loop trips at ~35 min. Window chosen 6 h
   not 24 h because ao + deployment-ui had >100 merges in the last 24 h AND have real drift — a 24 h window would have
   wrongly blocked their legitimate post-restore promotion.
3. **`ldr-to-main-promote.yml` — same tree gate** ahead of the changed-files-count check, inside the no-open-PR branch
   only (the existing-PR/arming path is untouched, so quickmerge's standing-PR model is unaffected). **Reason**: the
   `compare …files|length` gate has the same merge-base flaw — it counts files touched since merge-base, not tree delta;
   it survived on PM only because main-backmerge's merge-commit advances the merge-base. Make it exact, not
   incidentally-correct.

**Verified**: YAML parses; `bash -n` clean on every run block; the EXACT `gh api`/`gh pr list --jq` commands
smoke-tested from laptop against the live fleet (tree gate: SKIPs all 15 phantoms incl. mdps ahead_by=130 / ibkr 189,
PROCEEDs the 3 real-drift repos; breaker jq returned real counts: features=100-capped, deployment-api=12).

**NOT verified (honest risk register)**:

- The modified workflow has **never executed end-to-end** (it's disabled + billing wall) — no live run, no actionlint
  (not installed locally).
- `--jq 'now|strftime'` builtins behave on local gh; the **runner's gh version is assumed** same-family (unverified).
- Phantom-PR close vs `ci_failure_watcher --auto-recover` interplay: watcher targets BLOCKED open PRs, a closed PR
  should be out of scope — **expected no interplay, unverified**.
- +2 `gh api` calls/repo/tick (~36/tick) + 1 `gh pr list`/active repo against the App-token pool — trivial vs the 5k/hr
  budget, unmeasured.
- Tree-gate fail-open: on API error the sentinels (`ERR_LDR`≠`ERR_STG`) compare unequal → behaves exactly like the old
  gate (loop possible during API errors). Chosen so a GitHub blip can't dam promotion; flag if you prefer fail-closed.

**QG caveat**: local `quality-gates.sh` could NOT go green for this ship — both failure modes are the PRE-EXISTING
typecheck-debt you filed 2026-06-11
(`fix(qg): bump PM scripts/ basedpyright ceiling 1511->1517 + file typecheck-debt follow-up`): without UAC in the venv,
coverage fails (61.4% — prospectus tests skip on missing pydantic); with UAC installed, basedpyright jumps to 1606 >
1517 ceiling (CI sees ~1454 via content-first clone — three-way count drift). Diff contains zero Python, so shipped
under carve-out 3 (PM `.github/**` to unblock the pipeline — same path as your `ci(spend)` pushes). **Revert**:
`git revert 932d42f4c` on LDR.

### C. Local-host change (hk laptop only, no repo effect)

Installed `unified-api-contracts` (editable) + `pydantic 2.13.4` into PM `.venv` — un-skips the prospectus tests
(coverage gate passes again locally) and is what surfaced the basedpyright 1606-vs-1517 local count for the
typecheck-debt follow-up.

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

## Appendix — data backing the findings (collected 2026-06-12 03:30–06:00Z)

### A. quality-gates-v2 runs/day per repo (REST `total_count`, `created=` windows — `gh run list` caps at 1000)

The 06-10 LDR-trunk decoupling was expected to REDUCE CI QG volume; it quintupled instead (the empty-promote loop):

| repo (QGv2 runs)               |   06-09 |   06-10 |     06-11 | 06-12\* |
| ------------------------------ | ------: | ------: | --------: | ------: |
| features-service               |      11 |      42 |       450 |       0 |
| client-reporting-api           |      42 |      76 |       333 |      19 |
| agent-orchestrator             |       6 |      12 |       253 |      11 |
| unified-trading-system-ui      |       2 |      17 |       206 |      12 |
| market-data-processing-service |      32 |      93 |       201 |      65 |
| deployment-ui                  |      28 |      44 |       180 |      38 |
| unified-api-contracts          |      52 |      55 |       179 |      28 |
| unified-trading-pm             |      50 |     175 |       166 |       3 |
| system-integration-tests       |      36 |      57 |       151 |      41 |
| ibkr-gateway-infra             |      45 |      43 |       146 |      45 |
| trading-agent-service          |      42 |      46 |       139 |      47 |
| greeks-service                 |       9 |      16 |       132 |       0 |
| e2e-testing                    |      11 |      22 |       105 |      62 |
| unified-trading-library        |      41 |      56 |       102 |       3 |
| market-tick-data-service       |      51 |      69 |        67 |       3 |
| instruments-service            |      47 |      95 |        47 |       3 |
| **fleet total**                | **505** | **918** | **2,857** | **380** |

\*06-12 partial: billing wall from 02:18Z (0-step failures bill ≈ nothing).

### B. Fleet phantom-vs-real snapshot (2026-06-12 ~05:30Z; LDR vs staging)

PHANTOM = `ahead_by > 0` but `commit.tree.sha` identical (nothing promotable; the old gate loops on it). This is what
the drain faces at restore:

agent-orchestrator ahead_by=17 REAL · deployment-api 6 REAL · deployment-ui 145 REAL · client-reporting-api 61 PHANTOM ·
deployment-service 4 PHANTOM · e2e-testing 2 PHANTOM · execution-service 3 PHANTOM · features-service 13 PHANTOM ·
ibkr-gateway-infra 189 PHANTOM · instruments-service 2 PHANTOM · mdps 130 PHANTOM · mtds 2 PHANTOM · strategy-service 2
PHANTOM · system-integration-tests 123 PHANTOM · trading-agent-service 184 PHANTOM · unified-api-contracts 130 PHANTOM ·
unified-trading-library 1 PHANTOM · unified-trading-system-ui 2 PHANTOM → **15 PHANTOM / 3 REAL of 18**.

### C. Top spenders (72h audit 06-09→06-12; durations from jobs API on successful pre-kill runs; billable = per-job ceil-to-minute)

| #   | Workflow                                 | Trigger                    | Runs/day |           Bill min/run | Est min/day |
| --- | ---------------------------------------- | -------------------------- | -------: | ---------------------: | ----------: |
| 1   | quality-gates-v2 (16 repos)              | pull_request ~80%          |    1,537 |            4–16 (~9.6) |  **14,723** |
| 2   | ci-status-update (PM)                    | repository_dispatch 100%   |    2,039 | 4 (4 jobs × ~5 s each) |   **8,156** |
| 3   | Staging Lock Check (fleet)               | pull_request               |    1,198 |                      2 |       2,396 |
| 4   | ldr-to-staging-promote (PM)              | repo_dispatch ~98% (!)     |      612 |                      2 |       1,225 |
| 5   | deterministic-promotion-conflict-resolve | repository_dispatch        |      593 |                      2 |       1,186 |
| 6   | Conflict Resolution Agent (PM)           | repository_dispatch        |      588 |                      1 |         588 |
| 7   | main-backmerge-to-ldr (fleet)            | cron \*/20 (stale on main) |      377 |                      1 |         377 |

Growth curves (PM, runs/day): ci-status-update 815 → 1,492 → **3,501**; ldr-to-staging-promote 90 → 298 → **1,241**;
conflict pair 0 → 946 → **2,597** (combined). Fleet ≈ 26,188 runs/72h, PM alone 53%. Cost: ~30,600 min/day ≈ $245/day ≈
$7,350/month pace ($0.008/min ubuntu; 24/25 repos private — only uts-ui is free, which is why it stayed green through
every wall).

### D. The empty-promote loop, forensically (features-service, 06-11)

- 100/100 most-recent QGv2 runs: trigger `pull_request`, actor `uts-ci-poller[bot]`, **all on head SHA `06a83fb6`**,
  **all green**, one every ~83 s for 2.3 h (21:02–23:21Z) — ~1,480 billable min re-verifying one already-green commit.
- Drain PRs #486–490 sampled: each created→merged in ~40 s; each reports "7 changed files / +991/−750" (the SAME diff —
  phantom, merge-base-relative); **375 drain PRs merged that day**; every merged squash on staging is EMPTY
  (`git show <sha> --stat` = no files; consecutive squash trees identical).
- Loop closure: squash never lands LDR's commits on staging → `ahead_by` never hits 0 → next tick re-opens. The dispatch
  storm (tier-ab-green per status green) ran the "15-min" sweep every ~70 s.
