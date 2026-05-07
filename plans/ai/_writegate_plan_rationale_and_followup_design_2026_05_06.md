---
type: rationale
locked_by: live-defi-rollout
locked_since: 2026-05-06
created: 2026-05-06
companion_plans:
  - writegate_honest_coverage_endtoend_2026_05_06.plan.md
  - predictions_canonical_question_group_polymarket_migration_2026_05_06.plan.md
status: drafted
---

# Writegate-Honest-Coverage + Predictions — Rationale + Follow-Up Design Notes

This is a meta document — not a plan with executable todos. It explains **why** the writegate-honest-coverage plan + the
predictions plan are shaped the way they are, **what's still open** for the remaining follow-up plans (B / C / D), and
**what production-grade execution requires** end-to-end across migrations / manifest / GCS / code / re-downloads /
backfills / deletions / re-validations.

The intended reader is the agent (or human reviewer) executing the writegate plan + drafting follow-up plans B/C/D. The
intended effect is that nothing in this work-package is taken on faith — every design decision has its rationale here,
and every temporary state has a named successor plan documented. Future agents reading this won't undo the work because
they understand why it was done.

---

## Workflow note (also in each plan)

Direct git workflow. NOT quickmerge. Per user direction 2026-05-06: `git add` + `git commit` +
`git push origin live-defi-rollout` directly. Quickmerge per commit is friction without benefit on a multi-week
multi-repo plan.

Before every commit + push: `git fetch origin` → list incoming commits with `git log HEAD..origin/live-defi-rollout`.
For each: compatible (rebase + continue), touches plan files (read diff, adapt or flag), direct conflict (DO NOT revert
silently — flag with hash + author + file:line + summary, pause that file, continue on unaffected files). After push,
re-check for race-incoming commits.

Concurrent streams running in parallel: writegate-honest-coverage (this work-package), sports phantom recovery
(`af-backfill-*` VMs + 5 follow-on entity VMs — see writegate plan §"Concurrent in-flight stream"), and (when drafted)
Plans B / C / D. Coordinate; don't undo each other's work.

---

## Why the writegate plan + predictions plan are shaped this way

### Cross-cutting principles (codified in CLAUDE.md as of 2026-05-06)

The user articulated these explicitly during the 2026-05-06 design conversation. They bind every plan in this
work-package and were added to workspace `unified-trading-pm/cursor-configs/CLAUDE.md` as enforceable rules so future
agents inherit them:

1. **Production-grade `>99%` means real `>99%`.** Denominator clipped to legitimately-coverable shards (per
   `SOURCE_COVERAGE_START` / `KNOWN_COVERAGE_GAPS` / `venue_trading_calendar`); numerator counts only honest captures
   (real rows passing the 4-pillar write-gate). NaN placeholders + partial bundles + silent per-schema drops do not
   count toward coverage.
2. **Single SSOT only — no double-SSOT in data-saving methodology.** Where two paths produce the same outcome, one is
   deleted. No coexistence of `_create_empty_output()` and `_handle_empty_tick_data()`; no `_ensure_timestamp` shim
   alongside per-source `stamp_available_at_*` helpers; no parallel v3-shape `_write_manifest_records` alongside the v6
   canonical writer; no inline NaN-ratio gate alongside UTL `write_gate_helper`; no per-service phantom-audit drift
   probe alongside UTL `manifest_audit`.
3. **Schema, manifest, GCS, code rewrites sanctioned wherever the SSOT requires.** No backwards-compatibility shims, no
   fallback readers for legacy shapes (one documented exception: hive-vocab `category=` → `asset_group=` per existing
   CLAUDE.md asset-group section). Migration scripts replace fallback readers; fallback readers get deleted.
4. **Live = batch — same data, same fields, same timing semantics, different sources OK.** Only the SOURCE differs;
   historical writes timestamped with the live-pipeline-equivalent `available_at`. Banned: separate live-only data_types
   like `LINEUPS_PRE_MATCH` vs `LINEUPS_POST_MATCH`; field sets that diverge between live + batch parquets.
