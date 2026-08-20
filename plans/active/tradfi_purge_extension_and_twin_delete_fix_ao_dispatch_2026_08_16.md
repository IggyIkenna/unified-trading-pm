---
doc_type: plan
title: TradFi residual catalogue-leg purge extension + twin-delete lookup-bug fix
summary: >-
  Operator-ruled 2026-08-16 (na-eligibility-audit follow-up Q&A round 3) — two TradFi items:
  extend the already-granted 4-leg operator go-ahead to the residual 2-leg catalogue purge
  (NASDAQ/NYSE SPOT_PAIR mis-classification, 318 rows + 12 cefi-singles EQUITY/EQUITY-USD
  rows), and fix the suspected canonical_twin_path() lookup-logic bug BEFORE trusting the 0%
  twin-coverage measurement that gates the legacy-twin bucket delete.
status: active
nature: process
asset_group: [tradfi]
stage: [data]
repos: [instruments-service, market-tick-data-service, deployment-service]
scope: [engineer]
tags: [tradfi, canonicalization, manifest, gcs-delete]
related:
  [
    /plans/active/instruments_tradfi_g1_g5_gate_execution_2026_07_24.md,
    /plans/active/tradfi_legacy_twin_bucket_deletes_signoff_2026_07_24.md,
  ]
created: "2026-08-16"
last_updated: "2026-08-17"
parent_epic: instruments_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.6
assigned_role: data_engineering
effort: max
drift_direction: advance-code
depends_on: []
supersedes:
superseded_by:
source: "na-eligibility-audit follow-up Q&A round 3, 2026-08-16"
locked_by:
context_scope:
  [
    /plans/active/instruments_tradfi_g1_g5_gate_execution_2026_07_24.md,
    /plans/active/tradfi_legacy_twin_bucket_deletes_signoff_2026_07_24.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    instruments-service/scripts/cleanup_legacy_twins.py,
  ]
locked_since:
resolved_by:
---

# TradFi residual catalogue-leg purge extension + twin-delete lookup-bug fix

## Todos

- [ ] [DATA] P2. Execute the residual catalogue-leg purge (NASDAQ/NYSE SPOT_PAIR mis-classification, 318 rows, plus
      12 cefi-singles EQUITY/EQUITY-USD rows) from `instruments_tradfi_g1_g5_gate_execution_2026_07_24.md` — operator
      extended the already-granted 4-leg go-ahead to cover this residual 2-leg set 2026-08-16. Same mis-classification
      class as the 4 already-approved legs. (repo: instruments-service)
