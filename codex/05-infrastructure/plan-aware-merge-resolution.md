---
title: "Plan-aware merge resolution — slot master reconciliation protocol"
scope: [engineer]
status: active
last_updated: 2026-05-10
owner: ikenna
related_plans:
  - plans/active/per_agent_worktrees_2026_05_10.md
related_codex:
  - codex/05-infrastructure/per-tab-worktrees.md
  - ../../cursor-configs/CLAUDE.md
last_reviewed: 2026-05-17
---

# Plan-aware merge resolution — slot master reconciliation protocol

**TL;DR.** When a slot master rebases its slot branch onto `origin/live-defi-rollout` per shippable unit and finds
conflicts, this protocol classifies conflict shape + auto-resolves trivial ones + escalates semantic conflicts to the
operator with plan-context reasoning. PM repo is the always-touched surface, so most conflicts surface in
`plans/active/` files — and most of those resolve via append-union without operator input.

## Why this protocol exists

Under the per-slot worktree model (see [`per-tab-worktrees.md`](per-tab-worktrees.md)):

- Each slot pushes to its slot branch `tab/<operator>/<N>` per shippable unit.
- Merge into `origin/live-defi-rollout` happens via rebase + fast-forward push.
- Multiple slots ship to PM in parallel (plan flips, codex updates, issue docs) — conflicts are **expected**, not
  exceptional.

Without a protocol, every conflict becomes an operator interruption ("how should I resolve this PM merge conflict?").
With a protocol, ~80% of conflicts auto-resolve. The remaining 20% reach the operator with a 5-line escalation summary
instead of "there's a conflict here, what do?"

## The reconciliation step (per shippable unit)

```bash
# Slot master, after committing its shippable unit on tab/<operator>/<N>:
bash unified-trading-pm/scripts/dev/slot-master-rebase.sh
# OR, equivalently:
git fetch origin live-defi-rollout
git rebase origin/live-defi-rollout                  # apply protocol on conflict
git push origin tab/<operator>/<N>                   # push slot branch
# (Merge to live-defi-rollout via fast-forward — separate shippable-unit step.)
```

The helper script (`slot-master-rebase.sh`) wraps the rebase + emits machine-readable conflict reports the slot master
agent can parse + reason about.

## The 4-step protocol on conflict

1. **Read the incoming commit.** `git log -1 origin/live-defi-rollout` — author slot tag, commit message, plan reference
   if any (`docs(plans):` commits cite the plan they flipped).
2. **Read the affected file's plan-of-record context.** For PM/plan conflicts: which plan does the conflicting section
   belong to? What stage of execution? Cross-reference against your own slot's plan-of-record.
3. **Classify conflict shape** (closed set — see below).
4. **Auto-resolve OR escalate** per shape. Resolution commit message includes the slot SHAs + plan-context reasoning.

## Closed conflict-shape taxonomy

### Shape A — append-section conflict (auto-resolve via union)

Two slots both appended to the same plan section / DONE block / `## Open questions` / scoreboard table — but at
different positions, with no overlapping content. Most common shape for PM conflicts.

**Detection.** Both sides add lines; no line is modified on both sides.

**Resolution.** Union: keep both sides' additions, in chronological order by commit timestamp. The slot master writes a
resolution commit with message:

```
docs(plans): rebase tab/<op>/<N> on live-defi-rollout — append-union merge

Incoming:  <sha>  <one-line>  (slot <other-N>'s appended <section>)
Local:     <sha>  <one-line>  (slot <my-N>'s appended <section>)
Resolution: union — both additions kept; chronological order by commit timestamp.
```

### Shape B — checkbox-flip collision (auto-resolve via later flip + dual evidence)

Two slots both flipped the same `- [ ] [SCRIPT] P0. ...` to `- [x]` with different evidence lines. Both did genuine
work, both deserve credit, but the checkbox is shared state.

**Detection.** Both sides change the checkbox line, both produce `- [x]` (same state outcome), evidence lines differ.

**Resolution.** Keep `- [x]`. Append BOTH evidence lines, separated by `+`. Example:

```markdown
- [x] [SCRIPT] P0. Ship UTL helper foo() (UTL@abc123 from slot 3 + UTL@def456 from slot 5 — bundled QG, both green)
```

Resolution commit cites both SHAs in the message.

### Shape C — paragraph-rewrite collision (ESCALATE to operator)

Two slots both modified the SAME paragraph (or codex SSOT section, or contract definition, or `## Why this exists`
prose) with **incompatible content**. Each side made a non-mechanical edit; neither is purely additive.

**Detection.** Same line-range modified on both sides; diffs are not strict subsets of each other.

