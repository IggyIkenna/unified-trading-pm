---
doc_type: plan
title: Phase 0 — System-Wide Standards Enforcement
summary: 'Establish a verified baseline across all repos before any hardening work begins.

  Every repo must meet minimum standards (coverage, file/function/method/class size,

  Python version, strict type checking, no os.getenv, cloud-agnostic I/O, no GCS* protocol names,

  no cross-service imports). Failures are fixed immediately (if trivial) or tracked in

  QUALITY_GATE_BYPASS_AUDIT.md. Phase 0 blocks Phase 1, Phase 2, and Phase 3 — must pass

  before any hardening work starts. Run in tier order (T0 first), parallel within each tier.'
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-api-contracts, unified-trading-library]
scope: [engineer, admin]
tags: []
related: []
created: "2026-03-05"
todos:
  - {
      id: p0-t0-parallel,
      content:
        "Run all 5 checks (quality-gates.sh, basedpyright, os.getenv scan, Any scan, cloud-agnostic scan) on all 6 T0
        repos in parallel: unified-api-contracts, unified-internal-contracts, unified-cloud-interface,
        unified-events-interface, unified-reference-data-interface, matching-engine-library. Fix trivial violations
        immediately; document bypasses.",
      status: done,
    }
  - {
      id: p0-t1-parallel,
      content:
        "Run all 5 checks on all 4 T1 repos in parallel (after T0 passes): unified-config-interface,
        unified-trading-library, execution-algo-library, unified-feature-calculator-library. Fix trivial violations
        immediately; document bypasses.",
      status: done,
    }
  - {
      id: p0-t2-parallel,
      content:
        "Run all 5 checks on all T2 repos in parallel (after T1 passes): unified-market-interface,
        unified-trade-execution-interface, unified-ml-interface, unified-position-interface,
        unified-defi-execution-interface, unified-sports-execution-interface. Fix trivial violations immediately;
        document bypasses.",
      status: done,
    }
  - {
      id: p0-t3,
      content:
        "Run all 5 checks on T3 repo: unified-domain-client. Fix trivial violations immediately; document bypasses.",
      status: done,
    }
  - {
      id: p0-services-batch1,
      content: "Run all 5 checks on services batch 1 (matches Phase 3 DAG order, batch 1). Fix or document.",
      status: done,
    }
  - { id: p0-services-batch2, content: Run all 5 checks on services batch 2. Fix or document., status: done }
  - { id: p0-services-batch3, content: Run all 5 checks on services batch 3. Fix or document., status: done }
  - { id: p0-services-batch4, content: Run all 5 checks on services batch 4. Fix or document., status: done }
  - {
      id: p0-bypass-audit-update,
      content:
        "Ensure QUALITY_GATE_BYPASS_AUDIT.md is up to date in every repo that required a bypass. Gate: zero undocumented
        suppressions.",
      status: done,
    }
  - {
      id: p0-gate-check,
      content:
        'Final gate check: all repos have quality-gates.sh passing (or bypass documented), basedpyright strict passing
        (or bypass documented), zero os.getenv in production source, zero Any in public API (or bypass documented),
        pyproject.toml has requires-python = ">=3.13,<3.14", QUALITY_GATE_BYPASS_AUDIT.md up to date.',
      status: done,
    }
isProject: true
---

# Phase 0: System-Wide Standards Enforcement

**Day:** 0 (before Phase 1 begins) **Scope:** All repos (T0–T3 libraries, services, UIs) **Blocks:** Phase 1, Phase 2,
Phase 3 — must pass before any hardening work starts **Owner:** Parallel agents (one per tier group)

## Purpose

Establish a verified baseline across all repos before any hardening work begins. Every repo must meet minimum standards.
Failures are documented and either fixed immediately (if trivial) or tracked in QUALITY_GATE_BYPASS_AUDIT.md (only for
genuinely unavoidable suppressions).

## Standards (All Blocking)

| Standard                | Rule                                                                                  | Enforcement         |
| ----------------------- | ------------------------------------------------------------------------------------- | ------------------- |
| Coverage                | MIN_COVERAGE=70 (libraries, services); 50 (infra/docs)                                | quality-gates.sh    |
| File size               | MAX_FILE_LINES=900 (warn at 700)                                                      | quality-gates.sh    |
| Function size           | MAX_FUNCTION_LINES=100                                                                | quality-gates.sh    |
| Method size             | MAX_METHOD_LINES=50                                                                   | quality-gates.sh    |
| Class size              | MAX_CLASS_LINES=500                                                                   | quality-gates.sh    |
| Python version          | `>=3.13,<3.14` in all pyproject.toml                                                  | quality-gates.sh    |
| Type checking           | `typeCheckingMode: strict`, `reportAny: error` in pyrightconfig.json                  | basedpyright        |
| No Any types            | No `Any`, `dict[str, Any]`, or `-> Any` in public API                                 | ruff + basedpyright |
| No os.getenv            | Zero `os.getenv()`, `os.environ.get()`, `os.environ[KEY]` in production source        | ruff (custom rule)  |
| Cloud agnostic          | All cloud I/O via `get_storage_client()`, `get_secret_client()`, `get_queue_client()` | audit script        |
| No GCS\* protocol names | Interface/protocol classes must use `Cloud`_ not `Gcs`_                               | code review         |
| Cross-service imports   | Shared types must live in T0/T2 libs (UIC, UML, etc.), not imported between services  | basedpyright        |

