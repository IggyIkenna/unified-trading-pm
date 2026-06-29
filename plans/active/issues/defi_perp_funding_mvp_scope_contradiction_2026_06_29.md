---
doc_type: plan
title: "DeFi perp_funding MVP-scope contradiction — is_mvp() vs capability registries vs the backfill plan (2026-06-29)"
created: 2026-06-29
parent_epic: defi_master
assigned_vm: NA
source:
  - mvp_backfill_defi_onchain_v10_2026_06_27.md (G1.5 blocked OPERATOR item + perp_funding backfill VMs)
  - agent-orchestrator backlog item mvp_backfill_defi_onchain_v10-010 (blocked)
  - unified_api_contracts/canonical/crosscutting/mvp_scope.py (is_mvp SSOT)
summary:
  "The `perp_funding` data_type evaluates is_mvp()=False for EVERY venue (DRIFT, Hyperliquid) under BOTH cefi and defi,
  yet the v10 backfill plan launched two perp_funding backfill VMs as MVP work and the honest-coverage denominator counts
  424 DRIFT perp_funding cells as reachable. Three SSOTs disagree about whether DeFi perp_funding is in MVP scope.
  Blocks resolution of the P0 AO item on the Solana-drift backfill stall."
status: active
nature: process
asset_group: defi
stage: [meta]
repos: [unified-api-contracts, instruments-service, market-tick-data-service]
scope: [engineer, admin]
tags: [mvp-scope, defi, perp-funding, drift, hyperliquid, ssot-contradiction, data-quality, honest-coverage]
related:
  - plans/active/mvp_backfill_defi_onchain_v10_2026_06_27.md
priority: P1
drift_direction: advance-code
execution_scope: orchestrator-agent
depends_on: []
last_updated: 2026-06-29
---

# DeFi perp_funding MVP-scope contradiction (2026-06-29)

> Filed while investigating the only `blocked` item in the locally-running agent-orchestrator backlog
> (`mvp_backfill_defi_onchain_v10-010`, `[OPERATOR] P0` — "Solana-drift backfill performance stall"). Before deciding
> the stall intervention, the operator asked: **is DRIFT / Solana actually in the DeFi MVP list?** Verifying that against
> the UAC SSOT surfaced a three-way contradiction that gates the answer.

## TL;DR

- **DRIFT-SOLANA the venue IS in the defi MVP list** — but only in its **DEX role** (`POOL`/`DEX_POOL` →
  `dex_pool_state`/`dex_pool_swaps`). Those cells are `is_mvp()`-true.
- **DRIFT `perp_funding` is NOT MVP**, and neither is Hyperliquid `perp_funding`. The `perp_funding` data_type
  evaluates `is_mvp()=False` for **every** venue under **both** asset groups.
- Funding data for perps is actually MVP **under `cefi`** via the `funding_rate` / `derivative_ticker` data_types on
  `PERPETUAL` instruments — NOT via the defi `perp_funding` data_type.
- **Per the operator's standing rule** ("fix only if under MVP scope, else don't download for now"), the blocked
  Solana-drift backfill is currently **out of MVP scope → do not build the sig index / do not download.** But the
  contradiction below must be ruled on first, because it equally affects the Hyperliquid perp VM and the v10 G2 gate.

## Evidence

### 1. `is_mvp()` says `perp_funding` is MVP-true for zero cells

`is_mvp()` ([mvp_scope.py:1091-1098](../../../../unified-api-contracts/unified_api_contracts/canonical/crosscutting/mvp_scope.py)) gates a defi cell on a **strict 3-axis AND**: `venue` AND `instrument_type` AND `data_type` must all be declared in the rule.

Probe results (run via `unified-api-contracts/.venv`):

| asset_group | venue | instrument_type | data_type | `is_mvp` |
|---|---|---|---|---|
| defi | DRIFT-SOLANA | DEX_POOL | dex_pool_swaps | ✅ True |
| defi | DRIFT-SOLANA | POOL | dex_pool_state | ✅ True |
| defi | DRIFT-SOLANA | **PERPETUAL** | **perp_funding** | ❌ **False** |
| cefi | DRIFT / DRIFT-SOLANA | PERPETUAL | perp_funding | ❌ False (DRIFT not a classified cefi venue) |
| cefi | HYPERLIQUID | PERPETUAL | **perp_funding** | ❌ **False** |
| cefi | HYPERLIQUID | PERPETUAL | funding_rate | ✅ True |
| cefi | HYPERLIQUID | PERPETUAL | derivative_ticker | ✅ True |
| cefi | HYPERLIQUID | PERPETUAL | trades | ✅ True |

