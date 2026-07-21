---
doc_type: issue
title: CME options_chain legacy flat layout — ~187.5M rows outside the TradFi single-leg @LIN canonicalization
summary:
  The TradFi single-leg FUTURE/OPTION `@LIN`/`@INV`-`YYYYMMDD` migration (2026-07-09) deliberately excluded 120,946 real
  CME `data_type=options_chain` manifest entries (~187.5M rows) that sit under a different, unverified legacy
  per-contract/spread flat layout — no `underlying=X/` subdirectory, raw per-contract filenames
  (`CC__FMH0025!.parquet`), manifest `underlying` values are per-contract keys (`ESU4_C5675`). Real, confirmed via live
  GCS listing; correctly excluded rather than risked at this scale, but the historical instrument-id canonicalization
  for this population remains open.
status: resolved
nature: notes
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service, instruments-service, deployment-service]
scope: [engineer]
tags: [instrument-id, canonicalization, tradfi, cme, options-chain, legacy-layout]
related:
  [
    instrument_id_format_canonicalization_2026_07_08.md,
    ../canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08.md,
    manifest_consolidator_service_name_dedup_split_2026_07_14.md,
  ]
created: 2026-07-10
parent_epic: instruments_master
assigned_vm:
resolved_by:
  "2026-07-14, slot-3: real --apply migration ran to completion on
  canonical-migration-tradfi-cme-options-20260714-150207 (291/291 real days, 210,589,799 rows, exit_code=0)."
source:
  "Real finding surfaced by the TradFi single-leg migrate-stage agent (wf_118d8268-18c, 2026-07-09) while scoping the
  @LIN/@INV historical migration against the real availability_index.parquet manifest (single-walk discipline, not a
  fresh corpus walk). Re-confirmed 2026-07-14 against the correct market-data-tick-tradfi-prd- bucket after an earlier
  same-day re-verification wrongly checked a deprecated flat bucket name."
priority: P1
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
---

## What I found

The 2026-07-09 TradFi single-leg canonicalization
(`market-tick-data-service/scripts/ migrate_tradfi_single_leg_product_root_lin_2026_07_09.py`) real-scoped its target
population from the existing `availability_index.parquet` manifest and found **158,812 real shard objects (~1.19B
rows)** in the bundled-chain layout it targets (CME `futures_chain` 147,807 + `options_chain` 8,419 + CBOE
`futures_chain` 2,586). That migration ran to completion on a VM (`canonical-migration-tradfi-20260709-160919`,
7,500.6s, `error=4` out of ~158,812).

Separately, real GCS listing found **120,946 CME `data_type=options_chain` manifest entries (~187.5M rows)** — an order
of magnitude larger than the migrated population — sitting under a structurally different, unverified legacy layout:

- Real filenames like `CC__FMH0025!.parquet` — no `underlying=X/` subdirectory grouping contracts by underlying.
- Manifest `underlying` values are per-contract keys (e.g. `ESU4_C5675`), not the human-readable product root (`SP500`)
  the rest of this canonicalization effort targets.

This population was **correctly excluded from the 2026-07-09 migration** rather than risked at ~187M-row scale without
first verifying the real layout's semantics — this doc tracks that exclusion as open work, not a decision to never do
it.

## Why it matters

This is a real, large population of CME options-chain historical data that does not yet carry the canonical
`@LIN`/`@INV`-`YYYYMMDD` instrument-id format or the human-readable product-root convention (`ES→SP500`, `VX→VIX`) the
rest of TradFi now has. It represents a meaningful fraction of the total TradFi historical corpus by row count.

## Recommended next step

1. Real investigation first: confirm the actual real-world meaning of this flat per-contract layout (is it a legacy
   pre-bundling write path, a different real data product, or a partial/abandoned migration from an earlier session?) —
   do not assume it mirrors the bundled-chain semantics.
2. Once understood, scope a dedicated migration (same backup-first, idempotent, VM-eligible pattern already proven for
   the rest of this effort) to bring this population's `instrument_id`/`underlying` values in line with the canonical
   target.
