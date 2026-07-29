---
doc_type: issue
title:
  Aster perp-funding backfill (leg c) — plan's named launcher is retired; 3-way genesis-date conflict found (2023-07-22
  vs 2023-11-01 vs 2024-01-01)
summary: >-
  cross_cutting_satellite_ao_dispatch_batch1b-006 leg (c) instructs running `launch-mtds-perp-funding-backfill-vm.sh
  --perp-protocols aster` — that launcher's target handler (PerpFundingHandler/collect-perp-funding) RETIRED Aster from
  standalone perp_funding capture 2026-07-08 (funding now comes solely from derivative_ticker via a different
  handler/launcher). Running the plan-literal command would hit an unknown-protocol branch and write false
  attempted_failed manifest rows. Separately, live manifest census found ASTER derivative_ticker's real captured
  coverage starts 2023-11-01, not the plan's stated 2023-07-22 native genesis nor the correct launcher's own documented
  2024-01-01 default — a genuine 3-way disagreement on the intended start date that should be resolved before any VM
  launch, not guessed.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [data]
repos: [market-tick-data-service, deployment-service]
scope: [engineer, admin]
tags: [aster, perp-funding, backfill, stale-reference, data-correctness]
related:
  [
    /plans/active/cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md,
    /plans/active/issues/perp_funding_data_semantics_and_cadence_2026_06_16.md,
  ]
created: 2026-07-28
priority: P2
parent_epic: mtds_mdps_master
assigned_vm: planning
execution_scope: orchestrator-agent
sequential: false
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: ["cross_cutting_satellite_ao_dispatch_batch1b-006, slot 14, 2026-07-28"]
drift_direction: advance-code
---

# Aster perp-funding backfill — stale launcher + genesis conflict (2026-07-28)

## What I found

**1. The plan's named launcher targets a retired code path.**
`market_tick_data_service/cli/handlers/ perp_funding_handler.py`'s own module docstring: "RETIRED (2026-07-08,
operator-approved): HYPERLIQUID, ASTER, and LIGHTER-ZKSYNC no longer capture a standalone `perp_funding` shard — their
funding rate is byte-identical to the `funding_rate` field already carried on `derivative_ticker`... HL/ASTER
`derivative_ticker` is captured independently via `collect-onchain-perp-batch` (`onchain_perp_batch_handler.py`)."
`PerpFundingHandler.DEFAULT_PROTOCOLS` today only lists `kalshi_perp`/ `polymarket_perp`; passing
`--perp-protocols aster` would dispatch to `_dispatch_protocol`'s "Unknown protocol" branch, which calls
`recorder.record_failed(...)` — i.e. it would write false `attempted_failed` manifest rows for every date requested, not
silently no-op. The CORRECT current launcher for Aster funding (via `derivative_ticker`) is
`deployment-service/scripts/vm/launch-cefi-hl-aster-historical-backfill.sh` (`VM_OPERATION=collect-onchain-perp-batch`),
which already supports `VENUES=ASTER DATA_TYPES=derivative_ticker` scoping plus
`OVERRIDE_START_DATE`/`OVERRIDE_END_DATE` clamps.

**2. Three disagreeing genesis dates for Aster funding coverage:**

- **2023-07-22** — the plan's own text + the source issue doc's "operator-confirmed genesis 2026-06-17" note (pre-2024
  explicitly labeled Binance-proxied Astherus funding).
- **2023-11-01** — the REAL earliest captured `derivative_ticker` row for ASTER, confirmed live via the availability
  manifest (`market-data-tick-cefi-prd-central-element-323112`): 226,008 `captured` rows span 2023-11-01→2026-07-27; the
  window 2023-07-22→2023-10-31 has **zero manifest rows of any kind** (not even `expected_unattempted` — genuinely never
  scanned/attempted by any prior run).
- **2024-01-01** — `launch-cefi-hl-aster-historical-backfill.sh`'s own hardcoded `VENUE_START_YEAR["ASTER"]=2024` /
  `VENUE_START_DATE["ASTER"]="2024-01-01"` defaults (its header comment: "ASTER: 2024-01-01 → today (17,675 cells, cefi
  manifest audit 2026-06-21)").

None of the three is self-evidently authoritative from code/docs alone — this is a genuine gap-window ambiguity (~102
days between the claimed native genesis and the real captured start), not a mechanical fact a worker should resolve by
picking one.

## Why it matters

Funding coverage feeds `carry_staked_basis` ranking (the same P1 driver cited throughout
`perp_funding_data_semantics_and_cadence_2026_06_16.md`). Launching the plan-literal (retired) command would actively
corrupt the manifest with false failures. Guessing the wrong genesis date for a corrective backfill either leaves a real
gap unfilled or wastes SPOT compute re-scanning dates that were never native Aster activity (the source doc already
flags pre-2024 as Binance-proxied, not honest Aster-native coverage).

