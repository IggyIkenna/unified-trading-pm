---
title: Human-led audit pool — issue catalogue for background-agent remediation
created: 2026-05-21
locked_by: live-defi-rollout
locked_since: 2026-05-21
priority: P0
status: SEEDED — initial 14-row catalogue. Rows graduate to ACKED + wrapper-plan as humans pick them up.
parent_epic: plan_hygiene_master
execution_scope: local-only
related_plans:
  - master_to_live_defi_2026_05_23.md
  - mega_audit_and_plan_beefup_progression_2026_05_20.md
  - strategy_archetype_logic_audit_2026_05_20.md
  - mtds_mdps_master.md
estimate_class: design
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.6
---

## Why this exists (operator framing — 2026-05-21)

Verbatim from operator note to Harsh ahead of meet, 2026-05-21:

1. We've done most of the work to get background agents polling with orchestrator working — considering a way to
   leverage that at scale below.
2. We need background agents to work regardless — we assumed they would drive our trading system when we are not at
   desk, so any issues need to be solved regardless.
3. Assuming they can work 24/7, why not hand them clear todos for plans, so we can focus on more complex audits during
   human/manual hours? Easier to synchronise a shared pool of work vs everyday new splits and coordinating 100s of tasks
   that way, vs one or two larger structured audits each daily instead. Agent orchestrator can handle telling the slots
   what to do, reading CLAUDE.md and using its brain for standard tasks.
4. If agreed on the above, what should those human-led audits include — ideas seeded below. Split them into issue docs +
   pick them up when we choose + make plans out of them that wrap existing plans + any new ones from issues/bugs +
   continue to assign background agents to solve, while we move onto new plans.
5. This doesn't stop us splitting work; it just focuses splits on Opus 4.7 1M-context human work. Handover also becomes
   much easier — no "take Harsh's work he's left" because background continues either way + the pool itself is shared.

## The mechanic — how a row in this doc becomes background-agent work

```
            ┌─ this doc (issue pool — 14 rows seeded) ─┐
            │                                          │
[row picked up by human, Opus 4.7 1M context]
            │
            ▼
[audit doc produced — `plans/audit/results/<slug>_2026_05_21.md`]
   • walks code + plans + codex docs vs intent
   • surfaces findings as P0/P1/P2/P3
   • declares mockability + dep mocks where backfill incomplete
            │
            ▼
[plans upgraded — favour upgrading existing plans over creating new ones]
   • each finding → todo in the most-relevant existing active plan
   • new findings without an existing plan home → new plan in `plans/active/`
            │
            ▼
[wrapper remediation plan — `plans/active/<slug>_remediation_2026_05_21.md`]
   • envelopes the upgraded existing plans + new ones as sub-plans
   • single plan-of-record for the AWS background-agent pool to dispatch from
   • inherits priority + ack from operator at wrapper-plan create time
            │
            ▼
[AWS 18-slot pool dispatches remediation work 24/7]
   • orchestrator reads CLAUDE.md + sub-agent mandatory rules
   • blocked items → BLOCKED-CREDENTIALS / BLOCKED-OPERATOR-DECISION ping back to humans
   • non-blocked items → shipped + plan-flipped per Half-1+2 commit pattern
            │
            ▼
[row archives from this pool — `resolution:` block names wrapper plan]
```

**Human work** = audit + plan upgrades + wrapper-plan creation + ack decisions. **Agent work** = remediation execution
against the wrapper plan. Audit work is Opus 4.7 1M context (cross-archetype, cross-codebase scope per
[`codex/06-coding-standards/model-tier-selection.md`](../../../codex/06-coding-standards/model-tier-selection.md));
remediation execution defaults to Sonnet 4.6.

## Roles

- **Operator (Ikenna)** — picks rows for self / Harsh; final ack on wrapper-plan scope + priorities.
- **Harsh** — picks rows for self; runs audits when awake; produces wrapper plans for agent dispatch.
- **AWS 18-slot pool** — pulls remediation items from wrapper plans; reads CLAUDE.md + sub-agent mandatory rules; pings
  humans on `BLOCKED-*` states.
- **Slot-1 main (both sides)** — owns this doc's row state + the master plan's "Human-led audit pool" cross-link.

