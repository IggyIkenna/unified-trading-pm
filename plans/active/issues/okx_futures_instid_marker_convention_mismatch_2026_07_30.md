---
doc_type: issue
title:
  "OKX-FUTURES 100% empty live capture traces to an unresolved cross-repo canonical instrument_id convention mismatch,
  not a bounded bug"
summary: >-
  Live-fix worker dispatched to fix a prior investigation's two confirmed CeFi live-capture bugs (BINANCE-FUTURES
  book_snapshot_5 parser bug -- SHIPPED, market-tick-data-service@4f244845 -- and this OKX-FUTURES id-mapper bug) found
  the OKX-FUTURES portion is NOT a bounded, single-side bug. OKX-FUTURES is empty across all three data_types uniformly
  (trades=137/137, book_snapshot_5=137/137, derivative_ticker=137/137), and 137/137 of the resolved live universe's
  instrument_ids carry an @LIN/@INV margin marker + an 8-digit YYYYMMDD expiry suffix (e.g.
  OKX-FUTURES:FUTURE:AAPL-USD@LIN-20310613), which every OKX-FUTURES connector's reverse instId mapper
  (_instrument_to_okx_futures_inst_id in okx_futures_ws.py, _instrument_to_okx_inst_id in okx_ws.py shared by the
  book/derivative_ticker siblings) sends to OKX verbatim including the marker+suffix -- a malformed instId no real OKX
  contract ever has, so every subscribe fails silently.

  Deeper investigation this session found this is not simply "one side is stale": okx_futures_ws.py's own module
  docstring states the OKX-FUTURES id convention is deliberately "RAW PASSTHROUGH, no @LIN/@INV marker ... OKX-FUTURES's
  own dated-future wire instId already unambiguously encodes margin type via the literal _UM infix" (real OKX wire
  shapes: BTC-USD-260710 inverse / BTC-USD_UM-260710 linear, 6-digit YYMMDD) -- "operator-decided 2026-07-09." Git
  history confirms this was not an oversight: commit 20dc1be8 (2026-07-10, "retrofit CeFi WS connectors to build the
  real canonical @LIN/@INV instrument_id shape") explicitly retrofitted
  BYBIT/KRAKEN-FUTURES/OKX-SWAP/BINANCE-FUTURES/DERIBIT with the marker -- and just as explicitly did NOT touch
  OKX-FUTURES, i.e. the exemption was deliberately reaffirmed the day after the marker's PERPETUAL-scope-expansion
  ruling, not simply forgotten.

  Meanwhile instruments-service's reference_data/adapters/cefi/tardis/parsing.py
  (_build_canonical_future_key/_build_dated_derivative_canonical_symbol) treats OKX-FUTURES identically to every other
  dated-derivative venue: it computes margin_type via an OKX-specific _UM/_CM inference helper (same real-wire evidence
  as MTDS's docstring) and then encodes that as @LIN/@INV in the canonical symbol (discarding the raw _UM/_CM infix)
  plus reformats the expiry to 8-digit YYYYMMDD (vs OKX's native 6-digit YYMMDD) -- the exact shape confirmed
  live-resolved in production. So both repos have a real, deliberate, independently-reasoned convention for this one
  venue, and they disagree. Fixing MTDS's reverse-mapper to strip the marker + reconstruct the real _UM/no-infix +
  6-digit-date wire form (mirroring instruments-service's inference logic) would restore some OKX-FUTURES capture, but
  (a) it means re-implementing instruments-service's OKX-specific margin-type-inference logic inside MTDS, a real
  service-boundary concern (T4 services import only UTL/UAC/unified-*-interface, never each other -- this venue-specific
  inference has never been factored into a shared UAC helper both sides could call), and (b) at least one confirmed
  universe entry (OKX-FUTURES:FUTURE:AAPL-USD@LIN-20310613, expiry 2031-06-13) does not obviously correspond to any real
  OKX-listed dated-futures contract per the existing tokenized-equity research
  (cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md line 454: OKX's US-equity contracts, including AAPL, are
  documented as AAPL-USDT-SWAP -- i.e. SWAP/PERPETUAL type, never a dated FUTURE) -- raising an unresolved question of
  whether instruments-service's OKX-FUTURES universe generation is itself producing synthetic/non-existent contract
  entries independent of the id-format question. Neither sub-question is a same-repo, single-file bug fix; both need an
  operator call before code changes, per this workspace's dispatch-scope-eligibility rule (a judgment/design call is not
  a bounded todo).
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service, instruments-service]
scope: [engineer, admin]
tags:
  [
    data-correctness,
    cefi,
    okx-futures,
    instrument-id,
    canonical-id,
    live-capture,
    cross-repo,
    operator-decision,
    margin-marker,
  ]
related:
  [
    /plans/archive/issues/instrument_id_format_canonicalization_2026_07_08.md,
    /plans/active/cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
  ]
created: 2026-07-30
author: unknown
parent_epic: cefi_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: research
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.72
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
source: live-fix-worker (dispatched for market-tick-data-service live CeFi capture-gap fix, 2026-07-30)
resolved_by:
context_scope:
  [
    /plans/archive/issues/instrument_id_format_canonicalization_2026_07_08.md,
    /plans/active/cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md,
    market-tick-data-service/market_tick_data_service/live/connectors/okx_futures_ws.py,
    market-tick-data-service/market_tick_data_service/live/connectors/okx_ws.py,
    instruments-service/instruments_service/reference_data/adapters/cefi/tardis/parsing.py,
  ]
---

## What's blocked

OKX-FUTURES live capture (trades + book_snapshot_5 + derivative_ticker) stays at 0 rows until an operator picks ONE of
the two live, mutually-incompatible canonical-instrument_id conventions below for this venue. The sibling
BINANCE-FUTURES/ASTER book_snapshot_5 bug (real depthUpdate wire shape, "b"/"a" not "bids"/"asks") from the same
investigation was a bounded, evidenced, zero-ambiguity fix and has been SHIPPED (market-tick-data-service@4f244845,
quality-gates green, 7627 passed). This OKX-FUTURES portion was deliberately NOT force-fixed in that same session -- see
reasoning above.

## Options

- A. Adopt the uniform @LIN/@INV-YYYYMMDD convention for OKX-FUTURES too (matching every other dated-derivative venue
  and instruments-service's actual deployed builder) -- update MTDS's
  _instrument_to_okx_futures_inst_id/_build_okx_futures_canonical_id (okx_futures_ws.py) to strip the marker, re-derive
  the real _UM/no-infix wire form + 6-digit date, and delete the module docstring's now-false "no marker" claim. Needs
  the OKX-specific _UM/_CM margin inference either duplicated (with an explicit note it must be kept in lockstep with
  instruments-service's copy) or promoted into a shared UAC helper both sides import. [WORKER REC -- keeps every venue's
  format uniform, least special-casing long-term]
- B. Revert instruments-service's OKX-FUTURES id generation to the raw-passthrough (no marker) convention, matching what
  MTDS's connector already expects and what the 2026-07-09/07-10 decision documented -- smaller code change (one repo,
  tardis/parsing.py's OKX branch) but re-introduces a venue-specific carve-out other engineers have already been bitten
  by once (this doc).
- C. First resolve the SEPARATE data-integrity question (is OKX-FUTURES:FUTURE:AAPL-USD@LIN-20310613 a real,
  currently-listed OKX contract, or a synthetic/placeholder universe entry?) via a live OKX
  /api/v5/public/instruments?instType=FUTURES pull, before committing to A or B -- if a material fraction of the
  137-instrument universe doesn't correspond to real OKX contracts, fixing the id-mapper alone won't restore full
  capture regardless of which convention wins.
- Other: operator can type a custom answer.

## Follow-up todos (once the operator decides)

- [x] ✅ [OPERATOR] P1. **RULED 2026-08-06 (operator), option A: ratify the already-shipped convention.** Matches every
      other dated-derivative venue and instruments-service's actual deployed builder — no revert needed. The sibling
      `[SCRIPT] P1` todo below (docstring reconciliation) already independently confirmed done-elsewhere in this same
      governance sweep (see `cefi_satellite_ao_dispatch_batch8_2026_08_06.md` todo 3). Decide convention A vs B vs
      C-first for OKX-FUTURES canonical instrument_id (this doc).
- [ ] [SCRIPT] P1. **CORRECTED 2026-08-04 (na-eligibility-audit) — the "whichever side loses, implement" framing is
      stale.** Option A's reverse-mapper fix already shipped (`market-tick-data-service@8a6bbc97`, 2026-07-30 22:55 UTC
      — landed BEFORE this operator decision, without the sign-off `[OPERATOR] P1` above requires). Remaining scope,
      either branch: (a) ✅ DONE-ELSEWHERE 2026-08-06 (batch8 todo 3, governance-sweep activation-readiness check) —
      `okx_futures_ws.py`'s module docstring already correctly describes the shipped `@LIN`/`@INV` marker convention;
      the "no marker" narrative was stale in this doc's text, not in the live file. Verified at
      `market-tick-data-service@8a6bbc97` and re-confirmed present in the LDR→main squash-promote `b5a1aa73`
      (2026-07-31). No code change needed for sub-part (a). (b) MOOT — `[OPERATOR] P1` ratified Option A 2026-08-06, no
      Option-B revert will be performed. Checkbox left open per
      `cefi_satellite_ao_dispatch_batch8_2026_08_06_finalize.md` todo 1 (batch8 finalize reconciliation 2026-08-07).
      **Remaining open in this doc: `[SCRIPT] P1` (nominally — both sub-parts resolved/moot as noted above), `[DATA] P1`
      (xperp wire-format fix — see new todo below)** — 2 items. `[SCRIPT] P2` and `[RESEARCH] P2` closed.
- [x] ✅ [SCRIPT] P2. Add a live-vs-batch OKX-FUTURES instrument_id parity test (mirroring the existing
      BINANCE-FUTURES/KRAKEN-FUTURES parity tests) so this class of drift can't silently regress again.
      `market-tick-data-service/tests/unit/test_okx_futures_live_batch_id_parity.py` —
      market-tick-data-service@d964dce4; QG green 2026-08-07 (exit 0, 14 parity tests pass).
- [x] ✅ [RESEARCH] P2. Live-verify whether AAPL-USD (and any other equity-underlying) OKX-FUTURES dated-future universe
      entries correspond to real, currently-listed OKX contracts (option C above) -- confirm via
      /api/v5/public/instruments?instType=FUTURES, not ccxt's cached market list. **CONFIRMED 2026-08-07 (slot 15,
      cefi_satellite_ao_dispatch_batch6-006)**: AAPL-USD and all equity-underlying OKX-FUTURES entries ARE real live OKX
      contracts (`ruleType=xperp`, "extended perpetual" 5-year dated futures). Live API
      (`/api/v5/public/instruments?instType=FUTURES`, 2026-08-07): 139 instruments total — 35 `ruleType=normal`
      (weekly/quarterly BTC/ETH) + 104 `ruleType=xperp` (wire format `BASE-USD_UM_XPERP-YYMMDD`). AAPL:
      `AAPL-USD_UM_XPERP-310613`, state=live, ctType=linear, expiry=2031-06-13. 28 equity/ETF-like xperp confirmed: AAPL
      AMD AMZN GOOGL META MSFT NVDA TSLA AAOI BILL COIN CRCL EWY HOOD INTC MRVL MSTR MU PLTR QCOM QQQ SAMSUNG SKHYNIX
      SNDK SOFTBANK SOXL SPCX SPY (all state=live). ⚠️ **SECONDARY FINDING (data-correctness, OPERATOR NOTIFIED)**: all
      104 xperp instruments use wire format `BASE-USD_UM_XPERP-YYMMDD` which `_OKX_FUTURES_WIRE_RE` (only matches
      `_UM-YYMMDD` and plain inverse) and `_instrument_to_okx_futures_inst_id` do NOT handle — xperp wire ids fall
      through to passthrough on inbound, and the reverse mapper produces `AAPL-USD_UM-310613` (a non-existent OKX
      instId) for subscription. The just-shipped parity test (`market-tick-data-service@d964dce4`) also uses the wrong
      `AAPL-USD_UM-310613` wire form for its AAPL parity case. All 104 xperp subscriptions silently fail at 0 rows. New
      `[DATA] P1` todo added below.
- [ ] [OPERATOR] P1. **CORRECTED 2026-08-12 (/plan-reconcile)** — retagged `[DATA]` → `[OPERATOR]`: this todo's own text
      (below) says "Needs `[OPERATOR]` decision ... tagging `[OPERATOR]` until decided," and the doc's own 2026-08-09
      na-eligibility-audit entry independently confirms "genuine operator-gated design work" — the bracket tag was never
      actually updated to match. **Add `_XPERP` infix support to OKX-FUTURES wire-format handling**
      (`market-tick-data-service`). In `okx_futures_ws.py`: (1) extend `_OKX_FUTURES_WIRE_RE` to match
      `BASE-USD_UM_XPERP-YYMMDD` (add optional `_XPERP` after `_UM`) and set infix group to linear; (2) update
      `_instrument_to_okx_futures_inst_id` to emit `AAPL-USD_UM_XPERP-{yymmdd}` for xperp instruments (operator decision
      needed: how to distinguish xperp vs non-xperp linear contracts from the canonical id alone — the canonical
      `@LIN-YYYYMMDD` shape is shared by `BTC-USD_UM-260814` and `AAPL-USD_UM_XPERP-310613`; options: (a) lookup via
      instruments-service at subscribe time, (b) encode `_XPERP` in the instFamily field, (c) use expiry heuristic: >3
      years = xperp). **Also update** `tests/unit/test_okx_futures_live_batch_id_parity.py` to add
      `AAPL-USD_UM_XPERP-310613` ↔ `OKX-FUTURES:FUTURE:AAPL-USD@LIN-20310613` parity. Source: `[RESEARCH] P2` above
      (2026-08-07). Needs `[OPERATOR]` decision on (a)/(b)/(c) before implementation — tagging `[OPERATOR]` until
      decided.

## Progress Log (na-eligibility-audit)

- **na-eligibility-audit 2026-08-01** (tranche=cefi, autonomous): KEEP-NA, stale-items — **and flagging a real
  production-safety finding, not just a checkbox nit.** This doc's body frames `[OPERATOR] P1` as gating ALL code
  changes ("both need an operator call before code changes") and claims OKX-FUTURES capture "stays at 0 rows" pending
  that decision. **Both claims are now stale**: `market-tick-data-service@8a6bbc97` (2026-07-30 22:55 UTC — landed
  BEFORE this doc was even committed) already implemented this doc's Option A in `okx_futures_ws.py` (the
  `@LIN`/`@INV`-marked canonical id) WITHOUT the operator sign-off this doc says is required, and OKX-FUTURES
  `book_snapshot_5` is independently live-verified producing real, non-empty rows in production as of 2026-07-31T21:14Z
  (`live_event_log_warm_sink_recovery_and_cold_compaction_2026_07_31.md` P1.1). The shipped code's own docstring also
  narrates the OKX-FUTURES exemption's history DIFFERENTLY than this doc's body does — two conflicting accounts written
  hours apart, never reconciled. **`[SCRIPT] P1` should be understood as already-code-complete for the Option-A half**
  (not "whichever side loses, implement" — A already shipped, reverting is still possible but is the harder path now);
  `[OPERATOR] P1` needs re-framing from "decide before any code changes" to "ratify or override a fait-accompli change
  already live on a production data-capture path, made without first resolving Option C's data-integrity prerequisite as
  this doc's own Options section says it should have." `[SCRIPT] P2` (parity test) and `[RESEARCH] P2`
  (AAPL-USD@LIN-20310613 real-contract check) stay open and unaffected — `[RESEARCH] P2` is now MORE urgent since A
  shipped without it. Doc stays `assigned_vm: NA` — the remaining question is squarely an operator ratification call,
  now higher-stakes. **Surfacing prominently**: a worker bypassed a documented required-sign-off gate on live
  data-capture code; operator should see this doc's `[OPERATOR] P1` item with the above context, not the original
  "nothing shipped yet" framing.
