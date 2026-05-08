# Session 3: Auth & Reporting & Instruments

> **2026-03-24:** Historical session charter. API names below were updated to the **consolidated** surface
> (**`unified-trading-api`**, **`auth-api`**) where they referred to standalone repos now under **`archive/`**. See
> **`archive/README.md`** and **`scripts/dev/ui-api-mapping.json`**.

## Services & Repos Affected

> **DO NOT work on these repos in other sessions -- they are owned by this session.**

| Repo                                             | What Changes                                                                                          | Risk |
| ------------------------------------------------ | ----------------------------------------------------------------------------------------------------- | ---- |
| unified-config-interface (auth/ dir only)        | entitlement_registry.yaml, service_access_matrix.yaml, entitlements.py                                | MED  |
| unified-cloud-interface                          | Pre-signed URL helpers (generate_upload_url, generate_download_url), shared auth middleware           | MED  |
| client-reporting-api                             | P&L reporting, invoicing, MiFID II compliance, DocuSign integration, document CRUD, seed_mock_data.py | HIGH |
| instruments-service                              | Batch validation residuals, data source separation, cloud config loading, live mode handler           | HIGH |
| unified-api-contracts (tradfi_symbology.py only) | Instrument identity / data-source separation (split TRADFI_VENUE_MAPPINGS)                            | MED  |
| system-integration-tests                         | Auth penetration tests, document upload/download SIT tests                                            | LOW  |

### S2S Auth Enrollment (read entrypoint, add middleware -- no business logic changes)

| Repo                             | What Changes                    | Risk |
| -------------------------------- | ------------------------------- | ---- |
| instruments-service              | S2S token validation middleware | LOW  |
| market-tick-data-service         | S2S token validation middleware | LOW  |
| market-data-processing-service   | S2S token validation middleware | LOW  |
| features-technical-service       | S2S token validation middleware | LOW  |
| features-microstructure-service  | S2S token validation middleware | LOW  |
| features-orderflow-service       | S2S token validation middleware | LOW  |
| features-alternative-service     | S2S token validation middleware | LOW  |
| features-cross-sectional-service | S2S token validation middleware | LOW  |
| features-sentiment-service       | S2S token validation middleware | LOW  |
| features-onchain-service         | S2S token validation middleware | LOW  |
| features-sports-service          | S2S token validation middleware | LOW  |
| strategy-service                 | S2S token validation middleware | LOW  |
| trading-agent-service            | S2S token validation middleware | LOW  |
| risk-management-service          | S2S token validation middleware | LOW  |
| position-balance-monitor-service | S2S token validation middleware | LOW  |
| pnl-attribution-service          | S2S token validation middleware | LOW  |
| reconciliation-service           | S2S token validation middleware | LOW  |
| ml-training-service              | S2S token validation middleware | LOW  |
| ml-inference-service             | S2S token validation middleware | LOW  |

### API Auth Standardization (middleware only -- no mock data or response schema changes)

| Repo                | What Changes                                                                 | Risk |
| ------------------- | ---------------------------------------------------------------------------- | ---- |
| deployment-api      | Auth middleware standardization, entitlement enforcement                     | MED  |
| unified-trading-api | Auth middleware on consolidated domain routes (replaces archived split APIs) | MED  |
| auth-api            | JWT/OAuth issuance, user lifecycle, provisioning                             | MED  |
| market-data-api     | Auth middleware standardization, entitlement enforcement                     | MED  |

### Shared Repo Boundaries

- **unified-config-interface**: Session 3 OWNS auth/ directory (entitlement_registry.yaml, service_access_matrix.yaml,
  entitlements.py). Session 2 OWNS domain config schemas. No overlap.
- **unified-cloud-interface**: Session 3 OWNS pre-signed URL helpers and shared auth middleware module. Session 2 does
  not touch UCI.
- **unified-api-contracts**: Session 3 OWNS registry/tradfi_symbology.py (instrument data-source separation) and
  registry/data_source_continuity.py. Session 1 OWNS registry/capability_declarations/ and
  scripts/generate_ui_reference_data.py. No overlap.
- **instruments-service**: Session 3 OWNS entirely (completion, batch validation, data source separation, live mode).
  Other sessions do not touch instruments-service.
- **client-reporting-api**: Session 3 OWNS business features (Plan I). Session 2 OWNS mock mode and response schema
  standardization only.
