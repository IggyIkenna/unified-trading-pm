---
title: Operator decisions resolved — 2026-05-08
type: operator-decisions-doc
status: active
created: 2026-05-08
author: ikenna (via Claude Code main orchestrator)
locked_by: live-defi-rollout
locked_since: 2026-05-08
deadline: 2026-05-23
---

# Operator decisions resolved — 2026-05-08

> **What this is.** A single durable record of all the open-Q resolutions Ikenna signed off on 2026-05-08 in one sweep.
> Every active plan with an `## Open questions` section was scanned; defaults / recommendations were either approved or
> overridden; the picks landed in this file AND were back-flipped into the per-plan Q&A entries (status ✅ RESOLVED).
> Use this file as the single-page reference when an agent encounters "I thought there was a question here but it's
> marked resolved" — every resolution is sourced here with the same wording as the per-plan flip.

## Summary table

| Plan                                                                 | Question                                 | Pick                                                                                                                                                           | Plan-side flip                                                         |
| -------------------------------------------------------------------- | ---------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| `master_to_live_defi_2026_05_23`                                     | Q&A 5 — manual-trade gating duration     | 3 days manual → 7 days automated                                                                                                                               | ✓                                                                      |
| `master_to_live_defi_2026_05_23`                                     | Q&A 6 — research-service repo            | Fold into deployment-api                                                                                                                                       | ✓                                                                      |
| `master_to_live_defi_2026_05_23`                                     | Q&A 7 — ML ladder targets                | DeFi rules-only; CeFi LIVE `ML_DIRECTIONAL_CONTINUOUS` ≥7d on real capital; Sports + TradFi + Predictions running on rep sample                                | ✓                                                                      |
| `cefi_master`                                                        | Which ML archetype family                | `ML_DIRECTIONAL_CONTINUOUS` on OKX + Binance + Bybit                                                                                                           | ✓                                                                      |
| `cefi_master`                                                        | Retraining cadence                       | Daily (UTC midnight + 30min)                                                                                                                                   | ✓                                                                      |
| `cefi_master`                                                        | Capital scale                            | $10k notional/venue ($30k total); 5% drawdown / 20% breach kill-switch; ARCHETYPE scope                                                                        | ✓                                                                      |
| `sports_master`                                                      | Sports ML archetype                      | Match-outcome (1X2)                                                                                                                                            | ✓                                                                      |
| `sports_master`                                                      | Leagues in scope                         | Top-5 European tier (EPL + LaLiga + Serie A + Bundesliga + Ligue 1)                                                                                            | ✓                                                                      |
| `sports_master`                                                      | Bookmaker scope                          | odds_api closing prices, top-5 bookmakers; in-play DEFERRED                                                                                                    | ✓                                                                      |
| `predictions_master`                                                 | Canonical question groups                | `BTC_UP_DOWN_HOURLY` + `SPX_UP_DOWN_DAILY` + `BTC_UP_DOWN_DAILY`                                                                                               | ✓                                                                      |
| `predictions_master`                                                 | CME event futures inventory              | OUT for May 23; track Polymarket SPX↔ES1 single arb cell as P1                                                                                                | ✓                                                                      |
| `predictions_master`                                                 | Opinion Trade integration                | OUT for May 23                                                                                                                                                 | ✓                                                                      |
| `tradfi_master`                                                      | C5 model shape stable                    | Yes — use existing C5 LightGBM hierarchical                                                                                                                    | ✓                                                                      |
| `tradfi_master`                                                      | Calendar feature inputs                  | Min FOMC + NFP + CPI; PCE + retail sales DEFERRED                                                                                                              | ✓                                                                      |
| `tradfi_master`                                                      | Bitcoin features granularity             | Hourly (Binance + OKX BTC perp `ohlcv_1h`)                                                                                                                     | ✓                                                                      |
| `tradfi_master`                                                      | Cross-venue ETF universe                 | US-listed only (SPY + IVV + VOO vs ES)                                                                                                                         | ✓                                                                      |
| `tradfi_master`                                                      | Backtest window                          | 2 years confirmed (rolling 2024-05-08 → 2026-05-07)                                                                                                            | ✓                                                                      |
| `defi_master`                                                        | Manual-trade gating duration             | 3d manual → 7d automated, stagger ≥1d across archetypes                                                                                                        | ✓                                                                      |
| `defi_master`                                                        | research-service repo                    | Fold into deployment-api                                                                                                                                       | ✓                                                                      |
| `defi_master`                                                        | `leveraged_funding_arb` strict P0?       | Strict P0 — both archetypes required                                                                                                                           | ✓                                                                      |
| `cross_cutting_may_23_2026.epic`                                     | Strategy catalogue completeness bar      | Archetype-level + venue-lookup-deferred for May 23                                                                                                             | ✓                                                                      |
| `cross_cutting_may_23_2026.epic`                                     | DART manual-trade lane scope             | Operator-only manual; broker-style DEFERRED                                                                                                                    | ✓                                                                      |
| `cross_cutting_may_23_2026.epic`                                     | AWS parity scope                         | DeFi-only by May 23, full-workspace post-cutover                                                                                                               | ✓                                                                      |
| `issues/cross_cutting_strategy_catalogue_already_shipped_2026_05_08` | Option A / B / C                         | **Option A — extend existing v2 SSOTs**                                                                                                                        | ✓                                                                      |
| `deploy_missing_auto_launch`                                         | IAM scope (Decision 1)                   | Option B + C combined                                                                                                                                          | ✓                                                                      |
| `deploy_missing_auto_launch`                                         | Audit-log shape (Decision 2)             | BigQuery primary + Cloud Logging mirror + GCS cold tier; sync-blocking write; 90d hot / 5y cold                                                                | ✓                                                                      |
| `deploy_missing_auto_launch`                                         | Rate-limit ceilings (Decision 3)         | 30/op/hr + 200/op/day + 100/proj/hr + 1 active per shard_key for 6h; Firestore counter state; alerts to `#uts-prod-alerts`                                     | ✓                                                                      |
| `alerting_service_live_rules`                                        | Q1 — UAC `kill_switch_scope` field owner | **Assigned to `alerting-phase2-publisher-hook` agent** (they have local code ready) — same agent ships UAC field + per-code seed + validator + tests in one PR | (in plan body — left to alerting agent to flip per Two-teammates rule) |
| `alerting_service_live_rules`                                        | PagerDuty service tier (Phase 4)         | **Shared `uts-prod-live-trading`** until cefi_ml goes live ≥7d; revisit per-archetype split post-cutover                                                       | ✓                                                                      |
| `alerting_service_live_rules`                                        | Telegram chat structure (Phase 4)        | **Single `uts-prod-alerts`** chat for May 23; severity routing via per-message ROUTING_TIER tag, not per-chat                                                  | ✓                                                                      |
| `alerting_service_live_rules`                                        | On-call rotation (Phase 4)               | **Solo Ikenna primary / Harsh backup** until cefi_ml live ≥7d; formal rotation post-cutover                                                                    | ✓                                                                      |

