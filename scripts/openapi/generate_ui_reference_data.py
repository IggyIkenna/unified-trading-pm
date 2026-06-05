"""
Generate a comprehensive UI reference data file.

Extracts all registries, enums, config schemas, venue details, and strategy
constraints from the codebase — everything a UI designer needs to populate
dropdowns, filters, and understand the domain bounds.

SSOT for how this fits other UI sync paths: unified-trading-pm/docs/ui-alignment-ssot.md
Extend this script for new UAC/UIC/UCI-driven UI registries; do not add a parallel extractor.

Usage:
    python generate_ui_reference_data.py [--output-dir PATH]
"""

from __future__ import annotations

import os

os.environ.setdefault("CLOUD_PROVIDER", "local")
os.environ.setdefault("CLOUD_MOCK_MODE", "true")
os.environ.setdefault("DISABLE_AUTH", "true")
os.environ.setdefault("MOCK_STATE_MODE", "deterministic")
os.environ.setdefault("GCP_PROJECT_ID", "mock-project")
os.environ.setdefault("PUBSUB_EMULATOR_HOST", "localhost:8085")
os.environ.setdefault("STORAGE_EMULATOR_HOST", "http://localhost:4443")
os.environ.setdefault("BIGQUERY_EMULATOR_HOST", "localhost:9050")
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "mock-project")
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("API_KEY", "mock-api-key-for-openapi-gen")

import argparse
import contextlib
import enum
import json
import logging
import traceback
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def extract_enum_values(enum_class: type[enum.Enum]) -> list[str]:
    """Extract all values from an enum class."""
    return [m.value for m in enum_class]


def safe_extract(label: str, fn: object) -> object:
    """Safely extract data, returning error string on failure."""
    try:
        return fn()
    except Exception as e:
        logger.warning("  Failed to extract %s: %s", label, e)
        return f"EXTRACTION_ERROR: {e}"


def extract_uac_registries() -> dict[str, object]:
    """Extract all registry data from unified-api-contracts."""
    data: dict[str, object] = {}

    try:
        from unified_api_contracts.registry import (  # noqa: qg-deep-import
            CLOB_VENUES,
            DEX_VENUES,
            ENDPOINT_REGISTRY,
            INSTRUMENT_TYPE_FOLDER_MAP,
            INSTRUMENT_TYPES_BY_VENUE,
            SPORTS_VENUES,
            VENUE_CATEGORY_MAP,
            ZERO_ALPHA_VENUES,
        )

        data["venue_category_map"] = {str(k): str(v) for k, v in VENUE_CATEGORY_MAP.items()}
        # sorted() the inner values: INSTRUMENT_TYPES_BY_VENUE values are sets, so an unsorted
        # list comprehension emits a non-deterministic order → the registry-drift CI diff would
        # false-fail every run. (HARD RULE: generators MUST emit deterministically.)
        data["instrument_types_by_venue"] = {
            str(k): sorted(str(t) for t in v) for k, v in INSTRUMENT_TYPES_BY_VENUE.items()
        }
        data["instrument_type_folder_map"] = {str(k): str(v) for k, v in INSTRUMENT_TYPE_FOLDER_MAP.items()}
        data["clob_venues"] = sorted(str(v) for v in CLOB_VENUES)
        data["dex_venues"] = sorted(str(v) for v in DEX_VENUES)
        data["sports_venues"] = sorted(str(v) for v in SPORTS_VENUES)
        data["zero_alpha_venues"] = sorted(str(v) for v in ZERO_ALPHA_VENUES)

        # DeFi protocol registry — full venue→protocol mapping + chain context
        try:
            from unified_api_contracts.registry import (  # noqa: qg-deep-import
                DEFI_PROTOCOLS,
                DEFI_VENUE_TO_PROTOCOL,
            )

            data["defi_venue_to_protocol"] = {
                str(k): {"protocol": v[0], "chain": v[1]} for k, v in DEFI_VENUE_TO_PROTOCOL.items()
            }
            data["defi_protocols"] = [{"protocol": p[0], "chain": p[1]} for p in DEFI_PROTOCOLS]
            logger.info(
                "  DeFi protocol registry: %d venues, %d protocols", len(DEFI_VENUE_TO_PROTOCOL), len(DEFI_PROTOCOLS)
            )
        except Exception as e:
            logger.warning("  Failed to extract DeFi protocol registry: %s", e)

        # Chain RPC templates — chain_id → RPC URL template
        try:
            from unified_api_contracts.registry import CHAIN_RPC_TEMPLATES  # noqa: qg-deep-import

            data["chain_rpc_templates"] = {str(k): str(v) for k, v in CHAIN_RPC_TEMPLATES.items()}
            logger.info("  Chain RPC templates: %d chains", len(CHAIN_RPC_TEMPLATES))
        except Exception as e:
            logger.warning("  Failed to extract CHAIN_RPC_TEMPLATES: %s", e)

        # Solana DeFi protocols
        try:
            from unified_api_contracts.registry import SOLANA_DEFI_PROTOCOLS  # noqa: qg-deep-import

            data["solana_defi_protocols"] = {
                str(k): {str(pk): str(pv) for pk, pv in v.items()} for k, v in SOLANA_DEFI_PROTOCOLS.items()
            }
            logger.info("  Solana DeFi protocols: %d", len(SOLANA_DEFI_PROTOCOLS))
        except Exception as e:
            logger.warning("  Failed to extract SOLANA_DEFI_PROTOCOLS: %s", e)

        # DeFi pool pairs
        try:
            from unified_api_contracts.registry import DEFI_POOL_PAIRS  # noqa: qg-deep-import

            data["defi_pool_pairs"] = [{"base": p[0], "quote": p[1]} for p in DEFI_POOL_PAIRS]
        except Exception as e:
            logger.warning("  Failed to extract DEFI_POOL_PAIRS: %s", e)

        # Endpoint registry — extract venue capabilities
        endpoint_data = {}
        registry_items = (
            ENDPOINT_REGISTRY.items() if isinstance(ENDPOINT_REGISTRY, dict) else enumerate(ENDPOINT_REGISTRY)
        )
        for key, spec in registry_items:
            try:
                venue_name = str(getattr(spec, "venue", key))
                endpoint_data[venue_name] = {
                    "base_url": getattr(spec, "base_url", None),
                    "ws_url": getattr(spec, "ws_url", None),
                    "access_mode": str(getattr(spec, "access_mode", "")),
                    "data_types": [str(dt) for dt in getattr(spec, "data_types", [])],
                }
            except Exception:
                endpoint_data[str(key)] = "EXTRACTION_ERROR"
        data["endpoint_registry"] = endpoint_data

        logger.info("  UAC registries extracted")
    except Exception as e:
        logger.warning("  Failed to extract UAC registries: %s", e)
        traceback.print_exc()

    return data


