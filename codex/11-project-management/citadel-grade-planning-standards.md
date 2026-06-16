---
scope: [engineer, admin]
---

# Citadel-Grade Planning Standards

> **CLAUDE.md anchor**: "Citadel-Grade Planning Standards".
>
> Workspace-wide planning requirements for all plans in `plans/active/`, `plans/epics/`, and `plans/audit/`. These
> standards ensure plans are thorough, parallelisable, and production-ready.

## The Nine Requirements

Every plan MUST include:

### 1. Pre-Audit Before Execution

Workspace-wide grep for every removed/renamed symbol; embed manifest. No plan ships without pre-auditing downstream
consumers.

### 2. Phased Execution DAG with Explicit Dependencies

QG gates between phases. Clear phase ordering with explicit dependencies. No ambiguous "then do X" steps.

### 3. No Technical Debt

Clean breaks, no shims. Every refactor/migration leaves the codebase in a better state than before.

### 4. Parallelization

Independent items marked PARALLEL. Optimise for agent slot utilisation.

### 5. Success Criteria per Phase

QG/basedpyright/ruff + test + deployment gates. Each phase MUST have a verifiable completion criterion.

### 6. Downstream Consumer Updates

Pre-audit EVERY workspace consumer for removed/renamed public symbols. Include consumer update phases.

### 7. Single Source of Truth

Types in UAC or `unified_api_contracts.internal`. No local type definitions that duplicate UAC.

### 8. Foundation-Completion-Gate Discipline

No plan ships items in layer N+1 before layer N is GREEN-audited + manifest-divergence = 0 for affected asset_groups.
Parallel-up across asset_groups within a layer is encouraged; parallel-up across layers is review-blocking.

Full layer table + application rules + anti-patterns:
`codex/11-project-management/foundation-completion-gate-discipline.md`.

Master tracker: `plans/active/issues/mega_audit_and_plan_beefup_progression_2026_05_20.md`.

### 9. Issue-Doc Lifecycle Discipline

Issue docs in `plans/active/issues/` exist to surface UNACKED work. Once acked (into a plan / shipped code /
out-of-scope with named successor), they archive immediately.

Banner-marked-in-`active/issues/` is a transitional convenience, NOT a permanent state. "Stays until parent closes"
lifecycles are dual-tracking and review-blocking.

State machine + audit recipe + anti-patterns: `codex/11-project-management/issue-doc-lifecycle.md`.

## Plan Review Checklist

Before approving any plan, verify:

- [ ] Pre-audit section lists every removed/renamed symbol + workspace grep results
- [ ] Phase DAG is explicit with numbered dependencies
- [ ] No "TODO refactor later" or temporary shims in final state
- [ ] PARALLEL tags on independent items for slot optimisation
- [ ] Each phase has testable completion criteria
- [ ] Consumer audit covers ALL workspace importers of changed APIs
- [ ] No local types that duplicate UAC domains
- [ ] Layer ordering respects foundation-completion-gate
- [ ] No orphan issue docs created without clear archival path

## Anti-Patterns (review-blocking)

- **"We'll fix the tech debt in a follow-up"** — the plan must leave clean state
- **"Phases 1-3 can run in any order"** — specify the DAG explicitly
- **"Obviously parallel items"** — mark with PARALLEL tag for slot assignment
- **"Success = no errors"** — specify the verification recipe
- **"Consumer impact TBD"** — audit before execution, not after
- **"Quick local type for now"** — use UAC or unified_api_contracts.internal
- **"Layer N+1 is just cleanup"** — layer ordering is HARD; no exceptions

## Composes With

- `plans/PLAN_FORMAT.md` — checkbox syntax and frontmatter requirements
- `codex/11-project-management/foundation-completion-gate-discipline.md` — layer ordering rules
- `codex/11-project-management/issue-doc-lifecycle.md` — issue doc state machine
- `codex/11-project-management/active-plan-inventory-tracker.md` — plan dashboard and orphan detection
