---
doc_type: plan
title: Deployment registry Firestore migration — Phase 4 — DynamoDB backend for AWS-readiness
summary:
  Add a DynamoDB backend implementing the same DeploymentRegistryStore contract as the Firestore backend, selected by
  the active cloud (GCP to Firestore, AWS to DynamoDB) the same way resolve_bucket_name selects GCS vs S3 — so the
  eventual AWS migration is a backend swap, not a rewrite. Wire and contract-test it now against DynamoDB Local;
  provision the table via terraform but leave it inactive until the AWS cutover flips the cloud selector.
status: complete # (was: active) 2026-07-15 plan-reconcile §7-residual: operator ruling A (archival + codex-sync); verified 0 open todos, evidence spot-checked
nature: process
asset_group: [meta]
stage: [meta]
repos: [unified-trading-library, deployment-service]
scope: [engineer]
tags: [dynamodb, deployment-registry, aws, cloud-interface, migration]
related:
  - /plans/active/deployment_registry_firestore_migration_2026_07_14.md
  - /plans/archive/2026_07/deployment_registry_firestore_p1_dualwrite_2026_07_14.md
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

- [x] ✅ [INFRA] P2. Implement `DynamoDbDeploymentRegistryStore` (same `DeploymentRegistryStore` Protocol) over table
      `deployments` (PK `deployment_id`, GSI on `status`), reusing the lazy boto3 pattern in
      `cloud_interface/providers/_aws_sdk_protocols.py`. `heartbeat` uses a conditional write for ordering (DynamoDB
      analogue of the Firestore CAS); `query_by_status` uses the GSI. — unified-trading-library@c3baaa29:
      `unified_trading_library/cloud_interface/dynamodb_deployment_registry_store.py` (`DynamoDbDeploymentRegistryStore`
      over the env-scoped physical table `unified-trading-{env}-deployments`, GSI `status-index`; boto3 lazy-imported
      inside `_default_boto3_module()` behind a Protocol slice, never at module top; `heartbeat()` uses a native
      `ConditionExpression` —
      `attribute_not_exists(deployment_id) OR (NOT (status IN terminal) AND last_heartbeat_at <=     :new_hb)` — the
      DynamoDB-atomic analogue of the Firestore transaction CAS; float↔Decimal boxing so a DynamoDB item round-trips to
      a field-identical `DeploymentRegistryEntry`, reusing Phase 1's `_entry_to_doc`/`_doc_to_entry`).
- [x] ✅ [BACKEND] P2. Cloud-select the backend from the active cloud (mirror `resolve_bucket_name`): GCP → Firestore,
      AWS → DynamoDB, behind the store factory so no caller changes. Default stays Firestore (GCP) — DynamoDB is inert
      until the AWS cutover. — unified-trading-library@c3baaa29: `build_deployment_registry_store()` appended to
      `cloud_interface/deployment_registry_store.py` (selects on `UnifiedCloudConfig.is_aws`);
      `deployment_registry.py`'s `_maybe_build_firestore_store()` renamed to `_maybe_build_registry_store()` and routed
      through the factory — GCP behaviour unchanged (still Firestore); exported from `cloud_interface/__init__.py`.
- [x] ✅ [REVIEW] P2. Contract-test the DynamoDB store against the SAME suite the Firestore store passes (run against
      DynamoDB Local or `moto`): round-trip register/heartbeat/complete, conditional-write ordering rejects a stale
      heartbeat, and the `status` GSI query returns only matching docs. `bash scripts/quality-gates.sh` green. —
      unified-trading-library@c3baaa29: `tests/cloud_interface/unit/test_dynamodb_deployment_registry_store.py` — 14
      tests against a FAKE boto3 module (dict-backed Table; no moto — moto is not installed, per plan note) covering
      round-trip (incl. a dedicated float↔Decimal boxing test), heartbeat CAS ordering rejection, terminal-resurrection
      rejection, first-write-never-stale, `complete()`'s terminal-status guard, GSI `query_by_status`/`list_active`
      (incl. malformed-item skip), and the cloud-select factory (GCP→Firestore / AWS→DynamoDB).
      `bash     scripts/quality-gates.sh --no-fix` GREEN (basedpyright 0 errors; full UTL suite 6117 passed, 8 skipped,
      1 xfailed).
- [x] ✅ [DATA] P2. Provision (do not activate) — add the DynamoDB `deployments` table + GSI via terraform in
      deployment-service (on-demand capacity, or the 25-WCU/25-RCU free-tier provisioned mode), left inactive. Document
      the one-line activation step (flip the cloud selector) in the AWS-migration runbook. — deployment-service@4d39f44:
      `terraform/aws/deployment_registry_dynamodb.tf` (table `unified-trading-{env}-deployments`, PK `deployment_id`,
      GSI `status-index`, `deployment_registry_dynamodb_billing_mode` var PAY_PER_REQUEST/PROVISIONED); activation step
      documented in `/codex/05-infrastructure/deployment-observability.md` § "AWS backend activation
      (deployment-registry DynamoDB)".
- [x] ✅ [INFRA] P2. Ship (commit + push, cite shas) and flip this plan's items (`docs(plans):`). THEN hand off —
      activate the final phase ONLY IF Phase 3 is already `complete`: set
      `deployment_registry_firestore_p5_verify_2026_07_14.md` frontmatter `status: draft`→`active` and commit. If Phase
      3 is not yet done, leave P5 `draft` — Phase 3's last todo activates it (whichever of P3/P4 finishes last flips
      P5). — Shipped unified-trading-library@c3baaa29 (pushed to `live-defi-rollout`). **P5 activation deferred** —
      checked `deployment_registry_firestore_p3_cutover_2026_07_14.md`: `status: draft`, none of its todos are checked
      (a parallel agent is still on Phase 2→3). Left `deployment_registry_firestore_p5_verify_2026_07_14.md` at
      `status: draft` per the deferral rule — whichever of P3/P4 finishes last activates P5.