- **21 services (S2S auth)**: Session 3 adds auth middleware to entrypoints only (main.py/app.py). Session 2 wires
  config hot-reload callbacks (different code paths, different files). No overlap.
- **9 API repos (auth middleware)**: Session 3 OWNS middleware/auth.py files. Session 2 OWNS mock_data.py and models.py.
  No overlap.
- **system-integration-tests**: Session 3 OWNS auth penetration tests and document flow tests. Session 4 OWNS scenario
  tests and performance tests.

## Plans Covered

| Plan                                 | Phases              | Todos Remaining | Reference                                                            |
| ------------------------------------ | ------------------- | --------------- | -------------------------------------------------------------------- |
| Plan G: Auth & Entitlement           | Phase 0-4           | ~18 todos       | plans/active/plan_g_auth_entitlement_2026_03_21.md              |
| Plan I: Client Reporting & Docs      | Phase 0-6           | ~31 todos       | plans/active/plan_i_client_reporting_docs_2026_03_21.md         |
| instruments_service_completion       | Phases 3-6          | ~12 todos       | plans/active/instruments_service_completion_2026_03_21.md       |
| instruments_service_batch_validation | Phases B2, C, B4, A | ~11 todos       | plans/active/instruments_service_batch_validation_2026_03_17.md |
| instrument_data_source_separation    | All phases          | ~10 todos       | plans/active/instrument_data_source_separation_2026_03_21.md    |

## What's Already Done (Don't Redo)

- **Plan G Phase 0**: service_access_matrix.yaml and entitlement_registry.yaml may already exist in UCfgI auth/
  directory. Verify before creating.
- **Plan G**: S2S auth already enrolled in 2 services (execution-service, risk-and-exposure-service). AUTH_FAILURE
  events already added to 4 API services (full_system_audit P0-04 done). S2S_AUTH_SUCCESS/FAILURE event types created in
  UEI (full_system_audit P0-05 done).
- **instruments_service_completion Phase 1**: All 9 services wired to UTL topology resolver (DONE).
- **instruments_service_completion Phase 2**: All DeFi venue fixes done (Aave V3, Balancer, Hyperliquid verified).
- **instruments_service_batch_validation Phase B1**: UAC reference data centralization fully done (tradfi_symbology.py,
  defi_protocol_registry.py, market_data_categories.py, venue mapping expansion, facade exports).
- **instruments_service_batch_validation Phase B3**: topology_reader moved to UTL (done in live_batch_alignment).
- **Plan I Phase 0 infrastructure**: UIC document schemas and UCI pre-signed URL helpers are new work -- nothing done
  yet.

## Execution Order

1. **Plan G Phase 0** (PARALLEL, no dependencies):
   - Define 8 service categories (internal/external)
   - Document subscription slicing (7 tiers -> endpoints -> limits)
   - Create service-access-matrix.yaml in UCfgI auth/

2. **instrument_data_source_separation Phase 1** (PARALLEL with Plan G Phase 0):
   - Split TRADFI_VENUE_MAPPINGS in tradfi_symbology.py into identity + provider bindings
   - Update VENUE_TO_DATA_SOURCES 1:N in canonical_mappings.py
   - Generalize data_source_continuity.py
   - Fix polymarket lint errors
   - UAC QG gate

3. **Plan G Phase 1** (SEQUENTIAL after Phase 0):
   - Audit S2S auth enrollment (which 2 already done, which 19 not)
   - Enroll remaining 19 services in S2S static token auth
   - Token rotation automation script
   - QG check for S2S auth middleware

4. **Plan I Phase 0** (PARALLEL with Plan G Phase 1):
   - Add DocumentMetadata + DocumentCategory to UIC
   - Add pre-signed URL helpers to UCI
   - Add documents bucket to UCI bucket registry
   - Document metadata storage

5. **instrument_data_source_separation Phase 2** (after Phase 1):
   - Update instruments-service venue_config.py for new bindings structure
   - Update instruments-service tests
   - QG gate

6. **instruments_service_batch_validation Phases B2, C** (PARALLEL with Phase 5):
   - B2: Update instruments-service (delete duplicates, import from UAC), update MDPS, features-delta-one
   - C: Config generation script, wire config loading, TickerUniverseConfig, bootstrap config

