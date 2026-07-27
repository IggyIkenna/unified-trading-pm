---
doc_type: plan
title: Give ao/ci/infra real asset_group enum values — retag the corpus, stop the cross-cutting ambiguity bug
summary: >-
  ao/ci/infra content has been tagged bare `asset_group=cross-cutting` since 2026-07-25 (avoiding a schema migration) --
  but `/ag-closeout-audit`'s own docs admit this needs real per-doc content judgment, not a mechanical rule, because
  `parent_epic=infrastructure_master` is shared by BOTH genuine cross-cutting data-pipeline docs and pure ci/infra
  content. Confirmed live 2026-07-27: a fresh 9-tranche audit found 37 of 40 cross-cutting candidates were genuinely
  ao/ci/infra -- a 92.5% false-positive rate on the current tag. This plan adds `ao`/`ci` as real enum values (infra
  already exists), retags the ~220-doc affected population, and updates every schema-definition site. The
  epic/consolidated-plan/batch scaffolding for ao/ci/infra already exists (`ao_consolidated_closeout_2026_07_25.md` etc)
  -- this is a tag-correctness fix, not new infrastructure.
status: active
nature: design
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [asset-group, schema, taxonomy, ao, ci, infra, cross-cutting, retag, ag-closeout-audit]
related:
  [
    /plans/active/task_template.md,
    /plans/PLAN_FORMAT.md,
    /plans/active/na_docs_validity_and_ao_eligibility_audit_2026_07_26.md,
    /codex/11-project-management/doc-frontmatter-schema.md,
  ]
created: "2026-07-27"
last_updated: "2026-07-27"
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 1.2
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source:
  "operator directive 2026-07-27, following a fresh /ag-closeout-audit all run whose cross-cutting tranche measured a
  37/40 (92.5%) false-positive rate on the current bare-cross-cutting tag for ao/ci/infra content"
assigned_role: infra
drift_direction: advance-docs
---

# Give ao/ci/infra real asset_group enum values

> **Why LOCAL, not AO-dispatched**: "should ao/ci/infra become real asset_group values" is a taxonomy judgment call, not
> a worker-executable todo (operator confirmed 2026-07-27: "definitely to be done locally to avoid getting to that
> backlog of already 700 backlog AO queue" — the very ambiguity this plan fixes would make a naive AO-dispatched version
> of this retag pass hard to trust). The retag EXECUTION (Phase 2) is mechanical once the schema decision is made, and
> could in principle run on the fleet — but it touches the same corpus `/ag-closeout-audit`'s own classification depends
> on, so a first pass stays local/supervised; a future batch could dispatch remaining docs once this plan proves the
> pattern.

