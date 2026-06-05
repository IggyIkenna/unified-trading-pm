---
name: sports_master
title: "Sports Master — asset_group umbrella"
type: epic
tier: L0
status: active
priority: P1
assigned_vm: vm-sports
parent: master_to_live_defi_2026_05_23
created: 2026-05-07
last_updated: 2026-05-21
locked_by: live-defi-rollout
locked_since: 2026-05-07
related_plans:
  - ../active/d2_uac_continuity_2026_05_20.md
  - ../archive/sports_gcs_partition_rekey_2026_05_23.plan.md
  - ../archive/2026_05/hard_schema_enforcement_2026_05_08.md
  - ../archive/2026_05/sports_scrapers_post_cutover_2026_06_01.md
  - ../archive/wave3x_residual_ssots_2026_05_08.plan.md
  - ../archive/2026_05/writegate_honest_coverage_endtoend_2026_05_06.md
  - ../active/trading_agent_service_architecture_unlock_2026_05_22.md
---

> **StrategyPnlStreamEvent**: archetypes in this plan emit StrategyPnlStreamEvent per UAC contract (see
> trading_agent_service_architecture_unlock plan Phase 1+2). Status: TODO post-cutover unless explicitly listed in this
> plan's May-23 scope.

> **🔴 P0 ABSORBED 2026-05-20 — mega-audit A3 findings for sports asset_group**: 25,652 `MISSING_EXPECTED` cells across
> ALL 11 bookmaker × data_type combos (BET365/BETFAIR/DRAFTKINGS/FANDUEL/ODDS_API/PINNACLE × odds_snapshot +
> odds_movement). The full window is missing — sports backfill has NOT run for any of these venues. Reassigned slot 7
> (was simulation_scenarios + defi_master P2-3) per `work_split_2026_05_19_ikenna.md` § "Slot 7 — REASSIGNED" +
> CLAUDE.md HARD RULE "Data Pipeline Correctness Is The Heartbeat". Includes A2 oracle gap remediation for sports
> off-season calendars per `audit/results/expected_coverage_calendar_decisions_2026_05_20.md`.
>
> **Scope MUST cover every bookmaker × data_type — no asset_group skipped, no deadline-driven cutbacks** (operator
> directive 2026-05-20). Closed-set deferral only via `BLOCKED-CREDENTIALS` / `BLOCKED-OPERATOR-DECISION` /
> `BLOCKED-UPSTREAM-OUTAGE` with operator ack.

> **🟡 STAMPING SCOPE FOLDED INTO UMBRELLA — `available_at_lookahead_bias_completion_2026_05_08`** (codified 2026-05-08)
>
> **Phase 1-2 stamping refs ONLY** (sports adapter `available_at` per-source cascade: lineups / fixture_events /
> injuries / pre-match odds / post-match xG+stats / weather forecast-issue) are folded into the available_at umbrella.
> Other sports_master scope (backfills, source coverage, league enumeration) remains owned here.
>
> Stamping owner:
> [`plans/active/available_at_lookahead_bias_completion_2026_05_08.md`](../active/available_at_lookahead_bias_completion_2026_05_08.md)

# Sports Master — asset_group umbrella

> **🟡 IN-FLIGHT REFACTOR — `available_at` adapter stamping** (coordinated by
> `available_at_lookahead_bias_completion_2026_05_08` Phase 1). Re-verify per-adapter `available_at` stamping wiring
> before adding new adapters to this plan.

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
- **Blocked by**: `manifest_migration_SUPERSEDED_2026_05_21:Stage 1` (sports `data_available_at` rename Phase 2 =
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
`predictions_master.md`).

## Sub-plans (referenced from this epic)

- **`plans/active/sports_retired_data_types_code_cleanup_2026_05_13.md`** — Retired-data-type cleanup (refactor class,
  ~1.2 cal-AI-days, deadline 2026-05-20). Removes stale references to data types that were retired in the manifest
  migration.
- **`plans/archive/api_football_phase_3b_3c_smoke_forward_poll_2026_05_13.md`** — Phase 3B/3C api-football smoke +
  forward-poll operational verification (P0, deadline 2026-05-14 EOD).
- **`plans/active/api_football_minimal_flattening_removal_2026_05_07.md`** — API-football payload flattening removal
  (near complete, 13/16 done).
- **`plans/active/wave2_polymarket_record_captured_from_counts_2026_05_09.md`** (Polymarket subset May-23) —
  bundled-shard SSOT migration; Kalshi + opinion.trade Phase 3 stays 2026-06-15.

**MVP scope SSOT** for sports backtest universe:
[`codex/09-strategy/mvp-universe-per-asset-group.md`](../../codex/09-strategy/mvp-universe-per-asset-group.md) — Top-5
EU football (EPL + LaLiga + Serie A + Bundesliga + Ligue 1) × 4 markets (1X2 / Over-Under 2.5 / BTTS / Asian Handicap).
MLS + other leagues post-cutover. Tier A archetype = `ml-settled` (post-fixture-settlement ML).

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
- UAC `BETTING_SPORTS_VENUES` manifest entries for the 14 scrapers.
- execution-service `adapters/scrapers/*.py` files (14 scrapers + `base_scraper.py` + `version_registry.py`) and
  `adapters/browser/us_books.py` `_make_us_book` factory.

Closes:

- `plans/active/issues/catalogue_audit_sports_2026_05_12.md` SP-5 (universe-contraction).
- `plans/active/issues/catalogue_audit_sports_2026_05_12.md` SP-13 (P0 phantom-import-path bug; resolved by 14-row
  deletion + 4-row rewrite).

**Successor plan (2026-05-14)**:
[`plans/archive/2026_05/sports_scrapers_post_cutover_2026_06_01.md`](../archive/2026_05/sports_scrapers_post_cutover_2026_06_01.md)
— `BLOCKED-OPERATOR-DECISION`; CREDENTIAL APPROVAL REQUEST pre-filled per CLAUDE.md "External Data Is Always Available"
HARD RULE. Status cross-linked to `master_to_live_defi_2026_05_23.md` § "Workspace-coordination + post-cutover successor
plans" (PM@`82d73711`). **ARCHIVED 2026-05-21 — all 4 items DEFERRED-POST-CUTOVER; activates post-2026-06-01 when
operator acks account provisioning.**

## Current state (2026-05-07)

- **honest-coverage architecture**: 16/49 = 33% done. Phase 1 UAC `UpstreamReq` + `in_coverage` started; Phase 2
  feature-compute `in_coverage` calls + NaN-state migration not yet shipped.
- **`data_available_at` rename**: Phase 1 shipped; Phase 2B GCS migration RUNNING (PID 95894, 200 workers, ~200/sec, ETA
  ~1h, 2026-05-22 05:36 UTC start); Phase 3 (4-repo source rename) SHIPPED 2026-05-22 — instruments-service@fc7b306 +
  UTL@94e43e8c + features-service@9847b350; Phase 4 verify pending (gated on migration completion).
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
[`manifest_migration_SUPERSEDED_2026_05_21.md`](./manifest_migration_SUPERSEDED_2026_05_21.md) for the sequencing DAG,
conflicts (esp. `batch_handler.py` overlap with writegate Phase 2.C), VM impact matrix, and operator pause-resume
guidance. Stage 1 Phase 3 features-sports `batch_handler.py` rename SHOULD ship in the SAME commit as writegate Phase
2.C `_ensure_timestamp` shim deletion (avoids two-commit churn on same lines).

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

#### Phase 2 — GCS migration (RE-RUN NEEDED 2026-05-23)

> **🟡 IN-FLIGHT — Re-running GCS migration on GCE VM 2026-05-23. Prior macOS run (2026-05-22) migrated the BASE bucket
> only (`instruments-store-sports-central-element-323112`) — PRD bucket was NOT migrated. Spot-check confirmed:
> base=DONE (available_at=True), prd=NOT DONE (data_available_at=True). Re-running against PRD bucket on GCE VM.**

- [x] [OPERATOR] P0. Sports VMs confirmed NOT running — no need to pause. Verified 2026-05-22.
- [x] ✅ [AGENT] P0. Launch GCS migration on GCE VM against PRD bucket (operator-authorized, re-run 2026-05-23):
      `scripts/migrate_sports_available_at_column.py --bucket gs://instruments-store-sports-prd-central-element-323112 --workers 32`.
      COMPLETED on `instr-backfill-sports` VM — 739594 files processed: A_renamed=527462, B_dedup=6, C_skip=0,
      D_skip=212126, E_cas_failed=0, F_read_failed=0. elapsed=16691.7s. dry_run=False. Completed 2026-05-23 20:35 UTC.
