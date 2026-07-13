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
- [ ] [VERIFY] P0. **Whole-asset_group final re-verify + close-out report.** Once all sources above are addressed:
      re-read the live manifest fresh, produce a final per-source table matching §0's shape, confirm every source is at
      the understat standard (0/0/0 literal or a documented equivalent), update this plan's DoD, and write the rule-9
      final report (per `AUTONOMOUS_AGENT_RULES.md`) — no operator pickup items should remain.

# 2. Definition of DONE

Every active sports source (api_football, footystats, soccer_football_info, transfermarkt, open_meteo, odds_api or its
formal retirement, mdps_odds_horizon_bucket or its formal `BLOCKED-CREDENTIALS` scaffold) shows 0 `attempted_failed` / 0
(or documented-equivalent) `expected_unattempted` / 0 duplicate dedup-key groups / correct `service_name`+`asset_group`;
every root cause is fixed in code (not just data patched); all findings filed in the relevant plans/issue docs; final
report written in this plan's Progress Log.

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
