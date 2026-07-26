---
doc_type: issue
title:
  First live run of /vm-preemption-billing-waste-audit + design for a cross-run pre-flight gate on known-dead shards
summary: >-
  Two follow-ups from `/codex/05-infrastructure/vm-preemption-and-billing-waste-monitoring.md` (shipped 2026-07-24) that
  the codex doc itself explicitly defers: (1) the skill (`/vm-preemption-billing-waste-audit`) exists but has never been
  run for real against both clouds' live fleets — its findings are unknown until it's actually invoked; (2) the codex
  doc's own "What this contract deliberately does NOT do" section names a real gap — no automated pre-flight gate stops
  a future backfill wave from re-attempting a shard `classify_venue_error()` already FAIL-classified, or one that's
  failed identically across N consecutive waves. Both are tracked here per
  `data_pipeline_e2e_milestones_gate_2026_07_24.md` §4.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service, market-tick-data-service, instruments-service, unified-api-contracts]
scope: [engineer, admin]
tags: [vm, spot, preemption, billing, attempted_failed, monitoring, cost, pre-flight-gate]
related:
  [
    /codex/05-infrastructure/vm-preemption-and-billing-waste-monitoring.md,
    /codex/04-architecture/shard-level-failure-isolation.md,
    /codex/05-infrastructure/spot-vms-for-backfill.md,
    /plans/active/data_pipeline_e2e_milestones_gate_2026_07_24.md,
  ]
created: "2026-07-24"
last_updated: "2026-07-25"
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.8
assigned_role: infra
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: /plans/active/data_pipeline_e2e_milestones_gate_2026_07_24.md §4
depends_on: []
---

# First live run of the VM billing-waste audit + pre-flight gate design

## Todos

- [x] [SCRIPT] P1. Run `/vm-preemption-billing-waste-audit` for the first time against both clouds' live fleets with a
      30-day lookback. Definition-of-done: for every launcher family, either a filed finding (preemption with no
      matching auto-recovery, or a confirmed billing-wasting `attempted_failed` cluster) or a stated "clean" — cite the
      run's own output, not a summary. **DONE 2026-07-25 — see Progress Log (both entries); GCP-side is now exhaustive —
      all 18 launcher families covered across the two runs (197/197 preemption events accounted for), with a confirmed
      new billing-waste finding (`tradfi-bf-*`) and an alerting gap. AWS side remains IAM-blocked
      (`ec2:DescribeSpotInstanceRequests` — re-confirmed 2026-07-25, `uts-orchestrator-epic-role` still lacks the
      permission) — noted gap per this todo's own carve-out, not treated as a blocker.**
- [ ] [BACKEND] P2. Design + wire a cross-run pre-flight gate: when `classify_venue_error()` returns `action=FAIL` for a
      shard (or N consecutive waves hit the identical `error_reason` on the same shard), route it to a "known-dead, do
      not re-attempt" manifest-level marker instead of the current default (silent infinite retry via
      `record_failed()`). Definition-of-done: the marker mechanism is designed (schema field or side-table), at least
      one launcher family wired to check it before dispatching a shard, and a regression test proving a marked shard is
      skipped on the next wave.

## Progress Log

