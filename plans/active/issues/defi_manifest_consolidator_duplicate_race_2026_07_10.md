---
doc_type: issue
title: DeFi manifest has 1.79M genuine duplicate rows — recurring consolidator race, ~2 months old
summary:
  "A live spot-check during the 2026-07-10 backlog apply found the SAME empty_confirmed row
  (ALCHEMY/ARBITRUM/gas_fees/2018-01-01) written twice by two enumerator runs 2.5 weeks apart. A full scan of
  gs://market-data-tick-defi-prd-central-element-323112/_index/availability_index.parquet found 4,630,138 defi rows in
  duplicate-key groups; of those, 1,789,793 groups have IDENTICAL capture_status across every copy (genuine,
  zero-new-information duplication — pure denominator inflation). The other 525,276 groups have DIFFERING capture_status
  (legitimate state-transition history, e.g. expected_unattempted -> captured) and are NOT duplicates.
  Duplicate-contributing enumerator_run_ids span 2026-05-07 through 2026-07-10 (~2 months), consistent with the
  recurring DAILY expected-universe-v2 Cloud Scheduler job repeatedly hitting the same race. Root cause not fixed (out
  of this doc's immediate scope) — hypothesis: the per-VM-shard-to-main-index consolidator deletes a shard before (or
  without atomically) completing its merge into the main index, so a run landing in that window sees neither the shard
  nor the merged row and re-enumerates already-covered honest-absence cells."
status: open
nature: notes
asset_group: [defi]
stage: [data]
repos: [instruments-service, unified-trading-library]
scope: [engineer]
tags: [manifest, duplication, consolidator, honest-coverage, defi, data-correctness]
related:
  [
    plans/active/issues/defi_expected_unattempted_backlog_1m_2026_07_03.md,
    codex/02-data/availability-manifest-and-data-status.md,
    codex/05-infrastructure/manifest-consolidator-ssot.md,
  ]
created: 2026-07-10
parent_epic: instruments_master
priority: P1
source:
  "Found live during the 2026-07-10 DeFi expected_unattempted backlog apply
  (defi_expected_unattempted_backlog_1m_2026_07_03.md). A second year-chunked apply pass re-wrote the exact same
  2018/2019 candidates the first pass already wrote, prompting a direct manifest spot-check that surfaced this much
  larger, pre-existing pattern."
assigned_vm: NA
execution_scope: local-only
model_tier: sonnet-doable
thinking_tier: medium
estimate_class: infra
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.6
last_updated: 2026-07-10
supersedes:
superseded_by:
depends_on:
assigned_role: data-pipeline-engineer
drift_direction: advance-code
locked_by:
locked_since:
resolved_by:
---

## Real evidence

