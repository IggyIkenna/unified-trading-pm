---
title: "Manifest consolidator — memory-bounded DuckDB rewrite (cefi flat OOM fix)"
created: 2026-05-26
author: harsh + Claude Opus 4.7 (1M)
status: active
parent_epic: mtds_mdps_master
assigned_vm: vm-cross-cutting
estimate_class: infra
estimate_baseline_ai_days: 3.0
estimate_calibrated_ai_days: 2.4
---

# Manifest consolidator — memory-bounded DuckDB rewrite

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
- [ ] [VERIFY] P0. ❌ **Verify gate FAILS the "schema_version 100% v8" criterion** — see finding. (Row count ≈75.5M ✓;
      freshness ✓; dedup correctness ✓.)

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

- [ ] [CODE] P1. Fix `instruments-service/scripts/enumerate_expected_universe.py::_write_absent_rows`: stamp
      `schema_version` (= canonical version, not hard-coded), `written_at` (= now UTC), and the full manifest column set
      on every enumerated row — OR route the write through UTL `ManifestWriter`/`record_expected_empty` instead of the
      raw `to_parquet`. Currently it only aligns to the full schema when `manifest_df` is provided. Harsh /
      instruments-service lane. Until fixed, no consolidation (one-shot or cron) can hold 100% v8. **Re-run the cefi
      enumeration after the fix so the slot4-cefi-c\* shards carry the full schema.**
- [ ] [DECISION] P0. **AWAITING OPERATOR** (tomorrow): upload the faithful refresh now (restore cefi visibility;
      reversible via pre-write snapshot; accept surfaced NULL-version rows) **vs** hold the upload until the enumerator
      is fixed + re-run, then consolidate clean. (Seed parquet ready: `/data/cefi_consolidate/consolidated.parquet`.)

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

- [ ] [INFRA] P1. Rebuild UTL base + market-tick-data-service images (picks up duckdb dep + the rewrite). Note: **no
      Cloud Run memory bump needed** — fits the existing 16 GiB at `memory_limit=8GB`.
- [ ] [INFRA] P0. Seed the cefi flat canonical once (75.5M rows) via `--force` on a big-RAM host
      (`CONSOLIDATOR_DUCKDB_MEMORY_LIMIT=46GB`) — OR upload the validated `/data/cefi_consolidate/consolidated.parquet`.
      Gated on the enumerator-fix / NULL-version decision above. Without a seed the first cron cycle would only pick up
      post-canonical-mtime shards (misses the ~40M older cells); a `--force` seed captures everything.
- [ ] [INFRA] P0. Un-pause `uts-prod-manifest-consolidator-market-data-cefi(-legacy)-cron`; verify
      `availability_index.parquet` advances each cycle and stays within memory.
- [ ] [VERIFY] P1. 24 h watch: no signal-9 in logs, index freshness < 2 min, coverage cron correct.

### Phase 3 — Codex SSOT ✅ DONE

- [x] [DOC] P1. ✅ Updated `codex/05-infrastructure/manifest-consolidator-ssot.md` — new "Merge engine — memory-bounded
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
  the OOMing one). Both currently PAUSED.

## Temporary states + their canonical follow-up plans

- cefi flat consolidator PAUSED + index frozen → resolved by Phase 0 (one-shot) then Phase 2 (re-enable).
- Full flat→prd data migration is NOT in scope here — owned by `bucket_name_ssot_canonicalisation_2026_05_10.md` Phase
  2.6.
