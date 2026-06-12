---
name: predictions_master
title: "Predictions Master — asset_group umbrella"
type: epic
tier: L0
status: active
priority: P1
assigned_vm: vm-prediction
parent: master_to_live_defi_2026_05_23
created: 2026-05-07
last_updated: 2026-06-20
locked_by: live-defi-rollout
locked_since: 2026-05-07
related_plans:
  - ../active/predictions_other_bucket_and_ui_drilldown_2026_06_20.md
  - ../active/predictions_lookahead_and_reader_migration_2026_06_20.md
  - ../active/predictions_ml_walk_forward_and_arb_2026_06_20.md
  - ../active/prediction_manifest_canonicalisation_2026_06_01.md
  - ../archive/2026_05/available_at_lookahead_bias_completion_2026_05_08.md
  - ../archive/2026_05/kalshi_api_migration_to_elections_subdomain_2026_05_20.md
  - ../active/trading_agent_service_architecture_unlock_2026_05_22.md
---

> **🔧 RESTRUCTURED 2026-06-20 (asset-group-umbrella thinning)**: this epic had accumulated ~30+ open `- [ ]` todos
> INLINE in its body (a frozen May-07/08 snapshot from when child plans were "folded in"). The backlog regen
> (`regen_backlog_from_plan.py`) only scans `plans/active/*.md`, never `plans/epics/`, so those inline todos were never
> dispatched — the epic read as "0 plans / 0%". The inline blocks have been **reconciled, not deleted**: net-new unowned
> work extracted to child active plans (see § "Assigned active plans"); already-owned work pointed at its owning June
> plan; cutover success-criteria routed to the master. No work was dropped and nothing was flipped ✅ without evidence.
> See § "Workstream routing (restructured 2026-06-20)" below for the full map.

> **Cross-link 2026-05-20**: Emits StrategyPnlStreamEvent per UAC contract (see
> trading_agent_service_architecture_unlock plan Phase 1+2). Status: TODO post-cutover unless explicitly listed in this
> plan's May-23 scope.

> **🔴 P0 ABSORBED 2026-05-20 — mega-audit A3 findings for prediction asset_group**: 3,442 `MISSING_EXPECTED` cells.
> KALSHI trades: 1,756 cells missing. POLYMARKET trades: 1,686 cells missing. Both are POST-launch cells (Polymarket
> 2020-09-01, Kalshi 2021-07-30) that should have data — adapter never ran or never emitted. Reassigned slot 9 portion
> per `work_split_2026_05_19_ikenna.md` § "Slot 9 — REASSIGNED" + CLAUDE.md HARD RULE.
>
> **Scope MUST cover every venue × data_type — no asset_group skipped, no deadline-driven cutbacks**.

> **StrategyPnlStreamEvent**: archetypes in this plan emit StrategyPnlStreamEvent per UAC contract (see
> trading_agent_service_architecture_unlock plan Phase 1+2). Status: TODO post-cutover unless explicitly listed in this
> plan's May-23 scope.

# Predictions Master — asset_group umbrella

> **🟡 IN-FLIGHT REFACTOR — `available_at` adapter stamping** (coordinated by
> `available_at_lookahead_bias_completion_2026_05_08` Phase 1). Re-verify per-adapter `available_at` stamping wiring
> before adding new adapters to this plan.

## Codex SSOTs

This plan implements / extends the following codex documents (read these BEFORE making code changes; drift between code
and these docs is a review-blocking failure per `doc → plan → code`):

- [`codex/02-data/availability-manifest-and-data-status.md`](../../codex/02-data/availability-manifest-and-data-status.md)
  — manifest v5 schema + canonical-question-group cluster validation at `record_captured`
- [`codex/02-data/honest-absence-downstream-handling.md`](../../codex/02-data/honest-absence-downstream-handling.md) —
  lifecycle-bounded absence reasons for prediction shards + downstream NaN handling
- [`codex/02-data/prediction-schema-paths.md`](../../codex/02-data/prediction-schema-paths.md) — prediction GCS path
  layout + canonical-question-group bundling (raw market_ids → BTC_UP_DOWN_HOURLY etc.)
- [`codex/04-architecture/batch-live-architecture.md`](../../codex/04-architecture/batch-live-architecture.md) —
  batch=live pipeline guarantees (same shard atom, same fields, same `available_at` semantics across modes)
- [`codex/09-strategy/architecture-v2/cross-cutting/prediction-markets.md`](../../codex/09-strategy/architecture-v2/cross-cutting/prediction-markets.md)
  — prediction-market lifecycle (`market_created_at` / `resolution_time` / `settlement_time`) + canonical-question-group
  SSOT

If any of the docs above is missing, this plan creates a stub for it (see [`codex/`](../../codex/) tree).

## Audit 2026-05-07

- **Audit run**: 2026-05-07 (parallel-agent pass)
- **Verified**: 35 of 35 unchecked todos
- **Mis-marked DONE → flipped**: 0
- **In-flight (running VMs)**: 0 — NO mtds-prediction VMs in current snapshot
- **Blocked by**: `sports_master:Group E gate` (predictions ML half is gated on sports half completion of
  `sports_predictions_e2e` per explicit GATE marker); `manifest_migration_SUPERSEDED_2026_05_21:Stage 3` (Polymarket
  parquet rewrite + manifest reflip is Stage 3); `writegate_honest_coverage_endtoend:Phase 2.A` (placeholder method
  deletion must complete before manifest migration)
- **Blocks**: `master_to_live_defi_2026_05_23:G` (DART manual-trade gate — features pipeline running on representative
  sample is required readiness floor for predictions); does NOT block live trading per master plan
  ("features-pipeline-running, no ML this cycle")
- **Last meaningful commit**: UAC@`af2bc9b` (canonical-question-group SSOT + lifecycle + classifier wrapper — Phase 1A);
  UAC@`5f76bd4` (CLASSIFIER_STABILITY_HASH for prediction-market reclassification gating); UAC@`58cc5f8` (Polymarket
  lifecycle aliases + edge-case regression tests); UAC@`bb24aba` (DATA_TYPE_TO_CLUSTER_REGISTRY +
  SPORTS_FIXTURE_CLUSTERS + PREDICTION_GROUPS); UAC@`a901e91` (vault-venue canonical names + Polymarket CLOB coverage)
- **Recommendation**: KEEP ACTIVE. Phase 1A scaffolding shipped (taxonomy + lifecycle + classifier wrapper SSOTs in
  UAC); BUT no MTDS adapter migration, no instruments-service lifecycle ingestion writer, no parquet rewrite/reflip yet.
  P1 priority is correct (features-pipeline-running, not live-ML, by 2026-05-23). Critical pending: 14 P0 items in 16
  days. Per user direction 2026-05-07 (MEMORY entry C.12 in the plan body): small Polymarket dataset means migration is
  feasible in a single VM run; the OTHER bucket pattern is required to remove "out of scope" badge in deployment-ui.
  Block Phase 5 baseline + ratchet until POLYMARKET no longer renders "out of scope".

## Scope

Single source of truth for **prediction asset_group** work. Per master plan asset-group readiness ladder, predictions is
**features-pipeline-running (no ML this cycle)** by 2026-05-23.

Covers:

- **Canonical question group taxonomy + classifier**: Polymarket / Kalshi raw market_ids → canonical groups
  (`BTC_UP_DOWN_HOURLY` (24/day), `BTC_UP_DOWN_DAILY` (1/day), `SPX_UP_DOWN_DAILY`, `ELECTION_PRESIDENT_2028`, etc.).
  Like options-chain bundling.
- **Polymarket / Kalshi market lifecycle**: `market_created_at` / `resolution_time` / `settlement_time` per market_id.
  MTDS CLOB capture respects bounds (no ticks before created or after settled).
- **`asset_group=prediction` shard atom migration**: from legacy `category=prediction_market` / `data_type=<base_asset>`
  to canonical
  `(asset_group=prediction, venue, data_type=prediction_canonical_question_group, canonical_question_group, day)`.
- **Per-market lifecycle gating in feature compute**: `LookaheadBiasError` extension — features at time T see only
  market_ids where `market_created_at ≤ T`.
- **Predictions ML half of `sports_predictions_e2e`**: ml-training Model 2A walk-forward + arb_calculator + Group E/F ML
  gates. Sports half (288M ODDS_API row migration + MDPS bucketing + FSS) lives in `sports_master`.

**MVP backtest scope** (per
[`codex/09-strategy/mvp-universe-per-asset-group.md`](../../codex/09-strategy/mvp-universe-per-asset-group.md)):
Polymarket subset only by May-23 (BTC_UP_DOWN_HOURLY + other canonical question groups in scope). Kalshi + opinion.trade
backtest/live → 2026-06-15 (per wave2_polymarket plan split 2026-05-13). Tier A archetypes touching Prediction:
arbitrage-event-markets (Polymarket vs CME) + arbitrage-sports-book (Polymarket vs Betfair).

## Current state (2026-05-07)

- **predictions_canonical_question_group_polymarket_migration**: 14/37 = 38% done. Phase 0 audit + classifier shape
  documented; Phase 1 lifecycle ingestion writer + Phase 2 reader/feature/strategy migration NOT yet shipped.
- **UAC `PREDICTION_GROUPS`**: empty registry (`{}`) per CLAUDE.md "Temporary state"; canonical-question-group registry
  seeding pending Phase 1.
- **MTDS POLYMARKET + KALSHI adapters**: write per-row `data_type="trades"` (canonical, aligned with CeFi) via
  `polymarket_adapter.py:531` + `kalshi_adapter.py:256` — NOT the legacy `<base_asset>` shape claimed earlier (that was
  migrated away from previously per Tab 1 sub-agent investigation 2026-05-08). The remaining Phase 2 gap is at the
  manifest-bundling layer: shards need re-bundling by `canonical_question_group` per UAC `BUNDLED_DATA_TYPES` SSOT,
  mirroring `instruments-service@b904785` `engine/orchestrator.py:2133-2186` pattern. See § "Open questions" Q1 for the
  re-scope decision.
- **MTDS UMI tick provider routing**: caller-side legacy `category="prediction_market"` kwarg dropped from
  `umi_tick_provider.py:264-279` (mtds@`3f631b9` 2026-05-08). Factory-internal `VENUE_REGISTRY` tag rename deferred to
  `venue_axis_asset_group_vocabulary_2026_04_25.plan.md` Waves C/D ([UAC] cross-cutting scope).
- **288M ODDS_API legacy row migration**: scoped per `sports_predictions_e2e`; sports half tracked in `sports_master`.

## Open questions

### Q1 — [instruments-live-tab, 2026-05-08 11:30 UTC] — Re-scope of "Replace POLYMARKET writer" todo (line 159)

**Status**: ✅ RESOLVED — operator picked option (a) at 2026-05-08 ~14:30 UTC. See A1 below.

The Phase 2 todo "Replace POLYMARKET writer (`orchestrator.py:1990–1995`): old `data_type = <base_asset>` → new
`data_type = prediction_canonical_question_group`" was investigated by Tab 1's umi-rename sub-agent (mtds@`3f631b9`
adjacent investigation, 2026-05-08). Finding: the original framing as a string rename is wrong.

**Concrete state on disk:**

- No per-`base_asset` writer exists in MTDS source. The legacy `data_type=BTC|ETH|SPX` shape was migrated away from
  previously. Current MTDS prediction adapters
  (`market-tick-data-service/market_tick_data_service/market_interface/adapters/prediction/polymarket_adapter.py:531`
  - `kalshi_adapter.py:256`) write per-row `data_type="trades"` (canonical, aligned with CeFi) via the standard
    `PartitionedTickWriter` path.