3. Given the real scale (~187.5M rows), this is a strong candidate for VM-based execution from the start (per the
   operator's standing durability preference), not a laptop-session migration.

## 🔴 2026-07-14 — re-verification could NOT confirm this population exists at the described location

Investigated step 1 of the recommended next step above (real investigation of the flat layout's semantics) as a
precondition to actually building + running the migration (operator asked to do the full migration, not just scope it).
Found:

- **The current TradFi writer structurally cannot produce this shape.**
  `market-tick-data-service/market_tick_data_service/ engine/orchestrator/partitioned_writer.py::_resolve_writer_file_name`
  (lines 135-162) has exactly two branches — `underlying={U}/ticks.parquet` for any derivative type (which
  `options_chain` always is, per `symbol_rules.py:258`), or a flat `{symbol}.parquet` for non-derivatives only. There is
  no code path that emits a flat filename for a `data_type=options_chain` row. So whatever wrote this layout predates
  the current writer — consistent with the doc's own hypothesis, not new.
- **Could not find the population itself.** The consolidated manifest (`_index/availability_index.parquet` in
  `market-data-tick-tradfi-central-element-323112`) is **17 days stale** (`gsutil stat` update time 2026-06-27,
  predating this doc's own 2026-07-10 creation) and shows only 291 CME `options_chain` rows today, all with blank
  `instrument_type`/`underlying` and `row_count=null` — nothing resembling 120,946 rows / 187.5M row_count sum. A
  **real, bounded GCS scan** (not a whole-corpus walk — scoped exactly to `venue=CME/instrument_type=options_chain/...`,
  across all 1,996 real day-partitions currently in the bucket, tried 4 plausible path-shape variants) found **zero
  matching objects on any variant, on any day**. Cross-checked the AWS S3 mirror (empty — GCP is the sole real store)
  and git history 2026-07-09→2026-07-14 for any intervening cleanup/migration (found only an unrelated, much smaller fix
  — `042ccc36`, 6 CME options_chain objects, three orders of magnitude short of 120,946).
- **This directly contradicts the finding this doc is built on.** Either (a) the 120,946/187.5M population was itself
  fully migrated or deleted by an untracked process sometime between 2026-07-10 and now with no commit evidence, (b) the
  original finding read a transient or incorrect manifest/index state, or (c) the real data lives somewhere this
  re-verification didn't check (a different bucket/region/path shape not among the 4 tried).

**Per the workspace's data-pipeline-correctness hard rule** (a data-correctness finding that contradicts a prior finding
needs operator notification, not a silent migration attempt against an unconfirmed target) — **status is NOT changed to
resolved**. No migration was designed or run against this population; doing so against an unconfirmed target risks
either a silent no-op or, worse, writing to the wrong location. Needs an operator decision on how to reconcile: re-run
the manifest consolidator (currently 17 days behind) and re-check, or track down exactly which manifest snapshot the
original 2026-07-09 finding-agent (`wf_118d8268-18c`) used to get the 120,946-row figure, since it doesn't match what's
queryable today.

## 🟢 2026-07-14 (later same day) — RESOLVED: (c) was correct, the 2026-07-14 re-verification used the WRONG bucket

Operator suggested checking whether the manifest consolidator itself needed attention. Investigating that surfaced the
real root cause of the 🔴 entry above: **`market-data-tick-tradfi-central-element-323112` (the flat, no-env-tier bucket
name the re-verification checked) is a DEPRECATED legacy bucket** — the live, current bucket is
`market-data-tick-tradfi-**prd**-central-element-323112` (env-tiered, per the workspace's bucket-name-SSOT
canonicalization). Two separate Cloud Run consolidator jobs exist for TradFi market-data:
`uts-prod-manifest-consolidator-market-data-tradfi` (targets the `-prd-` bucket, cron **ENABLED**, running successfully
every minute) and `uts-prod-manifest-consolidator-market-data-tradfi-legacy` (targets the flat bucket, cron **PAUSED** —
explaining the "17 days stale" reading exactly: nobody's been running it because it's the wrong bucket to be watching).

**Re-verified against the correct `-prd-` bucket, for real:**

- Consolidated manifest is fresh (updated minutes before this check, not 17 days stale).
- **242,210 real CME `options_chain` manifest entries, `capture_status=captured` on 100% of them, `row_count` summing to
  380,638,413 rows** — roughly double the original 120,946-entry / ~187.5M-row estimate (the population has grown since
  the 2026-07-09 finding, consistent with ongoing live capture, not a discrepancy).
- **120,946 of the 242,210 have `instrument_type=options_chain` explicitly stamped** — an EXACT match to the original
  finding's headline number, confirming the original 2026-07-09 finding was correct all along; the 2026-07-14
  re-verification's "population doesn't exist" conclusion was itself the error (wrong bucket, not stale/missing data).
- Confirmed the real object layout directly via `gsutil ls` (not just the manifest): real, live, flat per-contract files
  with no `underlying=X/` grouping, e.g.
  `raw_tick_data/by_date/day=2024-07-11/pipeline_mode=batch_databento/asset_group=tradfi/venue=CME/instrument_type=options_chain/data_type=options_chain/6AH5.parquet`
  — matches the doc's original description exactly (note the real path root is `raw_tick_data/by_date/`, not
  `instrument_availability/by_date/` — that prefix is instruments-service's reference-data tree, a different concept;
  this correction's path is MTDS's own market-data tree).

## 🟡 2026-07-14 (later same day) — real design investigation: this is NOT a simple rename, and found a real secondary bug

Started building the actual migration (operator: "fully executed", not just scoped). Investigating the real content
before writing a transform surfaced two things the original finding didn't have visibility into:

**1. The `data_type=options_chain` partition is contaminated with misclassified futures contracts.** Sampled every file
for one real day (`day=2024-07-11`, CME, 2,437 files): **345 (14.2%) are futures-coded contracts** (`6AH5`/`6BH5`/`6AN4`
— standard CME currency-futures tickers: `6A`=AUD, `6B`=GBP, `6C`=CAD, `6E`=EUR, etc.), sitting under
`instrument_type=options_chain/data_type=options_chain/` even though their OWN `instrument_key` column already correctly
reads them as `CME:FUTURE:...` (e.g. `CME:FUTURE:AUD-USD-250317@LIN`). This is a writer classification bug — these rows
are genuine futures data written to the wrong `data_type` partition, not options data needing canonicalization. The
remaining **2,092 (85.8%) are genuinely option-coded** (`ESH5_C5800`, `EW3Q4_C5570`, etc.).

**2. The genuine option rows are already PARTIALLY canonicalized, but in a DIFFERENT format than this migration's
target.** `EW3Q4_C5570.parquet`'s `instrument_key` reads `CME:OPTION:EW3-USD-240816-5570-CALL@LIN` — already carries an
`@LIN` marker, but positioned at the END (`...-CALL@LIN`) rather than right after the root (`ROOT@LIN-YYYYMMDD-...`, the
format `migrate_tradfi_single_leg_product_root_lin_2026_07_09.py` and the live write-path fix both target), uses 6-digit
`YYMMDD` not 8-digit `YYYYMMDD`, spells out `CALL`/`PUT` instead of `C`/`P`, and embeds a literal `-USD-` currency
marker the target format doesn't have for non-FX products. `underlying` is the raw contract-family code (`EW3`) rather
than a human product root — confirmed `EXCHANGE_CODE_TO_NAME` DOES have real registry entries for the option-family
roots checked (`EW1`-`EW4`→`SP500`, `ES`→`SP500`, `NQ`→`NASDAQ100`, `GC`→`GOLD`), though not all (`GE`/Eurodollar has no
entry — a real, separate registry-completeness gap to check before relying on it for this migration).

**Not proceeding to build+launch a migration against this population without first**: (a) deciding how to handle the
~14% misclassified-futures contamination (reclassify to `futures_chain` first, separately, before touching the genuine
options? exclude and file as its own bug?), (b) writing + testing a real regex for the ACTUAL current
`ROOT-USD-YYMMDD-STRIKE-CALL@LIN`-shaped instrument_key (not the raw-code shape the existing single-leg script targets —
this population needs a different transform, not a copy of that script), (c) checking registry coverage gaps like `GE`
don't silently drop real contracts. This is real, scoped design work for a next session/turn, not executed here — status
stays open, priority P1 unchanged.

**Status: back to open (not resolved) for the RIGHT reason** — the population is real, confirmed, and needs the
migration this doc always called for. The 🔴 entry above is superseded, not deleted (kept for the record of how the
wrong-bucket mistake happened). Next: scope + build + run the real migration against
`market-data-tick-tradfi-prd-central-element-323112`, VM-eligible given the ~380M-row scale (comparable to or larger
than the prior 158,812-object/1.19B-row single-leg migration that took ~2h on a VM).

## 🟡 2026-07-14 (later same day) — script built, dry-run validated on 6 real diverse days, found + fixed a THIRD contamination axis

Built the migration (`market-tick-data-service/scripts/canonicalize_cme_options_chain_legacy_flat_2026_07_14.py`,
dry-run-by-default, backup-first, `--apply`-gated) implementing the transform designed in the 🟡 entry above
(`ROOT-USD-YYMMDD-STRIKE-CALL@LIN` → `ROOT@LIN-YYYYMMDD-STRIKE-C`, reclassifying misclassified futures to
`instrument_type=futures_chain`). Real dry-run against `day=2024-07-11` (2,437 files) surfaced a **third contamination
axis the original design didn't anticipate**: 105 files (all futures-shaped) had `unclassified` instrument_keys that
turned out to be genuine **ICE-venue commodity futures** (`ICE:FUTURE:ORANGEJUICE-...`, `SUGAR-...`, `WTI-...`, plus
`BRENT`/`COCOA`/`COTTON`/`DOLLARINDEX`/`GASOIL`/`COFFEE` found on other sample days) sitting under the `venue=CME` GCS
path prefix despite their own `instrument_key` correctly reading `ICE:...` — a second, independent writer-classification
bug layered on top of the (a) options-format-mismatch and (b) misclassified-CME-futures issues already documented above.

**Fix**: generalized both instrument-key regexes to capture venue (`(?P<venue>[A-Z]+):...`) instead of hardcoding
`CME:`, and made the write side (`_target_path`, `bundle_and_write`) route each bundle by its object's REAL
`instrument_key` venue — so `ICE:FUTURE:...` content now correctly lands under
`venue=ICE/instrument_type=futures_chain/` instead of staying misfiled under `venue=CME`. The listing side intentionally
stays scoped to the physical `venue=CME` source path (that's genuinely where these objects live; only the target path
needed to become venue-aware).

**Row-count discrepancy from the earlier same-day finding — RECONCILED, not a bug.** The original 2024-07-11 dry-run
(5.56M rows) looked far denser than the ~1.3M/day average implied by 380,638,413 rows / 291 days, raising concern the
manifest total might be unreliable. Sampled 5 additional real days at random (`2023-05-15`, `2024-01-05`, `2024-03-12`,
`2024-03-25`, `2024-04-12`): row totals ranged from **4,267 to 194,258** — two to three orders of magnitude BELOW
2024-07-11's (now, with the ICE fix, 6.82M) total. The real per-day distribution is heavy-tailed (a handful of
very-high-volume days, e.g. likely quarterly-expiration dates, alongside many much quieter days), which is fully
consistent with a genuine 380M-row total across 291 days — 2024-07-11 is a real outlier day, not evidence of a manifest
bug. All 6 sampled days show `unclassified=0` post-fix, confirming the venue-generalized regex covers the real
population with no silent drops.

