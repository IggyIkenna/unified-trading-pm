---
doc_type: codex-ssot
title: Artifact Versioning
summary:
  3-axis versioning model (code SHA/semver · artifact content-hash+monotonic-v · schema UAC-semver) — all consumers pin
  explicit versions, no auto-upgrade anywhere; shadow-before-promote, permanent retention for replay; config_hash is the
  strategy unit-of-truth.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [deployment-service, execution-service, features-service, instruments-service, strategy-service]
scope: [engineer, admin]
tags: [artifact, versioning, ml, features, execution, strategy]
related:
  [
    /codex/04-architecture/backtest-groups.md,
    /codex/06-coding-standards/artifact-naming.md,
    /codex/02-data/feature-formula-versioning.md,
  ]
created: 2026-04-17
authoritative_for: [three-axis code/artifact/schema versioning model]
referenced_by:
  [
    /codex/02-data/feature-formula-versioning.md,
    /codex/04-architecture/backtest-groups.md,
    /codex/04-architecture/execution-policy.md,
    /codex/04-architecture/schema-versioning.md,
    /codex/04-architecture/shadow-deployment-pattern.md,
    /codex/04-architecture/strategy-execution-protocol.md,
    /codex/06-coding-standards/artifact-naming.md,
    /codex/06-coding-standards/strategy-identity-versioning.md,
  ]
owner:
last_reviewed: 2026-05-17
code_refs:
---

# Artifact Versioning

> **What it is:** The 3-axis versioning model the system uses to track code, artifacts, and schemas independently. All
> consumers reference artifacts by **explicit version** — no auto-upgrade anywhere. Version bumps are deliberate,
> auditable, replayable.

## Three independent axes

| Axis             | Tracks                                       | Versioned by                     | Change trigger  |
| ---------------- | -------------------------------------------- | -------------------------------- | --------------- |
| **Code / Build** | Service source + algo + archetype code       | Git SHA, semver on releases      | Any code change |
| **Artifact**     | Runtime configs, trained models, rule tables | Content hash + monotonic version | Content change  |
| **Schema**       | Data format / wire contract                  | UAC semver                       | Format change   |

These are **independent**. A code release may ship with no artifact changes. An artifact change (new model version)
doesn't require a code release. A schema bump may touch both.

## Why separate axes

Collapsing these conflates unrelated change velocities:

- Code changes are weekly/monthly
- Artifacts (configs, models) change daily
- Schemas change rarely

Separating lets:

- Code deployment not block model tuning
- Model rollout be per-consumer-opt-in
- Schema migrations proceed independently with back-compat windows

## Artifact types in the system

Every artifact listed below is versioned, content-hashed, and consumer-opt-in:

| Artifact                         | Owner                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            | Versioned by                                                        |
| -------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------- |
| Feature groups                   | features-service (delta_one + onchain family + others) — registry SSOT is PER-FAMILY, not a single shared file: `delta_one` uses `features_service/delta_one/app/features/registry.py`; `onchain` uses its own `BUILDER_REGISTRY` (group_name → `BuilderEntry`) in `features_service/onchain/schemas/feature_builder_registry.py` (corrected 2026-07-24, `data_pipeline_e2e_milestones_gate_2026_07_24.md` §8 — this row previously named only the delta_one path as if it were shared). Implementation details: [`feature-formula-versioning.md`](/codex/02-data/feature-formula-versioning.md) | content hash + monotonic v (per-group: `max(spec.formula_version)`) |
| ML models                        | ml-training-service                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              | content hash + monotonic v                                          |
| Execution policies (rule tables) | execution-service                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                | content hash + monotonic v                                          |
| Cost models                      | execution-service                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                | content hash + monotonic v                                          |
| Benchmark modes                  | execution-service                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                | content hash + monotonic v                                          |
| Allocator algorithms             | portfolio-allocator-service                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      | content hash + monotonic v                                          |
| Risk policies (limits tables)    | risk-and-exposure-service                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        | content hash + monotonic v                                          |
| Venue capabilities               | UAC registry                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     | semver on UAC                                                       |
| MEV policies                     | execution-service                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                | content hash + monotonic v                                          |
| Bridge selection policies        | transfer/rebalance                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               | content hash + monotonic v                                          |
| Strategy archetypes              | strategy-service codebase                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        | build version (git SHA + semver)                                    |
| Strategy configs                 | strategy-service registry                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        | content hash + monotonic v per slot-version                         |
| Reference data snapshots         | instruments-service                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              | snapshot date + version                                             |
| Event calendars                  | event-driven data providers                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      | version per update                                                  |
| Vol surface fits                 | vol-services                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     | timestamp + fit version                                             |
| Bookmaker mappings               | sports reference                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 | version per update                                                  |

## Version tuple on every event

Every event / fill / instruction carries the full tag set:

```
(
  family,
  archetype_id,
  archetype_build_version,       # the strategy code version
  strategy_instance_id,
  slot_version,
  config_hash,
  config_version,
  client_id,
  share_class,

  # per-reference (nested via config):
  model_version,                  # consumed model, if any
  feature_group_versions: [...],
  execution_policy_version,
  cost_model_version,
  risk_policy_version,
  allocator_version,
  ...
)
```

This is exhaustive for audit but collapses to compact form in hot paths (ids only; versions resolved via registry).

## Rules

### Rule 1 — Content hash as identity

Artifacts are identified by `content_hash`. Two artifacts with identical content have the same hash regardless of when
created. Enables deduplication + replay.

