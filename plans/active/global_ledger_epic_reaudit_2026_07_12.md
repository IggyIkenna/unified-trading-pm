---
doc_type: plan
title: Global Ledger + PnL Attribution epic — full re-audit vs repo reality
summary: >-
  Operator-ordered (plan-reconciliation finding 366, 2026-07-12) full re-audit of
  plans/epics/global_ledger_pnl_attribution_master.md — the epic is ~7 weeks stale (last_updated 2026-05-23) and this
  session's spot-checks already found evidence that Phase 7 (InstructionLedger writer) and Phase 8 (PassiveLedger
  synthesiser), both claimed "0/27 DEFERRED-POST-CUTOVER," have partially-shipped, unacknowledged code in
  execution-service and strategy-service. Every claim in the epic gets enumerated, verified against repo code + shipped
  SHAs, given a per-phase verdict, and the epic synced with evidence.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    unified-trading-pm,
    execution-service,
    strategy-service,
    unified-api-contracts,
    greeks-service,
    instruments-service,
    alerting-service,
    client-reporting-api,
  ]
scope: [engineer, admin]
tags: [audit, epic-reaudit, global-ledger, pnl-attribution, plan-reconciliation, evidence-verification]
related:
  [
    ../epics/global_ledger_pnl_attribution_master.md,
    issues/plan_reconciliation_operator_decisions_2026_07_11.md,
    ../archive/2026_05/global_ledger_pnl_attribution_discovery_2026_05_21.md,
    ../archive/2026_05/global_ledger_pnl_attribution_migration_2026_06_01.md,
  ]
created: "2026-07-12"
last_updated: 2026-07-12
parent_epic: global_ledger_pnl_attribution_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: research
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 3.6
assigned_role: review
drift_direction: correct-codex
depends_on:
locked_by:
locked_since:
supersedes:
superseded_by:
source:
  "operator ruling 2026-07-12, plan-reconciliation Q&A (finding 366) — see
  plans/active/issues/plan_reconciliation_operator_decisions_2026_07_11.md §A2"
---

> **Why this plan exists.** `plans/epics/global_ledger_pnl_attribution_master.md` frontmatter reads
> `last_updated: 2026-05-23` — ~7 weeks stale as of this plan's creation (2026-07-12). The epic's own body claims Phase
> 7 (execution-service InstructionLedger writer refactor) and Phase 8 (strategy-service PassiveLedger synthesiser) are
> both "DEFERRED-POST-CUTOVER" with the archived migration plan at literal 0/27 items implemented. A same-session grep
> already found `PassiveLedger` referenced in `strategy-service/strategy_service/engine/backtest/paper_run_passive.py`
>
> - `paper_run_attribution.py`, and `build_attribution_rows`/`InstructionLedger`-adjacent code live in
>   `execution-service/execution_service/pnl_attribution/rows.py` with a passing unit test
>   (`tests/unit/pnl_attribution/test_build_attribution_rows.py`). That is exactly the "Phase-8 partially shipped
>   unacknowledged" pattern the operator flagged — this plan runs the full re-audit, not just that one spot-check.

## Codex SSOTs

Read these before verifying claims — they are the target-state the epic's claims are supposed to match:

| Doc                                                                  | Owns                                                                                                  |
| -------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| `codex/04-architecture/global-ledger-architecture.md`                | 4-SSOT-+-4-derived ledger model; universal PnL recipe; per-service writer/reader gap status           |
| `codex/02-data/ledger-event-taxonomy.md`                             | `EventOrigin`/`EventType`(37)/`AssetClass`(17)/`Direction`/`OptionRight` enum SSOT + invariant tables |
| `codex/09-strategy/architecture-v2/cross-cutting/pnl-attribution.md` | Carry-as-theta-family attribution framing; ledger→factor decomposition                                |
| `codex/04-architecture/client-funds-isolation.md`                    | Cross-client transfer HARD RULE — `client_id == counterparty_client_id` on every transfer/bridge row  |
| `plans/PLAN_FORMAT.md`, `plans/active/task_template.md`              | Plan/epic authoring format this re-audit's output must conform to                                     |

## Pre-audit manifest — claims to verify (seed; todo 1 finalizes)

