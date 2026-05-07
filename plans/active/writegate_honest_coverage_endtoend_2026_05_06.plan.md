---
type: plan
role: umbrella
locked_by: live-defi-rollout
locked_since: 2026-05-06
created: 2026-05-06
companion_handover: plans/archive/shard_granularity_ssot_propagation_2026_05_06.HANDOVER.md
parent_plan: infrastructure_master_2026_05_07.plan.md # peer/umbrella; was shard_granularity_ssot_propagation, now folded
related:
  - predictions_master_2026_05_07.plan.md # folds in predictions_canonical_question_group_polymarket_migration
  - infrastructure_master_2026_05_07.plan.md # folds in shard_granularity + data_status_multi_axis + deployment_service_build_infra
supersedes_phases:
  - plans/archive/shard_granularity_ssot_propagation_2026_05_06.plan.md § Phase 1 Tier 1 #1 (MDPS 1440-NaN, paused — now scoped here)
  - plans/archive/shard_granularity_ssot_propagation_2026_05_06.plan.md § Phase 1 Tier 2 raw-tables (sports
    available_at, paused — now scoped here)
manifest_migration_coordinator: manifest_migration_master_2026_05_07.plan.md # Stage 2.A/2.B/2.C + Stage 3.A/3.B/3.C scoped here; coordinator owns cross-plan sequencing + VM impact + operator pause-resume gates
status: drafted
---

# Write-Gate + Honest-Coverage End-to-End — Plan (UMBRELLA)

## Audit 2026-05-07

- **Audit run**: 2026-05-07 (parallel-agent pass over 87 unchecked todos)
- **Verified**: 87 of 87 unchecked todos
- **Mis-marked DONE → flipped**: 12 (multiple Phase 1A/1B helpers + Phase 2.A registry + scanner + MTDS partition
  validation + MTDS cluster wiring (ES.OPT slice) + Phase 2.A prediction empty-path silent-drop fix + ES.OPT lift + UTL
  availability_stamping helpers + assert_available_at_present wiring + CLAUDE.md cross-link + CLAUDE.md
  sync-to-mirrors + features-onchain partial-stub fixture_lineups; see per-line audit markers)
- **In-flight (running VMs)**: 37 VMs at 03:30 UTC writing to manifest. CeFi historical
  (bitfinex/bitget/coinbase/hyperliquid/kraken ~24 VMs T+12-22h), TradFi mdps-tradfi-2021..2025 (5 VMs T+22h), Sports
  af/fs/sfi/us-backfill (4 VMs T+5h). They emit `record_empty(reason=...)` per Phase 2.E.1 contract IF tarballs include
  UTL@958634f9 + MDPS Tier 2A/C/D/E commits. **Untracked WIP detected**:
  `features-sports-service/scripts/features_sports_reconcile_available_at.py` (16718 bytes, untracked, dated 04:18 —
  another agent's in-flight work per "Two teammates" rule. NOT touched by this audit.)
- **Blocked by**: predictions_master_2026_05_07 — Phase 2.A prediction silent-drop fix (line 1030) substantially shipped
  but row_key shape fully resolves only when canonical_question_group SSOT lands in predictions plan. Reconciler in
  Phase 3.A re-flips after.
- **Blocks**:
  - `defi_master_2026_05_07` (relies on writegate Phase 1A/2.A typed-error contract for DeFi reconcilers)
  - `infrastructure_master_2026_05_07` (data_status_multi_axis Phase 2/3 needs writegate Phase 4.A typed-error rendering
    surface)
  - `master_to_live_defi_2026_05_23` Group F trading prereqs (need honest manifest reasons for batch-vs-live
    reconciliation + alerting)
- **Last meaningful commit**: instruments-service@21aef51 Tier 3D.2 reconciler refactor importing UTL classifier;
  UTL@c5c2669e classify_legacy_empty_row helper; deployment-api@176c599 reader-side wiring (3 commits chain shipped
  2026-05-07)
- **Recommendation**:
  1. **HIGHEST LEVERAGE — Phase 4.A deployment-api typed-error rendering** (lines 1536-1544, 4 todos): unblocks operator
     visibility for the new reasons + prevents "we have honest data but can't see it" failure. Minimal scope, high
     value. Sequence before May 23.
  2. **Phase 2.A residual** (lines 1027, 1030, 1038, 1040, 1058, 1060, 1062, 1064): batch_workers.py path B/C catch
     (live_workers shipped @c924410), `_write_manifest_records` v3-shape delete, v6 column wiring, MDPS chain-bundle
     cluster wiring, integration tests, QG green. ~3-4 days work.
  3. **Phase 2.B residual** (lines 1095, 1102 partly DONE, 1108, 1110, 1126, 1135, 1137, 1140, 1142-1145): MTDS
     partitioner+cluster wiring shipped for ES.OPT only; broader bundle types + per-fixture sharding deferred. Can run
     parallel with #2.
  4. **Phase 2.C** (lines 1163-1217): features-sports stub wiring + `_ensure_timestamp` deletion + per-table
     `available_at` migration. Self-contained; 2-3 days.
  5. **Phase 3.A residual reconcilers** (lines 1404, 1408 in-flight, 1411, 1415): partition-mismatch +
     sports-available_at + boot-sequence wiring. Lower urgency than Phase 4.A.
  6. **Phase 3.D.3 + Phase 5 baseline + Phase 4.B UI**: deferrable to post-Phase-4.A unblock.
  7. **Phase 1C / 1A doc + QG steps** (lines 888, 890, 996, 1308): low-cost; fold into nearest commit cycle.
- **Cross-plan blockers**: see "Cross-plan blockers" section below for downstream gating.

### Cross-plan blockers detected

- `writegate:Phase 4.A` BLOCKS `infrastructure_master:data_status_multi_axis Phase 2-3` (deployment-api/UI need
  typed-error reasons surfaced first)
- `writegate:Phase 2.A` (line 1030 prediction silent-drop) blocked by `predictions_master:Phase 1A`
  (canonical_question_group SSOT for stable row_key)
- `writegate:Phase 5 ratchet` BLOCKS `master_to_live_defi_2026_05_23:Group F trading prereqs` (batch-vs-live
  reconciliation needs honest baseline)
- `writegate:Phase 2.D match_end_time cascade` (line 1246) BLOCKS `sports_master:strategy alpha measurement`
  (lookahead-bias gate needs accurate match-end timestamps)

---

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
| [`data_status_multi_axis_shard_propagation_2026_05_06.plan.md`](./data_status_multi_axis_shard_propagation_2026_05_06.plan.md)                                                                    | child                            | Read/display side:`fixture_id` (display-axis only) + `job_id` manifest columns; UAC `data_status_axis_matrix.py` SSOT; deployment-api `breakdowns` + `secondary_axis` filtering; deployment-ui DataStatusTab dropdowns + `BreakdownsAccordion`                                                             |

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

| #     | Amendment                                                                                                                                                                                                                                                                                                                                                                                                                                                              | Status                                                                              | Owner                    |
| ----- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- | ------------------------ |
| A     | Correct Phase 2.B file paths (monolithic `tardis_adapter.py` / `databento_adapter.py` / `tradfi_shared.py`, NOT non-existent `adapters/tardis/options_chain.py` etc.)                                                                                                                                                                                                                                                                                                  | **Applied**                                                                         | Cosmetic — Claude        |
| B     | Drop `announced_at` from Phase 2.D schema bumps (no source field exists)                                                                                                                                                                                                                                                                                                                                                                                               | **Applied**                                                                         | Evidence-backed — Claude |
| C     | Drop `report_time` / `occurrence_time` for injuries from Phase 2.D as immediately actionable (api_football `/injuries` has no timestamp; we have dates not exact times). Documented in schema-additions table comments.                                                                                                                                                                                                                                                | **Applied**                                                                         | Evidence-backed — Claude |
| D     | Defer `match_end_time` schema bump to Stage 2 follow-up plan; keep detection cascade design + current `kickoff+120min` fallback as Stage 1. We have dates not exact end times. Documented in schema-additions table comments.                                                                                                                                                                                                                                          | **Applied**                                                                         | Evidence-backed — Claude |
| E     | Add 4 stub-wiring todos to Phase 2.C as prerequisites (`fixture_lineups`, `fixture_player_stats`, `coaches`, `rounds`). 4 export functions silently return empty — distinct bug class from 1440-NaN.                                                                                                                                                                                                                                                                   | **Applied**                                                                         | Scope expansion — Claude |
| **F** | **Phase 2.B cluster wiring point** — audit found ZERO `record_captured` callsites for any MTDS bundle. All bundles flow through `writer_manifest.add()` at `engine/orchestrator.py:1940`. Phase 1A's `MissingClusterValidationError` guard at `record_captured` would never fire. Plan needs to either (i) move the wiring point to `orchestrator.py:1940`, or (ii) refactor adapters to call `record_captured` directly. Affects Phase 1A contract design assumption. | **RESOLVED 2026-05-06: option (i) — orchestrator boundary, with bundle-only check** | Architectural — Ikenna   |

**Amendment F resolution (2026-05-06): ALREADY IMPLEMENTED for ES.OPT — generalisation deferred until 2nd bundle adapter
exists.**

Inspection of `engine/orchestrator.py:2126-2193` showed cluster validation is wired today for ES.OPT
(`venue_name == "CME-OPTIONS"` + `itype_key in _UNDERLYING_PARTITIONED_TYPES`). The flow:

1. Adapter writes parquets, `writer.cluster_counts` populated per `(itype, dt, underlying)`.
2. Orchestrator aggregates into `chain_cluster_counts[(venue, itype, dt, underlying)]` at line 1867.
3. Per-bundle gate at lines 2138-2179: `get_active_es_options_clusters_for_date_from_snapshot` → expected;
   `ManifestWriter.check_cluster_coverage_from_counts(observed, expected)` → routes under-coverage to
   `record_failed(ClusterCoverageError)`; otherwise `writer_manifest.add()` proceeds.

The earlier framing (Phase 1A guard at `record_captured` never fires because adapters call `writer_manifest.add()` not
`record_captured` directly) is **correct** but the orchestrator already wraps the gate around `writer_manifest.add()`
for bundles. So the design goal — bundle-only cluster validation gating the manifest write — is met for ES.OPT.

**What still ships in Phase 2.B (deferred until those bundles need validation):**

- Replace the hardcoded `venue_name == "CME-OPTIONS"` branch with `data_type in BUNDLED_DATA_TYPES` lookup driven by
  UAC.
- Per-bundle `expected_root_clusters` lookup (today: ES uses `get_active_es_options_clusters_for_date_from_snapshot`;
  futures_chain / prediction_canonical_question_group / sports_fixture_bundle each need their own expected-cluster
  source).

For ES.OPT today (the only currently-needed bundle), Phase 1A's design intent is met. Phase 2.B generalisation kicks in
when a second bundle adapter ships.

**ES_OPTIONS_CLUSTERS naming clarification (2026-05-06):** The earlier "`ES_OPTIONS_CLUSTERS` → generic
`OPTIONS_CLUSTERS_BY_ROOT` rename" note was a misread of the architecture. The 11-cluster taxonomy (`ES`, `EW`,
`EW1`-`EW4`, `E1A`-`E5A`, `EOM`) is genuinely ES-specific — driven by CME futures symbology
(`<root><month-letter><year>` format). Deribit BTC options (`BTC-30JUN24-50000-C`) and Solana DEX options have
completely different formats, requiring separate extractor regexes + cluster taxonomies. The correct pattern when a
second root lands: add `DERIBIT_BTC_OPTIONS_CLUSTERS` + `extract_deribit_btc_options_cluster` +
`get_active_deribit_btc_options_clusters_for_date` as **siblings** to the ES symbols, plus a per-(data_type, root)
lookup at `DATA_TYPE_TO_CLUSTER_REGISTRY`. **No rename needed today; current symbols are correctly scoped.**

**Phase 2.B execution gate (UPDATED 2026-05-06)**: ES.OPT cluster gate **shipped** in MTDS orchestrator already
(CME-OPTIONS branch). Generalisation to other bundle types deferred to when a second bundle data_type exists with live
MTDS adapters.

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
| `market_interface/adapters/tradfi/tardis_adapter.py` (Tardis CeFi + TradFi options/futures bundles) | 870, 1693, 1804   | Bundle write — Phase 2.B cluster validation site.**Path corrected per audit 2026-05-06 amendment A**: original plan listed `adapters/tardis/options_chain.py` and `adapters/tardis/futures_chain.py` which do not exist. Tardis logic is in this monolithic file (CeFi + TradFi paths) — `finalise_and_write_cefi_shards()` at line 870, `_download_futures_per_instrument()` at 1693, futures_chain TradFi path at 1804.                                                                                                                                               |
| `market_interface/adapters/cefi/tardis_shared.py`                                                   | 84, 507           | Tardis CeFi shared helper —`CHAIN_INSTRUMENT_TYPES` constant + `build_partition_path()` for v5/v6 chain paths. Phase 2.B touches if cluster_extractor wires through here.                                                                                                                                                                                                                                                                                                                                                                                               |
| `market_interface/adapters/tradfi/tradfi_shared.py`                                                 | 296, 423          | TradFi shared write helper —`_shard_instrument_type_for(OPTION) → "options_chain"` decision at line 296; `write_tradfi_shard()` at line 423 is the actual upload site for both Tardis-TradFi and Databento-TradFi bundle paths.                                                                                                                                                                                                                                                                                                                                         |
| `market_interface/adapters/tradfi/databento_adapter.py` (Databento TradFi options/futures bundles)  | 91, 822, 869–1001 | Bundle write — Phase 2.B cluster validation site.**Path corrected per audit 2026-05-06 amendment A**: original plan listed `adapters/databento/options_chain.py` and `adapters/databento/futures_chain.py` which do not exist. Databento logic is in this monolithic file: `_PARTITION_INSTRUMENT_TYPE` at line 91 (OPTION → options_chain), `download_batch_df()` writer.write_chunk() at 822, `_enrich_with_canonical_ids()` at 869-1001.                                                                                                                             |
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

| File                       | Line                        | Change                                                                                                                                                 |                                                                                                               |
| -------------------------- | --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------- |
| `manifest_writer.py`       | 97                          | `ClusterCoverageError` ✓ exists                                                                                                                        |                                                                                                               |
| `manifest_writer.py`       | 1098                        | `check_cluster_coverage` — make private (`_check_cluster_coverage`); no longer public API                                                              |                                                                                                               |
| `manifest_writer.py`       | 1163                        | `record_captured` — add `expected_root_clusters: Mapping[str, int] \| None` + `cluster_extractor: Callable                                             | None `kwargs; raise`MissingClusterValidationError `when`data_type ∈ BUNDLED_DATA_TYPES` and kwargs not passed |
| `errors.py`                | new                         | `UpstreamTimestampBiasError`, `MalformedTickFieldError`, `MissingClusterValidationError`                                                               |                                                                                                               |
| `availability_stamping.py` | (already exists per LIFT-3) | Add `stamp_available_at_post_match`, `stamp_available_at_announcement`, `stamp_available_at_explicit`, `stamp_available_at_kickoff_offset(minutes=60)` |                                                                                                               |

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
| Per-pillar breakdown     | New columns:`failed_row_count` / `failed_nan_ratio` / `failed_schema` / `failed_cluster` per shard                                                                                                |
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
`sports_phantom_fixtures_recovery_2026_05_06.plan.md` plan AND its successor
`sports_fixtures_truthset_recovery_2026_05_06.plan.md`. Be aware while executing this plan because the recovery touches
the same `ManifestWriter` / orchestrator / `available_at` surfaces this plan modifies — the streams must not step on
each other.

> **2026-05-06 cross-cluster sequencing note (Conflict 14 resolution).** Three plans touch features-sports
> `available_at` from different angles: (a) this writegate plan (Phase 2.C deletes `_ensure_timestamp` + per-source
> `stamp_available_at_*` helpers, then Phase 3 flips `LookaheadBiasError` to strict-mode), (b) HANDOVER audit calls out
> features-sports `_ensure_timestamp` midnight bug + `LookaheadBiasError` silent-downgrade in `writer.py:65-66`, (c)
> sports truthset recovery is rewriting parquets that need `available_at` populated. **Required sequence (do not
> interleave):**
>
> 1. **First** — sports truthset recovery completes (FIXTURES + 5 downstream entities populated; capture_status
>    correct).
> 2. **Second** — this writegate plan's Phase 2.C ships `_ensure_timestamp` deletion + per-source stamping helpers.
> 3. **Third** — flip `LookaheadBiasError` to `strict=True` last (Phase 3). Flipping earlier would block the truthset
>    recovery's writes mid-flight.

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
- [x] [AUDIT] P0. instruments-service sports schemas — confirm the columns to add (`announced_at` on fixtures;
      `event_time` on fixture_events; `report_time` on injuries; `match_end_time` on fixture_stats /
      fixture_player_stats). **PARTIAL via #0.4 audit**: features-sports audit revealed source-side blockers — see
      "Phase 0 audit findings — features-sports TABLE_TO_EXPORT inventory" §"Tables blocked on upstream source-field
      availability". Schema bumps still needed for `event_time` (derivable from `kickoff_utc + elapsed_min`); the
      remaining proposed columns (`announced_at`, `report_time`, `match_end_time`) cannot be sourced from current
      providers — see findings below. [AUDIT 2026-05-07: DONE — audit complete; amendments B/C/D applied to plan; only
      `event_time` survives as in-scope schema bump (Phase 2.D); `announced_at`/`report_time`/`match_end_time` deferred
      with low-confidence fallback shipping per amended Phase 2.D body.]

QG between Phase 0 and Phase 1A/1B/1C: audit manifest reviewed by user; per-callsite A/B/C decisions signed off;
SOURCE_PRIORITY tie-breaker rules confirmed for each (asset_group, data_type) where multi-source applies.

---

## Phase 0 audit findings (2026-05-06 Claude session)

### Phase 0 audit findings — MDPS callsite categorisation

**Total callsites: 37** (NOT 53 — original plan estimate counted method definitions; actual
`return self._create_empty_output(...)` callsites = 37). Distribution: 16 A / 15 B / 5 C / 2 ?.

| File:Line                                 | Branch trigger                                                                                       | Category | Reason                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| ----------------------------------------- | ---------------------------------------------------------------------------------------------------- | -------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `cefi/book_snapshot_adapter.py:87`        | tick_data empty on entry                                                                             | A        | Honest absence — no rows from MTDS                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| `cefi/book_snapshot_adapter.py:117`       | tick_data empty after `interval_idx` filter                                                          | B        | Ticks present, all outside requested day — upstream timestamp bias                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| `cefi/derivative_adapter.py:69`           | tick_data empty on entry                                                                             | A        |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| `cefi/derivative_adapter.py:99`           | tick_data empty after filter                                                                         | B        |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| `cefi/futures_chain_adapter.py:75`        | tick_data empty on entry                                                                             | A        | Bundle: "no rows" = no contracts had quotes; not a cluster failure                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| `cefi/futures_chain_adapter.py:105`       | tick_data empty after filter                                                                         | B        | Bundle B-category — upstream partition bias                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| `cefi/liquidations_adapter.py:143`        | tick_data empty on entry                                                                             | A        | Legitimately sparse for low-OI                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| `cefi/liquidations_adapter.py:173`        | tick_data empty after filter                                                                         | B        |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| `cefi/options_chain_adapter.py:164`       | tick_data empty on entry                                                                             | A        | Bundle A-category                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| `cefi/options_chain_adapter.py:194`       | tick_data empty after filter                                                                         | B        | Bundle B-category                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| `cefi/trades_adapter.py:69`               | tick_data empty on entry                                                                             | A        |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| **`cefi/trades_adapter.py:74`**           | `_prepare_tick_data` returned None (interval_idx filter dropped all)                                 | **B**    | **Plan-confirmed reproduction path** — non-empty input, empty after bucketing                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| `cefi/trades_adapter.py:83`               | `price_col is None` (no derivable price column)                                                      | C        | Schema/field error — derive_price_column failed                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| `defi/fx_rate_adapter.py:120`             | tick_data empty on entry                                                                             | A        |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| `defi/fx_rate_adapter.py:131`             | `_detect_asset(instrument_id)` returned None                                                         | **C**    | **NEW finding**: instrument_id pattern unrecognised — schema/metadata gap                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| `defi/fx_rate_adapter.py:136`             | `_ASSET_TO_FEATURE.get(asset)` returned None                                                         | **C**    | **NEW finding**: asset detected but no feature mapping — registry gap                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| `defi/fx_rate_adapter.py:167`             | `price_col is None` (none of `(price, close, last, price_usd, usd_price)` in columns)                | **C**    | **NEW finding**: source schema drift — column name probe stale                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| `defi/liquidity_adapter.py:87`            | tick_data empty on entry                                                                             | A        |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| `defi/liquidity_adapter.py:119`           | tick_data empty after filter                                                                         | B        |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| `defi/market_state_adapter.py:77`         | tick_data empty on entry                                                                             | A        |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| `defi/market_state_adapter.py:109`        | tick_data empty after filter                                                                         | B        |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| `defi/swap_adapter.py:74`                 | tick_data empty on entry                                                                             | A        |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| **`defi/swap_adapter.py:106`**            | tick_data empty after filter                                                                         | **B**    | **Plan-confirmed reproduction path** — 1440 NaN bars when swaps timestamp-mislabeled                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| `sports/arbitrage_adapter.py:42`          | tick_data empty on entry                                                                             | A        |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| `sports/arbitrage_adapter.py:79`          | tick_data empty after filter                                                                         | B        | Sports odds B-category — multi-day spans + wrong partition                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| `sports/bucket_assignment_adapter.py:313` | tick_data empty on entry                                                                             | A        |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| `sports/bucket_assignment_adapter.py:319` | `_prepare_tick_data` returned empty (pivot/column failure)                                           | C        | Schema mismatch —`bm_minutes_to_kickoff` missing or pivot failed                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| `sports/bucket_assignment_adapter.py:331` | all rows had `horizon_idx == -1` (outside staleness caps)                                            | **?**    | **Ambiguous**: legitimately stale odds (A) vs miscalculated `bm_minutes_to_kickoff` (C). **Recommend C provisionally** — derived field; miscalc most likely cause                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| `sports/odds_movement_adapter.py:37`      | tick_data empty on entry                                                                             | A        |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| `sports/odds_movement_adapter.py:74`      | tick_data empty after filter                                                                         | B        |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| `sports/odds_snapshot_adapter.py:41`      | tick_data empty on entry                                                                             | A        |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| `sports/odds_snapshot_adapter.py:78`      | tick_data empty after filter                                                                         | B        |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| `tradfi/ohlcv_passthrough.py:89`          | tick_data empty on entry →`_create_full_day_empty_output` (5760-row NaN grid, `market_state=CLOSED`) | **A**    | **Resolved 2026-05-07** (master-plan-audit A2 audit). Banned-placeholder pattern: identical shape to `_create_empty_output` — produces NaN-OHLC rows that pass manifest as `captured`. Delete + replace with `record_empty(empty_confirmed)`. Sibling banned method `_create_closed_market_candle` in `orchestration_writer.py:65` (1-row-per-non-trading-day variant) — same fix shape. Consumer-impact audit: `features-volatility-service` `_filter_market_state` (orchestrator.py:531-558 + volatility_orchestration.py:67-73) and `features-delta-one-service` `_filter_market_state` (orchestrator.py:614-630) currently filter `market_state.isin(["normal", "auction"])` to drop closed/pre/post candles. Filter has TWO roles: (1) drop full-day placeholder rows from these methods (DISAPPEARS after delete — `record_empty` means no parquet to read), (2) drop intra-day pre/post/closed minutes on real trading days from `_apply_market_state` (LEGITIMATE — stays). Consumer refactor: add manifest pre-flight gate (skip `empty_confirmed` days at parquet-load time, never enter `_filter_market_state` for those days); the existing intra-day filter is unchanged. |
| `tradfi/tbbo_adapter.py:73`               | tick_data empty on entry                                                                             | A        |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| `tradfi/tbbo_adapter.py:103`              | tick_data empty after filter                                                                         | B        |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| `tradfi/trades_adapter.py:67`             | tick_data empty on entry                                                                             | A        |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| `tradfi/trades_adapter.py:97`             | tick_data empty after filter                                                                         | B        |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |

