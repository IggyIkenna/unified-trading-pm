# Harsh main-orchestrator polling instructions

> Loaded each `/loop` fire to keep the chat-visible `/loop` text small (just
> `/loop poll harsh slots — see poll_main_prompt.md`). The full polling logic + sub-agent prompt template live here so
> the chat panel stays readable.

## Per-cycle main-orchestrator workflow

1. **Spawn ONE sub-agent** (general-purpose, sonnet) with the prompt below. Get ≤150-word summary back, then act:
   - Slot queue exhausted → refill from master plan inventory residuals (plans at 80%+ in active plan inventory).
   - Slot stuck >20 min no commit → drop ping in `slot_N.md` OR cross-side via `_agent_pings.md`.
   - Big finding → escalate to operator (text reply, not just ledger).
   - Slot silent 2+ cycles after a direct-dispatch ping → format the dispatch with explicit recipe + "if you can read
     this, ack within 10 min" (the pattern that recovered slots 2/3/6/9 earlier today).
   - **Known-benign list (do not re-flag)**:
     - Dual-flip false-positive: REFINED audit only flags items that EXPLICITLY name a `plans/active/*.md` path AND
       don't touch it. Code-only / codex-only items are EXEMPT.
     - utl_qg_failures_2026_05_15.md issue doc is RESOLVED (slot 6 shipped fix UTL@d3488b7 + UTL@30db050 today).
     - Slots 4 + 9 silent-working historically (commits in owned repos, no PM ping). Verify via owned-repo activity
       check before flagging.
   - B-015 VM monitored by dedicated agent — main does NOT poll the VM.

### Slot-retire audit (mandatory when a slot stops)

When a slot declares QUEUE EXHAUSTED, is stopped by operator, or has been silent ≥3 cycles after direct-dispatch nudges,
run an end-of-shift audit before considering the slot retired:

1. **Work-volume**: commits today, items flipped per work_split § Slot N, plans touched.
2. **Dual-flip compliance** (refined audit): every flip commit must touch the underlying plan-of-record (when the
   work_split item names a `plans/active/*.md` path). Code-only and codex-only items are exempt.
3. **Tab worktree state per repo** in `.tabs/N/<repo>/`:
   - `git status --short` — any uncommitted files?
   - `git rev-list --left-right --count HEAD...origin/live-defi-rollout` — how far behind LDR?
   - **Ruff formatting changes** are NOT to be discarded — they are part of git CI (pre-commit hooks + quality-gates).
     If a tab worktree has uncommitted ruff format changes: a. Verify they're scoped to slot N's owned repos. b. Stage +
     commit + push as `chore(format): apply ruff format` (or include in the next functional commit if grouped with
     related work). c. Do NOT discard via `git restore` / `git checkout` — that loses CI-required formatting.
4. **Off-scope incidents**: did the slot touch foreign ping files, Ikenna-owned plans (`code_freeze_*`, `cefi_master_*`,
   `tradfi_master_*`, `manifest_evolution_master_*`), UAC enum changes, or post-cutover plans? Log any in the slot's
   audit summary.
5. **Verdict**: healthy / minor concerns / scope drift detected.
6. **Recommended commits before retire**: list any uncommitted files worth committing (especially ruff formatting per #3
   above). Main-orchestrator commits them directly if slot N's tab agent is stopped.

Audit output goes to the operator (text reply). Update slot N's ping file with the audit verdict + final SHA tally.

2. **After acting**, ScheduleWakeup for next fire:
   - default 240s (4 min — slightly past cache window, but only ~1 cache miss per cycle)
   - 60-120s if blocker triage active
   - 600s if all slots actively shipping + plenty of queue depth
   - prompt: `/loop Poll harsh slot work — see poll_main_prompt.md` (this exact short string; do NOT inline the verbose
     spec)

## Sub-agent prompt template (paste verbatim each cycle)

```
You are a polling sub-agent. 2026-05-18 harsh-side. Read-only.

1. cd /home/hk/unified-trading-system-repos/unified-trading-pm && git fetch origin live-defi-rollout 2>&1 | tail -3
2. git log origin/live-defi-rollout --oneline --since='10 minutes ago' (count + per-slot flips)
3. Per-slot ping tail from ORIGIN: for s in 2 3 4 5 6 7 8 9; do echo === slot $s ===; git show origin/live-defi-rollout:harsh_orchestrator/pings/slot_$s.md | tail -3; done
4. Unchecked count: git show origin/live-defi-rollout:plans/active/work_split_2026_05_18_harsh.md | awk '/^### Slot ([0-9])/{slot=$3} /^- \[ \]/{count[slot]++} END{for (s in count) print "slot" s ": " count[s]}'
5. Owned-repo activity check for any silent-working slot: for r in <owned-repos>; do echo === $r ===; (cd /home/hk/unified-trading-system-repos/$r 2>/dev/null && git log origin/live-defi-rollout --oneline --since='2026-05-18 13:00 UTC' 2>&1 | head -3); done
6. REFINED dual-flip audit (per operator direction): for each flip commit in recent window:
   (a) git show <sha> --pretty=%B | head -3 — identify item number
   (b) Read item text in work_split — does it name a `plans/active/*.md` path?
   (c) If YES (PoR named) AND commit doesn't touch that path → NON-COMPLIANT
   (d) If NO (code-only / codex-only item) → EXEMPT, do not count

Return ≤150 words structured as:
- Active+shipping (last 8-10 min): [slot Ns + commit count]
- Idle-with-queue (notified, no commits): [list]
- Truly exhausted (0 unchecked): [list]
- Refined dual-flip: [N/M scored; X exempt]
- NEW big findings (skip known-benign): [list]
- Recommended next delay: [180 / 240 / 600 seconds]
- Recommended actions for main: [≤3 bullets]
```

## Known slot ownership map (for owned-repo activity check)

- Slot 2 — execution-service lint surface + workspace audit
- Slot 3 — strategy-service + codex
- Slot 4 — system-integration-tests + alerting-service + batch-live-reconciliation-service + features-service tests
- Slot 5 — execution-service Phase 9 + risk-and-exposure-service + pnl-attribution-service
- Slot 6 — strategy-service codex + sit + UTL bash + codex/06
- Slot 7 — deployment-api + deployment-ui (SOLE owner)
- Slot 8 — cross-repo audit + UTL HMAC + workspace-constraints
- Slot 9 — market-tick-data-service + position-balance-monitor-service + market-data-processing-service

## Direct-dispatch recipe template (for recovering stalled slots)

When a slot has been silent 2+ cycles after ping nudges, drop a direct-dispatch ping with this shape (proven to recover
slots 2/3/6/9 earlier today):

```
[YYYY-MM-DD HH:MM UTC] [main → slot N] — 🟢 **DIRECT DISPATCH** — <state observation>. Direct task: **item X — <theme>**. Recipe:
  1. `cd /home/hk/unified-trading-system-repos/unified-trading-pm`
  2. `git pull --rebase origin live-defi-rollout` (if behind)
  3. <specific 1-2 line action>
  4. Ship + commit + dual-flip work_split slot N item X + plan-of-record.
**If you can read this ping, you are still active.** Acknowledge "STARTED item X" within 10 min.
```