def extract_uac_enums() -> dict[str, list[str]]:
    """Extract all enum values from UAC (auto-discovered)."""
    enums: dict[str, list[str]] = {}
    try:
        import unified_api_contracts as uac

        for name in sorted(dir(uac)):
            obj = getattr(uac, name, None)
            if obj and isinstance(obj, type) and issubclass(obj, enum.Enum) and obj is not enum.Enum:
                with contextlib.suppress(Exception):
                    enums[name] = extract_enum_values(obj)
        logger.info("  Extracted %d UAC enums (auto-discovered)", len(enums))
    except Exception as e:
        logger.warning("  Failed to extract UAC enums: %s", e)
    return enums


def extract_uic_enums() -> dict[str, list[str]]:
    """Extract all enum values from UIC."""
    enums: dict[str, list[str]] = {}

    try:
        import unified_api_contracts.internal as uic

        for name in dir(uic):
            obj = getattr(uic, name, None)
            if obj and isinstance(obj, type) and issubclass(obj, enum.Enum) and obj is not enum.Enum:
                with contextlib.suppress(Exception):
                    enums[name] = extract_enum_values(obj)

        logger.info("  Extracted %d UIC enums", len(enums))
    except Exception as e:
        logger.warning("  Failed to extract UIC enums: %s", e)

    return enums


def extract_config_schema_universe() -> dict[str, object]:
    """Extract config schemas from UCI and key services."""
    configs: dict[str, object] = {}

    # UCI UnifiedCloudConfig fields
    try:
        from unified_trading_library import UnifiedCloudConfig

        fields = {}
        for field_name, field_info in UnifiedCloudConfig.model_fields.items():
            fields[field_name] = {
                "type": str(field_info.annotation),
                "default": repr(field_info.default) if field_info.default is not None else None,
                "required": field_info.is_required(),
            }
        configs["UnifiedCloudConfig"] = {
            "source": "unified-trading-library (config_interface/)",
            "fields": fields,
        }
        logger.info("  UnifiedCloudConfig: %d fields", len(fields))
    except Exception as e:
        logger.warning("  Failed to extract UnifiedCloudConfig: %s", e)

    # UCI validation constants
    try:
        from unified_api_contracts import (
            VALID_ALGORITHMS,
            VALID_ASSET_GROUPS,
            VALID_BOOK_TYPES,
            VALID_INSTRUCTION_TYPES,
            VALID_MODES,
            VALID_TIMEFRAMES,
        )

        configs["validation_constants"] = {
            "valid_algorithms": VALID_ALGORITHMS
            if isinstance(VALID_ALGORITHMS, (list, dict))
            else str(VALID_ALGORITHMS),
            "valid_asset_groups": list(VALID_ASSET_GROUPS)
            if hasattr(VALID_ASSET_GROUPS, "__iter__")
            else str(VALID_ASSET_GROUPS),
            "valid_modes": list(VALID_MODES) if hasattr(VALID_MODES, "__iter__") else str(VALID_MODES),
            "valid_timeframes": list(VALID_TIMEFRAMES)
            if hasattr(VALID_TIMEFRAMES, "__iter__")
            else str(VALID_TIMEFRAMES),
            "valid_book_types": list(VALID_BOOK_TYPES)
            if hasattr(VALID_BOOK_TYPES, "__iter__")
            else str(VALID_BOOK_TYPES),
            "valid_instruction_types": list(VALID_INSTRUCTION_TYPES)
            if hasattr(VALID_INSTRUCTION_TYPES, "__iter__")
            else str(VALID_INSTRUCTION_TYPES),
        }
        logger.info("  Validation constants extracted")
    except Exception as e:
        logger.warning("  Failed to extract validation constants: %s", e)

    return configs


