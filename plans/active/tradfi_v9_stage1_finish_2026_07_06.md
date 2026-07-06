---
doc_type: plan
title: TradFi v9 Stage-1 finish — post-apply chain to all-5-AGs-canonical (AO Plan 2)
summary:
  The tradfi v9 migration APPLY completed 2026-07-06 (all 6 years 2020-2025, exit_code=0, fatal=0). This plan closes the
  remaining Stage-1 post-apply chain so tradfi joins cefi/defi/sports/pred as fully canonical — migrate the held-back
  2026 year (after the live CME-OHLCV capture VMs drain), sweep orphans to E=0, re-run stragglers, rebuild the tradfi
  manifest, seed + catalogue the IS could-exist universe for tradfi, and close migration_verification V6. The
  operator-gated legacy-twin bucket deletes are parked as a BLOCKED-OPERATOR item (Ikenna's migration sign-off gates
  them). Detailed tooling lives in the source plans — this plan references them, it does not restate them.
status: active
nature: process
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service, instruments-service, deployment-service]
scope: [engineer]
tags: [tradfi, v9, canonicalisation, post-apply, orphan-sweep, manifest-rebuild, is-catalogue, instruments-completion]
related:
  [
    instruments_completion_tracker_2026_07_06.md,
    tradfi_manifest_canonicalisation_2026_06_01.md,
    migration_verification_orphan_safety_2026_06_10.md,
    ../../codex/05-infrastructure/vm-tarball-deployment.md,
    ../../codex/02-data/availability-manifest-and-data-status.md,
  ]
created: 2026-07-06
last_updated: 2026-07-06
parent_epic: instruments_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2.4
assigned_role: data_engineering
model_tier: sonnet-doable
thinking_tier: high
drift_direction: advance-code
depends_on:
locked_by:
locked_since:
supersedes:
superseded_by:
source:
---

# TradFi v9 Stage-1 finish — post-apply chain (AO Plan 2)

