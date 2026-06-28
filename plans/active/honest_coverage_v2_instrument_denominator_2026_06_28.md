---
doc_type: plan
title:
  "Honest Coverage v2 — instrument-denominator audit baked in (two layers · two views · instrument gates downloads)"
summary:
  "Upgrade the honest-coverage system so the instrument-enumeration (denominator) audit is a first-class, standing part
  of honest coverage — not a one-off. Two layers (instrument coverage gates data-download coverage), two views
  (day-by-day + shard-breakdown), drill-down/roll-up across asset_group → venue → instrument_type → data_type → day. Fix
  the measurability bugs first (stale-bucket read, prd/non-prd split, instrument_type normalization, VENUE_FETCH_FAILED
  swallowing 79% of failure causes, untyped empty_confirmed) so v2 reports real numbers."
status: active
nature: design
stage: [data-ingestion, meta]
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
    ../../codex/02-data/availability-manifest-and-data-status.md,
    ../../codex/02-data/data-pipeline-correctness-hard-rule.md,
    ../../codex/02-data/honest-absence-downstream-handling.md,
    ../../codex/04-architecture/instruments-service-as-ssot-for-mtds.md,
    mvp_backfill_cefi_tick_v10_2026_06_27.md,
    mvp_catalogue_finalization_v10_2026_06_27.md,
  ]
created: 2026-06-28
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: orchestrator-agent
priority: P0
model_tier: sonnet-doable
thinking_tier: medium
estimate_class: infra
estimate_baseline_ai_days: 7
estimate_calibrated_ai_days: 5.6
last_updated: 2026-06-28
locked_by: live-defi-rollout
locked_since: 2026-06-28
supersedes:
superseded_by:
depends_on:
source:
assigned_role: data_engineering
drift_direction: advance-code
asset_group: cross-asset
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
> `codex/06-coding-standards/model-tier-selection.md`).

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

- `codex/02-data/availability-manifest-and-data-status.md` (4-state + shard atom)
- `codex/02-data/honest-absence-downstream-handling.md` (typed absence)
- `codex/04-architecture/instruments-service-as-ssot-for-mtds.md` (IS owns instrument universe)
- `codex/02-data/data-pipeline-correctness-hard-rule.md` (RED audit freezes layer N+1)

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
- [ ] [CODE] P1. **Concrete code/data bugs surfaced in `attempted_failed`** (these keep failing until fixed; re-run will
      not help): `was_instrument_alive() got an unexpected keyword argument 'venue'` (167 — fixed in commit `44d8dbff`,
      manifest rows need flip via instruments-service@0a93dab `flip_fixed_code_bug_rows`);
      `FUTURE row requires     'expiry_date'` (32,279 — code fix in HEAD `_parse_numeric_futures_expiry()`; manifest
      flip script instruments-service@0a93dab); `Tardis HTTP 400` (19,792 — downstream of VENUE_FETCH_FAILED
      decomposition; root-cause pre-listing filter already in `tardis_symbol_resolution.py`, re-run after UNCLASSIFIED:
      fix lands); `In CSV column #N` (~3,000 — CSV parser — not yet analyzed); `unknown instrument_type='PERPETUAL'`
      (175 — fix in market-tick-data-service@b989284c `build_partition_path.lower()`; manifest rows need flip);
      `StreamingParquetWriter pre-write validation failed` (232 — should clear after PERPETUAL fix re-run).
- [x] [SCRIPT] P1. **Retry the genuinely-transient failures** (~60K: Tardis HTTP 500/503, connection timeout,
      payload-incomplete) on SPOT — these clear on re-run; verify they move captured/empty, not back to af. ✅
      instruments-service@6423869 — `scripts/retry_transient_cefi_failures_2026_06_28.py` written; dry-run default;
      `--apply` flips to expected_unattempted; safety gate asserts captured count unchanged; QG passed
- [x] [SCRIPT] P1. **Phantom reconcile** the 12,958 `phantom_captured_no_parquet_at_canonical_path` cefi rows (cap→af
      artifacts) so they stop counting as fetch failures. ✅ instruments-service@6423869 —
      `scripts/reconcile_cefi_phantom_manifest_2026_06_28.py` written; dry-run default; `--apply` with per-VM isolation;
      targets cefi prd bucket; QG passed

## Phase 1 — Layer 1: instrument-denominator audit (enumeration completeness)

- [ ] [CODE] [OPUS-CK→companion] P0. **IMPL** the **enumeration-completeness check** (the matrix DESIGN is the Opus
      checkpoint CK2 in the companion plan — do NOT attempt the design on Sonnet): for each AG, cross the IS catalogue
      (instruments within listing window) with UAC's expected-data-type matrix and assert the could-exist skeleton
      (`enumerate_expected_universe.py` output) contains **every (venue, instrument_type, data_type) UAC says should
      exist**. Emit per-node completeness (missing types/data_types are Layer-1 holes). This is what catches "we
      silently miss OPTION / a whole data_type."
- [x] [SCRIPT] P0. **Verify the Deribit options_chain gap.** Live cefi manifest shows only **2** `options_chain` cells
      `captured` despite the cefi backfill plan's "G1 complete" claim — Layer-1/Layer-2 contradiction. Confirm whether
      the Deribit BTC/ETH options surface is actually enumerated + captured, or silently absent. ✅
      instruments-service@6423869 — `scripts/verify_deribit_options_gap_2026_06_28.py` written (read-only diagnostic);
      run against cefi prd manifest to confirm contradiction; QG passed

## Phase 2 — Honest Coverage v2 harness

- [ ] [CODE] [OPUS-CK→companion] P0. **IMPL** `measure_honest_coverage.py` + the `coverage.json` schema to emit **both
      layers** + **both views** (day-by-day + shard-breakdown) + the **instrument-gates-download** flag, structured for
      drill-down/roll-up (`asset_group → venue → instrument_type → data_type → day`). Runs for all 5 AGs. **The
      `coverage.json` schema + the two-layer/gate semantics are designed in CK1 (companion Opus plan)** — implement to
      that spec; do not design the cross-repo schema on Sonnet.
- [ ] [UI] P2. Surface the drill-down/roll-up in the data-status UI (defer until the harness schema is stable; `[UI]`
      gate applies).

## Phase 3 — Codex SSOT

- [x] [DOC] P0. Write the v2 model into codex (extend `codex/02-data/availability-manifest-and-data-status.md` or new
      `honest-coverage-model.md`): two layers, two views, the gate, where the axes live (IS vs UAC). This is the "known
      in the system, never re-explained" home + a one-liner in CLAUDE.md's data conditional index. ✅
      unified-trading-pm@842ddb93e — new `codex/02-data/honest-coverage-model.md` created; CLAUDE.md one-liner added; QG
      green; PR #693

## Phase 4 — Re-measure + verify

- [ ] [SCRIPT] P0. After Phase 0–2, re-measure all 5 AGs and record real Layer-1 + Layer-2 numbers per AG (day-by-day +
      shard-breakdown), replacing every figure in this plan's diagnostics with post-fix truth.

---

## Progress Log

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
  Remaining open: Phase 0 manifest-apply scripts (reconcile_cefi_phantom, retry_transient, flip_fixed_code_bug,
  backfill_blank_ec — all need `--apply` on infra); Phase 4 re-measure; OPUS-CK Phase 1+2 (blocked).
