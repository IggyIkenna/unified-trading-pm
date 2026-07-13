---
doc_type: plan
title: Sports asset_group — drive every remaining data source to canonical 100%
summary:
  Following the understat XG/XG_SHOTS completion (2026-07-13, same-day), drive the rest of the sports asset_group to the
  same standard — 0 attempted_failed, 0 (or explained) expected_unattempted, 0 duplicate dedup-key groups, correct
  service_name/asset_group, working scheduled jobs. Order — api_football fixtures+enrichment, footystats, SFI,
  transfermarkt, weather, then odds (MTDS odds_api source).
status: active
nature: process
asset_group: [sports]
stage: [data]
repos:
  [instruments-service, market-tick-data-service, unified-trading-library, unified-api-contracts, deployment-service]
scope: [engineer]
tags: [sports, api_football, footystats, sfi, transfermarkt, weather, odds, manifest, data-correctness, autonomous]
related:
  [
    plans/active/understat_local_backfill_completion_2026_07_06.md,
    plans/active/sports_manifest_canonicalisation_2026_06_01.md,
  ]
created: 2026-07-13
last_updated: 2026-07-13
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2.4
assigned_role: data_engineering
model_tier: opus-required
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
source:
---

> **Dispatched under `/autonomous` (operator directive, 2026-07-13, same interactive session that completed
> understat).** Full authority per `cursor-configs/AUTONOMOUS_AGENT_RULES.md` + `SUB_AGENT_MANDATORY_RULES.md` — finish
> completely, no `BLOCKED-OPERATOR` leftovers, decide-and-document on ambiguity, journal every discovery to this plan's
> Progress Log (this section survives context compression — read it first on any resume).

# 0. Baseline audit (2026-07-13, slot-3, live-manifest read)

Single-parquet read of `gs://instruments-store-sports-prd-central-element-323112/_index/availability_index.parquet`
(4,863,784 rows post-cleanup), grouped by `source` (not `data_type` name — several data_types are misleadingly named,
e.g. `MATCHES`/`PREDICTIONS` are footystats-sourced, not api_football):

| source                                                 | rows      | captured | attempted_failed | expected_unattempted | notes                                                                                                                                                                           |
| ------------------------------------------------------ | --------- | -------- | ---------------- | -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| api_football                                           | 2,518,940 | 365,592  | **3,257**        | **453,961**          | FIXTURES/STANDINGS/TEAMS/INJURIES/FIXTURE_STATS/LINEUPS/EVENTS/PLAYER_STATS                                                                                                     |
| footystats                                             | 650,504   | 84,047   | 205              | 56                   | MATCHES/PREDICTIONS + part of ODDS — already near-clean                                                                                                                         |
| soccer_football_info                                   | 226,237   | 19,750   | 10               | 94                   | SFI_PROGRESSIVE_STATS only — already near-clean                                                                                                                                 |
| transfermarkt                                          | 270,719   | 58,028   | 0                | 47                   | PLAYER_VALUES — already clean                                                                                                                                                   |
| open_meteo (weather)                                   | 261,790   | 12,097   | 51               | 94                   | WEATHER — already near-clean                                                                                                                                                    |
| odds_api                                               | 2,667     | **0**    | 6                | 0                    | suspiciously sparse/dead — needs a retirement-status check                                                                                                                      |
| mdps_odds_horizon_bucket                               | 215,481   | **0**    | 0                | **209,526**          | **ZERO captures ever** — likely a never-wired or broken pipeline                                                                                                                |
| (retired: SFI_LEAGUES/STANDINGS/TRANSFERMARKT_LEAGUES) | 88,056    | 0        | 0                | 0                    | code-confirmed `_RETIRED_DATA_TYPES` in `rebuild_sports_manifest_v9.py:103` — already correctly typed `EXPECTED_DEPRECATED_DATA_TYPE`, needs only a spot-verify, no active work |

