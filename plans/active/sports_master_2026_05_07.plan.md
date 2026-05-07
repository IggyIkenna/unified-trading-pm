---
name: sports-master
slug: sports_master_2026_05_07
date: 2026-05-07
owner: claude-code
status: active
priority: P1
phase: pending_approval
domain: sports
asset_group: sports
type: umbrella
locked_by: live-defi-rollout
locked_since: 2026-05-07
folds_in:
  - features_sports_honest_coverage_2026_05_05
  - sports_data_available_at_rename_2026_05_07
  - sports_fixtures_truthset_recovery_2026_05_06
  - sports_phantom_recon_and_failure_triage_2026_05_01
  - sports_predictions_e2e_2026_05_05 # sports half (predictions half goes to predictions_master)
  - market_tick_data_to_100pct_2026_05_05 # sports slice
related_plans:
  - master_to_live_defi_2026_05_23
  - writegate_honest_coverage_endtoend_2026_05_06
---

# Sports Master — asset_group umbrella

## Scope

Single source of truth for **sports asset_group** work. Per master plan asset-group readiness ladder, sports is
**ML-pipeline-running on representative sample** by 2026-05-23 (no live trading this cycle).

Covers:

- **Sports honest-coverage architecture**: `UpstreamReq` + `in_coverage(source, entity, league, date)` + per-feature
  expected denominator + 3-state NaN handling.
- **Sports fixture truthset recovery**: residual `empty_confirmed` reconciliation post-AF-enrichment.
- **Sports phantom audit + failure triage**: SFI_STANDINGS / open-meteo / api-football date-range reconciliation.
- **Sports `data_available_at` → `available_at` rename + GCS migration**: blocks writegate Phase 2.C strict-mode flip.
- **Sports MTDS slice to ≥99%** (per-(asset_group=sports, source, data_type, league_id, day)).
- **Sports half of `sports_predictions_e2e`**: legacy 288M ODDS_API row migration + MDPS SportsBucketAssignmentAdapter
  - feature-store run. (Predictions ML training half lives in `predictions_master`.)

**Not covered here**: predictions ML training + arb_calculator + Group E ML walk-forward (those belong in
`predictions_master_2026_05_07.plan.md`).

## Current state (2026-05-07)

- **honest-coverage architecture**: 16/49 = 33% done. Phase 1 UAC `UpstreamReq` + `in_coverage` started; Phase 2
  feature-compute `in_coverage` calls + NaN-state migration not yet shipped.
- **`data_available_at` rename**: Phase 1 (migration script) shipped; Phase 2 (operator GCE migration), Phase 3 (atomic
  4-repo source rename), Phase 4 (verify) pending.
- **Fixture truthset recovery**: 9/12 = 75% done. Phase 3 chain-runner needs operator trigger; Phase 4 drift audit
  - Phase 5 UI verification pending.
- **Phantom recon + failure triage**: 5/16 = 31% done. SFI_STANDINGS 100% failed (42/42); open-meteo silent for 2 days;
  api-football + understat UAC date-range mismatches blocking proper recon.
- **288M ODDS_API legacy row migration**: scoped per `sports_predictions_e2e`; not yet executed.

## Critical path

| Workstream                                                         | Status                              | Source                                      |
| ------------------------------------------------------------------ | ----------------------------------- | ------------------------------------------- |
| Sports `data_available_at` → `available_at` rename + GCS migration | Phase 1 shipped; Phase 2-4 pending  | `sports_data_available_at_rename`           |
| Sports honest-coverage architecture (Phase 1+2)                    | Phase 1 partial                     | `features_sports_honest_coverage`           |
| Fixture truthset recovery — chain runner + drift audit             | 75% done; operator action pending   | `sports_fixtures_truthset_recovery`         |
| Phantom recon — SFI_STANDINGS + open-meteo + UAC date ranges       | partial; operator decisions pending | `sports_phantom_recon_and_failure_triage`   |
| 288M ODDS_API legacy row migration + MDPS bucketing                | scoped; not started                 | `sports_predictions_e2e` (sports half)      |
| Sports MTDS slice to ≥99%                                          | partial                             | `market_tick_data_to_100pct` (sports slice) |

## Consolidated todos (P0/P1 only)

### Sports `data_available_at` → `available_at` rename (folded 2026-05-07; full DAG below)

