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

> **Why now**: `codex/04-architecture/artifact-versioning.md` declares the contract
> (every feature_group has `content_hash + monotonic v`, consumers pin by `@vN`,
> registry retained for replay). features-service has **not implemented it**:
> `formula_version` / `feature_group_version` / `calculator_version` return 0
> grep hits across the repo, no version column in `DeltaOneFeatureRecord`, no
> status field on `FeatureSpec`, and **29 of 34 calculator groups have no
> registry entry at all** (Phase 2 distribution + cross-TF tests can't reach
> them — verified 2026-05-28).
>
> Result: GCS parquets in `features-delta-one-{ag}-{pid}` have no marker tying
> a row back to which Python implementation produced it. Strategy / ML configs
> cannot pin to a specific formula version, so a formula edit silently changes
> the meaning of every downstream backfill.

## Operator directive (verbatim, 2026-05-28)

> "yes please extend the registry for sure and we have to also give tags to each
> of these of some kind so we can track what is the status of each feature
> calculator. you can take a look at the `.extra/new-sports-batting-services/footballbets/features`,
> here I have few tags for each calculator and we can even extend these status
> so we can check if the feature group of individual feature is verified and
> tested you know."
>
> "then we will also need versioning of the features, so for eg if we change the
> function then we can also see that the already available and calculated
> feature data in gcs, which version it belongs to. and then we can also use
> different versions of functions for different ml models or strategies. I am
> not talking about the config change for eg rsi 14 vs rsi 18, that is config
> change i am talking about the rsi formula itself."
>
> "its possible that we already have some mechanism to do this already in the
> codex docs or the code itself, but we will definetely need these things to
> track the data in gcs that this particular parquet file belongs to this
> particular version and config"

## Reference patterns

- **Status tags**: `.extra/new-sports-batting-services/footballbets/features/tracking/`
  uses `(name, status, priority, tables, description)` tuples with closed-set
  `Status = Literal["C","D","T","L","B","X","N"]` (Completed / In-Dev / Tested /
  Listed / Blocked / Deprecated / Need-Data) and `Priority = Literal["high","med","low"]`.
  Per-category file (`team_features.py`, etc.) + an aggregator script that
  produces summary tables + CSV/Markdown exports.
- **Codex versioning contract** already names: `content_hash` (sha256 truncated)
  + `monotonic_version` per artifact family + consumer pins by `@vN` + retain
  every version for replay.

## Design

### Layer 1 — FeatureSpec extensions

