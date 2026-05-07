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

## Audit 2026-05-07

- **Audit run**: 2026-05-07 (parallel-agent pass)
- **Verified**: ~70 of 70 unchecked todos
- **Mis-marked DONE → flipped**: 0 (existing checked items intact and accurate per commit refs)
- **In-flight (running VMs)**: 4 VMs in current gcloud snapshot — `af-backfill-20260507-033214` (T+0h, just started;
  api_football all 4 entities), `sfi-backfill-20260507-010938` (T+5h; SFI_PROGRESSIVE_STATS),
  `us-backfill-20260507-010653` (T+5h; understat XG), and `vm-zombie-watchdog-20260506-175221` (T+22h; ongoing
  watchdog). Note: `fs-backfill` and `weather-backfill` named in plan are NOT in current snapshot — either completed
  already, were renamed, or named differently. ETA for active 3: 4-12h depending on date range, so 2026-05-07 to
  2026-05-08
- **Blocked by**: `manifest_migration_master_2026_05_07:Stage 1` (sports `data_available_at` rename Phase 2 =
  operator-triggered GCE migration); `writegate_honest_coverage_endtoend:Phase 2.C` (`_ensure_timestamp` shim deletion
  intersects rename Phase 3)
- **Blocks**: `master_to_live_defi_2026_05_23:G` (DART manual-trade gate); `predictions_master:ML half` (gated on sports
  half completion of `sports_predictions_e2e`)
- **Last meaningful commit**: instruments-service@`8050477` (A1 Phase 1 sports data_available_at→available_at migration
  script + 11 unit tests); instruments-service@`070f7e7` (api_football throttle bumped to full Mega tier 15 req/sec);
  instruments-service@`cf20016` (promote recovery_fixture_ids to redo_all bypassing pre-flight skip);
  instruments-service@`9f0e3f9` (dedup_phantom_after_recovery.py shipped); features-sports@`a215e36` (Path-A post-fetch
  record_empty with reason=SOURCE_RETURNED_ZERO); features-sports@`f123069` (features_sports_reconcile_available_at.py —
  Phase 3.B legacy gap detector); deployment-service@`7453741`/`3a95ae7` (`--recovery-fixture-ids` plumbed through 4
  sports launchers + AF launcher + chain runner); UAC@`fb02104` (event_time field on CanonicalFixtureEvent — Phase 2.D)
- **Recommendation**: KEEP ACTIVE. Heavy P0/P1 surface area + cross-plan coordination required
  (rename→writegate→fixture-recovery dedup chain). Some "ai/" plan refs (e.g.
  `api_football_minimal_flattening_removal_2026_05_07.plan.md` for B.1) need verification — those are still in
  `plans/ai/`. After 4 recovery VMs drain (ETA 2026-05-08), the post-recovery dedup script
  (`dedup_phantom_after_recovery.py`) is the critical-path next move. Do NOT flip B.1/C.2/C.4/C.6 to DONE — those are
  real shipped-code-pending plans.

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
      `openmeteo-fwd-*`). [AUDIT 2026-05-07: BLOCKED-ON manifest_migration_master_2026_05_07:Stage 1 sequencing — Phase
      2 starts after current 4 recovery VMs drain (2026-05-08)]
- [ ] [OPERATOR] P0. Pause sports backfill VMs (`af-backfill-*`, `fs-backfill-*`, etc.). [AUDIT 2026-05-07: BLOCKED-ON
      manifest_migration_master_2026_05_07:Stage 1 — coordinate with current `af-backfill`/`sfi-backfill`/`us-backfill`
      recovery VMs]
- [ ] [OPERATOR] P0. Launch migration VM in `asia-northeast1-c` per CLAUDE.md "same-region GCE VM" rule. VM name
      `sports-migrate-available-at-{ts}` (add prefix to `vm_zombie_watchdog.py` `VM_PREFIX_TO_BUCKET` first). Run
      `--dry-run` first; review; then full run. [AUDIT 2026-05-07: FRESH — actionable post recovery-VM-drain]
- [ ] [OPERATOR] P0. Verify completion: spot-check ~20 parquets across years 2018-2026 — `pq.read_schema(uri).names`
      includes `available_at` and not `data_available_at`. [AUDIT 2026-05-07: BLOCKED-ON sports_master:Phase 2 migration
      VM run]
- [ ] [OPERATOR] P0. DO NOT resume FWD/BACKFILL VMs until Phase 3 atomic source rename ships. [AUDIT 2026-05-07:
      BLOCKED-ON sports_master:Phase 3]

#### Phase 3 — Atomic 4-repo source rename (PENDING — sequenced after Phase 2)

- [ ] [SCRIPT] P0. UAC: rename in 4 schema files (1 commit, push to `live-defi-rollout`). [AUDIT 2026-05-07: BLOCKED-ON
      sports_master:Phase 2 migration VM completion]
