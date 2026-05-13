---
name: sports-master
slug: sports_master_2026_05_07
date: 2026-05-07
deadline: 2026-05-23
last_updated: 2026-05-08
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

> **🟡 STAMPING SCOPE FOLDED INTO UMBRELLA — `available_at_lookahead_bias_completion_2026_05_08`** (codified 2026-05-08)
>
> **Phase 1-2 stamping refs ONLY** (sports adapter `available_at` per-source cascade: lineups / fixture_events /
> injuries / pre-match odds / post-match xG+stats / weather forecast-issue) are folded into the available_at umbrella.
> Other sports_master scope (backfills, source coverage, league enumeration) remains owned here.
>
> Stamping owner:
> [`plans/active/available_at_lookahead_bias_completion_2026_05_08.md`](../active/available_at_lookahead_bias_completion_2026_05_08.md)

# Sports Master — asset_group umbrella

## Codex SSOTs

This plan implements / extends the following codex documents (read these BEFORE making code changes; drift between code
and these docs is a review-blocking failure per `doc → plan → code`):

- [`codex/02-data/availability-manifest-and-data-status.md`](../../codex/02-data/availability-manifest-and-data-status.md)
  — manifest v5 schema + sports per-fixture-bundle cluster validation (`ODDS_SNAPSHOT` / `ODDS_MOVEMENT` / `ARBITRAGE`
  per-league-tier expected bookmaker sets); per-(source, data_type, league_id, day) shard atom
- [`codex/02-data/honest-absence-downstream-handling.md`](../../codex/02-data/honest-absence-downstream-handling.md) —
  sports-specific empty_confirmed legitimacy: instrument-day-grain empty IS legit (no fixtures today / no markets active
  is normal); paused-league windows (`KNOWN_COVERAGE_GAPS`) + pre-`SOURCE_COVERAGE_START` clip rules
- [`codex/02-data/per-asset-group-bucket-layouts.md`](../../codex/02-data/per-asset-group-bucket-layouts.md) — sports
  per-source folder layout per CLAUDE.md "Sports GCS path SSOT":
  `sports_reference/by_date/day=*/entity={F}/league={L}/{F}.parquet`;
  `candidate_parquet_paths(data_type, day, league_id)` is the canonical probe API
- [`codex/04-architecture/batch-live-architecture.md`](../../codex/04-architecture/batch-live-architecture.md) —
  batch=live unified pipeline: same shard atom, same fields, same `available_at` semantics; sports lineups stamped at
  `kickoff − 60min`, fixture_stats / understat at `match_end_time`, weather at forecast-issue-time
- [`codex/09-strategy/architecture-v2/archetypes/ml-directional-event-settled.md`](../../codex/09-strategy/architecture-v2/archetypes/ml-directional-event-settled.md)
  — ML-directional event-settled archetype (sports prediction)
- [`codex/09-strategy/architecture-v2/archetypes/market-making-event-settled.md`](../../codex/09-strategy/architecture-v2/archetypes/market-making-event-settled.md)
  — Market-making event-settled archetype
- [`codex/09-strategy/architecture-v2/archetypes/rules-directional-event-settled.md`](../../codex/09-strategy/architecture-v2/archetypes/rules-directional-event-settled.md)
  — Rules-directional event-settled archetype
- [`codex/09-strategy/architecture-v2/archetypes/event-driven.md`](../../codex/09-strategy/architecture-v2/archetypes/event-driven.md)
  — Event-driven archetype foundation (cross-cutting; sports + predictions)

If any of the docs above is missing, this plan creates a stub for it (see [`codex/`](../../codex/) tree).

## AI-day estimate

- **Total**: ~10-12 ai-days net (XL umbrella; 112 todos enumerated, ~13% in-flight per 2026-05-07 audit).
- **Workstream split**:
  - Sports `data_available_at` → `available_at` rename Phases 2-4 + GCS migration: ~2 ai-days (Phase 1 shipped per
    instruments-service@8050477; Phase 2 = operator-triggered GCE migration of millions of parquets)
  - Sports honest-coverage Phases 1-2 + features-sports reconciler shipping: ~2 ai-days (legacy gap detector shipped per
    features-sports@f123069; full reconciliation run + write-flips pending)
  - Fixture truthset recovery — chain runner finalisation + dedup_phantom_after_recovery script: ~1.5 ai-days (~75% done
    per audit)
  - Phantom recon — SFI_STANDINGS + open-meteo + UAC date ranges: ~1 ai-day (operator decisions pending)
  - 288M ODDS_API legacy row migration + MDPS bucketing: ~2 ai-days (scoped, not started)
  - Sports MTDS slice to ≥99% (per-source ≥99% across all 6 source families): ~1.5 ai-days
  - Sports predictions e2e (sports half — predictions ML half goes to predictions_master): ~1.5 ai-days
- **Parallelism factor**: ~3x (the 6 sport sources have largely independent backfills; rename + honest-coverage +
  recovery are independent workstreams). **~3-4 calendar days** wall-clock with 3+ parallel agents.
- **Critical path to 2026-05-23 cutover**: features-pipeline-running (no live ML this cycle); rename Phase 2-4 +
  honest-coverage Phase 2 are the gates that unblock features-pipeline. Live trading on sports is **post-May-23**;
  master plan readiness floor is "DART manual-trade gate green" with batch features computing daily.

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
  `api_football_minimal_flattening_removal_2026_05_07.md` for B.1) need verification — those are still in `plans/ai/`.
  After 4 recovery VMs drain (ETA 2026-05-08), the post-recovery dedup script (`dedup_phantom_after_recovery.py`) is the
  critical-path next move. Do NOT flip B.1/C.2/C.4/C.6 to DONE — those are real shipped-code-pending plans.

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
`predictions_master_2026_05_07.md`).

## Scrapers DEFERRED-INDEFINITELY 2026-05-12 per operator

> **Operator decision 2026-05-12 (verbatim)**: _"remove bet365 from the universe and docs and update plans we wont have
> bet365 anytime soon. same for other scrapers if implemented"_.

The 14 UK/EU scraper bookmakers (`bet365`, `bet888sport`, `betfred`, `betvictor`, `betway`, `boylesports`, `bwin`,
`coral`, `ladbrokes`, `paddypower`, `sbo` / `sbobet`, `skybet`, `unibet`, `williamhill`) plus `DRAFTKINGS` and `FANDUEL`
(US sportsbook browser-stub adapters) are **DEFERRED-INDEFINITELY** from the active sports universe. They do NOT
participate in any pre-cutover work; sports_master scope is now anchored on the **3 remaining-active sports venues**:
`ODDS_API` (multi-bookmaker aggregator, raw tick data), `PINNACLE` (sharp benchmark), `BETFAIR` (exchange / lay
liquidity).

Shipped 2026-05-12:

- `uac@56d941e` — removed `DRAFTKINGS`, `FANDUEL`, `BET365` from `VENUES_BY_ASSET_GROUP["sports"]` +
  `VENUE_DATA_TYPE_CAPABILITIES`; sports universe = `[ODDS_API, PINNACLE, BETFAIR]`.
