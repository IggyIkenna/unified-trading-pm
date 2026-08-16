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
status: active
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

# OKX-FUTURES xperp wire-format fix

## Todos

- [ ] [DATA] P1. **RULED 2026-08-16 (operator): option (b) — encode `_XPERP` in the instFamily field.**
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

- **2026-08-16 (na-eligibility-audit follow-up Q&A round 6, operator ruling)**: extracted from
  `okx_futures_instid_marker_convention_mismatch_2026_07_30.md`; operator chose option (b) of the 3 listed
  disambiguation options (lookup via instruments-service / encode in instFamily / expiry heuristic).
