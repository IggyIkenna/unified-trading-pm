---
doc_type: issue
title:
  mtds_chunk_loop.sh / cefi_coverage_chunk_loop.sh's `HAD_FAILURE`/`PROGRESS.json` checkpoint gates only on
  whole-subprocess exit code, not per-payload success — a chunk that loses most of its days to a transient guard (e.g.
  manifest-consolidator staleness) can still report `CHUNK_RC=0` and silently advance the monotonic checkpoint past a
  real, uncaptured gap
summary: >-
  Discovered while closing `tradfi_backfill_oom_remediation_2026_06_24.md`'s "watch the relaunch to completion" todo.
  `tradfi-bf-cme-ohlcv-1m-g01-es-es-2020-20260731-134654` ran all 53/53 date chunks and self-deleted cleanly
  (`EXIT_STATUS=0`), but from chunk 25/53 onward (2026-07-31T16:08:12Z, when the in-run tradfi manifest-consolidator
  staleness guard started firing) most chunks silently lost the majority of their days' payloads — weekly chunks that
  normally report `Batch complete: 7 results collected` dropped to 2-5/7 for ~28 consecutive chunks (only the very last
  chunk, which hit 0/7, also flipped the subprocess exit code non-zero and got logged as `CHUNK_FAILED`). Because
  `mtds_chunk_loop.sh`'s `HAD_FAILURE` flag (and the `PROGRESS.json` monotonic checkpoint it gates) only look at the
  per-chunk subprocess `CHUNK_RC`, not at how many of that chunk's payloads actually succeeded, the checkpoint kept
  advancing right through the lossy chunks and ended at `last_completed_date: 2020-12-22` — reading as "the year is
  essentially done" when roughly a third of it (≈2020-06-17 through 2020-12-29) most likely never got real data. The
  same gating pattern is mirrored verbatim in `cefi_coverage_chunk_loop.sh`.
status: resolved # (was: open) 2026-08-03 -- both todos done, doc archived per the 6-step ritual
nature: issue
asset_group: [tradfi, cefi, meta]
stage: [data]
repos: [deployment-service, market-tick-data-service]
scope: [engineer, admin]
tags:
  [
    tradfi,
    cefi,
    backfill,
    manifest,
    consolidator,
    staleness,
    silent-partial-failure,
    progress-checkpoint,
    data-correctness,
    honest-absence,
  ]
related:
  [
    /plans/active/issues/tradfi_backfill_oom_remediation_2026_06_24.md,
    /plans/archive/2026_08/tradfi_ohlcv_backfill_oom_preflight_fails_paused_consolidator_2026_08_02.md,
    /plans/active/mtds_available_at_cross_asset_backfill_2026_07_13.md,
    /plans/active/issues/mtds_backfill_vm_memory_hang_large_chunk_2026_07_22.md,
  ]
created: 2026-08-03
parent_epic: tradfi_master
priority: P2
source:
  [
    "gs://deployment-scripts-central-element-323112/vm-logs/tradfi-bf-cme-ohlcv-1m-g01-es-es-2020-20260731-134654/{EXIT_STATUS,PROGRESS.json,run.log}",
    "deployment-service/scripts/vm/setup-data-pipeline-vm.sh:1740-1800 (mtds_chunk_loop.sh generation) and :~1820-1880
    (cefi_coverage_chunk_loop.sh generation)",
    "gcloud scheduler jobs describe uts-prod-manifest-consolidator-market-data-tradfi-cron --location=asia-northeast1
    (state: ENABLED, verified 2026-08-03T19:33Z)",
  ]
assigned_vm: planning
resolved_by:
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
context_scope:
  [
    deployment-service/scripts/vm/setup-data-pipeline-vm.sh,
    /codex/05-infrastructure/vm-launcher-runbook.md,
    /codex/02-data/honest-absence-downstream-handling.md,
    /plans/active/issues/tradfi_backfill_oom_remediation_2026_06_24.md,
  ]