- The plan-referenced `market-tick-data-service/market_tick_data_service/engine/orchestrator.py:1990–1995` is the
  bookmaker-odds writer (`venue=bookmaker / instrument_type=odds / data_type=trades / league_id=...`), NOT a POLYMARKET
  writer. The plan's file:line ref is stale.
- The orchestrator's prediction-shard manifest aggregation at `orchestrator.py:2084-2238` uses `data_type_key="trades"`
  from per-row data — neither legacy `<base_asset>` nor canonical `prediction_canonical_question_group`.

**The actual canonical fix** (mirroring `instruments-service@b904785` `engine/orchestrator.py:2133-2186` shape):
manifest-level shard re-bundling by `canonical_question_group` — writing
`data_type=prediction_canonical_question_group` + `underlying=<canonical_group>` per UAC `BUNDLED_DATA_TYPES` SSOT
(`UAC@bb24aba` already added `DATA_TYPE_TO_CLUSTER_REGISTRY` incl `PREDICTION_GROUPS`), with cluster-validation kwargs
at `record_captured`. This is non-trivial DESIGN work — writer-level grouping over per-row trade data, not a string
rename.

**Implicit acknowledgment in plan body**: line 146 ("Integration tests against a live ManifestWriter on the orchestrator
path deferred — bundled within MTDS Phase 2 cluster-gate verification") already concedes this is deferred design work.
The "[SCRIPT] P0. Replace POLYMARKET writer" framing is misleading.

**Decision needed**:

(a) **Manifest re-bundling lands in MTDS orchestrator** — mirror instruments-service@b904785: bundle Polymarket / Kalshi
rows into one
`(asset_group=prediction, venue, data_type=prediction_canonical_question_group, canonical_question_group, day)` manifest
row per canonical group; per-row tick `data_type="trades"` stays as-is on disk; manifest layer is the re-bundling
surface. Cluster gate counts `market_id`s active per (canonical_question_group, day). [Likely answer per the
per-asset-group shard-key matrix in CLAUDE.md.]

(b) **Stay implicit via the per-row `data_type="trades"`** with `canonical_question_group` attached as a separate
manifest column — does NOT match the per-asset-group shard-key matrix in CLAUDE.md, but is closer to current state.

(c) Other re-scope.

Most likely answer is (a) but it's [UAC] + [UTL] + [per-service] cross-cutting design work, which per the Daily
Work-Split Process split principle is Ikenna-side. Tab 1 (Harsh-side) can ship the per-service writer migration once the
cross-cutting helper signature is locked.

**Tab 1 status while waiting**: Polymarket adapter lifecycle gating (`polymarket_adapter.py:454-602`) + Kalshi adapter
lifecycle gating (`kalshi_adapter.py:242-269`) are the SIBLING todos that don't depend on this Q — they could ship in
parallel once the multi-agent collision risk on `kalshi_adapter.py` (already in basedpyright diagnostics from a
concurrent agent's edits) is resolved by main agent. Tab 1 holding pending main's direction on which adapter sub-agent
is safe to spawn.

#### A1 — [main, 2026-05-08 ~14:30 UTC]

**Status**: ✅ RESOLVED — operator (Harsh) confirmed option **(a)** is the correct shape.

**Decision**: ship the MTDS-side migration mirroring the `instruments-service@b904785`
[`engine/orchestrator.py:2133-2186`](../../instruments-service/instruments_service/engine/orchestrator.py) shape.
Manifest-layer re-bundling by `canonical_question_group`:

- Per-row tick `data_type="trades"` stays unchanged on disk (no parquet schema migration; aligned with CeFi).
- MTDS orchestrator groups Polymarket + Kalshi tick rows by `canonical_question_group` (via UAC
  `classify_polymarket_to_canonical_group` / `classify_kalshi_to_canonical_group` SSOT).
- One manifest row per
  `(asset_group=prediction, venue, data_type=prediction_canonical_question_group, canonical_question_group, day)`
  bundle, with `underlying=<canonical_group>` (analogous to options-chain root-bucketing).
- Cluster-validation gate at `record_captured` counts `market_id`s active per `(canonical_question_group, day)` per
  `expected_market_ids_for_canonical_group` from the lifecycle reader. UAC `BUNDLED_DATA_TYPES` /
  `DATA_TYPE_TO_CLUSTER_REGISTRY` SSOT (`UAC@bb24aba`) already declares `PREDICTION_GROUPS` — half the cross-cutting
  helper is already in place.

**Cross-side ordering**: this is cross-cutting [UAC] + [UTL] + [per-service] design work. Per the Daily Work-Split
Process split principle, the cross-cutting helper signature (UAC `BUNDLED_DATA_TYPES` completeness check + UTL
`record_captured` cluster-coverage kwargs for `prediction_canonical_question_group`) is **Ikenna-side**. Tab 1
(Harsh-side) ships the **per-service migration** in MTDS orchestrator once that helper signature is locked. Operator
will flag this to Ikenna via the cross-side handshake protocol.

**Tab 1 immediate actions**:

1. **Resume Phase 2 adapter-level lifecycle gating in parallel** (independent of this Q1 — already partly on disk via
   uncommitted Tab 1 WIP in MTDS):
   - Polymarket adapter (`polymarket_adapter.py:454-602`) lifecycle gating per UAC
     `classify_polymarket_to_canonical_group` + per-market `available_from_datetime`/`available_to_datetime` from
     `instruments-service@98bb167` lifecycle ingestion.
   - Kalshi adapter (`kalshi_adapter.py:242-269`) lifecycle gating — same shape.
   - 2 untracked unit-test files already on disk (`test_polymarket_adapter_lifecycle_gating.py` +
     `test_kalshi_adapter_lifecycle_gating.py`).
   - Multi-agent collision risk on `kalshi_adapter.py` per Tab 1's flag: main confirms current dirty WIP IS Tab 1's own
     (4 modified MTDS files + 2 untracked tests verified post-pull). No concurrent-agent diagnostics block; proceed.

2. **Defer the writer migration to next cycle** until Ikenna locks the cross-cutting helper signature. When that lands
   (Ikenna will announce via cross-side handshake on this plan-of-record's `## Open questions` § or via the work-split's
   cross-side handshake table), Tab 1 spawns a fresh sub-agent for the MTDS orchestrator-bundling layer migration
   mirroring `instruments-service@b904785`.

3. **UMI tick provider rename** (`umi_tick_provider.py:225` data_type rename) ships in parallel with adapter gating —
   independent of writer migration; ship it.

**Decision rationale**: option (a) matches CLAUDE.md "Per-asset-group shard-key matrix → Prediction"
(`(asset_group=prediction, venue, data_type, canonical_question_group, day)`) which is the workspace SSOT; option (b)
would have left a permanent semantic mismatch between the manifest layer and the shard-key matrix and would not have
supported cluster-validation cleanly; option (c) was open but not preferred per the SSOT.

### Q2 — [polymarket-rebundling-tab (Tab F5), 2026-05-08 ~21:30 UTC] — UTL contract gap blocks A1 option (a) implementation as specified

**Status**: ✅ RESOLVED 2026-05-09 — option (δ) shipped: UTL@ef47c81b + MTDS@a2f8d80. See A2 below.

**Context**: Tab F5 (this tab) was spawned to ship the MTDS orchestrator-side migration mirroring
`instruments-service@b904785` per A1 option (a). Pre-req gate confirmed: UAC `BUNDLED_DATA_TYPES` includes
`prediction_canonical_question_group` (UAC@b02335d via cross-side ping `[2026-05-08 13:34 UTC] ikenna-main`); UAC
`PREDICTION_GROUPS` registry fully populated with 9 canonical groups; UAC `expected_market_ids_for_canonical_group`
shipped at `unified_api_contracts.canonical.domain.predictions.lifecycle:103`; UTL `_check_cluster_coverage` +
`check_cluster_coverage_from_counts` + `MissingClusterValidationError` shipped at
`unified-trading-library/unified_trading_library/manifest_writer.py:1862, 1901, 173`.

**The architectural gap surfaced during code-walk**: the contract for `ManifestWriter.record_captured(...)` (UTL
`manifest_writer.py:1968`) requires:

1. A non-empty pandas `df` (used by `_check_cluster_coverage` to extract per-row clusters via
   `df[symbol_column].astype(str).map(cluster_extractor)` at L1961-1963);
2. The `df` to carry an `available_at` column (enforced via `assert_available_at_present(df)` at L2153, raising
   `LookaheadBiasError` if missing).

**Why this blocks the orchestrator-finalize-loop bundling path**: in
`mtds@market_tick_data_service/engine/orchestrator.py` the finalize-loop (line 2084 onwards) iterates
`shard_counts: dict[tuple[str, ...], int]` — a COUNTS-only aggregate. The original tick DataFrames have already been
streamed to per-instrument parquets via `PartitionedTickWriter` (line 891 onwards) and discarded. Reconstructing a
synthetic `df` with the per-row `available_at` semantics for the bundle would require either (a) re-reading every
per-condition_id parquet that was written that day (potentially 100s of MB of GCS round-trips per (venue, day, group)
bundle, defeating the streaming-write architecture), or (b) plumbing the original ticks through the writer and into a
memory-resident bundle df (reverts the OOM fix that motivated `PartitionedTickWriter` at line 906-909).

The CME-OPTIONS chain-bundle precedent at `orchestrator.py:2186-2217` sidesteps this exact problem by:

1. Using the legacy `writer_manifest.add(...)` path (NOT `record_captured`) for the bundle manifest row;
2. Calling
   `ManifestWriter.check_cluster_coverage_from_counts(observed=cluster_counts, expected_root_clusters=cluster_expected)`
   BEFORE `add()` to gate against partial-bundle misses (routing to `record_failed(ClusterCoverageError)` on miss,
   falling through to `add()` on pass);
3. The legacy `add()` path neither requires `df` nor enforces `BUNDLED_DATA_TYPES` (only `record_captured` does the
   `MissingClusterValidationError` raise at L2122-2128 — `add()` bypasses it).

This precedent IS the natural shape for the prediction bundle (counts already present in
`PartitionedTickWriter._row_counts` keyed per condition_id; classifier output is per-row already-known;
`expected_market_ids_for_canonical_group` returns `set[str]`; can be converted to
`{condition_id: PREDICTION_GROUPS[group]["_per_market_min_rows"]}` for `check_cluster_coverage_from_counts`).

**HOWEVER**, mirroring the CME-OPTIONS precedent for the prediction bundle creates a documented SSOT-vs-precedent
tension:

- **CLAUDE.md "Cluster validation MANDATORY at `record_captured` for bundled shards"** says "**QG STEP 5.64 statically
  walks every `record_captured(` callsite + asserts the kwargs are passed when the literal data_type is bundled**". The
  CME-OPTIONS path uses `add()` not `record_captured` for `data_type="trades"` (which is NOT in `BUNDLED_DATA_TYPES`),
  so it technically isn't violating the rule today. But for prediction we'd be calling
  `add(data_type= "prediction_canonical_question_group")` for a data_type that IS in `BUNDLED_DATA_TYPES` — a call shape
  the future-QG static walk would flag as a violation.
- **CLAUDE.md "No double SSOT in data-saving methodology"** says "Where two paths produce the same outcome, one is
  deleted." The orchestrator-finalize-loop has TWO bundle-validating paths today: (1) the
  `record_captured(data_type=…, expected_root_clusters=…, cluster_extractor=…)` path which IS the "right shape" but
  requires df+available_at; (2) the `check_cluster_coverage_from_counts → add()` path which is a counts-only path used
  for CME-OPTIONS and clearly the only path that works with the streaming-finalize architecture. The "right shape" path
  is unreachable for the orchestrator finalize loop without an architectural change.

**The architectural decision needed**: which option is canonical?

(α) **Mirror CME-OPTIONS precedent** — call `check_cluster_coverage_from_counts(...)` then
`add(data_type="prediction_canonical_question_group", underlying=<group>, …)`. Ships today; no UTL changes needed;
matches existing chain-bundle precedent. **Tradeoff**: future QG STEP 5.64 AST-walk flags this as a violation of the
"Cluster validation MANDATORY at `record_captured`" rule. CLAUDE.md would need an explicit "exception for
orchestrator-finalize-loop bundles where df is unavailable" clause, OR option (β/γ) ships in parallel.

(β) **Lift a new UTL helper `record_captured_from_counts(...)` that accepts**:

- `row_key` + `data_type` + `expected_root_clusters` + `cluster_observed: Mapping[str, int]` instead of `df` +
  `cluster_extractor`;
- An `available_at_envelope: tuple[datetime, datetime]` (min, max across the bundled rows) stamped at write-time by the
  orchestrator from per-instrument parquets' tick timestamp + scrape latency, instead of
  `assert_available_at_present(df)`.
- Internally calls `check_cluster_coverage_from_counts` + the existing schema-validation + manifest-row-emit but skips
  the df-required gates.

This unifies the "right shape" with the streaming-finalize architecture; CME-OPTIONS would migrate to it too.
**Tradeoff**: cross-cutting [UTL] design work — Ikenna-side. Adds 1-2 days to the prediction-bundle ship surface.

(γ) **Plumb a synthetic bundle df through the orchestrator** — `PartitionedTickWriter` keeps a minimal "bundle ledger"
(per-(asset_group, venue, group) lightweight df with columns `[symbol/condition_id, available_at]` only — N rows per
cluster, NOT N rows per tick) so the finalize loop can pass it to `record_captured`. **Tradeoff**: per-shard memory cost
grows proportional to cluster count (HOURLY=24, DAILY=1 → trivial). Schema stays unified. Ships in 1 day on Ikenna-side
once the writer extension lands.

(δ) **Ship α now + open a Wave-2 successor plan to consolidate to β or γ**. Predictions writer migration unblocks
immediately; the SSOT-vs-precedent reconciliation lands as a separate workstream. Per CLAUDE.md "Temporary state must
have a named successor plan" rule.

**Recommendation from Tab F5**: option (δ) — ship α now per the CME-OPTIONS precedent (which is already running in
production for ES.OPT bundles + presumably under scrutiny each release), with a `## Temporary states` entry in this plan
citing a new `utl_record_captured_from_counts_for_streaming_bundles_2026_05_09.md` (or similar) successor plan that
lifts options β/γ to the unified path. Tab F5 stops here pending the architectural call from the operator OR
Ikenna-main. Predictions Phase 2 deferred work continues unblocked (adapter lifecycle gating already shipped per
mtds@7643a5c + e8a6903).

**Tab F5 stop posture**:

- Confirmed UAC + UTL pre-reqs (cross-side ping ack + code-walk verified).
- Read instruments-service@b904785 + 98bb167 reference impl (writer + lifecycle adapter).
- Mapped MTDS orchestrator finalize-loop architecture (line 2071-2238 + PartitionedTickWriter line 891-1192).
- Identified UTL contract gap (described above).
- Did NOT ship code (per "Clear context = implement, don't ask" rule has explicit exception: "Don't apply when... the
  operation is destructive beyond what was authorized"; here, shipping α without operator buy-in on the SSOT tension is
  the architectural-debt equivalent of destructive).
- Foot-gun #4 (prek auto-revert) NOT observed this session.
- Working tree clean on MTDS (zero edits made).

#### A2 — [main, 2026-05-09 ~14:30 UTC]

**Status**: ✅ RESOLVED — option (δ) chosen.

Operator picked option (δ) per `wave2_polymarket_record_captured_from_counts_2026_05_09.md` Phase 1 + 3:

1. UTL helper `record_captured_from_counts(...)` shipped at UTL@ef47c81b — accepts pre-aggregated `total_rows`,
   `observed_clusters`, `available_at_envelope: pd.Timestamp` instead of df. Same 4-pillar gate (cluster coverage +
   available_at presence + row-count > 0); routes under-coverage to `record_failed(ClusterCoverageError)`, zero-rows to
   `record_empty(SOURCE_RETURNED_ZERO)`.
2. MTDS orchestrator finalize-loop branch shipped at MTDS@a2f8d80 — per-venue `prediction_cluster_counts_by_venue` +
   `prediction_envelope_by_venue` accumulators feed into `record_captured_from_counts` per
   `(canonical_question_group, processing_date, venue)`. Envelope =
   `max(per-row available_at) + emission_latency_ms_for_source("polymarket_clob")` (200ms per UAC@e197173).
3. CLAUDE.md "Cluster validation MANDATORY" rule untouched — the new path satisfies the gate via the unified helper, not
   via an exception clause. Wave-2 plan tracks Phase 4 (legacy `add()` deletion) as the future SSOT cleanup so the
   double-SSOT collapses cleanly post-cutover.

## Critical path

| Workstream                                                                       | Status                          | Source                                                      |
| -------------------------------------------------------------------------------- | ------------------------------- | ----------------------------------------------------------- | ----------- | ---- |
| Canonical question group taxonomy + classifier                                   | Phase 0 audit done              | `predictions_canonical_question_group_polymarket_migration` |
| Lifecycle ingestion (created_at / resolution / settlement per market_id)         | NOT started                     | same                                                        |
| Polymarket adapter migration (data_type rename)                                  | NOT started                     | same                                                        |
| Kalshi adapter migration                                                         | NOT started                     | same                                                        |
| Reader-side migration (callsites: `data_type=BTC                                 | ETH                             | ...` → canonical_question_group)                            | NOT started | same |
| Per-market lifecycle gating in features compute (`LookaheadBiasError` extension) | NOT started                     | same                                                        |
| Strategy-service prediction archetypes — canonical_group config                  | NOT started                     | same                                                        |
| Manifest reflip + parquet migration scripts                                      | scoped                          | same                                                        |
| ML training Model 2A walk-forward (predictions half)                             | gated on sports half completion | `sports_predictions_e2e`                                    |
| arb_calculator in FSS                                                            | scoped                          | `sports_predictions_e2e`                                    |
| Predictions MTDS slice to ≥99%                                                   | partial                         | `market_tick_data_to_100pct` (predictions slice)            |

## Workstream routing (restructured 2026-06-20)

The predictions work is dispatched through child active plans (regen scans `plans/active/`, not this epic). Every former
inline todo block below maps to one of these homes — nothing dropped, nothing flipped ✅ without evidence:

| Former inline block                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 | Disposition                              | Home (the live, dispatchable plan)                                                                                                                                                                                                                                                                                                                                                                                 |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Synthetic `OTHER` canonical-question-group bucket end-to-end (UAC `PREDICTION_GROUPS` seeding incl OTHER · classifier `OTHER_BUCKET_MEMBER_ADDED` event · writer-rebundle OTHER coverage); data-status predictions panel `(venue, canonical_question_group, day)`; deployment-ui 3-level `asset_group → canonical_question_group → cadence` drilldown + per-shard parquet download; the timeline/panel "out of scope" VERIFY gates; Phase-5 30+ canonical-groups backfill remainder; prediction sentinel fan-out for empty CQG rows | **EXTRACTED (net-new)**                  | [`predictions_other_bucket_and_ui_drilldown_2026_06_20`](../active/predictions_other_bucket_and_ui_drilldown_2026_06_20.md)                                                                                                                                                                                                                                                                                        |
| Reader callsite migration to `prediction_canonical_question_group`; per-market `LookaheadBiasError` feature-compute enforcement (stated twice in the body — written as ONE todo); strategy-service archetype configs reference `canonical_question_group`; E2E smoke 1 group × 1 day; predictions feature_groups → UAC `FEATURE_REQUIRED_INPUTS`                                                                                                                                                                                    | **EXTRACTED (net-new)**                  | [`predictions_lookahead_and_reader_migration_2026_06_20`](../active/predictions_lookahead_and_reader_migration_2026_06_20.md)                                                                                                                                                                                                                                                                                      |
| Model 2A walk-forward; acceptance metrics (log-loss/calibration/AUC); training-config sanity; Group-F AUC≥0.55/calib≤5% gate; FSS `arb_calculator`; model-registry persistence; predictions MTDS completion-% slice — all the predictions ML half of `sports_predictions_e2e` (sports_master line 148 confirms these belong here, NOT sports). GATED ON `sports_master:Group E` (FSS ≥95% non-NULL).                                                                                                                                | **EXTRACTED (net-new)**                  | [`predictions_ml_walk_forward_and_arb_2026_06_20`](../active/predictions_ml_walk_forward_and_arb_2026_06_20.md)                                                                                                                                                                                                                                                                                                    |
| Writer-rebundling (`Replace POLYMARKET writer`) + manifest/parquet canonicalisation + reflip + reconcilers + `category=→asset_group=` migration + `_index` v9 rebuild + CF-7 relabel                                                                                                                                                                                                                                                                                                                                                | **OWNED ELSEWHERE — do not duplicate**   | [`prediction_manifest_canonicalisation_2026_06_01`](../active/prediction_manifest_canonicalisation_2026_06_01.md) (slot-5 Prediction master orchestrator: single-walk legacy→canonical migration E1–E8 + writer rebundle by `canonical_question_group` + `record_captured_from_counts` atom). The epic's own resolved Open-Questions Q1/A1 + Q2/A2 (UTL@ef47c81b / MTDS@a2f8d80) are this plan's design decisions. |
| Lifecycle-bounded `available_at` stamping for Polymarket + Kalshi adapters (`available_at = max(tick_ts, market_created_at)`, refuse rows past `market_settlement_time`)                                                                                                                                                                                                                                                                                                                                                            | **OWNED ELSEWHERE — do not duplicate**   | [`available_at_lookahead_bias_completion_2026_05_08`](../archive/2026_05/available_at_lookahead_bias_completion_2026_05_08.md) Phase 1 (distinct from the FEATURE-COMPUTE per-market gate, which is in the lookahead child plan above)                                                                                                                                                                             |
| May-23 deliverable success criteria (Polymarket/Kalshi backtest, data pipeline clean, cross-asset features, cluster-validation, strategy+execution progressed)                                                                                                                                                                                                                                                                                                                                                                      | **ROUTED TO MASTER**                     | [`master_to_live_defi_2026_05_23`](../active/master_to_live_defi_2026_05_23.md) — predictions readiness ladder = "BACKTEST only / features-pipeline-running (no ML this cycle)"                                                                                                                                                                                                                                    |
| Opinion Trade backtest + CME event-futures arb backtest                                                                                                                                                                                                                                                                                                                                                                                                                                                                             | **ROUTED TO MASTER as OUT/post-cutover** | Both CONTRADICTED by this epic's own resolved Open-Questions ("OUT for May-23" — Opinion Trade has no integration this cycle; CME event-contracts need a separate adapter + catalog, deferred). Not active work.                                                                                                                                                                                                   |

The blocks below are the **frozen May-07/08 source snapshot**, retained for archaeology only. They are SUPERSEDED by the
routing table above — do NOT pick work from them directly.

## Consolidated todos (P0 only) — SUPERSEDED 2026-06-20 (history only; see § "Workstream routing")

> **SUPERSEDED 2026-06-20**: the open `- [ ]` items in this section are EXTRACTED to the child plans (taxonomy/OTHER/UI
> → `predictions_other_bucket_and_ui_drilldown`; reader/feature/strategy migration →
> `predictions_lookahead_and_reader_migration`; ML walk-forward + arb → `predictions_ml_walk_forward_and_arb`) or OWNED
> ELSEWHERE (manifest/parquet migration + writer-rebundling → `prediction_manifest_canonicalisation_2026_06_01`;
> `available_at` adapter stamping → the `available_at_lookahead_bias_completion` plan). Do NOT dispatch from here.
> Retained below for context only.

### Canonical-question-group taxonomy + lifecycle ingestion

- [x] [AUDIT] P0. Classifier stability hash design — pending; audit-3 documented existing classifier shape but hash
      design not finalized. [AUDIT 2026-05-07: DONE — UAC@5f76bd4 (CLASSIFIER_STABILITY_HASH for prediction-market
      reclassification gating)]
- [x] [SCRIPT] P0. Lifecycle ingestion in instruments-service: capture `market_created_at`, `resolution_time`,
      `settlement_time` per conditionId / Kalshi ticker. [AUDIT 2026-05-07: FRESH — actionable; UAC SSOT (af2bc9b
      lifecycle wrapper) is in place but instruments-service writer not yet shipped] (instruments-service@98bb167 —
      Polymarket + Kalshi adapters expose `classify_lifecycle()` + `get_market_lifecycles()` returning per-market
      `MarketLifecycle` rows keyed on UAC canonical_question_group; `available_from_datetime` / `available_to_datetime`
      stamped on the emitted InstrumentRecord — orchestrator MARKET_LIFECYCLE writer pending)
- [x] [SCRIPT] P0. New writer path in `engine/orchestrator.py` for prediction with canonical_group + lifecycle. [AUDIT
      2026-05-07: FRESH — actionable] (instruments-service@b904785 — Polymarket + Kalshi prediction writer at
      `engine/orchestrator.py:2128` now bundles by `canonical_question_group`; manifest emits
      `data_type=prediction_canonical_question_group` + `underlying={GROUP}` per UAC `BUNDLED_DATA_TYPES` SSOT.
      MARKET_LIFECYCLE separate parquet emit deferred to Phase 2 — lifecycle metadata is already discoverable via
      `InstrumentRecord.available_from_datetime` / `available_to_datetime` stamped in 98bb167)
- [x] [SCRIPT] P0. `_extract_prediction_shard` / `_compute_prediction_shards` (orchestrator.py:2497–2524) call
      classifier; emit
      `(asset_group=prediction, venue, data_type=prediction_canonical_question_group,     canonical_question_group, market_id, day)`
      shard atom. [AUDIT 2026-05-07: FRESH — actionable] (instruments-service@b904785 — replaced with
      `_extract_prediction_canonical_group(row)` calling `classify_polymarket_to_canonical_group` /
      `classify_kalshi_to_canonical_group` from UAC; per-market_id manifest row deferred to Phase 2 along with the
      bundle-level cluster-coverage gate at `record_captured` that consumes `expected_market_ids_for_canonical_group`
      from the lifecycle reader)
- [x] [TEST] P0. instruments-service unit + integration tests for lifecycle ingestion + classifier integration. [AUDIT
      2026-05-07: FRESH — actionable] (instruments-service@98bb167 + b904785 — 14 lifecycle tests + 9 canonical-group
      shard tests; full unit suite 2267 passing post-change. Integration tests against a live ManifestWriter on the
      orchestrator path deferred — bundled within MTDS Phase 2 cluster-gate verification)

### Adapter migration (MTDS — Polymarket + Kalshi)

- [x] [SCRIPT] P0. Polymarket adapter (`polymarket_adapter.py:454–602`): read lifecycle from instruments-service; reject
      ticks outside `[market_created_at, settlement_time]` window per CLAUDE.md "Prediction market lifecycle timing"
      rule. [AUDIT 2026-05-07: BLOCKED-ON predictions_master:lifecycle-ingestion writer in instruments-service (Phase 1)
      → BLOCKER CLEARED 2026-05-08 by instruments-service@`98bb167` + `b904785`] **SHIPPED mtds@`7643a5c`**
      "feat(predictions): Polymarket adapter per-market lifecycle gating + tests" — `_LifecycleBounds` at
      `polymarket_adapter.py:135` + `_load_lifecycles_from_gcs` at `:834` confirmed on origin. **WIP-READY ON-DISK
      2026-05-08 (Tab 1 instruments-live-tab — pending main-agent commit + push)**:
      `market_tick_data_service/market_interface/adapters/prediction/polymarket_adapter.py` (~268-line diff vs HEAD)
      adds frozen `_LifecycleBounds` dataclass + `_load_lifecycles_from_gcs(date)` static method reading
      `instrument_availability/by_date/day=…/venue=POLYMARKET/instruments.parquet` (the same parquet
      `_load_instruments_from_gcs` reads) extracting `available_from_datetime` (= `market_created_at`) +
      `available_to_datetime` (= `settlement_time`) per `condition_id`; `download_batch` now drops ticks with
      `tick_ts < market_created_at` or `tick_ts >= settlement_time` per market and counts the rejected counts in a
      summary log line; emits `canonical_question_group` column derived via UAC
      `classify_polymarket_to_canonical_group(title, slug, event_slug, outcome, condition_id)` (sub-classifier output →
      `OTHER` for unrecognised); stamps per-row `available_at = max(ts_event, market_created_at)` (the `created_floor`
      clamp) per CLAUDE.md "available_at is per-row, write-time, equal to live-pipeline-arrival" rule;
      `_coerce_to_aware_utc` helper handles parquet/JSON/`pd.NaT` lifecycle-cell coercion (covered by 1 dedicated test).
      7 dedicated regression tests in `tests/unit/test_polymarket_adapter_lifecycle_gating.py` (260 lines, 7/7 GREEN
      under `pytest tests/unit/test_polymarket_adapter_lifecycle_gating.py -v`): pre-creation 1d / 1min before, post-
      settlement, in-window with `available_at` stamp, `canonical_question_group` column emit, no-lifecycle = no-gating
      graceful-degrade, `_coerce_to_aware_utc` ISO/`pd.Timestamp`/datetime/None/NaT handling. **Cluster- validation
      kwargs at `record_captured` for the bundled `prediction_canonical_question_group` data_type** DEFERRED to Q1 →
      option (a) writer migration (Ikenna-side cross-cutting helper signature lock first); Phase 2 adapter-level work
      scope correctly stops at the per-row column emission + lifecycle gate.
- [x] [SCRIPT] P0. Kalshi adapter (`kalshi_adapter.py:242–269`): same migration. [AUDIT 2026-05-07: BLOCKED-ON
      predictions_master:Phase 1 lifecycle ingestion → BLOCKER CLEARED 2026-05-08 by instruments-service@`98bb167`]
      **SHIPPED mtds@`e8a6903`** "feat(predictions): Kalshi adapter per-market lifecycle gating + tests" —
      `_load_lifecycles_from_gcs` at `kalshi_adapter.py:369` confirmed on origin. **WIP-READY ON-DISK 2026-05-08 (Tab 1
      — pending main-agent commit + push)**:
      `market_tick_data_service/market_interface/adapters/prediction/kalshi_adapter.py` (~233-line diff vs HEAD) adds
      module-level `_coerce_datetime` + `_extract_lifecycles_from_dataframe` + `_extract_lifecycles_from_records`
      helpers + `_load_lifecycles_from_gcs(date) -> dict[ticker, (created, settlement)]` (replaces legacy
      `_load_tickers_from_gcs` which is retained as a one-line legacy wrapper); reads
      `instrument_availability/by_date/day=…/venue=KALSHI/instruments.parquet` (parquet path) with JSON fallback
      (`instruments.json` / `.jsonl`); `download_batch` now drops ticks with `tick_ts < market_created_at` or
      `tick_ts >= settlement_time` per ticker and counts rejected; emits `canonical_question_group` column via UAC
      `classify_kalshi_to_canonical_group(ticker)` (`KALSHI_TICKER_TO_GROUP` override-only registry currently empty per
      CLAUDE.md "Synthetic OTHER bucket" rule, so most rows route to `CanonicalQuestionGroup.OTHER` — that's the valid
      catch-all bucket); stamps per-row `available_at = max(tick_ts, market_created_at)` (`created_floor` clamp);
      CLI-passed `instrument_ids` short-circuit to `(None, None)` lifecycle = no gating (caller-decision matching the
      polymarket short-circuit shape). 9 dedicated regression tests in
      `tests/unit/test_kalshi_adapter_lifecycle_gating.py` (357 lines, 9/9 GREEN under
      `pytest tests/unit/test_kalshi_adapter_lifecycle_gating.py -v`): pre-creation 1d / 1min, post-settlement,
      in-window with `available_at`, `available_at` floored to `market_created_at`, `OTHER` canonical-group capture,
      no-gating-when-instrument_ids-passed, lifecycle-loader-reads-parquet-columns, per-market filter applies
      independently (3 tickers — active / pre-creation-bound / post-settlement-bound — each gated by its own market's
      lifecycle, not a global window). Same Phase-2-scope-stops-at-per-row-emission discipline as Polymarket (writer
      migration deferred).
- [x] [SCRIPT] P0. `umi_tick_provider.py:225`: replace `category="prediction_market"` with `asset_group="prediction"` +
      `data_type="prediction_canonical_question_group"`. [AUDIT 2026-05-07: FRESH — actionable; UAC@bb24aba already
      added DATA_TYPE_TO_CLUSTER_REGISTRY incl PREDICTION_GROUPS] (mtds@`3f631b9` 2026-05-08 by Tab 1 umi-rename
      sub-agent — caller-side legacy `category="prediction_market"` kwarg dropped from `umi_tick_provider.py:264-279`
      `get_adapter()` call in the prediction-venue (POLYMARKET/KALSHI) branch; mock assertion in
      `tests/unit/test_umi_tick_provider_routes.py:157` updated; 3 prediction-routing tests pass. Factory-internal
      `VENUE_REGISTRY` tag rename `prediction_market` → `prediction` deferred to
      `venue_axis_asset_group_vocabulary_2026_04_25.plan.md` Waves C/D per CLAUDE.md "Asset-group vocabulary" rule —
      that rename touches the adapter factory's venue-registry (cross-cutting, [UAC] layer) which is Ikenna-side design
      scope; the caller-side fix was Harsh-side mechanical scope.)
- [ ] [SCRIPT] P0. Replace POLYMARKET writer (`orchestrator.py:1990–1995`): old `data_type = <base_asset>` → new
      `data_type = prediction_canonical_question_group`. [AUDIT 2026-05-07: FRESH — actionable] **PHANTOM-PARTIAL
      finding 2026-05-08 (Tab 1 umi-rename sub-agent, sha mtds@`3f631b9` adjacent investigation)**: No per-`base_asset`
      writer exists in MTDS source. The legacy `data_type=BTC|ETH|SPX` shape was migrated away from previously; current
      MTDS prediction adapters write per-row `data_type="trades"` via the standard `PartitionedTickWriter` path (per
      `polymarket_adapter.py:531` + `kalshi_adapter.py:256`). The plan-referenced `engine/orchestrator.py:1990–1995` is
      the bookmaker-odds writer, not a POLYMARKET writer. The intended canonical fix — manifest-level shard re-bundling
      by `canonical_question_group`, writing `data_type=prediction_canonical_question_group` +
      `underlying=<canonical_group>` per UAC `BUNDLED_DATA_TYPES`, with cluster-validation kwargs at `record_captured`
      mirroring `instruments-service@b904785` `engine/orchestrator.py:2133-2186` pattern — is non-trivial DESIGN work
      (writer-level grouping over per-row trade data, not a string rename). Plan-body line 146 already declares
      "Integration tests against a live ManifestWriter on the orchestrator path deferred — bundled within MTDS Phase 2
      cluster-gate verification" — so the deferred sub-design is implicitly tracked. **Re-scope this todo**: kept `[ ]`
      because the canonical fix isn't shipped; the original "string rename" framing is wrong. Need Ikenna-side design
      call on whether the manifest re-bundling lands here (MTDS orchestrator) or stays implicit via the per-row
      `data_type="trades"` shape with `canonical_question_group` attached as a separate manifest column. Flagged for
      plan-of-record Q&A not chat — see `## Open questions` below.
- [x] [TEST] P0. MTDS unit tests: lifecycle gating (pre-created tick rejected, post-settled tick rejected); cluster
      validation per `(canonical_question_group, day)`. [AUDIT 2026-05-07: BLOCKED-ON above adapter migrations]
      **SHIPPED mtds@`7643a5c` + mtds@`e8a6903`** — 16 lifecycle-gating tests on origin (lifecycle-gating half complete;
      cluster-validation tests for the bundled `prediction_canonical_question_group` data_type remain deferred to the
      orchestrator-level Q1 option (a) writer migration). **WIP-READY ON-DISK 2026-05-08 (Tab 1 — pending main-agent
      commit + push)**: 16 lifecycle-gating tests covering both adapters (7 polymarket + 9 kalshi, all GREEN under
      `pytest -v` — see WIP-READY annotations on the two adapter todos above for the per-test list). Cluster-validation
      tests for the bundled `prediction_canonical_question_group` data_type are NOT included in this Phase 2 scaffold
      because the cluster-coverage gate at `record_captured` is the deferred orchestrator-level work tracked in Q1
      (option (a) writer migration) — that landing will add cluster-validation tests in MTDS at the orchestrator layer,
      mirroring `instruments-service@b904785`'s 9 canonical-group shard tests. Lifecycle-gating half is fully covered.

### Reader / feature / strategy migration

- [ ] [SCRIPT] P0. Reader migration: every callsite with `data_type=BTC|ETH|...` →
      `data_type=prediction_canonical_question_group` + filter on `canonical_question_group`. [AUDIT 2026-05-07:
      BLOCKED-ON predictions_master:Phase 1 lifecycle + adapter migration]
- [ ] [SCRIPT] P0. Per-market lifecycle gating in feature compute: `LookaheadBiasError` extension — feature at time T
      consumes only market_ids where `market_created_at ≤ T`. [AUDIT 2026-05-07: BLOCKED-ON predictions_master:Phase 1]
- [ ] [SCRIPT] P0. Strategy-service prediction archetypes: archetype configs reference `canonical_question_group`
      directly (not base_asset). [AUDIT 2026-05-07: BLOCKED-ON predictions_master:Phase 1]
- [ ] [TEST] P0. End-to-end smoke: 1 canonical_group (`BTC_UP_DOWN_HOURLY`) × 1 day; run feature compute + verify.
      [AUDIT 2026-05-07: BLOCKED-ON predictions_master:Phase 1 ship]

### Manifest + parquet migration

**Cross-plan coordination**: Polymarket parquet rewrite + manifest reflip is **Stage 3** of the workspace-wide manifest
migration. See [`manifest_migration_SUPERSEDED_2026_05_21.md`](./manifest_migration_SUPERSEDED_2026_05_21.md) for
sequencing DAG, VM impact, and operator gates. Key constraints: PAUSE `mtds-prediction-*` VMs during rewrite window;
resume ONLY after MTDS Polymarket adapter migration ships (so resumed VMs write `canonical_question_group` shape, not
legacy per-base_asset). Migration must run AFTER writegate Phase 2.A placeholder-method deletions complete.

- [ ] [SCRIPT] P0. New script `mtds_migrate_polymarket_per_base_asset_to_canonical_group.py` (in scripts/). [AUDIT
      2026-05-07: BLOCKED-ON manifest_migration_SUPERSEDED_2026_05_21:Stage 3 + writegate Phase 2.A]
- [ ] [SCRIPT] P0. Manifest reflip script `mtds_reflip_polymarket_per_base_asset.py` per
      `unified_trading_library.run_lifecycle` pattern. [AUDIT 2026-05-07: BLOCKED-ON
      manifest_migration_SUPERSEDED_2026_05_21:Stage 3]
- [ ] [SCRIPT] P0. Old parquet deletion — only AFTER (a) new parquets verified by hand-inspection (sample 10 random
      groups × random days), (b) downstream features compute clean, (c) operator approval. [AUDIT 2026-05-07: BLOCKED-ON
      predictions_master:above migration scripts run + verified]
- [ ] [SCRIPT] P0. Backfill any missing canonical_groups — markets in `conditionid_universe.csv` that classifier maps to
      a group not yet in `PREDICTION_GROUPS` registry. [AUDIT 2026-05-07: FRESH — actionable; per CLAUDE.md "Temporary
      state" rule, PREDICTION_GROUPS empty registry has predictions_master named as successor]
- [ ] [SCRIPT] P0. Confirm `migrate_polymarket_canonical.py` (MTDS) ran for all targets; afterwards delete legacy
      `category=prediction` fallback reader in MTDS (no compat shim per workspace rule). [AUDIT 2026-05-07: BLOCKED-ON
      above migration]
- [ ] [SCRIPT] P0. Every reconciler wraps work in `unified_trading_library.run_lifecycle.run_lifecycle(...)`. [AUDIT
      2026-05-07: FRESH — actionable]
- [ ] [SCRIPT] P0. Each reconciler supports `--max-flips-per-run=10000` halt safety; operator confirms first 10k flips.
      [AUDIT 2026-05-07: FRESH — actionable]
- [ ] [SCRIPT] P0. CSV audit at `gs://{pid}-reconciler-audit/{run_id}/`. [AUDIT 2026-05-07: FRESH — actionable]

### Data-status panel — Predictions asset_group drill-down

- [ ] [SCRIPT] P0. Predictions asset_group panel — drill-down shape: `(venue, canonical_question_group, day)`. [AUDIT
      2026-05-07: BLOCKED-ON predictions_master:Phase 1 + manifest reflip; aligns with infrastructure_master Data-status
      multi-axis follow-up]

### Predictions ML half (`sports_predictions_e2e`)

- [ ] [SCRIPT] P0. Run ml-training Model 2A walk-forward against the Group-D-validated feature matrix (gated on sports
      half completion in `sports_master`). [AUDIT 2026-05-07: BLOCKED-ON sports_master:Group E gate (FSS produces ≥95%
      non-NULL features)]
- [ ] [ANALYSIS] P0. Acceptance metrics — log-loss, calibration, AUC for win/draw/loss; threshold per consolidated plan
      bar. [AUDIT 2026-05-07: BLOCKED-ON predictions_master:walk-forward run]
- [ ] [SCRIPT] P0. Training-config sanity check: feature columns match FSS schema, label leakage absent, walk-forward
      window correct. [AUDIT 2026-05-07: BLOCKED-ON predictions_master:walk-forward run]
- [ ] [GATE] P0. Block Group F until walk-forward AUC ≥ 0.55 and calibration error ≤ 5%. [AUDIT 2026-05-07: ACTIVE GATE
      — explicitly BLOCKS master_to_live_defi_2026_05_23:Group F]
- [ ] [CODE] P0. Implement (or verify shipped) `arb_calculator` in FSS: cross-bookmaker arb %, eligible pairs, duration.
      [AUDIT 2026-05-07: FRESH — actionable; verify shipped status against features-sports-service catalog]
- [ ] [ANALYSIS] P1. Persist model + metrics to ml-models registry; tag `model_family=sports_arb_v1`. [AUDIT 2026-05-07:
      BLOCKED-ON predictions_master:walk-forward run]

### Predictions MTDS slice (`market_tick_data_to_100pct` — predictions)

- [ ] [AGENT] P1. Per-(canonical_question_group, day) completion %: HOURLY = 24 expected/day, DAILY = 1, ELECTION = 1
      over months/years. [AUDIT 2026-05-07: BLOCKED-ON predictions_master:Phase 1 lifecycle ingestion + classifier]

### Audit findings 2026-05-07 — folded from session wrapper

**Source**: `plans/ai/session_2026_05_07_data_status_audit_findings.md` row C.12. Operator inspected the deployment-ui
prediction panel + saw POLYMARKET tagged "out of scope" (badge driven by UAC `VENUE_DATA_TYPE_CAPABILITIES` declaring
`data_type=prediction_canonical_question_group` while MTDS still writes legacy per-base-asset shape `BTC` / `ETH` /
`SPX`). Per user direction 2026-05-07: NOT actually out of scope — small Polymarket dataset means full migration is
feasible in one VM run.

#### C.12 — POLYMARKET "out of scope" badge resolution + synthetic OTHER bucket

The Phase 1 critical-path todos above already cover the canonical-question-group classifier + lifecycle ingestion +
adapter migration. The two items below close the loop on the deployment-ui panel surface specifically:

- [ ] [SCRIPT] P0. **Synthetic `OTHER` canonical-question-group bucket** — the classifier MUST map every Polymarket
      `conditionId` (and Kalshi ticker) to SOME canonical group. Markets that don't fit the curated registry
      (`BTC_UP_DOWN_HOURLY`, `BTC_UP_DOWN_DAILY`, `SPX_UP_DOWN_DAILY`, `ELECTION_PRESIDENT_2028`, etc.) get mapped to
      `OTHER`. Rationale per user direction 2026-05-07: small Polymarket dataset means we can audit `OTHER` membership
      after each backfill VM run and promote frequently-seen patterns to first-class groups. Treating `OTHER` as a known
      catch-all bucket is honest absence; treating those markets as "out of scope" hides them from the panel and from
      the classifier audit loop. [AUDIT 2026-05-07: FRESH — actionable; UAC@bb24aba seeded PREDICTION_GROUPS but OTHER
      bucket presence unverified]
  - [ ] UAC `PREDICTION_GROUPS` registry seeding (Phase 1 critical-path item) MUST include `OTHER` as a special-case
        entry from day one. Cluster validation for `OTHER` is per-day count > 0 (any markets fall through), not a target
        count. [AUDIT 2026-05-07: FRESH — actionable]
  - [ ] Classifier emits an `INFO`-level event `OTHER_BUCKET_MEMBER_ADDED` whenever it routes a `conditionId` to
        `OTHER`. Operator periodically queries the event stream to find candidate groups for promotion. [AUDIT
        2026-05-07: FRESH — actionable]
  - [ ] Data-status panel renders `OTHER` as a normal canonical-question-group bucket (not "out of scope"). Hover
        tooltip: "Markets not yet mapped to a curated canonical question group — review event stream + promote recurring
        patterns to first-class groups." [AUDIT 2026-05-07: FRESH — actionable]
- [ ] [VERIFY] P0. Phase 1 timeline check against 2026-05-23 master deadline: 14/37 done (38%) as of 2026-05-07. The 14
      remaining P0 items in Phase 1 + Phase 2 + Phase 3 (lifecycle ingestion + classifier + adapter migration + parquet
      rewrite + manifest reflip) need to ship in ~16 days. Per user direction: small dataset means migration is
      feasible. Block Phase 5 baseline + ratchet until POLYMARKET no longer renders "out of scope" in deployment-ui.
      [AUDIT 2026-05-07: FRESH — actionable; this IS the timeline gate]
- [ ] [VERIFY] P0. After Phase 1 ships: re-walk deployment-ui prediction panel; POLYMARKET drill-down renders as
      `(venue=POLYMARKET, data_type=prediction_canonical_question_group, canonical_question_group, market_id, day)` per
      CLAUDE.md per-asset-group shard-key matrix. No "out of scope" badge. `OTHER` bucket visible alongside curated
      groups. [AUDIT 2026-05-07: BLOCKED-ON predictions_master:Phase 1 ship]

### Predictions completeness hierarchy + lifecycle drilldown (migrated from `predictions_completeness_hierarchy_lifecycle_drilldown_2026_05_08`)

Source issue archived. 26KB consumer-side completion list — Phase 1A SSOT (canonical_question_group + lifecycle +
classifier) shipped; Phase 2-5 consumer-side wiring incomplete. The issue is NOT a competing plan; it specifies the gap
surfaces left by the existing predictions_master phase structure.

**Cross-plan banner**: feeds `cme_polymarket_arb_2026_05_08` Phase 2 (canonical_question_group cross-link); 6 new
canonical groups (CRUDE_OIL / GOLD / DOGE / SOL / etc. — full list in archived issue) must ship from Phase 5 below
before CME arb can link.

- [x] ✅ [SCRIPT] P0. **instruments-service MARKET_LIFECYCLE parquet writer**. Persist `market_created_at` /
      `resolution_time` / `settlement_time` per market_id into a separate parquet (NOT bundled into the canonical-group
      shard). Path:
      `gs://instruments-store-prediction-{pid}/market_lifecycle/by_canonical_group/group={g}/by_date/day={d}/...parquet`.
      Schema: `{market_id, canonical_question_group, market_created_at, resolution_time, settlement_time, status}`.
      Reader-side helper `unified_trading_library.predictions.lifecycle_for_market(market_id) -> MarketLifecycle`. —
      IS@2aabd7b `_build_market_lifecycle_df` + `_write_market_lifecycle` + lifecycle_sink + 9 unit tests (2026-05-22)
- [x] ✅ [SCRIPT] P0. **MTDS umi_tick_provider lifecycle-bounded clip**. Today MTDS captures CLOB ticks for every
      registered market_id without bound; flip to read MARKET_LIFECYCLE first, then clip per-market: NO ticks before
      `market_created_at`, NO new ticks after `settlement_time`. Per CLAUDE.md "Prediction market lifecycle timing" rule
      already declared. — MTDS@006beab5 `_load_market_lifecycle_for_date` helper + Polymarket + Kalshi updated to try
      MARKET_LIFECYCLE path first, fall back to instrument_availability/; 16 new unit tests (2026-05-22)
- [x] ✅ [SCRIPT] P0. **MTDS cluster validation per (canonical_question_group, day)**. HOURLY groups expect 24
      market_ids/day; DAILY = 1; recurring election groups = 1 over months/years. Add to UAC `BUNDLED_DATA_TYPES` for
      Polymarket/Kalshi CLOB writes; cluster-validation kwargs at `record_captured` per writegate Phase 1A. —
      MTDS@e777dc40 `_load_expected_clusters_for_cqg()` helper reads IS MARKET_LIFECYCLE parquet per (cqg, day); falls
      back to observed=expected when parquet absent; 9 unit tests (2026-05-22)
- [x] ✅ [SCRIPT] P0. **MDPS PredictionTradesAdapter 4-category A/B/C/D empty-output decision wiring** (per CLAUDE.md
      "Four-category empty-output decision" rule). Today MDPS PredictionTradesAdapter doesn't classify; add explicit
      branches: A = source returned 0 ticks → `record_empty(reason=SOURCE_RETURNED_ZERO)`; B = ticks returned but
      filtered out by interval_idx → `record_failed(UpstreamTimestampBiasError)`; C = malformed source fields →
      `record_failed(MalformedTickFieldError)`; D = catalog says alive but source returned 0 → write zero-activity bars
      per category-D rule. MDPS@ea76662 (base_adapter + PredictionTradesAdapter + live_workers + 15 tests). 2026-05-22
      slot-2.
- [ ] [SCRIPT] P0. **features per-market LookaheadBiasError check**. Per CLAUDE.md prediction-lifecycle rule: feature
      compute at time T can only consume ticks where `tick.timestamp <= T` AND `tick.market_id`'s
      `market_created_at <= T`. Today features-cross-instrument doesn't enforce this per-market; flip to strict-mode
      check.
- [ ] [SCRIPT] P0. **deployment-ui 3-level hierarchy + per-shard parquet download**. Today MARKETS list is flat; flip to
      `asset_group → canonical_question_group → cadence (HOURLY/DAILY/etc.)` 3-level drilldown matching sports + tradfi
      pattern. Per-shard parquet download wires through existing
      `deployment-ui/src/components/HierarchicalShardDrilldown` machinery.
- [ ] [SCRIPT] P1. **Phase 5 — canonical-groups backfill (30+ groups beyond initial 9)**. Full list in archived issue:
      CRUDE_OIL_UP_DOWN_DAILY, GOLD_UP_DOWN_DAILY, DOGE_UP_DOWN_DAILY, SOL_UP_DOWN_DAILY, ECRTY/ECYM/ECGC/
      ECCL/ECNG/EC6E (CME-linked), and ~24 others. Per-group: define in UAC `PREDICTION_GROUPS`; backfill
      instruments-service catalog + MTDS CLOB tick history; cluster-validation expected counts populated. **GATES
      `cme_polymarket_arb_2026_05_08` Phase 2 cross-link**. **UAC DONE (2026-05-22 slot-2)**: 7 CME-linked groups
      defined in `CanonicalQuestionGroup` + `PREDICTION_GROUPS` + `cme_polymarket_link.py` fully wired (UAC@9c491bdd).
      cme-arb Phase 2 FULL. **Classifier rules DONE (2026-05-22 slot-2 UAC@55d068f7)**: taxonomy.py RUT slug prefixes
      (rut-/russell-2000-/russell-) + CLASSIFIER_VERSION=2026-05-22.1; classifiers.py 7 entries in
      `_CATEGORY_UNDERLYING_PERIOD_TO_GROUP` (NDX/DJIA/RUT/GOLD/CRUDE_OIL/NAT_GAS/EURUSD); 24 tests pass. **Classifier
      MONTHLY→DAILY fallback DONE (2026-05-23 slot-1 UAC@228c317a)**: Polymarket daily-price markets use month+day slugs
      (e.g. "btc-up-or-down-may-22") → taxonomy assigns MONTHLY → no dict hit → OTHER. Fixed by adding
      RANGE_BRACKET+MONTHLY→DAILY fallback in `classify_polymarket_to_canonical_group`; bumped
      CLASSIFIER_VERSION=2026-05-23.1. Smoke-test verified: BTC/SPX/CRUDE_OIL/GOLD/NATGAS daily slugs all route to
      correct groups. Remaining: IS prediction catalog re-backfill (purge existing OTHER rows for these 5 groups + rerun
      instr-backfill-pred VM with UAC@228c317a) + MTDS CLOB tick history for 7 new groups.
- [x] ✅ [SCRIPT] P1. **Phase 5.reclassify — purge OTHER + re-launch IS prediction backfill with UAC@228c317a**:
      2026-05-23 slot-1. (1) Wrote IS@d76b877f `scripts/purge_prediction_other_group_rows.py` — purged 435 OTHER rows
      (stored in `underlying` col) from canonical manifest + 821 from 2 per-VM shards; 108 clean rows remain
      (CPI_PRINT_PER_MONTH + BTC_UP_DOWN_HOURLY). (2) Rebuilt tarball (`--allow-dirty-tarball`; UAC@c07058537253
      includes classifier fix). (3) Launched `instr-backfill-pred-20260523` VM (2020-01-01→2026-05-23,
      MANIFEST_PER_VM_SHARDS=true); VM completed chunks 1-68 (2020-01-01→2025-08-01) then stopped. — IS@d76b877f | VM:
      instr-backfill-pred-20260523 TERMINATED (replaced by parallel VMs below)
- [x] ✅ [UAC] P1. **Phase 5.intraday — add BTC/ETH_UP_DOWN_INTRADAY canonical groups**: 2026-05-23 slot-1. 5m/15m
      Polymarket markets (INTRADAY resolution period) had no dict entry → fell to OTHER. Added BTC_UP_DOWN_INTRADAY +
      ETH_UP_DOWN_INTRADAY to: CanonicalQuestionGroup enum; CANONICAL_GROUP_METADATA (cadence="intraday", 288
      markets/day, 2h settlement lag); PREDICTION_GROUPS in honest_coverage (min 20 rows);
      \_CATEGORY_UNDERLYING_PERIOD_TO_GROUP in classifiers.py. Bumped CLASSIFIER_VERSION 2026-05-23.1→2026-05-23.2. 1h =
      already covered (BTC/ETH_UP_DOWN_HOURLY). Monthly slug-encoded-day markets = handled by existing MONTHLY→DAILY
      fallback (UAC@228c317a). — UAC@bd570664
- [x] ✅ [SCRIPT] P1. **Phase 5.parallel_vms — relaunch remaining range as 3 parallel VMs with INTRADAY classifier**:
      2026-05-23 slot-1. Rebuilt tarball with UAC@bd570664 (INTRADAY groups + CLASSIFIER_VERSION=2026-05-23.2). Launched
      3 parallel VMs: instr-backfill-pred-20251031 (2025-08-02→2025-10-31), instr-backfill-pred-20260228
      (2025-11-01→2026-02-28), instr-backfill-pred-20260522 (2026-03-01→2026-05-22). All 3 RUNNING in asia-northeast1-c.
      Used --end 2026-05-22 for 3rd VM to avoid name collision with old terminated instr-backfill-pred-20260523 shard. —
      VMs RUNNING (launched 2026-05-23)
- [x] ✅ [UAC] P1. **Phase 5.5min_split — add 5MIN/15MIN granularity to classifier** (SUPERSEDES INTRADAY-only from
      Phase 5.parallel_vms): 2026-05-23 slot-1. Added ONE_MIN/FIVE_MIN/FIFTEEN_MIN to PredictionShardResolutionPeriod.
      Updated \_infer_resolution_period() to extract digit from slug tokens before falling back to INTRADAY (15-minute →
      FIFTEEN_MIN, 5-minute → FIVE_MIN, 1-minute → ONE_MIN). Added BTC/ETH_UP_DOWN_5MIN + 15MIN CanonicalQuestionGroup
      enum values with metadata (5MIN cadence=288/day, 15MIN cadence=96/day). INTRADAY remains as fallback for
      unknown-interval intraday slugs. Updated classifiers.py + honest_coverage.py. Bumped CLASSIFIER_VERSION
      2026-05-23.2→2026-05-23.3. Fixed bash empty-array nounset bug in create-code-tarballs.sh. — UAC@e6ae5013
- [x] ✅ [SCRIPT] P1. **Phase 5.5min_relaunch — stop old INTRADAY VMs + relaunch 3 IS VMs with 5MIN/15MIN classifier**:
      2026-05-23 slot-1. Stopped instr-backfill-pred-20251031/20260228/20260522 (had written with INTRADAY-only
      classifier). Rebuilt tarball (UAC@e6ae5013 with 5MIN/15MIN). Relaunched same 3 VMs with --force to reprocess all
      shards. All 3 RUNNING in asia-northeast1-c. — VMs RUNNING (launched 2026-05-23)
- [x] ✅ [SCRIPT] P1. **Phase 5.mtds_canonical — launch MTDS canonical prediction backfill (10 parallel VMs)**:
      2026-05-23 slot-1. Fixed ImportError (MTDS@498148da). Operator requested 5× concurrency → 1/5 time. Split full
      2020-01-01→2026-05-22 range into 10 shards, all launched with --force bypassing singleton. VMs 1-5 (2020→2025):
      1=(2020-01-01→2021-02-11) 2=(2021-02-11→2022-03-25) 3=(2022-03-25→2023-05-06) 4=(2023-05-06→2024-06-16)
      5=(2024-06-16→2025-08-01). VMs 6-10 (2025→2026): 6=(2025-08-02→2025-09-29) 7=(2025-09-29→2025-11-26)
      8=(2025-11-26→2026-01-23) 9=(2026-01-23→2026-03-22) 10=(2026-03-22→2026-05-22). All 10 RUNNING ~58 chunks each.
      ETA: ~1-1.5h total. — MTDS@498148da
- [x] ✅ [SCRIPT] P1. **Phase 5.mtds_import_fix — fix ImportError in tick_data_handler.py + relaunch**: 2026-05-23
      slot-1. get_venues_for_categories → get_venues_for_asset_groups at 3 locations in tick_data_handler.py. QG green
      (pre-existing failures only). Committed MTDS@498148da, pushed LDR. Rebuilt tarball (GCS 21:10:42 UTC). —
      MTDS@498148da
- [x] ✅ [SCRIPT] P1. **Phase 5.mtds_canonical_2 — launch MTDS canonical prediction backfill VM (2025-08→2026-05)**:
      Absorbed into Phase 5.mtds_canonical 10-VM split (VMs 6-10 cover this range). IS VMs confirmed TERMINATED. All 10
      VMs RUNNING as of 2026-05-23 ~21:20 UTC.
- [x] ✅ [SCRIPT] P0. **Phase 5.mtds_trades_gap_fill — fix 23-day MTDS trades gap (2026-04-30..2026-05-22) + root
      causes**: 2026-05-24 slot-1. Two root-cause bugs fixed: (1) `base_prediction_adapter.py` +
      `polymarket_adapter.py` + `kalshi_adapter.py` used `get_write_bucket_name("instruments","prediction")` → wrong
      bucket `instruments-store-prediction-*` (correct: `instruments-store-pred-prd-*`); replaced with
      `resolve_bucket_name(cloud="gcp", kind="instruments-store-prediction")`. Also fixed `defi_catalog_reader.py`
      `BlobMetadata.endswith()` crash. (2) `tick_data_handler.py` called `process_ticks()` without `force=self._force` —
      even with `--force` CLI flag, the orchestrator pre-flight read VM3 empty_confirmed rows as "fully covered" and
      skipped POLYMARKET. Fixed by adding `force=self._force` to the `process_ticks()` call. Also added `--vm-force`
      flag to `launch-mtds-prediction-backfill-vm.sh`. VM5 (`mtds-prediction-20260524-015510`) ran clean: 5,655 captured
      rows across 21 dates; 230 empty_confirmed for 23 dates (2026-05-13 + 2026-05-18 legitimately empty); zero
      attempted_failed. Consolidated into availability_index. — MTDS@e5e3ca36,2b7c7760

## `available_at` adapter stamping (coordinated) — SUPERSEDED 2026-06-20 (owned by the coordinator plan; history only)

> **OWNED ELSEWHERE**: the lifecycle-bounded adapter `available_at` stamping is tracked in
> [`available_at_lookahead_bias_completion_2026_05_08`](../archive/2026_05/available_at_lookahead_bias_completion_2026_05_08.md)
> Phase 1 (+ the feature_groups → UAC `FEATURE_REQUIRED_INPUTS` slice is mirrored in the
> `predictions_lookahead_and_reader_migration` child plan). Do NOT dispatch from here. Retained below for context only.

> **Coordinator:**
> [`available_at_lookahead_bias_completion_2026_05_08`](../archive/2026_05/available_at_lookahead_bias_completion_2026_05_08.md)
> Phase 1. Predictions stamping is **lifecycle-bounded**: every prediction-market tick must have
> `available_at = max(tick_ts, market_created_at)` and must NOT carry rows past `market_settlement_time`. Depends on
> Phase 1 (canonical-question-group + lifecycle ingestion) of THIS plan AND on coordinator Phase 0 (MDPS bar boundary
> contract).

- [ ] [SCRIPT] P0. **Lifecycle-bounded `available_at` stamping for Polymarket + Kalshi adapters**. After lifecycle
      ingestion lands (Phase 1 of this master), MTDS Polymarket / Kalshi adapters stamp every tick row with
      `available_at = max(tick_ts, market_created_at)`. Adapters refuse to write rows past `market_settlement_time`
      (already partly enforced via lifecycle gates above; this todo makes the row-level stamping explicit). Coordinator
      Phase 1 + this master Phase 1.
- [ ] [SCRIPT] P1. **Predictions feature_groups → UAC `FEATURE_REQUIRED_INPUTS`**. Per-canonical_question_group +
      per-binary-outcome features need registry entries. Source-of-truth: features-\* services that consume prediction
      tick data. Coordinator Phase 4.

## May-23 deliverable (folded from `prediction_markets_may_23_2026.epic` 2026-05-08) — SUPERSEDED 2026-06-20 (routed to master; history only)

> **ROUTED TO MASTER**: the May-23 success criteria below are cutover gates owned by
> [`master_to_live_defi_2026_05_23`](../active/master_to_live_defi_2026_05_23.md) (predictions readiness ladder =
> "BACKTEST only / features-pipeline-running, no ML this cycle"). The **Opinion Trade backtest** + **CME event-futures
> arb backtest** criteria are CONTRADICTED by this section's own resolved Open-Questions (both **OUT for May-23 /
> post-cutover**) — they are NOT active work. Do NOT dispatch from here. Retained below for context only.

> **Folded epic** (operator direction 2026-05-08): consolidated from
> `plans/epics/prediction_markets_may_23_2026.epic.md`. Archived:
> [`plans/archive/prediction_markets_may_23_2026.epic.md`](../archive/prediction_markets_may_23_2026.epic.md).

**Why:** Prediction-markets ship **full backtest** for May 23 — features → strategy → execution all backtest, no live.
Like sports ML, end-to-end pipeline coverage at every layer; unlike S&P prediction which only goes to ML training.
Cross-asset features (S&P, sports, crypto) consumed since prediction-markets often resolve based on outcomes other
features predict.

### End-state at May 23 (success criteria)

- [ ] **Polymarket backtest** runs end-to-end through unified pipeline for at least one canonical-question-group
      archetype (BTC up-down hourly OR SPX up-down daily OR similar).
- [ ] **Kalshi backtest** runs for at least one event family (e.g. CPI prints, FOMC outcomes).
- [ ] **Opinion Trade backtest** runs for at least one event family.
- [ ] **CME event futures arbitrage backtest** runs for at least one cross-venue pair (e.g. CME inflation event future
      vs Kalshi CPI market).
- [ ] **Prediction data pipeline clean**: instruments (per-market lifecycle: market_created_at / resolution_time /
      settlement_time) + tick data (CLOB captures respecting lifecycle bounds) + features (canonical-question-group
      bundle SSOT).
- [ ] **Cross-asset features wired**: S&P features, sports features, crypto features all consumable by prediction
      strategies as inputs.
- [ ] **LookaheadBiasError strict** at every features compute — feature compute at time T can only consume ticks where
      `tick.timestamp ≤ T AND tick.market_id`'s `market_created_at ≤ T` (CLAUDE.md "Prediction market lifecycle timing"
      SSOT).
- [ ] **Cluster validation MANDATORY** for `prediction_canonical_question_group` bundle data_type at `record_captured`
      (UAC `BUNDLED_DATA_TYPES` includes prediction).
- [ ] **Strategy + execution layers PROGRESSED** through unified pipeline — backtest end-to-end, no inline settlement.

### IN/OUT scope

- **IN**: full backtest of 4 prediction-market archetypes (Polymarket / Kalshi / Opinion Trade / CME event futures arb);
  prediction-market data pipeline (instrument lifecycle 3 timestamps per market_id, CLOB tick capture,
  canonical-question-group bundle aggregation); cross-asset feature consumption (S&P / sports / crypto); strategy +
  execution backtest through unified pipeline.
- **OUT**: live trading; live tick capture; production deployment of any prediction strategy; full
  canonical-question-group SSOT for every market_id (cover at minimum the archetypes in scope; remaining mappings
  post-May-23).

### Cross-epic handshakes

- **Depends on:** `cross_cutting_may_23_SUPERSEDED_2026_05_21` for strategy catalogue (4 prediction archetypes × all
  canonical-question-groups + venues enumerated). Cross-asset features depend on `tradfi_master` (S&P features) +
  `sports_master` (sports features) + DeFi/CeFi crypto features (`defi_master` + `cefi_master`).
- **Shares with:** Cross-asset features pipeline shared with all other ML/backtest deliverables.

### Open questions

- [x] ✓ **Canonical question groups for May 23 — RESOLVED 2026-05-08.** **3 canonical groups, backtest-only**:
      `BTC_UP_DOWN_HOURLY` (24/day; HOURLY lifecycle), `SPX_UP_DOWN_DAILY` (1/day; cross-asset feed for tradfi S&P
      prediction), `BTC_UP_DOWN_DAILY` (1/day; cross-asset feed for cefi_ml diagnostic calibration). ELECTION + CPI
      DEFERRED post-cutover. See `plans/archive/operator_decisions_2026_05_08.plan.md`.
- [x] ✓ **CME event futures inventory — RESOLVED 2026-05-08.** **OUT for May-23 cross-venue arb.** The price-arb May-23
      deliverable per `tradfi_master:deliverable B` covers FUTURES products (CME same-day-expiry + ETF↔future +
      cross-venue ETF). CME event-contracts (binary outcomes) need a separate MTDS adapter + instruments-service catalog
      work; defer post-cutover. ONE cross-venue arb cell IN: Polymarket `SPX_UP_DOWN_DAILY` ↔ S&P futures-implied
      probability (single cell, runs on existing Polymarket + Databento ES1, no new adapter) — track as P1 inside this
      plan.
- [x] ✓ **Opinion Trade integration depth — RESOLVED 2026-05-08.** **OUT for May 23.** No Opinion Trade integration this
      cycle (neither static historical nor live venue connector). Backtest-only per master Q&A 7; Polymarket + Kalshi
      static historical sufficient for the 3 picked canonical groups. Re-evaluate post-cutover.

## Anti-patterns + workspace-rule cross-references

- **Prediction market lifecycle timing** (CLAUDE.md): NO ticks before `market_created_at`, NO ticks after
  `settlement_time`. MTDS adapters MUST gate on lifecycle bounds.
- **Cluster validation per `(canonical_question_group, day)`**: HOURLY → 24 clusters expected; DAILY → 1; ELECTION → 1
  over its window. Cluster gate at `record_captured` per CLAUDE.md "Cluster validation MANDATORY".
- **Temporary state**: UAC `PREDICTION_GROUPS = {}` empty registry until taxonomy seeded — CLAUDE.md "Temporary state"
  rule applies; this plan IS the named successor.

## Assigned active plans

_Active plans declaring `parent_epic: predictions_master`. Workers pick up in priority order (P0 first). Auto-populated
by `scripts/plans/populate_epic_bodies_2026_05_21.py` — the list below was seeded by the 2026-06-20 restructure and the
script keeps it in sync from frontmatter._

**Delegated (predictions work tracked under service-epic plans, listed for visibility — NOT direct `parent_epic`
children):**
[`prediction_manifest_canonicalisation_2026_06_01`](../active/prediction_manifest_canonicalisation_2026_06_01.md)
(manifest / parquet canonicalisation + writer-rebundling) ·
[`available_at_lookahead_bias_completion_2026_05_08`](../archive/2026_05/available_at_lookahead_bias_completion_2026_05_08.md)
(lifecycle-bounded adapter `available_at` stamping).

## P0 — must complete before next foundation gate

### [`predictions_other_bucket_and_ui_drilldown_2026_06_20`](../active/predictions_other_bucket_and_ui_drilldown_2026_06_20.md)

**status**: active · **estimate**: 4 cal AI-days (class: brand-new). Synthetic `OTHER` canonical-question-group bucket
end-to-end (UAC seeding + classifier event + manifest coverage) + deployment-ui 3-level
`asset_group → canonical_question_group → cadence` drilldown + per-shard parquet download + data-status predictions
panel + the "out of scope" VERIFY gates + the P2 prediction sentinel fan-out for empty CQG rows.

### [`predictions_lookahead_and_reader_migration_2026_06_20`](../active/predictions_lookahead_and_reader_migration_2026_06_20.md)

**status**: active · **estimate**: 3 cal AI-days (class: brand-new). Reader callsite migration to
`prediction_canonical_question_group`; per-market `LookaheadBiasError` feature-compute enforcement; strategy archetype
configs reference `canonical_question_group`; 1-group × 1-day E2E smoke; predictions feature_groups → UAC
`FEATURE_REQUIRED_INPUTS`.

### [`predictions_ml_walk_forward_and_arb_2026_06_20`](../active/predictions_ml_walk_forward_and_arb_2026_06_20.md)

**status**: active · **estimate**: 4.8 cal AI-days (class: research). Predictions ML half of `sports_predictions_e2e` —
Model 2A walk-forward + acceptance metrics + Group-F AUC≥0.55/calib≤5% gate + FSS `arb_calculator` + model-registry
persistence + MTDS completion-% slice. **GATED ON `sports_master:Group E`** (FSS ≥95% non-NULL).

## P1 — important; post-current-gate

_(no plans currently assigned at this priority — P1 items live within the P0 child plans above.)_

## P2 — useful; opportunistic

_(the prediction sentinel fan-out for empty CQG rows is tracked as a P2 todo inside
[`predictions_other_bucket_and_ui_drilldown_2026_06_20`](../active/predictions_other_bucket_and_ui_drilldown_2026_06_20.md).)_

## Archived plans

### [`kalshi_api_migration_to_elections_subdomain_2026_05_20`](../archive/2026_05/kalshi_api_migration_to_elections_subdomain_2026_05_20.md)

**status**: ✅ ARCHIVED 2026-05-23 — Phase 1 (URL sweep 5 repos) + Phase 2 cassette re-record done; 8 items
DEFERRED-OPERATOR-DECISION (BLOCKED-CREDENTIALS — Kalshi API key not yet provisioned). · **estimate**: 1.0 cal AI-days
(class: refactor)

**Deferred (MIGRATED FROM archived plan)** — BLOCKED-CREDENTIALS backlog:

- **Phases 2-4 (8 items, P1-P2, BLOCKED-CREDENTIALS)**: Schema diff + update; provision `kalshi-api-key` +
  `kalshi-private-key-pem` to GCP Secret Manager; integration test (authenticate + fetch); MTDS Kalshi adapter verify;
  execution-service paper-order flow verify; UAC weekly-validation cassette regression; predictions_master URL
  regression check. Gate: `api_keys_wallets_accounts_readiness_2026_05_10.md` 5.B.2.

### [`data_status_coverage_gaps_and_prediction_manifest_fix_2026_05_22`](../archive/2026_05/data_status_coverage_gaps_and_prediction_manifest_fix_2026_05_22.md)

**status**: ✅ ARCHIVED 2026-05-23 — IS cefi/sports/prediction manifest gaps fixed; prediction bucket consolidated
(100.0% captured); codex `prediction-schema-paths.md` + `sports-data-source-coverage-matrix.md` updated. · **estimate**:
1.2 cal AI-days

**Deferred (MIGRATED FROM archived plan)** — P1 operator-monitoring backlog:

- **Monitor `instr-backfill-sports` VM**: ~60-day background backfill for 2020→2026 historical. No May-23 gate. Operator
  monitors until STATUS=TERMINATED; verify sports gaps drop from 3063 to < 200.
- **Schema column in drilldown**: verify `canonical_question_group` schema link in deployment-api UI routes to correct
  `CanonicalQuestionGroup` UAC metadata per group (not flat Polymarket schema).

## P3 — backlog; revisit quarterly

_(no plans currently assigned at this priority)_

## Cross-references

- Master plan: [`master_to_live_defi_2026_05_23.md`](../active/master_to_live_defi_2026_05_23.md).
- Sibling asset_group umbrellas: `cefi_master`, `defi_master`, `tradfi_master`, `sports_master`.
- Sports half of e2e: `sports_master.md` (288M ODDS_API row migration + MDPS bucketing + FSS).
- Honest-coverage % surface: `GET /api/data-status/honest-coverage` + `HonestCoverageCard` (deployment-ui). SSOT:
  [`codex/03-deployment/data-status-ui-surface.md`](../../codex/03-deployment/data-status-ui-surface.md). Phase 7F per
  `cross_asset_group_catalogue_audit_2026_05_10.md`.
- Canonical asset_group registry: `unified_api_contracts.canonical.crosscutting.asset_group_registry` (Phase 5C/5D).

## Folded plans (archived 2026-05-07)

- `predictions_canonical_question_group_polymarket_migration_2026_05_06.md` — full migration spec; P0 todos lifted
  above.
- `sports_predictions_e2e_2026_05_05.md` (predictions half) — ML training + arb_calculator + Group E/F gates; sports
  half went to `sports_master`.
- `market_tick_data_to_100pct_2026_05_05.md` (predictions slice) — full plan archived after split per asset_group.

## Temporary states + their canonical follow-up plans

Per CLAUDE.md "Temporary state must have a named successor plan" — Phase 1 (Tab 10) shipped a partial implementation;
the items below are intentional deferrals named back to this plan (Phase 2 / 3) so reviewers can see scope, not silent
"fix later" work:

- **MARKET_LIFECYCLE separate parquet emit (instruments-service)** — Phase 1 wired
  `PolymarketReferenceDataAdapter.get_market_lifecycles()` + `KalshiReferenceDataAdapter.get_market_lifecycles()` and
  stamps `available_from_datetime` / `available_to_datetime` on the `InstrumentRecord` shard, but the orchestrator
  doesn't yet write a separate `MARKET_LIFECYCLE` parquet (no adapter-instance pass-through plumbing today). Lifecycle
  bounds are discoverable downstream via the `InstrumentRecord` slots; full lifecycle row (with `canonical_group` +
  `current_status`) lands when the orchestrator gains an adapter-handle on the prediction venue branch. **Successor**:
  this plan, Phase 2 — lifted into the "Adapter migration (MTDS — Polymarket + Kalshi)" tier as a sibling todo so it
  ships alongside the MTDS lifecycle reader.
- **Per-market_id manifest rows + cluster-coverage gate** — Phase 1's writer emits one manifest row per
  `(venue, canonical_question_group, day)` bundle; per-market_id rows + `record_captured(expected_root_clusters=…)`
  cluster-coverage gating wait for the MTDS Phase 2 lifecycle reader (`expected_market_ids_for_canonical_group`) because
  the bundle-level cluster expectation is derived from the lifecycle table, not the instruments parquet. **Successor**:
  this plan, Phase 2 — within the MTDS adapter-migration tier.
- **Kalshi `KALSHI_TICKER_TO_GROUP` override seeding** — UAC override dict is empty per
  `unified_api_contracts/canonical/domain/predictions/classifiers.py`. Kalshi rows currently route to `OTHER`. Operator
  periodically reviews the `OTHER_BUCKET_MEMBER_ADDED` event stream to identify recurring tickers worth promoting.
  **Successor**: this plan, "Audit findings 2026-05-07 — folded from session wrapper" → C.12 OTHER-bucket-promotion
  subitem; lights up once Phase 1 production data surfaces enough recurring tickers.

## DONE-2026-05-08

Tab 10 (predictions-phase1-ingestion-tab) shipped the Phase 1 instruments-service half — lifecycle ingestion in
adapters + classifier-based shard atom in the writer:

- instruments-service@`98bb167` — feat(predictions): per-market lifecycle ingestion in Polymarket + Kalshi adapters.
  `classify_lifecycle()` + `get_market_lifecycles()` on both adapters; `available_from_datetime` /
  `available_to_datetime` stamped on `InstrumentRecord` for downstream MTDS lifecycle gating + features-\* compute
  per-market `LookaheadBiasError`. 14 unit tests pinning canonical-question-group routing, settlement_lag derivation,
  status enum mapping, and silent-drop of unclassifiable markets.
- instruments-service@`b904785` — feat(predictions): orchestrator emits prediction_canonical_question_group shard atom.
  Replaces `_extract_prediction_shard(base_asset)` with classifier-based `_extract_prediction_canonical_group(row)`;
  writer at `engine/orchestrator.py:2128` now bundles Polymarket + Kalshi rows by `canonical_question_group` and emits
  manifest `data_type=prediction_canonical_question_group` + `underlying={GROUP}` per UAC `BUNDLED_DATA_TYPES`. 9
  additional unit tests covering BTC/ETH HOURLY routing, OTHER fallback, Kalshi override-only path, and
  `_compute_prediction_shards` aggregation across 24 BTC HOURLY + 1 SPX DAILY + 5 OTHER markets.
- unified-trading-pm@`7343b93` — plan(predictions-master): flip Phase 1 lifecycle-ingestion checkbox citing
  instruments-service@98bb167.

Phase 2 deferrals (named per "Temporary states" above): MTDS Polymarket / Kalshi adapter lifecycle gating;
`umi_tick_provider.py:225` + `orchestrator.py:1990-1995` data_type rename to `prediction_canonical_question_group`;
`MARKET_LIFECYCLE` separate parquet emit; per-market_id manifest rows + `record_captured` cluster-coverage gate
consuming `expected_market_ids_for_canonical_group` from the lifecycle reader.

QG status: ruff clean on every file Tab 10 touched; basedpyright/pre-existing diagnostics outside Tab 10's edited line
ranges (Ikenna's QG sweep cycle 2026-05-07 → 2026-05-09 per CLAUDE.md "Findings Triage Discipline" § "Temporary
exception"). Full instruments-service unit suite (2267 tests) green post-change.
