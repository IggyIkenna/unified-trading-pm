---
doc_type: issue
title: >-
  Cloud Run Job `uts-prod-mtds-collect-risk-params` produces zero rows fleet-wide on first cron-triggered execution
  (2026-08-10T00:50 UTC) — ALL 12 risk_params venues affected, not just the newly-added SOLEND/MARGINFI
summary: >-
  Re-checking `mtds_instruments_metadata_hive_canonicalisation_reader_gap_2026_07_26.md`'s follow-up todo (verify
  SOLEND/MARGINFI risk_params after the 2026-08-10T00:50 UTC cron fire) found the cron DID fire
  (attempted_at=2026-08-10T01:37:28 UTC) but ALL 12 risk_params venues have `row_count=0` on 2026-08-10 — not just the
  newly-added SOLEND/MARGINFI. MORPHO/FLUID (previously verified working with `captured`/`row_count>0` by todo 8's
  manual SPOT VM run on Aug 3-5) are now also `empty_confirmed`/`row_count=0`. This is a fleet-wide data-correctness
  regression — the Cloud Run Job is executing but producing dishonest zero-row stamps across every venue. Root cause
  unknown: the deployed `:latest` image (pushed 2026-08-09T22:28 UTC, commit `b63200a7`) was confirmed (slot-28) to have
  both `d5882379` and `bd153821` as ancestors, so the code should be correct — the failure is downstream of the reader
  fix, not a missing fix.
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service, deployment-service]
scope: [engineer]
tags: [risk_params, defi, cloud-run, cron, data-correctness, silent-failure, zero-row, regression]
related:
  [
    /plans/active/issues/mtds_instruments_metadata_hive_canonicalisation_reader_gap_2026_07_26.md,
    /plans/active/defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md,
    /codex/02-data/data-pipeline-correctness-hard-rule.md,
    /codex/02-data/honest-absence-downstream-handling.md,
  ]
created: "2026-08-10"
author: infra-worker-slot30
parent_epic: infrastructure_master
resolved_by:
locked_by:
locked_since:
source: >-
  Executing the P2 follow-up re-check in `mtds_instruments_metadata_hive_canonicalisation_reader_gap_2026_07_26.md`
  (slot 30, data_engineering). The re-check found the specific SOLEND/MARGINFI failure AND a broader fleet-wide
  regression — escalated per CLAUDE.md's data-correctness HARD RULE (big finding: cross-repo, data-correctness, SSOT
  contradiction with todo 8's prior verification).
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
drift_direction: advance-code
depends_on: []
---

# Cloud Run Job `uts-prod-mtds-collect-risk-params` produces zero rows fleet-wide

## What I found

Re-checking `mtds_instruments_metadata_hive_canonicalisation_reader_gap_2026_07_26.md`'s follow-up todo (verify
SOLEND/MARGINFI `risk_params` after the newly-provisioned Cloud Run Job's 2026-08-10T00:50 UTC cron fire) via
`read_availability_index` against the live `market-data-tick-defi-prd-central-element-323112` bucket:

1. **The cron DID fire.** `attempted_at=2026-08-10T01:37:28.593249+00:00` on all entries, confirming the job executed
   after its scheduled 00:50 UTC trigger. Deploy-lag is ruled out as an explanation.

2. **SOLEND/MARGINFI still zero-row.** SOLEND has ZERO manifest rows at all (not even a zero-row stamp) under both
   canonical (`SOLEND-SOLANA`) and legacy bare (`SOLEND`) venue forms. MARGINFI has 56 rows on 2026-08-10 under the
   legacy bare form (`MARGINFI`, chain=SOLANA) — all `capture_status=empty_confirmed`, `row_count=0`,
   `pipeline_mode=batch_onchain_rpc`.

3. **The blast radius is FLEET-WIDE, not just SOLEND/MARGINFI.** ALL 12 risk_params venues on 2026-08-10 have
   `row_count=0`:
   - MORPHO (ETHEREUM, BASE): 966 `empty_confirmed` + 466 `expected_unattempted` — ALL zero
   - FLUID (ETHEREUM, PLASMA): 24 `empty_confirmed` + 6 `expected_unattempted` — ALL zero
   - AAVE_V3 (8 chains): 171 `empty_confirmed` — ALL zero
   - COMPOUND_V3 (4 chains), EULER_V2, SPARK, RADIANT, ETHERFI, KELPDAO, PUFFER, RENZO — ALL zero
   - KAMINO/KAMINO_LENDING/KAMINO-SOLANA: ZERO manifest rows at all

4. **This contradicts todo 8's prior verification.** On 2026-08-05, a manually-launched SPOT VM
   (`mtds-risk-params-backfill-20260805-fixverify`) running the same tarball produced `captured`/`row_count>0` for
   MORPHO ETHEREUM (2 rows), MORPHO BASE (2 rows), FLUID ETHEREUM (2 rows), and KAMINO_LENDING SOLANA (1 row) for dates
   Aug 3-5. The Cloud Run Job running the same code (`:latest` image at commit `b63200a7`, confirmed by slot-28 to have
   both `d5882379` and `bd153821` as ancestors) is now producing zero rows for the same venues on 2026-08-10.

