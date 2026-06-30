---
doc_type: plan
title: "CI/CD MVP — LDR→SIT→main, simplified single-path pipeline (supersedes the WS-L complex pipeline)"
summary:
  "OPERATOR DECISION (Harsh + Ikenna, reaffirmed 2026-06-30): we do NOT need the complex CI/CD pipeline. The MVP is:
  commits reach LDR via local-green quality-gates + quickmerge (already enforced) → SIT validates → merge LDR→main.
  Staging is DORMANT (reversible switch kept). The promote gate set is exactly THREE things: SIT-green + quality-gates-v2
  (on the promote PR) + quickmerge-provenance. Everything beyond that — label-check, the SIT cross-repo COMBINATION
  digest, the dep-order gate, version-out-of-source (D13/Phase-2), per-repo cross-repo SIT invariants — is OUT OF SCOPE
  and is what was BLOCKING the pipeline. This plan is the single SSOT for the simplified pipeline; it supersedes the WS-L
  plan family and resolves the promotion-stall issue docs. It also folds in the still-real HEALTH work needed to keep the
  MVP flowing (harden the flaky QG dep-clone, the legacy-ref cleanup, the --delete-branch guard, cron reliability,
  local↔CI parity)."
status: active
nature: process
asset_group: cross-asset
stage: [meta]
repos:
  - unified-trading-pm
  - system-integration-tests
scope: [engineer, admin]
tags: [cicd, mvp, ldr-main, single-path, staging-dormant, SIT, quickmerge, simplification]
related:
  - plans/active/issues/ldr_main_promotion_findings_consolidated_2026_06_29.md
  - codex/08-workflows/ci-cd-flow.md
created: 2026-06-30
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: orchestrator-agent
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 1.2
assigned_role: infra
drift_direction: advance-code
depends_on: []
last_updated: 2026-06-30
locked_by: live-defi-rollout
locked_since: 2026-06-30
supersedes:
  - cicd_consolidated_remaining_2026_06_24.md
  - cicd_retire_staging_branch_2026_06_27.md
  - cicd_staging_main_deadcode_retirement_2026_06_27.md
  - cicd_phase2_foundation_2026_06_27.md
  - cicd_phase2_finalize_2026_06_27.md
  - cicd_phase2_semver_retarget_2026_06_27.md
  - cicd_sit_full_coverage_handoff_2026_06_27.md
  - cicd_workflow_sprawl_consolidation_2026_06_27.md
  - cicd_local_ci_parity_2026_06_27.md
  - cicd_misc_hygiene_2026_06_27.md
  - cicd_deployment_ui_followups_2026_06_27.md
  - cicd_aws_dual_cloud_build_2026_06_27.md
superseded_by:
source: operator directive 2026-06-30 (Harsh, Ikenna offline 2 days) — "we don't need the complex pipeline; MVP = run SIT and merge LDR→main; everything else out of scope"
---

# CI/CD MVP — LDR→SIT→main

> **THE pipeline, simplified to the MVP.** A commit is green locally (`quality-gates.sh`) and reaches `live-defi-rollout`
> via `quickmerge`. SIT validates the LDR content. We merge LDR→main. That's it. `staging` stays dormant behind a
> reversible switch. This plan **supersedes the entire WS-L "complex pipeline" family** (see frontmatter `supersedes`)
> and **resolves** the promotion-stall issue docs. Full forensic detail of how we got here lives in
> `issues/ldr_main_promotion_findings_consolidated_2026_06_29.md` (the findings-of-record).

## The MVP gate set (the ONLY gates on LDR→main)

1. **SIT-green** — the cross-repo SIT suite validated this repo's LDR tree (`full-workspace-sit` on the promoted content).
2. **quality-gates-v2** — the required check on the promote PR (per-repo correctness).
3. **quickmerge-provenance** — only quickmerge'd content reaches main (already enforced on the LDR side).

Plus the trivial mechanics that are not "gates": content-differs, don't-promote-a-RED-repo (Tier-A), runaway-breaker.

## OUT OF SCOPE (the complexity we are removing — this is what was blocking)

These were the WS-L "complex pipeline" and are explicitly deferred/retired for the MVP. Removing them is the core of
Phase 1:

- **label-check gate** (semver-bump match in the promoter) — false-blocked UAC/mtds via the range-asymmetry bug; belongs
  to the version machinery, not the MVP promote.
- **SIT cross-repo COMBINATION workspace-digest** — thrashes under fleet churn (blocked features-service/agent-orch); the
  MVP keeps only the per-repo SIT-tree check.
