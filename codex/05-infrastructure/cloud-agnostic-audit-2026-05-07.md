---
title: Cloud-Agnostic Audit (point-in-time 2026-05-07)
status: planned
created: 2026-05-07
authoritative_for: Workspace-wide audit (snapshot 2026-05-07) of every shell script + every Python script + every Cloud Run service + every adapter against the cloud-agnostic-script-pattern. Tracks compliance status + per-violation remediation owner + target completion date.
referenced_by:
  - plans/active/aws_migration_defi_first_2026_05_06.plan.md
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

- **Plan(s) implementing this:** [`aws_migration_defi_first`](../../plans/active/aws_migration_defi_first_2026_05_06.plan.md).
- **Related codex SSOTs:** [`cloud-agnostic-script-pattern`](./cloud-agnostic-script-pattern.md), [`cloud-agnostic-build-lineage`](./cloud-agnostic-build-lineage.md).
- **Code:** TBD audit script — likely `unified-trading-pm/scripts/audit/cloud-agnostic-audit.sh`.

## Open questions

- Where does the audit-table data live — a separate `.parquet`, a checked-in `.yaml`, or just a markdown table that the
  audit script regenerates?
- How do we count "violation severity" — number of call sites, frequency of execution, blast radius if it breaks at
  cutover?
- Do we hard-block PRs that introduce new violations, or just track them with an SLA?
- Who owns the audit re-run — workspace-wide infrastructure rotation, or assigned per-repo?
