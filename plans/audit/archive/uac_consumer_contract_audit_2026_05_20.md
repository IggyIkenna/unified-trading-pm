---
pair: unified-api-contracts → All 25 service repos
auditor: slot-4 sub-agent
audit_date: 2026-05-20
audit_file: plans/audit/uac_consumer_contract_audit_2026_05_20.md
feeds_ordering_step: C9 (cross-cutting — all services → UAC)
status: complete
repo_shas:
  unified-api-contracts: 2bdc0f07
  execution-service: f6795bfe0
  instruments-service: 95ae0b5
  features-service: 33e85297
  market-tick-data-service: fae9416
  market-data-processing-service: dbf5386
  deployment-api: 413f4a7
  strategy-service: e4e5a1e6
  deployment-service: c84b046
  unified-trading-library: a786d2fa
---

# C9 Contract Audit — All Services → UAC (unified-api-contracts)

> Read-only audit. No code changes made. Output fed into mega-audit tracker
> `mega_audit_and_plan_beefup_progression_2026_05_20.md` § Phase C C9 row.

---

## 0. Audit scope

**Upstream**: `unified-api-contracts` (UAC) — canonical type definitions, import surface facade, error taxonomy,
emission policies, manifest schema, venue registry, expected coverage, coverage_start dates.

**Downstream**: All 25 service repos in the workspace. Audit focuses on Pattern 7 (UAC import surface rule — the C9
primary) with cross-cutting findings from Patterns 3, 4, and 6.

**Scan coverage**: Exhaustive `rg` across all `.py` files in each repo excluding `.venv*`, `__pycache__`,
`node_modules`. Every service directory and test directory scanned. Scripts directories included.

**What is NOT in scope for this audit**: GCS data state (covered by A3/A4), manifest emission per handler (covered by
C1–C8 per-pair audits), bucket-SSOT (covered by A1 `resolve_bucket_name` check).

---

## Pattern 7 — UAC Import Surface (Primary for C9)

### What this pattern governs

All consumer repos MUST import from UAC facade modules only:

```python
# CORRECT
from unified_api_contracts import DefiErrorCode, EmptyConfirmedReason
from unified_api_contracts.sports import get_league, build_fixture_id
from unified_api_contracts.execution import CanonicalOrder
```

Deep imports into `canonical/`, `normalize_utils/`, `config/`, `shared/`, or `schemas/` sub-modules are blocked. QG STEP
5.23 in `base-service.sh` enforces this for production source directories (excludes `test_*`, `conftest*`).

**Rule source**: `cursor-configs/imports/uac-import-surface-enforcement.mdc` + CLAUDE.md UAC import rule.

---

## Per-Service Import Surface Compliance Table

Counted via `rg 'from unified_api_contracts\.canonical\.' <repo>/ --type py`. QG enforcement checked via STEP 5.23
(`UAC_CANONICAL_EXEMPT` override detection). Production violations = SOURCE*DIR hits excluding `test*_`and`conftest_`.

