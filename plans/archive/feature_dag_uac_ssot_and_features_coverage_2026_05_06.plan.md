---
doc_type: plan
title: feature-dag-uac-ssot-and-features-coverage
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-api, deployment-ui, instruments-service, unified-trading-library]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-06
overview:
  Companion to writegate_honest_coverage_endtoend_2026_05_06 — covers ONLY the features-pipeline gaps writegate defers
  or doesn't touch. (1) UAC feature_group->required_inputs DAG SSOT (writegate explicitly defers this as
  feature_dag_uac_ssot_<TBD>). (2) UAC EXPECTED_FEATURE_GROUPS_BY_SERVICE + FEATURE_COVERAGE_START registries —
  honest-coverage denominator for features (writegate covers raw-data shards, not features). (3) data-status denominator
  clip for features in deployment-api. (4) Phantom-row audit extension to features manifest. (5) ManifestFreshnessCache
  lifted to UTL + adopted in features-sports + features-volatility BatchHandlers.
type: code
epic: data-pipeline-completion
owner: Harsh
locked_by: live-defi-rollout
locked_since: 2026-05-06
completion_gates: { code: C5, deployment: D2, business: B2 }
repo_gates:
  - { repo: unified-api-contracts, code: C0, deployment: none, business: none }
  - { repo: unified-trading-library, code: C0, deployment: none, business: none }
  - { repo: features-sports-service, code: C0, deployment: D0, business: none }
  - { repo: features-volatility-service, code: C0, deployment: D0, business: none }
  - { repo: features-onchain-service, code: C0, deployment: D0, business: none }
  - { repo: features-delta-one-service, code: C0, deployment: D0, business: none }
  - { repo: deployment-api, code: C0, deployment: D0, business: none }
  - { repo: instruments-service, code: C0, deployment: none, business: none }
depends_on: [writegate_honest_coverage_endtoend_2026_05_06]
isProject: false
---

> **ARCHIVED 2026-05-07** — folded into
> [`ml_and_features_master_2026_05_07.md`](../active/ml_and_features_master_2026_05_07.md). All open todos preserved in
> the umbrella's Phase 1-4. This file is the historical SSOT.

# Feature DAG UAC SSOT + features-only coverage

## Audit 2026-05-07

- **Audit run**: 2026-05-07 (parallel-agent pass)
- **Verified**: 11 of 11 unchecked todos
- **Mis-marked DONE → flipped**: 0 (none — all 11 still genuinely pending)
- **In-flight (running VMs)**: none (Phase 1 is pure UAC + UTL code work; no VMs needed yet)
- **Blocked by**:
  - `writegate_honest_coverage_endtoend_2026_05_06` — Phase 2.D `available_at` stamping shape + `LookaheadBiasError` +
    `AVAILABILITY_AT_SEMANTICS` taxonomy must land first (this plan reuses, not redefines). Per writegate handoff
    2026-05-07-late, Tier 1 UTL contract + Tier 2A sports adapters shipped, but `LookaheadBiasError` strict-mode +
    sports `available_at` rename (Phase 2.C) still pending — see writegate handoff cascade.
