---
doc_type: issue
title:
  "TradFi garbage-underlying recovery (2026-07-20): 428 content-recovered rows never registered under their real root +
  the run's own _quarantine/ physical mirror is now stale"
summary:
  While correcting the live tradfi availability_index for the 2026-07-20 garbage-underlying recovery run's 98,256
  processed rows (tradfi_satellite_ao_dispatch_batch2_2026_07_25.md item "Correct the live tradfi availability_index
  manifest for the ~97,828 combo/chain objects"), found that the run's own summed apply_outcomes.json Counters split
  cleanly into 97,828 genuinely-quarantined + 428 content-recovered-and-merged-elsewhere (97,828 + 428 == 98,256
  selected, 0 unaccounted). The 428 recovered rows' DATA now lives under a different (real) product root, but no NEW
  manifest row was ever registered for that root — the recovery script has no ManifestWriter call at all. Separately,
  verified the run's physical `_quarantine/` mirror for these 98,256 rows no longer exists on GCS today (only 9
  unrelated `day=2026-01-*` prefixes remain under `_quarantine/raw_tick_data/`, from a different quarantine event) — so
  a live GCS existence check can no longer disambiguate the two outcomes at the row level; only the retained TSV +
  apply_outcomes.json artifacts remain authoritative.
status: open
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [tradfi, manifest, recovery, registration-gap, data-correctness]
related:
  [
    /plans/archive/2026_07/tradfi_satellite_ao_dispatch_batch2_2026_07_25.md,
    /plans/archive/issues/cme_combo_underlying_extraction_garbage_2026_07_19.md,
  ]
created: 2026-07-27
author: unknown
priority: P2
parent_epic: tradfi_master
source:
  "tradfi_satellite_ao_dispatch_batch2-012 (Correct the live tradfi availability_index manifest for the ~97,828
  combo/chain objects), 2026-07-27"
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
assigned_vm: planning
resolved_by: ""
archive_exempt: true # BRIDGE 2026-08-12: clearing the stale locked_by:live-defi-rollout placeholder (operator ruling, option B, see /plans/active/issues/locked_by_live_defi_rollout_placeholder_corpus_wide_2026_08_10.md) immediately surfaces this doc as 0-open-todos archive-eligible. Per that ruling's explicit scope ("do NOT auto-archive in this same pass"), archival is deferred to a separate follow-on pass. Bridged via the sanctioned flip-then-mv two-commit pattern documented in scripts/plan-hygiene/check_archive_candidates.sh -- drop this line + git mv to plans/archive/[issues/] in that follow-on pass.
locked_by:
locked_since:
context_scope:
  [
    /plans/archive/2026_07/tradfi_satellite_ao_dispatch_batch2_2026_07_25.md,
    /plans/archive/issues/cme_combo_underlying_extraction_garbage_2026_07_19.md,
    market-tick-data-service/market_tick_data_service/scripts/recover_tradfi_chain_manifest_registration_2026_07_22.py,
    market-tick-data-service/market_tick_data_service/scripts/register_tradfi_recovery_quarantine_manifest_2026_07_30.py,
    /plans/epics/tradfi_master.md,
  ]
---

# TradFi garbage-underlying recovery: 428 recovered rows unregistered + stale quarantine ground truth

## What I found

Working `tradfi_satellite_ao_dispatch_batch2-012` (correct the live tradfi `availability_index` manifest for the
`recover_tradfi_garbage_underlying_2026_07.py --apply` run `20260720-120911`), I downloaded and summed all 20 shards'
retained `recovery_mapping.tsv` + `*.apply_outcomes.json` artifacts (never a fresh GCS walk — per the plan's own
instruction). Two findings:

1. **428 rows were content-recovered, not quarantined, and were never registered under their real root.** The run's
   `A_QUARANTINE` category total across all 20 shards is 98,256; the summed `attempted_failed` outcome is exactly
   97,828; the summed `RECOVERED:*` outcome is exactly 428; 97,828 + 428 == 98,256 with zero unaccounted/error outcomes.
   `recover_tradfi_garbage_underlying_2026_07.py` has no `ManifestWriter` call anywhere in it (verified via full read),
   so neither branch ever touches the manifest. The 97,828 genuinely-quarantined rows are the ones this task's
   manifest-correction script (`correct_tradfi_recovery_quarantine_manifest_2026_07_27.py`) marks `attempted_failed` —
   but the 428 recovered rows' real, content-resolved data now sits in a canonical bundle under a DIFFERENT root with NO
   manifest row of its own. This mirrors the exact gap `recover_tradfi_chain_manifest_registration_2026_07_22.py`'s
   register phase already fixes for a DIFFERENT raw-underlying corpus (per-contract Databento symbols stored raw in
   `underlying=`) — the same register-then-verify pattern would apply here, just against this recovery run's 428-row
   population instead.