| Repo                             | Total violations | noqa exemptions | Prod-code violations | Test violations | Scripts violations | QG state                                            | P-level |
| -------------------------------- | ---------------: | --------------: | -------------------: | --------------: | -----------------: | --------------------------------------------------- | ------- |
| `instruments-service`            |               32 |               0 |                   20 |               4 |                  8 | **BYPASSED** (`UAC_CANONICAL_EXEMPT=true` line 132) | P0      |
| `execution-service`              |               25 |               5 |      11 (6 w/o noqa) |              14 |                  0 | **BYPASSED** (`UAC_CANONICAL_EXEMPT=true` line 19)  | P0      |
| `deployment-api`                 |               29 |               2 |                    7 |              22 |                  0 | Enforced (STEP 5.23 active) — QG failing            | P0      |
| `features-service`               |               12 |               0 |                    1 |              11 |                  0 | Enforced (STEP 5.23 active) — QG failing            | P0      |
| `market-data-processing-service` |               13 |               0 |                    4 |               9 |                  0 | Enforced (STEP 5.23 active) — QG failing            | P0      |
| `market-tick-data-service`       |               10 |               2 |                    6 |               4 |                  0 | Enforced (no exempt set) — QG failing               | P0      |
| `unified-trading-library`        |               26 |               2 |                    0 |              26 |                  0 | CLEAN prod                                          | P2      |
| `deployment-service`             |                5 |               0 |                    0 |               0 |                  5 | CLEAN prod (scripts only)                           | P2      |
| `strategy-service`               |                2 |               0 |                    0 |               2 |                  0 | CLEAN prod                                          | P2      |
| `market-data-processing-service` |               13 |               0 |                    4 |               9 |                  0 | Enforced — failing                                  | P0      |
| `unified-api-contracts`          |              352 |               0 |                  352 |               — |                  — | EXEMPT (UAC itself)                                 | OK      |
| `unified-trading-pm`             |                5 |               0 |          5 (scripts) |               0 |                  0 | PM scripts — no QG                                  | P3      |
| `unified-trading-system-ui`      |               12 |               0 |                    0 |               0 |            12 (TS) | UI context — different rule                         | P3      |
| All other repos (≤0 violations)  |                0 |               — |                    0 |               0 |                  0 | CLEAN                                               | OK      |

**Total non-UAC-internal violations (prod code)**: 49 files across 6 repos.

**QG bypass P0**: `instruments-service` and `execution-service` have `UAC_CANONICAL_EXEMPT=true` set in their
`quality-gates.sh` despite being consumer repos (not UAC). This flag is only valid for `unified-api-contracts` itself,
`system-integration-tests`, and `unified-cloud-interface`. Setting it in consumer repos silently defeats the entire STEP
5.23 gate.

---

## Dim 1 — Violation taxonomy by canonical sub-path

| Sub-path violated                                                               | Repos                                                                                 | Facade available at                                                                                                     | P-level         |
| ------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- | --------------- |
| `canonical.domain.sports.league_data`                                           | instruments-service (17 hits in orchestrator.py alone)                                | `unified_api_contracts.sports` → `get_league`, `get_leagues_by_classification`, `LEAGUE_REGISTRY`, etc. ALL re-exported | P0              |
| `canonical.domain.sports.canonical_ids`                                         | instruments-service, execution-service (test)                                         | `unified_api_contracts.sports` → `build_fixture_id` re-exported                                                         | P0              |
| `canonical.crosscutting.errors.defi`                                            | execution-service (cctp.py, recursive_loop_orchestrator.py)                           | `unified_api_contracts` → `DefiErrorCode` IS on root facade                                                             | P0              |
| `canonical.crosscutting.errors`                                                 | execution-service (orchestrator.py, instruction_router.py, multi_leg_orchestrator.py) | `unified_api_contracts` → `ErrorAction`, `classify_venue_error` ARE on root facade                                      | P0              |
| `canonical.crosscutting.execution`                                              | execution-service (backtest/node_builder.py)                                          | `BENCHMARK_FILL_ALGO_TYPE`, `BATCH_FILL_ALGO_TYPES` — **NOT on root facade** (P0 gap in UAC itself)                     | P0              |
| `canonical.crosscutting.honest_coverage`                                        | features-service (perp_funding_handler.py), market-tick-data-service, MDPS            | `EmptyConfirmedReason` IS on root facade; `RecordFailedReason` **NOT on root facade** (P0 UAC gap)                      | P0              |
| `canonical.crosscutting.source_priority`                                        | MDPS (canonical_writer.py), market-tick-data-service                                  | `get_source_priority`, `has_source_priority`, `read_with_source_priority` ARE on root facade                            | P0              |
| `canonical.crosscutting.service_emission_policy`                                | features-service (tests), strategy-service (tests), MDPS (tests)                      | `ServiceEmissionPolicy`, `ServiceEmissionStateEnum`, `next_state` ARE on root facade                                    | P2 (tests only) |
| `canonical.crosscutting.pipeline_mode`                                          | market-tick-data-service (test)                                                       | `PipelineMode` — check facade                                                                                           | P2 (test only)  |
| `canonical.crosscutting.source_priority`                                        | market-tick-data-service (orchestrator.py)                                            | IS on root facade                                                                                                       | P0              |
| `canonical.crosscutting.venue_thresholds`                                       | execution-service (test)                                                              | Not confirmed on root facade                                                                                            | P2 (test only)  |
| `canonical.crosscutting` (bare)                                                 | deployment-service (vm_zombie_watchdog.py)                                            | `LifecycleClass` IS on root facade                                                                                      | P0              |
| `canonical.domain.sports` (league_classification_data_a/b, provider_league_ids) | deployment-service (scripts)                                                          | Sports scripts (not prod service)                                                                                       | P2              |

