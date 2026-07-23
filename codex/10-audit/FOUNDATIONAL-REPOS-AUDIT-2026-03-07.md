---
doc_type: codex-ssot
title: Foundational Repos Audit — 2026-03-07
summary:
  Historical 2026-03-07 snapshot grading 18 pre-service repos (T0–T3 + system-integration-tests) across 10 dimensions —
  headline "0 of 18 repos pass their quality gate"; per-repo grades, cross-cutting systemic issues (coverage-gaming
  files, schema duplication, REPO_ARCH_TIER unwired), and a P0–P3 remediation order. Superseded by later QG hardening —
  use repos/<name>.yaml for current readiness.
status: stale
nature: ssot
asset_group: [meta]
stage: [meta]
repos:
  [
    deployment-service,
    execution-service,
    features-service,
    instruments-service,
    market-tick-data-service,
    strategy-service,
  ]
scope: [engineer, admin]
tags: [audit, quality-gates, ssot-audit, coverage, tier]
related: [/codex/10-audit/QUALITY_GATES_COVERAGE_REPORT.md, /codex/10-audit/QUALITY_GATE_BYPASS_AUDIT.md]
created: 2026-03-27
authoritative_for: [2026-03-07 foundational-repos audit snapshot]
referenced_by: [/codex/10-audit/QUALITY_GATES_COVERAGE_REPORT.md, /codex/10-audit/VALIDATOR_COVERAGE_MATRIX.md]
owner:
last_reviewed:
code_refs:
---

# Foundational Repos Audit — 2026-03-07

> **Historical snapshot (2026-03-07).** All grades, QG statuses, and suppression counts reflect the state of the
> workspace on 2026-03-07. Significant refactoring has occurred since then (features-service consolidation, QG step
> hardening through STEP 5.70, manifest v8 migration, bucket SSOT canonicalisation, etc.). The "0 of 18 repos have a
> passing quality gate" headline was the Mar-07 state; re-run `bash scripts/quality-gates.sh` per-repo for current QG
> status. Use `codex/10-audit/repos/{repo-name}.yaml` for the current CR/DR/BR readiness state.

**SSOT:** This document. Registered in `unified-trading-pm/codex/00-SSOT-INDEX.md`. **Scope:** 18 pre-service repos
(T0–T3 + system-integration-tests) + 10-section workspace-level audit. **Method:** 18 parallel per-repo agents + 10
parallel workspace-category agents. **Note on coverage:** 5 per-repo agents hit rate limits mid-run; findings recovered
from partial transcripts + direct re-audit.

---

## PART 1 — PER-REPO GRADES (18 Pre-Service Repos)

### Grading Dimensions

1. Coverage — threshold vs actual
2. Basedpyright — error count in source (not tests)
3. Integration Tests — meaningful cross-boundary tests
4. VCR Tests — cassette-backed external call validation
5. Orphaned/Duplicated Code — dead code, schema duplication
6. Tech Debt — TODO/FIXME/type:ignore/os.getenv in source
7. Dependency Versions — bounded, aligned, minimal
8. Single Responsibility — scope violations
9. Quality Gates — QG passes/fails
10. Inter-repo Usage — correct tier imports

---

### Summary Scorecard

| #   | Repo                                                               | Tier | Grade | Pyright (src)                     | Coverage                            | QG Status                                                                                                 |
| --- | ------------------------------------------------------------------ | ---- | ----- | --------------------------------- | ----------------------------------- | --------------------------------------------------------------------------------------------------------- |
| 1   | unified-cloud-interface                                            | T0   | B+    | A (0 errors)                      | B (87%, gate 70%)                   | FAILING — 85 ruff (70×E501, 2×C901)                                                                       |
| 2   | matching-engine-library                                            | T0   | B+    | A (0 errors)                      | A (88.9%, gate 88%)                 | FAILING — 3×E501 (amm.py:537, trade_matcher.py:120, test_amm.py:210)                                      |
| 3   | instruments-service                                                | T1   | B+    | C (0 src / 58 test)               | A (91.4%, gate 87%)                 | FAILING — 4 violations (test >900 lines, 2× backward-compat shims)                                        |
| 4   | unified-api-contracts                                              | T0   | B     | A (0 errors)                      | B (81%, gate 80%)                   | B — gate mismatch: script enforces 70%, pyproject says 80%                                                |
| 5   | unified-trading-library                                            | T0   | B     | B (1 test error)                  | C (97%, gate 99%)                   | FAILING — coverage gap + REPO_ARCH_TIER wiring broken → tier checks skip in CI                            |
| 6   | position-balance-monitor-service                                   | T2   | B     | A (0 src / 30 test)               | B (84%, gate 70%)                   | FAILING — hardcoded absolute path in VCR test, gate too low                                               |
| 7   | unified-api-contracts (internal/)                                  | T0   | C+    | D (56 errors)                     | A (100%, gate 99%)                  | FAILING — type-check step fails on schema_definition.py                                                   |
| 8   | unified-trading-library                                            | T2   | C+    | D (23 errors, stale bypass audit) | A (92.6%, gate 93%)                 | FAILING — 1×E501 in base.py blocks step 1; steps 3–6 never run                                            |
| 9   | unified-ml-interface                                               | T2   | C+    | D (38 src errors)                 | A (92.1%, gate 91%)                 | FAILING — 12 ruff (C901×1, E501×2)                                                                        |
| 10  | unified-trading-library                                            | T1   | C     | D (391 errors)                    | C (76.1%, gate 70%)                 | FAILING — 87 ruff errors blocked at lint step                                                             |
| 11  | unified-defi-exec-interface                                        | T2   | C     | D (133 errors)                    | B (88.8%, gate 88%)                 | FAILING — 4 ruff (N806 + E501)                                                                            |
| 12  | unified-trade-exec-interface                                       | T2   | C-    | pending                           | C (76.1%, gate 72%)                 | FAILING — 40 ruff; C901 in upbit_ccxt.get_fills (complexity 13); coverage_boost.py 483 lines              |
| 13  | unified-domain-client                                              | T3   | C-    | pending                           | C (77.8%, gate 70%)                 | FAILING — 35 ruff (E501); `# pyright: reportUnknownVariableType=false` in **init**.py                     |
| 14  | execution-algo-library                                             | T0   | D     | C (0 src / 157 test)              | D (72%, gate 95%)                   | FAILING at step 1 — C901 violations block all CI; almgren_chriss 18%, sor_dex 41%                         |
| 15  | unified-config-interface                                           | T1   | D     | D (55 errors)                     | D (74.5%, below gate 77%)           | FAILING — 42 ruff; os.getenv in 3 source files (\_env_bootstrap.py, **init**.py, topology_reader.py)      |
| 16  | unified-sports-exec-interface                                      | T2   | D     | F (193 errors)                    | C (77.3%, gate 73%)                 | FAILING — 17 ruff; C901 in polymarket.py (complexity 10); gate too low at 73%                             |
| 17  | system-integration-tests                                           | int  | D     | D (97 errors)                     | F (12.4% — only HTTP endpoint hits) | FAILING — format error; no threshold set; only health-check smoke tests                                   |
| 18  | market-tick-data-service/market_tick_data_service/market_interface | T2   | F     | F (7,757 errors)                  | C (70.3%, gate 70%)                 | FAILING — 60 ruff; 14 test*coverage_boost*\* files gaming coverage; os.getenv in config.py + constants.py |