- [ ] [SCRIPT] P0. UTL: rename `DEFAULT_AS_OF_COLUMNS` + `point_in_time.py` comment + tests (1 commit, push). [AUDIT
      2026-05-07: BLOCKED-ON sports_master:Phase 2]
- [ ] [SCRIPT] P0. instruments-service: rename 13 orchestrator callsites + 2 scripts + tests (1 commit, push). [AUDIT
      2026-05-07: BLOCKED-ON sports_master:Phase 2]
- [ ] [SCRIPT] P0. features-sports-service: rename `batch_handler.py` reference. **Coordinate with writegate Phase 2.C**
      `_ensure_timestamp` deletion if 2.C is mid-flight (fold into 2.C's batch_handler work instead of separate commit).
      [AUDIT 2026-05-07: BLOCKED-ON sports_master:Phase 2 + writegate_honest_coverage_endtoend:Phase 2.C coordination]
- [ ] [QG] P0. Run `quality-gates.sh` on all 4 repos sequentially before each push. [AUDIT 2026-05-07: BLOCKED-ON
      sports_master:Phase 3 commits]
- [ ] [QG] P0. Workspace-wide ripgrep for stragglers — `rg -n 'data_available_at' --type py --glob '!.venv*'` returns
      ZERO non-test, non-archived results. [AUDIT 2026-05-07: BLOCKED-ON sports_master:Phase 3 commits]
- [ ] [SKIP] `tests/unit/test_availability_stamping.py` in UTL — DIRTY with another agent's WIP, do NOT touch in Phase 3
      ship; coordinate with owner before final ship. [AUDIT 2026-05-07: BLOCKED-ON UTL teammate coordination per
      CLAUDE.md "Two teammates" rule]

#### Phase 4 — Writegate Phase 2.C unblock + verify (PENDING)

- [ ] [SCRIPT] P0. Smoke-run sports backfill; confirm `record_captured` no longer raises `LookaheadBiasError`. [AUDIT
      2026-05-07: BLOCKED-ON sports_master:Phase 3]
- [ ] [VERIFY] P0. Update writegate plan Phase 2.C "prerequisites" section to mark sports rename as shipped. [AUDIT
      2026-05-07: BLOCKED-ON sports_master:Phase 3]
- [ ] [VERIFY] P0. Update master plan Q&A 14 to mark HIGH-2 as SHIPPED + record commit SHAs. [AUDIT 2026-05-07:
      BLOCKED-ON sports_master:Phase 3]
- [ ] [OPERATOR] P0. Resume forward-poll + backfill VMs. [AUDIT 2026-05-07: BLOCKED-ON sports_master:Phase 4]

### Sports honest-coverage architecture (`features_sports_honest_coverage`)

- [x] [AGENT] P1. UAC `unified_api_contracts.sports`: add `UpstreamReq` dataclass + `FEATURE_UPSTREAM_REQUIREMENTS`
      dict + `in_coverage(source, entity, league, date) -> bool` helper. [AUDIT 2026-05-07: DONE — UAC@3137271
      (UpstreamReq + FEATURE_UPSTREAM_REQUIREMENTS + in_coverage Phase 1)]
- [ ] [AGENT] P1. Unit tests for `in_coverage` — coverage of each clip rule; pre-launch dates + paused leagues. [AUDIT
      2026-05-07: FRESH — actionable; UAC@3137271 commit message says Phase 1 implies tests; verify test file exists]
- [ ] [AGENT] P2. features-sports-service: feature compute path calls `in_coverage` per upstream before
      fetching/joining. [AUDIT 2026-05-07: FRESH — actionable]
- [ ] [AGENT] P2. NaN handling — distinguish NaN-by-design (write parquet, manifest `captured`) from
      NaN-from-missing-upstream (manifest `empty_confirmed` no parquet) per
      `codex/02-data/honest-absence-downstream-handling.md`. [AUDIT 2026-05-07: FRESH — actionable; codex doc shipped
      per MEMORY entry project_master_plan_audit_continuation_2026_05_07 (A3 ship)]
- [ ] [AGENT] P2. Backwards-compat — features computed before this change have manifest rows without coverage info;
      one-time migration or tolerate via reader-side fallback (per honest-absence doc). [AUDIT 2026-05-07: FRESH —
      actionable; UTL `classify_legacy_empty_row` helper landed via Tier 3D.2 per MEMORY
      (handoff_writegate_tier3d2_2026_05_07_late4)]
- [ ] [AGENT] P3. Add `axis: per_feature_per_league_per_fixture_date` to `_sports_honest_coverage` in data-status
      reconciler. Per-feature-group denominator = (clipped fixture dates) × (in-coverage leagues). [AUDIT 2026-05-07:
      FRESH — actionable]

### Fixture truthset recovery (`sports_fixtures_truthset_recovery`)

- [x] [HUMAN] P0. Operator triggers Phase 3 chain runner per the recovery script.
- [x] [AGENT] P0. Monitor + rescan + audit. Verify detached chain orchestrator completes; manifest reflects.
- [x] [AGENT] P0. Architecture: `--recovery-fixture-ids` CLI flag (instruments-service `cbb50fa` / `e900769` /
      `7ce509e`), 4 non-api_football launchers plumbed (deployment-service `7453741`), throttle 0.1s → 0.067s for full
      Mega tier (instruments-service `070f7e7`), UTL cache split (`bf41175c`).
- [ ] [AGENT] P0. Monitor 5 parallel recovery VMs to STOPPED: `af-backfill-20260507-033214` (api_football all 4
      entities), `us-backfill-20260507-010653` (understat XG), `fs-backfill-20260507-010724` (footystats MATCHES +
      PREDICTIONS + ODDS), `weather-backfill-20260507-010923` (open_meteo WEATHER), `sfi-backfill-20260507-010938`
      (SFI_PROGRESSIVE_STATS). Verify auto-shutdown on completion (`VM_SHUTDOWN_ON_COMPLETION=true`). Allowlist parquet:
      `gs://instruments-store-sports-central-element-323112/_audits/fixtures_recovery_allowlist_20260506-153914.parquet`
      (112,192 af_fixture_ids). [AUDIT 2026-05-07: IN-FLIGHT — 3 of 5 named VMs RUNNING in current snapshot (af/sfi/us);
      fs-backfill-20260507-010724 + weather-backfill-20260507-010923 NOT in current `gcloud running` listing — likely
      already drained or auto-shutdown fired. Verify via STOPPED event log or recreate if missing. ETA for active 3:
      2026-05-07 to 2026-05-08]
- [ ] [OPERATOR] **P0. POST-RECOVERY PHANTOM DEDUP — REQUIRED.** Once ALL 5 recovery VMs above are STOPPED (or DELETED
      via `VM_SHUTDOWN_ON_COMPLETION`), run the dedup script on a same-region VM (or laptop, GCS-only):

      ```
      cd instruments-service
      python scripts/dedup_phantom_after_recovery.py --dry-run   # report counts
      python scripts/dedup_phantom_after_recovery.py --apply     # commit
      ```

      **Why this exists**: recovery writes new `captured` rows with `venue=API_FOOTBALL` (api_football) while phantom
      `empty_confirmed` rows carry `venue=""`. Different `venue` axis → `_merge_shard_frames` keeps BOTH rows in
      canonical → data-status dashboard double-counts (sees same `(date, league_id, data_type)` cell as both
      "captured" AND "empty_confirmed"). The script walks every shard (canonical + per-VM), identifies cells with
      a captured-w/data row anywhere, and drops other rows in those cells.

      **Pre-flight check**: VMs must be DONE before running, else we race the recovery writes:
      ```
      gcloud compute instances list \
        --filter='(name~"^af-backfill-" OR name~"^us-backfill-" OR name~"^fs-backfill-" \
                  OR name~"^weather-backfill-" OR name~"^sfi-backfill-") AND status=RUNNING' \
        --zones=asia-northeast1-c
      ```
      Must return EMPTY.

      **What the script does** (all sport per-fixture entities — handles api_football + footystats + understat +
      sfi + open_meteo in one pass):
        Targets: FIXTURES / FIXTURE_STATS / FIXTURE_EVENTS / FIXTURE_LINEUPS / PLAYER_STATS / INJURIES /
                 XG / MATCHES / ODDS / PREDICTIONS / SFI_PROGRESSIVE_STATS / WEATHER
        Logic: for any cell with a captured-w/data row, drop empty_confirmed / attempted_failed / captured-zero rows.
        Backups: `_index/availability_index.{run_ts}.dedup_phantom.bak.parquet` per shard (canonical + per-VM).

- [ ] [AGENT] P0. Query deployment-api data-status: SPORTS attempted ≥50%, captured ≥45%, **% empty drops** as phantoms
      get dedup'd. [AUDIT 2026-05-07: BLOCKED-ON sports_master:recovery VM drain + post-recovery dedup script run]
- [ ] [AGENT] P0. Spot-check 3 random dates × 5 entities (INJURIES / FIXTURE_STATS / FIXTURE_LINEUPS / PLAYER_STATS /
      ODDS). [AUDIT 2026-05-07: BLOCKED-ON sports_master:recovery VM drain]
- [ ] [AGENT] P0. Re-smoke after writer fix `f36651c` lands on forward-poll VM. [AUDIT 2026-05-07: FRESH — actionable]
- [ ] [AGENT] P0. Apply per-league empty-loop pattern (Bug 6 fix) to AF enrichment. [AUDIT 2026-05-07: FRESH —
      actionable]
- [ ] [HUMAN] P1. Phase 5 UI verification — clear deployment-api turbo cache + open SPORTS data-status. Verify `% empty`
      figure has dropped from the ~70% baseline observed pre-recovery. [AUDIT 2026-05-07: BLOCKED-ON
      sports_master:recovery VM drain + dedup]
- [ ] [HUMAN] P1. After verification, delete manifest backup blobs (`*.bak.parquet`, `*.dedup_phantom.bak.parquet`).
      [AUDIT 2026-05-07: BLOCKED-ON sports_master:Phase 5 UI verification]

### Phantom recon + failure triage (`sports_phantom_recon_and_failure_triage`)

- [ ] [HUMAN] P0. **SFI_STANDINGS 100% failed** (42/42 rows phantom 2026-04-29). All have empty error_reason — diagnose
      adapter or upstream data. [AUDIT 2026-05-07: FRESH — actionable; sfi-backfill-20260507-010938 VM RUNNING may be
      addressing this]
- [ ] [HUMAN] P0. **open-meteo silent 2 days** (last `written_at` 2026-04-29 13:22 UTC). Diagnose forward-poll VM.
      [AUDIT 2026-05-07: FRESH — actionable]
- [ ] [HUMAN] P0. **api-football date-range starts 2015-01-01** but UAC declares 2018-01-01. Reconcile UAC
      `SOURCE_COVERAGE_START` vs reality. [AUDIT 2026-05-07: FRESH — actionable; per CLAUDE.md
      `DATA_TYPE_COVERAGE_START` per-(source, data_type) override pattern is the canonical fix shape]
- [ ] [HUMAN] P0. **understat date-range starts 2014-01-01** but UAC declares 2015-01-16. Same issue. [AUDIT 2026-05-07:
      FRESH — actionable]
- [ ] [HUMAN] P0. Wait for `af-backfill-test-`, `sfi-backfill-` VMs to drain. [AUDIT 2026-05-07: IN-FLIGHT —
      sfi-backfill-20260507-010938 RUNNING (T+5h); af-backfill-test- not in current snapshot]
- [ ] [HUMAN] P0. Run real recon scoped to footystats first. [AUDIT 2026-05-07: FRESH — actionable]
- [ ] [HUMAN] P0. deployment-api `_sports_honest_coverage` MR review + merge. [AUDIT 2026-05-07: FRESH — actionable]

### Sports half of `sports_predictions_e2e` — 288M ODDS_API row migration

- [ ] [SCRIPT] P0. Inventory existing 288M legacy `venue=ODDS_API` rows: probe parquet to confirm columns. [AUDIT
      2026-05-07: FRESH — actionable]
- [ ] [SCRIPT] P0. Migrate rows to canonical sports manifest shape (re-key from `venue=ODDS_API` to canonical
      `(asset_group=sports, source=odds_api, data_type, league_id, day)`). [AUDIT 2026-05-07: FRESH — actionable;
      coordinate with manifest_migration_master_2026_05_07:Stage 3]
- [ ] [SCRIPT] P0. Run MDPS `SportsBucketAssignmentAdapter` on migrated rows for 1 recent week (smoke pass) — all 8
      horizons (T-24h / T-12h / T-6h / T-4h / T-2h / T-1h / T-10m / T-0). [AUDIT 2026-05-07: BLOCKED-ON
      sports_master:288M migration above]
- [ ] [ANALYSIS] P0. Bucket-coverage check: how many fixtures have ≥1 row per (fixture, bookmaker, bucket). [AUDIT
      2026-05-07: BLOCKED-ON sports_master:bucket smoke run]
- [ ] [SCRIPT] P0. Backfill MDPS bucketing across full historical window (5+ years) on migrated rows. [AUDIT 2026-05-07:
      BLOCKED-ON sports_master:bucket smoke verified]
- [ ] [SCRIPT] P1. Run features-sports-service (FSS) on bucketed dataset — verify odds features populate (velocity, CLV,
      steam, late-money). [AUDIT 2026-05-07: BLOCKED-ON sports_master:full bucket backfill]
- [ ] [SCRIPT] P1. Verify feature matrix is ML-ready (one row per fixture × bucket, NaN only where honest-absence).
      [AUDIT 2026-05-07: BLOCKED-ON sports_master:FSS run]
- [ ] [GATE] P0. Block predictions Group E until FSS produces ≥95% non-NULL features for trained universe at the buckets
      predictions ML targets. [AUDIT 2026-05-07: ACTIVE GATE — explicitly BLOCKS predictions_master:ML half]

### Sports MTDS slice (`market_tick_data_to_100pct` — sports)

- [ ] [AGENT] P1. Per-source completion %: api_football, footystats, transfermarkt, sfi, understat, open_meteo,
      odds_api. Surface to deployment-ui. [AUDIT 2026-05-07: BLOCKED-ON sports_master:recovery VM drain]
- [ ] [AGENT] P1. Apply UAC `SOURCE_COVERAGE_START` clipping in data-status denominators. [AUDIT 2026-05-07: FRESH —
      actionable; deployment-api wiring needed (per MEMORY entry, deployment-api has B.3 per-chain clipping wired
      analogously)]
- [ ] [AGENT] P1. Apply UAC `KNOWN_COVERAGE_GAPS` for documented date-range provider outages. [AUDIT 2026-05-07: FRESH —
      actionable]

### Audit findings 2026-05-07 — folded from session wrapper

**Source**: `plans/ai/session_2026_05_07_data_status_audit_findings.plan.md` rows B.1 / C.2 / C.3 / C.4 / C.6 / C.7 /
C.10. Operator inspected the deployment-ui data-status panel + schema modals; the findings below all surfaced as
sports-asset_group writer / contract / cadence issues.

#### Bonus — FootyStats per-season league-id drift-detection automation (filed 2026-05-07)

Operator question 2026-05-07: "what in code actually triggers that change [`FOOTYSTATS_SEASON_IDS` refresh]. if its in
the code how do we ship it automatically". Investigation found NO existing automation:

- `unified-api-contracts/.github/workflows/weekly-validation.yml` runs API schema validation but does NOT touch
  `FOOTYSTATS_SEASON_IDS`.
- No tests in `unified-api-contracts/tests/` reference `FOOTYSTATS_SEASON_IDS`.
- No script in instruments-service refreshes the dict.

The "Refresh by calling FootyStats `/league-list` at season start" comment at
`unified-api-contracts/unified_api_contracts/canonical/domain/sports/provider_league_ids.py:103` is a manual reminder.
Real gap. Without automation, the dict drifts every August (European football season start) and downstream backfills
silently fail to discover newly-listed leagues for the new season until someone notices the data-status panel showing no
FIXTURES for those leagues.

- [ ] [SCRIPT] P1. **FOOTYSTATS_SEASON_IDS drift-detection automation.** Extend
      `unified-api-contracts/.github/workflows/weekly-validation.yml` (or a sibling cron workflow) with a job that:
  - [ ] Calls FootyStats `/league-list` once per week
  - [ ] Diffs the response's per-league season IDs against UAC's hardcoded `FOOTYSTATS_SEASON_IDS` dict
  - [ ] If new league IDs detected (typically per-season at August / January for European / Brazilian seasons): opens a
        PR with the dict update + appends new IDs to `FOOTYSTATS_HISTORICAL_SEASON_IDS` (append-only as seasons accrue).
        PR title format `chore(provider-league-ids): footystats season refresh — {YYYY-MM-DD}`.
  - [ ] Same shape for `TRANSFERMARKT_IDS` if Transfermarkt has analogous per-season drift (verify via spot-check live
        API call).
  - [ ] ~50-line Python helper in `unified-api-contracts/scripts/check_footystats_season_drift.py` driven by the GHA
        cron. Calls `client.get_league_list()`, compares to `FOOTYSTATS_SEASON_IDS`, emits drift report + PR-creation
        step.
  - [ ] Test: mock the API response with a new fake league ID, assert the script flags it. Locked in
        `tests/test_footystats_season_drift.py`.

  **Why P1 (not P0)**: today's workflow has the operator manually refresh dicts at season start; this is a
  reliability+ergonomics improvement, not a correctness fix. The dicts are correct as long as the operator remembers. P0
  priority would be appropriate if we had a recent miss (probably the case but not yet documented as a specific
  incident).

#### B.1 — API-Football payload flattening (FIXTURE_STATS / FIXTURE_EVENTS / FIXTURE_LINEUPS / INJURIES)

Plan in `plans/ai/api_football_minimal_flattening_removal_2026_05_07.plan.md` (5 phases). Owner-side todo:

- [ ] [SCRIPT] P0. UAC `unified_api_contracts/external/api_football/normalize.py:372-395` — replace 4 stub-pass-through
      normalizers (`normalize_fixture_stats`, `normalize_fixture_event`, `normalize_lineup`, `normalize_injury`) with
      real flatteners that unpack the nested `statistics: [...]` / `events: [...]` /
      `startXI: [...] + substitutes: [...]` / `players: [...]` arrays into per-row records. [AUDIT 2026-05-07: FRESH —
      actionable; UAC@fb02104 added event_time field on CanonicalFixtureEvent (Phase 2.D) which is pre-req prep]
- [ ] [SCRIPT] P0. UAC contract update for the 4 data_types — declare the actual flattened columns (per-stat, per-event,
      per-lineup-slot, per-injured-player), `cadence: "per_fixture"`. [AUDIT 2026-05-07: FRESH — actionable]
- [ ] [SCRIPT] P0. instruments-service AF batch_handler: switch from raw-passthrough to the flattening writer. [AUDIT
      2026-05-07: FRESH — actionable]
- [ ] [SCRIPT] P0. Migration shape: flip every existing manifest row for the 4 data_types →
      `record_failed(reason=INCOMPLETE_PAYLOAD_PRE_FLATTENING, attempted_at=now)`, delete the thin parquets, then
      re-fetch via a dedicated VM (`af-backfill-flatten-{ts}`). The 4 data_types use ISOLATED endpoints
      (`/fixtures/statistics`, `/fixtures/events`, `/fixtures/lineups`, `/injuries`) — separate from `/fixtures` itself
      — so quota cost is bounded to the 4-endpoint × historical-fixture-set product, NOT a full FIXTURES re-fetch.
      [AUDIT 2026-05-07: FRESH — actionable; coordinate with manifest_migration_master_2026_05_07:Stage 3]
- [ ] [TEST] P0. Cassette parity test (`unified-api-contracts/tests/test_cassette_schema_parity.py` extension):
      flattened normalizer output matches the per-row UAC schema for each of the 4 data_types. [AUDIT 2026-05-07: FRESH
      — actionable]
- [ ] [VERIFY] P0. After re-fetch VM completes for one league × one season, open deployment-ui schema modal for each of
      the 4 data_types and confirm full per-row column set (xG, shots-on-target, possession, goal-events with minute,
      starting-XI per slot, etc.). [AUDIT 2026-05-07: BLOCKED-ON above flatten ship + re-fetch VM]

#### C.2 — ODDS in instruments-service: provenance audit + canonical-home decision

The `data_type=odds` row appears under instruments-service in deployment-ui. Three plausible writers: odds_api (which
should live in MTDS, not instruments-service), `footystats_odds` (separate UAC normalizer per SSOT), api_football's
`/odds` endpoint. UAC has no contract for `(asset_group=sports, source=∅, data_type=odds)`.

- [x] [AGENT] P0. Traced the writer for `data_type=ODDS` in instruments-service:
      `instruments-service/instruments_service/engine/orchestrator.py:4760-4900`. Source = footystats
      `get_fixture_odds_snapshot()`
      (instruments-service/instruments_service/reference_data/adapters/sports/adapters/footystats.py:270). The
      footystats adapter's `get_odds()` is a deprecated stub that logs "use get_fixture_odds_snapshot() instead" — no
      api_football odds path. Pre-match snapshot, 68 markets, `data_available_at = kickoff - 72h`. Path:
      `gs://instruments-store-sports-{pid}/sports_reference/by_date/day=*/entity=footystats_odds/league={L}/footystats_odds.parquet`.
- [x] [AGENT] P0. Decided canonical home: **instruments-service ODDS = pre-match refdata-style snapshot, KEEP**.
      Reasoning: it's not "market-typed odds" (not intra-day-ticking) — it's a one-shot opening snapshot per (league,
      date) used by features-sports for backtest training. The intra-day movement counterpart is MTDS `odds_api` which
      writes 8 horizon buckets (T-24h/T-12h/T-6h/T-4h/T-2h/T-1h/T-10m/T-0) under data_type `odds_horizon_bucket`. The
      two are different-purpose data and SHOULD coexist in their current homes. NO migration; NO merge. The data-status
      panel renders them separately under their respective service nodes.
- [x] [SCRIPT] P0. **No code change required** (verdict = instruments-service-owned refdata; no UAC contract change
      needed beyond the already-existing FootyStats schema declarations). The `cadence` field per C.11 still applies as
      a separate workspace-wide refdata-cadence migration; instruments-service ODDS is per-(league, date) which already
      matches the per-day shard atom — no cadence drift to fix.
- [x] [DOC] P0. Documented the outcome in `codex/02-data/sports-data-source-coverage-matrix.md` § 4 (resolved the "ODDS
      duplication" open question), § 2.2 (clarified `ODDS` here = footystats snapshot only), and § 5 changelog.
      Schema-modal disambiguation under C.3 below.

#### C.3 — PREDICTIONS vs ODDS schema-modal clarity (doc-only)

footystats publishes BOTH `/odds` (market odds) and `/predictions` (model-output predicted probabilities, odds-like).
The two data_types collide visually in the data-status panel without a clear distinction.

- [x] [DOC] P1. **SHIPPED 2026-05-07** (Phase 2 round 3 — doc-only). Updated UAC docstrings on
      `unified_api_contracts/external/footystats/normalize.py`: - `normalize_footystats_odds`: now opens with "What this
      is: real published bookmaker odds…" + cross-references `normalize_footystats_predictions` to call out the
      model-output-vs-market-odds distinction. - `normalize_footystats_predictions`: rewritten as "Extract FootyStats
      PROPRIETARY pre-match forecast fields" with explicit per-field documentation (potentials = likelihood scores, xG
      prematch = expected-goals model, PPG = points-per-game projections); cross-references the odds normalizers + warns
      "NOT to be confused with…". - `normalize_footystats_odds_snapshot`: short docstring pointing at
      `normalize_footystats_odds` for the full bookmaker-odds vs FootyStats-predictions distinction.

      Codex doc updated: `codex/02-data/sports-data-source-coverage-matrix.md` §2.2 — added `PREDICTIONS vs ODDS —
      disambiguation` block under the §2.2 footystats data_types matrix. Calls out the FOUR concrete differences:
      (a) PREDICTIONS = MODEL OUTPUT (FootyStats's algorithm), (b) ODDS = MARKET DATA (real bookmaker quotes),
      (c) downstream consumers must NOT merge them (different statistical properties), (d) strategy-service must NOT
      use PREDICTIONS as input feature for a model targeting ODDS for the same fixture (same-source label leakage).

#### C.4 — Transfermarkt PLAYER_VALUES per-player flatten

Same minimal-flattening pattern as B.1. Current PLAYER_VALUES carries team-level aggregates (`squad_size`,
`player_count`); per-player `market_value_eur` is dropped at write-time.

- [ ] [SCRIPT] P0. UAC `unified_api_contracts/external/transfermarkt/normalize.py` — extend `normalize_player_values` to
      emit per-(team, player, season, fetch_day) rows with `player_id`, `player_name`, `position`, `age`,
      **`market_value_eur`**, `contract_until`, `current_club_id`, `nationality_iso`. [AUDIT 2026-05-07: FRESH —
      actionable]
- [ ] [SCRIPT] P0. UAC contract: bump PLAYER_VALUES schema to per-player shape; old team-aggregate becomes a derived
      view in features-sports OR is dropped if features-sports is happy rolling per-player at compute time. [AUDIT
      2026-05-07: FRESH — actionable]
- [ ] [SCRIPT] P0. Migration shape: same flip-to-failed + delete + re-fetch pattern as B.1; Transfermarkt's
      per-team-per-season endpoint is already isolated, no upstream impact. [AUDIT 2026-05-07: FRESH — actionable]
- [ ] [TEST] P0. Cassette parity test for the new per-player shape. [AUDIT 2026-05-07: FRESH — actionable]

#### C.6 + C.10 — `match_end_time` cascade implementation (groups together)

The cascade is codified in CLAUDE.md (api_football native → SFI freeze → footystats/understat → kickoff+120min
low-confidence fallback) but no writer implements it. Load-bearing for odds-settlement timing + post-match
`available_at` stamping.

- [ ] [SCRIPT] P0. **Step 1**: api_football FIXTURES write-time computation. When `status_short ∈ {FT, AET, PEN}`,
      compute `match_end_time ≈ kickoff + periods.second.duration + et.duration +     injury_time` from the API
      response. Add `match_end_time` column to UAC FIXTURES contract. [AUDIT 2026-05-07: FRESH — actionable]
- [ ] [SCRIPT] P0. **Step 2**: SFI progressive freeze detection. Add `ft_timer` (raw `timer_seconds` from the
      snapshot) + `match_end_time` (detected freeze point — the last snapshot where `timer_seconds` advances) columns to
      UAC `SFI_PROGRESSIVE_STATS` contract. Detect freeze at write-time in
      `instruments-service/instruments_service/sfi/normalize.py` (or wherever the SFI snapshot writer lives). [AUDIT
      2026-05-07: FRESH — actionable]
- [ ] [SCRIPT] P0. **Step 3**: UTL helper
      `unified_trading_library.fixtures.resolve_match_end_time(fixture_id) -> tuple[datetime, str]` walking the cascade
      in priority order: api_football FIXTURES.match_end_time → SFI freeze → footystats/understat post-match timestamp →
      low-confidence `kickoff + 120min` fallback. Returns the timestamp + provenance string. [AUDIT 2026-05-07: FRESH —
      actionable]
- [ ] [SCRIPT] P0. Wire `resolve_match_end_time()` into per-source `available_at` stamping for post-match data_types
      (FIXTURE_STATS / SFI_PROGRESSIVE_STATS / understat XG / fixture_player_stats) per CLAUDE.md "available_at per-row,
      write-time, equal-to-live-pipeline-arrival" rule. [AUDIT 2026-05-07: FRESH — actionable; coordinate with
      sports_master:Phase 3 rename]
- [ ] [TEST] P0. Unit tests covering each branch of the cascade + the `kickoff + 120min` fallback shape. [AUDIT
      2026-05-07: FRESH — actionable]
- [ ] [VERIFY] P0. After ship + smoke, deployment-ui schema modal for FIXTURES / SFI_PROGRESSIVE_STATS / FIXTURE_STATS
      shows `match_end_time` column populated for completed fixtures. [AUDIT 2026-05-07: BLOCKED-ON above C.6 ship]

#### C.7 — Sanity-sweep STANDINGS / WEATHER / XG / MATCHES schema modals

Targeted audit, lower priority than the explicit flattens above. XG (per-shot events from understat) is the most likely
follow-up flatten target; STANDINGS and MATCHES are probably already correct.

- [x] [AGENT] P1. **AUDIT COMPLETE 2026-05-07** (Phase 2 round 4). Code-level audit of UAC normalizers (no deployment-ui
      visit needed — source-payload signal density is in the dataclass schemas). Findings:
  - **WEATHER (open_meteo) — OK.** `normalize_open_meteo_weather_multi`
    (`unified_api_contracts/external/open_meteo/normalize.py:44`) explicitly emits one record per metric (temperature,
    humidity, wind_speed, precipitation). NO flatten miss; close-out item.
  - **STANDINGS (api_football) — STUB-PASS-THROUGH.** `normalize_api_football_standing`
    (`unified_api_contracts/external/api_football/normalize.py:367`): `return {"league_id": ..., "season": ..., **raw}`.
    Same C.8 stub-normalizer pattern as B.1. The api_football `/standings` endpoint returns nested
    `league.standings: [[...]]` array with team/league/all/home/away nested objects; PyArrow flattens inconsistently or
    drops the nested array silently. **Follow-up #1 below.**
  - **XG (understat) — SEVERELY TRUNCATED (BIGGEST MISS).** `normalize_understat_feature_record`
    (`unified_api_contracts/external/understat/normalize.py:261-279`): only captures `value=xg` from each shot, drops
    the full UnderstatShot payload (~15+ fields per shot — minute, player_id, player_name, situation, shot_type, result,
    x/y coordinates, last_action, season, h_team, a_team, h_a, date, h_goals, a_goals). **Follow-up #2 below.**
  - **MATCHES (footystats) — PARTIAL FIELD-MAPPING.** `normalize_footystats_match`
    (`unified_api_contracts/external/footystats/normalize.py:26-114`): populates ~25 CanonicalFixture fields but
    hardcodes 15+ to `None` (referee, halftime goals, shots*on_target, fouls, yellow/red cards, shots_blocked, offsides,
    passes_total/accuracy) **despite the FootyStatsMatch source dataclass carrying**
    `team_a*_`/    `team*b*_`for shots_on_target / yellow_cards / red_cards / fouls (verified via`rg` on schemas.py).     Source-to-canonical name-mapping miss (`team_a`→`home`, `team_b`→`away`).
    Smaller scope than full flatten; just rewire the field assignments. **Follow-up #3 below.**
- [ ] [SCRIPT] P1. **Follow-up #1 — STANDINGS flatten.** UAC `normalize_api_football_standing` rewrite to unpack the
      nested `league.standings: [[...]]` array into per-(league, team, season, position) row records with full stats
      subobjects (all/home/away each have played/win/draw/lose/goals/goalsAgainst/goalDifference/points). Same migration
      shape as B.1: flip manifest STANDINGS rows → `attempted_failed reason=INCOMPLETE_PAYLOAD_PRE_FLATTENING` + delete
      thin parquets + re-fetch via dedicated VM (`af-backfill-standings-{ts}` if isolated, or fold into
      af-backfill-flatten-{ts} from B.1). Cassette parity test extension to lock the flat shape.
- [ ] [SCRIPT] P1. **Follow-up #2 — XG per-shot flatten (BIG WIN).** UAC `normalize_understat_feature_record` is
      currently ONE feature value per shot. Replace with `normalize_understat_shot` returning a flat dict with all ~15
      fields: `xg`, `xa`, `minute`, `player_id`, `player_name`, `situation` (open_play / set_piece / penalty),
      `shot_type` (header / left_foot / right_foot / other), `result` (goal / saved / missed / blocked / post), `x`,
      `y`, `last_action`, `home_or_away` (h / a), `assist_player_id`, `season`, `match_id`. Lift `feature_name=shot_xg`
      callers to read from the `xg` column instead. Same B.1 migration shape (flip + delete + re-fetch via dedicated
      `us-backfill-shots-flatten-{ts}` VM + cassette parity). features-sports consumers updated to read per-shot
      dimensions; XG features become much richer (position-on-pitch, shot-quality decomposition, set-piece vs open-play
      splits).
- [ ] [SCRIPT] P1. **Follow-up #3 — MATCHES field-mapping fix.** Smaller-scope fix to `normalize_footystats_match`:
      replace 15+ hardcoded `None` with proper `team_a_*` / `team_b_*` → `home_*` / `away_*` mappings from the
      FootyStatsMatch source dataclass. Add `referee` mapping if FootyStats provides it on the match endpoint (verify
      via raw-payload sample). Migration: if downstream consumers tolerate NaN, no flip needed (just landing the new
      normalizer + re-fetching going forward writes populated columns from now on; historical rows stay None-populated
      and are NaN-tolerant); if any consumer explicitly checks column existence via `.dropna(subset=...)`, then full
      B.1-shape migration (flip + delete + re-fetch) is required. Cassette parity test catches the wire-up regression.

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
