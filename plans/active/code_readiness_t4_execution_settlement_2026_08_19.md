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

- [ ] [FROM-T5] P0. **Expose a real per-venue instruction-path check in `execution-service`** — this is the leg the
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

> **T1 unblock notice 2026-08-20** — UAC `OrderStatus` is now the full 9-state machine the codex SSOT describes.
> `FAIL_OUTBOUND` and `RECONCILED` exist, and so do `ORDER_STATUS_TRANSITIONS`, `TERMINAL_ORDER_STATUSES`,
> `is_terminal_order_status()` and `is_legal_order_transition()`, all exported from the top-level
> `unified_api_contracts` facade. You are unblocked on this edge; the two todos below are the follow-through.

- [ ] [FROM-T1] P1. Migrate execution-service's `OrderStatus.PENDING` / `OrderStatus.OPEN` call sites to the
      renamed `OrderStatus.PENDING_NEW` / `OrderStatus.NEW`, then tell T1 to DELETE the two transitional aliases.
      **Nothing is broken right now** — T1 landed the rename as enum ALIASES (`OrderStatus.PENDING is
      OrderStatus.PENDING_NEW` is True, `.value` byte-identical), precisely so this is not a stop-the-world edit.
      Blast radius MEASURED at hand-off: **24 `OrderStatus.PENDING`/`.OPEN` call sites in execution-service** (plus
      1 in unified-trading-system-ui, which T1 owns and will handle). Fleet-wide there is NO `.name`-based,
      `OrderStatus[...]`, `len(OrderStatus)` or iteration coupling, so this is a mechanical rename with no
      semantic edge cases. The aliases are a deliberate, tracked exception to the no-shims rule: the
      entity-rename SSOT wants consumers migrated in the SAME change, and T1 is forbidden from editing your repo.
      Evidence: `/plans/active/issues/order_state_machine_ssot_vs_uac_orderstatus_2026_07_31.md`.
- [ ] [FROM-T1] P1. Write `execution-service/tests/unit/orders/test_state_machine.py` — the codex doc's own
      declared `verifier:`, which has never existed in the repo's history and is why the 9-state-vs-7-state
      divergence went unnoticed from 2026-05-12 to 2026-07-31. T1 already pins the ENUM against the codex table
      (`unified-api-contracts/tests/unit/test_order_state_machine.py`, 9 tests); what is missing is the
      SERVICE-side assertion that execution-service's own emitted transitions obey `ORDER_STATUS_TRANSITIONS`.
- [ ] [FROM-T1] P2. Decide whether `PARTIALLY_FILLED -> CANCELLED / EXPIRED` is a legal transition. T1 transcribed
      `ORDER_STATUS_TRANSITIONS` edge-for-edge from the codex diagram, which draws exactly ONE edge out of
      `PARTIALLY_FILLED` (full fill) — deliberately NOT widened on intuition, because a too-permissive machine
      silently accepts an illegal transition whereas a too-strict one fails loudly. Real venues do cancel
      partially-filled orders, so this likely needs the codex diagram amended first (the doc is the SSOT; the UAC
      map is its projection). You own the venue behaviour evidence, so this is your call to make and T1's to land.

## Todos

### W22 — strategy to execution messaging and the external instruction API

- [ ] [BACKEND] P0. Build the strategy→execution messaging path end to end. Confirmed unbuilt by a 2026-08-19
      workspace-wide search — the only live path is manual. Publish/read via the UTL `EventTransport` facade
      (`InMemoryTransport` for paper/colocated, Pub/Sub for live) so `paper(W) == batch-rerun(W)` holds at epsilon
      zero. SSOT: `/codex/02-data/live-data-persistence-and-event-log.md`.
- [x] ✅ [BACKEND] P0. **Expose a real per-venue execution-instruction-path check** — **execution-service@b70d2edb16**
      (landing verified independently of quickmerge's exit code: all six new files resolve under
      `git cat-file -e origin/live-defi-rollout:<path>`, and `git diff --stat origin/live-defi-rollout` is empty for
      the two modified files). `execution_service/readiness/instruction_path.py` exposes
      `instruction_path_availability(venue)`; `python -m execution_service.readiness` is the cross-venv probe.
      T5 has the frozen contract under their `## Inbound requests` (`unified-trading-pm@34999f0adf`), posted before
      the code landed so they were never idle-waiting. Measured verdicts are in the Progress Log.
- [ ] [BACKEND] P0. Build the external instruction API surface, coordinating the contract with T1.
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
      tranche: T1 recorded a superseded-shape ruling (Q12-Q16) and retagged `reference_position` / `credit` on
      `StrategyInstructionEnvelope` as `BLOCKED-OPERATOR` when landing the sensitivity triple
      (`unified-trading-pm@3353254d7a`). Execution-side work resumes the moment that shape is decided; the price
      leg above is independent of it and is already shipped. Evidence: same issue doc, plus T1's plan.