- `mtds@66df106` — deleted 14 scraper entries from MTDS `_ADAPTER_PATHS` (`market_interface/sports/registry.py`);
  rewrote the 4 keep-venue paths (`betfair / matchbook / onexbet / odds_api`) from phantom
  `unified_sports_execution_interface.adapters.*` to canonical `execution_service.sports_execution.adapters.*` (SP-13
  hybrid fix). MTDS unit + integration tests updated (EXPECTED_KEYS 22→8).
- `execution-service@63ba730c` — DEFERRED-INDEFINITELY docstring banners on
  `execution_service/sports_execution/adapters/scrapers/__init__.py` + `adapters/browser/us_books.py`. Adapter source
  modules retained as future-work scaffolding; reference from MTDS or any production code path is forbidden until
  operator un-defers.

Retained scaffolding (NOT removed, but inactive):

- UAC `venue_constants.py`
  `BET365 / DRAFTKINGS / FANDUEL / WILLIAMHILL / LADBROKES / CORAL / PADDYPOWER / SKYBET / BETWAY / BETVICTOR / BOYLESPORTS / BWIN / BET888SPORT / UNIBET / BETFRED / SBOBET`
  venue constants + their `SPORTS_BOOKMAKER_WEB_VENUES` / `SPORTS_CAPTCHA_RISK` / `VENUE_EXECUTION_REGISTRY` /
  `INSTRUMENT_TYPES_BY_VENUE` / `VENUE_FEE_MODEL_MAP` / `VENUE_ALPHA_PROFILE` rows (broader UAC venue-constants cleanup
  is owned by the cross-asset catalogue audit plan Phase 1D `to_canonical_venue()` work; mass-sweep would collide with
  that plan).
- UAC `BETTING_SPORTS_VENUES` manifest entries for the 14 scrapers + `manifold` (manifold's a separate ghost — SP-1).
- execution-service `adapters/scrapers/*.py` files (14 scrapers + `base_scraper.py` + `version_registry.py`) and
  `adapters/browser/us_books.py` `_make_us_book` factory.

Closes:

- `plans/active/issues/catalogue_audit_sports_2026_05_12.md` SP-5 (universe-contraction).
- `plans/active/issues/catalogue_audit_sports_2026_05_12.md` SP-13 (P0 phantom-import-path bug; resolved by 14-row
  deletion + 4-row rewrite).

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

| Workstream                                                         | Status                                                                                                                                                                                                                            | Source                                      | Success gate                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| ------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Sports `data_available_at` → `available_at` rename + GCS migration | Phase 1 shipped; Phase 2-4 pending                                                                                                                                                                                                | `sports_data_available_at_rename`           | All sports parquets on disk carry the canonical `available_at` column; manifest entries reflect the rename; reader-side fallback path deleted; LookaheadBiasError fires correctly on stale `data_available_at`-only fixtures                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| Sports honest-coverage architecture (Phase 1+2)                    | Phase 1 partial                                                                                                                                                                                                                   | `features_sports_honest_coverage`           | features-sports reconciler `--apply-flips` run completes; legacy null-reason `empty_confirmed` rows classified per UAC SSOT (`EXPECTED_PAUSED_LEAGUE` / `EXPECTED_PRE_SOURCE_COVERAGE_START` / `SOURCE_RETURNED_ZERO`)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| Fixture truthset recovery — chain runner + drift audit             | 75% done; operator action pending                                                                                                                                                                                                 | `sports_fixtures_truthset_recovery`         | All 4 recovery VMs drained; `dedup_phantom_after_recovery.py` shipped + clean-run; phantom rate <1% per (league, source); chain runner emits `STARTED`+`PROCESSING_*` events for every fixture                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| Phantom recon — SFI_STANDINGS + open-meteo + UAC date ranges       | **SLOT-6 RE-RAN 2026-05-11 — 16.8% phantom rate, WAY above the <0.5% bar; needs audit-dispatcher + date-range-clip fixes (almost certainly mostly false-positive — the 2026-04-29 stale-sports-path-SSOT class). NOT --apply'd.** | `sports_phantom_recon_and_failure_triage`   | `reconcile_phantom_manifest_rows_all.py --asset-group sports --dry-run` reports <0.5% phantom rate; UAC `SOURCE_COVERAGE_START` + `KNOWN_COVERAGE_GAPS` reflect every probed gap. **SLOT-6 RUN** (`defi-phantom-recon-sports-20260511-195856`, 686086 captured rows in scope, done 14:33 UTC, exit 0): **570562 real / 115524 phantom = 16.8% phantom rate**. Phantom distribution (top): `STANDINGS` 12828, `SFI_LEAGUES` 12777, `INJURIES` 9843, `PLAYER_STATS` 878, `PLAYER_VALUES` 708, `FIXTURE_LINEUPS` 670, `FIXTURE_STATS` 492, `FIXTURE_EVENTS` 438, `TEAMS` 387, `ODDS` 279, `PREDICTIONS` 264, + ~63k in other data_types. **Almost certainly mostly false-positive** — sports has its own per-league/bare-path SSOT (`unified_api_contracts.sports.candidate_parquet_paths`) and `reconcile_phantom_manifest_rows_all.py`'s sports dispatcher (`"sports": { "prefix_tpls": [""], # handled separately via the unified UAC dispatcher`) must (a) use the CURRENT `candidate_parquet_paths` layout (the 2026-04-29 incident was a stale `entity=odds/` vs `entity=footystats_odds/` probe → false 26% ODDS phantom — same failure class), AND (b) apply the UAC `SOURCE_COVERAGE_START` + `DATA_TYPE_COVERAGE_START` + `KNOWN_COVERAGE_GAPS` date-range clips (pre-coverage-start dates would otherwise be flagged as phantoms — and the STANDINGS/SFI_LEAGUES/INJURIES clusters smell exactly like un-clipped pre-launch-date rows). **Pending (sports phantom-recon owner)**: verify the audit's sports dispatcher against the current `candidate_parquet_paths` SSOT + confirm the date-range clips are applied; THEN re-run; only `--apply`-flip the genuinely-real residual. Do NOT `--apply` the current 115524 (would corrupt the manifest, 2026-04-29-class). Cross-ref: `code_freeze_migrate_backfill_sequencing_2026_05_10.md` DONE-2026-05-11 deferral table + `harsh_orchestrator/pings/slot_6.md` 2026-05-11 ~14:33 UTC. |
| 288M ODDS_API legacy row migration + MDPS bucketing                | scoped; not started                                                                                                                                                                                                               | `sports_predictions_e2e` (sports half)      | Migration script ships per-VM-shard isolation; legacy rows re-keyed to canonical hive shape; MDPS bucketing reflects per-(league_id, day) instead of monolithic; coverage % unchanged post-migration (no data loss)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| Sports MTDS slice to ≥99%                                          | partial                                                                                                                                                                                                                           | `market_tick_data_to_100pct` (sports slice) | data-status drilldown shows ≥99% per (source, data_type, league_id) within each league's `SOURCE_COVERAGE_START` clip; residual stamped with typed `EMPTY_CONFIRMED_REASONS`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |

## Consolidated todos (P0/P1 only)

### Sports `data_available_at` → `available_at` rename (folded 2026-05-07; full DAG below)

**Cross-plan coordination**: this rename is **Stage 1** of the workspace-wide manifest migration. See
[`manifest_migration_master_2026_05_07.md`](./manifest_migration_master_2026_05_07.md) for the sequencing DAG, conflicts
(esp. `batch_handler.py` overlap with writegate Phase 2.C), VM impact matrix, and operator pause-resume guidance. Stage
1 Phase 3 features-sports `batch_handler.py` rename SHOULD ship in the SAME commit as writegate Phase 2.C
`_ensure_timestamp` shim deletion (avoids two-commit churn on same lines).

**Folded from `sports_data_available_at_rename_2026_05_07.md`.** Original plan archived at
`plans/archive/sports_data_available_at_rename_2026_05_07.md`. Phase 1 SHIPPED via `instruments-service@8050477`
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
- [x] [AGENT] P1. Apply UAC `SOURCE_COVERAGE_START` clipping in data-status denominators. (verified 2026-05-07:
      deployment-api/deployment_api/services/data_status_service.py:58 imports `clip_dates_to_source_coverage`, applied
      at lines 451/494/621) [AUDIT 2026-05-07: FRESH — actionable; deployment-api wiring needed (per MEMORY entry,
      deployment-api has B.3 per-chain clipping wired analogously)]
- [x] [AGENT] P1. Apply UAC `KNOWN_COVERAGE_GAPS` for documented date-range provider outages. (verified 2026-05-07:
      deployment-api/deployment_api/services/data_status_service.py:61 imports `is_in_known_gap`, applied at lines
      460/505) [AUDIT 2026-05-07: FRESH — actionable]

### Audit findings 2026-05-07 — folded from session wrapper

**Source**: `plans/ai/session_2026_05_07_data_status_audit_findings.md` rows B.1 / C.2 / C.3 / C.4 / C.6 / C.7 / C.10.
Operator inspected the deployment-ui data-status panel + schema modals; the findings below all surfaced as
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

Plan in `plans/ai/api_football_minimal_flattening_removal_2026_05_07.md` (5 phases). Owner-side todo:

- [x] [SCRIPT] P0. UAC `unified_api_contracts/external/api_football/normalize.py:372-395` — replace 4 stub-pass-through
      normalizers with real flatteners. (UAC@c76e6d0 — all 4 normalizers flatten nested structs into per-row dicts;
      `_FIXTURE_STAT_TYPE_MAP` 18-entry closed set; `normalize_api_football_lineup` explodes startXI+subs.)
- [x] [SCRIPT] P0. UAC contract update for the 4 data_types — declare the actual flattened columns (per-stat, per-event,
      per-lineup-slot, per-injured-player), `cadence: "per_fixture"`. (UAC@c76e6d0 — SPORTS_FIXTURE_STATS /
      FIXTURE_EVENTS / FIXTURE_LINEUPS / INJURIES SchemaContracts extended with full ColumnSpec lists.)
- [x] [SCRIPT] P0. instruments-service AF batch_handler: switch from raw-passthrough to the flattening writer.
      (instruments-service@539130f — all 4 normalizers wired via chain.from_iterable in api_football adapter.)
- [ ] [SCRIPT] P0. Migration shape: flip every existing manifest row for the 4 data_types →
      `record_failed(reason=INCOMPLETE_PAYLOAD_PRE_FLATTENING, attempted_at=now)`, delete the thin parquets, then
      re-fetch via a dedicated VM (`af-backfill-flatten-{ts}`). The 4 data_types use ISOLATED endpoints
      (`/fixtures/statistics`, `/fixtures/events`, `/fixtures/lineups`, `/injuries`) — separate from `/fixtures` itself
      — so quota cost is bounded to the 4-endpoint × historical-fixture-set product, NOT a full FIXTURES re-fetch.
      [AUDIT 2026-05-07: FRESH — actionable; coordinate with manifest_migration_master_2026_05_07:Stage 3]
- [x] [TEST] P0. Normalizer output shape tests. (UAC@c76e6d0 — 13 unit tests in
      `tests/unit/test_normalize_api_football.py` covering full payload shape, partial null-fill, unknown-stat-type
      skip, no-coach lineup, missing-fixture injury, malformed-input returns. `test_sports_contracts.py` parametrized
      cases verify schema registration for all 4 data_types. Note: `test_cassette_schema_parity.py` was NOT extended —
      the per-normalizer unit tests satisfy the same invariant.)
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

- [x] [SCRIPT] P0. UAC `unified_api_contracts/external/transfermarkt/normalize.py` — extend `normalize_player_values` to
      emit per-(team, player, season, fetch_day) rows with `player_id`, `player_name`, `position`, `age`,
      **`market_value_eur`**, `contract_until`, `current_club_id`, `nationality_iso`. [AUDIT 2026-05-07: FRESH —
      actionable] **COMPLETED 2026-05-13**: UAC@3b29f7e — added normalize_player_values() function + PlayerValue
      NamedTuple.
- [x] [SCRIPT] P0. UAC contract: bump PLAYER_VALUES schema to per-player shape; old team-aggregate becomes a derived
      view in features-sports OR is dropped if features-sports is happy rolling per-player at compute time. [AUDIT
      2026-05-07: FRESH — actionable] **COMPLETED 2026-05-13**: UAC@3b29f7e — updated SPORTS_PLAYER_VALUES to per-player
      granularity (player_id symbol column, dropped squad_size/player_count team aggregates).
- [ ] [SCRIPT] P0. **DEFERRED**: Migration shape: same flip-to-failed + delete + re-fetch pattern as B.1;
      Transfermarkt's per-team-per-season endpoint is already isolated, no upstream impact. [AUDIT 2026-05-07:
      actionable; depends on features-sports readiness to consume per-player shape]
