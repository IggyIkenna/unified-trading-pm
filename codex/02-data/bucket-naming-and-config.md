---
doc_type: codex-ssot
title: Bucket Naming and Config Standards — SUPERSEDED 2026-05-11
summary:
  SUPERSEDED redirect stub — the legacy {bucket_prefix}-{gcp_project_id} env-var bucket-naming pattern is BANNED; use
  resolve_bucket_name(cloud, kind, asset_group, env) per codex/05-infrastructure/bucket-isolation-model.md and the QG
  STEP 5.69 ratchet.
status: superseded
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [deployment-service, unified-trading-library, unified-trading-pm]
scope: [engineer, admin]
tags: [bucket-naming, canonicalisation, ssot-audit, migration, infrastructure]
related:
  [
    ../../plans/archive/2026_05/bucket_name_ssot_canonicalisation_2026_05_10.md,
    ../05-infrastructure/gcs-object-operations.md,
  ]
created: 2026-03-27
authoritative_for: [legacy bucket-prefix env-var pattern deletion-gate stub]
referenced_by:
  [
    codex/02-data/README.md,
    codex/02-data/data-lineage-MTDS-features-ml.md,
    codex/02-data/is-test-run-audit-2026-04-20.md,
  ]
owner:
last_reviewed: 2026-05-17
code_refs:
superseded_by: codex/05-infrastructure/bucket-isolation-model.md
superseded_on: 2026-05-11
---

# Bucket Naming and Config Standards — SUPERSEDED 2026-05-11

> **SUPERSEDED 2026-05-11 — live SSOT is now
> [`codex/05-infrastructure/bucket-isolation-model.md`](../05-infrastructure/bucket-isolation-model.md)** (four-tier
> naming, Group A vs Group B, Wave-3 folded shapes) + the `resolve_bucket_name()` resolver + the QG STEP 5.69 ratchet
> (CLAUDE.md § "Writing STORAGE code?" carries the one-line rule). This document described the legacy
> `{bucket_prefix}-{gcp_project_id}` env-var pattern (`MARKET_DATA_BUCKET_PREFIX_CEFI`, per-category overrides). That
> pattern is BANNED. QG STEP 5.69 ratchet rejects inline f-string bucket-name building.

## Canonical SSOT (NEW)

Every bucket lookup MUST go through the unified resolver:

```python
from unified_trading_library.cloud_interface.bucket_naming import resolve_bucket_name

bucket = resolve_bucket_name(
    cloud="gcp",                 # or "aws"
    kind="market-data-tick",     # registered bucket kind
    asset_group="cefi",          # cefi | defi | tradfi | sports | prediction
    env="prod",                  # staging | prod | development
)
```

- **Canonical config**: `unified_api_contracts/config/cloud-providers.yaml` (UAC-packaged — the always-available SSOT,
  since UTL is T0 and reads it via `importlib.resources`; relocated 2026-06-10 to fix the T0→T4 sibling-walk that broke
  standalone CI clones). The `deployment-service/configs/cloud-providers.yaml` copy is the authoring location + the
  local `deployment_service.env_substitutor` read; `unified-trading-pm/configs/cloud-providers.yaml` is a byte-identical
  mirror. All three stay in sync. SSOT:
  `plans/archive/2026_07/bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md`.
- **Env tier** (`${DEPLOYMENT_ENV}` → staging/prod/development) extends to ALL buckets across both clouds.
- **`pipeline_mode` lives in PATH**, NOT in bucket name.
- **Region-pinned**: GCP `asia-northeast1`, AWS `ap-northeast-1` (Tokyo same-metro, ~5× cheaper egress).
- **VM launchers MUST read `DEPLOYMENT_ENV`** before resolving any bucket.

## What you should read instead

1. [`codex/05-infrastructure/bucket-isolation-model.md`](../05-infrastructure/bucket-isolation-model.md) — the live
   naming / tiers / Group-A-vs-B / folded-Group-B SSOT. CLAUDE.md § "Writing STORAGE code?" carries the one-line
   workspace rule and the QG STEP 5.69 ratchet.
2. `unified-trading-library/unified_trading_library/cloud_interface/bucket_naming.py` — canonical resolver code.
3. `deployment-service/configs/cloud-providers.yaml` — the per-bucket-kind registry.
4. `plans/archive/2026_05/bucket_name_ssot_canonicalisation_2026_05_10.md` — migration plan (archived; complete).

## Why this doc was retained as a stub (not deleted)

Active plans, codex docs, and search engines reference this file path. A redirect stub preserves discoverability while
making it impossible for a reader to re-introduce the legacy env-var-prefix pattern. The stub is the closed-set deletion
gate for the legacy pattern.
