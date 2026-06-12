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

Compiled by harsh-main 03:30–07:00Z with 2 sub-agent audits (72h run-volume/duration + full dispatch-emitter trace),
then DEEPENED 07:00–09:30Z with 2 more (storm attribution via log-sampling + hourly closure; n=301 billing re-sample) —
the deepening CORRECTED two first-pass claims, marked ⚠️ inline. The wall is STILL UP (verified live 03:52Z; slots 1/4/5
logged four more escalations through 05:46Z).

**What is CONCRETE (exact API data)**: per-workflow run counts (REST `total_count`), conclusion mixes
(success/cancelled/failure, all runs fetched + deduped), per-run job wall-times (jobs API), the loop forensics
(PR/commit/tree evidence), the phantom snapshot. **What is ESTIMATE**: every **$ figure and "billable minutes" total** —
GitHub's billing ledger is NOT readable by any token we hold (verified 06-12: 4 SM tokens × 2 billing endpoints, all
403/401 — billing needs owner / `Plan: read`, and the per-run `/timing` API is deprecated, returns 0). The estimates
apply per-job 1-min round-up + $0.008/min all-ubuntu assumptions to measured wall-times; treat them as
order-of-magnitude, NOT ±10%. → **2-min ask: pull Settings → Billing → Usage report (June CSV) — that makes every $
figure here ledger-true; or mint a fine-grained PAT with `Plan: read` and we automate it permanently.**

Volume facts (concrete): pathological 06-11 ran ~15,962 runs across the audited workflows vs a 06-09 baseline ~3,200 — a
~5× multiplier, and ~80% of the pathological VOLUME traces to ONE closed loop (the empty-promote loop, § Root cause #3 +
Appendix E). Estimated cost translation: ≈$390 on 06-11 vs ≈$62–81 baseline (order-of-magnitude). Raising the limit
without the loop fix re-burns whatever it is in hours.

**Your decision queue, in order:**

1. **Raise the spending limit** (only you can) — and while in Billing, **download the June usage report CSV** (or mint a
   fine-grained PAT with `Plan: read` for us): it converts every estimated $ figure in this doc to ledger truth and
   shows exactly which earlier-June days hit the previous limit raises.
2. **Review harsh's overnight changes** (§ "Changes implemented by harsh-main" below — full rationale + risk register +
   one-line reverts). Headline: a tree-SHA equality gate + runaway breaker in the two promote bots (PM LDR `932d42f4c`,
   NOT yet on main), and 4 workflows `gh workflow disable`d (reconciler, ldr-ci-monitor, ldr-to-staging-promote, ao
   tab-mirror). These were implemented to stop an instant post-restore re-burn — they are YOUR call to keep, amend, or
   revert; nothing is irreversible and the drain stays parked until you re-enable it.
3. **Walk the restore-day runbook** (bottom of doc) — ordering matters: the tree-gate fix must reach PM `main` (via
   ldr-to-main-promote, left ENABLED) before re-enabling ldr-to-staging-promote.
4. **P0 remediation todos** (§ Remediation plan) — re-ranked after the attribution audit: stale-check/auto-recover
   cooldowns are the remaining P0; the reconciler breaker/batching items were DEMOTED to P2/P3 (the deep audit cleared
   the reconciler as a spend driver — ~0.5–1% of dispatch volume).

Key context you're missing from yesterday: the 06-10 LDR-trunk decoupling did NOT reduce QGv2 volume — it
**quadrupled-to-quintupled** it (full fleet, 25 v2-running repos: 787 → 1,545 → 3,502 runs/day; § Appendix A), via the
empty-promote loop (§ Root cause #3): **87% of all v2 runs in the audited window are drain-PR re-runs (`pull_request`,
head=`live-defi-rollout`)**, not human pushes. 15 of 18 staging repos are phantom-ahead right now (§ Appendix B) —
that's what the unfixed drain would chew on at restore.

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

