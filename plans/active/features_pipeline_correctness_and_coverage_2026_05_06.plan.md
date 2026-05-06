---
name: features-pipeline-correctness-and-coverage
overview:
  Pre-backfill correctness + observability hardening for all 8 features-* services. Ship four interlocked things
  before bulk feature compute scales out: (a) UTL write-gate helper covering pillars 2-4 (NaN ratio, schema match,
  cluster coverage), (b) UTL LookaheadBiasError + UAC feature_group->required_inputs DAG + write-time available_at
  stamping, (c) UAC EXPECTED_FEATURE_GROUPS_BY_SERVICE + FEATURE_COVERAGE_START + data-status denominator clip +
  phantom audit extension to features, (d) per-date manifest freshness re-check in features-sports +
  features-volatility BatchHandlers.
type: code
epic: data-pipeline-completion
status: active
owner: Harsh
created: 2026-05-06
locked_by: live-defi-rollout
locked_since: 2026-05-06
completion_gates:
  code: C5
  deployment: D2
  business: B2
repo_gates:
  - repo: unified-api-contracts
    code: C0
    deployment: none
    business: none
  - repo: unified-trading-library
    code: C0
    deployment: none
    business: none
  - repo: features-calendar-service
    code: C0
    deployment: D0
    business: none
  - repo: features-commodity-service
    code: C0
    deployment: D0
    business: none
  - repo: features-cross-instrument-service
    code: C0
    deployment: D0
    business: none
  - repo: features-delta-one-service
    code: C0
    deployment: D0
    business: none
  - repo: features-multi-timeframe-service
    code: C0
    deployment: D0
    business: none
  - repo: features-onchain-service
    code: C0
    deployment: D0
    business: none
  - repo: features-sports-service
    code: C0
    deployment: D0
    business: none
  - repo: features-volatility-service
    code: C0
    deployment: D0
    business: none
  - repo: deployment-api
    code: C0
    deployment: D0
    business: none
  - repo: instruments-service
    code: C0
    deployment: none
    business: none
depends_on: []
isProject: false
---

# Features pipeline — correctness & coverage hardening (pre-backfill)

## Why now

Pre-compute audit `unified-trading-pm/plans/ai/features_pipeline_pre_compute_audit_2026_05_06.md` confirms three hard
gaps that, left in place, will silently corrupt 7 years × 8 services of feature backfill:

1. `LookaheadBiasError` does not exist anywhere; `available_at` column does not exist anywhere; the
   `feature_group → required_inputs` DAG referenced in CLAUDE.md is not implemented.
2. UAC has no `EXPECTED_FEATURE_GROUPS_BY_SERVICE` registry. Data-status denominator is inferred from manifest
   contents, so coverage % can read 100% even when half the feature_groups never wrote a row.
3. `instruments-service/scripts/reconcile_phantom_manifest_rows_all.py` doesn't probe feature parquets — phantom rows
   in the features manifest are invisible.

Plus two perf/concurrency items that are cheap to fix and very expensive to leave:

4. Write-gate (4 pillars from CLAUDE.md SSOT): only pillar 1 (row-count > 0) is implemented. Pillars 2-4 (NaN ratio,
   schema match, cluster coverage) are absent or inlined per calculator.
5. features-sports + features-volatility BatchHandlers iterate without per-date manifest freshness re-check, violating
   CLAUDE.md manifest-concurrency principle. Concurrent backfill VMs will redo each other's work.

All five gaps are pre-conditions for honest scale-out. Once bulk backfill starts, refilling 7 years to fix them is
prohibitive.

## Scope

This plan ships ONE coordinated change set across UAC + UTL + 8 features-* services + deployment-api + instruments-service
(audit script). Sequenced so UAC + UTL land first, then services pick up the new helpers in parallel.

Out of scope: ML training read-perf, feature-store consolidation, UI drill-down — covered by sibling plans
`ml_training_feature_read_perf_2026_05_06.plan.md` and `features_consolidation_and_drilldown_2026_05_06.plan.md`.

