---
doc_type: plan
title: Code readiness T1 — contracts, library and the external API surface
summary: >-
  Tranche 1 of the five-agent code-readiness push — makes unified-api-contracts, unified-trading-library and the external API surface code-complete against the four client artefacts. Owns the registry P0s every other tranche blocks on (venue asset-group resolution, the three disagreeing chain registries, the canonical-path oracle) plus the contract extensions T3 and T4 are waiting on.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-api-contracts, unified-trading-library, unified-trading-api, deployment-api, deployment-ui, unified-trading-system-ui]
scope: [engineer]
tags: [code-readiness, uac, utl, registry-hardening, external-api, tranche-1]
related:
  [
    /plans/epics/system_readiness_master.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /plans/audit/results/code_completion_scope_2026_08_19.md,
    /plans/audit/results/code_readiness_allocation_2026_08_19.json,
    /codex/14-customer-journeys/commercial-model/platform-architecture.html,
  ]
created: 2026-08-19
last_updated: 2026-08-19
parent_epic: system_readiness_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: refactor
estimate_baseline_ai_days: 20
estimate_calibrated_ai_days: 8
locked_by:
locked_since:
context_scope:
  [
    /plans/epics/system_readiness_master.md,
    /plans/audit/results/code_completion_scope_2026_08_19.md,
    /codex/12-agent-workflow/commit-push-flip-rule.md,
    /codex/12-agent-workflow/measurement-claims-discipline.md,
    /codex/06-coding-standards/quality-gates.md,
    /codex/05-infrastructure/per-tab-worktrees.md,
  ]
supersedes:
superseded_by:
depends_on:
source: >-
  Operator directive 2026-08-19 — allocate every active plan and issue across five parallel agents and drive the four
  client artefacts to code-ready, excluding manifest migration and data backfills.
assigned_role: backend_engineer
effort: max # multi-day autonomous tranche — 30-40 todos spanning several repos, cross-tranche contract edges
drift_direction: advance-code
---

# Code readiness T1 — contracts, library and the external API surface

> **Tranche 1 of 5.** Owned repos — **unified-api-contracts, unified-trading-library, unified-trading-api, deployment-api, deployment-ui, unified-trading-system-ui**. Allocated corpus —
> **62 docs** (11 spine, 2 excluded as data-movement), **130 open todos**
> at authoring. You are one of five agents running in parallel on disjoint repos.

**T1 is upstream of every other tranche.** Four of the five known cross-tranche blocking edges terminate here.
Land the contract extensions (todos 9-11) EARLY even if their consumers are not ready — an unconsumed field costs
nothing; a missing one stalls two agents for days.

## The goalpost — what "done" means (operator ruling 2026-08-19)

Everything in this tranche is **complete in code**. The ONLY things that may still be pending when this plan closes:

1. **Backfills still running** — batch data landing.
2. **Venue connectivity** — private feed and public feed, orders and trades.
3. **Market data live.**
4. **Testnets, where they exist.**
5. **Strategy archetypes code-ready for batch / paper / live — pending testing with real data.**

Anything outside those five that is not code-complete is REMAINING WORK. SSOT for the goalpost:
`/plans/epics/system_readiness_master.md` § "Definition of done".

**The acceptance test is the artefacts.** These three client-sendable documents must stop carrying `pending`,
`planned`, `partial`, `not built` or `unverified` on any claim that is not one of the five above:

- `/codex/14-customer-journeys/commercial-model/platform-architecture.html`
- `/codex/14-customer-journeys/commercial-model/platform-external-api-walkthrough.html`
- `/codex/14-customer-journeys/commercial-model/strategy-service-deep-dive.html`

Their status markers carry `owner: W1`…`W22` tags binding each claim to a workstream in
`/plans/epics/system_readiness_master.md`. Closing a W-item is what clears its marker. **Never clear a marker by
editing the HTML** — the marker is derived from real state; change the state, then re-derive.

## Standing rules for this tranche — HARD

- **Do NOT run backfills, manifest migrations, corpus sweeps or GCS deletes** (operator ruling 2026-08-19). Fixing
  the manifest-writer / path-registry / capture-status **code** is IN scope; launching the data movement is NOT.
  A todo whose only remaining step is "relaunch the VM" or "apply the delete" is marked `BLOCKED-OPERATOR` and left.
- **Do NOT request or wait on API keys / credentials.** Where a real credential is missing, build the adapter and
  the full code path anyway and mark the item `BLOCKED-CREDENTIALS` — never descope it. SSOT:
  `/codex/02-data/external-data-always-available-rule.md`.
- **Edit ONLY the repos this tranche owns** (listed above). Another tranche owns every other repo, and a same-file
  edit across two agents is the one thing the workspace concurrency model forbids. Need a change in someone else's
  repo? File it via the handoff protocol below — never reach across.
- **Every claim ≤ its measurement.** A proxy (line count, exit 0, a green test, a cached `origin/`) is not the
  property. Measure it or say you did not. SSOT: `/codex/12-agent-workflow/measurement-claims-discipline.md`.
- **Commit + push + flip the checkbox in the SAME turn**, with `<repo>@<sha>` evidence. SSOT:
  `/codex/12-agent-workflow/commit-push-flip-rule.md`.
- **Ship code only via** `bash scripts/quickmerge.sh "msg" --agent --files '<paths>'` from a `quality-gates.sh`-green
  tree. Doc/plan-only changes go via `bash scripts/dev/safe-doc-push.sh`.

## Cross-tranche handoff protocol

Five agents run in parallel on disjoint repos. When your work needs a change in a repo you do not own:

1. Append a `- [ ]` todo to the OWNING tranche's plan under its `## Inbound requests` section, tagged
   `[FROM-<your-tranche>]`, naming the exact symbol/file and what shape you need.
2. Commit that plan edit via `safe-doc-push.sh` (doc-only, no code).
3. Keep working — build your side against the contract you asked for, behind a feature flag or an adapter seam if
   it does not exist yet. Do not block, and do not edit their repo yourself.

**Known blocking edges at authoring time** (T1 is upstream of everyone — it runs first and fastest by design):

- T4 delta-proxy repricer generalization → needs T1 to extend UAC `QuoteInstruction` with
  `delta` / `gamma` / `underlying_instrument_id`.
- T3 + T4 strategy→execution reference triple → needs T1 to add `reference_position` and `credit` to
  `StrategyInstructionEnvelope`.
- T5 readiness dump's execution-instruction leg (the structural reason all 864 rows read `unverified`) → needs T4
  to expose a real per-venue instruction-path check.
- T5 coverage dump at `instrument_type` / `data_type` grain → needs T2 to land those axes in `coverage.json`.

## Your allocated corpus

The full, reproducible allocation lives in `/plans/audit/results/code_readiness_allocation_2026_08_19.json`,
regenerated by `scripts/plan-hygiene/allocate_code_readiness_tranches.py`. Every one of the 892 active plan/issue
docs is assigned to exactly one tranche, so nothing is orphaned and nothing is worked twice.

```bash
python3 -c "
import json
d=json.load(open('plans/audit/results/code_readiness_allocation_2026_08_19.json'))
for x in d['tranches']['T1-contracts-library-externalapi']['docs']:
    if not x['excluded_data_movement']:
        print(('SPINE ' if x['spine'] else '      '), x['priority'], x['open_todos'], x['path'])
"
```

**Work order**: `spine: true` docs FIRST, in priority order — those are the docs that back a presentation claim.
Then the tail. A doc flagged `excluded_data_movement: true` is skipped per the standing rules above; open its
todos only to confirm they are data-movement, then leave it.


## Inbound requests

> Other tranches append `- [ ] [FROM-Tn]` items here when they need a change in a repo you own. Work them at the
> priority they state — another agent is blocked on each one.

- [x] ✅ [FROM-T4] P2. **DONE — unified-api-contracts@43033d1152.**
      `ORDER_STATUS_TRANSITIONS[OrderStatus.PARTIALLY_FILLED]` now includes `CANCELLED` and `EXPIRED` alongside
      `FILLED`. Paired test `test_partially_filled_can_be_cancelled_or_expired` in `test_order_state_machine.py`
      asserts both new edges plus the existing `FILLED` edge and that both new terminals still reconcile
      afterward. QG green (13438 passed, 0 failed). Landed alongside no unrelated change — the codex doc was
      already amended per this request; nothing further needed there.

- [x] ✅ [FROM-T2] P2. **Acknowledged, already queued — see the `[BACKEND] P2` item below, no separate action
      needed on this flag itself.** The manifest-writer per-VM shard flush issue is entirely yours — T2 has no code to change.
      `/plans/active/issues/manifest_writer_per_vm_shard_flush_scales_with_shard_size_2026_07_28.md` was allocated
      into T2's tranche plan as a P1, but the writer lives in
      `unified-trading-library/unified_trading_library/manifest_writer/` and every remaining todo is UTL-side: the
      append-only "delta shard" pattern (P2), a reworded P3, and a `[SCRIPT] P3` verification gated on "once either
      fix above ships". Flagging so it does not sit unworked in a tranche that cannot action it. Its own doc
      priority is P2. No response needed if it is already queued.

- [x] ✅ [FROM-T2] P0. **ALREADY RESOLVED before this got picked up — unified-api-contracts@910d35da (slot-15,
      2026-08-20 05:20).** Verified independently rather than trusting the request's framing: the decision
      landed is "writer authoritative" — `_instrument_catalogue_contract.py` now declares the 41 rolled-up
      `CATALOG_COLUMNS` explicitly under `INSTRUMENTS_CATALOGUE_SCHEMA_VERSION`, keyed on `instrument_id`, and
      `test_instrument_catalogue_contract.py` pins zero violations on a writer-shaped frame. The 85-column
      `INSTRUMENTS_PARQUET_SCHEMA` mismatch this request describes was a CATEGORY ERROR, not a genuine drift —
      that schema documents the per-date raw `InstrumentRecord` parquet shape, not the aggregated catalogue
      roll-up `build_instrument_catalogue.py` actually produces; the two were never meant to be gated 1:1. Every
      UAC-side todo in `/plans/archive/issues/instruments_schema_not_locked_versioned_2026_08_18.md` is now
      checked done — only its instruments-service-owned write-choke-point wiring todo (T2's own repo) remains
      open. No further UAC action needed on this.
- [x] ✅ [FROM-T2] P0. **SUPERSEDED by the resolution immediately above — kept, not deleted, per the todo-count
      conservation rule (a checkbox flip never shrinks the total).** Original text follows verbatim.
      `INSTRUMENTS_PARQUET_SCHEMA` has never matched the catalogue writer — a decision is needed
      before B23's schema lock can be enforced anywhere. MEASURED 2026-08-20 by building B23 part 4's write-time
      gate in `instruments-service` and running it before shipping (then reverting it — shipping would have blocked
      production catalogue promotion for all five asset groups):

      - `build_instrument_catalogue.py`'s `CATALOG_COLUMNS` emits **41** columns; the contract declares **85**.
      - **4 of the 6 `required=True` columns are emitted by NO asset group**: `instrument_key`, `symbol`,
        `available_from_datetime`, `timestamp` (identical result for cefi, defi, tradfi, prediction, sports).
      - The writer's canonical identifier is **`instrument_id`** — `build_instrument_catalogue.py:279` states
        outright that "`instrument_id` is written as the canonical column (the helper also accepts
        `instrument_key`)". The contract requires `instrument_key`.
      - Same split on the date columns: writer emits `available_from`/`available_to`, contract declares
        `available_from_datetime`/`available_to_datetime`.
      - Wiring the gate turned 3 existing `promote_catalogue` tests red with 80 violations on a cefi frame.

      The ask: decide which side is authoritative, since UAC owns both `INSTRUMENTS_PARQUET_SCHEMA` and the five
      `*_INSTRUMENT_CATALOGUE` contracts. Tracked as a new P0 part 0 in
      `/plans/archive/issues/instruments_schema_not_locked_versioned_2026_08_18.md`.

