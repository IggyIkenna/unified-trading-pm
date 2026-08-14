---
doc_type: plan
title: MTDS live sports arb feeds — SharpAPI, odds-api.io, Unity
summary: |
  Productionises the three live odds feeds that today live as e2e-testing scripts. MTDS gains a WSFeedConnector per
  provider (SharpAPI WS, odds-api.io WS, Unity Java-sidecar bridge) writing the union of bookmakers through the SAME
  live manifest path every other venue uses, reusing the existing fixture_id_resolver rather than porting the scanner's
  ad-hoc team matching. Live-only by operator ruling — no historical backfill beyond what Odds API already captures.
status: active
nature: process
asset_group: [sports]
stage: [data]
repos: [market-tick-data-service, unified-api-contracts, deployment-service, e2e-testing]
scope: [engineer]
tags: [sports, live-trading, mtds, arb, odds, wsfeedconnector, unity, sharpapi]
related:
  [
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /codex/05-infrastructure/live-pipeline-architecture.md,
    /codex/02-data/live-data-persistence-and-event-log.md,
    /codex/02-venues/unity-integration.md,
    /codex/02-data/external-data-always-available-rule.md,
    /plans/archive/issues/wsfeedconnector_phase35_gap_2026_07_06.md,
  ]
created: 2026-08-14
last_updated: 2026-08-14
parent_epic: sports_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: brand-new
estimate_baseline_ai_days: 12
estimate_calibrated_ai_days: 12
assigned_role: data_engineering
effort: xhigh
drift_direction: advance-code
context_scope:
  [
    market-tick-data-service/market_tick_data_service/live/connectors/,
    market-tick-data-service/market_tick_data_service/live/websocket_runner.py,
    market-tick-data-service/market_tick_data_service/live/manifest_recorder.py,
    market-tick-data-service/market_tick_data_service/market_interface/adapters/sports/fixture_id_resolver.py,
    e2e-testing/scripts/sports/live_arb_scanner.py,
    e2e-testing/scripts/sports/LIVE_PUBSUB_README.md,
    e2e-testing/docs/sports/LIVE_ODDS_PROVIDERS.md,
    unified-api-contracts/unified_api_contracts/internal/unity_child_books.py,
  ]
depends_on: [venue_capability_route_axis_and_cross_ag_declarations_2026_08_14]
gate_on_depends: true
supersedes:
superseded_by:
locked_by:
locked_since:
source: Batch-vs-live venue parity audit + operator arb-scope ruling, 2026-08-14
---

# MTDS live sports arb feeds — SharpAPI, odds-api.io, Unity

> **Track**: LOCAL / human plan (`assigned_vm: NA`). Hand to a Sonnet-5 worker; audit on completion.
>
> **Gated on** the registry plan — the venues these feeds write must exist with a route before a connector can claim
> them. `gate_on_depends: true`.

## Operator scope ruling (2026-08-14)

> "For the sharp api stuff it's SharpAPI vs Unity vs Betfair we will check for arb. There's no need for now to have hist
> data for any of that beyond what Odds API already captures. The idea, just like e2e-testing implied, is we would run
> live and find arb as it exists, matching books as they show up. Migrate that logic into MTDS, strategy service and
> execution service. We know we would get feed from SharpAPI and Odds API and Unity for the union of bookmakers."

Consequences that bind this plan:

- **Live-only.** Every venue this plan adds gets `batch = none`. No historical backfill, no Tardis-shaped archive leg,
  no coverage-floor obligation. Odds API's existing 5.6M-row historical capture is unchanged and remains the ML/feature
  history.
- **Union, not intersection.** The feed set is the union of what SharpAPI, odds-api.io and Unity serve. A book on two
  providers is one venue with a provider preference, not two venues.
- **The representative book list is a starting point.** It will change; some books may eventually need scraping. Build
  the registration path so adding a book is a registry edit, not a code change, and do not design around today's list.

## Architecture decision — MTDS owns the socket

