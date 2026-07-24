---
doc_type: plan
title: Honest Coverage v2 — instrument-denominator audit baked in (two layers · two views · instrument gates downloads)
summary:
  Upgrade the honest-coverage system so the instrument-enumeration (denominator) audit is a first-class, standing part
  of honest coverage — not a one-off. Two layers (instrument coverage gates data-download coverage), two views
  (day-by-day + shard-breakdown), drill-down/roll-up across asset_group → venue → instrument_type → data_type → day. Fix
  the measurability bugs first (stale-bucket read, prd/non-prd split, instrument_type normalization, VENUE_FETCH_FAILED
  swallowing 79% of failure causes, untyped empty_confirmed) so v2 reports real numbers.
status: complete # (was: active) 2026-07-15 plan-reconcile §7-residual: operator ruling A (archival + codex-sync); verified 0 open todos, evidence spot-checked
nature: design
asset_group: [cross-cutting]
stage: [data, meta]
repos: [instruments-service, unified-api-contracts, deployment-service, unified-trading-library]
scope: [engineer, admin]
tags:
  [
    honest-coverage,
    denominator-audit,
    instrument-coverage,
    availability-manifest,
    4-state,
    drill-down,
    data-correctness,
  ]
related:
  [
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/data-pipeline-correctness-hard-rule.md,
    /codex/02-data/honest-absence-downstream-handling.md,
    /codex/04-architecture/instruments-service-as-ssot-for-mtds.md,
    /plans/archive/2026_07/mvp_backfill_cefi_tick_v10_2026_06_27.md,
    /plans/archive/2026_07/mvp_catalogue_finalization_v10_2026_06_27.md,
  ]
created: 2026-06-28
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 7
estimate_calibrated_ai_days: 5.6
last_updated: 2026-06-28
locked_by: # cleared 2026-07-15 — operator [unlock-plan] (plan-reconcile §7)
locked_since:
supersedes:
superseded_by:
depends_on:
source:
model_tier: sonnet-doable
thinking_tier: medium
assigned_role: data_engineering
drift_direction: advance-code
---

> **HUMAN PLAN (`assigned_vm: NA`)** — operator-driven, NOT auto-dispatched. Captures the Honest-Coverage-v2 design +
> the live diagnostics gathered 2026-06-28. Operator decision (2026-06-28): human-owned.
>
> **🤖 MODEL TIER: `sonnet-doable` (thinking: medium).** This is the **Sonnet implementation** half — bounded,
> single-repo mechanical fixes + impl-from-spec. The **few Opus checkpoints** (cross-repo design + final certification)
> live in the companion **`honest_coverage_v2_opus_checkpoints_2026_06_28.md`** (`model_tier: opus-required`). The two
> `[OPUS-CK]`-tagged items below are BLOCKED on that plan's design output — do not attempt them on Sonnet. **BOOT GATE
> (run FIRST, STOP on non-zero):**
> `python3 scripts/plans/audit_model_tier.py --assert plans/active/honest_coverage_v2_instrument_denominator_2026_06_28.md`
> — hard-fails if the running agent's model doesn't satisfy this plan's tier (SSOT:
> `/codex/06-coding-standards/model-tier-selection.md`).

## The model — Honest Coverage v2

**Two layers (the gate):**

1. **Layer 1 — Instrument coverage (the denominator audit, first-class).** Is the could-exist universe itself complete?
   = does **IS catalogue × UAC expected-data-type matrix** (`DATA_TYPES_BY_ASSET_GROUP` /
   `get_expected_data_types_for_venue`) enumerate **every (venue, instrument_type, data_type) that should exist**,
   bounded by listing windows? Measured BEFORE Layer 2.
2. **Layer 2 — Data-download coverage.** The 4-state `capture_status` accounting (captured / empty_confirmed[typed] /
   attempted_failed / expected_unattempted) against the **Layer-1-verified** denominator.

**The gate:** instrument coverage GATES download coverage. Layer-2 % is reported as trustworthy ONLY when Layer-1 =
100%. The system never reports "downloads look good" while the instrument denominator has holes — you cannot have honest
download coverage on top of a dishonest instrument denominator.

