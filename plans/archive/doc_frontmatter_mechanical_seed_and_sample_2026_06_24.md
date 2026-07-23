---
doc_type: plan
title: Mechanical frontmatter auto-seed + 5-per-doc_type sample (W3, cheap pass)
summary:
  The cheap/mechanical frontmatter pass — a docspec-driven auto-seed that fills only the derivable universal-core +
  per-type fields (leaving summary/tags present-but-empty), applied breadth-first as a 5-per-doc_type in-place sample
  for operator review, ahead of the full rollout.
status: complete
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [frontmatter, docspec, seed, backfill, rag, agent-operating-framework, sample]
related: [agent_operating_framework_master, doc_frontmatter_schema_and_validator_2026_06_24]
created: 2026-06-24
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2.4
last_updated: 2026-07-02
archived: 2026-07-02
locked_by: NA
locked_since: NA
supersedes:
superseded_by:
depends_on: [doc_frontmatter_schema_and_validator_2026_06_24]
source:
drift_direction: advance-code
---

## Deferred work — migrated to:

**None** — successor: not applicable. Plan archived as 100% completed (no open `- [ ]` items at archive time). Any
incidental DEFERRED / post-cutover / out-of-scope tokens in the body are historical context, not unfinished work.

# Mechanical frontmatter auto-seed + 5-per-doc_type sample (W3, cheap pass)

> **🗄️ ARCHIVED 2026-07-02 (operator-directed) — COMPLETE; every deferred todo since done elsewhere or owned
> elsewhere.** The shipped scope (seeder + validator + 35-doc sample) verified at archival (`scripts/docs/` all
> present). The deferred worklist resolved: full rollout + status-normalize + cursor-rules shipped via the archived
> `frontmatter_full_corpus_coverage_2026_06_30.md`; agent-role charters via `agent-orchestrator@acbf930`; the
> `summary`/`tags` content pass + the single comprehensive blocking gate are owned by the live
> `frontmatter_content_pass_and_gate_consolidation_2026_06_30.md`. Per-item evidence on each todo below.

> **W3** of `agent_operating_framework_master`, scoped per operator (2026-06-24) to the **cheap/mechanical** step,
> applied **breadth-first across all doc types** as a **5-per-doc_type sample** so the operator can review the shape
> before the full rollout. **Deferred (operator):** the full rollout to every doc · the `summary`/`tags` content pass ·
> status normalization · the QG-gate enforcement (W5) · validator-green over the whole corpus.

## What this is

`docspec` (W2) defines the schema; this plan adds `seed_frontmatter.py` — a **mechanical** auto-seed that fills only the
**derivable** universal-core + per-type fields and leaves the expensive content fields (`summary`, `tags`)
present-but-empty for the later content pass. Run breadth-first over a 5-per-doc_type sample, in place, for review.

## Shipped

- **`scripts/docs/seed_frontmatter.py`** — derives `doc_type` (path), `title` (H1/`name`), `nature` (per-type default),
  `asset_group` (from `parent_epic`), `stage` (`[meta]` default), `repos` (body grep vs manifest), `scope`
  (`[engineer, admin]` default), `created` (git first-commit), and keeps existing per-type fields; `summary`/`tags`
  present-but-empty. Modes: `--sample` (non-destructive → scratchpad), `--apply PATH…`, `--apply-sample` (in place,
  git-dirty + cross-repo guarded).
- **`scripts/docs/docspec.py` + `test_docspec.py`** (W2 Phase 2) — validator + 15 unit tests (3-state logic, enums,
  precedence, conditional, exemptions). Re-used here to validate every seeded doc.
- **5-per-doc_type sample applied IN PLACE** — **35 PM docs** (5 each across `plan`/`epic`/`issue`/`audit-result`/
  `audit-instruction`/`codex-ssot`/`codex-runbook`), **all `docspec` hard=0**. The remaining softs are the deferred
  worklist (`summary`/`tags` content + status-normalization).

## Decisions made this pass (operator-confirmed or within documented intent)

- **issue `status: active` → `open`** (operator 2026-06-24) — the seed maps it; issue status enum is
  `open/blocked/resolved/false-positive/superseded`.
- **`scope` vs `audited_scope` collision** — `scope` is the AUDIENCE axis (a list, `engineer/admin/…`); audit docs
  historically used `scope` for prose COVERAGE, which the seed rehomes to **`audited_scope`** and resets `scope` to the
  audience default. (Within documented intent — `audited_scope` already existed on audit-result.)
