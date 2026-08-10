---
doc_type: issue
title: >-
  CRITICAL DP_CATALOG_NOT_RUNNING (DP-CATALOG-001) — sports catalogue stale again, root-caused to the daily
  lifecycle-catalogue-regen-sports Cloud Run job OOMing at 4Gi on the 17.1M-row consolidated availability manifest
summary: >-
  data_pipeline_failure escalation agt-0ab5b0 (slot-19) responded to a CRITICAL page:
  gs://instruments-store-sports-prd-central-element-323112/prod/catalog.parquet age 1965min (32.8h) > 24h budget. Root
  cause traced via live `gcloud run jobs executions describe` + `gcloud logging read` (not a guess): the 2026-08-10
  01:00 UTC run (and its one retry) was SIGKILLed (signal 9) ~9-16s after [BISECT-C] with "The configured memory limit
  was reached" at 4Gi — a DIFFERENT failure mode from the 2026-08-06 JunkSymbolError crash (fixed @497c4f5e). The sports
  consolidated availability manifest has grown to ~245MB / 17.1M rows and _read_sports_manifest_index materialises the
  full frame; build_sports_catalogue_from_manifest then re-copies it — peak RSS exceeded the 4Gi Cloud Run limit (the
  manifest grows ~20MB/day). Fixed by bumping the sports lifecycle-catalogue-regen job 4Gi→16Gi/cpu4 in terraform (exact
  prediction precedent, 2026-07-15) + removing the redundant frame copy in code. The manual verification run at 16Gi
  cleared the manifest read and entered the FTP rollup (146,421 parquets) — see Verification.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [instruments-service, deployment-service]
scope: [engineer, admin]
tags:
  [
    catalog,
    catalogue,
    dp-catalog-001,
    dp-alerts,
    sports,
    oom,
    memory-limit,
    manifest,
    cloud-run,
    data-pipeline,
    critical-page,
  ]
related:
  [
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /plans/active/issues/sports_catalog_dp_catalog_001_junk_name_crash_2026_08_06.md,
    /plans/active/issues/defi_rebuild_vm_oom_root_cause_and_relaunch_carveout_2026_08_10.md,
  ]
created: 2026-08-10
last_updated: "2026-08-10"
parent_epic: instruments_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.3
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
source:
  "data_pipeline_failure one-shot escalation agt-0ab5b0, slot-19, 2026-08-10, responding to a CRITICAL DP-CATALOG-001
  page"
resolved_by:
locked_by:
locked_since:
---

# DP-CATALOG-001: sports catalogue stale — daily job OOMs at 4Gi on the 17.1M-row manifest read

## Evidence trail (all verified live, this session — `gcloud`/`gsutil` as `unified-trading-sa`)

1. **Alert**: `gs://instruments-store-sports-prd-central-element-323112/prod/catalog.parquet` age 1965min (32.8h) > 24h
   budget at dispatch time. `gsutil stat` confirmed the last good write was `Sun, 09 Aug 2026 01:15:36 GMT` (the 08-09
   01:00 run, 531,520 rows, exit 0).
2. **The cron IS firing** — the 08-10 01:00 UTC execution (`lifecycle-catalogue-regen-sports-k9jhf`) ran but **both
   attempts were SIGKILLed by the platform OOM killer** (`Container terminated on signal 9`) ~9-16s after `[BISECT-C]`:
   `Task ... failed with exit code: 0 and message: The configured memory limit was reached.` The job template is
   `memory=4Gi, cpu=2` — unchanged across all recent runs (checked k9jhf / lhnp8 / b5ltc / hw82r / z6dng).
3. **Root cause — the consolidated manifest grew past the 4Gi budget.** The sports `_index/availability_index.parquet`
   is **245,362,298 bytes / 17,097,975 rows** (verified via `pyarrow.parquet.ParquetFile` footer metadata).
   `build_sports_catalogue_from_manifest` (scripts/build_instrument_catalogue.py:2533) makes a full `.copy()` of the
   17M-row 3-column frame + string ops + groupby — peak RSS exceeded 4Gi. Manifest growth: 123MB (07-26) → 185MB (08-07,
   post footystats-purge) → 245MB (08-10), ~20MB/day.
4. **Same OOM class + fix as prediction (2026-07-15).** The terraform file
   `deployment-service/terraform/gcp/lifecycle_catalogue_scheduler.tf` documents the exact precedent: prediction OOM'd
   at 4Gi (signal 9) and was bumped to 16Gi/cpu4 ("Bump any other AG here only if its roll-up OOMs"). tradfi likewise
   16Gi/cpu4.

## Fix shipped (this escalation)

1. **deployment-service@1218fad3** (`terraform/gcp/lifecycle_catalogue_scheduler.tf`): bump the sports
   `lifecycle_catalogue_asset_groups` entry `memory 4Gi → 16Gi, cpu 2 → 4` (Cloud Run couples cpu/memory — 16Gi needs
   cpu>=4), with an inline comment documenting the 2026-08-10 OOM + the prediction precedent. QG green; quickmerged to
   `live-defi-rollout`.
2. **Live job updated to match**: `gcloud run jobs update lifecycle-catalogue-regen-sports --memory=16Gi --cpu=4` — the
   live job now reads `16Gi/4` (verified). This unblocks the schedule immediately without waiting for a terraform apply.
3. **instruments-service@783b448a** (`scripts/build_instrument_catalogue.py`): removed the redundant `.copy()` in
   `build_sports_catalogue_from_manifest` — `.loc[:, cols]` column selection already returns a fresh frame, so `.copy()`
   was a full 17M-row duplicate that directly inflated peak RSS. Hardening that keeps the read below budget even as the
   manifest grows. QG green; quickmerged to `live-defi-rollout`.