def extract_operational_modes() -> dict[str, object]:
    """Extract all operational mode axes and presets."""
    return {
        "mode_axes": {
            "ui_data": {
                "env_var": "VITE_MOCK_API",
                "mock_value": "true",
                "real_value": "false",
                "controls": "Client-side mock data vs API calls",
            },
            "ui_auth": {
                "env_var": "VITE_SKIP_AUTH",
                "mock_value": "true",
                "real_value": "false",
                "controls": "OAuth login requirement",
            },
            "api_data": {
                "env_var": "CLOUD_MOCK_MODE",
                "mock_value": "true",
                "real_value": "false",
                "controls": "Sample data vs real cloud",
            },
            "api_auth": {
                "env_var": "DISABLE_AUTH",
                "mock_value": "true",
                "real_value": "unset",
                "controls": "Token validation",
            },
            "mock_state": {
                "env_var": "MOCK_STATE_MODE",
                "mock_value": "interactive",
                "real_value": "deterministic",
                "controls": "Stateful vs stateless mock",
            },
        },
        "presets": {
            "ci": "CI smoke tests, deterministic, no cache persistence",
            "mock": "Local dev/UAT (default), interactive state, persists to .local-dev-cache/",
            "api-real": "Test APIs against real cloud data",
            "real": "Staging-like, needs credentials + OAuth",
        },
        "testing_stages": [
            "MOCK",
            "HISTORICAL",
            "LIVE_MOCK",
            "LIVE_TESTNET",
            "STAGING",
            "LIVE_REAL",
        ],
        "runtime_modes": ["LIVE", "BATCH"],
        "cloud_providers": ["GCP", "AWS", "LOCAL"],
    }


def extract_service_port_registry() -> dict[str, object]:
    """Extract the service/port mapping from ui-api-mapping.json."""
    try:
        workspace = Path(__file__).resolve().parent.parent.parent.parent
        mapping_file = workspace / "unified-trading-pm" / "scripts" / "dev" / "ui-api-mapping.json"
        if mapping_file.exists():
            with open(mapping_file) as f:
                data = json.load(f)
            return data.get("stacks", {})  # noqa: qg-empty-fallback
    except Exception as e:
        logger.warning("  Failed to read ui-api-mapping.json: %s", e)
    return {}


def extract_strategy_configs(ui_root: Path, uac_root: Path) -> list[dict[str, object]]:
    """Extract strategy configs from system-topology.json (sourced from strategy-manifest.json)."""
    topo_path = ui_root / "lib" / "registry" / "system-topology.json"
    if not topo_path.exists():
        topo_path = uac_root / "openapi" / "system-topology.json"
    if not topo_path.exists():
        logger.warning("  system-topology.json not found")
        return []

    with open(topo_path) as f:
        topo = json.load(f)

    strategies = topo.get("strategies", [])  # noqa: qg-empty-fallback
    # Return a serialisable summary per strategy for the UI
    configs: list[dict[str, object]] = []
    for s in strategies:
        configs.append(
            {
                "strategy_id": s.get("strategy_id", ""),
                "display_name": s.get("display_name", ""),
                "asset_group": s.get("asset_group", ""),
                "subcategory": s.get("subcategory", ""),
                "domain": s.get("domain", ""),
                "asset_groupes": s.get("asset_groupes", []),  # noqa: qg-empty-fallback
                "venues": s.get("venues", []),  # noqa: qg-empty-fallback
                "instruments": s.get("instruments", []),  # noqa: qg-empty-fallback
                "batch_capable": s.get("batch_capable", False),
                "live_capable": s.get("live_capable", False),
                "testnet_capable": s.get("testnet_capable", False),
            }
        )

    logger.info("  Extracted %d strategy configs", len(configs))
    return configs


