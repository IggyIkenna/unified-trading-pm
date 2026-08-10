---
doc_type: plan
title: Infra satellite AO batch 14 — add a `.pre-commit-config.yaml` to `unified-trading-ci`
summary: >-
  Fourteenth AO-dispatch batch for the `infra` topic tranche, produced during a round-11 combined
  RECLASSIFY+satellite-extraction sweep (2026-08-09) over the 11-doc `infra` KEEP-NA-marker gap list. Single source:
  `shared_ci_workflow_repo_extraction_2026_08_06.md` todo 20 — a bounded, worker-determinable, `(stretch, optional)` P3
  hygiene task (add a `prek` pre-commit hook to `unified-trading-ci`, which today only has the pre-push
  strict-quickmerge hook installed at slot-provisioning time). That source doc's OTHER remaining open item, todo 3 (add
  `image-build-gate.yml` to `rollout-workflow-templates.sh`'s managed file set), is NOT extracted here — it remains
  conflict-gated per the 2026-08-08 round7 sweep's finding against `ci_satellite_ao_dispatch_batch6_2026_08_08.md`
  (D6-1: that batch's own todo 9 owns the `scripts/workflow-templates/` rollout mechanism this round) and was deferred
  to a future ci-tranche batch, not this infra one. Todo 20 itself was independently assessed as conflict-clear by that
  same 2026-08-08 audit ("todo 20 ... shows no conflict on its own ... flagging todo 20 as a RECLASSIFY candidate for a
  future, properly-scoped follow-up once todo 3's collision clears") — this batch is that follow-up, re-conflict-checked
  fresh as of 2026-08-09.
status: active
nature: process
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-ci]
scope: [engineer, admin]
tags: [infra, ao-dispatch, satellite-docs, batch-14, ci-cd, pre-commit, hygiene]
related:
  [
    /plans/active/infra_satellite_ao_dispatch_batch14_finalize_2026_08_09.md,
    /plans/active/shared_ci_workflow_repo_extraction_2026_08_06.md,
    /plans/active/infra_consolidated_closeout_2026_07_25.md,
    /codex/08-workflows/ci-cd-flow.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-09"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0.15
estimate_calibrated_ai_days: 0.12
assigned_role: infra
effort: medium
sequential: false
drift_direction: advance-code
locked_by:
locked_since:
context_scope: [/plans/active/shared_ci_workflow_repo_extraction_2026_08_06.md, /codex/08-workflows/ci-cd-flow.md]
supersedes:
superseded_by:
depends_on: []
source: >-
  `shared_ci_workflow_repo_extraction_2026_08_06.md` todo 20, filed 2026-08-06. Extracted during the round-11
  infra-tranche RECLASSIFY+satellite-extraction sweep (candidate list = docs already carrying a KEEP-NA marker written
  by a staleness-only check, never re-checked against accumulated precedents).
---

# Infra satellite docs — AO dispatch batch 14

## Why this plan exists

`shared_ci_workflow_repo_extraction_2026_08_06.md` extracted the fleet's shared reusable CI-workflow YAML into a new
dedicated public repo, `unified-trading-ci`. That repo was seeded with the pre-push strict-quickmerge hook (installed
automatically at slot-provisioning time, per that plan's todo 7b) but has no `prek` pre-commit hook — so unlike every
other fleet repo, no commit-time gate (gitleaks secret-scan, conventional-commit message check, trailing-whitespace,
etc.) runs on a local commit to this repo before it ever reaches CI. The source plan's own todo 20 flagged this as a
`(stretch, optional)` low-risk consistency gap: "Low risk given the repo's tiny, YAML-only surface, but worth closing
for consistency." This batch extracts exactly that one self-contained todo.

## Conflict check (before drafting)

- **Sibling todo in the same source doc (todo 3)**: confirmed still conflict-gated as of 2026-08-09 — deferred to a
  future ci-tranche batch per the 2026-08-08 `na-eligibility-audit` (round7 RECLASSIFY sweep) Progress Log entry on
  `shared_ci_workflow_repo_extraction_2026_08_06.md`, which cites `ci_satellite_ao_dispatch_batch6_2026_08_08.md` D6-1
  ("Todo 9 owns the `scripts/workflow-templates/` rollout mechanism this round"). That batch is now archived
  (`plans/archive/2026_08/ci_satellite_ao_dispatch_batch6_2026_08_08.md`, `status: complete`); its own D6-1 entry parked
  todo 3 forward to "batch 7" — `ci_satellite_ao_dispatch_batch7_2026_08_09.md` is also now archived
  (`status: complete`) and its content (checked via direct read) does not carry an `image-build-gate.yml`
  rollout-mechanism todo. Todo 3 therefore remains genuinely un-picked-up — but that is the CI tranche's own candidate
  to extract (it owns `scripts/workflow-templates/`'s rollout mechanism per D6-1's own framing), not this infra batch's.
  Not extracted here; left exactly as-is on the source doc.
- **This batch's own item (todo 20)**: grepped `plans/active/*.md` + `plans/active/issues/*.md` for
  `pre-commit-config` + `unified-trading-ci` together — the only hits are
  `infra_satellite_ao_dispatch_batch9_2026_08_09.md` (an unrelated `UV_VERSION` hardcoding follow-up that happens to
  mention `unified-trading-ci` as the live host of a reusable workflow, not a pre-commit-hook task) and
  `cross_cutting_satellite_ao_dispatch_batch6_2026_08_09.md` (an unrelated template-drift-detection todo scoped to
  `unified-trading-pm`, not `unified-trading-ci`'s own repo tooling). No other active plan, satellite batch, or the
  `infra_consolidated_closeout_2026_07_25.md` doc claims this delta.
- Confirmed live: `unified-trading-ci/.pre-commit-config.yaml` does not exist in the current checkout (verified via a
  direct file-existence check against the sibling top-level `unified-trading-ci` clone on this host).

## Todos

- [ ] [INFRA] P3. **Add a `.pre-commit-config.yaml` to `unified-trading-ci`.** Mirror the hook set every other fleet
      repo runs at commit time (gitleaks secret-scan, conventional-commit message check, trailing-whitespace /
      end-of-file-fixer, YAML-lint given this repo's content is 100% workflow YAML) — use an existing lean fleet repo's
      `.pre-commit-config.yaml` as the template (this repo has no Python/Node toolchain, so skip any language-specific
      hooks that don't apply) and wire `scripts/dev/safe-doc-push.sh`-equivalent `prek` invocation per
      `/codex/06-coding-standards/quality-gates.md`'s documented pre-commit convention. Done when: a
      deliberately-introduced secret/bad-commit-message in a scratch commit is caught locally by `prek run` before it
      would reach a push, and a real clean commit to this repo passes `prek run --all-files` with zero violations.
      Source: `shared_ci_workflow_repo_extraction_2026_08_06.md` todo 20. Repo: unified-trading-ci.

## Operator approval gate

**RULED 2026-08-09 (operator, bulk approval): approved.** Flipped `status: draft` → `status: active` in
`unified-trading-pm@78e91572f3` ("flip 14 satellite-extraction batches draft->active for AO dispatch") alongside 13
sibling batches (ao batch9-16, infra batch11-14, prediction batch10, sports batch12); its finalize twin was drafted
alongside it, gated on this plan per the finalize-plan-coverage rule. This banner was stale (still read "awaiting
review" against an already-`active` frontmatter) until fixed by `/ag-closeout-audit infra` 2026-08-10.

## Codex SSOTs (read before touching a todo)

- `/codex/08-workflows/ci-cd-flow.md` — reusable-workflow hosting, `unified-trading-ci`'s role in the fleet
- `/codex/06-coding-standards/quality-gates.md` — `prek` pre-commit hook convention
- `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` — archival ritual the finalize plan runs
- `/plans/active/task_template.md` §4 — finalize-plan-coverage rule

## Progress Log

- **2026-08-09** — Drafted during the round-11 infra-tranche combined RECLASSIFY+satellite-extraction sweep. Paired with
  `infra_satellite_ao_dispatch_batch14_finalize_2026_08_09.md` per the finalize-plan-coverage rule.