- [x] ✅ [FROM-T2] P1. **Answered — T1's job here was to investigate and answer, which is done below; the
      population itself was correctly NOT changed (see the answer's own conclusion).** MEASURED 2026-08-20 by T1
      — the population question you asked for an answer to genuinely doesn't resolve cleanly your way, and here's
      why. `KNOWN_CHAINS`'s stated job (my own
      27ebc544b2 commit's docstring) is venue-suffix SPLITTING: recognising the `<CHAIN>` token in a live
      `<PROTOCOL>-<CHAIN>` venue string. Checked all ten against `ALL_DEFI_VENUES`
      (`v.upper().endswith("-" + CHAIN)`): **ZERO of the ten have any currently-registered venue with that
      suffix.** So by KNOWN_CHAINS's own stated purpose, none of the ten are a parsing gap the way
      SCROLL/PLASMA genuinely were (those had 4 live venues silently failing the split; these have none).
      **But that doesn't make this nothing** — your own table shows `AURORA` (2,725 captured) and `MANTLE`
      (1,537 captured) have REAL captured rows, meaning something DID write real data tagged with those chain
      values despite no venue-suffix path producing them. That points at a chain value coming from somewhere
      OTHER than venue-suffix parsing (a direct per-adapter chain declaration, a venue since renamed/retired
      from `ALL_DEFI_VENUES` post-capture, etc.) — which is a write-path question in MTDS/your repo, not a UAC
      registry-membership one. I can't safely trace that without reading your capture code, which is out of
      this tranche's scope. **My answer to your actual ask**: `KNOWN_CHAINS` is correctly scoped to its stated
      population (venue-suffix tokens) and should NOT have all ten added on the strength of manifest presence
      alone — that would conflate "a chain the manifest carries" with "a chain a live venue string encodes",
      exactly the distinction your own request asked me not to erase. If you trace AURORA/MANTLE's actual
      write path and it turns out a CURRENTLY-LIVE venue does need the suffix split (a venue naming pattern I
      didn't find, or a stale `ALL_DEFI_VENUES` entry), re-file with that specific venue name and I'll fix it
      the same way as SCROLL/PLASMA. `STARKNET`'s 0-captured rows are consistent with your own note that it's a
      deliberate CeFi exclusion, not evidence either way.

      Context: T2 removed three hand-rolled copies of this set in `instruments-service` so they now import
      UAC's — `instruments-service@2b482a1247`.
- [x] ✅ [FROM-T2] P1. **SUPERSEDED by the resolution immediately above — kept, not deleted, per the todo-count
      conservation rule.** Original text follows verbatim. The `KNOWN_CHAINS` gap fixed for SCROLL/PLASMA is
      still open for TEN more chains carrying 46,698 live manifest rows (STARKNET/AURORA/MANTLE/BLAST/MODE/
      METIS/MOONBEAM/CELO/FANTOM/GNOSIS). MEASURED 2026-08-20 against the live
      `gs://central-element-323112-honest-coverage/2026-08-19/coverage.json` (`by_chain.defi`): the DeFi
      manifest carries 23 distinct chains; `KNOWN_CHAINS` has 14; 10 manifest chains are outside it. Every
      `if chain in KNOWN_CHAINS:` consumer takes the ELSE branch for all ten. `ASTER` is in `KNOWN_CHAINS` but
      has ZERO DeFi manifest rows — over- and under-inclusive at once. Deliberately not assumed that all ten
      belong in `KNOWN_CHAINS`; the ask was to state which population it represents and reconcile against that.

- [x] ✅ [FROM-T4] P2. Pendle wired into the SIT cascade invariant — unified-api-contracts@b9f63f883.
      `DEFI_VENUE_TO_CONNECTOR_CLASS["pendle"] = "PendleConnector"` and `DEFI_VENUE_TO_GATE_MARKER["pendle"] =
      "PENDLE"` added; `pendle` removed from `tests/data/execution_service_venue_reachability_baseline.json`
      (`karak` deliberately kept — separately tracked for decommission, not part of this request). MEASURED
      before/after rather than assumed: the invariant genuinely FAILED with a stale-baseline-entry assertion
      before the baseline edit, then 11/11 passed after — confirming pendle is now really reachable, not just
      that the dict has an entry. LEND-only caveat encoded as an inline comment on the dict entry (not silently
      widened): `PendleConnector.withdraw()` stays simulation-only per its own docstring, so a future full-family
      assertion needs an explicit carve-out for this venue. QG green (1076s — slow, shared-slot contention, but
      real exit 0 captured directly). Evidence: `unified-api-contracts/tests/
      test_execution_service_venue_coverage_cascade_invariant.py`,
      `tests/data/execution_service_venue_reachability_baseline.json`.

- [x] ✅ [FROM-T4] P1. **DONE — all 4/4 shipped.** `WithdrawInstruction`/`RepayInstruction` landed first
      (`unified-api-contracts@f5fc118ae1`); `LpMintInstruction`/`LpBurnInstruction` landed 2026-08-21 exactly per the
      shape T1 proposed below — `unified-api-contracts@d751e743` (+ `@3204e607` JSON round-trip tests), verified
      against `unified_api_contracts/internal/architecture_v2/schemas.py` (both classes present, both in the
      `StrategyInstructionV2` union) and `merge-base --is-ancestor` against `origin/live-defi-rollout`. T4's BATCH
      settlement gap is now closed 5/5 (`CONVERT_DUST`/`WITHDRAW`/`REPAY`/`LP_MINT`/`LP_BURN` all have dataclasses).
      Also folded into the codex post-phase audit — `/codex/04-architecture/strategy-execution-protocol.md`'s
      instruction-action table updated to reflect the shipped shape (`unified-trading-pm@0dd2475e82`). Original
      request text follows verbatim for provenance.
      Original ask, MEASURED 2026-08-20 by T4 closing its "Close the BATCH settlement gap" todo:
      `InstructionActionV2` has 16 members; `execution_service/backtest_v2/action_handlers.py`'s
      `resolve_settlement` dispatches on `isinstance(instruction, <Type>)` over `StrategyInstructionEnvelope`
      subclasses; `WITHDRAW`/`REPAY`/`LP_MINT`/`LP_BURN` had enum members but no dataclass anywhere in UAC
      (`CONVERT_DUST` was already fixed the same way, `execution-service@6f664e80a0`).
      **Shipped `unified-api-contracts@f5fc118ae1`**: `WithdrawInstruction` (protocol/asset/
      `target_supplied_amount`, rate-matched inverse of `LendInstruction`) and `RepayInstruction` (protocol/asset/
      `target_debt_amount`, inverse of `BorrowInstruction`), both added to the `StrategyInstructionV2` union, both
      export levels (`architecture_v2/__init__.py`, `internal/__init__.py`), 4 tests
      (`tests/internal/unit/test_withdraw_repay_instructions.py`). T4's `resolve_settlement` can now add 2 more
      `isinstance` branches, mechanically, same pattern as `CONVERT_DUST`.
      **`LpMintInstruction`/`LpBurnInstruction` remain open** — genuinely need the DEFI_LP position shape specified
      first (concentrated-LP-specific fields: pool identity, tick range or equivalent, NFT position id if
      Uniswap-V3-shaped — none of that exists anywhere in this repo today, confirmed by grep for
      `tick_lower`/`pool_id`/`lp_token`/`token0`/`token1` across `architecture_v2/schemas.py`, zero hits). T1 will
      not guess this shape under time pressure and ship something T4 has to rework — state the fields
      `LP_MINT`/`LP_BURN` actually need (the orchestrator already dispatches to
      `UniswapConnector.mint_position()`/`burn_position()` per the enum's own comment — read those signatures for
      the real shape) and T1 will add both in one pass.

      **Shape specified 2026-08-20, T4's call as asked.** Read BOTH real connector families before proposing — they
      genuinely differ, not just in naming: `UniswapConnector.mint_position(token0, token1, fee_tier,
      sqrt_price_lower, sqrt_price_upper, amount0_desired, amount1_desired, amount0_min=None, amount1_min=None,
      deadline_offset_seconds=1800)` / `burn_position(token_id, liquidity, amount0_min=0, amount1_min=0,
      deadline_offset_seconds=1800, burn_nft=False)` (`execution_service/defi_execution/protocols/uniswap.py:450,
      500`) is NFT-position-based with sqrt-price bounds; `OrcaConnector.add_liquidity(whirlpool, amount_a,
      amount_b, lower_tick, upper_tick)` / `remove_liquidity(whirlpool, liquidity_amount)` and Raydium's identical
      shape (`orca.py:168,292`, `raydium.py:181,304`) are pool-address + raw-tick, no NFT. Proposed generalized
      schema (superset, protocol-specific fields nullable):

      ```python
      class LpMintInstruction(StrategyInstructionEnvelope):
          action: Literal[InstructionActionV2.LP_MINT] = InstructionActionV2.LP_MINT
          protocol: str  # "uniswap_v3" | "orca" | "raydium" | ...
          pool_id: str  # pool/whirlpool address (Uniswap: derivable from asset_a/asset_b/fee_tier, still populated for logging)
          asset_a: str
          asset_b: str
          amount_a_desired: Decimal
          amount_b_desired: Decimal
          amount_a_min: Decimal | None = None  # slippage floor -- Uniswap's connector already enforces this;
          amount_b_min: Decimal | None = None  # Orca/Raydium's connectors do NOT yet -- a real gap the W15 security
                                                # audit's checklist point 4 (slippage/deadline bounds) will surface
          lower_tick: int
          upper_tick: int  # universal range representation -- Orca/Raydium's native input; execution-service's own
                            # wiring converts to sqrt_price_lower/upper before calling Uniswap's mint_position (a
                            # T4-side wiring detail, not a UAC schema concern)
          fee_tier: int | None = None  # Uniswap-specific tiered-pool selector; None for single-pool-per-pair protocols

      class LpBurnInstruction(StrategyInstructionEnvelope):
          action: Literal[InstructionActionV2.LP_BURN] = InstructionActionV2.LP_BURN
          protocol: str
          pool_id: str
          position_token_id: str | None = None  # Uniswap V3's NFT position id; None for Orca/Raydium (no NFT)
          liquidity_amount: Decimal  # universal across all 3 -- Uniswap's `liquidity` param, Orca/Raydium's
                                     # `liquidity_amount` param, identical concept
          amount_a_min: Decimal | None = None
          amount_b_min: Decimal | None = None
      ```

      `deadline_utc` reuses the base envelope's existing field rather than a redundant offset-seconds param.
      Once these land, T4's `resolve_settlement` gets 2 more `isinstance` branches, closing the BATCH settlement
      gap todo 5/5, matching the pattern `CONVERT_DUST`/`WITHDRAW`/`REPAY` already established.

- [ ] [FROM-T2] P1. **New declared registry: which leagues does bookmaker venue X actually offer.** Operator
      ruled 2026-08-22 to extend instruments-service's Layer-1 completeness gate to
      `(venue, instrument_type, data_type, league_id)` grain for sports. No live sports adapter expresses true
      per-bookmaker league scope (`odds_api_adapter.py` fetches a sport-wide pool for all ~21 bookmakers alike;
      `betfair_adapter.py` does ad hoc substring matching, no canonical mapping). Closest existing thing —
      `sports_bookmaker_league_coverage.BOOKMAKER_LEAGUE_COVERAGE` — is manifest-derived, so it cannot feed the
      EXPECTED-side denominator (`expected_universe.py`'s own hard rule: never derive EXPECTED from the
      manifest — circular). **Ask**: declare `EXPECTED_BOOKMAKER_LEAGUE_COVERAGE: dict[str, frozenset[str]]`,
      seeded from the current `BOOKMAKER_LEAGUE_COVERAGE` snapshot (bootstrapped-then-frozen, same pattern as
      `VENUES_BY_ASSET_GROUP`), covering at minimum `odds_api`'s ~21 bookmakers + `betfair`'s 3 sub-venues. T2
      consumes it in `expected_universe.py`/`check_enumeration_completeness.py` (own repo, already scoped) once
      it lands. Repo: unified-api-contracts.

- [ ] [FROM-T2] P1. **New declared registry: which InstrumentRecord fields are mutable (get historised).**
      Operator ratified 2026-08-22 the current-state + narrow-change-log design for
      `instruments_catalogue_definitions_and_field_history_2026_08_17.md` (over monthly-snapshots-only and
      full-row-versioning — the log-replay approach is the only one that resolves an intra-month change
      correctly at a cost proportional to actual changes, not row count). **Ask**: declare the mutable-field set
      explicitly — only tick_size/contract_size/DeFi lending risk params are believed mutable today (per the
      design doc's own table), DeFi contract-address immutability still needs verifying (tracked separately,
      `cross_cutting_satellite_ao_dispatch_batch15_2026_08_17.md` item 12). A field NOT declared mutable that
      later changes silently is the correctness bug this whole design exists to prevent — the declaration is the
      control. T2 builds the monthly catalogue + field-change-log writer (own repo, instruments-service) against
      whichever fields land here. Repo: unified-api-contracts.

## Todos

### Registry SSOT — the P0s everything else is wrong without

- [x] ✅ [BACKEND] P0. `unified_api_contracts.execution.get_venue_asset_group()` fails closed —
      unified-api-contracts@d4cded41b8. Root cause MEASURED (not the reported one): the lookup was keyed on
      capability-declaration `source` names (`binance`, `aave` — 55 keys) while callers pass `PROTOCOL-CHAIN`
      venue slugs, so the two vocabularies had ZERO overlap and all 209 registered venues missed. Now delegates to
      the existing fail-closed `classify_venue_asset_group()` SSOT, keeps the capability-source table as an
      explicit second step (29 of 55 source keys resolve to nothing in the venue vocabulary, so deleting it would
      have lost real behaviour), and raises `UnknownVenueAssetGroupError` on a real miss. Caller migration was a
      no-op: a fleet-wide grep found ZERO code callers — every hit was docs/plans. Also fixed a collision found in
      the classifier itself (bare `COINBASE` → `defi` via false-match on `COINBASE-ETHEREUM`, the same trap its own
      comment documents for `BINANCE`) plus two systematic invariants so the next one fails the suite. Evidence:
      `/plans/archive/2026_08/issues/uac_get_venue_asset_group_silently_returns_cefi_for_all_venues_2026_08_19.md`.
- [x] ✅ [BACKEND] P0. Chain registries reconciled to ONE vocabulary SSOT — unified-api-contracts@27ebc544b2.
      `ChainKind` is now declared the vocabulary SSOT in its own docstring, with the other two DERIVING their legal
      values from it (the issue's own "derive from it or die" option A) — they are NOT merged, because measurement
      showed they own three genuinely different concerns: `ChainKind` = vocabulary, `KNOWN_CHAINS` = UPPERCASE
      token recognition for splitting `<PROTOCOL>-<CHAIN>` venue strings, `VENUE_CHAIN_MAP` = venue→chain for
      shared-wallet routing (which legitimately covers only wallet-sharing venues, so "4 of 192" is its scope, not
      a gap). Added `ChainKind.PLASMA` and taught `KNOWN_CHAINS` to recognise SCROLL + PLASMA. Six containment
      invariants now pin all three together. **Two premises in this todo were measured WRONG and corrected in the
      issue doc**: `KNOWN_CHAINS` held 12 entries, not 10; and `starknet` was NOT added, because its cited
      justification `EXTENDED-STARKNET` is a **CeFi** venue absent from `ALL_DEFI_VENUES` — it cannot justify an
      entry in a DeFi-venue token-recognition set. Evidence:
      `/plans/active/issues/three_chain_registries_disagree_none_authoritative_2026_08_19.md`.
- [x] ✅ [BACKEND] P0. Consumer migration — **a no-op by construction, and that is the correct outcome.** No
      registry was retired (see above: all three survive, owning different concerns), so there is no renamed or
      removed entity for a consumer to be migrated off, and
      `/codex/02-data/entity-rename-and-split-consumer-migration-rule.md` does not apply. Consumers were still
      enumerated to confirm this: `ChainKind` (6 UAC modules + MTDS `umi_tick_provider.py`), `KNOWN_CHAINS`
      (instruments-service `writers.py`/`catalogue.py` + MTDS `rebuild_mtds_manifest.py`, all reading membership,
      none binding the name into a path or filename), `VENUE_CHAIN_MAP` (UAC-internal only). Every one keeps
      working and now gets a MORE complete answer. The re-check of whether any already-written chain-scoped output
      was affected by the SCROLL/PLASMA non-recognition is data verification in T2-owned repos — filed as an
      inbound request on T2's plan, not silently assumed clean.
- [x] ✅ [BACKEND] P0. `canonical_path_violations()` validates the filename stem — **already shipped before this
      tranche existed; this todo was STALE, not outstanding.** Landed `unified-api-contracts@d40c5d7d` +
      `@502ef57e` (+ `market-tick-data-service@953679de` for the writer side). VERIFIED BY MEASUREMENT rather than
      by trusting the issue doc's own "how it shipped" section: `CanonicalViolationClass` exists as a StrEnum whose
      `ID_FORM` member is documented as "The FILENAME STEM: whether the per-instrument shard is named for a …"; the
      `id_form` violation list is populated at 4 distinct sites in
      `unified_api_contracts/canonical/_partition_path_canonicality.py`; and the default
      `violation_classes=None` reports BOTH classes, so the pre-2026-07-20 structure-only behaviour is now the
      explicit opt-in (`frozenset({CanonicalViolationClass.STRUCTURAL})`) rather than the silent default. The
      source issue is still `status: open`, but its 2 remaining open todos are unrelated `[DATA]` P2/P3 findings
      from 2026-08-17, not this oracle fix. Evidence:
      `/plans/active/issues/canonical_path_oracle_blind_to_filename_stem_2026_07_20.md` § 9.
- [x] ✅ [BACKEND] P0. `canonical_path_violations()` VALUE blindness closed — unified-api-contracts@03e8e90f. Both
      halves done: the oracle is EXTENDED (new `CanonicalViolationClass.VALUE` checks `venue=`/`chain=`/
      `data_type=`/`instrument_type=` against `VENUES_BY_ASSET_GROUP`/`ALL_VENUES`+`ALL_DEFI_VENUES`,
      `DATA_TYPES_BY_ASSET_GROUP`/`ALL_DATA_TYPES`, `InstrumentType`, `ChainKind`) AND the residual blindness is
      explicit in the return type (a named `DEFAULT_VIOLATION_CLASSES` constant, not a bare `None` default).
      **VALUE is deliberately OPT-IN — the load-bearing decision, not a shortcut.** Measured before writing a
      line: `canonical_path_violations()` feeds a WRITE boundary that RAISES
      (`market-tick-data-service/.../symbol_rules.py:517`), and this exact module already documents the failure
      mode — on 2026-06-23 an over-eager venue guard froze the deribit/hyperliquid/binance live VMs for hours on
      the legitimate `BINANCE-FUTURES` token. `violation_classes=None` still answers exactly STRUCTURAL + ID_FORM;
      `canonical_path_violations_classified()` reports VALUE unconditionally (an audit has no write path to
      break). Regression test asserts a fictional-venue path still returns `[]` under the default.
      **Membership is case-INSENSITIVE** — measured, not assumed: `ALL_VENUES`/`InstrumentType` are UPPERCASE,
      `ChainKind` is lowercase, `ALL_DATA_TYPES` is genuinely mixed. A missing axis is silent (absence is already
      a STRUCTURAL finding). 8 tests. QG green — real exit code captured directly (538s), never through a pipe.
      Evidence: `/plans/active/issues/canonical_path_oracle_blind_to_filename_stem_2026_07_20.md` (parent issue;
      the VALUE todo was its own sibling P0 in this plan, not filed as a separate issue doc).
- [x] ✅ [BACKEND] P1. Both resolved — unified-api-contracts@0d7afa29e.
      **Venue→chain**: NOT a merge — measured this was never a duplicate needing one. `get_chain_for_protocol()`
      derives the chain via the SAME `split_glued_venue_chain()` primitive the chain-registry SSOT already uses,
      resolving 7 of strategy-service's 8 hardcoded `_STAKING_PROTOCOL_CHAIN` entries with zero new data — the
      information was never missing from UAC, only queried through the wrong mechanism. `coinbase_staking` is
      the sole genuine exception (zero `ALL_DEFI_VENUES` matches — it's Coinbase's custodial retail product, not
      an on-chain protocol), handled via one documented exception entry. 12 tests verbatim-copy strategy-
      service's own 8 expected values as the ongoing cross-repo parity check. Migration filed as a `[FROM-T1]`
      inbound request on T3's plan (out of tranche scope — strategy-service is theirs).
      **VenueFeature/VenueCapability**: retyping VenueCapabilityV2 to reuse VenueCapability directly would have
      LOST the 6 genuinely-unique account-structure members (`CROSS_MARGIN`/`PORTFOLIO_MARGIN`/`SUBACCOUNT`/
      `ATOMIC_MULTI_LEG`/`DARK_POOL`/`BACK_LAY_EXCHANGE`), so full retyping was wrong. Instead removed the 6
      REDUNDANT members that duplicated `VenueCapability` under different spelling (`FLASH_LOAN`/
      `NATIVE_STAKING`/`LP_PROVISION`/`OPTIONS_TRADING`/`PERPS_TRADING`/`SPOT_TRADING`) — measured zero
      fleet-wide call sites constructed any of them first, so removal changed no live behaviour;
      `VenueCapabilityV2.supported_operations: list[str]` already existed as the free-form home for
      action-level data, so `.features` was never actually the right place for these. 3 tests pin the surviving
      vocabulary and assert zero remaining name collisions between the two enums. QG green (214s). Evidence:
      `/plans/archive/2026_08/registry_ssot_hardening_2026_08_16.md`.
- [x] ✅ [BACKEND] P1. **STALE — already resolved weeks before this tranche existed; closed by measurement, not
      new code.** Every code-level todo in the source issue is checked done: sports registries 1+3 confirmed
      structurally one SSOT (registry 1 imports `league_data.SOURCE_COVERAGE_START` directly — not a duplicate
      needing a merge); registry 2's disconnect from registry 1 closed via a permanent CI falsifier
      (`unified-api-contracts@09169cfe`, `scripts/check_coverage_floor_registry_drift.py` +
      `tests/unit/test_coverage_floor_registry_drift.py`, wired into `quality-gates.sh`) with a
      shrinking-ratchet `KNOWN_DIVERGENCES` baseline (a stale entry whose pair no longer disagrees is itself a
      failure); all 8 confirmed CeFi value mismatches fixed and verified against live manifest data
      (`unified-api-contracts@3d24f147c`), baseline shrunk 16→10 tracked divergences. The one item still open in
      that issue (line ~431, `[DATA] P3`, re-verify a HYPERLIQUID backfill VM) is data-side and explicitly out
      of this tranche's no-backfill scope. Evidence:
      `/plans/active/issues/coverage_floor_registries_no_cross_propagation_2026_07_17.md`.
- [x] ✅ [BACKEND] P1. **STALE — already resolved before this tranche existed; closed by measurement.** The
      exact CME/ICE cell this todo cites is fixed — `unified-api-contracts@fa9cece5` "two-layer data-type-
      validity combinator redesign", confirmed a real ancestor of `origin/live-defi-rollout` (not a doc claim
      taken on faith). Every `[CODE]`/`[DESIGN]` todo in the source issue is checked done (finding 1 CME/ICE
      fix, finding 2 the two-layer target-shape redesign, DeFi vocabulary reconciliation, dead-code deletion,
      31-DeFi-venue capability audit). Only 2 items remain open, both `[DATA] P2` — a prod full-history backfill
      "IN PROGRESS" and its terminal-state verification — both explicit data-movement, out of this tranche's
      no-backfill scope. Evidence:
      `/plans/active/issues/uac_data_type_validity_combinator_fragmentation_2026_07_07.md`.

### Contract extensions — unblock T3 and T4 EARLY

- [x] ✅ [BACKEND] P0. UAC `QuoteInstruction` extended with `delta`, `gamma`, `underlying_instrument_id` —
      unified-api-contracts@6be4b136d7. **T4 IS UNBLOCKED on this edge.** All three are optional; `None` reproduces
      exactly the previously-hardcoded `delta=1.0` / `underlying_instrument_id=instrument` self-underlying case, so
      no existing construction changes meaning. Semantics match `DeltaProxyRepricer._reprice()` as already
      implemented (`effective_delta = delta + gamma * underlying_move`), verified by a test that computes that
      formula from schema-carried values. Also documented `refresh_cadence_ms` as the STRATEGY-side cadence
      specifically — the issue is explicit that conflating it with execution's faster tick-driven loop is a design
      error. 5 tests incl. a JSON round-trip (the instruction crosses the EventTransport seam).
- [ ] [BACKEND] P0. **OPERATOR RULING 2026-08-22 — resolves the apparent tension flagged in the 2026-08-21
      close-out pass below. The fabric snapshot contract GOVERNS. Q12's named field list described the required
      ECONOMIC CONTENT, not flat scalar fields to place directly on every `StrategyInstructionEnvelope`.**
      Verbatim ruling: "The fabric model does not prohibit scalars; it prohibits collapsing vectors and matrices
      into misleading scalars." Concept → correct representation mapping the operator specified:
      - Reference price → `F_i0`: scalar per output instrument, with price convention and units.
      - Reference position → `q_0`: snapshot-level vector keyed by canonical risk dimension.
      - Credit → `c_i`: typed per instrument/side/action; define whether already included in `F_i0`.
      - Reference position adjustment → `a_i0`: scalar per output instrument.
      - Position response → `A_i`: keyed row/vector against position dimensions — not one scalar unless
        genuinely one-dimensional.
      - Delta/Jacobian → `J_i`: keyed factor vector. Gamma/Hessian → `H_i`: sparse keyed factor-pair matrix.
      - Theta → `Θ_i`: scalar with an explicit time unit.
      - Cross-sensitivities → optional sparse `B_i` or equivalent typed structure.

      **Explicit instruction — do not ship the literal Q12 field list, and do not wait for the full fabric spec
      (Parts II-V) to be written**: "Implement a minimal versioned `StrategyModelSnapshot` now: snapshot-level
      keyed `z0` and `q0`; per-instrument `reference_price`/`F_i0`; typed `credit` and reference adjustment; keyed
      `J_i`; sparse keyed `H_i`; unit-qualified `Theta_i`; and keyed position-response row `A_i`." The instruction
      envelope references the snapshot/model generation and relevant factor/position watermarks — carries
      `model_snapshot_id`/`model_generation`/`factor_state_epoch`+`sequence`/`position_state_epoch`+`sequence`/
      instruction-action data; the immutable `StrategyModelSnapshot` itself carries `F_i0`, `z0`, `q0`, `J_i`,
      `H_i`, `Θ_i`, `A_i`, `c_i`, validity limits and watermarks. **Include dimension IDs, units, inclusion
      conventions, and validity limits so no coefficient is ambiguous or double-counted.** This unblocks
      implementation without locking into the wrong (flat-scalar) shape. Now bounded, real code work — build
      `StrategyModelSnapshot` in UAC per this shape, then wire `StrategyInstructionEnvelope` to reference it.
      **2026-08-21 close-out pass's original finding, preserved for context** (still the accurate diagnosis of WHY
      this was ambiguous, now resolved by the ruling above): Q12-Q16 themselves ARE answered (confirmed against
      `/codex/04-architecture/cross-domain-state-fabric.md` § 14, "Closed since first publication" +
      "RESOLVED 2026-08-21" banner, and the issue doc's own "OPERATOR RULING 2026-08-21" section). But that same
      ruling explicitly says the implementation vehicle is the fabric's **snapshot/factor-state contract**
      (per-instrument `J_i`/`H_i`/`Theta_i` against canonical factors, in a versioned snapshot with watermarks) —
      **NOT** literal scalar delta/gamma/theta fields bolted onto `StrategyInstructionEnvelope`. The ruling's own Q12
      answer then names a concrete field list (`references: list[InstrumentReferenceEntry]` with per-entry
      `reference_price`/`reference_position`/`credit`/`position_adjustment_bps_per_unit_risk`/
      `sensitivity_coefficient`/`second_order_coefficient`/`time_decay_coefficient`) that reads as exactly those
      scalar-shaped fields the same paragraph just said not to build — an apparent internal tension in the ruling
      text itself, not resolved by re-reading it twice. Separately, the fabric doc's own "Not settled here" §14 states
      Parts II-V of the restructured spec (per-profile detail, archetype manifests) don't exist yet, so the stated
      implementation vehicle isn't buildable code today either way. Shipping the literal `InstructionReferenceEntry`
      field list would risk re-committing exactly the "wrong shape" mistake the operator already caught once
      (2026-08-19 scalar-vs-vector correction, same issue doc). This is a genuine design/architecture judgment call,
      not a coding task — needs the operator to confirm which of the two readings governs before this becomes
      bounded work. Was previously tagged as merely needing "a ruling on Q12-Q16"; that framing is now stale since
      the ruling landed — retagged to reflect the real remaining gap.
      **UNBLOCKED 2026-08-21 in DIRECTION, shape governed by the fabric SSOT**: operator answered the
      legacy Q12-Q16 set (vector one home; per-entry matrix incl. optional theta; venue nested per-instrument;
      per-entry credit/trigger/coefficient) — but Q12-Q16 were superseded by the factor-state model, so the
      implementation shape is `/codex/04-architecture/cross-domain-state-fabric.md` (R1-R16 snapshot/factor
      contract), with those answers as constraints. Position vectors are RESOLVED (fabric R22, reconfirmed by operator 2026-08-21); the five Wave-0 rulings were ALL RESOLVED 2026-08-21 (stale "still open" corrected 2026-08-22 — see the repricer-generalization issue doc §15 item 5 for the five resolutions; the remaining gap is solely the fabric-vehicle-vs-literal-field-list tension + fabric Parts II-V absence described below). Add `reference_position` to `StrategyInstructionEnvelope`. **The shape this
      todo names (`dict[venue, Decimal]`, "same shape as the existing price leg") is SUPERSEDED** — the source issue
      carries a dated correction banner from a later same-day operator revision ruling that shape incomplete: it
      solves the venue axis but not the INSTRUMENT axis, since a strategy instance holds a universe of instruments.
      The replacement (`references: list[InstrumentReferenceEntry]`) is published in that issue under the heading
      **"Proposed shape (illustrative — not finalized; this is what needs resolving, not what's decided)"** followed
      by **"Open questions for the operator — do not resolve unilaterally"** (Q12-Q16). Implementing the todo's
      literal text would ship the rejected shape; implementing the vector would answer five questions explicitly
      reserved for the operator. **Needs: a ruling on Q12-Q16**, then this becomes a bounded code task.
      Evidence: `/plans/active/issues/execution_delta_proxy_repricer_generalization_2026_08_18.md`.
- [ ] [BACKEND] P0. **RESOLVED by the same 2026-08-22 operator ruling documented in full on the `reference_position`
      todo immediately above — not repeating verbatim.** `credit` maps to `c_i`: "typed per instrument/side/action;
      define whether already included in `F_i0`" — carried on the `StrategyModelSnapshot`, not as a flat envelope
      scalar. Ship together with `reference_position`/`StrategyModelSnapshot` above; do not implement separately
      (the ruling treats the whole coefficient set as one typed snapshot, not independent fields landing
      piecemeal). **RE-CHECKED 2026-08-21 (close-out pass) — same finding as
      `reference_position` immediately above: Q12-Q16 answered, but the ruling's stated implementation vehicle (the
      fabric snapshot/factor-state contract) vs. its own literal per-entry field list are in apparent tension, and
      Parts II-V of the fabric spec don't exist yet. Not re-explaining verbatim — see the note above.**
      **UNBLOCKED 2026-08-21 in direction, same fabric-SSOT governance as above** (credit is per-entry,
      optional, strategy-owned — consistent with the fabric contract's `c_i` term). Add the `credit` leg to `StrategyInstructionEnvelope`. Formerly same gate as
      `reference_position` above — Q14 asks whether `credit` varies per-entry or is one policy shared across the
      vector, which cannot be answered without first resolving Q12 (where the vector lives). Landing `credit` as a
      flat envelope field now would re-commit the exact scalar-shape regression the operator caught. Note the
      design IS settled on two points that survive whichever way Q12-Q16 land: `credit` is OPTIONAL (a "flavor",
      not mandatory — pure-passive, fire-immediately and patient-then-escalate are all valid consumers) and
      strategy-OWNED/strategy-COMPUTED with execution merely consuming it.
      Evidence: `/plans/active/issues/execution_delta_proxy_repricer_generalization_2026_08_18.md`.
- [x] ✅ [BACKEND] P1. `OrderStatus` advanced to the full 9-state machine — unified-api-contracts@a3c572f8.
      **T4 is unblocked on this edge.** `FAIL_OUTBOUND` and `RECONCILED` now exist, and the machine ships with
      them — `ORDER_STATUS_TRANSITIONS` (transcribed edge-for-edge from the codex diagram),
      `TERMINAL_ORDER_STATUSES`, `is_terminal_order_status()`, `is_legal_order_transition()` — exported at all
      four package levels so consumers reach them through the top-level `unified_api_contracts` facade.
      **The rename shipped WITHOUT breaking anything, by design**: `PENDING`/`OPEN` became `PENDING_NEW`/`NEW`
      with the old names retained as enum ALIASES (`OrderStatus.PENDING is OrderStatus.PENDING_NEW` is True,
      wire values byte-identical), so nothing already persisted or published is re-encoded and none of the 24
      execution-service call sites break. That aliasing is a deliberate, tracked exception to the no-shims rule,
      taken because the entity-rename SSOT demands consumers migrate in the SAME change while this tranche is
      forbidden from editing execution-service — resolution is filed as a `[FROM-T1]` request on T4's plan, not
      left open-ended. MEASURED basis for calling aliasing safe: fleet-wide there is NO `.name`-based,
      `OrderStatus[...]`, `len(OrderStatus)` or iteration coupling, so no consumer can observe the rename.
      9 tests pin the enum against the codex state table (incl. that the original seven wire values are
      unchanged, and that aliases resolve by IDENTITY rather than merely comparing equal). QG green — real exit
      0 captured without a pipe, 273s; landing verified by `merge-base --is-ancestor`, not by exit code.
      **Deliberately NOT widened**: the codex diagram draws exactly one edge out of `PARTIALLY_FILLED` (full
      fill), so that is what the map encodes — real venues do cancel partially-filled orders, but the doc is the
      SSOT and the map is its projection, so amending it is a codex change first. Filed as a `[FROM-T1]` P2
      question on T4's plan rather than guessed at. Evidence:
      `/plans/archive/2026_08/issues/order_state_machine_ssot_vs_uac_orderstatus_2026_07_31.md` (archived
      2026-08-21, resolved).
### Walkthrough feedback 2026-08-21

- [ ] BLOCKED-OPERATOR-DECISION [AGENT] P0. Execute the registry cluster of the 2026-08-21 walkthrough feedback,
      tracked in `/plans/active/walkthrough_feedback_remediation_2026_08_21.md` (todos live there — this plan is
      over the line cap). **2026-08-21: all T1-actionable items in that cluster now closed** — the 12 unresolved
      venue/data_type pairs (`unified-api-contracts@f79cd936`, a concurrent session's fix, independently verified
      0 unresolved of 683 triples), the DeFi venue-set dedup, and the CeFi instrument_type roster over-fan are all
      shipped (no longer in that plan's open-todo list). **One item remains, genuinely operator-gated, not
      T1-forceable**: bucketing the 23 declared-but-unbucketed DeFi venues requires an operator ruling on which of
      20 `pipeline`-phase venues are actually IS-producible/ready to flip to `live` — a readiness call, not a
      registry-hygiene fix. See that plan's own todo for detail.

### W5 — venue registry completeness

- [ ] BLOCKED-OPERATOR-DECISION [BACKEND] P0. Populate `VenueCapabilityV2.collateral_rules` / `MarginSpec` for
      EVERY venue. The schema exists and strategy-service risk-v2 already consumes it, but zero venues are
      populated, so every risk-v2 read degrades silently to "no data". **2026-08-20: T1 investigated and
      deliberately did not fabricate this.** This is "population, not schema design" per the research doc itself —
      real per-venue collateral/margin data (LTV ratios, haircuts, margin tiers) for 192+ venues, feeding a live
      risk system. Getting these wrong could cause real financial harm; this needs genuine data-research (a
      credential-gated data source or a manual research pass), not code. Evidence: epic W5 +
      `/plans/audit/results/venue_transfer_custody_collateral_research_2026_08_18.md`.
- [x] ✅ [BACKEND] P1. `TransferCapabilityV2` added to `VenueCapabilityV2` — unified-api-contracts@45a545e5ad.
      New fields, schema only (population is separate, tracked work, per this todo's own text):
      `copper_eligible`/`ceffu_eligible` (kept independent — CEFFU is a specific custody-provider identity Copper
      routes on behalf of, not a synonym), `manual_transfer_eligible`, `prime_broker_eligible: list[str]` (an
      open-set of broker names, e.g. `["IBKR", "Alpaca"]`, not a closed enum — a new prime-broker integration
      never needs a schema edit). Every field defaults to the eligible-nowhere state. Field set sourced directly
      from `/plans/audit/results/venue_transfer_custody_collateral_research_2026_08_18.md`, no invented names.
      5 tests incl. a JSON round-trip. QG green (481s, full 13k+ suite). W22 transfer routing is now unblocked on
      the schema side; still needs real per-venue population before W22 can consume live values.
- [x] ✅ [BACKEND] P1. W8 weightings SSOT declared — unified-api-contracts@e55fc5a9d. New `WeightingDimension`
      enum (`PORTFOLIO_PER_CLIENT` / `ARCHETYPE_LEVEL`, deliberately binary) plus `ALLOCATOR_ARCHETYPE_DIMENSION`,
      a TOTAL mapping over all 17 `AllocatorArchetype` members. Grounded in real terminology, not invented:
      read `strategy-service/strategy_service/portfolio_allocator/archetypes_base.py` +
      `archetypes.py`/`archetypes_simple.py`/`archetypes_rank.py` first — `AllocatorArchetype` was ALREADY a
      UAC-owned enum (strategy-service imports it via `from unified_api_contracts.internal import
      AllocatorArchetype`), so this is additive to the existing contracts registry, not a new one. The 8 generic
      engines (FIXED/PNL_WEIGHTED/SHARPE_WEIGHTED/RISK_PARITY/KELLY/MIN_CVAR/REGIME_AWARE/MANUAL) weight
      `StrategyInputSeries.strategy_instance_id` → `PORTFOLIO_PER_CLIENT`; the 9 rank allocators
      (CARRY_FUNDING_RANK + 7 per-archetype ranks + CARRY_FUNDING_DISPERSION_RANK) weight along an axis inside
      one archetype's own universe via `BaseRankAllocator` → `ARCHETYPE_LEVEL`. Totality is ENFORCED, not just
      documented — a future archetype added without a matching dimension entry fails
      `test_allocator_archetype_dimension_is_total`. 5 tests total (totality, both groups' membership, the
      no-overlap/no-gap partition property, `WeightingDimension` staying a deliberate binary). Exported at both
      package levels matching `AllocatorArchetype`'s own existing surface. QG green (240s). Evidence:
      `/plans/epics/system_readiness_master.md` § W8.

### unified-trading-library

- [x] ✅ [BACKEND] P0. `PATH_REGISTRY` honours the `mode=` kwarg — unified-trading-library@783d98ec73. All 5
      templates (`execution_fills`/`positions`/`pnl_attribution`/`strategy_orders`/`strategy_instructions` —
      confirming the previous scoping's own correction: it's 5, not 4) now carry `{mode}`, placed right after
      `day=` to match `unified-trading-api/.../live_service.py`'s OWN parallel path map, which already assumed
      mode-partitioning was real. `partition_keys` updated to match; the `_MODE_KWARG_PENDING_MIGRATION`
      carve-out that let `build_path()` silently swallow `mode=` for these 5 datasets is DELETED.
      **One premise in the scoping note was measured WRONG and is corrected here**: the note called the 6
      call sites `pnl.py:40`/`positions.py:41`/`strategy.py:39,50`/`execution.py:59,72` "LIVE" — a repo-wide
      census (not assumed) found ZERO fleet-wide call sites for any of them (`PnLDomainClient`,
      `PositionsDomainClient`, `StrategyDomainClient`, `ExecutionDomainClient`'s domain_client variant are
      exported but never instantiated anywhere outside the package's own `__init__.py`/tests). They would not
      have raised in production; they were dead code that would only have raised on some FUTURE call. Migrated
      anyway — added `mode: str = "live"` to all 6, mirroring every real reader's own default
      (`strategy-service` `domain_adapter.py`), so the placeholder landing doesn't turn a future call into a
      landmine. `get_instructions` in particular already carried a code comment claiming zero call sites;
      confirmed true by this census, not just re-quoted.
      **Found in passing, not fixed (T1 cannot edit strategy-service): the `strategy_instructions` REGISTRY
      entry now diverges from its real writer** — `gcs_storage_service.py::write_instructions` hardcodes its
      own path string and bypasses `PATH_REGISTRY`/`build_path()` entirely, so it will keep emitting the OLD
      mode-less shape regardless of this fix. Filed as a `[FROM-T1]` inbound request on T3's plan.
      Existing smoke tests (`test_paths_registry_smoke.py`) updated to pass `mode=` and assert the new shape;
      new dedicated suite (`test_path_registry_mode_kwarg.py`, 11 tests) proves live/batch no longer collide on
      one path, that omitting `mode=` now raises `KeyError` (never silently defaults), and that the carve-out
      constant is actually gone (not just unused). QG green — real exit captured directly (309s), not via pipe.
      **Also found and set aside, not lost**: an unrelated peer's dead WIP (8+ hrs stale, no live process) sat
      in this same checkout on `unified_trading_library/cloud_interface/providers/gcp.py` — a `__getattr__`
      loud-fail guard for the GCS-client-silent-write-failure P0, T1's OWN next todo. It was failing this
      tranche's own quality gate (908 lines, over the 900 hard cap) purely by co-residence, not because of
      anything in this change. Stashed by name rather than touched or discarded:
      `stash@{0}: inherited-dead-wip-gcp-blob-getattr-guard-2026-08-20` in the UTL checkout — recovered and
      finished as its own dedicated unit under the next todo, not folded into this commit.
      Data migration stays `BLOCKED-OPERATOR` under this tranche's no-data-movement rule, per the ruling's own
      text. Evidence:
      `/plans/archive/2026_08/issues/path_registry_dead_mode_kwarg_execution_fills_positions_strategy_instructions_pnl_attribution_2026_08_15.md`.
- [x] ✅ [BACKEND] P0. GCS client silent write failure fixed — unified-trading-library@425ce119d.
      `GCSBlobHandle.__getattr__` now raises `UnsupportedNativeBlobMethodError` (a `RuntimeError`, deliberately
      NOT an `AttributeError`) on the four raw-SDK methods it doesn't implement
      (`upload_from_string`/`upload_from_file`/`upload_from_filename`/`download_as_string`), naming the
      supported replacement. A `RuntimeError` propagates straight through the defensive
      `getattr(blob, "upload_from_string", None)` pattern that caused the original incident
      (`deployment_service/deployment/state.py` returning a success-shaped result while persisting nothing) —
      that exact guard shape now fails loud at the call site instead of silently degrading.
      **Provenance**: this began as another session's uncommitted, 8-hours-stale WIP sitting in this shared UTL
      checkout (confirmed dead — no live process — before touching it). Reviewed in full rather than shipped
      blind, and a real bug was found in it: `download_as_text` was listed as unsupported, but `StorageBlob`
      (the base class) already implements it as a working default (`download_as_bytes().decode(encoding)`), so
      normal attribute lookup finds it before `__getattr__` ever fires — it could never actually have raised.
      Caught by a parametrized test over every mapped method (`DID NOT RAISE`), not assumed correct. Removed
      from the map; two dedicated tests now pin both directions (stays out of the trap map, genuinely still
      works).
      Split into a new `_gcp_blob_guard.py` sibling module (matching the existing `_gcp_credentials.py`/
      `_gcp_sdk_protocols.py` convention) rather than landing inline — `gcp.py` was already at 866 lines and
      this tranche's own 900-line hard cap would have failed on the addition otherwise; lands at 883.
      QG green (281s, real exit captured directly). This is scoped narrower than the source issue's full
      651-line multi-session history (deployment-service remediation across many callers, largely already
      shipped in earlier sessions per that doc's own "Fixed" section) — this closes the SHARED-WRAPPER root
      cause in UTL itself, the piece that was this tranche's own todo. Evidence:
      `/plans/active/issues/utl_gcs_client_upload_from_string_silent_write_failure_2026_08_18.md`.
- [x] ✅ [BACKEND] P1. 55 failing `config_interface`/`cloud_interface` tests — symptom GONE on direct re-run,
      2026-08-20: 1355 passed, 25 skipped, 0 failed across the exact suites named in the issue. Stale-venv
      hypothesis explicitly RULED OUT (`uv sync --frozen --dry-run`: no changes needed), not left unconfirmed.
      Root cause not re-derivable at a 5-day remove — closed on the measured symptom, not a reconstructed cause.
      Issue archived: `/plans/archive/2026_08/issues/unified_trading_library_config_interface_mass_test_failure_2026_08_15.md`.
- [ ] [BACKEND] P2. Complete the UAC lazy / scoped-loading refactor — full detail and Progress Log in
      `/plans/active/lazy_scoped_loading_refactor_2026_08_16.md` (not duplicated here). 2026-08-20: operator ruled
      option (a) lazy submodule attributes (PEP 562, zero breaking changes); `registry/__init__.py`
      (`unified-api-contracts@684c6e0e52`) and `architecture_v2/__init__.py` + `internal/__init__.py`
      (`unified-api-contracts@34b81221ef`) all shipped; a 4th file not in the original plan
      (`unified_api_contracts/__init__.py` itself,
      the top-level package root — its `_VENUES` eager-import loop needs hand-written design, not the mechanical
      converter) discovered and partially done. **Operator ruled 2026-08-21: YES, convert the root too — write
      the public-API import-parity test first, then the hand-designed lazy root.** Real measured win once all land: 1,766→1,295 modules (~27%) on
      `from unified_api_contracts.internal import StrategyArchetype`.
      **2026-08-21: `_VENUES` loop shipped `unified-api-contracts@ab0f9dba7c`** (sys.meta_path finder +
      PEP 562 `__getattr__`/`__dir__`, import-parity tested). Still open: the top-level file's other ~1098 eager
      re-exports remain unconverted — that mechanical conversion was attempted and deliberately REVERTED
      2026-08-20 after a silent data-corruption bug, root cause unresolved. Full detail:
      `/plans/active/lazy_scoped_loading_refactor_2026_08_16.md`'s "Layer 2 (UAC)" todo.
- [ ] [BACKEND] P2. Manifest-writer per-VM shard flush scales with shard size — UTL-owned, per T2's inbound flag
      (`[FROM-T2]` above). **2026-08-20: investigated and designed, not yet implemented.** Read the real
      implementation (`_writer_io.py`'s `_flush_per_vm_pending`/`_read_per_vm_shard`,
      `manifest_consolidator.py`'s `consolidate()`) and validated the load-bearing fact the design depends on: the
      consolidator already dedups by content key across every `_index/per_vm/*.parquet` glob match, not by source
      filename — so a delta-shard file needs ZERO consolidator-side changes, only writer-side ones. Full 5-step
      proposal (delta upload on non-final flush, glob+concat on the writer's own read-back, compact-and-delete on
      `process_final=True`, the crash-safety argument, explicitly-not-designed collision/orphan-cleanup edges) is
      in the issue doc's Progress Log. Real code changes to a durability-critical, fleet-wide hot path deserve
      their own review + a SIGKILL-mid-delta test written first — not a same-session implementation. Evidence:
      `/plans/active/issues/manifest_writer_per_vm_shard_flush_scales_with_shard_size_2026_07_28.md`.

### External API surface — `platform-external-api-walkthrough.html`

> **2026-08-20 re-triage** — T1 read this section's target file directly (artefact line 1361 cites
> `execution-service/execution_service/api/external_instruction_api.py`, verified) and found every remaining item
> below targets a repo T1 does not own (`execution-service`=T4, `strategy-service`=T3). None of these are
> `unified-trading-api` — that repo's own `routes/execution.py` is an unrelated mock/demo store with no `/external/*`
> surface at all (confirmed: no `501`/`NOT_IMPLEMENTED` anywhere in the repo outside `.venv`). Redirected via
> `[FROM-T1]` inbound flags rather than either fabricating out-of-repo edits or silently dropping the finding.

- [x] ✅ SUPERSEDED — redirected, not built by T1. [BACKEND] P0. ~~Replace the honest HTTP 501s with real
      implementations — `transfer`, `bridge`, `atomic`, `cancel`.~~ Target is `execution-service`'s
      `/external/instructions` router (T4-owned) — see `[FROM-T1]` in T4's plan. **Self-correction, same day**: the
      first pass here checked the wrong (legacy) vocabulary and wrongly claimed QUOTE/TRANSFER/CANCEL were missing
      from UAC. The CURRENT contract is `StrategyInstructionV2` (a Pydantic union in
      `unified_api_contracts.internal.architecture_v2.schemas`), and it already has real dataclasses for every one
      of the 10 — `SwapInstruction`/`LendInstruction`/`BorrowInstruction`/`StakeInstruction`/`UnstakeInstruction`/
      `QuoteInstruction`/`TransferInstructionV2`/`BridgeInstructionV2`/`AtomicInstruction`/`CancelInstruction` —
      keyed off real `InstructionActionV2` enum members. If T4's router 501s on these, the gap is
      execution-service's own dispatch, not a missing UAC type. Corrected in T4's plan too
      (`unified-trading-pm@3e7d7c14b9`).
- [x] ✅ SUPERSEDED — redirected, not built by T1. [BACKEND] P0. ~~Build the counterparty-facing surface the
      artefact marks `planned — shape in`.~~ Target is `strategy-service` (T3-owned) — see `[FROM-T1]` in T3's plan.
- [x] ✅ SUPERSEDED — redirected, not built by T1. [BACKEND] P1. ~~Enumerate exactly the API surface...~~ Spans
      `instruments-service`+`market-tick-data-service` (T2) and `execution-service` (T4) routers, none T1-owned;
      this is doc-generation work reading routes across repos, not editing any of them — redirected to T5 (already
      builds route-surface tooling for the readiness dump) with a note that it needs T2/T4 to hold their routers
      stable while it walks them.
- [x] ✅ [BACKEND] P1. **Closed by T4's answer, 2026-08-20 — no contract change needed.** T4 answered the
      `[FROM-T1]` question on their own plan: do NOT add `KILL_SWITCH`/`FLATTEN_POSITION` to the strategy
      instruction vocabulary at all. Both capabilities already exist, correctly, on the DELIBERATELY separate
      `AccountInstruction` envelope — `kill_switch.activate()`/`.deactivate()` (durable state-file, admin-only,
      `POST /kill-switch/activate`) and `AccountInstruction.CLOSE_ALL` (operator-driven, `authorization_id`-gated,
      real per-venue wiring — `execution-service@96411b68c9` + `@c0839616be`). Adding these to
      `StrategyInstructionType`/`InstructionActionV2` would expose them on `/external/instructions` — the
      third-party-reachable surface — under the WRONG authority model (strategy-engine, not operator-only); T4
      cited `/codex/04-architecture/account-instructions.md`'s own stated rationale for keeping the two envelopes
      separate ("different authority model... different risk gates, some ops bypass strategy-layer checks by
      design"). External partner-facing kill/flatten access, if ever wanted, is a product/security policy call for
      the operator, not something to build speculatively. **Correct outcome: T1 does nothing here** — the original
      artefact marker calling this "planned, not yet" was itself the thing that needed correcting, not the code.
- [x] ✅ [UI] P1. **Closed by measurement, 2026-08-20 — the wizard already exists and is functional; there was
      nothing to build.** The artefact's "build the wizard surface" framing was stale: `unified-trading-system-ui`
      already has a full 6-stage wizard implementation (`app/(wizard)/wizard/`, `components/wizard/` — 13
      components mapping directly onto the artefact's Archetype/Universe/Sizing/Risk/Execution/Identity stages,
      plus `ConfigOutput.tsx` for the generated-config example the artefact asks for) and 11 spec files / 34 tests
      under `tests/smoke/wizard*.spec.ts` (portfolio mode, screener mode, custody stage, data coverage, jurisdiction
      filter, save-session, readiness badges, isolation mode, param forms — every feature area the artefact
      describes and more). **`pw:L2 ✓`**: ran the full suite fresh — 33/34 passed on first run; the one failure was
      a hardcoded venue count (`"225"`) drifted stale against the live registry (now 230) — the exact same drift
      class the test's own comment already documents happening once before (was "195"→"225", now "225"→"230"), not
      a functional regression. Fixed and re-verified green —
      `unified-trading-system-ui@109a488a78` (`tests/smoke/wizard.spec.ts`). **Regression spec**:
      `tests/smoke/wizard.spec.ts` + the 10 sibling `wizard-*.spec.ts` files, all passing.
      **What's still genuinely missing is artefact-side, not UI-side** — real screenshots and a real
      generated-config example IN the HTML artefact — and per the close-out rule ("never hand-edit the HTML"),
      that's a regeneration task, not something to hand-write here. Not filing a fresh redirect for it: the exact
      artefact file (`platform-external-api-walkthrough.html`) already shows large, active, in-flight edits from a
      concurrent session this same day (5 related `codex/14-customer-journeys/commercial-model/*.html` files, 2000+
      line diffs observed) — flagging here so whoever lands that regeneration knows the wizard itself is real,
      tested, and ready to be captured, not still pending a build.
- [x] ✅ SUPERSEDED — redirected, not built by T1. [BACKEND] P2. ~~Ceffu integration is a stub pending its API
      spec...~~ Target is `execution-service/execution_service/transfer_coordinator.py` (T4-owned, confirmed by the
      artefact's own citation at line 16915) — see `[FROM-T1]` in T4's plan.
- [x] ✅ [BACKEND] P2. **Shipped — `unified-api-contracts@01a595d3aa`.** Fee and gas modelling cost components —
      contracts side. Added `clearing_fee_bps`, `broker_fee_bps`, `other_fee_bps` to
      `ExecutionCostEstimate` (`unified_api_contracts/internal/domain/execution_service/cost_estimate.py`), matching
      W17's exact "clearing, broker, exchange, gas, and other" breakdown (`exchange_fee_bps`/`gas_cost_usd` already
      existed). All three default to `Decimal("0")` — backward-compatible, and deliberately NOT folded into
      `total_cost_bps` (documented) so no existing producer's total silently drifts. 3 tests added
      (`tests/internal/unit/domain/execution_service/test_cost_estimate_fee_breakdown.py`), passing standalone.
      W17's service-side split (baking these into strategy's decision and execution's alpha PnL) is T3/T4, per the
      plan's own framing — not redirected, since the todo already said so.

### Close-out

- [ ] [AGENT] P1. **PARTIAL, 2026-08-21 close-out pass — this plan's OWN todos are zeroed; the wider JSON-allocation
      corpus tail is not, and is NOT claimed done.** Re-walked every remaining `- [ ]` in THIS
      plan top to bottom (the spine section is already 100% closed, verified above). Result: `LpMintInstruction`/
      `LpBurnInstruction` was genuinely done and unflipped — fixed above with evidence. `reference_position`/`credit`
      re-tagged `BLOCKED-OPERATOR-DECISION` (was tagged as merely needing "a ruling," which is now stale — the
      ruling landed 2026-08-21 but exposed a real apparent tension between its own two halves; see the notes above,
      not forced). The walkthrough-feedback registry cluster (line ~477) and W5 collateral/margin population
      (line ~489) were independently re-verified still correctly `BLOCKED-OPERATOR-DECISION` — not touched, per this
      todo's own explicit instruction not to spend effort trying to unblock them. The lazy-loading refactor P2
      (line ~588) and manifest-writer per-VM shard flush P2 (line ~603) were re-verified still accurately described
      (checked the real code state, not just re-read the doc) and correctly deferred — not forced.
      **The `§ "Your allocated corpus"` JSON allocation is a SEPARATE, much larger surface** (~45 non-spine docs,
      the allocation script assigns doc-level, not todo-level, so many carry T1-repo-touching todos alongside
      other-tranche domain work). A sampled audit (frontmatter `repos:` + live open-todo count on ~20 of them)
      confirms the same pattern already established for this plan's own "External API surface" section: most tail
      todos are prediction/sports/tradfi/UI-domain work that only incidentally names a T1 repo (e.g. deployment-api
      as a display surface), not T1 contract/library work. Fully resolving that ~45-doc / ~90-todo surface to the
      same rigor as the External API surface redirect (per-doc investigation, `[FROM-T1]` redirects where genuinely
      out-of-repo) is real work beyond one close-out pass's bounded scope and risks concurrent-edit collisions across
      ~45 files other tranches may be actively touching (this session already hit exactly that collision risk once,
      on this same repo, today). Recommending that surface become its own follow-up if the operator wants it swept —
      not claiming it silently zeroed. This plan's OWN todos (the actual close-out unit) are the ones verified done
      above.
- [x] ✅ [AGENT] P0. **Post-phase codex audit complete, 2026-08-21 — all 6 items checked, 3 codex docs updated.**
      Evidence: `unified-trading-pm@0dd2475e82`.
      1. **`QuoteInstruction` sensitivity fields** — real drift found: `/codex/04-architecture/strategy-execution-protocol.md`'s
         `### QUOTE` section (and its "11 actions" framing throughout) predated this session's schema changes.
         Updated with `delta`/`gamma`/`underlying_instrument_id` + the `effective_delta` formula.
      2. **`TransferCapabilityV2`** — no codex doc mentioned it at all. Added a "Transfer capability" section to
         `/codex/03-services/venue-capability-registry.md` (the correct SSOT — `authoritative_for: venue capability
         declaration schema`), with a disclosure note that the doc's existing dataclass sketch is V1-era and hasn't
         been fully reconciled to `VenueCapabilityV2`.
      3. **W17 fee breakdown** (`clearing_fee_bps`/`broker_fee_bps`/`other_fee_bps`) — searched for an
         `ExecutionCostEstimate` SSOT; the only codex hits (`defi-execution-overview.md`,
         `defi-risk-monitoring.md`, `pnl-attribution.md`) describe DIFFERENT DeFi-specific cost classes
         (`DefiCostEstimate`/`UnwindCostEstimate`), not the CeFi `ExecutionCostEstimate` this field landed on. No
         doc exists for it and none is warranted — small, self-explanatory field addition, matches the judgment bar
         set by the lazy-loading precedent (no doc manufactured for coverage's sake).
      4. **`WithdrawInstruction`/`RepayInstruction`** (+ `LpMintInstruction`/`LpBurnInstruction`, found genuinely
         shipped during this same pass, see above) — same `strategy-execution-protocol.md` doc, same real drift:
         its "11 Actions" table had none of the 4 new actions. Added all 4 (title/summary/authoritative_for/body
         updated to "15 Actions" — the target-state family; `KILL_SWITCH`/`FLATTEN_POSITION`/`CONVERT_DUST` noted as
         a separate control-plane family, not silently folded into the same count).
      5. **Venue→chain SSOT + `VenueFeature`/`VenueCapability` overlap fix** — checked
         `venue-capability-registry.md`'s existing illustrative `VenueFeature` example
         (`CROSS_MARGIN`/`PORTFOLIO_MARGIN`/`SUBACCOUNT`/`ATOMIC_MULTI_LEG`) against the real post-dedup
         `VenueCapabilityV2.features` set (`unified-api-contracts@0d7afa29e`) — **no drift**, the doc's own example
         already matches exactly. Added a confirming note (folded into the same TransferCapabilityV2 edit) rather
         than leaving the match undocumented.
      6. **W8 weightings** — `/codex/03-services/portfolio-allocator.md` already correctly described the Group
         1/Group 2 archetype split in prose; no drift, but the new `WeightingDimension`/
         `ALLOCATOR_ARCHETYPE_DIMENSION` enum now codifies exactly that split with a totality test. Added a
         cross-reference note so a future reader finds the enforced enum, not just the prose description.
      **Hazard hit and recovered from mid-task**: this repo's shared-checkout auto-reconcile quarantined the first
      attempt at these 3 doc edits into an autostash (an 87-entry pile) before they could be committed — confirmed
      via `git status`/`git diff --stat` showing the edits absent, not just a stale notification. Redone from
      scratch, shipped immediately via `safe-doc-push.sh` (isolated-worktree commit, unaffected by the working-tree
      quarantine), landing verified against `origin/live-defi-rollout`. A subsequent `git pull --ff-only` conflicted
      re-applying a stale autostash of the SAME edit against itself (cosmetic table-width diff only, not content) —
      resolved by keeping the already-landed version; several OTHER sessions' unrelated foreign WIP that surfaced in
      the same autostash pop was re-quarantined by name (`git stash push -u -m "quarantine: ..."`, never dropped)
      rather than touched, per the multi-agent-safety hard rule.
- [ ] BLOCKED-OPERATOR-DECISION [AGENT] P0. **Confirmation done, 2026-08-21 — genuinely blocked, not a
      missing-tooling gap; re-derivation itself cannot happen yet.** Found `platform-external-api-walkthrough.html`'s markers are real: `class="st st-*"`
      (`st-part`/`st-plan`/`st-live`) + `class="ev ev-*"` (`ev-check`/`ev-assumed`/`ev-verified`) hand-authored
      markup, read by `scripts/plan-hygiene/check_artefact_claim_ownership.py` (ownership/count ratchet) and
      `check_artefact_enum_drift.py` (count-vs-UAC-enum ratchet) — both are CHECKERS, not regenerators; these files
      are explicitly hand-authored (both scripts' own docstrings state this), so "re-derive" means edit the HTML
      to match measured reality, then re-run the checkers to confirm — not run a generator script (none exists, and
      none should be invented for this todo). **T5 (this artefact's actual owner) already has a standing, explicit,
      2026-08-20 operator ruling to freeze ALL hand-edits to all 4 client artefacts** — sourced from
      `/plans/active/state_fabric_artefacts_2026_08_20.md` line 357 ("wait for this plan's ledger-binding approach,
      do not hand-edit the artefacts") and independently confirmed by that same plan's own todo 1/2 ("Persist a
      versioned readiness + coverage ledger" / "Bind the artefacts to the ledger") both still open `- [ ]` — the
      ledger-binding this freeze is conditioned on has NOT landed. T5's own na-eligibility-audit entry
      (`code_readiness_t5_readiness_observability_presentations_2026_08_19.md` line ~978) independently corroborates:
      "4 DOC 're-derive artefacts' todos — Not started — operator decision 2026-08-20: wait for the ledger plan."
      **The "five allowed pending states"** are the marker vocabulary itself, per
      `check_artefact_claim_ownership.py`'s own docstring: `st-part`/`st-plan`/`ev-check`/`ev-assumed` are the four
      OPEN states (one of the operator's 5 goalpost exceptions is allowed to still read one of these) plus `st-live`/
      `ev-verified` as the closed pair — matches this plan's own line 62-73 "goalpost" framing (backfills-running /
      venue-connectivity / market-data-live / testnets / archetypes-pending-real-data are the 5 allowed reasons a
      marker stays open). Not hand-editing the HTML per the todo's own explicit instruction AND the operator's
      standing freeze — correctly left as `BLOCKED-OPERATOR-DECISION`, T1 has nothing further to do here until T5's
      ledger plan lands.

## Progress Log

> Append-only. One entry per shippable unit — what you changed, the `<repo>@<sha>`, and what you MEASURED (not what
> you assume). This log is the handoff document if this agent's context ends and a fresh one resumes the tranche.

- 2026-08-19/2026-08-20 entries (plan authoring, 3 pre-compact checkpoints, 3 contract-edge landings, 2 registry
  P0 fixes, a session handover, cross-tranche redirects, W5/W17 items) — **moved to
  `/plans/active/code_readiness_t1_progress_history_2026_08_20.md` verbatim** (2026-08-21 line-cap split, parent
  crossed the 1000-line hard cap; mirrors the T2/T3/T5 sibling plans' identical split). Read that doc for the full
  audit trail; nothing here was lost, only relocated.
- 2026-08-20 — **Self-caught and corrected a wrong claim from the entry above, same session, before T4 acted on
  it.** While closing T4's separate BATCH-settlement-gap request (below), found `unified_api_contracts.internal.
  architecture_v2.schemas.StrategyInstructionV2` — a Pydantic union with real dataclasses for SWAP/LEND/BORROW/
  STAKE/UNSTAKE/QUOTE/TRANSFER(`TransferInstructionV2`)/BRIDGE(`BridgeInstructionV2`)/ATOMIC(`AtomicInstruction`)/
  CANCEL(`CancelInstruction`), each backed by a real `InstructionActionV2` enum member. This directly contradicts
  the earlier entry's claim that QUOTE/TRANSFER/CANCEL were "genuinely absent from the contract" — that claim
  checked `StrategyInstructionType`, a DIFFERENT, legacy vocabulary in
  `unified_api_contracts/internal/domain/strategy_service/_instruction_base.py`, not the current v2 architecture
  `StrategyInstructionEnvelope` subclasses actually use. **Corrected in both plans** (this file and T4's) before
  T4 could chase a phantom contract gap — `unified-trading-pm@3e7d7c14b9`. **Lesson**: this repo carries
  parallel instruction-type vocabularies (legacy `StrategyInstructionType` vs. current `InstructionActionV2`/
  `StrategyInstructionV2`) — grep for the CONSUMING code's actual import (`execution_service/backtest_v2/
  action_handlers.py`'s `resolve_settlement` dispatches via `isinstance` over `StrategyInstructionV2`) before
  claiming a vocabulary gap, not just the first `InstructionType`-shaped name that matches.
  **Shipped — `unified-api-contracts@f5fc118ae1`.** Closed 2 of T4's 4 requested BATCH-settlement-gap
  dataclasses: `WithdrawInstruction` (protocol/asset/`target_supplied_amount`, rate-matched inverse of
  `LendInstruction`) and `RepayInstruction` (protocol/asset/`target_debt_amount`, inverse of `BorrowInstruction`),
  modelled directly on the existing Lend/Borrow field shape per T4's own explicit description ("same
  protocol/asset/target-amount shape, opposite direction"). Added to `StrategyInstructionV2` (both the
  `schemas.py` definition and `architecture_v2/__init__.py`'s separately-inlined copy — the module docstring there
  explains why it isn't a straight re-export: avoiding a Pydantic reimport race) and both `__all__` export levels.
  4 tests (`tests/internal/unit/test_withdraw_repay_instructions.py`), verified passing standalone before the
  full-repo gate; `ruff check --fix` needed one pass for 3 `RUF022` unsorted-`__all__` violations (auto-fixed, not
  hand-ordered — three files' worth of insertion points is exactly what the tool exists for). `LpMintInstruction`/
  `LpBurnInstruction` deliberately NOT built — zero existing DeFi-LP position-shape reference anywhere in this
  repo (grepped `tick_lower`/`pool_id`/`lp_token`/`token0`/`token1`, zero hits), and T4's own request said the
  shape is "not designed here — that's a UAC-side call." Rather than invent a concentrated-liquidity schema from
  nothing for a live execution path, asked T4 to name the fields (pointed them at
  `UniswapConnector.mint_position()`/`burn_position()`'s real signatures, which the enum's own comment already
  cites as the dispatch target) — held open, not fabricated.

- [x] ✅ [FROM-T2] P3. **Flip `InstrumentRecord.model_config = ConfigDict(extra="forbid")`** in
      `unified-api-contracts/unified_api_contracts/internal/reference/instrument.py`. Every REMOVE-verdict caller
      is now clean fleet-wide — T2 finished the last one (`min_order_size`, zero consumers, removed from all 5
      call sites, `instruments-service@588f35aeb0`). Shipped `unified-api-contracts@cdb8ae8806` (bundled with the
      6-bookmaker removal); 4 new regression tests added
      (`tests/unit/test_instrument_record_extra_forbid.py`). Full disposition history + evidence:
      `/plans/archive/2026_08/instrument_record_schema_completeness_extra_forbid_2026_07_18.md` (resolved+archived).
- **na-eligibility-audit 2026-08-21** (cross-cutting tranche, first audit pass): KEEP-NA, valid — Tranche 1 of the operator-slot-launched code-readiness series (see the coordinator doc's Launch-prompts mechanism — paste-into-a-slot + `/autonomous`, not AO-backlog dispatch); actively worked, extensive shipped-commit evidence throughout. Remaining open items mix genuine operator-gated design questions (Q12-Q16 reference-position/credit shape ruling via the cross-domain-state-fabric SSOT, W5 collateral/margin data explicitly requiring real per-venue research — 'T1 will not invent financial risk parameters'), a kill-switch/flatten-position design call held pending T4's answer, an un-started wizard UI item, and standing tail-closure/codex-audit/marker-confirmation todos gated on the rest of the tranche completing. None clears the whole-doc RECLASSIFY bar.
- **Close-out session 2026-08-21**: worked all 3 close-out todos. (1) **Non-spine tail** — this plan's own remaining
  open todos re-walked top to bottom: `LpMintInstruction`/`LpBurnInstruction` found genuinely shipped
  (`unified-api-contracts@d751e743`/`@3204e607`) and flipped with evidence; `reference_position`/`credit` re-tagged
  `BLOCKED-OPERATOR-DECISION` (Q12-Q16 answered 2026-08-21 but exposed a real apparent tension between the ruling's
  stated implementation vehicle — the fabric snapshot/factor-state contract — and its own literal field-list answer;
  not forceable without another operator pass); the two "do not force" items (W5 collateral, manifest-writer flush)
  and the two already-blocked items (walkthrough-feedback registry cluster, lazy-loading refactor) all independently
  re-verified still accurate. The wider `§ "Your allocated corpus"` JSON-allocation tail (~45 non-spine docs) was
  sampled, not exhaustively worked — most sampled docs carry other-tranche domain work (prediction/sports/tradfi/UI
  features) that only incidentally names a T1-owned repo; fully redirecting all of it needs the same per-doc rigor
  as the "External API surface" section got, which is beyond one close-out pass — left open with this finding
  recorded rather than claimed done. (2) **Post-phase codex audit** — all 6 named contract changes checked against
  existing codex docs; 3 docs updated (`strategy-execution-protocol.md`: QuoteInstruction sensitivity fields +
  WITHDRAW/REPAY/LP_MINT/LP_BURN, "11 Actions"→"15 Actions"; `venue-capability-registry.md`: TransferCapabilityV2 +
  VenueFeature/VenueCapability confirmation; `portfolio-allocator.md`: WeightingDimension cross-reference); W17 fee
  breakdown confirmed to need no doc (no existing `ExecutionCostEstimate` SSOT, small self-explanatory field
  addition). Evidence: `unified-trading-pm@0dd2475e82`, verified against `origin/live-defi-rollout`. (3) **Artefact
  markers** — confirmed genuinely `BLOCKED-OPERATOR-DECISION`: T5 (the artefact's actual owner) has a standing
  2026-08-20 operator freeze on hand-editing all 4 client artefacts pending
  `/plans/active/state_fabric_artefacts_2026_08_20.md`'s ledger-binding, which has not landed (its own todos 1-2
  still open). The marker vocabulary (`st-part`/`st-plan`/`ev-check`/`ev-assumed` open, `st-live`/`ev-verified`
  closed) is hand-authored by design (both artefact-check scripts' own docstrings say so) — confirmed no
  regeneration script exists or should exist; per the todo's own instruction, did not hand-edit the HTML.
  **Mid-session hazard**: this repo's shared-checkout auto-reconcile quarantined the first attempt at the 3 codex
  doc edits into an 87-entry autostash before they were committed (measured via `git status`, not assumed from a
  stale notification); redone and shipped via `safe-doc-push.sh` (isolated-worktree commit, unaffected by the
  working-tree quarantine), then a `git pull --ff-only` produced one cosmetic table-width conflict against a stale
  copy of the SAME edit (resolved by keeping the landed content) plus several other sessions' unrelated foreign WIP
  in the same autostash pop — that foreign WIP was re-quarantined by name (`git stash push -u -m "quarantine: ..."`,
  never dropped, never inspected further) rather than touched, per the multi-agent-safety hard rule. **Verified
  every shipment against `origin/live-defi-rollout` directly** (`git fetch` + `git show origin/...:<path>` /
  `merge-base --is-ancestor`), not trusted off a ship script's own success message.