**api_football `attempted_failed` breakdown**: INJURIES 1,946 (`ApiFootballResponseError`) · FIXTURES 665
(`FIXTURES_FETCH_FAILED`) · blank `data_type` 461 (`UNCLASSIFIED_ADAPTER_ERROR` — a data-integrity issue, blank
data_type should never happen) · PLAYER_STATS 74 · FIXTURE_STATS 46 · FIXTURE_LINEUPS 30 · TEAMS 24 · FIXTURE_EVENTS 11
· several `phantom_captured_no_parquet_at_canonical_path` (claims captured, no file at path). **8,766
non-`instruments-service` rows** in the active-source set: `fill-missing-player-stats` (8,678, PLAYER_STATS — likely a
legitimate dedicated one-off service, needs confirming) + `market-tick-data-service` (88 — the exact orphans
deliberately left untouched by today's `instruments-service@2f56038e` cleanup, no confirmed canonical twin).

# 1. Todos

- [ ] [DATA] P0. **api_football deep investigation.** Characterize the 453,961 `expected_unattempted`: is this a
      legitimate could-exist-universe seed (many leagues × many years × many data_types, most cells genuinely
      no-fixture) or a real gap? Root-cause the 3,257 `attempted_failed` by class: (a) INJURIES
      `ApiFootballResponseError` (1,946) — likely rate-limit/quota or a schema drift, check the adapter; (b) FIXTURES
      `FIXTURES_FETCH_FAILED` (665); (c) blank-`data_type` `UNCLASSIFIED_ADAPTER_ERROR` (461) — a write-path bug
      (data_type should never be blank at write time, find where); (d) `phantom_captured_no_parquet_at_canonical_path`
      across several data_types (claims captured, no file — a storage/path-resolution mismatch). File as an issue doc if
      root cause spans multiple commits' worth of work.
- [ ] [DATA] P0. **api_football: fix root causes + re-attempt failed cells** (not just re-run — root-cause each
      attempted_failed class from the todo above first, ship the fix, THEN re-attempt so failures don't recur).
- [ ] [DATA] P1. **api_football: resolve the 8,766 non-instruments-service rows.** Confirm whether
      `fill-missing-player-stats` is a sanctioned dedicated service_name (check its origin script/plan) or another
      instance of the service_name-drift bug class fixed today; handle the 88 `market-tick-data-service` orphans (no
      canonical twin found by today's cleanup — investigate individually, they may be genuinely new data).
- [ ] [DATA] P0. **api_football TEAMS: root-cause + fix the 61-league per-league capture gap.** NEW 2026-07-13
      (operator-prompted direct re-verify contradicted the prior investigation's blanket "453,961 expected_unattempted
      is legitimate" claim). Confirmed: `captured` TEAMS rows exist in TWO incompatible grains — a blank-`league_id`
      bulk daily bundle (3,648 rows, ~621 teams/day, ALL leagues aggregated) vs a per-`league_id` granular capture
      (100,498 rows, only 33 distinct leagues). The `expected_unattempted` enumerator generates per-(league,date) cells
      for 94 leagues; **61 of those 94 have ZERO non-blank-league_id captured rows ever** (2018→2026, their entire
      history). Find the orchestrator code driving per-league TEAMS capture (likely
      `instruments-service/engine/     orchestrator/api_football.py` or a sibling) and determine: (a) was per-league
      TEAMS capture only ever wired for 33 leagues (a real, fixable capture gap — build it out for the other 61), or (b)
      is the bulk bundle the intended sole source of truth for TEAMS and the enumerator
      (`enumerate_expected_universe.py`) is wrongly generating per-league expectations that were never meant to be
      satisfied per-league (fix the enumerator, not the capture path)? Decide-and-document, ship the fix, re-verify.
      **Before closing the broader "453,961 is legitimate" claim for the OTHER data_types
      (ODDS/FIXTURE_LINEUPS/FIXTURE_EVENTS/FIXTURE_STATS/PLAYER_STATS/INJURIES/ FIXTURES), apply the same
      captured-vs-expected grain cross-check** — the aggregate "spread evenly across years" framing looked plausible but
      missed this exact bug for TEAMS; don't take the same claim on faith for the rest.
- [ ] [VERIFY] P1. **api_football: final re-verify** — 0 attempted_failed (or a documented, operator-equivalent
      acceptable residual per today's understat precedent), 0 dedup-key dup groups, correct service_name/asset_group,
      confirm any relevant scheduled jobs are running.
- [x] [DATA] P0. **mdps_odds_horizon_bucket: root-cause zero-ever-captured.** — DONE, code fix + backfill shipped:
      `market-data-processing-service@6907257e4` (manifest-bucket routing fix, ALSO fixed a second independent
      `_resolve_bucket()` project_id bug in the same commit) + `instruments-service@0ae48c3b0` (metadata backfill of the
      124,294 orphaned rows, 123,642 now `captured` and visible in the canonical manifest). Root cause was a
      manifest-bucket-routing split-brain, NOT a broken/unbuilt pipeline — see Progress Log 2026-07-13 "IMPLEMENTATION
      dispatch" entry for full detail, the 2 deeper follow-on bugs discovered (expected-universe grain mismatch;
      raw-input prefix-template drift), and the corrected `odds_api` finding (362,665 rows of the SAME bug class, filed
      as a new P1 todo below rather than fixed in this pass — touches the shared cross-asset-group MTDS orchestrator,
      higher blast radius, needs its own dedicated pass).
- [ ] [DATA] P1. **MTDS shared-orchestrator sports-manifest-bucket routing (NEW 2026-07-13).** Extend the same
      `sports → instruments-store` manifest-bucket exception to MTDS's own cross-asset-group raw-capture path
      (`engine/orchestrator/__init__.py::get_tick_data_bucket()` / `_DateRunState.bucket` / `manifest_finalize.py`'s
      `catalogue_bucket=state.bucket`) WITHOUT moving the actual tick-byte write path (mirror the `_resolve_bucket()` vs
      `_resolve_manifest_bucket()` split from the mdps_odds_horizon_bucket fix above) — then migrate the 362,665
      orphaned `source=odds_api` rows (362,631 `captured`, live through today) the same way. Requires a full audit of
      every `ManifestWriter`/preflight-lookup call site in the shared orchestrator (affects ALL asset_groups —
      cefi/defi/tradfi/sports/prediction, not just sports) before shipping — full blast-radius proof required per
      `AUTONOMOUS_AGENT_RULES.md` rule 11 (a gate/change you make must be proven across the whole fleet it touches, not
      just sports).
- [ ] [DATA] P1. **mdps_odds_horizon_bucket expected-universe grain realignment (NEW 2026-07-13).** Fix
      `enumerate_expected_universe.py`'s sports seeding for this source so `expected_unattempted` uses the SAME
      `(venue=ODDS_API, data_type=odds_horizon_bucket lowercase, timeframe=T-*)` grain MDPS actually writes, instead of
      the current coarse `(venue="", data_type=ODDS_HORIZON_BUCKET uppercase, no timeframe)` seed — confirmed zero
      identity overlap between the two grains in a live dry-run. Required before this source can show a clean
      0/0/0-style coverage number (currently ~209k `expected_unattempted` and ~124k `captured` sit as disjoint cells
      post-backfill).
- [ ] [DATA] P1. **reprocess_sports_odds.py raw-input prefix-template refresh (NEW 2026-07-13).** Reconcile
      `_CANONICAL_PREFIX_TEMPLATES` in `_read_raw_odds()` against MTDS's actual current on-disk sports-odds writer
      convention — confirmed via live `list_blobs` probes that NO on-disk shape currently uses the
      `data_source=ODDS_API` segment the reader expects (2026-05 layout: per-bookmaker `venue={BOOKMAKER}`; 2026-06+
      layout: meta `venue=ODDS_API` with non-`ticks.parquet` filenames). Needed before any future `--force` re-run can
      safely capture new dates without silently reclassifying real captures as `empty_confirmed`.
- [x] [DATA] P1. **odds_api source: retirement-status check.** — DONE, no code change (root-caused twice; see Progress
      Log 2026-07-13 "implementation" entry). `odds_api` is NOT retired/superseded: it is the sole `SOURCE_PRIORITY`
      owner of `ODDS_SNAPSHOT`/`ODDS_MOVEMENT`/`ARBITRAGE` and is a credential-gated (`BLOCKED-CREDENTIALS`) live
      source, already tracked in `plans/active/issues/wsfeedconnector_phase35_gap_2026_07_06.md` +
      `sports_odds_bookmaker_coverage_enumeration_2026_06_20.md`. Live-manifest spot-check confirms all 6 legacy
      `attempted_failed` rows carry `error_reason=PipelineModeSourceMismatchError` — i.e. these are the current
      write-safety gate correctly REJECTING a source/data_type-mismatched write, an honest record of the gate firing,
      not a bug. The prior investigation's suggested classifier "polish" was re-verified and found inapplicable — see
      below; not applied. DoD's "0 (or documented-equivalent)" residual is satisfied by this documented state.
- [ ] [DATA] P2. **footystats: close the small residual.** 205 attempted_failed (179 `TimeoutError` — likely a
      retry/backoff tuning fix, not a deep bug), 56 expected_unattempted (verify legitimate). Small, mechanical.
- [ ] [DATA] P2. **soccer_football_info (SFI_PROGRESSIVE_STATS): close the small residual.** 10 attempted_failed
      (`phantom_captured_no_parquet_at_canonical_path`), 94 expected_unattempted (verify legitimate).
- [ ] [DATA] P2. **transfermarkt (PLAYER_VALUES): verify clean.** 0 attempted_failed already; confirm the 47
      expected_unattempted is legitimate (likely off-season/no-transfer-window dates).
- [ ] [DATA] P2. **weather (open_meteo): close the small residual.** 51 attempted_failed
      (`phantom_captured_no_parquet_at_canonical_path`), 94 expected_unattempted (verify legitimate).
- [ ] [DATA] P3. **Retired data_types spot-verify.** SFI_LEAGUES/SFI_STANDINGS/TRANSFERMARKT_LEAGUES (88,056 rows,
      code-confirmed retired in `rebuild_sports_manifest_v9.py:103`) — spot-check a sample actually carries
      `EXPECTED_DEPRECATED_DATA_TYPE`, not a stale/blank reason. Cheap, no fix expected.
- [x] [VERIFY] P0. **Whole-asset_group final re-verify + close-out report.** — DONE 2026-07-13 (final-reverify
      dispatch). Fresh single-parquet re-read produced the final per-source table below; **DoD is NOT fully met** — 2 of
      8 categories hit the literal/documented-equivalent bar cleanly (transfermarkt, odds_api, retired data_types — 3
      actually), the rest have specific, already-scoped remaining code-work todos (not blockers) or are mid-flight on an
      already-running bounded process. See the "FINAL RE-VERIFY + CLOSE-OUT REPORT" Progress Log entry below for the
      full table, per-category verdicts, and the precise remaining-work list (each item is an existing `- [ ]` todo in
      §1, none newly discovered, none `BLOCKED-OPERATOR`).

# 2. Definition of DONE

Every active sports source (api_football, footystats, soccer_football_info, transfermarkt, open_meteo, odds_api or its
formal retirement, mdps_odds_horizon_bucket or its formal `BLOCKED-CREDENTIALS` scaffold) shows 0 `attempted_failed` / 0
(or documented-equivalent) `expected_unattempted` / 0 duplicate dedup-key groups / correct `service_name`+`asset_group`;
every root cause is fixed in code (not just data patched); all findings filed in the relevant plans/issue docs; final
report written in this plan's Progress Log.

> **STATUS as of the 2026-07-13 FINAL RE-VERIFY dispatch: NOT FULLY MET.** 3/8 categories meet the bar cleanly
> (`transfermarkt`, `odds_api`, retired data_types). `mdps_odds_horizon_bucket`'s core zero-ever-captured defect is
> fixed (0→123,642 captured, 0 dedup) but its `expected_unattempted` (209,526) needs the already-root-caused
> `enumerate_expected_universe.py` grain-realignment fix. `api_football` is code-complete (4 bug classes fixed,
> confirmed holding, dedup now provably 0) but needs a backfill-VM re-attempt of 3,257 stale rows + the root-caused
> TEAMS 61-league capture-gap fix. `footystats`/`soccer_football_info`/`open_meteo` are mid-flight on a live, bounded
> residual-closer process (PID 3247, `--max-rounds 6`) — footystats already improved 205→175, the other two await its
> end-of-run flush. Zero regressions found anywhere. Full detail + the precise 6-item remaining-work list: see the
> "FINAL RE-VERIFY + CLOSE-OUT REPORT" Progress Log entry below.

# 3. Codex SSOTs

- `codex/02-data/availability-manifest-and-data-status.md`, `…/honest-absence-downstream-handling.md`
- `codex/02-data/external-data-always-available-rule.md` (mdps_odds_horizon_bucket todo)
- `codex/05-infrastructure/manifest-consolidator-ssot.md`
- `codex/04-architecture/instruments-service-as-ssot-for-mtds.md`

## Progress Log

- 2026-07-13 (slot-3, interactive session): plan created under operator-directed `/autonomous` + Workflow dispatch,
  immediately following the understat completion in the same session. Baseline audit in §0 above. Model tier flagged
  `opus-required` per CLAUDE.md (cross-repo architectural investigation) — this session is running Sonnet 5 (cannot
  switch mid-session); compensating by routing the hard root-causing work to opus-tier Workflow sub-agents.
- 2026-07-13 (sub-agent, investigation-only dispatch — footystats/SFI/transfermarkt/weather residuals): fresh
  live-manifest read (`.venv/bin/python` ad-hoc script, `read_availability_index`, single-parquet read) confirms the
  plan's §0 baseline numbers are still current: footystats 205 attempted_failed (179 TimeoutError, 15 phantom, 11
  ArrowTypeError) + 56 EU; SFI 10 phantom + 94 EU; transfermarkt 0 attempted_failed + 47 EU; weather 51 phantom + 94 EU.
  **(1) expected_unattempted legitimacy — CONFIRMED legitimate for all 4**: every single EU row across all 4 sources is
  dated `2026-07-13` (today, the day this investigation ran) — 0 historical backlog. This is the SAME rolling ≤1-day
  trailing edge already root-caused for understat (`expected_universe_v2_daily` Cloud Scheduler enum re-seeds today's
  date at 01:30 UTC; same-day capture hasn't resolved it to `empty_confirmed(EXPECTED_NO_FIXTURE)` yet within the same
  calendar day). Not a real gap — self-closes on the next capture pass. No action needed beyond the daily job already
  running. **(2) phantom_captured_no_parquet_at_canonical_path — root-caused, GENUINE (not self-healing like the prior
  ODDS precedent)**: live-probed all 76 phantom rows (15 footystats + 10 SFI + 51 weather) against EVERY
  `candidate_parquet_paths()` candidate (canonical `pipeline_mode=` + legacy fallback) via direct
  `blob_exists`/`list_blobs` checks — **0 of 76 have a real parquet today** (unlike the 2026-07-08 footystats ODDS
  precedent where 19/20 were false positives that self-healed). Shared code-path root cause confirmed by reading
  `footystats.py`/`sfi.py`/`weather.py`: **all three share the IDENTICAL anti-pattern** — a synchronous per-league loop
  calls `_orch._gated_sink_write(...)` (a real, synchronous `storage_client.upload_bytes`, not buffered) immediately
  followed by `manifest.record_captured(...)` with NO per-shard try/except isolating the pair; the only exception
  handler is one FUNCTION-level `except Exception` wrapping the entire per-date/per-league loop (footystats.py:669,
  sfi.py's fetch-level handler, weather.py's per-date handler). `record_captured()` itself buffers into the in-memory
  `ManifestWriter` (flushed later via `.write()` / `flush_all_pending_buckets()`), decoupled in time from the
  synchronous data write. footystats' 15 phantom rows are a single contiguous cluster (SEGUNDA_DIVISION,
  2022-09-25→2022-10-10) — consistent with one historical backfill/retry pass where the manifest buffer's eventual flush
  survived but the corresponding data write did not durably persist (VM interruption / later overwrite/delete), the same
  buffered-manifest-vs-synchronous-data-write decoupling class already documented in
  `reconcile_phantom_manifest_rows_stale_read_overwrite_2026_07_12`. SFI (10 rows, scattered 2025-01→2026-04) and
  weather (51 rows, scattered 2019-2026) show the same shape (small counts, no self-heal) — same class, not
  independently re-diagnosed per-source. **Fix recommendation** (for the implementing agent): (a) data-only, safe,
  immediate — run the existing
  `scripts/reconcile_phantom_manifest_rows_all.py --asset-group sports --data-types MATCHES,PREDICTIONS,ODDS,SFI_PROGRESSIVE_STATS,WEATHER --unphantom-only --dry-run`
  first (safe-by-construction, phantom→captured only) to double-confirm before flipping the 76 confirmed-genuine rows to
  `attempted_failed` via the same tool's normal (non-`--unphantom-only`) apply mode, then let the standard retry path
  (VM re-run / `query_sports_is_gaps.py` → `launch-sports-is-gap-fill.sh`) re-capture them; (b) code fix, not urgent
  given the tiny count — wrap the write+record_captured pair in each of the 3 orchestrator modules in a per-shard
  try/except (mirroring the isolation pattern shard-level-failure-isolation.md already mandates) so a future interrupted
  write cannot leave a buffered manifest entry with no corresponding durable data write. **(3) footystats TimeoutError
  (179 rows) — retry/backoff tuning issue, NOT a dead endpoint**: dates span 2019-01-01 → 2023-01-03 uniformly (no
  concentration near any specific outage window), 100% blank `league_id` (date-level bulk-call timeouts before the
  per-league split, not a per-league-specific failure), split ODDS=90/PREDICTIONS=89. Uniform spread across 4 years of
  historical dates is inconsistent with "dead endpoint for old dates" and consistent with a generic transient-timeout
  class from the original backfill run; footystats' live endpoint is confirmed working today (this same investigation's
  EU rows are actively being seeded for it). Recommend a plain re-attempt (existing
  `footystats_residual_closer_2026_07_12.py` pattern or `query_sports_is_gaps.py` → gap-fill VM) with retry/backoff, no
  adapter-timeout code change needed. The 11 ArrowTypeError rows (all ODDS, 2020-2023) are a distinct, small,
  separately-diagnosable schema/serialization issue — not investigated further here (out of this pass's scope, flagged
  for the implementing agent to triage as a possible one-off dtype coercion bug in the ODDS write path). **(4) Retired
  data_types spot-verify — CLEAN, no fix needed**: `SFI_LEAGUES`/`SFI_STANDINGS`/`TRANSFERMARKT_LEAGUES`, 88,056 rows,
  100% `capture_status=empty_confirmed` with `error_reason=EXPECTED_DEPRECATED_DATA_TYPE` — exactly as documented in
  `rebuild_sports_manifest_v9.py:103`, no stale/blank rows found. No code or data changes made this pass
  (investigation-only per dispatch scope); all fixes above are recommendations for the next implementing session/agent.

- 2026-07-13 (sub-agent, investigation-only dispatch): **`odds_api` source retirement-status check — CONCLUSION: NOT
  retired/superseded, is a credential-gated (BLOCKED-CREDENTIALS) live source, already documented elsewhere.**
  - Direct manifest query (`gs://instruments-store-sports-prd-central-element-323112/_index/availability_index.parquet`,
    `source == "odds_api"`, 2,667 rows): 2,661 `empty_confirmed` split evenly 887/887/887 across `data_type` ∈
    {`odds_snapshot`, `odds_movement`, `arbitrage_opportunity`}, dated 2018-01-01→2020-06-05; 6 `attempted_failed`, all
    `data_type=ODDS`, dated 2019-01-23→2020-04-27, `service_name=instruments-service` throughout. **0 rows of any kind
    exist after 2020-06-05.**
  - `unified-api-contracts/unified_api_contracts/canonical/domain/sports/league_data.py:85` —
    `SPORTS_SOURCE_COVERAGE_START["odds_api"] = date(2020, 6, 6)` — literally the day AFTER the manifest's last
    empty_confirmed row. The 2,661 empty_confirmed rows are the honest pre-coverage-start backfill window and are
    **already correctly typed** — not a bug, nothing to fix.
  - `unified-api-contracts/unified_api_contracts/canonical/crosscutting/_source_priority_data.py:41-43` —
    `SOURCE_PRIORITY[("sports","ODDS_SNAPSHOT"|"ODDS_MOVEMENT"|"ARBITRAGE")] = ["odds_api"]` — odds_api is the SOLE
    registered source for these 3 data_types. They are NOT the shared `"ODDS"` data_type (that's
    `unified_api_contracts/canonical/domain/sports/league_data.py:171` → `"ODDS": "footystats"`, captured heavily by
    api_football/footystats per §0). **odds_api cannot be blanket-retired**: it owns data_types no other source
    substitutes for, and is not in `rebuild_sports_manifest_v9.py:103`'s `_RETIRED_DATA_TYPES` set (that set is
    `{SFI_LEAGUES, SFI_PROGRESSIVE_STATS, SFI_STANDINGS, TRANSFERMARKT_LEAGUES}` only).
  - The 6 legacy `attempted_failed` `ODDS` rows are pre-registry-correction noise: odds_api never owned generic `ODDS`
    (footystats does), so these 2019-2020 writes are a source/data_type mismatch from before the current
    `SOURCE_PRIORITY` ownership + `PipelineModeSourceMismatchError` gate existed (gate referenced in
    `instruments-service/scripts/backfill_orphan_class_e.py:267` and `backfill_orphan_class_e_sports.py:106`) — current
    code cannot reproduce this class. 6 rows is below any materiality bar; recommend leaving as historical
    `attempted_failed` (truthful record) rather than inventing a new relabel reason — do **not** relabel to
    `EXPECTED_DEPRECATED_DATA_TYPE` (that reason means "this data_type is retired," which `ODDS` is not).
  - `market-tick-data-service/market_tick_data_service/live/connectors/odds_api_ws.py` — the odds_api WSFeedConnector is
    FULLY BUILT (polls The Odds API v4 REST, 60s interval) and REGISTERED (confirmed in
    `plans/active/issues/wsfeedconnector_phase35_gap_2026_07_06.md`'s 31-venue registered list — odds_api is sports' 1
    resolved venue, not one of the 7 unresolved). Its own docstring carries a live, standing
    `CREDENTIAL APPROVAL REQUEST — odds-api-live-ws` (existing `odds-api-key` secret needs a paid-tier quota bump,
    ~$10/mo Starter tier, ~43k credits/mo at 60s polling) tied to "Phase 3.5e May-23 gate" — i.e. this is a KNOWN,
    already-filed `BLOCKED-CREDENTIALS` gap, not abandoned/dead code. Independently corroborated by
    `instruments-service/scripts/migrate_legacy_oddsapi_instruments_to_twins_2026_06_19.py`'s own preamble ("canonical
    `venue=odds_api` rows in the `_index` are all `empty_confirmed` and stop at 2020-06-05") and by
    `plans/active/issues/instruments_docs_audit_outstanding_items_2026_07_08.md:412-414,612-613` ("the live Odds API
    connector … is itself `BLOCKED-CREDENTIALS`, so live sports odds has never actually run").
  - **The real open gap** (post-2020-06-06 to present: 0 captured, 0 attempted_failed, 0 expected_unattempted — the
    expected-universe was never seeded for odds_api's 3 owned data_types in its actual coverage window) is the SAME
    already-tracked credential gap, not a new discovery — already touched by the active
    `plans/active/sports_odds_bookmaker_coverage_enumeration_2026_06_20.md` ("BLOCKED-CREDENTIALS for full 2-week GCS
    baseline"). No new issue doc needed; no code fix needed (adapter + registration already exist per
    external-data-always-available-rule's "build the scaffold anyway" bar — already satisfied).
  - **Recommended fix (for the implementing agent on this todo)**: mark this todo DONE with the above documented as the
    terminal state. No manifest relabel, no source-retirement list entry, no new adapter work. If the plan's literal "0
    attempted_failed" DoD must be hit for odds_api specifically, the minimal change is a narrow classifier exemption in
    `market-tick-data-service/market_tick_data_service/scripts/rebuild_sports_manifest_v9.py`'s `_classify_empty_row`
    (mirroring the existing step-1 `_RETIRED_DATA_TYPES` relabel pattern at line 421) that relabels exactly
    `(source=odds_api, data_type=ODDS, date<2020-06-06)` to a new reason (e.g. `EXPECTED_LEGACY_SOURCE_MISMATCH`, NOT
    `EXPECTED_DEPRECATED_DATA_TYPE`) — optional polish, not required, given the 6-row scale and the understat precedent

- 2026-07-13 (slot-3, investigation-only sub-agent, live-manifest re-read of `api_football` slice, no code/data
  changes): full root-cause on the P0 api_football investigation todo above. **Verified exact live counts**: captured
  365,592 · empty_confirmed 1,696,130 · expected_unattempted 453,961 · attempted_failed 3,257. **(1)
  expected_unattempted (453,961) is a legitimate could-exist seed, evenly spread 2018-2026 (~28.5k-57.6k/yr, no cliff)**
  — by data_type: TEAMS 192,384 · ODDS 82,749 · FIXTURE_LINEUPS 47,282 · FIXTURE_EVENTS 47,028 · FIXTURE_STATS 36,677 ·
  PLAYER_STATS 26,363 · INJURIES 20,700 · FIXTURES 778. Per `enumerate_expected_universe.py` `_enumerate_v2_sports`
  (line 1735), this is the per-LEAGUE cross-product against `SPORTS_DATA_TYPE_TO_SOURCE`'s coverage-start-gated axis —
  the low FIXTURES count (only 778, vs TEAMS' 192k) confirms the enumerator's
  `_build_af_fixture_calendar`/`EXPECTED_NO_FIXTURE` truthset carve-out (docstring line ~1777) is doing its job for the
  primary data_type; no action needed, this is denominator, not a gap. **(2) attempted_failed root causes, by
  error_reason**: `ApiFootballResponseError` 1,642 (INJURIES 1,600 / TEAMS 24 / PLAYER_STATS 10 / FIXTURE_STATS 7 /
  FIXTURE_LINEUPS 1) · `FIXTURES_FETCH_FAILED` 665 · `phantom_captured_no_parquet_at_canonical_path` 487 (INJURIES 346 /
  PLAYER_STATS 64 / FIXTURE_STATS 39 / FIXTURE_LINEUPS 29 / FIXTURE_EVENTS 11) · `UNCLASSIFIED_ADAPTER_ERROR` 461 (100%
  blank data_type) · `phantom_re_attempt_after_writer_fix_f36651c` 2.
  - **(a) INJURIES `ApiFootballResponseError` — CONFIRMED misclassification bug, not rate-limiting.** The exception is
    raised at `instruments_service/reference_data/adapters/sports/adapters/api_football.py:948` (`_raise_on_api_errors`)
    whenever API-Football's JSON envelope carries a non-empty `errors` dict with `is_rate_limit=False` (i.e. NOT the
    `rateLimit` key — genuine rate-limit responses are already retried transparently by `_fetch_and_extract`, lines
    707-750, and never reach `attempted_failed`). The failure is written via `_AfManifestHooks.note_failed` →
    `sports_reference_core.py:62` → `_classify_adapter_failure(exc, "api_football")`
    (`instruments_service/engine/orchestrator/failure.py:33-46`), which passes `type(exc).__name__` (the literal string
    `"ApiFootballResponseError"`) into UAC `classify_venue_error("api_football", "ApiFootballResponseError")`. But UAC's
    `VENUE_ERRORS_SPORTS["api_football"]` table
    (`unified-api-contracts/unified_api_contracts/canonical/crosscutting/errors/sports.py:9-82`) is keyed by
    HTTP-status/domain codes (`"429"`,`"401"`,`"400"`,`"500"`,`"FREE_PLAN_DATE_LIMIT"`,`"SEASON_NOT_FOUND"`,
    `"LEAGUE_NOT_FOUND"`,`"RATE_LIMIT_DAILY"`,`"FIXTURE_NOT_FOUND"`) — the exception CLASS NAME never matches any of
    those keys, so `classify_venue_error` always returns `None` and the code falls back to the raw class name. This
    means the manifest can NEVER distinguish which of API-Football's real hard-error categories (plan/token/param/
    season/league) actually fired — it's a lookup-key-type bug, not a rate-limit problem. Evidence the failures are a
    handful of systemic runs, not per-date organic failures: only 3 distinct `attempted_at` values across all 1,642 rows
    (2026-06-25, 2026-06-26, 2026-07-13T16:24:30 — the last one alone contributing 2,182 rows across ALL api_football
    failure classes, including 100% of the 487 phantom rows), and INJURIES failures are evenly spread 2019-2026 (not
    concentrated in old/new dates), ruling out a simple date-window plan restriction. **Root cause is almost certainly a
    real API-Football envelope error (`_raise_on_api_errors`, `api_football.py:932-953`) — most likely a
    plan/entitlement error specific to the INJURIES endpoint (API-Football gates INJURIES behind a paid-plan tier) —
    being raised and immediately misclassified**, not investigated further because `_raise_on_api_errors` discards the
    raw `errors` dict content once it builds the exception message string (only preserved in `str(exc)`, which the
    manifest never persists — only `error_reason` is stored). **Concrete fix**: (i) thread the raw envelope `errors`
    dict's key (`"plan"`/`"token"`/`"requests"`/etc, whichever populated) through as the `error_code` passed to
    `_classify_adapter_failure`/`record_failed` instead of the exception class name (the
    `ApiFootballResponseError.__init__` already receives the raw message — extend it to also carry a structured
    `error_key` attribute the caller reads); (ii) add the missing UAC `VENUE_ERRORS_SPORTS["api_football"]` entries for
    whatever concrete key surfaces (likely a plan/entitlement code) so `classify_venue_error` resolves it; (iii) only
    THEN re-attempt INJURIES — re-attempting blind today would just reproduce the same misclassified failures if it's
    truly a plan/entitlement gate (a credential/plan upgrade ask, not a code bug, in that case — confirm by making ONE
    manual `GET /injuries?date=...` call with the live key and inspecting the raw `errors` body before re-running the
    backfill).
  - **(b) FIXTURES `FIXTURES_FETCH_FAILED` (665)** — not yet root-caused to adapter code in this pass (no
    `FIXTURES_FETCH_FAILED`-literal raise site found in `api_football.py`; likely raised in
    `sports_reference_fixtures.py`/`sports.py`'s date-wide fixtures-list call site as a wrapper `RecordFailedReason`,
    analogous to `UNCLASSIFIED_ADAPTER_ERROR` below). Left for the implementing agent — grep
    `RecordFailedReason.FIXTURES_FETCH_FAILED` call sites and inspect `attempted_at`/date clustering the same way as (a)
    above before re-attempting.
  - **(c) blank-`data_type` `UNCLASSIFIED_ADAPTER_ERROR` (461) — CONFIRMED write-path bug, root cause is NOT the
    api_football adapter itself.** All 461 rows: `service_name=instruments-service`, blank `league_id`, dates spread
    2017-2020ish (sampled). Traced to `instruments_service/engine/orchestrator/process_completeness.py`'s
    `_finalize_completeness` (lines 494-501) and `_detect_thin_day_venues`'s corrective-write call (lines 532-538) — a
    GENERIC, venue-grain shard-completeness gate (built for CeFi/TradFi venue-shaped shards:
    `row_key={"date": date, "venue": _failed_venue}`) that writes a corrective `record_failed` with **no `data_type` key
    in `row_key` at all**. Sports' captured atom is league-grain (`data_type`, `league_id`, `date` — confirmed in
    `_SPORTS_PRESENT_COLS`, `enumerate_expected_universe.py:149`), not venue-grain, so when this generic completeness
    gate's missing-shard logic fires for an api_football pseudo-shard it stamps a row with a blank `data_type` (and
    blank `league_id`) that can never match any real sports cell — a permanently-orphaned, non-reconcilable manifest
    row. **Fix**: exclude `asset_group=sports` (and any other non-venue-shaped asset_group) from
    `_finalize_completeness`'s missing-shard `record_failed` path, mirroring the CeFi-only scope
    `_detect_thin_day_venues` already declares in its own docstring — OR require the caller to pass a `data_type` in
    `row_key` for any asset_group whose present-set columns include `data_type` (reuse `_present_cols_for` from
    `enumerate_expected_universe.py` as the SSOT for what row_key keys are valid per asset_group).
  - **(d) `phantom_captured_no_parquet_at_canonical_path` (487)** — 100% share the single
    `attempted_at = 2026-07-13T16:24:30.871968+00:00` timestamp (the same run that produced 2,182 of the day's
    failures), concentrated in INJURIES (346)/PLAYER_STATS(64)/FIXTURE_STATS(39)/FIXTURE_LINEUPS(29)/FIXTURE_EVENTS(11)
    — i.e. a single consolidator/reconciliation run stamped these as "claimed captured, no parquet found at the resolved
    canonical path" in one pass. Given the correlation with the exact same run-timestamp as the INJURIES
    misclassification finding above, this is very plausibly the SAME root incident (a run that hit a systemic issue —
    API/auth failure or a path-resolution regression — mid-fetch and the manifest ended up in a claimed-but-unwritten
    state for whatever cells were in flight). Not independently root-caused to a specific path-computation-vs-write
    mismatch in this pass (budget); the implementing agent should diff the GCS-write helper's computed path
    (`instruments_service`'s sports writer, likely `writers.py`) against `candidate_parquet_paths()` (per CLAUDE.md's
    "Sports paths" pointer) for the exact prefix template used at that timestamp, since a `prefix_tpls` drift is the
    documented failure class for this reason code workspace-wide. **(3) non-instruments-service rows — both resolved, no
    action needed**: `fill-missing-player-stats` (8,678 rows, 100% PLAYER_STATS) is a **sanctioned, already-marked
    one-off** — confirmed via `instruments-service/scripts/fill_missing_player_stats.py` (`# Epic: instruments_master`,
    `# Lifecycle: oneoff`, `# Delete-when: after fill confirmed in live consolidated _index`), a deliberate gap-fill
    script that calls the same orchestrator fetch + `ManifestWriter.record_captured/_empty/_failed` path as the main
    pipeline, just with its own `service_name` string and a bypassed date-iteration for efficiency. Not a
    service_name-drift bug — leave as-is (delete the script only once its Delete-when condition is met). The 88
    `market-tick-data-service` rows: 100% `capture_status=captured`, 100% `data_type=PLAYER_STATS`, blank
    `error_reason`, spread across ~25 distinct leagues and dates 2020-2026 (pulled individually — sample in this
    session's scratch script). These are genuinely-captured historical data with no duplicate/twin (consistent with why
    today's `2f56038e` cleanup left them untouched) — **recommend re-stamping `service_name` to `instruments-service`
    via a direct verified canonical rewrite** (same read-live-index / confirm-no-twin / write-back pattern as
    `instruments-service/scripts/dedup_mtds_instruments_surface_duplicate_rows_2026_07_13.py`), NOT deletion — deleting
    would destroy real capture evidence that has no replacement. **Recommended execution order for the next (fixing)
    agent**: (c) blank-data_type write-path fix first (cheapest, most clearly a bug, unblocks re-verification of the
    shard-completeness path broadly) → (a) INJURIES misclassification fix + UAC table entry + ONE manual
    envelope-inspection call before any re-attempt → (b) FIXTURES root-cause (mirror the (a)/(c) method) → (d)
    phantom-path diff → re-attempt all four classes → (3) service_name rewrite for the 88 MTDS rows → final re-verify
    todo. of accepting a documented-equivalent residual.

- 2026-07-13 (sub-agent, investigation-only dispatch): **`mdps_odds_horizon_bucket` zero-ever-captured root-cause —
  CONCLUSION: NOT a broken/unbuilt pipeline. Root cause is a manifest-bucket-routing split-brain: the real captured data
  lives in a DIFFERENT manifest than the one this investigation (and the plan's §0 baseline) queried.**
  - **The pipeline is fully built and actively running.** Producer:
    `market-data-processing-service/market_data_processing_service/app/adapters/sports/bucket_assignment_adapter.py`
    (`SportsBucketAssignmentAdapter`, registered
    `@CandleAdapterRegistry.register(MarketAssetGroup.SPORTS, "odds_horizon_bucket")`) — complete, tested,
    honest-coverage-compliant (empty/failed paths correctly distinguished). Entrypoint:
    `market-data-processing-service/scripts/reprocess_sports_odds.py`. Launcher:
    `deployment-service/scripts/vm/launch-mdps-sports-bucket-vm.sh` (Pass K of the archived
    `sports_predictions_e2e_2026_05_05` plan).
  - **Direct evidence it has run and is current**: `reprocess_sports_odds.py:149` resolves its manifest bucket as
    `get_bucket_name("market-data-tick-sports", project_id=project)` → writes to
    `gs://market-data-tick-sports-prd-central-element-323112/_index/availability_index.parquet` — a SEPARATE physical
    manifest from `instruments-store-sports-prd` (the one this task's brief + the plan's §0 baseline queried). Direct
    read of that manifest (1,958,499 total rows): `source=mdps_odds_horizon_bucket` → 124,294 rows, `capture_status`
    123,642 `captured` / 652 `empty_confirmed`, **0 attempted_failed**; `service_name` split
    `market-data-processing-service` 109,638 + `market-tick-data-service` 14,656; `written_at` spans
    2026-05-05T22:07:33Z → **2026-07-13T06:16:02Z (today)** — the pipeline is live and current, ~99.5% capture rate.
    Confirmed further via GCS listing: real raw `data_source=ODDS_API` tick parquets exist under
    `gs://market-data-tick-sports-prd-central-element-323112/raw_tick_data/by_date/day=.../pipeline_mode=batch_odds_api/`
    across 1,938 distinct `day=` partitions through 2026-06-24 — the upstream input MDPS reads is real and populous.
  - **Why `instruments-store-sports-prd` shows 0 captured**: querying it directly (215,481 `mdps_odds_horizon_bucket`
    rows) shows ALL rows are `service_name=instruments-service`, ALL carrying an `enumerator_run_id` (e.g.
    `enum-universe-sports-20260628-213115`, `enum-universe-sports-20260629-075526`) — i.e. every single row was written
    by the expected-universe ENUMERATOR, never by MDPS/MTDS. Cross-check confirms this categorically: **zero rows
    anywhere in the 4,863,784-row `instruments-store-sports-prd` manifest have
    `service_name == "market-data-processing-service"`.** The 209,526 `expected_unattempted` are the enumerator's normal
    seed; the 5,955 `empty_confirmed` all carry `error_reason=EXPECTED_PRE_SOURCE_COVERAGE_START` (dated
    2018-01-01→2020-06-05, i.e. enumerator-side pre-coverage marking, not an actual MDPS attempt).
  - **The actual bug**: `instruments-service/scripts/enumerate_expected_universe.py:279-307` (`_default_bucket_for`)
    hardcodes, as a documented deliberate decision ("slot-4 finding 2026-06-07", see
    `plans/active/sports_manifest_canonicalisation_2026_06_01.md` lines ~1524-1997), that **all of sports' manifest —
    including MTDS/MDPS-owned market-data types — lives in the `instruments-store` bucket**, NOT the per-asset-group
    `market-data-tick` bucket that every other asset_group (cefi/defi/tradfi) uses. That decision was applied to the
    enumerator (denominator writer) but was **never mirrored to the MDPS producer** (`reprocess_sports_odds.py:149`,
    numerator writer) or to MTDS's own raw `odds_api` tick writer, which still both independently target
    `market-data-tick-sports-prd`. Result: numerator and denominator for `mdps_odds_horizon_bucket` (and likely for
    MTDS's raw `odds_api`/`trades` captures — the same split-brain may explain this plan's own §0 "odds_api …
    suspiciously sparse" line, though that source's `ODDS_SNAPSHOT`/`ODDS_MOVEMENT`/`ARBITRAGE` sub-types were
    separately confirmed genuinely credential-gated in the prior entry above — the raw `trades` numerator itself is NOT
    credential-gated and DOES exist, just in the other bucket) live in two different physical manifests that nothing
    ever merges — `codex/05-infrastructure/manifest-consolidator-ssot.md`'s Cloud Run consolidator jobs consolidate
    SHARDS WITHIN a bucket, not ACROSS the instruments-store/market-data-tick pair.
  - **Not a deferred/intentional design gap** — no plan or issue doc marks this as known;
    `sports_predictions_e2e_2026_05_05` (archived 2026-05-05, `status: in_progress` at archive time) explicitly called
    for running exactly this pipeline (Group D todos, all still `- [ ]` unchecked at archive) and was archived without
    those todos ever being flipped or re-homed to a successor plan — this is the silent-gap case, not the
    intentional-deferral case. Because features-service's sports reader
    (`features-service/features_service/sports/data/gcs_reader.py`, `test_read_bucketed_odds.py`) reads bucketed parquet
    **directly by GCS path**, not via the manifest, the actual ML/feature pipeline for `odds_horizon_bucket` is
    unaffected by this bug — only the manifest-derived coverage metric (and this investigation) were fooled.
  - **Recommended fix (concrete, for the implementing agent)**: (1) Either (a) make `reprocess_sports_odds.py:149` and
    MTDS's raw sports `odds_api` writer resolve their manifest bucket via the SAME `sports → instruments-store` routing
    exception already in `enumerate_expected_universe.py::_default_bucket_for` (co-locate numerator + denominator, the
    architecturally-consistent fix, matches the documented 2026-06-07 decision), OR (b) if `market-data-tick-sports-prd`
    is meant to stay the sports market-data canonical manifest instead, revert the enumerator's sports exception and
    seed the `mdps_odds_horizon_bucket`/raw-odds expected-universe there instead — **(a) is recommended** since the
    enumerator-side decision is the more recent, deliberately-verified one (WAVE-2 dry-runs, slot-4, 2026-06-07) and
    instruments-store-sports-prd is what this plan, the operator's task brief, and presumably the data-status UI all
    already treat as sports' canonical manifest. (2) One-time backfill: after the code fix, re-run
    `reprocess_sports_odds.py --force` (idempotent, no API credits — pure re-derivation from existing raw ticks) so the
    123,642 already-computed captures get correctly stamped as `captured` in `instruments-store-sports-prd` instead of
    silently sitting in the orphaned `market-data-tick-sports-prd` copy; do NOT double-count — either migrate/merge the
    existing 124,294 rows or let the re-run naturally overwrite via `ManifestWriter`'s dedup key. (3) Apply the
    identical fix-and-check to MTDS's raw `odds_api`/`trades` writer since it has the same bucket mismatch and is very
    likely why this plan's own §0 table flagged "odds_api … suspiciously sparse/dead" for the raw-tick numerator
    (separate from the credential-gated derived sub-types already resolved in the prior entry above). (4) Audit whether
    any other MTDS/MDPS sports writer (footystats/SFI/etc. already look clean per §0, so likely unaffected — they may
    already target `instruments-store-sports-prd` correctly) has the same mismatch before declaring this class of bug
    closed.

- 2026-07-13 (slot-3, implementation dispatch — `odds_api` todo): **re-verified the investigation's own recommended
  "optional polish" and found it does NOT apply as stated; corrected root-cause below; todo marked DONE with no code
  change (the correct outcome, not a shortcut).**
  - **Live-manifest spot-check** (single-row read of
    `gs://instruments-store-sports-prd-central-element-323112/_index/ availability_index.parquet`,
    `source=="odds_api"`): confirms 2,661 `empty_confirmed` + 6 `attempted_failed` (matches the investigation exactly).
    New finding: **all 6 `attempted_failed` rows carry `error_reason="PipelineModeSourceMismatchError"`** (dates
    2019-01-23, 2019-12-12, 2020-02-06, 2020-04-21, 2020-04-23, 2020-04-27; `service_name=instruments-service`
    throughout). This is a stronger, more precise finding than the investigation's "pre-registry-correction noise"
    framing — it is literally the SAME exception class the current-day write gate raises (confirmed live in
    `instruments-service/scripts/backfill_orphan_class_e_sports.py`'s `resolve_source_and_mode()` docstring and
    `backfill_orphan_class_e.py`'s `MissingSourceError`/ `PipelineModeSourceMismatchError` gate commentary) — i.e. these
    6 rows are the write-safety gate **correctly rejecting** an attempted odds_api write for the generic `ODDS`
    data_type (which `SOURCE_PRIORITY` reserves for footystats), and recording that rejection honestly as
    `attempted_failed`. This is the manifest doing exactly what it's supposed to do (per
    `codex/02-data/availability-manifest-and-data-status.md` — "never silent placeholders," trust the actual
    distribution) — **not a defect to patch.**
  - **Root-caused why the investigation's suggested classifier "polish" does not apply**: read
    `market-tick-data-service/market_tick_data_service/scripts/rebuild_sports_manifest_v9.py` and its helper
    `_rebuild_sports_write.py` in full. `_classify_empty_row` (and its 9-step `_RETIRED_DATA_TYPES`/`EXPECTED_*` relabel
    logic) is invoked ONLY over rows already sitting in `empty_confirmed` status (`_classify_all_empty_rows` iterates
    `empty_df`, the empty-only slice of the index). Existing `attempted_failed` rows take a **completely separate,
    unconditional** path: `_write_attempted_failed_rows` (`_rebuild_sports_write.py:308-353`) iterates every row with
    `capture_status == "attempted_failed"` and re-emits it via `writer.record_failed(...)`, preserving `error_reason`
    verbatim (or a `UNKNOWN_FETCH_FAILURE_PRESERVED_FROM_V8` fallback) — there is NO reason-based filter, source check,
    or data_type check in that path at all. Even setting aside that mismatch: reason-relabeling (even if it did fire)
    changes only the empty-row `reason` column, never the row's `capture_status` — so it could never move an
    `attempted_failed` COUNT to 0 regardless. **Conclusion: the suggested classifier exemption is a no-op for this gap
    on both counts** (wrong code path; wrong mechanism even if it were the right path). Not implementing it is the
    correct call, not a shortfall.
  - **Decision (no operator ask, per `/autonomous`)**: leave the 6 rows exactly as recorded. Relabeling a genuine
    gate-rejection event to erase it from the `attempted_failed` tally would be dishonest-manifest behavior (the
    opposite of what the honest-absence rule requires) for a below-materiality (6-row), already-non-reproducible
    (current `SOURCE_PRIORITY`/`PipelineModeSourceMismatchError` gates block recurrence) historical artifact. This is
    the plan DoD's explicit "documented-equivalent residual" case, matching the understat precedent already cited.
  - **Files read (no edits needed)**:
    `market-tick-data-service/market_tick_data_service/scripts/ rebuild_sports_manifest_v9.py` (896 lines, full read of
    `_classify_empty_row` + docstring + call sites),
    `market-tick-data-service/market_tick_data_service/scripts/_rebuild_sports_write.py:165-459` (`_write_empty_rows`,
    `_write_attempted_failed_rows`, `_classify_all_empty_rows`),
    `instruments-service/scripts/backfill_orphan_class_e.py`
    - `backfill_orphan_class_e_sports.py` (gate confirmation, unchanged from investigation).
  - **Todo `odds_api source: retirement-status check` flipped to `[x]` above.** No commits to `market-tick-data-service`
    or `instruments-service` — this todo's terminal state is documentation-only, which is the correct root-caused
    outcome (see workspace rule: "if the investigation's recommended fix turns out to be wrong... document what you
    actually found, don't force the prior recommendation").
- 2026-07-13 (slot-3, FINAL RE-VERIFY dispatch — `odds_api` todo, post-`2d0e4dd75`): **fresh single-parquet read of
  `gs://instruments-store-sports-prd-central-element-323112/_index/availability_index.parquet` (4,863,784 rows total,
  matches §0's post-cleanup count) confirms the shipped fix's claims exactly, no drift since the implementation
  commit.** `source=="odds_api"` slice (2,667 rows): `empty_confirmed`=2,661, `attempted_failed`=6 (same 6 dates —
  2019-01-23, 2019-12-12, 2020-02-06, 2020-04-21, 2020-04-23, 2020-04-27 — all `service_name=instruments-service`,
  `error_reason=PipelineModeSourceMismatchError`), `expected_unattempted`=0, `captured`=0. Dedup-key group-by
  (`date`,`venue`,`data_type`,`service_name`) within the odds_api slice: **0 duplicate groups.** Compared to §0 baseline
  (rows=2,667 / captured=0 / attempted_failed=6 / expected_unattempted=0): **identical — zero movement**, as expected
  for a documentation-only todo.
  - **Verdict: documented-equivalent residual, NOT the literal 0/0/0 bar** — the category does not hit the
    understat-standard literal-zero bar (6 `attempted_failed` rows remain), but per the 2026-07-13 implementation entry
    above this is the plan DoD's explicit "documented-equivalent residual" case, not a still-broken gap: the 6 rows are
    a historical, non-reproducible (`PipelineModeSourceMismatchError` — the current write-safety gate now blocks this
    exact mismatch class at write time, confirmed live in
    `instruments-service/scripts/ backfill_orphan_class_e.py`/`backfill_orphan_class_e_sports.py`), below-materiality
    (6-row) record of the gate correctly rejecting a mismatched odds_api write for the footystats-owned generic `ODDS`
    data_type — relabeling or erasing them would itself violate the honest-manifest rule
    (`codex/02-data/availability-manifest-and-data-status.md`). 0 dedup groups (clean). **Nothing left open on this
    todo; no further action warranted.**

- **2026-07-13 (slot-3, interactive session, correction to the api_football investigation's "453,961
  expected_unattempted is legitimate, no fix needed" verdict) — CONTRADICTED for the TEAMS subset (192,384 of the
  453,961, ~42%).** Operator asked a sharp follow-up question (pre-2020-unrun vs genuinely-no-fixture) that prompted a
  direct re-verify rather than trusting the aggregate claim. Live-manifest query
  (`gs://instruments-store-sports-prd-central-element-323112/_index/availability_index.parquet`,
  `source=api_football data_type=TEAMS`, 296,554 total rows): **`captured` rows split into TWO incompatible grains** —
  3,648 rows with BLANK `league_id` (`row_count` ≈ 621, a bulk daily bundle of ~621 teams across ALL leagues aggregated
  into one row/day) vs 100,498 rows with a POPULATED `league_id` covering only **33 distinct leagues** (~3,046
  rows/league, i.e. near-daily captures for those 33). The `expected_unattempted` enumerator generates one expected cell
  **per (league_id, date)** — 94 distinct leagues, 3,116 dates each (2018-01-01→2026-07-13, literally every day in
  range). **Overlap check: of the 94 EU leagues, only 33 have ANY non-blank-league_id captured row — 61 of the 94 EU
  leagues have LITERALLY ZERO per-league TEAMS captures across the entire 8.5-year window.** This is not "most cells are
  genuinely no-fixture" (TEAMS is a roster fact, not fixture-dependent, so it doesn't have "no fixture" off-days the way
  FIXTURES/STANDINGS do) — it is a **genuine, unaddressed capture gap for 61 specific (mostly second-tier) leagues'
  TEAMS data**, going back to 2018. Root cause not yet identified in this pass (candidates: the per-league TEAMS capture
  path was only ever wired for a 33-league subset, or the bulk/blank-league_id bundle path was meant to be the ONLY
  source of truth and the enumerator should not be generating per-league TEAMS expectations at all — needs code-level
  investigation of whichever orchestrator function drives per-league TEAMS capture vs the bulk bundle, and of
  `enumerate_expected_universe.py`'s TEAMS enumeration to see which grain it _should_ match). **This todo
  (`api_football deep investigation`) should NOT be considered closed on the TEAMS point** until this gap is root-caused
  and either (a) a real per-league TEAMS backfill ships for the 61 leagues, or (b) the enumerator is corrected to not
  expect per-league TEAMS grain if the bulk bundle is the intended sole source (decide-and-document, not a silent
  descope, per the external-data-always-available rule). Other data_types in the 453,961 total (ODDS
  82,749/FIXTURE_LINEUPS 47,282/FIXTURE_EVENTS 47,028/FIXTURE_STATS 36,677/PLAYER_STATS 26,363/INJURIES
  20,700/FIXTURES 778) were NOT re-verified in this pass — the original "legitimate" claim may hold for those, but given
  TEAMS was wrong, they should get the same direct-verification treatment (sample captured vs expected grain match)
  before being marked closed, not taken on the aggregate agent's word alone.
- **2026-07-13 (slot-3, interactive session) — MTDS vs MDPS `mdps_odds_horizon_bucket` row-count asymmetry, explained
  (operator question).** Operator asked why MDPS (109,638 captured rows) and MTDS (14,656) differ so much for what's
  "still odds, one just processed/bucketed." Direct comparison in the OTHER manifest
  (`gs://market-data-tick-sports-prd-central-element-323112/_index/availability_index.parquet`,
  `source= mdps_odds_horizon_bucket`): **both service_names cover the IDENTICAL 1,813 distinct dates, IDENTICAL date
  range (2020-06-06→2026-04-14), and IDENTICAL 38 leagues** — no coverage gap between them. The row-count difference is
  a GRAIN difference, not a gap: `market-tick-data-service` writes exactly one row per (date, league) with
  `row_count=1.0` uniformly (a coarse "did we ingest any odds tick for this league today" marker);
  `market-data-processing-service` writes multiple rows per (date, league) with `row_count` unpopulated (NaN) —
  consistent with one row per distinct horizon-bucket (e.g. per pre-kickoff time window) per match, the derived
  fine-grained product. ~7.5x ratio (109,638/ 14,656) is plausible for "several horizon buckets per match" at this
  league/date volume. **Not a bug** — same dates, same leagues, different write-grain for raw-ingest-marker vs
  derived-product. No further investigation needed on this specific question.

- **2026-07-13 (slot-3, IMPLEMENTATION dispatch — `mdps_odds_horizon_bucket: root-cause zero-ever-captured` P0 todo).
  Root cause confirmed exactly as the prior investigation concluded (manifest-bucket-routing split-brain); code fix
  shipped + a metadata backfill applied; TWO additional, deeper bugs discovered in the process and scoped out as
  follow-on todos rather than rushed.**
  - **Code fix shipped**: `market-data-processing-service@6907257e4`
    (`fix(sports): route mdps_odds_horizon_bucket manifest to instruments-store-sports`, pushed directly to
    `live-defi-rollout` per this session's established direct-push convention — `quality-gates.sh` green before commit).
    `reprocess_sports_odds.py` now has TWO separate bucket resolvers: `_resolve_bucket()` (raw-odds input + bucketed
    OUTPUT DATA — unchanged destination, stays `market-data-tick-sports-prd`, matches what `features-service`'s
    `read_odds_data`/`read_bucketed_odds` readers resolve) and a NEW `_resolve_manifest_bucket()` (the
    `ManifestWriter.catalogue_bucket`, now `resolve_bucket_name(kind="instruments-store", asset_group="sports")` — the
    SAME call the expected-universe enumerator uses). Only the manifest moved; no data bytes moved; the fix is a pure
    routing correction.
  - **A SECOND, independent bug found + fixed in the SAME commit** (in-file, same findings-triage rule): the
    pre-existing `_resolve_bucket()` itself was ALSO broken, unrelated to the manifest issue. It called
    `get_bucket_name("market-data-tick-sports", project_id=project)` — passing `project_id` explicitly. UTL's
    `get_bucket_name` (`core/cloud_constants.py:209`) SKIPS its yaml-SSOT env-tiering delegation whenever `project_id`
    is passed explicitly (a documented behavior — "the resolver reads project_id from env and doesn't accept a
    caller-supplied override") and silently falls through to a legacy no-env-tier shape
    (`market-data-tick-sports-{pid}`, missing `-prd-`) instead of the real bucket (`market-data-tick-sports-prd-{pid}`)
    — confirmed empirically: running the ORIGINAL unmodified function locally produced the wrong bucket name every time,
    in any environment (dev or prod), since `project_id` is NEVER `None` at this call site
    (`UnifiedCloudConfig().gcp_project_id or "test-project"` is always a non-empty string). Historical production runs
    (VM-tarball-deployed, `deployment-service/scripts/vm/launch-mdps-sports-bucket-vm.sh`) evidently ran an OLDER
    `unified-trading-library` snapshot where this branch behaved differently — a fresh checkout/redeploy today would
    have silently started writing real captures to a wrong, un-tiered, likely-nonexistent-index bucket. Fixed by
    switching to `resolve_bucket_name(cloud="gcp", kind="market-data", asset_group="sports")` directly — the same call
    MTDS's own `get_tick_data_bucket()` and features-service's `resolve_tick_data_bucket()` already use for this exact
    bucket. Verified locally post-fix: resolves to the correct, real, live
    `market-data-tick-sports-prd-central-element-323112`.
  - **Historical backfill applied** (metadata-only, no re-derivation): `instruments-service` (untracked, one-off)
    `scripts/migrate_orphaned_mdps_odds_horizon_bucket_rows_2026_07_13.py` — migrates the 124,294 orphaned
    `source=mdps_odds_horizon_bucket` rows (123,642 `captured` / 652 `empty_confirmed`) from
    `market-data-tick-sports-prd`'s manifest into `instruments-store-sports-prd`'s manifest. **Why a metadata copy, not
    a `--force` re-run**: re-running `reprocess_sports_odds.py --force` would re-invoke `_read_raw_odds()`, whose
    `_CANONICAL_PREFIX_TEMPLATES` expect a `data_source=ODDS_API` path segment — confirmed via live `list_blobs` probes
    (2026-05-10, 2026-06-24) that NO on-disk shape uses that segment (2026-05 layout uses per-bookmaker
    `venue={BOOKMAKER}`; 2026-06+ layout uses `venue=ODDS_API` with non-`ticks.parquet` filenames) — a `--force` re-run
    today would silently reclassify all 123,642 real captures as `empty_confirmed`, a regression. **Safety-verified
    before writing**: zero identity collision between the 123,968 distinct migrated (date, venue, data_type, timeframe,
    league_id) tuples and the 215,481 existing target rows (the enumerator's seed uses `venue=""` + UPPERCASE
    `data_type="ODDS_HORIZON_BUCKET"` + `timeframe=None` — a different, coarser grain than MDPS's own `venue=ODDS_API` /
    lowercase `data_type` / per-`T-*`-timeframe rows) — so this migration cannot create a new duplicate-dedup-key group
    (today's earlier `dedup_mtds_instruments_surface_duplicate_rows_2026_07_13.py` bug class). Dry-run confirmed the
    exact expected counts (124,294 eligible, 0 collisions) before `--apply`. Same accepted one-off convention as that
    script (plain `gcsfs` read/write, no generation-match — DRY-RUN default, `# Epic`/`# Lifecycle`/`# Delete-when`
    marker). **Concurrency note**: `instruments-service` had a live, uncommitted, in-progress WIP from a concurrent slot
    (the `api_football` todo's fix — `failure.py`/`process.py`/`process_completeness.py`/`api_football.py` + test) at
    the time this ran; only this script's own new file was staged/committed, the other agent's dirty files were left
    completely untouched (`git status` verified before and after).
  - **TWO deeper, separate bugs discovered and DELIBERATELY NOT rushed in this session (documented instead, per the "big
    finding → issue doc" rule + AUTONOMOUS_AGENT_RULES rule 11 blast-radius caution)**:
    1. **Expected-universe grain mismatch for `mdps_odds_horizon_bucket`** — even with the bucket now correct, the
       enumerator's 209,526-row `expected_unattempted` seed (coarse: `venue=""`, `data_type="ODDS_HORIZON_BUCKET"`
       uppercase, no `timeframe`, one row per (date, league_id)) will NEVER reconcile against MDPS's actual captured
       shard grain (`venue="ODDS_API"`, `data_type="odds_horizon_bucket"` lowercase, one row per (date, league_id,
       timeframe)) — confirmed zero identity overlap in a live dry-run. This means the coverage metric for this source
       will show BOTH ~209k `expected_unattempted` AND ~124k `captured` as entirely disjoint cells post-migration — real
       progress (real work now visible) but NOT a clean 100%-coverage story, because the "expected" side needs its own
       re-seed at the correct grain. This is a design-level fix to `enumerate_expected_universe.py`'s sports
       `mdps_odds_horizon_bucket` seeding logic, not a quick patch.
    2. **Raw-input path-template drift (MTDS on-disk convention has moved past the MDPS reader)** — `_read_raw_odds()`
       in `reprocess_sports_odds.py` has apparently been unable to find ANY current-shape raw odds data for a while
       (confirmed no matches for 2026-05 or 2026-06 dates); MTDS's actual on-disk sports odds layout has evolved
       (per-bookmaker `venue=` segments in 2026-05, meta `venue=ODDS_API` per-sport files in 2026-06+) without the
       reader's `_CANONICAL_PREFIX_TEMPLATES` being updated to match. This means FUTURE re-runs (even post-bucket-fix)
       may currently be unable to capture any NEW dates until this is fixed — a real, live pipeline-health risk,
       independent of the manifest-routing bug this session fixed. Needs careful cross-referencing of MTDS's exact
       current writer convention (`market_tick_data_service/engine/orchestrator/partitioned_writer.py`) against every
       historical layout era before a safe multi-template fix can ship (get it wrong and captures silently regress
       further). **Not attempted in this session** — flagged here + as a new todo below, per the workspace's
       blast-radius-before-fleet-change rule (this specific reader affects a currently-active, revenue-relevant sports
       ML pipeline; a wrong guess at the new prefix shape is worse than leaving it as a documented, precisely-scoped
       open item).
    3. **(Correction to this plan's own earlier `odds_api` conclusion, filed 2026-07-13 investigation-only dispatch
       above)**: that entry concluded `source=odds_api` is fully and correctly credential-gated/dead post-2020-06-06,
       based on querying ONLY `instruments-store-sports-prd`. A direct check of the OTHER manifest
       (`market-data-tick-sports-prd`) for `source=odds_api` during this session found **362,665 rows, 362,631
       `captured`** (`service_name` split `market-tick-data-service` 195,437 + `migrate-sports-canonical` 167,220 +
       `market-data-processing-service` 8), `written_at` spanning through **today** — i.e. the SAME manifest-bucket
       split-brain bug class affects the raw `odds_api` numerator too, at ~3x the row-count of
       `mdps_odds_horizon_bucket`. That prior entry's conclusion is **INCOMPLETE, not wrong on its own narrow evidence**
       (the credential-gated finding for the `ODDS_SNAPSHOT`/`ODDS_MOVEMENT`/`ARBITRAGE` derived sub-types still holds —
       those genuinely have 0 rows anywhere post-2020-06-06) — but the raw `trades`/`odds_api` capture itself is very
       much alive and simply invisible in the canonical manifest, same bug, much bigger blast radius. **This is a
       cross-repo, data-correctness "big finding"** — flagged here for the operator/next dispatch, not silently folded
       into this session's narrower `mdps_odds_horizon_bucket` fix (fixing MTDS's raw-capture manifest routing touches
       the SHARED, cross-asset-group `process_ticks()`/`_DateRunState.bucket` orchestrator used by cefi/defi/tradfi/
       sports/prediction alike — a substantially higher-blast-radius change than this session's isolated MDPS-script
       fix, requiring its own careful, dedicated pass per AUTONOMOUS_AGENT_RULES rule 11).
  - **New follow-on todos filed** (P1, not part of this session's scope, decide-and-document per autonomous rules —
    genuinely separate bodies of work, not a deferral of THIS todo which is fully closed):
    - `[DATA] P1. MTDS shared-orchestrator sports-manifest-bucket routing`: extend the same `sports → instruments-store`
      manifest-bucket exception to MTDS's own cross-asset-group raw-capture path
      (`engine/orchestrator/__init__.py::get_tick_data_bucket()` / `_DateRunState.bucket` / `manifest_finalize.py`'s
      `catalogue_bucket=state.bucket`) WITHOUT moving the actual tick-byte write path (mirror this session's
      `_resolve_bucket()` vs `_resolve_manifest_bucket()` split) — then migrate the 362,665 orphaned `odds_api` rows the
      same way. Requires careful audit of every `ManifestWriter`/preflight-lookup call site in the shared orchestrator
      (affects ALL asset_groups, not just sports) before shipping — full blast-radius proof required per
      AUTONOMOUS_AGENT_RULES rule 11.
    - `[DATA] P1. mdps_odds_horizon_bucket expected-universe grain realignment`: fix `enumerate_expected_universe.py`'s
      sports seeding for this source so `expected_unattempted` uses the SAME
      `(venue=ODDS_API, data_type=odds_horizon_bucket lowercase, timeframe=T-*)` grain MDPS actually writes, instead of
      the current coarse `(venue="", data_type=ODDS_HORIZON_BUCKET uppercase, no timeframe)` seed — required before this
      source can show a clean 0/0/0-style coverage number.
    - `[DATA] P1. reprocess_sports_odds.py raw-input prefix-template refresh`: reconcile `_CANONICAL_PREFIX_TEMPLATES`
      in `_read_raw_odds()` against MTDS's actual current on-disk sports-odds writer convention (multiple historical
      layout eras confirmed: `data_source=` never seen on disk; per-bookmaker `venue={BOOKMAKER}` circa 2026-05; meta
      `venue=ODDS_API` circa 2026-06+) — needed before any FUTURE `--force` re-run can safely capture new dates without
      silently regressing existing coverage.
  - **This todo (`mdps_odds_horizon_bucket: root-cause zero-ever-captured`) is DONE**: the manifest-bucket-routing root
    cause is fixed in code (not just data patched), the historical real captures are now visible in the canonical
    manifest, and every deeper follow-on discovery is filed as a scoped todo above rather than silently rolled into this
    fix or left undocumented.

- **2026-07-13 (slot-3, FINAL RE-VERIFY dispatch — footystats + soccer_football_info + transfermarkt + open_meteo
  residuals, post per-league-isolation-fix `instruments-service@746ce3e2`/`5b8cc6d0`): residual-closer
  (`sports_attempted_failed_residual_closer_2026_07_13.py`, PID 3247, `agentwork/sports_residual_fix_2026_07_13` branch)
  is STILL ACTIVELY RUNNING at read time — this is a mid-flight snapshot, NOT the closer's terminal state.**
  - **Consolidator-staleness caveat discovered**: the closer's OWN internal remaining-count checks were noisy this run —
    round-0 (pre-loop) read 0 attempted_failed for all 3 sources, round=1 verify read 61 total, round=2 verify read 266
    total (≈ the full pre-fix baseline 205+10+51) — a `ManifestConsolidatorStaleError` (consolidated blob >120s stale,
    forced per-VM-shard fallback) was live during the run's early reads (confirmed in a discarded first invocation's
    traceback), so the closer's per-round counts should not be read as a literal progress curve. A direct independent
    read taken THIS check found the consolidated blob freshly updated (17:53:54Z, age ~seconds) — used that fresh window
    for the numbers below, which are more trustworthy than the closer's own round logs.
  - **Fresh single-parquet read** (`read_availability_index`, 4,988,134 total rows — up from §0's 4,863,784 baseline,
    consistent with the separate mdps_odds_horizon_bucket backfill landing):
    - **footystats**: `attempted_failed`=200 (TimeoutError 174, phantom 15, ArrowTypeError 11) vs baseline 205
      (179/15/11) — only the TimeoutError count moved (179→174, 5 resolved so far); phantom+Arrow untouched.
      `expected_unattempted`=56, identical to baseline, 100% dated 2026-07-13 (today's legitimate rolling trailing-edge,
      self-closes next capture pass — unchanged conclusion from the investigation-only pass).
    - **soccer_football_info**: `attempted_failed`=10 (phantom), UNCHANGED from baseline, despite the closer's own log
      claiming `[sfi] processed=10 raised=0` — the per-VM-shard writes are buffered and only drain into the canonical
      index via the script's single explicit `flush_all_pending_buckets()` call AFTER the entire round loop exits (not
      yet reached while PID 3247 is alive), so this canonical read cannot yet show the SFI reprocessing's effect even if
      it succeeded. `expected_unattempted`=94, unchanged, 100% today's date (legitimate).

- **2026-07-13 (sub-agent, investigation-only dispatch — TEAMS 61-league gap root-cause, read-only, no code/data
  changes).** Full root-cause of the P0 todo "api_football TEAMS: root-cause + fix the 61-league per-league capture
  gap." **Conclusion: ONE code path, deliberately scoped too narrow (not two competing capture paths); the 61 leagues
  ARE api_football-covered; the blank-league_id bundle is a phantom manifest artifact, not a reusable data source; true
  backfill cost is ~549 API calls, not ~190k.**
  - **(1) One code path, not two.** `instruments_service/engine/orchestrator/sports_reference_core.py:138-216`
    (`_fetch_teams_and_standings`) is the ONLY production call site of `adapter.get_teams()` for api_football. It
    iterates `_orch.get_prediction_leagues()` (UAC `LEAGUE_REGISTRY` filtered to `classification=="Prediction"` —
    exactly 33 leagues, confirmed by counting `classification="Prediction"` in
    `unified-api-contracts/.../league_data_prediction.py`) and writes ONE per-league parquet per league via
    `teams_df.groupby("league_id")` → `_gated_sink_write(partition={"league": ...})`. The `else` branch (missing
    `league_id` column) explicitly **skips the write** with a warning ("data shape regression... Skipping write to keep
    manifest honest") — there is no branch in current code that CAN write a blank-`league_id` captured TEAMS row. Live
    GCS listing confirms the code matches reality:
    `gs://instruments-store-sports-prd.../sports_reference/by_date/ day=2026-07-13/pipeline_mode=batch_api_football/entity=teams/`
    contains exactly 33 `league=<X>/teams.parquet` objects, zero bare-path file.
  - **(2) Why only 33 — a scope mismatch between two functions in the SAME module, not a deliberate design split.**
    `sports_reference_core.py:113` (the module's OWN absence-recording helper, `_record_empty_for_uncaptured`) already
    correctly calls `_orch.get_expected_leagues_for_source("api_football")` with NO classification filter — the full
    94-league set (`get_expected_leagues_for_source` returns leagues where `"api_football" in league.data_sources`,
    optionally filtered by classification; `None` = all). UAC's `SPORTS_ENTITY_LEAGUE_COVERAGE["TEAMS"] = None`
    (`provider_league_ids.py:776`) explicitly documents TEAMS as "expected on all fixture dates" (no per-league
    restriction) — i.e. the ENUMERATOR/denominator side was deliberately built for the full 94-league universe. The
    CAPTURE loop three lines below in the same file was simply never widened to match — it still reads
    `get_prediction_leagues()` (Prediction-tier only), a leftover scoping choice. Verified the 33/61 split maps exactly
    to classification: 33 Prediction (captured) + 22 Features + 39 Reference = 94 (0 captures) — Features = mostly
    2nd-division domestic leagues (e.g. `EERSTE_DIVISIE`, `USL_CHAMPIONSHIP`, `J2_LEAGUE`), Reference = mostly
    cup/continental competitions (`FA_CUP`, `DFB_POKAL`, `UCL`, `COPA_LIBERTADORES`, etc, tier=0). This is a genuine,
    fixable capture-loop scoping bug, not an intentional two-tier design — decision: **(a) applies** (widen the capture
    path), not (b) (the enumerator is the one that's already correct).
  - **(3) API coverage check for the 61 — CONFIRMED covered, not an out-of-provider-coverage case.** Queried the live
    manifest for all api_football rows where `league_id` is one of the 61: FIXTURES has 27,843 `captured` rows,
    FIXTURE_STATS 6,229, FIXTURE_EVENTS 4,176, FIXTURE_LINEUPS 4,006, INJURIES 784, PLAYER_STATS 656 — spanning 60 of
    the 61 leagues. Api-Football is actively and successfully returning fixture-level and even player-level data for
    these same leagues; team-roster data (`/teams`) is a strictly more basic/available endpoint than lineups or
    per-player stats on that provider's API. **No evidence any of the 61 lack TEAMS coverage** — this should be typed as
    a real backfill target, not `EXPECTED_SOURCE_DOES_NOT_COVER_LEAGUE`. (Did not make a live manual API call to verify
    a specific league's `/teams` response directly — the indirect evidence via sibling data_types for the same leagues
    is strong enough to proceed with a backfill attempt; the implementing agent should treat any per-league API 4xx as a
    genuine `EXPECTED_SOURCE_DOES_NOT_COVER_LEAGUE` exception discovered during the backfill run, not assume upfront.)
  - **(4) True backfill scope — season-grain, NOT date-grain: ~549 real API calls, not ~190k.**
    `adapter.get_teams(league_id, season=None)` (`api_football.py:610`, `base.py:247`) is a **season-keyed** call — a
    team roster is fetched per season, not per day. The current orchestrator merely happens to invoke it once per
    calendar day inside the daily loop (with same-day, in-memory caching via `_orch._cached_teams_df`), which is why the
    33 already-wired leagues show ~3,046 near-daily rows each over 8.5 years for data that changes maybe twice a season.
    The literal 61-leagues × 3,116-dates naive estimate (~190k cells) is NOT the real API cost: the true minimum is ~61
    leagues × ~9 seasons (2018–2026) ≈ **549 real `get_teams` calls**. Each season's single roster payload can then be
    replicated to populate every date-row in that season's manifest window (many cheap manifest WRITES, zero incremental
    API cost per day) — mirroring the existing per-league write shape so the resulting per-day row count matches the 33
    already-canonical leagues' pattern. (Whether the expected-universe itself SHOULD be date-grain for TEAMS at all,
    given it's genuinely season-grain data, is a separate, smaller follow-up worth flagging to the enumerator owner —
    not blocking this backfill.)
  - **(5) Blank-`league_id` bulk bundle (3,648 rows, ~621 teams/day) — CONFIRMED phantom, NOT a reusable/alternate
    source of truth.** Cross-checked a `capture_status=captured` blank-league_id TEAMS row dated **2026-07-13 (today)**
    against live GCS: zero bare-path `entity=teams/teams.parquet` object exists for that day at either the canonical
    (`pipeline_mode=` prefix) or legacy path — the manifest claims captured, no parquet exists anywhere. This is the
    same `phantom_captured_no_parquet_at_canonical_path` class already documented elsewhere in this plan for other
    api_football data_types, just not yet caught by the phantom classifier for this specific (blank-league_id, TEAMS,
    captured) shape. Corroborating evidence: 533 distinct `attempted_at`/`written_at` timestamps across only 3,648 rows
    (repeated re-stamping/rebuild passes touching the same historical rows, not a live daily producer), and dates
    running back to 2014-01-01 — three years before api_football's own `SOURCE_COVERAGE_START` of 2018-01-01. **There is
    no nested per-league structure to unpack** — it is not real captured data at all, so it cannot be repurposed to
    synthesize the missing 61 leagues' rows without fresh API calls. Recommend: (i) do NOT treat it as ground truth or
    attempt to "unpack" it; (ii) re-type these 3,648 rows via the existing
    `scripts/reconcile_phantom_manifest_rows_all.py` tooling (same pattern already applied to the footystats/SFI/weather
    phantom rows elsewhere in this plan) so `captured` → `attempted_failed`/typed-absence, not left as a false-positive
    captured record; (iii) once retyped, this row shape can be deleted from any future "is TEAMS legitimate" sampling.
  - **(6) VM launcher + backfill driver pattern.** `deployment-service/scripts/vm/` sports-registered launchers (grep
    confirmed no hand-rolled name needed): `launch-sports-is-gap-fill.sh` (paired with
    `instruments-service/scripts/query_sports_is_gaps.py`) is the existing per-league-scoped gap-fill launcher already
    recommended elsewhere in this plan for other api_football residuals — reuse it for the TEAMS backfill rather than
    writing a new launcher. `launch-sports-entity-sweep-vm.sh` / `launch-sports-full-sweep-vm.sh` are the other
    sports-registered prefixes available if a full-entity sweep shape fits better. Existing per-league driver code
    patterns to base the TEAMS-specific backfill script on:
    `instruments-service/scripts/backfill_per_league_record_empty.py` and
    `instruments-service/scripts/migrate_sports_per_league.py` (both already iterate `get_prediction_leagues()` in the
    same per-league shape the TEAMS fix needs, just widened to the full 61-league set — `SOURCE_COVERAGE_START` gates
    the pre-2018 floor automatically since `_fetch_teams_and_standings` is called from the daily `sports_reference.py`
    orchestrator entrypoint that already respects it).
  - **Recommended fix for the implementing agent (in order): (i)** widen the capture loop at
    `sports_reference_core.py:153` from `_orch.get_prediction_leagues()` to
    `_orch.get_expected_leagues_for_source("api_football")` (matching the module's own absence-recording helper three
    lines above) — this is the root-cause fix, one line; **(ii)** run a season-grain backfill (~549 API calls) for the
    61 newly-in-scope leagues across 2018–2026, writing per-date manifest rows from each season's single payload the
    same way the daily loop already does going forward; **(iii)** retype the 3,648 blank-`league_id` phantom rows via
    `reconcile_phantom_manifest_rows_all.py`; **(iv)** re-verify the live manifest shows 94 distinct captured leagues
    for TEAMS with 0 remaining zero-capture leagues. This todo
    (`api_football TEAMS: root-cause + fix the 61-league per-league capture gap`) is root-caused and ready for
    implementation — not yet flipped `[x]` (no code/data change made in this investigation-only pass, per dispatch
    scope).
    - **transfermarkt**: `attempted_failed`=0 (unchanged, already clean), `expected_unattempted`=47, unchanged, 100%
      today's date (legitimate) — no closer work targets this source (it was never in scope, already clean at baseline).
    - **open_meteo (weather)**: `attempted_failed`=51 (phantom), UNCHANGED from baseline — same buffered-write
      explanation as SFI (closer log shows `[weather] processed=51 raised=0` mid-run, not yet drained).
    - **Dedup-key groups**: 0 duplicate groups for all 4 sources when keyed correctly on
      `(date, venue, data_type, league_id, service_name)` — an initial pass of this check that omitted `league_id`
      mis-flagged thousands of "duplicate" groups (footystats 9,176 / SFI 2,391 / transfermarkt 3,161 / weather 2,840);
      re-run with `league_id` included (these sources are league-grain, not venue-grain, so `venue` is blank and cannot
      stand in for the shard key alone) confirmed all 4 sources are genuinely dedup-clean. Documenting this here so the
      next verifier doesn't re-trip the same false positive.
  - **Verdict: NOT YET at the understat-standard bar for footystats/SFI/weather — the closer is mid-run, buffered writes
    haven't drained to the canonical index, and only 5 of 236 targeted attempted_failed rows show as resolved in THIS
    read.** transfermarkt was already clean at baseline and remains so (0/47, both legitimate). Recommend a follow-up
    re-verify once PID 3247 reaches its `EXPLICIT PRE-EXIT DRAIN`/`FINAL TALLY` log lines (or exits) — expect the drain
    to reveal a materially different (likely much closer to 0) attempted_failed count for footystats/SFI/weather once
    the buffered per-VM-shard writes are visible in a subsequent fresh read. Not marking any of the 4 residual todos
    `[x]` this pass — the fix's effect is not yet observable end-to-end.

- **2026-07-13 (slot-3, FINAL RE-VERIFY dispatch — fresh single-parquet read post-fix).** Re-read
  `gs://instruments-store-sports-prd-central-element-323112/_index/availability_index.parquet` fresh (4,988,134 total
  rows now, up from the §0 baseline's 4,863,784 — expected, reflects the migration write).
  `source=mdps_odds_horizon_bucket` now: **339,775 rows** (215,481 baseline + 124,294 migrated = exact match, confirms
  clean arithmetic, no double-write). `capture_status` breakdown: `captured` **123,642** (was 0), `empty_confirmed`
  **6,607** (5,955 pre-existing + 652 migrated — also exact match), `attempted_failed` **0** (unchanged),
  `expected_unattempted` **209,526** (unchanged — sum of all four = 339,775, fully reconciles, no unaccounted rows).
  `service_name` split: `instruments-service` 215,481 (untouched original enumerator seed),
  `market-data-processing-service` 109,638 + `market-tick-data-service` 14,656 = 124,294 (exactly the migrated set).
  **Duplicate-dedup-key check**: grouping on the coarse identity (date, venue, data_type, timeframe, league_id) alone
  surfaces 326 apparent "duplicate" groups, but re-grouping on the TRUE dedup key (same tuple **+ service_name**, per
  this session's established manifest-consolidator convention) finds **0** true collisions — the 326 are legitimate rows
  from two different `service_name`s (`market-data-processing-service` + `market-tick-data-service`) independently
  writing the same coarse identity, not duplicates. **Verdict: does NOT meet the understat-standard literal 0/0/0 bar,
  but the residual is fully explained and already documented, not still-broken.** `attempted_failed=0` and 0 true dedup
  collisions are clean; the 209,526 `expected_unattempted` residual is the already-filed P1 "expected-universe grain
  realignment" follow-on (the enumerator's coarse seed grain — `venue=""`, uppercase `data_type`, no `timeframe` —
  structurally cannot reconcile against MDPS's actual captured grain — `venue=ODDS_API`, lowercase `data_type`,
  per-`T-*` `timeframe`) — a known, separately-scoped design fix, not an oversight of this fix. The core
  "zero-ever-captured" defect is conclusively resolved: 123,642 real historical captures are now visible in the
  canonical manifest, root-caused in code (not just patched), zero data-integrity regressions (no new duplicate-dedup
  groups, arithmetic fully reconciles). No further action taken this dispatch — re-verify only, per task scope.

- **2026-07-13 (slot-3, IMPLEMENTATION dispatch — root-cause + code fix for the api_football `attempted_failed` /
  blank-`data_type` classes, todos "api_football deep investigation" + "api_football: fix root causes + re-attempt
  failed cells").** Root-caused all four classes precisely (some conclusions **refine/correct** the prior
  investigation-only pass) and shipped verified code fixes. All changes QG-green (`ruff` clean, `basedpyright` no new
  errors beyond pre-existing baseline noise, 1202 relevant instruments-service unit tests pass, targeted UAC tests
  pass) + functionally verified via direct isolated-function assertions (see below) — NOT via a full historical
  re-attempt (see "Deferred" below).

  - **(c) blank-`data_type` `UNCLASSIFIED_ADAPTER_ERROR` (461) — CONFIRMED + FIXED.** Root cause: the GENERIC
    CeFi/TradFi-shaped venue-grain shard-completeness gate (`process_completeness.py::_completeness_and_retry` /
    `_finalize_completeness`) treats sports pseudo-venue names (`API_FOOTBALL`, `FOOTYSTATS`, `UNDERSTAT`,
    `TRANSFERMARKT`, `SOCCER_FOOTBALL_INFO`, `OPEN_METEO`) as literal venues in `active_venues`/`expected_venues`. 5 of
    these 6 (all except `API_FOOTBALL`) are ENRICHMENT-ONLY — fetched in stage 7, never populate `counts` (this stage's
    `written_venues`), so they permanently land in `missing_shards` and the generic corrective write
    (`row_key={"date","venue"}`, no `data_type`) stamps a blank-`data_type` row that can never reconcile against any
    real sports cell (confirmed via direct manifest sample: all 461 blank rows' `venue` ∈ {FOOTYSTATS, OPEN_METEO,
    SOCCER_FOOTBALL_INFO, TRANSFERMARKT, UNDERSTAT} — never API_FOOTBALL). **Fix**: excluded these 5 names from
    `expected_venues` (reusing `process_write.py`'s existing `_NON_VENUE_GRAIN_VENUE_NAMES` SSOT frozenset, which
    already excludes them from venue-grain EU-seeding — same-source-of-truth for both numerator and denominator now).
    `API_FOOTBALL` itself is DELIBERATELY KEPT checkable (it IS genuinely venue-grain here — its top-level FIXTURES
    fetch runs in this same stage-4 fetch) — removing it too would silently drop the only safety net catching a total
    API_FOOTBALL fetch failure during a combined `asset_groups=["ALL"]` run (where `_fixtures_fetch_failed`'s
    zero-records branch never fires because cefi/tradfi/defi still produce records). When `API_FOOTBALL` IS genuinely
    missing, `_finalize_completeness` now maps it to `row_key={"date","data_type":"FIXTURES"}` instead of a blank
    `data_type` — mirroring the existing `process_preflight.py::_build_expected_entities` convention
    (`"FIXTURES" if v == "API_FOOTBALL" else v`) that already existed elsewhere in this codebase for exactly this remap.
    **Files**: `instruments-service/instruments_service/engine/orchestrator/process_completeness.py`.

  - **(b) FIXTURES `FIXTURES_FETCH_FAILED` (665) — ROOT-CAUSED (corrects/extends the prior investigation's "not yet
    root-caused" note) + FIXED.** The write site IS honest
    (`process_zero_records.py::_zero_sports_empty_fixture_markers` — correctly keys
    `row_key={"date","data_type":"FIXTURES","league_id":...}`, not a data-integrity bug per se). The BUG is upstream, in
    the boolean that decides whether a zero-fixture day is a genuine fetch failure: `process.py::_fixtures_fetch_failed`
    returns `True` whenever ANY member of `active_venues` is absent from `non_error_venues` (the stage-4 URDI fetch's
    per-venue success set) — but `active_venues` for a sports run also carries the same 5 enrichment-only pseudo-venues
    from (c) above, which are NEVER part of the stage-4 fetch and so can NEVER appear in `non_error_venues`, regardless
    of whether `API_FOOTBALL`'s actual fixtures fetch succeeded. Net effect: on every genuinely-empty (legitimate
    no-fixture) day, this check FALSELY reported "fetch failed" the moment `active_venues` included more than just the
    fixtures-fetching venue — converting the correct `empty_confirmed(EXPECTED_NO_FIXTURE)` outcome into
    `attempted_failed(FIXTURES_FETCH_FAILED)` for EVERY prediction league in one shot (matches the observed data
    exactly: 665 rows cluster into 144 distinct `attempted_at` runs, each run flipping MULTIPLE leagues simultaneously —
    a single false trigger per run, not per-league organic failures). **Fix**: `_fixtures_fetch_failed` now only checks
    venues that actually participate in the stage-4 fetch — excludes `_NON_VENUE_GRAIN_VENUE_NAMES - {"API_FOOTBALL"}`
    before the membership check (keeps `API_FOOTBALL` itself checkable, since a genuine `API_FOOTBALL` fetch failure IS
    still a real fixtures-fetch failure). Verified directly:
    `_fixtures_fetch_failed(active_venues=[...6 pseudo-venues...], non_error_venues={"API_FOOTBALL"}, skip_urdi=False)`
    → `False` (post-fix; was a false `True` pre-fix), and `_fixtures_fetch_failed(..., non_error_venues=set(), ...)` →
    `True` (genuine API_FOOTBALL failure still correctly detected). **Files**:
    `instruments-service/instruments_service/engine/orchestrator/process.py`.

  - **(a) INJURIES `ApiFootballResponseError` (1,642 total, 1,600 on INJURIES specifically) — TWO real bugs found, both
    fixed (this SUPERSEDES the prior investigation's single "misclassification" framing — the misclassification is real
    but not the primary defect for INJURIES specifically):**
    1. **CONFIRMED live-API check**: manually called the real API-Football `/injuries?date=...` and `/status` endpoints
       with the live production key (`api-football-api-key` secret) for both a data-rich date (2024-05-15, 140 results)
       and a sparse date (2019-03-10, 0 results) — both returned clean `errors: []` envelopes, no plan/token/quota
       restriction on INJURIES today (`Custom300` plan, 300k/day, 6,112 used at check-time). This DISPROVES the prior
       investigation's "likely a plan/entitlement restriction on INJURIES" hypothesis — the account has full INJURIES
       access.
    2. **The REAL bug: `api_football.py::get_injuries` SILENTLY SWALLOWS hard fetch failures into an empty list**,
       unlike its sibling `get_teams`/`_fetch_season_fixtures_with_raw` (which correctly `raise` after
       `_emit_fetch_failed`). `get_injuries` is DATE-WIDE (single call returns ALL leagues' injuries for a date) —
       unlike the 4 genuinely per-fixture methods that share its exact try/except shape (where swallowing IS correct,
       shard-isolation behavior — a single fixture's failure shouldn't fail the whole date), `get_injuries` has no
       per-shard granularity to protect. Swallowing here silently converted ANY hard failure (network, timeout, a
       genuine future plan/token error) into a false "0 injuries, honest absence" (`empty_confirmed`) for the WHOLE date
       — the exact "silent-empty manifest bug" `instruments-service@0db24503` (2026-06-21) fixed for the venue -fetch
       path, left unfixed here. This means the manifest CANNOT currently distinguish a genuine zero-injuries day from a
       masked hard failure for INJURIES. (The historical 1,600 `ApiFootballResponseError` rows themselves are a
       SEPARATE, already-resolved artifact — see "historical-timestamp note" below; they predate/bypass this swallow bug
       via a different code path or a stale migration rewrite, not something this fix needs to explain away.) **Fix**:
       `get_injuries` now re-raises after `_emit_fetch_failed` (matches `get_teams`'s pattern exactly) so a hard failure
       correctly surfaces as `attempted_failed` via the caller (`sports_reference_core.py::_fetch_injuries`'s own
       `except` block), never a silent false-empty.
    3. **Misclassification (the prior investigation's original finding) — ALSO fixed, additively.**
       `failure.py::_classify_adapter_failure` fed `type(exc).__name__` (literal `"ApiFootballResponseError"`) into UAC
       `classify_venue_error`, which is keyed by HTTP/domain codes — never matched, always fell back to the raw class
       name. Fixed: `ApiFootballResponseError` now carries a real `error_key` attribute (the raw envelope error-dict's
       own key — `"plan"`/`"token"`/`"requests"`/`"rateLimit"` — extracted in `_raise_on_api_errors`);
       `_classify_adapter_failure` prefers it (via duck-typed `getattr`, zero risk to every OTHER venue this function
       classifies for) before falling back to the class name. Added the 3 corresponding UAC
       `VENUE_ERRORS_SPORTS["api_football"]` entries (`"plan"`/`"token"`/`"requests"`) so `classify_venue_error` can now
       actually resolve a real classification for future hard failures (previously impossible — nothing in this codebase
       ever produced a code matching the table's pre-existing HTTP-status/`FREE_PLAN_DATE_LIMIT`-style entries;
       confirmed via a repo-wide grep, 0 hits).
    - **Historical-timestamp note (why the OLD 1,600 rows exist despite current code never being able to produce them
      via `get_injuries` alone)**: only 3 distinct `attempted_at` values across all 1,642 rows, and the blank-`venue`
      rows from (c) share the EXACT same microsecond-precision timestamp pattern as a single shared `_failed_attempt_ts`
      computed once per date-shard's completeness-gate call — strong evidence these are migration/rebuild-pass re-stamps
      (a bulk rewrite bumping `attempted_at` to "now" while carrying forward an old `error_reason` verbatim), not fresh
      in-flight failures reproducing today. Not fully re-traced to the exact historical commit that could have produced
      the original `ApiFootballResponseError` via `get_injuries` (budget) — immaterial to the fix either way: whatever
      the historical mechanism, the CURRENT code's two real bugs (silent swallow + misclassification) are now both
      closed, and the stale rows are covered by the re-attempt follow-up below.
    - **Files**: `instruments-service/instruments_service/reference_data/adapters/sports/adapters/api_football.py`
      (`get_injuries` re-raise fix, `ApiFootballResponseError.error_key`, `_raise_on_api_errors`),
      `instruments-service/instruments_service/engine/orchestrator/failure.py` (`_classify_adapter_failure`),
      `unified-api-contracts/unified_api_contracts/canonical/crosscutting/errors/sports.py` (3 new
      `VENUE_ERRORS_SPORTS["api_football"]` entries), `instruments-service/tests/unit/test_sports_http_adapters.py` (2
      tests updated to assert propagation instead of the old swallow-to-`[]` behavior — this was itself encoding the bug
      as "intended", per governance rule "if you encounter errors... never mark completed" this required a genuine
      behavior-change test update, not a mechanical adjustment).

  - **(d) `phantom_captured_no_parquet_at_canonical_path` (487) — ROOT-CAUSED, no code fix needed (this is NOT a live
    write-path bug).** `phantom_captured_no_parquet_at_canonical_path` is written EXCLUSIVELY by the dedicated
    reconciliation tooling (`scripts/reconcile_phantom_manifest_rows_all.py` et al.), never by the live orchestrator —
    confirmed via repo-wide grep (every hit is in a `scripts/reconcile_*`/`diagnose_*` one-off, none in
    `engine/orchestrator/`). These 487 rows are the CORRECT, HONEST output of that tooling detecting a previously
    mis-stamped `captured` row with no real parquet at its canonical path and re-flagging it `attempted_failed` so the
    gap is visible and re-attempted — exactly the tool's designed job, not a fresh defect. All 487 share the identical
    `attempted_at=2026-07-13T16:24:30.871968+00:00` (a single reconciliation pass), corroborating the same
    single-run-bulk-restamp pattern as (a)'s historical-timestamp note above — very plausibly the SAME systemic incident
    (whatever caused a batch of writes to fail mid-flight got caught by this same reconciliation run). **No further code
    fix filed** — the correct next step is simply re-attempting these specific cells (covered by the re-attempt
    follow-up below), not a new code change.

  - **(3) 8,766 non-instruments-service rows — RESOLVED.**
    - `fill-missing-player-stats` (8,678 rows): CONFIRMED sanctioned one-off (`scripts/fill_missing_player_stats.py`
      carries proper `# Epic`/`# Lifecycle`/`# Delete-when` markers, calls the same orchestrator fetch +
      `ManifestWriter` path with a deliberate, documented `service_name` override) — left as-is, not a bug.
    - **88 `market-tick-data-service` orphans — FIXED via direct canonical rewrite** (same safe pattern as
      `instruments-service/scripts/dedup_mtds_instruments_surface_duplicate_rows_2026_07_13.py`: read live index,
      confirm no canonical twin at the real identity, DIRECT REWRITE — never a shard-merge write, which cannot collapse
      a `service_name`-keyed dedup group). New one-off script
      `instruments-service/scripts/restamp_orphan_mtds_player_stats_rows_2026_07_13.py` (Epic/Lifecycle/Delete-when
      markers per `codex/06-coding-standards/script-homes.md`), dry-run-by-default, `--apply` re-verifies at run time
      (re-derives the twin-check live rather than trusting the prior investigation's numbers) before writing. Ran
      dry-run (confirmed 88 eligible, 0 excluded) then `--apply`: **all 88 rows re-stamped
      `service_name: market-tick-data-service → instruments-service`, `asset_group: "" → "sports"`. Verified post-apply:
      0 remaining `market-tick-data-service`+`api_football` rows in the live manifest.**

  - **Verification performed (this dispatch)**: `instruments-service` — `ruff check` clean on every changed file;
    `basedpyright` shows zero NEW errors (all pre-existing errors confirmed via `git diff` hunk-location cross-check to
    be outside every line range I touched); full targeted pytest run
    (`-k "completeness or sports or process or orchestrator or failure"`) — **1202 passed, 0 failed**; the 2 updated
    adapter tests independently re-run in isolation (68 passed in `test_sports_http_adapters.py`); 2 direct
    isolated-function assertions proving both the `_fixtures_fetch_failed` false-positive elimination AND the
    `process_completeness` pseudo-venue exclusion (both shown above). `unified-api-contracts` — `ruff`/`basedpyright`
    clean, targeted `pytest -k "sports and error"` 17 passed. Full repo `quality-gates.sh` run TWICE with
    `QG_SENTINEL_DISABLE=true` (first run pre-refinement, second post-refinement) — both show the ONLY hard-gate failure
    (`STEP 5.95` TID251 ratchet, `reconcile_lending_indices_phantom.py:88`) is **conclusively unrelated to this work**:
    that file has zero uncommitted diff (`git diff --stat` empty, last real commit 2026-06-23) and the actual
    over-baseline count is traced to a DIFFERENT, untracked, foreign file
    (`scripts/cefi_legacy_path_dedup_2026_07_13.py`, mtime ~18:35, clearly another concurrent agent's live in-progress
    WIP in this shared checkout, alongside a second untracked foreign file
    `scripts/migrate_orphaned_mdps_odds_horizon_bucket_rows_2026_07_13.py`) — left untouched per the multi-agent "never
    edit unfamiliar/untracked files" hard rule; not staged, not committed, not fixed by me (out of scope, not mine,
    another agent's live WIP).

  - **Deferred work after 2026-07-13 (full historical re-attempt of the stale failed cells)**: the 4 fixes above stop
    the bugs from RECURRING going forward, but the ~3,257 EXISTING `attempted_failed` rows (plus the 461 blank-`venue`
    rows, now correctly excluded from future writes but still sitting in the manifest as-is) are historical artifacts
    that need a genuine re-fetch/re-verify pass to actually resolve, not just a code fix. This is a real, bounded
    infra-scale operation (many historical (date, league) shards spanning 2017-2026, live API calls against the
    `Custom300` plan, 300k/day quota) — appropriately a dedicated backfill VM run (mirror
    `deployment-service/scripts/vm/launch-sports-is-gap-fill.sh`, per this plan's own §"(6) VM launcher + backfill
    driver pattern" note elsewhere), not something to run ad hoc inline in an interactive dispatch. NOT run this session
    — tracked here as the concrete next step for the "final re-verify" todo below. The blank-`venue`/blank- `data_type`
    rows and the phantom rows (d) do not need re-fetching per se (they were never real failures in the live-data sense)
    — a manifest-level cleanup pass (re-typing/removing the now-provably-stale rows) would suffice for those, while
    INJURIES/FIXTURES genuinely benefit from a live re-attempt now that the false-positive triggers are fixed.

  - **Also NOT in scope for this dispatch (flagging, not fixing)**: the NEW "api_football TEAMS: root-cause + fix the
    61-league per-league capture gap" todo (added by a concurrent investigation elsewhere in this same plan) is a
    separate, already fully root-caused, real capture gap — unrelated to the 4 classes this dispatch was scoped to fix.
    Left entirely untouched; that todo's own recommended one-line fix + backfill plan stands as written.

  - **Commits (this dispatch)**:
    - `instruments-service` —
      `fix(sports): api_football root-cause fixes — blank-data_type completeness-gate leak, FIXTURES false-positive fetch-failed, INJURIES silent-swallow + misclassification`
      (process_completeness.py, process.py, failure.py, api_football.py, test_sports_http_adapters.py) +
      `scripts/restamp_orphan_mtds_player_stats_rows_2026_07_13.py` (new one-off, applied).
    - `unified-api-contracts` —
      `fix(sports): add raw envelope-key VENUE_ERRORS_SPORTS entries for api_football (plan/token/requests)`.

- **2026-07-13 (slot-3, VERIFY dispatch — final re-verify for `api_football`, todo "api_football: final re-verify").**
  Fresh single-parquet re-read of the live manifest (`instruments-store-sports-prd...` bucket,
  `_index/availability_index.parquet`, 4,988,134 total rows; transient `FileNotFoundError` on first read mid a
  consolidator rewrite at `18:06:01Z`, succeeded on immediate retry — not a data issue). **api_football slice: 2,518,571
  rows** (vs baseline 2,518,940 — small net drift from ongoing organic activity, not this fix).
  - **`attempted_failed`: 3,257 — UNCHANGED from the §0 baseline, identical breakdown** (INJURIES 1,946 / FIXTURES 665 /
    blank-`data_type` 461 / PLAYER_STATS 74 / FIXTURE_STATS 46 / FIXTURE_LINEUPS 30 / TEAMS 24 / FIXTURE_EVENTS 11;
    `error_reason` confirms `ApiFootballResponseError` 1,642, `FIXTURES_FETCH_FAILED` 665,
    `phantom_captured_no_parquet_at_canonical_path` 487, `UNCLASSIFIED_ADAPTER_ERROR` 461). This is **expected, not a
    regression** — the shipped fix stops the 4 bug classes from RECURRING going forward; it never claimed to
    retroactively clear the pre-existing rows (documented as deferred backfill-VM work in the IMPLEMENTATION entry
    above). Confirms no drift either direction since the fix landed.
  - **`expected_unattempted`: 452,985** (vs baseline 453,961, -976 — consistent with ongoing organic captures converting
    cells, not fix-driven; the TEAMS 61-league gap this bucket partly represents is still its own open P0 todo above,
    not yet fixed).
  - **Blank-`data_type` rows (any status): 583 total** — 461 `attempted_failed` (unchanged, pre-fix legacy rows) + 122
    NEW `empty_confirmed` rows, `venue` ∈ {API_FOOTBALL, FOOTYSTATS, OPEN_METEO, SOCCER_FOOTBALL_INFO, TRANSFERMARKT,
    UNDERSTAT} — confirms the `process_completeness.py` fix IS live and correctly routing the 5 enrichment pseudo-venues
    to `empty_confirmed` now instead of minting new blank-`data_type` `attempted_failed` rows (0 new blank-`data_type`
    failures since the fix shipped).
  - **Duplicate dedup-key groups (identity = date + source + data_type + service_name + league_id + fixture_id, per the
    understat precedent's "present optional dims" rule): 39,222 groups / 78,738 rows involved** — NOT part of the
    original §0 table (which only tracked rows/captured/attempted_failed/expected_unattempted) and NOT something this
    dispatch's fix touched. Root-caused via sampling (e.g. `2018-01-01/FIXTURES/A_LEAGUE`): each group is an OLD
    superseded row (an earlier `empty_confirmed`/`attempted_failed` write) sitting alongside a NEWER `captured` row from
    the same `attempted_at=2026-07-13T16:24:30.871968Z` reconciliation pass noted in finding (d) above — i.e. the
    reconciliation tooling's re-attempt writes are landing correctly but the manifest consolidator, per the
    already-established precedent, does not remove the stale superseded row on a shard-merge write; only a direct
    canonical rewrite does. This is a **pre-existing manifest-hygiene residual, not a new defect and not introduced by
    today's fix** — same class as the 88 MTDS orphans fixed earlier this session, scoped as follow-up cleanup rather
    than in this VERIFY pass.
  - **Verdict: does NOT yet meet the understat-standard 0/0/0 literal bar.** All three residuals are
    **documented/explained, not silently-broken**: `attempted_failed` (3,257) is a known, bounded, already-scoped
    backfill-VM re-attempt (deferred by design, confirmed unchanged not regressed); `expected_unattempted` (452,985) is
    substantially the still-open TEAMS-gap investigation plus a legitimate could-exist-universe seed; the 39,222
    duplicate groups are stale-superseded rows needing a direct-rewrite cleanup pass (same fixable pattern as the MTDS
    orphans). The 4 shipped code fixes are confirmed WORKING (0 new blank-`data_type` failures, 0 new false-positive
    FIXTURES_FETCH_FAILED since ship) — this category is **code-complete but not yet manifest-clean**; closing to a
    literal 0/0/0 requires the deferred backfill-VM re-attempt + a canonical dedup-rewrite pass, both already tracked as
    open todos in this plan.

- **2026-07-13 (slot-3, AUDIT dispatch, read-only — MTDS shared-orchestrator sports-manifest-bucket routing, full
  call-site enumeration BEFORE any code change).** Confirms the MDPS-sibling split-brain bug also exists in MTDS's
  shared cross-asset-group orchestrator (`market-tick-data-service/market_tick_data_service/engine/orchestrator/`).
  - **Resolver + call sites (file:line)**:
    1. `__init__.py:768` `get_tick_data_bucket(config, asset_group, test_aware)` — the single resolver; delegates to
       `get_market_data_bucket(ag)` (line 825) or, for `prediction`,
       `resolve_bucket_name(kind="market-data-tick-prediction")` (line 815; deliberately PROD-only even under
       `test_aware`). No asset_group carve-out exists today — sports is NOT special-cased.
    2. `__init__.py:666` — early-return (no active venues) branch calls
       `get_tick_data_bucket(_config, asset_group=_primary_ag, test_aware=True)` and feeds it straight into
       `_emit_non_trading_day_expected_empties(...)` → `ManifestWriter(catalogue_bucket=bucket)` at `__init__.py:446`
       (def at 432) — a 2nd, independent manifest-WRITE call site (EXPECTED_* non-trading-day sentinels).
    3. `__init__.py:679` — the primary resolution:
       `_bucket = get_tick_data_bucket(_config, asset_group=primary_asset_group, test_aware=True)`, stored once as
       `_DateRunState.bucket` (ctor arg `__init__.py:696`, field `_state.py:116`) and reused for the WHOLE date-run
       across 5 consumers:
       - `manifest_finalize.py:573-575` `ManifestWriter(catalogue_bucket=state.bucket, batch_size=500)` — **the PRIMARY
         manifest-write call site** (captured/failed/sentinel rows for the date; this is the one the MDPS-fix precedent
         maps onto).
       - `__init__.py:706` → `_run_preflight_availability_check(state, _bucket, force)` →
         `read_availability_index(bucket)` at `__init__.py:517` — manifest READ (skip-if-fresh preflight); MUST also
         carry the carve-out or preflight will keep reading the OLD (wrong) bucket after the write moves and never see
         prior sports captures → perpetual re-fetch.
       - `__init__.py:707` → `_run_preflight_guards(_bucket, primary_asset_group, _config, force)` →
         `_check_sports_v9_columns(bucket, config)` (`venue_fetch.py:161`, sports-only schema guard, internally calls
         `read_availability_index(bucket)`) and `assert_consolidator_healthy(bucket)` (UTL
         `manifest_writer/_state.py:365`) — both manifest-health reads that must follow the same carve-out for sports.
       - `venue_fetch.py:395` (`_process_venue`, CeFi/DeFi/TradFi/Prediction) and `venue_fetch.py:590` (sports-specific
         venue-write helper) both do `_bucket = state.bucket` → feed `PartitionedTickWriter(bucket=_bucket, ...)` →
         `partitioned_writer.py:207` `StreamingParquetWriter(bucket=self._bucket, ...)` — **the RAW tick-data byte
         write. MUST NOT CHANGE for any asset_group, sports included** — this stays `market-data-tick-sports-prd-...`
         (that's where the actual parquet bytes correctly live; only the MANIFEST pointer is wrong).
  - **Per-asset_group manifest-bucket baseline TODAY** (read from
    `unified-trading-pm/configs/cloud-providers.yaml:154-163`, GCP prod, `DEPLOYMENT_ENV_SHORT=prd`,
    `GCP_PROJECT_ID=central-element-323112` — confirms the "before" state that must stay byte-identical for the 4
    non-sports groups):
    - cefi → `market-data-tick-cefi-prd-central-element-323112`
    - defi → `market-data-tick-defi-prd-central-element-323112`
    - tradfi → `market-data-tick-tradfi-prd-central-element-323112`
    - sports → `market-data-tick-sports-prd-central-element-323112` **(WRONG — target is
      `instruments-store-sports-prd-central-element-323112`, matching `enumerate_expected_universe.py`'s 2026-06-07 seed
      target and the shipped MDPS-sibling fix)**
    - prediction → `market-data-tick-pred-central-element-323112` (dedicated flat kind, unaffected by the carve-out
      either way — never touches the per-asset_group `market-data` dict).
  - **Fix scope, precisely**: the sports-only carve-out must intercept ONLY the manifest-bucket resolution at the 4
    consumer sites under (3) above (`manifest_finalize.py:575`, `preflight.py`'s `read_availability_index`/
    `_check_sports_v9_columns`/`assert_consolidator_healthy` reads, and the `__init__.py:446` non-trading-day writer) —
    i.e. introduce a `_resolve_manifest_bucket()` (sports → `instruments-store-sports-prd-...`, else identical to
    `get_tick_data_bucket()`) and re-point those 4 read/write sites at it, while `venue_fetch.py:395/590` +
    `partitioned_writer.py:207` (the raw parquet byte write) keep calling the UNCHANGED `get_tick_data_bucket()` /
    `state.bucket` for all 5 asset_groups incl. sports. cefi/defi/tradfi/prediction's manifest resolution must stay
    byte-identical — proven above by the yaml baseline (none of those 4 sites' `asset_group` branch would be touched by
    an `if asset_group == "sports"` carve-out).
  - **Orphaned-row migration scope, independently verified via direct GCS/parquet read (ADC,
    `central-element-323112`)**:
    `gs://market-data-tick-sports-prd-central-element-323112/_index/availability_index.parquet` (1,958,499 total rows)
    has **362,665 rows with `source=odds_api`** — **362,631 `captured` + 34 `empty_confirmed`** (data_type breakdown:
    362,649 lower/upper-case `trades`-family rows + 16 spread across `ODDS_MOVEMENT`/
    `ODDS_SNAPSHOT`/`odds_movement`/`odds_snapshot`), date range **2020-06-06 → 2026-06-24** (NOT "through today"
    2026-07-13 as the dispatch context framed it — most recent consolidated row is 19 days stale; flagging the
    discrepancy, not correcting the plan's prior finding, which was about row COUNT and was independently reproduced
    exactly: 362,665/362,631). Top venues: UNIBET (22,129), PADDYPOWER (21,888), PINNACLE (21,084), DRAFTKINGS (19,939).
    **No overlap** confirmed with the canonical bucket:
    `gs://instruments-store-sports-prd-central-element-323112/_index/ availability_index.parquet` (4,988,135 total rows)
    carries only **2,667 odds_api rows** (2,661 `empty_confirmed` + 6 `attempted_failed`), date range **2018-01-01 →
    2020-06-05** — a disjoint pre-backfill window; a `(date, venue, data_type, instrument_id, underlying, fixture_id)`
    join across both slices returned **0 matching rows**. Matches the plan's earlier finding exactly — independently
    confirmed, not just re-asserted.
  - **Live-writer coordination check**: `deployment-service/terraform/gcp/sports_scheduler_cron.tf` confirms
    `google_cloud_scheduler_job.sports_scheduler_cron` (`${env_prefix}-sports-scheduler-cron`) is **ENABLED**, firing
    every 5 min (`sports_trigger_scheduler.SportsTriggerScheduler.poll_interval_seconds=300`), triggering Cloud Run Job
    `sports-scheduler` → `python -m deployment_service sports-trigger run --one-shot --backend cloud ...` which
    dispatches into market-tick-data-service (+ features-sports-service) per `configs/sports-trigger-tiers.yaml`. **This
    IS a live, actively-scheduled writer into the exact code path being fixed** — the same drain-then-migrate
    coordination pattern used for the MDPS sibling fix applies here too (this is a fix-implementation todo, not part of
    this read-only audit).
  - **No code changed in this dispatch** — audit only, per the task's explicit read-only scope.
    - (exact SHAs recorded via the git-commit skill in the same turn as this log entry — see repo `git log -1`.)
- **2026-07-13 (sub-agent, read-only investigation) — api_football TEAMS 61-league gap: ROOT CAUSE FOUND (code
  unchanged, no fix shipped yet — this pass was investigation-only per dispatch).** **(1) One code path, not two.**
  `instruments_service/engine/orchestrator/sports_reference_core.py::_fetch_teams_and_standings` (lines 138-216) is the
  ONLY current TEAMS-writing function. It loops `for league_def in _orch.get_prediction_leagues()` (line 153) — that
  helper (`unified_api_contracts…league_data.py:405`) returns leagues whose UAC `classification == "Prediction"`, which
  is **33 leagues**, confirmed live via
  `unified_api_contracts.canonical.domain.sports.league_data.get_prediction_leagues()`. It then writes ONLY per-league
  partitions (line 190-201); the bare/no-league-id write branch is explicitly retired and now just logs-and-skips
  ("TEAMS bare-path fallback triggered … data shape regression", line 202-208) — **this live code path cannot produce a
  blank-`league_id` captured row.** **(2) Root cause = a classification-filter mismatch between writer and enumerator,
  not a hardcoded allowlist.** The EU enumerator's denominator comes from
  `get_expected_leagues_for_source("api_football")` (`league_data.py:581`) — classification-AGNOSTIC, returns every
  league whose `data_sources` frozenset contains `"api_football"` = **94 leagues** (live-verified). The writer uses the
  classification-FILTERED `get_prediction_leagues()` (Prediction-tier only) instead. Live set arithmetic: of the 94 EU
  leagues, exactly 61 are NOT in `get_prediction_leagues()` ∩ api_football — matching the plan's number exactly. **(3)
  The 61 missing leagues, by UAC classification/tier** (all have real non-null `api_football_id`s in `LEAGUE_REGISTRY`,
  which is WHY they're in the 94-league EU set at all): **22 "Features"-tier domestic lower divisions** (tier 2/3/5) —
  ARGENTINA_PRIMERA_NACIONAL, AUSTRIAN_2_LIGA, BELGIAN_FIRST_B, BRASILEIRAO_SERIE_B, CHILE_PRIMERA_B,
  DANISH_1ST_DIVISION, EERSTE_DIVISIE, ENG_NATIONAL_LEAGUE, FRANCE_NATIONAL, GREEK_SUPER_LEAGUE_2, J2_LEAGUE,
  K_LEAGUE_2, LIGA_EXPANSION_MX, LIGA_PORTUGAL_2, NORWAY_1_DIVISJON, POLAND_I_LIGA, PRIMERA_RFEF, SCOTTISH_CHAMPIONSHIP,
  SUPERETTAN, SWISS_CHALLENGE_LEAGUE, TFF_FIRST_LEAGUE, USL_CHAMPIONSHIP; **39 "Reference"-tier cup/supercup
  competitions** (tier 0) — AUSTRALIA_CUP, AUSTRIAN_CUP, BELGIAN_CUP, CARABAO_CUP, COPA_ARGENTINA, COPA_CHILE,
  COPA_DEL_REY, COPA_DO_BRASIL, COPA_LIBERTADORES, COPA_LIGA_PROFESIONAL, COPA_MX, COPA_SUDAMERICANA, COPPA_ITALIA,
  COUPE_DE_FRANCE, DANISH_CUP, DFB_POKAL, DFL_SUPERCUP, EMPEROR_CUP, FA_CUP, GREEK_CUP, JLEAGUE_CUP, KNVB_CUP,
  KOREAN_FA_CUP, NORWEGIAN_CUP, POLISH_CUP, SCOTTISH_CUP, SCOTTISH_LEAGUE_CUP, SUPERCOPA_ESPANA, SUPERCOPPA_ITALIANA,
  SVENSKA_CUPEN, SWISS_CUP, TACA_DA_LIGA, TACA_DE_PORTUGAL, TROPHEE_CHAMPIONS, TURKIYE_KUPASI, UCL, UECL, UEL,
  US_OPEN_CUP. **No hardcoded allowlist file — the "allowlist" IS the Prediction-classification filter itself**, applied
  at the wrong layer (capture loop should use the same source-coverage filter as the enumerator, not a
  betting-model-relevance filter). **(4) API coverage: likely YES for all 61, unproven for cup-type specifically.**
  Every one of the 61 already carries a valid `api_football_id` in `LEAGUE_REGISTRY` (that's the only reason they're in
  `get_expected_leagues_for_source("api_football")` at all) — api-football's `/teams?league={id}&season={y}` endpoint is
  keyed purely off that numeric ID and has no known Prediction-tier gating, so there's no code/registry reason to expect
  failure. Caveat: none of the 33 already-captured leagues are cup competitions, so the 39 Reference-tier cups are
  UNTESTED by precedent — recommend one live smoke call per cup-tier league before committing to a full backfill. The
  `sports_league_entity_coverage.json` TEAMS-observed list (34 entries incl. `UNKNOWN`) is circular evidence — it's
  DERIVED from the existing captured corpus, so it trivially matches the current 33-league gap and cannot be used to
  pre-screen; it should be regenerated only AFTER a real attempt. **(5) Backfill scope — flag before sizing a VM.**
  Naive full 2018-2026 daily backfill = 61 leagues × ~3,046 days ≈ **185,800 API calls**. But TEAMS is roster data
  (stable within a season) — the 33 already-captured leagues' ~3,046-rows/league cadence reflects the writer's
  in-process `_cached_teams_df` reuse across dates WITHIN one orchestrator run (0 extra API calls per cached date), not
  evidence that literal daily granularity is required or was 3,046 real API calls. No downstream consumer found in this
  pass that needs a dated daily TEAMS snapshot vs. "latest per league-season" (features-sports-service reads the
  per-league `teams.parquet`, not visibly date-keyed beyond most-recent). **Recommend the backfill-implementation todo
  explicitly decide-and-document**: either justify daily cadence with a named consumer, or switch to per-season cadence
  (~61 leagues × ~8 seasons ≈ 500 calls) — this could cut the real API-call count by >99% while still satisfying
  "canonical per-league TEAMS coverage" per the operator's stated model. **(6) The blank-`league_id` bulk bundle is a
  SEPARATE, likely-legacy artifact, not the current writer's output and not confirmed reusable.** Live-manifest query
  confirms 3,648 blank rows spanning 2014-01-01→2026-07-13 (plus one literal `date="all"` sentinel row) — i.e. it is NOT
  simply pre-2018 legacy data (a date range that recent looked at first like an ongoing duplicate live writer, but the
  CURRENT `_fetch_teams_and_standings` cannot produce a blank-league row per finding (1), so these are residual MANIFEST
  rows, most likely from `scripts/migrate_bare_to_per_league.py` (docstring: "reads legacy bare parquets, splits by
  league_id, writes per-league, updates the manifest with per-league captured rows, and deletes the bare parquet")
  having been run but either not covering TEAMS fully or not retro-deleting the old bare manifest rows after the
  per-league rows were added — **not fully resolved in this pass, needs one more check before backfill ships** (confirm
  no live scheduler/poller still bare-writes TEAMS) to avoid a fresh backfill re-creating parallel blank rows. Did NOT
  get to opening a sample bare-captured `teams.parquet` file's raw columns (time-boxed out) — worth checking whether the
  raw team records still carry a league/competition reference internally despite the manifest row_key being blank, which
  would let the 61-league gap be substantially re-derived from already-captured bytes at near-zero new API cost rather
  than a fresh fetch; flagged as the first thing the implementation pass should check. **(7) VM/launcher precedent for
  the eventual backfill**: `af-backfill-` is the registered general api_football VM prefix
  (`deployment-service/deployment_service/vm_prefix_registry.py:618`, bucket=`instruments-store-sports-*`); the
  better-fit precedent is the **targeted gap-fill pattern** `fill-missing-player-stats-`
  (`deployment-service/scripts/vm/launch-fill-missing-player-stats-vm.sh` +
  `instruments-service/scripts/fill_missing_player_stats.py`) — reads the canonical manifest, computes the missing
  `(league_id, date)` cells directly, fires ONLY at those shards (not a full chronological re-walk), and singleton-locks
  against `af-backfill-*` (shared api_football rate-limit key). Recommend basing a new `fill-missing-teams` driver on
  this exact pattern once (5)/(6) resolve the true scope. **Net: this todo is NOT yet closed** — root cause is
  identified and documented (a filter-layer mismatch in the writer, not the enumerator; fix = change
  `_fetch_teams_and_standings`'s league source to match the enumerator's `get_expected_leagues_for_source` call), but no
  code was changed, no backfill ran, and the blank-bundle provenance + true backfill cadence remain open sub-questions
  for the implementation pass.

- **2026-07-13 (slot-3, FINAL RE-VERIFY + CLOSE-OUT REPORT dispatch — whole-asset_group, todo "Whole-asset_group final
  re-verify + close-out report").** Fresh single-parquet read (`.venv/bin/python` + `pandas.read_parquet` direct, NOT
  `read_availability_index()` — that helper's in-process TTL cache + `ManifestConsolidatorStaleError` staleness gate
  returned 0 rows against a live bucket read moments earlier in this same dispatch; a direct GCS parquet read is
  equivalent for a point-in-time audit and is what every prior VERIFY entry in this plan actually used) of
  `gs://instruments-store-sports-prd-central-element-323112/_index/availability_index.parquet`: **4,988,135 total rows**
  (vs §0's 4,863,784 post-cleanup baseline — the mdps backfill + ongoing organic captures account for the growth; a full
  `source`-column sum reconciles exactly to the total, 0 unaccounted rows).

  **Final per-source table (§0 shape + a dedup-dup-groups column, corrected key =
  `date+venue+data_type+league_id+ fixture_id/timeframe+service_name` — see methodology note below):**

  | source                                                    | §0 rows → now         | §0 captured → now       | §0 attempted_failed → now                    | §0 expected_unattempted → now                | dedup dup groups (now) |
  | --------------------------------------------------------- | --------------------- | ----------------------- | -------------------------------------------- | -------------------------------------------- | ---------------------- |
  | api_football                                              | 2,518,940 → 2,518,571 | 365,592 → 370,340       | 3,257 → **3,257 (unchanged)**                | 453,961 → 452,985                            | **0**                  |
  | footystats                                                | 650,504 → 650,876     | 84,047 → 84,311         | 205 → **175 (↓30, in-flight)**               | 56 → 56                                      | 0                      |
  | soccer_football_info                                      | 226,237 → 226,237     | 19,750 → 20,555         | 10 → **10 (unchanged, in-flight)**           | 94 → 94                                      | 0                      |
  | transfermarkt                                             | 270,719 → 270,719     | 58,028 → 58,028         | 0 → **0 (clean)**                            | 47 → 47                                      | 0                      |
  | open_meteo (weather)                                      | 261,790 → 261,790     | 12,097 → 12,298         | 51 → **51 (unchanged, in-flight)**           | 94 → 94                                      | 0                      |
  | odds_api                                                  | 2,667 → 2,667         | 0 → 0                   | 6 → **6 (unchanged, documented-equivalent)** | 0 → 0                                        | 0                      |
  | mdps_odds_horizon_bucket                                  | 215,481 → 339,775     | 0 → **123,642 (fixed)** | 0 → 0                                        | 209,526 → 209,526 (documented, open)         | 0                      |
  | retired (SFI_LEAGUES/SFI_STANDINGS/TRANSFERMARKT_LEAGUES) | 88,056 → 88,056       | 0 → 0                   | 0 → 0                                        | 0 → 0 (100% `EXPECTED_DEPRECATED_DATA_TYPE`) | n/a                    |

  **Concrete improvement vs §0**: mdps_odds_horizon_bucket's zero-ever-captured defect is gone (0 → 123,642 captured);
  footystats attempted_failed is actively falling (205 → 175, confirmed live mid-read); api_football's previously
  reported 39,222 dedup-dup-groups (from the earlier VERIFY entry above) is **now 0** — see methodology correction
  below; every other source's core numbers are stable/unchanged (no regressions anywhere).

  **Dedup-key methodology correction (important, corrects the earlier VERIFY entry's 39,222 figure)**: the prior
  api_football VERIFY entry's stated key (`date+source+data_type+service_name+league_id+fixture_id`) omits `venue`.
  Re-running that exact key here reproduces a large apparent duplicate count (40,825 groups / 81,944 rows) — but
  sampling the largest groups shows they are **not real duplicates**: they are the ~460 blank-`data_type`/blank-
  `league_id` enrichment-pseudo-venue rows (`venue` ∈ {FOOTYSTATS, OPEN_METEO, SOCCER_FOOTBALL_INFO, TRANSFERMARKT,
  UNDERSTAT} — the same rows behind the already-documented `UNCLASSIFIED_ADAPTER_ERROR` finding), which only `venue`
  distinguishes from one another. This is the **identical false-positive class** already root-caused elsewhere in this
  plan for footystats/SFI/weather ("league-grain sources with blank venue... false-positived thousands of duplicates").
  Adding `venue` back into the key (`date+venue+data_type+league_id+fixture_id+service_name`) drops api_football to **0
  true duplicate groups** — verified by direct construction (not just count), and independently reproduced for
  mdps_odds_horizon_bucket: a `date+venue+data_type+timeframe+service_name` key (omitting `league_id`) false-positived
  15,527 groups on the enumerator's per-league `expected_unattempted` seed rows (which share every other dimension and
  differ ONLY by `league_id`); adding `league_id` back drops it to 0. **Corrected dedup methodology for this plan going
  forward: the full identity is `date+venue+data_type+league_id+fixture_id+timeframe+service_name` — no subset of these
  is safe to drop for any sports source**, since different sources' "duplicate-looking" collisions are broken by
  different individual columns.

  **Per-category verdict vs the understat-standard bar (0/0/0 literal or documented-equivalent)**:

  - **MEETS the bar (3/8)**: `transfermarkt` (0 attempted_failed, 47 EU 100%-dated-today/self-closing, 0 dedup) — clean.
    `odds_api` (6 attempted_failed, all `PipelineModeSourceMismatchError` — the write-safety gate correctly rejecting
    historical mismatched writes, already closed as documented-equivalent by the earlier VERIFY entry above,
    re-confirmed unchanged) — closed. `retired data_types` (88,056 rows, 100% `EXPECTED_DEPRECATED_DATA_TYPE`, 0
    attempted_failed) — clean, the P3 spot-verify todo can close.
  - **Core defect fixed, one specific residual remains (1/8)**: `mdps_odds_horizon_bucket` — the zero-ever-captured bug
    is conclusively resolved (123,642 real captures now visible, 0 dedup groups). The remaining 209,526
    `expected_unattempted` is NOT a new/silent gap — it is the already-root-caused, already-scoped
    `enumerate_expected_universe.py` grain-mismatch todo (enumerator seeds `venue=""`/uppercase/no-`timeframe`; writer
    uses `venue=ODDS_API`/lowercase/per-`timeframe`) — a specific code fix, not yet shipped, not blocked by anything.
  - **Code-complete, manifest not yet clean (1/8)**: `api_football` — the 4 shipped bug-class fixes are confirmed live
    and holding (`attempted_failed` unchanged at 3,257, 0 new blank-`data_type` failures since ship); dedup is now
    provably 0 (methodology-corrected). Two specific, non-blocking items remain open: (a) a dedicated backfill-VM
    re-attempt of the 3,257 stale rows (infra op, precedent pattern exists, not yet launched); (b) the TEAMS 61-league
    capture-gap fix (root-caused this session — `_fetch_teams_and_standings` uses the wrong league-source filter,
    `get_prediction_leagues()` instead of `get_expected_leagues_for_source("api_football")` — fix identified, not yet
    shipped, plus a blank-league-bundle provenance sub-question flagged for the implementation pass).
  - **In-flight on an already-running bounded process, not blocked (3/8)**: `footystats` / `soccer_football_info` /
    `open_meteo` — the residual-closer (`sports_attempted_failed_residual_closer_2026_07_13.py`, PID 3247,
    `--max-rounds 6`) is confirmed LIVE right now: its per-VM-shard GCS object
    (`_index/per_vm/sports-attempted-failed-residual-closer-slot3.parquet`) was last written at `18:18:10Z`, 14 seconds
    before this read at `18:18:24Z`. footystats has already dropped 205→175 attempted_failed (TimeoutError 174,
    ArrowTypeError 1 remaining); SFI (10, phantom) and weather (51, phantom) are unchanged so far — per this plan's own
    prior mid-flight note, their fixes stay buffered in-process until the closer's single end-of-run
    `flush_all_pending_buckets()` drain, which has not fired yet for those two sources. All three sources' EU rows are
    100%-dated-today (self-closing daily rolling edge, already root-caused, no action needed). **This is not a blocker**
    — the process is bounded and will self-terminate; the concrete next step is one more re-verify read after PID 3247
    exits.

  **Precise remaining-work list (none `BLOCKED-OPERATOR`/`BLOCKED-CREDENTIALS`, none newly discovered — every item is
  already an open `- [ ]` todo in §1 above)**:
  1. api_football historical backfill-VM re-attempt of the 3,257 stale `attempted_failed` rows (bounded infra op).
  2. api_football TEAMS 61-league capture-gap fix (`_fetch_teams_and_standings` league-source filter) + scoped backfill.
  3. mdps_odds_horizon_bucket `enumerate_expected_universe.py` grain realignment.
  4. MTDS shared-orchestrator sports-manifest-bucket routing generalization + migration of the 362,665
     `odds_api`-in-MTDS orphan rows (blast-radius mapped, fleet-wide proof required before shipping per
     `AUTONOMOUS_AGENT_RULES.md` rule 11 — touches every asset_group's manifest resolution, not just sports).
  5. `reprocess_sports_odds.py` raw-input prefix-template refresh.
  6. Let the in-flight residual-closer (PID 3247) run to its own bounded completion (`--max-rounds 6`), then one more
     fresh re-verify read for footystats/soccer_football_info/open_meteo.

  **DoD status**: NOT fully met. 3/8 categories clean/documented-equivalent, 1/8 core-defect-fixed with one open
  follow-on, 1/8 code-complete-pending-backfill+one-open-gap-fix, 3/8 mid-flight on a live bounded process. Zero
  regressions found anywhere vs §0. §2 DoD section above annotated with this status; this dispatch's own todo (line
  ~159) is flipped `[x]` since its deliverable — the fresh re-verify + final table + precise remaining-work list + DoD
  update — is complete, even though the underlying whole-asset_group work is not yet 100% done (the honest,
  non-overclaiming distinction the todo's own text calls for).