**Cross-plan coordination**: this rename is **Stage 1** of the workspace-wide manifest migration. See
[`manifest_migration_master_2026_05_07.plan.md`](./manifest_migration_master_2026_05_07.plan.md) for the sequencing DAG,
conflicts (esp. `batch_handler.py` overlap with writegate Phase 2.C), VM impact matrix, and operator pause-resume
guidance. Stage 1 Phase 3 features-sports `batch_handler.py` rename SHOULD ship in the SAME commit as writegate Phase
2.C `_ensure_timestamp` shim deletion (avoids two-commit churn on same lines).

**Folded from `sports_data_available_at_rename_2026_05_07.plan.md`.** Original plan archived at
`plans/archive/sports_data_available_at_rename_2026_05_07.plan.md`. Phase 1 SHIPPED via `instruments-service@8050477`
(migration script + 11 unit tests). Phases 2-4 below are pending operator action + atomic source-rename.

**Why this matters now**: writegate plan Phase 2.C flips `LookaheadBiasError` to strict-mode workspace-wide. The flip
hard-fails every sports `record_captured` call as long as parquets stamp the prefixed `data_available_at`.

**Pre-audit manifest** (35+ callsites — full table in archived plan):

- UAC `unified_api_contracts/internal/schemas/_sports_*.py` — 4 schema files, 8 declarations.
- UTL `unified_trading_library/instruments_write_gate.py` — `DEFAULT_AS_OF_COLUMNS` tuple.
- UTL `unified_trading_library/point_in_time.py` — comment.
- instruments-service `engine/orchestrator.py` — 13 callsites in sports + weather paths.
- instruments-service `scripts/recover_fixtures_from_truthset.py` — 7 callsites.
- instruments-service `scripts/migrate_local_sfi_to_canonical.py` — 3 callsites.
- features-sports-service `cli/handlers/batch_handler.py` — reader-side (intersects writegate Phase 2.C
  `_ensure_timestamp` deletion).

#### Phase 1 — Migration script (SHIPPED 2026-05-07 via `instruments-service@8050477`)

- [x] [SCRIPT] P0. `instruments-service/scripts/migrate_sports_available_at_column.py` — idempotent column-rename
      migration; 4 cases (A renamed / B dedup / C already canonical / D outside scope); per-blob CAS via
      `if_generation_match`; HTTP pool tuned to `2*workers`.
- [x] [SCRIPT] P0. 11 unit tests covering all 4 cases.
- [x] [QG] P0. ruff clean; basedpyright argparse-`Any` errors out-of-scope (scripts/ excluded from typecheck).

#### Phase 2 — Operator runs migration (PENDING — sequenced after Phase 1)

- [ ] [OPERATOR] P0. Pause sports forward-poll VMs (`af-fwd-*`, `fs-fwd-*`, `tm-fwd-*`, `sfi-fwd-*`, `us-fwd-*`,
      `openmeteo-fwd-*`).
- [ ] [OPERATOR] P0. Pause sports backfill VMs (`af-backfill-*`, `fs-backfill-*`, etc.).
- [ ] [OPERATOR] P0. Launch migration VM in `asia-northeast1-c` per CLAUDE.md "same-region GCE VM" rule. VM name
      `sports-migrate-available-at-{ts}` (add prefix to `vm_zombie_watchdog.py` `VM_PREFIX_TO_BUCKET` first). Run
      `--dry-run` first; review; then full run.
- [ ] [OPERATOR] P0. Verify completion: spot-check ~20 parquets across years 2018-2026 — `pq.read_schema(uri).names`
      includes `available_at` and not `data_available_at`.
- [ ] [OPERATOR] P0. DO NOT resume FWD/BACKFILL VMs until Phase 3 atomic source rename ships.

#### Phase 3 — Atomic 4-repo source rename (PENDING — sequenced after Phase 2)