- **context-scout 2026-08-03**: populated context_scope (5 entries).
- **na-eligibility-audit 2026-08-04** (tranche=cefi, autonomous): KEEP-NA, stale items — reaffirms the 2026-08-01
  verdict (nothing has changed in the doc since besides the context-scout refresh) and actually applies the correction
  that entry only described in prose: rewrote `[SCRIPT] P1`'s text in place (still open — docstring reconciliation +
  contingent Option-B revert remain live work). `[OPERATOR] P1` stays open and NA (genuine, now higher-stakes
  ratification call); `[SCRIPT] P2`/`[RESEARCH] P2` unaffected.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (5 entries), unchanged.
- **na-eligibility-audit 2026-08-06** (tranche=cefi, autonomous): KEEP-NA, valid — `[OPERATOR] P1` ratification remains
  the load-bearing open gate. Today's independent `/ag-closeout-audit cefi` run reached convergent classification,
  drafting (not activating) the non-operator sub-items into batch6/batch8 — strong cross-validation that whole-doc NA
  pending operator ratification is correct.
- **na-eligibility-audit 2026-08-07**: KEEP-NA, valid — do NOT re-litigate: the 2026-08-07 batch8-finalize pass already
  explicitly ruled to leave the [SCRIPT] P1 item open nominal-only; 3 genuine-work items remain.