## Status legend (per row)

| Status                 | Meaning                                                                        |
| ---------------------- | ------------------------------------------------------------------------------ |
| `SEEDED`               | row proposed here; no human picked up yet                                      |
| `PICKED-UP <owner>`    | human owner started the audit                                                  |
| `AUDIT-COMPLETE`       | audit doc landed in `plans/audit/results/`; wrapper plan not yet created       |
| `WRAPPER-PLAN-CREATED` | wrapper plan in `plans/active/`; dispatched to AWS pool                        |
| `IN-FLIGHT`            | wrapper plan being executed by agents; some todos open                         |
| `DONE`                 | wrapper plan resolved; archives both this row + the wrapper plan               |
| `BLOCKED-*`            | per CLAUDE.md § "External Data Is Always Available" closed-set blocking states |

## The 14 audit rows

### #1. Strategy archetype audit (53 archetypes, cross-codebase)

| Field             | Value                                                                                                                                                                                                                                                                                        |
| ----------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Track             | AUDIT-EXISTING                                                                                                                                                                                                                                                                               |
| Owner-side        | Ikenna (in-flight via parallel Opus-1M agent)                                                                                                                                                                                                                                                |
| Mockability       | n/a — audit reads code + plans + codex                                                                                                                                                                                                                                                       |
| Deps              | Post strategy-service consolidation (Phase 11) clean                                                                                                                                                                                                                                         |
| Wrapper plan      | TBD post-audit                                                                                                                                                                                                                                                                               |
| Wraps existing    | [`strategy_archetype_logic_audit_2026_05_20.md`](../../audit/results/strategy_archetype_logic_audit_2026_05_20.md), `strategy_and_dart_master_SUPERSEDED_2026_05_21.md`, `defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md`, `defi_recursive_borrow_archetypes_2026_05_10.md` |
| Operator approval | n/a — already acked 2026-05-20                                                                                                                                                                                                                                                               |
| Status            | `IN-FLIGHT`                                                                                                                                                                                                                                                                                  |

Owns: per-archetype logic audit + master strategy plan deliverable. Not in scope for re-pickup — included for inventory
completeness.

### #2. Data pipeline mega audit (Phase A → D)

| Field             | Value                                                                                    |
| ----------------- | ---------------------------------------------------------------------------------------- |
| Track             | AUDIT-EXISTING                                                                           |
| Owner-side        | Ikenna (mega audit Phase A complete; B/C/D in-flight)                                    |
| Mockability       | n/a — audit reads code + manifest data + GCS/S3 reality                                  |
| Deps              | Phase -2 / -1 consolidation tail                                                         |
| Wrapper plan      | [`mtds_mdps_master.md`](../mtds_mdps_master.md) (already exists)                         |
| Wraps existing    | `mega_audit_and_plan_beefup_progression_2026_05_20.md` + 8 sequenced ordering-step plans |
| Operator approval | n/a — already acked 2026-05-20                                                           |
| Status            | `IN-FLIGHT` (Phase A GREEN; B/C/D pending)                                               |

Owns: data-pipeline correctness (manifest divergence / v8 backfill / expected_coverage / IS↔MTDS contract). Included
for inventory completeness; not for re-pickup.

### #3. DeFi May-23 archetypes — batch backtest e2e (mock-data feed)