### W11 — order lifecycle and execution state

- [ ] [BACKEND] P0. Fix CeFi live venue-string dispatch in the order-adapter factory, broken for 9 of 12 major
      venues — same legacy bare-token table defect as strategy-service's. Coordinate the canonical form with T3.
- [x] ✅ [BACKEND] P0. Add CANCELLED and AMENDED to `OrderTracker` — **ALREADY SHIPPED; this plan's todo was
      stale at authoring.** MEASURED 2026-08-20 in code, not from the issue's checkboxes:
      `execution_service/orders/tracker.py:51` `mark_cancelled()` sets status `"CANCELLED"`, `:61`
      `mark_amended()` sets `"AMENDED"`, and `:117` `is_instruction_complete()` treats
      `terminal_statuses = {"FILLED", "CANCELLED"}` — so a cancel-only instruction DOES flip complete. Both are
      called from the live surface (`api/manual_instruction_api.py:473` `/cancel`, `:551` `/amend`). The source
      issue's remaining open item is a P3 (`instruction_to_order_ids` staleness), not this P0. Evidence:
      `/plans/active/issues/execution_order_tracker_missing_cancelled_amended_status_2026_08_17.md`.
- [ ] [BACKEND] P0. Implement the full 9-state order lifecycle once T1 lands the `OrderState` contract.
- [ ] [BACKEND] P0. Fix the broken emergency close-all path — **CONFIRMED 2026-08-20, and worse than this todo
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
- [ ] [BACKEND] P0. Build state recovery so a restart, a partial fill or a reconciliation drift cannot leave the two
      sides disagreeing. The artefacts describe this as guaranteed; it is not built.
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
- [ ] [BACKEND] P0. **Reconcile the deployed HTTP surface with what this plan and the artefacts claim.** MEASURED
      2026-08-20: `Dockerfile` CMD is `uvicorn execution_service.api.main:create_app --factory`, and
      `execution_service/api/main.py:43-44` registers ONLY the UTL health router and
      `external_instruction_api.router`. `manual_router` (`/instruction`, `/cancel`, `/amend`,
      `/instructions/{id}`, `/venues`, `/algos`, `/pending`) is registered on `api/app.py:127`, which the container
      never serves — `api/app.py` is imported only by CLI handlers and `evidence_router`. So on the DEPLOYED
      service the single HTTP instruction path is `POST /external/instructions`, which 501s every action except
      TRADE. **This contradicts this plan's own framing that "the only live instruction path today is manual".**
      NOT YET MEASURED, and required before deciding the fix: how DART's manual-trade surface actually reaches
      execution-service (a second deployment target, an in-process CLI path, or genuinely unreachable). Resolve
      that first, then either register `manual_router` on `main.py` or record why it is deliberately CLI-only.
- [ ] [BACKEND] P1. Verify the production live orchestrator actually satisfies the `LiveOrchestrator` protocol it is
      cast to — untested end to end, and the prior pass spot-checked location only. Evidence:
      `/plans/active/issues/execution_service_live_orchestrator_protocol_mismatch_untested_2026_08_16.md`.

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
- [ ] [BACKEND] P0. Reach-test every connector module. Marinade, Kamino and Jupiter connectors have zero production
      callers; the Pendle connector is built but never instantiated in `DeFiAdapter` and is absent from
      `DEFI_VENUE_TO_CONNECTOR_CLASS` / `DEFI_VENUE_TO_GATE_MARKER`. Wire them or delete them — no shims. Evidence:
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
      derives `batch=wired` instead of `deployed`. `REPAY`/`WITHDRAW` are rate-matched inverses of the shipped
      `BORROW`/`LEND` handlers and should be cheap; `LP_MINT`/`LP_BURN` need the DEFI_LP position shape. SSOT:
      `/codex/09-strategy/operational/paper-batch-live-reconciliation.md` §4.2.

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
- [ ] [BACKEND] P1. Implement manual trade entry on EVERY venue — epic definition-of-done item, and manual execution
      mode is first-class alongside automated per the 2026-08-19 addition to W1.

### W14, W15, W17 — fidelity, security, cost

- [ ] [BACKEND] P0. Implement per-venue error codes and classify through UAC `classify_venue_error()`. Shard-level
      failure isolation, no `raise` in per-shard loops. SSOT:
      `/codex/04-architecture/shard-level-failure-isolation.md`.
- [ ] [BACKEND] P0. Pin the exchange version per venue and re-run cassettes on drift, so a silent venue-version
      change cannot go undetected (W14). No owning plan existed at authoring time.
