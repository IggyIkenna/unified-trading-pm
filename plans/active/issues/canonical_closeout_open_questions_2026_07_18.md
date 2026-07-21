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

> **⚠ RESHAPED 2026-07-18 — DeFi migration is now PER-INSTRUMENT (R1–R4 in the DeFi close-out).** The operator directed
> DeFi to shard-write one parquet per instrument (flat pattern #1) instead of the capture-batch model; DeFi capture is
> STOPPED. The A-items below still apply but FOLD into R1–R4: A1 (lending-guard bug) → R1/R2; A2/A3/A4 (POOL 3-seg /
> SPOT_PAIR / retire-LENDING) → resolved BEFORE grouping in R1 + in the R3 union migration; A5 (63.9M seed) → R2's IS
> `available_from/to` denominator; A6 (GCS deletes) → still snapshot-first, now alongside the R3 batch→per-instrument
> rewrite. The batch-model dedup rationale for A5's purge dissolves (per-instrument overwrite). See
> `defi_consolidated_closeout_2026_07_18.md` § Per-instrument re-architecture.

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
- **A6 [P1, IRREVERSIBLE — snapshot-first] — GCS deletes**: ~~the dead Shape-B `dex_pools/`+`lending_indices/` top-level
  prefixes~~ **← WITHDRAWN, see correction below**; the culled-venue (DRIFT/PACIFICA/…) manifest+GCS data; the
  lending-indices legacy bucket (C0f). All snapshot-before-delete per the VM runbook. ~~**REC: authorize as a batch with
  the pre-delete snapshot.**~~ **REC WITHDRAWN for the Shape-B prefixes.**

  > **⛔ corrected 2026-07-20 — do NOT authorize the `dex_pools/`+`lending_indices/` prefix delete; it DESTROYS DATA.**
  > The "dead Shape-B" premise was **overturned by R5 in `defi_consolidated_closeout_2026_07_18.md:254-262`**, authored
  > AFTER this A6 item: content-verify found PARTIAL-OVERLAP, not duplication — legacy=98 pools, canon=99,
  > **intersection only 66**, with **32 legacy-only high-TVL raydium pools ABSENT from canon** ($47M XMR/USDC, $18M
  > BNB/USDC, …). A live GCS probe on 2026-07-20 confirms that for **KAMINO `dex_pool_state` and SOLEND** there is **no
  > canonical twin at all** — the legacy objects are the only copy. Snapshot-first is NOT sufficient protection here.
  > Additionally, `execution-service/execution_service/providers/solana_amm_depth_provider.py:41` **still READS this
  > legacy shape at runtime**. **This withdrawal also voids the A6 leg of the A8 start-order authorization question
  > below** — the other A6 legs (culled-venue data, the C0f legacy bucket) are unaffected and may still be authorized.
  > **Required order: (1) content-UNION into canon; (2) repoint execution-service to `data_type=dex_pool_state` and fix
  > its broken `resolve_bucket_name` call; (3) only then consider delete.** Full evidence + resolution criteria:
  > `defi_dex_pools_delete_order_stale_2026_07_20.md`.

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

### Phase-1 sweep results (31 contradictions + 10 done-but-unchecked; corpus mechanically GREEN, 0 hard failures)

**APPLIED this pass**: removed BINANCE-DELIVERY from the cefi plan's "Drop venues (remove entirely)" list (it was still
there in the CEFI CANONICAL SPEC section — contradicting the keep-non-MVP ruling + would delete real COIN-M data) →
moved to KEPT.

**C2 — OPERATOR RULINGS needed (4 still parked; C2a RULED 2026-07-20, D1)**:

- **C2a [P2] `instrument_type` COLUMN case — ✅ RULED 2026-07-20 (operator ruling D1): UPPERCASE column, catalogue
  wins.** ~~UPPER vs lowercase (⚠ affects the SSOT I just shipped). The cross-asset SSOT §7 + the defi plan say the
  manifest `instrument_type` COLUMN is lowercase; but tradfi + cefi ALREADY SHIPPED scripts that UPPERCASE the column
  (both citing "operator 2026-07-18"). REC: confirm UPPERCASE column (it shipped) → then correct SSOT §7 + the defi plan
  (codex edit = operator-gated).~~ Recorded in
  [`../data_pipeline_reconciliation_skill_2026_07_20.md`](../data_pipeline_reconciliation_skill_2026_07_20.md) §
  "OPERATOR DECISIONS — ALL THREE RULED 2026-07-20" (D1) and reflected by the tradfi plan's Phase-B "CASING FREEZE
  LIFTED 2026-07-20, D1" banner. The GCS path SEGMENT stays lowercase; the id middle segment stays UPPER; the manifest
  `instrument_type` COLUMN is now UPPERCASE. Codex §7/§11 correction already shipped (reconciliation-skill tick 20).
