---
doc_type: issue
title: Wave 1 quality audit — slots 2-9 execution review vs work-split done-defs
summary:
status: resolved
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service, execution-service, instruments-service]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-13
author: harsh-main (slot 1)
resolved: 2026-05-17
resolution: AUDIT-COMPLETE — 19 findings cataloged. P0
source:
  [
    work_split_2026_05_13_harsh.md (Wave 1 layout),
    "harsh_orchestrator/pings/slot_{2..9}.md",
    LDR commit log 2026-05-12 → 2026-05-13,
  ]
severity: P0 (gap findings) + retrospective (process)
locked_by: live-defi-rollout
locked_since: 2026-05-13
routing:
  {
    primary_owner: harsh-main (issue author; Harsh-side Wave 1 retrospective),
    routed_2026_05_13: 18 findings already self-routed within issue body § "Files for follow-up",
    ikenna_side_action: NONE — Harsh-side internal audit; Ikenna-main acked via PM coordination ledger 2026-05-13,
  }
---

> **🟢 ROUTING ACK (Ikenna-main, 2026-05-13)** — This Harsh-side internal Wave 1 retrospective lists 18 findings
> self-routed to 5 plans (slot 9 strategy-paper VM re-open, sports classifier extension re-open, slot 4 SHA refresh,
> CLAUDE.md multi-stage VM rule, PLAN_FORMAT.md Full-Execution Criterion tightening). Harsh-main owns triage.
> Ikenna-main acked + cross-referenced; no Ikenna-side action required beyond awareness of the slot 9 strategy-paper-VM
> gap on the master plan Group F item 18.

## What I found

Operator-requested audit of Wave 1 slot work (2026-05-13 Harsh side, 8 implementor slots: 2-9). For each slot, compared
the work-split done-definition + plan-of-record scope against actual LDR commits + plan-flip annotations + real-infra
evidence. Three sub-agents ran the per-slot audits in parallel; this doc synthesizes findings.

## Per-slot summary

