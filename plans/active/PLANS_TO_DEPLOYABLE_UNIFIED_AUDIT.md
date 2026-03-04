# Plans → Code → Tested → Deployable: Unified Audit and Plan Alignment

**Status:** Proposal
**Created:** 2026-03-04
**Purpose:** Unify PM Codex Drift Zero, Other Alignment, and deployment topology into a single coherent flow. Add two stages (Tested, Deployable) so plans become code, then tested, then deployable. Reference audit prompt and checklists. Document where plans diverge, align, and decide.

**SSOT:** This plan references and consolidates:
- pm_codex_drift_zero_architecture_2d72151d.plan.md (PM Codex plan)
- other_alignment_plan.md (Other Alignment)
- PM_CODEX_VS_OTHER_ALIGNMENT_DIFF.md (Diff analysis)
- trading-system-audit-prompt.md (Audit prompt)
- deployment-service/configs/ (runtime topology, checklists)

---

## 1. Extended Pipeline: Plans → Code → Tested → Deployable

**Current:** Plans → Codex → Code (implemented)

**Enhancement:** Add two stages so the full pipeline is:

PM (plans, manifest) → Codex (specs) → Code (implemented) → Tested (quality gates + integration tests pass) → Deployable (checklist complete, actually deploys)

| Stage | What it means | Gate |
|-------|---------------|------|
| Plans | PM owns manifest, active plans index, topology | Manifest validation; plan incorporation |
| Codex | Docs reflect post-plan architecture | Codex merge gate |
| Code | Services implement against Codex | Per-repo drift (validators); quality gates |
| Tested | Code runs; quality gates pass; integration tests pass | quality-gates.sh; pytest; CI green |
| Deployable | Passes deployment checklist; data catalogue; recovery; security | Checklist YAML; runtime-topology; audit |

**Deployable** is different from working code: data availability verified, deployment stages passed, data catalogue filled, recovery documented, security audit trails in place. The audit prompt can then give A+ because everything is documented and verifiable.

---

## 2. Deployment Topology and Checklists

**SSOT:** deployment-service/configs/ — runtime-topology, RUNTIME_TOPOLOGY_DECISIONS.md, RUNTIME_DEPLOYMENT_TOPOLOGY_DAG.svg

**Modes:** Live, Batch (per-service checklists)

**Checklist phases (from checklist.template.service.yaml):**

| Phase | Covers |
|-------|--------|
| Phase 1 | Repository Foundation (repo, deps, config, logging, error handling, secrets, Dockerfile) |
| Phase 2 | Testing & Quality (unit tests, E2E, quality gates, pre-commit, Cloud Build) |
| Phase 3 | Deployment Infrastructure (sharding, CLI, GCS, Terraform, buckets, deploy CLI) |
| Phase 4 | Local Validation (code runs locally, dependency data, schema, timestamp alignment) |
| Phase 5 | Production Deployment (image builds, deployment runs, data completeness) |
| Phase 6 | Documentation (README, architecture, schema, GCS paths, error handling, config) |
| Phase 7 | Data Catalogue (data-catalogue.{service}.yaml enumerates shards) |

**Additional checklist areas (per user request):** data availability, passing deployment stages, data catalogue, filling empty gaps, recovery processes, security audit trails.

---

## 3. Audit Prompt Integration

**SSOT:** unified-trading-pm/plans/active/trading-system-audit-prompt.md

**Purpose:** When an agent runs the audit, it evaluates the workspace against institutional-grade standards. If the pipeline is complete and all checklists are filled, the audit finds no issues — A+.

---

## 4. Plan Cross-Reference: Divergence, Unison, Decisions

### 4.1 PM Codex Drift Zero Architecture
Scope: Manifest sync, cleanup, active plans, Codex merge gate, PM triggers Codex, CI clone, per-repo drift, diff checker.
Unison with Other: Manifest sync, plan-level tracking, drift enforcement.
Divergence: PM Codex uses validators; no per-file headers.

### 4.2 Other Alignment Plan
Scope: Version tracking at repo, doc, file, plan levels. Approach A (manifest) + Approach B (per-file headers).
Unison with PM Codex: Manifest as SSOT, plan headers, drift enforcement.
Divergence: Other adds per-file codex-ref and doc_version; PM Codex does not.

### 4.3 PM_CODEX_VS_OTHER_ALIGNMENT_DIFF
Merge: Manifest sync, plan headers, codex YAML front-matter, check-alignment-drift as validator.
Decisions: Per-file headers (A/B/C), doc_version format, enforcement strictness, retroactive coverage.

### 4.4 This Plan (Plans → Deployable)
Additions: Two stages (Tested, Deployable); checklist enhancements; audit prompt as final gate.

---

## 5. Decisions That Need to Be Made

| # | Decision | Options |
|---|----------|---------|
| 1 | Per-file headers | A) Validator-only, B) Headers-only, C) Hybrid |
| 2 | doc_version format | Semantic vs date vs integer |
| 3 | Enforcement strictness | Block vs warn; staleness threshold |
| 4 | Retroactive headers | All files vs touched-only |
| 5 | Checklist enhancements | Add items for data availability, gaps, recovery, security |
| 6 | Tested vs Deployable gate | Two gates: Tested = quality gates pass; Deployable = checklist complete |

---

## 6. Consolidated Phase Order (Unified)

Phase 0: Manifest sync | Phase 0b: Cleanup + SSOT indexes | Phase 1: Manifest validation | Phase 2: Active plans index + plan headers | Phase 3: Codex merge gate | Phase 4: PM triggers Codex | Phase 5: CI clone | Phase 6: Per-repo drift | Phase 7: Diff checker refactor | Phase 8: Per-file headers (optional) | Phase 9: **Tested gate** | Phase 10: **Deployable gate** | Phase 11: **Audit** — trading-system-audit-prompt.md run; target A+

---

## 7. Potential Enhancements (From User)

1. Plans → Code → Tested → Deployable — Four stages; Tested and Deployable distinct from working code.
2. Deployment topology — Live, batch; reference runtime-topology, RUNTIME_TOPOLOGY_DECISIONS.
3. Checklists — Data availability, deployment stages, data catalogue, filling gaps, recovery, security audit trails.
4. Audit prompt — Agent runs audit; A+ when everything is documented and verifiable.
5. Unified plan — One plan referencing all others; divergence, unison, decisions documented.

---

## 8. Next Steps

1. Merge PM Codex and Other per PM_CODEX_VS_OTHER_ALIGNMENT_DIFF.
2. Add checklist items for data availability, gap-filling, recovery, security audit trail.
3. Define Tested gate — explicit criteria (quality gates + integration tests).
4. Define Deployable gate — checklist phases 1–7 complete; new items if added.
5. Wire audit prompt — Ensure audit runs after Deployable; document in plan.
6. Update trading-system-audit-prompt.md — Add reference to deployment-service.
7. Archive or consolidate — Other plans reference this as the unified plan; avoid duplication.