5. **`available_at` is per-row, write-time, equal to live-pipeline-arrival.** Per-source rules in UAC
   `availability_semantics.AVAILABILITY_AT_SEMANTICS`. Never derived at read-time.
6. **Cluster validation MANDATORY at `record_captured` for bundled shards.** No opt-out, no helper-call-pattern. Runtime
   guard (UTL) + static guard (QG STEP 5.64).
7. **Three-category empty-output decision tree** (A: source returned 0 ticks → `record_empty`; B: ticks present, all
   outside the requested day → `record_failed(UpstreamTimestampBiasError)` + paired upstream MTDS partitioner-validation
   fix; C: rows in window, downstream calc dropped due to malformed fields → `record_failed(MalformedTickFieldError)`).
   NO fourth category. NO silent NaN placeholder rows.
8. **Temporary state must have named successor plan.** No silent "fix later." Every partial implementation lists its
   named successor in the plan's `## Temporary states + their canonical follow-up plans` section.
9. **Per-VM shard isolation for concurrent backfills.** Every multi-worker backfill sets `VM_NAME=<unique>` +
   `MANIFEST_PER_VM_SHARDS=true`. Runtime guard + QG STEP 5.66.
10. **Prediction market lifecycle timing.** Instrument definitions capture `market_created_at` / `resolution_time` /
    `settlement_time` per market_id. MTDS respects lifecycle bounds. LookaheadBiasError per-market-aware.

### Design decisions specific to writegate-honest-coverage

**Why bundle Q1 (MDPS empty-output) + Q3 (cluster validation) into one plan:** both redefine the contract of
`ManifestWriter.record_captured`. Q1 says "captured implies non-empty real data, not 1440 placeholders." Q3 says
"captured implies cluster-coverage met." Same contract, two facets. Sequential delivery would re-edit `record_captured`
twice with regression risk; bundled delivery designs the unified write-gate decision tree (record_empty for path A,
record_failed-with-typed-reason for paths B/C/cluster-incomplete) coherently.

**Why expand Q1's scope beyond the 2 confirmed callsites to all 53:** the parent HANDOVER scoped only
`defi/swap_adapter.py:106` + `cefi/trades_adapter.py:74`. Real count from
`app/adapters/{cefi,defi,tradfi,sports,prediction}/` is 53 `_create_empty_output` references. Under the user's "no
double-SSOT, production-grade" rule, the helper itself has to die — leaving it around invites future authors to default
to it and reintroduce the bug. Deleting `_create_empty_output` from `base_adapter.py` forces every callsite-author to
make the A/B/C decision explicitly.

**Why path B is `record_failed`, not `record_empty`:** path B (ticks present, all fall outside the requested day after
interval filter) is upstream corruption — partition mislabeled at MTDS write-time, source replay covered wrong window,
or clock-skew. Treating it as honest empty would silently accept a real bug. The fix lives at MTDS `raw_tick_hive.py`
partitioner-validation; MDPS just needs to detect + route to `record_failed(UpstreamTimestampBiasError)` so operators
see the typed reason in the data-status panel and can investigate the upstream.

**Why sports per-fixture sharding moved in-scope:** user direction 2026-05-06: ML predictions are fixture-level; without
per-fixture sharding, can't drill down on missing fixtures or fixture-specific stats. League stays as a higher rollup
grouping (data-status panel filtering), NOT the shard atom. Anything that breaks (MTDS reader paths, MDPS sports
adapter, features-sports input pipeline, deployment-ui drill-down) is fixed within the writegate plan.

**Why `match_end_time` detection cascade replaces 120min default:** user direction 2026-05-06: SFI progressive-stats
freeze detection (re-uses the halftime detector algorithm — `≥4-of-6` freeze threshold across 6 columns) is more
accurate than `kickoff + 120min` for cup matches with extra time. Cascade: api_football native → SFI progressive-freeze
→ footystats / understat → low-confidence kickoff+120min fallback. Audit column tags which detector won; data-status
surfaces low-confidence fixtures.