## Detail — alerting service Phase 4 + Q1

The alerting plan file `plans/active/alerting_service_live_rules_2026_05_07.md` is in another agent's dirty working tree
2026-05-08 14:00 UTC (per `_agent_pings.md` Q1 restoration). Per workspace HARD RULE "Two teammates × multiple parallel
agents — don't edit unfamiliar files," this doc records the operator picks for the alerting agent to back-flip into
their plan-of-record body when their next commit lands. The picks themselves are operator-binding immediately.

### Q1 — UAC `rules.py` `kill_switch_scope` field collision (4 reverted edits)

**Pick:** assign **`alerting-phase2-publisher-hook` agent** as the single owner for the UAC field landing. They have the
local code ready (alerting-service router + 5 integration tests written, just waiting for the UAC field). One agent, one
PR, no parallel-edit collision.

**Sequencing for the assigned agent:**

1. Take a fresh `git pull` on UAC repo `live-defi-rollout` immediately before editing `rules.py`.
2. Edit `unified-api-contracts/unified_api_contracts/canonical/crosscutting/alerting/rules.py` — add
   `kill_switch_scope: KillSwitchScope | None = None` field on `AlertRule`; add per-code seed in `LIVE_ALERT_RULES`
   (`LIQUIDATION_RISK=GLOBAL`, `PORTFOLIO_DRAWDOWN=GLOBAL`, `VENUE_DISCONNECT=VENUE`,
   `KILL_SWITCH_ML_MODEL_FAILURE=ARCHETYPE`); add validator `_validate_kill_switch_scope_matches_code_family`; new unit
   tests in `tests/internal/unit/test_alerting_taxonomy.py`.