- **Blocks**:
  - `features_consolidation_and_drilldown_2026_05_06` — Phase 1+2+3 all transitively depend on this plan's UAC SSOTs
    (denominator clip, expected-feature-groups registry).
  - `ml_training_feature_read_perf_2026_05_06` Phase 4 benchmark sign-off — won't measure correctly until features
    manifest is honest (this plan's denominator clip).
  - `master_to_live_defi_2026_05_23` Group D (Coverage & shard 12-14) for features-\* services.
- **Last meaningful commit**: nothing in this plan's scope. Adjacent activity: features-cross-instrument
  `190bea1`/`2804f47`/`071604f`/`d1da107` (paired_dispersion calculator+resolver+catalog+dispatch — Phase 9 of strategy
  v2, NOT this plan); features-onchain `7f1b2a1` (canonical columns — Phase 9, NOT this plan). No commits touch UAC
  `features/required_inputs.py` or UTL `manifest/freshness.py` (paths don't exist).
- **Recommendation**: KEEP active. Phase 1 (UAC + UTL foundations) is mechanically simple and unblocks everything
  downstream. The feature DAG SSOT is one of the highest-leverage 1-day items remaining for `LookaheadBiasError`
  enforcement to be honest. Schedule Phase 1 as soon as writegate Phase 2.D (`AVAILABILITY_AT_SEMANTICS`) lands. Phases
  2-3 are sequenced after but trivially parallelisable across the 3 features-\* services.

## Why this exists (and what it deliberately doesn't cover)

`writegate_honest_coverage_endtoend_2026_05_06.md` (in-flight, locked to live-defi-rollout) is the canonical plan for
`LookaheadBiasError`, `available_at` write-time stamping, sports temporal rules (`stamp_available_at_*` family),
`record_captured` write-gate integration, the 4-pillar gate (incl. cluster validation), and the UAC `BUNDLED_DATA_TYPES`
registry. **This plan does not duplicate any of that.**

Writegate's "Temporary states + their canonical follow-up plans" table (line 113) explicitly defers two items that this
plan picks up:

> "MDPS / features-\* `feature_group → required_inputs[]` DAG inlined per-service — Three services keep their local DAGs
> (features-onchain, features-sports, features-delta-one). Lookahead-bias enforcement still runs but reads from
> per-service DAG. Successor: `feature_dag_uac_ssot_2026_<TBD>.md`"

This plan is that `feature_dag_uac_ssot_2026_<TBD>` plan, plus the four features-only coverage items writegate doesn't
touch (because writegate is scoped to raw-data shards, not features manifests).

## Scope (5 items)

1. **UAC `feature_group → required_inputs[]` DAG SSOT** — single declaration consumed by writegate's
   `LookaheadBiasError` + by deployment-api's denominator clip. Today the DAG is inlined three times across
   features-onchain, features-sports, features-delta-one (per writegate findings).
2. **UAC `EXPECTED_FEATURE_GROUPS_BY_SERVICE` + `FEATURE_COVERAGE_START`** — honest-coverage denominator for the
   features manifest, mirroring the existing `SOURCE_COVERAGE_START` shape for sports sources.
3. **`deployment-api/services/data_status_service.py`** — feature-coverage rollup uses (a) UAC registry as denominator
   (instead of inferring from manifest contents), (b) `_clip_dates_to_feature_coverage(...)` mirroring the sports clip
   helper.
4. **`instruments-service/scripts/reconcile_phantom_manifest_rows_all.py`** — extend audit to probe features manifest
   paths. Add features-specific drift axes (timeframe hive casing, feature_group empty-check).
5. **UTL `ManifestFreshnessCache(ttl_seconds=60)`** — lift the `_refresh_captured_cache` + `_is_now_captured` pattern
   (currently inlined at `/tmp/fill_missing_ohlcv.py` per CLAUDE.md manifest-concurrency principle) to a shared UTL
   helper. Adopt in features-sports + features-volatility BatchHandlers (the two services running under concurrent
   backfill scale-out per the audit).

Out of scope (owned elsewhere):

- `LookaheadBiasError` definition + `available_at` stamping + sports temporal rules — owned by
  `writegate_honest_coverage_endtoend_2026_05_06`.
- Write-gate pillars 1-4 (row-count, NaN ratio, schema match, cluster coverage) — writegate.
- UAC `BUNDLED_DATA_TYPES` + `record_captured` cluster guard — writegate.
- Per-source `available_at` schema columns + `stamp_available_at_*` helpers — writegate.
- ML training feature-read perf — sibling `ml_training_feature_read_perf_2026_05_06`.
- Feature-store consolidation, UTL `FeatureBatchHandler` base, deployment-ui drill-down — sibling
  `features_consolidation_and_drilldown_2026_05_06`.

## Pre-audit manifest

| Symbol                                                                                                                  | Producers | Consumers                                                                                                                                       |
| ----------------------------------------------------------------------------------------------------------------------- | --------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| `unified_api_contracts.canonical.domain.features.required_inputs.FEATURE_REQUIRED_INPUTS: dict[str, list[InputReq]]`    | UAC (new) | writegate's `LookaheadBiasError.assert_no_lookahead()`; data-status denominator clip; phantom audit denominator                                 |
| `unified_api_contracts.canonical.domain.features.registry.EXPECTED_FEATURE_GROUPS_BY_SERVICE: dict[str, list[str]]`     | UAC (new) | data-status denominator; phantom audit denominator                                                                                              |
| `unified_api_contracts.canonical.domain.features.registry.FEATURE_COVERAGE_START: dict[(service, feature_group), date]` | UAC (new) | data-status `_clip_dates_to_feature_coverage`                                                                                                   |
| `unified_trading_library.manifest.freshness.ManifestFreshnessCache`                                                     | UTL (new) | features-sports BatchHandler; features-volatility orchestrator; future backfill scripts (replaces `/tmp/fill_missing_ohlcv.py` ad-hoc inlining) |

## Phased execution DAG

```
Phase 1 [UAC]                 Phase 1 [UTL]                  (parallel)
   |                              |
   +-------------+----------------+
                 |
                 v
Phase 2: features-* + deployment-api integrations (parallel sub-tasks)
                 |
                 v
Phase 3: phantom audit extension + sanity replay
```

QG gate between phases.

## Phase 1 — UAC + UTL (PARALLEL)

### 1A — UAC

- [x] [AGENT] P0. **`FEATURE_REQUIRED_INPUTS` DAG**. Single declaration in
      `unified_api_contracts/canonical/domain/features/required_inputs.py`. Lift the inlined DAG entries currently
      scattered across features-onchain, features-sports, features-delta-one (writegate identified these locations).
      `InputReq(source, data_type, available_at_rule, horizon)` where `available_at_rule` reuses writegate's
      `AVAILABILITY_AT_SEMANTICS` taxonomy (do NOT redefine — import). Export via `unified_api_contracts.features`
      facade. **SHIPPED 2026-05-07 UAC@4a25b07**: dataclass shape
      `InputReq(asset_group, data_type, available_at_rule, horizon, source=None)` — `(asset_group, data_type)` is the
      lookup key into AVAILABILITY_AT_SEMANTICS (data_type alone is ambiguous: `trades` exists in
      cefi+tradfi+prediction). 32 feature_groups seeded: 2 onchain (lst_staking_yields, defillama_tvl) + 30 delta-one
      (price + microstructure + S/R + enrichment + Phase-1 ML). Re-exported from
      `unified_api_contracts.canonical.domain.features` (and via the `unified_api_contracts.features` facade by
      transitivity). 10 onchain + all sports feature_groups omitted pending AVAILABILITY_AT_SEMANTICS defi-vocabulary
      follow-up (see "Temporary states" section below).
- [x] [AGENT] P0. **Per-service registry**. `EXPECTED_FEATURE_GROUPS_BY_SERVICE: dict[str, list[str]]` in
      `unified_api_contracts/canonical/domain/features/registry.py`. Source: each service's `app/calculators/` directory
      listing + the matrix in `/codex/02-data/data-lineage-MTDS-features-ml.md` Layer 3 table. **SHIPPED 2026-05-07
      UAC@4a25b07**: 5 services seeded — features-onchain (12), features-delta-one (33), features-sports (36),
      features-volatility (empty stub per audit 2026-05-07), features-cross-instrument (empty stub pending
      BuilderRegistry rollout). Used by data-status `_build_feature_group_breakdown` denominator clip.
- [x] [AGENT] P0. **Per-feature-group coverage floor**. `FEATURE_COVERAGE_START: dict[tuple[str, str], date]` mirroring
      `SOURCE_COVERAGE_START` shape. Default = epoch when not declared. **SHIPPED 2026-05-07 UAC@4a25b07**: 6 onchain
      floors seeded (Aave V3 mainnet 2022-03-16, Lido stETH 2020-12-18, EigenLayer 2023-06-14, Morpho 2022-06-01).
      `get_feature_coverage_start(service, feature_group) -> date | None` returns None for unregistered pairs (no clip).
- [x] [AGENT] P0. **Tests**. UAC unit tests assert: (a) every service in `EXPECTED_FEATURE_GROUPS_BY_SERVICE` has a
      corresponding directory in workspace; (b) every entry in `FEATURE_REQUIRED_INPUTS` references a real
      source/data_type from existing UAC registries; (c) DAG has no cycles. **SHIPPED 2026-05-07 UAC@4a25b07**: 15 tests
      in `tests/test_feature_dag_ssot.py` covering all 3 plan invariants + helper round-trips + frozen-dataclass
      behaviour + FEATURE_COVERAGE_START sanity (range guard + every key references a registered feature_group). All
      pass; basedpyright clean; ruff clean.

### 1B — UTL

- [x] [AGENT] P0. **`unified_trading_library/manifest/freshness.py::ManifestFreshnessCache(ttl_seconds=60)`**. Methods:
      `is_now_captured(row_key) -> bool`, `refresh()` on TTL expiry, `bulk_load(skip_set)` at startup. Reference impl:
      `/tmp/fill_missing_ohlcv.py` `_refresh_captured_cache` + `_is_now_captured`. Tests must cover concurrent-write
      race: two workers picking up same row_key from a stale skip-set; one's `is_now_captured` returns True after the
      other's `record_captured`; loser skips. **SHIPPED 2026-05-07 UTL@d7902f6**: shipped as
      `unified_trading_library/manifest_freshness.py` (flat path matching the existing
      `manifest_writer.py`/`manifest_consolidator.py` convention; aligns with the audit suggestion that the manifest/
      sub-package isn't worth carving for one new module). Class wraps `read_availability_index(bucket)` with a
      row-key-shaped `frozenset` membership for O(1) per-row lookups. Thread-safe via internal `threading.Lock`. Read
      failure preserves the prior captured set (better to over-fetch than to silently over-skip). 17 unit tests
      including the canonical concurrent-write race scenario (two threads sharing a `threading.Barrier`; loser sees
      winner's write after TTL expiry).
- [x] [AGENT] P0. **Public API**: re-export from `unified_trading_library.manifest`. Document the 60s TTL default and
      the trade-off explicit in CLAUDE.md (don't drop below 30s — burns GCS reads). **SHIPPED 2026-05-07 UTL@d7902f6**:
      `from unified_trading_library import ManifestFreshnessCache, DEFAULT_TTL_SECONDS` works (top-level facade; no
      `unified_trading_library.manifest` sub-namespace per the flat-path convention chosen above). 60s TTL default
      documented in module docstring + DEFAULT_TTL_SECONDS docstring with the "<30s burns GCS reads" + ">60s tolerates
      slightly stale skip decisions" trade-off. CLAUDE.md "Manifest concurrency principle" already documents the 60s
      default — no edit needed.

**Phase 1 success**: UAC + UTL pass quickmerge; downstream services can
`from unified_api_contracts.features import FEATURE_REQUIRED_INPUTS, EXPECTED_FEATURE_GROUPS_BY_SERVICE, FEATURE_COVERAGE_START`
and `from unified_trading_library.manifest import ManifestFreshnessCache`.

### 1A.3 — Sports vocabulary alignment (consolidated from "Temporary states" 2026-05-07)

Closes the sports-vocab gap that left 36 sports feature_groups in `EXPECTED_FEATURE_GROUPS_BY_SERVICE` but absent from
`FEATURE_REQUIRED_INPUTS`. Per workspace rule "follow-ups consolidate into existing plans, not new plans" — the previous
"open a separate plan" annotation is replaced by this concrete todo block. Sequence: pick approach → build resolver →
lift entries → tests.

- [ ] [AGENT] P1. **Pick the resolution approach.** Three options under consideration; ~30 min decision with the
      operator. Append the chosen path under this todo as the "decided" line + flip to `[x]`:
  - (a) **Mapping table** (cheapest) — UAC adds `SPORTS_INPUT_NAME_TO_DATA_TYPE: dict[str, list[tuple[str, str]]]` keyed
    on the bare reference-entity name (e.g. `"target_fixtures" → [("sports", "FIXTURES")]`,
    `"fixtures_history" → [("sports", "FIXTURES")]` — multi-source pairs allowed). Pros: zero changes to
    `BuilderEntry.required_inputs: list[str]`; clean lookup at the resolver. Cons: extra indirection layer.
  - (b) **Tuple-typed required_inputs** (cleanest, more invasive) — change `BuilderEntry.required_inputs: list[str]` →
    `list[tuple[str, str]]` and migrate every sports calculator's declaration. Pros: same shape as
    `FEATURE_REQUIRED_INPUTS`. Cons: 36 calculator-side migrations + risk of breaking other agents' in-flight
    features-sports work.
  - (c) **Namespaced names** — adopt `"sports.FIXTURES"` as the single canonical input-name vocabulary; parse the prefix
    at lookup time. Pros: backwards-compat (string shape unchanged); explicit at call sites. Cons: runtime parsing +
    sports `BuilderEntry` still doesn't match `FEATURE_REQUIRED_INPUTS` shape.
- [ ] [AGENT] P1. **Build the resolver** per the chosen approach. If (a): UAC `SPORTS_INPUT_NAME_TO_DATA_TYPE` dict +
      `resolve_sports_input(name) -> list[InputReq]` helper. If (b): `BuilderEntry` migration + per-calculator sweep. If
      (c): UAC `parse_namespaced_input(name) -> tuple[str, str]` helper + namespacing audit. Tests: every sports
      `BuilderEntry.required_inputs` entry resolves to at least one registered `(asset_group, data_type)` pair in
      `AVAILABILITY_AT_SEMANTICS`.
- [ ] [AGENT] P1. **Lift the 36 sports feature_groups into `FEATURE_REQUIRED_INPUTS`** using the resolver. Mapping
      derived from `features_sports_service` calculator registry — read each calculator's `required_inputs` list and
      convert to
      `InputReq(asset_group="sports", data_type=<resolved>, available_at_rule=<from     AVAILABILITY_AT_SEMANTICS>, source=<from calculator metadata>)`.
      Multi-source entries (e.g. `FIXTURES` from both api_football + footystats) emit one `InputReq` per source.
- [ ] [TEST] P1. **Closed-set guarantee test** (similar to the defi
      `test_phase_1a_2_lift_8_onchain_feature_groups_seeded` shape) — assert each of the 36 sports feature_groups has ≥
      1 input, every input's `(asset_group, data_type)` is in `AVAILABILITY_AT_SEMANTICS`, every `available_at_rule`
      matches the registry. Plus a per-source multiplicity check for the multi-source feature_groups.
- [ ] [DOCS] P1. **Update temporary-states bullet** at line ~363 from "actionable as Phase 1A.3" → "fully closed
      <commit-sha>" with link to the lift commit. Same flip pattern as the defi vocabulary gap above (Half 2 shipped
      UAC@7a3299a).

## Phase 2 — Service integrations (PARALLEL)

### 2A — Replace per-service DAGs with UAC import + wire UTL lookahead helper

- [x] [AGENT] P1. **UTL `assert_no_lookahead_for_feature_group(feature_group, inputs_df, target_ts)` helper**. Concrete
      API for the workspace-wide lookahead-bias check. Reads UAC `FEATURE_REQUIRED_INPUTS[feature_group]` (29 groups),
      computes `max_horizon` across declared inputs, raises `LookaheadBiasError` if any input row has
      `available_at > target_ts - horizon`. Skips silently for unregistered feature_groups, empty df, or missing
      `available_at` col (rollout-friendly degradation). 9 unit tests covering clean-pass / violation-raise /
      unregistered-skip / empty / naive-tz / label / multi-violation. SHIPPED `unified-trading-library@4354276c`,
      exposed via top-level facade. [AUDIT 2026-05-07: SHIPPED]
- [ ] [AGENT] P1. **features-onchain-service**: delete local feature_group → required_inputs DAG (if any) + call
      `assert_no_lookahead_for_feature_group(feature_group, inputs_df, target_ts)` at each calculator's input-load
      boundary BEFORE compute. Sites: `app/calculators/*.py` (12 calculators) — insertion point is the start of
      `calculate_features(raw_data)`. Each calculator must receive `available_at`-stamped raw_data — see prerequisite
      todo below. [AUDIT 2026-05-07: BLOCKED-ON adapter-side `available_at` stamping prerequisite (next todo)]
- [ ] [AGENT] P1. **features-sports-service**: same. Calculators in `features_sports_service/calculators/*.py`. Sports
      `required_inputs` uses reference-entity-name vocabulary (`target_fixtures`, `fixtures_history`, etc.) NOT
      `(asset_group, data_type)`. UAC `FEATURE_REQUIRED_INPUTS` deliberately omits sports — first task here is to decide
      whether sports should be added to UAC SSOT (with reference-entity-name shape) OR sports keeps its own
      `required_inputs` (and the helper skips sports). [AUDIT 2026-05-07: BLOCKED-ON UAC sports vocabulary decision]
- [ ] [AGENT] P1. **features-delta-one-service**: same. Calculator sites in `features_delta_one_service/`. [AUDIT
      2026-05-07: BLOCKED-ON adapter-side `available_at` stamping prerequisite (next todo)]
- [ ] [AGENT] P0. **Adapter-side `available_at` write-time stamping prerequisite (B4 part 2 prerequisite)** — every
      calculator's input adapter MUST stamp `available_at` per the workspace SSOT
      `unified_trading_library.availability_stamping.stamp_available_at_*` (per `AVAILABILITY_AT_SEMANTICS` rules).
      Without the stamp, `assert_no_lookahead_for_feature_group(...)` degrades to a silent no-op via the "missing col"
      branch. Adapters needing stamping (sample): features-onchain DefiLlama / AAVE subgraph / Lido contract / Pyth
      Solana / Chainlink EVM / DefiBalances; features-delta-one MTDS readers; features-volatility VIX / Yahoo readers;
      features-cross-instrument multi-asset-group delta-one concat path. Sequence: adapter stamps → helper validates →
      consumer trusts. Partial coverage already exists via writegate Phase 2.D `available_at` work. [AUDIT 2026-05-07:
      FRESH — load-bearing prerequisite for B4 part 2 wiring above; tracks Phase 2.D writegate dependencies]

### 2B — Adopt `ManifestFreshnessCache`

- [ ] [AGENT] P1. **features-sports-service BatchHandler**: instantiate `ManifestFreshnessCache(ttl_seconds=60)` at
      handler init; call `cache.is_now_captured(row_key)` before any expensive remote call (per-source API fetch).
      Reference: CLAUDE.md "Manifest concurrency principle" rule. **DEFERRED 2026-05-07** — Phase 1B unblocks the cache
      infra, but the BatchHandler already has a `_should_skip_attempted(feature_group)` helper at
      [`batch_handler.py:479`](../../../features-sports-service/features_sports_service/cli/handlers/batch_handler.py#L479)
      keyed by `table_name` (sports `TABLE_SCHEMAS` vocabulary). That table-name vocabulary is NOT aligned with the
      Phase 1A `EXPECTED_FEATURE_GROUPS_BY_SERVICE['features-sports-service']` calculator-output vocabulary (sports
      tables = raw entities like `fixtures` / `lineups` / `odds_snapshot`; calculators = `team_form` / `xg_features` /
      etc.). A clean wire-in needs the manifest row_key shape rationalised first — successor: the same sports vocabulary
      alignment plan flagged in this plan's "Temporary states" section (sports `BuilderEntry.required_inputs` lift).
      Pick up after that lands.
- [ ] [AGENT] P1. **features-volatility-service orchestrator**: same. Skip if manifest already says captured; avoids
      redundant IV-surface fits under concurrent backfill. **DEFERRED 2026-05-07** — features-volatility-service's
      `BuilderRegistry` is a placeholder per audit 2026-05-07 (no calculators registered yet);
      `EXPECTED_FEATURE_GROUPS_BY_SERVICE['features-volatility-service']` is empty. Cache adoption is meaningless until
      the orchestrator ships live IV-surface fits. Pick up alongside features-volatility's BuilderRegistry rollout.

### 2C — deployment-api denominator clip

- [x] [AGENT] P1. **`data_status_service.py`**:
  - Add `_clip_dates_to_feature_coverage(service, feature_group, start, end)` mirroring the sports clip helper at lines
    39-50. Reads UAC `FEATURE_COVERAGE_START`.
  - `_build_feature_group_breakdown` (line 3684): denominator = clipped_dates \*
    `EXPECTED_FEATURE_GROUPS_BY_SERVICE[service]` (instead of inferring from what's been written).
    `found = captured + empty_confirmed`. `missing = attempted_failed`. Same shape as sports.
  - Endpoint `/data_status?check_feature_groups=true` (line 2288) returns honest expected/found/missing per
    feature_group. **SHIPPED 2026-05-07 deployment-api@9b51dfb**: implemented as a sibling method
    `_build_feature_group_breakdown_uac` rather than overriding the existing `_build_feature_group_breakdown` (the
    existing method has a duplicate at L5070 that does timeframe sub-grouping for the v4 detail breakdown path;
    modifying the L4259 wrapper to take a `service` kwarg would have broken the L5427 caller because Python class-body
    resolution lets the L5070 definition win at runtime). Call site at L4197 (features-\* venue-entry rollup) now calls
    the UAC-aware sibling; existing L5427 caller (v4 detail breakdown) keeps the legacy method. Imports use the
    `unified_api_contracts.features` facade per Citadel rules. 8 unit tests in
    `tests/unit/test_feature_group_breakdown_uac.py` covering registered-service UAC denominator, pre-floor-date
    clipping (Aave V3 2022-03-16), empty-EXPECTED stub fallback, and the no-feature_group-column edge case.

**Phase 2 success**: per-service QG passes; data-status feature-coverage % matches honest expected/found/missing when
verified against deployment-ui DataStatusTab on a representative shard.

## Phase 3 — Phantom audit + sanity replay

- [ ] [AGENT] P2. **`instruments-service/scripts/reconcile_phantom_manifest_rows_all.py`**: extend `--asset-group` to
      accept `features` (or add `--features` flag). Probe feature parquet paths via UAC SSOT candidate-path helper
      (mirror sports' `candidate_parquet_paths`). New drift axes: timeframe hive casing, feature_group empty-check
      (parquet exists but is 0 rows or all-NaN beyond writegate's NaN-threshold). Regression test: synthesise a phantom
      row + missing parquet; audit flags it. [AUDIT 2026-05-07: FRESH — actionable; verified absent:
      `reconcile_phantom_manifest_rows_all.py` grep `features|FEATURE_REQUIRED_INPUTS|EXPECTED_FEATURE_GROUPS` → 0 hits
      (the audit only walks raw-data manifests). Soft-blocked-on Phase-1A SSOTs (probe denominator).]
- [ ] [AGENT] P2. **Same-region GCE smoke run** of the audit in `--dry-run` against the features manifest (per CLAUDE.md
      cross-region listing perf rule). Confirm zero phantoms or document genuine drift. [AUDIT 2026-05-07: BLOCKED-ON
      preceding todo.]
- [ ] [AGENT] P3. **Sanity replay** — pick 3 small representative shards (one DeFi onchain, one CeFi delta-one, one
      sports), recompute. Assert: (a) features-\* services no longer carry inlined DAGs (grep returns 0); (b)
      data-status feature-coverage % matches expected (denominator clip works); (c) phantom audit dry-run output is
      parseable. [AUDIT 2026-05-07: FRESH — final acceptance; depends on Phase 1+2+3 + relevant raw-data backfill VMs
      finishing per writegate and the asset-group umbrellas.]

**Phase 3 success**: features manifest is now under the same phantom-audit regime as raw data; data-status shows honest
features coverage end-to-end.

## Success criteria

| Criterion                                                                                                          | Gate |
| ------------------------------------------------------------------------------------------------------------------ | ---- |
| `FEATURE_REQUIRED_INPUTS`, `EXPECTED_FEATURE_GROUPS_BY_SERVICE`, `FEATURE_COVERAGE_START` declared in UAC + tested | C2   |
| Three features-\* services consume UAC DAG (no inlined duplicates)                                                 | C5   |
| `ManifestFreshnessCache` in UTL + adopted by features-sports + features-volatility                                 | C5   |
| data-status feature-coverage % uses UAC denominator + coverage-start clip                                          | C5   |
| Phantom audit covers features manifest                                                                             | C5   |
| Sanity replay passes on 3 representative shards                                                                    | B2   |

## Anti-patterns

- Don't redefine `LookaheadBiasError` or `available_at` stamping helpers — writegate owns them. Import.
- Don't redefine `AVAILABILITY_AT_SEMANTICS` taxonomy — writegate owns. Reuse.
- Don't keep per-service DAGs alive in parallel with the UAC SSOT (workspace "delete deprecated code" rule).
- Don't tune `ManifestFreshnessCache` TTL below 30s — CLAUDE.md says it burns GCS reads for marginal gain.
- Don't add a fallback "if UAC registry missing, infer from manifest" — that's the bug we're fixing.

## Temporary states + their canonical follow-up plans

Per workspace rule "Temporary state must have a named successor plan (no silent 'fix later')". Phase 1A (UAC@4a25b07)
shipped a partial seed of `FEATURE_REQUIRED_INPUTS`; the gaps below must be closed before Phase 2A consumer migration
completes.

- **AVAILABILITY_AT_SEMANTICS defi vocabulary gap — fully closed 2026-05-07.**
  - **Half 1 shipped UAC@2f40c9d**: `lending_indices` / `risk_params` / `rewards` / `flash_loan_events` /
    `eigenlayer_rewards` now registered in
    `unified_api_contracts.canonical.crosscutting.availability_semantics.AVAILABILITY_AT_SEMANTICS` with the
    `tick_timestamp` semantic. 7 unit tests cover every new entry + the closed-set guarantee.
  - **Half 2 shipped UAC@7a3299a**: 8 of the 10 deferred onchain feature_groups lifted into `FEATURE_REQUIRED_INPUTS` —
    `aave_lending_rates` / `aave_utilization` / `aave_risk_params` / `eigen_rewards` / `protocol_rewards` /
    `flash_loan_availability` / `aave_rate_impact` / `onchain_regime`. Mapping derived from
    `features_onchain_service.schemas.feature_builder_registry._metadata` SSOT. The remaining 2 (`fear_greed` +
    `macro_sentiment`) are intentionally NOT lifted — they're live HTTP pass-throughs over Alternative.me + CoinGecko
    sentiment APIs that bypass the manifest entirely. Documented inline in `required_inputs.py` + tracked as a separate
    "External-sentiment-API live-read pass-throughs" bullet below. 3 new unit tests cover: every lifted entry,
    onchain_regime's 2-input structure, and the explicit non-seeding of fear_greed + macro_sentiment.

- **External-sentiment-API live-read pass-throughs (deferred, post-May-23 if needed).** `fear_greed` (live HTTP fetch
  from Alternative.me) + `macro_sentiment` (live HTTP fetch from CoinGecko + DefiLlama) bypass the manifest entirely —
  there's no upstream `(asset_group, data_type)` to enforce LookaheadBias against. Two paths to close, both deferred:
  - (a) Register `crypto_sentiment` and/or `macro_metrics` as DeFi data_types in
    `unified_api_contracts.registry.market_data_categories.DEFI_DATA_TYPES` + add availability_semantics
    - write a captured-tick adapter (probably in MTDS) that snapshots the API output into a manifest data_type on a
      sensible cadence. Then lift the calculators here.
  - (b) Treat both calculators as out-of-band sentiment overlays that don't participate in honest-coverage accounting at
    all (analogous to how options Greeks aren't manifest data_types). Document the carve-out in the
    EXPECTED_FEATURE_GROUPS_BY_SERVICE comment so they don't appear in the denominator either. Decision deferred to a
    focused 2-hour session with the operator. Not a May-23 blocker — these are enrichment features, not core trading
    signals.
- **Sports vocabulary alignment — actionable as Phase 1A.3 (this plan, todos below).** features-sports
  `BuilderEntry.required_inputs: list[str]` uses reference-entity names (e.g. `"target_fixtures"`, `"fixtures_history"`)
  rather than `(asset_group, data_type)` pairs. 36 sports feature_groups appear in `EXPECTED_FEATURE_GROUPS_BY_SERVICE`
  for denominator counting but are absent from `FEATURE_REQUIRED_INPUTS`. Per workspace rule "follow-ups consolidate
  into existing plans, not new plans" — this bullet is no longer a successor-plan placeholder; it's actionable as Phase
  1A.3 under §"Phase 1 — UAC + UTL foundations" below. Pick the approach (mapping table / tuple-typed / namespaced
  names) in the first todo, then ship the lift in subsequent todos.
- **features-volatility-service + features-cross-instrument-service stubs.** Both services have empty
  `EXPECTED_FEATURE_GROUPS_BY_SERVICE` lists today — populate as their respective `BuilderRegistry` patterns consolidate
  (volatility currently a placeholder per audit 2026-05-07; cross-instrument has 20+ calculators in dir but no central
  registry yet). Successor: rolled into Phase 2A consumer-migration when those services adopt the pattern.

## Coordination with writegate

- Watch writegate's commit stream on `live-defi-rollout`; rebase as needed.
- If writegate's Phase 2.D landed before this plan starts, the per-source `available_at` stamping shape is fixed —
  confirm `FEATURE_REQUIRED_INPUTS.available_at_rule` semantics match writegate's `AVAILABILITY_AT_SEMANTICS` exactly.
  If divergent, treat as a writegate amendment, not a fork.
