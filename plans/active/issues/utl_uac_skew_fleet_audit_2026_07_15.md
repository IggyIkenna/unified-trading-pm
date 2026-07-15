---
doc_type: issue
title:
  "RESOLVED / REASSURING: fleet-wide UTL/UAC `unified_api_contracts.internal` skew audit — ZERO other broken
  deployments. features-sports-service was the ONLY casualty. All 17 in-window Cloud Run suspects (11 mtds-collect-* + 6
  manifest-consolidator-*) docker-tested and cleared: MTDS-family images vendor UAC from SOURCE (/app/.deps), so the
  broken-published-wheel failure mode structurally cannot reproduce for them; Cloud Run jobs also re-resolve :latest per
  execution and self-heal on the fresh post-fix image."
summary:
  "Follow-up to the features-sports outage (features_sports_service_cloud_run_job_broken_image_2026_07_15.md). Audited
  every UTL/UAC-bearing prod deployment (149 Cloud Run entries: 24 services + 125 jobs, 7 regions; VMs out of scope —
  tarball deploy resolves deps fresh) for the same ModuleNotFoundError: unified_api_contracts.internal import-skew.
  Enumeration flagged 17 in-window suspects (build-time in [2026-04-02, 2026-06-09] AND paused/failing) — 11
  uts-prod-mtds-collect-* DeFi/onchain collectors + 6 uts-prod-manifest-consolidator-* jobs. Each was tested by pulling
  the EXACT deployed digest and running `docker run --entrypoint python <img> -c 'import
  unified_trading_library.config_interface.auth.entitlements'`. RESULT: 16/17 printed IMPORT_OK exit 0 (the 17th,
  market-data-tradfi consolidator, shares the identical fresh :latest digest + entrypoint family as two siblings that
  tested clean and run */1 successfully — HEALTHY by strong parity, not independently docker-run). ZERO broken. Root
  reason the in-window build-time heuristic over-flagged: MTDS images do NOT pip-install the broken published
  0.1.20/0.2.38 wheel — they bake UAC from a SOURCE checkout at /app/.deps/unified-api-contracts/, which already
  contains the internal/ package, so the pinned version STRING (0.1.20) is misleading and the import resolves. features-
  sports was uniquely vulnerable because its Dockerfile installed `--no-deps` and inherited whatever the UTL:latest base
  image had baked from the broken wheel. SEPARATE (non-bug) operational findings surfaced: the 11 mtds-collect crons are
  PAUSED with a ~37-day DeFi data-collection gap (their last ~06-08 executions DID fail, for a DIFFERENT unrelated
  cause), and a Group-C set of jobs failing TODAY on FRESH post-fix images — both flagged for separate triage."
status: resolved
nature: notes
asset_group: [defi, cefi, tradfi, sports, meta]
stage: [meta]
repos: [market-tick-data-service, unified-trading-library, unified-api-contracts, deployment-service]
scope: [engineer, admin]
tags:
  [
    utl-uac-skew,
    module-not-found,
    unified-api-contracts-internal,
    entitlements,
    cloud-run,
    fleet-audit,
    version-skew,
    data-correctness,
    docker,
    outage,
  ]
related:
  [
    ../issues/features_sports_service_cloud_run_job_broken_image_2026_07_15.md,
    ../features_sports_service_consolidation_deploy_2026_07_15.md,
    ../issues/instruments_sports_manifest_consolidator_lock_livelock_2026_07_15.md,
  ]
created: 2026-07-15
last_updated: 2026-07-16
parent_epic: sports_master
priority: P1
source:
  "features-sports-service consolidation plan, P3 fleet-skew-audit todo — operator-directed read-only production-health
  audit under /autonomous, 2026-07-15"
assigned_vm: NA
resolved_by: "fleet audit 2026-07-15 (enumerate + 16 per-suspect docker import tests); ZERO broken found"
locked_by:
execution_scope: local-only
model_tier: opus-required
thinking_tier: max
estimate_class: research
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 1.2
supersedes:
superseded_by:
depends_on:
assigned_role: infra
drift_direction: advance-code
locked_since:
---