---

> **✅ ARCHIVED 2026-08-03 — both todos done, no lock.** Todo 1 (the `HAD_FAILURE`/checkpoint gating fix in both
> generated chunk-loop scripts) shipped `deployment-service@5478a92`; todo 2 (spot-check the CME ES/MES 2020 gap dates)
> confirmed all 5 sampled dates genuinely `captured` via a direct manifest query — the wave-launcher's routine
> skip-if-fresh cadence self-healed the gap as this doc's own "Why it matters" section anticipated. No targeted relaunch
> needed. See Progress Log for both closures.

## What I found

While closing `tradfi_backfill_oom_remediation_2026_06_24.md`'s final todo ("watch the 2026-07-31T13:46Z relaunch of
`tradfi-bf-cme-ohlcv-1m-g01-es-es-2020-20260731-134654` to completion"), I read the VM's durable GCS logs
(`vm-logs/<vm>/{EXIT_STATUS,PROGRESS.json,run.log}`; the VM itself long since self-deleted). It did **not**
false-stall-kill — good news, confirms the P1 watchdog fix (`deployment-service@3c71176`+`470159e`) holds — but a
full-log trace (not just the tail) surfaced a distinct, real problem:

- Chunks 1-24 (2020-01-01 through 2020-06-16) completed normally: `Batch complete: 7 results collected` every time, real
  `StreamingParquetWriter: uploaded ...` lines throughout, chunk cadence ~5-6 min (genuine per-date fetch/decode work).
- At `2026-07-31T16:08:12Z` (mid chunk-25 processing), the in-run `assert_consolidator_healthy()` guard
  (`unified_trading_library.manifest_writer._state`) started raising `ManifestConsolidatorStaleError` for bucket
  `market-data-tick-tradfi-prd-central-element-323112` — heartbeat age grew monotonically 7266s → 7771s across the rest
  of the run (never recovered before self-delete at 16:16:39Z). Root cause (already independently diagnosed and fixed
  elsewhere): the tradfi manifest-consolidator cron (`uts-prod-manifest-consolidator-market-data-tradfi-cron`) had been
  deliberately `PAUSED` since 2026-07-29 as part of
  `/plans/active/mtds_available_at_cross_asset_backfill_2026_07_13.md`'s snapshot→pause→apply→resume protocol; resumed
  2026-08-02 (that plan's Progress Log, slot-3). This VM's run sits chronologically BETWEEN the pause and the fleet-wide
  24h-boot-preflight outage that `tradfi_ohlcv_backfill_oom_preflight_fails_paused_consolidator_2026_08_02.md` diagnosed
  — i.e. this is corroborating evidence the staleness was already causing (smaller, in-run) damage hours before it grew
  severe enough to trip the 24h preflight fleet-wide.
- From chunk 25 through chunk 52 (~2020-06-17 through 2020-12-29), `Batch complete: N results collected` dropped from
  7/7 to 2-5/7 for every single chunk — most of each week's days lost their payload to the stale-consolidator guard.
  Chunk 53 (2020-12-30→31, the last chunk) hit 0/7 (well, 0/2 for its shorter 2-day range) and was the ONLY one where
  the whole chunk subprocess also returned non-zero (`CHUNK_RC≠0` → `CHUNK_FAILED` logged, `HAD_FAILURE=1`).
- **The bug**: `mtds_chunk_loop.sh` (generated inline by `deployment-service/scripts/vm/setup-data-pipeline-vm.sh`, the
  `VM_TASK=mtds-backfill` branch) only sets `HAD_FAILURE=1` when the whole-chunk subprocess's `CHUNK_RC` is non-zero. A
  chunk where SOME payloads succeed and SOME fail (the CLI's internal per-payload handler retries/catches failures and
  the process itself still exits 0 as long as at least one payload succeeded) never sets `HAD_FAILURE`, so the
  `[[VM_PROGRESS]] last_completed_date=...` monotonic checkpoint keeps advancing straight through 28 consecutive lossy
  chunks. The final `PROGRESS.json` reads `{"last_completed_date": "2020-12-22", "monotonic": true}` — i.e. it claims
  the entire year through late December is done, when in reality roughly a third of it is most likely still uncaptured.
  `cefi_coverage_chunk_loop.sh` (same file, the `VM_TASK=cefi-coverage-backfill` branch) is generated from an almost
  line-for-line copy of the same gating logic and has the identical blind spot.

## Why it matters

- **`PROGRESS.json` is exactly the signal `RelaunchPreemptedVm` trusts to resume a SPOT-preempted VM from "where it left
  off" instead of replaying `START_DATE`** (per the workspace's `/codex/05-infrastructure/vm-launcher-runbook.md` §
  preemption-recovery HARD RULE). If a VM hits this exact pattern (partial-payload chunk loss without a whole-chunk
  failure) and THEN gets SPOT-preempted, the auto-resume would skip straight past the real gap forever, believing it
  already-captured. This VM was not preempted (it completed and self-deleted normally), so no auto-resume skip actually
  happened here — but the latent mechanism is real and will bite the next VM that hits both conditions together.
