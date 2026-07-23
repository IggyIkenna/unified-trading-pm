---
doc_type: issue
title: CeFi historical market-data — 775.9k attempted_failed cells are Tardis-billing-gated (BLOCKED-CREDENTIALS)
summary:
  "The CeFi market-data manifest (consolidated v9 `_index`, 2026-06-21) carries **801,975 `attempted_failed`** cells. A
  measured breakdown by `source` / `pipeline_mode`:"
status: resolved
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: []
scope: [engineer, admin]
tags: [cefi, backfill, manifest, honest-coverage, cost, mtds, data-correctness]
related: [../data_completion_to_100_all_ag_2026_06_21.md, cefi_hl_aster_batch_data_gaps_2026_06_22.md]
created: 2026-06-21
parent_epic: cefi_master
priority: P2
source:
  [
    plans/active/data_completion_to_100_all_ag_2026_06_21.md,
    "consolidated v9 _index gs://market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet",
  ]
assigned_vm:
resolved_by:
  "operator ruling 2026-07-12 (plan-reconciliation Q&A finding 228): billing gate LIFTED — paid, unlimited access
  confirmed (corroborates cefi_hl_aster_batch_data_gaps_2026_06_22.md:426)"
locked_by: live-defi-rollout
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-06-27
---

# CeFi 775.9k `attempted_failed` cells are Tardis-historical-billing-gated

> **RESOLVED 2026-07-12 — Tardis billing gate LIFTED.** Operator ruling (plan-reconciliation Q&A finding 228 (+27),
> `plans/active/issues/plan_reconciliation_operator_decisions_2026_07_11.md` §A2): billing is paid, unlimited access
> confirmed — corroborates `cefi_hl_aster_batch_data_gaps_2026_06_22.md:426`. The exclusion described below is LIFTED;
> the 775,860 `attempted_failed` CeFi historical cells (Tardis-sourced) are now **DISPATCHABLE** for backfill. Blocked
> framing throughout this doc is retained for history, annotated `(was: …)`.

## What I found

The CeFi market-data manifest (consolidated v9 `_index`, 2026-06-21) carries **801,975 `attempted_failed`** cells. A
measured breakdown by `source` / `pipeline_mode`:

| bucket                            | rows    | re-fetchable for free?                        |
| --------------------------------- | ------- | --------------------------------------------- |
| `source=tardis` (`batch_tardis`)  | 753,341 | ❌ Tardis historical replay = BILLED          |
| `batch_tardis` phantom-no-parquet | 22,519  | ❌ (same Tardis-gated dates; re-fetch billed) |
| `source=hyperliquid` (native)     | 30,835  | ✅ free (native venue API)                    |
| `source=aster` (native)           | 17,675  | ✅ free (native venue API)                    |
| misc / null                       | 124     | —                                             |

**775,860 (96.7%)** of the failed cells are **Tardis-sourced** — Binance/Bybit/OKX/Deribit/Coinbase/Upbit/Kraken spot +
futures across `book_snapshot_5` / `trades` / `derivative_ticker` / `futures_chain` / `options_chain` / `liquidations`,
2019→2026. Top error reasons: `UNCLASSIFIED_ADAPTER_ERROR` (689,899), `VENUE_FETCH_FAILED` (83,923),
`phantom_captured_no_parquet_at_canonical_path` (22,700), `HTTP_429` (3,652) — consistent with the Tardis historical
replay endpoint returning 401/429 when the `tardis-api-key` subscription does not cover the requested
exchange×date×data_type (the paid historical entitlement).

The free-venue failures (HYPERLIQUID + ASTER, 48,510) are re-fetched separately via
`launch-cefi-onchain-forward-poll.sh` (native APIs, no Tardis) — tracked in the parent plan, NOT this issue.

## Why it matters

Re-fetching the 775.9k Tardis-gated cells requires the **Tardis historical replay subscription** (the `replay` /
`replay-normalized` tardis-machine endpoints, billed per exchange×day). The operator has **LIFTED the exclusion on batch
Tardis (cefi historical)** — billing gate paid, unlimited access confirmed (operator ruling 2026-07-12, finding 228)
(was: "explicitly EXCLUDED batch Tardis (cefi historical) from this data-completion dispatch" — 2026-06-21: "batch
Tardis (cefi historical) is BILLING-GATED — do NOT launch cefi batch backfills"). So these cells **CAN now move
`attempted_failed → captured`** (was: "cannot move `attempted_failed → captured` without a billing decision — they are
honestly blocked, not a code defect").

This caps CeFi MTDS honest-coverage: with the 775.9k permanently-failed (until funded) + 1.28M `empty_confirmed` + 482k
`expected_unattempted` (mostly Tardis-sourced too), the realistic non-Tardis ceiling is ~36% (current 33.9% + the 48.5k
free re-fetch). Maxing past that requires the Tardis spend.

## CREDENTIAL APPROVAL REQUEST

- **Vendor / tier:** Tardis.dev — **historical data API subscription** (`replay-normalized`), per-exchange historical
  entitlement covering the CeFi venue set (Binance spot+futures, Bybit, OKX spot+swap+futures, Deribit, Coinbase, Upbit,
  Kraken spot+futures).
- **Secret-Manager key:** `tardis-api-key` (already present; entitlement is the gate, not key absence).
- **What it unblocks:** re-fetch of 775,860 `attempted_failed` CeFi historical cells (2019→2026) + ~the Tardis-sourced
  share of 482k `expected_unattempted` → CeFi MTDS honest-coverage toward 100%.
- **Cost:** Tardis historical pricing is per-exchange/month of API access; operator to size against the venue×year span.
- **Status:** `UNBLOCKED — DISPATCHABLE` (was: `BLOCKED-CREDENTIALS` — operator has currently EXCLUDED this spend;
  lifting the exclusion (funding the Tardis historical entitlement) is the only unblock. No agent action until operator
  `[ack]`.) Operator ruling 2026-07-12 (plan-reconciliation Q&A finding 228): billing gate LIFTED — paid, unlimited
  access confirmed.

## Recommended decision — RESOLVED 2026-07-12

Operator ruling 2026-07-12 (plan-reconciliation Q&A finding 228, corroborated by
`cefi_hl_aster_batch_data_gaps_2026_06_22.md:426`): **decision (a)** — the Tardis historical entitlement IS funded/paid,
unlimited access confirmed; an agent should year-shard `launch-cefi-sharded-backfill.sh` across the venue×year span to
drain the 775.9k `attempted_failed` cells — now UNBLOCKED, not yet executed. (was: "Operator: either (a) fund the Tardis
historical entitlement → an agent year-shards `launch-cefi-sharded-backfill.sh` across the venue×year span to drain the
775.9k; or (b) confirm the exclusion stands → these cells remain honest `attempted_failed` and CeFi honest-coverage is
reported against the non-Tardis ceiling.") The free-venue (HYPERLIQUID+ASTER) re-fetch + the live-websocket stream
proceed regardless (no Tardis dependency).
