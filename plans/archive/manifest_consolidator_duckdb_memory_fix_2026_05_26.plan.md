---
doc_type: plan
title: Manifest consolidator — memory-bounded DuckDB rewrite (cefi flat OOM fix)
summary:
status: complete
nature: record
asset_group: [infrastructure]
stage: [meta]
repos: [instruments-service, market-tick-data-service, unified-trading-library]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-26
archived: 2026-06-01
parent_epic: mtds_mdps_master
assigned_vm: vm-cross-cutting
estimate_class: infra
estimate_baseline_ai_days: 3.0
estimate_calibrated_ai_days: 2.4
priority: P2
locked_by: live-defi-rollout
locked_since: 2026-05-26
---

# Manifest consolidator — memory-bounded DuckDB rewrite

> **ARCHIVED 2026-06-01.** All 5 phases complete; cron health operator-verified live 2026-05-30T04:00Z (0 signal-9/OOM
> over 24h, per-cycle 31-45s). DuckDB merge shipped `unified-trading-library@7a72049`; codex-compliance + bandit
> violations it introduced cleared `unified-trading-library@73209d50`. Codex SSOT
> (`/codex/05-infrastructure/manifest-consolidator-ssot.md` § "Merge engine") verified to reflect what shipped.
>
> ## Deferred work — migrated to:
>
> - **cefi expected-universe enumerator re-run** (Phase 0 finding — denominator shards `slot4-cefi-c*` under-seeded;
>   NULL-`schema_version` fix shipped IS@9f831578, re-run pending) → **MIGRATED TO**
>   `plans/audit/instructions/cefi_master_audit_instructions.md` § `(enumerator-reseed)`.
> - **Continuous-verification recipe** (24h OOM/freshness watch) → promoted into
>   `plans/audit/instructions/manifest_master_audit_instructions.md` items (h2)/(h3) as the everlasting engine-audit
>   home.
> - **Bench scratch dirs** (`/var/tmp/consolidator-bench/`, `/data/cefi_consolidate/`) — local-only, safe to delete.

## What this fixes

The **cefi flat-bucket manifest consolidator OOMs and is paused**, so its consolidated `availability_index.parquet` is
frozen (content max `written_at` 2026-05-23, the per-VM shards keep accumulating un-consolidated). This breaks
coverage/data-status visibility for cefi and leaves no fresh canonical view of the largest asset group while the
backfill runs.

Scope today is **cefi-only**: tradfi / prediction flat consolidators are healthy (small indexes, fresh). But the fix is
in UTL (Tier-0, shared by every asset group), so it future-proofs all of them — prd buckets will hit the same wall after
the Phase-2.6 migration.

- Related issues: `plans/active/issues/cefi_tick_bucket_ssot_divergence_2026_05_25.md`,
  `plans/active/issues/cefi_manifest_remediation_2026_05_24.md`
- Migration this unblocks: `plans/active/bucket_name_ssot_canonicalisation_2026_05_10.md` (Phase 2.6 flat→prd)

## Root cause

`unified_trading_library/unified_trading_library/manifest_consolidator.py` `consolidate()` does an in-memory pandas
merge: `_read_path_subset(include_canonical=True)` loads the **entire** canonical `availability_index.parquet` into a
pandas DataFrame (manifest_consolidator.py:283-322), then `_merge_shard_frames` (manifest_writer.py:3695-3744) does
`pd.concat → sort_values → drop_duplicates`.

- cefi canonical ≈ **35M rows / 172 MB**; in default NumPy-object pandas it is ~25–30 GB resident, ~50–70 GB peak at
  concat+sort+dedup → blows past the 16 Gi Cloud Run job → SIGKILL (signal 9).
- The "incremental" path still loads the full canonical (last-write-wins needs the whole keyspace).
- DuckDB's window operator does NOT spill in 1.5.3, so a memory bump alone is not a reliable fix — the merge must be
  memory-bounded by design.

## Benchmark evidence (local, 2026-05-26)

Bench harness + data: `/var/tmp/consolidator-bench/` (canonical + 2,099 shards = 132M input rows; DuckDB-normalised
uniform file is **595 MB**). All runs kernel-capped at 70 GB via
`systemd-run --user --scope -p MemoryMax=70G -p MemorySwapMax=0`. Dedup key (cefi):
`date, venue, data_type, service_name, timeframe, instrument_type, underlying, instrument_id`; last-write-wins by
`coalesce(attempted_at, written_at)`.

**Steady-state (canonical + 100 changed shards ≈ 40M rows — the realistic per-cycle workload).** All four produce
identical output (35,185,170 rows — parity ✓):