- **2026-07-25 — First `/vm-preemption-billing-waste-audit` run (partial, GCP-only, 2 of ~18 launcher families traced in
  depth).**
  `gcloud compute operations list --filter="operationType=compute.instances.preempted" --project= central-element-323112`,
  30-day lookback: **197 preemption events**, collapsing to roughly 18 distinct launcher families once per-shard-suffix
  noise is stripped. Full family breakdown captured in this session's scratchpad (not promoted — regenerable via the
  same filter). Two families traced to their `vm-logs/{vm}/` GCS contents + `run.log`:
  - **`canonical-migration-tradfi-cdlap`** (54 events, the single largest family — all within a ~10-minute burst on
    2026-07-23): checked `vm-logs/canonical-migration-tradfi-cdlap-20260723-105729/` — only `LAUNCH_PARAMS.json` +
    `TARBALL_PINS.json` exist, no `run.log`, meaning these VMs were preempted within seconds of creation, before writing
    any output — a SPOT capacity crunch on that zone/machine-type at that moment, not a mid-run loss. Negligible billing
    impact (GCP does not meaningfully bill for a VM that never completed boot/init). This burst's timing matches exactly
    when the independent `/data-pipeline-reconciliation --asset-group tradfi` run (this same session, earlier) measured
    the tradfi canonical-id migration had jumped from 30.8%→99.3% clean — strong circumstantial evidence this family's
    preemptions were absorbed by successful relaunches, not a silent loss. **Verdict: clean, no finding.**
  - **`canonical-migration-defi-rebuild`** (14 events, spread across the full window, not a single burst): checked
    `vm-logs/canonical-migration-defi-rebuild-20260723-073604/` — this one DID run for real (~56 min, `run.log` shows
    active date-by-date manifest scanning, 2.2M+ manifest entries written incrementally to its own per-VM shard) before
    being preempted mid-scan. **No `PROGRESS.json` was ever written by this launcher** — it does not use the documented
    PROGRESS-checkpoint contract at all; its only persisted state is the cumulative per-VM manifest shard itself.
    `LAUNCH_PARAMS.json` shows `RESUME_START_DATE=2026-01-01` (fixed), not a value derived from measured progress. This
    is a genuine partial-conformance gap against the codex contract — **but the actual billing-waste risk is bounded,
    not confirmed severe**: `relaunch_backfill_vm.py`'s own code comments confirm the dangerous case is specifically a
    `--force`/`redo_all` run with no checkpoint (which PAGEs loudly rather than silently replaying); this launch's
    params show `RESUME_MODE=full`, not a force run, so a blind restart-from-`START_DATE` would still benefit from the
    launcher's presence-skip default (re-scanning is cheap; re-fetching already-captured data is not). **Verdict: real
    conformance gap, bounded/moderate risk — filed as a follow-up todo below, not escalated as urgent.**
  - **Remaining ~16 families NOT traced this run** (`mtds-backfill-tradfi-pipelinecheck` 13, `cefi-aster` 7,
    `canonical-migration-defi-pi-range` 7, `instr-backfill-tradfi-pchk` 5, `cefi-queue-heavy-binancefutu-x17` 5,
    `mtds-dex-swaps-backfill` 4, `canonical-migration-cefi-cdlap` 4, `af-backfill` 4, `canonical-migration-defi-relabel`
    3, `datapoint-validation-{prediction,cefi,defi}` 5, `cefi-hyperliquid` 2, the
    `canonical-migration-cefi-wp*`/`-content-*` migration wave ~31 events, `tradfi-bf-*` per-shard backfill ~35 events,
    plus 4 singleton families) — **declared scope limitation, not silently omitted**. Time-boxed this run in favor of
    covering the two highest-event-count families plus the `attempted_failed` sweep below; a follow-up session should
    trace the rest, prioritizing `tradfi-bf-*` and the `canonical-migration-cefi-wp*` wave (highest remaining event
    counts).
  - **AWS side: blocked.** `aws ec2 describe-spot-instance-requests` (us-east-1) returned `UnauthorizedOperation` — the
    orchestrator role (`uts-orchestrator-epic-role`) lacks `ec2:DescribeSpotInstanceRequests`. A broader
    `describe-instances` filter for terminated/stopped backfill/migration/canonical-tagged instances in us-east-1
    returned empty (either genuinely no AWS backfill fleet right now, or the wrong region/account scope — not
    conclusively determined). **Filed as its own gap** — an IAM grant (if AWS-side SPOT monitoring is wanted) or
    confirmation that AWS is not currently used for backfill VMs is an operator-level call, not something to route
    around.
  - **`attempted_failed` sweep**: leveraged this session's own 5 `/data-pipeline-reconciliation` runs (same day) rather
    than re-deriving from scratch. CeFi's largest cluster (Tardis HTTP 403, 797,323 rows / 75.3%) is already tracked
    (`tardis_concurrent_ip_lockout_2026_07_12.md`). The next-largest untracked slice, `VENUE_FETCH_FAILED` (219,071
    rows, 20.7% of cefi's `attempted_failed`, spread across BINANCE-FUTURES/
    KRAKEN-FUTURES/BITFINEX-FUTURES/BYBIT/others), was investigated this run: date range 2020-03-20→2026-05-21, **NOT
    growing for the last 2+ months** (today is 2026-07-25) — real historical waste, but not an ACTIVE, ongoing billing
    drain (nothing is currently re-attempting these specific shards). **Verdict: informational, not urgent.** Other 4
    AGs' `attempted_failed` distributions not independently re-swept this run.
  - **Step 3 (alert-firing verification) not performed this run** — time-boxed out; flagged as not done, not assumed
    clean.

### New follow-up todo from this run

