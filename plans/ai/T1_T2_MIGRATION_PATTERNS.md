# T1/T2 Migration Patterns for Remaining Services

**Phase 6+7 completed**: position-balance-monitor-service, pnl-attribution-service, instruments-service validation.

## Import Patterns (T1/T2)

### Cloud Primitives (Tier 1)
```python
from unified_trading_services import (
    GCSEventSink,
    setup_service,
    get_storage_client,
    get_pubsub_subscriber_client,
    handle_api_errors,
    handle_storage_errors,
    CloudTarget,
    ParquetSchemaEnforcer,
    StandardizedDomainCloudService,
    project_config,
)
```

### Domain (Tier 2)
```python
from unified_domain_client import (
    InstrumentKey,
    DateFilterService,
    validate_timestamp_date_alignment,
    InstrumentsDomainClient,
)
```

### Event Logging
```python
from unified_events_interface import log_event
from unified_trading_services import GCSEventSink, setup_service

setup_service(
    service_name="my-service",
    mode="batch",
    sink=GCSEventSink(
        project_id=config.gcp_project_id,
        bucket=getattr(config, "events_bucket", f"{config.gcp_project_id}-events"),
        service_name="my-service",
    ),
)
```

## pyproject.toml Dependencies

**Workspace path resolution** (use existing repos):

```toml
[project]
dependencies = [
    "unified-trading-services>=2.2.0,<3.0.0",
    "unified-domain-client>=1.0.0,<2.0.0",
]

[tool.uv.sources]
unified-trading-services = { path = "../unified-trading-services" }
unified-domain-client = { path = "../unified-domain-client" }
```

**Note**: `unified-trading-services` provides `unified_trading_services` (Python package). `unified-domain-client` provides both `unified_domain_client` and `unified_domain_client`. Prefer `unified_trading_services` and `unified_domain_client` for imports.

## Verification Checklist

1. **No direct cloud deps** in pyproject.toml (no `google-cloud-*` except via unified-trading-services)
2. **Imports** from `unified_trading_services` and `unified_domain_client`. Never `unified_trading_services` or `unified_domain_client` in new code.
3. **setup_service** with `sink=GCSEventSink(...)` for event logging.
4. **InstrumentsDomainClient** from `unified_domain_client` (or `unified_domain_client` if UDC not yet migrated).

## Services Remaining (Phase 8+)

- market-tick-data-handler
- market-data-processing-service
- strategy-service
- execution-services
- features-* services
- ml-* services

## unified-domain-client Package Fix

Include `unified_domain_client` in packages:

```toml
[tool.setuptools.packages.find]
include = ["unified_domain_client*", "unified_domain_client"]
```