---

## Dim 2 — UAC internal gaps (symbols NOT on root/domain facade)

Two symbols are being imported deep because they have no facade-level re-export. This is a UAC-side gap — consumer
deep-import is the symptom, the cause is missing facade promotion.

| Symbol                     | Deep path used                           | Facade gap status                                                       | Impact                                                                           | P-level |
| -------------------------- | ---------------------------------------- | ----------------------------------------------------------------------- | -------------------------------------------------------------------------------- | ------- |
| `BENCHMARK_FILL_ALGO_TYPE` | `canonical.crosscutting.execution`       | Missing from `unified_api_contracts.__init__` AND `execution.py` facade | execution-service `backtest/node_builder.py` forced to use deep path             | P0      |
| `BATCH_FILL_ALGO_TYPES`    | `canonical.crosscutting.execution`       | Missing from root facade                                                | execution-service `backtest/node_builder.py` forced to use deep path             | P0      |
| `RecordFailedReason`       | `canonical.crosscutting.honest_coverage` | Missing from root facade                                                | MDPS `dependency_checker.py`, `orchestration_service.py` forced to use deep path | P0      |

**Note**: These symbols exist and are stable — they are simply not promoted to the root `__init__.py` facade. Fix is 3
lines in `unified-api-contracts/unified_api_contracts/__init__.py`.

---

## Dim 3 — QG bypass audit (UAC_CANONICAL_EXEMPT misuse)

| Repo                                               | Line                        | Justification (if any)                           | Verdict                                       |
| -------------------------------------------------- | --------------------------- | ------------------------------------------------ | --------------------------------------------- |
| `execution-service/scripts/quality-gates.sh:19`    | `UAC_CANONICAL_EXEMPT=true` | No comment — appears to be a blanket suppression | **INVALID** — consumer repo must not set this |
| `instruments-service/scripts/quality-gates.sh:132` | `UAC_CANONICAL_EXEMPT=true` | No comment                                       | **INVALID** — consumer repo must not set this |

The `UAC_CANONICAL_EXEMPT` flag was designed for three repos only: `unified-api-contracts` (internal),
`system-integration-tests` (tests UAC internals), and `unified-cloud-interface`. Setting it in a consumer service
silently bypasses 20+ production violations per repo, making STEP 5.23 ineffective for the highest-violation repos in
the workspace.

---

## Dim 4 — UAC own-code violations (internal deep-import pattern)

`unified-api-contracts/scripts/generate_instrument_catalogue.py` imports `canonical.coverage_starts` and
`canonical.gcs_paths` directly (lines 41–46). This is **exempt** — it is a UAC-internal script, not a consumer repo. The
same script contains a `# Pre-v5 fallback` comment (line ~158) which is a data-shape legacy guard, not an import
fallback. No violation.

---

## Pattern 3 — Schema-version (UAC manifest_schema.py finding A4)

`unified-api-contracts/unified_api_contracts/canonical/crosscutting/manifest_schema.py` declares:

```python
MANIFEST_SCHEMA_VERSION_V8: Final[int] = 8
```