`e2e-testing/scripts/sports/LIVE_PUBSUB_README.md` sketches an alternative where standalone feed processes publish raw
ticks to `sports-odds-raw-*` Pub/Sub topics and MTDS subscribes. **Do not build that.** Every other venue in the system
reaches MTDS through a `WSFeedConnector` driven by `LiveWebsocketRunner`, and that path is what gives shard-level
failure isolation, the 4-category empty-output semantics, live manifest recording, and the `EventTransport` facade that
makes `paper(W) == batch-rerun(W)`. A parallel publisher tier would be a second live data path — exactly what
`/codex/04-architecture/batch-live-architecture.md` forbids.

The one genuine exception is Unity: `/codex/02-venues/unity-integration.md` specifies a single TCP connection plus a
supplied Java Feed Connector binary running as a sidecar. That is a connector whose transport happens to be a local
socket to the sidecar rather than a direct WSS dial — the same shape the existing polling connectors already use (Curve,
Orca and Raydium are `WSFeedConnector`s with no websocket at all). It stays inside the connector Protocol.

## Reuse, do not re-implement

`live_arb_scanner.py` carries its own team/event matching (`_normalize_team`, `_team_tokens`, `_normalize_event_key`,
`_index_sharpapi_event`, `_resolve_oddsapiio_event`, `_load_betfair_event_names`, `_resolve_poly_event`). **MTDS already
has this in production**: `market_interface/adapters/sports/fixture_id_resolver.py`, used by both `odds_api_adapter.py`
and `betfair_adapter.py`, returning a canonical api-football fixture id plus a `FixtureMatchStatus`, backed by UAC's
per-league team alias tables (`EPL_ALIASES` / `BUNDESLIGA_ALIASES` / `LA_LIGA_ALIASES` in
`unified_api_contracts/external/api_football/team_mappings.py`). Porting the scanner's version would create a second,
diverging matcher on the same problem.

## Todos

### P0 — fix the live sports path that is already broken

- [x] [DATA] P0. Diagnose why the running `mtds-live-sports-odds-api-trades` VM produces zero captured rows — the sports
      manifest holds 97 live rows since 2026-06-21 and every one is `empty_confirmed` or `attempted_failed`, with
      `ODDS_API` trades `empty_confirmed` as recently as 2026-08-14 — DoD: root cause named with evidence (VM log
      excerpt plus the failing call), not a restart. ✅ Root cause: `LiveWebsocketRunner.record_tick()`
      (`market_tick_data_service/live/websocket_runner.py`) did an exact-match dict lookup against the ORIGINAL
      subscription instrument_ids (`ODDS_API:SPORT:{sport_key}`), but `OddsApiWSFeedConnector` is a fan-out poller whose
      yielded ticks carry a different, richer id (`ODDS_API:BOOKMAKER:{bm}:LEAGUE:{league}:FIXTURE:{fixture}` — its own
      docstring documents the two id spaces as unrelated). Every tick silently missed the lookup and was dropped with
      zero logging. Verified: (1) VM `mtds-live-sports-odds-api-trades-20260804-131449`'s run.log (64,567 lines,
      2026-08-04→08-14) has zero ERROR/Exception/"OddsApi" lines and zero `MTDS_LIVE_WS_STARTED`/connect-related
      activity beyond heartbeat/resource-sample noise; (2) manifest at
      `gs://market-data-tick-sports-prd-central-element-323112/_index/per_vm/mtds-live-sports-odds-api-trades-20260804-131449.parquet`
      — all 25 rows `capture_status=empty_confirmed, error_reason=SOURCE_RETURNED_ZERO`; (3) direct API call with the
      production `odds-api-key` secret returned real fixture/bookmaker data for all 5 subscribed leagues (200 OK, 10.3M
      credits remaining — ruling out credentials/quota despite the stale `BLOCKED-CREDENTIALS` module comment); (4)
      standalone repro of `OddsApiWSFeedConnector.connect()`+`.stream()` yielded real ticks immediately, proving the
      connector itself is correct and isolating the bug to the runner's buffer-key matching.