- [ ] [TEST] P0. **DEFERRED**: Cassette parity test for the new per-player shape. [Requires migration to be spec'd]

#### C.6 + C.10 — `match_end_time` cascade implementation (groups together)

The cascade is codified in CLAUDE.md (api_football native → SFI freeze → footystats/understat → kickoff+120min
low-confidence fallback) but no writer implements it. Load-bearing for odds-settlement timing + post-match
`available_at` stamping.

- [ ] [SCRIPT] P0. **Step 1**: api_football FIXTURES write-time computation. When `status_short ∈ {FT, AET, PEN}`,
      compute `match_end_time ≈ kickoff + periods.second.duration + et.duration +     injury_time` from the API
      response. Add `match_end_time` column to UAC FIXTURES contract. [AUDIT 2026-05-07: FRESH — actionable] **PARTIAL
      2026-05-12 slot 5 (instruments-service@9bffca2)**: UAC field `match_end_time: datetime | None` added to
      `CanonicalFixture`; `detect_match_end_time()` helper shipped in SFI adapter. **UAC HALF SHIPPED 2026-05-13**:
      UAC@0ba9e5b — `match_end_time` column added to SPORTS_FIXTURES schema (parquet-level). The write-path call
      (instruments-service SFI progressive-stats writer → populate `fixture.match_end_time`) is NOT yet wired.
      **DEFERRED**: wire `detect_match_end_time()` result into instruments-service SFI progressive-stats write path so
      the `match_end_time` field is populated on the written `CanonicalFixture` object.
- [x] [SCRIPT] P0. **Step 2**: SFI progressive freeze detection. Add `ft_timer` (raw `timer_seconds` from the
      snapshot) + `match_end_time` (detected freeze point — the last snapshot where `timer_seconds` advances) columns to
      UAC `SFI_PROGRESSIVE_STATS` contract. Detect freeze at write-time in
      `instruments-service/instruments_service/sfi/normalize.py` (or wherever the SFI snapshot writer lives). [AUDIT
      2026-05-07: FRESH — actionable] **COMPLETED 2026-05-13**: UAC@1848647 — added ft_timer (int64) + match_end_time
      (datetime64[ns, UTC]) to SFI_PROGRESSIVE_STATS schema contract.
- [x] [SCRIPT] P0. **Step 3**: UTL helper
      `unified_trading_library.fixtures.resolve_match_end_time(fixture_id) -> MatchEndTimeResolution(datetime, str)`
      walking the cascade in priority order: api_football FIXTURES.match_end_time → SFI freeze → footystats/understat
      post-match timestamp → low-confidence `kickoff + 120min` fallback. Returns MatchEndTimeResolution with timestamp +
      provenance. [AUDIT 2026-05-07: FRESH — actionable] **COMPLETED 2026-05-13**: UTL@89c0ae15 — implemented
      resolve_match_end_time() with NamedTuple return + cascade logic.
- [ ] [SCRIPT] P0. Wire `resolve_match_end_time()` into per-source `available_at` stamping for post-match data_types
      (FIXTURE_STATS / SFI_PROGRESSIVE_STATS / understat XG / fixture_player_stats) per CLAUDE.md "available_at per-row,
      write-time, equal-to-live-pipeline-arrival" rule. [AUDIT 2026-05-07: FRESH — actionable; coordinate with
      sports_master:Phase 3 rename]