**Critical headline: 0 of 18 repos have a passing quality gate.**

---

### Per-Repo Detail

#### unified-cloud-interface (T0) — B+

| Dimension             | Grade | Finding                                                                              |
| --------------------- | ----- | ------------------------------------------------------------------------------------ |
| Coverage              | B     | 87% actual, gate only 70% — threshold needs raising to ≥85%                          |
| Basedpyright          | A     | 0 errors in source; 6k errors in autogen protobuf stubs (excluded)                   |
| Integration Tests     | C     | tests/integration/ exists but is empty — no emulator tests                           |
| VCR Tests             | C     | No moto/fake-gcs/vcrpy — only unittest.mock.patch                                    |
| Orphaned/Dup Code     | B     | `__init__.py.bak` stale; `get_logging_client()` disconnected from GCPLoggingProvider |
| Tech Debt             | B     | 24 type:ignore, 4 deprecated category params silently ignored, 2 unused noqa         |
| Dep Versions          | A     | All google-cloud-\* + boto3 current, semver bounded                                  |
| Single Responsibility | A     | Perfect T0 isolation, DataSink/EventBus pattern correct                              |
| Quality Gates         | C     | FAILING — 85 ruff errors (70×E501, 2×C901)                                           |
| Inter-repo Usage      | A     | Zero workspace imports — correct T0                                                  |

**Top fix:** 85 lint errors (70 line-length, 2 complexity). Raise coverage gate to ≥85%. Add emulator integration tests.
Wire GCPLoggingProvider into factory.

---

#### matching-engine-library (T0) — B+

| Dimension             | Grade | Finding                                                                              |
| --------------------- | ----- | ------------------------------------------------------------------------------------ |
| Coverage              | A     | 88.9%, gate 88% ✓                                                                    |
| Basedpyright          | A     | 0 errors, strict mode                                                                |
| Integration Tests     | A     | No private deps — correctly absent                                                   |
| VCR Tests             | A     | No external calls — correctly absent                                                 |
| Orphaned/Dup Code     | B     | L1/L2Matcher are NautilusTrader stubs (misleading names)                             |
| Tech Debt             | A     | Zero TODO/FIXME/type:ignore                                                          |
| Dep Versions          | A     | Zero runtime deps, stdlib only                                                       |
| Single Responsibility | A-    | Clean T0 scope; Uniswap V4 hook simulation is borderline                             |
| Quality Gates         | C     | FAILING — 3 ruff E501 (amm.py:537, trade_matcher.py:120, tests/unit/test_amm.py:210) |
| Inter-repo Usage      | A     | Zero workspace imports — correct T0                                                  |

**Top fix:** 3 line-length violations — QG exits at step 1 so type-check/test steps never run in CI.

---

#### instruments-service (T1) — B+

| Dimension             | Grade | Finding                                                                                                                       |
| --------------------- | ----- | ----------------------------------------------------------------------------------------------------------------------------- |
| Coverage              | A     | 91.4% line, branch 71% (below 80% standard)                                                                                   |
| Basedpyright          | C     | 0 src errors, 58 test errors (private method access, wrong TypedDict args)                                                    |
| Integration Tests     | A     | Mocked CCXT contract validation + import sanity tests                                                                         |
| VCR Tests             | A     | Binance + Deribit cassette replay, record_mode="none" ✓                                                                       |
| Orphaned/Dup Code     | C     | databento.py + tardis.py: every method raises NotImplementedError; backward-compat aliases InstrumentRef, CanonicalInstrument |
| Tech Debt             | B     | Source clean; backward-compat shims flagged by QG                                                                             |
| Dep Versions          | A     | All aligned; vcrpy undeclared in pyproject.toml dev deps                                                                      |
| Single Responsibility | B     | UCI/UEI used correctly, no os.getenv; UniverseSnapshot(BaseModel) should be in UAC/UIC                                        |
| Quality Gates         | C     | FAILING — 4 violations: test file 1219 lines >900 limit, 2× backward-compat shims                                             |
| Inter-repo Usage      | A     | T0-only deps; clean public API                                                                                                |

**Top fix:** Remove backward-compat shims; implement or delete NotImplementedError stub adapters; move UniverseSnapshot
to UIC.

---

#### unified-api-contracts (T0) — B

| Dimension             | Grade | Finding                                                                                                                                        |
| --------------------- | ----- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| Coverage              | B     | 81% actual, script gate 70% (misaligned — pyproject says 80%)                                                                                  |
| Basedpyright          | A     | 0 errors, 0 warnings — strict mode + reportAny ✓                                                                                               |
| Integration Tests     | A     | VCR tests serve as integration layer — appropriate for contracts lib                                                                           |
| VCR Tests             | A     | 40 VCR test files, 78 venue dirs, VCR_AUTH_STATUS.md tracking doc                                                                              |
| Orphaned/Dup Code     | C     | errors.py + errors_alt.py and cefi_extended.py + cefi_extended2.py — file-size workaround splits with #noqa:E402 mid-file imports              |
| Tech Debt             | C     | Silent pass in 4 normalizer except blocks (fail-loud violation); Kalshi deprecated cent fields past cleanup deadline; 1 type:ignore in versifi |
| Dep Versions          | A     | Only pydantic in prod; CVE overrides with GHSA citations ✓                                                                                     |
| Single Responsibility | B     | Clean T0 scope; stdlib logging in nautilus (not UEI) — acceptable at T0                                                                        |
| Quality Gates         | B     | Comprehensive 18-check QG; gate mismatch between script (70%) and pyproject (80%)                                                              |
| Inter-repo Usage      | A     | 8+ downstream consumers; no T1+ imports ✓                                                                                                      |

