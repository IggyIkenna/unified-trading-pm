---
doc_type: plan
title: TradFi satellite AO-dispatch batch 18 — ETF-drift row re-measure + DXY duplicate-artifact manifest purge
summary: >-
  Fresh carve-out of 2 bounded, conflict-checked-clean todos extracted by na-eligibility-audit's 2026-08-19 tradfi
  tranche pass: a read-only re-measurement of the deprecated-ETF manifest row re-accumulation count, and a
  named-cell, reversibility-verified manifest purge/reclassify of duplicate-VM-race attempted_failed rows for 3
  Yahoo-daily cells. Both items' source docs stay assigned_vm:NA for their remaining genuinely open/gated todos.
status: active
nature: process
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service, instruments-service]
scope: [engineer]
tags: [tradfi, ao-dispatch, satellite-batch, na-eligibility-audit, manifest-hygiene]
related:
  [
    /plans/active/issues/tradfi_deprecated_etf_manifest_rows_forward_scope_drift_2026_08_18.md,
    /plans/active/tradfi_satellite_ao_dispatch_batch13_2026_08_13.md,
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
  ]
created: 2026-08-19
last_updated: 2026-08-20
parent_epic: tradfi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.32
assigned_role: data_engineering
effort: medium
drift_direction: advance-code
depends_on: []
context_scope:
  [
    /plans/active/issues/tradfi_deprecated_etf_manifest_rows_forward_scope_drift_2026_08_18.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /plans/archive/issues/dxy_duplicate_vm_billing_waste_ao_outage_2026_08_12.md,
  ]
supersedes:
superseded_by:
locked_by:
locked_since:
source: >-
  na-eligibility-audit, tradfi tranche, dispatch agt-5d34f9, 2026-08-19 — RECLASSIFY (per-todo split) extraction
  from 2 assigned_vm:NA issue docs (one since archived — see todo 2's Source citation), both conflict-cleared per
  /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md § 3.
---

# TradFi satellite AO-dispatch batch 18

> Two independent, unrelated-file todos. No ordering constraint between them — dispatch concurrently.

## Todos

- [ ] [DATA] P3. **Re-measure the current deprecated-ETF manifest row count** in `market-data-tick-tradfi`'s
      availability index for the exact pattern tracked in
      `tradfi_deprecated_etf_manifest_rows_forward_scope_drift_2026_08_18.md`: tickers
      `ETHE`/`GBTC`/`BITO`/`FBTC`/`ARKB`/`FETH` at venues `NYSE`/`NYSE_ARCA`/`BATS`/`CBOE_BZX`. Compare the fresh
      count against the 2026-08-18 baseline of 5,932 rows. Read-only query, no write. Repo: market-tick-data-service.
      Done when: the fresh count is posted back to the source doc's Progress Log (with the query used), and the
      source doc's todo 2 checkbox is confirmed still correctly showing this extraction.
      Source: `plans/active/issues/tradfi_deprecated_etf_manifest_rows_forward_scope_drift_2026_08_18.md` todo 2.
- [ ] [DATA] P2. **Purge/reclassify stale `attempted_failed` rows** in `market-data-tick-tradfi`'s
      `availability_index` for `(venue, data_type)` ∈ {(ICE, ohlcv_24h), (CBOE, ohlcv_24h), (FX, ohlcv_24h)} where a
      `captured` row ALREADY exists for the same date (duplicate-VM-race artifacts). Measured overlap: CBOE 100%
      (1521/1521), FX 99.3% (1369/1379), ICE 97.6% (1494/1531) of `attempted_failed` dates already have a captured
      counterpart for the same date. The small residual with NO captured counterpart (FX: 10 dates, ICE: 37 dates)
      are calendar weekends/holidays — reclassify those to `empty_confirmed`, not purge as duplicates. Mirror the
      Surface A-D / `WithinBoundsTradfiSourceZero` dry-run→review→`--apply` playbook (measure first, confirm the
      "duplicate artifact" theory with a live count, snapshot backup before any CAS write). Soft-delete retention on
      `market-data-tick-tradfi-prd-central-element-323112` already confirmed 604800s (7 days) — reversibility gate
      passes per `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §3a finding T, no `[OPERATOR]` tag
      needed. Repo: market-tick-data-service. Done when: dry-run counts cited per cell, `--apply` completes with
      before/after evidence, self-verify shows 0 remaining same-date captured+attempted_failed duplicate pairs for
      the 3 cells.
      Source: `plans/archive/issues/dxy_duplicate_vm_billing_waste_ao_outage_2026_08_12.md` (archived same pass —
      this was its sole remaining open todo before the na-eligibility-audit extraction below closed the doc out).

## Progress Log

- **2026-08-19 (na-eligibility-audit, tradfi tranche, dispatch agt-5d34f9)**: authored. Both items conflict-checked
  clear per the shared protocol — see each source doc's own Progress Log entry for the specific conflict-check
  evidence (batch13 explicitly deferred the DXY purge here rather than claiming it; corpus-wide grep found no other
  doc tracking the ETF re-measure). Todo 2's source doc (`dxy_duplicate_vm_billing_waste_ao_outage_2026_08_12.md`)
  reached 0 open todos as a direct result of this same pass's fixes and was archived to
  `plans/archive/issues/` in the same commit — its own Progress Log carries the full incident history.
- **context-scout 2026-08-20**: populated/refreshed context_scope (4 entries)
