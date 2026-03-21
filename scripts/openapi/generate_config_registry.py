"""
Generate a comprehensive config registry from all service configs.

Extracts every Pydantic BaseSettings/BaseConfig/BaseModel config class
from every service and interface repo, with all fields, types, defaults.

Usage:
    python generate_config_registry.py [--output-dir PATH]
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
import json
import logging
import subprocess
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# (repo_name, module_path, class_name)
CONFIG_REGISTRY: list[tuple[str, str, str]] = [
    # === API Services ===
    ("deployment-api", "deployment_api.deployment_api_config", "DeploymentApiConfig"),
    ("config-api", "config_api.config", "ConfigApiConfig"),
    ("trading-analytics-api", "trading_analytics_api.config", "TradingAnalyticsApiConfig"),
    ("batch-audit-api", "batch_audit_api.config", "BatchAuditApiConfig"),
    ("ml-inference-api", "ml_inference_api.config", "MLInferenceApiConfig"),
    ("ml-training-api", "ml_training_api.config", "MLTrainingApiConfig"),
    ("market-data-api", "market_data_api.config", "MarketDataApiConfig"),
    ("client-reporting-api", "client_reporting_api.config", "ClientReportingApiConfig"),
    # === Core Services ===
    ("alerting-service", "alerting_service.config", "AlertingSystemConfig"),
    ("execution-service", "execution_service.service_config", "ExecutionServicesConfig"),
    ("risk-and-exposure-service", "risk_and_exposure_service.config", "RiskAndExposureServiceConfig"),
    (
        "position-balance-monitor-service",
        "position_balance_monitor_service.config",
        "PositionBalanceMonitorServiceConfig",
    ),
    ("deployment-service", "deployment_service.deployment_config", "DeploymentConfig"),
    ("pnl-attribution-service", "pnl_attribution_service.config", "PnlAttributionServiceConfig"),
    ("strategy-service", "strategy_service.config", "StrategyServiceConfig"),
    # === Feature Services ===
    ("features-sports-service", "features_sports_service.config", "FeaturesSportsServiceConfig"),
    ("features-cross-instrument-service", "features_cross_instrument_service.config", "FeaturesCrossInstrumentConfig"),
    ("features-delta-one-service", "features_delta_one_service.config", "FeaturesDeltaOneConfig"),
    ("features-calendar-service", "features_calendar_service.config", "CalendarFeaturesConfig"),
    ("features-commodity-service", "features_commodity_service.config", "CommodityFeaturesConfig"),
    ("features-multi-timeframe-service", "features_multi_timeframe_service.config", "FeaturesMtfConfig"),
    # === Batch Services ===
    ("market-data-processing-service", "market_data_processing_service.config", "MarketDataProcessingServiceConfig"),
    ("batch-live-reconciliation-service", "batch_live_reconciliation_service.config", "ReconConfig"),
    ("ml-inference-service", "ml_inference_service.config", "InferenceConfig"),
    ("trading-agent-service", "trading_agent_service.config", "TradingAgentConfig"),
    # === Interfaces / Libraries ===
    ("unified-config-interface", "unified_config_interface.cloud_config", "UnifiedCloudConfig"),
    ("unified-config-interface", "unified_config_interface.base_config", "BaseConfig"),
    ("unified-config-interface", "unified_config_interface.ml_config", "MLTrainingConfig"),
    ("unified-config-interface", "unified_config_interface.domain_configs", "InstrumentDomainConfig"),
    ("unified-config-interface", "unified_config_interface.domain_configs", "StrategyDomainConfig"),
    ("unified-config-interface", "unified_config_interface.domain_configs", "ClientDomainConfig"),
    ("unified-config-interface", "unified_config_interface.domain_configs", "VenueDomainConfig"),
    ("unified-config-interface", "unified_config_interface.domain_configs", "StrategyRiskSubscriptionConfig"),
    ("unified-config-interface", "unified_config_interface.domain_configs", "CustomRiskScenarioConfig"),
    ("unified-market-interface", "unified_market_interface.config", "MarketDataProviderConfig"),
    ("unified-trade-execution-interface", "unified_trade_execution_interface.config", "OrderInterfaceConfig"),
    ("unified-trade-execution-interface", "unified_trade_execution_interface.config", "ExecutionDataSourceConfig"),
    # === Strategy internals ===
    ("strategy-service", "strategy_service.engine.core.config_loader", "StrategyConfig"),
    ("strategy-service", "strategy_service.engine.core.config_loader", "MLSignalConfig"),
    ("strategy-service", "strategy_service.engine.core.config_loader", "RiskConfig"),
    ("strategy-service", "strategy_service.engine.core.config_loader", "RebalancingConfig"),
    ("strategy-service", "strategy_service.engine.core.config_loader", "SmartOrderRoutingConfig"),
    ("strategy-service", "strategy_service.engine.core.config_loader", "BenchmarkConfig"),
    ("strategy-service", "strategy_service.engine.core.config_loader", "PositionConfig"),
]

EXTRACT_TIMEOUT = 30


def _extract_config_script(module_path: str, class_name: str) -> str:
    """Generate subprocess script to extract config fields."""
    return f"""\
