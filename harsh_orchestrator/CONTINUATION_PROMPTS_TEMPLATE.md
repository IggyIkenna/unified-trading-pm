---
title: Per-slot multi-item continuation prompts (Harsh side)
type: orchestration-template
status: active
locked_by: live-defi-rollout
locked_since: 2026-05-14
---

# Continuation Prompts — Lever 1 (autonomous slot pivoting)

> **Goal**: each slot gets its full session backlog up-front. Slot pivots to next item on DONE without waiting for main dispatch. Main intervenes only for BLOCKED / cross-side / EOD.
>
> **Pattern borrowed from**: [`ikenna_orchestrator/`](../ikenna_orchestrator/) — see e.g. `plans/active/continuation_prompts_2026_05_12.md`.
> **Mirror doc**: this is a Harsh-side adaptation. Ikenna runs Model A (fixed thematic cycles); we run hybrid (Model B with pre-loaded queues per cycle).
>
> **Companion docs**:
> - [`THEMATIC_CLUSTERS.md`](THEMATIC_CLUSTERS.md) — stable per-slot specialization map (which repos / theme tags each slot owns across cycles). This per-cycle template draws from those stable themes.
> - [`../scripts/agents/harsh_auto_poll.sh`](../scripts/agents/harsh_auto_poll.sh) — Lever 2 auto-poller that handles mechanical orchestrator work between operator polls.

---

## When to use this doc

Each cycle (typically a half-day or full-day session), main orchestrator (slot 1) writes a fresh `plans/active/continuation_prompts_harsh_<YYYY_MM_DD>.md` from this template **before spawning slot agents**.

- **One section per slot** (slot 2-9; slot 1 = main)
- **3-5 items per slot** in priority order
- **"Scope extension reserve"** at the end of each section (items to pull if slot finishes early)
- **Auto-pivot rule** at the top — slot ships item 1, marks DONE, ships item 2, …
- **Escalation rules** — when to drop BLOCKED ping vs continue

After writing, main reduces polling cadence from "every 3 min" to "every 10-15 min" — slots run autonomously between checks.

---

## Per-slot section template

```markdown
### Slot N — <primary theme>

> **Auto-pivot rule**: ship items in order. After each item, append a DONE ping with SHA(s) to `harsh_orchestrator/pings/slot_N.md`, then START the next item without waiting for main dispatch. Main reads pings on cadence — no acknowledgment delay.
>
> **Stop conditions** (these need main, drop BLOCKED ping + stand by):
> 1. Cross-side handshake required (Ikenna ACK on UAC change, etc.)
> 2. Ambiguous design decision (when fix could go either way)
> 3. Foreign-file collision (untracked or unfamiliar files in your scope)
> 4. Plan-of-record says "AWAITING USER DIRECTION"
>
> **Owned repos**: `<list>`
> **Model tier**: `sonnet-doable / opus-required` · **Thinking**: `medium / high / max`

#### Item 1 (P0) — <title>
- **Task**: <one-sentence description>
- **Done-def**: <objective measurable criterion — QG green, X tests pass, plan checkbox flipped, SHA in DONE ping>
- **Est**: <wall-clock per slot>
- **Plan-ref**: `<plan file + section>`
- **Notes**: <coordination flags, e.g. "slot M also touches repo X; serialise commits">

#### Item 2 (P0) — <title>
[same shape]

#### Item 3 (P1) — <title>
[same shape]

#### SCOPE EXTENSION reserve (pull if early)
- (R1) <title> — <est> — <plan-ref>
- (R2) <title> — <est> — <plan-ref>

#### Item N — Final wave only
- **Trigger**: only start after items 1-3 DONE AND <prereq>
- [same shape]
```

---

## Worked example — slot 5 (2026-05-15 cycle, hypothetical)

### Slot 5 — Phase 8.A coverage continuation + Phase 3 TradFi migration follow-on

> **Auto-pivot rule**: ship items 1 → 2 → 3 sequentially. DONE ping after each. Do NOT wait for main between items.
> **Stop conditions**: (1) cross-side handshake; (2) ambiguous; (3) foreign-file; (4) plan says AWAITING.
> **Owned repos**: `risk-and-exposure-service` + `execution-service` + `instruments-service` + `unified-trading-pm`
> **Model tier**: sonnet-doable · **Thinking**: medium

