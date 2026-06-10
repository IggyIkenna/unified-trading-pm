---
scope: [engineer, admin]
status: SUPERSEDED
superseded_by: cursor-configs/CLAUDE.md § "Bucket-name SSOT (b+)"
superseded_on: 2026-05-11
last_reviewed: 2026-05-17
---

# Bucket Naming and Config Standards — SUPERSEDED 2026-05-11

> **SUPERSEDED 2026-05-11 by CLAUDE.md § "Bucket-name SSOT (b+) — env-aware bucket architecture (codified 2026-05-11)"**
> — this document described the legacy `{bucket_prefix}-{gcp_project_id}` env-var pattern
> (`MARKET_DATA_BUCKET_PREFIX_CEFI`, per-category overrides). That pattern is BANNED. QG STEP 5.69 ratchet rejects
> inline f-string bucket-name building.

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
  mirror. All three stay in sync. SSOT: `plans/active/bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md`.
- **Env tier** (`${DEPLOYMENT_ENV}` → staging/prod/development) extends to ALL buckets across both clouds.
- **`pipeline_mode` lives in PATH**, NOT in bucket name.
- **Region-pinned**: GCP `asia-northeast1`, AWS `ap-northeast-1` (Tokyo same-metro, ~5× cheaper egress).
- **VM launchers MUST read `DEPLOYMENT_ENV`** before resolving any bucket.

## What you should read instead

1. `cursor-configs/CLAUDE.md` § "Bucket-name SSOT (b+)" — workspace rule + the QG ratchet.
2. `unified-trading-library/unified_trading_library/cloud_interface/bucket_naming.py` — canonical resolver code.
3. `deployment-service/configs/cloud-providers.yaml` — the per-bucket-kind registry.
4. `plans/active/bucket_name_ssot_canonicalisation_2026_05_10.md` — migration plan.
5. `plans/active/code_freeze_migrate_backfill_sequencing_2026_05_10.md` — freeze + migration sequencing.

## Why this doc was retained as a stub (not deleted)

Active plans, codex docs, and search engines reference this file path. A redirect stub preserves discoverability while
making it impossible for a reader to re-introduce the legacy env-var-prefix pattern. The stub is the closed-set deletion
gate for the legacy pattern.