**Two views (both layers expose both):**

- **day-by-day** (time axis) — for each day, are all expected shards present? Catches "missed a whole day/range."
- **shard-breakdown** (entity axis) — for each (venue × instrument_type × data_type), complete across its lifetime?
  Catches **"missed OPTION entirely / a whole data_type."**

**Drill-down / roll-up:** one number at top → `asset_group → venue → instrument_type → data_type → day`, expandable
either direction.

**Codex SSOTs (READ before touching):**

- `/codex/02-data/availability-manifest-and-data-status.md` (4-state + shard atom)
- `/codex/02-data/honest-absence-downstream-handling.md` (typed absence)
- `/codex/04-architecture/instruments-service-as-ssot-for-mtds.md` (IS owns instrument universe)
- `/codex/02-data/data-pipeline-correctness-hard-rule.md` (RED audit freezes layer N+1)

Where the axes live: **instruments = IS catalogue** (with `mvp` a stamped column); **data_types per venue = UAC**; **MVP
filter = UAC `mvp_scope.py`**.

---

## Phase 0 — Measurability fixes (PREREQUISITE — v2 must report real numbers)

> Diagnostics below are from the LIVE cefi prd manifest (`market-data-tick-cefi-prd-central-element-323112`),
> 2026-06-28T19:25Z. Each is a reason the current honest-coverage number cannot be trusted.

- [x] [CODE] P0. **Harness reads the stale bucket.** `instruments-service/scripts/measure_honest_coverage.py` selects
      the candidate bucket with the MOST rows → picks the stale non-prd cefi manifest (35.8M rows, last written
      2026-06-08, 20 days old) over the live prd bucket (5.2M rows + fresh per_vm shards). Result: cefi reported 11.68%
      when the live prd manifest has **2,920,384 captured** (~4× under-count). Fix: prefer the bucket with the freshest
      `written_at` / most-recent capture activity (or merge both), and LOUD-LOG which won. Add a regression test. ✅
      instruments-service@bbff145 — blob.updated timestamp ranking + LOUD-LOG; 8 unit tests green; QG passed
- [x] [INFRA] P0. **prd ↔ non-prd manifest split.** prd holds live captured data but **no `expected_unattempted`
      skeleton**; non-prd holds the full skeleton but stale captures. The env-tiering "Phase 2.6 consolidate onto -prd"
      never completed → no single-bucket read carries both a complete denominator AND live numerator. Finish the
      consolidation (or have the harness union the skeleton from one + captures from the other) so denominator and
      numerator live together. ✅ instruments-service@bbff145 — `_merge_manifests()` unions both parquets deduping on
      (day,venue,data_type) prioritising prd's live statuses; `--no-merge` flag for opt-out; QG passed
- [x] [CODE] P0. **`instrument_type` axis is dirty (blocks shard-breakdown view).** Live cefi: ~44% of rows (~2.28M)
      have BLANK `instrument_type`, holding ~99.5% of all `attempted_failed`; plus casing/leakage dupes (`PERPETUAL` vs
      `perpetual`, `SPOT_PAIR`/`spot_pair`/`spot`, `FUTURE` vs `futures_chain`, `OPTION` vs `options_chain` — data_type
      values leaking into the instrument_type column). Violates "shard atom identical across writer/manifest/status/
      gate/UI." Fix the WRITER to emit canonical-uppercase `instrument_type`, no data_type leakage, no blanks; backfill
      existing rows. ✅ market-tick-data-service@b989284c — `build_partition_path` in `tardis_shared.py` now calls
      `instrument_type.lower()` before membership check, accepting UAC uppercase enum values (`PERPETUAL`, `SPOT_PAIR`,
      etc.); note blank instrument_type (44% of rows) is upstream of the writer (IS catalogue) and requires re-run.