- [x] [DATA] P0. Fix that root cause and prove recovery — DoD: at least one `captured` sports row with a `live_odds_api`
      pipeline_mode and a date after the fix lands; cite the manifest query. ✅ Fix: `record_tick()` now lazily
      registers a new buffer for an unseen instrument_id (mirrors the existing `apply_instrument_delta` pattern) and
      logs a WARNING on the mismatch so a genuine 1:1-connector canonical-id regression (the BYBIT incident the
      pre-existing test guarded) stays observable. Shipped `market-tick-data-service@0974060ae0` (fix) + `@adf74dcf11`
      (900-line-cap follow-up — see
      `/plans/active/issues/mtds_websocket_runner_over_900_line_cap_blocks_commits_2026_08_14.md`, now resolved).
      Quality gates green both times (10,676 tests). Deployed `mtds-live-sports-odds-api-trades-20260814-110648` (old
      broken VM `...-20260804-131449` deleted). Recovery verified: per-VM manifest
      (`gs://market-data-tick-sports-prd-central-element-323112/_index/per_vm/mtds-live-sports-odds-api-trades-20260814-110648.parquet`)
      shows 779 `capture_status=captured` rows (climbing) vs. only the original 5 coarse subscription keys still
      `empty_confirmed` (expected — they never receive direct ticks under this fan-out connector). Sample row:
      `instrument_id=ODDS_API:BOOKMAKER:UNIBET_UK:LEAGUE:LIGUE_1:FIXTURE:600aeb3560814afc9a02bec5126b249d`,
      `pipeline_mode=live_odds_api`, `source=odds_api`, `date=2026-08-14`, `written_at=2026-08-14T11:11:01Z`. NOTE:
      attempted to also correct the shard's `data_type` from `trades` to the batch-matching `ODDS` (batch
      `odds_api_adapter.py:759` writes `data_type=ODDS`) for full batch=live symmetry, but that crashes
      `live_pipeline_mode_for_venue` — UAC's `SPORTS_DATA_TYPE_TO_SOURCE["ODDS"]` (an IS/footystats reference-entity
      registry, `unified_api_contracts/canonical/domain/sports/league_data.py:224`) resolves to source=`footystats`,
      which has no `LIVE_FOOTYSTATS` `PipelineMode` —
      `ValueError: No PipelineMode for source 'footystats' in mode     'live'`. Reverted to `trades` (the only
      currently-launchable data_type for this venue) to unblock this recovery; the `trades`-vs-`ODDS` batch/live
      data_type mismatch is a real, separate cross-cutting gap — tracked as a new P1 todo below rather than blocking
      this fix on it.
- [x] [DATA] P0. Add a live-capture staleness check for sports so a zero-capture live VM pages instead of running
      silently for weeks — DoD: the check fires on the pre-fix condition when replayed against the historical manifest
      window, and routes per `/codex/04-architecture/agent-orchestrator-alerting.md`'s actionable-only rule. ✅ Already
      satisfied — `DP-LIVE-004` / `check_live_capture_productivity` in
      `deployment-service/deployment_service/data_pipeline_monitors/live_stream_watcher.py` (shipped
      `deployment-service@ebeef843c` this morning, 2026-08-14 05:00, `cross_ag_live_capture_parity_2026_08_14.md`
      Finding C), generically covers every running `LONG_LIVED_LIVE` VM via `VM_PREFIX_TO_BUCKET` + the live GCP compute
      census — no sports-specific code needed. Wired into the CLI sweep (`data_pipeline_monitors/cli.py`).
      `test_dp_live_004_fires_when_shard_alive_but_never_captured` in `tests/unit/test_data_pipeline_monitors.py`
      already reproduces this exact VM's pre-fix shape (`vm_name="mtds-live-sports-odds-api-trades-20260804-131449"`,
      `empty_confirmed` rows) and asserts it fires `DP_CRON_DID_NOT_FIRE` at `PAGE_OPERATOR` tier. Routes through
      `emit_finding`/`PipelineFinding`, the shared actionable-only path.

### P0 — connector foundation

- [ ] [DATA] P0. Define the canonical sports live tick shape once — the `ReceivedTick` payload every provider connector
      emits, carrying canonical venue, canonical fixture id, market/outcome, price, and provider-of-record — DoD: a UAC
      schema exists and `find_schema("sports", <data_type>)` resolves it, so the smoke matrix can prove live and batch
      target the same columns.