- [ ] [BACKEND] P2. **`canonical-migration-defi-rebuild`'s launcher (`launch-canonical-migration-vm.sh` via
      `RESUME_MODE=full`) does not write a `PROGRESS.json` checkpoint** — it relies only on the cumulative per-VM
      manifest shard, and `RESUME_START_DATE` is a fixed launch param, not derived from measured progress. Bounded risk
      today (not a `--force` run, presence-skip limits the cost of a blind restart to re-scan time, not re-fetch), but
      out of conformance with the documented PROGRESS-checkpoint contract
      (`/codex/05-infrastructure/spot-vms-for-backfill.md`). Either wire this launcher to emit `PROGRESS.json` like the
      conforming launchers do, or confirm the per-VM-manifest-shard mechanism is an accepted equivalent and document
      that exception in the codex SSOT. Repo: deployment-service.

- **2026-07-25 (second session) — remaining 16 GCP launcher families traced; AWS re-confirmed blocked; Step 3 done.**
  Re-ran
  `gcloud compute operations list --filter="operationType=compute.instances.preempted" --project=central-element-323112`,
  30-day lookback: **197 events** (same total as the first session's run — the window hadn't rolled since), collapsing
  to the same **18 launcher families**. The 2 families the first session traced are unchanged; this session traced the
  remaining 16, accounting for all 197/197 events family-by-family (34+31+13+7+7+5+5+4+4+4+3+5+2+5(singletons)+68(prior
  two) = 197). Evidence trail (VM names, `gsutil ls`/`cat` output) is in this session's scratchpad, regenerable via the
  same filter + `vm-logs/{vm}/` lookups against `gs://deployment-scripts-central-element-323112/`.

  - **`tradfi-bf-*` (34 events, prioritized — highest remaining count) — CONFIRMED NEW BILLING-WASTE FINDING, not just
    bounded risk.** Every sampled shard (`tradfi-bf-cme-ohlcv-1m-btc-2020-20260721-050757`,
    `...-eth-2022-20260721-051043`, `...-krx-eq-ohlcv-24h-2021-20260722-193435`, `...-nasdaq-...-g04-2026-...`) shows
    substantial real `run.log` content (170KB-450KB) — genuine mid-run preemptions, not boot-preempts. This launcher
    (`_tradfi-ohlcv-launcher-lib.sh` / `launch-tradfi-bf-*.sh`, shared `mtds_chunk_loop.sh`) writes **no `PROGRESS.json`
    and no `LAUNCH_PARAMS.json`** — only `run.log` — relying entirely on GCS manifest presence-skip
    (`_apply_freshness_skip()`) for idempotent resume. Directly traced TWO independent shards end-to-end:
    - `tradfi-bf-cme-ohlcv-1m-btc-2020`: VM `...-041531` completed Chunk 1/53
      (`PROGRESS: chunk=1/53 range=2020-01-01→2020-01-07 time=...T03:24:04Z`) then died (not itself a logged
      `compute.instances.preempted` event) around 03:28. Its successor `...-050757` (the VM that WAS logged preempted,
      ~05:18 UTC) **restarted at Chunk 1/53** and its own pre-flight check logged
      `Pre-flight: venue=CME date=2020-01-02 ... partial coverage; 1 of 1 expected atoms still missing` — i.e. it did
      NOT see `041531`'s already-recorded rows and **re-fetched from Databento**
      (`DatabentoBaseClient warmup successful`, new client session) before reaching (and being preempted at) Chunk 7/53.
    - `tradfi-bf-cme-ohlcv-1m-eth-2022`: same pattern — VM `...-041824` completed through Chunk 1/53 at `03:32:19Z`;
      successor `...-051043` (preempted) **also restarted at Chunk 1/53** (`04:25:21Z`), not from Chunk 2. This is a
      **confirmed**, directly-observed double-fetch (real Databento API calls re-issued for already-captured dates), not
      the "presence-skip bounds the cost" reasoning that scoped `canonical-migration-defi-rebuild` as bounded/moderate
      in the first session — the presence-skip did NOT actually prevent re-fetch here. `tradfi-bf-*` is also the single
      largest remaining family (34 of the 129 events this session covered) and shares its
      no-`PROGRESS.json`/`mtds_chunk_loop.sh` architecture with `mtds-backfill-tradfi-pipelinecheck` (13 events),
      `mtds-dex-swaps-backfill` (4), `cefi-aster` (7), `cefi-hyperliquid` (2), `cefi-queue-heavy-binancefutu-x17` (5),
      and `af-backfill` (4) below — so the exposure is broader than this one family. **Verdict: real, confirmed billing
      waste — filed as a new P1 follow-up todo below (higher priority than the existing
      `canonical-migration-defi-rebuild` todo, since this one is empirically confirmed rather than theoretical, and
      covers more VMs).**

  > **⚠️→✅ CORRECTED 2026-07-25 (adversarial verification, 3-agent independent refuter panel, 3/3 REFUTED) — the
  > "confirmed double-fetch of already-captured data" framing above is FACTUALLY WRONG for both cited examples.**
  > Independently re-pulled all 4 full `run.log`s and grepped for `total_records=`/`complete=True`: the PREDECESSOR VMs
  > (`...-041531` btc-2020, `...-041824` eth-2022) never actually captured or uploaded any real rows for Chunk 1 — every
  > date returned `total_records=0 complete=False`. Root cause visible in the same logs:
  > `[DATABENTO_FETCH_FAILED] after 0 rows: underlying='BTC'/'ETH' is not a real product root ... quarantine, never fake-canonicalize`
  > — the launch was configured expecting 2 atoms (FUT+OPT) for BTC/ETH CME, and the OPT atom hit an unresolvable
  > combo-symbol path that the system correctly refused to fake-canonicalize (by design, not a bug — see new P3
  > follow-up below). The successor VMs' pre-flight "still missing" check was therefore **CORRECT, not a presence-skip
  > failure** — there was nothing valid to skip. The successors then succeeded because their launches expected only 1
  > atom (FUT-only, not FUT+OPT), avoided the buggy combo path, and got real records for the first time (e.g. eth
  > `...-051043`: 1973-8654 real records/date, `complete=True`). One refuter additionally read
  > `market-tick-data-service/market_tick_data_service/engine/orchestrator/venue_fetch.py`'s
  > `_apply_preflight_skip_filter` and confirmed a real atom-aware skip layer exists downstream of the coarse "Chunk
  > N/53" progress marker — presence-skip is working as designed, the chunk-loop's log line alone just doesn't show it.
  > **The no-`PROGRESS.json`/no-`LAUNCH_PARAMS.json` architectural gap is still real and confirmed** (all 3 refuters
  > independently verified this) — but the "CONFIRMED billing waste" upgrade is retracted; this reverts to the SAME
  > "bounded/theoretical risk" classification as `canonical-migration-defi-rebuild` below, not a worse one. The P1 todo
  > below is corrected accordingly (downgraded to P2, folded alongside the other architecture-gap families rather than
  > escalated ahead of them). **Lesson**: a chunk-level "restarted at Chunk 1/53" symptom looks identical whether the
  > predecessor genuinely captured data (real waste on restart) or never captured anything at all (correct retry) —
  > don't conclude "double-fetch" from the restart point alone; grep the actual `total_records=`/`complete=` values for
  > the specific chunk before calling it confirmed.
  - **`canonical-migration-cefi-wp*`/`-content-*` migration wave (31 events: 25 `wp*` + 6 `content-*`, prioritized) —
    CLEAN, no finding.** Both sub-families invoke the same idempotent-by-design script,
    `scripts/migrate_cefi_content_instrument_id_catalogue_2026_07_17.py --apply --start-date … --end-date … --workers N`
    — verified in the script itself (`rows_already_canonical` tracking, `already_canonical_skipped` return path,
    explicit code comment "idempotency — the written id column already resolves to itself"). Sample
    `canonical-migration-cefi-wp21-wpf07210859` shows TWO preemption events in the ops log for the identical VM name
    (GCE name reused across relaunches, unlike `tradfi-bf-*`'s per-launch timestamped names) but its (necessarily
    latest-surviving) `run.log` shows a single successful run ending `command exited rc=0` +
    `VM_SHUTDOWN_ON_COMPLETION=true` self-delete — i.e. it ultimately succeeded. Sample
    `canonical-migration-cefi-content-12-20260719-135509` (preempted for real, `run.log` shows 14,400/139,376 files
    processed with `already_canonical_skipped` climbing) confirms the mechanism: a relaunch replaying the same
    `--start-date`/`--end-date` window re-reads already-patched files, finds them already-canonical, and skips — cheap,
    not a re-fetch. **Verdict: clean — no `PROGRESS.json` needed because the underlying script is idempotent by
    construction.**
  - **`mtds-backfill-tradfi-pipelinecheck` (13 events) — same architecture gap as `tradfi-bf-*` but bounded exposure.**
    Same `mtds_chunk_loop.sh`, no `PROGRESS.json`. Sample shard (`...bbc403`): preempted at 08:02 UTC, relaunched ~4 min
    later as `...-080359-bbc403`, which completed cleanly (`command exited rc=0`, `DEPLOYMENT_COMPLETED exit_code=0`)
    for its single-day chunk (`chunk=1/1`, date=2026-07-13) within 4 minutes. Chunks here are 1 day (pipeline-check
    shards), not the 53-chunk/year windows `tradfi-bf-*` uses, so even an unverified worst-case replay costs far less.
    **Verdict: same architectural gap, materially lower exposure — folded into the `tradfi-bf-*` follow-up todo rather
    than filed separately.**
  - **`instr-backfill-tradfi-pchk` (5 events) — CLEAN.** All 5 (`s-cme`, `f-ice`, `s-ice`, `f-cboe`, `s-krx`) confirmed
    **boot-preempts**: zero GCS objects under `vm-logs/{vm}/` for every one of them (`gsutil ls` → "One or more URLs
    matched no objects"). Negligible billing impact — preempted before any output.
  - **`canonical-migration-cefi-cdlap` (4 events) — CLEAN, and a positive counter-example worth noting.** Sample
    `canonical-migration-cefi-cdlap-20260722-215112` has `LAUNCH_PARAMS.json` + `TARBALL_PINS.json` +
    **`MIGRATION_PROGRESS-shard2.json`**
    (`{"last_processed_line_index":70247,"processed_count":70248,"shard_index":2, "shard_of":10,"total_shard_lines":93990,...}`)
    — a real, working checkpoint, just under a **non-standard filename** (not literally `PROGRESS.json`). Functionally
    conformant (line-indexed, monotonic within its shard). **Open question, not independently verified this run**: does
    `exit_code_fleet_monitor.py`'s `read_progress_checkpoint()` (which reads by a specific expected filename per
    `/codex/05-infrastructure/spot-vms-for-backfill.md`) actually recognize `MIGRATION_PROGRESS-shard{N}.json`, or does
    this launcher's checkpoint silently go unread by the generic actuator despite existing? Filed as a minor follow-up
    below.
  - **`canonical-migration-defi-relabel` (3 events) — CLEAN, fully conformant.** Sample
    `canonical-migration-defi-relabel-20260724-001905-d06to09v2` has `LAUNCH_PARAMS.json`, `TARBALL_PINS.json`, AND a
    real `PROGRESS.json`: `{"last_completed_date":"2026-05-04","monotonic":true,...}` — exactly the documented contract.
    **Verdict: clean — a positive example the pattern works when implemented.**
  - **`instr-backfill-defi-targeted` (singleton, 1 event) — CLEAN, fully conformant**, same shape: `PROGRESS.json` =
    `{"last_completed_date":"2020-06-21","monotonic":true,...}`.
  - **`canonical-migration-defi-subgraph-deindex` (singleton) and `orphan-sweep-defi` (1 of 10 vm-log dirs was the
    actually-preempted instance, `...-033413`) — CLEAN, both confirmed boot-preempts** (0 objects / a bare 100-byte
    `LAUNCH_PARAMS.json` with no `run.log`).
  - **`canonical-migration-defi-pi-range` (7 events) and `canonical-migration-defi-per-instrument` (singleton) — real
    substantial work, NO checkpoint of any kind, flagged for the same follow-up (not independently deep-traced for
    double-fetch this run, time-boxed).** `canonical-migration-defi-pi-range-20260719-130722-2025q1`'s `run.log` alone
    is **731 MB** (no `LAUNCH_PARAMS.json`, no `PROGRESS.json`) — the largest log seen this audit, implying a long
    single-shard runtime with zero checkpoint. Note: the operator/orchestrator appears to have already noticed this —
    later `vm-logs/` entries show the same logical shard split into `2025q1s1`..`2025q1s6` sub-shards (smaller units,
    mitigating exposure), so this may already be self-correcting operational practice rather than an unaddressed gap.
    `canonical-migration-defi-per-instrument-20260722-053820`'s `run.log` is **79 MB**, also no checkpoint file at all
    (only `TARBALL_PINS.json`).
  - **`cefi-queue-heavy-binancefutu-x17` (5 events), `cefi-aster` (7 events), `cefi-hyperliquid` (2 events),
    `mtds-dex-swaps-backfill` (4 events) — real substantial work confirmed, no `PROGRESS.json`, NOT deep-traced for
    double-fetch (time-boxed).** `cefi-queue-heavy-binancefutu-x17` is the Tardis `launch-cefi-sharded-backfill.sh`
    `SINGLE_VM_QUEUE=1` launcher (36 `vm-logs/` dirs across ~4 days — mostly queue-drain progression, not
    preemption-churn); its per-instrument `StreamingParquetWriter` writes are a finer natural checkpoint granularity
    than `tradfi-bf-*`'s date-chunk level, so the double-fetch risk is plausibly (not confirmedly) lower. CeFi's Tardis
    fleet already has extensive existing oversight (cap-1 concurrency guard, the tracked
    `tardis_concurrent_ip_lockout_2026_07_12.md` `attempted_failed` cluster), so this wasn't re-prioritized for a full
    trace given the time budget. `mtds-dex-swaps-backfill` reuses one GCE name across relaunches (like `wp21`) over a
    wide `--start-date 2023-01-01 --end-date 2026-07-22` window.
  - **`af-backfill` (4 events) — MIXED / partially-resolved finding, needs follow-up.** Command:
    `instruments_service --operation instruments --asset-group SPORTS --start-date 2019-01-01 --end-date 2026-07-17 --force --sports-provider API_FOOTBALL --sports-entity FIXTURES`
    — a `--force` full re-fetch over 7+ years, exactly the case `relaunch_backfill_vm.py` flags as dangerous
    (`force_run_not_replayable` → PAGE when no monotonic checkpoint exists). The preempted VM
    `af-backfill-20260718-141638`'s `vm-logs/` dir has **only `run.log`** — no `LAUNCH_PARAMS.json` — despite
    `launch-api-football-backfill-vm.sh`'s own comment describing `lc_write_launch_params` as writing one ("best-effort,
    non-fatal"), and despite `exit_code_fleet_monitor.py` sourcing `launch_env` for the relaunch actuator via
    `_gcs.read_launch_params(...)` — i.e. the exact file the actuator needs was missing for this shard. Yet the
    empirical relaunch 9 minutes later (`af-backfill-20260718-150353`) ran with `--start-date 2019-01-10` (advanced 9
    days from the original `2019-01-01`, not a blind day-one replay) — so SOME resume signal reached it, through a path
    this session could not fully trace within budget (possibly a manifest/entity-level resume separate from the generic
    VM-level `PROGRESS.json`/`LAUNCH_PARAMS.json` contract). **Verdict: not a clean bill — the specific mechanism that
    produced the correct-looking resume is unconfirmed, and the `LAUNCH_PARAMS.json` gap is real and reproducible on
    this sample. Filed as a follow-up todo below** rather than asserted as either broken or fine.
  - **`datapoint-validation-{prediction,cefi,defi}` (5 events total: 2+2+1) — LOW SEVERITY, no finding filed.** Runs
    `scripts/validate_datapoint_schema_id.py` — the Tier-2 **read-only** per-datapoint id+schema validation job (per
    `/codex/02-data/reconciliation-census-and-compute-tiers.md`). No `PROGRESS.json`, but a replay re-reads/re-validates
    GCS parquet already there — it does NOT re-issue paid external API calls (Databento/Tardis), so even an unconfirmed
    worst-case blind restart costs internal GCS-read compute time, not real third-party billing. **Verdict:
    architecturally same gap, immaterial billing severity — not escalated.**
  - **`backfill-orphan-e-prediction` (singleton) — real work confirmed (75KB `run.log`), no checkpoint, not deep-traced
    (low event count, time-boxed).**
  - **AWS side re-confirmed blocked.** `aws sts get-caller-identity` succeeds (`uts-orchestrator-epic-role` via
    `i-0dd9812a96cdda5dc`); `aws ec2 describe-spot-instance-requests --region us-east-1` still returns
    `UnauthorizedOperation` (`ec2:DescribeSpotInstanceRequests` not granted). No change from the first session — this
    remains an operator-level IAM-grant decision, not something resolvable from this session.
  - **Step 3 (alert-firing verification) — DONE this run (the first session explicitly deferred it).** Traced
    `relaunch_backfill_vm.py`'s own severity classification: a "successful" relaunch (the launcher subprocess ran
    without error) self-emits `DP_VM_PREEMPTED` at **INFO** severity ("the routine, benign case") — no page. Only
    `DP_VM_PREEMPTED_NO_RELAUNCH` (no launcher binding / relaunch-budget exceeded / launcher subprocess failure /
    `force_run_not_replayable`) is **CRITICAL** and pages. **Finding: a `tradfi-bf-*`-shaped blind START_DATE replay
    would NOT have paged** (was: "the `tradfi-bf-\*` double-fetch confirmed above" — corrected 2026-07-26,
    `/plan-reconcile` infra shard: this doc's own ⚠️→✅ adversarial-verification banner (3/3 refuters, 2026-07-25)
    RETRACTED the "confirmed double-fetch" framing for both cited shards, so no confirmed double-fetch exists to
    reference here; the alerting gap below stands on its own as a structural blind spot, independent of whether that
    particular instance was real) — from the actuator's point of view the relaunch "succeeded" (VM launched, ran,
    eventually either completed or was preempted again), which is indistinguishable at the INFO-severity level from a
    relaunch that correctly resumed from a checkpoint. **The current alerting has no mechanism to distinguish "resumed
    correctly" from "wastefully re-did already-captured work"** — both look identical (a non-erroring subprocess exit)
    to the actuator. This is a genuine alerting-hardening gap, not just an unmonitored condition — filed as a follow-up
    todo below.