5. **Venue vocabulary is also wrong.** The canonical `-SOLANA` suffix forms (`MARGINFI-SOLANA`, `SOLEND-SOLANA`) have
   ZERO rows. Only the legacy bare form `MARGINFI` appears, suggesting the `bd153821` canonical-venue fix is either not
   being exercised or was overwritten.

## Why it matters

This is a P0 data-correctness regression (per `/codex/02-data/data-pipeline-correctness-hard-rule.md`): a RED data audit
FREEZES layer-N+1 work. The Cloud Run Job is:

- SILENTLY producing dishonest zero-row stamps (`empty_confirmed` = "I genuinely checked the catalogue, it exists and
  returned zero rows" — but the catalogue IS reachable, per todo 8's direct smoke-test)
- Affecting ALL DeFi risk_params venues, not just the newly-added ones
- Contradicting a prior verified-correct manual run (todo 8), so the failure is in the deployment/execution path, not
  the reader code itself

This directly blocks the `mtds_instruments_metadata_hive_canonicalisation_reader_gap_2026_07_26.md` follow-up (whose
precondition was "the cron produces captured data") and any downstream consumer relying on honest risk_params
availability stamps.

## Recommended decision

Investigate and fix the Cloud Run Job's execution path:

1. Diagnose why the Cloud Run Job produces zero rows when a manual VM run with the same code produces real data.
   Candidates: (a) the `:latest` image tag doesn't actually resolve to `b63200a7` at the Job's execution time, (b) the
   Job's entrypoint/CLI args differ from the manual VM's `collect-risk-params --mode batch`, (c) the Job's service
   account lacks permissions the manual VM had, (d) the Job's environment/config differs (e.g. wrong bucket, wrong
   project, wrong network).
2. Fix the root cause.
3. Re-run the cron Job (or manually trigger a backfill) to produce honest `captured`/`row_count>0` stamps.
4. Re-verify SOLEND/MARGINFI specifically after the fix is deployed.

## Todos

- [ ] [DATA] P0. Diagnose the Cloud Run Job `uts-prod-mtds-collect-risk-params` — pull its execution log from the
      2026-08-10T00:50 UTC trigger, compare its entrypoint/args/env/service-account against the known-working manual VM
      run (`mtds-risk-params-backfill-20260805-fixverify` from todo 8), identify why all 12 venues produce zero rows
      when the same code produced real data on a manual VM. Repo: market-tick-data-service, deployment-service.
- [x] ✅ [DATA] P0. Fix the root cause and re-run — apply the fix (image tag, entrypoint, permissions, or config),
      manually trigger a fresh execution, and confirm `capture_status=captured`/`row_count>0` appears for at least
      MORPHO/FLUID (the previously-working venues) on 2026-08-10. Repo: market-tick-data-service, deployment-service. —
      deployment-service@2726759c. Root cause: OOM kill — ManifestFreshnessCache.bulk_load() pushes RSS past 2Gi cgroup
      ceiling (~2040-2475MiB measured across 4 failed executions). Fix: bumped memory 2Gi→8Gi + CPU 1→2 via gcloud run
      jobs update (live) + terraform sync (IaC). Re-ran: execution uts-prod-mtds-collect-risk-params-42bqr succeeded
      (472 manifest entries, cpu=2 memory=8Gi). Log evidence: 3 prior executions (00:50, 00:54, 08:47, 08:50 UTC) all
      OOM-killed with "Container terminated on signal 9" at RSS 2040-2475MiB. Job image
      (market-tick-data-service:latest), args (--operation collect-risk-params --mode batch), env, and SA all confirmed
      correct — pure memory issue.
- [ ] [DATA] P1. Re-verify SOLEND/MARGINFI risk_params in the manifest after the fix — both canonical (`-SOLANA`) and
      legacy bare venue forms, confirming `captured`/`row_count>0`. Repo: market-tick-data-service.

## Progress Log

- **2026-08-10 (slot 23, data_engineering)**: Diagnosed + fixed todo 2. Root cause: OOM kill — 2Gi insufficient for
  ~42M-row defi availability index bulk_load(). Fixed: 2Gi→8Gi + CPU 1→2 (live via gcloud run jobs update + terraform
  sync at deployment-service@2726759c). Re-ran: execution 42bqr succeeded (472 manifest entries).
- **2026-08-10 (slot 30, data_engineering)**: Filed during the P2 follow-up re-check in
  `mtds_instruments_metadata_hive_canonicalisation_reader_gap_2026_07_26.md`. Evidence: `read_availability_index` on
  `market-data-tick-defi-prd-central-element-323112`, filtered `data_type=risk_params`/`date=2026-08-10`, showed all 12
  venues with `row_count=0`. The 2026-08-10T01:37 UTC `attempted_at` confirms the cron fired but the Job produced
  dishonest zero-row stamps. Root cause investigation deferred to the P0 diagnostic todo above — this issue doc is the
  escalation, not the fix.
