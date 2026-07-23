---
name: pre-compact
description:
  Make the session's work durable BEFORE context is lost — audit what exists only in context or in the scratchpad,
  promote/commit anything the repo needs, convert deferred discoveries from prose into tracked `- [ ]` plan todos, write
  a `## Deferred work after <date>` table, and push until `ahead=0`. Ends with an explicit VERDICT on whether it is safe
  to compact. Trigger on `/pre-compact`, "I'm about to compact", "update the plans so we don't lose anything", "context
  is high, write down anything important", "save the context", "checkpoint before compacting", "session end — write it
  up", "anything you want to write before I compact", or before any handoff/session end.
---

# /pre-compact — make it durable before the context goes

Compaction and session-end silently destroy three things: (1) findings that were only ever said in chat, (2) files in
the scratchpad — **including ones your committed docs now point at**, and (3) the hard-won "don't do that again" lessons
that cost real time to learn. This skill is the ritual that saves them.

**The bar is not "I wrote a summary." It is: a fresh session with ZERO memory of this one can pick the work up from the
repo alone and not redo anything.** Write for that reader.

## Cardinal rule

**Durable = committed AND pushed.** Not "in the plan file on disk", not "in my summary", not in `memory/` (banned for
agents, per-cwd, never reaches a teammate or VM). If `git rev-list --count origin/<branch>..HEAD` is not `0`, you are
not done.

---

## Modes

- **Interactive (default, operator present)**: run Steps 1–8 as written; Step 3's "big finding, notify the operator"
  cases and the final Step 8 verdict go directly into the chat response — the operator is right there to read them.
- **Autonomous / AO-dispatched** (mid-loop under `/autonomous`, or a background AO worker about to compact): there is no
  chat to relay into, so every operator-facing output becomes a WRITE, not a message. Step 3's "big finding, notify the
  operator" cases MUST land in `plans/active/issues/<slug>_<date>.md` as a `BLOCKED-OPERATOR-DECISION` entry with
  options + recommendation (SUB_AGENT_MANDATORY_RULES escalation format) — never silently deferred, since a run that
  hides its own findings from the very ritual meant to prevent loss defeats the point. Step 8's verdict goes into the
  plan's Progress Log (this ritual's output IS the autonomous loop's rule-6 journal entry for this tick — they are the
  same artifact, not two separate write-ups). **ASK > PARK still applies**: if the operator is actually present and
  reachable in this session despite an `/autonomous` flag, ask directly instead of parking — the flag means "don't block
  on them," not "they're gone."
- **Never weakened by either mode**: the Cardinal Rule (durable = committed AND pushed) and Step 7's verification
  (`git rev-list --count` MUST be 0) apply identically — there is no autonomous shortcut that skips actually pushing.

## Step 1 — Audit for loss. Do this FIRST; it is the step people skip.

Ask, and actually check, not from memory:

1. **`git status`** — anything uncommitted? Untracked files you created?
2. **Scratchpad sweep** — `ls -la <scratchpad>`. For each file: is it (a) referenced by something committed, (b) needed
   by an OPEN todo, or (c) expensive to recreate? Any yes ⇒ **promote it** (Step 2). Everything else is fine to lose —
   say so explicitly rather than promoting noise.
3. **Dangling references** — the highest-value check: `grep -rn 'scratchpad\|/tmp/' plans/ codex/ docs/ 2>/dev/null`.
   **A committed doc pointing at a scratchpad path is a broken doc the moment this session ends.** Fix the reference or
   promote the target.
4. **Chat-only findings** — did you discover, decide, recommend, or measure something that exists nowhere on disk?
5. **Secrets** — any token-shaped file in the scratchpad? Destroy it (`shred -u`), and say so.

## Step 2 — Promote what the repo needs

If a tool/script earned its keep, give it a home. Do NOT dump it as-is:

- Correct home (`scripts/<area>/`), lifecycle marker (`# Epic:` / `# Lifecycle:` / `# Delete-when:`) — the workspace
  requires it on every `scripts/` file.
- A **"why this exists"** header, and the **traps you hit** getting it right. A tool whose lessons died with the session
  will have those lessons re-learned by the next person.
