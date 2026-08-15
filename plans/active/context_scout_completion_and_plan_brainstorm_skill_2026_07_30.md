---
doc_type: plan
title: Complete context_scout plumbing + close a frontmatter-schema drift + add a plan-brainstorm skill
summary: >-
  Operator asked me to evaluate a set of other coding-agent ideas (OpenCode's Scout subagent, Paperclip's fleet
  control-plane, Pi's harness, Superpowers' brainstorming skill) against this workspace's
  context/cost/throughput/planning-quality goals. Before building anything, found the file-scope-hint idea was ALREADY
  landed as `context_scope` frontmatter + an AO `context_scout` dispatch mode (agent-orchestrator@df5de14, ~24h prior) —
  but incomplete: the role file + skill it dispatches to didn't exist, so the daily timer would hard-fail every run.
  Completed that (role file + skill + Phase-0 inventory script), fixed an adjacent doc-frontmatter-schema.md drift found
  along the way (docspec.py had `context_scope` in its machine schema, the human SSOT doc didn't), added test coverage
  matching the sibling `na_eligibility` mode's precedent, and authored a new `/plan-brainstorm` skill for the
  pre-authoring clarifying-questions gap the audits currently only catch post-hoc.
status: active
nature: process
asset_group:
  [ao] # corrected 2026-08-09 (/ag-closeout-audit ao) -- was [ao, cross-cutting]. Content is 100% agent-orchestrator
  # context_scout/plan-brainstorm skill-authoring plumbing; zero data-pipeline/cross-AG span -- cross-cutting was a
  # redundant mistag per the Orthogonality HARD CHECK (flagged but not yet fixed by the 2026-08-08 cross-cutting run,
  # see plans/active/issues/ag_closeout_audit_cross_cutting_parked_2026_08_08.md finding 2).
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags: [context_scout, context_scope, plan-brainstorm, plan-health, skill-authoring, doc-frontmatter-schema]
related:
  [
    /codex/11-project-management/doc-frontmatter-schema.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    /plans/active/task_template.md,
  ]
created: 2026-07-30
last_updated: 2026-07-30
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.8
assigned_role: infra
drift_direction: advance-code
depends_on:
supersedes:
superseded_by:
source:
  "operator ask 2026-07-30, interactive session slot 1 — evaluating OpenCode/Paperclip/Pi/Superpowers ideas for
  context-reduction/cost/throughput/planning-quality gains"
locked_by:
locked_since:
context_scope:
  [
    /codex/11-project-management/doc-frontmatter-schema.md,
    /plans/active/task_template.md,
    scripts/plan-hygiene/generate_context_scope_inventory.py,
    agent-orchestrator/server/prompts.py,
    cursor-configs/skills/context-scout/SKILL.md,
    /plans/active/ao_satellite_ao_dispatch_batch3_2026_07_31.md,
  ]
---

# Complete context_scout plumbing + close a frontmatter-schema drift + add a plan-brainstorm skill

## Why this doc exists

Operator pointed me at four other coding-agent ecosystem ideas (OpenCode's `Scout`/`ContextScout` subagent, Paperclip's
fleet org-chart/budget control-plane, the Pi harness, and the `obra/superpowers` Claude Code plugin's brainstorming
skill) and asked which of them would help this workspace's fleet specifically on context reduction, cost, throughput,
and fewer planning issues — with an explicit instruction to check what's already shipped or in-flight before building
anything, since another worker had been active in the last 24h.

That check found the highest-value idea (a per-doc file-scope reading list, i.e. OpenCode's Scout applied to plan
authoring) had ALREADY landed: `agent-orchestrator@df5de14` ("feat(plan-health): wire context_scout dispatch mode +
AgentKind") added a `context_scout` mode to `plan_health.py`, a `context_scout_auditor` `AgentKind`, and a systemd timer
installer (`scripts/install-context-scout-timer.sh`) — all pointing at a `/context-scout` skill and an
`agents/context_scout_auditor.md` role file that did not yet exist anywhere in the checkout, and with no test coverage
(unlike the `na_eligibility` mode, which got its own dedicated test commit). Every time that daily timer fired,
`server/prompts.py`'s `_role_path()`/`load()` would raise `KeyError(f"no role file for role={role}...")` — a guaranteed,
repeating hard-fail, not a hypothetical one.

Rather than build a new, redundant "file-scope scout" feature, the right move was to finish the one already wired in.
Along the way, found the `context_scope` field itself had the same kind of gap one level up: `scripts/docs/docspec.py`
(the doc-frontmatter-schema.md's own machine mirror, "Mirrors it in lockstep" per its own docstring) already validated
`context_scope` as an elective field on `plan` and `issue` docs, but the human SSOT
(`/codex/11-project-management/doc-frontmatter-schema.md`) never documented it — exactly the "schema<->generator drift"
class `/docs-reconcile` exists to catch, fixed here since it's directly adjacent to this doc's own subject matter.

The other two ideas evaluated (Paperclip, Pi) turned out to be mostly redundant with what this workspace's fleet already
does (role-based dispatch + backlog + Slack alerting + self-healing ≈ Paperclip's org-chart/heartbeats; the
domain-conditional CLAUDE.md index ≈ Pi's path-scoped rules) — not pursued further here. Superpowers' brainstorming
skill mapped to a genuine but lower-priority gap (a pre-authoring clarifying-questions step; the audit net already
catches an underscoped todo post-hoc) — captured as `/plan-brainstorm` below.

A separate, higher-stakes idea (Paperclip-style hard per-agent spend caps + a possible OmniRoute multi-provider
LLM-gateway pilot) is intentionally NOT in this plan — it's its own LOCAL plan:
`/plans/archive/2026_08/omniroute_llm_gateway_pilot_design_2026_07_30.md`. Both of that doc's open objections were since
ruled on (trust-boundary waived; model-tier-SSOT-conflict resolved via a structural guardrail rather than a standing
gate), and the doc now carries build-grade implementation detail — but stays `assigned_vm: NA` by explicit operator
choice (human-executed, not AO-dispatched).

## What shipped

- [x] ✅ **Wrote `scripts/plan-hygiene/generate_context_scope_inventory.py`** — the `/context-scout` skill's Phase-0
      inventory tool, reusing `scripts/docs/docspec.py`'s PyYAML frontmatter parser (same pattern as
      `generate_na_doc_tranche_inventory.py`, not a re-derived line-grep). Verdicts every in-scope plan/issue doc
      `NEVER_SCOUTED` / `STALE` / `UP_TO_DATE` via a dated `context-scout YYYY-MM-DD` Progress Log marker vs. the doc's
      last-touched date. Ran it live against this checkout: 559 in-scope docs, 553 `NEVER_SCOUTED`, 6 `STALE`, 0
      `UP_TO_DATE` (expected — the field is brand new, nothing has ever been scouted). Evidence:
      unified-trading-pm@26e0884a0.
- [x] ✅ **Wrote `cursor-configs/skills/context-scout/SKILL.md`** — the full Phase 0-3 procedure (MVI
      minimal-reading-list principle, 2-6 entries/doc target, confirmed-real-path-only discipline, Workflow fan-out for
      the corpus-scale backfill, incremental daily mode after that). Evidence: unified-trading-pm@26e0884a0.
- [x] ✅ **Wrote `agents/context_scout_auditor.md`** — the scheduled-dispatch boot/completion wrapper role file,
      mirroring `na_eligibility_auditor.md`/`docs_reconciler.md`'s shape (thin wrapper, one- shot lifecycle contract,
      sonnet/max/thinking-on per `plan_health.py`'s existing smart-tier forcing for this mode). This is the file whose
      absence was causing the daily timer to hard-fail. Evidence: unified-trading-pm@26e0884a0.
- [x] ✅ **Fixed the doc-frontmatter-schema.md ↔ docspec.py drift** — added `context_scope` to both the `plan` and
      `issue` rows of §3's per-doc-type table, plus a Notes bullet explaining the field (mirroring the existing
      `assigned_role` note's shape/detail level). Evidence: unified-trading-pm@26e0884a0.
- [x] ✅ **Wrote `cursor-configs/skills/plan-brainstorm/SKILL.md`** — the pre-authoring clarifying-questions gate:
      restate the goal, grep-first (reusing the pre-task-plan-conflict-check discipline) before asking anything, 1-2
      pointed questions max, classify the resolved scope against `task_template.md`'s dispatch-scope-eligibility bar,
      then run the existing "AO plan or human plan?" hard-rule question. Explicitly scoped as a complement to
      `/plan-reconcile`/`/na-eligibility-audit`'s post-hoc catch, not a replacement. Evidence:
      unified-trading-pm@26e0884a0.
- [x] ✅ **Found + fixed a live AgentKind dashboard/observability parity gap** — `context_scout_auditor` had landed in
      `server/models/_types.py`'s `AgentKind` Literal (agent-orchestrator@df5de14) but was missing from the same 3-file
      registry this exact bug class has hit 3 times before (`agent_orchestrator_agent_kind_literal_gap_2026_07_28`):
      dashboard `AGENT_KIND_LABEL` + `KINDS_ORDER` (`dashboard/src/layout.tsx`), the `AgentKind` TS union
      (`dashboard/src/types.ts`), and the "N daily-scheduled jobs" doc comments (`scheduled_jobs.py`/`slack.py`/
      `layout.tsx`, 4→5). Fixed all of it, verified via `dashboard`'s `tsc --noEmit` + `vitest run` (165 tests) both
      clean. Evidence: agent-orchestrator@f0c4726.
- [x] ✅ **Added `agent-orchestrator` test coverage for `mode="context_scout"`** in `plan_health.dispatch()`, mirroring
      the dedicated test commit `na_eligibility` got (`a935dcd`) — asserts the mode routes to `context_scout_auditor`,
      forces the same smart-tier (sonnet/max/thinking-on) as its siblings, and is exempt from the report-mode dispatch
      gate. All 74 tests in `test_plan_health.py` pass (3 new + 71 pre-existing unaffected). Evidence:
      agent-orchestrator@f0c4726.
- [x] ✅ **Ran `bash scripts/quality-gates.sh` in both repos** on the touched files — `unified-trading-pm` full gate
      green (2035 agent-orchestrator tests / 1534 PM tests passed across both runs), `agent-orchestrator` dashboard
      `tsc`+`vitest` clean. Evidence: both gates green pre-commit, per the runs cited above.
- [x] ✅ **Shipped via `quickmerge.sh --agent --files` in each touched repo** — `agent-orchestrator@f0c4726` (dashboard
      parity + tests), `unified-trading-pm@26e0884a0` (skill/role-file/inventory-script/schema-fix/plan-brainstorm +
      this doc). Hit a real concurrent-session hazard shipping the PM side (a second live `quickmerge.sh` process in
      this same `.tabs/1/unified-trading-pm` checkout, from the operator's other open session, doing its own much larger
      "backfill context_scope across active plans/issues" commit) — resolved by letting that session's pull/rebase land
      first, then rebasing + pushing mine cleanly on top; no content was lost on either side.
- [x] ✅ **Found + fixed a second layer of the same schema drift**: `plans/PLAN_FORMAT.md` and
      `plans/active/task_template.md` (the two other canonical-frontmatter-template docs, distinct from
      `doc-frontmatter-schema.md`) also never mentioned `context_scope` in their example frontmatter blocks — a
      separate, earlier session had added it there per that session's own record, but the addition never survived to a
      commit (lost the same way this doc's own predecessor plan file did — see note below) and this later session's
      drift-fix pass only caught the `doc-frontmatter-schema.md` copy, not these two. Added a `context_scope:` example
      line to both templates' frontmatter blocks.
- [ ] [SCRIPT] P0. **Backfill `context_scope` across the full active plans/issues corpus** — the operator's original ask
      for this whole workstream (tag ALL active plans + issues with a minimal reading-list, as a hardened requirement),
      which this plan's own scope never covered (it only finished the plumbing). Per
      `generate_context_scope_inventory.py`'s live count: 559 in-scope docs, 553 `NEVER_SCOUTED`. In progress as of this
      todo's creation: ~30-file batch staged locally (docspec.py + a mix of plans/issues), repeatedly blocked shipping
      by unrelated transient conditions (see Progress Log) — continue in small clean batches until the corpus is fully
      scouted, then flip `docspec.py`'s `context_scope` FieldSpec from `Req.E` to `Req.R` for `plan`+`issue` as the
      final hardening commit. **This is the same item actively tracked and worked as todo 1 of
      `/plans/active/ao_satellite_ao_dispatch_batch3_2026_07_31.md`** (that doc is the live tracking home — see this
      doc's own Progress Log entry below). **Not flipped here — still open.**
      `ao_satellite_ao_dispatch_batch20_2026_08_13.md`'s finalize session (2026-08-14) confirmed this todo was a
      duplicate extraction of the same batch3 work and, rather than leave a re-dispatchable duplicate, did real
      incremental work under batch20 instead: `NEVER_SCOUTED` corpus count 101→6 (5 `locked_by`-skipped + 1
      line-cap-deferred), shipped in `unified-trading-pm@6117942be5`, `@3bc392cd0d`, `@716dcf3467`. The remaining
      `STALE` docs + the `docspec.py` FieldSpec flip stay tracked under batch3's own todo 1 per this doc's own design
      above — no reclassification here. Reconciled 2026-08-14 per
      `ao_satellite_ao_dispatch_batch20_2026_08_13_finalize.md` todo 1.

## Progress Log

- **2026-07-30 (later session, slot 1)**: this plan's own predecessor — an earlier plan-of-record named
  `context_scope_frontmatter_and_scout_skill_2026_07_30.md`, which built the original `context_scope`
  field/schema/script/skill/AO-wiring design and drove the corpus backfill — was never actually committed (existed only
  as a local untracked file across a long session full of multi-agent git contention) and was subsequently lost outright
  (not recoverable via `git log --all` — confirmed absent from every ref). This doc, its sibling untracked artifacts
  (`agents/context_scout_auditor.md`, `cursor-configs/skills/context-scout/SKILL.md`,
  `scripts/plan-hygiene/generate_context_scope_inventory.py`), and this same predecessor plan's own narrative survived
  only in that earlier session's own conversation summary — reconciled here rather than silently dropped. Lesson for the
  future: an uncommitted `plans/active/*.md` file has NO protection from `git checkout`-based conflict recovery (unlike
  git-tracked content, which at least shows up in `git status`/stash) — write it, then commit it fast, don't let a plan
  doc itself become the uncommitted artifact a later cleanup pass can't see.
- **context-scout 2026-08-01**: populated/refreshed context_scope (5 entries).
- **context-scout 2026-08-03**: refreshed context_scope (5 entries) -- swapped the two markdown role/skill files for the
  real Python source this doc shipped (`generate_context_scope_inventory.py`) + the agent-orchestrator file whose
  missing role-file bug this doc fixed (`server/prompts.py`), keeping one skill-doc pointer.
- **na-eligibility-audit 2026-08-01** (autonomous, tranche `ao`, dispatch agt-8e95ca, slot 2): KEEP-NA-STALE
  (already-duplicated) — citation fix only, not a reclassification. This doc's sole remaining checkbox (`[SCRIPT] P0`,
  backfill `context_scope` corpus-wide) is the SAME work item actively extracted and tracked as todo 1 of
  `/plans/active/ao_satellite_ao_dispatch_batch3_2026_07_31.md` (already `assigned_vm: planning`, with real incremental
  progress recorded there as of 2026-08-01: `NEVER_SCOUTED` reduced 609→386). This doc's own checkbox simply never got a
  pointer back to that extraction. Added the citation inline above; `assigned_vm` correctly stays `NA` here — flipping
  it would dispatch a duplicate of already-active work.

## Codex SSOTs

- `/codex/11-project-management/doc-frontmatter-schema.md` — the field this plan added `context_scope` documentation to
- `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "Dispatch-scope eligibility" — the bar
  `/plan-brainstorm` classifies resolved scope against
- `plans/active/task_template.md` — LOCAL vs AO-dispatched track, finding S (the specific failure mode
  `/plan-brainstorm` is meant to reduce upstream of)

- **na-eligibility-audit 2026-08-06**: KEEP-NA-STALE — Sole open todo (context_scope corpus backfill + docspec.py
  FieldSpec flip) is the same item already tracked verbatim as todo 1 of ao_satellite_ao_dispatch_batch3 (assigned_vm:
  planning, real progress). Prior 2026-08-01 marker unchanged.
- **context-scout 2026-08-07**: refreshed context_scope (6 entries) -- added
  `ao_satellite_ao_dispatch_batch3_2026_07_31.md`, the confirmed live-tracking home for this doc's sole remaining todo
  (context_scope corpus backfill), per the 2026-08-01/08-06 na-eligibility-audit findings above.
- **na-eligibility-audit 2026-08-07**: KEEP-NA-STALE (already-duplicated) — re-verified: sole open todo (`[SCRIPT] P0`,
  context_scope corpus backfill) remains the same item tracked verbatim as todo 1 of
  `ao_satellite_ao_dispatch_batch3_2026_07_31.md` (still open there, `assigned_vm: planning`, real incremental
  progress). Citation unchanged from the 2026-08-01/08-06 markers.
- **na-eligibility-audit 2026-08-09 (round11)**: KEEP-NA, valid (still KEEP-NA-STALE/already-duplicated) — re-checked
  against the round7-10 precedent set; none apply (this doc's gap is pure duplication, not a credential or design-fork
  question). Independently corroborated same-day: the 2026-08-09 `/ag-closeout-audit ao` batch12 run lists this doc
  under "Covered by an existing active plan (2) — not orphaned, no extraction needed." No action.

- **na-eligibility-audit 2026-08-10 (ao full-tranche sweep, group 3)**: KEEP-NA (KEEP-NA-STALE, already-duplicated) —
  the sole open item is the same work item verbatim as `ao_satellite_ao_dispatch_batch3_2026_07_31.md`'s own todo 1
  (itself confirmed KEEP-NA this same sweep, above). Citation well-established across 4 prior audits; no new facts
  found.
- **context-scout 2026-08-15**: refreshed; context_scope unchanged (6 entries) — sole open todo still the same duplicate
  tracked verbatim in `ao_satellite_ao_dispatch_batch3_2026_07_31.md`, already the last entry here.