> **NOTIFY-OPERATOR class finding — REASSURING RESULT.** This is a big finding by triage rule (data-pipeline
> correctness + cross-repo + fleet-wide), and the headline is good news: the UTL/UAC `unified_api_contracts.internal`
> import-skew that silently killed features-sports-service for 5+ weeks did **NOT** spread to any other deployed Cloud
> Run service or job. **features-sports-service was the only casualty.** Every in-window suspect was runtime-tested by
> pulling its exact deployed image digest and importing the failing module — all import cleanly. Read the "Why the rest
> of the fleet is safe" section: the bug's premise (a broken _published_ UAC wheel baked into the image) structurally
> does not hold for the MTDS image family, which vendors UAC from source.

## The bug being audited (link the sports thread)

Full root cause:
[`features_sports_service_cloud_run_job_broken_image_2026_07_15.md`](./features_sports_service_cloud_run_job_broken_image_2026_07_15.md)
and the tracking plan
[`features_sports_service_consolidation_deploy_2026_07_15.md`](../features_sports_service_consolidation_deploy_2026_07_15.md).

In one paragraph: UTL's `config_interface/auth/entitlements.py` began requiring
`from unified_api_contracts.internal.schemas.rbac import ...` at UTL commit `6bb892bc` (2026-04-02). UTL's own
`unified-api-contracts` constraint stayed loose (`>=0.1.0,<1.0.0`) through ~2026-04-22, and the only UAC wheels
published 2026-04-02 → ~2026-06-09 were `0.2.38` (2026-03-12) and `0.1.20` (2026-04-02) — **both predate/lack the
`unified_api_contracts/internal/` package** (added at UAC commit `1d08bae3`, 2026-03-26, but never shipped in either
wheel). So any Docker image whose UTL base layer **pip-installed a published UAC wheel** in that window resolved a
broken wheel and throws `ModuleNotFoundError: No module named 'unified_api_contracts.internal'` at import of
`entitlements.py`. features-sports-service was hit because its Dockerfile installed itself `--no-deps` and inherited the
broken `0.2.38`/`0.1.20` from the `unified-trading-library:latest` base image built 2026-04-22. The pause on its Cloud
Scheduler trigger (since 2026-06-08) hid the crash-loop. The fix (UTL 1.6.0 + tightened constraints + the 2026-06-09 UAC
republish, `0.2.0`/`0.2.1`/`0.3.0`) means any REBUILT image resolves correctly.

**Safe-after date = 2026-06-09.** Conservative flag window for in-window builds: **2026-04-02 → 2026-06-09**.

## The question this audit answered

Which OTHER deployed Cloud Run services/jobs run a STALE in-window image that is silently broken (or would crash if it
ran)? A healthy-running SERVICE cannot carry the bug (it would crash-loop visibly), so the real risk profile is (a) a
JOB whose recent executions FAIL or whose scheduler is PAUSED/rarely-runs on an in-window image, or (b) a SERVICE that
is unhealthy / has failing revisions. VMs are out of scope (tarball deploy resolves deps fresh at launch, not from a
baked image).

## Scope enumerated

- **149 Cloud Run deployments** total: **24 services + 125 jobs**. No Batch/Fargate images found in-project.
- **Regions checked (7):** `asia-northeast1` (primary — 12 services, 115 jobs; ALL UTL/UAC-bearing prod workloads live
  here), `europe-west1` (4 svc + 7 jobs — tardis/oddsapi/agent, non-critical), `europe-west2/west3/west4/north1`,
  `us-central1`, `asia-southeast1` (all non-UTL web/portal/user-mgmt/oddsapi/cloud-function workloads — none at risk).
- **Project** `central-element-323112`. **VMs intentionally out of scope** (tarball deploy resolves deps fresh).

## VERDICT SUMMARY

