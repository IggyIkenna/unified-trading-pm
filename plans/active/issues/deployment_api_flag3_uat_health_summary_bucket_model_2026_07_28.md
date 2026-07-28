---
doc_type: issue
title: deployment-api FLAG-3 — UAT health-summary bucket model decided (option C); cross-cutting pipeline-health bucket tracked as deferred future fix
summary: >-
  Operator-decided (2026-07-28) resolution of the deployment-api FLAG-3 model decision
  (data_completion_cefi_2026_07_15.md:154): commentary/pipeline_uat.py's instruments/features
  health-summary reads have no non-AG aggregate bucket kind to point at (verified live against
  cloud-providers.yaml) and are left functionally as-is (UAT/commentary-only, already degrades to
  None, zero regression risk) with honest known-gap comments replacing the misleading
  # CORRECT-LOCAL / # QG-allow markers' implied meaning. The CORRECT long-term fix — a dedicated
  cross-cutting env-tiered pipeline-health bucket written by instruments-service + features-service
  — is tracked here as deferred, out-of-scope-for-deployment-api-alone, NOT abandoned.
status: open
nature: process
asset_group: [cefi]
stage: [data]
repos: [deployment-api, deployment-service, instruments-service, features-service]
scope: [engineer, admin]
tags: [bucket-naming, deployment-api, uat-commentary, data-completion, cefi]
related: [/plans/active/data_completion_cefi_2026_07_15.md, /plans/active/data_completion_prediction_2026_07_15.md, /plans/active/cefi_consolidated_closeout_aggregated_sources_2026_07_24.md]
created: 2026-07-28
parent_epic: manifest_master
priority: P3
assigned_vm: NA
resolved_by:
locked_by:
source: [data_completion_cefi_2026_07_15.md FLAG-3 todo, BLK-9817ba72 operator answer 2026-07-28]
execution_scope: local-only
drift_direction: advance-code
depends_on: []
---

# deployment-api FLAG-3 — UAT health-summary bucket model

## What I found

`data_completion_cefi_2026_07_15.md:154` carried an open FLAG-3 todo re-scoped by a 2026-06-05
slot-3 evaluation as "NOT a mechanical f-string→`resolve_bucket_name` swap — a model decision."
`commentary/pipeline_uat.py` reads 4 non-AG "pipeline-health summary" paths
(`instruments-store-{pid}/instruments/latest/manifest.json`,
`features-store-{pid}/health/latest.json`, plus ml-training-metrics and execution-recon paths) to
feed an LLM-generated UAT commentary. Live registry check
(`deployment-service/configs/cloud-providers.yaml`) confirms:

- `instruments-store` is registered ONLY per-AG (`CEFI`/`DEFI`/`TRADFI`/`SPORTS`, env-tiered) plus
  a separate flat `instruments-store-prediction` key — no non-AG aggregate kind exists.
- `features-store` does not exist as a kind AT ALL — only family-specific kinds
  (`features-delta-one`/`volatility`/`onchain`/`xinstrument`/`mtf`/`sports`/`commodity`/
  `calendar`/`prediction`).
- The ml-store and execution-store reads in the SAME file were ALREADY migrated (they use
  `config.effective_ml_training_artifacts_bucket` / `config.effective_execution_store_bucket`,
  both folded env-tiered flat buckets registered in the yaml) — only the instruments/features
  reads remained unresolved.

A sibling plan (`data_completion_prediction_2026_07_15.md:326`) cites an "operator DECIDED
2026-06-02: env-tier the `*-store` buckets" note as though it resolves this, but that note predates
the 2026-07-17 bucket-fold work (`bucket_fold_ml_2026_07_17.md`,
`bucket_fold_execution_strategy_2026_07_17.md`) that already reshaped ml-store/execution-store into
flat folded env-tiered buckets and instruments-store into a per-AG dict — neither shape matches a
generic non-AG health-summary bucket the June note implied, so applying it literally today would
conflict with the current registry. `cefi_consolidated_closeout_aggregated_sources_2026_07_24.md`
(more recent, 2026-07-24) correctly still frames this as an undecided model question.

## Why it matters

The two hardcoded f-string reads (`f"instruments-store-{project_id}"`,
`f"features-store-{project_id}"`) carried QG-exemption markers (`# QG-allow:
legacy-bucket-name-migration`, `# CORRECT-LOCAL`) whose plain meaning is misleading: neither read is
"correct" (no such bucket exists) nor is one "actively migrating" (there is nothing to migrate to
yet). Left as-is with those labels, a future reader would wrongly conclude either that the code is
fine or that a migration is already underway, when the honest state is "known gap, deliberately
deferred."

## Recommended decision (operator-decided 2026-07-28, BLK-9817ba72)

**Option C selected**: leave the reads functionally as-is — this is a UAT/commentary-only LLM-summary
path, not a production/manifest/gate/trading path; it `try/except`-degrades to `None` and has NEVER
resolved a real bucket, so regression risk is zero either way, and the data-pipeline-correctness HARD
RULE does not force a full fix here.

- **Rejected — Option A** (per-AG loop + aggregate for instruments; pick one feature family to stand
  in for "overall feature health"): the features half is semantically arbitrary — it would fabricate
  a health number, not report an honest one.
- **Rejected for this todo — Option B** (new cross-cutting env-tiered `pipeline-health` bucket kind,
  written by instruments-service AND features-service, read by deployment-api): this **IS the correct
  long-term model** — but it needs coordinated writer-side changes in two other repos, which is a
  service-dependency this one deployment-api AO todo must not absorb unplanned.

**Amendment (applied in this fix)**: replaced the misleading marker-adjacent comments with an honest
"KNOWN GAP, not a migration" annotation in `deployment_api/commentary/pipeline_uat.py`, while keeping
the exact QG-allow/CORRECT-LOCAL token text needed to keep `quality-gates.sh` green (STEP 5.31 /
5.96 bucket-literal-ban checks) — the token is a gate-exemption marker, not an accuracy claim.

## Follow-up (tracked, not abandoned)

- [ ] [DESIGN] P3. Design + scope a dedicated cross-cutting env-tiered `pipeline-health` bucket kind
      (register in `deployment-service/configs/cloud-providers.yaml`) that `instruments-service` and
      `features-service` each write a small daily summary blob to (`health/latest.json` per service);
      `deployment-api`'s `pipeline_uat.py` reads from there instead of the non-existent
      `instruments-store-{pid}` / `features-store-{pid}` paths. Cross-repo (instruments-service,
      features-service, deployment-service, deployment-api) — needs its own scoped plan, not a single
      AO todo. (repo: deployment-service, instruments-service, features-service, deployment-api)