### New follow-up todos from this session

- [ ] [BACKEND] P2. **`tradfi-bf-*` (and the shared `mtds_chunk_loop.sh` family: `mtds-backfill-tradfi-pipelinecheck`,
      `mtds-dex-swaps-backfill`, `cefi-aster`, `cefi-hyperliquid`, `cefi-queue-heavy-binancefutu-x17`, `af-backfill`)
      write no `PROGRESS.json`/`LAUNCH_PARAMS.json` checkpoint** — confirmed architectural gap (3/3 independent
      adversarial re-verification agreed), same class as `canonical-migration-defi-rebuild` below. **CORRECTED
      2026-07-25** (see the adversarial-verification note above): the two sampled shards' "restart at Chunk 1/53" was
      NOT a confirmed double-fetch of already-captured data — the predecessor VMs never actually captured any real rows
      for that chunk (an unrelated Databento combo-symbol quarantine issue, see new P3 todo below), so the atom-aware
      presence-skip layer (`_apply_preflight_skip_filter`) correctly retried genuinely- missing data. Downgraded from
      P1/"confirmed" back to P2/"bounded, theoretical" — the architecture gap is real and worth closing, but there is no
      direct evidence of actual billing waste from it yet. Wire `record_vm_progress`/`PROGRESS.json` emission into
      `_tradfi-ohlcv-launcher-lib.sh`'s `mtds_chunk_loop.sh` path (or the equivalent shared chunk-loop used by the
      sibling families above) so `relaunch_backfill_vm.py`'s existing monotonic-checkpoint resume logic (already
      implemented and working for the conformant launchers, e.g. `canonical-migration-defi-relabel`) actually engages
      instead of falling through to a blind START_DATE replay — still worth doing for defense-in-depth even though this
      run found no confirmed instance of it actually costing money. Repo: deployment-service, market-tick-data-service.
