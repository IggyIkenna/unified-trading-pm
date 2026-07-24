---
doc_type: plan
title: Expected-unattempted propagation chain — instruments → MTDS → MDPS → features → ML
summary:
status: complete
nature: record
asset_group: [infrastructure]
stage: [meta]
repos:
  [
    deployment-api,
    deployment-service,
    features-service,
    instruments-service,
    market-data-processing-service,
    market-tick-data-service,
  ]
scope: [engineer, admin]
tags: []
related:
  [
    manifest_evolution_SUPERSEDED_2026_05_21,
    manifest_cross_asset_rescan_design_2026_05_08,
    writegate_honest_coverage_endtoend_2026_05_06,
    expected_universe_v2_design_2026_05_08,
  ]
created: 2026-05-12
priority: P0
last_updated: 2026-05-12
parent: manifest_evolution_SUPERSEDED_2026_05_21
migrated_from: plans/active/issues/expected_unattempted_propagation_gap_2026_05_12.md
locked_by: live-defi-rollout
locked_since: 2026-05-12
estimate_class: brand-new
estimate_baseline_ai_days: 6.6
estimate_calibrated_ai_days: 6.6
estimate_calibration_note: "+1.1 added 2026-05-12 for Phase 1.5 (sports fixture SSOT fix ~0.8) + Phase 2 extension (MDPS
  forward-fill contract ~0.3).

  brand-new class, multiplier 1.0×.

  "
effective_concurrent_slots: 4
model_tier: sonnet-doable
thinking: high
parent_epic: manifest_master
---

## Deferred work — migrated to:

| Item                                                                                              | Successor plan                                                                                                                                                                                |
| ------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Phase 6 validation — prod MTDS/MDPS run to verify `expected_unattempted` rows generated correctly | [`issues/expected_unattempted_validation_pending_phase3_2026_05_19.md`](../active/issues/expected_unattempted_validation_pending_phase3_2026_05_19.md) — re-verify after Phase 3 MTDS VMs run |
| Phase 3 sports + features per-shard upstream `capture_status` branching                           | [`writegate_honest_coverage_endtoend_2026_05_06.md`](../active/writegate_honest_coverage_endtoend_2026_05_06.md) Phase 6.x                                                                    |
| DeFi classifier catalog crossref (deferred P2)                                                    | [`issues/expected_unattempted_propagation_gap_2026_05_12.md`](../active/issues/expected_unattempted_propagation_gap_2026_05_12.md) — post-live-cutover                                        |

# Expected-unattempted propagation chain — instruments → MTDS → MDPS → features → ML

## Why

The manifest dependency chain does not propagate `expected_unattempted` through services at runtime. Every service runs
its own pre-flight but ignores upstream manifest state. Results:

1. **MTDS** writes `attempted_failed` for instruments that instruments-service says don't exist → false-positive phantom
   rows inflate phantom counts; "0 phantoms" target is unreachable.
2. **MDPS** reads MTDS manifest via `DependencyChecker` but writes NO row when skipping a shard → invisible gaps in
   manifest; data-status panel shows nothing for legitimately-skipped shards.
3. **Features** filters by `subscription_list` config per module but writes NO row for non-MVP instruments → can't
   distinguish "not in scope" from "failed to compute" from "never attempted".
4. **ML** same gap as features.

**Complement to G3 enumerator** (`expected_universe_v2_design_2026_05_08`): G3 is a one-time batch script that
pre-populates `expected_unattempted` for historical data from the instruments catalog. THIS PLAN covers runtime
propagation — every future run correctly records `expected_unattempted` at the moment a shard is skipped. Both are
required; G3 fills history, this plan prevents re-accumulation.

**Pre-condition for `--apply-flips`**: reconciliation `--apply-flips` on MTDS/MDPS/features manifests is BLOCKED until
Phases 1–4 land. Running `--apply-flips` before will flip false-positive `attempted_failed` rows to `empty_confirmed`,
masking the root cause.

## Scope + dependency order

```
Phase 0: UAC reason + UTL cross-service reader (SERIAL — foundation)
    ↓
Phase 1: MTDS pre-flight wired to instruments-service manifest (SERIAL — root)
    ↓
Phase 2: MDPS record_expected_unattempted on skip (SERIAL — depends on Phase 1)
    ↓
Phase 3: Features per-module expected_unattempted + MVP scope constant (PARALLEL per module)
Phase 4: ML services expected_unattempted + ML scope constant (PARALLEL with Phase 3)
    ↓
Phase 5: Manifest reconciliation scripts — dry-run baseline + apply-flips in dependency order
    ↓
Phase 6: Validation gate — phantom count target + manifest accuracy sign-off
```

## Repos touched

| Repo                                    | Scope                                                                                                               |
| --------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| `unified-api-contracts`                 | Phase 0A: new `EXPECTED_OUTSIDE_PROCESSING_SCOPE` + `EXPECTED_UPSTREAM_EMPTY` EmptyConfirmedReason values           |
| `unified-trading-library`               | Phase 0B: `read_upstream_manifest()` helper; Phase 2: `BaseDependencyChecker.record_expected_unattempted_on_skip()` |
| `market-tick-data-service` (MTDS)       | Phase 1: instruments-service pre-flight in batch orchestrator                                                       |
| `market-data-processing-service` (MDPS) | Phase 2: DependencyChecker wiring                                                                                   |
| `features-service`                      | Phase 3: per-module batch handler wiring                                                                            |
| `ml-training` + `ml-inference-service`  | Phase 4: ML scope wiring                                                                                            |
| `instruments-service`                   | Phase 5: reconciliation script execution                                                                            |
| `unified-trading-pm`                    | This plan + plan flips                                                                                              |

---

## Phase 0 — UAC reason extension + UTL cross-service manifest reader

**model_tier**: sonnet-doable | **thinking**: medium | **Cal AI-days**: ~0.4

### Phase 0A — UAC: two new EmptyConfirmedReason values

File: `unified-api-contracts/unified_api_contracts/canonical/crosscutting/honest_coverage.py`

Add to `EmptyConfirmedReason` StrEnum (after existing `EXPECTED_KNOWN_SOURCE_GAP`):

```python
EXPECTED_OUTSIDE_PROCESSING_SCOPE = "expected_outside_processing_scope"
# Used by features/ML batch handlers when an instrument exists in instruments-service
# catalog but is not in the service's subscription_list / MVP scope config.
# Reason: not a data gap — deliberate scope exclusion.

EXPECTED_UPSTREAM_EMPTY = "expected_upstream_empty"
# Used by downstream services (MTDS, MDPS, features) when skipping a shard because
# the upstream service's manifest has capture_status in ('empty_confirmed', 'expected_unattempted').
# Reason: upstream honest-absence propagated downstream; no fetch attempted.
```

Also update `EMPTY_CONFIRMED_REASONS` closed-set dict with descriptions for both new values.

Run `assert_pipeline_mode_source_priority_round_trip` + `pytest tests/test_cassette_schema_parity.py`.

- [x] [CODE] P0. Add `EXPECTED_OUTSIDE_PROCESSING_SCOPE` + `EXPECTED_UPSTREAM_EMPTY` to UAC `EmptyConfirmedReason` +
      `EMPTY_CONFIRMED_REASONS` dict. QG + push. (uac@0457b0e — 20 total reasons; en-dash ruf001 fixed; pushed
      2026-05-12)

### Phase 0B — UTL: cross-service manifest reader helper

File: `unified-trading-library/unified_trading_library/manifest_reader_fallback.py` (or `manifest_writer.py`)

**First**: check if `ManifestReader` already supports reading an arbitrary GCS bucket by instantiating with a different
bucket param. If it does, document the pattern; no code change needed.

If NOT: add to UTL `manifest_writer.py` or a new `manifest_cross_service.py`:

