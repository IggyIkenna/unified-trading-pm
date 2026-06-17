---
title:
  "Hyperliquid cefi data stranded on retired pipeline_mode=batch_hyperliquid_rest — RESOLVED 2026-06-17 (defi was empty
  derived cells, not data)"
created: 2026-06-17
status: resolved
priority: P2
locked_by: live-defi-rollout
source:
  - 2026-06-17 carry_staked_basis harness work — verifying HL funding read path surfaced the stranded pipeline_mode
parent_epic: mtds_mdps_master
---

# Hyperliquid cefi+defi data stranded on `batch_hyperliquid_rest` (missed by v9 migration)

## What I found — and what it turned out to be (resolved 2026-06-17)

Operator R4 (2026-06-07) retired the glued-transport `hyperliquid_rest` pipeline_mode → canonical
`pipeline_mode=batch_hyperliquid` (vendor only) with `transport=rest` as a separate manifest column. The **code** is
fully canonical (UAC `PipelineMode` has no `*_HYPERLIQUID_REST` member; the resolver maps
`HYPERLIQUID → BATCH_HYPERLIQUID`; `hyperliquid_rest` survives only as a legacy READ-token in UAC
`possible_manifest.py`). But the on-disk DATA was never migrated and the rename was in NO v9 migration script.

**The verdict-pack "19.4K + 64K = ~83K" were PROJECTED/derived index counts (`_index/audit/projected_index_*.parquet`),
not on-disk reality. Tracing to ground truth (2026-06-17) corrected the picture — it was smaller and cleaner:**

- **cefi = 19,361 REAL objects** physically on `pipeline_mode=batch_hyperliquid_rest/` paths (data_types
  `derivative_ticker` / `trades` / `book_snapshot_5` / `liquidations`). This is the genuine stranded data.
- **defi = 0 objects, 0 captured.** The "64K" is **64,418 `empty_confirmed` (64,232) + `attempted_failed` (186)**
  manifest cells — `perp_funding` across **40 non-HL DeFi/lending venues** (UNISWAPV4, AAVEV3-\*, COMPOUNDV3-\*,
  ETHENA…). They carry `pipeline_mode=batch_hyperliquid_rest` **only in the audit PROJECTION's derivation**
  (perp_funding → HL handler mode), NOT on disk. There is **no defi data to migrate.**
- **The LIVE consolidated manifest never stores `pipeline_mode`** (blank/None for all 2.73M cefi + 1.58M defi rows;
  per_vm shards = 0 rows with the literal). pipeline_mode is DERIVED from object paths at projection/rebuild time. So
  there was **no live manifest re-key to do** — only the object paths carried the literal.
- **Fleet-wide scan = HYPERLIQUID is the SOLE glued-transport offender** across all 5 asset_groups; every other source
  (tardis, massive, databento, onchain_rpc/subgraph, pyth_hermes, polymarket_clob, odds_api) is canonical vendor-based.

## Resolution (2026-06-17) — ✅ DONE

Migrated the cefi objects with `market-tick-data-service/scripts/migrate_hyperliquid_rest_pipeline_mode_2026_06_17.py`
(segment-based path rename, server-side `gcs_copy_object` → verify dst → `gcs_delete_object`, idempotent,
dry-run-first). Drain satisfied (no HL writers running; per-epic data fleet down). Independently verified: **0 objects
remain under `batch_hyperliquid_rest` fleet-wide; the 19,361 objects are now under `batch_hyperliquid` with
byte-for-byte parity** (per-day counts matched exactly, e.g. day=2026-04-01 28→28, day=2025-06-01 19→19), zero data
loss.

- [x] [DATA] ✅ P2. cefi object rename `batch_hyperliquid_rest → batch_hyperliquid` (19,361 objs) — verified 0 remaining
      / 0 loss. `mtds/scripts/migrate_hyperliquid_rest_pipeline_mode_2026_06_17.py`.
- [x] [DATA] ✅ P2. Manifest re-key — **N/A by construction**: the live `_index` stores pipeline_mode BLANK (derived
      from paths at projection time); 0 stored rows + 0 per_vm shard rows carried the literal. A fresh projection now
      derives `batch_hyperliquid` from the verified-clean object paths. defi rows are empty/failed cells (no data) whose
      projection-label resolves to canonical once regenerated with current code — no migration.
- [ ] [DATA] P3. defi projection-label cosmetic: the audit projection labels 40 venues' empty `perp_funding` cells
      `batch_hyperliquid_rest`. Confirm the projection/`analyze_diff` derivation (PM verdict-pack tooling) uses the
      current resolver so a regenerated projection shows 0 `batch_hyperliquid_rest` in both AGs. **Repo:
      unified-trading-pm (verdict-pack tooling) + market-tick-data-service (rebuild derivation).**
- [ ] [DATA] P3. Drop the transitional `hyperliquid_rest` read-tokens in UAC `possible_manifest.py` (POSSIBLE_SOURCES
      CEFI/DEFI) and remove `_VENUE_DIR_LEGACY_PIPELINE_MODES` in the carry harness — now that 0 objects carry the
      literal. **Repo: unified-api-contracts + e2e-testing.**
- [ ] [DOCS] P3. Update stale `BATCH_HYPERLIQUID_REST`/`hyperliquid_rest` refs in
      `codex/02-data/pipeline-mode-and-batch-live-reconciliation.md`. **Repo: unified-trading-pm.**

Cross-link: `plans/active/pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md` (the R4 retirement
SSOT).
