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
status: resolved
nature: issue
asset_group:
  [cross-cutting] # corrected 2026-07-25 (ag-closeout-audit orthogonality fix) -- was [cefi, cross-cutting],
  # a genuine mistag: this is UTL manifest CAS-path + deployment-api/ui quote_asset/margin_type surfacing, a genuinely
  # cross-AG manifest-schema concern with no cefi-specific content

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
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
  ]
created: "2026-07-21"
author: unknown
parent_epic: infrastructure_master
priority: P3
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: data_engineering
drift_direction: advance-code
source: [pm_qg_plan_discipline_and_frontmatter_regression-006]
resolved_by:
locked_by:
context_scope:
  [
    /codex/02-data/shard-granularity-cefi.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /plans/archive/issues/cefi_chain_tail_v6_canonicalisation_2026_07_21.md,
    unified-trading-library/unified_trading_library/manifest_writer/_writer_io.py,
    unified-trading-library/unified_trading_library/manifest_writer/_maintenance.py,
  ]
depends_on: []
gate_on_depends: false
sequential: true
---

> **ARCHIVED (2026-08-10) — all todos done, unlocked.** Both residual items resolved: the legacy CAS-path re-scope
> concluded "no deletion, no code change" (still live + deliberately reused for canonical-index force-rewrites); the
> quote_asset/margin_type API+UI gap shipped `deployment-api@c250348` + `deployment-ui@e2d109a` (2026-08-05). Archived
> by `plan_reconciler` (cross-cutting tranche, dispatch `agt-33a6ec`). Deferred work migrated to: none (no
> DEFERRED/NICE-TO-HAVE items found in this doc).

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

- [x] ✅ [CODE] P3. Add `quote_asset`/`margin_type` to the deployment-api data-status API response for cefi chain shards
      — deployment-api@c250348 + evidence: AXIS_CENSUS_COLUMNS extended,
      get_schema/get_data_status_manifest/get_schema_for_shard params added, manifest service plumbing wired, 8 files +
      tests — gate on `cefi_chain_tail_v6_canonicalisation_2026_07_21.md` landing first (surfacing pre-migration data
      would be misleading). (repo: deployment-api)

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

  **na-eligibility-audit 2026-08-03**: the depended-on doc has since resolved —
  `plans/archive/issues/cefi_chain_tail_v6_canonicalisation_2026_07_21.md` is now `status: resolved` (`resolved_by`:
  "all 8 todos shipped with commit SHAs, test names, and a real GCS `-test-` bucket end-to-end proof dated 2026-07-27"),
  including todos 5-8 this block cited as open. The gate's stated reason ("surfacing pre-migration data would be
  misleading") is now moot too: todo 6 there enumerated **0** real v5 cefi chain objects to migrate (307 manifest rows,
  all `attempted_failed`/`empty_confirmed`, zero `captured`), so there is no inconsistent pre-migration data to surface.
  **Not closing this todo** — the gate is cleared but the actual API work (adding `quote_asset`/`margin_type` to the
  deployment-api response) has not been implemented; this is still genuinely open, just no longer blocked. Same applies
  to the UI todo below (transitively gated on this one).

  **RESOLVED 2026-08-05 — verified by plan_reconciler 2026-08-10.** The checkbox above (`[x]`, `deployment-api@c250348`)
  is correct, not this note — the API work landed the same day this note's gate-clearing finding did, just a few commits
  later. Live-verified: `c250348a92eab639e95f66c784ebd062ad0ff6e7` is on `deployment-api`'s `origin/live-defi-rollout`
  and its own commit message ("Fixes: manifest_v6_batch3_residual_orphaned_work-001") matches the exact 6-file
  `AXIS_CENSUS_COLUMNS`/schema/manifest-API change this todo describes. This "still genuinely open" line is left in
  place as the historical record of the state at 08-03, not a live claim — see also the Follow-ups section below, which
  reopened this (and the UI todo) as fresh duplicate items based on this same stale read; both closed as moot there.

- [x] ✅ [UI] P3. Make the deployment-ui coverage heatmap filterable by `quote_asset`/`margin_type` once the API exposes
      them — deployment-ui@e2d109a | pw:L2 ✓ | regression: tests/e2e/data-status-axis-value-census.spec.ts (repo:
      deployment-ui)

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

`/codex/02-data/shard-granularity-cefi.md`, `/codex/02-data/availability-manifest-and-data-status.md`.

