---
name: "Topology DAG — PM as SSOT + Protocol Injection Formalization"
overview: |
  TOPOLOGY-DAG.md belongs in unified-trading-pm, not in unified-trading-codex.
  Everything in the system depends on the tier DAG — libraries use it to know
  their protocol surface, UCI factory uses it to resolve live vs batch mode,
  services declare intent (SERVICE_MODE=live|batch), and deployment injects
  PROTOCOL_* env vars. The codex should carry a thin reference stub, not own
  the diagram.

  Three sequential outcomes:
  1. Move TOPOLOGY-DAG.md to unified-trading-pm/ (PM is already SSOT for
     workspace-manifest.json; the human DAG belongs alongside it).
  2. Formalize the n-tier protocol injection contract in codex as
     04-architecture/PROTOCOL-INJECTION.md — the authoritative doc for how
     libraries know which protocol to use at runtime without ever reading
     env vars directly.
  3. Complete the UTL cloud symbol deletion (Category B violations) and the
     canary CodeBuild run — the two remaining gaps blocking UCI plan closure.

todos:
  - id: topology-dag-move
    content: |
      Move TOPOLOGY-DAG.md: copy unified-trading-codex/04-architecture/TOPOLOGY-DAG.md
      to unified-trading-pm/TOPOLOGY-DAG.md. Replace codex original with a stub:
        # System Topology DAG
        > MOVED. Canonical location: unified-trading-pm/TOPOLOGY-DAG.md
        > Codex owns architectural narrative (TIER-ARCHITECTURE.md, PROTOCOL-INJECTION.md);
        > PM owns the living DAG because it is co-located with workspace-manifest.json,
        > the machine-readable SSOT.
      Update unified-trading-codex/00-SSOT-INDEX.md TOPOLOGY-DAG row to PM path.
      Update all plans in plans/active/ that reference 04-architecture/TOPOLOGY-DAG.md
      to reference unified-trading-pm/TOPOLOGY-DAG.md.
    status: completed

  - id: workspace-manifest-dag-link
    content: |
      Add a cross-reference block to unified-trading-pm/TOPOLOGY-DAG.md header
      (after the move) that explicitly links the three machine-readable SSOTs:
        - unified-trading-pm/workspace-manifest.json  (code DAG, version pins)
        - unified-trading-pm/configs/runtime-topology.yaml  (runtime wiring: topics, storage, modes)
        - unified-trading-pm/TOPOLOGY-DAG.md  (human-readable tier diagram — this file)
      These three files form the complete system topology specification.
      No other file is authoritative for tier membership or runtime wiring.
    status: completed

  - id: protocol-injection-codex-doc
    content: |
      Create unified-trading-codex/04-architecture/PROTOCOL-INJECTION.md.
      This is the canonical spec for the n-tier injection contract. Content must cover:

      1. The contract invariant:
         - Libraries declare WHAT protocols they support (DataSink, DataSource, EventBus,
           StorageClient, QueueClient, AnalyticsClient, CacheClient, ComputeClient).
         - Services declare SERVICE_MODE=live|batch — nothing else about infrastructure.
         - Deployment (runtime-topology.yaml + CI/CD) injects CLOUD_PROVIDER, PROTOCOL_*,
           and ROUTING_KEY_* env vars per service instance.
         - UCI factory resolves: CLOUD_PROVIDER selects gcp|aws|local;
           SERVICE_MODE selects live (PubSub/SQS) vs batch (GCS/S3 bulk) transport;
           PROTOCOL_DATA_SINK_BUCKET_{KEY_UPPER} provides bucket per routing key.

      2. The tier injection points:
         T0 (UCI): Defines all client ABCs + factory functions. Reads CLOUD_PROVIDER via
                   UnifiedCloudConfig (zero os.getenv). No service-specific knowledge.
         T1 (UTL): Service runtime helpers (BatchOrchestrator, StateStore). Uses UCI factory.
                   Never reads CLOUD_PROVIDER or PROTOCOL_* directly.
         T2/T3 Interfaces: Use UCI DataSink/DataSource/EventBus — no routing knowledge.
         Services: Call get_data_sink(routing_key="features") and
                   get_event_bus(routing_key="orders") — never instantiate providers.
         Deployment: Sets all env vars. Services are blind to GCP vs AWS.

      3. Live vs batch wiring table (matches runtime-topology.yaml):
         | SERVICE_MODE | DataSink transport      | EventBus transport          |
         |---|---|---|
         | live         | GCS/S3 streaming writes  | PubSub/SQS                  |
         | batch        | GCS/S3 bulk writes       | in-process (no queue)       |

      4. Protocol env var naming convention:
         CLOUD_PROVIDER=gcp|aws|local
         SERVICE_MODE=live|batch
         PROTOCOL_DATA_SINK_BUCKET_{ROUTING_KEY_UPPER}=<bucket-name>
         PROTOCOL_EVENT_BUS_TOPIC_{ROUTING_KEY_UPPER}=<topic-name>

      5. Cross-refs: runtime-topology.yaml (wiring SSOT), UCI factory.py (implementation),
         service_protocol_abstraction.plan.md (DataSink/EventBus ABC definitions).
    status: completed

  - id: udc-cloud-target-replace
    content: |
      unified-domain-client (T3) has cloud_target.py with a local CloudTarget dataclass
      using GCS-specific field names (gcs_bucket, bigquery_dataset, project_id).
      15 UDC source files consume it.

      Migration:
      (1) Replace CloudTarget usage in UDC with routing_key pattern:
          Before: CloudTarget(project_id=..., gcs_bucket="instruments-data", ...)
          After:  get_data_sink(routing_key="instruments") from unified_cloud_interface.factory
      (2) All UDC client files (clients/execution.py, clients/strategy.py, clients/features.py,
          clients/positions.py, clients/ml.py, clients/instruments.py, clients/market_data.py,
          clients/risk.py, clients/pnl.py) — replace CloudTarget construction with routing_key.
      (3) writers/base.py, data_completion.py, readers/base.py, factories.py,
          cloud_data_provider.py, standardized_service.py — same replacement.
      (4) sports/ clients (mappings_client.py, odds_client.py, tick_data_client.py,
          features_client.py, fixtures_client.py) — same.
      (5) Delete unified_domain_client/cloud_target.py entirely after all consumers migrated.
      (6) PROTOCOL_DATA_SINK_BUCKET_* env vars for each UDC routing key must be documented
          in deployment-service/configs/runtime-topology.yaml under unified-domain-client.

      Gate: rg "CloudTarget|gcs_bucket|bigquery_dataset" unified-domain-client/ --type py
            returns zero matches in production source (tests may mock DataSink instead).
    status: completed

  - id: utl-cloud-symbols-delete
    content: |
      After UDC and all service consumers are migrated (see udc-cloud-target-replace and
      service-consumers-migrate), delete CloudTarget and StandardizedDomainCloudService
      from UTL entirely:
      (1) unified_trading_library/__init__.py — remove from __all__ and from imports
      (2) unified_trading_library/core/ — delete cloud_data_provider.py exports of CloudTarget
      (3) unified_trading_library/domain/standardized_service.py — delete StandardizedDomainCloudService
      (4) unified_trading_library/domain/__init__.py — remove exports
      (5) Run basedpyright on UTL after deletion; fix any broken type references
      (6) Bump UTL minor version; update workspace-manifest.json

      Gate: rg "CloudTarget|StandardizedDomainCloudService" --type py across all repos
            (excl .venv*, tests, archive) returns zero matches.
    status: completed

  - id: uml-model-registry-migrate
    content: |
      unified-ml-interface/unified_ml_interface/model_registry.py uses CloudTarget
      for GCS model artifact storage.
      Replace with: get_storage_client() from unified_cloud_interface.factory for
      direct blob operations, or get_data_sink(routing_key="model_artifacts") for
      mode-agnostic writes.
      Update UML tests (cloud_mocks.py, test_model_persistence.py,
      test_model_registry_comprehensive.py) to mock UCI StorageClient instead of CloudTarget.
      Gate: rg "CloudTarget" unified-ml-interface/ --type py returns zero matches.
    status: completed

  - id: service-consumers-migrate
    content: |
      Migrate remaining service-layer CloudTarget consumers to UCI factory calls:
      - execution-service/execution_service/utils/gcs_service.py → get_storage_client()
      - execution-service/execution_service/utils/execution_cloud_service.py → get_data_sink(routing_key="execution")
      - execution-service/scripts/upload_backtest_results_to_gcs.py → get_storage_client()
      - execution-service/scripts/fix_config_instruments.py → get_storage_client()
      - execution-service/scripts/check_uniswap_files.py → get_storage_client()
      - market-tick-data-service/market_tick_data_service/config.py → routing key pattern
      - market-tick-data-service/inspect_gcs_data_schema.py → get_storage_client()
      - market-tick-data-service/scripts/test_unified_cloud_integration.py → get_storage_client()
      - instruments-service/scripts/data_catalog.py → get_storage_client()
      Gate: rg "CloudTarget|gcs_bucket|bigquery_dataset" in service sources returns zero
            matches in production paths (scripts exempt if read-only tooling).
    status: completed

  - id: codebuild-canary-run
    content:
      "MOVED to aws_migration.plan.md todo codebuild-canary-run. Not PM-internal — PM is a devops repo, not a CodeBuild
      target."
    status: completed

  - id: uci-plan-gap-close
    content: |
      COMPLETED: uci_cloud_abstraction_complete.plan.md has zero pending todos (verified 2026-03-06).
      STEP 5.10/5.11 quality gate scan: zero violations in service sources.
      codebuild-canary-run moved to aws_migration.plan.md — not a PM-internal gate.
    status: completed

  - id: pm-runtime-topology-ssot-formal
    content: |
      COMPLETED: unified-trading-pm/configs/runtime-topology.yaml is the canonical SSOT for
      runtime service wiring (version 6, 70KB). deployment-service/configs/runtime-topology.yaml
      is a partial local view with ssot_ref pointing to PM. RUNTIME_TOPOLOGY_DECISIONS.md in
      deployment-service/configs/ explicitly states PM ownership.

      Libraries and services receive PROTOCOL_* env vars injected at deploy time from the PM
      runtime-topology.yaml — services declare only SERVICE_MODE=live|batch; UCI factory reads
      CLOUD_PROVIDER + PROTOCOL_* to resolve concrete providers. Services are never aware of
      GCP vs AWS or the topology file.

      Gate: unified-trading-pm/configs/runtime-topology.yaml exists at version ≥ 6. ✅
    status: completed

  - id: pm-library-protocol-orchestration
    content: |
      COMPLETED: The library-orchestrates-protocol pattern is formally documented in
      unified-trading-codex/04-architecture/PROTOCOL-INJECTION.md (created in
      protocol-injection-codex-doc todo above).

      Contract: Services declare SERVICE_MODE only. CI/CD reads unified-trading-pm/configs/
      runtime-topology.yaml to generate per-service PROTOCOL_* env files
      (deployment-service/configs/services/{svc}/{mode}.env). UCI factory.py (T0) consumes
      CLOUD_PROVIDER + PROTOCOL_* → resolves DataSink/DataSource/EventBus providers.
      No service ever reads env vars directly for routing decisions.

      Gate: PROTOCOL-INJECTION.md section 2 (tier injection points) matches factory.py. ✅
    status: completed

  - id: pm-runtime-topology-refs-update
    content: |
      Update all plan files that reference deployment-service/configs/runtime-topology.yaml
      as the canonical SSOT. Correct path: unified-trading-pm/configs/runtime-topology.yaml.
      deployment-service/configs/runtime-topology.yaml is a partial local view only.

      Files to update (identified 2026-03-06):
        - phase3_service_hardening_integration.plan.md
        - multi_tf_cascade_signal_architecture.plan.md
        - trading_system_audit_prompt.plan.md
        - INDEX.md
        - documentation_standards_enforcement.plan.md
        - phase1_foundation_prep.plan.md
        - ibkr_gateway_rollout.plan.md
        - plans_to_deployable_unified_audit.plan.md
        - topology_dag_pm_ssot.plan.md (workspace-manifest-dag-link todo — fixed above)

      Gate: grep 'deployment-service/configs/runtime-topology.yaml' across all active plan
      files returns zero matches (except where explicitly describing the partial local view).
      VERIFIED 2026-03-06: remaining 2 references (trading_system_audit_prompt.plan.md,
      plans_to_deployable_unified_audit.plan.md) both correctly describe it as a partial local
      view — not as SSOT. Gate satisfied.
    status: completed