**Why predictions get their own plan instead of being folded in:** the canonical_question_group SSOT is greenfield UAC
work (`CanonicalQuestionGroup` enum + classifier with stability hash + per-market lifecycle module + 3 mapping
registries) plus a substantial classifier-derived re-grouping migration of existing per-base_asset parquets. Roughly 2-3
weeks of work. Folding it into writegate would (a) blow that plan's scope past what's reviewable in one sitting, and (b)
create unnecessary serialisation — predictions can run in parallel because it touches a separate UAC namespace
(`unified_api_contracts.predictions.*`) and a separate cluster registry slot (`PREDICTION_GROUPS`).

### Why the 4-plan packaging for follow-ups

Plans B / C / D / (predictions = A) are shaped to maximise parallel execution while respecting hard dependencies:

- **Plan A (predictions)** — `predictions_canonical_question_group_polymarket_migration_2026_05_06.plan.md` (drafted
  2026-05-06). Independent of writegate at the file level (separate UAC namespace, separate registry slot). Can run in
  parallel with writegate execution.
- **Plan B (UTL/UAC lift triple)** — DAG SSOT + NaN-ratio gate + phantom-audit drift-probe. Independent of writegate at
  the file level (UTL helpers + UAC registries that aren't in writegate's scope). Should ship before Plan D so
  multi-source merge can use the DAG.
- **Plan C (pre-flight + concurrency hardening + migration runbook)** — UTL `check_shard_freshness` tightening + per-VM
  shard isolation rule + `category=` GCS migration runbook. Independent at the file level. Coordination-sensitive
  (concurrent sports phantom recovery VM uses the per-service `d73565a` workaround that Plan C reverts after UTL fix).
- **Plan D (multi-source merge)** — depends on Plan B (DAG SSOT) and writegate (SOURCE_PRIORITY top-entry) to be in
  place. Ships last.

---

## What else to think about for follow-up plans (B / C / D)

### Plan B — UTL/UAC lift triple (Q #2 + Q #4 + Q #5)

Scope: lift three currently-inlined utilities to UTL/UAC. Mechanical work; 1-1.5 weeks.

**Q #2 — `feature_group → required_inputs[]` DAG SSOT in UAC.** Currently inlined 3 ways (features-onchain,
features-sports, features-delta-one). The DAG drives `LookaheadBiasError` enforcement — having three different DAGs
means three different lookahead-bias enforcement behaviours, which is a correctness regression in waiting.

Production-grade execution requires (per user framework):

- **Forward**: UAC `feature_dag.py` with `FEATURE_DAG: dict[FeatureGroup, FeatureNode]`. Each node has
  `required_inputs: tuple[InputSpec, ...]` (asset_group + data_type + horizon + required-flag), `output_schema`,
  `feature_horizon`. Per-service registries become facade imports.
- **Schema migration**: any per-service `*_FEATURE_REGISTRY` constants get re-exported from UAC; old per-service
  definitions deleted.
- **Manifest implication**: `feature_group` axis already in manifest v5/v6; no schema bump.
- **GCS rewrites**: none — features are computed, not stored as registry data.
- **Re-downloads**: none — DAG is metadata.
- **Backfills**: none — but `LookaheadBiasError` may newly fire on existing on-disk feature parquets if the prior
  per-service DAG was missing required inputs the canonical UAC DAG enforces. Each fired shard flips
  `attempted_failed[reason=LookaheadBiasViolation]` for re-attempt.
- **Deletion**: per-service DAG modules deleted (no compat shim).
- **Tests**: UAC parametrised tests across every `FeatureGroup` — assert input-spec resolves to a real (asset_group,
  data_type) in UAC; assert horizon is a valid timedelta; assert output_schema matches the actual on-disk parquet
  schema.
- **Validation**: end-to-end LookaheadBiasError smoke per service.
- **Temporary state forward**: none — full lift.

**Q #4 — NaN-ratio gate lift to UTL.** Currently in instruments-service `_validate_predictions_null_rates`
(FootyStats-only, hardcoded 5% / 20% thresholds).

Production-grade execution:

- **Forward**: UTL
  `write_gate_helpers.check_nan_ratio(df, *, thresholds: Mapping[str, float], feature_group: str | None) -> NanRatioExceededError | None`.
  UAC `nan_thresholds.NAN_RATIO_THRESHOLDS: dict[(asset_group, data_type, column), float]`.
  `ManifestWriter.record_captured` calls `check_nan_ratio` internally when thresholds exist for the
  `(asset_group, data_type)`.
