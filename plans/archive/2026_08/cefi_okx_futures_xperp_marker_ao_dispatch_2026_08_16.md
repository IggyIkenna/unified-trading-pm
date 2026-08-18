---
doc_type: plan
title: OKX-FUTURES xperp wire-format fix — encode _XPERP in instFamily field (operator-ruled 2026-08-16)
summary: >-
  Operator-ruled 2026-08-16 (na-eligibility-audit follow-up Q&A round 6) on the `[OPERATOR]` P1 todo in
  okx_futures_instid_marker_convention_mismatch_2026_07_30.md: option (b) — encode `_XPERP` in the instFamily
  field to distinguish OKX's 104 xperp (5-year dated futures, ruleType=xperp) contracts from regular linear
  futures, which currently collide under the same canonical @LIN-YYYYMMDD id shape (all 104 xperp subscriptions
  silently fail at 0 rows today). Extracting into its own AO-dispatch plan since the parent issue doc stays
  assigned_vm: NA.
status: archived
nature: process
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [cefi, okx, xperp, canonicalization, instrument-id]
related:
  [
    /plans/active/issues/okx_futures_instid_marker_convention_mismatch_2026_07_30.md,
  ]
created: "2026-08-16"
last_updated: "2026-08-16"
parent_epic: cefi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.6
assigned_role: backend_engineer
effort: max
drift_direction: advance-code
depends_on: []
supersedes:
superseded_by:
source: "na-eligibility-audit follow-up Q&A round 6, 2026-08-16 — operator ruling option (b) on okx_futures_instid_marker_convention_mismatch_2026_07_30.md"
locked_by:
context_scope:
  [
    /plans/active/issues/okx_futures_instid_marker_convention_mismatch_2026_07_30.md,
    market-tick-data-service/tests/unit/test_okx_futures_live_batch_id_parity.py,
  ]
locked_since:
resolved_by:
---

> **ARCHIVED 2026-08-18** — superseded by (completed alongside) its finalize companion,
> `/plans/archive/2026_08/cefi_okx_futures_xperp_marker_ao_dispatch_2026_08_16_finalize.md`. All todos done.

# OKX-FUTURES xperp wire-format fix

## Todos

- [x] ✅ [DATA] P1. **RULED 2026-08-16 (operator): option (b) — encode `_XPERP` in the instFamily field.**
      market-tick-data-service@3acdd478e5.
      `market-tick-data-service/.../okx_futures_ws.py`: (1) extend `_OKX_FUTURES_WIRE_RE` to match
      `BASE-USD_UM_XPERP-YYMMDD` (add optional `_XPERP` after `_UM`) and set infix group to linear; (2) update
      `_instrument_to_okx_futures_inst_id` to emit `AAPL-USD_UM_XPERP-{yymmdd}` for xperp instruments, distinguishing
      them from non-xperp linear contracts via the instFamily field (not the expiry heuristic, not a live
      instruments-service lookup). Also update `tests/unit/test_okx_futures_live_batch_id_parity.py` to add
      `AAPL-USD_UM_XPERP-310613` ↔ `OKX-FUTURES:FUTURE:AAPL-USD@LIN-20310613` parity. Source evidence: 104/139
      OKX-FUTURES contracts are `ruleType=xperp` (28 equity/ETF-like incl. AAPL, 76 crypto), all `state=live`,
      wire format `BASE-USD_UM_XPERP-YYMMDD`, currently 100% silently failing at 0 rows. Repo:
      market-tick-data-service.

## Progress Log

- **context-scout 2026-08-17**: populated/refreshed context_scope (2 entries)
- **2026-08-16 (na-eligibility-audit follow-up Q&A round 6, operator ruling)**: extracted from
  `okx_futures_instid_marker_convention_mismatch_2026_07_30.md`; operator chose option (b) of the 3 listed
  disambiguation options (lookup via instruments-service / encode in instFamily / expiry heuristic).
- **2026-08-16 (slot 6, backend_engineer)**: ✅ DONE — `market-tick-data-service@3acdd478e5`, quality-gates green
  (10968 passed, 0 failed; sentinel `.qg_last_passed_sha=3acdd478e544b11db8d05cf31f255769e0da96cc`). Implemented
  option (b) as a static `_OKX_FUTURES_XPERP_EQUITY_BASES` instFamily (base-quote) membership check in
  `okx_futures_ws.py`, not a live lookup or expiry heuristic. Fixed the AAPL parity case in both
  `test_okx_futures_live_batch_id_parity.py` and the pre-existing `test_okx_futures_ws_2026_07_13.py` (which the
  QG run's first pass caught as 3 regressions — the old `AAPL-USD_UM-310613` expectation was never a real OKX wire
  form; corrected to `AAPL-USD_UM_XPERP-310613`). **Scope note**: only the 28 confirmed-live equity/ETF xperp bases
  are enumerated (exact match to the `[RESEARCH] P2` 2026-08-07 finding); the remaining 76 confirmed-live crypto
  xperp bases are NOT yet enumerated by name in this codebase, so those contracts still round-trip through the
  plain (non-xperp) wire form and remain silently unfixed. Follow-up todo filed on
  `okx_futures_instid_marker_convention_mismatch_2026_07_30.md` to enumerate + add them. This plan's only todo is
  now done — eligible for archival.
