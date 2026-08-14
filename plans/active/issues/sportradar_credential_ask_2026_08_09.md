---
doc_type: issue
title: Sportradar sports-data adapter — no live credential ask tracker (BLOCKED-CREDENTIALS)
summary: >-
  `market-tick-data-service/market_tick_data_service/market_interface/adapters/sports/sportradar_adapter.py` (240 lines,
  `ENDPOINT_STATUS=IMPLEMENTED`) has been fully scaffolded since at least 2026-05-21, but its ONLY credential-ask record
  was a file-based ping (`ikenna_orchestrator/pings/slot_9.md`) — a mechanism RETIRED per
  `unified-trading-pm/agents/RULES.md` § 6, confirmed no-longer-live by the adapter's own module docstring (updated
  2026-08-01, `sports_adapter_dead_code_fallback_duplicate_audit_2026_08_01.md` Finding 6). `gcloud secrets list`
  (central-element-323112, 2026-08-09) confirms no `sportradar-api-key` (or any obvious variant) exists — the credential
  genuinely was never provisioned; this doc gives it a live PM tracker in the current issue-doc format. A genuinely
  credential-free unit-test suite (21 tests, mocked HTTP) is added in the same commit as this doc — previously the
  adapter had ONLY the `@pytest.mark.requires_credentials`-marked integration suite, which SKIPS entirely in CI/QG with
  no live key, i.e. zero test coverage ran by default.
status: open
nature: issue
asset_group:
  [sports] # corrected 2026-08-10 (/ag-closeout-audit cross-cutting) -- was [cross-cutting]. Content is 100%
  # sports (sportradar-api-key for the sports-only SportradarAdapter, discussed against sports vendors/data
  # types) -- forked from Step 4 of the cross-AG coordinator data_completion_to_100_all_ag_2026_06_21.md,
  # inherited the parent's [cross-cutting] tag verbatim despite narrowing to single-AG scope.
stage: [data]
repos: [market-tick-data-service]
scope: [engineer, admin]
tags: [credential-ask, sportradar, sports, blocked-credentials, external-data-always-available]
related:
  [
    /plans/active/data_completion_to_100_all_ag_2026_06_21.md,
    /plans/archive/2026_08/cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md,
    /codex/02-data/external-data-always-available-rule.md,
  ]
created: 2026-08-09
author: agent (slot-19)
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: research
estimate_baseline_ai_days: 0.15
estimate_calibrated_ai_days: 0.18
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
context_scope:
  [
    market-tick-data-service/market_tick_data_service/market_interface/adapters/sports/sportradar_adapter.py,
    /codex/02-data/external-data-always-available-rule.md,
  ]
source:
  [
    /plans/active/data_completion_to_100_all_ag_2026_06_21.md,
    "gcloud secrets list (central-element-323112), run 2026-08-09 — no sportradar match",
    market-tick-data-service/market_tick_data_service/market_interface/adapters/sports/sportradar_adapter.py:16-22,
  ]
---

# Sportradar credential ask

## What I found

Step 4's original 2026-06-21 vendor line paired Sportradar with Odds-API ("Sportradar/Odds-API"). Re-verifying current
state before filing: every Odds-API variant (`odds-api-key`, `odds-api-io-key`, `oddsjam-api-key`, `oddspapi-api-key`,
`opticodds-api-key`) already has a live GSM secret and is wired into production (footystats/odds-backfill VMs in the
2026-06-21 sports launch matrix). **Sportradar is the genuinely-still-blocked half of that pair.**

The adapter itself is fully built (schedule/results/odds fetch, retry/error classification via UAC
`classify_venue_error`, `normalize_odds` best-price selection across books) — but:

1. It carries `ENDPOINT_STATUS=IMPLEMENTED` yet is registered NOWHERE (`factory.VENUE_REGISTRY`/`PLANNED_VENUES`,
   `market_interface/sports/registry.py::_ADAPTER_PATHS`, `adapters/sports/__init__.py::__all__`,
   `market_interface/__init__.py`'s import list) — confirmed by the module's own docstring, updated 2026-08-01.
2. Its only test coverage was the `requires_credentials`-marked integration suite, which skips unconditionally without
   `SPORTRADAR_API_KEY` — meaning it ran in exactly zero CI/QG passes. Added a genuinely mocked unit-test suite in the
   same commit as this doc (`tests/unit/test_sportradar_adapter.py`, 21 tests: constructor, auth-param wiring, 429/401/
   403/generic error → `CanonicalError` classification, schedule/results/odds happy paths, `normalize_odds` best-price
   logic across multiple books).
3. Its credential ask has no live PM tracker — the only record is a retired file-based ping reference.

**Exact capability blocked:** live schedule/results/betting-odds data for soccer/basketball/tennis/NFL via Sportradar
(Basic tier ~$499/mo per sport, 5K calls/day; Trial tier is 100 calls/day free for 30 days only — not a durable free
path).

**Specific credential needed:** one Secret Manager string secret, `sportradar-api-key`.

## Why it matters

Per the external-data-always-available HARD RULE, exhausting the free path (Sportradar's trial expires after 30 days) is
a credential ask, not a descope. The adapter is otherwise ready — nothing downstream depends on it today (it isn't
registered anywhere reachable), so there's no active regression, but the credential-ask record itself was silently stale
(pointing at a retired mechanism), which is the kind of gap that lets a real ask sit unanswered indefinitely.

## Recommended decision

File a fresh `CREDENTIAL APPROVAL REQUEST` for `sportradar-api-key` (Basic tier, ~$499/mo, scoped to whichever sport(s)
sports coverage actually needs — soccer is the adapter's default and likely the right first scope given
`footystats`/`odds-api` already cover soccer odds; confirm with the operator which SPORT + which capability
(schedule/results vs. odds specifically) is actually wanted before subscribing, since odds may be redundant with the
already-credentialed Odds-API/footystats path). Once provisioned:

- [ ] [OPERATOR] P2. Decide + confirm Sportradar's intended role given Odds-API/footystats already cover odds — is
      Sportradar wanted for schedule/results only (a genuinely new capability) or as an odds cross-check (redundant with
      existing sources)? This is a scope decision, not a mechanical implementation step.
- [ ] [CODE] P2. Once scope is confirmed + `sportradar-api-key` lands: register `SportradarAdapter` in
      `factory.VENUE_REGISTRY` (or `PLANNED_VENUES` if not yet wired into a handler),
      `market_interface/sports/registry.py::_ADAPTER_PATHS`, `adapters/sports/__init__.py::__all__`, and
      `market_interface/__init__.py`'s import list — the 4 registration points the module's own docstring names as
      currently missing. `BLOCKED-CREDENTIALS` — awaiting `sportradar-api-key` AND the scope decision above. Repo:
      market-tick-data-service.

## Progress Log

- 2026-08-09 (slot-19): Filed. Confirmed via live `gcloud secrets list` that Sportradar (unlike its Step-4 pairing,
  Odds-API, which is already credentialed) genuinely has no secret provisioned. Added 21 mocked unit tests
  (`market-tick-data-service@<see plan-flip commit>`) closing the "unit tests for the adapter now" half of the Step-4
  requirement — previously this adapter's ONLY test coverage was credential-gated and never ran.
- **context-scout 2026-08-14**: populated context_scope (2 entries).
