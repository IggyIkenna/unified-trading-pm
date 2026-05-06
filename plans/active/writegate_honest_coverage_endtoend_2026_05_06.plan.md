---
type: plan
role: umbrella
locked_by: live-defi-rollout
locked_since: 2026-05-06
created: 2026-05-06
companion_handover: shard_granularity_ssot_propagation_2026_05_06.HANDOVER.md
parent_plan: shard_granularity_ssot_propagation_2026_05_06.plan.md
related:
  - predictions_canonical_question_group_polymarket_migration_2026_05_06.plan.md
  - data_status_multi_axis_shard_propagation_2026_05_06.plan.md
  - shard_granularity_ssot_propagation_2026_05_06.plan.md
  - shard_granularity_ssot_propagation_2026_05_06.HANDOVER.md
supersedes_phases:
  - shard_granularity_ssot_propagation_2026_05_06.plan.md § Phase 1 Tier 1 #1 (MDPS 1440-NaN, paused — now scoped here)
  - shard_granularity_ssot_propagation_2026_05_06.plan.md § Phase 1 Tier 2 raw-tables (sports available_at, paused — now
    scoped here)
status: drafted
---

# Write-Gate + Honest-Coverage End-to-End — Plan (UMBRELLA)

**Branch:** `live-defi-rollout` **Goal:** Collapse two double-SSOT bugs (MDPS empty-handling, sports `available_at`
stamping) and the partial-bundle silent-acceptance class into one cohesive contract change at
`ManifestWriter.record_captured`. Forward + retrospective + UI + QG enforcement so post-merge backfill % across every
service means **real** % (no fake captured rows, no NaN placeholders, no partial bundles passing as complete).

---

## Wrapped sibling plans (this is the single SSOT plan to reference end-to-end)

This is the **umbrella PM plan** for the honest-coverage + shard-granularity work-package. It binds together four
interlocking PM plans into one execution surface. **Do not re-derive todos here** — each child plan remains the
canonical source for its own todos. The umbrella's job is references, sequencing across the layered DAG, and
coordination notes.

| Plan file                                                                                                                                                                                         | Role                             | Owns                                                                                                                                                                                                                                                                                                       |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **`writegate_honest_coverage_endtoend_2026_05_06.plan.md`** (this file)                                                                                                                           | UMBRELLA                         | UTL `record_captured` 4-pillar gate; UAC SSOTs (BUNDLED_DATA_TYPES, source_priority, availability_semantics); MDPS `_create_empty_output` delete + 37-callsite A/B/C migration; MTDS partition validation; features-sports `available_at`; CLAUDE.md rules; UI typed-error rendering; reconcilers; ratchet |
| [`predictions_canonical_question_group_polymarket_migration_2026_05_06.plan.md`](./predictions_canonical_question_group_polymarket_migration_2026_05_06.plan.md)                                  | child                            | UAC predictions classifier + lifecycle module; instruments-service MARKET_LIFECYCLE writer; MTDS Polymarket / Kalshi adapter rekey to `prediction_canonical_question_group`; per-base_asset → canonical_group GCS rewrite; per-market lifecycle gating in features-cross-instrument                        |
| [`shard_granularity_ssot_propagation_2026_05_06.plan.md`](./shard_granularity_ssot_propagation_2026_05_06.plan.md) + [`HANDOVER.md`](./shard_granularity_ssot_propagation_2026_05_06.HANDOVER.md) | parent / architectural rationale | Per-asset-group shard-key matrix; layer discipline (UAC/UTL/per-service); workspace `manifest.add()` → `record_captured()` migration directive (HANDOVER Item 1, mainline). Phase 1 Tier 1 #1 + Tier 2 raw-tables superseded by writegate Phase 2                                                          |
| [`data_status_multi_axis_shard_propagation_2026_05_06.plan.md`](./data_status_multi_axis_shard_propagation_2026_05_06.plan.md)                                                                    | child                            | Read/display side: `fixture_id` (display-axis only) + `job_id` manifest columns; UAC `data_status_axis_matrix.py` SSOT; deployment-api `breakdowns` + `secondary_axis` filtering; deployment-ui DataStatusTab dropdowns + `BreakdownsAccordion`                                                            |

**Layered DAG across all four plans:**

```
Layer 1 (UTL/UAC contract changes — block everything)
  ├── writegate Phase 1A   — UTL record_captured signature + 3 typed errors + availability_stamping helpers
  ├── data_status Phase 0  — UTL fixture_id + job_id columns; UAC data_status_axis_matrix SSOT
  ├── writegate Phase 1B   — UAC BUNDLED_DATA_TYPES / DATA_TYPE_TO_CLUSTER_REGISTRY / SPORTS_FIXTURE_CLUSTERS / PREDICTION_GROUPS={}
  ├── writegate Phase 1C   — CLAUDE.md sections (4 new rules)
  └── predictions Phase 1A — UAC predictions modules; PREDICTION_GROUPS populate; semantics+priority entries
       ↓
Layer 2 (per-service writers — parallel after Layer 1)
  ├── writegate Phase 2.A  — MDPS _create_empty_output delete + 37 A/B/C migration + v3 path delete + v6 column wiring
  ├── writegate Phase 2.B  — MTDS partition validation + workspace-wide manifest.add() → record_captured() migration
  ├── writegate Phase 2.C  — features-sports _ensure_timestamp delete + 4 stub exporter wiring
  ├── writegate Phase 2.D  — URDI sports schema bump (event_time only)
  ├── predictions Phase 2  — instruments-service MARKET_LIFECYCLE + MTDS Polymarket rekey + features-cross-instrument
  ├── data_status Phase 1A — sports fixture_id writers (instruments-service / MTDS / features-sports)
  └── data_status Phase 1B — job_id writers (ml-training / ml-inference / strategy-service / execution-service)
       ↓
Layer 3 (deployment-api + UI — parallel after Layer 2; shares data_status_service.py)
  ├── writegate Phase 4.A   — typed-error rendering + per-pillar breakdown + live-vs-historical alert
  ├── predictions Phase 4.A — PREDICTION_DATA_TYPE_META + lifecycle expected-coverage endpoint
  ├── data_status Phase 2   — SHARD_AXIS_MATRIX consumer + _build_breakdowns + secondary_axis query params
  ├── writegate Phase 4.B   — DataStatusTab per-typed-error display
  ├── predictions Phase 4.B — canonical_question_group rollup + lifecycle viz + classifier confidence
  └── data_status Phase 3   — BreakdownsAccordion + axis selector + cell-grid query wiring
       ↓
Layer 4 (retrospective migrations — parallel after Layer 2)
  ├── writegate Phase 3      — 1440-NaN flip + partial-bundle reflip + pre-v6 cleanup + GCS available_at backfill
  ├── predictions Phase 3    — Polymarket per-base_asset → canonical_group GCS rewrite + manifest reflip
  └── data_status Phase 4    — almost no-op; conditional per-service migrations only if Phase 1A audit reveals incorrectly-populated feature_group/chain/timeframe/league_id writers
       ↓
Layer 5 (validation + ratchet)
  ├── data_status Phase 5    — rollup worker rebuild (Cloud Run)
  ├── writegate Phase 5      — coverage measurement + baseline doc + LookaheadBias smoke + write-gate quartet
  ├── predictions Phase 5    — per-canonical_group baseline + ratchet floor
  └── data_status Phase 6    — workspace QG sweep + e2e ml-training + e2e sports fixture drill-down
```

QG gate between every layer. No Layer N+1 todo starts until every Layer N todo across every sibling plan is checked +
workspace QG passes on every repo touched in Layer N.

---

This plan resolves the 3 CRITICAL questions in the parent HANDOVER (MDPS contract shape / sports raw-tables migration /
cluster-validation sequencing) into a single shippable work-package per the user's framework: production-grade, no
double-SSOT, schema/manifest/GCS migrations sanctioned where needed, no compat shims.

---

## Workflow note for the executing agent

**Direct git workflow, NOT quickmerge.** Confirmed by user 2026-05-06: `bash scripts/quality-gates.sh` per-repo on the
touched files, then `git add` + `git commit` + `git push origin live-defi-rollout` directly. Skip the two-pass model.
Skip `quickmerge`. Reasoning: this is a multi-week multi-repo plan; quickmerge per commit is friction without benefit.

**Before every commit + push:**

1. `git fetch origin` — pull the latest reference; do NOT auto-merge.
2. `git log HEAD..origin/live-defi-rollout --pretty='%h %ae %s'` — list incoming commits from anyone else (semver-bot,
   harshkantariya, parallel agents).
3. For each incoming commit, decide:
   - **Compatible with this plan's scope** → `git pull --rebase` to absorb cleanly + continue.
   - **Touches the same files this plan modifies** → read the diff. If complementary, rebase + adapt. If in direct
     conflict with a plan principle, do NOT revert silently — flag back to the user with: commit hash, author, file:line
     of conflict, summary of what the incoming commit does vs what the plan requires, and ask for direction. Pause work
     on that file until user responds; continue on unaffected files.
4. After your push, `git fetch origin && git log HEAD..origin/live-defi-rollout` — if anything new landed during your
   push (race), absorb-and-continue or flag-and-pause per the same rule.

**Concurrent-stream awareness (sports phantom recovery)**: the "Concurrent in-flight stream" section below documents the
active sports backfill VM. Don't kill that VM, don't revert commits from that stream without coordination — they're
solving a related-but-separate phantom-recovery problem with its own correctness invariants.

**Workspace concurrency rule (CLAUDE.md `§ Per-VM shard isolation`)**: when this plan's reconciler scripts in Phase 3
fan out to multiple VMs, each VM sets `VM_NAME=<unique>` + `MANIFEST_PER_VM_SHARDS=true`. Without this, parallel
reconcilers clobber each other's manifest writes.

---

## Cross-cutting principles (confirmed 2026-05-06)

These bind every todo in this plan. Workspace CLAUDE.md additions in Phase 1C codify them:

1. **Production-grade `>99%` means real `>99%`** — denominator clipped to legitimately-coverable shards (per existing
   `SOURCE_COVERAGE_START` / `KNOWN_COVERAGE_GAPS` / `venue_trading_calendar`); numerator counts only honest captures
   (real rows passing the 4-pillar write-gate). NaN placeholders + partial bundles + silent per-schema drops do not
   count.

2. **Single SSOT only — no double-SSOT in the data-saving methodology.** Where two paths exist for the same outcome, one
   is deleted. No `_create_empty_output()` AND `_handle_empty_tick_data()`; no `_ensure_timestamp` shim AND per-source
   `stamp_available_at_*` helpers; no parallel v3-shape `_write_manifest_records` AND v6 canonical writer; no inline
   NaN-ratio gate AND UTL helper.

3. **Schema, manifest, GCS, code rewrites are sanctioned wherever the SSOT requires them.** No backwards-compatibility
   shims, no fallback readers for legacy shapes (one documented exception: hive-vocab `category=` vs `asset_group=` per
   existing CLAUDE.md asset-group section). Migration scripts replace fallback readers; fallback readers get deleted.

4. **Live = batch = same data, same fields, same timing semantics.** Live just gets the data through different
   sources/endpoints because some live sources are faster than the canonical historical one. Historical writes are
   timestamped as if collected by the live pipeline (the source the live pipeline would actually use). Live and batch
   produce identical schemas; they do NOT differ in data_types or fields available.

5. **`available_at` is per-row, stamped at write-time, equal to when our live pipeline would have actually got that
   row's information.** Never derived at read-time. For multi-source data_types, the source priority registry (Phase 1B)
   determines which source's timestamp is used.

6. **Cluster validation is mandatory at `record_captured` for bundled shards.** No opt-out, no helper-call-pattern, no
   "will wire it later." Runtime enforcement (UTL guard) + static enforcement (QG STEP 5.64). If the data_type is in
   `BUNDLED_DATA_TYPES`, `expected_root_clusters` must be passed or the call raises.

7. **Three-category empty-output decision tree.** Every condition that could produce an empty result resolves to ONE of:
   - **A. Source returned 0 ticks for the requested window** → `record_empty(row_key, attempted_at)`. Honest absence.
   - **B. Source returned ticks; ALL fall outside the requested day after `interval_idx` filter** →
     `record_failed(UpstreamTimestampBiasError(observed_dates, expected_day, n_ticks))`. **Upstream bug — partition
     mislabeled at MTDS write-time, OR source replay covered wrong window, OR clock-skew. NOT honest empty.** Paired
     upstream fix in MTDS (Phase 2.B).
   - **C. Rows in window but downstream calc dropped all rows due to NaN/malformed source fields** →
     `record_failed(MalformedTickFieldError(field, n_dropped, sample_values))`. Data-quality issue worth diagnosing.
   - No fourth category. No silent NaN placeholder rows. The `_create_empty_output()` method is deleted from
     `base_adapter`.

---

## Temporary states + their canonical follow-up plans

**Principle**: nothing in this plan accepts a temporary state as final. Every partial implementation lists its named
successor plan that ships the proper fix. No "we'll fix it later" without a doc.

| Temporary state shipped here                                                                                             | What it means                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       | Successor plan / phase                                                                                                                                                                |
| ------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `BUNDLED_DATA_TYPES` includes `prediction_canonical_question_group` with `PREDICTION_GROUPS = {}` empty registry         | The slot is reserved + cluster guard is wired. No caller currently uses this data_type (Polymarket shards per-`base_asset` per current audit). When canonical_question_group SSOT lands, registry gets populated AND Polymarket migrates AND cluster guard fires meaningfully. Until then: any caller using this data_type fails loud → forces them to wait for the SSOT.                                                                                                                                           | [`predictions_canonical_question_group_polymarket_migration_2026_05_06.plan.md`](./predictions_canonical_question_group_polymarket_migration_2026_05_06.plan.md) — drafted 2026-05-06 |
| (no temporary state on `match_end_time`)                                                                                 | `match_end_time` is detected from real source signals, not a constant. Detection cascade in Phase 2.D below: api_football native field → SFI progressive-stats freeze → footystats / understat fallbacks → last-resort `kickoff + 120min` only when all else missing (and that case marks the row with a low-confidence flag).                                                                                                                                                                                      | (in-scope)                                                                                                                                                                            |
| MTDS v6 columns owner sign-off                                                                                           | Wired per the explicit decision rule (see Phase 2.A). UAC owner verifies completeness post-merge in case any data_type's row carries v6-relevant fields we missed.                                                                                                                                                                                                                                                                                                                                                  | In-plan Phase 5 verification todo.                                                                                                                                                    |
| `SOURCE_PRIORITY` registry top-entry-only                                                                                | Phase 1B seeds the priority-1 source per `(asset_group, data_type)`. Multi-source merge (timestamp-availability > coverage > info-richness > merge-different-fields per user 2026-05-06) is its own design pass.                                                                                                                                                                                                                                                                                                    | `multi_source_priority_merge_2026_<TBD>.plan.md` (Tracked Open Questions §7)                                                                                                          |
| MDPS / features-\* `feature_group → required_inputs[]` DAG inlined per-service                                           | Three services keep their local DAGs (features-onchain, features-sports, features-delta-one). Lookahead-bias enforcement still runs but reads from per-service DAG.                                                                                                                                                                                                                                                                                                                                                 | `feature_dag_uac_ssot_2026_<TBD>.plan.md` (Tracked Open Questions §2)                                                                                                                 |
| `announced_at` / `report_time` / `match_end_time` ship with low-confidence default values + `*_confidence` audit columns | Phase 0 audit (2026-05-06) found these fields UNSOURCEABLE from currently-used providers (api_football `/injuries` no timestamp; no source exposes fixture announcement; SFI freeze IS available for match_end_time). Until forward-poll source lands, rows stamp with `kickoff_utc − 14d` (announced_at) / `kickoff_utc − injury_lead_time` (report_time) / `kickoff_utc + 120min` (match_end_time fallback when SFI/api_football miss). `*_confidence` audit columns surface low-default fixtures for re-attempt. | `sports_forward_poll_timestamps_2026_<TBD>.plan.md` (TBD; captures real-time scraping of announcement / injury / match-end timestamps from sources that DO expose them).              |
| Prediction empty path patched with current Polymarket per-base_asset row_key                                             | Phase 2.A scope expansion fixes silent `success=True, candles_generated=0, NO manifest record` bug at `live_workers.py:268-271` with `record_empty(row_key)` call. Until Plan A predictions migrates shard atom to `(asset_group, venue, data_type=prediction_canonical_question_group, canonical_question_group, market_id, day)`, row_key uses current per-base_asset shape. Reconciler in Phase 3.A re-flips these rows once Plan A migrates shape.                                                              | [`predictions_canonical_question_group_polymarket_migration_2026_05_06.plan.md`](./predictions_canonical_question_group_polymarket_migration_2026_05_06.plan.md) — drafted 2026-05-06 |

Anything not listed here is intended as the final shape post-merge. If a reviewer finds a hidden temporary state, file
it as a plan-amendment todo before merging.

---

## Plan amendments — post Phase 0 audit (2026-05-06 Claude session)

The Phase 0 audits surfaced 6 amendments. 5 (A-E) are routed-and-applied based on evidence (see commit message on the
amendment commit for rationale per item). 1 (**F**) is routed to Ikenna because it touches the Phase 1A contract design.