```python
def read_upstream_manifest(
    upstream_bucket: str,
    project_id: str,
    asset_group: str | None = None,
    date_min: date | None = None,
    date_max: date | None = None,
) -> pd.DataFrame:
    """Read the canonical manifest parquet from an upstream service's GCS bucket.

    Returns the availability_index DataFrame filtered to the requested date range.
    Used by downstream services for pre-flight cross-service dependency checks.
    """
```

The implementation reads `gs://{upstream_bucket}/_index/availability_index.parquet` via GCS client (same ADC-based
pattern as existing ManifestWriter internals).

Add 3 unit tests (mock GCS): empty result, filtered by date, all-rows path.

- [x] [CODE] P0. Verify ManifestReader bucket parameterization OR add `read_upstream_manifest()` to UTL. QG + push.
      **Discovery (2026-05-12)**: `read_availability_index(bucket: str)` in UTL `manifest_writer.py:3257` already
      accepts any bucket name and returns the full v8-schema DataFrame. No new helper needed. Downstream services (MTDS,
      MDPS, features) call `read_availability_index(upstream_bucket)` directly. Tests in
      `tests/unit/test_manifest_completeness.py` already cover mock-GCS paths. No UTL code change; pattern documented.

---

## Phase 1 — MTDS pre-flight: instruments-service manifest read

**model_tier**: sonnet-doable | **thinking**: high | **Cal AI-days**: ~1.5

**Goal**: Before MTDS starts per-shard fetches for a batch run, read the instruments-service manifest to learn which
instruments exist and what their status is. Write `expected_unattempted` for shards that instruments-service says are
`empty_confirmed` or `expected_unattempted`, skipping the fetch entirely for those shards.

### Pre-audit (implementer must do first)

```bash
# Find instruments-service bucket names per asset_group
grep -rn "instruments.store\|instruments_store\|INSTRUMENTS_BUCKET" \
  instruments-service/instruments_service/ \
  unified-trading-library/unified_trading_library/ \
  deployment-service/configs/ \
  --include="*.py" --include="*.yaml" | grep -v .venv | head -30

# Find where MTDS batch orchestrator loops per-shard
grep -rn "record_captured\|record_failed\|record_empty\|manifest_writer" \
  market-tick-data-service/market_tick_data_service/orchestrators/ \
  market-tick-data-service/market_tick_data_service/cli/handlers/ \
  --include="*.py" | head -30

# Check if ManifestReader accepts a bucket param
grep -n "class ManifestReader\|def __init__\|bucket" \
  unified-trading-library/unified_trading_library/manifest_writer.py | head -20
```

### Implementation pattern

In the MTDS batch orchestrator (per asset_group):

```python
# At orchestrator startup (BEFORE the per-shard fetch loop)
from unified_trading_library.manifest_cross_service import read_upstream_manifest
from unified_trading_library.cloud_interface.bucket_naming import resolve_bucket_name
from unified_api_contracts.canonical.crosscutting.honest_coverage import EmptyConfirmedReason

# SSOT: resolve_bucket_name uses deployment-service/configs/cloud-providers.yaml.
# DEPLOYMENT_ENV comes from UnifiedCloudConfig (never os.getenv directly).
instruments_bucket = resolve_bucket_name(
    cloud="gcp",
    kind="instruments",
    asset_group=asset_group,
    env=cloud_config.deployment_env,
)

upstream_manifest = read_upstream_manifest(
    upstream_bucket=instruments_bucket,
    project_id=cloud_config.project_id,
    date_min=batch_date_min,
    date_max=batch_date_max,
)

# Build set of (venue, instrument_id, date) for which instruments-service has captured or empty_confirmed rows
# "captured" or "empty_confirmed" means instruments-service KNOWS about this shard → MTDS should attempt
# "expected_unattempted" or absent → MTDS should write expected_unattempted and skip
upstream_known: set[tuple[str, str, date]] = {
    (row.venue, row.instrument_id, row.date)
    for row in upstream_manifest.itertuples()
    if row.capture_status in ("captured", "empty_confirmed")
}

# For each MTDS shard (venue, instrument_id, data_type, date) NOT in upstream_known:
for shard in planned_shards:
    if (shard.venue, shard.instrument_id, shard.date) not in upstream_known:
        manifest_writer.record_expected_unattempted(
            ...,
            reason=EmptyConfirmedReason.EXPECTED_UPSTREAM_EMPTY,
        )
        continue
    # ... existing fetch logic
```

**Bucket name verification**: `resolve_bucket_name(cloud="gcp", kind="instruments", asset_group=ag, env=env)` is the
canonical call (SSOT: `deployment-service/configs/cloud-providers.yaml`). Implementer MUST verify the `instruments` kind
key exists in cloud-providers.yaml for each asset_group. If the key is missing (instruments-service bucket not yet
registered), add it to cloud-providers.yaml as part of this phase — do NOT hardcode the bucket string inline (QG STEP
5.69 ratchet rejects inline f-string bucket lookups). Never use `os.getenv()` — get `deployment_env` from
`UnifiedCloudConfig`.

**Shard isolation**: MTDS must pass `VM_NAME` + `MANIFEST_PER_VM_SHARDS=true` for the expected_unattempted writes (same
as captured writes) to avoid multi-worker collision.

**Tests**: mock read_upstream_manifest returning 3 scenarios: all known, some unknown, none known. Assert
expected_unattempted calls for unknown shards.

- [x] [CODE] P0. Pre-audit: confirm INSTRUMENTS_BUCKET_BY_ASSET_GROUP names from cloud-providers.yaml. **Discovery
      (2026-05-12)**: `instruments-store` kind registered in `cloud-providers.yaml` lines 128-138 for all 5
      asset_groups. `resolve_bucket_name(cloud="gcp", kind="instruments-store", asset_group=ag, env=env)` is valid for
      cefi/defi/tradfi/sports/prediction. No constant needed — pattern uses canonical bucket naming SSOT.
- [x] [CODE] P0. Wire instruments-service manifest read into MTDS batch orchestrator pre-flight per above pattern. Cover
      all 5 asset_groups. Add 3 unit tests. (mtds@5717ee9 — sentinel pass emits `record_expected_unattempted` per
      expected data_type for venues in `skipped_shards`; 3 unit tests: all_dts / dt_start_gate / no_expected_dts)
- [x] [QG] P0. `cd market-tick-data-service && bash scripts/quality-gates.sh`. Push. (lint on my files clean; pre-
      existing failures in `test_tardis_stream_processor.py:B017` + `test_lst_rates_handler.py:RUF002` are foreign;
      pushed mtds@5717ee9)

---

## Phase 1.5 — Sports: fixture-as-instrument SSOT fix in classifier + pre-flight

**model_tier**: sonnet-doable | **thinking**: medium | **Cal AI-days**: ~0.8

**Goal**: For sports, the instruments-service fixture manifest is the canonical universe. A shard slot where no fixture
exists for that (league, date) should be `expected_unattempted` — not `SOURCE_RETURNED_ZERO`. A shard where a fixture
DID exist but data is missing AND there is no UAC-based source limitation (understat limited leagues, footystats
pre/post-season, UAC per-source league filter) should be `attempted_failed`, not `SOURCE_RETURNED_ZERO`.

The current classifier in `legacy_reason_classifier.py` does NOT check fixture existence — it falls through to
`SOURCE_RETURNED_ZERO` for any sports shard without a matching UAC coverage-gap reason. This over-counts "empty" and
under-counts "failed" for sports.

### Pre-audit

```bash
grep -n "fixture\|FIXTURE\|api_football\|check.*fixture\|fixture.*exist" \
  unified-trading-library/unified_trading_library/legacy_reason_classifier.py | head -20

grep -rn "fixture.*manifest\|manifest.*fixture\|check.*fixture.*shard" \
  instruments-service/instruments_service/ --include="*.py" | grep -v .venv | head -20
```

### Implementation pattern

In `_classify_sports()` (after source-coverage + known-gap + source-limitation checks, before `SOURCE_RETURNED_ZERO`
fallback):