- [ ] [SCRIPT] P0. **DEFERRED from slot 5 Phase 2.D (2026-05-12)**: Wire `assert_available_at_present` into the
      instruments-service SFI progressive-stats / FIXTURES write path (spawn prompt step 8). Blocked on Step 3 UTL
      helper above. Successor: this item (step 3 + wire = same Phase 2.D completion sprint).
- [x] [SCRIPT] P0. **DEFERRED from slot 5 Phase 2.D (2026-05-12)**: Derive
      `report_time = match_end_time + SFI_DATA_LAG_P95_SECONDS` in instruments-service SFI progressive-stats write path.
      (instruments-service@af06124 — `match_end_time` + `report_time` columns added to SFI progressive stats rows in
      orchestrator per-match loop, using `detect_match_end_time()` + `SFI_DATA_LAG_P95_SECONDS=300`.)
- [ ] [TEST] P0. Unit tests covering each branch of the cascade + the `kickoff + 120min` fallback shape. [AUDIT
      2026-05-07: FRESH — actionable] **PARTIAL 2026-05-12 slot 5 (instruments-service@9bffca2)**: 5 unit tests for
      freeze-detect + announced_at + PST/CANC shipped in `test_phase2d_match_timing.py`. Cascade-branch tests (Step 3
      UTL helper) still needed.
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
- [x] [SCRIPT] P1. **Follow-up #1 — STANDINGS flatten.** UAC `normalize_api_football_standing` rewrite to unpack the
      nested `league.standings: [[...]]` array into per-(league, team, season, position) row records with full stats
      subobjects (all/home/away each have played/win/draw/lose/goals/goalsAgainst/goalDifference/points). Same migration
      shape as B.1: flip manifest STANDINGS rows → `attempted_failed reason=INCOMPLETE_PAYLOAD_PRE_FLATTENING` + delete
      thin parquets + re-fetch via dedicated VM (`af-backfill-standings-{ts}` if isolated, or fold into
      af-backfill-flatten-{ts} from B.1). Cassette parity test extension to lock the flat shape. **COMPLETED
      2026-05-13**: UAC@ac12d80 — normalize_api_football_standing() rewrite + SPORTS_STANDINGS schema flatten (14 → 32
      columns: team_id/name/logo + all/home/away × played/win/draw/lose/goals_for/goals_against). Migration still
      deferred (operational VM launch).
- [ ] [SCRIPT] P1. **Follow-up #2 — XG per-shot flatten (BIG WIN).** UAC `normalize_understat_feature_record` is
      currently ONE feature value per shot. Replace with `normalize_understat_shot` returning a flat dict with all ~15
      fields: `xg`, `xa`, `minute`, `player_id`, `player_name`, `situation` (open_play / set_piece / penalty),
      `shot_type` (header / left_foot / right_foot / other), `result` (goal / saved / missed / blocked / post), `x`,
      `y`, `last_action`, `home_or_away` (h / a), `assist_player_id`, `season`, `match_id`. Lift `feature_name=shot_xg`
      callers to read from the `xg` column instead. Same B.1 migration shape (flip + delete + re-fetch via dedicated
      `us-backfill-shots-flatten-{ts}` VM + cassette parity). features-sports consumers updated to read per-shot
      dimensions; XG features become much richer (position-on-pitch, shot-quality decomposition, set-piece vs open-play
      splits).
- [x] [SCRIPT] P1. **Follow-up #3 — MATCHES field-mapping fix.** Smaller-scope fix to `normalize_footystats_match`:
      replace 15+ hardcoded `None` with proper `team_a_*` / `team_b_*` → `home_*` / `away_*` mappings from the
      FootyStatsMatch source dataclass. Add `referee` mapping if FootyStats provides it on the match endpoint (verify
      via raw-payload sample). Migration: if downstream consumers tolerate NaN, no flip needed (just landing the new
      normalizer + re-fetching going forward writes populated columns from now on; historical rows stay None-populated
      and are NaN-tolerant); if any consumer explicitly checks column existence via `.dropna(subset=...)`, then full
      B.1-shape migration (flip + delete + re-fetch) is required. Cassette parity test catches the wire-up regression.
      (UAC@4e23bd9 — added home*goals_halftime/halftime, home_shots_on_target, home_yellow_cards, home_red_cards,
      home_fouls, home_offsides + away*\* variants to FootyStatsMatch; normalized to CanonicalFixture fields)

### FIXTURES schema split — SCHEDULE + OUTCOMES (migrated from issue `fixtures_lookahead_bias_post_match_scores_2026_05_08`)

Source issue archived to `plans/archive/issues/`. Critical lookahead-bias fix: today, post-match scores ride the same
FIXTURES row as the schedule, and `available_at` uses an arbitrary `kickoff − 7d` heuristic instead of real announcement
time. Every sports feature compute that joins FIXTURES on schedule fields can silently leak post-match scores into
pre-match feature windows. Already covered for the match_end_time cascade by section C.6 above (Q4 of the related
lifecycle issue); this sub-section covers the SCHEMA SPLIT (Q1 + Q3 of the lookahead-bias issue) which C.6 does NOT.

**Cross-plan banner**: writegate Phase 2.D `available_at` strict-mode enforcement (already shipped) flips this to a
hard-fail once the new schema lands — schema split MUST ship in a single workspace-wide commit so writegate doesn't
break sports parquets mid-migration. Coordinate with `writegate_honest_coverage_endtoend_2026_05_06`. Reader-side join
helper hides the split so consumers don't need to refactor (per issue's preferred approach).

