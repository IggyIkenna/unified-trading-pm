---
title: Databento adapter `to_df(count=N)` chunk-iteration fails with int(Timestamp) error
created: 2026-05-16
author: slot-5-claude
source:
  - tradfi-bf-es-adhoc-adhoc-20260516-130240 VM log (post-temp-file-fix MTDS@741eb5d)
  - market-tick-data-service/market_interface/adapters/tradfi/databento_adapter.py:650
locked_by: live-defi-rollout
---

## What I found

After fixing the `NamedTemporaryFile` temp-file collision (MTDS@`741eb5d`), the next call site in the streaming code
path also fails for every (ES.FUT × ohlcv_1m|trades × 2026-05-{01..07}) tuple:

```
WARNING DatabentoAdapter: GLBX.MDP3/ohlcv_1m chunk-iteration failed [DATABENTO_FETCH_FAILED] after 0 rows:
        int() argument must be a string, a bytes-like object or a real number, not 'Timestamp'
WARNING DatabentoAdapter: GLBX.MDP3/trades chunk-iteration failed [DATABENTO_FETCH_FAILED] after 0 rows:
        int() argument must be a string, a bytes-like object or a real number, not 'Timestamp'
```

Site:
[`market-tick-data-service/market_interface/adapters/tradfi/databento_adapter.py:650`](../../market-tick-data-service/market_interface/adapters/tradfi/databento_adapter.py#L650)

```python
for raw_chunk in dbn_store.to_df(count=chunk_rows):   # ← fails immediately on first iter
    ...
```

`chunk_rows` defaults to 50,000 via `MarketTickDataServiceConfig.databento_chunk_rows` / `MTDS_DATABENTO_CHUNK_ROWS` env
var.

## Why it matters

This blocks **all** TradFi Databento backfills end-to-end. The temp-file fix from earlier today let the actual API call
succeed (`DatabentoBaseClient warmup successful: API key valid, 29 datasets available`) but the SDK's pandas-conversion
path then chokes on every chunk. Symptom: every fetch returns 0 records; VM exits exit_code=0 with no captured data.
Master plan [`tradfi_master_2026_05_07.md`](../../plans/epics/tradfi_master_2026_05_07.md) backfill items 1 + 6

- 10 are now blocked on this, not on credentials.

## Recommended decision

The error originates inside the Databento Python SDK (0.78.0 in the VM venv vs 0.73.0 pinned in
`market-tick-data-service/uv.lock`). The 0.78 → 0.73 mismatch is the leading hypothesis: the SDK upgrade introduced a
Timestamp→int conversion that didn't exist when the path-streaming code was written (MTDS@`d8358f9`, Phase 1).

Three diagnostic next steps in order of cost:

1. **Pin SDK to 0.73.0 on the VM venv** — confirm via `pip show databento` after VM boot that it matches the lockfile,
   not the local PyPI latest. If the divergence is "VM resolves >=0.32.0 constraint to latest at boot time" then the fix
   is tightening pyproject to `<=0.73.0` or to a tighter `~=0.73.0` range, and re-tarballing.
2. **Repro locally** with a 1-day window + Databento test key against a known-good ES.FUT date (e.g. 2024-01-02). If the
   error reproduces on 0.78, the bug is in 0.78 — pin down.
3. **Switch off path-streaming** (Phase 1 escape hatch) — `_fetch_timeseries_range(path=None)` returns an in-memory
   `BytesIO` `DBNStore`; `to_df()` (no count) returns one DataFrame. Higher memory peak on heavy ES.OPT days but proven
   path; trade-off acceptable for un-blocking.

Per workspace HARD RULE "External Data Is Always Available — Never Silently Defer Adapters", this is **not** a
credentials block. Credentials are now valid (account-locked resolved earlier today). This is an internal-adapter
regression.

**Priority**: P0 (May-23 critical — blocks the entire TradFi backfill cutover lane).

**Owner**: next slot 5 turn (or slot 3 / slot 6 if reassignment makes sense — MTDS is multi-owned).