- **research-worker 2026-08-07 (slot 15, cefi_satellite_ao_dispatch_batch6-006)**: `[RESEARCH] P2` DONE — OKX DOES list
  AAPL-USD and other equity-underlying FUTURES as real contracts: 28 equity/ETF-like + 76 crypto = 104 `ruleType=xperp`
  instruments, all `state=live`, wire format `BASE-USD_UM_XPERP-YYMMDD`, 5-year expiries (alias=`this_five_years`).
  Universe NOT synthetic. ⚠️ DATA-CORRECTNESS FINDING: `_OKX_FUTURES_WIRE_RE` + `_instrument_to_okx_futures_inst_id` do
  not handle `_XPERP` infix — 104/139 OKX-FUTURES contracts fall through to passthrough or generate a non-existent
  subscribe instId; parity test (`market-tick-data-service@d964dce4`) tests wrong wire format for AAPL. New `[DATA] P1`
  (needs `[OPERATOR]` decision on xperp-vs-linear disambiguation) added above.
- **na-eligibility-audit 2026-08-09** (tranche=cefi, autonomous): KEEP-NA, valid — verified
  cefi_satellite_ao_dispatch_batch8_2026_08_06_finalize.md todo 1 (status: complete, archived): its own reconciliation
  deliberately left the [SCRIPT] P1 checkbox open ('checkbox left open per plan') even though both sub-parts are
  resolved/moot — an established, cited ruling, not new staleness. No action needed; [DATA] P1 (xperp wire-format) is
  genuine operator-gated design work.

## Progress Log (context-scout)

- **context-scout 2026-08-09**: populated/refreshed context_scope (5 entries).
