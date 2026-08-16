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
  ]
locked_since:
resolved_by:
---

# TradFi legacy bucket delete — E7 verify-then-delete

## Todos

- [ ] [DATA] P0. **E7 Verify**: run `cf_manifest_audit_2026_06_01.py market-data-tick-tradfi-prd-…` → confirm
      CF-1..CF-12 GREEN data-state (esp. v9 confirmed on real rows). ⚠️ IRREVERSIBLE — only after GREEN: **delete
      legacy `market-data-tick-tradfi` permanently** + **bulk-delete the 12 `day-*` hyphen 0-row-placeholder
      prefixes** in `tradfi-prd` (~110k objects); pre-delete guard: re-assert 0-row per object before deleting,
      abort the prefix on any non-empty object. Scope: complete for the MIGRATED corpus only (~5,553,198 rows,
      schema_version=9=100%) — the ~2,008 legacy-only tradfi days destroyed without migration are irrecoverable
      and out of scope for this delete's "done" bar; do not claim full tradfi completeness from this checkbox.
      Repo: market-tick-data-service. Source: `data_completion_tradfi_2026_07_15.md` E7 (line 211).

## Progress Log

- **2026-08-16 (na-eligibility-audit follow-up Q&A round 8, operator re-confirmation)**: extracted from
  `data_completion_tradfi_2026_07_15.md` for AO dispatch, since the parent doc stays `assigned_vm: NA`.
