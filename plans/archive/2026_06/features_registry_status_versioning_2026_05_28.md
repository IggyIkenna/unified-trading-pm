---
name: features_registry_status_versioning_2026_05_28
title: "Features registry expansion + status tags + formula versioning"
parent_epic: features_and_ml_master
assigned_vm: vm-ml
tier: L2
priority: P1
status: active
created: 2026-05-28
last_updated: 2026-05-28
estimate_class: brand-new
estimate_baseline_ai_days: 5
estimate_calibrated_ai_days: 5
locked_by: live-defi-rollout
locked_since: 2026-05-28
codex_ssots:
  - codex/04-architecture/artifact-versioning.md
  - codex/02-data/availability-manifest-and-data-status.md
  - codex/06-coding-standards/strategy-identity-versioning.md
related_plans:
  - ./features_calc_efficiency_and_correctness_2026_05_27.md
  - ./features_service_e2e_pipeline_test_2026_05_26.md
---

# Features registry expansion + status tags + formula versioning

> **✅ ARCHIVED 2026-06-21 — ships clean (own temp-states: none); 4 codex docs written/aligned. Consumer-pin + other-family rollout are epic-owned (features_and_ml_master). [unlock-plan]**

> **Why now**: `codex/04-architecture/artifact-versioning.md` declares the contract (every feature_group has
> `content_hash + monotonic v`, consumers pin by `@vN`, registry retained for replay). features-service has **not
> implemented it**: `formula_version` / `feature_group_version` / `calculator_version` return 0 grep hits across the
> repo, no version column in `DeltaOneFeatureRecord`, no status field on `FeatureSpec`, and **29 of 34 calculator groups
> have no registry entry at all** (Phase 2 distribution + cross-TF tests can't reach them — verified 2026-05-28).
>
> Result: GCS parquets in `features-delta-one-{ag}-{pid}` have no marker tying a row back to which Python implementation
> produced it. Strategy / ML configs cannot pin to a specific formula version, so a formula edit silently changes the
> meaning of every downstream backfill.

## Operator directive (verbatim, 2026-05-28)

> "yes please extend the registry for sure and we have to also give tags to each of these of some kind so we can track
> what is the status of each feature calculator. you can take a look at the
> `.extra/new-sports-batting-services/footballbets/features`, here I have few tags for each calculator and we can even
> extend these status so we can check if the feature group of individual feature is verified and tested you know."
>
> "then we will also need versioning of the features, so for eg if we change the function then we can also see that the
> already available and calculated feature data in gcs, which version it belongs to. and then we can also use different
> versions of functions for different ml models or strategies. I am not talking about the config change for eg rsi 14 vs
> rsi 18, that is config change i am talking about the rsi formula itself."
>
> "its possible that we already have some mechanism to do this already in the codex docs or the code itself, but we will
> definetely need these things to track the data in gcs that this particular parquet file belongs to this particular
> version and config"

## Reference patterns

- **Status tags**: `.extra/new-sports-batting-services/footballbets/features/tracking/` uses
  `(name, status, priority, tables, description)` tuples with closed-set `Status = Literal["C","D","T","L","B","X","N"]`
  (Completed / In-Dev / Tested / Listed / Blocked / Deprecated / Need-Data) and
  `Priority = Literal["high","med","low"]`. Per-category file (`team_features.py`, etc.) + an aggregator script that
  produces summary tables + CSV/Markdown exports.
- **Codex versioning contract** already names: `content_hash` (sha256 truncated)
  - `monotonic_version` per artifact family + consumer pins by `@vN` + retain every version for replay.

## Design

### Layer 1 — FeatureSpec extensions

Extend `features_service.delta_one.app.features.registry.FeatureSpec` with three new declarative fields:

```python
@dataclass(frozen=True)
class FeatureSpec:
    # ... existing fields ...

    # NEW — status tracking
    status: Literal["verified", "tested", "in_dev", "listed", "blocked", "deprecated", "need_data"]
    priority: Literal["high", "med", "low"]

    # NEW — formula identity (NOT config; the math itself)
    formula_version: int  # monotonic; bump only when the formula CHANGES
    formula_hash: str | None  # sha256(canonicalised source of the calculator method); auto-computed
    custom_or_third_party: Literal["custom", "ta_lib", "pandas_std", "numpy_std"]
    # — "custom" = bespoke math, no public reference
    # — "ta_lib" = re-implementation of a ta-lib function (covered by 2.2 equality test)
    # — "pandas_std" / "numpy_std" = thin wrapper around library primitives
```

`formula_version` semantics (deliberate; matches codex `artifact-versioning.md`):

- Bump ONLY when the formula's MATH changes. Not when a config like a window size or threshold changes (that's the
  consumer config layer).