**Top fix:** Fix gate mismatch (script must enforce 80% not 70%); remove silent-pass except blocks; fix ruff
E501/F-undefined in binance/market_schemas.py (5 undefined name errors currently blocking QG).

---

#### unified-trading-library (T0) — B

| Dimension             | Grade | Finding                                                                                                                          |
| --------------------- | ----- | -------------------------------------------------------------------------------------------------------------------------------- |
| Coverage              | C     | 97% actual, gate 99% — fails; 5 uncovered Protocol stub branches                                                                 |
| Basedpyright          | B     | 1 error: conftest.py reportUnusedFunction on autouse fixture (false positive)                                                    |
| Integration Tests     | B     | Empty integration dir but no external calls — acceptable                                                                         |
| VCR Tests             | N/A   | No external I/O — correctly absent                                                                                               |
| Orphaned/Dup Code     | C     | LifecycleEvent exported but never instantiated on hot path; pydantic+python-dateutil declared as deps but not imported in source |
| Tech Debt             | A     | Zero TODO/FIXME/type:ignore                                                                                                      |
| Dep Versions          | B     | Versions match but phantom deps wasteful                                                                                         |
| Single Responsibility | A     | Clean 3-file T0 boundary                                                                                                         |
| Quality Gates         | D     | FAILING: coverage 97%<99%; REPO_ARCH_TIER defaults to "library" not "0" → tier-0 violation checks never run in CI                |
| Inter-repo Usage      | A     | Correctly used across 20+ services; zero upstream deps                                                                           |

**Top fix:** Wire REPO_ARCH_TIER="0" from pyproject.toml into QG script. Remove phantom pydantic runtime dep. Cover 5
Protocol stub branches to reach 99%.

---

#### position-balance-monitor-service (T2) — B

| Dimension             | Grade | Finding                                                                                          |
| --------------------- | ----- | ------------------------------------------------------------------------------------------------ |
| Coverage              | B     | 84% actual, gate 70% — passes but threshold needs raising to ≥80%                                |
| Basedpyright          | A     | 0 errors in source; 30 in test files (excluded from pyrightconfig)                               |
| Integration Tests     | B     | 6-venue adapter + VCR schema validation tests                                                    |
| VCR Tests             | B     | Cassettes for 6 venues; position/balance cassette gaps acknowledged                              |
| Orphaned/Dup Code     | B     | IBKR + Upbit stubs not registered in factory (unreachable); Canonical\* schemas should be in UIC |
| Tech Debt             | A     | Zero TODO/FIXME/type:ignore in source                                                            |
| Dep Versions          | A     | Single runtime dep (UIC), perfectly aligned                                                      |
| Single Responsibility | B     | Clean scope; locally-defined Canonical\* schemas are minor violation                             |
| Quality Gates         | C     | FAILING — fail_under=70 too low; hardcoded absolute path in VCR test breaks CI                   |
| Inter-repo Usage      | A     | Only UIC as runtime dep — perfect T2 tier compliance                                             |

**Top fix:** Raise coverage gate to ≥80%; fix hardcoded path in VCR test; move Canonical\* schemas to UIC.

---

#### unified-api-contracts internal subpackage (T0) — C+

| Dimension             | Grade | Finding                                                                                                                                                  |
| --------------------- | ----- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Coverage              | A     | 100% actual, gate 99% ✓                                                                                                                                  |
| Basedpyright          | D     | 56 errors in schema_definition.py:from_dict() — iterates dict[str, object], so col["name"]/.items()/etc. all fail; type:ignore only partially suppresses |
| Integration Tests     | B     | tests/integration/test_uac_integration.py — validates UAC contract compatibility                                                                         |
| VCR Tests             | N/A   | Pure schemas/contracts — correctly absent                                                                                                                |
| Orphaned/Dup Code     | B     | Rich domain/ structure (15 dirs); tests/test_coverage_gaps.py has 22 type:ignore (coverage gaming flag)                                                  |
| Tech Debt             | C     | 4 type:ignore in schema_definition.py; test_coverage_gaps.py name suggests gaming                                                                        |
| Dep Versions          | A     | Minimal: pydantic + pandas + UAC — lean and correct                                                                                                      |
| Single Responsibility | A     | SSOT for internal schemas; clean domain subdirectory structure                                                                                           |
| Quality Gates         | D     | FAILING — type-check step fails on schema_definition.py                                                                                                  |
| Inter-repo Usage      | A     | Only T0 deps (UAC) — correct tier placement                                                                                                              |

**Root cause of 56 errors:** `from_dict()` parameter is `data: dict[str, object]`. Pyright sees `col` as `object` when
iterating, so `col["name"]`, `col.get("nullable_overrides")`, `.items()` all fail. Fix: introduce `_RawColumn` and
`_RawSchema` TypedDicts — all type:ignore comments can then be removed.

---

#### unified-trading-library (T2) — C+

| Dimension             | Grade | Finding                                                                                                      |
| --------------------- | ----- | ------------------------------------------------------------------------------------------------------------ |
| Coverage              | A     | 92.6% actual vs 93% gate — marginally failing threshold                                                      |
| Basedpyright          | D     | 23 errors in src; bypass audit falsely claims "0 errors resolved 2026-03-07" (stale entry)                   |
| Integration Tests     | A     | Pure math — no private deps, not applicable                                                                  |
| VCR Tests             | A     | No HTTP calls — correctly absent                                                                             |
| Orphaned/Dup Code     | B     | 6 of 8 feature services don't consume this library; features-delta-one has own duplicate resample_features() |
| Tech Debt             | B     | Stale bypass audit entry; dead exception branches (network exceptions in pure math library)                  |
| Dep Versions          | A     | numpy/pandas/scipy/sklearn all current                                                                       |
| Single Responsibility | A     | Clean T2 math scope — no cloud, no os.getenv ✓                                                               |
| Quality Gates         | D     | FAILING at step 1 — 1×E501 in base.py; base.py 908 lines >900 limit; steps 3–6 never run                     |
| Inter-repo Usage      | C     | Only 2 of 8 feature services consume it — consolidation goal not realized                                    |