Root cause:
- **defi rule** ([mvp_scope.py:567-584](../../../../unified-api-contracts/unified_api_contracts/canonical/crosscutting/mvp_scope.py)):
  `instrument_types = {POOL, DEX_POOL, LST, LENDING}` — **no `PERPETUAL`**; `data_types` includes `perp_funding`.
  Perp funding semantically lives on `PERPETUAL` instruments, so the 3-axis AND can never pass for `perp_funding`.
- **cefi rule**: `data_types = {book_snapshot_5, derivative_ticker, funding_rate, trades}` — **no `perp_funding`**.
  cefi captures funding via `funding_rate` / `derivative_ticker` instead.
- **`perp_funding`** is therefore a **defi-only data_type name** that is unreachable for MVP under either rule.

git-blame: the defi `instrument_types` frozenset was authored 2026-06-08 (`824944660`); `PERPETUAL` was never included.
Current `MVP_SCOPE_CONFIG_VERSION = 12`.

### 2. The defi rule's own comment lists perp_funding as intended-MVP

[mvp_scope.py:537](../../../../unified-api-contracts/unified_api_contracts/canonical/crosscutting/mvp_scope.py):
> `perp_funding — Perpetual funding rates (Hyperliquid, Aster, Drift)`

So author **intent** was that perp_funding (incl. Drift) is MVP — but the coded `instrument_types` axis contradicts it.

### 3. The capability/coverage registries DO declare DRIFT perp_funding (drives the denominator)

- [defi_venue_capabilities.py:139](../../../../unified-api-contracts/unified_api_contracts/registry/defi_venue_capabilities.py):
  `"DRIFT-SOLANA": {"perp_funding": "2022-01-01", "dex_pool_swaps": "2022-01-01"}`
- [expected_coverage.py:268](../../../../unified-api-contracts/unified_api_contracts/registry/expected_coverage.py):
  `"DRIFT-SOLANA": ["perp_funding", "position_data"]`

`measure_honest_coverage.py` computes `reachable = captured + attempted_failed + expected_unattempted`
([measure_honest_coverage.py:429](../../../../instruments-service/scripts/measure_honest_coverage.py)) — it does **NOT**
gate the denominator on `is_mvp()`. The reachable set comes from the catalogue/manifest, which is seeded by these
capability registries. That is why the v10 G2 coverage table reports **424 DRIFT `perp_funding` cells as reachable** and
the gate FAILS until they are filled — even though `is_mvp()` says those cells are out of MVP.

### 4. The v10 plan treats perp_funding as MVP and launched two perp backfill VMs

[mvp_backfill_defi_onchain_v10_2026_06_27.md](../mvp_backfill_defi_onchain_v10_2026_06_27.md):
- G1 launched `mtds-solana-drift-backfill` (DRIFT `perp_funding`) **and** `mtds-perp-funding-backfill` (Hyperliquid `perp_funding`) as MVP work.
- G2 gate enumerates `perp_funding` as 1 of the 6 MVP defi data_types that must reach `attempted_failed=0`.

### 5. Live state of the blocked backfill (2026-06-29)

- VM `mtds-solana-drift-backfill` no longer exists (SPOT — preempted/terminated after its last log write 09:13Z).
- Consolidated `_index/drift_v2_sig_index.parquet` was **never built** (Option A not executed); only the 6,293+ parts exist.
- The **429-burst anomaly** is real: run.log's final writes show ~24 batches advanced in 0.25s on pure HTTP 429s
  (no backoff). DRIFT `perp_funding` parquets exist only for 2025-01-09/10/11 (117/94/74 MB); the 429-burst dates
  (e.g. 2026-03-05/06) have **no** DRIFT parquet. The repeated Helius 429s point to a Helius plan rate-limit ceiling.

## The three-way contradiction (what must be ruled on)

