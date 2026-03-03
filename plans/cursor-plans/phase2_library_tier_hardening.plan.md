---
name: Phase 2 — Library Tier Hardening
overview: |
  Hardens all library tiers (T0→T1→T2→T3) to fully green quality gates.
  REQUIRES Phase 1 complete (quickmerge template + CI/CD live across all repos).

  ## Execution Meta-Flow

  Each tier follows the same step sequence — do NOT skip or reorder:

  - **Step A**: Deploy Structure — CI/CD wiring, QG config, pyproject.toml, .dependency-matrix.json
  - **Step B**: Tests First — write/fix tests before any code rewrite
  - **Step C**: Code Rewrite — implement todos, fix violations, restructure
  - **Step D1**: `quickmerge --lint-only` — fastest feedback (syntax, import ordering, formatting)
  - **Step D2**: `quickmerge --unit-only` — import errors, type errors, unit tests
  - **Step D3**: `quickmerge --qg-only` — full QG, no git ops (integration test failures, coverage gaps)
  - **Step D4**: `quickmerge --quick` — full QG + git ops, skip act simulation
  - **Step D5**: `quickmerge` (no flags) — full with act simulation; **TIER GREEN GATE**

  ## INVARIANT

  **Never touch tier N until tier N-1 is fully green (all D5 passes).**
  > **Tier disambiguation:** "T0/T1/T2/T3" here = library architecture tiers (code dependency depth). Separate from workspace-manifest.json `merge_level` (CI/CD cascade order, L0–L10 as of 2026-02-28 restructure). Do not confuse the two.
  T0 repos must ALL pass D5 before any T1 work starts.
  T0 + T1 must both be green before any T2 work starts.
  T0 + T1 + T2 must all be green before T3 work starts.

  ## Progressive Validation

  D1 catches the fastest-failing issues (formatting, import order) and is nearly free.
  D2 adds unit tests and type checking — catches import-time errors early.
  D3 runs integration tests and coverage analysis without touching git — safe to retry.
  D4 runs everything plus git staging/branch ops but skips act (Cloud Build simulation).
  D5 is the full pipeline including act simulation — the only gate that counts for tier promotion.

  ## Integration Layer 0

  Contract alignment tests (Layer 0 of the 4-layer integration testing strategy) run during
  **T0 STEP B**. These are the AC↔UIC schema pair tests and must pass before any T1 work begins.
  See `.cursor/rules/integration-testing-layers.mdc` for the full 4-layer strategy.

  ## Cross-References

  - Phase 1: `phase1_foundation_prep.plan.md` — prerequisite
  - Phase 3: `phase3_service_hardening_integration.plan.md` — follows this phase (T4–T6 services)
---

## NAMING CHANGE MANDATE — Zero Technical Debt

> **No shortcut renames.** When any library, package, or import path changes, the change is COMPLETE only when every level below is updated. This applies to any renames that surface during T0–T3 hardening (e.g., package name changes in UTS, UDC dual-publish rename).

| Level                                     | What to Change                                                                            |
| ----------------------------------------- | ----------------------------------------------------------------------------------------- |
| **`pyproject.toml` `name`**               | Must match canonical name in `workspace-manifest.json`                                    |
| **Python package directory**              | Rename the source dir; update all `__init__.py`                                           |
| **All imports**                           | `rg` all 57 repos for old package name; replace every occurrence                          |
| **Artifact Registry**                     | Rename GCP AR package; update all `cloudbuild.yaml` `--tag` lines that publish/install it |
| **`workspace-manifest.json`**             | `name`, `artifact_registry_url`, `package_name` — all fields                              |
| **All dependent repos' `pyproject.toml`** | Replace old dep entry with new name at correct version                                    |
| **CI/CD**                                 | `version-bump.yml`, Cloud Build trigger name, `quality-gates.yml` dep install step        |
| **Cursor rules + codex docs**             | `rg` for old name; fix every occurrence                                                   |

### UTS Dual-Publish Rename (T1 STEP C: `lib-phase2-uts-rename-step1`)

Adds `unified_trading_services/` re-export package. When this is published:

- **ALL 14 services + 7 T2 libraries** must update their `pyproject.toml` dep entry in the SAME `--dep-branch` cascade
- Old import path must be **deleted** from all files — no fallback re-export kept

