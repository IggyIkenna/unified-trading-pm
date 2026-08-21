---
doc_type: plan
title: Strict Basedpyright Compliance Plan
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: []
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-05'
overview: Achieve typeCheckingMode strict and reportAny error across all Python repos. No dict[str, Any] in public API. Run basedpyright on source_dir only (never .).
todos:
- {id: pyrightconfig-strict, content: 'Verify pyrightconfig.json — typeCheckingMode strict, reportAny error', status: done}
- {id: run-basedpyright, content: Run timeout 120 basedpyright <source_dir>/ (never basedpyright .), status: done}
- {id: fix-type-ignores, content: 'Fix or document every # type: ignore in QUALITY_GATE_BYPASS_AUDIT.md. THRESHOLD: T0–T3 libraries: zero # type: ignore allowed in production source (any bypass is an architectural violation — fix the root cause per no-type-any-use-specific.mdc). Services: each # type: ignore must have a documented entry in QUALITY_GATE_BYPASS_AUDIT.md with: file:line, reason, and owner. GATE: T0–T3 repos have rg ''# type: ignore'' returning 0 matches in production source; services have QUALITY_GATE_BYPASS_AUDIT.md with entries for every # type: ignore hit.', status: done}
- {id: remove-any, content: 'Remove Any; use typed alternatives (TypedDict, Protocol, dict[str, X]). GATE: rg '': Any$|-> Any$|\[Any\]'' --type py --glob ''!.venv*'' --glob ''!tests'' in public API files (top-level __init__.py and public interface modules) returns 0 matches for all T0–T3 repos.', status: done}
- {id: tier-order, content: 'T0 first → T1 → T2 → T3 → services. GATE: each tier complete before next begins. Tier complete = basedpyright exits 0 on source_dir + reportAny: error + zero # type: ignore in T0–T3 production source. Record completion date per repo in workspace-manifest.json ci_status field.', status: done}
isProject: false
---

# Strict Basedpyright Compliance Plan

**Order:** 4 (see master_pre_deployment_plan_chain.md) **SSOT:** trading_system_audit_prompt.md §6.5, §8.6, §9.7, §9.10

---

## Blockers

| Blocker                            | Type          | Specific Dependency                                                                           | Resolution                                                                                                                          |
| ---------------------------------- | ------------- | --------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| Phase 0 baseline not established   | `[DONE]`      | [phase0_standards_enforcement.md](phase0_standards_enforcement.md) § todo `p0-gate-check`     | Phase 0 complete (2026-03-05). All repos have basedpyright strict configs; all bypasses documented in QUALITY_GATE_BYPASS_AUDIT.md. |
| Any violations in public T0/T1 API | `[PLAN_TODO]` | [phase2_library_tier_hardening.md](phase2_library_tier_hardening.md) § todo `t0-code-rewrite` | T0 Any violations must be fixed during T0 STEP C before T1 compliance can be achieved; run in tier order T0→T1→T2→T3→services       |

---

## Requirements

- typeCheckingMode: "strict" in pyrightconfig.json
- reportAny: "error"
- No dict[str, Any] in public API
- Run timeout 120 basedpyright / (never basedpyright .)
- Exclude build/, dist/, .venv/

> **Safe Invocation (B3):** Always run `run_timeout 120 basedpyright <source_dir>/` (e.g.,
> `timeout 120 basedpyright execution_service/`). NEVER run `basedpyright .` from workspace root or any directory
> without an explicit source dir and timeout. Omitting the source dir causes basedpyright to scan all files including
> venvs; omitting timeout causes hangs on large repos.

---

## Per-Repo Actions

1. Verify pyrightconfig.json: strict + reportAny error
2. Run basedpyright on source_dir only
3. Fix or document every # type: ignore in QUALITY_GATE_BYPASS_AUDIT.md
4. Remove Any; use typed alternatives

---

## Cross-Service Type Imports and reportAny

**Cross-service type imports and reportAny:** When fixing cross-service type imports (e.g., RC-12: ml-inference
importing from ml-training-service), the fix must place shared types in protocol libraries:

- Internal service-to-service schemas → `unified-internal-contracts` (T0, UIC)
- Domain interfaces and protocols → appropriate T2 library (UML for ML, UMI for market, etc.)
- Types must be `Protocol`, `TypedDict`, or concrete Pydantic models — never `Any` or `dict[str, Any]`
- `reportAny: error` applies to ALL code, including types imported from other packages
- If an imported type resolves to Any, fix the source library — do not suppress with `# type: ignore`

---

## Execution Order

T0 first → T1 → T2 → T3 → services.
