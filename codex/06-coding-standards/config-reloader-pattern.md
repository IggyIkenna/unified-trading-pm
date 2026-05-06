---
scope: [engineer]
---

<!-- POST_PLAN_BANNER_2026_05_06_FINAL -->

> **Post-2026-05-06** — read [`../POST_PLAN_REALITY_2026_05_06.md`](../POST_PLAN_REALITY_2026_05_06.md) before code/doc
> changes informed by this doc. Active plans: writegate-honest-coverage, predictions-canonical_question_group,
> data-status-multi-axis-shard. If this doc disagrees with active plans, the plans win. Flag conflicts to user.

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

## Rules

1. `CONFIG_LOADED` must fire on `__init__()` (enforced by UTL since 0.3.151)
2. `CONFIG_CHANGED` fires on every live reload (handled by `ConfigReloader._on_message_bytes`)
3. Never read raw env vars for domain config — use `ConfigReloader` or `DomainConfigReloader`
4. `replay_at(timestamp)` is the canonical pattern for batch workers needing historical config
5. Pass `project_id` explicitly — do not rely on env fallback in production code
6. Services with API keys MUST use `ApiKeyReloader` — never store keys in a frozen `self._api_keys` dict
7. `config_reloaders.py` must type `start_domain_config_reloaders(service_config: TypedConfigClass)` — no `object` type,
   no `getattr()` with fallback defaults