- [ ] [BACKEND] P2. **`af-backfill`'s `LAUNCH_PARAMS.json` was absent from `vm-logs/af-backfill-20260718-141638/`**
      despite `launch-api-football-backfill-vm.sh` calling `lc_write_launch_params` at create time and
      `exit_code_fleet_monitor.py` sourcing the SPOT-preemption relaunch actuator's `launch_env` from exactly that file
      (`_gcs.read_launch_params`). This launcher's `--force` full-history mode (`--start-date 2019-01-01 ... --force`)
      is the documented dangerous case (`force_run_not_replayable` → PAGE when no checkpoint). The observed relaunch DID
      advance its start date (`2019-01-01` → `2019-01-10`) by an unconfirmed mechanism — investigate whether this is a
      genuine resume path outside the generic `LAUNCH_PARAMS.json`/`PROGRESS.json` contract (e.g. an
      entity-level/manifest-derived resume specific to `instruments_service --operation instruments`), or whether
      `lc_write_launch_params`'s "best-effort, non-fatal" write is silently failing for this launcher and the observed
      advance was coincidental (e.g. an operator-adjusted manual relaunch, not the automated actuator). Repo:
      deployment-service.
- [ ] [BACKEND] P3. **Verify `exit_code_fleet_monitor.py`'s `read_progress_checkpoint()` recognizes
      `canonical-migration-cefi-cdlap`'s non-standard checkpoint filename** (`MIGRATION_PROGRESS-shard{N}.json`, not
      literally `PROGRESS.json`) — the launcher writes a real, functionally-conformant checkpoint
      (`last_processed_line_index`/`shard_index`/`shard_of`), but if the generic actuator only globs for the standard
      filename, this checkpoint may exist on disk yet never actually be consulted on relaunch (silent, not loud). Either
      generalize the reader's filename pattern or document this as an accepted per-launcher naming exception in
      `/codex/05-infrastructure/spot-vms-for-backfill.md`. Repo: deployment-service.