```python
# Check fixture existence BEFORE falling through to SOURCE_RETURNED_ZERO
# If no fixture exists for this (league_id, date) → expected_unattempted (not a real slot)
if not fixture_exists_for_shard(venue, instrument_id, date, fixture_manifest):
    return "EXPECTED_UNATTEMPTED"  # slot doesn't exist in fixture universe

# Fixture exists + no UAC source limitation → attempted_failed (should have data)
return None  # caller flips to attempted_failed
```

`fixture_manifest` is a lightweight read of instruments-service `data_type=fixtures` manifest rows, cached in-process.
The classifier gains an optional `fixture_manifest: pd.DataFrame | None = None` param; callers in the reconciler pass it
in after reading instruments-service manifest for the asset_group + date range.

**Note**: this is the same pre-flight pattern as Phase 1 (MTDS reads instruments-service manifest before fetching).
Reconciler scripts should read instruments-service manifest once and pass into classifier.

- [x] [CODE] P1. Add `fixture_manifest` param to `classify_blank_reason_row()` in `legacy_reason_classifier.py`. Wire
      fixture existence check via `_fixture_exists_for_shard()` helper BEFORE `SOURCE_RETURNED_ZERO` fallback. Add 4
      unit tests (empty manifest → expected_unattempted; wrong league → expected_unattempted; fixture+limitation →
      empty_confirmed; fixture+no limitation → attempted_failed). (utl@290a4150 — test_sports_fixture_classifier.py + 4
      tests pass)
- [x] [CODE] P1. Update `reconcile_legacy_blank_to_typed_reason.py` to read instruments-service fixture manifest for the
      sports asset_group and pass it into the classifier. Add Shape (c) upgrade path. (instruments-service@715139a)
- [x] [RESEARCH] P1. Audit instruments-service manifest for transfermarkt data. **FINDING (2026-05-14 slot 4)**:
      `EXPECTED_OUTSIDE_TRANSFER_WINDOW` is NOT wired into the orchestrator PLAYER_VALUES write path. Current design:
      non-trigger dates use a cache short-circuit (`get_leagues_needing_refresh` → empty list → `_cache_hit=True`),
      which then emits `record_captured_from_counts` from cached squad data. Every date gets a `captured` row (from
      cache), NOT `expected_unattempted/EXPECTED_OUTSIDE_TRANSFER_WINDOW`. `available_at` is correctly set to write-time
      (`datetime.now(UTC)`) per UTL SSOT. **Design verdict**: intentional — player_values are slowly-changing reference
      data; caching the last-known squad is correct. `EXPECTED_OUTSIDE_TRANSFER_WINDOW` exists in UAC for future use
      (e.g. TRANSFERS entity, or if the cadence changes). No code change needed. **No per-league transfer window
      tracking in IS manifest** — the window logic lives in `get_leagues_needing_refresh()` which gates API calls but
      not manifest rows. Filed as **DESIGN NOTE** (not bug): `plans/active/issues/` if operator wants deeper audit.
- [x] [QG] P1. `cd unified-trading-library && bash scripts/quality-gates.sh`.
      `cd instruments-service && bash scripts/quality-gates.sh`. Push. UTL: 4 new tests pass
      (test_sports_fixture_classifier.py); 109 pre-existing manifest_writer failures (foreign). instruments-service: 6/6
      reconciler tests pass (instruments-service@703d36b fixed Shape-b test gap from 3a05e4f); 84 pre-existing failures
      (orchestrator_coverage, phase2d, urdi — foreign). (instruments-service@703d36b)

---

## Phase 2 — MDPS: record_expected_unattempted on skip + forward-fill semantics codification

> **⚠️ COUNTING SEMANTICS SUPERSEDED (2026-05-19)**: this phase propagates `expected_unattempted` rows correctly, but
> leaves the counting role of `expected_unattempted` unspecified. The **canonical split** is: `expected_unattempted`
> with `error_reason` startswith `"EXPECTED_"` → counts toward numerator (`expected_unattempted_known_empty`);
> non-`EXPECTED_*` reason → counts against coverage (`expected_unattempted_pending_fetch`, retried on next backfill).
> Formula SSOT: `compute_honest_coverage(CaptureStatusCounts(...))` from `unified_api_contracts`
> (`unified-api-contracts@a9891f9`). Full plan: `honest_coverage_formula_consolidation_2026_05_19.md`.

**model_tier**: sonnet-doable | **thinking**: medium | **Cal AI-days**: ~0.8 (was ~0.5; +0.3 for forward-fill semantics)

**Goal**: When MDPS's `DependencyChecker` finds upstream MTDS shard absent or empty, write `expected_unattempted` in
MDPS's own manifest rather than returning silently. ALSO codify the downstream consumption contract so MDPS knows
exactly how to behave based on upstream manifest state.

### MDPS downstream consumption contract (operator direction 2026-05-12)

The whole point of correct upstream manifest classification is that MDPS can act intelligently:

| Upstream MTDS `capture_status` | MDPS behaviour                                                           | Why                                                                                                 |
| ------------------------------ | ------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------- |
| `captured`                     | Process normally                                                         | Data exists                                                                                         |
| `empty_confirmed` + any reason | Write **zero-volume / forward-fill-last-price** bars for that time block | "Good missing" — confirmed no trades; price continuity preserved; not a data quality issue          |
| `attempted_failed`             | Write **NaN** (do NOT forward-fill)                                      | "Bad missing" — data may exist but fetch failed; downstream must not treat silence as zero-activity |
| `expected_unattempted`         | Write `expected_unattempted` in MDPS manifest + skip                     | Upstream said skip — MDPS propagates honest absence                                                 |

This contract means MDPS must READ upstream MTDS capture_status per shard, not just check presence.

- [x] [CODE] P0. Add `record_expected_unattempted` call in MDPS `DependencyChecker` when skipping due to absent/empty
      MTDS shard. Pass `manifest_writer` reference at construction if not already present. (mdps@3f70cf6 —
      `record_expected_unattempted_for_shard` in canonical_writer.py + `_record_expected_unattempted_on_skip` wired into
      process_category skip path)
- [x] [CODE] P0. Codify MDPS downstream consumption contract in MDPS orchestration_service: route MTDS `empty_confirmed`
      → zero-vol/forward-fill; `attempted_failed` → NaN; `expected_unattempted` → propagate skip. Add 4 unit tests (one
      per upstream status). (mdps@3f70cf6 — 4 unit tests in tests/unit/test_expected_unattempted_on_dep_skip.py; all
      pass)
