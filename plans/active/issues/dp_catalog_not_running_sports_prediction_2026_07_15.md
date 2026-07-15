---
doc_type: issue
title:
  DP_CATALOG_NOT_RUNNING fired for sports + prediction (25.7h/25.8h stale) — two UNRELATED root causes, both
  pre-existing, NOT caused by the same-session tradfi corp-actions fix
summary:
  'Two CRITICAL `DP_CATALOG_NOT_RUNNING` (DP-CATALOG-001) alerts fired 2026-07-15 ~03:47 local for sports
  (`instruments-store-sports-prd-…/prod/catalog.parquet`, 25.7h stale) and prediction
  (`instruments-store-pred-prd-…/prod/catalog.parquet`, 25.8h stale). Investigated as a regression-suspect against the
  same-session instruments-service commit `03f71c81a` (tradfi corp-actions MTDS-manifest exclusion) — CLEARED: that
  commit touches only `enumerate_expected_universe.py` (the expected-universe/manifest-seeding script, writes
  `_index/availability_index.parquet`), never `build_instrument_catalogue.py` (the actual `prod/catalog.parquet` writer
  these alerts probe) — a structurally different script/artifact — and its edit is `elif asset_group ==
  "tradfi":"`-scoped in both call sites, never touching the sports/prediction branches. Root causes (confirmed via live
  Cloud Run Job logs, both PRE-DATE the 03f71c81a commit landing at 2026-07-15T02:21:54Z): **sports** —
  `lifecycle-catalogue-regen-sports`''s monotonic guard REJECTED a same-day roll-up (27,210 rows < previous 27,216) as
  `CATALOGUE_SHRINK_BLOCKED`, correctly refusing to overwrite the prod catalogue with a smaller row count (exit 1,
  01:00:59 UTC 07-15 — before the commit existed). **prediction** — `lifecycle-catalogue-regen-prediction` has been
  SIGKILLed (signal 9, consistent with OOM against its 4Gi Cloud Run memory limit) at the monotonic-guard/promote-write
  stage on 3 consecutive days (07-13, 07-14, 07-15), first failure ~40h before the commit landed.'
status: open
nature: issue
asset_group: [sports, prediction]
stage: [data]
repos: [instruments-service, deployment-service]
scope: [engineer, admin]
tags: [catalog, catalogue, monotonic-guard, oom, cloud-run-job, monitoring, data-pipeline, sports, prediction]
related:
  [
    codex/05-infrastructure/data-pipeline-alerts.registry.yaml,
    codex/02-data/instruments-foundation-and-catalogue-completeness.md,
    codex/05-infrastructure/manifest-consolidator-ssot.md,
    plans/active/issues/cefi_monotonicity_guard_alerting_and_dark_venues_2026_07_07.md,
    plans/active/issues/cross_ag_never_seeded_backlog_scan_2026_07_06.md,
    plans/active/issues/tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md,
  ]
created: 2026-07-15
parent_epic: instruments_master
priority: P1
source: ["operator report: CRITICAL DP_CATALOG_NOT_RUNNING x2 (sports, prediction) at 2026-07-15 ~03:47"]
assigned_vm:
resolved_by:
locked_by:
locked_since:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-15
---

## Regression check against same-session instruments-service@03f71c81a — CLEARED

Commit `03f71c81ad055eea1f55f1cddc4607a40ac5b5ba` (2026-07-15T03:21:54+01:00 = **02:21:54 UTC**) added
`_TRADFI_MTDS_TICK_MANIFEST_EXCLUDED_DATA_TYPES` + `_tradfi_mtds_tick_manifest_data_types()` to
`instruments-service/scripts/enumerate_expected_universe.py`, wired into two `elif asset_group == "tradfi":` branches
(`enumerate_v2()` and `main()`). Two independent lines of evidence clear it:

1. **Wrong artifact/script entirely.** `enumerate_expected_universe.py` READS a catalog parquet (via `--catalog-path`)
   and WRITES `_index/availability_index.parquet` + `_index/expected_universe_ranges.parquet` (the
   expected-universe/manifest-seeding artifact). The alert probes `prod/catalog.parquet` — that file is written by a
   DIFFERENT script, `build_instrument_catalogue.py` (confirmed via
   `gcloud run jobs describe lifecycle-catalogue-regen-{sports,prediction}`: container args are
   `/app/instruments-service/scripts/build_instrument_catalogue.py --asset-group {sports,prediction} ...`). The two
   scripts are architecturally separate; the tradfi fix never touches `build_instrument_catalogue.py`.
2. **Even if it were the same script, the edit is tradfi-scoped.** Both call sites are `elif asset_group == "tradfi":`
   branches; sports hits its own pre-existing `elif asset_group == "sports":` branch (`_sports_data_types()`, unchanged)
   and prediction falls through the unchanged generic `else`. No shared helper was touched.
3. **Timing precludes causation regardless.** Both failing Cloud Run executions started BEFORE the commit landed: sports
   `lifecycle-catalogue-regen-sports-ffgl4` started 2026-07-15T01:00:15Z; prediction
   `lifecycle-catalogue-regen-prediction-7d4sz` started 2026-07-15T01:00:13Z — both ~1h20m before the commit's 02:21:54Z
   landing, and the prediction failure streak's FIRST occurrence (07-13, execution `jlwmj`) was 2026-07-13T01:00:07Z,
   ~49h before the commit existed.