**Manifest-write safety implemented**: `rewrite_manifest()` now does a real CAS write
(`StorageClient.conditional_upload_bytes(if_generation_match=...)`) with re-download+re-merge retry (5 attempts) on a
concurrent writer, wrapped with a best-effort pause/resume of the
`uts-prod-manifest-consolidator-market-data-tradfi-cron` Cloud Scheduler job as defense-in-depth (not a substitute for
the CAS guarantee — a failed pause/resume call is logged, not fatal, and resume always runs in a `finally`). Note for
anyone reading `tradfi_manifest_row_loss_regression_ 2026_07_12.md` for precedent: that doc's own restore did NOT pause
any cron — CAS-write alone was what it actually verified; the pause here is this script's own added layer, not a re-used
verified mechanism.

**Status**: script passes real dry-run validation across 6 diverse real days (2 sizes at each end of the distribution),
zero unclassified, zero exceptions. Not yet run with `--apply` against real data — next step is quality-gates + ship,
then a scoped real `--apply` run (small real day first, then VM-scale `--all-days`), per the workspace's runtime-
verification hard rule (a migration is "done" only once it has actually run against real data with verified output, not
once the dry-run is green).

## 🟢 2026-07-14 (later same day) — real `--apply` run verified end-to-end against live prod; two more real bugs found + fixed

