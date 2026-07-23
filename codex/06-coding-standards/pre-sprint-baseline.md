---
doc_type: codex-ssot
title: Pre-Sprint Baseline (Phase 0)
summary:
  Phase-0 pre-sprint baseline audit protocol — the 6 read-only per-repo checks (python-version, quality-gates.sh
  --no-fix, basedpyright strict + reportAny, os.getenv/os.environ scan, Any-in-public-API scan, cloud-SDK-import scan)
  run in tier order before ANY hardening sprint, with the failure protocol, gate criteria, and QUALITY_GATE_BYPASS_AUDIT
  format.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos:
  [
    execution-service,
    features-service,
    instruments-service,
    market-tick-data-service,
    unified-api-contracts,
    unified-trading-library,
  ]
scope: [engineer]
tags: [pre-sprint-baseline, quality-gates, audit, ssot-audit, refactor]
related:
  [
    /codex/06-coding-standards/quality-gates.md,
    /codex/06-coding-standards/integration-testing-layers.md,
    /codex/04-architecture/tier-and-import-architecture.md,
  ]
created: 2026-03-27
authoritative_for: [Phase-0 pre-sprint baseline audit protocol]
referenced_by: [/codex/04-architecture/cloud-agnostic-migration.md]
owner:
last_reviewed:
code_refs:
---

# Pre-Sprint Baseline (Phase 0)

**Last Updated:** 2026-03-04 **SSOT for:** The Phase 0 audit protocol that every repo must pass before any hardening
sprint begins. **Cross-refs:**

- Plan: `unified-trading-pm/plans/archive/phase0_standards_enforcement.plan.md`
- Quality gates: `unified-trading-pm/codex/06-coding-standards/quality-gates.md`
- Integration testing layers: `unified-trading-pm/codex/06-coding-standards/integration-testing-layers.md`
- Tier architecture: `04-architecture/tier-and-import-architecture.md`
- Workspace manifest: `unified-trading-pm/workspace-manifest.json`

---

## Purpose

Before any hardening sprint begins (Phase 1, 2, or 3), every repo in scope must pass a baseline verification. This is
"Phase 0" — a read-only audit that surfaces the current state and either fixes trivial violations immediately or
documents genuine exceptions.

**No hardening work starts until Phase 0 is complete.**

---

## The 6 Per-Repo Checks

Run in this order per repo:

```bash
# 1. Verify Python version
grep 'requires-python' pyproject.toml
# Must be: requires-python = ">=3.13,<3.14"

# 2. Quality gates (coverage, file size, function/method/class size)
bash scripts/quality-gates.sh --no-fix
# Targets: MIN_COVERAGE=70, MAX_FILE_LINES=900, MAX_FUNCTION_LINES=200, MAX_METHOD_LINES=50, MAX_CLASS_LINES=900

# 3. Strict type checking
timeout 120 basedpyright <source_dir>/
# Must pass with typeCheckingMode: strict, reportAny: error

# 4. os.getenv / os.environ scan
rg "os\.getenv|os\.environ" --type py --glob '!.venv*' --glob '!tests' <source_dir>/
# Must return zero results in production source

# 5. Any-type scan
rg ": Any|-> Any|\[Any\]|dict\[str, Any\]" --type py --glob '!.venv*' <source_dir>/
# Must return zero results in public API (protocol/interface modules)

# 6. Cloud-agnostic scan (direct SDK imports outside providers/)
rg "from google\.cloud|import boto3" --type py --glob '!.venv*' --glob '!providers' <source_dir>/
# Must return zero results outside providers/ directories
```

---

## Execution Order

Run in tier order (T0 first, services last). Within each tier, run all repos in parallel.

| Tier     | Repos                                                                                                                                                                                                                                                                                                                                                            |
| -------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| T0       | unified-api-contracts (incl. internal subpackage), unified-cloud-interface, unified-trading-library, instruments-service (formerly unified-reference-data-interface), matching-engine-library                                                                                                                                                                    |
| T1       | unified-config-interface, unified-trading-library, execution-algo-library, unified-trading-library                                                                                                                                                                                                                                                               |
| T2       | market-tick-data-service/market_tick_data_service/market_interface, execution-service (formerly unified-trade-execution-interface), unified-ml-interface, position-balance-monitor-service (formerly unified-position-interface), execution-service (formerly unified-defi-execution-interface), execution-service (formerly unified-sports-execution-interface) |
| T3       | unified-domain-client                                                                                                                                                                                                                                                                                                                                            |
| Services | Per Phase 3 DAG order (instruments-service first)                                                                                                                                                                                                                                                                                                                |

---

## Failure Protocol

| Violation                                    | Action                                                                             |
| -------------------------------------------- | ---------------------------------------------------------------------------------- |
| `os.getenv` in source                        | Fix immediately — `UnifiedCloudConfig` (config) or `get_secret_client()` (secrets) |
| `Any` in public API                          | Fix immediately — use `TypedDict`, `Protocol`, or concrete type                    |
| File >900L                                   | Split by SRP in a separate commit                                                  |
| Coverage <70%                                | Add tests OR document in `QUALITY_GATE_BYPASS_AUDIT.md` with justification         |
| Python version not 3.13                      | Update `pyproject.toml`; fix syntax incompatibilities                              |
| `reportAny` violations                       | Fix the type — never `# type: ignore` to hide Any                                  |
| Direct cloud SDK import outside `providers/` | Refactor through `get_storage_client()` / `get_secret_client()`                    |

---

## QUALITY_GATE_BYPASS_AUDIT.md

Each repo's root must contain a `QUALITY_GATE_BYPASS_AUDIT.md` documenting any bypass. Format:

```markdown
| Rule         | File              | Line | Reason                                                         | Owner          | Review by  |
| ------------ | ----------------- | ---- | -------------------------------------------------------------- | -------------- | ---------- |
| coverage<70% | trading_engine.py | —    | Legacy integration-only code; unit tests require live exchange | @ikennaigboaka | 2026-04-01 |
```

Bypasses are reviewed at each sprint end and must decrease over time.

---

## Gate Criteria

Phase 0 is complete when ALL repos have:

- [ ] `quality-gates.sh --no-fix` passes (or bypass documented)
- [ ] `basedpyright` strict + `reportAny: error` passes (or bypass documented)
- [ ] Zero `os.getenv`/`os.environ` in production source
- [ ] Zero `Any` in public API (or bypass documented)
- [ ] `requires-python = ">=3.13,<3.14"` in `pyproject.toml`
- [ ] `QUALITY_GATE_BYPASS_AUDIT.md` up to date

---

## Known Offenders (as of 2026-03-04)

| Repo                                | Violation                        | Status                  |
| ----------------------------------- | -------------------------------- | ----------------------- |
| features-service (delta-one family) | Python 3.9 in CI (requires 3.13) | Must fix before Phase 3 |
| (run Phase 0 to discover others)    |                                  |                         |

---

## Related

- [phase0_standards_enforcement.plan.md](../../plans/archive/phase0_standards_enforcement.plan.md)
- [quality-gates.md](quality-gates.md)
- [integration-testing-layers.md](integration-testing-layers.md)
