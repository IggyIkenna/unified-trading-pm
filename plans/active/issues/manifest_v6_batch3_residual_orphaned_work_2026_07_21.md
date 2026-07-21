---
doc_type: issue
title:
  Batch-3 archived-plan-debt residuals — legacy CAS-path cleanup re-scope (UTL) + quote_asset/margin_type never surfaced
  in deployment-api/ui
summary: >-
  Triaging archived-plan debt batch 3 (instruments/market-data/manifest, 9 plans) surfaced 2 genuinely orphaned items
  with no active-plan successor, distinct from the ~220 other items that all resolved to HAS_SUCCESSOR/STALE_OBSOLETE:
  (1) `manifest_429_per_vm_sharding_2026_04_25.plan.md`'s "delete the legacy `_write_with_generation_match` CAS path +
  feature flag" — the path is still live and, per live-code inspection, may no longer be a clean deletion candidate (the
  codebase now also deliberately reuses it for direct canonical-index force-rewrites), so this needs a fresh re-scope,
  not a blind re-execution of the 2026-04-25 todo; (2) `manifest_schema_v6_quote_margin_combo_2026_04_23.plan.md`'s
  "deployment-api data-status API + deployment-ui heatmap filterable by quote_asset/margin_type" — grepped both repos,
  zero hits, never shipped, no active plan claims it.
status: open
nature: issue
asset_group: [cefi, cross-cutting]
stage: [data]
repos: [unified-trading-library, deployment-api, deployment-ui]
scope: [engineer]
tags:
  [
    manifest-writer,
    cas-path,
    generation-conflict,
    quote-asset,
    margin-type,
    data-status,
    heatmap,
    orphaned-work,
    plan-debt,
  ]
related:
  [
    plans/archive/manifest_429_per_vm_sharding_2026_04_25.plan.md,
    plans/archive/manifest_schema_v6_quote_margin_combo_2026_04_23.plan.md,
    plans/active/issues/cefi_chain_tail_v6_canonicalisation_2026_07_21.md,
    plans/active/issues/pm_qg_plan_discipline_and_frontmatter_regression_2026_07_21.md,
  ]
created: "2026-07-21"
parent_epic: infrastructure_master
priority: P3
assigned_vm: planning
execution_scope: orchestrator-agent
drift_direction: advance-code
source: [pm_qg_plan_discipline_and_frontmatter_regression-006]
resolved_by:
locked_by:
depends_on: []
---

# What I found

## 1. `_write_with_generation_match` legacy CAS path was never deleted, and may no longer be a clean deletion

`manifest_429_per_vm_sharding_2026_04_25.plan.md` Phase 6 asked to delete `_write_with_generation_match` (the legacy
compare-and-set write path) + its feature flag once per-VM sharding fully rolled out. Live-verified: the function still
exists at `unified-trading-library/unified_trading_library/manifest_writer/_writer_io.py:857` and is still actively
called (line 616) whenever `_per_vm_enabled` is false — `MANIFEST_PER_VM_SHARDS` is still an opt-in flag (default
`False`), not deleted. Separately, `manifestwriter_unconditional_write_race_data_loss_2026_07_13.md` (resolved)
_hardened_ a related legacy fallback path rather than removing it, and the codebase now also uses the CAS path
deliberately for direct canonical-index force-rewrites (`_refuse_if_index_shrink`). So the original "clean break, just
delete it" premise from 2026-04-25 may itself be stale — this needs re-scoping against current architecture before any
deletion, not a blind re-run of the old todo.

## 2. `quote_asset`/`margin_type` never surfaced in deployment-api or deployment-ui

`manifest_schema_v6_quote_margin_combo_2026_04_23.plan.md` asked for the data-status API to include the new
`quote_asset`/`margin_type` manifest dimensions and for the deployment-ui heatmap to be filterable by them. Grepped both
repos for `quote_asset`/`margin_type` (any casing) — zero hits in either. No active plan
(`data_status_page_ux_and_canonicalisation_2026_07_16.md` doesn't mention it either) claims this work. Given the
underlying v5→v6 cefi chain-tail migration itself is still incomplete (tracked in
`cefi_chain_tail_v6_canonicalisation_2026_07_21.md`), surfacing these dimensions in the UI is arguably premature until
that migration lands — but it's a real, currently-untracked gap either way.

# Why it matters

Neither is urgent (both P3), but both are genuine unfinished asks with zero current ownership — left unfiled they will
keep resurfacing as stale checkboxes in future plan-debt sweeps instead of accumulating real progress.

# Recommended decision

File both as P3 backlog items on one doc since they're small and unrelated enough not to need separate tracking
overhead.

## Todos

- [ ] [DIAG] P3. Re-scope the `_write_with_generation_match` legacy-CAS-path cleanup against current architecture (it's
      now also used for canonical-index force-rewrites) — determine whether a clean deletion is still possible, or
      whether the 2026-04-25 todo's premise needs updating. (repo: unified-trading-library)
- [ ] [CODE] P3. Add `quote_asset`/`margin_type` to the deployment-api data-status API response for cefi chain shards —
      gate on `cefi_chain_tail_v6_canonicalisation_2026_07_21.md` landing first (surfacing pre-migration data would be
      misleading). (repo: deployment-api)
- [ ] [UI] P3. Make the deployment-ui coverage heatmap filterable by `quote_asset`/`margin_type` once the API exposes
      them (previous todo). pw:L2 regression spec required. (repo: deployment-ui)

## Codex SSOTs

`codex/02-data/shard-granularity-cefi.md`, `codex/02-data/availability-manifest-and-data-status.md`.