- **The wrapper-level signal set (`EXIT_STATUS`, `CHUNK_FAILED` markers) undersells the actual damage.** A human or
  monitor reading only `EXIT_STATUS=0` + "only the last chunk `CHUNK_FAILED`" would reasonably conclude the backfill is
  ~99% complete with a 2-day gap — the real picture (a full-log `Batch complete: N` trace) is closer to a third of the
  year missing. This is a general risk for any long multi-chunk MTDS/cefi-coverage backfill VM that runs through a
  period of manifest-consolidator instability, not specific to this one shard/date-range.
- **Likely self-healing on the DATA side, not a permanent loss**: the consolidator-staleness exception fires in the
  read/preflight path before any write, so no phantom `captured`/`empty_confirmed` manifest row gets written for the
  skipped dates — the routine wave-launcher cadence (fresh launch, `VM_FORCE=false`, manifest-driven skip-if-fresh, not
  `PROGRESS.json`-driven) should keep re-attempting the genuinely-missing dates on its normal ~2-3h cycle, independent
  of this bug. A fresh relaunch of this exact shard was already in flight at check time
  (`tradfi-bf-cme-ohlcv-1m-g01-es-es-2020-20260803-180128`, launched 18:01Z 2026-08-03, healthy, consolidator confirmed
  fresh — `Update time: 2026-08-03T19:30:26Z`, cron `ENABLED`), so this doc's P2 spot-check todo below should mostly
  just be confirming the self-heal happened, not performing it manually.

## Recommended decision

Fix the gating so a partial-payload chunk is distinguishable from a fully-successful one (either have the Python CLI
return a non-zero/distinct exit code when ANY payload in the batch failed even if others succeeded, or have the shell
loop parse the `Batch complete: N results collected` line against the chunk's expected payload count and treat a
shortfall the same as `CHUNK_RC≠0` for `HAD_FAILURE` purposes) in both generated chunk-loop scripts. Separately, confirm
the actual CME ES/MES 2020 gap this incident left behind has been recaptured by the ordinary wave-launcher cadence.