- [ ] [DATA] P0. Build the provider-agnostic sports connector base handling reconnect/backoff, the `pop_reconnect_flag`
      stale-not-missing contract, and fixture resolution via `fixture_id_resolver` — DoD: unit tests cover a reconnect
      mid-window setting the stale flag, and an unresolvable team name recording
      `FixtureMatchStatus.UNRESOLVED_TEAM_NAME` rather than dropping the tick silently.
- [ ] [DATA] P0. Decide and document how an unresolved fixture is recorded — an honest-absence manifest row, never a
      fabricated fixture id — DoD: the decision is written into `/codex/02-data/honest-absence-downstream-handling.md`
      or a sibling, and a test asserts no tick is written under a guessed fixture id.

### P1 — batch/live data_type symmetry gap (found 2026-08-14 during P0 recovery)

- [ ] [DATA] P1. Resolve the `ODDS_API` venue's batch/live `data_type` mismatch — the batch adapter
      (`market_tick_data_service/market_interface/adapters/sports/odds_api_adapter.py:759`) writes `data_type="ODDS"`,
      but the live shard (`sports:ODDS_API:trades`) uses `data_type="trades"` because `"ODDS"` crashes
      `live_pipeline_mode_for_venue`: UAC's `SPORTS_DATA_TYPE_TO_SOURCE["ODDS"]`
      (`unified_api_contracts/canonical/domain/sports/league_data.py:224`) resolves the source to `footystats` — an
      unrelated IS reference-entity registry entry (footystats' own pre-match odds snapshot, per that file's own
      2026-06-27 operator-decision comment) — which has no `LIVE_FOOTYSTATS` `PipelineMode`, raising
      `ValueError: No     PipelineMode for source 'footystats' in mode 'live'`. Live and batch currently write under
      different shard identities for the same data, breaking the "Live = batch" shard-atom-identical contract — DoD:
      either (a) make `live_pipeline_mode_for_venue` venue-aware so `ODDS_API` + `data_type=ODDS` resolves
      source=odds_api instead of falling through to the data_type-only `SPORTS_DATA_TYPE_TO_SOURCE` lookup, or (b)
      rename the live shard's `data_type` and get the batch adapter to match it — state which and cite the resolved
      shard identity used by both sides.

### P1 — the three providers

- [ ] [DATA] P1. Port `sharpapi_live_feed.py` into a registered `WSFeedConnector` for the SharpAPI-routed venues,
      reusing its WS framing and auth but dropping its ad-hoc event indexing in favour of `fixture_id_resolver` — DoD:
      the connector registers under canonical venue names, and a recorded-fixture test replays a captured SharpAPI frame
      to a canonical tick.
- [ ] [DATA] P1. Port `odds_api_live_feed.py` into a registered `WSFeedConnector` for the odds-api.io-routed venues on
      the same base — DoD: same bar, recorded-fixture test from a captured odds-api.io frame.
- [ ] [DATA] P1. Build the Unity connector as a sidecar bridge — connect to the Java Feed Connector's local socket,
      honour the single-TCP-connection constraint, and fan the feed out to Unity's 10 child-book venues — DoD: the mock
      sidecar in `execution-service/execution_service/sports_execution/adapters/unity/mock_feed_connector.py` drives the
      connector end-to-end in a test with no live credentials.
- [ ] [DATA] P1. BLOCKED-CREDENTIALS gate for Unity — if the subscription is not live, ship the connector as a
      Protocol-conforming scaffold that logs BLOCKED-CREDENTIALS and streams nothing, per the
      External-data-always-available rule — DoD: `test_stream_yields_nothing_when_blocked_credentials` passes and no
      fake tick is ever emitted.
- [ ] [DATA] P1. Register every provider connector under CANONICAL venue names only — the runtime handler resolves by
      exact/lower/upper match, so a lowercase or bare protocol key is unreachable from a canonical shard-spec — DoD: for
      each registered venue, `WS_FEED_CONNECTOR_FACTORIES` resolves the exact `VENUES_BY_ASSET_GROUP` token; a test
      iterates the sports venue list and asserts resolution.
- [ ] [DATA] P1. Add a provider-preference resolver for books served by more than one provider, so the union does not
      double-write a venue — DoD: a book on both SharpAPI and odds-api.io produces one tick stream; the losing provider
      is recorded as a fallback, and the preference is registry data, not a hardcoded branch.