- **Schema migration**: existing on-disk parquets unchanged; thresholds applied at write-time going forward.
- **Manifest implication**: shards that newly fail the NaN gate flip from `captured` to
  `attempted_failed[reason=NanRatioExceeded(column, observed, threshold)]`. Reconciler script flips historical shards.
- **GCS rewrites**: none required for the gate itself; reconciler may re-attempt shards after upstream re-fetch.
- **Re-downloads**: yes — for any shard that flips to `attempted_failed[NanRatioExceeded]`, re-attempt may pull cleaner
  upstream data. If upstream is the issue, escalate per the data-quality bug class (similar shape to path B/C in
  writegate plan three-category decision).
- **Backfills**: scoped to shards that flipped.
- **Deletion**: instruments-service `_validate_predictions_null_rates` inline implementation deleted;
  orchestrator.py:4099–4147 calls UTL helper.
- **Tests**: UTL parametrised tests across asset_group × data_type × column matrix; assert correct error fires when
  threshold breached, no-op when below.
- **Validation**: write-gate quartet integration test (writegate plan Phase 5 todo currently has this as
  deferred-pending-Plan-B; Plan B completes the test).
- **Temporary state forward**: none — full lift.

**Q #5 — phantom-audit drift-probe lift to UTL.** Currently in
`instruments-service/scripts/reconcile_phantom_manifest_rows_all.py:64–152` (5-axis drift logic + `ASSET_GROUP_CONFIG`).
Used by every backfill / reconciliation script.

Production-grade execution:

- **Forward**: UTL `manifest_audit.py` module exposing
  `probe_phantom_rows(manifest, bucket, asset_group, *, drift_axes, dry_run) -> PhantomAuditResult`. 5 drift axes as
  named enum: `HiveVocab` / `InstrumentTypeCasing` / `EmptySchema4InstrumentType` / `PathPrefix` /
  `ChainBundleEquivalence`. `ASSET_GROUP_CONFIG` lifted to UAC.
- **Schema migration**: none — module is utility code.
- **Manifest implication**: existing `attempted_failed[reason=phantom_*]` rows continue to be processable by the lifted
  utility; behaviour preserved.
- **GCS rewrites**: none.
- **Re-downloads**: none — utility code.
- **Backfills**: existing reconciliation runs unchanged in behaviour (utility is the same logic); future asset-groups
  added by editing UTL once instead of duplicating across scripts.
- **Deletion**: instruments-service `scripts/reconcile_phantom_manifest_rows_all.py` shrinks to ~30-line wrapper calling
  the UTL helper. The 5-axis drift logic + `ASSET_GROUP_CONFIG` deleted from the script (lifted, not duplicated).
- **Tests**: UTL parametrised tests across each drift axis × each asset_group; assert detection works; integration test
  against a sample manifest with each drift type seeded.
- **Validation**: re-run existing reconciliation scripts post-lift; assert results match pre-lift.
- **Temporary state forward**: none — full lift.

**Combined timeline**: 1-1.5 weeks.

### Plan C — Pre-flight tightening + per-VM concurrency rule + migration runbook (Q #6 + Q #8 + run-status)

Scope: harden UTL `check_shard_freshness` + codify per-VM shard isolation as workspace QG-enforced rule + run the
`category=` GCS migration runbook to completion.

**Q #8 — UTL `check_shard_freshness` two bugs:**

- (a) Doesn't include `league_id` (or any v5/v6 column beyond venue + data_type + date) in match key. Workaround:
  instruments-service `d73565a` orchestrator patch defers per-(date, data_type, league_id) to per-entity handlers when
  sports per-league entities are expected.
- (b) Treats `attempted_failed` as "fresh" — bug. Re-attempts blocked. Per
  `feedback_check_shard_freshness_ignores_capture_status.md`.

Production-grade execution:

- **Forward**:
  `check_shard_freshness(row_key: Mapping[str, object], capture_status_filter: tuple[str, ...] = ("captured",))`. Match
  keys at full v5/v6 granularity (any column passed in `row_key`). Default `capture_status_filter` = `("captured",)`
  only — `attempted_failed` and `empty_confirmed` get separate filter parameters.
- **Schema migration**: none — function signature change; existing manifest rows compatible.
- **Manifest implication**: behaviour change — formerly-skipped `attempted_failed` shards are now re-attempted. Watch
  for compute-resource spike on first run; cap with `--max-flips-per-run`.
- **GCS rewrites**: none directly; downstream re-attempts may rewrite parquets.
- **Re-downloads**: yes, for all `attempted_failed` shards that previously skipped.
- **Backfills**: as above.
- **Deletion**: instruments-service `d73565a` orchestrator patch reverted after UTL fix lands AND concurrent sports VM
  completes. Coordinate timing.
- **Tests**: UTL parametrised tests across capture_status_filter values; integration test against a manifest with mixed
  capture_status; assert correct subset matched.
- **Validation**: end-to-end smoke that previously-skipped shards now re-attempt; honest baseline re-measured.

**Q #6 — Per-VM shard isolation as workspace rule (codified in CLAUDE.md 2026-05-06 already)**:

- **Forward**: `ManifestWriter.__init__` runtime guard raises `MultiWorkerWithoutShardIsolationError` when multi-process
  detected without `MANIFEST_PER_VM_SHARDS=true`. New base-service.sh QG STEP 5.66 AST-walks launcher scripts that fork
  multi-process; asserts envvar setting.
- **Schema migration**: none.
- **Manifest implication**: per-VM shards under `_index/per_vm/{vm_name}.parquet` already exist as a pattern (per
  `feedback_manifest_reader_staleness_per_vm_fallback.md`); rule formalises it.
- **GCS rewrites**: none.
- **Re-downloads**: none — runtime+QG guard, no historical reprocessing.
- **Backfills**: none — guard catches future regressions, doesn't fix past ones (which were caught manually per
  `00f6352` / `619a32e`).
- **Deletion**: any launcher script that forks multi-process without per-VM isolation flagged by QG; fixed inline.
- **Tests**: UTL guard test (multi-process detection + envvar absence → raise); QG self-test (fixture launcher script
  with / without envvar → fails / passes).
- **Validation**: existing chunk-worker scripts (`run_vm_backfill_e2e.sh`, `sports_chunked_backfill.sh`) pass post-rule;
  flag any that don't.

**Migration run-status:**

- **`category=` → `asset_group=` GCS migration per asset_group**: confirm migration scripts exist for every asset_group
  (cefi, defi, tradfi, sports, prediction); run sequentially with verification (sample `gcloud storage ls` after each,
  assert ≥99% canonical hive vocab); after 100% migration AND a hold period confirms no readers fail, delete the
  `category=` legacy fallback reader. Per writegate plan Phase 3.A.
- **Polymarket residual `category=prediction` objects** — covered by Plan A (predictions). Mark as deferred-to-Plan-A in
  Plan C.

**Combined timeline**: 1 week (most of it is sequential verification of migration runbook on GCE).

### Plan D — Multi-source merge spec (Q #7)

Scope: extend SOURCE_PRIORITY from top-entry-only to multi-entry merge. Per user direction 2026-05-06:
timestamp-availability > coverage > info-richness > merge-different-fields tie-breakers; for fields different across
sources, merge with per-field provenance.

Production-grade execution:

- **Forward**: UAC `source_priority.SOURCE_PRIORITY: dict[(asset_group, data_type), list[SourcePriorityEntry]]`. Each
  entry: `source_key`, `rank_basis` (timestamps_available / coverage_pct / info_richness_score), `merge_strategy`
  (replace / merge_fields / append_rows). Multi-source merge algorithm in UTL
  `multi_source_merge.merge_per_field(rows: dict[source_key, pd.DataFrame], priority: list[SourcePriorityEntry]) -> pd.DataFrame`
  with per-field provenance audit columns (`{field}_source` per row).
