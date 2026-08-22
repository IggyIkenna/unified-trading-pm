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
last_updated: 2026-08-21
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
    market-tick-data-service/tests/unit/test_okx_futures_live_batch_id_parity.py,
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
- [x] ✅ [OPERATOR] P1. **na-eligibility-audit 2026-08-16**: this doc's own 2026-08-16 Progress Log entry records the operator ruling + extraction of this exact scope to `cefi_okx_futures_xperp_marker_ao_dispatch_2026_08_16.md` (+ finalize), assigned_vm: planning, status: active — DONE 2026-08-16, `market-tick-data-service@3acdd478e5` (see that plan's Progress Log for full evidence). Original text: **CORRECTED 2026-08-12 (/plan-reconcile)** — retagged `[DATA]` → `[OPERATOR]`: this todo's own text
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
- [x] ✅ EXTRACTED — see `cefi_satellite_ao_dispatch_batch21_2026_08_17.md` item 3 (na-eligibility-audit 2026-08-17,
      cefi tranche, conflict-checked clear). Original: [RESEARCH] P2. **NEW 2026-08-16 (slot 6, follow-up gap from the `[DATA]`/`[OPERATOR] P1` fix above).** The
      shipped `_OKX_FUTURES_XPERP_EQUITY_BASES` set in `okx_futures_ws.py` only enumerates the 28 confirmed
      equity/ETF-like xperp base symbols from `[RESEARCH] P2`'s 2026-08-07 finding (AAPL AMD AMZN GOOGL META MSFT
      NVDA TSLA AAOI BILL COIN CRCL EWY HOOD INTC MRVL MSTR MU PLTR QCOM QQQ SAMSUNG SKHYNIX SNDK SOFTBANK SOXL
      SPCX SPY). The remaining 76 confirmed-live crypto xperp base symbols (part of the same 104-instrument
      `ruleType=xperp` universe, `/api/v5/public/instruments?instType=FUTURES`) were never enumerated by name in
      that finding, so `_instrument_to_okx_futures_inst_id` still emits the plain non-XPERP wire form for them —
      those contracts remain silently mis-subscribed (same failure mode as the equity ones, just not yet fixed).
      Live-verify + enumerate the 76 crypto base symbols via `/api/v5/public/instruments?instType=FUTURES`
      (`ruleType=xperp`, excluding the 28 already-known equity/ETF ones), then add them to
      `_OKX_FUTURES_XPERP_EQUITY_BASES` (or a sibling crypto set) in `market-tick-data-service`'s
      `okx_futures_ws.py`. Repo: market-tick-data-service.
- [ ] [DATA] P2. **RULED 2026-08-21 (D15, ADOPTED-REC): implement instFamily-based lookup at subscribe time**
      (option b) for BTC/ETH/SOL/XAU xperp-vs-normal disambiguation — deterministic and consistent with the
      already-ruled mechanism for the original xperp ambiguity (`[OPERATOR] P1` above, RULED 2026-08-16). **NEW
      2026-08-18 (slot 15, follow-up gap surfaced while closing the item above).** Live re-verification
      (`/api/v5/public/instruments?instType=FUTURES`, 2026-08-18) found the confirmed-live xperp universe grew to
      128 instruments (125 `state=live`), and — separately from the stale "76" figure — found that 4 bases (BTC,
      ETH, SOL, XAU) carry BOTH live `ruleType=xperp` AND live `ruleType=normal` (near-term weekly/quarterly)
      contracts. `okx_futures_ws.py`'s reverse mapper (`_instrument_to_okx_futures_inst_id`) disambiguates
      xperp-vs-normal via a static base-membership check against `_OKX_FUTURES_XPERP_BASES` (renamed from
      `_OKX_FUTURES_XPERP_EQUITY_BASES`, `market-tick-data-service@6436fcbe01`) — this only works because every
      OTHER xperp base has no normal-type sibling contract. For these 4 bases the canonical `@LIN-YYYYMMDD` id is
      genuinely ambiguous (identical shape for both contract types), so they are deliberately EXCLUDED from the
      set — meaning their own xperp dated-futures remain silently mis-subscribed (same failure mode this whole doc
      chases), while their normal-type contracts continue to work correctly (unaffected, unambiguous default).
      **Done when**: `okx_futures_ws.py` resolves BTC/ETH/SOL/XAU xperp-vs-normal via a live instFamily lookup at
      subscribe time (not a static base-membership set), and a parity test asserts all 4 bases correctly route to
      their xperp contract when one is live. Repo: market-tick-data-service.

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
- **2026-08-16 (na-eligibility-audit follow-up Q&A round 6, operator ruling)**: the open `[OPERATOR]` P1 xperp
  wire-format todo is RULED — option (b), encode `_XPERP` in the instFamily field. Extracted to
  `/plans/archive/2026_08/cefi_okx_futures_xperp_marker_ao_dispatch_2026_08_16.md` (+ finalize, now archived — done
  2026-08-18) for AO dispatch, since this
  doc stays `assigned_vm: NA`. Do not re-litigate the (a)/(b)/(c) choice.

