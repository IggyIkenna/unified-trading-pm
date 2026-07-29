---
doc_type: plan
title: Artifact Registry / ECR cleanup — side-tracks (other repos, AWS ECR, legacy GCR bucket, GCS tarball bucket)
summary:
  Satellite plan split out of docker_artifact_registry_cleanup_policy_2026_07_24.md on 2026-07-27 so this work can run
  IN PARALLEL with that plan's Phase B-D `unified-trading-system` spine instead of being serialized behind it by the
  parent's sequential flag. Extends the same deployed-digest-keep + keep-5-floor + delete-older-than-3d pattern to
  `unified-trading-library` and the remaining ~73 GCP Artifact Registry repos, designs the equivalent AWS ECR lifecycle
  policy for 20 ECR repos, deletes the legacy (GCR-era) GCS bucket, documents the pattern in codex, and adds a GCS
  lifecycle rule for the separate code-tarball bucket (a different artifact class, GCS not AR). Local-only — AR/ECR
  image-version deletes stay human-gated (no undelete mechanism exists for AR image versions — untouched by the
  2026-07-28 §3a extension); the legacy GCR bucket delete is a whole-bucket destroy that IS now reversibility-qualified
  (2026-07-28 ruling, /codex/02-data/gcs-and-manifest-delete-safety-protocol.md §3a extended) provided a fresh same-run
  soft-delete-retention check clears.
status: active
nature: process
asset_group: [infrastructure]
stage: [meta]
repos:
  [
    unified-trading-pm,
    unified-trading-library,
    deployment-service,
    market-tick-data-service,
    instruments-service,
    strategy-service,
    execution-service,
    ml-service,
    features-service,
    market-data-processing-service,
  ]
scope: [engineer]
tags: [artifact-registry, ecr, docker-images, storage-cost, cleanup-policy, retention, cicd, gcs-lifecycle]
related: [/plans/active/docker_artifact_registry_cleanup_policy_2026_07_24.md]
created: 2026-07-27
last_updated: 2026-07-28
parent_epic: infrastructure_master
assigned_vm: harsh_pc
execution_scope: orchestrator-agent
sequential: true
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 1.8
estimate_calibrated_ai_days: 1.4
assigned_role: infra
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source:
  Split from docker_artifact_registry_cleanup_policy_2026_07_24.md on 2026-07-27 — that plan's Phase E/F todos were
  genuinely independent of its Phase B-D `unified-trading-system` spine (different repos/cloud/bucket) but were being
  serialized behind it by the parent plan's sequential flag, blocking the operator's request to run this work in
  parallel with the main spine once Phase A's audit was done. See the parent plan's Progress log for the split
  rationale.
---

# Artifact Registry / ECR cleanup — side-tracks