**Top fix:** Fix 1 E501 in base.py to unblock CI. Update stale bypass audit. Get 6 remaining feature services to consume
this library.

---

#### unified-ml-interface (T2) — C+

| Dimension             | Grade | Finding                                                                                                                         |
| --------------------- | ----- | ------------------------------------------------------------------------------------------------------------------------------- |
| Coverage              | A     | 92.1% line, 84% branch; passes 91% gate ✓                                                                                       |
| Basedpyright          | D     | 38 errors in production source (dict.get() returns object, unnarrowed before arithmetic)                                        |
| Integration Tests     | B     | MockCloudService-backed integration tests — structurally sound                                                                  |
| VCR Tests             | N/A   | No HTTP — all GCS via UCI mock                                                                                                  |
| Orphaned/Dup Code     | D     | PredictionSnapshot + CascadeConfig duplicated in both UMI and UIC — deprecation notice exists but unresolved; pyyaml dep unused |
| Tech Debt             | C     | 1 type:ignore in source; stale bypass audit entries; duplication tracked but unfixed                                            |
| Dep Versions          | B     | Versions aligned; pyyaml phantom dep                                                                                            |
| Single Responsibility | B     | ModelRegistry doing GCS I/O in an "interface" lib is borderline; no os.getenv ✓                                                 |
| Quality Gates         | C     | FAILING — 12 ruff (C901 in get_model_metadata complexity 11, 2×E501)                                                            |
| Inter-repo Usage      | B     | Correct T0/T1 deps; no log_event calls — ML lifecycle events go to stdlib logging only, not UEI                                 |

**Top fix:** Complete PredictionSnapshot/CascadeConfig migration from UMI → UIC (already planned). Fix 12 ruff errors.
Wire ML lifecycle events through UEI.

---

#### unified-trading-library (T1) — C

| Dimension             | Grade | Finding                                                                                     |
| --------------------- | ----- | ------------------------------------------------------------------------------------------- |
| Coverage              | C     | 76.1% actual, gate 70% (threshold too low, near-miss not flagged)                           |
| Basedpyright          | D     | 391 errors — mostly pandas/cloud SDK stub gaps                                              |
| Integration Tests     | B     | tests/integration/ has cloud correctness + dep integration tests                            |
| VCR Tests             | C     | No VCR; integration tests mock via UCI                                                      |
| Orphaned/Dup Code     | B     | cloud_storage_service.py + cloud_pubsub_service.py deleted ✓ (Session 12)                   |
| Tech Debt             | C     | os.environ in tracing.py (4×) — should use UnifiedCloudConfig; python-dotenv dep suspicious |
| Dep Versions          | B     | Lean but python-dotenv + web3 are heavy; versions aligned                                   |
| Single Responsibility | B     | cloud_base_service.py correctly uses UCI ✓; tracing.py has os.environ violations            |
| Quality Gates         | F     | FAILING — 87 ruff errors blocked at lint step; E501 in id_conventions.py                    |
| Inter-repo Usage      | B     | Uses UCI + UIC correctly; os.environ leaks in non-bootstrap code                            |

**Top fix:** 87 ruff errors blocking all CI. Replace os.environ in tracing.py with UnifiedCloudConfig. Raise coverage
gate to ≥80%. reportAny must be "error" not "none" in pyrightconfig.json.

---

#### unified-defi-exec-interface (T2) — C

| Dimension             | Grade | Finding                                                                     |
| --------------------- | ----- | --------------------------------------------------------------------------- |
| Coverage              | B     | 88.8%, gate 88% — passes by 0.8% margin                                     |
| Basedpyright          | D     | 133 errors (mostly in tests: MagicMock.assert_called_once is Any)           |
| Integration Tests     | B     | test_uic_integration.py validates UIC contract compatibility                |
| VCR Tests             | B     | test_vcr_defi_schemas.py with cassettes                                     |
| Orphaned/Dup Code     | B     | Clean DeFi scope; no schema overlap post UAC thegraph/schemas migration     |
| Tech Debt             | C     | 5 os.getenv in test code; 6 type:ignore; N806 variable naming               |
| Dep Versions          | A     | Single runtime dep (UIC), minimal                                           |
| Single Responsibility | A     | SWAP/LEND/BORROW/STAKE scope — clean                                        |
| Quality Gates         | F     | FAILING — 4 ruff (N806 ConnectorClass naming + 1 E501 in protocols/base.py) |
| Inter-repo Usage      | A     | Only UIC as runtime dep — correct T2                                        |

**Top fix:** Fix N806 naming violation + 1 E501 to unblock QG. Fix 133 pyright errors in test mock usage.

---

#### unified-trade-exec-interface (T2) — C-

| Dimension             | Grade   | Finding                                                                         |
| --------------------- | ------- | ------------------------------------------------------------------------------- |
| Coverage              | C       | 76.1% actual, gate 72% — passes but threshold below 80% standard                |
| Basedpyright          | pending | Agent was still running when audit completed                                    |
| Integration Tests     | B       | test_account_queries, test_l1_orderbook_integration, test_vcr_schema_validation |
| VCR Tests             | C       | test_vcr_schema_validation.py exists but no cassettes/ directory                |
| Orphaned/Dup Code     | D       | tests/test_coverage_boost.py — 483-line coverage gaming file                    |
| Tech Debt             | B       | No os.getenv in source, no type:ignore found                                    |
| Dep Versions          | B       | UAC, UEI, UCI + ccxt, aiohttp, ib_insync — well-bounded versions                |
| Single Responsibility | B       | Uses proper workspace interfaces; ib_insync scope appropriate                   |
| Quality Gates         | F       | FAILING — 40 ruff; C901 in upbit_ccxt.get_fills (complexity 13)                 |
| Inter-repo Usage      | B       | Uses UAC, UEI, UCI — correct T2 dependencies                                    |

**Top fix:** Delete tests/test_coverage_boost.py (coverage gaming). Fix C901 complexity in upbit_ccxt. Add actual VCR
cassettes.

---

#### unified-domain-client (T3) — C-