## Progress Log

- **na-eligibility-audit 2026-08-16** [body-hash:204e1fba79b30ecd]: KEEP-NA, stale-citation fix applied (checkbox(es) corrected to cite where the work actually landed -- see inline citations above). Doc stays assigned_vm: NA.
- **na-eligibility-audit 2026-08-17 (cefi tranche)** [body-hash:6fb3d5716bd463b0]: RECLASSIFY-SPLIT — extracted the newly-added [RESEARCH] P2 item (76 crypto xperp base-symbol enumeration, added 2026-08-16 after this doc's prior marker) to `cefi_satellite_ao_dispatch_batch21_2026_08_17.md` item 3, conflict-checked clear (no other active doc claims this ground). The [SCRIPT] P1 item stays NA on its own repeatedly-established "nominal-only, do not re-litigate" ruling (`cefi_satellite_ao_dispatch_batch8_2026_08_06_finalize.md` todo 1) — not re-opened. Doc stays assigned_vm: NA for that remaining item. Note: this doc's prior marker looked hash-current under the pre-fix inventory script because a same-dated INLINE CITATION of the marker convention inside the [OPERATOR] P1 todo's own text (line ~129 area, no `[body-hash:]` tag) was being matched as if it were a real, later marker — fixed at the root by a concurrent same-day dispatch (`unified-trading-pm@b57b839a6b`, sports-tranche discovery of the identical bug, independently confirmed here on cefi content).
- **na-eligibility-audit 2026-08-18 (cefi tranche)** [body-hash:694008c2e8776a8a]: KEEP-NA, valid — reaffirmed, no re-litigation. The sole remaining open item ([SCRIPT] P1, line 134) stays on the same repeatedly-established "nominal-only, do not re-litigate" ruling (`cefi_satellite_ao_dispatch_batch8_2026_08_06_finalize.md` todo 1), confirmed across every prior audit pass on this doc (2026-08-01 through 2026-08-17, most recently the 2026-08-17 RECLASSIFY-SPLIT pass which explicitly left it NA). Doc stays assigned_vm: NA.
- **2026-08-16 (slot 6, backend_engineer)**: `[OPERATOR] P1` DONE — `market-tick-data-service@3acdd478e5` (via
  `cefi_okx_futures_xperp_marker_ao_dispatch_2026_08_16.md`), QG green (10968 passed, 0 failed). Filed new
  `[RESEARCH] P2` above for the 76 unenumerated crypto xperp base symbols — genuine remaining gap, not fully closed
  by this fix.
- **context-scout 2026-08-17**: populated/refreshed context_scope (5 entries)
- **2026-08-18 (slot 15, backend_engineer, task cefi_satellite_ao_dispatch_batch21-f8e8608af7cc)**: closed the
  extracted `[RESEARCH] P2` crypto-xperp-enumeration item (see `cefi_satellite_ao_dispatch_batch21_2026_08_17.md`
  item 3) — `market-tick-data-service@6436fcbe01`, QG green (11072 passed). Live re-verification found the universe
  grew (104→128 xperp instruments since 2026-08-07) and the crypto count is 97, not the stale "76". Added 93 of
  those 97 to the renamed `_OKX_FUTURES_XPERP_BASES` set; filed a new `[OPERATOR] P2` todo above for the remaining 4
  (BTC/ETH/SOL/XAU) — a genuine xperp-vs-normal disambiguation gap discovered live, deliberately not papered over.
- **na-eligibility-audit 2026-08-18 (re-verify, same-day)** [body-hash:bbe2c34ebd59bd47]: KEEP-NA, valid — re-verified after
  this doc's own later-same-day append (batch21 item 3 closed, new [OPERATOR] P2 filed for the 4 remaining BTC/ETH/
  SOL/XAU ambiguous xperp-vs-normal bases). 2 open items: [SCRIPT] P1 stays on its repeatedly-established
  "nominal-only, do not re-litigate" ruling; the new [OPERATOR] P2 is a genuine operator design-decision
  (instFamily-lookup vs expiry-heuristic vs accept-gap), consistent with this doc's established pattern. Doc stays
  assigned_vm: NA.
- **context-scout 2026-08-20**: refreshed context_scope (6 entries)
- **2026-08-21 — ruling D15 (OKX-FUTURES xperp disambiguation)**: ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): instFamily lookup — deterministic and consistent with the already-ruled mechanism for the original xperp ambiguity. Source: /plans/active/issues_corpus_completion_dispatch_2026_08_21.md ledger.
