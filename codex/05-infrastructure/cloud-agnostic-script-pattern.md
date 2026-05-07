---
title: Cloud-Agnostic Script Pattern
status: planned
created: 2026-05-07
authoritative_for: The mandatory pattern every workspace script that touches cloud resources must follow — `--cloud {gcp,aws}` flag default from `CLOUD_PROVIDER` env, no direct gcloud/gsutil/google.cloud.storage without an AWS branch, UCI factory pattern for SDK construction.
referenced_by:
  - plans/active/aws_migration_defi_first_2026_05_06.plan.md
related:
  - codex/05-infrastructure/cloud-agnostic-audit-2026-05-07.md
  - codex/05-infrastructure/cloud-agnostic-build-lineage.md
  - codex/04-architecture/unified-cloud-interface.md
---

# Cloud-Agnostic Script Pattern

> **Status:** PLANNED — stub created 2026-05-07 to anchor forward-references from active plans. Body to be filled in
> as the work shipped by the referencing plan progresses.

## Purpose

Every script in the workspace that touches cloud resources MUST follow a single pattern so the same script runs against
GCP today and AWS tomorrow without copy-paste. This doc is the SSOT for that pattern; the audit doc tracks which scripts
already comply.

## Scope

- Bash scripts under `scripts/`, `deployment-service/scripts/`, `*/scripts/` that talk to cloud SDKs.
- Python scripts (one-off backfills, migration tools) that import cloud SDKs.
- Cloud Run services and Lambda functions (build-time cloud selection).
- Excluded: pure-local dev scripts that never touch a cloud (test runners, lint helpers).

## Outline (planned sections)

1. **The contract** — every script accepts `--cloud {gcp,aws}` (default = `${CLOUD_PROVIDER:-gcp}`); no positional
   alternative. Scripts that hardcode a provider are violations.
2. **Bash pattern** — branching on `$CLOUD`: `gcloud storage` for gcp, `aws s3` for aws. Helper sourcing from
   `deployment-service/scripts/lib/cloud-helpers.sh` (TBD).
3. **Python pattern** — use UCI factory: `from unified_cloud_interface import get_storage_client; client = get_storage_client(cloud=args.cloud)`. Never `from google.cloud import storage` directly.
4. **Bucket / object naming** — canonical names through UCI; never hardcoded `gs://` or `s3://` URIs at the call site.
5. **Authentication** — UCI handles ADC vs IAM role + cross-cloud secret manager lookups. Scripts never call
   `gcloud auth` / `aws configure` directly.
6. **Anti-patterns + lint rules** — QG step that greps for forbidden direct calls; auto-fail on `gsutil` / `gcloud
   storage` / `aws s3` outside the helper layer.
7. **Migration plan** — how legacy scripts get dragged onto the pattern incrementally (use the audit doc as the punch
   list).

## Cross-references

- **Plan(s) implementing this:** [`aws_migration_defi_first`](../../plans/active/aws_migration_defi_first_2026_05_06.plan.md) Phase 1.5.D.
- **Related codex SSOTs:** [`cloud-agnostic-audit-2026-05-07`](./cloud-agnostic-audit-2026-05-07.md), [`cloud-agnostic-build-lineage`](./cloud-agnostic-build-lineage.md).
- **Code:** `unified-cloud-interface/`, `deployment-service/scripts/lib/cloud-helpers.sh` (TBD).

## Open questions

- Should we ship a `cloud-shim` wrapper that auto-translates `gcloud storage cp` → `aws s3 cp` for legacy scripts during the migration window? (probably no — encourages laziness)
- How strict is the lint on third-party SDK imports? Allow-list (`import boto3` allowed in `aws_*.py`-suffixed files only)?
- What happens for hybrid operations (read from GCS, write to S3 during dual-write window)? Pattern needs a `--source-cloud` + `--dest-cloud` extension.