### UDC Rename (T3 STEP C: `lib-phase2-rename-step2`)

Same rule: ALL consumers update simultaneously. Old import path deleted. AR package old name decommissioned.

### NEVER

- Keep old import alongside new as "transitional"
- Bump version without renaming all consumers (`--dep-branch` cascades this automatically)
- Leave any `from old_package import ...` after rename PR merges

---

todos:

- id: p2-global-violation-sweep
  content: "Run ONCE across ALL repos after Phase 1 complete. THREE rounds per repo: ROUND 1 (mechanical, no structural changes): os.getenv(KEY,'') or os.getenv(KEY) → config class or os.environ[KEY]; bare except: → specific type + log + reraise; except Exception: pass → log+reraise; except <AnyType>: pass (ANY silent swallow) → log+reraise; print() in source → logger.info(); datetime.now()/utcnow() → datetime.now(timezone.utc); List[x]/Dict[x,y]/Tuple[x] → list[x]/dict[x,y]/tuple[x]; except ImportError fallbacks → delete and fail loud. ROUND 2 (error completeness): every except block must reraise OR raise typed error OR log ERROR + reraise — no silent discards. If typed error class is missing from AC/UIC_INT → add it there first (bottom-up rule). ROUND 3 (size enforcement): find files >900 lines (split by SRP, separate commit); find functions >50 lines (extract helpers). ALSO: before Round 1, run pure import smoke test in every repo: python -c 'import <package>' — failures are P0, fix first. Commit Round 1+2: 'fix: global violation sweep — error handling + mechanical QG fixes'. Commit Round 3: 'refactor: split large files by SRP'. 10 agents PARALLEL (5-6 repos each)."
  status: pending

- id: t0-deploy-structure
  content: "T0 STEP A — DEPLOY STRUCTURE [8 agents PARALLEL, 1 per repo]: Each agent: verify cloudbuild.yaml, quality-gates.sh, pyproject.toml, .dependency-matrix.json present and correct. Todos per repo: ci-quality-gates-missing-repos (AC, UEI, URDI), ci-cloudbuild-quality-gate-wire (each), ci-bypass-audit-missing-repos (each), ci-quality-gates-alignment (ruff+basedpyright+coverage settings). Repos: AC=unified-api-contracts, UIC_INT=unified-internal-contracts, UCI=unified-config-interface, UEI=unified-events-interface, UCLI=unified-cloud-interface, URDI=unified-reference-data-interface, EAL=execution-algo-library, MEL=matching-engine-library. Max parallel: 8."
  status: pending

- id: t0-tests-first
  content: "T0 STEP B — TESTS FIRST [8 agents PARALLEL]: Integration Layer 0 MUST complete in T0: integration-layer0-ac-uic-unit (unified-api-contracts: test_contract_alignment.py), integration-layer0-ac-uic-integration (unified-api-contracts: test_ac_uic_alignment.py — AC→UIC schema pairs), integration-layer0-uic-ac-unit (unified-internal-contracts: internal), integration-layer0-uic-ac-integration (unified-internal-contracts: test_uic_ac_alignment.py). Also: ic-uic-coverage-floor (UIC_INT 35%→80%), ic-uic-py-typed, ac-coverage-90. Schema todos: ic-greeks-position-schema, ic-pnl-breakdown-schema, ic-circuit-breaker-schema, ic-eod-settlement-contract, ic-feature-contracts, ic-ml-training-contracts, ic-rebalance-instruction, ic-portfolio-risk-contracts, ic-client-account-domain-model, ic-unified-internal-repo (create repo). API contracts: ac-ccxt-completeness, ac-fee-borrow-all-venues, ac-risk-infrastructure, ac-funding-settlement-portfolio-margin, ac-vol-surface-all-venues, ac-sentiment-oi-all-venues, ac-account-lifecycle-all-venues, ac-aggregate-trades-fills-mark-price, ac-shared-schema-extensions, ac-restructure, ac-dual-structure-doc, ac-exhaustive-schema-universe."
  status: pending