- [x] ✅ [AGENT] P0. Verify completion: spot-check 5 parquets across years 2019-2025 in PRD bucket —
      `available_at=True data_available_at=False` for ALL 5 dates (2019, 2021, 2023, 2024, 2025). Spot-check 2026-05-23.
- [ ] [OPERATOR] P0. DO NOT resume FWD/BACKFILL VMs until Phase 3 atomic source rename ships AND Phase 2 migration
      verified. Phase 3 is SHIPPED (2026-05-22). Waiting on Phase 2 migration completion (prd bucket).

#### Phase 3 — Atomic 4-repo source rename (SHIPPED 2026-05-22)

- [x] [SCRIPT] P0. UAC: no changes needed — UAC had no data_available_at references. [AUDIT 2026-05-07: DONE — UAC
      clean, verified 2026-05-22]
- [x] [SCRIPT] P0. UTL: rename `DEFAULT_AS_OF_COLUMNS` + `point_in_time.py` comment + tests (1 commit, push). —
      unified-trading-library@94e43e8c (2026-05-22)
- [x] [SCRIPT] P0. instruments-service: rename 10 orchestrator callsites + 2 scripts + tests (1 commit, push). —
      instruments-service@fc7b306 (2026-05-22)
- [x] [SCRIPT] P0. features-sports-service: update comment reference `_available_at_helpers.py`. —
      features-service@9847b350 (2026-05-22)
- [x] [QG] P0. Run `quality-gates.sh` on all repos; pre-existing failures (seed_writer.py, UAC Polygon import) not from
      our changes. Tests in test_instruments_write_gate + test_point_in_time: 56 PASSED. [2026-05-22]
- [x] [QG] P0. Workspace-wide ripgrep for stragglers — `rg -n 'data_available_at' --type py --glob '!.venv*'` returns
      ZERO non-test non-migration results across instruments-service/UTL/UAC/features-service. [2026-05-22]
- [x] [SKIP] `tests/unit/test_availability_stamping.py` in UTL — was clean (not dirty); skipped per task instructions.

#### Phase 4 — Writegate Phase 2.C unblock + verify (PENDING — migration must complete first)

- [x] ✅ [SCRIPT] P0. Smoke-run sports backfill; confirm `record_captured` no longer raises `LookaheadBiasError`. Run:
      instruments_service SPORTS FOOTYSTATS 2024-11-15 --force — 4 prediction rows + 4 odds rows written, 0 errors, NO
      LookaheadBiasError. Phase 2B migration unblocked this gate. 2026-05-24.
- [x] [VERIFY] P0. Update writegate plan Phase 2.C "prerequisites" section to mark sports rename as shipped. — sports
      rename Phase 3+4 shipped (2026-05-22) — instruments-service@fc7b306, UTL@94e43e8c
- [x] ✅ [VERIFY] P0. Update master plan Q&A 14 to mark HIGH-2 as SHIPPED + record commit SHAs. Q&A 14 updated: HIGH-2
      fully shipped; all 4 phases complete. 2026-05-24.
- [x] ✅ [OPERATOR] P0. Resume forward-poll + backfill VMs. sports-scheduler-20260525-072005 launched 2026-05-25 (daemon
      e2-small asia-northeast1-c, poll=300s). Sports rename fully shipped (fc7b306/94e43e8c); Phase 2B GCS migration
      done (739,594 files); Phase 4 smoke verified 2026-05-24. Backfill VMs resume on next scheduler tick.

> **🔎 SPORTS-CANON ALIGNMENT (2026-06-01):** The sports-scheduler was **subsequently STOPPED again 2026-06-01** as part
> of the pre-migration fleet drain in `bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md` Phase 3. Relaunch
> is GATED on the sports L3 canonicalisation plan completing (C-GREEN) and the legacy tick + instruments-store buckets
> being decommissioned. Do NOT relaunch the sports-scheduler before those gates. SSOT for relaunch prerequisites:
> `bucket_name_ssot…` Phase 4 `[SCRIPT] P0 GATED` item.

### Sports honest-coverage architecture (`features_sports_honest_coverage`)

- [x] [AGENT] P1. UAC `unified_api_contracts.sports`: add `UpstreamReq` dataclass + `FEATURE_UPSTREAM_REQUIREMENTS`
      dict + `in_coverage(source, entity, league, date) -> bool` helper. [AUDIT 2026-05-07: DONE — UAC@3137271
      (UpstreamReq + FEATURE_UPSTREAM_REQUIREMENTS + in_coverage Phase 1)]
- [x] ✅ [AGENT] P1. Unit tests for `in_coverage` — coverage of each clip rule; pre-launch dates + paused leagues.
      [AUDIT 2026-05-07: FRESH — actionable; UAC@3137271 commit message says Phase 1 implies tests; verify test file
      exists] UAC@31372710 — 4 test classes (TestUpstreamReq, TestFeatureUpstreamRequirements, TestInCoverage,
      TestInCoverageDt) covering pre-launch dates, league coverage clips, SFI DATA_TYPE_COVERAGE_START override, derived
      source bypass. Verified 2026-05-22.
- [x] ✅ [AGENT] P2. features-sports-service: feature compute path calls `in_coverage` per upstream before running each
      calculator. Implemented via `_gate_then_run` + `_run_simple_gated_calc` in `derived_new_calculators.py` — calls
      `check_calculator_coverage` (which calls `in_coverage` per upstream req) before each calculator. Confirmed running
      in all 11 Phase-4 calculators — features-service@a9d0c32c.
- [x] ✅ [AGENT] P2. NaN handling — distinguish NaN-by-design (OUT_OF_COVERAGE → `out_of_coverage` status, parquet
      written with NaN) from NaN-from-missing-upstream (UPSTREAM_MISSING → `upstream_missing` status, calculator
      skipped) per `codex/02-data/honest-absence-downstream-handling.md`. quality_tracker records the distinction;
      batch_handler uses `record_empty(SOURCE_RETURNED_ZERO)` for empty derived features groups. Tests in
      `tests/sports/unit/test_run_new_calculators_coverage_gate.py` confirm both paths — features-service@a9d0c32c.