## Pre-audit manifest (blast radius)

| Symbol introduced | Consumers (every features-* service + ml-training-service feature reader) |
| --- | --- |
| `unified_trading_library.ml.lookahead_bias_guard.LookaheadBiasError` | features-calendar / commodity / cross-instrument / delta-one / multi-timeframe / onchain / sports / volatility (all 8 calculators); ml-training-service `feature_data_adapter.py` (read-side validation) |
| `unified_trading_library.io.write_gate.validate_shard()` (pillars 2-4) | All 8 features-* writers + MDPS writer (cross-cutting per CLAUDE.md "applies top-to-bottom") |
| UAC `EXPECTED_FEATURE_GROUPS_BY_SERVICE` + `FEATURE_COVERAGE_START` + `FEATURE_REQUIRED_INPUTS` (DAG) | `deployment-api/services/data_status_service.py` (denominator clip); all 8 features-* services (DAG consumed by lookahead guard); `instruments-service/scripts/reconcile_phantom_manifest_rows_all.py` (denominator for phantom check) |
| Per-date freshness re-check pattern (CLAUDE.md `_is_now_captured(row_key)` + 60s TTL) | features-sports BatchHandler, features-volatility orchestrator. (Reference impl: `/tmp/fill_missing_ohlcv.py`.) |

## Phased execution DAG

```
Phase 1 [UAC]            Phase 1 [UTL]                  (parallel)
   |                         |
   +-----------+-------------+
               |
               v
Phase 2: features-* integrations (8 services in parallel)
               |
               v
Phase 3: deployment-api denominator clip + phantom audit extension (parallel)
               |
               v
Phase 4: workspace QG + data-status sanity replay
```

QG gate between every phase.

## Phase 1 — UAC + UTL foundation (PARALLEL)

### Phase 1A — UAC contracts

- [ ] [AGENT] P0. **UAC: `EXPECTED_FEATURE_GROUPS_BY_SERVICE`** — declare static dict
      `dict[str, list[str]]` mapping each features-*-service name to its expected feature_group set. Source: each
      service's `app/calculators/` directory listing + the matrix in
      `codex/02-data/data-lineage-MTDS-features-ml.md` Layer 3 table. Place in
      `unified_api_contracts/canonical/domain/features/registry.py` (new file). Export via
      `unified_api_contracts.features` facade.
- [ ] [AGENT] P0. **UAC: `FEATURE_COVERAGE_START`** — `dict[(service, feature_group), date]` mirroring
      `SOURCE_COVERAGE_START` shape (sports already has this for sources). Floors per-feature-group launch dates so
      data-status denominator clipping works. Default = epoch when not declared.
- [ ] [AGENT] P0. **UAC: `FEATURE_REQUIRED_INPUTS` DAG** — `dict[str, list[InputReq]]` mapping each feature_group to
      its required upstream entities. `InputReq(source, data_type, available_at_rule, horizon)`. `available_at_rule`
      is a discriminated union: `"event_time"` | `"forecast_issue_time"` | `("offset", timedelta)` (e.g. `kickoff − 60min`
      for lineups). Mirror sports temporal rules from CLAUDE.md verbatim.
- [ ] [AGENT] P0. **UAC: `available_at` column declared in feature SchemaContract** — every feature_group's
      SchemaContract row in `unified_api_contracts/internal/schemas/contracts.py::CONTRACT_REGISTRY` adds a
      mandatory `available_at: datetime` column. Tests assert presence.

### Phase 1B — UTL helpers

