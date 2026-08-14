---
doc_type: issue
title:
  "Glassnode on-chain analytics — no credential provisioned (BLOCKED-CREDENTIALS). Kaiko half CLOSED 2026-08-10 (removed
  vendor)"
summary: >-
  Neither `glassnode-api-key` nor `kaiko-api-key` exists in GCP Secret Manager (central-element-323112) as of 2026-08-09
  (confirmed: `gcloud secrets list` returns no match for either name or any obvious variant). Glassnode's adapter code
  already exists (`market-tick-data-service/market_tick_data_service/market_interface/adapters/onchain/glassnode.py`,
  shipped 2026-05-21) but is intentionally parked — listed in `factory.py::PLANNED_VENUES` as `"glassnode":
  "analytics"`, not wired into `get_adapter()`. Kaiko had NO adapter at all until this session — scaffolded now
  (`kaiko.py`, `market-tick-data-service@<see plan-flip commit>`) mirroring the Glassnode pattern (Bearer-header auth
  instead of query-param, same retry/backoff/log_event shape), also parked in `PLANNED_VENUES` as `"kaiko":
  "analytics"`. Both adapters' unit tests run fully mocked (44 tests total between the two files) and pass with zero
  live credential.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [data]
repos: [market-tick-data-service, unified-api-contracts]
scope: [engineer, admin]
tags:
  [credential-ask, glassnode, on-chain-analytics, blocked-credentials, external-data-always-available, kaiko-removed]
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
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.24
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
    market-tick-data-service/market_tick_data_service/market_interface/adapters/onchain/glassnode.py,
    /codex/02-data/external-data-always-available-rule.md,
  ]
source:
  [
    /plans/active/data_completion_to_100_all_ag_2026_06_21.md,
    "gcloud secrets list (central-element-323112), run 2026-08-09 — no glassnode/kaiko match",
  ]
---

> **✅ 2026-08-10 — RESCOPED TO GLASSNODE ONLY. The Kaiko half is CLOSED and its scaffold is DELETED.** Do NOT provision
> `kaiko-api-key`. Kaiko is a removed provider workspace-wide, not just in DeFi execution. This ask was written in good
> faith: CLAUDE.md's removed-providers list sits under its "Working on DeFi EXECUTION?" conditional bullet, so it did
> not obviously bind an MTDS on-chain-**analytics** adapter. The operator ruled on 2026-08-10 that the ban is
> fleet-wide. The scaffolded `kaiko.py` adapter, its test, its `PLANNED_VENUES` entry and its UAC `SourceCapability` are
> all being deleted under `/plans/archive/2026_08/kaiko_provider_removal_2026_08_10.md` (no shim — CLAUDE.md's
> delete-deprecated-code rule), and the CLAUDE.md wording is being fixed there so the ambiguity cannot recur.
>
> **The GLASSNODE half of this ask remains OPEN and live** — Glassnode is not a removed provider, `glassnode-api-key` is
> still unprovisioned in Secret Manager, and per `/codex/02-data/external-data-always-available-rule.md` exhausting the
> free path is a credential ask, not a descope. This doc WAS formally rescoped to Glassnode-only on 2026-08-10 by
> `/plans/archive/2026_08/kaiko_provider_removal_2026_08_10_finalize.md` todo 3 (now landed and archived): read every
> Kaiko statement below as historical record, not as an open request.

# Glassnode + Kaiko on-chain analytics credential ask

## What I found

Per `data_completion_to_100_all_ag_2026_06_21.md` Step 4, this was flagged (2026-06-21) as one of five "credential-gated
venues" needing an ask. Re-verifying current state before filing (per the pre-task plan/issue conflict-check rule — a
Step-4-dated line can be stale by the time it's actually worked): a live `gcloud secrets list` sweep on
`central-element-323112` (2026-08-09) confirms **Glassnode and Kaiko are the only two of the five Step-4 vendor groups
with genuinely no credential provisioned today** — Helius, Alchemy, Tardis, Databento (core 3-dataset subscription), and
every Odds-API variant already have a live secret and are wired into production paths. (Sportradar is ALSO genuinely
blocked — filed separately: `plans/active/issues/sportradar_credential_ask_2026_08_09.md`, since it pairs with Odds-API
in the original Step-4 line rather than with these two.)

