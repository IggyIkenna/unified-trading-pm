---
doc_type: issue
title:
  GCS path resolution centralization audit — SPORTS + PREDICTION rounds (continuation of the CEFI/DEFI/TRADFI audit)
summary: >-
  RESOLVED 2026-07-29. Continuation doc for /plans/active/issues/gcs_path_resolution_centralization_audit_2026_07_28.md
  (the parent doc, now at 586 lines — split here to stay clear of the plan line cap rather than grow the parent past
  it). Same recurring bug class (hand-rolled GCS prefixes silently drifting from the canonical
  `pipeline_mode=`/`asset_group=` hive-partitioned shape), same 4-round audit methodology, scoped to SPORTS and
  PREDICTION per the operator's original expanded directive (CEFI/DEFI/TRADFI/SPORTS/PREDICTION, batch+paper+live, under
  /autonomous). All 4 todos done: rounds 4-5 audits complete, the P0 live-mode sports odds writer shape fix shipped
  (market-tick-data-service@d6d539a8), the 5 dead sports_* PATH_REGISTRY rows deleted (folded into
  unified-trading-library@f4987fb8). Archived — parent doc stays active (5 unrelated deferred items remain there,
  outside this doc's SPORTS+PREDICTION scope).
status: resolved
nature: issue
asset_group: [sports, prediction]
stage: [meta]
repos:
  [
    unified-trading-library,
    unified-api-contracts,
    market-tick-data-service,
    market-data-processing-service,
    features-service,
    strategy-service,
    execution-service,
    instruments-service,
  ]
scope: [engineer, admin]
tags: [gcs, path-resolution, pipeline-mode, silent-failure, canonical-paths, centralization]
related:
  [
    /plans/active/issues/gcs_path_resolution_centralization_audit_2026_07_28.md,
    /plans/archive/issues/mdps_t1_recon_job_oom_failing_7_days_2026_07_26.md,
  ]
created: 2026-07-28
last_updated: 2026-07-29
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.8
assigned_role: infra
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  split off /plans/active/issues/gcs_path_resolution_centralization_audit_2026_07_28.md (parent doc) once it reached 586
  lines after rounds 1-3 (CEFI/DEFI/TRADFI); continues the operator's original expanded-scope directive for SPORTS +
  PREDICTION under /autonomous.
resolved_by: >-
  All 4 todos shipped 2026-07-29 — see summary for the commit list.
depends_on: []
---

# GCS path resolution centralization audit — SPORTS + PREDICTION

## Origin

See the parent doc (`/plans/active/issues/gcs_path_resolution_centralization_audit_2026_07_28.md`) for the full origin
story, the canonical SSOT description, and rounds 1-3 (CEFI/DEFI/TRADFI) findings. This doc exists ONLY to keep the
parent under its line cap while continuing the same audit for the two remaining asset groups the operator named: SPORTS
and PREDICTION.

**SPORTS-specific context worth knowing before auditing**: this asset group already had a real, resolved investigation
this same day — `/plans/archive/issues/mdps_t1_recon_job_oom_failing_7_days_2026_07_26.md` Update 13 found and fixed a
`pipeline_mode=`-omission bug in MDPS's `_check_existing_outputs` (the bug that KICKED OFF this entire audit) and
reclassified/backfilled 1,944+3,055 sports odds-horizon-bucket manifest rows for the exact same root cause. Any
SPORTS-round agent should read that doc first so it doesn't re-discover the same ground — the question for this round is
whether OTHER sports code paths (not `orchestration_scanner.py`, already fixed) have sibling instances of the same bug
class, plus the batch/paper/live centralization question the operator asked for generally.

**PREDICTION-specific context**: the original P2 fix that started this whole audit
(`market-data-processing-service@df02dd0`) already covers one PREDICTION data point (Kalshi/Polymarket prediction
markets share MDPS's `_check_existing_outputs`, now fixed). Round 1's CEFI audit also flagged (but did not resolve) a
MTDS finding: `_perp_funding_kalshi_polymarket.py`'s "CeFi paths carry no pipeline_mode" comment possibly applying to
prediction-shaped perp-funding writers — that open DESIGN todo lives in the parent doc, cross-reference it rather than
re-deriving.

## Audit round 4 (SPORTS-scoped) — COMPLETE, 2 agents, both returned 2026-07-28

Good news, similar to round 3 (TradFi): **no CRITICAL live-firing bug**. Execution-service is confirmed clean by absence
(zero GCS/storage-client usage anywhere in `sports_execution/` — no sports equivalent of round 2's DeFi loader bug
exists to fix). Findings are one real dormant landmine and 5 confirmed dead-and-wrong registry rows.

### Confirmed bugs

1. **[dormant, code-confirmed] MTDS's live-mode sports odds writer produces a structurally incompatible shape vs. the
   batch writer.** Batch (`venue_fetch.py::_build_sports_shard_path`, live-verified) writes one shard per
   `(bookmaker, league, fixture)`:
   `raw_tick_data/by_date/day={D}/pipeline_mode={pm}/asset_group=sports/venue={BOOKMAKER}/league_id={L}/fixture_id={F}/instrument_type=odds/data_type=trades/ticks.parquet`
   (25 real bookmaker venues verified live). The live writer (`live/websocket_runner.py::live_tick_blob_path`) instead
   writes ONE file per `instrument_id`, no `league_id=`/`fixture_id=` partition — and the live connector
   (`live/connectors/odds_api_ws.py`) sets `instrument_id` to one-per-SPORT (not per-fixture) while bundling every
   bookmaker's odds as nested JSON inside a single tick payload. A real live capture would be structurally
   invisible/unparseable to every batch-shaped downstream consumer (MDPS's sports adapters, `dependency_checker.py`'s
   bookmaker-venue matching). **UPDATE 2026-07-29 — the landmine is now live-armed, not proven-live-firing-yet**: the
   connector's own docstring said `BLOCKED-CREDENTIALS`, and as of the last sample zero `pipeline_mode=live_odds_api`
   objects existed anywhere in the sports bucket — but the operator rotated `odds-api-key` to a working key the same
   day, and this connector resolves that exact secret. The credential half of "whenever live odds_api credentials land"
   has now landed; see the P0 todo below (bumped from P2).
2. **5 CONFIRMED WRONG-AND-DEAD `sports_*` PATH_REGISTRY rows** (`registry.py:268-302`) —
   `sports_features`/`sports_fixtures`/`sports_raw_odds`/`sports_mappings`/`sports_tick_data`. Every one is BOTH
   wrong-shaped (live-verified against the real writer's actual output) AND dead (zero callers anywhere outside their
   own matching `SportsXDomainClient` in the already-known-dead `domain_client` layer — rounds 1/3 found this same layer
   dead for CEFI/TradFi; this is the 5th-9th confirmed instance). `sports_tick_data` is the worst: its
   `bucket_template="market-tick-data-{project_id}"` doesn't even exist as a bucket (reversed word order AND missing the
   `-prd-` env tier — the real bucket is `market-data-tick-sports-prd-{project_id}`, same double-defect class as round
   2/3's `calendar_features`/`instruments` bucket-template findings). Both instruments-service and features-service
   independently bypass PATH_REGISTRY entirely for sports data with their own correct hand-rolled implementations —
   these 5 rows look like a vestigial early design nothing ever wired up to.

### Confirmed-safe / positive baseline

- `market-tick-data-service`'s `sports_catalog_reader.py` (dual legacy/canonical probe),
  `venue_fetch.py::_build_sports_shard_path` (batch writer), `dependency_checker.py`'s
  `UPSTREAM_DEPS_BY_ASSET_GROUP["SPORTS"/"PREDICTION"]` day-only shallow prefixes — all live-verified correct.
- MDPS's sports adapters (`bucket_assignment`/`odds_loss_guard`/`odds_movement`/`odds_snapshot`/`arbitrage`) do zero
  path construction of their own — pure consumers of the already-audited-safe scanner output.
- `features-service/features_service/sports/data/{gcs_paths,gcs_reader,gcs_mappings,writer}.py` — gold-standard,
  correctly delegate to UAC `candidate_parquet_paths()`/registry SSOTs, live-verified against real GCS.
- `strategy-service` has no sports GCS reader at all (Pub/Sub event-log subscriber pattern only) — safe by absence.
- `execution-service`'s entire `sports_execution/` stack has **zero** GCS/storage-client usage anywhere — confirmed
  clean by absence, no sports analog of round 2's execution-service CRITICAL bug exists.
- instruments-service's sports writers bypass the 5 wrong registry rows entirely with their own correct hand-rolled
  implementation (re-confirms round 1's already-documented duplication finding, not new).

### Structural gaps already tracked generically — confirmed to ALSO apply to sports (no new todo needed)

- `_candidate_pipeline_mode_values()`'s `Mode.REPLAY` omission (already tracked, DeFi-flagged originally) — confirmed
  applies to sports too (every sports source has `Mode.REPLAY` registered in UAC; dormant, zero live replay objects
  found).
- MDPS `dependency_checker.py`'s `max_results=1000/2000` listing cap (already tracked, DeFi-flagged originally) —
  sports' fan-out shape (25 bookmaker venues × 11+ leagues × multiple fixtures, in ONE day) makes this plausible here
  too; not proven (a full recursive listing did not complete in-session).

### Not fully verified

- Whether the live odds_api connector is wired into any real deployment-service launcher (inferred dormant from zero
  live GCS objects + the connector's own docstring, not a direct launcher trace).
- ml-service's sports feature consumers (`training/app/core/{sports_feature_loader,cloud_feature_provider}.py`) —
  outside this round's assigned repo list; flag as a follow-up if the audit ever extends to ml-service.
- Pre-2020-06-06-floor `sports_reference` objects still present in GCS — an adjacency to the already-tracked disposition
  item in `sports_consolidated_closeout_2026_07_19.md`, not a new finding of this audit.

## Audit round 5 (PREDICTION-scoped) — COMPLETE, 1 agent, returned 2026-07-29

**Resolves round 1's open DESIGN question** (`_perp_funding_kalshi_polymarket.py`'s "CeFi paths carry no pipeline_mode"
comment) — and the answer is worse than round 1 estimated: **STALE BUG, CONFIRMED LIVE-FIRING**, not a dormant/unproven
one. Otherwise the PREDICTION asset_group itself (as opposed to the mis-scoped cefi file living in a
"kalshi_polymarket"-named module) is clean — no PREDICTION-specific PATH_REGISTRY rows exist at all (relies entirely on
the generic `raw_tick_data`/`processed_candles`/`instruments` rows, all independently re-verified correct here too), and
execution-service/strategy-service are both confirmed clean by absence (no DeFi-style CRITICAL bug, matching rounds
3-4).

### Confirmed bugs

1. **[CONFIRMED LIVE-FIRING, ~5 weeks]
   `market-tick-data-service/market_tick_data_service/cli/handlers/_perp_funding_kalshi_polymarket.py:115-168`**
   (`_write_cefi_perp_funding_rows`) is the ONLY CeFi writer in the entire codebase that skips the mandatory post-hoc
   `pipeline_mode=` insertion every sibling performs (`symbol_rules.py::_build_partition_path_for_asset_group`,
   `live/websocket_runner.py::live_tick_blob_path`, `book_microstructure_handler.py` all `.replace()`-insert
   `pipeline_mode=` on top of UAC's `build_cefi_partition_path()`, which has no such param by design). Live-verified:
   real `KALSHI_PERP` objects write to
   `raw_tick_data/by_date/day={D}/asset_group=cefi/venue=KALSHI_PERP/instrument_type=perpetual/data_type=perp_funding/{id}.parquet`
   — no `pipeline_mode=` ancestor segment — while every sibling cefi venue on the SAME day correctly nests under
   `pipeline_mode=batch_{venue}/`. File introduced 2026-06-21 (`mtds@88c2f0c7`), KALSHI_PERP launched 2026-05-29 —
   writing under the wrong shape for ~5 weeks. Path≠manifest divergence confirmed (manifest correctly records
   `pipeline_mode=batch_kalshi_perp` via `record_captured`; the object path doesn't carry it). No downstream consumer
   reads this data yet (zero hits in execution-service/strategy-service), so a landmine + unreachable-data problem
   today, not active data corruption. `POLYMARKET_PERP` has zero real objects (upstream `BLOCKED-UPSTREAM-OUTAGE`) so
   only the KALSHI_PERP half is actually firing. **Despite the filename, these venues are UAC-classified
   `asset_group=cefi`, not `prediction`** — worth remembering when picking up the fix todo below. No write-time
   canonicality guard exists on this path at all (the live writer has one via
   `canonical_path_violations(require_pipeline_mode=True)`; this batch writer has none).

### Confirmed-safe / positive baseline

- **PATH_REGISTRY has zero prediction-specific rows** — relies entirely on the generic
  `raw_tick_data`/`processed_candles`/`instruments` rows, independently re-verified correct for `asset_group=prediction`
  (real bucket family uses the `pred` token, not `prediction` —
  `market-data-tick-pred-prd-*`/`instruments-store-pred-prd-*`/`features-pred-prd-*`).
- Batch write (`kalshi_adapter.py` via `symbol_rules.py`) and live write (`websocket_runner.py`, live connector
  `kalshi_trades_ws.py` marked "Status: ACTIVE") both correctly insert `pipeline_mode=`; live-mode prediction objects
  just haven't appeared in the 5 sampled recent days (code-correct, currently unexercised in practice).
- `_candidate_pipeline_mode_values("prediction")` correctly derives from UAC's generic
  `external_batch_sources_for_asset_group` — no hand-listed source-enumeration gap. The already-tracked generic
  `Mode.REPLAY` omission applies here too (no new todo).
- `features-service`'s prediction cross-venue calculators (`prediction_cross_venue_{trade_dispatch,dispatch}.py`,
  `prediction_cross_venue_betfair.py`) all use the safe day-only-prefix + client-side substring-match pattern.
- `execution-service`'s prediction execution stack (Kalshi/Polymarket handlers/adapters) — zero GCS/bucket/blob usage
  anywhere; operates directly against live venue APIs. `strategy-service`'s prediction strategies consume typed
  event-driven inputs, zero GCS imports. Both confirmed clean by absence, matching rounds 3-4.
- `instruments-service`'s prediction reference-data sinks (`_instrument_availability_sink_for`,
  `_market_lifecycle_sink_for`) — pipeline_mode-aware, hand-rolled-but-correct, already fixed for the alphabetical-sort
  partition-key trap (`instrument_availability_hive_canonicalisation_2026_07_21.md`).

### Not fully verified

- Whether the live `kalshi_trades_ws.py`/`polymarket_trades_ws.py` connectors are wired into a real running
  deployment-service launcher (inferred dormant from zero live GCS objects, not a direct launcher trace).
- `_perp_funding_kalshi_polymarket.py`'s manifest row_key uses lowercase `venue="kalshi_perp"` vs. the GCS path's
  uppercase `venue=KALSHI_PERP` — a possible secondary shard-atom-identity mismatch, noticed but not deep-dived; flag
  for whoever picks up the primary fix.

## Todos

- [x] [SCRIPT] P1. **Round 4 (SPORTS-scoped) audit** — DONE 2026-07-28, findings documented above. No CRITICAL
      live-firing bug; execution-service confirmed clean by absence. New follow-up todos logged below.

- [x] [SCRIPT] P0. **URGENT 2026-07-29 — Fix MTDS's live-mode sports odds writer shape mismatch BEFORE the live
      connector runs.** `market_tick_data_service/live/websocket_runner.py::live_tick_blob_path` (non-CeFi branch) +
      `live/connectors/odds_api_ws.py::_parse_fixture_response` now write one shard per (bookmaker, league, fixture) —
      matching the batch `venue_fetch.py::_build_sports_shard_path` shape — instead of one nested-JSON-bundled file per
      sport. **No longer dormant**: the operator rotated `odds-api-key` (Secret Manager, project
      `central-element-323112`) to a new working key on 2026-07-29 (5,000,000-credits/month subscription, live-verified)
      — the same secret `odds_api_ws.py` resolves via `cfg.odds_api_secret_name`. Fixed before the live sports-odds WS
      connector could be enabled/dispatched against production. Evidence: `market-tick-data-service@d6d539a8`. New
      parity test proves the round-trip: fixture response -> ticks -> blob path matches the batch builder's output for
      the same fixture. (repo: market-tick-data-service)

- [x] [SCRIPT] P2. **Delete the 5 confirmed wrong-and-dead `sports_*` PATH_REGISTRY rows + their dead
      `SportsXDomainClient` consumers** — `sports_features`/`sports_fixtures`/`sports_raw_odds`/`sports_mappings`/
      `sports_tick_data` (`unified_trading_library/config_interface/paths/registry.py:268-302`) plus
      `unified_trading_library/domain_client/sports/{features,fixtures,odds,mappings,tick_data}_client.py`. Zero callers
      anywhere in the workspace outside their own definition/export files; `sports_tick_data`'s bucket doesn't even
      exist. Folded into the parent doc's dead-code-cleanup todo — shipped together as a single sweep. Evidence:
      `unified-trading-library@f4987fb8`. (repo: unified-trading-library)

- [x] [SCRIPT] P1. **Round 5 (PREDICTION-scoped) audit** — DONE 2026-07-29, findings documented above. Resolved round
      1's open MTDS DESIGN question (stale bug, confirmed live-firing — see the parent doc's flipped todo for the full
      ruling + fix scope). No other CRITICAL finding; execution-service/strategy-service confirmed clean by absence,
      matching rounds 3-4.

**All 5 audit rounds (CEFI/DEFI/TRADFI/SPORTS/PREDICTION) are now complete.** See the parent doc's own "What's NOT done
yet" section (now stale — will be updated in the same pass as this flip) for the remaining open work: the
genuine-centralization design todo, and the accumulated per-finding fix todos across both docs.