| #     | Amendment                                                                                                                                                                                                                                                                                                                                                                                                                                                              | Status             | Owner                    |
| ----- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------ | ------------------------ |
| A     | Correct Phase 2.B file paths (monolithic `tardis_adapter.py` / `databento_adapter.py` / `tradfi_shared.py`, NOT non-existent `adapters/tardis/options_chain.py` etc.)                                                                                                                                                                                                                                                                                                  | **Applied**        | Cosmetic — Claude        |
| B     | Drop `announced_at` from Phase 2.D schema bumps (no source field exists)                                                                                                                                                                                                                                                                                                                                                                                               | **Applied**        | Evidence-backed — Claude |
| C     | Drop `report_time` / `occurrence_time` for injuries from Phase 2.D as immediately actionable (api_football `/injuries` has no timestamp; we have dates not exact times). Documented in schema-additions table comments.                                                                                                                                                                                                                                                | **Applied**        | Evidence-backed — Claude |
| D     | Defer `match_end_time` schema bump to Stage 2 follow-up plan; keep detection cascade design + current `kickoff+120min` fallback as Stage 1. We have dates not exact end times. Documented in schema-additions table comments.                                                                                                                                                                                                                                          | **Applied**        | Evidence-backed — Claude |
| E     | Add 4 stub-wiring todos to Phase 2.C as prerequisites (`fixture_lineups`, `fixture_player_stats`, `coaches`, `rounds`). 4 export functions silently return empty — distinct bug class from 1440-NaN.                                                                                                                                                                                                                                                                   | **Applied**        | Scope expansion — Claude |
| **F** | **Phase 2.B cluster wiring point** — audit found ZERO `record_captured` callsites for any MTDS bundle. All bundles flow through `writer_manifest.add()` at `engine/orchestrator.py:1940`. Phase 1A's `MissingClusterValidationError` guard at `record_captured` would never fire. Plan needs to either (i) move the wiring point to `orchestrator.py:1940`, or (ii) refactor adapters to call `record_captured` directly. Affects Phase 1A contract design assumption. | **PENDING IKENNA** | Architectural — Ikenna   |

**Phase 2.B execution gate**: do NOT execute the cluster_extractor wiring todo in Phase 2.B until amendment F is
resolved. The Phase 2.B body has been annotated with this gate.

---

## Pre-audit blast radius

> **Phase 0 audit synthesis 2026-05-06 (commit `b304d4ba`)**: counts + file paths + scope below revised based on audit
> findings. See "Phase 0 audit findings" section further down for the full per-callsite breakdown. This pre-audit
> summary is the post-audit shape that Phase 2 todos consume.

### MDPS (market-data-processing-service)

Confirmed **37 `_create_empty_output` callsites** across `app/adapters/{cefi,defi,tradfi,sports}/` (NOT 53 — original
estimate counted method definitions; actual `return self._create_empty_output(...)` callsites = 37). Distribution: **16
path A / 15 path B / 5 path C / 2 ambiguous**. Prediction adapters: **0 direct callsites** — `PredictionTradesAdapter`
subclasses `CefiTradesAdapter` and inherits the 3 cefi/trades_adapter.py callsites without override. Sample paths
showing the bug class:

| Adapter                                                                                             | Sites                    | Notes                                                                                                            |
| --------------------------------------------------------------------------------------------------- | ------------------------ | ---------------------------------------------------------------------------------------------------------------- |
| `defi/swap_adapter.py`                                                                              | 106                      | Confirmed path B (1440 NaN bars when ticks present but outside day)                                              |
| `cefi/trades_adapter.py`                                                                            | 69, 74, 83               | Multiple path types; needs A/B/C decision per site                                                               |
| `cefi/derivative_adapter.py`                                                                        | 69, 99                   |                                                                                                                  |
| `cefi/book_snapshot_adapter.py`                                                                     | 87, 117                  |                                                                                                                  |
| `cefi/futures_chain_adapter.py`                                                                     | 75, 105                  | Bundle data_type — also Phase 2.B cluster-validation site                                                        |
| `cefi/liquidations_adapter.py`                                                                      | 143, 173                 | Liquidations are legitimately sparse — most sites probably path A                                                |
| `cefi/options_chain_adapter.py`                                                                     | 164, 194                 | Bundle — cluster validation site                                                                                 |
| `tradfi/trades_adapter.py`, `tradfi/tbbo_adapter.py`                                                | (multiple)               |                                                                                                                  |
| `sports/odds_snapshot_adapter.py`, `sports/odds_movement_adapter.py`, `sports/arbitrage_adapter.py` | (multiple)               |                                                                                                                  |
| `prediction/*_adapter.py`                                                                           | 0 direct (inherits cefi) | `PredictionTradesAdapter` subclasses `CefiTradesAdapter` without override; cefi/trades_adapter.py 69/74/83 apply |

Existing honest path: `app/core/{batch,live}_workers.py:189` `_handle_empty_tick_data` (called from line 269 of
live_workers — so the routing infra exists; adapters bypass it). **NEW BUG SURFACED in Phase 0 audit — distinct from
1440-NaN class but equally opaque**: orchestrator's prediction empty path at `live_workers.py:268-271` calls
`_handle_empty_tick_data(category, ...)`. For `MarketAssetGroup.PREDICTION`, `batch_workers.py:199` skips the TRADFI
branch and falls through to lines 219-228: returns `success=True, candles_generated=0` **with NO manifest record** (no
`record_empty`, no `record_captured`, no `record_failed`). Phase 2.A scope expanded to fix this.

### MTDS (market-tick-data-service)

| File                                                                                                | Line              | Concern                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| --------------------------------------------------------------------------------------------------- | ----------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `market_tick_data_service/raw_tick_hive.py`                                                         | (writer)          | Phase 2.B: write-time `tick.timestamp.date()` vs `day=` partition validation; reject + log mismatches                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| `adapters/databento_adapter.py`                                                                     | 30–48             | `_PerSchemaFailure` already shipped (parent plan Phase 1) — verify                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| `market_interface/adapters/tradfi/tardis_adapter.py` (Tardis CeFi + TradFi options/futures bundles) | 870, 1693, 1804   | Bundle write — Phase 2.B cluster validation site. **Path corrected per audit 2026-05-06 amendment A**: original plan listed `adapters/tardis/options_chain.py` and `adapters/tardis/futures_chain.py` which do not exist. Tardis logic is in this monolithic file (CeFi + TradFi paths) — `finalise_and_write_cefi_shards()` at line 870, `_download_futures_per_instrument()` at 1693, futures_chain TradFi path at 1804.                                                                                                                                              |
| `market_interface/adapters/cefi/tardis_shared.py`                                                   | 84, 507           | Tardis CeFi shared helper — `CHAIN_INSTRUMENT_TYPES` constant + `build_partition_path()` for v5/v6 chain paths. Phase 2.B touches if cluster_extractor wires through here.                                                                                                                                                                                                                                                                                                                                                                                              |
| `market_interface/adapters/tradfi/tradfi_shared.py`                                                 | 296, 423          | TradFi shared write helper — `_shard_instrument_type_for(OPTION) → "options_chain"` decision at line 296; `write_tradfi_shard()` at line 423 is the actual upload site for both Tardis-TradFi and Databento-TradFi bundle paths.                                                                                                                                                                                                                                                                                                                                        |
| `market_interface/adapters/tradfi/databento_adapter.py` (Databento TradFi options/futures bundles)  | 91, 822, 869–1001 | Bundle write — Phase 2.B cluster validation site. **Path corrected per audit 2026-05-06 amendment A**: original plan listed `adapters/databento/options_chain.py` and `adapters/databento/futures_chain.py` which do not exist. Databento logic is in this monolithic file: `_PARTITION_INSTRUMENT_TYPE` at line 91 (OPTION → options_chain), `download_batch_df()` writer.write_chunk() at 822, `_enrich_with_canonical_ids()` at 869-1001.                                                                                                                            |
| `engine/orchestrator.py`                                                                            | 1940              | **CRITICAL ARCHITECTURAL FINDING — amendment F escalated to Ikenna by harsh's `72ebe7a6`**: ALL MTDS bundles flow through `writer_manifest.add()` here. ZERO `record_captured` callsites for any MTDS bundle adapter. Phase 1A guard inside `record_captured` would NEVER fire if Phase 2.B wires at the adapter layer. Phase 2.B wiring point likely needs to MOVE to this orchestrator callsite (Option α: refactor `:1940` to call `record_captured`) OR refactor each adapter to call `record_captured` directly (Option β). Pending Ikenna review per amendment F. |
| `polymarket_adapter.py`                                                                             | 590               | Prediction CLOB write — current `data_type="trades"` + group-by `underlying`; future `prediction_canonical_question_group` per Plan A predictions plan. Phase 2.B keeps the cluster guard wired but with empty `PREDICTION_GROUPS` registry until Plan A's UAC SSOT lands.                                                                                                                                                                                                                                                                                              |
| `umi_tick_provider.py`                                                                              | 225               | `category=` → `asset_group=` vocab cleanup                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |

### features-sports-service

| File                                                        | Line               | Concern                                                                        |
| ----------------------------------------------------------- | ------------------ | ------------------------------------------------------------------------------ |
| `cli/handlers/batch_handler.py`                             | 76–91              | `TABLE_TO_EXPORT` 14 entries — drives Phase 2.C per-table available_at logic   |
| `cli/handlers/batch_handler.py`                             | 146                | `_ensure_timestamp` shim (DELETE in Phase 2.C)                                 |
| `cli/handlers/batch_handler.py`                             | 383, 465, 528, 597 | `_ensure_timestamp` callsites — replace with per-source `stamp_available_at_*` |
| `cli/batch_write.py`                                        | 38, 88             | Sibling `_ensure_timestamp` (DELETE)                                           |
| `exporters/exports.py`                                      | (each export\_\*)  | Per-table `available_at` stamping logic                                        |
| `exporters/_fetch_runner.py` (or wherever the runner lives) | —                  | Add `_FETCH_COMPLETED_AT: dict[table, datetime]` for the 8 reference tables    |

### instruments-service (sports schemas)

Schema additions (in `unified_reference_data_interface` / sports schemas):

| Schema                                                  | Add column                                                                                                    | Status (post Phase 0 audit 2026-05-06) | Reason / Source-side reality                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| ------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- | -------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `FIXTURES_COLUMNS`                                      | ~~`announced_at` (timestamp UTC)~~                                                                            | **DROPPED — amendment B**              | NO source exposes fixture-announcement time. api_football, footystats, understat all return scheduled kickoffs without an announcement timestamp. Current `kickoff − 7d` proxy in `_stamp_available_at` (`batch_handler.py:278-280`) is the maximum achievable precision; document as canonical synthesis. If a future provider exposes announcement time, route to a separate plan.                                                                                                                                                                                                                                                                                                                                                              |
| `FIXTURE_EVENTS_COLUMNS`                                | `event_time` (timestamp UTC)                                                                                  | **KEPT — derivable**                   | api_football provides `time.elapsed` (integer in-game minute). `event_time = kickoff_utc + elapsed_min * 60s` — derive at the normalizer (in `gcs_reader._normalize_fixture_events`) when `kickoff_utc` is joinable. Approximation caveat: doesn't account for clock-stoppage / extra-time overruns; maximum precision available without per-event wall-clock from api_football.                                                                                                                                                                                                                                                                                                                                                                  |
| `INJURIES_COLUMNS`                                      | ~~`report_time` / `occurrence_time` (timestamp UTC)~~                                                         | **DROPPED — amendment C**              | API-Football `/injuries?date=YYYY-MM-DD` endpoint returns NO timestamp field — only `player`, `team`, `fixture`, `league`, `season`, `reason`, `type`. The `date` filter is the FETCH date, not the injury event time. **We only have dates, not exact times.** Route to a separate plan: instruments-service forward-poll-vs-backfill timestamp differentiation (so `available_at` could be approximated as "first time we observed this injury in our forward-poll stream").                                                                                                                                                                                                                                                                    |
| `FIXTURE_STATS_COLUMNS`, `FIXTURE_PLAYER_STATS_COLUMNS` | ~~`match_end_time` (timestamp UTC)~~ as Stage 1 in this plan; precision upgrade deferred to Stage 2           | **DEFERRED — amendment D**             | **We only have dates, not exact end times** from any current source. api_football stores `status` string ("FT") but not `fixture.fixture.timestamp` or `fixture.status.elapsed` in the FIXTURES schema. understat / footystats not yet audited for match-end timestamp exposure. Stage 1 (in this plan): keep `stamp_available_at_post_match(kickoff_col=kickoff_utc, duration_min=120)` fallback (already wired at `batch_handler.py:287-312`). Stage 2 (deferred follow-up plan): instruments-service stores `fixture.status.elapsed` + `fixture.fixture.timestamp` from api_football response → enables match_end_time precision upgrade. The detection cascade (Phase 2.D body) stays in scope as designed; only the schema bump is deferred. |
| `FIXTURE_LINEUPS_COLUMNS`                               | `available_at` derived as `kickoff_utc − 60min` (constant); no schema column needed if we stamp at write-time | **KEPT**                               | Conservative — lineups are always at LEAST 60min before, often 1–2h. Stamping rule applies via `stamp_available_at_kickoff_offset(kickoff_col=kickoff_utc, minutes=60)`. Prerequisite: wire `fixture_lineups` stub (currently discards GCS data at `_fetch_runner.py:171`) — see Phase 2.C amendment E.                                                                                                                                                                                                                                                                                                                                                                                                                                           |

Blast radius for schema bumps: **0 references to these schemas outside features-sports-service** (verified:
`FIXTURE_STATS_COLUMNS|FIXTURE_EVENTS_COLUMNS|FIXTURE_LINEUPS_COLUMNS|FIXTURE_PLAYER_STATS_COLUMNS|INJURIES_COLUMNS` —
47 hits all inside features-sports-service, 0 in MDPS / strategy-service / features-onchain). Schema bumps are free.

**Net Phase 2.D schema-bump scope (post-amendments)**: only `event_time` on `FIXTURE_EVENTS_COLUMNS` (derivable).
`FIXTURE_LINEUPS` uses the kickoff-offset stamping rule without a new column. The other 3 proposed columns
(`announced_at`, `report_time`/`occurrence_time`, `match_end_time`) are unsourceable from any current provider — we have
dates, not exact times. The `kickoff − 7d` / `kickoff + 120min` proxies remain the canonical synthesis until separate
follow-up plans add forward-poll timestamp differentiation or upstream-source enrichment.

### UTL (unified-trading-library)

| File                       | Line                        | Change                                                                                                                                                 |
| -------------------------- | --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------- |
| `manifest_writer.py`       | 97                          | `ClusterCoverageError` ✓ exists                                                                                                                        |
| `manifest_writer.py`       | 1098                        | `check_cluster_coverage` — make private (`_check_cluster_coverage`); no longer public API                                                              |
| `manifest_writer.py`       | 1163                        | `record_captured` — add `expected_root_clusters: Mapping[str, int] \| None` + `cluster_extractor: Callable                                             | None`kwargs; raise`MissingClusterValidationError`when`data_type ∈ BUNDLED_DATA_TYPES` and kwargs not passed |
| `errors.py`                | new                         | `UpstreamTimestampBiasError`, `MalformedTickFieldError`, `MissingClusterValidationError`                                                               |
| `availability_stamping.py` | (already exists per LIFT-3) | Add `stamp_available_at_post_match`, `stamp_available_at_announcement`, `stamp_available_at_explicit`, `stamp_available_at_kickoff_offset(minutes=60)` |

### UAC (unified-api-contracts)

New SSOT registries (each under `unified_api_contracts.canonical.crosscutting.honest_coverage` or similar):

| Registry                        | Type                                                   | Content                                                                                                                                                         |
| ------------------------------- | ------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `BUNDLED_DATA_TYPES`            | `frozenset[str]`                                       | `{"options_chain", "futures_chain", "prediction_canonical_question_group", "sports_fixture_bundle"}`                                                            |
| `DATA_TYPE_TO_CLUSTER_REGISTRY` | `dict[str, str]`                                       | `data_type` → registry-symbol-name (e.g. `"options_chain"` → `"OPTIONS_CLUSTERS"`)                                                                              |
| `OPTIONS_CLUSTERS`              | `dict[root, dict[cluster, min_rows]]`                  | ES.OPT seed already exists in instruments-service per HANDOVER; lift to UAC                                                                                     |
| `FUTURES_CLUSTERS`              | (analogous)                                            | Combo/spread cluster taxonomies; greenfield-light                                                                                                               |
| `SPORTS_FIXTURE_CLUSTERS`       | (TBD)                                                  | Greenfield — per-fixture aggregate cluster (bookmakers per fixture, etc.)                                                                                       |
| `SOURCE_PRIORITY`               | `dict[(asset_group, data_type), list[str]]`            | Source rank by tie-breakers (timestamp-availability > coverage > info-richness) — Phase 1B writes top entry only; multi-source merge logic deferred             |
| `AVAILABILITY_AT_SEMANTICS`     | `dict[(asset_group, data_type), AvailabilitySemantic]` | Per-data_type stamping rule (`fetch_completed_at`, `kickoff_minus_60min`, `match_end_time`, `event_time`, `report_time`, `announced_at`, `forecast_issue_time`) |

Existing UAC artifacts to preserve: `SOURCE_COVERAGE_START`, `DATA_TYPE_COVERAGE_START`, `KNOWN_COVERAGE_GAPS`,
`venue_trading_calendar`, `RAW_TICK_ASSET_GROUP_HIVE_KEY` / `_LEGACY`.

### deployment-ui / deployment-api

| Surface                  | Change                                                                                                                                                                                            |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Data-status panel        | Render `attempted_failed` reasons distinctly per typed error (color + drill-down): `EmptyPlaceholderBugBackfill`, `ClusterCoverageError`, `UpstreamTimestampBiasError`, `MalformedTickFieldError` |
| Schema-view per-leaf     | Show `available_at` min/max/null-count alongside row-count + per-column NaN ratio                                                                                                                 |
| Per-pillar breakdown     | New columns: `failed_row_count` / `failed_nan_ratio` / `failed_schema` / `failed_cluster` per shard                                                                                               |
| Live-vs-historical alert | Surface when historical-mode produces the same `data_type` for a date that is in the live window (would imply double-write)                                                                       |

---

## Phase DAG

```
Phase 0 (audit, mostly done)
  → Phase 1A (UTL contract)  ──┐
  → Phase 1B (UAC SSOTs)    ──┤── Phase 2 (parallel: 2A MDPS, 2B MTDS, 2C features-sports, 2D instruments-service)
  → Phase 1C (CLAUDE.md)    ──┘     │
                                    ▼
                              Phase 3 (Retrospective: 3A reconcilers, 3B GCS stamping, 3C pre-v6 cleanup)
                                    │
                                    ▼
                              Phase 4 (UI + alerts) ── runs partly in parallel with Phase 2
                                    │
                                    ▼
                              Phase 5 (Validation + honest-coverage baseline)
```