**Notable findings**:

- 5 NEW Path C sites in `fx_rate_adapter` not in original plan estimate — 3 distinct error classes (asset detection,
  feature mapping, price-column probe).
- `tradfi/ohlcv_passthrough.py:89` resolved 2026-05-07 as **A (honest absence)** per master-plan-audit A2 — same banned
  placeholder pattern as `_create_empty_output`, plus sibling `_create_closed_market_candle` in
  `orchestration_writer.py:65`. Delete both, replace with `record_empty(empty_confirmed)`, add manifest pre-flight gate
  to `_filter_market_state` consumers (features-volatility + features-delta-one). Phase 2.A scope expansion absorbs both
  deletions.
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
| `candle_processing_service.py:591` | `for prefix in prefixes` per-(date_str, data_type) GCS listing      | (ValueError, TypeError, KeyError, AttributeError, RuntimeError) | GCS listing failure for an entire `(date_str, data_type)` prefix. Silently empty → entire date×data_type shard dropped. No manifest row.                                                             | Reader/infrastructure failure (Category C).`record_failed` at (date_str, data_type) granularity + `ADAPTER_FETCH_FAILED` event before `continue`.                                     |
| `candle_write_mixin.py:141`        | Per-instrument candle write (live orchestration)                    | (OSError, ValueError, RuntimeError, KeyError, TypeError)        | GCS write failure returns `None`. Caller at `live_workers.py:682` does NOT check return — unconditionally increments `total_candles`, appends to `processed_timeframes`. Failure looks like success. | Return-value check at every call site; on `None` `record_failed(...)` with typed `WriteFailedError`. Or consolidate into single canonical writer (preferred).                         |
| `data_sink.py:290`                 | `SyncGCSDataSink.write()` per-instrument (older batch path)         | (ValueError, TypeError, KeyError, AttributeError, RuntimeError) | GCS write failure returns `None`. Callers cannot distinguish success from failure. No `record_failed`.                                                                                               | Same — re-raise typed `WriteFailedError`; let shard-level caller record.                                                                                                              |
| `orchestration_writer.py:413`      | `_write_candles_to_gcs` per-instrument                              | (ValueError, TypeError, KeyError, AttributeError, RuntimeError) | GCS write failure returns `None`. Callers test `if result is None` for the **skip case** (existing file) — error case also returns `None`, indistinguishable.                                        | Same — distinguish skip vs error via typed return / sentinel;`record_failed` on error.                                                                                                |
| `output_writer_service.py:341`     | `OutputWriterService.write_candles` per-instrument                  | (OSError, ValueError)                                           | Same pattern — write fails, returns `None`, callers test for already-exists skip. No `record_failed`.                                                                                                | Same.                                                                                                                                                                                 |
| `live_workers.py:890`              | `_maybe_dispatch_chain_streaming` per chain blob                    | (OSError, ValueError, RuntimeError, KeyError, TypeError)        | Streaming dispatch fails for chain blob — returns `None`, caller falls through to **eager path** as fallback. If eager also fails, shard lost with no record.                                        | Acceptable as first-level fallback within same request. Outer caller must `record_failed` if eager path also produces no output.                                                      |

**MEDIUM severity (per-symbol/per-instrument drops inside aggregate, corrupts completeness)**:

| File:Line             | Loop / context                                                           | Caught                                                          | What is swallowed                                                                                                                                                                                                | Fix shape                                                                                                                                                   |
| --------------------- | ------------------------------------------------------------------------ | --------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `live_workers.py:512` | `for group_value in groups` per-symbol slice in `_iter_chain_symbol_dfs` | (pl.exceptions.ComputeError, OSError, RuntimeError)             | Single symbol's Polars filter fails → silently dropped from chain output. For options_chain / futures_chain, downstream may write**partial-cluster parquet** with missing symbols and no `ClusterCoverageError`. | Per-symbol counter `dropped_symbols`, warn-summary after generator's `finally`. For bundled data_types, feed into cluster-coverage validator (Phase 2.B).   |
| `live_workers.py:773` | `for inst_key in instrument_keys` in `_process_chain_timeframe`          | `Exception` (bare)                                              | `classify_and_emit_error` is called (event emitted) but no per-symbol counter, no warn-summary. N instruments → M fail → M dropped with no aggregate accounting.                                                 | Add `dropped_count` counter + `logger.warning("Dropped %d/%d instruments for %s")` after loop (consistent with `solana_defi_handler.py` `7fedfe5` pattern). |
| `live_workers.py:835` | `for symbol in symbols` in `_process_chain_timeframe_by_symbol`          | `Exception` (bare)                                              | Same as line 773 but legacy-bundle `symbol`-keyed path.                                                                                                                                                          | Same fix.                                                                                                                                                   |
| `live_workers.py:490` | `_iter_chain_symbol_dfs` Polars lazy scan to enumerate groups            | (pl.exceptions.ColumnNotFoundError, pl.exceptions.ComputeError) | Failure to enumerate groups → bare `return` → generator exits yielding 0 symbols → entire chain bundle silently skipped. `ColumnNotFoundError` here is schema-drift bug (Category C).                            | `record_failed` at blob level + classify as Category C (schema drift), not silent skip.                                                                     |

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

| Adapter                              | data_type                                                                                                                                                                                                                         | Write site                                                                                                                                             | Cluster identity                                                                                                                               | `cluster_extractor` recipe                                                                                                                                      | Status                                                                             |     |                                                 |                     |
| ------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- | --- | ----------------------------------------------- | ------------------- |
| Tardis CeFi                          | `options_chain` (Tardis URL alias; canonical `instrument_type=options_chain`, `data_type=trades`)                                                                                                                                 | `tardis_adapter.py:870` `finalise_and_write_cefi_shards`                                                                                               | `underlying` (groupby key) — DERIBIT path additionally splits by `(underlying, quote_asset, margin_type)` for inverse/linear v6 disambiguation | `lambda row: row["underlying"]` — already present per row                                                                                                       | Wire `cluster_extractor` at orchestrator boundary                                  |     |                                                 |                     |
| Tardis CeFi                          | `futures_chain`                                                                                                                                                                                                                   | `tardis_adapter.py:1804` via `finalise_and_write_cefi_shards`                                                                                          | `underlying` per row; expiry-bucket NOT in row schema (front/back/spread cluster)                                                              | **Gap**: derive expiry_bucket from `symbol` parsing (`ESM6` → March 2026 → near-term). Need helper or new column                                                | Schema gap must be closed before cluster gate fires meaningfully                   |     |                                                 |                     |
| Tardis TradFi                        | `options_chain` (via `tradfi_shared.py:296` `_shard_instrument_type_for(OPTION) → options_chain`)                                                                                                                                 | `tradfi_shared.py:450` `write_tradfi_shard`                                                                                                            | `underlying` per row; ES.OPT 11-cluster prefix encoded in `symbol` (E1A/EW1/EOM etc.)                                                          | `lambda symbol: re.match(r'^(E[1-5]A                                                                                                                            | EW[1-4]                                                                            | EOM | ES)', symbol).group(0)` — confirmed extractable | Ready (regex-based) |
| Databento TradFi                     | `options_chain` (via `databento_adapter.py:91` `_PARTITION_INSTRUMENT_TYPE[OPTION]="options_chain"`)                                                                                                                              | `databento_adapter.py:822` `writer.write_chunk(df)` + `_enrich_with_canonical_ids()` at line 869                                                       | `underlying` set at `:981` from `cls.underlying`; weekly-series cluster (E1A/EW1/etc.) in `raw_symbol` prefix                                  | **Gap**: `DatabentoClassification` needs new `root_cluster: str` field. Currently only `underlying` is exposed; weekly-series prefix requires new pattern match | UAC change needed                                                                  |     |                                                 |                     |
| Databento TradFi                     | `futures_chain` (via `:90` `_PARTITION_INSTRUMENT_TYPE[FUTURE]="futures_chain"`)                                                                                                                                                  | Same `databento_adapter.py:822` path                                                                                                                   | `underlying` per row; expiry NOT exposed as column                                                                                             | **Gap**: same as Tardis futures_chain — derive from `raw_symbol`                                                                                                | Schema gap                                                                         |     |                                                 |                     |
| Sports `odds_api_adapter.py`         | **`ODDS_SNAPSHOT` / `ODDS_MOVEMENT` / `ARBITRAGE` data_type strings DO NOT EXIST in current code** — current live data_type = `"trades"` with `instrument_type="odds"`. Plan adds the new strings as part of per-fixture sharding | `orchestrator.py:1780` `instrument_type=odds/data_type=trades/ticks.parquet`; groups by `(bookmaker_key, league_id)` — **NO per-fixture grouping yet** | `bookmaker_key` per row (= `venue` after rename at line 1747)                                                                                  | `lambda row: row["bookmaker"]` — UAC `SPORTS_ODDS_SNAPSHOT` schema confirms `bookmaker` is the cluster identity                                                 | **Blocked**: per-fixture sharding (Phase 2.B line 520) must land first             |     |                                                 |                     |
| `polymarket_adapter.py` (prediction) | Current `"trades"`; future `prediction_canonical_question_group`                                                                                                                                                                  | `polymarket_adapter.py:590` `writer.write_chunk(df)`                                                                                                   | NO canonical_question_group column exists. Current grouping by `underlying` (BTC/ETH/etc.) is informal — written to `underlying` column only   | `lambda condition_id: PREDICTION_GROUPS[condition_id]` — but `PREDICTION_GROUPS = {}` empty                                                                     | **Blocked**: requires UAC canonical_question_group SSOT (Tracked Open Question §1) |     |                                                 |                     |
| `kalshi_adapter.py` (prediction)     | Same as Polymarket                                                                                                                                                                                                                | `kalshi_adapter.py:256` `df["data_type"] = "trades"`                                                                                                   | `instrument_type="prediction"` (note: inconsistency — Polymarket uses `"prediction_market"`)                                                   | Same blocker                                                                                                                                                    | Same blocker                                                                       |     |                                                 |                     |

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

| Table                  | Current schema status                           | Phase 2.D readiness                                       | Risk                                                       |
| ---------------------- | ----------------------------------------------- | --------------------------------------------------------- | ---------------------------------------------------------- |
| `fixture_stats`        | 20 cols, no `match_end_time`                    | Stamped correctly today via `kickoff + 120min` fallback   | MEDIUM —`match_end_time` unsourceable                      |
| `fixture_events`       | 9 cols, no `event_time`                         | Derivable (`kickoff_utc + elapsed_min * 60s`)             | HIGH — needs schema bump +`kickoff_utc` join in normalizer |
| `fixture_lineups`      | 11 cols                                         | Stub not wired (data discarded at `_fetch_runner.py:171`) | CRITICAL — fix stub before Phase 2.D applies               |
| `fixture_player_stats` | 33 cols                                         | Stub not wired (data discarded at `:173`)                 | CRITICAL — fix stub before Phase 2.D applies               |
| `injuries`             | 6 cols, no `report_time`                        | UNSOURCEABLE from any current provider                    | HIGH — blocked indefinitely                                |
| `players`              | 10 cols                                         | Already stamped via `datetime.now(UTC)`                   | LOW —`_FETCH_COMPLETED_AT` is precision improvement        |
| `venues`               | 8 cols, derived inline from fixtures            | Already stamped                                           | LOW                                                        |
| `fixtures`             | 23 cols, has `kickoff_utc` ✓, no `announced_at` | UNSOURCEABLE;`kickoff - 7d` proxy is best achievable      | MEDIUM — remove `announced_at` from Phase 2.D scope        |
| `leagues`              | 6 cols                                          | Already stamped                                           | LOW                                                        |
| `teams`                | 7 cols                                          | Already stamped                                           | LOW                                                        |
| `referees`             | 3 cols, derived inline                          | Already stamped                                           | LOW                                                        |
| `coaches`              | 5 cols                                          | Stub returns empty; no source fetch                       | LOW for stamping; HIGH for data quality                    |
| `standings`            | 15 cols                                         | Already stamped                                           | LOW                                                        |
| `rounds`               | 6 cols                                          | Stub returns empty; no source fetch                       | LOW for stamping; HIGH for data quality                    |

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
- [x] [SCRIPT] P0. `availability_stamping.py` extend with: -
      `stamp_available_at_kickoff_offset(df, kickoff_col="kickoff_utc", minutes=60)` — for lineups -
      `stamp_available_at_post_match(df, kickoff_col="kickoff_utc", duration_min=120, scrape_latency_min=15)` — for
      fixture_stats / fixture_player_stats - `stamp_available_at_event_time(df, event_time_col="event_time")` — per-row
      pass-through, used for fixture_events + injuries (when row has its own time) -
      `stamp_available_at_announcement(df, announced_col="announced_at")` — for fixtures -
      `stamp_available_at_explicit(df, fetch_completed_at: datetime)` — for 8 reference tables [AUDIT 2026-05-07: DONE —
      UTL `unified_trading_library/availability_stamping.py` now exports 5 helpers: `stamp_available_at_lineups` (==
      kickoff_offset), `stamp_available_at_event_time`, `stamp_available_at_post_match`, `stamp_available_at_offset`
      (covers announcement/fixtures), `stamp_available_at_explicit`. Naming differs slightly from plan but behavioural
      surface is complete.]
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
      are reintroduced (grep-based static check; can be fooled but catches the obvious). [AUDIT 2026-05-07: FRESH —
      actionable; no grep against `_create_empty_output|_handle_empty_tick_data` regression in
      unified-trading-library/scripts/quality-gates.sh. ~1 hour to add.]
- [x] [DEP] P0. Bump UTL version (semver-agent handles; do NOT bump manually) on merge. (verified 2026-05-07:
      semver-agent auto-bumped on UTL@958634f9 + UTL@c5c2669e merges) [AUDIT 2026-05-07: STALE — semver-agent auto-fires
      on every merge with feat:/fix: prefix; UTL@958634f9 + UTL@c5c2669e have already shipped post-merge bumps. This
      todo is bookkeeping; close at next push.]

QG between Phase 1A and Phase 2: UTL tests green; UTL pushed to live-defi-rollout; downstream consumers rebuild against
new UTL pinned in workspace-manifest.json.

---

## Phase 1B — UAC SSOTs (parallel with 1A)

> **2026-05-06 progress note**: Phase 0 audit discovered that `ES_OPTIONS_CLUSTERS` (11-cluster taxonomy),
> `extract_es_options_cluster`, and `get_active_es_options_clusters_for_date` (calendar fallback) **already exist** in
> UAC `unified_api_contracts/registry/tradfi_symbology.py:539` — earlier than this plan assumed. The "lift from
> instruments-service" step is therefore a delete-and-delegate: instruments-service
> `reference_data/options_cluster_lookup.py` consumers re-import from UAC; no new SSOT needed for ES.OPT itself.
>
> **2026-05-06 follow-up (Conflict 2 resolution — REVISED 2026-05-06 after architecture re-read)**: The earlier proposal
> to rename `ES_OPTIONS_CLUSTERS` → generic `OPTIONS_CLUSTERS_BY_ROOT` was a misread. The 11-cluster taxonomy (`ES`,
> `EW`, `EW1`-`EW4`, `E1A`-`E5A`, `EOM`) is genuinely ES-specific — driven by the CME futures symbology regex
> (`<root><month-letter><year>` format). Deribit BTC options (`BTC-30JUN24-50000-C`), Solana DEX options, and ETH index
> options have completely different formats — each needs its own extractor regex + cluster taxonomy + active- calendar
> logic, not a shared dispatch over `ES_OPTIONS_CLUSTERS`. **Current naming is correct.** When a second root ships, the
> pattern is sibling symbols: `DERIBIT_BTC_OPTIONS_CLUSTERS` + `extract_deribit_btc_options_cluster` +
> `get_active_deribit_btc_options_clusters_for_date`, plus a per-(data_type, root) lookup at
> `DATA_TYPE_TO_CLUSTER_REGISTRY` so MTDS orchestrator can dispatch on venue/root. No UAC rename ships today; see the
> Amendment F resolution above for the equivalent finding on the orchestrator side (cluster validation already wired for
> ES.OPT; generalisation deferred to 2nd bundle adapter). **Already-shipped (UAC commit `31e9e75` 2026-05-06)**:
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
- [x] [SCRIPT] P0. Lift instruments-service ES.OPT cluster lookup (`reference_data/options_cluster_lookup.py`) to UAC
      `OPTIONS_CLUSTERS` registry. Delete the instruments-service module; update consumers. [AUDIT 2026-05-07: DONE —
      instruments-service `reference_data/options_cluster_lookup.py` no longer exists (deleted); UAC
      `unified_api_contracts/registry/tradfi_symbology.py:539` owns `ES_OPTIONS_CLUSTERS` +
      `extract_es_options_cluster()` + `get_active_es_options_clusters_for_date()`; MTDS orchestrator uses UTL
      `get_active_es_options_clusters_for_date_from_snapshot` which delegates to UAC.]
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

  **§ "Live = batch — same data, different sources"** Live and batch are operational modes of the SAME pipeline. They
  produce identical schemas + identical `data_types` + identical fields. They differ only in WHICH source serves a given
  `(asset_group, data_type)`, because some sources lag others on real-time emission. Historical writes MUST be
  timestamped with the `available_at` we'd actually have in live mode (the source priority registry's top entry's
  emission time, not the canonical historical source's slower archive time). Applies to every asset_group; canonical
  example: sports injuries — historical source may give report_time post-match, but live pipeline scrapes a faster
  source mid-match; historical writes stamp with the live-pipeline-equivalent time, NOT the historical-source post-match
  time.

  **§ "Three-category empty-output decision (MDPS + every per-shard adapter)"** Every condition producing an empty
  result resolves to ONE of: A (source returned 0 ticks → `record_empty`), B (ticks present, all outside requested day →
  `record_failed(UpstreamTimestampBiasError)` + paired upstream MTDS partitioner fix), C (ticks in window, downstream
  calc dropped due to malformed fields → `record_failed(MalformedTickFieldError)`). No fourth category. No silent NaN
  placeholder rows. `_create_empty_output()`-style methods are banned; `base_adapter` does not provide one.

  **§ "Cluster validation mandatory at record_captured"** For any `data_type ∈ UAC.BUNDLED_DATA_TYPES`,
  `record_captured` requires `expected_root_clusters` + `cluster_extractor` kwargs. UTL guard raises
  `MissingClusterValidationError` if absent. QG STEP 5.64 statically walks every `record_captured(` callsite + asserts
  the kwargs are passed when the literal data_type is bundled. Runtime + static enforcement; no opt-out.

  **§ "`available_at` is per-row, write-time, equal to live-pipeline-arrival"** Every shard's parquet contains an
  `available_at` column. Each row's value = when the live pipeline would have actually had that row's information (per
  `UAC.AVAILABILITY_AT_SEMANTICS`). For multi-source data*types, the `UAC.SOURCE_PRIORITY` top entry determines the
  source whose timing is used. NEVER derived at read-time. Stamping helpers:
  `unified_trading_library.availability_stamping.stamp_available_at*\*`. UTL's `record_captured`calls `assert_available_at_present`
  internally.

- [x] [DOCS] P0. Update existing CLAUDE.md "Honest absence vs fake placeholders" section with explicit cross-link to the
      three-category decision; rewrite the "Reader/schema-drift bug" sub-bullet to call out path B (timestamp bias) as a
      distinct sub-class. [AUDIT 2026-05-07: DONE — CLAUDE.md line 309 carries explicit cross-link to
      `codex/02-data/honest-absence-downstream-handling.md`; line 286 "Three-category empty-output decision" rule
      references reason taxonomy + per-service consumer-class audit.]
- [ ] [DOCS] P0. Update `unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md` to inherit the new sections
      (it's a per-repo synced file). [AUDIT 2026-05-07: FRESH — actionable; SUB_AGENT_MANDATORY_RULES.md missing the
      four Phase 1C sections ("Live = batch", "Three-category empty-output decision", "Cluster validation mandatory",
      "available_at is per-row"). ~30 min to copy-paste the canonical text from CLAUDE.md.]