- [x] [CODEX] P1. Add `## MDPS downstream consumption contract` section to
      `/codex/02-data/honest-absence-downstream-handling.md` documenting the 4-row table above. Reference this plan +
      writegate Phase 2.A. (pm@5ab28423 — /codex/02-data/honest-absence-downstream-handling.md § "MDPS downstream
      consumption contract")
- [x] [QG] P0. `cd market-data-processing-service && bash scripts/quality-gates.sh`. Push. (mdps@3f70cf6 — lint clean;
      19 pre-existing test failures in foreign files from UTL/UAC schema drift; my 4 Phase 2 tests pass; committed +
      pushed)

### Pre-audit

```bash
grep -n "record_expected_unattempted\|expected_unattempted\|return.*empty\|return.*None\|skip" \
  market-data-processing-service/market_data_processing_service/app/core/dependency_checker.py \
  market-data-processing-service/market_data_processing_service/app/core/orchestration_service.py \
  | head -30
```

### Implementation pattern

In `DependencyChecker` (or `BaseDependencyChecker`) when `check_shard_freshness` returns absent/empty:

```python
# Currently (gap):
if not upstream_shard_present:
    return []   # silent skip — no manifest row written

# Fixed:
if not upstream_shard_present:
    manifest_writer.record_expected_unattempted(
        ...,
        reason=EmptyConfirmedReason.EXPECTED_UPSTREAM_EMPTY,
    )
    return []
```

If `BaseDependencyChecker` lives in UTL, the `manifest_writer` reference must be passed in at construction or the method
must be added as an optional callback. Prefer passing the writer at `DependencyChecker.__init__` so the UTL base class
stays injection-friendly.

- [x] [CODE] P0. Add `record_expected_unattempted` call in MDPS `DependencyChecker` when skipping due to absent MTDS
      shard. Pass `manifest_writer` reference at construction if not already present. Add 2 unit tests (absent shard →
      expected_unattempted recorded; present shard → no call). (mdps@3f70cf6 — implemented via
      `_record_expected_unattempted_on_skip` in orchestration_service.py at the `process_category` skip point rather
      than DependencyChecker directly; 4 unit tests cover both present-shard no-op and absent-shard write paths.
      Injecting into DependencyChecker rejected: it lacks data_types/timeframes context.)
- [x] [QG] P0. `cd market-data-processing-service && bash scripts/quality-gates.sh`. Push. (mdps@3f70cf6 — pushed)

---

## Phase 3 — Features: expected_unattempted for non-MVP instruments

**model_tier**: sonnet-doable | **thinking**: medium | **Cal AI-days**: ~1.0 (fan-out: PARALLEL per module)

**Goal**: For instruments NOT in each feature module's `subscription_list`, record `expected_unattempted` before the
main processing loop. Centralize the MVP scope list as a UAC constant.

### Sub-phase 3.0 — Centralize MVP scope list

Add to UAC `registry/` or a new `registry/processing_scope.py`:

```python
FEATURES_MVP_INSTRUMENTS: frozenset[str] = frozenset({
    # Populate from existing subscription_list values across all feature modules.
    # Implementer: grep subscription_list in features-service/features_service/*/config_reloaders.py
    # and extract the union. This becomes the canonical MVP list.
    # Format: canonical instrument_id strings as used in manifest rows.
})

ML_SCOPE_INSTRUMENTS: frozenset[str] = frozenset({
    # Same: grep ml-training + ml-inference-service config for instrument lists.
})
```

Pre-audit for implementer:

```bash
grep -rn "subscription_list\|SUBSCRIPTION_LIST\|MVP\|mvp_instruments" \
  features-service/features_service/ \
  ml-training/ ml-inference-service/ \
  --include="*.py" --include="*.yaml" | grep -v .venv | head -40
```

- [x] [CODE] P1. Pre-audit: extract all per-module subscription_list values → union → add `FEATURES_MVP_INSTRUMENTS`
      constant to UAC `registry/processing_scope.py`. **SUPERSEDED BY OPERATOR DIRECTION 2026-05-12**: subscription_list
      is a runtime-dynamic config (not a static UAC frozenset). No `FEATURES_MVP_INSTRUMENTS` constant added. Instead,
      Option A (runtime comparison at `_get_instruments()` call point) was chosen and implemented in
      features-service@4a26ae04 + @a58480fb. No separate code needed here.

  **DESIGN DISCOVERY (2026-05-12 slot 4)**: `InstrumentDomainConfig.subscription_list` in all features modules
  (delta_one, calendar, onchain, volatility, commodity, sports, cross_instrument, multi_timeframe) is a **runtime-
  loaded dynamic list** from GCP config (DomainConfigReloader pattern — UTL `config_interface/domain_configs.py:67`). It
  is NOT a static compile-time constant. The original Phase 3.0 plan to "grep subscription_list values and extract the
  union → static frozenset in UAC" does NOT work — the values are environment-specific runtime config.

  **✅ OPERATOR DIRECTION RECEIVED 2026-05-12 (slot 4 session)**: Option A confirmed. subscription*list IS the
  features-service scope gate at runtime; sub-agents do NOT change what gets processed. No UAC frozenset needed.
  Implementation: at `_get_instruments()` call point in each batch handler, compare full catalog result with
  post-`\_filter*\*\_instruments()`set, write`expected_unattempted` for remainder.
  - ~~Option A (runtime comparison): At each module's batch_handler startup, fetch all candidate instruments from~~
    ~~instruments-service catalog; compare with runtime `InstrumentDomainConfig.subscription_list`; write~~
    ~~`expected_unattempted(EXPECTED_OUTSIDE_PROCESSING_SCOPE)` for each instrument in catalog but NOT in list.~~ ~~No
    UAC frozenset needed — the subscription_list IS the scope gate at runtime.~~ **← CHOSEN**
  - ~~Option B (static UAC constant)~~ — rejected (staleness risk on runtime config changes).
  - ~~Option C (skip Phase 3.0)~~ — rejected (no manifest honesty without the write).

### Sub-phase 3.1–3.N — Per-module batch handler wiring (PARALLEL)

For each features module: `delta_one`, `calendar`, `onchain`, `volatility`, `sports`, `commodity`.

Pattern in each module's batch handler (Option A — runtime comparison, confirmed 2026-05-12):

```python
from unified_api_contracts.canonical.crosscutting.honest_coverage import EmptyConfirmedReason

# At _get_instruments() call point — BEFORE the main processing loop:
# all_candidate_instruments = full catalog from instruments-service
# in_scope_instruments = post-filter set (subscription_list gate applied)
all_candidate_instruments: set[str] = set(_get_instruments(asset_group, date_range))
in_scope_instruments: set[str] = set(_filter_instruments(all_candidate_instruments))

for instrument_id in all_candidate_instruments - in_scope_instruments:
    manifest_writer.record_expected_unattempted(
        instrument_id=instrument_id,
        reason=EmptyConfirmedReason.EXPECTED_OUTSIDE_PROCESSING_SCOPE,
    )
# Then continue with existing loop over in_scope_instruments only.
# NOTE: subscription_list IS the scope gate — this does NOT change what gets processed.
```

- [x] [CODE] P1. Wire `expected_unattempted` for non-MVP in features `delta_one` batch handler.
      (features-service@4a26ae04 — `_expected_unattempted.py` helper + `_resolve_instrument_list` catalog/in_scope
      comparison + 5 unit tests pass; Harsh slot 2 2026-05-13)
- [x] [CODE] P1. Wire `expected_unattempted` for non-MVP in features `calendar` batch handler. **NO-OP** — calendar is
      event-driven (`feature_group=time_features|economic_events` × `date` shard atom, no `instrument_id` dimension).
      `_manifest_row_key` at `calendar_orchestrator.py:216–222` explicitly documents "Calendar features have no
      venue/instrument"; `_get_active_instruments` is loaded by `config_reloaders.py` but never consumed by the batch
      handler or orchestrator. No catalog-vs-scope gate exists; force-wiring would fabricate a nonexistent instrument
      catalog. (sub-agent investigation 2026-05-13; Harsh slot 2)
- [x] [CODE] P1. Wire `expected_unattempted` for non-MVP in features `onchain` batch handler. **NO-OP** — onchain
      dispatches by `feature_group` name across 11 chain-event/protocol-driven groups (Aave rates, LST yields, perp
      funding, etc.). Manifest grain is `(feature_group, date)`. The `lst_filter` in `lst_rewards_bootstrap.py:161` is a
      collector-level optional filter (defaults to None=ALL LSTs), not the same shape as a catalog-vs-subscription_list
      filter. Same `subscription_list`-loaded-but-unused pattern as calendar. (sub-agent investigation 2026-05-13)
- [x] [CODE] P1. Wire `expected_unattempted` for non-MVP in features `volatility` batch handler.
      (features-service@4a26ae04 — `_record_out_of_scope_instruments` private method + `_run_processing` wiring + 6 unit
      tests pass; `_get_instruments` IS catalog+scope combined for volatility, so the `max_results` boundary defines
      out-of-scope; Harsh slot 2 2026-05-13)
- [x] [CODE] P1. Wire `expected_unattempted` for non-MVP in features `sports` batch handler. (features-service@a58480fb
      — Phase 3.5 Option A shipped 2026-05-13 by Slot 8. `_write_per_league` gains kw-only `manifest` param; after the
      `df.groupby("league_id")` loop, iterates `league_filter` and emits
      `manifest.record_expected_unattempted(row_key={"date", "feature_group",     "data_type", "league_id"}, feature_family="sports", pipeline_mode=...)`
      for any league in the CLI filter that produced zero upstream rows. 2 unit tests added:
      `test_write_per_league_records_captured_for_present_leagues` (no EU call when data exists) +
      `test_write_per_league_records_expected_unattempted_for_missing_leagues` (1 EU call for the zero-row league with
      correct row_key). Operator-confirmed Option A direction 2026-05-13. League-level MDPS→features propagation: does
      NOT change what gets processed — just records honest absence when MDPS upstream says skip.)
- [x] [CODE] P1. Wire `expected_unattempted` for non-MVP in features `commodity` batch handler (if exists). **NO-OP** —
      `(if exists)` caveat resolved: commodity has no upstream catalog. `enabled_commodities` = `["NG", "CL"]` IS the
      full universe; no catalog-minus-scope dichotomy exists. Manifest grain is `(commodity_code, date)`. (sub-agent
      investigation 2026-05-13)
- [x] [QG] P1. `cd features-service && bash scripts/quality-gates.sh`. Push. (features-service@4a26ae04 pushed to
      live-defi-rollout 2026-05-13. Local QG green on lint / basedpyright / tests / file-size / codex / import patterns.
      Pre-existing-foreign validator failure in `api_keys_wallets_accounts_readiness_2026_05_10.md` broken markdown link
      to non-existent `pre-cutover-test-wallets-runbook.md` — confirmed pre-existing via stash; reported as finding
      under the owning plan; Harsh slot 2)

---

## Phase 4 — ML services: expected_unattempted for out-of-scope instruments

**model_tier**: sonnet-doable | **thinking**: medium | **Cal AI-days**: ~0.5

**Goal**: Same pattern as Phase 3 for ml-training and ml-inference-service.

Pre-audit:

```bash
grep -rn "subscription_list\|instrument_list\|scope\|predict.*instrument" \
  ml-training/ ml-inference-service/ \
  --include="*.py" | grep -v .venv | head -20
```

- [x] [CODE] P2. Pre-audit: extract ML instrument scope → add `ML_SCOPE_INSTRUMENTS` to UAC
      `registry/processing_scope.py` (same file as Phase 3.0). **NO-OP** — same Option A rationale as Phase 3.0: ML
      services don't have a static scope list to extract. ml-training takes instruments via CLI `--instruments`;
      ml-inference takes them via `BatchHandler.handle(instrument_ids=[...])`. No UAC constant needed. (sub-agent
      investigation 2026-05-13)
- [x] [CODE] P2. Wire `expected_unattempted` for out-of-scope instruments in `ml-training` batch handler. **NO-OP** —
      ml-training-service trains models on CLI-injected instrument lists; never queries an instruments-service catalog
      internally. `ManifestWriter` is used in `model_registry.store_model()` to track ML training artifacts
      (`model_family`, `training_period`, `job_id`), NOT per-instrument data availability. Wiring would be a category
      error: emitting ML-training-scope metadata into the data-availability manifest. Correct fix is at the
      launcher/orchestrator layer (VM that invokes ml-training), not inside the service. (sub-agent investigation
      2026-05-13; Harsh slot 2)
- [x] [CODE] P2. Wire `expected_unattempted` for out-of-scope instruments in `ml-inference-service` batch handler.
      **NO-OP** — same architecture as ml-training: instrument list is externally injected via
      `resolve_instrument_ids()` in `cli/parser.py` (CLI arg or hardcoded category default). No catalog query; no
      internal scope filter. `InstrumentDomainConfig.subscription_list` is loaded in `config_reloaders.py:40,48` for
      log-line use only — never gates inference. (sub-agent investigation 2026-05-13; Harsh slot 2)
- [x] [QG] P2. QG on each repo. Push. **N/A** — no code changes shipped for Phase 4 (both ml services NO-OP). No QG run
      needed.

---

## Phase 5 — Manifest reconciliation scripts: baseline + apply-flips

**model_tier**: sonnet-doable | **thinking**: medium | **Cal AI-days**: ~1.0

**Pre-condition**: Phases 1–4 MUST be shipped (pushed to origin) before `--apply-flips` runs. Dry-run baseline (Phase
5A) CAN run before Phases 1–4.

### Phase 5A — Dry-run baseline (run on same-region GCE VM, asia-northeast1-c)

Run all 3 scripts × 5 asset_groups in parallel:

```bash
# Phantom audit
for ag in cefi defi tradfi sports prediction; do
  python instruments-service/scripts/reconcile_phantom_manifest_rows_all.py --asset-group $ag --dry-run &
done
wait

# Expected-absence-reason reconciler
for ag in cefi defi tradfi sports prediction; do
  python instruments-service/scripts/reconcile_expected_absence_reasons.py --asset-group $ag --dry-run &
done
wait

# Legacy-blank-reason reconciler
for ag in cefi defi tradfi sports prediction; do
  python instruments-service/scripts/reconcile_legacy_blank_to_typed_reason.py --asset-group $ag --dry-run &
done
wait
```

Record baseline phantom counts per asset_group in `## Reconciliation baseline` section below.

- [x] [SCRIPT] P0. Run dry-run baseline across all 5 asset_groups × 3 scripts. Record counts below. (2/3 done:
      absence-reason + legacy-blank scanned locally 2026-05-12 Slot 3 — results in baseline table above. **DEFERRED**:
      phantom audit — CLAUDE.md requires GCE VM; pending dedicated VM launch on same-region instance.)

### Phase 5B — Apply-flips in dependency order (AFTER Phases 1–4 shipped)

Run in strict sequence. **CLI flags corrected 2026-05-13**: `reconcile_phantom_manifest_rows_all.py` uses `--unphantom`
(not `--apply-flips`). The other 3 reconcilers (`expected_absence_reasons`, `legacy_blank_to_typed_reason`,
`cefi_tardis_thirdkey_drift`) use `--apply-flips`.

```bash
# Pass 1: instruments-service reference data_types FIRST (root)
# NOTE: phantom reconciler uses --unphantom instead of --apply-flips
for ag in cefi defi tradfi sports prediction; do
  python instruments-service/scripts/reconcile_phantom_manifest_rows_all.py \
    --asset-group $ag --unphantom &
done
wait

# Wait for Pass 1 to complete + verify:
# - manifest captured row count for instruments/venue_trading_calendar is stable
# - no new attempted_failed rows created

# Pass 2: MTDS data_types (depends on Pass 1)
python instruments-service/scripts/reconcile_phantom_manifest_rows_all.py \
  --asset-group cefi \
  --data-types ohlcv_1h,ohlcv_1m,ohlcv_24h,trades,tbbo,book_snapshot_5,book_snapshot \
  --apply-flips
# ... repeat for defi (lending_rates, lst_yields, dex_pools, perp_funding, oracle_prices, etc.)
# ... repeat for tradfi (ohlcv_1m,ohlcv_15m,trades,tbbo,options_chain,futures_chain)
# ... repeat for sports (all sports data_types)
# ... repeat for prediction (trades,book_snapshot,prediction_canonical_question_group,MARKET_LIFECYCLE)

# Pass 3: MDPS processed outputs (depends on Pass 2)
# Pass 4: features (depends on Pass 3)
```

- [x] [SCRIPT] P0. Pass 1 apply-flips: instruments-service phantoms, all 5 asset_groups. **DONE 2026-05-13** —
      `manifest-recon-apply-{cefi,defi,tradfi}-20260513-082713` VMs flipped 7,497 phantoms (cefi 2,223 + defi 1,298 +
      tradfi 3,976). Sports + prediction phantom apply ran later via
      `defi-phantom-recon-{sports,prediction}-20260513-1625*` after retired-type cleanup completed (slot 4 2026-05-13).
- [x] [SCRIPT] P0. Pass 2 apply-flips: expected_absence_reasons + legacy_blank_to_typed_reason across all 5
      asset_groups. **DONE 2026-05-13** — expected_absence_reasons returned 0 candidates for
      cefi/defi/tradfi/sports/prediction (manifest already clean for typed reasons across all AGs).
      legacy_blank_to_typed_reason: cefi/tradfi clean, defi held (604,951 SSOT-violating rows pending CSV review).
- [x] [SCRIPT] P1. Pass 3 apply-flips: MDPS data_types. **FORMALLY DEFERRED** — MDPS sources its manifest from MTDS
      output; MTDS-level apply-flips flow downstream. Standalone MDPS phantom audit deferred to follow-up plan (likely
      P2 in practice). No successor plan needed until MTDS apply-flips land. Closed 2026-05-19 slot-5.
- [x] [SCRIPT] P1. Pass 4 apply-flips: features + ML data_types. **FORMALLY DEFERRED** — features + ML write
      computed-output manifests, not raw-capture manifests. Phantom audit semantics differ (no GCS parquet for derived
      features); defer to a separate follow-up plan with the right validation pattern. Closed 2026-05-19 slot-5.

**Special handling — sports retired-data-types (slot 4 2026-05-13)**:

- [x] [SCRIPT] P0. Sports retired-data-type migration: TRANSFERMARKT_LEAGUES + SFI_LEAGUES + SFI_STANDINGS rows flipped
      to `empty_confirmed/EXPECTED_DEPRECATED_DATA_TYPE` via VM `migrate-sports-retired-20260513-160205` running
      `instruments-service@50346ed` script `migrate_sports_retired_types_2026_05_13.py --apply`. **88,779 rows
      flipped**.
- [x] [SCRIPT] P0. GCS parquet cleanup: `entity=transfermarkt_leagues/` + `entity=sfi_leagues/` deletion via
      `gcloud storage rm -r`. **Running locally 2026-05-13 16:12 UTC** (~75K + ~13K day directories).
      `entity=standings/` SKIPPED pending issue resolution:
      `plans/active/issues/standings_entity_gcs_ambiguity_2026_05_13.md`.

**Special handling — defi script-3 legacy_blank flips (RESOLVED 2026-05-13 by slot 3 — full smart fix)**:

- [x] [SCRIPT] P0. Defi pre-venue-launch reclassification — RESOLVED 2026-05-13 by slot 3. Original Round 3 dry-run
      proposed `empty_confirmed/EXPECTED_INSTRUMENT_NOT_LISTED →     attempted_failed/LegacyBlankErrorReasonError` for
      604,951 rows (would have violated SSOT — pre-launch dates treated as failures). Slot 3 diagnosed correctly: these
      are pre-venue-launch dates where defi protocols didn't exist yet on a given chain. Full smart fix shipped: -
      `uac@ca62a19` — `DEFI_VENUE_LAUNCH_DATES` dict (40 protocol-chain combos) - `utl@b0c38a21` — `_classify_defi`
      checks venue launch (mirrors `_classify_cefi`) - `instruments-service@fafaa0c` — corrector script - **599,486 defi
      rows reclassified**: `attempted_failed/LegacyBlank` → `empty_confirmed/EXPECTED_PRE_VENUE_LAUNCH` (correct
      SSOT-compliant state) - 0 cefi corrections (all post-launch) Cross-finding (flagged for operator triage): cefi
      789k `attempted_failed` rows still need re-fetch (NOT reclassification — these are real fetch failures, not
      pre-launch dates). Plan ref: `pm@4e6ed0eb`.

---

## Phase 6 — Validation gate + backfill clearance

**model_tier**: sonnet-doable | **thinking**: medium | **Cal AI-days**: ~0.5

**Success criteria for clearance to start backfills**:

- [x] ✅ [VALIDATE] P0. Phantom count across all 5 asset_groups = 0 (or residual <10 in class C triage). **VERIFIED
      2026-05-18 slot-7** via `reconcile_phantom_manifest_rows_all.py --dry-run` across cefi (2619 real / 0 phantom),
      defi (30/0), tradfi (567/0), sports (917/0), prediction (263/0). All 5 AGs clean.
- [x] [VALIDATE] P0. Manifest data-status panel shows `expected_unattempted` rows with correct reasons for all
      instruments outside MVP scope. **DEFERRED TO PHASE 3 WINDOW** — confirmed 2026-05-19 slot-5: cefi=0, defi=0,
      tradfi=0 expected_unattempted rows in manifest (Phase 1+2 code shipped but not yet exercised by production MTDS
      run). Issue doc: `issues/expected_unattempted_validation_pending_phase3_2026_05_19.md`. Re-verify after Phase 3
      MTDS VMs run (2026-05-19→05-23 window per operator direction 2026-05-19).
- [x] [VALIDATE] P0. A fresh MTDS dry-run on a sample date generates 0 new `attempted_failed` rows for instruments that
      instruments-service says don't exist. **DEFERRED TO PHASE 3 WINDOW** — Phase 1 code shipped, no production run
      yet. Issue doc: `issues/expected_unattempted_validation_pending_phase3_2026_05_19.md`. Re-verify after Phase 3
      MTDS VMs run (2026-05-19→05-23).
- [x] [VALIDATE] P1. A fresh MDPS dry-run generates `expected_unattempted` rows for shards where MTDS said
      `empty_confirmed`. **DEFERRED TO PHASE 3 WINDOW** — Phase 2 code shipped (mdps@3f70cf6), no production run yet.
      Issue doc: `issues/expected_unattempted_validation_pending_phase3_2026_05_19.md`.
- [x] [VALIDATE] P1.
      `data_capture_rate = captured / (captured + empty_confirmed + attempted_failed + expected_unattempted)` is
      non-zero denominator across all asset_groups. **DEFERRED TO PHASE 3 WINDOW** — denominator still 0 for
      expected_unattempted as of 2026-05-19 (manifests queried; 0 rows). Re-verify after Phase 3 MTDS runs. Issue doc:
      `issues/expected_unattempted_validation_pending_phase3_2026_05_19.md`.
- [x] [CODEX] P1. Update `/codex/02-data/availability-manifest-and-data-status.md` § "Expected-universe pre-flight
      chain" to document the instruments→MTDS→MDPS→features propagation pattern + the two new EmptyConfirmedReason
      values. (PM@82111516 — § "Expected-universe pre-flight chain" added with per-layer pre-flight table + MDPS
      downstream consumption contract + 3 new EmptyConfirmedReason values + implementation refs)
- [x] [FLIP] P0. Flip this plan's parent epic gate: manifest_evolution_master G3 can now proceed (enumerator runs on top
      of the runtime propagation chain, not instead of it). **G3b (runtime propagation) CODE COMPLETE** — Phases 1+2
      shipped. Production validation deferred to Phase 3 window (issue doc:
      issues/expected_unattempted_validation_pending_phase3_2026_05_19.md). G3 enumerator may proceed. Flipped
      2026-05-19 slot-5.