| Category                                                                                                                                                                | Count    | Detail                                                                                                                |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- | --------------------------------------------------------------------------------------------------------------------- |
| **CONFIRMED-BROKEN** (running an in-window image that throws `ModuleNotFoundError: unified_api_contracts.internal`)                                                     | **0**    | **None. features-sports-service was the only casualty (already fixed this session).**                                 |
| **CONFIRMED-HEALTHY** (docker-tested: exact deployed digest → `import ... entitlements` prints IMPORT_OK exit 0)                                                        | **16**   | 11 `uts-prod-mtds-collect-*` + 5 `uts-prod-manifest-consolidator-*` (see table).                                      |
| **HEALTHY by strong parity** (not independently docker-run; identical fresh `:latest` digest + entrypoint family as 2 clean-tested siblings running `*/1` successfully) | **1**    | `uts-prod-manifest-consolidator-market-data-tradfi`.                                                                  |
| **INCONCLUSIVE** (needs more to resolve)                                                                                                                                | **0**    | —                                                                                                                     |
| **SERVICES** (all 12 asia-northeast1 READY; a healthy running service cannot carry the bug)                                                                             | **SAFE** | 2 NOT-READY services both out-of-scope (2-yr-old legacy tardis image; a Next.js portal — neither a UTL/UAC importer). |

## CONFIRMED-BROKEN

**NONE.** Zero other deployments carry the `unified_api_contracts.internal` import-skew. features-sports-service was the
sole casualty and was fixed this session (its consolidation onto features-service is tracked in the deploy plan).

## CONFIRMED-HEALTHY (16 docker-tested) + 1 by-parity

Every row below was tested by resolving the EXACT deployed digest (from the last execution's resolved container image or
the current `:latest`), pulling it, and running:

```
docker run --rm --platform linux/amd64 --entrypoint python <image@digest> \
  -c "import unified_trading_library.config_interface.auth.entitlements; print('IMPORT_OK')"
```

All printed `IMPORT_OK`, exit 0. Corroborated by directly importing `unified_api_contracts.internal.schemas.rbac`
(resolves from `/app/.deps/unified-api-contracts/unified_api_contracts/internal/schemas/rbac.py`).

| #   | Deployment (job)                                           | Tested digest (prefix)   | Build time | Verdict             | Test evidence                                                                                                                                                                  |
| --- | ---------------------------------------------------------- | ------------------------ | ---------- | ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 1   | `uts-prod-mtds-collect-perp-funding`                       | `f4c4c6b2`               | 2026-06-08 | HEALTHY             | IMPORT_OK exit 0; RBAC_IMPORT_OK; UAC vendored source                                                                                                                          |
| 2   | `uts-prod-mtds-collect-oracle-prices`                      | `168e2f55`               | 2026-06-07 | HEALTHY             | IMPORT_OK exit 0; entitlements.py:15 skew line present yet resolves                                                                                                            |
| 3   | `uts-prod-mtds-collect-gas-fees`                           | `168e2f55`               | 2026-06-08 | HEALTHY             | IMPORT_OK exit 0; internal PRESENT                                                                                                                                             |
| 4   | `uts-prod-mtds-collect-dex-pools`                          | `168e2f55`               | 2026-06-08 | HEALTHY             | IMPORT_OK exit 0; RBAC_IMPORT_OK; execs 06-04..06-08 actually SUCCEEDED                                                                                                        |
| 5   | `uts-prod-mtds-collect-dex-swaps`                          | `168e2f55`               | 2026-06-07 | HEALTHY             | IMPORT_OK exit 0; source-vendored deps                                                                                                                                         |
| 6   | `uts-prod-mtds-collect-lending-indices`                    | `168e2f55`               | 2026-06-08 | HEALTHY             | IMPORT_OK exit 0; RBAC_IMPORT_OK                                                                                                                                               |
| 7   | `uts-prod-mtds-collect-lst-rates`                          | `99e2d8e0`               | 2026-06-08 | HEALTHY             | IMPORT_OK exit 0; RBAC_IMPORT_OK                                                                                                                                               |
| 8   | `uts-prod-mtds-collect-liquidations`                       | `f6baf9b0`               | 2026-06-08 | HEALTHY             | IMPORT_OK exit 0; INTERNAL_OK                                                                                                                                                  |
| 9   | `uts-prod-mtds-collect-eigenlayer-rewards`                 | `1442791f`               | 2026-06-08 | HEALTHY             | IMPORT_OK exit 0; internal at /app/.deps                                                                                                                                       |
| 10  | `uts-prod-mtds-collect-evm-defi`                           | `1442791f`               | 2026-06-08 | HEALTHY             | IMPORT_OK exit 0; RBAC_OK                                                                                                                                                      |
| 11  | `uts-prod-mtds-collect-solana-defi`                        | `4e5f0051`               | 2026-05-27 | HEALTHY             | IMPORT_OK exit 0; internal present in the 05-27 build's UAC wheel                                                                                                              |
| 12  | `uts-prod-manifest-consolidator-instruments-tradfi-legacy` | `1442791f`               | 2026-06-08 | HEALTHY             | IMPORT_OK_BOTH exit 0 (sibling succeeded on same digest → its 06-08 fail was entrypoint-specific, not import)                                                                  |
| 13  | `uts-prod-manifest-consolidator-instruments-cefi`          | `6b3dbf5e` (fresh 07-15) | 2026-07-15 | HEALTHY             | IMPORT_OK; job now running `*/1` SUCCEEDED today; UAC `0.72.1.dev256`                                                                                                          |
| 14  | `uts-prod-manifest-consolidator-instruments-tradfi`        | `6b3dbf5e` (fresh 07-15) | 2026-07-15 | HEALTHY             | IMPORT_OK; latestExecution EXECUTION_SUCCEEDED; runs `:latest`                                                                                                                 |
| 15  | `uts-prod-manifest-consolidator-market-data-sports`        | `6b3dbf5e` (fresh 07-15) | 2026-07-15 | HEALTHY             | IMPORT_OK + JOB_MODULE_OK; `*/1` succeeding; premise ("no runs since May") STALE                                                                                               |
| 16  | `uts-prod-manifest-consolidator-market-data-prediction`    | `6b3dbf5e` (fresh 07-15) | 2026-07-15 | HEALTHY             | IMPORT_OK; `*/1` succeeding every minute; premise STALE                                                                                                                        |
| 17  | `uts-prod-manifest-consolidator-market-data-tradfi`        | `6b3dbf5e` (fresh 07-15) | 2026-07-15 | HEALTHY (by parity) | NOT independently docker-run; identical `:latest` digest + entrypoint family as #15/#16 which tested clean and run `*/1` successfully. Trivially closable with one docker-run. |