- [x] ✅ [AGENT] P2. Backwards-compat — features computed before this change have manifest rows without coverage info;
      UTL `classify_legacy_empty_row` helper (Tier 3D.2) handles reader-side fallback for rows without coverage info.
      Reader side tolerates gracefully — no one-time migration needed (per honest-absence doc § "Per-reason-group →
      consumer policy" reader fallback). UTL@94e43e8c.
- [x] ✅ [AGENT] P3. Add `axis: per_feature_per_league_per_fixture_date` to `_sports_honest_coverage` in data-status
      reconciler. Per-feature-group denominator = (clipped fixture dates) × (in-coverage leagues). — **VERIFIED ALREADY
      SATISFIED 2026-06-03 (deployment-api@96e7ac7)**: the axis is declared in `SportsAxis` + assigned to every
      calculator in `FEATURES_SPORTS_PER_CALC_META`, and `_sports_honest_coverage` already computes `expected_shards` as
      the sum across leagues of `_features_sports_expected_dates_for_calculator(...)` (fixture-dates ×
      in-coverage-leagues, per calculator = per feature). Added 3 verification tests
      (`tests/unit/test_features_sports_per_feature_axis.py`); no production change needed.

### Fixture truthset recovery (`sports_fixtures_truthset_recovery`)

- [x] [HUMAN] P0. Operator triggers Phase 3 chain runner per the recovery script.
- [x] [AGENT] P0. Monitor + rescan + audit. Verify detached chain orchestrator completes; manifest reflects.
- [x] [AGENT] P0. Architecture: `--recovery-fixture-ids` CLI flag (instruments-service `cbb50fa` / `e900769` /
      `7ce509e`), 4 non-api_football launchers plumbed (deployment-service `7453741`), throttle 0.1s → 0.067s for full
      Mega tier (instruments-service `070f7e7`), UTL cache split (`bf41175c`).
- [x] ✅ [AGENT] P0. Monitor 5 parallel recovery VMs to STOPPED: all 5 VMs confirmed DELETED/STOPPED (2026-05-23).
      `gcloud compute instances list` returned empty for all af-backfill-_, us-backfill-_, fs-backfill-_,
      weather-backfill-_, sfi-backfill-\* prefixes in asia-northeast1-c. Auto-shutdown confirmed.
- [x] ✅ [AGENT] **P0. POST-RECOVERY PHANTOM DEDUP — COMPLETED 2026-05-23.** All 5 recovery VMs confirmed STOPPED.
      Dry-run: 79 shards, 366,799 phantom rows to drop (FIXTURES 105,053 / WEATHER 127,835 / PREDICTIONS 33,727 / ODDS
      33,438 / PLAYER_STATS 25,088 / FIXTURE_LINEUPS 6,964 / FIXTURE_EVENTS 6,928 / FIXTURE_STATS 6,528 / INJURIES 9,783
      / XG 10,818 / MATCHES 66 / SFI_PROGRESSIVE_STATS 571). Apply ran (IS@local dedup_phantom_after_recovery.py).
      Backup parquets written per shard. 2026-05-23.

- [x] ✅ [AGENT] P0. Query deployment-api data-status: SPORTS post-dedup state (2026-05-23): 2,685,279 canonical rows.
      captured=21.8% (584,076), empty_confirmed=74.8% (2,009,134), attempted_failed=3.2% (85,200), null=0.3% (6,869).
      Targets (≥50% attempted, ≥45% captured) NOT yet met — blocked on forward-poll VMs resuming + additional backfill.
      Per data_type: LEAGUES+TEAMS+VENUES at 99-100% captured; FIXTURES 19%; FIXTURE_STATS 9%; FIXTURE_EVENTS 8%;
      FIXTURE_LINEUPS 8%; PLAYER_STATS 5%; INJURIES 4%; STANDINGS 34%; SFI_STANDINGS 0% (known issue). Canonical index
      last updated 2026-05-23 19:52 UTC (post-dedup run). 2026-05-23.
- [x] ✅ [AGENT] P0. Spot-check 3 dates × 5 entities in BASE bucket (2026-05-23): 9 parquets checked across 2021-10-23,
      2022-03-12, 2023-08-15. All have `available_at=True, data_available_at=False` (migration clean). INJURIES empty
      parquets (0 rows, pre-schema) exist but are pre-migration artifacts. PLAYER_STATS/FIXTURE_STATS/FIXTURE_LINEUPS
      across EPL/BUNDESLIGA/UCL all ✅. 2026-05-23.
- [x] ✅ [AGENT] P0. Re-smoke after writer fix `f36651c` lands on forward-poll VM. — instruments-service@76be157d.
      Verified f36651c (zero-fixture record_empty) is deployed on forward-poll VMs. Also found + fixed a second bug:
      `kind="instruments"` → `kind="instruments-store"` in both `instruments_handler.py` and
      `sports_fixtures_daily_repoll.py` — caused ManifestWriter final flush to silently fail on all 4 asset groups
      (SPORTS/CEFI/DEFI/TRADFI) every run. Forward-poll run footystats-fwd-20260523-230012 confirmed rc=0 with fix
      deployed. 2026-05-23.
- [x] ✅ [AGENT] P0. Apply per-league empty-loop pattern (Bug 6 fix) to AF enrichment. [AUDIT 2026-05-07: FRESH —
      actionable] **ALREADY IMPLEMENTED**: `_af_emit_empty_gaps_for_entity()` at orchestrator.py:3842 is called for
      STANDINGS (line 4004), INJURIES (lines 4081/4106), and all per-fixture entities FIXTURE_STATS/EVENTS/LINEUPS/
      PLAYER_STATS (lines 4526/4561) via the entity loop. Per-league `record_empty` with typed reason fired correctly.
      Backfill-flip 2026-05-23 (instruments-service@fa0b6f04).
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
- [x] ✅ [HUMAN] P0. deployment-api `_sports_honest_coverage` MR review + merge. **[DONE — verified 2026-06-05 (slot-4
      e2e audit dim ⑦): merged + live in `data_status_service.py` (the primary sports coverage path, denominator from
      the UAC fixtures/leagues universe).]**

### Sports half of `sports_predictions_e2e` — 288M ODDS_API row migration

- [x] ✅ [SCRIPT] P0. Inventory existing 288M legacy `venue=ODDS_API` rows: probe parquet to confirm columns. [AUDIT
      2026-05-07: FRESH — actionable] **COMPLETED 2026-05-23**: Rows live in
      `market-data-tick-sports-central-element-323112` under
      `processed/by_date/day={day}/data_type=odds_horizon_bucket/league_id={league}/timeframe={T-Xh}/bucketed.parquet`.
      144,080 manifest rows; ODDS_API = dominant venue (144,080). 31 columns confirmed: bookmaker_key, fixture_id,
      sport_key, home/away/draw odds, asian_handicap, over_under, btts, horizon_idx, horizon_name, kickoff_utc,
      minutes_to_kickoff, bm_minutes_to_kickoff, staleness_seconds, fetch_utc, source. Full schema = MTDS
      `odds_horizon_bucket` contract. Data already in canonical path — NOT a raw legacy dump, but a properly bucketed
      MDPS output. The "288M rows" refers to row-level bookmaker ticks, not manifest rows. **Finding**: No migration
      needed — data is already in canonical MTDS format with 8 horizon buckets. The plan's "migrate from venue=ODDS_API"
      referred to the manifest re-key; manifest already has correct key shape (date, venue, data_type, league_id,
      timeframe). Next step: run MDPS `SportsBucketAssignmentAdapter` smoke pass.
- [x] ✅ [SCRIPT] P0. Migrate rows to canonical sports manifest shape (re-key from `venue=ODDS_API` to canonical
      `(asset_group=sports, source=odds_api, data_type, league_id, day)`). **COMPLETED 2026-05-23**: Migration already
      ran as part of bucket SSOT canonicalisation (2026-04). Raw data is at
      `raw_tick_data/by_date/day={D}/asset_group=sports/data_source=ODDS_API/` (2020-2025) and
      `raw_tick_data/by_date/day={D}/pipeline_mode=batch_api_football/asset_group=sports/data_source=ODDS_API/` (2026+).
      Manifest key shape is already canonical. Fixed `reprocess_sports_odds.py` bug where `_CANONICAL_PREFIX_TEMPLATE`
      used stale `category=sports` instead of `asset_group=sports` — MDPS@34d7172.
- [x] ✅ [SCRIPT] P0. Run MDPS `SportsBucketAssignmentAdapter` on migrated rows for 1 recent week (smoke pass) — all 8
      horizons (T-24h / T-12h / T-6h / T-4h / T-2h / T-1h / T-10m / T-0). **COMPLETED 2026-05-23**: live run verified
      2026-04-14 → 2352 raw rows → 501 bucketed rows (8 horizons, 22 bookmakers, 16 league×horizon shards). Manifest
      updated (335,105+17 entries; 1 day-level + 16 league×horizon shards). Fixed 2 bugs in script: stale
      `category=sports` path prefix (MDPS@34d7172) + `record_empty()` missing typed reason (MDPS@7f7c1ad).
- [x] ✅ [ANALYSIS] P0. Bucket-coverage check: how many fixtures have ≥1 row per (fixture, bookmaker, bucket). —
      2024-11-01 sample: 22 fixtures × 22 bookmakers × 8 timeframes (T-0/T-10m/T-1h/T-2h/T-4h/T-6h/T-12h/T-24h); 77.8%
      of (fixture,bookmaker) combos have all 7 non-T-0 timeframes; 99.8% have ≥5. Processed bucket: 1813/1837 raw days
      bucketed (98.7%). Only 24 days missing: 20× Sep-Oct 2022 + 3 isolated (2023-06-25, 2024-05-11, 2025-02-01). All
      existing bucketed dates have 100% timeframe coverage. Analysis 2026-05-23.
- [x] ✅ [SCRIPT] P0. Backfill MDPS bucketing across full historical window (5+ years) on migrated rows. — MDPS@6c90451.
      Ran `reprocess_sports_odds.py` (2022-09-08→2022-10-01, workers=4): all 24 "missing" days reported
      `skipped(manifest)` — they already have `empty_confirmed` entries (Sep-Oct 2022 = international break, no club
      matches). 3 isolated dates (2023-06-25, 2024-05-11, 2025-02-01) also confirmed `empty_confirmed`. Net result:
      1813/1837 bucketed (98.7%) + 24 honest-empty. Backfill complete 2026-05-23. Added `source=ODDS_API` path template
      for pre-2022 data (MDPS@6c90451).
- [ ] [SCRIPT] P1. Run features-sports-service (FSS) on bucketed dataset — verify odds features populate (velocity, CLV,
      steam, late-money). [AUDIT 2026-05-07: BLOCKED-ON sports_master:full bucket backfill]
- [ ] [SCRIPT] P1. Verify feature matrix is ML-ready (one row per fixture × bucket, NaN only where honest-absence).
      [AUDIT 2026-05-07: BLOCKED-ON sports_master:FSS run]
- [ ] [GATE] P0. Block predictions Group E until FSS produces ≥95% non-NULL features for trained universe at the buckets
      predictions ML targets. [AUDIT 2026-05-07: ACTIVE GATE — explicitly BLOCKS predictions_master:ML half]

### Sports MTDS slice (`market_tick_data_to_100pct` — sports)

- [x] ✅ [AGENT] P1. Per-source completion % (2026-05-23 post-dedup, canonical manifest 2.68M rows): api_football=22.9%
      cap (441K/1.93M); footystats=22.5% (73K/324K); odds_api=26.5% (28K/105K); open_meteo=12.0% (14K/115K); sfi=24.5%
      (23K/92K); transfermarkt=0% (75K all empty_confirmed); understat=21.4% (5K/25K). TRANSFERMARKT_LEAGUES 100% empty
      — needs P0 triage (no forward-poll VM running). Surface to deployment-ui: **DEFERRED** — blocked on forward-poll
      VM resume + UI code change (post-migration gate).
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

- [x] [SCRIPT] P1. **FOOTYSTATS_SEASON_IDS drift-detection automation.** ✅ Extend
      `unified-api-contracts/.github/workflows/weekly-validation.yml` with a job that:
  - [x] Calls FootyStats `/league-list` once per week — GHA `check-footystats-season-drift` job in weekly-validation.yml
  - [x] Diffs the response's per-league season IDs against UAC's hardcoded `FOOTYSTATS_SEASON_IDS` dict —
        `check_footystats_season_drift.check_drift()`
  - [x] If new league IDs detected: creates GitHub issue with exact code changes needed (PR title format
        `chore(provider-league-ids): footystats season refresh — {YYYY-MM-DD}` used as issue title)
  - [ ] **DEFERRED** Same shape for `TRANSFERMARKT_IDS` — verify via spot-check; Transfermarkt IDs are numeric
        competition IDs (not season-specific) so likely static; investigate before implementing
  - [x] ~50-line Python helper `unified-api-contracts/scripts/check_footystats_season_drift.py` — 150 lines; also emits
        `footystats_drift_report.md` as PR-creation payload consumed by GHA step
  - [x] Test: 20 mock-based tests in `tests/test_footystats_season_drift.py` — covers no-drift, rollover drift, unknown
        seasons, missing from API, name lookup, historical_additions
  - **Bonus fix**: added `14923: AUSTRIAN_BUNDESLIGA`, `15163: GREEK_SUPER_LEAGUE` to
    `FOOTYSTATS_HISTORICAL_SEASON_IDS`; fixed `15066: LA_LIGA_2 → SEGUNDA_DIVISION`
  - Evidence: UAC@bcbf703d — uac@bcbf703d

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
- [x] ✅ [SCRIPT] P0. Migration shape: flip every existing manifest row for the 4 data_types →
      `record_failed(reason=INCOMPLETE_PAYLOAD_PRE_FLATTENING, attempted_at=now)`, delete the thin parquets, then
      re-fetch via a dedicated VM (`af-backfill-flatten-{ts}`). The 4 data_types use ISOLATED endpoints
      (`/fixtures/statistics`, `/fixtures/events`, `/fixtures/lineups`, `/injuries`) — separate from `/fixtures` itself
      — so quota cost is bounded to the 4-endpoint × historical-fixture-set product, NOT a full FIXTURES re-fetch.
      **SHIPPED 2026-05-23**: `INCOMPLETE_PAYLOAD_PRE_FLATTENING` added to `RecordFailedReason` (UAC@84c8c49d);
      migration script `flip_b1_thin_payload_to_reattempt.py` ships (instruments-service@b0a1d284). **Run after sports
      PRD available_at migration completes** (in progress): `--dry-run` first, then `--apply     --delete-parquets` on
      both base + PRD buckets. Then launch `af-backfill-flatten-{ts}` VM. [AUDIT 2026-05-07: FRESH — actionable;
      coordinate with manifest_migration_SUPERSEDED_2026_05_21:Stage 3]
- [x] [TEST] P0. Normalizer output shape tests. (UAC@c76e6d0 — 13 unit tests in
      `tests/unit/test_normalize_api_football.py` covering full payload shape, partial null-fill, unknown-stat-type
      skip, no-coach lineup, missing-fixture injury, malformed-input returns. `test_sports_contracts.py` parametrized
      cases verify schema registration for all 4 data_types. Note: `test_cassette_schema_parity.py` was NOT extended —
      the per-normalizer unit tests satisfy the same invariant.)
- [ ] [VERIFY] P0. After re-fetch VM completes for one league × one season, open deployment-ui schema modal for each of
      the 4 data_types and confirm full per-row column set (xG, shots-on-target, possession, goal-events with minute,
      starting-XI per slot, etc.). [AUDIT 2026-05-07: BLOCKED-ON above flatten ship + re-fetch VM]

**Operational verification owner**: `plans/archive/api_football_phase_3b_3c_smoke_forward_poll_2026_05_13.md` (P0,
deadline 2026-05-14 EOD) — folded into this epic 2026-05-13 (was orphan per inventory dashboard); covers Phase 3.B
live-API smoke (✅ PASSED 2026-05-13) + Phase 3.C EPL forward-poll VM verification.

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

- [x] ✅ [SCRIPT] P0. **Step 1**: api_football FIXTURES write-time computation. When `status_short ∈ {FT, AET, PEN}`,
      compute `match_end_time ≈ kickoff + periods.second.duration + et.duration +     injury_time` from the API
      response. Add `match_end_time` column to UAC FIXTURES contract. [AUDIT 2026-05-07: FRESH — actionable] **PARTIAL
      2026-05-12 slot 5 (instruments-service@9bffca2)**: UAC field `match_end_time: datetime | None` added to
      `CanonicalFixture`; `detect_match_end_time()` helper shipped in SFI adapter. **UAC HALF SHIPPED 2026-05-13**:
      UAC@0ba9e5b — `match_end_time` column added to SPORTS_FIXTURES schema (parquet-level). **COMPLETED 2026-05-23**:
      `detect_match_end_time()` wired into instruments-service SFI progressive-stats write path at
      orchestrator.py:6331-6349 — `match_end_time` + `report_time` populated per-match (instruments-service@af06124,
      backfill-flip 2026-05-23).
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
      resolve_match_end_time() with NamedTuple return + cascade logic. Tests: UTL@520cbb2a (8 unit tests).
- [x] ✅ [SCRIPT] P0. Wire `resolve_match_end_time()` into per-source `available_at` stamping for post-match data_types
      (FIXTURE_STATS / SFI_PROGRESSIVE_STATS / understat XG / fixture_player_stats) per CLAUDE.md "available_at per-row,
      write-time, equal-to-live-pipeline-arrival" rule. [AUDIT 2026-05-07: FRESH — actionable; coordinate with
      sports_master:Phase 3 rename] **COMPLETED 2026-05-23**: All four data types fixed — wall-clock override removed;
      SFI uses report_time (instruments-service@8b8db4ad); XG uses kickoff+24h (instruments-service@04abbd63);
      FIXTURE_STATS/EVENTS/LINEUPS/PLAYER_STATS use date+17h KO+2h approximation already set in code
      (instruments-service@66a887f1).
