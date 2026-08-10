---
doc_type: issue
title:
  Two issue docs' sole todos claim a "RULED 2026-08-06 (operator)" decision with leftover contradictory text and no
  corroborating Progress Log entry — verify before dispatching either
summary: >-
  Found during the round11 2026-08-09 cross-cutting RECLASSIFY sweep. Both
  `issues/strategy_config_hot_reload_doc_vs_shipped_2026_07_31.md` and
  `issues/order_state_machine_ssot_vs_uac_orderstatus_2026_07_31.md` have a sole `[CODE] P2` follow-up todo whose text
  opens with `RULED 2026-08-06 (operator), option A: ...` and a tag flip `[OPERATOR]`→`[CODE]`, but each todo's OWN
  trailing text still reads `Rule between A / B / C` (leftover from before the claimed ruling), and neither doc's
  Progress Log has ANY entry recording who ruled, when, or in what session — the same-day and later na-eligibility-audit
  passes on both docs continued describing the item as an undecided `[OPERATOR]` 3-way design call, contradicting the
  "RULED" text sitting directly above them. Both docs were authored the same day (2026-07-31, "codex freshness re-review
  shard-B") and both carry the identical malformed pattern, suggesting a single prior session half-applied a templated
  edit (flipped the tag + added the "RULED" preamble) without completing it (didn't strip the leftover "Rule between
  A/B/C" text, didn't add a Progress Log entry, and evidently never actually obtained/confirmed the ruling). Neither doc
  was reclassified or dispatched on the strength of this contradictory text in this sweep — flagging for operator
  confirmation instead.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [strategy]
repos: [unified-trading-pm, strategy-service, execution-service]
scope: [admin]
tags: [ssot-contradiction, operator-ruling, data-integrity, strategy, order-state-machine, hot-reload]
related:
  [
    /plans/active/issues/strategy_config_hot_reload_doc_vs_shipped_2026_07_31.md,
    /plans/active/issues/order_state_machine_ssot_vs_uac_orderstatus_2026_07_31.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-08-09
author: claude-agent
parent_epic: infrastructure_master
priority: P1
source: >-
  round11 cross-cutting+ui RECLASSIFY + satellite-extraction sweep 2026-08-09 — found while re-checking both docs' sole
  open todo for RECLASSIFY eligibility; the "RULED... AO-dispatchable" framing looked like a clean unblock until the
  internal contradiction (leftover "Rule between A/B/C" text + no corroborating Progress Log entry, both docs) was
  caught on a full read.
assigned_vm: NA
execution_scope: local-only
estimate_class: research
drift_direction: needs-decision
depends_on: []
locked_by:
resolved_by:
context_scope:
  [
    /plans/active/issues/strategy_config_hot_reload_doc_vs_shipped_2026_07_31.md,
    /plans/active/issues/order_state_machine_ssot_vs_uac_orderstatus_2026_07_31.md,
  ]
---

# Two "RULED 2026-08-06" claims with no corroborating evidence

## What I found

Both docs' sole actionable todo:

| Doc                                                         | Todo text (verbatim opening)                                             | Contradiction                                                                                                                                                                                                                                                                         |
| ----------------------------------------------------------- | ------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `strategy_config_hot_reload_doc_vs_shipped_2026_07_31.md`   | "RULED 2026-08-06 (operator), option A: implement the documented guard." | Same todo closes: "Rule between A / B / C — specifically, confirm whether a live instrument-universe swap is position-state-safe." Doc's own 2026-08-06 na-eligibility-audit entry: "sole remaining todo is an `[OPERATOR]` 3-way design call on live-trading position-state safety." |
| `order_state_machine_ssot_vs_uac_orderstatus_2026_07_31.md` | "RULED 2026-08-06 (operator), option A: advance the contract."           | Same todo closes: "Rule between A / B / C above for the order-lifecycle enum." Doc's own 2026-08-06 na-eligibility-audit entry: "item 1 is an undecided..."                                                                                                                           |

Neither doc's Progress Log has an entry recording the actual ruling — no date, no session, no operator quote, nothing
resembling the sourced-ruling citations this corpus normally carries (compare e.g.
`content_derived_backlog_task_ids_2026_08_08.md`'s "Operator ruling 2026-08-08 (interactive session): 'b please'" — a
real quoted ruling). Both docs were authored the same day (2026-07-31, "codex freshness re-review shard-B") and carry
the identical malformed shape: tag flipped `[OPERATOR]`→`[CODE]`, "RULED... AO-dispatchable" preamble added, but the
pre-ruling "Rule between A/B/C" sentence never removed and no Progress Log entry ever added.

## Why it matters

Both underlying decisions are genuinely consequential — one gates whether a live-trading strategy-config hot-reload
guard gets built (a safety-net implementation choice), the other gates a breaking, fleet-wide UAC `OrderStatus` rename
(execution-critical). A worker reading either todo's opening sentence in isolation could reasonably dispatch real
implementation work on the strength of a ruling that may never have actually happened — or may have happened but was
never properly recorded, which is nearly as bad (no auditable provenance).

## Recommended decision

- **A** — Operator confirms the 2026-08-06 ruling was real (option A on both) — then both docs get a proper Progress Log
  entry citing the actual ruling context, the "Rule between A/B/C" leftover text is stripped, and both become clean
  RECLASSIFY candidates for a future sweep.
- **B** — Operator says no such ruling was made — then both todos revert the tag `[CODE]`→`[OPERATOR]` and the "RULED"
  preamble is removed as a hallucinated/erroneous edit, restoring both to genuinely-undecided `[OPERATOR]` status.
- **C** — Investigate further (check chat/session history from 2026-08-06 for the actual ruling session) before either A
  or B.

## Follow-ups

- [ ] [OPERATOR] P1. Confirm whether the 2026-08-06 "RULED... option A" claim on either or both docs is real, per the
      decision above. Provenance: this doc.
- [ ] [DOC] P2. Once ruled, fix both docs' todo text (strip the contradictory leftover sentence, add a proper Progress
      Log citation) in the same commit as whichever direction is confirmed. Repo: unified-trading-pm.

## Progress Log

- **2026-08-09**: Filed during the round11 cross-cutting RECLASSIFY sweep. Neither underlying doc was reclassified or
  dispatched on the strength of the contradictory "RULED" text — both stay `assigned_vm: NA`, flagged here instead.
