---
doc_type: plan
title: Dynamic Config Injection
summary:
status: in_progress
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-api, deployment-ui, execution-service, instruments-service, strategy-service]
scope: [engineer, admin]
tags: []
related: []
created: 2026-03-06
id: config_dynamic_injection
phase: implementation
priority: P1
overview: "Enable runtime config changes (instruments, strategies, clients, venues) without

  service redeployment. Config server writes versioned YAML to cloud storage via UCI,

  publishes per-domain events, and services hot-reload affected domain config slices

  via DomainConfigReloader.


  Architecture:

  - deployment-ui Config tab -> POST /api/config-store/{domain} -> deployment-api

  - deployment-api validates schema + writes versioned YAML via ConfigStore

  - UCI get_storage_client() -> GCS or S3 (cloud-agnostic)

  - UCI get_event_bus() -> publish config-domain-{domain} topic

  - DomainConfigReloader (UTL) subscribes per service -> downloads + validates config

  - Service component callbacks handle hot-reload without full restart


  Code changes = redeploy. Config changes = hot-reload via event bus.

  "
todos:
  - {
      id: p0-config-store-fix,
      content:
        Fix ConfigStore._get_storage() in unified-config-interface to use get_storage_client() from
        unified-cloud-interface. Add get_config_store(domain) convenience factory to __init__.py. Update pyproject.toml
        with unified-cloud-interface dependency.,
      status: completed,
    }
  - {
      id: p0-domain-schemas,
      content:
        "Add typed domain config schemas to unified-config-interface: InstrumentDomainConfig, StrategyDomainConfig,
        ClientDomainConfig, VenueDomainConfig. Each extends BaseConfig with __config_schema_version__. Add
        schema_for_domain(domain) helper. Export from __init__.py.",
      status: completed,
    }
  - {
      id: p0-queue-subscribe,
      content:
        "Add subscribe_streaming(topic, subscription_name, callback, project_id) -> Callable[[], None] to QueueClient
        ABC in unified-cloud-interface. Implement in PubSubQueueClient (GCP streaming), SQSQueueClient (long-poll),
        LocalQueueProvider (drain loop). All deferred imports.",
      status: completed,
    }
  - {
      id: p1-config-reloader-cloud-agnostic,
      content:
        "Refactor ConfigReloader in unified-trading-library to use get_queue_client().subscribe_streaming() instead of
        direct google.cloud.pubsub_v1. Use get_storage_client().download_bytes() for cloud URI config loading. Remove
        direct PubSub Protocol types. Support both gs:// and s3:// URIs.",
      status: completed,
    }
  - {
      id: p1-domain-config-reloader,
      content:
        "Add DomainConfigReloader[T] to unified-trading-library. Subscribes to config-domain-{domain} topics. Multiple
        callbacks (fan-out). Cloud-agnostic via get_queue_client() + get_storage_client(). Includes _cloud_uri.py shared
        utility. Unit tests added.",
      status: completed,
    }
  - {
      id: p2-config-api,
      content:
        "Add config management routes to deployment-api: POST/GET /api/config-store/{domain}, GET /versions, GET
        /versions/{ts1}/diff/{ts2}, POST /rollback/{timestamp}. Uses ConfigStore for versioned reads/writes. Publishes
        config-domain-{domain} event + logs CONFIG_CHANGED event on every write.",
      status: completed,
    }
  - {
      id: p2-config-ui,
      content:
        Add Config Management tab to deployment-ui. Domain selector tabs (instruments/strategies/clients/venues).
        Version history panel with rollback buttons. Active config JSON viewer. Edit dialog with JSON validation. Diff
        view between two versions. All API functions in client.ts.,
      status: completed,
    }
  - {
      id: p3-execution-hooks,
      content:
        Wire DomainConfigReloader in execution-service for instruments + clients domains. Add config_store_bucket field
        to ExecutionServicesConfig. Create config_reloaders.py with start/stop functions. Wire into FastAPI lifespan or
        startup event. Graceful degradation when CONFIG_STORE_BUCKET not set.,
      status: completed,
    }
  - {
      id: p3-strategy-hooks,
      content:
        Wire DomainConfigReloader in strategy-service (strategies + instruments domains) and instruments-service
        (instruments domain). Add config_store_bucket to service configs. Create config_reloaders.py per service. Wire
        into service startup/shutdown.,
      status: completed,
    }
  - {
      id: p4-quality-gates,
      content:
        "Add STEP 5.12 to quality-gates-*.sh: block direct ConfigStore() construction (must use get_config_store()). Add
        cursor rule cursor-rules/config/dynamic-config-injection.mdc. Update SSOT-INDEX if needed.",
      status: completed,
    }
  - {
      id: p4-codex,
      content:
        "Add /codex/08-workflows/config-injection.md with architecture ASCII diagram, domain schema reference, how to
        add a new domain, service wiring pattern, UI usage guide. RESOLVED 2026-03-08: File already exists (358 lines),
        covers all required sections.",
      status: completed,
    }
  - {
      id: p4-audit-integration,
      content:
        "Update trading_system_audit_prompt.md with config injection compliance checks (Sections 13.11-13.15, 14.3.8,
        2.13, 3.15-3.16, 12.16-12.20, 17.x, 22.11) that cross-reference all citadel_audit_remediation.md stream checks.
        RESOLVED 2026-03-08: All checks 13.11-13.15, 14.3.8, 2.13, 3.15-3.16 already integrated with YES answers.",
      status: completed,
    }