- [ ] [AGENT] P0. **UTL `unified_trading_library/ml/lookahead_bias_guard.py`** (new module).
      - `class LookaheadBiasError(ValueError)` — raised, never warned. Carries `(feature_group, target_ts, offending_input,
        offending_input_available_at, horizon)`.
      - `def assert_no_lookahead(feature_group: str, target_ts: datetime, inputs: pd.DataFrame, horizon: timedelta) -> None`
        — for each row, asserts `inputs["available_at"] <= target_ts - horizon`. Reads required-inputs spec from UAC
        `FEATURE_REQUIRED_INPUTS`. Strict-mode raise.
      - Unit tests covering: lineups (kickoff−60min), injuries (event-time), post-match xG (match_end_time), weather
        (forecast-issue-time), pre-match odds (publication time).
- [ ] [AGENT] P0. **UTL `unified_trading_library/io/write_gate.py`** (new module). Replaces inlined per-calculator
      validation.
      - `def validate_shard(df: pd.DataFrame | pl.DataFrame, *, contract: SchemaContract, expected_clusters:
        dict[str, int] | None, cluster_extractor: Callable[[str], str] | None, nan_thresholds: dict[str, float] | None)
        -> None` — raises `WriteGateError` if any pillar fails. Pillars: row-count > 0 (or caller used record_empty);
        column types match contract; per-column NaN ratio under threshold (default 0.10, configurable per
        feature_group via UAC); cluster coverage ≥ expected for bundled shards (carries the chain-bundle case for
        Vol futures + sports leagues).
      - Unit tests covering each pillar + a mixed-failure case.
- [ ] [AGENT] P0. **UTL: `ManifestWriter.record_captured` calls `write_gate.validate_shard()` first**. On failure,
      flips to `record_failed(row_key, error=WriteGateError(...))` instead of writing the parquet. This is the
      shard-granularity SSOT enforcement from CLAUDE.md.
- [ ] [AGENT] P0. **UTL: per-date freshness re-check helper** —
      `unified_trading_library/manifest/freshness.py::ManifestFreshnessCache(ttl_seconds=60)`. Lift the
      `_refresh_captured_cache` + `_is_now_captured` pattern from `/tmp/fill_missing_ohlcv.py` into a reusable
      class. Methods: `is_now_captured(row_key) -> bool`, `refresh()` (called on TTL expiry).
- [ ] [AGENT] P0. **UTL unit tests** — concurrent-write race scenario: two workers picking up the same row_key
      from a stale skip-set; one's `is_now_captured` returns True after the other's `record_captured`; loser skips.

**Phase 1 success**: UAC + UTL repos pass quickmerge; new modules land on `live-defi-rollout`; downstream services
can `from unified_trading_library.ml.lookahead_bias_guard import LookaheadBiasError` and
`from unified_trading_library.io.write_gate import validate_shard`.

## Phase 2 — features-* integrations (PARALLEL across 8 services)

For EACH features-*-service:

- [ ] [AGENT] P1. Wire `available_at` stamping at write-time. Per CLAUDE.md sports rules where applicable; for
      market-data-derived features, `available_at = bar_close_ts` is correct and trivial.
- [ ] [AGENT] P1. Wire `assert_no_lookahead(feature_group, target_ts, inputs, horizon)` in calculator base class
      (UTL `BaseFeatureServiceV2` or per-service `app/calculators/base_calculator.py`). Strict-mode raise.
- [ ] [AGENT] P1. Replace inlined validation with `write_gate.validate_shard()` call before parquet write.
- [ ] [AGENT] P1. Confirm `record_empty/failed` is called on every legitimately-empty / write-gate-failed path
      (no silent skips).

For features-sports + features-volatility specifically:

- [ ] [AGENT] P1. Inject `ManifestFreshnessCache(ttl_seconds=60)` into BatchHandler iteration loop. Before any
      expensive remote call (API fetch, parquet read, IV-surface fit), call `cache.is_now_captured(row_key)` and
      skip if True.

**Phase 2 success**: all 8 services pass per-repo quality-gates.sh Pass 1 + quickmerge `--agent`; smoke-test one
feature_group on one date for each service before scale-out (per the "smoke-test one shard before scaling out"
feedback rule).

## Phase 3 — deployment-api + phantom audit (PARALLEL)