def extract_execution_algos() -> dict[str, object]:
    """Extract execution algorithm definitions from UAC trading_validation."""
    algos: dict[str, object] = {}
    try:
        from unified_api_contracts import (
            VALID_ALGORITHMS,
            VALID_BOOK_TYPES,
            VALID_INSTRUCTION_TYPES,
        )

        VALID_OMS_TYPES: list[str] = ["NETTING", "HEDGING"]  # noqa: N806

        algos["algorithms"] = list(VALID_ALGORITHMS)
        algos["book_types"] = list(VALID_BOOK_TYPES)
        algos["instruction_types"] = list(VALID_INSTRUCTION_TYPES)
        algos["oms_types"] = list(VALID_OMS_TYPES)
        logger.info(
            "  Extracted %d algos, %d book types, %d instruction types",
            len(VALID_ALGORITHMS),
            len(VALID_BOOK_TYPES),
            len(VALID_INSTRUCTION_TYPES),
        )
    except Exception as e:
        logger.warning("  Failed to extract execution algos: %s", e)

    return algos


def extract_sports_bookmaker_registry() -> dict[str, dict[str, object]]:
    """Extract the full bookmaker registry from UAC."""
    registry: dict[str, dict[str, object]] = {}
    try:
        from unified_api_contracts import BOOKMAKER_REGISTRY

        for key, info in BOOKMAKER_REGISTRY.items():
            registry[key] = {
                "display_name": info.display_name,
                "category": info.category.value if hasattr(info.category, "value") else str(info.category),
                "currency": info.currency,
                "supports_live_betting": info.supports_live_betting,
                "supports_cash_out": info.supports_cash_out,
                "min_bet_gbp": str(info.min_bet_gbp),
            }
            if hasattr(info, "max_bet_gbp") and info.max_bet_gbp is not None:
                registry[key]["max_bet_gbp"] = str(info.max_bet_gbp)
            if hasattr(info, "api_docs_url") and info.api_docs_url:
                registry[key]["api_docs_url"] = info.api_docs_url

        logger.info("  Extracted %d bookmakers", len(registry))
    except Exception as e:
        logger.warning("  Failed to extract bookmaker registry: %s", e)

    return registry


def extract_defi_protocol_capabilities() -> dict[str, object]:
    """Extract DeFi protocol registry and venue-to-protocol mapping from UAC."""
    capabilities: dict[str, object] = {}
    try:
        from unified_api_contracts.registry.defi_protocol_registry import (  # noqa: qg-deep-import
            DEFI_PROTOCOLS,
            DEFI_VENUE_TO_PROTOCOL,
        )

        capabilities["protocols"] = [{"adapter_key": proto, "chain": chain} for proto, chain in DEFI_PROTOCOLS]
        capabilities["venue_to_protocol"] = {
            venue: {"adapter_key": proto, "chain": chain} for venue, (proto, chain) in DEFI_VENUE_TO_PROTOCOL.items()
        }
        logger.info(
            "  Extracted %d DeFi protocols, %d venue mappings", len(DEFI_PROTOCOLS), len(DEFI_VENUE_TO_PROTOCOL)
        )
    except Exception as e:
        logger.warning("  Failed to extract DeFi protocol capabilities: %s", e)

    # Solana DeFi protocols
    try:
        from unified_api_contracts.registry.capability_declarations import SOLANA_DEFI_PROTOCOLS  # noqa: qg-deep-import

        capabilities["solana_protocols"] = {name: dict(info) for name, info in SOLANA_DEFI_PROTOCOLS.items()}
        logger.info("  Extracted %d Solana DeFi protocols", len(SOLANA_DEFI_PROTOCOLS))
    except Exception as e:
        logger.warning("  Failed to extract Solana DeFi protocols: %s", e)

    return capabilities


def extract_tradfi_exchange_calendars() -> dict[str, dict[str, object]]:
    """Extract TradFi exchange session times from UAC session_times registry."""
    calendars: dict[str, dict[str, object]] = {}
    try:
        from unified_api_contracts.registry.session_times import _EXCHANGE_SESSIONS  # noqa: qg-deep-import

        for exchange, session in _EXCHANGE_SESSIONS.items():
            calendars[exchange] = {
                "timezone": str(session.timezone),
                "open_time": session.open_time.isoformat(),
                "close_time": session.close_time.isoformat(),
                "open_weekday": session.open_weekday,
                "close_weekday": session.close_weekday,
                "is_24_7": session.is_24_7,
            }

        logger.info("  Extracted %d exchange session calendars", len(calendars))
    except Exception as e:
        logger.warning("  Failed to extract exchange calendars: %s", e)

    return calendars