- [x] ✅ [SCRIPT] P0. **DEFERRED from slot 5 Phase 2.D (2026-05-12)**: Wire `assert_available_at_present` into the
      instruments-service SFI progressive-stats / FIXTURES write path (spawn prompt step 8). **ALREADY WIRED
      2026-05-23**: `assert_available_at_present(data)` is called at orchestrator.py:414 inside `_gated_sink_write`,
      which is used by all sports write paths (SFI progressive stats, FIXTURES, per-fixture entities, understat XG). No
      additional wiring needed — verified by grep. Backfill-flip 2026-05-23.
- [x] [SCRIPT] P0. **DEFERRED from slot 5 Phase 2.D (2026-05-12)**: Derive
      `report_time = match_end_time + SFI_DATA_LAG_P95_SECONDS` in instruments-service SFI progressive-stats write path.
      (instruments-service@af06124 — `match_end_time` + `report_time` columns added to SFI progressive stats rows in
      orchestrator per-match loop, using `detect_match_end_time()` + `SFI_DATA_LAG_P95_SECONDS=300`.)
- [x] ✅ [TEST] P0. Unit tests covering each branch of the cascade + the `kickoff + 120min` fallback shape. [AUDIT
      2026-05-07: FRESH — actionable] **COMPLETED 2026-05-23**: 6 new C.6 tests added to `test_phase2d_match_timing.py`
      (14 tests total): report_time→available_at, None report_time→wall-clock, mixed rows, detect_match_end_time+lag
      derivation, XG kickoff+24h preserved, XG None-kickoff fallback — instruments-service@fa0b6f04. All 14 PASSED.
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
- [x] [SCRIPT] P1. **Follow-up #2 — XG per-shot flatten (BIG WIN).** ✅ PARTIAL — UAC `SPORTS_XG_SHOTS` schema + UAC
      path/coverage/source registries (UAC@ab62291f). ✅ (a) instruments-service `_run_understat_shots_date()` write
      path shipped (IS@a21401ea). ✅ (b) `get_match_shots(match_id)` + `get_match_ids_for_date(date)` shipped
      (IS@a21401ea). ✅ (c) cassette parity test for `normalize_understat_shot` shipped (UAC@d9ab06d9). ✅ (d) backfill
      VM launched: `us-backfill-20260523-211154` (2019-01-01..2026-05-23, asia-northeast1-c). ✅ (e) features-sports
      consumers updated to read per-shot dimensions — shot_quality_calculator.py (22 cols: shot_count_avg,
      xg_per_shot_avg, open/set_piece/penalty/counter_attack xG pcts, head/left/right foot pcts, conversion_rate) +
      gcs_reader read_historical_xg_shots(90d) + coverage_gate XG_SHOTS wiring + \_run_simple_gated_calc integration —
      features-service@a9d0c32c, UAC@967e2565.
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

