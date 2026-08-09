---
doc_type: plan
title:
  Prediction satellite AO batch 9 — bounded-item extraction from the RECLASSIFY sweep's 2 whole-doc-ineligible
  prediction docs (2026-08-09)
summary: >-
  Satellite-batch extraction mirroring /ag-closeout-audit's pattern, produced from a targeted read of the 2 prediction
  plan docs a same-day RECLASSIFY sweep found did NOT qualify for a whole-doc `assigned_vm` flip.
  prediction_consolidated_closeout_2026_07_18.md is a 0-native-todo coordination hub (archive_exempt, by design) with
  zero extractable items. prediction_cross_venue_arb_and_coverage_2026_07_24.md yielded 2 conflict-clear items — a
  Kalshi historical-backfill build whose prerequisite gate (batch4's own todo #1, POLYMARKET instrument-lifecycle
  bounds) shipped 2026-08-07, and a now-safe operational `--apply` run whose blocking script bug was already fixed.
  Conflict-checked against prediction_satellite_ao_dispatch_batch4/6/7/8 (all active/complete) — zero collisions.
status: active
nature: process
asset_group: [prediction]
stage: [data]
repos: [instruments-service, market-tick-data-service, e2e-testing, unified-trading-pm]
scope: [engineer]
tags: [prediction, ao-dispatch, satellite-extraction, batch-9, orphan-extraction]
related:
  [
    /plans/active/prediction_cross_venue_arb_and_coverage_2026_07_24.md,
    /plans/active/prediction_consolidated_closeout_2026_07_18.md,
    /plans/active/prediction_satellite_ao_dispatch_batch8_2026_08_08.md,
    /plans/active/prediction_satellite_ao_dispatch_batch9_2026_08_09_finalize.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-09"
parent_epic: predictions_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.2
locked_by:
locked_since:
supersedes:
superseded_by:
context_scope:
  [
    /plans/active/prediction_cross_venue_arb_and_coverage_2026_07_24.md,
    /codex/04-architecture/prediction-batch-live.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    market-tick-data-service/market_tick_data_service/scripts/rebuild_prediction_manifest.py,
  ]
depends_on: []
source: >-
  Targeted satellite-batch extraction (2026-08-09), scoped to the 18-doc list a same-day RECLASSIFY sweep flagged as NOT
  whole-doc-flip-eligible (14 defi + 2 tradfi + 2 prediction). Both prediction candidates read end to end; extractable
  items conflict-checked against every active/recently-drafted prediction satellite batch (4, 6, 7, 8).
assigned_role: data_engineering
effort: high
sequential: false
drift_direction: advance-code
---

# Prediction satellite AO batch 9 — 2026-08-09

Only 2 items qualified, both from `prediction_cross_venue_arb_and_coverage_2026_07_24.md`.
`prediction_consolidated_closeout_2026_07_18.md` is a coordination hub (`archive_exempt: true`,
`gate_on_depends: false`, 0 native todos by its own frontmatter and design — it only aggregates 4 forked-out Phase A-E
child plans, none of which are in this run's 18-doc scope) and contributed nothing to extract.

## Todos

- [x] [SCRIPT] P1. **Build the series-scoped `/historical/*` Kalshi enumeration to close the 2025-10→2026-04 Kalshi
      trades mid-gap.** ✅ — `instruments-service@3f2ddca0` + `e2e-testing@5e2f90e`. The deep-corpus seed (Jon-Becker
      free Parquet) already covers 2021-06-30→~2025-09, and the recent-window live backfill covers the last ~60 days —
      the 2025-10→2026-04 mid-gap is the precise, bounded residual. Both prerequisites this todo needs are already
      shipped: the IS cutoff-aware date routing (`instruments-service@8b118d9`, live `/markets` vs `/historical/markets`
      by `/historical/cutoff`) and the RSA-PSS auth for the `/historical/*` tier. Built: `KalshiReferenceDataAdapter`
      gained `enumerate_all_series` (unfiltered `GET /series`, ~11k series — the tractable enumeration unit, flat
      market-pagination is infeasible at this scale) / `fetch_series_markets_in_window` (per-series
      `/markets?status=closed`, client-filtered by close_time) / `fetch_historical_trades` (RSA-PSS-signed
      `/historical/trades`, cursor-paginated) / `enumerate_historical_gap_markets` (orchestrator), all shard-isolated +
      429-retried per the existing live series-scoped pattern (7 new unit tests, `instruments-service` QG green). Driver
      `e2e-testing/scripts/prediction/kalshi_historical_gap_backfill.py` wires series→markets→trades→write via the
      standard `record_captured_from_counts`/`record_failed` honest-absence contract, matching the already-established
      canonical schema (`trade_id`/`count`/`yes_price`/`no_price`/`taker_side`/`created_time`/`ticker`/
      `canonical_question_group`/`available_at`) and the exact `pipeline_mode=batch_kalshi`/`source=kalshi` bundle shape
      `ingest_kalshi_bulk_to_canonical.py` already emits (byte-shape-identical, source-blind downstream). The gate this
      todo was originally parked behind — POLYMARKET instrument-lifecycle bounds landing first, so the backfill emits
      honest lifecycle-bounded cells — shipped 2026-08-07 (`instruments-service@3617261f`, confirmed via
      `prediction_cross_venue_arb_and_coverage_2026_07_24.md`'s own finalize-reconciled Progress Log entry). Repos:
      e2e-testing (driver) + instruments-service (series enumerator). Source:
      `prediction_cross_venue_arb_and_coverage_2026_07_24.md` ("series-scoped historical backfill" todo, 2026-06-23
      section). **Scope note**: this todo's own "done when" (a manifest read confirming real captured rows across the
      full window) requires an actual ~11k-series production run — VM-scale heavy I/O per
      `/codex/05-infrastructure/vm-launcher-runbook.md`, out of a single dispatched-task session's scope (build the code
      vs. run the campaign are different bounded units). The dispatched task's own `done_definition` was "checkbox
      flipped in plan + code shipped" — satisfied. The production run + manifest verification is tracked as a fresh
      follow-up todo below, not silently folded into this one.
- [x] ✅ [SCRIPT] P1. **Run the now-safe `--apply --venue KALSHI` operational re-walk for cqg batch re-classification.**
      The blocking script bug is already fixed (`market-tick-data-service@24db3f16` — `rebuild_prediction_manifest.py`
      now threads `venue` into `compute_object_atom` and routes `classify_kalshi_to_canonical_group(ticker=cid)` for
      KALSHI vs the tuple path for POLYMARKET, with 2 regression tests + the venue-aware routing verified against real
      tickers, e.g. `KXCPI→CPI_PRINT_PER_MONTH`, `KXMLBGAME→SPORTS_MLB_MATCH`). The run itself remains: (1) a dry-run
      over the dates where Kalshi TICK parquets actually exist (a 2026-05-01..03 sample previously showed `objects:0` —
      find the real seeded-date range first), (2) confirm the dry-run reclassifies to real cqg groups (non-OTHER), (3)
      `--apply` (local or VM, ~5000s at the doc's own prior-measured scale). Re-reads existing tick parquets only — NOT
      a tick migration, no GCS object mutation. Repo: market-tick-data-service. Source:
      `prediction_cross_venue_arb_and_coverage_2026_07_24.md` ("cqg partition-completeness — BATCH re-classification
      re-walk" todo, 2026-06-23 section). Done when: the `--apply` run completes with a dry-run-confirmed non-OTHER cqg
      distribution for the reclassified KALSHI dates, and the doc's own note about the 116,192 `SOURCE_RETURNED_ZERO`
      rows lacking `available_from/to` (which stay `empty_confirmed`, unresolvable by this re-walk alone) is preserved
      as a distinct residual, not silently folded into "done". **DONE 2026-08-09.** Evidence: apply VM
      `mtds-prediction-kalshi-cqg-rewalk-20260809-101228` (n2-standard-8, SPOT, asia-northeast1-c) completed cleanly —
      `[vm-exec] command exited rc=0`, `DEPLOYMENT_COMPLETED ... (exit_code=0)`, self-deleted per
      `VM_SHUTDOWN_ON_COMPLETION=true`. Full run: `run_id=20260809T101545Z-cc1caa66`, `elapsed_s=17536.0` (~4.87hr,
      launch ~10:12 UTC → completion 15:08:01 UTC), all 63 chunks (2021-06-30..2026-08-08) with
      `unparseable/failed_unclassified/failed_zero_row: 0` on every chunk (chunk 61 alone had 5 `failed_envelope` — a
      tiny residual, ~0.0002% of the run's 3,169,427 total objects, not blocking). Step (2)'s non-OTHER confirmation was
      already satisfied by the beta-preview dry-run VM (`mtds-prediction-kalshi-cqg-beta-preview-20260809-091716`, 41+
      real KALSHI cqg groups, only 2.5% OTHER) — corroborated by this apply run's `failed_unclassified: 0` across every
      one of the 63 production chunks (a misclassification-to-OTHER regression would show as nonzero here). **Residual
      update**: live `availability_index.parquet` spot-check (`venue=='KALSHI'`) shows 229,320 rows with
      `capture_status=empty_confirmed` + `error_reason=SOURCE_RETURNED_ZERO` — grown from the cited 116,192 because that
      figure was a narrower-scope pre-apply probe (~2025-05-01..2026-06-24 per
      `archive/2026_08/prediction_cross_venue_arb_and_coverage_history_2026_08.md:620`), while this apply run's real
      scope is the full 2021-06-30..2026-08-08 corpus (adds ~4 earlier years + the newer 2026-06-23..2026-08-08 live
      window). This is expected growth from broader coverage, not a regression — all 229,320 rows remain correctly
      `empty_confirmed` (not reclassified, not folded into "done"), tied to the SAME P0 lifecycle-gap (P0 43d, KALSHI
      markets lacking `available_from/to`) this todo's own scope explicitly excludes. Verification script + raw output
      preserved this session (scratchpad, not promoted — regenerable via `pandas.read_parquet` against the live manifest
      path, one-line query).
- [ ] [OPS] P2. **Run the Kalshi historical mid-gap backfill campaign on a VM + manifest-verify closure.** Follow-up to
      the now-shipped series-scoped enumeration (todo 1 above) — that todo built the code; this todo runs it at
      production scale. Launch
      `e2e-testing/scripts/prediction/kalshi_historical_gap_backfill.py --start 2025-10-01     --end 2026-04-21` on a
      dedicated VM per `/codex/05-infrastructure/vm-launcher-runbook.md` (register via `VM_PREFIX_TO_BUCKET`, default
      SPOT, verify STARTED + ongoing progress + a terminal state — no fire-and-forget; ~11k series × throttled
      per-series fetch, expect hours). Before the full run, smoke-test with `--limit-series 5     --dry-run` to confirm
      the live Kalshi API response shapes (`/series`, `/markets?status=closed`, `/historical/trades`) match this todo's
      mocked-response assumptions — the adapter code was built + unit-tested against the documented/inferred Kalshi
      schema without a live credentialed call in the dev sandbox; if a real response shape differs, fix the adapter
      parsing before the full run, don't launch blind. Requires `kalshi-api-credentials` (Secret Manager) for the
      `/historical/*` signed tier — if inaccessible from the VM's identity, record the credential gap and self-grant per
      `/codex/05-infrastructure/orchestrator-cloud-identity-self-service.md` (do not pause). Done when: a manifest read
      confirms real `captured`/`empty_confirmed` rows for KALSHI trades across the full 2025-10→2026-04 window (the
      todo-1 script's own "done when"), closing the previously-empty mid-gap — cite the manifest read + VM
      run/completion evidence in the checkbox flip. **NOT satisfied by the 2026-08-09 production run** (see Progress Log
      below) — the run itself completed cleanly but the manifest shows 0 `captured` + 0 `empty_confirmed` rows; stays
      unchecked pending todo 4 below.
- [ ] [SCRIPT] P1. **Fix `kalshi_historical_gap_backfill.py`'s silent-drop-on-empty gap, then re-run the campaign.** The
      2026-08-09 production run (`mtds-prediction-kalshihistgap-20260809-164319`, `elapsed_s=6514.7` / ~1.81hr,
      `DEPLOYMENT_COMPLETED exit_code=0`) enumerated all 12,574 series and found 2,658 markets closing in the
      2025-10→2026-04 window, but a manifest read of the per-VM shard it wrote
      (`gs://market-data-tick-pred-prd-central-element-323112/_index/per_vm/mtds-prediction-kalshihistgap-20260809-164319.parquet`)
      shows **only 3 rows total, all `capture_status=attempted_failed` / `error_reason=ClassifierConfidenceLow`** — 0
      `captured`, 0 `empty_confirmed`. Root cause, confirmed by direct API probes during this session: the other
      2,655/2,658 markets genuinely returned `200 {"cursor":"","trades":[]}` (verified honest, not a fetch failure —
      only 7 `ADAPTER_FETCH_FAILED` events fired across the whole run) but `run()`'s `if annotated.empty: continue`
      (kalshi_historical_gap_backfill.py) silently drops them with **zero manifest footprint** — no `record_empty` call
      at all, so the manifest can't distinguish "checked, confirmed empty" from "never checked" (a real breach of the
      honest-absence discipline, `/codex/02-data/honest-absence-downstream-handling.md`). The 3 markets that DID have
      trades were then legitimately-but-unhelpfully classified `OTHER` by `classify_kalshi_to_canonical_group` (a real,
      honest classifier gap for niche tickers like `KXATPMATCH-…`/`KXNCAAFGAME-…`/`KXNBAMENTION-…` — not itself a bug,
      `classify_kalshi_to_canonical_group` is documented non-Optional with `OTHER` as a legitimate catch-all) and routed
      to `record_failed`, so even the rare real trades never landed as `captured`. Fix requires TWO changes: (1)
      instruments-service `KalshiReferenceDataAdapter.fetch_historical_trades` currently returns a bare `list[dict]`
      with no HTTP-status/ response-received signal — it must additionally surface enough to build a
      `unified_api_contracts.FetchEvidence` (`http_status`, `response_received`, `rows_in_response=0`,
      `error_signal=""`) so the driver can prove `SOURCE_RETURNED_ZERO` honest absence per `record_empty`'s own gate
      (raises `UnprovenHonestAbsenceError` without it — checked directly against the writer source this session, not
      assumed); (2) `kalshi_historical_gap_backfill.py`'s `run()` must call
      `writer.record_empty(row_key={date: <market close date>, venue: KALSHI, ...}, reason="SOURCE_RETURNED_ZERO",     fetch_evidence=…, pipeline_mode=PipelineMode.BATCH_KALSHI)`
      for every market whose `fetch_and_annotate_market` returns empty, instead of silently `continue`-ing. After
      shipping the fix, RE-RUN the full campaign (mirrors todo 3's own launcher:
      `deployment-service/scripts/vm/launch-prediction-kalshi-historical-gap-backfill-vm.sh`, already fleet-hardened
      this session — see the two infra fixes below). Done when: a fresh manifest read shows `captured` rows for the
      (likely few) real-trade markets AND `empty_confirmed` rows (not silent absence) for the confirmed-empty majority,
      covering the full 2025-10→2026-04 window — THEN todo 3 above can be checked off citing both this fix's SHA and the
      re-run's manifest evidence.

## Not extracted this batch — items that stay behind

- `prediction_consolidated_closeout_2026_07_18.md` — `archive_exempt: true`, `gate_on_depends: false`, 0 native todos by
  design (a coordination hub referencing 4 forked-out Phase A-E child plans, none of which are in this run's 18-doc
  scope). Nothing to extract.
- `prediction_cross_venue_arb_and_coverage_2026_07_24.md`'s `[OPS] P2` tarball-overwrite race item — a design choice
  ("consider SHA-pinned tarball fetch... or a build-lock") not yet resolved to one approach; also already flagged by
  `prediction_satellite_ao_dispatch_batch4_2026_07_26.md`'s own Deferred section as belonging to the `infra`/`ci`
  tranche's closeout, not prediction's. Stays behind.
- `prediction_cross_venue_arb_and_coverage_2026_07_24.md`'s `[DESIGN] P1` fixture-pairing residual (team-name
  canonicaliser) — already claimed verbatim by the ACTIVE `prediction_satellite_ao_dispatch_batch6_2026_07_29.md`'s own
  `[DATA] P2` "team-name alias tables" todo — conflict, not re-drafted.

## Progress Log

- 2026-08-09 (targeted satellite-batch extraction, RECLASSIFY-sweep follow-up): drafted alongside its finalize twin. 2
  conflict-clear todos extracted from `prediction_cross_venue_arb_and_coverage_2026_07_24.md`; the sibling
  consolidated-closeout doc contributed zero (0-native-todo hub by design). Both extracted items were previously
  time-gated/blocked in `prediction_satellite_ao_dispatch_batch4_2026_07_26.md`'s own Deferred section on prerequisites
  that have since shipped (verified via the source doc's own finalize-reconciled Progress Log, not assumed) —
  conflict-check against batch4/6/7/8 found zero collisions on the 2 extracted items themselves.
- 2026-08-09 (todo 1 shipped): `instruments-service@3f2ddca0` adds
  `enumerate_all_series`/`fetch_series_markets_in_window`/`fetch_historical_trades`/`enumerate_historical_gap_markets`
  to `KalshiReferenceDataAdapter` (7 new unit tests, QG green); `e2e-testing@5e2f90e` adds the
  `kalshi_historical_gap_backfill.py` driver wiring series→markets→trades→canonical-write (QG green). Both verified
  ancestors of `origin/live-defi-rollout`. Added a fresh follow-up todo (P2 OPS) for the actual VM-scale production run
  - manifest verification — the code build and the production campaign are different bounded units; this todo's own
    code-ship scope is complete, the campaign is tracked separately, not silently folded in.
- 2026-08-09 (todo 2 IN PROGRESS — slot 26): probed GCS to find the real Kalshi tick-parquet date windows (per todo 2's
  own step (1)): deep-corpus seed **2021-06-30 → 2025-11-25** (`pipeline_mode=batch_kalshi`) + recent/live window
  **2026-06-23 → today** (`batch_kalshi`/`live_kalshi`); confirmed empty gap 2025-11-26..2026-06-22 (matches the
  2025-10→2026-04 mid-gap todo 1 targets, plus a few extra empty weeks either side). **Local-host attempt FAILED
  repeatedly** (4 separate SIGTERM kills — unwrapped, 6G-capped, 10G-capped, foreground-with-590s-timeout — all died at
  the SAME point: right after the CF-11 honest-absence reemit loads the full ~2.68M-row consolidated `_index` and starts
  its `iterrows()` pass; root cause is genuine shared-host memory pressure, not a script bug or Bash-tool timeout — the
  planning-vm was running ~26 concurrent agent slots at 12-28GB/30GB used during these attempts). **Resolution: built a
  dedicated one-off VM launcher** `deployment-service/scripts/vm/launch-prediction-kalshi-cqg-rewalk-vm.sh` (Pattern A /
  `VM_TASK=canonical-migration`, mirrors `launch-cefi-mvp-reclassify-vm.sh`) and ran the operation on GCE instead
  (matches `/codex/05-infrastructure/vm-launcher-runbook.md`'s "genuinely corpus-scale → dedicated VM" guidance). Two
  VMs confirmed the dry-run step cleanly: `mtds-prediction-kalshi-cqg-beta-preview-20260809-091716` (small window
  2026-08-01..08, `--beta-manifest-out`, completed in 1529s/exit 0) — direct inspection of the projected parquet shows
  **41+ real KALSHI cqg groups, only 8/323 (2.5%) OTHER** (`BTC_UP_DOWN_DAILY`, `CPI_PRINT_PER_MONTH`,
  `SPORTS_MLB_MATCH`, `FED_RATE_DECISION_PER_FOMC`, etc. all present) — confirming the venue-aware classifier fix works
  at real production scale, satisfying step (2). A second VM (`mtds-prediction-kalshi-cqg-rewalk-20260809-090742`, full
  range 2021-06-30..2026-08-08, `--chunk-days 30`) ran as extra full-corpus validation — reached chunk 44+/~62 with
  `failed_unclassified: 0` on every single chunk before this progress note was written (still running independently; not
  required for step (2), which was already satisfied by the beta-preview VM). **Production `--apply` VM launched**:
  `mtds-prediction-kalshi-cqg-rewalk-20260809-101228` (n2-standard-8, SPOT, same full range + `--chunk-days 30`, no
  `--dry-run`) — in progress as of this note, ETA ~45-90 min based on the dry-run's observed chunk rate. **Also found +
  fixed as a side effect** (not a plan-scope bug, just this slot's stale venv state): `market-tick-data-service/.venv`
  had corrupted `pycryptodome`/`rlp` installs (missing `__init__.py`/leftover `.tmp*` dirs) and `deployment-service` had
  no `.venv` at all — both fixed via `uv sync --frozen [--reinstall]`; unrelated to this task's code, purely local
  environment drift. **Remaining before this todo can be checked off**: confirm `--apply` VM completes cleanly,
  spot-verify the LIVE `availability_index.parquet` (not just the beta-preview projection) shows non-OTHER KALSHI cqg
  for the reclassified dates, then flip this checkbox with both VM names + elapsed times as evidence — the 116,192
  `SOURCE_RETURNED_ZERO` residual (lacking `available_from/to`) stays `empty_confirmed`/unresolved by design, per this
  todo's own "done when" clause — not to be silently folded into "done".
- 2026-08-09 (todo 2 SHIPPED — slot 26): apply VM `mtds-prediction-kalshi-cqg-rewalk-20260809-101228` completed cleanly
  after ~4.87hr (`elapsed_s=17536.0`, launch ~10:12 UTC → `DEPLOYMENT_COMPLETED exit_code=0` at 15:08:01 UTC,
  self-deleted per `VM_SHUTDOWN_ON_COMPLETION=true`). All 63 chunks (2021-06-30..2026-08-08) processed with
  `unparseable/failed_unclassified/failed_zero_row: 0` throughout (chunk 61 alone: 5 `failed_envelope`, ~0.0002% of the
  3,169,427 total objects — a tiny non-blocking residual). The parallel full-corpus dry-run validation VM
  (`mtds-prediction-kalshi-cqg-rewalk-20260809-090742`, referenced in the prior note as still running) also completed
  cleanly during this monitoring window: `rc=0`, all 63 chunks, zero real errors — independent corroboration the
  reclassification logic is sound across the entire corpus. **cqg non-OTHER confirmation**: satisfied via the
  beta-preview dry-run (41+ real groups, 2.5% OTHER, already recorded above) + this apply run's `failed_unclassified: 0`
  on every one of 63 chunks (a misclassification-to-OTHER regression would surface here). **Residual reconciliation**
  (the step this note exists to get right): live `availability_index.parquet` spot-check (`pandas.read_parquet` against
  `gs://market-data-tick-pred-prd-central-element-323112/_index/availability_index.parquet`, filtered `venue=='KALSHI'`)
  shows 416,240 KALSHI rows total — 151,791 `captured`, 247,783 `empty_confirmed` (of which 229,320 carry
  `error_reason=SOURCE_RETURNED_ZERO`), 15,670 `attempted_failed`, 996 `expected_unattempted`. The 229,320
  SOURCE_RETURNED_ZERO count is UP from the previously-cited 116,192 — traced this to the 116,192 figure being a
  narrower pre-apply probe scoped to roughly `2025-05-01..2026-06-24`
  (`archive/2026_08/prediction_cross_venue_arb_and_coverage_history_2026_08.md:620`), while this apply run's real scope
  is the full `2021-06-30..2026-08-08` corpus — a wider range that necessarily surfaces more lifecycle-bound-less KALSHI
  markets. This is expected growth from broader date coverage, NOT a regression or a cqg-classification defect —
  confirmed by cross-checking that `availability_index.parquet` has no `cqg`/`canonical_question_group` column at all
  (the per-chunk `captured_bundles`/`captured_cells` counters carry that classification, not this manifest; the 0
  `failed_unclassified` count across all chunks is the correct proxy). All 229,320 rows remain correctly
  `empty_confirmed` — not reclassified into a cqg group, not silently folded into "done" — because they lack
  `available_from/to` lifecycle bounds, the SAME P0 lifecycle-gap (P0 43d) this todo's own scope explicitly excludes
  ("unresolvable by this re-walk alone"). Verification scripts + raw pandas output kept in this session's scratchpad
  only (not promoted — trivially regenerable, one `pandas.read_parquet` + `value_counts()` call against the live
  manifest). Checkbox flipped this commit.
- 2026-08-09 (todo 3 attempted — slot 28): local bounded smoke test (`--limit-series 5` then `300`, `--dry-run`) against
  the LIVE Kalshi API confirmed `/series`, `/markets?status=closed`, `/historical/trades` all return correctly-shaped
  200 responses with valid RSA-PSS auth (`kalshi-api-credentials` — `uts-prd-sa` already carries project-level
  `secretmanager.secretAccessor`, no credential gap); the 300-series sample found 33 real in-window markets, proving
  discovery works — no adapter fix needed (todo 3's own pre-flight step). Built a new one-off launcher
  `deployment-service/scripts/vm/launch-prediction-kalshi-historical-gap-backfill-vm.sh` (Pattern A, compound
  `VM_SERVICE=market_tick_data_service+instruments_service+chaos-drill` to stage all 3 needed tarballs,
  direct-script-path invocation to sidestep an mtds-vs-e2e-testing `scripts/` package-name collision under `-m`). **3 VM
  launch attempts, 2 real shared-infra bugs found + fixed along the way** (both scoped fixes, not workarounds): (1)
  attempts 1-2 failed identically at `uv pip install` (`e2e-testing`'s pyproject declares
  `execution-service`/`strategy-service` as hard deps, unresolvable via `--no-sources` when those tarballs aren't
  staged) — `setup-data-pipeline-vm.sh`'s NODEPS routing only covered `strategy-paper`/`strategy-live`/`defi-paper`/
  `synthetic-benchmark`, never `canonical-migration` with a narrower compound `VM_SERVICE`; fixed by routing
  `e2e-testing` to NODEPS whenever its sibling dirs are genuinely absent, VM_TASK-agnostic
  (`deployment-service@fe20aed8c`). (2) The fix's own republish then got silently clobbered by a concurrent agent's own
  launcher run before this launcher's VM booted (`gcloud storage objects describe` showed the OLD content re- written
  seconds after this session's own republish) — live-reproduced, dated confirmation of the shared-fleet race
  `vm_launcher_setup_script_freshness_gap_2026_07_31.md` already tracked but couldn't previously confirm (Progress Log
  entry added there); fixed in this launcher by calling
  `LC_SETUP_SCRIPT_FRESHNESS=auto lc_verify_setup_script_freshness` directly (not via `lc_gcloud_create`, which lacks
  SPOT support) immediately before `gcloud compute instances create`, narrowing the race window
  (`deployment-service@b57336dd1`). 3rd attempt (`mtds-prediction-kalshihistgap-20260809-164319`) booted clean and ran
  to completion: `DEPLOYMENT_COMPLETED exit_code=0`, `elapsed_s=6514.7` (~1.81hr), all 12,574 series enumerated, 2,658
  markets found in-window. **Manifest verification then surfaced a real, separate correctness gap** (not an infra issue)
  — see the new todo 4 above for the full root-cause + fix spec: the campaign's own per-VM manifest shard shows 0
  captured + 0 empty_confirmed rows (only 3 `attempted_failed`/`ClassifierConfidenceLow` rows), because
  `kalshi_historical_gap_ backfill.py` silently drops (no manifest row at all) every market whose trades fetch honestly
  returned empty (2,655/2,658 of them) instead of recording `empty_confirmed` — todo 3's own "done when"
  (captured/empty_confirmed rows proving the window is honestly covered) is genuinely NOT met by this run despite the
  clean `exit_code=0`. Todo 3 stays UNCHECKED. Filed as todo 4 (P1) rather than a separate issue doc since it's a
  direct, narrowly-scoped continuation of this exact todo's own script, not a cross-cutting finding.
