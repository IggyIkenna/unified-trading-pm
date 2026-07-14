---
doc_type: plan
title: Deployment registry Firestore migration — Phase 4 — DynamoDB backend for AWS-readiness
summary:
  Add a DynamoDB backend implementing the same DeploymentRegistryStore contract as the Firestore backend, selected by
  the active cloud (GCP to Firestore, AWS to DynamoDB) the same way resolve_bucket_name selects GCS vs S3 — so the
  eventual AWS migration is a backend swap, not a rewrite. Wire and contract-test it now against DynamoDB Local;
  provision the table via terraform but leave it inactive until the AWS cutover flips the cloud selector.
status: active
nature: process
asset_group: [meta]
stage: [meta]
repos: [unified-trading-library, deployment-service]
scope: [engineer]
tags: [dynamodb, deployment-registry, aws, cloud-interface, migration]
related:
  - deployment_registry_firestore_migration_2026_07_14.md
  - deployment_registry_firestore_p1_dualwrite_2026_07_14.md
created: "2026-07-14"
last_updated: "2026-07-14"
parent_epic: observability_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2.4
assigned_role: infra
drift_direction: advance-code
depends_on:
  - deployment_registry_firestore_p1_dualwrite_2026_07_14.md
gate_on_depends: true
locked_by:
locked_since:
supersedes:
superseded_by:
source: deployment_registry_firestore_migration_2026_07_14.md (master, Phase 4)
---

# Phase 4 — DynamoDB backend (AWS-ready)

> **Dispatch:** `assigned_role: infra` · **model: Sonnet** (default) · **effort: high**. `status: draft` — activated by
> Phase 1's last todo (needs the `DeploymentRegistryStore` Protocol) — NOT gated on the Phase 3 cutover, so it can run
> in parallel once Phase 1 lands. Contract-defined + mechanical. **Pulled to LOCAL execution 2026-07-14**
> (`assigned_vm: NA` / `execution_scope: local-only`, same as the rest of this phase chain) — see Phase 0's Dispatch
> note for why.

## Context (read first — self-contained)

Phase 1 defined the `DeploymentRegistryStore` Protocol in UTL `cloud_interface` with a Firestore impl. This phase adds a
**DynamoDB** impl of the SAME Protocol so the registry survives the GCP→AWS migration as a backend swap. The workspace
already has an AWS provider layer to extend:
[`unified_trading_library/cloud_interface/providers/aws.py`](../../unified-trading-library/unified_trading_library/cloud_interface/providers/aws.py),
`aws_compute.py`, and `_aws_sdk_protocols.py` (lazy-loaded boto3 behind protocols — mirror this; do NOT import boto3 at
module top). Cloud selection mirrors `resolve_bucket_name` (GCS vs S3) — GCP → Firestore, AWS → DynamoDB, chosen from
the active cloud, so no caller changes.

DynamoDB shape: table `deployments`, partition key `deployment_id`, a GSI on `status` for the by-status query
(equivalent to the Firestore `query_by_status`). Heartbeat ordering uses a DynamoDB conditional write
(`ConditionExpression`) — the DynamoDB analogue of the Firestore CAS.

**Gotchas:** lazy-import boto3 (QG bans top-level `boto3`/`try/except ImportError` — follow the existing
`_aws_sdk_protocols.py` pattern). Do NOT activate DynamoDB in prod this phase — GCP stays on Firestore; wire + test +
provision only. No `os.getenv`; UTC datetimes; QG-green.

## Todos

- [ ] [INFRA] P2. Implement `DynamoDbDeploymentRegistryStore` (same `DeploymentRegistryStore` Protocol) over table
      `deployments` (PK `deployment_id`, GSI on `status`), reusing the lazy boto3 pattern in
      `cloud_interface/providers/_aws_sdk_protocols.py`. `heartbeat` uses a conditional write for ordering (DynamoDB
      analogue of the Firestore CAS); `query_by_status` uses the GSI.
- [ ] [BACKEND] P2. Cloud-select the backend from the active cloud (mirror `resolve_bucket_name`): GCP → Firestore, AWS
      → DynamoDB, behind the store factory so no caller changes. Default stays Firestore (GCP) — DynamoDB is inert until
      the AWS cutover.
- [ ] [REVIEW] P2. Contract-test the DynamoDB store against the SAME suite the Firestore store passes (run against
      DynamoDB Local or `moto`): round-trip register/heartbeat/complete, conditional-write ordering rejects a stale
      heartbeat, and the `status` GSI query returns only matching docs. `bash scripts/quality-gates.sh` green.
- [x] ✅ [DATA] P2. Provision (do not activate) — add the DynamoDB `deployments` table + GSI via terraform in
      deployment-service (on-demand capacity, or the 25-WCU/25-RCU free-tier provisioned mode), left inactive. Document
      the one-line activation step (flip the cloud selector) in the AWS-migration runbook. — deployment-service@4d39f44:
      `terraform/aws/deployment_registry_dynamodb.tf` (table `unified-trading-{env}-deployments`, PK `deployment_id`,
      GSI `status-index`, `deployment_registry_dynamodb_billing_mode` var PAY_PER_REQUEST/PROVISIONED); activation step
      documented in `codex/05-infrastructure/deployment-observability.md` § "AWS backend activation (deployment-registry
      DynamoDB)".
- [ ] [INFRA] P2. Ship (commit + push, cite shas) and flip this plan's items (`docs(plans):`). THEN hand off — activate
      the final phase ONLY IF Phase 3 is already `complete`: set `deployment_registry_firestore_p5_verify_2026_07_14.md`
      frontmatter `status: draft`→`active` and commit. If Phase 3 is not yet done, leave P5 `draft` — Phase 3's last
      todo activates it (whichever of P3/P4 finishes last flips P5).

## Success criteria

- A DynamoDB store passes the identical `DeploymentRegistryStore` contract suite as Firestore.
- Cloud selection is automatic (GCP → Firestore, AWS → DynamoDB); no caller changes; DynamoDB inert on GCP.
- Table + GSI provisioned via terraform, inactive; activation step documented.
- boto3 lazy-imported (no top-level import, no `try/except ImportError`); no `os.getenv`; UTC datetimes; QG green.

## Codex SSOTs

- `codex/05-infrastructure/deployment-observability.md` — registry SSOT (the backend-swap note added Phase 5).
