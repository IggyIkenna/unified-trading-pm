---
scope: [engineer]
last_reviewed: 2026-06-25
---

# Config Reloader Pattern

## When to Use

| Class                       | Use When                                                   |
| --------------------------- | ---------------------------------------------------------- |
| `ConfigReloader`            | Simple key/value config from PubSub `config-updates` topic |
| `DomainConfigReloader`      | Domain-typed config with schema validation                 |
| Static `UnifiedCloudConfig` | Bootstrap / one-time read at startup                       |

## Required: CONFIG_LOADED on Init

Every service using `ConfigReloader` or `DomainConfigReloader` must receive a `CONFIG_LOADED` event on initialisation.
This is emitted automatically by UTL since version 0.3.151.

## Batch Pattern: replay_at(timestamp)

For batch pipeline workers that need to load config as-of a specific date:

```python
reloader = ConfigReloader(config_class=MyConfig, service_name="my-service", callback=..., project_id=...)
cfg = ConfigReloader.replay_at(
    timestamp=datetime(2026, 3, 10, tzinfo=UTC),
    config_class=MyConfig,
    service_name="my-service",
    bucket_name="config-store-my-project",
)
```

## Live Pattern: subscribe to CONFIG_CHANGED

Long-running services receive `CONFIG_CHANGED` events when config is updated. The `ConfigReloader` handles this
automatically via PubSub subscription:

```python
reloader = ConfigReloader(
    config_class=MyConfig,
    service_name="my-service",
    callback=on_config_change,
    project_id=cfg.gcp_project_id,
    config_file="gs://config-bucket/my-service.yaml",
)
reloader.start_watching()
```

## API Key Hot-Reload: `ApiKeyReloader`

Services that fetch API keys from Secret Manager (instruments-service, market-tick-data-service) must use
`ApiKeyReloader` instead of a one-shot `validate_api_keys_for_venues()` call. This ensures key rotations propagate to
running services without restarts.

```python
from unified_trading_library import ApiKeyReloader

# In preflight:
self._key_reloader = ApiKeyReloader(
    venues=active_venues,
    project_id=self.runtime.gcp_project_id,
    refresh_interval=300,  # 5 min periodic re-fetch
)
self._key_reloader.start()  # synchronous first fetch — fail-fast on missing keys

# In process() — always read from reloader, never cache:
api_keys = self._key_reloader.current_keys
```

**Key properties:**

- `start()` is synchronous for the initial fetch (fail-fast), then spawns a daemon thread for periodic refresh
- `current_keys` is thread-safe (returns a dict copy under lock)
- In CLOUD_MOCK_MODE, returns empty keys and does not start the periodic thread
- Emits `API_KEYS_REFRESHED` event when keys change
- Callbacks via `on_refresh(fn)` for logging/metrics

## QG-Enforced Service Infrastructure Requirements (Steps 5.61 / 5.62 / Schema Provenance)

These three requirements are enforced as **ERRORS** by `quality-gates.sh` on every service repo. They companion the
typed-config rule (STEP 5.34) and the `ApiKeyReloader` rule (rule 6 below).

### STEP 5.61 — `ServiceBootstrap` must appear in service source

Every deployable service MUST instantiate `ServiceBootstrap(...)` from UTL in its service source. The bootstrap is
responsible for emitting the three mandatory lifecycle events: `STARTED`, `STOPPED`, and `FAILED`. Services that omit
the bootstrap leave lifecycle telemetry dark — the orchestrator cannot detect crashes or clean shutdowns, and the
`WorkerLivenessWatchdog` misclassifies the slot.

```python
from unified_trading_library.bootstrap import ServiceBootstrap

bootstrap = ServiceBootstrap(
    service_name="my-service",
    version=__version__,
)
bootstrap.start()   # emits STARTED
# ... service work ...
bootstrap.stop()    # emits STOPPED (call in finally/teardown)
```

The QG step fails if no `ServiceBootstrap(` call is found anywhere in the service source tree.

### STEP 5.62 — `api/main.py` must use `make_health_router` with a `data_freshness` callback

Every service that exposes an HTTP API must wire a health endpoint via `make_health_router` from UTL. The router must
accept a `data_freshness` callback so the liveness check reports genuine data-pipeline staleness rather than
always-healthy.

```python
# api/main.py
from unified_trading_library.api import make_health_router

app.include_router(
    make_health_router(
        service_name="my-service",
        data_freshness=lambda: my_engine.last_capture_at,
    )
)
```

The QG step fails if `api/main.py` does not import or call `make_health_router`.

### Schema Provenance — domain types from UAC or `unified_api_contracts.internal`, never local definitions

All domain schema types (request/response bodies, event payloads, manifest rows, config dataclasses) MUST be sourced
from:

- `unified_api_contracts.<domain>` (public UAC surface), or
- `unified_api_contracts.internal` (cross-service internal contracts)

**Never define local equivalents** — a locally-defined `MyInstrumentRecord` that duplicates UAC's `InstrumentRecord`
drifts silently and breaks SIT the first time the canonical shape changes. If the type you need does not exist in UAC,
add it there (UAC owns the schema SSOT) and import it. The only exception is truly service-internal implementation
detail (e.g. a temporary `_ProcessingState` dataclass that never crosses a service boundary).

## Rules