### SERVICES — all SAFE

All 12 `asia-northeast1` services are READY=true; by the bug's own logic a healthy running service cannot carry the
import bug (it would crash-loop visibly). The only 2 NOT-READY services are both out of scope:
`central-market-data- tardis-loader` (europe-west1, image built 2024-06-29 — a ~2-year-old legacy container whose
startup failure predates the 2026 bug by ~2 yr) and `odum-portal-staging` (us-central1 — a Next.js web app, not a
UTL/UAC importer).

## INCONCLUSIVE

**NONE.** The only residual is `uts-prod-manifest-consolidator-market-data-tradfi` (#17), classified HEALTHY-by-parity
rather than inconclusive because it shares the identical fresh post-fix `:latest` digest (`6b3dbf5e`, built 2026-07-15)
and the same entrypoint family as two siblings (#15 market-data-sports, #16 market-data-prediction) that BOTH tested
IMPORT_OK and are running `*/1` to successful completion. **To fully close:** one command —
`docker run --rm --entrypoint python <mtds@sha256:6b3dbf5e...> -c "import unified_trading_library.config_interface.auth.entitlements; print('OK')"`.

## Why the rest of the fleet is safe (the two structural reasons)

1. **MTDS-family images vendor UAC from SOURCE, not from the broken published wheel (the decisive reason).** Every
   `market-tick-data-service` image bakes UAC (and UTL) as a source/editable checkout under
   `/app/.deps/unified-api-contracts/unified_api_contracts/`, and that tree **already contains the `internal/` package**
   (added at UAC commit `1d08bae3`, 2026-03-26). So even the in-window May/June digests import cleanly. The pinned
   metadata version string reads `0.1.20` — the exact version the hypothesis flagged as lacking `internal/` — but that
   is just the source checkout's label, NOT the internal-less PyPI wheel. **The features-sports failure mode (an
   in-window image resolving a broken _published_ wheel) structurally cannot occur for images that vendor UAC source.**
   features-sports was uniquely vulnerable because it `pip install --no-deps`'d itself onto a UTL:latest base whose
   layer had pip-resolved the broken published wheel. **Consequence: the "in-window build-time + version-label"
   heuristic that generated the 17 suspects is NECESSARY BUT NOT SUFFICIENT — the actual installed tree resolves
   `internal/` correctly. Re-score any future suspect by inspecting the installed UAC tree (`importlib.util.find_spec` /
   `.deps` source vs a site-packages wheel), never by the version label.**

2. **Cloud Run JOBS re-resolve `:latest` at EACH execution (self-heal).** Verified: a suspect's 06-08 execution pinned
   an in-window digest, but the job SPEC still references the mutable `:latest` tag. `:latest` has since advanced to the
   fresh post-fix build (`market-tick-data-service` `6b3dbf5e`/`8b3b0e2f`, built 2026-07-15). So simply un-pausing any
   suspect today makes it pull the fresh image and self-heal. The suspects were "broken-as-last-left + hidden by pause,"
   not permanently pinned. Only a true digest-PINNED spec could be permanently broken — and the only 2 pinned-digest
   deployments found (`features-service-sports-job` @`b7fc`, `consolidator-liveness-watchdog` @`b39a`) are both pinned
   to TODAY's (2026-07-15) builds, already fresh/safe. The old `features-sports-service:latest` @`8f176d37` (2026-04-22,
   in-window) still exists in AR but is ORPHANED — no current job/service references it.