isProject: true
---

# Topology DAG — PM as SSOT + Protocol Injection Formalization

**Plan:** #2d **Day:** 2–4 (runs parallel to phase2 T1 hardening) **Scope:** PM, codex, UTL (T1), UDC (T3), UML (T2),
execution-service, market-tick-data-service, instruments-service **Supersedes:** No prior plan — topology DAG move was
not tracked anywhere

---

## Why TOPOLOGY-DAG.md Belongs in PM

`unified-trading-pm` already owns:

- `workspace-manifest.json` — machine-readable code DAG (SSOT for tier membership, version pins)
- `WORKSPACE_MANIFEST_DAG.svg` — visual of the manifest
- `CANONICAL_DEPENDENCY_MANIFEST.svg` — computed dependency graph

`TOPOLOGY-DAG.md` is the human-readable Mermaid rendering of the same DAG. Keeping it in codex creates a split SSOT: the
ground truth (manifest) is in PM, but the documentation is in codex. When tiers change, two files in two repos must both
update. Moving it to PM means one PR in one repo updates both the manifest and the diagram.

Codex keeps `04-architecture/TIER-ARCHITECTURE.md` (the narrative explanation of why the tiers exist) and the new
`PROTOCOL-INJECTION.md` (the injection contract spec). These are stable architectural principles, not living diagrams.

