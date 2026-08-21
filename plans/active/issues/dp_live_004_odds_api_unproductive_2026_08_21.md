---
doc_type: issue
title: "DP-LIVE-004: live sports Odds API shard remains unproductive"
created: 2026-08-21
author: data-pipeline-failure
parent_epic: observability_master
assigned_vm: vm-cross-cutting
source:
  - DP-LIVE-004
locked_by: live-defi-rollout
summary: "Live sports Odds API shard is still attempting but has never captured a row; diagnose the remaining root cause after the HTTP-401 and upstream-failure fixes."
status: open
nature: process
asset_group: [sports]
stage: [meta]
repos: [market-tick-data-service]
scope: [engineer, admin]
tags: [data-pipeline, dp-alerts, dp-live-004, sports, odds-api]
related:
  - /plans/active/sports_consolidated_closeout_2026_07_19.md
priority: P1
resolved_by:
execution_scope: local-only
drift_direction: advance-code
depends_on: []
context_scope:
  - /codex/05-infrastructure/data-pipeline-alerts.md
  - /codex/02-data/availability-manifest-and-data-status.md
  - /codex/02-data/honest-absence-downstream-handling.md
  - market-tick-data-service/market_tick_data_service/live/connectors/odds_api_ws.py
  - market-tick-data-service/tests/unit/test_odds_api_ws_connector.py
  - /plans/active/sports_consolidated_closeout_2026_07_19.md
---

# DP-LIVE-004: live sports Odds API shard remains unproductive

## What I found

The escalation payload reports live VM `mtds-live-sports-odds-api-odds-20260816-145019`, venue `ODDS_API`, data type `odds`, still attempting with its last attempt approximately 0.7 hours ago, but never capturing a row within the three-day staleness budget. No issue document had been filed by the emitting path, so this record is being filed by the escalation worker.

The MTDS checkout already contains local DP-LIVE-004 remediation commits for (1) terminal Odds API HTTP-401 handling in the historical adapter and (2) surfacing live upstream failures so failed polls cannot become `SOURCE_RETURNED_ZERO`. Those changes do not by themselves prove that this shard is productive; the live runner, subscription universe, and manifest evidence still require verification.

## Why it matters

An unproductive live shard can either hide a credential/upstream failure as honest absence or run indefinitely without producing the expected sports odds coverage. The data-pipeline alert is therefore a root-cause work item, not a reason to mute the monitor or write placeholder data.

## Recommended decision

Diagnose the live runner and Odds API shard end to end. Preserve `attempted_failed` for upstream/auth failures and only emit `empty_confirmed` when the fetch has proven HTTP-successful zero-row evidence. Fix and ship the smallest root-cause change in `market-tick-data-service`, then rerun the relevant live connector/manifest checks and close this issue with measured evidence.

## Todos

- [ ] [CODE] P1. Diagnose and fix the unproductive `ODDS_API` sports live shard in `market-tick-data-service`; verify the connector, subscription universe, runner fanout, and manifest status for VM `mtds-live-sports-odds-api-odds-20260816-145019` (event `DP-LIVE-004`, registry `DP-LIVE-004`).