| Dimension             | Grade   | Finding                                                                                        |
| --------------------- | ------- | ---------------------------------------------------------------------------------------------- |
| Coverage              | C       | 77.8% actual, gate 70% — passes but gate too low                                               |
| Basedpyright          | pending | Agent still running                                                                            |
| Integration Tests     | D       | No tests/integration/ directory at all — T3 cloud aggregator with no integration tests         |
| VCR Tests             | D       | No VCR — cloud aggregation calls never cassette-tested                                         |
| Orphaned/Dup Code     | B       | Rich domain/ structure; BigQueryCatalog/GlueCatalog co-exist without clear routing             |
| Tech Debt             | C       | `# pyright: reportUnknownVariableType=false` at top of **init**.py suppresses errors file-wide |
| Dep Versions          | B       | Full T0-T3 dependency chain; pandas-stubs in dev ✓                                             |
| Single Responsibility | B       | Domain client scope; StandardizedDomainCloudService naming leaks cloud intent                  |
| Quality Gates         | F       | FAILING — 35 ruff (E501 in validation.py); pyright suppression directive                       |
| Inter-repo Usage      | A       | Depends on UAC, UCI, UEI, UIC, UTL — all within T0-T1 boundary ✓                               |

**Top fix:** Add integration tests. Fix 35 ruff errors. Remove file-level pyright suppression directive.

---

#### execution-algo-library (T0) — D

| Dimension             | Grade | Finding                                                                                 |
| --------------------- | ----- | --------------------------------------------------------------------------------------- |
| Coverage              | D     | 72% actual vs 95% threshold — catastrophic gap. almgren_chriss.py 18%, sor_dex.py 41%   |
| Basedpyright          | C     | 0 errors in source; 157 errors in test files (untyped fixtures, private member access)  |
| Integration Tests     | A     | No private deps — correctly absent                                                      |
| VCR Tests             | A     | No external calls — correctly absent                                                    |
| Orphaned/Dup Code     | B     | Clean algo domain, no overlap with MEL                                                  |
| Tech Debt             | C     | 4 C901 complexity violations (complexity 8–14 vs max 7), not documented in bypass audit |
| Dep Versions          | A     | Lean stdlib + pydantic only, aligned                                                    |
| Single Responsibility | A     | Perfect T0 scope — pure computation                                                     |
| Quality Gates         | F     | FAILING at step 1/6 — C901 violations block ruff --fix; all downstream gates never run  |
| Inter-repo Usage      | A     | Zero T1+ imports — correct                                                              |

**Top fix:** Fix 4 C901 complexity violations (or document in QUALITY_GATE_BYPASS_AUDIT.md) to unblock CI. Then address
72% vs 95% coverage gap.

---

#### unified-config-interface (T1) — D

| Dimension             | Grade | Finding                                                                           |
| --------------------- | ----- | --------------------------------------------------------------------------------- |
| Coverage              | D     | 74.5% actual, gate 77% — fails its own threshold                                  |
| Basedpyright          | D     | 55 errors (mostly in tests — topology_reader.py: os.environ is Any)               |
| Integration Tests     | B     | test_unified_cloud_config.py for Secret Manager integration                       |
| VCR Tests             | B     | VCR present for config fetch mocking                                              |
| Orphaned/Dup Code     | B     | Config loading duplicates UCI Secret Manager calls in 2 places                    |
| Tech Debt             | C     | os.getenv in \_env_bootstrap.py, **init**.py, topology_reader.py — 3 source files |
| Dep Versions          | B     | pydantic + pydantic-settings + UEI + UCI — reasonable; aws optional dep           |
| Single Responsibility | B     | T1→T0 dep structure correct; UCI present ✓                                        |
| Quality Gates         | F     | FAILING — 42 ruff errors; coverage below its own gate                             |
| Inter-repo Usage      | B     | T0-only runtime deps; correctly provides UnifiedCloudConfig                       |

**Top fix:** 42 E501 errors blocking CI. Remove os.getenv from 3 source files — use UnifiedCloudConfig/SecretManager.
Fix coverage to ≥77%.

---

#### unified-sports-exec-interface (T2) — D

| Dimension             | Grade | Finding                                                                               |
| --------------------- | ----- | ------------------------------------------------------------------------------------- |
| Coverage              | C     | 77.3% actual, gate 73% — passes but gate below 80% standard                           |
| Basedpyright          | F     | 193 errors (dict[Unknown, Unknown] throughout from untyped betfairlightweight lib)    |
| Integration Tests     | A     | tests/integration/ with VCR cassettes                                                 |
| VCR Tests             | A     | cassettes/ dir + test_vcr_betting_exchange_schemas.py ✓                               |
| Orphaned/Dup Code     | B     | Clean sports scope                                                                    |
| Tech Debt             | C     | 5 TODO/FIXME; os.getenv in polymarket.py source (6 calls)                             |
| Dep Versions          | B     | Betfairlightweight, playwright, aioresponses — reasonable; all bounded                |
| Single Responsibility | B     | Sports betting execution scope; polymarket normalize function too complex (C901 10>7) |
| Quality Gates         | F     | FAILING — 17 ruff/C901; polymarket.py normalize_polymarket_market complexity 10>7     |
| Inter-repo Usage      | A     | Only UAC as runtime dep — correct T2                                                  |

**Top fix:** 193 pyright errors from untyped betfairlightweight — add stubs or cast at adapter boundary. Fix C901 in
polymarket.py. Remove os.getenv.

---

#### system-integration-tests — D

| Dimension             | Grade | Finding                                                                                               |
| --------------------- | ----- | ----------------------------------------------------------------------------------------------------- |
| Coverage              | F     | 12.4% — only HTTP endpoint hits register; no real library integration coverage                        |
| Basedpyright          | D     | 97 errors (test_pipeline_smoke.py: httpx response types all Unknown)                                  |
| Integration Tests     | D     | Only Layer 3a health-check smoke tests + empty Layer 3b stubs; no actual T0-T3 cross-repo integration |
| VCR Tests             | D     | VCR mentioned in code but no cassettes present                                                        |
| Orphaned/Dup Code     | B     | Small codebase, no duplication                                                                        |
| Tech Debt             | C     | 5 TODO/FIXME; no coverage threshold set; line-length=120 (non-standard vs workspace 100)              |
| Dep Versions          | B     | Only httpx + pytest in prod — minimal                                                                 |
| Single Responsibility | C     | Should validate T0-T3 interactions; currently only tests API health endpoints                         |
| Quality Gates         | F     | FAILING — format error (system_integration_tests dir not found); no proper QG setup                   |
| Inter-repo Usage      | F     | No T0-T3 library imports — SIT never exercises the library tier                                       |

