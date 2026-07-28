---
doc_type: issue
title:
  "Solana address primitives (base58 codec + ed25519 on-curve + find_program_address) duplicated across sibling mtds
  handlers"
summary: >-
  market_tick_data_service ships base58 codec logic in two sibling CLI handlers independently:
  cli/handlers/raydium_classic_amm_handler.py carries its own _BASE58_ALPHABET + _base58_encode, and
  defi_satellite_ao_dispatch_batch1-007 (mtds@f771e841) added cli/handlers/orca_whirlpool_state_handler.py which
  hand-rolls base58 encode/decode + ed25519 on-curve + PDA (find_program_address) derivation locally. base58 is now
  duplicated across the two handlers, and orca's ed25519/PDA math has no shared home yet. A shared-module precedent
  already exists in that exact dir (_solana_rpc_async, which orca imports). P3 non-blocking DRY consolidation: both
  handlers pass QG and are tested — this is a cleanup so the next Solana handler reuses one tested copy of the curve
  math instead of rolling a 3rd.
status: open
nature: issue
asset_group: [defi]
stage: [meta]
repos: [unified-trading-pm, market-tick-data-service]
scope: [engineer]
tags: [dry, refactor, solana, base58, ed25519, pda, mtds, handlers, cleanup]
related: [/plans/active/defi_consolidated_closeout_2026_07_18.md]
created: 2026-07-28
last_updated: 2026-07-28
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.12
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: >-
  REVIEW-craft finding 2026-07-28 (msg 2486, non-blocking P3) after slot-3 shipped defi_satellite_ao_dispatch_batch1-007
  (mtds@f771e841). Reviewer flagged the duplication and asked main to file as a tracked todo. Both handlers pass QG +
  are tested; not a redo-shipped-work ask.
---

## Finding

Two sibling handlers in `market_tick_data_service/cli/handlers/` each carry Solana address-encoding logic:

- `raydium_classic_amm_handler.py` — own `_BASE58_ALPHABET` + `_base58_encode`.
- `orca_whirlpool_state_handler.py` (added by `defi_satellite_ao_dispatch_batch1-007`, mtds@f771e841) — hand-rolls
  base58 encode/**decode** + ed25519 on-curve check + `find_program_address` (PDA) derivation locally.

So base58 is duplicated across both, and orca's ed25519/PDA primitives have no shared home. A shared-module precedent
already exists in the same dir (`_solana_rpc_async`, which orca already imports from).

## Suggested fix (P3, non-blocking)

Extract the Solana address primitives — base58 codec, ed25519 on-curve, `find_program_address` — into a shared
`_solana_pda.py` (or fold into an existing `_solana_*` module) in `market_tick_data_service/cli/handlers/`, and repoint
both handlers. One tested copy of the curve math instead of N.

## Notes

- Non-blocking: both handlers are green under QG and tested; nothing to redo.
- `assigned_vm: NA` — captured/tracked, NOT auto-dispatched. Operator can flip to `planning` + `active` to dispatch this
  as a data_engineering cleanup todo if worth the slot time.

## Progress Log

- 2026-07-28: Filed by main from REVIEW-craft finding (msg 2486). Acked to reviewer; flagged to operator that it's
  tracked as NA pending a dispatch decision.