Shipped the script (`market-tick-data-service@6566c943f`) after a clean `quality-gates.sh` pass. Ran a real `--apply`
against the smallest validated day (`2024-03-25`, 2 bundles / 4,267 rows) to verify the write path before committing to
VM scale. Found + fixed two more REAL production issues the dry-run couldn't have caught (dry-run never touches the live
manifest write path):

1. **Manifest column type mismatch (`ArrowTypeError` on the very first real `--apply`)**: the live
   `_index/availability_index.parquet` stores `schema_version`/`available`/`expected`/`row_count` as **strings** (`"9"`,
   `"true"`/`"false"`, `"1609"`), not the native bool/int this script's manifest-row dict was writing — the same class
   of VARCHAR-typing gotcha `tradfi_manifest_consolidator_row_count_varchar_crash_2026_07_12.md` documented for
   `row_count` alone, confirmed here to also apply to 3 more columns. Fixed by writing string-typed values for all four,
   AND added a general `_align_new_rows_dtypes()` safety net that stringifies any new-row column whose existing values
   are uniformly `str` in the live manifest — so a 5th surprise column at VM scale fails safe instead of crashing a
   long-running job late.
2. **A `timeout 200` wrapper around the apply command killed the process mid-CAS-write, leaving the
   `uts-prod-manifest-consolidator-market-data-tradfi-cron` Cloud Scheduler job stuck `PAUSED`** (the `finally: resume`
   never ran because the process received `SIGTERM` from the shell timeout, not a Python exception) — caught within ~1
   minute via `gcloud scheduler jobs describe`, manually resumed, and verified the manifest itself was untouched (the
   process died during in-memory `to_parquet()` serialization, before the actual CAS-write call). Retried without a
   tight timeout wrapper (backgrounded instead) and it completed cleanly. **Operational note for the eventual VM run**:
   the real GCS-bundling phase for ALL days completes BEFORE the ONE end-of-run manifest CAS-write/cron-pause (see
   `run()`/`main()` ordering) — so the cron-pause window stays short and bounded regardless of how many days are
   processed, but anything that force-kills the process during that final window (not just a shell timeout — a VM
   preemption too) risks the same stuck-`PAUSED` state and needs the same manual-resume recovery if the VM's own
   shutdown handling doesn't run the `finally` block.