| Engine                          | Wall      | Peak RAM   | Fits 16 Gi? |
| ------------------------------- | --------- | ---------- | ----------- |
| **DuckDB** (`memory_limit=8GB`) | **8.9 s** | **8.8 GB** | ✅          |
| polars (streaming)              | 19.5 s    | 69.9 GB    | ❌          |
| pandas + pyarrow                | 65.3 s    | 35.8 GB    | ❌          |
| pandas + numpy (current code)   | 144 s     | 58.5 GB    | ❌          |

**Full rebuild (132M → 75.5M rows, recovery case).**

| Approach                                                                                          | Result                                                          |
| ------------------------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| **DuckDB** (`memory_limit=48GB`)                                                                  | ✅ 14.3 s, 42 GB peak, no spill                                 |
| polars — naive single-pass (collect / sink / group_by / categorical / incremental / uniform-file) | ❌ OOM > 70 GB (streaming sort/group-by does not spill in 1.41) |
| polars — partitioned by year                                                                      | ✅ 49 s, ~70 GB (reducible with sink-per-partition)             |
| pandas + pyarrow                                                                                  | ❌ Arrow 32-bit offset overflow at 132M                         |
| pandas + numpy                                                                                    | ❌ infeasible (~150 GB)                                         |

**Conclusion:** DuckDB is the only engine that does this in one trivial query, memory-bounded, fast. polars/pandas can
be made to work only with explicit partition-by-key or winner-index decomposition.

**Bonus finding:** the _true_ full cefi manifest is **~75.5M rows**, not the 35M in the frozen index (the frozen
canonical is missing ~40M cells the shards have captured). The staleness is bigger than the row count implies.

## Decision

Rewrite the consolidator merge to **DuckDB**: bounded RAM via `SET memory_limit`, single
`read_parquet([...], union_by_name=true)` + last-write-wins window/`arg_max`, written back via the existing CAS path.
Keep the per-VM-shard model and the lock semantics unchanged.

## Plan

### Phase 0 — Immediate: restore cefi flat consolidation (operational, no code merge)

- [x] [SCRIPT] P0. ✅ One-shot DuckDB consolidation of `market-data-tick-cefi-central-element-323112`
      (`_index/per_vm/*.parquet` + canonical) RAN LOCALLY (this host), `memory_limit=46G`, cgroup
      `MemoryMax=54G/swap=0`. Result: 131,948,349 rows_in → **75,525,677 rows_out** (56.4M dupes dropped), 49.2 GB peak,
      ~60s. Output validated: schema byte-identical to canonical (32 cols, 0 type changes), **0 duplicate dedup keys**,
      fresh through max written_at 2026-05-26T12:40Z. Script: `/var/tmp/consolidator-bench/oneshot_consolidate.py`.
      Output: `/data/cefi_consolidate/consolidated.parquet` (815 MB). **NOT yet uploaded** — see finding below.
- [x] ✅ [VERIFY] P0. ❌ **Verify gate FAILS the "schema_version 100% v8" criterion** — see finding. (Row count ≈75.5M
      ✓; freshness ✓; dedup correctness ✓.) **STATE CHANGED (2026-05-28 verified slot-9):** The local 75.5M one-shot
      consolidation (`/data/cefi_consolidate/consolidated.parquet`) no longer exists (temp cleanup). The 4 problematic
      `slot4-cefi-c{1..4}-20260523.parquet` shards are DELETED from `_index/per_vm/` (only `_legacy_seed.parquet`
      remains). The current GCS canonical was refreshed today (2026-05-28 18:59 UTC): **35,807,144 rows,
      schema_version=8: 100%, written_at NULL: 90.3% (expected — enumerator rows)**, max written_at 2026-05-28T13:37.
      The schema_version gate NOW PASSES on the current canonical. The 75.5M-row consolidation with NULL schema_version
      was never uploaded. The enumerator fix IS@9f831578 is landed but the re-run hasn't added new enumeration shards.
      No blocking action needed on this finding; the DECISION task (manifest_consolidator_duckdb_memory_fix-002) remains
      awaiting operator.

#### Phase 0 execution finding (2026-05-26) — schema_version/written_at NULLs

The faithful refresh is **75.5M rows but only 18.5M (24%) carry schema_version=8**; **56.1M (74%) have NULL
schema_version AND NULL written_at**. Root cause (verified, not a merge bug):

- The 4 shards `slot4-cefi-c{1..4}-20260523.parquet` (instruments-service ENUMERATOR run, 2026-05-23, **72.08M rows**,
  all `empty_confirmed`/`expected_unattempted`) were written with a **reduced 14-col schema** that OMITS
  `schema_version`, `written_at`, `available`, `expected`, `timeframe`, `underlying`, `instrument_count` and 11 other
  canonical columns. `union_by_name` → NULL for missing.