- [x] [SCRIPT] P0. Run `bash unified-trading-pm/scripts/propagation/sync-claude-md-to-all-repos.sh` (or the equivalent)
      so per-repo `CLAUDE.md` mirrors pick up the new sections. [AUDIT 2026-05-07: DONE — verified MDPS
      `.claude/CLAUDE.md` mirror has 2 hits for "Three-category empty-output / live-pipeline-arrival"; sync ran
      successfully.]

QG between Phase 1C and Phase 2: every per-repo `.claude/CLAUDE.md` (or symlink) contains the new sections; validated by
grep.

---

## Phase 2 — Service forward fixes (parallel after 1A+1B+1C)

### Phase 2.A — MDPS forward fixes (delete `_create_empty_output`)

- [x] [SCRIPT] P0. ~~Delete `_create_empty_output` from `app/adapters/base_adapter.py`~~ — base never had one. Instead
      ADDED shared `_make_empty_candle_output()` to `BaseCandleAdapter` as the canonical zero-row factory; per-adapter
      `_create_empty_output()` helpers (the legacy NaN-bar shape) deleted from every migrated subclass. Path A returns
      this shared zero-row CandleOutput; live_workers loop's `.empty` branch routes to `record_empty_for_shard`. Path B
      raises `UpstreamTimestampBiasError`; Path C raises `MalformedTickFieldError`. Both typed errors propagate from UTL
      (added via UTL `record_empty(reason=...)` extension shipped UTL@958634f9). Shipped MDPS@5b52d0b 2026-05-07.
- [x] [SCRIPT] P0. For each of the 37 callsites (16 A / 15 B / 5 C / 2 ambiguous per Phase 0 audit): convert
      `return self._create_empty_output(...)` to `_make_empty_candle_output()` (path A) /
      `raise UpstreamTimestampBiasError` (path B) / `raise MalformedTickFieldError` (path C). Tier 2A sports (4 adapters
      × 9 callsites) shipped MDPS@5b52d0b. Tier 2C cefi (6 adapters × 13 callsites incl. trades_adapter Path C) shipped
      MDPS@b9f9328. Tier 2D defi (4 adapters × 8 callsites incl. fx_rate_adapter 3×C: instrument_id schema gap +
      ASSET_TO_FEATURE registry gap + usd_price column drift) shipped MDPS@80cf141. Tier 2E tradfi (2 adapters × 4
      callsites) shipped MDPS@e9520a0. **Excluded INTENTIONALLY**: `tradfi/ohlcv_passthrough.py:89` uses
      `_create_full_day_empty_output()` — INTENTIONAL closed-market signal, NOT the banned 1440-NaN pattern. Per session
      memory 2026-05-06 audit decision. Total 23-of-37 callsites migrated this writegate session (lower number than
      audit estimate because some "callsites" the audit counted were method definitions, not
      `return self._create_empty_output(...)` invocations).
- [x] [SCRIPT] P0. Update `_handle_empty_tick_data` in `batch_workers.py` + `live_workers.py` to catch all three
      exceptions + route to `record_empty` (path A) / `record_failed(UpstreamTimestampBiasError)` (path B) /
      `record_failed(MalformedTickFieldError)` (path C). **AUDIT-CORRECTION + TEST 2026-05-07 MDPS@f2f5428**: Re-read of
      the orchestration mixin chain confirms path B/C ARE already covered in batch mode — the audit's "NOT yet wired in
      batch_workers run loop" was based on inspecting `batch_workers.py` in isolation and missing the explicit MRO
      override. Actual chain: `BatchOrchestrationMixin._process_files_parallel` (batch_workers.py:314) submits
      `self._process_instrument_file` to a ThreadPoolExecutor; `CandleOrchestrationService._process_instrument_file`
      (orchestration_service.py:87-104) explicitly overrides MRO to call
      `LiveOrchestrationMixin._process_instrument_file`, which invokes `_process_all_timeframes` (live_workers.py:613)
      where the path B/C catch lives at line 780. `batch_workers.py` does NOT (and SHOULD NOT) duplicate the catch —
      that would violate "no double SSOT". `_handle_empty_tick_data` is path-A only by design; path B/C are typed
      exceptions that bubble to the per-timeframe catch in the live mixin's compute loop. **Test gap closed**: 6
      structural regression guards in
      [`tests/unit/test_batch_workers_typed_error_routing.py`](../../../market-data-processing-service/tests/unit/test_batch_workers_typed_error_routing.py)
      — assert the BatchOrchestrationMixin stub raises NotImplementedError, the override exists on
      `CandleOrchestrationService.__dict__`, the override body references `LiveOrchestrationMixin`, `live_workers.py`
      imports the typed errors, `batch_workers.py` does NOT (no double SSOT), and
      `LiveOrchestrationMixin._process_all_timeframes` source contains the catch. Also covered live-mixin-side by
      pre-existing `tests/unit/test_live_workers_typed_error_routing.py`.
- [x] [SCRIPT] P0. **Phase 2.A scope expansion (Phase 0 audit finding 2026-05-06)**: fix prediction empty path silent
      drop. At `live_workers.py:268-271` + `batch_workers.py:199-228`, the prediction asset_group fall-through returns
      `success=True, candles_generated=0` with NO manifest record. Add
      `record_empty(row_key=<full v6 key including     canonical_question_group + market_id>, attempted_at=<now>)` call
      so prediction empties surface in the manifest as honest absence. Coordinate row_key shape with Plan A predictions
      (canonical_question_group + market_id columns land via that plan). Until Plan A lands, use a placeholder row_key
      with current Polymarket per-base_asset shape; reconciler script (Phase 3.A new entry) re-flips these rows once
      Plan A migrates the shape. [AUDIT 2026-05-07: DONE — both `live_workers._process_all_timeframes` (line 759
      `record_empty_for_shard` per timeframe) and `batch_workers._handle_empty_tick_data:230-269` (non-TRADFI
      fall-through `record_empty_for_shard` per (instrument, timeframe) — including prediction) emit `record_empty`
      instead of silent return. Row_key uses placeholder per-base_asset shape per plan note; reconciler in Phase 3.A
      re-flips when canonical_question_group SSOT lands via predictions plan.]
- [x] [SCRIPT] P0. Delete `_write_manifest_records` v3-shape parallel write from `orchestration_service.py:329–388`.
      Single canonical v6 path via `canonical_writer` only. (Resolves parent HANDOVER §"❌ MDPS mismatches" item.)
      Shipped MDPS@e56d0e4 — method body deleted (-110 LOC), call site at line 242 removed, orphan UTL imports
      (`ManifestWriter`, `validate_batch_completeness`) dropped. **AUDIT-CORRECTION 2026-05-07**: the prior
      `**DEFERRED**` annotation worried that `check_shard_freshness` at `orchestration_service.py:160` matched the v3
      summary rows (per-(date, data_type), empty venue + no instrument_id) and that deleting them would force
      every-category re-processing. Re-investigation found that's NOT the case:
      `check_shard_freshness(expected_venues=[<data_type>])` matches on the `data_type` column (UTL `manifest_writer.py`
      ~line 2970) via the `venue == v | data_type == v` union, and the per-instrument rows that
      `canonical_writer.write_candle_parquet` writes for every shard ALREADY populate the `data_type` column. So the
      freshness check sees a fresh shard from per-instrument rows alone — the summary rows were genuinely redundant.
      Regression guard: `tests/unit/test_check_shard_freshness_granular_rows_only.py` (3 tests asserting freshness check
      works correctly with ONLY per-instrument rows present, including the missing-data_type and attempted_failed-only
      branches). Locked in BEFORE the delete so any future regression fails CI loudly.
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
      carries v6-relevant info we missed. [AUDIT 2026-05-07: FRESH — actionable; MDPS canonical_writer schema includes
      v6 columns but per-adapter population not yet audited. Tracked Open Question §3 also covers this. ~3-5 days work.]
- [x] [SCRIPT] P0. Add missing data_types to `_CEFI_TRADFI_DEFI_DATA_TYPES` in `orchestration_scanner.py:46–72`
      (`dex_pool_swaps`, `evm_defi_lending`, `evm_defi_amm`, `staking_yields`). [AUDIT 2026-05-07: DONE —
      `market_data_processing_service/app/core/orchestration_scanner.py:46-83` includes all 4 data_types
      (dex_pool_swaps:57, evm_defi_lending:68, evm_defi_amm:69, staking_yields:70).]
- [x] [SCRIPT] P0. Fix adapter registry imports — add `liquidity`, `market_state`, `fx_rates` to
      `app/adapters/__init__.py` so decorators fire. [AUDIT 2026-05-07: DONE — MDPS@72b2d5f registered missing chain +
      DeFi adapters; `app/adapters/__init__.py:34-36` imports `DefiFxRateAdapter`, `DefiLiquidityAdapter`,
      `DefiMarketStateAdapter`.]
- [ ] [SCRIPT] P0. Wire `expected_root_clusters` + `cluster_extractor` into MDPS chain-bundle write paths
      (futures_chain, options_chain). Use UAC `DATA_TYPE_TO_CLUSTER_REGISTRY` to look up the registry per data_type.
      [AUDIT 2026-05-07: FRESH — actionable; zero `expected_root_clusters` callsites in MDPS (`grep -r
      "expected_root_clusters" market_data_processing_service/` returns empty). MTDS has the wiring at
      orchestrator.py:2155 for ES.OPT only; MDPS chain-bundle adapters need parallel wiring. Couples to MTDS Phase 2.B
      item below.]
- [ ] [TEST] P0. Per-adapter integration test: simulate path A / path B / path C; assert correct manifest verb fires;
      assert NO 1440-row NaN parquet ever lands on disk. [AUDIT 2026-05-07: FRESH — actionable. Migration code shipped
      Tier 2A/C/D/E (MDPS@5b52d0b/b9f9328/80cf141/e9520a0); integration tests verifying the path-routing remain
      unwritten.]
- [ ] [TEST] P0. End-to-end smoke: pick 1 venue × 1 instrument × 1 day across each asset_group; run MDPS; assert
      manifest reflects honest verb; spot-check 1 parquet per data_type; assert OHLC populated where claimed `captured`.
      [AUDIT 2026-05-07: IN-FLIGHT — VMs running 2026-05-07T03:30 UTC are end-to-end live tests (37 VMs
      CeFi/TradFi/Sports). Per the writegate contract they MUST emit honest record_empty/record_captured/record_failed.
      Validation is via deployment-ui post-completion review. Formal automated smoke harness not yet written.]
- [ ] [QG] P0. MDPS quality-gates.sh green. [AUDIT 2026-05-07: FRESH — actionable; depends on resolution of items above.
      Last MDPS QG run: c924410 (auto-pass on push). Workspace-wide QG sweep is Phase 5 item.]

### Phase 2.B — MTDS partitioner validation + cluster wiring

- [x] [SCRIPT] P0. Add write-time partition-key validation to `raw_tick_hive.py`: assert
      `tick.timestamp.date() == day_partition_key` before writing each tick. On mismatch: log + emit
      `RAW_TICK_PARTITION_MISMATCH` event + reject the tick (do NOT write to GCS). Per-instrument shard-level isolation;
      one instrument's mismatch doesn't kill the venue run. [AUDIT 2026-05-07: DONE —
      `market_tick_data_service/raw_tick_hive.py:60-104` `validate_day_partition_alignment()` shipped; raises
      `UpstreamTimestampBiasError` on mismatch. Wired into `engine/orchestrator.py:1008` so writes route through the
      gate.]
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
  - **MTDS reader paths** — wherever a reader keys on `(venue, data_type, date)` for sports, expand the lookup to
    include `fixture_id` (where applicable). Audit + fix in Phase 0.
  - **MDPS sports adapter** — if it consumes MTDS sports parquets keyed by `(bookmaker, league)`, update to read
    per-fixture parquets and aggregate up if needed.
  - **features-sports input pipeline** — `mtds_canonical_reader` and similar must read per-fixture; verify
    per-(asset_group, data_type) reader granularity matches the new writer granularity.
  - **deployment-ui data-status panel** — sports panel surfaces league + proficiency rollups (drill-down view), but the
    underlying shard atom is now per-fixture. UI rolls up per-league for filter view + per-fixture for drill-down.
    Explicitly: `(league_id) → (fixture_id) → (data_type) → leaf_parquet` drill-down path. Phase 4.B picks this up.
  - **Manifest reconciliation** — existing manifest rows with `(bookmaker, league)` shard keys flip to a new shape;
    reconciler script in Phase 3.A handles the migration: read old parquet, split per-fixture, write new parquets, mark
    old `attempted_failed[reason=ShardSchemaMigrated]` for re-attempt under new contract.

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
      fetch_completed_at)`where `fetch_completed_at`    comes from`\_FETCH_COMPLETED_AT[table_name]` cache populated at
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
      nullable`(in `INJURIES_COLUMNS`) — populated when injury fixture's `fixture_events`table contains the injury event; else null. No fallback.     **Successor plan**:`sports_forward_poll_timestamps_2026*<TBD>.plan.md`— captures real-time scraping of announcement, injury report, and match end times from sources that DO expose these (verify per source in that plan's Phase 0). After successor plan lands + retrospective backfill completes, the `\*\_confidence`
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

### Phase 2.E — Expanded reason taxonomy + per-service consumer-class audit (added 2026-05-07)

