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
        from unified_api_contracts.registry import (
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
        data["instrument_types_by_venue"] = {str(k): [str(t) for t in v] for k, v in INSTRUMENT_TYPES_BY_VENUE.items()}
        data["instrument_type_folder_map"] = {str(k): str(v) for k, v in INSTRUMENT_TYPE_FOLDER_MAP.items()}
        data["clob_venues"] = sorted(str(v) for v in CLOB_VENUES)
        data["dex_venues"] = sorted(str(v) for v in DEX_VENUES)
        data["sports_venues"] = sorted(str(v) for v in SPORTS_VENUES)
        data["zero_alpha_venues"] = sorted(str(v) for v in ZERO_ALPHA_VENUES)

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
    """Extract all enum values from UAC."""
    enums: dict[str, list[str]] = {}

    enum_imports = [
        ("OrderSide", "unified_api_contracts"),
        ("OrderType", "unified_api_contracts"),
        ("OrderStatus", "unified_api_contracts"),
        ("TimeInForce", "unified_api_contracts"),
        ("ExecutionStatus", "unified_api_contracts"),
        ("OperationType", "unified_api_contracts"),
        ("InstrumentType", "unified_api_contracts"),
        ("InstructionType", "unified_api_contracts"),
        ("MarketState", "unified_api_contracts"),
        ("Sport", "unified_api_contracts"),
        ("OddsFormat", "unified_api_contracts"),
        ("OddsType", "unified_api_contracts"),
        ("BetStatus", "unified_api_contracts"),
        ("BetSide", "unified_api_contracts"),
        ("OptionType", "unified_api_contracts"),
        ("FeeType", "unified_api_contracts"),
        ("CloudProvider", "unified_api_contracts"),
        ("ComputeTarget", "unified_api_contracts"),
        ("ScalingMode", "unified_api_contracts"),
        ("VenueCategory", "unified_api_contracts"),
        ("AlternativeDataType", "unified_api_contracts"),
        ("RiskType", "unified_api_contracts"),
        ("RiskCategory", "unified_api_contracts"),
        ("SignalSource", "unified_api_contracts"),
        ("BookmakerCategory", "unified_api_contracts"),
        ("MatchPeriod", "unified_api_contracts"),
        ("OutcomeType", "unified_api_contracts"),
        ("MarketStatus", "unified_api_contracts"),
        ("PredictionMarketCategory", "unified_api_contracts"),
    ]

    import importlib

    for enum_name, module_path in enum_imports:
        try:
            mod = importlib.import_module(module_path)
            cls = getattr(mod, enum_name, None)
            if cls and isinstance(cls, type) and issubclass(cls, enum.Enum):
                enums[enum_name] = extract_enum_values(cls)
        except Exception as e:
            logger.warning("  Failed to extract enum %s: %s", enum_name, e)

    logger.info("  Extracted %d UAC enums", len(enums))
    return enums


def extract_uic_enums() -> dict[str, list[str]]:
    """Extract all enum values from UIC."""
    enums: dict[str, list[str]] = {}

    try:
        import unified_api_contracts.internal as uic

        for name in dir(uic):
            obj = getattr(uic, name, None)
            if obj and isinstance(obj, type) and issubclass(obj, enum.Enum) and obj is not enum.Enum:
                try:
                    enums[name] = extract_enum_values(obj)
                except Exception:
                    pass

        logger.info("  Extracted %d UIC enums", len(enums))
    except Exception as e:
        logger.warning("  Failed to extract UIC enums: %s", e)

    return enums


def extract_config_schema_universe() -> dict[str, object]:
    """Extract config schemas from UCI and key services."""
    configs: dict[str, object] = {}

    # UCI UnifiedCloudConfig fields
    try:
        from unified_trading_library.config_interface import UnifiedCloudConfig

        fields = {}
        for field_name, field_info in UnifiedCloudConfig.model_fields.items():
            fields[field_name] = {
                "type": str(field_info.annotation),
                "default": repr(field_info.default) if field_info.default is not None else None,
                "required": field_info.is_required(),
            }
        configs["UnifiedCloudConfig"] = {
            "source": "unified-config-interface",
            "fields": fields,
        }
        logger.info("  UnifiedCloudConfig: %d fields", len(fields))
    except Exception as e:
        logger.warning("  Failed to extract UnifiedCloudConfig: %s", e)

    # UCI validation constants
    try:
        from unified_api_contracts import (
            VALID_ALGORITHMS,
            VALID_BOOK_TYPES,
            VALID_CATEGORIES,
            VALID_INSTRUCTION_TYPES,
            VALID_MODES,
            VALID_TIMEFRAMES,
        )

        configs["validation_constants"] = {
            "valid_algorithms": VALID_ALGORITHMS
            if isinstance(VALID_ALGORITHMS, (list, dict))
            else str(VALID_ALGORITHMS),
            "valid_categories": list(VALID_CATEGORIES)
            if hasattr(VALID_CATEGORIES, "__iter__")
            else str(VALID_CATEGORIES),
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
            return data.get("stacks", {})
    except Exception as e:
        logger.warning("  Failed to read ui-api-mapping.json: %s", e)
    return {}


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate UI reference data")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory",
    )
    args = parser.parse_args()

    workspace_root = Path(__file__).resolve().parent.parent.parent.parent
    output_dir = args.output_dir or (workspace_root / "unified-api-contracts" / "openapi")
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

    # Write output
    output_path = output_dir / "ui-reference-data.json"
    with open(output_path, "w") as f:
        json.dump(reference, f, indent=2, sort_keys=False, default=str)
    logger.info("\nOutput written: %s", output_path)

    # Summary
    print("\n" + "=" * 60)
    print("UI REFERENCE DATA — GENERATION SUMMARY")
    print("=" * 60)
    regs = reference.get("registries", {})
    print(f"Venues in category map:  {len(regs.get('venue_category_map', {}))}")
    print(f"UAC enums:               {len(reference.get('uac_enums', {}))}")
    print(f"UIC enums:               {len(reference.get('uic_enums', {}))}")
    print(f"Config schemas:          {len(reference.get('config_schemas', {}))}")
    print(f"Service stacks:          {len(reference.get('service_port_registry', {}))}")
    print(f"\nOutput: {output_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