QG gates between every phase. No Phase N+1 todo starts until every Phase N todo is checked + workspace QG passes on
every repo touched in Phase N.

---

## Concurrent in-flight stream — sports phantom FIXTURES recovery (2026-05-06)

A separate stream is running in parallel to this plan, owned by the
`sports_phantom_fixtures_recovery_2026_05_06.plan.md` plan. Be aware while executing this plan because the recovery
touches the same `ManifestWriter` / orchestrator surfaces this plan modifies — the two streams must not step on each
other.

### What's running

**Live VM (as of 2026-05-06 13:54 UTC)**: `af-backfill-20260506-135454` on asia-northeast1-c, e2-standard-4, running
api_football FIXTURES backfill 2020-06-06 → 2026-05-04. Estimated ~10h wall-clock (most dates are no-fixture days = fast
paths; match days ~80s each for the api_football fetch + per-league manifest write). After this VM auto-shuts, a
sequential chain runner (`deployment-service/scripts/vm/run-sports-phantom-downstream-chain.sh`, commit `5be53a7`)
launches 5 follow-on VMs (PLAYER_STATS / FIXTURE_STATS / FIXTURE_EVENTS / FIXTURE_LINEUPS / INJURIES) — singleton-locked
on `af-backfill-` prefix; ~3-5h sequential.

### Why it's running

The orchestrator's FIXTURES adapter pre-2026-05-06 was emitting `manifest.add(row_count=0)` for every Prediction-tier
league × date (zero-fixture days), creating ~100k phantom `captured` rows that violate CLAUDE.md "4 pillars" rule #1.
Root-cause writer fix shipped in instruments-service `f36651c`. The recovery sequence:

1. `flip_phantom_fixtures_zero_rows.py` (instruments-service `962982e`) flipped 100k phantoms
   `captured`+`instrument_count=0` → `empty_confirmed`. **Wrong**: orchestrator skips both `captured` and
   `empty_confirmed`.
2. `flip_phantom_to_attempted_failed.py` (`2821111`) re-flipped to `attempted_failed` + extended to 75k cap-zero rows on
   per-fixture downstreams (PLAYER_STATS / FIXTURE_STATS / FIXTURE_EVENTS / FIXTURE_LINEUPS / INJURIES).
   **Insufficient**: discovered `check_shard_freshness` ignores `capture_status` — attempted_failed treated as "fresh"
   by orchestrator pre-flight (see `feedback_check_shard_freshness_ignores_capture_status.md`).
3. `write_phantom_reflip_per_vm_shard.py` (`2d18d0d`) mirrored corrective rows to a fresh per-VM shard so reader's
   fall-back merge sees them past the 120s canonical mtime threshold (see
   `feedback_manifest_reader_staleness_per_vm_fallback.md`).
4. `delete_phantom_rows_from_shards.py` (`73be000`) **DELETED** the 176k phantom rows (canonical + 10 per-VM shards with
   backups). Goal: orchestrator sees them as MISSING and re-fetches.
5. **Discovered**: orchestrator pre-flight is at (date, data_type) granularity, not per-league — once any league has
   FIXTURES for date X, the date is "fresh" and the WHOLE date is skipped. See
   `feedback_orchestrator_freshness_per_league_granularity.md`.
6. **Orchestrator patched** (instruments-service `d73565a`) to defer pre-flight to per-entity handlers when `expected[]`
   contains any of 17 sports per-league entities. Per-entity handlers' existing `_should_skip_date_for_per_league`
   pattern (orchestrator.py:490) handles per-(date, data_type, league_id) correctly. **THIS is the architectural fix
   this plan should be aware of.**

The currently-running VM v6 was launched after the patch + confirmed working in production: log shows
`"date=2020-06-07: deferring pre-flight to per-league entity handlers"` +
`"SPORTS: No fixtures for date=2020-06-07 — wrote empty_confirmed markers for 33 leagues"`. Patch is live + correct
behavior.

### Potential effects on this plan

**Surfaces touched that overlap with this plan's scope:**

1. **`ManifestWriter` per-VM shard merge** (`unified-trading-library/.../manifest_writer.py:2222`): the recovery
   stream's `delete_phantom_rows_from_shards.py` mutated the `_index/per_vm/*.parquet` set in the sports bucket. If this
   plan's Phase 1A `record_captured` contract change introduces new shard-key columns or migrates existing ones, the
   recovery's deleted-then-rewritten rows must migrate cleanly. The DELETE script's signature filter
   (`(capture_status='attempted_failed' AND error_reason marker) OR (capture_status='captured' AND instrument_count==0)`)
   leaves all columns otherwise unchanged, so a v6→v7 schema upgrade should be transparent.

2. **`check_shard_freshness` (UTL)**: this plan's Phase 1A may add per-row capture_status filtering to the freshness
   check (closing the "attempted_failed treated as fresh" hole architecturally rather than via per-service
   defer-to-handler workaround). When that lands, the per-service patch in instruments-service `d73565a` becomes
   redundant but harmless — it just makes is_fresh=False unconditionally for sports per-league entities, which is what
   the new UTL behavior would do anyway. Recommend keeping the instruments-service patch in place until UTL fix ships +
   verifying the new path doesn't regress (test: launch a `--sports-entity FIXTURES` VM, confirm it doesn't skip-cycle).

3. **Manifest backups in canonical bucket**: recovery wrote 4 backup blobs in
   `gs://instruments-store-sports-central-element-323112/_index/`:
   - `availability_index.20260506-111222.bak.parquet` (pre-flip-1)
   - `availability_index.20260506-112347.bak.parquet` (pre-flip-2)
   - 10 per-VM shard `.20260506-120021.bak.parquet` siblings (pre-DELETE) These are reversibility safety nets. **Do not
     delete** them while the recovery VMs are still running. After verify (~2026-05-07) they can be purged.

4. **`af-backfill-` VM concurrency**: the recovery stream's chain runner uses the singleton-locked launcher
   (`launch-api-football-backfill-vm.sh`). This plan's Phase 2.D instruments-service work (writer-side changes to
   `_create_empty_output` callsite categorisation) does not launch `af-backfill-` VMs, so no direct lock conflict — but
   if a Phase 2.D smoke test wants to launch one, sequence after the chain runner has finished its 5 entities or use
   `--force`.

5. **Orchestrator `defer pre-flight` log line**: the new log signature is
   `"date={D}: deferring pre-flight to per-league entity handlers (sports per-league mode; expected={...})"`. If this
   plan adds telemetry/structured events around pre-flight, this is a new log shape to be aware of.

### Memory entries to read for context

- `project_sports_phantom_fixtures_recovery_2026_05_06.md` — full session log
- `feedback_orchestrator_freshness_per_league_granularity.md` — the architectural finding that drives the orchestrator
  patch