## Actual root causes (confirmed via live Cloud Run Job log reads)

### Sports — `CATALOGUE_SHRINK_BLOCKED`, monotonic guard working as designed

`lifecycle-catalogue-regen-sports` (Cloud Run Job, `asia-northeast1`, daily `0 1 * * *` UTC) rolled up 27,210 sports
catalogue rows from `sports_reference/by_date/` — 6 rows FEWER than the current promoted catalogue (27,216). The
monotonic guard (`build_instrument_catalogue.py`'s promote-write step) correctly REJECTED the write:
`Monotonic guard: new=27210 current=27216 decision=REJECT (shrink_blocked)` →
`CATALOGUE_SHRINK_BLOCKED: new=27210 < current=27216 — keeping previous good catalogue ... (pass --allow-catalogue-shrink to override for a legitimate corrective shrink)`
→ `exit_code=1`. This is the guard doing its job (per DP-CATALOG-002's own registry entry,
`detector: promote_catalogue/evaluate_monotonic_guard`) — the last GOOD catalogue (2026-07-14T01:06:00Z, 27,216 rows)
stayed live, but the job's exit(1) means the daily refresh never advances, so DP-CATALOG-001 (staleness) fires once the
gap crosses 24h. **Needs an operator call**: is the 6-row shrink a legitimate correction (league
de-registration/retirement — this codebase has an active 24-league de-registration ruling per
`enumerate_expected_universe.py`'s `_SPORTS_LEAGUE_ID_SENTINELS`/UAC `LEAGUE_REGISTRY` gate) that should be re-run with
`--allow-catalogue-shrink`, or a genuine by_date data regression that needs investigation first?

Secondary finding (non-blocking but worth fixing): the job's own `CATALOGUE_SHRINK_BLOCKED` structured-event upload to
the `central-element-323112-events` bucket 403s (`lifecycle-catalogue-regen@…iam.gserviceaccount.com` lacks
`storage.objects.create` on that bucket) — the failure reason is visible in Cloud Logging but never reaches the
structured event-log sink, degrading observability for this exact incident class.

### Prediction — SIGKILL (signal 9) at monotonic-guard/promote-write, 3 consecutive days

`lifecycle-catalogue-regen-prediction` has failed 07-13, 07-14, 07-15 (last success 07-12,
`lifecycle-catalogue-regen-prediction-vhlf2`). Each failing run reaches `[BISECT-E] monotonic-guard + promote-write`
(2,673,230 rows, MVP-tagged) and is then killed: `Container terminated on signal 9` — both retry attempts (task0, task1)
hit the identical point before the job gives up. The Cloud Run Job's resource limit is `cpu: 2, memory: 4Gi` — signal 9
immediately after MVP-tagging a 2.67M-row dataframe and before the guard/promote step completes is consistent with an
OOM kill, not an application exception (no traceback, no `CATALOGUE_ROLLUP_FAILED` event — the process is killed
externally). `prod/catalog.parquet` for prediction is frozen at 2026-07-14T00:58:37Z / 2,673,230 rows (the last
successful promote). Needs: bump the job's memory limit (or slim the guard/promote-write step's peak memory) and re-run.

## Not previously tracked

Grepped `plans/active/issues/` for `DP_CATALOG_NOT_RUNNING`, `DP-CATALOG-001/002`, `CATALOGUE_SHRINK_BLOCKED`, and
`lifecycle-catalogue-regen-prediction` — no existing issue doc covers this specific sports-shrink-block / prediction-OOM
pair. `cefi_monotonicity_guard_alerting_and_dark_venues_2026_07_07.md` covers the SAME guard mechanism but for cefi
(dark-venue alerting gap, resolved); this is a new, distinct finding for sports/prediction.

## Open work (tracked todos)

- [ ] [OPS] P1. Sports — operator decision: confirm whether the 27,216→27,210 shrink is a legitimate
      league-de-registration correction; if so, re-run `lifecycle-catalogue-regen-sports` with
      `--allow-catalogue-shrink`; if not, investigate the by_date source data regression first. Repo:
      instruments-service.
- [ ] [INFRA] P1. Prediction — raise `lifecycle-catalogue-regen-prediction`'s Cloud Run Job memory limit above 4Gi (or
      profile/slim the monotonic-guard + promote-write step's peak memory for a 2.67M-row catalogue) so the job stops
      SIGKILLing at the promote stage; re-run once fixed and verify `prod/catalog.parquet` advances past
      2026-07-14T00:58:37Z. Repo: deployment-service (Cloud Run Job config) + instruments-service (memory profiling).
- [ ] [INFRA] P3. Grant `lifecycle-catalogue-regen@central-element-323112.iam.gserviceaccount.com`
      `storage.objects.create` on `central-element-323112-events` (or the correct events-sink bucket) so
      `CATALOGUE_SHRINK_BLOCKED`/similar structured events stop silently 403ing out of the event-log sink. Repo:
      deployment-service (IAM) — low priority, Cloud Logging already carries the same signal.

## Progress Log

- 2026-07-15: Filed by background investigation agent dispatched to check whether the same-session instruments-service
  tradfi corp-actions commit (`03f71c81a`) caused this staleness. Regression CLEARED (different script/artifact +
  tradfi-scoped edit + timing precludes causation — see above). Root-caused both alerts via live
  `gcloud run jobs executions list` + `gcloud logging read` + `gsutil stat` (no code changes made; diagnosis only).
