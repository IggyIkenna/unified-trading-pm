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

## Root cause (investigated 2026-05-13 by slot-4-harsh)

**No code bug in LDR.** Both sides are already aligned on `live-defi-rollout`:

- **UTL** `unified_trading_library/legacy_reason_classifier.py:479` has:
  ```python
  def classify_blank_reason_row(
      asset_group: str,
      row: Mapping[str, object],
      *,
      fixture_manifest: pd.DataFrame | None = None,
  ) -> tuple[str, str]:
  ```
  Added in UTL commit `290a415` (`feat(legacy-classifier): Phase 1.5 sports fixture-existence check`).

- **Reconciler** `instruments-service/scripts/reconcile_legacy_blank_to_typed_reason.py:260` passes:
  ```python
  classify_blank_reason_row(asset_group, row, fixture_manifest=fixture_manifest)
  ```

**Actual root cause**: The VM run on 2026-05-13 07:47 UTC used **OLD UTL tarballs** (pre-`290a415`) where
`fixture_manifest` kwarg did not yet exist, while the reconciler script had already been updated to pass it.
This is a VM tarball staleness issue — not a source code bug.

**Per workspace rules**: VMs always run from tarballs. After code changes, tarballs must be refreshed via
`bash deployment-service/scripts/vm/create-code-tarballs.sh`. The reconciler-VM launcher was not re-tarred
after UTL commit `290a415` landed.

## Recommended decision (updated 2026-05-13)

**No code change needed** — both call-site and UTL signature are aligned on LDR.

**Fix path**: Refresh UTL + instruments-service tarballs, then re-run Script 3 dry-run for
defi/sports/prediction to confirm non-zero upgrades. Only then proceed with `--apply-flips` (subject to
Ikenna's hold direction on manifest reconciliation VMs — see manifest_cross_asset_rescan_design_2026_05_08).

1. `bash deployment-service/scripts/vm/create-code-tarballs.sh --unified-trading-library --instruments-service`
2. Re-run Script 3 dry-run (NO `--apply-flips`).
3. Confirm upgrade counts are non-zero for defi/sports/prediction.
4. Await Ikenna direction on `--apply-flips`.

**Owner**: instruments-service maintainer (Ikenna per workstream — instruments-service is cross-cutting
design scope). Tarball refresh is operator-executable.

**Status**: P1 → resolved at source-code level; P1 remains for tarball refresh + re-run verification.
