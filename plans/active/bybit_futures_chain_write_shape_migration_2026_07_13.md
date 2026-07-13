---
doc_type: plan
title: Migrate BYBIT futures_chain historical data to the canonical underlying= hive shape
summary: >-
  BYBIT raw_tick_data instrument_type=futures_chain has at least 3 coexisting/sequential write shapes across ~2025-06
  through 2026-05 (flat glued base+quote files, bare-underlying flat siblings, and the correct underlying= hive form) —
  a regex bug fixed in code 2026-07-09 was never backfilled, and the true affected window is wider than first estimated.
  Audit the exact scope, then reshape/backfill to the single canonical underlying= form with parity verification before
  any cleanup of the non-canonical originals.
status: active
nature: process
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service, market-data-processing-service]
scope: [engineer]
tags: [migration, bucket-placement, data-correctness, canonicalisation, cefi, bybit, futures_chain]
related: [issues/bybit_futures_chain_write_shape_2026_07_13.md, aster_cefi_data_defi_bucket_migration_2026_07_13.md]
created: 2026-07-13
last_updated: 2026-07-13
parent_epic: mtds_mdps_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2.4
assigned_role: data_engineering
drift_direction: advance-code
depends_on:
source:
  [
    "Follow-up to issues/bybit_futures_chain_write_shape_2026_07_13.md (filed during the deployment-service
    bigquery_feature_external_tables.tf fix session, 2026-07-13). Operator directed a real fix + AO dispatch after a
    same-day rescoping check found the affected window is wider than the issue doc's initial spot-check estimated
    (~2025-06 through ~2026-05, not just 2026-01; some days carry a THIRD shape — bare-underlying flat files, e.g.
    ETH.parquet, coexisting with the glued BTCUSDT-style files on the same day; no futures_chain data found for BYBIT at
    all June-July 2026, pre- or post the 2026-07-09 code fix — needs explanation).",
  ]
locked_by: live-defi-rollout
locked_since: 2026-05-21
supersedes:
superseded_by:
---

# Migrate BYBIT futures_chain to the canonical underlying= shape

## Finding (2026-07-13, rescoped same day from the original issue doc)