- [x] ✅ [CODE] P2. Fix `HAD_FAILURE`/checkpoint gating in `mtds_chunk_loop.sh`'s generator
      (`setup-data-pipeline-vm.sh`, `VM_TASK=mtds-backfill` branch, ~line 1740-1800) and the mirrored
      `cefi_coverage_chunk_loop.sh` generator (`VM_TASK=cefi-coverage-backfill` branch, ~line 1820-1880) so a chunk with
      partial payload loss (some but not all of that chunk's date-payloads failed) is treated the same as a fully-failed
      chunk for `HAD_FAILURE`/ `[[VM_PROGRESS]]` checkpoint-advancement purposes — the checkpoint must never advance
      past a date range that didn't fully succeed. Prefer surfacing this at the Python CLI layer (return a
      distinguishable exit code, e.g. via `market_tick_data_service`'s batch handler, when
      `results_collected < payloads_submitted`) over shell-side log-scraping of "Batch complete: N results collected"
      (fragile string match); if the CLI-layer signal isn't readily available, the shell-side parse is an acceptable
      fallback — just add a regression test either way. Target repo: deployment-service (shell wrapper) and/or
      market-tick-data-service (CLI exit-code signal), whichever the implementer determines is the cleaner surface. —
      deployment-service@5478a92 (see Progress Log)
- [x] ✅ [DATA] P2. Once the in-flight `tradfi-bf-cme-ohlcv-1m-g01-es-es-2020-20260803-180128` relaunch (or its
      wave-launcher successor) completes, spot-check manifest `capture_status` for a sample of the dates this incident
      likely dropped (e.g. 2020-07-01, 2020-09-15, 2020-11-11, 2020-12-30, 2020-12-31 — CME ES/MES
      `ohlcv_1m`/`ohlcv_1s`) to confirm they are now genuinely `captured`, not still gapped. If any remain uncaptured
      after that relaunch completes, a targeted relaunch of just the remaining gap is the follow-up (do not
      blind-relaunch the whole year again). Target repo: NA (verification-only). — verified genuinely `captured` for all
      5 sample dates (see Progress Log)

## Progress Log