- [x] ✅ [DATA] P1. **DONE 2026-08-17 (slot-23) — fix was ALREADY SHIPPED (instruments-service@271b3d33, 2026-08-14,
      predates this plan's creation); this todo's work was verifying it + re-measuring coverage.** `canonical_twin_path()`
      now derives the pre-hive venue/instrument_type via the shared `_pre_hive_parser()` (loaded from
      `backfill_orphan_class_e.py`) and builds the full canonical path by FORMATTING the matched
      `unified_api_contracts.canonical_path_templates(asset_group)` entry — exactly the fix this todo specified, not a
      partial string splice. Verified via 2 independent checks: (1) the existing regression suite
      (`tests/scripts/test_cleanup_legacy_twins.py::TestCanonicalTwinPath`) already asserts the EXACT pre-hive tradfi
      case byte-for-byte
      (`test_pre_hive_tradfi_shape_carries_asset_group_and_correct_order` — the same ABBV/NYSE example from the
      2026-08-09 root-cause finding) plus the hive-shaped-legacy case still passes
      (`test_inserts_pipeline_mode_after_day`, `test_category_normalised_to_asset_group`,
      `test_already_canonical_not_double_inserted`) and a graceful-fallback case
      (`test_pre_hive_unresolvable_source_falls_through_never_crashes`); (2) independently re-derived + live-verified
      against prod GCS (not just the test suite): `canonical_twin_path("raw_tick_data/by_date/day=2025-01-02/data_type=ohlcv_1m/equities/NYSE/NYSE:EQUITY:ABBV-USD.parquet", "databento", "tradfi")`
      → `gcs_describe_object` on the derived path resolves to a REAL object
      (`last_modified=2026-08-10T12:24:04Z`, `crc32c=kiIx0w==`) — the fix produces a path that matches live prod
      reality, not just a unit-test fixture. The commit's "Secondary (optional)" ask
      (`_source_by_cell_from_manifest` full-manifest-read memory bloat) was also fixed in the SAME commit (vectorized
      cell-filtered pyarrow lookup, replacing the `pd.read_parquet`+`to_dict("records")` pattern that hit a 4.4GB RSS
      kill on tradfi's manifest).
      **Re-measured twin coverage 2026-08-17** (dry-run, no `--apply`, per this todo's own constraint): re-ran
      `cleanup_legacy_twins.py --asset-group tradfi --report-uri _index/audit/orphan_sweep_tradfi.parquet` against the
      EXISTING candidate report (900 class-B rows, generated 2026-07-30) —
      **result: 0/900 deletable, 900/900 blocked, but the block reason changed from the old "canonical twin NOT
      captured in manifest" (0% Part-5 coverage) to "legacy object no longer exists - nothing to delete (stale
      candidate-report entry)" for ALL 900 rows.** Independently spot-verified one row directly
      (`gcs_describe_object` on the legacy URI → `None`; on its now-correctly-derived canonical twin → resolves, real
      object, `last_modified=2026-08-10`) — this is genuine: the 900 legacy pre-hive objects the 2026-07-30 report
      named have themselves already been deleted from GCS sometime in the intervening ~2.5 weeks (consistent with the
      already-noted 995→900 unexplained-shrink pattern continuing further), not a code artifact. **Consequence: Part
      5's twin-coverage CANNOT be re-validated as 100% (or any %) against this stale report** — there is nothing left
      in it to measure coverage FOR. The fix is proven correct; the report it was meant to re-validate against has
      gone stale in a NEW way (0 remaining candidates, not 0% coverage). A fresh `migration_orphan_sweep.py
      --asset-group tradfi` full-bucket walk is required before the "auto-execute once coverage clears 100%" rule in
      the sibling doc can ever fire meaningfully again — filed as the new todo below (VM-scale, out of this todo's
      own scope). Verdict report (audit artifact, not authoritative):
      `gs://market-data-tick-tradfi-prd-central-element-323112/_index/audit/cleanup_legacy_twins_verify_2026_08_17.parquet`.
      No delete executed (per this todo's own constraint) — evidence: `instruments-service@271b3d33` (pre-existing
      fix), no new code shipped by this todo.
- [ ] [DATA] P2. **NEW (filed 2026-08-17, follow-up to the todo above)**: run a fresh
      `migration_orphan_sweep.py --asset-group tradfi` full-bucket walk (VM-scale, in-region per the heavy-I/O HARD
      RULE — never on the shared planning host) to rebuild the class-B legacy-duplicate candidate list. The existing
      `_index/audit/orphan_sweep_tradfi.parquet` report (generated 2026-07-30) is now fully stale — a 2026-08-17
      re-verify (this plan's own todo above) found all 900 of its class-B rows already absent from GCS. Once the fresh
      sweep writes a current report, re-run `cleanup_legacy_twins.py --dry-run` against it to get a trustworthy Part-5
      twin-coverage measurement for the sibling gate doc
      (`tradfi_legacy_twin_bucket_deletes_signoff_2026_07_24.md`) — only THAT measurement (not this todo) may clear
      the delete gate. (repo: instruments-service)

## Progress Log

- **2026-08-17 (slot-23)**: flipped the P1 canonical_twin_path() todo — the fix was already shipped
  (instruments-service@271b3d33, 2026-08-14) before this plan existed; verified it (regression suite + independent
  live-GCS cross-check) and re-measured twin coverage against the existing tradfi candidate report. Finding: the
  report itself is now 100% stale (all 900 legacy candidates already deleted from GCS since 2026-07-30) — twin
  coverage cannot be re-validated from it. Filed a new P2 follow-up todo (fresh orphan-sweep walk) to unblock a
  trustworthy re-measurement. The residual catalogue-leg purge todo (P2, item 1) is untouched — out of this task's
  scope.
- **2026-08-16 (na-eligibility-audit follow-up Q&A round 3, operator ruling)**: extracted from
  `instruments_tradfi_g1_g5_gate_execution_2026_07_24.md` and `tradfi_legacy_twin_bucket_deletes_signoff_2026_07_24.md`.
  The delete itself remains gated on 100% measured twin coverage post-fix — this plan does not authorize the delete,
  only the lookup-bug investigation that determines whether the current 0% measurement can be trusted.
- **context-scout 2026-08-17**: populated/refreshed context_scope (4 entries).
