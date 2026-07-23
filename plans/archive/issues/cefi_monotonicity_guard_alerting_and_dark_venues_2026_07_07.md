---
doc_type: issue
title: "CeFi monotonicity guard has zero alerting — LIGHTER and PACIFICA are currently dark 11+ days, undetected"
summary:
  "A CeFi-specific Cloud Scheduler pipeline already runs build_instrument_catalogue.py daily (01:00 UTC) + weekly full
  (Sat 03:00 UTC) and already calls evaluate_monotonic_guard() unconditionally on every run (promote-blocking). But a
  guard rejection only does logger.info — no Slack, PagerDuty, or alerting-service hook exists anywhere, and the
  standalone manual report script (cefi_cumulative_drawdown_guard_2026_06_27.py) is not scheduled either. Actually
  running that script against live production GCS on 2026-07-07 found two currently-dark venues: LIGHTER and PACIFICA
  have had zero captured data of any kind since 2026-06-26 (11 days), each preceded by a partial capture immediately
  before going silent — the signature of an adapter breaking mid-fetch. The default script output hides this (truncates
  to top-40-by-severity, never prints its own total_thin counter of 1,007 catalogue-wide thin-day collapses)."
status: resolved
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
    /plans/active/issues/manifest_reprocessing_generic_utility_2026_07_07.md,
  ]
created: 2026-07-07
parent_epic: instruments_master
priority: P0
source:
  "ASTER/CEFI instrument-service data-status audit, 2026-07-07 — a real execution of
  cefi_cumulative_drawdown_guard_2026_06_27.py against production GCS via instruments-service/.venv + GCP ADC"
assigned_vm: NA
resolved_by:
  instruments-service@0db619d5 + deployment-service tofu apply (terraform/gcp/cefi_drawdown_guard_scheduler.tf,
  terraform/gcp/audit03_cron_provisioning.tf) 2026-07-10
locked_by:
execution_scope: local-only
model_tier: sonnet-doable
thinking_tier: medium
estimate_class: infra
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.6
last_updated: 2026-07-10
supersedes:
superseded_by:
depends_on:
assigned_role: infra
drift_direction: advance-code
locked_since:
---

> **NOTIFY-OPERATOR class finding — live, currently-active, undetected data outage.** LIGHTER and PACIFICA (both 24/7
> CeFi/on-chain perp venues) have produced no manifest rows of any capture status since 2026-06-26. Nothing paged
> anyone. This is filed both as the live incident and as the systemic gap that let it go unnoticed for 11 days.

## What already exists (don't rebuild this)

- Terraform: `deployment-service/terraform/gcp/lifecycle_catalogue_scheduler.tf` —
  `google_cloud_scheduler_job.lifecycle_catalogue_regen_daily["cefi"]` (cron `0 1 * * *`) runs
  `build_instrument_catalogue.py --asset-group cefi` (incremental); a weekly full self-heal
  (`lifecycle_catalogue_full_weekly["cefi"]`, `0 3 * * 6`) runs the same script `--mode full`.
- `promote_catalogue()` (`instruments-service/scripts/build_instrument_catalogue.py:1571-1636`) calls
  `evaluate_monotonic_guard()` (line 1584) **unconditionally** on every run, both daily and weekly — this already blocks
  a catalogue promotion whose total row count shrinks vs. the current canonical catalogue.
- The user's "fold the check into the daily job instead of a slow CI gate" instinct is already how this half works —
  there is no separate CI gate to replace; the check already lives inside the production scheduled script.

## What's actually missing — zero alerting, on either mechanism

- On rejection, `build_instrument_catalogue.py:1594-1611` calls `_emit_event("CATALOGUE_SHRINK_BLOCKED", ...)`, which
  (`_emit_event`, line 234-237) is a **"best-effort structured event log"** — plain `logger.info`, Cloud Logging only.
  It does not call UTL's `log_event()`, does not write to the GCS event-log path
  (`events/instruments-service/{date}/events.jsonl`), does not call alerting-service, Slack, or PagerDuty.