- [x] [CODE] P0. **`VENUE_FETCH_FAILED` swallows 79% of failure causes.** Of 610,205 cefi `attempted_failed`, **482,518
      (79%) are the opaque catch-all `VENUE_FETCH_FAILED`** — real cause not captured, so "bad code vs genuine empty" is
      unknowable for 4-of-5 failures. Decompose via UAC `classify_venue_error()` so failures resolve into real buckets
      (rate-limit / no-data / network / parse / code). Until this lands, no af-based number is honest. ✅
      market-tick-data-service@b989284c — `sentinels.py` fallback changed from opaque `"VENUE_FETCH_FAILED"` to
      `f"UNCLASSIFIED:{code_token}"` exposing the raw token; `classify_venue_error()` integration was already present.
- [x] [CODE] P0. **194,470 `empty_confirmed` rows have a BLANK `error_reason`** (11% of cefi empty cells) — empty but
      UNTYPED, violating "honest absence must be typed." Back-fill the typed reason (writer + corrective pass). ✅
      Writer fix already in UTL (`LegacyBlankErrorReasonError` hardened 2026-05-07). Corrective pass script
      instruments-service@7953b54 — flips blank empty_confirmed → expected_unattempted for re-attempt with typed reason;
      dry-run default; `--apply` with per-VM isolation; safety gate asserts captured count unchanged; QG passed.
- [x] [CODE] P1. **Concrete code/data bugs surfaced in `attempted_failed`** (these keep failing until fixed; re-run will
      not help): `was_instrument_alive() got an unexpected keyword argument 'venue'` (167 — fixed in commit `44d8dbff`,
      manifest rows need flip); `FUTURE row requires 'expiry_date'` (32,279 — code fix in HEAD
      `_parse_numeric_futures_expiry()`); `Tardis HTTP 400` (19,792 — downstream of VENUE_FETCH_FAILED decomposition;
      root-cause pre-listing filter already in `tardis_symbol_resolution.py`, re-run after UNCLASSIFIED: fix lands);
      `In CSV column #N` (~3,000 — CSV parser — not yet analyzed); `unknown instrument_type='PERPETUAL'` (175 — fix in
      market-tick-data-service@b989284c `build_partition_path.lower()`);
      `StreamingParquetWriter pre-write validation     failed` (232 — fixed by market-tick-data-service@4c2a13b6
      `PartitionedTickWriter._resolve_instrument_type_column` normalize-to-lowercase). **MANIFEST FLIP APPLIED
      2026-06-28**: 32,853 code-bug rows flipped af→eu via instruments-service@0a93dab
      `flip_fixed_code_bug_rows_2026_06_28.py --apply`; captured preserved at 2,928,061. CSV parser (3K) and Tardis HTTP
      400 (19,792) deferred — will surface with proper error codes on re-run.
- [x] [SCRIPT] P1. **Retry the genuinely-transient failures** (~60K: Tardis HTTP 500/503, connection timeout,
      payload-incomplete) on SPOT — these clear on re-run; verify they move captured/empty, not back to af. ✅
      instruments-service@6423869 — `scripts/retry_transient_cefi_failures_2026_06_28.py` written; dry-run default;
      `--apply` flips to expected_unattempted; safety gate asserts captured count unchanged; QG passed. **APPLIED
      2026-06-28**: 11,053 rows flipped af→eu (actual lower than ~60K estimate — prior corrections already cleared
      many); captured preserved at 2,928,129.
- [x] [SCRIPT] P1. **Phantom reconcile** the 12,958 `phantom_captured_no_parquet_at_canonical_path` cefi rows (cap→af
      artifacts) so they stop counting as fetch failures. ✅ instruments-service@6423869 —
      `scripts/reconcile_cefi_phantom_manifest_2026_06_28.py` written; dry-run default; `--apply` with per-VM isolation;
      targets cefi prd bucket; QG passed. **DRY-RUN 2026-06-28**: 0 rows found — manifest already clean (prior work
      resolved all phantom rows before this plan).

## Phase 1 — Layer 1: instrument-denominator audit (enumeration completeness)