- `feedback_check_shard_freshness_ignores_capture_status.md` — the related UTL-level finding
- `feedback_manifest_reader_staleness_per_vm_fallback.md` — the 120s mtime threshold gotcha (relevant to any one-shot
  manifest mutation script this plan's Phase 3 might write)

---

## Phase 0 — Pre-audit + remaining blast-radius gaps

- [x] [AUDIT] P0. instruments-service delta vs HANDOVER findings (done 2026-05-06; see HANDOVER §instruments-service
      post-audit).
- [x] [AUDIT] P0. MDPS — categorise all 53 `_create_empty_output` callsites into A / B / C. **Done 2026-05-06.** See
      "Phase 0 audit findings — MDPS callsite categorisation" below.
- [x] [AUDIT] P0. MDPS prediction adapters — count `_create_empty_output` sites + classify. **Done 2026-05-06.** See
      "Phase 0 audit findings — MDPS prediction adapters" below.
- [x] [AUDIT] P0. MTDS — confirm bundle adapter list + each adapter's row schema. **Done 2026-05-06.** See "Phase 0
      audit findings — MTDS bundle adapter inventory" below.
- [x] [AUDIT] P0. features-sports — for each of the 14 `TABLE_TO_EXPORT` entries, document the actual source columns
      currently present. **Done 2026-05-06.** See "Phase 0 audit findings — features-sports TABLE_TO_EXPORT inventory"
      below.
- [x] [AUDIT] P0. Multi-source coverage matrix per `(asset_group, data_type)`. **Done 2026-05-06.** See "Phase 0 audit
      findings — multi-source coverage matrix" below.
- [ ] [AUDIT] P0. instruments-service sports schemas — confirm the columns to add (`announced_at` on fixtures;
      `event_time` on fixture_events; `report_time` on injuries; `match_end_time` on fixture_stats /
      fixture_player_stats). **PARTIAL via #0.4 audit**: features-sports audit revealed source-side blockers — see
      "Phase 0 audit findings — features-sports TABLE_TO_EXPORT inventory" §"Tables blocked on upstream source-field
      availability". Schema bumps still needed for `event_time` (derivable from `kickoff_utc + elapsed_min`); the
      remaining proposed columns (`announced_at`, `report_time`, `match_end_time`) cannot be sourced from current
      providers — see findings below.

QG between Phase 0 and Phase 1A/1B/1C: audit manifest reviewed by user; per-callsite A/B/C decisions signed off;
SOURCE_PRIORITY tie-breaker rules confirmed for each (asset_group, data_type) where multi-source applies.

---

## Phase 0 audit findings (2026-05-06 Claude session)

### Phase 0 audit findings — MDPS callsite categorisation

**Total callsites: 37** (NOT 53 — original plan estimate counted method definitions; actual
`return self._create_empty_output(...)` callsites = 37). Distribution: 16 A / 15 B / 5 C / 2 ?.

| File:Line                                 | Branch trigger                                                                          | Category | Reason                                                                                                                                                                                                                 |
| ----------------------------------------- | --------------------------------------------------------------------------------------- | -------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `cefi/book_snapshot_adapter.py:87`        | tick_data empty on entry                                                                | A        | Honest absence — no rows from MTDS                                                                                                                                                                                     |
| `cefi/book_snapshot_adapter.py:117`       | tick_data empty after `interval_idx` filter                                             | B        | Ticks present, all outside requested day — upstream timestamp bias                                                                                                                                                     |
| `cefi/derivative_adapter.py:69`           | tick_data empty on entry                                                                | A        |                                                                                                                                                                                                                        |
| `cefi/derivative_adapter.py:99`           | tick_data empty after filter                                                            | B        |                                                                                                                                                                                                                        |
| `cefi/futures_chain_adapter.py:75`        | tick_data empty on entry                                                                | A        | Bundle: "no rows" = no contracts had quotes; not a cluster failure                                                                                                                                                     |
| `cefi/futures_chain_adapter.py:105`       | tick_data empty after filter                                                            | B        | Bundle B-category — upstream partition bias                                                                                                                                                                            |
| `cefi/liquidations_adapter.py:143`        | tick_data empty on entry                                                                | A        | Legitimately sparse for low-OI                                                                                                                                                                                         |
| `cefi/liquidations_adapter.py:173`        | tick_data empty after filter                                                            | B        |                                                                                                                                                                                                                        |
| `cefi/options_chain_adapter.py:164`       | tick_data empty on entry                                                                | A        | Bundle A-category                                                                                                                                                                                                      |
| `cefi/options_chain_adapter.py:194`       | tick_data empty after filter                                                            | B        | Bundle B-category                                                                                                                                                                                                      |
| `cefi/trades_adapter.py:69`               | tick_data empty on entry                                                                | A        |                                                                                                                                                                                                                        |
| **`cefi/trades_adapter.py:74`**           | `_prepare_tick_data` returned None (interval_idx filter dropped all)                    | **B**    | **Plan-confirmed reproduction path** — non-empty input, empty after bucketing                                                                                                                                          |
| `cefi/trades_adapter.py:83`               | `price_col is None` (no derivable price column)                                         | C        | Schema/field error — derive_price_column failed                                                                                                                                                                        |
| `defi/fx_rate_adapter.py:120`             | tick_data empty on entry                                                                | A        |                                                                                                                                                                                                                        |
| `defi/fx_rate_adapter.py:131`             | `_detect_asset(instrument_id)` returned None                                            | **C**    | **NEW finding**: instrument_id pattern unrecognised — schema/metadata gap                                                                                                                                              |
| `defi/fx_rate_adapter.py:136`             | `_ASSET_TO_FEATURE.get(asset)` returned None                                            | **C**    | **NEW finding**: asset detected but no feature mapping — registry gap                                                                                                                                                  |
| `defi/fx_rate_adapter.py:167`             | `price_col is None` (none of `(price, close, last, price_usd, usd_price)` in columns)   | **C**    | **NEW finding**: source schema drift — column name probe stale                                                                                                                                                         |
| `defi/liquidity_adapter.py:87`            | tick_data empty on entry                                                                | A        |                                                                                                                                                                                                                        |
| `defi/liquidity_adapter.py:119`           | tick_data empty after filter                                                            | B        |                                                                                                                                                                                                                        |
| `defi/market_state_adapter.py:77`         | tick_data empty on entry                                                                | A        |                                                                                                                                                                                                                        |
| `defi/market_state_adapter.py:109`        | tick_data empty after filter                                                            | B        |                                                                                                                                                                                                                        |
| `defi/swap_adapter.py:74`                 | tick_data empty on entry                                                                | A        |                                                                                                                                                                                                                        |
| **`defi/swap_adapter.py:106`**            | tick_data empty after filter                                                            | **B**    | **Plan-confirmed reproduction path** — 1440 NaN bars when swaps timestamp-mislabeled                                                                                                                                   |
| `sports/arbitrage_adapter.py:42`          | tick_data empty on entry                                                                | A        |                                                                                                                                                                                                                        |
| `sports/arbitrage_adapter.py:79`          | tick_data empty after filter                                                            | B        | Sports odds B-category — multi-day spans + wrong partition                                                                                                                                                             |
| `sports/bucket_assignment_adapter.py:313` | tick_data empty on entry                                                                | A        |                                                                                                                                                                                                                        |
| `sports/bucket_assignment_adapter.py:319` | `_prepare_tick_data` returned empty (pivot/column failure)                              | C        | Schema mismatch — `bm_minutes_to_kickoff` missing or pivot failed                                                                                                                                                      |
| `sports/bucket_assignment_adapter.py:331` | all rows had `horizon_idx == -1` (outside staleness caps)                               | **?**    | **Ambiguous**: legitimately stale odds (A) vs miscalculated `bm_minutes_to_kickoff` (C). **Recommend C provisionally** — derived field; miscalc most likely cause                                                      |
| `sports/odds_movement_adapter.py:37`      | tick_data empty on entry                                                                | A        |                                                                                                                                                                                                                        |
| `sports/odds_movement_adapter.py:74`      | tick_data empty after filter                                                            | B        |                                                                                                                                                                                                                        |
| `sports/odds_snapshot_adapter.py:41`      | tick_data empty on entry                                                                | A        |                                                                                                                                                                                                                        |
| `sports/odds_snapshot_adapter.py:78`      | tick_data empty after filter                                                            | B        |                                                                                                                                                                                                                        |
| `tradfi/ohlcv_passthrough.py:89`          | tick_data empty on entry → `_create_full_day_empty_output` (sets `market_state=CLOSED`) | **?**    | **Ambiguous**: INTENTIONAL (closed-market signal) IF orchestrator pre-skips non-trading days via `venue_trading_calendar`; A/B otherwise. **Needs human review**: verify pre-flight reliability before re-categorising |
| `tradfi/tbbo_adapter.py:73`               | tick_data empty on entry                                                                | A        |                                                                                                                                                                                                                        |
| `tradfi/tbbo_adapter.py:103`              | tick_data empty after filter                                                            | B        |                                                                                                                                                                                                                        |
| `tradfi/trades_adapter.py:67`             | tick_data empty on entry                                                                | A        |                                                                                                                                                                                                                        |
| `tradfi/trades_adapter.py:97`             | tick_data empty after filter                                                            | B        |                                                                                                                                                                                                                        |

**Notable findings**:

- 5 NEW Path C sites in `fx_rate_adapter` not in original plan estimate — 3 distinct error classes (asset detection,
  feature mapping, price-column probe).
- `tradfi/ohlcv_passthrough.py:89` could be **INTENTIONAL** (deletes the site entirely) — needs runtime verification of
  orchestrator's `venue_trading_calendar` pre-skip.
- Bundle adapters (futures_chain / options_chain): A/B sites fire BEFORE cluster validation; cluster-coverage failure is
  a separate path at `record_captured` (Phase 2.B).

### Phase 0 audit findings — MDPS prediction adapters

**Direct callsites in `app/adapters/prediction/`: 0**.

`PredictionTradesAdapter` subclasses `CefiTradesAdapter` directly and **does not override `process_to_candles`**. The 3
cefi/trades_adapter.py callsites (69 / 74 / 83) are inherited as-is and apply to prediction (mapping to A / B / C
respectively).

**NEW BUG SURFACED — distinct from 1440-NaN class**: orchestrator's prediction empty path at `live_workers.py:268-271`
calls `_handle_empty_tick_data(category, ...)`. For prediction (`MarketAssetGroup.PREDICTION`), `batch_workers.py:199`
skips the TRADFI branch and falls through to lines 219-228: `success=True, candles_generated=0` returned **with NO
manifest record** (no `record_empty`, no `record_captured`, no `record_failed`).

Implications:

- Resolved/never-traded condition_ids return `success` silently — invisible to manifest, denominator counts as
  `missing`.
- Pipeline re-attempts every backfill run (wasted I/O against empty GCS paths).
- Cannot distinguish "haven't processed this day" from "processed it, market resolved before day".
- **Phase 2.A scope expansion**: orchestrator's prediction empty path needs a `record_empty(row_key)` call alongside the
  typed-exception migration.

Plan's 53-site count confirmed: prediction contributes 0 direct sites; the actual full count is 37
(cefi/defi/tradfi/sports inherited paths only).

### Phase 0 audit findings — MDPS `except: continue / return None` sweep beyond `_create_empty_output`

**Methodology**: AST-walked all `.py` files under `market_data_processing_service/` (excluding `.venv`, `build`,
`tests`) for `except` blocks whose body contains `continue`, `pass`, `return None`, or bare `return`. Each site read in
context, classified by severity, checked against whether a manifest `record_failed` follows.

**Total sites found: 24** across 15 files. Distribution: 7 HIGH / 4 MEDIUM / 13 LOW.

**Key cross-cutting finding (refactor target — feeds Phase 2.A scope expansion)**:

Three parallel write-path copies of the same swallow exist — `candle_write_mixin._write_candles` (line 141),
`data_sink.SyncGCSDataSink.write` (line 290), and `orchestration_writer._write_candles_to_gcs` (line 413). All three
contain an identical `except (OSError, ValueError, RuntimeError, ...) → logger.error → return None` block wrapping a
`write_candle_parquet` call. Per CLAUDE.md "no double SSOT" + Phase 2.A consolidation target, these three write paths
should be consolidated into ONE canonical writer, with a single `record_failed` site at the leaf. Any fix to
write-failure manifest recording today must be applied in three places with diverging call signatures — known
maintenance trap. **Phase 2.A scope expansion**: include consolidation of these three write paths.

**HIGH severity (per-instrument or larger granularity silent drops, no manifest record)**:

| File:Line                          | Loop / context                                                      | Caught                                                          | What is swallowed                                                                                                                                                                                    | Fix shape                                                                                                                                                                             |
| ---------------------------------- | ------------------------------------------------------------------- | --------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `candle_processing_service.py:349` | `for timeframe in sorted_timeframes` per-(instrument_id, timeframe) | (ValueError, TypeError, KeyError, AttributeError, RuntimeError) | Entire per-instrument per-timeframe candle generation failure (`_generate_or_aggregate_candles` raised). No `record_failed`. Direct batch-path analogue of MTDS `PerLeafFailureRouter` gap.          | `record_failed(row_key=(instrument_id, timeframe, data_type, date_str), error=classify_venue_error(e), attempted_at=now())` before `continue`. Wire `ManifestWriter` into this class. |
| `candle_processing_service.py:591` | `for prefix in prefixes` per-(date_str, data_type) GCS listing      | (ValueError, TypeError, KeyError, AttributeError, RuntimeError) | GCS listing failure for an entire `(date_str, data_type)` prefix. Silently empty → entire date×data_type shard dropped. No manifest row.                                                             | Reader/infrastructure failure (Category C). `record_failed` at (date_str, data_type) granularity + `ADAPTER_FETCH_FAILED` event before `continue`.                                    |
| `candle_write_mixin.py:141`        | Per-instrument candle write (live orchestration)                    | (OSError, ValueError, RuntimeError, KeyError, TypeError)        | GCS write failure returns `None`. Caller at `live_workers.py:682` does NOT check return — unconditionally increments `total_candles`, appends to `processed_timeframes`. Failure looks like success. | Return-value check at every call site; on `None` `record_failed(...)` with typed `WriteFailedError`. Or consolidate into single canonical writer (preferred).                         |
| `data_sink.py:290`                 | `SyncGCSDataSink.write()` per-instrument (older batch path)         | (ValueError, TypeError, KeyError, AttributeError, RuntimeError) | GCS write failure returns `None`. Callers cannot distinguish success from failure. No `record_failed`.                                                                                               | Same — re-raise typed `WriteFailedError`; let shard-level caller record.                                                                                                              |
| `orchestration_writer.py:413`      | `_write_candles_to_gcs` per-instrument                              | (ValueError, TypeError, KeyError, AttributeError, RuntimeError) | GCS write failure returns `None`. Callers test `if result is None` for the **skip case** (existing file) — error case also returns `None`, indistinguishable.                                        | Same — distinguish skip vs error via typed return / sentinel; `record_failed` on error.                                                                                               |
| `output_writer_service.py:341`     | `OutputWriterService.write_candles` per-instrument                  | (OSError, ValueError)                                           | Same pattern — write fails, returns `None`, callers test for already-exists skip. No `record_failed`.                                                                                                | Same.                                                                                                                                                                                 |
| `live_workers.py:890`              | `_maybe_dispatch_chain_streaming` per chain blob                    | (OSError, ValueError, RuntimeError, KeyError, TypeError)        | Streaming dispatch fails for chain blob — returns `None`, caller falls through to **eager path** as fallback. If eager also fails, shard lost with no record.                                        | Acceptable as first-level fallback within same request. Outer caller must `record_failed` if eager path also produces no output.                                                      |

**MEDIUM severity (per-symbol/per-instrument drops inside aggregate, corrupts completeness)**:

| File:Line             | Loop / context                                                           | Caught                                                          | What is swallowed                                                                                                                                                                                                 | Fix shape                                                                                                                                                   |
| --------------------- | ------------------------------------------------------------------------ | --------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `live_workers.py:512` | `for group_value in groups` per-symbol slice in `_iter_chain_symbol_dfs` | (pl.exceptions.ComputeError, OSError, RuntimeError)             | Single symbol's Polars filter fails → silently dropped from chain output. For options_chain / futures_chain, downstream may write **partial-cluster parquet** with missing symbols and no `ClusterCoverageError`. | Per-symbol counter `dropped_symbols`, warn-summary after generator's `finally`. For bundled data_types, feed into cluster-coverage validator (Phase 2.B).   |
| `live_workers.py:773` | `for inst_key in instrument_keys` in `_process_chain_timeframe`          | `Exception` (bare)                                              | `classify_and_emit_error` is called (event emitted) but no per-symbol counter, no warn-summary. N instruments → M fail → M dropped with no aggregate accounting.                                                  | Add `dropped_count` counter + `logger.warning("Dropped %d/%d instruments for %s")` after loop (consistent with `solana_defi_handler.py` `7fedfe5` pattern). |
| `live_workers.py:835` | `for symbol in symbols` in `_process_chain_timeframe_by_symbol`          | `Exception` (bare)                                              | Same as line 773 but legacy-bundle `symbol`-keyed path.                                                                                                                                                           | Same fix.                                                                                                                                                   |
| `live_workers.py:490` | `_iter_chain_symbol_dfs` Polars lazy scan to enumerate groups            | (pl.exceptions.ColumnNotFoundError, pl.exceptions.ComputeError) | Failure to enumerate groups → bare `return` → generator exits yielding 0 symbols → entire chain bundle silently skipped. `ColumnNotFoundError` here is schema-drift bug (Category C).                             | `record_failed` at blob level + classify as Category C (schema drift), not silent skip.                                                                     |

**LOW severity** (13 sites — documented intentional path-probes / observability hooks / per-blob metadata isolation):

- `live_workers.py:158` and `:228` — D10 lifecycle/progress event emission; documented "must not raise from
  observability hook".
- `candle_processing_service.py:681` — `MarketAssetGroup(category)` enum coercion fallback to `None`; downstream handles
  `None` gracefully.
- `path_parsing.py:59,61` and `orchestration_scanner.py:307,367` — per-blob path-metadata parse error isolation;
  documented in module docstring.
- `orchestration_scanner.py:201` and `orchestration_scheduling.py:165` — `_load_instrument_definitions` fallback to
  `None` (no trading-hours filter); processing still runs.
- `market_state_detector.py:140` — `_parse_time_string` utility returns `None`.
- `canonical_writer.py:229` — `lookup_mdps_contract` fallback when `strict=False`; `strict=True` path re-raises.
- `live_workers.py:394` — Polars→pandas read fallback (acceptable I/O fallback; pandas raise propagates).
- `engine/mock_data_provider.py:205,243,262` — mock/dev path only.
- `cli/main.py:76` — pre-flight asset-group bucket env-var check; intentional "this category not configured on this VM".

**Top 5 priority fixes**:

1. **Write-path consolidation** (`candle_write_mixin.py:141` + `data_sink.py:290` + `orchestration_writer.py:413` +
   `output_writer_service.py:341`) — 4 sites, same root cause. Phase 2.A scope addition: single canonical writer with
   one `record_failed` site at the leaf.
2. **`candle_processing_service.py:349`** — batch-path counterpart of MTDS `PerLeafFailureRouter` gap. Highest-impact
   single site.
3. **`live_workers.py:512`** — per-symbol Polars filter failure in streaming chain path; for bundled data_types, this
   directly contradicts Phase 2.B cluster-coverage validation.
4. **`candle_processing_service.py:591`** — entire date×data_type prefix lost on GCS listing failure (HIGH — invisible
   in manifest).
5. **`live_workers.py:773` and `:835`** — per-symbol classify+emit but no aggregate warn-summary (MEDIUM, consistency
   with `7fedfe5` pattern).

**Implications for the master plan**:

- Phase 2.A scope expanded: not just `_create_empty_output` migration but also write-path consolidation (3 → 1) AND
  `candle_processing_service.py:349,591` `record_failed` wiring.
- Phase 2.B cluster-coverage validation gains a sibling concern: `live_workers.py:512`'s per-symbol drop must feed into
  the cluster validator OR the streaming path must short-circuit on first symbol failure.
- LOW sites left as-is (documented intentional patterns); add codex doc reference at `app/utils/path_parsing.py` for the
  5-site per-blob isolation pattern.

**Phase 2.A write-path consolidation pre-audit (2026-05-06 round 2)**:

Read-only callsite map for the 4 parallel write-path swallows. Critical finding: **3 of the 4 write-paths are ORPHANED
in production**.

| Path | Site                           | Production callsites | ManifestWriter access? | Status                                                             |
| ---- | ------------------------------ | -------------------- | ---------------------- | ------------------------------------------------------------------ |
| 1    | `candle_write_mixin.py:141`    | **3 active**         | None — must plumb      | **LIVE** — `live_workers.py:682,1061` + `batch_workers.py:164`     |
| 2    | `data_sink.py:290`             | **0**                | n/a                    | **ORPHANED** — `GCSDataSink.write_candles` has no production calls |
| 3    | `orchestration_writer.py:413`  | **0**                | n/a                    | **ORPHANED** — `_write_candles_to_gcs` is dead code                |
| 4    | `output_writer_service.py:341` | **0**                | n/a                    | **ORPHANED** — `OutputWriterService.write_candles` unwired         |

**Path 1 (CandleWriteMixin.\_write_candles) callers — all 3 ignore the return value**:

- `live_workers.py:682` (`_process_all_timeframes`) — return discarded; errors caught at outer try at line 721.
- `live_workers.py:1061` (`_write_chain_candles_concat`) — return discarded; errors appended to list at line 1074.
- `batch_workers.py:164` (`_write_closed_market_candles`) — bare call; outer try/except at line 214 catches if write
  raises (but the swallow blocks re-raising, so the failure is silent).

**Phase 2.A consolidation simplifies**: delete Paths 2/3/4 entirely (dead code removal aligns with the "no double
SSOT" + "delete deprecated code" rules); focus consolidation on Path 1's 3 callers. **Canonical writer is the leaf**:
`canonical_writer.py:41-47` already wraps `write_candle_parquet()` with `ManifestWriter.record_captured()` — Phase 2.A
plumbs `record_failed` alongside this so `canonical_writer.py` becomes the single failure-recording site.

**Caller-side fix required**: each of the 3 Path 1 callers must check the return value (or get the error via plumbed
`ManifestWriter` reference). The return-None ambiguity (None means "skipped, file existed" OR "swallowed error") must be
resolved via a typed return shape (`WriteResult` enum or `Result[str, WriteFailedError]` shape).

**Exception-set unification needed**: Path 1 catches `(OSError, ValueError, RuntimeError, KeyError, TypeError)` but the
orphans differ. Phase 2.A unifies to the broadest set and routes ALL caught exceptions through `classify_venue_error`.

### Phase 0 audit findings — MTDS bundle adapter inventory

**CRITICAL plan correction**: Phase 2.B file paths at lines 510-516 are wrong:

- `adapters/tardis/options_chain.py` — **does not exist**. Logic is in
  `market_interface/adapters/tradfi/tardis_adapter.py` (CeFi+TradFi paths) and
  `market_interface/adapters/cefi/tardis_shared.py` (shared helper).
- `adapters/databento/options_chain.py` — **does not exist**. Logic is in
  `market_interface/adapters/tradfi/databento_adapter.py` and `tradfi_shared.py`.
- `odds_snapshot_adapter.py` / `odds_movement_adapter.py` / `arbitrage_adapter.py` — **do not exist as separate files**.
  Implemented in `adapters/sports/odds_api_adapter.py` + `engine/orchestrator.py:_process_sports_venue_with_leagues()`.

**CRITICAL ARCHITECTURAL FINDING**: ZERO `record_captured` callsites for ANY MTDS bundle. All bundles flow through
`writer_manifest.add()` at `engine/orchestrator.py:1940`. The plan's Phase 1A guard (`MissingClusterValidationError`
raised inside `record_captured` when `data_type ∈ BUNDLED_DATA_TYPES`) **would never fire** because nothing calls
`record_captured`. **Phase 2.B wiring point at line 513 (adapters) is the wrong layer — must wire at
`orchestrator.py:1940` callsite OR refactor adapters to call `record_captured` directly.** Plan needs amendment.

| Adapter                              | data_type                                                                                                                                                                                                                         | Write site                                                                                                                                             | Cluster identity                                                                                                                               | `cluster_extractor` recipe                                                                                                                                      | Status                                                                             |
| ------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- | --- | ----------------------------------------------- | ------------------- |
| Tardis CeFi                          | `options_chain` (Tardis URL alias; canonical `instrument_type=options_chain`, `data_type=trades`)                                                                                                                                 | `tardis_adapter.py:870` `finalise_and_write_cefi_shards`                                                                                               | `underlying` (groupby key) — DERIBIT path additionally splits by `(underlying, quote_asset, margin_type)` for inverse/linear v6 disambiguation | `lambda row: row["underlying"]` — already present per row                                                                                                       | Wire `cluster_extractor` at orchestrator boundary                                  |
| Tardis CeFi                          | `futures_chain`                                                                                                                                                                                                                   | `tardis_adapter.py:1804` via `finalise_and_write_cefi_shards`                                                                                          | `underlying` per row; expiry-bucket NOT in row schema (front/back/spread cluster)                                                              | **Gap**: derive expiry_bucket from `symbol` parsing (`ESM6` → March 2026 → near-term). Need helper or new column                                                | Schema gap must be closed before cluster gate fires meaningfully                   |
| Tardis TradFi                        | `options_chain` (via `tradfi_shared.py:296` `_shard_instrument_type_for(OPTION) → options_chain`)                                                                                                                                 | `tradfi_shared.py:450` `write_tradfi_shard`                                                                                                            | `underlying` per row; ES.OPT 11-cluster prefix encoded in `symbol` (E1A/EW1/EOM etc.)                                                          | `lambda symbol: re.match(r'^(E[1-5]A                                                                                                                            | EW[1-4]                                                                            | EOM | ES)', symbol).group(0)` — confirmed extractable | Ready (regex-based) |
| Databento TradFi                     | `options_chain` (via `databento_adapter.py:91` `_PARTITION_INSTRUMENT_TYPE[OPTION]="options_chain"`)                                                                                                                              | `databento_adapter.py:822` `writer.write_chunk(df)` + `_enrich_with_canonical_ids()` at line 869                                                       | `underlying` set at `:981` from `cls.underlying`; weekly-series cluster (E1A/EW1/etc.) in `raw_symbol` prefix                                  | **Gap**: `DatabentoClassification` needs new `root_cluster: str` field. Currently only `underlying` is exposed; weekly-series prefix requires new pattern match | UAC change needed                                                                  |
| Databento TradFi                     | `futures_chain` (via `:90` `_PARTITION_INSTRUMENT_TYPE[FUTURE]="futures_chain"`)                                                                                                                                                  | Same `databento_adapter.py:822` path                                                                                                                   | `underlying` per row; expiry NOT exposed as column                                                                                             | **Gap**: same as Tardis futures_chain — derive from `raw_symbol`                                                                                                | Schema gap                                                                         |
| Sports `odds_api_adapter.py`         | **`ODDS_SNAPSHOT` / `ODDS_MOVEMENT` / `ARBITRAGE` data_type strings DO NOT EXIST in current code** — current live data_type = `"trades"` with `instrument_type="odds"`. Plan adds the new strings as part of per-fixture sharding | `orchestrator.py:1780` `instrument_type=odds/data_type=trades/ticks.parquet`; groups by `(bookmaker_key, league_id)` — **NO per-fixture grouping yet** | `bookmaker_key` per row (= `venue` after rename at line 1747)                                                                                  | `lambda row: row["bookmaker"]` — UAC `SPORTS_ODDS_SNAPSHOT` schema confirms `bookmaker` is the cluster identity                                                 | **Blocked**: per-fixture sharding (Phase 2.B line 520) must land first             |
| `polymarket_adapter.py` (prediction) | Current `"trades"`; future `prediction_canonical_question_group`                                                                                                                                                                  | `polymarket_adapter.py:590` `writer.write_chunk(df)`                                                                                                   | NO canonical_question_group column exists. Current grouping by `underlying` (BTC/ETH/etc.) is informal — written to `underlying` column only   | `lambda condition_id: PREDICTION_GROUPS[condition_id]` — but `PREDICTION_GROUPS = {}` empty                                                                     | **Blocked**: requires UAC canonical_question_group SSOT (Tracked Open Question §1) |
| `kalshi_adapter.py` (prediction)     | Same as Polymarket                                                                                                                                                                                                                | `kalshi_adapter.py:256` `df["data_type"] = "trades"`                                                                                                   | `instrument_type="prediction"` (note: inconsistency — Polymarket uses `"prediction_market"`)                                                   | Same blocker                                                                                                                                                    | Same blocker                                                                       |

**Cluster_extractor recipes (concrete)**:

- `options_chain` (Tardis CeFi): `lambda row: row["underlying"]` — direct column
- `options_chain` (TradFi Tardis): `lambda symbol: re.match(r'^(E[1-5]A|EW[1-4]|EOM|ES)', symbol.upper()).group(0)` —
  symbol-prefix regex
- `options_chain` (TradFi Databento): blocked on `DatabentoClassification.root_cluster: str` UAC enrichment
- `futures_chain` (both): blocked on `expiry_bucket` derivation from symbol parsing — needs new helper
- `ODDS_*` (sports): `lambda row: row["bookmaker"]` — but blocked on per-fixture sharding
- `prediction_canonical_question_group`: blocked on UAC SSOT

### Phase 0 audit findings — features-sports TABLE_TO_EXPORT inventory

**SURPRISE FINDING**: `_stamp_available_at` is **already implemented** in `cli/handlers/batch_handler.py:238-338`. Phase
2.C work is ~80% done in code I hadn't read this session. Three stamping buckets already wired:

- `fixtures` → `stamp_available_at_offset(kickoff_col="kickoff_utc", offset=-7d)` (line 278-280)
- `_POST_MATCH_TABLES` (5 tables) → `stamp_available_at_post_match(kickoff_col="kickoff_utc")` with `kickoff + 120min`
  fallback (lines 287-312)
- `_REFERENCE_TABLES` (8 tables) → `stamp_available_at_explicit(when=datetime.now(UTC))` (lines 319-320)

**`_FETCH_COMPLETED_AT` cache: does not exist.** Phase 2.C must build it from scratch. Current `datetime.now(UTC)` at
stamp time is architecturally safe (slightly pessimistic) — it's run-start, never read-time-derived.

**4 export STUBS surfaced** (silently writing empty parquets every batch run — distinct bug class from 1440-NaN, equally
opaque):

- `export_fixture_lineups()` — GCS data IS read (`_fetch_runner.py:171`) but discarded; no `_fetched_fixture_lineups`
  cache. Stub returns empty.
- `export_fixture_player_stats()` — same pattern; `player_stats` data read at `:173` but never stored.
- `export_coaches()` — no source fetch implemented.
- `export_rounds()` — no source fetch implemented.

**CRITICAL Phase 2.D blockers** (proposed schema bumps cannot be filled from current sources):

- **`announced_at`** for `fixtures`: NO source exposes fixture announcement timestamp. api_football, footystats,
  understat all return scheduled kickoffs without an `announced_at`. Current `kickoff - 7d` proxy is the maximum
  achievable precision. **Plan Phase 2.D `announced_at` column is unsourceable.**
- **`report_time` / `occurrence_time`** for `injuries`: API-Football `/injuries` endpoint returns `player`, `team`,
  `fixture`, `league`, `reason`, `type` — NO timestamp. The endpoint is a roster-availability snapshot for a given
  `date`. **Plan Phase 2.D injury timestamp work is blocked indefinitely** unless instruments-service builds a
  forward-poll-vs-backfill timestamp differentiation.
- **`match_end_time`** for `fixture_stats` / `fixture_player_stats`: NO source exposes this directly. api_football
  stores `status` string ("FT") but not the actual `elapsed` clock value at FT. The plan's match_end_time detection
  cascade (Phase 2.D bullet) hits a wall: requires instruments-service to store `fixture.status.elapsed` from API
  responses (it currently doesn't).
- **`event_time`** for `fixture_events`: derivable as `kickoff_utc + elapsed_min * 60s` (api_football provides
  `time.elapsed` integer in-game minute). Schema bump still useful but is a derivation, not native.

| Table                  | Current schema status                           | Phase 2.D readiness                                       | Risk                                                        |
| ---------------------- | ----------------------------------------------- | --------------------------------------------------------- | ----------------------------------------------------------- |
| `fixture_stats`        | 20 cols, no `match_end_time`                    | Stamped correctly today via `kickoff + 120min` fallback   | MEDIUM — `match_end_time` unsourceable                      |
| `fixture_events`       | 9 cols, no `event_time`                         | Derivable (`kickoff_utc + elapsed_min * 60s`)             | HIGH — needs schema bump + `kickoff_utc` join in normalizer |
| `fixture_lineups`      | 11 cols                                         | Stub not wired (data discarded at `_fetch_runner.py:171`) | CRITICAL — fix stub before Phase 2.D applies                |
| `fixture_player_stats` | 33 cols                                         | Stub not wired (data discarded at `:173`)                 | CRITICAL — fix stub before Phase 2.D applies                |
| `injuries`             | 6 cols, no `report_time`                        | UNSOURCEABLE from any current provider                    | HIGH — blocked indefinitely                                 |
| `players`              | 10 cols                                         | Already stamped via `datetime.now(UTC)`                   | LOW — `_FETCH_COMPLETED_AT` is precision improvement        |
| `venues`               | 8 cols, derived inline from fixtures            | Already stamped                                           | LOW                                                         |
| `fixtures`             | 23 cols, has `kickoff_utc` ✓, no `announced_at` | UNSOURCEABLE; `kickoff - 7d` proxy is best achievable     | MEDIUM — remove `announced_at` from Phase 2.D scope         |
| `leagues`              | 6 cols                                          | Already stamped                                           | LOW                                                         |
| `teams`                | 7 cols                                          | Already stamped                                           | LOW                                                         |
| `referees`             | 3 cols, derived inline                          | Already stamped                                           | LOW                                                         |
| `coaches`              | 5 cols                                          | Stub returns empty; no source fetch                       | LOW for stamping; HIGH for data quality                     |
| `standings`            | 15 cols                                         | Already stamped                                           | LOW                                                         |
| `rounds`               | 6 cols                                          | Stub returns empty; no source fetch                       | LOW for stamping; HIGH for data quality                     |

**Plan amendments needed**:

1. Drop `announced_at` from Phase 2.D (no source field). Keep `kickoff - 7d` proxy as documented synthesis.
2. Drop `report_time` / `occurrence_time` from Phase 2.D as immediately actionable; route to a separate plan that adds
   forward-poll vs backfill timestamp differentiation in instruments-service.
3. Drop `match_end_time` schema bump from Phase 2.D as immediately actionable; current `kickoff + 120min` fallback is
   the maximum without instruments-service exposing `fixture.status.elapsed`.
4. Keep `event_time` schema bump (derivable; useful for downstream readers).
5. Add 4 stub-wiring todos as Phase 2.C prerequisites: `fixture_lineups`, `fixture_player_stats`, `coaches`, `rounds`.

### Phase 0 audit findings — multi-source coverage matrix

**Most pairs are single-source** (no priority decision needed). The genuinely contested multi-source pairs:

| Pair                                      | Sources                                                                                             | Priority decision                                                                                                                                                                                                     |
| ----------------------------------------- | --------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `(cefi, trades)` HYPERLIQUID-specific     | Tardis (returns `[]` for HL) vs Hyperliquid S3 (≥2025-03-22) + REST                                 | **Hyperliquid S3 wins** on coverage + timestamp-availability. Already routed at `umi_tick_provider.py` HYPERLIQUID branch before Tardis check.                                                                        |
| `(tradfi, ohlcv_15m)` CBOE VIX            | Barchart CSV (2020-01-02 → 2025-11-12) + Yahoo Finance (rolling 60d) + GAP (2025-11-13 → today−60d) | **Temporal layering, not tie-break.** `data_source_continuity.py:get_vix_15m_source()` is the SSOT. Recommend `["barchart_csv", "yahoo_finance"]` with note that date-based dispatch governs.                         |
| `(sports, ODDS)`                          | footystats (backfill, 46 leagues, ≥2019) + odds_api (live, 33 prediction leagues, ≥2020-06-06)      | **odds_api priority-1** for live + 33 prediction leagues; footystats priority-2 for 13 additional leagues + pre-2020-06 history. Recommend `["odds_api", "footystats"]`.                                              |
| `(sports, STANDINGS)`                     | api_football (entity=standings) vs footystats (per `SPORTS_DATA_TYPE_TO_SOURCE`)                    | **AMBIGUOUS — needs runtime verification.** SSOT (`league_data.py:133`) maps to footystats but adapter dependency doc shows api_football also writes. If both write, api_football wins on breadth (95 vs 46 leagues). |
| `(prediction, trades)`                    | POLYMARKET (live WS) vs KALSHI (no US account)                                                      | **POLYMARKET priority-1** on all tie-breakers; KALSHI priority-2 contingent on account setup.                                                                                                                         |
| `(sports, FIXTURE_STATS)`                 | api_football (detailed: xG, duels, passes) vs footystats MATCHES (aggregated)                       | **api_football priority-1** on info-richness; footystats is merge-different-fields candidate (deferred).                                                                                                              |
| `(cefi, derivative_ticker)` live vs batch | Direct WS (live, all venues) vs Tardis (batch)                                                      | **Live=batch source split**: WS for live pipeline, Tardis for batch backfill. `SOURCE_PRIORITY` should encode `["direct_ws_<venue>", "tardis"]`.                                                                      |
| `(defi, lending_indices)`                 | The Graph (AaveV3) + Morpho REST (Morpho protocol)                                                  | **Non-overlapping protocols** — merge-different-protocols, not tie-break. Encode as `["the_graph", "morpho_blue_api"]`.                                                                                               |

**Migration-target pairs** (current source not optimal):

- `(tradfi, trades/ohlcv_1m/tbbo)`: Polygon.io declared in capability but not wired; would enable `live_capable=True`
  for tradfi.
- `(tradfi, ohlcv_24h)`: ECB declared but not wired; more authoritative for FX than Yahoo.
- `(defi, gas_fees)`: Etherscan-via-catalog vs Alchemy (key already in SM); Alchemy `eth_feeHistory` is more granular
  and reuses existing key.

**merge-different-fields opportunities** (deferred to multi-source merge plan):

- `(sports, FIXTURE_EVENTS + XG)`: api_football scaffold + understat per-shot xG join by `(fixture_id, player, minute)`.
- `(sports, FIXTURE_STATS + MATCHES)`: api_football granular + footystats derived (ELO, ppg).
- `(prediction, prediction_trades)`: POLYMARKET (crypto/sports) + KALSHI (US macro/regulatory) — non-overlapping
  domains.

**SOURCE_PRIORITY seeding for Phase 1B**:

- ~85% of pairs: single-element list (document the monopoly).
- 6-8 contested pairs (above): explicit `[priority1, priority2]` lists.
- Sports/ODDS, tradfi/ohlcv_15m: encode temporal/league-tier routing in module docstring; Phase 1B writes top entry
  only.

---

## Phase 1A — UTL contract changes (sequential, blocks all)

- [x] [SCRIPT] P0. Add 3 new typed errors to `unified_trading_library/errors.py`: -
      `UpstreamTimestampBiasError(observed_date_range: tuple[date, date], expected_day: date, n_ticks_seen: int, instrument_id: str | None = None)`
      — path B -
      `MalformedTickFieldError(field: str, n_dropped: int, sample_values: list[Any] = None, instrument_id: str | None = None)`
      — path C - `MissingClusterValidationError(data_type: str, expected_registry_key: str)` — record_captured guard
- [x] [SCRIPT] P0. `manifest_writer.py:1163` `record_captured` signature change: - Add
      `expected_root_clusters: Mapping[str, int] | None = None` - Add
      `cluster_extractor: Callable[[str], str] | None = None` - Add `symbol_column: str = "symbol"` (currently in
      helper) - Inside `record_captured`: if `data_type in BUNDLED_DATA_TYPES` (imported from UAC) and
      `expected_root_clusters is None` → raise
      `MissingClusterValidationError(data_type, DATA_TYPE_TO_CLUSTER_REGISTRY.get(data_type))`. - When kwargs present:
      call `_check_cluster_coverage` internally; on `ClusterCoverageError` return → call `record_failed(...)` instead of
      writing the parquet.
- [x] [SCRIPT] P0. `manifest_writer.py:1098` rename `check_cluster_coverage` → `_check_cluster_coverage`. Remove from
      `__all__`. Internal-only.
- [ ] [SCRIPT] P0. `availability_stamping.py` extend with: -
      `stamp_available_at_kickoff_offset(df, kickoff_col="kickoff_utc", minutes=60)` — for lineups -
      `stamp_available_at_post_match(df, kickoff_col="kickoff_utc", duration_min=120, scrape_latency_min=15)` — for
      fixture_stats / fixture_player_stats - `stamp_available_at_event_time(df, event_time_col="event_time")` — per-row
      pass-through, used for fixture_events + injuries (when row has its own time) -
      `stamp_available_at_announcement(df, announced_col="announced_at")` — for fixtures -
      `stamp_available_at_explicit(df, fetch_completed_at: datetime)` — for 8 reference tables
- [x] [SCRIPT] P0. New UTL helper `manifest_writer.assert_available_at_present(df: pd.DataFrame)` — raises
      `LookaheadBiasError` (existing) if `available_at` column missing or contains NaN. Called automatically from
      `record_captured` when not in cluster path.
- [x] [TEST] P0. UTL unit tests: - `record_captured` raises `MissingClusterValidationError` for every entry in
      `BUNDLED_DATA_TYPES` when kwarg not passed. - `record_captured` succeeds + writes when kwargs passed and clusters
      complete. - `record_captured` calls `record_failed` (no parquet write) when clusters incomplete. -
      `record_captured` calls `assert_available_at_present` and raises `LookaheadBiasError` on missing/null
      `available_at`. - `record_empty` accepts `attempted_at` + writes manifest row only. - `record_failed` accepts each
      new typed error variant + writes appropriate `error_reason`.
- [ ] [QG] P0. Add UTL `quality-gates.sh` step that fails if `_create_empty_output`-style placeholder return patterns
      are reintroduced (grep-based static check; can be fooled but catches the obvious).
- [ ] [DEP] P0. Bump UTL version (semver-agent handles; do NOT bump manually) on merge.

QG between Phase 1A and Phase 2: UTL tests green; UTL pushed to live-defi-rollout; downstream consumers rebuild against
new UTL pinned in workspace-manifest.json.

---

## Phase 1B — UAC SSOTs (parallel with 1A)

> **2026-05-06 progress note**: Phase 0 audit discovered that `ES_OPTIONS_CLUSTERS` (11-cluster taxonomy),
> `extract_es_options_cluster`, and `get_active_es_options_clusters_for_date` (calendar fallback) **already exist** in
> UAC `unified_api_contracts/registry/tradfi_symbology.py:539` — earlier than this plan assumed. The "lift from
> instruments-service" step is therefore a delete-and-delegate: instruments-service
> `reference_data/options_cluster_lookup.py` consumers re-import from UAC; no new SSOT needed for ES.OPT itself.
> **Already-shipped (UAC commit `31e9e75` 2026-05-06)**:
> `unified_api_contracts/canonical/crosscutting/honest_coverage.py` with `BUNDLED_DATA_TYPES` (frozenset of 4 —
> options_chain, futures_chain, prediction_canonical_question_group, sports_fixture_bundle), `futures_expiry_bucket()`
> derivation (front/back/spread/unknown bucketing for futures_chain bundle cluster_extractor — closes the row-schema gap
> noted in row 583 of the cluster wiring matrix), `FUTURES_CHAIN_BUCKETS` constant, plus re-export surface delegating to
> the registry SSOT. 30 unit tests cover BUNDLED_DATA_TYPES membership, parametric front/back/spread bucketing, custom
> front-window override, and re-export delegation regression. **Remaining Phase 1B work**:
> `DATA_TYPE_TO_CLUSTER_REGISTRY`, `SPORTS_FIXTURE_CLUSTERS` greenfield seeds, `PREDICTION_GROUPS = {}` placeholder
> slot, source_priority + availability_semantics modules.
>
> **2026-05-06 progress note (round 2)**: UAC commit `106430c` adds the remaining two crosscutting modules —
> `canonical/crosscutting/availability_semantics.py` (36 seed entries; 10-mode `AvailabilitySemantic` literal covering
> kickoff_minus_60min / match_end_time / event_time / report_time / announced_at / forecast_issue_time /
> publication_time / fetch_completed_at / tick_timestamp / market_created_at; raises `KeyError` on unregistered pairs —
> no silent default, failing loud is intentional) and `canonical/crosscutting/source_priority.py` (single-source Phase
> 1B seeds with `get_primary_source` convenience helper for stamping callers; multi-source merge logic deferred to
> follow-up). 38 new tests (18 + 20), total 68 with honest_coverage. Cross-module consistency check validates every
> `(asset_group, data_type)` pair appears in BOTH registries (stamping helpers can't compute `available_at` without a
> source priority entry). **Phase 1B status**: 3 of 4 crosscutting modules shipped. Remaining:
> `DATA_TYPE_TO_CLUSTER_REGISTRY` mapping (data_type → cluster registry symbol reference), `SPORTS_FIXTURE_CLUSTERS`
> greenfield seed (per-league-tier bookmaker sets), and `PREDICTION_GROUPS = {}` placeholder slot (gets populated by
> Plan A canonical_question_group SSOT — flagged in temporary-states section).

- [x] [SCRIPT] P0. New module `unified_api_contracts/canonical/crosscutting/honest_coverage.py`: -
      `BUNDLED_DATA_TYPES: frozenset[str]` initial seed: - `"options_chain"` — registry: `OPTIONS_CLUSTERS` (populated,
      lifted from instruments-service ES.OPT 11-cluster taxonomy; per-root entries) - `"futures_chain"` — registry:
      `FUTURES_CLUSTERS` (greenfield; ES + MES seeds; expand per-root in this plan) - `"ODDS_SNAPSHOT"`,
      `"ODDS_MOVEMENT"`, `"ARBITRAGE"` — registry: `SPORTS_FIXTURE_CLUSTERS` (greenfield; per-(league-tier → bookmaker
      set); seed tier-1 EU football here, expand per-tier in this plan + follow-up) -
      `"prediction_canonical_question_group"` — registry: `PREDICTION_GROUPS = {}` **EMPTY temporary state**. Slot
      reserved + cluster guard wired. NO caller currently uses this data*type (Polymarket shards per-`base_asset` per
      current audit). When canonical_question_group SSOT lands in
      `prediction_canonical_question_group_uac_ssot_2026*<TBD>.plan.md`, registry gets populated AND Polymarket migrates AND cluster guard fires meaningfully. Documented in §"Temporary states + their canonical follow-up plans".     - `DATA_TYPE_TO_CLUSTER_REGISTRY:
      dict[str,
      str]`(data_type → registry symbol name).     -`OPTIONS_CLUSTERS`lifted from instruments-service (ES.OPT 11-cluster taxonomy as seed; per-root entries).     -`FUTURES_CLUSTERS`(greenfield; ES + MES seeds; spreads + butterflies per root).     -`SPORTS_FIXTURE_CLUSTERS` (greenfield; per-`league_tier`→ expected bookmaker set; tier-1 EU football seed; tier-2 / tier-3 expansion in this plan or follow-up).     -`PREDICTION_GROUPS
      = {}` (empty placeholder; gets populated by canonical_question_group SSOT plan).
- [x] [SCRIPT] P0. New module `unified_api_contracts/canonical/crosscutting/source_priority.py`: - `SourcePriority` enum
      or dataclass per `(asset_group, data_type)`. - `SOURCE_PRIORITY: dict[tuple[str, str], list[str]]` — ordered list
      of source keys, top entry is primary. - Tie-breaker rules documented in module docstring (timestamp-availability >
      coverage > info-richness > merge-different-fields). - Phase 1B seeds the dict for sports data_types (lineups,
      fixture_events, injuries) with single-source entries; multi-source merge logic deferred.
- [x] [SCRIPT] P0. New module `unified_api_contracts/canonical/crosscutting/availability_semantics.py`: -
      `AvailabilitySemantic = Literal["fetch_completed_at", "kickoff_minus_60min", "match_end_time", "event_time", "report_time", "announced_at", "forecast_issue_time", "publication_time"]` -
      `AVAILABILITY_AT_SEMANTICS: dict[tuple[str, str], AvailabilitySemantic]` — per-(asset_group, data_type) stamping
      rule. - Sports seeds: `("sports", "FIXTURES")` → `announced_at`; `("sports", "FIXTURE_LINEUPS")` →
      `kickoff_minus_60min`; `("sports", "FIXTURE_EVENTS")` → `event_time`; `("sports", "INJURIES")` → `report_time`;
      `("sports", "FIXTURE_STATS"|"FIXTURE_PLAYER_STATS")` → `match_end_time`; reference tables →
      `fetch_completed_at`. - CeFi / DeFi / TradFi / prediction seeds: TBD per Phase 0 audit (most are fetch-time /
      event-time straightforward).
- [ ] [SCRIPT] P0. Lift instruments-service ES.OPT cluster lookup (`reference_data/options_cluster_lookup.py`) to UAC
      `OPTIONS_CLUSTERS` registry. Delete the instruments-service module; update consumers.
- [x] [TEST] P0. UAC unit tests: - Every entry in `BUNDLED_DATA_TYPES` has a corresponding entry in
      `DATA_TYPE_TO_CLUSTER_REGISTRY`. - Every registry symbol referenced in `DATA_TYPE_TO_CLUSTER_REGISTRY` resolves to
      a non-empty dict. - Every `(asset_group, data_type)` shipped by any service has an entry in
      `AVAILABILITY_AT_SEMANTICS` (parametrise over service registries). - Every multi-source `(asset_group, data_type)`
      has an entry in `SOURCE_PRIORITY`.

QG between Phase 1B and Phase 2: UAC tests green; UAC pushed; consumer-pin propagates.

---

## Phase 1C — Workspace CLAUDE.md rule additions (parallel with 1A/1B)

- [x] [DOCS] P0. Add to `unified-trading-pm/cursor-configs/CLAUDE.md` (between "No fire-and-forget VM launches" and
      "Sports GCS path SSOT", or wherever fits):

      **§ "Live = batch — same data, different sources"**
      Live and batch are operational modes of the SAME pipeline. They produce identical schemas + identical `data_types` + identical fields. They differ only in WHICH source serves a given `(asset_group, data_type)`, because some sources lag others on real-time emission. Historical writes MUST be timestamped with the `available_at` we'd actually have in live mode (the source priority registry's top entry's emission time, not the canonical historical source's slower archive time). Applies to every asset_group; canonical example: sports injuries — historical source may give report_time post-match, but live pipeline scrapes a faster source mid-match; historical writes stamp with the live-pipeline-equivalent time, NOT the historical-source post-match time.

      **§ "Three-category empty-output decision (MDPS + every per-shard adapter)"**
      Every condition producing an empty result resolves to ONE of: A (source returned 0 ticks → `record_empty`), B (ticks present, all outside requested day → `record_failed(UpstreamTimestampBiasError)` + paired upstream MTDS partitioner fix), C (ticks in window, downstream calc dropped due to malformed fields → `record_failed(MalformedTickFieldError)`). No fourth category. No silent NaN placeholder rows. `_create_empty_output()`-style methods are banned; `base_adapter` does not provide one.

      **§ "Cluster validation mandatory at record_captured"**
      For any `data_type ∈ UAC.BUNDLED_DATA_TYPES`, `record_captured` requires `expected_root_clusters` + `cluster_extractor` kwargs. UTL guard raises `MissingClusterValidationError` if absent. QG STEP 5.64 statically walks every `record_captured(` callsite + asserts the kwargs are passed when the literal data_type is bundled. Runtime + static enforcement; no opt-out.

      **§ "`available_at` is per-row, write-time, equal to live-pipeline-arrival"**
      Every shard's parquet contains an `available_at` column. Each row's value = when the live pipeline would have actually had that row's information (per `UAC.AVAILABILITY_AT_SEMANTICS`). For multi-source data_types, the `UAC.SOURCE_PRIORITY` top entry determines the source whose timing is used. NEVER derived at read-time. Stamping helpers: `unified_trading_library.availability_stamping.stamp_available_at_*`. UTL's `record_captured` calls `assert_available_at_present` internally.

- [ ] [DOCS] P0. Update existing CLAUDE.md "Honest absence vs fake placeholders" section with explicit cross-link to the
      three-category decision; rewrite the "Reader/schema-drift bug" sub-bullet to call out path B (timestamp bias) as a
      distinct sub-class.
- [ ] [DOCS] P0. Update `unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md` to inherit the new sections
      (it's a per-repo synced file).
- [ ] [SCRIPT] P0. Run `bash unified-trading-pm/scripts/propagation/sync-claude-md-to-all-repos.sh` (or the equivalent)
      so per-repo `CLAUDE.md` mirrors pick up the new sections.

QG between Phase 1C and Phase 2: every per-repo `.claude/CLAUDE.md` (or symlink) contains the new sections; validated by
grep.

---

## Phase 2 — Service forward fixes (parallel after 1A+1B+1C)

### Phase 2.A — MDPS forward fixes (delete `_create_empty_output`)

- [ ] [SCRIPT] P0. Delete `_create_empty_output` from `app/adapters/base_adapter.py`. Replace with a private helper
      `_classify_empty_path(tick_data, day_start, day_end) -> Literal["A", "B", "C"]` plus typed exceptions
      `EmptyAfterFilterError` (path A — adapter raises, orchestrator catches → `record_empty`),
      `UpstreamTimestampBiasError` (path B — propagates from UTL), `MalformedTickFieldError` (path C — propagates from
      UTL).
- [ ] [SCRIPT] P0. For each of the 37 callsites (16 A / 15 B / 5 C / 2 ambiguous per Phase 0 audit): convert
      `return self._create_empty_output(...)` to `raise <appropriate>` per the Phase 0 A/B/C manifest. Code owner
      sign-off per adapter file. **Special cases**: - 5 NEW Path C sites in `fx_rate_adapter` (added to scope by Phase 0
      audit; were not in original 53 estimate). - `tradfi/ohlcv_passthrough.py:89` — flagged AMBIGUOUS by audit; may be
      INTENTIONAL when `venue_trading_calendar` pre-skip already excludes the date. Verify at runtime: if pre-skip is
      reliable, convert to path A; if not, treat as path C with `MalformedTickFieldError`.
- [ ] [SCRIPT] P0. Update `_handle_empty_tick_data` in `batch_workers.py` + `live_workers.py` to catch all three
      exceptions + route to `record_empty` (path A) / `record_failed(UpstreamTimestampBiasError)` (path B) /
      `record_failed(MalformedTickFieldError)` (path C).
- [ ] [SCRIPT] P0. **Phase 2.A scope expansion (Phase 0 audit finding 2026-05-06)**: fix prediction empty path silent
      drop. At `live_workers.py:268-271` + `batch_workers.py:199-228`, the prediction asset_group fall-through returns
      `success=True, candles_generated=0` with NO manifest record. Add
      `record_empty(row_key=<full v6 key including     canonical_question_group + market_id>, attempted_at=<now>)` call
      so prediction empties surface in the manifest as honest absence. Coordinate row_key shape with Plan A predictions
      (canonical_question_group + market_id columns land via that plan). Until Plan A lands, use a placeholder row_key
      with current Polymarket per-base_asset shape; reconciler script (Phase 3.A new entry) re-flips these rows once
      Plan A migrates the shape.
- [ ] [SCRIPT] P0. Delete `_write_manifest_records` v3-shape parallel write from `orchestration_service.py:329–388`.
      Single canonical v6 path via `canonical_writer` only. (Resolves parent HANDOVER §"❌ MDPS mismatches" item.)
- [ ] [SCRIPT] P0. Wire v6 columns (`quote_asset` / `margin_type` / `combo_type` / `leg_weights`) into
      `canonical_writer.add()` per the explicit decision rule below — no UAC-owner blocking dependency: **Wire (row
      carries v6-relevant info):** - CeFi: `derivative_adapter`, `futures_chain_adapter`, `options_chain_adapter` —
      populate `quote_asset` from instrument metadata (`USD` / `USDT` / `USDC` / `BTC` etc.) + `margin_type` (`linear` /
      `inverse` / `quanto`). DERIBIT inverse vs linear is the canonical disambiguation case — without these columns,
      manifest row-keys collide. - CeFi `book_snapshot_adapter`, `liquidations_adapter`, `trades_adapter` — populate
      `quote_asset` + `margin_type` (same source as above). - TradFi `futures_chain_adapter` — populate `combo_type`
      (`outright` / `spread` / `butterfly` / `condor`) + `leg_weights` (legs JSON list); ES.OPT spreads are the
      canonical case. - TradFi `options_chain_adapter` — populate `combo_type` (`single` / `vertical` / `straddle` /
      etc.) + `leg_weights`. **Skip (leave at default `""`):** - All DeFi adapters (`swap_adapter`, `liquidity_adapter`,
      `market_state_adapter`, etc.) — DEX spot has no margin_type; quote_asset is the second leg of the pool which is
      the data_type axis already. - All sports adapters — irrelevant. - All prediction adapters — irrelevant. Phase 5
      verification todo: UAC owner confirms the wired set matches the v6 schema spec; flag any data_type whose row
      carries v6-relevant info we missed.
- [ ] [SCRIPT] P0. Add missing data_types to `_CEFI_TRADFI_DEFI_DATA_TYPES` in `orchestration_scanner.py:46–72`
      (`dex_pool_swaps`, `evm_defi_lending`, `evm_defi_amm`, `staking_yields`).
- [ ] [SCRIPT] P0. Fix adapter registry imports — add `liquidity`, `market_state`, `fx_rates` to
      `app/adapters/__init__.py` so decorators fire.
- [ ] [SCRIPT] P0. Wire `expected_root_clusters` + `cluster_extractor` into MDPS chain-bundle write paths
      (futures_chain, options_chain). Use UAC `DATA_TYPE_TO_CLUSTER_REGISTRY` to look up the registry per data_type.
- [ ] [TEST] P0. Per-adapter integration test: simulate path A / path B / path C; assert correct manifest verb fires;
      assert NO 1440-row NaN parquet ever lands on disk.
- [ ] [TEST] P0. End-to-end smoke: pick 1 venue × 1 instrument × 1 day across each asset_group; run MDPS; assert
      manifest reflects honest verb; spot-check 1 parquet per data_type; assert OHLC populated where claimed `captured`.
- [ ] [QG] P0. MDPS quality-gates.sh green.

### Phase 2.B — MTDS partitioner validation + cluster wiring

- [ ] [SCRIPT] P0. Add write-time partition-key validation to `raw_tick_hive.py`: assert
      `tick.timestamp.date() == day_partition_key` before writing each tick. On mismatch: log + emit
      `RAW_TICK_PARTITION_MISMATCH` event + reject the tick (do NOT write to GCS). Per-instrument shard-level isolation;
      one instrument's mismatch doesn't kill the venue run.
- [ ] [SCRIPT] P0. Wire `expected_root_clusters` + `cluster_extractor` into every MTDS bundle write site (paths
      corrected per audit 2026-05-06 amendment A — original plan listed non-existent files): -
      `market_interface/adapters/tradfi/tardis_adapter.py:870` `finalise_and_write_cefi_shards()` (Tardis CeFi
      options_chain + futures_chain bundle write; cluster = `underlying` per row, also splits by
      `(underlying, quote_asset, margin_type)` for DERIBIT inverse/linear v6 disambiguation) + `tardis_adapter.py:1804`
      (TradFi futures_chain via same shared helper). - `market_interface/adapters/tradfi/tradfi_shared.py:423`
      `write_tradfi_shard()` (TradFi options_chain final upload; cluster_extractor:
      `lambda symbol: re.match(r'^(E[1-5]A|EW[1-4]|EOM|ES)', symbol.upper()).group(0)` for ES.OPT 11-cluster
      taxonomy). - `market_interface/adapters/tradfi/databento_adapter.py:822` `writer.write_chunk(df)` (Databento
      TradFi options/futures bundle; cluster from `cls.underlying` set at line 981 — but Databento weekly-series cluster
      E1A/EW1/etc. is in `raw_symbol` prefix, NOT exposed as a named field). **Gap**: requires UAC-side
      `DatabentoClassification.root_cluster: str` enrichment — see todo immediately below. - `polymarket_adapter.py`
      (uses `prediction_canonical_question_group` once Plan A predictions lands — for now, pass an empty registry →
      cluster gate is a no-op, slot reserved per Plan A). **CRITICAL ROUTING FINDING from audit 2026-05-06 (amendment F,
      escalated to Ikenna by harsh's `72ebe7a6`)**: ALL MTDS bundles flow through `writer_manifest.add()` at
      `engine/orchestrator.py:1940`, NOT through `record_captured`. Phase 1A's `MissingClusterValidationError` guard
      would never fire at the adapter layer. Two resolution options (pick by Ikenna): - **Option α (Claude recommends —
      single SSOT)**: refactor `engine/orchestrator.py:1940` callsite to use `record_captured` instead of
      `writer_manifest.add()`; pass `expected_root_clusters` + `cluster_extractor` per `data_type` lookup in UAC
      `DATA_TYPE_TO_CLUSTER_REGISTRY`. Single change site, all bundles benefit, cluster guard fires correctly. -
      **Option β**: refactor each bundle adapter to call `record_captured` directly instead of
      `writer.write_chunk(df) + writer_manifest.add()`. More callsites, more code review, but keeps adapter-level write
      atomicity. **Do NOT execute this Phase 2.B todo until amendment F is resolved by Ikenna.**
- [ ] [SCRIPT] P0. **UAC enrichment: `DatabentoClassification.root_cluster: str` field** (Phase 0 audit gap finding —
      lifted from "deferred follow-up plan" to in-scope Phase 2.B todo per workspace rule that no temporary state ships
      without a named successor; rather than naming a successor we just do it here). Databento TradFi options_chain
      bundles need a `root_cluster` for weekly-series cluster extraction (E1A / EW1 / EOM / etc.). Currently
      `DatabentoClassification` exposes `underlying` only; weekly-series prefix from `raw_symbol` requires a new pattern
      match. Add the field + pattern parser in UAC; populate at MTDS write time. Without this, ES.OPT 11-cluster
      taxonomy can't validate Databento-fed days against Tardis-fed days at the cluster level.
- [ ] [SCRIPT] P0. **Futures expiry_bucket helper for cluster validation** (Phase 0 audit gap finding — same lift
      pattern as `DatabentoClassification.root_cluster`). Tardis + Databento `futures_chain` bundles have `underlying`
      per row but expiry_bucket (front / back / spread / butterfly) is NOT a column — it must be derived from
      `raw_symbol` (e.g. `ESM6` → March 2026 → near-term front). New helper
      `unified_api_contracts.canonical.domain.futures.derive_expiry_bucket(symbol: str, today: date) -> str` OR a new
      `expiry_bucket` column populated at MTDS write time. Schema gap closes before cluster gate fires meaningfully.
- [ ] [SCRIPT] P0. `umi_tick_provider.py:225` — replace `category="prediction_market"` with `asset_group=...` per
      workspace vocabulary.
- [ ] [SCRIPT] P0. **Sports per-fixture_id shard granularity (in-scope, NOT deferred — confirmed 2026-05-06).**
      `orchestrator.py:1739` currently groups by `(bookmaker, league)` only; expand to full v5/v6 spec
      `(asset_group=sports, source, data_type, league_id, fixture_id|day-aggregate, day)`. Per-fixture data_types
      (`ODDS_SNAPSHOT`, `ODDS_MOVEMENT`, `ARBITRAGE`, `FIXTURE_STATS`, `FIXTURE_EVENTS`, `FIXTURE_LINEUPS`,
      `FIXTURE_PLAYER_STATS`, `INJURIES` when fixture-scoped) shard at fixture_id; aggregate data_types (`STANDINGS`,
      `LEAGUES`, `TEAMS`, etc.) shard at day-aggregate. Reasoning: the entire sports ML stack predicts at fixture-level
      — without per-fixture sharding, can't drill down on missing fixtures or fixture-specific stats. League stays as a
      higher-level rollup grouping for data-status panel filtering, NOT as the shard atom.

      **Break-fix scope (anything that breaks because of this change is fixed in this plan):**
      - **MTDS reader paths** — wherever a reader keys on `(venue, data_type, date)` for sports, expand the lookup to include `fixture_id` (where applicable). Audit + fix in Phase 0.
      - **MDPS sports adapter** — if it consumes MTDS sports parquets keyed by `(bookmaker, league)`, update to read per-fixture parquets and aggregate up if needed.
      - **features-sports input pipeline** — `mtds_canonical_reader` and similar must read per-fixture; verify per-(asset_group, data_type) reader granularity matches the new writer granularity.
      - **deployment-ui data-status panel** — sports panel surfaces league + proficiency rollups (drill-down view), but the underlying shard atom is now per-fixture. UI rolls up per-league for filter view + per-fixture for drill-down. Explicitly: `(league_id) → (fixture_id) → (data_type) → leaf_parquet` drill-down path. Phase 4.B picks this up.
      - **Manifest reconciliation** — existing manifest rows with `(bookmaker, league)` shard keys flip to a new shape; reconciler script in Phase 3.A handles the migration: read old parquet, split per-fixture, write new parquets, mark old `attempted_failed[reason=ShardSchemaMigrated]` for re-attempt under new contract.

- [ ] [SCRIPT] P0. **Sports `BUNDLED_DATA_TYPES` registry seeding** (couples to per-fixture sharding above). Per-fixture
      data_types that aggregate multiple bookmakers/sub-rows in one shard's parquet → `BUNDLED_DATA_TYPES`-eligible.
      Concrete entries: - `ODDS_SNAPSHOT` / `ODDS_MOVEMENT` / `ARBITRAGE` — cluster_extractor: `bookmaker`.
      `SPORTS_FIXTURE_CLUSTERS = {tier_1: {pinnacle, bet365, ...}, tier_2: {...}}` per league-tier (UAC seeds tier-1 EU
      football tier list; expand per follow-up). - `FIXTURE_STATS` / `FIXTURE_PLAYER_STATS` from a single source —
      typically NOT bundled (one row per fixture or per (fixture, player)) unless multi-source merge is enabled
      (deferred to multi-source merge plan). `sports_fixture_bundle` in `BUNDLED_DATA_TYPES` is a logical category; the
      actual `data_type` strings registered are the per-data_type entries above (`ODDS_SNAPSHOT`, etc.). Update Phase 1B
      `BUNDLED_DATA_TYPES` seed to include those concrete data_type names.
- [ ] [SCRIPT] P0. GMX multi-chain — `perp_funding_handler.py:225` currently writes `chain=""`; emit per-chain Tier-2
      fan-out per HANDOVER follow-up note.
- [ ] [SCRIPT] P0. Skip-if-exists granularity — `tick_data_handler.py:166` currently calls `check_shard_freshness` at
      `(venue, data_type, date)`; tighten to full v6 key including `quote_asset` + `margin_type` to avoid DERIBIT
      inverse/linear suppression bug.
- [ ] [SCRIPT] P0. DeFi venue-split rationalisation — `orchestrator.py:1880–1908` hardcoded 27-protocol tuple; replace
      with `_VENUE_MAPPING.all_defi_venues` lookup (single SSOT).
- [ ] [TEST] P0. MTDS unit test: feed a tick with `timestamp.date() != day_key` → assert rejection + event emission.
- [ ] [TEST] P0. MTDS bundle adapter test: feed a partial bundle (8 of 11 ES.OPT clusters) → assert
      `record_failed(ClusterCoverageError)` fires + no parquet written.
- [ ] [QG] P0. MTDS quality-gates.sh green.

### Phase 2.C — features-sports forward fixes

**Audit 2026-05-06 update** (amendment E + audit #0.4 findings):

- `_stamp_available_at` already implemented in `cli/handlers/batch_handler.py:238-338` (~80% of original Phase 2.C work
  done in code we hadn't read). 3 stamping buckets wired: `fixtures` (`kickoff−7d`), 5 post-match tables
  (`stamp_available_at_post_match` with `kickoff+120min` fallback), 8 reference tables (`datetime.now(UTC)`).
- `_FETCH_COMPLETED_AT` cache does NOT exist; Phase 2.C builds it from scratch.
- 4 export STUBS surfaced — must be wired BEFORE per-table `available_at` work makes sense (otherwise the new stamping
  rules write `available_at` onto perpetually-empty parquets).
- Per-table stamping rules below are amended to reflect amendments B/C/D — `announced_at` / `report_time` /
  `match_end_time` columns dropped from Phase 2.D scope; we keep proxy-based stamping until follow-up plans add
  upstream-source enrichment.

#### Phase 2.C prerequisites — wire export stubs (amendment E)

- [ ] [SCRIPT] P0. **Wire `fixture_lineups` stub.** `_fetch_runner.py:171` reads GCS lineup data but **discards it** (no
      `_fetched_fixture_lineups` cache). `export_fixture_lineups()` at `exporters/exports.py:70-71` always returns
      `_empty_df`. Fix: (i) add `_fetched_fixture_lineups: list[dict]` module-level cache in `_fetch_runner.py`; (ii)
      populate in `_load_event_entities` from the `gcs_data["fixture_lineups"]` already being read; (iii) add
      `get_fetched_fixture_lineups()` accessor; (iv) implement `export_fixture_lineups()` using it. Then switch
      `fixture_lineups` out of `_POST_MATCH_TABLES` (currently incorrect rule applied) into the kickoff-offset stamping
      path (`stamp_available_at_kickoff_offset(kickoff_col="kickoff_utc",     minutes=60)`).
- [ ] [SCRIPT] P0. **Wire `fixture_player_stats` stub.** Same pattern as `fixture_lineups`. `_fetch_runner.py:173` logs
      row count but never stores. `export_fixture_player_stats()` returns empty. Fix: add `_fetched_player_stats`
      cache + accessor + real export. Stamping stays as `post_match` once wired.
- [ ] [SCRIPT] P0. **Wire OR scope-out `coaches` stub.** `export_coaches()` at `exports.py:135-137` always returns
      empty; no source fetch is implemented anywhere in `_fetch_runner.py`. Decide: (a) implement an
      `api_football /coachs` endpoint fetch path, OR (b) explicitly mark `coaches` as deferred + emit
      `record_empty(row_key)` for every batch run so the manifest is honest. **Default if no decision: (b)** — surfaces
      the gap as honest absence rather than silent empty. Per workspace rule on path A/B/C decisions for empty exports
      (CLAUDE.md `§ Three-category empty-output decision`), the bug class is the same as MDPS Phase 2.A: silent empty
      parquets with manifest `captured` is banned; route through `record_empty` instead.
- [ ] [SCRIPT] P0. **Wire OR scope-out `rounds` stub.** Same status as `coaches` — `export_rounds()` at
      `exports.py:148-150` returns empty; no source fetch. Same decision: implement OR `record_empty`. Default (b).

#### Phase 2.C body — `available_at` stamping migration (post-amendments)

- [ ] [SCRIPT] P0. Delete `_ensure_timestamp` from `cli/handlers/batch_handler.py:146` AND `cli/batch_write.py:38`. No
      shim, no fallback.
- [ ] [SCRIPT] P0. Replace 4 `_ensure_timestamp` callsites in `batch_handler.py:383, 465, 528, 597` (and 1 in
      `batch_write.py:88`) with the appropriate `availability_stamping.stamp_available_at_*` call per
      `UAC.AVAILABILITY_AT_SEMANTICS`.
- [ ] [SCRIPT] P0. For each of the 14 `TABLE_TO_EXPORT` entries in `cli/handlers/batch_handler.py:76-91`, wire
      write-time `available_at` stamping per UAC semantic (rules amended per audit findings 2026-05-06): - `fixtures` →
      `stamp_available_at_offset(df, "kickoff_utc", offset=-7d)` — **synthesis-only** since no source exposes
      announcement time (amendment B). Document `kickoff−7d` as canonical proxy until upstream source enrichment plan
      lands. - `fixture_stats`, `fixture_player_stats` →
      `stamp_available_at_post_match(df, "kickoff_utc",       duration_min=120)` — **already wired**; `match_end_time`
      schema bump deferred to Stage 2 follow-up plan (amendment D). Current implementation is the maximum precision
      available. - `fixture_events` → `stamp_available_at_event_time(df, "event_time")` — `event_time` derived from
      `kickoff_utc + elapsed_min * 60s` in `gcs_reader._normalize_fixture_events` (amendment kept; only derivable column
      from Phase 2.D bumps). - `fixture_lineups` → `stamp_available_at_kickoff_offset(df, "kickoff_utc", minutes=60)`.
      Prerequisite: wire stub above first. - `injuries` →
      `stamp_available_at_post_match(df, "kickoff_utc", duration_min=120)` — **fallback only** since api*football
      `/injuries` exposes no timestamp (amendment C). Document as best-effort proxy until forward-poll-vs-backfill
      timestamp differentiation lands in instruments-service (separate plan
      `sports_forward_poll_timestamps_2026*<TBD>.plan.md`).     - 8 reference tables → `stamp_available_at_explicit(df,
      fetch_completed_at)`where`fetch_completed_at`      comes from`\_FETCH_COMPLETED_AT[table_name]` cache populated at
      fetch time.
- [ ] [SCRIPT] P0. Add `_FETCH_COMPLETED_AT: dict[str, datetime]` module-level cache in `_fetch_runner.py` (verified
      location via audit 2026-05-06; currently does not exist). Populate inside each `run_fetch_*` for the 8 reference
      tables at the moment the GCS read returns. Accessor: `get_fetch_completed_at(table_name) -> datetime`. Today's
      `datetime.now(UTC)` at stamp time is architecturally safe (slightly pessimistic — run-start, not per-entity fetch
      finish) but will be replaced by precise per-entity timestamps after this work lands.
- [ ] [TEST] P0. Per-table unit test: build a fixture row → call export → assert `available_at` column present + matches
      semantic + would pass `LookaheadBiasError` for a feature at `kickoff − 24h` window.
- [ ] [TEST] P0. Integration test: run batch over 1 day × 1 league × all 14 tables; assert manifest reflects honest
      verbs; assert `available_at` populated on every parquet; assert no row has `available_at > kickoff_utc + 4h`
      (sanity bound for post-match).
- [ ] [QG] P0. features-sports quality-gates.sh green.

### Phase 2.D — instruments-service sports schema bumps + write-time stamping

> **Phase 0 audit blockers 2026-05-06**: `announced_at`, `report_time`, `match_end_time` are **NOT sourceable** from
> currently-used providers (api_football's `/injuries` has no timestamp; no source exposes fixture announcement time; no
> source exposes match end time directly). Audit recommends scoping these OUT of Phase 2.D as immediately actionable and
> tracking them in a separate **forward-poll-vs-backfill timestamp plan** (drafted as a follow-up). Phase 2.D remains
> in-scope ONLY for `event_time` (derivable from `kickoff_utc + elapsed_min` per-event). The other three columns ship
> with low-confidence default values + audit columns + named successor plan reference.

- [ ] [SCRIPT] P0. **In-scope schema bump (event_time only — derivable)**: Add `event_time: timestamp_utc not null` to
      `FIXTURE_EVENTS_COLUMNS` (verify whether already there per-event in the audit). Populate at MTDS /
      instruments-service write time as `kickoff_utc + timedelta(minutes=event.elapsed_min)`. No source dependency.
- [ ] [SCRIPT] P0. **Deferred schema bumps with low-confidence fallback shipping today (named successor plan listed
      below)**: `announced_at` (FIXTURES), `report_time` (INJURIES), `match_end_time` (FIXTURE*STATS /
      FIXTURE_PLAYER_STATS) ship as nullable columns with paired `*_confidence`audit columns: -    `announced_at:
      timestamp_utc nullable`+    `announced_at_confidence: Literal["source_native",
      "low_default_kickoff_minus_14d"]`. Today: every row gets     `kickoff_utc -
      14d`+`low_default_kickoff_minus_14d`. When successor plan lands a forward-poll source that     captures real announcement time, rows re-stamp from the new source. - `report_time:
      timestamp_utc nullable`+    `report_time_confidence: Literal["source_native",
      "low_default_kickoff_minus_lead_time"]`. Today: every row gets     `kickoff_utc -
      injury_lead_time_estimate`(per-league average lead time, default 7 days) +    `low_default\*_`. Successor plan: forward-poll injury sources with timestamps.     - `match*end_time:
      timestamp_utc nullable`+`match_end_time_source: Literal["api_football_native", "sfi_progressive_freeze",
      "footystats_native", "understat_native",
      "low_default_kickoff_plus_120min"]`. Today: detection cascade lands per Phase 2.D below; rows that fall to last-resort get `low_default*\_`. SFI freeze-detection IS achievable today (re-uses halftime detector), so most fixtures resolve via cascade not fallback.     - `occurrence*time:
      timestamp_utc
      nullable`(in`INJURIES_COLUMNS`) — populated when injury fixture's `fixture_events`table contains the injury event; else null. No fallback.     **Successor plan**:`sports_forward_poll_timestamps_2026*<TBD>.plan.md`— captures real-time scraping of announcement, injury report, and match end times from sources that DO expose these (verify per source in that plan's Phase 0). After successor plan lands + retrospective backfill completes, the`\*\_confidence`
      audit columns surface low-default fixtures in data-status panel for re-attempt.
- [ ] [SCRIPT] P0. **`match_end_time` detection cascade (in scope — SFI freeze-detection IS achievable today)**. Cascade
      per-fixture (UAC `MATCH_END_TIME_DETECTORS` registry, source-priority ordered): 1. `api_football` —
      `fixture.fixture.timestamp` +
      `status_long ∈ {"Match Finished", "Finished after extra time", "Finished after penalties"}` resolves to actual end
      time. Use if status indicates finished AND timestamp present. 2. `soccer_football_info` (SFI) — re-use
      halftime-freeze detector (`≥4-of-6` freeze threshold across
      `shoots_total/shoots_on_target/shoots_off_target/attacks_dangerous_away/dominance_index_home/dominance_index_away`
      per existing features-sports halftime algorithm) but applied to second-half tail to detect full-time. Output:
      timestamp of longest stable freeze run after minute 80, min 5-min duration. Surface
      `match_end_time_source = "sfi_progressive_freeze"`. 3. `footystats` — match end timestamp if present in
      match-detail endpoint (verify in Phase 0 audit). 4. `understat` — match end timestamp if present (verify in Phase
      0 audit). 5. **Last-resort fallback only**: `kickoff_utc + 120min` with
      `match_end_time_source = "low_default_kickoff_plus_120min"`. Manifest row gets
      `attempted_failed[reason=MatchEndTimeUndetected]` if NO cascade source resolves AND fallback is used — operator
      can re-attempt later via successor plan.
- [ ] [SCRIPT] P0. instruments-service stale comment fix: `engine/orchestrator.py:4980` "ManifestWriter v5" →
      "ManifestWriter v6".
- [ ] [SCRIPT] P0. Wire `assert_available_at_present` (UTL helper) into `InstrumentsWriteGate._gated_sink_write` so any
      ingester forgetting to stamp `available_at` fails loud.
- [ ] [TEST] P0. Per-source ingester test: feed a sample API response → assert `available_at` column populated correctly
      per UAC semantic.
- [ ] [QG] P0. instruments-service quality-gates.sh green.

QG between Phase 2 and Phase 3: every Phase 2 service has QG green; integration smoke run end-to-end produces honest
manifest verbs across all 4 services for a 1-day × 1-venue test run.

---

## Phase 3 — Retrospective migration (after Phase 2 lands)

The whole point of Phase 3 is: existing on-disk parquets + manifest rows that were written under the old (buggy)
contract get corrected, so the post-merge backfill % means real %. No silent "old data still lies, new data is honest"
split.

### Phase 3.A — Manifest reconciliation scripts

- [ ] [SCRIPT] P0. `mdps_reconcile_1440_nan_placeholders.py` — scan every MDPS-written parquet under
      `gs://{pid}-mdps-*/raw_candle_data/`; for each file, compute `nan_ratio_per_column` for OHLC columns; if all 4 of
      (open, high, low, close) are >95% NaN AND row_count == n_candles → flip manifest row from `captured` to
      `attempted_failed[reason=EmptyPlaceholderBugBackfill]`. Per-VM shard write (manifest concurrency rule).
      Idempotent + dry-run + scoped by `--asset-group` / `--data-type`. Re-attempt happens via existing MDPS backfill
      flow once Phase 2.A lands.
- [ ] [SCRIPT] P0. `mtds_reconcile_partial_bundles.py` — for every `data_type ∈ BUNDLED_DATA_TYPES` with on-disk
      parquets, count clusters per UAC registry; if observed clusters < expected → flip manifest from `captured` to
      `attempted_failed[reason=ClusterCoverageError(historical)]` with the missing cluster set in the error_reason
      payload. Handles options_chain (ES.OPT 11-cluster), futures_chain, sports_fixture_bundle. Per-VM shard write.
- [ ] [SCRIPT] P0. `mtds_reconcile_partition_mismatch.py` — scan a sample of raw_tick parquets; for each instrument's
      parquet under `day=YYYY-MM-DD`, check if any tick's `timestamp.date()` differs from the partition key. Stats-only
      first (count mismatches per venue / data_type / day); flag for human review before flipping any manifest rows
      (this is upstream-bug detection, not data-quality fix).
- [ ] [SCRIPT] P0. `features_sports_reconcile_available_at.py` — for every features-sports parquet on disk, check if
      `available_at` column present + populated correctly per the new UAC semantic. If missing or wrong → flip manifest
      from `captured` to `attempted_failed[reason=MissingAvailableAt]`. Re-attempt happens via Phase 2.C re-run.
- [ ] [SCRIPT] P0. Pre-v5 / pre-v6 manifest row purge — wire
      `instruments-service/scripts/dedupe_manifest_schema_drift.py` + `purge_legacy_unsharded_manifest_rows.py` into the
      orchestrator boot sequence (per parent HANDOVER §"Migration items"). Delete the fallback readers that previously
      handled legacy shapes.
- [ ] [SCRIPT] P0. `category=` → `asset_group=` GCS migration runbook — confirm migration scripts exist for every
      asset_group (cefi/defi/tradfi/sports/prediction); run sequentially per asset_group with a verification step
      (sample list_blobs after each, assert ≥99% canonical hive vocab). Do NOT delete the legacy fallback reader until
      100% migrated AND a hold-period confirms no readers fail.

### Phase 3.B — GCS available_at backfill (sports + others)

- [ ] [SCRIPT] P0. For every sports parquet on disk pre-Phase-2.C, add `available_at` column with the value derived from
      the new UAC semantic + the row's existing columns (kickoff_utc / event_time / report_time / match_end_time /
      fetch_completed_at). One-shot rewrite per file. Manifest update: `available_at_stamped_at = <run_time>` audit
      column.
- [ ] [SCRIPT] P0. Delete legacy `_ensure_timestamp`-stamped `timestamp` columns where they equalled the (now-incorrect)
      midnight UTC fallback. The new `available_at` column replaces them as the SSOT.
- [ ] [SCRIPT] P0. Per-(asset_group, data_type) backfill scope: - **sports** (above) - **CeFi**: confirm raw_tick
      partitions already have implicit per-tick `timestamp` column → derive
      `available_at = timestamp + scrape_latency_estimate` per source priority registry - **DeFi**: similar to CeFi but
      per-block + RPC-latency offset - **TradFi**: similar to CeFi - **Prediction**: deferred until
      canonical_question_group SSOT lands (follow-up plan)

### Phase 3.C — Reconciler observability + halt-on-error

- [ ] [SCRIPT] P0. Every reconciler script wraps work in `unified_trading_library.run_lifecycle.run_lifecycle(...)` (per
      existing run_lifecycle SSOT rollout). Emits `RECONCILER_STARTED` / `RECONCILER_PROGRESS` (per-asset-group with row
      counts) / `RECONCILER_COMPLETED` / `RECONCILER_FAILED`.
- [ ] [SCRIPT] P0. Each reconciler script supports `--max-flips-per-run` halt safety; default 100k. Operator confirms
      first 100k flips look right before lifting the cap.
- [ ] [SCRIPT] P0. Each reconciler emits a CSV/JSON audit report at `gs://{pid}-reconciler-audit/{run_id}/` listing
      every flipped (row_key, old_status, new_status, error_reason).

QG between Phase 3 and Phase 4: every reconciler has run end-to-end on a 1-week sample window; audit reports reviewed by
user; no anomalies.

---

## Phase 4 — Data-status UI + alerts (parallel with Phase 2 after Phase 1 lands)

### Phase 4.A — deployment-api

- [ ] [SCRIPT] P0. New per-pillar write-gate failure breakdown in `data_status_service.py`: - Aggregate
      `attempted_failed` rows by `error_reason` → return per-shard breakdown - New columns: `failed_row_count`,
      `failed_nan_ratio`, `failed_schema`, `failed_cluster`, `failed_timestamp_bias`, `failed_malformed`,
      `failed_empty_placeholder_backfill`
- [ ] [SCRIPT] P0. New endpoint `GET /data-status/{service}/leaf/{shard_key}/schema` — returns per-leaf-parquet schema
      view: columns, types, row_count, per-column non_null_count, per-column NaN ratio, `available_at`
      min/max/null_count.
- [ ] [SCRIPT] P0. Live-vs-historical envelope alert: when historical-mode produces a `data_type` for a date in the live
      window AND `live_pipeline_already_wrote = true` → emit `LIVE_HISTORICAL_DOUBLE_WRITE` warning event.

### Phase 4.B — deployment-ui (unified-trading-system-ui)

- [ ] [SCRIPT] P0. Render new `attempted_failed` reasons distinctly per typed error in the data-status panel: - Distinct
      color + icon per (`EmptyPlaceholderBugBackfill`, `ClusterCoverageError`, `UpstreamTimestampBiasError`,
      `MalformedTickFieldError`, `MissingAvailableAt`, `ClusterCoverageError(historical)`,
      `RAW_TICK_PARTITION_MISMATCH`) - Drill-down per reason → leaf parquet + audit report link
- [ ] [SCRIPT] P0. Surface per-pillar write-gate failure breakdown as a stacked-bar visualisation per shard.
- [ ] [SCRIPT] P0. Schema-view modal (per-leaf parquet) — call new `/leaf/.../schema` endpoint; render columns + types +
      row_count + NaN ratio + `available_at` envelope.
- [ ] [SCRIPT] P0. Live-vs-historical envelope alert badge in the asset-group panel header.

QG between Phase 4 and Phase 5: UI smoke-test (Tier 0 + Tier 1) — every new color/badge/drill-down renders correctly
against seeded fixtures.

---

## Phase 5 — Validation + honest-coverage baseline

- [ ] [SCRIPT] P0. Per-service end-to-end coverage measurement (post-reconcile): - Denominator =
      `expected_dates × expected_instruments × expected_data_types` clipped by `SOURCE_COVERAGE_START` /
      `KNOWN_COVERAGE_GAPS` / `venue_trading_calendar` - Numerator =
      `count(manifest_rows where capture_status == "captured")` - Honest empty =
      `count(capture_status == "empty_confirmed")` (NOT in numerator, but tracked as legitimate absence) - Failed =
      `count(capture_status == "attempted_failed")` per error_reason (NOT in numerator)
- [ ] [SCRIPT] P0. Document the post-merge baseline at
      `unified-trading-pm/codex/02-data/honest_coverage_baseline_2026_05.md`: - Per-(service, asset_group, data_type)
      baseline % - Per-error_reason failure breakdown - Set as the ratchet floor — future merges that drop coverage
      below this % fail QG (per parent plan §"coverage_ratchet_policy")
- [ ] [SCRIPT] P0. LookaheadBiasError end-to-end smoke test: pick 1 strategy / 1 model / 1 fixture; run feature compute
      at `kickoff − 24h`; assert no input row consumed has `available_at > kickoff − 24h`; CI-runnable.
- [ ] [SCRIPT] P0. Write-gate quartet integration test (per asset_group × per bundled data_type matrix): row=0 →
      `record_empty`; partial bundle → `record_failed(ClusterCoverageError)`; high NaN →
      `record_failed(NanRatioExceededError)` (deferred to follow-up plan once that pillar lands); schema mismatch →
      `record_failed(SchemaMismatchError)`. CI-runnable.
- [ ] [QG] P0. Workspace-wide QG on every repo touched (UTL, UAC, MDPS, MTDS, features-sports, instruments-service,
      deployment-api, deployment-ui, unified-trading-pm). Per-repo `quality-gates.sh` green.

QG end-of-plan: user signs off on baseline document; ratchet floor activated.

---

## Coordination with sibling plans

> **2026-05-06 update**: this plan is now the **umbrella** for the honest-coverage + shard-granularity work-package. See
> "Wrapped sibling plans (this is the single SSOT plan to reference end-to-end)" section near the top. The four wrapped
> plans (writegate / predictions / shard_granularity / data_status_multi_axis) execute against the layered DAG defined
> there. Coordination notes below are surface-level cross-references; full execution sequencing lives in the
> wrapped-plans Layer 1-5 DAG.

**Wrapped child plans:**

- **[`predictions_canonical_question_group_polymarket_migration_2026_05_06.plan.md`](./predictions_canonical_question_group_polymarket_migration_2026_05_06.plan.md)**
  — child plan. Predictions Phase 1A populates the `PREDICTION_GROUPS = {}` slot reserved by writegate Phase 1B;
  predictions Phase 2 ships instruments-service MARKET_LIFECYCLE writer + MTDS Polymarket / Kalshi adapter rekey +
  features-cross-instrument reader migration. Sequenced Layer 2 in DAG.
- **[`data_status_multi_axis_shard_propagation_2026_05_06.plan.md`](./data_status_multi_axis_shard_propagation_2026_05_06.plan.md)**
  — child plan. Phase 0 ships UTL `fixture_id` / `job_id` columns + UAC `data_status_axis_matrix.py` SSOT (bundles with
  writegate Phase 1A UTL change); Phase 1A sports fixture_id writers + Phase 1B job_id writers ship alongside writegate
  Phase 2.B/2.C; Phase 2 deployment-api + Phase 3 deployment-ui ship alongside writegate Phase 4. `fixture_id` is
  **display-axis only**, not a manifest shard atom (per the plan's "When to shard vs when to just add a display axis"
  framework). Phase 4 is almost no-op (no bulk fixture_id or job_id backfill).

**Parent plan + companion HANDOVER (architectural):**

- **`shard_granularity_ssot_propagation_2026_05_06.plan.md` Phase 1 Tier 1 #1 (MDPS 1440-NaN, paused)** — superseded by
  this plan's Phase 2.A. Mark as superseded in companion plan; delete the "AWAITING USER DIRECTION" todo.
- **`shard_granularity_ssot_propagation_2026_05_06.plan.md` Phase 1 Tier 2 raw-tables (sports available_at, paused)** —
  superseded by this plan's Phase 2.C + Phase 2.D. Mark as superseded; delete the "Paused pending user direction on
  hybrid acceptance" todo.
- **HANDOVER §"Item 1 — Cluster-aware bundle validation"** — superseded by this plan's Phase 1A `record_captured`
  mandatory kwarg + Phase 1C CLAUDE.md rule. The "TradFi MVP follow-ups parallel stream" framing is no longer accurate;
  cluster validation is now the mainline contract change, not a parallel stream. **HANDOVER lines 67-73, 709, 772, 807,
  834, 953 commit to workspace-wide `manifest.add()` → `record_captured()` migration** — this plan's Phase 2.B is the
  MTDS instance of that workspace migration. Same pattern rolled across features-sports `batch_handler.py:615-628`,
  features-onchain canonical writer, instruments-service `writer.add()`, features-delta-one, MDPS
  `canonical_writer.py:313-326`.

**Other related plans (not wrapped):**

- **`market_tick_data_to_100pct_2026_05_05.plan.md`** — coordination: Phase 2.B partition-key validation + cluster
  wiring overlap with this plan's MTDS scope. Reconcile ownership in Phase 0 before Phase 2.B starts.
- **`data_status_ui_fixes_2026_05_06.plan.md`** + **`data_status_offline_rollup_2026_05_06.plan.md`** —
  predecessor/sibling plans whose incremental fixes ship pre-umbrella; outputs already in production per
  data_status_multi_axis plan §References ("This session's incremental fixes (already shipped, not part of this plan)").
- **`manifest_schema_v6_quote_margin_combo_2026_04_23.plan.md`** — Phase 2.A v6 column wiring + Phase 2.B v6 column
  wiring align. Verify v6 schema state matches what this plan assumes.
- **`feature_dag_uac_ssot_and_features_coverage_2026_05_06.plan.md`** — referenced by data_status_multi_axis as related;
  feature DAG SSOT work is Tracked Open Q #2 here (not in umbrella scope yet — separate follow-up).

---

## Tracked open questions (deferred to follow-up plans)

These remain open and will be resolved in subsequent plans the user drafts:

1. ~~**UAC `canonical_question_group` SSOT** for Polymarket / Kalshi predictions~~ — **ABSORBED INTO UMBRELLA
   2026-05-06.** Now a child plan under "Wrapped sibling plans" section above:
   [`predictions_canonical_question_group_polymarket_migration_2026_05_06.plan.md`](./predictions_canonical_question_group_polymarket_migration_2026_05_06.plan.md).
   Layered DAG sequences predictions Phase 1A after writegate Phase 1B (PREDICTION_GROUPS slot + classifier wraps
   existing UAC `_prediction_market_taxonomy.py`). Also resolves Tracked Open Question §10 (Polymarket shard-key
   sequencing) and the residual `category=prediction` legacy hive vocab cleanup.
2. **`feature_group → required_inputs[]` DAG SSOT in UAC** — currently inlined 3 different ways across features-onchain,
   features-sports, features-delta-one. Drives `LookaheadBiasError` enforcement.
3. **v6 columns `quote_asset` / `margin_type` / `combo_type` / `leg_weights` ownership** — only MTDS writes them;
   instruments-service, MDPS leave at `""`. Confirm MTDS-only or roll out.
4. **NaN-ratio gate lift to UTL** — currently inlined in instruments-service `_validate_predictions_null_rates`
   (FootyStats-only). Lift to UTL `write_gate_helper` with per-feature-group thresholds in UAC.
5. **Phantom-audit drift-probe lift to UTL** — `reconcile_phantom_manifest_rows_all.py` 5-axis logic +
   `ASSET_GROUP_CONFIG` is script-local. Lift to UTL `manifest_audit` so MDPS / MTDS / features-\* can reuse.
6. **Per-VM shard isolation as workspace rule** — `MANIFEST_PER_VM_SHARDS=true` + unique `VM_NAME` pattern from
   `00f6352`/`619a32e` should become every-concurrent-backfill default. Add to base-service.sh QG check.
7. **Multi-source merge spec** — Phase 1B seeds `SOURCE_PRIORITY` top entry only. Full multi-source merge
   (timestamp-availability > coverage > info-richness > merge-different-fields) is a follow-up plan.
8. **Bulk pre-flight tightening in instruments-service** — UTL `check_shard_freshness` line 2259–2267 doesn't include
   `league_id` in match unless explicitly passed; orchestrator line 1224 calls without it. Harsh's commit `7bfa877`
   extended downstream per-league skip; tightening the bulk gate is deferred.
9. ~~**MTDS sports per-fixture_id shard-granularity**~~ — **MOVED IN-SCOPE 2026-05-06.** Now Phase 2.B in this plan.
   Reasoning: ML predictions are fixture-level; without per-fixture sharding, can't drill down on missing fixtures or
   fixture-specific stats. League stays as a higher-level rollup grouping. Anything that breaks (MTDS reader paths, MDPS
   sports adapter, features-sports input pipeline, deployment-ui sports panel) is fixed in this plan. Manifest
   reconciliation handles the shard-shape migration in Phase 3.A. **Update 2026-05-06 (data_status_multi_axis plan)**:
   `fixture_id` is now correctly framed as a **display-axis-only column** (per
   [data_status_multi_axis_shard_propagation_2026_05_06.plan.md](./data_status_multi_axis_shard_propagation_2026_05_06.plan.md)
   "When to shard vs when to just add a display axis" section), NOT a manifest shard-atom. `(league_id, day)` bounds the
   fixture set; per-fixture detail comes from the parquet at drill-down time. Writers populate `fixture_id` as a column
   on per-fixture rows for filter/group; no bulk manifest row-expansion script.
10. **Polymarket shard-key sequencing** — commits `b336834`/`d7bd17f` fixed crypto-keyword false-positives but the
    shard-key (`data_type=<base_asset>`) still deviates. Resolved by Q #1 successor (predictions plan, now child of
    umbrella).
11. **Multi-axis read-side display + manifest column additions** (`fixture_id`, `job_id`, UAC axis matrix SSOT,
    deployment-api `breakdowns`, deployment-ui dropdowns) — **ABSORBED INTO UMBRELLA 2026-05-06.** Child plan:
    [`data_status_multi_axis_shard_propagation_2026_05_06.plan.md`](./data_status_multi_axis_shard_propagation_2026_05_06.plan.md).
    Sequenced into Layer 1 (Phase 0 UTL+UAC) / Layer 2 (Phase 1A sports fixture_id writers + Phase 1B job_id writers) /
    Layer 3 (Phase 2 deployment-api + Phase 3 deployment-ui) / Layer 4 (Phase 4 conditional migrations) / Layer 5 (Phase
    5 rollup + Phase 6 e2e). One open follow-up: `client_id` semantics rework — kept as separate Tracked Open Question
    here per the data_status plan's "What this plan does NOT do" section.
12. **`client_id` semantics rework** — already in v6 with multi-tenant scoping meaning. Out of scope for both the
    umbrella and the data_status_multi_axis child plan; deferred to a future plan that has a real consumer needing the
    rework.

---

## Estimated timeline

- Phase 0: 2-3 days (audit completion)
- Phase 1A + 1B + 1C: 1 week parallel (UTL + UAC + CLAUDE.md)
- Phase 2: 2 weeks parallel across 4 services
- Phase 3: 1 week (reconcilers + GCS rewrites; compute-heavy)
- Phase 4: 1 week parallel with Phase 2 (UI + alerts)
- Phase 5: 2-3 days (baseline measurement + ratchet activation)

**Total: ~3.5 weeks of focused work + reconciler runtime.**

---

## Success criteria

- ✓ All 6 cross-cutting principles enforced at runtime (UTL guards) AND statically (QG steps).
- ✓ `_create_empty_output` deleted; `_ensure_timestamp` deleted; `_write_manifest_records` v3-shape deleted;
  `check_cluster_coverage` made internal. Single SSOT per concern, no shims.
- ✓ Every shard's parquet on disk has `available_at` column populated correctly per UAC semantic. No row has
  `available_at` derived at read-time.
- ✓ Every bundle data_type's `record_captured` is wired with `expected_root_clusters` + `cluster_extractor`. QG STEP
  5.64 enforces.
- ✓ Forward writes produce honest manifest verbs only (`captured`, `empty_confirmed`,
  `attempted_failed[<typed_reason>]`).
- ✓ Retrospective on-disk corrections: 1440-NaN historical shards flipped + queued for re-attempt; partial bundles
  flipped + queued; pre-v6 rows purged; legacy fallback readers deleted.
- ✓ Data-status UI surfaces per-typed-error breakdown + per-pillar write-gate failure stack + `available_at` envelope
  per leaf parquet.
- ✓ Honest coverage baseline measured per service; ratchet floor activated; future regressions detectable.
- ✓ Workspace-wide QG green on every repo touched.
- ✓ Live = batch verification: any new (asset_group, data_type) shipped after this plan must declare `SOURCE_PRIORITY` +
  `AVAILABILITY_AT_SEMANTICS` entries; QG enforces.
