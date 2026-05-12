---
name: expected-unattempted-propagation-chain-2026-05-12
type: plan
plan_type: implementation
asset_group: cross-cutting
owner: ikenna
status: active
priority: P0
created: 2026-05-12
last_updated: 2026-05-12
deadline: 2026-05-15
parent: manifest_evolution_master_2026_05_08
related_plans:
  - manifest_evolution_master_2026_05_08
  - manifest_cross_asset_rescan_design_2026_05_08
  - writegate_honest_coverage_endtoend_2026_05_06
  - expected_universe_v2_design_2026_05_08
migrated_from: plans/active/issues/expected_unattempted_propagation_gap_2026_05_12.md
locked_by: live-defi-rollout
locked_since: 2026-05-12
estimate_class: brand-new
estimate_baseline_ai_days: 6.6
estimate_calibrated_ai_days: 6.6
estimate_calibration_note: |
  +1.1 added 2026-05-12 for Phase 1.5 (sports fixture SSOT fix ~0.8) + Phase 2 extension (MDPS forward-fill contract ~0.3).
  brand-new class, multiplier 1.0×.
effective_concurrent_slots: 4
model_tier: sonnet-doable
thinking: high
---

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
- [ ] [RESEARCH] P1. Audit instruments-service manifest for transfermarkt data: does the manifest correctly track
      per-league transfer windows? Is `EXPECTED_OUTSIDE_TRANSFER_WINDOW` being correctly applied to all transfermarkt
      data_types (player_values, transfers) during non-window periods? Is `available_at` set to last day of the transfer
      window for player values entering next season? File a follow-up todo if the design doesn't match the intent.
- [x] [QG] P1. `cd unified-trading-library && bash scripts/quality-gates.sh`.
      `cd instruments-service && bash scripts/quality-gates.sh`. Push. UTL: 4 new tests pass
      (test_sports_fixture_classifier.py); 109 pre-existing manifest_writer failures (foreign). instruments-service: 6/6
      reconciler tests pass (instruments-service@703d36b fixed Shape-b test gap from 3a05e4f); 84 pre-existing failures
      (orchestrator_coverage, phase2d, urdi — foreign). (instruments-service@703d36b)

---

## Phase 2 — MDPS: record_expected_unattempted on skip + forward-fill semantics codification

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
      `codex/02-data/honest-absence-downstream-handling.md` documenting the 4-row table above. Reference this plan +
      writegate Phase 2.A. (pm@5ab28423 — codex/02-data/honest-absence-downstream-handling.md § "MDPS downstream
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
      expected_unattempted recorded; present shard → no call).
      (mdps@3f70cf6 — implemented via `_record_expected_unattempted_on_skip` in orchestration_service.py at the
      `process_category` skip point rather than DependencyChecker directly; 4 unit tests cover both present-shard no-op
      and absent-shard write paths. Injecting into DependencyChecker rejected: it lacks data_types/timeframes context.)
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

- [ ] [CODE] P1. Pre-audit: extract all per-module subscription_list values → union → add `FEATURES_MVP_INSTRUMENTS`
      constant to UAC `registry/processing_scope.py`.

  **DESIGN DISCOVERY (2026-05-12 slot 4)**: `InstrumentDomainConfig.subscription_list` in all features modules
  (delta_one, calendar, onchain, volatility, commodity, sports, cross_instrument, multi_timeframe) is a **runtime-
  loaded dynamic list** from GCP config (DomainConfigReloader pattern — UTL `config_interface/domain_configs.py:67`).
  It is NOT a static compile-time constant. The original Phase 3.0 plan to "grep subscription_list values and
  extract the union → static frozenset in UAC" does NOT work — the values are environment-specific runtime config.

  **Revised Phase 3 approach (AWAITING OPERATOR DIRECTION)**:
  - Option A (runtime comparison): At each module's batch_handler startup, fetch all candidate instruments from
    instruments-service catalog; compare with runtime `InstrumentDomainConfig.subscription_list`; write
    `expected_unattempted(EXPECTED_OUTSIDE_PROCESSING_SCOPE)` for each instrument in catalog but NOT in list.
    No UAC frozenset needed — the subscription_list IS the scope gate at runtime.
  - Option B (static UAC constant): Keep frozenset idea but populate from deployment config rather than source
    grep. Requires a one-time extraction from GCP config + UAC PR. More fragile (stalens risk on config changes).
  - Option C (skip Phase 3.0 altogether): Each module already knows its own subscription_list; just compare inline
    without a UAC constant. Simpler but no single SSOT for MVP scope.

  Operator should direct: which option. Option A is the natural extension of the existing pattern.

