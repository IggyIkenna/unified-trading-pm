---
doc_type: issue
title: /codex/08-workflows/deployment-flow.md still describes the retired staging-mediated pipeline as current
summary: >-
  Discovered as a side effect of the qg_sentinel_environment_blind_2026_07_23.md fix (ci_satellite_ao_dispatch_batch2
  todo 1): deployment-flow.md's "Full Pipeline: LDR → Cloud Build" diagram and Gate 1/2/3 walkthrough describe the OLD
  staging-mediated promotion model (quickmerge → staging PR → auto-merge → semver-agent on staging → staging-to-main) as
  the operator-facing default. CLAUDE.md's current rule is the opposite: "default promote is LDR→main DIRECT — staging
  DORMANT" (per-repo `promotion_model: ldr_main` toggle). ci-cd-flow.md was already fully rewritten to the new MVP model
  (cicd_mvp_ldr_to_main_pipeline_2026_06_30.md's Phase-3 P0 DOCS todo, unified-trading-pm@b9d0b9209) but that plan never
  touched deployment-flow.md, so the two sibling docs (engineer view vs operator view, per each doc's own header) now
  disagree on the actual pipeline shape.
status: resolved
nature: issue
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ci-cd, docs, codex, staleness, ldr-direct, deployment-flow]
related:
  - /codex/08-workflows/deployment-flow.md
  - /codex/08-workflows/ci-cd-flow.md
  - /plans/archive/2026_07/cicd_mvp_ldr_to_main_pipeline_2026_06_30.md
created: 2026-07-30
author: unknown
priority: P2
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
drift_direction: correct-codex
assigned_role: infra
estimate_class: refactor
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.24
locked_by:
resolved_by: unified-trading-pm@445f02081 (2026-08-06, ci_satellite_ao_dispatch_batch4 [DOC] P2)
depends_on: []
context_scope:
  [
    /codex/08-workflows/deployment-flow.md,
    /codex/08-workflows/ci-cd-flow.md,
    /plans/archive/2026_08/ci_satellite_ao_dispatch_batch4_2026_07_31.md,
  ]
source:
  - "surfaced while updating deployment-flow.md's sentinel-format claims for qg_sentinel_environment_blind_2026_07_23.md
    (ci_satellite_ao_dispatch_batch2 todo 1) — the local sentinel-format fix was applied inline (small+clear), but the
    doc's much larger structural staleness (whole pipeline model) is out of that todo's scope"
---

# deployment-flow.md pre-dates the LDR-direct MVP pipeline

## What I found

`/codex/08-workflows/deployment-flow.md`'s "Full Pipeline: LDR → Cloud Build" ASCII diagram (§ near the top) and its
Gate 1/2/3 walkthrough sections describe promotion as: quickmerge → `gh pr create` to `staging` (auto-merge) →
`workspace-qg` GHA on the staging PR → semver-agent bumps on staging → `staging-to-main.yml` squash-merges to `main`.

This is the **retired** model. Per CLAUDE.md § "Git discipline + shipping pipeline" (current) and
`cicd_mvp_ldr_to_main_pipeline_2026_06_30.md` (the migration plan, `status: active`, already substantially shipped):
**quickmerge lands on LDR directly; default promote is LDR→main DIRECT with staging DORMANT** (a reversible per-repo
`promotion_model: ldr_main` toggle). The gate set is now exactly three checks (`sit-gate/fleet-green` +
`quality-gates-v2` + quickmerge-provenance), not the staging-mediated chain this doc still walks through.

`ci-cd-flow.md` (the sibling "engineer view" doc, per both docs' own headers) was fully rewritten to the MVP model as
that plan's Phase-3 P0 DOCS todo (`unified-trading-pm@b9d0b9209`) — but `deployment-flow.md` (the "operator view") was
never touched in that pass and still reads as if staging-mediation is the live default.

I fixed the narrow, LOCAL overlap with my own change (the `.qg_last_passed_sha` sentinel now also carries
`ENVIRONMENT`/`DEPLOYMENT_ENV`, not just the SHA) at the two spots in this doc that specifically describe the sentinel
format — that part is done, in the same commit as the code fix. The BROADER staleness (the whole pipeline-shape
narrative) is untouched; fixing it properly is a doc-rewrite of similar scope to `ci-cd-flow.md`'s own Phase-3 rewrite,
not a small drive-by edit, so I did not attempt it inline.

## Why it matters

An operator or agent reading `deployment-flow.md` today to understand "what actually happens after I push to LDR" gets a
materially wrong mental model — it describes a staging PR + auto-merge + semver-on-staging chain that, per the current
default, doesn't run for most repos anymore. This is exactly the kind of doc↔reality drift CLAUDE.md's "post- phase
codex audit" rule exists to prevent, and it was apparently missed when `cicd_mvp_ldr_to_main_pipeline` did its Phase-3
codex sweep (that plan's own `## Codex SSOTs` section names only `ci-cd-flow.md` and `integration-testing-layers.md` —
`deployment-flow.md` was never in scope for that pass despite being a direct sibling doc covering the same pipeline).

## Recommended decision

Fold this into `cicd_mvp_ldr_to_main_pipeline_2026_06_30.md` (it's still `status: active` and already owns the
ci-cd-flow.md rewrite precedent to follow) as a new todo, OR — if that plan is close to archival — dispatch it as its
own small AO-eligible todo: rewrite `deployment-flow.md`'s pipeline diagram + Gate 1/2/3 sections to the current
LDR-direct-with-dormant-staging model, mirroring `ci-cd-flow.md`'s already-shipped rewrite (same source of truth, just
the operator-facing framing). Bounded, deterministic outcome (diff the two docs' pipeline descriptions against
CLAUDE.md's current § "Git discipline"), so it's AO-dispatchable once picked up.

## Todos

- [x] ✅ [DOC] P2. Rewrite `/codex/08-workflows/deployment-flow.md`'s "Full Pipeline: LDR → Cloud Build" diagram + Gate
      1/2/3 walkthrough to reflect the LDR-direct-promote-with-dormant-staging model (mirror `ci-cd-flow.md`'s already-
      shipped rewrite, `unified-trading-pm@b9d0b9209`, for the target shape). Done when: the two sibling docs (engineer
      view / operator view) describe the SAME pipeline shape, and every staging-mediated-as-default claim in
      `deployment-flow.md` is corrected or explicitly marked as the non-default toggle path. **DONE — shipped via
      `/plans/archive/2026_08/ci_satellite_ao_dispatch_batch4_2026_07_31.md`'s `[DOC] P2` item:
      `unified-trading-pm@445f02081` (2026-08-06T17:02:28Z, "docs(codex): rewrite deployment-flow.md pipeline diagram +
      Gates 1/2/3 for LDR-direct model"), confirmed a real ancestor of `origin/live-defi-rollout`. Live-verified
      2026-08-09 (stale-recheck sweep): the doc now carries a "Target branch updated for the LDR-direct model" banner
      and the rewritten pipeline sections. Batch4's own doc had already flipped this checkbox at the source
      (`status: active`) — this doc's citation-copy was simply never updated to match; closing that gap now.**

## na-eligibility-audit verdict

**na-eligibility-audit 2026-07-31** (tranche `ci`, autonomous): **KEEP-NA-STALE (already-duplicated).** Taken in
isolation this todo reads as a clean RECLASSIFY candidate (small, bounded, calibrated 0.24 AI-days, explicit done-when,
mirrors an already-shipped precedent). But the sibling `/ag-closeout-audit ci` skill's same-day draft
`/plans/archive/2026_08/ci_satellite_ao_dispatch_batch4_2026_07_31.md` has **already extracted this exact todo
verbatim** (its own `[DOC] P2` item, citing
`Source: issues/deployment_flow_doc_stale_pre_ldr_direct_mvp_2026_07_30.md`). Reclassifying this doc's own `assigned_vm`
now would open a second, independent dispatch path to the identical file edit once batch4 activates. Staying NA until
batch4 either ships this todo or is archived without shipping it — if the latter, re-open this doc as a RECLASSIFY
candidate on the next audit pass. (Also flags a cross-skill population overlap worth a standing fix — see
`/plans/active/issues/na_and_ag_closeout_audit_population_overlap_2026_07_31.md`.)

**na-eligibility-audit 2026-08-02** (tranche `ci`, autonomous): **CONFIRMS KEEP-NA-STALE, unchanged.** Re-verified the
holding condition live rather than trusting the prior verdict: `ci_satellite_ao_dispatch_batch4_2026_07_31.md` still
exists, still carries this exact todo verbatim as its own `[DOC] P2` item, and is still `status: draft` — i.e. neither
shipped nor archived-unshipped, so the "re-open as RECLASSIFY" trigger has NOT fired. The only change to this doc since
the last marker is the 2026-08-01 context-scout `context_scope` backfill (metadata only). Citation fix applied to the
open checkbox above this run so a future pass does not re-flag the same content as an unaddressed orphan.

**na-eligibility-audit 2026-08-04** (tranche `ci`, autonomous): **CONFIRMS KEEP-NA-STALE, unchanged.** Re-walked full
git history past the 2026-08-02 marker via `git log --follow -p`: exactly 2 commits, both mechanical (a
reference-path-format normalization touching only the leading-slash form of one codex path, and a context-scout rescout)
— zero content change. Live re-verified the holding condition: `ci_satellite_ao_dispatch_batch4_2026_07_31.md` still
exists, is still `status: draft`, and its `[DOC] P2` todo still cites this doc verbatim as Source. The "re-open as
RECLASSIFY" trigger has not fired.

## Progress Log

- **context-scout 2026-08-01**: populated context_scope (3 entries).
- **context-scout 2026-08-03**: refreshed context_scope (3 entries, unchanged) —
  `ci_satellite_ao_dispatch_batch4_2026_07_31.md` confirmed still `status: draft` and still carrying this todo verbatim,
  so the set stands.
- **context-scout 2026-08-05**: re-scouted; context_scope re-verified (3 entries), unchanged.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (3 entries), unchanged.

**na-eligibility-audit 2026-08-06**: KEEP-NA-STALE — doc rewrite todo extracted verbatim to
ci_satellite_ao_dispatch_batch4_2026_07_31.md (still draft)