- **C2b [P1] cefi Track-2 reopen-50.79%** — `cefi_consolidated_closeout:119` autonomously RE-OPENED the archived
  completion program + REVERSED the operator's 50.79% coverage acceptance. Human-only governance; do NOT resume the
  backfill until explicit confirm/deny.
- **C2c [P1] DeFi expected_unattempted denominator** — `instruments_completion_tracker:242` marks it DONE (1.38M v1
  grain) + derives 62.06% coverage; the v2 SSOT (locked issue) says the real backlog is 63.9M, never applied →
  denominator understated. Edits a DONE-claim + live coverage on an operator-owned tracker + a locked issue. REC: add a
  correction note (1.38M = retired v1; v2 = 63.9M open → Track-3).
- **C2d [P2] GCS lifecycle codex** — `codex/05-infrastructure/gcs-lifecycle-policies.md` says "*-store NOT lifecycle'd"
  vs the operator 2026-07-13 STANDARD→COLDLINE@60d ruling (already provisioned on ml-store). Codex edit + confirm the
  exact ladder.
- **C2e [P2] sports_odds_bookmaker locked** — `status:active` + `locked_by: live-defi-rollout`, genuine open work (28
  unmapped league tiers). Needs `[unlock-plan]` to archive, OR confirm the follow-up migrated to sports_master.

**C3 — EPIC + May-23-critical-path narrative banners (parked — authority-gated; provable but epics/critical-path are not
autonomously edited)**: `defi_master.md:258/292/307` + `master_to_live_defi_2026_05_23.md:524/308` +
`master_data_canonicalisation_migration_catalogue:1972` still frame HYPERLIQUID/ASTER as DeFi perp DEXs; the SSOT §6 +
shipped code classify them **cefi CLOB** (GMX is the sole defi perp). REC: add a 2026-07-18 correction banner (matching
the existing `defi_master:260` pattern), NOT a blind find-replace.

**C4 — small auto-fixes VERIFIED-provable, ready to apply next pass** (deferred from this pass to avoid mass-editing
concurrently-edited plans in deep context): cefi Track-4 deribit_options_chain (:150) → repoint to Track-2 (the plan's
own :223 operator correction invalidates the "P0 writer-gate/reclass" framing; reconcile 112,727↔122,585); cefi headline
:10/:73/:98 "awaiting only drain+apply" → "+ Track-6 alignment"; defi Track-6 (:321) → repoint to the SHIPPED
`GET /api/data-status/axis-value-census` (deployment-ui@3fb6779), drop the new `/distinct-values` endpoint;
data_completion_to_100 (:416) "lease-mode" → N=1 Tardis cap; scratch_scenarios 13 (:9) drop "Drift"; tradfi A2 (:189)
"restoration" → "verify declaration = billing reality"; codex_alignment_deviations (:17) `assigned_vm` → NA;
bucket_estate (:11) ml count; strategy_master (:90) 53→59. **Checkbox flips (HARD evidence)**: tradfi:316
(deployment-api@09656f4 + ui@3fb6779), bucket_fold_ml:170 (UTL deserialize-gate), deployment_registry status table.

**C5 — archival-ready (verified superseded/complete + unlocked; execute next pass to avoid dangling-ref/orphan risk)**:
`defi_pool_id_chain_uniqueness_2026_07_18`, `instruments_service_docs_consolidation_2026_07_08`,
`execution_fidelity_tiers_uac_governed_2026_06_28`, + issues `slot6_git_reset_dataloss`, `drift_helius_path_obsolete`,
`drift_helius_perp_funding_shards…`, `instruments_service_bitfinex_futures_golden_drift`,
`drift_v2_sig_index_parts_cache_full_download`, `drift_v2_sig_index_program_wide_helius_oom`. **Migrate-then-archive**
(residual to a live issue first): `data_pipeline_e2e_check` (confirm next-steps tracked), `mtds_solana_drift_backfill…`
(migrate the fail-open gate-check class), `gcs_bucket_estate_cleanup` (migrate the lending-indices twin GCS-delete
residual).

**No-miss ledger**: 31 contradictions + 10 done-unchecked → **26 auto-fixable** (1 applied + 25 enumerated in C4/C5) +
**5 operator-rulings** (C2, +the SSOT §7 self-correction) parked here. routed_to_operator == parked. agent skips: 0. 4
items = scope/time/history (not findings — durability sweeps still running, foreign-tfvars-blocked flip).