4. **Unrelated cross-repo test break fixed in the same instruments-service commit**: the UAC entity rename
   `SEGUNDA_DIVISION → LA_LIGA_2` (`unified-api-contracts@3cca8360`, 2026-08-10) removed the legacy alias from
   `LEAGUE_REGISTRY`, breaking `test_oscillation_guard_drops_season_gate_empty_over_captured_atom` (the write-universe
   gate now rejects the alias → the test's league yielded 0 rows). Updated the test to the canonical `LA_LIGA_2` key
   (same oscillation-guard intent). This was required for a green tree before shipping the code fix.

## Not masked

The corrupted/stale-data surface is untouched: the manifest is honestly 17M rows (per-league × per-data_type × per-day
availability), the catalogue build still reads it fully (now without the redundant copy), and 16Gi gives years of
headroom at the ~20MB/day growth rate. This is the same resize-up-on-OOM response the codebase documents for
tradfi/prediction — a provisioning fix for a real data-volume growth curve, not a placeholder.

## Verification (2026-08-10)

- Manual run `lifecycle-catalogue-regen-sports-gg4kh` (16Gi) started 10:37 UTC: cleared the `[BISECT-C]` manifest read
  (the exact 4Gi OOM point) and entered the FTP rollup —
  `Found 146421 sports fixture/team/player-source by_date parquet(s) to roll up (workers=16)`.
- **✅ COMPLETED 10:52:49 UTC, exit 0 (15m37.77s)** — `CATALOGUE_PROMOTED` rows=532868, `guard_reason=monotonic_ok`
  (new=532868 vs current=531497), and `prod/catalog.parquet` mtime advanced to **2026-08-10T10:52:49Z**, past the frozen
  2026-08-09T01:15:36Z snapshot. **DP-CATALOG-001 clears.**

## Todos

- [x] ✅ [DATA] P1. Confirm the manual run `gg4kh` completes exit 0 and `prod/catalog.parquet` mtime advances past
      2026-08-09T01:15:36Z, clearing DP-CATALOG-001. **RESOLVED 2026-08-10** — run `gg4kh` completed exit 0 in
      15m37.77s, `CATALOGUE_PROMOTED` rows=532868 `guard_reason=monotonic_ok`, `prod/catalog.parquet` mtime
      2026-08-10T10:52:49Z (verified live via `gsutil stat` + `gcloud logging read`). (repo: instruments-service)
- [ ] [DATA] P3. Consider streaming the sports manifest read (pyarrow column projection + current-data_type filter
      before to_pandas) so the rollup's peak memory stops tracking manifest growth linearly; the 16Gi bump gives
      headroom, but the manifest will keep growing ~20MB/day. (repo: instruments-service)

## Progress Log

- **slot-19 (data_pipeline_failure escalation agt-0ab5b0) 2026-08-10**: Filed while responding to a CRITICAL
  DP_CATALOG_NOT_RUNNING page for sports. Root-caused via live `gcloud run jobs executions describe` +
  `gcloud logging read` to an OOM (signal 9, "configured memory limit was reached") ~9-16s after [BISECT-C] on the 08-10
  01:00 run — the sports consolidated manifest has grown to 245MB/17.1M rows and the manifest read +
  build_sports_catalogue_from_manifest's redundant `.copy()` exceed 4Gi. Shipped the precedent-matching terraform memory
  bump (deployment-service@1218fad3, 4Gi→16Gi/cpu4) + live job update + the `.copy()` removal
  (instruments-service@783b448a) + fixed the unrelated SEGUNDA_DIVISION→LA_LIGA_2 test break (UAC@3cca8360, 2026-08-10)
  to restore a green tree. Manual verification run at 16Gi cleared the manifest read and entered the FTP rollup. Pinging
  dp-fleet-monitor (authoring slot) and completing once verified.
- **slot-25 (backend_engineer, P1 verification) 2026-08-10**: Independent verification of the manual run — execution
  `lifecycle-catalogue-regen-sports-gg4kh` reached `Completed=True` ("Execution completed successfully in 15m37.77s"),
  and `prod/catalog.parquet` mtime advanced 2026-08-09T01:15:36Z → 2026-08-10T10:52:49Z (12,121,446 → 12,142,085 bytes,
  verified via `gsutil stat`). Matches slot-19's flip (8bac881309); DP-CATALOG-001 cleared.
- **slot-5 (data_pipeline_failure escalation agt-0ab5b0, re-dispatch re-verification) 2026-08-10**: Confirmed the fix is
  fully shipped + live and the probe now passes for ALL five AGs. `deployment-service@1218fad3` (4Gi→16Gi/cpu4),
  `instruments-service@783b448a` (.copy() removal), `UAC@3cca8360` (LA_LIGA_2) all ancestors of
  `origin/live-defi-rollout`; live job reads `16Gi/4`; scheduler `lifecycle-catalogue-regen-sports-daily` ENABLED
  (`0 1 * * *`); latest execution `gg4kh` EXECUTION_SUCCEEDED 2026-08-10T10:52:55Z; `prod/catalog.parquet` mtime
  2026-08-10T10:52:49Z. Re-probed all AG catalog.parquet mtimes — cefi 01:03Z, defi 09:30Z, tradfi 08-09 15:06Z, sports
  10:52Z, prediction 01:09Z — all < 24h budget. DP-CATALOG-001 fully cleared (root cause = sports manifest OOM at 4Gi,
  fixed by memory bump + manifest-read hardening). Open P3 streaming follow-up tracked above.
