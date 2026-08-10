---
doc_type: issue
title:
  "Manifest-correction scripts that mutate capture_status without bumping attempted_at/written_at silently lose the
  consolidator's dedup tie-break — cefi confirmed, defi confirmed-ran-twice (merge outcome unverifiable, both scripts
  still unpatched)"
summary:
  "reconcile_correct_legacy_blank_misflips_cefi_2026_05_13.py (cefi) mutated capture_status/error_reason in place but
  preserved the original row's attempted_at/written_at, so its per-VM shard tied exactly with the row it was meant to
  override. The consolidator's dedup tie-break (attempted_at -> written_at DESC NULLS LAST) resolves an exact tie by
  scan order, not correction-wins — confirmed live 2026-08-09: N1b's apply uploaded a clean shard but the next
  consolidator merge recorded rows_added=0 and the canonical kept the stale attempted_failed rows. Fixed for cefi
  (instruments-service@159c0ebe0, amend of the original 8cf44c665 fix commit). A SECOND, independent bug surfaced on
  re-apply: the fixed shard carried only the bulk-scan's column-pruned 10/42 columns, missing service_name (part of the
  consolidator's dedup key base) -- would have landed as a duplicate row rather than an overwrite. Caught live before
  the next consolidator cycle could merge it (broken shard deleted directly via the SDK at 2026-08-09T12:00:05Z) and
  fixed by re-fetching full columns for corrected rows via DuckDB (instruments-service@159c0ebe0, same commit). The
  sibling defi corrector (instruments-service/scripts/reconcile_correct_legacy_blank_misflips_2026_05_13.py:301-303) has
  the SAME class of defect via a different mechanism — it sets attempted_at=None on correction, and NULLS LAST means a
  null attempted_at always loses to a row carrying a real timestamp — so any defi corrections already applied via this
  script may also have silently failed to merge into the canonical. NOT independently verified live for defi in this
  session (out of N1b's cefi-only scope) — flagging for operator triage rather than assuming either outcome."
status: open
nature: issue
asset_group: [cefi, defi]
stage: [data]
repos: [instruments-service, unified-trading-library]
scope: [engineer, admin]
tags: [manifest, consolidator, data-correctness, dedup, per-vm-shards, corrector-script]
related:
  [
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
    plans/active/instruments_mtds_consistency_remediation_residuals_2026_07_24.md,
    plans/active/cefi_consolidated_closeout_2026_07_18.md,
    plans/active/defi_consolidated_closeout_2026_07_18.md,
  ]
created: 2026-08-09
last_updated: 2026-08-09
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.12
assigned_role: data
drift_direction: advance-code
depends_on:
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: N1b (slot 6, cefi corrector re-verification, 2026-08-09)
---

# Corrector scripts' dedup-tiebreak timestamp bug — cefi confirmed, defi at risk

## What happened (cefi, confirmed live)

`instruments-service/scripts/reconcile_correct_legacy_blank_misflips_cefi_2026_05_13.py`'s apply path (pre-fix) mutated
only `capture_status`/`error_reason`/`reconciler_run_id` on a corrected row, leaving `attempted_at`/ `written_at` at the
ORIGINAL row's values. The per-VM shard it uploaded therefore carried a row that, on every dedup-key field the
consolidator sorts by, was an EXACT tie with the row it was meant to override.

Per `/codex/05-infrastructure/manifest-consolidator-ssot.md` § "Merge engine" / "Dedup key": last-write-wins is resolved
by `attempted_at -> written_at DESC NULLS LAST`. An exact tie on both fields is not resolved by "correctness" — it falls
to DuckDB's window-function scan order, which is not something the writer controls.

**Live evidence (2026-08-09, N1b)**: applied a 7-row correction (`HYPERLIQUID:PERPETUAL:IP-USD@LIN`/2026-06-29,
`attempted_failed/UNCLASSIFIED_ADAPTER_ERROR` → `empty_confirmed/EXPECTED_INSTRUMENT_DELISTED`), shard uploaded cleanly
(`gs://market-data-tick-cefi-prd-central-element-323112/_index/per_vm/slot6-n1b-corrector-cefi-1786273499.parquet`). The
consolidator ran ~3 min later (`_index/latest.json`: `shards_scanned=8, shards_changed=4, rows_added=0`) — the shard was
scanned and counted as "changed" but contributed zero new rows. Direct comparison confirmed the shard's 7 rows carried
`attempted_at`/`written_at` identical to the microsecond (`2026-07-28T14:28:57.682261+00:00` etc.) to the canonical's
still-`attempted_failed` rows for the same key. The canonical never updated.

**Fix**: `instruments-service@8cf44c665` — the apply loop now stamps a single fresh `datetime.now(UTC).isoformat()` onto
both `attempted_at` and `written_at` for every corrected row, and `_NEEDED_COLUMNS` now includes both fields (they were
previously excluded from the column-pruned read entirely, which would have produced a NULL-column shard on any future
run of the pruned-read version — an even more certain tie-break loss). Regression test added:
`test_apply_flips_bumps_timestamps_past_original_row`.

## Second bug, caught on re-apply — column-pruned shard would have caused duplicate rows

Re-applying with the timestamp fix above uploaded a new shard (`slot6-n1b-corrector-cefi-retry-1786276.parquet`) that
turned out to carry only the bulk-scan's column-pruned 10/42 columns (`_download_manifest`'s `_NEEDED_COLUMNS` subset) —
missing `service_name`, which per `manifest-consolidator-ssot.md` "Dedup key" is PART of the consolidator's dedup key
base (`date, venue, data_type, service_name`). A shard row missing that column is NULL-padded on the UNION-ALL
projection, so it would fail to match the canonical row's real `service_name` and land as a **duplicate row instead of
an overwrite** — a different failure mode from the timestamp bug (corruption via doubling, not silent no-op).