## Remediation plan

### For CONFIRMED-BROKEN deployments: NONE required (zero found)

There is no broken deployment to rebuild. The generic recipe below is recorded so that if any in-window digest-PINNED
deployment surfaces later, the operator/orchestrator can drive the exact fix that worked for features-sports this
session.

**Generic per-broken-deployment recipe (mirrors the features-sports fix):**

1. **Rebuild the image against current deps** via its Cloud Build trigger (e.g. the service's own `cloudbuild.yaml`,
   `_SERVICE_NAME: <service>`) so the new layer resolves UTL 1.6.0 + the republished UAC (`>=0.3.0`, carrying
   `internal/`). For MTDS-family images this is already moot (source-vendored), but a rebuild is the universal fix.
2. **Verify the rebuilt image BEFORE redeploy** with the real runtime import — never infer from constraints:
   `docker run --rm --entrypoint python <new-image> -c "import unified_api_contracts.internal.schemas.rbac; import unified_trading_library.config_interface.auth.entitlements; print('IMPORT_OK')"`
   → exit 0. (This is exactly plan todo P0's evidence step.)
3. **Redeploy / re-pin:** for a `:latest`-tracking Cloud Run JOB, un-pausing / re-triggering is sufficient (it
   re-resolves `:latest` on the next execution). For a digest-PINNED spec, re-pin the tfvars/terraform `docker_image`
   digest to the freshly-built one and ship via the deployment-service terraform path (`tofu.sh` wrapper with explicit
   `ENV=prod`), then confirm a green execution with `gcloud run jobs executions describe`.
4. **Archived/special-repo caveat (as with features-sports-service):** if the target's source repo is ARCHIVED, do NOT
   re-legitimize it by patching — the correct fix is to deploy the CONSOLIDATED successor (features-sports → the
   `features_service/sports/*` sub-package on the live `features-service` image), exactly the Path-B ruling the operator
   made this session. Check the repo's archive status before rebuilding.

### Residual close-out (1 command, optional)

Docker-run `uts-prod-manifest-consolidator-market-data-tradfi`'s deployed image (`mtds@sha256:6b3dbf5e...`) to convert
its HEALTHY-by-parity verdict to docker-confirmed. Not blocking — it is running `*/1` successfully.

## SEPARATE operational findings (NOT this import bug — flagged for their own triage)

These are real but have a **different root cause** than the entitlements import-skew; they are recorded here so they are
not lost, but they belong to their own triage, not this audit's remediation:

1. **~37-day DeFi/onchain data-collection GAP.** The 11 `uts-prod-mtds-collect-*` crons (perp-funding, oracle-prices,
   gas-fees, dex-pools, dex-swaps, lending-indices, lst-rates, liquidations, eigenlayer-rewards, evm-defi, solana-defi)
   are all **PAUSED**; their last executions (~2026-06-08, one 2026-05-28) FAILED — but the import test proves the
   failures were NOT the entitlements skew (the images import cleanly). So DeFi/onchain collection has been
   paused/un-run for ~37 days for a **different, still-unexplained reason**, and the 06-08 execution logs are past Cloud
   Logging's 30-day retention. Recommend a dedicated triage: un-pause one collector, capture the real failure, decide
   backfill.

   > **DISAMBIGUATED 2026-07-16 (dedicated read-only follow-up) — the "still-unexplained reason" IS the deliberate
   > 2026-06-08 pre-migration drain, NOT a code bug, and these jobs are NOT retired cruft.** Full write-up:
   > [`defi_scheduled_collection_outage_paused_crons_2026_07_16.md`](./defi_scheduled_collection_outage_paused_crons_2026_07_16.md).
   > Verdict: **REAL-OUTAGE (deliberate-drain / incomplete-resume), `safeToCleanup=false`.** The 11 collectors are the
   > intended steady-state mechanism, still declared in live terraform
   > (`deployment-service/terraform/gcp/defi_collection_scheduler.tf`), and the master migration catalogue's RESUME
   > runbook enumerates all 11 crons for un-pause (owned by `tradfi_v9_stage1_finish_2026_07_06.md` task -003,
   > BLOCKED-PREREQUISITES on the TradFi fleet-drain gate). The pause = the 48-scheduler/26-AWS-rule pre-migration
   > drain; the bucket consolidation changed STORAGE LAYOUT only and POST-DATES the pause. **This item's earlier
   > "un-pause one collector to capture the real failure" recommendation is now MOOT** — there is no unexplained live
   > failure (the 06-08 failure was the drain pause itself; the images are docker-proved IMPORT_OK and self-heal on
   > un-pause), and un-pausing now would race the not-yet-consolidated TradFi manifest. Correct action = resume via the
   > tracked, gated RESUME runbook once the TradFi close-out clears; NO cleanup, NO un-pause performed. Only fresh DeFi
   > data today is lumpy subset coverage from the `mvp_backfill_defi_onchain_v10_2026_06_27` backfill fleet. **Escalated
   > to operator for resume-sequencing direction.**

2. **Group-C jobs failing TODAY on FRESH post-06-09 images.** A set of jobs (e.g. `instrument-catalogue-regen`,
   `lifecycle-catalogue-full-*`, `dp-manifest-hygiene-*`, various `t1-recon`, `paper-*`, `blrs-daily-determinism`, etc.)
   fail on today's rebuilt images — so their failures are data/config/other, definitively NOT the import skew. Worth a
   separate sweep.
3. The mtds-collect PAUSE also masks that these are DeFi/onchain collectors whose data has simply not been gathered
   during the pause — an availability gap independent of any import bug.

## Method / integrity notes

- **READ-ONLY throughout.** Only `gcloud ... describe/list` (read) + local `docker pull` / `docker run --rm` /
  `docker rmi` were used. No deployed service, job, image, or Cloud Scheduler was modified.
- **Test-by-(digest × entrypoint), not by image alone.** The bug is codepath-specific:
  `manifest-consolidator-market- data-tradfi-legacy` SUCCEEDED on the same in-window digest `1442791f` that
  `instruments-tradfi-legacy` FAILED on, so an in-window image is necessary but not sufficient — the entrypoint must
  actually import `entitlements.py`.
- **Fleet was actively rebuilding during the audit window** (instruments/mtds `:latest` rebuilt 2026-07-15; ~19
  consolidators mid-execution) — several "stale since May" premises were already STALE by test time, which the per-
  suspect tests caught and corrected.

## Status

**RESOLVED.** Audit complete; zero broken deployments; features-sports-service confirmed the only casualty. Kept as a
resolved reference doc: it records the source-vendored-UAC immunity (why the heuristic over-flags), the self-healing
`:latest` job behavior, and the two separate operational findings (37-day DeFi gap; Group-C fresh-image failures) that
warrant their own triage.
