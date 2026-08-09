---
doc_type: issue
title:
  "Manifest-correction scripts that mutate capture_status without bumping attempted_at/written_at silently lose the
  consolidator's dedup tie-break — cefi confirmed, defi at risk"
summary:
  "reconcile_correct_legacy_blank_misflips_cefi_2026_05_13.py (cefi) mutated capture_status/error_reason in place but
  preserved the original row's attempted_at/written_at, so its per-VM shard tied exactly with the row it was meant to
  override. The consolidator's dedup tie-break (attempted_at -> written_at DESC NULLS LAST) resolves an exact tie by
  scan order, not correction-wins — confirmed live 2026-08-09: N1b's apply uploaded a clean shard but the next
  consolidator merge recorded rows_added=0 and the canonical kept the stale attempted_failed rows. Fixed for cefi
  (instruments-service@42b9319b). The sibling defi corrector
  (instruments-service/scripts/reconcile_correct_legacy_blank_misflips_2026_05_13.py:301-303) has the SAME class of
  defect via a different mechanism — it sets attempted_at=None on correction, and NULLS LAST means a null attempted_at
  always loses to a row carrying a real timestamp — so any defi corrections already applied via this script may also
  have silently failed to merge into the canonical. NOT independently verified live for defi in this session (out of
  N1b's cefi-only scope) — flagging for operator triage rather than assuming either outcome."
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
assigned_vm: NA
execution_scope: local-only
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

**Fix**: `instruments-service@42b9319b` — the apply loop now stamps a single fresh `datetime.now(UTC).isoformat()` onto
both `attempted_at` and `written_at` for every corrected row, and `_NEEDED_COLUMNS` now includes both fields (they were
previously excluded from the column-pruned read entirely, which would have produced a NULL-column shard on any future
run of the pruned-read version — an even more certain tie-break loss). Regression test added:
`test_apply_flips_bumps_timestamps_past_original_row`.

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

## Recommended fix (defi, not yet applied — outside N1b's cefi scope)

Mirror the cefi fix: stamp a fresh `datetime.now(UTC)` onto both `attempted_at` and `written_at` (not clear
`attempted_at` to `None`) for every corrected row, ensuring the correction unambiguously wins the tie-break.

## Broader pattern risk

Any OTHER script in the workspace that writes a per-VM shard correcting an existing row's `capture_status` (not just
these two correctors) is subject to the same rule and should be audited for the same defect. Not enumerated here — scope
this as its own follow-up if the defi check above confirms live impact.

## Todo

- [ ] [DATA] P1. **Verify whether defi's corrector has ever run `--apply-flips` live, and if so whether its claimed
      corrections actually merged into the canonical `_index`** (same live-comparison method as this issue's evidence
      section). — instruments-service
- [ ] [SCRIPT] P2. **If defi impact is confirmed (or as a preventive fix regardless): stamp fresh
      attempted_at/written_at in `reconcile_correct_legacy_blank_misflips_2026_05_13.py`'s apply path**, mirroring
      `instruments-service@42b9319b`. Add a regression test analogous to
      `test_apply_flips_bumps_timestamps_past_original_row`. — instruments-service
- [ ] [DATA] P3. **Audit other per-VM-shard-writing correction scripts workspace-wide for the same tie-break defect**
      (any script that mutates `capture_status` on an existing row without bumping `attempted_at`/`written_at`). —
      cross-cutting
