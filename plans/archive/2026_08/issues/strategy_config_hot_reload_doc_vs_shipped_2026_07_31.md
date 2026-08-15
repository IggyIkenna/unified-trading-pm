---
doc_type: issue
title:
  live-strategy-config-hot-reload.md documents a safe-field allow-list and UnsafeConfigChangeError that do not exist —
  and the shipped reloader hot-swaps the instrument universe the doc lists as restart-required
summary: >-
  `/codex/04-architecture/live-strategy-config-hot-reload.md` (status `current`, `authoritative_for` the live
  strategy-config hot-reload contract) described a `StrategyConfigReloader` class that validates each config diff
  against a safe-field allow-list and raises `UnsafeConfigChangeError` for unsafe fields. Verified 2026-07-31 against
  `strategy-service/strategy_service/config_reloaders.py`: the capability IS shipped but under a different shape —
  module-level `start_domain_config_reloaders()` built on UTL `DomainConfigReloader` — and **none of the safety
  machinery exists**. There is no `StrategyConfigReloader`, no `UnsafeConfigChangeError` anywhere in the workspace, and
  no safe-list / allow-list / restart guard in the module (`rg -in 'unsafe|safe_list|allow_list|restart'` returns
  nothing). Every reload is an unconditional atomic swap. Most importantly, the doc's table lists "Underlying
  instruments = NO (position-state continuity is broken; restart required)", but `_on_instruments_reload()` hot-swaps
  `_active_instruments`, computes an added/removed delta, and fans it out via `INSTRUMENT_UNIVERSE_CHANGED` — so the
  exact change the doc calls unsafe is applied live today with no error raised.
status: resolved
nature: issue
asset_group: [cross-cutting]
stage: [strategy]
repos: [strategy-service, unified-trading-library, unified-trading-pm]
scope: [engineer, admin]
tags: [strategy, live-trading, hot-reload, config, ssot-contradiction, safety]
related:
  [
    /codex/04-architecture/live-strategy-config-hot-reload.md,
    /codex/06-coding-standards/config-reloader-pattern.md,
    /codex/04-architecture/instrument-lifecycle-cache-delta-hot-reload.md,
  ]
created: 2026-07-31
author: unknown
priority: P2
parent_epic: infrastructure_master
source:
  "slot-3, codex freshness re-review shard-B, discovered re-reviewing live-strategy-config-hot-reload.md, 2026-07-31"
execution_scope: local-only
drift_direction: needs-decision
depends_on: []
assigned_vm: NA
resolved_by: strategy-service@c688512912
locked_by:
locked_since:
last_updated: "2026-08-14"
context_scope:
  [
    strategy-service/strategy_service/config_reloaders.py,
    unified-trading-library/unified_trading_library/domain_config_reloader.py,
    /codex/04-architecture/live-strategy-config-hot-reload.md,
    /codex/04-architecture/instrument-lifecycle-cache-delta-hot-reload.md,
    /codex/06-coding-standards/config-reloader-pattern.md,
  ]
---

> **🟢 ARCHIVED 2026-08-14 — RESOLVED** (status: resolved, 1/1 todo `[x]`, unlocked). Safe-field allow-list +
> `UnsafeConfigChangeError` guard implemented in `strategy_service/config_reloaders.py` (`strategy-service@c688512912`)
> per the operator-confirmed 2026-08-12 option-A ruling; codex doc updated to reflect the strategies-domain enforcement.
> Archived by review worker (slot 20).

# Documented hot-reload safety machinery does not exist; instrument-universe row contradicts shipped behaviour

## Doc vs shipped (measured 2026-07-31)

| Doc claim                                            | Shipped reality                                                                            |
| ---------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| `StrategyConfigReloader` class registered at startup | Module-level `start_domain_config_reloaders(service_config)` on UTL `DomainConfigReloader` |
| Emits `STRATEGY_CONFIG_RELOADED`                     | Emits `CONFIG_CHANGED` (`details.domain`) + `INSTRUMENT_UNIVERSE_CHANGED`                  |
| Validates diff against a safe-field allow-list       | **No allow-list exists**; unconditional atomic swap                                        |
| Unsafe fields raise `UnsafeConfigChangeError`        | **Symbol does not exist anywhere in the workspace**                                        |
| "Underlying instruments — NO, restart required"      | `_on_instruments_reload()` hot-swaps the universe + notifies engines via delta             |
| "SAME validation rules apply batch and live"         | No validation gate on the live reload path at all                                          |

Also shipped but undocumented: `VersionGovernanceReloader` / `start_version_governance_reloader()` and
`StrategyDirectiveReloader` / `start_directive_reloader(poll_interval_seconds=60)`.

## Why this matters beyond naming

This doc is the SSOT an operator or agent would consult before changing a live strategy's config. It currently promises
a guard-rail that is not there. Two concrete risks:

1. **False confidence in a safety net.** An operator reading "unsafe-field changes raise `UnsafeConfigChangeError` and
   require a planned restart through DART" may push an archetype-family or instrument-universe change to a live strategy
   expecting the system to refuse it. Nothing refuses it.
2. **Unclear correctness on instrument swaps.** The design asserts that swapping the underlying instrument set breaks
   position-state continuity. The code does exactly that swap, live. Either the design concern is real (and we have a
   live correctness hazard on every instrument-universe reload), or the concern is obsolete (and the doc is scaring
   operators off a supported operation). Both readings are currently defensible from the corpus, which is precisely the
   problem.

