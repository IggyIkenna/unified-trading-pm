---
doc_type: plan
title: Sports arb engine — same-operator guard silently passes on canonical venues + SMARKETS commission unmodelled
summary: >-
  Two live money bugs in the sports arbitrage engine, found by the 2026-08-08 venue/data-type audit and independent of
  the taxonomy migration that audit triggered. (1) `arb_config.VENUE_OPERATOR_GROUPS` is keyed on LOWERCASE vendor
  spellings (`betfair_ex_uk`, `unibet_uk`, `ladbrokes_uk`) — the exact spellings UAC's `SPORTS_VENUE_FOLD` was built to
  eliminate from the data layer — so when fed the canonical UPPERCASE venue values production now emits,
  `arb_legs_are_independent(['BETFAIR_EX_UK','BETFAIR_EX_EU'])` returns True and the engine will size a "risk-free" arb
  across two skins of the same book. Measured live this session, not inferred. (2) `EXCHANGE_VENUES` omits SMARKETS — a
  real commission-charging exchange with 5,626 captured shards — so its commission is not modelled on any arb leg,
  overstating net edge. Shipped as a standalone fast fix ahead of the taxonomy chain (operator ruling 2026-08-08) since
  neither depends on the rename work and both are live-capital exposure.
status: active
nature: process
asset_group: [sports]
stage: [strategy]
repos: [unified-api-contracts, strategy-service]
scope: [engineer]
tags: [sports, arbitrage, venue-canonicalisation, operator-group, commission, money-bug, casing]
related:
  [
    /plans/active/sports_taxonomy_p1_capture_and_contracts_2026_08_08.md,
    /plans/active/sports_arb_decay_window_and_alpha_gate_design_2026_07_21.md,
    /codex/02-data/defi-canonical-naming-ssot.md,
  ]
created: 2026-08-08
last_updated: 2026-08-08
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: refactor
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.4
assigned_role: backend_engineer
supersedes:
superseded_by:
resolved_by:
drift_direction: advance-code
depends_on:
context_scope:
  [
    unified-api-contracts/unified_api_contracts/internal/domain/sports/arb_config.py,
    unified-api-contracts/unified_api_contracts/registry/venue_constants.py,
    unified-api-contracts/unified_api_contracts/registry/market_data_categories.py,
    strategy-service/strategy_service/adapters/sports/arbitrage_detector.py,
    /codex/06-coding-standards/quality-gates.md,
  ]
source: ["sports venue/data-type audit, 2026-08-08 interactive session — operator ruling: ship now, standalone"]
locked_by:
locked_since:
---

# Sports arb engine — two live money bugs

> **Independent of the sports taxonomy chain by design.** These fixes must NOT wait on the rename/migration work
> (`/plans/active/sports_taxonomy_p1_capture_and_contracts_2026_08_08.md`). Operator ruling 2026-08-08: "ship now as a
> standalone fast fix".

## Bug 1 — the same-operator guard silently passes on canonical venue values

`unified_api_contracts/internal/domain/sports/arb_config.py::VENUE_OPERATOR_GROUPS` maps LOWERCASE vendor spellings to
operator groups. `arb_legs_are_independent()` calls `get_operator(v)`, which falls back to `v` itself on a miss — so an
unrecognised spelling becomes its own operator and the guard passes.

**Measured this session (not inferred), against the shipped code:**

| call                                                          | returns           | correct?              |
| ------------------------------------------------------------- | ----------------- | --------------------- |
| `arb_legs_are_independent(['BETFAIR_EX_UK','BETFAIR_EX_EU'])` | **True**          | **NO**                |
| `arb_legs_are_independent(['betfair_ex_uk','betfair_ex_eu'])` | False             | yes                   |
| `arb_legs_are_independent(['UNIBET_UK','UNIBET'])`            | **True**          | **NO**                |
| `get_operator('BETFAIR_EX_UK')`                               | `'BETFAIR_EX_UK'` | should be `'BETFAIR'` |

**Why production hits the broken path**: UAC `SPORTS_VENUE_FOLD` deliberately folds the vendor's wire spellings
(`ladbrokes_uk`, `sport888`) to canonical UPPERCASE at write time, and MTDS/MDPS writers stamp the canonical form. The
manifest's `venue` column therefore carries `BETFAIR_EX_UK`, never `betfair_ex_uk`. The guard is keyed on a vocabulary
the data layer no longer produces.

**Consequence**: a two-leg "arb" across Betfair Exchange UK and Betfair Exchange EU is not an arb — same counterparty,
same book, and Betfair will void or limit it. The engine currently sizes it as risk-free.

## Bug 2 — SMARKETS commission unmodelled

`EXCHANGE_VENUES = {betfair_ex_uk, betfair_ex_eu, betfair_ex_au, matchbook}`. SMARKETS is a real UK betting exchange
that charges commission on net winnings and has **5,626 captured `trades` shards** in the prod sports manifest. It is
absent, so `_expected_commission_pct()` contributes 0 for any SMARKETS leg and net edge is overstated.

## Bug 3 (adjacent, same file) — a fifth venue vocabulary

`arb_config.py` references `betfair_ex_au`, `unibet_fr`, `unibet_nl`, `unibet_se`, `ladbrokes_au`, `williamhill_us`,
`winamax_fr`, `winamax_de`, `leovegas_se` — **none of which exist in `venue_constants.py`**. This is a fourth/fifth
parallel venue vocabulary drifting from the UAC registry. In scope here because it is the same file and the same class
of defect; the canonical fix is to key everything on the UAC venue constants.

---

## Todos

