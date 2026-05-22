---
title: "AUDIT-03 — findings routed to Ikenna for decision / codex-intent"
created: 2026-05-22
author: Harsh (Claude Opus 4.7)
priority: P1
status: active
locked_by: live-defi-rollout
source:
  - audits/audit-files/audit_03_defi_archetypes_e2e.md (§6 + §6.1 re-verification ledger)
---

# AUDIT-03 — findings routed to Ikenna

These AUDIT-03 findings are **Opus-confirmed real** but are NOT pure code fixes — each needs a judgment call,
cross-cutting architecture decision, or a codex-intent ruling that Ikenna owns (trading-judgment / governance /
cross-repo spec authority). They are deliberately kept OUT of the remediation plans (carry-safety, cron-provisioning,
drift-backlog) until the decision lands, so we don't ship a fix that contradicts the intended design.

> Cross-side ping: on next push, add a one-line entry to `plans/active/_agent_pings.md` pointing here. (Held back per
> "local commit only" instruction 2026-05-22.)

## 1. F-34 (XAS-01) — rollout-subset vs missing-engines decision **[DECISION]**

**What I found**: `ARCHETYPE_ENGINE_REGISTRY` has 28 entries; `StrategyArchetype` enum has 55 members (docstring stale
at "53"). 27 archetypes (18 `VOL_*`, 5 granular market-making, 2 `ARBITRAGE_*`, 4 `PORTFOLIO_*`) have no engine.
Dispatch (`factory.py:87-95`) raises a descriptive `KeyError` whose docstring says "every enum value must have an
engine" — i.e. the code treats the 27-gap as a BUG, and there is no `SUPPORTED_ARCHETYPES` allowlist marking the 28 as
an intended May-23 subset.

**Why it matters**: If these 27 are an intended phased rollout, the code is fine but needs an explicit allowlist +
docstring/count fix so the gap isn't read as a regression by the next auditor. If they are genuinely-missing engines,
they are 27 latent `KeyError`s waiting for a config that names them.

**Recommended decision (Ikenna)**: confirm "28 = intended May-23 rollout subset". If yes → add `SUPPORTED_ARCHETYPES`
allowlist + fix the "53"→55 docstring + a guard that returns a typed "archetype not in rollout" error. If no → file the
missing engines as their own epic.

## 2. F-06 (ONB-07) — operating-entity governance **[DECISION]**

**What I found**: CLAUDE.md names Odum / Cayman as the operating legal entities; codex references "Elysium" only as a
DELETED-provider archived ref, "POD" as a custody-delivery party (not a legal entity), and no "BVI". So it is NOT a
clean active-entity conflict (§6.1 reframe) — the real issue is a stale archived Elysium reference + no single
entity-model SSOT.

**Why it matters**: onboarding + custody + audit trails key off the operating entity; ambiguity here touches client
funds isolation + reporting.

**Recommended decision (Ikenna)**: declare the canonical entity-model SSOT (which doc owns Odum/Cayman) + scrub the
stale Elysium reference. Governance call, not a code fix.

## 3. F-13 / F-14 / F-15 (APD) — codex strategy-spec phantom fields **[CODEX-INTENT]**

**What I found** (all confirmed): codex `arbitrage-price-dispersion.md` references config fields/values the engine does
NOT implement, and the engine uses different mechanisms:

- F-13: codex calls `dynamic-best-long-short` a `PairSelectionMode`; it is actually a `venue_selection_mode` value. The
  enum has only `single-best` / `top-k` / `all-above-threshold`.
- F-14: codex `max_underlying_move_pct: 3.0` is phantom; the engine guards via `vol_cap_clamp_*` instead.
- F-15: codex `react_to_equity_change` + `max_capital_per_opp_pct` are phantom; the engine auto-scales via
  `stake_fraction · target_equity` (functionally equivalent).

**Why it matters**: codex is the strategy SSOT; if it specifies fields that don't exist, either the engine is missing a
guard (F-14 is the only one with a possible safety implication — a raw price-move abort) or the codex is describing a
superseded design.

**Recommended decision (Ikenna)**: per field — reconcile codex to the implemented mechanism, OR rule that the engine
must implement it. F-14 (`max_underlying_move_pct`) is the one to look at first: is `vol_cap_clamp` an acceptable
substitute for a raw 1h price-move abort, or do we need both?

## 4. F-32 (EXE-02) — is MEV mode meant to be size-selected? **[CODEX-INTENT]**

**What I found**: there is NO code that selects an MEV-protection mode by trade notional (e.g. `>$10k → FLASHBOTS`).
`MevRouter.route(mode, chain)` (`mev_router.py:97`) takes the mode as a parameter; it is purely directive/config-driven.
BLOXROUTE is correctly excluded.

**Why it matters**: if codex intends auto-selection-by-size, this is a real GAP (a large swap could go to the public
mempool). If codex says the directive carries the mode, there is no defect and the finding closes.

**Recommended decision (Ikenna)**: rule on the EXE-02 oracle — directive-driven (close F-32) or size-driven (it becomes
a P1 fix in the carry-safety / execution plan).

## 5. F-45 (RPT-07) — events path: instance_id vs correlation_id **[CODEX-INTENT]**

**What I found**: `GcsEventSink` writes `events/{service}/{date}/{instance_id}/hour=.../` (`event_sink.py:128-131`);
codex `live-deployment-monitoring.md:38` specifies `correlation_id` as that 3rd segment. The code uses VM-scoped
`instance_id` (VM_NAME / host-pid); codex wants run-scoped `correlation_id`.

**Why it matters**: determines whether you can prefix-filter the events stream by correlation_id (per-run trace) vs
per-VM. Likely the codex doc is the stale side (post-2026-05-01 sink rev), but that's a canonical-side ruling.

**Recommended decision (Ikenna)**: declare which is canonical. If code wins → update the codex doc. If codex wins → add
`correlation_id` to the sink path (a code fix that then moves to the drift-backlog plan).

---

## Routing summary

| Finding    | Type         | One-line decision needed                                   |
| ---------- | ------------ | ---------------------------------------------------------- |
| F-34       | DECISION     | Is the 28-engine set an intended May-23 rollout subset?    |
| F-06       | DECISION     | Canonical operating-entity SSOT + scrub stale Elysium ref  |
| F-13/14/15 | CODEX-INTENT | Reconcile APD codex phantom fields to code (F-14 first)    |
| F-32       | CODEX-INTENT | Is MEV mode directive-driven (close) or size-driven (fix)? |
| F-45       | CODEX-INTENT | events path: instance_id (code) vs correlation_id (codex)? |