- **dep-order gate** — turned one flaky tier-0 into a fleet-wide freeze (the overnight incidents); SIT already validates
  the assembled workspace, so it is redundant for the MVP.
- **version-out-of-source / D13 (Phase-2: foundation/finalize/semver-retarget)** — the entire tag→Firestore-registry
  versioning re-architecture. Not needed to "run SIT and merge." Shelved (reversible; revisit if/when wanted).
- **per-repo cross-repo SIT invariants / 21-of-21 full coverage** (`sit_full_coverage_handoff`) — beyond MVP.
- **deploy-infra items** folded from superseded plans, deferred (revisit post-MVP): AWS dual-cloud image build
  (`cicd_aws_dual_cloud_build`), cloudbuild silent-failure alerting, GHA billing-wall, deployment-ui pipeline follow-ups.

## Phase 1 — simplify the promoter to the MVP gate set (the unblock)

- [x] [WORKFLOW] P1. ✅ **label-check gate → advisory** (no longer blocks) — `ldr-to-main-promote-fleet.yml`, PM #729
      (merged main@7ffba64d). Unblocked unified-api-contracts + market-tick-data-service.
- [x] [WORKFLOW] P1. ✅ **SIT cross-repo COMBINATION workspace-digest check REMOVED**; per-repo `sit_validated_tree ==
      LDR tree` kept — PM #729. Unblocked features-service (promoted via per-repo tree match).
- [x] [WORKFLOW] P1. ✅ **dep-order gate → advisory** (removed as a blocker; kills the flaky-tier-0 fleet-freeze) — PM #729.
- [ ] [CONFIG] P1. Flip `e2e-testing` + `ibkr-gateway-infra` to `promotion_model=ldr_main` OR scope branch-health to skip
      non-`ldr_main` repos. **PENDING operator A/B decision.**
