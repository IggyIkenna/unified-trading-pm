---
title: Massive CME futures history is on the S3 FLAT-FILES, not the REST /futures/v1 endpoint
created: 2026-06-17
author: ikennaigboaka
source:
  - operator ping 2026-06-17 (sibling agent pulled 5y ES from Massive S3 flat-files)
  - market-tick-data-service/scripts/massive_flat_files_smoke.py (in-repo S3 recipe seed)
  - plans/active/tradfi_massive_dual_source_2026_05_28.md (Phase 4 + the now-corrected futures-endpoint todo)
locked_by: live-defi-rollout
parent_epic: tradfi_master
---

# Massive CME futures: use the S3 flat-files, not the REST `/futures/v1` HTTP endpoint

## What I found

The Massive TradFi futures ingestion was chasing the **wrong transport**. The `MassiveTradfiRestConnector`
(`market-tick-data-service/.../tradfi/massive_tradfi_rest_connector.py`) fetches futures via the REST API
(`api.polygon.io` → originally `/v3/reference/futures/*`, then "fixed" 2026-06-16 to
`/futures/v1/{contracts,products}`). **Both are dead ends for CME futures history** — our Massive **Stocks-Starter REST
tier is equities-only; CME futures are not served on the REST API at all** (the `/futures/v1` HTTP/SSL/auth errors seen
in prod are this).

A sibling agent pulled **5 years of CME ES futures (2021-06-13 → 2026-06-12, 114,981×15m bars, 1,232 daily files)
entirely from Massive's S3 FLAT-FILES — zero REST calls.** The same path works for any CME future, not just ES. The
in-repo seed `scripts/massive_flat_files_smoke.py` already proves the S3 endpoint/auth/schema for one day (but it omits
the mandatory path-style addressing — see the gotcha below).

### Ground-truth recipe (from the sibling agent's working downloader)

- **Endpoint**: `https://files.massive.com` (S3-compatible) — **NOT** `api.polygon.io` / `api.massive.com/futures/v1`.
- **Bucket / key**: `flatfiles` → `us_futures_cme/minute_aggs_v1/YYYY/MM/YYYY-MM-DD.csv.gz` (one gzipped CSV per session
  day).
- **⚠️ THE GOTCHA — path-style addressing is MANDATORY.** Virtual-host addressing (boto3's default) SSL-fails against
  `files.massive.com`. This is almost certainly the HTTP/SSL error prod hit. Fix:
  `boto3.client("s3", endpoint_url=…, aws_access_key_id=…, aws_secret_access_key=…, config=Config(s3={'addressing_style':'path'}, retries={'max_attempts':4}))`.
- **Credentials**: `MASSIVE_S3_ACCESS_KEY_ID` + `MASSIVE_S3_SECRET_ACCESS_KEY` in Secret Manager (project
  `central-element-323112`) — **distinct S3 keys, NOT the REST `MASSIVE_API_KEY`** (all three secrets confirmed
  present).
- **CSV schema**: `ticker, window_start, open, high, low, close, volume`. `window_start` is in **NANOSECONDS** (and is
  the **LEFT/open edge** → canonical right-edge `t_close` = `window_start + 60e9` ns for 1m; `// 1e6` → ms epoch).
- **Ticker convention** (trips people up): outrights are **single-digit year** — `ESZ5` = Dec-2025, NOT `ESZ25`. Filter
  outrights with `^<ROOT>[FGHJKMNQUVXZ]\d$` to exclude spreads (`ESZ5-ESH6`) and non-outrights. Front month = the
  highest-volume outright that day; ratio-back-adjust across rolls for a continuous return series.
- **History depth**: ≥5 years on the flat-files (sibling capped at 2021-06; earlier exists).

## Why it matters

- It is the **operator gate** on the Massive/TradFi futures cell. The futures-endpoint todo in
  `tradfi_massive_dual_source_2026_05_28.md` was flipped 2026-06-16 to "`/futures/v1` fixed" — that is **factually wrong
  for CME** (REST tier doesn't carry CME futures). Left as-is it would ship a connector that 404/SSL-errors forever and
  never capture a single futures bar, while the manifest reads "code fixed."
- The data **exists and is proven reachable** (5y ES, 1,232 files) — so per the External-Data-Always-Available rule this
  is **not** a defer/credentials ask; it is a transport-correction we implement now.
- `MassiveTradfiRestConnector` currently has **0 production consumers** (dead code; matches R5-fix-6) — so re-pointing
  the futures path to the flat-files has no live blast radius beyond the connector + its tests.

## Recommended decision (ADOPTED — implementing this autonomous run)

1. Add an **S3 flat-files ingestion path** to the Massive connector: lazy path-style `boto3` client against
   `files.massive.com`/`flatfiles`, creds via `get_api_key("MASSIVE_S3_ACCESS_KEY_ID"/"MASSIVE_S3_SECRET_ACCESS_KEY")`
   (endpoint + bucket as constants). Fetch `us_futures_cme/minute_aggs_v1/YYYY/MM/DD.csv.gz`, parse, filter CME
   outrights for the requested root(s), normalise `window_start` (ns, LEFT) → canonical right-edge `t_close` (ns→ms),
   emit the canonical OHLCV shape with `source="massive"` + `pipeline_mode=BATCH_MASSIVE`.
2. **Re-point futures ingestion off REST**: `fetch_futures_chain` / the futures `ohlcv_*` dispatch derive the universe +
   bars from the flat-files; **delete the `/futures/v1` REST futures code** (delete-deprecated — it does not serve CME).
   Equities/options REST paths (`/v3/trades`, `/v3/quotes`, `/v2/aggs`, `/v3/snapshot/options`) are unchanged (those ARE
   on the Stocks-Starter tier).
3. Unit-test on a mocked S3 client (synthetic `minute_aggs_v1` CSV: outright filtering, ns→right-edge, front-month
   roll). Live S3 pull is credentialled (`@pytest.mark.requires_credentials`) — the recipe is proven by the sibling's 5y
   pull.
4. Update `tradfi_massive_dual_source_2026_05_28.md`: correct the futures-endpoint todo, record the flat-files transport
   as the canonical futures path, and unlock the operator gate.

## Status

- **IN PROGRESS (2026-06-17 /autonomous)** — connector implementation + plan correction shipping this run. This issue
  doc archives once the flat-files path is merged + the plan reflects it.
