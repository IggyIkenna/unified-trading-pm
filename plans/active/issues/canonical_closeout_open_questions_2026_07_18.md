---
doc_type: issue
title: Canonical close-out — consolidated OPEN QUESTIONS + parked decisions for the operator (2026-07-18)
summary: >-
  The single list of everything the canonical-target close-out session left for the operator to rule on when they return
  — authored under /autonomous (operator away 2h) per rule 2 (decide-and-document; park what genuinely needs them). Two
  classes: (A) the MIGRATION-PHASE go-aheads (the 17 code fixes + the operator-gated data ops — decided in shape, gated
  on the operator saying "start"), and (B) the small open sub-decisions defaulted-with-a-flag. Plus any /plan-reconcile
  parked rulings appended as that sweep lands. Nothing here BLOCKS the shipped doc/SSOT work; it gates the code+data
  migration phase the operator sequenced AFTER the SSOT.
status: open
nature: process
asset_group: [defi, cefi, tradfi]
stage: [meta]
repos: [instruments-service, market-tick-data-service, unified-api-contracts, deployment-service, unified-trading-pm]
scope: [engineer, admin]
tags: [canonicalisation, open-questions, migration, operator-decision, close-out, spot-taxonomy, lending, pool-id]
related:
  [
    defi_consolidated_closeout_2026_07_18.md,
    cefi_consolidated_closeout_2026_07_18.md,
    tradfi_consolidated_closeout_2026_07_18.md,
    prediction_consolidated_closeout_2026_07_18.md,
    ../../codex/02-data/cross-asset-canonical-target-ssot.md,
  ]
created: 2026-07-18
last_updated: 2026-07-18
parent_epic: defi_master
priority: P1
assigned_vm: NA
execution_scope: local-only
resolved_by:
locked_by:
locked_since:
drift_direction: none
depends_on: []
source:
  Autonomous canonical-target close-out session (slot-4, 2026-07-18) — operator directed docs+SSOT first, migrations
  after; away 2h on /autonomous, so genuine decisions are parked here per AUTONOMOUS_AGENT_RULES rule 2.
---

# Canonical close-out — open questions + parked decisions (2026-07-18)

> **What shipped already (no decision needed — done):** the 4 consolidated close-out plans, the 75-finding contradiction
> audit, the **58 doc-contradiction fixes** across UAC/IS/MTDS/PM, and the **cross-asset canonical target SSOT**
> (`codex/02-data/cross-asset-canonical-target-ssot.md`). The operator's 4 live Q&A this session were ruled (purge
> dead-only+keep LIGHTER/EXTENDED · POOL 3-seg · combos leg-aware · ASTER per-symbol · BINANCE-DELIVERY keep-non-MVP).
> Everything below is the NEXT phase.

## A. Migration-phase go-aheads (decided in shape — gated on "start the migrations")

The operator sequenced code+data changes AFTER the SSOT. These are ready; each needs the go-ahead (some are irreversible
→ snapshot-first). Full detail in the four close-out plans' tracks.

- **A1 [P0, safe, unblocking] — the 7-lending-adapter silent-`[]` bug.** `euler_v2`/`venus`/`solend`/`radiant`/`benqi`/
  `marginfi`/`fluid` guard `if instrument_type not in (None, LENDING)` but mint A_TOKEN/DEBT_TOKEN → return zero
  instruments. Pure code fix (guard on `(None, A_TOKEN, DEBT_TOKEN)`, mirror `morpho.py:93`), no data change,
  QG-verifiable. **REC: authorize immediately — it's a live capture gap, not a design change.** (instruments-service)
- **A2 [P0] — POOL 3-segment glued-key convergence.** `unified-api-contracts/.../canonical/crosscutting/defi.py:313`
  emits 4-seg keys diverging from the MTDS 3-seg producer (data-join breakage). Code fix + a bounded reclass of the
  affected `canonical_instrument_id` values. (unified-api-contracts, then a data pass)
- **A3 [P1] — SPOT_PAIR reclassify + validator.** EIGEN/ETHFI→SPOT_ASSET, meteora/lifinity AMM→DEX_POOL, the
  `:SPOT:`/`:PERP:`/`:STAKE:` shorthand fixes, + a defi validator (SPOT_PAIR requires a two-token symbol). Code + a data
  reclass of the affected rows.
- **A4 [P1] — retire legacy LENDING** from `canonical_id_builder`, migrate the ~16.7M `lending` rows to
  A_TOKEN/DEBT_TOKEN, and bake the split into `build_instrument_catalogue.py` (kills the `--mode full` revert landmine).
- **A5 [P1, WRITE-VOLUME GATE] — the ~63.9M `expected_unattempted` seed.** Apply ONLY after purging the ~1.79M
  duplicate + ~219.5K phantom rows first. Operator write-volume gate. (market-tick-data-service)
- **A6 [P1, IRREVERSIBLE — snapshot-first] — GCS deletes**: the dead Shape-B `dex_pools/`+`lending_indices/` top-level
  prefixes; the culled-venue (DRIFT/PACIFICA/…) manifest+GCS data; the lending-indices legacy bucket (C0f). All
  snapshot-before-delete per the VM runbook. **REC: authorize as a batch with the pre-delete snapshot.**
- **A7 [P1] — restore the raw distinct-values data-status enumeration view** (deployment-api/ui) — the SSOT-alignment
  tool the operator asked for.
- **A8 [meta] — start order**: A1 (safe now) → A2/A4 (builder+data) → A3 → A5 (after purge) → A6 (snapshot-first) → A7.
  **QUESTION: authorize the migration phase to begin, and confirm the snapshot-first GCS-delete batch (A6)?**

## B. Small open sub-decisions (defaulted-with-a-flag — override if you disagree)

- **B1 — TradFi `etf`**: DEFAULT keep `etf` as a distinct canonical instrument_type (ETF ≠ equity; IBIT/ETHA are MVP
  crypto-ETFs); case-fold `ETF`→`etf`. Alt: fold ETF into `equity` (270,460 rows). [tradfi plan]
- **B2 — Combo top-level id**: the leg-aware spec says "no separate strategy field, infer from legs," but
  `build_combo_id` bakes the strategy name into the id (`CME:COMBO:SP500-BUTTERFLY-…`). DEFAULT: keep the strategy-named
  top-level id (legs carry the signed weights in the definition). Alt: leg-derived opaque top-level id. [tradfi plan]
- **B3 — DeFi bare `SUSHISWAP`/`UNISWAP` version** (199,397 rows, data doesn't record the version): DEFAULT derive the
  `_V{N}` per-pool from the factory/router contract address (an audit, not a guess); surface if underivable. [defi plan]
- **B4 — Legacy `barchart` tradfi rows** (4,655, retired vendor): DEFAULT drop them (vendor retired per CLAUDE.md). Alt:
  keep as historical. [tradfi plan]

## C. /plan-reconcile parked rulings (appended as the sweep lands)

- **C1 — archival of `gcs_hive_partition_malformed_paths_remediation_2026_06_01.md`** (terminal/superseded but
  `locked_by: live-defi-rollout`) — locked plans are never autonomous-archived; needs `[unlock-plan]`. **REC: unlock +
  archive** (it's superseded by the venue-before-chain canonicalisation).
- _(Further Phase-1 contradiction-sweep rulings + near-complete fold targets appended here.)_

## Progress Log

- **2026-07-18 (slot-4, /autonomous)** — Authored as the consolidated question list per the operator's "list all
  questions you have" + the /autonomous park-don't-block contract. A/B above are decided-in-shape; C fills from the
  running /plan-reconcile sweep (`wf_9458e3be`).