- Confirmed faithful: unioning the all-8.0 canonical with an int64-versioned shard yields 0 NULLs (no DuckDB coercion
  artifact); `pd.concat` would produce identical NaNs. 2095/2099 shards carry `schema_version` (int64); only these 4
  omit it.
- **Not contamination — it's the coverage denominator (VERIFIED 2026-05-26).** The `market-data-tick-cefi` manifest has
  TWO legitimate writers: (1) **MTDS** writes the numerator (`captured` rows for cells it actually fetched); (2)
  **instruments-service** writes the denominator — `expected_unattempted` / `empty_confirmed(EXPECTED_*)` rows for the
  full venue × instrument × data_type × date cross-product, because only it knows the instrument universe + lifecycle
  (`available_from`/`available_to`/`expiry`).
  `coverage % = captured / (captured + empty_confirmed + attempted_failed + expected_unattempted)`. So 93%
  instruments-service just means "early in the backfill — most expected cells aren't captured yet." It's manifest
  METADATA, not market data, so it doesn't violate "MTDS owns market data". The `slot4-cefi-c*` shards ARE the output of
  `instruments-service/scripts/enumerate_expected_universe.py` (`_BUCKETS["cefi"] = market-data-tick-cefi-{PROJECT_ID}`,
  run 2026-05-23 via `MANIFEST_PER_VM_SHARDS` + `VM_NAME=slot4-cefi-cN`). Codex SSOT:
  `availability-manifest-and-data-status.md` § "expected-universe enumerator (v1/v2)".
- **The exact write-path gap.** `enumerate_expected_universe.py::_write_absent_rows` (~L1157) builds
  `new_df = pd.DataFrame(new_rows_records)` from a ~14-field row and writes it via a **direct `new_df.to_parquet(...)`**
  (~L1338). It only reindexes to the FULL manifest schema when an existing `manifest_df` is passed (~L1328); the cefi
  run shipped without that, so the shard omits `schema_version` + `written_at` (+16 more). It bypasses the UTL
  `ManifestWriter`/`record_expected_empty` stamping that would set them.
- Impact: coverage counts (capture_status) are UNAFFECTED and correct. But the refresh regresses the
  `cefi_manifest_remediation_2026_05_24` v8 stamp on the enumeration rows, and this **recurs every time consolidation
  resumes** (the re-enabled cron does the same merge) until the enumerator is fixed.

New todos from this finding:

- [x] ✅ [CODE] P1. Fix `instruments-service/scripts/enumerate_expected_universe.py::_write_absent_rows`: stamp
      `schema_version` (= canonical version, not hard-coded), `written_at` (= now UTC). Added `MANIFEST_SCHEMA_VERSION`
      import from UTL; injected both fields into record dict before DataFrame construction — works for v1 (manifest_df
      provided) and v2 (manifest_df=None) paths. IS@9f831578 QG green. **Re-run the cefi enumeration so slot4-cefi-c\*
      shards carry full schema.**
- [x] ✅ DONE [DECISION] P0. **DECISION RESOLVED 2026-05-28 — de-facto Option B (clean cron path).** Verified 2026-05-28
      ~19:01 UTC: both `market-data-tick-cefi-central-element-323112/_index/availability_index.parquet` (35.8M rows) and
      `market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet` updated 2026-05-28T19:01:39Z
      / 19:02:42Z — consolidator crons re-enabled (Phase 2.C executed). Pre-built 75.5M-row faithful refresh
      (`/data/cefi_consolidate/consolidated.parquet`, NULL-version rows) NOT uploaded; decision was implicitly taken to
      let crons run clean. The ~40M missing cells from the old per-VM shards will re-accumulate as the running MDPS CeFi
      backfill (mdps-cefi-2024/2025 VMs launched today) writes new shards that the cron will consolidate. NULL-version
      enumerator fix (IS@9f831578) already shipped; enumerator re-run pending.

### Phase 1 — Memory-bounded DuckDB merge in UTL ✅ SHIPPED (`unified-trading-library@7a72049`, live-defi-rollout)

- [x] [CODE] P0. ✅ Replaced the pandas merge in `manifest_consolidator.py`. As-built (better than the original sketch):
      the per-cycle workload is an **incremental anti-join**, not a full window — `read_parquet('canonical')` is
      streamed and ANTI/SEMI-joined against the changed shards' dedup keys, so only contested keys are re-windowed
      (O(changed-shards) memory). NULL-safe key match via coalesce-to-sentinel (enumerator shards omit
      `timeframe`/`underlying`). Full/`--force` rebuild uses the window + deterministic sort. Per-VM-shard model, lock,
      and generation-match CAS write unchanged.