- [ ] [SCRIPT] P0. UAC: split `CanonicalFixture` into `CanonicalFixtureSchedule` (kickoff_time, league_id, home_team_id,
      away_team_id, venue, status, scheduled fields) + `CanonicalFixtureOutcomes` (home_score_regulation,
      away_score_regulation, home_score_after_extra_time, away_score_after_extra_time,
      home_score_after_penalty_shootout, away_score_after_penalty_shootout, home_penalty_shootout_score,
      away_penalty_shootout_score, went_to_extra_time, went_to_penalties, match_result, match_end_time). New
      entity_types `FIXTURES_SCHEDULE` + `FIXTURES_OUTCOMES` replacing the single `FIXTURES`. Both written to same
      `sports_reference/by_date/day=<day>/...` path with separate `entity=fixtures_schedule` /
      `entity=fixtures_outcomes` sub-folders. Per-row `available_at` differs: SCHEDULE = `announced_at` (per-league
      empirical floor — see workstream below); OUTCOMES = `match_end_time` (from C.6 cascade already shipped).
- [ ] [SCRIPT] P0. UTL reader-side join helper
      `unified_trading_library.fixtures.read_fixtures_joined(day, league_id) ->     pd.DataFrame` returns single fixture
      row with both schedule + outcome columns + a `outcomes_available_at` column. Consumers see one DataFrame;
      LookaheadBiasError fires per-row when feature compute timestamp < outcomes_available_at AND any outcome column is
      read.
- [ ] [SCRIPT] P0. Per-league announcement-floor empirical audit (Phase 2 of issue). 2-week observation window per
      league; record api_football fixture-publication-time vs kickoff_time. Output: per-league
      `ANNOUNCEMENT_FLOOR_HOURS` table in UAC `unified_api_contracts.canonical.crosscutting.availability_semantics`
      (replacing the kickoff−7d heuristic). Default 14d for unobserved leagues; per-league override once observed.
- [ ] [SCRIPT] P1. Cross-source backfill for historical `announced_at` where api_football didn't capture it (Phase 3
      optional). footystats + SFI publication-time as fallback. Stamp at write-time during the migration.
- [ ] [SCRIPT] P0. One-shot manifest migration: existing `entity=fixtures` rows split into `entity=fixtures_schedule` +
      `entity=fixtures_outcomes`. Script under `instruments-service/scripts/migrate_fixtures_split.py` mirroring the
      existing `migrate_sports_available_at_column.py` pattern (idempotent, per-blob CAS, dry-run + apply).
- [ ] [QG] P0. Coordinate with writegate Phase 2.D — schema split commit must ship same-day as writegate
      strict-mode-flip-on-FIXTURES (avoid mid-migration hard-fail).

### Cross-source fixture status verifier + status enum (migrated from `fixtures_postponed_cancelled_lifecycle_2026_05_08`)

Source issue archived. Two failure modes: (1) api_football misflags postponed fixtures as cancelled (lineups + stats
populated despite `cancelled` status — the match was played); (2) reference itself misses match data despite the match
being played (cross-source data exists but never reconciled). Postponed-fixture identity behaviour empirically
unverified — three plausible models (a/b/c — see issue body) need observation.

**Cross-plan banner**: feeds Issue-1 `FIXTURES_OUTCOMES` schema (above) — must distinguish match-played-but-mis-flagged
vs genuinely-cancelled rows BEFORE the OUTCOMES split lands so the OUTCOMES rows aren't poisoned by mis-flagged
cancellations.

- [x] [SCRIPT] P0. UAC `MatchStatus` typed StrEnum SSOT — 9 canonical states + `AF_STATUS_SHORT_MAP` + grouping
      frozensets + `from_af_short()` classmethod. (UAC@1a831b0 —
      `unified_api_contracts/canonical/domain/sports/fixture_status.py`; exported via domain `__init__`.) **DEFERRED**:
      "Replace freeform string status across all sports adapters" — the SSOT is shipped; adapter migration (replacing
      `{"FT","AET","PEN"}` ad-hoc sets with `AF_COMPLETED_CODES` / `MatchStatus` comparisons) is a follow-up refactor
      across instruments-service adapters.
- [ ] [SCRIPT] P0. Cross-source verifier integration at instruments-service orchestrator commit-time. When api_football
      reports `CANCELLED` BUT footystats / SFI / understat reports the fixture has match data (lineups + stats +
      events): emit `FIXTURES_STATUS_DISCREPANCY` event (NEW UAC LifecycleEventType) + flip api_football status to
      `POSTPONED_RESCHEDULED` (or whichever the cross-source ground truth indicates) at write-time + stamp
      `status_provenance: "cross_source_override"` column. Manifest `record_failed(reason=REFERENCE_STATUS_DISCREPANCY)`
      for the originally-mis-flagged row + `record_captured` for the corrected row.
- [ ] [AGENT] P1. Empirical investigation — postponed-fixture identity. Pull 30 confirmed-postponed fixtures from
      api_football across 2024-2026; confirm for each whether: (a) same `fixture_id` retained at the new kickoff, OR (b)
      new `fixture_id` issued at reschedule, OR (c) original `fixture_id` deleted + replaced. Document the
      empirically-correct model in `codex/02-data/sports-fixtures-lifecycle.md` (NEW codex doc; see codex todo below).
- [ ] [AGENT] P0. NEW codex doc `unified-trading-pm/codex/02-data/sports-fixtures-lifecycle.md` capturing: status enum
      taxonomy, postponed-fixture identity model (case a/b/c), cross-source verifier rules, FIXTURES_STATUS_DISCREPANCY
      event semantics. SSOT for both this section + Issue-1 schema split.

### Match HT/ET/PEN timestamps + score-distinction columns + pre-features extractor (Q5 + Q6 + Q7 from `instruments_lifecycle_and_fixtures_endtime_cascade_2026_05_08`)

Source issue archived. Q1+Q2 (futures + options expiry) are migrated to `tradfi_master_2026_05_07` (Batch D); Q4 is
already covered by the C.6 match_end_time cascade above; Q3 (predictions) is gold standard, no work. Q5+Q6+Q7 land here
in sports_master Phase 3 (per operator decision 2026-05-08: tradfi_master owns Q1+Q2; sports_master owns Q4-Q7; operator
chose Option (a) for Q7 — UTL helper at instruments-service write-time, NOT a separate pre-features extractor service).

