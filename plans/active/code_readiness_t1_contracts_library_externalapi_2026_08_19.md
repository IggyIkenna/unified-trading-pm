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

**The acceptance test is the artefacts.** These four client-sendable documents must stop carrying `pending`,
`planned`, `partial`, `not built` or `unverified` on any claim that is not one of the five above:

- `/codex/14-customer-journeys/commercial-model/platform-architecture.html`
- `/codex/14-customer-journeys/commercial-model/platform-external-api-walkthrough.html`
- `/codex/14-customer-journeys/commercial-model/strategy-service-deep-dive.html`
- `/codex/14-customer-journeys/commercial-model/strategy-service-walkthrough.html`

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
      UAC-side todo in `/plans/active/issues/instruments_schema_not_locked_versioned_2026_08_18.md` is now
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
      `/plans/active/issues/instruments_schema_not_locked_versioned_2026_08_18.md`.

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

- [ ] [FROM-T4] P1. **2 of 4 shipped — `WithdrawInstruction`/`RepayInstruction` done; `LpMintInstruction`/
      `LpBurnInstruction` still need the DeFi LP position shape specified (T4's call, not designed here).**
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
      `/plans/active/issues/uac_get_venue_asset_group_silently_returns_cefi_for_all_venues_2026_08_19.md`.
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
      `/plans/active/registry_ssot_hardening_2026_08_16.md`.
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
- [ ] [BACKEND] **BLOCKED-OPERATOR** P0. Add `reference_position` to `StrategyInstructionEnvelope`. **The shape this
      todo names (`dict[venue, Decimal]`, "same shape as the existing price leg") is SUPERSEDED** — the source issue
      carries a dated correction banner from a later same-day operator revision ruling that shape incomplete: it
      solves the venue axis but not the INSTRUMENT axis, since a strategy instance holds a universe of instruments.
      The replacement (`references: list[InstrumentReferenceEntry]`) is published in that issue under the heading
      **"Proposed shape (illustrative — not finalized; this is what needs resolving, not what's decided)"** followed
      by **"Open questions for the operator — do not resolve unilaterally"** (Q12-Q16). Implementing the todo's
      literal text would ship the rejected shape; implementing the vector would answer five questions explicitly
      reserved for the operator. **Needs: a ruling on Q12-Q16**, then this becomes a bounded code task.
      Evidence: `/plans/active/issues/execution_delta_proxy_repricer_generalization_2026_08_18.md`.
- [ ] [BACKEND] **BLOCKED-OPERATOR** P0. Add the `credit` leg to `StrategyInstructionEnvelope`. Same gate as
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
      `/plans/active/issues/order_state_machine_ssot_vs_uac_orderstatus_2026_07_31.md`.
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
      converter) discovered and partially done. Real measured win once all land: 1,766→1,295 modules (~27%) on
      `from unified_api_contracts.internal import StrategyArchetype`.
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

- [ ] [AGENT] P1. Work the non-spine tail of this tranche's allocation (see § "Your allocated corpus") to zero open
      todos or an explicit `BLOCKED-*` tag on every remainder.
- [ ] [AGENT] P0. Post-phase codex audit — update every changed contract doc, stub new patterns, add SUPERSEDED
      banners to invalidated docs. Plan↔codex drift is review-blocking. **In progress, 2026-08-20 — one pattern
      stubbed, not a full sweep yet.** The lazy-loading refactor had no codex SSOT at all (pattern + both real bugs
      + the top-level file's known-broken state lived only in the plan's own Progress Log, which archives when the
      plan does) — wrote `/codex/06-coding-standards/uac-init-lazy-loading-pattern.md`. Order-state-machine SSOT
      was already handled by T4 earlier today (`c74d869b36`, stale 7-state warning + diagram). Remaining
      contract-shaped changes this tranche shipped that have NOT yet been checked against an existing codex doc for
      drift: `QuoteInstruction` sensitivity fields, `TransferCapabilityV2`, W17 fee breakdown, `WithdrawInstruction`/
      `RepayInstruction`, the venue→chain SSOT + `VenueFeature`/`VenueCapability` overlap fix, W8 weightings. Not
      claiming this todo done off one doc.
