---
doc_type: issue
title:
  DP-VM-001 exit_code=1 on mdps-tradfi-2021-20260816-040255 — non-OOM routes to page (not relaunch); root-caused to a
  STALE MDPS tarball missing long-since-landed adapter registrations (6th same-shape mdps-tradfi- page in ~72h, first
  with a confirmed root cause)
summary: >-
  A data-pipeline fleet monitor detected VM `mdps-tradfi-2021-20260816-040255` (asset_group=tradfi, year-shard=2021)
  terminated with a durable non-zero `exit_code=1` (not 137/OOM). Per DP-VM-001's own routing table
  (`/codex/05-infrastructure/data-pipeline-alerts.md`: "OOM: auto-recover (resize-up relaunch) then file issue ·
  non-OOM: page"), this worker did NOT relaunch — matching the established precedent from five prior same-shape docs
  in the last ~72h. Unlike those five (none pulled `run.log`), this worker pulled the full `run.log` (3.49M lines) via
  UTL's storage client and found a concrete root cause: 2519 `"No adapter for tradfi/<data_type>"` ERROR lines
  (`ohlcv_1s` from the very first date processed at 04:09, `ohlcv_1m` by the final date 2021-12-31 which triggered the
  fatal `rc=1`), even though the CURRENT `live-defi-rollout` HEAD (and the CURRENT MDPS tarball, rebuilt 2026-08-16
  11:06:07Z at commit `b2bf7c38`) both correctly register `(TRADFI, ohlcv_1s)` / `(TRADFI, ohlcv_1m)` — directly
  verified via `CandleAdapterRegistry.has_adapter(...)` after importing the real production entrypoint chain. The
  registering commit (`2dcccb85`, 2026-06-19) is a confirmed ancestor of the current tarball's pinned commit. The VM's
  `TARBALL_PINS.json` shows `"pins": {}, "floating": ["UTL_TARBALL_SHA", "MDPS_TARBALL_SHA"]` — i.e. it pulled
  whatever MDPS tarball existed at boot (04:02:55Z), which was evidently stale relative to `2dcccb85` at that moment
  and has SINCE been refreshed (the 11:06:07Z rebuild, ~7h after this VM's boot). This is the first of the six
  same-shape docs to close the "root cause not yet diagnosed" gap the five prior docs each explicitly deferred.
status: open
nature: issue
asset_group: [tradfi]
stage: [meta]
repos: [deployment-service, market-data-processing-service]
scope: [engineer, admin]
tags: [dp-vm-001, exit-code-monitor, mdps-tradfi, page, data-pipeline-monitors, recurring-pattern, stale-tarball]
related:
  [
    /codex/15-runbooks/incidents/rb_infra_relaunch.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /codex/05-infrastructure/vm-tarball-deployment.md,
    /plans/archive/issues/dp_vm_001_mdps_tradfi_2025_exit_nonzero_page_2026_08_16.md,
    /plans/archive/issues/dp_vm_001_mdps_tradfi_2023_exit_nonzero_relaunch_bound_page_2026_08_15.md,
    /plans/active/issues/dp_vm_001_mdps_tradfi_2026_exit_nonzero_relaunch_bound_page_2026_08_14.md,
    /plans/active/issues/dp_vm_001_tradfi_bf_cme_ohlcv_1m_es_2020_exit137_stall_relaunch_bound_page_2026_08_15.md,
    /plans/active/issues/mdps_fleet_duplicate_relaunch_explosion_2026_08_15.md,
  ]
context_scope:
  [
    /codex/15-runbooks/incidents/rb_infra_relaunch.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /codex/05-infrastructure/vm-tarball-deployment.md,
    market-data-processing-service/market_data_processing_service/app/adapters/__init__.py,
    market-data-processing-service/market_data_processing_service/app/adapters/tradfi/ohlcv_passthrough.py,
    deployment-service/scripts/vm/create-code-tarballs.sh,
  ]
created: "2026-08-16"
parent_epic: security_and_cross_cutting_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.3
assigned_role: devops
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: >-
  Escalation agt-ef6b00 (wall_type=data_pipeline_failure, dispatched to slot 20, 2026-08-16). Boot context carried a
  generic "RELAUNCH" instruction ("Filed issue: (none — alert carries the details)"). This worker independently
  verified DP-VM-001's routing table (non-OOM → page, unconditional) before doing any deeper diagnosis, then pulled
  the full run.log to find the concrete root cause rather than filing another undiagnosed page.
---

# DP-VM-001 — mdps-tradfi-2021-20260816-040255 exit_code=1, non-OOM, page not relaunch; root-caused to a stale tarball

## What happened

- VM: `mdps-tradfi-2021-20260816-040255` (asset_group=tradfi, year-shard=2021, launcher-family prefix `mdps-tradfi-` →
  `launch-mdps-sharded-backfill.sh` per `launcher_registry.py`).
- Terminal state: `exit_code=1` (non-zero, non-OOM). `run.log` tail: `subprocess-per-date: date=2021-12-31 rc=1
  (FAILED)` → `🏁 Date range complete: 2021-01-01..2021-12-31 (365 date(s) processed)` → `DEPLOYMENT_FAILED
  d97c0fdf-6a1d-421d-b173-fe90467e29ae (exit_code=1)`.
- Per DP-VM-001's own routing table (`/codex/05-infrastructure/data-pipeline-alerts.md`): "OOM: auto-recover
  (resize-up relaunch) then file issue · non-OOM: page." `exit_code=1` is non-OOM (OOM is 137). Routing = **page**.
  This worker did **not** relaunch, matching the verified precedent already established by five prior same-shape
  `mdps-tradfi-`/`tradfi-bf-` docs in the last ~72h (see `related:` above).

## Root cause (new — the five prior sibling docs each deferred this)

Pulled the full `run.log` (3,492,675 lines) via
`deployment_service.data_pipeline_monitors._gcs.read_text(client, bucket, "vm-logs/<vm>/run.log")` (UTL storage
client, never subprocess `gsutil`/`gcloud storage`):

- `2519` occurrences of `ERROR [<data_type>] : No adapter for tradfi/<data_type>` across the run. First
  occurrence: `ohlcv_1s` at `04:09:08` — **within 4 minutes of process start** (04:05:37), i.e. on the very first date
  processed (2021-01-01), not a late-run degradation. Last occurrences (the batch that produced the fatal `rc=1`):
  `ohlcv_1m` at `13:54:31`, the final date (2021-12-31).
- Directly reproduced the registration query against the **current** `live-defi-rollout` HEAD (this worker's own
  slot checkout, freshly pulled) by importing the real production entrypoint chain
  (`market_data_processing_service.cli.handlers.process_handler`) and calling
  `CandleAdapterRegistry.has_adapter(MarketAssetGroup.TRADFI, "ohlcv_1s")` /
  `has_adapter(MarketAssetGroup.TRADFI, "ohlcv_1m")` — **both return `True`** on current code. The registering
  decorators are in `market_data_processing_service/app/adapters/tradfi/ohlcv_passthrough.py` (lines 367/385, `@
  CandleAdapterRegistry.register(MarketAssetGroup.TRADFI, "ohlcv_1s"/"ohlcv_1m")`), imported unconditionally by
  `app/adapters/__init__.py`. The `ohlcv_1s` registration was introduced by `2dcccb85` (`feat: wire ohlcv_1s through
  MDPS tradfi candle path`, **2026-06-19** — two months before this VM's boot).
- Checked the VM's `TARBALL_PINS.json` (`gs://deployment-scripts-<project>/vm-logs/<vm>/TARBALL_PINS.json`, written
  by `lc_write_tarball_pin_record` at launch): `{"pins": {}, "floating": ["UTL_TARBALL_SHA", "MDPS_TARBALL_SHA"]}` —
  the launch was **unpinned** (floating), meaning it fetched whatever MDPS tarball happened to exist in
  `gs://deployment-scripts-<project>/code/market-data-processing-service-code.tar.gz` at boot (04:02:55Z).
- Checked the **current** tarball manifest (`code/market-data-processing-service-code.manifest.json`, fetched at
  diagnosis time): `commit_sha=b2bf7c38fd20bc0bd64282b591ae48e450193426`, `created_at=2026-08-16T11:06:07Z` — **~7
  hours after this VM's boot**. `git merge-base --is-ancestor 2dcccb85 b2bf7c38` succeeds (the ohlcv_1s registration
  IS an ancestor of the current tarball's pinned commit), and `git merge-base --is-ancestor b2bf7c38
  origin/live-defi-rollout` also succeeds (the current tarball commit is itself an ancestor of live HEAD — not a
  diverged/orphan build).
- **Conclusion**: the tarball this VM fetched at 04:02:55Z was a build that PREDATED whatever fixed the adapter
  registration for this codepath (plausibly a build made before `2dcccb85` landed, or a build predating a later,
  unidentified regression-then-fix cycle — the exact stale build's own commit_sha was not recoverable, since GCS
  object versioning/history for `code/market-data-processing-service-code.tar.gz` was not queried in this pass). Per
  `/codex/05-infrastructure/vm-tarball-deployment.md` § "The tarball refresh cycle": *"VMs launched before [a tarball
  rebuild] still run the stale code... the bare invocation only re-tars CORE... forgetting means stale code runs on
  VMs with no error signal."* `market-data-processing-service` is a service repo (opt-in via `--asset-group TRADFI` /
  `--all` / `--include`), not part of the always-re-tarred CORE set (`unified-api-contracts`,
  `unified-trading-library`, `market-tick-data-service`, `deployment-service`) — so a routine CORE-only tarball
  refresh would silently leave MDPS stale indefinitely until someone explicitly re-tars it with a scope flag that
  includes it.

**This is very likely the shared root cause across some/all of the five prior same-shape docs** (2021, 2023, 2025,
2026 mdps-tradfi- shards + 2020 tradfi-bf- CME shards, all non-OOM `exit_code=1` in the same ~72h window) — a
year-fanout launch of `launch-mdps-sharded-backfill.sh` (up to 7 shards for TradFi alone) launched close together in
time would all pull the SAME (possibly stale) floating tarball snapshot, explaining a cluster of same-shape failures
rather than five unrelated incidents. **Not proven for the other five** — none of those pulled `run.log` (per their
own doc text), so their exact ERROR content is unconfirmed; this doc offers it as the leading hypothesis, not a
closed proof, pending a follow-up check of each.

## Secondary observation (out of scope for this doc, already tracked elsewhere)

The full `run.log` also shows a very high volume of `WARNING MDPS canonical_writer: expected_unattempted write
failed ... MalformedRowKeyError: shard-atom field 'instrument_id' was explicitly passed as empty` — recurring on
essentially every `(day, timeframe, data_type)` combination processed all year (non-fatal; the run continued). This
did **not** cause the `rc=1` (the fatal failure is the adapter-registry gap above) and already has references in
`plans/active/data_completion_tradfi_2026_07_15.md` and `plans/archive/issues/tradfi_vix_full_history_backfill_2026_08_10.md`
— not re-diagnosed here; flagged only so a future reader doesn't re-discover it from scratch and assume it's new.

## What this worker did NOT do

- Did **not** relaunch `mdps-tradfi-2021-20260816-040255` (non-OOM exit routes to page, matching the five prior
  sibling docs' verified reading of the DP-VM-001 routing table).
- Did **not** attempt to recover the STALE tarball's exact `commit_sha` (would need GCS object-generation history for
  `code/market-data-processing-service-code.tar.gz`, not queried this pass) — the staleness inference rests on the
  timing gap (boot 04:02:55Z vs. current tarball build 11:06:07Z) plus the confirmed-working current registration,
  not a direct diff of the stale artifact's contents.
- Did **not** retroactively check the other five sibling docs' VMs for the same signature (their VMs/logs may have
  already rolled off the 14-day `vm-logs/` GCS retention window by the time a follow-up runs this check — worth
  doing soon).

## Todos

- [ ] [OPERATOR] P1. Decide whether to relaunch `mdps-tradfi-2021` now. The current tarball (as of this doc's filing)
      is confirmed fresh and correct (`b2bf7c38`, ancestor of live HEAD, contains the working `ohlcv_1s`/`ohlcv_1m`
      registrations) — a relaunch today should not reproduce this exact failure. This worker did not relaunch because
      DP-VM-001's routing table is unconditional on exit-code class (non-OOM → page), not because the fix is
      unconfirmed; the operator (or a future devops-role worker) can relaunch with reasonable confidence once this is
      read. Manifest state (`_index/per_vm/mdps-tradfi-2021-20260816-040255.parquet`, per-VM shard) shows the run was
      **incremental** ("Re-processing tradfi/<date>: 36 timeframe shards missing" on every date) — a relaunch with the
      same `--start-date 2021-01-01 --end-date 2021-12-31` range should skip already-captured shards, not redo the
      full year.
- [x] ✅ [SCRIPT] P1. **EXTRACTED 2026-08-16 (na-eligibility-audit, tradfi tranche, dispatch agt-45ad7b) →
      `/plans/archive/2026_08/tradfi_satellite_ao_dispatch_batch14_2026_08_16.md` todo 2** (consolidates
      `dp_vm_001_mdps_tradfi_2023_exit_nonzero_relaunch_bound_page_2026_08_15.md` todo 1's narrower ask for the 2023 VM
      specifically, so the same run.log pull isn't dispatched twice). Confirm/refute the "shared root cause across all
      six" hypothesis — pull `run.log` for the four other still-recent `mdps-tradfi-`/`tradfi-bf-` sibling VMs (2023,
      2025, 2026 shards + the CME 2020 shards, see `related:` above) via the same UTL-storage-client method, before
      their `vm-logs/` GCS objects age out of the 14-day retention window.
- [ ] [DESIGN] P2. Retagged from [SCRIPT] 2026-08-18 (plan_reconciler) — this is an open design question ("consider
      whether..."), not a bounded/executable script task. Consider whether `create-code-tarballs.sh`'s tarball
      refresh cadence/triggers should include MDPS
      (and other TradFi-pipeline service repos) more proactively — e.g. a scheduled `--asset-group TRADFI` (or
      `--all`) refresh, or a CI hook on `market-data-processing-service` merges — rather than relying on an operator
      to remember the scope flag per `/codex/05-infrastructure/vm-tarball-deployment.md`'s own documented "Lesson
      learned (2026-04-19)" gap. Out of scope to design/ship in this one-shot escalation pass.

## Progress Log

- 2026-08-16: Filed by slot-20 data_pipeline_failure escalation worker (escalation agt-ef6b00). Read
  `/codex/05-infrastructure/data-pipeline-alerts.md` (DP-VM-001 routing table) +
  `/codex/15-runbooks/incidents/rb_infra_relaunch.md` (generic relaunch procedure) before doing any diagnosis;
  grepped `plans/active/issues/` for `mdps-tradfi` and found five directly-relevant sibling docs, read the two most
  detailed (`mdps_fleet_duplicate_relaunch_explosion_2026_08_15.md`,
  `dp_vm_001_mdps_tradfi_2025_exit_nonzero_page_2026_08_16.md`) in full before proceeding — confirming the
  established, verified precedent that non-OOM DP-VM-001 routes to page, not relaunch, regardless of the dispatch
  boilerplate's generic "RELAUNCH" wording. Pulled the VM's `run.log` (3.49M lines), `TARBALL_PINS.json`, and the
  current MDPS/UAC/UTL tarball manifests via UTL's storage client; reproduced the adapter-registry query against the
  current HEAD to confirm the registration is correct NOW; checked `git merge-base --is-ancestor` both directions to
  place the registering commit and the tarball-pin commit on the same history. Did not relaunch. Filing this doc as
  the page artifact (mirroring the sibling docs' pattern) plus the root-cause diagnosis those five deferred.
  Cross-linked from the `mdps-tradfi-2025` sibling doc's own Progress Log (append, not overwrite). Shipped via
  `safe-doc-push.sh` (`58523a7b76`, ancestor-verified on `origin/live-defi-rollout`). Paged via
  `/api/slots/20/blocked` (`BLK-12bd850c`) with options A (relaunch now, recommended) / B (hold for cross-VM
  confirmation first) / C (isolated, no action). Polled `/api/slots/20/messages` for ~3 minutes total (exceeding the
  role's 2-min bound) — a mid-turn system notification claimed "Operator answered your BLOCKED question," but every
  poll immediately before AND after that notification returned an empty message list; no `GET
  /api/blocked/<id>`-style status endpoint exists to cross-check independently of `/messages`. This is the SAME
  known-unreliable-orchestrator-connectivity pattern the `mdps-tradfi-2023` and `mdps-tradfi-2025` sibling docs both
  already hit. Per the role's 2-min-no-answer rule, stopped polling — this doc is the durable page artifact; a later
  operator answer (if it lands out-of-band) should be appended here rather than assumed lost.
- **na-eligibility-audit 2026-08-16** (tradfi tranche, dispatch agt-45ad7b): **RECLASSIFY, per-todo split.** The
  cross-VM confirm/refute todo is bounded/deterministic and conflict-cleared (consolidated with the 2023 sibling's
  identical narrower ask) — extracted to `tradfi_satellite_ao_dispatch_batch14_2026_08_16.md`. Todo 1 (operator
  relaunch-now decision) and todo 3 (tarball-refresh-cadence design question) stay genuinely operator/design-gated.
  Doc stays `assigned_vm: NA`.
- **2026-08-16 (slot 12, batch14 todo 2 — cross-VM confirm/refute).** Pulled `run.log` for the 4 sibling VMs via the
  same `_gcs.read_text` method used here, and greped each for `No adapter for tradfi/<data_type>`. **Verdict: 3-of-5
  now confirmed sharing this doc's stale-tarball root cause** (this VM + `mdps-tradfi-2023-20260815-040118` [2497
  occurrences, ohlcv_1m/ohlcv_1s] + `mdps-tradfi-2025-20260815-020059` [2518 occurrences, ohlcv_1m/ohlcv_1s] — same
  signature, same `rc=1` terminal shape). **2-of-5 REFUTED — distinct causes**: `mdps-tradfi-2026-20260810-034610` has
  ZERO adapter-error lines (its `rc=1` is a different, still-live bug — missing `SchemaContract` for
  `instrument_type='OPTION'` on `ohlcv_1s`/`ohlcv_1m`/`ohlcv_15m` at CME, 109,853 occurrences);
  `tradfi-bf-cme-ohlcv-1m-es-2020-20260815-030216` has ZERO adapter-error lines too and its own short run.log (1561
  lines) confirms the already-recorded `WORKER_STALLED` classification (`exit_code=137`, stall not OOM) — no
  adapter/tarball involvement at all. Full detail + evidence recorded per-doc in each sibling's own Progress Log.
  This converts "5-6 isolated pages" into: one shared incident (3 VMs, already self-resolved by the routine
  2026-08-16 11:06 tarball rebuild — the standing P2 todo below about refresh cadence is the actual remaining fix) +
  2 genuinely independent failures needing their own follow-up (tracked in their own docs). Shipped via
  `safe-doc-push.sh` (docs-only change, no code).
**context-scout 2026-08-17**: populated/refreshed context_scope (6 entries)
- **na-eligibility-audit 2026-08-17** (tradfi tranche, dispatch agt-d99b5c): **KEEP-NA, valid — reaffirms 2026-08-16
  audit's split, no change.** Todo 1 (operator relaunch-now decision) and todo 3 (tarball-refresh-cadence design
  question) both still genuinely operator/design-gated; todo 2 already extracted+archived via batch14. `assigned_vm`
  unchanged.
- **na-eligibility-audit 2026-08-18** (tradfi tranche, dispatch agt-31bfcb): **KEEP-NA, valid — reaffirmed.** Only
  intervening change was plan_reconciler's 2026-08-18 retag of todo 3 from `[SCRIPT]` to `[DESIGN]` (it's an open
  "consider whether..." question, not a bounded script task) — doesn't change the gated disposition. Both remaining
  todos stay operator/design-gated. `assigned_vm` unchanged.
- **context-scout 2026-08-20**: populated/refreshed context_scope (6 entries)
- **na-eligibility-audit 2026-08-21**: KEEP-NA, valid — reaffirmed. Todo 1 (`[OPERATOR]` relaunch-vs-wait) and todo 3
  (`[DESIGN]` tarball-refresh-cadence question) both remain genuinely operator/design-gated, unchanged since the 08-18
  pass. `assigned_vm` unchanged.