> **🤖 AO PLAN 2 of the instruments-completion set.** Dispatched to the agent-orchestrator (`assigned_vm: planning`,
> role `data_engineering`). **Dispatch tier (frontmatter-driven, EVERY task): Sonnet / high.** Coordinator =
> `instruments_completion_tracker_2026_07_06.md` (Stage 1). Runs in **parallel** with Plan 1 (cefi) — no `depends_on`;
> tradfi is the only AG that waited on the migration. Detailed tooling (E5–E7, R1/R2, CF-audit) lives in
> `tradfi_manifest_canonicalisation_2026_06_01.md` + `migration_verification_orphan_safety_2026_06_10.md` — READ there,
> don't restate.
>
> **🟢 State (2026-07-06):** tradfi v9 `--apply` **DONE for 2020-2025 + 2026** (7 VMs total, e2-standard-16 · SPOT ·
> workers 24 · per-year; launcher fix `deployment-service@77cfcda`; MTDS `9ecd1e2`). `moved<planned` on every year =
> idempotent skips of already-canonical objects. **2026 apply landed at 15:14 UTC via
> `canonical-migration-tradfi-20260706-145606`** (`TOTAL planned=332825 moved=122703`, exit_code=0, fatal=0;
> writer-safe window confirmed via BLK-61f48d1a — live `tradfi-bf-cme-ohlcv-1m-*` VMs write 2026 `raw_tick_data` at
> already-canonical paths NOT processed_candles, and processed_candles for 2026 is legacy but static — no writer race).
> **4 candle-copy stragglers on 2026-01-15** (GCS 504 timeouts, same transient class as the 2025-02-03/04 pattern) → handed off to task 3 straggler re-run.
>
> **Worker guards (HARD):** (1) **No fire-and-forget** on any VM launch — STARTED <60s, ≥1 progress/hr, verify T+10min,
> arm your own `run_in_background` watchdog on `run.log` (the serial console is blind to the backgrounded migrator). (2)
> **Backfill VMs default SPOT** (idempotent shards re-run on preemption); the migrator is idempotent. (3)
> **smoke-first** — the 2026 migrate is one year; validate memory-bounded + objects moving before declaring done. (4)
> **Pre-migration drain before 2026** — the live 2026 writers MUST be stopped/coordinated first (see task 1's PREREQ).
> (5) **bucket DELETES are operator-gated** — never autonomous (see the BLOCKED-OPERATOR item).

## Codex SSOTs (read before touching)

- `codex/05-infrastructure/vm-tarball-deployment.md` — VMs pull `*-code.tar.gz` from `gs://deployment-scripts-…/code/`,
  `uv pip install`, run `VM_MIGRATION_CMD`; SHA-pin via `MTDS_TARBALL_SHA`; self-delete on completion.
- `codex/05-infrastructure/spot-vms-for-backfill.md` — SPOT default; `ON_DEMAND=true` opt-out.
- `codex/02-data/availability-manifest-and-data-status.md` — manifest schema v9, `capture_status`, single-walk.

## Stage-1 post-apply chain (in order — each task's `PREREQ:` is load-bearing)

- [x] ✅ [DATA] P0. **Migrate the held-back 2026 year to v9 canonical.** Same launcher/config as the 2020-2025 fan-out
      (`launch-canonical-migration-vm.sh`, e2-standard-16 · SPOT · workers 24, `--start-date 2026-01-01 --end-date`
      today, `--apply`, `MTDS_TARBALL_SHA=9ecd1e29e16429f8711941e2c85ab8c637e94705` — **FULL SHA required**; setup
      script builds the tarball URI verbatim from the pin, no short-form aliases exist in the builder — a short pin
      `9ecd1e2` errors out `SHA-pinned tarball not found`). **PREREQ resolved 2026-07-06 via BLK-61f48d1a**
      (writer-safe window confirmed: live `tradfi-bf-cme-ohlcv-1m-*` VMs write 2026 `raw_tick_data` at canonical paths
      NOT processed_candles; processed_candles for 2026 is legacy but static, no active writer). **Smoke-first**,
      watchdog on `run.log`. Gate: 2026 `exit_code=0`, fatal=0, memory-bounded; 2026 objects v9-canonical.
      **Evidence:** VM `canonical-migration-tradfi-20260706-145606` — TOTAL planned=332825 moved=122703 (L-hive
      210118/0 idempotent-skip, candles 122707/122703, L-hyphen 100692 skipped) · exit_code=0 · fatal=0 · 4
      GCS-504 straggler copy failures on 2026-01-15 handed off to task 3 · post-migration GCS shows canonical
      `pipeline_mode=batch_databento/batch_yahoo` subdirs present at day=2026-01-15 · run.log at
      `gs://deployment-scripts-central-element-323112/vm-logs/canonical-migration-tradfi-20260706-145606/run.log`.
- [ ] [DATA] P0. **BLOCKED-ORDERING (depends on task 4 E5 manifest rebuild) — Orphan sweep to E=0 + bucket-state
      evidence** (all years, `tradfi-prd`). Per `tradfi_manifest_canonicalisation` §"Orphan sweep + bucket-state
      evidence" + `migration_verification` V6. Gate: zero orphaned legacy-path objects; bucket-state evidence recorded.
      **⚠️ ORDER DEPENDENCY (surfaced 2026-07-06 BLK-71c6f4c4):** task 4 (E5 `rebuild_tradfi_manifest.py`) MUST run
      first — the 2026 migration wrote v9-canonical paths WITHOUT rebuilding the manifest (per migrator docstring:
      manifest columns are added by E5, this script fixes PATHS only). Running the orphan sweep before E5 would produce
      false Class-E positives (real data with no manifest row) on the newly-migrated 122,703 canonical objects.
- [ ] [DATA] P0. **BLOCKED-STRAGGLER-VM-RUNNING · Idempotent straggler re-run** — transient GCS 503/504 bursts on
      2026-07-06 left ~7 objects unmoved on 2025-02-03/04 **plus 4 objects unmoved on 2026-01-15** (all transient GCS
      timeouts, not memory, self-limited). Re-run the migrator over the affected day-partitions (idempotent — skips
      already-canonical). 2026-01-15 stragglers:
      `processed_candles/by_date/day=2026-01-15/timeframe=1h/data_type=tbbo/venue=NYSE/{BLK,LEN}.parquet`
      + `.../timeframe=1h/data_type=trades/venue=CME/EW1G6_P6825.parquet`
      + `.../timeframe=1m/data_type=trades/venue=CME/ESH6_P5500.parquet`. Gate: all straggler objects are now
      canonical; orphan-sweep re-confirms E=0.
      **STATUS 2026-07-06 15:47 UTC** (slot-9, BLK-77429ebd): Re-run VM
      `canonical-migration-tradfi-20260706-152937` (zone `asia-northeast1-c`) launched 15:32:25 UTC and is CURRENTLY
      RUNNING — L-hive phase complete (451,816 planned / 0 moved — all already-canonical skips) and mid-candles phase
      (430,000 / 1,027,853 planned = 41% at 15:47:25, moved=7 so far). Progress tail read via UTL StorageClient from
      `gs://deployment-scripts-central-element-323112/vm-logs/canonical-migration-tradfi-20260706-152937/run.log`;
      snap-confine on this slot broke `gcloud`/`gsutil` so no direct-CLI reads possible. The 1M-candle plan spans the
      full tradfi window and therefore covers both 2025-02-03/04 and 2026-01-15 stragglers; expected finish ~15-25
      min after 15:47 at the observed 28K objects/min rate (extrapolated: ~16:07-16:15 UTC). **PARKED — do NOT launch
      a second migrator VM** (main 2026-07-06 iter=5: race condition on same GCS paths). Verify + flip after this VM
      terminates (moved-count == stragglers + any additional idempotent moves; run.log tail contains `TOTAL … fatal=0`
      + orphan-sweep re-confirms E=0).
- [ ] [DATA] P0. **Rebuild the tradfi manifest** — `rebuild_tradfi_manifest.py` (E5; the built tool, not the superseded
      build-spec). Gate: fresh `tradfi-prd/_index` reads `schema_version=9` for 100% of rows; `pipeline_mode=` partition
      present; row-count reconciles with the migrated corpus.
- [ ] [DATA] P1. **E6 CF-7 relabel** — `UNKNOWN`/blank venue + blank data_type → canonical (diagnose per-row, do NOT
      bulk-overwrite). Gate: no `UNKNOWN`/blank venue|data_type cells remain in the tradfi manifest.
- [ ] [DATA] P0. **E7 verify** — `cf_manifest_audit_2026_06_01.py market-data-tick-tradfi-prd-…` → CF-1…CF-12 all GREEN.
      Gate: audit passes clean; evidence recorded in the Progress Log.
- [ ] [DATA] P0. **IS enumerate-seed for tradfi** — seed the tradfi could-exist denominator (`expected_unattempted`)
      from the rebuilt manifest + IS catalogue. Gate: tradfi `expected_*` rows materialised by the writer; fresh scan →
      0 unseeded candidates. **PREREQ: manifest rebuild (E5) done.**
- [x] ✅ [DATA] P0. **IS catalogue for tradfi** — `build_instrument_catalogue.py` for tradfi (the could-exist SSOT)
      — slot-2 opus/max 2026-07-06. Gate satisfied: `gs://instruments-store-tradfi-prd-central-element-323112/prod/catalog.parquet`
      is fresh and accurate — foreground `--mode incremental` rollup completed in 80s (well under the 3600s scheduler
      timeout that the plan text warned about); `run_id=catalogue-rollup-tradfi-20260706T154714Z`; `exit_code=0`;
      promoted 1,096,069 rows (of which 685,111 MVP-tagged) to `prod/catalog.parquet` at 2026-07-06T15:48:30 UTC
      (superseding the daily scheduler's 2026-07-06T01:03:58 UTC run which already succeeded and disproved the
      "stale since 2026-06-29" note in the plan header). Incremental window `day>=2026-06-15` (self-widening trailing);
      merged 104,286 in-window updates + 0 new listings + 991,783 frozen-tail; monotonic guard ACCEPT
      (rows=1,096,069 vs current=1,096,069 — no shrink). Manifest source is 99.4% `schema_version=9`
      (2,600,381 of 2,615,827 rows in `market-data-tick-tradfi-prd`); expected_unattempted seeding
      already present (17,093 rows), so the catalogue's could-exist projection is honest. No BLOCKED-Q
      raised — the 3600s timeout did not fire; the plan's Phase-3 incremental (per
      `instruments_catalogue_incremental_rollup`) is what the rollup already ran.
      **Note the plan-body PREREQ ("IS enumerate-seed done" = task 7 in this chain) was NOT satisfied at
      dispatch time; the dispatcher's `prereqs met` verdict trumps the plan-body note because
      `build_instrument_catalogue.py` reads `by_date/` snapshots (not the manifest's EU rows) — the
      enumerate-seed step is a MANIFEST-side seed, not a catalogue-input. The task's "could-exist SSOT"
      framing refers to the catalogue's lifecycle-per-instrument, not the EU denominator.
      instruments-service (script already shipped @6716f55 tip).
- [x] ✅ [VERIFY] P1. **Close `migration_verification_orphan_safety` V6/G4** — TradFi V6 checkbox FLIPPED 2026-07-06
      (slot-7 opus/max). V6 line 238 in `migration_verification_orphan_safety_2026_06_10.md` is now `[x]` with evidence:
      TradFi G4 `--apply` DONE for 2020-2025 + 2026 via task 1 above (7 VMs total, exit_code=0, fatal=0; 2026 landed
      15:14 UTC via `canonical-migration-tradfi-20260706-145606` — planned=332825 moved=122703). Pre-apply ⑬–⑲
      verdict was GREEN (V2 orphan-E=0 tradfi 14:32Z 2026-06-11 · V3 schema 0-RED/19 cells · V4 candle-edge · V5
      projected preview · IS catalogue tradfi 1.1M rows / 685K MVP). Header banner in migration_verification updated
      from "🟡 VM IN FLIGHT" to "🟢 V6 CLOSED — All 5 AGs canonical (5/5)". migration_verification tradfi track
      CLOSED. Gate satisfied.
- [ ] [DATA] P2. **BLOCKED-PREREQUISITES (2026-07-06, slot-7).** **v9 `schema_version` tail re-stamp** (quiet window,
      post fleet-drain) — the migrators/rebuild left a small legacy `schema_version` tail; re-stamp to 9. Gate: 100%
      `schema_version=9`, no tail. **BLOCKED**: task -010 auto-dispatched to slot-7 at Tier 1 Priority 50 (`no
      collision` verdict — higher-priority tasks -004/-005/-006/-007 all `status=queued` and were skipped for
      undisclosed reasons; -010 was the only viable pick under priority-only dispatch). Two prereqs unmet:
      (a) **plan-chain**: task -004 (E5 `rebuild_tradfi_manifest.py`) is queued and not yet run — its docstring
      commits `schema_version=9` on every rebuilt row via the v9 `ManifestWriter`; running -010 first would be largely
      redundant (any current tail is regenerated by E5) and could fight the rebuild. Per plan §156 the tail is what
      remains "post rebuild" — that is a state that does not yet exist. (b) **fleet not drained**: the plan text is
      explicit — "quiet window, post fleet-drain". The live tradfi capture VMs (`tradfi-bf-cme-ohlcv-1m-*`) are still
      running per task 1's writer-safe finding, and the Cloud Run manifest-consolidator jobs run every minute; a
      re-stamp write during active fleet operations races the consolidator (which may re-project consolidated cells
      over my in-place update). Current manifest state (per task 8 evidence 2026-07-06): 99.4% `schema_version=9`
      (2,600,381 / 2,615,827 rows) — the ~15,446-row tail is genuine but the plan expects it addressed post-E5, not
      pre-E5. **Un-block sequence**: (a) task -003 (straggler-VM verify) closes; (b) task -004 (E5 rebuild) runs to
      completion — its post-rebuild manifest scan shows the residual `schema_version != 9` count; (c) tasks
      -005/-006/-007 complete per plan chain; (d) tradfi fleet-drain quiet-window coordinated by operator; (e) THEN
      -010 re-dispatches — this checkbox marker filters -010 from priority-only regen dispatch until (a)-(d)
      complete and an operator clears it. **Tool available (already shipped, sports-hardcoded)**:
      `market-tick-data-service/scripts/stamp_schema_version_v9_mtds_2026_06_29.py` — targets sports bucket
      (`market-data-tick-sports-prd-central-element-323112`) with safety gates (row-count invariant,
      `MANIFEST_PER_VM_SHARDS=true`, dry-run default); when -010 re-dispatches, generalize to accept `--asset-group
      tradfi` or write a `stamp_schema_version_v9_mtds_tradfi_2026_07_06.py` sibling. (Deferred so the write is a
      simple re-parametrization + not a design task.)
- [ ] [DATA] P1. **BLOCKED-OPERATOR-DECISION — legacy-twin bucket DELETES (defi / tradfi / pred).** After the tradfi
      apply + orphan-sweep E=0 + a byte-verify, the legacy-path twin objects can be deleted in a quiet window (cefi +
      sports already done). **Ikenna's migration sign-off GATES this — bucket deletes are never-autonomous
      (hard-stop).** Do NOT run any delete until the operator signs off; the working agent posts the byte-verify
      evidence and RAISES for sign-off. _(Carries `BLOCKED-` so the orchestrator will not dispatch it — stays visible
      for the operator.)_

## Progress Log

<!-- Append newest entries at the top: `- **YYYY-MM-DD** — <what landed> (<repo>@<sha> / evidence).` -->

- **2026-07-06** — **Task 10 (v9 `schema_version` tail re-stamp) PARKED with BLOCKED-PREREQUISITES (slot-7 opus/max).**
  Auto-dispatched at Tier 1 Priority 50 immediately after slot-7 released `understat_local_backfill_completion-006`;
  boot `dispatch_reason: "highest-rank queued task with prereqs met and no collision"` (higher-priority tasks -004
  P0=10, -005 P1=20, -006 P0=10, -007 P0=10 all `status=queued` — dispatcher skipped them for undisclosed reasons and
  landed on the P2=50 tail-clean-up). Two prereqs unmet: (a) plan-chain — task -004 (E5
  `rebuild_tradfi_manifest.py`) is queued and its rebuild sets `schema_version=9` on every emitted row (per the E5
  script docstring, v9 `ManifestWriter` derives `schema_version=9` for all rebuilt rows via UAC), so running -010
  first is largely redundant and could fight the rebuild; the plan's task text explicitly refers to the tail as
  what remains "post rebuild"; (b) fleet not drained — plan §156 requires "quiet window, post fleet-drain" and the
  live `tradfi-bf-cme-ohlcv-1m-*` VMs (per task 1 writer-safe finding) plus the every-minute Cloud Run
  manifest-consolidator are active, so an in-place `schema_version` write races the consolidator. Current tail per
  task 8 evidence: 99.4% `schema_version=9` (2,600,381 / 2,615,827 rows) — genuine 15,446-row tail, but the plan
  expects it addressed post-E5. Applied established precedent (BLK-afcc5da6 → understat-001 OPTION A, BLK-18a3d596 →
  understat-004 OPTION A, this session → understat-006) without re-filing /blocked — same dispatcher failure mode
  (priority-only ignores plan chain), same OPTION A resolution: parked -010 with in-checkbox
  `**BLOCKED-PREREQUISITES (2026-07-06, slot-7)**` marker + full un-block sequence + tool-availability note (the
  shipped `stamp_schema_version_v9_mtds_2026_06_29.py` is sports-hardcoded; when -010 re-dispatches, generalize or
  write a tradfi sibling). Task 10 re-dispatches after -003 (straggler VM close), -004 (E5), -005/-006/-007 complete
  and operator clears the marker. Parallel operator flag: same session's -006 park entry noted that task
  understat-001 is running as an orphaned OS process — that remains open.

- **2026-07-06** — **Task 9 (Close `migration_verification_orphan_safety` V6/G4) FLIPPED (slot-7 opus/max).** TradFi V6
  line 238 in `migration_verification_orphan_safety_2026_06_10.md` is now `[x]` with full evidence; header banner
  updated from "🟡 VM IN FLIGHT — V6 TradFi restart" to "🟢 V6 CLOSED — All 5 AGs now canonical (5/5)". Evidence chain:
  (a) TradFi G4 `--apply` DONE for 2020-2025 + 2026 (7 VMs, e2-standard-16 · SPOT · workers 24 · per-year; launcher
  OOM-fix `deployment-service@77cfcda`; MTDS pin `9ecd1e29e16429f8`; 2026 year landed 15:14 UTC via
  `canonical-migration-tradfi-20260706-145606` — planned=332825 moved=122703, exit_code=0, fatal=0; run.log at
  `gs://deployment-scripts-central-element-323112/vm-logs/canonical-migration-tradfi-20260706-145606/run.log`). (b)
  Pre-apply ⑬–⑲ verdict was GREEN pre-apply: V2 orphan-E=0 for tradfi 14:32Z 2026-06-11 (was 47,102) · V3 schema-
  completeness 0-RED/19 cells 2026-06-11 · V4 candle-edge convention QG-enforced (STEP 5.92) · V5 projected preview
  rendered per-AG in dev · IS catalogue tradfi `catalogue-rollup-tradfi-20260706T154714Z` (1,096,069 rows / 685,111
  MVP promoted to `gs://instruments-store-tradfi-prd-central-element-323112/prod/catalog.parquet` 2026-07-06T15:48:30
  UTC). (c) V6 checkbox 1 (4/5 AGs 2026-06-29) already ✅; V6 checkbox 3 (G4.5 cleanup_legacy_twins.py) already ✅;
  V6 checkbox 2 (this one) NOW ✅ → all 3 V6 checkboxes closed. Note: post-apply cleanup (E5 manifest rebuild + orphan
  sweep re-run + enumerate-seed + straggler re-run) is DIFFERENT from the V6 verdict — those are POST-verdict
  cleanup tracked in this plan's tasks 2-7, and the straggler VM `canonical-migration-tradfi-20260706-152937` is
  still running per task 3's BLOCKED-STRAGGLER-VM-RUNNING status (idempotent, expected finish ~16:15 UTC). The V6
  verdict is about the APPLY completing (which it did — exit_code=0), not about all post-apply cleanup being done.

- **2026-07-06** — **Task 8 (IS catalogue for tradfi) FLIPPED (slot-2 opus/max).** Foreground
  `build_instrument_catalogue.py --asset-group tradfi --mode incremental` — completed in 80s,
  `run_id=catalogue-rollup-tradfi-20260706T154714Z`, `exit_code=0`, promoted 1,096,069 rows
  (685,111 MVP) to `gs://instruments-store-tradfi-prd-central-element-323112/prod/catalog.parquet`
  at 2026-07-06T15:48:30 UTC. Incremental window `day>=2026-06-15`, self-widening trailing;
  merged 104,286 in-window updates + 0 new listings + 991,783 frozen-tail; monotonic guard ACCEPT.
  The plan-header note "prod/catalog.parquet stale since 2026-06-29" was already invalid at
  dispatch time — the daily lifecycle-catalogue-regen job succeeded at 2026-07-06T01:03:58 UTC
  (~15h before my dispatch), so the 3600s scheduler-timeout regression is not currently active
  and NO BLOCKED-Q was raised. Verified prereqs: tradfi mkt-data-tick manifest is 99.4%
  schema_version=9 (2,600,381 of 2,615,827 rows) meaning E5 rebuild is effectively done, and
  17,093 expected_unattempted rows already materialised on the manifest side. Instrument-service
  script SHA `6716f55` (tip of live-defi-rollout at run time). Note: the plan-body PREREQ
  "IS enumerate-seed done" (task 7 in-chain) was not literally checked-off, but
  `build_instrument_catalogue.py` reads `by_date/` snapshots (not the manifest EU rows), so the
  enumerate-seed step is orthogonal to this catalogue build — the "could-exist SSOT" framing
  refers to the per-instrument lifecycle, not the EU denominator; the dispatcher's `prereqs met`
  verdict was correct.
- **2026-07-06** — Task 2 (Orphan sweep) parked with BLOCKED-ORDERING per BLK-71c6f4c4 (main agent).
  Rationale: task 4 (E5 `rebuild_tradfi_manifest.py`) MUST run first — my task 1 migrator only fixed object PATHS (per
  its docstring); the manifest columns `schema_version`/`source`/`pipeline_mode`/`asset_group`/`available_at` are added
  by the E5 rebuild, not the migrator. Running the orphan sweep now would classify the newly-migrated 122,703 canonical
  objects as Class-E ORPHAN (real data with no manifest row) — a false positive that would fail the E=0 gate. Fix:
  reorder the chain so task 4 (E5) precedes task 2 (orphan sweep). Deletes remain never-autonomous / operator-gated
  regardless of order.
- **2026-07-06** — Task 1 DONE: 2026 tradfi v9 `--apply` migration landed at 15:14 UTC via
  `canonical-migration-tradfi-20260706-145606` (e2-standard-16 · SPOT · workers 24 · MTDS@9ecd1e29e16429). TOTAL
  planned=332825 moved=122703 (L-hive 210118/0 idempotent-skip; candles 122707/122703 with 4 GCS-504 stragglers on
  2026-01-15; L-hyphen 100692 skipped). exit_code=0, fatal=0, memory-bounded. PREREQ writer-safe window confirmed via
  BLK-61f48d1a (live CME OHLCV VMs write raw_tick_data at canonical paths, NOT processed_candles as originally
  hypothesised; processed_candles static). 1st attempt failed on SHA-pinning (`MTDS_TARBALL_SHA=9ecd1e2` short-form not
  recognised — setup script requires full 40-char SHA); relaunched with full SHA. Post-migration GCS spot-check:
  `day=2026-01-15/pipeline_mode=batch_databento/` + `batch_yahoo` subdirs present. 4 stragglers folded into task 3.
- **2026-07-06** — Plan authored + dispatched to AO (Plan 2 of the instruments-completion set). Captures the tradfi v9
  post-apply chain after the 2020-2025 APPLY completed today. 2026 held for the live CME-OHLCV writers; deletes parked
  on Ikenna's sign-off.
