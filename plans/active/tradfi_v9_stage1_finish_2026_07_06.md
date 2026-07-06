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
- [ ] [DATA] P0. **Idempotent straggler re-run** — transient GCS 503/504 bursts on 2026-07-06 left ~7 objects unmoved on
      2025-02-03/04 **plus 4 objects unmoved on 2026-01-15** (all transient GCS timeouts, not memory, self-limited).
      Re-run the migrator over the affected day-partitions (idempotent — skips already-canonical). 2026-01-15
      stragglers: `processed_candles/by_date/day=2026-01-15/timeframe=1h/data_type=tbbo/venue=NYSE/{BLK,LEN}.parquet`
      + `.../timeframe=1h/data_type=trades/venue=CME/EW1G6_P6825.parquet`
      + `.../timeframe=1m/data_type=trades/venue=CME/ESH6_P5500.parquet`. Gate: all straggler objects are now
      canonical; orphan-sweep re-confirms E=0.
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
- [ ] [DATA] P0. **IS catalogue for tradfi** — `build_instrument_catalogue.py` for tradfi (the could-exist SSOT). Gate:
      tradfi `prod/catalog.parquet` fresh + accurate; feeds the Stage-3 denominator re-measure (Plan 4). **PREREQ: IS
      enumerate-seed done.** ⚠️ NOTE the standing tradfi catalogue-scheduler timeout issue (daily
      `lifecycle_catalogue_scheduler` killed at 3600s, `prod/catalog.parquet` stale since 2026-06-29) — if the rollup
      still times out, RAISE a BLOCKED-Q (re-enable the operator-declined band-aid vs. ship the Phase-3 incremental —
      operator decision, tracked in `instruments_catalogue_incremental_rollup` / Plan 3).
- [ ] [VERIFY] P1. **Close `migration_verification_orphan_safety` V6/G4** — flip the tradfi apply verdict; assert all 5
      AGs canonical. Gate: V6 checkbox flipped with evidence; migration_verification tradfi track closed.
- [ ] [DATA] P2. **v9 `schema_version` tail re-stamp** (quiet window, post fleet-drain) — the migrators/rebuild left a
      small legacy `schema_version` tail; re-stamp to 9. Gate: 100% `schema_version=9`, no tail.
- [ ] [DATA] P1. **BLOCKED-OPERATOR-DECISION — legacy-twin bucket DELETES (defi / tradfi / pred).** After the tradfi
      apply + orphan-sweep E=0 + a byte-verify, the legacy-path twin objects can be deleted in a quiet window (cefi +
      sports already done). **Ikenna's migration sign-off GATES this — bucket deletes are never-autonomous
      (hard-stop).** Do NOT run any delete until the operator signs off; the working agent posts the byte-verify
      evidence and RAISES for sign-off. _(Carries `BLOCKED-` so the orchestrator will not dispatch it — stays visible
      for the operator.)_

## Progress Log

<!-- Append newest entries at the top: `- **YYYY-MM-DD** — <what landed> (<repo>@<sha> / evidence).` -->

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
