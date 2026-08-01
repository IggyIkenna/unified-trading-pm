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
    /plans/active/issues/instrument_id_format_canonicalization_2026_07_08.md,
    /plans/active/cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md,
  ]
created: 2026-07-30
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

- [ ] [OPERATOR] P1. Decide convention A vs B vs C-first for OKX-FUTURES canonical instrument_id (this doc).
- [ ] [SCRIPT] P1. Whichever side loses: implement the reverse-mapper/builder fix in that repo (MTDS okx_futures_ws.py
      for A, instruments-service tardis/parsing.py OKX branch for B) + update the stale module docstring claim.
- [ ] [SCRIPT] P2. Add a live-vs-batch OKX-FUTURES instrument_id parity test (mirroring the existing
      BINANCE-FUTURES/KRAKEN-FUTURES parity tests) so this class of drift can't silently regress again.
- [ ] [RESEARCH] P2. Live-verify whether AAPL-USD (and any other equity-underlying) OKX-FUTURES dated-future universe
      entries correspond to real, currently-listed OKX contracts (option C above) -- confirm via
      /api/v5/public/instruments?instType=FUTURES, not ccxt's cached market list.

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