7. **Plan G Phase 2** (after Phase 1):
   - Audit API auth patterns across 9 API repos
   - Standardize auth middleware (shared module in UCI)
   - Org-level filtering
   - Auth integration tests

8. **Plan I Phases 1-5** (PARALLEL groups after Phase 0):
   - Phase 1: P&L reporting, client returns, settlement reporting, read-only API key
   - Phase 2: Invoice generation, templates, delivery (after Phase 1)
   - Phase 3: MiFID trade reporting, best execution (PARALLEL with Phase 2)
   - Phase 4: DocuSign integration (PARALLEL with Phase 1)
   - Phase 5: Document API routes (PARALLEL with Phase 1)

9. **Plan G Phase 3** (after Phase 2):
   - Create entitlement registry in UCfgI auth/entitlements.py
   - API entitlement middleware for all user-facing APIs
   - Instrument count enforcement
   - Entitlement tests

10. **instruments_service_completion Phases 3-5** (after batch validation phases):
    - Phase 3: Wire features-sports-service data sources (USRI, UFI)
    - Phase 4: Live mode design + implementation
    - Phase 5: Final QG + documentation

11. **Plan G Phase 4 + Plan I Phase 6** (SEQUENTIAL, final):
    - QG sweep on all affected repos
    - Auth penetration test suite in SIT
    - Access matrix parity verification
    - client-reporting-api seed_mock_data.py, mock doc uploads, QG, SIT tests

## Key Rules

- `uv pip install` not `pip install`
- Never run pytest directly -- use `bash scripts/quality-gates.sh`
- Do NOT run quickmerge -- only `git add` + `git commit`
- `basedpyright` not `pyright` (with `run_timeout 120`)
- Interface credential convention: interfaces are API-keyless. Services fetch credentials from Secret Manager and inject
  at runtime via factory/constructor params.
- No `os.getenv()` -- use `UnifiedCloudConfig`. Token sourced from Secret Manager via UnifiedCloudConfig.
- In mock mode (CLOUD_MOCK_MODE=true), accept any token or skip validation.
- Services use URDI for reference data, not UMI -- UMI is for market data only.
- Pre-signed URLs: API never handles file bytes directly -- all file transfer is client-to-cloud-storage.

## CITADEL AUDIT FINDINGS (2026-03-21)

This session needs to address the following honest status corrections:

1. **S2S auth: 19/21 NOT applying to routes.** auth_s2s.py files were created in 19 services by a prior agent session,
   but verify_service_token is NOT applied to actual FastAPI route registrations. The middleware exists as dead code in
   all 19 services. Plan G Phase 1 p1-enroll-remaining-services has been reset to NOT DONE. Each service needs: (1)
   import the auth dependency in main.py/app.py, (2) apply it to the FastAPI app or individual routers, (3) add
   integration test that unauthenticated call returns 401.

2. **auth-api is P2 DEV.** No OAuth implementation. No production guard (being fixed separately). No RBAC enforcement.
   Plan G Phase 2 (API auth standardization) depends on auth-api being functional for token issuance and validation.
   This is a blocking dependency that must be tracked.

3. **Plan G Phase 0 (service access matrix) IS genuinely done.** service_access_matrix.yaml and
   entitlement_registry.yaml were correctly created in UCfgI auth/. Do not re-do this work.

4. **Plan I status is accurate.** The Phase 0-3 work that was marked done is genuinely done (document schemas,
   pre-signed URL helpers, invoicing endpoints, compliance endpoints, DocuSign integration). No corrections needed for
   Plan I.

## Success Criteria

- [ ] All QGs pass on: unified-config-interface, unified-cloud-interface, client-reporting-api, instruments-service, all
      9 API repos, system-integration-tests
- [ ] service-access-matrix.yaml created with all 21 services categorized
- [ ] All 21 services validate S2S tokens (19 newly enrolled + 2 existing)
- [ ] All 9 API repos use standardized auth middleware with org-level filtering
- [ ] Entitlement registry with 7 tiers, instrument count limits enforced at API level
- [ ] Auth penetration tests pass in SIT
- [ ] client-reporting-api has P&L, invoicing, MiFID compliance, DocuSign, document CRUD endpoints
- [ ] instruments-service: data source separation clean (VIX-USD loads without dataset/stype)
- [ ] instruments-service: batch validation produces instruments across all asset classes
- [ ] instruments-service: cloud config loading wired (ConfigReloader + TimeSeriesConfigStore)