## D — market/event lending DATA_TYPE canonical keying — ✅ RULED 2026-07-20 (was parked 2026-07-19)

> **⛔ RULED 2026-07-20, operator ruling D2 — this is no longer a parked/open decision.** ~~"NEW parked decision
> (2026-07-19)"~~. The operator ruled the **FULL retire** — market/event lending data_types adopt the A_TOKEN/DEBT_TOKEN
> split too (NOT the Option-A "keep `LENDING`" worker-rec interim). Recorded in
> [`../data_pipeline_reconciliation_skill_2026_07_20.md`](../data_pipeline_reconciliation_skill_2026_07_20.md) §
> "OPERATOR DECISIONS — ALL THREE RULED 2026-07-20" (D2). **It is the TARGET, NOT yet implemented** — the first attempt
> was reversed after breaking 5+ (really 8) MTDS lending writers, so the mandatory order is **fix the writers → migrate
> ~16.7M rows → re-sync the shard atom**, gated on
> [`../defi_lending_writer_retire_prerequisite_2026_07_20.md`](../defi_lending_writer_retire_prerequisite_2026_07_20.md).
> Until the migration lands, the uniform-`LENDING` interim holds and market/event flat `LENDING` is `migration_pending`
> (neither a fresh finding nor an open axis). The option-set below is HISTORY; Option A did NOT win.

**Context**: the DeFi close-out shipped the operator-ruled lending SSOT — aToken/debtToken as the canonical type for
lending **HOLDINGS** (IS adapters `@1af1be34`, all 7-adapter guards + the builder bake). Wave B then also retired flat
`InstrumentType.LENDING` in the UAC id-builder to `UNSUPPORTED_BY_DESIGN` (`@e319864f`). That over-reached: it made
`build_instrument_id(...LENDING...)` RAISE, which silently broke **5+ MTDS market/event lending writers**
(`lending_indices` for 6 EVM venues, `liquidation_events`, `flash_loan_events`, `position_data`, `solana_defi`) — each
caught by a shard-level `except ValueError` → `record_failed` → **attempted_failed, zero data** — and the partial
A_TOKEN work-around created a **shard-atom desync** (GCS `instrument_type=a_token` vs manifest `lending`). Reversed via
`wn12e7itc` (un-retire LENDING; keep POOL-3seg + SPOT-validator + GMX). Interim state = **uniform `LENDING` for
market/event lending data_types** (working, consistent); **holdings stay A_TOKEN/DEBT_TOKEN** (unaffected).

**THE DECISION (operator)**: how should the market/event lending DATA_TYPES — `lending_indices` (per-reserve supply +
borrow rate index), `liquidation_events`, `flash_loan_events`, `position_data` — be canonically keyed? These are NOT
per-token holdings; they are metrics/events about a lending market (which has an aToken supply side + a debtToken borrow
side).

- **Option A — keep `LENDING` as a market-level instrument_type** (current interim). Not the holdings-duplication the
  operator's ruling targeted (different grain). Simplest, no data re-key, historical rows unchanged. **[WORKER REC]** —
  least-bad, reversible, avoids a coarse/wrong per-side mapping across 4 heterogeneous data_types.
- **Option B — key each to the reserve's `A_TOKEN`** (aToken = reserve representative). Uniform with "A_TOKEN/DEBT_TOKEN
  only", but coarse: loses the debt side for `liquidation_events`/`position_data`/`flash_loan_events`, and forces a
  ~N-row historical re-key + a manifest shard-atom migration.
- **Option C — split per side** (supply-index/collateral → A_TOKEN; borrow-index/debt/flash-loan → DEBT_TOKEN). Most
  semantically precise, biggest change (row-shape + doubling for indices + historical re-key).

**If the operator picks B or C**: re-activate the UTL consumer #3 todo + a full MTDS writer migration (all 5+ writers,
NOT the partial 3) + a Wave-D historical re-key, and fix the shard-atom on both axes. If A: mark the UAC LENDING-retire
item holdings-only-done and drop the UTL/MTDS market-level migration.

## Progress Log

- **2026-07-19 (slot-4, /autonomous)** — Appended parked decision D (market/event lending data_type keying) after the
  Wave-B LENDING-retire was found to over-reach + break 5+ MTDS writers; reversed to the working interim, decision
  routed to the operator.
- **2026-07-18 (slot-4, /autonomous)** — Authored as the consolidated question list per the operator's "list all
  questions you have" + the /autonomous park-don't-block contract. A/B above are decided-in-shape; C fills from the
  running /plan-reconcile sweep (`wf_9458e3be`).
