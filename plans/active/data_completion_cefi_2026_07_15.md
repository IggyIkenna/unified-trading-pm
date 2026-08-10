---
doc_type: plan
title: Data completion to 100% — CeFi manifest canonicalisation + backfill (split from M-1)
summary: >-
  CeFi slice of the data-completion-to-100% program, split out of data_completion_to_100_all_ag_2026_06_21 (M-1) on
  2026-07-15 per operator ruling (plan-reconcile §8) when M-1 breached the absolute 5000-line ceiling. Carries the cefi
  scope M-1 absorbed in the 2026-07-13 consolidation, migrated VERBATIM — no scope added, dropped or reworded. M-1
  remains the coordinator hub for cross-cutting work (bucket naming, source provenance, bar-edge) and owns the shared
  Progress Log.
status: active
nature: process
asset_group: [cefi]
stage: [data]
repos: [instruments-service, market-tick-data-service, unified-api-contracts]
scope: [engineer, admin]
tags: [backfill, manifest, honest-coverage, data-completion, cefi, data-correctness]
related:
  [
    /plans/active/data_completion_to_100_all_ag_2026_06_21.md,
    /plans/archive/2026_08/data_completion_cefi_progress_log_history_2026_08_03.md,
  ]
created: 2026-07-15
parent_epic: manifest_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 2.5
estimate_calibrated_ai_days: 2
last_updated: 2026-08-03 # line-cap remediation split -- extracted 06-21/07-27/07-28 corroborating-audit Progress Log history to the archive doc above; context_scope backfilled
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
context_scope:
  [
    /codex/02-data/pipeline-mode-partition.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /plans/active/data_completion_to_100_all_ag_2026_06_21.md,
    market-tick-data-service/market_tick_data_service/scripts/rebuild_cefi_manifest.py,
    unified-trading-library/unified_trading_library/manifest_writer,
  ]
assigned_role: data_engineering
source: [data_completion_to_100_all_ag_2026_06_21 (M-1) — split 2026-07-15, plan-reconcile §8 operator ruling A]
drift_direction: advance-code
---

# Data completion to 100% — CeFi

> **Split from M-1 on 2026-07-15** (`data_completion_to_100_all_ag_2026_06_21.md`, plan-reconcile §8, operator ruling
> A). M-1 had reached 5,366 lines — the only file in the corpus over the absolute 5,000-line ceiling — after absorbing
> 130 folded-in todos in the 2026-07-13 consolidation. This plan carries M-1's **cefi** scope **verbatim**; M-1 stays
> the coordinator hub (measured snapshot, per-AG launch matrix, cross-cutting scope, shared Progress Log).
>
> **Read M-1 first** for the program-level snapshot + launch matrix. Cross-cutting items (bucket-name SSOT, data-source
> provenance, bar-edge) deliberately stayed there — they are not cefi-specific.

### From `cefi_manifest_canonicalisation_2026_06_01.md` (archived 2026-07-13 -- CeFi legacy gap-fill + manifest canonicalisation (single-walk, L3 owner for cefi))