- [ ] [AGENT] P0. Confirm every artefact marker owned by this tranche now reads live, or is one of the five allowed
      pending states. Re-derive; never hand-edit the HTML.

## Progress Log

> Append-only. One entry per shippable unit — what you changed, the `<repo>@<sha>`, and what you MEASURED (not what
> you assume). This log is the handoff document if this agent's context ends and a fresh one resumes the tranche.

- 2026-08-19 — Plan authored. Allocation derived by `scripts/plan-hygiene/allocate_code_readiness_tranches.py`
  against the 892-doc active corpus. No code work started yet.
- 2026-08-20 — **PRE-COMPACT CHECKPOINT.** Context hit 67%; ran `/pre-compact` per the harness hook. Two significant
  finds during the audit, both from earlier (compacted-out) work in this same session:
  1. **Shipped**: 180 lines of FACTOR-STATE MODEL design work on the delta-proxy repricer issue doc
     (`execution_delta_proxy_repricer_generalization_2026_08_18.md` §11-15) were sitting uncommitted —
     unified-trading-pm@(latest, verified via `grep FACTOR-STATE` on origin post-push). Covers the unified
     fair-value function, canonical factors vs per-venue prices, snapshot watermarks, currency/numeraire ruling,
     rebase-without-jaggedness, and a placement ruling (anchor estimator lives in features-service, not
     strategy-service). Carries its own 3 tracked todos (`[DOC]`/`[REVIEW]`/`[BACKEND]`) plus 5 open items for
     the next operator session (§15) — READ THAT SECTION before touching `reference_position`/`credit` again;
     it may supersede the Q12-Q16 framing this plan cites elsewhere. The ship hit a self-healing collision
     (safe-doc-push detected its own corruption attempt from a concurrent peer edit, restored my content from a
     snapshot, verified zero conflict markers before proceeding) — landed clean, verified on origin.
  2. **UPDATE, same session, post-checkpoint: item 2 below was a FALSE ALARM, not real loss — recorded because
     the diagnostic trail is worth keeping.** After writing this checkpoint, the local working-tree copy of
     `TransferCapabilityV2` genuinely disappeared from `schemas.py` (confirmed: 0 matches, clean `git status`),
     and the gate run launched against it failed with `ImportError: cannot import name 'TransferCapabilityV2'`
     — indistinguishable from real data loss at the time. Reconstructed the change from the diff already
     captured in-session, re-verified 5/5 tests, re-gated (green, 377s), and went to ship it — at which point
     quickmerge's own Not-Behind Gate reported `unified-api-contracts@45a545e5ad` (this SAME slot, an EARLIER
     part of this compacted-out session) had **already landed the identical change** minutes before the
     checkpoint was written. The "revert" was never a revert: the working tree had simply reset to
     post-commit-clean state after that earlier successful ship, and re-reading it without re-checking `git log`
     first made it look like loss. Diffed the reconstruction against origin's landed version — byte-identical —
     then discarded the local duplicate and `pull --ff-only`'d clean (0 ahead/behind). **Lesson for next time**:
     before treating a missing local change as reverted, check `git log HEAD..origin/<branch>` FIRST — a
     same-slot earlier-session commit reads identically to a hostile revert until you do.
  (The original item-2 text this replaced described the pre-resolution "in flight, not yet shipped" state — moot
  now; the todo at line 376 already carries the correct landed sha.)
  **Standing state, unaffected by either item above**: 22 of T1's remaining todos need no gate finished, no
  outstanding uncommitted work exists in `unified-trading-library` (clean, 0 ahead) or `unified-trading-pm`
  (clean, 0 ahead, 0 behind after the restore above). All prior Progress Log entries in this file remain the
  authoritative record of what shipped before this checkpoint — do not re-derive.
