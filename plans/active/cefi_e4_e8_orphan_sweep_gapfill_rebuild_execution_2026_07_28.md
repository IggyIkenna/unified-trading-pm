---
doc_type: plan
title: CeFi E4→E8 orphan-sweep + legacy gap-fill + manifest rebuild — VM execution chain
summary: >-
  Consolidates THREE overlapping, previously-separately-dispatched todos in data_completion_cefi_2026_07_15.md (the "E4
  remaining work = ORPHAN SWEEP + gap-fill" todo / data_completion_cefi-015, its "Orphan sweep + bucket-state evidence"
  sibling / data_completion_cefi-013, and the "NEXT SESSION — execute the migration" todo) into ONE properly-scoped,
  phased execution chain — main-agent ruling BLK-650261be, 2026-07-28. All steps are human-executed (LOCAL, not
  AO-dispatched) — this is ~1.2M-object prod-bucket delete + VM-scale work, squarely the delete-safety-protocol
  hard-stop class, never an autonomous-agent action.
status: active
nature: process
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service, deployment-service, unified-trading-library]
scope: [engineer, admin]
tags: [backfill, manifest, cefi, data-correctness, irreversible-delete, vm-scale, operator-gated]
related:
  [
    /plans/active/data_completion_cefi_2026_07_15.md,
    /plans/active/legacy_bucket_dual_write_decommission_2026_07_24.md,
    /plans/active/issues/cefi_rebuild_false_phantom_itype_underlying_drift_2026_07_28.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
created: 2026-07-28
last_updated: 2026-07-28
parent_epic: manifest_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2.4
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source: [data_completion_cefi_2026_07_15.md — consolidated 2026-07-28 per main-agent ruling BLK-650261be (slot-4)]
---

# CeFi E4→E8 orphan-sweep + legacy gap-fill + manifest rebuild — VM execution chain

> **Why this plan exists.** `data_completion_cefi_2026_07_15.md` accumulated THREE separately-worded, separately-
> dispatched todos that all describe the SAME underlying E4→E8 chain (delete the pre-`pipeline_mode=` orphan objects,
> backfill the legacy-only cells, rebuild the manifest, verify, then retire the legacy bucket):
> `data_completion_cefi-015` ("E4 remaining work = ORPHAN SWEEP + gap-fill, NOT a path walk"),
> `data_completion_cefi-013` ("Orphan sweep + bucket-state evidence"), and the older "NEXT SESSION — execute the
> migration" todo (already flagged BLOCKED by a 2026-07-27 slot-14 session for the exact same reason this plan exists:
> bundling 5 irreversible/VM-scale steps into one ~1h dispatch is unsafe). Three different sessions independently
> arrived at "this needs to be its own phased plan" rather than executed as a single dispatched todo. This plan is that
> phased plan — authored 2026-07-28 (slot-4) per main-agent coordination ruling `BLK-650261be`.
>
> **Nothing in this plan auto-executes.** Every phase below is `[OPERATOR]` or requires an operator-supervised VM
> launch + monitoring — see `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` § "3. Human-only hard stops"
> (#2, the LEGACY-COPIED-NOT-MOVED invariant, applies to the ENTIRE orphan-sweep-delete phase below — it is a
> categorical hard stop, not eligible for the §3a reversibility carve-out, because §3a only narrows hard-stop #1,
> general prod-object deletes; it does not touch hard-stop #2 at all).

## Already-shipped tooling (credit, not a flip)

The delete MECHANISM this plan executes already exists and is QG-green, shipped 2026-07-28 (slot-3,
`market-tick-data-service@e663d72f`): `migrate_cefi_flat_to_v9_canonical.py --drop-stale` — twin-verified backup+delete
of the pre-canonicalisation cefi objects (day=/candle trees without `pipeline_mode=`, plus the 9 L-flat root orphans),
reusing the shared `_migrate_drop_stale.py` helper originally built for `migrate_sports_canonical_v9`'s already-proven
E8 sweep (snapshot-first → per-object twin-verify → backup-copy → parity-check → delete → verify-gone → HARD-ABORT on
any mismatch). Needs `--apply`; dry-run reports only.

A VM-launcher category wiring this tool was added this session (slot-4, `deployment-service` —
`launch-canonical-migration-vm.sh cefi-drop-stale <start> <end> {dry|full}`, DRY-BY-DEFAULT, `--apply` for full,
`--also-legacy` available via `MIGRATION_EXTRA_ARGS`). **Neither of these ships a prod-touching run** — both are tooling
only, proven in unit tests with mocked GCS, never invoked against production. This plan is where that invocation
actually happens, phase by phase, with an operator at each irreversible step.

## Phase A — E4a(i): PRE-DELETE GUARANTEE copy pass (additive, reversible, VM-launched)

- [ ] [OPERATOR] P0. Launch a fresh full-corpus-range `--apply` COPY-ONLY pass (bare `cefi` category, **NOT**
      `--drop-stale`) on a SPOT VM: `bash launch-canonical-migration-vm.sh cefi 2019-03-30 <today> full`. This is
      additive/idempotent (already-copied objects skip) — no delete happens in this phase. Monitor to completion (no
      fire-and-forget; ≥1 progress line/hr, verify STOPPED/FAILED). **Done when**: the VM's `run.log` reports a clean
      full-range pass with 0 unexpected errors — this is the "every orphan provably has a migrated dest" guarantee the
      delete phase below depends on. Cite the VM name + run.log tail as evidence.

## Phase B — E4a(ii): orphan-sweep DELETE (irreversible, `[OPERATOR]`, hard-stop #2)

- [ ] [OPERATOR] P0. **Only after Phase A is confirmed clean.** Launch the delete sweep on a dedicated SPOT VM:
      `bash launch-canonical-migration-vm.sh cefi-drop-stale 2019-03-30 <today> full` — deletes the ~1.2M
      (`~474/day × ~2,613 days`) OLD `day=/asset_group=cefi/…` (no-`pipeline_mode=`) orphan objects corpus-wide + the 9
      L-flat root orphans, via the twin-verify/backup/delete/verify-gone contract in `_migrate_drop_stale.py`. Cite
      `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` § Part 5 (LEGACY-COPIED-NOT-MOVED) — this is hard-stop
      #2, human-execute-only regardless of the §3a soft-delete carve-out (§3a narrows hard-stop #1 only). **Also
      covers**: the pre-existing legacy-FORM `-prd` objects measured 2026-06-02 (`market-data-tick-cefi-prd` was ~65% of
      legacy object count, ~17 days stale, INTERMEDIATE FORM — has `asset_group=cefi` in the path but no
      `pipeline_mode=` partition) — these become orphans the SAME way once their `pipeline_mode=` siblings exist, so
      this sweep must delete them too, not only a separate legacy SOURCE-bucket pass. **Done when**: post-sweep object
      count via Cloud Monitoring `storage/v2/total_count` (`type=live-object` — never a naive recursive `ls`, which
      double-counts noncurrent versions + soft-deleted objects) confirms the pre-`pipeline_mode=` shape is gone
      corpus-wide. Cite the before/after Monitoring counts as evidence. Absorbs the measured-evidence content of the
      former `data_completion_cefi_2026_07_15.md` "Orphan sweep + bucket-state evidence" todo
      (`data_completion_cefi-013`).

## Phase C — E4b: legacy→canonical gap-fill (additive, VM-scale)

- [ ] [DATA] P1. The 5,233-cell legacy-only gap-fill:
      `MIGRATION_EXTRA_ARGS="--also-legacy" bash     launch-canonical-migration-vm.sh cefi <start> <end> full` (bare
      `cefi` category — additive-only, no `--drop-stale` in this phase; `--also-legacy` reads the legacy
      `market-data-tick-cefi` bucket as an additional source and copies any still-missing cell forward to canonical).
      Shard/bigger-mem: the 1.9M legacy-object listing previously stalled an `e2-standard-4` (use
      `MACHINE_TYPE=e2-standard-16` or shard the date range across multiple VMs). **Done when**: a fresh
      legacy-only-cells count reads 0 (was 5,233).

## Phase D — E5: manifest `_index` rebuild — BLOCKED on the false-phantom fix

- [ ] [DATA] P0. **Depends on** `plans/active/issues/cefi_rebuild_false_phantom_itype_underlying_drift_2026_07_28.md`
      landing (in-flight, per main 2026-07-28) — a clean `rebuild_cefi_manifest.py --dry-run` over the full corpus must
      show `phantom_to_failed` collapsed to a small DERIBIT-chain-style residual (was 490,639 / ~8.6% of the prior
      index, a confirmed false-phantom bug, NOT real orphans) before this phase runs `--apply`. Once unblocked: run
      `rebuild_cefi_manifest.py --apply` full range on a VM (now CF-11-canonical + false-phantom-safe, `mtds#fa2b02c7` +
      the fix). **Done when**: the rebuild completes and a fresh `cf_manifest_audit` shows `phantom_to_failed` at the
      expected small residual, not the 8.6% figure.

## Phase E — E7: verify

- [ ] [DATA] P0. Re-run `unified_trading_library.cf_manifest_audit.audit()` against `market-data-tick-cefi-prd-…` (the
      reusable tool already used by prior sessions this week) → confirm **CF-1…CF-12 GREEN on data-state**: v9=100% (was
      97.4-97.5%), `source` blank=0% (was 24.0%), `pipeline_mode` blank=0% (was 1.4-1.5%), Era-B legacy-form rows=0 (was
      ~490K). Flip the CF-coverage rows in `cefi_master_audit_instructions.md`. **Done when**: the audit's own printed
      verdict is GREEN on all four criteria — do not flip on a RED audit (data-pipeline-correctness HARD RULE). Once
      GREEN, flip the "E7 Verify" AND the "Post-walk" audit todos in `data_completion_cefi_2026_07_15.md` (both
      currently RED, most recently re-confirmed 2026-07-28 by slot-6/slot-8) citing this plan's evidence.

## Phase F — E8: legacy bucket delete — human-only hard stop, triple-gated

- [ ] [OPERATOR] P0. **Gated on ALL of**: (1) Phase E reads GREEN on all four criteria; (2)
      `plans/active/legacy_bucket_dual_write_decommission_2026_07_24.md`:134 — "Do NOT delete an AG's legacy bucket
      while its L3 plan is open" — cefi's L3 plan (`data_completion_cefi_2026_07_15.md`) must itself be C-GREEN/closed,
      or this specific decommission item explicitly re-evaluated against its then-current open items; (3)
      delete-safety-protocol hard-stop #1 — a **whole-bucket** destroy is NEVER reversibility-qualified under §3a
      regardless of soft-delete config, so this step is human-execute-only unconditionally. Once all three clear:
      permanently delete the legacy `market-data-tick-cefi` bucket (both GCP live objects AND the 3.81M
      noncurrent/versioned objects it carries) — canonical `market-data-tick-cefi-prd` becomes the sole SSOT. Record the
      action in `_index/snapshots/decommission_2026_0X.md` per the decommission plan's own convention.

## Progress Log

### 2026-07-28 (slot-4, `data_engineering`) — plan authored, consolidating 3 overlapping todos per main ruling BLK-650261be

Main-agent coordination (via `/api/slots/4/progress` message) identified that `data_completion_cefi-015` (this session's
dispatched task) is the SAME underlying E4→E8 chain as its sibling `data_completion_cefi-013` (slot-3, "Orphan sweep +
bucket-state evidence") and the older "NEXT SESSION — execute the migration" todo (already declined by a 2026-07-27
slot-14 session for the identical reason). Ruling: do NOT execute the irreversible sweep now (human-only per
delete-safety §3a / hard-stop #2); author ONE consolidated, phased plan instead (this doc); mark all three source todos
`superseded_by` this plan in `data_completion_cefi_2026_07_15.md`, checkboxes left UNCHECKED (no sweep has run); credit
the already-shipped `--drop-stale` tooling (`mtds@e663d72f`) as a nested done-note, not a flip. Also shipped this
session, ahead of this plan: the `cefi-drop-stale` VM-launcher category in `deployment-service`
(`launch-canonical-migration-vm.sh` + regression tests, mocked-GCS only, no prod invocation) — Phases A-C above are how
that tooling actually gets run against production, one operator-supervised step at a time.
