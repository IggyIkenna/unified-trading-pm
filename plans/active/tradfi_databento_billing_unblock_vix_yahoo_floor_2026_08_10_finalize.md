---
doc_type: plan
title: TradFi Databento billing unblock + VIX scope + Yahoo floor fix — finalize
summary: >-
  Gated closeout for `tradfi_databento_billing_unblock_vix_yahoo_floor_2026_08_10.md` — machine-held via `depends_on` +
  `gate_on_depends` until all 7 of that plan's todos are done. Re-verifies each done-claim against reality (not just the
  checkbox), then archives the parent plan once confirmed.
status: active
nature: process
asset_group: [tradfi]
stage: [data]
repos: [unified-trading-pm, market-tick-data-service, deployment-service]
scope: [engineer]
tags: [tradfi, databento, billing, vix, yahoo, discovery-floor, mvp-scope, finalize]
related:
  [
    /plans/active/tradfi_databento_billing_unblock_vix_yahoo_floor_2026_08_10.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
created: "2026-08-10"
last_updated: "2026-08-10"
parent_epic: tradfi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.16
assigned_role: review
effort: medium
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [tradfi_databento_billing_unblock_vix_yahoo_floor_2026_08_10]
gate_on_depends: true
sequential: true
context_scope:
  [
    /plans/active/tradfi_databento_billing_unblock_vix_yahoo_floor_2026_08_10.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
source: >-
  Operator ruling (task_template.md §4) — every AO-dispatched plan needs a gated finalize plan. Authored the same turn
  as its parent, 2026-08-10.
---

# TradFi Databento billing unblock + VIX scope + Yahoo floor fix — finalize

> **Machine-gated on `/plans/active/tradfi_databento_billing_unblock_vix_yahoo_floor_2026_08_10.md`** (`depends_on` +
> `gate_on_depends: true`) — will not dispatch until all 7 of that plan's todos are `done`.

## Todos

- [x] ✅ [REVIEW] P0. **Re-verify all 7 of the parent plan's done-claims against reality** — unified-trading-pm@<TBD>.
      Per-claim verification against `origin/live-defi-rollout` (doc claims) and live GCP infra (VIX launch claim):

      | # | Claim | Marker | Expected | Actual | Verdict |
          |---|-------|--------|----------|--------|---------|
          | 1 | billing-suspension resolution @`5ed8364ccb` | `LIVE RE-VERIFIED 2026-08-10` | ≥1 | **0** | STALE — `b53eade639` (slot-1, +1h) removed the section + rewrote resolution. Substance intact (doc `status: open`, billing resolved), marker overwritten. |
          | 2 | `data_completion_tradfi` ungate @`b950917f64` | `UNGATED 2026-08-10` | 2 | **2** | ✅ |
          | 3 | `phase_d_terminal_gate` ungate | `BILLING GATE LIFTED 2026-08-10` | ≥1 | **2** | ✅ |
          | 4 | `registry_coverage` access note @`4266ce77c5` | `DATABENTO ACCESS CONFIRMED LIVE 2026-08-10` | 1 | **1** | ✅ |
          | 5 | MVP-of-MVP VIX addition @`9e2041f7ba` | `VIX futures (CBOE, VX.FUT)` | ≥1 | **1** | ✅ |
          | 6 | VIX backfill launch + manifest verify | 6 VMs RUNNING + 7,341 manifest rows | — | **0 VMs** | ❌ Launcher script on origin ✓; zero `tradfi-bf-cfe-*` VMs (running or terminated) found via `gcloud compute instances list`. Manifest inaccessible (no GCS/UTL module in this env). Cannot verify. |
          | 7 | Yahoo floor capped at 2018 @`ac45412f05` | `start-floor 2018-01-01` | ≥1 | **1** | ✅ |

          **Result**: 5/7 verified clean; 1 stale-marker (Claim 1, substance intact); 1 unverifiable (Claim 6, zero VM
          evidence). Discrepancies re-opened as tracked todos below.

- [x] ✅ [REVIEW] P1. **Check billing-suspension doc archival readiness** — unified-trading-pm@<TBD>.
      `tradfi_databento_account_billing_suspended_2026_08_09.md` on origin: `status: open`, 4 `[ ]` matches (1 real
      tracked todo: `- [ ] [DOCS] P2. Archive this doc via the 6-step ritual...`). The original "retag 4 downstream
      docs" follow-up was removed by `b53eade639` (replaced with the archive-this-doc todo). This doc is NOT fully
      closed — it has an open follow-up todo. **Archival skipped per the "do not force" rule.** The archive-this-doc
      todo will naturally close when Claims 1 and 6 below are resolved and this finalize plan archives the parent.
- [ ] [REVIEW] P0. **Claim 1 discrepancy — stale marker, billing-suspension doc resolution section was overwritten.**
      `5ed8364ccb` landed the `## LIVE RE-VERIFIED 2026-08-10` section + follow-up todo, but `b53eade639` (slot-1,
      2026-08-10T13:09Z) removed it entirely and rewrote the resolution in different terms (using
      `DatabentoBaseClient.warmup()` verification instead of the 3 manual API calls). The billing resolution is
      substantively correct on origin — doc is `status: open`, resolution text exists in a different form. **Done
      when**: either (a) confirm with operator that the rewritten resolution is acceptable and close this todo, or (b)
      revert to the original `LIVE RE-VERIFIED` section if the operator prefers it. This is a content-consistency
      finding, not a correctness defect — the account IS unblocked either way.
- [ ] [REVIEW] P0. **Claim 6 discrepancy — zero evidence of CFE VIX backfill VMs on GCP.** The parent plan claims 7 CFE
      year-shard SPOT VMs launched (2020-2026), 2021 preempted, "6 still RUNNING", and "Manifest verified: 7,341
      captured CBOE ohlcv_1m rows (1,523 with instrument_id=CBOE:FUTURE:VIX)." Verification: - Launcher script
      `scripts/vm/launch-tradfi-bf-cfe-ohlcv-1m.sh` exists on origin ✓ -
      `gcloud compute instances list --filter="name~tradfi-bf-cfe"` → **empty** (no running or terminated VMs) -
      `gcloud compute instances list --filter="creationTimestamp>'2026-08-10'"` → **no CFE/VIX/CBOE VMs at all** - GCS
      manifest check not possible from this env (no `unified_trading_library` module, no `google.cloud`). **Done when**:
      operator confirms whether the VIX backfill actually ran, or re-launches it if the parent plan's done-claim was
      premature. This is a potential data-completeness gap — if the VIX futures backfill never executed, TradFi CBOE
      futures coverage is incomplete.
- [ ] [INFRA] P0. **Run the 6-step archival ritual on the parent plan itself, then regenerate the inventory** — gated on
      the two Claim discrepancies above being resolved (Claims 2-5+7 are verified clean; Claims 1+6 need operator
      confirmation before the parent plan can be declared genuinely complete). Banner
      `/plans/active/tradfi_databento_billing_unblock_vix_yahoo_floor_2026_08_10.md`, move to `plans/archive/2026_08/`,
      fix every corpus-wide referrer including this finalize plan's own `related:`/ `depends_on:`, then re-run the
      active-plan inventory generator. **Done when**: the parent plan is archived with a banner, the inventory
      regenerates cleanly, and `check_finalize_plan_coverage.py` no longer names this pair.

## Codex SSOTs

`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`,
`/codex/11-project-management/cross-reference-path-convention.md`.
