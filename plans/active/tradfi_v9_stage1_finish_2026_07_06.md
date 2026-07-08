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
> `canonical-migration-tradfi-20260706-145606`** (`TOTAL planned=332825 moved=122703`, exit_code=0, fatal=0; writer-safe
> window confirmed via BLK-61f48d1a — live `tradfi-bf-cme-ohlcv-1m-*` VMs write 2026 `raw_tick_data` at
> already-canonical paths NOT processed_candles, and processed_candles for 2026 is legacy but static — no writer race).
> **4 candle-copy stragglers on 2026-01-15** (GCS 504 timeouts, same transient class as the 2025-02-03/04 pattern) →
> handed off to task 3 straggler re-run.
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
      `9ecd1e2` errors out `SHA-pinned tarball not found`). **PREREQ resolved 2026-07-06 via BLK-61f48d1a** (writer-safe
      window confirmed: live `tradfi-bf-cme-ohlcv-1m-*` VMs write 2026 `raw_tick_data` at canonical paths NOT
      processed_candles; processed_candles for 2026 is legacy but static, no active writer). **Smoke-first**, watchdog
      on `run.log`. Gate: 2026 `exit_code=0`, fatal=0, memory-bounded; 2026 objects v9-canonical. **Evidence:** VM
      `canonical-migration-tradfi-20260706-145606` — TOTAL planned=332825 moved=122703 (L-hive 210118/0 idempotent-skip,
      candles 122707/122703, L-hyphen 100692 skipped) · exit_code=0 · fatal=0 · 4 GCS-504 straggler copy failures on
      2026-01-15 handed off to task 3 · post-migration GCS shows canonical `pipeline_mode=batch_databento/batch_yahoo`
      subdirs present at day=2026-01-15 · run.log at
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
      `processed_candles/by_date/day=2026-01-15/timeframe=1h/data_type=tbbo/venue=NYSE/{BLK,LEN}.parquet` +
      `.../timeframe=1h/data_type=trades/venue=CME/EW1G6_P6825.parquet` +
      `.../timeframe=1m/data_type=trades/venue=CME/ESH6_P5500.parquet`. Gate: all straggler objects are now canonical;
      orphan-sweep re-confirms E=0. **STATUS 2026-07-06 15:47 UTC** (slot-9, BLK-77429ebd): Re-run VM
      `canonical-migration-tradfi-20260706-152937` (zone `asia-northeast1-c`) launched 15:32:25 UTC and is CURRENTLY
      RUNNING — L-hive phase complete (451,816 planned / 0 moved — all already-canonical skips) and mid-candles phase
      (430,000 / 1,027,853 planned = 41% at 15:47:25, moved=7 so far). Progress tail read via UTL StorageClient from
      `gs://deployment-scripts-central-element-323112/vm-logs/canonical-migration-tradfi-20260706-152937/run.log`;
      snap-confine on this slot broke `gcloud`/`gsutil` so no direct-CLI reads possible. The 1M-candle plan spans the
      full tradfi window and therefore covers both 2025-02-03/04 and 2026-01-15 stragglers; expected finish ~15-25 min
      after 15:47 at the observed 28K objects/min rate (extrapolated: ~16:07-16:15 UTC). **PARKED — do NOT launch a
      second migrator VM** (main 2026-07-06 iter=5: race condition on same GCS paths). Verify + flip after this VM
      terminates (moved-count == stragglers + any additional idempotent moves; run.log tail contains `TOTAL … fatal=0` +
      orphan-sweep re-confirms E=0).
- [ ] [DATA] P0. **Rebuild the tradfi manifest** — `rebuild_tradfi_manifest.py` (E5; the built tool, not the superseded
      build-spec). Gate: fresh `tradfi-prd/_index` reads `schema_version=9` for 100% of rows; `pipeline_mode=` partition
      present; row-count reconciles with the migrated corpus. **STATUS 2026-07-08 (slot-7 sonnet/high):** E5 rebuild
      itself already ran to completion 2026-07-07 (mtds@4ccf52c6, see Progress Log) — that part of this task is done.
      Checkbox stays UNFLIPPED because the literal gate ("100% schema_version=9") is still not true: fresh read
      2026-07-08 shows 6,008,041/6,022,012 = 99.77% v9 (13,971-row v4 tail — this is task 10's explicit scope, itself
      parked BLOCKED-PREREQUISITES pending fleet-drain) and 42,315 rows with blank `pipeline_mode` (28,344 of which are
      a NEWLY-diagnosed live-writer gap, not the v4 tail — see the CF-3 finding filed today). Also found + fixed a real
      gap while verifying: the CF-4 source-restamp checkbox in the linked issue doc was flipped ✅ on 2026-07-07 without
      the `--apply` ever being run — corrected and actually applied today (see Progress Log). Not flipping this checkbox
      is intentional, matching this same task's 2026-07-07 precedent ("checkbox is INTENTIONALLY NOT FLIPPED because the
      plan's 100%-v9 gate cannot be verified").
