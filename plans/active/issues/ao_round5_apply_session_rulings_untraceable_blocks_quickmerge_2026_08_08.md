---
doc_type: issue
title:
  "5 operator rulings cite an untraceable 'ao round-5 apply session' — quickmerge is blocked repo-wide in
  unified-trading-pm"
summary: >-
  MEASURED 2026-08-08 13:2xZ: check_plan_operator_ruling_evidence.py went 58 -> 63 (baseline 58) after commits landed
  from a live "ao round-5 apply session". The new violations are checked todos citing **"operator ruling 2026-08-08 (ao
  round-5 apply session, item N)"** with a verbatim quoted ruling but NO traceable source doc — `rg` finds no plan,
  issue, or codex doc for that session anywhere in the corpus, only the citing todos themselves. Because
  quality-gates.sh re-gates the WHOLE tree, every agent's `quickmerge.sh` in unified-trading-pm now fails on an
  inherited red, regardless of what they changed. Needs the authoring session (or the operator) to name where those
  rulings are recorded; a third party cannot add the citation without fabricating the evidence the gate exists to catch.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm]
scope: [admin]
tags: [quality-gates, plan-hygiene, operator-ruling, evidence, shipping-blocker, findings-triage]
related:
  [
    /plans/active/issues/mtds_plan_flip_fabricated_commit_sha_evidence_2026_07_30.md,
    /plans/active/issues/ao_silently_non_dispatchable_todos_have_no_visibility_gate_2026_08_08.md,
  ]
created: 2026-08-08
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P1
assigned_role: admin
drift_direction: advance-docs
resolved_by:
locked_by:
source:
  "slot-3 interactive, 2026-08-08 — hit while shipping the AO dispatch-visibility gate; quickmerge re-gate failed on an
  inherited red"
depends_on: []
---

# "ao round-5 apply session" rulings have no traceable source, and the red is fleet-wide

## What happened

While shipping `/plans/active/issues/ao_silently_non_dispatchable_todos_have_no_visibility_gate_2026_08_08.md`'s gate, a
full `bash scripts/quality-gates.sh --no-fix` ran GREEN (exit 0). `quickmerge.sh` then did its STAGE 0.4
`git pull --rebase`, pulled in peer commits, re-gated the resulting tree, and failed:

```
❌ 1 post-gate check(s) FAILED: plan-operator-ruling-evidence
Unsourced operator-ruling citations: 63 (baseline 58).
```

**None of the 63 violations is in any file this session touched** (verified by matching the checker's full violation
list against the 11 edited paths: 0 hits). The +5 arrived with the pull.

## The specific defect

The new violations are checked todos of this shape:

```
(checkbox prefix elided below — see the note after this block)
[x] ✅ 12. [OPERATOR] P3. **Operator ruling 2026-08-08** (ao round-5 apply session, item 2): "Yes, build it." …
[x] ✅ [INFRA] P1. **DECIDED — operator ruling 2026-08-08** (ao round-5 apply session, item 6): "AO-dispatched plan …
```

> The leading `- ` is deliberately stripped from the two examples above. `check_plan_operator_ruling_evidence.py` does
> NOT skip fenced code blocks, so quoting a violating todo verbatim in a doc ABOUT the violation adds two more
> violations — measured live while filing this (63 → 65, both from this file). Worth knowing before citing any todo
> shape in a plan doc; the same fence-blindness bites `check_plan_commit_sha_evidence.py`'s todo scan.

The ruling text is quoted verbatim, so this is very likely a REAL operator decision, not a fabrication. The problem is
that **"ao round-5 apply session" is not a traceable source**: `rg "round-5 apply|ao round-5" plans/` returns only the
citing todos themselves — there is no session doc, no plan, no issue, no codex entry recording those rulings. An
`item N` index into a document nobody can open is exactly the authority-bypass shape
`check_plan_operator_ruling_evidence.py` was built for (see
`/plans/active/issues/mtds_plan_flip_fabricated_commit_sha_evidence_2026_07_30.md`).

Affected docs (at least): `deepseek_flash_ab_routing_test_2026_08_05.md`,
`issues/context_scope_consumption_enforcement_2026_07_30.md`,
`issues/blocked_questions_ux_redesign_context_loss_and_scale_2026_07_24.md`,
`issues/agent_reply_cannot_address_a_different_role_silent_cross_role_blind_spot_2026_07_22.md`,
`ao_satellite_ao_dispatch_batch2_2026_07_30.md`.

## Why it is escalated rather than fixed in place

Three closed doors, which is what makes this operator-gated rather than a normal findings-triage fix:

1. **Cannot re-baseline.** Baselines only go DOWN (CLAUDE.md HARD RULE). Raising 58 → 63 to absorb a peer's regression
   is precisely the ratchet-defeating move that `check_plan_commit_sha_evidence.py`'s own docstring records as the
   failure that made its baseline climb 2 → 4 → 6 → 8 over two days.
2. **Cannot add the citation.** Only the authoring session knows where those rulings are recorded. A third party writing
   a plausible-looking source path would be fabricating completion evidence — the exact failure class the gate exists to
   catch, committed in the act of satisfying it.
3. **Cannot edit around it.** These are another in-flight session's docs; per multi-agent safety, not ours to rewrite.

## Blast radius

`quality-gates.sh` gates the whole tree, and `quickmerge.sh` re-gates before landing. So **every agent trying to ship
ANY change to unified-trading-pm is blocked on this**, not just the session that introduced it — a shared-pipeline
stall, not a local one. Pure-doc pushes via `scripts/dev/safe-doc-push.sh` (prek only) are unaffected.

## Resolution

- [ ] [OPERATOR] P1. **Name where the "ao round-5 apply session" rulings are recorded, or confirm they should be
      re-derived.** If a session doc exists, its path goes into each of the 5 citing todos (within 300 chars of the
      ruling phrase) and the gate clears on its own. If the rulings were only ever spoken in a chat session with no
      durable record, that is itself the finding — the decisions need a home before the todos citing them can claim
      done. Either way the authoring session should make the edit; this doc exists so the blocker is tracked rather than
      absorbed by the next agent to hit it. **Done when**:
      `python3 scripts/quality_gates/check_plan_operator_ruling_evidence.py --workspace-root ..` reports ≤ 58 with the
      baseline untouched. Repo: unified-trading-pm.

## Progress Log

- **2026-08-08 (slot 3, interactive)** — Filed on hitting it mid-ship. Diagnosis is measured, not inferred: the
  session's own full QG passed at exit 0 before the rebase; the checker's complete 63-entry violation list contains zero
  of this session's 11 edited paths; and `rg` confirms the cited session has no doc anywhere in `plans/`. Deliberately
  NOT re-baselined and NOT hand-patched, for the three reasons in the section above.
