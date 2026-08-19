---
doc_type: plan
title: TradFi legacy bucket delete — E7 verify-then-delete (operator re-confirmed 2026-08-16)
summary: >-
  Operator re-confirmed 2026-08-16 (na-eligibility-audit follow-up Q&A round 8) the prior ruling on
  data_completion_tradfi_2026_07_15.md's E7 todo: verify `cf_manifest_audit_2026_06_01.py` GREEN (CF-1..CF-12,
  esp. schema v9 on real rows), then permanently delete the legacy `market-data-tick-tradfi` bucket + bulk-delete
  the 12 `day-*` hyphen 0-row-placeholder prefixes in `tradfi-prd` (~110k objects). IRREVERSIBLE — only proceed
  after GREEN, with the pre-delete guard (re-assert 0-row per object before deleting, abort the prefix on any
  non-empty object) already specified in the source todo. Scope note (carried from the source doc's own
  2026-08-02 re-opening): complete for the MIGRATED corpus only — ~2,008 legacy-only tradfi days destroyed
  without migration are irrecoverable and NOT part of the "100%" claim; do not let this checkbox imply full
  completeness.
status: active
nature: process
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [tradfi, gcs, delete, manifest, irreversible, bucket-decommission]
related:
  [
    /plans/active/data_completion_tradfi_2026_07_15.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
created: "2026-08-16"
last_updated: "2026-08-16"
parent_epic: tradfi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.7
assigned_role: data_engineering
effort: max
drift_direction: none
depends_on: []
supersedes:
superseded_by:
source: "na-eligibility-audit follow-up Q&A round 8, 2026-08-16 — operator re-confirmed the cited prior ruling"
locked_by:
context_scope:
  [
    /plans/active/data_completion_tradfi_2026_07_15.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /plans/active/issues/cf_manifest_audit_first_full_rollup_findings_2026_07_26.md,
    unified-trading-library/unified_trading_library/cf_manifest_audit.py,
  ]
locked_since:
resolved_by:
---

# TradFi legacy bucket delete — E7 verify-then-delete

## Todos

- [x] ✅ [DATA] P0. **E7 Verify — DONE 2026-08-16 (slot-5, data_engineering). Result: NOT GREEN (CF-8 RED) — delete
      correctly WITHHELD, gate not met.** Ran the CF-1..CF-14 audit against
      `market-data-tick-tradfi-prd-central-element-323112` live (14,454,704 rows). **First, a pre-check**: the
      legacy `market-data-tick-tradfi` bucket target is **already permanently deleted** (independently reconfirmed
      via `get_storage_client().bucket(...).exists() == False`, matching the existing R1 finding in
      `data_completion_tradfi_2026_07_15.md` — that half of this todo is moot, not newly executed).
      **CF audit result** (via `unified_trading_library.cf_manifest_audit.audit()` — the canonical, actively-fixed
      module; the named `plans/audit/results/cf_manifest_audit_2026_06_01.py` one-off predecessor OOMs the shared
      host on this bucket's current row count and was abandoned in favour of the column-pruned canonical tool,
      same audit logic): **CF-1 GREEN** (v9=100%) · **CF-2 GREEN** · **CF-3 GREEN** (pipeline_mode 100% populated)
      · **CF-4 GREEN** (source 100%) · **CF-5 GREEN** · **CF-6 GREEN** · **CF-8 RED** (`available_at`
      non-null=7,913,406/8,116,669 captured rows, 97.5% — NOT 100%) · **CF-13 GREEN** (100% source-aware) ·
      **Era-B GREEN** (adjudicated tradfi bundle-grain exception, 107,296 rows) · **CF-9 GREEN**. **CF-2-paths /
      CF-3-partition**: the shared shallow-probe checker returned a FALSE RED here (found + fixed — see below);
      independently confirmed GREEN via a direct scoped descent into `raw_tick_data/by_date/day=1962-02-18/` →
      reached `pipeline_mode=batch_fred/asset_group=tradfi/venue=FRED/instrument_type=...` (both segments present).
      **CF-8 is a genuine, already-known, already-tracked gap** (not new — see
      `plans/active/issues/cf_manifest_audit_first_full_rollup_findings_2026_07_26.md`'s tradfi CF-8 entry,
      diagnosed 2026-08-02; the fill-rate-ceiling fix is actively in progress across many sessions in
      `plans/active/mtds_available_at_cross_asset_backfill_2026_07_13.md` — not re-worked here, would be
      duplicate/unplanned scope). Per this todo's own literal gate ("only after GREEN"), **the irreversible delete
      (12 `day-*` hyphen 0-row-placeholder prefix bulk-delete, ~110k objects) is correctly WITHHELD, not
      executed** — CF-8 RED means CF-1..CF-12 is not GREEN. **Checker bug found + fixed in the same turn**: the
      canonical `unified_trading_library.cf_manifest_audit._probe_paths()` had regressed (2026-07-26 refactor) to a
      single-top-level-branch-only descent AND dropped the `configs`/`databento-batch-registry` exclusions the
      pre-refactor one-off script already had — reproducing the exact tradfi-prd false CF-2-paths/CF-3-partition
      RED first caught 2026-07-12 (`configs/patches/*.py` sorts ahead of `raw_tick_data/`, carries no
      `asset_group=`/`pipeline_mode=` segment). Fixed + regression-tested + shipped:
      `unified-trading-library@a5e4765017`. **Next step: see Todo 2 below (added 2026-08-19 — was prose-only,
      "tracked, not this todo", with no actual todo anywhere; corrected per the HARD RULE that every follow-up is
      a tracked `- [ ]` item, never prose).** Scope: complete for the
      MIGRATED corpus only (~5,553,198 rows as of 2026-07-16, schema_version=9=100%) — the ~2,008 legacy-only
      tradfi days destroyed without migration are irrecoverable and out of scope for this delete's "done" bar; do
      not claim full tradfi completeness from this checkbox. Repo: market-tick-data-service (verify only, no
      MTDS code touched), unified-trading-library (checker fix). Source: `data_completion_tradfi_2026_07_15.md` E7
      (line 211).

- [ ] [DATA] P1. **Re-run the E7 verify once CF-8 clears GREEN, then execute the bulk-delete if the full
      CF-1..CF-12 gate is met.** Gated on `market-data-tick-tradfi-prd`'s CF-8 (`available_at` fill-rate) turning
      GREEN — tracked in `plans/active/issues/cf_manifest_audit_first_full_rollup_findings_2026_07_26.md`'s tradfi
      CF-8 entry; do not re-attempt this todo until that entry shows CF-8 GREEN for this bucket. When it clears:
      re-run `unified_trading_library.cf_manifest_audit.audit()` against `market-data-tick-tradfi-prd-central-element-323112`,
      confirm CF-1..CF-12 all GREEN (not just CF-8), then execute the bulk-delete of the 12 `day-*` hyphen 0-row
      placeholder prefixes (~110k objects) with the pre-delete guard already specified above (re-assert 0-row per
      object before deleting, abort the prefix on any non-empty object) — irreversible, per
      `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`. Done when: either the delete executes with a
      verified pre/post object count, or the gate remains RED and this todo is released `GATED` citing the current
      CF-8 status. Repo: market-tick-data-service.

## Progress Log

- **2026-08-16 (na-eligibility-audit follow-up Q&A round 8, operator re-confirmation)**: extracted from
  `data_completion_tradfi_2026_07_15.md` for AO dispatch, since the parent doc stays `assigned_vm: NA`.
- **2026-08-16 (slot-5, data_engineering)**: ran E7's verify step. Full result + reasoning inline on the todo
  above (checkbox flipped — verify is genuinely complete, but the result is RED, not GREEN, so the delete did not
  run). Summary: legacy bucket already gone (moot); canonical bucket CF-1..CF-7/CF-9/CF-13/Era-B all GREEN; CF-8
  genuinely RED (pre-existing, tracked elsewhere); found + fixed a real regression in the shared CF-audit
  path-probe checker along the way (`unified-trading-library@a5e4765017`) since it was giving a false RED on
  CF-2-paths/CF-3-partition for this exact bucket. No GCS delete of any kind was executed this session — the
  irreversible action stays gated until CF-8 clears.
- **context-scout 2026-08-17**: populated/refreshed context_scope (4 entries).
- **plan_reconciler 2026-08-19** (epic-scoped `tradfi_master` pass): found the "Next step (tracked, not this
  todo)" phrase inside Todo 1 was a HARD RULE violation — real remaining work (re-verify + delete once CF-8
  clears) described only in prose, no actual todo tracked it anywhere (confirmed via the finalize plan's own
  Progress Log: "no newer delete-execution task exists"). Added Todo 2 to track it explicitly; corrected the
  prose reference to point at it.
