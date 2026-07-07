---
doc_type: issue
title: 'CeFi monotonicity guard has zero alerting — LIGHTER and PACIFICA are currently dark 11+ days, undetected'
summary:
  'A CeFi-specific Cloud Scheduler pipeline already runs build_instrument_catalogue.py daily (01:00 UTC) + weekly
  full (Sat 03:00 UTC) and already calls evaluate_monotonic_guard() unconditionally on every run
  (promote-blocking). But a guard rejection only does logger.info — no Slack, PagerDuty, or alerting-service hook
  exists anywhere, and the standalone manual report script (cefi_cumulative_drawdown_guard_2026_06_27.py) is not
  scheduled either. Actually running that script against live production GCS on 2026-07-07 found two currently-dark
  venues: LIGHTER and PACIFICA have had zero captured data of any kind since 2026-06-26 (11 days), each preceded by a
  partial capture immediately before going silent — the signature of an adapter breaking mid-fetch. The default
  script output hides this (truncates to top-40-by-severity, never prints its own total_thin counter of 1,007
  catalogue-wide thin-day collapses).'
status: open
nature: notes
asset_group: [cefi]
stage: [data, meta]
repos: [instruments-service, unified-trading-library, unified-api-contracts, alerting-service, deployment-service]
scope: [engineer, admin]
tags: [monotonicity, alerting, data-correctness, cefi, dark-venue, honest-coverage]
related:
  [
    ../instruments_completion_tracker_2026_07_06.md,
    ../instruments_foundation_completeness_2026_06_24.md,
    manifest_reprocessing_generic_utility_2026_07_07.md,
  ]
created: 2026-07-07
parent_epic: instruments_master
priority: P0
source: 'ASTER/CEFI instrument-service data-status audit, 2026-07-07 — a real execution of cefi_cumulative_drawdown_guard_2026_06_27.py against production GCS via instruments-service/.venv + GCP ADC'
assigned_vm: NA
resolved_by:
locked_by:
execution_scope: local-only
model_tier: sonnet-doable
thinking_tier: medium
estimate_class: infra
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.6
last_updated: 2026-07-07
supersedes:
superseded_by:
depends_on:
assigned_role: infra_engineering
drift_direction: advance-code
locked_since:
---

> **NOTIFY-OPERATOR class finding — live, currently-active, undetected data outage.** LIGHTER and PACIFICA (both
> 24/7 CeFi/on-chain perp venues) have produced no manifest rows of any capture status since 2026-06-26. Nothing
> paged anyone. This is filed both as the live incident and as the systemic gap that let it go unnoticed for 11 days.

## What already exists (don't rebuild this)

- Terraform: `deployment-service/terraform/gcp/lifecycle_catalogue_scheduler.tf` —
  `google_cloud_scheduler_job.lifecycle_catalogue_regen_daily["cefi"]` (cron `0 1 * * *`) runs
  `build_instrument_catalogue.py --asset-group cefi` (incremental); a weekly full self-heal
  (`lifecycle_catalogue_full_weekly["cefi"]`, `0 3 * * 6`) runs the same script `--mode full`.
- `promote_catalogue()` (`instruments-service/scripts/build_instrument_catalogue.py:1571-1636`) calls
  `evaluate_monotonic_guard()` (line 1584) **unconditionally** on every run, both daily and weekly — this already
  blocks a catalogue promotion whose total row count shrinks vs. the current canonical catalogue.
- The user's "fold the check into the daily job instead of a slow CI gate" instinct is already how this half works —
  there is no separate CI gate to replace; the check already lives inside the production scheduled script.

## What's actually missing — zero alerting, on either mechanism

- On rejection, `build_instrument_catalogue.py:1594-1611` calls `_emit_event("CATALOGUE_SHRINK_BLOCKED", ...)`, which
  (`_emit_event`, line 234-237) is a **"best-effort structured event log"** — plain `logger.info`, Cloud Logging
  only. It does not call UTL's `log_event()`, does not write to the GCS event-log path
  (`events/instruments-service/{date}/events.jsonl`), does not call alerting-service, Slack, or PagerDuty.