**Exact capability blocked:**

- **Glassnode** — on-chain analytics (MVRV, SOPR, NUPL, NVT, exchange balance/flow, active addresses, tx count, price
  close) for BTC/ETH/SOL/LTC/BNB. Standard plan ($29/mo+) required for most indicators; a subset (price close) is
  available on the free tier for BTC/ETH only.
- **Kaiko** — CeFi/on-chain trade + order-book analytics (raw trades, VWAP, order-book snapshots) across tracked
  exchanges. Paid tier required for historical/analytics endpoints.

**Specific credential needed:** two Secret Manager string secrets — `glassnode-api-key` and `kaiko-api-key` — API keys
from each vendor's paid dashboard.

## Why it matters

Per the external-data-always-available HARD RULE, exhausting the free path is a credential ask, not a descope. Neither
vendor's data is currently used anywhere in the pipeline (both adapters are parked in `PLANNED_VENUES`, not reachable
via `get_adapter()`), so nothing downstream is silently degraded today — but the adapter code paths + tests are now
built and ready to wire in the moment credentials land, closing the "build the scaffold now, backfill on creds" half of
the Step-4 requirement.

## Recommended decision

File a `CREDENTIAL APPROVAL REQUEST` for both `glassnode-api-key` and `kaiko-api-key` (Standard/paid tier, ~$29-99/mo
each depending on plan). Once provisioned:

- [ ] [CODE] P2. Promote `GlassnodeAdapter` from `PLANNED_VENUES` into `VENUE_REGISTRY` + `get_adapter()` dispatch, and
      wire it into a collect handler (which downstream feature consumer needs on-chain analytics is a separate design
      decision — do not guess a handler; ask if unclear). `BLOCKED-CREDENTIALS` — awaiting `glassnode-api-key`. Repo:
      market-tick-data-service.
- [ ] [CODE] P2. Promote `KaikoAdapter` (`market_tick_data_service/market_interface/adapters/onchain/kaiko.py`, added
      2026-08-09) from `PLANNED_VENUES` into `VENUE_REGISTRY` + `get_adapter()` dispatch, and wire it into a collect
      handler (same caveat as above — target handler is a design decision, not a guess). `BLOCKED-CREDENTIALS` —
      awaiting `kaiko-api-key`. Repo: market-tick-data-service.
- [ ] [DATA] P3. Once live-credential integration tests are added (mirroring
      `tests/integration/test_glassnode_integration.py`'s `@pytest.mark.requires_credentials` pattern), add a Kaiko
      counterpart. Repo: market-tick-data-service.

## Progress Log

- 2026-08-09 (slot-19): Filed. Re-verified Step-4's 5-vendor list against live GSM state before filing — Tardis billing
  gate already LIFTED 2026-07-12 (`plans/archive/issues/cefi_tardis_historical_blocked_credentials_2026_06_21.md`,
  resolved), Helius/Alchemy/Databento/Odds-API all carry live secrets already. Scaffolded `KaikoAdapter` + 18 mocked
  unit tests (`market-tick-data-service@<see plan-flip commit>`); Glassnode's existing scaffold (370-line adapter + 26
  unit tests, already shipped 2026-05-21) re-verified still green, no changes needed.
- **context-scout 2026-08-14**: populated context_scope (2 entries).

## Kaiko removal COMPLETE (2026-08-10)

The Kaiko scaffold this ask was filed for no longer exists anywhere: `unified-api-contracts@c48238266b` (capability +
base URL + registry membership) and `market-tick-data-service@da86db197e` (adapter, test, `PLANNED_VENUES` entry,
docstring) — both QG-green and ancestry-verified on LDR. `rg -il kaiko` across the workspace returns zero integration
references; the only survivors are prose records of the ban and two investor-relations lines naming Kaiko as a market
COMPETITOR.

**What remains open on this doc is the GLASSNODE half only**: `glassnode-api-key` is still unprovisioned in Secret
Manager, Glassnode is NOT a removed vendor, and per `/codex/02-data/external-data-always-available-rule.md` exhausting
the free path is a credential ask rather than a descope. Tracked for the operator on
`/plans/active/issues/operator_action_items_consolidated_2026_08_08.md`.
