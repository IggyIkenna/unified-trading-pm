---
doc_type: plan
title: "KRX equity twins eu=372 — no Databento dataset, no launcher, operator decision needed"
created: 2026-06-28
parent_epic: tradfi_master
assigned_vm: NA
source:
  - mvp_backfill_tradfi_ohlcv1m_v10_2026_06_27.md
locked_by: live-defi-rollout
summary: "During G2 verification of `mvp_backfill_tradfi_ohlcv1m_v10_2026_06_27.md`, the tradfi manifest shows 372 `expected_unattempted` rows for KRX (Korea Stock Exchange) that cannot be filled:"
status: active
nature: process
asset_group: tradfi
stage: [meta]
repos: []
scope: [engineer, admin]
tags: []
related: []
execution_scope: orchestrator-agent
priority: P2
drift_direction: advance-code
depends_on: []
last_updated: 2026-06-27
---

# KRX equity twins: eu=372 — no source, operator decision needed

## Finding

During G2 verification of `mvp_backfill_tradfi_ohlcv1m_v10_2026_06_27.md`, the tradfi manifest shows
372 `expected_unattempted` rows for KRX (Korea Stock Exchange) that cannot be filled:

| instrument_id | dates | count |
|---------------|-------|-------|
| KRX:EQUITY:000660 (SK Hynix) | 2026-02-20 → 2026-06-23 | ~124 |
| KRX:EQUITY:005380 (Hyundai Motor) | 2026-02-20 → 2026-06-23 | ~124 |
| KRX:EQUITY:005930 (Samsung Electronics) | 2026-02-20 → 2026-06-23 | ~124 |

**Root cause:** No Databento dataset covers KRX (Korea Stock Exchange, venue code XKRX). The 3
Databento billing datasets for TradFi are GLBX.MDP3 (CME), XCBF.PITCH (CBOE VX), and
XNAS.ITCH/XNYS.PILLAR (NASDAQ/NYSE). KRX is not in any of these. No `launch-tradfi-bf-krx-*.sh`
script exists in `deployment-service/scripts/vm/`.

These instruments ARE in `TRADFI_EQUITY_PERP_BASIS_UNIVERSE` (KRX equities backing Binance
tradfi-perps), so they are in the MVP scope. The G2 gate ("eu=0 for MVP universe") cannot be met
without resolving this.

## Impact

- G2 gate: BLOCKED on KRX eu=372 (cannot reach eu=0 without filling or reclassifying)
- Coverage: 98.95% → after NASDAQ/NYSE VMs drain, ~99.9% excluding KRX
- MVP criterion: KRX ohlcv_1m data is missing for 3 instruments for 2026-02-20 → 2026-06-23

## Decision options

**Option A — Find a Databento KRX dataset:**
Check if Databento offers XKRX.ITCH or equivalent. If available, build
`launch-tradfi-bf-krx-ohlcv-1m.sh` and fill the gaps. Billing impact: new dataset.

**Option B — Alternative source (Barchart, Refinitiv, etc.):**
KRX data is available from other vendors. Build adapter + launcher. Timeline: 1-2 days.

**Option C — Reclassify as EXPECTED_SOURCE_NOT_AVAILABLE (honest-empty):**
If no source is available or prioritized, mark these instruments' KRX data as honest-empty with
reason `EXPECTED_SOURCE_NOT_AVAILABLE`. They would then be excluded from the G2 denominator.
Requires MTDS/IS code change to write the correct reason code for KRX instruments.

**Option D — Remove KRX from MVP universe:**
If the Binance perps backed by KRX equities are not in the v10 trading universe, remove
KRX:EQUITY:000660/005380/005930 from `TRADFI_EQUITY_PERP_BASIS_UNIVERSE`. Requires IS change.

## Recommended action

Operator decision required. Fastest path to G2 green: Option C (reclassify as honest-empty).
Correct long-term path: Option A or B (acquire the data). Option D requires confirming these
Binance perps are not in the v10 trading strategy scope.

## Todos

- [ ] [OPERATOR] P0. Decide: KRX equity twins — fill (Option A/B), reclassify honest-empty (C), or descope (D). See options above.
- [ ] [CODE] P1. Implement chosen option. If Option C: add `EXPECTED_SOURCE_NOT_AVAILABLE` reason for KRX instruments in MTDS backfill writer. If Option A/B: build launcher + fill.