**Top fix:** SIT must import and exercise T0-T3 libraries directly, not just call API health endpoints. Fix format
error. Add proper coverage threshold.

---

#### market-tick-data-service/market_tick_data_service/market_interface (T2) — F

| Dimension             | Grade | Finding                                                                                    |
| --------------------- | ----- | ------------------------------------------------------------------------------------------ |
| Coverage              | C     | 70.3% actual, gate 70% — passes by 0.3%; 14 test*coverage_boost*\* files inflating numbers |
| Basedpyright          | F     | 7,757 errors — worst in workspace; ccxt + web3 lack type stubs                             |
| Integration Tests     | B     | tests/integration/ with VCR schema tests                                                   |
| VCR Tests             | B     | test_vcr_ac_schema_validation.py present                                                   |
| Orphaned/Dup Code     | C     | Sports adapter module that delegates to USEI (borderline duplication)                      |
| Tech Debt             | D     | os.getenv in config.py + constants.py; 14 coverage_boost test files (gaming)               |
| Dep Versions          | B     | ccxt, web3, databento, yfinance, polars — all bounded                                      |
| Single Responsibility | C     | 24-venue scope is large; os.getenv violates config standard                                |
| Quality Gates         | F     | FAILING — 60 ruff errors; coverage gaming via 14 test*coverage_boost*\* files              |
| Inter-repo Usage      | B     | Correct UAC/UCI/UEI/UIC deps — no T2 upward violations                                     |

**Top fix:** Delete 14 test*coverage_boost*\* files (coverage gaming). Remove os.getenv from config.py/constants.py. Add
ccxt + web3 stubs or add targeted pyright suppressions with bypass audit entries to reduce 7,757 errors.

---

## PART 2 — CROSS-CUTTING FINDINGS

### Systemic Issue 1 — Quality Gates: 0 of 18 repos pass (CRITICAL)

Every single repo fails its quality gate. The QG system exists but CI has no passing foundation. Root causes by
frequency:

- E501 line-length violations — present in 12/18 repos
- C901 complexity violations — present in 5/18 repos (EAL, USEI, UTEI, UMI, UFCL)
- Coverage below threshold — 4/18 repos (EAL, UCI, UFCL, UAC by gate mismatch)
- Type-check failures — 3/18 repos (UIC, UTL, UCI)

### Systemic Issue 2 — Coverage Gates Too Low

11 of 18 repos have gates below 80%. The workspace standard requires ≥80% but most repos were set to 70-73% "to pass
quickly." Repos needing gate raises:

- unified-cloud-interface (70% → 85%), position-balance-monitor-service (70% → 80%), unified-defi-exec-if (88% threshold
  is fine but margin is thin), unified-domain-client (70% → 80%), unified-trade-exec-if (72% → 80%),
  unified-sports-exec-if (73% → 80%), market-tick-data-service/market_tick_data_service/market_interface (70% → 80%),
  unified-trading-library (70% → 80%), unified-domain-client (70% → 80%)

### Systemic Issue 3 — Coverage Gaming

Three repos contain test files designed to inflate coverage without meaningful tests:

- `market-tick-data-service/market_tick_data_service/market_interface`: 14 test_coverage_boost_umi\*.py files
- `unified-trade-exec-interface`: tests/test_coverage_boost.py (483 lines)
- `unified-api-contracts (internal/)`: internal/tests/unit/test_coverage_gaps.py (the file itself is legitimate coverage
  gap filling, but 22 type:ignore[union-attr] calls indicate the root issue is a TypedDict fix in schema_definition.py,
  not a test problem)

### Systemic Issue 4 — Basedpyright Errors in T1-T2

Only T0 repos have clean pyright (MEL, UCI, UAC have 0 errors). T1-T2 accumulate:

- market-tick-data-service/market_tick_data_service/market_interface: 7,757 (ccxt + web3 no stubs)
- unified-trading-library: 391 (pandas stubs incomplete)
- unified-sports-exec-if: 193 (betfairlightweight no stubs)
- unified-defi-exec-if: 133 (mock method access)
- unified-ml-interface: 38 (dict.get() unnarrowed)
- unified-trading-library: 23 (stale bypass audit false claim)
- unified-config-interface: 55 (os.environ Any propagation)
- unified-api-contracts (internal/): 56 (schema_definition.py TypedDict fix needed)

### Systemic Issue 5 — Schema Duplication

- `PredictionSnapshot` + `CascadeConfig` exist in both unified-ml-interface and `unified_api_contracts.internal`
  (documented, unresolved)
- `Canonical*` types defined locally in position-balance-monitor-service (should be in `unified_api_contracts.internal`)
- `UniverseSnapshot(BaseModel)` in instruments-service (should be in UAC canonical or `unified_api_contracts.internal`)

### Systemic Issue 6 — REPO_ARCH_TIER Not Wired

unified-trading-library (T0) has REPO_ARCH_TIER defaulting to "library" in QG script — tier-0 violation checks never run
in CI. This means upward-import checks that should enforce T0 isolation never execute. Affects UEI and potentially other
T0 repos.

---

## PART 3 — POST-AUDIT FIX COMMIT ANALYSIS

The following fix commits landed after the audit was captured (via `git log --oneline`):

