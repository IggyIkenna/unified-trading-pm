---
doc_type: issue
title: TradFi Databento account suspended by vendor for non-payment — all Databento fetches fail account-wide
summary: >-
  Operator report 2026-08-09: Databento has suspended our account because the bill was not paid. This is a FULL
  account-level outage — broader than the existing 3-dataset billing-safety allowlist
  (`/codex/02-data/tradfi-databento-sourcing-ssot.md`), which guards against silent metered charges on an otherwise-live
  subscription. With the account itself suspended, EVERY Databento request (batch backfill AND the live
  `databento_tradfi_ws` connector) will fail regardless of allowlist compliance, until the operator pays the bill and
  the vendor restores the account. Every open TradFi MTDS/backfill todo that depends on a live Databento fetch is
  non-dispatchable until this resolves. Features/ML work on already-captured data is UNAFFECTED and should proceed.
status: blocked
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service, instruments-service, deployment-service, unified-trading-pm]
scope: [engineer, admin]
tags: [tradfi, databento, billing, backfill, mtds, operator-decision, outage]
related:
  [
    /codex/02-data/tradfi-databento-sourcing-ssot.md,
    /plans/active/tradfi_satellite_ao_dispatch_batch8_2026_08_08.md,
    /plans/active/tradfi_satellite_ao_dispatch_batch7_2026_08_06.md,
    /plans/active/tradfi_satellite_ao_dispatch_batch6_2026_08_01.md,
    /plans/active/tradfi_backfill_throughput_followups_2026_07_24.md,
    /plans/active/tradfi_registry_coverage_and_ao_readiness_2026_07_25.md,
    /plans/active/data_completion_tradfi_2026_07_15.md,
  ]
created: 2026-08-09
author: claude-code (interactive session, operator-reported 2026-08-09)
parent_epic: tradfi_master
assigned_vm: NA
execution_scope: local-only
priority: P0
source:
  [
    'Operator chat instruction, 2026-08-09: "tradfi is currently billing blocked because databento have stopped our
    account because we didn''t pay .. every issue and plan involving a databento backfill needs to be put on hold for
    now because it won''t work anyway. anything which is not mtds or is backfill related can proceed including features
    and ml because we do have data for those."',
  ]
resolved_by:
locked_by:
locked_since:
context_scope: [/codex/02-data/tradfi-databento-sourcing-ssot.md]
drift_direction: advance-code
depends_on: []
---

# TradFi Databento account suspended by vendor for non-payment

## What's actually different from the existing billing-safety SSOT

`/codex/02-data/tradfi-databento-sourcing-ssot.md` documents a **fail-closed allowlist** that stops us from being billed
for out-of-subscription `(dataset, schema, start)` cells on an otherwise-live, paid-up subscription. That mechanism is
unrelated to this issue: this is the vendor suspending the **account itself** for non-payment. Every Databento call —
allowlisted or not — will now fail (auth/entitlement rejection at the account level), including:

- The MTDS batch OHLCV/tick backfill launchers (`--source databento`).
- The instruments-service reference-data `definition` schema fetch
  (`instruments_service/reference_data/adapters/tradfi/databento/adapter.py`).
- The live `databento_tradfi_ws` connector (same account, same credential) — **not explicitly called out by the operator
  but almost certainly affected too**; worth a live-side verification pass once someone is checking on this, it is not
  itself the thing being paused here.

## What is paused

Any OPEN (`- [ ]`) todo in a TradFi-tagged active plan/issue that requires a **new fetch from Databento** — MTDS
backfill launches, instruments-service databento-sourced instrument-definition backfills, VM launches whose payload
calls the Databento adapter. These are gated `BLOCKED-OPERATOR-DECISION` (task_template.md's non-dispatchable
ingestion-gate family) pointing at this doc, so the AO backlog stops offering them to workers. Re-check
`unified-api-contracts/registry/databento_subscription_allowlist.py`'s live behavior once the operator confirms the
account is restored, then lift the gates doc-by-doc.

## What is NOT paused (operator explicit)

- **Features / ML** — feature computation and model training/inference read already-captured data; they do not call
  Databento. Proceed normally.
- Any non-TradFi asset_group work (cefi/defi/sports/prediction) — Databento is TradFi-only, unaffected.
- TradFi audit/reconciliation/read-only todos that don't fetch new data (e.g. manifest/catalog audits, canonical-path
  reconciliation, docs work) — these read what's already captured, not blocked.
- TradFi ML/strategy/backtest work that consumes already-captured TradFi data.

## Resolution path

Operator pays the outstanding Databento bill and the vendor restores account access. Until then this is a
`BLOCKED-OPERATOR-DECISION` (finding U(i) class — a business/spend judgment with no data-derivable answer). Once
restored: live-verify with a cheap real call (e.g. `definition` schema fetch for a known instrument) before resuming any
bulk backfill, then flip each gated todo's marker back to dispatchable in the same edit that confirms it works (per the
"retag the moment the block resolves" hard rule).

## Todos

- [ ] [OPERATOR] P0. **Pay the outstanding Databento bill so the vendor restores account access.** Gates every open
      TradFi Databento-fetch todo across the corpus (see "Plans/issues gated by this doc" below for the current
      7-todo/4-doc sweep — re-sweep once paid, since the gate list drifts as new work lands). Not tracked as a
      checkbox anywhere else in the corpus (verified via grep) despite being escalated in prose in at least
      `tradfi_satellite_ao_dispatch_batch11_2026_08_10.md`'s "Deferred — operator-gated" section ("has sat blocked
      since 2026-08-09 and gates multiple other orphaned docs' items"). Once paid: live-verify with a cheap real call
      before resuming any bulk backfill, then flip each gated todo's marker back to dispatchable in the same edit that
      confirms it works.