## Progress Log

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid — both remaining todos carry `depends_on` +
  `gate_on_depends: true` on `cefi_chain_tail_v6_canonicalisation_2026_07_21`, whose todos 5-8 are still open — never
  re-litigate a live gate.
- **na-eligibility-audit 2026-08-03 (reclassify pass)**: RECLASSIFY -> planning. The gating prerequisite
  (`cefi_chain_tail_v6_canonicalisation_2026_07_21.md`) resolved 2026-08-03 (see the `[CODE] P3` todo's own inline note
  above) — 0 real v5 cefi chain objects needed migrating, so the "surfacing pre-migration data would be misleading"
  reason for the gate is moot. Both remaining todos are now bounded, worker-determinable engineering (add
  `quote_asset`/`margin_type` to a deployment-api response + a deployment-ui heatmap filter on those fields, pw:L2 spec
  required) with no judgment/design call left. Conflict-check clear: grepped `plans/active/*.md` +
  `plans/active/issues/*.md` for `quote_asset`/`margin_type`; no other `assigned_vm: planning` doc claims this exact
  work — corroborated by `cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md`'s own prior conflict-check on this
  same doc ("No genuine conflict found, and nothing is stealthily duplicating this doc's ground"). `locked_by` empty.
  `execution_scope` was already `orchestrator-agent` (no change needed); only `assigned_vm` flipped. A companion
  finalize doc is owed (not authored here).
- **context-scout 2026-08-03**: refreshed context_scope (5 entries) — reviewed against current doc content, list still
  accurate (unchanged).
- **slot-3 dispatch-ordering fix 2026-08-03**: `-002` (the `[UI]` heatmap-filter todo) was dispatched to a ui_developer
  craft worker BEFORE `-001` (the `[CODE]` deployment-api todo it depends on) had shipped — live-verified zero
  `quote_asset`/`margin_type` hits in either `deployment-api` or `deployment-ui` repos. The 2026-08-03 reclassify pass
  flipped `assigned_vm: planning` for both todos but never sequenced them (`depends_on`/`gate_on_depends` only gate a
  whole PLAN against another plan, not one todo in a doc against a sibling todo in the same doc) — so nothing stopped
  `-002` from dispatching before `-001`. Implementing the UI filter now would mean wiring controls to a contract the API
  doesn't return yet, violating the ui_developer craft's "render exactly what the API returns" rule. Fix: added
  `sequential: true` to this doc's frontmatter so `-001` must land before `-002` dispatches. Releasing `-002` back to
  the queue via `/skip-current-task`; `-001` is genuinely data_engineering-craft work (manifest/data-status API) and
  should dispatch next.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (5 entries), unchanged.

## Follow-ups

- [x] ✅ [CODE] P3. ~~Add quote_asset/margin_type to the deployment-api data-status API response for cefi chain shards~~
      **MOOT — verified by plan_reconciler 2026-08-10.** This duplicated the main `[CODE] P3` checkbox above (itself a
      malformed entry too — the original text ran this together with the UI item below via a mid-line `; - [ ]`, which
      never parsed as two real list items). Both are already done: `deployment-api@c250348` (2026-08-05).
- [x] ✅ [UI] P3. ~~Make the deployment-ui coverage heatmap filterable by quote_asset/margin_type once the API exposes
      them~~ **MOOT — verified by plan_reconciler 2026-08-10.** Duplicated the main `[UI] P3` checkbox above; already
      done: `deployment-ui@e2d109a` (2026-08-05).

> **2026-08-06 archive-candidate audit**: Both CODE and UI todos are marked [x] but the inline na-eligibility-audit
> 2026-08-03 note says 'the actual API work ... has not been implemented; this is still genuinely open, just no longer
> blocked' and 'Same applies to the UI todo below' — checkbox contradicts the prose.
>
> **RESOLUTION (plan_reconciler, 2026-08-10):** the checkboxes were right, the 08-03 prose was stale by the time this
> audit ran — both `deployment-api@c250348` and `deployment-ui@e2d109a` shipped 2026-08-05, one day before this audit
> note, and are confirmed live on `origin/live-defi-rollout` in their respective repos. The correct fix at the time
> would have been a closing note on the 08-03 prose (now added above), not reopening the items as fresh duplicate
> Follow-ups (done immediately above, marked moot rather than removed so the record of why they existed is preserved).