| Repo                                                               | Fix Commit                                                                                     | Coverage                                                                 |
| ------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| unified-api-contracts                                              | `419627a fix: resolve QG violations`                                                           | Likely fixes ruff; 5 undefined-name binance errors may remain            |
| unified-api-contracts (internal/)                                  | `fa9e7e0 fix: resolve QG violations - coverage/lint/type/compliance`                           | schema_definition.py errors may still be present (TypedDict fix complex) |
| unified-cloud-interface                                            | `88286fc fix: resolve QG violations - aws.py type errors and test failures`                    | Partial fix; 85 ruff errors likely reduced                               |
| unified-config-interface                                           | `ab2ab37 fix: resolve QG violations - type/compliance`                                         | Type fixes; 42 E501 violations may remain                                |
| execution-algo-library                                             | `a259570 fix: update before downstream merge`                                                  | C901 status unknown; coverage gap likely unchanged                       |
| matching-engine-library                                            | `d30cc28 fix: update before downstream merge`                                                  | 3 E501 status unknown                                                    |
| market-tick-data-service/market_tick_data_service/market_interface | `be3f1d5 fix: resolve QG violations - F401 unused imports` + `baffc15 fix: failing tests/lint` | Partial; 7,757 pyright errors unchanged                                  |
| unified-trade-exec-interface                                       | `b940daa fix: resolve QG violations - coverage`                                                | Coverage improved; C901 in upbit_ccxt status unknown                     |
| position-balance-monitor-service                                   | `d9f3d91 fix: resolve QG violations - lint/format`                                             | Likely green                                                             |
| unified-sports-exec-interface                                      | `0342b2a fix: resolve QG violations - lint/format`                                             | Likely partial; 193 pyright errors unchanged                             |
| unified-trading-library                                            | `a107088 fix: resolve QG violations - coverage/lint/type/compliance`                           | Likely fixed 1 E501 blocker                                              |
| unified-domain-client                                              | `6ac1669 fix: resolve QG violations - coverage/lint`                                           | Likely partial                                                           |
| instruments-service                                                | `37a5e5c fix: resolve QG violations - basedpyright import resolution and lint`                 | Import resolution fixed; 4 QG violations may remain                      |
| unified-trading-library                                            | `31c882e fix: resolve QG violations` + `631f028 fix: remove T2 optional deps`                  | 87 ruff likely reduced; 391 pyright errors unchanged                     |

**Assessment:** Most repos received partial QG fixes. The deeper issues (high pyright error counts, coverage gaming
files, schema duplication) are architectural and not addressed by `fix:` commits.

---

## PART 4 — HARD RESET ANALYSIS

Checked reflog for destructive operations across key repos:

| Repo                              | Reset Type                                         | Assessment                                                                     |
| --------------------------------- | -------------------------------------------------- | ------------------------------------------------------------------------------ |
| unified-api-contracts             | `reset: moving to HEAD` (×3)                       | No-op / safe — HEAD unchanged                                                  |
| unified-api-contracts (internal/) | `reset: moving to origin/main` (×3 in reflog)      | Historical — all happened before current fix commits; no in-progress work lost |
| matching-engine-library           | `reset: moving to origin/main` (×3 in reflog)      | Historical — before current fix commits; no work lost                          |
| execution-algo-library            | `reset: moving to HEAD` + `origin/main` (multiple) | Historical; current HEAD is fix commit on top of reset point                   |

**Conclusion:** Hard resets to `origin/main` occurred in the unified-api-contracts internal subpackage and
matching-engine-library but these were sync operations (likely `git pull` followed by `git reset --hard origin/main`).
All occurred prior to subsequent `fix:` commits, confirming no in-progress work was destroyed. The MEMORY.md rule
("NEVER run git reset --hard without explicit user confirmation") was not violated by recent sessions — the resets in
reflog predate the fix commit chain.

---

## PART 5 — WORKSPACE-LEVEL AUDIT (10 Categories)

Separate 10-agent audit covering workspace governance, not per-repo code quality.

### §1 Workspace Manifest — 10 PASS / 5 FAIL

| Finding                                                                                     | Status |
| ------------------------------------------------------------------------------------------- | ------ |
| `execution_service/` orphan directory on disk (removed from manifest but not deleted)       | FAIL   |
| `unified-api-contracts` manifest version 0.1.20 vs pyproject.toml 0.1.52 (32 patches stale) | FAIL   |
| `unified-trading-pm` at version 1.2.0 violates pre-stable policy                            | FAIL   |
| 6 repos with wrong `doc_standard` field vs their `type`                                     | FAIL   |
| All other criteria pass                                                                     | PASS   |

### §2 Tier Architecture — 12 PASS / 1 FAIL

| Finding                                               | Status |
| ----------------------------------------------------- | ------ |
| `WORKSPACE_MANIFEST_DAG.svg` does not exist           | FAIL   |
| All tier DAG constraints enforced — T0→T1→T2→T3 clean | PASS   |
| No service-to-service Python imports                  | PASS   |
| All 11 UI repos are TypeScript-only                   | PASS   |

### §3 SSOT Enforcement — 10 PASS / 4 FAIL

| Finding                                                                                      | Status |
| -------------------------------------------------------------------------------------------- | ------ |
| 60 of 95 files referenced in `00-SSOT-INDEX.md` do not exist                                 | FAIL   |
| 36 duplicate schema/config classes across repos                                              | FAIL   |
| `UnifiedCloudServicesConfig` still exported from UTL alongside `UnifiedCloudConfig` from UCI | FAIL   |
| Same config class naming issue in UTL pyproject.toml and tests                               | FAIL   |
| Cursor rules correctly symlinked; runtime-topology SSOT synchronized                         | PASS   |

### §4 Dependency Governance — 10 PASS / 2 WARN

| Finding                                                                           | Status |
| --------------------------------------------------------------------------------- | ------ |
| 14 packages used across 7 repos not in `workspace-constraints.toml` and unbounded | WARN   |
| `rich` has anomalously wide bound `<16.0.0` (should be `<15.0.0`)                 | WARN   |
| All 47 repos have `uv.lock`; `uv` enforced as package manager                     | PASS   |

### §5 Documentation + Cloud Isolation — 6 PASS / 8 FAIL

| Finding                                                                                                                            | Status |
| ---------------------------------------------------------------------------------------------------------------------------------- | ------ |
| **HARD GATE:** 30+ direct `google.cloud.*`/`boto3` imports in deployment-service backends outside UCI                              | FAIL   |
| **HARD GATE:** `execution-service/execution_service/utils/gcs_service.py` exposes `gcs_bucket=`, `bigquery_dataset=` in production | FAIL   |
| deployment-service has 5 stub docs (≤16 lines each)                                                                                | FAIL   |
| settlement-ui has 2 stub docs                                                                                                      | FAIL   |
| Hardcoded bucket names in docs (`gs://execution-store-cefi-project`)                                                               | FAIL   |

### §6 Cursor Rules — 9 PASS / 1 FAIL / 2 WARN