Operator direction 2026-05-07: the manifest is the single source of truth for "what's there + why what's there is or
isn't there." Two refinements over the original 3-category model in Phase 2.A — codified in
[`codex/02-data/honest-absence-downstream-handling.md` § &#34;Reason taxonomy (codified 2026-05-07)&#34;](../../codex/02-data/honest-absence-downstream-handling.md):

1. **Expanded reason taxonomy.** `empty_confirmed` rows now carry one of: `EXPECTED_HOLIDAY`, `EXPECTED_WEEKEND`,
   `EXPECTED_PAUSED_LEAGUE`, `EXPECTED_PRE_SOURCE_COVERAGE_START`, `EXPECTED_PRE_GENESIS_CHAIN`,
   `EXPECTED_INSTRUMENT_NOT_LISTED`, `EXPECTED_INSTRUMENT_DELISTED`, `EXPECTED_PARTIAL_HALF_DAY`, or
   `SOURCE_RETURNED_ZERO`. Today the manifest writes `error_reason=None` for honest empty, losing the distinction.
2. **No parquet for bad/partial-expected days.** Even when the data is "good but partial" (half-day session), the
   default is NO parquet on disk + manifest row with the reason. Optional exception for partial-expected only when the
   downstream consumer needs the rows directly + the parquet schema is honest about its short row count (no NaN-fill to
   "complete" the day).

Phase 2.A per-adapter migration MUST emit the expanded reason taxonomy. Per-service consumer-class audit (which service
handles which reason how) is the workspace-wide contract; the codex doc Section "Per-service consumer-class audit"
carries the SSOT table.

#### Phase 2.E.1 — UTL contract extension (block-everything; ships before per-service Phase 2.A migration)

- [x] [SCRIPT] P0. Extend `unified_trading_library/manifest_writer.py` `record_empty()` to accept an optional
      `reason: str = ""` kwarg. The reason flows through to the manifest row's `error_reason` column verbatim. UTL
      validates `reason` against a closed set per
      `unified_api_contracts.canonical.crosscutting.honest_coverage.EMPTY_CONFIRMED_REASONS` enum (new); unknown reasons
      raise `UnknownEmptyConfirmedReasonError`. Existing callsites (no `reason` kwarg) continue to work —
      `error_reason=""` preserved for back-compat. Shipped UTL@958634f9 2026-05-07.
- [x] [SCRIPT] P0. New UAC SSOT `unified_api_contracts/canonical/crosscutting/honest_coverage.EMPTY_CONFIRMED_REASONS` —
      `StrEnum` with the 9 reason codes from the codex doc § "Reason taxonomy" matrix. Adding a new reason = adding it
      here AND to the codex doc table AND to the per-service consumer-class audit. Shipped UAC@8867891 2026-05-07.
- [x] [SCRIPT] P0. New UTL helper `record_expected_empty(row_key, reason, attempted_at)` — thin wrapper around
      `record_empty(row_key, reason=reason, attempted_at=attempted_at)` that asserts `reason.startswith("EXPECTED_")` so
      calendar-pre-skip callsites don't accidentally emit `SOURCE_RETURNED_ZERO`. Shipped UTL@958634f9 2026-05-07.
- [x] [TEST] P0. UTL unit tests cover: known reason → row has `error_reason=<reason>`; unknown reason →
      `UnknownEmptyConfirmedReasonError`; `record_expected_empty` rejects non-`EXPECTED_*` reasons. 14 tests in
      `tests/unit/test_manifest_writer_record_empty_reason.py` shipped UTL@958634f9 2026-05-07.
- [ ] [QG] P0. UTL `quality-gates.sh` step asserts every `record_empty(reason=...)` callsite outside UTL passes a reason
      from the closed set (static AST walk, mirrors STEP 5.64's bundled-data_type guard).

#### Phase 2.E.2 — Per-service writer migration (parallel after 2.E.1; one commit per service)

For each writer service in the order MTDS / MDPS / instruments-service / features-_ / ml-_ / strategy / execution:

- [x] [SCRIPT] P0. **Replace orchestrator pre-skip with manifest emission.** Where the orchestrator currently consults
      `venue_trading_calendar` / `KNOWN_COVERAGE_GAPS` / `SOURCE_COVERAGE_START` and skips queueing the shard, replace
      with `record_expected_empty(row_key, reason=EXPECTED_<X>)`. So the manifest carries a row for EVERY
      `(shard_key, day)` in the expected universe — no silent "no row at all" cases. **2026-05-07**: shipped for
      instruments-service@8b5eca3 (TradFi non-trading-day venue + per-venue + SFI pre-coverage-start + SFI known-gap
      sites; new `databento.non_trading_day_reason()` helper) + UAC@2a970c5 (`registry.non_trading_day_reason()` SSOT
      helper + 9 unit tests). MTDS verified consistent — its existing skip-without-row policy aligns with reconciler-
      excludes-from-denominator (no migration needed). features-sports has no calendar pre-skip (consumer-side only).
- [x] [SCRIPT] P0. **Per-adapter A/B/C migration upgrade**: where the original Phase 2.A scope said `record_empty(...)`
      for path A (source returned zero), update to `record_empty(reason=SOURCE_RETURNED_ZERO)` so downstream consumers
      can distinguish "we asked, source had nothing" from "we expected nothing." **2026-05-07**: features-sports@a215e36
      (4 post-fetch sites in batch_handler — TABLE_TO_EXPORT loop + odds_features + derived_features +
      fixture_features). MDPS adapter A/B/C migration shipped 2026-05-07 in Tier 2A/C/D/E (commits
      5b52d0b/b9f9328/80cf141/e9520a0); their A-path uses zero-row CandleOutput (no record_empty call needed).
- [ ] [SCRIPT] P0. **Partial-bundle / cluster-coverage failures**: the existing `ClusterCoverageError` flow under
      `attempted_failed` stays. NEW: where a bundle is legitimately partial because some clusters didn't exist on that
      date (e.g. ES.OPT before a weekly was listed), emit `record_expected_empty(reason=EXPECTED_INSTRUMENT_NOT_LISTED)`
      for the missing-cluster sub-shards instead of `attempted_failed`.
- [x] [TEST] P0. Per-service: feed a calendar-skipped day → assert manifest has the right `EXPECTED_*` row, NOT "no row
      at all." **2026-05-07**: instruments-service `test_process_instruments_tradfi_non_trading_day_writes_manifest`
      asserts `record_expected_empty.call_count > 0` + reason ∈ {EXPECTED_HOLIDAY, EXPECTED_WEEKEND}; UAC
      `test_non_trading_day_reason.py` covers 9 cases of the discriminator helper.

#### Phase 2.E.3 — Per-service downstream-consumer-class audit (parallel after 2.E.2)

For each downstream service, audit the read-path code against the codex SSOT § "Per-service consumer-class audit" table
and fix any drift. The audit produces a yes/no answer per (consumer-class × reason) pair:

- [ ] [AUDIT] P0. **execution-service**: every reading callsite (live trade emission + signal-broadcast) consults
      manifest reason and skips trade for `EXPECTED_*` reasons; alerts + skips for `attempted_failed`. No "trade anyway,
      NaN-fill the price" patterns.
- [ ] [AUDIT] P0. **ml-training-service**: continuous-series training NaN-fills for `EXPECTED_*` AND
      `SOURCE_RETURNED_ZERO`; adds `data_quality_flag` column for `attempted_failed` rows so the model can learn to
      discount.
- [ ] [AUDIT] P0. **ml-inference-service**: same as training for `EXPECTED_*`; **blocks inference** for
      `attempted_failed` (live model can't infer through gaps).
- [ ] [AUDIT] P0. **features-volatility / features-cross-instrument / features-onchain — rolling-window calcs**: keep
      window size, adjust denominator for `EXPECTED_*` + `SOURCE_RETURNED_ZERO`, skip + emit
      `record_empty(reason=NO_INPUT_AVAILABLE)` for `attempted_failed`. Calc output carries `n_valid` sibling column.
- [ ] [AUDIT] P0. **features-\* — same-day single-sample calcs**: NaN-fill output OR emit
      `record_empty(reason=NO_INPUT_AVAILABLE)` (per-calc choice; document in calc docstring).
- [ ] [AUDIT] P0. **features-cross-instrument — paired/cross-leg calcs**: if EITHER leg `empty_confirmed`, emit
      `record_empty(reason=LEG_ABSENT_<which>)`; if EITHER leg `attempted_failed`, propagate
      `record_failed(reason=UPSTREAM_LEG_FAILED)`.
- [ ] [AUDIT] P0. **strategy-service backtest mode**: allocator skips the asset for that allocation cycle on any absence
      (forgiving — reconstructing history). Live mode: skip + alert for `attempted_failed`.
- [ ] [AUDIT] P0. **batch-live-reconciliation-service**: both sides should agree on absence reason; if one side has data
      and the other has `EXPECTED_*` with same reason, no flag; if reasons differ OR one side has data and the other has
      `attempted_failed`, flag.
- [ ] [TEST] P0. End-to-end smoke: pick 1 venue × 1 instrument × 7 days with a mix of (`captured` / `EXPECTED_HOLIDAY` /
      `SOURCE_RETURNED_ZERO` / `attempted_failed[ClusterCoverageError]`); run features-onchain rolling APY → assert
      `n_valid` per output row matches the expected (7 - n_excluded); run ml-training → assert NaN-fill +
      `data_quality_flag` shape; run execution → assert correct skip/trade decisions; run reconciliation → assert
      reason-agreement check.

#### Phase 2.E.4 — Update CLAUDE.md "Three-category empty-output decision" rule

- [ ] [DOCS] P0. CLAUDE.md "Three-category empty-output decision" section: update to reference the expanded taxonomy +
      the codex doc § "Reason taxonomy" + the per-service consumer-class audit. The 3-category model stays as the
      WRITE-side discipline (path A/B/C); the reason taxonomy is the EXPRESSION of those categories + the
      calendar-pre-skip cases as structured manifest rows.
- [ ] [DOCS] P0. CLAUDE.md cross-link from "Honest absence vs fake placeholders" → codex doc § "Reason taxonomy" and §
      "Per-service consumer-class audit."
- [ ] [SCRIPT] P0. Run `bash unified-trading-pm/scripts/propagation/sync-claude-md-to-all-repos.sh` so all repos see the
      updated rule.

---

## Phase 3 — Retrospective migration (after Phase 2 lands)

The whole point of Phase 3 is: existing on-disk parquets + manifest rows that were written under the old (buggy)
contract get corrected, so the post-merge backfill % means real %. No silent "old data still lies, new data is honest"
split.

### Phase 3.A — Manifest reconciliation scripts

- [x] [SCRIPT] P0. `mdps_reconcile_1440_nan_placeholders.py` — scan every MDPS-written parquet under
      `gs://{pid}-mdps-*/raw_candle_data/`; for each file, compute `nan_ratio_per_column` for OHLC columns; if all 4 of
      (open, high, low, close) are >95% NaN AND row_count == n_candles → flip manifest row from `captured` to
      `attempted_failed[reason=EmptyPlaceholderBugBackfill]`. Per-VM shard write (manifest concurrency rule).
      Idempotent + dry-run + scoped by `--asset-group` / `--data-type`. Re-attempt happens via existing MDPS backfill
      flow once Phase 2.A lands. Shipped MDPS@d3be0ef 2026-05-07.
- [x] [SCRIPT] P0. `mtds_reconcile_partial_bundles.py` — for every `data_type ∈ BUNDLED_DATA_TYPES` with on-disk
      parquets, count clusters per UAC registry; if observed clusters < expected → flip manifest from `captured` to
      `attempted_failed[reason=ClusterCoverageError(historical)]` with the missing cluster set in the error_reason
      payload. Handles options_chain (ES.OPT 11-cluster), futures_chain. sports_fixture_bundle +
      prediction_canonical_question_group are deferred (script returns exit 3 + RECONCILER_FAILED event with
      `reason=data_type_deferred`) until predictions Phase 1A + sports Phase 2.B's lifecycle SSOT lands. Shipped
      MTDS@ba5423f 2026-05-07.
- [x] [SCRIPT] P0. `mtds_reconcile_partition_mismatch.py` — scan a sample of raw*tick parquets; for each instrument's
      parquet under `day=YYYY-MM-DD`, check if any tick's `timestamp.date()` differs from the partition key. Stats-only
      first (count mismatches per venue / data_type / day); flag for human review before flipping any manifest rows
      (this is upstream-bug detection, not data-quality fix). Shipped MTDS@a32433b —
      `scripts/mtds_reconcile_partition_mismatch.py` (454 lines). Walks
      `raw_tick_data/by_date/day=*/...`via     ThreadPoolExecutor + pyarrow column-only reads; samples up to`--sample-size`rows (default 1000) per parquet and     counts ticks whose`tick_timestamp.date()`differs from the path partition`day=`. Probes 7 candidate timestamp     column names (`timestamp`/`ts`/`tick_timestamp`/`event_timestamp`/`block_timestamp`/`trade_timestamp`/    `kline_timestamp`); skips parquets without one. Output: CSV report at     `$TMPDIR/mtds-partition-mismatch-{asset_group}-{ts}.csv`+ top-20`(venue,
      data_type,
      day)`aggregate logged for     operator quick-look. **Stats-only by design** — does NOT flip manifest rows. Operator decides remediation     (typically: launch MTDS gapfill VM for the high-mismatch_pct tuples). RECONCILER*\* events emitted via UTL     log_event. Filters:`--asset-group
      {cefi,defi,tradfi,prediction}`+ optional`--venue`/`--data-type`/`--day` for incremental review. Smoke-verified
      module loads + asset_group set + timestamp probe order.
- [x] [SCRIPT] P0. `features_sports_reconcile_available_at.py` — for every features-sports parquet on disk, check if
      `available_at` column present + populated correctly per the new UAC semantic. If missing or wrong → flip manifest
      from `captured` to `attempted_failed[reason=MissingAvailableAt]`. Re-attempt happens via Phase 2.C re-run. Shipped
      features-sports@f123069 — `scripts/features_sports_reconcile_available_at.py` (462 lines). Walks
      `sports_features/by_date/day=*/...` parquets via pyarrow footer reads; flips when the column is absent OR 100%
      null. Empty parquets with the column present are treated as honest-empty, not flipped. Default scan-only;
      `--apply-flips` requires `MANIFEST_PER_VM_SHARDS=true` + `VM_NAME` (verified guards fire with exit 4).
      RECONCILER\_\* events, CSV audit, `--max-flips-per-run` 100k halt safety. Smoke-verified path parser handles both
      per-league (`league={id}/feature_group={fg}/...`) and bare (`feature_group={fg}/...`) layouts.
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

### Phase 3.D — Expanded-reason backfill (added 2026-05-07 — operator gap finding)

**Why this exists.** Phase 2.E.1 ships UTL `record_empty(reason=...)` so NEW writes carry the expanded reason taxonomy.
But existing manifest rows have `error_reason=None` for honest empty, and calendar-pre-skipped days have NO row at all.
Without a retrospective backfill, the per-service consumer-class audit (NaN-fill for `EXPECTED_HOLIDAY`, etc.) only
works for new data — historical reads land on rows the consumer can't classify.

The fix is **two-layer defensive**:

1. **Retrospective backfill** (this Phase 3.D) — populate the manifest with reasons for every historical row + generate
   missing rows for the calendar-pre-skip cases.
2. **Reader-side fallback** (codified in the codex doc — see § "Reader-side fallback for legacy rows") — every consumer
   service implements: "if `error_reason` is empty, consult `venue_trading_calendar` / `SOURCE_COVERAGE_START` /
   `KNOWN_COVERAGE_GAPS` / instrument-listing windows to classify on the fly." This makes the consumer code robust
   during migration AND future-proofs against any new asset_group whose backfill hasn't run yet.

#### Phase 3.D.1 — `reconcile_expected_absence_reasons.py` per asset_group

- [x] [SCRIPT] P0. ~~New script per asset_group~~ → **single script with `--asset-group` dispatch + per-asset-group
      classifier functions** shipped 2026-05-07 at `instruments-service/scripts/reconcile_expected_absence_reasons.py`
      (commit `1f93745`). Iterates manifest rows directly (not "expected universe enumeration") — focus is on the
      empty_confirmed-AND-null-reason subset which is the highest-leverage pass. Expected-universe enumeration for "no
      row at all → record_expected_empty" deferred to Phase 3.D.1 v2 (needs cross-bucket join with instruments-service
      catalog + lifecycle). Uses UAC SSOTs: `non_trading_day_reason()` (TradFi) + `is_in_known_gap()` /
      `get_source_coverage_start()` (sports) + `get_chain_genesis_date()` (DeFi). Smoke-verified classifiers with
      synthetic rows.
- [x] [SCRIPT] P0. Decision matrix for empty_confirmed-AND-null-reason rows shipped (the highest-leverage pass).
      Classification: TradFi → EXPECTED_HOLIDAY/WEEKEND via `non_trading_day_reason`; Sports → EXPECTED_PAUSED_LEAGUE
      via `is_in_known_gap` / EXPECTED_PRE_SOURCE_COVERAGE_START via `get_source_coverage_start`; DeFi →
      EXPECTED_PRE_GENESIS_CHAIN via `get_chain_genesis_date` (handles both `chain=` column AND legacy combined
      `venue=PROTOCOL-CHAIN` suffix); CeFi/prediction default to SOURCE_RETURNED_ZERO. Captured + typed-failed rows left
      alone. **Deferred to v2**: "no row at all → record_expected_empty" path — requires expected-universe enumeration
      via cross-bucket join with instruments-service catalog (much larger surface).
- [x] [SCRIPT] P0. Same safety scaffolding as `reconcile_1440_nan_placeholders.py`: default scan-only mode,
      `--apply-flips`, `--max-flips-per-run` default 100k, `MANIFEST_PER_VM_SHARDS=true` + `VM_NAME` required for apply
      (verified guard fires), RECONCILER\_\* lifecycle events with structured details, CSV audit at
      `${TMPDIR}/recon-reasons-{asset_group}-{ts}.csv`, distribution summary printed for operator review before write.
      Per-VM shard write at `_index/per_vm/{VM_NAME}.parquet` — consolidator merges into canonical manifest.
- [x] [SCRIPT] P0. Idempotent — `_build_null_reason_mask` only matches rows with empty `error_reason`; re-runs after a
      flip find 0 candidates and no-op. Classifier functions are pure (deterministic on input).
- [x] [TEST] P0. Per-asset-group unit test on a fixture day-set covering each branch of the decision matrix
      (UTL@c5c2669e — `tests/unit/test_legacy_reason_classifier.py` 19 unit tests covering every classifier branch
  - closed-set output guarantee. Single SSOT shared with read-side fallback.)

#### Phase 3.D.2 — Reader-side fallback in every consumer service

- [x] [SCRIPT] P0. New helper in UTL: `classify_legacy_empty_row(asset_group, row) -> str` — consults the same
      calendar/coverage SSOTs the writer uses. Returns one of the `EXPECTED_*` or `SOURCE_RETURNED_ZERO` codes.
      (UTL@c5c2669e + instruments-service@21aef51 — Tier 3D.1 reconciler refactored to import from this single SSOT,
      killing the 116-LOC inline duplicate.)
- [x] [SCRIPT] P0. Per-consumer-service: when reading a manifest row with `capture_status=empty_confirmed` AND
      `error_reason` empty, call `classify_legacy_empty_row(...)` to derive the reason at read time. Apply the
      consumer-class audit rule (NaN-fill / skip / etc.) using the classified reason. (deployment-api@176c599 —
      `_gcs_metadata` + `lookup_capture_status_for_shard` both wired. **Audit finding**: the other 7 services in the
      original list — execution-service / ml-training-service / ml-inference-service / strategy-service /
      features-volatility / features-cross-instrument / features-onchain — do NOT directly read `capture_status` /
      `error_reason` columns from the manifest in production code paths. They consume manifest state via UTL
      `check_data_available` / `check_shard_freshness` / `dependency_check` helpers, and the empty_confirmed branching
      they need is presence/absence-of-row, not reason-of-empty. So deployment-api is the only consumer service that
      surfaces `error_reason` in a UI-visible way; wiring it covers the operator-visible fallback. The features-\*
      services have a `scripts/smoke_matrix.py` that mentions `capture_status` but it's a smoke-test harness, not a
      production read site.)
- [x] [TEST] P0. Per-consumer test: feed a legacy row (no `error_reason`) → assert reader applies the right
      consumer-class action. (deployment-api@176c599 — `tests/unit/test_legacy_reason_classifier_wiring.py` 8 tests
      covering both wired sites with TradFi weekend / DeFi pre-genesis / sports pre-source-coverage-start /
      preserve-existing-reason / asset_group=None backwards compat / unknown asset_group skip / captured-row skip /
      mocked manifest read.)

#### Phase 3.D.3 — Operator runbook + sequencing

The retrospective backfill is potentially several million row writes per asset_group (TradFi alone has ~190k
weekend/holiday rows over 5 years; CeFi has ~few hundred chain-genesis rows; DeFi has ~few thousand chain-pre- genesis
rows; sports has ~thousands of paused-league rows). Operator decision per asset_group on when to run `--apply-flips`:

- [ ] [DOCS] P0. Document the per-asset-group expected backfill volume in
      `unified-trading-pm/codex/02-data/expected-absence-backfill-runbook.md`. Operator picks scan-only first to verify
      volume, then `--apply-flips` per asset_group sequentially.
- [ ] [DOCS] P0. Cross-link from the codex § "Reason taxonomy" matrix → Phase 3.D backfill script + reader-side fallback
      helper.

QG between Phase 3.D and Phase 4: every asset_group's backfill scan-only run reviewed; reader-side fallback unit-tested;
per-consumer integration tests demonstrate same downstream behaviour for legacy + new manifest rows.

#### Phase 3.D.4 — Expected-universe enumerator v2 (NEW 2026-05-07 — operator directive)

> **2026-05-07 expected-universe enumerator `--apply-write` sweep (Phase 3.D.4) — ALL 5 asset_groups committed. Total
> rows written: 1,455,901.**
>
> | asset_group | VM name                                             | state       | rows written | distribution                                                                                        |
> | ----------- | --------------------------------------------------- | ----------- | -----------: | --------------------------------------------------------------------------------------------------- |
> | tradfi      | `expected-universe-enum-tradfi-20260507-154607`     | **WRITTEN** |       35,033 | 32,825 `EXPECTED_WEEKEND` + 2,208 `EXPECTED_HOLIDAY`                                                |
> | sports      | `expected-universe-enum-sports-20260507-154819`     | **WRITTEN** |       13,176 | 13,176 `EXPECTED_PRE_SOURCE_COVERAGE_START`                                                         |
> | cefi        | `expected-universe-enum-cefi-20260507-154922`       | **WRITTEN** |      119,152 | 119,152 `EXPECTED_PRE_VENUE_LAUNCH` (NEW reason — UAC@ac218dc) across 13 post-2018 venues           |
> | prediction  | `expected-universe-enum-prediction-20260507-155030` | **WRITTEN** |        2,280 | 2,280 `EXPECTED_PRE_VENUE_LAUNCH` (POLYMARKET 974 + KALSHI 1306) — UAC@ac218dc                      |
> | defi        | `expected-universe-enum-defi-20260507-155353`       | **WRITTEN** |    1,286,260 | 688,220 `EXPECTED_PRE_GENESIS_CHAIN` + 598,040 `EXPECTED_INSTRUMENT_NOT_LISTED` (protocol launches) |
>
> **Total rows merged into per-VM shards: 1,455,901.** Consolidator daemon merges per-VM shards into canonical
> `_index/availability_index.parquet` within ~5min of each VM shutdown.
>
> **What changed since the scan-only sweep earlier today (PM@dae6d40d):**
>
> - UAC@ac218dc — added `EXPECTED_PRE_VENUE_LAUNCH` to `EmptyConfirmedReason` enum + new
>   `unified_api_contracts.registry.venue_launch_dates` SSOT (20 CeFi venues + 2 Prediction venues).
> - instruments-service@d1c9928 — replaced CeFi + Prediction enumerator stubs with real per-venue pre-launch
>   implementations using the new SSOT. Bumped `--max-writes-per-run` default from 100k to 1M.
> - deployment-service@38b7a58 — launcher accepts a third positional arg passing through to `--max-writes-per-run` so
>   cap-bumped reruns don't need ad-hoc launchers.
>
> **DeFi cap-bump path:** the first `--apply-write` defi VM (`-145024`) also hit the 1M default cap — DeFi's true
> universe is ~1.28M absent rows. Re-launched (`-155353`) with the new launcher's third positional arg `5000000`
> (deployment-service@38b7a58 pass-through) and completed cleanly in 26.3s. The default 1M cap stays in place as a
> halt-safety; operators bump per-asset-group when the universe genuinely exceeds it.
>
> **Per-VM shard isolation** (`MANIFEST_PER_VM_SHARDS=true` + `VM_NAME=…`) is wired into the launcher metadata for every
> run. All VMs ran on `asia-northeast1-c` `e2-standard-4` + 50GB and auto-shut down on completion. Per-VM shard upload
> paths logged on each ENUMERATOR_COMPLETED event:
> `gs://market-data-tick-{asset_group}-{pid}/_index/per_vm/expected-universe-enum-{asset_group}-{ts}.parquet` (sports
> uses `instruments-store-sports-{pid}` instead).

**Why this exists.** Phase 3.D.1 reconciler stamps reasons on `empty_confirmed AND error_reason IS NULL` rows (legacy
backfill), but does **NOT enumerate the expected universe** — tuples that have NO manifest row at all stay absent. This
leaves the rollup-vs-drilldown denominator gap open (per
[`codex/02-data/availability-manifest-and-data-status.md`](../../codex/02-data/availability-manifest-and-data-status.md)
§ "Rollup-vs-drilldown denominator divergence (codified 2026-05-07)"). To close the gap, every expected
`(shard_key, day)` MUST have a manifest row.

**Operator directive 2026-05-07**: _"if needs be, we can just write the manifest with every single entry as
not-attempted or something that's not the same as empty, so that all the possible combinatorics are already reflected in
the manifest. Use that to plug in the gaps... so that the manifest not having an entry literally means it's not
relevant."_ The workspace already has the equivalent structure (`empty_confirmed + error_reason=EXPECTED_*`); this
sub-phase ships the enumerator that physically writes those rows.

**Scope per asset_group** (cross-product over UAC SSOTs + service catalogs):

| Asset group | Expected-universe inputs                                                                                                                                                                                                | Expected backfill volume                                    |
| ----------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------- |
| DeFi        | UAC `CHAIN_GENESIS_DATES` × instruments-service protocol catalog × UAC `DATA_TYPES_BY_ASSET_GROUP['defi']` × dates(2018-01-01 → today). Per-(chain, protocol, data_type) clip at `max(chain_genesis, protocol_launch)`. | ~few thousand pre-genesis rows per chain × N chains         |
| Sports      | UAC `SOURCE_COVERAGE_START` / `DATA_TYPE_COVERAGE_START` × leagues catalog × `is_in_known_gap` filter × `SPORTS_DATA_TYPE_TO_FOLDER` × dates                                                                            | ~thousands of paused-league + pre-coverage rows per source  |
| TradFi      | UAC `venue_trading_calendar` × instruments-service catalog × UAC `DATA_TYPES_BY_ASSET_GROUP['tradfi']` × dates                                                                                                          | ~190k weekend/holiday rows over 5 years (already partly on) |
| CeFi        | Instrument lifecycle (`available_from` / `available_to` / `expiry`) × venue × UAC `DATA_TYPES_BY_ASSET_GROUP['cefi']` × dates                                                                                           | ~few hundred lifecycle-bound rows per venue                 |
| Prediction  | Market lifecycle (`market_created_at`, `settlement_time`) × UAC `PREDICTION_GROUPS` registry × dates                                                                                                                    | depends on prediction-canonical rollout (Phase 2.E.5 dep)   |

**Tasks** — sequential per asset_group (DeFi first per operator priority — multi-chain coverage the most user-visible).

- [x] [SCRIPT] P0 (shipped instruments-service@8e404c8). NEW
      `instruments-service/scripts/enumerate_expected_universe.py` — accepts
      `--asset-group {defi | sports | tradfi | cefi | prediction}` flag, walks the asset*group's expected universe per
      the matrix above, reads the canonical manifest ONCE (manifest concurrency principle), filters to tuples with NO
      manifest row, writes
      `record_expected_empty(reason=EXPECTED*\*)`rows via UTL`record_expected_empty`helper.     Default scan-only (CSV report);`--apply-write`requires`MANIFEST_PER_VM_SHARDS=true`+`VM_NAME=...`per the     per-VM shard isolation rule.`--max-writes-per-run`default 100k halt safety. Mirrors the safety scaffolding of    `reconcile_expected_absence_reasons.py`.
- [ ] [SCRIPT] P0. Per-asset-group reason classifier dispatch — DeFi → `EXPECTED_PRE_GENESIS_CHAIN` +
      `EXPECTED_INSTRUMENT_NOT_LISTED`; Sports → `EXPECTED_PAUSED_LEAGUE` + `EXPECTED_PRE_SOURCE_COVERAGE_START`; TradFi
      → `EXPECTED_HOLIDAY` / `EXPECTED_WEEKEND` / `EXPECTED_PARTIAL_HALF_DAY`; CeFi → `EXPECTED_INSTRUMENT_NOT_LISTED` +
      `EXPECTED_INSTRUMENT_DELISTED`. Reuses UTL `classify_legacy_empty_row` SSOT (single classifier, both reconciler +
      enumerator import from UTL).
- [x] [SCRIPT] P0 (shipped deployment-service@dcc5c87). NEW
      `deployment-service/scripts/vm/launch-expected-universe-enumerator-vm.sh` — follows
      `launch-defi-phantom-recon-vm.sh` pattern (singleton lock per `expected-universe-enum-` prefix in
      `asia-northeast1-c`, `e2-standard-4` + 50GB, `VM_TASK=expected-universe-enum` metadata routes through the
      `mdps-backfill | features-backfill | phantom-recon | expected-universe-enum` elif in `setup-data-pipeline-vm.sh`).
      Added `expected-universe-enum-` prefix to `deployment-service/scripts/vm/vm_zombie_watchdog.py`
      `VM_PREFIX_TO_BUCKET` (heartbeat-only `None` — script writes per-VM manifest shards, no per-asset-group bucket
      signal needed). Watchdog VM relaunched (`vm-zombie-watchdog-20260507-145047`) so the new prefix is live.
      Tarballs + setup-data-pipeline-vm.sh refreshed via `create-code-tarballs.sh --all` (2026-05-07 13:49 UTC).
- [ ] [TEST] P0. Per-asset-group unit test on a fixture day-set covering each branch of the enumerator's classifier
      dispatch. Test the cross-product enumeration shape (right rows present, wrong rows absent) with mocked manifest +
      UAC SSOT fixtures.
- [x] [VM-LAUNCH] P0 (scan-only + `--apply-write` complete — see banner table above; PM@79e47874). DeFi scan-only first
      halted on the default `--max-writes-per-run=100000` cap (`expected-universe-enum-defi-20260507-145714`, rc=5 +
      `ENUMERATOR_FAILED reason=max_writes_exceeded`). Default raised to 1M (instruments-service@d1c9928) and launcher
      cap pass-through shipped (deployment-service@38b7a58); the second `--apply-write` run still hit 1M, so a third run
      with `5000000` via the new pass-through completed cleanly in 26.3s on
      `expected-universe-enum-defi-20260507-155353` — final 1,286,260 rows (688,220 `EXPECTED_PRE_GENESIS_CHAIN` +
      598,040 `EXPECTED_INSTRUMENT_NOT_LISTED`). Per-VM shard merged into canonical 18:07 UTC after consolidator P0 fix
      shipped (PM@341bb285 + instruments-service@a936a28).
- [x] [VM-LAUNCH] P0 (scan-only + `--apply-write` complete for tradfi / sports / cefi / prediction; PM@79e47874). Per
      the banner table above: - **TradFi** — 35,033 rows written (32,825 `EXPECTED_WEEKEND` + 2,208 `EXPECTED_HOLIDAY`)
      on `expected-universe-enum-tradfi-20260507-154607`. - **Sports** — 13,176 rows written (all
      `EXPECTED_PRE_SOURCE_COVERAGE_START`) on `expected-universe-enum-sports-20260507-154819`. - **CeFi** — 119,152
      rows written (real impl per UAC@ac218dc + instruments-service@d1c9928, no longer a stub: all
      `EXPECTED_PRE_VENUE_LAUNCH` across 13 post-2018 venues) on `expected-universe-enum-cefi-20260507-154922`. -
      **Prediction** — 2,280 rows written (real impl per UAC@ac218dc + instruments-service@d1c9928: POLYMARKET 974 +
      KALSHI 1306 `EXPECTED_PRE_VENUE_LAUNCH`) on `expected-universe-enum-prediction-20260507-155030`. Per-instrument
      lifecycle (`PREDICTION_GROUPS` registry) tracked separately under `predictions_master_2026_05_07.plan.md`. Each VM
      emitted ENUMERATOR_STARTED + ENUMERATOR_COMPLETED + auto-shut down. Consolidator cycles 18:07-18:14 UTC merged all
      5 per-VM shards into canonical (cefi/sports clean throughout; tradfi/defi/prediction unblocked at PM@341bb285
      after the `ArrowTypeError` on `instrument_count` was patched).
- [ ] [VERIFY] P0. Operator-side rollup-vs-drilldown spot-check on 3-5 (venue, data_type) tuples in deployment-ui — with
      all 5 per-VM shards now merged into canonical (consolidator unblocked at PM@341bb285), the rollup % and drilldown
      % should agree within rollup cache TTL (~5 min). Pending the operator pass on the data-status panel. Fine-grained
      per-instrument lifecycle (cefi instrument-listed-since / prediction `PREDICTION_GROUPS` per-day) is the v2
      universe in Phase 3.D.5 below, not Phase 3.D.4.
- [x] [DOCS] P0 (shipped 2026-05-07, PM@5e8f8ca6). Updated
      [`codex/02-data/expected-absence-backfill-runbook.md`](../../codex/02-data/expected-absence-backfill-runbook.md)
      from PLANNED stub to SHIPPED runbook: documents both passes (reconciler + enumerator), per-asset-group volumes
      table (1,455,901 total rows), scan-only / apply-write recipe, verification protocol (events + per-VM shard +
      canonical merge spot-check), operational hazards (cap-bump for DeFi, per-VM shard isolation requirement,
      dtype-correct fill-default fix), re-run cadence, open follow-ups.
- [x] [DOCS] P0 (shipped 2026-05-07, PM@5e8f8ca6). Marked
      [`codex/02-data/availability-manifest-and-data-status.md`](../../codex/02-data/availability-manifest-and-data-status.md)
      § "Rollup-vs-drilldown denominator divergence" "Half 2 — Backward-fill" sub-section as **SHIPPED** with VM
      commit shas (PM@79e47874 + PM@341bb285) + spot-check evidence (DeFi 688,220 EXPECTED_PRE_GENESIS_CHAIN sample
      `chain=ARBITRUM venue=AAVEV3-ARBITRUM day=2018-01-01`; TradFi 35,050 EXPECTED_WEEKEND sample
      `venue=BARCHART day=2018-01-06`).

**QG between Phase 3.D.4 and Phase 4**: every asset_group's enumerator scan-only run reviewed by operator;
`--apply-write` produces convergent rollup-vs-drilldown percentages on spot-checked tuples; codex doc updated to reflect
shipped state.

**Cost estimate per asset_group VM**: ~e2-standard-4 + 50GB + 30-60min runtime ≈ $0.50-$1.00 per VM. Total
five-asset-group sequence ≈ $5 + ~3hr operator time. Cheap relative to the operator-time savings from honest rollup
percentages.

**Successor / co-ordination**: Phase 3.D.4 is paired with the per-asset-group **forward-write** Phase 2.E.2 work already
in flight — once both halves ship per asset_group, that asset_group's denominator is closed permanently.

#### Phase 3.D.4 — Open follow-ups discovered during 2026-05-07 scan-only sweep

The all-5-asset_group scan-only sweep surfaced three follow-up items not covered in the original Phase 3.D.4 task list:

- [x] [SCRIPT] P0 (shipped 2026-05-07, instruments-service@d1c9928). **DeFi cap bump.** Default `--max-writes-per-run`
      raised from 100k to 1M. `--apply-write` defi run still hit 1M cap (true universe ~1.286M rows); relaunched with
      `5000000` via the new launcher pass-through (next item). Final defi written count: 1,286,260 rows (688,220
      EXPECTED_PRE_GENESIS_CHAIN + 598,040 EXPECTED_INSTRUMENT_NOT_LISTED).
- [x] [SCRIPT] P0 (shipped 2026-05-07, deployment-service@38b7a58). **Launcher pass-through for
      `--max-writes-per-run`.** Third positional arg on `launch-expected-universe-enumerator-vm.sh` validates as
      positive integer + appends `--max-writes-per-run <N>` to `BACKFILL_CMD`. Empty/missing falls through to script
      default (1M). Used to ship the defi 5M-cap rerun without an ad-hoc launcher.
- [ ] [SCRIPT] P1. **CSV report upload to GCS before VM auto-shutdown.** The enumerator writes its CSV report to
      `tempfile.gettempdir()` (i.e. `/tmp` on the VM), which is local disk and is destroyed when
      `VM_SHUTDOWN_ON_COMPLETION=true` self-deletes the VM. Operator can read distribution-by-reason from the events
      log + run.log (those persist), but row-by-row inspection requires SSH-before-shutdown which is a race. Add a
      `--gcs-report-bucket` flag to the script (or environment-driven) so the CSV gets uploaded to
      `gs://deployment-scripts-{pid}/enumerator-reports/{vm_name}/<asset_group>-<ts>.csv` before exit. Low priority
      because the events log already captures the distribution; needed only if the operator wants to inspect specific
      candidate rows.

#### Phase 3.D.5 — Instruments-service-driven enumeration v2 (NEW 2026-05-07 — operator architectural directive)

**User directive 2026-05-07 (post Phase 3.D.4 apply-write completion):**

> "are all our mtds asset groups only checking for missing data based on what instruments are declared in instruments
> services? this should be the convention"
>
> "for odds api in mtds i guess equivalent is checking fixtures that exist in fixtures (that's originally come from API
> Football, but we just get them from GCS.)"

**The architectural model.** The `(instruments-service catalog) × (data_types) × (dates_in_window)` cross-product IS the
expected universe — at every per-(venue, instrument_id, day) grain. Today's Phase 3.D.4 enumerator covers the **coarse
"venue/chain/source didn't exist yet"** layer (38,033 tradfi calendar rows + 13,176 sports pre-coverage rows + 119,152
cefi pre-venue-launch rows + 2,280 prediction pre-venue-launch rows + 1,286,260 defi pre-genesis-and-pre-protocol-launch
rows = **1,455,901 total**). It does NOT yet enumerate the **fine-grained per-instrument lifecycle** (instrument
listed/delisted/expired) which is much larger and requires reading the per-asset-group instruments-service catalog.

**v1 (shipped today)** is honest as far as it goes — it correctly marks every coarse "didn't exist yet" tuple. **v2
(this phase)** layers per-instrument lifecycle on top so EVERY `(asset_group, venue, data_type, instrument_id, day)`
tuple in the manifest's expected universe is either `captured` / `empty_confirmed` / `attempted_failed` — no silent
absence.

**Convention to codify in CLAUDE.md after this phase ships:** _"MTDS missing-data checks for any asset_group MUST derive
their expected universe from the instruments-service catalog for that asset_group, NOT from inline / hardcoded lists.
Adding a new venue / data_type / instrument anywhere in the workspace = adding it to the instruments-service catalog
(the SSOT) and the enumerator picks it up automatically next run."_

**Per-asset-group catalog read sources (the SSOT inputs to v2 enumeration):**

| asset_group | catalog source                                                                                                               | shard atom (per CLAUDE.md)                                                              | per-instrument lifecycle fields                                                                                                                                |
| ----------- | ---------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| cefi        | `gs://instruments-store-cefi-{pid}/…` (Tardis-based per-venue instrument catalog)                                            | `(asset_group, venue, data_type, instrument_type, instrument_id, day)` — per-instrument | `available_from`, `available_to`, `expiry` (perp/futures contracts), `listed_at`, `delisted_at`                                                                |
| tradfi      | `gs://instruments-store-tradfi-{pid}/…` (Databento per-venue instrument catalog: ETF tickers, futures roots, options chains) | `(asset_group=tradfi, venue, data_type, instrument_type, instrument_id-or-root, day)`   | `listed_at` (ticker first traded), `delisted_at` (delisted from the venue), `expiry` (futures + options), `last_trade_date` (options expiry per cluster)       |
| defi        | `gs://instruments-store-defi-{pid}/…` (per-(chain, protocol) pool/instrument catalog) — currently sparse, expansion in scope | `(asset_group=defi, chain, venue/protocol, data_type, instrument_or_protocol_id, day)`  | `created_at` (pool / instrument deployed on chain), `deactivated_at` (pool drained / paused), `migration_target` (pool migrated to v2/v3)                      |
| sports      | `gs://instruments-store-sports-{pid}/fixtures/…` (API-Football fixtures catalog, also team / league / season catalogs)       | `(asset_group=sports, source, data_type, league_id, fixture_id-or-day-aggregate, day)`  | `kickoff_time`, `league_active_window` (off-season pauses), `fixture_status` (postponed / cancelled), bookmaker `available_from` per `(odds_api, league)` pair |
| prediction  | `gs://instruments-store-prediction-{pid}/…` (per-canonical-question-group catalog)                                           | `(asset_group=prediction, venue, data_type, canonical_question_group, day)`             | `market_created_at` (per market_id), `resolution_time`, `settlement_time`, canonical-question-group active window (HOURLY / DAILY / ELECTION cycles)           |

**Tasks.** Sequential per asset_group — start with the asset_group whose catalog is most mature (sports fixtures +
tradfi Databento) and end with the asset_group whose catalog needs the most work (defi + prediction).

- [ ] [UAC] P0. **Catalog-read interface contract.** Every asset_group's instruments-service catalog must expose a
      uniform `list_instruments(asset_group, start_date, end_date) -> Iterator[CatalogRow]` shape — same columns as the
      manifest's row_key (`venue`, `chain`, `data_type`, `instrument_type`, `instrument_id`, `league_id`, ...) plus the
      lifecycle columns (`available_from`, `available_to`, `expiry`, etc.). Define the contract in
      `unified_api_contracts/canonical/domain/instruments_catalog.py` (NEW) so the enumerator + downstream consumers
      (data-status drilldown, MTDS pre-flight skip checks, MDPS dependency gate) all read from one shape.
- [ ] [SCRIPT] P0. **Sports v2 enumerator** — the lowest-risk first cut because the fixtures catalog is already in
      `gs://instruments-store-sports-{pid}/fixtures/by_date/day=…/entity=fixtures/…` (per
      `unified_api_contracts.sports.candidate_parquet_paths` SSOT). For odds_api: cross-product
      `(league_id, fixture_id, bookmaker, market_type) × dates` filtered by `kickoff_time ∈ [day_00:00, day_23:59]`.
      Reasons: `EXPECTED_INSTRUMENT_NOT_LISTED` for fixtures-not-yet-scheduled, `EXPECTED_PAUSED_LEAGUE` for off-season
      windows (existing reason, currently unused by enumerator), `EXPECTED_PRE_SOURCE_COVERAGE_START` for
      pre-bookmaker-coverage dates (existing reason). Wire into `_enumerate_sports` replacing today's per-source-only
      branch.
- [ ] [SCRIPT] P0. **CeFi v2 enumerator** — read per-venue instrument catalog from
      `gs://instruments-store-cefi-{pid}/by_venue/{venue}/instruments.parquet` (or whatever the canonical Tardis-derived
      layout is — needs an `instruments-service`-side audit). Cross-product
      `(venue, instrument_type, instrument_id, data_type) × dates` filtered by `available_from ≤ day ≤ available_to`.
      Today's `EXPECTED_PRE_VENUE_LAUNCH` becomes a special-case of `EXPECTED_INSTRUMENT_NOT_LISTED` (every instrument's
      `available_from` ≥ venue launch date by definition). For options/futures: bundled-by-root cluster atoms —
      `EXPECTED_INSTRUMENT_NOT_LISTED` gates per-root-day. For perp futures: `EXPECTED_INSTRUMENT_DELISTED` when
      contract expires.
