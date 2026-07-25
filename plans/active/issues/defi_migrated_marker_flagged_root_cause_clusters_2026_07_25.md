---
doc_type: issue
title: FLAGGED `_migrated_*` markers are 3+ distinct unresolved root-cause clusters, not just interrupted runs
summary:
  Live sampling of the delete_migrated_defi_markers_2026_07_23.py dry-run (2026-07-25) found the FLAGGED population is
  NOT dominated by simple interrupted-migration cases as originally assumed. At least 3 distinct clusters with different
  root causes and no safe blind-remediation path -- GMX perp_funding 1-row aggregate snapshots (~1,896 markers, matches
  the tool's own docstring precedent, needs_attribution flush never ran), TRADER_JOE_V2/AVALANCHE dex_pool_state rows
  that DO have a real distinct on-chain pool_id per row but never got symbol/pool_address resolved (~944 markers, NOT
  unattributable data, an unresolved symbol-resolution gap), and an lst_rates cluster (COINBASE/MAKER/SWELL, ~678
  markers). None of these are fixed by blindly re-running migrate_defi_batch_to_per_instrument.py --apply.
status: open
nature: issue
asset_group: defi
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [defi, per-instrument-model, needs-attribution, symbol-resolution, migration, data-correctness]
related: [defi_consolidated_closeout_2026_07_18]
created: 2026-07-25
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: research
drift_direction: unknown
depends_on: []
source:
  [
    "found 2026-07-25 during a /autonomous session's read-only sampling of the in-flight
    delete_migrated_defi_markers_2026_07_23.py dry-run, per the operator's 'migrate the FLAGGED ones too' direction
    (defi_consolidated_closeout_2026_07_18.md progress log, 2026-07-25 entry)",
  ]
resolved_by:
locked_by:
locked_since:
---

# FLAGGED `_migrated_*` markers are 3+ distinct unresolved root-cause clusters

## Why this exists

`delete_migrated_defi_markers_2026_07_23.py`'s dry-run (running now on VM
`canonical-migration-defi-marker-cleanup-20260724-182226`, two parallel processes, see the plan's 2026-07-25 progress
entry) never deletes FLAGGED markers — only SAFE ones. The operator asked: for markers that come back FLAGGED, we should
also migrate/fix those, "else what's the point." Before attempting any remediation, this issue characterizes WHAT the
FLAGGED population actually is, from live sampling of ~268k processed markers (both shards' resume-logs merged,
pre-dedup) as of 2026-07-25 ~00:40 UTC.

**Bottom line: do NOT blindly re-run `migrate_defi_batch_to_per_instrument.py --apply` against FLAGGED cells.** The
population splits into distinct clusters with different root causes; at least one (TRADER_JOE_V2) would NOT be fixed by
a re-run at all, since the underlying gap is upstream of the migration tool.

## Cluster breakdown (raw counts, pre-dedup across shard-a/shard-b, ~268k of 356,391 markers sampled so far)