- **2026-08-03 (slot-11, data_engineering)**: filed while closing `tradfi_backfill_oom_remediation_2026_06_24.md`'s
  final todo. Full-log trace (not just tail) of `tradfi-bf-cme-ohlcv-1m-g01-es-es-2020-20260731-134654`'s `run.log`
  (370k lines) via `gsutil cat` + `grep`/`awk` (no whole-corpus GCS walk — single VM's own log only). Confirmed current
  consolidator health (`gsutil stat` single-object check + `gcloud scheduler jobs describe`, both narrow/bounded reads)
  and the in-flight relaunch's clean progress before filing rather than guessing.
- **2026-08-03 (slot-2, infra)**: fixed todo 1 via the shell-side fallback, not the CLI-layer exit code. Investigated
  the CLI-layer option first (`unified_trading_library.service_framework._adapter`'s `_drive_serial`/`_drive_concurrent`
  - `bootstrap.py`'s `status`→exit-code mapping): the per-date `processed`/`failed` counters already exist there, but
    they back EVERY `UnifiedServiceHandler`+`BatchIO` batch service (MTDS, MDPS, features-service, …), not just MTDS
    download — changing `status="ok"` semantics there would flip exit-code behavior for every batch service's wrapper/
    cron simultaneously, which is out of scope for a P2 fix declared against only `deployment-service` +
    `market-tick-data-service`. Went with the shell-side fallback the issue doc explicitly sanctioned instead: both
    `mtds_chunk_loop.sh` and `cefi_coverage_chunk_loop.sh` generators
    (`deployment-service/scripts/vm/ setup-data-pipeline-vm.sh`) now (a) emit each chunk's expected day-count alongside
    its date range, (b) tee the CLI subprocess's output to a scratch file (via `PIPESTATUS[0]` to still capture the real
    exit code), (c) parse the CLI's own `Batch complete: N results collected` line and treat `N < expected_days` the
    same as `CHUNK_RC≠0` for `HAD_FAILURE`/checkpoint-advancement purposes (new `reason=PARTIAL_PAYLOAD_LOSS` marker,
    reusing the existing `CHUNK_FAILED:` greppable prefix). Added 8 regression tests
    (`TestChunkLoopPartialPayloadLossGating` in `tests/unit/test_vm_launcher_scripts.py`) that extract the REAL
    generated heredoc bodies from the setup script and run them against a stub CLI reporting canned
    results-collected/exit-code pairs per chunk — covering full success, partial loss, an earlier partial loss blocking
    a later fully-successful chunk's checkpoint advance (the exact incident pattern), and unchanged full-failure
    behavior. All 185 tests in the file pass (`quality-gates.sh` run separately before shipping). Todo 2 (spot-check the
    CME ES/MES 2020 gap) is unclaimed — separate DATA/verification-only scope, left for pickup.
- **context-scout 2026-08-03**: refreshed context_scope (4 entries) — swapped the preemption-monitoring codex doc for
  `vm-launcher-runbook.md`, which the doc's own "Why it matters" section explicitly cites as the exact mechanism
  (RelaunchPreemptedVm / PROGRESS.json trust) this bug threatens — this VM wasn't preempted, so that was a weaker match.
- **2026-08-03 (slot-3, data_engineering)**: closed todo 2. The named relaunch (`...-180128`) turned out to have been
  SPOT-preempted at 2026-08-03T20:23:53Z — confirmed via `gcloud compute operations list` (`compute.instances.preempted`
  systemevent timestamp matches the VM's own last `PROGRESS.json`/watchdog-trace update to the second) — and its
  immediate wave-launcher successor (`...-210126`) was itself preempted ~90s after insert (`LAUNCH_PARAMS.json` only, no
  `run.log` ever written). Both are ordinary `VM_FORCE=false` skip-if-fresh relaunches, not the PROGRESS.json-driven
  resume path (`START_DATE` stayed `2020-01-01` in `LAUNCH_PARAMS.json` — expected and correct for this launcher mode,
  not a checkpoint-replay bug), so I queried the tradfi availability manifest directly rather than wait on any single
  VM's completion — a single bounded `_index/availability_index.parquet` download (small object, not a whole-corpus
  walk) filtered in pandas for the 5 sample dates. Initial query used bare `instrument_id` values ("ES"/"MES"/"ES.FUT"/
  "ES.OPT"/"MES.FUT"/"MES.OPT") and showed `attempted_failed`/`empty_confirmed`/`NO_ROW_FOUND` for every row — looked
  alarming until I cross-checked two CONTROL dates (2020-02-03, well before the incident window, and 2020-08-04, the
  exact date the `...-180128` run.log shows real `StreamingParquetWriter` uploads landing) and found the IDENTICAL
  `attempted_failed`-paired-with-`empty_confirmed` pattern on both — proving this pairing is a pre-existing, systemic
  manifest artifact tied to those raw instrument_id strings (a duplicate/legacy row shape), unrelated to this incident,
  not evidence of a real gap (per CLAUDE.md "probe the vocabulary the WRITER emits" — the real write target, confirmed
  from the run.log itself, is grouped by `instrument_type=futures_chain`/`underlying=SP500`, not by literal `ES`/`MES`
  instrument_id). Re-queried on `venue=CME, underlying=SP500, instrument_type=futures_chain` for both `ohlcv_1m` and
  `ohlcv_1s`: all 5 target dates read `capture_status=captured, expected=True, available=True`, with real row_counts
  (1392-2824 for 1m, 27755-63315 for 1s), `source=databento` — genuinely captured, not gapped. No targeted relaunch
  needed. Both todos in this doc are now done with no lock — archiving per
  `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`'s 6-step ritual in a separate follow-up commit
  (never bundle a checkbox flip with the `git mv` per `agents/RULES.md` § 2). Noted but did NOT file a new issue for the
  VM's repeated-preemption pattern (4x in <24h for this one shard, including the ~90s-after-insert case) — the
  self-healing skip-if-fresh cadence worked exactly as this doc's own "Why it matters" section predicted despite it, so
  this reads as ordinary SPOT contention in a busy zone (many concurrent tradfi VMs at check time), not a defect.