**Resolution.** STOP the rebase. Write a 5-line escalation to the operator + the plan-of-record's `## Open questions`
section. Standard format:

```
## Open questions

### Q<N> — [slot-<my-N>-<theme>, YYYY-MM-DD HH:MM UTC] — paragraph-rewrite conflict in <file>:<line-range>

**Status**: 🟡 BLOCKED — waiting for resolution

Incoming commit: <sha> — <one-line> (slot <other-N>-<other-theme>)
Local commit:    <sha> — <one-line> (slot <my-N>-<my-theme>)
Conflict shape:  paragraph-rewrite at <file>:<line-range>
Their version:   "<one-sentence summary>"
My version:      "<one-sentence summary>"
Recommendation:  <my version | their version | merge of both | revert and re-plan> because <plan-context reason>
ASK:             confirm recommendation or redirect.
```

Append a 1-line ping to `_agent_pings.md`. Continue with anything else the slot can do; resume after operator answers.

### Shape D — code-conflict (UAC / UTL / services — usually semantic; ESCALATE unless purely mechanical)

Two slots modified the SAME Python file. Could be:

- **Mechanical**: both renamed a symbol, both added a docstring section, both fixed the same ruff rule — auto-resolve
  via re-application.
- **Semantic**: two contract definitions diverge, two helper signatures conflict, two service consumers wire the same
  upstream differently — escalate.

**Detection.** Same-file conflict with overlapping line ranges in Python source.

**Resolution heuristic.** If both diffs are pure additions to disjoint regions of the same function/class → union
auto-resolve. If both diffs modify shared lines → escalate Shape C-style.

For code conflicts, the escalation message cites both the consumer plan AND the upstream contract change (e.g. "slot 3
added `EmissionDecision.is_published` per writegate Phase 4; slot 5 added `EmissionDecision.severity` per alerting plan
Phase 2 — both extend the same frozen dataclass; need contract decision on combined shape").

## What "plan-aware" means concretely

The slot master has full local context from its own work:

- The plan-of-record it's executing against (every section it has read this session).
- Its own shippable units (every commit it's pushed today).
- The sub-agents' outputs (every fan-out result it has reconciled).

When it sees an incoming commit's plan reference (every PM commit on `live-defi-rollout` uses `docs(plans):` per the
workspace convention), it cross-references:

1. **Is the incoming plan related to my slot's plan?** (Same domain master? Same epic? Shared codex SSOT?)
2. **Is the incoming author the same operator?** (Cross-side Harsh → Ikenna or vice versa is hard-gate territory.)
3. **Does the workspace SSOT (CLAUDE.md / codex) name the canonical answer?** (Plan-filename convention is in CLAUDE.md;
   "live = batch" principle is in CLAUDE.md; etc.)

Plan-context recommendation = the slot master picks the resolution that aligns with workspace SSOT + the master's own
plan's stated direction. The operator confirms or redirects in one line.

## Anti-patterns

- **Don't auto-resolve a Shape C conflict.** Paragraph-rewrite conflicts are by definition semantic; auto-resolving by
  "later commit wins" or "longer commit wins" loses real work. Escalate.
- **Don't escalate Shape A conflicts.** Append-union is mechanical; operators don't need to be in the loop for "both
  slots flipped different checkboxes, keep both."
- **Don't push the slot branch without resolving conflicts.** A force-push to `tab/<op>/<N>` with conflict markers in
  files breaks the slot's history. Rebase, resolve, then push.
- **Don't bypass via `git merge -X theirs/ours`.** That's auto-pick-one-side, not plan-aware. Use the protocol.
- **Don't escalate without the 5-line summary.** "There's a conflict" wastes operator time. The summary IS the
  escalation — operator answers in one line.

## Composes with

- [`per-tab-worktrees.md`](per-tab-worktrees.md) — the slot model this protocol runs inside.
- `cursor-configs/CLAUDE.md` § "Commit + Push + Flip Plan Checkboxes" — the per-shippable-unit cadence that triggers
  this protocol.
- `cursor-configs/CLAUDE.md` § "Findings Triage Discipline" — when a conflict surfaces a real finding (not just a
  reconciliation), case-1-to-5 routing applies.
- `cursor-configs/CLAUDE.md` § "Daily Work-Split Process" § "Plan-of-record + Q&A bus" — the `## Open questions` section
  format used for Shape C/D escalations.

## References

- Plan: [`plans/active/per_agent_worktrees_2026_05_10.md`](../../plans/archive/per_agent_worktrees_2026_05_10.md) Phase
  3
- Helper script: [`scripts/dev/slot-master-rebase.sh`](../../scripts/dev/slot-master-rebase.sh)
- Sibling SSOT: [`per-tab-worktrees.md`](per-tab-worktrees.md)
