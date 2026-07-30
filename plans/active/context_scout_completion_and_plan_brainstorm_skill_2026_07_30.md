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
asset_group: [ao, cross-cutting]
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
    cursor-configs/skills/context-scout/SKILL.md,
    agents/context_scout_auditor.md,
    plans/active/task_template.md,
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
(`codex/11-project-management/doc-frontmatter-schema.md`) never documented it — exactly the "schema<->generator drift"
class `/docs-reconcile` exists to catch, fixed here since it's directly adjacent to this doc's own subject matter.

The other two ideas evaluated (Paperclip, Pi) turned out to be mostly redundant with what this workspace's fleet already
does (role-based dispatch + backlog + Slack alerting + self-healing ≈ Paperclip's org-chart/heartbeats; the
domain-conditional CLAUDE.md index ≈ Pi's path-scoped rules) — not pursued further here. Superpowers' brainstorming
skill mapped to a genuine but lower-priority gap (a pre-authoring clarifying-questions step; the audit net already
catches an underscoped todo post-hoc) — captured as `/plan-brainstorm` below.

A separate, higher-stakes idea (Paperclip-style hard per-agent spend caps + a possible OmniRoute multi-provider
LLM-gateway pilot) is intentionally NOT in this plan — it's a genuine judgment/security call, not bounded execution
work, so it's its own design-only LOCAL plan: `/plans/active/omniroute_llm_gateway_pilot_design_2026_07_30.md`.

## What shipped

- [x] ✅ **Wrote `scripts/plan-hygiene/generate_context_scope_inventory.py`** — the `/context-scout` skill's Phase-0
      inventory tool, reusing `scripts/docs/docspec.py`'s PyYAML frontmatter parser (same pattern as
      `generate_na_doc_tranche_inventory.py`, not a re-derived line-grep). Verdicts every in-scope plan/issue doc
      `NEVER_SCOUTED` / `STALE` / `UP_TO_DATE` via a dated `context-scout YYYY-MM-DD` Progress Log marker vs. the doc's
      last-touched date. Ran it live against this checkout: 559 in-scope docs, 553 `NEVER_SCOUTED`, 6 `STALE`, 0
      `UP_TO_DATE` (expected — the field is brand new, nothing has ever been scouted). Evidence:
      unified-trading-pm@`<pending-commit>`.
- [x] ✅ **Wrote `cursor-configs/skills/context-scout/SKILL.md`** — the full Phase 0-3 procedure (MVI
      minimal-reading-list principle, 2-6 entries/doc target, confirmed-real-path-only discipline, Workflow fan-out for
      the corpus-scale backfill, incremental daily mode after that). Evidence: unified-trading-pm@`<pending-commit>`.
- [x] ✅ **Wrote `agents/context_scout_auditor.md`** — the scheduled-dispatch boot/completion wrapper role file,
      mirroring `na_eligibility_auditor.md`/`docs_reconciler.md`'s shape (thin wrapper, one- shot lifecycle contract,
      sonnet/max/thinking-on per `plan_health.py`'s existing smart-tier forcing for this mode). This is the file whose
      absence was causing the daily timer to hard-fail. Evidence: unified-trading-pm@`<pending-commit>`.
- [x] ✅ **Fixed the doc-frontmatter-schema.md ↔ docspec.py drift** — added `context_scope` to both the `plan` and
      `issue` rows of §3's per-doc-type table, plus a Notes bullet explaining the field (mirroring the existing
      `assigned_role` note's shape/detail level). Evidence: unified-trading-pm@`<pending-commit>`.
- [x] ✅ **Wrote `cursor-configs/skills/plan-brainstorm/SKILL.md`** — the pre-authoring clarifying-questions gate:
      restate the goal, grep-first (reusing the pre-task-plan-conflict-check discipline) before asking anything, 1-2
      pointed questions max, classify the resolved scope against `task_template.md`'s dispatch-scope-eligibility bar,
      then run the existing "AO plan or human plan?" hard-rule question. Explicitly scoped as a complement to
      `/plan-reconcile`/`/na-eligibility-audit`'s post-hoc catch, not a replacement. Evidence:
      unified-trading-pm@`<pending-commit>`.
- [ ] [INFRA] P2. Add `agent-orchestrator` test coverage for `mode="context_scout"` in `plan_health.dispatch()`,
      mirroring the dedicated test commit `na_eligibility` got
      (`a935dcd test(plan-health): add na_eligibility mode dispatch coverage`) — assert the mode routes to
      `context_scout_auditor`, forces the same smart-tier (sonnet/max/thinking-on) as its siblings, and is exempt from
      the report-mode dispatch gate. Done-when: new test(s) pass under `bash scripts/quality-gates.sh` in
      `agent-orchestrator`.
- [ ] [INFRA] P2. Run `bash scripts/quality-gates.sh` in both `unified-trading-pm` and `agent-orchestrator` on the
      touched files (`--no-fix`, own named files) and fix anything red before committing. Done-when: both gates green.
- [ ] [INFRA] P2. Ship via `quickmerge.sh --agent --files '<paths>'` in each touched repo, then flip every `[x]` todo
      above from `<pending-commit>` to the real `<repo>@<sha>`, per the commit-push-flip HARD RULE.
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
      final hardening commit.

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

## Codex SSOTs

- `/codex/11-project-management/doc-frontmatter-schema.md` — the field this plan added `context_scope` documentation to
- `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "Dispatch-scope eligibility" — the bar
  `/plan-brainstorm` classifies resolved scope against
- `plans/active/task_template.md` — LOCAL vs AO-dispatched track, finding S (the specific failure mode
  `/plan-brainstorm` is meant to reduce upstream of)
