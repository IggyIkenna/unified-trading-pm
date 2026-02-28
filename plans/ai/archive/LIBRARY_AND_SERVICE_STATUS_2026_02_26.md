# Library and Service Status — 2026-02-26

Consolidated status for library framework and service hardening. Use with claude_plan_26_02.md — Phase 0 mostly done; agents can jump to Phase 1 (library builds) and Phase 3 (service hardening).

---

## ✅ Already Done (More Than Expected)

| Item | Status |
|------|--------|
| UCLI v1.0.0 — providers/gcp, aws, local; factory; abstractions | ✅ Complete |
| UCS __all__ stale domain symbols | ✅ Already cleaned |
| UCS core/ — 7 legacy files removed (down to 16) | ✅ Done |
| UCS → UTS alias package (unified_trading_services/__init__.py) | ✅ Exists inside UCS |
| UDS → UDC alias package (unified_domain_client/__init__.py) | ✅ Exists inside UDS |
| UDS broken imports | ✅ Already fixed (no unified_trading_services.domain.* imports) |
| pnl-attribution-service git init + commit | ✅ Has .git, recent commits |
| Service pyproject.toml direct cloud deps (10 services) | ✅ All clean |
| URDI — BaseReferenceAdapter, get_reference_adapter, venue adapters (Binance/Bybit/OKX/Deribit/Coinbase/IBKR) | ✅ Exists (60 files) |
| GracefulShutdownHandler — 11/14 services | ✅ (missing: market-data-processing, risk, position-balance-monitor, pnl-attribution) |
| UTEI UCS imports | ✅ Only docstring ref, not runtime |
| **CSVSampler + create_sampling_service** | ✅ **Restored** in unified-trading-services (utils/csv_sampler.py, core/sampling_service.py) |

---

## ❌ Still Missing — Library Framework (Plan 2)

These need to be built — none exist yet:

| Item | Target Library |
|------|----------------|
| ServiceCLI, BaseModeHandler, BatchOrchestrator, @with_retry | UCS / UTS |
| DataCompletionChecker, get_available_date_range | UDC |
| paths/ subpackage (PathRegistry, 20 datasets) | UDC |
| clients/ subpackage (14 domain clients) | UDC |
| readers/ + writers/ subpackages | UDC |
| BaseWebSocketClient, VenueRateLimiter | UMI |
| UnifiedOrderManager, OrderTracker, SmartOrderRouter | UTEI |
| FeatureCalculatorRegistry, BaseFeatureService | UFC |
| UPI (unified-position-interface) — entire repo missing | New repo |

---

## ⚠️ Small Remaining Cleanups

| Item | Notes |
|------|-------|
| UCS core/ | async_gcp_clients.py + secret_manager.py — move to UCLI (3 files left of 10 targeted) |
| UMI aster_adapter.py | 1 real `from unified_trading_services import AsterBaseClient, AsterClientConfig` left |
| UML model_registry.py | 1 `from unified_trading_services import CloudTarget, handle_storage_errors` (in try-except) |

---

## ❌ Service Hardening (Plan 4) — 0/14 Done

Everything in the table is not started across all 14 services:

| Check | Count |
|-------|-------|
| ServiceCLI | 0/14 |
| BatchOrchestrator | 0/14 |
| DataCompletionChecker | 0/14 |
| get_writer / get_reader from UDC | 0/14 |
| instruments-service still imports ccxt directly | ❌ |
| market-tick-data-handler still imports databento in service source | ❌ |
| gcs_path_utils.py still exists in 2 services | market-tick, market-data-processing |

---

## What This Means Practically

1. **Hard structural work (Plan 1)** — Essentially done. Library skeleton is there.
2. **Big remaining chunk** — Two things:
   - **Build library framework additions** (UCS service framework + UDC domain layer + UMI connectivity + UFC + UPI) — pure greenfield writing, no ripping out old code.
   - **Service hardening (Plan 4)** — Mechanical but large; needs library work done first.
3. **claude_plan_26_02.md** — Accurate and ready to run. Phase 0 mostly done; agents can jump straight into Phase 1 (library builds) and Phase 3 (service hardening). Phase 2 (repo renames) also already has the alias packages.

---

## CSVSampler / SamplingService Restore (2026-02-26)

**Context:** sampling_service.py and csv_sampler.py were deleted as "dead code" (library_foundation.plan PR-A). They are required by instruments-service, market-data-processing-service, and market-tick-data-handler.

**Restored:**
- `unified_trading_services/utils/csv_sampler.py` — CSVSampler class (debugging stub)
- `unified_trading_services/core/sampling_service.py` — SamplingService, create_sampling_service (env-based config)
- Exported from unified_trading_services __init__.py and __all__
- unified_trading_services re-exports via `from unified_trading_services import *`
