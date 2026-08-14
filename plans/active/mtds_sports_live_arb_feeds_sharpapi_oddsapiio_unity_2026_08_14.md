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
depends_on: [sports_venue_universe_and_capability_route_axis_2026_08_14]
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

- [ ] [DATA] P0. Diagnose why the running `mtds-live-sports-odds-api-trades` VM produces zero captured rows — the sports
      manifest holds 97 live rows since 2026-06-21 and every one is `empty_confirmed` or `attempted_failed`, with
      `ODDS_API` trades `empty_confirmed` as recently as 2026-08-14 — DoD: root cause named with evidence (VM log
      excerpt plus the failing call), not a restart.
- [ ] [DATA] P0. Fix that root cause and prove recovery — DoD: at least one `captured` sports row with a `live_odds_api`
      pipeline_mode and a date after the fix lands; cite the manifest query.
- [ ] [DATA] P0. Add a live-capture staleness check for sports so a zero-capture live VM pages instead of running
      silently for weeks — DoD: the check fires on the pre-fix condition when replayed against the historical manifest
      window, and routes per `/codex/04-architecture/agent-orchestrator-alerting.md`'s actionable-only rule.

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

_(append dated entries here)_