- [ ] [BACKEND] P0. Run a security audit of EVERY venue adaptor, especially DeFi, covering every on-chain write
      path (W15). P0 in the epic with no plan doing it systematically. Size this into phases and track them here.
- [ ] [BACKEND] P0. Build the full fees and gas breakdown — clearing, broker, exchange, gas, other — on the
      execution side (W17). Coordinate the strategy-side half with T3.
- [ ] [BACKEND] P1. Complete the execution policy and fill-model gaps — collapse the two independent benchmark
      implementations into one sent value, stop no-op'ing the lending path, de-duplicate the algo vocabulary across
      two modules. Evidence: `/plans/active/execution_service_policy_and_fill_model_gaps_2026_08_19.md`.
- [ ] [BACKEND] P2. Complete per-venue scope-key provisioning. Evidence:
      `/plans/active/issues/per_venue_scope_key_provisioning_incomplete_2026_07_23.md`.
- [ ] [BACKEND] P3. Keep the Tenderly-fork integration test as a real test and tag it credential-gated —
      do NOT delete the skip and do NOT descope. Evidence: `/plans/active/issues/exec_tenderly_2026_08_15.md`.

### Settlement, reporting and Elysium

- [ ] [BACKEND] P1. Work the Elysium October delivery and code-disclosure readiness plan (88 open todos) — the
      largest single doc in this tranche. Split into phases here as you go. Evidence:
      `/plans/active/elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md`.
- [ ] [BACKEND] P1. Wire transfer netting and custody routing end to end in production — the artefacts mark these
      target-state, not wired.
- [ ] [BACKEND] P2. Close the batch-live-reconciliation-service, fund-administration-service, greeks-service and
      client-reporting-api items in this tranche's allocation.

### Close-out

- [ ] [AGENT] P1. Work the non-spine tail of this tranche's allocation to zero open todos or an explicit
      `BLOCKED-*` tag on every remainder.
- [ ] [AGENT] P0. Post-phase codex audit across `/codex/04-architecture/` for every contract changed.
- [ ] [AGENT] P0. Confirm every execution marker in the artefacts now reads live, or is one of the five allowed
      pending states.

## Progress Log

> Append-only. One entry per shippable unit — what you changed, the `<repo>@<sha>`, and what you MEASURED (not what
> you assume). This log is the handoff document if this agent's context ends and a fresh one resumes the tranche.
> **Condensed 2026-08-20** to stay inside the 500-line soft cap; every durable fact below is preserved.

- 2026-08-19 — Plan authored. Allocation derived by `scripts/plan-hygiene/allocate_code_readiness_tranches.py`
  against the 892-doc active corpus. No code work started yet.

### 2026-08-20 session

**Where to work.** Use `.tabs/5`, NOT `.tabs/7`: tab 7 has no `execution-service/.venv`, so its quality gate
cannot run. Tab 5 is provisioned for all seven owned repos, and is shared with one other live session working
other repos — scope every commit by name, never `git add .`.

**Shipped, each verified in origin rather than by trusting quickmerge's exit code:**

1. **`execution-service@b70d2edb16` — the 864-row unblocker.** `readiness/instruction_path.py` exposes
   `instruction_path_availability(venue)` → `{batch, paper, live, actions, handlers, batch_unhandled_actions,
   detail}`, each mode `none|wired|deployed`, derived from three registries the runtime really dispatches on (the
   order-adapter factory, the new DeFi route table, the sports exchange adapters). No I/O.
   `python -m execution_service.readiness` is the cross-venv probe. To make "reads the real registry" true rather
   than aspirational, `DeFiAdapter`'s three private substring `if`-chains were extracted into
   `adapters/defi_instruction_routes.py`, which the adapter now dispatches through — match order and all three
   error wordings pinned by tests. `backtest_v2/action_handlers.py` gained `BATCH_SETTLEMENT_ACTIONS` /
   `BATCH_NO_FILL_ACTIONS` and a DERIVED `BATCH_UNHANDLED_ACTIONS`, so a new enum member lands in the gap set
   automatically. MEASURED verdicts and the `CONVERT_DUST, LP_BURN, LP_MINT, REPAY, WITHDRAW` batch gap are on the
   checkbox above; `COINBASE-FUTURES` correctly derives all-`none` because the factory refuses it and the check
   inherits that rather than stripping the suffix.

2. **`execution-service@dc4fad8de7` — delta-proxy price leg + QUOTE receipt point.** Detail on its checkbox.

3. **`unified-trading-pm@34999f0adf` / `694423478b` / `d262ccdaca`** — T5's frozen probe contract (posted BEFORE
   the code landed so T5 was never idle-waiting), checkbox flips, and findings.

**Gate lessons worth more than the code (all measured, none anticipated):**

