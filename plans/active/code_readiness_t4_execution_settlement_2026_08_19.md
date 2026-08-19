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

_None at authoring time._

## Todos

### W22 — strategy to execution messaging and the external instruction API

- [ ] [BACKEND] P0. Build the strategy→execution messaging path end to end. Confirmed unbuilt by a 2026-08-19
      workspace-wide search — the only live path is manual. Publish/read via the UTL `EventTransport` facade
      (`InMemoryTransport` for paper/colocated, Pub/Sub for live) so `paper(W) == batch-rerun(W)` holds at epsilon
      zero. SSOT: `/codex/02-data/live-data-persistence-and-event-log.md`.
- [ ] [BACKEND] P0. **Expose a real per-venue execution-instruction-path check.** This is the single check that
      unblocks grading on all 864 readiness rows — **T5 blocks on it directly.** Ship it early and tell T5.
- [ ] [BACKEND] P0. Build the external instruction API surface, coordinating the contract with T1.
- [ ] [BACKEND] P1. Complete the delta-proxy repricer generalization to the full price + position + credit triple.
      `DeltaProxyRepricer` + `QuoteMaintainer` implement the price leg only. **Needs T1's `QuoteInstruction`
      extension first** — build against the agreed shape meanwhile. Note the strategy-side receipt point
      (`QuoteHandler`) was deleted 2026-08-15 as dead code with no replacement; rebuild it. Evidence:
      `/plans/active/issues/execution_delta_proxy_repricer_generalization_2026_08_18.md`.

### W11 — order lifecycle and execution state

- [ ] [BACKEND] P0. Fix CeFi live venue-string dispatch in the order-adapter factory, broken for 9 of 12 major
      venues — same legacy bare-token table defect as strategy-service's. Coordinate the canonical form with T3.
- [ ] [BACKEND] P0. Add CANCELLED and AMENDED to `OrderTracker`. `GET /instructions/{id}` reports a genuinely
      cancelled order as SUBMITTED forever and `is_instruction_complete()` never flips true for a cancel-only
      instruction. Evidence:
      `/plans/active/issues/execution_order_tracker_missing_cancelled_amended_status_2026_08_17.md`.
- [ ] [BACKEND] P0. Implement the full 9-state order lifecycle once T1 lands the `OrderState` contract.
- [ ] [BACKEND] P0. Fix the broken emergency close-all path — strategy POSTs to `/api/orders` and execution-service
      exposes no such route.
- [ ] [BACKEND] P0. Build state recovery so a restart, a partial fill or a reconciliation drift cannot leave the two
      sides disagreeing. The artefacts describe this as guaranteed; it is not built.
- [ ] [BACKEND] P1. Verify the production live orchestrator actually satisfies the `LiveOrchestrator` protocol it is
      cast to — untested end to end, and the prior pass spot-checked location only. Evidence:
      `/plans/active/issues/execution_service_live_orchestrator_protocol_mismatch_untested_2026_08_16.md`.

### Correctness P0s — silently wrong today

- [ ] [BACKEND] P0. Implement the CCXT `withdraw()` stub. The real exchange call is commented out, so every
      CEX_WITHDRAW-routed venue (18 of 22) would report a successful withdrawal that never happened. Evidence:
      `/plans/active/issues/cefi_ccxt_withdraw_stub_returns_false_confirmed_2026_08_16.md`.
- [ ] [BACKEND] P0. Fix `CloudKmsCustodyProvider` silently defaulting an unmapped chain to `chain_id=1` (Ethereum)
      on HOT_TRADING and GAS_RESERVE wallets. UAC's own `resolve_chain_id()` raises on the same case — match it.
      Evidence: `/plans/active/issues/defi_cloud_kms_silent_wrong_chain_id_fallback_2026_08_16.md`.
- [ ] [BACKEND] P0. Reach-test every connector module. Marinade, Kamino and Jupiter connectors have zero production
      callers; the Pendle connector is built but never instantiated in `DeFiAdapter` and is absent from
      `DEFI_VENUE_TO_CONNECTOR_CLASS` / `DEFI_VENUE_TO_GATE_MARKER`. Wire them or delete them — no shims. Evidence:
      `/plans/active/issues/pendle_venue_onboarding_2026_08_16.md`.
- [ ] [BACKEND] P0. Enforce the funds-isolation invariant in code — funds NEVER move between clients; every transfer
      is scoped to one `client_id` and `TransferCoordinator` raises `CrossClientTransferForbiddenError`. SSOT:
      `/codex/04-architecture/client-funds-isolation.md`.

### W12 — reconciliation

- [ ] [BACKEND] P0. Build pause-before-manual-entry. Explicitly unbuilt.
- [ ] [BACKEND] P0. Build virtual and persistent delta exclusion. Explicitly unbuilt.
- [ ] [BACKEND] P0. Build the soft-delete audit trail. Explicitly unbuilt.
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

- 2026-08-19 — Plan authored. Allocation derived by `scripts/plan-hygiene/allocate_code_readiness_tranches.py`
  against the 892-doc active corpus. No code work started yet.
