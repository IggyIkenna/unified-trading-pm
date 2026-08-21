---
doc_type: issue
title: na-eligibility-audit's per-tranche idempotency guard did not prevent two full concurrent dispatches of the SAME defi tranche, causing a real edit collision
summary: >-
  Two independent na_eligibility_auditor dispatches (agt-72629d/slot 18, this doc's author; agt-9095fb/slot 26) both
  ran a full `/na-eligibility-audit defi` pass within the same short window on 2026-08-18, each reading the identical
  Phase-0 in-scope set (4 of 60 defi-tranche docs) and reaching the same verdicts. This is distinct from the
  already-documented multi-tranche-membership race
  (na_audit_multi_tranche_shared_doc_ownership_and_draft_p0_park_2026_07_30.md, where ONE doc legitimately belongs
  to several DIFFERENT tranches and gets touched by each tranche's own single worker) — here, the SAME tranche was
  dispatched twice. The skill's own doc claims "a per-tranche idempotency guard makes every fire after that
  tranche's first success of the day a cheap no-op" (SKILL.md § Scheduled cadence), but slot 26's dispatch was not a
  cheap no-op — it ran a full, non-trivial audit and landed a real commit before slot 18's overlapping dispatch
  reached the same files. Caused one real, self-inflicted edit collision: slot 18's `Write` tool call to
  `na_eligibility_audit_defi_blocks_2026_08_18.md` blindly overwrote slot 26's already-committed content (Write
  replaces wholesale, unlike Edit's old_string match) before slot 18 discovered the collision via a failed Edit's
  "File has been modified since read" error on a different file and investigated. No content was permanently lost
  (slot 26's version was already committed, recovered via `git show`), and slot 18 also caught + retracted a
  genuinely incorrect duplicate action it had taken (extracting a satellite AO batch that slot 26's more thorough
  conflict-check had correctly avoided) — but this worked out safely only because slot 26 happened to commit before
  slot 18's Write executed. A slightly different timing (both uncommitted when the collision occurred) would have
  silently destroyed real work with no recovery path.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm, agent-orchestrator]
scope: [engineer, admin]
tags:
  [na-eligibility-audit, plan-hygiene, concurrency, ao-dispatch, idempotency, duplicate-dispatch, edit-collision]
related:
  [
    /cursor-configs/skills/na-eligibility-audit/SKILL.md,
    /plans/active/issues/na_audit_multi_tranche_shared_doc_ownership_and_draft_p0_park_2026_07_30.md,
    /plans/active/issues/na_eligibility_body_hash_unstable_across_marker_appends_2026_08_17.md,
    /plans/active/issues/na_eligibility_audit_defi_blocks_2026_08_18.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
  ]
parent_epic: plan_hygiene_master
created: 2026-08-18
last_updated: 2026-08-19 # was 2026-08-18 -- stale vs the 2026-08-19 na-eligibility-audit + RECLASSIFY-split entries (the doc's true tail); corrected (plan_reconciler ao)
author: claude-code (na_eligibility_auditor, slot 18, DISPATCH_ID=agt-72629d, tranche=defi)
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.32
assigned_role: backend_engineer
drift_direction: none
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
context_scope:
  [
    /cursor-configs/skills/na-eligibility-audit/SKILL.md,
    agent-orchestrator/server/plan_health.py,
    agent-orchestrator/scripts/install-na-eligibility-auditor-timer.sh,
  ]
source: >-
  Discovered live during the 2026-08-18 `/na-eligibility-audit defi` run (dispatch agt-72629d, slot 18), while
  reconciling a failed Edit call ("File has been modified since read") on
  defi_leverage_archetypes_health_factor_wrong_source_2026_08_16.md.
---

# na-eligibility-audit's per-tranche idempotency guard did not hold across two concurrent same-tranche dispatches

## What happened

This session (slot 18, `DISPATCH_ID=agt-72629d`, `TRANCHE=defi`) ran Phase 0 of `/na-eligibility-audit defi` and
found the expected small incremental set: 4 of 60 defi-tranche docs in scope (56 already-verdicted-and-unchanged).
Mid-run, an `Edit` call on `defi_leverage_archetypes_health_factor_wrong_source_2026_08_16.md` failed with "File has
been modified since read" — the file had changed on disk between this session's `Read` and its `Edit` attempt,
despite no commit having landed from THIS session in between.

Investigation (`git log --since="15 minutes ago"`) found commit `d0cc419300` — authored `ikennaigboaka
[main·planning]`, message `docs(plans): na-eligibility-audit defi 2026-08-18 — close 8 leverage-archetype todos by
citation, cross-reference FOLD-3 residual with C4, supersede blocks doc` — landed moments earlier. Its content
(read via `git show d0cc419300`) is a complete, correct `/na-eligibility-audit defi` pass: the same Phase-0 result
(4 of 60 docs in scope), the same 4 verdicts this session independently reached, sourced from dispatch `agt-9095fb`,
slot 26.

**Two full audits of the identical single tranche ran concurrently**, not two different tranches sharing one
overlapping doc (the already-documented and already-mitigated class).

## Why this is a distinct finding from the multi-tranche-membership race

`na_audit_multi_tranche_shared_doc_ownership_and_draft_p0_park_2026_07_30.md` and the shipped `owning_tranche`
primary-owner mechanism solve a different problem: ONE doc legitimately belonging to several DIFFERENT tranches
(e.g. `asset_group: [cefi, defi, tradfi]`) being read by each tranche's own single dispatched worker, with only the
owning tranche allowed to write the marker. That mechanism assumes each TRANCHE has at most one live worker at a
time. This incident breaks that assumption directly — the SAME tranche (`defi`) had two live workers at once, so
even a doc with a completely unambiguous single-tranche `owning_tranche` (all 4 of today's in-scope docs are
defi-only) still got a race.

The skill's own SKILL.md § "Scheduled cadence" states: "Cadence as of 2026-07-30: every 2 hours, on ODD hours at
:30 UTC (a per-tranche idempotency guard makes every fire after that tranche's first success of the day a cheap
no-op, so this is retry-until-capacity, not 12 audits a day)." That guard did not hold here — slot 26's dispatch was
a full, real, multi-file, multi-commit audit, not a no-op, and it ran close enough in time to slot 18's own dispatch
that both did the complete Phase-0-through-Phase-3 cycle independently before either could observe the other's
result.

## The real (if narrowly-avoided) consequence: a blind-Write collision

Once the concurrent dispatch was discovered, reconciliation found slot 18 had:

1. **Independently reached the same verdicts** as slot 26 on 3 of 4 docs (harmless redundancy — both landed
   equivalent, correct citation markers; left as-is rather than risk a second collision cleaning it up).
2. **Made a genuinely worse call than slot 26 on the 4th item** (the `defi_migration_audit_log_2026_07_24.md`
   FOLD-3-orphan-data_types mandatory carry-forward residual): slot 18 extracted it into a new standalone
   `defi_satellite_ao_dispatch_batch17_2026_08_18.md` satellite batch; slot 26 had already correctly found that
   `data_completion_defi_2026_07_15.md`'s existing NA todo "C4" (a schema v4→v9 re-version walk) likely already
   covers the same 3 data_types, and deliberately did NOT extract — to avoid dispatching a duplicate schema-reversion
   walk. Slot 18's own conflict-check grep had actually surfaced `data_completion_defi_2026_07_15.md` as a hit
   (matched on `vault_share_price`/`risk_params`), but slot 18 did not follow up by reading that specific doc before
   concluding "conflict-check clear" — a real gap in slot 18's own conflict-check execution, not just bad luck from
   the race. Caught and retracted on discovery (batch17 + its finalize deleted, never committed; the incorrect
   checkbox-flip + citation on the source doc reverted to match slot 26's correct, unresolved-but-cross-referenced
   state).
3. **Blindly overwrote slot 26's already-landed `na_eligibility_audit_defi_blocks_2026_08_18.md`** via a `Write`
   tool call (which replaces a file's content wholesale) rather than an `Edit` (which requires an exact `old_string`
   match and would have failed loudly, the way the leverage-archetypes `Edit` did). Slot 18's `Write` call result
   even reported "has been updated successfully" rather than "has been created successfully" — a signal, in
   hindsight, that the file already existed and this session's context did not know why. Recovered cleanly only
   because slot 26's version was already committed (`git show d0cc419300:<path>`); restored verbatim plus one
   addendum documenting this incident.

**If slot 26's commit had landed a few seconds LATER** — i.e., both sessions' edits to
`na_eligibility_audit_defi_blocks_2026_08_18.md` still uncommitted and in-flight at the same time — the blind
`Write` would have silently destroyed real, uncommitted work with no git history to recover from. This incident's
safe outcome was a timing accident, not a property of the current design.

## Open questions for the operator / a dispatched investigation (not resolved by this doc)

- [x] ✅ [BACKEND] P2. **Root-caused 2026-08-18 (plan_reconciler, ao tranche, hunter #3) — was mistagged
      `[OPERATOR]`, retagged: this was pure code-reading investigation, not a credential/judgment call.** Read
      `server/plan_health.py`'s `dispatch()` directly: its only at-most-one-live-dispatch coalescing mechanism,
      `_report_dispatch_gate()`, is called exclusively when `mode == "report"`; the function's own docstring lists
      `mode="na_eligibility"` explicitly among the modes "exempt from the whole gate (their own scheduled call, not
      promotion-triggered)". **Verdict: a design gap, not a race in the tracking** — there is no server-side
      duplicate/live-dispatch guard for this mode at all, so it doesn't matter whether the two triggers were the
      scheduled timer + a manual call or two scheduled fires; neither would have been coalesced. The "per-tranche
      idempotency guard" SKILL.md describes is a WORKER-side behavior (Phase 0's incremental-skip via each doc's
      own already-verdicted content), not a dispatch-level lock. Evidence: `agent-orchestrator/server/plan_health.py`
      (`dispatch()`'s `if mode == "report": ... _report_dispatch_gate(...)` gate + its docstring's explicit
      exemption list). Same root cause independently confirmed to also affect `mode="reconcile"` (the
      `plan_reconciler` skill) — see `plan_reconciler_dead_run_no_lock_ttl_2026_08_12.md` todo 4, cross-linked.
      Todo 2 below (the actual hardening fix) remains open and is now unblocked with a concrete, evidenced target.
- [x] N. ✅ [BACKEND] P2. **Harden the same-tranche concurrent-dispatch case regardless of root cause**, once the above is
      answered — options include: a dispatch-time lock per tranche (reject/queue a second `defi` dispatch while one
      is already live), or narrowing every na-eligibility-audit Phase-3 file-touching step to `Edit`-only (never
      `Write`) for any file that might already exist from a concurrent run, so a genuine collision fails loudly
      (like the leverage-archetypes doc did) instead of silently overwriting. The second option is cheap and
      defends against MORE than just this specific race (any stale-Read scenario), independent of the first. Extracted to `plans/active/ao_satellite_ao_dispatch_batch25_2026_08_19.md` item 2 (na-eligibility-audit 2026-08-19, ao tranche, RECLASSIFY per-todo split).
- [ ] [OPERATOR] P3. **Decide whether this warrants a `SKILL.md` update** — e.g., "when creating a NEW same-day
      artifact doc (a blocks-index doc, a satellite batch), prefer `Edit` with a narrow anchor + `replace_all: false`
      over a blind `Write`, even for a path Phase 0 didn't report as already existing" — since Phase 0's inventory
      snapshot is itself a point-in-time read that a concurrent dispatch can invalidate.

## Progress Log

- **2026-08-18 (na-eligibility-audit, defi tranche, dispatch agt-72629d, slot 18)**: filed after discovering + fully
  reconciling the collision described above. No corpus content lost. Both incorrect slot-18 edits (the FOLD-3
  extraction and the blocks-doc overwrite) reverted/restored to slot 26's correct state; one small addendum left on
  `na_eligibility_audit_defi_blocks_2026_08_18.md` documenting the incident for anyone reading its history later.
- **plan_reconciler 2026-08-18 (ao tranche, hunter #3)**: read the live `agent-orchestrator` dispatch code directly
  to answer this doc's own open todo 1 ("was this a design gap or a race in the tracking?"). Answer: **design gap,
  not a race.** `plan_health.py`'s ONLY at-most-one-live-dispatch coalescing mechanism, `_report_dispatch_gate()`,
  is wired into `dispatch()` exclusively for `mode == "report"`; the function's own docstring explicitly lists
  `mode="na_eligibility"` (this skill's own dispatch mode) among the modes "exempt from the whole gate" — there is
  no server-side duplicate/live-dispatch check for this mode at all, regardless of whether the two triggering calls
  came from the scheduled timer, a manual invocation, or both. The "per-tranche idempotency guard" SKILL.md
  describes is a WORKER-side behavior (Phase 0's incremental-skip via each doc's own already-verdicted content), not
  a dispatch-level lock — so when two dispatches fire close enough together that neither's Phase-0 read reflects the
  other's in-flight work, both proceed as full runs, exactly as observed here. **Same root cause, same file, as
  `plan_reconciler_dead_run_no_lock_ttl_2026_08_12.md` todo 4** (which found the identical gate exemption for
  `mode="reconcile"`, the `plan_reconciler` skill's own mode) — cross-linked there too. Not fixed here (real
  `agent-orchestrator` engineering); this doc's own todo 1 can now be considered answered (the two options it
  posed — "design gap" vs "race in tracking" — resolve to "design gap," confirmed via code, not requiring the
  operator investigation it originally called for) even though todo 2 (the actual hardening fix) remains open.

- **na-eligibility-audit 2026-08-19 (ao tranche)** [body-hash:f6a1c78847a68470]: RECLASSIFY (per-todo split) — todo 2 (harden the same-tranche concurrent-dispatch case) extracted to `plans/active/ao_satellite_ao_dispatch_batch25_2026_08_19.md` item 2. Doc stays NA for todo 3 ([OPERATOR] SKILL.md-update decision).
- **context-scout 2026-08-20**: refreshed context_scope (3 entries)
- **na-eligibility-audit 2026-08-21 (ao tranche batch 3/3)**: KEEP-NA, valid — sole open item (`[OPERATOR] P3`, decide whether this warrants a SKILL.md update) is an explicit operator-authority preference call over documentation wording, not a bounded/deterministic worker outcome.
