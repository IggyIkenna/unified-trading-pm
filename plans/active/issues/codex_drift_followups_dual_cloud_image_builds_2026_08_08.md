---
doc_type: issue
title: Follow-up findings from fixing dual-cloud-image-builds.md's 5 named codex drifts (2026-08-08)
summary: >-
  While fixing the 5 named codex drifts in `/codex/05-infrastructure/dual-cloud-image-builds.md`
  (`ui_satellite_ao_dispatch_batch1-003`, source `artifact_pipeline_observability_2026_07_17.md` Phase 5) and running
  the standard post-phase codex audit on the rest of the doc, live verification against GCP/AWS turned up several
  smaller findings that are code/infra changes, not doc corrections, so they're out of scope for that narrowly-scoped
  doc-correction task. Tracked here per the findings-closure rule.
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm, deployment-service]
scope: [engineer, admin]
tags: [ci-cd, dual-cloud, codex-drift, gcp, aws, cloud-build, provenance]
related:
  [
    /codex/05-infrastructure/dual-cloud-image-builds.md,
    /plans/active/artifact_pipeline_observability_2026_07_17.md,
    /plans/active/ui_satellite_ao_dispatch_batch1_2026_08_06.md,
    /codex/05-infrastructure/orchestrator-cloud-identity-self-service.md,
  ]
created: "2026-08-08"
last_updated: "2026-08-08"
author: ikennaigboaka [slot-5]
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.12
assigned_role: infra
drift_direction: advance-process
depends_on: []
locked_by:
locked_since:
resolved_by:
source: >-
  ui_satellite_ao_dispatch_batch1-003 ("Fix the 5 named dual-cloud-image-builds.md codex drifts"), 2026-08-08, slot 5.
context_scope: [/codex/05-infrastructure/dual-cloud-image-builds.md]
---

# Follow-up findings from fixing dual-cloud-image-builds.md's codex drifts

## What I found

Fixing the 5 named drifts (registry name, tag convention, trigger/project naming, canonical-trigger claim,
empty-manifest provenance) required re-verifying live GCP/AWS state (per the todo's own "Done when" evidence
requirement). That live verification surfaced additional issues that are code/infra fixes, not doc corrections, so they
weren't folded into the doc-only task:

1. **`scripts/propagation/templates/cloudbuild.yaml`'s `_AR_REPO` substitution default is stale** — it reads
   `_AR_REPO: "unified-trading"`, but the real Artifact Registry repository is `unified-trading-system` (verified live
   2026-08-08: `unified-trading` returns `NOT_FOUND`). This PM-owned template appears unused by the actual per-repo
   `cloudbuild.yaml` files (they use their own `_REGISTRY_REPO` substitution, correctly defaulted to
   `unified-trading-system` — confirmed on `execution-service` and `market-tick-data-service`), so this may be
   dead/orphaned rather than actively misleading a build — but it's still wrong and would mislead anyone using it as a
   base for a new repo's `cloudbuild.yaml`.
2. **`cloud-build-router.yml`'s `gcloud builds triggers run` call hardcodes `_AR_REPO=unified-trading`** (same stale
   name) in its `--substitutions` list. Per-repo `cloudbuild.yaml` files don't reference `_AR_REPO` (they use
   `_REGISTRY_REPO` with their own correct default), so this substitution appears to be dead/unused — but dead-and-wrong
   is still worth cleaning up so it doesn't get copy-pasted into a future change.