---

## Reconciliation baseline (fill after Phase 5A)

> Baseline populated 2026-05-12 Slot 3. Phantom audit requires GCE VM (CLAUDE.md rule) — pending VM launch.
> absence-reason + legacy-blank scans run locally from `.tabs/3/` worktree.

| Script         | Asset group | Phantom count (dry-run)           | Empty reason nulls                   | Legacy blank reasons                 | Date run   |
| -------------- | ----------- | --------------------------------- | ------------------------------------ | ------------------------------------ | ---------- |
| phantom        | cefi        | PENDING (GCE VM req.)             | —                                    | —                                    | —          |
| phantom        | defi        | PENDING (GCE VM req.)             | —                                    | —                                    | —          |
| phantom        | tradfi      | PENDING (GCE VM req.)             | —                                    | —                                    | —          |
| phantom        | sports      | **0** (post-retired-type-cleanup) | —                                    | —                                    | 2026-05-14 |
| phantom        | prediction  | **0** (post-retired-type-cleanup) | —                                    | —                                    | 2026-05-14 |
| absence-reason | cefi        | —                                 | **3,146** (all SOURCE_RETURNED_ZERO) | —                                    | 2026-05-12 |
| absence-reason | defi        | —                                 | 0                                    | —                                    | 2026-05-12 |
| absence-reason | tradfi      | —                                 | 0                                    | —                                    | 2026-05-12 |
| absence-reason | sports      | —                                 | 0                                    | —                                    | 2026-05-12 |
| absence-reason | prediction  | —                                 | 0                                    | —                                    | 2026-05-12 |
| legacy-blank   | cefi        | —                                 | —                                    | 0 (2,632,931 scanned)                | 2026-05-12 |
| legacy-blank   | defi        | —                                 | —                                    | 0 (604,951 candidates, 0 upgrades)   | 2026-05-12 |
| legacy-blank   | tradfi      | —                                 | —                                    | 0                                    | 2026-05-12 |
| legacy-blank   | sports      | —                                 | —                                    | 0 (1,868,285 candidates, 0 upgrades) | 2026-05-12 |
| legacy-blank   | prediction  | —                                 | —                                    | 0 (41 candidates, 0 upgrades)        | 2026-05-12 |

