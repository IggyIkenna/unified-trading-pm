---
doc_type: issue
title:
  tradfi ohlcv_1h was added to SOURCE_PRIORITY without an availability semantic — the choice is a point-in-time
  correctness decision, not a registry fill-in
summary: >-
  A half-finished change adds ("tradfi","ohlcv_1h"):["yahoo"] to SOURCE_PRIORITY and to the validity matrix but never to
  AVAILABILITY_AT_SEMANTICS, so 6 UAC tests fail tree-wide and every unrelated UAC ship is blocked. The missing entry
  cannot be filled mechanically: the two sibling timeframes disagree — ("tradfi","ohlcv_1m") is tick_timestamp and
  ("tradfi","ohlcv_1d") is fetch_completed_at — and for a Yahoo-served bar the choice decides whether we assert the bar
  was available at its own timestamp. Choosing tick_timestamp when Yahoo only serves the bar later writes lookahead bias
  into a shared contract that every downstream consumer trusts. The work is parked (stashed + backed up), not reverted;
  UAC Phases 2-3 shipped around it.
status: open
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [unified-api-contracts, market-tick-data-service]
scope: [engineer]
tags: [data-correctness, availability-semantics, source-priority, point-in-time, blocked-operator-decision]
related:
  [
    /plans/active/issues/tradfi_databento_account_billing_suspended_2026_08_09.md,
    /codex/02-data/honest-absence-downstream-handling.md,
    /codex/02-data/tradfi-databento-sourcing-ssot.md,
    /plans/active/alert_driven_dependency_revocation_2026_08_12.md,
  ]
created: 2026-08-13
last_updated: "2026-08-13"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: design
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.2
assigned_role: data_engineer
drift_direction: advance-code
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  Found 2026-08-13 inheriting ~5h-idle WIP in slot 4 while shipping UAC Phases 2-3. The Yahoo half was the sole cause of
  all 6 gate failures; the revocation half was clean and shipped separately.
depends_on: []
context_scope:
  [
    unified-api-contracts/unified_api_contracts/canonical/crosscutting/availability_semantics.py,
    unified-api-contracts/unified_api_contracts/canonical/crosscutting/_source_priority_data.py,
    unified-api-contracts/unified_api_contracts/registry/market_data_categories.py,
  ]
---

# tradfi ohlcv_1h has no availability semantic

## What is parked, and where

Two files, stashed under the named ref `slot4-PARKED-yahoo-ohlcv_1h-needs-availability-semantic-decision` in slot 4's
`unified-api-contracts` checkout, with a file-level copy under the session scratchpad:

| file                                              | change                                                   |
| ------------------------------------------------- | -------------------------------------------------------- |
| `canonical/crosscutting/_source_priority_data.py` | adds `("tradfi","ohlcv_1h"): ["yahoo"]`                  |
| `registry/market_data_categories.py`              | adds `"ohlcv_1h"` to the tradfi equities validity matrix |

Nothing was reverted and nothing was adjudicated on the author's behalf. It is parked precisely because the missing
piece is a judgment, not a typo.

## Why it blocks everything, not just itself

The pair is registered as a source but has no availability semantic, so two symmetry invariants fail and take four more
tests with them:

```
SOURCE_PRIORITY pairs unreachable from the validity matrix: [('tradfi', 'ohlcv_1h')]
Era-B purge would break SOURCE_PRIORITY <-> AVAILABILITY_AT_SEMANTICS symmetry.
  SOURCE_PRIORITY-only: [('tradfi', 'ohlcv_1h')]; AVAILABILITY-only: []
```

Six failures, one root. Because they are tree-wide, ANY unrelated `unified-api-contracts` ship is blocked while this
sits — which is how it was found.

## The decision needed (this is the whole issue)

**Which availability semantic does a Yahoo-sourced `tradfi ohlcv_1h` bar carry?** The sibling timeframes do not agree,
so there is no precedent to copy:

| pair                     | semantic             | meaning                                    |
| ------------------------ | -------------------- | ------------------------------------------ |
| `("tradfi", "ohlcv_1m")` | `tick_timestamp`     | available AT the bar's own timestamp       |
| `("tradfi", "ohlcv_1d")` | `fetch_completed_at` | available only when we actually fetched it |

This is not a formatting choice. `tick_timestamp` asserts point-in-time availability at the bar's timestamp; if Yahoo
only serves that bar some minutes or hours later, then every backtest reading this registry gets **lookahead bias**,
silently, from a contract it is entitled to trust. `fetch_completed_at` is the conservative direction — it can only make
a strategy look worse than reality, never better.

The author's own comment concedes the uncertainty: the start date is described as "the operator-scoped real-launch
window floor (2026-01-01), NOT a Yahoo serving-floor fact", i.e. Yahoo's real 1h lookback and delay were never measured.

## Todos

- [ ] [OPERATOR] P1. **Decide the semantic for `("tradfi","ohlcv_1h")`.** Done-when: the choice and its justification
      are recorded here. If the answer is "we don't know Yahoo's serving delay", that makes it `fetch_completed_at` by
      default — the conservative direction — not a coin flip.
- [ ] [DATA] P1. **Measure Yahoo's actual 1h serving delay** rather than assuming it: fetch the same symbol repeatedly
      across a session boundary and record when each bar first becomes retrievable relative to its own close timestamp.
      That measurement is what makes the todo above answerable, and it is cheap. Repo: market-tick-data-service.
- [ ] [CODE] P1. Once decided, add the entry to `AVAILABILITY_AT_SEMANTICS`, unstash the two parked files, and verify
      all six tests go green together (`test_source_priority`, `test_validity_matrix_completeness`, and the four
      `test_era_b_purge` cases). Repo: unified-api-contracts.
- [ ] [DOCS] P2. Record in `/codex/02-data/tradfi-databento-sourcing-ssot.md` that Yahoo is an interim `ohlcv_1h` source
      while Databento billing is suspended, with its measured delay — so the next person adding an interim vendor knows
      the availability semantic is part of the change, not a follow-up.

## Progress Log

- 2026-08-13 — Filed while inheriting ~5h-idle WIP in slot 4. The Yahoo half was the sole cause of all 6 UAC gate
  failures; the dependency-revocation half in the same dirty tree was independent and clean, so it was separated and
  shipped as `unified-api-contracts@c206f9100d` (Phases 2-3) rather than being held hostage to this decision. Parked
  rather than guessed because a wrong `tick_timestamp` here is invisible: it produces optimistic backtests, not an
  error. The failing test is the only thing standing between that guess and a shared contract.