- [ ] [BACKEND] P3. **Harden the preemption-relaunch alert to distinguish "resumed correctly" from "wastefully
      replayed"** — `relaunch_backfill_vm.py` emits the same quiet `DP_VM_PREEMPTED` (INFO, no page) for both a
      genuinely-successful checkpoint-resumed relaunch and a blind START_DATE replay that re-does already-captured work
      (the `tradfi-bf-*`-shaped case above — note its "confirmed" label was RETRACTED by this doc's own 2026-07-25
      adversarial-verification banner; corrected 2026-07-26, `/plan-reconcile` infra shard. The gap is structural and
      real regardless: the actuator genuinely cannot tell the two apart, so a REAL instance would be just as silent). A
      future wave of such a replay would page just as silently. Candidate approach: compare the relaunched VM's per-VM
      manifest shard row-count growth against its wall-clock runtime/expected shard size, or downgrade `DP_VM_PREEMPTED`
      to WARN-and-flag whenever `launch_env` had no usable checkpoint AND the run was not `--force` (the exact
      silent-gap condition). Repo: deployment-service.
- [ ] [BACKEND] P3. **`canonical-migration-defi-pi-range` and `canonical-migration-defi-per-instrument` write no
      checkpoint at all** (not even the manifest-shard-only pattern `canonical-migration-defi-rebuild` uses) and
      produced this audit's largest observed `run.log`s (731 MB / 79 MB) — fold into the P2 `PROGRESS.json` rollout
      above rather than treating as a separate design. Repo: deployment-service.