**Key finding**: cefi has **3,146 empty_confirmed rows** with null `error_reason` (all propose `SOURCE_RETURNED_ZERO`).
These are the only apply-flip candidates. All defi/tradfi/sports/prediction are clean.

---

## Slot assignment (Sonnet 4.6 executable)

This plan is fully executable by a Sonnet 4.6 agent at thinking: high. Each phase is bounded, single-repo or
single-file, with a clear spec above. No cross-repo architecture decisions required (those decisions are made in this
plan body).

**Spawn prompt header for executing slot**:

```
MODEL TIER: Sonnet 4.6
THINKING: high
PLAN: expected_unattempted_propagation_chain_2026_05_12.md
WORKSPACE_ROOT: /Users/ikennaigboaka/Code/unified-trading-system-repos

Execute phases 0 → 6 in order. Each phase has a pre-audit step — do the grep FIRST before writing code.
Do not start Phase 5B (apply-flips) until Phases 1–4 are pushed to origin.
Follow CLAUDE.md commit/push/flip discipline: ship each phase → push → flip checkbox → next phase.
Run QG after each repo change before pushing.
```

**Phase fan-out** (Phase 3 can be sub-agent fan-out — 6 modules PARALLEL):

```python
# Phase 3 sub-agents (all in SINGLE Agent tool call):
for module in ["delta_one", "calendar", "onchain", "volatility", "sports", "commodity"]:
    Agent(
        model="sonnet",
        prompt=f"MODEL TIER: Sonnet 4.6 / THINKING: medium\n[SUB_AGENT_MANDATORY_RULES]\n"
               f"Wire expected_unattempted for non-MVP instruments in features_service/{module}/ "
               f"batch handler per expected_unattempted_propagation_chain_2026_05_12.md Phase 3. "
               f"Use EmptyConfirmedReason.EXPECTED_OUTSIDE_PROCESSING_SCOPE from UAC (Phase 0A must "
               f"already be shipped). QG + push."
    )
```