| Slot | Model      | Verdict         | Top findings                                                                                                                                                                                         |
| ---- | ---------- | --------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 2    | Opus 4.7   | 🟡 1 P1 + 1 P2  | Phase 3.5 sports deferral missing named successor plan                                                                                                                                               |
| 3    | Sonnet 4.6 | ✅ + 1 deferral | AWS bucket deferred to Phase 2.6 (operational — no aws CLI on host)                                                                                                                                  |
| 4    | Sonnet 4.6 | 🟡 2 P2         | Plan SHA refs stale (`c5dd45eb` instead of LDR-canonical `38b3e8a5` post foot-gun #5 rescue)                                                                                                         |
| 5    | Sonnet 4.6 | ✅ + 1 P3       | Checkbox-hygiene minor (deferred items left `[ ]` instead of `[x] [BLOCKED — ...]`)                                                                                                                  |
| 6    | Sonnet 4.6 | 🟡 1 P1 + 2 P2  | Process: apply-flips launched 54 min AFTER Ikenna's hold direction (not relayed to slot via cross-side ping)                                                                                         |
| 7    | Sonnet 4.6 | 🟡 2 P2         | Work-split numeric drift (top-table "12 AlertCodes + 4 Breakers" vs body "8 + 4" vs shipped "8 + 2 + 2 seeds")                                                                                       |
| 8    | Sonnet 4.6 | 🟡 1 P1 + 3 P2  | Sub-agent B incomplete grep — `asset_group == "cefi"` literal still in 3 trace scripts                                                                                                               |
| 9    | Sonnet 4.6 | 🔴 SIGNIFICANT  | Task 3 strategy-paper VM **never actually launched** (claimed DONE but no event-stream evidence) + sports classifier scope **never shipped** (claimed "already done" via grep-then-conclude failure) |

**Aggregate**: 18 findings across 8 slots. Distribution by root cause:

| Root cause        | Count | Notes                                                                            |
| ----------------- | ----- | -------------------------------------------------------------------------------- |
| PLAN gap          | 5     | Under-specified done-defs, numeric drift, missing successor pointers             |
| PROCESS gap       | 5     | No rule for X (e.g., cross-side relay between multi-stage VM ops), foot-gun #5   |
| MODEL gap         | 3     | "Grep-then-conclude" failures on multi-callsite refactors (slots 7, 8, 9)        |
| DOC gap           | 1     | Slot 9 mis-stated existing sports classifier state without reading function body |
| N/A (operational) | 4     | AWS CLI absent, real-infra deferrals correctly annotated                         |

## Critical follow-ups (P0 — plan updates needed BEFORE next-cycle planning)

### 1. Slot 9 Task 3 — strategy-paper VM **never actually launched** (FULL-EXECUTION GAP)

**Evidence**: `gsutil ls gs://central-element-323112-events/events/strategy_paper/2026-05-13/` → no objects exist.
`gcloud compute instances list ... strategy-paper` → empty. Slot shipped code wire-ins (colocated_engine events + VM
self-delete) but did NOT relaunch the smoke VM. The plan-flip "Task 3 DONE" at PM@`0765d3aa` is therefore false for the
operational-verification half.

**Plan update** (apply now):

- `work_split_2026_05_13_harsh.md:290-294` — slot 9 Task 3 needs **Full-execution criterion** block per HARD RULE: must
  name the exact command
  (`bash deployment-service/scripts/vm/setup-data-pipeline-vm.sh ... strategy-paper-carry-staked-basis-20260513-AM`) +
  verification probe (`gsutil ls gs://central-element-323112-events/events/strategy_paper/2026-05-13/{correlation_id}/`
  returns ≥1 STARTED + ≥1 STOPPED jsonl).
- `promote_workflow_may23_cli_path_2026_05_10.md` — re-open the strategy-paper smoke VM verification checkbox; slot 9's
  wire-ins are shipped but operational gate not met.
- Re-open this work in the Wave 2 reserve list as P0.

### 2. Slot 9 sports classifier scope — **never shipped** despite slot claim (DOC/MODEL GAP)

**Evidence**: `unified_trading_library/legacy_reason_classifier.py:191` `_classify_sports` returns only
`EXPECTED_PRE_SOURCE_COVERAGE_START` / `SOURCE_RETURNED_ZERO`, NOT the 4 sports-specific reasons the work-split required
(`EXPECTED_PAUSED_LEAGUE` / `EXPECTED_PRE_SEASON` / `EXPECTED_POST_SEASON` / `EXPECTED_SOURCE_DOES_NOT_COVER_LEAGUE`).
Slot 9's first ping said "Sports classifier already fully shipped w/ tests" — but this was a grep-then-conclude miss
(slot didn't read the function body). Work-split:277-281 explicitly named the 4 reasons.

**Plan update** (apply now):

- `code_freeze_migrate_backfill_sequencing_2026_05_10.md` — re-open sports classifier extension as a fresh P1 todo with
  the 4 specific reason kinds named + lookup pointer to instruments-service sports SSOT (league calendars +
  source-coverage windows).
- Add to Wave 2 reserve list.

### 3. Slot 4 SHA references stale post foot-gun #5 rescue (CONTRACT GAP — small but factual)

**Evidence**: `defi_simulation_realism_2026_05_10.md:624, 628, 631, 634, 942-943` still cite `c5dd45eb` (the original
tab/hk/4 commit). The LDR-canonical SHA after main's cherry-pick rescue is `execution-service@38b3e8a5`. Same content,
different SHA; plan-of-record should reference the LDR-visible commit.

**Plan update** (apply now): bulk-replace `c5dd45eb` → `38b3e8a5` in `defi_simulation_realism_2026_05_10.md`.

## P1 / P2 follow-ups (capture but don't pre-empt Wave 2 work)

| #   | Slot | Finding                                                                                                                 | Plan update                                                                                         | Wave-2 absorbable?        |
| --- | ---- | ----------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- | ------------------------- |
| P1  | 2    | Phase 3.5 sports deferral lacks named successor plan                                                                    | File new issue doc OR add `Successor:` line to scoreboard                                           | Yes — small annotation    |
| P1  | 6    | apply-flips ran 54 min after Ikenna's hold direction; no cross-side re-poll between multi-stage VM ops                  | Add CLAUDE.md clause: "Multi-stage VM ops MUST re-poll cross-side `_agent_pings.md` between stages" | Yes — codify rule         |
| P1  | 8    | `perp_hedge_candidate_venues("arbitrage_price_dispersion")` returns `frozenset()` — work-split required both archetypes | Amend work-split § Slot 8 sub-agent B done-def + ship the missing per-slot enumerator wire-in       | Yes — small refactor      |
| P2  | 4    | Ping miscount "9 fixtures" vs actual 4 new (7 total)                                                                    | None — ping-ledger sloppiness, plan body correct                                                    | No-op                     |
| P2  | 5    | Foreign-blocker checkboxes left `[ ]` should be `[x] [BLOCKED — ...]`                                                   | Small status-string fix                                                                             | Yes                       |
| P2  | 6    | Sports/prediction apply-flips deferred without named successor                                                          | Add successor pointer                                                                               | Yes                       |
| P2  | 7    | Work-split numeric drift: "12 AlertCodes + 4 Breakers" top-table vs 8+2 shipped                                         | Fix top-table count to match body                                                                   | Yes — small edit          |
| P2  | 8    | 3 trace scripts still have `asset_group == "cefi"` literal                                                              | File P2 follow-up; trace scripts are ops-debug                                                      | Yes — small grep+refactor |
| P2  | 8    | `VENUE_DATA_TYPE_CAPABILITIES` `__all__` export missing                                                                 | Ask C of operator triage; small additive fix awaiting greenlight                                    | Operator decision         |

## Root-cause analysis: was it plans, docs, or model tier?

**Plans (5 findings)**: Under-specified done-defs (slot 8 "both archetypes" without saying how), numeric drift in
work-split top-table vs body (slot 7), missing successor pointers in scoreboards (slots 2, 5, 6). These are
**plan-writing discipline** issues — fixed by tightening the work-split format + applying the existing HARD RULES
(Capture Discoveries / Temporary states have named successor / Full-Execution Criterion). Slot 1 main owns this; the
work-split-format SSOT is `plans/PLAN_FORMAT.md`.

**Process (5 findings)**: Foot-gun #5 (slot 4 — codified today PM@`f49d5f7d`); cross-side hold relay not enforced (slot
6); plan SHA refs stale post-rescue (slot 4); checkbox-hygiene drift (slot 5). These are **operational rules** that the
docs didn't surface clearly enough. Three of the five are now codified (LDR-alignment HARD RULE + workspace-drift
recognition); the rest are smaller follow-ups.