- Validate: `bash -n` / `shellcheck` / it actually runs.
- **Beware the "one-off" label.** If an OPEN todo needs the tool, it is not a one-off. If its ANSWER CHANGES over time
  (live state, moving targets), the operator must re-run it — so it must exist, and its doc must say "re-run this; the
  number has a date on it."

## Step 3 — Discoveries become TODOS, not prose

**Workspace HARD RULE: every deferral mentioned in a summary must already exist as a `- [ ]` todo.** A finding in a
Progress Log is a story; a `- [ ]` is tracked work. Convert:

- `- [ ] [TAG] P0-P3. **Title** — what, why, evidence/provenance, and the SSOT/issue-doc link.`
- Findings outside every plan ⇒ `plans/active/issues/<slug>_<date>.md` (big/cross-repo/SSOT-contradiction ⇒ **also
  notify the operator**).
- Record **who owns it** if it is not you (operator-deferred, another person) so nobody duplicates the work.

## Step 4 — Flip what actually landed

Per the commit+push+flip rule: anything shipped this session gets its checkbox flipped **with evidence** —
`N. ✅ [item] — <repo>@<sha> + evidence` — and a `docs(plans):` commit. Do not leave a shipped item unticked; that is
the #1 source of false progress and the next session will redo it.

## Step 5 — The `## Deferred work after <date>` table

Required for any non-final multi-item session. The value is **not** the list — it is separating the kinds of "not done",
because they need different responses:

| Kind                   | Meaning                                                                 |
| ---------------------- | ----------------------------------------------------------------------- |
| **Not done**           | blocked on nobody — real work, pick it up                               |
| **Cannot be done yet** | needs elapsed time / real infra / an external event — NOT work, waiting |
| **Operator-owned**     | a human decision or action — do not start it                            |

Columns: item · state/why deferred · blocked-on. **Name the recommended NEXT item and why**, so the next session does
not re-derive the priority order.

## Step 6 — Carry the lessons, not just the state

The part everyone drops. Write down what would otherwise be re-learned the hard way:

- **Measurement traps** you hit ("this API under-reports", "that flag doesn't exist", "the tool answered a different
  question than I asked").
- **Corrections to your own earlier claims** — if you overclaimed and fixed it, say so, or the wrong number survives in
  someone's head.
- **Invariants** discovered ("X is the real guarantee, not Y").
- **Rejected approaches + why** — stops the next session re-walking a dead end.

## Step 7 — Ship and VERIFY

Pre-commit is MANDATORY: `git status && git diff --cached --stat` with **no path arg**; `git restore --staged` anything
not yours; stage **by name**, never `git add .` / `-A`. Push. Then **prove it**:

```bash
git rev-list --count origin/<branch>..HEAD    # MUST be 0
git status --porcelain                        # MUST be empty (or knowingly-ignored)
```

Behind remote ⇒ `git pull --rebase --autostash`. Rejected push ⇒ rebase and retry; **never force-push a shared branch**.

## Step 8 — Give the verdict

End with a short, plain report:

- **Safe to compact: YES/NO** + the pushed SHA(s) and `ahead=0`.
- **What was at risk and is now saved** — lead with anything that would genuinely have been lost (a dangling doc
  reference, a destroyed credential, a tool with no home). If nothing was at risk, say that plainly; do not manufacture
  drama.
- **What is deliberately NOT saved** and why (regenerable artefacts).
- **Where to resume**, in one line.

---

## Anti-patterns

- **"I'll just summarise it in chat."** The summary dies with the context. Only the repo survives.
- **Promoting everything.** Regenerable exports and dead harnesses are noise. Name them as deliberate drops.
- **Ticking a box without evidence.** A `- [x]` with no sha/log is a lie the next session inherits.
- **`git add -A` under time pressure.** You will commit another slot's WIP.
- **Stopping at "committed".** Unpushed is unsaved — other slots and VMs cannot see it.
- **Calling a tool "one-off" to avoid the work of giving it a home.** If a todo needs it, it is not one-off.

## Provenance

Extracted from the ritual run repeatedly during `github_actions_ci_cost_reduction_2026_07_15` (2026-07-17), where the
audit caught a committed issue doc pointing at a scratchpad path that was about to vanish, and (in an earlier session) a
live `github_pat_` sitting in `/tmp`. Both were found by Step 1, not by remembering.