- Grepped `alerting-service` for `instruments-service` / `catalogue` / `drawdown` / `monotonic`: zero matches to
  `CATALOGUE_SHRINK_BLOCKED` or `evaluate_monotonic_guard`. The only catalogue-adjacent alert is
  `alerting-service/alerting_service/notifiers/data_pipeline_slack.py:93-99`'s `DP_CATALOG_NOT_RUNNING` — a
  **different**, staleness-based signal (the artifact hasn't refreshed within budget), wired end-to-end via a real
  UTL event constant → a UAC `_dp_rule("DP-CATALOG-001", ..., CRITICAL, PAGE_OPERATOR)` → alerting-service's Slack /
  PagerDuty notifiers. **No equivalent event constant or rule exists for a shrink/monotonic-guard trip.**
- The standalone report script `instruments-service/scripts/cefi_cumulative_drawdown_guard_2026_06_27.py` is a plain
  read-only CLI (`print()` only) with no scheduler entry anywhere (`.tf`/`.yml` grep across the workspace: zero
  hits). Its own header says `# Delete-when: superseded by a CLI subcommand once the cumulative-drawdown guard is
  wired into the catalogue build / QG` — the codebase's own comment says this is not yet wired in.
- A shrink-blocked exit code today produces: (a) one Cloud Logging error line, (b) a FAILED Cloud Run Job execution
  visible only if someone runs `gcloud run jobs executions list`, (c) one scheduler retry. Nothing pages, pings
  Slack, or reaches a human by default. No `google_monitoring_alert_policy` exists on the
  `lifecycle-catalogue-regen-*` jobs.

## The live incident this blind spot let through (found running the script for real, 2026-07-07)

Ran `instruments-service/.venv/bin/python scripts/cefi_cumulative_drawdown_guard_2026_06_27.py` against production
GCS (`instruments-store-cefi-prd-central-element-323112/_index/availability_index.parquet`) via GCP ADC. Real
output, all 29 CeFi venues, 64,096 captured cells:

- **Catalogue-wide: 5,621 total day-over-day drop-days; 1,007 cross the thin-day-collapse threshold (<50% of
  trailing 14-day median).** The script's default stdout truncates to the top 40 rows by collapse severity and
  never prints its own computed `total_thin` — so this number is invisible unless you re-derive it, as this audit
  did. Most of the 1,007 are historical and since recovered (DERIBIT 2020-2022, BYBIT early-2026 — both current as
  of 2026-07-07).
- **LIGHTER and PACIFICA are dark right now.** Both had rock-steady flat-line counts for their entire history
  (LIGHTER 198-213, PACIFICA 10), then each shows exactly one partial capture immediately before going silent —
  LIGHTER 213→18 (~8.5% of median), PACIFICA 10→4 (~40% of median) — and **zero rows of any capture status since
  2026-06-26** (11 days as of this filing). A partial capture immediately followed by total silence is the classic
  signature of an adapter breaking mid-fetch, not a deliberate venue pause.
- **ASTER itself has no active collapse** by this guard's definition — 119 day-over-day drops, worst single drop
  -279 (332→53, 2023-08-13→14), zero thin-day collapses, cumulative-ever-seen monotonic (never decreases, currently
  53→499). The repeated small drops read as periodic perp-contract roll-offs, not capture failures. Filed here only
  for completeness — no action needed on ASTER from this specific guard.
- **Residual worth reconciling separately, not part of this issue's scope:** this guard's cell-presence view says
  ASTER has 0 missing dates (1,082 consecutive days, 2023-07-22→2026-07-07), while the live turbo API says 11
  missing / 1,071 expected for the same venue and window — two counting methods disagreeing by 11 days. Tracked as
  a Stage-3 checklist item on the tracker, not duplicated here.

## Todos

- [ ] [SCRIPT] P0. Diagnose LIGHTER and PACIFICA's adapters — both went silent 2026-06-26 after a partial capture.
      Check the standard suspects first (base-URL / auth / rate-limit change on either exchange's API, a deploy that
      broke the fetch, a queue/scheduler that stopped dispatching these two venues specifically). Re-run the guard
      script post-fix to confirm data resumes. **Partial finding 2026-07-07 (see Progress Log)**: exchange APIs +
      adapter code both confirmed healthy right now; instead found the `uts-prod-instruments-service-cefi-t1-recon`
      Cloud Run Job (2cpu/4Gi) OOM-killing on 07-05/06/07, timing-correlated with 3 venues being added to the same
      CEFI batch on 2026-06-25 without a resource bump — plausible but NOT YET CONFIRMED as the actual 06-26 cause
      (06-26 itself shows a clean "completed successfully" in the Cloud Run audit log). Next agent: (1) bump the
      job to 4cpu/8Gi via `gcloud run jobs update uts-prod-instruments-service-cefi-t1-recon --region=asia-northeast1
      --cpu=4 --memory=8Gi` and watch the next 06:00 UTC run for OOM recurrence + LIGHTER/PACIFICA row counts; (2)
      find (or conclude is missing) the IaC resource pinning this job's current 2cpu/4Gi so the bump isn't reverted
      by a future `terraform apply` — not found in `t1_batch_scheduler.tf` (scheduler-trigger only, not the job
      itself), `cloud_run_job_registry.py` (observability classification only), `_imports_reconcile.tf`, the
      `container-job` module, or `terraform/services/instruments-service/gcp/terraform.tfvars` (references a
      different/legacy job name+schedule); (3) if genuinely unmanaged, that's its own infra-hygiene finding worth a
      one-line note once confirmed.
- [ ] [SCRIPT] P0. Once fixed, backfill the 2026-06-26 → fix-date gap for both venues if the source API supports
      historical reconstruction (same "filter the current adapter fetch by available_from/available_to" mechanism
      already used for other instrument-definition backfills); if not backfillable, stamp the gap with an honest
      `EXPECTED_*` reason rather than leaving it an unexplained hole.
- [ ] [CODE] P1. Wire the drawdown-guard's own `total_thin` counter into its stdout (currently computed but never
      printed) and drop or raise the top-40 truncation — the 1,007 catalogue-wide figure should not require a
      separate re-derivation to see.