3. **Two GCP Cloud Build triggers, `api-contracts-build` and `api-contracts-feature-build`, look like a stale naming
   leftover** from before the repo was renamed to `unified-api-contracts` — the live trigger list
   (`gcloud builds triggers list --project=central-element-323112 --region=asia-northeast1`, 2026-08-08) shows both
   these AND a separate `unified-api-contracts-live-defi-rollout` trigger. Not confirmed whether the `api-contracts-*`
   pair still fires (would need to check each trigger's GitHub repo binding) — flagging as a possible orphan pair worth
   checking, not asserting they're dead.
4. **AWS-side claims in the codex doc (project naming = bare `<repo>`, and the "router is canonical" nuance) could not
   be independently re-verified this pass.** This worker's ambient AWS identity is
   `arn:aws:iam::427895769566:user/ikenna-worker`, which lacks `codebuild:ListProjects` / `codebuild:BatchGetBuilds`,
   and IAM introspection/self-grant on THAT identity is out of scope — the documented AO self-service identity for this
   exact "hit a permission gap, grant it yourself" pattern is the separate `uts-orchestrator-epic-role` (EC2
   instance-profile role, not assumable from this worktree — no metadata service reachable here), per
   `/codex/05-infrastructure/orchestrator-cloud-identity-self-service.md`. The codex doc retains the original 2026-07-17
   measurement for these claims, explicitly flagged as unverified-this-pass.
5. **`workspace-manifest.json`'s `deployed_versions`/`deployed_versions_aws` provenance fields are dead code paths, not
   just stale docs.** `cloud-build-router.yml`/`cloud-build-router-aws.yml` are both written to update these fields on a
   successful build, but live state (verified 2026-08-08) shows `deployed_versions` is present-but-empty
   (`{"dev": {}, "staging": {}, "prod": {}}`) and `deployed_versions_aws` is entirely absent — meaning either the write
   path is broken, or it was never wired up to begin with. The codex doc now describes this honestly (fixed), but the
   underlying code intent (recording build provenance in the manifest) is currently unfulfilled either way.

## Why it matters

None of these block the doc fix itself (which is now accurate against live state), but each represents either
dead/misleading code (findings 1-3) that could confuse a future change, or a genuine capability gap (finding 4) that
should be closed properly rather than worked around repeatedly, or a real provenance gap (finding 5) that means "what
got deployed where" cannot currently be answered from the manifest at all — a data-correctness- adjacent gap for a
build/deploy pipeline, even if not the live-trading-critical kind.

## Recommended decision

No operator decision needed to act on 1-3 and 5 — they're bounded, deterministic-outcome fixes. Finding 4 is
informational (either grant `ikenna-worker` narrow least-privilege `codebuild:ListProjects`/ `codebuild:BatchGetBuilds`
read-only access if it's meant to be a general AWS-capable identity, or confirm it isn't and stop expecting AWS read
access from this worktree).

## Todos

- [x] ✅ [INFRA] P3. **KEEP-NA-STALE — CLOSED 2026-08-09 (reclassify+satellite sweep, round 9): duplicated verbatim in
      `infra_satellite_ao_dispatch_batch9_2026_08_09.md` todo 2, which is now `status: active`** (flipped by operator
      2026-08-09, confirmed live in this same session — an earlier same-day na-eligibility-audit pass found this exact
      duplication but withheld the close because batch9 was still `status: draft` at that time; it has since activated).
      Tracked there going forward. Original: Update `scripts/propagation/templates/cloudbuild.yaml`'s `_AR_REPO` default
      from `"unified-trading"` to `"unified-trading-system"` (or confirm the template is fully superseded by the
      per-repo `_REGISTRY_REPO` convention and delete/retire it instead — check whether
      `rollout-workflow-templates.sh --template cloudbuild.yaml` is still ever run). Repo: unified-trading-pm.
- [x] ✅ [INFRA] P3. **KEEP-NA-STALE — CLOSED 2026-08-09, same batch9 todo 2 as above** (todo 2 explicitly bundles both
      the template default AND the workflow hardcode as one two-part fix). Original: Remove or correct the hardcoded
      `_AR_REPO=unified-trading` substitution in `.github/workflows/cloud-build-router.yml`'s `gcloud builds triggers run`
      call (confirm it's genuinely unused by every per-repo `cloudbuild.yaml` before deleting — grep the fleet for any
      repo whose `cloudbuild.yaml` still references `_AR_REPO` instead of `_REGISTRY_REPO`). Repo: unified-trading-pm.
- [x] ✅ [INFRA] P3. **KEEP-NA-STALE — CLOSED 2026-08-09: duplicated verbatim in
      `infra_satellite_ao_dispatch_batch9_2026_08_09.md` todo 3 (status: active).** Original: Check whether the
      `api-contracts-build` / `api-contracts-feature-build` GCP Cloud Build triggers are orphaned (pre-rename leftovers
      from before `unified-api-contracts`'s current name) and, if confirmed dead, delete them via
      `gcloud builds triggers delete`. Repo: unified-trading-pm (trigger ownership) / central-element-323112 (GCP
      project).
- [x] ✅ [INFRA] P3. **KEEP-NA-STALE — CLOSED 2026-08-09: duplicated verbatim in
      `infra_satellite_ao_dispatch_batch9_2026_08_09.md` todo 4 (status: active).** Original: Decide + fix
      `deployed_versions`/`deployed_versions_aws` manifest provenance: either wire up the actual write path in
      `cloud-build-router.yml` / `cloud-build-router-aws.yml` so these fields get populated on a successful build, or
      remove the dead write-intent code and stop presenting the manifest as a provenance source anywhere in the
      codebase. Repo: unified-trading-pm.
- [ ] [OPERATOR] P3. **RULED 2026-08-09 (operator): grant `ikenna-worker`'s AWS IAM identity read-only
      `codebuild:ListProjects`/`codebuild:BatchGetBuilds`.** STANDING-ACTION — the decision is made, execution is still
      pending: applying this grant requires the operator's own AWS console/CLI access, not a worker-self-serviceable
      identity (`ikenna-worker` is a human-owned IAM user, distinct from the self-service `uts-orchestrator-epic-role`
      covered by `/codex/05-infrastructure/orchestrator-cloud-identity-self-service.md`). Stays open until the operator
      (or someone with the operator's AWS access) actually applies the grant; done when a worker re-verifies the
      capability live (`aws codebuild list-projects` succeeding as `ikenna-worker` from a worker worktree).

## Progress Log

- **reclassify+satellite sweep 2026-08-09 (infra tranche, round 9)**: KEEP-NA-STALE — closed all 4 `[INFRA]` todos.
  Confirmed live: `infra_satellite_ao_dispatch_batch9_2026_08_09.md` flipped `status: draft` → `status: active` earlier
  today (operator-approved) — this closes exactly the gap the same-day na-eligibility-audit pass below identified
  ("falls short of the KEEP-NA-STALE bar... recommend a forward-pointer citation once batch9 activates"). Doc stays
  `assigned_vm: NA` overall — the sole remaining item (grant `ikenna-worker`'s AWS IAM identity) is a genuine
  `[OPERATOR]` standing-action, not worker-dispatchable.
- **na-eligibility-audit 2026-08-09** (infra tranche) [body-hash:8ba083853016bd9a]: KEEP-NA, valid — first verdict for
  this doc. Findings 1/2/3/5 (all `[INFRA]`-tagged) already extracted verbatim into
  `infra_satellite_ao_dispatch_batch9_2026_08_09.md` (status: draft, not yet active — falls short of the KEEP-NA-STALE
  bar, which requires an ACTIVE extracting doc). Finding 4 (AWS IAM identity scope for `ikenna-worker`) is a genuine
  `[OPERATOR]` decision, correctly not extracted. Recommend a forward-pointer citation once batch9 activates.
- **context-scout 2026-08-09**: re-scouted; context_scope unchanged (1 entry), still accurate.
- **2026-08-09 (operator ruling)**: RULED — grant `ikenna-worker`'s AWS identity read-only
  `codebuild:ListProjects`/`codebuild:BatchGetBuilds`. Kept `[OPERATOR]` (not retagged away) and marked STANDING-ACTION:
  the decision is made but execution requires the operator's own AWS console/CLI access, which no worker can self-serve
  for this identity. Stays open pending the actual grant + a live re-verification.
