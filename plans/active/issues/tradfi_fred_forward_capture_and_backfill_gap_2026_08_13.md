---
doc_type: issue
title: >-
  Two live-prod FRED contradictions found in a macro-audit grace-window flag: forward-capture still accrues
  attempted_failed rows after its capability-filter fix, and the "self-sufficient-to-completion" backfill claim doesn't
  match prod (99 dates only, zero 1962-1970 floor dates, no FRED VM in the fleet)
summary: >-
  Two findings flagged (not auto-fixed) during a macro-audit re-check inside its grace window, routed via a
  blocked-question and approved for filing as one tradfi-owned issue. (1) A FRED capability-filter fix has shipped, but
  prod still accrued attempted_failed ohlcv_15m/1s rows across 2026-07-29 through 2026-08-05 — the fix does not appear
  to have stopped the accrual. (2) A "self-sufficient to completion" FRED backfill claim doesn't match live prod state:
  only 99 captured dates exist (2024-01-01 through 2026-08-05), zero dates in the 1962-1970 floor range appear in any
  bucket, and no FRED-labeled VM is currently in the launcher fleet — the backfill isn't running and isn't close to its
  own stated completion bar.
status: open
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [tradfi, fred, macro, backfill, forward-capture, honest-coverage, prod-contradiction]
related:
  [
    /plans/archive/2026_08/issues/macro_micro_econ_data_capture_audit_2026_06_05.md,
    /plans/archive/issues/fred_backfill_early_date_indefinite_stall_2026_07_30.md,
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
  ]
created: 2026-08-13
author:
  main-agent (blocked-question BLK-f8e14d80, originally routed by a macro-audit worker 2026-08-07, slot 13, agt-c6e8c7)
source:
  "Macro/micro econ data capture audit re-check, grace-window flag-only pass, 2026-08-07 (slot 13, agt-c6e8c7). Not
  auto-fixed at the time -- routed for a decision on where to route both findings; approved 2026-08-13 to file as one
  tradfi-owned issue with the prod evidence already gathered."
assigned_vm: NA
execution_scope: local-only
assigned_role: data_engineering
priority: P2
estimate_class: research
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.6
drift_direction: advance-code
parent_epic: mtds_mdps_master
depends_on: []
resolved_by:
locked_by:
last_updated: 2026-08-20
context_scope:
  [
    /plans/archive/2026_08/issues/macro_micro_econ_data_capture_audit_2026_06_05.md,
    /plans/archive/issues/fred_backfill_early_date_indefinite_stall_2026_07_30.md,
    /codex/02-data/tradfi-databento-sourcing-ssot.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
  ]
---

# Two live-prod FRED contradictions

## What this is

Filed from a macro-audit grace-window re-check (2026-08-07) that flagged, but did not investigate or fix, two
contradictions between what's documented as shipped/complete and what prod actually shows. Both need real investigation
— this doc records the flag so the finding isn't lost, not a completed root-cause.

**Note going in**: `fred_backfill_early_date_indefinite_stall_2026_07_30.md` (archived, resolved) previously
investigated a DIFFERENT FRED symptom — a suspected indefinite hang that turned out to be a legitimate bounded wait for
a manifest-consolidator lock, not a code defect. That finding does not cover or resolve either contradiction below (it's
about apparent stalling on the first chunk, not about attempted_failed accrual or backfill completeness); cited here
only as prior, related FRED-backfill context.

## Finding 1 — forward-capture still accrues attempted_failed after its capability-filter fix

A FRED capability-filter fix has shipped, but prod continued to accrue `attempted_failed` `ohlcv_15m`/`ohlcv_1s` rows
across 2026-07-29 through 2026-08-05 (per the flagging audit's own live read). Either the fix doesn't cover the full
failure surface, or something else is generating these rows independent of the capability filter.

## Finding 2 — the "self-sufficient to completion" backfill claim doesn't match prod

**Source identified 2026-08-18 (plan_reconciler)**: `plans/archive/2026_08/issues/macro_micro_econ_data_capture_audit_2026_06_05.md:515` is the doc making the "self-sufficient to completion" claim (already in this doc's own `related:` list, but never explicitly connected to this finding). It doesn't match live state as of the
2026-08-07 audit: only 99 captured dates exist (2024-01-01 through 2026-08-05 — a ~2.5 year window, not the full
historical range), zero dates in the 1962-1970 floor range appear in any bucket, and no FRED-labeled VM was found in the
launcher fleet. A backfill that isn't running and hasn't reached anywhere near its floor date is not "self-sufficient to
completion" in any live sense.

## Todos

- [ ] [DATA] P2. **Investigate Finding 1** — confirm what's actually generating the 2026-07-29→08-05 `attempted_failed`
      `ohlcv_15m`/`ohlcv_1s` rows post-capability-filter-fix; either the filter has a gap or a different code path is
      responsible. Fix or file a narrower follow-up once root-caused.
- [ ] [DATA] P2. **Investigate Finding 2** — confirm current FRED backfill state (is a VM meant to be running? was one
      launched and never completed, or never launched at all?), re-verify the 99-date/zero-floor-dates read against
      current prod, and either launch/resume the backfill toward the 1962-1970 floor or correct whatever doc claims
      "self-sufficient to completion" if that claim is simply wrong. Follow
      `/codex/05-infrastructure/vm-launcher-runbook.md` if a VM launch is the right next step.

## Progress Log

- **na-eligibility-audit 2026-08-16** (tradfi tranche, dispatch agt-45ad7b): **KEEP-NA, valid.** Both todos are
  open-ended, unscoped investigations explicitly flagged (not root-caused) by the filing session itself. First audit
  pass, no established ruling to defer to. `assigned_vm` unchanged.
- **context-scout 2026-08-17**: populated/refreshed context_scope (3 entries).
- **na-eligibility-audit 2026-08-18** (tradfi tranche, dispatch agt-31bfcb): **KEEP-NA, valid — reaffirmed.** Both
  todos remain open-ended root-cause investigations. Only intervening change was plan_reconciler's 2026-08-18 fix
  identifying the source of Finding 2's "self-sufficient to completion" claim
  (`macro_micro_econ_data_capture_audit_2026_06_05.md:515`) — a citation improvement, not new work. `assigned_vm`
  unchanged.
- **context-scout 2026-08-20**: populated/refreshed context_scope (4 entries)