- **quickmerge exit 0 does NOT mean landed.** Run 1 returned exit 0 while its log ended `❌ Re-gate FAILED`.
  Always verify with `git cat-file -e origin/<branch>:<path>` and an empty `git diff --stat origin/<branch>`.
  Capture the log to a FILE — `| tail -N` threw away the itemised violation and cost a diagnosis round-trip.
  Also: `❌ unified-trading-library: DIFFERS` at STAGE 1 is NOT a failure (clean tree, one commit behind, branch
  isolation mode) — grep for `Quality gates FAILED` / `Re-gate FAILED` instead.
- **`api/main.py` runs `app = create_app()` at IMPORT.** Any global mutation inside the factory is therefore an
  import-time side effect on the whole test suite. Wiring the manual handler there broke four pre-existing tests
  that build a bare `FastAPI()` with no `app.state.limiter` and then 500 inside slowapi.
- **A lifespan that only sets still leaks.** Moving the wiring to a lifespan was not enough: it never restored the
  globals, so the new test contaminated later tests on the same xdist worker and the same four failed again.
  `set_limiter_instance` / `set_manual_handler` now accept `None` so the previous values are restored on shutdown
  (a no-op in production, where shutdown is process exit).
- **`api/manual_instruction_api.py` sits at EXACTLY the 900-line file cap.** Ten lines of docstring took it to 910
  and failed the gate. Anything added there needs the file split first.
- **Re-run the size check after EVERY edit, not once per unit.** Two of the three unit-3 failures were size/state
  regressions introduced by a later edit in the same unit.

**Measured findings that changed this plan's picture:**

- Four of this plan's "silently wrong today" P0s were already fixed before it was authored — verified in CODE, not
  from the issue docs' checkboxes. Flipped above with file:line: OrderTracker CANCELLED/AMENDED, the CCXT
  `withdraw()` stub, `CloudKmsCustodyProvider`'s `chain_id=1` fallback, and the funds-isolation invariant.
- **`POST /manual/instruction` 404s on the deployed service** — its own P0 above. Found by answering "which app
  does the container actually serve".
- **CORRECTION to an earlier entry**: I first logged emergency close-all as "reports success while closing
  nothing" in production. `AccountInstructionOrchestrator` has ZERO production callers, so it is an unreachable
  latent trap, not a live defect. The todo carries the corrected reading and the required fix ORDER.

**W12 — built and verified, gating behind unit 3 (gates must stay serial).** New
`batch-live-reconciliation-service/api/resolution_state.py` + endpoints in `resolution_api.py` implement all three
W12 P0s. Verified by driving the real store: interlock raises without a pause; pause lookup is case-insensitive
(recon output casing vs operator input); a revoked pause is retained but no longer satisfies the interlock; a
VIRTUAL exclusion applies only to its own `run_date` and does NOT survive a new store; VIRTUAL without a
`run_date` is REJECTED rather than silently promoted to persistent; PERSISTENT ignores a supplied `run_date`,
reaches GCS, and survives a new store; revoke is a soft delete that retains the record and stops suppressing.
A corrupt exclusions object fails OPEN (breaks re-raised) rather than suppressing on half-parsed state.
Note: `client.upload_bytes` returns a value — this repo's convention is `_ = client.upload_bytes(...)`.

## Deferred work after 2026-08-20

| item | state | why |
|---|---|---|
| Emergency close-all | open P0 | needs real CLOSE_ALL wiring BEFORE any route — order matters |
| Delta-proxy position + credit legs | `BLOCKED-OPERATOR` | T1's superseded-shape ruling (Q12-Q16) |
| BATCH settlement gap | open P1 | `CONVERT_DUST, LP_BURN, LP_MINT, REPAY, WITHDRAW` have no handler |
| `api/app.py` vs `api/main.py` | open P0, needs operator | app.py holds production startup wiring the container never runs |
| W22 strategy→execution messaging | untouched | no `EventTransport` subscriber exists in execution-service |
| W11 9-state order lifecycle | untouched | needs T1's `OrderState` contract |
| W14/W15/W17, Elysium, settlement tail | untouched | not reached this session |

- 2026-08-20 — **W12 shipped: `batch-live-reconciliation-service@1e210addb1`** (verified by an empty
  `git diff --stat origin/live-defi-rollout` over all four files plus confirming `resolution_state.py` and
  `require_pause` resolve in the landed tree). Its first gate failed on two PRE-EXISTING tests
  (`test_book_correction_positive_delta_is_buy` / `..._negative_delta_is_sell`) which called `book_correction`
  with no pause and passed — they encode the pre-W12 contract, and the interlock is precisely the change. They
  now establish a pause first; the refusal itself stays asserted in `test_resolution_state.py`, so the behaviour
  they used to cover is not silently lost. Size + basedpyright were run BEFORE gating this time (the lesson from
  execution-service's four-attempt unit) and were clean.
