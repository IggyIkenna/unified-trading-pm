---
doc_type: plan
title:
  "Finalize — plan-corpus hygiene AO batch 1 (2026-08-10) — verify every retag landed, re-measure the parked corpus, and
  archive the batch"
summary: >-
  Gated companion to `meta_plan_corpus_hygiene_ao_dispatch_batch1_2026_08_10.md`, per `task_template.md`'s
  finalize-plan-coverage rule (every `assigned_vm: planning` doc needs a companion gated finalize plan;
  `check_finalize_plan_coverage.py`). Held by `depends_on` + `gate_on_depends: true` until every batch-1 todo lands. Its
  job is to prove the batch actually changed the corpus rather than just recording intent: re-run the machine checks,
  assert no `cross-cutting` dual-tag survives among the named targets, re-measure the parked-doc open count against the
  pre-batch baseline of 62, and confirm the SKILL.md rules that close the recurrence are live in the scheduled runs'
  behavior (the next daily `/ag-closeout-audit` must fix mechanical hygiene in-run, not park it).
status: active
nature: process
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [meta, ao-dispatch, plan-hygiene, ag-closeout-audit, finalize, batch-1]
related:
  [
    /plans/active/meta_plan_corpus_hygiene_ao_dispatch_batch1_2026_08_10.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /plans/active/task_template.md,
  ]
created: "2026-08-10"
last_updated: "2026-08-10"
parent_epic: agent_operating_framework_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.12
assigned_role: infra
effort: medium
drift_direction: none
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [meta_plan_corpus_hygiene_ao_dispatch_batch1_2026_08_10]
gate_on_depends: true
context_scope:
  [
    /plans/active/meta_plan_corpus_hygiene_ao_dispatch_batch1_2026_08_10.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /scripts/docs/docspec.py,
  ]
source: >-
  Authored alongside `meta_plan_corpus_hygiene_ao_dispatch_batch1_2026_08_10.md` on 2026-08-10, per the
  finalize-plan-coverage rule. Gated — does not dispatch until batch 1 completes.
---

# Finalize — plan-corpus hygiene AO batch 1

Gated behind `meta_plan_corpus_hygiene_ao_dispatch_batch1_2026_08_10.md`. Do not start until every todo there is `[x]`
or explicitly re-parked with a stated reason.

## Todos

- [ ] [DOCS] P3. **Verify every retag actually landed and is legal.** Re-read the `asset_group` of all 24 named retag
      targets across batch-1 todos 1-7 and assert: each is a single value from the `docspec.py` `ASSET_GROUP` enum, no
      `cross-cutting` survives on any of them, and no dual-tag remains. **Done when**: a per-doc before/after table is
      in this plan's Progress Log, with any target that was skipped (locked, archived mid-flight) named and explained.
- [ ] [DOCS] P3. **Re-measure the parked corpus against the pre-batch baseline.** Baseline as of 2026-08-10: 28
      `ag_closeout_audit_*_parked_*.md` docs, 62 open todos, of which ~22 mechanical / 18 `[OPERATOR]` / 5 tombstones /
      ~12 judgment calls, plus 12 duplicate copies across 4 distinct findings. **Done when**: the same counts are
      recomputed and reported, the duplicate count is 0, the tombstone count is 0, and any INCREASE over baseline is
      explained (a new audit run legitimately adding findings is fine; the same finding re-parked is not).
- [ ] [DOCS] P3. **Confirm the SKILL.md recurrence fix is live in observed behavior, not just in the doc.** Read the
      most recent daily `/ag-closeout-audit` parked doc written AFTER `unified-trading-pm@bd812c57ad` and assert: (a)
      any mechanical corpus-hygiene finding it made was fixed in-run and recorded under "Resolved this run", not parked
      as a `[DOCS]` todo; (b) it contains no actor-less "No action needed" `- [ ]` line; (c) no finding it carries also
      appears as an open todo in an older parked doc. **Done when**: all three assertions are checked against a real
      post-fix run and any failure is filed as a follow-up todo against the skill.
- [ ] [DOCS] P3. **Run the machine gates and archive the pair.** `check_frontmatter_schema.py`, `check_todo_format.sh`,
      `check_line_caps.sh`, `check_reference_paths.py`, `check_finalize_plan_coverage.py`, then
      `regenerate_active_plan_inventory.py` (orphan count must be 0). Archive both batch-1 and this finalize doc via the
      6-step ritual once green. **Done when**: gates green, both docs archived with banners, every corpus referrer
      repointed.

## Codex SSOTs

- `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` — the 6-step archival ritual
- `/codex/11-project-management/doc-frontmatter-schema.md` + `/scripts/docs/docspec.py` — `asset_group` enum
- `/codex/11-project-management/cross-reference-path-convention.md` — leading-slash refs

## Progress Log

- **2026-08-10** — Authored alongside batch 1. Gated via `depends_on` + `gate_on_depends: true`; will not dispatch until
  batch 1's todos land.
