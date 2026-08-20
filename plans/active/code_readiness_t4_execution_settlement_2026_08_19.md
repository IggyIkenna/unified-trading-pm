---
doc_type: plan
title: Code readiness T4 — execution, settlement and risk
summary: >-
  Tranche 4 of the five-agent code-readiness push — makes execution-service and the settlement and reporting services code-complete. Owns order lifecycle, reconciliation, exchange contract fidelity, the venue-adaptor security audit, fees and gas, and the strategy-to-execution messaging plus external instruction API that is confirmed unbuilt end to end.
status: active
nature: process
asset_group: [cross-cutting]
stage: [execution]
repos: [execution-service, batch-live-reconciliation-service, fund-administration-service, greeks-service, client-reporting-api, trading-agent-service, ibkr-gateway-infra]
scope: [engineer]
tags: [code-readiness, execution, order-lifecycle, reconciliation, security, w22, tranche-4]
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
estimate_baseline_ai_days: 40
estimate_calibrated_ai_days: 16
locked_by:
locked_since:
context_scope:
  [
    /plans/epics/system_readiness_master.md,
    /plans/audit/results/code_completion_scope_2026_08_19.md,
    /codex/12-agent-workflow/commit-push-flip-rule.md,
    /codex/12-agent-workflow/measurement-claims-discipline.md,
    /codex/05-infrastructure/per-tab-worktrees.md,
    execution-service/,
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

# Code readiness T4 — execution, settlement and risk

> **Tranche 4 of 5.** Owned repos — **execution-service, batch-live-reconciliation-service, fund-administration-service, greeks-service, client-reporting-api, trading-agent-service, ibkr-gateway-infra**. Allocated corpus —
> **27 docs** (11 spine, 1 excluded as data-movement), **203 open todos**
> at authoring. You are one of five agents running in parallel on disjoint repos.

**You own the structural reason all 864 readiness rows read `unverified`.** The artefacts state plainly that
"the execution-instruction leg is unverified on all 864 rows". Until this tranche exposes a real per-venue
instruction-path check, T5's readiness dump cannot grade a single row — so treat todo 1 as the highest-leverage item
in the entire five-agent effort. **W22 is confirmed unbuilt end to end**; the only live instruction path today is
manual (`ManualOperationHandler → LiveOrchestrator`).

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
for x in d['tranches']['T4-execution-settlement']['docs']:
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

- [x] ✅ [FROM-T1] P0. **Spun out into the dedicated W22 AO plan, 2026-08-20 —
      `/plans/active/w22_strategy_execution_messaging_external_api_2026_08_20.md`** (same underlying ask as this
      tranche's own "Build the external instruction API surface" todo, closed the same way above). Original
      text kept below for provenance. **Replace the honest HTTP 501s in `execution-service`'s `/external/instructions` router** — T1
      re-triaged its own plan's "External API surface" section 2026-08-20 and found this targets `execution-service`,
      not any T1-owned repo. Only the TRADE action is live end-to-end today (routed through
      `ManualOperationHandler → LiveOrchestrator.execute_instruction()`); the other 10 (swap, lend, borrow, stake,
      unstake, quote, transfer, bridge, atomic, cancel) return an honest HTTP 501
      (`platform-external-api-walkthrough.html` line ~1361, verified against
      `execution-service/execution_service/api/external_instruction_api.py`).
      **Correction to this item, same day**: the first pass below checked the wrong, legacy vocabulary
      (`StrategyInstructionType`) and wrongly told you QUOTE/TRANSFER/CANCEL were missing from UAC — they are
      not. The CURRENT contract is `unified_api_contracts.internal.architecture_v2.schemas.StrategyInstructionV2`
      (a Pydantic union), and it already has real dataclasses for **every one of the 10**:
      `SwapInstruction`/`LendInstruction`/`BorrowInstruction`/`StakeInstruction`/`UnstakeInstruction`/
      `QuoteInstruction`/`TransferInstructionV2`/`BridgeInstructionV2`/`AtomicInstruction`/`CancelInstruction`, each
      keyed off a real `InstructionActionV2` enum member. If `external_instruction_api.py` 501s on these today, the
      gap is in execution-service's own dispatch/construction logic, not a missing UAC type — check what
      `external_instruction_api.py` actually imports and isinstance-checks against before assuming a contract gap.
      T1 already closed the ONE genuine UAC-side gap this surfaced (below, separately) — the 4 settlement actions
      with an enum member but no dataclass. If you find a REAL missing type while wiring this, name it exactly
      (file + expected fields) and T1 will add it — don't invent a parallel local enum either way; the mapping is
      load-bearing and T1 would rather extend it once than have it drift from a shadow copy.
      (Superseded text, kept for provenance: the original claim below this line was wrong.)
      ~~T1 measured the UAC-side vocabulary first so you don't have to: `StrategyInstructionType`
      (`unified_api_contracts/internal/domain/strategy_service/_instruction_base.py`) already covers SWAP/LEND/
      BORROW/STAKE/UNSTAKE/BRIDGE/FLASH_LOAN(=atomic), backed by a total `INSTRUCTION_TYPE_TO_OPERATIONS` mapping.
      QUOTE, a standalone TRANSFER (distinct from BRIDGE), and CANCEL are genuinely absent from the contract too —
      if the real implementation needs those as first-class instruction types (not just `OperationType` steps
      internally), ask T1 for the contract addition rather than inventing a parallel local enum; the mapping is
      load-bearing and T1 would rather extend it once than have it drift from a shadow copy.~~
- [x] ✅ [FROM-T1] P1. **Shipped — `unified-api-contracts@f5fc118ae1`.** The 4 BATCH-settlement-gap
      dataclasses this tranche asked for below — see that item's own entry for full detail. `WithdrawInstruction`
      and `RepayInstruction` are done (rate-matched inverses of `LendInstruction`/`BorrowInstruction`, added to
      `StrategyInstructionV2`). `LpMintInstruction`/`LpBurnInstruction` are still open — genuinely need the DeFi LP
      position shape specified, which is your call per the original request, not invented here.
- [ ] [FROM-T1] P1. **Kill-switch / flatten-position as instructions a caller can send** — both are already
      conceptually present as system behaviour but not expressible as an instruction on the envelope
      (`platform-external-api-walkthrough.html` §25). T1 has deliberately NOT added `KILL_SWITCH`/
      `FLATTEN_POSITION` to `StrategyInstructionType` yet — it is a genuine design call (does a control instruction
      decompose into `OperationType` steps at all, or does it need its own dispatch path — recall
      `INSTRUCTION_TYPE_TO_OPERATIONS` is a total mapping over every member) and T1 does not want to guess a shape
      you then have to rework. State what execution-service actually needs and T1 will land it, or say if T1's
      first reasonable draft is fine to just ship.

      **Answered 2026-08-20, then CORRECTED same day — my first answer was wrong, caught by re-checking today's
      LDR rulings before proceeding further.** First pass recommended NOT adding `KILL_SWITCH`/`FLATTEN_POSITION`
      to `StrategyInstructionType`, reasoning from `AccountInstruction`'s separate-authority-model rationale alone
      — I hadn't re-read `/plans/epics/system_readiness_master.md` W22 before answering. **That epic section is
      the actual operator-ruled scope for this exact question**, and it explicitly requires the opposite: "Add
      kill-switch and flatten-position as instructions, not only as internal system behaviour... a caller must be
      able to send them, scoped the same way the internal kill-switch is (all-live / per-archetype / per-venue)."
      **Corrected recommendation: DO add them.** The two answers reconcile, they don't actually conflict on
      substance — the epic's own "scoped the same way the internal kill-switch is" clause is exactly my original
      authority-model concern, just answered as an implementation requirement (external kill/flatten needs the
      SAME authorization gating `AccountInstruction`/`kill_switch.py` already enforce — `authorization_id` +
      admin auth, not open access) rather than a reason to skip the feature. T1: please add `KILL_SWITCH`/
      `FLATTEN_POSITION` to `StrategyInstructionType`, each carrying an authorization/approval field mirroring
      `AccountInstruction`'s `authorization_id` (this tranche will wire the execution-service handler to reuse
      the existing `kill_switch.py`/`AccountInstructionOrchestrator.CLOSE_ALL` machinery underneath, not
      duplicate it — a strategy-envelope KILL_SWITCH/FLATTEN_POSITION instruction becomes a thin translation into
      the SAME already-authorized internal call, never a second independent authority path). Apologies for the
      churn — should have re-checked the epic section before answering the first time.
- [x] ✅ [FROM-T1] P1. **Spun out into the dedicated W22 AO plan, 2026-08-20 —
      `/plans/active/w22_strategy_execution_messaging_external_api_2026_08_20.md`'s "Messaging bridge" section**
      (execution-service opened its own EventTransport subscriber build there; T3's matching inbound item is
      T3's own to track — this tranche's side is no longer stalled waiting). Original text kept below for
      provenance. **Joint with T3 — strategy→execution messaging bridge.** See the matching `[FROM-T1]` item on
      T3's `## Inbound requests` for full detail (no internal messaging connects strategy-service's decisions to
      execution-service today). Whichever tranche has capacity first can open the UTL `EventTransport` subscription
      on the execution side (subscribing to strategy's instruction stream + the features-service groups it needs)
      — don't let it stall waiting on the other.
- [ ] [FROM-T1] P2. **Ceffu integration** — `execution-service/execution_service/transfer_coordinator.py` is
      confirmed the target (the artefact cites it directly). It's a stub pending its API spec; build the full code
      path behind the provider interface, credential-gated, never descope. Do NOT invent a distinct Ceffu custody
      member — the artefact already lists Ceffu alongside Copper/manual-transfer/prime-broker eligibility on
      `VenueCapabilityV2.transfer_capability` (shipped `unified-api-contracts@45a545e5ad`).

      **Checked 2026-08-20, genuinely not actionable yet — not the same blocker as BLOCKED-CREDENTIALS.**
      `transfer_coordinator.py` has ZERO Ceffu/Copper/prime-broker code today — only a generic `TransferHandler`
      Protocol and one concrete `_SubaccountMoveHandler` (Binance/OKX only). A conforming Ceffu handler needs
      Ceffu's actual REST/API surface (endpoints, auth scheme, request/response shapes) to implement correctly —
      this todo's own text already says "pending its API spec," meaning the spec doesn't exist in this workspace
      at all, not just missing credentials. Building a `TransferHandler`-conforming class without it would mean
      inventing an interface with no basis to verify against — real risk of shipping something plausible-looking
      but wrong for a CUSTODY integration. Deliberately not attempted rather than guessed. `BLOCKED` on the actual
      Ceffu API spec landing somewhere in this workspace (not a credential ask — a documentation ask).
- [x] ✅ [FROM-T5] P0. **Shipped — `execution-service@7202047877`.** Expose a real per-venue instruction-path check in `execution-service` — this is the leg the
      readiness dump names as the structural reason its rows cannot confirm execution readiness. T5 has done the
      groundwork and needs only the venue-aware surface; the shape asked for is deliberately minimal.

      **What T5 measured 2026-08-20, so you do not repeat it** (`unified-trading-pm`
      `cursor-configs/skills/readiness-state-dump/scripts/instruction_actions.py`):

      1. `execution_service/v2/policy_resolver.py` is **NOT** an instruction-adaptor registry, despite the readiness
         SKILL.md having claimed so (now corrected). It resolves an execution *algorithm* keyed by
         `(client_id, slot_label)`; venue appears only as an `applies_to` gate dimension (`venue_category`).
      2. The only action-keyed dispatch that exists is `backtest_v2/action_handlers.py::resolve_settlement`, which is
         **venue-independent and backtest-scoped**. AST-measured coverage: **11/16 `InstructionActionV2` actions have
         a settlement path** (10 handled + `CANCEL` control-plane no-fill by design); **5 raise
         `UnhandledActionError`: `CONVERT_DUST`, `LP_BURN`, `LP_MINT`, `REPAY`, `WITHDRAW`**. `REPAY`/`WITHDRAW` are
         core lending actions; `LP_MINT`/`LP_BURN` are what the enum's own comment says `DEFI_LP_CONCENTRATED` emits.
      3. Mapping actions onto UAC `operation_details` keys was considered and **rejected as drift** — that vocabulary
         is per-venue idiosyncratic (`place_order` / `create_order` / `new_order` / `post_order` / `add_order` /
         `submit_order` / `buy`+`sell`) and mixed with feed endpoints, across 47 of 67 registered sources. Please do
         not build the readiness check on that mapping either.

      **Shape T5 needs** — anything callable from a subprocess probe under `execution-service/.venv`, mirroring the
      existing `_execution_order_capability_probe.py` (stdin: JSON venue list; stdout: JSON dict). Concretely, per
      canonical dash-form venue, per env (`mainnet`/`testnet`):
      `{venue: {action_name: "supported" | "unsupported" | "unknown"}}` over `InstructionActionV2` members. A real
      `unsupported` is as valuable as a `supported` — the dump reports a genuine negative as `not_ready`. `unknown`
      keeps the leg honestly `unverified` rather than inventing a pass.

      T5 is NOT idle-waiting on this: the leg already prints `unverified` per venue with a measured denominator, and
      the global handler gap is surfaced as a dump-level finding. Wire-up on T5's side is a one-line probe call.
      Evidence: `/plans/active/code_readiness_t5_readiness_observability_presentations_2026_08_19.md` Progress Log,
      2026-08-20.

      **Shipped 2026-08-20**: `instruction_action_support(venue)` on `execution_service.readiness` returns exactly
      the requested shape — `{"mainnet": {...}, "testnet": {...}}` over every `InstructionActionV2` member, each
      `"supported"`/`"unsupported"`/`"unknown"` — additive to the already-frozen `instruction_path_availability`
      contract (same probe call, new key, no breaking change). T5 still needs to wire the consuming side.

> **T1 unblock notice 2026-08-20** — UAC `OrderStatus` is now the full 9-state machine the codex SSOT describes.
> `FAIL_OUTBOUND` and `RECONCILED` exist, and so do `ORDER_STATUS_TRANSITIONS`, `TERMINAL_ORDER_STATUSES`,
> `is_terminal_order_status()` and `is_legal_order_transition()`, all exported from the top-level
> `unified_api_contracts` facade. You are unblocked on this edge; the two todos below are the follow-through.

- [x] ✅ [FROM-T1] P1. **Migrated — `execution-service@35f0bfb1b`.** `OrderStatus.PENDING`/`.OPEN` renamed to
      `.PENDING_NEW`/`.NEW` in every site that genuinely imports UAC's enum: 5 source files
      (`betfair_order_mapping.py`, `kalshi.py`, `polymarket_clob.py`, `kraken_futures_orders.py`,
      `kraken_rest_adapter.py`) + their 2 test files (`test_kraken_adapter.py`, `test_kalshi_adapter.py`) — 18
      call sites total. **Correction to the 24-site blast-radius estimate**: 6 of the original 24 were never UAC's
      enum at all — `execution_service/orders/oms.py` and `trade_execution/oms/persistent_oms.py` each define
      their OWN LOCAL `OrderStatus(StrEnum)` (7-state: PENDING/VALIDATED/SUBMITTED/PARTIAL_FILLED/FILLED/
      REJECTED/CANCELLED — a different type, not an alias) plus 3 test files that exercise them
      (`test_order_manager.py`, `test_oms.py`, `test_oms_decimal.py`). An initial pass renamed all 24
      mechanically and hit `AttributeError: type object 'OrderStatus' has no attribute 'PENDING_NEW'` on those 6 —
      reverted them to `.PENDING` (byte-identical to origin, confirmed via `git diff`) since they were never UAC's
      alias to begin with. 18/18 true UAC sites now use the renamed members; repo-wide grep for
      `OrderStatus\.PENDING\b`/`OrderStatus\.OPEN\b` against UAC's import returns zero. **Safe to delete the two
      transitional aliases from execution-service's side** — T1 still needs to confirm no other fleet consumer (UI
      aside, which T1 already owns) before actually deleting them.
