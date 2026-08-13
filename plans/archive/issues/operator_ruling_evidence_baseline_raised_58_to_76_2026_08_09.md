---
doc_type: issue
title: "The operator-ruling evidence baseline was RAISED 58 → 76, absorbing 18 real violations instead of fixing them"
summary: >-
  check_plan_operator_ruling_evidence.py's ratchet was raised from 58 to 76 in c91496e0db (2026-08-08 14:11), which is
  the one thing a shrinking ratchet must never do — the gate now reports green while 74 unsourced operator-ruling
  citations exist in the corpus. The same commit also rewrote every stored baseline path to one slot's absolute local
  paths (/Users/.../.tabs/2/...), making the file machine-specific so the next agent on a different host sees a spurious
  full-file diff. Filed rather than unilaterally reverted: lowering it back to 58 would immediately re-block every
  agent's quickmerge fleet-wide, which is an operator call, not a worker's. RESOLVED 2026-08-09 without needing that
  call — 20 violations were fixed outright, so the ratchet went 76 → 53 (below the pre-raise 58) on a green tree, and
  both baseline defects (absolute paths, silent RAISE) are fixed in both evidence gates. One todo remains: ratchet 53 →
  0.
status: resolved
nature: issue
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm]
scope: [admin]
tags: [quality-gates, ratchet, evidence, plan-hygiene, findings-triage, shipping-blocker]
related:
  [
    /plans/archive/2026_08/issues/ao_round5_apply_session_rulings_untraceable_blocks_quickmerge_2026_08_08.md,
    /plans/active/issues/operator_ruling_record_ao_round5_apply_session_2026_08_08.md,
    /plans/archive/issues/mtds_plan_flip_fabricated_commit_sha_evidence_2026_07_30.md,
  ]
created: 2026-08-09
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P1
assigned_role: admin
drift_direction: advance-docs
resolved_by:
  "76->53 fixed same-day by the filing session; the remaining ratchet-to-0 tail extracted into
  ao_satellite_ao_dispatch_batch13_2026_08_09.md todo 1 for AO dispatch"
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
   `/plans/archive/issues/mtds_plan_flip_fabricated_commit_sha_evidence_2026_07_30.md` and the E-1 precedent, that is
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

- [x] ✅ [SCRIPT] P1. **~~[OPERATOR] Decide the baseline's correct value and the path back to it.~~ RESOLVED BY EVENTS
      2026-08-09 — retagged `[OPERATOR]` → `[SCRIPT]` because the decision became moot before it was ever asked.** The
      three options offered were (a) restore 58 and accept a fleet-wide red, (b) set the measured 74 as an honest floor,
      (c) keep 76 as accepted debt. None was needed: **20 of the violations were fixed outright**, so the baseline
      ratcheted 76 → **53** on a green tree — below the pre-raise 58, i.e. option (a)'s goal reached without option
      (a)'s cost. That is why this is a worker call rather than an operator one: lowering the NUMBER was operator-gated
      (it re-reds every agent), but removing the VIOLATIONS is ordinary work and needs nobody's permission.
      **Evidence**: `unified-trading-pm@<this commit>` — 73 → 53 measured by
      `python3 scripts/quality_gates/check_plan_operator_ruling_evidence.py`, 18 plan docs edited, baseline regenerated
      via `--baseline-write` (never hand-edited). Repo: unified-trading-pm.
- [x] ✅ [SCRIPT] P2. **Make the baseline file host-portable again — DONE 2026-08-09.** `_write_baseline` now stores
      `path` relative to the PM repo root (`_PM_ROOT`) in BOTH evidence gates, and
      `plan_operator_ruling_evidence_baseline.yaml` was regenerated. **Verified**: `grep -c '/Users/'` returns 0 on both
      baselines, so a regeneration from any slot is byte-identical. Repo: unified-trading-pm.
- [x] ✅ [SCRIPT] P2. **Make a RAISE loud rather than silent — DONE 2026-08-09.** Both
      `check_plan_commit_sha_evidence.py` and `check_plan_operator_ruling_evidence.py` now read the previous baseline
      before writing and print `WARNING: <key> RAISED x -> y -- a shrinking ratchet must only go DOWN` to stderr on any
      increase, matching `check_ao_dispatch_visibility_gate.py`'s existing convention. **Verified**: silent on this
      session's legitimate 76 → 53 ratchet-DOWN. Repo: unified-trading-pm.