- [x] [CODE] P0. ✅ **Re-key `VENUE_OPERATOR_GROUPS` onto the UAC canonical venue constants** (uppercase, imported from
      `registry.venue_constants`, never string literals). Keep `get_operator()`'s "unmapped venue is its own operator"
      fallback — that default is correct — but make the lookup case-insensitive (normalise via `.upper()` on entry) so
      BOTH the canonical form and any residual lowercase vendor spelling resolve to the same group. Do not simply
      lowercase the caller: the data layer's canonical output is uppercase and the registry is the SSOT. —
      unified-api-contracts@e080ef74
- [x] [CODE] P0. ✅ **Add the missing operator-group parent for Betfair.** Per operator ruling 2026-08-08, bare
      `BETFAIR` stops being a data-axis venue and becomes the operator-group PARENT that `BETFAIR_EX_UK` /
      `BETFAIR_EX_EU` / `BETFAIR_SB_UK` roll up to. Encode that hierarchy in UAC (a real venue→operator map keyed on
      venue constants), and have `VENUE_OPERATOR_GROUPS` derive from it rather than restating it. **PRE-SPECIFIED**: all
      three roll up to a single `BETFAIR` operator — the sportsbook and the exchange are the same counterparty for
      arb-independence purposes, which is the only question this map answers. Do not preserve the separate `BETFAIR_SB`
      group. — unified-api-contracts@b9a0be80
- [ ] [CODE] P0. **Add SMARKETS to `EXCHANGE_VENUES` + `EXCHANGE_COMMISSION_RATES` at `0.02` (2.0% on net winnings).**
      Rate PRE-SPECIFIED by the operator 2026-08-08 so this todo needs no decision: use `0.02`, and record in the
      Progress Log the published source you verified it against. If the published rate turns out to differ, ship `0.02`
      anyway and file a follow-up `- [ ]` todo with the corrected figure — do NOT stall the fix on a rate lookup, since
      an unmodelled commission (today's state) is strictly worse than a slightly-wrong one.
- [ ] [CODE] P1. **Reconcile the phantom regional venues** (`betfair_ex_au`, `unibet_fr/nl/se`, `ladbrokes_au`,
      `williamhill_us`, `winamax_fr/de`, `leovegas_se`). **Decision rule PRE-SPECIFIED, no judgment call**: a venue
      stays only if it appears in the live prod sports manifest's `venue` column OR in `SPORTS_VENUE_FOLD`'s key set;
      otherwise DELETE the entry. Measured today, none of the nine appear in either — so the expected outcome is nine
      deletions. Re-measure at run time and report the actual counts; no shims, workspace rule is delete deprecated
      code.
- [ ] [TEST] P0. **Regression test asserting the exact measured failures above now pass**:
      `arb_legs_are_independent(['BETFAIR_EX_UK','BETFAIR_EX_EU']) is False`,
      `arb_legs_are_independent(['UNIBET_UK','UNIBET']) is False`, `get_operator('BETFAIR_EX_UK') == 'BETFAIR'`, and a
      SMARKETS leg producing a non-zero expected commission. Test the CANONICAL uppercase spellings specifically — a
      test written in lowercase would have passed against the broken code and is exactly why this shipped.
- [ ] [TEST] P1. **Property test: every venue in `SPORTS_BET_PLACEMENT_VENUES` resolves through `get_operator()` without
      falling through to the identity default unless it is genuinely a standalone operator.** This is the guard that
      stops the next venue addition from silently reintroducing the bug.
- [ ] [REVIEW] P1. **Audit `arbitrage_detector.py`'s call site for any other casing assumption.**
      `_find_best_odds_per_outcome` passes `entry["bookmaker"]` straight into `arb_legs_are_independent`; confirm what
      casing the live market dict actually carries end-to-end (read the producer, do not assume), and record the
      finding. Grep-then-READ — a zero-hit grep is not evidence here.
- [ ] [SCRIPT] P1. **Quantify the blast radius**: over the paper-trade / backtest record, count how many detected arbs
      had all legs within one operator group (i.e. would have been rejected by the fixed guard) and how many carried a
      SMARKETS leg. This tells us whether any historical "alpha" was this bug. Report the counts in the Progress Log; if
      the count is non-zero, file a follow-up `- [ ]` todo against the arb-decay/alpha-gate design plan so its baseline
      is recomputed on the corrected population.

## Codex SSOTs

- `/codex/06-coding-standards/quality-gates.md` — QG-green tree is the contract; commit only from green.
- `/codex/02-data/defi-canonical-naming-ssot.md` — precedent for "the registry is the SSOT, not a parallel literal map".

## Progress Log

- **2026-08-08** — Authored from the interactive sports venue/data-type audit. Both bugs measured live against the
  shipped `arb_config.py` (see the table above), not inferred from reading. Operator ruled: ship standalone, ahead of
  and independent of the sports taxonomy chain.
- **2026-08-08** — Todo 1 (re-key VENUE_OPERATOR_GROUPS) shipped in unified-api-contracts@e080ef74. Imported UAC
  constants (BETFAIR_EX_UK/EU, BETFAIR_SB_UK, UNIBET, LEOVEGAS, LADBROKES, WILLIAMHILL) replace the previous lowercase
  string literals; `.upper()` normalisation added to `get_operator()`. Remaining string literals in the dict
  (BETFAIR_EX_AU, UNIBET_UK/FR/NL/SE, LADBROKES_AU, WILLIAMHILL_US, WINAMAX_FR/DE, LEOVEGAS_SE) are the phantom regional
  venues with no UAC constant — their fate is decided by todo 4 (expected: nine deletions).
