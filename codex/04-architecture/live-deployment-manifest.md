---
scope: [engineer, admin]
title: Live Deployment Manifest — SSOT
type: architecture
status: living
last_reviewed: 2026-05-17
owner: deployment-platform
---

# Live Deployment Manifest — SSOT

> Created: 2026-05-15 Scope: May-23 promote workflow (Phase U1). Post-cutover Phase 2 enrichments documented in **§
> Post-cutover Phase 2 extension** below. Plan: `plans/active/promote_workflow_may23_cli_path_2026_05_10.md` § Phase U1.
> Post-cutover plan: `plans/active/promote_workflow_post_cutover_ui_pipeline_2026_05_10.md`

## What is a candidate manifest?

A **candidate manifest** is the immutable record created at the moment a strategy instance is promoted from batch→paper
or paper→live. It captures the minimum data needed to:

1. Round-trip the candidate config through the promote workflow (Promote UI → deployment-api → strategy VM launcher).
2. Provide an immutable audit trail for every promote decision.
3. Gate paper/live VM auto-launch (the launcher reads this document directly).

The manifest is **frozen at promote time** — it never mutates after creation. Post-cutover Phase 2 adds optional
enrichment fields (pinned commit SHAs, model refs, etc.) without requiring a schema break.

---

## May-23 shape — `MinimalCandidateManifest`

**UAC type**: `unified_api_contracts.internal.domain.strategy_service.candidate_manifest.MinimalCandidateManifest`

| Field                  | Type                    | Description                                                      |
| ---------------------- | ----------------------- | ---------------------------------------------------------------- |
| `manifest_id`          | `str` (UUID4)           | Unique ID; doubles as the Firestore document ID. Auto-generated. |
| `strategy_instance_id` | `str`                   | Identifies the strategy instance being promoted.                 |
| `version_id`           | `str \| None`           | Links to `StrategyVersion` if version governance is active.      |
| `archetype`            | `StrategyArchetype`     | DeFi/CeFi/TradFi archetype of the strategy.                      |
| `config_json`          | `dict[str, object]`     | The candidate's full config — frozen at promote time.            |
| `score_vector`         | `GroupBMetrics`         | Backtest score vector captured at promote time (immutable).      |
| `target_phase`         | `StrategyMaturityPhase` | `PAPER_1D` or `LIVE_EARLY` only (validated in `__post_init__`).  |
| `created_at`           | `datetime`              | UTC timestamp of manifest creation.                              |
| `created_by`           | `str`                   | Operator or service that triggered the promote.                  |
| `reason`               | `str`                   | Operator-supplied rationale for the promote decision.            |

### GroupBMetrics (frozen)

The score vector is frozen at promote time — it can never change after the decision was made.

| Field              | Type    |
| ------------------ | ------- |
| `sharpe_ratio`     | `float` |
| `calmar_ratio`     | `float` |
| `max_drawdown_pct` | `float` |
| `win_rate`         | `float` |
| `backtest_days`    | `int`   |
| `total_return_pct` | `float` |

---

## Firestore persistence

**Collection**: `strategy_candidate_manifests` **Document ID**: `manifest_id` (UUID4 string — O(1) lookup by ID)

**UTL wrapper**: `unified_trading_library.CandidateManifestStore`

```python
from unified_trading_library import CandidateManifestStore

store = CandidateManifestStore(project_id=cloud_config.gcp_project_id)
manifest_id = store.write(manifest)   # emits STRATEGY_PROMOTED_TO_CANDIDATE
manifest = store.read(manifest_id)    # returns None if not found
all_for = store.list_for_instance("strat_abc")  # newest-first
```

The collection is auto-created by Firestore on first write. No migration script needed.

---

## Event emitted

`STRATEGY_PROMOTED_TO_CANDIDATE` fires from `CandidateManifestStore.write()` on every successful write. Payload includes
`manifest_id`, `strategy_instance_id`, `target_phase`, `created_by`, `archetype`.

---

## Validation rules

- `target_phase` MUST be `PAPER_1D` or `LIVE_EARLY` — validated in `__post_init__`; raises `ValueError` otherwise.
- `strategy_instance_id`, `created_by`, `reason` are required (empty string raises `ValueError`).
- `manifest_id` is auto-generated UUID4 if not supplied (always unique per promote event).

---

## Post-cutover Phase 2 extension

> **[DELTA 2026-05-22]** **Current state:** The following fields exist on `MinimalCandidateManifest` but are always
> `None` at the May-23 cutover. The schema is intentionally minimal — post-cutover enrichment adds fields without a
> schema break. **Planned delta:** `plans/active/promote_workflow_post_cutover_ui_pipeline_2026_05_10.md` owns Phase 2
> enrichment. **Target architecture:** Promoted manifests carry pinned SHAs, model refs, features manifest version, and
> chain RPC pins for full reproducibility.

The following fields are present on `MinimalCandidateManifest` but always `None` at May-23 cutover. Post-cutover Phase 2
populates them without a UAC schema break:

| Field                       | Type                     | Purpose                                                         |
| --------------------------- | ------------------------ | --------------------------------------------------------------- |
| `pinned_shas`               | `dict[str, str] \| None` | Pinned git SHAs for every service deployed with this config.    |
| `model_refs`                | `list[ModelRef] \| None` | ML model artifact references (model_id, version, artifact_uri). |
| `features_manifest_version` | `str \| None`            | Features manifest version pinned at promote time.               |
| `chain_rpc_pins`            | `dict[str, str] \| None` | Pinned RPC endpoints for DeFi chains.                           |

`ModelRef` shape (frozen):

```python
@dataclass(frozen=True)
class ModelRef:
    model_id: str
    version: str
    artifact_uri: str
```

---

## Serialization

Both `to_firestore_dict()` and `from_firestore_dict()` are provided on `MinimalCandidateManifest` for round-trip
persistence through Firestore. The `archetype` and `target_phase` are stored as their `.value` strings; deserialization
reconstructs the enum via the enum constructor.