- [x] [VERIFY] P1. ✅ Verified from `main`: market-tick-data-service (#469) + deployment-service (#321) + features-service
      (#733) all PROMOTED through the MVP gates (tree-equal); label-check advisory ("promoting anyway"); only UAC held by
      the kept provenance gate (real non-quickmerge code). No false blocks.

## Phase 2 — keep the MVP flowing (health work folded from superseded plans/issues)

- [x] [CICD] P1. ✅ **Harden the flaky QG dep-clone** — retry the primary `live-defi-rollout` clone 3× before the
      stale-tag fallback (the documented dep-resolution-skew root). PM@`4a0607a1` (live on LDR for 38 gates + merged main).
- [x] [CICD] P1. ✅ **Harden the promoter's superseded-ref cleanup** — `process_repo` now deletes the legacy no-slash
      `promote/<repo>` ref before per-SHA creation (PM@`980ef126`, LDR). Reaches main on PM's next promote.
- [x] [CICD] P0. ✅ **`--delete-branch` guard** — `process_repo` auto-closes any stale `head=live-defi-rollout` promote PR
      up-front (PM #732 → main). Self-healing land-mine removal.
- [ ] [CICD] P1. **Cron reliability — LEFT AS-IS per operator (2026-06-30).** GHA `schedule` fires ~1/1.5–2h (best-effort,
      drops ticks). Ikenna to decide when faster draining is needed. Options: (A) self-hosted VM heartbeat dispatching the
      promoter every 15 min via `gh workflow run` [recommended — deterministic]; (B) event-driven dispatch from quickmerge
      when content lands on a repo's LDR. The fleet still drains, just on a 30–90 min cadence.
- [x] [CICD] P1. ✅ **YAML-valid gate now fleet-wide, single-source** — moved the invocation from PM's repo-specific
      `quality-gates.sh` into the shared `base-service.sh` (referencing the ONE PM-hosted checker via `WORKSPACE_ROOT`), so
      every repo validates its own `.github/workflows` with zero per-repo copies. PM@`44280bb3` (LDR; live for all QG).
      Verified from system-integration-tests (15 workflows green). [operator-corrected approach: no rollout]
- [ ] [CICD] P2. **Local↔CI parity** (folded from `cicd_local_ci_parity`): keep local `quality-gates.sh`-green a reliable
      predictor of server `quality-gates-v2`-green (manifest canonical-form churn-protection) — underpins the MVP's
      "commits reach LDR via local-green QG" premise. (Not yet done — lower priority.)

## Phase 3 — verify healthy, then archive the superseded family

- [x] [VERIFY] P1. ✅ Pipeline healthy — from-`main` run promoted mtds + deployment-service + features-service through
      the MVP gates with no false blocks; only real blocks remain (UAC provenance).
- [x] [DOCS] P2. ✅ Archived 12 superseded plans → `plans/archive/2026_06/` + 9 resolved issue docs → `plans/archive/issues/`
      (incl. the consolidated findings doc). Only `cicd_mvp_ldr_to_main_pipeline` remains active.
- [x] [DOCS] P2. ✅ `codex/08-workflows/ci-cd-flow.md` MVP banner added (gate set + retired-gates note + pointer here);
      full rewrite of the 1208-line body deferred (Phase-3 follow-up below).
- [ ] [DOCS] P3. Full rewrite of `ci-cd-flow.md` body + the CLAUDE.md "Git discipline + shipping pipeline" section to the
      MVP (remove the complex-gate prose) — bigger contract edit, for operator review when Ikenna is back.

## Operator decisions / notes

- **dep-order removal** (Phase 1) is the one behavior change with a trade-off (a dependent could reach main before its
  dep; cosmetic since deployments stage from LDR and SIT validates the LDR assembly). Recommendation: remove. Reversible.
- **Phase-2/D13 (version-out-of-source)** is shelved, not deleted — the superseded plans remain in archive as the spec if
  it's ever revived.
- **UAC provenance** + the flaky-QG **Cause A** are the two NON-bug blockers (a real violation + a real flake); they are
  in Phase 2 / owner-handled, not "remove the gate." UAC RESOLVED 2026-06-30 — PR #544 merged (v2+SIT-gated), the
  provenance marker advanced, UAC is content-identical on main.
- **Provenance-gate leak (finding, 2026-06-30) — for Ikenna.** The strict-quickmerge provenance gate runs ONLY on promote
  PR *creation*, not on *re-arm* of an existing clean PR. A later promoter tick found UAC #544 clean and re-armed it past
  the provenance check → it merged on v2 despite the non-QM commits (that's how UAC self-resolved). So the
  quickmerge-provenance gate is NOT airtight — v2+SIT-validated content that bypassed quickmerge can still reach main via
  the re-arm path. For the MVP this is arguably acceptable (content isn't permanently stuck on a provenance technicality;
  it flows once SIT+v2 are green — the MVP's bar). DECISION for Ikenna: accept (MVP-aligned) or close the re-arm leak
  (re-run the provenance check before re-arming an existing PR).
- **Archival caveat (2026-06-30).** `cicd_consolidated_remaining` (archived) was a MULTI-workstream SSOT with ~51 open
  todos beyond the promote pipeline (WS-I service-to-service-auth migration, D13 version-out-of-source, misc P2/P3
  hygiene). Per the operator "everything else out of scope for now" directive these are DEFERRED, living in the archived
  plan as their record; a few codex docs (`codex/07-security/service-to-service-auth.md`, `ci-cd-flow.md` body) still cite
  it. If any non-pipeline workstream (esp. WS-I service-auth) is still wanted, it needs re-homing into an active plan;
  otherwise the archived plan is the deferred spec.

## Codex SSOTs

- `codex/08-workflows/ci-cd-flow.md` (the pipeline SSOT — update to the MVP at Phase 3).
- `codex/06-coding-standards/integration-testing-layers.md` (SIT's role).

## Progress Log

- 2026-06-30: Created as the single MVP SSOT per operator directive. Supersedes the WS-L complex-pipeline plan family
  (12 plans) and resolves the promotion-stall issue docs (statuses flipped the same day, ahead of the Phase-1 work).
  Phase-1 unblock (gate removal) + Phase-2 health work folded in so nothing is lost on archival.
- 2026-06-30 (Phase 1 + 3 done): Shipped the promoter simplification (PM #729 → main@7ffba64d) — label-check + dep-order
  → advisory, SIT-combination digest removed (per-repo tree check kept). Verified from `main`: mtds #469 +
  deployment-service #321 + features-service #733 all PROMOTED through the MVP gates, no false blocks; only UAC held by
  the kept provenance gate. Archived the 21 superseded/resolved docs (12 plans → archive/2026_06, 9 issue docs →
  archive/issues); ci-cd-flow.md MVP banner added. REMAINING: Phase 2 health items (flaky-QG, ref-cleanup, delete-branch
  guard, cron, YAML-gate coverage), the e2e/ibkr A/B decision, the UAC provenance re-ship (owner), and the Phase-3 full
  ci-cd-flow/CLAUDE.md rewrite (for Ikenna).