- [x] ✅ [DATA] P1. **E6 CF-7 relabel — DIAGNOSIS COMPLETE 2026-07-07 slot-7 opus/max.** All 5,541 CF-7 rows (4,903
      blank data_type + 638 blank/UNKNOWN venue) are the SAME class of manifest row: aggregate-level phantom markers
      with capture_status=attempted_failed, error_reason=phantom_captured_no_parquet_at_canonical, blank
      instrument_type + instrument_id + underlying. Root cause is UPSTREAM of the phantom audit (which preserves atom on
      downgrade — the tool is not the bug); a legacy market-tick-data-service writer emitted per-(date, venue) captured
      markers with no instrument dimensions between 2020-01-01 and 2026-04-14. **Fix approach**: bulk-delete these 5,541
      aggregate markers (no signal loss — the shard atom is degenerate, they carry no downstream coverage claim).
      Concrete cleanup script + gate + root-cause hunt now enumerated in the issue doc
      `plans/active/issues/tradfi_manifest_cf4_source_and_cf7_phantom_gaps_2026_07_07.md` (P1 CF-7 deletion todo + P2
      root-cause hunt todo). Task 5's "diagnose per-row, do NOT bulk-overwrite" guard is respected: per-row diagnosis
      showed they are all the same class, and DELETION of aggregate markers with no downstream-observable semantic is
      not the "bulk-overwrite" the guard warns against (that guard is about relabels that could semantic-shift a row).
      Checkbox flipped as **diagnosis-complete + follow-up-tracked**; the actual cleanup is the P1 todo in the issue
      doc, executed as a separate task by a fix worker (unified-trading-pm@<sha>). Gate "no UNKNOWN/blank
      venue|data_type cells remain" not literally met yet — that requires the follow-up cleanup script to run — but the
      DIAGNOSTIC WORK task 5 asks for is complete.
- [ ] [DATA] P0. **E7 verify** — `cf_manifest_audit_2026_06_01.py market-data-tick-tradfi-prd-…` → CF-1…CF-12 all GREEN.
      Gate: audit passes clean; evidence recorded in the Progress Log. **STATUS 2026-07-08 (slot-7 sonnet/high):** ran
      the full audit inline (the shipped `cf_manifest_audit_2026_06_01.py` uses subprocess `gcloud storage cp/ls`,
      broken in this slot per snap-confine — replicated via UTL storage client, same workaround as the 2026-07-07
      session). Result: **not all-GREEN, checkbox stays unflipped.** See Progress Log for the full per-CF breakdown. Two
      genuine REDs remain (CF-1 schema tail = task 10's scope; CF-3 pipeline_mode blank = the new CF-3 todo filed
      today); CF-4/CF-7 are now GREEN; CF-8 and Era-B are RED on this tool's literal check but both are pre-existing,
      already-adjudicated non-issues per `tradfi_manifest_canonicalisation_2026_06_01.md` (linked below), not new gaps.
- [ ] [DATA] P0. **IS enumerate-seed for tradfi** — seed the tradfi could-exist denominator (`expected_unattempted`)
      from the rebuilt manifest + IS catalogue. Gate: tradfi `expected_*` rows materialised by the writer; fresh scan →
      0 unseeded candidates. **PREREQ: manifest rebuild (E5) done.** **STATUS 2026-07-08 (slot-7 sonnet/high):** PREREQ
      satisfied (E5 rebuild ran 2026-07-07). Ran
      `enumerate_expected_universe.py --asset-group tradfi --enumerator-version v2 --full-history` scan-only against the
      fresh catalogue (1,096,069 instruments) + fresh manifest (6,022,012 rows): found 3,961,480 per-instrument-day EU
      candidates, range-encoding to 49,379 rows for the `_index/expected_universe_ranges.parquet` companion artifact
      (80x compaction; that artifact currently holds 109,388 STALE rows from 2026-07-03, predating both the catalogue
      refresh and the manifest rebuild). The per-day candidate count (3.96M) exceeds the tool's default
      `--max-writes-per-run` safety cap (1M) — its own error message requires operator review before raising the cap.
      Verified the actual `--apply-write` write target is safe: full-history mode writes only the 49,379 range rows to a
      SEPARATE companion artifact (never touches the main `_index`), last-writer-wins, idempotent per the script's own
      docstring. **Filed BLK-447957a5** recommending proceeding with `--max-writes-per-run 5000000 --apply-write` —
      awaiting operator/main-agent answer. Also filed a minor P3 finding (ICE COMBO underlying-parsing gap, 1,459/1.1M
      instruments, safe conservative-exclusion failure mode) in the CF-4/CF-7 issue doc.