> **Split plan, not standalone** — the diagnosis, policy shape, and safety rules all live in the parent,
> [docker_artifact_registry_cleanup_policy_2026_07_24.md](/plans/active/docker_artifact_registry_cleanup_policy_2026_07_24.md)
> (§ Diagnosis, § Why audit-first, § Policy shape, § Operator decisions — all still apply here, this doc does not repeat
> them). **`sequential: true`** — todos 15-17 are a real chain (16 needs 15's referenced-tarball-set output; 17 needs
> 16's drafted rule); todos 10-13 don't depend on each other or on 15-17, but are kept in the same top-to-bottom order
> for the same reason the parent plan added the flag — avoid AO reaching a gated delete/apply todo (17) before its real
> prerequisites exist; todo 13 was `[OPERATOR]`-gated at the time of this split but was downgraded to AO-dispatchable
> 2026-07-28, see its own text below. **Todo numbers (10-13, 15-17) are preserved from the pre-split single plan** for
> cross-doc traceability — not renumbered, and not contiguous with each other (14 stayed in the parent plan as the
> codex-stub todo). No AR soft-delete/undelete exists — deletion of an AR image version is permanent and stays
> human-gated (untouched by the 2026-07-28 §3a extension, which covers only stores WITH an undelete mechanism). The
> legacy GCR bucket delete (todo 13) is a whole-bucket destroy — **operator ruling 2026-07-28** (codex
> `gcs-and-manifest-delete-safety-protocol.md` §3a extended) made this class reversibility-qualified too, the same way
> object deletes already were, provided a fresh same-run `gcs_bucket_soft_delete_retention_seconds()` check on the
> target bucket clears (>=604800s) — see todo 13 for the dispatch shape.

## Plan

### Phase E — Extend to the rest of the estate

- [x] ✅ 10. [INFRA] P3. Repeat Phases A-D (of the parent plan) for `unified-trading-library` (928 GB) — profile it
      sub-path-by-sub-path first, then apply the same deployed-digest-keep + floor + 3-day pattern. —
      unified-trading-pm@75e21803 (policy + dry-run report). **Phases A-C complete 2026-07-29.** Phase A: 4 packages
      (e2e-audit=4, paper-signal-engine=9, paper-trading-engine=12, unified-trading-library=1,241), 1,266 images, ~1,024
      GB. All 6 live Cloud Run Jobs use `:latest` tags → inherently protected by keep-5-recent (confirmed: each
      `:latest` digest is at position #1 in its package). Zero non-`:latest` pinned consumers → no explicit
      keep-deployed-digests entries needed. `vm-serial-capture-prd` references `deployment-service:latest` under this
      repo — that package doesn't exist (broken job, not blocking). Phase B: 2-rule policy committed (keep-5-recent +
      delete-older-than-3d/259200s). Phase C: dry-run applied live + verified via `describe`
      (`cleanupPolicyDryRun: true`); replicated logic against 1,266 live images → 19 kept, 1,247 flagged;
      zero-intersection PASSES (all :latest digests at position #1, inherently within keep-5). Phase D (flip
      non-dry-run) is operator-gated — same as parent plan's todo 8, AR has no soft-delete. Policy file:
      `docker_artifact_registry_cleanup_policy_unified_trading_library.json`; dry-run report:
      `docker_artifact_registry_cleanup_policy_dryrun_report_unified_trading_library_2026_07_29.json`.
- [x] ✅ 11. [DATA] P3. Profile the remaining ~73 GCP Artifact Registry repos (see
      `docker_artifact_storage_audit_2026_07_24.csv`) and apply the same pattern to any showing the
      unbounded-CI-retention shape. — unified-trading-pm@d836194 (classification + 5 policy files + 18 repos policied).
      **Complete 2026-07-29.** Classification report: `docker_artifact_registry_repo_classification_2026_07_29.json`.
      **Policies applied (dry-run) to 18 repos:** (a) 4 priority repos with live consumers — `deployment-dashboard` (720
      imgs, 112 GB, SHA-pinned service needs keep-deployed-digests), `market-data-tick-handler` (6 imgs, 6 live
      `:latest` jobs), `quota-broker` (3 imgs, SHA-pinned service), `market-data-handler` (0 imgs per CSV, `:v2` job);
      (b) 14 remaining service repos — standard 2-rule policy applied. **Out-of-scope:** GCP-managed repos
      (cloud-run-source-deploy×5, gcf-artifacts×3, firebaseapphosting-images×2, container-registry, gae-standard,
      gcr.io×3 — cannot apply custom policies); `unified-libraries` (PYTHON format, not Docker); 20 zero-artifact repos
      (policy unnecessary but available). AWS ECR (18 repos) → todo 12. Legacy GCR bucket → todo 13. Policy files
      committed: `deployment_dashboard.json` (3-rule), `quota_broker.json` (3-rule), `market_data_handler.json`
      (3-rule), `standard_2rule.json` (reusable template).
- [ ] 12. [INFRA] P3. Design the AWS ECR lifecycle policy for the 20 ECR repos — ECR syntax differs (JSON rule-priority
      list, `countType`/`tagStatus`), and its dry-run analog is `aws ecr start-lifecycle-policy-preview` /
      `get-lifecycle-policy-preview`; apply the same deployed-digest-keep principle. Done-when: a previewed ECR policy
      is presented to the operator for the same sign-off gate as the parent plan's Phase C.
- [ ] 13. [INFRA] P3. Delete the legacy GCR bucket `gs://artifacts.central-element-323112.appspot.com` (8.9 GiB, GCR is
      shut down). **Downgraded from [OPERATOR] 2026-07-28** — operator ruling 2026-07-28
      (`/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §3a, extended): whole-bucket destroys are now
      reversibility-qualified the same way object/version deletes already were, PROVIDED a fresh same-run
      `gcs_bucket_soft_delete_retention_seconds(bucket)` check on THIS bucket clears (>=604800s) immediately before the
      delete. A 2026-07-27 check found `soft_delete_policy.retentionDurationSeconds=604800` on this bucket — that
      confirms the mechanism exists but is NOT itself the fresh check; re-run the check in the SAME session as the
      delete and cite the actual returned value. If it clears, execute the bucket delete via the sanctioned UTL storage
      helpers (`get_storage_client()` — never subprocess `gcloud`/`gsutil`) with no operator step. If the fresh check
      errors or returns <604800s, it stays gated — fall back to §3a's approve-executes flow (stage the exact delete
      command, open a structured BLOCKED question recommending "approve — execute now"; a FINAL operator answer
      authorizes the SAME worker session to run it immediately) rather than assuming clearance. **Also confirmed live
      2026-07-27 (parent plan's Phase A audit)**: one Cloud Run Job (`live-event-log-compactor`) references a
      `gcr.io/central-element-323112/...` image, but that image has never existed since the Job's creation
      (`ContainerMissing`, confirmed via `gcloud run jobs describe`) — so this does NOT block the delete, there is
      nothing real in that path to lose; note it for the Job's owner separately, it's been silently broken for a month
      regardless of this bucket. Done-when: the bucket is gone and the re-audit no longer lists it, with the fresh
      retention-check value cited in this plan (or the approve-executes fallback was used, cited here).

### Phase F — Code-tarball bucket retention (GCS lifecycle, human-gated)

- [ ] 15. [DATA] P3. Determine which `@sha` tarballs in `gs://deployment-scripts-central-element-323112/code/` are still
      referenced — by a live VM (`gcloud compute instances list`), a launcher default, or a `deployments/active/*.json`
      registry entry — so the lifecycle rule never deletes a referenced copy. Done-when: the referenced-`@sha` set (or
      "only current-pointers referenced") is listed.
- [ ] 16. [INFRA] P3. Draft a GCS lifecycle rule on the `code/` prefix that ages out old `@sha` tarballs + manifests
      (e.g. `age > 30d` AND not the current-pointer AND not in the Phase-15 referenced set); the per-repo
      `<repo>-code.tar.gz` current-pointer is always kept. Done-when: the lifecycle JSON is committed and a dry
      enumeration shows only stale `@sha` objects in scope.
- [ ] 17. [INFRA] P3. Apply the tarball lifecycle rule live on `gs://deployment-scripts-central-element-323112`.
      Done-when: `gcloud storage buckets describe` shows the rule and the `code/` prefix size stops growing. Downgraded
      from [OPERATOR] 2026-07-27 (reversibility-verified, finding T,
      /codex/02-data/gcs-and-manifest-delete-safety-protocol.md §3a): this is an object/prefix-scoped GCS lifecycle
      delete against a NAMED bucket with a defined predicate (age > 30d AND not current-pointer AND not in the Phase-15
      referenced set), not a whole-bucket destroy — distinct from todo 13's bucket destroy (a different reversibility
      sub-case, downgraded from [OPERATOR] separately on 2026-07-28 — see its own text). The bucket's soft-delete
      retention was 0 (unset) as of a fresh check this session; enabled live via
      `gcloud storage buckets update gs://deployment-scripts-central-element-323112 --soft-delete-duration=7d` and
      re-confirmed at 604800s retention — any object the lifecycle rule deletes is recoverable within that window, same
      as an object delete/overwrite.

## Codex SSOTs

- [/codex/05-infrastructure/vm-tarball-deployment.md](/codex/05-infrastructure/vm-tarball-deployment.md) — tarball vs
  Docker-image runtime split.
- [/codex/02-data/gcs-and-manifest-delete-safety-protocol.md](/codex/02-data/gcs-and-manifest-delete-safety-protocol.md)
  — human-gated-delete discipline the GCR bucket delete (todo 13) and tarball lifecycle rule (todo 17) follow.
- The parent plan's todo 14 creates `/codex/05-infrastructure/artifact-registry-cleanup-policy.md` — this plan's todos
  10-12 should follow that pattern once it exists rather than re-deriving it.

## Supporting artifacts

Same source as the parent plan — see its § Supporting artifacts for the audit CSV/HTML paths and regeneration command.

## Progress log

- **2026-07-27 (operator)**: created by splitting Phase E (todos 10-13) and Phase F (todos 15-17) out of
  `docker_artifact_registry_cleanup_policy_2026_07_24.md`, at the operator's request, once that plan's Phase A audit was
  done locally — see that plan's Progress log for the full split rationale. No work done in this plan yet; all todos
  carried over unchanged (still `[ ]`) from the parent plan.
- **2026-07-28 (gate-cleanup pass)**: retagged todo 13 from `[OPERATOR]` to `[INFRA]` per the operator's 2026-07-28
  ruling extending the §3a reversibility carve-out to whole-bucket destroys
  (`/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §3a, extended) — the todo now dispatches as a normal AO
  todo requiring a fresh same-run soft-delete-retention check before executing the delete, falling back to the
  approve-executes flow if that check doesn't clear. No delete executed as part of this pass (retag/dispatch-shape
  only).
