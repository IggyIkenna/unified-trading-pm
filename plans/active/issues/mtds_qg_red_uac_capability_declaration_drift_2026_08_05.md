---
doc_type: issue
title: >-
  MTDS quality-gates.sh is RED on LDR baseline — 2 pre-existing cross-repo failures from today's UAC
  capability-declaration commits (AAVE `collect-rewards`, POLYMARKET `fills`) block ALL MTDS shipping
summary: >-
  Two MTDS unit tests fail on the clean LDR baseline (no relation to any in-flight MTDS change). Both were introduced
  TODAY by UAC commits on the editable PATH source: UAC@b2874193 (08-05 12:15, "add 10 undeclared DeFi data_types to
  PROTOCOL_CAPABILITIES") declared `collect-rewards` in AAVE's `mtds_operations` with no MTDS handler module, and
  UAC@6e791b05 (08-05 12:07, "declare market_metadata and fills in VENUE_DATA_TYPE_CAPABILITIES for POLYMARKET/KALSHI")
  declared `fills` for POLYMARKET, which the Tier-3 per-instrument sentinel emits as an instrument-less row. Because
  MTDS commits only from a quality-gates.sh-GREEN tree (HARD RULE), the red baseline is blocking every MTDS ship —
  including the unrelated per-date iterrows()→cached-row-dict fix (fred_backfill_early_date_indefinite_stall_2026_07_30,
  no-regression-proven: 9999 passed vs 9996 baseline, delta = exactly its 3 new tests). Both failures need a decision
  from the declaring UAC-owner side (are the declarations aspirational or is capture being wired?); neither is safely
  guessable from the MTDS side.
status: open
nature: issue
asset_group: [defi, prediction]
stage: [data]
repos: [unified-api-contracts, market-tick-data-service]
scope: [engineer]
tags: [data-correctness, cross-repo, ci-red, capability-declarations, protocol-capabilities, sentinel, operator-notify]
related: [defi_protocol_capabilities_lst_rates_audit_2026_08_05, fred_backfill_early_date_indefinite_stall_2026_07_30]
created: 2026-08-05
priority: P0
parent_epic: infrastructure_master
source: slot-7
assigned_vm: planning
execution_scope: orchestrator-agent
drift_direction: advance-docs
resolved_by:
locked_by:
---

# MTDS QG red from UAC capability-declaration drift

## Findings (both reproduced on a clean MTDS baseline, 08-05)

### 1. `test_protocol_class_ops_have_modules[lending]` — AAVE `collect-rewards`

- **UAC commit**: `unified-api-contracts@b2874193` (08-05 12:15) added `collect-rewards` to AAVE's `mtds_operations` in
  `unified_api_contracts/registry/capability_declarations/_defi.py` (~line 443, ProtocolClass.LENDING).
- **MTDS test**: `tests/unit/test_collect_handler_schema.py:187-194` asserts every declared mtds_operation has an entry
  in `_CLI_OP_TO_MODULE`. There is no `collect-rewards` key — only `collect-eigenlayer-rewards`.
- **Class**: declared-but-unimplemented operation — the same class as the audit's Finding C
  (`/plans/active/issues/defi_protocol_capabilities_lst_rates_audit_2026_08_05.md`, resolved for LIDO/ETHERFI by
  removing aspirational `rewards` at `unified-api-contracts@bc397b93`). AAVE's `collect-rewards` was added AFTER that
  resolution and is unwired.

### 2. `test_tier3_prediction_polymarket_no_crash` — POLYMARKET `fills`

- **UAC commit**: `unified-api-contracts@6e791b05` (08-05 12:07) declared `market_metadata` and `fills` in
  `VENUE_DATA_TYPE_CAPABILITIES` for POLYMARKET/KALSHI.
- **MTDS test**: `tests/unit/test_orchestrator_per_data_type_sentinel.py:988` (invariant at line 1051
  `assert rk.get("instrument_id")`) — the Tier-3 per-instrument fan-out now emits a PREDICTION POLYMARKET `fills` row
  with empty `instrument_type`, so the derived `instrument_id` is falsy. Sentinel logs
  `data_type 'fills' is not valid for this venue's asset group` yet still emits the instrument-less row.

## Why it matters

- MTDS commits only from a `quality-gates.sh`-GREEN tree (HARD RULE, `/codex/06-coding-standards/quality-gates.md`). The
  red baseline freezes **all** MTDS shipping — CI (`quality-gates-v2`) will go red on the next run that reaches pytest,
  and local quickmerge re-gates will abort.
- Evidence the failures are PRE-EXISTING (not any in-flight MTDS change): both reproduce on the unmodified baseline; my
  iterrows fix runs 9999 passed / 2 failed vs baseline 9996 passed / 2 failed — the exact delta is its 3 new regression
  tests (`fred_backfill_early_date_indefinite_stall_2026_07_30`).
- Honest-coverage denominator: both declarations change the EXPECTED matrix (`_venue_itype_is_valid` / per-instrument
  fan-out) before capture is wired — the same declared-but-not-collected failure mode the audit documented.

## Resolution options (need UAC-owner intent, NOT guessable from MTDS side)

- **#1 (collect-rewards)**: (a) remove `collect-rewards` from AAVE's `mtds_operations` in UAC (consistent with the
  audit's `bc397b93` pattern) IF AAVE rewards collection is not implemented; or (b) wire a `collect-rewards` →
  handler-module mapping in MTDS IF an AAVE rewards handler exists/should be built.
- **#2 (fills)**: (a) MTDS sentinel must not emit an instrument-less `fills` row for a venue whose asset_group doesn't
  support `fills` (skip venue-level-invalid dts); or (b) scope/revert the `fills` declaration for POLYMARKET in UAC if
  prediction fills capture is not imminent.

## Status / owner

- **Owner**: the workers who landed `unified-api-contracts@6e791b05` and `@b2874193` (or operator-gated decision on
  which of (a)/(b) each resolves to).
- **Unblock criterion**: MTDS `bash scripts/quality-gates.sh` green on LDR baseline. Once green, the staged iterrows fix
  ships immediately.
- **Fleet-wide context**: slot-14 reports the SAME UAC churn wave reds instruments-service's defi expected-universe
  golden (`instruments_service_defi_golden_red_capability_lockstep_gap_2026_08_05.md`): 12 `PROTOCOL_CAPABILITIES`
  commits 2026-08-05 11:07Z→12:29Z, with nobody owning lockstep golden regen. The two blocking commits here (`6e791b05`
  @12:07Z, `b2874193` @12:15Z) landed inside that wave — a fleet-wide mid-audit state, not a single rogue declaration.
  Operator resolution should cover the wave (aspirational-vs-wired decision per declaration), not just these two.
- **Promote-lag nuance (verified 08-05 14:30Z)**: UAC `origin/main` is at `8de39ca2` (last LDR→main promote 08:49Z),
  which PRE-DATES the 12:07Z/12:15Z declarations — so both blockers are absent from main only by lag, NOT by revert. The
  next `*/15` promote carries them onto main and flips MTDS CI red on the first run that reaches pytest. A fresh session
  must NOT read "blocker absent from UAC main" as resolved; LDR HEAD (`6e791b05`) is the ground truth until an explicit
  revert/scope lands on LDR.
- **NOTIFIED**: operator via this doc (cross-repo, CI-red — big-finding class,
  `/codex/11-project-management/ plan-priority-tier-and-dispatch-ordering.md` findings triage).