| SSOT | Says about DeFi `perp_funding` |
|---|---|
| `mvp_scope.is_mvp()` (the "what is MVP" SSOT) | **NOT MVP** — unreachable for any cell |
| `defi_venue_capabilities` + `expected_coverage` (drive the manifest/coverage denominator) | **In scope** — DRIFT-SOLANA produces perp_funding since 2022-01-01 → 424 reachable cells, gate-failing |
| v10 backfill plan + cefi `funding_rate`/`derivative_ticker` | Plan treats it as MVP; meanwhile cefi already models perp funding under a different data_type/asset_group |

## Resolution options (OPERATOR RULING REQUIRED)

- **Option 1 — SSOT is correct; perp_funding out of defi MVP.** Remove `perp_funding` from `DRIFT-SOLANA` (and any other
  defi venue) in `defi_venue_capabilities` + `expected_coverage` so it leaves the reachable denominator; resolve the AO
  P0 item as out-of-scope (no sig index, no download); re-examine the Hyperliquid perp VM under the same logic. Net: do
  not download DRIFT perp data now.
- **Option 2 — intent is correct; perp_funding IS MVP.** Add `PERPETUAL` to the defi rule's `instrument_types` (matching
  the line-537 comment) so DRIFT/Hyperliquid/Aster perp_funding becomes `is_mvp()`-true; then the DRIFT backfill IS in
  scope → fix it (Helius plan upgrade for the 429 ceiling + build the consolidated sig index). Must also reconcile
  defi `perp_funding` vs cefi `funding_rate`/`derivative_ticker` to avoid double-modeling the same funding data.
- **Option 3 — perp funding is cefi-only.** Treat DRIFT/Hyperliquid perps as cefi; capture funding via cefi
  `funding_rate`/`derivative_ticker` on `PERPETUAL`; remove `perp_funding` from the defi rule + registries entirely;
  classify DRIFT as a cefi perp venue if it should be in scope at all.

**Recommendation:** the `is_mvp()` SSOT + the existing cefi `funding_rate`/`derivative_ticker` model both point to
Option 1/3 (DeFi `perp_funding` is not the intended capture path) — i.e. **the Solana-drift backfill is out of MVP scope
and should not be downloaded now.** But this is an operator ruling because it determines whether the Hyperliquid perp VM
and the v10 G2 perp_funding gate are valid.

## Todos

- [ ] [OPERATOR] P0. Rule on the contradiction: choose Option 1 / 2 / 3 above. This unblocks AO item
      `mvp_backfill_defi_onchain_v10-010` and determines DRIFT + Hyperliquid perp backfill scope.
- [ ] [SCRIPT] P1. Once ruled: reconcile `mvp_scope.py` (defi `instrument_types` / `data_types`) with
      `defi_venue_capabilities.py` + `expected_coverage.py` so `is_mvp()` and the coverage denominator agree on
      `perp_funding`. Repo: `unified-api-contracts`. Add a `test_mvp_scope.py` assertion pinning the ruling.
- [ ] [SCRIPT] P1. Apply the ruling to the v10 plan: update G1/G2 scope for `perp_funding`; resolve the AO blocked item;
      flip 424 DRIFT `perp_funding` cells to the correct honest state (out-of-scope vs attempted_failed) so the coverage
      gate reflects reality. Repos: `instruments-service`, `unified-trading-pm`.
- [ ] [SCRIPT] P2. If Option 1/3: confirm Hyperliquid perp funding is captured via cefi `funding_rate`/`derivative_ticker`
      and is not silently dropped by removing defi `perp_funding`. Repo: `market-tick-data-service`.

## Codex SSOTs

- `codex/02-data/honest-coverage-model.md` — two-layer / instrument-gates-download denominator model.
- `codex/02-data/availability-manifest-and-data-status.md` — `expected_unattempted` / reachable semantics.
- UAC `mvp_scope.py` is the live SSOT for "what is MVP"; the capability/coverage registries are the live SSOT for the
  reachable denominator — this issue is precisely that those two disagree for `perp_funding`.

## Progress Log

### 2026-06-29 — filed

Investigation triggered by the blocked AO item. Confirmed `is_mvp()` returns False for all `perp_funding` cells (defi +
cefi), confirmed the capability/coverage registries declare DRIFT-SOLANA perp_funding (424 reachable cells), confirmed
cefi models funding via `funding_rate`/`derivative_ticker`, and confirmed the v10 plan launched two perp_funding VMs as
MVP work. Live state: DRIFT VM gone, sig index never built, 429-burst anomaly real (only 3 dates of genuine data).
Awaiting operator ruling on Option 1/2/3.