- [ ] [SCRIPT] P0. UAC: rename in 4 schema files (1 commit, push to `live-defi-rollout`).
- [ ] [SCRIPT] P0. UTL: rename `DEFAULT_AS_OF_COLUMNS` + `point_in_time.py` comment + tests (1 commit, push).
- [ ] [SCRIPT] P0. instruments-service: rename 13 orchestrator callsites + 2 scripts + tests (1 commit, push).
- [ ] [SCRIPT] P0. features-sports-service: rename `batch_handler.py` reference. **Coordinate with writegate Phase 2.C**
      `_ensure_timestamp` deletion if 2.C is mid-flight (fold into 2.C's batch_handler work instead of separate commit).
- [ ] [QG] P0. Run `quality-gates.sh` on all 4 repos sequentially before each push.
- [ ] [QG] P0. Workspace-wide ripgrep for stragglers — `rg -n 'data_available_at' --type py --glob '!.venv*'` returns
      ZERO non-test, non-archived results.
- [ ] [SKIP] `tests/unit/test_availability_stamping.py` in UTL — DIRTY with another agent's WIP, do NOT touch in Phase 3
      ship; coordinate with owner before final ship.

#### Phase 4 — Writegate Phase 2.C unblock + verify (PENDING)

- [ ] [SCRIPT] P0. Smoke-run sports backfill; confirm `record_captured` no longer raises `LookaheadBiasError`.
- [ ] [VERIFY] P0. Update writegate plan Phase 2.C "prerequisites" section to mark sports rename as shipped.
- [ ] [VERIFY] P0. Update master plan Q&A 14 to mark HIGH-2 as SHIPPED + record commit SHAs.
- [ ] [OPERATOR] P0. Resume forward-poll + backfill VMs.

### Sports honest-coverage architecture (`features_sports_honest_coverage`)

- [ ] [AGENT] P1. UAC `unified_api_contracts.sports`: add `UpstreamReq` dataclass + `FEATURE_UPSTREAM_REQUIREMENTS`
      dict + `in_coverage(source, entity, league, date) -> bool` helper.
- [ ] [AGENT] P1. Unit tests for `in_coverage` — coverage of each clip rule; pre-launch dates + paused leagues.
- [ ] [AGENT] P2. features-sports-service: feature compute path calls `in_coverage` per upstream before
      fetching/joining.
- [ ] [AGENT] P2. NaN handling — distinguish NaN-by-design (write parquet, manifest `captured`) from
      NaN-from-missing-upstream (manifest `empty_confirmed` no parquet) per
      `codex/02-data/honest-absence-downstream-handling.md`.
- [ ] [AGENT] P2. Backwards-compat — features computed before this change have manifest rows without coverage info;
      one-time migration or tolerate via reader-side fallback (per honest-absence doc).
- [ ] [AGENT] P3. Add `axis: per_feature_per_league_per_fixture_date` to `_sports_honest_coverage` in data-status
      reconciler. Per-feature-group denominator = (clipped fixture dates) × (in-coverage leagues).

### Fixture truthset recovery (`sports_fixtures_truthset_recovery`)

- [ ] [HUMAN] P0. Operator triggers Phase 3 chain runner per the recovery script.
- [ ] [AGENT] P0. Monitor + rescan + audit. Verify detached chain orchestrator completes; manifest reflects.
- [ ] [AGENT] P0. Query deployment-api data-status: SPORTS attempted ≥50%, captured ≥45%.
- [ ] [AGENT] P0. Spot-check 3 random dates × 5 entities (INJURIES / FIXTURE_STATS / FIXTURE_LINEUPS / PLAYER_STATS /
      ODDS).
- [ ] [AGENT] P0. Re-smoke after writer fix `f36651c` lands on forward-poll VM.
- [ ] [AGENT] P0. Apply per-league empty-loop pattern (Bug 6 fix) to AF enrichment.
- [ ] [HUMAN] P1. Phase 5 UI verification — clear deployment-api turbo cache + open SPORTS data-status.
- [ ] [HUMAN] P1. After verification, delete manifest backup blobs (`*.bak.parquet`).

### Phantom recon + failure triage (`sports_phantom_recon_and_failure_triage`)

- [ ] [HUMAN] P0. **SFI_STANDINGS 100% failed** (42/42 rows phantom 2026-04-29). All have empty error_reason — diagnose
      adapter or upstream data.
- [ ] [HUMAN] P0. **open-meteo silent 2 days** (last `written_at` 2026-04-29 13:22 UTC). Diagnose forward-poll VM.
- [ ] [HUMAN] P0. **api-football date-range starts 2015-01-01** but UAC declares 2018-01-01. Reconcile UAC
      `SOURCE_COVERAGE_START` vs reality.
- [ ] [HUMAN] P0. **understat date-range starts 2014-01-01** but UAC declares 2015-01-16. Same issue.
- [ ] [HUMAN] P0. Wait for `af-backfill-test-`, `sfi-backfill-` VMs to drain.
- [ ] [HUMAN] P0. Run real recon scoped to footystats first.
- [ ] [HUMAN] P0. deployment-api `_sports_honest_coverage` MR review + merge.

### Sports half of `sports_predictions_e2e` — 288M ODDS_API row migration

- [ ] [SCRIPT] P0. Inventory existing 288M legacy `venue=ODDS_API` rows: probe parquet to confirm columns.
- [ ] [SCRIPT] P0. Migrate rows to canonical sports manifest shape (re-key from `venue=ODDS_API` to canonical
      `(asset_group=sports, source=odds_api, data_type, league_id, day)`).
- [ ] [SCRIPT] P0. Run MDPS `SportsBucketAssignmentAdapter` on migrated rows for 1 recent week (smoke pass) — all 8
      horizons (T-24h / T-12h / T-6h / T-4h / T-2h / T-1h / T-10m / T-0).
- [ ] [ANALYSIS] P0. Bucket-coverage check: how many fixtures have ≥1 row per (fixture, bookmaker, bucket).
- [ ] [SCRIPT] P0. Backfill MDPS bucketing across full historical window (5+ years) on migrated rows.
- [ ] [SCRIPT] P1. Run features-sports-service (FSS) on bucketed dataset — verify odds features populate (velocity, CLV,
      steam, late-money).
- [ ] [SCRIPT] P1. Verify feature matrix is ML-ready (one row per fixture × bucket, NaN only where honest-absence).
- [ ] [GATE] P0. Block predictions Group E until FSS produces ≥95% non-NULL features for trained universe at the buckets
      predictions ML targets.

### Sports MTDS slice (`market_tick_data_to_100pct` — sports)

- [ ] [AGENT] P1. Per-source completion %: api_football, footystats, transfermarkt, sfi, understat, open_meteo,
      odds_api. Surface to deployment-ui.
- [ ] [AGENT] P1. Apply UAC `SOURCE_COVERAGE_START` clipping in data-status denominators.
- [ ] [AGENT] P1. Apply UAC `KNOWN_COVERAGE_GAPS` for documented date-range provider outages.

## Anti-patterns + workspace-rule cross-references

- **Sports GCS path SSOT** (CLAUDE.md): use `unified_api_contracts.sports.candidate_parquet_paths` — NEVER hardcode
  `sports_reference/by_date/day=*/entity=*/...` paths.
- **Sports source coverage windows** (CLAUDE.md): `SOURCE_COVERAGE_START` + per-(source,data_type) overrides in
  `DATA_TYPE_COVERAGE_START`. Apply via `clip_dates_to_source_coverage`.
- **Honest absence**: paused leagues + pre-launch dates → `record_empty(empty_confirmed)`.
- **`available_at` per-row stamping rules**: kickoff−60min for lineups; event_time for fixture_events; match_end_time
  for post-match (sfi_progressive / understat / fixture_stats); kickoff−72h for early refs (per orchestrator paths).

## Cross-references

- Master plan: [`master_to_live_defi_2026_05_23.plan.md`](./master_to_live_defi_2026_05_23.plan.md).
- Sibling asset_group umbrellas: `cefi_master_2026_05_07`, `defi_master_2026_05_07`, `tradfi_master_2026_05_07`,
  `predictions_master_2026_05_07`.
- Sports rename plan (KEPT ACTIVE — its own DAG):
  [`sports_data_available_at_rename_2026_05_07.plan.md`](./sports_data_available_at_rename_2026_05_07.plan.md).
- Sports phantom-fixtures-recovery handover: `plans/ai/_sports_phantom_fixtures_recovery_handover_2026_05_06.md`.

## Folded plans (archived 2026-05-07)

- `features_sports_honest_coverage_2026_05_05.plan.md` — full architecture spec; P1+ todos lifted above.
- `sports_fixtures_truthset_recovery_2026_05_06.plan.md` — operator-triggered chain runner + audit.
- `sports_phantom_recon_and_failure_triage_2026_05_01.plan.md` — operator decisions per source.
- `sports_predictions_e2e_2026_05_05.plan.md` (sports half) — predictions ML training half went to `predictions_master`.
- `market_tick_data_to_100pct_2026_05_05.plan.md` (sports slice) — full plan archived after split per asset_group.

## Folded into this umbrella (archived 2026-05-07)

- `sports_data_available_at_rename_2026_05_07.plan.md` — full 4-phase DAG lifted into the "Sports `data_available_at` →
  `available_at` rename" section above. Phase 1 SHIPPED; Phases 2-4 pending.
