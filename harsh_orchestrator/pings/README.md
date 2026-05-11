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