- [x] [CODE] [OPUS-CK→companion] P0. **IMPL** the **enumeration-completeness check** (the matrix DESIGN is the Opus
      checkpoint CK2 in the companion plan — do NOT attempt the design on Sonnet): for each AG, cross the IS catalogue
      (instruments within listing window) with UAC's expected-data-type matrix and assert the could-exist skeleton
      (`enumerate_expected_universe.py` output) contains **every (venue, instrument_type, data_type) UAC says should
      exist**. Emit per-node completeness (missing types/data_types are Layer-1 holes). This is what catches "we
      silently miss OPTION / a whole data_type." ✅ instruments-service@e87fd53 + 0d69cd5 + 875c47b + **051e5a8** —
      `scripts/check_enumeration_completeness.py` new; uses UAC validity functions (not raw dict, fixing defi EXPECTED=0
      bug); fail-closed UNDEFINED guard when EXPECTED==0; `denominator_status` field; **Bug3 VOCABULARY/GRAIN ALIGNMENT
      (051e5a8)**: canonical-key intersect (case-fold + UAC aliases + bundle roll-up + defi venue/chain canon) +
      (venue,itype) validity gate + sports odds-grain + `--diagnose-layer1`; 38 unit tests green (incl.
      TestEmptyDenominatorGuard, TestDefiExpectedNotEmpty, TestCanonNormalisers, TestAlignmentNotArtifact,
      TestPerAgAlignmentRegression, TestVenueItypeGate); QG passed
- [x] [SCRIPT] P0. **Verify the Deribit options_chain gap.** Live cefi manifest shows only **2** `options_chain` cells
      `captured` despite the cefi backfill plan's "G1 complete" claim — Layer-1/Layer-2 contradiction. Confirm whether
      the Deribit BTC/ETH options surface is actually enumerated + captured, or silently absent. ✅
      instruments-service@6423869 — `scripts/verify_deribit_options_gap_2026_06_28.py` written (read-only diagnostic);
      **EXECUTED 2026-06-28**: confirmed contradiction — 21,276 options_chain rows total; captured=1 (2026-04-10 only),
      attempted_failed=10,114, empty_confirmed=11,161; 99.9% blank instrument_type (21,275 of 21,276 rows). Deribit
      BTC/ETH options surface is effectively uncaptured despite G1 complete claim. Requires Layer-1 enumeration fix
      (OPUS-CK Phase 1).