## Per-Repo Checklist

For each repo, run in order:

```bash
# 1. Verify Python version in pyproject.toml
grep 'requires-python' pyproject.toml  # must be ">=3.13,<3.14"

# 2. Run quality gates (coverage, file size, function size)
bash scripts/quality-gates.sh --no-fix

# 3. Strict type checking
timeout 120 basedpyright <source_dir>/

# 4. Scan for os.getenv violations
rg "os\.getenv|os\.environ" --type py --glob '!.venv*' --glob '!tests' <source_dir>/

# 5. Scan for Any-type violations
rg ": Any|-> Any|\[Any\]" --type py --glob '!.venv*' <source_dir>/

# 6. Scan for non-cloud-agnostic patterns (direct GCP/AWS imports in non-provider files)
rg "from google\.cloud|import boto3" --type py --glob '!.venv*' --glob '!providers' <source_dir>/
```

## Execution Order

Run in tier order (T0 first), parallel within each tier:

### Tier 0 (L2) — 6 repos in parallel

- unified-api-contracts
- unified-internal-contracts
- unified-cloud-interface
- unified-events-interface
- unified-reference-data-interface
- matching-engine-library

### Tier 1 (L3–L4) — 4 repos in parallel

- unified-config-interface
- unified-trading-library
- execution-algo-library
- unified-feature-calculator-library

### Tier 2 (L5–L6) — 7 repos in parallel

- unified-market-interface
- unified-trade-execution-interface
- unified-ml-interface
- unified-position-interface
- unified-defi-execution-interface
- unified-sports-execution-interface
- unified-feature-calculator-library (if T2)

### Tier 3 (L6) — 1 repo

- unified-domain-client

### Services (L7–L10) — 4 batches matching Phase 3 DAG order

Run same 5 checks per service; prioritise high-violation repos first.

## Failure Protocol

| Violation type       | Action                                                                            |
| -------------------- | --------------------------------------------------------------------------------- |
| os.getenv in source  | Fix immediately — replace with UnifiedCloudConfig or get_secret_client()          |
| Any in public API    | Fix immediately — use TypedDict/Protocol                                          |
| File >900L           | Split by SRP — separate commit per file                                           |
| Coverage <70%        | Add tests OR document in QUALITY_GATE_BYPASS_AUDIT.md with justification          |
| Python <3.13         | Update pyproject.toml; fix any syntax incompatibilities                           |
| reportAny violations | Fix type — no # type: ignore to hide Any                                          |
| GCS\* protocol name  | Rename to Cloud\* (protocol/interface only; providers/gcp.py keeps GCS internals) |

## Gate Criteria

Phase 0 is complete when ALL repos have:

- quality-gates.sh passes (or bypass documented)
- basedpyright strict + reportAny:error passes (or bypass documented)
- Zero os.getenv/os.environ in production source
- Zero Any in public API (or bypass documented)
- pyproject.toml has `requires-python = ">=3.13,<3.14"`
- QUALITY_GATE_BYPASS_AUDIT.md up to date

## Related Plans

- **Companion (parallel Phase 0):** `phase0_audit_remediation.md` — fixes the FAIL/WARN items this plan discovers. Both
  must complete before Phase 1. Relationship: this plan SCANS and VERIFIES; remediation FIXES. No circularity.

> **Sequencing mandate (J3):** (1) Enforcement gates added in WARN mode first (no merge block); (2) Remediation PRs
> merged while enforcement warns; (3) Enforcement switched to BLOCK mode only after all remediation PRs merge. This
> ordering is mandatory and is NOT implied by `blockedBy` alone — must be explicitly followed.

- Feeds into: `phase1_foundation_prep.md`, `phase2_library_tier_hardening.md`
- Standards SSOT: `unified-trading-/codex/06-coding-standards/quality-gates.md`
- Cursor rules: `.cursor/rules/core/no-type-any-use-specific.mdc`, `strict-quality-gates.mdc`, `cloud-agnostic.mdc`

> **Phase 0 gate note:** `p0-gate-check: done` means the enforcement scan and initial baseline was established
> (2026-03-04 audit). It does NOT mean all violations are fixed — that is the job of `phase0_audit_remediation.md`. The
> final Phase 0 → Phase 1 gate requires BOTH plans complete.