UTL `manifest_writer.py` declares `MANIFEST_SCHEMA_VERSION = 8` (also v8). Both are aligned at v8.

**A4 code-side finding**: 6 code files across the workspace still reference hardcoded `schema_version` < 8 (from A1 scan
`manifest_v8` check, 6 violations). These are in MTDS and IS migration scripts. See A4 audit
`results/manifest_v8_compliance_2026_05_20.md` for the full data-side picture (majority of prod rows are v4–v7).

**UAC-specific note**: The `manifest_schema.py` module (`canonical/crosscutting/manifest_schema.py`) is entirely omitted
from `[tool.coverage.run].omit` in UAC `pyproject.toml`:

```toml
"unified_api_contracts/canonical/crosscutting/*",
```

This means the v8 column declarations in `manifest_schema.py` have 0% test coverage in UAC's own test suite. This is the
`uac_coverage_excludes_blank_8b_8c_ratchet_2026_05_17.md` issue. See UAC coverage gap finding below.

---

## Pattern 4 — Honest-absence reason taxonomy (A2 context)

UAC `coverage_starts.py` has 5 `# TODO verify` entries that affect `expected_coverage()` preflight accuracy:

| Venue        | Asset group | Seeded date  | TODO                                       | Impact                                             |
| ------------ | ----------- | ------------ | ------------------------------------------ | -------------------------------------------------- |
| `TARDIS`     | CEFI        | `2017-06-01` | Unverified against prod manifest min(date) | May over-clip early dates                          |
| `ETHERFI`    | DEFI        | `2023-11-01` | Unverified                                 | May cause false EXPECTED_PRE_SOURCE_COVERAGE_START |
| `UNISWAP_V4` | DEFI        | `2025-01-31` | Unverified                                 | Same                                               |
| `TARDIS`     | TRADFI      | `2017-06-01` | Unverified                                 | Same                                               |
| `CME`        | TRADFI      | `2010-01-01` | Unverified                                 | May over-clip pre-2010 dates                       |

VX/CBOE front-month gap: `tradfi_symbology.py` maps `VX → (VX.FUT, XCBF.MDP3)` and `VIX_FUT → (VX.FUT, XCBF.MDP3)`. No
VX-specific `coverage_start` entry exists in `TRADFI_SOURCE_COVERAGE_START`. Expected-coverage checks for VX fall back
to the CME entry (`2010-01-01`) or return `None` (no clip). This was flagged in issue
`unified_api_contracts_todo_audit_2026_05_19.md` as Issue 1 (VX front-month CBOE gap). The issue is correctly subsumed
by C9 (this audit) per the open_issues_triage doc.

---

## UAC Coverage Exclusion Gap (P0 for UAC itself)

`unified-api-contracts/pyproject.toml` `[tool.coverage.run].omit` excludes entire directories:

```toml
"unified_api_contracts/canonical/crosscutting/*",
"unified_api_contracts/canonical/crosscutting/errors/*",
```

This means the following modules have **0% UAC test coverage**:

- `manifest_schema.py` (v8 column declarations)
- `honest_coverage.py` (EmptyConfirmedReason, RecordFailedReason, compute_honest_coverage)
- `errors/` (DefiErrorCode, ErrorAction, classify_venue_error)
- `service_emission_policy.py`
- All 28 other modules under `canonical/crosscutting/`

The omit is labeled "Transitional: exclude new-path copies until old paths are removed (citadel phase 1)". As of
2026-05-20 this exclusion has been in place for multiple phases and the old paths are no longer present in the `shared/`
or `normalize/` directories. The "transitional" label is stale. The `fail_under = 84` coverage threshold is only
enforced on the non-omitted subset of code.

**This issue is documented in**: `issues/uac_coverage_excludes_blank_8b_8c_ratchet_2026_05_17.md` (triage:
MEGA-AUDIT:D:cross-cutting-QG-ratchet per `open_issues_triage_against_mega_audit_2026_05_20.md`).

---

## 4-Dimensional Audit Matrix