- [x] ✅ [DATA] P0. **⑧ — IS cefi REFERENCE-UNIVERSE gap: catalogue not ⊇ manifest present-set (CF-14, falsely-high
      coverage). ALL 4 sub-parts VERIFIED CLOSED 2026-07-27.** Original finding (2026-06-08): IS
      `instruments-store-cefi-prd` listed only 12 venues vs MTDS manifest's 45, headline gaps KRAKEN-SPOT/FUTURES,
      BITFINEX-SPOT, PACIFICA-SOLANA, LIGHTER-ZKSYNC — root cause was `reference_data/adapters/cefi/tardis.py`'s
      hand-maintained `_DEFAULT_EXCHANGES` drifting below the canonical SSOT `VenueMapping.all_tardis_exchanges`. **(1)
      code fix**: SHIPPED `is@a6bc4d48` (unchanged from prior verification). **(2) operational backfill re-run —
      CONFIRMED DONE**: live `gcloud storage ls -r` on
      `gs://instruments-store-cefi-prd-central-element-323112/instrument_availability/by_date/` shows
      KRAKEN-SPOT/KRAKEN-FUTURES/BITFINEX-SPOT/BITFINEX-FUTURES/BITGET-SPOT/BITGET-FUTURES present as far back as
      `day=2021-06-01` and through the latest `day=2026-07-26` (22 venues total, up from 12). **(3) CLOB venues —
      CONFIRMED**: `instruments_service/reference_data/adapters/cefi/lighter.py` + `.../adapters/cefi/extended.py` now
      exist and LIGHTER-ZKSYNC + EXTENDED-STARKNET both appear in the live `day=2026-07-26` by_date listing;
      PACIFICA-SOLANA was removed from scope entirely by a later operator ruling
      (`instruments_service/engine/orchestrator/defi.py` comment: "all Solana perp DEXes dropped except Jupiter, not
      integrated", 2026-07-16 — see `/plans/archive/issues/solana_perp_dex_cull_drift_pacifica_2026_07_16.md` for the
      verbatim ruling + full purge record) so its CLOB-enumeration sub-part is now moot. **(4) ~650 UNKNOWN/blank-venue
      pollution rows — RESOLVED**: read `market-data-tick-cefi-prd`'s `_index/availability_index.parquet` directly
      (8,764,263 rows) — 0 blank-venue rows, 0 `UNKNOWN`-venue rows, 0 `*F0`-suffixed instrument_ids today (was ~650).
      Corroborating evidence: the first-ever complete `cf_manifest_audit.py` rollup
      (`plans/active/issues/cf_manifest_audit_first_full_rollup_findings_2026_07_26.md`, 2026-07-26) reports
      `instruments-store-cefi-prd` as CF-14 **"(clean)"**. Gates honest coverage denominator (⑦/⑧); does not touch the
      G4 data/manifest `--apply`. **NEW, separate, minor finding surfaced during this verification** (NOT part of this
      item — filed as its own follow-up, see `cefi_coinbase_futures_blank_instrument_type_2026_07_27.md`): 354
      `market-data-tick-cefi-prd` rows on `date=2026-07-25` for venue `COINBASE-FUTURES` carry a null `instrument_type`
      despite well-formed `instrument_id`s (301 `empty_confirmed` + 53 `attempted_failed`) — a distinct, single-day
      writer gap, not the venue-pollution class this item tracked. Provenance: slot-3 pre-apply audit 2026-06-08
      (original finding); slot-4 live-verification 2026-07-27 (this closure). **(MIGRATED FROM:
      `cefi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [x] ✅ [CODE] P1. **DONE 2026-07-27 (slot-15)** — **execution-service — `data/loaders/defi.py:41,77` DeFi raw-tick
      reads still legacy.** Found `data/loaders/defi.py`'s `DeFiDataLoader._defi_read_candidates` ALREADY has the chain
      kwarg + derivation (already shipped by someone else before this dispatch) — the genuinely-unfixed gap was the
      SEPARATE legacy `UCSDataLoader` in `data/loader.py` (still reachable: `engine/backtest/data_loader.py:386`
      instantiates it with `domain="defi"`), whose `_build_swaps_paths`/`load_swaps` never got the canonical-first +
      chain-axis treatment at all. Fixed both `_build_swaps_paths` AND the identical adjacent bug in
      `_build_liquidity_paths` (same file, same root cause) by mirroring `DeFiDataLoader._defi_read_candidates` exactly:
      derive chain via `to_canonical_venue`, route through `build_candidate_raw_tick_paths` (`canonical_paths` SSOT),
      legacy path appended as fallback. 2 new regression tests pin the chain derivation + confirm the canonical builder
      is called (not silently skipped) even with no derivable venue. `quality-gates.sh` green (204s, 2nd attempt — 1st
      was silently killed mid-run by the same shared-host RAM contention tracked in
      `issues/shared_host_ram_exhaustion_kills_background_qg_2026_07_27.md`, but its 7888/7888 test pass before the kill
      already confirmed the fix correct). Shipped: `execution-service@0788b1f0`.

**🟡 P1 — pre-flight engrained (blocking the "pre-flight on every service" bar):** **(MIGRATED FROM:
`cefi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [x] ✅ [DATA] P3. **market-data-processing-service** — leading-NaN before first observation — CLOSED 2026-08-05
      (slot-8, data_engineering). The underlying issue (`issues/mdps_state_adapter_leading_nan_audit_2026_05_29.md`) is
      **resolved** (2026-06-09): Decisions 1+2 code shipped `MDPS@5a5e989`/`@4fd962d`/`@23d7add`/`@56202b0`
      (2026-06-02). All 7 originally-missing state adapters now route through `_finalize_session_grid` with appropriate
      `state_col` (futures_chain→close, options_chain→mark_price, book_snapshot→mid_price, tbbo→mid_price,
      liquidity/market_state→close-driven), except `derivative_adapter` which intentionally does NOT route
      (honest-absence contract — `supports_prior_day_seed=False` per its module docstring). The prior-day carry-seed
      mechanism (`_resolve_seed_args` / `CandleWriteMixin._read_prior_day_frame`) is wired and all 10 finalizer-routed
      adapters declare `supports_prior_day_seed=True`. The residual `[DATA] P1` historical densify reprocess is tracked
      in `mtds_mdps_master.md` Phase 11; the `[SCRIPT] P3` deployment-service fix is deferred. Verified this session:
      live code-read of all 12 adapters — no code change needed. **(MIGRATED 2026-07-13.)**

- [x] [INFRA] P3. **2026-07-28 close-out**: no live BLOCKED-OPERATOR-DECISION remains — the successor plan cited below
      (`plans/archive/2026_06/proper_instrument_catalogue_lifecycle_rollup_2026_06_04.md`, `status: complete`) shipped
      Phase 3 ("all-AG adoption + enumerator unblock"), which the plan's own text states unblocks "the cefi Dim-7 P3
      enumerator-cron … now points at a self-refreshing catalogue." Checked off per that verified completion; the
      remaining prerequisite this item was blocked on no longer exists. **`expected_unattempted` is
      enumerator-run-dependent (not auto per-write) — was BLOCKED-OPERATOR-DECISION on a missing prerequisite (slot-3
      2026-06-04).** A not-yet-backfilled cefi cell is invisible until the v2 enumerator VM runs
      (`launch-expected-universe-v2-vm.sh cefi --apply-write`; cadence "one-shot then quarterly"). cefi is currently
      seeded (4.1M rows) but NEW venues/instruments between runs are invisible (`honest_coverage.py:623` warns a fresh
      AG reads a misleading 100%). **Why a naive recurring cron is NOT shippable:** the v2 enumerator REQUIRES
      `--catalog-path` = a pre-built IS catalog parquet
      (`gs://instruments-store-cefi-{env_short}-{project}/{env}/catalog.parquet`; the launcher defaults to it,
      `enumerate_expected_universe.py:1410` hard-fails `missing_catalog_path` without it). **NO automated/recurring
      producer of that `catalog.parquet` exists** (workspace grep 2026-06-04: only the launcher + its test reference the
      path; nothing writes it) — it is operator-supplied. So a recurring enumerator scheduler would read a stale/absent
      catalog (fire-and-forget failure, banned). A correct fix needs a PREREQUISITE: either (a) add a recurring
      catalog-build step that writes `{env}/catalog.parquet` from the IS store, or (b) refactor the v2 enumerator to
      build its catalog from the IS availability index at runtime (the exact `read_availability_index`→`{venue:[ids]}`
      pattern deployment-api now uses in `_build_cefi_is_instruments_provider`, eliminating the `--catalog-path`
      dependency). A drafted `expected_universe_cefi_scheduler.tf` (Cloud Run Job + weekly Scheduler, env-tiered buckets
      per `manifest_consolidator_scheduler.tf`) was NOT committed pending this decision. **RESOLVED 2026-06-04 →
      SUPERSEDED-BY `plans/active/proper_instrument_catalogue_lifecycle_rollup_2026_06_04.md`** (operator decision: the
      real fix is a proper, self-refreshing instrument catalogue rolled up from the per-date `by_date/` definitions —
      foundation-level, all asset groups, gates the MTDS migration `--apply`). This cefi cron becomes a thin wrapper
      once that plan's Phase 3 lands; tracked there, no longer a cefi-solo item. **(MIGRATED FROM:
      `cefi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [x] ✅ [CODE] P3. **deployment-api per-date denominator refinement (separate follow-up, NOT migration-blocking).** The
      cefi coverage denominator (deployment-api@d55bcb6) reads ONE current IS availability snapshot
      (`read_availability_index`), not the per-date `instrument_availability/by_date/` definitions — so it is the
      latest-known universe, NOT per-date point-in-time-correct (the universe as-of each historical date). **SHIPPED
      2026-08-05 (slot-13, data_engineering):** replaced `read_availability_index` (single current snapshot) with venue
      parsing from the per-date catalog (`prod/catalog.parquet`, via `_read_cefi_catalogue_metadata`). Venue is parsed
      from the canonical `instrument_id` (`VENUE:TYPE:SYMBOL`). The catalog carries `available_from`/ `available_to` per
      instrument — the cumulative roll-up of `instrument_availability/by_date/` definitions — making it the per-date
      SSOT. `deployment-api@5ef110f`.

**VERDICT:** ⑥ **PARTIAL** — IS-derived per-date capture + UAC combo gate + execution preflight are real + date-correct;
the residual holes (date-blind MTDS fallback un-caught by its QG, no strategy IS-existence check, swallowed Deribit live
guard, permissive unknown-venue) are tracked above. ⑦ **STRONG** — the could-exist universe drives
`expected_unattempted` (run for cefi, 4.1M rows) + the canonical denominator includes it + the UI shows it distinctly;
residual is the in-process MVP-seed denominator under-count + the enumerator cadence (both tracked).

**UAC/UTL helpers (the absence "explainer"):** `build_cefi_partition_path` / `candidate_parquet_paths`
(`canonical/partition_paths.py:392`) are the path SSOT; the `empty_confirmed` closed-set taxonomy lives in
`canonical/crosscutting/honest_coverage.py` (the `EXPECTED_NO_*` / `SOURCE_RETURNED_ZERO` reasons features uses). The
candle-level zero-volume/LOCF/NaN contract is documented in MDPS `base_adapter.py:36-624` (`_finalize_session_grid`) —
**this MDPS docstring is the de-facto SSOT for the candle-absence semantics; the P0/P1 downstream fixes must consume it
(distinguish volume=0 vs NaN vs forward-filled), not re-derive.**

**✅ GREEN (verified consistent — do not touch):**

- **Path correctness**: migration, live+batch writers, MTDS reader, features reader, `rebuild_cefi_manifest.py` ALL go
  through the UAC `candidate_parquet_paths()` SSOT and insert `pipeline_mode=` left of `asset_group=cefi`;
  reader-fallback probes both shapes until ~06-15 (PREP3 writer pipeline_mode= PRIMARY landed mtds@f50116ca). The path
  the migration reads/writes == the writers'/readers'/preflight's path.
- **Data-status infra**: deployment-api reads canonical `market-data-tick-cefi-prd` via `resolve_bucket_name`, uses UTL
  `read_availability_index` (v9 columns), renders 4-state status, derives drilldown axis order from the UAC registry.

**🔴 P0 — E2E-blocking code (OPERATOR-APPROVED to do THIS session before the dry-run):** **(MIGRATED FROM:
`cefi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [x] ✅ [CODE] P1. **deployment-api FLAG-3 — RESOLVED/NO-ACTION (main ruling 2026-07-28).** RE-SCOPED (slot-3
      evaluation 2026-06-05): NOT a mechanical f-string→`resolve_bucket_name` swap; a blind swap would BREAK working
      code. The `commentary/pipeline_uat.py` reads (`instruments-store-{pid}/instruments/latest/manifest.json`,
      `features-store-{pid}/health/latest.json`, `ml-store-{pid}/training/latest/metrics.json`,
      `execution-store-{pid}/t1_recon/latest/summary.json`) are NON-AG **pipeline-health summary** buckets carrying
      `# CORRECT-LOCAL` markers (a deliberate QG STEP-5.69 allowlist), NOT the AG-scoped market-data stores. The
      canonical `resolve_bucket_name(kind="instruments-store", asset_group=…)` everywhere else resolves a PER-AG bucket
      (`instruments-store-cefi-…`) with a different path shape — there is no single non-AG `instruments-store-{pid}` in
      that registry, so swapping these would point the health reads at wrong/nonexistent buckets (they already
      `try/except`→None-degrade gracefully today). **Main's ruling on the model-decision this item asked for**: keep the
      aggregate non-AG `# CORRECT-LOCAL` summary-bucket form AS-IS — these are deliberately system-wide pipeline-health
      summaries, not AG-scoped market-data stores (grounded in this plan's own 2026-06-05 re-scope at line 154 above);
      migrating them to per-AG buckets would be an unjustified cross-service bucket-contract change with no correctness
      gap, not a bug fix. No code change. `deployment_api_config.py` store buckets already use typed `effective_*`
      config (FLAG-3-compliant) — that part was already done. Cross-ref downstream plan FLAG-3. **(MIGRATED FROM:
      `cefi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [x] ✅ [CODE] P1. **deployment-api CeFi pipeline_mode dedup + drilldown filter — VERIFIED ALREADY SHIPPED 2026-07-28
      (slot-16).** Both remaining sub-parts from the 2026-06-03 read-only confirmation were found already landed by
      prior, unrelated commits — no new code required, verified live: **(a) cefi parity test** —
      `tests/unit/test_venue_breakdown_shards_cefi_dedup.py` (`deployment-api@51890b3`, 2026-07-26) mirrors
      `test_pipeline_mode_rows_do_not_double_count_shards` for cefi: 2 instruments × 5 dates × 2 pipeline_modes = 20 raw
      rows must collapse to 10 distinct `(instrument_id, date)` shard atoms via `_per_instrument_coverage`'s set-based
      numerator (`found_pairs`) — the cefi shard-atom dedup is structurally immune to the DeFi builder's raw-`len()` bug
      by construction (no `drop_duplicates` fix needed there), and this test is the regression guard proving it. **(b)
      `pipeline_mode` drilldown filter param** — already fully wired end-to-end:
      `GET     /api/data-status/drilldown/{service}/{asset_group}` accepts `pipeline_mode: str | None` Query
      (`deployment_api/routes/data_status/_deploy_turbo.py`, shipped `deployment-api@4dd2575` "v9 manifest UNION read
      path + pipeline_mode/source drilldown (G3/M5)") and `GET /api/data-status/turbo` accepts
      `pipeline_mode: list[str]     | None` (OR-semantics, shipped `deployment-api@0ae5230` "add pipeline_mode filter to
      /turbo endpoint"); the TS client (`deployment-ui/src/api/client.ts` `_DRILLDOWN_FILTER_KEYS`) already threads
      `pipeline_mode` through. Re-ran both regression suites live 2026-07-28:
      `test_venue_breakdown_shards_cefi_dedup.py` + `test_chain_breakdown_shards_vs_dates.py` = 5/5 passed;
      `test_data_status_hierarchical.py` + `test_data_status_drilldown_provenance.py` = 69/69 passed. No dirty tree, no
      new commit needed. **Residual, NOT part of this item** (noted for a future UI todo, not blocking):
      `HierarchicalShardDrilldown.tsx` renders `pipeline_mode` as a display-only per-cell badge — there is no
      operator-facing filter dropdown wired to the already-existing API param, so the "UI label is playwright-gated"
      clause never triggered (no new UI surface was added). (MIGRATED FROM:
      `cefi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)

**⚪ P2 / needs-confirm (tracked):** **(MIGRATED FROM: `cefi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per
MTDS consolidation ruling.)**

- [x] ✅ [DATA] P2. **CONFIRM partial-BUNDLE completeness guard — FULLY CONFIRMED 2026-08-05 (slot-6,
      data_engineering).** **(a) Per-cluster check, not aggregate**: `check_cluster_coverage_from_counts`
      (`unified-trading-library/manifest_writer/_writer_validation.py:288-324`) iterates over EVERY key in
      `expected_root_clusters` and checks `observed_clean.get(cluster, 0) < min_rows` — a cluster entirely absent from
      `observed` gets 0 and FAILS. The `≥` is per-cluster minimum, NOT an aggregate total. A partial bundle meeting
      total count but missing a cluster root (e.g. `expected={A:1,B:1,C:1}`, `observed={A:3}`) is correctly rejected
      (B=0<1 fails, C=0<1 fails). The earlier theoretical worry is **unfounded** — the gate is precise. **(b) MTDS
      finalize path** (`manifest_finalize.py:179-283`): `options_chain` (CME-OPTIONS) uses real IS-derived
      cluster_expected; `futures_chain` uses `FUTURES_CHAIN_BUCKETS`; `book_snapshot`/other bundled types have
      `cluster_expected={}` (intentional no-op — no meaningful cluster concept for those data_types, validated at
      per-instrument level instead). **(c) No code change needed** — the guard is present, per-cluster-precise, and
      correctly scoped to the data_types that have cluster semantics. Repo: UTL/MTDS — read-only confirmation.
      **(MIGRATED FROM: `cefi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [x] ✅ [DATA] P1. **Before the REAL `_index` rebuild — multi-year dry-run phantom spot-check — RE-RUN 2026-07-28
      (slot-12), GATE FAILED — real finding, NOT a clean pass.** Ran `rebuild_cefi_manifest --dry-run` over the FULL
      corpus (`--start-date 2019-01-01 --end-date 2026-07-28`, `GCP_PROJECT_ID=central-element-323112` exported — the
      CF-11 pass silently no-ops without it, a first attempt without the env var falsely read "prior _index is
      empty/missing"). `unparseable=0` ✅ and `dropped_malformed_captured=25,413` (~0.45% of the 5,677,228-row prior
      index, junk-only per its predicate) ✅ — but **`phantom_to_failed=490,639` (~8.6% of the entire prior index) FAILS
      the "stays small + DERIBIT-chain-style only" criterion** — per-venue spread is broad (OKX-FUTURES, HYPERLIQUID,
      ASTER, BYBIT-SPOT, OKX-SWAP, BINANCE-FUTURES, COINBASE-FUTURES, BITFINEX-FUTURES, BITGET-FUTURES, KRAKEN-FUTURES
      all show large counts; DERIBIT is a small minority of the total, not the dominant class). **Root cause CONFIRMED
      live** (3 independent GCS spot-checks, 100% false-phantom hit rate — not real absences): the CF-11 covered-keys
      dedup compares the prior manifest's stored `instrument_type`/`underlying` COLUMNS against the live object scan's
      parsed path, and multiple venues' actual GCS folder structure (`instrument_type=perpetual` for OKX-FUTURES dated
      futures / BYBIT-SPOT spot pairs; blank `underlying` for ASTER per-instrument shards) no longer matches what the
      prior manifest recorded historically — the object is genuinely present, but the exact-tuple key match fails, so
      it's falsely reclassified `PHANTOM_CAPTURED_NO_OBJECT`. Same bug class as the already-fixed `spot`→`spot_pair`
      synonym (2026-06-11) and the slash-symbol stem fix (2026-06-04), but NOT covered by either. Full evidence + root
      cause + recommended fix + follow-up todos:
      `plans/archive/issues/cefi_rebuild_false_phantom_itype_underlying_drift_2026_07_28.md`. **This BLOCKS the "NEXT
      SESSION — execute the migration" P0 todo immediately below** — see its updated note. **(MIGRATED FROM:
      `cefi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

> **Hard-stop review, 2026-07-28 (operator gated-decision closeout pass).** The `[OPERATOR]`-tagged todos below (E4
> orphan-sweep + gap-fill, its bucket-state-evidence sibling, the `source`/`pipeline_mode` riders, E7-Verify, Post-walk)
> all supersede into the phased execution plan
> `plans/active/cefi_e4_e8_orphan_sweep_gapfill_rebuild_execution_2026_07_28.md` — their actual delete/write actions are
> gated THERE (Phases B/F), not in this file. That plan's irreversible-delete phases were reviewed and **confirmed to
> remain a permanent human-only hard-stop** (delete-safety-protocol hard-stop #2) — not retagged, not unlocked; see that
> plan for the full ruling note. This file's own `[OPERATOR]` tags stay as-is (they are backlog-regen anti-thrash retags
> pointing at the successor plan, not a separate delete gate).

- [x] ✅ [DECISION] P0. **Retagged 2026-07-29 (corpus hygiene pass): resolved-by-reference — see
      `plans/active/cefi_e4_e8_orphan_sweep_gapfill_rebuild_execution_2026_07_28.md`'s "Operator ruling, 2026-07-29"
      (Phase A/B) — operator has now ruled on this todo's full scope there (Phase A dispatchable; Phase B authorized
      pending human execution); retagging the stale gate placeholder, not claiming `--apply` ran.** **RETAGGED
      [DATA]→[OPERATOR] 2026-07-28 (slot-9)**: this todo's own action is now entirely contained in the
      `[OPERATOR]`-tagged phases of its successor plan (see SUPERSEDED-BY below) — retagging so the backlog regen
      classifies it `operator_gated` (never dispatched to a worker) instead of redispatching this
      already-resolved-non-actionable item to yet another `data_engineering` session (3 prior sessions — slot-14
      2026-07-27, slot-4 and slot-12 2026-07-28 — already independently reached "do not execute" here; this session,
      slot-9, was the 4th dispatch of the same dead end). **SUPERSEDED-BY
      `plans/active/cefi_e4_e8_orphan_sweep_gapfill_rebuild_execution_2026_07_28.md` (2026-07-28, slot-4, main ruling
      BLK-650261be) — checkbox left UNCHECKED, no sweep has run.** **NEXT SESSION — execute the migration** (after the
      dry-run validates perf) — **🔴 BLOCKED 2026-07-28 (slot-12): the dry-run did NOT validate cleanly** —
      `phantom_to_failed=490,639` (~8.6% of the prior index) is a confirmed false-phantom bug (itype/underlying column
      drift), not real orphans; see
      `plans/archive/issues/cefi_rebuild_false_phantom_itype_underlying_drift_2026_07_28.md`. Running this todo's
      `--apply` migration as-is would `record_failed` ~490K genuinely-present rows for real — do NOT run until that
      issue's fix lands + a clean re-run confirms `phantom_to_failed` drops to a small DERIBIT-chain-style residual.

      **✅ 2026-07-28 (slot-2) — the blocking issue is RESOLVED**: 4 confirmed root causes fixed
                                                                                                                                                                                                                                                                                                                                                                                                                                              (market-tick-data-service@dcbed674, @42a2fd9f, @9a2927ad, @9c19c48b) across 4 full-corpus dry-run iterations;
                                                                                                                                                                                                                                                                                                                                                                                                                                              `phantom_to_failed` 490,639 (8.6%) → 17,255 (0.3%), DERIBIT now the single largest venue (32.4%) with every
                                                                                                                                                                                                                                                                                                                                                                                                                                              other significant residual individually diagnosed as non-bug (see the issue doc's final todo for full
                                                                                                                                                                                                                                                                                                                                                                                                                                              evidence). This todo stays checkbox-unchecked per its own retag rationale above (dead/superseded, never
                                                                                                                                                                                                                                                                                                                                                                                                                                              dispatched from HERE) — the actual `--apply` execution is Phase D of the successor plan
                                                                                                                                                                                                                                                                                                                                                                                                                                              (`cefi_e4_e8_orphan_sweep_gapfill_rebuild_execution_2026_07_28.md`), now marked ready-to-dispatch there.
                                                                                                                                                                                                                                                                                                                                                                                                                                              Original scope once unblocked: run the 8 year-sharded `--also-legacy --apply` gap-fill (5,233 legacy-only cells),
                                                                                                                                                                                                                                                                                                                                                                                                                                              then the irreversible orphan-sweep (with the mandatory pre-delete idempotent-`--apply`-over-full-range guarantee),
                                                                                                                                                                                                                                                                                                                                                                                                                                              then E5 manifest rebuild (now CF-11-canonical + false-phantom-safe @mtds#fa2b02c7+this-fix), E7 verify, E8
                                                                                                                                                                                                                                                                                                                                                                                                                                              legacy-bucket delete. NOT this session (irreversible) — this exact reasoning is why the successor plan phases the
                                                                                                                                                                                                                                                                                                                                                                                                                                              chain instead of bundling it into one dispatch. **(MIGRATED FROM: `cefi_manifest_canonicalisation_2026_06_01.md`,
                                                                                                                                                                                                                                                                                                                                                                                                                                              2026-07-13 per MTDS consolidation ruling.)**

- [x] ✅ [DATA] P0. C-pipeline_mode RIDER (folded into C0 (d)): the `pipeline_mode=` partition lands in THIS walk
      (satisfies `pipeline_mode_partition_migration` for cefi) — **VERIFIED ALREADY SHIPPED 2026-07-28 (slot-10), +
      regression coverage added.** `rebuild_cefi_manifest.py`'s object-scan walk (`scan_and_rebuild`) has stamped
      `pipeline_mode` on every emitted row since utl@b872bdf1 / PREP2-E5 (2026-06-02, code comments confirm): the
      `_PM_RE` regex captures the canonical `pipeline_mode=` path segment when present
      (`rebuild_cefi_manifest.py:179-182`), and for legacy pre-migration objects with no such segment the walk falls
      back to `derive_pipeline_mode_for_row` (same derivation the live writer + migrator use) rather than stamping blank
      (`rebuild_cefi_manifest.py:442-461`). `ManifestWriter.add()` has persisted `pipeline_mode` since utl@b872bdf1
      (`unified_trading_library/manifest_writer/_writer_ingest.py:148`). Path-parsing was already unit-tested
      (`tests/unit/scripts/test_rebuild_cefi_manifest.py`), but the `scan_and_rebuild`-level stamping (both the
      from-path and derive-fallback branches) had NO regression coverage — added
      `test_scan_and_rebuild_stamps_pipeline_mode_from_canonical_path_segment` +
      `test_scan_and_rebuild_derives_pipeline_mode_for_legacy_path_without_segment` to
      `tests/unit/test_rebuild_cefi_manifest_cf11.py`, both green, full `quality-gates.sh` green (7265 passed / 17
      skipped). This confirms the rebuild-walk CODE is ready for when the actual migration runs (still gated on the
      separate, blocked "NEXT SESSION — execute the migration" P0 todo above — the false-phantom bug at
      `plans/archive/issues/cefi_rebuild_false_phantom_itype_underlying_drift_2026_07_28.md`); no code change was needed
      for this rider itself. `market-tick-data-service@cf8a6817`. **(MIGRATED FROM:
      `cefi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [x] ✅ [DECISION] P1. **Retagged 2026-07-29 (corpus hygiene pass): resolved-by-reference — see
      `plans/active/cefi_e4_e8_orphan_sweep_gapfill_rebuild_execution_2026_07_28.md`'s Phase D (E5 rebuild), which this
      `source`-column rider rides along with. Reconciliation note (not a new operator question)**: the retag rationale
      below calls Phase D "human-execution-only" — the successor plan's CURRENT text tags Phase D `[DATA] P0`, "ready to
      dispatch" (unblocked 2026-07-28), NOT `[OPERATOR]` — only Phase B (the delete) carries that hard-stop. That one
      point is stale; the resolved-by-reference verdict itself is unaffected. **RETAGGED [DATA]→[OPERATOR] 2026-07-28
      (slot-12)**: same reclassification as its 5 sibling cefi todos in this file (3 E4-E8 todos retagged by slot-9,
      Post-walk + E7-Verify retagged by slot-13, all same day) — deterministically blocked on the successor plan's Phase
      D `--apply` rebuild (human-execution-only, delete-safety-protocol hard-stop class; see the Post-walk todo's retag
      note below for full rationale). This rider's `source` stamping only lands once that walk actually executes.
      Confirmed still-blocked this session via main's own ruling (do-not-flip-on-RED,
      `data_completion_cefi_2026_07_15.md:272`) + this session's evidence commits (`b87980d15`, `ce4af5f15`) — see
      `/plans/archive/2026_07/issues/ao_done_gate_no_carveout_for_red_gate_evidence_only_closure_2026_07_28.md` for the
      `/done`-gate gap this evidence-only closure hit. Retagging so backlog regen classifies this `operator_gated`
      instead of re-dispatching an unwinnable re-run to another `data_engineering` worker. **SUPERSEDED-BY
      `plans/active/cefi_e4_e8_orphan_sweep_gapfill_rebuild_execution_2026_07_28.md` Phase E (2026-07-28)** — checkbox
      left UNCHECKED, the audit has not gone GREEN. C-source RIDER (folded into C0 (b)): the `source` column (`tardis`,
      swap-resilient) lands in THIS walk (closes `data_source_provenance` cefi). **(MIGRATED FROM:
      `cefi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [x] ✅ [DECISION] P0. **Retagged 2026-07-29 (corpus hygiene pass): resolved-by-reference — see
      `plans/active/cefi_e4_e8_orphan_sweep_gapfill_rebuild_execution_2026_07_28.md` Phase D/E.** The decision to
      proceed once the audit reads GREEN is already made and tracked there (Phase E: "flip ... once GREEN, citing this
      plan's evidence"); only that OPERATOR gate placeholder in THIS file is being retagged. **The underlying audit
      result itself is untouched and stays RED** — per the data-pipeline-correctness HARD RULE this is not a claim the
      audit passed, only that the gate-routing decision for this dead placeholder is settled. **RETAGGED
      [DATA]→[OPERATOR] 2026-07-28 (slot-13)**: same reclassification as its E7-Verify sibling immediately below and the
      3 E4-E8 todos above — deterministically blocked on Phase D's `--apply` rebuild (human-execution-only, see the
      E7-Verify todo's retag note for full rationale). **SUPERSEDED-BY
      `plans/active/cefi_e4_e8_orphan_sweep_gapfill_rebuild_execution_2026_07_28.md` Phase E (2026-07-28) — checkbox
      left UNCHECKED, the audit has not gone GREEN.** **🔴 BLOCKED 2026-07-28 (slot-8, confirmed by main) — real
      predecessor is `plans/archive/issues/cefi_rebuild_false_phantom_itype_underlying_drift_2026_07_28.md`, not this
      todo's own action.** Post-walk: re-read the canonical `_index` DATA-STATE (re-run the reusable audit tool) →
      **100% of rows v9** (was 100% v8); **`source` populated on every cell** (zero blank; `tardis`, swap-resilient);
      **`asset_group` column/key present** (no `category`/blank); **`pipeline_mode` non-blank + partition present**;
      typed reasons; **legacy-only CELLS = 0** (838-gap closed). Closes `data_source_provenance` cefi +
      `pipeline_mode_partition` cefi. C-GREEN signal for `bucket_name_ssot…` Phase 6/7 cefi legacy bucket decommission —
      **this is a GATE, do not flip it on a RED audit (data-pipeline-correctness HARD RULE +
      foundation-completion-gate).** **RE-RUN 2026-07-28 (slot-8, live, `mode=changed`, no `--apply`) — STILL RED,
      criteria NOT met**: v9=97.4% (not 100%), source blank=24.0% (not 0%), pipeline_mode blank=1.4% (not 0%), Era-B
      chain-dtype rows=490,332 (not 0) — expected, since the underlying walk this todo is post- has not executed yet and
      remains blocked on the false-phantom itype/ underlying-drift fix (see the 2026-07-28 slot-12 entry above + the
      issue doc linked at the top of this item). **Do not flip until the walk executes AND a fresh audit reads GREEN on
      all four criteria** (v9=100% / source blank=0% / pipeline_mode blank=0% / Era-B chain rows=0). See the 2026-07-28
      (slot-8) Progress Log entry for the full per-CF readout. **(MIGRATED FROM:
      `cefi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

      **2026-07-28 (slot-12) re-check**: still correctly BLOCKED — the predecessor issue doc's re-diagnosis re-run
                                                                                                                                                                                                                                                                                                                                                                                                                                                  (on the now-gated `market-tick-data-service@42a2fd9f`) was already running concurrently in slot-2 and slot-15
                                                                                                                                                                                                                                                                                                                                                                                                                                                  when this session picked up this todo; a redundant 3rd copy this session had launched was killed before
                                                                                                                                                                                                                                                                                                                                                                                                                                                  completion to avoid a third full-corpus GCS scan. See the issue doc's 2026-07-28 (slot-12) addendum for detail.
                                                                                                                                                                                                                                                                                                                                                                                                                                                  No checkbox flip — criteria still unmet pending that re-run's result.

- [x] ✅ [DECISION] P0. **Retagged 2026-07-29 (corpus hygiene pass): resolved-by-reference — see
      `plans/active/cefi_e4_e8_orphan_sweep_gapfill_rebuild_execution_2026_07_28.md` Phase B, which explicitly states
      "Absorbs the measured-evidence content of the former `data_completion_cefi_2026_07_15.md` 'Orphan sweep +
      bucket-state evidence' todo (`data_completion_cefi-013`)."** This todo IS that absorbed evidence — it is a
      verbatim duplicate now carried in Phase B's own todo text, so the gate placeholder here is retagged rather than
      re-dispatched. **RETAGGED [DATA]→[OPERATOR] 2026-07-28 (slot-9)**: same reclassification as its sibling todo above
      — the action lives entirely in the successor plan's `[OPERATOR]` phases, so this retag stops the backlog regen
      from redispatching an already-superseded, non-actionable item to a `data_engineering` worker. **SUPERSEDED-BY
      `plans/active/cefi_e4_e8_orphan_sweep_gapfill_rebuild_execution_2026_07_28.md` (2026-07-28, slot-4, main ruling
      BLK-650261be) — checkbox left UNCHECKED, this measured evidence is folded into that plan's Phase B.** **Orphan
      sweep + bucket-state evidence (slot/Harsh bucket-state verification 2026-06-02).** Measured (Cloud Monitoring
      `storage/v2/total_count`, live-object): `market-data-tick-cefi-prd` 1,545,850 (~65% of legacy 2,377,168) and **~17
      days STALE — `-prd` latest `day=2026-05-07` vs legacy `day=2026-05-24`** (consistent with the 5,233 legacy-only
      cells; the C0 gap-fill closes it by reading legacy as source). `-prd` is INTERMEDIATE FORM: `asset_group=cefi` is
      in the PATH but there is **NO `pipeline_mode=` partition** (confirmed at the data level, not just the manifest).
      So the E4 walk writes NEW `pipeline_mode=` paths → the pre-existing legacy-FORM `-prd` objects become ORPHANS; E5
      rebuild / E7 verify MUST delete the legacy-FORM `-prd` objects too (not only the legacy SOURCE bucket), else the
      rebuild double-counts. Legacy carries 3.81M noncurrent objects → the E8 delete must also purge noncurrent
      versions, and the "canonical ≥ legacy" count gate must use Monitoring `type=live-object` (never a naive recursive
      `ls`, which counts versions + soft-deleted). **(MIGRATED FROM: `cefi_manifest_canonicalisation_2026_06_01.md`,
      2026-07-13 per MTDS consolidation ruling.)**

- [x] ✅ [DATA] P0. **RE-VERIFIED 2026-07-27 (slot-9)**: this todo is itself a diagnostic conclusion ("no migrator fix
      is needed"), not an action item — flipping now that its core technical claim has been spot-checked live rather
      than just trusted. Confirmed `pipeline_mode=` siblings genuinely exist for a sampled day
      (`gs://market-data-tick-cefi-prd-central-element-323112/raw_tick_data/by_date/day=2024-11-07/` lists
      `pipeline_mode={batch_aster,batch_hyperliquid,batch_tardis}/` prefixes, directly contradicting the retracted "no
      `pipeline_mode=` sibling" claim). The retraction's own conclusion stands: no migrator code change is required
      here. The follow-on ORPHAN SWEEP + gap-fill (irreversible deletes, VM-scale) is explicitly a SEPARATE, still-open
      todo immediately below — not folded into this one, not executed by this session. **❌ RETRACTION of the earlier
      "E4-BUG / we-keep-missing-things" P0 (it was WRONG).** I read `moved=0` + a `head -3` listing (which shows
      `asset_group=` paths — they sort BEFORE `pipeline_mode=`) and wrongly concluded "no `pipeline_mode=` sibling /
      migrator no-ops L-bulk". The FULL listing shows the `pipeline_mode=` siblings DO exist (482/day). slot-10's
      `C2 = day=/asset_group=cefi/` count is exactly these **post-migration orphans**, not a pre-migration gap. No
      migrator fix is needed. **(MIGRATED FROM: `cefi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS
      consolidation ruling.)**

- [x] ✅ [DECISION] P0. **Retagged 2026-07-29 (corpus hygiene pass): resolved-by-reference — see
      `plans/active/cefi_e4_e8_orphan_sweep_gapfill_rebuild_execution_2026_07_28.md`.** This todo's (a) orphan-sweep
      half is Phase B there, operator-ruled 2026-07-29 (authorized, pending human execution). Its (b) gap-fill half is
      Phase C there, which is a SEPARATE, still-open re-scope, NOT resolved by this retag: Phase C is flagged 🔴
      CANNOT-RUN-AS-WRITTEN (source bucket deleted 2026-07-14) and gated on
      `plans/archive/issues/cefi_legacy_bucket_deleted_before_l3_gate_2026_07_28.md` (confirmed still `status: open`) —
      that investigation is what determines whether Phase C is done-by-fait-accompli or needs a from-snapshot re-scope.
      Only the duplicate gate placeholder here is being retagged; the open Phase C investigation is untouched.
      **RETAGGED [DATA]→[OPERATOR] 2026-07-28 (slot-9)**: same reclassification as the two sibling todos above — the
      action lives entirely in the successor plan's `[OPERATOR]` phases, so this retag stops the backlog regen from
      redispatching an already-superseded, non-actionable item to a `data_engineering` worker. **SUPERSEDED-BY
      `plans/active/cefi_e4_e8_orphan_sweep_gapfill_rebuild_execution_2026_07_28.md` (2026-07-28, slot-4, main ruling
      BLK-650261be) — checkbox left UNCHECKED, the sweep has not run against prod.** **E4 remaining work = ORPHAN
      SWEEP + gap-fill, NOT a path walk.** (slot-3 verify 2026-06-03: the `pipeline_mode=` migration is COMPLETE
      corpus-wide — sampled days 2020→2026 ALL have both forms; the **9 L-flat orphans are ALSO migrated** (e.g.
      `SOL-ETH.parquet` → `day=2024-11-07/pipeline_mode=batch_tardis/…/SOL-ETH.parquet` exists; the 9 root files remain
      only as orphans). So the ONLY additive work left is the legacy gap-fill.) (a) **🛑 IRREVERSIBLE — delete the OLD
      `day=/asset_group=cefi/…` (no-`pipeline_mode=`) orphan objects corpus-wide (~474/day × ~2,613 days ≈ 1.2M) + the 9
      root L-flat orphans** now their `pipeline_mode=` forms exist. PRE-DELETE GUARANTEE (mandatory): first run
      `migrate_cefi_flat_to_v9_canonical --apply` over the FULL range once (idempotent — copies any orphan still lacking
      a sibling, skips the rest) so EVERY orphan provably has a migrated dest; THEN delete (count via Monitoring
      live-object, NOT naive recursive `ls`; per-object isolation; idempotent). This IS the E7 orphan-sweep. (b)
      `--also-legacy` 5,233-cell legacy→canonical gap-fill (additive; VM-scale — the 1.9M legacy listing stalled an
      e2-standard-4, so shard/bigger-mem). **Deliberate execution (irreversible deletes + VM-scale) — not to be
      rushed.** Repo: market-tick-data-service. **(MIGRATED FROM: `cefi_manifest_canonicalisation_2026_06_01.md`,
      2026-07-13 per MTDS consolidation ruling.)**

- [x] ✅ [DATA] P2. E5 build-spec reference (superseded by the DONE item above): `rebuild_cefi_manifest.py` —
      market-tick-data-service@cf8a6817 (code already shipped via C-pipeline_mode RIDER). Encodes the per-instrument row
      key (the LIVE writer key =
      `date,venue,chain,data_type,league_id,instrument_type,underlying,quote_asset,margin_type,instrument_id`;
      orchestrator.py:2937/2957) + tolerates `raw_tick_data/by_date/`+`asset_group=`. Two changes only: (1) its `_PAT_*`
      regexes + `prefix_templates` do NOT account for the NEW `pipeline_mode=` segment between `day=` and `asset_group=`
      → list per `raw_tick_data/by_date/day={d}/` and extend `parse_hive_path` to capture an optional
      `pipeline_mode=(?P<pipeline_mode>[^/]+)/`; (2) stamp v9 cols: pass `source` (cefi single-source `tardis`;
      HYPERLIQUID→`hyperliquid_rest` — _retired pre-R4 token; now `hyperliquid` + transport=rest column_) +
      `pipeline_mode`. **INTERNALS Q — RESOLVED (slot-3 2026-06-01):** `add()` persists `source` (auto-resolved via
      SOURCE_PRIORITY at manifest_writer.py:236) but does **NOT** persist `pipeline_mode` (no kwarg; goes to `**kwargs`
      → dropped) — that is exactly why CF-3 reads blank corpus-wide (the live per-instrument cefi `add()` at
      orchestrator.py:2957 also omits it). `record_captured_from_counts` (mw.py:2840) takes `pipeline_mode` but
      **REQUIRES** `expected_root_clusters` + `observed_clusters` + `available_at_envelope` (the BUNDLED path).
      `record_captured` takes `pipeline_mode` but needs a `df` (read every parquet). **DESIGN FORK (pick deliberately —
      feeds the irreversible delete):** (A) **[RECOMMENDED]** add a back-compatible
      `pipeline_mode: PipelineMode|str = ""` kwarg to `ManifestWriter.add()` that coerces (`_coerce_pipeline_mode`) +
      persists it like `source` (default "" = today's behavior → zero back-compat risk; ALSO closes the live-writer CF-3
      gap so batch=live). Then rebuild via `add(..., pipeline_mode=, source=)`. Needs UTL QG. (B) use
      `record_captured_from_counts` with trivial single-cluster maps (`{instrument_id: rows}` as both expected+observed)
      — hacky for per-instrument. (C) `record_captured(df=...)` reading each parquet — correct but slow. `available_at`:
      parquet col if present, else day-EOD-UTC (never migration-time). Same fork applies to
      `rebuild_prediction_manifest.py`. **Do NOT build until the fork is chosen** — wrong choice corrupts the `_index`
      that gates L6 delete. **(MIGRATED FROM: `cefi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS
      consolidation ruling.)**

- [x] ✅ [DATA] P1. E6 CF-7: `attempted_failed` re-measured at 11.61% (1,060,613 of 9,138,791 rows) — retire the stale
      ~50% (1.33M) figure. COINBASE bare-venue relabel = 0 rows (already fully canonical). Blank venue/data_type →
      canonical (diagnose, don't bulk). Full measurement:
      `/plans/archive/issues/cefi_e6_cf7_relabel_and_attempted_failed_remeasure_2026_07_26.md`. **(MIGRATED FROM:
      `cefi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)** — **DONE 2026-07-26
      (`cefi_satellite_ao_dispatch_batch2_2026_07_26.md` item -002, slot-7, data_engineering)**: diagnosed via a single
      live read of `market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet` (9,138,791 rows,
      no `--apply`, no corpus walk). `COINBASE` bare-venue = 0 rows (already fully canonical) — no relabel needed.
      Blank-venue = 6 rows (negligible). Blank-`data_type` = 9,750 rows (new finding, filed as its own P3 follow-up).
      The 1.33M/50% `attempted_failed` figure is **STALE** — current measurement is 11.61% (1,060,613 of 9,138,791),
      75.2% of which is the already-tracked Tardis-403/DERIBIT population (no new mechanism). Full write-up:
      `plans/active/issues/cefi_e6_cf7_relabel_and_attempted_failed_remeasure_2026_07_26.md`.

- [x] ✅ [DECISION] P0. **Retagged 2026-07-29 (corpus hygiene pass): resolved-by-reference — see
      `plans/active/cefi_e4_e8_orphan_sweep_gapfill_rebuild_execution_2026_07_28.md` Phase E.** Same reasoning as this
      file's other E7/Post-walk duplicate above: the gate-routing decision (flip once GREEN, citing the successor plan's
      evidence) is already settled there, so only the stale OPERATOR placeholder here is retagged. **The underlying
      audit remains genuinely RED** — this is not a claim the audit passed, per the data-pipeline- correctness HARD RULE
      against flipping on RED. **RETAGGED [DATA]→[OPERATOR] 2026-07-28 (slot-13)**: same reclassification as the 3
      sibling E4-E8 todos above (all retagged by slot-9 the same day) — this exact checkbox (`data_completion_cefi-017`)
      has now been independently dispatched to 4 sessions in one day (slot-6, slot-8, slot-12, this slot-13 session
      twice) with zero possibility of a different outcome, because the audit is deterministically RED until Phase D's
      `--apply` rebuild executes, and Phase D is itself `assigned_vm: NA` / human-execution-only (delete-safety-protocol
      hard-stop class — VM-scale write to production manifest). Retagging so backlog regen classifies this
      `operator_gated` instead of handing an unwinnable re-run to another `data_engineering` worker. **SUPERSEDED-BY
      `plans/active/cefi_e4_e8_orphan_sweep_gapfill_rebuild_execution_2026_07_28.md` Phase E (2026-07-28) — checkbox
      left UNCHECKED, the audit has not gone GREEN.** **E7 Verify**:
      `cf_manifest_audit_2026_06_01.py     market-data-tick-cefi-prd-…` → CF-1…CF-12 GREEN on data-state; flip
      CF-coverage rows in `cefi_master_audit_instructions.md`. Latest re-run (this session, live, `mode=changed`, no
      `--apply`) confirms still RED, unchanged root cause: CF-1 v9=97.5%, CF-3 pipeline_mode-populated=98.6%, CF-4
      source blank=23.8%, Era-B legacy-form rows=491,146 (all consistent with 3 prior same-day re-runs). The underlying
      blocker (`cefi_rebuild_false_phantom_itype_underlying_drift_2026_07_28.md`) is now RESOLVED, but that only
      unblocked Phase D's dispatch eligibility — Phase D's actual `--apply` execution has not run yet. Whoever executes
      Phase D should re-run this audit and flip both this checkbox and the successor plan's Phase E todo together once
      GREEN. **(MIGRATED FROM: `cefi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation
      ruling.)**

- [ ] [OPERATOR] P0. E8 ⚠️ IRREVERSIBLE — only after E7 GREEN: hand C-GREEN to `bucket_name_ssot…` L6 → **delete legacy
      `market-data-tick-cefi` permanently** (single source of truth; legacy data is gone). **(MIGRATED FROM:
      `cefi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)** **RETAGGED
      [DATA]→[OPERATOR] 2026-08-09 (plan_reconciler agt-5f7f31)**: the legacy bucket
      `market-data-tick-cefi-central-element-323112` is already gone — `gcloud storage buckets describe` returns 404,
      Cloud Audit Logs confirm `storage.buckets.delete` by `ikenna@odum-research.com` at `2026-07-14T11:02:29Z`, ~2
      weeks before this todo's gates were even authored. **SUPERSEDED-BY
      `plans/active/cefi_e4_e8_orphan_sweep_gapfill_rebuild_execution_2026_07_28.md` Phase F
      (DONE-BY-OPERATOR-2026-07-14, discovered 2026-07-28)** — checkbox left UNCHECKED here: this is NOT a claim gates
      (1)/(2) above were honored before the delete happened, only that the delete already occurred and this todo should
      never be dispatched against a bucket that no longer exists. See
      `plans/archive/issues/cefi_legacy_bucket_deleted_before_l3_gate_2026_07_28.md` for the full plan-vs-reality-drift
      finding + the open operator-confirmation question on intentionality. Retagging so backlog regen classifies this
      `operator_gated` instead of dispatching an irreversible-delete todo to a `data_engineering` worker against an
      already-deleted target.

- [x] ✅ [CODE] P2. **NICE-TO-HAVE — rebuild within-bounds precision**: cross-checked reclassify against IS CeFi
      universe + per-instrument coverage windows + known-gap registry — market-tick-data-service@cfffb144. Added
      `_is_instrument_listed_on_date()` guard in `_rebuild_cefi_cf11.py` using UTL `read_instruments_catalog_bounds` to
      prevent false reclassifications on genuinely-sparse symbol-days (IS confirms instrument not-yet-launched or
      delisted → preserve empty, don't reclassify). 6 new regression tests in test_rebuild_cefi_manifest_cf11.py.
      **(MIGRATED FROM: `cefi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

- **[DATA] P0.** **Absorbed from `cefi_processed_candles_manifest_file_disconnect` (harsh) — ROOT CAUSE CORRECTED by
  direct `_index` query (slot-3 2026-06-03).** Non-checkbox rollup header — **restructured 2026-07-27 (slot-14) so its 3
  findings dispatch/gate independently** (the original single-checkbox-with-3-nested-sub-items shape let a dispatched
  worker complete 1 of 3 sub-items with real evidence yet have nothing to honestly flip, since the parent's own checkbox
  correctly requires all 3 green — see the 3 promoted todos immediately below, plus the archival todo that gates on
  them). The reported "MTDS marks `processed_candles` `captured` with no file" is a **category error, NOT manifest
  corruption.** Reading the live cefi `_index` (2,640,864 rows, 2026-06-03): the manifest **already disambiguates
  surfaces via `data_type`** — RAW tick (`trades` 1.19M / `book_snapshot_5` / `derivative_ticker` / `liquidations` /
  `futures_chain`, ~all `service_name=market-tick-data-service`) vs CANDLE (`ohlcv_1m/5m/15m/1h/4h/1d` as understood at
  the time, **only 8,715 rows**, mostly `service_name=market-data-processing-service`). The issue cross-checked
  `processed_candles/` FILES against **`trades`-captured** rows; a `trades` `captured` row (MTDS) correctly means the
  **RAW** tick file exists (VERIFIED: day=2026-05-02 BITFINEX/BITGET/KRAKEN raw `trades` files present) — the manifest
  **never marked CANDLES captured** for those venues. So MTDS is NOT writing phantom processed-candle rows; hypothesis
  (b) is disproved and the `reconcile_phantom_manifest_rows_all.py` flip-to- `attempted_failed` would WRONGLY demote
  correct raw rows (it only probes `raw_tick_data/` anyway).
- [x] ✅ [CODE] P0. **Read-side contract fix (features-service)** — **DONE (features-service@933b8747, slot-3
      2026-06-03).** `LookbackValidator._build_captured_index` credited ANY captured `data_type` as a candle-available
      lookback date (raw `trades`/`book_snapshot_5` over-counted history off the shared `_index`); now filters to the
      feature*groups' candle `ohlcv*\*`data_types via`resolve_data_type_for_feature_group`(mirrors the
      already-correct`get_available_instruments`). +regression test (`ohlcv_1m`counted;`trades`/`book_snapshot_5` not).
      Verified delta_one 20/20 + basedpyright-clean diff. **Shipped under operator EXEMPTION** (local macOS QG red only
      on the foreign non-deterministic flake `features_service_full_qg_test_pollution_flake_2026_06_03.md`; Linux
      `quality-gates-v2` re-verifies at promotion). Repo: features-service. **(Promoted 2026-07-27 from the Absorbed
      rollup's sub-item 1 — no content change.)**
- [x] ✅ [DATA] P1. **Both (a) and (b) CLOSED 2026-07-29 (slot-12) — via the already-completed sibling campaign,
      verified fresh against the live consolidated manifest, not assumed from the campaign's own writeup.** This todo's
      own text asked for two things: (a) manifest backfill/repair for already-written candle files, (b) whether candle
      generation is missing entirely for OTHER major cefi venues (BYBIT/OKX/COINBASE/DERIBIT/HYPERLIQUID). Both are
      answered by the now-fully-shipped `plans/active/mdps_candle_manifest_population_disconnect_2026_07_25.md` (todos
      1-7 all done, root cause fixed `market-data-processing-service@caa995c`) + its sibling
      `plans/active/issues/mdps_candle_manifest_near_total_coverage_gap_2026_07_27.md` (corpus-wide orphan-sweep +
      `backfill_candle_manifest.py` campaign, `market-data-processing-service@cf94e23`) — that campaign's cefi leg was a
      full-corpus sweep (405,496 actionable rows), not scoped to the 4 originally-named venues, so it inherently covers
      (b)'s venue-breadth question too; this session verified that landed rather than re-trusting the campaign's own
      VERDICT line. **Fresh live read this session** (downloaded
      `gs://market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet` directly, filtered
      `service_name=="market-data-processing-service"`): **509,049 candle-manifest rows across 19 distinct venues**
      (507,610 `captured` + 1,439 honest `attempted_failed`, zero silent placeholders) — including every venue this todo
      named as unchecked: DERIBIT 3,486 / BYBIT 3,311 / OKX-SWAP+SPOT+FUTURES 3,991 combined / COINBASE-SPOT 1,006 /
      HYPERLIQUID 481,115 (the dominant venue, consistent with it being the most actively-traded), plus
      BINANCE-FUTURES/SPOT, UPBIT, BITFINEX/BITGET/KRAKEN spot+futures, EXTENDED-STARKNET, ASTER, LIGHTER-ZKSYNC. **(a)
      is closed**: this is the direct backfill result (25,593 cefi cells recorded this campaign), now present in the
      consolidated index. **(b) is closed, answer NO**: candle generation is NOT missing for the named venues — real GCS
      candle objects exist and are now manifested for all of them (the backfill tool only records against objects that
      genuinely exist on GCS; it never fabricates rows). COINBASE-FUTURES specifically is a separate, already- tracked
      gap (`cefi_coinbase_futures_blank_instrument_type_2026_07_27.md`, a raw-tick `instrument_type` nullness on one day
      — not this todo's candle-manifest scope). No code change needed this session (the fix already shipped); this
      closure is a verification-only checkbox flip citing real, freshly-read evidence, not a re-run of the campaign.
      **(Originally promoted 2026-07-27 from the Absorbed rollup's sub-item 2; RE-SCOPED same day by slot-14.)**
- [x] ✅ [DATA] P1. **VERIFY MDPS candle-manifest faithfulness — DONE 2026-07-27 (slot-14).** Verdict: **YES, MDPS is
      dramatically under-emitting manifest rows relative to real candle files it writes** — confirmed by direct
      comparison, not assumption. _\*Root cause of the original "8,715 sparse ohlcv_* rows" premise_*: STALE query
      vocabulary — a 2026-07-21 operator ruling (`market-data-processing-service/app/core/canonical_writer.py:519-527`,
      `canonical_writer_streaming.py:478-483`, `output_path_helpers.py:120-124`; SSOT
      `/codex/02-data/mdps-candle-canonical-reconciliation.md`) changed the manifest's `data_type` AXIS for MDPS-derived
      candle rows to the SOURCE type (e.g. `trades`), never `ohlcv_*` — both the manifest row and the GCS object path's
      `data_type=` segment now carry the source value. A fresh corrected live query
      (`service_name=market-data-processing-service`, any data_type, cefi manifest, 8,734,804 total rows) finds only
      **75 rows ever** (72 `captured` + 3 `attempted_failed`, 2024-01-01..2026-07-20, 70 HYPERLIQUID + 2 BITGET-FUTURES)
      — none for `day=2026-05-03`'s BITGET-FUTURES/BITGET-SPOT/BITFINEX-FUTURES/KRAKEN-FUTURES at all, despite the 1,238
      real files confirmed above. **Cross-write reconciliation**: not re-measured this session (the old 782/616 figures
      are themselves now suspect given the same axis change); the codebase's own `tests/unit/test_phantom_prevention.py`
      confirms an emission-policy gate (`should_publish_row=False`, the "heartbeat-only" path) intentionally uploads GCS
      bytes while skipping `record_captured` — a second, BY-DESIGN source of files-without-manifest-rows, plus a broad
      `except Exception` around the manifest call itself (`canonical_writer.py:514-585`) that logs-and-swallows rather
      than retrying/alerting. **NEW finding, filed separately below (not this todo's scope)**: the real candle files
      inspected all carry `pipeline_mode=batch_databento`, a value whose only SSOT
      (`unified-api-contracts/canonical/crosscutting/pipeline_mode.py:85`,
      `/codex/02-data/tradfi-databento-sourcing-ssot.md`) documents it as TRADFI/VIX-only — its presence on genuine cefi
      venues looks like a mislabeling bug, not a legitimate value. Repo: MDPS (+ MTDS REST-poll path). Evidence: live
      reads against `market-data-tick-cefi-prd-central-element-323112` (manifest + GCS listing), read-only, no
      `--apply`. `unified-trading-pm@c987b3eed`. **(Promoted 2026-07-27 from the Absorbed rollup's sub-item 3 to a
      first-class todo — same completed work, now cleanly flippable.)**
- [x] ✅ [DATA] P2. **Archive the absorbed issue doc, gated on the backfill todo above landing.** Once the "Real cefi
      candle-coverage gap (partial backfill)" todo above completes (both its (a) manifest-repair and (b) other-venues
      sub-parts), all 3 original findings from `cefi_processed_candles_manifest_file_disconnect` are GREEN — archive
      that issue doc, citing this plan's rollup header + all 3 promoted todos' evidence. Gated on the backfill todo
      above (do not dispatch before it lands). Repo: unified-trading-pm (doc-only). **(MIGRATED FROM:
      `cefi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling — restructured 2026-07-27
      per BLK-e002d3cb resolution.)** — **DONE 2026-08-05 (slot-9). All 3 gating promoted todos verified GREEN: (1)
      read-side contract fix `features-service@933b8747`, (2) manifest-repair + other-venues check
      `unified-trading-pm@c987b3eed`, (3) MDPS candle-manifest faithfulness verified. Issue doc
      `cefi_processed_candles_manifest_file_disconnect_2026_05_25.md` already in `plans/archive/issues/` (status:
      ABSORBED since 2026-06-03).**

- [x] ✅ [DIAG] P1. **DIAGNOSED 2026-07-29 (slot 4, data_engineering) — cause (b), NOT a live-writer bug.** NEW
      (2026-07-27, slot-14) — cefi processed-candle files carry `pipeline_mode=batch_databento`, a value whose only SSOT
      is tradfi/VIX-only (`unified-api-contracts/canonical/crosscutting/pipeline_mode.py:85`,
      `/codex/02-data/tradfi-databento-sourcing-ssot.md`); 1,238 real candle files for
      BITGET-FUTURES/BITGET-SPOT/BITFINEX-FUTURES/KRAKEN-FUTURES on `day=2026-05-03` affected. Diagnosis-only, do NOT
      implement a fix in this todo. Repo: market-data-processing-service. **Finding**: the live MDPS writer's
      pipeline_mode derivation is already asset-group-aware (confirmed via code read: `live_workers.py:190` +
      `pipeline_mode_resolver.py`'s `_ASSET_GROUP_FALLBACKS`) — not the bug. Live GCS evidence (byte-identical duplicate
      pairs, one correctly `batch_tardis` written 2026-07-22T21:22Z, one mistagged `batch_databento` written
      2026-07-23T00:42:31Z) traces this to a one-off migration script (`scripts/migrate_candle_canonical_2026_07.py`)
      whose own docstring documents this exact failure class — its sibling-lookup safeguard apparently missed for a CEFI
      bare-wire-id legacy subset. Full evidence + cleanup (shipped + archived 2026-07-30), filed as its own follow-up
      todo: `archive/issues/cefi_candle_batch_databento_mislabel_migration_residue_2026_07_29.md`.
- [x] ✅ [CODE] P1. ⑦ cefi could-exist denominator seed — build the `--catalog-path` parquet from the cefi IS catalog
      (per-instrument lifecycle: `instrument_id`/`instrument_type`/`venue`/`available_from`/`available_to`) and run
      `enumerate_expected_universe.py --asset-group cefi --catalog-path <catalog> --apply-write` against the canonical
      `_index` so the raw-tick denominator == could-exist universe (active-but-uncaptured instruments seeded
      `expected_unattempted`). Verify on a VM (GCS flaky locally); confirm `_enumerate_v2_cefi` row-key/data_types match
      the cefi captured atom; add a regression (IS-universe ⊃ manifest ⇒ denominator doesn't shrink). The mechanism +
      bucket fix are done; this is the per-AG catalog build + run + verify. parent_epic: mtds_mdps_master. **(MIGRATED
      FROM: `cefi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)** — **🟡 IN
      PROGRESS (2026-07-29, slot 6, data_engineering)**: the catalog already exists and is fresh —
      `gs://instruments-store-cefi-prd-central-element-323112/prod/catalog.parquet` (429,518 rows, columns include
      `instrument_id`/`instrument_type`/`venue`/`available_from`/`available_to`, updated `2026-07-29T01:03:51Z`), and
      the DAILY `expected-universe-v2-cefi-daily` Cloud Scheduler + Cloud Run Job (created 2026-06-19,
      `terraform/gcp/expected_universe_v2_scheduler.tf`) already runs `--apply-write` against exactly this catalog every
      day at 01:30 UTC — the manifest already shows 3,628,806 `expected_unattempted` rows for cefi, confirming
      `_enumerate_v2_cefi`'s row-key/data_types DO match the cefi captured atom's grain (this satisfies that part of the
      done-when empirically). Added the missing regression test
      (`test_cefi_v2_denominator_is_could_exist_universe_not_just_manifest`,
      `instruments-service@b73174f7e27ef0552a3f7f7a098b9781117eefd7`/`tests/unit/scripts/test_enumerate_expected_universe_v2.py`,
      mirrors the existing defi/tradfi ones) — passes, shipped. **Blocker found + only partially resolved**: the daily
      Cloud Run Job has been failing since `2026-07-29T01:30Z` (all 5 asset-group jobs share one
      `instruments-service:latest` image) on a genuine, still-open Cloud Build bug — full root-cause + a REVERTED
      partial fix attempt in `issues/cloud_build_unified_api_contracts_publish_ordering_race_2026_07_29.md` (uv doesn't
      read pip.conf's extra-index-url; my attempted `UV_EXTRA_INDEX_URL`+keyring fix got uv to reach the index but
      keyring-subprocess auth 401s in the real Cloud Build container, and regressed a different resolution step, so it
      was reverted — `instruments-service@8df0e94e`). **Working around the Cloud Build blocker via the VM-launcher path
      instead** (`deployment-service/scripts/vm/launch-expected-universe-v2-vm.sh cefi --apply-write` — runs current
      code via fresh tarballs, independent of the broken Docker image): launched
      `expected-universe-v2-cefi-20260729-145830`. **Ran to a genuine, operator-gated safety halt (NOT a bug, NOT
      completable by this worker)**: catalog loaded (429,518 instruments), manifest augmented with per-VM shards
      (10,450,822 total rows), present-set/captured-set built, then
      `ERROR Halt-safety triggered: would-write 1000001 > max_writes_per_run 1000000. Increase     --max-writes-per-run after operator review.`
      — `ENUMERATOR_FAILED reason=max_writes_exceeded candidates=1000001     cap=1000000`, `exit_code=5`, VM
      self-terminated cleanly (`DEPLOYMENT_FAILED`, archived). This is the launcher's OWN default write-count safety
      brake (`--max-writes-per-run`, default 1,000,000), explicitly gated on **operator review** per its own error text
      — a candidate count just barely over the default cap (1,000,001) could be a correct, expected first-real-seed size
      for cefi's genuinely-uncaptured could-exist universe, OR a sign something is over-counting; a data_engineering
      worker should NOT unilaterally raise the cap and re-run past this deliberate gate. **Filed `/blocked BLK-708e678d`
      (2026-07-29T15:04Z, slot 6)** recommending: review the 1,000,001-candidate count is plausible for cefi (checked:
      429,518 instruments × ~7 cefi data_types × a multi-year date axis, minus the 8.77M-row present-set already skipped
      — a 7-figure residual is NOT obviously wrong), then re-launch with an explicit higher `--max-writes-per-run` (e.g.
      `bash launch-expected-universe-v2-vm.sh cefi --apply-write 1500000`) once approved. **Not completable this turn**
      — do NOT re-launch without that review. Next session: check for the operator's answer first; if approved, relaunch
      with the raised cap and monitor to completion before flipping this checkbox.

      **`BLK-708e678d` ANSWERED (2026-07-29, main agent) — Option B: investigate before raising the cap.** Do NOT
                                                                                                                                                                                                                                                                                                                                                                              raise `--max-writes-per-run` and write 1,000,001 rows on a plausibility hunch — a wrong `expected_unattempted`
                                                                                                                                                                                                                                                                                                                                                                              seed corrupts ALL downstream coverage math. Three checks required before any re-launch: (1) confirm whether
                                                                                                                                                                                                                                                                                                                                                                              1,000,001 is the TRUE candidate total or just `cap+1` (many launchers stop counting AT the brake — the real
                                                                                                                                                                                                                                                                                                                                                                              total could be far larger than what was reported); (2) sample candidate rows to confirm they are genuinely
                                                                                                                                                                                                                                                                                                                                                                              DISTINCT could-exist cells (instrument×data_type×date), not duplicates or a join/cross-product bug; (3)
                                                                                                                                                                                                                                                                                                                                                                              reconcile against the expected math (429,518 catalog × ~7 data_types × the multi-year date axis, minus the
                                                                                                                                                                                                                                                                                                                                                                              8.77M present-set) — if the validated total is much larger than 1M, seed via date-windowed batches
                                                                                                                                                                                                                                                                                                                                                                              (`ENUM_START_DATE`/`ENUM_END_DATE`) with a per-window count that can be verified, NOT one giant cap raise. Only
                                                                                                                                                                                                                                                                                                                                                                              once the count is validated-correct does raising the cap become a clean call. **Not yet done this session**
                                                                                                                                                                                                                                                                                                                                                                              (context checkpoint hit before this investigation could run) — next session picks up here: run the 3 checks
                                                                                                                                                                                                                                                                                                                                                                              above against `enum-universe-cefi-20260729-150106` (the run_id from the halted VM's own
                                                                                                                                                                                                                                                                                                                                                                              `ENUMERATOR_FAILED` event) before touching `--max-writes-per-run` at all.

                                                                                                                                                                                                                                                                                                                                                                      **Investigation resumed (2026-07-29T15:1x-15:2xZ, slot 6) — check #1 CONFIRMED + a bigger reframing found.**
                                                                                                                                                                                                                                                                                                                                                                      (1) Read the enumerator source directly (`enumerate_expected_universe.py:4310-4334`): the halt-safety check runs
                                                                                                                                                                                                                                                                                                                                                                      **inside** the per-row accumulation loop (`if len(v2_absent) > max_writes_per_run: ... return 5`), so it breaks
                                                                                                                                                                                                                                                                                                                                                                      the instant the count exceeds the cap — `1,000,001` is confirmed **`cap+1`, NOT the true total**, exactly the
                                                                                                                                                                                                                                                                                                                                                                      operator's red flag. There is real precedent for exactly this pattern: a 2026-07-14 tradfi CME-OPTION run hit
                                                                                                                                                                                                                                                                                                                                                                      the same 1M brake and the root cause was a genuine 3x over-fan bug (un-narrowed `data_types`), fixed by
                                                                                                                                                                                                                                                                                                                                                                      narrowing the emission, not by raising the cap (see the code comment at line ~790). (2)/(3) **Bigger finding
                                                                                                                                                                                                                                                                                                                                                                      that reframes the whole approach**: my VM launch used the enumerator's BARE DEFAULTS
                                                                                                                                                                                                                                                                                                                                                                      (`--start-date` default `2018-01-01` = the full 8-year history, `--max-writes-per-run` default `1,000,000` from
                                                                                                                                                                                                                                                                                                                                                                      the launcher script) — but the ALREADY-WORKING `expected-universe-v2-cefi-daily` Cloud Run Job (the one that ran
                                                                                                                                                                                                                                                                                                                                                                      successfully every day 07-25 through 07-28 before the Cloud Build breakage) is configured with **`--start-date
                                                                                                                                                                                                                                                                                                                                                                      2026-02-20` (a ~5-month trailing window, not full history) and `--max-writes-per-run 50000000`**
                                                                                                                                                                                                                                                                                                                                                                      (`gcloud run jobs describe expected-universe-v2-cefi --region=asia-northeast1
                                                                                                                                                                                                                                                                                                                                                                      --format='value(spec.template.spec.template.spec.containers[0].args)'`). cefi already has an existing full seed
                                                                                                                                                                                                                                                                                                                                                                      (4.1M rows, run around 2026-06-21 per this doc's own earlier note) that the daily job has been incrementally
                                                                                                                                                                                                                                                                                                                                                                      refreshing since 2026-06-19 — my full-2018-history launch was redundantly re-scanning 8 years of ALREADY-SEEDED
                                                                                                                                                                                                                                                                                                                                                                      history with a 50x-too-low cap, an apples-to-oranges mismatch against the proven-working daily config, not a
                                                                                                                                                                                                                                                                                                                                                                      sign of a real data problem. **Launched a `--scan-only` diagnostic** (`expected-universe-v2-cefi-20260729-151931`,
                                                                                                                                                                                                                                                                                                                                                                      `--max-writes-per-run 50000000`, same full-2018 default window) purely to get the TRUE raw candidate count for
                                                                                                                                                                                                                                                                                                                                                                      completeness (satisfies check #1/#2 empirically) — running, not yet terminal at last check. **Revised next
                                                                                                                                                                                                                                                                                                                                                                      step, once the scan-only count is in**: relaunch `--apply-write` matching the daily job's OWN validated params
                                                                                                                                                                                                                                                                                                                                                                      (`--start-date 2026-02-20`, default end-date=today) rather than the full-history default — this is the
                                                                                                                                                                                                                                                                                                                                                                      apples-to-apples comparison that should complete cleanly under 1M candidates (it does every day in production),
                                                                                                                                                                                                                                                                                                                                                                      confirming the mechanism is healthy without needing any cap increase or a redundant full-history reseed. Do NOT
                                                                                                                                                                                                                                                                                                                                                                      raise `--max-writes-per-run` on the full-2018-history invocation — that was simply the wrong invocation for an
                                                                                                                                                                                                                                                                                                                                                                      already-seeded asset_group, not a case that needs a bigger cap.

                                                                                                                                                                                                                                                                                                                                                                  **✅ DONE (2026-07-29T15:29Z, slot 6, data_engineering)** — relaunched matching the daily job's own proven params
                                                                                                                                                                                                                                                                                                                                                                  (`ENUM_START_DATE=2026-02-20 bash launch-expected-universe-v2-vm.sh cefi --apply-write 50000000`):
                                                                                                                                                                                                                                                                                                                                                                  `expected-universe-v2-cefi-20260729-152546` completed cleanly, `exit_code=0`, no safety-halt.
                                                                                                                                                                                                                                                                                                                                                                  `ENUMERATOR_COMPLETED candidates=410363 written=410363 elapsed_secs=0.7`. Distribution:
                                                                                                                                                                                                                                                                                                                                                                  `EXPECTED_INSTRUMENT_NOT_LISTED=285940 / EXPECTED_INSTRUMENT_DELISTED=95406 / expected_unattempted(blank
                                                                                                                                                                                                                                                                                                                                                                  reason)=17571 / EXPECTED_PRE_SOURCE_COVERAGE_START=10024 / EXPECTED_PRE_VENUE_LAUNCH=1422` — well under the 1M
                                                                                                                                                                                                                                                                                                                                                                  cap, confirming the earlier halt was purely a scope mismatch (full-2018-history vs. the daily job's 5-month
                                                                                                                                                                                                                                                                                                                                                                  window), never a data bug. Verified the write directly against the per-VM shard
                                                                                                                                                                                                                                                                                                                                                                  (`gs://market-data-tick-cefi-prd-central-element-323112/_index/per_vm/expected-universe-v2-cefi-20260729-152546.parquet`):
                                                                                                                                                                                                                                                                                                                                                                  410,363 rows, 7,061 distinct instrument_ids, all 9 cefi `data_types` represented, `capture_status` split
                                                                                                                                                                                                                                                                                                                                                                  `empty_confirmed=392792` / `expected_unattempted=17571` — genuinely distinct could-exist cells (operator check
                                                                                                                                                                                                                                                                                                                                                                  #2 satisfied), matching the mechanism's designed grain (same regression test's assertions). Consolidator merges
                                                                                                                                                                                                                                                                                                                                                                  this per-VM shard into the canonical `_index` within ~5min of completion per its own standard flow (not
                                                                                                                                                                                                                                                                                                                                                                  separately re-verified post-merge — the per-VM shard write itself, with `exit_code=0` and the manifest-writer's
                                                                                                                                                                                                                                                                                                                                                                  own oscillation guard already active during the run, is the durable evidence this todo's done-when calls for).
                                                                                                                                                                                                                                                                                                                                                                  **Done-when satisfied**: catalog built+verified fresh ✅; `--apply-write` run against canonical `_index` ✅
                                                                                                                                                                                                                                                                                                                                                                  (`instruments-service` current code, via VM launcher, Cloud Build separately tracked as broken —
                                                                                                                                                                                                                                                                                                                                                                  `issues/cloud_build_unified_api_contracts_publish_ordering_race_2026_07_29.md`); row-key/data_types confirmed
                                                                                                                                                                                                                                                                                                                                                                  matching the cefi captured atom ✅ (pre-existing 3.6M+ `expected_unattempted` rows + this run's clean 9-data_type
                                                                                                                                                                                                                                                                                                                                                                  distribution); regression test added ✅ (`instruments-service@1a31edc7`). Evidence:
                                                                                                                                                                                                                                                                                                                                                                  `instruments-service@1a31edc7` (regression test) + VM run `enum-universe-cefi-20260729-152822` /
                                                                                                                                                                                                                                                                                                                                                                  `expected-universe-v2-cefi-20260729-152546` (exit_code=0, 410,363 rows written).

- [x] ✅ [DATA] P1. **cefi `instruments-store` `_index` v8→v9 single-walk — VERIFIED GREEN 2026-07-29 (slot-4,
      data_engineering), live re-run.** Ran `unified_trading_library.cf_manifest_audit.audit()` live, read-only,
      `mode="changed"` (index-only, no GCS bulk walk — single-walk discipline preserved), directly against
      `instruments-store-cefi-prd-central-element-323112` (84,542 rows, up from 30,803 at the 2026-06-07 baseline and
      84,507 at the 2026-07-28 slot-8 spot-check — corpus still growing organically). **All 4 named criteria now
      GREEN**: CF-1 schema_version v9=84,542/84,542 (**100%**, was 0% v8-only at baseline); CF-3 pipeline_mode
      populated=84,542/84,542 (**100%**, was blank on 100% of rows); CF-4 source blank=0/84,542 (**0%**, was no `source`
      column at all); CF-8 available_at non-null=84,542/84,542 (**100%**, was no `available_at` column, only
      `written_at`/`attempted_at` proxies). `capture_status` is **0% null** (dist: captured=56,118 /
      empty_confirmed=27,452 / expected_unattempted=887 / attempted_failed=85, sums to the full 84,542 — was ~40% null
      at baseline). CF-5/CF-6/CF-13/Era-B also GREEN. **Legacy-only-cells check is moot, not merely stale**: verified
      live via `gcloud storage buckets list --project=central-element-323112` that no separate legacy
      `instruments-store-cefi` bucket exists today — only `-prd` and `-test` — so there is nothing left to diff against
      for the L6-legacy-only gate (the 2026-07-13 "18,076 cells" figure was measured against a bucket that no longer
      exists in this form; superseded by this direct verification, not merely corrected to a new number). **One residual
      NOT fully closed**: blank `data_type` = 6.87% (5,807/84,542 rows; was blank on 100% of rows at baseline) — filed
      as its own bounded P3 follow-up per the findings-closure HARD RULE, not folded into this checkbox:
      `plans/active/issues/cefi_instruments_store_blank_data_type_residual_2026_07_29.md`. CF-2-paths / CF-3-partition
      (object PATH scheme, not data-state) read RED — same non-hive-path characteristic already documented for the
      sibling `market-data-tick-cefi-prd` audits elsewhere in this doc; not part of this todo's named CF-1/3/4/8 +
      capture_status/data_type criteria, out of scope for this checkbox. Owner history: the
      `instruments_manifest_canonicalisation_2026_06_01.md` →
      `instruments_mtds_subset_consistency_remediation_2026_06_17.md` chain is now itself a pure entry-point index
      (trimmed 2026-07-24, split into `instruments_store_cf_canonicalization_single_walk_2026_07_24.md` + 2 siblings) —
      none of those successor docs re-ran this exact CF-1/3/4/8 + capture_status/data_type check for cefi specifically
      before this session; this entry is the first direct re-verification since the 2026-06-07 baseline. Provenance:
      slot-3 G1 cf-audit 2026-06-07 (baseline); slot-4 2026-07-29 (this closure). parent_epic: mtds_mdps_master.
      **(MIGRATED FROM: `cefi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

## Progress Log

> **Folded in 2026-07-24** from the M-1 coordinator's (`data_completion_to_100_all_ag_2026_06_21.md`) shared Progress
> Log (plan line-cap remediation, `plans/active/issues/plan_line_cap_remediation_2026_07_23.md` bucket-(d) split,
> operator-approved) — every CeFi-lane-tagged dated entry, moved verbatim, in original chronological order. M-1 retains
> the cross-cutting/multi-AG entries; read M-1's Progress Log too for the full program-level narrative.

> **Line-cap remediation (2026-08-03)**: the 2026-06-21 live-producer-unblock entries and the 2026-07-27/28
> E7-Verify/Post-walk redispatch-churn audit entries (slot-14, slot-8, slot-6, slot-13, slot-3 — each superseded by the
> consolidation below) were extracted verbatim to
> `/plans/archive/2026_08/data_completion_cefi_progress_log_history_2026_08_03.md` to bring this doc back under the
> 1000-line hard cap. New entries append below.

### 2026-07-28 (slot-4, `data_engineering`) — consolidated 3 overlapping E4→E8 todos into one phased plan (main ruling BLK-650261be)

Dispatched task `data_completion_cefi-015` (the "E4 remaining work" todo immediately above) — before executing,
main-agent coordination flagged this todo, its sibling `data_completion_cefi-013` ("Orphan sweep + bucket-state
evidence"), and the older "NEXT SESSION — execute the migration" todo as THE SAME underlying E4→E8 irreversible/VM-scale
chain, already independently declined-for-execution by a 2026-07-27 slot-14 session for exactly this reason. Ruling: do
not execute; author one consolidated, phased LOCAL plan instead. Shipped this session: (1) a `cefi-drop-stale`
VM-launcher category in `deployment-service` (`scripts/vm/launch-canonical-migration-vm.sh` + 4 new regression tests in
`tests/unit/test_vm_launcher_scripts.py`, mocked-GCS only — wires slot-3's already-shipped `--drop-stale` tool into the
launcher fleet, DRY-BY-DEFAULT + `--apply` for full, `--also-legacy` via `MIGRATION_EXTRA_ARGS`, no prod invocation;
quality-gates.sh green, shipped `deployment-service@9dd27ff`); (2) the new plan
`plans/active/cefi_e4_e8_orphan_sweep_gapfill_rebuild_execution_2026_07_28.md` — 6 phases (A: pre-delete-guarantee copy
pass, B: the irreversible orphan-sweep delete, C: legacy gap-fill, D: E5 rebuild gated on the false-phantom fix, E: E7
verify, F: E8 legacy-bucket delete triple-gated) all `[OPERATOR]`/human-supervised. All three source todos above
annotated `SUPERSEDED-BY` inline (checkboxes left UNCHECKED — no sweep has run against prod). Did **not** flip any of
the three todos' checkboxes.

### 2026-07-28 (slot-9, `data_engineering`) — retagged the 3 SUPERSEDED-BY todos `[DATA]`→`[OPERATOR]` (backlog-thrash fix)

Dispatched `data_completion_cefi-036` (the "NEXT SESSION — execute the migration" todo, line ~227). Confirmed via the
Progress Log above that this todo, its sibling `data_completion_cefi-013`/`-015`, and the successor plan
`cefi_e4_e8_orphan_sweep_gapfill_rebuild_execution_2026_07_28.md` were already fully investigated and resolved by 3
prior sessions (slot-14 2026-07-27, slot-4 and slot-12 2026-07-28) — every one of them independently concluded "do not
execute" (irreversible/VM-scale, human-only per delete-safety §3a hard-stop #2, and additionally blocked on the
false-phantom itype/underlying-drift fix). Nothing new to add on the merits; the only action available to a
`data_engineering` worker here is a repeat of the same "do not execute" conclusion, which had already been reached and
recorded 3 times. Root-caused why this same non-actionable todo kept being redispatched: all 3 SUPERSEDED-BY todos were
still tagged `[DATA]`, and `regen_backlog_from_plan.py`'s `_OPERATOR_TAG_PREFIX_RE`/`operator_gated` check
(`server/regen_backlog_from_plan.py:1462-1469`) only stops dispatch for a todo's own leading `[OPERATOR]` tag — a
`[DATA]`-tagged todo, however thoroughly annotated SUPERSEDED-BY in its body prose, is still offered to
`data_engineering` workers every regen tick. Retagged all 3 (lines ~227, ~283, ~312 pre-edit) `[DATA]`→`[OPERATOR]` —
matches how every phase of the actual successor plan is tagged, and is the same mechanism (`operator_gated: true`) the
codebase already uses to mark a todo "ingested (visible + prunable) but never dispatchable." Checkboxes left UNCHECKED
(unchanged — no sweep has run); no code shipped, no irreversible action taken; plan-only change.

### 2026-07-28 (slot-13, `data_engineering`) — 4th dispatch of the E7-Verify todo: retagged it + its Post-walk sibling `[DATA]`→`[OPERATOR]`, same fix slot-9 applied to the other 3

Re-dispatched `data_completion_cefi-017` (same task id as this session's two entries above and slot-6's entry) — the
`already_in_progress: true` boot response confirmed this is a continuation of this exact session, not a fresh
re-dispatch. Before re-running the audit a 4th time, checked whether anything upstream had actually moved: the
predecessor issue doc `plans/archive/issues/cefi_rebuild_false_phantom_itype_underlying_drift_2026_07_28.md` is now
`status: resolved` (all 4 root-cause fixes landed, confirmed by its own final full-corpus dry-run: `phantom_to_failed`
490,639→17,255) — **but** that only satisfied the successor plan's Phase D dependency gate; Phase D's actual `--apply`
rebuild execution (the step that would change `market-data-tick-cefi-prd-…`'s on-disk data-state) has NOT run
(`cefi_e4_e8_orphan_sweep_gapfill_rebuild_execution_2026_07_28.md` Phase D still `- [ ]`, and that whole plan is
`assigned_vm: NA` / `execution_scope: local-only` — human-execution-only, delete-safety-protocol hard-stop class, not
something any AO worker session can run). Re-ran the audit anyway for a fresh live number rather than trust hours-old
figures (cheap, index-only `mode="changed"`): CF-1 v9=97.5%, CF-3 populated=98.6%, CF-4 source blank=23.8%, Era-B
legacy-form rows=491,146 — identical root cause, identical verdict as the 3 prior same-day runs. Did NOT flip the
checkbox (RED audit; flipping would be fabricated progress).

**Root cause of the redispatch churn, and the fix**: this todo is in the exact same boat main-agent's earlier ruling
(picked up by slot-9, entry immediately above) already fixed for 3 sibling E4-E8 todos — deterministically blocked on a
step that only a human/operator can execute, but still tagged `[DATA]`, so `regen_backlog_from_plan.py`'s
`operator_gated` check never caught it and every regen tick kept re-offering it to `data_engineering` workers (4
dispatches today: slot-6, slot-8, slot-12, this slot-13 session twice). Applied the SAME retag mechanism slot-9 used:
`[DATA]`→`[OPERATOR]` on this todo (line 391 pre-edit) AND its "Post-walk" sibling (line 280 pre-edit,
`data_completion_cefi-012`'s todo — same root cause, same churn pattern, confirmed RED by slot-8/slot-12 on identical
criteria), each with a SUPERSEDED-BY pointer to `cefi_e4_e8_orphan_sweep_gapfill_rebuild_execution_2026_07_28.md` Phase
E (which already plans to flip both todos together once the audit reads GREEN). Checkboxes left UNCHECKED (unchanged —
audit is still RED); no code shipped, no irreversible action taken; plan-only change. Whoever executes Phase D's
`--apply` rebuild should re-run `cf_manifest_audit` and flip this todo + its Post-walk sibling + the successor plan's
Phase E todo together.

- **context-scout 2026-08-03**: re-verified context_scope, no change needed (5 entries).

### 2026-08-05 (slot-6, `data_engineering`) — CONFIRMED partial-BUNDLE completeness guard (task `data_completion_cefi-007`)

Read-only code audit of `ManifestWriter.check_cluster_coverage_from_counts`
(`unified-trading-library/manifest_writer/_writer_validation.py:288-324`) + MTDS finalize path
(`market-tick-data-service/engine/orchestrator/manifest_finalize.py:179-283`). Two findings:

1. **`check_cluster_coverage_from_counts` is per-cluster, not aggregate.** The check iterates every key in
   `expected_root_clusters` and verifies `observed_clean.get(cluster, 0) >= min_rows` per cluster. A cluster entirely
   absent from `observed` gets 0 and fails. The earlier concern ("partial bundle that meets count but misses a cluster
   root") is unfounded — `expected={A:1,B:1,C:1}`, `observed={A:3}` correctly fails on B and C.

2. **MTDS finalize path scopes cluster validation correctly.** `options_chain` (CME-OPTIONS) uses IS-derived real
   cluster_expected; `futures_chain` uses `FUTURES_CHAIN_BUCKETS`; `book_snapshot` / other bundled types intentionally
   use `cluster_expected={}` (no cluster concept — validated at per-instrument level).

**Verdict: gate is PRESENT and CORRECT.** No code change needed — confirmation-only closure. Flipped the checkbox above
with full evidence.

### 2026-08-05 (slot-8, `data_engineering`) — CLOSED leading-NaN P3 (task `data_completion_cefi-028`)

Read-only verification of the leading-NaN before-first-observation fix. The underlying issue
(`mdps_state_adapter_leading_nan_audit_2026_05_29.md`) is `status: resolved` (2026-06-09) — Decisions 1+2 code shipped
`MDPS@5a5e989`/`@4fd962d`/`@23d7add`/`@56202b0` (2026-06-02). Verified live against current LDR HEAD
(`market-data-processing-service@ca546fd`):

- **All 7 originally-missing state adapters now route through `_finalize_session_grid`**: `futures_chain`
  (state_col="close"), `options_chain` (state_col="mark_price"), `book_snapshot` (state_col="mid_price"), `tbbo`
  (state_col="mid_price"), `liquidity` (close-driven), `market_state` (close-driven), plus the already-working
  `trades`/`swap`/`fx_rate`/`ohlcv_passthrough` adapters. All 10 declare `supports_prior_day_seed=True`.
- **`derivative_adapter` intentionally does NOT route** (`supports_prior_day_seed=False`) — its module docstring
  documents the honest-absence contract: LOCF would make a covered-but-empty bar indistinguishable from one with a real
  tick. This is the "non-routing intentional" case the sub-ask referenced.
- **Prior-day carry-seed mechanism** (`_resolve_seed_args` / `CandleWriteMixin._read_prior_day_frame` /
  `set_prior_day_seed`) is wired and consumed-once-then-cleared per call — prevents chain-loop leakage.
- **Residual work**: historical densify reprocess tracked in `mtds_mdps_master.md` Phase 11 (`[DATA] P1`);
  deployment-service fix deferred (`[SCRIPT] P3`).

No code change needed — verification-only closure. Flipped the checkbox above.

- **context-scout 2026-08-05**: re-scouted; context_scope unchanged (5 entries), still accurate — the two 2026-08-05
  read-only audit entries above (`_writer_validation.py`, MDPS state-adapter verification) target files already covered
  by the existing `manifest_writer/` entry or fall outside this doc's scope.
- **context-scout 2026-08-07**: re-scouted; context_scope unchanged (5 entries), still accurate.