- [x] ✅ [FROM-T1] P1. **Written and shipped — `execution-service@69a9a088be`.** Real validation now exists to
      assert against: `orders/oms.py` and `trade_execution/oms/persistent_oms.py`'s `update_order_status()` were
      MEASURED 2026-08-20 to accept any status string with ZERO transition enforcement (real production callers
      confirmed via `handle_nautilus_order_event`/`reconcile_with_nautilus`) — a late fill racing a cancel could
      silently overwrite a terminal CANCELLED record back to FILLED. Fixed via a local-status -> UAC-canonical
      mapping + `is_terminal_order_status()`. **Deliberately narrower than the full `ORDER_STATUS_TRANSITIONS`
      edge set** — the pre-existing `tests/unit/live/test_oms.py::test_oms_handle_nautilus_order_canceled` (et
      al.) correctly cover a real fast-path where a venue-confirmed terminal event arrives while the local record
      is still PENDING (no separate `OrderSubmitted` ack processed first); strict edge-by-edge enforcement broke
      those 4 real tests on first attempt, so the invariant actually shipped is narrower but still real: **once
      terminal (CANCELLED/FILLED/REJECTED/EXPIRED/FAIL_OUTBOUND), the only legal further move is RECONCILED** —
      catches state resurrection, tolerates the legitimate skip-ahead path. `tests/unit/orders/test_state_machine.py`
      pins both the mapping function and the `update_order_status()` integration on both files.
      `execution_service/orders/tracker.py`'s bare-string vocabulary (`"AMENDED"` etc.) was investigated
      separately and found to be **dead code — zero production instantiation sites of `OrderTracker` anywhere in
      the repo** (only test/re-export references), so it was correctly left untouched rather than reconciled —
      not a gap, a confirmed non-issue.
- [x] ✅ [FROM-T1] P2. **Decided: `PARTIALLY_FILLED -> CANCELLED / EXPIRED` IS a legal transition** —
      `unified-trading-pm@c74d869b36` (codex `order-state-machine.md` amended: diagram + events table widened,
      ruling + evidence recorded 2026-08-20). Real CLOB venues let an operator cancel the still-working remainder
      of a partially-filled order (final status reports cancelled with nonzero filled quantity, never forced to
      `FILLED` first); corroborated in execution-service's own code, which already treats `PARTIALLY_FILLED` as an
      open/cancellable state (`trade_execution/oms/tracker.py`). The codex doc — the SSOT — is now amended; the
      code (`ORDER_STATUS_TRANSITIONS` in UAC) is NOT yet widened to match, filed as a `[FROM-T4]` inbound request
      on T1's plan since T4 does not edit UAC directly.

## Todos

### W22 — strategy to execution messaging and the external instruction API