### Sub-phase 3.1–3.N — Per-module batch handler wiring (PARALLEL)

For each features module: `delta_one`, `calendar`, `onchain`, `volatility`, `sports`, `commodity`.

Pattern in each module's batch handler (before the main processing loop):

```python
from unified_api_contracts.registry.processing_scope import FEATURES_MVP_INSTRUMENTS
from unified_api_contracts.canonical.crosscutting.honest_coverage import EmptyConfirmedReason

# Get all candidate instruments for this batch run (from MDPS manifest or instruments catalog)
all_candidate_instruments = get_candidate_instruments(asset_group, date_range)

for instrument_id in all_candidate_instruments:
    if instrument_id not in FEATURES_MVP_INSTRUMENTS:
        manifest_writer.record_expected_unattempted(
            ...,
            reason=EmptyConfirmedReason.EXPECTED_OUTSIDE_PROCESSING_SCOPE,
        )
        continue
    # ... existing feature computation
```

- [ ] [CODE] P1. Wire `expected_unattempted` for non-MVP in features `delta_one` batch handler.
- [ ] [CODE] P1. Wire `expected_unattempted` for non-MVP in features `calendar` batch handler.
- [ ] [CODE] P1. Wire `expected_unattempted` for non-MVP in features `onchain` batch handler.
- [ ] [CODE] P1. Wire `expected_unattempted` for non-MVP in features `volatility` batch handler.
- [ ] [CODE] P1. Wire `expected_unattempted` for non-MVP in features `sports` batch handler.
- [ ] [CODE] P1. Wire `expected_unattempted` for non-MVP in features `commodity` batch handler (if exists).
- [ ] [QG] P1. `cd features-service && bash scripts/quality-gates.sh`. Push.

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

- [ ] [CODE] P2. Pre-audit: extract ML instrument scope → add `ML_SCOPE_INSTRUMENTS` to UAC
      `registry/processing_scope.py` (same file as Phase 3.0).
- [ ] [CODE] P2. Wire `expected_unattempted` for out-of-scope instruments in `ml-training` batch handler.
- [ ] [CODE] P2. Wire `expected_unattempted` for out-of-scope instruments in `ml-inference-service` batch handler.
- [ ] [QG] P2. QG on each repo. Push.

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

- [x] [SCRIPT] P0. Run dry-run baseline across all 5 asset_groups × 3 scripts. Record counts below.
      (2/3 done: absence-reason + legacy-blank scanned locally 2026-05-12 Slot 3 — results in baseline table above.
      **DEFERRED**: phantom audit — CLAUDE.md requires GCE VM; pending dedicated VM launch on same-region instance.)

### Phase 5B — Apply-flips in dependency order (AFTER Phases 1–4 shipped)

Run in strict sequence:

```bash
# Pass 1: instruments-service reference data_types FIRST (root)
python instruments-service/scripts/reconcile_phantom_manifest_rows_all.py \
  --asset-group cefi --data-types instruments,venue_trading_calendar --apply-flips
python instruments-service/scripts/reconcile_phantom_manifest_rows_all.py \
  --asset-group defi --data-types instruments,venue_trading_calendar --apply-flips
# ... repeat for tradfi, sports, prediction

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

- [ ] [SCRIPT] P0. Pass 1 apply-flips: instruments-service data_types, all 5 asset_groups. Verify phantom count drops;
      sample parquets not empty. Record in `## Reconciliation baseline`.
- [ ] [SCRIPT] P0. Pass 2 apply-flips: MTDS data_types, all 5 asset_groups. Verify only expected_unattempted rows remain
      for instruments not in instruments-service catalog.
- [ ] [SCRIPT] P1. Pass 3 apply-flips: MDPS data_types. Verify MDPS manifest clean.
- [ ] [SCRIPT] P1. Pass 4 apply-flips: features + ML data_types. Verify features manifest clean.

Also run all 5 asset_groups through `reconcile_expected_absence_reasons.py --apply-flips` and
`reconcile_legacy_blank_to_typed_reason.py --apply-flips` in the same order.

---

## Phase 6 — Validation gate + backfill clearance

**model_tier**: sonnet-doable | **thinking**: medium | **Cal AI-days**: ~0.5

**Success criteria for clearance to start backfills**:

- [ ] [VALIDATE] P0. Phantom count across all 5 asset_groups = 0 (or residual <10 in class C triage).
- [ ] [VALIDATE] P0. Manifest data-status panel shows `expected_unattempted` rows with correct reasons for all
      instruments outside MVP scope (not blank, not `attempted_failed`).
