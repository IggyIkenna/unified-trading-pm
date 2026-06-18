---
title: CI/CD docs + diagram refresh, then plan/issue consolidation
name: cicd_docs_and_consolidation_2026_06_18
parent_epic: infrastructure_master
assigned_vm: vm-cross-cutting
created: 2026-06-18
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

> **✅ COMPLETE (2026-06-18) — consolidation shipped; kept active as the provenance anchor the 19 archived banners point
> to.** The owner is driving this to completion autonomously in one session (`/autonomous`). The coarse phase todos
> below are flipped as each phase ships; the 4 new themed plans are born populated at Phase 2, so their granular todos
> are correct from creation.

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

- [x] ✅ [DOCS] P1. **Phase 1 — document the current shape.** Refresh `codex/08-workflows/ci-cd-flow.md` to the as-built
      final pipeline (complete the D5–D9 partial pass); add a top-level mermaid (commit→LDR→staging→SIT→main→image, each
      node tagged with its workflow) via the existing `cicd-pipeline-definition.yaml`→`CI-CD-PIPELINE.svg` generator;
      add an **auto-generated workflow catalog**
      (`name | trigger | concurrency | stage | reads/writes |     fires-next`) emitted by a generator that parses the
      `.yml` files so it can't rot.
- [x] ✅ [DOCS] P1. **Phase 2 — consolidate into the 4 themed plans** above, each carrying ONLY open items (triaged:
      still-real / shipped-unflipped→close / obsolete→close-with-reason), tight context, pointing at the Phase-1 codex
      SSOT. Zero open `- [ ]` silently dropped.
- [x] ✅ [DOCS] P1. **Phase 3 — archive + repoint.** Archive the 16 consolidated originals + 5 zero-open/decided via the
      5-step ritual (`[unlock-plan]`, deferred-scan, banner, codex-alignment, CLAUDE.md repoint). Fix the 3 standalone
      plans' frontmatter (D21). Verify the orchestrator backlog re-derives cleanly from the 4 new plans.

---

## Progress Log (append-only — durable memory across context compression)

- **2026-06-18 (open):** Trigger fired. FF-pulled to current on LDR (0/0). Built the authoritative inventory above (119
  open / 18 in-scope docs / monster = `cicd_contract_hardening` 5224L). Confirmed `cloud_build_router` exists (keyword
  pass had missed it). Confirmed `vm-cross-cutting` valid (registry L265). uv issue is `decided/0-open` → archivable.
  Filed this tracking plan.
- **2026-06-18 — Phase 1a/1b SHIPPED.** Fanned out 5 Opus sub-agents → ground-truth facts for all 51 workflows. Authored
  `scripts/generate-workflow-catalog.py` (parses the `.yml`, emits `docs/repo-management/CICD-WORKFLOW-CATALOG.md` — the
  auto-generated drill-down: 51 workflows × stage/trigger/concurrency/mutates/fires-next; can't rot). Gate lessons (cost
  2 fix cycles): the codex-compliance grep scans `scripts/` too → had to drop a `.get("cron", "")` empty-string fallback
  AND a `try/except ImportError` shim (fallback-import ratchet). Shipped via quickmerge → **PR #401** (PM Option-B →
  main, auto-merge). Content-sentinel correctly recognized the files survived a peer FF. **Next: Phase 1c (ci-cd-flow.md
  refresh + mermaid) + Phase 1d (rewrite the stale `cicd-pipeline-definition.yaml`).** ci-cd-flow.md reviewer returned a
  25-item refresh list (doc broadly as-built; 4 front sections wholesale-obsolete + retired vocab).

## Phase 2 working data — `cicd_contract_hardening` (monster) open-item triage

The 32 open checkboxes → 41 rows (lines 3204/3212/3219 pack 3 per-repo ruleset todos). **Flip-not-carry** (LIKELY-DONE):
#5, #10 (the LDR drain — blockers resolved 2026-06-09), #19 (uac xdist flake — siblings root-fixed). **Propose-close**
(STALE): #9 (Vercel-strip removes it), #14 (gate green, only operator ruleset-PATCH pends), #22 (self-declared
out-of-scope, data/features track). Buckets: promotion #3,5,10,20,21,27,29,31,35; quality-gates #1,2,8,19,23; release
#4,6,7,11,14,18,24,33,34,36,37,38,39,40,41; sit-fleet #9,12,13,15,16,17,22,25,26,28,30,32. Full table lives in the
sub-agent return (this session); the bucket assignment above is the carry-forward map for the 4 new plans.

## New drift findings from the Phase-1 workflow read (beyond audit D1–D25 — capture per Findings-Triage)

Surfaced while reading the 51 workflows; **route into the themed plans at Phase 2** (do NOT fix piecemeal mid-docs):