def extract_venue_data_availability() -> dict[str, dict[str, object]]:
    """Extract provider timing metadata (when data arrives post-T) from UAC."""
    availability: dict[str, dict[str, object]] = {}
    try:
        from unified_api_contracts.registry import VENUE_DATA_AVAILABILITY  # noqa: qg-deep-import

        for venue_name, entry in VENUE_DATA_AVAILABILITY.items():
            availability[venue_name] = {
                "venue_name": entry.venue_name,
                "asset_group": str(entry.asset_group),
                "availability_lag_hours": entry.availability_lag_hours,
                "available_after_utc_hour": entry.available_after_utc_hour,
                "is_t_plus_one": entry.is_t_plus_one,
                "notes": entry.notes,
            }

        logger.info("  Extracted %d venue data availability entries", len(availability))
    except Exception as e:
        logger.warning("  Failed to extract VENUE_DATA_AVAILABILITY: %s", e)

    return availability


def extract_venue_coordinates() -> dict[str, dict[str, float]]:
    """Extract stadium geographic coordinates from UAC."""
    coordinates: dict[str, dict[str, float]] = {}
    try:
        from unified_api_contracts.registry import VENUE_COORDINATES  # noqa: qg-deep-import

        for venue_id, coord in VENUE_COORDINATES.items():
            coordinates[str(venue_id)] = {
                "latitude": coord.latitude,
                "longitude": coord.longitude,
            }

        logger.info("  Extracted %d venue coordinates", len(coordinates))
    except Exception as e:
        logger.warning("  Failed to extract VENUE_COORDINATES: %s", e)

    return coordinates


def extract_tradfi_tick_data_windows() -> list[dict[str, str]]:
    """Extract date windows for expensive tick data collection from UAC."""
    windows: list[dict[str, str]] = []
    try:
        from unified_api_contracts.registry import TRADFI_TICK_DATA_WINDOWS  # noqa: qg-deep-import

        windows = list(TRADFI_TICK_DATA_WINDOWS)
        logger.info("  Extracted %d TradFi tick data windows", len(windows))
    except Exception as e:
        logger.warning("  Failed to extract TRADFI_TICK_DATA_WINDOWS: %s", e)

    return windows


def extract_mvp_cme_exchange_codes() -> list[str]:
    """Extract MVP CME exchange codes from UAC."""
    codes: list[str] = []
    try:
        from unified_api_contracts.registry import MVP_CME_EXCHANGE_CODES  # noqa: qg-deep-import

        codes = sorted(MVP_CME_EXCHANGE_CODES)
        logger.info("  Extracted %d MVP CME exchange codes", len(codes))
    except Exception as e:
        logger.warning("  Failed to extract MVP_CME_EXCHANGE_CODES: %s", e)

    return codes


def extract_strategy_registry() -> dict[str, object]:
    """Extract the full strategy registry from UAC (families, categories, archetypes, execution modes)."""
    registry: dict[str, object] = {}
    try:
        from unified_api_contracts.strategy import STRATEGY_REGISTRY  # noqa: qg-deep-import

        registry = STRATEGY_REGISTRY.to_dict()
        strategies = registry.get("strategies", registry)
        count = len(strategies) if isinstance(strategies, (list, dict)) else 0
        logger.info("  Extracted strategy registry: %d strategies", count)
    except Exception as e:
        logger.warning("  Failed to extract STRATEGY_REGISTRY: %s", e)

    return registry


def extract_client_registry() -> dict[str, object]:
    """Extract the client registry from UAC (client allocations, strategy assignments)."""
    registry: dict[str, object] = {}
    try:
        from unified_api_contracts.strategy import CLIENT_REGISTRY  # noqa: qg-deep-import

        registry = CLIENT_REGISTRY.to_dict()
        clients = registry.get("clients", registry)
        count = len(clients) if isinstance(clients, (list, dict)) else 0
        logger.info("  Extracted client registry: %d clients", count)
    except Exception as e:
        logger.warning("  Failed to extract CLIENT_REGISTRY: %s", e)

    return registry


def extract_strategy_instance_catalogue() -> dict[str, object]:
    """Extract the 5-dim strategy-instance catalogue (Plan A UAC foundation).

    ``STRATEGY_INSTANCE_CATALOGUE`` materialises the cross-product of archetype,
    venue-set-variant and share-class — the UI's <FamilyArchetypePicker> 3rd
    cascade feeds off this, and <PerformanceOverlay> uses the instance_id as
    the series key for backtest / paper / live data.
    """
    catalogue: dict[str, object] = {}
    try:
        from unified_api_contracts.internal.domain.strategy_service import (
            STRATEGY_INSTANCE_CATALOGUE,
        )

        catalogue = STRATEGY_INSTANCE_CATALOGUE.to_dict()
        instances = catalogue.get("instances", [])  # noqa: qg-empty-fallback
        count = len(instances) if isinstance(instances, list) else 0
        logger.info("  Extracted strategy instance catalogue: %d instances", count)
    except Exception as e:
        logger.warning("  Failed to extract STRATEGY_INSTANCE_CATALOGUE: %s", e)

    return catalogue