`gs://market-data-tick-cefi-prd-central-element-323112/raw_tick_data/by_date/`,
`pipeline_mode=batch_tardis/asset_group=cefi/venue=BYBIT/instrument_type=futures_chain/` has AT LEAST 3 shapes,
confirmed via direct sampling (not yet a full day-by-day audit — that is this plan's Phase 1):

1. **Correct canonical hive form**: `.../data_type=trades/underlying={U}/ticks.parquet` — matches the SSOT
   (`market-tick-data-service/docs/GCS_PATHS.md`, `docs/canonical-write-conventions.md`), same shape DERIBIT uses
   correctly across its whole history (DERIBIT needs NO migration — its shape is already canonical, confirmed via
   codex + consistency across 2019-2026; do not touch it, per the same investigation that found this BYBIT issue).
2. **Bare-underlying flat siblings**: e.g. `ETH.parquet` coexisting with `ETHUSDT.parquet` in the SAME
   `data_type=trades/` folder on the same day (confirmed 2025-06-01, 2025-09-01).
3. **Glued base+quote flat files (the regex-bug window)**: `BTCUSDT.parquet`, `ETHUSDT.parquet`, etc., no `underlying=`
   segment. Root cause documented in `canonical-write-conventions.md` lines 212-217 (`_extract_underlying_for_chain`
   regex bug, captured `BTCUSDT` instead of `BTC`), **fixed in code 2026-07-09**.

**Rescoped date range** (wider than the issue doc's initial 2026-01 estimate): glued-shape files confirmed present on
sampled days from **2025-06-01 through 2026-05-01**; **no futures_chain data at all found for BYBIT from 2026-06-01
onward** (checked through 2026-07-13, both the flat and hive forms — needs explanation: did collection pause, move
venues, or change instrument_type classification? Phase 1 owns this).

> **✅ Superseded by Phase 1's exhaustive audit (2026-07-13)**: the true glued-shape window is **2025-02-11 →
> 2026-05-22** (wider on both ends than this section's sampling estimate above), and the June-July 2026 absence is
> explained — see Phase 1 Todo 1 below for the full results and the cross-reference to the system-wide Tardis
> concurrent-IP-lockout issue that's the likely cause.

## Codex SSOTs

- `market-tick-data-service/docs/GCS_PATHS.md`, `docs/canonical-write-conventions.md` (canonical `underlying=` hive
  shape for `futures_chain`/`options_chain`)
- `codex/02-data/availability-manifest-and-data-status.md` (manifest rewrite discipline, single-walk rule)
- `codex/05-infrastructure/gcs-object-operations.md` (`gcs_copy_object`/`gcs_delete_object`, never subprocess
  `gcloud`/`gsutil`)

## Phase 1 — Full scope audit (P0)

- [x] [DATA] P0. ✅ Full (not sampled) day-by-day walk of
      `pipeline_mode=batch_tardis/asset_group=cefi/venue=BYBIT/instrument_type=futures_chain/data_type=trades/` across
      2023-02-01 → 2026-06-10 (padded around a bisection probe that found real data 2023-04-05 → 2026-05-22) —
      `market-tick-data-service@5e367479` (`scripts/audit_bybit_futures_chain_shape_scope_2026_07_13.py`), run for real
      against production GCS (1226 days audited in ~30s). Wrote per-day classification to
      `gs://market-data-tick-cefi-prd-central-element-323112/_index/audit/bybit_futures_chain_shape_scope_2026_07_13.parquet`
      (1226 rows). **Results:**
  - Day classification counts: `absent`=495, `hive_only`=23, `bare_flat_only`=97, `bundled_flat_only`=41,
    `glued_flat_only`=162, `mixed`=408.
  - **Exact shape (3) glued-file window: 2025-02-11 → 2026-05-22** — WIDER than this plan's own "rescoped" estimate
    (2025-06-01 was just the earliest day previously _sampled_, not the true start; the true start is ~3.5 months
    earlier). `hive` (correct form) is present 2023-04-05 → 2025-03-22 (281 days); `bare_flat` 2023-04-05 → 2025-09-23;
    `bundled_flat` (bare `ticks.parquet`) 2024-11-12 → 2025-07-18. All 4 shapes coexist/overlap across parts of the 2025
    window — 408 `mixed` days confirms this is not a clean sequential handoff.
  - **Last day with ANY BYBIT futures_chain data (any shape): 2026-05-22** — confirmed, not 2026-05-01 as this plan's
    finding section estimated; also not a sampling gap (the full day-by-day walk found genuinely zero objects from
    2026-05-23 onward through 2026-06-10).
  - **June-July 2026 absence explained — NOT BYBIT-specific, NOT futures_chain-specific.** A follow-up live-GCS check
    (whole-bucket, not just BYBIT) found the ENTIRE `pipeline_mode=batch_tardis` partition (covers BINANCE-FUTURES,
    BYBIT, BITGET-FUTURES, UPBIT, OKX-SWAP, KRAKEN-FUTURES, OKX-FUTURES, DERIBIT, and all other Tardis-sourced CeFi
    venues) collapsed from ~4,500 objects/day (2026-05-20/22) → ~500 (2026-05-23) → a flat 203/day (2026-05-25 through
    2026-06-03, all `EXTENDED-STARKNET` — a mislabeled remnant, not real CEX capture) → **zero** from 2026-06-04 onward.
    Meanwhile sibling `pipeline_mode=batch_aster`/`batch_hyperliquid`/`batch_extended` have normal objects on
    2026-06-15/2026-07-01/2026-07-10 (current dates) — so this is a `batch_tardis`-specific cessation, not a bucket-wide
    or manifest-wide issue. This lines up with — and is a sharper, write-level corroboration of — the already-tracked P0
    issue `issues/tardis_concurrent_ip_lockout_2026_07_12.md` (Tardis academic key allows only ONE concurrent IP; 74.9%
    of all cefi `attempted_failed` rows are 403 code=274 lockouts, not honest absence). Added a cross-reference addendum
    to that issue's Verification Log with this write-level finding (zero GCS objects, not just elevated
    `attempted_failed` counts) — see that doc for the full remediation status (option (a) GCS-lease stopgap shipped
    DEFAULT-OFF 2026-07-12, awaiting operator enablement). **Not a new issue** — already P0-tracked; this plan's
    BYBIT-specific write-shape problem (3 coexisting shapes 2023-2025) is orthogonal to this system-wide 2026-06+
    capture-cessation finding and does not block Phase 2's reshape work (which only touches the 2023-04→2026-05-22
    window where data actually exists).
  - Todo #2 below (shape-2 duplicate-vs-unique determination) is unblocked by this audit's per-day classification.
- [x] ✅ [DATA] P0. For every day classified shape (2) or mixed (bare-underlying + glued coexisting): determine whether
      the two files are duplicates (same trades, different naming) or genuinely different data — **DONE, slot 8,
      read-only investigation, no code shipped (none needed — pure data-comparison finding).** Sampled 5 days across the
      audit's classification bands (2023-04-05, 2023-04-10, 2023-06-01, 2024-11-15, 2025-03-22) and downloaded + diffed
      both variants at row level (sort by `(timestamp, id)`, compare
      `exchange/symbol/timestamp/local_timestamp/     id/side/price/amount`):
  - **`bare_flat` (e.g. `BTC.parquet`) vs `hive` (`underlying=BTC/ticks.parquet`) on the same day**: the bare_flat file
    is consistently a **strict subset of the hive form's contract-expiry coverage** — e.g. 2023-04-05's `BTC.parquet`
    holds only 2 of that day's 7 distinct BTC futures contracts (`BTC-29SEP23`/`BTC-21APR23`, symbols like
    `BTC-07APR23`/`BTC-28APR23`/`BTC-26MAY23`/`BTC-30JUN23`/`BTC-14APR23` exist ONLY in the hive file); every
    overlapping contract's rows are **byte-identical** between the two forms (exact row-count match per contract AND
    `DataFrame.equals()` True on the common columns, confirmed for all 4/5 sample days where both forms coexist). Zero
    symbols found existing ONLY in the flat form across all samples (`only_in_flat` empty set every time).
  - **`bundled_flat` (bare `ticks.parquet`) vs its sibling per-symbol `bare_flat` files on the same day**: 2024-11-15
    confirmed the bundled file is an **exact concatenation** of that day's `BTC.parquet`+`ETH.parquet`+`SOL.parquet` —
    34,605 rows in both, `DataFrame.equals()` True after sorting, zero symbols exclusive to either side. This
    corroborates the issue doc's original 2025-01-01 spot-check ("size ≈ sum of the three per-underlying hive files")
    with an exact row-level proof rather than a size approximation.
  - **Verdict: shape (2) in BOTH its variants is a pre-existing PARTIAL duplicate of shape (1)/(3)'s data, never a
    source of genuinely unique trades** — it needs NO reshape logic of its own. Phase 2's reshape script can treat every
    `bare_flat`/`bundled_flat` object as safe-to-supersede-then-delete once its overlapping hive/canonical counterpart
    is confirmed present (no new data to migrate FROM these forms). **Caveat (sample-based, not exhaustive)**: only 5 of
    the 831 non-absent audited days were checked at row level — Phase 2's dry-run/verify step should still run a real
    byte/row parity check per day before treating any specific bare_flat/bundled_flat file as disposable, rather than
    assuming this pattern holds for all 831 days from a 5-day sample.

