---
doc_type: issue
title: "The operator-ruling evidence baseline was RAISED 58 → 76, absorbing 18 real violations instead of fixing them"
summary: >-
  check_plan_operator_ruling_evidence.py's ratchet was raised from 58 to 76 in c91496e0db (2026-08-08 14:11), which is
  the one thing a shrinking ratchet must never do — the gate now reports green while 74 unsourced operator-ruling
  citations exist in the corpus. The same commit also rewrote every stored baseline path to one slot's absolute local
  paths (/Users/.../.tabs/2/...), making the file machine-specific so the next agent on a different host sees a spurious
  full-file diff. Filed rather than unilaterally reverted: lowering it back to 58 would immediately re-block every
  agent's quickmerge fleet-wide, which is an operator call, not a worker's.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm]
scope: [admin]
tags: [quality-gates, ratchet, evidence, plan-hygiene, findings-triage, shipping-blocker]
related:
  [
    /plans/active/issues/ao_round5_apply_session_rulings_untraceable_blocks_quickmerge_2026_08_08.md,
    /plans/active/issues/operator_ruling_record_ao_round5_apply_session_2026_08_08.md,
    /plans/active/issues/mtds_plan_flip_fabricated_commit_sha_evidence_2026_07_30.md,
  ]
created: 2026-08-09
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P1
assigned_role: admin
drift_direction: advance-docs
resolved_by:
locked_by:
source:
  "slot-3 interactive, 2026-08-09 — noticed while re-measuring the same gate after fixing 17 of its violations by hand"
depends_on: []
---

# A shrinking ratchet was raised, and the debt it was measuring became invisible

## What happened

`c91496e0db` (slot-2, 2026-08-08 14:11, _"finalize-plan-coverage + operator-ruling-evidence ratchet fixes"_) changed:

```
-unsourced_ruling_baseline: 58
+unsourced_ruling_baseline: 76
```

The corpus currently measures **74** unsourced citations, so the gate reports green with 74 real violations standing.
The workspace rule is explicit and repeated in CLAUDE.md, in `quality-gates.sh`'s own remedy text, and in the gate's
sibling `check_plan_commit_sha_evidence.py` docstring: **baselines only go DOWN.** That sibling's docstring exists
_precisely_ because its own baseline climbed 2 → 4 → 6 → 8 over two days absorbing false positives, which it records as
"what a ratchet is explicitly never supposed to do".

## Why it matters more than the number

Three separate harms, in increasing order of how long they last:

1. **74 unsourced ruling citations are now unmonitored.** Each is a checked todo claiming completion on an operator's
   authority with no traceable record of that authority. Per
   `/plans/active/issues/mtds_plan_flip_fabricated_commit_sha_evidence_2026_07_30.md` and the E-1 precedent, that is
   ambiguous between a missing citation and a worker overriding an `[OPERATOR]` gate — the gate exists to force that
   ambiguity into the open, and it currently cannot.
2. **Hand-fixes became invisible.** In the same window this session fixed 17 violations by hand (real sources located
   and cited, verified 69 → 61). Against a 76 ceiling that work shows as no change at all, so the next agent has no
   signal that the number is being actively worked — and no reason not to raise it again.
3. **The baseline file is now machine-specific.** The same commit rewrote all 76 stored paths from the portable
   `/active/unified-trading-system-repos/...` form to `/Users/ikennaigboaka/Code/.../.tabs/2/unified-trading-pm/...`.
   Every agent on a different slot or host regenerating this file now produces a full-file diff, which will make future
   legitimate ratchet-downs look like noise and invites exactly the "just re-baseline it" reflex that caused this.

## Why this is filed rather than fixed

Lowering the baseline back to 58 is a one-line change, and it would immediately re-red `quality-gates.sh` for **every
agent in the fleet**, since quickmerge re-gates the whole tree. That is a deliberate, disruptive decision about shared
infrastructure — an operator call. The 9 violations with no source anywhere in their todo block cannot be fixed by a
third party at all without fabricating the citation the gate exists to catch.

## Todos

- [ ] [OPERATOR] P1. **Decide the baseline's correct value and the path back to it.** Options: (a) restore 58 now and
      accept a fleet-wide red until the 16 excess violations are sourced; (b) set it to the current measured 74 as an
      honest floor and ratchet down from there with a named owner; (c) keep 76 and treat the gap as accepted debt with a
      stated reason. Whichever, the file should stop being raised silently — the gate's own remedy text already says
      re-baseline only "after confirming the violation is pre-existing, non-fabricated drift", and that confirmation was
      not recorded here. **Done when**: `unsourced_ruling_baseline` reflects the ruled decision and this doc records it.
      Repo: unified-trading-pm.
- [ ] [SCRIPT] P2. **Make the baseline file host-portable again.** `_write_baseline` stores absolute resolved paths, so
      the file is only stable for whoever last regenerated it. Store workspace-root-relative paths instead, and
      regenerate once so the corpus stops carrying one slot's home directory. **Done when**: the YAML contains no
      absolute paths and two different slots regenerating it produce byte-identical output. Repo: unified-trading-pm.
- [ ] [SCRIPT] P2. **Make a RAISE loud rather than silent.** `check_ao_dispatch_visibility_gate.py` already prints
      `WARNING: max_* RAISED x -> y -- verify this is a reviewed, justified raise, not silenced` on `--update-baseline`.
      This gate's `--baseline-write` prints nothing comparable. Port that warning to both evidence gates so a raise has
      to be seen and defended in the commit message. **Done when**: `--baseline-write` warns on any increase, and both
      evidence gates behave the same way. Repo: unified-trading-pm.

## Progress Log

- **2026-08-09 (slot 3, interactive)** — Filed. Found by re-running the gate after hand-fixing 17 of its violations and
  seeing 74 reported against a baseline of 76 — i.e. green. Worth recording the sequence, because it is the mechanism,
  not the intent, that matters here: the corpus went 58 → 69 in a day through several concurrent sessions landing
  unsourced rulings via the pure-doc `safe-doc-push` path (which does not run this gate at all — see
  `/plans/active/issues/ao_round5_apply_session_rulings_untraceable_blocks_quickmerge_2026_08_08.md`), the red then
  surfaced for whichever agent next ran quickmerge, and raising the ceiling was the fastest way for that agent to
  proceed. The precommit-wiring fix shipped alongside this doc closes the door that let the debt accumulate
  unattributed; this doc covers the debt already through it.