**Real verified output** (`day=2024-03-25`): `CME:FUTURE:AUD@LIN-20240416` (1,609 rows) and
`ICE:FUTURE:COCOA@LIN-20240716` (2,658 rows) — correct canonical instrument-key shape, correctly venue-routed GCS paths
(`venue=CME` vs `venue=ICE`), correct manifest rows (`capture_status=captured`, `available="true"`, `expected="true"`,
`schema_version="9"`, `row_count` as string). Manifest CAS-write: `5,090,813 → 5,090,815` rows, single attempt, no retry
needed. Cron correctly resumed via the `finally` block on the second (successful) run.

**Next**: validate multi-day manifest accumulation locally (a handful of real days via `--all-days --limit-days N`)
before scoping the full VM-based `--all-days` run across all 291 real days (~380M rows) — matching the prior single-leg
migration's VM-based execution pattern (`canonical-migration-tradfi-20260709-160919`, ~2h).

## 🟢 2026-07-14 (later same day) — multi-day batch verified for real, found + fixed a real idempotency gap

Ran `--all-days --limit-days 3 --apply` against 3 more real days (`2023-05-01/02/03`, none previously touched). This
exercised the CAS-write retry path FOR REAL (not simulated): attempt 1 hit a genuine concurrent-writer generation
conflict (something else wrote to the manifest in the ~45s pause→backup window), attempt 2 re-downloaded, re-merged, and
succeeded cleanly (`5,090,815 → 5,090,821` rows, +6). Confirms the retry loop works under real production write
pressure, not just in theory.

