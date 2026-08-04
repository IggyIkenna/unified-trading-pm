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
    /plans/active/issues/defi_dex_pool_fees_retirement_recommendation_2026_08_04.md,
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

| #   | Scope                                                                          | Mechanism                                                                                    | Status at checkpoint time                                                                                                                                             | How to check current status                                                                                                                                                                                                                                                                                                                      |
| --- | ------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 1   | gas_fees legacy-prefix delete (10 venues, 27,293 objects)                      | Directly executed by dispatching session                                                     | `--dry-run` done: 22,359 would-delete (twin+content verified), 4,933 content-mismatch (correctly refused), 1 no-twin. `--apply` launched, not yet confirmed complete. | `git log market-tick-data-service -- scripts/delete_legacy_gas_fees_venue_2026_08_04.py`; check `plans/archive/issues/defi_gas_fees_historical_venue_path_migration_2026_07_28.md` for a Progress Log entry with real delete counts                                                                                                              |
| 2   | POOL→pool casing fold (1,919,789 rows)                                         | NOT YET DISPATCHED — scale just discovered at checkpoint time, one level bigger than assumed | Not started                                                                                                                                                           | Check `defi_cefi_venue_chain_axis_contamination_2026_07_28.md`'s POOL todo status; if still `[ ]` with no Progress Log entry citing real execution, this is genuinely not done — dispatch it treating it with the SAME weight as the dex_pools/dex_swaps/rate_indices migration (item 4 below), not as a quick P3                                |
| 3   | Fold 22 composite `PROTOCOL-CHAIN` venues                                      | Sub-agent (background)                                                                       | Dispatched, in progress                                                                                                                                               | `git log market-tick-data-service` for a new fold script commit; check for a new `plans/active/issues/defi_underscored_multichain_composite_venue_fold_2026_08_04.md` (or similar name the agent may have chosen)                                                                                                                                |
| 4   | Migrate `dex_pools`/`dex_swaps`/`rate_indices` (~4M rows)                      | Sub-agent (background)                                                                       | Dispatched, in progress                                                                                                                                               | Check `plans/active/issues/defi_legacy_data_type_names_manifest_migration_scope_2026_08_04.md` — if its todos are still `[ ]` with the doc's title still saying "scoping only, NOT executed", this has not landed                                                                                                                                |
| 5   | Retire `dex_pool_fees` (repoint strategy reader)                               | Sub-agent (background)                                                                       | Dispatched, in progress                                                                                                                                               | Check `plans/active/issues/defi_dex_pool_fees_retirement_recommendation_2026_08_04.md`; `git log strategy-service` for a `canonical_dex_pool_provider.py` change                                                                                                                                                                                 |
| 6   | Root-cause + fix HYPERLIQUID/EXTENDED/LIGHTER/BLAZESTAKE residue               | Sub-agent (background)                                                                       | Dispatched, in progress                                                                                                                                               | Check `plans/active/issues/defi_hyperliquid_residual_manifest_rows_2026_08_04.md`                                                                                                                                                                                                                                                                |
| 7   | GMX catalogue rebuild (stop the daily re-seed) + KAMINO_LENDING                | Sub-agent (background)                                                                       | Dispatched, in progress                                                                                                                                               | Check `plans/archive/2026_07/defi_gmx_venue_removal_2026_07_25.md`'s Progress Log for a rebuild confirmation; **note**: `git status` in `instruments-service` at checkpoint time already shows `scripts/build_instrument_catalogue.py` modified + uncommitted — this is almost certainly this agent's in-progress work, do not assume it's stray |
| 8   | Register `perp_mark_price` + backfill                                          | Sub-agent (background)                                                                       | Dispatched, in progress                                                                                                                                               | Mirrors the already-shipped `perp_daily_ctx` pattern (`unified-api-contracts@17b1cf21`) — check `unified-api-contracts`'s `DATA_TYPES_BY_ASSET_GROUP["defi"]` for a `perp_mark_price` entry, and `unified-trading-pm/scripts/migration/` for a new backfill script                                                                               |
| 9   | Real fix (not permanent-exception) for the 5 CeFi-venue DeFi-bucket duplicates | Sub-agent (background)                                                                       | Dispatched, in progress                                                                                                                                               | Check `defi_cefi_venue_chain_axis_contamination_2026_07_28.md`'s P2(b) item for an update past "RE-SCOPED 2026-08-04"                                                                                                                                                                                                                            |

## Already shipped this session (durable, verified, not at risk)

- `perp_daily_ctx` registered + 1,158 manifest rows backfilled — `unified-api-contracts@17b1cf21`,
  `features-service@c678f0fd`, `unified-trading-pm@ccbef0315`.
- Stale `_schema_spec_defi.py` docstring fix — `unified-api-contracts@ab4693de` / `520baddc` (two related commits).
- GMX GCS+manifest purge — 90 objects deleted, 660 manifest rows dropped, cron resumed. Corrected a stale "already
  complete" claim in the archived removal doc.
- GMX 4 residual-row root cause found (stale `catalog.parquet`, daily re-seed) — feeds directly into item 7 above.
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