| Cluster                                                                                      | Count                                | Disposition                     | Root cause (verified via direct parquet inspection)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| -------------------------------------------------------------------------------------------- | ------------------------------------ | ------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `GMX` / `ARBITRUM`+`AVALANCHE` / `perp_funding`                                              | 1,896                                | `FLAGGED_NO_SIBLINGS_NO_BACKUP` | Every sampled marker has `marker_rows == 1` — a single daily funding-rate aggregate, not per-instrument data. Matches the tool's own docstring precedent exactly ("5/9 sampled GMX perp_funding 1-row snapshots had NO needs_attribution twin... the marker itself is the ONLY surviving copy"). The `_needs_attribution/day=.../perp_funding_*.parquet` object is absent for these days — the original migration run's end-of-run flush apparently never fired for this pipeline_mode/data_type.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| `TRADER_JOE_V2` / `AVALANCHE` / `dex_pool_state`                                             | 944 (878 NO_SIBLINGS + 66 SHORTFALL) | both                            | Verified on a concrete example (`day=2022-02-15`, 659 rows / `day=2022-03-12`, 522 rows, etc.): `instrument_id`/`symbol`/`pool_address` are 100% NULL on every row, so the tool correctly sees "unattributable." **But `pool_id` is 100% populated with a distinct real on-chain address per row** (e.g. `0x92030226cbd8b8cf...`) — this is NOT identity-less data, the symbol-resolution step for these specific pools (obscure pairs — sampled names included WAVAX-MLORD, WAVAX-THRONE, WAVAX-THUNDER) never populated `symbol`/`pool_address` from `pool_id`. Re-running the SAME migration tool would not fix this — it doesn't do symbol resolution, it only routes rows that are ALREADY unattributable to the needs_attribution fallback (which also doesn't exist for these days — checked `_needs_attribution/day=2022-02-15/dex_pool_state_2022-02-15.parquet`, absent). Spans many consecutive days Jan-Mar 2022 — looks like a sustained gap for this venue/period, not a one-off. |
| `COINBASE`/`MAKER`/`SWELL` / `ETHEREUM` / `lst_rates`                                        | 678 (404+264+10)                     | `FLAGGED_NO_SIBLINGS_NO_BACKUP` | Not yet root-caused in detail this session (time-boxed the investigation to the two largest clusters) — flagging the volume and the venue names since `lst_rates_handler.py` was ALREADY separately flagged this session (defi_consolidated_closeout_2026_07_18.md line ~768) as writing to "a non-canonical, non-hive path" — plausibly related, needs its own look.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| `VELODROME_V2`/OPTIMISM, `CURVE`/ETHEREUM, `SUSHISWAP`/ARBITRUM `dex_pool_state`/`dex_swaps` | 421 (223+132+2 sampled so far)       | `FLAGGED_ROWCOUNT_SHORTFALL`    | Same shape as TRADER_JOE_V2 SHORTFALL cases (siblings exist for the FEW attributable rows, but most rows in the bundle are unattributed and there's no needs_attribution twin) — likely the same symbol-resolution gap, not independently verified per-venue yet.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |

These counts are from a still-running dry-run (~75% of the corpus sampled as of this writing) and are NOT deduped across
shard-a/shard-b — treat as directional, not final. The final report (once the dry-run completes or the 8h autonomous
window ends) will have exact deduped counts.

## Why this matters for the delete decision

The tool's SAFE/FLAGGED classification itself looks correct and appropriately conservative — nothing here suggests a
SAFE marker is wrongly classified. The finding is about what "fix the FLAGGED ones" actually requires:

1. **GMX perp_funding** — these are single-row daily aggregates, not something that gets "split" in the per-instrument
   sense. If the content is only in the marker (no needs_attribution twin), the real question isn't "re-run the
   migration" — it's whether these 1-row aggregates are even meant to go through the per-instrument split at all, or
   whether they should have a different retirement/keep policy from the start. **Design question, not a migration bug.**
2. **TRADER_JOE_V2 (and likely the other dex_pool_state SHORTFALL clusters)** — this is a genuine upstream gap: pools
   have a real identity (`pool_id`) but no symbol resolution. The FIX (if pursued) is a symbol/pool metadata backfill
   for these specific pools — likely an instruments-service / URDI concern, NOT something
   `migrate_defi_batch_to_per_instrument.py` can do by re-running, since it never reads a token/symbol registry, it just
   routes based on whatever `symbol`/`pool_address` already are on the row.
3. **lst_rates cluster** — needs its own investigation; flagging the volume so it isn't lost.

## Recommendation (operator decision needed — not made here)

- Do NOT re-run `migrate_defi_batch_to_per_instrument.py --apply` against any of these clusters expecting it to resolve
  them — verified it wouldn't fix at least the TRADER_JOE_V2 case, and the GMX case isn't really a "migration" problem
  at all.
- The FLAGGED markers should stay exactly as-is (never deleted) until each cluster gets its own scoped decision:
  accept-as-permanently-orphaned (GMX 1-row aggregates, if that's ruled the right call), a symbol/pool-metadata backfill
  (TRADER_JOE_V2 + likely other dex_pool_state venues), or further investigation (lst_rates).
- This is exactly what the delete_migrated_defi_markers_2026_07_23.py dry-run is FOR — it correctly refuses to touch any
  of this. No corrective action needed on that script; this issue is about what comes after, once its report is final.

## Related

- `plans/active/defi_consolidated_closeout_2026_07_18.md` — parent plan, 2026-07-25 progress log entry has the session
  context and the queued operator decisions this issue backs.
- `market-tick-data-service/scripts/one_offs/delete_migrated_defi_markers_2026_07_23.py` — the verification tool itself
  (module docstring already documents the GMX 1-row precedent this issue confirms at scale).

## Update (2026-07-25, later same session — deeper per-cluster verification)

Direct parquet inspection + two dispatched research agents refined every cluster's characterization. Corrections to the
analysis above:

- **GMX perp_funding — confirmed venue-wide daily aggregate, not per-instrument data at all.** Downloaded and inspected
  a real marker directly: `market="all"`, `symbol`/`instrument_id`/`coin` all NULL, but `funding_rate_long/short`,
  `long_oi_usd`/`short_oi_usd`, `tvl_usd`, `daily_volume_usd` populated -- one row = the WHOLE GMX venue on one chain
  for one day. There is no per-instrument content to lose; the per-instrument split migration was applied to a data_type
  that structurally isn't per-instrument. Design question (should this data_type even go through per-instrument
  splitting?), confirmed not a bug.
- **lst_rates cluster root-caused, and it's actually TWO different, more benign situations than first assumed**:
  - `COINBASE` (cbETH) / `SWELL` (swETH): every FLAGGED marker is `marker_rows=1`, and it's a genuinely legitimate
    single-instrument row (cbETH is the only token for protocol=coinbase, so 1 row/day is correct, not a data-loss
    symptom). The split-migration's "write my own leaf" step just never completed for these -- fixing this is a trivial,
    low-risk leaf-copy, not a backfill, since there's zero ambiguity about the content.
  - `MAKER` (sDAI) / `ETHENA` (sUSDe): these are PRE-2026-07-23 remnants of a data_type that has since been corrected --
    `lst_rates_handler.py`'s own code history explicitly removed sDAI/sUSDe from `lst_rates` (2026-07-23,
    `lst_venue_registry_gap_and_cron_crash_loop_2026_07_22.md`) because they're not real LSTs (no validator staking),
    reassigning them to `vault_share_price_handler.py`. These old markers represent a classification the system has
    already moved away from.
  - **Canonical destination for the 4 rate types the operator asked about**: `lst_rates` (this handler) = ONLY the
    on-chain protocol par/redemption rate (e.g. Lido's `getPooledEthByShares` via direct RPC `eth_call` -- confirmed
    reading the handler code, not the subgraph). The Chainlink/lending-oracle rate already has its own separate
    canonical home: `oracle_prices` (see `issues/defi_lst_oracle_timestamp_glued_instrument_id_2026_07_20.md`). DEX
    market rate and CEX rate for an LST token need no new data_type -- they're just that token traded on whatever
    DEX/CEX it trades on, captured by the existing `dex_pool_state`/`dex_swaps`/cefi market-data paths, same as any
    other token.
