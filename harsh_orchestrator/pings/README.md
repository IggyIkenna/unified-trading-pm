# Per-slot ping ledgers (Harsh side)

**Why per-slot files?** `_agent_pings.md` was a single file every spawned slot appended to → the highest-frequency
rebase-conflict source under the direct-to-`live-defi-rollout` merge model. Since slot 1 (the orchestrator) is the
**only reader**, there's no reason to share it. Each spawned slot `N` writes ONLY `slot_<N>.md` — its commits never
touch another slot's ping file → zero collision on the ping surface.

## Files

- `slot_2.md` … `slot_<N>.md` — one append-only activity log per spawned slot (STARTED ack / blocker pointer / status /
  DONE announcement). Slot 1 polls `harsh_orchestrator/pings/*.md` every ~1 min while the operator is active.
- (Slot 1 = orchestrator; it has no ping file — it reads, it doesn't ping itself.)

## Line format (use `date -u` — this machine's clock is IST, NOT UTC)

```text
[YYYY-MM-DD HH:MM UTC] <agent-tag> — <one-liner with plan-doc pointer>
```

Examples:

```text
[2026-05-11 06:05 UTC] harsh-features-consolidation-tab — STARTED slot 2 (plans/active/features_repo_consolidation_2026_05_08.md)
[2026-05-11 09:20 UTC] harsh-features-consolidation-tab — 🟡 BLOCKED on UAC FeatureFamily collision; see features_repo_consolidation_2026_05_08.md § Open questions Q1
[2026-05-11 14:10 UTC] harsh-features-consolidation-tab — DONE Phase 4 (features-service@<sha> + PM@<sha> plan-flip); continuing Phase 5
```

## Lifecycle

- **Spawned slot** appends a line per shippable-unit / boot / blocker / done, then commits + conditional-pushes it as
  part of its normal cadence (it's a tiny diff, never collides because it's the slot's own file).
- **Slot 1** reads `pings/*.md` each poll. For a blocker line → goes to the plan-of-record `## Open questions`, writes
  A1 (escalating to operator if needed). For STARTED → flips the LEDGER registry slot entry to 🟢 IN FLIGHT. For DONE →
  verifies the done-definition + flips to ✅ DONE. Slot 1 does NOT edit the per-slot ping files (avoids a slot-1-vs-slot-N
  race) — they're each slot's own append-only log; slot 1 tracks "handled up to line X" in its own working context.
- **Daily reset**: slot 1 archives the prior day's `slot_<N>.md` contents into the LEDGER historical log (or just
  truncates with a date marker) and the new cycle's slots start fresh.

## Transition note (2026-05-11)

`harsh_orchestrator/_agent_pings.md` is being retired in favour of this dir. Slots already running on 2026-05-11
(2/3/4/6) were spawned with prompts pointing at the old `_agent_pings.md`, so they keep writing there for this cycle;
slot 1 reads BOTH `pings/*.md` and `_agent_pings.md` during the transition. Slots spawned from 2026-05-11 onward (and
all re-spawns) use `pings/slot_<N>.md`. Once this cycle's slots finish, `_agent_pings.md` becomes the redirect stub
only.

## Cross-side pings

Cross-side (Ikenna ↔ Harsh) hard-gate signalling stays in the shared `plans/active/_agent_pings.md` — that one is
low-traffic (<5 active entries normally) so a single shared file is fine there. Per CLAUDE.md "Daily Work-Split Process"
§ "Ping ledger bifurcation".

## Bidirectional comms (codified 2026-05-11)

The per-slot file is **two-way**. Beyond the slot's own STARTED/blocker/DONE/status lines, **slot 1 (main) may append
`[main → slot N]` messages here** — acks, scope changes ("re-read work-split § Slot N — your scope grew"), pointers
("Q1 answered in <plan> § Open questions — proceed with X"), short directives. So this file is the lightweight
bidirectional comm doc between main and the slot; substantive Q→A still uses the slot's plan-of-record `## Open
questions` (Q from slot → A1 from main) — `slot_<N>.md` just carries the *pointer* to the A1.

**The slot's read loop**: after each shippable-unit push you do `git fetch origin live-defi-rollout && git rebase
origin/live-defi-rollout` anyway (per the conditional-push merge model). When you do — **re-read your `slot_<N>.md` for
new `[main → slot N]` messages + your plan-of-record `## Open questions` for new A1s.** That's how main reaches you
without going through the operator. The operator may also nudge you ("take a pull, main has a message in your slot
file") — same thing, just a hint.

**Collision note**: main appending `[main → slot N]` lines + the slot appending its own lines = an append-section
conflict on a flat list IF you push within the same few-second window — trivially resolved "keep both" per the
plan-aware-merge protocol. Much smaller than the old every-slot-on-one-file collision; acceptable. (If it ever gets
noisy, split this file into a `## Pings from slot <N>` section + a `## Messages from main` section so the appends never
overlap — not needed yet.)

**Pull-safety under per-tab worktrees**: `git pull --rebase` / `git rebase origin/live-defi-rollout` from inside your
slot worktree only affects YOUR worktree — it can't auto-stash another slot's WIP (the old shared-tree foot-gun is
unrepresentable). The only thing to watch: don't rebase mid-edit with uncommitted WIP — commit first (you do this per
shippable unit anyway), then rebase, then read your messages. Worst case is a trivial rebase conflict you resolve via
the plan-aware-merge protocol.