- id: t0-code-rewrite
  content: "T0 STEP C — CODE REWRITE [8 agents PARALLEL]: lib-phase3-urdi-setup (URDI T0 hardening: verify REST adapters, get_secret_client via UCLI, rate limiting, retry via @with_retry), mel-deps-remove (MEL zero inter-lib deps: remove any UTS/UCI imports), dag-mel-tier-mismatch (fix MEL visual bug in DAG SVG — move to T0 blue), cohesion-uic-int-unified-api-contracts-dep (add AC as dep in UIC_INT pyproject.toml + manifest), auth-endpoint-registry-unvalidated (CassetteStatus enum + backfill 22+ auth-required venues), vcr-urdi-parse-raw-umi-stubs (add abstract \_parse_raw to URDI base_adapter), vcr-public-venues (cassettes for 8 public venues: kalshi, polymarket, thegraph, defillama, barchart, open_meteo, upbit, fear_greed), quality-importerror-fallbacks (AC only), quality-large-file-splits (aws_schemas.py 1424L, venue_manifest.py 1058L, binance/schemas.py 1033L)."
  status: pending

- id: t0-progressive-validation
  content: "T0 STEP D→E — PROGRESSIVE VALIDATION [8 agents PARALLEL]: D1: quickmerge --lint-only (fastest feedback — syntax, import ordering, formatting); D2: quickmerge --unit-only (import errors, type errors, unit tests); D3: quickmerge --qg-only (full QG no git ops — integration test failures, coverage gaps); D4: quickmerge --quick (full QG + git ops, skip act); D5: quickmerge (full, no flags) — T0 TIER GREEN GATE. Do NOT move to T1 until ALL 8 T0 repos pass D5."
  status: pending

- id: t1-uts-deploy-structure
  content: "T1 STEP A — DEPLOY STRUCTURE [REQUIRES: all T0 repos green]: lib-phase5-t1-quality-gates (verify QG passes in UTS=unified-trading-services); ci-cloudbuild-quality-gate-wire for UTS."
  status: pending

- id: t1-uts-tests
  content: "T1 STEP B — TESTS FIRST: qg-uts-conftest-skip-pattern (fix GCP auth skip pattern — use google.auth.default() per gcp-auth-in-tests.mdc; reference market-data-processing-service/tests/conftest.py as correct pattern). ConfigReloader test already in UTS (moved from UCI)."
  status: pending

- id: t1-uts-code-rewrite
  content: "T1 STEP C — CODE REWRITE: lib-phase1-uts-domain-cleanup (remove create_instruments_client, create_market_candle_data_client, StandardizedDomainCloudService re-export from **init**.py — services import from UDC only); lib-phase2-uts-rename-step1 (add unified_trading_services/ re-export package, update pyproject.toml for dual publish, update workspace-manifest.json, update cursor rules + codex docs); dag-uts-v22-feature-audit (verify GCSEventSink, PubSubEventSink, QueueEventSink, ServiceCLI, BatchOrchestrator, @with_retry, setup_service, StateStore, BaseCloudWriter, GracefulShutdownHandler are all implemented — update plan phases for already-done items); quality-importerror-fallbacks (UTS only); uts-v5-cleanup (clean optional extras to remove tier leakage and stale package names)."
  status: pending

- id: t1-uts-progressive-validation
  content: "T1 STEP D→E — PROGRESSIVE VALIDATION: D1 (--lint-only) → D2 (--unit-only) → D3 (--qg-only) → D4 (--quick) → D5 (full). T1 TIER GREEN GATE = D5 passes."
  status: pending

- id: t2-deploy-structure
  content: "T2 STEP A — DEPLOY STRUCTURE [REQUIRES: T0+T1 green] [7 agents PARALLEL]: lib-phase5-t2-quality-gates (UMI=unified-market-interface, UTEI=unified-trade-execution-interface, UML=unified-ml-interface, UFC=unified-feature-calculator-library, UPI=unified-position-interface, UDEI=unified-defi-execution-interface, USEI=unified-sports-execution-interface — per-library QG checklist); ci-quality-gates-missing-repos (UTEI, UPI); cohesion-umi-udc-dep-violation (CRITICAL: remove UDC from UMI pyproject.toml deps — T2 must only import T0+T1; add tier-boundary CI check to UMI quality-gates.sh)."
  status: pending