## Recommended decision

Confirm the correct Aster funding/derivative_ticker genesis date (2023-07-22 native vs 2023-11-01
first-actually-captured vs 2024-01-01 launcher-documented), then run:

```bash
VENUES=ASTER DATA_TYPES=derivative_ticker YEARS="2023" \
  OVERRIDE_START_DATE=<confirmed-genesis> OVERRIDE_END_DATE=2023-11-01 \
  bash deployment-service/scripts/vm/launch-cefi-hl-aster-historical-backfill.sh
```

— safe/idempotent (write-only, no deletes, matches the original todo's own no-`[OPERATOR]`-gate reasoning) once the date
is confirmed. Also update the parent plan's leg (c) text to stop citing the retired
`launch-mtds-perp-funding-backfill-vm.sh --perp-protocols aster` command.

## Todos

- [ ] [DATA][OPERATOR] P2. Confirm the correct Aster funding genesis date for the 2023-07-22→2023-11-01 gap window
      (native vs Binance-proxied vs never-existed) — **OPERATOR-gated 2026-07-29 (main, BLK-a94f446d)**: this is an
      operator-recall decision (the 2026-06-17 confirmed-genesis intent), not worker-resolvable; slot-15 already
      researched it and re-blocked. Confirmed facts: 2023-11-01 = real earliest captured row; 2023-07-22→2023-10-31 =
      zero manifest rows ever; 2023-07-22 was the operator-confirmed Binance-proxied (synthetic) start. Interim guidance
      already given to workers: proceed on the 2023-11-01+ real floor (honest-absence-safe). Operator to decide ONLY
      whether the 2023-07-22→2023-11-01 Binance-proxied window is reconstructed or declared out-of-scope; then launch
      the scoped backfill via `launch-cefi-hl-aster-historical-backfill.sh` (command above) for whichever sub-window is
      confirmed real. (repo: market-tick-data-service + deployment-service). **Done when**: a full re-census of ASTER
      `derivative_ticker` manifest rows for 2023-07-22→2023-11-01 shows either genuine captured/empty_confirmed coverage
      (backfill ran) or a documented decision that the window predates real Aster activity (no backfill needed).

## Progress Log

- 2026-07-29T15:3xZ (slot 15, data_engineering): attempted to resolve the genesis-date ambiguity via external research
  (mirroring how the sibling margining-registry todo in this same batch was resolved via a live API check) — **this
  deepens the ambiguity rather than resolving it, do NOT act on it as a green-light to pick a date.** Public sources
  (Cointelegraph, CryptoSlate, The Block, Chainwire, The Defiant — Astherus/APX Finance merger press coverage) place
  Astherus+APX Finance's merger and the "Aster" rebrand/DEX launch at **2025-03-31**, with the native `ASTER` token
  launching 2025-09-17 — i.e. the real-world Astherus/Aster product's public history postdates ALL THREE candidate
  genesis dates in this doc (2023-07-22 / 2023-11-01 / 2024-01-01) by well over a year. This means the "Binance-proxied
  Astherus funding" label the source doc's 2026-06-17 operator-confirmed genesis note uses for pre-2024 data is most
  likely describing an internal/methodological construct (a synthetic funding-rate proxy our own pipeline computes from
  Binance data under an "Astherus" label) rather than tracking any real-world Astherus product timeline — so this is NOT
  a fact a web search can settle; the actual question ("what date did WE decide to start treating Binance-proxied
  synthetic Astherus/Aster funding as valid, and does the manifest reflect that decision correctly") is internal/
  operator-methodology-only. **Not resolved — still needs the original 2026-06-17 operator-confirmed-genesis
  conversation/decision-record consulted (not re-discoverable from either code or public sources), or a fresh operator
  ruling.** No VM launched, no date guessed, no code changed. Filed as a `/blocked` question from the parent plan's todo
  (`cross_cutting_satellite_ao_dispatch_batch1b-006`) rather than proceeding.
- 2026-07-29T20:19Z (slot 4, data_engineering): re-verified from scratch after a fresh pull — no operator answer to
  `BLK-a94f446d` yet (grepped the corpus for the id, checked recent commit history on this doc + the parent plan's todo,
  both confirm no change since main's `[OPERATOR]`-gate tag). All 4 sibling legs (a/b/d/e) remain resolved; this is the
  sole open leg on the parent todo, and it has no unblocked partial action available — the uncontested 2023-11-01+ floor
  is already fully captured (226,008 rows through 2026-07-27), so the ONLY remaining scope is the disputed
  2023-07-22→2023-11-01 window this blocker gates. Nothing to do until the operator answers. Released via
  `/skip-current-task {"reason_code": "BLOCKED"}` on the parent todo.
