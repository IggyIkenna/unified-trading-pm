---
doc_type: epic
title: Global Ledger + PnL Attribution Master
summary:
  L2 epic owning the canonical ledger architecture — 4 SSOT ledgers (Instruction/Passive/Treasury/ Pricing) + 4 derived
  views (Position/Exposure/PnL/PnLAttribution) + one RiskView; UAC LedgerRow + EventType(39, was 37)/AssetClass(17)
  enums + CrossClientTransferForbiddenError validator shipped. Migration plan itself stayed 0/27, but its Phase 3/5/6
  operator gate WAS acked 2026-05-23 (pm@351a47b61, recorded in the archived MTDS carry-rates plan — never synced back
  here until the 2026-07-12 re-audit) and the SAME Phase 7/8 scope (InstructionLedger/PricingLedger/TransferLedger
  writers + paper-mode PassiveLedger synthesiser) SHIPPED via the Citadel determinism-spine plan; live PassiveLedger
  listener + the acked ledger_type=treasury partition still genuinely missing.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos:
  [alerting-service, client-reporting-api, execution-service, greeks-service, instruments-service, strategy-service]
scope: [engineer, admin]
tags: [strategy, execution, uac, reconciliation, data-correctness, client-isolation]
related:
  [
    plans/archive/2026_05/global_ledger_pnl_attribution_discovery_2026_05_21.md,
    plans/archive/2026_05/global_ledger_pnl_attribution_migration_2026_06_01.md,
  ]
created: 2026-05-21
name: global_ledger_pnl_attribution_master
tier: L2
priority: P0
assigned_vm: vm-trading-core
parent: master_to_live_defi_2026_05_23
co_operators:
codex_ssots:
related_plans: []
last_updated: 2026-07-12
locked_by: live-defi-rollout
locked_since: 2026-05-21
---

# Global Ledger + PnL Attribution Master

**Owns**: the canonical ledger architecture from which position, exposure, PnL, and PnL-attribution are all derived.
Four SSOT ledgers (Instruction / Passive / Treasury / Pricing) authored by execution-service + strategy-service + MTDS +
instruments-service; four derived materialised views (Position / Exposure / PnL / PnLAttribution) computed in
strategy-service `position/` + `risk/` + `pnl/` + `portfolio_allocator/`; one RiskView consumed by alerting-service.

**Status (2026-05-23, was — see 2026-07-12 correction below)**: UAC schemas SHIPPED — `LedgerRow` + 5 enums
(`EventOrigin`, `EventType` 37 values, `AssetClass` 17 values, `Direction`, `OptionRight`) +
`CrossClientTransferForbiddenError` validator landed in `unified_api_contracts.canonical.crosscutting.ledger/`.
Discovery plan 36/38 BACKED + 2/38 PARTIAL (Phase 2 enum expansion + Phase 6 TreasuryLedger split — closed by enum
expansion + recorded decision; operator [ack] pending). Migration plan 0/27 — gated on operator [ack] of discovery Phase
3 / 5 / 6 decisions (was: "Phase 3 / 4 / 5" — internal numbering error, corrected 2026-07-12; see correction note below)
before implementation starts (target window: post-cutover, 2026-06-01).

