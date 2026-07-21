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
depends_on: [plans/active/issues/cefi_chain_tail_v6_canonicalisation_2026_07_21.md]
gate_on_depends: true
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

- [x] [DIAG] P3. Re-scope the `_write_with_generation_match` legacy-CAS-path cleanup against current architecture (it's
      now also used for canonical-index force-rewrites) — determine whether a clean deletion is still possible, or
      whether the 2026-04-25 todo's premise needs updating. (repo: unified-trading-library) — ✅ RE-SCOPED, no code
      change: **deletion is NOT safe, the 2026-04-25 premise is stale.**

  Live-code trace (`unified_trading_library/manifest_writer/_writer_io.py`,
  `unified_trading_library/manifest_writer/_maintenance.py`, `unified_trading_library/manifest_writer/_state.py`,
  2026-07-21):

  1. `ManifestWriter.write()` (`_writer_io.py:658-662`) branches on `self._per_vm_enabled` (`_resolve_per_vm_shards()`)
     — per-VM shard write when true, `_write_with_generation_match` (the legacy CAS path) when false.
     `MANIFEST_PER_VM_SHARDS` defaults `False` and is set `true` by ~80+ `deployment-service/scripts/vm/launch-*.sh`
     launchers — so per-VM IS now the norm for VM-launched backfill/live jobs, confirming the flag rollout itself
     succeeded.
  2. BUT `unified_trading_library/manifest_writer/_maintenance.py:430`'s `emit_migration_manifest_updates()` — the
     migration-tooling function that applies canonical-dimension rewrites during a live migration (e.g. the in-flight
     `cefi_chain_tail_v6_canonicalisation_2026_07_21.md` v5→v6 work, and the recently-landed DeFi-fold registration) —
     constructs `ManifestWriter(service_name=..., catalogue_bucket=...)` with NO `per_vm_shards` override, and its
     docstring is explicit that "the write uses the same GCS generation-match path as `ManifestWriter.write`, so
     concurrent migration VMs are safe." This is a DELIBERATE, current-day production dependency on
     `_write_with_generation_match`'s CAS retry-loop semantics — a one-shot canonical-index mutation needs the immediate
     atomicity CAS provides; the per-VM path's "write your own shard, consolidate later" model doesn't fit a migration
     that must land its rewrite before returning.
  3. `_write_with_generation_match` → `_try_conditional_write` → `_refuse_if_index_shrink` (the 2026-07-15
     328k-row-clobber regression guard) and its `allow_index_shrink=True` deliberate-force-rewrite override
     (`_writer.py:102`, docstring: "Explicit force flag for the direct-canonical-index...") are layered specifically on
     this write path. Deleting the path deletes the only sanctioned way to do a guarded, forced, atomic one-off
     canonical-index rewrite.

  **Conclusion**: the archived plan's Phase 6 framing ("after last bucket cutover: delete `_write_with_generation_match`
  legacy path, delete feature flag") assumed per-VM sharding would become universal and retire the single-blob path
  entirely. That premise is now stale — per-VM sharding solved the _concurrent incremental-write_ contention problem it
  targeted, but a _second, distinct_ use case (atomic direct-canonical-index rewrites for migrations/maintenance)
  emerged afterward and deliberately keeps building on the "legacy" path. `MANIFEST_PER_VM_SHARDS` is not a temporary
  rollout flag to be deleted — it is a permanent mode selector between two write strategies with different consistency
  needs. No deletion, no code change. Archived plan `plans/archive/manifest_429_per_vm_sharding_2026_04_25.plan.md`
  Phase 6's unchecked "delete the legacy path" todo is superseded by this finding (archived plans are not re-executed
  per this workspace's SSOT-direction rule; this issue doc is the resolution record — no edit made to the archive
  itself).

- [ ] [CODE] P3. Add `quote_asset`/`margin_type` to the deployment-api data-status API response for cefi chain shards —
      gate on `cefi_chain_tail_v6_canonicalisation_2026_07_21.md` landing first (surfacing pre-migration data would be
      misleading). (repo: deployment-api)

  **BLOCKED on dependency (2026-07-21, BLK-3f4c6134, confirmed by main)**: dispatched to a worker who checked
  `cefi_chain_tail_v6_canonicalisation_2026_07_21.md` and found todos 5-8 (prove W1 emits v6, migrate v5→v6 objects,
  resync manifest/data-status, record cutover date) still open/unchecked — only the code-fix todos (1-4) have landed.
  Implementing this now would surface pre-migration/inconsistent data through the API, tripping the data-pipeline-
  correctness heartbeat rule. Recorded as a formal `depends_on` in this doc's frontmatter (see above) so this todo
  re-dispatches once that migration's remaining todos land and its cutover date is recorded — do NOT implement until
  then.

  **Re-dispatched + re-verified still blocked (2026-07-21, same day, slot 7)**: this todo was dispatched again despite
  the block above — the frontmatter `depends_on` alone does NOT gate dispatch (per this workspace's plan-authoring
  rules, only `gate_on_depends: true` machine-holds a task), which this doc never set, so it kept re-entering the queue.
  Re-checked `cefi_chain_tail_v6_canonicalisation_2026_07_21.md` fresh: todos 5-8 are STILL open/unchecked — the block
  genuinely still applies, this is not stale. **Fixed the actual bug**: added `gate_on_depends: true` to this doc's
  frontmatter so both blocked todos here (this one + the UI heatmap one below) stop being mis-dispatched until the v6
  migration's remaining todos actually land. No feature code implemented (correctly still blocked) — escalating via
  `/blocked` rather than fabricating progress or silently sitting idle.

- [ ] [UI] P3. Make the deployment-ui coverage heatmap filterable by `quote_asset`/`margin_type` once the API exposes
      them (previous todo). pw:L2 regression spec required. (repo: deployment-ui) — same `depends_on` gate as above
      (transitively blocked on the API todo, which is blocked on the v6 migration).

  **Re-dispatched a THIRD time despite `gate_on_depends: true` (2026-07-21, slot 2)**: re-verified fresh —
  `cefi_chain_tail_v6_canonicalisation_2026_07_21.md` todos 5-8 are STILL open/unchecked, the block genuinely still
  applies (same conclusion as the slot-7 re-check above). This is the SECOND observed instance of
  `gate_on_depends: true` failing to prevent dispatch on this exact doc (slot-7 already fixed the frontmatter once for
  this same symptom) — either the fix didn't take effect, the dispatcher reads a cached/stale backlog projection, or
  there's a genuine bug in how `gate_on_depends` is enforced. This is an agent-orchestrator dispatch-logic question, out
  of scope for a UI todo to diagnose or fix mid-course. No feature code implemented (correctly still blocked — the
  data-pipeline-correctness heartbeat rule explicitly forbids surfacing pre-migration/inconsistent data). Escalating via
  `/blocked` rather than fabricating progress; whoever owns agent-orchestrator's dispatch logic should check why
  `gate_on_depends: true` isn't holding this doc's todos.

## Codex SSOTs

`codex/02-data/shard-granularity-cefi.md`, `codex/02-data/availability-manifest-and-data-status.md`.