### P1 — flip the live axis and prove symmetry

- [ ] [DATA] P1. Flip each newly-wired venue's capability record `live` axis from `none` to `wired` as its connector
      lands — DoD: the registry plan's drift guard stays green and the axis reflects reality per venue, not per batch of
      work.
- [ ] [DATA] P1. Run `e2e-testing/scripts/validation/validate_batch_live_smoke_matrix.py --asset-group sports` and drive
      every newly-wired cell off `blocked-not-registered` — DoD: cite the run output; cells legitimately blocked on
      credentials must read `blocked-credentials`, never a fake pass.
- [ ] [DATA] P1. Correct the validator's `_CREDENTIAL_BOUND_LIVE_VENUES` static list, which currently hardcodes
      `odds_api` and the Databento tradfi venues as credential-blocked even though live VMs for both are running — DoD:
      the list is derived from real credential state or removed; state which.

### P2 — deploy

- [ ] [DATA] P2. Write the consolidated sports live launcher under `deployment-service/scripts/vm/`, following the
      `launch-mtds-live-cefi-consolidated.sh` pattern of one VM running N shard processes — DoD: the launcher enumerates
      its shards from the registry, and the VM-name prefix is registered in `VM_PREFIX_TO_BUCKET`.
- [ ] [OPERATOR] P2. Launch the sports live consolidated VM and verify capture — VM launches are operator-gated per
      `/codex/05-infrastructure/vm-launcher-runbook.md` — DoD: verify STARTED, then ongoing progress measured as the
      count of NEW `captured` manifest rows per venue (entity-scoped, `time_created`), never process liveness.
- [ ] [DATA] P2. Right-size the sports live VM per `/vm-resource-rightsizing-check` once it has run 30 minutes — DoD:
      cite measured CPU and memory-growth; the cefi fleet audit found 6-7% CPU on 16 vCPU, so do not copy a machine type
      without measuring.
- [ ] [DATA] P2. Retire the e2e-testing feed scripts that are now production code, leaving a pointer — DoD:
      `sharpapi_live_feed.py` and `odds_api_live_feed.py` either delete or shrink to thin harnesses calling the MTDS
      connectors; no second implementation of the same feed survives, per the no-shims rule.

## Definition of done for the whole plan

Sports live capture produces `captured` rows again; SharpAPI, odds-api.io and Unity each stream through a registered
canonical-venue `WSFeedConnector` on the standard live path; the union of bookmakers writes without double-counting;
fixture resolution goes through the one production resolver; and the smoke matrix shows no `blocked-not-registered`
sports cell that we actually have a provider for.

## Progress Log

- 2026-08-14: Closed all three P0 "fix the live sports path that is already broken" todos in one session. Root cause of
  the 10-day zero-capture outage: `LiveWebsocketRunner.record_tick()` exact-matched tick instrument_ids against the
  original subscription set only, silently dropping every tick from `OddsApiWSFeedConnector` (a fan-out poller whose
  ticks carry a different, richer per-(bookmaker,fixture) id than its coarse subscription key). Fixed via lazy buffer
  registration (`market-tick-data-service@0974060ae0`, follow-up line-cap cleanup `@adf74dcf11`). Redeployed
  `mtds-live-sports-odds-api-trades-20260814-110648` (old broken VM deleted); verified 779 `captured` rows within 2
  minutes of boot, `pipeline_mode=live_odds_api`. The staleness-check todo turned out to already be satisfied by
  `DP-LIVE-004` (shipped same morning by other work, `deployment-service@ebeef843c`) — no new code needed. Also
  attempted to fix a batch/live `data_type` mismatch found along the way (batch writes `ODDS`, live used `trades`) by
  relaunching under `data_type=ODDS`, but that crashes `live_pipeline_mode_for_venue` (UAC's
  `SPORTS_DATA_TYPE_TO_SOURCE["ODDS"]` resolves to `footystats`, which has no live `PipelineMode`) — reverted to
  `trades` to unblock this recovery and filed it as a new P1 todo instead of blocking on it.