| Dim   | What it measures                           | Status                                                                                                 | Evidence                         |
| ----- | ------------------------------------------ | ------------------------------------------------------------------------------------------------------ | -------------------------------- |
| Dim 1 | Upstream (UAC) facade coverage             | **GAP** — `BENCHMARK_FILL_ALGO_TYPE`, `BATCH_FILL_ALGO_TYPES`, `RecordFailedReason` not on root facade | Dim 2 table above                |
| Dim 2 | Downstream import surface compliance       | **49 production violations across 6 repos**                                                            | Per-service table above          |
| Dim 3 | QG enforcement state                       | **2 repos improperly bypass STEP 5.23** (execution-service, instruments-service)                       | Dim 3 table above                |
| Dim 4 | UAC own test coverage of canonical modules | **0% coverage on all of `canonical/crosscutting/`** due to stale omit list                             | pyproject.toml coverage.run.omit |

---

## P0 Findings Summary

| ID      | Finding                                                                                                                  | Repo                           | Severity | Remediation                                                                                                                       |
| ------- | ------------------------------------------------------------------------------------------------------------------------ | ------------------------------ | -------- | --------------------------------------------------------------------------------------------------------------------------------- |
| C9-P0-1 | `execution-service` sets `UAC_CANONICAL_EXEMPT=true` — bypasses STEP 5.23 for 11 production violations                   | execution-service              | P0       | Remove flag; fix 6 deep imports (others are already `# noqa` pending facade promotion)                                            |
| C9-P0-2 | `instruments-service` sets `UAC_CANONICAL_EXEMPT=true` — bypasses STEP 5.23 for 20 production violations                 | instruments-service            | P0       | Remove flag; migrate `canonical.domain.sports.league_data` → `unified_api_contracts.sports`                                       |
| C9-P0-3 | `BENCHMARK_FILL_ALGO_TYPE` and `BATCH_FILL_ALGO_TYPES` not on root facade — consumers forced to deep-import              | unified-api-contracts          | P0       | Promote to `unified_api_contracts/__init__.py` (3 lines)                                                                          |
| C9-P0-4 | `RecordFailedReason` not on root facade — MDPS forces deep `canonical.crosscutting.honest_coverage`                      | unified-api-contracts          | P0       | Promote to root facade                                                                                                            |
| C9-P0-5 | `features-service` has 1 prod violation (`perp_funding_handler.py:20`) that should fail QG STEP 5.23                     | features-service               | P0       | Change `canonical.crosscutting.honest_coverage import EmptyConfirmedReason` → `unified_api_contracts import EmptyConfirmedReason` |
| C9-P0-6 | `deployment-api` has 7 prod violations — QG STEP 5.23 should be failing                                                  | deployment-api                 | P0       | Audit each file; most symbols (`EmptyConfirmedReason`, `ErrorAction`, `LifecycleClass`) ARE on root facade                        |
| C9-P0-7 | MDPS has 4 prod violations (`RecordFailedReason` + `source_priority` deep imports) — QG failing                          | market-data-processing-service | P0       | After P0-4 fix (facade promotion), these become 1-line changes                                                                    |
| C9-P0-8 | MTDS has 6 prod violations (`source_priority` deep imports in orchestrator.py) — QG should fail                          | market-tick-data-service       | P0       | `source_priority` IS on root facade; change imports                                                                               |
| C9-P0-9 | 5 `# TODO verify` coverage_start dates in UAC — affects `expected_coverage()` accuracy for TARDIS/ETHERFI/UNISWAP_V4/CME | unified-api-contracts          | P0       | Verify against prod manifest `read_availability_index().date.min()` per venue                                                     |

---

## P1/P2/P3 Findings