This is NOT a payment-instrument problem. **Corrected numbers (deep audit 06-12, n=301 run-duration samples +
conclusion-mix weighting; supersedes the first-pass ~$245/day estimate)**: the pathological 06-11 day burned **≈48,700
billable min ≈ $390** across the audited workflow set; the healthy 06-09 baseline was **≈$62–81/day** — i.e. the broken
machinery multiplied spend ~5×. The 3,000 free min/month last hours. 24/25 repos are private (only uts-ui is free — why
it stayed green through every wall). The deep audit also showed the "four structural problems" below are really **one
dominant closed loop (#3, ~80% of pathological spend directly + via fan-out) plus three secondary issues** — the
attribution evidence is in Appendix E. Numbered findings kept for traceability:

1. **Recovery bots lack circuit breakers — a real resilience gap, but NOT the storm source. ⚠️ CORRECTION 2026-06-12
   (deep audit)**: the first-pass analysis attributed the `ci-status-update` storm (13/hr → 145–166/hr) primarily to
   `ci-status-reconciler.yml`'s sleep-70 dispatch stream. **That attribution was WRONG.** Three independent measurements
   (Appendix E): (a) hour-by-hour closure — ci-status-update creations ≈ fleet v2 completions to a residual of **5 runs
   over 27 hours**; (b) log sampling — **27/27** sampled dispatch payloads carry a `sha` (the v2-emitter signature), 0
   reconciler-shaped, across storm/loop/baseline windows alike; (c) the reconciler's own runs show it ticked only
   ≤25×/day (~hourly effective, NOT `*/15`) emitting 0–7 dispatches/tick ≈ **10–40/day total (~0.5–1%)**. So ≥99% of
   ci-status-update volume is the `if: always()` fan-out from v2 completions (`python-quality-gates-v2.yml:624`) — i.e.
   **entirely downstream of the empty-promote loop (#3)**; even the 00:00–02:30Z "storm" was 100% v2 fan-out from LDR
   drain-PR re-runs (mdps/e2e/tas/ibkr). What REMAINS true and needs fixing: the stale-check /
   `ci_failure_watcher --auto-recover` / `ldr-ci-monitor` re-trigger paths have no per-sha memory, cooldown, or
   fleet-red breaker — during an outage they re-fire full v2 runs (which DO cost full price, finding #3) against heads
   that cannot newly pass. The conflict-resolve pair (0 → ~2,600 runs/day combined, `promotion-conflict` dispatched per
   conflicted repo per sweep with no dedup) is the same breaker-less pattern.
2. **The per-job 1-minute round-up tax — corrected smaller than first-pass**: `ci-status-update.yml` does ~25–40 s of
   real work; a typical success run executes **2** jobs (update + persist; build-message/notify usually SKIPPED, and
   skipped jobs bill 0) → ~2 min, with notify-worthy transitions at 4 jobs. Two samplers measured 2.17 (n=17) and 3.53
   (n=31) min/success — treat as a 2.2–3.5 range (transition-heavy days skew high). Crucially **51–54% of its runs are
   concurrency-cancelled at 0 jobs** (`manifest-update` group keeps ≤1 pending; superseded pendings cancel) and bill
   **$0**. Corrected 06-11 burn: **≈3,500–5,600 min (~$28–45)**, not the naive 14,000 (~$112). Still pure bookkeeping
   overhead, still worth the 1-job collapse + side-store cutover — but a second-order spender, not a primary one.
3. **quality-gates-v2 is THE spender — ~63% of corrected 06-11 total** (≈30,559 of ≈48,700 min; deep-sampled n=217:
   fleet volume-weighted **8.7 min/run**, per-repo spread 4× — UTL 14.6 / features 13.4 / UAC 10.5 … deployment-ui 3.7;
   **failures bill the same as successes**, 9.1 vs 8.6 min, n=52 — no fail-fast discount). **PINNED — the EMPTY-PROMOTE
   LOOP (squash-accounting trap) drives it**: full-fleet QGv2 volume (25 repos run v2, not 16 — full scan) went 787 →
   1,545 → **3,502** runs/day post-decoupling, and **87% of all v2 runs in the 06-11→06-12 window were `pull_request`
   runs with head=`live-defi-rollout`** — i.e. drain-PR re-runs, not human pushes. Cause: `ldr-to-staging-promote`'s
   "ahead?" gate read `compare ahead_by`, which after a **squash**-merge NEVER returns to 0 (LDR's commits never
   literally land on staging; the merge-base compare reports the same phantom changed-files forever). Verified on
   features-service 06-11: **375 drain PRs opened+merged in one day, every ~70 s, each squash commit provably EMPTY**
   (`git show` = zero file changes; consecutive staging trees identical; each PR still reporting "7 changed files" —
   phantom), each PR spawning a full QGv2 run (450 that day on features alone). The loop is fully self-contained: sweep
   → empty PR → green v2 → ci-status-update (fan-out, #1) → `tier-ab-green` dispatch → next sweep (~70 s, 13× its 15-min
   design cadence). **Each phantom PR also fed the riders**: `staging-lock-check` (3,037 runs ≈ 4,500 min on 06-11 — a
   hidden spender absent from the first-pass table) + `plan-alignment-agent` + the conflict pair. Fleet snapshot
   2026-06-12: **15 of 18 staging repos sit tree-IDENTICAL with ahead_by 1–189** — on billing restore the unfixed gate
   would resume empty-looping on all 15 simultaneously. FIX SHIPPED (see mitigations): TREE-SHA equality gate (identical
   `commit.tree.sha` == nothing to promote, immune to squash history) in BOTH promote bots (`ldr-to-main-promote`'s
   changed-files-count gate has the same merge-base flaw — it survived only because PM's main-backmerge merge-commit
   advances the merge-base), plus a generic RUNAWAY BREAKER (≥30 drain merges per repo per 6 h → refuse + CRITICAL page)
   that catches ANY future promote-loop shape, not just tree-equal ones. **Fixing #3 collapses #1's dispatch volume and
   the riders 1:1.**
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

| Workflow                     | Repo               | Why                                                                                                                                                                                                              | Revert                                                                                                 |
| ---------------------------- | ------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| `tab-mirror-to-ldr.yml`      | agent-orchestrator | Retired (Path-B); 18 peer repos already `disabled_manually`, this was the last ACTIVE one (96 runs/day zombie)                                                                                                   | `gh workflow enable tab-mirror-to-ldr.yml -R IggyIkenna/agent-orchestrator` (recommend: keep disabled) |
| `ci-status-reconciler.yml`   | PM                 | Precautionary — was the SUSPECTED storm source; deep audit later CLEARED it (~0.5–1% of dispatch volume, Appendix E). Harmless to re-enable once the fleet is no longer drifted; kept disabled pending your call | `gh workflow enable ci-status-reconciler.yml -R IggyIkenna/unified-trading-pm`                         |
| `ldr-ci-monitor.yml`         | PM                 | Hourly unconditional v2 dispatch × ~24 repos into a red fleet                                                                                                                                                    | `gh workflow enable ldr-ci-monitor.yml -R IggyIkenna/unified-trading-pm`                               |
| `ldr-to-staging-promote.yml` | PM                 | 15/18 repos phantom-ahead (Appendix B) → unfixed gate resumes the empty-promote loop on first post-restore tick                                                                                                  | `gh workflow enable ldr-to-staging-promote.yml -R IggyIkenna/unified-trading-pm`                       |

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

**End-to-end DRY-RUN executed 2026-06-12 ~07:55Z (closes the top risk item)**: the full promote step (extracted verbatim
from the YAML) ran on-host against the live fleet with `DRY_RUN=true` + an `act` harness validated the job wiring
(App-token mint 139531741 + checkout + gates). Results: tree gate SKIPped all **14 phantom repos** and identified **12
open phantom drain PRs** ("would close", correctly NOT closed in dry-run); PROCEED branch passed the **4 real-drift
repos** (deployment-api +6, deployment-service +6, deployment-ui +145, agent-orchestrator +20) through tier gates to
"would open PR"; breaker untripped (correct — last drain merges >6 h old); outputs + exit 0 clean; zero mutations. Two
dry-run side-effect bugs were FOUND + FIXED during test prep (phantom-close and breaker Slack page ran even in dry-run —
both now `DRY_RUN`-guarded, commit below). ⚠️ The act run also surfaced a NEW restore-day blocker: **Tier B blocks the
entire drain because the latest full-workspace SIT conclusion is `failure`** — but that failure is a 0-step billing
kill, not a real SIT verdict → at restore, dispatch `full-workspace-sit` and let it complete green (or the drain no-ops
at Tier B even once re-enabled). Added to runbook.

**NOT verified (residual risk register)**:

- No actionlint locally; the act harness validates wiring but uses host tooling — the **runner's gh version** for the
  `--jq 'now|strftime'` builtins is assumed same-family (works on host gh; unverifiable until billing restores).
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

Savings estimates against the corrected 06-11 burn (≈48.7k min ≈ $390; healthy 06-09 baseline ≈ $62–81/day — post-fix
target). Priorities re-ranked after the attribution audit (Appendix E): the spend fixes are the #3-loop items;
reconciler items are RESILIENCE, demoted from P0. Companion plans: `ci_status_firestore_side_store_2026_06_10.md` (Phase
2 = the structural ci-status fix), `gh_rate_budget_reduction_2026_06_10.md` (API-rate sibling),
`cicd_workflow_sprawl_audit_2026_06_10.md` (dead workflows).

- [ ] [CICD] P2 (was P0 — demoted: attribution cleared the reconciler as a spend driver, ~10–40 dispatches/day).
      **Reconciler fleet-red circuit breaker + per-tick cap** — `unified-trading-pm`
      `.github/workflows/ci-status-reconciler.yml`: (a) cap dispatches/tick (≤5); (b) if >40% of repos drift in one tick
      → ONE Slack CRITICAL ("systemic CI outage"), dispatch NOTHING; (c) skip repo if last tick dispatched the same
      target status and that run failed. Good hygiene before re-enabling, no longer a spend precondition. (~0.5 day)
- [ ] [CICD] P3 (was P0 — same demotion; at ≤25 ticks/day the batching saves ~minutes). **Batch the reconciler's
      dispatches** — ONE `ci-status-update` dispatch with `client_payload.updates[]`; teach `ci-status-update.yml` to
      apply N statuses in one run/one manifest commit. (~0.5 day)
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
- [ ] [CICD] P1. **Collapse ci-status-update to 1 job + shallow clone** — typical success run is 2 executed jobs (the
      round-up tax is per-JOB): fold persist (+notify when worthy) into the update job as steps; drop `fetch-depth: 0`
      (1-file edit + retry-rebase needs no history). ~2 min → 1 min/run ≈ **~500–1,000 min/day saved at baseline
      volumes** (corrected from the first-pass ~6,100 — that assumed 4 billed jobs on every run; in reality notify jobs
      usually skip and 51–54% of runs are 0-job cancellations). (~0.5 day)
- [ ] [CODE] P1. **ci_status Firestore side-store Phase 2 cutover** (existing plan
      `ci_status_firestore_side_store_2026_06_10.md`) — emitters write `scripts/cicd/ci_status_store.py` DIRECTLY (CAS
      no-downgrade already built); readers (`tier_c_promotion_gate.py` et al) read the store; the per-status Actions run
      disappears entirely. Structural elimination of spender #2 (corrected: ~1–2k min/day at baseline, ~3.5–5.6k on a
      pathological day). (medium)
- [ ] [CICD] P1. **Promote the stranded `ci(spend)` crons to `main` fleet-wide** — the `*/20→hourly` backmerge
      relaxation is inert on 21/25 repos (LDR-only). Rides the normal LDR→staging→main drain post-restore; VERIFY with
      `for r in …; do git -C $r show origin/main:.github/workflows/main-backmerge-to-ldr.yml | grep cron; done` — worth
      ~1,000 runs/day. Also delete `tab-mirror-to-ldr.yml` from `main` everywhere (currently only disabled-by-API; the
      file deletion is already on LDR). (rides existing promotion)
- [ ] [CICD] P2. **ldr-ci-monitor conditional dispatch** — only re-dispatch a repo's LDR v2 when its conclusion changed
      or >6 h since last; precondition for re-enabling. (~0.5 day)
- [ ] [CICD] P2. **v2 spend trims on the 63% heavyweight** — concurrency `cancel-in-progress: true` on PR-synchronize
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
first sweep should log `SKIP … tree == LDR tree` for the ~14 phantom repos (closing their 12 stale open drain PRs) and
open real PRs for the ~4 drifted ones (dep-api/dep-service/dep-ui/ao) — dry-run-verified 06-12 ~07:55Z; (4b) **dispatch
`full-workspace-sit`** (`gh workflow run full-workspace-sit.yml -R IggyIkenna/system-integration-tests`) — the drain's
Tier-B gate reads the LATEST completed SIT conclusion, which is currently a 0-step billing-kill `failure` → the drain
no-ops at Tier B until a real SIT run lands green; (5) ci-failure-watcher drains the remaining armed PRs; (6) land the
remaining P0 circuit-breaker todos via the normal path; (7) re-enable reconciler, watch
`gh run list -w ci-status-update --limit 50` for an hour (expect <15/hr); (8) re-enable ldr-ci-monitor after its
conditional-dispatch fix; (9) verify the stranded `ci(spend)` crons reached `main` (item above).

## Appendix — data backing the findings (collected 2026-06-12 03:30–06:00Z)

### A. quality-gates-v2 runs/day per repo (REST `total_count`, `created=` windows — `gh run list` caps at 1000)

The 06-10 LDR-trunk decoupling was expected to REDUCE CI QG volume; it quintupled instead (the empty-promote loop). ⚠️
This table covers the 16 repos first sampled; a later full scan found **25 repos run v2** — full-fleet totals are **787
/ 1,545 / 3,502** for 06-09/10/11 (extra volume in the 06-11→06-12 window: unified-trading-api 237, strategy-service 88,
execution-service 72, deployment-api 65, deployment-service 49, batch-live-reconciliation 47, fund-administration 44,
alerting 34, ml-service 25). Subset table (still ~85% of volume):

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

Refreshed ~07:50Z (morning LDR pushes landed): deployment-service flipped PHANTOM→REAL (ahead_by 6) → **14 PHANTOM / 4
REAL**; 12 of the 14 phantoms carry a stale OPEN drain PR (the fix closes them on its first real sweep). Verified again
by the full dry-run sweep at ~07:55Z (§ Changes implemented, end-to-end dry-run).

### C. Top spenders — CORRECTED (n=301 stratified duration samples, conclusion-mix weighted; supersedes the first-pass 5-sample table)

06-11 (pathological day), measured volumes × measured billable-min distributions:

| Workflow                                  | Runs (06-11)      | Bill min/run (weighted)                          |       Billable min |
| ----------------------------------------- | ----------------- | ------------------------------------------------ | -----------------: |
| quality-gates-v2 (25-repo fleet)          | 3,502             | 8.7 mean (3.7 dep-ui … 14.6 UTL; fail ≈ success) |        **≈30,559** |
| ci-status-update (PM)                     | 3,501 (54% canc.) | 2.2–3.5/success; cancelled = 0                   |       ≈3,500–5,600 |
| staging-lock-check (fleet) — hidden in v1 | 3,037             | ~1.5                                             |             ≈4,462 |
| deterministic-promotion-conflict-resolve  | 1,303             | exactly 2.0                                      |              2,587 |
| ldr-to-staging-promote (PM)               | 1,241 (8% canc.)  | ~1.7                                             |              2,095 |
| conflict-resolution-agent (PM)            | 1,294             | exactly 1.0                                      |              1,294 |
| backmerges + plan-align + ldr-to-main     | ~2,084            | exactly 1.0                                      |              2,084 |
| **TOTAL (audited set)**                   | ~15,962           |                                                  | **≈48,700 ≈ $390** |

Baseline 06-09 (same method): ≈7,800–10,200 min ≈ **$62–81/day**. Steady-state cron floor ≈1,400 min/day (~$11).
Unaudited tail (semver-agent, watchers, SIT, notify) adds somewhat to both. Growth curves (runs/day): ci-status-update
815 → 1,492 → **3,501**; ldr-to-staging-promote 90 → 298 → **1,241**; conflict pair 0 → 946 → **2,597**. Notable: QGv2
**failure runs bill the same as successes** (9.1 vs 8.6 min, n=52) — no fail-fast discount; per-repo QGv2 cost spread is
4× (deployment-ui 3.7 vs UTL 14.6 min/run). $0.008/min ubuntu; 24/25 repos private (only uts-ui free — why it stayed
green through every wall).

### D. The empty-promote loop, forensically (features-service, 06-11)

- 100/100 most-recent QGv2 runs: trigger `pull_request`, actor `uts-ci-poller[bot]`, **all on head SHA `06a83fb6`**,
  **all green**, one every ~83 s for 2.3 h (21:02–23:21Z) — ~1,480 billable min re-verifying one already-green commit.
- Drain PRs #486–490 sampled: each created→merged in ~40 s; each reports "7 changed files / +991/−750" (the SAME diff —
  phantom, merge-base-relative); **375 drain PRs merged that day**; every merged squash on staging is EMPTY
  (`git show <sha> --stat` = no files; consecutive squash trees identical).
- Loop closure: squash never lands LDR's commits on staging → `ahead_by` never hits 0 → next tick re-opens. The sweep
  ran every ~70 s (13× its 15-min design) because each green v2 → ci-status-update → `tier-ab-green` dispatch → next
  sweep — the loop accelerates itself; no external storm needed.

### E. ci-status-update attribution audit (the deep pass that CORRECTED Root-cause #1; collected 06-12 07:00–09:30Z)

Question: who sent the 3,501 ci-status-update dispatches on 06-11 (13/hr baseline → 145–166/hr)? Three independent
methods, all converging:

1. **Hourly closure** (27 hourly buckets, 06-11T00 → 06-12T03): ci-status-update runs CREATED = 3,888; full-fleet v2
   runs COMPLETED (25 repos, success+failure) = 3,883 → **residual 5 runs over 27 hours** (per-hour ±jitter is
   :00-boundary smearing). v2 fan-out (`if: always()` at `python-quality-gates-v2.yml:624`) explains effectively ALL
   volume; there is no unexplained sender.
2. **Direct log classification** (persist job echoes the payload; v2-emitted carries a 40-char `commit_sha`,
   reconciler-emitted doesn't): 27 runs sampled across three windows — storm 06-12 00:00–02:30Z, promote-loop 06-11
   21:00–23:30Z, baseline 06-11 12:00–16:00Z — **27/27 v2-emitted, 0 reconciler**. Storm samples were mdps×4,
   e2e-testing×4, uac×1, matching the storm-window v2 leaders (369/390 of those v2 runs were `pull_request` on LDR).
3. **Reconciler bounded from its own run logs**: it ticked 25/21/17×/day (effective ~hourly, not `*/15`) emitting 0–7
   dispatches/tick → **~10–40 dispatches/day (~0.5–1%)** — invisible at storm scale. The first-pass "sleep-70 stream ≈
   51/hr" model overestimated it ~5× (it assumed every tick walks a fully-drifted fleet; real ticks corrected 0–1).

Conclusion mix (all 6,117 runs in window fetched + deduped; matches API total_count exactly): 06-09 = 487 success / 239
cancelled / 11 failure; 06-10 = 825/665/2; 06-11 = 1,586/**1,907**/8; 06-12 partial = 227/147/13 (all 13 post-wall
billing-kills). Cancelled runs verified 0-jobs (bill $0) — superseded pendings in the `manifest-update` concurrency
group. Billable estimate per success run: 2 executed jobs typical (notify/build-message usually skipped) — two samplers
measured 2.17 (n=17) and 3.53 (n=31) min/success; treat as 2.2–3.5 (transition-heavy days run more 4-job notify runs).
Corrected ci-status-update billable: ≈1,080 / ≈1,790 / ≈3,460–5,600 min for 06-09/10/11 — roughly ¼ of the naive
all-runs×4-min figure.

**What this changes**: ≥99% of ci-status-update volume is v2-completion fan-out → entirely downstream of the
empty-promote loop (#3). Fixing #3 collapses ci-status-update, staging-lock-check, plan-alignment and the conflict pair
1:1. The reconciler/ldr-ci-monitor disables remain harmless-but-precautionary; the reconciler breaker work is hygiene
(P2/P3), not a spend fix. Known caveats: billable minutes are jobs-API wall-time estimates with per-job round-up (the
`/timing` API is deprecated, returns 0 — no ledger numbers available to a collab token); cancelled-run sender
attribution is by arithmetic closure (0 jobs = no logs); Actions secret-masking hid the `status` values in sampled logs
(repo + sha presence were readable).