- **Schema migration**: parquets gain per-field provenance audit columns. Schema bump for every multi-source data_type.
- **Manifest implication**: `(venue, data_type, …)` row keys remain at the bundle level; per-source row counts go in
  metadata. Cluster validation per-source.
- **GCS rewrites**: existing single-source parquets get re-merged with available alternative sources where applicable;
  reconciler script per data_type. Audit-column added.
- **Re-downloads**: yes — for data_types where alternative sources weren't previously captured but are needed for merge
  enrichment.
- **Backfills**: per data_type per multi-source-eligible window.
- **Deletion**: any per-service multi-source ad-hoc merge code (none confirmed yet — Plan D Phase 0 audits) deleted;
  canonical `multi_source_merge.merge_per_field` only.
- **Tests**: UTL parametrised tests across tie-breaker scenarios; integration test simulating each tie-breaker with
  synthetic source data.
- **Validation**: LookaheadBiasError now per-field-aware — feature at T can only consume a row's field where
  `field_available_at <= T`. End-to-end smoke per service.
- **Dependencies**: requires Plan B (DAG SSOT — for input resolution) and writegate (SOURCE_PRIORITY seeded with top
  entries). Ship last.

**Timeline**: 1.5-2 weeks.

---

## End-to-end production-grade execution requirements (every plan in this work-package)