### Rule 2 — Monotonic version per artifact family

Within an artifact family (e.g., `CRYPTO_BTC_CATBOOST_V4` model), version increases monotonically. `v1`, `v2`, `v3` —
never skip, never reorder.

### Rule 3 — No auto-upgrade

Consumers reference artifacts by **explicit version pin**:

```yaml
model_ref: CRYPTO_BTC_CATBOOST_V4@v3
feature_group_refs:
  - crypto-ohlc-5m@v7
  - crypto-onchain-ethereum@v4
execution_policy_ref: cefi-crypto-large-size-v3
```

When a new version is published (e.g., `CRYPTO_BTC_CATBOOST_V4@v4`), consumers keep using `v3` until a deliberate config
change bumps the reference.

### Rule 4 — Consumer-opt-in upgrade

To adopt a new artifact version:

1. Update strategy config with new ref
2. Config hash changes
3. Config version increments
4. Live engine picks up new config on reload
5. Old config still replayable for audit

### Rule 5 — Shadow deployment before promoting

For material artifact upgrades (new model family, major execution policy change), run a **shadow strategy** in parallel:

```
prod: ML_DIRECTIONAL_CONTINUOUS@hyperliquid-btc-5m-usdt-prod      (model v3)
shadow: ML_DIRECTIONAL_CONTINUOUS@hyperliquid-btc-5m-usdt-v2-prod  (model v4; live but paper)
```

Compare outputs for N days; promote if behavior satisfactory. Retire old on promotion.

### Rule 6 — Retention for replay

Old artifact versions MUST be retained for:

- Audit reproducibility (regulatory + internal)
- Backtest replay over historical periods
- Post-mortem analysis

Retention policy: permanent for all artifacts referenced by any live or past strategy fill.

## Artifact registry

Every artifact is registered in an artifact registry (content-addressed store). Bucket name MUST resolve via
`unified_trading_library.cloud_interface.bucket_naming.resolve_bucket_name(cloud=..., kind="ml-models-store", env=...)`
per **Bucket-name SSOT (b+)** — never hardcode `s3://artifacts/` or `gs://...` (QG STEP 5.69 enforces). Canonical kind =
`ml-models-store-{pid}`.

```
{bucket}/{type}/{family}/{version}/
  content.json (or model.joblib for models — workspace no-pickle rule per python-backend.md;
                ONNX export is the inference-serving format per ml-inference-service model_loader.py
                docstring — pending ML-7 reconciliation in slot 8 audit ML-1/ML-7)
  meta.json (created_at, created_by, description, links to derived_from, input_hashes)
  conformance_tests_passed: true
```

Registry emits `ARTIFACT_PUBLISHED` events; downstream services can react (CI, test suites, shadow deploy).

## Dependency graph

Artifacts reference other artifacts:

```
strategy_config
  ├── archetype_build_version
  ├── feature_group_refs ──> feature group artifacts
  │                            └── underlying data period
  ├── model_ref ──> model artifact
  │                 ├── training_data_period
  │                 ├── feature_group_refs (training-time)
  │                 └── hyperparams
  ├── execution_policy_ref ──> execution policy artifact
  │                             ├── algo_library_ref
  │                             └── cost_model_ref
  ├── risk_policy_ref
  ├── mev_policy_ref (DeFi only)
  └── cost_model_ref
```

Registry stores the graph. Useful for:

- "what strategy versions depend on model v3?" → impact analysis before retiring
- "what happens if I upgrade feature group X?" → find consumer configs

## Schema versioning

Schemas (UAC) follow semver:

- **Patch** (1.4.2 → 1.4.3): doc / comment only
- **Minor** (1.4 → 1.5): backward-compatible field additions
- **Major** (1 → 2): breaking change; migration required

Consumers pin UAC major version. Major bumps enter a **deprecation window** (60 days default) during which both versions
are supported.

Full schema versioning: [schema-versioning.md](schema-versioning.md).

## Version resolution at runtime

At strategy tick:

```python
cfg = config_registry.get(strategy_instance_id, config_version)
model = model_registry.get(cfg.model_ref)                  # pin-resolved
features = feature_registry.get_batch(cfg.feature_group_refs)
exec_policy = exec_policy_registry.get(cfg.execution_policy_ref)
# ... all resolved by explicit version
```

Resolution is cached; versions are immutable; restart-safe.

## Config-hash = "unit of truth"

A strategy instance's behavior at time T is fully determined by:

- `archetype_build_version` (code)
- `config_hash` (all refs + thresholds)
- Market data up to T
- Last-known position state

Given these, the tick is deterministic (modulo non-deterministic I/O, which is logged).

## Cross-references

- Coding standards: [/codex/06-coding-standards/artifact-naming.md](/codex/06-coding-standards/artifact-naming.md)
- Strategy identity + versioning:
  [/codex/06-coding-standards/strategy-identity-versioning.md](/codex/06-coding-standards/strategy-identity-versioning.md)
- Schema versioning: [schema-versioning.md](schema-versioning.md)
- Execution policy: [execution-policy.md](execution-policy.md)
- Strategy-execution protocol: [strategy-execution-protocol.md](strategy-execution-protocol.md)

## Not in this doc

- **Per-artifact content schemas** — owned by respective service; UAC-defined
- **Storage backend** — artifact registry implementation (S3 / GCS / KV)
- **Training pipelines for models** — ml-training-service docs
- **Compile/build pipelines** — deployment-service
- **Commit/branch strategy** — CLAUDE.md + quickmerge
