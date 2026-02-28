---
name: Service Scaffolding Prompt
overview: Generate a ready-to-paste Claude Code prompt that instructs parallel agents to restructure all 12 services to use the new UTS/UDC library names, clean orphaned code, fix imports, and harden quality gate scaffolding — without requiring quickmerge or full QG pass.
todos: []
isProject: false
---

# Service Scaffolding: Claude Code Parallel Agent Prompt

## How to use this plan

The body below IS the prompt to paste directly into Claude Code. Copy everything from the line `Follow all workspace cursor rules` through the end.

---

## Research Summary (do not paste — for reference)

**What the exploration found:**

- 12 service repos present (not 14 — `risk-and-exposure-service` and `position-balance-monitor-service` exist but weren't in search scope)
- All 12 services import `unified_trading_services` (old Tier 1 name)
- 0 services import `unified_trading_services` (new name not yet in use)
- 0 services import `unified_domain_client` (new UDC name not yet in use)
- `unified-trading-services` package: still named `unified-trading-services`, no `unified_trading_services` alias yet
- `unified-domain-client` package: still named `unified-domain-client`, no `unified_domain_client` alias yet
- UCS `__all__` still has stale symbols: `create_domain_cloud_service`, `create_instruments_cloud_service`, etc.
- `features-onchain-service`: most broken — uses `unified_trading_services.domain` (deleted) + `UnifiedCloudServicesConfig` (deprecated)
- `strategy-service`: broken TODO imports from `unified_domain_client`
- `ml-training-service` + `ml-inference-service`: import `CloudTarget`, `StandardizedDomainCloudService` from UCS (should come from UDC)
- 4 services have direct `google-cloud-`* or `boto3` in `pyproject.toml`
- `execution-service`: extensive `os.environ` / `os.getenv` for API keys (should route via config/library adapters)

**Key cursor rules that use OLD names (agents must follow the PATTERN, not the literal import):**

- `.cursor/rules/event-logging.mdc` — `from unified_trading_services import GCSEventSink` → use `unified_trading_services`
- `.cursor/rules/instruments-domain-and-api-keys.mdc` — `from unified_trading_services import ...` examples → use `unified_trading_services`
- `.cursorrules` anti-patterns table — references old package names in examples

---

## The Claude Code Prompt

```
Follow all workspace cursor rules in .cursorrules.
No commits. No quickmerge. No git operations. No PRs.
No summary docs, no _SUMMARY.md, no _COMPLETE.md files.
uv not pip. Delete deprecated code — do not archive.
WORKSPACE: /Users/ikennaigboaka/Documents/repos/unified-trading-system-repos

╔══════════════════════════════════════════════════════════════╗
║  TESTING CONSTRAINTS                                         ║
║                                                              ║
║  ALLOWED mid-task:                                           ║
║    ✓ python -c "import <module>; print('OK')"               ║
║    ✓ pytest tests/unit/ -x --no-header -q                   ║
║    ✗ bash scripts/quality-gates.sh (too early)              ║
║    ✗ basedpyright (only if you specifically fix a type)      ║
║                                                              ║
║  Full quality-gates.sh may be run ONLY after Phase 1 done.  ║
║  Expect failures — they are NOT a blocker. Log them only.   ║
║  Quickmerge is NOT a success criterion.                      ║
╚══════════════════════════════════════════════════════════════╝

═══════════════════════════════════════════════════════════════
SECTION 1 — NAME MAPPING (TREAT AS ALREADY DONE)
═══════════════════════════════════════════════════════════════

The following renames are IN PROGRESS. Assume they are DONE for
code purposes. Compatibility aliases exist or must be created.

  unified_trading_services  →  unified_trading_services  (Tier 1)
  unified_domain_client →  unified_domain_client     (Tier 3)

PACKAGE NAME ALIASES (must exist before service updates):
  unified-trading-services/unified_trading_services/__init__.py
    → re-exports everything from unified_trading_services
  unified-domain-client/unified_domain_client/__init__.py
    → re-exports everything from unified_domain_client

═══════════════════════════════════════════════════════════════
SECTION 2 — CURSOR RULES: WHAT TO FOLLOW vs WHAT TO ADAPT
═══════════════════════════════════════════════════════════════

The following cursor rules use OLD package names in their examples.
Follow the PATTERN described; substitute new names:

  event-logging.mdc:
    OLD: from unified_trading_services import GCSEventSink, setup_service
    NEW: from unified_trading_services import GCSEventSink, setup_service

  instruments-domain-and-api-keys.mdc:
    OLD: from unified_trading_services import (CloudTarget, ...)
    NEW: from unified_trading_services import (CloudTarget, ...)
    OLD: from unified_domain_client import InstrumentsDomainClient
    NEW: from unified_domain_client import InstrumentsDomainClient

  .cursorrules anti-patterns table:
    Same substitution — patterns are correct, package names are old.

All other cursor rules (no-type-any, utc-datetime, uv-not-pip,
async-http, etc.) apply as-is with no adaptation.

═══════════════════════════════════════════════════════════════
SECTION 3 — IMPORT ROUTING MAP (final state, all services)
═══════════════════════════════════════════════════════════════

FROM unified_trading_services IMPORT:
  GCSEventSink, PubSubEventSink, CompositeEventSink, setup_service
  get_storage_client, get_secret_client
  handle_api_errors, handle_storage_errors
  ConfigStore, BaseCloudWriter, BaseCloudLoader, BaseGCSWriter, BaseGCSLoader
  generate_date_range, ColumnSchema, BaseDependencyChecker
  CloudTarget, ParquetSchemaEnforcer
  @with_retry (when available)

FROM unified_domain_client IMPORT:
  InstrumentsDomainClient, ExecutionDomainClient
  StandardizedDomainCloudService
  DomainValidationService, DomainValidationConfig
  validate_timestamp_date_alignment
  get_earliest_valid_date, should_skip_date
  (any domain client that was previously in unified_domain_client)

FROM unified_config_interface IMPORT:
  UnifiedCloudConfig, BaseConfig

FROM unified_events_interface IMPORT:
  setup_events, log_event, MockEventSink

FROM unified_cloud_interface IMPORT:
  StorageClient, SecretClient, get_storage_client (Tier 0 primitives)

FORBIDDEN in service source code (not tests):
  os.getenv("API_KEY_*")           → use get_secret_client() in library adapter
  os.getenv("TARDIS_API_KEY")      → same
  from google.cloud import storage → route via get_storage_client()
  import boto3                     → route via unified_trading_services
  UnifiedCloudServicesConfig       → use UnifiedCloudConfig (from unified_config_interface)
  from unified_trading_services.domain → use unified_domain_client
  setup_cloud_logging              → use setup_service or setup_events

═══════════════════════════════════════════════════════════════
SECTION 4 — PHASE 0: ALIAS SETUP (1 agent; BLOCKS Phase 1)
═══════════════════════════════════════════════════════════════

⛔ DO NOT START Phase 1 until Phase 0 agent is done.

────────────────────────────────────────────────────────────────
AGENT 0 — Create compatibility aliases + fix UCS __all__
Touches: unified-trading-services/, unified-domain-client/
────────────────────────────────────────────────────────────────

Step 1 — UTS alias
  Read: unified-trading-services/unified_trading_services/__init__.py
  Check if unified-trading-services/unified_trading_services/ exists.
  If NOT: create unified-trading-services/unified_trading_services/__init__.py
  Content:
    """Compatibility alias for unified_trading_services → unified_trading_services rename."""
    from unified_trading_services import *  # noqa: F401, F403
    try:
        from unified_trading_services import __all__ as _all
        __all__ = _all
    except ImportError:
        pass
  Add "unified_trading_services" to packages in unified-trading-services/pyproject.toml
  (under [tool.setuptools.packages.find] or explicit packages list)
  Quick sanity: python -c "from unified_trading_services import GCSEventSink; print('OK')"

Step 2 — UDC alias
  Read: unified-domain-client/unified_domain_client/__init__.py
  Check if unified-domain-client/unified_domain_client/ exists.
  If NOT: create unified-domain-client/unified_domain_client/__init__.py
  Content:
    """Compatibility alias for unified_domain_client → unified_domain_client rename."""
    from unified_domain_client import *  # noqa: F401, F403
    try:
        from unified_domain_client import __all__ as _all
        __all__ = _all
    except ImportError:
        pass
  Add "unified_domain_client" to packages in unified-domain-client/pyproject.toml
  Quick sanity: python -c "from unified_domain_client import InstrumentsDomainClient; print('OK')"

Step 3 — Fix UCS __all__ stale symbols
  File: unified-trading-services/unified_trading_services/__init__.py
  Remove from __all__ (reference deleted domain/ code — cause AttributeError):
    create_domain_cloud_service
    create_backtesting_cloud_service
    create_features_cloud_service
    create_instruments_cloud_service
    create_market_data_cloud_service
    create_strategy_cloud_service
    create_portfolio_cloud_service
  Also remove if present (owned by UDC, not UCS):
    StandardizedDomainCloudService (remove from __all__ + import line only if UDS-defined)
    DomainValidationConfig
    DomainValidationService
  If any function definitions for the above stale symbols exist in UCS, DELETE them.
  Quick sanity: python -c "from unified_trading_services import GCSEventSink, handle_api_errors, ConfigStore; print('OK')"

Step 4 — Fix UDS broken imports
  Read: unified-domain-client/unified_domain_client/__init__.py
  Read (if exists): unified-domain-client/unified_domain_client/standardized_service.py
  Read (if exists): unified-domain-client/unified_domain_client/factories.py
  For any import referencing:
    unified_trading_services.domain.standardized_service  → delete the import; if class needed, keep local def
    unified_trading_services.domain.factories             → delete the import
    unified_trading_services.core.config                  → replace with: from unified_config_interface import UnifiedCloudConfig
    unified_trading_services.core.market_category         → replace with: from api_contracts import MarketCategory (or delete if unused)
  If standardized_service.py / factories.py cannot be fixed without the deleted UCS domain/ logic:
    DELETE those files. Update __init__.py to remove those imports.
  Quick sanity: python -c "from unified_domain_client import InstrumentsDomainClient; print('OK')"

═══════════════════════════════════════════════════════════════
SECTION 5 — PHASE 1: SERVICE UPDATES (4 parallel agents)
═══════════════════════════════════════════════════════════════

✅ All 4 agents have ZERO file overlap — run ALL in parallel after Phase 0.

────────────────────────────────────────────────────────────────
AGENT 1-A — instruments-service, market-tick-data-handler, market-data-processing-service
────────────────────────────────────────────────────────────────

For EACH service in this group, apply the SERVICE HARDENING CHECKLIST (Section 6).

Additional notes:
  instruments-service:
    - Has 99 Python files — focus on top-level service package, config.py, main.py, dependency_checker.py
    - config_utils.py uses os.getenv for secrets → remove; secrets via get_secret_client in library adapters
    - dependency_checker.py uses os.getenv → replace with config class field access
    - GCSEventSink already wired — verify pattern matches Section 3
    - Direct exchange REST calls: leave for now (URDI migration is out of scope here)

  market-tick-data-handler:
    - Has boto3 in pyproject.toml → REMOVE
    - Uses InstrumentsDomainClient from UDS → update to UDC name
    - config.py uses os.getenv → replace with config class

  market-data-processing-service:
    - Has boto3 in pyproject.toml → REMOVE
    - os.environ.get("VM_INSTANCE_NAME") → acceptable (infra metadata, not API key); leave it
    - InstrumentsDomainClient from UDS → update to UDC name

────────────────────────────────────────────────────────────────
AGENT 1-B — features-delta-one-service, features-calendar-service, features-onchain-service
────────────────────────────────────────────────────────────────

For EACH service in this group, apply the SERVICE HARDENING CHECKLIST (Section 6).

Additional notes:
  features-onchain-service (most broken — fix in this order):
    1. Find all imports of UnifiedCloudServicesConfig → replace with:
         from unified_config_interface import UnifiedCloudConfig
       and rename the config class to inherit from UnifiedCloudConfig
    2. Find all imports of unified_trading_services.domain.* → replace with unified_domain_client imports
    3. setup_cloud_logging calls → replace with setup_service(... sink=GCSEventSink(...))
    4. Has google-cloud-storage in pyproject.toml → REMOVE
    5. Run python -c "from features_onchain_service import ..." to verify imports
    NOTE: This service is the most structurally broken. If a whole module is
    permanently broken around deleted UCS domain logic, DELETE the module and
    remove its import from __init__.py. Do not try to reconstruct deleted logic.

  features-calendar-service:
    - economic_calendar_loader.py uses os.environ.get("FRED_API_KEY")
    - Move FRED_API_KEY access to config field: add fred_api_key field to config class
      OR: the cleaner approach per architecture is that FRED connectivity should live
      in a library adapter — but since no such adapter exists yet, add it as a config
      field with: fred_api_key: str = Field(default="", description="FRED API key")
      and access via config.fred_api_key (not os.environ directly)

  features-delta-one-service:
    - os.getenv only in examples/ not service code — leave it (examples are not production)

────────────────────────────────────────────────────────────────
AGENT 1-C — features-volatility-service, ml-training-service, ml-inference-service
────────────────────────────────────────────────────────────────

For EACH service in this group, apply the SERVICE HARDENING CHECKLIST (Section 6).

Additional notes:
  ml-training-service:
    - Imports CloudTarget, StandardizedDomainCloudService from unified_trading_services
      → replace with: from unified_domain_client import StandardizedDomainCloudService
      → CloudTarget: from unified_trading_services import CloudTarget
    - Has boto3 in pyproject.toml → REMOVE
    - os.environ["USE_MOCK_FEATURES"] in train_handler.py → move to config field:
        use_mock_features: bool = Field(default=False)
      accessed via config.use_mock_features — delete the os.environ line

  ml-inference-service:
    - Imports CloudTarget, StandardizedDomainCloudService from unified_trading_services
      → replace with new names per Section 3
    - ModelVariantConfig from unified_trading_services → check if this exists in UTS;
      if not defined anywhere, check if it is service-owned (it may be an inference-specific
      config class that was incorrectly placed in UCS — if so, move definition into service)

  features-volatility-service:
    - os.getenv only in tests/conftest.py — leave it (GCP auth pattern is correct there)
    - verify setup_service(sink=GCSEventSink(...)) pattern in main.py

────────────────────────────────────────────────────────────────
AGENT 1-D — strategy-service, execution-service, pnl-attribution-service
────────────────────────────────────────────────────────────────

For EACH service in this group, apply the SERVICE HARDENING CHECKLIST (Section 6).

Additional notes:
  strategy-service:
    - Has broken TODO import comments in test_schema_validation.py, cloud_strategy_storage.py,
      dependency_checker.py — find these files and fix the actual imports (not TODO comments)
    - Imports CloudTarget, StandardizedDomainCloudService, ParquetSchemaEnforcer,
      DomainValidationService from unified_trading_services
      → CloudTarget, ParquetSchemaEnforcer → unified_trading_services
      → StandardizedDomainCloudService, DomainValidationService → unified_domain_client
    - Has boto3 in pyproject.toml → REMOVE
    - setup_events (legacy) in main.py → update to setup_service(sink=GCSEventSink(...))
      pattern per event-logging.mdc (with new UTS name)

  execution-service (largest service — 365 files, 661 Python files total):
    SCOPE LIMIT: Only touch these specific problem areas:
      1. service_config.py: os.getenv calls → use config class fields
      2. utils/gcs_service.py: os.getenv calls → use config class fields
      3. utils/dependency_checker.py: os.getenv calls → use config class
      4. config/grid_generator.py: os.getenv calls → use config class
      5. visualizer-api: if it has os.getenv for secrets → config or skip if it's a separate app
      6. pyproject.toml: update import names (no boto3 to remove based on audit)
      7. All `from unified_trading_services import` in service code → unified_trading_services
      8. All `from unified_domain_client import` → unified_domain_client
    DO NOT refactor the entire execution engine — too risky without tests passing.
    DO NOT touch NautilusTrader integration, backtest engine, live execution paths
    beyond import name updates.
    DELETE: Any file with "backtest_old.py" in its name — this is explicitly deprecated.

  pnl-attribution-service:
    - Minimal — 15 files. Full hardening checklist applies.
    - Verify pyproject.toml has all required deps (see Section 6 step 3)
    - Verify minimum required files exist (see Section 6 step 7)

═══════════════════════════════════════════════════════════════
SECTION 6 — SERVICE HARDENING CHECKLIST (apply to every service)
═══════════════════════════════════════════════════════════════

For EVERY service, in this order:

Step 1 — Read current state
  Read: <service>/<service_package>/__init__.py
  Read: <service>/<service_package>/config.py (or config/ package)
  Read: <service>/main.py (or __main__.py)
  Read: <service>/pyproject.toml

Step 2 — Update all unified library imports
  a) Replace ALL occurrences of `from unified_trading_services import` with
     `from unified_trading_services import` in all .py files under the service package
  b) Replace ALL occurrences of `from unified_domain_client import` with
     `from unified_domain_client import` in all .py files
  c) Replace `import unified_trading_services` → `import unified_trading_services`
  d) Replace `import unified_domain_client` → `import unified_domain_client`
  e) Replace `UnifiedCloudServicesConfig` with `UnifiedCloudConfig`
     (and update import: from unified_config_interface import UnifiedCloudConfig)
  f) Replace `setup_cloud_logging(...)` with `setup_events(service_name=..., mode=...)`
     or preferably the full setup_service(sink=GCSEventSink(...)) pattern

Step 3 — Verify/harden pyproject.toml
  Required dependencies (add if missing, keep existing version pins):
    "unified-trading-services" (or "unified-trading-services" if alias not published yet —
     keep whichever works; the alias handles import names)
    "unified-domain-client" (or "unified-domain-client" — same note)
    "unified-config-interface"
    "unified-events-interface"
    "api-contracts"
    (add "unified-market-interface" if service uses market data adapters)
    (add "unified-trade-execution-interface" if service submits orders)
  Required dev dependencies:
    "ruff==0.15.0"
    "pytest>=9.0.1"
    "pytest-cov>=7.0.0"
    "pytest-asyncio>=0.25.0"
    "basedpyright"
  REMOVE from dependencies (route through unified libraries):
    "google-cloud-storage"
    "google-cloud-bigquery"
    "boto3"
    "google-cloud-pubsub"
    (any other direct google-cloud-* unless explicitly needed for auth)
  Python: requires-python = ">=3.13,<3.14"

Step 4 — Remove direct API key access from service code
  Search for: os.getenv("*API_KEY*"), os.environ.get("*KEY*"), os.environ["*KEY*"]
  If found in service source (NOT in tests/):
    - If it is an external venue API key (Tardis, Databento, FRED, exchange keys):
      Move to config class as: field_name: str = Field(default="")
      Access via config.field_name
      NOTE: Long-term these should be in library adapters (UMI, URDI) — but for now,
      config class access is the correct intermediate step.
    - If it is infrastructure metadata (VM_INSTANCE_NAME, HOSTNAME): leave it
    - If it is GCP_PROJECT_ID: replace with config.gcp_project_id

Step 5 — Verify GCSEventSink wiring
  In main.py or startup code, ensure pattern is:
    from unified_trading_services import GCSEventSink, setup_service
    setup_service(
        service_name="<service-name>",
        mode="batch",  # or "live" for live services
        sink=GCSEventSink(
            project_id=config.gcp_project_id,
            bucket=config.events_bucket,
            service_name="<service-name>",
        ),
    )
  If service uses legacy setup_events without GCSEventSink: update to above pattern.
  If GCSEventSink already wired: verify it uses new import name (UTS).

Step 6 — Delete orphaned / deprecated code
  Delete if found:
    Any file with "_old.py", "_legacy.py", "_deprecated.py" suffix
    Any file with "# deprecated" or "# legacy" header
    Imports that reference modules known to be deleted:
      unified_trading_services.domain.*  (whole domain/ package was deleted from UCS)
      unified_trading_services.core.cloud_config (moved to UCLI)
      unified_trading_services.core.market_category (moved to api_contracts)
    Dead code blocks (functions never called, imports never used)
      — Ruff will flag these as errors; trust RED squiggles

Step 7 — Verify minimum required files exist (create stubs if missing)
  Required files per service:
    <service_package>/__init__.py
    <service_package>/config.py  — class <ServiceName>Config(UnifiedCloudConfig)
    tests/__init__.py
    tests/unit/__init__.py
    tests/unit/test_event_logging.py  — standard 11-event lifecycle test
    pyrightconfig.json  — {"pythonVersion": "3.13", "strict": true, "include": ["<service_package>"]}
    .env.example
  If test_event_logging.py is missing: create it using the standard pattern:
    from unified_events_interface import MockEventSink
    (reference: unified-trading-codex/03-observability/lifecycle-events.md)

Step 8 — Quick sanity check (python -c ONLY)
  python -c "import <service_package>; print('OK')"
  If it raises: fix the broken import. Do NOT skip or comment it out.
  Then: pytest tests/unit/ -x --no-header -q
  Log failures but do NOT block on them — structural changes may break some tests
  that depend on now-deleted UCS domain/ logic.

═══════════════════════════════════════════════════════════════
SECTION 7 — QUALITY GATE STRUCTURE HARDENING (non-blocking)
═══════════════════════════════════════════════════════════════

After Phase 1 completes, a single cleanup agent (Agent 2) should verify
that every service repo has the hardened quality gate scaffold:

AGENT 2 — QG scaffold audit + fix (run after all Phase 1 agents done)
Touches: all 12 service repos (read-heavy, targeted writes only)

For each service, verify scripts/quality-gates.sh has:
  STEP 5.5: Dependency tier check (no Tier 2 in Tier 0-1)
  STEP 5.6: No Tier 2 importing from Tier 1 (REPO_ARCH_TIER enforcement)
  MIN_COVERAGE=35 (absolute minimum; should be 50 for production readiness)
  Ruff version: ruff==0.15.0 (match pyproject.toml dev dep)

Reference hardened template:
  unified-trading-codex/06-coding-standards/quality-gates.md
  (REPO_ARCH_TIER=service for all service repos)

If quality-gates.sh is missing or severely outdated:
  Copy from closest similar service (e.g., instruments-service is most up-to-date)
  Update service name references inside the script

Do NOT run quality-gates.sh — just verify the file structure is correct.

═══════════════════════════════════════════════════════════════
SECTION 8 — CODEX REFERENCES (read before acting)
═══════════════════════════════════════════════════════════════

Required reading before service updates:
  unified-trading-codex/06-coding-standards/README.md        (config, imports, types)
  unified-trading-codex/03-observability/lifecycle-events.md  (11 required events)
  unified-trading-codex/06-coding-standards/quality-gates.md  (QG structure)
  unified-trading-codex/05-infrastructure/unified-libraries/dependency-matrix.md

Import routing reference:
  unified-trading-pm/plans/ai/claude_plan_26_02.md  SECTION 5 (IMPORT ROUTING MAP)

Tier architecture reference:
  unified-trading-pm/plans/ai/claude_plan_26_02.md  SECTION 2 (TARGET ARCHITECTURE)

Dataset registry (PathRegistry spec):
  unified-trading-pm/plans/ai/claude_plan_26_02.md  SECTION 3

Domain client specs (14 clients, method signatures):
  unified-trading-pm/plans/ai/claude_plan_26_02.md  SECTION 4

Tier 1/2 library hardening plan (context):
  .cursor/plans/tier_1_and_tier_2_library_hardening_2d05e68a.plan.md

Library ecosystem plan (context):
  unified-trading-pm/plans/ai/library_ecosystem.plan.md

═══════════════════════════════════════════════════════════════
SECTION 9 — EXECUTION ORDER
═══════════════════════════════════════════════════════════════

  Phase 0 (1 agent, sequential):
    Agent 0: UTS alias + UDC alias + UCS __all__ fix + UDS broken import fix

  Phase 1 (4 agents, FULLY PARALLEL — zero file overlap):
    Agent 1-A: instruments-service, market-tick-data-handler, market-data-processing-service
    Agent 1-B: features-delta-one-service, features-calendar-service, features-onchain-service
    Agent 1-C: features-volatility-service, ml-training-service, ml-inference-service
    Agent 1-D: strategy-service, execution-service, pnl-attribution-service

  Phase 2 (1 agent, after all Phase 1 done):
    Agent 2: QG scaffold audit + hardening across all 12 services

═══════════════════════════════════════════════════════════════
SUCCESS CRITERIA (non-negotiable)
═══════════════════════════════════════════════════════════════

  ✅ python -c "from unified_trading_services import GCSEventSink" succeeds
  ✅ python -c "from unified_domain_client import InstrumentsDomainClient" succeeds
  ✅ Every service: zero `from unified_trading_services import` in service source
  ✅ Every service: zero `from unified_domain_client import` in service source
  ✅ Every service: zero UnifiedCloudServicesConfig references
  ✅ Every service: zero google-cloud-* or boto3 in [project.dependencies] pyproject.toml
  ✅ Every service: setup_service(sink=GCSEventSink(...)) wired at startup
  ✅ Every service: pyrightconfig.json exists with "strict": true
  ✅ Every service: tests/unit/test_event_logging.py exists
  ✅ features-onchain-service: zero unified_trading_services.domain.* imports
  ✅ No _old.py, _legacy.py, _deprecated.py files anywhere in service packages

  NOT required:
  ✗ bash scripts/quality-gates.sh passing (libraries still in transition)
  ✗ quickmerge or git commits
  ✗ All unit tests passing (some will fail due to in-progress library changes)
```