2. **The run's physical `_quarantine/` mirror for these 98,256 rows is gone.** I initially designed the
   manifest-correction script to disambiguate the 97,828-vs-428 split via a targeted `gcs_describe_object` existence
   check against each row's quarantine target (`_quarantine/<original_rel>`) — mirroring
   `recover_tradfi_chain_manifest_registration_2026_07_22.py`'s `confirm_targets_on_gcs` pattern. Live-verified
   2026-07-27: 0/98,256 targets exist. Listing `_quarantine/raw_tick_data/by_date/` (non-recursive, bounded — not a
   corpus walk) shows only 9 `day=2026-01-*` prefixes today, holding a DIFFERENT population entirely
   (`underlying=CME:OPTION:EW1-USD-260102-...@LIN` — a full instrument id stored as `underlying=`, not the
   numeric/opaque garbage codes this run processed). No bucket lifecycle rule explains this (only a 60-day Coldline
   storage-class transition; no auto-delete rule). Some unrelated, unidentified later operation evidently reused or
   pruned `_quarantine/raw_tick_data/` since 2026-07-20. Net effect: going forward, the retained TSV/JSON artifacts are
   the ONLY surviving ground truth for this run's outcome split — the live bucket can no longer corroborate it.

## Why it matters

Finding 1 is a small (0.44%), bounded, always-fixable-later data-visibility gap: 428 tradfi combo/chain cells have real
captured data sitting under a canonical bundle with no manifest row pointing at it, so a consumer querying by that real
root would see it as `todo`/missing rather than `captured`. Finding 2 means this specific disambiguation opportunity is
now closed — any future attempt to split this population by physical GCS state will get the same false "nothing
confirmed" result. Not urgent (finding 1 is additive-only, no destructive risk; finding 2 is a closed door, not an open
wound), but should be tracked rather than silently absorbed.

## Recommended decision

- [x] ✅ [SCRIPT] P2. Write a register-phase script (mirroring
      `recover_tradfi_chain_manifest_registration_2026_07_22.py`'s register phase) that: for each of the 428
      `RECOVERED:*` rows implied by this run's per-shard `apply_outcomes.json` (the aggregate count is known; deriving
      the EXACT 428 keys requires either re-deriving the recovered root from the CURRENT canonical bundle's content — a
      targeted read per candidate combo/chain cell already resolved by the sibling migrate/rebundle tooling — or
      accepting that the exact 428 keys are unrecoverable and instead doing a targeted sweep: for every `A_QUARANTINE`
      TSV candidate whose OLD key is NOT registered `captured` anywhere, check whether a real-root canonical bundle
      exists for its (day, venue, instrument_type, data_type) tuple and, if so and no manifest row exists for that
      canonical key yet, register one additively (no CAS, mirrors `ManifestWriter.add()`/`per_vm_shards=True`)),
      confirms via targeted (never corpus-walking) `gcs_describe_object` checks, and additively registers the missing
      canonical rows. Repo: market-tick-data-service. **Done when**: every canonical bundle target reachable from this
      run's 98,256-row population that (a) physically exists on GCS today and (b) has no manifest row yet, is registered
      `captured`; count of newly-registered rows reported against the ~428 expected upper bound. —
      market-tick-data-service@c1e1de71: shipped `register_tradfi_recovery_quarantine_manifest_2026_07_30.py` (13 unit
      tests green, full quality-gates.sh clean). Implements the SWEEP alternative (the exact 428 keys are unrecoverable
      per the finding above — the run's own retained artifacts carry no per-row outcome, only the path-based A-category
      and the aggregate Counter): dedups the 98,256 A_QUARANTINE rows to their distinct
      (date,venue,instrument_type,data_type) cells, sweeps every recognised real product root per cell (excluding roots
      already keyed in the live manifest), confirms each candidate target via targeted `gcs_describe_object`, and writes
      a dry-run mapping TSV (`--apply` for the additive write). NOT yet executed against prod GCS — that dry-run +
      `--apply` pass is tracked as a new follow-up todo below (VM-scale I/O, out of scope for an interactive session per
      the heavy-I/O HARD RULE).
