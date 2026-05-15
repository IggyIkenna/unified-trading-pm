---
title: MTDS 53 market_interface unit test failures — mixed API drift + mock issues
created: 2026-05-14
author: slot-3 (harsh)
resolved: 2026-05-15
resolver: slot-9 (harsh) — mtds@1515170
source:
  - market-tick-data-service/tests/market_interface/unit/
severity: P1
suggested_owner: operator triage
locked_by: live-defi-rollout
locked_since: 2026-05-14
---

## Resolution (2026-05-15 — slot-9, mtds@1515170)

53 original failures reduced to 6 by earlier sessions; slot-9 fixed the remaining 6 in 3 clusters:

| Cluster | Root cause | Failures | Fix |
|---|---|---|---|
| A (Databento CME + OPRA) | test fixtures had `symbol=""` + no expiry field → `_parse_expiry` raised ValueError | 2 | Added `expiration_date`/`expiration` to fixtures |
| B (Prediction parquet schema) | `reader.py` filtered by `("symbol", "==", instrument_id)` but prediction parquets have `market_id` column; instrument_id is file-path only for prediction | 3 | Skip `symbol` filter when `asset_group == "prediction"` in `reader.py` |
| C (Alchemy SOLANA) | Solana now supported via `SOLANA_RPC_TEMPLATES` (Pyth unbanned 2026-05-06); test expected `ValueError` for SOLANA | 1 | Use `TRON` (genuinely unsupported); add `test_get_rpc_url_solana_returns_url` |

**Final state**: `pytest tests/market_interface/unit/` → 1770 passed, 2 skipped, 0 failed.

---

## What I found (2026-05-14)

Running `pytest tests/market_interface/unit/` in `.tabs/3/market-tick-data-service` produced 53 failures across 5 test
modules. Most were fixed by subsequent sessions; 6 remained as of 2026-05-15 22:15 UTC.

## Why it matters

MTDS market_interface/unit suite was non-green since 2026-05-14.

## Recommended decision

✅ RESOLVED — all 6 remaining failures fixed at mtds@1515170.