3. Commit + push UAC repo immediately (no batching with other UAC work — minimise the parallel-edit-collision window
   that wiped 4 prior attempts).
4. Switch to alerting-service repo. The local code (`router.py` helpers + 5 integration tests) is ready — drop the
   defensive `getattr(rule, "kill_switch_scope", None)` for direct access; commit + push.
5. Flip Phase 2 + Phase 3 todos in `alerting_service_live_rules` plan-of-record (same logical unit — push the plan flip
   in PM repo with `docs(plans):` prefix referencing both code commits).

**If the parallel-edit-collision recurs** (4th attempt + failed): operator escalation path is to grep PM commits for who
else holds an open lock on UAC `rules.py` and ask them to rebase + drop their lock. NOT skip-hooks, NOT mass-reset.

### Phase 4 ops decisions

**PagerDuty service tier**: shared `uts-prod-live-trading`. Reasoning: cefi_ml + DeFi go live in the same 7-day window
per the manual-trade gating resolution. Per-archetype split adds rotation complexity for marginal call-routing benefit.
Revisit post-cutover when archetypes have differentiated incident profiles.

**Telegram chat structure**: single `uts-prod-alerts`. Reasoning: severity routing via per-message ROUTING_TIER tag
(P0=PagerDuty, P1=Telegram-mention, P2=Telegram-no-mention) is cleaner than per-severity chat. Operator-readable,
testable in one place. Per-severity chats deferred until alert volume justifies (>50 alerts/day routed to mute the
chat).

**On-call rotation**: Ikenna primary / Harsh backup until cefi_ml + DeFi cumulative ≥7d live without SEV1. Formal
rotation (e.g. weekly handoff via PagerDuty schedule) post-cutover when the pipeline is stable enough that "primary"
isn't always-on. Both operators receive PagerDuty pages for P0; Harsh receives Telegram-mention for P1.

## Detail — strategy catalogue Option A migration sequencing