def extract_venue_set_variants() -> list[dict[str, object]]:
    """Extract the venue-set variant ladder (Plan A UAC foundation).

    Each archetype has one or more named venue-set variants (Elysium has 4 —
    base_3cex → premium_6cex → multi_evm → multi_evm_plus_sol). The UI picker
    renders these as the 3rd cascade tier with the pricing_tier label.
    """
    variants: list[dict[str, object]] = []
    try:
        from unified_api_contracts.internal.domain.strategy_service import (
            VENUE_SET_VARIANTS,
        )

        for v in VENUE_SET_VARIANTS:
            variants.append(
                {
                    "id": v.id,
                    "archetype": v.archetype.value,
                    "venues": list(v.venues),
                    "instrument_types": [it.value for it in v.instrument_types],
                    "label": v.label,
                    "pricing_tier": v.pricing_tier.value,
                }
            )
        logger.info("  Extracted venue-set variants: %d", len(variants))
    except Exception as e:
        logger.warning("  Failed to extract VENUE_SET_VARIANTS: %s", e)

    return variants


def extract_lifecycle_enums() -> dict[str, list[str]]:
    """Extract Plan A lifecycle enum values for UI dropdowns.

    ``StrategyMaturityPhase`` drives the 9-phase admin editor and the
    ``<PerformanceOverlay>`` gating. ``ProductRouting`` gates which product
    surfaces can see each instance. ``AccountType`` distinguishes odum-paper
    / odum-live seeds from live customer accounts.
    """
    result: dict[str, list[str]] = {}
    try:
        from unified_api_contracts.internal.domain.strategy_service import (
            AccountType,
            ProductRouting,
            StrategyMaturityPhase,
        )

        result["strategy_maturity_phases"] = [p.value for p in StrategyMaturityPhase]
        result["product_routings"] = [r.value for r in ProductRouting]
        result["account_types"] = [t.value for t in AccountType]
        logger.info(
            "  Extracted lifecycle enums: %d phases, %d routings, %d account types",
            len(result["strategy_maturity_phases"]),
            len(result["product_routings"]),
            len(result["account_types"]),
        )
    except Exception as e:
        logger.warning("  Failed to extract lifecycle enums: %s", e)

    return result