- [ ] [CODE] P1. Build the alerting path, mirroring the proven `DP_CATALOG_NOT_RUNNING` / `DP-CATALOG-001` pattern:
  - [ ] Add a canonical event constant (e.g. `CATALOGUE_SHRINK_BLOCKED`) to
        `unified-trading-library/unified_trading_library/events/event_types.py`.
  - [ ] Add a matching UAC alerting rule (`_dp_rule("DP-CATALOG-00X", ..., CRITICAL, PAGE_OPERATOR)`) in
        `unified-api-contracts/unified_api_contracts/canonical/crosscutting/alerting/rules.py`.
  - [ ] Swap `build_instrument_catalogue.py`'s `_emit_event` call at the `CATALOGUE_SHRINK_BLOCKED` site to the real
        `unified_trading_library.log_event(...)` so the event actually leaves the process.
  - [ ] Add a notifier-side entry mirroring `data_pipeline_slack.py`'s `DP_CATALOG_NOT_RUNNING` block so
        alerting-service's Slack/PagerDuty path recognizes and renders the new event.
- [ ] [INFRA] P2. Schedule `cefi_cumulative_drawdown_guard_2026_06_27.py` (or its logic folded into the daily
      catalogue build directly, per the code-hook point already identified above) so a thin-day-collapse detection
      runs automatically, not only when a human remembers to invoke it by hand.
- [ ] [CODE] P2. Cross-cutting: extract DeFi's `_enforce_defi_monotonicity` (`instruments_service/engine/orchestrator/defi.py:119-156,187-225`)
      into an asset-group-parameterized shared helper in `venue_core.py`, called from the shared
      `process_fetch.py:169-179` chokepoint, scoped to `_VENUE_GRAIN_ASSET_GROUP_TOKENS` (CEFI/TRADFI — DeFi keeps
      its existing bespoke caller; Sports/Prediction don't get this, their manifest grain isn't venue-count-shaped).
      Neither CeFi nor TradFi has a dedicated orchestrator file today — they run the fully shared path — so this is
      a single insertion point, not five per-asset-group copies. **Caveat:** the threshold *policy* must be a
      per-asset-group parameter, not a verbatim copy of DeFi's strict never-regress-below-all-time-max rule — CeFi
      delistings and TradFi contract expiries are real, expected decreases in *today's active count* (though never
      in *instruments-ever-seen*), and a blind DeFi-style block would permanently false-block the first legitimate
      CeFi delisting.

## Progress Log

- **2026-07-07 (partial diagnosis — deprioritized mid-investigation, operator redirect)** — Ruled out: LIGHTER's
  exchange API is up and healthy (direct `curl` to `mainnet.zklighter.elliot.ai` returns real market data);
  PACIFICA's adapter is a static curated list with zero network dependency and cannot fail on the exchange side.
  Ran both adapters' `get_instruments()` + UAC `validate_instrument_records()` locally against today's date — both
  produce clean, fully-valid output right now (PACIFICA 10/10 valid), so the Python code itself is not currently
  broken for either venue. **Found a real, currently-active, separate problem**: the daily Cloud Run Job
  `uts-prod-instruments-service-cefi-t1-recon` (the actual CeFi capture job, `--asset-group=CEFI`, 2cpu/4Gi) has been
  OOM-killing (`"The configured memory limit was reached"`, signal 9) on at least 2026-07-05, -06, -07 — timing that
  lines up with 2026-06-25's reclassification commit (`2f7d4548`) adding 3 more venues (LIGHTER-ZKSYNC,
  PACIFICA-SOLANA, EXTENDED-STARKNET) to the same CEFI batch without raising the container's resource limits.
  2026-06-26 (the actual outage start) itself shows `"Execution completed successfully"` in the Cloud Run audit
  log, and 2026-06-27 shows a different failure (`"container exited with an error"`, exit code 1) — so the OOM
  pattern is NOT yet confirmed as the day-1 cause, only as a real problem that is CURRENTLY ongoing (last 3 days).
  Could not find zero-arg application stdout/stderr for ANY of these executions (only Cloud Run's own
  audit/system-event log lines) to see per-venue progress, and could not locate the Terraform/IaC resource that
  pins this job's 2cpu/4Gi limit (searched `t1_batch_scheduler.tf`, `cloud_run_job_registry.py`, `_imports_reconcile.tf`,
  the `container-job` module, `terraform/services/instruments-service/gcp/terraform.tfvars` — none is a confirmed
  match; the job may be unmanaged/ad-hoc-`gcloud`-created, which is itself worth flagging). Stopped here on operator
  redirect (session priority shifted to the deployment-api/deployment-ui drilldown work) — **not fixed, evidence
  preserved below for whoever picks this back up.**
- **2026-07-07** — Filed from the ASTER/CEFI instrument-service data-status audit, after the operator asked to
  actually run the manual guard script rather than only read its code. Read-only investigation + one real (safe,
  read-only) execution against production GCS; no files edited, no writes to any bucket.