- **TRADER_JOE_V2/VELODROME_V2/CURVE dex_pool_state — root cause is an ACTIVE CODE BUG, not just historical.** Full
  detail in the new sibling issue, `issues/defi_dex_pools_subgraph_query_missing_input_tokens_2026_07_25.md`: the
  subgraph query used for these 3 venues (`_CURVE_QUERY`, verified byte-for-byte in `dex_pools_handler.py`) never
  requests `inputTokens { symbol }` from the subgraph -- only a sibling query variant (`_MESSARI_DEX_QUERY`, used by
  other venues) does. This means symbol resolution ONLY happens via the instruments-service catalogue fallback (tier 1),
  never via the subgraph (tier 2), for these 5 venues (curve/sushiswap/gmx/velodrome_v2/trader_joe_v2). **This bug is
  still live** -- DeFi capture is currently operator-paused (since 2026-07-18, pending the per-instrument
  re-architecture), so it isn't actively producing bad rows RIGHT NOW, but will resume producing them the moment capture
  restarts, unless fixed first.
- **Canonical-coverage check, answering "do we already have canonical data for this shard dimension elsewhere?"**
  (checked live GCS + codex, 2026-07-25):

  | Shard                                  | Current/live coverage?                                                                                                      | Already well-attributed?                                              |
  | -------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------- |
  | TRADER_JOE_V2/AVALANCHE/dex_pool_state | None -- venue currently empty                                                                                               | N/A                                                                   |
  | VELODROME_V2/OPTIMISM/dex_pool_state   | Yes, through 2026-07-24                                                                                                     | Yes -- masked by catalogue-tier-1 coverage despite the same query bug |
  | CURVE/ETHEREUM/dex_pool_state          | Yes, through 2026-07-18                                                                                                     | No -- still address-keyed, bug visibly live                           |
  | UNISWAP_V3/ETHEREUM/dex_pool_swaps     | Yes, through 2026-07-24                                                                                                     | Yes -- different query path, never had this bug                       |
  | HYPERLIQUID/HYPERLIQUID/perp_funding   | None as this shard -- venue reclassified `asset_group=cefi` 2026-06-25, current cefi capture only writes `data_type=trades` | N/A -- whole data_type discontinued for this venue                    |
  | SUSHISWAP dex_pool_state               | Stopped ~2026-06-20/25                                                                                                      | Was address-keyed when active (same bug)                              |
  | AURORA/AURORA/gas_fees                 | Continues under `venue=ALCHEMY,chain=AURORA` (RPC provider replaced chain as the venue key)                                 | Not really comparable -- single feed, not per-pool                    |

  Net: VELODROME_V2 and UNISWAP_V3's old batch markers are genuinely low-value to fix (current data already covers the
  same shard well). CURVE's gap is live and ongoing. TRADER_JOE_V2 and HYPERLIQUID/perp_funding have literally no
  current equivalent -- the old markers are the only record, for whatever that's worth given the underlying
  attribution/classification issues.

Full detail on the active bug: `issues/defi_dex_pools_subgraph_query_missing_input_tokens_2026_07_25.md`.