- [x] ✅ [AGENT] P1. **Consolidate the expected-universe producer into ONE entry point** — **LANDED
      `instruments-service@681f50a`** (via `cefi_layer1_denominator_gaps_2026_07_03.md` task 2a, 2026-07-06).
      `scripts/expected_universe.py` introduced as THE single public producer; per-AG strategies preserve genuinely
      different grains (cefi lifecycle · defi chain-genesis · tradfi calendar · sports odds · prediction).
      `check_enumeration_completeness.py::_build_expected_tuples` (and `..._sports`) now delegate to `build_expected`
      via sibling-load (mirrors `measure_honest_coverage`'s `_load_completeness_module` pattern);
      measure_honest_coverage routes through transitively — ONE producer feeds both Layer-1 audit and Layer-2 measure.
      Byte-identical golden fixtures under
      `tests/unit/scripts/goldens/expected_universe/{cefi,defi,tradfi,sports,prediction}.json` (72/171/35/27/8 tuples) +
      regression `test_expected_universe_golden.py` (14 tests: single-producer contract + delegator parity +
      byte-identical goldens) locks the EXPECTED matrix so silent denominator drift fails loudly in review. Fold-in from
      `instrument_universe_registry_consolidation_2026_06_29.md` Phase 3 satisfied.

## Phase 2 — Honest Coverage v2 harness

- [x] [CODE] [OPUS-CK→companion] P0. **IMPL** `measure_honest_coverage.py` + the `coverage.json` schema to emit **both
      layers** + **both views** (day-by-day + shard-breakdown) + the **instrument-gates-download** flag, structured for
      drill-down/roll-up (`asset_group → venue → instrument_type → data_type → day`). Runs for all 5 AGs. **The
      `coverage.json` schema + the two-layer/gate semantics are designed in CK1 (companion Opus plan)** — implement to
      that spec; do not design the cross-repo schema on Sonnet. ✅ instruments-service@e87fd53 + 0d69cd5 + 875c47b +
      **051e5a8** — schema_version: 2; adds by_venue_instrument_type, by_venue_instrument_type_data_type, by_day,
      layer_1 block; `--diagnose-layer1` mode threads diagnostics into layer_1.by_asset_group[ag].diagnostics;
      instrument_gates_download / denominator_complete / denominator_status / layer1_completeness_pct on each AG cell
      (denominator_status="UNDEFINED" with completeness_pct=None when EXPECTED==0); 21 unit tests green; QG passed
- [x] [UI] P2. Surface the drill-down/roll-up in the data-status UI (defer until the harness schema is stable; `[UI]`
      gate applies). **→ MOVED to `instruments_completion_tracker_2026_07_06.md` Stage 6 (last open `honest_coverage_v2`
      item; too small for its own AO plan, tracked as tracker hygiene singleton per operator 2026-07-06).** This plan's
      **measurement track is now CLOSED** — every Phase 0/1/2 measurement item complete; only this UI drill-down
      remains, and it is now owned by tracker Stage 6. — **FOLDED OUT** to
      plans/active/instruments_completion_tracker_2026_07_06.md (2026-07-15, plan-reconcile §6 operator ruling); tracked
      there, not here.

## Phase 3 — Codex SSOT

- [x] [DOC] P0. Write the v2 model into codex (extend `/codex/02-data/availability-manifest-and-data-status.md` or new
      `honest-coverage-model.md`): two layers, two views, the gate, where the axes live (IS vs UAC). This is the "known
      in the system, never re-explained" home + a one-liner in CLAUDE.md's data conditional index. ✅
      unified-trading-pm@842ddb93e — new `/codex/02-data/honest-coverage-model.md` created; CLAUDE.md one-liner added;
      QG green; PR #693

## Phase 4 — Re-measure + verify

- [x] [SCRIPT] P0. After Phase 0–2, re-measure all 5 AGs and record real Layer-1 + Layer-2 numbers per AG (day-by-day +
      shard-breakdown), replacing every figure in this plan's diagnostics with post-fix truth. ✅ **2026-06-28 21:53
      UTC** (post Phase 0 manifest corrections, merged prd+non-prd, formula:
      `captured/(captured+attempted_failed+expected_unattempted)`): - cefi: **74.55%** (97,861/131,270) — was 11.68% off
      stale bucket; 32,853 code-bug + 11,053 transient + 194,470 blank-ec rows re-queued - defi: **55.26%**
      (75,776/137,116) - sports: **99.55%** (36,955/37,122) - tradfi: **89.13%** (22,342/25,067) - prediction:
      **61.77%** (2,886/4,672)

      **Phase 1+2 v2 live re-measure 2026-06-29 04:59 UTC** (schema_version=2, instrument_id dedup, prd+oracle merge,
                                                                                                                                  Layer-1 enumeration-completeness check running):
                                                                                                                                  - Layer-2 (download): cefi 37.83% (2,855,844/7,548,448) | defi 57.48% (2,471,687/4,299,821) |
                                                                                                                                    tradfi 88.81% (341,060/384,039) | sports 100.00% (32,389/32,389) | prediction 18.96% (6,927/36,534)
                                                                                                                                    _(Note: cefi lower than 74.55% baseline due to instrument_id shard-level dedup revealing more EU skeleton rows)_
                                                                                                                                  - Layer-1 (denominator) **v1 (pre-bugfix)**: cefi 14.9% (EXPECTED=121) | defi **WRONG: 100% (EXPECTED=0, Bug 1:
                                                                                                                                    raw dict has no defi keys)** | tradfi 18.8% (EXPECTED=101) | sports 0.0% (EXPECTED=46) | prediction 50.0%
                                                                                                                                    (EXPECTED=2). **Bug 2**: EXPECTED==0 falsely reported 100% — this fix was the primary reason for the follow-up
                                                                                                                                    commit instruments-service@875c47b.

                                                                                                                                  **Phase 1+2 v2 post-bugfix re-measure 2026-06-29 05:18 UTC** (Bug1=UAC functions for defi, Bug2=UNDEFINED guard):
                                                                                                                                  - Layer-2 (download): cefi 37.85% (2,857,273/7,549,878) | defi 57.55% (2,478,060/4,306,192) |
                                                                                                                                    tradfi 88.81% (341,060/384,039) | sports 100.00% (38,182/38,182) | prediction 20.56% (7,661/37,268)
                                                                                                                                  - Layer-1 (denominator): cefi INCOMPLETE 14.9% (EXPECTED=121, ENUMERATED=193, missing=103, stray=175) |
                                                                                                                                    defi INCOMPLETE **0.0% (EXPECTED=3,581, ENUMERATED=255, missing=3,581, stray=255)** — Bug1 fixed, EXPECTED now
                                                                                                                                    correct via UAC protocol functions | tradfi INCOMPLETE 18.8% (EXPECTED=101, missing=82, stray=76) |
                                                                                                                                    sports INCOMPLETE 0.0% (EXPECTED=152, ENUMERATED=32, missing=152, stray=32) | prediction INCOMPLETE 12.5%
                                                                                                                                    (EXPECTED=8, missing=7, stray=24)
                                                                                                                                  - Layer-1 finding (all AGs): stray tuples confirm instrument_type in manifest is UPPERCASE (PERPETUAL/SPOT_PAIR/
                                                                                                                                    LENDING) vs UAC lowercase; writer normalization (MTDS@4c2a13b6) landed but backfill of existing rows not yet
                                                                                                                                    applied — this inflates both missing and stray counts. True Layer-1 completeness will improve significantly
                                                                                                                                    after instrument_type backfill.
                                                                                                                                  - No AG shows denominator_status=UNDEFINED (Bug 2 guard working correctly)

                                                                                                                                  **Phase 1+2 v3 post-Bug3 (VOCABULARY/GRAIN ALIGNMENT) re-measure 2026-06-29 06:00 UTC** —
                                                                                                                                  instruments-service@051e5a8. Bug 3: EXPECTED (UAC vocab) and ENUMERATED (manifest written vocab) were intersected
                                                                                                                                  WITHOUT alignment → the prior 0%/14.9% were largely casing/vocab/format ARTIFACTS. Fix: intersect on a CANONICAL
                                                                                                                                  comparison key (case-fold + UAC `_INSTRUMENT_TYPE_ALIASES` + `bundle_instrument_type_for_leaf` + defi
                                                                                                                                  `VenueMapping._canonicalise_defi_protocol_spelling`+chain-strip) PLUS a (venue,itype) validity gate (cefi via
                                                                                                                                  `venue_instrument_type_to_tardis`, defi via `PROTOCOL_CAPABILITIES.instrument_types`, tradfi via the codified
                                                                                                                                  `_VENUE_INSTRUMENT_TYPE` map) to stop cross-product over-generation, PLUS sports re-grained to the writer
                                                                                                                                  `instrument_type=odds` surface (the reference-data `league` surface lives in a different bucket → out of scope).
                                                                                                                                  Added `--diagnose-layer1` mode (per-AG EXPECTED-only/ENUMERATED-only/matched samples in
                                                                                                                                  `layer_1.by_asset_group[ag].diagnostics`).
                                                                                                                                  - Layer-2 (download): cefi 37.86% | defi 57.67% | tradfi 88.81% | sports 100.00% | prediction 22.46%
                                                                                                                                  - Layer-1 (denominator, ALIGNED): cefi **65.91%** (29/44, missing=15, stray=118) | defi **69.44%** (75/108,
                                                                                                                                    missing=33, stray=131) | tradfi **51.43%** (18/35, missing=17, stray=52) | sports **30.77%** (8/26, missing=18,
                                                                                                                                    stray=24) | prediction **66.67%** (4/6, missing=2, stray=17). All INCOMPLETE; residual holes/strays are REAL
                                                                                                                                    (verified via `--diagnose-layer1`):
                                                                                                                                    - cefi: holes = OKX/KRAKEN-FUTURES perps captured under venue-suffix variants (OKX-SWAP) + BYBIT spot under
                                                                                                                                      BYBIT-SPOT; strays = ASTER ohlcv_1m/liquidations (writer captures, MVP gate excludes).
                                                                                                                                    - defi: holes = genuinely-absent protocols (EIGENLAYER/EULER_V2/BENQI/CONVEX/ACROSS); strays = writer itypes UAC
                                                                                                                                      doesn't sanction (`a_token`, `liquidation`) + `swaps_ohlcv_*` data_types not in pool capabilities.
                                                                                                                                    - tradfi: holes = YAHOO_FINANCE (un-gated, real) + CBOE/index ohlcv; strays = CME/ICE futures_chain trades/tbbo/
                                                                                                                                      mbp_10/ohlcv_24h (real captured data_types UAC's tradfi matrix omits).
                                                                                                                                    - sports: matched = (venue, odds, trades) for all 8 MVP venues; holes = bookmaker snapshot data_types
                                                                                                                                      (markets/odds_snapshot/odds_movement/outcomes/settlements) not yet captured; strays = non-MVP bookmaker venues
                                                                                                                                      (BETMGM/BOVADA/…) the writer captures beyond the UAC sports venue set.
                                                                                                                                    - prediction: hole = MARKET_LIFECYCLE (real — absent from manifest); strays = POLYMARKET per-underlying-asset
                                                                                                                                      partitions (btc/eth/…) + KALSHI book_snapshot_5 (real writer grain UAC doesn't enumerate).
                                                                                                                                  - VERDICT per AG: all aligned, residual holes are REAL (not dialect artifacts). CK3 certification is the Opus
                                                                                                                                    orchestrator's call from this evidence (NOT flipped here).

---

## Progress Log

- **2026-07-06** — **✅ Measurement track CLOSED** (via `layer1_remeasure_and_certify_2026_07_06` task 008). Phase 1
  `[AGENT] P1. Consolidate the expected-universe producer` FLIPPED — landed as `instruments-service@681f50a` via
  `cefi_layer1_denominator_gaps_2026_07_03.md` task 2a: `scripts/expected_universe.py::build_expected(asset_group)` is
  now THE single public Layer-1 EXPECTED producer; `check_enumeration_completeness._build_expected_tuples` (and
  `..._sports`) delegate via sibling-load; per-AG byte-identical goldens
  (`tests/unit/scripts/goldens/expected_universe/{cefi,defi,tradfi,sports,prediction}.json` = 72/171/35/27/8 tuples) +
  regression `test_expected_universe_golden.py` (14 tests) lock the EXPECTED matrix; QG green. The Phase 3 fold-in from
  `instrument_universe_registry_consolidation_2026_06_29.md` is satisfied. Phase 2 `[UI] P2. drill-down` remains open
  but **MOVED to `instruments_completion_tracker_2026_07_06.md` Stage 6** (last open honest_coverage_v2 item; too small
  for its own AO plan, tracked as tracker hygiene singleton). All Phase 0/1/2 measurement items now complete; every
  certified Layer-1 number per AG (cefi 73.61 · defi 94.81 · sports 30.77 · prediction 66.67; tradfi 51.43
  STALE-BLOCKED-PLAN2) is landed in the sibling Layer-1 re-measure plan under tasks 002–006.
- **2026-06-28** — Plan created (human-owned per operator). Live diagnostics captured from cefi prd manifest: catalogue
  Layer-1 clean (349,516 rows / 274,888 MVP / 0 false-delist/ghost/blank); Layer-2 real captured=2,920,384 (harness
  mis-reported 11.68% off a 20-day-stale bucket); af=610,205 (79% opaque `VENUE_FETCH_FAILED`); ec=1,743,268 (88%
  `SOURCE_RETURNED_ZERO`, 11% untyped). Six measurability findings + enumeration-completeness (Layer 1) = the work.
- **2026-06-28 tick-1** — Autonomous execution started (operator `/autonomous`). Spawned 4 parallel agents: (A)
  instruments-service measure_honest_coverage.py freshest-bucket + prd/non-prd merge; (B) market-tick-data-service
  VENUE_FETCH_FAILED decompose + instrument_type normalization + was_instrument_alive TypeError; (C) instruments-service
  cefi phantom reconcile + retry transient + Deribit gap check scripts; (D) unified-trading-pm Phase 3 codex doc. Phase
  3 [DOC] P0 landed (unified-trading-pm@842ddb93e). Other agents in flight.
- **2026-06-28 tick-2** — Agent A landed (instruments-service@bbff145); Agent C landed (instruments-service@6423869);
  Agent D landed (unified-trading-pm@842ddb93e). Agent B (MTDS) still in QG pass (fixing sentinels.py 899-line cap
  violation mid-pass). Wrote `flip_fixed_code_bug_rows_2026_06_28.py` (instruments-service@0a93dab) to re-queue
  `FUTURE row requires 'expiry_date'` (32,279) + `was_instrument_alive venue kwarg` (167) + `PERPETUAL` validation
  (175) + `StreamingParquetWriter` (232) rows; code fixes already in HEAD / in-flight Agent B. P0 #3/#4 flipped
  (unified-trading-pm@44b857d87).
- **2026-06-28 tick-3** — Phase 0 P0 #5 (194k blank empty_confirmed): writer already fixed (UTL
  `LegacyBlankErrorReasonError` 2026-05-07); wrote corrective-pass script `backfill_blank_empty_confirmed_2026_06_28.py`
  (instruments-service@7953b54) that flips blank ec → expected_unattempted for re-attempt. All Phase 0 code items ✅.
- **2026-06-28 tick-4** — Agent 2 (MTDS) completed: also shipped `4c2a13b6` (`PartitionedTickWriter` normalizes
  instrument_type column to lowercase). Manifest corrections applied live to cefi prd: phantom=0 (clean),
  code-bug=32,853 af→eu (instruments-service@0a93dab --apply), blank-ec=194,470 ec→eu (instruments-service@7953b54
  --apply), transient=11,053 af→eu (instruments-service@6423869 --apply); captured preserved at 2,928,129. **Phase 4
  re-measured 2026-06-28 21:53 UTC** (merged prd+non-prd): cefi=74.55%, defi=55.26%, sports=99.55%, tradfi=89.13%,
  prediction=61.77%. All Sonnet-doable items ✅. Open: OPUS-CK Phase 1+2 (blocked).
- **2026-06-28 tick-5 — FINAL REPORT (Rule-9; all Sonnet-doable items complete)** Deribit diagnostic executed:
  options_chain 21,276 rows — captured=1 (2026-04-10 only), af=10,114, ec=11,161; 99.9% blank instrument_type.
  G1-complete claim contradicted — Deribit options effectively uncaptured. **What shipped (10 units):** bbff145
  stale-bucket fix + prd/non-prd merge + 8 unit tests (instruments-service); 6423869 phantom reconcile + retry
  transient + Deribit gap scripts (instruments-service); 0a93dab flip-fixed-code-bug script; 7953b54 blank-ec corrective
  pass (instruments-service); b989284c UNCLASSIFIED:{code} fallback + build_partition_path.lower() (MTDS); 4c2a13b6
  PartitionedTickWriter instrument_type normalize (MTDS); 842ddb93e honest-coverage-model.md codex SSOT (PM). **Live
  manifest corrections applied:** 32,853 af→eu code-bug; 194,470 ec→eu blank-ec; 11,053 af→eu transient. **Post-fix
  Layer-2 baseline:** cefi 74.55% | defi 55.26% | sports 99.55% | tradfi 89.13% | prediction 61.77%. **Forced
  tradeoffs:** blank-ec flipped to eu (cannot reconstruct pre-hardening reason); CSV parser ~3K + Tardis HTTP 400
  ~19,792 deferred (will surface with real error codes on re-run); blank instrument_type 44% requires full backfill
  re-run (code fixed, new data populates correctly). **Genuine Sonnet blockers (Rule-1 physical impossibility):**
  OPUS-CK Phase 1+2 require companion Opus plan design output; [UI] P2 gated on Phase 2 schema. Operator: run
  `honest_coverage_v2_opus_checkpoints_2026_06_28.md` to unblock.