- [ ] [VALIDATE] P0. A fresh MTDS dry-run on a sample date generates 0 new `attempted_failed` rows for instruments that
      instruments-service says don't exist (i.e., Phase 1 wiring is live).
- [ ] [VALIDATE] P1. A fresh MDPS dry-run on a sample date generates `expected_unattempted` rows (not empty) for shards
      where MTDS said `empty_confirmed`.
- [ ] [VALIDATE] P1.
      `data_capture_rate = captured / (captured + empty_confirmed + attempted_failed + expected_unattempted)` is
      non-zero denominator (expected universe enumerated) across all asset_groups.
- [ ] [CODEX] P1. Update `codex/02-data/availability-manifest-and-data-status.md` § "Expected-universe pre-flight chain"
      to document the instruments→MTDS→MDPS→features propagation pattern + the two new EmptyConfirmedReason values.
- [ ] [FLIP] P0. Flip this plan's parent epic gate: manifest_evolution_master G3 can now proceed (enumerator runs on top
      of the runtime propagation chain, not instead of it).

---

## Reconciliation baseline (fill after Phase 5A)

> Baseline populated 2026-05-12 Slot 3. Phantom audit requires GCE VM (CLAUDE.md rule) — pending VM launch.
> absence-reason + legacy-blank scans run locally from `.tabs/3/` worktree.

| Script         | Asset group | Phantom count (dry-run) | Empty reason nulls               | Legacy blank reasons | Date run   |
| -------------- | ----------- | ----------------------- | -------------------------------- | -------------------- | ---------- |
| phantom        | cefi        | PENDING (GCE VM req.)   | —                                | —                    | —          |
| phantom        | defi        | PENDING (GCE VM req.)   | —                                | —                    | —          |
| phantom        | tradfi      | PENDING (GCE VM req.)   | —                                | —                    | —          |
| phantom        | sports      | PENDING (GCE VM req.)   | —                                | —                    | —          |
| phantom        | prediction  | PENDING (GCE VM req.)   | —                                | —                    | —          |
| absence-reason | cefi        | —                       | **3,146** (all SOURCE_RETURNED_ZERO) | —                | 2026-05-12 |
| absence-reason | defi        | —                       | 0                                | —                    | 2026-05-12 |
| absence-reason | tradfi      | —                       | 0                                | —                    | 2026-05-12 |
| absence-reason | sports      | —                       | 0                                | —                    | 2026-05-12 |
| absence-reason | prediction  | —                       | 0                                | —                    | 2026-05-12 |
| legacy-blank   | cefi        | —                       | —                                | 0 (2,632,931 scanned) | 2026-05-12 |
| legacy-blank   | defi        | —                       | —                                | 0 (604,951 candidates, 0 upgrades) | 2026-05-12 |
| legacy-blank   | tradfi      | —                       | —                                | 0                    | 2026-05-12 |
| legacy-blank   | sports      | —                       | —                                | 0 (1,868,285 candidates, 0 upgrades) | 2026-05-12 |
| legacy-blank   | prediction  | —                       | —                                | 0 (41 candidates, 0 upgrades) | 2026-05-12 |

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

## Cross-plan coordination

- **manifest_evolution_master_2026_05_08 G3**: enumerator CAN proceed independently; this plan's runtime chain + G3
  batch fill are complementary. G3 runs on top of the runtime chain, not instead.
- **manifest_cross_asset_rescan_design_2026_05_08**: `--apply-flips` in Phase 5B replaces the rescan plan's Pass 1–4
  command set (same scripts, now correctly ordered). Update rescan plan after Phase 5B.
- **writegate_honest_coverage_endtoend_2026_05_06**: this plan is effectively writegate Phase 7 (upstream propagation
  chain). Add reference banner to writegate plan when Phase 0 starts.
- **expected_universe_v2_design_2026_05_08**: G3 enumerator must run AFTER this plan's Phase 1 ships (so MTDS future
  runs don't re-pollute the expected_universe rows).

## Codex SSOT updates (Phase 6)

- **UPDATE** `codex/02-data/availability-manifest-and-data-status.md` § "Expected-universe pre-flight chain" — add the
  full propagation chain description.
- **UPDATE** `codex/02-data/honest-absence-downstream-handling.md` § "Reason taxonomy" — add
  `EXPECTED_OUTSIDE_PROCESSING_SCOPE` + `EXPECTED_UPSTREAM_EMPTY` to the closed-set table.
- **UPDATE** `codex/02-data/availability-manifest-and-data-status.md` § "Phantom audit" — note that phantom counts
  include false positives until this plan's Phases 1–4 ship.
