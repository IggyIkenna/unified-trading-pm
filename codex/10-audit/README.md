---
scope: [engineer, admin]
---

# 10-audit — Canonical Repo Readiness Checklist SSOT

**This directory is the SSOT for all per-repo readiness state in the unified trading workspace.**

Every repo in `workspace-manifest.json` has exactly one readiness file at `repos/{repo-name}.yaml`.

---

## SSOT Boundary

This directory owns: **repo readiness criteria** (CR/DR/BR stage state, automation check status).

`unified-trading-pm/configs/` is SSOT for:

- Sharding dimensions (`sharding.{service}.yaml`)
- Venue mappings (`venues.yaml`)
- Data catalogue completion (`data-catalogue.{service}.yaml`)
- Expected start dates (`expected_start_dates.yaml`)

See `ssot-reference-mapping.md` for the full authority table.

---

## v3.0 Schema — Three Readiness Axes

Every repo tracks three independent readiness axes. Progression on one axis does not require progression on another.

### Code Readiness (CR)

| Stage | Gate | Criteria                                                                                             |
| ----- | ---- | ---------------------------------------------------------------------------------------------------- |
| CR0   | C0   | Not started                                                                                          |
| CR1   | C1   | Functionality 100% — zero `NotImplementedError`, zero stub handlers, no TODO/FIXME in prod-path code |
| CR2   | C2   | Unit tests 100% — QG unit stage green, coverage >= floor, `--cov-report=xml` written                 |
| CR3   | C3   | Integration tests 100% — every manifest dependency has a test in `tests/integration/`                |
| CR4   | C4   | Quality gate passing locally — `bash scripts/quality-gates.sh` Pass 1 fully green                    |
| CR5   | C5   | Quickmerge to feature branch — CI passes on `feat/code-readiness-{repo}` or cascade to main          |

**CR3 rule**: Count `dependencies[]` in `workspace-manifest.json`. Zero-dep repos satisfy CR3 automatically.

### Deployment Readiness (DR)

| Stage | Criteria                                                                                         |
| ----- | ------------------------------------------------------------------------------------------------ |
| DR0   | Not started                                                                                      |
| DR1   | Docker builds; cloudbuild.yaml correct; infra provisioned; setup-workspace.sh succeeds           |
| DR2   | CI smoke tests pass — production_mock_e2e GHA suite green; emulators only; zero live cloud calls |
| DR3   | Feature environment deployed — Cloud Run feat/dev; GET /health 200; GET /readiness 200           |
| DR4   | Staging SIT pass — system-integration-tests full suite green; no circuit breaker trips           |
| DR5   | Load/performance pass — P99 <= SLA; no memory leaks; throughput >= target                        |
| DR6   | Production-ready — zero CRITICAL CVEs; no DISABLE_AUTH in prod; runbook exists; 24hr health pass |

**Libraries**: `deployment_modes: null`. All DR items set to `na` with reason "library; wheel published to AR".

### Business Readiness (BR)

| Stage | Criteria                                                                                       |
| ----- | ---------------------------------------------------------------------------------------------- |
| BR0   | Not started                                                                                    |
| BR1   | Acceptance criteria defined in owning plan                                                     |
| BR2   | Circuit breaker validated via FaultInjectionTransport — CLOSED/OPEN/HALF_OPEN cycle verified   |
| BR3   | UEI events fire correctly; schema matches UAC canonical; correlation_id propagated             |
| BR4   | Domain KPIs declared AND measured                                                              |
| BR5   | PnL optimization validated — backtest confirms positive contribution (revenue-path repos only) |
| BR6   | Batch vs live validation — t+1 check within declared tolerance                                 |
| BR7   | Staging parity — N-minute replay within tolerance                                              |
| BR8   | **User approved** — human sign-off. NO AGENT MAY SET THIS.                                     |

**N/A rules**:

- BR2: `na` for libraries and UIs
- BR5: `na` for non-revenue-path repos
- BR6, BR7: `na` for libraries and UIs
- BR8: **always required** — even for infra repos

**Revenue-path repos** (BR5 required): `execution-service`, `strategy-service`, `pnl-attribution-service`,
`risk-and-exposure-service`, `ml-inference-service`, `ml-training-service`, `alerting-service`

---

## v1.0.0 Gate

A repo's version reaches `1.0.0` ONLY when ALL of these are verified AND user gives explicit approval (BR8):

- CR5 (merged to `main`, not just `feat/*`)
- DR3 (feature env deployed at least once)
- DR4 (staging SIT pass)
- BR2 (circuit breaker — services only)
- BR3 (event handling)
- BR4 (perf targets met)
- BR8 (user approved — **no agent may set this**)

---

## Directory Structure

```
10-audit/
  README.md                          — this file (SSOT declaration)
  REPO_READINESS_CHECKLIST.yaml      — v3.0 canonical template (copy to repos/ and fill in)
  consolidation-gap-analysis.md      — Phase 0 gap analysis (batch/live vs CR/DR/BR vs deployment-service)
  ssot-reference-mapping.md          — authority table: which source owns which domain
  repos/
    {repo-name}.yaml                 — one file per repo in workspace-manifest.json (65 files)
  _archive/
    batch/                           — archived per-service batch audit files (pre-v3.0 schema)
    live/                            — archived per-service live audit files (pre-v3.0 schema)
  _checklist-template.yaml           — v1.0 full 110-item checklist (preserved for reference)
  _checklist-template-enhanced.yaml  — v2.0 enhanced template with validator IDs (preserved for reference)
  _service-baseline-template.yaml    — service baseline template (preserved)
  ...other audit reports and matrices
```

---

## How to Use

### Updating a repo's readiness state

1. Open `repos/{repo-name}.yaml`
2. Update `code_readiness.current_stage` and fill in evidence for the completed stage
3. Update individual `cr*/dr*/br*` item statuses from `not_assessed` to `pass`/`fail`/`partial`
4. Commit to `feat/readiness-codex-*` branch and PR

### Creating a file for a new repo

1. Copy `REPO_READINESS_CHECKLIST.yaml` to `repos/{new-repo-name}.yaml`
2. Fill in `repo`, `repo_type`, `arch_tier`, `deployment_modes`, `business_modes`, `version`
3. Add the repo to `workspace-manifest.json` in unified-trading-pm (separate PR)

### Automated validators

Validator IDs in `code_audit_items` (COD-01..REGULATORY-04) map to scripts in
`unified-trading-codex/scripts/validators/`. Run validators to auto-populate audit item statuses.

---

## Batch/Live Split

The `deployment_modes` and `business_modes` fields in each repo file drive which DR/BR sub-sections are populated:

- `deployment_modes: ["batch"]` — only `dr.batch` populated
- `deployment_modes: ["live"]` — only `dr.live` populated
- `deployment_modes: ["batch", "live"]` — both `dr.batch` and `dr.live` populated
- `deployment_modes: null` — library; all DR items `na`

The old `batch/` and `live/` per-service files (pre-v3.0 schema) are preserved in `_archive/` for historical reference
but are no longer the authoritative readiness record.

---

## References

- **Master tracker**: `unified-trading-pm/plans/archive/code_readiness_master_plan_2026_03_11.plan.md`
- **SSOT checklist doc**: `unified-trading-pm/docs/REPO_READINESS_CHECKLIST.md`
- **Semver v1 hardening**: `unified-trading-pm/cursor-rules/core/semver-v1-hardening.mdc`
- **Repo readiness cursor rule**: `unified-trading-pm/cursor-rules/core/repo-readiness-checklist.mdc`
- **operational configs SSOT**: `unified-trading-pm/configs/` (sharding, venues, data-catalogue)
