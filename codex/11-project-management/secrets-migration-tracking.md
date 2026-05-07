---
title: Secrets Migration Tracking
status: planned
created: 2026-05-07
authoritative_for: Per-secret tracking matrix for the GCP Secret Manager → AWS Secrets Manager dual-write migration. Each row tracks `secret_name / current_provider / target_provider / migration_status / consumer_services / owner / target_completion_date`.
referenced_by:
  - plans/active/aws_migration_defi_first_2026_05_06.plan.md
related:
  - codex/05-infrastructure/cloud-agnostic-script-pattern.md
  - codex/04-architecture/interface-credential-convention.md
---

# Secrets Migration Tracking

> **Status:** PLANNED — stub created 2026-05-07 to anchor forward-references from active plans. Body to be filled in
> as secrets are dual-written + reconciled.

## Purpose

Track the migration of every workspace secret from GCP Secret Manager (current SSOT) to AWS Secrets Manager (target
SSOT for AWS-side workloads + dual-write source of truth during the migration window). Each row is the per-secret
contract: who consumes it, what's its dual-write status, who owns the migration, and when it's expected to clear.

## Scope

- Every secret currently in GCP Secret Manager (venue API keys, wallet private keys, Tenderly creds, signal-broadcast
  HMAC keys, etc.).
- Cross-cloud secret routing — `ApiKeyReloader` + `unified-config-interface` factory must lookup from the right
  provider per `CLOUD_PROVIDER` at runtime.
- Excluded: local-dev fake credentials (Firebase emulators, mock-mode keys); ADC-handled credentials.

## Outline (planned sections)

1. **Secret taxonomy** — venue keys, wallet keys, third-party service keys, internal HMAC, custody integration creds.
2. **Migration lifecycle states** — `gcp_only` → `dual_write` → `aws_primary` → `gcp_decommissioned`. Each transition
   has a verification step.
3. **Tracking matrix** — one row per secret: `name, gcp_resource_id, aws_resource_id, status, consumers, owner,
   last_synced_at, target_state_date`.
4. **Dual-write tooling** — script (TBD) that reads from GCP and writes to AWS, with version-pinning + rollback.
5. **Consumer-side reload** — services using `ApiKeyReloader` already hot-reload; AWS-side reload path needs verifying.
6. **Verification at cutover** — pre-cutover checklist asserting every `aws_primary`-state secret has an AWS-resident
   consumer service that successfully fetched it within the past 24h.
7. **Decommissioning** — once `aws_primary`, schedule GCP secret deletion after 30-day cooling-off.

## Cross-references

- **Plan(s) implementing this:** [`aws_migration_defi_first`](../../plans/active/aws_migration_defi_first_2026_05_06.plan.md).
- **Related codex SSOTs:** [`cloud-agnostic-script-pattern`](../05-infrastructure/cloud-agnostic-script-pattern.md), [`interface-credential-convention`](../04-architecture/interface-credential-convention.md).
- **Code:** `unified-config-interface/`, `unified-trading-library/api_key_reloader.py`.

## Open questions

- What is the dual-write cadence — push-on-change (event-driven) vs nightly batch?
- Do we require AWS-side rotation parity (if GCP rotates a secret, AWS must reflect within minutes)?
- Who is the named owner for venue keys vs internal keys vs custody keys? (need rotation table)
- How do we verify "no consumer is silently still reading from GCP" at the post-cutover stage?