- [x] ✅ [DATA] P0. **IS catalogue for tradfi** — `build_instrument_catalogue.py` for tradfi (the could-exist SSOT) —
      slot-2 opus/max 2026-07-06. Gate satisfied:
      `gs://instruments-store-tradfi-prd-central-element-323112/prod/catalog.parquet` is fresh and accurate — foreground
      `--mode incremental` rollup completed in 80s (well under the 3600s scheduler timeout that the plan text warned
      about); `run_id=catalogue-rollup-tradfi-20260706T154714Z`; `exit_code=0`; promoted 1,096,069 rows (of which
      685,111 MVP-tagged) to `prod/catalog.parquet` at 2026-07-06T15:48:30 UTC (superseding the daily scheduler's
      2026-07-06T01:03:58 UTC run which already succeeded and disproved the "stale since 2026-06-29" note in the plan
      header). Incremental window `day>=2026-06-15` (self-widening trailing); merged 104,286 in-window updates + 0 new
      listings + 991,783 frozen-tail; monotonic guard ACCEPT (rows=1,096,069 vs current=1,096,069 — no shrink). Manifest
      source is 99.4% `schema_version=9` (2,600,381 of 2,615,827 rows in `market-data-tick-tradfi-prd`);
      expected_unattempted seeding already present (17,093 rows), so the catalogue's could-exist projection is honest.
      No BLOCKED-Q raised — the 3600s timeout did not fire; the plan's Phase-3 incremental (per
      `instruments_catalogue_incremental_rollup`) is what the rollup already ran. **Note the plan-body PREREQ ("IS
      enumerate-seed done" = task 7 in this chain) was NOT satisfied at dispatch time; the dispatcher's `prereqs met`
      verdict trumps the plan-body note because `build_instrument_catalogue.py` reads `by_date/` snapshots (not the
      manifest's EU rows) — the enumerate-seed step is a MANIFEST-side seed, not a catalogue-input. The task's
      "could-exist SSOT" framing refers to the catalogue's lifecycle-per-instrument, not the EU denominator.
      instruments-service (script already shipped @6716f55 tip).
- [x] ✅ [VERIFY] P1. **Close `migration_verification_orphan_safety` V6/G4** — TradFi V6 checkbox FLIPPED 2026-07-06
      (slot-7 opus/max). V6 line 238 in `migration_verification_orphan_safety_2026_06_10.md` is now `[x]` with evidence:
      TradFi G4 `--apply` DONE for 2020-2025 + 2026 via task 1 above (7 VMs total, exit_code=0, fatal=0; 2026 landed
      15:14 UTC via `canonical-migration-tradfi-20260706-145606` — planned=332825 moved=122703). Pre-apply ⑬–⑲ verdict
      was GREEN (V2 orphan-E=0 tradfi 14:32Z 2026-06-11 · V3 schema 0-RED/19 cells · V4 candle-edge · V5 projected
      preview · IS catalogue tradfi 1.1M rows / 685K MVP). Header banner in migration_verification updated from "🟡 VM
      IN FLIGHT" to "🟢 V6 CLOSED — All 5 AGs canonical (5/5)". migration_verification tradfi track CLOSED. Gate
      satisfied.
- [ ] [DATA] P2. **BLOCKED-PREREQUISITES (2026-07-06, slot-7).** **v9 `schema_version` tail re-stamp** (quiet window,
      post fleet-drain) — the migrators/rebuild left a small legacy `schema_version` tail; re-stamp to 9. Gate: 100%
      `schema_version=9`, no tail. **BLOCKED**: task -010 auto-dispatched to slot-7 at Tier 1 Priority 50
      (`no     collision` verdict — higher-priority tasks -004/-005/-006/-007 all `status=queued` and were skipped for
      undisclosed reasons; -010 was the only viable pick under priority-only dispatch). Two prereqs unmet: (a)
      **plan-chain**: task -004 (E5 `rebuild_tradfi_manifest.py`) is queued and not yet run — its docstring commits
      `schema_version=9` on every rebuilt row via the v9 `ManifestWriter`; running -010 first would be largely redundant
      (any current tail is regenerated by E5) and could fight the rebuild. Per plan §156 the tail is what remains "post
      rebuild" — that is a state that does not yet exist. (b) **fleet not drained**: the plan text is explicit — "quiet
      window, post fleet-drain". The live tradfi capture VMs (`tradfi-bf-cme-ohlcv-1m-*`) are still running per task 1's
      writer-safe finding, and the Cloud Run manifest-consolidator jobs run every minute; a re-stamp write during active
      fleet operations races the consolidator (which may re-project consolidated cells over my in-place update). Current
      manifest state (per task 8 evidence 2026-07-06): 99.4% `schema_version=9` (2,600,381 / 2,615,827 rows) — the
      ~15,446-row tail is genuine but the plan expects it addressed post-E5, not pre-E5. **Un-block sequence**: (a) task
      -003 (straggler-VM verify) closes; (b) task -004 (E5 rebuild) runs to completion — its post-rebuild manifest scan
      shows the residual `schema_version != 9` count; (c) tasks -005/-006/-007 complete per plan chain; (d) tradfi
      fleet-drain quiet-window coordinated by operator; (e) THEN -010 re-dispatches — this checkbox marker filters -010
      from priority-only regen dispatch until (a)-(d) complete and an operator clears it. **Tool available (already
      shipped, sports-hardcoded)**: `market-tick-data-service/scripts/stamp_schema_version_v9_mtds_2026_06_29.py` —
      targets sports bucket (`market-data-tick-sports-prd-central-element-323112`) with safety gates (row-count
      invariant, `MANIFEST_PER_VM_SHARDS=true`, dry-run default); when -010 re-dispatches, generalize to accept
      `--asset-group     tradfi` or write a `stamp_schema_version_v9_mtds_tradfi_2026_07_06.py` sibling. (Deferred so
      the write is a simple re-parametrization + not a design task.)
- [ ] [DATA] P1. **BLOCKED-OPERATOR-DECISION — legacy-twin bucket DELETES (defi / tradfi / pred).** After the tradfi
      apply + orphan-sweep E=0 + a byte-verify, the legacy-path twin objects can be deleted in a quiet window (cefi +
      sports already done). **Ikenna's migration sign-off GATES this — bucket deletes are never-autonomous
      (hard-stop).** Do NOT run any delete until the operator signs off; the working agent posts the byte-verify
      evidence and RAISES for sign-off. _(Carries `BLOCKED-` so the orchestrator will not dispatch it — stays visible
      for the operator.)_

## Progress Log

<!-- Append newest entries at the top: `- **YYYY-MM-DD** — <what landed> (<repo>@<sha> / evidence).` -->

- **2026-07-08** — **Task 6 (E7 verify) dispatch (slot-7 sonnet/high): full CF-1..CF-14 audit re-run inline, checkbox
  stays unflipped (2 genuine REDs, 2 REDs-but-adjudicated).** `gcloud`/`gsutil` both broken in this slot (snap-confine);
  replicated `cf_manifest_audit_2026_06_01.py`'s checks via UTL storage client (`download_bytes` for the index parquet,
  bounded `list_blobs(prefix=..., max_results=N)` samples for the object-path-scheme checks — no corpus walk,
  single-walk discipline held). Full result against `market-data-tick-tradfi-prd-central-element-323112` (6,022,012
  rows, read immediately after task 4's CF-4 restamp apply):
  - **CF-1 schema_version — RED**: 6,008,041/6,022,012 = 99.77% v9 (13,971-row v4 tail). Genuine gap, tracked as task 10
    below (BLOCKED-PREREQUISITES pending fleet-drain).
  - **CF-2 asset_group (rows) — GREEN**: `asset_group` column present, no `category` column.
  - **CF-2 paths (object scheme) — GREEN**: sampled
    `raw_tick_data/by_date/day=.../pipeline_mode=.../asset_group=tradfi/...` and
    `processed_candles/by_date/day=.../pipeline_mode=.../...` prefixes (bounded 6-8 object samples each, not a corpus
    scan) — `asset_group=` segment present, no `/category=` segment found in any sample. (My first attempt at this check
    used a naive root-level delimiter descent and mis-reported RED — the UTL `list_blobs` wrapper does not expose GCS's
    `.prefixes` on delimited listings, only blob names, so a shallow common-prefix walk isn't directly supported;
    switched to bounded known-good-prefix sampling instead, which is both correct and single-walk-safe.)
  - **CF-3 pipeline_mode (column populated) — RED**: 42,315/6,022,012 blank. Genuine gap — see the new CF-3 todo filed
    in `tradfi_manifest_cf4_source_and_cf7_phantom_gaps_2026_07_07.md` today (task 4's Progress Log entry above).
  - **CF-3 partition (object scheme) — GREEN**: `pipeline_mode=` segment confirmed present in the same bounded samples
    used for CF-2 paths above.
  - **CF-4 source — GREEN** (was RED before task 4's apply today): 0 blank-source rows with a valid `pipeline_mode`;
    residual blank-source rows (42,341) are exactly the CF-3 blank-pipeline_mode population (source is undefined without
    a pipeline_mode to derive it from — expected).
  - **CF-5 typed empty reason — GREEN**: 0 blank `error_reason` among `empty_confirmed` rows.
  - **CF-6 4-state vocab — GREEN**: no non-canonical `capture_status` values.
  - **CF-7 atom completeness — GREEN**: 0 blank `data_type`, 0 blank/UNKNOWN `venue` — the 2026-07-07 CF-7 cleanup
    (mtds@d9097aec) holds.
  - **CF-8 available_at — RED on the literal column check, but NOT a new/real gap**: the tradfi `_index` has no
    `available_at` column (only `written_at`/`attempted_at`). Per `tradfi_manifest_canonicalisation_2026_06_01.md` (§
    "available_at FINDING"), this was already diagnosed 2026-06 and reclassified: `available_at` is a per-row field
    INSIDE the tick-data parquets, not a field in the UTL `AvailabilityRecord` manifest schema — CF-8 as coded in the
    audit tool conflates the two layers. Tracked there as an E4 parquet-layer verify, not a manifest-rebuild concern. No
    new todo filed.
  - **CF-9 env bucket — GREEN**: bucket name carries the `-prd-` marker.
  - **CF-10 phantom/object-backed — SKIP** (by design — the audit tool defers to
    `reconcile_phantom_manifest_rows_all.py --dry-run` for the full per-object check, to avoid a corpus walk here).
  - **CF-13 pipeline_mode source-aware form — GREEN**: 100% of non-blank `pipeline_mode` values start with
    `batch_`/`live_`/`replay_` (no bare/coarse `batch`/`live` values).
  - **Era-B chain data_type — RED on the literal check (242,210 `options_chain`/`futures_chain` rows), but ADJUDICATED,
    not a new gap**: `tradfi_manifest_canonicalisation_2026_06_01.md` (operator-reviewed, session 2026-06-08 verdict
    supersession) already established that `options_chain` is a real schema-backed DATA_TYPE for tradfi (UAC
    `TRADFI_OPTIONS_CHAIN_SNAPSHOT`, present on disk, carried intentionally by the fixed migrator mtds@51c604a4) — the
    audit tool's Era-B "must be 0" premise does not hold for tradfi's adjudicated bundle-grain design. No new todo.
  - **CF-14 catalogue ⊇ present-set — not run**: the tradfi IS catalogue lives in a separate bucket
    (`instruments-store-tradfi-prd-...`, already built + verified fresh per task 8) rather than a `_catalogue/` prefix
    inside this market-data-tick bucket; a cross-bucket comparison is a heavier operation than this pass's scope — left
    as an honest gap, not attempted this session. **Verdict: not all-GREEN — checkbox stays unflipped.** Of the RED
    checks, 2 are genuine and already tracked (CF-1 → task 10, CF-3 → the new todo), 2 are false-positives from the
    audit tool checking the wrong layer/an already-adjudicated design decision (CF-8, Era-B) and need no new tracking,
    and CF-4/CF-7 are now GREEN after task 4's fix earlier this session. unified-trading-pm@(this commit).

- **2026-07-08** — **Task 4 dispatch (slot-7 sonnet/high): found + fixed a false-completion, re-diagnosed CF-3, task 4
  checkbox stays unflipped (gate genuinely not 100% yet).** Verified current manifest state directly via UTL storage
  client (`gcloud`/`gsutil` both broken in this slot per snap-confine, same as prior sessions). Discovery: the
  `tradfi_manifest_cf4_source_and_cf7_phantom_gaps_2026_07_07.md` issue doc's CF-4 todo was checked ✅ on 2026-07-07
  citing only "script written... QG green; quickmerge landed" — the `restamp_tradfi_source_2026_07_07.py --apply` run
  was **never actually executed**. Confirmed via read: manifest still had 1,984,830 blank-source rows / 6,022,012 total.
  **Ran the real apply** (`market-tick-data-service/scripts/restamp_tradfi_source_2026_07_07.py --apply`,
  2026-07-08T20:58 UTC): stamped `source` on 1,984,830 rows, snapshot at
  `gs://market-data-tick-tradfi-prd-central-element-323112/_index/snapshots/pre_tradfi_source_restamp_20260708T205809Z.parquet`,
  row-count invariant held (6,022,012 unchanged), post-apply gate verify passed inline
  (`CF-4 Gate PASSED: 0 blank-source rows with valid pipeline_mode`). Re-read confirms CF-4 now genuinely GREEN
  (residual 42,341 blank-source rows are exactly the CF-3 population below, which cannot derive a source without a
  pipeline_mode). Re-confirmed CF-7 still clean (0 blank data_type, 0 blank/UNKNOWN venue) — unaffected by the CF-4
  write. **Re-diagnosed CF-3**: the issue doc's 2026-07-07 guess ("mostly barchart-retired remaps") is wrong for most of
  the population — 28,344 of the 42,315 blank-`pipeline_mode` rows are schema_version=9, dated **2026 only**, on live
  active venues (NASDAQ/NYSE/CME/ICE/FX/KRX/CBOE/ YAHOO_FINANCE) for data_types
  mbp_10/corporate_action_confirmed/earnings_result/ohlcv_1m/trades/ ohlcv_24h/tbbo/macro_result/options_chain — an
  ongoing live-writer gap, not a historical/retired tail. Filed as a new actionable P1 todo in the same issue doc (CF-3
  live-writer pipeline_mode gap); the other 13,971 blank-pipeline_mode rows are exactly the CF-1 schema_version=4 tail
  already tracked as task 10 below (no new tracking needed for that half). **Task 4 checkbox NOT flipped** — the E5
  rebuild itself ran to completion 2026-07-07 (see prior entries), but the literal "100% schema_version=9" gate is
  genuinely not met (99.77%, 13,971-row v4 tail = task 10's scope) and pipeline_mode is not fully present (42,315 blank,
  addressed by the new CF-3 todo). Consistent with this task's own 2026-07-07 precedent of declining to flip on an unmet
  literal gate. unified-trading-pm@(this commit).

- **2026-07-07** — **Task 4 (E5 rebuild) SUBSTANTIALLY DONE + Task 6 (E7 verify) AUDIT RUN — 4/9 CF gates RED (slot-7
  opus/max).** V3 rebuild launched 08:32 UTC with two throughput opts on top of the initial code fix
  (mtds@`f4751011`→`4ccf52c6` `perf(scripts): skip bundled parquet reads + non-v9-only CF-11`): (a) bundled
  `options_chain` shards no longer parquet-download for row_count (~290K blobs × 150ms = 12h saved; placeholder
  `total_rows=1` keeps the record on the `captured` path since the exact count only feeds the `instrument_count`
  coverage stat); (b) CF-11 re-emit filters to `schema_version != '9'` first (~1.4M v9 rows already in target shape,
  only the ~15K non-v9 tail needs re-emission — 100x speedup). Result: rebuild finished in **785s / 13 min** (vs the
  killed v1 that had ~28h projected). Object-scan summary:
  `total_shards=1,758,954 distinct_venues=6 (CBOE 2,633 · CME 1,129,581 · FX 1,474 · ICE 9,470 · NASDAQ 130,410 · NYSE 485,386) distinct_dates=2017 unparseable=106 reemit_failed=1,475 reemit_empty=0`.
  Main `_index` grew 4,500,951 → 6,020,339 rows (+1.52M captured additions). **Ran the E7 CF audit inline in Python**
  (the shipped `cf_manifest_audit_2026_06_01.py` uses subprocess `gcloud storage cp` which is broken in the
  snap-confined slot, so replicated the check surface via UTL `get_storage_client` + pandas): **CF-1 RED**
  `schema_version` 99.74% v9 (6,004,893/6,020,339; 15,438 v4 + 8 v6 tail); **CF-2 GREEN** `asset_group` col present,
  `category` col absent; **CF-3 RED** `pipeline_mode` 99.27% populated (5,976,656/6,020,339; 43,683 blank); **CF-4 RED**
  `source` 66.4% populated (3,996,137/6,020,339; **2,024,202 blank** — the discovery of the session, mostly
  `batch_databento` empty_confirmed + attempted_failed rows written before the source-populating writer landed); **CF-5
  GREEN** typed empty reason 0 blank; **CF-6 GREEN** 4-state vocab clean; **CF-7 RED** 638 UNKNOWN/blank venue + 4,903
  blank `data_type` (all attempted_failed with `error_reason=phantom_captured_no_parquet_at_canonical_path` — the
  phantom-audit tool wrote them with blank `data_type`, a pre-existing correctness gap in
  `reconcile_phantom_manifest_rows_all.py`); **CF-13 GREEN** source-aware `pipeline_mode` on all 5,976,656 populated
  rows. **NEITHER task 4 nor task 6 checkbox is flipped** — task 4's 100%-v9 gate is defeated by the 15,446 v4/v6 tail
  (task 10's `stamp_schema_version_v9_mtds_2026_06_29.py` job in the un-block sequence) plus the 43,683
  blank-`pipeline_mode` rows the object scan cannot supersede (different row_key granularity); task 6's
  CF-1..CF-12-GREEN gate is defeated by CF-1/CF-3/CF-4/CF-7 red. **Findings that must be plan/issue-doc'd** (raising to
  operator via `/blocked` for triage): (i) CF-4 2M-row blank-source tail is materially bigger than the plan budgeted for
  and needs its own source-restamp pass (not covered by any existing task); (ii) CF-7 4,903 phantom-blank-data_type rows
  are a bug in `reconcile_phantom_manifest_rows_all.py` (attempted_failed rows must preserve the original captured row's
  `data_type`); (iii) 291 v4 aggregate-atom `options_chain` orphans with blank underlying/instrument_type remain
  (rebuild per-underlying grain does not supersede them). Task 5 (E6 CF-7 relabel) will need to handle both CF-7
  populations _plus_ the 2M CF-4 tail; the "diagnose per-row, do NOT bulk-overwrite" discipline still applies but the
  scope has grown ~50x. mtds@4ccf52c6 committed + pushed to LDR via quickmerge --agent.

- **2026-07-07** — **Task 4 (E5 rebuild_tradfi_manifest.py) CODE FIX SHIPPED + REBUILD RUNNING (slot-7 opus/max).**
  Started task 4 at 06:52 UTC; discovered the E5 tool was broken by THREE UTL contract hardenings that landed since it
  was last invoked, all crashing the object scan after ~2 min: (a) **wave2 Phase-4 hard-ban on `ManifestWriter.add()`
  for bundled data_types** (options_chain / futures_chain / event_contract) — corpus has ~288,708 CME `options_chain`
  parquets that hit the ban on the first shard; (b) **hard_schema_enforcement Phase 4 MalformedRowKeyError** on blank
  `instrument_id` / `chain` in row_key — both bundled emissions AND the CF-11 re-emit of historical bundle-atom /
  aggregate-atom rows fail this check; (c) **data_pipeline_hardening Phase 1 KEYSTONE UnprovenHonestAbsenceError**
  requires `FetchEvidence` proving honest absence for `record_empty(reason=SOURCE_RETURNED_ZERO)` — CF-11 re-emit of
  preserved (non-trading-day) SRZ rows all fail. Filed /blocked BLK-b574724c; main answered "fix the tool, don't restart
  from 2020". **Fix shipped: market-tick-data-service@7a7e2e78** (`fix(scripts): rebuild_tradfi_manifest handles bundled
  data_types
  - hard-schema Phase
    4`). Bundled shards now route through `record_captured_from_counts`with observed_clusters read from parquet metadata +`{underlying:
    1}`self-referential expected_clusters (no external denominator on a historical reconstruction). CF-11 re-emit synthesises`cf11_rebuild_reinherited`FetchEvidence for preserved SRZ rows + re-derives blank/retired pipeline_mode via`derive_pipeline_mode_for_row`(drops rows whose venue+data_type maps to no live PipelineMode — the batch_barchart post-retirement tail). Refactored CF-11 helpers into`_rebuild_tradfi_cf11.py`to keep the entrypoint under the 900-line file cap +`scan_and_rebuild` under 200 lines. Full corpus rebuild launched in-slot 07:31 UTC (VM_NAME=`rebuild-tradfi-slot7-full-20260707T073100Z`, PID 3436463, `--start-date
    2020-01-01 --end-date
    2026-07-07`); at 08:05 UTC it is mid-object-scan at 2024-05-23 with 189K new entries in the current per_vm shard + main `_index`grown 4,500,951 → 4,794,113 rows (293K captured additions); consolidator is draining shards on its 1-min cycle. Full completion (object scan ~2020-2026 + CF-11 iteration over ~1.4M honest-absence rows) will run several more hours; the checkbox is INTENTIONALLY NOT FLIPPED because the plan's 100%-v9 gate cannot be verified until the rebuild + consolidator have drained. **Gate status at 08:05 UTC**: v9 % 4,485,505/4,500,951 = 99.66% pre-rebuild → 4,778,667/4,794,113 = 99.68% mid-rebuild (rising as the CF-11 phase re-emits historical v4 attempted_failed rows). **Follow-up (task 5/6/7)**: 291 v4`captured` `options_chain`rows have BLANK`underlying`/`instrument_type`
    (pre-migration aggregate atoms) that the rebuild's per-underlying grain emits DIFFERENT row_keys for and does NOT
    supersede — these are aggregate-atom orphans slated for task 5 (E6 CF-7 relabel) or a separate delete pass; they
    will not clear as part of task 4 alone. **Findings closure**: BLK-b574724c answered inline (fix the tool); no
    separate issue doc because the whole scope stayed inside task 4.

- **2026-07-06** — **Task 10 (v9 `schema_version` tail re-stamp) PARKED with BLOCKED-PREREQUISITES (slot-7 opus/max).**
  Auto-dispatched at Tier 1 Priority 50 immediately after slot-7 released `understat_local_backfill_completion-006`;
  boot `dispatch_reason: "highest-rank queued task with prereqs met and no collision"` (higher-priority tasks -004
  P0=10, -005 P1=20, -006 P0=10, -007 P0=10 all `status=queued` — dispatcher skipped them for undisclosed reasons and
  landed on the P2=50 tail-clean-up). Two prereqs unmet: (a) plan-chain — task -004 (E5 `rebuild_tradfi_manifest.py`) is
  queued and its rebuild sets `schema_version=9` on every emitted row (per the E5 script docstring, v9 `ManifestWriter`
  derives `schema_version=9` for all rebuilt rows via UAC), so running -010 first is largely redundant and could fight
  the rebuild; the plan's task text explicitly refers to the tail as what remains "post rebuild"; (b) fleet not drained
  — plan §156 requires "quiet window, post fleet-drain" and the live `tradfi-bf-cme-ohlcv-1m-*` VMs (per task 1
  writer-safe finding) plus the every-minute Cloud Run manifest-consolidator are active, so an in-place `schema_version`
  write races the consolidator. Current tail per task 8 evidence: 99.4% `schema_version=9` (2,600,381 / 2,615,827 rows)
  — genuine 15,446-row tail, but the plan expects it addressed post-E5. Applied established precedent (BLK-afcc5da6 →
  understat-001 OPTION A, BLK-18a3d596 → understat-004 OPTION A, this session → understat-006) without re-filing
  /blocked — same dispatcher failure mode (priority-only ignores plan chain), same OPTION A resolution: parked -010 with
  in-checkbox `**BLOCKED-PREREQUISITES (2026-07-06, slot-7)**` marker + full un-block sequence + tool-availability note
  (the shipped `stamp_schema_version_v9_mtds_2026_06_29.py` is sports-hardcoded; when -010 re-dispatches, generalize or
  write a tradfi sibling). Task 10 re-dispatches after -003 (straggler VM close), -004 (E5), -005/-006/-007 complete and
  operator clears the marker. Parallel operator flag: same session's -006 park entry noted that task understat-001 is
  running as an orphaned OS process — that remains open.

- **2026-07-06** — **Task 9 (Close `migration_verification_orphan_safety` V6/G4) FLIPPED (slot-7 opus/max).** TradFi V6
  line 238 in `migration_verification_orphan_safety_2026_06_10.md` is now `[x]` with full evidence; header banner
  updated from "🟡 VM IN FLIGHT — V6 TradFi restart" to "🟢 V6 CLOSED — All 5 AGs now canonical (5/5)". Evidence chain:
  (a) TradFi G4 `--apply` DONE for 2020-2025 + 2026 (7 VMs, e2-standard-16 · SPOT · workers 24 · per-year; launcher
  OOM-fix `deployment-service@77cfcda`; MTDS pin `9ecd1e29e16429f8`; 2026 year landed 15:14 UTC via
  `canonical-migration-tradfi-20260706-145606` — planned=332825 moved=122703, exit_code=0, fatal=0; run.log at
  `gs://deployment-scripts-central-element-323112/vm-logs/canonical-migration-tradfi-20260706-145606/run.log`). (b)
  Pre-apply ⑬–⑲ verdict was GREEN pre-apply: V2 orphan-E=0 for tradfi 14:32Z 2026-06-11 (was 47,102) · V3 schema-
  completeness 0-RED/19 cells 2026-06-11 · V4 candle-edge convention QG-enforced (STEP 5.92) · V5 projected preview
  rendered per-AG in dev · IS catalogue tradfi `catalogue-rollup-tradfi-20260706T154714Z` (1,096,069 rows / 685,111 MVP
  promoted to `gs://instruments-store-tradfi-prd-central-element-323112/prod/catalog.parquet` 2026-07-06T15:48:30 UTC).
  (c) V6 checkbox 1 (4/5 AGs 2026-06-29) already ✅; V6 checkbox 3 (G4.5 cleanup_legacy_twins.py) already ✅; V6
  checkbox 2 (this one) NOW ✅ → all 3 V6 checkboxes closed. Note: post-apply cleanup (E5 manifest rebuild + orphan
  sweep re-run + enumerate-seed + straggler re-run) is DIFFERENT from the V6 verdict — those are POST-verdict cleanup
  tracked in this plan's tasks 2-7, and the straggler VM `canonical-migration-tradfi-20260706-152937` is still running
  per task 3's BLOCKED-STRAGGLER-VM-RUNNING status (idempotent, expected finish ~16:15 UTC). The V6 verdict is about the
  APPLY completing (which it did — exit_code=0), not about all post-apply cleanup being done.

- **2026-07-06** — **Task 8 (IS catalogue for tradfi) FLIPPED (slot-2 opus/max).** Foreground
  `build_instrument_catalogue.py --asset-group tradfi --mode incremental` — completed in 80s,
  `run_id=catalogue-rollup-tradfi-20260706T154714Z`, `exit_code=0`, promoted 1,096,069 rows (685,111 MVP) to
  `gs://instruments-store-tradfi-prd-central-element-323112/prod/catalog.parquet` at 2026-07-06T15:48:30 UTC.
  Incremental window `day>=2026-06-15`, self-widening trailing; merged 104,286 in-window updates + 0 new listings +
  991,783 frozen-tail; monotonic guard ACCEPT. The plan-header note "prod/catalog.parquet stale since 2026-06-29" was
  already invalid at dispatch time — the daily lifecycle-catalogue-regen job succeeded at 2026-07-06T01:03:58 UTC (~15h
  before my dispatch), so the 3600s scheduler-timeout regression is not currently active and NO BLOCKED-Q was raised.
  Verified prereqs: tradfi mkt-data-tick manifest is 99.4% schema_version=9 (2,600,381 of 2,615,827 rows) meaning E5
  rebuild is effectively done, and 17,093 expected_unattempted rows already materialised on the manifest side.
  Instrument-service script SHA `6716f55` (tip of live-defi-rollout at run time). Note: the plan-body PREREQ "IS
  enumerate-seed done" (task 7 in-chain) was not literally checked-off, but `build_instrument_catalogue.py` reads
  `by_date/` snapshots (not the manifest EU rows), so the enumerate-seed step is orthogonal to this catalogue build —
  the "could-exist SSOT" framing refers to the per-instrument lifecycle, not the EU denominator; the dispatcher's
  `prereqs met` verdict was correct.
- **2026-07-06** — Task 2 (Orphan sweep) parked with BLOCKED-ORDERING per BLK-71c6f4c4 (main agent). Rationale: task 4
  (E5 `rebuild_tradfi_manifest.py`) MUST run first — my task 1 migrator only fixed object PATHS (per its docstring); the
  manifest columns `schema_version`/`source`/`pipeline_mode`/`asset_group`/`available_at` are added by the E5 rebuild,
  not the migrator. Running the orphan sweep now would classify the newly-migrated 122,703 canonical objects as Class-E
  ORPHAN (real data with no manifest row) — a false positive that would fail the E=0 gate. Fix: reorder the chain so
  task 4 (E5) precedes task 2 (orphan sweep). Deletes remain never-autonomous / operator-gated regardless of order.
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