- [x] ✅ [SCRIPT] P0. **UAC schema DONE additively (uac@c4058c68, 2026-06-05) — writer-emit + entity-split + migration
      GATED until AFTER canonicalisation (single-walk).** Added CanonicalFixtureSchedule + CanonicalFixtureOutcomes +
      MatchResult + FIXTURES_SCHEDULE/FIXTURES_OUTCOMES constants + MatchLifecycle ALONGSIDE the live
      CanonicalFixture/FIXTURES (NOT a rename/replace yet). The entity-folder split + `migrate_fixtures_split.py` walk +
      writegate same-day flip are the gated walk-after steps. ~~split `CanonicalFixture` into `CanonicalFixtureSchedule`
      (kickoff_time, league_id, home_team_id,~~ away_team_id, venue, status, scheduled fields) +
      `CanonicalFixtureOutcomes` (home_score_regulation, away_score_regulation, home_score_after_extra_time,
      away_score_after_extra_time, home_score_after_penalty_shootout, away_score_after_penalty_shootout,
      home_penalty_shootout_score, away_penalty_shootout_score, went_to_extra_time, went_to_penalties, match_result,
      match_end_time). New entity_types `FIXTURES_SCHEDULE` + `FIXTURES_OUTCOMES` replacing the single `FIXTURES`. Both
      written to same `sports_reference/by_date/day=<day>/...` path with separate `entity=fixtures_schedule` /
      `entity=fixtures_outcomes` sub-folders. Per-row `available_at` differs: SCHEDULE = `announced_at` (per-league
      empirical floor — see workstream below); OUTCOMES = `match_end_time` (from C.6 cascade already shipped).
- [x] ✅ [SCRIPT] P0. **DONE (utl@b2f60f31, 2026-06-05): `read_fixtures_joined(day, league_id)` returns one row/fixture
      with schedule+outcome cols + `outcomes_available_at`; `read_fixtures_outcomes_pit_safe` wraps it with the existing
      PointInTimeEnforcer/LookaheadBiasError (per-row fire when compute-ts < outcomes_available_at + outcome cols read).
      Reads current entity=fixtures (TODO(walk-after) for the two-entity read post-split).** ~~UTL reader-side join
      helper~~ `unified_trading_library.fixtures.read_fixtures_joined(day, league_id) ->     pd.DataFrame` returns
      single fixture row with both schedule + outcome columns + a `outcomes_available_at` column. Consumers see one
      DataFrame; LookaheadBiasError fires per-row when feature compute timestamp < outcomes_available_at AND any outcome
      column is read.
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
- [x] ✅ [SCRIPT] P0. **PURE VERIFIER + CONTRACTS DONE; orchestrator WIRING gated (walk-after) (2026-06-05)**: pure
      `unified_trading_library.fixtures.verify_fixture_status` (utl@068c919a, 11 tests, conservative — overrides only on
      strong cross-source match-data evidence) + UAC contracts (uac@4e9eebb3: `MatchStatus.POSTPONED_RESCHEDULED`,
      `FIXTURES_STATUS_DISCREPANCY` event, `REFERENCE_STATUS_DISCREPANCY` reason, signal schema). The IS orchestrator
      commit-time WIRING (calling the verifier + emitting the event + record_failed/record_captured) stays GATED —
      heartbeat-safe, lands with the writer-emit/entity-split walk-after step. ~~Cross-source verifier integration at
      instruments-service orchestrator commit-time. When api_football~~ reports `CANCELLED` BUT footystats / SFI /
      understat reports the fixture has match data (lineups + stats + events): emit `FIXTURES_STATUS_DISCREPANCY` event
      (NEW UAC LifecycleEventType) + flip api_football status to `POSTPONED_RESCHEDULED` (or whichever the cross-source
      ground truth indicates) at write-time + stamp `status_provenance: "cross_source_override"` column. Manifest
      `record_failed(reason=REFERENCE_STATUS_DISCREPANCY)` for the originally-mis-flagged row + `record_captured` for
      the corrected row.
- [x] ✅ [AGENT] P1. Empirical investigation — postponed-fixture identity. Pull 30 confirmed-postponed fixtures from
      api_football across 2024-2026; confirm for each whether: (a) same `fixture_id` retained at the new kickoff, OR (b)
      new `fixture_id` issued at reschedule, OR (c) original `fixture_id` deleted + replaced. Document the
      empirically-correct model in `codex/02-data/sports-fixtures-lifecycle.md` (NEW codex doc; see codex todo below).
      **COMPLETED 2026-05-23**: Case (a) confirmed — 0 PST fixtures found across
      EPL/SerieA/Bundesliga/Ligue1/Championship/ LaLiga/Eredivisie for seasons 2023-2025; PST is transient, reverts to
      NS on reschedule, same fixture_id retained. Codex doc updated with full evidence table + operational implications
      — PM@(see commit).
- [x] [AGENT] P0. NEW codex doc `unified-trading-pm/codex/02-data/sports-fixtures-lifecycle.md` capturing: status enum
      taxonomy, postponed-fixture identity model (case a/b/c), cross-source verifier rules, FIXTURES_STATUS_DISCREPANCY
      event semantics. SSOT for both this section + Issue-1 schema split. **COMPLETED 2026-05-13**: PM@1a86b6ab —
      shipped sports-fixtures-lifecycle.md with 8-state lifecycle + per-state available_at table + cross-source verifier
      design (responsibilities + architecture diagram + consensus decision logic + adapter integration via MatchStatus
      SSOT). Postponed-fixture identity model (cases a/b/c) deferred pending empirical investigation (sibling todo).

### Match HT/ET/PEN timestamps + score-distinction columns + pre-features extractor (Q5 + Q6 + Q7 from `instruments_lifecycle_and_fixtures_endtime_cascade_2026_05_08`)

Source issue archived. Q1+Q2 (futures + options expiry) are migrated to `tradfi_master` (Batch D); Q4 is already covered
by the C.6 match_end_time cascade above; Q3 (predictions) is gold standard, no work. Q5+Q6+Q7 land here in sports_master
Phase 3 (per operator decision 2026-05-08: tradfi_master owns Q1+Q2; sports_master owns Q4-Q7; operator chose Option (a)
for Q7 — UTL helper at instruments-service write-time, NOT a separate pre-features extractor service).