- Grepped `alerting-service` for `instruments-service` / `catalogue` / `drawdown` / `monotonic`: zero matches to
  `CATALOGUE_SHRINK_BLOCKED` or `evaluate_monotonic_guard`. The only catalogue-adjacent alert is
  `alerting-service/alerting_service/notifiers/data_pipeline_slack.py:93-99`'s `DP_CATALOG_NOT_RUNNING` — a
  **different**, staleness-based signal (the artifact hasn't refreshed within budget), wired end-to-end via a real UTL
  event constant → a UAC `_dp_rule("DP-CATALOG-001", ..., CRITICAL, PAGE_OPERATOR)` → alerting-service's Slack /
  PagerDuty notifiers. **No equivalent event constant or rule exists for a shrink/monotonic-guard trip.**
- The standalone report script `instruments-service/scripts/cefi_cumulative_drawdown_guard_2026_06_27.py` is a plain
  read-only CLI (`print()` only) with no scheduler entry anywhere (`.tf`/`.yml` grep across the workspace: zero hits).
  Its own header says
  `# Delete-when: superseded by a CLI subcommand once the cumulative-drawdown guard is wired into the catalogue build / QG`
  — the codebase's own comment says this is not yet wired in.
- A shrink-blocked exit code today produces: (a) one Cloud Logging error line, (b) a FAILED Cloud Run Job execution
  visible only if someone runs `gcloud run jobs executions list`, (c) one scheduler retry. Nothing pages, pings Slack,
  or reaches a human by default. No `google_monitoring_alert_policy` exists on the `lifecycle-catalogue-regen-*` jobs.

## The live incident this blind spot let through (found running the script for real, 2026-07-07)

Ran `instruments-service/.venv/bin/python scripts/cefi_cumulative_drawdown_guard_2026_06_27.py` against production GCS
(`instruments-store-cefi-prd-central-element-323112/_index/availability_index.parquet`) via GCP ADC. Real output, all 29
CeFi venues, 64,096 captured cells:

- **Catalogue-wide: 5,621 total day-over-day drop-days; 1,007 cross the thin-day-collapse threshold (<50% of trailing
  14-day median).** The script's default stdout truncates to the top 40 rows by collapse severity and never prints its
  own computed `total_thin` — so this number is invisible unless you re-derive it, as this audit did. Most of the 1,007
  are historical and since recovered (DERIBIT 2020-2022, BYBIT early-2026 — both current as of 2026-07-07).
- **LIGHTER and PACIFICA are dark right now.** Both had rock-steady flat-line counts for their entire history (LIGHTER
  198-213, PACIFICA 10), then each shows exactly one partial capture immediately before going silent — LIGHTER 213→18
  (~8.5% of median), PACIFICA 10→4 (~40% of median) — and **zero rows of any capture status since 2026-06-26** (11 days
  as of this filing). A partial capture immediately followed by total silence is the classic signature of an adapter
  breaking mid-fetch, not a deliberate venue pause.
- **ASTER itself has no active collapse** by this guard's definition — 119 day-over-day drops, worst single drop -279
  (332→53, 2023-08-13→14), zero thin-day collapses, cumulative-ever-seen monotonic (never decreases, currently 53→499).
  The repeated small drops read as periodic perp-contract roll-offs, not capture failures. Filed here only for
  completeness — no action needed on ASTER from this specific guard.
- **Residual worth reconciling separately, not part of this issue's scope:** this guard's cell-presence view says ASTER
  has 0 missing dates (1,082 consecutive days, 2023-07-22→2026-07-07), while the live turbo API says 11 missing / 1,071
  expected for the same venue and window — two counting methods disagreeing by 11 days. Tracked as a Stage-3 checklist
  item on the tracker, not duplicated here.

## Todos

- [x] [SCRIPT] P0. Diagnose LIGHTER and PACIFICA's adapters — both went silent 2026-06-26 after a partial capture.
      **RESOLVED 2026-07-10, real diagnosis + real fix — see Progress Log.** Two findings, not one: (1) the "dark venue"
      framing was a stale artifact of a venue-key rename — `git log` confirms commit `2f7d4548` ("reclassify
      EXTENDED/PACIFICA/LIGHTER on-chain perp CLOBs defi->cefi") migrated these 3 venues onto new canonical keys
      `LIGHTER-ZKSYNC`/`PACIFICA-SOLANA`/`EXTENDED-STARKNET` around 2026-06-25/26; a live GCS read (2026-07-10) confirms
      the NEW keys have had **continuous, unbroken daily captures through 2026-07-09** (LIGHTER-ZKSYNC 215 instruments,
      PACIFICA-SOLANA 10, EXTENDED-STARKNET 101 — all current). The bare `LIGHTER`/`PACIFICA` keys correctly stop at the
      rename date; there is no live outage under the venues' real current identity. (2) The OOM IS real and was
      confirmed independently: `uts-prod-instruments-service-cefi-t1-recon` failed **100% of its daily runs for 11
      straight days** (2026-06-27 through 2026-07-10 — 3 days `exit(1)`, then OOM every day from 06-30),
      timing-correlated with the same 06-25 reclassification growing the CEFI corpus without a resource bump. Real fix
      applied + verified: `gcloud run jobs update ... --cpu=4 --memory=8Gi` still failed (exit 1, not OOM — the
      container just needed more room); `--cpu=8 --memory=16Gi` **completed successfully in 1m2.14s**
      (`uts-prod-instruments-service-cefi-t1-recon-jt7w8`, matches the same OOM-at-4/8Gi-fixed-at-16Gi pattern already
      documented for `lifecycle_catalogue_scheduler.tf`'s tradfi rollup job — Deribit alone parses ~333K raw instruments
      in memory before filtering). Also confirmed: this job was **never Terraform-managed** (created ad hoc via `gcloud`
      2026-06-23, redeployed only by `unified-trading-sa`'s image-push `ReplaceJob` calls — unlike its
      `mtds_cefi_t1_recon_job` sibling) — fixed for real via new `module     "instruments_cefi_t1_recon_job"` + import
      block in `deployment-service` (see Progress Log; `tofu apply` still pending to make Terraform authoritative).
      Separately confirmed (not fixed, flagged): this job's application-level stdout/stderr **never reaches Cloud
      Logging for any execution** (only the 2-line Cloud Run system/audit events) — a real observability gap that
      blocked root-causing the intermediate `exit(1)` failure mode from logs alone; a local repro via the real
      `python -m instruments_service` entrypoint was needed instead (see Progress Log).
- [x] [SCRIPT] P0. ~~Once fixed, backfill the 2026-06-26 → fix-date gap~~ **NOT NEEDED — corrected finding.** Per the
      item above, `LIGHTER-ZKSYNC`/`PACIFICA-SOLANA`/`EXTENDED-STARKNET` (the venues' real current canonical keys) have
      zero gap — continuous captures through 2026-07-09. The bare pre-rename keys' history correctly stops at the
      reclassification date; that is the expected shape of a clean venue-key migration, not an unexplained hole
      requiring an `EXPECTED_*` stamp.
- [x] [CODE] P1. Wired the drawdown-guard's `total_thin` counter into stdout (was computed, never printed) and dropped
      the top-40 truncation on both the drop-rows and thin-rows tables — full catalogue-wide detail now prints
      unconditionally. `instruments-service/scripts/cefi_cumulative_drawdown_guard_2026_06_27.py`.
- [x] [CODE] P1. Built the alerting path, mirroring the proven `DP_CATALOG_NOT_RUNNING` / `DP-CATALOG-001` pattern
      exactly:
  - [x] Added `CATALOGUE_SHRINK_BLOCKED` event constant to
        `unified-trading-library/unified_trading_library/events/event_types.py` (+ `events/__init__.py` exports).
  - [x] Added `DP-CATALOG-002` (`_dp_rule(..., CRITICAL, PAGE_OPERATOR)`) to
        `unified-api-contracts/unified_api_contracts/canonical/crosscutting/alerting/rules.py`, and its
        human-SSOT-mirror entry in `codex/05-infrastructure/data-pipeline-alerts.registry.yaml`.
  - [x] Swapped `build_instrument_catalogue.py`'s `_emit_event` call at the `CATALOGUE_SHRINK_BLOCKED` site to real
        `unified_trading_library.log_event(..., severity="CRITICAL")`, with
        `setup_events(mode="batch",     sink=GcsEventSink(...))` wired once in `main()` (the sole real CLI entry point —
        tests call `run_rollup()`/`promote_catalogue()` directly and never reach it, so no test-suite risk).
  - [x] Added a `CATALOGUE_SHRINK_BLOCKED` notifier entry to
        `alerting-service/alerting_service/notifiers/     data_pipeline_slack.py` (explanation + remediation text) + 3
        new Slack fields (`new_count`/`current_count`/ `hint`) — auto-wired end-to-end since the router/subscriber
        iterate `DATA_PIPELINE_ALERT_RULES` generically (no hardcoded event allowlist found).
- [x] [INFRA] P2. Scheduled `cefi_cumulative_drawdown_guard_2026_06_27.py` for real recurring execution — new
      `deployment-service/terraform/gcp/cefi_drawdown_guard_scheduler.tf` (Cloud Run Job, 1cpu/2Gi, + Cloud Scheduler
      `0 7 * * *` UTC, mirroring `honest_coverage_scheduler.tf`'s module+http_target pattern). **RESOLVED 2026-07-10 —
      `tofu apply` run for real, scoped + verified.** Terraform code was committed earlier today (`4dd8d53`) but never
      applied; ran a SCOPED `tofu apply` (init against the real prod backend — `terraform/state/prod`, project
      `central-element-323112` — targeting only `module.instruments_cefi_t1_recon_job` +
      `module.cefi_drawdown_guard_job` + `google_cloud_scheduler_job.cefi_drawdown_guard_daily`, explicitly avoiding the
      unrelated dirty `cf_manifest_audit_scheduler.tf` files per this todo's own caveat). Plan: 1 import (adopts the
      already-live OOM-fixed `uts-prod-instruments-service-cefi-t1-recon` job, converging Terraform to the real
      8cpu/16Gi spec — confirmed post-apply via `gcloud run jobs describe` still shows 8cpu/16Gi, no revert), 1 in-place
      update (labels + args-list-form normalize, matching every other job in this file), 2 creates (the new
      drawdown-guard Cloud Run Job + its Cloud Scheduler). Post-apply `tofu plan` on the same 3 targets shows **"No
      changes" (zero drift)**. Live-verified beyond the apply: manually executed the new job
      (`gcloud run jobs execute uts-prod-cefi-drawdown-guard-daily --wait`) — real production run
      `uts-prod-cefi-drawdown-guard-daily-p47fs` **completed successfully in 43.99s**.
      `gcloud scheduler jobs describe     uts-prod-cefi-drawdown-guard-daily` confirms `state=ENABLED`,
      `schedule=0 7 * * *`.
- [x] [CODE] P2. Cross-cutting: extract DeFi's `_enforce_defi_monotonicity`
      (`instruments_service/engine/orchestrator/defi.py:119-156,187-225`) into an asset-group-parameterized shared
      helper in `venue_core.py`, called from the shared `process_fetch.py:169-179` chokepoint, scoped to CEFI/TRADFI
      (DeFi keeps its existing bespoke caller; Sports/Prediction don't get this, their manifest grain isn't
      venue-count-shaped). **RESOLVED 2026-07-10 — `instruments-service@0db619d5`.** Re-checked liveness immediately
      before editing (per this todo's own instruction): `defi.py` mtime was 17,967s old, `venue_core.py` 7,530s old —
      both long past the 120s threshold, `git status` showed neither dirty. Implemented:
      `venue_core._get_manifest_high_watermarks(asset_group)` +
      `venue_core._enforce_monotonicity(records, hwm, *,     block_on_regression, min_ratio)` — the generalized,
      asset-group-parameterized pair. `defi.py`'s `_get_defi_manifest_high_watermarks()` /
      `_enforce_defi_monotonicity()` now thin-wrap these (`block_on_regression=True, min_ratio=1.0` — DeFi's exact
      original strict policy, unchanged; existing DeFi tests pass unmodified). `process_fetch.py`'s shared non-DeFi
      branch (the real "always fetch fresh" chokepoint every CEFI/TRADFI capture run — batch AND live, not gated by mode
      like DeFi's own check) now calls the generalized helper per-asset-group with
      `block_on_regression=False, min_ratio=_CEFI_TRADFI_THIN_COLLAPSE_RATIO` (0.5 — same thin-day-collapse ratio as
      `cefi_cumulative_drawdown_guard_2026_06_27.py`, so "collapse" means the same thing everywhere in this codebase) —
      **detect-only, never blocks the write**, per this todo's own caveat that CeFi delistings / TradFi expiries are
      legitimate today's-active-count decreases unlike DeFi's immutable-contract invariant. New tests (all passing):
      `TestEnforceMonotonicityGeneralized` + `TestGetManifestHighWatermarksGeneralized` (unit-level parameterization
      checks, incl. a delisting-tolerance case and a DeFi-policy-parity case) plus one `process_instruments`-level
      integration test (`test_cefi_venue_collapse_is_detected_but_not_blocked`) proving a LIGHTER-ZKSYNC-shaped 213→1
      collapse is logged at ERROR but the record is still written. `quality-gates.sh --no-fix` green (sentinel matched
      HEAD). Shipped via **direct push carve-out (dirty-deps)** — `unified-trading-library` (`post_trade/settler.py`,
      `cf_manifest_audit.py`) and `unified-api-contracts` (`test_cme_options_universe.py`,
      `tradfi_instrument_universe.py`) both had live-then-stale uncommitted changes from a concurrent sibling session
      blocking quickmerge's pre-flight dep-cleanliness audit; per workspace policy this is a documented carve-out
      (WARN-only `check_strict_quickmerge.py`, confirmed non-blocking) rather than committing unrelated/unverified
      foreign code on their behalf.

## Progress Log

- **2026-07-10 (session 2) — both remaining tails closed for real; issue fully resolved.** Re-verified every material
  claim in the earlier 2026-07-10 entry against live code/commits/infra myself before touching anything (all checked out
  — `CATALOGUE_SHRINK_BLOCKED` alerting chain end-to-end, the dark-venue rename diagnosis re-confirmed live against GCS
  today showing `LIGHTER-ZKSYNC`/`PACIFICA-SOLANA`/`EXTENDED-STARKNET` current through 2026-07-10, the OOM fix live at
  8cpu/16Gi). Then executed the two concrete next steps:
  1. **Terraform activation** — scoped `tofu apply` (real prod backend, 3 targeted resources, zero drift on post-apply
     plan) + a live `gcloud run jobs execute --wait` smoke test of the new drawdown-guard job (43.99s, success). See the
     Todos section above for full command/evidence detail.
  2. **Todo 6 (DeFi-monotonicity-helper generalization)** — re-checked file liveness immediately before editing (both
     `defi.py`/`venue_core.py` long past the 120s threshold, git-clean), implemented the asset-group-parameterized
     shared helper (`venue_core._enforce_monotonicity` / `_get_manifest_high_watermarks`), wired a non-blocking
     CeFi/TradFi thin-collapse detector into `process_fetch.py`'s shared chokepoint, added unit + integration tests, ran
     `quality-gates.sh --no-fix` green, and shipped via a **direct-push dirty-deps carve-out**
     (`instruments-service@0db619d5`) after `unified-trading-library`/`unified-api-contracts` had unrelated
     live-then-stale uncommitted WIP blocking quickmerge's pre-flight audit (waited ~150s for the sibling session's
     edits to go stale before concluding it was safe to treat as a genuine dirty-deps block, not a live conflict on
     files I was editing).
  - **Repos touched this session**: `instruments-service` (`0db619d5`), `deployment-service` (terraform apply only — no
    new commit, the `.tf` code was already committed as `4dd8d53` in the earlier session), `unified-trading-pm` (this
    doc).
  - Both todos in this doc are now `[x]` — no open items remain.

- **2026-07-10 — full resolution, all real evidence against production GCP/GCS.** Real ADC admin access used throughout;
  no destructive ops.
  - **Root cause confirmed (2 distinct findings, not 1)**:
    1. **"Dark venue" claim was a stale rename artifact, not a live outage.**
       `git log --since=2026-06-24 --until=2026-06-27 -- instruments_service/` surfaced commit `2f7d4548`: "fix(defi):
       reclassify EXTENDED/PACIFICA/LIGHTER on-chain perp CLOBs defi->cefi capture path" (2026-06-25). A read-only GCS
       check (`_index/availability_index.parquet` in `instruments-store-cefi-prd-central-element-323112`) shows: bare
       `LIGHTER`/`PACIFICA` keys stop 2026-06-26 (as originally diagnosed); but `LIGHTER-ZKSYNC` (215 instruments),
       `PACIFICA-SOLANA` (10), `EXTENDED-STARKNET` (101) all show **unbroken daily captures through 2026-07-09**
       (yesterday relative to this fix). Every other real cefi venue (BYBIT, DERIBIT, OKX-SWAP/SPOT/ FUTURES,
       KRAKEN-SPOT/FUTURES, HYPERLIQUID, COINBASE-SPOT/FUTURES/CDE, BITGET/BITFINEX/BINANCE-\*, UPBIT, ASTER) is also
       current through 2026-07-09; only the already-known-legacy bare `OKX`/`COINBASE` keys are stale (since 2026-03-02,
       unrelated pre-existing issue, not part of this incident).
    2. **The OOM is real, independently confirmed, and now fixed.** `gcloud run jobs executions list` for
       `uts-prod-instruments-service-cefi-t1-recon` shows **100% daily failure for 11 straight days**: 2026-06-27
       through 06-29 = `exit(1)` "container exited with an error"; 06-30 through 07-10 = explicit "The configured memory
       limit was reached" (signal 9). `gcloud logging read ... Jobs.ReplaceJob` shows 3 automated redeploys by
       `unified-trading-sa` on 06-26/06-27 (image-push-triggered, resources unchanged at 2cpu/4Gi both before and after)
       — timing-consistent with the same 06-25 reclassification commit growing the CEFI corpus (3 more venues) without a
       resource bump.
  - **Real fix applied + verified with a live execution, not just read**:
    `gcloud run jobs update uts-prod-instruments-service-cefi-t1-recon --region=asia-northeast1 --cpu=4 --memory=8Gi` →
    manual `gcloud run jobs execute --wait` still **failed** (`exit(1)`, not OOM this time — ran ~3min vs. the usual
    ~2min, further but not far enough). Bumped again: `--cpu=8 --memory=16Gi` → `gcloud run jobs execute --wait` →
    **`uts-prod-instruments-service-cefi-t1-recon-jt7w8` completed successfully in 1m2.14s.** This matches an
    already-documented precedent in this exact workspace — `lifecycle_catalogue_scheduler.tf`'s comment on the tradfi
    rollup job: `memory = each.value.memory # ... tradfi 16Gi — OOM'd at 4Gi+8Gi`. A local repro
    (`python -m instruments_service --operation=instruments --mode=batch --asset-group=CEFI --run-tag=t1-recon`, the
    real Docker `ENTRYPOINT`) showed the likely memory driver: Deribit alone parses `API /exchanges` into ~333K raw
    instruments in memory before filtering down to ~3,250 MVP-scoped rows.
  - **Real, additional, confirmed infra-hygiene finding**: `uts-prod-instruments-service-cefi-t1-recon` was **never
    Terraform-managed** — `run.googleapis.com/creator: ikenna@odum-research.com` (created via raw `gcloud` 2026-06-23),
    redeployed only by `unified-trading-sa`'s `Jobs.ReplaceJob` calls (a CI image-push side-effect). Confirmed absent
    from `_imports_reconcile.tf` / `audit03_cron_provisioning.tf` — unlike its `market-tick-data-service-cefi-t1-recon`
    sibling, which IS Terraform-managed (`module "mtds_cefi_t1_recon_job"`, 4cpu/8Gi). **Fixed for real**: added
    `module "instruments_cefi_t1_recon_job"` (8cpu/16Gi, matching the verified-working live spec) to
    `deployment-service/terraform/gcp/ audit03_cron_provisioning.tf` + an adopting `import` block in
    `_imports_reconcile.tf`, so a future `tofu apply` converges to zero drift instead of silently reverting the fix.
    **`tofu apply` not yet run this session** (pending, same class as other tracked `tofu apply` items in this
    workspace).
  - **Real, additional, confirmed observability gap (flagged, not fixed — out of this task's scope)**: this job's
    application-level stdout/stderr **never reaches Cloud Logging for any execution** — confirmed across 3 separate
    executions (2026-06-27 OOM, 2026-07-10 06:00 OOM, 2026-07-10 manual `exit(1)` test): `gcloud logging read` with
    every `resource.type`/`logName` combination tried returns only the 2 Cloud Run system/audit-log lines
    (`Container terminated on signal 9` / `Container called exit(1)`), zero application log lines, despite
    `PYTHONUNBUFFERED=1` already being set. This blocked root-causing the `exit(1)` failure mode from Cloud Logging
    alone — the only way to see real progress was a local repro against the real Docker entrypoint
    (`python -m instruments_service`, not `python -m instruments_service.cli.main` — the latter silently no-ops, exit 0,
    ~0 real work, because it bypasses `main_service_cli`'s `ServiceBootstrap`). The local repro's real run (against real
    production GCS, `env=dev` label but real `GCP_PROJECT_ID=central-element-323112` target) completed cleanly: "Shard
    completeness OK: 24/24 venues written for date=2026-07-10", 12,150 records, confirming the application code itself
    is healthy — the failures are purely a resource-envelope problem. Worth a follow-up issue doc on the Cloud Logging
    gap itself (why gen2 Cloud Run Jobs on this specific job produce zero app-log output) — not filed separately here as
    it's adjacent-but-outside this issue's scope.
  - **Todos 3-5 (total_thin stdout, alerting path, scheduler) shipped as originally scoped** — see Todos section above
    for the per-file breakdown. Todo 6 (generalize DeFi's monotonicity helper) deferred — live-file conflict with a
    concurrent parallel session actively editing the exact 2 files it touches (`defi.py`, `venue_core.py`).
  - **Repos touched this session**: `instruments-service` (drawdown-guard stdout fix, `build_instrument_catalogue.py`
    event wiring), `unified-trading-library` (event constant), `unified-api-contracts` (DP-CATALOG-002 rule),
    `alerting-service` (notifier entry), `deployment-service` (2 new/modified terraform files — OOM-fix IaC adoption +
    new drawdown-guard scheduler), `unified-trading-pm` (this doc + the registry yaml mirror).

- **2026-07-07 (partial diagnosis — deprioritized mid-investigation, operator redirect)** — Ruled out: LIGHTER's
  exchange API is up and healthy (direct `curl` to `mainnet.zklighter.elliot.ai` returns real market data); PACIFICA's
  adapter is a static curated list with zero network dependency and cannot fail on the exchange side. Ran both adapters'
  `get_instruments()` + UAC `validate_instrument_records()` locally against today's date — both produce clean,
  fully-valid output right now (PACIFICA 10/10 valid), so the Python code itself is not currently broken for either
  venue. **Found a real, currently-active, separate problem**: the daily Cloud Run Job
  `uts-prod-instruments-service-cefi-t1-recon` (the actual CeFi capture job, `--asset-group=CEFI`, 2cpu/4Gi) has been
  OOM-killing (`"The configured memory limit was reached"`, signal 9) on at least 2026-07-05, -06, -07 — timing that
  lines up with 2026-06-25's reclassification commit (`2f7d4548`) adding 3 more venues (LIGHTER-ZKSYNC, PACIFICA-SOLANA,
  EXTENDED-STARKNET) to the same CEFI batch without raising the container's resource limits. 2026-06-26 (the actual
  outage start) itself shows `"Execution completed successfully"` in the Cloud Run audit log, and 2026-06-27 shows a
  different failure (`"container exited with an error"`, exit code 1) — so the OOM pattern is NOT yet confirmed as the
  day-1 cause, only as a real problem that is CURRENTLY ongoing (last 3 days). Could not find zero-arg application
  stdout/stderr for ANY of these executions (only Cloud Run's own audit/system-event log lines) to see per-venue
  progress, and could not locate the Terraform/IaC resource that pins this job's 2cpu/4Gi limit (searched
  `t1_batch_scheduler.tf`, `cloud_run_job_registry.py`, `_imports_reconcile.tf`, the `container-job` module,
  `terraform/services/instruments-service/gcp/terraform.tfvars` — none is a confirmed match; the job may be
  unmanaged/ad-hoc-`gcloud`-created, which is itself worth flagging). Stopped here on operator redirect (session
  priority shifted to the deployment-api/deployment-ui drilldown work) — **not fixed, evidence preserved below for
  whoever picks this back up.**
- **2026-07-07** — Filed from the ASTER/CEFI instrument-service data-status audit, after the operator asked to actually
  run the manual guard script rather than only read its code. Read-only investigation + one real (safe, read-only)
  execution against production GCS; no files edited, no writes to any bucket.