- [ ] [SCRIPT] P0. UAC `CanonicalFixtureSchedule` extension (Q5): `halftime_start_time`, `halftime_end_time`,
      `extra_time_first_half_start_time`, `extra_time_first_half_end_time`, `extra_time_second_half_start_time`,
      `extra_time_second_half_end_time`, `penalty_shootout_start_time`, `penalty_shootout_end_time`,
      `whistle_full_time_at`. All nullable (regular matches don't have ET/penalties). Populate from api_football
      `periods.first` / `periods.second` / `et` / `score.penalty.played_at` at write-time.
- [ ] [SCRIPT] P0. UAC `CanonicalFixtureOutcomes` score-distinction columns (Q6): `home_score_regulation`,
      `home_score_after_extra_time`, `home_score_after_penalty_shootout`, `home_penalty_shootout_score`,
      `away_score_regulation`, `away_score_after_extra_time`, `away_score_after_penalty_shootout`,
      `away_penalty_shootout_score`, `went_to_extra_time` (bool), `went_to_penalties` (bool), `match_result` (`home_win`
      / `away_win` / `draw_regulation` / `home_win_after_et` / `away_win_after_et` / `home_win_after_pens` /
      `away_win_after_pens` — closed StrEnum). Populate from api_football `score.fulltime` / `score.extratime` /
      `score.penalty`. NEVER collapse pen-shootout score into single field.
- [ ] [SCRIPT] P0. UTL helper `unified_trading_library.fixtures.extract_match_lifecycle(fixture_id) -> MatchLifecycle`
      at instruments-service write-time (Q7 — operator chose Option (a) UTL helper, NOT separate service). Reads
      api_football response, returns typed dataclass with all HT/ET/PEN timestamps + score-distinction columns. Called
      by FIXTURES adapter at orchestrator commit. Avoids the circular dependency the issue's pre-features-extractor
      option (b) introduced (features-sports would need to wait for instruments-service regardless).
- [ ] [SCRIPT] P1. Deferred follow-up TODO: if features-sports HT-feature work grows past 3 calculators, extract
      `match_lifecycle_extractor` into a dedicated pre-features service stage (Q7 option (b)). Not scoped now per
      operator direction.
- [ ] [TEST] P0. Unit tests for `extract_match_lifecycle` covering: regulation match (no ET/PEN), ET-only match, full
      ET+PEN match, abandoned match (whistle_full_time_at NULL), missing-data fallback (low-confidence kickoff+90min).
- [ ] [VERIFY] P0. After ship, deployment-ui schema modal for FIXTURES_SCHEDULE / FIXTURES_OUTCOMES shows all 9 new
      timestamp columns + 11 new score-distinction columns populated for completed fixtures.

### Per-fixture orchestrator iteration (migrated from `sports_per_fixture_anchored_cascade_2026_05_08`)

Source issue archived. instruments-service orchestrator iterates per-league-per-day for FIXTURE_STATS / EVENTS / LINEUPS
/ INJURIES instead of per-fixture-id. If api_football returns 11 of 12 fixtures, the 12th's missing stats produce ZERO
manifest rows instead of per-fixture expected universe. Honest-coverage broken for sports.

**Cross-plan banner**: writegate Phase 3.D.5 Wave 3 v2 enumerator must wire sports expected-universe = captured
FIXTURES_SCHEDULE rows (Phase 4 of source issue documented this dependency). Coordinate with
`writegate_honest_coverage_endtoend_2026_05_06`.

- [ ] [SCRIPT] P0. Orchestrator refactor: per-fixture-id iteration for FIXTURE_STATS / FIXTURE_EVENTS / FIXTURE_LINEUPS
      / INJURIES. Replace `for league_id in leagues: for date in dates: fetch(league, date)` with
      `for fixture in     captured_fixtures_today(league_id, date): fetch(fixture.fixture_id)`. Pre-flight: depends on
      FIXTURES_SCHEDULE rows existing for the (league, date) pair (validate via Phase A.10 preflight from
      `instruments_live_master_2026_05_08`).
- [ ] [SCRIPT] P0. Manifest row_key extension: `fixture_id` becomes a first-class shard axis for the 4 per-fixture
      data_types. v6 ManifestWriter already supports arbitrary row_keys; just wire the column. Per-instrument shard atom
      per CLAUDE.md "shard-granularity SSOT" — for sports per-fixture data, row_key =
      `(asset_group, source,     data_type, league_id, fixture_id, day)`.
- [ ] [SCRIPT] P0. Cluster validation at `record_captured` for bundled fixture-day parquets (per Phase 1A of writegate).
      Add `FIXTURE_STATS` / `FIXTURE_EVENTS` / `FIXTURE_LINEUPS` / `INJURIES` to UAC `BUNDLED_DATA_TYPES` with
      `expected_root_clusters = {league_id: count_of_fixtures_today}` extracted via FIXTURES_SCHEDULE join.
- [ ] [SCRIPT] P0. One-shot manifest migration: existing per-league-per-day rows expanded into per-fixture rows. Script
      under `instruments-service/scripts/migrate_per_fixture_manifest.py` mirroring existing migration patterns.
      Idempotent; dry-run + apply.
- [ ] [VERIFY] P0. Post-migration smoke: random sample of 20 (league, date) pairs across 2018-2026 — sum of per-fixture
      rows == count of captured fixtures (no orphans, no duplicates).
- [ ] [AGENT] P1. Open question — does api_football provide a per-fixture endpoint or only bulk? If only bulk, the
      orchestrator's per-fixture iteration becomes a filter on a single bulk fetch (rate-limit budget unchanged). Verify
      via the api_football docs + a smoke probe before committing the refactor shape.

### EXPECTED_BOOKMAKER_MARKET_SETS NaN-fill enumeration (migrated from `odds_fixture_anchored_nan_fill_2026_05_08`)

Source issue archived. Today's orchestrator fetches the day-level ODDS endpoint; no logic ensures every (fixture ×
bookmaker × market_type) triple is enumerated. Missing triples produce zero rows instead of NaN-fill, violating the
zero-volume-bar precedent from category-D MDPS pattern (CLAUDE.md "Honest absence" rule). Arbitrage / odds-movement
features silently miss bookmaker × market gaps.

- [ ] [AGENT] P1. Empirical audit per league tier: which bookmakers + markets are expected to be present per (fixture,
      league_tier)? Output: UAC
      `EXPECTED_BOOKMAKER_MARKET_SETS: dict[LeagueTier, dict[BookmakerKey,     list[MarketType]]]`. League tiers:
      TIER_1_DOMESTIC (EPL/LaLiga/SerieA/Bundesliga/Ligue1), TIER_2_DOMESTIC, TIER_1_INTERNATIONAL (UCL/UEL), etc.
      Empirical baseline: 2-week sample of fully-covered fixtures per tier.