- [ ] [AGENT] P2. **deployment-api `data_status_service.py`** —
      - Add `_clip_dates_to_feature_coverage(service, feature_group, start, end)` mirroring sports clip helper. Use
        UAC `FEATURE_COVERAGE_START`.
      - Use UAC `EXPECTED_FEATURE_GROUPS_BY_SERVICE` as denominator instead of inferring from manifest contents.
      - `_build_feature_group_breakdown` (line 3684) flips to honest-coverage rollup: `expected = clipped_dates ×
        EXPECTED_FEATURE_GROUPS`; `found = captured + empty_confirmed`; `missing = attempted_failed`.
- [ ] [AGENT] P2. **`instruments-service/scripts/reconcile_phantom_manifest_rows_all.py`** —
      - Add `--features` flag (or extend `--asset-group features`). Probe feature parquet paths via the same
        candidate-path SSOT. Drift axes to add: timeframe hive casing, feature_group empty-check (parquet exists but
        is 0 rows or all-NaN beyond write-gate threshold).
      - Regression test: synthesise a phantom row + missing parquet; audit flags it.
- [ ] [AGENT] P2. Smoke-test: run audit script in `--dry-run` against features manifest on a same-region GCE VM
      (per CLAUDE.md cross-region listing perf rule). Confirm zero phantoms (or document genuine drift).

**Phase 3 success**: deployment-api PR passes QG; data-status UI now correctly reports honest features coverage
(can verify in deployment-ui after the API deploy).

## Phase 4 — workspace QG + sanity replay

- [ ] [AGENT] P3. Workspace-wide QG sweep across all 12 affected repos. Zero new failures.
- [ ] [AGENT] P3. **Sanity replay** — pick 3 small representative shards (one DeFi, one CeFi, one sports), recompute
      with new pipeline, diff parquet against pre-change output. Diff should show: (a) new `available_at` column, (b)
      identical existing feature columns (lookahead-bias-free calculators were already correct on spot-check), (c) new
      manifest rows with `record_failed(WriteGateError)` for any shard that previously silently wrote NaN/empty.
- [ ] [AGENT] P3. **Data-status sanity** — load deployment-ui DataStatusTab post-deploy. Verify a feature_group with
      a known coverage gap (e.g. understat XG pre-2015-01-16) shows correct denominator + `empty_confirmed` rather
      than missing.

**Phase 4 success**: zero regressions; data-status reflects honest coverage; ready to launch bulk feature backfill VMs.

## Success criteria

| Criterion | Gate |
| --- | --- |
| `LookaheadBiasError` defined + tested in UTL | C2 |
| `available_at` column present in every feature SchemaContract | C2 |
| `validate_shard()` enforces 4 pillars + tests | C2 |
| `ManifestWriter.record_captured` rejects pillar-failed shards | C2 |
| `EXPECTED_FEATURE_GROUPS_BY_SERVICE` + `FEATURE_COVERAGE_START` + `FEATURE_REQUIRED_INPUTS` declared in UAC | C2 |
| All 8 features-* services consume the new helpers | C5 |
| features-sports + features-volatility use `ManifestFreshnessCache` | C5 |
| data-status feature-coverage % matches honest expected/found/missing | D2 |
| Phantom audit covers features manifest | C5 |
| Sanity replay diff shows expected schema additions only | B2 |
| Bulk feature backfill ready to launch | B2 |

## Anti-patterns (don't do)

- Don't add `LookaheadBiasError` as a warn-mode log — strict raise, per CLAUDE.md.
- Don't inline write-gate logic per calculator — lift to UTL once.
- Don't probe legacy GCS paths in the phantom audit — use UAC SSOT path helpers (sports already has
  `candidate_parquet_paths`; mirror that for features).
- Don't `pkill -f` wildcards on backfill VM wrappers (per memory feedback) — use explicit PIDs if any worker needs to
  be killed during smoke-test.
- Don't `record_empty` to mask write-gate failures — `record_failed(WriteGateError)` is the honest signal.