- [ ] [SCRIPT] P0. **TradFi v2 enumerator** — replace today's `non_trading_day_reason` cross-product (which generates
      35,033 calendar rows per (venue, data_type) without instrument granularity) with per-
      `(venue, instrument_type, instrument_id-or-root, data_type, day)` enumeration driven by the Databento instruments
      catalog. ETF / equity tickers get per-instrument lifecycle (NASDAQ-listed-at, delisted-at); futures + options
      chains get per-root + cluster-day enumeration with weekly + standard expiries. Calendar non-trading days remain
      `EXPECTED_HOLIDAY` / `EXPECTED_WEEKEND` per the existing reason taxonomy.
- [ ] [SCRIPT] P0. **DeFi v2 enumerator** — extend today's PROTOCOL_LAUNCH_DATES + CHAIN_GENESIS_DATES cross-product
      with the per-pool instrument lifecycle. Each (chain, protocol) maintains a list of pools/instruments that get
      added/removed over time (Aave V3 listing/delisting individual reserves, Uniswap V3 pool deployments, Curve gauge
      additions, etc.). Today's `EXPECTED_INSTRUMENT_NOT_LISTED` blanket-marks 598,040 rows for "protocol on chain
      hadn't launched yet"; v2 makes that per-(chain, protocol, instrument_id, day) so we mark individual
      pools/positions correctly.
- [ ] [SCRIPT] P0. **Prediction v2 enumerator** — depends on UAC `PREDICTION_GROUPS` registry landing per
      `predictions_master_2026_05_07.plan.md`. Once that ships, cross-product
      `(venue, canonical_question_group, market_id, data_type, day)` filtered by
      `market_created_at ≤ day ≤ settlement_time`. Today's `EXPECTED_PRE_VENUE_LAUNCH` is the floor; v2 adds
      canonical-group lifecycle (HOURLY = 24 markets/day, DAILY = 1, ELECTION = 1 over months/years) so per-day coverage
      of recurring groups is honest.
- [ ] [DOCS] P0. **Codify the convention in CLAUDE.md.** After v2 ships across all 5 asset*groups, add a new
      Key-Rules-Quick-Reference bullet: *"MTDS / instruments-service / data-status missing-data checks for ANY
      asset*group derive their expected universe from the instruments-service catalog for that asset_group, NOT from
      inline / hardcoded venue / data_type / date lists. The catalog IS the SSOT for `what should exist`. Adding a new
      venue / data_type / instrument = adding to the instruments-service catalog; downstream enumerators + data-status
      panel + MTDS preflight + MDPS dependency-gate pick it up automatically."*

**Coordination with parallel plans** — Phase 3.D.5 touches the same instruments-service catalog infrastructure as the
per-asset-group umbrella plans. Reference cross-plan banners (CLAUDE.md "Cross-Plan Coordination Banners" rule) — the
Phase 3.D.5 v2 enumerator must align with:

- `cefi_master_2026_05_07.plan.md` — CeFi instrument catalog scope + lifecycle field schema
- `predictions_master_2026_05_07.plan.md` — UAC `PREDICTION_GROUPS` SSOT + per-canonical-group lifecycle
- `sports_master_2026_05_07.plan.md` — fixtures catalog read shape + `KNOWN_COVERAGE_GAPS` integration
- `tradfi_master_2026_05_07.plan.md` — Databento instrument catalog scope + cluster taxonomy
- `defi_master_2026_05_07.plan.md` — per-pool catalog expansion (currently sparse)

Each asset_group's v2 enumerator implementation lives under instruments-service/scripts/, but the catalog schema + read
interface lives in UAC. The v1 enumerator stays in place during the v2 buildout — v2 is a strictly additive layer; v1's
coarse rows stay correct (just less complete than v2 will be).

**Why ship v1 first then v2** — v1 is a one-day shippable unit that closes the rollup-vs-drilldown gap for the largest
"didn't exist yet" slice (1.45M rows). v2 is multi-week work that requires per-asset-group catalog audits + schema
agreement. Operator gets immediate denominator-divergence relief from v1 while v2 is built; no v2 prerequisite blocks
v1's value.

#### Phase 3.D.5 — Hierarchical SSOT model (operator framing 2026-05-07 evening, REVISED)

The operator clarified the architecture (revising the earlier v1-vs-v2 trade-off framing): v1 and v2 are **hierarchical
layers of one model**, not competing approaches. Two SSOTs, one manifest:

- **UAC = single SSOT for "is `(asset_group, venue/chain, day)` structurally possible"** — the coarse availability axis
  (chain genesis, venue launch, source coverage start, calendar non-trading days). Cheap, idempotent, doesn't move when
  instruments evolve. Owned by UAC `*_LAUNCH_DATES` / `CHAIN_GENESIS_DATES` / `SOURCE_COVERAGE_START` /
  `venue_trading_calendar`.
- **instruments-service = single SSOT for "given that triple is possible, what instruments are live"** — the
  per-instrument universe. Time-dependent (perp futures listed/delisted/expired, fixtures created per-kickoff,
  prediction market_ids cycled per canonical-question-group). Updates whenever the catalog discovers new instruments.

**They compose, they don't replace each other:**

```
expected_universe(venue, data_type, day):
    if not UAC.venue_alive_on(venue, day):
        yield (venue, data_type, "", "", day, reason=PRE_VENUE_LAUNCH)   # v1 layer (shipped today)
    else:
        for instr in instruments_service.list_instruments(venue, day):
            if day < instr.available_from:
                yield (..., reason=INSTRUMENT_NOT_LISTED)                # v2 layer
            elif day > instr.available_to:
                yield (..., reason=INSTRUMENT_DELISTED)                  # v2 layer
            else:
                yield (..., capture_status=expected_unattempted)         # v2 layer (NEW status)
```

**The 4th `capture_status` value: `expected_unattempted` (NEW, operator direction 2026-05-07).** Today the manifest only
has 3 capture*status values (`captured` / `empty_confirmed` / `attempted_failed`) and they all imply "we tried." Per the
operator: *"so we do need to write the instrument definition instruments into the manifest enumeration so that we can
write them as something that indicates that we haven't tried them yet, but they should exist."\_

`expected_unattempted` is distinct from `empty_confirmed` (which means "we tried, source returned 0 / the day is
structurally empty per calendar/genesis/coverage rules") and from `attempted_failed` (which means "we tried, got an
exception"). Pre-populated by v2 enumerator from the instruments-service catalog; flipped to `captured` (or
`empty_confirmed` / `attempted_failed`) by MTDS when it actually fetches. The manifest becomes the to-do list — what
stays as `expected_unattempted` IS the work backlog, no separate worklist needed.

**Coverage % at every drilldown level becomes meaningful and sums right:**