| #   | Claim (epic location)                                                                                | Spot-check status this session                                                                                                                                   |
| --- | ---------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Frontmatter `last_updated: 2026-05-23`, `status: active`, `locked_by: live-defi-rollout`             | Stale by construction — 7 weeks with zero updates while dependent code shipped                                                                                   |
| 2   | "UAC schemas SHIPPED — `LedgerRow` + 5 enums + `CrossClientTransferForbiddenError` validator landed" | CONFIRMED present: `unified_api_contracts/canonical/crosscutting/ledger/_ledger_row.py` exists — verify enum counts + validator behavior, not just file presence |
| 3   | "Discovery plan 36/38 BACKED + 2/38 PARTIAL... operator [ack] pending"                               | Unverified — check for any ack since 2026-05-23                                                                                                                  |
| 4   | "Migration plan 0/27 — gated on operator [ack]... target window post-cutover 2026-06-01"             | CONTRADICTED by spot-check: `PassiveLedger` (Phase 8) + attribution-row code (Phase 7) already exist in strategy-service/execution-service                       |
| 5   | P2 item: greeks cross-check "shipped at `greeks-service@b0b702d`"                                    | Unverified — confirm SHA + that the Pub/Sub sub + IS API integration + write-back are still live at HEAD                                                         |
| 6   | "Anticipated net-new VM prefixes... ABSORB-into-existing for all... No new prefixes added"           | Unverified against live `VM_PREFIX_TO_BUCKET` registry                                                                                                           |
| 7   | 4 Codex SSOT docs cited as owning docs                                                               | Unverified whether these docs exist / reflect current ledger state (epic flags them "DEFERRED-POST-CUTOVER")                                                     |

## Todos

- [ ] [AUDIT] P0. **Finalize the claim manifest** — walk `plans/epics/global_ledger_pnl_attribution_master.md` line by
      line (frontmatter + body: status line, "Assigned active plans," "Archived plans," "VM assignment notes,"
      "Continuous-verification path") and extend the seed table above into the complete claim-by-claim checklist with
      source line numbers. Gate: table has ≥1 row per distinct factual claim in the epic.
- [ ] [AUDIT] P0. **Verify claim #2 (UAC schema-shipped)** — read
      `unified-api-contracts/unified_api_contracts/canonical/crosscutting/ledger/` in full: confirm `LedgerRow` fields,
      count `EventType`/`AssetClass` enum members against the claimed 37/17, and read
      `CrossClientTransferForbiddenError`'s raise condition against `codex/04-architecture/client-funds-isolation.md`.
      Gate: verdict (BACKED/PARTIAL/STALE) + repo@sha citation.
- [ ] [AUDIT] P0. **Verify claim #4 Phase 8 (PassiveLedger)** — read
      `strategy-service/strategy_service/engine/backtest/paper_run_passive.py` +
      `strategy_service/engine/backtest/paper_run_attribution.py` + their tests in full. Determine: is this the real
      Phase 8 "PassiveLedger synthesiser... per-event divergence check path" the epic describes, or an unrelated
      backtest-only construct that happens to share the name? If real, the epic's "Phase 8 DEFERRED-POST-CUTOVER, gate:
      Phase 3/4/5 ack" framing is FALSE and the archived migration plan's "0/27" count is wrong. Gate: verdict +
      file:line evidence either way.
- [ ] [AUDIT] P0. **Verify claim #4 Phase 7 (InstructionLedger writer)** — read
      `execution-service/execution_service/pnl_attribution/rows.py` + `build_attribution_rows` +
      `tests/unit/pnl_attribution/test_build_attribution_rows.py` in full. Determine whether this is the Phase 7
      "`attribution_builder.build_attribution_rows` → emit via writegate path" work the epic claims is
      DEFERRED-POST-CUTOVER. Gate: verdict + file:line evidence.
- [ ] [AUDIT] P0. **Verify claim #3 — operator-[ack] gate status.** Grep `plans/active/_agent_pings.md` history and this
      epic's own commit log for any operator ack of discovery Phase 3 (late-arriving-data) / Phase 4 (greeks-home) /
      Phase 5/6 (TreasuryLedger split) since 2026-05-23. If todos above confirm Phase 7/8 code shipped WITHOUT a
      recorded ack, this is a governance-gate breach (code shipped past an operator-gated decision point) — flag
      explicitly, do not silently normalize it as "the gate must have been informally cleared."