- **Cosmetic comment-vs-cron drift** (→ `cicd_release_machinery`, one "workflow doc-comment cadence cleanup" item):
  `cloud-build-failure-watcher.yml` header "every 15 min" vs cron `*/30`; `ci-status-reconciler.yml` "every 10 min" vs
  `*/15`; `ldr-ci-monitor.yml` "30-min tick" vs hourly; `publish-package.yml` self-labels "Reusable workflow" but has no
  `workflow_call`.
- **Telegram→Slack stale comments** (→ same cleanup item): `secret-health-check`, `cassette-drift-check`,
  `plan-notification`, `agent-audit`, `overnight-dead-man-switch`, `fix-approval-timeout`, `cold-storage-cleanup` carry
  "Telegram alert" comments / `send_telegram()` names though all post to Slack (Telegram retired 2026-06-02).
- **3 POSSIBLE-REAL-BUGS — verify before fix** (→ themed plans):
  1. `conflict-resolution-agent.yml` — a **duplicate `env:` key** in the dispatch step (the 2nd clobbers the 1st,
     dropping GH_PAT/REPO_NAME/PR_NUMBER). If real, the escalation dispatch fires with empty creds. (→
     promotion/release)
  2. `hotfix-mode.yml` — bare `git push` (no rebase-retry) inside the shared `manifest-update` concurrency group; can
     lose a non-fast-forward race that `update-repo-version.yml` (×5 retry) survives. (→ release)
  3. `rollout-action-ref.yml` — pins/commits `quality-gates.yml` (the **v1 filename**) while the live required check is
     `quality-gates-v2`; verify it isn't re-pinning a retired workflow file fleet-wide. (→ release)

---

## Completion report (2026-06-18) — exercise DONE

All three phases shipped autonomously in one session.

**Phase 1 — docs + diagram (codex is now the as-built SSOT):**

- `codex/08-workflows/ci-cd-flow.md` refreshed to the LDR-trunk model — added the canonical **mermaid** pipeline
  diagram + the catalog pointer; replaced the retired three-tier headline; fixed `workspace-qg`→v2, codex-as-repo,
  tab-mirror, the `--to-staging`/dep-branch worked example; collapsed the dead 2026-06-01 snapshot; added the 7-state
  ci_status lifecycle. (33bad466c)
- New **auto-generated drill-down** `docs/repo-management/CICD-WORKFLOW-CATALOG.md` (51 workflows ×
  stage/trigger/concurrency/mutates/fires-next) via `scripts/generate-workflow-catalog.py` — regenerable, can't rot.
  (PR#401 merged, v2-green on main)
- `cicd-pipeline-definition.yaml` (the rendered-SVG companion) rewritten from the 50-node dead-pipeline monster to a
  14-node as-built backbone. (6e7939cf0)

**Phase 2 — 4 lean themed plans (zero open items dropped):** `cicd_promotion_pipeline` (30) · `cicd_quality_gates` (15)
· `cicd_sit_and_fleet` (11) · `cicd_release_machinery` (42) = **98 active open items** consolidated from 16 sources,
each carrying provenance. Disposition rule: REAL→Open · likely-done→Verify-and-flip · stale→Closed-with-reason ·
AWS-parity→Deferred annex. Cross-source dups merged (monster #35 ≡ self_healing G10; monster #37–40 ≡ sprawl Tier-5; the
AR-lag dup). (bb94a23c6)

**Phase 3 — archive + repoint:** 19 originals archived (banner + status flip + `git mv`, `[unlock-plan]`); CLAUDE.md's 7
cicd SSOT pointers repointed off the archived plans onto the 4 themed plans + this tracker. Working tree clean; backlog
re-derives from the 4 new plans only. (67bc7deba / 8c506a127 / 70ccf39a5)

**Decisions made under autonomy (documented):**

- `fleet_audit_triad_deferred_followups` kept STANDALONE — cross-domain grab-bag (its `[DATA]` reprocess items are
  data-pipeline, not cicd).
- Cross-epic plans (`fleet_git_health` orchestrator · `test_fleet_image_builds` deployment · `dependency_promotion`
  slot-3-fresh) left standalone — consolidating them under `infrastructure_master` would mis-assign their VM/epic.
- `ci_dashboard_deployment_ui` NOT archived — 0 open but BLOCKED-PLAYWRIGHT (the UI `pw:L2` gate can't run in this
  slot).
- Custom-SVG path lean-rewritten, not retired — retiring would touch the shared `quality-gates.sh` gate template
  (fleet-rollout risk); the mermaid is canonical, the SVG a rendered companion.

**Residual (tracked, not dropped):** the 3 `[BUG?]` verify-then-fix items in `cicd_release_machinery`
(conflict-resolution-agent dup-env-key · hotfix-mode bare-push race · rollout-action-ref v1-filename) are real findings
from the workflow read, captured for a worker to verify. This tracker stays in `plans/active/` as the provenance anchor
the 19 archived banners reference.