| Field             | Value                                                                                                                                                                                                  |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Track             | AUDIT-EXISTING                                                                                                                                                                                         |
| Owner-side        | Either                                                                                                                                                                                                 |
| Mockability       | **YES** — mock features-onchain output (lending indices + staking rates fixed); mock MTDS (DEX prices + CEX perp marks fixed); real strategy-service code; real execution-service code with mock fills |
| Deps              | Strategy-service consolidation clean; archetype-audit (#1) deliverables for `carry_staked_basis` + `arbitrage_price_dispersion`                                                                        |
| Wrapper plan      | `plans/active/defi_may23_batch_backtest_remediation_2026_05_21.md` (TBD on pickup)                                                                                                                     |
| Wraps existing    | `master_to_live_defi_2026_05_23.md` Group D + E items, `phase5_features_streaming_carry_staked_basis_mvp_2026_05_19.md`                                                                                |
| Operator approval | n/a if pure mock-data audit; required if findings span >1 archetype family                                                                                                                             |
| Status            | `SEEDED`                                                                                                                                                                                               |

Scope: feed mock features + MTDS data through strategy-service onward for `carry_staked_basis` +
`arbitrage_price_dispersion`. Verify P&L, P&L attribution, rebalancing triggers, transfers + omnichain dynamics, venue
choice, execution-service path (directive shapes, validations, restrictions). Findings flow into existing Group D/E
plans. Graduation criterion before live: mock-green → real-backfill-data-green re-run.

### #4. DeFi May-23 archetypes — paper-mode e2e (mock-data feed)

| Field             | Value                                                                                                                      |
| ----------------- | -------------------------------------------------------------------------------------------------------------------------- |
| Track             | AUDIT-EXISTING                                                                                                             |
| Owner-side        | Either                                                                                                                     |
| Mockability       | **YES** — same mock layer as #3; paper-mode differs only in execution-service fill simulation + Firestore promote workflow |
| Deps              | #3 audit conclusions; promote workflow paths (`promote_workflow_may23_cli_path_2026_05_10.md` clean)                       |
| Wrapper plan      | `plans/active/defi_may23_paper_remediation_2026_05_21.md` (TBD)                                                            |
| Wraps existing    | `promote_workflow_may23_cli_path_2026_05_10.md`, `master_to_live_defi_2026_05_23.md` Group F                               |
| Operator approval | required — paper-mode touches Firestore + promote button surface                                                           |
| Status            | `SEEDED`                                                                                                                   |

Same scope as #3 but executed via paper-mode pipeline. Validates DART `ManualTradeGateDialog` shows correct directives
for first 3 trading days. Separate doc from #3 because failure modes differ (Firestore state, promote button auth, DART
rendering).

### #5. Machine-learning audit × 3 paths (sports / TradFi / CeFi) × 3 sub-questions

| Field             | Value                                                                                                                                        |
| ----------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| Track             | AUDIT-EXISTING                                                                                                                               |
| Owner-side        | Harsh (ML repo consolidation owner)                                                                                                          |
| Mockability       | **YES** — mock historical features data; real ml-training-service + ml-inference-service code; mock subscribers for inference-output routing |
| Deps              | ML repo consolidation (`ml_repo_consolidation_preaudit_2026_05_19.md`) clean; per-archetype feature schemas locked                           |
| Wrapper plan      | `plans/active/ml_three_path_audit_remediation_2026_05_21.md` (TBD)                                                                           |
| Wraps existing    | `ml_repo_consolidation_preaudit_2026_05_19.md` + any per-archetype ML plans in `plans/active/`                                               |
| Operator approval | required — touches deployment topology + subscriptions                                                                                       |
| Status            | `SEEDED`                                                                                                                                     |

3 paths × 3 sub-questions:

1. **Perf / optimization** — is training fast enough? Inference latency under SLO?
2. **Deployment topology** — training schedule vs inference triggers; config + subscriptions + hot-reloads; what
   triggers re-train (data-volume / time / feature-drift signal).
3. **Pipeline correctness** — does multi-stage walk-forward work? Bias check? Visualisations match expectation? Results
   shape-stable across re-runs?

All testable on mock data — does NOT block on backfill.

### #6. Execution-service backtest on mock × archetype-family (split per family)