1. `CONFIG_LOADED` must fire on `__init__()` (enforced by UTL since 0.3.151)
2. `CONFIG_CHANGED` fires on every live reload (handled by `ConfigReloader._on_message_bytes`)
3. Never read raw env vars for domain config — use `ConfigReloader` or `DomainConfigReloader`
4. `replay_at(timestamp)` is the canonical pattern for batch workers needing historical config
5. Pass `project_id` explicitly — do not rely on env fallback in production code
6. Services with API keys MUST use `ApiKeyReloader` — never store keys in a frozen `self._api_keys` dict
7. `config_reloaders.py` must type `start_domain_config_reloaders(service_config: TypedConfigClass)` — no `object` type,
   no `getattr()` with fallback defaults
8. **Per-wallet credential reload (added 2026-05-12 per
   [`api_keys_wallets_accounts_readiness_2026_05_10.md`](../../plans/active/api_keys_wallets_accounts_readiness_2026_05_10.md)
   Phase 9.H + 3.C.1)**: `execution-service/custody/cloud_kms.py` lazy-caches the plaintext PK
   per-`CloudKmsCustodyProvider` instance. When operator flips `WalletProvisioningConfig.signing_surface` (e.g.
   `CLOUD_KMS_ENCRYPTED` → `FIREBLOCKS_MPC` June-1), `ApiKeyReloader` detects the change via the wallet-config GCS
   poll + invalidates the cached PK + rebuilds the `CustodyProvider` instance per-wallet via the factory. Per-wallet
   `kms_key_uri` rotation (90d CMK auto-rotation per [`rotation-runbook.md`](../05-infrastructure/rotation-runbook.md)
   § 2) is the SAME pattern — invalidate the cache, refetch via KMS, swap PK. Pattern reference:
   `unified_trading_library.config_reloaders.ApiKeyReloader.on_refresh()` callback fires `WALLET_PROVISIONING_RELOADED`
   event consumed by execution-service to rebuild affected providers.

## Per-wallet credential class — added 2026-05-12 (Phase 9.H)

UAC SSOT:
[`WalletProvisioningConfig`](../../unified-api-contracts/unified_api_contracts/internal/domain/defi/wallet_config.py)
(`signing_surface` + `kms_key_uri` + `private_key_secret_ref` + `custodian_wallet_id`).

The reloader treats per-wallet credentials as a special class because their shape varies per `signing_surface` (May-23
`CLOUD_KMS_ENCRYPTED` requires KMS-URI + wrapped-PK; June-1 `COPPER_MPC` / `FIREBLOCKS_MPC` requires custodian wallet
ID + HMAC/RS256 keys). The reload event MUST trigger factory rebuild per-wallet, not bulk-invalidate the whole
`_api_keys` dict.

```python
# Pattern (execution-service custody loader):
class WalletCustodyReloader(ApiKeyReloader):
    """Per-wallet custody provider rebuild on config flip."""

    def on_refresh(self) -> None:
        new_config = self._fetch_wallet_provisioning_config()  # GCS poll
        for wallet_id, row in new_config.wallets.items():
            old_surface = self._cached_surface.get(wallet_id)
            if old_surface != row.signing_surface:
                # Flip detected — rebuild provider via factory
                self._providers[wallet_id] = get_custody_provider(
                    CustodyConfig(
                        provider=row.signing_surface_to_factory_name(),
                        kms_key_uri=row.kms_key_uri,
                        private_key_secret_ref=row.private_key_secret_ref,
                        custodian_wallet_id=row.custodian_wallet_id,
                    ),
                )
                self._cached_surface[wallet_id] = row.signing_surface
                log_event("WALLET_CUSTODY_PROVIDER_RELOADED",
                          wallet_id=wallet_id,
                          old_surface=old_surface, new_surface=row.signing_surface)
```

## StrategyDirectiveReloader pattern — added 2026-05-20 (trading-agent-service architecture unlock)

`StrategyDirectiveReloader` (in `strategy_service/config_reloaders.py`) is a **push-based in-memory store** for
`ArchetypeAllocationDirective` objects. It differs from `DomainConfigReloader` (poll-based GCS) in that directives are
pushed via `inject_directive()` rather than polled from a store.

Key properties:

- In-memory `dict[archetype_id, ArchetypeAllocationDirective]` with `threading.Lock`
- TTL eviction via `valid_until` field (directives auto-expire on `get_directive()` + each poll cycle)
- `inject_directive(directive)` / `get_directive(archetype_id)` / `poll_once()` public API
- Consumed by `AllocatorArchetypeEngine.weight_with_directive()` in `portfolio_allocator/archetypes.py`
- No-op default: absent directive → `weight()` called unchanged (static config preserved)

**Pattern**:

```python
from strategy_service.config_reloaders import StrategyDirectiveReloader

reloader = StrategyDirectiveReloader(poll_interval_seconds=60)
reloader.start()

# Push-based: trading-agent-service calls inject_directive() when emitting
reloader.inject_directive(ArchetypeAllocationDirective(archetype_id="carry_staked_basis", ...))

# Pull-based: strategy engine calls get_directive() per tick
directive = reloader.get_directive("carry_staked_basis")  # None if absent/expired
weight = engine.weight_with_directive(directive)           # fallback to static if None
```

**Thread-safety**: `_lock` guards `_directives` dict. All reads/writes use `with self._lock`. `enabled=False` directives
are stored and returned — callers must check `.enabled`.

**Post-cutover**: lifted into UTL as `make_directive_reloader()` alongside `make_config_reloader()` per
`strategy_repo_consolidation_2026_05_19.md`.

Full architecture: `codex/04-architecture/trading-agent-service-directive-pipeline.md`.