| ID      | Finding                                                                                                                   | Repo                       | Severity                                                                             |
| ------- | ------------------------------------------------------------------------------------------------------------------------- | -------------------------- | ------------------------------------------------------------------------------------ |
| C9-P2-1 | `service_emission_policy` deep-imported in tests (features-service, strategy-service, MDPS tests)                         | multiple                   | P2 — `ServiceEmissionPolicy` IS on root facade; test imports should switch to facade |
| C9-P2-2 | `deployment-service` scripts use `canonical.domain.sports.league_classification_data_a/b` — symbols not clearly on facade | deployment-service scripts | P2                                                                                   |
| C9-P2-3 | `unified-trading-library` tests use 26 deep canonical imports — no prod violations                                        | unified-trading-library    | P2 — tests only                                                                      |
| C9-P2-4 | UAC `generate_instrument_catalogue.py` uses `canonical.coverage_starts` and `canonical.gcs_paths` directly                | unified-api-contracts      | P3 — UAC-internal script, exempt                                                     |
| C9-P2-5 | VX/CBOE front-month period has no dedicated coverage_start entry in TRADFI dict — falls back to CME                       | unified-api-contracts      | P2                                                                                   |
| C9-P3-1 | UAC `[tool.coverage.run].omit` stale — `canonical/crosscutting/*` excluded since citadel phase 1 which is now complete    | unified-api-contracts      | P3 (non-blocking but degrades QG signal)                                             |

---

## Pattern 7 — Remediation priority order

**Wave 1 — UAC facade promotion (unblocks all consumers, 30 min)**:

1. Promote `BENCHMARK_FILL_ALGO_TYPE`, `BATCH_FILL_ALGO_TYPES` to `unified_api_contracts/__init__.py`
2. Promote `RecordFailedReason` to `unified_api_contracts/__init__.py`

**Wave 2 — Remove QG bypass exemptions + fix production violations**: 3. Remove `UAC_CANONICAL_EXEMPT=true` from
`execution-service/scripts/quality-gates.sh` 4. Fix 6 production violations in execution-service (swap deep paths for
root facade imports) 5. Remove `UAC_CANONICAL_EXEMPT=true` from `instruments-service/scripts/quality-gates.sh` 6. Fix 20
production violations in instruments-service (swap `canonical.domain.sports.league_data` for
`unified_api_contracts.sports`)

**Wave 3 — Fix currently-QG-failing repos**: 7. Fix
`features-service/features_service/cefi/cli/handlers/perp_funding_handler.py:20` 8. Fix MDPS 4 prod violations (post
Wave 1 — `RecordFailedReason` will be on facade) 9. Fix MTDS 6 prod violations (`source_priority` already on facade) 10.
Fix deployment-api 7 prod violations

**Wave 4 — Verify coverage_starts TODO items**: 11. Probe prod manifests for TARDIS, ETHERFI, UNISWAP_V4, CME actual
min(date)

---

## QG-Ratchet Phase (what to wire)

| Pattern                 | Current state                                             | Gap                           | Proposed step                                                                                                                                        |
| ----------------------- | --------------------------------------------------------- | ----------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| P7 — UAC import surface | STEP 5.23 SHIPPED — but bypassed by 2 repos               | `UAC_CANONICAL_EXEMPT` misuse | Remove misuse; add CI check that `UAC_CANONICAL_EXEMPT` is only set in exempt repos                                                                  |
| P7 — test coverage      | Tests excluded from STEP 5.23                             | Tests accumulate deep imports | Consider extending STEP 5.23 to `tests/` with a ratchet baseline (today: cursor rule only)                                                           |
| UAC facade completeness | No gate verifying all consumer symbols are on root facade | 3 symbols missing             | Add `check_uac_facade_coverage.py` to UAC QG that asserts every symbol in `__all__` of `canonical/**` is re-exported through a root or domain facade |
| Coverage exclusion      | `canonical/crosscutting/*` omitted from UAC coverage      | Stale omit                    | Remove omit lines in UAC `pyproject.toml` once citadel phase 2 migration is confirmed complete                                                       |

---

## Continuous Verification Column