- [x] ✅ [SCRIPT] P2. Run `register_tradfi_recovery_quarantine_manifest_2026_07_30.py` (market-tick-data-service)
      against prod: first a dry-run (`--out register_mapping.tsv`, no `--apply`) and inspect the confirmed-candidate
      count against the ~428 upper bound + spot-check a sample of the mapping TSV's `target_uri` column for a real
      captured bundle; then, once the dry-run count looks sane, `--apply` (additive `ManifestWriter.add()`/
      `record_captured_from_counts()`, no CAS — safe to re-run) to register the confirmed rows, sharded
      (`--shard-of`/`--shard-index`) if the unsharded dry-run's candidate-key count makes a single-process
      `gcs_describe_object` sweep impractically slow. Repo: market-tick-data-service. **Done when**: the dry-run mapping
      TSV + confirmed count are reported, the `--apply` run completes, and a post-run spot-check confirms a sample of
      the newly-registered canonical keys read `captured` in the live manifest. — **Dry-run**: 248/585,331 candidates
      confirmed present on GCS (within the ~428 upper bound; 6,797 distinct cells x 144 recognised roots), 2
      independently spot-checked `target_uri`s confirmed real content on GCS. **Apply**: 248 canonical rows registered
      into `_index/per_vm/local-2108856-43a6.parquet` (additive, no CAS). **Data-correctness finding + remediation**
      (see `/plans/archive/issues/tradfi_register_underlying_translation_bug_2026_07_30.md`, RESOLVED): 98/248 (39.5%)
      of the written rows carried a manifest `underlying` that did NOT match the `underlying=` segment of the row's own
      physically-confirmed GCS path (chain instrument_types translate the root through `_exchange_to_product_root` when
      building the target path, but `apply_register` wrote the untranslated root). Caught BEFORE the
      manifest-consolidator cron merged the shard (main index `updateTime` 12:00:59 UTC, shard write 12:06:04 UTC,
      caught+patched by 12:10 UTC) — hand-patched the shard in place via a generation-CAS read-modify-write, verified 0
      remaining mismatches across all 186 affected cells. Root cause fixed at market-tick-data-service@35d1f328 (added
      `actual_underlying` to `RegisterCandidate`, used in both `apply_register` write branches; 4 new regression tests,
      19 total unit tests green). Also fixed an unrelated pre-existing QG-blocking failure (stale `SPORTS` shard-count
      pin, verified against `unified-api-contracts` commit history as a legitimate re-pin, not a regression) at
      market-tick-data-service@b4fd439e so both commits could ship. Full `quality-gates.sh` clean on both.
- [x] ✅ [DATA] P3. Investigate what pruned/reused `_quarantine/raw_tick_data/` between 2026-07-20 and 2026-07-27 —
      **ROOT CAUSE: UNABLE TO DETERMINE from committed evidence** (see Progress Log 2026-08-04, slot 14 investigation).
      The committed codebase contains no script, lifecycle rule, or automated process that deletes objects from
      `_quarantine/raw_tick_data/`. The `_rel()` function in `migrate_tradfi_canonical_2026_07.py` strips the
      `_quarantine/` prefix via `path.find(marker)` (a latent bug for already-quarantined objects), but this bug causes
      source-not-found errors (`SRC_ALREADY_GONE` / `QUARANTINE_VERIFY_FAILED`), NOT accidental deletions — confirmed by
      full trace through the apply-phase logic. Same latent bug is inherited by `rebundle_tradfi_chains_2026_07.py`
      (imports `_rel`), same non-deletion outcome. The 9 remaining `day=2026-01-*` prefixes (different quarantine event,
      `CME:OPTION:EW1-USD-...` data) confirm the removal was selective, not a bucket-level operation. Most plausible
      explanations: (a) manual operator cleanup via `gsutil rm` or equivalent, (b) uncommitted one-off cleanup script.
      Recommended follow-up: check Cloud Audit Logs for the tradfi tick bucket (`storage.objects.delete` on
      `_quarantine/raw_tick_data/` prefix, 2026-07-20 to 2026-07-27) if definitive identification is desired. The
      `_rel()` bug (stripping `_quarantine/` prefix on already-quarantined objects) is a latent correctness issue — file
      as a separate preventative fix. Repo: market-tick-data-service.