- `captured` count = data exists on disk
- `empty_confirmed` count = honest absence (pre-launch, weekend, holiday, paused-league, source-zero)
- `attempted_failed` count = something broke (with typed error_reason)
- `expected_unattempted` count = work backlog (catalog says it should exist, MTDS hasn't tried)
- Coverage % = `captured / (captured + empty_confirmed + attempted_failed + expected_unattempted)`. The denominator is
  the catalog × dates universe, not "rows in manifest" — the universe is fully enumerated.

**🚨 RED ALERT context (2026-05-07 evening, parallel-agent finding).** 5 CeFi VMs wrote manifest rows with
`capture_status=empty_confirmed` and **blank** `error_reason` (violating the 2026-05-07 writegate Phase 2.E taxonomy
that requires every empty_confirmed row to carry a typed reason). Implausible coverage gaps:

| VM                          | total | empty_confirmed | captured | error_reason |
| --------------------------- | ----: | --------------: | -------: | ------------ |
| `bitfinex-spot-2020-heavy`  |   200 |       192 (96%) |        8 | all blank    |
| `bitfinex-spot-2024-heavy`  |   600 |       576 (96%) |       24 | all blank    |
| `bitget-futures-2025-light` | 6,059 |    6,059 (100%) |        0 | all blank    |
| `kraken-spot-2020-heavy`    |   250 |       240 (96%) |       10 | all blank    |
| `kraken-spot-2023-heavy`    |   550 |       528 (96%) |       22 | all blank    |

Bitfinex 2024 spot at 96% empty is implausible (continuous volume in 2024); Bitget futures 2025 at 100% empty is even
worse. Pattern matches the lending-indices silent-zero bug from yesterday — **adapter returns no data, downstream emits
empty_confirmed without reason instead of attempted_failed**.

**The fix is the catalog-aware write-gate** (Wave 2 below). When MTDS attempts an instrument that instruments-service
catalog says was alive on day D and the source returns nothing, the writer must REJECT
`record_empty(reason=SOURCE_RETURNED_ZERO)` and force `record_failed(EmptyFromLiveInstrumentError)`. This converts
silent "we tried, source said empty" into loud "catalog says alive, source said empty — investigate." Also fixes the
silent-fallback failure mode (blank error_reason) — the writer guard rejects ANY `record_empty` that doesn't supply a
`reason` per the existing closed-set taxonomy. Migration script rewrites the existing blank-reason empty_confirmed rows
to attempted_failed with a typed `LegacyBlankErrorReasonError` reason so they get re-attempted on next VM run instead of
silently passing.

**Operator directive 2026-05-07 evening (Step 4 — codebase-wide cascade):**

> "this concept applies for MDPS, features, ml strategy etc all services because they all have dependent data, they all
> have an expected start. Obviously, their expected start single source of truth should be based on the upstream
> expected start single source of truth as well, or use the same thing. There's no point trying to get features for a
> venue which didn't exist. There's no point trying to do machine learning for a time period where the venue didn't
> exist. This stuff should be done codebase-wide, and the manifest and data status should be able to understand them and
> the services when they're looking at their dependencies. They should be able to use them to understand as well. This
> isn't all new work. A lot of the pipes are pretty much there. They just need tightening."

**Cross-service cascade — every dependent service's expected start derives from its upstream's:**

```
instruments-service (catalog SSOT)
    ├── MTDS         (per-(venue, day) → catalog filters fetch list)
    │       └── MDPS         (per-(venue, day) → MTDS manifest gates compute)
    │               └── features-*   (per-(venue/asset_group, day) → MDPS manifest gates calc)
    │                       └── ml-training   (per-asset_group → features manifest gates training window)
    │                       └── strategy      (per-archetype → features manifest gates signal generation)
    │                       └── execution     (per-venue, day → strategy + position-balance)
    └── UAC SSOTs (CHAIN_GENESIS, VENUE_LAUNCH, SOURCE_COVERAGE_START, venue_trading_calendar) —
        the structural "is this triple even possible" floor that ALL layers honour first
```

**At every layer the rule is the same:** if upstream marks a `(venue, data_type, day)` shard as `expected_unattempted`
(catalog says it should exist) or `empty_confirmed` (catalog says it shouldn't), the downstream service must propagate
that — features compute on `expected_unattempted` upstream → write own `expected_unattempted`; ML training window omits
days where upstream is `expected_unattempted` (or loads the manifest backlog as the work-list); strategy doesn't signal
for a venue that didn't exist on day D. **Cascade short-circuits silent waste.** A lot of code already does this in
spirit (DependencyError fail-fast at boundaries, manifest pre-flight skip), it just needs tightening + a uniform read
interface on the manifest.

**Tasks for the new 4th capture_status (cross-repo blast radius — multi-day shippable):**

- [x] [UAC + UTL] P0 (shipped UTL@68b3804a 2026-05-07). `EXPECTED_UNATTEMPTED` added as the 4th value of
      `unified_trading_library.manifest_writer.CaptureStatus` enum (capture_status taxonomy lives in UTL, not UAC —
      corrected from initial plan placement). Docstring spells out 4-state model + supersede property. Coverage formula
      codified inline.
- [x] [UTL] P0 (shipped UTL@68b3804a 2026-05-07).
      `ManifestWriter.record_expected_unattempted(row_key=,     attempted_at=)` helper added mirroring `record_empty` /
      `record_failed`. Per-VM shard isolation via `_record_status` (same path as the other write methods).
      Last-writer-wins supersede happens naturally via the consolidator's row_key dedup.
- [ ] [UTL] P1. Update consolidator + `record_captured` / `record_empty` / `record_failed` last-writer-wins audit —
      verify the supersede path (prior `expected_unattempted` row → MTDS writes `captured` for same row_key). Smoke test
      on a CeFi manifest after Wave 3 enumerator lands. **DEFERRED** — manifest-consolidator already does
      last-writer-wins on row_key (existing design), so the new `expected_unattempted` rows participate naturally. Audit
      pass + unit test for the supersede path remain.
- [ ] [SCRIPT] P0. Extend `instruments-service/scripts/enumerate_expected_universe.py` v2 branches (cefi / tradfi / defi
      / sports / prediction) to emit `expected_unattempted` rows for every catalog instrument whose
      `(venue, data_type, instrument_type, instrument_id, day)` is not already in the manifest with a stronger status.
      Today's v1 keeps writing `empty_confirmed/EXPECTED_PRE_VENUE_LAUNCH` etc.
- [ ] [deployment-api] P0. Coverage-calculation update: per-shard coverage denominator includes `expected_unattempted`
      count. Surface the breakdown in the response payload (`captured`, `empty_confirmed`, `attempted_failed`,
      `expected_unattempted` as 4 buckets). Backwards-compat: if `expected_unattempted` count is 0, response shape
      unchanged.
- [ ] [deployment-ui] P0. **Per-instrument × per-day drilldown visualisation.** Operator direction 2026-05-07: _"data
      status in deployment ui needs to be able to visualise that to the instrument granularity breakdown so we can
      visually see, per instrument, which days are available and which are missing. Since there can be so many
      instruments, I think there's already something in the UI that groups them and we can click to see more, click to
      see more, etc. It needs to be the same with days as well so that we can see all the days available vs missing."_ _
      Today's drilldown lands at `(venue, data_type, instrument_type, instrument_id)` and shows
      `X days captured of Y total` — aggregate. Operator wants to drill **into the days dimension** per instrument to
      see which specific days are captured / empty / failed / unattempted. _ Per-instrument pagination already exists
      (Phase 6 shipped per `data_status_drilldown_shard_atom_alignment_2026_05_07.plan.md` — 200 instruments per page,
      load-more button). Mirror that pattern at the day grain: per-instrument-leaf, render a calendar / list of days
      with status badges (4 colours for the 4 capture_status values), paginate chronologically. _ Layout suggestion:
      per-instrument click expands to a year × 12-month grid (visual calendar) where each cell shows the day's status
      colour. Hover for details (error_reason, attempted_at, file size if captured). Click a day → leaf actions
      (re-deploy that day's shard, download the parquet, inspect the failure reason). _ Pagination at the day grain may
      be unnecessary if rendered as a calendar (8 years × 365 = ~2920 days per instrument fits a single tall page). For
      instrument-types with thousands of expiring contracts (options chains), the per-cluster bundle drilldown already
      collapses; per-day for the bundle root is the relevant grain.
- [ ] [DOCS] P0. Update
      [`codex/02-data/availability-manifest-and-data-status.md`](../../codex/02-data/availability-manifest-and-data-status.md)
      to document the 4-state capture_status taxonomy + the v1+v2 hierarchical SSOT model + the `expected_unattempted` →
      `captured` supersede semantics.
- [ ] [DOCS] P0. After the cross-repo ship lands, codify in CLAUDE.md Key-Rules-Quick-Reference: _"manifest
      `capture_status` is a 4-state closed set: `captured` / `empty_confirmed` / `attempted_failed` /
      `expected_unattempted`. UAC SSOTs (`*_LAUNCH_DATES`, `*_GENESIS_DATES`, `SOURCE_COVERAGE_START`,
      `venue_trading_calendar`) own the coarse 'is this triple structurally possible' axis. instruments-service catalog
      owns the fine 'given alive, what instruments exist on this day' axis. Both layers write to the manifest; MTDS's
      `captured` writes supersede prior `expected_unattempted` rows by row_key. Coverage % at every drilldown level =
      `captured / (captured +     empty_confirmed + attempted_failed + expected_unattempted)` — denominator is the full
      universe."_

**Wave 2 — catalog-aware write-gate (the RED ALERT fix). UTL guard rule + migration. CRITICAL P0.**

- [x] [UAC] P0 (shipped UAC@e855051 2026-05-07). `EmptyFromLiveInstrumentError` + `LegacyBlankErrorReasonError` typed
      exceptions added to `unified_api_contracts.canonical.crosscutting.honest_coverage` exports. Both feed the writer
      guard + migration script. Pattern mirrors `MissingClusterValidationError` / `UpstreamTimestampBiasError`.
- [ ] [UTL] P1. **Catalog-aware write-gate in `ManifestWriter.record_empty(reason=...)`** — pending Wave 3 (depends on
      MTDS adapters wiring the `instrument_catalog` callable at construction). `EmptyFromLiveInstrumentError` typed
      class shipped today (UAC@e855051); the writer-side guard is a follow-up that requires MTDS / MDPS / features-\* to
      pass the catalog reference. Until then the blank-reason guard (next item, shipped) catches the most-common
      silent-fallback path.
- [x] [UTL] P0 (shipped UTL@68b3804a 2026-05-07). **Reject blank `error_reason` writes loudly.**
      `ManifestWriter.record_empty(reason="")` now raises `LegacyBlankErrorReasonError` early, BEFORE the
      `EMPTY_CONFIRMED_REASONS` membership check. Catches the silent-fallback bug pattern (RED ALERT 2026-05-07 — 5 CeFi
      VMs writing 96-100% empty rows with all blank reasons). Adapters MUST pass a typed reason or call `record_failed`
      for unexpected absence.
- [x] [TEST] P0 (smoke-tested 2026-05-07; full unit test pending). Smoke-tested 4 cases locally: (a) blank reason →
      LegacyBlankErrorReasonError, (b) SOURCE_RETURNED_ZERO accepted, (c) bogus reason →
      UnknownEmptyConfirmedReasonError, (d) record_expected_unattempted writes capture_status=expected_unattempted. Full
      pytest unit test for the supersede path remains a follow-up.

**Wave 2.M — Migration script for the existing bad rows.** The 5 RED ALERT VMs wrote ~7,659 blank-reason empty_confirmed
rows to canonical CeFi manifest. Plus an unknown number of historical bad rows from prior silent-fallback bugs.

**Asset-group-specific empty_confirmed legitimacy (operator directive 2026-05-07 evening, msg 6):**

> "sports and prediction markets are allowed to have empty_confirmed and reason like no match today or something. cefi,
> defi, tradfi cannot have empty_confirmed. if its genuinely empty then it should be on venue level like holiday or
> exchange issue or something. Illiquid ones like far OTM options are not going to have any trades for multiple days,
> its possible but in that case it should be 0 volume candles with LTP as current price."

This codifies a per-asset-group rule the existing UTL `classify_legacy_empty_row` helper does NOT honour. Today the
helper defaults `_classify_cefi` / `_classify_defi` blank-reason rows to `SOURCE_RETURNED_ZERO` (an empty_confirmed
reason) — per the operator, this is WRONG. It silently grants cefi/defi rows legit-empty status when actually they
should flip to `attempted_failed` to force re-attempt. **Audit finding 2026-05-07**: the existing
`reconcile_expected_absence_reasons.py` (which uses the helper) has been retroactively stamping cefi/defi blank-reason
rows as `empty_confirmed/SOURCE_RETURNED_ZERO` — propagating the silent-bug semantics into the manifest. Any rows
touched by that reconciler in cefi/defi need a re-pass to flip to the correct shape.

| asset_group | Legit empty_confirmed at instrument-day? | Default for un-classifiable blank-reason rows                     |
| ----------- | ---------------------------------------- | ----------------------------------------------------------------- |
| sports      | YES — no fixtures today is normal        | `empty_confirmed/SOURCE_RETURNED_ZERO`                            |
| prediction  | YES — no markets active that day         | `empty_confirmed/SOURCE_RETURNED_ZERO`                            |
| cefi        | NO at instrument-day — venue-level only  | `attempted_failed/LegacyBlankErrorReasonError` — force re-attempt |
| defi        | NO at instrument-day — venue-level only  | `attempted_failed/LegacyBlankErrorReasonError` — force re-attempt |
| tradfi      | NO at instrument-day — venue-level only  | `attempted_failed/LegacyBlankErrorReasonError` — force re-attempt |

Venue-level legit empties for cefi/defi/tradfi (kept as `empty_confirmed` with typed reason):

- `EXPECTED_HOLIDAY` / `EXPECTED_WEEKEND` — calendar non-trading days (tradfi).
- `EXPECTED_PARTIAL_HALF_DAY` — half-session days (tradfi).
- `EXPECTED_PRE_VENUE_LAUNCH` — venue not yet operating (cefi/defi).
- `EXPECTED_PRE_GENESIS_CHAIN` — chain not yet alive (defi).
- `EXPECTED_INSTRUMENT_NOT_LISTED` — instrument's `available_from` is after the day (per-instrument catalog read; Wave 3
  will populate this from instruments-service).
- `EXPECTED_INSTRUMENT_DELISTED` — instrument's `available_to` has passed.

**Illiquid-instrument carve-out (deferred to a separate adapter fix, NOT this migration).** Per the operator: illiquid
options (far OTM, distant expiry) may have zero trades for multiple days. The correct manifest shape for those is NOT
`empty_confirmed` — it's `captured` with 0-volume candles where OHLC carries LTP-from-prior-day. This is an MTDS / MDPS
adapter behaviour change, not a manifest classification change. Tracked as a follow-up below (Wave 3.M).

**Manifest column hygiene (operator clarification msg 6):** the manifest already carries `attempted_at` (per the
existing v5 schema) which is the "last time this data point was checked" / `checked_at` semantics. No new column needed.
Updating an existing row's reason / status via the consolidator's last-writer-wins merge naturally bumps `attempted_at`
to the new write — no schema change. Reconciler stamps + adapter writes both refresh the timestamp.

**Empty-files-vs-manifest-rows (operator clarification msg 6):** writing fake-empty parquet files (0-volume candles, NaN
OHLC bars) is NOT the right model — has bad implications for ML / features / strategy / execution backtests if consumers
misinterpret. Manifest absence rows are the clear, service-decides-policy instruction. Each downstream service reads the
manifest and decides per its own policy (NaN-fill, fail period, propagate, skip). Single SSOT for "what should exist",
clear instruction for "what's actually there", per-service flexibility for "how to handle absence."

- [x] [SCRIPT] P0 (shipped instruments-service@86804c7 + UTL@7eca2c20 + UTL@7276cca1 2026-05-07). NEW
      `instruments-service/scripts/reconcile_blank_error_reason_rows.py` walks all 5 asset*group manifests; finds rows
      where `capture_status=empty_confirmed AND (error_reason IS NULL OR     error_reason=='')`; classifies via the
      discriminated UTL helper `classify_blank_reason_row(asset_group, row) -> tuple[capture_status, error_reason]`. Per
      operator msg 6: sports/prediction → keep empty_confirmed/SOURCE_RETURNED_ZERO; cefi/defi/tradfi → keep
      empty_confirmed/EXPECTED*\* if classifier matches venue-level rule (PRE_VENUE_LAUNCH / PRE_GENESIS_CHAIN / HOLIDAY
      / WEEKEND), else flip to attempted_failed/LegacyBlankErrorReasonError. Classifier helper enhanced (UTL@7276cca1)
      to use UAC `CEFI_VENUE_LAUNCH_DATES` / `PREDICTION_VENUE_LAUNCH_DATES` for pre-launch detection. Default
      scan-only; `--apply-flips` requires `MANIFEST_PER_VM_SHARDS=true` + `VM_NAME=<unique>`. Halt-safety
      `--max-flips-per-run=100k` default.
- [x] [VM-LAUNCH] P0 (launcher shipped deployment-service@f72686b 2026-05-07).
      `deployment-service/scripts/vm/launch-blank-reason-recon-vm.sh` — singleton-locked GCE launcher mirroring
      `launch-defi-phantom-recon-vm.sh`. Watchdog prefix `blank-reason-recon-` registered.
- [x] [VM-LAUNCH] P0 (shipped 2026-05-07 evening — `blank-reason-recon-cefi-20260507-173136`). **CeFi `--apply-flips`
      complete: 1,238,229 rows flipped.** Distribution: 1,238,079 attempted_failed/LegacyBlankErrorReasonError + 150
      empty_confirmed/EXPECTED_PRE_VENUE_LAUNCH (mostly post-2018-launch venues — BYBIT pre-Dec-2018, HYPERLIQUID
      pre-2023). Per-VM shard at
      `gs://market-data-tick-cefi-central-element-323112/_index/per_vm/blank-reason-recon-cefi-20260507-173136.parquet`.
      Consolidator merging into canonical within ~5min.
- [x] [VM-LAUNCH] P0 (shipped 2026-05-07 evening — 4 parallel VMs). **All 5 asset_groups `--apply-flips` complete.
      Total: 3,114,843 rows flipped across 5,457,181 manifest rows (57.07% of all manifests had blank error_reason).**
      Per-asset-group: _ **cefi** — 1,238,229 flipped (1,238,079 attempted_failed + 150 EXPECTED_PRE_VENUE_LAUNCH) _
      **sports** — 1,868,285 flipped (100% empty_confirmed/SOURCE_RETURNED_ZERO — sparse-fixtures legit per msg 6;
      sports CAN have legit empty days) _ **tradfi** — 7,603 flipped (5,159 attempted_failed + 2,225 EXPECTED_WEEKEND +
      219 EXPECTED_HOLIDAY) _ **defi** — 685 flipped (100% attempted_failed/LegacyBlankErrorReasonError) \*
      **prediction** — 41 flipped (100% empty_confirmed/SOURCE_RETURNED_ZERO — sparse trading legit) All 5 per-VM shards
      uploaded; consolidator merging into canonical manifests within ~5min. Net effect: ~1.25M cefi/defi/tradfi rows
      flagged for re-attempt by orchestrator (catches the silent-fallback adapter paths via the new UTL@68b3804a
      blank-reason guard); ~1.87M sports + few-K tradfi/prediction empty-with-typed-reason rows now properly classified
      for downstream consumer policy decisions.

**Wave 3 — instruments-service v2 enumerator + downstream cascade. Multi-day, plan-detail.**

- [ ] [SCRIPT] P0. Extend `instruments-service/scripts/enumerate_expected_universe.py` v2 branches with the 4th
      capture_status. Each asset_group gets: _ Pre-venue/chain-launch dates → continue writing
      `empty_confirmed/EXPECTED_PRE_VENUE_LAUNCH` / `EXPECTED_PRE_GENESIS_CHAIN` (Wave 1 — already shipped today). _
      Per-instrument-alive dates with no manifest row → write `expected_unattempted` (NEW). _ Per-instrument-pre-listing
      dates → write `empty_confirmed/EXPECTED_INSTRUMENT_NOT_LISTED`. _ Per-instrument-post-delisting dates → write
      `empty_confirmed/EXPECTED_INSTRUMENT_DELISTED`.
- [ ] [MTDS] P0. Wire `instrument_catalog` callable through MTDS adapters → ManifestWriter at construction time. Each
      adapter passes a catalog reader for the venue it serves. Writes that hit the catalog-aware guard get classified
      appropriately.
- [ ] [MDPS] P1. Cascade rule: MDPS reads the upstream MTDS manifest. For shards marked `expected_unattempted` upstream,
      MDPS writes its own `expected_unattempted` (no compute possible without raw ticks). For shards marked
      `empty_confirmed/EXPECTED_*`, MDPS propagates the same reason (e.g. `EXPECTED_PRE_VENUE_LAUNCH` upstream →
      `EXPECTED_PRE_VENUE_LAUNCH` downstream).
- [ ] [features-*] P1. Same cascade rule. Features compute reads MDPS manifest; for `expected_unattempted` /
      `empty_confirmed/EXPECTED_*` shards, write own row with the same status. The `feature_group → required_inputs` DAG
      already encodes which features depend on which data_types; the cascade walks that DAG.
- [ ] [ml-training] P1. Training-window selector reads features manifest; omits days where any required feature*group is
      `expected_unattempted` or `empty_confirmed/EXPECTED*\*`. Training set size becomes honest about the universe.
- [ ] [strategy] P1. Signal generation gates on features manifest; no signal for a `(venue, day)` where upstream is not
      `captured` or `empty_confirmed/SOURCE_RETURNED_ZERO`. (Honest source-zero is OK to signal on; pre-launch /
      unattempted is not.)
- [ ] [execution] P2. Position / fill simulation respects upstream cascade. (Mostly already correct via the manifest
      pre-flight gate — this is an audit pass.)
- [ ] [DOCS] P0. Codify the cascade in `codex/02-data/honest-absence-downstream-handling.md` — per-service
      consumer-class audit table extension to include `expected_unattempted` and the cascade-propagation contract.

**Coordination notes** — adding `expected_unattempted` is the largest schema change in the writegate plan to date.
Cross-repo touch:

- UAC — capture_status enum extension (small)
- UTL — `ManifestWriter` 4th method + supersede semantics (small-medium)
- MTDS — verify that `record_captured` already supersedes prior writes by row_key (no change expected, but audit needed)
- deployment-api — coverage calc 4-bucket breakdown (small)
- deployment-ui — per-instrument × per-day calendar visualization (medium-large; operator-flagged P0)
- codex docs — manifest schema doc + CLAUDE.md rule (small)
- downstream consumers — every code path that switches on `capture_status` needs a handler for the 4th value (audit
  pass + small fixes per consumer)

**Suggested sequencing** — UAC + UTL first (schema landing), then enumerator + manifest backfill, then
deployment-api/UI. Manifest backfill ships v2 catalog reads per-asset-group (sports first since fixtures catalog is most
mature, prediction last since `PREDICTION_GROUPS` is still empty in UAC).

#### Phase 3.D.5 — Per-asset-group catalog SSOT model (operator directive 2026-05-07 msg 7, COMPREHENSIVE)

The operator extended the architecture beyond cefi/defi/tradfi to cover every asset_group AND the typed- reason-taxonomy
growth process. Reproduced here so the per-asset-group catalog tasks (Wave 3 above) honour the right shape:

**1. Sports fixtures = instruments.** The API-Football fixtures catalog (in
`gs://instruments-store-sports-{pid}/fixtures/by_date/day=…/entity=fixtures/…`) IS the per-day source-of- truth for
"what fixtures should exist on day D for league L." Downstream sources (footystats, understat, transfermarkt, sfi,
odds_api, weather) gate their expected universe on this catalog with per-source exception rules:

- **understat coverage rules** — encoded as a per-(league, season) inclusion list. Understat covers EPL/La Liga/Serie
  A/Bundesliga/Ligue 1; for other leagues we don't expect xG data. UAC SSOT to add:
  `UNDERSTAT_COVERED_LEAGUES: dict[str, dict[str, tuple[str, str]]]` mapping league_id → season → (start_date,
  end_date). Days outside coverage → `EXPECTED_INSTRUMENT_NOT_LISTED` (or new `EXPECTED_SOURCE_DOES_NOT_COVER_LEAGUE` if
  more specific).
- **transfermarkt transfer windows** — UAC SSOT to add: `TRANSFER_WINDOWS: list[tuple[str, str, str]]` (window_name,
  start, end) for the canonical summer + winter windows per league family. Outside the window:
  `EXPECTED_OUTSIDE_TRANSFER_WINDOW`. Inside: enumerate (league, day) tuples we expect transfer data for.
- **footystats per-league season bounds** — UAC SSOT to add:
  `FOOTYSTATS_LEAGUE_SEASONS: dict[str, list[tuple[str, str, str]]]` mapping league_key → list of (season_id,
  season_start, season_end). Days outside any active season → `EXPECTED_PRE_SEASON` or `EXPECTED_POST_SEASON` (new
  reasons). Days within a season → expect data.
- **fixture_events / fixture_stats / lineups** — gated by per-fixture `kickoff_time`. Events / stats / lineups only
  expected during/after the match window per fixture (already partly encoded via `available_at` stamping rules).
- **per-source-rate-limited skips** — when a source's rate limit forces us to defer a fixture's data fetch, that's
  `attempted_failed/RateLimitError`, NOT `empty_confirmed`. Captured in the typed-reason expansion process below.

**2. Prediction markets = same model.**

- Per-market lifecycle (`market_created_at`, `resolution_time`, `settlement_time`) lives in instruments-service catalog
  (per `predictions_master_2026_05_07.plan.md`).
- Pre-`market_created_at` → `EXPECTED_INSTRUMENT_NOT_LISTED` (per-market grain).
- Post-`settlement_time` → `EXPECTED_INSTRUMENT_DELISTED`.
- Within active window with no trades that day → `empty_confirmed/SOURCE_RETURNED_ZERO` (legit per msg 6 — sparse
  trading is fine for prediction markets, distinct from "genuinely missing").
- Per-canonical-question-group (HOURLY=24/day, DAILY=1, ELECTION=1-over-months) cluster expectations enforced at
  `record_captured` via cluster validation.

**3. Typed-reason-taxonomy expansion process (operator framing — system robustness ratchet).**

> "If an instrument has empty data, we still need to be able to record why it's empty, as long as we write a clear
> reason. ... Over time as we find more and more reasons that shouldn't fail with `empty_confirmed` (like auth for
> example or rate limits that shouldn't be empty_confirmed), we can do it. It's basically how we figure out our system
> is robust or not."

Today UAC `EmptyConfirmedReason` enum has 12 values (HOLIDAY / WEEKEND / PAUSED_LEAGUE / PRE_SOURCE_COVERAGE_START /
PRE_GENESIS_CHAIN / PRE_VENUE_LAUNCH / INSTRUMENT_NOT_LISTED / INSTRUMENT_DELISTED / PARTIAL_HALF_DAY /
DEPRECATED_DATA_TYPE / REFDATA_CADENCE_CHANGE / SOURCE_RETURNED_ZERO). Each operator-flagged "this should never have
been empty_confirmed" finding adds:

- A new typed `attempted_failed` error class (or extends an existing one) — e.g. `RateLimitError` /
  `AuthenticationError` / `MalformedSourceResponseError` / `UpstreamCorrelationIDDuplicate` — distinct from the
  EmptyConfirmedReason set.
- A migration pass to flip historical rows that were silently empty_confirmed but should have been attempted_failed
  under the new typed reason. Mirrors `reconcile_blank_error_reason_rows.py` (Wave 2.M).
- A reader-side classifier extension so consumer services (data-status panel, ML training, strategy) can distinguish
  "auth-failure-retry-pending" from "honest-no-data" in their per-status policy.

**Process — when an operator flags a "shouldn't be empty_confirmed" pattern:**

1. File a finding doc in `plans/active/issues/<short-name>_<YYYY_MM_DD>.md` per the Findings Triage Discipline rule.
   Include sample row, suspected root cause, suggested typed-reason class.
2. Add the typed error class to UAC honest_coverage.py exports.
3. Add a UTL migration script (templated on `reconcile_blank_error_reason_rows.py`) that flips historical rows. Run
   scan-only; operator approves; --apply-flips.
4. Update the adapter that was silently writing empty_confirmed to call `record_failed` with the typed error.
5. Codify the typed reason in CLAUDE.md "Three-category empty-output decision" rule expansion.

**Tasks for the per-asset-group catalog SSOT extension (Wave 3.S — sports / prediction):**

- [ ] [UAC] P1. NEW `unified_api_contracts/registry/sports_per_source_rules.py` — codify `UNDERSTAT_COVERED_LEAGUES`,
      `TRANSFER_WINDOWS`, `FOOTYSTATS_LEAGUE_SEASONS`, plus a uniform
      `is_expected_for_source(source, league_id, day) -> tuple[bool, str|None]` helper that returns (is_expected,
      reason_if_not). Mirrors the chain_env / venue_launch_dates / source_coverage_start pattern.
- [ ] [UAC] P0. Two new EmptyConfirmedReason values: `EXPECTED_OUTSIDE_TRANSFER_WINDOW` +
      `EXPECTED_SOURCE_DOES_NOT_COVER_LEAGUE`. (Or use `EXPECTED_INSTRUMENT_NOT_LISTED` semantically with these as
      classifier-internal — operator preference.)
- [ ] [SCRIPT] P0. Extend the v2 enumerator (Phase 3.D.5 Wave 3 above) sports branch to read
      `instruments-store-sports-{pid}/fixtures/…` per-day fixtures catalog; cross-product with
      `(source, league_id, fixture_id, data_type)` filtered by per-source-rules. Yields `expected_unattempted` rows for
      the shards we DO expect; emits `empty_confirmed` with the right EXPECTED\_\* for shards we DON'T expect.
- [ ] [SCRIPT] P0. Extend the v2 enumerator prediction branch with per-canonical-question-group lifecycle (depends on
      UAC `PREDICTION_GROUPS` per `predictions_master_2026_05_07.plan.md`). Yields `expected_unattempted` for active
      markets, `EXPECTED_INSTRUMENT_NOT_LISTED` / `EXPECTED_INSTRUMENT_DELISTED` for outside-lifecycle dates.
- [ ] [DOCS] P0. Update `codex/02-data/honest-absence-downstream-handling.md` with the per-source-rules table + the
      typed-reason-taxonomy expansion process.

**Wave 3.M — Zero-activity-bars-during-market-hours (operator msg 6 + msg 8 — broadened scope).**

Operator msg 8 (2026-05-07 evening, after Wave 2.M migration completed): _"when a instrument has ohlcv, trades or
quotes/depth stuff during expected market hours for expected instrument definitions, marking them 0 for volume or trade
volume but still recording them so that we know they're available so that if we're plotting for example a volatility
smile we have all the instruments and we understand that it was zero volume as opposed to not collecting that
instrument."_

**Use case — volatility smile.** When plotting a volatility smile across a venue's options chain, every strike must be
visible. If a far-OTM strike skipped collection, the smile has a gap and the modeller can't tell "this strike was just
illiquid" from "this strike wasn't captured." Zero-volume bars with prior-day LTP fill this gap honestly — the modeller
sees ALL strikes, with volume=0 flagging the illiquidity. Generalizes beyond options to any cross-instrument analysis
where completeness matters (CeFi thin pairs, TradFi after-hours, sports zero-bookmaker-coverage hours).

**Scope — the rule applies to EVERY (asset_group, data_type) where:**

- The instrument is alive per instruments-service catalog AND
- The day falls within the venue's expected market hours (per `venue_trading_calendar` / `KNOWN_COVERAGE_GAPS` / source
  rules) AND
- The data*type is one where "no activity but still tradeable" is a meaningful state —
  `ohlcv*\*`, `trades`, `book_snapshot_5`, `derivative_ticker`, `options_chain`, `futures_chain`, `odds_snapshot`
  (sports — no bookmaker offered odds for an active fixture), etc.

**Manifest representation:** `capture_status=captured` (real bars on disk, just zero-volume). Distinct from
`empty_confirmed` (we tried, source said empty / structurally empty), `attempted_failed` (error), `expected_unattempted`
(catalog-known but not yet fetched). Volume = 0 in the parquet column tells the consumer "tradeable but no trades
happened."

**Per-data-type bar shape:**

| data_type                              | zero-activity bar shape                                                                               |
| -------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| `ohlcv_1m` / `ohlcv_15m` / `ohlcv_24h` | open=high=low=close=prior_LTP, volume=0, trade_count=0                                                |
| `trades`                               | one row per minute (or interval) with price=prior_LTP, qty=0, side=none — preserves time-axis density |
| `book_snapshot_5`                      | snapshot every interval with prior bid/ask kept, no new updates; trade_count_in_window=0              |
| `derivative_ticker`                    | last-known funding/mark/index carried forward, last_trade=null, oi=prior_value                        |
| `options_chain`                        | per-cluster bundle: every root's per-strike row gets a zero-volume candle with prior LTP              |
| `futures_chain`                        | per-root bundle: every contract gets a zero-volume candle with prior LTP                              |
| `odds_snapshot`                        | per-bookmaker row with last-known odds carried forward, ts=hour-bucket, mark "stale=true" optional    |

**This is an MTDS / MDPS adapter behaviour change** (writes real data instead of `empty_confirmed`), separate from the
manifest classification work but closely related — once Wave 2.M's blank-reason guard catches silent-fallback paths, the
next adapter behaviour to fix is "what to do when source returns nothing for an active instrument." Wave 3.M is that
fix.

**Tasks:**

- [ ] [SCRIPT] P1. **Audit MTDS adapters per (venue, data_type)** for the zero-volume-during-market- hours behaviour.
      Each adapter has a per-shard fetch loop; the post-fetch branch on "fetched empty / source returned no rows" must
      distinguish: (a) instrument NOT alive that day per catalog → write `empty_confirmed/EXPECTED_INSTRUMENT_*` (b)
      instrument alive, day within market hours → **NEW:** write zero-volume bars with prior LTP, record `captured` with
      real bar count > 0 (typically full interval grid for the day). (c) instrument alive, day outside market hours
      (calendar non-trading) → write `empty_confirmed/EXPECTED_HOLIDAY/WEEKEND` (existing flow). Use the catalog-aware
      write-gate (Wave 2 `instrument_catalog` callable) to drive (a) vs (b)/(c).
- [ ] [SCRIPT] P1. **Per-data-type bar-shape templates in UTL.** A single `unified_trading_library.zero_activity_bars`
      helper that generates the right zero-activity shape per data_type per the table above. Adapters call
      `make_zero_activity_bars(data_type, instrument_id, day, prior_ltp, market_hours)` and write the result through
      ManifestWriter. Avoids per-adapter inlined zero-bar logic drift.
- [ ] [SCRIPT] P1. **prior_ltp source SSOT.** The "prior LTP" needs a uniform read source: query the previous day's
      `captured` parquet for the same instrument; if not available, fall back to the most recent captured day in the
      manifest (lookback up to N days). UTL helper
      `get_prior_ltp(asset_group, venue, instrument_id, day) -> Decimal | None`. None → still write zero-activity bars
      but with `null` price (volume=0, trade_count=0; consumers can handle).
- [ ] [SCRIPT] P1. **MDPS options-candle-builder cascade follow-on.** If upstream MTDS parquet now has zero-volume bars
      (post-Wave 3.M), MDPS sees them as `captured` and processes them through the normal candle pipeline — output
      candles also have zero volume. No special logic; the cascade handles it. **Audit needed**: confirm MDPS doesn't
      have a special-case "drop zero-volume bars" filter that would re-introduce the gap.
- [ ] [SCRIPT] P2. **Volatility-smile completeness QG check.** A smoke test in MDPS / features-vol that picks a recent
      options chain day, asserts the smile has all 11 ES.OPT clusters present (per UAC `ES_OPTIONS_CLUSTERS`) — no
      missing strikes, even for far-OTM. Catches Wave 3.M regressions automatically.
- [ ] [DOCS] P1. Update CLAUDE.md "Three-category empty-output decision" rule to add a 4th case: **D. Source returned 0
      ticks but instrument is alive per catalog AND day falls within market hours** → write zero-activity bars with
      prior LTP, `record_captured` (real OHLC, zero volume). Distinct from cases A/B/C — this is the "honest tradeable
      but no activity" path.

**Manifest column hygiene (operator msg 7 reaffirm).** No new manifest columns needed. `attempted_at` already encodes
"checked_at"; combined with `error_reason` it tells us "we tried at T and got X". The event log (GCS) provides the
lifecycle audit trail. **If a future case arises where checked_at and created_at semantically diverge** (e.g. an
enumerator pre-write vs an actual fetch attempt), we'd add a new column at THAT point — not preemptively. Today the
consolidator's last-writer-wins on identical row_key naturally bumps `attempted_at` to the most recent write.

**Empty-files-vs-manifest-rows reaffirm (operator msg 6).** No fake parquet files for absence. Manifest absence rows +
the typed reason ARE the SSOT instruction. Each downstream service reads the manifest and applies its own policy
(NaN-fill, fail period, propagate, skip) per the typed reason. Adding new fake-data conventions has audit costs that
compound over time; manifest absence is the clear single instruction.

#### Phase 3.D.5 — Operator's reasoning trail (2026-05-07 evening, kept for audit context)

The operator walked through the v1/v2 architecture in three steps. Reproduced here verbatim so the final
hierarchical-SSOT model (immediately above) is anchored to the reasoning that produced it:

**Step 1 — initial trade-off framing.** Operator: _"Yeah, I guess the only downside of doing it based on instrument
services is if instrument services haven't run yet, then what do you do? I guess it just means that we'd have to keep
re-running it as instrument services expand. ... Whereas if you do it this way, you're going to get a whole bunch of
empty data that you know is empty because you haven't run instrument services, but at least once instrument service is
100%, you can run it just a straight data status, because the manifest is already making sense. That's the trade-off,
right?"_ — read as v1 vs v2 competing.

**Step 2 — clarification toward a hybrid.** Operator: _"a perp instrument is a shard in itself ... so when you're doing
a data status check on market tick data service how does it know that that instrument is missing if it doesn't use
instrument service ... unified api contracts only tells us when a venue data type instrument type day shard should start
but it doesn't tell us how many instruments we should expect in that ... I could understand a hybrid ... we could use
the single source of truth for like venue instrument type data type availability on a daily basis, but then we'd still
need instrument service for the deep dive."_ — recognises v1 and v2 are at different grains.

**Step 3 — final synthesis.** Operator: _"so we do need to write the instrument definition instruments into the manifest
enumeration so that we can write them as something that indicates that we haven't tried them yet, but they should
exist."_ — proposes the 4th `capture_status` (`expected_unattempted`) that makes the manifest fully self-describing
across both grains. **This is the implementation directive** captured as concrete tasks in the section above.

**The contrast (kept for downstream consumer audits + future-agent reading) — what changed between "v1 alone vs v2
alone" and the final "v1 + v2 hierarchical with `expected_unattempted`":**

| Property                                        | v1 cross-product (shipped today)                                                                                 | v2 catalog-driven (Phase 3.D.5 above)                                                                             |
| ----------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| Granularity                                     | (asset_group, venue, data_type, day) — coarse, no per-instrument                                                 | (asset_group, venue, data_type, instrument_type, instrument_id, day) — fine, per-instrument                       |
| What it marks as expected-empty                 | "venue / chain / source did not exist" — the floor of absence                                                    | All of v1's set PLUS per-instrument NOT_LISTED / DELISTED / EXPIRED / paused-league windows                       |
| Idempotence vs catalog evolution                | **IDEMPOTENT** — chain genesis / venue launch dates rarely change; rerun only when SSOT itself changes           | **NOT idempotent** — every catalog addition (new venue, new pool, new fixture, new market) requires a rerun       |
| Sensitivity to instruments-service completeness | **insensitive** — works even when catalog is 0% populated, lets the manifest tell the truth about coarse absence | **sensitive** — under-marks if catalog is incomplete; over-marks if catalog includes deprecated/wrong instruments |
| Operator workflow                               | Run once when SSOT changes (~quarterly cadence)                                                                  | Run on every catalog-update commit (~daily / weekly cadence) or wire as a post-instruments-service hook           |
| Risk if not run                                 | Coarse "didn't exist" rows stay missing — rollup % off until a new venue's pre-launch dates land                 | Per-instrument rows stay missing — fine-grain denominator off but coarse layer is fine                            |

**The right shape, given the trade-off, is BOTH layers running concurrently:**

- **v1 (today's enumerator)** = always-live coarse layer. Re-runs when UAC `CHAIN_GENESIS_DATES` /
  `PROTOCOL_LAUNCH_DATES` / `CEFI_VENUE_LAUNCH_DATES` / `PREDICTION_VENUE_LAUNCH_DATES` / `SOURCE_COVERAGE_START` evolve
  (rare — quarterly-ish). Idempotent. The floor of expected-empty rows that doesn't drift even if instruments-service is
  0%.
- **v2 (Phase 3.D.5 to-be-built)** = catalog-driven precision layer on top of v1. Re-runs when instruments-service
  catalog evolves (frequent). Wire as a post-instruments-service hook so re-running is automatic, not manual.

The two layers are **complementary, not competing**. v1 stays correct even when v2 is incomplete; v2 adds precision
without replacing v1's coverage. Manifest-consolidator merges per-VM shards from both layers into the same canonical
`_index/availability_index.parquet` — last-writer-wins on identical row_keys means a v2 write for
`(venue, data_type, instrument_id=X, day=D)` cleanly supersedes a v1 write for
`(venue, data_type, instrument_id="", day=D)` if both ever collide (they don't with today's empty-string sentinel
discipline, but the model is robust to future grain refinements).

**Codified as workspace convention (NEW Key-Rule):** the v2 enumerator is the SSOT for fine-grain expected-empty; v1 is
the SSOT for coarse expected-empty. Neither replaces the other. Adding a new venue / data_type / instrument type goes
into BOTH SSOTs — UAC `*_LAUNCH_DATES` / `*_GENESIS_DATES` for v1 if it's a new "structural" entity, AND the
instruments-service catalog for v2's per-instrument enumeration. The data-status drilldown reads the canonical manifest
(which has both layers merged) — no special-casing.

#### Phase 3.D.5 Wave 3.X — Comprehensive expected-universe-dimensions matrix audit (operator msg 9, 2026-05-07 evening)

Operator msg 9 (post Wave 2.M migration completion): _"What about missing instrument because there's no trades or no
volume, or missing odds because there's no odds or something? Have we factored that in as well if that's during the
expected range? ... If not, then all of that stuff should be in PM active plans. Check if it's not, then we should add
it, and then we should get to doing it. migrations, backfills, tests, whatever needs to be done."_

**The audit.** Below maps every dimension of "is this data point supposed to exist" against where the SSOT lives
today, what status it's in, whether it's wired into the classifier / write-gate / cascade, and what gaps remain.
Status legend: ✅ shipped + wired · ⚠️ shipped but unwired (needs consumer integration) · 🟡 partial · ❌ missing.

**Sports / Prediction dimensions:**

| # | Dimension                                            | UAC SSOT                                                            | Status | Classifier-aware? | Cascade-wired? | Gap                                                                          |
| - | ---------------------------------------------------- | ------------------------------------------------------------------- | ------ | ----------------- | -------------- | ---------------------------------------------------------------------------- |
| 1 | Per-fixture kickoff_time (session start)             | `instruments-store-sports/fixtures/…` catalog (not UAC — instruments-service catalog) | ✅ | ❌ — classifier doesn't read fixtures yet | ❌ | Wave 3.S v2 enumerator must read fixtures + emit per-(league, fixture, day) expected universe |
| 2 | Per-fixture event windows (events / lineups / stats) | `availability_semantics.AVAILABILITY_AT_SEMANTICS` (per-data-type stamping rules)   | ✅ | ❌ | ⚠️ partial (lineups stamping is `kickoff-60min` already) | Wave 3.S enumerator must derive expected windows from kickoff per data_type |
| 3 | Source coverage start (api_football, footystats etc.)| `unified_api_contracts.sports.SOURCE_COVERAGE_START` + `DATA_TYPE_COVERAGE_START`   | ✅ | ✅ (`_classify_sports`) | ✅ (clip in data_status) | None — fully wired                                                          |
| 4 | Paused-league windows                                | `unified_api_contracts.sports.KNOWN_COVERAGE_GAPS` (currently empty dict)            | ⚠️ | ✅ helper exists | ✅ orchestrator pre-skips | Populate `KNOWN_COVERAGE_GAPS` per known incidents (e.g. EFL paused windows) |
| 5 | Transfer windows per country                          | `unified_api_contracts.canonical.domain.sports.transfer_windows.TRANSFER_WINDOWS`     | ✅ | ❌ — classifier doesn't gate transfer_records | ⚠️ partial (features-sports uses it; data_status doesn't) | Wire `is_transfer_window_open` into `_classify_sports` → `EXPECTED_OUTSIDE_TRANSFER_WINDOW` (NEW reason) |
| 6 | Per-league season bounds (footystats league_id changes)| `unified_api_contracts.sports.provider_league_ids.FOOTYSTATS_SEASON_IDS`            | ✅ | ❌ — no bounds check | ⚠️ partial | Add `EXPECTED_PRE_SEASON` / `EXPECTED_POST_SEASON` reasons; classifier branch on (league, season) |
| 7 | Understat per-league coverage list                    | ❌ MISSING                                                                            | ❌ | ❌ | ❌ | NEW UAC SSOT `UNDERSTAT_COVERED_LEAGUES: dict[league_id → list[season_id]]` (top-5 leagues only) |
| 8 | Prediction canonical_question_group enum              | `unified_api_contracts.canonical.domain.predictions.canonical_groups.CanonicalQuestionGroup` + `CANONICAL_GROUP_METADATA` | ✅ | ❌ — `_classify_prediction` is venue-only today | ❌ | Wave 3.S extension: gate prediction shards on canonical-question-group lifecycle |
| 9 | Prediction per-market lifecycle (created_at / settlement_time) | `unified_api_contracts.canonical.domain.predictions.lifecycle` module             | ✅ | ❌ | ❌ | Wave 3.S enumerator + MTDS CLOB capture must respect bounds                  |
|10 | Prediction venue launch (POLYMARKET / KALSHI)         | `unified_api_contracts.registry.venue_launch_dates.PREDICTION_VENUE_LAUNCH_DATES`    | ✅ | ✅ (`_classify_prediction`) | ✅ (Wave 1 enumerator) | None                                                                      |

**TradFi dimensions:**

| # | Dimension                                       | UAC SSOT                                                              | Status | Classifier-aware? | Cascade-wired? | Gap                                                                                   |
| - | ----------------------------------------------- | --------------------------------------------------------------------- | ------ | ----------------- | -------------- | ------------------------------------------------------------------------------------- |
|11 | Venue trading calendar (weekend / holiday)      | `unified_api_contracts.registry.venue_trading_calendar`               | ✅ | ✅ (`_classify_tradfi`) | ✅ | None — fully wired                                                                    |
|12 | **Half-day sessions** (Thanksgiving Friday, Christmas Eve, etc.) | ❌ — `EXPECTED_PARTIAL_HALF_DAY` enum exists but no calendar | ❌ | ❌ | ❌ | NEW UAC SSOT `HALF_DAY_SESSIONS: dict[venue, list[(date, close_time)]]` + classifier branch |
|13 | **Intra-day session hours** (NYSE 9:30-16:00, CME 17:00-16:00 next-day, FX continuous) | ❌ — no session_open / session_close per venue | ❌ | ❌ | ❌ (today: classifier operates at day grain, doesn't gate intra-day windows) | NEW UAC SSOT `VENUE_SESSION_HOURS` + `EXPECTED_OUTSIDE_TRADING_HOURS` reason for ohlcv_15m / book_snapshot during off-hours |
|14 | Per-instrument lifecycle (ETF listed_at, futures expiry, options last-trade-date) | `instruments-store-tradfi/…` catalog (instruments-service) | ⚠️ partial | ❌ — classifier only does day-level | ❌ | Wave 3 v2 enumerator must read TradFi catalog + emit per-instrument NOT_LISTED / DELISTED / EXPIRED |

**CeFi dimensions:**

| # | Dimension                          | UAC SSOT                                                                                       | Status | Classifier-aware? | Cascade-wired? | Gap                                                                                |
| - | ---------------------------------- | ---------------------------------------------------------------------------------------------- | ------ | ----------------- | -------------- | ---------------------------------------------------------------------------------- |
|15 | Venue launch dates                 | `unified_api_contracts.registry.venue_launch_dates.CEFI_VENUE_LAUNCH_DATES` (20 venues)         | ✅ | ✅ (`_classify_cefi` post UTL@7276cca1) | ✅ | None — Wave 1 shipped                                                              |
|16 | Per-instrument lifecycle (perp listing, futures expiry, instrument_type changes) | `instruments-store-cefi/by_venue/{venue}/instruments.parquet` (Tardis-derived catalog) | ⚠️ partial | ❌ | ❌ | Wave 3 v2 enumerator + catalog-aware write-gate at MTDS adapters                 |

**DeFi dimensions:**

| # | Dimension                              | UAC SSOT                                                                  | Status | Classifier-aware? | Cascade-wired? | Gap                                                                        |
| - | -------------------------------------- | ------------------------------------------------------------------------- | ------ | ----------------- | -------------- | -------------------------------------------------------------------------- |
|17 | Chain genesis dates                    | `unified_api_contracts.registry.chain_env.CHAIN_GENESIS_DATES`            | ✅ | ✅ (`_classify_defi`) | ✅ | None                                                                       |
|18 | Protocol launch dates per chain        | `unified_api_contracts.registry.chain_env.PROTOCOL_LAUNCH_DATES`          | ✅ | ⚠️ partial (Wave 1 enumerator uses it; classifier doesn't directly) | ✅ via enumerator | Wave 3 — extend `_classify_defi` to use PROTOCOL_LAUNCH_DATES for finer per-(chain, protocol) classification |
|19 | Per-pool lifecycle (deployed_at, deactivated_at) | `instruments-store-defi/…` catalog (sparse, expansion in scope per `defi_master`) | ❌ | ❌ | ❌ | Wave 3 v2 enumerator + per-pool catalog expansion (defi_master plan)        |

**Cross-cutting dimensions:**

| # | Dimension                                                       | Where it should live                              | Status | Gap                                                                          |
| - | --------------------------------------------------------------- | ------------------------------------------------- | ------ | ---------------------------------------------------------------------------- |
|20 | Per-data-type zero-activity bar shapes (ohlcv 0-vol, trades 0-qty, book carry-forward, depth quotes carry-forward, derivative_ticker carry-forward, odds_snapshot carry-forward) | UTL `zero_activity_bars` helper (NEW)              | ❌ | Wave 3.M — full per-data-type template SSOT                                  |
|21 | Catalog-aware write-gate at MTDS / MDPS / features-* adapters    | UTL `ManifestWriter.record_empty(instrument_catalog=…)` callable + adapter wiring | ⚠️ partial | UTL `EmptyFromLiveInstrumentError` shipped; adapters not yet wired to pass `instrument_catalog` reference at construction |
|22 | Cross-service cascade — MDPS / features-* / ml / strategy / execution propagate `expected_unattempted` + `EXPECTED_*` from upstream manifest | Per-service manifest read + propagation logic | ❌ | Wave 3 cross-service cascade — multi-day                                    |
|23 | Data-status panel reflects 4-state capture_status (4-bucket coverage) | deployment-api `data_status_service.py` + deployment-ui | ⚠️ partial | Wave 3 — 4-bucket coverage breakdown + per-instrument×per-day calendar viz   |
|24 | GCS-side past data alignment with manifest semantics            | One-shot migration scripts + per-asset-group rescan | 🟡 in flight | Today's Wave 2.M migration covered the blank-reason rows. Future migrations as new typed reasons land per the taxonomy-expansion process |
|25 | prior_LTP carry-forward source for zero-activity bars            | UTL `get_prior_ltp` helper + lookback-N-days fallback | ❌ | Wave 3.M task                                                                |

**Net gap summary** — 11 dimensions need NEW SSOTs, classifier extensions, or UTL helpers; 6 dimensions need
consumer-side wiring (cascade); 8 dimensions are fully shipped today.

**Tasks added (incremental over existing Wave 3 / 3.S / 3.M):**

- [ ] [UAC] P1. **Half-day sessions calendar.** NEW SSOT
      `unified_api_contracts/registry/half_day_sessions.py` — `HALF_DAY_SESSIONS: dict[venue, list[(iso_date,
      close_time_HHMM, reason)]]`. Populate per CME / NYSE / NASDAQ documented half-days (Thanksgiving Friday,
      Christmas Eve, etc.). Wire `non_trading_day_reason` to also return `EXPECTED_PARTIAL_HALF_DAY` when applicable.
- [ ] [UAC] P1. **Intra-day session hours.** NEW SSOT
      `unified_api_contracts/registry/venue_session_hours.py` —
      `VENUE_SESSION_HOURS: dict[venue, dict[weekday, list[(open_HHMM_TZ, close_HHMM_TZ)]]]`. Cover NYSE 9:30-16:00 ET,
      CME equity-index futures 17:00 ET prev → 16:00 ET, FX continuous (Mon 5pm ET → Fri 5pm ET), CBOE etc.
      NEW `EXPECTED_OUTSIDE_TRADING_HOURS` reason in `EmptyConfirmedReason`.
      Used by ohlcv_15m / book_snapshot adapters to gate intra-day shards.
- [ ] [UAC] P1. **Understat covered leagues + seasons.** NEW SSOT
      `unified_api_contracts.canonical.domain.sports.understat_coverage.UNDERSTAT_COVERED_LEAGUES:
      dict[league_id → list[season_id]]` with the 5 covered leagues (EPL / La Liga / Serie A / Bundesliga / Ligue 1)
      and their season ranges. Classifier extension: pre-fixture-day check returns
      `EXPECTED_SOURCE_DOES_NOT_COVER_LEAGUE` for understat shards outside this set.
- [ ] [UAC] P1. **Per-league season bounds for footystats.** Extend `FOOTYSTATS_SEASON_IDS` with
      season_start / season_end tuples (already partly available — needs explicit bounds-check helper
      `get_footystats_season_window(league, day) -> tuple[start, end] | None`). NEW
      `EXPECTED_PRE_SEASON` / `EXPECTED_POST_SEASON` reasons; classifier branch.
- [ ] [UAC] P1. Two new EmptyConfirmedReason enum values: `EXPECTED_OUTSIDE_TRADING_HOURS` and
      `EXPECTED_OUTSIDE_TRANSFER_WINDOW` and `EXPECTED_PRE_SEASON` and `EXPECTED_POST_SEASON` and
      `EXPECTED_SOURCE_DOES_NOT_COVER_LEAGUE`. (5 new typed reasons.)
- [ ] [UTL] P1. **Classifier extension** — `_classify_sports` consumes the new SSOTs (transfer_windows,
      footystats_season_bounds, understat_coverage) returning the appropriate typed `EXPECTED_*` reason. Same
      discriminated `(capture_status, error_reason)` shape as today.
- [ ] [UTL] P1. **Classifier extension** — `_classify_tradfi` consumes the half-day calendar +
      session hours SSOTs returning `EXPECTED_PARTIAL_HALF_DAY` / `EXPECTED_OUTSIDE_TRADING_HOURS` where applicable.
- [ ] [UTL] P1. **Classifier extension** — `_classify_prediction` consumes the canonical-question-group lifecycle
      SSOT returning `EXPECTED_INSTRUMENT_NOT_LISTED` / `EXPECTED_INSTRUMENT_DELISTED` for outside-active-window
      prediction-shard dates.
- [ ] [DOCS] P1. CLAUDE.md "Three-category empty-output decision" rule extension to enumerate the new typed
      reasons. Codex `02-data/honest-absence-downstream-handling.md` per-service consumer-class audit table extension
      (per-reason: ML NaN-fill / execution skip / rolling-window denominator policy).
- [ ] [SCRIPT] P1. **Migration: re-classify already-flipped attempted_failed/LegacyBlankErrorReasonError rows
      using the extended classifier.** After the Wave 2.M migration today flipped 1.24M cefi + 5,159 tradfi +
      685 defi rows to attempted_failed/LegacyBlankErrorReasonError, those rows that should actually be
      typed (e.g. rows during understat-not-covered-league fixtures, cefi-perp pre-listing dates per
      catalog) are recoverable on the next migration pass. New reconciler:
      `reconcile_legacy_blank_to_typed_reason.py` — walks the manifest, finds attempted_failed/
      LegacyBlankErrorReasonError rows, re-classifies via the extended classifier, flips back to
      empty_confirmed/EXPECTED_* if a typed-reason rule fires (otherwise leaves as attempted_failed for
      retry).

**Sequencing note:** the new typed reasons + classifier extensions ship before the migration script (the
reconciler depends on the extended classifier). Tasks can be parallelised within Wave 3.S (sports) and
Wave 3.T (tradfi) and Wave 3.P (prediction) — distinct asset_group surfaces.

---

## Phase 4 — Data-status UI + alerts (parallel with Phase 2 after Phase 1 lands)

### Phase 4.A — deployment-api

- [x] [SCRIPT] P0. New per-pillar write-gate failure breakdown in `data_status_service.py`: - Aggregate
      `attempted_failed` rows by `error_reason` → return per-shard breakdown - New columns: `failed_row_count`,
      `failed_nan_ratio`, `failed_schema`, `failed_cluster`, `failed_timestamp_bias`, `failed_malformed`,
      `failed_empty_placeholder_backfill`. **SHIPPED 2026-05-07 deployment-api@453836d**: helper
      `_compute_failure_pillar_counts(df)` buckets `error_reason` strings by typed-error class prefix into the closed
      taxonomy `_FAILURE_PILLAR_KEYS`. Pillars wired today: `failed_timestamp_bias` (UpstreamTimestampBiasError),
      `failed_malformed` (MalformedTickFieldError), `failed_cluster` (ClusterCoverageError +
      MissingClusterValidationError), `failed_lookahead_bias` (LookaheadBiasError), `failed_other` (catch-all for
      unrecognised reprs — surfaces future error classes BEFORE the taxonomy is updated, so new failure modes don't
      silently disappear). Placeholder pillars seeded for `failed_nan_ratio`, `failed_schema`,
      `failed_empty_placeholder_backfill`, `failed_missing_available_at` per the plan column list — they show count=0
      until those typed-error classes ship in writegate Phase 1A.future. Surfaced on the venue entry as
      `failure_pillars: dict[str, int]` alongside existing `capture_status_counts`. 8 unit tests cover empty df,
      missing-columns, every registered prefix, unrecognised-prefix routing to `failed_other`, NaN handling, and
      pillar-key contract guard.
- [x] [SCRIPT] P0. **Per-empty_reason breakdown — operator-visible payoff for Tier 3D.1/3D.2/3B/2.E.2.** Companion to
      the `failure_pillars` rollup above; bundles `capture_status=empty_confirmed` rows by `error_reason` per the closed
      taxonomy from `unified_api_contracts.canonical.crosscutting.honest_coverage.EMPTY_CONFIRMED_REASONS` (11 known
      reasons + `empty_unclassified` catch-all). **SHIPPED 2026-05-07 deployment-api@7d57056**: helper
      `_compute_empty_reason_counts(df)` exact-matches `error_reason` against `_EMPTY_REASON_KEYS`. Surfaced on the
      venue entry as `empty_reasons: dict[str, int]` alongside `failure_pillars`. The `empty_unclassified` catch-all
      acts as a back-fill progress indicator — non-zero whenever a venue still has legacy null-reason rows the Tier 3D.1
      reconciler hasn't reached. 9 unit tests cover empty df, missing capture_status / error_reason columns, every
      closed-set member routing to its bucket, unrecognised reason → unclassified, NULL/NaN/blank → unclassified,
      captured/attempted_failed exclusion, mixed aggregation, and a closed-set drift guard against UAC
      `EMPTY_CONFIRMED_REASONS` (caught 2 missing reasons during dev). Without this rollup, the Phase 2.E + Phase 3.D +
      Phase 3.B work that stamps typed reasons on every empty_confirmed row stays invisible to the operator.
- [x] [SCRIPT] P0. New endpoint `GET /data-status/leaf-stats` — returns per-leaf-parquet live stats: row_count,
      per-column non_null_count, per-column NaN ratio, `available_at` envelope (min/max/null_count), and file size.
      Distinct from existing `/schema` endpoint (declared `SchemaContract` from UAC, not actual stats). **SHIPPED
      2026-05-07 deployment-api@3b0477a**: new `get_leaf_parquet_stats()` helper in `services/shard_detail.py` (mirrors
      `get_shard_detail`'s resolution shape via `_gcs_path_for_shard` so a single coordinate tuple lights all three
      views off the same parquet); new `LeafParquetStats` / `LeafParquetColumnStat` / `LeafAvailableAtEnvelope` Pydantic
      models in `types/shard_detail.py`; new `GET /api/data-status/leaf-stats` route in `routes/shard_detail.py`.
      Bounded at 500k rows with the `truncated` flag set on oversize parquets. Never raises for data-level failures:
      missing path / corrupt parquet / read errors all resolve to `available=False` with a typed `error_reason` so the
      UI can render the diagnostic state without a 500. 7 unit tests cover unresolved path, parquet read failure,
      successful read with per-column NaN ratios + available_at envelope, missing-`available_at`-column failure mode
      (writegate Phase 1A.future `MissingAvailableAt`), oversize-parquet truncation, zero-row parquet (no div-by-zero),
      and coord echo. **DEFERRED to follow-up commit**: TTL cache (currently each request re-reads from GCS — fine for
      the schema-modal use case which is one-click-per-modal, not a hot path); lift to a 5-min TTL cache once Phase
      4.B.3 modal lands and reveals real query patterns.
- [ ] [SCRIPT] P0. Live-vs-historical envelope alert: when historical-mode produces a `data_type` for a date in the live
      window AND `live_pipeline_already_wrote = true` → emit `LIVE_HISTORICAL_DOUBLE_WRITE` warning event.
      **Investigation 2026-05-07**: multi-repo write-time guard. Needs (a) a UAC `LIVE_HISTORICAL_DOUBLE_WRITE` event
      type addition, (b) UTL `manifest_writer` write-time guard that detects the double-write at `record_captured` time,
      (c) MDPS / MTDS / instruments-service callsite passing `mode=batch|live` so the guard knows which side we're on.
      Cross-cuts UAC + UTL + 3 services — bigger coordination than items 1/2. Successor is this same plan item, paired
      with the Phase 1A.future error-class additions (`NanRatioExceededError`, `SchemaMismatchError`,
      `EmptyPlaceholderBugBackfill`, `MissingAvailableAt`) so the new event class lands alongside its peers.

### Phase 4.B — deployment-ui (unified-trading-system-ui)

- [x] [SCRIPT] P0. Render new `attempted_failed` reasons distinctly per typed error in the data-status panel: Distinct
      color + icon per (`EmptyPlaceholderBugBackfill`, `ClusterCoverageError`, `UpstreamTimestampBiasError`,
      `MalformedTickFieldError`, `MissingAvailableAt`, `ClusterCoverageError(historical)`,
      `RAW_TICK_PARTITION_MISMATCH`). **SHIPPED 2026-05-07 deployment-ui@a7384a0 + @621f0b3**: new `TypedReasonBadges`
      component renders one colored pill per non-zero count for both the failure_pillars (typed-error class prefix
      taxonomy) and empty_reasons (UAC `EMPTY_CONFIRMED_REASONS` closed set + back-fill catch-all) rollups
      deployment-api emits per venue. 11 unit tests cover empty/zero render, failure-pillar-first ordering, count +
      tooltip wiring, click-through mode vs static, and a closed-set drift guard against deployment-api
      `_FAILURE_PILLAR_KEYS` + `_EMPTY_REASON_KEYS`. Component wired into `DataStatusTab.tsx` venue summary line between
      the existing "blocked on raw" badge and BucketCountsBadge so every venue with any typed-failure or typed-empty
      surfaces the breakdown without expanding the row. **DEFERRED**: drill-down per reason → leaf parquet + audit
      report link — depends on Phase 4.A.3 leaf-schema endpoint (next item below).
- [x] [SCRIPT] P0. Surface per-pillar write-gate failure breakdown as a stacked-bar visualisation per shard. **SHIPPED
      2026-05-07 deployment-ui@a7384a0 + @621f0b3**: new `FailurePillarStack` component renders a proportional
      horizontal stacked bar with one segment per non-zero pillar (zero counts suppressed; layout stays deterministic).
      Wired alongside `TypedReasonBadges` on the venue summary line. 13 unit tests cover proportional widths, total
      emission via `data-failure-total`, click-through mode, prefix namespacing, and closed-set ignore.
- [x] [SCRIPT] P0. Schema-view modal (per-leaf parquet) — call new `/leaf-stats` endpoint; render columns + types +
      row_count + NaN ratio + `available_at` envelope. **SHIPPED 2026-05-07 deployment-ui@8f630a6**: new
      `LeafSchemaModal` component renders three blocks: (1) header with gs:// URI + row count + column count +
      file size + truncated hint when applicable; (2) `available_at` envelope (present/missing badge + min/max +
      null count; missing renders as a writegate contract violation per CLAUDE.md "available_at is per-row,
      write-time, equal to live-pipeline-arrival"); (3) per-column table with NaN-ratio color coding (muted at 0%,
      yellow > 0%, amber ≥ 10%, red ≥ 50%). Companion `fetchLeafParquetStats()` API client + typed response shape
      (`LeafParquetStatsResponse` / `LeafParquetColumnStat` / `LeafAvailableAtEnvelope`) added to `client.ts`.
      15 unit tests cover loading state, fetch error, unavailable response with error_reason, missing-available_at
      contract violation, successful payload with per-column NaN ratio rendering + boundary inclusivity for the
      color thresholds, oversize-parquet truncated hint, plus pure-helper tests for `nanRatioColor` +
      `formatNanRatio`. **DEFERRED to follow-up commit**: mounting the modal into a click-target on the venue
      summary row — separate layout edit so the modal can be reviewed + reverted independently. Pairs with the
      Phase 4.B.1 `TypedReasonBadges` `onBadgeClick` callback already plumbed through (the badge click is the
      natural drill-down trigger to open this modal).
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
- [x] [SCRIPT] P0. Document the post-merge baseline at
      `unified-trading-pm/codex/02-data/honest_coverage_baseline_2026_05.md`: Per-(service, asset_group, data_type)
      baseline %, per-error_reason failure breakdown, set as the ratchet floor — future merges that drop coverage
      below this % fail QG (per parent plan §"coverage_ratchet_policy"). **SHIPPED 2026-05-07 PM@5c876f9d** (bundled
      due to workspace prek-race; baseline doc edits authored same session): doc promoted from `status=planned` to
      `status=draft` with the full methodology + ratchet design + table schema. Sections covered: exact formulas
      for the 4-state capture taxonomy (`captured` / `empty_confirmed_with_reason` / `empty_unclassified` /
      `attempted_failed` / `expected_unattempted`) + 3 derived percentages (`honest_coverage_pct` /
      `attempt_coverage_pct` / `unclassified_drag_pct`) + the sanity invariant; baseline-table column schema (one
      seed row per asset_group, per-data_type rows TBD via measurement script); ratchet schedule (±0.5pp default
      tolerance, monthly cadence, 99% long-term floor); QG ratchet implementation outline; override procedure with
      explicit override-log section. **DEFERRED**: per-data_type rows + numeric cells — populated by an operator-run
      measurement script on a same-region GCE VM. Reference impl: TBD
      `unified-trading-pm/scripts/qg/measure-honest-coverage.py` (writegate Phase 5 follow-up — needs same-region VM
      + cross-asset-group manifest read). Once cells are filled, the QG ratchet at
      `unified-trading-pm/scripts/qg/honest-coverage-ratchet.sh` reads this doc as the frozen baseline.
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