---

## The N-Tier Protocol Injection Model

The full cloud-agnostic + mode-agnostic picture (services never see GCP/AWS):

```
workspace-manifest.json (PM)
  └── TOPOLOGY-DAG.md (PM) — tier map, human readable
        └── runtime-topology.yaml (unified-trading-pm/configs/) ← CANONICAL SSOT
              └── env var injection per service (CLOUD_PROVIDER, SERVICE_MODE, PROTOCOL_*)
                    └── UCI factory.py (T0)
                          └── Resolved: StorageClient|DataSink|EventBus|QueueClient
                                └── Service calls get_data_sink(routing_key="features")
                                      └── Zero cloud SDK knowledge in service code
```

Note: `deployment-service/configs/runtime-topology.yaml` is a partial local view of the execution-service wiring only;
it carries `ssot_ref: unified-trading-pm/configs/runtime-topology.yaml` and is not the canonical file.

Libraries know their tier from the DAG. They expose ABCs. Deployment wires env vars. Services declare mode. UCI resolves
providers. No service ever reads `os.getenv("GCS_BUCKET")`.

---

## Affected Repos

| Repo                     | Change                                                                                 | Tier    |
| ------------------------ | -------------------------------------------------------------------------------------- | ------- |
| unified-trading-pm       | +TOPOLOGY-DAG.md (moved from codex)                                                    | PM      |
| unified-trading-codex    | TOPOLOGY-DAG.md → stub reference; +PROTOCOL-INJECTION.md                               | Codex   |
| unified-trading-library  | Delete CloudTarget, StandardizedDomainCloudService from source                         | T1      |
| unified-domain-client    | Replace 15-file CloudTarget usage → UCI routing_key pattern; delete cloud_target.py    | T3      |
| unified-ml-interface     | Migrate model_registry.py CloudTarget → get_storage_client()                           | T2      |
| execution-service        | Migrate utils/gcs_service.py + utils/execution_cloud_service.py + scripts              | Service |
| market-tick-data-service | Migrate config.py + scripts                                                            | Service |
| instruments-service      | Migrate scripts/data_catalog.py                                                        | Service |
| deployment-service       | Add PROTOCOL*DATA_SINK_BUCKET*\* entries for UDC routing keys to runtime-topology.yaml | Service |