- [x] ✅ [CODE] P3. **Fix the latent `_rel()` prefix-stripping bug** in `migrate_tradfi_canonical_2026_07.py` (line
      160-163, `path.find("raw_tick_data/by_date/")`) — for an already-quarantined object
      (`_quarantine/raw_tick_data/by_date/...`), this strips the `_quarantine/` prefix and computes the WRONG
      bucket-relative path, causing the apply-phase to silently treat the object as `SRC_ALREADY_GONE` instead of
      correctly identifying it as already-quarantined and skipping it. Confirmed non-destructive today (traced both
      `A_COPY`/`A_QUARANTINE` code paths — neither deletes on this bug), but it's a real correctness defect, not just
      cosmetic. Same bug is inherited by `rebundle_tradfi_chains_2026_07.py` (imports `_rel`) — fix both call sites.
      Repo: market-tick-data-service. **Done when**: `_rel()` correctly detects the `_quarantine/` prefix (e.g. checks
      for it explicitly before stripping `raw_tick_data/by_date/`), a regression test covers an already-quarantined
      input path, and `quality-gates.sh` is green on both files. — market-tick-data-service@ff6c2f4a: already shipped
      (found already on origin at task pickup, landed as part of the batch7 hardening pass — `rel_with_holding_prefix()`
      in `_tradfi_migration_recurrence_fixes_2026_08_06.py`, explicitly citing this issue doc). Checks for
      `_quarantine/raw_tick_data/by_date/` and `_content_repair/raw_tick_data/by_date/` markers BEFORE falling back to
      the bare `raw_tick_data/by_date/` marker, so an already-held object's holding prefix is preserved instead of
      stripped. `migrate_tradfi_canonical_2026_07.py` aliases `_rel` to this function (line 121);
      `rebundle_tradfi_chains_2026_07.py` imports the same `_rel` symbol from the migrate module (one fix closes both
      call sites, per the commit message). 5 regression tests cover it in
      `tests/unit/scripts/test_migrate_tradfi_canonical_2026_07.py`: `test_rel_preserves_quarantine_holding_prefix`,
      `test_rel_preserves_content_repair_holding_prefix`, `test_already_quarantined_object_recognized_and_left_in_place`
      (asserts `D_ALREADY_HELD`/`A_SKIP`/no target),
      `test_already_content_repair_held_object_recognized_and_left_in_place`,
      `test_apply_one_already_quarantined_object_skips_cleanly_no_wrong_path_error` (asserts zero GCS calls on
      already-quarantined re-run). No further code change needed — this was purely an unflipped checkbox.

## Progress Log

- **context-scout 2026-08-01**: populated/refreshed context_scope (3 entries).
- **context-scout 2026-08-03**: fixed a duplicate entry (`cme_combo_underlying_extraction_garbage_2026_07_19.md` was
  listed twice) — deduped to 5 distinct entries, otherwise unchanged.