Operator picked **Option A — extend existing v2 SSOTs** for `issues/cross_cutting_strategy_catalogue_already_shipped`.
The pickup steps for the next agent (whoever picks up `cross_cutting_may_23_deliverables` deliverables #1 + #2 + #3):

1. **Revert the parallel-SSOT files shipped in `uac@3591037`**:
   - Delete `unified_api_contracts/canonical/domain/client/__init__.py`
   - Delete `unified_api_contracts/canonical/domain/client/model.py`
   - Delete `unified_api_contracts/client.py` (root facade)
2. **Migrate the genuine-gap CapitalAllocation primitives** into existing `internal/architecture_v2/`:
   - Create `internal/architecture_v2/capital_allocation.py` (sibling to existing `client_registry.py`)
   - Move `CapitalAllocation` + `AllocationViolationError` + `validate_allocation_respect` + `is_within_allocation` +
     `CAPITAL_ALLOCATION_SEED` into the new module.
3. **Re-export through existing facade** `unified_api_contracts/strategy.py`:
   - Add the 5 symbols to the `__all__` list alongside existing `ClientDefinition` + `ClientRegistry` re-exports.
4. **Migrate the test file**:
   - `tests/unit/test_client_model.py` → `tests/unit/test_capital_allocation.py`
   - Update imports from `unified_api_contracts.client` → `unified_api_contracts.strategy`
   - Delete `Client` + `VenueAccount` test cases (those parallel SSOTs are reverted; the existing
     `internal/domain/strategy_service/client_registry.py` `ClientDefinition` + `internal/domain/account.py`
     `TradingAccount` + `AccountType` + `WalletRole` are the canonical SSOTs for those concepts).
   - Keep + adapt `CapitalAllocation` test cases.
5. **Seed `ArchetypeConfig`** for May-23 live archetypes:
   - Create `internal/architecture_v2/archetype_config.py`
   - `ArchetypeConfig` frozen dataclass with
     `{collateral, hedge_ratio, position_cap_usd, kill_switch_drawdown_pct, kill_switch_position_breach_pct}` fields.
   - Seed for: CARRY_STAKED_BASIS Solana, CARRY_STAKED_BASIS Ethereum, CARRY_BASIS_PERP × 6 perp venues
     (Bybit/Deribit/Binance/OKX/Hyperliquid/Aster), ML_DIRECTIONAL_CONTINUOUS × 3 venues (OKX/Binance/Bybit) — applying
     the master Q&A 7 capital-scale resolution ($10k/venue, 5% drawdown, 20% breach, ARCHETYPE scope).
   - Re-export through `strategy.py` facade.
6. **Update codex `strategy-summary.md`**: 8-family / 18-archetype baseline → 9-family / 53-archetype shape from current
   `enums.StrategyFamily` + `StrategyArchetype` registry. (2026-05-08: codex SSOT now reflects 53 archetypes per the
   2026-04-25 Phase 9 expansion — see strategy-summary.md "2026-05-08 drift correction" subsection.)
7. **Rewrite `cross_cutting_may_23_deliverables_2026_05_08` plan body** deliverables #1 + #2 + #3 todos to reflect
   extension-not-greenfield path. Use the issue doc § "Recommended decision (extends Option A above)" as the canonical
   shape.

## Composes with

- `master_to_live_defi_2026_05_23.md` — Q&A 5 + 6 + 7 are flipped in the master plan body alongside this doc.
- `cefi_master_2026_05_07.md` / `sports_master_2026_05_07.md` / `predictions_master_2026_05_07.md` /
  `tradfi_master_2026_05_07.md` / `defi_master_2026_05_07.md` / `cross_cutting_may_23_2026.epic.md` — each plan's
  `## Open questions` section is back-flipped to ✅ RESOLVED with the same picks recorded here.
- `deploy_missing_auto_launch_2026_05_07.md` § "Operator decision summary" — banner flipped to ✅ APPROVED.
- `issues/cross_cutting_strategy_catalogue_already_shipped_2026_05_08.md` — frontmatter
  `operator_decision: option_a_extend_v2`; `## Recommended decision` block flipped to ✅ RESOLVED.
- `_agent_pings.md` — 3 active pings (alerting Phase 2 publisher hook + deploy-missing Phase 0 facilitation +
  uac-strategy-catalogue Tab 6.A) cleared.
- `CLAUDE.md` "Capture discoveries as plan todos immediately" + "Findings Triage Discipline" — these resolutions unblock
  case-1-to-5 routing for ~25-35 AI-days of currently-blocked work.

## What changes for downstream agents

- **CeFi-ML (Tab 2 Ikenna design + Tab 2 Harsh wiring) is now P0 critical-path** — was P1 under "running on
  representative sample" default. `mlr-p4-strategy-calibrated-signals` + `mlr-p4-cost-aware-strategy` flip from P1 → P0.
  Live model registry + hot-reload + `model_version` tagging flip from P1 → P0.
- **DeFi paper-trade smoke must complete by 2026-05-15** to allow 7d automated cutover window before May 23 deadline.
  Stagger order = `carry_staked_basis` first (manual 2026-05-13 → 2026-05-15, automated 2026-05-16 → 2026-05-22),
  `leveraged_funding_arb` second (manual 2026-05-14 → 2026-05-16, automated 2026-05-17 → 2026-05-23).
- **CeFi-ML cutover staggered by ≥1 day from DeFi** to isolate kill-switch tests — manual 2026-05-15 → 2026-05-17,
  automated 2026-05-18 → 2026-05-23 (7d nominal but tighter window than DeFi).
- **Sports + Predictions + TradFi remain backtest-only** — no live deployment this cycle.
- **Deploy-Missing Phase 2 wiring is unblocked** — proceed to implementation per existing Phase 2 todos.
- **Strategy catalogue Tab 6.A is unblocked under Option A scope** — pickup per the migration sequencing above.
- **Alerting Q1 is unblocked** — assigned owner ships UAC field + per-code seed + validator + tests in one PR.

## Lifecycle

This doc lives in `plans/active/` until its picks are fully reflected in the per-plan checkbox flips. After all
referenced flips land (target ≤2026-05-09), this doc archives to `plans/archive/operator_decisions_2026_05_08.md`
preserving the audit trail.