| Finding                                                                                              | Status |
| ---------------------------------------------------------------------------------------------------- | ------ |
| `codex-maintenance.mdc` has `alwaysApply: true` + glob constraint simultaneously — semantic conflict | FAIL   |
| 4 supplementary rules missing `priority:` field                                                      | WARN   |
| 2 emergency scripts with force-push (documented exceptions)                                          | WARN   |
| All 8 blocking rules (priority ≥90) present with correct CODEX references                            | PASS   |

### §7 Codex vs Code — 10 PASS / 4 FAIL

| Finding                                                                                     | Status |
| ------------------------------------------------------------------------------------------- | ------ |
| `generate-per-service-specs.py` uses deprecated event name `INGESTING_DATA`                 | FAIL   |
| `UnifiedCloudServicesConfig` still defined and exported by UTL                              | FAIL   |
| `unified-api-contracts` ruff check fails — 5 undefined names in `binance/market_schemas.py` | FAIL   |
| AC/UIC refactor Phase 9 QG still blocked                                                    | FAIL   |
| No hardcoded bucket names in production code; Dockerfiles correct; repo names current       | PASS   |

### §8 Linting & Quality Gates — 13 PASS / 5 WARN / 2 FAIL

| Finding                                                                                                                         | Status |
| ------------------------------------------------------------------------------------------------------------------------------- | ------ |
| E722 globally ignored in 4 repos: instruments-service, execution-algo-library, unified-trading-codex, risk-and-exposure-service | FAIL   |
| 32+ `\|\| true` instances in `cloudbuild.yaml`/`buildspec.aws.yaml` cleanup steps                                               | FAIL   |
| execution-service uses 120-char line length (non-standard)                                                                      | WARN   |
| 2/6 sample repos missing `typeCheckingMode: "strict"`                                                                           | WARN   |

### §9 Type Safety — 5 PASS / 4 WARN / 2 FAIL

| Finding                                                                                                                | Status |
| ---------------------------------------------------------------------------------------------------------------------- | ------ |
| `unified-trading-pm/codex/pyrightconfig.json` uses `"basic"` mode — the standards repo is not strict                   | FAIL   |
| `unified-trading-library/pyrightconfig.json` sets `reportAny: "none"` — nullifies enforcement for foundational library | FAIL   |
| 0 instances of `typing.List`/`typing.Dict` — PEP 585 built-ins used everywhere                                         | PASS   |
| 80 Protocol definitions for duck typing                                                                                | PASS   |

### §10 Security & Secrets — 8 PASS / 6 WARN / 1 FAIL

| Finding                                                                                                                                             | Status |
| --------------------------------------------------------------------------------------------------------------------------------------------------- | ------ |
| 5 `.env` files tracked in git: deployment-service, unified-trading-library, strategy-service, trading-analytics-ui, archive/execution-visualizer-ui | FAIL   |
| `execution_service/utils/gcs_service.py` uses raw `os.getenv()` for bucket/dataset names                                                            | WARN   |
| `deployment-service/.env` contains hardcoded project ID `central-element-323112` tracked in git                                                     | WARN   |
| f-string SQL queries in ml-training/ml-inference (config-based values; nosec comments present)                                                      | WARN   |
| No `verify=False`; all API endpoints authenticated; Swagger disabled in production                                                                  | PASS   |

---

## PART 6 — PRIORITY REMEDIATION ORDER

### P0 — Unblock CI (all-repo impact)

1. **Fix 1 E501 in unified-trading-library/base.py** — unblocks steps 3–6 of QG
2. **Fix 4 C901 violations in execution-algo-library** or document in BYPASS_AUDIT — QG exits at step 1
3. **Fix E501/C901 in matching-engine-library (3 lines)** — QG blocked at step 1
4. **Fix 5 undefined names in unified-api-contracts/binance/market_schemas.py** — QG blocked
5. **Fix gcs_bucket=/bigquery_dataset= in execution-service/utils/gcs_service.py** — Cloud Isolation Hard Gate
6. **Remove google.cloud/boto3 imports from deployment-service backends** — Cloud Isolation Hard Gate
7. **Convert 5 .env files to .env.example** — Security

### P1 — Foundational Quality

8. **Fix schema_definition.py TypedDict in UIC** — eliminates 56 pyright errors and QG type-check failure in the T0
   contract SSOT
9. **Raise coverage gates to ≥80%** across 11 repos
10. **Delete 14 test*coverage_boost*\* files in market-tick-data-service/market_tick_data_service/market_interface**
11. **Delete tests/test_coverage_boost.py in unified-trade-exec-interface** (483 lines)
12. **Fix 60 lint errors in unified-trading-codex** to unblock SSOT-INDEX accuracy
13. **Wire REPO_ARCH_TIER="0" in unified-trading-library QG script** — tier-0 violation checks currently skip
14. **Sync unified-api-contracts manifest version** from 0.1.20 to 0.1.52
15. **Delete orphan `execution_service/` directory** from workspace root

### P2 — Type Safety + Architecture

16. **Fix `unified-trading-pm/codex/pyrightconfig.json`** — change `"basic"` to `"strict"`, add `reportAny: "error"`
17. **Fix `unified-trading-library/pyrightconfig.json`** — change `reportAny` from `"none"` to `"error"`; add explicit
    bypass audit entries for 40 documented cases
18. **Complete PredictionSnapshot/CascadeConfig migration** from UMI → UIC
19. **Remove UnifiedCloudServicesConfig from UTL** — migrate all usages to UCI's UnifiedCloudConfig
20. **Sync SSOT-INDEX.md** — create or register the 60 missing referenced files

### P3 — Tech Debt Reduction

21. **Add 14 missing packages to workspace-constraints.toml** with proper upper bounds
22. **Fix `codex-maintenance.mdc`** — remove `alwaysApply: true` or remove glob constraint (semantic conflict)
23. **Update `generate-per-service-specs.py`** event name: `INGESTING_DATA` → `DATA_INGESTION_STARTED`
24. **Add 6 feature services as UFCL consumers** — remove local resample_features() duplicates
25. **Replace os.getenv in UTL tracing.py, UMI config, and UCI source files** with UnifiedCloudConfig

---

## Overall Assessment

**Tier grades:** T0 average B, T1 average C+, T2 average C, T3 C-

**Overall tier grade: C — The foundation libraries (T0) are in better shape (B average), but T1–T2 degrade sharply, and
the quality gate system is broken everywhere. The single most urgent fix is that 0 of 18 repos have a passing quality
gate — the CI equivalent of having no safety net.**