Caught before the 2026-08-09 12:00 UTC hourly consolidator cycle could merge it: the broken shard was deleted directly
via the `google.cloud.storage` SDK (`blob.delete()`, GCS soft-delete retention applies) at 2026-08-09T12:00:05Z.
**Fix**: `instruments-service@159c0ebe0` — the apply path now re-fetches full columns for exactly the corrected rows via
DuckDB predicate-pushdown off the local downloaded manifest (the same memory-safety pattern the consolidator's own merge
engine uses), so the shard carries every canonical column rather than just the candidate-scan subset. Regression tests
added: `test_apply_flips_bumps_timestamps_past_original_row` (extended) and an `instrument_type` propagation assertion
in `test_apply_flips_corrects_pre_listing_row_only`.

**Broader implication for the "verify defi" todo below**: if defi's corrector also does a column-pruned bulk scan (check
`_download_manifest` there), a defi fix needs BOTH the timestamp bump AND the full-column re-fetch — fixing only the
timestamp tie-break would trade "silent no-op" for "silent duplicate row", not actually resolve anything.

## Why defi is at risk (NOT independently verified — flagging, not asserting)

`instruments-service/scripts/reconcile_correct_legacy_blank_misflips_2026_05_13.py:296-303` (the cefi script's docstring
calls it the script this one "mirrors"):

```python
for c in corrections:
    idx = c["row_index"]
    df.at[idx, "capture_status"] = c["new_status"]
    df.at[idx, "error_reason"] = c["new_reason"]
    # Clear attempted_at on revert to empty_confirmed.
    if "attempted_at" in df.columns:
        df.at[idx, "attempted_at"] = None
```

This sets `attempted_at` to `None` rather than preserving it — a different mechanism from the cefi bug, but the same
failure MODE under the documented tie-break rule: `NULLS LAST` means a null `attempted_at` sorts behind ANY row carrying
a real timestamp, so the corrected (empty_confirmed) row would lose the tie-break against the original attempted_failed
row it's meant to replace, regardless of `written_at`. `written_at` is never touched at all in this script's apply path.

**This has not been checked against a live defi manifest in this session** — it is possible defi's dedup key/schema
differs enough that this doesn't reproduce, or that no defi corrections have been applied via this script since it
shipped. Someone with defi scope should: (1) grep `RECONCILER_COMPLETED corrected=` events / git history for whether
this script has ever been run with `--apply-flips` against a live defi bucket, and if so (2) spot-check a handful of its
claimed corrections against the live defi `_index` the same way this issue's live-evidence section did for cefi.

## Defi verification (2026-08-09, slot 28) — confirmed run history, evidence of the original merge failing, a SECOND defi corrector also at risk, current state moot