#### Item 1 (P0) — Verify B-009 coverage held after B-014 rollout
- **Task**: `bash scripts/quality-gates.sh` in risk-and-exposure + execution. Confirm B-009 tests (CIRCUIT_BREAKER_OPEN, KILL_SWITCH_AUTO_DEACTIVATED) still pass after slot 8's STEP X.N1/X.N2/X.N3 enabled in base-service.sh.
- **Done-def**: QG green both repos; no new failures attributable to ratchet enable.
- **Est**: 30 min
- **Plan-ref**: `deployment_and_qg_strategy_implementation_2026_05_13.md` § Phase 8.B kill-switch
- **Notes**: if NEW failure appears, file P1 issue doc — do not patch silently.

#### Item 2 (P0) — Phase 3 TradFi migration consumer cascade
- **Task**: Run `instruments-service/scripts/migrate_tradfi_expiry_schema.py` against staging GCS; verify backfilled parquets have `expiration` field populated for all legacy CanonicalFuturesContract records.
- **Done-def**: 100% of legacy records have `expiration` set; migration audit log committed to `plans/active/issues/tradfi_migration_audit_2026_05_15.md`; QG green.
- **Est**: 1h
- **Plan-ref**: `tradfi_canonical_futures_contract_hard_required_fields_2026_05_13.md` § Phase 4
- **Notes**: coordinate with Ikenna slot 5 on shared TradFi master; cross-ping if conflict.

#### Item 3 (P1) — risk-and-exposure-service coverage sweep (B-009 follow-on)
- **Task**: Identify any uncovered branches in CIRCUIT_BREAKER state-machine (idempotent disarm, re-arm race conditions). Add 2-3 edge-case tests.
- **Done-def**: QG coverage ≥ 87.7% (existing baseline); plan checkbox flipped.
- **Est**: 1h

#### SCOPE EXTENSION reserve (pull if items 1-3 finish early)
- (R1) Codex audit on B-009 work — verify codex/04-architecture/kill-switch-and-circuit-breaker.md is current — 30 min
- (R2) deployment-service kill-switch arming docs review — 30 min — `plans/active/deployment_and_qg_strategy_implementation_2026_05_13.md`

---

## Mechanical autopilot — Lever 2 hookup

The auto-poller [`scripts/agents/harsh_auto_poll.sh`](../scripts/agents/harsh_auto_poll.sh) runs every ~3 min (cron or `--watch` mode) and handles mechanical work without invoking main:

- New STARTED ping detected → flips LEDGER slot row from 🟡 AWAITING → 🟢 IN FLIGHT, commits + pushes
- DONE / BLOCKED / BIG-finding ping detected → appends to `harsh_orchestrator/auto_poll_log/operator_alerts.log` for next main wake-up
- New cross-side ping (Ikenna → Harsh) → appends to operator alerts log
- FF-only pull (won't auto-rebase if local diverges — leaves for human triage)
- Exit codes: 0 = clean, 1 = mechanical edits applied, 2 = needs main, 3 = error

Usage:
```bash
bash scripts/agents/harsh_auto_poll.sh             # one-shot
bash scripts/agents/harsh_auto_poll.sh --watch     # loop every 3 min
bash scripts/agents/harsh_auto_poll.sh --dry-run   # preview without writing
```

Main is summoned only when the alert log is non-empty. **Operator no longer needs to manually trigger orchestrator polls** unless they want a status check.

---

## Migration to Model A (Lever 3) — readiness criteria

Pivot to fixed thematic 8-slot clustering (like Ikenna) when:

1. **Work-split is predictable for the full cycle** (4-day blocks) — no mid-cycle BACKLOG churn
2. **Per-slot themes are stable**: deployment scripts, coverage, QG ratchets, etc. — slot owns the theme, not items
3. **Density target is defined**: cal-AI-days per slot per cycle
4. **Continuation prompts cover full cycle** (Day 1-4 + scope extension reserves)

Until then: hybrid model (multi-item briefs + auto-poller) keeps reactivity high while reducing operator juggling.

---

## How tomorrow's main boots

1. Read `harsh_orchestrator/LEDGER.md` § "🏁 End-of-shift summary" for shift-end state
2. Read `plans/active/_agent_pings.md` for cross-side asks pending Ikenna response
3. Read this template, decide whether to write today's continuation prompts doc
4. If yes: copy template, fill per-slot sections, save as `plans/active/continuation_prompts_harsh_<YYYY_MM_DD>.md`
5. Drop link to each slot's section in their `pings/slot_N.md` direction ping
6. Start `scripts/orchestrator/auto-poll-harsh.sh` (or rely on /loop wrapper)
7. Reduce polling cadence to ~10-15 min while auto-poller handles mechanical work
