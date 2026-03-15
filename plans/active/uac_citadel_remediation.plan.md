---
name: uac-citadel-remediation
overview: |
  Remediation plan for incomplete items from the UAC Citadel Architecture execution.
  The structural foundation is in place (facades, domain sub-packages, tier model, capability registry)
  but several cleanup items were marked done prematurely. This plan tracks the actual remaining work.
type: code
epic: epic-code-completion
status: active
completion_gates:
  code: C4
  deployment: none
  business: none
repo_gates:
  - repo: unified-api-contracts
    code: C0
    deployment: none
    business: none
  - repo: unified-internal-contracts
    code: C0
    deployment: none
    business: none
  - repo: unified-sports-execution-interface
    code: C0
    deployment: none
    business: none
  - repo: unified-trade-execution-interface
    code: C0
    deployment: none
    business: none
  - repo: unified-market-interface
    code: C0
    deployment: none
    business: none
  - repo: unified-trading-library
    code: C0
    deployment: none
    business: none
  - repo: unified-trading-pm
    code: C0
    deployment: none
    business: none
  - repo: system-integration-tests
    code: C0
    deployment: none
    business: none
depends_on:
  - uac-citadel-implementation-execution
todos:
  # ═══════════════════════════════════════════════════════════════
  # A. STALE DIRECTORIES (should have been deleted, still exist)
  # ═══════════════════════════════════════════════════════════════
  - id: a1-delete-canonical-normalize
    content: |
      - [ ] [AGENT] P0. Delete canonical/normalize/ directory from UAC. It was supposed to move to normalize_utils/ in Phase 1 but the original was never deleted. 25 aggregator files remain as duplicates. Consumers: 9 files (all UAC-internal tests + normalize_utils/errors modules). Migration: update those 9 files to import from normalize_utils/ instead of canonical.normalize, then delete the directory.
    status: pending
    note:
      "canonical/normalize/ has 25 .py files that are duplicated in normalize_utils/. The functions are defined in BOTH
      locations."

  - id: a2-delete-external-sports
    content: |
      - [ ] [AGENT] P0. Delete external/sports/ directory from UAC. All canonical types moved to canonical/domain/sports/ in Phase 2, all sources flattened to external/{provider}/ in Phase 3. Remaining consumers: 27 test files in unified-sports-execution-interface. Migration: update USEI tests to import from canonical.domain.sports or top-level facades instead of external.sports.canonical.
    status: pending
    note:
      "external/sports/ contains canonical/ subdirectory with types that are now duplicated in canonical/domain/sports/"

  - id: a3-fix-venue-manifest-location
    content: |
      - [ ] [AGENT] P0. The Phase 1 move was backwards -- external/venue_manifest/ is the ACTIVE copy (3 UAC test files import from it), registry/venue_manifest/ is the STALE copy with zero importers. Either: (a) delete registry/venue_manifest/ and keep external/venue_manifest/ as-is, or (b) update the 3 test files to import from registry/venue_manifest/ and delete external/venue_manifest/. Option (b) matches the architecture plan.
    status: pending
    note: "registry/venue_manifest/ has zero importers. external/venue_manifest/ has 3 test file importers."

  - id: a4-delete-schemas-dir
    content: |
      - [ ] [AGENT] P1. Delete unified_api_contracts/schemas/ directory. Contains only __init__.py and __pycache__. Check if schemas/__init__.py is imported by anything: rg 'from unified_api_contracts.schemas' --type py. One known consumer: test_contract_alignment.py. Update it, then delete.
    status: pending

  # ═══════════════════════════════════════════════════════════════
  # B. DUPLICATE CODE (same functions defined in 2+ locations)
  # ═══════════════════════════════════════════════════════════════
  - id: b1-dedupe-normalize-functions
    content: |
      - [ ] [AGENT] P0. 49 external/{source}/normalize.py files were created with COPIES of functions from normalize_utils/*.py, but the originals in normalize_utils/ were never removed. Every normalizer function now exists in TWO places. After a1-delete-canonical-normalize completes and normalize_utils/ is the sole aggregator location, update normalize_utils/__init__.py to re-export from external/{source}/normalize.py instead of defining functions inline. Then the normalize_utils/*.py files (tickers.py, orderbooks.py, etc.) become thin re-export facades importing from external/{source}/normalize.py.
    status: pending
    blocked_by: a1-delete-canonical-normalize
    note: "~210 functions duplicated between normalize_utils/*.py and external/*/normalize.py"

  - id: b2-dedupe-sports-canonical
    content: |
      - [ ] [AGENT] P1. external/sports/canonical/*.py types are duplicated in canonical/domain/sports/. After a2-delete-external-sports, verify no remaining consumers reference the old location.
    status: pending
    blocked_by: a2-delete-external-sports

  - id: b3-dedupe-venue-manifest
    content: |
      - [ ] [AGENT] P1. After a3-fix-venue-manifest-location resolves the ownership, delete the stale copy.
    status: pending
    blocked_by: a3-fix-venue-manifest-location

  # ═══════════════════════════════════════════════════════════════
  # C. MISSING PER-SOURCE FILES (plan says every source gets these)
  # ═══════════════════════════════════════════════════════════════
  - id: c1-missing-normalize-py
    content: |
      - [ ] [AGENT] P1. 25 data source dirs have schemas.py but no normalize.py. For sources that HAVE normalizer functions in normalize_utils/ (check normalize_utils/sports.py, instruments.py, etc.), extract those functions to external/{source}/normalize.py. Sources: alchemy, api_football, baker_hughes, bloxroute, cftc, cryptoquant, eia, fear_greed, footystats, github, instadapp, mev, odds_api, odds_engine, oddsjam, open_meteo, opticodds, polygon, sharpapi, soccer_football_info, thegraph, transfermarkt, understat. Exempt (not data sources): defi, prime_broker, protocol_sdks.
      - [ ] REFERENCE: docs/normalize-phase2-agent-reference.md — domain mapping, canonical types, reference normalizers (betfair, glassnode, fred), agent assignment for up to 20 parallel agents, Context7 refs (Alchemy: /alchemyplatform/docs).
    status: pending

  - id: c2-missing-mappings-py
    content: |
      - [ ] [AGENT] P2. Zero external/{source}/mappings.py files exist. The plan says per-source mappings should be extracted from common_mappings.py (now in normalize_utils/). However, common_mappings.py doesn't exist either (may have been renamed or lost). Check: does normalize_utils/ have any mappings data? If yes, split to per-source. If the data was in canonical_mappings.py which was renamed, find it. Cross-venue lookups (DATA_SOURCE_TO_VENUES, VENUE_TO_DATA_SOURCE) should stay in registry/.
    status: pending

  # ═══════════════════════════════════════════════════════════════
  # D. ORPHANED/UNUSED INFRASTRUCTURE (built but never wired)
  # ═══════════════════════════════════════════════════════════════
  - id: d1-wire-capability-registry
    content: |
      - [ ] [AGENT] P1. resolve_capability() exists in UAC registry/capability.py but is called by ZERO consumers. bootstrap_capabilities() registers 20 providers but nobody calls it. Wire into at least one interface adapter (UMI is the best candidate) as a proof-of-concept: call resolve_capability() before API calls. Then other interfaces can adopt incrementally.
    status: pending

  - id: d2-implement-validation-functions
    content: |
      - [ ] [AGENT] P1. validate_mode(), validate_environment(), validate_auth_scope() were specified in Phase 10 but never implemented. The error classes exist in UTL (UnsupportedModeError, etc.) but no validation functions call them. Create validate_mode_env_auth() in UAC registry/capability.py that checks SourceCapability fields and raises the appropriate UTL error.
    status: pending
    blocked_by: d1-wire-capability-registry

  - id: d3-backfill-remaining-providers
    content: |
      - [ ] [AGENT] P2. Only 20 of ~80 providers have SourceCapability declarations. Backfill the remaining ~60 providers in capability_data.py. This is data entry work -- check each external/{source}/ directory to determine domains, modes, auth.
    status: pending
    blocked_by: d1-wire-capability-registry

  # ═══════════════════════════════════════════════════════════════
  # E. DOWNSTREAM CONSUMER MIGRATION (old paths still used)
  # ═══════════════════════════════════════════════════════════════
  - id: e1-migrate-usei-sports-errors
    content: |
      - [ ] [AGENT] P0. 25+ USEI test files import ScraperError from unified_api_contracts.external.sports.errors (stale path). Migrate all to: from unified_api_contracts.errors import ScraperError (or from unified_api_contracts import ScraperError if re-exported). Verify ScraperError is available via the errors facade. Files: tests/unit/scrapers/test_{coral,williamhill,betvictor,paddypower,sbobet,skybet,boylesports,betfred,betway,bwin,bet888sport,ladbrokes,bet365,unibet}_adapter.py + tests/unit/adapters/test_{api_football,odds_api}_adapter.py + test_adapter_stubs.py.
    status: pending

  - id: e1b-migrate-usei-betfair-canonical-execution
    content: |
      - [ ] [AGENT] P0. CRITICAL PRODUCTION CODE: unified-sports-execution-interface/adapters/exchanges/betfair.py imports from canonical.execution (with noqa comment). Change to: from unified_api_contracts.execution import OrderSide, OrderStatus, OrderType. Remove the noqa:qg-deep-import comment. Run USEI QG.
    status: pending

  - id: e2-migrate-uac-test-canonical-normalize
    content: |
      - [ ] [AGENT] P0. 9 UAC-internal files still import from canonical.normalize.*. Migrate to normalize_utils.* paths. Then canonical/normalize/ can be deleted (a1).
    status: pending

  - id: e3-migrate-uac-test-venue-manifest
    content: |
      - [ ] [AGENT] P1. 3 UAC test files import from external.venue_manifest.*. Migrate to registry.venue_manifest.* paths. Then external/venue_manifest/ can be deleted (a3 option b).
    status: pending

  - id: e4-migrate-uac-test-schemas
    content: |
      - [ ] [AGENT] P1. 1 UAC test file imports from unified_api_contracts.schemas. Migrate to facade import. Then schemas/ can be deleted (a4).
    status: pending

  - id: e5-migrate-trading-agent-deep-imports
    content: |
      - [ ] [AGENT] P1. 4 files in trading-agent-service tests import from canonical.domain.derivatives (ComboLeg, ComboStrategyType). Migrate to: from unified_api_contracts.derivatives import ComboLeg, ComboStrategyType. Files: tests/unit/test_coverage_boost_trading_agent.py (3 occurrences), tests/unit/test_strategy_ranker.py.
    status: pending

  - id: e6-migrate-strategy-service-deep-import
    content: |
      - [ ] [AGENT] P1. strategy-service/tests/unit/test_vol_surface_strategy.py imports from canonical.options. Migrate to: from unified_api_contracts.options import NormalizedStrikeCoordinate.
    status: pending

  - id: e7-migrate-umi-sports-domain-import
    content: |
      - [ ] [AGENT] P1. 2 UMI test files import from canonical.domain.sports.errors. Migrate to: from unified_api_contracts.errors import X (or unified_api_contracts.sports import X). File: tests/unit/sports/test_sports_registry.py.
    status: pending

  - id: e8-migrate-umi-schemas-suffix
    content: |
      - [ ] [AGENT] P1. 20+ UMI adapter and test files use from unified_api_contracts.external.{source}.schemas import X (with .schemas suffix). Drop the .schemas -- should be from unified_api_contracts.external.{source} import X (uses __init__.py re-export). Sources: thegraph, bybit, okx, instadapp, kraken, deribit, bitfinex, bitget, bitstamp, gateio, huobi, kucoin, mexc, upbit, dydx. Files span adapters/defi/*.py and tests/schema_validation/*.py and tests/integration/test_vcr_ac_schema_validation.py.
    status: pending

  - id: e9-service-external-import-audit
    content: |
      - [ ] [AGENT] P2. Final verification: no service production code imports from unified_api_contracts.external.{source}. Current audit found 0 production imports (only comments). Re-verify after all other migrations. The Phase 6 linter catches new violations.
    status: pending

  # ═══════════════════════════════════════════════════════════════
  # F. QG / TOOLING FIXES
  # ═══════════════════════════════════════════════════════════════
  - id: f1-qg-exemption-persistence
    content: |
      - [x] [AGENT] P0. Fixed rollout-quality-gates-unified.py to preserve custom QG config (UAC_CANONICAL_EXEMPT, BROAD_EXCEPT_EXTRA_EXCLUDES) during re-rollout. Also added auto-detection by PACKAGE_NAME/SERVICE_NAME in base-library.sh and base-service.sh.
    status: done

  - id: f2-qg-verbose-violations
    content: |
      - [x] [AGENT] P0. Made codex violation output verbose -- STEP 5.23 (deep UAC imports), broad except Exception, and imports-inside-functions now show offending file paths in QG output.
    status: done

  - id: f3-uac-qg-green
    content: |
      - [ ] [AGENT] P0. UAC quality gates must pass with zero violations. Currently 1 codex violation (broad except in tardis/normalize.py). Either fix the except or add to BROAD_EXCEPT_EXTRA_EXCLUDES in QG config. Run full QG and verify all green.
    status: pending

  # ═══════════════════════════════════════════════════════════════
  # G. TECH DEBT DOCUMENTATION
  # ═══════════════════════════════════════════════════════════════
  - id: g1-update-execution-plan-status
    content: |
      - [ ] [AGENT] P0. Update uac_citadel_implementation_execution.plan.md to honestly reflect which todos are actually complete vs partially complete. Todos that were marked done but have remaining work should be re-opened or have follow-up todos in this plan.
    status: pending

  - id: g2-document-remaining-normalize-utils-role
    content: |
      - [ ] [AGENT] P2. After b1-dedupe completes, document the final role of normalize_utils/: it should contain ONLY shared primitives (sides.py, symbols.py, _helpers.py) and re-exports from external/{source}/normalize.py. All venue-specific function definitions should live in external/{source}/normalize.py.
    status: pending
    blocked_by: b1-dedupe-normalize-functions

isProject: false
---

# UAC Citadel Remediation Plan

## Related Documents

- Original execution: `unified-trading-pm/plans/active/uac_citadel_implementation_execution.plan.md`
- Architecture spec: `unified-trading-pm/plans/active/uac_citadel_architecture_0ccb5b9b.plan.md`
- Implementation spec: `unified-trading-pm/plans/active/uac_citadel_implementation.plan.md`

## What's Actually Complete (from original execution)

- Manifest tier+role schema (69 repos)
- UTL tier violations fixed
- 15 root-level facade files (market.py, execution.py, etc.)
- Domain sub-packages (canonical/domain/{market,execution,reference,sports,...}/)
- Crosscutting types separated (canonical/crosscutting/)
- 49 per-source normalize.py files created
- 21 services LogLevel migrated to UTL
- Interface adapter imports updated (UMI, USEI, UPI)
- Transition facades deleted (canonical/execution.py, options.py, odds.py, spread.py)
- Phase 6 linter enforcement wired into base scripts
- Capability registry + 20 providers backfilled
- 3 new repos created (UFI, UFOL, USRI)
- Error taxonomy in UTL (5 error classes)
- Codex docs updated

## What's NOT Complete (this plan tracks)

### Category A: Stale directories (4 items)

Directories that should have been deleted but still exist because consumers weren't migrated first.

### Category B: Duplicate code (3 items)

Same functions/types defined in 2+ locations. The "new" location was created but the "old" location was never cleaned
up.

### Category C: Missing per-source files (2 items)

25 data sources still lack normalize.py. Zero sources have mappings.py.

### Category D: Orphaned infrastructure (3 items)

Capability registry, validation functions, and provider backfills were built but never wired into any consumer.

### Category E: Consumer migration (9 items)

Downstream repos still import from old paths. Must migrate before stale dirs can be deleted. Includes:

- 25+ USEI test files using external.sports.errors (ScraperError)
- 1 USEI production file using canonical.execution (CRITICAL)
- 4 trading-agent-service test files using canonical.domain.derivatives
- 1 strategy-service test file using canonical.options
- 2 UMI test files using canonical.domain.sports.errors
- 20+ UMI adapter/test files using .schemas suffix (should use **init**.py re-export)
- UAC-internal test migrations (normalize, venue_manifest, schemas)

### Category F: QG/tooling (1 remaining item)

UAC QG not fully green.

### Category G: Documentation (2 items)

Honest status updates and architecture documentation.

## Execution Order

```
Phase 1 (parallel -- all consumer migrations):
  E1 (USEI ScraperError 25 files) + E1b (USEI betfair.py CRITICAL)
  E2 (UAC normalize tests) + E3 (UAC venue_manifest tests) + E4 (UAC schemas test)
  E5 (trading-agent derivatives) + E6 (strategy-service options) + E7 (UMI sports errors)
  E8 (UMI .schemas suffix 20+ files)
  F3 (UAC QG green)
  |
  v
Phase 2 (parallel -- delete stale dirs after consumers migrated):
  A1 (delete canonical/normalize/) + A2 (delete external/sports/)
  A3 (fix venue_manifest) + A4 (delete schemas/)
  |
  v
Phase 3 (parallel -- deduplicate):
  B1 (dedupe normalize functions ~210) + B2 (dedupe sports) + B3 (dedupe venue_manifest)
  |
  v
Phase 4 (parallel -- fill gaps):
  C1 (25 sources need normalize.py) + C2 (mappings.py extraction)
  |
  v
Phase 5 (sequential -- wire infrastructure):
  D1 (wire capability registry) -> D2 (validation functions) -> D3 (backfill 60 providers)
  |
  v
Phase 6 (parallel -- final):
  E9 (final service audit) + G1 (update execution plan) + G2 (document normalize_utils role)
```

## Total: 24 todos (2 done, 22 pending)