import os, sys, json

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

import importlib
mod = importlib.import_module("{module_path}")
cls = getattr(mod, "{class_name}")

fields = {{}}
# Pydantic v2 BaseModel / BaseSettings
if hasattr(cls, "model_fields"):
    for name, info in cls.model_fields.items():
        ann = str(info.annotation) if info.annotation else "unknown"
        default = info.default
        if default is not None:
            try:
                json.dumps(default)  # test serializable
            except (TypeError, ValueError):
                default = repr(default)
        fields[name] = {{
            "type": ann,
            "default": default,
            "required": info.is_required(),
        }}
# TypedDict
elif hasattr(cls, "__annotations__"):
    for name, ann in cls.__annotations__.items():
        fields[name] = {{
            "type": str(ann),
            "default": None,
            "required": True,
        }}

# Determine base classes
bases = [b.__name__ for b in cls.__mro__[1:] if b.__name__ not in ("object", "BaseModel", "BaseSettings")]

result = {{
    "class_name": "{class_name}",
    "module": "{module_path}",
    "bases": bases,
    "field_count": len(fields),
    "fields": fields,
}}
json.dump(result, sys.stdout, default=str)
"""


def extract_config(repo_name: str, module_path: str, class_name: str) -> dict[str, object] | None:
    """Extract a config class's fields via subprocess."""
    script = _extract_config_script(module_path, class_name)
    try:
        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            timeout=EXTRACT_TIMEOUT,
            env={**os.environ, "PYTHONPATH": os.environ.get("PYTHONPATH", "")},
        )
        if result.returncode != 0:
            stderr_lines = result.stderr.strip().split("\n")
            last_line = stderr_lines[-1] if stderr_lines else "unknown error"
            logger.warning("  SKIP %s.%s: %s", repo_name, class_name, last_line)
            return None
        return json.loads(result.stdout)
    except subprocess.TimeoutExpired:
        logger.warning("  TIMEOUT: %s.%s", repo_name, class_name)
        return None
    except json.JSONDecodeError as e:
        logger.warning("  BAD JSON: %s.%s: %s", repo_name, class_name, e)
        return None
    except Exception as e:
        logger.warning("  ERROR: %s.%s: %s", repo_name, class_name, e)
        return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate config registry")
    parser.add_argument("--output-dir", type=Path, default=None)
    args = parser.parse_args()

    workspace_root = Path(__file__).resolve().parent.parent.parent.parent
    output_dir = args.output_dir or (workspace_root / "unified-api-contracts" / "openapi")
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Extracting config classes from %d entries...\n", len(CONFIG_REGISTRY))

    # Group by repo
    by_repo: dict[str, list[dict[str, object]]] = {}
    extracted = 0
    failed = 0

    for repo_name, module_path, class_name in CONFIG_REGISTRY:
        result = extract_config(repo_name, module_path, class_name)
        if result:
            by_repo.setdefault(repo_name, []).append(result)
            field_count = result.get("field_count", 0)
            logger.info("  OK: %s.%s (%d fields)", repo_name, class_name, field_count)
            extracted += 1
        else:
            failed += 1

    # Build output
    output = {
        "_meta": {
            "description": (
                "Config registry: every Pydantic config class from every service "
                "and interface repo, with all fields, types, and defaults. "
                "Grouped by repo/domain."
            ),
            "generated_by": "generate_config_registry.py",
            "total_configs": extracted,
            "total_repos": len(by_repo),
        },
        "configs_by_repo": by_repo,
    }

    output_path = output_dir / "config-registry.json"
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2, sort_keys=False, default=str)

    print("\n" + "=" * 60)
    print("CONFIG REGISTRY — GENERATION SUMMARY")
    print("=" * 60)
    print(f"Configs extracted:  {extracted}/{len(CONFIG_REGISTRY)}")
    print(f"Repos represented:  {len(by_repo)}")
    print(f"Failed/skipped:     {failed}")
    for repo, configs in sorted(by_repo.items()):
        total_fields = sum(c.get("field_count", 0) for c in configs)
        names = [c["class_name"] for c in configs]
        print(f"  {repo}: {', '.join(names)} ({total_fields} fields)")
    print(f"\nOutput: {output_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