> **🟡 Coordination note (2026-07-27) — a concurrent agent is live-building overlapping infrastructure.** Mid-session,
> another AO worker was found actively shipping: a new `na-eligibility-audit` skill
> (`cursor-configs/skills/na-eligibility-audit/SKILL.md`), a shared conflict-check SSOT
> (`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md`), a `check_na_corpus_ratchet.py`
> shrinking-ratchet gate wired into `run_hygiene_sweep.sh`, an `agents/na_eligibility_auditor.md` worker role, and edits
> to `cursor-configs/skills/ag-closeout-audit/SKILL.md` + `plan-reconcile/SKILL.md` + `task_template.md` + `CLAUDE.md`.
> **This plan deliberately does NOT touch any of those files** — Phase 3 (originally "update ag-closeout-audit SKILL.md
> to reflect the new schema") is dropped entirely; that skill's classification-mechanism section will need a follow-up
> once the new enum values exist AND the concurrent agent's rewrite has landed and stabilized. The scheduling/sharding
> work from an earlier plan-mode session (`federated-wishing-lovelace.md` — retime nightly crons + shard
> `/ag-closeout-audit all` dispatch via a new `tranche` field on `plan_health.py`'s `PlanHealthDispatchRequest`) is also
> NOT started here — the concurrent agent's own todo list includes "wire dispatch mode server-side (plan_health.py)", a
> same-file collision risk. Re-check both before resuming either piece.

## Phase 1 — Schema definition (3 files, mechanical, additive-only)

- [ ] [SCRIPT] P1. Add `ao` and `ci` to `ASSET_GROUP` in `scripts/docs/docspec.py` (currently
      `frozenset({"cefi", "defi", "tradfi", "sports", "prediction", "cross-cutting", "infrastructure", "meta"})` —
      `infra` already has a home via the existing `infrastructure` value; only `ao`/`ci` are missing). Additive-only,
      non-breaking — no existing doc's valid tag changes.
- [ ] [DOC] P1. Update `plans/PLAN_FORMAT.md`'s `asset_group` enum documentation to match.
- [ ] [DOC] P1. Update `/codex/11-project-management/doc-frontmatter-schema.md`'s `asset_group` enum documentation to
      match (this is the human SSOT `docspec.py` mirrors — keep them in lockstep per that doc's own header).
- [ ] [REVIEW] P2. Grep every consumer of the asset_group enum outside docs (`grep -rl "ASSET_GROUP" --include=*.py`
      found 444 hits workspace-wide at scoping time, plus 264 in deployment-ui/deployment-api) for any hardcoded "5
      AGs + cross-cutting" closed-list assumption that would need to ALSO learn about `ao`/`ci` (most are enum consumers
      that just need the new values present, not rewritten logic — but confirm before assuming zero UI/API impact).

## Phase 2 — Corpus-wide retag pass

- [ ] [SCRIPT] P2. Re-run `generate_ag_closeout_audit_candidates.py`-style membership derivation across the FULL 241-doc
      bare-`[cross-cutting]` population (not just the 40-doc sample from the fresh audit) to get a complete
      classification: genuinely cross-cutting (stays as-is) vs. really-ao vs. really-ci vs. really-infra (retag to the
      new/existing value). Use real per-doc agent reads, not a mechanical epic-only rule — that is exactly the trap this
      plan exists to fix.
- [ ] [DOC] P2. Retag every confirmed ao/ci/infra doc found above: `asset_group: [cross-cutting]` -> `asset_group: [ao]`
      / `[ci]` / `[infrastructure]` as appropriate. Batch via QG-sweep (gate once, commit in reasonably-sized units, not
      one file per commit). Re-run `check_ag_closeout_linkage.py` after each batch (per the ag-closeout-audit skill's
      own documented finding: a retag can newly orphan a doc WITHIN its real tranche if nothing in that tranche's
      closeout family mentions it yet — the linkage check catches this, don't skip it).
- [ ] [REVIEW] P2. **Done when**: re-running the fresh-audit citation-pre-filter methodology against `cross-cutting`
      shows a false-positive rate near 0% (down from 37/40), and `check_ag_closeout_linkage.py` reports 0 orphans
      post-retag.

## Phase 3 — Follow-ups intentionally NOT in this plan (tracked, not silently dropped)

- [ ] [REVIEW] P3. Once the concurrent `na-eligibility-audit`/`ag-closeout-audit` skill work (see coordination note
      above) has landed and stabilized, revisit whether `ag-closeout-audit` SKILL.md's classification-mechanism section
      needs a follow-up edit now that ao/ci have real enum values (its current "no dedicated asset_group value — read
      the closeout doc's Sources list instead" workaround section becomes obsolete once Phase 1+2 land).
- [ ] [REVIEW] P3. Once `plan_health.py` is confirmed not mid-edit by the concurrent agent, resume the
      `federated-wishing-lovelace` scheduling design (retime `ag-closeout-auditor`/`docs-reconcile`/`plan-reconciler`
      nightly timers to 2h gaps; shard `/ag-closeout-audit all` into 9 parallel per-tranche AO workers via a new
      `tranche` field threaded through `PlanHealthDispatchRequest` -> `autospawn._do_spawn` -> a single-tranche STEP 1
      variant in `agents/ag_closeout_auditor.md`) — full design already scoped, not re-derived here.

## Codex SSOTs

- `plans/active/task_template.md` §1-2 (LOCAL vs AO track, frontmatter)
- `codex/11-project-management/doc-frontmatter-schema.md` (asset_group enum SSOT)
- `cursor-configs/skills/ag-closeout-audit/SKILL.md` (classification-mechanism section this plan's schema change
  eventually simplifies — do not edit until the concurrent rewrite lands, see coordination note)

## Progress Log

- **2026-07-27** — Scoped by operator directive following a fresh `/ag-closeout-audit all` run
  (`na_docs_validity_and_ao_eligibility_audit_2026_07_26.md`'s Progress Log) that measured a 37/40 false-positive rate
  on the bare-`cross-cutting` tag for ao/ci/infra content. Blast radius checked before drafting: 241 docs currently
  bare-tagged `[cross-cutting]`, 444+264 code references to the enum (mostly consumers, not hardcoded lists). Not yet
  started — Phase 1 is next.