- Once a version is published to GCS, NEVER reuse it for a different formula — archive the old function (renamed `_v1`,
  `_v2`, etc.) and bump to `_v3`.
- Every parquet row carries `formula_version` per emitted column; this is how consumers pin.

### Layer 2 — Registry coverage for 29 missing groups

The 29 calculator groups currently absent from the registry:

| Likely-bespoke (formula needs hand-verification)                          | Likely-standard (still needs cataloguing)        |
| ------------------------------------------------------------------------- | ------------------------------------------------ |
| `microstructure`, `supply_demand_zones`, `level_confluence`, `confluence` | `vwap`, `returns`, `momentum`, `volume_analysis` |
| `signal_confirmation`, `sr_memory`, `statistical_anomaly`                 | `candlestick_patterns` (most ta-lib-equivalent)  |
| `swing_outcome_targets`, `market_structure_sequence`                      | `liquidations`, `funding_oi`, `futures_basis`    |
| `order_flow_inference`, `volume_flow`, `polynomial_trendlines`            | `volatility_realized`, `targets`, `temporal`     |
| `round_numbers`, `streaks`, `risk_reward`, `fibonacci`                    | `economic_events`                                |
| `return_kurtosis`                                                         |                                                  |

Each gets one FeatureSpec per emitted column. Starting status for every new spec: `"listed"` (= "the calculator exists
but we have not yet verified the formula"). Promote to `"tested"` once Phase 2 (2.4/2.6/2.7) catches it.

### Layer 3 — Wire `formula_version` through to GCS parquet

1. Add `{output_name}_formula_version: int8` column to `DeltaOneFeatureRecord` (UAC) for every registered output.
2. `feature_writer.write_daily_partition()` reads the registry, stamps each row's per-column version, asserts every
   emitted column has a spec entry (HARD: refuse to write a column that isn't in the registry).
3. Manifest row key extension: add `formula_versions: dict[str, int]` field (column-name → version) so the consumer sees
   the version mix without reading the parquet.
4. Backfill: existing rows pre-this-change get `formula_version=0` ("legacy, un-versioned"). Strategies opting into
   versioning must pin `>=1`.

### Layer 4 — Status tracker CLI

Mirror the footballbets `feature_status.py` pattern. New module
`features_service/delta_one/app/features/status_report.py`:

```bash
features-status                       # summary table (per-group counts)
features-status --detailed            # full per-group breakdown
features-status --group market_structure
features-status --next 20             # high-priority "listed" features to verify next
features-status --export csv          # to CSV / markdown
features-status --check-drift         # compute formula_hash for each spec, flag if drifted from registry
```

`--check-drift` is the audit-time invariant: if any calculator method's canonical source-hash changes but
`formula_version` doesn't bump, fail loudly in QG. This is the "you changed the formula but didn't bump the version"
guard.

### Layer 5 — Codex alignment

- Update `codex/04-architecture/artifact-versioning.md` § Feature groups to cite the actual implementation paths
  (registry.py, feature_writer.py, status_report.py).
- New codex doc `codex/02-data/feature-formula-versioning.md` — the drift-detection mechanism + the per-column
  `formula_version` parquet column
  - the consumer pin pattern.
- `MEMORY.md` reference to the new docs.

## Phases

### Phase 1 — FeatureSpec schema extension + populate existing 47 specs [P0]

- [x] ✅ [LIB] P0. Add `status`, `priority`, `formula_version`, `implementation` fields to `FeatureSpec`; set defaults
      for the 47 existing specs (technical_indicators/oscillators/moving_averages = "verified";
      market_structure/wedge_quality = "tested"; formula_version=1 baseline) — features@9a53b888.
- [x] ✅ [LIB] P0. Helper `compute_formula_hash(func) -> str` in `formula_hash.py`: canonicalises source (strip
      comments/docstrings/blank lines), sha256-truncated 16-hex digest. Used for drift detection — features@9a53b888.
- [x] ✅ [LIB] P0. 253 new pytest cases (per-spec invariants + hash determinism + canonicaliser strips
      comments/docstrings/blank lines). 2.4/2.6/2.7 still green: 655 + 253 = 908 passed — features@9a53b888.
- [x] ✅ [LIB] P0. basedpyright clean (0 errors). Widened `valid_range` type to
      `tuple[float | None, float | None] | None` so one-sided bounds (e.g. ATR's `(0.0, None)`) typecheck —
      features@9a53b888.

### Phase 2 — Catalog the 29 missing groups [P0]

- [x] ✅ [LIB] P0. Walked every uncatalogued calculator on synthetic OHLCV; added one FeatureSpec per BASE column
      (mechanical derivatives `_lag_N`, `_in_last_N_bars`, `time_since_*` inherit version from base). 47 → 1,382 specs
      across 34 groups (every group in CALCULATOR_REGISTRY). 6 groups requiring extra input columns registered with
      `status="need_data"` placeholder — features@e4e085d1.
- [x] ✅ [LIB] P0. 2.4 / 2.6 / 2.7 parametrization filtered to `status in {"verified","tested"}` so new "listed"
      placeholders don't false-fail. 47 verified/tested specs still pass; 1,335 listed ones are
      documented-but-unverified pending hand audit — features@e4e085d1.
- [x] ✅ [LIB] P0. Coverage delta: registered groups 5 → 34, total specs 47 → 1,382 (top groups: round_numbers 314 /
      momentum 241 / volatility_realized 160 / candlestick_patterns 86 / targets 82). All 8,385 tests pass, basedpyright
      clean — features@e4e085d1.

### Phase 3 — Parquet schema + writer + manifest version wiring [P1]

- [x] ✅ [LIB] P1. **Corrected 2026-05-28 per operator directive**: `feature_group_version` is a GCS HIVE PARTITION KEY
      (`.../feature_group=X/feature_group_version={N}/timeframe=Y/...`) — NOT a per-row column. Selective reads list
      paths instead of scanning every parquet. Writer adds `"feature_group_version": str(version)` to the partition dict
      passed to `data_sink.write(...)`. File-level parquet footer metadata KEPT (3 keys: `feature_group_version` +
      `feature_column_versions` JSON + `feature_group`) for self-describing files / drift detection — features@0fe3160d
      (initial column-based) → features@<next> (corrected to path-based).
- [x] ✅ [LIB] P1. Registry helpers `compute_group_version` + `compute_column_versions` resolve per-group ints from
      `max(spec.formula_version)` matching codex artifact-versioning.md Rule 4 (consumer PIN by
      `technical_indicators@v2`) — features@0fe3160d.
- [x] ✅ [LIB] P1. Sentinel `feature_group_version=0` surfaces in the GCS path (`feature_group_version=0/`) when called
      on a group with no registered specs — operationally visible without parsing per-file metadata. Writer logs
      warning + falls back rather than raising so existing batch handlers don't brick during rollout.
- [x] ✅ [LIB] P1. 10 pytest cases (revised from 8): resolve helper, sentinel fallback, metadata build, parquet metadata
      round-trip via PyArrow for 3 groups, assertion that NO per-row column is added, partition dict carries
      `feature_group_version` key, sentinel surfaces in partition path. 8,407 total tests pass, basedpyright clean.
- [x] ✅ [LIB] P2. ManifestWriter cross-repo extension to also carry `feature_group_version` — **DEFERRED** to follow-up
      plan (touches UTL + UAC contracts; out-of-scope for this layer). **ACK (2026-05-30 slot-2)**: Operator-directed
      DEFERRED at plan-write time. Scope confirmed: ManifestWriter `record_captured()` would need a new
      `formula_versions: dict[str, int]` kwarg + schema-version bump in UTL; `DeltaOneFeatureRecord` in UAC would need
      the matching field; and the features-service writer would need to pass the per-column version dict from
      `compute_column_versions()`. The GCS hive partition key (`feature_group_version=N/`) is already wired
      (features@0fe3160d). Manifest extension deferred to a follow-up plan when UTL+UAC contract changes can be
      sequenced safely. No code changes in this pass.

### Phase 4 — Status tracker CLI + drift detection [P1]

- [x] ✅ [SCRIPT] P1. `features-status` CLI shipped at `features_service.delta_one.app.features.status_report` +
      console-script entry in pyproject.toml. Modes: summary table, --detailed, --group, --next N, --export
      csv|markdown, --check-drift — features@32c0a1ce.
- [x] ✅ [SCRIPT] P1. `--check-drift` emits SHA-256 baseline of every calculator's `_calculate_features` (or `calculate`
      fallback) method. Diff vs prior baseline = drift; ready for QG wiring once recorded hashes are added to
      FeatureSpec — features@32c0a1ce.
- [x] ✅ [SCRIPT] P1. 12 pytest cases cover every CLI mode + drift baseline. 8,405 total tests pass, basedpyright clean
      — features@32c0a1ce.
- [x] ✅ [QG] P2. **DRIFT GATE OPERATIONAL** — features@dd2ed36f shipped 2026-05-29: (a)
      `registry.BASELINE_FORMULA_HASHES` records per-group hash for the 5 verified/tested groups; (b) `check_drift()`
      compares + exits non-zero on mismatch (MATCH/DRIFTED/NEW outcomes; NEW = informational only so the 29 listed
      groups don't fail the gate); (c) QG STEP 5.91 in `scripts/quality-gates.sh` runs every quality-gates invocation. 3
      new tests cover clean baseline + forced-mismatch detection + `main()` exit code propagation. 6,952 total tests
      pass, basedpyright clean. Today's state: `MATCH=5  DRIFTED=0  NEW=29`. Drift detection is now operational, not
      informational — audit item (r) is GREEN.

### Phase 5 — Codex alignment + consumer pin pattern [P2]

- [x] ✅ [DOC] P2. Updated `codex/04-architecture/artifact-versioning.md` § Feature groups row to cite the registry.py
      SSOT path + per-group `max(spec.formula_version)` resolution + link to the new implementation doc.
- [x] ✅ [DOC] P2. New codex doc `codex/02-data/feature-formula-versioning.md` (~190 lines) covering: 4-file
      architecture, per-row sidecar + file-level parquet metadata, group version resolution, bump procedure, 0 sentinel,
      drift detection, status field semantics, consumer pin pattern, composition with other codex docs.
- [x] ✅ [DOC] P2. Consumer pin example
      (`feature_group_refs: [delta_one/technical_indicators@v2, delta_one/market_structure@v1, ...]`) documented in the
      new codex doc § "Consumer pin pattern (target — not yet shipped on strategy side)".
- [x] ✅ [CLAUDE.md] P2. Added 5-line block under "Service architecture" — registry SSOT path / CLI / bump-rule /
      sentinel / codex SSOT pointer.

## Success Criteria

- 47 + 29 = ~76 calculator-output-columns in the registry (all 34 groups represented; expect ~150-200 total specs once
  every column is enumerated).
- Every `features-delta-one-*` parquet written post-Phase-3 has per-column `formula_version` populated.
- `features-status` CLI shows: total / verified / tested / listed / blocked / deprecated per group.
- `--check-drift` is wired in QG; calculator math change without `formula_version` bump fails the build.
- Codex contract (`artifact-versioning.md`) reflects implementation paths.

## Continuous Verification

- QG STEP 5.XX (drift detection) runs every commit touching `features_service/delta_one/app/calculators/`.
- Daily `features-status` snapshot exported to the master plan inventory regenerator's dashboard.

## Deferred / out of scope

- ML / strategy consumer updates to actually PIN feature versions in their configs (post-this-plan; this plan ships the
  version emission, consumers opt in later).
- Other families (volatility, cross-instrument, onchain, multi-timeframe) — same pattern applies, but this plan only
  covers delta_one. Successor plans needed:
  - `features_volatility_registry_status_versioning_<date>.md`
  - `features_cross_instrument_registry_status_versioning_<date>.md`
  - `features_onchain_registry_status_versioning_<date>.md`
  - `features_multi_timeframe_registry_status_versioning_<date>.md`

## Temporary states + their canonical follow-up plans

(none — this plan ships clean)
