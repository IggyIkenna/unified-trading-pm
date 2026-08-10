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
status: open
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
resolved_by: >-
  2026-08-10 — operator confirmed the Databento billing suspension is paid/resolved and asked to unblock every TradFi
  Databento backfill todo citing it. Independently live-reverified that day (3 real Databento API calls across all 3
  core datasets — GLBX.MDP3 ES.FUT ohlcv-1d, DBEQ.BASIC/XNAS.ITCH, XCBF.PITCH VX.FUT ohlcv-1d — all succeeded with real
  data). Source plan: /plans/active/tradfi_databento_billing_unblock_vix_yahoo_floor_2026_08_10.md
locked_by:
locked_since:
context_scope: [/codex/02-data/tradfi-databento-sourcing-ssot.md]
drift_direction: advance-code
depends_on: []
---

# TradFi Databento account suspended by vendor for non-payment

## LIVE RE-VERIFIED 2026-08-10 — account is live, do NOT re-verify from scratch

**RESOLVED.** Operator confirmed the Databento billing suspension is paid/resolved (2026-08-10) and asked to unblock
every TradFi Databento backfill todo that cited it. Independently live-reverified the same day (not just the report)
with 3 real, dated calls against the live Databento API:

1. `metadata.list_datasets()` — succeeded, 29 datasets visible (an account-level suspension would reject this outright).
2. Real metered pull, `GLBX.MDP3` (CME) `ES.FUT ohlcv-1d`, `2026-08-05→2026-08-06` — succeeded, 5 real rows (ESZ6, ESU6,
   real volumes e.g. 1,401,190).
3. Real metered pull, `XCBF.PITCH` (CBOE/CFE) `VX.FUT ohlcv-1d`, same date range — succeeded, 57 real rows (VX/G7,
   VX/X6, VX/Z6, genuine VIX-futures prices).

All 3 core subscribed datasets (`GLBX.MDP3`, `DBEQ.BASIC`/`XNAS.ITCH`, `XCBF.PITCH`) confirmed live with real data as of
2026-08-10. Does NOT resolve the separate ICE/OPRA subscription question
(`/plans/active/issues/databento_ice_opra_subscription_ask_2026_08_09.md`) — dataset visibility in
`metadata.list_datasets()` is not proof of subscription; leave that doc untouched. Full reproduction + evidence:
`/plans/active/tradfi_databento_billing_unblock_vix_yahoo_floor_2026_08_10.md` ("Confirmed finding" section).

- [ ] [DOCS] P2. **Retag the 4 downstream docs' billing-gate references now that the suspension is resolved** — still
      needing their update per `tradfi_databento_billing_unblock_vix_yahoo_floor_2026_08_10.md` todos 2–5 (this doc
      stays `status: open` and non-archivable until these land): 1. `/plans/active/data_completion_tradfi_2026_07_15.md`
      — un-gate the 2 `BLOCKED-OPERATOR-DECISION (databento        account billing-suspended 2026-08-09` todos (marker
      `UNGATED 2026-08-10`). 2. `/plans/active/tradfi_phase_d_terminal_gate_2026_07_24.md` — un-gate the 2
      billing-blocked todos (marker `BILLING GATE LIFTED 2026-08-10`; PRESERVE the separate Phase-D-completeness caveat
      / chain-sampler root-mismatch blocker). 3. `/plans/active/tradfi_registry_coverage_and_ao_readiness_2026_07_25.md`
      — add the `DATABENTO ACCESS CONFIRMED LIVE 2026-08-10` note to the re-feed-chain todo. 4.
      `/plans/active/issues/tradfi_mvp_of_mvp_instrument_scope_ruling_2026_08_09.md` — add VIX futures (CBOE, VX.FUT) to
      the MVP-of-MVP in-scope list (operator decision 2026-08-10).

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

**RESOLVED 2026-08-10.** The operator paid the outstanding Databento bill and the vendor restored account access;
independently live-reverified that day (3 real API calls across all 3 core datasets — `GLBX.MDP3`, `DBEQ.BASIC`/
`XNAS.ITCH`, `XCBF.PITCH` — all succeeded with real data; see the `## LIVE RE-VERIFIED 2026-08-10` section above and
`/plans/active/tradfi_databento_billing_unblock_vix_yahoo_floor_2026_08_10.md`). The `BLOCKED-OPERATOR-DECISION` gate is
lifted; each gated todo's marker is being flipped back to dispatchable in the same edit that confirms it works (per the
"retag the moment the block resolves" hard rule) — tracked by the `[DOCS] P2` todo in the section above. The live-side
`databento_tradfi_ws` connector should also work again; worth a live-side verification pass when convenient.

## Todos

- [x] [OPERATOR] P0. **Pay the outstanding Databento bill so the vendor restores account access.** — ✅ DONE 2026-08-10:
      operator paid; account live-reverified that day (3 real Databento calls across all 3 core datasets — see the
      `## LIVE RE-VERIFIED 2026-08-10` section above). Gates every open TradFi Databento-fetch todo across the corpus
      (see "Plans/issues gated by this doc" below for the current 7-todo/4-doc sweep — the re-sweep once paid is now
      tracked by the `[DOCS] P2` todo above, since the gate list drifts as new work lands). Not tracked as a checkbox
      anywhere else in the corpus (verified via grep) despite being escalated in prose in at least
      `tradfi_satellite_ao_dispatch_batch11_2026_08_10.md`'s "Deferred — operator-gated" section ("has sat blocked since
      2026-08-09 and gates multiple other orphaned docs' items"). Once paid: live-verify with a cheap real call before
      resuming any bulk backfill, then flip each gated todo's marker back to dispatchable in the same edit that confirms
      it works.

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
- **na-eligibility-audit 2026-08-10 (formalized-docs follow-up)**: KEEP-NA, valid — the sole open todo is paying an
  outstanding vendor bill, an explicit `[OPERATOR]`-tagged business/spend decision with no data-derivable answer
  (`status: blocked`, `BLOCKED-OPERATOR-DECISION` per the doc's own text). Doc stays NA.
