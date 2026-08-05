---
doc_type: plan
title: >-
  DeFi distinct-values panel — drive every axis (venues/chains/instrument_types/data_types) to zero non-canonical, not a
  reduced count — in-flight tracking for a 9-way parallel dispatch
summary: >-
  Operator corrected this session's initial posture (treating several findings as "low priority, scope only, defer") —
  the actual bar is ZERO non-canonical values across every axis, permanently, with live writers and backfills verified
  not to regress the fix, not a partial cleanup. This doc is the durable tracking record for the resulting 9-way
  parallel dispatch (7 sub-agents + 2 directly-executed scripts) so results can be reconciled even if the dispatching
  session's context is lost. Checkpoint written under context pressure (68% usage) per this workspace's pre-compact
  ritual — treat every "in progress" item below as needing a live status check (git log / manifest read), not as
  evidence anything actually landed.
status: active
nature: process
asset_group: [defi, cross-cutting]
stage: [data]
repos:
  [
    unified-trading-pm,
    unified-api-contracts,
    market-tick-data-service,
    strategy-service,
    features-service,
    instruments-service,
    unified-trading-library,
  ]
scope: [engineer, admin]
tags:
  [defi, distinct-values, canonicalisation, manifest, venues, chains, instrument-types, data-types, dispatch-tracking]
related:
  [
    /plans/active/issues/defi_cefi_venue_chain_axis_contamination_2026_07_28.md,
    /plans/active/issues/defi_legacy_precanonical_composite_venue_objects_2026_07_24.md,
    /plans/active/issues/defi_legacy_data_type_names_manifest_migration_scope_2026_08_04.md,
    /plans/archive/issues/defi_dex_pool_fees_retirement_recommendation_2026_08_04.md,
    /plans/active/issues/defi_hyperliquid_residual_manifest_rows_2026_08_04.md,
    /plans/archive/2026_07/defi_gmx_venue_removal_2026_07_25.md,
    /plans/active/issues/defi_perp_daily_ctx_manifest_gap_reader_risk_2026_07_22.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
created: "2026-08-04"
last_updated: "2026-08-04"
parent_epic: manifest_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 3.6
source: >-
  Interactive session 2026-08-04, operator corrected the dispatching session's "defer, don't execute" posture twice;
  this dispatch is the direct response — verify then EXECUTE every finding, not just document it.
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
depends_on: []
context_scope:
  [
    /plans/active/issues/defi_cefi_venue_chain_axis_contamination_2026_07_28.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /codex/02-data/defi-canonical-naming-ssot.md,
  ]
---

# DeFi distinct-values — zero non-canonical dispatch (2026-08-04)

## Full non-canonical inventory the operator pasted (live panel read, this session — treat as the ground truth to

re-verify against, not the earlier 16-20-count estimates in older docs)