isProject: true
blockedBy:
  - {
      plan: phase0_standards_enforcement.md,
      reason: P0 gate must be green before P4 quality gate additions take effect in any repo.,
    }
  - {
      plan: uci_cloud_abstraction_complete.md,
      reason:
        "UCI cloud-agnostic foundations (get_storage_client, get_queue_client, get_event_bus) must be complete before
        DomainConfigReloader can work.",
    }
---

## Deferred work — migrated to:

**None** — successor: not applicable. Plan archived as 100% completed (no open `- [ ]` items at archive time). Any
incidental DEFERRED / post-cutover / out-of-scope tokens in the body are historical context, not unfinished work.

## Phase Table

| Phase | Deliverable                                                                                | Status |
| ----- | ------------------------------------------------------------------------------------------ | ------ |
| P0    | Library foundations (UCI persistence fix, domain schemas, QueueClient.subscribe_streaming) | DONE   |
| P1    | UTL hot-reload (ConfigReloader cloud-agnostic, DomainConfigReloader)                       | DONE   |
| P2    | Config API (deployment-api) + Config UI (deployment-ui)                                    | DONE   |
| P3    | Service wiring (execution, strategy, instruments)                                          | DONE   |
| P4    | Quality gates, cursor rules, codex, audit prompt update                                    | DONE   |

## Domain Topics

| Domain      | Topic                     | Subscribing Services                                     |
| ----------- | ------------------------- | -------------------------------------------------------- |
| instruments | config-domain-instruments | execution-service, strategy-service, instruments-service |
| strategies  | config-domain-strategies  | strategy-service, execution-service                      |
| clients     | config-domain-clients     | execution-service                                        |
| venues      | config-domain-venues      | execution-service, strategy-service                      |

## Key Design Decisions

1. **Cloud-agnostic**: All storage via `get_storage_client()`, all messaging via `get_queue_client()` from
   unified-cloud-interface. GCS/S3 and PubSub/SQS routed transparently by CLOUD_PROVIDER env var.
2. **Per-domain fan-out**: Each domain has its own topic. Services subscribe to only the domains they care about.
3. **Graceful degradation**: If CONFIG_STORE_BUCKET not set, hot-reload is disabled but service starts normally.
4. **Multiple callbacks**: `DomainConfigReloader.on_reload()` supports multiple registered callbacks — services can
   fan-out to multiple components.
5. **Rate limiting**: 5-second minimum between reloads per reloader instance.
6. **No service restart required**: Config changes propagate in <10s via hot-reload without redeployment.
7. **Code changes = redeploy**: Only code changes (new algorithms, new adapters) require deployment. Config changes
   (instrument lists, strategy params, client accounts, venues) go through the config injection system.