- [ ] [AUDIT] P1. **Verify claim #5 (greeks P2 item)** — confirm `greeks-service@b0b702d` exists in git history; read
      the current HEAD state of the Pub/Sub subscription + IS API integration + PricingLedger write-back described;
      confirm no regression/removal since that SHA. Gate: verdict + repo@sha.
- [ ] [AUDIT] P1. **Verify claim #6 (VM prefixes)** — grep the live `VM_PREFIX_TO_BUCKET` registry
      (`deployment-service/scripts/vm/` per CLAUDE.md § Launching VMs) for `ledger-reconcile-` / `passive-listener-` and
      confirm the epic's claimed absorption targets (`batch-live-recon-cron-`, `strategy-live-*`, `strategy-paper-*`,
      `client-reporting-cutover-*`) actually run the described workloads, not just that no new prefix string was
      registered.
- [ ] [AUDIT] P1. **Verify claim #7 (4 Codex SSOTs)** — for each of the 4 codex docs in the "Codex SSOTs" table above,
      confirm the file exists at HEAD and its content is not a stub; if any is missing/stub, note it as a real
      deferred-doc gap rather than assuming the epic's "DEFERRED-POST-CUTOVER" framing self-resolves it.
- [ ] [AUDIT] P0. **Produce the per-phase verdict table** — one row per claim from todo 1, verdict ∈ {BACKED, PARTIAL,
      STALE, CONTRADICTED-BY-CODE}, with repo@sha or file:line evidence per row. This is the audit's primary
      deliverable; embed it in this plan's Progress Log.
- [ ] [CODE] P0. **Sync the epic** — edit `plans/epics/global_ledger_pnl_attribution_master.md`: bump `last_updated`,
      correct the status line and any STALE/CONTRADICTED-BY-CODE body claims found above (esp. the Phase 7/Phase 8
      framing if todos 3/4 confirm real shipped work), with evidence citations inline. Do not leave the 7-week-stale
      date unfixed even if every individual claim turns out BACKED.
- [ ] [CODE] P1. **Un-gate or forward-carry real shipped scope.** If todos 3/4 confirm genuine Phase 7/8 progress, the
      archived `plans/archive/2026_05/global_ledger_pnl_attribution_migration_2026_06_01.md` cannot be edited (archives
      are frozen) — decide whether to (a) spawn a fresh small active plan under
      `parent_epic: global_ledger_pnl_attribution_master` carrying the residual real scope forward with credit for what
      already shipped, or (b) fold the residual into this epic's existing P2/P3 sections directly. Document the choice +
      execute it.
- [ ] [AUDIT] P1. **Escalate any governance-gate breach found in todo 5** to the operator using the structured options
      format (`SUB_AGENT_MANDATORY_RULES.md` § "When escalating") — do not silently resolve a finding that code shipped
      past an un-acked operator decision point.
- [ ] [DOCS] P1. **Post-phase codex-alignment check** — for each of the 4 Codex SSOTs, file a corrective `[DOCS]`
      follow-up todo in THIS plan (not a silent chat deferral) if todo 7 found it missing/stale; do not close this plan
      with a known codex gap left undocumented.
- [ ] [DOCS] P0. **Wire findings into the reconciliation issue doc** — append a dated Progress Log entry to
      `plans/active/issues/plan_reconciliation_operator_decisions_2026_07_11.md` §A2 citing finding 366 and this plan's
      verdict table (repo@sha for the epic-sync commit), so the reconciliation record stays authoritative.

## Progress Log

- **2026-07-12** — Plan authored per operator ruling 2026-07-12 (finding 366,
  `plans/active/issues/plan_reconciliation_operator_decisions_2026_07_11.md` §A2: "FULL RE-AUDIT of global_ledger
  epic... authored as HUMAN plan (assigned_vm: NA)"). Seed claim table populated from this session's read of the epic
  - a same-session grep confirming `PassiveLedger` in strategy-service and `build_attribution_rows` in execution-service
    — both areas the epic claims are 0% shipped. No verification or epic edits performed yet; that is this plan's scope.