Extend `features_service.delta_one.app.features.registry.FeatureSpec` with three
new declarative fields:

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
- Bump ONLY when the formula's MATH changes. Not when a config like a window
  size or threshold changes (that's the consumer config layer).
- Once a version is published to GCS, NEVER reuse it for a different formula —
  archive the old function (renamed `_v1`, `_v2`, etc.) and bump to `_v3`.
- Every parquet row carries `formula_version` per emitted column; this is how
  consumers pin.

### Layer 2 — Registry coverage for 29 missing groups

The 29 calculator groups currently absent from the registry:

| Likely-bespoke (formula needs hand-verification) | Likely-standard (still needs cataloguing) |
|---|---|
| `microstructure`, `supply_demand_zones`, `level_confluence`, `confluence` | `vwap`, `returns`, `momentum`, `volume_analysis` |
| `signal_confirmation`, `sr_memory`, `statistical_anomaly` | `candlestick_patterns` (most ta-lib-equivalent) |
| `swing_outcome_targets`, `market_structure_sequence` | `liquidations`, `funding_oi`, `futures_basis` |
| `order_flow_inference`, `volume_flow`, `polynomial_trendlines` | `volatility_realized`, `targets`, `temporal` |
| `round_numbers`, `streaks`, `risk_reward`, `fibonacci` | `economic_events` |
| `return_kurtosis` | |

Each gets one FeatureSpec per emitted column. Starting status for every new
spec: `"listed"` (= "the calculator exists but we have not yet verified the
formula"). Promote to `"tested"` once Phase 2 (2.4/2.6/2.7) catches it.

### Layer 3 — Wire `formula_version` through to GCS parquet

1. Add `{output_name}_formula_version: int8` column to `DeltaOneFeatureRecord`
   (UAC) for every registered output.
2. `feature_writer.write_daily_partition()` reads the registry, stamps each
   row's per-column version, asserts every emitted column has a spec entry
   (HARD: refuse to write a column that isn't in the registry).
3. Manifest row key extension: add `formula_versions: dict[str, int]` field
   (column-name → version) so the consumer sees the version mix without
   reading the parquet.
4. Backfill: existing rows pre-this-change get `formula_version=0` ("legacy,
   un-versioned"). Strategies opting into versioning must pin `>=1`.

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

`--check-drift` is the audit-time invariant: if any calculator method's
canonical source-hash changes but `formula_version` doesn't bump, fail loudly
in QG. This is the "you changed the formula but didn't bump the version" guard.

### Layer 5 — Codex alignment

- Update `codex/04-architecture/artifact-versioning.md` § Feature groups to
  cite the actual implementation paths (registry.py, feature_writer.py,
  status_report.py).
- New codex doc `codex/02-data/feature-formula-versioning.md` — the
  drift-detection mechanism + the per-column `formula_version` parquet column
  + the consumer pin pattern.
- `MEMORY.md` reference to the new docs.

## Phases

### Phase 1 — FeatureSpec schema extension + populate existing 47 specs [P0]
- [x] ✅ [LIB] P0. Add `status`, `priority`, `formula_version`, `implementation` fields to `FeatureSpec`; set defaults for the 47 existing specs (technical_indicators/oscillators/moving_averages = "verified"; market_structure/wedge_quality = "tested"; formula_version=1 baseline) — features@9a53b888.
- [x] ✅ [LIB] P0. Helper `compute_formula_hash(func) -> str` in `formula_hash.py`: canonicalises source (strip comments/docstrings/blank lines), sha256-truncated 16-hex digest. Used for drift detection — features@9a53b888.
- [x] ✅ [LIB] P0. 253 new pytest cases (per-spec invariants + hash determinism + canonicaliser strips comments/docstrings/blank lines). 2.4/2.6/2.7 still green: 655 + 253 = 908 passed — features@9a53b888.
- [x] ✅ [LIB] P0. basedpyright clean (0 errors). Widened `valid_range` type to `tuple[float | None, float | None] | None` so one-sided bounds (e.g. ATR's `(0.0, None)`) typecheck — features@9a53b888.

### Phase 2 — Catalog the 29 missing groups [P0]
- [ ] [LIB] P0. Walk each of the 29 calculator classes; add one FeatureSpec per emitted column (`status="listed"`, `priority` from group's table above, `formula_version=1`, `custom_or_third_party` per the table).
- [ ] [LIB] P0. Re-run 2.4 / 2.6 / 2.7 against the expanded registry; flip status to `"tested"` for any group that passes all three; leave `"listed"` for ones that don't.
- [ ] [LIB] P0. Surface coverage delta in plan body: `count_before` / `count_after` per group.

### Phase 3 — Parquet schema + writer + manifest version wiring [P1]
- [ ] [UAC] P1. Add `*_formula_version: int8` columns to `DeltaOneFeatureRecord`; UAC minor bump.
- [ ] [LIB] P1. `feature_writer.write_daily_partition()` stamps per-column versions from registry; raises `UnregisteredFeatureColumnError` on a column with no spec.
- [ ] [LIB] P1. ManifestWriter row key gains `formula_versions: dict[str, int]`. Test against real GCS parquet.
- [ ] [LIB] P1. Backfill helper: legacy rows pre-this-change get `formula_version=0` (un-versioned sentinel) at read-time, not on a corpus walk (HARD rule: no whole-corpus GCS walks post-Phase-2.2).

### Phase 4 — Status tracker CLI + drift detection [P1]
- [ ] [SCRIPT] P1. `features-status` CLI mirroring footballbets pattern (summary / detailed / per-group / next / export).
- [ ] [SCRIPT] P1. `features-status --check-drift` — re-computes `formula_hash` for each spec, compares against recorded; flags mismatches.
- [ ] [QG] P1. Wire `--check-drift` into features-service `quality-gates.sh` as STEP 5.XX — drift detected ⇒ fail (forces the operator to either bump `formula_version` or revert the math change).

### Phase 5 — Codex alignment + consumer pin pattern [P2]
- [ ] [DOC] P2. Update `codex/04-architecture/artifact-versioning.md` § Feature groups with actual file paths.
- [ ] [DOC] P2. New codex doc `codex/02-data/feature-formula-versioning.md` covering per-column version column, drift detection, consumer pin.
- [ ] [DOC] P2. Strategy / ML config example: `feature_group_refs: [delta_one@v1, market_structure@v2]` pattern.
- [ ] [CLAUDE.md] P2. One-line pointer in `cursor-configs/CLAUDE.md` under "Service architecture" section.

## Success Criteria

- 47 + 29 = ~76 calculator-output-columns in the registry (all 34 groups represented; expect ~150-200 total specs once every column is enumerated).
- Every `features-delta-one-*` parquet written post-Phase-3 has per-column `formula_version` populated.
- `features-status` CLI shows: total / verified / tested / listed / blocked / deprecated per group.
- `--check-drift` is wired in QG; calculator math change without `formula_version` bump fails the build.
- Codex contract (`artifact-versioning.md`) reflects implementation paths.

## Continuous Verification

- QG STEP 5.XX (drift detection) runs every commit touching `features_service/delta_one/app/calculators/`.
- Daily `features-status` snapshot exported to the master plan inventory regenerator's dashboard.

## Deferred / out of scope

- ML / strategy consumer updates to actually PIN feature versions in their configs (post-this-plan; this plan ships the version emission, consumers opt in later).
- Other families (volatility, cross-instrument, onchain, multi-timeframe) — same pattern applies, but this plan only covers delta_one. Successor plans needed:
  - `features_volatility_registry_status_versioning_<date>.md`
  - `features_cross_instrument_registry_status_versioning_<date>.md`
  - `features_onchain_registry_status_versioning_<date>.md`
  - `features_multi_timeframe_registry_status_versioning_<date>.md`

## Temporary states + their canonical follow-up plans

(none — this plan ships clean)