- [x] ✅ [SCRIPT] P2. **KEEP-NA-STALE, citation-closed 2026-08-09 (na-corpus-hygiene pass).** Keep ratcheting: 53 → 0 —
      content already extracted verbatim into `ao_satellite_ao_dispatch_batch13_2026_08_09.md` todo 1. Tracked there
      going forward, not duplicated here. **CORRECTED 2026-08-12 (/plan-reconcile) — real completion evidence (was a
      bare redirect pointer):** `ao_satellite_ao_dispatch_batch13_2026_08_09.md` todo 1 shipped and was verified by its
      finalize plan (`ao_satellite_ao_dispatch_batch13_finalize_2026_08_09.md`, "Re-verify batch13's done-claim against
      reality" todo): corpus-wide `python3 scripts/quality_gates/check_plan_operator_ruling_evidence.py` →
      `Unsourced operator-ruling citations: 2 (baseline 2)` — matches batch13's claimed final baseline (52→4→2) exactly,
      the ratchet held at 0 new violations, and the 2 residual lines are batch13's own named deliberately-unrecoverable
      citations, not a regression.

## Progress Log

- **2026-08-09 (slot 3, interactive)** — Filed. Found by re-running the gate after hand-fixing 17 of its violations and
  seeing 74 reported against a baseline of 76 — i.e. green. Worth recording the sequence, because it is the mechanism,
  not the intent, that matters here: the corpus went 58 → 69 in a day through several concurrent sessions landing
  unsourced rulings via the pure-doc `safe-doc-push` path (which does not run this gate at all — see
  `/plans/archive/2026_08/issues/ao_round5_apply_session_rulings_untraceable_blocks_quickmerge_2026_08_08.md`), the red
  then surfaced for whichever agent next ran quickmerge, and raising the ceiling was the fastest way for that agent to
  proceed. The precommit-wiring fix shipped alongside this doc closes the door that let the debt accumulate
  unattributed; this doc covers the debt already through it.

- **2026-08-09 (slot 3, interactive) — 76 → 53, and the operator gate dissolved.** Fixed 20 violations by hand rather
  than arguing about the number. Method, because it is reusable: the gate inspects a ±window around the ruling PHRASE
  inside a blank-line-terminated todo block, so "the source is in the todo" is often false — it is in the todo but 400
  chars away, or after a blank line, which the block walk ends on. To see what the gate actually sees I swapped
  `_has_traceable_source` for a recording spy and let the REAL function keep deciding (same parser-is-the-oracle
  technique as the dispatch-visibility report); re-implementing the window arithmetic would have been a second copy to
  drift. Pairing note for anyone reusing it: misses and violations are 1:1 **per file** (the gate breaks on a block's
  first unsourced match), so reset the recorder per file and zip — taking "the last miss" silently mispairs.

  **Three fix classes, and only one of them is "add a citation":**

  1. **Source exists, verified, just outside the window (12).** Cite it AT the phrase. Every one was confirmed to exist
     before it was cited — e.g. `june_2026_vintage_audit_findings_2026_07_27.md` §5-RESOLVED item 35 turned out to name
     the two features-service todos citing it, exactly; the Phase-3/4 clearance genuinely resolves to
     `/plans/archive/issues/codex_ssot_audit_phase3_hold_vs_reclassify_contradiction_2026_07_27.md`, which the todo
     already named 400 chars later.
  2. **Not a citation at all (5) — the interesting class.** The gate fires on "Operator ruling **needed**", "**no**
     operator ruling recorded", "code-verified, **not** an operator ruling", and a quoted code-comment TEMPLATE
     `# ... (operator ruling: ...)`. These claim no authority; several assert its ABSENCE. Reworded to "operator
     decision" so the phrase "operator ruling" keeps meaning an actual ruling. This is not gate-gaming: a doc that says
     a ruling is missing should not read as though it had one.
  3. **A ruling that was never an operator's (1).** `cefi_consolidated_closeout_2026_07_18.md`'s close-out criterion
     said "operator ruling recorded" for a ruling the doc itself labels AUTONOMOUS. Corrected to say so, and to say it
     must not be cited as an operator ruling. This one was a real mislabel, found only because the gate flagged it.

  **Not fixed, deliberately**: the AO state-home ruling (2026-07-18) and the DeFi-volatility removal (2026-07-17) have
  codex docs that DESCRIBE the end state but do not RECORD the ruling. Citing those would have satisfied the gate while
  pointing at a doc that cannot confirm a human decided anything — the failure mode this gate exists to catch, committed
  in the act of clearing it. Left in the 53.

  Fixed both baseline defects while here (portable paths, loud RAISE) — the raise that started this doc would have
  printed a warning under the new code.
