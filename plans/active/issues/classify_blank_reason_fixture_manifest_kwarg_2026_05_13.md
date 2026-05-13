---
title: "classify_blank_reason_row() fixture_manifest kwarg mismatch — Script 3 0 upgrades for defi/sports/prediction"
created: 2026-05-13
author: slot-6-harsh
source:
  - manifest_cross_asset_rescan_design_2026_05_08
severity: P1
locked_by: live-defi-rollout
locked_since: 2026-05-13
---

## What I found

During the 2026-05-13 all-5-asset-group dry-run reconciliation run, Script 3
(`reconcile_legacy_blank_to_typed_reason.py`) hit a per-row `TypeError` for every candidate row in
**defi** (604,951 rows), **sports** (1,868,285 rows), and **prediction** (41 rows):

```
WARNING Classifier failed for row <N>: classify_blank_reason_row() got an unexpected keyword
argument 'fixture_manifest' — leaving row unchanged
```

The script catches the exception per-row, does not crash, but produces **0 upgrades** for all affected
asset_groups. `cefi` and `tradfi` are unaffected (0 candidates, clean).

**Observed in logs** (run 2, 2026-05-13 07:47 UTC):
- `gs://deployment-scripts-central-element-323112/vm-logs/manifest-recon-defi-20260513-074716/run.log`
- `gs://deployment-scripts-central-element-323112/vm-logs/manifest-recon-sports-20260513-074736/run.log`
- `gs://deployment-scripts-central-element-323112/vm-logs/manifest-recon-prediction-20260513-074736/run.log`

## Why it matters

- **Script 3 apply-flips for defi/sports/prediction is fully broken** — running with `--apply-flips` would
  also produce 0 upgrades, leaving all legacy-blank rows un-reclassified.
- The `fixture_manifest` kwarg appears to have been added to the UTL `classify_blank_reason_row()` function
  (or removed from the reconciler call-site) after the reconciler script was last updated. This is an
  API-drift mismatch between the reconciler script and the UTL classifier function.
- Per CLAUDE.md "Findings Triage: Big finding" — affects data correctness for 3 of 5 asset_groups, blocks
  a manifest health reconciliation that has 1,868,285 + 604,951 = 2,473,277 affected rows.

## Likely root cause

Either:
1. `classify_blank_reason_row()` in UTL gained a required/keyword argument `fixture_manifest` (not passed
   by the reconciler), OR
2. The reconciler calls `classify_blank_reason_row(row, fixture_manifest=...)` but the UTL function no
   longer accepts that kwarg.

Check `instruments-service/scripts/reconcile_legacy_blank_to_typed_reason.py` call-site vs current UTL
`unified_trading_library.manifest.classify_blank_reason_row` signature.

## Recommended decision

**P1** — fix before next reconciliation run.

1. Find `classify_blank_reason_row` in UTL and read its current signature.
2. Find the call-site in `reconcile_legacy_blank_to_typed_reason.py`.
3. Align: either add `fixture_manifest` kwarg handling to the reconciler (pass the right value) or remove
   from the UTL function if it was added incorrectly.
4. Re-run Script 3 dry-run for defi/sports/prediction after fix to verify non-zero upgrades.
5. Only then run apply-flips.

**Owner**: instruments-service maintainer (Ikenna per workstream — instruments-service is cross-cutting
design scope).

**Suggested resolution slot**: next instruments-service touch by slot 1 or 3.