**(1) Defi's corrector HAS run `--apply-flips` live — twice, via two different scripts:**

- **2026-05-13 ~16:21 BST**: the generic multi-asset-group script
  `instruments-service/scripts/reconcile_correct_legacy_blank_misflips_2026_05_13.py` (`instruments-service@fafaa0c`)
  ran `--asset-group defi --apply-flips`, scanned 605,070 candidates, corrected **599,486 rows**
  (`attempted_failed/LegacyBlankErrorReasonError` → `empty_confirmed/EXPECTED_PRE_VENUE_LAUNCH`), shard uploaded to
  `gs://market-data-tick-defi-central-element-323112/_index/per_vm/ikenna-slot3-corrector.parquet`. Documented in the
  now-archived `plans/archive/issues/defi_legacy_blank_reclassification_2026_05_13.md`. This is the script this issue's
  "Why defi is at risk" section already quotes — its `attempted_at = None` apply-time bug is confirmed still present in
  the current live code (unpatched, same lines as quoted above).
- **2026-05-15**: a SEPARATE, defi-specific script `reconcile_correct_legacy_blank_misflips_defi_2026_05_13.py`
  (`instruments-service@2a398cd`/`3670534`, "Wave 3 DeFi corrector", NOT the script this issue originally quoted) ran
  `--asset-group defi --apply-flips`. Per `plans/archive/2026_05/work_split_2026_05_14_ikenna.md` item 2 ("Phase B
  re-attempt"): dry run found the **identical** 605,070 candidates / 599,486 proposed corrections, then apply-flips
  reported `RECONCILER_COMPLETED` on **599,486 rows**, shard uploaded to
  `gs://market-data-tick-defi-central-element-323112/_index/per_vm/ikenna-slot2-corrector-defi-20260515.parquet` in
  528.5s.

**(2) The May-15 dry-run finding the SAME 605,070/599,486 numbers as the May-13 apply-run is direct historical evidence
that the May-13 correction did NOT merge into the canonical.** If the May-13 shard had landed, those 599,486 rows would
already read `empty_confirmed` and the May-15 candidate mask (`capture_status=attempted_failed`) would not have
re-selected them. A 2-day-later re-scan finding the exact same candidate population is the same symptom this issue's
cefi "Live evidence" section describes (`shards_scanned` counted, `rows_added=0`) — consistent with, though not a byte-
for-byte replay of, the cefi tie-break bug (the May-13 script's mechanism is the `attempted_at=None` variant, not cefi's
original identical-timestamp variant, but both lose under `NULLS LAST`).

**(3) The May-15 re-run itself is independently at risk via a THIRD mechanism, and is unverified.** Reading
`reconcile_correct_legacy_blank_misflips_defi_2026_05_13.py`'s apply loop (current live code, lines ~377-384) directly:

```python
corrected_idx = [entry["row_index"] for entry in corrections]
for entry in corrections:
    df.at[entry["row_index"], "capture_status"] = entry["new_capture_status"]
    df.at[entry["row_index"], "error_reason"] = entry["new_reason"]
if "reconciler_run_id" in df.columns:
    for entry in corrections:
        df.at[entry["row_index"], "reconciler_run_id"] = run_id
```

This script does not touch `attempted_at`/`written_at` AT ALL — neither preserves-and-ties (cefi's original bug) nor
nulls (the May-13 defi script's bug) is quite right as a description; it simply leaves both fields at whatever the
downloaded row already had, which for a not-yet-corrected row IS the original value — an EXACT tie on both dedup-key
timestamp fields, the same failure class as cefi's ORIGINAL pre-`8cf44c665` bug. **No verification of the May-15 run's
consolidator merge outcome exists anywhere in the plans corpus** (grepped `plans/` for the shard filename and
`rows_added`/`corrector-defi` — only the single apply-flips log line above, no follow-up rows_added check or post-run
candidate-count-zero re-verification, despite the script's own docstring header naming that check as its "verifier").
Note: unlike cefi's second bug, neither defi script does a column-pruned bulk scan — both `_download_manifest`s do a
full unfiltered `pd.read_parquet`/`pd.read_parquet(io.BytesIO(...))` of every column, so the service_name/duplicate-row
failure mode does NOT apply to either defi script; only the timestamp tie-break is at risk.

**(4) Current live state cannot confirm or deny either run's merge outcome — 3 months of unrelated churn have
overwritten the affected population.** Live query (read-only, via
`resolve_bucket_name(cloud="gcp", kind="market-data", asset_group="defi")` →
`market-data-tick-defi-prd-central-element-323112` — note the archived docs' hardcoded
`market-data-tick-defi-central-element-323112` bucket name is STALE post-`bucket_name_ssot_canonicalisation_2026_05_10`)
against today's canonical `_index/availability_index.parquet`:

- **Zero** rows currently at `capture_status=attempted_failed AND error_reason LIKE '%LegacyBlankErrorReasonError%'`.
- **Zero** rows with `attempted_at IS NULL`.
- The 5 specific rows the archived `defi_legacy_blank_reclassification_2026_05_13.md` cited as "sample-verified"
  corrections (e.g. `CURVE-ETHEREUM 2019-07-25`, `AAVE_V3-POLYGON 2022-01-29`) now all read
  `empty_confirmed/EXPECTED_INSTRUMENT_NOT_LISTED` with `attempted_at`/`written_at` timestamped **2026-08-05**, not the
  May dates — a different, later correction already overwrote them.
- The manifest schema itself has changed since May: the `reconciler_run_id` column referenced in both scripts no longer
  exists in the live schema (queried, `Binder Error: column not found`) — the specific traceability marker that would
  distinguish "landed via the May shard" from "landed via a later process" is gone.
- The bulk of today's `attempted_failed` population (1,891,784 + 241,218 rows) carries
  `superseded_by_content_verified_canonical_dex_pool_swaps_twin_2026_08_09` / `..._dex_pool_state_twin_2026_08_05`
  reasons — large, unrelated 2026-08-05/08-09 canonicalization migrations that rewrote most of the defi manifest's
  `attempted_failed` population wholesale, independent of this issue.

**Conclusion**: whatever the May-13/May-15 runs' actual merge outcomes were, there is no LIVE correctness gap
attributable to them TODAY (the affected rows have since been legitimately superseded either way) — but this is NOT the
same as confirming either shard ever merged, and it is not evidence the underlying defect is safe to leave unpatched.
The evidence in (2) leans toward "the May-13 shard did not merge"; (3) shows the May-15 re-run carries an independent,
still-live, still-unverified risk of the identical failure class. **Both defi-relevant scripts remain unpatched today**
and would reproduce the bug on any future re-run.

## Recommended fix (defi, code not yet shipped)

Mirror the cefi fix in BOTH defi-relevant scripts: stamp a fresh `datetime.now(UTC)` onto both `attempted_at` and
`written_at` for every corrected row (never `None`, never left untouched), ensuring the correction unambiguously wins
the tie-break:

1. `reconcile_correct_legacy_blank_misflips_2026_05_13.py` (generic, lines ~301-303) — currently sets
   `attempted_at = None`.
2. `reconcile_correct_legacy_blank_misflips_defi_2026_05_13.py` (Wave-3 defi-specific, lines ~377-384) — currently does
   not touch `attempted_at`/`written_at` at all.

Neither needs the column-pruning/full-column-refetch half of the cefi fix (both already read the full manifest,
unfiltered) — only the timestamp-stamp half applies.

## Broader pattern risk

Any OTHER script in the workspace that writes a per-VM shard correcting an existing row's `capture_status` (not just
these two correctors) is subject to the same rule and should be audited for the same defect. Not enumerated here — scope
this as its own follow-up if the defi check above confirms live impact.

## Todo

- [x] ✅ [DATA] P1. **Verify whether defi's corrector has ever run `--apply-flips` live, and if so whether its claimed
      corrections actually merged into the canonical `_index`** (same live-comparison method as this issue's evidence
      section). — instruments-service. **DONE 2026-08-09 (slot 28)**: see "Defi verification" section above. Confirmed
      TWO live `--apply-flips` runs (2026-05-13 generic script + 2026-05-15 defi-specific Wave-3 script, both 599,486
      rows). The May-15 dry-run finding the identical candidate population the May-13 run had supposedly already fixed
      is direct evidence the May-13 shard did not merge. The May-15 re-run carries an independent, unverified,
      still-live risk (its script never bumps attempted_at/written_at at all). Live manifest today shows zero residual
      affected rows, but only because unrelated 2026-08-05/08-09 canonicalization migrations have since overwritten the
      whole population — not proof either shard merged. Both scripts remain unpatched.
- [x] ✅ [SCRIPT] P2. **DONE 2026-08-09 — `instruments-service@7be93d5d`.** Stamped fresh `attempted_at`/`written_at` in
      BOTH defi-relevant scripts' apply paths, mirroring `instruments-service@159c0ebe0`'s timestamp logic (only the
      timestamp-stamp half — neither script needed the column-pruning/full-column-refetch half, both already read the
      full unfiltered manifest). `reconcile_correct_legacy_blank_misflips_2026_05_13.py` (generic): replaced the
      `attempted_at = None` clear with a fresh `datetime.now(UTC).isoformat()` stamp on both `attempted_at` and
      `written_at`; also extracted a `_download_manifest()` helper (mirrors both sibling correctors' own seam) since
      this script had zero test coverage before this change and the inline `storage.Client()` chain wasn't
      monkeypatchable. `reconcile_correct_legacy_blank_misflips_defi_2026_05_13.py` (Wave-3 defi-specific): added the
      same fresh-stamp on both fields (previously touched neither). Regression tests:
      `test_apply_flips_bumps_timestamps_past_original_row` in a new
      `tests/unit/test_reconcile_correct_legacy_blank_misflips_2026_05_13.py` (plus baseline apply-flow/idempotency/
      env-guard coverage for a script that had none) and the same-named test added to the existing Wave-3 defi test
      file. `quality-gates.sh` green (5330 passed, 88.96% coverage). — instruments-service
- [ ] [DATA] P3. **Audit other per-VM-shard-writing correction scripts workspace-wide for the same tie-break defect**
      (any script that mutates `capture_status` on an existing row without bumping `attempted_at`/`written_at`). —
      cross-cutting

## Progress Log

- **round9-reclassify-satellite-sweep 2026-08-09** (cefi tranche): **RECLASSIFY, `assigned_vm: NA -> planning`**
  (`execution_scope` `local-only -> orchestrator-agent`). All 3 open todos clear the bounded/worker-determinable bar:
  todo 1 is a live-comparison verification whose exact method this doc's own "Live evidence" section already spells out
  step-by-step; todo 2 is a mechanical mirror-fix of an already-shipped commit (`instruments-service@159c0ebe0`) — the
  doc's own "Second bug" section explains precisely what that fix does and why it's needed regardless of todo 1's
  outcome ("as a preventive fix regardless"); todo 3 is a grep-scoped cross-workspace audit for one named defect
  pattern. No genuine judgment/design call remains. Conflict-check clear: the only other corpus reference to this doc is
  `instruments_mtds_consistency_remediation_residuals_2026_07_24.md`'s citation, which is this doc's OWN origin (the N1b
  session that filed it), not a duplicate extraction or competing dispatch surface. Companion gated finalize plan
  authored: `/plans/active/corrector_scripts_dedup_tiebreak_timestamp_bug_2026_08_09_finalize_2026_08_09.md`.
- **2026-08-09 (slot 28)**: Worked todo 1 (defi verification). Findings in "Defi verification" section above; todo 1
  flipped done. Discovered a SECOND defi-relevant corrector script
  (`reconcile_correct_legacy_blank_misflips_defi_2026_05_13.py`, Wave-3, not the one this issue originally quoted) with
  an independent variant of the same defect, confirmed run live 2026-05-15. Expanded todo 2's scope to cover both
  scripts. No code changes in this session (todo 1 was verification-only; todo 2's fix is separately tagged
  `[SCRIPT] P2` and out of this task's scope).
- **slot-15 worker 2026-08-09** (task `corrector_scripts_dedup_tiebreak_timestamp_bug-c823410f6918`): shipped todo 2
  (`instruments-service@7be93d5d`). Both scripts now stamp a fresh `attempted_at`/`written_at` on every corrected row
  instead of clearing/leaving them untouched. Regression tests added for both (the generic script had none before this —
  its download step wasn't monkeypatchable, so a `_download_manifest()` helper was extracted first, mirroring the
  pattern both sibling correctors already used). `quality-gates.sh` green. Todo 3 (cross-workspace audit for the same
  defect pattern) is still open, out of this task's scope.
