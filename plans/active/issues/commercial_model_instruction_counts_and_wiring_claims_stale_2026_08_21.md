---
doc_type: issue
title: "Commercial-model artefacts: stale spelled-out instruction counts and overtaken wiring claims"
summary: >-
  The numeric artefact-count drift fix (13 to 16) landed, but spelled-out count words are invisible to
  check_artefact_enum_drift.py and stayed stale. Measured ground truth 2026-08-21: StrategyInstructionEnvelope
  subclass_count = 16 (checker and the StrategyInstructionV2 union agree). This pass fixed the 9 stale "thirteen"
  total-count claims across 3 artefacts; the remaining work is authoring, not word swaps — three enumerations still
  show 13 or 11 of the 16 classes, and two artefacts carry 2026-08-18-era wiring claims overtaken by
  execution-service@0aa709f076 / @b49a3f1a96 (all 16 action types now dispatch from POST /external/instructions; a
  live tick-ingestion loop is wired).
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm, unified-api-contracts, execution-service]
scope: [engineer]
tags: [commercial-model, artefacts, enum-drift, doc-drift]
related:
  [
    /plans/active/cross_cutting_satellite_ao_dispatch_batch21_2026_08_21.md,
    /plans/active/issues/execution_state_does_not_survive_restart_2026_08_20.md,
  ]
created: 2026-08-21
author: claude-code (slot-3, infra craft; review-message follow-up on the artefact count drift fix)
parent_epic: strategy_master
assigned_vm: NA
execution_scope: local-only
priority: P3
source:
  [
    "slot-3 review messages 10251/10252: spelled-out count claims the numeric checker cannot see; assess/update or record follow-up",
  ]
resolved_by:
locked_by:
locked_since:
context_scope:
  [
    codex/14-customer-journeys/commercial-model/strategy-service-walkthrough.html,
    codex/14-customer-journeys/commercial-model/strategy-service-deep-dive.html,
    codex/14-customer-journeys/commercial-model/platform-architecture.html,
    codex/14-customer-journeys/commercial-model/platform-external-api-walkthrough.html,
    unified-trading-pm/scripts/plan-hygiene/check_artefact_enum_drift.py,
  ]
drift_direction: advance-docs
depends_on: []
---

# Commercial-model artefacts: stale spelled-out instruction counts and overtaken wiring claims

## What was measured (2026-08-21, slot-3)

- `check_artefact_enum_drift.py` ground truth: `strategy_instruction_envelope` subclass_count = **16**
  (`unified-api-contracts/unified_api_contracts/internal/architecture_v2/schemas.py:299-489`), and the
  `StrategyInstructionV2` union (schemas.py:502+) lists the same 16. `strategy_family` = 9 (matches the artefacts).
- `BusTransferType` (`unified-api-contracts/.../canonical/crosscutting/transfer_events.py`) = **13 members** — so
  strategy-service-walkthrough.html's "The thirteen transfer types and the three rails" is CORRECT and was left
  untouched.
- Numeric claims in the artefacts already say 16 ("all 16", "All sixteen of sixteen", "15 of 16") — only
  SPELLED-OUT count words had stayed stale (the checker scans integers adjacent to counting words only).
- Wiring ground truth: all 16 action types dispatch from `POST /external/instructions` as of 2026-08-21 —
  `execution_service/api/external_instruction_api.py` module docstring ("``CONTROL`` was the last:
  ``_submit_control_instruction()``") and `_submit_control_instruction()` at line 328, per
  execution-service@b49a3f1a96; BRIDGE/LP_MINT/LP_BURN engines + live tick-ingestion loop per
  execution-service@0aa709f076. platform-api-reference.html §01's 2026-08-21 callout is the current account.

## Fixed in this pass (2026-08-21, slot-3) — 9 mechanical count-word edits, no authoring

Digits are used in place of spelled-out counts so the claims become checker-scannable going forward.

- strategy-service-walkthrough.html: summary "Thirteen of the 16 action types" (was "The thirteen action types");
  the 2026-08-18 verification note now states the union lists 16 and names the 3 classes not shown; the
  "wires exactly two" verification is re-dated 2026-08-18 and points to platform-api-reference.html §01 for the
  current all-16 wiring.
- strategy-service-deep-dive.html: lede + §"external-strategy integration surface" now say "the 16 instruction
  types"; the strategy_master owner-chip title drops the rotted count (its own §02 enumeration is the stale one,
  todo 1).
- platform-architecture.html: ref-block header "13 of 16 actions" (was "Thirteen actions"; the name list that
  follows has exactly 13 of 16); "envelope, 13 of 16 actions" (was "thirteen actions"); "common to every action"
  (was "common to all thirteen actions").

## Todos

- [ ] [DOCS] P3. **Extend the three instruction-type enumerations to the full 16** (add `ControlInstruction`,
      `LpMintInstruction`, `LpBurnInstruction` — plus `WithdrawInstruction`/`RepayInstruction` where the list omits
      them) with real fields, in each artefact's own voice: strategy-service-deep-dive.html §02 ("Eleven subtypes"
      keypoint at ~1253, "all eleven subtypes" summary at ~1262, and the detail block — lists 11 names),
      platform-architecture.html ref block (~5601, 13 names + per-action field lists), strategy-service-walkthrough.html
      §"action types" code block (13 classes shown).
- [ ] [DOCS] P3. **Rewrite strategy-service-walkthrough.html's "Reaching this contract over the network" passage
      against current code** — its 2026-08-18-verified claims ("wires exactly two", "nothing in execution-service
      yet drives the underlying-tick loop (`on_underlying_tick`)") are overtaken by execution-service@0aa709f076
      (BRIDGE/LP_MINT/LP_BURN engines + wired tick-ingestion loop) and @b49a3f1a96 (ControlInstruction dispatch);
      mirror platform-api-reference.html §01's 2026-08-21 verified callout.
- [ ] [DOCS] P3. **Update platform-external-api-walkthrough.html's "15 of 16" callout + §26** — ControlInstruction
      HAS dispatched from `POST /external/instructions` since 2026-08-21 (execution-service@b49a3f1a96,
      `_submit_control_instruction` at `external_instruction_api.py:328`); "has a built handler that is not yet
      dispatched from this endpoint" is stale.

## Progress Log

- **2026-08-21 — filed (slot-3).** Same pass fixed the 9 stale spelled-out count words (listed above) and measured
  all ground truths cited here (checker run, union read, BusTransferType member count, endpoint dispatch grep). No
  authoring changes made — enumeration extension and passage rewrites need the artefacts' editorial voice and are
  left as the three P3 todos.