| Field             | Value                                                                                                                                                    |
| ----------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Track             | AUDIT-EXISTING                                                                                                                                           |
| Owner-side        | Either (parallelisable across families)                                                                                                                  |
| Mockability       | **YES** — mock strategy-service directive output; real execution-service code; mock venue fills                                                          |
| Deps              | `strategy_execution_contract_remediation_2026_05_20.md` clean; per-family archetype audit (#1) findings                                                  |
| Wrapper plan      | One per family: `execution_backtest_<family>_remediation_2026_05_21.md` (carry_staked_basis / arbitrage_price_dispersion / sports / tradfi / prediction) |
| Wraps existing    | `strategy_execution_contract_remediation_2026_05_20.md`, `per_client_isolation_and_venue_fanout_topology_2026_05_20.md`                                  |
| Operator approval | n/a per family — wrapper-plan ack at create time                                                                                                         |
| Status            | `SEEDED`                                                                                                                                                 |

Verify: right execution instructions over right restrictions; validations enforced; venue constraints respected;
client-isolation invariant holds. Splits per archetype family so a slot can take one family at a time without 1M-context
blowout.

### #7. Risk audit

| Field             | Value                                                                                                 |
| ----------------- | ----------------------------------------------------------------------------------------------------- |
| Track             | AUDIT-EXISTING                                                                                        |
| Owner-side        | Ikenna (trading-judgment)                                                                             |
| Mockability       | Partial — risk-checks against mock position data; some risk-limit-config validation reads live config |
| Deps              | Archetype audit (#1) for risk-axis definition per archetype                                           |
| Wrapper plan      | `plans/active/risk_audit_remediation_2026_05_21.md` (TBD)                                             |
| Wraps existing    | Any plans referencing risk-limits / pre-trade checks / position-size caps                             |
| Operator approval | required — trading-judgment surface                                                                   |
| Status            | `SEEDED`                                                                                              |

Scope: pre-trade risk checks, position-size caps, exposure limits per client + per archetype, drawdown gates,
kill-switch wiring. Identifies risk axes not currently enforced + adds enforcement plan.

### #8. Liquidation alerting audit

| Field             | Value                                                                                           |
| ----------------- | ----------------------------------------------------------------------------------------------- |
| Track             | AUDIT-EXISTING + DESIGN-AND-BUILD                                                               |
| Owner-side        | Either                                                                                          |
| Mockability       | **YES** — mock health-factor / margin-ratio streams; real alerting-service code                 |
| Deps              | DeFi error classification (UAC `DefiErrorCode`) + Aave/Hyperliquid liquidation signals coverage |
| Wrapper plan      | `plans/active/liquidation_alerting_remediation_2026_05_21.md` (TBD)                             |
| Wraps existing    | Any active alerting-service plans                                                               |
| Operator approval | required — live alerting touches operator phone/Slack                                           |
| Status            | `SEEDED`                                                                                        |

Scope: liquidation-imminent detection (Aave/Compound health factor; perp margin ratio; recursive-loop unwind triggers).
Alert routing + escalation tiers. Mock-testable until live wallets funded.

### #9. Continuous-monitoring + 3am auto-recovery agent

| Field             | Value                                                                                           |
| ----------------- | ----------------------------------------------------------------------------------------------- |
| Track             | **DESIGN-AND-BUILD** (not an audit of existing — building new agent surface)                    |
| Owner-side        | Ikenna (orchestration + agent surface)                                                          |
| Mockability       | **YES** — mock data-staleness signals + service-down signals; real agent-orchestrator dispatch  |
| Deps              | agent-orchestrator prod stable; ScheduleWakeup / RemoteTrigger surfaces understood              |
| Wrapper plan      | `plans/active/auto_recovery_agent_remediation_2026_05_21.md` (TBD — new plan, no existing wrap) |
| Wraps existing    | None — net-new                                                                                  |
| Operator approval | required — auto-recovery agents take action without human in loop (kill-switch boundary)        |
| Status            | `SEEDED`                                                                                        |

Scope: when system goes down at 3am (data stale / service crash / VM zombie / consolidator stalled), an agent spins up
and tries to remediate before paging operator. Reuses agent-orchestrator + sub-agent rules. Closed-set authorized
remediation actions (restart service / re-launch VM / re-run consolidator / re-trigger backfill); anything outside the
closed set pages operator. Hard-stop list explicit (wallet keys / kill-switch / force-push / 1.0.0 graduation per
CLAUDE.md).

### #10. Manual-UI replication of every strategy archetype

| Field             | Value                                                                                        |
| ----------------- | -------------------------------------------------------------------------------------------- |
| Track             | **DESIGN-AND-BUILD**                                                                         |
| Owner-side        | Harsh (UI heavy)                                                                             |
| Mockability       | Partial — UI surface mock-testable; execution-service path real                              |
| Deps              | Archetype audit (#1) for canonical action set per archetype; execution-service contract (#6) |
| Wrapper plan      | `plans/active/manual_ui_archetype_replication_remediation_2026_05_21.md` (TBD)               |
| Wraps existing    | Any unified-trading-system-ui plans + execution-service manual-mode plans                    |
| Operator approval | required — manual-mode UI fires real venue actions                                           |
| Status            | `SEEDED`                                                                                     |

Scope: every strategy archetype replicable via manual UI actions (buy spot / sell perp / transfer / bridge / stake /
borrow / unwind-loop). Tests strategy-execution contract end-to-end without strategy-service in the loop. Test surface
for new venue/archetype before strategy-service wiring lands.

### #11. Credential + adapter inventory audit (no orphans, UAC SSOT alignment)

| Field             | Value                                                                    |
| ----------------- | ------------------------------------------------------------------------ |
| Track             | AUDIT-EXISTING                                                           |
| Owner-side        | Either                                                                   |
| Mockability       | n/a — audit reads code + UAC adapter manifest + Secret Manager inventory |
| Deps              | UAC adapter surface stable                                               |
| Wrapper plan      | `plans/active/adapter_inventory_remediation_2026_05_21.md` (TBD)         |
| Wraps existing    | `api_keys_wallets_accounts_readiness_2026_05_10.md`                      |
| Operator approval | required per orphan-removal decision (Kaiko etc.)                        |
| Status            | `SEEDED`                                                                 |

Scope: every adapter in the codebase has: (a) a stated purpose, (b) live API keys or operator-acked
`BLOCKED-CREDENTIALS` ping, (c) batch + testnet + live coverage where applicable, (d) UAC SSOT alignment + codex doc.
Orphans (Kaiko etc.) — remove or document why kept. Per CLAUDE.md `External Data Is Always Available` hard rule, no
adapter silently dropped without operator ack.

### #12. Multi-client flow audit (N clients, dynamic add/remove, no downtime)

| Field             | Value                                                                                                                                                                         |
| ----------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Track             | AUDIT-EXISTING + DESIGN-AND-BUILD                                                                                                                                             |
| Owner-side        | Ikenna (cross-cutting design)                                                                                                                                                 |
| Mockability       | **YES** — mock client config + per-client position state                                                                                                                      |
| Deps              | Per-client isolation pre-audit (`per_client_isolation_preaudit_2026_05_20.md`) clean; `cross_client_funds_isolation_retroactive_audit_2026_05_20.md` resolved                 |
| Wrapper plan      | `plans/active/multi_client_dynamic_lifecycle_remediation_2026_05_21.md` (TBD)                                                                                                 |
| Wraps existing    | `per_client_isolation_preaudit_2026_05_20.md`, `cross_client_funds_isolation_retroactive_audit_2026_05_20.md`, `per_client_isolation_and_venue_fanout_topology_2026_05_20.md` |
| Operator approval | required — touches Odum UK + Cayman entity boundary                                                                                                                           |
| Status            | `SEEDED`                                                                                                                                                                      |

Scope: how to add/remove a client at runtime without taking the system down. Config-reload paths per service. Isolation
invariants per CLAUDE.md § "Client funds isolation" hold across add/remove cycles. Operator demos: spin up test-client-N
→ run carry_staked_basis → tear down → verify no residue.

### #13. Reconciliation audit (code + paper/live test)

| Field             | Value                                                                     |
| ----------------- | ------------------------------------------------------------------------- |
| Track             | AUDIT-EXISTING                                                            |
| Owner-side        | Either                                                                    |
| Mockability       | **YES for code audit**; live test requires paper/live positions           |
| Deps              | batch-live-reconciliation-service surface stable; #4 paper-mode e2e green |
| Wrapper plan      | `plans/active/reconciliation_remediation_2026_05_21.md` (TBD)             |
| Wraps existing    | Any batch-live-reconciliation-service plans                               |
| Operator approval | required for live test (touches real positions)                           |
| Status            | `SEEDED`                                                                  |

Scope: automatic + manual reconciliation between our position state and venue position state. Diff surface (UI + alert).
Two layers: code-only audit (does the diff logic work on mock?) + paper/live test (does it match reality?).

### #14. Batch ↔ live symmetry audit (workspace-wide overarching theme)

| Field             | Value                                                                                        |
| ----------------- | -------------------------------------------------------------------------------------------- |
| Track             | AUDIT-EXISTING                                                                               |
| Owner-side        | Ikenna (cross-cutting)                                                                       |
| Mockability       | n/a — audit reads code (schemas / data_types / handlers) per service                         |
| Deps              | Per-service consolidation tail; mega-audit Phase B/C/D (data-pipeline correctness substrate) |
| Wrapper plan      | `plans/active/batch_live_symmetry_remediation_2026_05_21.md` (TBD)                           |
| Wraps existing    | `writegate_honest_coverage_endtoend_2026_05_06.md`, `mtds_mdps_master.md`                    |
| Operator approval | required for any service identified as batch-only with no live partner                       |
| Status            | `SEEDED`                                                                                     |

Scope: every service that has batch MUST have live for the same data_types + schemas. Translations / data sources can
differ; the surface MUST look and feel the same. Audits per-service: which data_types ship batch only? Why? Operator-ack
the gap or fix it. Codifies CLAUDE.md § "Batch = Live (CRITICAL)" as enforceable inventory.

## Cross-cutting tradeoffs (read before picking up any row)

### Mock-data parity risk

Rows #3, #4, #5, #6, #8, #9, #10, #12, #13 explicitly allow mock-data audits so backfill incompleteness doesn't block.
**This creates a parity risk**: a mock-validated audit can pass while live data breaks the system. Every wrapper plan
MUST declare a **graduation criterion** stating when mock-green must be re-validated against real-backfill-green.
Default graduation criterion: row archives only after both passes are green AND mega-audit Phase D is GREEN for affected
asset_groups.

### "Audit existing" vs "design and build"

Rows #9, #10, #12 are partly or fully `DESIGN-AND-BUILD` — they don't have a pre-existing surface to audit; they scope +
build new infrastructure. The AWS pool dispatch differs: design-and-build rows MUST land an architecture decision +
operator ack BEFORE remediation items are dispatched. Audit-existing rows can dispatch findings directly.

### Prioritization order (proposed; operator-tunable)

Tier 1 (May-23 critical path): #3, #4, #6 (carry_staked_basis + arbitrage_price_dispersion families), #11. Tier 2
(May-23 desirable, post-cutover acceptable): #7, #8, #14. Tier 3 (post-cutover): #5, #9, #10, #12, #13.

#1 + #2 are in-flight; not in the pickup pool.

### Foundation-completion-gate composition

This pool composes with CLAUDE.md § "Plans Run To Actual Completion" +
`codex/11-project-management/foundation-completion-gate-discipline.md`: no Tier-2 or Tier-3 row is dispatched while
Tier-1 wrapper plans have open P0 items on the same surface. Slot-1 main enforces this at row-pickup time.

### Issue-doc lifecycle (per CLAUDE.md § Issue-Doc Lifecycle Discipline)

Each row archives the moment its wrapper plan is created + ACKED — the wrapper plan becomes the single source of truth.
**Don't dual-track** by keeping the row "for visibility" once a wrapper plan exists. The whole pool doc archives when
all 14 rows are `DONE` or have explicit operator-acked `DEFERRED` lines.

## Acked / archive criterion

**Per-row archive**: row state transitions to `DONE` when its wrapper plan resolves + manifest evidence (live or paper
sample run) confirms remediation landed.

**Doc-level archive**: this issue doc archives to `plans/archive/` when (a) all 14 rows are `DONE` or operator-acked
`DEFERRED` with named successor plan, AND (b) any new audit candidates discovered during execution are landed in
follow-up issue docs (next-round pool).

## Next-round candidates (not seeded — surface for next pool doc if useful)

- Performance audit per service (latency / throughput SLOs).
- Cost audit (GCP + AWS + venue API fees per asset_group per archetype).
- Disaster-recovery audit (region failover; venue outage; custody-provider failover).
- Compliance audit (per-jurisdiction venue restrictions; KYC/AML touchpoints; audit-log surface).
- Audit-trail audit (every operator action + every agent action logged + queryable).

## Status update — 2026-05-22

Updated stale link: `strategy_archetype_logic_audit_2026_05_20.md` moved to `plans/audit/results/` — link fixed in Row
#1 Wraps existing column. Rows #1–#2 remain IN-FLIGHT. Rows #3–#14 remain SEEDED (no slots assigned yet). This file
stays active while the audit pool is running.