- **Direct spot-check**: `(venue=ALCHEMY, chain=ARBITRUM, data_type=gas_fees, date=2018-01-01)` present TWICE in the
  live manifest — once written `2026-06-22T11:38:24Z` (`enum-reseed-defi-gas-20260622-113817`), once written
  `2026-07-10T13:03:24Z` (`enum-universe-defi-20260710-130231`, my own session's first year-chunked backlog apply). Both
  rows are byte-identical on every non-provenance column (`capture_status=empty_confirmed`,
  `error_reason=EXPECTED_PRE_GENESIS_CHAIN`).
- **Full-manifest scan** (`asset_group=defi`, 15,805,771 rows before fix): 4,630,138 rows sit in duplicate-key groups
  (key = `asset_group, venue, chain, data_type, instrument_type, instrument_id, date`).
  - **1,789,793 rows removed as genuine duplicates** — identical key AND identical `capture_status` across every copy in
    the group (kept the latest `written_at` copy per group).
  - **525,276 groups left untouched** — differing `capture_status` across copies, i.e. real state-transition history
    (the manifest is append-only; this is expected and correct).
- **Duplicate-contributing `enumerator_run_id`s** (top offenders, by row count): `enum-universe-defi-20260706-130616`
  (1,379,692), `enum-universe-defi-20260710-130231` (896,860, mine), `enum-universe-defi-20260710-130607` (884,608,
  mine), `enum-universe-defi-20260507-145635` (390,419), `enum-universe-defi-20260624-102449` (268,878),
  `enum-universe-defi-20260624-013038` (216,873), `enum-universe-defi-20260628-013034` (42,086),
  `enum-reseed-defi-gas-20260622-113817` (13,416), + smaller. **This predates the current session by ~2 months** — the
  vast majority (≈2.85M of 4.63M) comes from runs dated 2026-05-07 through 2026-07-08, well before today.

## Root-cause hypothesis (NOT fixed here — needs its own investigation)

`launch-expected-universe-v2-vm.sh`-style runs write to a per-VM shard (`_index/per_vm/<vm-name>.parquet`), and a
separate consolidator process later merges the shard into the main `_index/availability_index.parquet`, then
(apparently) deletes the shard — confirmed live: the shard for `expected-universe-v2-defi-20260710-140018` (my session's
2018 chunk) existed at 13:57 (found + correctly present-set-augmented by a verification scan) but was GONE by 14:35, and
its data WAS present in the main index by then (2 rows, not 1 — i.e. the merge succeeded but so did a second independent
write). A second enumerator run targeting the same window, landing after the shard was gone but seemingly before (or
without correctly reading) the merged row, recomputed and rewrote the identical candidates. The `_build_present_set()`
function itself does not filter by `capture_status` (correct — it should treat every already-written row as "present"
regardless of status), so the bug is not there; it's somewhere in the shard-lifecycle / manifest-read timing around
consolidation. The recurring daily Cloud Scheduler job (`expected-universe-v2-<ag>-daily`, `codex` runbook: "RECURRING
daily 01:30 UTC") landing on this same race for ~2 months is the most likely explanation for the ~2.85M pre-existing
duplicates.

## Fix shipped (dedup only — NOT the root cause)

`instruments-service/scripts/defi_manifest_dedup_2026_07_10.py` — one-off, backup-first (full pre-dedup manifest
snapshot to `_migration_backup/defi_manifest_dedup_2026_07_10/`), verify-after, with an explicit safety check (asserts
the count of legitimate multi-`capture_status` key-groups is UNCHANGED before writing — refuses to touch anything that
isn't a byte-identical duplicate). Removes exactly the 1,789,793 genuine-duplicate rows, keeping the latest `written_at`
copy per `(key, capture_status)` group.

## Todos

- [x] [VERIFY] P1. Confirm the finding is real (direct manifest spot-check + full duplicate-key scan). Done, see "Real
      evidence" above.
- [x] [SCRIPT] P1. Write + dry-run-verify the dedup fix. Done —
      `instruments-service/scripts/defi_manifest_dedup_2026_07_10.py`.
- [x] ✅ [INFRA] P1. **Applied to production 2026-07-10.** `defi` manifest rows 15,805,771 → 14,015,978 (removed
      1,789,793). Backup verified (463,952,531 bytes) at
      `gs://market-data-tick-defi-prd-central-element-323112/_migration_backup/defi_manifest_dedup_2026_07_10/availability_index_pre_dedup_20260710-143528.parquet`
      before the write. Safety check (legitimate multi-status groups unchanged at 525,276) held throughout.
- [ ] [DESIGN] P1. **Root-cause the consolidator race** — read `manifest_consolidator_ssot.md`'s actual merge
      implementation, confirm whether shard-delete happens before or atomically with the main-index write, and whether
      there's a read-time race for a manifest load that starts while a merge is in flight. This is what actually needs
      fixing — the dedup script only cleans up symptoms, and the daily scheduled job will keep recreating duplicates
      until this lands.
- [ ] [VERIFY] P2. Check whether the SAME race affects other asset groups (cefi/tradfi/prediction/sports) — this session
      found the identical `--start-date`/`--end-date`-bounded code path is shared across all asset groups, so the race
      is plausibly universal, not defi-specific. Not yet checked.
- [ ] [DATA] P2. Once root-caused and fixed, consider whether the daily Cloud Scheduler job's history should be audited
      for the same pattern in cefi/tradfi/prediction/sports.

## Progress Log

- 2026-07-10: Filed. Real evidence gathered via direct GCS parquet reads (not inferred). Dedup script written, dry-run
  confirmed 1,789,793 genuine duplicates + a safety check that the 525,276 legitimate state-transition groups are
  unaffected. `--apply` run in progress.