| Pattern                        | Verification path                                      | Cadence                        | Last verified                  |
| ------------------------------ | ------------------------------------------------------ | ------------------------------ | ------------------------------ |
| P7 — UAC import surface (prod) | STEP 5.23 in `base-service.sh`                         | Every push to LDR              | 2026-05-20 (this audit)        |
| P7 — QG bypass exemption       | Manual audit of `quality-gates.sh` per repo            | Per C-series audit cycle       | 2026-05-20 (this audit)        |
| Facade completeness            | Manual audit (no automated check yet)                  | Per C-series audit cycle       | 2026-05-20 (this audit)        |
| coverage_starts accuracy       | `read_availability_index().date.min()` probe per venue | Per A2 expected_coverage cycle | Not yet run (TODOs unverified) |

---

## Phased Execution DAG

```
Phase 1 — UAC facade promotion (Wave 1 — 3 lines in __init__.py)
   Unblocks: all MDPS + execution-service deep imports become fixable
   │
   ├── Phase 2 — Remove UAC_CANONICAL_EXEMPT from consumer repos + fix violations
   │   (instruments-service, execution-service)
   │
   ├── Phase 3 — Fix currently-failing QG repos
   │   (features-service, MDPS, MTDS, deployment-api)
   │
   ├── Phase 4 — Verify coverage_starts TODO items against prod manifests
   │
   ├── Phase 5 — Remove stale omit from UAC pyproject.toml
   │
   └── Phase Q — QG ratchet
       - Assert UAC_CANONICAL_EXEMPT only set for exempt repos (3 allowed)
       - Add check_uac_facade_coverage.py to UAC QG
       - Extend STEP 5.23 to test directories with ratchet baseline
```

**Foundation-completion-gate**: C9 Phase 1+2+3 must be GREEN before any audit depends on STEP 5.23 for cross-cutting
contract enforcement.

---

## Scope exclusions (verified clean)

- **Pattern 1 (SSOT-owned reference)**: Not applicable for UAC pair — UAC IS the SSOT.
- **Pattern 2 (Manifest emission)**: Covered per-pair in C1–C8 audits.
- **Pattern 5 (expected_coverage preflight)**: Covered by A2/A3 audits.
- **Pattern 6 (error classification)**: `classify_venue_error` IS on root facade. Repos importing via deep path should
  switch to root facade, but the error classification semantics themselves are correct.
- **Repos with 0 violations** (verified clean prod code): `trading-agent-service`, `alerting-service`,
  `agent-orchestrator`, `ml-service`, `ml-training-service`, `ml-inference-service`,
  `batch-live-reconciliation-service`, `unified-trading-api`, `system-integration-tests`, `client-reporting-api`,
  `fund-administration-service`, `ibkr-gateway-infra`.

---

## Temporary States + Canonical Follow-Up Plans

| State                                                                                  | Introduced by                                                    | Retires when                                                   |
| -------------------------------------------------------------------------------------- | ---------------------------------------------------------------- | -------------------------------------------------------------- |
| `noqa: qg-deep-import` suppressions in execution-service sports adapters (5 instances) | Pre-existing — added as bridge while facade symbols were pending | Phase 2 — after Wave 1 facade promotion, noqa comments removed |
| `UAC_CANONICAL_EXEMPT=true` in execution-service + instruments-service QG scripts      | Pre-existing workaround                                          | Phase 2 — removed as part of remediation wave                  |
| `# TODO verify` on 5 coverage_start dates                                              | Pre-existing conservative seeding                                | Phase 4 — verified against prod manifest probes                |
| `[tool.coverage.run].omit` excluding `canonical/crosscutting/*`                        | Citadel phase 1 transition                                       | Phase 5 — removed after confirming old paths fully removed     |

**Successor plan**: All remediations tracked under `mega_audit_and_plan_beefup_progression_2026_05_20.md` Phase D
(QG-ratchet + cross-cutting fixes). Specific phase D items: D cross-cutting QG-ratchet plan (facade completeness gate) +
individual C-series service fixes (instruments-service C2, execution-service C3, MTDS C0, features-service C1/C4,
deployment-api C-new).
