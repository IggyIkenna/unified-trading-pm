---
title: CI/CD docs + diagram refresh, then plan/issue consolidation
name: cicd_docs_and_consolidation_2026_06_18
parent_epic: infrastructure_master
assigned_vm: vm-cross-cutting
created: 2026-06-18
date: 2026-06-18
author: ikenna [autonomous]
status: active
locked_by: live-defi-rollout
locked_since: 2026-06-18
priority: P1
estimate_class: design
estimate_baseline_ai_days: 6
estimate_calibrated_ai_days: 3.6
source:
  - plans/audit/results/cicd_pipeline_vs_plans_drift_audit_2026_06_17.md (§ "Deferred exercise")
  - the 13 infrastructure_master cicd active plans + 11 cicd issue docs (inventory below)
  - codex/08-workflows/ci-cd-flow.md (the engineer SSOT being refreshed)
  - .github/workflows/*.yml (51 live workflows — ground truth)
---

> **🟢 IN-FLIGHT (slot interactive, 2026-06-18) — do NOT dispatch to a worker.** The owner is driving this to completion
> autonomously in one session (`/autonomous`). The coarse phase todos below are flipped as each phase ships; the 4 new
> themed plans are born populated at Phase 2, so their granular todos are correct from creation.

# CI/CD docs + diagram refresh, then plan/issue consolidation — 2026-06-18

**Trigger fired (operator 2026-06-18):** D1/D10 (uv frozen-lock — slot-3, `uv_lock_frozen_model_contradiction` now
`status: decided / 0-open`; `dependency_promotion` uv phases landed) is DONE; the other live agents are on
data-pipeline/strategy (disjoint surface). The gated docs+consolidation exercise from the drift audit is now GO.

**Mission.** The live CI/CD pipeline is healthy but the DOCS + PLAN LAYER lag it badly: the engineer SSOT
`ci-cd-flow.md` teaches a retired model in places, 51 workflows are impossible to grasp top-down, and ~119 open items
are scattered across 18 long plans/issues (one is **5224 lines / 284 done / 32 open**). Fix in 3 phases: **(1) document
the final stable shape into codex + a top-level diagram + an auto-generated workflow catalog; (2) consolidate the
scattered open work into 4 lean themed plans pointing at the refreshed codex; (3) archive the originals per the 5-step
ritual with the zero-item-dropped invariant.** Docs FIRST so the design rationale is harvested into codex before the
plans are archived.

---

## Authoritative inventory (measured 2026-06-18, post-FF-pull)

`OPEN`/`DONE` = `- [ ]`/`- [x]` checkbox counts. Disposition per the scoping decision below.

### Active plans

| Plan                                          | epic           | OPEN | DONE | LINES | Disposition                                         |
| --------------------------------------------- | -------------- | ---- | ---- | ----- | --------------------------------------------------- |
| `cicd_contract_hardening`                     | infrastructure | 32   | 284  | 5224  | **CARVE + ARCHIVE** (the monster)                   |
| `ldr_trunk_promotion_decoupling`              | infrastructure | 4    | 19   | 331   | → `cicd_promotion_pipeline`                         |
| `ci_status_firestore_side_store`              | infrastructure | 9    | 10   | 231   | → `cicd_promotion_pipeline`                         |
| `ldr_tarball_auto_refresh`                    | infrastructure | 2    | 7    | 88    | → `cicd_promotion_pipeline`                         |
| `cloud_build_router_aws_parity`               | infrastructure | 6    | 4    | 136   | → `cicd_promotion_pipeline` (image)                 |
| `qg_commit_quality_boundary_and_slot_ff_push` | infrastructure | 5    | 70   | 817   | → `cicd_quality_gates`                              |
| `ci_local_qg_parity`                          | infrastructure | 1    | 11   | 149   | → `cicd_quality_gates`                              |
| `worktree_ldr_unification`                    | infrastructure | 4    | 14   | 221   | → `cicd_quality_gates`                              |
| `staging_clean_start_and_stale_pr_hygiene`    | infrastructure | 0    | 15   | 294   | **ARCHIVE** (0 open)                                |
| `ci_dashboard_deployment_ui`                  | observability  | 0    | 36   | 347   | **ARCHIVE** (0 open; gate `pw:L2`)                  |
| `fleet_git_health_orchestrator`               | orchestrator   | 3    | 12   | 179   | **STANDALONE** (cross-epic; fix D21)                |
| `test_fleet_image_builds_from_current_code`   | deployment     | 8    | 4    | 289   | **STANDALONE** (cross-epic, recent)                 |
| `dependency_promotion_range_pins`             | infrastructure | 8    | 34   | 748   | **STANDALONE** (slot-3 fresh; distinct dep concern) |

### Issue docs

| Issue                                         | OPEN | DONE | Disposition                                        |
| --------------------------------------------- | ---- | ---- | -------------------------------------------------- |
| `ci_pipeline_self_healing_gaps`               | 18   | 15   | → `cicd_release_machinery` (watchers/auto-recover) |
| `fleet_audit_triad_deferred_followups`        | 8    | 0    | → `cicd_sit_and_fleet`                             |
| `semver_version_bump_skip_ci_promotion_block` | 5    | 5    | → `cicd_release_machinery` (D22)                   |
| `cicd_workflow_sprawl_audit`                  | 5    | 11   | → `cicd_release_machinery` (D22/D24/D25)           |
| `ci_incident_findings`                        | 4    | 4    | → triage-split across the 4 (per topic)            |
| `gh_rate_budget_reduction`                    | 3    | 11   | → `cicd_release_machinery`                         |
| `promotion_queue_conflict_wall_pileup`        | 1    | 19   | → `cicd_promotion_pipeline`                        |
| `sit_uac_orphan_cap_stale_consumer_list`      | 1    | 3    | → `cicd_sit_and_fleet`                             |
| `dashboard_promotion_drain_visibility`        | 0    | 5    | **ARCHIVE** (0 open)                               |
| `gcp_cloudbuild_sibling_context_staging`      | 0    | 0    | **ARCHIVE** (shipped; D23)                         |
| `uv_lock_frozen_model_contradiction`          | 0    | 0    | **ARCHIVE** (`decided`; slot-3 uv landed)          |

**Totals:** ≈119 open items to preserve · 5 zero-open/decided to archive outright · 3 cross-epic standalone · 16
consolidate-then-archive.

---

## Scoping decisions (operator "grouping + scope sounds logical"; details decided here per autonomous rule 12f)

1. **In-scope for consolidation** = `infrastructure_master`-epic cicd pipeline machinery + the epic-less cicd issue
   docs. These collapse into 4 themed plans (all `parent_epic: infrastructure_master`, `assigned_vm: vm-cross-cutting`).
2. **Out-of-scope, left STANDALONE** (pulling them under infrastructure_master would mis-assign their VM/epic):
   - `fleet_git_health_orchestrator` (orchestrator_master) — fix D21 (`assigned_vm: vm-orchestrator`→`planning`); ref'd
     from codex.
   - `test_fleet_image_builds_from_current_code` (deployment_master) — image-build verification; recent (2026-06-17).
   - `dependency_promotion_range_pins` (infrastructure, but slot-3-fresh + a distinct dep-version concern, 8 non-uv
     open) — do not disturb a just-active plan; verify uv items flipped + reference from codex.
3. **Image-build story spans two homes by epic** (intentional): the infra router/parity items
   (`cloud_build_router_aws_parity`) consolidate into `cicd_promotion_pipeline`'s image-build tail; the deployment-epic
   `test_fleet_image_builds` stays standalone. Codex links both.

## 4-plan grouping (intent — exact item placement happens at Phase-2 triage)

| New plan (`*_2026_06_18`) | Theme                                                                     | Fed by (open-item sources)                                                                                   |
| ------------------------- | ------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| `cicd_promotion_pipeline` | commit→LDR→staging→SIT→main→image + ci_status SSOT                        | ldr_trunk, ci_status_firestore, ldr_tarball, promotion_queue, cloud_build_router, contract_hardening(subset) |
| `cicd_quality_gates`      | quickmerge + quality-gates.sh + local↔CI + worktree                      | qg_commit_boundary, ci_local_parity, worktree_ldr, contract_hardening(subset)                                |
| `cicd_release_machinery`  | semver/version/manifest + sprawl/templates + watchers/self-heal + gh-rate | semver_skip_ci, sprawl, gh_rate, self_healing_gaps, ci_incident, contract_hardening(subset)                  |
| `cicd_sit_and_fleet`      | SIT + fleet audit/re-audit + UAC orphan cap                               | sit_uac_orphan, fleet_audit_triad, contract_hardening(subset)                                                |

---

## Phases

- [ ] [DOCS] P1. **Phase 1 — document the current shape.** Refresh `codex/08-workflows/ci-cd-flow.md` to the as-built
      final pipeline (complete the D5–D9 partial pass); add a top-level mermaid (commit→LDR→staging→SIT→main→image, each
      node tagged with its workflow) via the existing `cicd-pipeline-definition.yaml`→`CI-CD-PIPELINE.svg` generator;
      add an **auto-generated workflow catalog**
      (`name | trigger | concurrency | stage | reads/writes |     fires-next`) emitted by a generator that parses the
      `.yml` files so it can't rot.
- [ ] [DOCS] P1. **Phase 2 — consolidate into the 4 themed plans** above, each carrying ONLY open items (triaged:
      still-real / shipped-unflipped→close / obsolete→close-with-reason), tight context, pointing at the Phase-1 codex
      SSOT. Zero open `- [ ]` silently dropped.
- [ ] [DOCS] P1. **Phase 3 — archive + repoint.** Archive the 16 consolidated originals + 5 zero-open/decided via the
      5-step ritual (`[unlock-plan]`, deferred-scan, banner, codex-alignment, CLAUDE.md repoint). Fix the 3 standalone
      plans' frontmatter (D21). Verify the orchestrator backlog re-derives cleanly from the 4 new plans.

---

## Progress Log (append-only — durable memory across context compression)

- **2026-06-18 (open):** Trigger fired. FF-pulled to current on LDR (0/0). Built the authoritative inventory above (119
  open / 18 in-scope docs / monster = `cicd_contract_hardening` 5224L). Confirmed `cloud_build_router` exists (keyword
  pass had missed it). Confirmed `vm-cross-cutting` valid (registry L265). uv issue is `decided/0-open` → archivable.
  Filed this tracking plan. **Next: Phase 1 — fan out Opus sub-agents to extract structured facts from the 51 workflow
  clusters, then synthesize the ci-cd-flow.md refresh + catalog generator.**
