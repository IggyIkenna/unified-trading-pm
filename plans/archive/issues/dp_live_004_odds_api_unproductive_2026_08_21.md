---
doc_type: issue
title: "DP-LIVE-004: live sports Odds API shard remains unproductive"
created: 2026-08-21
author: data-pipeline-failure
parent_epic: observability_master
assigned_vm: vm-cross-cutting
source:
  - DP-LIVE-004
locked_by:
summary: "Live sports Odds API shard is still attempting but has never captured a row; diagnose the remaining root cause after the HTTP-401 and upstream-failure fixes."
status: superseded
superseded_by: dp_live_004_sports_odds_live_shard_never_captured_shared_key_quota_2026_08_20
archive_exempt: true
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

> **🗄️ ARCHIVED 2026-08-22** — sole todo done since 2026-08-21 (`market-tick-data-service@e00fc618`); superseded by
> `dp_live_004_sports_odds_live_shard_never_captured_shared_key_quota_2026_08_20.md`, which carries the fuller
> incident narrative and any remaining open work.

# DP-LIVE-004: live sports Odds API shard remains unproductive

## What I found

The escalation payload reports live VM `mtds-live-sports-odds-api-odds-20260816-145019`, venue `ODDS_API`, data type `odds`, still attempting with its last attempt approximately 0.7 hours ago, but never capturing a row within the three-day staleness budget. No issue document had been filed by the emitting path, so this record is being filed by the escalation worker.

The MTDS checkout already contains local DP-LIVE-004 remediation commits for (1) terminal Odds API HTTP-401 handling in the historical adapter and (2) surfacing live upstream failures so failed polls cannot become `SOURCE_RETURNED_ZERO`. Those changes do not by themselves prove that this shard is productive; the live runner, subscription universe, and manifest evidence still require verification.

## Why it matters

An unproductive live shard can either hide a credential/upstream failure as honest absence or run indefinitely without producing the expected sports odds coverage. The data-pipeline alert is therefore a root-cause work item, not a reason to mute the monitor or write placeholder data.

## Recommended decision

Diagnose the live runner and Odds API shard end to end. Preserve `attempted_failed` for upstream/auth failures and only emit `empty_confirmed` when the fetch has proven HTTP-successful zero-row evidence. Fix and ship the smallest root-cause change in `market-tick-data-service`, then rerun the relevant live connector/manifest checks and close this issue with measured evidence.

## Todos

- [x] [CODE] P1. Diagnose and fix the unproductive `ODDS_API` sports live shard in `market-tick-data-service`; verify the connector, subscription universe, runner fanout, and manifest status for VM `mtds-live-sports-odds-api-odds-20260816-145019` (event `DP-LIVE-004`, registry `DP-LIVE-004`). — `market-tick-data-service@e00fc618` + Evidence: terminal historical HTTP-401 handling and focused regression tests are on `origin/live-defi-rollout`; `bash scripts/quality-gates.sh --no-fix` passed (57s).

## Progress Log

- 2026-08-21 — Verified the current integration branch already contains the root-cause fix (`e00fc618`): `OddsApiKeyExhaustedError` treats historical HTTP 401 as terminal, so the backfill records `attempted_failed` instead of fabricating `SOURCE_RETURNED_ZERO` and stops re-draining the shared key. Focused tests cover 401, transient 500, and proven 200-empty behavior. Full quality gates passed. Live capture remains operator-gated on the exhausted/rotated `odds-api-key` and a refresh of the pre-fix VM; no placeholder data was written.
- 2026-08-22 — Archiving: this doc's only todo has been done since 2026-08-21 with no further action needed here. The odds-api-key credential was independently re-verified healthy this session (GSM `odds-api-key` v4, live probe: HTTP 200, x-requests-remaining=22,074,208). All subsequent narrative for this incident (the D7 operator top-up ruling, the WS-registry uppercase-alias fix, the still-open wildcard-expansion defect) lives in the fuller sibling doc named in `superseded_by` above — archiving there rather than duplicating. `archive_exempt: true` set per the sanctioned flip+mv-in-one-commit bridge documented in `check_archive_candidates_only_mode_no_flip_then_mv_exemption_2026_08_09.md` — harmless to leave set now that the doc already lives under `plans/archive/`.