- [ ] [SCRIPT] P0. Orchestrator post-FIXTURES_SCHEDULE-capture step: for each fixture today, enumerate expected (fixture
      × bookmaker × market) triples per `EXPECTED_BOOKMAKER_MARKET_SETS[tier]`; for each missing triple, write a
      NaN-fill row with `record_captured` (NaN values per workspace honest-absence rule, NOT `record_empty` —
      `record_empty` is for legitimately-absent source responses; NaN-fill is for "we expected this triple but the
      source didn't return it").
- [ ] [SCRIPT] P0. Cluster validation kwargs at `record_captured` for ODDS bundled writes:
      `expected_root_clusters = {fixture_id: len(EXPECTED_BOOKMAKER_MARKET_SETS[tier])}` per Phase 1A of writegate.
- [ ] [AGENT] P1. Downstream consumer guidance — features-sports arbitrage / odds-movement calculators handle NaN rows:
      arbitrage drops NaN bookmakers from the pricing comparison (already correct behavior); odds-movement treats NaN
      snapshot as no-update (already correct). Document in `codex/02-data/honest-absence-downstream-handling.md` § "ODDS
      NaN-fill semantics" (extend existing doc, not new).

## `available_at` + lookahead-bias coordination (2026-05-08 audit)

> **Coordinator:**
> [`active/available_at_lookahead_bias_completion_2026_05_08`](../active/available_at_lookahead_bias_completion_2026_05_08.md).
> Sports is the canonical reference precedent: features-sports `_enforce_pit_sports`
> ([data/writer.py:42-72](../../../features-sports-service/features_sports_service/data/writer.py#L42-L72)) shows the
> writer-boundary `PointInTimeEnforcer(strict=True)` pattern other features-\* services should mirror. Sports historical
> parquet backfill
> ([`migrate_sports_available_at_column.py`](../../../features-sports-service/scripts/migrate_sports_available_at_column.py)
> shipped 2026-05-07) is the canonical reconciler shape to generalize for cefi / defi / tradfi / predictions
> (coordinator Phase 2).

- [ ] [SCRIPT] P0. **Sports feature_groups → UAC `FEATURE_REQUIRED_INPUTS`**. ~60 sports feature_groups (form,
      league_strength, fixture_xg, lineup_quality, market_consensus, etc.) need registry entries. Source-of-truth:
      `features-sports-service/features_sports_service/calculators/` calculator metadata. Coordinator Phase 4.

## May-23 deliverable (folded from `sports_ml_may_23_2026.epic` 2026-05-08)

> **Folded epic** (operator direction 2026-05-08): consolidated from `plans/epics/sports_ml_may_23_2026.epic.md`.
> Archived: [`plans/archive/sports_ml_may_23_2026.epic.md`](../archive/sports_ml_may_23_2026.epic.md).

**Why:** Sports ML prediction ships **backtest-only** for May 23 — but unlike S&P prediction (data → ML training only),
this goes **all the way through strategy backtest + execution backtest** as well. ML signal + strategy + execution all
backtest in the unified pipeline. No live trading. Bugs/backfills/schema fixes inclusive at every layer.

### End-state at May 23 (success criteria)

- [ ] **Sports ML model trains end-to-end in batch** on representative history.
- [ ] **Strategy backtest** of ML signal runs end-to-end through unified pipeline (no standalone backtest engine, no
      inline settlement) — strategy interacts with PBM + R&E + execution-service per `Batch = Live` rule.
- [ ] **Execution backtest** runs through matching engine (Sports L0 TOB matcher, per matching_engine SSOT) — simulated
      fills with accurate slippage / commission / latency / venue liquidity, NOT face-value odds.
- [ ] **Sports data pipeline clean** end-to-end: instruments (URDI sports/) + odds (api_football, footystats,
      odds_api) + features (features-sports) — no phantom rows, no NaN placeholders, manifest 100% honest,
      `available_at` correctly stamped per row.
- [ ] **Honest-coverage baseline** for sports manifest: ratchet established + monitored.
- [ ] **Phantom recovery complete** for sports fixtures (truthset rebuild + capture-status reclassification).
- [ ] **Strategy + execution layers fixed where needed** — bugs across ML + strategy + execution caught this cycle.

### IN/OUT scope

- **IN**: full backtest pipeline (instruments → odds → features → ML training → ML inference → strategy → execution →
  PBM → R&E → P&L attribution); sports backfill end-to-end (api_football / footystats / transfermarkt / understat /
  soccer_football_info / open_meteo / odds_api / MDPS odds horizon bucket); sports phantom-recovery + honest-coverage
  close-outs; `available_at` rename + per-row stamping (kickoff−60min for lineups, event-time for events, match_end_time
  for post-match); execution backtest with L0 TOB matcher (real fills); 2-year-equivalent backtest config grid.
- **OUT**: live trading; live odds capture (forward-poll continues but not gating); multiple ML archetypes (one is the
  bar); production deployment.

### Cross-epic handshakes

- **Depends on:** `cross_cutting_may_23_2026` for strategy catalogue (sports ML archetype + venues), infrastructure
  baseline, UI replication of backtest harness.
- **Shares with:** `cefi_ml`, `sp_prediction`, `prediction_markets` (now folded into respective masters) share ML
  lifecycle (training pipeline, model registry, drift detection, batch backtest harness).
- **Provides to:** `predictions_master` (folded `prediction_markets`) may consume sports ML signals as inputs to
  sports-betting prediction-market strategies (Polymarket fixture markets).

### Open questions

- [x] ✓ **Which sports ML archetype — RESOLVED 2026-05-08.** **Match-outcome (1X2)**. Most data-rich label, best
      signal-to-noise (FSS progressive + lineups + injuries + odds movement → home/draw/away), cleanest walk-forward
      validation. Goal-scorer + in-play live-odds DEFERRED post-cutover. See
      `plans/active/operator_decisions_2026_05_08.md`.
- [x] ✓ **Leagues in scope — RESOLVED 2026-05-08.** **Top-5 European tier** for May-23 backtest deliverable: EPL +
      LaLiga + Serie A + Bundesliga + Ligue 1. Deepest historical coverage, tightest market-making, most consistent
      fixture metadata. MLS + all-leagues DEFERRED post-cutover.
- [x] ✓ **Bookmaker scope — RESOLVED 2026-05-08.** **odds_api closing prices for May-23 batch backtest** (consensus
      market-implied probability at kickoff, no leakage since stamped `available_at = kickoff`). Top-5 bookmakers by
      EXPECTED_BOOKMAKER_MARKET_SETS coverage (Bet365 + Pinnacle + 1xBet + Marathonbet + William Hill). Slippage: 1%
      over closing for liquid markets, 3% for thin. MDPS odds horizon bucket DEFERRED with in-play archetype.

## Catalogue audit findings (re-audited 2026-05-12)

Folded from `plans/archive/issues/catalogue_audit_sports_2026_05_12.md` — re-audit verdicts (2026-05-12,
ikenna-sports-re-audit-sp-5-10-12 slot 8 sub-agent):

- [ ] [SCRIPT] **P0**. **SP-13 — MTDS sports registry phantom-import bug (critical-path May-23 blocker)**.
      `market-tick-data-service/market_tick_data_service/market_interface/sports/registry.py:23-40` `_ADAPTER_PATHS`
      routes 18 sportsbook/exchange/bookmaker keys (betfair / matchbook / onexbet / odds_api / skybet / coral /
      paddypower / betfred / betvictor / boylesports / bwin / ladbrokes / williamhill / betway / unibet / bet888sport /
      bet365 / sbo) to `unified_sports_execution_interface.adapters.*` — a **phantom Python package** (no such package
      exists workspace-wide; URDI ELIMINATED 2026-03-26 per codex/GLOSSARY.md). Every `adapter_for_bookmaker(key)` call
      raises `ModuleNotFoundError` at the `importlib.import_module()` line. **Fix**: rewrite the 18 phantom paths to
      `execution_service.sports_execution.adapters.<subdir>.<module>` per the post-merge layout in
      `execution-service/execution_service/sports_execution/adapters/__init__.py:1-32`. Other agent in flight on this
      fix.
- [ ] [SCRIPT] **P1**. **SP-5 — bet365 + DK/FD scrapers**. bet365 wired wrong (phantom import per SP-13); DraftKings /
      FanDuel have NO scraper (only `NotImplementedError` browser stubs in `sports_execution/adapters/scrapers/`). Fix
      scope: either ship the scrapers OR delete the venue capability entries for DK/FD so they don't show as live in the
      catalogue.
- [ ] [SCRIPT] **P1**. **SP-10 — cluster-validation kwargs MISSING workspace-wide**. 0 hits for `expected_root_clusters`
      / `cluster_extractor` in any sports adapter. CLAUDE.md cluster-validation mandate (`record_captured()` for bundled
      data_types) not wired through `instruments_service/engine/orchestrator.py` for sports per-fixture bundles. Add
      cluster kwargs at the bundle-writer boundary in orchestrator.
- [ ] [SCRIPT] **P1**. **SP-12(a) — execution-service `sports_execution` missing `classify_venue_error()`**.
      instruments-service sports reference adapters GREEN via `BaseSportsReferenceAdapter`; execution-service
      sports_execution has 0 hits. Add classify wiring at adapter-base level.
- [ ] [SCRIPT] **P2**. **SP-12(e) — capability-decl vs method match**. 17 caps declared vs 15 execution classes present.
      Reconcile.
- [ ] [SCRIPT] **P2**. **SP-12(f) — shard-level isolation**. Orchestrator-level catch preserves isolation but
      per-adapter not enforced. Tighten.

Already GREEN (re-audit closed): SP-1/SP-2/SP-3 case-folding (cross_asset_group Phase 1D), SP-4 data-type-namespace note
(cross_asset_group Phase 1D), SP-6 KNOWN_COVERAGE_GAPS (folded to sports phantom-recon plan), SP-7 launch-dates
asymmetry (docstring fix shipped), SP-8 EMPTY_CONFIRMED_REASONS taxonomy (closed-set verified), SP-9 LINEUPS_PRE/POST
absent (clean), SP-11 sports-reference GCS paths (clean), SP-12(b) `ADAPTER_FETCH_FAILED` (ref adapters GREEN), SP-12(c)
typed empty reasons (GREEN at orchestrator/triggers).

## Anti-patterns + workspace-rule cross-references

- **Sports GCS path SSOT** (CLAUDE.md): use `unified_api_contracts.sports.candidate_parquet_paths` — NEVER hardcode
  `sports_reference/by_date/day=*/entity=*/...` paths.
- **Sports source coverage windows** (CLAUDE.md): `SOURCE_COVERAGE_START` + per-(source,data_type) overrides in
  `DATA_TYPE_COVERAGE_START`. Apply via `clip_dates_to_source_coverage`.
- **Honest absence**: paused leagues + pre-launch dates → `record_empty(empty_confirmed)`.
- **`available_at` per-row stamping rules**: kickoff−60min for lineups; event_time for fixture_events; match_end_time
  for post-match (sfi_progressive / understat / fixture_stats); kickoff−72h for early refs (per orchestrator paths).

## Deferred work after 2026-05-12 slot-5 session

Session shipped: instruments-service@af06124 (SFI report_time), UAC@1a831b0 (MatchStatus SSOT), plan flips for B.1
Phases 1-3+5, C.6 report_time, MatchStatus SSOT item.

| Phase / item                                        | Status as of 2026-05-12 | Successor / blocker                                                                     |
| --------------------------------------------------- | ----------------------- | --------------------------------------------------------------------------------------- |
| B.1 Phase 4: manifest flip + re-fetch VM            | `[ ]` NOT RUN           | Operational — needs VM launch + manifest migration; no code gap                         |
| C.4 Transfermarkt per-player flatten                | `[~]` partial-shipped   | UAC@3b29f7e — normalizer + schema done; migration/test deferred pending features-sports |
| C.6 Step 1: AF FIXTURES write-path `match_end_time` | `[~]` UAC-half-shipped  | UAC@0ba9e5b — schema column added; IS orchestrator write-path wiring still pending      |
| C.6 Step 2: SFI_PROGRESSIVE_STATS contract columns  | `[x]` shipped           | UAC@1848647 — added ft_timer + match_end_time columns; next: Step 3 (UTL resolver)      |
| C.6 Step 3: UTL `resolve_match_end_time()` cascade  | `[x]` shipped           | UTL@89c0ae15 — cascade resolver with NamedTuple return; next: Step 4 wiring             |
| C.6 assert_available_at_present wiring              | `[ ]` blocked           | Blocked on Step 3 UTL helper                                                            |
| C.7 Follow-up #1: STANDINGS flatten                 | `[~]` partial-shipped   | UAC@ac12d80 — normalizer + schema flatten (14→32 cols); migration deferred (VM op)      |
| C.7 Follow-up #3: MATCHES `team_a_*` → `home_*`     | `[x]` shipped           | UAC@4e23bd9 — FootyStats field mappings (12 home/away variants); migration deferred     |
| MatchStatus adapter migration                       | `[ ]` open (DEFERRED)   | Replace `{"FT","AET","PEN"}` ad-hoc sets with `AF_COMPLETED_CODES` across IS adapters   |
| Cross-source fixture status verifier                | `[ ]` open              | Uses MatchStatus SSOT (now shipped); no other blocker                                   |
| Codex doc `sports-fixtures-lifecycle.md`            | `[ ]` open              | Write after cross-source verifier design settles                                        |
| FIXTURES schema split (SCHEDULE + OUTCOMES)         | `[ ]` P0 open           | Large — coordinate with writegate strict-mode flip                                      |

**Next-agent entry point**: Pick any item from this table that has no blocker. Best candidates in priority order:

1. C.4 Transfermarkt per-player flatten (self-contained UAC normalizer + schema + migration + test)
2. C.6 Step 4: Wire resolve_match_end_time() cascade into available_at stamping (now unblocked by Step 3)
3. C.6 Step 1: AF FIXTURES write-path match_end_time (deferred wiring in IS orchestrator)

## Cross-references

- Master plan: [`master_to_live_defi_2026_05_23.md`](../active/master_to_live_defi_2026_05_23.md).
- Sibling asset_group umbrellas: `cefi_master_2026_05_07`, `defi_master_2026_05_07`, `tradfi_master_2026_05_07`,
  `predictions_master_2026_05_07`.
- Sports rename plan (KEPT ACTIVE — its own DAG):
  [`sports_data_available_at_rename_2026_05_07.md`](../archive/sports_data_available_at_rename_2026_05_07.md).
- Sports phantom-fixtures-recovery handover: `plans/ai/_sports_phantom_fixtures_recovery_handover_2026_05_06.md`.
- Honest-coverage % surface: `GET /api/data-status/honest-coverage` + `HonestCoverageCard` (deployment-ui). SSOT:
  [`codex/03-deployment/data-status-ui-surface.md`](../../codex/03-deployment/data-status-ui-surface.md). Phase 7F per
  `cross_asset_group_catalogue_audit_2026_05_10.md`.
- Canonical asset_group registry: `unified_api_contracts.canonical.crosscutting.asset_group_registry` (Phase 5C/5D).

## Folded plans (archived 2026-05-07)

- `features_sports_honest_coverage_2026_05_05.md` — full architecture spec; P1+ todos lifted above.
- `sports_fixtures_truthset_recovery_2026_05_06.md` — operator-triggered chain runner + audit.
- `sports_phantom_recon_and_failure_triage_2026_05_01.md` — operator decisions per source.
- `sports_predictions_e2e_2026_05_05.md` (sports half) — predictions ML training half went to `predictions_master`.
- `market_tick_data_to_100pct_2026_05_05.md` (sports slice) — full plan archived after split per asset_group.

## Folded into this umbrella (archived 2026-05-07)

- `sports_data_available_at_rename_2026_05_07.md` — full 4-phase DAG lifted into the "Sports `data_available_at` →
  `available_at` rename" section above. Phase 1 SHIPPED; Phases 2-4 pending.