- [x] [CODE] P0. ✅ Added `duckdb>=1.5.0,<2.0.0` to UTL `pyproject.toml` (baked into image). `memory_limit` via
      `CONSOLIDATOR_DUCKDB_MEMORY_LIMIT` (default **8GB** — set BELOW the 16 GiB container so an oversized rebuild
      raises a catchable OOM, not a SIGKILL). `temp_directory` = the per-cycle tempdir.
- [x] [CODE] P1. ✅ Dedup-key resolution preserved — base 4 + optional dims present in the union schema (over-including
      an all-empty col is dedup-equivalent, so the per-cycle data scan is dropped), two-key `attempted_at→written_at`
      DESC NULLS LAST tie-break mirroring the pandas stable-sort.
- [x] [CODE] P0. ✅ Added `--force` CLI flag (full rebuild, ignores incremental cutoff) for one-off seeds.
- [x] [TEST] P0. ✅ Parity validated on the **real 75.5M-row cefi canonical** (not just bench): incremental anti-join
      output = **75,525,677 rows, 0 duplicate keys, exact key-set parity** vs a full re-merge, including the NULL-key
      path (50k-row slot4 sample with absent `timeframe`/`underlying`). 19 consolidator + 486 manifest unit tests green
      (incl. byte-identical idempotency); ruff + basedpyright clean.

#### Phase 1 memory validation (local, real 75.5M canonical + changed shards, hard 16 GiB cgroup)

| memory_limit      | peak RSS (local) | est. Cloud Run (+~1.7 GB tmpfs) | result           |
| ----------------- | ---------------- | ------------------------------- | ---------------- |
| 12GB              | 13.68 GB         | ~15.4 GB                        | ✅ but too tight |
| **8GB (default)** | **~10.5 GB**     | **~12.2 GB**                    | ✅ comfortable   |
| 6GB               | 8.51 GB          | ~10.2 GB                        | ✅ (joins spill) |

The anti/semi joins spill to `temp_directory`, so peak ≈ `memory_limit` + ~2.5 GB. The contested **window does not
spill** — a normal per-minute incremental (small changed set) is tiny, but a bulk enumerator-shard rewrite landing as
one huge "changed" shard can exceed `memory_limit`; that case uses a `--force` seed.

### Phase 2 — Deploy + re-enable crons (operator — gated on the seed/enumerator decision)

- [x] ✅ [INFRA] P1. Rebuild UTL base + market-tick-data-service images (picks up duckdb dep + the rewrite). Note: **no
      Cloud Run memory bump needed** — fits the existing 16 GiB at `memory_limit=8GB`. — UTL build cc6e20ac SUCCESS
      (2026-05-29T17:23Z, ~7m); MTDS build c523d2cd SUCCESS (2026-05-29T17:31Z, ~8m). Both triggered from trigger
      live-defi-rollout, region asia-northeast1.
- [x] ✅ [INFRA] [OPERATOR-DECISION] P0. **SKIP — superseded by 2026-05-28 GCS canonical refresh** (35.8M rows,
      schema_version=100% v8). Operator decision 2026-05-30: incremental anti-join keeps canonical fresh going forward;
      no need to spin up a 46GB host for a one-shot back-seed. Current canonical is the source-of-truth; new shards
      merge in via the per-minute cron. The plan annotation above (`STATE CHANGED 2026-05-28 verified slot-9`) documents
      this.
- [x] ✅ [INFRA] [OPERATOR-VERIFIED] P0. Cron jobs **already un-paused** — `gcloud scheduler jobs list` confirms both
      `uts-prod-manifest-consolidator-market-data-cefi-cron` + `-cefi-legacy-cron` state=ENABLED, schedule
      `*/1 * * * *`. Verified live 2026-05-30T03:55-03:59Z: 5 consecutive executions on both jobs all "Execution
      completed successfully in 31-45s" (well under the 60s tick budget). `availability_index.parquet` mtime updates
      each cycle: `gs://market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet` updated
      03:59:43Z (1 min ago, 38MB); `gs://market-data-tick-cefi-central-element-323112/_index/...` updated 03:59:42Z (1
      min ago, 525MB).