def validate_config_registry_coverage(pm_root: Path, uac_root: Path, repos_root: Path) -> None:
    """Check which service/api repos have config files vs config-registry.json coverage."""
    manifest_path = pm_root / "workspace-manifest.json"
    config_registry_path = uac_root / "openapi" / "config-registry.json"
    workspace_root = repos_root  # per-repo existence probe below (lenient — absent repos skipped)

    if not manifest_path.exists():
        logger.warning("  workspace-manifest.json not found at %s", manifest_path)
        return

    with open(manifest_path) as f:
        manifest = json.load(f)

    # Get repos of type "service" or "api"
    repos = manifest.get("repos", manifest.get("folders", []))  # noqa: qg-empty-fallback
    service_repos: list[dict[str, str]] = []
    for repo in repos:
        repo_type = repo.get("type", "")
        if repo_type in ("service", "api"):
            service_repos.append(repo)

    # Find which service repos have a config.py or service_config.py
    repos_with_config: list[str] = []
    for repo in service_repos:
        repo_name = repo.get("name", repo.get("path", ""))
        repo_path = workspace_root / repo_name
        if not repo_path.exists():
            continue
        # Derive package name: repo-name -> repo_name
        pkg_name = repo_name.replace("-", "_")
        config_candidates = [
            repo_path / pkg_name / "config.py",
            repo_path / pkg_name / "service_config.py",
        ]
        for candidate in config_candidates:
            if candidate.exists():
                repos_with_config.append(repo_name)
                break

    # Load config-registry.json if it exists
    registry_repos: set[str] = set()
    if config_registry_path.exists():
        with open(config_registry_path) as f:
            config_registry = json.load(f)
        for entry in config_registry if isinstance(config_registry, list) else config_registry.values():
            source = entry.get("source", "") if isinstance(entry, dict) else str(entry)
            # Extract repo name from source like "unified-trading-library (config_interface/)"
            if isinstance(source, str) and source:
                registry_repos.add(source.split(" ")[0].split("/")[0])
        # Also check top-level keys which may be service names
        if isinstance(config_registry, dict):
            for key in config_registry:
                registry_repos.add(key.replace("_", "-"))

    # Report
    missing = [r for r in repos_with_config if r not in registry_repos]
    logger.info(
        "  Services with config files: %d | In config-registry.json: %d",
        len(repos_with_config),
        len(repos_with_config) - len(missing),
    )
    for repo_name in sorted(missing):
        logger.warning("  WARNING: %s has config.py but is NOT in config-registry.json", repo_name)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate UI reference data")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory",
    )
    # Explicit repo roots so the generator works regardless of checkout layout (e.g. GitHub
    # Actions, where sibling repos can't live outside GITHUB_WORKSPACE). Each defaults to the
    # sibling-of-PM path, preserving the original local-workspace behaviour.
    parser.add_argument(
        "--ui-root", type=Path, default=None, help="Path to the unified-trading-system-ui repo (default: sibling)"
    )
    parser.add_argument(
        "--uac-root", type=Path, default=None, help="Path to the unified-api-contracts repo (default: sibling)"
    )
    parser.add_argument(
        "--pm-root", type=Path, default=None, help="Path to the unified-trading-pm repo (default: sibling)"
    )
    args = parser.parse_args()

    workspace_root = Path(__file__).resolve().parent.parent.parent.parent
    ui_root = args.ui_root or (workspace_root / "unified-trading-system-ui")
    uac_root = args.uac_root or (workspace_root / "unified-api-contracts")
    pm_root = args.pm_root or (workspace_root / "unified-trading-pm")
    output_dir = args.output_dir or (uac_root / "openapi")
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Generating UI reference data...")

    reference: dict[str, object] = {
        "_meta": {
            "description": (
                "Supplementary reference data for UI designers. Contains all "
                "registries, enums, config schemas, venue details, and operational "
                "modes — everything needed to populate dropdowns, filters, and "
                "understand domain bounds. Use alongside the OpenAPI spec."
            ),
            "generated_by": "generate_ui_reference_data.py",
            "ssot_doc": "unified-trading-pm/docs/ui-alignment-ssot.md",
        }
    }

    logger.info("\n1. Extracting UAC registries...")
    reference["registries"] = extract_uac_registries()

    logger.info("\n2. Extracting UAC enums...")
    reference["uac_enums"] = extract_uac_enums()

    logger.info("\n3. Extracting UIC enums...")
    reference["uic_enums"] = extract_uic_enums()

    logger.info("\n4. Extracting config schemas...")
    reference["config_schemas"] = extract_config_schema_universe()

    logger.info("\n5. Extracting operational modes...")
    reference["operational_modes"] = extract_operational_modes()

    logger.info("\n6. Extracting service/port registry...")
    reference["service_port_registry"] = extract_service_port_registry()

    logger.info("\n7. Extracting strategy configs from system-topology...")
    reference["strategy_configs"] = extract_strategy_configs(ui_root, uac_root)

    logger.info("\n8. Extracting execution algo definitions...")
    reference["execution_algos"] = extract_execution_algos()

    logger.info("\n9. Extracting sports bookmaker registry...")
    reference["sports_bookmaker_registry"] = extract_sports_bookmaker_registry()

    logger.info("\n10. Extracting DeFi protocol capabilities...")
    reference["defi_protocol_capabilities"] = extract_defi_protocol_capabilities()

    logger.info("\n11. Extracting TradFi exchange calendars...")
    reference["tradfi_exchange_calendars"] = extract_tradfi_exchange_calendars()

    logger.info("\n12. Extracting venue data availability...")
    reference["venue_data_availability"] = extract_venue_data_availability()

    logger.info("\n13. Extracting venue coordinates...")
    reference["venue_coordinates"] = extract_venue_coordinates()

    logger.info("\n14. Extracting TradFi tick data windows...")
    reference["tradfi_tick_data_windows"] = extract_tradfi_tick_data_windows()

    logger.info("\n15. Extracting MVP CME exchange codes...")
    reference["mvp_cme_exchange_codes"] = extract_mvp_cme_exchange_codes()

    logger.info("\n16. Extracting strategy registry...")
    reference["strategy_registry"] = extract_strategy_registry()

    logger.info("\n17. Extracting client registry...")
    reference["client_registry"] = extract_client_registry()

    logger.info("\n18. Extracting strategy-instance catalogue (Plan A 5-dim)...")
    reference["strategy_instance_catalogue"] = extract_strategy_instance_catalogue()

    logger.info("\n19. Extracting venue-set variants (Plan A)...")
    reference["venue_set_variants"] = extract_venue_set_variants()

    logger.info("\n20. Extracting lifecycle enums (Plan A maturity/routing/account)...")
    reference["lifecycle_enums"] = extract_lifecycle_enums()

    logger.info("\n21. Validating config registry coverage...")
    validate_config_registry_coverage(pm_root, uac_root, workspace_root)

    # Write output
    output_path = output_dir / "ui-reference-data.json"
    with open(output_path, "w") as f:
        # sort_keys=True for DETERMINISM: several source registries are built from sets, so
        # their dict key-iteration order varies per process → without this the registry-drift
        # CI diff false-fails every run. (HARD RULE: generators MUST emit deterministically.)
        json.dump(reference, f, indent=2, sort_keys=True, default=str)
    logger.info("\nOutput written: %s", output_path)

    # Summary
    print("\n" + "=" * 60)
    print("UI REFERENCE DATA — GENERATION SUMMARY")
    print("=" * 60)
    regs = reference.get("registries", {})  # noqa: qg-empty-fallback
    print(f"Venues in category map:  {len(regs.get('venue_category_map', {}))}")  # noqa: qg-empty-fallback
    print(f"DeFi venue→protocol:     {len(regs.get('defi_venue_to_protocol', {}))}")  # noqa: qg-empty-fallback
    print(f"DeFi protocols:          {len(regs.get('defi_protocols', []))}")  # noqa: qg-empty-fallback
    print(f"Chain RPC templates:     {len(regs.get('chain_rpc_templates', {}))}")  # noqa: qg-empty-fallback
    print(f"UAC enums:               {len(reference.get('uac_enums', {}))}")  # noqa: qg-empty-fallback
    print(f"UIC enums:               {len(reference.get('uic_enums', {}))}")  # noqa: qg-empty-fallback
    print(f"Config schemas:          {len(reference.get('config_schemas', {}))}")  # noqa: qg-empty-fallback
    print(f"Service stacks:          {len(reference.get('service_port_registry', {}))}")  # noqa: qg-empty-fallback
    print(f"Strategy configs:        {len(reference.get('strategy_configs', []))}")  # noqa: qg-empty-fallback
    print(f"Execution algos:         {len(reference.get('execution_algos', {}).get('algorithms', []))}")  # noqa: qg-empty-fallback
    print(f"Bookmakers:              {len(reference.get('sports_bookmaker_registry', {}))}")  # noqa: qg-empty-fallback
    print(f"DeFi protocols:          {len(reference.get('defi_protocol_capabilities', {}).get('protocols', []))}")  # noqa: qg-empty-fallback
    print(f"Exchange calendars:      {len(reference.get('tradfi_exchange_calendars', {}))}")  # noqa: qg-empty-fallback
    print(f"Venue data availability: {len(reference.get('venue_data_availability', {}))}")  # noqa: qg-empty-fallback
    print(f"Venue coordinates:       {len(reference.get('venue_coordinates', {}))}")  # noqa: qg-empty-fallback
    print(f"TradFi tick windows:     {len(reference.get('tradfi_tick_data_windows', []))}")  # noqa: qg-empty-fallback
    print(f"MVP CME exchange codes:  {len(reference.get('mvp_cme_exchange_codes', []))}")  # noqa: qg-empty-fallback
    sr = reference.get("strategy_registry", {})  # noqa: qg-empty-fallback
    sr_strategies = sr.get("strategies", sr) if isinstance(sr, dict) else sr
    sr_count = len(sr_strategies) if isinstance(sr_strategies, (list, dict)) else 0
    print(f"Strategy registry:       {sr_count} strategies")
    cr = reference.get("client_registry", {})  # noqa: qg-empty-fallback
    cr_clients = cr.get("clients", cr) if isinstance(cr, dict) else cr
    cr_count = len(cr_clients) if isinstance(cr_clients, (list, dict)) else 0
    print(f"Client registry:         {cr_count} clients")
    sic = reference.get("strategy_instance_catalogue", {})  # noqa: qg-empty-fallback
    sic_instances = sic.get("instances", []) if isinstance(sic, dict) else []  # noqa: qg-empty-fallback
    sic_count = len(sic_instances) if isinstance(sic_instances, list) else 0
    print(f"Strategy instance catalogue: {sic_count} instances")
    vsv = reference.get("venue_set_variants", [])  # noqa: qg-empty-fallback
    vsv_count = len(vsv) if isinstance(vsv, list) else 0
    print(f"Venue-set variants:      {vsv_count}")
    le = reference.get("lifecycle_enums", {})  # noqa: qg-empty-fallback
    le_phases = le.get("strategy_maturity_phases", []) if isinstance(le, dict) else []  # noqa: qg-empty-fallback
    print(f"Maturity phases:         {len(le_phases) if isinstance(le_phases, list) else 0}")
    print(f"\nOutput: {output_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
