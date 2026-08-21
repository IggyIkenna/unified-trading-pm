---
doc_type: plan
title: ao satellite — parser inline-comment hardening extraction (batch 4)
summary: >-
  Two-todo extraction from /ag-closeout-audit's 2026-08-21 ao-tranche Phase 3 pass, sourced from
  backlog_500_malformed_depends_on_comment_2026_08_19.md's remaining open todos 4-5 (that doc's own orphan-table
  taxonomy already flagged these "2 bounded P3 fixes — good batch candidate"). Both harden the plan-frontmatter
  parser class against the SAME inline-`#`-comment-on-a-machine-parsed-field bug that 500'd `GET /api/backlog`
  fleet-wide on 2026-08-19 (already fixed for that one incident + a 41-doc corpus sweep) — this batch is the
  durable, forward-looking hardening the source doc's own todo 3 explicitly called for, not yet built.
status: draft
nature: process
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer]
tags: [ao, ao-dispatch, satellite, batch-4, ag-closeout-audit, parser-hardening, plan-format]
related:
  [
    /plans/active/issues/backlog_500_malformed_depends_on_comment_2026_08_19.md,
    /plans/active/ao_consolidated_closeout_2026_08_12.md,
    /plans/active/issues/ag_closeout_audit_ao_parked_2026_08_21.md,
  ]
created: "2026-08-21"
last_updated: "2026-08-21"
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.48
assigned_role: infra
effort: low
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /plans/active/issues/backlog_500_malformed_depends_on_comment_2026_08_19.md,
    agent-orchestrator/server/regen_backlog_from_plan.py,
    scripts/plan-hygiene/,
    /codex/11-project-management/cross-reference-path-convention.md,
  ]
source:
  [
    "ag-closeout-audit ao tranche, 2026-08-21 Phase 3 — extracted verbatim from
    backlog_500_malformed_depends_on_comment_2026_08_19.md's open todos 4 and 5.",
  ]
---

# ao satellite — parser inline-comment hardening (batch 4)

> **Fresh carve-out, two-todo, no finalize twin** (small-batch, no-finalize-twin precedent already established by
> infra batch1/batch4/batch5/batch19/batch20/CI batch16 — both items are conflict-clear and independently
> dispatchable, no cross-item dependency). `status: draft` / `assigned_vm: NA` pending operator review before
> dispatch, per this workspace's plan-destination rule.

## Todo 1 — strip inline comments in `_parse_frontmatter_assigned_vm`

- [ ] [BACKEND] P3. **Harden `_parse_frontmatter_assigned_vm`** (`agent-orchestrator/server/regen_backlog_from_plan.py`)
      to strip inline `# ...` comments, aligning it with `status`/`execution_scope`/`sequential`/`effort`, which all
      already `.split("#")[0]` — extracted verbatim from `backlog_500_malformed_depends_on_comment_2026_08_19.md`
      todo 4. The source doc's own todo-3 sweep (shipped `unified-trading-pm@ca6160aa10`) found 8 live issue docs
      carrying `assigned_vm: planning # reclassified NA -> planning ...` (added by the 2026-08-19
      na-eligibility-audit's own annotation convention), which makes `_resolve_plan_vms()` return a garbage VM id
      and silently drops the doc out of the ingestible set — starving any NEW todo added to it, with zero error
      surfaced. The 8 docs found at the time were already fixed by moving the comment off the field line; this todo
      is the parser-level fix so the SAME authoring pattern (which is still natural/common, since it's how a human
      or agent explains a reclassification inline) cannot silently reproduce the bug going forward. Done-when: a
      synthetic `assigned_vm: planning # test comment` frontmatter line parses to `planning`, not a garbage/None
      value, verified via a regression test; `quality-gates.sh`-green, shipped via `quickmerge.sh --agent --files`.
      Repo: agent-orchestrator.
      **Conflict-check (this pass, 2026-08-21)**: grepped `plans/active/*.md` + `plans/active/issues/*.md` for
      `_parse_frontmatter_assigned_vm` — only the source doc's own text and this batch reference it; no other
      active plan claims this fix.

## Todo 2 — plan-hygiene ratchet check for inline comments on machine-parsed fields

- [ ] [BACKEND] P3. **Add a plan-hygiene ratchet check** (new script under `scripts/plan-hygiene/` in
      unified-trading-pm) rejecting inline ` # ` comments on machine-parsed frontmatter field lines
      (`depends_on`/`parent_epic`/`supersedes`/`superseded_by`/`entry_point_for`/`assigned_vm`/`status`/
      `execution_scope`/`sequential`/`model_tier`/`effort`/`assigned_role`/`gate_on_depends`) — extracted verbatim
      from `backlog_500_malformed_depends_on_comment_2026_08_19.md` todo 5. Mirror the shrinking-ratchet baseline
      pattern already used by `reference_paths_baseline.yaml` / `line_caps_baseline.yaml`: seed the baseline from
      today's corpus (the source doc's own todo-3 sweep found the live corpus already clean post-fix — verify fresh
      at pickup, since the corpus moves daily) so the check tolerates zero currently-known instances and any future
      one is a hard failure, not a silent parser landmine. Wire into `check_plan_frontmatter`'s existing sweep family
      (or a new standalone script following the same CLI convention) so it runs in the routine hygiene sweep
      (`run_hygiene_sweep.sh`) and in prek `--precommit`. Done-when: a synthetic plan doc with an inline comment on
      one of the listed fields fails the check; a fresh full-corpus run against the live corpus passes clean (0
      violations); `quality-gates.sh`-green, shipped via `quickmerge.sh --agent --files`. Repo: unified-trading-pm.
      **Conflict-check (this pass, 2026-08-21)**: grepped `plans/active/*.md` + `plans/active/issues/*.md` for
      "inline comment" + "machine-parsed" — no other active plan claims this specific ratchet-check build; first
      dispatch of this item.

## Progress Log

- **ag-closeout-audit 2026-08-21 (ao tranche, Phase 3)**: drafted. Both todos extracted from
  `backlog_500_malformed_depends_on_comment_2026_08_19.md`'s own todos 4-5, which that doc's todos 1-3 (all done,
  shipped) already set up the evidence for. Re-verified fresh this pass (not just trusting the parked doc's
  "good batch candidate" label): both items remain genuinely bounded — concrete files, concrete done-when bars, no
  open design fork. Source doc's own todos 4-5 annotated `➡️ EXTRACTED` in the same pass.