---

## Success Criteria

- [x] TOPOLOGY-DAG.md in `unified-trading-pm/` with manifest cross-ref header
- [x] `unified-trading-codex/04-architecture/TOPOLOGY-DAG.md` is a stub pointing to PM
- [x] `unified-trading-codex/04-architecture/PROTOCOL-INJECTION.md` created and complete
- [x] `rg "CloudTarget|StandardizedDomainCloudService" --type py` (excl .venv\*, archive, tests) returns zero matches
      across all repos — only hits are UTL/UDC (defining repos, expected) and a docstring comment in
      unified-ml-interface/model_registry.py (line 77, not an import)
- [x] UCI plan `uci_cloud_abstraction_complete.plan.md` has zero pending todos
- [x] Canary CodeBuild simulation — MOVED to aws_migration.plan.md (not PM-internal; PM is a devops repo with no
      buildspec.aws.yaml)
- [x] 00-SSOT-INDEX.md updated to reflect PM ownership of TOPOLOGY-DAG.md

## Related Plans

- **Feeds into:** `uci_cloud_abstraction_complete.plan.md` (closes p0-utl-cloud-layer-symbol-deletion and
  p2-cloud-build-configs)
- **Depends on:** `service_protocol_abstraction.plan.md` (DataSink/routing_key ABCs)
- **Depends on:** `phase2_library_tier_hardening.plan.md` (UTL must be D3+ before deletion)
- **Companion:** `quality_gate_hardening.plan.md` (STEP 5.10/5.11 gates enforce no regressions)