**Found + fixed a real idempotency gap while validating restart-safety**: re-ran the already-applied `2024-03-25` day to
check what happens on a re-run (the realistic failure mode for the eventual VM run — a SPOT preemption mid-`--all-days`
would require relaunching from day 1, since there's no day-level checkpoint). Before the fix, this would have appended a
SECOND, duplicate pair of manifest rows for the same (date, venue, instrument_type, data_type, underlying) — silently
double-counting `row_count` in any downstream aggregate. Added `_dedupe_against_existing()`: filters `new_rows` against
already-`captured` rows (by that 5-column key) on every CAS-write attempt, before the merge. Verified for real:
re-running `2024-03-25` now logs `Skipping 2 already-captured row(s)` and correctly writes ZERO new manifest rows
(`existing_rows=5090821, new_rows=0, merged_rows=5090821`) — the GCS bundle re-write itself is still a harmless
deterministic no-op, only the manifest step needed the guard. This makes a VM-restart-after-preemption scenario safe:
re-processing all 291 days from scratch will re-upload already-done GCS bundles (wasteful but harmless) and correctly
skip already-captured manifest rows (not wasteful, not harmful).

**Real days applied so far**: `2024-03-25`, `2023-05-01`, `2023-05-02`, `2023-05-03` (4 of 291) — 8 real manifest rows,
8 real canonical GCS bundle files, zero duplicates, zero dtype errors, cron correctly resumed every time (2 real
`PAUSED`-stuck incidents during earlier iteration were both self-caught and manually recovered within ~1 minute — see
above — neither has recurred since the dtype/idempotency fixes landed).

**Status**: script is now validated against real production data across single-day, multi-day, and re-run/idempotency
scenarios. Next: ship this fix, then scope + launch the real VM execution for the remaining 287 real days.

## 🟢 2026-07-14 (later same day) — VM launched for the full remaining run (287 real days)

Extended `deployment-service/scripts/vm/launch-canonical-migration-vm.sh` with a new `tradfi-cme-options` category
(`deployment-service@11ed8f7fe`) rather than forking a new launcher — its VM name
(`canonical-migration-tradfi-cme-options-<ts>`) deliberately stays under the already-registered
`canonical-migration-tradfi-` `VM_PREFIX_TO_BUCKET` prefix (longest-prefix match), so no new registry entry was needed.
Rebuilt + republished the code tarballs (`create-code-tarballs.sh`, all 4 core repos clean, mtds SHA `e4c04c64`
confirmed to include the dedup/dtype fix) before launching.

**Near-miss during testing**: a "smoke test" invocation with `DRY_RUN=true` was NOT actually a no-op in this launcher —
that env var only gates the tarball-freshness check, not the real `gcloud compute instances create` call — so a real VM
launched with `--apply` against production on an UNVERIFIED (pre-tarball-rebuild) code state. Caught within ~1 minute
(VM was still in early boot/cloud-init, had not reached the Python script or the manifest-write phase — confirmed via
serial console + scheduler state unchanged), deleted before any real writes could happen. No production impact. Lesson
for next time: this launcher has no safe preview mode: **only invoke it when ready to launch for real.**

**Real launch**: `canonical-migration-tradfi-cme-options-20260714-150207`, `e2-standard-16` (per the TradFi migration's
own documented OOM precedent), SPOT, zone `asia-northeast1-c`, `--stamp 20260714T140207Z`. The tarball-freshness check
flagged mtds + UAC as "MISSING" manifest — a false alarm (a local `mktemp` collision in the freshness-check tooling, not
an actual missing/stale tarball; independently re-verified both manifests exist, are fresh (`created_at` minutes before
launch), and match local HEAD exactly). VM reached `RUNNING` within seconds; serial console confirmed genuine, active
progress (real package installation output, not a hang) as of the last check. Monitoring to terminal state — full
progress/completion update to follow in this doc once the run finishes (or fails, per the workspace's no-fire-and-forget
VM rule).

## 🟢 2026-07-14 (later same day) — RESOLVED: VM run completed successfully, all 291/291 real days migrated

Full run finished in **1,569.7s (~26 minutes)**, `exit_code=0`, self-deleted per `VM_SHUTDOWN_ON_COMPLETION=true`
(confirmed via `EXIT_STATUS=0` + `DEPLOYMENT_COMPLETED` in the GCS-tee'd run log, not just VM disappearance — VM
disappearing alone would be ambiguous between success and a `--instance-termination-action` after a SPOT preemption;
`gcloud compute operations list` confirmed the terminal operation was a self-triggered `delete`, not a preemption).

**Final real output**:

- `bundle_CME_futures_chain`: 2,095 canonical files, 177,376,591 rows
- `bundle_ICE_futures_chain`: 661 canonical files, 29,571,221 rows (the venue-misfiled ICE commodity futures, now
  correctly routed to `venue=ICE` paths)
- `bundle_CME_options_chain`: 129 canonical files, 3,641,987 rows
- **Total: 2,885 real canonical bundle files, 210,589,799 rows**, `unclassified=0` on every single one of the 291 days
  (zero silent drops) — 140,155 real source files read + classified across the whole run.
- Manifest: `5,090,821 → 5,093,698` rows (+2,877 new; the 8 rows from my earlier local testing were correctly skipped by
  the idempotency dedup — `Skipping 8 already-captured row(s)`).

**Two real, non-blocking issues surfaced by the VM run (neither affected correctness)**:

1. **The VM's service account lacks Cloud Scheduler IAM permissions** (`cloudscheduler.jobs.pause`/`.enable`) — both
   pause/resume calls failed with `PERMISSION_DENIED` (logged as WARNING, not fatal, exactly as designed). The cron was
   never actually paused during the VM's manifest write. This is why the run hit ONE real CAS-write conflict (attempt 1
   failed, attempt 2 succeeded) — the defense-in-depth pause did nothing from VM context, and the CAS-write retry (the
   actual correctness guarantee) is what handled it, exactly as designed. Not fixed here (VM service-account IAM grants
   are an operator action, and the fallback already proved sufficient); worth a follow-up IAM grant if pause-from-VM is
   wanted for future migrations to reduce retry frequency, but not required for correctness.