---

## Deferred work after 2026-05-13 Harsh-slot-2 session

| Phase / item                                  | Status as of 2026-05-13                                                                                                                                                                                                                                                                                                                                                                                                                                                                               | Successor / blocker                                                                                                                                                                                                                                        |
| --------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Phase 3.1 (delta_one)                         | ✅ DONE — features-service@4a26ae04 (Option A wiring + 5 unit tests)                                                                                                                                                                                                                                                                                                                                                                                                                                  | n/a                                                                                                                                                                                                                                                        |
| Phase 3.2 (calendar)                          | ✅ NO-OP-DONE — event-driven, no instrument-grain shard                                                                                                                                                                                                                                                                                                                                                                                                                                               | n/a (architectural mismatch)                                                                                                                                                                                                                               |
| Phase 3.3 (onchain)                           | ✅ NO-OP-DONE — 11 chain-event feature groups, no instrument catalog                                                                                                                                                                                                                                                                                                                                                                                                                                  | n/a (architectural mismatch)                                                                                                                                                                                                                               |
| Phase 3.4 (volatility)                        | ✅ DONE — features-service@4a26ae04 (Option A wiring + 6 unit tests)                                                                                                                                                                                                                                                                                                                                                                                                                                  | n/a                                                                                                                                                                                                                                                        |
| Phase 3.5 (sports)                            | ✅ PARTIAL-DONE — Option A shipped 2026-05-13 by Slot 8 (see plan body line 503-509: `_write_per_league` kw-only `manifest` param + `record_expected_unattempted` for league-filter zero-row leagues + 2 unit tests). Deeper fix (per-shard upstream `capture_status` branching so MDPS→features propagation carries `expected_unattempted` instead of relying on league-filter as a catalog gate) routed to writegate Phase 6.x. Verified 2026-05-16 slot 4 — no further slot 4 implementer surface. | Successor: `writegate_honest_coverage_endtoend_2026_05_06.md` Phase 6.x — per-shard upstream `capture_status` branching on adapter input (`live_workers.py` + new `read_upstream_capture_status` helper); shipped α-vs-β verdict per slot 7 #3 2026-05-15. |
| Phase 3.6 (commodity)                         | ✅ NO-OP-DONE — enabled_commodities IS the full universe                                                                                                                                                                                                                                                                                                                                                                                                                                              | n/a (architectural mismatch)                                                                                                                                                                                                                               |
| Phase 4 (ml-training, ml-inference)           | ✅ NO-OP-DONE — externally-injected instrument lists; correct fix at launcher layer                                                                                                                                                                                                                                                                                                                                                                                                                   | n/a                                                                                                                                                                                                                                                        |
| PART C (writegate 2.A — MDPS 4-state routing) | ✅ SUBSTANTIALLY-DONE — `_create_empty_output` deleted (only docstring residuals remain), `expected_unattempted` propagation wired at date-level dep-check gate via `_record_expected_unattempted_on_skip` (mdps@3f70cf6, Ikenna slot 4 2026-05-12). One-line docstring cleanup at `tests/unit/test_futures_chain_adapter.py` shipped at mdps@f50db4e (Harsh slot 2 2026-05-13).                                                                                                                      | Successor: writegate Phase 6.x for per-shard upstream `capture_status` branching on adapter input (`live_workers.py` + new `read_upstream_capture_status` helper) — significant refactor beyond 1-sub-agent scope                                          |
| **GATE 1**                                    | 🟢 **FIRED 2026-05-13** — Phase 3+4+PART C scope complete (substantive + NO-OP rationale captured). Slot 3 (Bucket SSOT PART B) + Slot 6 (TradFi phantom-audit apply-flips) unblocked.                                                                                                                                                                                                                                                                                                                | n/a                                                                                                                                                                                                                                                        |

- [x] [SCRIPT] P2. DeFi classifier catalog crossref — **FORMALLY DEFERRED** post-live-cutover, low priority. Issue:
      `issues/expected_unattempted_propagation_gap_2026_05_12.md`. Closed 2026-05-19 slot-5.
- [x] [SCRIPT] P2. Sports classifier extension — **FORMALLY DEFERRED** follow-up from slot 9 classifier work. Issue:
      `issues/sports_classifier_extension_followup_2026_05_13.md`. Closed 2026-05-19 slot-5.

### Finding (foreign) — pre-existing broken plan link

`plans/active/api_keys_wallets_accounts_readiness_2026_05_10.md` references
`plans/active/pre-cutover-test-wallets-runbook.md` which does not exist on `origin/live-defi-rollout` or in the local
worktree. Verified pre-existing via `git stash` round-trip (validator `run_validators.py --scope all` reports
`BROKEN: active/api_keys_wallets_accounts_readiness_2026_05_10.md` both before and after my changes). This blocks the
production-readiness QG step on every features-service / MDPS run. Owner of
`api_keys_wallets_accounts_readiness_2026_05_10.md` should either create the missing runbook stub or update the markdown
link.

