# PM Codex Drift Zero vs Other Alignment Plan — Diff and Merge Guide

**Purpose:** Compare pm_codex_drift_zero_architecture plan with other_alignment_plan.md for alignment, merge points, and
decisions.

---

## 1. Alignment (Same Direction)

| Area                       | PM Codex Plan                                         | Other Alignment Plan                | Verdict     |
| -------------------------- | ----------------------------------------------------- | ----------------------------------- | ----------- |
| **Manifest as SSOT**       | Phase 0: sync-manifest-versions (repository_dispatch) | Approach A + Phase 3: manifest sync | Same        |
| **PM → Codex → Code flow** | PM root, Codex reflects plans, Services implement     | Three layers; layered versioning    | Same        |
| **Drift enforceable**      | No merge without passing drift                        | Like a failing unit test            | Same        |
| **Plan-level tracking**    | plans/active/INDEX, plan incorporation                | plan_spec_current, spec_doc_version | Same intent |

---

## 2. Where to Merge

### 2.1 Manifest Sync

**Merge:** PM Codex Phase 0 is canonical. Other Phase 3 references it. No conflict.

### 2.2 Plan Headers

**Merge:** Add Other's plan header format (spec_doc, spec_doc_version) to PM Codex Phase 2. Add plan_spec_current check.

### 2.3 Codex Doc YAML Front-Matter

**Merge:** Add doc_version, codex_version to Codex per-service docs in Phase 0b or 3. Enables doc_version_match later.

### 2.4 Enforcement Script

**Merge:** Implement check-alignment-drift.py as validator or call from run_validators. Add in Phase 6. Covers
header/provenance; validators cover architectural standards.

---

## 3. Decisions Required

### 3.1 Per-File Headers vs Validator-Only

- **A) Validator-only:** PM Codex as-is. No per-file headers. Simpler.
- **B) Headers-only:** Other's # codex-ref: per file. Precise provenance.
- **C) Hybrid:** Both. Validators + headers. Maximum coverage.

**Recommendation:** Start with A. Add B/C later if file-level provenance needed.

### 3.2 doc_version Format

Semantic (1.2) vs date vs integer. Recommend semantic if YAML adopted.

### 3.3 Enforcement Strictness

Block on P0/P1. For doc_version_match: start with block; add staleness threshold if friction.

### 3.4 Retroactive Headers

If headers adopted: only files touched going forward initially.

---

## 4. Good Practices to Adopt

**From Other → PM Codex:** Scope rule (which files get headers), doc_version bumping rules, layered table, open
questions, time estimates.

**From PM Codex → Other:** Codex merge gate, PM triggers Codex, CI clone, cleanup, dependency cascade.

---

## 5. Consolidated Phase Order

0: Manifest sync | 0b: Cleanup + indexes | 1: Manifest validation | 2: Active plans + plan headers | 3: Codex merge
gate + YAML | 4: PM triggers Codex | 5: CI clone | 6: Per-repo drift + check-alignment-drift | 7: Diff checker | 8
(optional): Per-file headers if B/C chosen.

---

## 6. Summary

**Merge:** Manifest sync, plan headers, codex YAML, check-alignment-drift as validator. **Decide:** Per-file headers
(A/B/C), doc_version format, strictness, retroactive. **Recommendation:** PM Codex primary. Fold in Other's plan headers
and YAML. Defer per-file headers. Update Other to reference PM Codex or archive.