## Plans/issues gated by this doc (sweep log)

**Method**: swept every active plan/issue whose `asset_group` frontmatter includes `tradfi` (61 docs), narrowed to the
15 carrying an open (`- [ ]`) todo matching backfill/databento/mtds/ohlcv/launch/download/capture/fetch, then read each
match's surrounding context to judge whether it's a genuine new-Databento-fetch dependency vs. a manifest repair,
audit/read-only task, features/ML computation, or a non-Databento source (e.g. ForexFactory econ calendar, Yahoo VIX,
Massive-historical). 7 todos across 4 docs are genuine and now gated `BLOCKED-OPERATOR-DECISION`:

- `/plans/active/data_completion_tradfi_2026_07_15.md` — the `build_instrument_catalogue.py` scheduler todo (gated on
  Databento IS reference-capture restore) and the IS instrument-capture `--source databento` replacement-path todo.
- `/plans/active/instruments_tradfi_g1_g5_gate_execution_2026_07_24.md` — "Launch the ES_OPT backfill" and its dependent
  post-launch manifest-verify todo.
- `/plans/active/tradfi_phase_d_terminal_gate_2026_07_24.md` — the "MVP backfill readiness gate" (tradfi MVP backfills,
  SPOT VMs, single Databento IP) and its dependent post-backfill reconciliation-run checkpoint.
- `/plans/active/tradfi_satellite_ao_dispatch_batch6_2026_08_01.md` — the combined ES_OPT launch + manifest-verify todo
  (same task as the instruments_tradfi_g1_g5 pair above, tracked here too since batch6 is the live AO-dispatch surface;
  its own Progress Log recorded a watcher session actively polling the singleton lock and launching as of
  2026-08-07T~04:46Z — if that watcher is still running, it will now fail every attempt until billing is restored).
  **RETAGGED 2026-08-09 (was stale — flagged by two separate sessions as needing this fix, now applied): this specific
  gate is LIFTED.** `/plans/active/issues/tradfi_mvp_of_mvp_instrument_scope_ruling_2026_08_09.md` (same day, same
  author) recorded a live Databento API verification (`metadata.list_datasets` + a real `ES.FUT ohlcv-1m` pull, both
  succeeded) that lifted this gate specifically for its in-scope list — which includes S&P 500 futures+options. Live
  evidence since: 2 real `tradfi-bf-es-opt-*` launches on 2026-08-09 both fetched genuine Databento data (confirmed via
  manifest — 1,407/1,728 distinct trading dates already carry real OHLCV bars, see
  `tradfi_year_shard_backfill_launcher_missing_source_self_deletes_2026_08_09.md`). The account-level suspension this
  doc as a whole describes may still be real for OUT-of-scope Databento calls; this retag narrowly resolves only the
  batch6/ES_OPT entry per the scope-ruling doc's own explicit carve-out — not a claim that the broader billing issue is
  resolved.

**Explicitly left ungated** (read, judged not a live-fetch dependency):
`tradfi_backfill_throughput_followups_2026_07_24.md` (OOM-remediation umbrella pointer — its one real open leg is a
log-audit, not a fetch), `tradfi_forexfactory_econ_calendar_consensus_capture_2026_07_30.md` (ForexFactory, not
Databento), `tradfi_within_bounds_source_zero_shard_atom_mismatch_2026_07_28.md` (re-measure ratio on already-captured
data), `tradfi_volatility_no_perp_fx_underlyings_code_gap_2026_08_06.md` (features-VM relaunch, reads existing data),
`tradfi_es_cme_ohlcv_zero_capture_2026_07_30.md` (manifest-row repair script), `estate_orphan_assessment_2026_07_21.md`
(manifest reclassification script, cross-cutting not tradfi-specific), `data_completion_tradfi_2026_07_15.md`'s
ohlcv_15m/24h conversion todo (MDPS aggregation of already-captured 1s/1m data),
`honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md` (manifest reclassification, CEFI/TradFi),
`tradfi_registry_coverage_and_ao_readiness_2026_07_25.md`'s two open todos (an audit-pointer and a manifest-only
re-stamp/backfill of already-captured rows), `mdps_features_deadcode_consolidation_2026_07_20.md` (prediction/sports/
generic launcher bugs, none tradfi-specific), and `tradfi_satellite_ao_dispatch_batch7_2026_08_06.md` /
`..._batch8_2026_08_08.md` / the `_finalize` plans (all open todos there are manifest reconciliation, investigation, or
archival — no live Databento dependency).

## Progress Log

- **2026-08-10 (prose-findings formalization sweep)**: converted 1 prose finding into 1 formal todo (0 already
  resolved). The doc's own "Resolution path" prose ("Operator pays the outstanding Databento bill...") had never been
  formalized as a `- [ ]` checkbox despite `status: blocked`/`priority: P0` and being escalated in prose elsewhere
  (`tradfi_satellite_ao_dispatch_batch11_2026_08_10.md`'s Deferred section) — added an `[OPERATOR] P0` todo under a new
  `## Todos` section.