- id: t2-tests-first
  content: "T2 STEP B — TESTS FIRST [7 agents PARALLEL]: vcr-public-venues (UMI VCR cassettes: kalshi, polymarket, thegraph, defillama, fear_greed); vcr-new-adapters-public (UMI: kalshi, polymarket, defillama, fear_greed adapters); vcr-new-adapters-cefi-sports (aster, upbit, odds_api, pinnacle, glassnode, arkham — BLACKLISTED_UNVALIDATED); vcr-new-adapters-tradfi-altdata (ibkr, fred, ecb, ofr, openbb, yahoo_finance, api_football, footystats, soccer_football, mev); vcr-enhanced-error-high-priority (instruments-service 62 — test fixes, instruments-service itself is T4 but fix test infra now); p0-umi-skipped-test (unskip after p0-canonical-swap-fix); usei-v1-betfair-pinnacle (USEI Betfair + Pinnacle adapters using BaseSportsAdapter protocol)."
  status: pending

- id: t2-code-rewrite
  content: "T2 STEP C — CODE REWRITE [7 agents PARALLEL]: p0-canonical-swap-fix (bump UIC patch version + reinstall in UMI — CanonicalSwap stale installed package); vcr-urdi-parse-raw-umi-stubs (implement 12 NotImplementedError stubs in UMI: coinbase, databento, tardis, aster normalizers); lib-phase2-udc-rename-step1 (add unified_domain_client/ re-export package to UDC, update pyproject.toml for dual publish, update manifest); vcr-new-adapters-cefi-sports and vcr-new-adapters-tradfi-altdata (UMI); cohesion-upi-pbm-dependency (UPI adapters: CCXT, OKX, IBKR feed PBM reader seam); quality-importerror-fallbacks (T2 only); uml-protocol-refactor (define ModelArtifactStore protocol in UML, remove direct UDC imports — UML must not import T3); dag-venue-interface-plan (L2 LIBRARY: unified-venue-interface at L2 providing BaseVenueExecutionAdapter protocol — optional based on scope)."
  status: pending

- id: t2-progressive-validation
  content: "T2 STEP D→E — PROGRESSIVE VALIDATION [7 agents PARALLEL]: D1 (--lint-only) → D2 (--unit-only) → D3 (--qg-only) → D4 (--quick) → D5 (full). T2 TIER GREEN GATE = all 7 repos pass D5."
  status: pending

- id: t3-udc-deploy-structure
  content: "T3 STEP A — DEPLOY STRUCTURE [REQUIRES: T0+T1+T2 green]: lib-phase1-udc-tier2-compliance (replace CloudTarget/get_config/market_category imports from UTS with UCLI equivalents; remove unified-trading-services from UDC pyproject.toml; add unified-cloud-interface>=1.0.0,<2.0.0); lib-phase2-udc-rename-step1 (add unified_domain_client/ re-export package)."
  status: pending

- id: t3-udc-tests
  content: "T3 STEP B — TESTS FIRST: ic-deprecated-withdraw-cleanup (remove deprecated WITHDRAW instruction type and signal_id field per delete-deprecated.mdc); ic-trad-fi-datasource-tag (add data_source_constraint field to InstrumentRecord; tag TradFi as DATABENTO_ONLY); ic-onchain-freshness-contract (OnchainDataFreshnessConfig per chain)."
  status: pending

- id: t3-udc-code-rewrite
  content: "T3 STEP C — CODE REWRITE: lib-phase3-instruments-service-urdi-wire (wire instruments-service to URDI: replace direct exchange REST calls with get_reference_adapter(venue).get_instruments() — note: instruments-service is T4 but the wiring decision lives in UDC); lib-phase2-rename-step2 (update all 14 services + T2 libs to use new import names; remove aliases; rename GitHub repos + Artifact Registry packages + Cloud Build triggers); udc-artifact-impl (implement GcsModelArtifactStore in UDC, wire in ML services)."
  status: pending

- id: t3-udc-progressive-validation
  content: "T3 STEP D→E — PROGRESSIVE VALIDATION: D1 (--lint-only) → D2 (--unit-only) → D3 (--qg-only) → D4 (--quick) → D5 (full). T3 TIER GREEN GATE = D5 passes. Phase 2 complete when T3 D5 passes."
  status: pending

## isProject: true