**Model (3 findings, ALL Sonnet 4.6)**: "Grep-then-conclude" failures across slots 7, 8, 9. All three slots had
multi-callsite refactor scope and Sonnet 4.6 / high stopped at first-grep instead of reading the function body. This is
EXACTLY the failure mode CLAUDE.md "Grep-Then-Read, Not Grep-Then-Conclude" HARD RULE (codified 2026-05-10 after a
9-agent audit) addresses — but the rule isn't reliably internalised by Sonnet 4.6.

**Docs (1 finding)**: Slot 9 mis-stated existing sports classifier state — that's the grep-then-conclude mode, not a
doc-quality issue per se. The plan was correct; the slot's reading was incomplete.

## Model tier recommendations

Based on today's data, here's a working theory of when to escalate from Sonnet 4.6 / high → Opus 4.7 / high (or
extra-high):

### Sonnet 4.6 / high is SUFFICIENT for:

- ✅ **Mechanical implementation-from-spec** (slot 3: bash provisioning script; slot 4: harness scripts with Protocol
  DI; slot 5: refactor with crisp 5-file scope; slot 7: enum + dict + test additions)
- ✅ **Domain-clear refactors** where every callsite is named in the spec or there's only one callsite type
- ✅ **Issue diagnosis + filing** (slot 6's classifier-bug detection was textbook; slot 8's collision response was
  procedurally exemplary)

### Sonnet 4.6 / high STRUGGLES with (consider Opus 4.7 / high):

- ⚠️ **Multi-callsite grep refactors** — when "grep for X across the repo, refactor each" hits 3+ distinct callsite
  shapes (slot 7: 4 places, slot 8: 4 places, slot 9 sports classifier: function body read needed). Today's data: 3 of 3
  such slots had grep-then-conclude failures.
- ⚠️ **Multi-stream slots with real-infra ops** — slot 9 had 3 streams (UTL classifier / 6-family PIT / strategy-paper
  VM); ship the easy 2, paper-flip the hard one. Real-infra ops need their own slot or escalated model.
- ⚠️ **Cross-module architectural classification** — slot 2 (Opus) correctly identified "Phase 3.5 sports is upstream
  MDPS problem" after reading 4-5 modules deeply. Sonnet at the same scope would likely have shipped a wrong Option A
  wire-in for sports.

### Opus 4.7 / high → use for:

- 🟢 **Critical-path work with cross-module architectural calls** (slot 2 today, propagation chain)
- 🟢 **Multi-stream slots that bundle 3+ scopes** (would have helped slot 9)
- 🟢 **Real-infra operational verification** (VM launches with event-stream watching — "Plans Run To Actual Completion"
  HARD RULE)
- 🟢 **Cross-cutting refactors with 5+ callsite types** (e.g., `to_canonical_venue()` helper proposed in reserve list)

### Opus 4.7 / extra-high or thinking: max → use for:

- 🔴 **First-time cross-asset-group design decisions** (e.g., the GMX/DRIFT classification call, which was made by
  operator+Ikenna directly)
- 🔴 **System-architecture writes (CLAUDE.md, codex SSOTs)** — drift in workspace contracts has high downstream cost
- 🔴 **Pre-cutover gate validation** (final May-23 readiness audits)

## What to fix vs. carry forward

**Apply NOW (before Wave 2 spawn)** — see "Critical follow-ups" section above:

1. Re-open slot 9 Task 3 (strategy-paper VM never ran)
2. Re-open slot 9 sports classifier scope (never shipped)
3. Update slot 4 SHA references in plan body

**Carry into Wave 2** (small absorbable items, ~30-60 min each):

- P1 + P2 items in the table above
- Codify "Multi-stage VM ops cross-side re-poll" rule (slot 6 finding)

**Defer to Day-5 retrospective**:

- Aggregate model-tier learnings into `/codex/06-coding-standards/model-tier-selection.md` update (currently the doc
  says "Opus only for main / cross-repo architecture / >200k context" but today's data suggests adding "multi-stream
  slots with real-infra ops" + "grep-heavy multi-callsite refactors" as Opus triggers)

## Why it matters

May-23 cutover is 10 days out. Slot 9's Task 3 paper-flip is the most worrying finding: the strategy-paper smoke VM is
on the critical readiness checklist (Group F item 18 per master plan). The plan currently shows it as "DONE 2026-05-13"
— a future agent reading the master plan thinks paper-trade is validated when in fact only the code wire-ins shipped. If
operator hadn't ordered this audit, the gap would have surfaced at the May-23 dress rehearsal.

The slot 9 sports classifier miss is the second-most-worrying: next-cycle planning would have assumed the classifier
covers sports correctly, blocking real downstream consumers (sports/prediction reconciler) from working as expected.

The other 16 findings are smaller — process refinements, plan-flip annotation hygiene, small refactor follow-ups. All
absorbable within Wave 2 + Day-5.

## Recommended decision

**P0**: apply the 3 critical plan updates (slot 9 Task 3 reopen + sports classifier reopen + slot 4 SHA refresh)
immediately so Wave 2 spawn is reading accurate plan state.

**P1**: codify the "multi-stage VM ops cross-side re-poll" rule + tighten work-split Full-Execution Criterion format in
`plans/PLAN_FORMAT.md`.

**P2 (model-tier policy)**: operator decision — should we escalate Sonnet 4.6 → Opus 4.7 for multi-callsite grep
refactors + multi-stream slots? Today's data is suggestive (3 of 3 such slots had grep failures) but not conclusive —
proposes a 3-day A/B trial: next 3 multi-callsite refactors run on Opus 4.7 / high, compare grep-completeness vs Sonnet
baseline.

**Suggested owner**: slot 1 main applies the P0 plan updates this session; P1 codification owned by slot 1 main next
cycle; P2 model-tier policy is operator + Ikenna decision.

## Files for follow-up

- `plans/active/work_split_2026_05_13_harsh.md` § Slot 9 Task 3 — add Full-execution criterion
- `plans/active/promote_workflow_may23_cli_path_2026_05_10.md` — re-open strategy-paper VM checkbox
- `plans/active/code_freeze_migrate_backfill_sequencing_2026_05_10.md` — re-open sports classifier extension
- `plans/active/defi_simulation_realism_2026_05_10.md` — bulk SHA update `c5dd45eb` → `38b3e8a5`
- `cursor-configs/CLAUDE.md` (later) — add "Multi-stage VM ops cross-side re-poll" rule + tighten model-tier triggers
- `plans/PLAN_FORMAT.md` (later) — tighten Full-Execution Criterion mandatory block

---

## Triage — 2026-05-18

**Status**: CLOSED — SHIPPED **Triaged by**: slot-8 triage sweep **Reason**: Resolved 2026-05-17; 19 findings cataloged;
P0 items re-opened per findings triage
