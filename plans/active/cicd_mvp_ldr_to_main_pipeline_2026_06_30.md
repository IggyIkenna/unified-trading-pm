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

- [ ] [WORKFLOW] P1. In `ldr-to-main-promote-fleet.yml`, **remove the label-check gate** (stop blocking on semver-bump
      mismatch). Unblocks unified-api-contracts + market-tick-data-service.
- [ ] [WORKFLOW] P1. **Remove the SIT cross-repo COMBINATION workspace-digest check**; keep the per-repo
      `sit_validated_tree == LDR tree` check. Unblocks features-service + agent-orchestrator.
- [ ] [WORKFLOW] P1. **Remove (or, operator's call, neuter) the dep-order gate** so a flaky tier-0 can't fleet-freeze
      promotion. (Recommendation: remove — SIT is the cross-repo guarantee. Reversible.)
- [ ] [CONFIG] P1. Flip `e2e-testing` + `ibkr-gateway-infra` to `promotion_model=ldr_main` so they have the MVP promote
      path (today the monitor alerts on a path that doesn't exist), OR scope branch-health to skip non-`ldr_main` repos.
- [ ] [VERIFY] P1. After the change: a fleet run promotes the 4 currently-stuck repos (UAC, mtds, features-service, +
      e2e once pathed); `Promoted (N>0)`; no false blocks. (UAC's provenance block is separate — real non-quickmerge
      code, owner to re-ship.)

## Phase 2 — keep the MVP flowing (health work folded from superseded plans/issues)

- [ ] [CICD] P1. **Harden the flaky QG dep-clone** (phantom-version / stale-deps fallback) — the recurring overnight root
      that re-stales UTL's tier-0 ci_status (Cause A). Make the cross-repo dep resolution deterministic / fail loud.
      (folded from `fleet_promote_schedule_yaml_break`, `utl_main_red_dep_resolution_skew`.)
- [ ] [CICD] P1. **Harden the promoter's superseded-ref cleanup** to also delete the legacy no-slash `promote/<repo>` ref
      (the D/F-conflict that froze 15/21 repos; refs already cleared manually 2026-06-29).
- [ ] [CICD] P0. **Never arm `--delete-branch` on a `head=live-defi-rollout` PR** (it deleted deployment-ui's LDR branch);
      add a guard + a recurring sweep for legacy armed PRs.
- [ ] [CICD] P1. **Make LDR→main promotion not depend on GitHub's unreliable scheduled cron** (`*/15` actually fired
      ~1/1.5–2h) — event-driven (push-to-LDR) trigger or a self-hosted heartbeat.
- [ ] [CICD] P1. **Extend `check_workflow_yaml_valid.py`** to cover `system-integration-tests` (+ all repos carrying
      `.github/workflows`), not just PM — the SIT-producer YAML break slipped through because the gate was PM-scoped.
- [ ] [CICD] P2. **Local↔CI parity** (folded from `cicd_local_ci_parity`): keep local `quality-gates.sh`-green a reliable
      predictor of server `quality-gates-v2`-green (manifest canonical-form churn-protection) — underpins the MVP's
      "commits reach LDR via local-green QG" premise.

## Phase 3 — verify healthy, then archive the superseded family

- [ ] [VERIFY] P1. Pipeline healthy = a full fleet tick promotes all eligible repos with no false blocks for 2
      consecutive runs; the only blocks are real (RED repo / genuine non-quickmerge provenance).
- [ ] [DOCS] P2. Physically move the superseded plans + resolved issue docs to `plans/archive/2026_06/` (operator pass;
      they were status-flipped 2026-06-30 ahead of this).
- [ ] [DOCS] P2. Update `codex/08-workflows/ci-cd-flow.md` to the MVP gate set (remove the complex-gate descriptions).

## Operator decisions / notes

- **dep-order removal** (Phase 1) is the one behavior change with a trade-off (a dependent could reach main before its
  dep; cosmetic since deployments stage from LDR and SIT validates the LDR assembly). Recommendation: remove. Reversible.
- **Phase-2/D13 (version-out-of-source)** is shelved, not deleted — the superseded plans remain in archive as the spec if
  it's ever revived.
- **UAC provenance** + the flaky-QG **Cause A** are the two NON-bug blockers (a real violation + a real flake); they are
  in Phase 2 / owner-handled, not "remove the gate."

## Codex SSOTs

- `codex/08-workflows/ci-cd-flow.md` (the pipeline SSOT — update to the MVP at Phase 3).
- `codex/06-coding-standards/integration-testing-layers.md` (SIT's role).

## Progress Log

- 2026-06-30: Created as the single MVP SSOT per operator directive. Supersedes the WS-L complex-pipeline plan family
  (12 plans) and resolves the promotion-stall issue docs (statuses flipped the same day, ahead of the Phase-1 work).
  Phase-1 unblock (gate removal) + Phase-2 health work folded in so nothing is lost on archival.