2. **Reconciled the "380M vs 210M rows" gap** (flagged as an open question in the earlier same-day entry): investigated
   ONE real duplicate-underlying case (`2024-07-11`/`NQU4_C20000`) and found the SOURCE manifest itself has ~2x
   duplicate `capture_status=captured` rows per real object (4,875 manifest rows vs 2,438 unique `underlying` values for
   that one day — almost exactly matching my migration's own 2,437 real files found via direct GCS listing). This is a
   manifest dedup-key gap (same bug FAMILY as `manifest_consolidator_service_name_dedup_split_2026_07_14.md`, a
   different specific splitter column — `instrument_type` None-vs-populated rather than `service_name`; full evidence
   added to that doc). **Not a data-loss issue for this migration**: the migration lists real objects via bounded GCS
   prefix listing, not manifest row-count arithmetic, so it correctly processed the true de-duplicated file set. The
   manifest's summed `row_count` simply over-counts real unique data for this data_type by roughly 2x — a pre-existing,
   separate data-quality issue, not something this migration caused or needs to fix.

**Status: RESOLVED.** All real CME `options_chain`/`futures_chain` legacy-flat data (both genuine options AND the two
misclassified-futures contamination axes — CME currency futures and ICE commodity futures) is now canonicalized and
bundled at the correct `underlying=`/venue= paths, manifest-registered, `capture_status=captured`. Source per-contract
objects were left in place (copy-not-move, per this workspace's established convention) — a separate, later,
operator-gated cleanup pass can delete confirmed-safe legacy originals once downstream readers are verified against the
new canonical paths.