## Phase 2 — Build + dry-run the reshape (P0)

- [x] ✅ [DATA] P0. Build a reshape/backfill script (new script under `market-tick-data-service/scripts/`,
      `# Epic: mtds_mdps_master`, `# Lifecycle: oneoff` header per `codex/06-coding-standards/script-homes.md`) that
      parses glued `{BASE}{QUOTE}.parquet` filenames back into `{underlying}/{quote}` using the SAME
      base/quote-splitting logic the 2026-07-09 code fix now uses going forward (do not reinvent — import/reuse it),
      server-side copies to the canonical `underlying={U}/ticks.parquet` path via UTL `gcs_copy_object`, and is
      idempotent (skip when the canonical target already exists and is verified byte/row-identical). Handle shape (2)
      per Phase 1's duplicate-vs-unique finding. DRY-RUN default, `--apply` to mutate. — **DONE, slot 14,
      market-tick-data-service@`6f0efb52` (`scripts/reshape_bybit_futures_chain_glued_to_hive_2026_07_13.py`)**. Reads
      the Phase 1 audit parquet directly (single-walk discipline — no fresh corpus scan) to get the exact glued-present
      day list; extracts underlying via `TardisAdapter._extract_underlying_for_chain` (imported, not reimplemented, per
      the todo's own directive); idempotent `(size, crc32c)` parity check mirroring
      `migrate_aster_cefi_defi_bucket_2026_07_13.py`'s proven design from earlier this session (skip if matching,
      flag-not-overwrite if mismatched). Shape (2) is correctly OUT of this script's scope per Phase 1 Todo 2's own
      finding (needs no reshape logic, it's a pure duplicate) — the script only classifies+processes shape (3) glued
      files, verified via regex (`_GLUED_RE`) that excludes bare-underlying and bundled (`ticks.parquet`) filenames.
      Shipped after a repo-blocker (`RB-d6cac7c5`, pre-existing `check_adapter_contract_regression` stale-baseline
      failure, unrelated to this change — see
      `plans/active/issues/mtds_adapter_contract_regression_stale_baseline_2026_07_13.md`) resolved via `watcher_green`.
- [x] ✅ [DATA] P0. Dry-run across the full audited scope (Phase 1's day list); verify planned rename/copy count matches
      the audit; spot-check 10+ planned reshapes for correctness (base/quote split, target path). — **DONE, slot 14**
      (same dispatch as Todo 1 above, since Todo 1 wasn't done yet when this todo was dispatched). Full dry-run across
      all 323 audited glued-present days (2025-02-11 → 2026-05-22): **835 objects planned to reshape**, 0 errors.
      Spot-checked the 10 printed dry-run samples plus a separate stratified sample (every 15th day) for
      base/quote-split correctness across 7 distinct underlyings (`BTC`, `DOGE`, `ETH`, `MNT`, `SOL`, `XAUT`, `XRP`) —
      all correct splits, all correct target paths (`.../data_type=trades/underlying={U}/ticks.parquet`). Also verified
      (via a real GCS sample across 5 spread days) that no day has more than one glued source file mapping to the same
      underlying — the plan's implicit 1:1-copy assumption (not a merge) holds in practice; the script's idempotent
      parity-check design would safely flag any future collision as a conflict rather than silently mis-migrating if
      this assumption is ever violated. Nothing mutated (dry-run only).

## Phase 3 — Apply + verify (P0)

- [ ] [DATA] P0. `--apply` the reshape, sharded by date range if needed (VM launch per
      `codex/05-infrastructure/vm-launcher-runbook.md`, SPOT provisioning, no fire-and-forget — verify STARTED +
      progress + terminal state).
- [ ] [DATA] P0. Post-apply verification: re-run Phase 1's audit against the result, confirm 0 non-canonical shapes
      remain in the migrated window; spot-check row/byte parity (not just object presence) on 20+ migrated (day, symbol)
      pairs.
- [ ] [DATA] P1. Rewrite/extend the canonical `_index/availability_index.parquet` manifest rows for the reshaped objects
      (mirrors the pattern in `aster_cefi_data_defi_bucket_migration_2026_07_13.md` Phase 3) — dedup any rows that
      collapse to the same canonical key.

## Phase 4 — Cleanup (gated, separate from the reshape — P1)

- [ ] [DATA] P1. **BLOCKED-OPERATOR-DECISION** — only after Phase 3's parity verification is fully green: delete the
      non-canonical (glued + bare-underlying) originals. Version-aware, snapshot first, same rigor as
      `bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md` Phase-7. Explicitly NOT bundled with the reshape
      apply step.

## Success criteria

- Every BYBIT `futures_chain` object under the audited scope resolves to the single canonical
  `underlying={U}/ticks.parquet` shape — verified via a real BigQuery/query-style read, not just object presence.
- The June-July 2026 data absence is explained (documented finding, not a mystery left open).
- DERIBIT and all other `futures_chain` venues are untouched — this plan is BYBIT-scoped only.