Per user direction 2026-05-06 ("we're going to redo everything that needs to be done in migrations, manifest changes,
code changes, re-downloads, backfills, deleting of wrongly classified data, and redoing it, testing, validation checks,
etc."), every plan in this work-package must explicitly cover:

### 1. Forward path (new code uses new contract)

- Code edits per repo with file:line manifest in pre-audit.
- Schema additions / changes per affected data_type.
- New UAC / UTL / CLAUDE.md SSOTs — single registry, no duplicates.
- Contract tests parametrised over the relevant matrices.

### 2. Manifest changes

- Row-key shape changes (e.g. sports per-fixture sharding adds `fixture_id` to v5/v6 row key).
- New `error_reason` typed values for `attempted_failed` per new typed exception.
- Schema version bump if applicable (currently v6; bump to v7 when row-shape changes).
- Reconciler scripts that flip existing rows to new shape.

### 3. GCS rewrites

- Existing parquets that don't match the new shape get rewritten to the canonical path. Old path deleted after
  verification.
- Audit-column additions: `available_at`, `source`, `*_confidence`, `classifier_stability_hash`, `match_end_time_source`
  — wherever the design requires.
- Hive-key vocab migration where applicable (`category=` → `asset_group=`).

### 4. Re-downloads

- For every shard flipped to `attempted_failed`, identify whether the upstream is correct (re-attempt cleanly resolves)
  OR upstream needs paired fix first (e.g. MTDS partitioner-validation for path B `UpstreamTimestampBiasError`).
- For data_types newly enriched by multi-source merge (Plan D), re-download alternative sources where not previously
  captured.
- Compute-resource estimation per re-download: GCE VM hours, source API quota, downstream storage growth. Document in
  plan Phase 3 todos.

### 5. Backfills

- Reconciler-driven re-attempt of shards in batches; per-VM shard isolation per workspace rule.
- `--max-flips-per-run` halt safety; operator confirms first batch before lifting cap.
- Audit reports at `gs://{pid}-reconciler-audit/{run_id}/` per run.

### 6. Deletion of wrongly-classified data

- Old data_type=BTC parquets after Polymarket migration (Plan A).
- Old `(bookmaker, league)` sports parquets after per-fixture migration (writegate plan).
- Old midnight-UTC `_ensure_timestamp` rows after per-source `available_at` stamping (writegate plan).
- Old v3-shape `_write_manifest_records` rows after canonical v6 single path (writegate plan).
- Legacy fallback readers (`category=` hive vocab, pre-v5 manifest rows) after migration verifies clean.

### 7. Re-validating after redo

- Honest coverage baseline measured per service per asset_group post-migration.
- Ratchet floor activated — future merges that drop coverage below baseline fail QG (per
  `coverage_ratchet_policy_2026_04_19.plan.md`).
- LookaheadBiasError end-to-end smoke per service.
- Per-pillar write-gate integration test.

### 8. Testing

- Unit tests at the UTL/UAC/contract level (write-gate quartet, lifecycle gating, classifier stability, source
  priority).
- Integration tests at the service level (per-adapter / per-handler).
- End-to-end smoke at the workspace level (1 day × 1 venue × all 4 services for writegate; 1 canonical_group × 1 day for
  predictions).
- Fixture seeding in deployment-ui for new data-status panel states.

### 9. Validation checks

- Per-service `quality-gates.sh` green.
- UAC tests parametrised over every (asset_group, data_type) matrix.
- Cassette parity (existing `unified-api-contracts/tests/test_cassette_schema_parity.py`).
- Honest coverage baseline document committed to `unified-trading-pm/codex/02-data/honest_coverage_baseline_*.md`.

### 10. Documentation

- Per-plan `Why this plan exists` section explaining design choices.
- Per-plan `Cross-cutting principles` referencing CLAUDE.md.
- Per-plan `Coordination with sibling plans` listing overlap + sequencing.
- Per-plan `Tracked open questions / temporary states` section listing partial implementations + named successor plans
  (or `none deferred`).
- Workspace CLAUDE.md additions for new rules (codified 2026-05-06; future agents inherit).

---

## What NOT to do (anti-patterns this work-package explicitly rejects)

These come up in agent execution; flagging them so future agents don't slip:

1. **Don't silently revert incoming commits.** When you find an incoming commit that touches plan files, evaluate
   (compatible / adapt / direct conflict). For direct conflicts, FLAG to user — don't decide unilaterally.
2. **Don't add a third helper to "reconcile" two double-SSOT helpers.** Delete one. Per CLAUDE.md `§ No double SSOT`.
3. **Don't accept a temporary state without naming its successor plan.** Per CLAUDE.md
   `§ Temporary state must have named successor plan`.
4. **Don't write 1440-row NaN parquets, ever.** No silent placeholder rows. Per CLAUDE.md
   `§ Three-category empty-output decision`.
5. **Don't skip cluster validation for bundled shards.** UTL guard + QG STEP 5.64 catches it; don't try to suppress
   either. Per CLAUDE.md `§ Cluster validation MANDATORY`.
6. **Don't derive `available_at` at read-time.** Per CLAUDE.md `§ available_at is per-row, write-time`.
7. **Don't ship per-base_asset Polymarket parquets going forward.** Migration is the final shape; no compat shim. Per
   Plan A.
8. **Don't kill or revert sports phantom recovery VM commits without coordination.** Per writegate plan
   `§ Concurrent in-flight stream`.
9. **Don't forget per-VM shard isolation for concurrent backfills.** Per CLAUDE.md `§ Per-VM shard isolation`.
10. **Don't use quickmerge for these plans.** Direct git push to live-defi-rollout per user direction 2026-05-06.

---

## Summary

The work-package consists of 5 plans:

- **writegate-honest-coverage** (drafted) — MDPS empty-output A/B/C + cluster validation contract + sports
  `available_at` correctness + sports per-fixture sharding + MDPS v6 columns wiring + retrospective migration. ~3.5
  weeks.
- **predictions** (drafted 2026-05-06) — canonical_question_group SSOT + lifecycle timing + Polymarket migration. ~3
  weeks. Independent of writegate.
- **Plan B** (UTL/UAC lift triple — TBD) — DAG SSOT + NaN-ratio gate + phantom-audit drift-probe. ~1-1.5 weeks.
  Independent.
- **Plan C** (pre-flight + concurrency + migration runbook — TBD) — `check_shard_freshness` tightening + per-VM rule +
  `category=` migration. ~1 week. Coordinate with sports phantom recovery.
- **Plan D** (multi-source merge — TBD) — depends on Plan B + writegate. ~1.5-2 weeks. Ships last.

All five plans share the 10 cross-cutting principles codified in CLAUDE.md 2026-05-06. All five include forward +
schema + manifest + GCS + re-download + backfill + deletion + re-validation per the production-grade framework above. No
temporary state without named successor. No double-SSOT. No quickmerge.

Future agents reading this document understand why these decisions were made and won't undo them.
