---
doc_type: plan
title: TradFi satellite AO batch 8 — fresh /ag-closeout-audit extraction (3 clean orphans)
summary: >-
  Eighth AO-dispatch batch for tradfi, produced by a fresh `/ag-closeout-audit tradfi` pass on 2026-08-08 (autonomous
  mode, scheduled `ag_closeout_auditor` worker, sharded-tranche dispatch). Phase 0 rediscovered the covering set as 11
  docs (`generate_ag_closeout_audit_candidates.py`) and enumerated 40 real tradfi candidates (down from batch7's 54 —
  batch6/7's own dispatched work shrank the corpus). Phase 1 ran a 40-agent Workflow classifying every candidate: 0
  archivable now, 6 archivable-after-planned-work (already claimed by batch6/7's own open todos or self-dispatched), 4
  orphaned-partial-coverage, 13 orphaned-never-touched (9 raw + 4 recovered by a verification pass — see below), and 17
  excluded as genuinely cross-cutting. **A methodology correction this pass made**: the first Phase-1 pass returned 21
  exclude_cross_cutting verdicts, a sharp jump from batch7's 1 — a spot-check found 2 of the 21 had real, still-open
  tradfi-specific content (a doc's own agent had correctly READ it but wrongly excluded the whole doc rather than
  reporting a real orphan verdict + flagging cross-tranche ownership, per the skill's own primary-owner-rule text). A
  full re-verification pass across all 21 confirmed 17 as genuinely exclude-worthy (tradfi's own angle already resolved,
  or zero tradfi-specific content ever existed) and reclassified 4 to `orphaned_never_touched` — all 4 turn out to match
  batch7's own "Flagged, not batched — cross-tranche ownership" list from 2 days ago exactly, which is strong
  independent corroboration for both this pass's correction and batch7's original judgment. Net: **17 orphaned docs this
  pass** (down from batch7's 36), of which 3 cleared the Phase-3 conflict-check as bounded, conflict-free, AO-eligible
  work and are drafted below (from 3 distinct source docs). The other 14 stay deferred/flagged — see below.
status: active
nature: process
asset_group: [tradfi]
stage: [data]
repos: [instruments-service, unified-api-contracts, market-data-processing-service, features-service]
scope: [engineer]
tags: [tradfi, ao-dispatch, close-out, batch-8, satellite-docs, conflict-checked]
related:
  [
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /plans/active/tradfi_satellite_ao_dispatch_batch6_2026_08_01.md,
    /plans/active/tradfi_satellite_ao_dispatch_batch6_2026_08_01_finalize.md,
    /plans/active/tradfi_satellite_ao_dispatch_batch7_2026_08_06.md,
    /plans/active/tradfi_satellite_ao_dispatch_batch7_2026_08_06_finalize.md,
    /plans/active/canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08.md,
    /plans/active/issues/mdps_tradfi_ohlcv_15m_24h_conversion_still_zero_2026_07_27.md,
    /plans/active/issues/features_require_captured_misses_tradfi_processed_candles_gap_2026_07_27.md,
    /plans/active/issues/tradfi_volatility_no_perp_fx_underlyings_code_gap_2026_08_06.md,
    /plans/active/issues/governance_sweep_deferred_followups_2026_08_06.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-08-08"
last_updated: "2026-08-08"
parent_epic: tradfi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  /ag-closeout-audit tradfi run 2026-08-08 (autonomous / AO-dispatched mode, sharded daily `ag_closeout_auditor` worker,
  dispatch agt-ea6423, slot 6, operator away). Phase 0 used `generate_ag_closeout_audit_candidates.py` for the
  covering-plan + candidate-member discovery. Phase 1 classified all 40 real tradfi-primary candidates via a `Workflow`
  (40 agents, 0 errors, 409 tool calls, ~19.9 min wall-clock), followed by a dedicated verification pass
  (general-purpose agent, 25 tool calls) re-deriving all 21 initial exclude_cross_cutting verdicts against the
  primary-owner rule (4 reclassified — see summary). Phase 3 conflict-checked all 3 drafted todos below against the full
  corpus (not just the 11-doc covering set) via direct grep before drafting; the one item that failed the conflict-check
  (`tradfi_volatility_no_perp_fx_underlyings_code_gap_2026_08_06.md`'s todo 1) is deferred, not drafted — see Deferred —
  conflict-gated below.
assigned_role: data_engineering
effort: max
sequential: false
drift_direction: advance-code
context_scope:
  [
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    instruments-service/scripts/canonicalize_cboe_vx_combo_catalog_2026_07_08.py,
    unified-api-contracts/unified_api_contracts/internal/schemas/_candle_contracts.py,
    market-data-processing-service/market_data_processing_service/app/adapters/tradfi/ohlcv_passthrough.py,
    features-service/features_service/delta_one/app/core/dependency_checker.py,
  ]
---

# TradFi satellite AO batch 8 — fresh audit extraction

> **Status: active — operator-approved 2026-08-08.** A fresh conflict-check re-verified the original Phase 3 clearance
> still held before dispatch (see Progress Log). Per the ag-closeout-audit skill's autonomous-mode contract, a
> freshly-drafted batch always ships `status: draft` regardless of how clean the conflict-check came back; flipping to
> `active` is an operator decision, never autonomous — that decision has now been made.
>
> All 3 todos below are same-priority-independent and were checked for file collisions (see the matrix near the bottom)
> — all 3 touch distinct repos/files, no overlap.

## Why this batch exists

This is the first fresh `/ag-closeout-audit tradfi` pass since batch7 (2026-08-06), run as a full independent Phase 0-3
pass (not a delta) per this dispatch's autonomous-mode instructions.

1. **1 item is now ready that wasn't drafted before**:
   `canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08.md`'s residual catalog re-canonicalization was tagged
   `[OPERATOR]` and undecided as of batch1-7; the operator RULED 2026-08-06 ("go-ahead to run --apply"), independently
   reconfirmed 2026-08-07 after a same-day staleness contradiction was raised and resolved
   (`governance_sweep_deferred_followups_2026_08_06.md` item 1/6, closed). No covering plan owns a todo to actually run
   it — the consolidated-closeout's own citation is a stale digest listing (misstates "0 open todos") predating the
   ruling.
2. **2 new findings surfaced since batch7**, both from docs whose Progress Log gained a dated entry after batch7's
   2026-08-06 cutoff:
   - `mdps_tradfi_ohlcv_15m_24h_conversion_still_zero_2026_07_27.md`'s P3 ETF/OPTION zero-SchemaContract-coverage
     finding (from the 2026-08-03 re-run) is unblocked now that the doc's other 2026-08-03/06 findings (the `ohlcv_24h`
     alias, the COMBO scoping `[OPERATOR]` call) have both shipped — confirmed via the doc's own 2026-08-06
     context-scout note that this P3 is the sole remaining open item.
   - `features_require_captured_misses_tradfi_processed_candles_gap_2026_07_27.md`'s Follow-ups section carries a small,
     never-tracked P3 (a malformed `"ticks"` instrument_id surfacing in the delta_one pre-flight scanner), explicitly
     flagged in prose by a 2026-08-06 archive-candidate audit as "worth tracking" but never promoted to its own todo.
3. **1 candidate ruled back OUT by the conflict-check**:
   `tradfi_volatility_no_perp_fx_underlyings_code_gap_2026_08_06.md` was a `never_cited` candidate (created 2026-08-06,
   after batch7 ran) with 2 open P1 todos, but a corpus-wide grep (beyond the 11-doc covering set, per the skill's Phase
   3 mandate) found todo 1's CME `instrument_id`-verification sub-task is a near-verbatim duplicate of an open
   `[DIAG] P2` todo already tracked in `governance_sweep_deferred_followups_2026_08_06.md` (asset_group: cross-cutting —
   not part of tradfi's covering set, so tradfi's own Phase 1 pass had no way to see it without this explicit
   corpus-wide check). That doc's own text names this exact collision and states its own resolution mechanism is still
   pending. Drafting a competing todo here would risk two workers independently verifying the same instrument_id format.
   Deferred, not drafted — see Deferred — conflict-gated below.

## Todos

- [x] ✅ [DATA] P2. **Re-apply the TradFi combo/stock-class catalog canonicalization scripts against the residual rows
      reintroduced by the self-refreshing catalogue roll-up.** Operator-approved 2026-08-06 (reconfirmed 2026-08-07).
      **DONE 2026-08-09 (slot-9, data_engineering).** Re-ran both scripts against the live `prod/catalog.parquet`
      (919,493 total rows — the plan's cited 1,096,472 figure was stale; treat the count each script logs at run time as
      authoritative, per both scripts' own docstrings). Fresh dry-run found the residual population had shifted since
      drafting: CBOE `SPOT_PAIR`→`COMBO` residual was **0** (natural rolloff — VX calendar spreads are short-dated and
      the original 91-row residual had already expired out of the catalogue by run time), DBEQ
      `SPOT_PAIR`→`EQUITY`/`ETF` residual was **318** (317→EQUITY, 1→ETF for IBIT via `KNOWN_ETFS`). `--apply` completed
      for both (GATE passed: total rows unchanged 919,493→919,493, no unexpected (venue,instrument_type) drift).
      Post-apply dry-run confirms **0 residual non-canonical rows** for both scripts' scope (CBOE: 0 candidates; DBEQ: 0
      candidates, `KNOWN_ETFS: []`). No code changed — this is a data-only GCS rewrite
      (`instruments-store-tradfi-prd-central-element-323112/prod/catalog.parquet`), snapshots pre-existed from the
      2026-07-08 original run and were kept. **Not durable** — per the source doc, this needs re-running after every
      `build_instrument_catalogue.py` rollup cycle until the upstream `by_date` corpus migration lands
      (`tradfi_canonical_path_migration_design_2026_07_19.md`); do not treat this clean re-run as closing the item
      permanently. `canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08.md`'s checkbox flipped citing this
      evidence (same commit). Source: `canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08.md`.

- [ ] [DATA] P3. **Register TradFi ETF SchemaContract coverage and fix TradFi OPTION's caller-scoping crash — one
      combined todo (same underlying finding, same source doc, sequential sub-steps).** (1) `instrument_type=ETF` has
      ZERO SchemaContract coverage at any timeframe in `unified_api_contracts/internal/schemas/_candle_contracts.py`
      despite `VALID_DATA_TYPES_BY_AG_AND_INSTRUMENT_TYPE[("tradfi","etf")]` explicitly listing
      `ohlcv_1m`/`ohlcv_15m`/`ohlcv_24h`/`trades`/`tbbo`/`mbp_10` as valid (MVP TradFi scope: BlackRock spot ETFs
      IBIT/ETHA on NASDAQ) — confirm the correct per-instrument schema shape (same shape as `future`/`equity`, or a
      dedicated one) by comparing to how those adjacent instrument_types are already registered, then register ETF
      accordingly. (2) `instrument_type=OPTION` (the leaf grain, distinct from the already-working `options_chain`
      per-underlying bundle) is `frozenset()` in the same registry and crashes — this is NOT a registration gap, it is
      very likely the same caller-scoping class of bug already fixed for COMBO/futures_chain
      (`market-data-processing-service@0671953`'s `related_data_types` mechanism) — confirm via the same investigation
      pattern against `market-data-processing-service/.../app/adapters/tradfi/ohlcv_passthrough.py` and fix if
      confirmed. Repos: unified-api-contracts (ETF registration), market-data-processing-service (OPTION
      caller-scoping). **Done when**: ETF has registered SchemaContract coverage for its full valid data_type list with
      a passing regression test, the OPTION caller-scoping root cause is confirmed and fixed (or, if the investigation
      finds it's NOT the same bug class, that finding is recorded with a follow-up scoped), a live re-run shows candles
      for both instrument_types, and `quality-gates.sh` is green. Source:
      `mdps_tradfi_ohlcv_15m_24h_conversion_still_zero_2026_07_27.md`.

- [ ] [DATA] P3. **Investigate the pre-existing malformed `"ticks"` instrument_id surfaced by the delta_one pre-flight
      instrument scanner during TRADFI processing.** The 2026-08-05 TRADFI delta_one re-run's pre-flight scanner picked
      up a literal data_type name (`"ticks"`) where a real instrument_id was expected — flagged in the source doc's
      Progress Log as "a separate, pre-existing bug... not blocking [the force+skip] proof but worth tracking as a
      low-priority issue," never promoted to its own tracked item. Trace where this malformed id enters the scanner's
      input (likely a bundle/shard-path parsing artifact, similar in shape to other TradFi bundle-filename leak defects
      already fixed elsewhere in the corpus) and fix it, or if root-causing needs more than this todo's bounded scope,
      record the specific mechanism found so a follow-up can be scoped precisely. Repo: features-service. **Done when**:
      the malformed-id's origin is identified and documented with file:line evidence, either fixed with a regression
      test or (if out of bounded scope) handed off as a precisely-scoped follow-up item, and the source doc's Follow-ups
      checkbox is flipped citing the outcome. Source:
      `features_require_captured_misses_tradfi_processed_candles_gap_2026_07_27.md`.

## Deferred — too-large-or-risky (needs its own dedicated plan, not a batch todo)

- **`data_completion_tradfi_2026_07_15.md`** — unchanged from batch1-7. Phase 0 layout audit, ~133K-cell NASDAQ/NYSE
  backfill, G1 `--apply-write` denominator-seed execution (gate-b still frozen), and the catalogue-scheduler terraform
  wiring stay too large/interdependent for a batch todo.
- **`issues/tradfi_canonical_path_migration_design_2026_07_19.md`** — unchanged from batch1-7. Steps 5-6 are explicit
  `[GATE]` operator-go items over a 2.73M-object corpus; the whole sequencing stays deferred as one unit.
- **`instruments_tradfi_g1_g5_gate_execution_2026_07_24.md`'s full CME instrument-definitions re-fetch** (~2,368 days) —
  unchanged from batch6/7, still a real backfill campaign needing its own dedicated plan/VM launch. (Its other items —
  ES_OPT launch, anomalous-Sundays investigation — remain drafted in batch6, still pending operator approval; not
  re-drafted here.)
- **`tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md`** — re-confirmed still `orphaned_never_touched`,
  unchanged from batch7's re-confirmation. The underlying MDPS `continuous_future` data gap (79.2% `empty_confirmed`)
  has not closed since batch7 checked it 2 days ago. All 7 remaining items stay deferred until the underlying data gap
  itself is addressed as its own project.

## Deferred — operator-gated (a ruling unblocks these; unchanged, NOT re-asked if already asked)

Unchanged from batch6/7 (not re-asked): `issues/tradfi_chain_bundle_sampler_root_mismatch_2026_07_23.md` (which
`EXCHANGE_CODE_TO_NAME` registry is authoritative); `issues/tradfi_autonomous_session_operator_decisions_2026_07_25.md`
(the doc's remaining entries, unresolved since prior batches);
`issues/tradfi_within_bounds_source_zero_shard_atom_mismatch_2026_07_28.md`'s todo 1 (P0) + dependent todo 4 — a
destructive `--apply` migration/purge over ~81K CME+CBOE `WithinBoundsTradfiSourceZero` manifest rows, explicitly gated
on operator go-ahead per the delete-safety protocol. (Todo 3 of this same doc remains drafted, still-draft, in batch6 —
not re-drafted here.)

## Deferred — conflict-gated (re-triageable once the competing claim resolves)

- **`tradfi_volatility_no_perp_fx_underlyings_code_gap_2026_08_06.md`'s todo 1** (make `_resolve_spot_perp`
  asset-group-aware for TRADFI FX underlyings) — its CME `instrument_id`-format verification sub-task near-verbatim
  duplicates the open `[DIAG] P2` todo in `governance_sweep_deferred_followups_2026_08_06.md` (asset_group:
  cross-cutting, outside tradfi's covering set — found only via an explicit full-corpus grep, not the 11-doc covering
  set check). That doc's own text documents this exact collision as one of 6 items pending its own resolution ("Done
  when: each of the 6 is either reclassified... or explicitly re-affirmed KEEP-NA with the conflict cited"). Re-check
  next batch: once that doc's own reconciliation lands (either todo ships, or the duplicate sub-task is formally dropped
  from one side), todo 1's remaining actual-code-change part (and dependent todo 2, "implement the fix and relaunch the
  benchmark") become clean batch9 candidates.

## Deferred — already in flight (partially covered, not batch8 material)

- **`tradfi_legacy_twin_bucket_deletes_signoff_2026_07_24.md`** — the root-cause investigation (why the dry-run measures
  0% canonical-twin coverage) is already an open todo in `tradfi_satellite_ao_dispatch_batch7_2026_08_06.md` (todo 3,
  still `- [ ]`). The delete itself stays gated on that investigation's outcome — nothing new to draft until batch7's
  todo 3 lands.

## Deferred — already drafted elsewhere, pending that plan's promotion (not re-drafted here)

- **`tradfi_forexfactory_econ_calendar_consensus_capture_2026_07_30.md`** — unchanged from batch7. A complete, already
  well-scoped standalone draft PLAN (7 todos), needs operator review/promotion (`status: draft` → `active`), not folding
  into a batch todo.

## Deferred — time-gated (blocked on upstream, not batchable)

- **`features_require_captured_misses_tradfi_processed_candles_gap_2026_07_27.md`'s item 2** (genuine delta_one:TRADFI
  force+skip proof) — gated on TRADFI MDPS actually producing captured `processed_candles` rows in the pipeline_e2e scan
  window, an upstream data-availability blocker no batch todo can force. (Item 1 of this same doc is drafted above.)

## Flagged, not batched — cross-tranche ownership

Carried forward from batch6/7 (re-verified still open, still not tradfi's to draft, per the primary-owner rule —
`parent_epic` doesn't resolve to tradfi for any of these):

- **`issues/mtds_is_full_adapter_smoketest_findings_2026_07_07.md`** — 4 TradFi-specific bugs (CME BAG mistyping,
  ICE/CBOE routing, stale catalogue, Yahoo `instrument_ids` filter) never promoted to checkboxes;
  `parent_epic: instruments_master`, 5-way `asset_group`. Still unresolved as of this pass.
- **`issues/instruments_docs_audit_outstanding_items_2026_07_08.md`**'s §H — 4 items (MVP-universe mismatch, US2Y
  genesis date, ETHA `KNOWN_ETFS` miss, CBOE snapshot rewrite) genuinely 100% tradfi content, but the doc's own body
  explicitly frames TRADFI as "intentionally excluded" from its own scope and its `parent_epic` is `instruments_master`
  (5-way `asset_group`) — same precedent as the doc above.
- **`issues/uac_per_venue_seed_fallback_removal_deferred_2026_07_26.md`** — wiring live catalogue providers for
  DEFI/TRADFI/PREDICTION into `deployment-api/venue_resolution.py` is real, bounded, new engineering work, but
  `parent_epic: cefi_master` — cefi's own audit is the right vehicle to draft it, not tradfi.
- **`issues/honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md`** — an open `[CODE] P1` (line 503) to
  backfill historical CeFi/TradFi (incl. CME) manifest rows with the corrected per-instrument_type split; 4-way
  `asset_group` `[cefi, defi, tradfi, prediction]`, `instruments_master` epic — same precedent.

## Reconciliation ledger (orphan count accounting)

17 orphaned docs total this pass = 3 source docs drafted into the 3 todos above + 4 too-large-or-risky + 3
operator-gated + 1 conflict-gated (2 sub-items, same doc) + 1 already-in-flight (batch7's own todo 3 covers the
diagnostic half) + 1 already-drafted-elsewhere + 1 time-gated (same doc as todo 3 above, its second item) + 4 flagged
cross-tranche-owned. Every orphaned doc found this pass has a durable disposition recorded either as a todo above or in
one of the Deferred/Flagged sections — none is left only in this plan's own drafting-session reasoning.

## File-collision matrix (verified before finalizing — same-priority todos run concurrently by default)

| Todo | Primary file(s) touched                                                                                                    |
| ---- | -------------------------------------------------------------------------------------------------------------------------- |
| 1    | `instruments-service/scripts/canonicalize_cboe_vx_combo_catalog_2026_07_08.py` + `..._dbeq_stock_class_...py`              |
| 2    | `unified-api-contracts/.../_candle_contracts.py` + `market-data-processing-service/.../ohlcv_passthrough.py`               |
| 3    | `features-service` delta_one pre-flight scanner (exact file TBD by the worker — not yet identified below the module level) |

No file appears twice — all 3 todos touch distinct repos/files.

## Reconciliation

Once a todo here ships, flip the corresponding checkbox/section in its named source doc, citing this plan's commit as
evidence. This plan's own reconciliation-then-archive step is machine-gated via a companion
`tradfi_satellite_ao_dispatch_batch8_2026_08_08_finalize.md` (`depends_on` on this plan plus `gate_on_depends: true`),
mirroring the batch1-7 finalize pattern.

## Progress Log

- **2026-08-08 (ag_closeout_auditor, slot 6)**: Phase 0-3 run. Phase 1's first pass over-excluded 21/40 docs as
  `exclude_cross_cutting`; a dedicated verification pass reconciled this against the primary-owner rule, confirming 17
  and reclassifying 4 to `orphaned_never_touched` (all 4 independently corroborated by matching batch7's own "Flagged,
  not batched" list from 2 days prior). 3 of 17 orphaned docs cleared the conflict-check and are drafted above; 1
  candidate (`tradfi_volatility_no_perp_fx_underlyings_code_gap_2026_08_06.md`) failed the conflict-check against a doc
  outside tradfi's own covering set and is deferred, not drafted.
- **2026-08-08 (operator approval)**: flipped `status: draft` → `active` after a fresh conflict-check re-verified the
  original Phase 3 clearance: (a) no `tradfi_master` sibling batch drafted after this one exists (batch6/7 remain the
  only other active tradfi batches, both already accounted for in this doc's own drafting/file-collision matrix); (b)
  re-grepped the 3 todos' target files (`canonicalize_cboe_vx_combo_catalog_2026_07_08.py`/
  `canonicalize_dbeq_stock_class_catalog_2026_07_08.py`, `_candle_contracts.py`/`ohlcv_passthrough.py`, and the
  delta_one pre-flight scanner) across the full active corpus — only this doc and its cited source docs reference them,
  no new claim; (c) `tradfi_consolidated_closeout_2026_07_18.md` unchanged since this batch's drafting. `locked_by`
  unset. Dispatching.

- **context-scout 2026-08-09**: populated/refreshed context_scope (6 entries).

## Codex SSOTs

`/codex/02-data/availability-manifest-and-data-status.md`,
`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md`.