- [x] ✅ [SCRIPT] P0. **UAC Q5 fields DONE (uac@c4058c68): CanonicalFixtureSchedule carries all HT/ET/PEN phase
      timestamps (nullable, tz-aware).** Populate-from-api-football at write-time is the IS Phase-3 piece (pending).
      ~~extension (Q5): `halftime_start_time`, `halftime_end_time`,~~ `extra_time_first_half_start_time`,
      `extra_time_first_half_end_time`, `extra_time_second_half_start_time`, `extra_time_second_half_end_time`,
      `penalty_shootout_start_time`, `penalty_shootout_end_time`, `whistle_full_time_at`. All nullable (regular matches
      don't have ET/penalties). Populate from api_football `periods.first` / `periods.second` / `et` /
      `score.penalty.played_at` at write-time.
- [x] ✅ [SCRIPT] P0. **UAC Q6 fields DONE (uac@c4058c68): CanonicalFixtureOutcomes carries regulation/ET/PEN
      score-distinction + went_to_extra_time/went_to_penalties + match_result (pen-shootout never collapsed).**
      Populate-from-api-football at write-time is the IS Phase-3 piece (pending). ~~score-distinction columns (Q6):
      `home_score_regulation`,~~ `home_score_after_extra_time`, `home_score_after_penalty_shootout`,
      `home_penalty_shootout_score`, `away_score_regulation`, `away_score_after_extra_time`,
      `away_score_after_penalty_shootout`, `away_penalty_shootout_score`, `went_to_extra_time` (bool),
      `went_to_penalties` (bool), `match_result` (`home_win` / `away_win` / `draw_regulation` / `home_win_after_et` /
      `away_win_after_et` / `home_win_after_pens` / `away_win_after_pens` — closed StrEnum). Populate from api_football
      `score.fulltime` / `score.extratime` / `score.penalty`. NEVER collapse pen-shootout score into single field.
- [x] ✅ [SCRIPT] P0. **DONE (utl@b2f60f31 helper + is@9de5ac87 write-time call, 2026-06-05):
      `extract_match_lifecycle(af_response) -> MatchLifecycle` (parses parsed AF dict, no HTTP) + IS FIXTURES write
      populates the Q5/Q6 columns additively on entity=fixtures rows.** ~~UTL helper
      `unified_trading_library.fixtures.extract_match_lifecycle(fixture_id) -> MatchLifecycle`~~ at instruments-service
      write-time (Q7 — operator chose Option (a) UTL helper, NOT separate service). Reads api_football response, returns
      typed dataclass with all HT/ET/PEN timestamps + score-distinction columns. Called by FIXTURES adapter at
      orchestrator commit. Avoids the circular dependency the issue's pre-features-extractor option (b) introduced
      (features-sports would need to wait for instruments-service regardless).
- [ ] [SCRIPT] P1. Deferred follow-up TODO: if features-sports HT-feature work grows past 3 calculators, extract
      `match_lifecycle_extractor` into a dedicated pre-features service stage (Q7 option (b)). Not scoped now per
      operator direction.
- [x] ✅ [TEST] P0. **DONE (utl@b2f60f31 + is@9de5ac87, 2026-06-05): regulation / ET-only / ET+PEN / abandoned(NULL
      whistle) / missing-data-fallback covered (16 UTL + IS column tests).** ~~Unit tests for `extract_match_lifecycle`
      covering: regulation match (no ET/PEN), ET-only match, full~~ ET+PEN match, abandoned match (whistle_full_time_at
      NULL), missing-data fallback (low-confidence kickoff+90min).
- [ ] [VERIFY] P0. After ship, deployment-ui schema modal for FIXTURES_SCHEDULE / FIXTURES_OUTCOMES shows all 9 new
      timestamp columns + 11 new score-distinction columns populated for completed fixtures.

### Per-fixture orchestrator iteration (migrated from `sports_per_fixture_anchored_cascade_2026_05_08`)

Source issue archived. instruments-service orchestrator iterates per-league-per-day for FIXTURE_STATS / EVENTS / LINEUPS
/ INJURIES instead of per-fixture-id. If api_football returns 11 of 12 fixtures, the 12th's missing stats produce ZERO
manifest rows instead of per-fixture expected universe. Honest-coverage broken for sports.

**Cross-plan banner**: writegate Phase 3.D.5 Wave 3 v2 enumerator must wire sports expected-universe = captured
FIXTURES_SCHEDULE rows (Phase 4 of source issue documented this dependency). Coordinate with
`writegate_honest_coverage_endtoend_2026_05_06`.

- [x] ✅ [SCRIPT] P0. Orchestrator refactor: per-fixture-id iteration for FIXTURE_STATS / FIXTURE_EVENTS /
      FIXTURE_LINEUPS / INJURIES. **RESOLVED 2026-05-25**: enrichment-only mode already uses
      `_read_fixture_ids_from_gcs` to iterate per fixture_id; `?id=<fixture_id>` endpoint confirmed (verified 2026-05-23
      with id=867946). Standard-mode per-fixture iteration superseded — master plan ✓ decision: `(league_id, day)` is
      canonical shard atom; fixture-level iteration runs within the day shard.
- [x] ✅ [ABANDONED] P0. Manifest row_key extension: `fixture_id` as first-class shard axis. **SUPERSEDED 2026-05-25**
      by master plan decision (master_to_live_defi_2026_05_23.md §"Shard atom decisions"): `fixture_id` is NOT a shard
      atom. `(league_id, day)` already bounds fixtures. No row_key change needed.
- [x] ✅ [SCRIPT] P0. Cluster validation at `record_captured` for bundled fixture-day parquets. **RESOLVED 2026-05-25**
      by writegate Phase 3.D.5 v2 enumerators (Sports@9a1bcd91, CeFi@09361718, TradFi@d50b9453, DeFi@b0e4bcac) — v2
      enumerators implement expected-universe = captured FIXTURES_SCHEDULE rows. Cluster validation shape at
      `(league_id, day)` shard level is covered by the v2 enumerator contract.
- [x] ✅ [ABANDONED] P0. One-shot manifest migration: per-league-per-day → per-fixture rows. **SUPERSEDED 2026-05-25**:
      `fixture_id` not a shard atom; no row_key migration needed. Single-walk discipline also gates any new GCS walk.
- [x] ✅ [ABANDONED] P0. Post-migration smoke for per-fixture row expansion. **SUPERSEDED 2026-05-25**: no migration
      (per item 4 above). Item closed.
- [x] ✅ [AGENT] P1. Open question — does api_football provide a per-fixture endpoint or only bulk? If only bulk, the
      orchestrator's per-fixture iteration becomes a filter on a single bulk fetch (rate-limit budget unchanged). Verify
      via the api_football docs + a smoke probe before committing the refactor shape. **COMPLETED 2026-05-23**:
      Per-fixture endpoint EXISTS — `GET /fixtures?id=<fixture_id>` returns 1 result (verified with id=867946 → Crystal
      Palace vs Arsenal). Multi-fixture `?ids=X-Y-Z` syntax exists but returns 0 for tested IDs (likely consecutive IDs
      that don't form a valid set). **Refactor shape**: orchestrator SHOULD use the `?id=<fixture_id>` endpoint for
      targeted per-fixture updates (stats, events, lineups) after the date-bulk fetch identifies which fixtures need
      updating — per-fixture rate budget applies (100 req/min on free, 7500/day).

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
- [x] ✅ [AGENT] P1. Downstream consumer guidance — features-sports arbitrage / odds-movement calculators handle NaN
      rows: arbitrage drops NaN bookmakers from the pricing comparison (already correct behavior); odds-movement treats
      NaN snapshot as no-update (already correct). Document in `codex/02-data/honest-absence-downstream-handling.md` §
      "ODDS NaN-fill semantics" (extend existing doc, not new). **COMPLETED 2026-05-23**: Section added to
      honest-absence-downstream-handling.md with: NaN-fill vs record_empty distinction table, per-consumer policy table
      (arbitrage/CLV/ML/execution), implementation note on cluster validation denominator — PM@(see commit).

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

- [x] ✅ [SCRIPT] P0. **Sports feature_groups → UAC `FEATURE_REQUIRED_INPUTS`**. ~60 sports feature_groups (form,
      league_strength, fixture_xg, lineup_quality, market_consensus, etc.) need registry entries. Source-of-truth:
      `features-sports-service/features_sports_service/calculators/` calculator metadata. Coordinator Phase 4.
      **COMPLETED 2026-05-23**: 36 sports feature_groups registered in `required_inputs.py`; 9 missing raw data_types
      (XG/XG_SHOTS/MATCHES/STANDINGS/WEATHER/PREDICTIONS/ODDS/ODDS_HORIZON_BUCKET/TRANSFER_RECORDS) added to
      `AVAILABILITY_AT_SEMANTICS` + `source_priority.py`. `validate_required_inputs()` → 0 issues; 38/38 UAC tests pass.
      UAC@e9a613b8.

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

- **Depends on:** `cross_cutting_may_23_SUPERSEDED_2026_05_21` for strategy catalogue (sports ML archetype + venues),
  infrastructure baseline, UI replication of backtest harness.
- **Shares with:** `cefi_ml`, `sp_prediction`, `prediction_markets` (now folded into respective masters) share ML
  lifecycle (training pipeline, model registry, drift detection, batch backtest harness).
- **Provides to:** `predictions_master` (folded `prediction_markets`) may consume sports ML signals as inputs to
  sports-betting prediction-market strategies (Polymarket fixture markets).

### Open questions

- [x] ✓ **Which sports ML archetype — RESOLVED 2026-05-08.** **Match-outcome (1X2)**. Most data-rich label, best
      signal-to-noise (FSS progressive + lineups + injuries + odds movement → home/draw/away), cleanest walk-forward
      validation. Goal-scorer + in-play live-odds DEFERRED post-cutover. See
      `plans/archive/operator_decisions_2026_05_08.plan.md`.
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

- [x] ✅ [SCRIPT] **P0**. **SP-13 — MTDS sports registry phantom-import bug (critical-path May-23 blocker)**. **[DONE —
      verified 2026-06-05 (slot-4): `registry.py:39-41` `_ADAPTER_PATHS` already routes all keys to canonical
      `execution_service.sports_execution.adapters.*`; the phantom `unified_sports_execution_interface` package is
      eliminated. The earlier in-flight fix shipped; checkbox was stale.]**
      `market-tick-data-service/market_tick_data_service/market_interface/sports/registry.py:23-40` `_ADAPTER_PATHS`
      routes 18 sportsbook/exchange/bookmaker keys (betfair / matchbook / onexbet / odds_api / skybet / coral /
      paddypower / betfred / betvictor / boylesports / bwin / ladbrokes / williamhill / betway / unibet / bet888sport /
      bet365 / sbo) to `unified_sports_execution_interface.adapters.*` — a **phantom Python package** (no such package
      exists workspace-wide; URDI ELIMINATED 2026-03-26 per codex/GLOSSARY.md). Every `adapter_for_bookmaker(key)` call
      raises `ModuleNotFoundError` at the `importlib.import_module()` line. **Fix**: rewrite the 18 phantom paths to
      `execution_service.sports_execution.adapters.<subdir>.<module>` per the post-merge layout in
      `execution-service/execution_service/sports_execution/adapters/__init__.py:1-32`. Other agent in flight on this
      fix.
- [x] ✅ [SCRIPT] **P1**. **SP-5 — bet365 + DK/FD as live EXECUTION venues = ALREADY NOT LIVE (slot-4 investigation
      2026-06-05; operator "delete")**: bet365/DraftKings/FanDuel carry NO execution routing — absent from MTDS
      `_ADAPTER_PATHS` (removed 2026-05-12), NOT execution-declared in UAC capability decls (only
      betfair/kalshi/polymarket/matchbook), and not in `SportsRouter`/`SportsExecutionRouter`. NB `scrapers/bet365.py`
      is an ODDS-DATA reader (no `place_bet`) — keep. The only residual is the inert `DEFERRED-INDEFINITELY` `browser/`
      stub family (~69 venues, all `NotImplementedError`); a 3-venue carve-out is a no-op/odds-data-risk. **OPTION-B
      DONE (operator confirmed "physically delete it, it's pointless for now" 2026-06-05 —
      execution-service@8c24f9009)**: deleted the WHOLE deferred `adapters/browser/` execution-stub subsystem (8 files,
      ~68 stubs) + its browser-only test + the `routing.py` `browser_automation` source/`get_browser_adapter` branch;
      KEPT `scrapers/` (odds-data), the 4 real venues, and the UAC-owned `VENUE_EXECUTION_REGISTRY` (no local registry
      files existed). 304 targeted tests green, basedpyright clean, clean break (no shims). (Supersedes the earlier
      OPTION-B-open note + the original SP-5 "bet365 wired wrong / DK-FD have no scraper — ship-or-delete" framing —
      both resolved by the deletion above.)
- [x] ✅ [SCRIPT] **P1**. **SP-10 — cluster-validation kwargs MISSING workspace-wide**. **[DONE —
      instruments-service@b2a7ad75 2026-06-05: ASSESSED — no sports `record_captured_from_counts` site is a genuine
      multi-cluster bundle (one row per entity at (date,data_type[,league]); league is the row KEY, not a sub-cluster)
      AND no authoritative expected-cluster source applies (`get_expected_bookmakers` is the MTDS per-bookmaker feed,
      not the IS aggregated FootyStats odds) → any expectation would FALSE-FAIL captured data. All 10 `{}` sites
      documented with an SP-10 rationale + `test_sports_cluster_validation_contract.py` pins the gate (missing cluster →
      attempted_failed). The empty dict is the CORRECT, now-guarded decision.]** ~~0 hits for `expected_root_clusters`~~
      / `cluster_extractor` in any sports adapter. CLAUDE.md cluster-validation mandate (`record_captured()` for bundled
      data_types) not wired through `instruments_service/engine/orchestrator.py` for sports per-fixture bundles. Add
      cluster kwargs at the bundle-writer boundary in orchestrator.
- [x] ✅ [SCRIPT] **P1**. **SP-12(a) — execution-service `sports_execution` missing `classify_venue_error()`**. **[DONE
      — verified 2026-06-05: `classify_venue_error` is wired across 7 sports_execution adapters
      (onexbet/api_football/betfair/polymarket_clob/matchbook/kalshi/odds_api); the "0 hits" claim was stale.]**
      instruments-service sports reference adapters GREEN via `BaseSportsReferenceAdapter`; execution-service
      sports_execution has 0 hits. Add classify wiring at adapter-base level.
- [x] ✅ [SCRIPT] **P2**. **SP-12(e) — capability-decl vs method match**. **[DONE — execution-service@dbab41a0e
      2026-06-05: VERIFIED CONSISTENT — exactly 4 execution-capable sources (betfair/kalshi/polymarket/matchbook) each
      have an adapter; the other 11 sources are market/reference-data-only (Pinnacle correctly has NO execution
      adapter). The "17 vs 15" was a stale ill-posed count (it counted all sports SourceCapability data-feeds incl.
      removed _MANIFOLD/_SHARPAPI). Bidirectional capability⇄adapter drift-guard test added.]** ~~17 caps declared vs 15
      execution classes present. Reconcile.~~
- [x] ✅ [SCRIPT] **P2**. **SP-12(f) — shard-level isolation**. **[DONE — execution-service@dbab41a0e 2026-06-05:
      ALREADY per-adapter — `concurrent_executor._execute_single` wraps each venue's `place_bet()` in its own try/except
      + records the failure (not swallowed); `asyncio.gather` returns one result per venue without aborting the batch.
      Per-adapter isolation regression tests added.]** ~~Orchestrator-level catch preserves isolation but per-adapter
      not enforced. Tighten.~~

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
| C.6 Step 2: SFI_PROGRESSIVE_STATS contract columns  | `[x]` shipped           | UAC@1848647 — added ft_timer + match_end_time columns                                   |
| C.6 Step 3: UTL `resolve_match_end_time()` cascade  | `[x]` shipped           | UTL@89c0ae15 + UTL@520cbb2a tests — cascade resolver with NamedTuple return             |
| C.6 assert_available_at_present wiring              | `[ ]` open (UNBLOCKED)  | Was blocked on Step 3 UTL helper (now shipped); needs IS adapter wiring                 |
| C.7 Follow-up #1: STANDINGS flatten                 | `[~]` partial-shipped   | UAC@ac12d80 — normalizer + schema flatten (14→32 cols); migration deferred (VM op)      |
| C.7 Follow-up #3: MATCHES `team_a_*` → `home_*`     | `[x]` shipped           | UAC@4e23bd9 — FootyStats field mappings (12 home/away variants); migration deferred     |
| MatchStatus adapter migration                       | `[ ]` open (DEFERRED)   | Replace `{"FT","AET","PEN"}` ad-hoc sets with `AF_COMPLETED_CODES` across IS adapters   |
| Cross-source fixture status verifier                | `[x]` design-shipped    | PM@1a86b6ab — design in codex/02-data/sports-fixtures-lifecycle.md § verifier           |
| Codex doc `sports-fixtures-lifecycle.md`            | `[x]` shipped           | PM@1a86b6ab — 8-state lifecycle + per-state available_at + verifier design              |
| FIXTURES schema split (SCHEDULE + OUTCOMES)         | `[ ]` P0 open           | Large — coordinate with writegate strict-mode flip                                      |

**Next-agent entry point**: Pick any item from this table that has no blocker. Best candidates in priority order:

1. C.6 Step 4: Wire `resolve_match_end_time()` cascade into `available_at` stamping (now unblocked by Step 3)
2. C.6 Step 1 + assert_available_at_present wiring: IS orchestrator write-path wiring for `match_end_time` column
3. C.4 + C.7 #1 migrations: operational VM launches for flip-to-failed + delete + re-fetch (B.1 pattern)
4. MatchStatus adapter migration: replace `{"FT","AET","PEN"}` literal sets with `AF_COMPLETED_CODES` across IS adapters
5. FIXTURES schema split (SCHEDULE + OUTCOMES): coordinate with writegate strict-mode flip

### Trigger-based mapping storage + backfill (migrated from trigger_based_reference_data_2026_04_13)

> **MIGRATED FROM**: `plans/active/trigger_based_reference_data_2026_04_13.md` Phase A2.4-5 + A3.2-4 + A4.1 + C1b.
> Already-shipped items (A2.1-3, A3.1) were flipped in the source plan (pm@<flip-sha>).

- [x] ✅ [CODE] P2. **GCS write path for Transfermarkt mappings: `master/` (append-only) + `snapshots/`
      (trigger-dated)** — DONE 2026-06-03 (instruments-service@06e1274b). `_fetch_transfermarkt_data` now also writes
      (keeping `by_date/`): `sports_reference/master/entity={teams,team_mapping,player_values}/master.parquet`
      (accumulating) + `sports_reference/snapshots/entity=player_values/season={Y}/trigger={T}/player_values.parquet`
      (point-in-time, UTC trigger date) — via new `_master_blob_path` / `_snapshot_blob_path_player_values` /
      `_write_snapshot_player_values` helpers; bucket via `resolve_bucket_name`, cloud-agnostic storage client;
      all-non-blocking via `classify_and_emit_error`. Point-in-time squad values for lookahead-bias-free ML training.
- [x] ✅ [CODE] P2. **team_mapping append-only** — DONE 2026-06-03 (instruments-service@06e1274b).
      `_write_master_append`: download existing master (404→fresh) → `pd.concat([existing, new])` →
      `drop_duplicates(subset=key, keep="last")` (new wins) → upload. Dedup keys:
      `player_values=(canonical_league,team_id,season)` / `teams=(team_id,season)` /
      `team_mapping=(canonical_league,team_id)`.
- [x] ✅ [QG] P2. `bash scripts/quality-gates.sh` on instruments-service after A2.4-5 — exit 0; 18 unit tests
      (`tests/unit/test_transfermarkt_master_snapshots.py`, mocked storage). instruments-service@06e1274b. (NOTE:
      shipped via direct-LDR-push — sub-agent mis-cited the dirty-deps exception, UAC was clean; QG-green on LDR so it
      promotes via Tier-C, not lost.)
- [ ] [SCRIPT] P2. **Trigger-date backfill script** — for each league, for each trigger date 2019-2026 (from
      `get_reference_refresh_dates()`), run instruments-service with
      `--season=X --start-date=trigger_date     --end-date=trigger_date`. Template: adapts `sports_chunked_backfill.sh`
      pattern but iterates trigger dates not date ranges.
- [ ] [SCRIPT] P2. **VM fleet run** for trigger-date backfill (parallelize by league). Operational.
- [ ] [QG] P2. Validate GCS snapshots exist for all trigger dates × leagues × seasons.
- [x] ✅ [CODE] P2. **Trigger-date denominator in deployment-api** for mapping entities
      (teams/team*mapping/player_values). Depends on write-path item (must have data at `master/`/`snapshots/` to
      denominate against). — **DONE 2026-06-03 (deployment-api@96e7ac7)**: `TEAMS` was `global_periodic cadence_days=1`
      (~365/yr) and `PLAYER_VALUES` was `per_league_periodic cadence_days=90` (quarterly approx) — both WRONG (written
      at trigger dates only). Added `global_trigger_date` + `per_league_trigger_date` axes +
      `\_sports_trigger_dates_for*{window,league}`helpers (union     of`get_reference_refresh_dates`across leagues, clipped) reading from the UAC`LEAGUE_REGISTRY`(no GCS I/O, so it     works before the IS write-path lands — coverage shows 0% until then, correctly).`TEAMS`→`global_trigger_date`,     `PLAYER_VALUES`→`per_league_trigger_date`.
      8 tests incl. the trigger-date≪daily-calendar invariant. QG exit 0.
- [ ] [QG] P2. `bash scripts/quality-gates.sh` on deployment-api after A4.1.

## Assigned active plans

_5 active plans declare `parent_epic: sports_master` in their frontmatter. Workers pick up in priority order (P0 first).
Auto-populated by `scripts/plans/populate_epic_bodies_2026_05_21.py`._

## P0 — must complete before next foundation gate

### [`d2_uac_continuity_2026_05_20`](../active/d2_uac_continuity_2026_05_20.md)

**status**: active · **estimate**: 1.6 cal AI-days (class: infra) **title**: D2 — UAC continuity + known-gap calendars +
expected_coverage integration

## P1 — important; post-current-gate

_(no plans currently assigned at this priority)_

## P2 — useful; opportunistic

### [`hard_schema_enforcement_2026_05_08`](../archive/2026_05/hard_schema_enforcement_2026_05_08.md)

**status**: ✅ ARCHIVED 2026-05-21 — 100% complete (0 open todos); all 7 todos shipped; deferred P3 items migrated to
`tradfi_master.md`

### [`sports_scrapers_post_cutover_2026_06_01`](../archive/2026_05/sports_scrapers_post_cutover_2026_06_01.md)

**status**: ✅ ARCHIVED 2026-05-21 — BLOCKED-OPERATOR-DECISION; all phases DEFERRED-POST-CUTOVER-2026-06-01+; activates
on operator account-provisioning ack · **estimate**: 20 cal AI-days (class: brand-new)

### [`wave3x_residual_ssots_2026_05_08`](../archive/wave3x_residual_ssots_2026_05_08.plan.md)

**status**: ✅ ARCHIVED 2026-05-21 · **estimate**: 3.6 cal AI-days (class: design) — all tracks shipped; Track D
implementation → `wave3x_track_d_implementation_2026_05_19`; Track E wire-in →
`available_at_lookahead_bias_completion_2026_05_08` Phase B

### [`writegate_honest_coverage_endtoend_2026_05_06`](../archive/2026_05/writegate_honest_coverage_endtoend_2026_05_06.md)

**status**: ✅ ARCHIVED 2026-05-23 — Phases 1-7.A complete (write-gate + QG STEP 5.64/5.66 wired). Phases 7.B-7.D
DEFERRED (forward-fix QG step, retrospective backfill ~7.5M rows, verification A3+A4). · **estimate**: 24.0 cal AI-days
(class: design)

## P3 — backlog; revisit quarterly

- [x] ✅ [AGENT] P2. **MIGRATED FROM: plans/archive/api_football_phase_3b_3c_smoke_forward_poll_2026_05_13.md** —
      Orchestrator zero-fixture-path bug: `recovery_fixture_ids` does not bypass `_read_fixture_ids_from_gcs`; hardcoded
      `fixture_ids_override=[]` ignores the allowlist entirely. Bug was deferred to an issue doc
      `plans/active/issues/orchestrator_zero_fixture_path_recovery_bypass_bug_2026_05_14.md` that was never created.
      Fix: when `fixture_ids_override` is populated, skip the GCS read entirely and use the override list directly.
      Affects API-Football backfill recovery path. — instruments-service@b91b88a5 (already shipped by Harsh 2026-05-14;
      fix covers both per-fixture skip path + zero-fixture path; verified on branch)

## Archived plans

### [`writegate_honest_coverage_endtoend_2026_05_06`](../archive/2026_05/writegate_honest_coverage_endtoend_2026_05_06.md)

**status**: ✅ ARCHIVED 2026-05-23 — Phases 1-7.A complete. Phases 7.B/C/D deferred.

**Deferred (migrated):**

- **Phase 7.B — QG forward-fix step (DEFERRED-POST-CUTOVER)**: Add QG step to enforce write-gate for all future sports
  adapters going forward.
- **Phase 7.C — Retrospective backfill (~7.5M rows, ~6 AI-days, DEFERRED-POST-CUTOVER)**: Backfill all `honest_coverage`
  values for historical sports rows across all asset groups using the consolidated formula.
- **Phase 7.D — Verification A3+A4 (DEFERRED-POST-CUTOVER)**: Re-run mega-audit A3+A4 checks after backfill completes to
  confirm zero residual mismatches.

## Cross-references

- Master plan: [`master_to_live_defi_2026_05_23.md`](../active/master_to_live_defi_2026_05_23.md).
- Sibling asset_group umbrellas: `cefi_master`, `defi_master`, `tradfi_master`, `predictions_master`.
- Sports rename plan (KEPT ACTIVE — its own DAG):
  [`sports_data_available_at_rename_2026_05_07.md`](../archive/sports_data_available_at_rename_2026_05_07.plan.md).
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
