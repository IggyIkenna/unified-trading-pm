---
title: "Concurrent Backfill During Phase 2.6 Migration — Empirically Safe, Process Gap Documented"
created: 2026-05-15
author: ikenna-main
source:
  - plans/active/code_freeze_migrate_backfill_sequencing_2026_05_10.md
  - plans/active/tradfi_ohlcv_only_mvp_backfill_2026_05_15.md
severity: LOW
blocker: false
status: LESSONS-LEARNED
locked_by: live-defi-rollout
resolved: 2026-05-15
---

# Concurrent Backfill During Phase 2.6 Migration — Process Gap

## What I Found

Phase 2.0 of `code_freeze_migrate_backfill_sequencing_2026_05_10.md` specifies that in-flight VMs should be **drained
before the Phase 2.x writer migration** runs. The intent: avoid a situation where pre-migration VMs are writing
old-schema rows while the writer codebase is mid-update.

In practice, during the 2026-05-15 TradFi OHLCV backfill window:

- 63 OHLCV VMs were launched starting ~2026-05-15 (slot 5 autonomous execution)
- Phase 2.6 writer migration (`record_expected_empty` + `EXPECTED_*` reason taxonomy) was already complete
  (UAC@8867891 + UTL@958634f9, shipped 2026-05-07, ~8 days prior)
- Phase 1 freeze gate: **8/9 ✅** — UAC v8 schema, writer contract, MANIFEST_SCHEMA_VERSION 7→8 (UTL@547ff3c),
  ServiceEmissionPolicy, available_at semantics all shipped before VMs launched

So the migration happened _before_ the VMs launched, not concurrently. The Phase 2.0 drain gate was vacuously satisfied:
nothing to drain because no pre-migration VMs existed at that point.

## Empirical Safety Result

Slot 5 confirmed on 2026-05-17: **0 attempted_failed rows** in 214k captured OHLCV rows. The `expected_unattempted`
propagation chain (70% done at time of backfill) did NOT corrupt the captured set — it only affects how _future_
unattempted rows are classified.

The backfill was safe.

## Why It Matters — The Process Gap

The Phase 2.0 drain gate was written to catch the case where:

1. Old VMs with old writer contract are still running
2. A new writer migration lands (schema change, reason taxonomy, capture_status semantics)
3. The two writer versions produce mixed-schema rows in the same manifest shard

This scenario was _not_ present in the 2026-05-15 window (migration landed 8 days before any VMs launched). However, the
gate does not encode WHY it's safe — it just says "drain first." A future executor reading the plan could launch a
migration, then launch VMs against an already-migrated writer, and not realize the gate is vacuously satisfied vs.
genuinely unsafe.

Also: `expected_unattempted_propagation_chain` at 70% done (31/44) is non-blocking for captured rows but does mean ~30%
of expected-unattempted classification logic is not yet emitting properly. This is a separate correctness gap from the
writer migration (no contamination of captured rows confirmed).

## Recommended Decision

This is a **lessons-learned issue**, not a rollback or fix request.

**For the next migration window (or post-cutover lessons)**:

1. **Add a "migration timestamp" field to the drain gate** in `code_freeze_migrate_backfill_sequencing` — record which
   migration landed at which commit/date, so future executors can confirm "VMs launched after migration at
   `<sha>/<date>` are safe without a drain pass."

2. **Encode the vacuous-safety condition explicitly**: if `last_migration_date < first_vm_launch_date`, the drain gate
   is automatically satisfied. Add a comment to Phase 2.0.

3. **Finish `expected_unattempted_propagation_chain` before next backfill wave**: at 70% (31/44), the 30% gap means some
   expected-unattempted rows are silently falling through without classification. For the May-23 gate this is tolerable
   (captured rows are clean); post-cutover this gap should close before any new backfill wave runs.

4. **"Next time: drain first"** — for any migration where writer contract changes land _after_ VMs are already running,
   enforce a drain gate. The 2026-05-15 case was safe only because migration preceded VMs. If sequencing is reversed (VM
   starts → migration lands → VM still running), the drain gate is load-bearing.

## Cross-References

- **Drain gate**: `code_freeze_migrate_backfill_sequencing_2026_05_10.md` § Phase 2.0
- **Expected-unattempted chain**: `plans/active/expected_unattempted_propagation_chain_2026_05_10.md` (31/44 done at
  2026-05-17)
- **Manifest evolution**: `plans/active/manifest_evolution_master_2026_05_10.md`
- **Empirical confirmation**: slot-5 report 2026-05-17, tradfi_ohlcv_only_mvp_backfill_2026_05_15 Phase 5
- **Writer migration SHAs**: UAC@8867891, UTL@958634f9, UTL@547ff3c (MANIFEST_SCHEMA_VERSION 7→8)

---

## Triage — 2026-05-18

**Status**: CLOSED — SHIPPED  
**Triaged by**: slot-8 triage sweep  
**Reason**: LESSONS-LEARNED; process gap documented 2026-05-17; empirically safe
