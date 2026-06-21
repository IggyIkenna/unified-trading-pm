---
title: Massive does NOT carry VX/VIX futures (CFE not in Massive's flat-file product set) — VIX gap stays Barchart+Yahoo
created: 2026-06-17
source:
  - operator ping 2026-06-17 (re-check whether Massive carries VIX/VX futures after the flat-file adapter fix)
  - market-tick-data-service/.../tradfi/massive_flatfiles.py (CME-only flat-file adapter)
  - plans/active/issues/massive_cme_futures_flatfiles_not_rest_2026_06_17.md (the CME flat-file transport fix)
  - LIVE S3 listing of s3://flatfiles/ via files.massive.com (this run, 2026-06-17)
  - unified_api_contracts/registry/data_source_continuity.py (VIX 15m source layering)
locked_by: live-defi-rollout
parent_epic: tradfi_master
priority: P3
status: active
---

# Massive does NOT carry VX/VIX futures (CFE) — the VIX gap remains Barchart + Yahoo

## What I found

**Empirically settled (LIVE S3 listing, 2026-06-17, creds present):** Massive's flat-file bucket `s3://flatfiles/`
(`https://files.massive.com`, path-style) contains exactly these top-level product prefixes:

```
global_crypto/  global_forex/  us_futures_cbot/  us_futures_cme/  us_futures_comex/
us_futures_nymex/  us_indices/  us_options_opra/  us_stocks_sip/
```

The four futures prefixes are **all CME Group exchanges** (CME, CBOT, COMEX, NYMEX). **VX/VIX futures trade on CFE (Cboe
Futures Exchange), which is NOT a CME-Group exchange and is ABSENT from Massive's product set.** Explicit prefix probes
confirm it — all return EMPTY:

- `s3://flatfiles/us_futures_cfe/` → empty
- `s3://flatfiles/cfe/` → empty
- `s3://flatfiles/us_futures_cboe/` → empty
- `s3://flatfiles/cboe/` → empty
- `s3://flatfiles/vix/` → empty

And VX is not buried inside the CME file either: the `us_futures_cme/minute_aggs_v1/2026/06/2026-06-12.csv.gz` ticker
column has **zero `VX`/`VI` tickers** — the roots are ES/NQ/6E FX/SR3 SOFR/BTC-ETH-SOL crypto/etc., all CME-Group.

So the CME-only scope of the flat-file adapter (`massive_flatfiles.py` → `us_futures_cme/minute_aggs_v1/`) is correct
and complete for what Massive serves. A `us_futures_cfe/...` path **cannot be wired because the data does not exist on
Massive.**

**Important disambiguation — three distinct VIX things:**

1. **VX futures (CFE)** — the question here. NOT on Massive. (No CFE prefix.)
2. **VIX 15m INDEX level** (`CBOE:INDEX:VIX-USD`, `ohlcv_15m`) — this is the existing "Barchart+Yahoo gap" in
   `data_source_continuity.py`. It is the index VALUE, not a tradable future. Massive's `us_indices/` prefix exists, but
   that is a separate cell from VX futures and is not what this issue settles. The known permanent index-level gap
   (2025-11-13 → ~today-60d) stands as documented.
3. **VIX OPRA options** — `us_options_opra/` DOES carry VIX options (the smoke script filters underlier `VIX`/`VIXW`).
   Options ≠ the VX futures underlying. Not relevant to this question.

## Why it matters

- **Settles the re-litigated question definitively (NO).** CLAUDE.md's "Massive does NOT cover VIX/VX futures" line is
  CORRECT and now has live-listing evidence, not just the 2026-05-30 dual-source verification. Anyone proposing to wire
  a CFE flat-file path should read this first — the prefix simply isn't in Massive's catalog.
- **No code to ship.** The CME flat-file adapter (`massive_flatfiles.py`) is correctly CME-only. There is no
  `is_cfe_outright` / `cfe_minute_aggs_key` to add, no `_dispatch_data_type` VX route, no continuity-registry change to
  mark VX as Massive-covered — Massive does not carry it.
- The VIX-index 15m gap (Barchart ended 2025-11-12; Yahoo rolling 60d; FRED VIXCLS daily-only) is a SEPARATE,
  already-documented cell and is unchanged by this finding.

## Recommended decision

- **CLOSED — answer is NO.** Massive carries no CFE / VX / VIX-futures flat-file. The CME-only adapter scope is final.
- **If VX futures history is genuinely needed** (separate scope, NOT a Massive question), the canonical sources are
  **Cboe DataShop (the CFE-native vendor)** or **Databento (GLBX/CFE datasets)** — that would be a NEW adapter + a
  `BLOCKED-CREDENTIALS` operator ask (vendor + tier + cost), not a Massive wiring. No such ask is filed here because the
  operator question was specifically "does Massive carry it" — and it does not. File a credential ask under
  `tradfi_master` only if VX-futures (not the VIX index) becomes an MVP requirement.
- This issue doc may archive once acked — it exists only to stop the Massive/VX question being re-opened.

## Status

- **RESOLVED (2026-06-17 /autonomous).** Verified by live S3 listing of `s3://flatfiles/` (creds
  `MASSIVE_S3_ACCESS_KEY_ID`/`MASSIVE_S3_SECRET_ACCESS_KEY` present in `central-element-323112`): no `us_futures_cfe`,
  no `cfe`/`cboe`/`vix` prefix, no VX ticker in the CME minute_aggs file. Massive = CME-Group + crypto/forex + indices +
  OPRA options + US stocks ONLY. VX/VIX futures (CFE) are not part of Massive's product catalog. No wiring shipped (none
  possible). The VIX-index 15m Barchart+Yahoo gap stands as a distinct, already-tracked cell.
