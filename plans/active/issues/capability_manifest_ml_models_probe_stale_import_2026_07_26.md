---
doc_type: issue
title: generate_capability_manifest.py's ml_models probe fails with a stale import path (ml-service registry gap)
summary: >-
  While regenerating unified-api-contracts/openapi/capability-manifest.json with a full
  execution-service/features-service/strategy-service .venv environment (fixing the feature_group completeness gap,
  unified-api-contracts@449d1b3d), found the manifest's `service_registry:ml_models` gap_registry node stays gapped even
  with a real ml-service .venv built -- extract_service_registries()'s ml_models probe raises `ModuleNotFoundError: No
  module named 'ml_service.training.ml.model_registry'`, a different failure mode than the "no .venv" gap the other two
  registries had (a real import-path bug, not an environment-setup gap). Not investigated further or fixed (out of scope
  for the CI-scoping task that found it) -- ml-service's actual module layout needs to be checked to find the correct
  current import path, or determine the registry was renamed/removed.
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm, ml-service]
scope: [engineer]
tags: [capability-manifest, generator, ml-service, stale-import, wizard]
related:
  [
    /plans/archive/issues/defi_wizard_batch2_018_residual_findings_2026_07_26.md,
    /plans/active/issues/ci_registry_drift_uac_utl_stale_tag_version_conflict_2026_07_26.md,
  ]
created: 2026-07-26
parent_epic: infrastructure_master
priority: P3
estimate_class: refactor
assigned_vm: planning
resolved_by:
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
source: [unified-trading-pm/scripts/openapi/_capability_gaps.py, ml-service/ml_service/training/ml/model_registry.py]
---

## What I found

`unified-trading-pm/scripts/openapi/_capability_gaps.py`'s `extract_service_registries()` probes three services in their
own `.venv`s (`execution-service`, `features-service`, `ml-service`) via `_run_service_probe`. With
`execution-service`/`features-service` `.venv`s built, both probes now succeed (fixed in
`unified-api-contracts@449d1b3d`, recovering 21 real `execution_algo` + 35 real `feature_group` nodes). The `ml-service`
probe, even with a real `.venv` built (`uv sync` in `ml-service/`), fails with:

```
ml_models: ModuleNotFoundError: No module named 'ml_service.training.ml.model_registry'
```

This is a genuinely DIFFERENT failure mode than "no .venv" (the gap the other two registries had before their fix) —
it's an import-path error, meaning either:

- `_capability_gaps.py`'s hardcoded probe body imports a module path that has moved/been renamed inside `ml-service`
  since this probe was last verified working, or
- The `ml_models` registry itself was removed/restructured and the probe needs updating to match ml-service's current
  module layout, or
- Genuinely never existed at this path and the probe was written speculatively.

Not investigated further — reading ml-service's actual module tree to find the current (or correct) path is out of scope
for the CI-scoping work that surfaced this (a different repo, different craft).

## Why it matters

The manifest's `ml_models` capability surface (whatever ML-model-driven capabilities the wizard should show) is
currently ALWAYS gapped, identically in both the pre- and post-449d1b3d committed manifests — this bug predates and is
unrelated to the 449d1b3d fix, but that fix is what surfaced it clearly (by fixing the other two same-shaped gaps, this
one now stands out as the only remaining `service_registry` gap).

## Root cause + fix (2026-07-26, slot 6)

`ml_service/training/ml/model_registry.py` was **deleted** in `ml-service@40f45d8` ("refactor(ml): delete local
ModelRegistry, repoint to unified_trading_library") — its load-bearing controls were already carried into UTL's
`ModelRegistry`, and `ModelVariantConfig` moved with it. Confirmed via
`git log --all --diff-filter=D -- '**/model_registry.py'` and cross-checked against
`ml-service/ml_service/training/ml/models.py`'s own current import
(`from unified_trading_library import (... ModelVariantConfig ...)`). The probe's hardcoded import path was simply never
updated after that repoint.

Second, adjacent bug found in the same probe body: `ModelVariantConfig` used to be (apparently) a pydantic `BaseModel`
(hence `getattr(ModelVariantConfig, 'model_fields', {})` worked); the UTL version is a plain `@dataclass` (confirmed:
`ModelVariantConfig.__dataclass_fields__` has the real 4 fields, `model_fields` doesn't exist on it at all) — so
`variant_fields` was silently always empty even once the import worked. Fixed both in the same edit.

Verified live (not just read): built ml-service's `.venv` via `uv sync`, reproduced the exact
`ModuleNotFoundError: No module named 'ml_service.training.ml.model_registry'` on the old path, confirmed the fixed
probe body imports clean and `variant_fields` now populates (`instrument_id,target_params,target_type,timeframe`).
Regenerated `capability-manifest.json` with a full execution-service/features-service/ml-service `.venv` environment (no
regression to the 449d1b3d fix — `execution_algo`/`feature_group`/`param_schema` counts unchanged), confirmed
deterministic (byte-identical on a second run). Recovers 8 real `ml_model` nodes (was a single
`service_registry:ml_models` gap node) — new baseline 621 nodes / 2870 edges (prior 449d1b3d/3715d3ec baseline was
614/2760).

Shipped:

- `unified-trading-pm@da5bf1591` — probe body fix in `_capability_gaps.py`.
- `unified-api-contracts@c8029f80` — regenerated `capability-manifest.json` + orphan/readiness reports.
- `unified-trading-system-ui@be08ce4eb` — re-synced bundled manifest + updated the hardcoded node/edge count assertions
  in `tests/unit/wizard/graph.test.ts` / `tests/unit/wizard/parity-gates.test.ts` (614/2760 → 621/2870); ran the
  affected test files locally, 113/113 passed; full repo `quality-gates.sh` green (199s).

## Recommended decision

- [x] ✅ [SCRIPT] P3. Find the correct current import path for ml-service's model registry (grep
      `ml-service/ml_service/` for the actual registry module/function — likely renamed or moved since
      `_capability_gaps.py`'s probe body was written) and update the probe body in `extract_service_registries()` to
      match; OR, if the registry genuinely no longer exists, document that explicitly and consider whether the
      `ml_models` `gap_registry` node should be removed from the manifest schema entirely rather than perpetually
      gapped. Regenerate + re-sync `capability-manifest.json` into `unified-trading-system-ui` once fixed (mirroring the
      449d1b3d/3715d3ec pattern). Repos: unified-trading-pm, ml-service (read-only investigation),
      unified-api-contracts, unified-trading-system-ui.