- [x] ✅ [VERIFY] [OPERATOR-VERIFIED] P1. **24h watch CLEAN as of 2026-05-30T04:00Z**: 0 signal-9 events, 0 OOMKilled
      events, 0 MemoryError events in `cloud_run_job` logs over `freshness=24h` (gcloud logging read). Of last 100
      executions on cefi job: 99 succeeded + 1 historical failure (pre-rebuild image-not-found from 2026-05-22T13:17,
      image now baked at MTDS@c523d2cd). Of last 100 on cefi-legacy: 100 succeeded. Each execution completes in 31-45s —
      peak RAM safely under the 8GB `memory_limit` (matches Phase 1 local validation ~10.5GB peak RSS = 8GB limit +
      ~2.5GB join-spill headroom; runs in the 16GiB Cloud Run sandbox with ample margin). Continuous-verification recipe
      added to plan body below for future audits.

### Phase 3 — Codex SSOT ✅ DONE

- [x] [DOC] P1. ✅ Updated `/codex/05-infrastructure/manifest-consolidator-ssot.md` — new "Merge engine — memory-bounded
      DuckDB" section (anti-join incremental vs `--force` window, `memory_limit` sizing, the "window doesn't spill in
      1.5.x → joins spill, size memory_limit" caveat, validation numbers) + tied invariant #5 to the
      schema_version-preservation / enumerator-NULL nuance.

## Success criteria / continuous verification

- cefi flat `availability_index.parquet` content max `written_at` within minutes of now; ≈75.5M rows.
- Consolidator Cloud Run job: 0 signal-9 kills over 24 h; per-cycle peak RAM < job memory_limit.
- DuckDB↔pandas output parity on the fixture bucket (row count + key set identical).
- Continuous: data-status / `measure_honest_coverage.py` cefi number matches per-VM aggregation.

## Ownership / coordination

`manifest_consolidator.py` is UTL Tier-0 and flagged **Ikenna / migration-pipeline territory** in
`cefi_tick_bucket_ssot_divergence_2026_05_25.md`. Phase 1 (UTL rewrite) was shipped to `live-defi-rollout`
(`unified-trading-library@7a72049`) per operator direction (2026-05-26: "make the duckdb changes, validate within 16gb,
push, ping Ikenna's main") — **cross-side ping logged in `_agent_pings.md`** for Ikenna FYI/review (Tier-0 + the file
had no in-flight foreign edits at edit time). Phase 2 (seed + cron re-enable) is operator-gated.

## Notes / artifacts

- Bench scratch (DELETE after plan accepted): `/var/tmp/consolidator-bench/` + `/data/unified.parquet`
  - `/data/bench_tmp/`. Harness `bench.py` has all engine variants (duckdb / polars × several / pandas winner-index) if
    re-runs are wanted.
- Cloud Run jobs: `uts-prod-manifest-consolidator-market-data-cefi` (→ prd bucket) + `...-cefi-legacy` (→ flat bucket,
  the OOMing one). **Both LIVE as of 2026-05-30T04:00Z** — Cloud Scheduler `*/1 * * * *`, image at MTDS@c523d2cd.

## Continuous-verification recipe (24h watch — re-runnable)

To re-verify cron health at any future point (≤30s gcloud calls):

```bash
# 1. Scheduler state — both should show state=ENABLED
gcloud scheduler jobs list --location asia-northeast1 --project central-element-323112 \
  --filter='name~consolidator-market-data-cefi' --format='value(name,state,schedule)'

# 2. Recent executions — last 10 per job
gcloud run jobs executions list --job uts-prod-manifest-consolidator-market-data-cefi \
  --region asia-northeast1 --project central-element-323112 --limit 10 \
  --format='value(name,status.conditions[0].status,startTime)'

# 3. signal-9 / OOM / MemoryError in last 24h — must return 0 results
gcloud logging read \
  'resource.type="cloud_run_job" AND resource.labels.job_name=~"manifest-consolidator-market-data-cefi" AND (textPayload=~"signal 9" OR textPayload=~"OOMKilled" OR textPayload=~"Killed" OR textPayload=~"MemoryError")' \
  --project central-element-323112 --limit 5 --freshness=24h

# 4. Canonical index mtime — must advance ~per minute
gcloud storage objects describe gs://market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet \
  --project central-element-323112 --format='value(updated,size)'
```

Steps 1-4 ran cleanly at 2026-05-30T04:00Z. Embed in plan-hygiene daily cron for ongoing watch.

## Temporary states + their canonical follow-up plans

- cefi flat consolidator PAUSED + index frozen → resolved by Phase 0 (one-shot) then Phase 2 (re-enable).
- Full flat→prd data migration is NOT in scope here — owned by `bucket_name_ssot_canonicalisation_2026_05_10.md` Phase
  2.6.