- 2026-08-20 — **PATH_REGISTRY mode= fix landed — unified-trading-library@783d98ec73.** batch/paper/live rows
  for 5 datasets no longer collide on one GCS object path. Full details in the todo flip; noted here because it
  had TWO recoveries worth remembering: (1) a `check_todo_regression` gate catch of my own doing — a perl splice
  glued a following P1 todo onto the flip block with no newline, silently dropping it from the count (32->31);
  re-diffed against origin line-by-line, restored the newline, re-verified 32=32 before shipping. (2) a shared-
  checkout collision — running quality-gates.sh surfaced an 8-hour-stale, uncommitted peer edit on
  `unified_trading_library/cloud_interface/providers/gcp.py` (a `__getattr__` loud-fail guard for the GCS-
  client-silent-write-failure P0, this tranche's own NEXT todo) that was failing the gate on a 900-line file
  cap purely by co-residence. Confirmed dead (no live process, mtime 8h+ stale) before touching it, then set
  aside via a NAMED stash rather than fixed, discarded, or force-committed:
  `stash@{0}: inherited-dead-wip-gcp-blob-getattr-guard-2026-08-20` in the UTL checkout — recovered next.
- 2026-08-20 — **Oracle VALUE blindness closed — unified-api-contracts@03e8e90f.** Third violation class
  (`CanonicalViolationClass.VALUE`) answers "does this partition value name a real entity", checked against the
  venue / data_type / instrument_type / chain registries. CLAUDE.md's own conditional index warns agents that the
  oracle is "VALUE-BLIND"; that warning can now be narrowed to "value-blind BY DEFAULT, on purpose".
  **The design decision to re-read before changing anything here**: VALUE is OPT-IN. I measured the caller graph
  before writing a line — `canonical_path_violations()` feeds a WRITE boundary that RAISES
  (`market-tick-data-service/.../symbol_rules.py:517`), and the module already carries an inline account of the
  2026-06-23 incident where an over-eager venue guard flagged the legitimate `BINANCE-FUTURES` token and froze the
  deribit/hyperliquid/binance live VMs for hours. A registry that lags reality must degrade to a quiet audit
  finding, never a write outage — so `violation_classes=None` still answers exactly STRUCTURAL + ID_FORM, pinned by
  the named `DEFAULT_VIOLATION_CLASSES` constant AND by a regression test that asserts a path with a fictional
  venue still returns `[]` by default. The classified/audit view reports VALUE unconditionally, since an audit has
  no write path to break. **If someone later "tidies" VALUE into the default, that is the live-VM outage
  re-armed** — the constant's docstring says so in place.
  **Two limits stated rather than glossed**: membership is case-INSENSITIVE (measured: `ALL_VENUES`/`InstrumentType`
  UPPERCASE, `ChainKind` lowercase, `ALL_DATA_TYPES` genuinely mixed — case-sensitive comparison would manufacture
  violations on correct paths), and a missing axis is silent (absence is already STRUCTURAL; double-reporting it
  would inflate every audit). So "0 VALUE violations" means "every value present names something real", NOT "every
  value is correctly cased" and NOT "every required axis is present".
  Probed live before shipping: bogus `venue=NOT_A_VENUE` returns `[]` under the default and is caught under VALUE.
- 2026-08-20 — **Oracle filename-stem todo was STALE — closed by measurement, not by new code.** The plan listed
  `canonical_path_violations()` filename-stem validation as an open P0; it shipped weeks earlier
  (`unified-api-contracts@d40c5d7d`/`@502ef57e`). Confirmed against the CODE, not the issue doc's self-report:
  `CanonicalViolationClass.ID_FORM` is documented as "The FILENAME STEM", `id_form` is populated at 4 sites, and
  structure-only is now an explicit opt-in rather than the silent default. The source issue reads `status: open`
  only because 2 unrelated `[DATA]` findings from 2026-08-17 remain on it — a reminder that an issue's status
  field is not a verdict on any single todo inside it. **Still genuinely open**: the sibling VALUES todo — the
  oracle remains blind to `instrument_type`/`data_type`/`venue`/`chain` VALUES, which CLAUDE.md itself warns
  agents about, so "0 violations" still does not mean "canonical" on that third axis.
- 2026-08-20 — **Contract edge #3 landed: `OrderStatus` is now the 9-state machine — unified-api-contracts@a3c572f8.
  T4 unblocked.** Verified on origin, not by exit code: 9 canonical members + 2 aliases present in the landed blob,
  transition map + test file present, top-level export present, and `a3c572f8` confirmed via
  `merge-base --is-ancestor`. QG real exit 0 (273s), captured WITHOUT a pipe.
  **Design call worth re-reading before anyone "cleans up" the aliases**: option A (rename in place) was ruled and
  twice reconfirmed, but a literal rename breaks 24 execution-service call sites, and the entity-rename SSOT
  requires consumers to migrate in the SAME change — impossible from a tranche forbidden to edit that repo. The
  aliases resolve that conflict without shipping the rejected alternative: they are enum aliases (identity, not
  copies), so the state space cannot split in two. Removal is a filed `[FROM-T1]` todo on T4's plan, not a
  someday-note. MEASURED before choosing this: zero `.name`-based / `OrderStatus[...]` / `len()` / iteration
  coupling fleet-wide — that measurement is the whole basis for calling it behaviour-preserving, so if it is ever
  refuted the alias decision must be revisited.
  **What I deliberately did NOT do**: widen `PARTIALLY_FILLED` beyond the single edge the codex diagram draws.
  Real venues cancel partially-filled orders, so the map is probably incomplete — but the doc is the SSOT and this
  map is its projection, so the fix is a codex amendment first. Filed as a P2 question on T4's plan.
- 2026-08-20 — **Cross-tranche handoffs shipped — unified-trading-pm@617670c965.** T4 got three `[FROM-T1]` items
  (alias migration, the never-written `test_state_machine.py` verifier the codex doc has declared since 2026-05-12,
  and the `PARTIALLY_FILLED` edge question). T3 got a warning NOT to wait on `reference_position`/`credit`, since
  that edge is operator-gated on Q12-Q16 and will not clear on its own — with the two points that ARE settled
  (`credit` optional; strategy-owned/strategy-computed) called out so T3 can design against them today.
  **Also rescued 3 issue docs that existed ONLY in this slot's local clone** (defi SCE-suffix strategy_ids,
  health-factor monitor with no production entrypoint, MTDS availability data_type-without-venue) — they were
  sitting in an unpushed local commit the outgoing agent never landed, one `git` accident from gone.
  **Process findings, recorded because they cost real time tonight**: (1) `exit 0` lied THREE times — a
  safe-doc-push refusal, a failed lint, and a plan-hygiene block all surfaced as exit 0 through a pipe. Capture
  `$?` directly and grep the log for the verdict; never `| tail` a ship command, which is also how the first
  hygiene failure's own detail got truncated out of view. (2) The PM checkout carries **67 autostash entries** and
  safe-doc-push now calls that "extreme" — it is what produced tonight's merge conflict. (3) Writing
  `BLOCKED-OPERATOR` mid-sentence in a todo silently HOLDS that todo; the hygiene gate is right to fail it. Say
  "gated on an operator ruling" in prose and keep the marker in the leading tag cluster.- 2026-08-20 — **T1 SESSION HANDOVER — second agent took over the tranche under an explicit operator ruling.**
  Not a normal resume: two Claude sessions were live in slot 6 at once. MEASURED at takeover — the incumbent T1
  agent (PID 19387, started 23:13:08) was mid-`quickmerge` (children 26702/26708/27231) shipping the
  QuoteInstruction edge, with `--isolated` holding `schemas.py` evacuated into `stash qm-iso-evac-26708`. The
  incoming agent did NOT edit anything while that was true — it armed a watchdog on the ship's real terminal
  state, confirmed `6be4b136` landed on `origin/live-defi-rollout` and the evac stash cleared, and only then
  retired PID 19387 (SIGTERM, confirmed gone, no orphaned ship children). Operator answered "take over T1, retire
  the peer" when asked; the takeover was not autonomous.
  **Nothing was lost, and that is measured, not assumed**: every tracked file in the UAC tree was byte-identical
  to `origin/live-defi-rollout`, 2 of 3 untracked test files identical, the third differing only by a
  one-character docstring-formatting artifact (`""" "coinbase"` vs `""""coinbase"`). The tree was synced
  `--ff-only` to `6be4b136` (0 ahead / 0 behind) behind a retained safety stash
  `t1-takeover-safety-20260819T230423Z` — deliberately NOT dropped. The older `qm-iso-evac-56777` residue from the
  documented SIGTERM recovery was left alone (never drop foreign WIP).
  **Standing warning for whoever reads this next**: slot 6 still hosts 3 other live `claude` sessions
  (PIDs 2749, 32709, 97270 — two of them ~1d14h old). They share this checkout's `.git/index` and `.git/config`.
  Re-check for a live peer before assuming this tranche is yours.