Interim mitigation already applied: the codex doc now documents the shipped entry points and carries explicit ⚠️ blocks
stating that the allow-list and error type do not exist and that the instrument row is contradicted.

## Decision needed

- **A** — Implement the documented guard: add a safe-field allow-list + `UnsafeConfigChangeError` to
  `config_reloaders.py` so the codex contract becomes true. Preferred if the position-state-continuity concern is real.
- **B** — Retire the guard from the design: confirm instrument-universe hot-swap is intentional and safe (the delta
  callbacks suggest it was built deliberately), and rewrite the table to describe what is actually enforced.
- **C** — Split: keep hot-swap for the instrument universe (already relied on) but gate archetype-family changes only.

## Follow-ups

- [x] ✅ [CODE] P2. **RULED 2026-08-06 (operator), option A: implement the documented guard — CONFIRMED 2026-08-12
      (/plan-reconcile, operator confirmed interactively).** `[CODE]` tag (was `[OPERATOR]`) — build the safe-field
      allow-list + `UnsafeConfigChangeError` as originally designed, closing the real gap that any field can currently
      hot-swap into a live paper/live trading strategy. AO-dispatchable. Provenance: codex freshness re-review shard-B,
      2026-07-31. This todo previously carried a self-contradiction (opening line claimed RULED, closing line still
      called it a 3-way undecided design call, with no Progress Log entry recording an actual ruling event) — resolved
      2026-08-12: the operator confirmed option A is the standing ruling. The implementation itself (safe-field
      allow-list + guard) is NOT done here — this only resolves the doc-level contradiction; the code change remains
      open, AO-dispatchable work. — **IMPLEMENTATION DONE**, reconciled from
      `cross_cutting_satellite_ao_dispatch_batch13b_2026_08_13.md`: `strategy-service@c688512912` — added
      `SAFE_STRATEGY_RELOAD_FIELDS` + `UnsafeConfigChangeError` to `config_reloaders.py`; `_on_strategies_reload` now
      diffs incoming vs active config field-by-field, raising on any non-`strategy_params` change (previously active
      config stays in effect). 5 new unit tests. Codex SSOT updated same session.
- [x] [DOC] P3. Document `VersionGovernanceReloader` + `StrategyDirectiveReloader` in
      `/codex/04-architecture/live-strategy-config-hot-reload.md` — both are shipped and currently absent from the SSOT.
      -- CLOSED (na-eligibility-audit 2026-08-01): already done —
      `/codex/04-architecture/live-strategy-config-hot-reload.md` lines 62-63 (the "Pattern — as shipped" entry-points
      table) already list both `start_version_governance_reloader()` (`VersionGovernanceReloader`) and
      `start_directive_reloader(poll_interval_seconds=60)` (`StrategyDirectiveReloader`) with their roles.

## Progress Log

- **2026-08-14 (slot-29, review, `cross_cutting_satellite_ao_dispatch_batch13b_2026_08_13_finalize.md` todo 1)**:
  reached 0 open todos this session via checkbox reconciliation from
  `cross_cutting_satellite_ao_dispatch_batch13b_2026_08_13.md`. `archive_exempt: true` set deliberately — full 6-step
  archival (incl. corpus-wide referrer fixup) is that finalize plan's separate todo 2, not this reconciliation pass's
  scope. Drop this field and archive when todo 2 runs.
- **context-scout 2026-08-01**: populated/refreshed context_scope (3 entries).
- **na-eligibility-audit 2026-08-01**: KEEP-NA, stale items closed -- 1 item(s) closed as stale/duplicated (see
  checkboxes above), doc stays assigned_vm: NA. Full audit rationale: One item (the operator A/B/C ruling on whether
  live instrument-universe hot-swap is position-state-safe) is a genuine unresolved design/judgment call requiring an
  operator decision — stays KEEP_JUDGMENT. The other item (document VersionGovernanceReloader +
  StrategyDirectiveReloader in the codex SSOT...
- **context-scout 2026-08-03**: refreshed context_scope (5 entries) — swapped in the actual shipped source
  (`config_reloaders.py`) and its UTL base class (`domain_config_reloader.py`), and the sibling codex doc
  (`instrument-lifecycle-cache-delta-hot-reload.md`) the open `[OPERATOR]` position-state-safety ruling bears on;
  dropped the generic epic pointer.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (5 entries), unchanged.
- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — reaffirms 2026-08-01 (unchanged): sole remaining todo is an
  [OPERATOR] 3-way design call on live-trading position-state safety.
- **round11 RECLASSIFY sweep 2026-08-09**: NOT reclassified — found the sole todo's own opening text ("RULED 2026-08-06
  (operator), option A: implement the documented guard") directly contradicts its own closing text ("Rule between A / B
  / C — specifically, confirm whether a live instrument-universe swap is position-state-safe") and this SAME doc's own
  2026-08-06 audit entry immediately above, which still calls it an undecided `[OPERATOR]` call. No Progress Log entry
  anywhere records an actual ruling. Filed
  `issues/two_issue_docs_claim_2026_08_06_operator_ruling_with_no_corroborating_evidence_2026_08_09.md` (a sibling doc,
  `order_state_machine_ssot_vs_uac_orderstatus_2026_07_31.md`, has the identical malformed pattern) rather than acting
  on the unverified "RULED" text — this is a live-trading-safety decision, too consequential to dispatch on
  contradictory self-reported text. Doc stays `assigned_vm: NA`.