- **2026-08-04 (slot 14, data_engineering, task `tradfi_satellite_ao_dispatch_batch5-006`)** — Completed the quarantine
  staleness investigation (finding 2 / todo 3). **Root cause: UNABLE TO DETERMINE from committed evidence.** Full
  investigation below.

  **What I checked:**

  1. **Bucket lifecycle configuration**: the issue doc already established no auto-delete rule exists (only 60-day
     Coldline storage-class transition). Confirmed via the bucket lifecycle rule inventory in the existing doc text.

  2. **Committed scripts that could delete from `_quarantine/raw_tick_data/`**: Traced every `gcs_delete_object` /
     `blob.delete()` call site across the MTDS scripts directory. Zero committed scripts target the `_quarantine/`
     prefix for deletion. The scripts that interact with quarantine are:
     - `recover_tradfi_garbage_underlying_2026_07.py` — writes TO `_quarantine/` (MOVE via `gcs_copy` + `gcs_delete` of
       the ORIGINAL `raw_tick_data/` source), never deletes from `_quarantine/`.
     - `migrate_tradfi_canonical_2026_07.py` — can MOVE objects TO `_quarantine/` (`A_QUARANTINE` action), but the apply
       logic for already-quarantined objects fails safely (see latent bug below).
     - `rebundle_tradfi_chains_2026_07.py` — same `_move_to_quarantine` pattern (copy-to-quarantine + delete-source),
       and `_delete_merged` which deletes per-contract sources after successful rebundle.
     - `correct_tradfi_recovery_quarantine_manifest_2026_07_27.py` — manifest-only CAS correction (no GCS object ops).
     - `register_tradfi_recovery_quarantine_manifest_2026_07_30.py` — manifest-only additive registration (no GCS object
       ops).

  3. **Latent `_rel()` bug in `migrate_tradfi_canonical_2026_07.py`**: The `_rel()` function (line 160-163) uses
     `path.find("raw_tick_data/by_date/")` to extract the bucket-relative path. For objects in
     `_quarantine/raw_tick_data/by_date/...`, this strips the `_quarantine/` prefix, making `rel` =
     `"raw_tick_data/by_date/..."` — the object appears to be at its original (pre-quarantine) location. I fully traced
     the apply-phase logic for both `A_COPY` and `A_QUARANTINE` actions with this bug active:
     - `A_COPY`: `src = "gs://bucket/raw_tick_data/..."` (WRONG — object is at `_quarantine/...`) →
       `gcs_describe_object(src)` → None → returns `SRC_ALREADY_GONE` → **no deletion**.
     - `A_QUARANTINE`: `src = "gs://bucket/raw_tick_data/..."` (WRONG) → `gcs_describe_object(src)` → None →
       `gcs_describe_object(dst) and gcs_describe_object(src)` is False → **no deletion**.
     - The `NOOP_TARGET_EQUALS_SOURCE` guard at line 675 also doesn't trigger because `res.new_rel`
       (`"_quarantine/raw_tick_data/..."`) ≠ `rel` (`"raw_tick_data/..."`). **Conclusion**: this is a real latent bug
       (it silently fails to process already-quarantined objects rather than correctly identifying them as
       already-quarantined and skipping), but it does NOT cause deletion. The same bug is inherited by
       `rebundle_tradfi_chains_2026_07.py` (imports `_rel` from the migrate script), same non-deletion outcome.

  4. **Selectivity evidence**: The 9 remaining `day=2026-01-*` prefixes under `_quarantine/raw_tick_data/by_date/` are
     from a DIFFERENT quarantine event (`CME:OPTION:EW1-USD-...` full instrument-id-as-underlying data, not the
     numeric/opaque garbage codes from run `20260720-120911`). A bucket-level operation (lifecycle rule, `gsutil rm -r`)
     would not be this selective — it would delete ALL `_quarantine/raw_tick_data/` prefixes equally.

  **Plausible root causes (in descending likelihood):**
  - (a) Manual operator cleanup — `gsutil rm` of the garbage-underlying quarantine prefixes after confirming the
    manifest correction was complete.
  - (b) Uncommitted one-off cleanup script run on a VM during the migration/recovery campaign (2026-07-20 to
    2026-07-27).
  - (c) GCS infrastructure event (unlikely given the selectivity evidence).

  **Recommendation**: If definitive identification is desired, check Cloud Audit Logs for the tradfi tick bucket
  (`storage.objects.delete` on `_quarantine/raw_tick_data/` prefix, 2026-07-20 to 2026-07-27). The `_rel()` bug
  (stripping `_quarantine/` prefix on already-quarantined objects) should be filed as a separate preventative fix — it's
  a latent correctness issue even though it doesn't cause this specific problem.

- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (5 entries), unchanged.

- **2026-08-09 (slot 23, worker)** — Flipped the final `_rel()` prefix-stripping-bug todo. Verified the fix (and its
  regression tests) had already landed at market-tick-data-service@ff6c2f4a as part of the batch7 hardening pass
  (`_tradfi_migration_recurrence_fixes_2026_08_06.py`'s `rel_with_holding_prefix()`), which explicitly cites this issue
  doc in its own docstring — this task was purely an unflipped checkbox, no new code required. Confirmed the commit is
  on `origin/live-defi-rollout` and both call sites (`migrate_tradfi_canonical_2026_07.py` aliasing `_rel`,
  `rebundle_tradfi_chains_2026_07.py` importing the same symbol) share the fixed implementation, plus 5 passing
  regression tests covering already-quarantined/content-repair-held input paths. All 4 todos in this issue doc are now
  resolved — archival-eligible pending the `locked_by: live-defi-rollout` lock (set 2026-05-21; not unlocked here per
  the ask-before-unlock rule).
- **2026-08-12** — `locked_by`/`locked_since` cleared (corpus-wide fix, operator ruling Option B, interactive session
  2026-08-12; see /plans/active/issues/locked_by_live_defi_rollout_placeholder_corpus_wide_2026_08_10.md). This doc has
  0 open todos, so clearing the placeholder lock immediately makes it archive-eligible. Per the ruling's explicit scope
  ("do NOT auto-archive in this same pass"), archival itself is deferred to a separate follow-on pass; bridged with
  `archive_exempt: true` (the sanctioned flip-then-mv two-commit pattern documented in
  `scripts/plan-hygiene/check_archive_candidates.sh`) so this commit doesn't trip the archive-candidates pre-commit
  gate. The follow-on pass should drop `archive_exempt` and `git mv` this doc to `plans/archive/[issues/]`.