- 2026-08-19 — **Contract edge #1 landed: `QuoteInstruction` carries the sensitivity triple —
  unified-api-contracts@6be4b136d7. T4 IS UNBLOCKED on this edge.** Shipped by the outgoing agent; VERIFIED
  independently by the incoming one before adopting the claim: `6be4b136` is on `origin/live-defi-rollout`, and
  the landed `schemas.py` blob carries `underlying_instrument_id` (line 328), `delta` (335) and `gamma` (344), all
  three optional. The suite claim was re-measured too — 5 test functions, and the JSON round-trip is real
  (`QuoteInstruction.model_validate_json(original.model_dump_json())` at line 97), which matters because the
  instruction crosses the `EventTransport` seam. NOT re-measured by the incoming agent: the assertion that all 5
  pass (running `pytest` directly is banned, and the outgoing agent's own note records that UAC's gate suppresses
  pytest output on success) — they are on origin and inside the standing suite, so the next `quality-gates.sh` run
  in this repo covers them.
- 2026-08-19 — **Registry P0 #2 landed: chain registries reconciled — unified-api-contracts@27ebc544b2.** Verified
  landed (`27ebc544b2` an ancestor of `origin/live-defi-rollout`; landed blobs re-read). The issue's "three
  registries, three answers" framing is partly a CATEGORY ERROR — measured, they own three different concerns, so
  they were bound by containment invariants rather than merged (merging would have destroyed real distinctions;
  `VENUE_CHAIN_MAP`'s "4 chains" is its scope, not a gap). The REAL defect underneath was worse than under-reporting:
  4 live DeFi venues (`AAVE_V3-SCROLL`, `COMPOUND_V3-SCROLL`, `AAVE-PLASMA`, `FLUID-PLASMA`) parsed to chain tokens
  `KNOWN_CHAINS` did not contain, so every `if chain in KNOWN_CHAINS:` consumer silently else-branched on them.
  Three of the issue's own claims corrected by measurement: `KNOWN_CHAINS` was 12 not 10; `starknet` has NO DeFi
  venue justifying it (`EXTENDED-STARKNET` is CeFi and absent from `ALL_DEFI_VENUES`) so it was deliberately NOT
  added; and `PLASMA` was missing from `KNOWN_CHAINS` too, which the issue did not mention.
  **Process note**: this ship needed a recovery — the first `quickmerge` attempt was SIGTERM'd at the 2-minute
  foreground cap while `--isolated` had the files evacuated from the caller tree. Nothing was lost: the edits were
  in quickmerge's own `qm-iso-evac-<pid>` stash, restored via `git stash apply` and content-verified before the
  re-ship. Run quickmerge in the BACKGROUND in this repo — its pre-commit hooks exceed 120s.
- 2026-08-19 — **Registry P0 #1 landed: `get_venue_asset_group()` fails closed — unified-api-contracts@d4cded41b8.**
  MEASURED, not assumed: the old lookup held 55 capability-declaration `source` keys (`binance`, `databento`) and
  callers pass venue slugs (`BINANCE-SPOT`) — zero overlap, so all 209 registered venues fell through to the
  hardcoded `"cefi"`. Blast radius measured at ZERO code callers fleet-wide, so nothing stored or published was
  corrupted. Verified landed: `d4cded41b8` confirmed an ancestor of `origin/live-defi-rollout`, and the landed blobs
  re-read from that commit carry the raise + the COINBASE fix. QG green (exit 0, full log captured); the gate
  suppresses UAC's own pytest output on success, so I additionally executed both new test files' assertions
  directly as standalone probes — all passed. Second defect found and fixed in the same commit: bare `COINBASE`
  resolved to `defi` (false-match on `COINBASE-ETHEREUM`), the same trap already documented for `BINANCE`.
- 2026-08-19 — **T1 CLAIMED by slot-6·laptop.** No other slot had claimed a tranche (checked: slots 2-5 running
  unrelated work; no tranche plan referenced in any other slot's session). Taking T1 per the coordinator's
  "launch T1 first — four blocking edges terminate here". If another agent is also on T1, that agent should
  re-read this log before editing UAC/UTL.
- **context-scout 2026-08-20**: populated/refreshed context_scope (6 entries)
- 2026-08-20 — **SECOND PRE-COMPACT CHECKPOINT — merges an audit run by a concurrent peer session sharing this
  slot with this session's own subsequent work.** 18 done / 19 open on this plan as of this entry (peer's own
  snapshot read 16/21 — three items it listed "actionable now" were closed by this session AFTER that snapshot:
  venue→chain SSOT + VenueFeature/VenueCapability overlap (`unified-api-contracts@0d7afa29e`) and the
  coverage-floor-registries P1 (`unified-trading-pm@26b8b3ed64`, closed by measurement — already resolved weeks
  earlier). **Do not re-open or re-work those three** — the peer's "actionable now" list is stale on exactly
  those items; everything else in it still stands.
  **Audit (Step 1)**: all three touched repos (`unified-api-contracts`, `unified-trading-library`,
  `unified-trading-pm`) confirmed clean, `ahead=0`, verified against `origin` content directly (not exit codes).
  53 scratchpad files, all disposable probe scripts/QG-log captures — every finding already landed in a commit
  message or this Progress Log; none referenced by path from any committed doc. No secrets, no chat-only findings.
  **Lessons carried forward from the peer session's audit (verified still accurate, not re-derived)**:
  - The plan's own citations of "Q12-Q16" for `reference_position`/`credit` are STALE. The actual current
    blocker is `/plans/active/issues/execution_delta_proxy_repricer_generalization_2026_08_18.md` §15 ("OPEN —
    needs an operator ruling next session"), which supersedes Q12-Q16 with a full FACTOR-STATE MODEL (§11-14,
    shipped this session) and its own 4 named open questions plus 5 outstanding Wave-0 rulings. Read §11-14
    before touching that todo again — it is a real design, not a stub. Worth checking (not yet done): whether
    the `delta`/`gamma`/`underlying_instrument_id` fields already shipped on `QuoteInstruction`
    (`unified-api-contracts@6be4b136d7`) are a valid special case of the §11 model or need revisiting once it's
    formally adopted.
  - `unified-api-contracts` quality-gates.sh runs 180-1076s (contention-dependent) — ALWAYS background it, never
    foreground (this session independently hit the same 120s-foreground-cap lesson via a SIGTERM'd first attempt
    early on).
  - **This slot has a genuinely concurrent peer session actively working the SAME T1 plan.** `git pull --ff-only`
    immediately before every plan edit; expect conflicts; resolve ADDITIVELY (never blind-overwrite) — this
    session hit and cleanly recovered from exactly this twice (a `check_todo_regression` catch on its own
    provenance-preservation edits, and a `SELF-INFLICTED CONFLICT MARKER` auto-recovery on the FACTOR-STATE MODEL
    ship). `VenueType = {SINGLE_VENUE, META_BROKER, DATA_AGGREGATOR}` vs `VenueCategoryV2 = {CEFI, DEFI, ...}` are
    easy to confuse in test fixtures — cost the peer session one failed run.
  - **This session's own lesson, not yet in the peer's list**: before treating a locally-missing change as a
    revert/data-loss event, run `git log HEAD..origin/<branch>` FIRST. This session spent real effort
    reconstructing `TransferCapabilityV2` from a diff already in context after it "disappeared" locally — it had
    actually already landed via this SAME slot's earlier (compacted-out) work (`unified-api-contracts@45a545e5ad`)
    minutes before this checkpoint's predecessor was written; the "revert" was just the working tree resetting to
    post-commit-clean state. A same-slot earlier-session commit reads identically to a hostile revert until you
    check the log.
  **Verdict: Safe to compact: YES.** All shipped work committed and pushed, `ahead=0` on every touched repo,
  verified against actual trunk content.

- 2026-08-20 — **THIRD PRE-COMPACT CHECKPOINT — lightweight, since the second checkpoint landed only minutes
  earlier and this session's only work since was one closure.** 19 done / 18 open on this plan as of this entry.
  **Closed since the second checkpoint**: the `(venue, instrument_type) -> data_types` combinator P1 —
  STALE, already resolved weeks earlier (`unified-api-contracts@fa9cece5`, confirmed a real ancestor of
  `origin/live-defi-rollout`, not a doc claim taken on faith); every `[CODE]`/`[DESIGN]` todo in the source issue
  was already checked, only 2 out-of-scope `[DATA]` backfill items remain open there.
  **Audit**: `unified-api-contracts` and `unified-trading-library` clean, `ahead=0`. `unified-trading-pm` was
  momentarily 9 commits behind (routine fleet activity — T4's own plan + manifest housekeeping, unrelated to
  T1) and carried one stale staged artifact (matched HEAD byte-for-byte, unstaged harmlessly) — `ff-only` pulled
  clean, now `ahead=0` / status empty. **Observed but deliberately NOT touched**: the concurrent peer session
  sharing this slot is actively mid-edit on `execution_delta_proxy_repricer_generalization_2026_08_18.md`
  (mtime <2 min at observation time) and had a new `/codex/04-architecture/cross-domain-state-fabric.md` doc
  in progress — that is their own live WIP, not mine to commit, stage, or promote. If a future session finds
  this file dirty again, check its own commit/push status before assuming loss — the same "check git log before
  panicking" lesson from the prior checkpoint applies.
  **In-progress, not yet started**: the W8 weightings SSOT todo (line ~416) — read-only investigation only so
  far (`strategy-service/strategy_service/portfolio_allocator/__init__.py`'s docstring: three real weighting
  concepts exist — generic portfolio-statistic weighting engines (axis-agnostic: FIXED/PNL_WEIGHTED/
  SHARPE_WEIGHTED/RISK_PARITY/KELLY/MIN_CVAR/REGIME_AWARE/MANUAL) vs per-archetype RANK allocators that weight
  along a named axis (coin/venue/protocol/expiry/LST) — no UAC-side code written yet. Next step: read
  `archetypes_simple.py` + `archetypes_rank.py` + `param_schema.py` for the exact current field/param names
  before declaring the SSOT, so the declaration uses real terminology, not invented names.
  **Verdict: Safe to compact: YES.** Zero uncommitted work of this session's own exists anywhere; the one
  dirty file observed belongs to a different, live session.

- 2026-08-20 — **`VenueCapabilityV2.collateral_rules`/`MarginSpec` population (W5) — flagged, deliberately NOT
  fabricated.** Per `plans/audit/results/venue_transfer_custody_collateral_research_2026_08_18.md`, the schema is
  real and already consumed but populated for zero venues — the doc itself labels this "Population, not schema
  design." This is real per-venue collateral/margin data (LTV ratios, haircuts, margin tiers) for 192+ venues,
  feeding a live risk system. T1 will not invent financial risk parameters; getting these wrong could cause real
  harm. Left as `BLOCKED-OPERATOR-DECISION` in the plan (real data-research required, not code) rather than either
  fabricating values or silently skipping the line item.
- 2026-08-20 — **"External API surface" section re-triaged; 3 of 7 items were misassigned to T1, 1 shipped, 1 held
  on a genuine design question, 1 (wizard) left untouched.** Investigated the P0 "replace HTTP 501s with
  transfer/bridge/atomic/cancel" todo starting from `unified-trading-api/routes/execution.py` (T1-owned) —
  confirmed that repo has NO `/external/*` surface and no `501`s anywhere (grep, `.venv` excluded). Traced the
  artefact's actual citation (line 1361: `execution-service/execution_service/api/external_instruction_api.py`) —
  `execution-service` is T4-owned, not T1's. Same pattern held for the counterparty-facing-surface item
  (`strategy-service`, T3-owned), the API-surface-enumeration item (spans `instruments-service`+
  `market-tick-data-service`, T2-owned, and `execution-service`, T4-owned — redirected to T5 as read-only
  doc-generation, matching its existing `instruction_actions.py` tooling), and the Ceffu item
  (`execution-service/transfer_coordinator.py`, T4-owned, confirmed by the artefact's own file citation).
  Redirected all four via `[FROM-T1]` inbound flags (`unified-trading-pm@3837c66bbf`) with full measured context
  so the receiving tranche doesn't re-derive it, and closed T1's own copies as SUPERSEDED (kept for provenance,
  not deleted — the `check_todo_regression` conservation rule).
  **Kill-switch/flatten-position instruction todo** — genuinely half-T1 (adding them to
  `StrategyInstructionType` as caller-submittable actions, not just internal system behaviour) but is an open
  design call, not a mechanical enum fill: `INSTRUCTION_TYPE_TO_OPERATIONS` is a total mapping and control
  instructions may not decompose into `OperationType` steps the way trade/DeFi ones do. Held open, pending T4's
  answer on the needed shape (asked in the same inbound flag) — did not guess and ship a contract T4 would have
  to rework.
  **W17 fee/gas modelling (contracts side) — shipped `unified-api-contracts@01a595d3aa`.** Read
  `plans/epics/system_readiness_master.md` § W17 first (need was "clearing, broker, exchange, gas, and other";
  `exchange_fee_bps`/`gas_cost_usd` already existed on `ExecutionCostEstimate`). Added
  `clearing_fee_bps`/`broker_fee_bps`/`other_fee_bps`, all defaulting to `Decimal("0")` (zero existing/future
  construction call sites broken — none exist yet in this repo, confirmed by grep), deliberately NOT folded into
  `total_cost_bps` (documented, and locked in by a test) so no producer's total silently drifts. 3 tests in
  `tests/internal/unit/domain/execution_service/test_cost_estimate_fee_breakdown.py`, verified passing standalone
  before the full-repo gate (202s, clean — only pre-existing WARN-level findings, no new ones). The
  strategy-service/execution-service wiring ("bake into the decision" / "bake into alpha PnL") is T3/T4's, per the
  todo's own original framing — not redirected, since it already said so.
  **Wizard UI item (P1) left untouched** — genuinely T1-owned (`unified-trading-system-ui`) but not started this
  turn; next session should pick it up, needs `[UI]` + `pw:L2 ✓` + a cited regression spec per the plan's own note.
  **Lesson for future sessions**: a plan-authored P0 naming a specific artefact section is not proof the target
  repo is yours — the artefact cites its own source file per claim (grep the artefact around the todo's exact
  wording before writing code against your own repo's same-named-but-unrelated file).

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