- [ ] [SCRIPT] P3. **Check whether CME BTC/ETH options (OPT atom) coverage is intentionally excluded or a silent gap** —
      surfaced by the 2026-07-25 adversarial verification of the `tradfi-bf-*` finding above: the
      `cme-ohlcv-1m-btc-2020`/`eth-2022` predecessor VMs' launches expected 2 atoms (FUT+OPT) and hit
      `[DATABENTO_FETCH_FAILED] ... underlying='BTC'/'ETH' is not a real product root ... quarantine, never     fake-canonicalize`
      for the OPT atom on every attempt (0 rows, by design — the quarantine behavior itself looks correct, not a bug).
      The SUCCESSOR VMs' launches expected only 1 atom (FUT-only) and succeeded. Not independently confirmed this run:
      was dropping the OPT atom a deliberate decision (BTC/ETH CME options use a different root symbol this launcher
      should resolve instead of quarantining, or are genuinely out of MVP scope), or did something silently narrow the
      "expected atoms" set between launches without anyone deciding that on purpose? If the latter, CME BTC/ETH options
      coverage may have quietly gone from "expected, failing" to "no longer expected" rather than being fixed. Repo:
      market-tick-data-service, instruments-service.

- **2026-07-25 (third session) — adversarial verification of the `tradfi-bf-*` "CONFIRMED double-fetch" finding: 3/3
  independent refuters REFUTED it.** Given the finding's severity (P1, real vendor billing $ implications) and its
  potential to trigger an operator escalation, ran a 3-agent independent adversarial-verification Workflow before
  trusting it — each agent re-pulled the raw GCS `run.log`s from scratch and tried to find an innocent explanation. All
  3 found the same one, independently: the predecessor VMs never captured any real rows for the cited chunk
  (`total_records=0 complete=False` on every attempt, root-caused to an unrelated Databento combo-symbol quarantine
  issue), so the successor's "restart at Chunk 1/53" was a correct retry of genuinely-missing data, not a double-fetch
  of already-captured data. Corrected the finding above (P1→P2, "confirmed"→"bounded/ theoretical", matching
  `canonical-migration-defi-rebuild`'s classification) and filed the quarantine-behavior observation as its own new P3
  todo. **This audit's own methodology lesson, worth carrying forward**: a "chunk-loop restarted at chunk N" symptom is
  not sufficient evidence of waste on its own — always grep the actual `total_records=`/`complete=` values for the
  specific chunk before calling a re-fetch confirmed, since a genuinely-empty predecessor attempt looks identical to a
  genuinely-wasted one at the chunk-marker level alone.