## Success criteria

- A DynamoDB store passes the identical `DeploymentRegistryStore` contract suite as Firestore.
- Cloud selection is automatic (GCP → Firestore, AWS → DynamoDB); no caller changes; DynamoDB inert on GCP.
- Table + GSI provisioned via terraform, inactive; activation step documented.
- boto3 lazy-imported (no top-level import, no `try/except ImportError`); no `os.getenv`; UTC datetimes; QG green.

## Progress Log

- **2026-07-14 (sub-agent, Sonnet — local execution)** — Shipped P4 (utl@c3baaa29, one commit covering all four
  remaining todos). UTL `quality-gates.sh --no-fix` GREEN (basedpyright 0 errors; full suite 6117 passed / 8 skipped / 1
  xfailed, ~114s).
  - **What shipped**: `DynamoDbDeploymentRegistryStore` in a new
    `unified_trading_library/cloud_interface/dynamodb_deployment_registry_store.py`, satisfying the exact same
    `DeploymentRegistryStore` Protocol as the Phase 1 Firestore store (imported from `deployment_registry_store.py`, not
    redefined) — table `unified-trading-{env}-deployments` (env-scoped physical name, resolved lazily via
    `get_environment()`; caught during review that a bare `"deployments"` default would 404 against the real
    terraform-provisioned table), PK `deployment_id`, GSI `status-index`. `heartbeat()` uses a native
    `ConditionExpression`
    (`attribute_not_exists(deployment_id) OR (NOT (status IN terminal) AND last_heartbeat_at <= :new_hb)`) evaluated
    atomically by DynamoDB itself — no read-modify-write transaction needed, the true DynamoDB analogue of the Firestore
    transaction CAS; a rejected write is detected structurally
    (`exc.response["Error"]["Code"] == "ConditionalCheckFailedException"`, no botocore import needed) and treated as a
    no-op. Handles the float→Decimal boxing gotcha (boto3's DynamoDB resource layer raises `TypeError` on a raw Python
    `float`; always returns `Decimal` on read) so a DynamoDB item round-trips to a field-identical
    `DeploymentRegistryEntry`, reusing Phase 1's `_entry_to_doc`/`_doc_to_entry` (same JSON-shaped serialize/parse, not
    a parallel implementation).
  - **Cloud-select factory**: `build_deployment_registry_store()` appended to `deployment_registry_store.py` —
    `UnifiedCloudConfig.is_aws` picks DynamoDB, else Firestore (mirrors `resolve_bucket_name`'s GCS/S3 selection).
    `deployment_registry.py`'s `_maybe_build_firestore_store()` renamed to `_maybe_build_registry_store()` and routed
    through the factory — GCP behaviour is UNCHANGED (still Firestore); DynamoDB stays inert on every GCP deployment
    today and activates automatically post-AWS-cutover with no caller change. Both exported from
    `cloud_interface/__init__.py`.
  - **Tests**: 14 new unit tests against a FAKE boto3 module (dict-backed `Table`; no moto — moto is not installed, per
    the plan's own note) — round-trip (incl. a dedicated float↔Decimal test asserting the fake's backing item is really
    `Decimal`-boxed, then unboxes back to `float` on read), heartbeat CAS ordering rejection, terminal- resurrection
    rejection, first-write-is-never-stale, `complete()`'s terminal-status guard, GSI `query_by_status`/`list_active`
    (incl. malformed-item skip), and the cloud-select factory picking the right class per cloud. All existing
    Firestore + `DeploymentsRegistry` tests re-verified green (no regression from the rename).
  - **Terraform** (deployment-service@4d39f44) verified ALREADY PRESENT —
    `terraform/aws/deployment_registry_dynamodb.tf` matches this phase's contract exactly (table
    `unified-trading-{env}-deployments`, PK `deployment_id`, GSI `status-index`); not re-done.
  - **P5 handoff — deferred, not activated**: checked `deployment_registry_firestore_p3_cutover_2026_07_14.md` before
    touching P5 — it is `status: draft` with none of its todos checked (Phase 2→3 still in flight on a parallel Opus
    thread). Left `deployment_registry_firestore_p5_verify_2026_07_14.md` at `status: draft` per the deferral rule —
    whichever of P3/P4 finishes last flips P5 to `active`.

## Codex SSOTs

- `/codex/05-infrastructure/deployment-observability.md` — registry SSOT (the backend-swap note added Phase 5).