**Venues (~42 non-canonical)**: 9 chain-name venues (ARBITRUM/AURORA/AVALANCHE/BASE/BSC/ETHEREUM/LINEA/OPTIMISM/ POLYGON
— gas_fees legacy), 5 CeFi venues (BITFINEX/BITGET/BYBIT/KRAKEN/OKX), 4 on-chain-CLOB-reclassified venues
(BLAZESTAKE/EXTENDED/HYPERLIQUID/LIGHTER), GMX, KAMINO_LENDING, and **22 legacy `PROTOCOL-CHAIN` composite venues**
(AERODROME_V3-BASE, BALANCER×6, CAMELOT_V3-ARBITRUM, CURVE×2, PANCAKESWAP_V3×3, SUSHISWAP+SUSHISWAP_V3×4, UNISWAP_V3×5).
**Chains (2 non-canonical)**: FUTURES (fixed, code already shipped), HYPERLIQUID. **Instrument types (1 non-canonical by
scale, not by UI badge)**: `POOL` (uppercase) vs `pool` (lowercase) — silenced from the UI badge by a pre-existing
case-insensitive comparison exception, but **measured this session at 1,919,789 real manifest rows**
(`data_type=dex_pool_swaps` 1,904,256 + `dex_swaps` 15,533; `capture_status=captured` 1,919,766), spread across every
major DEX protocol. This is NOT the "small P3 cleanup" the dispatching session first assessed it as — correcting that
here explicitly. **Data types (6 non-canonical)**: `dex_pool_fees`, `dex_pools`, `dex_swaps`, `rate_indices`,
`perp_daily_ctx` (fix shipped this session, panel just hasn't refreshed — nightly rollup, cached from 2026-08-02),
`perp_mark_price`.

## In-flight work (9-way parallel dispatch) — CHECK LIVE STATUS, do not trust this table's state past the moment it

was written

| #   | Scope                                                                                                                                                                                                                                        | Mechanism                                                                                    | Status at checkpoint time                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            | How to check current status                                                                                                                                                                                                                                                                                       |
| --- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | gas_fees legacy-prefix delete (10 venues, 6,080 objects — real script is `purge_gas_fees_legacy_venue_prefixes_2026_08_04.py`, the row-1 script name below was never actually committed, likely stale/abandoned WIP from an earlier session) | Directly executed by dispatching session                                                     | **GCS-object delete 100% COMPLETE** (verified twice, directly, via a 10-venue-wide `match_glob` check — 0 remaining). **Manifest purge (12,425 rows) NOT complete** — blocked by a currently-active VM-boot `gsutil` infra hang, not a script bug; 3 IAM gaps + 2 script reliability issues found/fixed/shipped along the way. Consolidator cron resumed (was never mutated).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        | See `/plans/active/issues/defi_gas_fees_legacy_purge_manifest_step_blocked_vm_infra_flakiness_2026_08_05.md` for full detail + next-step todos.                                                                                                                                                                   |
| 2   | POOL→pool casing fold (1,919,789 rows)                                                                                                                                                                                                       | NOT YET DISPATCHED — scale just discovered at checkpoint time, one level bigger than assumed | Not started                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          | Check `defi_cefi_venue_chain_axis_contamination_2026_07_28.md`'s POOL todo status; if still `[ ]` with no Progress Log entry citing real execution, this is genuinely not done — dispatch it treating it with the SAME weight as the dex_pools/dex_swaps/rate_indices migration (item 4 below), not as a quick P3 |
| 3   | Fold 22 composite `PROTOCOL-CHAIN` venues                                                                                                                                                                                                    | Interactive session 2026-08-05                                                               | **RESOLVED — false alarm, not a bug.** Root-caused via a VM-run row-level provenance trace (`market-tick-data-service/scripts/one_offs/trace_composite_venue_provenance_2026_08_05.py`): writer is `market-data-processing-service`'s already-completed one-time `backfill_defi_dex_pool_swaps_source_correction.py` campaign (2026-08-03/04, 813,150 objects copied, 0 errors). Real backing data confirmed under MDPS's own `processed_candles/` path (the 2026-08-04 investigation only checked MTDS's `raw_tick_data/` convention — wrong path, not wrong conclusion). No fold, no purge, nothing to execute.                                                                                                                                                                                                                                                                                                                                                                                                                                                                    | See `plans/active/issues/defi_underscored_multichain_composite_venue_fold_2026_08_04.md` (status: resolved) for full detail.                                                                                                                                                                                      |
| 4   | Migrate `dex_pools`/`dex_swaps`/`rate_indices` (~4M rows)                                                                                                                                                                                    | Sub-agent (background)                                                                       | Dispatched, in progress                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              | Check `plans/active/issues/defi_legacy_data_type_names_manifest_migration_scope_2026_08_04.md` — if its todos are still `[ ]` with the doc's title still saying "scoping only, NOT executed", this has not landed                                                                                                 |
| 5   | Retire `dex_pool_fees` (repoint strategy reader)                                                                                                                                                                                             | Sub-agent (background)                                                                       | **DONE.** DIAG confirmed CURVE's `dex_pool_state` already carries real subgraph fees_usd/volume_usd/fee_rate_bps AND the `dex_pool_fees` corpus itself was 0 objects for its entire lifetime — retirement is risk-free. Repointed `canonical_dex_pool_provider.py`, deleted `materialize_dex_pool_fees.py`, 8/8 tests pass. strategy-service commit `f7ca12767a51dc5e7d9327b1d0b875dc5454bb8a`. Found + filed a SEPARATE genuine BALANCER writer-schema gap (`swap_volume`/`swap_fees` vs `tvl_usd`/`volume_usd`, cumulative not daily) as `plans/active/issues/defi_balancer_dex_pool_state_writer_schema_mismatch_2026_08_04.md` — does not block this item.                                                                                                                                                                                                                                                                                                                                                                                                                       | Check `/plans/archive/issues/defi_dex_pool_fees_retirement_recommendation_2026_08_04.md` (all todos closed); `git log strategy-service` for the commit above                                                                                                                                                      |
| 6   | Root-cause + fix HYPERLIQUID/EXTENDED/LIGHTER/BLAZESTAKE residue                                                                                                                                                                             | Sub-agent (background)                                                                       | Dispatched, in progress                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              | Check `plans/active/issues/defi_hyperliquid_residual_manifest_rows_2026_08_04.md`                                                                                                                                                                                                                                 |
| 7   | GMX catalogue rebuild (stop the daily re-seed) + KAMINO_LENDING                                                                                                                                                                              | Interactive session 2026-08-05                                                               | **KAMINO_LENDING half DONE.** Root-caused: a currently-LIVE bug in `risk_params_handler.py`/`lending_indices_handler.py` writing bare `venue=protocol` ("kamino_lending" -> uppercased KAMINO_LENDING by `write_defi_rows()`) instead of canonical `KAMINO-SOLANA` — confirmed writing real data as recently as 2026-08-04/05, not dead residue. Fixed via a shared `canonical_lending_venue()` helper (`market-tick-data-service@bd153821`) — also caught + fixed `solend`/`marginfi` (same bug, just enabled in risk_params by a concurrent commit landing mid-fix). Backfilled the 64 historical KAMINO_LENDING objects (2026-06-01/06-02/08-03/08-04) to canonical venue (`market-tick-data-service@0bfe72f5`), verified via a fresh manifest shard. GMX half: not re-checked this session (was already confirmed clean earlier 2026-08-05, see the GMX retraction entry above).                                                                                                                                                                                                 | See `plans/active/issues/defi_hyperliquid_residual_manifest_rows_2026_08_04.md` for the parent BLAZESTAKE/EXTENDED/LIGHTER/HYPERLIQUID investigation this reused the same session's findings from.                                                                                                                |
| 8   | Register `perp_mark_price` + backfill                                                                                                                                                                                                        | Interactive session 2026-08-05                                                               | **DONE.** Registered as canonical data_type + SchemaContract (`unified-api-contracts@75245222`) — pure manifest-visibility fix, zero live-reader risk (confirmed nothing reads this data_type today, unlike `perp_daily_ctx`). Backfill script (`unified-trading-pm/scripts/migration/register_perp_mark_price_manifest_backfill_2026_08_05.py`) found exactly 316 days / 22,690 objects (matches the archived 2026-07-13 migration doc's own "316d" figure exactly) — registered as 316 manifest rows, verified via a fresh per-VM shard read. Two bugs caught+fixed along the way: the first apply attempt silently failed to persist (forgot `MANIFEST_PER_VM_SHARDS=true`, the script's own final log line printed "success" regardless of the underlying write's outcome — re-ran correctly the second time); the original per-file row-count design would have taken 60+ minutes (22,690 sequential downloads) — fixed to use `len(blob_names)` directly, reusing the SAME verified 1-row/file shortcut the perp_daily_ctx precedent established for this identical HL corpus. | Verify: `unified-api-contracts` `DATA_TYPES_BY_ASSET_GROUP["defi"]` has `perp_mark_price`; fresh coverage.json shows 316 manifest rows registered.                                                                                                                                                                |
| 9   | Real fix (not permanent-exception) for the 5 CeFi-venue DeFi-bucket duplicates                                                                                                                                                               | Sub-agent (background)                                                                       | Dispatched, in progress                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              | Check `defi_cefi_venue_chain_axis_contamination_2026_07_28.md`'s P2(b) item for an update past "RE-SCOPED 2026-08-04"                                                                                                                                                                                             |

## Already shipped this session (durable, verified, not at risk)

- `perp_daily_ctx` registered + 1,158 manifest rows backfilled — `unified-api-contracts@17b1cf21`,
  `features-service@c678f0fd`, `unified-trading-pm@ccbef0315`.
- Stale `_schema_spec_defi.py` docstring fix — `unified-api-contracts@ab4693de` / `520baddc` (two related commits).
- GMX GCS+manifest purge — 90 objects deleted, 660 manifest rows dropped, cron resumed. Corrected a stale "already
  complete" claim in the archived removal doc.
- GMX 4 residual-row root cause found (stale `catalog.parquet`, daily re-seed) — feeds directly into item 7 above.
- **GMX "3,305 residual manifest rows" finding (2026-08-05, interactive session continuation) — investigated, RETRACTED,
  not real.** Surfaced while ad-hoc-querying the DeFi tick manifest during the gas_fees purge (item 1); the first query
  hit the wrong bucket (`instruments-store-defi-prd-*`, the catalogue bucket, instead of `market-data-tick-defi-prd-*`,
  the tick bucket the purge actually touches), and a second, correct-bucket query still returned inconsistent counts (0,
  then an error, then 0) while item 1's purge attempts were concurrently reading/mutating the same manifest. Once the
  manifest was fully quiescent (all further purge launches stopped, see
  `/plans/active/issues/defi_gas_fees_legacy_purge_manifest_step_blocked_vm_infra_flakiness_2026_08_05.md`), two fresh
  independent checks both returned **0 GMX rows**, and a fresh, independently-triggered honest-coverage rollup
  (`gs://central-element-323112-honest-coverage/2026-08-05/coverage.json`, `generated_at: 2026-08-05T14:42:13Z`,
  `partial: false`, all 5 asset groups measured) confirms `GMX` absent from `by_chain.defi` — matching the 4-row-case
  fix above, no new purge needed. Lesson: a manifest read taken WHILE a concurrent writer/purger is active is not
  trustworthy evidence either way; re-check once quiescent before filing a residual-row finding.
- 4 new issue docs filed: `defi_legacy_data_type_names_manifest_migration_scope_2026_08_04.md`,
  `defi_dex_pool_fees_retirement_recommendation_2026_08_04.md`, `defi_hyperliquid_residual_manifest_rows_2026_08_04.md`,
  `defi_manifest_column_fill_regression_from_gmx_purge_forced_full_merge_2026_08_04.md`.

## Big finding still open — needs operator attention independent of everything above

**`defi_manifest_column_fill_regression_from_gmx_purge_forced_full_merge_2026_08_04.md`** — the GMX purge's forced
full-merge triggered a CRITICAL `MANIFEST_COLUMN_FILL_REGRESSION` on 11 unrelated columns across the whole 42M-row DeFi
manifest (73.92%→71.71%), now live in production, NOT root-caused or remediated. This is unrelated to the
zero-non-canonical dispatch above and should not get lost in the volume of that work.

## Lessons from this checkpoint (Step 6 — carry forward, don't re-learn)

- **A "silenced by a comparison-exception" badge does not mean small scale.** POOL vs pool looked like a cosmetic P3
  until actually queried — it's 1.9M rows, comparable in size to the dex_pools/dex_swaps migration. Always get the real
  row count via a bounded manifest read before triaging severity by UI-badge visibility alone.
- **"Scope only, don't execute" was the wrong default for this dispatch.** The operator's standing principle this
  session: no axis gets a permanently-accepted duplicate; a finding that can be verified-then-executed should be, not
  filed as a recommendation. The exception that still holds: a change touching the live paper-trading determinism
  guarantee (`CanonicalPerpFundingProvider`) needs a stricter, evidence-gated bar (see item 9) — that is not laziness,
  it's a different, harder invariant.
- **Sub-agents that background their own long-running verification and then go idle without a live watchdog will stall
  silently across multiple turns** — the gas_fees sub-agent did this twice before the dispatching session took over
  execution directly. If a sub-agent reports "waiting for my own watchdog" and later shows `no active task` on resume,
  it was never actually running anything — nudge with a concrete, synchronous, narrated-inline instruction, or take over
  directly if it stalls a second time.
- **Composite-venue and non-canonical findings recur across at least 3 structurally-different populations** this session
  found (the already-folded 9-venue no-chain-variation population from 2026-07-24; the new 22-venue
  underscored-multichain population from today; the POOL-casing population) — when auditing "is X folded", verify the
  EXACT venue-name list matches, don't assume one fold covers a superficially-similar-looking one.

## Next steps for whoever resumes this (if the dispatching session's context is lost before reconciliation)

1. Check each row in the in-flight table above via the cited "how to check" method — do NOT assume anything landed.
2. For anything still not done, re-dispatch or execute directly following the same patterns already proven this session
   (five-part-proof + fresh soft-delete check for deletes; the `perp_daily_ctx` registration pattern for new data_types;
   the `fold_legacy_composite_venue_objects_2026_07_31.py` pattern for composite-venue folds).
3. Once every row above is genuinely done, re-pull the live distinct-values panel and confirm zero non-canonical remains
   (or document the specific, evidenced exceptions that genuinely can't reach zero yet, e.g. item 9 if it's still gated
   on the CeFi capture outage resolving).
4. Archive this tracking doc once superseded by a clean final state — it is a dispatch-tracking doc, not a permanent
   record.

## Progress Log

- **na-eligibility-audit 2026-08-04**: KEEP-NA, valid — live operator-session dispatch-tracking checkpoint for an
  in-flight 9-way parallel dispatch, written today under context pressure; 0 tracked `- [ ]` todos by design (its "work
  items" are a status table, not a checklist). Explicitly not archival-eligible yet (own § 4: "Archive this tracking doc
  once superseded by a clean final state") and not AO-dispatchable (every row needs a live status check a
  human/dispatching session must reconcile, not a worker-determinable outcome).