> **CORRECTED 2026-07-12** (full re-audit — `plans/archive/2026_07/global_ledger_epic_reaudit_2026_07_12.md`, operator
> ruling finding 366): the 05-23 status line above is STALE/CONTRADICTED-BY-CODE on two points, verified read-only
> against repo HEAD:
>
> 1. **`EventType` is now 39 values, not 37** (`unified-api-contracts@dc67ae6f` margin-traceability PR added
>    `COLLATERAL_POSTED` / `MARGIN_RELEASED`, additive) — `AssetClass` is still 17 (unchanged). Both counts verified by
>    AST-walking `unified_api_contracts/canonical/crosscutting/ledger/_enums.py` at HEAD (`a2751f36`).
>    `CrossClientTransferForbiddenError`'s raise condition (`counterparty_client_id != client_id`) matches
>    `/codex/04-architecture/client-funds-isolation.md`'s HARD RULE — BACKED.
> 2. **"Migration plan 0/27... Phase 7/8 DEFERRED-POST-CUTOVER" is CONTRADICTED-BY-CODE for Phase 7 + Phase 8's paper
>    leg.** The archived `plans/archive/2026_05/global_ledger_pnl_attribution_migration_2026_06_01.md` itself is
>    correctly frozen at 0/27 (nothing was implemented THROUGH that gated plan) — but the SAME scope shipped through a
>    **separate, operator-commissioned plan**: `plans/active/citadel_paper_batch_live_reconciliation_2026_06_19.md`
>    (`parent_epic: batch_live_symmetry_master`, NOT this epic — created 2026-06-19, "The thesis (operator,
>    2026-06-19)"). Verified real + tested at repo HEAD, not stub/backtest-only:
>    - **Phase 7 (InstructionLedger writer)**: `unified-trading-library@41d50461`
>      `unified_trading_library/ledger/run_writer.py` (`write_run_ledger` / `write_run_pricing_ledger` /
>      `write_run_transfer_ledger` / `write_run_passive_ledger`, all four `ledger_type=` GCS writers) wired live via
>      `strategy-service/strategy_service/engine/backtest/ledger_emit.py::write_paper_run`. A related but DISTINCT
>      artifact, `execution-service/execution_service/pnl_attribution/rows.py::build_attribution_rows`
>      (`execution-service@a4145838`→`49f42f77`, 140 lines, tested
>      `tests/unit/pnl_attribution/test_build_attribution_rows.py`, 342 lines) builds the derived `PnLAttributionRow`
>      factor×layer decomposition — real and shipped, though it is the PnLAttribution DERIVED view, not the
>      InstructionLedger SSOT write path itself.
>    - **Phase 8 (PassiveLedger synthesiser), paper/backtest leg**:
>      `strategy-service/strategy_service/engine/backtest/paper_run_passive.py` (`build_paper_run_passive` /
>      `emit_paper_run_passive`) constructs real `event_origin=PASSIVE` canonical `LedgerRow`s (STAKING_REWARD /
>      LENDING_INTEREST / FUNDING_ACCRUAL) via the UTL SSOT and writes them to `ledger_type=passive/{run_id}.jsonl` —
>      tested (`tests/unit/engine/backtest/test_paper_run_passive.py`). **NOT yet shipped**: the LIVE (non-paper)
>      per-event divergence-check listener this epic's own VM-assignment notes describe ("PassiveLedger synthesiser runs
>      inside `StrategySupervisor` per-client subprocess") — grepped `strategy-service` for a live
>      on-chain/venue-emission listener; none found. That piece is a genuine residual gap (carried forward below).
>    - **Governance note (RESOLVED 2026-07-12 — no breach)**: the operator [ack] this epic reports as "pending" actually
>      LANDED the same evening the status line was written — `unified-trading-pm@351a47b61` (2026-05-23 20:42 +0100, "6
>      operator-ACK'd decisions... Per operator") recorded every gated decision in
>      `plans/archive/2026_05/pricing_ledger_carry_rates_mtds_2026_06_01.md` § "Operator decisions (ACK'd 2026-05-23)":
>      Phase 3 late-arriving-data → Option A event-sourced append-only; Phase 4/6 TreasuryLedger → separate partition
>      `ledger_type=treasury/client_id={cid}/` (writer = fund-administration-service); Phase 5a greeks home → new
>      `greeks-service/` repo; plus 5b PricingLedger cadence + 5c dividend_yield / rebase_rate BOTH-paths. The shipped
>      Citadel-plan code is CONSISTENT with those acks. The only failure was doc-sync: neither this epic nor the
>      discovery plan's archival banner was ever updated with the ack, so both still read "pending" 7 weeks later.
>      Residual nuance: the acked `ledger_type=treasury/` partition (fund-administration-service writer) is itself still
>      unimplemented at HEAD (zero code hits for `ledger_type=treasury` across UTL / strategy-service /
>      execution-service / fund-administration-service / client-reporting-api); the Citadel plan's
>      `ledger_type=transfer` run tape is an adjacent paper-run construct, not that treasury SSOT.
> 3. **Internal phase-numbering inconsistency** (this doc, pre-existing): this line says discovery-plan ack is pending
>    on "Phase 3 / 4 / 5"; the "Archived plans" section below (and the archived discovery plan's own phase headers —
>    Phase 3=late-arriving-data, Phase 4=writer-side gap analysis [not ack-gated], Phase 5=pricing+greeks [ack-gated, >
>    > includes greeks-home], Phase 6=treasury cohort [ack-gated]) confirm the correct ack-gated set is **Phase 3 / 5 /
>    > 6**, not 3/4/5. This line is corrected to match.

See [`README.md`](README.md) for the canonical epic frontmatter schema + body structure.

## Codex SSOTs

| Doc                                                                   | Owns                                                                                                                                                                                                                                                                                                                                                                                     |
| --------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `/codex/04-architecture/global-ledger-architecture.md`                | 4-SSOT-+-4-derived ledger model; universal PnL recipe; ownership table; per-service writer/reader gap status                                                                                                                                                                                                                                                                             |
| `/codex/02-data/ledger-event-taxonomy.md`                             | `EventOrigin` / `EventType` (39, was: 37 — corrected 2026-07-14, doc-reconciliation finding 70: this epic's own 2026-07-12 correction callout above already established 39 at HEAD, `unified-api-contracts@dc67ae6f`; the codex doc itself still says 37, CODEX-GATED, not edited here) / `AssetClass` (17) / `Direction` / `OptionRight` enum SSOT + routing summary + invariant tables |
| `/codex/09-strategy/architecture-v2/cross-cutting/pnl-attribution.md` | Carry-as-theta-family attribution framing; ledger→factor decomposition (delta/gamma/theta/vega/carry/funding/settlement/residual)                                                                                                                                                                                                                                                        |
| `/codex/04-architecture/client-funds-isolation.md`                    | Cross-client transfer HARD RULE — `client_id == counterparty_client_id` on every transfer/bridge row                                                                                                                                                                                                                                                                                     |

**VERIFIED 2026-07-12** (re-audit): all 4 docs exist at HEAD, `status: current`, substantial (185-864 lines each, not
stubs), last git-touched 2026-07-04 — CONTRADICTS this epic's own "Archived plans" claim below that codex SSOT docs are
"DEFERRED-POST-CUTOVER." **CODEX-GATED finding — ACTIONED 2026-07-13** (was: "not edited by this audit — operator-gated
codex edit; flagged in the re-audit plan's Progress Log for a follow-up `[DOCS]` todo" — corrected 2026-07-14,
doc-reconciliation finding 73: operator authorization was granted 2026-07-13 and the codex doc was edited the same day —
see `plans/archive/2026_07/global_ledger_epic_reaudit_2026_07_12.md`'s Progress Log): `global-ledger-architecture.md`'s
"Current-State Gaps" table's `execution-service` row (§ "Current-State Gaps (Audit 2026-05-23)") — which listed a
`build_attribution_rows() stub`, itself stale/CONTRADICTED-BY-CODE per the Phase 7 evidence above (the function is real,
140 lines, tested) — now carries a `[DELTA 2026-07-13]`-banner-backed `(was: …)` correction citing
`execution-service@a4145838`→`49f42f77` + `tests/unit/pnl_attribution/test_build_attribution_rows.py`; verified live in
the codex doc at HEAD.

## Cross-epic handshakes

| Partner epic                             | Handshake                                                                                                          |
| ---------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| `execution_master`                       | InstructionLedger + PassiveLedger writers (`attribution_builder.build_attribution_rows`); emits via writegate path |
| `strategy_master`                        | Derived-ledger compute (`strategy_service/{position,pnl,risk,portfolio_allocator}/`); PassiveLedger synthesiser    |
| `mtds_mdps_master`                       | PricingLedger writes (`MARK_UPDATE` rows with mid/bid/ask/IV/greeks); carry-rate emission                          |
| `instruments_master`                     | Instrument metadata for passive-event synthesis (expiry / funding interval / rebase schedule / `exercise_style`)   |
| `client_isolation_and_governance_master` | UAC schema governance + cross-client funds isolation HARD RULE validator                                           |
| `observability_master`                   | RiskView consumes PassiveLedger LIQUIDATION/SLASHING rows for alerting                                             |
| `dart_and_promote_master`                | DART consumes PnL + PnLAttribution for promote workflow decisions                                                  |

## Assigned active plans

_(no active plans currently declare `parent_epic: global_ledger_pnl_attribution_master`. Audit-pool wrapper plans for
this epic land here as they are dispatched. See [README.md](README.md) for the audit→plan→epic flow.)_

## Archived plans

### [`global_ledger_pnl_attribution_discovery_2026_05_21`](../archive/2026_05/global_ledger_pnl_attribution_discovery_2026_05_21.md)

**status**: ✅ ARCHIVED 2026-05-23 — 36/38 BACKED + 2/38 PARTIAL; UAC schemas shipped; operator [ack] pending on Phase
3/5/6 (was pending at archival time; **ACK'd later the same day** — `unified-trading-pm@351a47b61`, see correction
below).

**Deferred (migrated):**

- **Operator [ack] pending (Phase 3/5/6)**: Late-arriving-data handling + greeks home + TreasuryLedger split decisions.
  Gate for migration sub-plan start. **CORRECTED 2026-07-12 — the ack LANDED 2026-05-23**
  (`unified-trading-pm@351a47b61`, 20:42 +0100, same day as archival): all gated decisions recorded in
  `plans/archive/2026_05/pricing_ledger_carry_rates_mtds_2026_06_01.md` § "Operator decisions (ACK'd 2026-05-23)". This
  banner was simply never synced after the ack. See the correction callout above the Status line.
- **Codex SSOT docs (DEFERRED-POST-CUTOVER)**: `global-ledger-architecture.md` + `ledger-event-taxonomy.md` +
  `pnl-attribution.md` update + CLAUDE.md pointer. All gated on service-repo access. **CORRECTED 2026-07-12 —
  CONTRADICTED-BY-CODE**: all 4 codex docs exist, are `status: current`, non-stub, and were last updated 2026-07-04 —
  see the "Codex SSOTs" table note above for the one residual gap found (a stale sub-claim inside
  `global-ledger-architecture.md` itself, flagged CODEX-GATED, not this epic's to fix).

### [`global_ledger_pnl_attribution_migration_2026_06_01`](../archive/2026_05/global_ledger_pnl_attribution_migration_2026_06_01.md)

**status**: ✅ ARCHIVED 2026-05-23 — Stub plan; 0/27 items implemented (all DEFERRED-OPERATOR-DECISION, start window
2026-06-01 post-cutover).

**Deferred (migrated):**

- **Pre-migration gate — Phase 3 operator [ack]**: Late-arriving-data handling decision (operator [ack] pending from
  discovery plan). **CORRECTED 2026-07-12 — ACK'd 2026-05-23** (`unified-trading-pm@351a47b61`,
  `plans/archive/2026_05/pricing_ledger_carry_rates_mtds_2026_06_01.md` § Operator decisions): **Option A —
  event-sourced append-only** + pre-join view layer at API boundary (enrichment closed set: clearing_house_id,
  final_fee_corrected, fx_rate_locked, regulatory_report_id, custody_reconciled). The shipped `LedgerRow` docstring
  implements exactly this (append-only `<type>_ENRICHMENT` rows); its "provisional" label is now itself stale.
- **Pre-migration gate — Phase 5 operator [ack]** (was: "Phase 4" — numbering corrected 2026-07-12): Greeks home (where
  greeks rows live in ledger) decision (operator [ack] pending from discovery plan). **CORRECTED 2026-07-12 — ACK'd
  2026-05-23** (same record, "Phase 5a greeks home"): **new `greeks-service/` repo** (not folded into MTDS or
  strategy-service). Shipped consistent with the ack: `unified-api-contracts@709e9aff` (greek + carry columns on
  `LedgerRow`), `greeks-service@b0b702d` (Pub/Sub sub + IS reader + PricingLedger writer).
- **Pre-migration gate — Phase 6 operator [ack]** (was: "Phase 5" — numbering corrected 2026-07-12): TreasuryLedger
  split decision (operator [ack] pending from discovery plan). **CORRECTED 2026-07-12 — ACK'd 2026-05-23** (same record,
  "Phase 4/6 TreasuryLedger split"): **separate partition** `ledger_type=treasury/client_id={cid}/`, writer =
  fund-administration-service. NOTE: that acked treasury partition is still UNIMPLEMENTED at HEAD (zero code hits for
  `ledger_type=treasury`); the `ledger_type=transfer` run tape shipped in `unified-trading-library@41d50461`
  (`write_run_transfer_ledger`) is an adjacent, run-scoped paper-run construct — not the treasury SSOT the ack
  specifies. Genuine residual implementation gap (fund-administration-service writer).
- **Phase 7 — execution-service InstructionLedger writer refactor**: `attribution_builder.build_attribution_rows` → emit
  via writegate path. Was: DEFERRED-POST-CUTOVER (gate: Phase 3/4/5 ack). **CORRECTED 2026-07-12 —
  CONTRADICTED-BY-CODE**: SHIPPED, but via `plans/active/citadel_paper_batch_live_reconciliation_2026_06_19.md` (a
  separate, operator-commissioned plan under `parent_epic: batch_live_symmetry_master`), not through this plan's gate.
  See the correction callout above the Status line for full evidence (unified-trading-library@41d50461,
  execution-service@a4145838→49f42f77).
- **Phase 8 — strategy-service PassiveLedger synthesiser**: Per-event divergence check path. Was: DEFERRED-POST-CUTOVER
  (gate: Phase 3/4/5 ack). **CORRECTED 2026-07-12 — PARTIAL**: the paper/backtest-mode synthesiser SHIPPED (same Citadel
  plan, `strategy-service/strategy_service/engine/backtest/paper_run_passive.py`) — real `event_origin=PASSIVE` rows,
  tested. The LIVE per-event divergence-check listener ("Per-event divergence check path" specifically) is genuinely NOT
  shipped — forward-carried as a new P3 todo above.
- **Phase 9 — DART / client-reporting-api / alerting-service reader refactor**: Consumes PnL + PnLAttribution.
  DEFERRED-POST-CUTOVER (gate: Phase 7/8) — **NOT independently re-verified this audit** (out of the seeded claim
  manifest's scope); still plausible as genuinely deferred given Phase 7/8's partial-not-complete state.

## VM assignment notes

Epic runs on **`vm-trading-core`** co-located with `execution_master` + `strategy_master` + `trading_agent_master` (per
`README.md` § "23 epics in 6 tiers" — was: § "19 epics in 5 tiers"; corrected 2026-07-12, finding 10003, §A2 B-queue
ruling, `plans/active/issues/plan_reconciliation_operator_decisions_2026_07_11.md`. NB the per-epic VM-topology model
this line references is itself SUPERSEDED per `README.md`'s own top banner — single-VM role-based dispatch since
2026-06-27; this citation is retained only to name the co-located service trio). Bulk of implementation lands in
execution-service + strategy-service code, which is the trading-core service trio. UAC schema PRs route through
`client_isolation_and_governance_master` review per its UAC-schema ownership.

**Anticipated net-new VM prefixes** (discovery Phase 8 confirmed ABSORB-into-existing for all). **VERIFIED 2026-07-12**
(re-audit, live grep of `deployment-service/scripts/vm/vm_zombie_watchdog.py`): zero `ledger-reconcile-` or
`passive-listener-` entries registered — BACKED, no net-new prefixes added. `strategy-paper-` / `strategy-live-` /
`client-reporting-cutover-` all confirmed present in `VM_PREFIX_TO_BUCKET`.

- `ledger-reconcile-` → **ABSORB into existing `batch-live-recon-`** (was: "`batch-live-recon-cron-`" — corrected
  2026-07-12: that string is the launcher script's name, `launch-batch-live-recon-cron-vm.sh`; the actual registered
  VM-name prefix / `VM_PREFIX_TO_BUCKET` key is `batch-live-recon-`) (SCHEDULED_RECURRING) for daily venue-vs-ledger
  reconciliation. Confirmed comment in the registry: "Nightly T+1 run of batch-live-reconciliation-service."
- `passive-listener-` → **ABSORB into existing `strategy-live-*`** (LONG_LIVED_LIVE) — PassiveLedger synthesiser runs
  inside `StrategySupervisor` per-client subprocess. **NOTE 2026-07-12**: this describes the LIVE listener, which per
  the P3 forward-carry todo above is NOT yet shipped — the prefix-absorption decision is confirmed correct (no VM
  registered), but the workload it describes doesn't exist yet either, so "absorbed" should be read as "will absorb,
  when built," not "already running inside `strategy-live-*` today."
- Derived ledgers → use existing `strategy-paper-*` / `strategy-live-*` / `client-reporting-cutover-*` cohorts.

No new prefixes added to `VM_PREFIX_TO_BUCKET`.

## Continuous-verification path (post-migration)

| Surface                                              | Verification                      | Cadence      |
| ---------------------------------------------------- | --------------------------------- | ------------ |
| InstructionLedger ⟷ venue execution reports          | Daily reconciliation cron         | T+1 daily    |
| PassiveLedger synthesiser ⟷ on-chain/venue emissions | Per-event divergence check        | Per emission |
| PricingLedger ⟷ MTDS canonical prices                | Snapshot cross-check              | Hourly       |
| Derived ledgers ⟷ SSOT replay                        | Backfill replay = production view | Pre-deploy   |
| RiskView liquidation rows ⟷ alerting-service pages   | End-to-end smoke                  | Per event    |