- **status mismatch = SOFT during the gateless soak** — the corpus uses 20+ ad-hoc status values; normalizing them is a
  CONTENT decision (deferred), so a status-not-in-enum is a SOFT "normalize" warning, not HARD. The enum is the target
  the content pass converges to.
- **Exemptions broadened** — `README.md`/`INDEX.md`/`*INDEX*`/`ROADMAP`/`PLAN_FORMAT.md` + ledgers (`_*`, e.g.
  `_agent_pings.md`) carry no frontmatter (data, not docs).
- **plan `assigned_vm` derived from `parent_epic`** when missing (operator overrides per D2 precedence); epic / no-epic
  → `NA` (= not dispatched until set).

## Deferred (NOT in this pass — operator-scoped) — closure review 2026-07-02: all done elsewhere / owned elsewhere

- [x] [SCRIPT] P1. **Full rollout** — `--apply` the mechanical seed to ALL docs of every type (not just the 5-per-type
      sample), in collision-aware batches. ✅ DONE ELSEWHERE — `plans/active` top-level via
      `plans_active_frontmatter_mechanical_rollout_2026_06_27` (unified-trading-pm@4d3083639, 102 docs); the rest of the
      corpus via `frontmatter_full_corpus_coverage_2026_06_30` (archived complete). Verified at archival: issues 77/77 ·
      epics 27/28 · audit-results 51/52 · instructions 20/21 · codex 807/842 carry `doc_type` — every gap is an exempt
      class (READMEs ×35, `_template`, index/ledger files).
- [x] [DOCS] P1. **`summary` + `tags` content pass** — ✅ MIGRATED (owned by the live
      `frontmatter_content_pass_and_gate_consolidation_2026_06_30.md`, explicit P3 todos for
      `summary`/`authoritative_for`/`tags`).
- [x] [DOCS] P2. **status normalization** — ✅ DONE ELSEWHERE — enum-normalize shipped per-tree via
      `frontmatter_full_corpus_coverage_2026_06_30` (archived). Verified at archival: 1 residual frontmatter value in
      `plans/active` (`mtds_file_size_refactor_2026_06_08.md` `status: deferred`) normalized to `paused` in this
      archival commit; the other odd `status:` greps are body text, not frontmatter.
- [x] [DOCS] P2. **agent-role (5) + cursor-rule** — ✅ DONE ELSEWHERE — all agent-role boot prompts schema-ified in
      `agent-orchestrator@acbf930` (role/model/thinking/lifecycle rows; W6/W9 charter work); cursor-rules got
      `doc_type: cursor-rule` (179 `.mdc`) via `frontmatter_full_corpus_coverage_2026_06_30`. AO-repo docspec
      enforcement is a remaining todo owned by `frontmatter_content_pass_and_gate_consolidation_2026_06_30.md`.
- [x] [SCRIPT] P2. **Validator-green over the whole corpus** + wiring `docspec` into `plan-hygiene` (report-only). ✅
      DONE/OWNED ELSEWHERE — per-tree validator-green gates shipped with `frontmatter_full_corpus_coverage_2026_06_30`;
      coverage is QG-enforced today via `scripts/quality_gates/check_docspec_coverage.py`; the comprehensive
      docspec-backed blocking gate is owned by `frontmatter_content_pass_and_gate_consolidation_2026_06_30.md`.
- [x] [SCRIPT] P3. **QG gate enforcement (W5)** — `check_*_frontmatter` warn→error. ✅ MIGRATED — enforce-LAST
      convergence to ONE blocking check is the explicit scope of
      `frontmatter_content_pass_and_gate_consolidation_2026_06_30.md` (which also retires `check_docspec_coverage.py`
      once live).

## Success criteria

- `seed_frontmatter.py` deterministically fills the mechanical fields + leaves content fields present-but-empty.
- The 5-per-doc_type sample is applied in place and every seeded doc is `docspec` hard=0.
- The deferred work is captured as todos above (no silent deferral); no QG enforcement landed.

## Codex SSOT updates

- `/codex/11-project-management/doc-frontmatter-schema.md` — refined this pass (exemptions, `scope`/`audited_scope`,
  status-soft-during-soak, issue `open`).

## Progress Log

- 2026-06-24: Created. Shipped `seed_frontmatter.py` + the W2 `docspec` validator (15 tests). Applied the
  **5-per-doc_type sample in place to 35 PM docs**, all `docspec` hard=0. Decisions: issue→open · scope/audited_scope
  collision rehome · status-mismatch SOFT during soak · broadened exemptions (ledgers/index) · plan `assigned_vm` from
  epic. agent-role + cursor-rule + full rollout + summary/tags + QG gate all DEFERRED (todos above). Shipped via qg →
  quickmerge.
