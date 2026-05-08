---
title: Cloud-Agnostic Audit (point-in-time 2026-05-07)
status: planned
created: 2026-05-07
authoritative_for: Workspace-wide audit (snapshot 2026-05-07) of every shell script + every Python script + every Cloud Run service + every adapter against the cloud-agnostic-script-pattern. Tracks compliance status + per-violation remediation owner + target completion date.
referenced_by:
  - plans/active/aws_migration_defi_first_2026_05_07.md
related:
  - codex/05-infrastructure/cloud-agnostic-script-pattern.md
  - codex/05-infrastructure/cloud-agnostic-build-lineage.md
---

# Cloud-Agnostic Audit (2026-05-07)

> **Status:** PLANNED — stub created 2026-05-07 to anchor forward-references from active plans. Body to be filled in
> as the audit completes; this is the punch list that drives the AWS migration.

## Purpose

Snapshot the workspace's compliance with [`cloud-agnostic-script-pattern`](./cloud-agnostic-script-pattern.md) on
2026-05-07, file-by-file. Each violation gets a remediation row (file, violation kind, owner, target date) so the AWS
migration plan has a concrete punch list rather than "we'll find them as we go."

## Scope

- All `*.sh` files under any repo's `scripts/` directory.
- All `*.py` files importing `google.cloud.*`, `boto3`, or shelling out to `gcloud`/`aws`/`gsutil`.
- All Cloud Run services' Dockerfiles + entrypoints.
- All `Dockerfile`s with cloud-specific base image references.
- Excluded: PM repo (docs only), `.venv*`, `node_modules/`, generated SVG/DAG artefacts.

## Outline (planned sections)

1. **Audit methodology** — the rg invocation, the AST walker for Python imports, the manual review for false-positives.
2. **Violation taxonomy** — `HARDCODED_GCLOUD`, `HARDCODED_GSUTIL`, `DIRECT_GOOGLE_CLOUD_IMPORT`, `MISSING_CLOUD_FLAG`,
   `HARDCODED_BUCKET_PREFIX`, `MIXED_CLOUD_NO_BRANCH`.
3. **Audit table** — one row per violation: `file:line, violation_kind, snippet, severity, owner, target_date, status`.
4. **Per-repo summary** — aggregate compliance % per repo; identify the 5 repos with the most work.
5. **Remediation roadmap** — phased fix plan; quick wins (mechanical) vs heavy lifts (services that need UCI plumbing).
6. **Re-audit cadence** — quarterly re-run + diff against this baseline; new violations get filed automatically by QG.

## Cross-references

- **Plan(s) implementing this:** [`aws_migration_defi_first`](../../plans/active/aws_migration_defi_first_2026_05_07.md).
- **Related codex SSOTs:** [`cloud-agnostic-script-pattern`](./cloud-agnostic-script-pattern.md), [`cloud-agnostic-build-lineage`](./cloud-agnostic-build-lineage.md).
- **Code:** TBD audit script — likely `unified-trading-pm/scripts/audit/cloud-agnostic-audit.sh`.

## Open questions

- Where does the audit-table data live — a separate `.parquet`, a checked-in `.yaml`, or just a markdown table that the
  audit script regenerates?
- How do we count "violation severity" — number of call sites, frequency of execution, blast radius if it breaks at
  cutover?
- Do we hard-block PRs that introduce new violations, or just track them with an SLA?
- Who owns the audit re-run — workspace-wide infrastructure rotation, or assigned per-repo?

## Inline-string bucket-name audit (2026-05-08)

First-pass enumeration ahead of the Tab 4 (AWS migration) bucket-naming SSOT consolidation
(UTL@`780a9575` shipped `cloud_interface/bucket_naming.py` as the canonical resolver).
Findings populate the audit table once methodology lands; for now they're a punch-list
for Wave 2 (consumer migration sweep).

### 1. `gs://` literals + `central-element-323112` project-id hardcodes

`grep -rn "central-element-323112\\|gs://" --include="*.py" --include="*.sh"` from
`WORKSPACE_ROOT` (excluding `.venv*`, `archive/`, `_archived/`, `node_modules/`,
`build/`, `dist/`): ~1961 hits across 80+ files. Classification:

| Category | Count | Action |
| --- | --- | --- |
| (a) UCI-resolved (lookup via `cloud_interface.factory` or new `bucket_naming.resolve_bucket_uri`) | ~95% | Compliant — no action. |
| (b) Test fixtures using SSOT-correct shape | ~3% | Compliant — no action. |
| (c) Legacy `# noqa: gs-uri` markers (already triaged, awaiting Wave 2 sweep) | ~85 sites | Wave 2 — migrate to `resolve_bucket_uri`. |
| (d) Untriaged `f"gs://"` / `f"s3://"` formatting (real anti-pattern) | ~70 sites | Wave 2 P0 — migrate. |
| (e) Module-level `BUCKET = "..."` constants | ~30 sites | Wave 2 P1 — migrate to lazy lookup. |
| (f) Operator-run one-off migration scripts (`scripts/migrate_*.py`) | small set | Compliant exception per "scripts excluded from Tier-3 default" rule. |

Hot-spot: `strategy-service/strategy_service/storage/gcs_storage_service.py` —
8+ inline `f"gs://"` sites, all `# noqa: gs-uri`-marked. Single-file refactor target
once `bucket_naming.py` ships (now done).

UTL-internal anti-pattern fix shipped 2026-05-08:
`unified-trading-library/unified_trading_library/core/seed_writer.py` (lines
167/180/192/204 previously built `f"gs://{self._bucket}/{blob}"` directly) now
routes through `_format_uri()` cached at `__init__` via `get_cloud_provider()`.
UTL@`780a9575`.

### 2. `cloud-providers.yaml` GCP↔AWS parity check

Probed `deployment-service/configs/cloud-providers.yaml`: every key under
`gcp.storage.*` has a matching key under `aws.storage.*`. **24 keys, zero drift.**
Phase 2 (deployment-service@`7da2f3d`) closed the 10 documented gaps
(`dex-pools`, `dex-swaps`, `evm-defi`, `eigenlayer-rewards`, `solana-defi`,
`pnl-store-defi`, `positions-store-defi`, `risk-store-defi`, `events`,
`config-store`). Yaml-side parity is **DONE** for the AWS plan Phase 1.5.A
yaml-parity sub-item.

### 3. Bucket-name SUFFIX drift

GCS pattern: `<kind>-central-element-323112-<asset_group>` — asset_group as
**suffix** (e.g. `pnl-store-central-element-323112-defi`).

AWS template: `unified-trading-<kind>-<asset_group>-<env>-<account>` — asset_group
as **infix** (e.g. `unified-trading-pnl-store-defi-prod-427895769566`).

**Recommendation: keep both, hide asymmetry behind `resolve_bucket_name`.** The
yaml internally maps each `kind` to per-cloud templates; same lookup-key works
for both. Migrating GCS bucket data on disk to match AWS-style infix is
prohibitively expensive (PB-scale rename) and gives nothing — the resolver
abstracts the difference. Wave 2 sweep migrates code from inline strings to the
resolver; on-disk data stays put.

### 4. Companion follow-ups (out of scope for 2026-05-08)

- `cloud_interface/constants.py:BUCKET_PREFIXES` is a drifted hardcode that
  pre-dates the yaml SSOT — missing several recently-added kinds (`dex-pools`,
  `events`, `config-store`, etc.). Migrate `constants.get_bucket_name()` to
  delegate into `bucket_naming.resolve_bucket_name()` (deprecate the hardcode).
- `UnifiedCloudConfig.<kind>_<cloud>_bucket_<asset_group>` fields (per-field
  env-var overrides) compose with `bucket_naming` rather than replace it —
  document the layering in `cloud-agnostic-script-pattern.md` § "Authentication
  (5)" extension if this layering surfaces a footgun.

### 5. AWS Phase 1 smoke readiness (2026-05-08)

Code-path readiness for `CLOUD_PROVIDER=aws` runtime swing: **🟢 GREEN.** Factory
swings cleanly between `GCSStorageClient` and `S3StorageClient`; AWS provider
methods at parity with GCS for read/write/list/exists/delete/copy on the
`StorageClient` ABC; `boto3` is a flat dep (`>=1.40.70`); production services
route through the factory rather than direct `google.cloud.storage` imports.

End-to-end Phase 1 smoke readiness: **🟡 AMBER.** Bucket-naming triple-drift
between (a) `setup-defi-buckets.sh` provisioned shape, (b) `BUCKET_PREFIXES`
hardcode in `cloud_interface/constants.py`, (c) `UnifiedCloudConfig`
per-field env-var defaults — none of the three agree on `(market_data, defi)`
target bucket. Phase 1 smoke ships TODAY with band-aid (`MARKET_DATA_S3_BUCKET_DEFI`
env explicit override), but Citadel-grade SSOT alignment requires the operator
triage call captured in
[`plans/active/issues/aws_phase_1_smoke_blockers_2026_05_08.md`](../../plans/active/issues/aws_phase_1_smoke_blockers_2026_05_08.md).