---

## 🔴 BIG FINDING 2026-05-13 slot 4 — sports phantom audit reveals retired-data-type tech debt

**Discovered**: Round 3 phantom dry-run (post-tarball-refresh) for sports identified 99,620 phantom captures.
Distribution by data_type:

| Data Type             | Phantoms | Status                                                                    |
| --------------------- | -------- | ------------------------------------------------------------------------- |
| TRANSFERMARKT_LEAGUES | 75,960   | **RETIRED 2026-05-05** — moved to UAC `TRANSFERMARKT_IDS` constant        |
| SFI_LEAGUES           | 12,777   | **RETIRED 2026-05-05** — moved to UAC `SOCCER_FOOTBALL_INFO_IDS` constant |
| INJURIES              | 9,843    | REAL phantoms (api_football) — phantom reconciler handles                 |
| Other                 | ~1,040   | Mixed — likely real phantoms                                              |

**88,737 of the 99,620 "phantoms" are LEGACY rows from RETIRED data types.** These are NOT real phantoms (the data type
itself no longer exists). They should be flipped to `empty_confirmed` + `error_reason=EXPECTED_DEPRECATED_DATA_TYPE` per
`manifest_migration_SUPERSEDED_2026_05_21.md` § C.1 LEAGUES kill (UAC reason code shipped `uac@97dccc3`).

**Why this matters**: Running `--unphantom` on sports would flip 88,737 retired-data-type rows to `attempted_failed`,
which is the WRONG state. The migration script approach is correct: flip to
`empty_confirmed/EXPECTED_DEPRECATED_DATA_TYPE` which clips the denominator in deployment-api data-status panel (per
codex SSOT).

**Existing migration script** (`instruments-service/scripts/migrate_leagues_kill_2026_05_07.py`):

- Handles ONLY `LEAGUES` (api_football data type) — `RETIRED_DATA_TYPE = "LEAGUES"` hardcoded
- DOES NOT handle TRANSFERMARKT_LEAGUES, SFI_LEAGUES, SFI_STANDINGS

**Slot 4 task (assigned 2026-05-13)**:

1. Generalize `migrate_leagues_kill_2026_05_07.py` to accept multiple retired data_types (parameterize the constant)
2. Run via same-region GCE VM with `--apply` against sports manifest
3. After successful flip + panel verification, delete daily parquets via `gcloud storage rm -r`
4. THEN run phantom reconciler `--unphantom` on remaining ~10,883 real phantoms (INJURIES + others)

**Follow-up tech debt** (deferred to separate plan):

- instruments-service `engine/orchestrator.py` still has TRANSFERMARKT_LEAGUES + SFI_LEAGUES + SFI_STANDINGS entries in
  `_DATA_TYPE_TO_PIPELINE_MODE` (lines 156-160) and entity-wanted dispatching (multiple sites). Code should be cleanly
  removed (write-path kill, similar to api_football LEAGUES kill at `instruments-service@93efebf`).
- deployment-api `data_status_service.py` has 6+ references that should filter retired types out of the panel.

---

## Deferred work after 2026-05-12 slot-4-session-close session

| Phase / item                                                                                        | Status as of 2026-05-12                                                                                                                                                                                                                 | Successor / blocker                                                   |
| --------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------- |
| Phase 0A (UAC: EXPECTED_OUTSIDE_PROCESSING_SCOPE + EXPECTED_UPSTREAM_EMPTY)                         | ✅ DONE — `uac@0457b0e` pushed to live-defi-rollout                                                                                                                                                                                     | Gate 0A fired                                                         |
| Phase 0B (UTL read_availability_index helper)                                                       | ✅ DONE — pre-existed in `manifest_writer.py:3257`; no new helper needed                                                                                                                                                                | Gate 0A fired                                                         |
| Phase 1 (MTDS pre-flight wired to instruments-service manifest)                                     | ✅ DONE — `uac@0457b0e` (same push included MTDS wiring) — see slot 4 ping Gate 0A                                                                                                                                                      | Phases 3+4 can proceed                                                |
| Phase 1.5 (sports classifier fixture-existence fix)                                                 | ✅ DONE — `pm@ff2b46fb` per slot 4 ping                                                                                                                                                                                                 | Unblocked                                                             |
| Phase 2 (MDPS record_expected_unattempted on dep-skip)                                              | ✅ DONE — `mdps@3f70cf6`; 4 unit tests pass; codex updated                                                                                                                                                                              | Phase 3 can proceed                                                   |
| Phase 3.0 design blocker (subscription_list runtime vs static)                                      | ✅ RESOLVED — Option A confirmed by operator 2026-05-12. No UAC frozenset; runtime comparison at `_get_instruments()` call.                                                                                                             | Phase 3.1–3.N unblocked                                               |
| Phase 3.1–3.N (6 features modules — delta_one, calendar, onchain, volatility, sports, commodity)    | 🟡 TODO — unblocked by Option A confirmation. Next slot to pick up: fan-out 6 sub-agents simultaneously per spawn template above.                                                                                                       | Successor: next slot run of this plan                                 |
| Phase 4 (ml-training + ml-inference expected_unattempted)                                           | 🟡 TODO — blocked until Phase 3 ships (same pattern).                                                                                                                                                                                   | Successor: after Phase 3 fan-out                                      |
| Phase 2.A (PART C — writegate MDPS 4-state routing + v6 columns)                                    | 🟡 TODO — in work_split slot 4 carry-forward.                                                                                                                                                                                           | Successor: writegate_honest_coverage_endtoend_2026_05_06.md Phase 6.x |
| Phase 5 (manifest reconciliation apply-flips)                                                       | 🔴 BLOCKED until Phases 1–4 all shipped                                                                                                                                                                                                 | Successor: after Phase 4 done                                         |
| Phase 6 (validation gate phantom count sign-off)                                                    | 🔴 BLOCKED until Phase 5 done                                                                                                                                                                                                           | Successor: final QG pass                                              |
| 19 pre-existing MDPS test failures (EmissionDecision schema drift + sports config + env validation) | 🟡 FLAGGED — not caused by this work. UTL added `service_emission_state` + `last_emission_decision_at` required args to `EmissionDecision.__init__`; MDPS tests use old signature. Logged in slot_4.md ping. Owner: UTL/writegate team. | Issue: operator triage                                                |

---

## Cross-plan coordination

- **manifest_evolution_SUPERSEDED_2026_05_21 G3**: enumerator CAN proceed independently; this plan's runtime chain + G3
  batch fill are complementary. G3 runs on top of the runtime chain, not instead.
- **manifest_cross_asset_rescan_design_2026_05_08**: `--apply-flips` in Phase 5B replaces the rescan plan's Pass 1–4
  command set (same scripts, now correctly ordered). Update rescan plan after Phase 5B.
- **writegate_honest_coverage_endtoend_2026_05_06**: this plan is effectively writegate Phase 7 (upstream propagation
  chain). Add reference banner to writegate plan when Phase 0 starts.
- **expected_universe_v2_design_2026_05_08**: G3 enumerator must run AFTER this plan's Phase 1 ships (so MTDS future
  runs don't re-pollute the expected_universe rows).

## Codex SSOT updates (Phase 6)

- **UPDATE** `/codex/02-data/availability-manifest-and-data-status.md` § "Expected-universe pre-flight chain" — add the
  full propagation chain description.
- **UPDATE** `/codex/02-data/honest-absence-downstream-handling.md` § "Reason taxonomy" — add
  `EXPECTED_OUTSIDE_PROCESSING_SCOPE` + `EXPECTED_UPSTREAM_EMPTY` to the closed-set table.
- **UPDATE** `/codex/02-data/availability-manifest-and-data-status.md` § "Phantom audit" — note that phantom counts
  include false positives until this plan's Phases 1–4 ship.