- [x] ✅ [BACKEND] P0. **Spun out into a dedicated AO plan, 2026-08-20** —
      `/plans/active/w22_strategy_execution_messaging_external_api_2026_08_20.md`, per the 2026-08-19 operator
      ruling directing this + the security audit be authored as dedicated plans rather than tracked inline here.
      That plan carries the full real detail (strategy-service already publishes via `EventTransport` keyed on
      `atomic_instruction`; the missing piece is execution-service's subscribe side) plus its mandatory gated
      finalize plan. This todo closes here; track further progress there, not in this doc.
- [x] ✅ [BACKEND] P0. **Expose a real per-venue execution-instruction-path check** — **execution-service@b70d2edb16**
      (landing verified independently of quickmerge's exit code: all six new files resolve under
      `git cat-file -e origin/live-defi-rollout:<path>`, and `git diff --stat origin/live-defi-rollout` is empty for
      the two modified files). `execution_service/readiness/instruction_path.py` exposes
      `instruction_path_availability(venue)`; `python -m execution_service.readiness` is the cross-venv probe.
      T5 has the frozen contract under their `## Inbound requests` (`unified-trading-pm@34999f0adf`), posted before
      the code landed so they were never idle-waiting. Measured verdicts are in the Progress Log.
- [x] ✅ [BACKEND] P0. **Spun out into the same dedicated W22 AO plan, 2026-08-20** —
      `/plans/active/w22_strategy_execution_messaging_external_api_2026_08_20.md`'s "Instruction action
      vocabulary" section carries the real remaining scope: `TRADE`/`QUOTE` are wired
      (`execution-service@dc4fad8de7` for QUOTE); every other `InstructionActionV2` member 501s, and the plan
      names the exact blocker (no `DeFiAdapter` construction/caching factory exists yet — modeled on
      `account_orchestrator.py`'s `_default_order_adapter_factory` pattern) plus per-action wiring todos. This
      todo closes here; track further progress there, not in this doc.
- [x] ✅ [BACKEND] P1. **Delta-proxy repricer — PRICE leg generalized + receipt point rebuilt** —
      **execution-service@dc4fad8de7**. T1's `QuoteInstruction` extension landed
      (`unified-api-contracts@6be4b136d7`), unblocking this. `quote_instruction_to_delta_proxy_params` now reads
      `underlying_instrument_id`/`delta`/`gamma` instead of hardcoding `delta=1` + self-underlying, treating each
      `None` as the self-underlying case UAC documents (so every Spot/Perp quote is byte-identical to before —
      the existing default tests still pass unchanged). `DeltaProxyRepricer._reprice` already implemented
      `effective_delta = delta + gamma * underlying_move` with `max_adjustment_pct` clamping; only the converter
      was discarding the inputs. The deleted `QuoteHandler` receipt point is rebuilt on the DEPLOYED surface:
      `POST /external/instructions` with `action=QUOTE` registers against `QuoteMaintainer` and answers
      `REGISTERED` with an explicit "No order was placed" note — registration arms repricing, and no
      underlying-tick loop exists, so claiming `SUBMITTED` would be false. MEASURED: `delta=0.5` on a `+100`
      underlying move gives `price_adjustment=+50`; a `-0.38` put delta survives unclamped; the triple survives
      the HTTP boundary; `CANCEL` still returns 501. Also fixed dead pointers in both engine modules (they named
      the deleted `v2.handlers.QuoteHandler` as the receipt point, and carried a scope note claiming the UAC
      fields did not exist). Evidence:
      `/plans/active/issues/execution_delta_proxy_repricer_generalization_2026_08_18.md`.
- [ ] [BLOCKED-OPERATOR] P1. Delta-proxy — the POSITION and CREDIT legs of the triple. NOT deferred by this
      tranche. **RE-CHECKED 2026-08-20, still genuinely blocked — reference updated, was stale.** The Q12-Q16
      citation this todo carried is itself stale per T1's own plan: the actual current blocker is
      `/plans/active/issues/execution_delta_proxy_repricer_generalization_2026_08_18.md` §15 ("OPEN — needs an
      operator ruling next session"), which supersedes Q12-Q16 with a full FACTOR-STATE MODEL (§11-14) and its
      own 4 named open questions plus 5 outstanding Wave-0 rulings — a real design, not a stub. Execution-side
      work resumes the moment that shape is decided; the price leg above is independent of it and is already
      shipped.

### W11 — order lifecycle and execution state

- [x] ✅ [BACKEND] P0. **Fix CeFi live venue-string dispatch — ALREADY SHIPPED; this todo was stale at
      authoring.** MEASURED 2026-08-20 in code, not from the issue's checkboxes:
      `execution_service/trade_execution/factory.py` imports and delegates to UAC's shared
      `split_venue_base_and_suffix` helper (`:14`, `_split_venue_suffix` at `:166` calling it at `:179`,
      `_resolve_venue_str` at `:193`) — the fix landed `execution-service@fcc6bbcc2c` (P0) +
      `execution-service@cba9ff511d` (P1 shared-helper migration) on 2026-08-17, before this session started.
      Strategy-service's mirror-image position-factory defect was independently fixed the same day
      (`strategy-service@9027c2f5a9`). Full detail, including the deeper COINBASE-FUTURES/CDE misroute risk that
      was closed alongside the ValueError fix: `/plans/active/issues/cefi_live_venue_string_dispatch_broken_2026_08_16.md`
      (both P0s + the P1 + the P2 non-CEFI audit are `[x]`; two low-priority P3s remain open there, dormant/
      non-blocking, not this tranche's to chase).
- [x] ✅ [BACKEND] P0. Add CANCELLED and AMENDED to `OrderTracker` — **ALREADY SHIPPED; this plan's todo was
      stale at authoring.** MEASURED 2026-08-20 in code, not from the issue's checkboxes:
      `execution_service/orders/tracker.py:51` `mark_cancelled()` sets status `"CANCELLED"`, `:61`
      `mark_amended()` sets `"AMENDED"`, and `:117` `is_instruction_complete()` treats
      `terminal_statuses = {"FILLED", "CANCELLED"}` — so a cancel-only instruction DOES flip complete. Both are
      called from the live surface (`api/manual_instruction_api.py:473` `/cancel`, `:551` `/amend`). The source
      issue's remaining open item is a P3 (`instruction_to_order_ids` staleness), not this P0. Evidence:
      `/plans/active/issues/execution_order_tracker_missing_cancelled_amended_status_2026_08_17.md`.
- [ ] [BACKEND] P0. Implement the full 9-state order lifecycle — T1's `OrderState`/`OrderStatus` contract is now
      landed (see the FROM-T1 unblock notice above), so this is UNBLOCKED. **PARTIAL PROGRESS 2026-08-20,
      `execution-service@69a9a088be`** (full detail on the `test_state_machine.py` todo above — not duplicated
      here): the real safety gap this todo exists to close — nothing enforced `is_legal_order_transition` — is now
      closed for the two LIVE vocabularies (`orders/oms.py` + `trade_execution/oms/persistent_oms.py`'s duplicate
      local 7-state enum), via terminal-state-never-overwritten validation. **What remains genuinely open, not
      done**: the full single-source-of-truth vocabulary UNIFICATION this todo originally scoped — the two local
      files still duplicate their own `OrderStatus(StrEnum)` rather than reading through UAC's canonical enum, and
      `orders/tracker.py`'s bare-string vocabulary was investigated and confirmed **dead** (zero production
      `OrderTracker()` instantiation sites — grepped repo-wide) rather than reconciled, since reconciling
      genuinely-dead code would be motion without safety value. Collapsing `orders/oms.py` and
      `trade_execution/oms/persistent_oms.py`'s literal file-level duplication into one shared module is a real,
      separate, still-open follow-up (not attempted — touching either file safely requires re-verifying it against
      `ManualOperationHandler`'s existing `/cancel`/`/amend` callers, the exact cross-file risk this todo always
      named). Left open rather than closed on a technicality.
- [x] ✅ [BACKEND] P0. Fix the broken emergency close-all path — **CONFIRMED 2026-08-20, and worse than this todo
      said.** Two independent defects, both measured: (a) no `/api/orders` route exists anywhere under
      `execution_service/api/`, so the strategy-side POST reaches nothing; (b) even the in-process path is a
      no-op — `v2/account_orchestrator.py:48` `AccountInstructionOrchestrator.dispatch()` validates
      `authorization_id`, logs, appends to `_history` and returns `accepted=True` **without closing anything**; its
      own module docstring says "real venue wiring lands in follow-up commits once each venue adapter exposes the
      right account-ops surface".
      **CORRECTION to an earlier reading in this plan's log**: I first wrote that this "reports success while
      closing nothing" in production. Re-measured — `AccountInstructionOrchestrator` has **ZERO production
      callers**: the only references anywhere are its own module and the `v2/__init__.py` re-export
      (`grep -rn "AccountInstructionOrchestrator" execution_service/`). So today it is an unreachable latent trap,
      NOT a live failure. That lowers the urgency but not the requirement: the moment a route is put in front of
      it, `accepted=True` becomes a lie about an emergency stop. Fix needs BOTH, in this order: real per-venue
      CLOSE_ALL wiring behind `AccountActionV2.CLOSE_ALL` (and a loud rejection for any action with no runner),
      THEN a route on the deployed app. Never the route first.

      **Wiring half SHIPPED 2026-08-20 — `execution-service@96411b68c9`.** `AccountInstructionOrchestrator._execute_close_all`
      now resolves a real credentialed `OrderAdapter` (same trusted credential path `LiveExecutionHandler` uses),
      reads real open positions via `BaseCLOBAdapter.get_positions()`, and submits an offsetting MARKET order per
      position (SELL for LONG, BUY for SHORT) — one leg's failure does not abort the rest, and the result honestly
      reports a partial failure. CLOB/CeFi-scoped only; DeFi/sports have no equivalent close-out primitive.
      Deliberately does NOT bundle cancelling resting orders (CLOSE_ALL means flatten positions, not also
      CANCEL_ALL). 8 new tests.

      **Route half SHIPPED 2026-08-20 — `execution-service@c0839616be`.** `POST /account/instruction` (new
      `execution_service/api/account_instruction_api.py`) registered on BOTH `api/app.py` and `api/main.py` (the
      real deployed entrypoint) — routes every `AccountInstruction` through the same `AccountInstructionOrchestrator`
      this todo's wiring half built. Kill-switch/drain-mode checked before dispatch; a business-level rejection
      (missing `authorization_id`, kill-switch active, a failed venue leg) returns HTTP 200 `accepted=False`, never a
      4xx — matching `manual_instruction_api`'s own documented convention that rejection is not a transport error. 5
      new HTTP-level tests, including one exercising real CLOSE_ALL flattening through the router via the same fake
      order-adapter-factory convention `test_account_orchestrator.py` established. Both halves now done — this todo
      is CLOSED.
- [x] ✅ [BACKEND] P0. Build state recovery so a restart, a partial fill or a reconciliation drift cannot leave the two
      sides disagreeing. The artefacts describe this as guaranteed; it is not built.

      **Real scope MEASURED 2026-08-20 — more nuanced than "not built": the FRAMEWORK exists and is even
      already-hardened this session, but its two core dependencies are explicit stubs, and it is never invoked at
      startup at all.** `engine/startup/order_recovery.py`'s `OrderRecoveryEngine` (407 lines: per-venue
      circuit-breaker-gated recovery, orphan reconciliation, partial-fill application — this session's own
      shard-isolation fix, `execution-service@ff0b43b5d3`, already hardened its `recover_venue()`) is real,
      tested, working machinery. But: (1) `OrderBook`'s own docstring says "Minimal in-memory order registry for
      testing/stub purposes. Production wiring should inject the live Nautilus OMS order registry" — it is never
      backed by `orders/oms.py`/`trade_execution/oms/persistent_oms.py` (this session's own transition-validation
      fix, `execution-service@69a9a088be`) or any other real persistence; (2) `_VenueAdapter`'s docstring says
      "Stub venue adapter... Production implementation should delegate to market-tick-data-service market_interface
      (UMI) venue adapters... stub returns deterministic empty data" — `fetch_open_orders()` always returns `[]`,
      `cancel_order()`/`confirm_cancel()` always return `True` without calling anything; (3) `grep -rln
      "OrderRecoveryEngine("` across the whole repo (excluding tests) returns ZERO production instantiation
      sites — it is never called from `main.py`, `_run_live_async`, or anywhere else at startup. Wiring
      `OrderRecoveryEngine()` into startup with its DEFAULT construction would produce real-looking
      `ORDER_RECOVERY_COMPLETED` log events while silently reconciling nothing — the same defect class as the
      already-fixed `AccountInstructionOrchestrator` ("accepted=True while closing nothing") and CCXT-withdraw-stub
      bugs this tranche found earlier. **Real fix is 3 pieces, not 1**: implement a real `OrderBook` backed by the
      persistent OMS, a real `_VenueAdapter` backed by `get_order_adapter()` (`trade_execution/factory.py:461`,
      same factory `_create_orchestrator_for_venue` already uses), then wire `OrderRecoveryEngine.run(venues)`
      into `_run_live_async` before instructions start flowing.

      **Spun out into a dedicated AO plan, 2026-08-20** —
      `/plans/active/w_state_recovery_real_wiring_2026_08_20.md`, operator directly authorized both the spin-out
      AND an immediate sub-agent dispatch against it (not waiting for normal fleet pickup). Second-pass scoping
      found the gap is even deeper than first measured: `_VenueAdapter.fetch_open_orders()` has NO real backing
      capability anywhere in the adapter layer (`grep -n "open_orders\|fetch_open\|get_orders"
      trade_execution/base_adapter.py adapters/order_adapter.py`: zero hits) — building it needs a NEW
      capability added across 8 ccxt-wrapped venues (likely cheap: ccxt has a standard `fetch_open_orders()` most
      exchanges support) plus native REST adapters (kraken/bitfinex/bitget, several already
      `BLOCKED-CREDENTIALS`, build the scaffold regardless). Sized into 3 phases (real `OrderBook`; real
      `_VenueAdapter` incl. the new fetch-open-orders capability; startup wiring) plus close-out and the
      mandatory gated finalize plan. This todo closes here; track further progress there, not in this doc.
- [x] ✅ [BACKEND] P0. **`POST /manual/instruction` 404s on the deployed execution-service — FIXED** —
      **execution-service@9c79bfa0ef** (landing verified by an empty `git diff --stat origin/live-defi-rollout`
      over all three files plus grepping the landed `api/main.py` for `manual_router`). The defect existed only in
      the seam between three individually-correct pieces: `manual_instruction_api.py:57` declares
      `APIRouter(prefix="/manual")`; that router was registered ONLY in `api/app.py:127`; and the `Dockerfile` CMD
      serves `api.main:create_app`. `unified-trading-api`'s caller
      (`unified_trading_api/routes/execution.py:660`, T1's repo) was correct as written — no inbound request was
      needed. `main.py` now registers `manual_router` and installs the handler + limiter in a **symmetric
      lifespan**: not in `create_app()` (which runs at import, so it would mutate globals for every importer), and
      restoring previous values on shutdown (a set-only lifespan still leaked). The handler is the SAME instance
      the external surface uses, so `/manual/instructions/{id}` sees orders submitted via
      `/external/instructions`. MEASURED: before serve both globals `None`; served, `/manual/venues` 200 and
      `/manual/instruction` 422 (validation, not routing); after teardown both `None` again; a bare app with a
      patched handler answers 422 not 500. Took four gate attempts — the three failures are recorded in the
      Progress Log because each was a distinct, reusable trap.
- [x] ✅ [BACKEND] P0. **Reconciled — RESOLVED BY THE SAME-DAY FIX, `execution-service@9c79bfa0ef`.** This todo's
      own "MEASURED 2026-08-20" text captured the state BEFORE that commit landed later the same day (01:01:43
      UTC+1). RE-MEASURED 2026-08-20 against current `main.py`: `create_app()` (`execution_service/api/main.py:107-125`)
      unconditionally registers all four routers — `health_router`, `external_instruction_router`, `manual_router`,
      `account_instruction_router` (the last added by the CLOSE_ALL-route todo above, same day) — with no
      conditional gating any of them. The Dockerfile's `uvicorn execution_service.api.main:create_app --factory`
      CMD therefore serves `/manual/*` (instruction/cancel/amend/instructions/{id}/venues/algos/pending),
      `/external/instructions`, and `/account/instruction` together, not `/external/instructions` alone. DART's
      manual-trade surface reaches this via `unified-trading-api`'s `/execution-service/manual/instruction` proxy
      (`unified-trading-system-ui/context/api-contracts/openapi/unified-trading-system.openapi.yaml:15434` — a
      second deployment target, not an in-process CLI-only path), which now resolves against a real registered
      route instead of 404ing. `api/app.py` still separately registers `manual_router` too (used only by CLI
      handlers per the original finding) — a harmless second FastAPI instance, not a conflict, since the two never
      share a running process.
- [x] ✅ [BACKEND] P1. **Fixed — `execution-service@197e80116`.** Verified the production live orchestrator did
      NOT satisfy the `LiveOrchestrator` protocol it was cast to; real root cause corrected the original
      diagnosis (see Progress Log). Evidence:
      `/plans/archive/2026_08/execution_service_live_orchestrator_protocol_mismatch_untested_2026_08_16.md`
      (archived — fixed).

### Correctness P0s — silently wrong today

- [x] ✅ [BACKEND] P0. Implement the CCXT `withdraw()` stub — **ALREADY SHIPPED; this plan's todo was stale at
      authoring.** MEASURED 2026-08-20 in code: `execution_service/engine/transfers/live_ccxt_adapter.py:227`
      makes the real call `await ccxt_exchange.withdraw(token, float(amount), to_address, params={"chain": chain})`
      — not a commented-out stub — and `engine/transfers/wiring.py:82` resolves credentials and builds one real
      CCXT exchange per wirable CEX_WITHDRAW venue. The issue's one remaining open item is
      `BLOCKED-CREDENTIALS` (exercise end-to-end against a real exchange), which is allowed-pending state 2
      (venue connectivity). Evidence:
      `/plans/active/issues/cefi_ccxt_withdraw_stub_returns_false_confirmed_2026_08_16.md`.
- [x] ✅ [BACKEND] P0. Fix `CloudKmsCustodyProvider`'s silent `chain_id=1` fallback — **ALREADY SHIPPED; this
      plan's todo was stale at authoring.** MEASURED 2026-08-20 in code:
      `execution_service/custody/cloud_kms.py:39` imports UAC's `resolve_chain_id`, and `:387` `_resolve_chain_id()`
      delegates to it (`:399`) so an unmapped chain RAISES instead of signing against Ethereum;
      `custody/local_key.py:15,140` is wired the same way. The issue's remaining open item is `[OPERATOR]` P0
      (inspect live `wallet_provisioning.json`), which this tranche cannot self-serve. Evidence:
      `/plans/active/issues/defi_cloud_kms_silent_wrong_chain_id_fallback_2026_08_16.md`.
- [x] ✅ [BACKEND] P0. Reach-test every connector module — **execution-service@0c0b6a1a40**. **Two of this
      todo's three claims were stale; the third was real.** MEASURED: Marinade, Kamino and Jupiter do NOT have
      zero production callers — `cli/handlers/live_execution_handler.py:519-521` constructs all three and passes
      them to `DeFiAdapter` at `:553`. Pendle WAS genuinely unreachable: the connector and its `PENDLE-ETHEREUM`
      venue map existed, but nothing instantiated it, and it was absent from the `defi_execution` facade, from
      `DeFiAdapter`, and from production construction. Now wired end to end — facade export, adapter constructor
      + `ensure_connected`, route table, real construction in `_build_defi_adapter`.
      **Wired for LEND ONLY, deliberately.** `PendleConnector` has no borrow/repay, and its `withdraw()` is
      simulation-only by its own docstring (real `YT.redeemPY()` with maturity branching is unwired). Routing a
      live WITHDRAW there would return a fabricated success — the same defect class as the CCXT `withdraw()`
      stub this tranche already fixed — so `PENDLE_OPERATIONS` is a strict subset of `LENDING_OPERATIONS` and
      WITHDRAW/BORROW/REPAY raise "Unsupported lending venue". Tests pin that so nobody "completes" the family
      without implementing redemption. The readiness check now derives `PENDLE-ETHEREUM` as `live=deployed`,
      actions `('LEND',)` instead of all-`none`. Evidence:
      `/plans/active/issues/pendle_venue_onboarding_2026_08_16.md`.
- [x] ✅ [BACKEND] P0. Enforce the funds-isolation invariant in code — **ALREADY ENFORCED; this plan's todo was
      stale at authoring.** MEASURED 2026-08-20: `execution_service/transfer_coordinator.py:275` raises
      `CrossClientTransferForbiddenError` when `intent.client_id` differs from the process's `client_id`, with the
      message "Funds NEVER move between different clients (custody + legal boundary)" citing the SSOT directly;
      `validate_intent` (`:173`) and the handler path (`:238-244`) both propagate it rather than swallowing. SSOT:
      `/codex/04-architecture/client-funds-isolation.md`.
- [ ] [BACKEND] P1. Close the BATCH settlement gap the instruction-path check surfaced 2026-08-20. MEASURED via
      `backtest_v2.action_handlers.BATCH_UNHANDLED_ACTIONS`: `resolve_settlement` has no handler for
      `CONVERT_DUST`, `LP_BURN`, `LP_MINT`, `REPAY`, `WITHDRAW`, so each raises `UnhandledActionError` and
      `paper(W) == batch-rerun(W)` cannot hold for any instruction using them — this is why every lending venue
      derives `batch=wired` instead of `deployed`. SSOT: `/codex/09-strategy/operational/paper-batch-live-reconciliation.md` §4.2.

      **3/5 CLOSED — stale text corrected 2026-08-20, this todo had drifted behind its own shipped progress.**
      `CONVERT_DUST` — `execution-service@6f664e80a0`. The UAC `ConvertDustInstruction` schema already existed
      (`unified_api_contracts/internal/architecture_v2/restaking_rewards.py`), it just was never wired into
      `resolve_settlement` or the `StrategyInstructionV2` union — the isinstance branch takes the base
      `StrategyInstructionEnvelope` type so no UAC-side union edit was needed. Priced order-matched (like
      `ATOMIC`), fill_size = Σ input-token amounts. 2 new tests. `WITHDRAW`/`REPAY` — `execution-service@59627fa2d2`.
      **RE-MEASURED 2026-08-20 directly against current code** (this todo's own prior text incorrectly claimed
      these two also had no UAC schema — they do, this was fixed the same session but the todo was never
      updated): `WithdrawInstruction`/`RepayInstruction` exist at
      `unified_api_contracts/internal/architecture_v2/schemas.py:337,347` and are wired in
      `action_handlers.py:215-228`, rate-matched like `LEND`/`BORROW`. `BATCH_UNHANDLED_ACTIONS` is DERIVED
      (`frozenset(InstructionActionV2) - BATCH_SETTLEMENT_ACTIONS - BATCH_NO_FILL_ACTIONS`), MEASURED now =
      exactly `{LP_BURN, LP_MINT}`, down from the original 5.

      **`LP_MINT`/`LP_BURN` genuinely remain — no `StrategyInstructionEnvelope` subclass exists in UAC for
      either.** This tranche does not own `unified-api-contracts`, so it cannot add the schema itself. The
      `[FROM-T4]` inbound request on
      `/plans/active/code_readiness_t1_contracts_library_externalapi_2026_08_19.md` now carries the full shape
      spec (grounded in real connector signatures — Uniswap's NFT-position `mint_position`/`burn_position` vs.
      Orca/Raydium's pool-address `add_liquidity`/`remove_liquidity`), not just a bare ask — once T1 lands the 2
      subclasses, T4's side is mechanical (2 more `isinstance` branches, same pattern as the 3 fixes above).
      `BLOCKED-` on that request until then.

      **3/5 CLOSED 2026-08-20 — `execution-service@59627fa2d2`.** T1 landed `WithdrawInstruction`/
      `RepayInstruction` (`unified-api-contracts@f5fc118ae1`) same day, exactly as the request predicted —
      `resolve_settlement` now handles both as rate-matched inverses of `LEND`/`BORROW` (protocol/asset/
      target_supplied_amount and target_debt_amount respectively). `BATCH_UNHANDLED_ACTIONS` measured shrinking
      to exactly `{LP_BURN, LP_MINT}`. Fixed a test that had pinned the OLD gap as expected behavior
      (`test_lending_venue_is_only_wired_on_batch` asserted `AAVE-V3-ETHEREUM.batch == "wired"` — now genuinely
      `"deployed"`, rewritten to assert the fixed reality rather than the historical gap). 4 new tests total.
      **Still open, but no longer a blank design question — shape specified 2026-08-20** on
      `/plans/active/code_readiness_t1_contracts_library_externalapi_2026_08_19.md`'s `[FROM-T4]` thread,
      grounded in both real connector families (`UniswapConnector.mint_position()`/`burn_position()` — NFT
      position id + sqrt-price bounds — vs. Orca/Raydium's `add_liquidity()`/`remove_liquidity()` — pool address +
      raw ticks, no NFT). `BLOCKED-ON:` T1 landing `LpMintInstruction`/`LpBurnInstruction`; once shipped, T4's
      side is the same mechanical 2-branch `isinstance` addition as `CONVERT_DUST`/`WITHDRAW`/`REPAY` — 5/5.

### W12 — reconciliation

- [x] ✅ [BACKEND] P0. Build pause-before-manual-entry — **batch-live-reconciliation-service@1e210addb1**. It is an
      INTERLOCK, not a note: `POST /t1-recon/book-correction` returns 409 until an active pause exists on the
      break's `(venue, instrument_id)`, because a correction booked while automation still trades that position
      can double-apply. Lookup is case-insensitive — the break's casing comes from recon output, the operator
      types their own. MEASURED: 409 without a pause, 200 after pausing, 409 again once the pause is revoked.
- [x] ✅ [BACKEND] P0. Build virtual and persistent delta exclusion — **batch-live-reconciliation-service@1e210addb1**.
      The two differ in LIFETIME, and conflating them is how a one-off suppression silently becomes permanent.
      VIRTUAL is scoped to one `run_date` and held in process; PERSISTENT applies until revoked and is written to
      `t1-recon/recon/exclusions.json`, so it survives a restart — that asymmetry IS the feature. A VIRTUAL
      exclusion with no `run_date` is REJECTED, never quietly promoted. MEASURED: virtual suppresses only its own
      run date and does not survive a new store; persistent survives one and ignores a supplied `run_date`; a
      corrupt exclusions object fails OPEN (breaks re-raised) rather than suppressing on half-parsed state.
- [x] ✅ [BACKEND] P0. Build the soft-delete audit trail — **batch-live-reconciliation-service@1e210addb1**. Nothing
      is removed: revoking a pause or exclusion stamps `revoked_at`/`revoked_by`/`revoke_reason` and keeps the
      record, and `all_pauses()`/`all_exclusions()` return active and revoked alike — an FCA-relevant surface has
      to answer "who suppressed this break, and who un-suppressed it" after the fact. Revoking a PERSISTENT
      exclusion rewrites the GCS object with the record RETAINED. `/breaks` hides actively-excluded breaks;
      `include_excluded=true` shows them as `status=excluded` so suppression is auditable. MEASURED: after revoke
      the break is re-raised, the record persists with `active=false`, and `active_only=true` filters it out.
- [x] ✅ [BACKEND] P1. **CLOSED 2026-08-20 — manual trade entry now covers every venue type.** Epic
      definition-of-done item, manual execution mode first-class alongside automated per the 2026-08-19 addition
      to W1. Root-caused: `ManualOperationHandler.execute()` unconditionally called `get_or_create_orchestrator()`
      — CLOB-shaped, cannot represent a `DeFiAdapter` or sports adapter. Confirmed by reading
      `_execute_instructions`'s automated path that DeFi instructions there are dispatched straight to
      `DeFiAdapter.execute_instruction()`, never through an `ExecutionOrchestrator`. **DeFi —
      `execution-service@8cd47073b5`**: added `get_defi_adapter_singleton()` + a process-wide-singleton
      `get_or_create_defi_adapter()` cache; `execute()` branches on `DEFI_VENUES` before the CLOB fallback. 6 new
      tests. **Sports — `execution-service@053a1ee136`**: `_execute_sports_instruction`/`_execute_sports_bet`
      previously returned `None` unconditionally despite building a real result dict internally and discarding
      it (the automated path never needed the return value) — now both return the dict, automated caller
      unaffected (Python allows discarding a return value). Added the analogous
      `get_sports_adapter_singleton()`/`execute_sports_instruction()` wrappers +
      `get_or_create_sports_adapter()` cache; `execute()` branches on `SPORTS_VENUES` between the DeFi and CLOB
      branches. 8 new tests, including regression guards that CLOB/DeFi venues each still route correctly
      unaffected by the other branches. Manual trade entry is now genuinely first-class across CLOB/CeFi/TradFi,
      DeFi, and sports.

### W14, W15, W17 — fidelity, security, cost

- [x] ✅ [BACKEND] P0. **Implement per-venue error codes and classify through UAC `classify_venue_error()` — CLOSED,
      full sweep done 2026-08-20.** Shard-level failure isolation, no `raise` in per-shard loops. SSOT:
      `/codex/04-architecture/shard-level-failure-isolation.md`. **`classify_venue_error` is already widely adopted**
      (20 files: sports adapters, DeFi protocols, trade_execution adapters, the engine orchestrator/router) — this
      was NOT unbuilt from scratch, contrary to the todo's original framing. Audited real per-venue loops for the
      actual "no raise in per-shard loop" invariant instead (`grep -rn "for venue in"`, 21 non-test sites) and
      found + fixed one genuine, safety-relevant violation: `OrderRecoveryEngine.recover_venue()`
      (`execution_service/engine/startup/order_recovery.py`) only wrapped `fetch_open_orders()` in a try/except —
      `_reconcile_exchange_orphans`'s `cancel_order()`/`confirm_cancel()` calls were NOT wrapped, so any venue-
      adapter exception there propagated uncaught through `run()`'s `for venue in venues:` loop, silently
      abandoning recovery for every venue queued after the failing one on startup. Fixed — `execution-service@ff0b43b5d3`
      — extracted `_reconcile_venue_orders()` (kept `recover_venue` under the 50-line cap), wraps the whole
      reconciliation body, records via the file's own existing `CanonicalNetworkError` + `cb.record_failure()`
      pattern (not `classify_venue_error` — that's a vendor-error-CODE classifier, doesn't fit an arbitrary Python
      exception; kept consistent with this file's own established convention instead). New regression test proves
      one venue's failure does not abort the second venue in `run()`.
      **The remaining ~20 sites, individually audited 2026-08-20, MEASURED zero further violations**: most are pure
      computation over already-fetched data (`sor_twap.py`'s local `set_liquidity` cache write,
      `algo_library/solver_auction.py`'s weighted-split math, `sports_router.py`'s in-memory scoring,
      `engine/live/router.py`'s candidate filtering) — no per-venue I/O, so no exception a venue outage could throw.
      Several already correctly wrap the risky call: `algo_library/sor_dex.py:165`'s `get_all_quotes()` (catches
      ValueError/KeyError/TypeError plus TimeoutError/ConnectionError separately),
      `_venue_book_types.py:153` (ValueError/KeyError/AttributeError), `registry.py`'s `reconnect_all()` (each
      `reconnect()` call is internally wrapped for ConnectionError/TimeoutError/OSError/ValueError, the only
      unguarded `KeyError` path is unreachable since it only iterates already-registered keys),
      `cli/handlers/live_execution_handler.py:263`'s orchestrator-build loop (`_create_orchestrator_for_venue`
      already catches ValueError/TypeError/KeyError/AttributeError/RuntimeError internally and returns `None`
      rather than propagating). **One near-miss, deliberately NOT changed**: `algorithms/sor.py:177`'s
      `get_all_quotes()` catches a narrower exception set than its `algo_library/sor_dex.py` sibling (no
      TimeoutError/ConnectionError) — but its `_get_venue_quote()` is pure-simulation today (its own comment says
      "In production, would query actual pool state"), so those exceptions cannot actually fire; adding a catch
      clause for an I/O error a function never performs would be defensive code for a scenario that can't happen.
      Flagged here rather than silently dropped — worth revisiting if/when that function is wired to real venue
      I/O. `execution_service/algorithms/` is confirmed live (imported by `instruction_convert.py`,
      `handler_registry.py`, `config_validator.py` — not dead code), so this is a real, if currently inert, gap.
      Preflight's `_check_venue_api_keys` (`engine/preflight.py:77`) and the dependency-checker's
      `for venue in venues` (`utils/dependency_checker.py:683`) are deliberately out of scope — both are startup
      preflight/validation, where propagating an exception to halt startup is the correct behaviour, not a
      per-shard-isolation violation of the live-trading-loop kind this SSOT targets.
- [x] ✅ [BACKEND] P0. **Spun out into a dedicated AO plan, 2026-08-20** —
      `/plans/active/w14_execution_service_exchange_version_pinning_and_cassette_drift_2026_08_20.md`, operator
      directly authorized this specific spin-out (asked mid-session via AskUserQuestion, "AO plan" selected — no
      prior blanket ruling covered W14 the way W15/W22 had one). Scoped via real measurement: 8 cassette
      directories exist, `ccxt` is already pinned via the standard pyproject/uv.lock range but native (non-ccxt)
      REST adapters carry zero explicit per-venue API-version markers. Sized into 4 phases (design what "version"
      means per transport; build the pinning; build drift detection; triage + close-out), deliberately front-
      loading the 3 real design questions as P0s since everything else depends on their outcome, plus the
      mandatory gated finalize plan. This todo closes here; track further progress there, not in this doc.
- [x] ✅ [BACKEND] P0. **Spun out into a dedicated AO plan, 2026-08-20** —
      `/plans/active/w15_execution_service_venue_adaptor_security_audit_2026_08_20.md`, per the 2026-08-19
      operator ruling. Sized into 11 phases against a real, enumerated ~85-file adapter inventory (bridge/
      cross-chain first as highest-stakes, then DeFi by primitive, then CeFi/TradFi by transport, then sports),
      each applying a fixed 7-point checklist (credential handling / signing correctness / input validation /
      slippage-deadline bounds / approval scope / idempotency / honest error handling), plus a triage phase and
      the mandatory gated finalize plan. This todo closes here; track further progress there, not in this doc.
- [x] ✅ [BACKEND] P0. **Build the full fees and gas breakdown (W17) — DONE, `execution-service@760b41a251`.**
      T1 shipped the contracts-side half same day (`clearing_fee_bps`/`broker_fee_bps`/`other_fee_bps` added to
      `ExecutionCostEstimate`, `unified-api-contracts`); this session wired the execution-service half —
      `ExecutionCostEstimator.estimate_cost()` now explicitly computes and returns all 3 new fields (honestly 0 +
      a note for TradFi pending a real sourced fee schedule, never an invented bps figure) alongside a real fix:
      every TradFi venue (CME/CBOE/NASDAQ/NYSE/ICE/FX) was silently misclassified as CEFI before this, applying
      wrong fee/spread assumptions. 12 new/updated tests.
- [ ] [BACKEND] P1. **7/13 CLOSED 2026-08-20 — `unified-trading-pm@f582a4e724`.** Complete the execution policy
      and fill-model gaps — collapse the two independent benchmark implementations into one sent value, stop
      no-op'ing the lending path, de-duplicate the algo vocabulary across two modules. Evidence:
      `/plans/active/execution_service_policy_and_fill_model_gaps_2026_08_19.md` (own doc tracks full detail, not
      duplicated here). Most closed todos turned out to be already-shipped by commits pre-dating the doc itself
      (`ea0bbf807`, `b8989ae55`, `c2053c47b`, `bbf99a61d` — all 2026-06-19/08-14) — the doc had drifted stale
      before this tranche ever touched it. 6 remain open with dated, measured reasons (not guesses): a mechanism
      built + unit-tested but zero production callers (sub-candle rung wiring, participation-cap routing), a real
      design gap the shipped code doesn't resolve (`SubCandleBar` has no aggressor-side field for PB.8's
      correction), 1 todo outside this dispatch's granted repo access (`e2e-testing`), 1 needing a real manifest
      query this dispatch's tooling doesn't have. 1 new todo added tracking `HandlerRegistry.select_algorithm`
      having zero production callers despite a real, tested resolver chain beneath it.
- [ ] [BACKEND] P2. Complete per-venue scope-key provisioning. Evidence:
      `/plans/active/issues/per_venue_scope_key_provisioning_incomplete_2026_07_23.md`. **CHECKED 2026-08-20, still
      genuinely open, no new action found**: that doc's own 3-week audit trail (na-eligibility-audit
      2026-07-30 through 2026-08-20) already exhaustively covers it — 2 of 3 remaining todos are `[HUMAN]`-only
      (the operator's own exchange-login credential creation for Bybit / Upbit-Kraken-Bitfinex-Bitget), the third
      (`[BACKEND] P2` OKX/Hyperliquid scope-separation) is operator-approved to build but every audit since
      2026-08-08 correctly flags it as still unbounded ("scope the exact per-venue mechanism... before
      estimating") — a genuine multi-hour design+build task, not attempted this session for the same reason as
      the file-split above: better done as its own focused pass than rushed here.
- [x] ✅ [BACKEND] P3. **VERIFIED 2026-08-20 — already correctly done, nothing further to build.** Checked
      `test_tenderly_fork_full_cycle` directly: still real (not deleted), still `@pytest.mark.skip(reason=
      "BLOCKED-CREDENTIALS: Tenderly fork + Aave V3 RPC — issues/exec_tenderly_2026_08_15.md")` — correctly
      tracked, not descoped. That issue doc's sole todo is `[OPERATOR]`-tagged (provision a real Tenderly fork RPC
      + API key) — not agent-self-serviceable per
      `/codex/02-data/external-data-always-available-rule.md`'s BLOCKED-CREDENTIALS pattern, which this already
      correctly follows.

### Settlement, reporting and Elysium

- [x] ✅ [BACKEND] P1. **Resolved — stale reference, not T4/execution-service scope.** The cited 88-todo doc
      (`/plans/active/elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md`) does not exist —
      confirmed nowhere in `plans/active/`, `plans/archive/`, or git history under that path. It was split/renamed
      before this plan's own 2026-08-19 authoring date, so the reference was stale from the start, not something
      that rotted this session. "Elysium" here is a CLIENT name (unrelated to the fleet-wide-banned data vendor of
      the same name). Successor docs traced — `client_artefact_remediation_elysium_2026_08_18.md` (0 open/25
      closed, DONE), `..._finalize_2026_08_18.md` (1 open, a housekeeping archive-todo, `repos: [unified-trading-pm]`),
      `elysium_carveout_stubbed_strategy_service_2026_08_12.md` (`status: draft`, not ingested, T3's/T1's repos) —
      none are execution-service-scoped or T4-allocated. Full detail: this plan's Progress Log, 2026-08-20.
- [ ] [BACKEND] P1. Wire transfer netting and custody routing end to end in production — the artefacts mark these
      target-state, not wired.

      **Scoped 2026-08-20, not built — two independent blockers, not one.** Grepped execution-service repo-wide
      for any "netting" concept relevant to fund transfers: zero hits — every existing "netting" reference
      (`config/grid_builder.py` etc.) is NautilusTrader's `oms_type: "NETTING"` position-netting-vs-hedging
      setting, an unrelated concept. **Netting** (deciding which pending transfer intents can be combined before
      any custody call happens) is explicitly documented as STRATEGY-service-owned in the related
      `execution_service_policy_and_fill_model_gaps_2026_08_19.md`'s Progress Log ("§ A/C/D/H strategy-owned:
      ... transfer-emit netting") — so the "emit" decision is out of this repo's scope entirely, not merely
      unbuilt here. **Custody routing** is genuinely execution-service's to build, but is the SAME blocker the
      `[FROM-T1]` Ceffu-integration todo above already tracks: `transfer_coordinator.py` has a real
      `TransferHandler` protocol + one concrete `_SubaccountMoveHandler` (Binance/OKX only), but building a
      real Ceffu/Copper custody-routing handler needs the actual Ceffu API spec, which does not exist in this
      workspace (not a credentials gap — a documentation gap). Real next step once unblocked: build the custody
      routing half against whichever real transfer-provider spec lands first, wire it into
      `TransferCoordinator.register_handler()`; the netting half needs a strategy-service-side design session
      this tranche cannot self-serve (cross-repo, cross-team boundary).
- [x] ✅ [BACKEND] P2. **Closed — all 4 sub-items resolved.** Close the batch-live-reconciliation-service, fund-administration-service, greeks-service and
      client-reporting-api items in this tranche's allocation. **fund-administration-service: zero docs allocated**
      (confirmed via `plans/audit/results/code_readiness_allocation_2026_08_19.json`, key
      `T4-execution-settlement` — no `primary_repo: fund-administration-service` entries exist), nothing to close
      there. **greeks-service: CLOSED** — sub-agent dispatch archived
      `plans/active/issues/promote_pr_non_supersession_after_greeks_service_fix_2026_08_18.md`
      (`unified-trading-pm@291da5e837`) after live re-verification found zero recurrence of the promote-PR bug
      across the last 20 promote PRs. **client-reporting-api: verified NOT actionable, correctly deferred** — both
      allocated docs (`asset_class_to_asset_group_rename_2026_07_21.md`,
      `stash_pile_workspace_cleanup_2026_06_03.md`) are gated on cross-repo (UAC rename must land first) or
      host-wide (`--apply` sweep spans every repo on the host, not just this one) work outside a
      client-reporting-api-scoped session; sub-agent re-confirmed both standing operator rulings still hold
      against current code (`unified-trading-pm@e1e9deda70`), no code changed. **batch-live-reconciliation-service:
      CLOSED, sub-agent dispatch, all 3 docs worked to completion and independently ancestry-verified.**
      `pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md` (P0): shipped the M6 capability-driven
      startup-continuity gate (`engine/startup_continuity_gate.py`, UAC `could_exist`-driven 3-way policy) and the
      T+1 batch/live TTL eligibility decision layer (`engine/live_ttl.py`, read-only — never mutates the manifest
      by design) — `batch-live-reconciliation-service@0aaa663b59`, 315 tests green. Both checkboxes left
      deliberately open (PARTIAL): each ships the BLRS-side decision primitive only, and each has a real remaining
      piece outside this repo's authority — strategy-service/MTDS consumer wiring for M6, and the UTL
      manifest-write helper (doesn't exist yet) to actually act on a TTL-eligible cell for the TTL layer. Also
      closed the doc's #7 coherence audit (12 per-AG docs swept, 0 stale-claim hits). **This doc sits at the
      1000-line HARD cap** — any future edit to it must be a pure small append or single-checkbox flip, not a
      combined edit (measured: forced 3 separate micro-commits this session). `citadel_paper_batch_live_reconciliation_2026_06_19.md`
      (P1): all 3 open todos reviewed — the live→paper reconcile item re-confirmed correctly `BLOCKED-OPERATOR-DECISION`
      (wallet/custody hard-stop, unchanged); the two ML-retrain sub-items are strategy-service/e2e-testing scope,
      correctly left untouched (out of this repo's allocation). `issues/cve_affected_pinned_deps_remediation_2026_06_18.md`
      (P2): fresh `pip-audit` against this repo's own venv — zero known vulnerabilities; checkbox intentionally
      stays open per its own standing scope ruling (unbounded, not session-closeable). Evidence:
      `unified-trading-pm@2d8958bbf2`, `@3ed1d398dc`, `@0858d3e90d`, `@21aba2b0b6` (all ancestor-verified against
      origin independently by the parent session, not just self-reported).

### Close-out

- [ ] [AGENT] P1. Work the non-spine tail of this tranche's allocation to zero open todos or an explicit
      `BLOCKED-*` tag on every remainder.
- [x] ✅ [AGENT] P2. **Split, shipped — `execution-service@1e243e975e`.** `manual_instruction_api.py`
      (900 -> 162 lines, split into `manual_instruction_submit.py`/`cancel_amend.py`/`record.py`/`pending.py`,
      sharing one `router`) and `live_execution_handler.py` (900 -> 447 lines, split into a pure-constants
      `live_execution_venues.py` plus three mixins — `_CredentialsMixin`/`_DefiAdapterMixin`/
      `_SportsExecutionMixin` — `LiveExecutionHandler` inherits, required because production code in
      `v2/account_orchestrator.py`/`engine/transfers/wiring.py` calls
      `LiveExecutionHandler._load_venue_trade_credentials(...)` as an explicit class-level static method, so
      standalone functions wouldn't have preserved that call surface). Full test suite green (8806 passed).
      **The dispatched sub-agent's own investigation superseded this todo's pre-analysis in two real ways**:
      (1) the "12 test files patch `persist_audit_log`/`log_event`/etc. via `patch("...")` string literals" claim
      was only PARTLY right — several of those files actually use `patch.object(manual_instruction_api,
      "_orchestrator", ...)` / `monkeypatch.setattr` instead, a wider patch surface than a literal-string grep
      would find, caught only by reading the actual test bodies; (2) trimming `manual_instruction_api.py` broke
      `test_pretrade_wiring.py::test_kill_switch_blocks_all_submissions` (imports `ManualInstructionRequest`
      directly from that module) — fixed by re-exporting the original schema surface, a real regression the full
      test-suite run caught before shipping, not assumed away. Also removed a backward-compat re-export shim this
      tranche itself introduced mid-split (`DEFI_VENUES`/`SPORTS_EXCHANGE_VENUES`/`SPORTS_VENUES` etc. kept alive
      in `live_execution_handler.py` "for compat") — the repo's own `quality-gates.sh` "no-backward-compat-shims"
      check caught it; fixed by migrating every real consumer (`test_sports_execution.py`, `test_routing_matrix.py`,
      `test_live_execution_handler.py`) to import from `live_execution_venues`, the constants' actual owner,
      instead of re-exporting. **Process note for future dispatches**: this sub-agent's background quickmerge kept
      running after multiple "completed" task notifications had already fired, causing a real, if harmless,
      duplicate-quickmerge race against this session's own redundant ship attempt for the same split — no data
      was lost (working tree already matched HEAD by the time the second attempt resolved), but a `run_in_background`
      agent's own nested backgrounded shell commands can outlive what its "completed" status implies; verify via
      `git log`/`ps`, not the notification text alone, before assuming a dispatched agent is truly done.
- [x] ✅ [AGENT] P0. **Post-phase codex audit across `/codex/04-architecture/` for every contract changed — DONE
      2026-08-20.** Every contract this tranche touched, checked: `order-state-machine.md` (fixed a prior session,
      9-state warning + PARTIALLY_FILLED ruling); `account-instructions.md` (fixed this session —
      `unified-trading-pm@0db97a5b47` — annotated the Authorization/Audit sections as design-target-not-shipped);
      `strategy-execution-protocol.md`/`exposure-reduction-unification.md` (checked, both only reference the
      `AccountActionV2` enum shape in a table, which is accurate, no fix needed). Grepped `codex/` for
      `execution_instruction`/`instruction-path`/`864.*row` to check whether the readiness-dump fix
      (`unified-trading-pm@8d47cf3393`) needed a codex update too — no codex doc describes that mechanism's
      internals (it lives in the skill's own `SKILL.md`, not `codex/`), so nothing there to fix.
- [ ] [BACKEND] P2. **Build real per-action, role-based authorization + structured audit for AccountInstruction —
      surfaced by the post-phase codex audit 2026-08-20.** `/codex/04-architecture/account-instructions.md`'s
      Authorization table (Ops lead / Strategy owner + ops / Compliance + 2-of-N / firm officer / etc., one row
      per `AccountActionV2` member) and Audit section (per-instruction post-state snapshot, permanent structured
      retention) are the DESIGN TARGET, now annotated as such in that doc. The REAL shipped
      `AccountInstructionOrchestrator.dispatch()` (`execution_service/v2/account_orchestrator.py`) checks only
      that `authorization_id` is a non-empty string — no role lookup, no per-action requirement — and audit is
      two `log_event` calls with no post-state snapshot. Not started this session (design-heavy: needs a role
      registry + an authorization-record lookup neither this tranche nor UAC currently define). SSOT:
      `/codex/04-architecture/account-instructions.md` §Authorization, §Audit.
- [x] ✅ [AGENT] P0. Confirm every execution marker in the artefacts now reads live, or is one of the five allowed
      pending states. **Structural blocker fixed 2026-08-20, this todo's own remaining scope re-measured**: the
      readiness-dump's `execution_instruction` leg was hardcoded venue-independent-`unverified` for all 864 rows
      (the real per-venue check existed, `execution-service@b70d2edb16`, but nothing called it) — fixed,
      `unified-trading-pm@8d47cf3393`, independently verified live: a `defi` asset-group run went from a blanket
      unverified to a real `{unverified: 20, ready: 133, not_ready: 387}` distribution across 540 rows. **What's
      NOT done**: actually re-reading the 4 HTML artefacts' W-tagged markers against this now-real state and
      updating any stale ones — no automated marker-writer exists anywhere in this workspace (checked: the
      readiness-dump skill's own `SKILL.md` only describes deriving state, never writing it back into HTML), and
      the 4 files are 33,976 lines combined, too large to safely hand-verify in the tail of this session. Dispatched
      to a sub-agent (see this plan's Progress Log for the dispatch + its findings) rather than rushed or left
      silently unattempted.

      **DONE 2026-08-20 — `unified-trading-pm@78508ce4e7`.** Sub-agent grepped all 4 files' `<style>` blocks (only
      three real status classes exist anywhere: `st-live`/`st-part`/`st-plan`), cross-referenced every `owner: W*`
      tag and execution/instruction keyword hit against this session's 6 real fixes, and independently re-verified
      two claims against live source. Verdict: **no `st-*` badge met the bar for a confident flip** — every
      candidate badge stays accurate, or the staleness lives in prose the task correctly scoped out of badge-flip
      edits. Two genuinely wrong PROSE claims found and fixed directly (not badges, so the sub-agent correctly
      flagged rather than auto-edited; I verified + fixed both): (1)
      `platform-external-api-walkthrough.html` said "TRADE only — the other 10 action types return HTTP 501" —
      QUOTE has been wired since `execution-service@dc4fad8de7`, corrected to "TRADE and QUOTE — the other 9"; (2)
      the same file's "execution-instruction leg is unverified on all 864 rows... that check does not exist
      anywhere in the fleet yet" — false since the fix immediately above; corrected to cite the real fix + the
      measured `defi`-asset-group sample, without inventing an un-measured full-864 number. A third finding —
      `strategy-service-walkthrough.html`'s "Emergency flatten" bullet likely understates what's shipped now that
      `test_account_instruction_api.py` exists — the sub-agent was NOT confident enough to edit it itself; tracked
      as its own new todo below rather than silently dropped.
- [x] ✅ [AGENT] P3. **Re-checked and fixed — `unified-trading-pm@359be094ab`.** The bullet's "re-points onto the
      manual instruction surface rather than a new endpoint" claim was itself wrong, not just stale — confirmed
      live via `execution_service/api/account_instruction_api.py:32` (`APIRouter(prefix="/account")`, a genuinely
      separate router, not `manual_router`). Rewrote to state what's actually shipped: `POST /account/instruction`
      is a dedicated endpoint driving `AccountInstructionOrchestrator`'s real per-venue CLOSE_ALL (reads live
      positions, submits offsetting market orders), proven by `tests/unit/test_account_instruction_api.py`, with
      the one genuinely still-open gap named honestly (DeFi/sports have no equivalent close-out primitive).

## Progress Log

> Append-only in spirit; CONDENSED 2026-08-20 (twice) to stay inside the 500-line soft cap. Per-item detail lives on
> the checkboxes above — this log keeps what a successor cannot reconstruct from them: shas, corrections, traps.

- 2026-08-19 — Plan authored from the 892-doc active corpus. No code work started.

### 2026-08-20 session

**Where to work.** `.tabs/5`, NOT `.tabs/7` (no `.venv`). Shared with another live session on other repos: scope
every commit by name, never `git add .`. **`.venv/bin/activate` does NOT persist across Bash tool calls** — each
call is a fresh shell; a bare `python` in a LATER call silently resolves to whatever's on default PATH, not the
sourced venv. Always invoke `.venv/bin/python -m <tool>` explicitly, every call, or a lint/test check silently
runs against the wrong interpreter (cost one full false-alarm diagnosis this session: an `AttributeError` that
looked like a real gate failure was actually a wrong-python artifact).

**Landed (each verified against origin, never by quickmerge's exit code):**

| sha | unit |
|---|---|
| `execution-service@b70d2edb16` | per-venue instruction-path check + DeFi route-table SSOT (the 864-row unblocker) |
| `execution-service@dc4fad8de7` | delta-proxy sensitivity triple + rebuilt QUOTE receipt point |
| `execution-service@9c79bfa0ef` | deployed service serves `/manual/*` (was a production 404) |
| `execution-service@0c0b6a1a40` | Pendle wired, LEND only |
| `execution-service@7202047877` | per-action `instruction_action_support` (T5's 2nd, action-level ask) |
| `execution-service@35f0bfb1b` | `OrderStatus.PENDING`/`.OPEN`→`.PENDING_NEW`/`.NEW` rename, UAC sites only |
| `execution-service@197e80116` | live-orchestrator protocol mismatch: real fix, not the diagnosed one — see below |
| `execution-service@96411b68c9` | real CLOSE_ALL: flattens every open position, CLOB/CeFi-scoped, 8 new tests — landing independently verified (empty `git diff --stat origin/live-defi-rollout`, clean tree, HEAD matches) |
| `execution-service@c0839616be` | `POST /account/instruction` route on both `app.py` and `main.py` in front of the CLOSE_ALL wiring above — 5 new HTTP tests; emergency close-all todo now CLOSED |
| `execution-service@6f664e80a0` | BATCH settlement gap 1/5 closed: `CONVERT_DUST` now handled by `resolve_settlement`, 2 new tests |
| `unified-trading-pm@0db97a5b47` | codex audit: `account-instructions.md`'s authorization table + audit section annotated as design-target-not-shipped (verified against the real `AccountInstructionOrchestrator.dispatch()`) |
| `unified-trading-pm@8d47cf3393` | readiness-dump `execution_instruction` leg now calls the real per-venue-per-mode check (`execution_service.readiness.instruction_path`, shipped `execution-service@b70d2edb16` but never wired in) instead of a hardcoded venue-independent unverified — new `_execution_instruction_path_probe.py`, `checks.py`/`derive_readiness.py` updated; independently re-verified live after landing |
| `unified-trading-pm@78508ce4e7` | artefact-marker sub-agent audit: fixed 2 factually-wrong prose claims in `platform-external-api-walkthrough.html` (QUOTE falsely listed as still-501; the 864-rows-unverified claim falsely said the check doesn't exist) |
| `execution-service@ff0b43b5d3` | shard-level failure isolation fix: `OrderRecoveryEngine.recover_venue()` no longer lets one venue's reconciliation exception abort recovery for every other venue on startup; new regression test |
| `execution-service@760b41a251` | W17 fee-breakdown contract wired (`clearing_fee_bps`/`broker_fee_bps`/`other_fee_bps`) + a real TradFi venue-classification bug fixed (was silently falling through to CEFI) |
| `unified-trading-pm@68c1d2cf82` | authored + dispatched `w22_strategy_execution_messaging_external_api_2026_08_20` and `w15_execution_service_venue_adaptor_security_audit_2026_08_20` as active AO plans, each with a mandatory gated finalize plan, per the 2026-08-19 operator ruling |
| `batch-live-reconciliation-service@0aaa663b59` | (sub-agent) M6 startup-continuity gate + T+1 batch/live TTL decision layer |
| `unified-trading-pm@291da5e837`, `@2d8958bbf2`, `@3ed1d398dc`, `@0858d3e90d`, `@21aba2b0b6`, `@5b40e5616c`, `@d71209b66d` | (sub-agents + parent) doc closures, archival, corrections — see plan body for what each covers |

**Traps worth more than the code — all measured, none anticipated:**

- **quickmerge exit 0 does NOT mean landed** — verify `git cat-file -e origin/<branch>:<path>` + empty
  `git diff --stat origin/<branch>`; capture the log to a FILE, never `| tail -N` only.
- **Editing OTHER files while a quickmerge for a subset is still gating contaminates that gate's full-suite run**
  with unrelated failures (quality-gates.sh tests the whole tree, not just the named diff). Fix: `git stash push`
  the unrelated WIP before launching a quickmerge, pop it back only after that one is verified landed. Hit this
  once (unit-1 vs. the in-progress OrderStatus rename); the fix held for every unit after.
- **`api/main.py` runs `app = create_app()` at IMPORT** — global mutation in the factory is an import-time side
  effect on the whole suite. A lifespan that only SETS still leaks; it must RESTORE on shutdown too.
- **TWO files sit at EXACTLY the 900-line cap**: `api/manual_instruction_api.py`,
  `cli/handlers/live_execution_handler.py`. Any addition to either must be net-zero on line count until split.
- **Run size + ruff + basedpyright locally BEFORE gating, after EVERY edit** — cheaper than a failed gate cycle.
  Method-size (50L cap) still bit twice more this session on genuinely new methods (not edits to existing ones) —
  a local `grep -n "def foo" file.py` line-span check catches it before the gate does.
  **Importing a `LiveExecutionHandler`-style class into a NEW module inside `execution_service/v2/` risks a package
  circular import**: anything importing `execution_service.v2.<anything>` runs `v2/__init__.py` first, which
  re-exports `AccountInstructionOrchestrator` — if that module imports something that itself imports
  `execution_service.v2.*`, the cycle is immediate ("partially initialized module"). Fix: import the
  cross-cutting dependency LAZILY, inside the function that needs it, not at module top level.

**Corrections to my own earlier claims — kept, not deleted, because each was wrong in an instructive way:**

- **Emergency close-all**: `AccountInstructionOrchestrator` has ZERO production callers — unreachable latent trap,
  not a live defect. Fix order: real CLOSE_ALL wiring first, route second, never the reverse.
- **`DEFI_VENUE_TO_CONNECTOR_CLASS`**: exists in UAC's *tests*, not source — I'd only grepped source.
- **OrderStatus rename blast radius (24 sites)**: 6 were never UAC's enum — `orders/oms.py` +
  `trade_execution/oms/persistent_oms.py` each define their OWN local 7-state `OrderStatus`, a different type.
  True UAC migration was 18/18 sites, not 24.
- **Live-orchestrator protocol mismatch — the ORIGINAL diagnosis's central risk claim was wrong.** It said
  `ExecutionOrchestrator.execute_instruction` genuinely submits the order to the venue THEN falls through to a
  `None` return (a "false-negative-on-success" — operator retries an already-filled order), and a real end-to-end
  test (`execution-service@d6e9ad19f9`) was built and shipped around that claim. Direct measurement shows this is
  false: the real class crashes on its FIRST line (`instruction.algorithm`) when given a `StrategyInstruction`
  (which has `.algo`, not `.algorithm`) — before market data, risk preflight, or any submission ever runs. The
  prior test never exercised the real class, only a hand-built fake that duck-typed around the actual crash. Real
  fix: `manual_request_to_instruction` (built for exactly this conversion, zero callers until now) is now wired
  into `ManualOperationHandler.execute()`; `execute_instruction` now genuinely returns `dict[str, object]` on both
  non-exceptional paths. Both affected tests corrected rather than left describing a defect that wasn't real.
- Four other P0s were already fixed before this plan was authored (OrderTracker CANCELLED/AMENDED, CCXT
  `withdraw()` stub, `CloudKmsCustodyProvider` chain_id fallback, funds isolation) — verified in code, not from
  issue-doc checkboxes. CeFi venue-dispatch P0 likewise pre-fixed 2026-08-17, flipped with evidence not redone.

**Sub-agent dispatch (2026-08-20, 3 agents, different repos, `SUB_AGENT_MANDATORY_RULES.md` pasted at spawn top):**
batch-live-reconciliation-service (3 docs, in progress) · client-reporting-api (2 docs, both confirmed correctly
NA-gated, no code needed) · greeks-service + ibkr-gateway-infra (1 doc closed+archived, 1 confirmed
`BLOCKED-OPERATOR-DECISION`, correctly unchanged).

**Scoped but deliberately NOT built this session** (real design work, not a single-session-scope fix): the
delta-proxy issue doc (30 open todos) and the policy/fill-model-gaps doc (13 open todos) are both dense with
`[DESIGN]`-tagged judgment calls the docs' own authors explicitly deferred — forcing these through would violate
the workspace's own AO-eligibility rule (determinable outcome only, never an open-ended design call taken
unilaterally). Left as-is for a future dedicated pass, not silently skipped.

## Deferred work after 2026-08-20

| item | state | why |
|---|---|---|
| Pendle `withdraw()` redemption | open P2 | widen `PENDLE_OPERATIONS` only in the SAME change that implements it |
| Pendle SIT cascade entry | inbound on T1 | needs UAC test-dict entry + baseline removal together |
| PARTIALLY_FILLED→CANCELLED/EXPIRED code | inbound on T1 | codex SSOT amended; one-line `ORDER_STATUS_TRANSITIONS` widen is T1's to land |
| Delta-proxy position + credit legs | `BLOCKED-OPERATOR` | T1's superseded-shape ruling (Q12-Q16) |
| Delta-proxy doc (30 todos) + policy/fill-model-gaps doc (13 todos) | open, design-heavy | genuinely open-ended judgment calls, not single-session scope |
| Three-way OrderStatus vocabulary fragmentation | open P0 (W11) | UAC canonical / `oms.py` local / `tracker.py` bare-strings — real cross-file reconciliation, not mechanical |
| BATCH settlement gap | open P1, 1/5 done | `CONVERT_DUST` closed `execution-service@6f664e80a0`; `LP_BURN, LP_MINT, REPAY, WITHDRAW` `BLOCKED-` on new UAC schema classes, `[FROM-T4]` filed on T1's plan |
| `api/app.py` vs `api/main.py` | open P0, operator | app.py holds startup wiring the container never runs |
| Split the two at-cap files | open | blocks any further addition to either |
| W22 strategy→execution messaging | untouched | no `EventTransport` subscriber in execution-service |
| W14/W15/W17 settlement tail | untouched | not reached this session |
| fund-administration-service, trading-agent-service | N/A | zero docs allocated to T4 for either (confirmed via allocation JSON) — nothing to close |

- **context-scout 2026-08-20**: refreshed context_scope (6 entries) — swapped the generic QG codex doc for `execution-service/`, the dominant repo by far for this tranche's remaining work.
