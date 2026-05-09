---
name: paper-vs-live-workflow-maturity
overview: Re-audit of paper-vs-live mode plumbing maturity + consistency across every strategy archetype, venue, instrument type, and strategy-instruction surface — plus the DART visualization toggle for batch/paper/live data, and the automated-vs-manual e2e setting per strategy. Conceptually pinned by operator: pricing has no real "paper" concept (just right data); mock-data = risk-simulation primitive (drop underlying, scenario tests); batch-vs-paper-vs-live differ only at the execution layer (strategy makes identical decisions, identical P&L, identical risk — only fill source changes).
type: question
status: plan-spawned
created: 2026-05-08
operator: ikenna
locked_by: live-defi-rollout
locked_since: 2026-05-08
spawned_plan: plans/active/master_to_live_defi_2026_05_23.md  # folded into Group F items 17/18/20/21/22 + Group G item 23 sub-items pvl-p17a..d / p18a..b / p20a..c / p21a / p22a / p23a..c
related_codex:
  # Both NEW — neither exists on disk today; will be created by the spawned plan.
  - unified-trading-pm/codex/04-architecture/operational-modes.md  # NEW
  - unified-trading-pm/codex/04-architecture/batch-equals-live-pipeline.md  # NEW
related_plans:
  - unified-trading-pm/plans/active/master_to_live_defi_2026_05_23.md  # fold-in target (Group F items 17/18 + 21)
  - unified-trading-pm/plans/active/arbitrage_price_dispersion_finalisation_2026_05_09.md  # owns the funding-arb archetype (was misnamed leveraged_funding_arb in earlier docs)
  - unified-trading-pm/plans/questions/promote_workflow_backtest_to_paper_to_live_2026_05_08.md
  - unified-trading-pm/plans/questions/risk_simulations_limits_alerting_2026_05_08.md
  - unified-trading-pm/plans/questions/mock_data_pipeline_benchmarking_2026_05_08.md
---

# Paper-vs-live workflow — maturity + consistency re-audit

## Settled (operator decisions 2026-05-09)

Ten plan-shape forks resolved. Question doc now drives a concrete plan extraction; this section is the at-a-glance summary, with detail folded into the relevant blocks below.

| # | Decision                              | Resolution                                                                                                                                                                                                                                                                                                  |
| - | ------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1 | Plan extraction path                  | **Fold into `master_to_live_defi_2026_05_23.md` Group F items 17 / 18** (and 21 for recon). Comprehensively spec the items via this doc's content; don't ship a parallel standalone plan.                                                                                                                  |
| 2 | Enum shape commitment                 | **Closest to existing code**: keep UAC `OperationalMode { LIVE, MANUAL, BACKTEST, PAPER }` as canonical (single 4-value enum already used by 6 consumer files across `execution-service` + `unified-trading-system-ui`). Add a derived helper `(target, trigger) ← Mode` for routing / recon / UI clarity. NO new `ExecutionTarget` / `ExecutionTrigger` enums; the helper is a pure function over the existing enum. Drop the "wrong shape" verdict in B1 below — it overcorrected. |
| 3 | Per-venue testnet policy              | **Simulate-first, testnet as fallback / upgrade where it exists.** Matching engine is the floor for every venue (CeFi perps, DeFi, sports, prediction). Where a venue exposes a testnet API + credentials, wire it as an upgrade path. Sports `PaperBettingAdapter` shape is the canonical simulator example. |
| 4 | Manual gate scope for May-23          | **Ships pre-cutover.** Manual execution must be triggerable via the unified-trading-system UI hooked up to backend. Block H is in scope.                                                                                                                                                                    |
| 5 | DART 3-way visualization scope        | **Ships pre-cutover, both views.** Side-by-side comparison view AND separate batch / paper / live views, both wired to real backend (not mock). Block G is in scope.                                                                                                                                       |
| 6 | `leveraged_funding_arb` status        | **Stale terminology.** No `LEVERAGED_FUNDING_ARB` symbol exists. The actual archetype is `StrategyArchetype.ARBITRAGE_PRICE_DISPERSION` with a `funding-rate-dispersion` variant. Owned by `plans/active/arbitrage_price_dispersion_finalisation_2026_05_09.md`. Cross-linked in `related_plans:` frontmatter. The May-23 lead pair is `carry_staked_basis` + the `ARBITRAGE_PRICE_DISPERSION:funding-rate-dispersion` variant — paper-runnable evidence run scopes against THAT archetype, not a fictional `LEVERAGED_FUNDING_ARB`. |
| 7 | `TestingStage` merge                  | **Merge.** `TestingStage.LIVE_TESTNET` collapses to `(target=TESTNET, trigger=AUTOMATED)` derived view. Don't keep TestingStage as a parallel progression-ladder enum; the (target, trigger) decomposition expresses the same information.                                                                  |
| 8 | Solana paper analogue                 | **Use the Solana equivalent (devnet / localnet / surfnet — operator-agnostic; pick the one with the fullest fork-state semantics for jitoSOL / mSOL / bSOL).** Same rule for any other non-EVM chain that doesn't have Tenderly: use that chain's native testnet/fork primitive. The plan needs a per-chain `paper_target_registry` in UAC: `chain → testnet/fork primitive`. |
| 9 | Instruction-layer mode-routing        | **UAC instruction envelope carries mode.** Lift `mode` (the `OperationalMode` enum value) into the UAC instruction schema. Enables A/B execution lanes, cleaner reconciliation, mode-tagged event audit trails. Boot-time injection at execution-service becomes a default-fallback when an instruction omits the field. |
| 10 | Mock-vs-paper boundary enforcement    | **No enforcement.** Operator-discipline only. The combinations `(paper_trade=true, CLOUD_MOCK_MODE=true)` and similar are legitimate — UI dev rendering against mock backend with paper-shaped data is a real use case. No hard refusal at execution-service boot. Block I drops the proposed boundary check. |

## Intent

The workspace SSOT is **batch = live = same code path, only fill source differs**. Layered on top, the operator wants
paper-trading as the bridge between batch (matching-engine simulated fills against historical replay) and live (real
venue + real custody + real capital): paper runs the same strategy + same instructions + same risk-and-exposure + same
position-balance + same alerting against **real-time live data** but with execution either (a) simulated by the same
matching engine that powers backtest, or (b) routed to a venue testnet / forked chain that gives realistic API
conditions without real money. **Strategy decisions, P&L attribution, risk checks are identical across all three modes —
the only difference is the fill source.**

The conceptual frame the operator wants pinned in the question:

- **Pricing data has no real "paper" concept.** Either the data is right (current live tick stream, accurate historical
  replay) or it isn't. There is no "paper price" that's distinct from a "live price." A strategy in batch reads
  historical ticks; in paper or live it reads the current Pub/Sub feed. Same upstream, same shape.
- **Mock data is a different concept entirely** — it's the primitive for **risk simulations** (drop the underlying 30%,
  spike funding to 100bps/8h, simulate a venue freeze, simulate a chain reorg, etc.) and for **dev-mode UI / test
  fixtures** (`CLOUD_MOCK_MODE=true`, `VITE_MOCK_API=true`, `MOCK_STATE_MODE=interactive`). Mock data is NOT the
  paper-trade surface; conflating them is an anti-pattern.
- **Batch / paper / live differ only at the execution layer.** Strategy-service emits the same instructions;
  risk-and-exposure runs the same checks; position-balance-monitor tracks the same way; alerting fires on the same
  rules; reconciliation expects the same shape. The seam is in execution-service: batch → matching-engine fills against
  historical, paper → matching-engine fills against live ticks OR venue-testnet / forked-chain fills, live → real venue
  / real chain fills with real capital.
- **Refined taxonomy (operator clarification 2026-05-08): the four modes are two orthogonal axes, not four peer enum
  values.**
  - **Execution-target axis**: `simulation` (matching engine produces fills) / `testnet` (real venue testnet or forked
    chain) / `live_venue` (real venue + real capital).
  - **Trigger axis**: `automated` (signals → instructions → fills fire end-to-end without operator intervention) /
    `manual` (operator manually triggers each execution; trades + endpoints are real, only the trigger differs).
  - The four named modes collapse to:

    | Named mode   | Execution-target                           | Trigger    | Notes                                                                                                                                                                                                                            |
    | ------------ | ------------------------------------------ | ---------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
    | **Backtest** | `simulation` only                          | automated  | Historical replay forces simulation — there's no testnet for past dates.                                                                                                                                                         |
    | **Paper**    | `simulation` OR `testnet`                  | automated  | Real-time data + simulated/testnet matching. Live data, no real money.                                                                                                                                                           |
    | **Live**     | `live_venue`                               | automated  | Real venue + real capital + automated execution.                                                                                                                                                                                 |
    | **Manual**   | `live_venue` (real trades, real endpoints) | **manual** | Real trades + real endpoints, just manual triggers for execution. May involve redundancy / different deployment / different account per operator config — that's a deployment-level choice, not a system-level mode distinction. |

  - Implication: **strategy / risk / P&L / position-balance / alerting / instructions are identical across all four
    cells.** The execution-target axis selects fill source; the trigger axis selects who pulls the trigger. Anything
    else branching on these axes is an anti-pattern.

This question doc is a **re-audit of how mature and consistent that frame is in code today**, across every strategy
archetype × venue × instrument type × strategy-instruction surface, AND of how the DART section in the
unified-trading-system UI should let the operator toggle between batch / paper / live data + e2e-automated / manual
modes per strategy.

It is **distinct from `promote_workflow_backtest_to_paper_to_live_2026_05_08.md`**, which audits the _lifecycle state
machine_ (button click → candidate → paper-deploy → live-deploy). This doc audits the _underlying mode plumbing_ — the
prerequisite the promote workflow assumes exists. It is also **distinct from
`risk_simulations_limits_alerting_2026_05_08.md`**, which owns the mock-data-as-stress-test surface, and from
`mock_data_pipeline_benchmarking_2026_05_08.md`, which owns synthetic-data benchmarking. Cross-referenced;
non-overlapping.

The 2026-05-23 cutover requires `carry_staked_basis` + `leveraged_funding_arb` to run on a real wallet for ≥7 continuous
days. That implies prior paper-mode runs on the same archetypes against real DeFi venue testnets / Tenderly forks; both
archetypes have to be paper-runnable end-to-end with strategy / risk / position / alerting / reconciliation all wired
identically to the live shape. Audit must establish: are they?

## Question

### Block A — Conceptual model: pricing, mock, paper, live

A1. Is the conceptual model above (pricing-has-no-paper, mock=risk-sim-primitive,
batch-paper-live-differ-only-at-execution, **manual is the orthogonal trigger axis not a peer mode**) **codified in a
codex SSOT today**, or only in CLAUDE.md prose + operator memory? If not codified, what's the right doc location —
`codex/04-architecture/operational-modes.md`, `codex/04-architecture/batch-equals-live-pipeline.md`, or a new
`codex/04-architecture/paper-vs-live-execution-seam.md`?

A2. The "execution layer is the only seam that differs" claim — is it actually true in code? Are there sneaky
non-execution branches on `mode == "paper"` anywhere (data-loader picking different bucket, feature compute applying
different lookahead bound, risk-check loosening thresholds, alerting suppressing events)? Per workspace SSOT this must
be NO; the audit has to verify NO.

A3. Mock-data-vs-paper boundary — is there a code-level enforcement preventing the two from being conflated? E.g. an
assertion in execution-service that `paper_mode=True ⇒ CLOUD_MOCK_MODE=False` (paper is real-data-real-API; not
mock-data-real-API)? Or could an operator misconfigure `paper + CLOUD_MOCK_MODE=true` and silently get a mock-data paper
run?

A4. The three-way recon — batch vs paper vs live — what's the closed expectation? Per master plan F18, batch-vs-live
recon is a service-readiness item. Is **paper-vs-live** also a recon target (we should expect paper P&L and live P&L to
match within slippage/commission tolerance over the same window)? Is **batch-vs-paper** a recon target (paper should
match batch over a replay window)? Or is the recon just batch-vs-live and paper sits orthogonal?

A5. **Two-axis taxonomy verification.** Per the refined model, the closed-set decomposition is:

- `ExecutionTarget { SIMULATION, TESTNET, LIVE_VENUE }` — selects fill source.
- `ExecutionTrigger { AUTOMATED, MANUAL }` — selects who pulls the trigger.
- Allowed combinations (closed set of 4): `(SIMULATION, AUTOMATED) = backtest`,
  `(SIMULATION | TESTNET, AUTOMATED) = paper`, `(LIVE_VENUE, AUTOMATED) = live`, `(LIVE_VENUE, MANUAL) = manual`.
- Disallowed combinations: `(SIMULATION, MANUAL)` (manual against simulation has no operational value);
  `(TESTNET, MANUAL)` (edge case — useful for manual-trader UX rehearsal but probably not a first-class mode).
- Question: should the codified enum shape BE these two axes, OR a single `Mode { BACKTEST, PAPER, LIVE, MANUAL }` enum
  with derived axes? Two axes are more compositional (clean for routing, recon, UI toggles); single enum is more
  familiar (matches how operators talk about it). Per workspace SSOT discipline, prefer two-axis with a
  `derived_named_mode` helper for human-facing labels.

A6. **Manual-mode deployment shape.** Operator clarification: "manual is real trades and endpoints, just manual triggers
— might be redundancy or different deployment or even account but that's up to user config for manual deployment."
Implication: manual mode does NOT mandate a separate VM / Cloud Run service / account; it's a per-strategy
`ExecutionTrigger.MANUAL` flag on the same execution stack. Operators MAY choose to run manual on a parallel deployment
(for redundancy / blast-radius isolation / accounting separation) but the system doesn't require it. Question: is there
a config schema in UAC / config-as-code for "this strategy runs manual on deployment X with account Y, automated on
deployment Z with account W"? Or is manual-deployment-routing operator-script territory today?

### Block B — UAC operating-mode SSOT reconciliation

B1. UAC `internal/modes.py:69-96` declares THREE enums today:

- `RuntimeMode { LIVE, BATCH }` — service execution transport (streaming vs batch jobs)
- `OperationalMode { LIVE, MANUAL, BACKTEST, PAPER }` — per-service instruction mode
- `TestingStage { MOCK, HISTORICAL, LIVE_MOCK, LIVE_TESTNET, STAGING, LIVE_REAL }` — strategy progression gates

**Verdict per operator decision 2026-05-09 (Settled #2 + #7)**: keep `OperationalMode { LIVE, MANUAL, BACKTEST, PAPER }` as canonical — closest-to-existing-code wins. Single 4-value enum already in use by `execution-service` (cli/handlers + engine/transfers/factory + engine/transfers/mock_adapter + tests/unit/test_operational_mode_validation) and `unified-trading-system-ui` (context/internal-contracts/schemas/modes). 6 consumer files; rewriting them for a fresh two-enum schema is more churn than the conceptual cleanliness is worth.

**The two-axis decomposition (A5) is preserved as a derived view**, additive to UAC — not a replacement:

```python
# UAC: unified_api_contracts/internal/modes.py — additive (no enum changes to OperationalMode)
class ExecutionTarget(StrEnum):
    SIMULATION = "simulation"
    TESTNET = "testnet"
    LIVE_VENUE = "live_venue"

class ExecutionTrigger(StrEnum):
    AUTOMATED = "automated"
    MANUAL = "manual"

def decompose(mode: OperationalMode) -> tuple[ExecutionTarget, ExecutionTrigger]:
    return {
        OperationalMode.BACKTEST: (ExecutionTarget.SIMULATION, ExecutionTrigger.AUTOMATED),
        # PAPER spans (SIMULATION | TESTNET) — derived helper returns SIMULATION as default;
        # caller queries `paper_target_registry[venue]` for the actual upgrade path per Settled #3.
        OperationalMode.PAPER:    (ExecutionTarget.SIMULATION, ExecutionTrigger.AUTOMATED),
        OperationalMode.LIVE:     (ExecutionTarget.LIVE_VENUE, ExecutionTrigger.AUTOMATED),
        OperationalMode.MANUAL:   (ExecutionTarget.LIVE_VENUE, ExecutionTrigger.MANUAL),
    }[mode]
```

Routing / recon / UI code uses `decompose(mode)` to switch on `target` or `trigger` independently; the on-disk + on-wire surface stays the single `OperationalMode` enum. **Anti-patterns A + B (execution-service `paper_trade: bool` and sports `_PAPER_VENUE_KEYS` string-set) still get deleted** — they're competing surfaces for the same single enum; the consolidation is independent of the two-axis-vs-single-enum question.

**`TestingStage` decision (Settled #7)**: merge. `TestingStage.LIVE_TESTNET` collapses to `(target=TESTNET, trigger=AUTOMATED)` derived view; deprecate `TestingStage` as a separate enum. Other `TestingStage` values (MOCK / HISTORICAL / LIVE_MOCK / STAGING / LIVE_REAL) are progression-ladder labels that get re-expressed via `OperationalMode` + a separate `progression_stage` field if still needed (likely UI-only).

**`RuntimeMode { LIVE, BATCH }`** stays as service-transport orthogonal axis — it composes with `OperationalMode` (a `RuntimeMode.LIVE` streaming service can run `OperationalMode.PAPER` against a Tenderly fork). Confirm in plan body that no consumer conflates the two.

B2. **Anti-pattern detected**: execution-service `service_config.py` declares a separate `paper_trade: bool` field
(alias `PAPER_TRADE | DEFI_PAPER_TRADE`). This is a competing surface to `OperationalMode.PAPER`. Sports has yet another
shape: `sports_execution/routing.py:16-25` declares `_PAPER_VENUE_KEYS = ("paper", "betfair", "matchbook")` — string-set
rather than enum. **Three competing surfaces for one concept.** Resolution: collapse to UAC `OperationalMode`
everywhere, delete the bool, delete the string-set, fail-loud on the deprecated paths. Question: is there a successor
plan that does this, or does this question doc spawn it?

B3. **Settled (per A5 + B1 verdict)**: automated-vs-manual is the orthogonal trigger axis, NOT a peer of paper/live.
Closed-set: `ExecutionTrigger { AUTOMATED, MANUAL }`. Sub-shapes within manual (per-trade-confirm vs arm-only-then-fire
vs full-manual-trader-ux) are operator-config-time choices, not separate enum values — the manual flag selects "operator
pulls trigger"; HOW the operator pulls (single-click confirm, multi-step arm-then-fire, full DART manual-trader cockpit)
is per-strategy operator config. **Open question for the spawned plan**: codify the per-strategy manual-config schema
(UAC type for `ManualExecutionConfig { confirm_threshold, arm_first, dart_surface_path, ... }`).

B4. Where is the SSOT for "what mode is service X running in right now"? execution-service reads from its boot config;
strategy-service has a `description="Execution mode (backtest, paper, live)"` config field but no branches on it (good —
SSOT holds); risk-and-exposure / position-balance-monitor / alerting — do they each carry a mode field, or is mode
propagated via the strategy-instruction envelope? UAC instruction protocol must be the carrier; the audit has to verify.

### Block C — Per-archetype paper-trade maturity matrix

C1. The May-23 lead archetypes:

- `carry_staked_basis` — `strategy-service/strategy_service/engine/strategies/v2/carry_and_yield/staked_basis.py` exists
  with tests. **Paper-mode end-to-end run evidence: not found.** Has the archetype been run paper-mode against real DeFi
  venues + real LST yields + Tenderly fork for hedge legs, or only batch-mode replay? If only batch, what's the gap to
  paper-runnable?
- `leveraged_funding_arb` — **no archetype code found in audit grep.** Is it under a different filename (funding-arb is
  a common name), or is it not implemented yet? Either way, paper-mode readiness is an open gap.

C2. Other archetypes in the catalogue (`strategy-service/strategy_service/portfolio_allocator/archetypes.py` references
the catalog) — what's the per-archetype paper-runnable status? A 4-state taxonomy:

- **Paper-runnable** — has run paper-mode end-to-end against real venues + real data, P&L attribution clean, recon
  green.
- **Paper-shippable** — code exists + tests exist + matching engine wired; never executed paper end-to-end on real
  infra.
- **Backtest-only** — only batch-mode evidence; paper plumbing not wired.
- **Stub / placeholder** — archetype name exists in catalogue but no engine code.

Need the matrix populated per archetype.

C3. Cross-archetype consistency — when a new archetype lands, what are the **paper-trade readiness gates** it must clear
before being eligible for `OperationalMode.PAPER`? Is this codified anywhere (UAC enum, codex SSOT, archetype-checklist
plan)? Per workspace SSOT _"every shippable thing has a closed set of gates"_ — the gate set should exist.

C4. Archetype-specific paper-trade differences — e.g. `carry_staked_basis` paper-mode needs Tenderly fork for the DeFi
swap leg + perp venue testnet for the hedge leg; `leveraged_funding_arb` paper-mode needs perp venue testnet for both
legs. Cross-venue-cross-chain-cross-asset-group paper composition — is the orchestration codified, or assembled ad-hoc
per archetype?

### Block D — Per-venue paper / testnet support

D1. **Biggest gap surfaced by audit**: 5 of 6 perp venues have no testnet routing in execution-service: **Bybit,
Binance, OKX, Hyperliquid, Aster — no testnet endpoint constructor found**. Only Deribit has a `testnet` reference in
`venues/deribit.py` (not yet a callable testnet-mode constructor per audit). For the May-23 cutover involving the hedge
leg of `carry_staked_basis` + both legs of `leveraged_funding_arb`, paper-mode is blocked on this. Question: which
venues actually offer testnets we can use (vs which we need to mock with the matching engine), and what's the wire-up
plan?

D2. DeFi paper analogue is **Tenderly fork** per `execution-service/execution_service/providers/base.py:~45`. Is
Tenderly fork available for every chain we trade (Ethereum, Arbitrum, Base, Polygon, Solana)? Solana is on a non-EVM
chain; Tenderly is EVM-only — what's the Solana paper-trade story (devnet? localnet? simulation?)? `carry_staked_basis`
has a Solana leg via Pyth + jitoSOL/mSOL/bSOL — must be addressable.

D3. Sports has the most mature paper surface:
`execution-service/execution_service/sports_execution/adapters/paper/paper_betting.py` has full `PaperBettingAdapter`
with bet placement / cancellation / settlement simulation. Question: is the sports pattern **the canonical shape we lift
to CeFi/DeFi**, or is the sports shape sports-specific because sports venues don't offer testnets so simulation is the
only option? Decide the per-venue policy: testnet-where-available vs always-simulate vs hybrid.

D4. Per-venue credential boundaries — paper-trade venue testnets need their own credential set (testnet API keys,
testnet wallet PKs, testnet Tenderly tokens) — distinct from live keys. Is there a `credentials/paper/` namespace in
Secret Manager, or is the boundary blurred? See cross-link to `api_keys_wallets_accounts_readiness_2026_05_08.md`.

D5. Paper-mode rate-limit / cost discipline — Tenderly forks burn fork-credits; venue testnets have rate limits;
matching-engine simulation has compute cost. Is the per-venue paper budget tracked? Could a runaway paper-trade VM
exhaust Tenderly credits or get a venue testnet blocked?

### Block E — Per-instrument-type paper-trade maturity

E1. Instrument-type matrix: spot / perp / options / futures / LST / liquidity-pool / lending-position /
prediction-market / sports-market. For each, what does paper-mode look like?

- **Spot (CeFi)** — venue testnet OR matching engine; question: do testnets exist for the 6 perp venues' spot products,
  or only their perp products?
- **Perp (CeFi)** — same as above; testnet routing the open gap (D1).
- **Options (CeFi)** — Deribit has options; testnet status?
- **Futures (TradFi)** — CME via Databento for batch; what's paper for TradFi? Does CME offer a testnet, or is paper
  purely matching-engine simulation against historical?
- **LST (DeFi)** — Tenderly fork covers this on EVM; Solana LSTs (jitoSOL etc.) need a non-Tenderly answer.
- **Liquidity-pool / Lending (DeFi)** — Tenderly fork + Aave/Uniswap forked contracts; flash-loan receiver deployed per
  chain; status per chain?
- **Prediction markets (Polymarket / Kalshi)** — do these venues offer testnets / sandbox markets? If not, paper =
  matching-engine simulation against the live market_id stream?
- **Sports markets (Betfair / Matchbook / others)** — `PaperBettingAdapter` covers; venue testnets exist?

E2. Cross-instrument-type composability — `carry_staked_basis` is multi-asset_group (DeFi LST + CeFi/DeFi perp hedge).
Paper-mode for the WHOLE archetype requires every leg paper-runnable simultaneously, in coordinated time. Is this
orchestrated centrally (one VM, one matching engine spanning all legs), or per-leg (each venue runs its own paper, the
strategy aggregates)?

### Block F — Strategy instruction layer mode-awareness

F1. Per audit, `execution-service/execution_service/strategy_instructions/gcs.py` shows the instruction protocol with
**no mode field in the instruction schema itself**. Mode is injected at execution-service boot. Question: should the
instruction carry the mode, OR is boot-time injection the right separation of concerns? Trade-offs:

- Instruction-carries-mode: one instruction can route to different execution lanes (batch replay + paper-live +
  live-prod simultaneously for A/B compare). Simpler reconciliation. More schema-complex.
- Boot-time injection: instruction is mode-agnostic; strategy emits one shape; execution-service config decides routing.
  Cleaner schema. Harder to A/B.

F2. The instruction schema is in UAC — does it have a `mode` field, an `execution_lane` field, a
`target_venue_or_simulator` field, or none? The promote workflow in
`promote_workflow_backtest_to_paper_to_live_2026_05_08.md` Block C5 needs the candidate manifest to capture the
execution lane; the instruction schema is upstream of that.

F3. Strategy emits identical instructions across modes — verified by audit (no `mode == 'paper'` branches in
strategy-service). But: does strategy emit the **same volume** of instructions in paper as in live? E.g. if paper venue
testnet has 10× the latency vs live, strategy might emit instructions faster than execution can fill — does the
strategy-instruction queue handle this, or do paper-mode runs silently drop instructions?

### Block G — DART visualization toggle (batch / paper / live)

G1. Per audit, DART surfaces in the UI today:

- `unified-trading-system-ui/components/shell/dart-scope-bar.tsx` — multi-axis filter cockpit (asset_group,
  instrument_type, strategy_family, archetype, share_class, venue/protocol). Has an "Execution Stream" toggle: paper vs
  live (live locked behind `execution-full` entitlement, confirms via `LiveConfirmDialog`).
- `unified-trading-system-ui/components/trading/execution-mode-toggle.tsx` — Live ↔ Batch toggle (with Pub/Sub vs GCS
  data-source badges). Mock data only today.
- `unified-trading-system-ui/app/(platform)/dashboard/page.tsx` — DART routes (`dart-terminal`, `dart-research`).

**What's missing**: a unified batch / paper / live three-way toggle on a single strategy, with side-by-side P&L curves /
fills / events / position trajectories. The two existing toggles are sequential (pick a mode, view that mode) — not
comparative.

G2. The user requirement: when looking at any strategy/archetype run in DART, the operator should be able to toggle
visualization between batch (historical replay), paper (real-time matching-engine simulated fills against
testnet/forked-chain), and live (real venue, real capital) — **side-by-side or via a 3-tab/dropdown surface**.
Per-strategy event stream + fills blotter + P&L curve + position trajectory + risk metrics. Question: what's the
cleanest UI surface — a triple-pane comparison view, a tab interface with shared filters, a single canvas with three
colored line series for P&L?

G3. Data plumbing for the three-way DART view — each lane reads from a different source today:

- Batch: parquet replay results in GCS (results/strategies/<archetype>/<run_id>.parquet or similar)
- Paper: live event stream `gs://{pid}-events/events/strategy-paper/...` + paper-mode fill ledger + paper-mode
  position-balance state
- Live: live event stream `gs://{pid}-events/events/strategy-live/...` + live fill ledger + live position-balance state

Is the data-loading abstracted behind a single API the UI calls (`GET /strategy/{id}/runs?mode=batch|paper|live`), or
does the UI have to talk to three different endpoints? Per workspace pattern, this should be a single API surface.

G4. Manual-trade gate — per audit, `LiveConfirmDialog` exists but is mode-toggle confirmation (operator confirms
switching to live mode), NOT per-trade approval. Master plan G23's "DART manual-trade gate" wants per-trade approval
(each order shows pre-trade risk preview + operator clicks approve/deny). This is **aspirational, not implemented**. Is
it in scope for May-23 or a follow-up?

G5. Automated-vs-manual per-strategy toggle — per audit, no UI setting found. The
`Engagement mode (monitor / replicate)` toggle in `dart-scope-bar.tsx:545-550` is surface-level filter, not
execution-gate. Where should this setting live, persist, and read at execution time? Trade-offs:

- UI store + Firestore: low-latency UI, adds Firestore as authoritative state.
- UAC config-as-code: clean SSOT, slow-iteration (commit + redeploy to flip).
- execution-service runtime-config + ApiKeyReloader-style hot-reload: middle ground, current pattern for credentials.

### Block H — `ExecutionTrigger.MANUAL` plumbing

Per A5 + B3, manual is the orthogonal trigger axis — NOT a peer execution-target. Manual = real venue + real endpoints +
manual triggers. Operator config decides where in the e2e flow the manual gate sits, and whether manual runs on the same
deployment as automated or on a redundant / different-account / different-VM deployment.

H1. **"Automated end-to-end" baseline shape**: signal generated → strategy emits instruction → risk-and-exposure
pre-flight checks → position-balance state-update → execution-service routes to (matching engine | testnet venue | real
venue) → fill received → position-balance updates → alerting watches → reconciliation runs. **For
`ExecutionTrigger.MANUAL`, where is the manual gate injected?** Three plausible insertion points; the plan needs a
closed-set:

- **Pre-execution gate** (most useful): instructions reach execution-service, but execution-service holds them in a
  manual-pending queue; operator approves each via DART → execution proceeds to live venue. Strategy / risk /
  position-balance unchanged.
- **Pre-strategy gate** (rarely useful): signals reach strategy but instruction emission requires operator approval.
  Inverts the strategy SSOT (strategy now branches on trigger axis). Anti-pattern.
- **Post-fill gate** (audit-only, not a gate): fills happen, operator acknowledges; not actually a gate, just a journal
  entry. Useful but distinct from manual-mode.

Settle on **pre-execution gate** as the canonical manual injection point (matches operator framing "manual triggers for
the execution"). Other points are out-of-scope.

H2. **Manual-trigger contract** — when an instruction lands in the manual-pending queue, what happens? Closed-set:

- Operator approves (single-click | arm-then-fire | DART-form-submit) → execution proceeds.
- Operator denies → execution rejected, event emitted (`MANUAL_REJECTED`), strategy informed (does strategy retry, mark
  instruction stale, or treat as fill-failure? per workspace pattern, treat as fill-failure with structured event).
- Operator timeout (instruction sits unconfirmed for N minutes) → auto-policy: cancel-with-audit |
  escalate-to-secondary-operator | hold-indefinitely. Per-strategy config.
- Operator offline (no operator session active) → auto-policy: hold | cancel | fail-loud. Per-strategy + per-deployment
  config.

H3. **Mixed mode within a portfolio** — can `carry_staked_basis` run automated-live while `leveraged_funding_arb` runs
manual-live simultaneously? Per-strategy independence is the design intent; verify the plumbing supports it. The
`ExecutionTrigger` field is per-strategy, not per-deployment.

H4. **Runtime trigger change** — operator flips a strategy from manual-live to automated-live at 14:30 UTC. In-flight
manual-pending instructions: (a) auto-approved, (b) preserved as manual for legacy / cancellation, (c) cancelled.
Closed-set policy needed; default proposal: **(b) preserved** — flipping the trigger forward doesn't retroactively
approve unconfirmed work; operator must explicitly resolve the pending queue before the trigger flip takes full effect.

H5. **Manual-mode deployment-redundancy options** (per operator clarification): operator may choose to run manual-mode
on a parallel deployment with a different account / VM / Cloud Run service for blast-radius isolation, accounting
separation, or operational redundancy. The system shouldn't FORCE this; per-strategy config decides:

- `manual_deployment.shares_with_automated: bool` — same VM / account / deployment as automated counterpart.
- `manual_deployment.account_id: Optional[str]` — override account if isolated.
- `manual_deployment.vm_pool_tag: Optional[str]` — override deployment if isolated.
- Default: shares with automated. Operator opts into isolation explicitly.

H6. **Manual UX surfaces** — DART per Block G is the canonical operator surface. But is there a fallback channel
(Telegram approval, email-with-confirm-link, Slack interactive button) for when DART is unavailable? Per-strategy:
`manual_approval_channels: list[ApprovalChannel]` with priority ordering. Closed-set policy + UAC enum needed.

### Block I — Mock data vs paper trading boundary enforcement

I1. The conceptual frame says **mock-data is for risk simulations + dev fixtures, not for paper-trading**. Is this
enforced anywhere in code? E.g. execution-service refuses to start with `paper_trade=true` AND `CLOUD_MOCK_MODE=true`?
Or is the boundary purely operator-discipline?

I2. Risk simulations as a separate surface — per `risk_simulations_limits_alerting_2026_05_08.md`, risk simulations are
scenario tests (drop underlying 30%, etc.). These run against mock-data-with-perturbations. Does the risk-simulation
service share code with paper-trading service, or are they fully separate? They probably should be fully separate
(mock-data path vs real-data-paper-execution path), but verify.

I3. UI mock-mode (`VITE_MOCK_API=true`, `MOCK_STATE_MODE=interactive`) is a third concept — UI dev fixtures so widgets
render without backend. It is NOT paper-mode AND NOT risk-sim-mode. The DART scope-bar today is mock-mode-only per audit
(`EXECUTION_MODES` dict, hardcoded fixtures). When does DART get wired to real paper data + real live data + real batch
data? Cross-link to deployment-api work-stream A.

### Block J — Three-way reconciliation: batch ↔ paper ↔ live

J1. `batch-live-reconciliation-service/` exists with `stages/stage3_execution_recon.py`. Is there an analogous
`paper-live-reconciliation` and `batch-paper-reconciliation`? Or does batch-live-recon generalize to a 3-way recon by
iterating over mode-pairs?

J2. Recon tolerance per mode-pair — batch vs live should match within slippage/commission tolerance over a window; paper
vs live should match more tightly (same data, similar API conditions); batch vs paper should match within
matching-engine fidelity tolerance. Are the tolerance thresholds codified per-pair?

J3. Recon failure routing — batch-live-recon failure today does what? Alerting fires? Auto-pauses live? Auto-demotes to
paper? Per master plan G23 + alerting service, this should be a closed-set policy.

J4. **Lookahead-bias verification across modes** — per workspace SSOT, batch must respect `LookaheadBiasError`
(input.available_at <= target_ts - horizon). Paper has no such issue (it's running in real-time so available_at by
definition <= now). Live has no such issue. But: when batch and paper are recon'd, the batch run must have used the SAME
`available_at` timestamps the live pipeline would have produced — otherwise batch is cheating via faster-than-live data
and the recon is invalid. Is this enforced?

## What "answered" looks like

- A canonical plan exists in `plans/active/` (or fold-into existing master) that covers: UAC mode-enum collapse to
  single SSOT, per-archetype paper-runnable matrix population, per-venue testnet wire-up plan (especially the 5 perp
  venue gap), per-instrument-type paper support, instruction-protocol mode-routing decision, DART 3-way visualization
  toggle, automated-vs-manual per-strategy plumbing, mock-vs-paper boundary enforcement, and 3-way recon shape.
- Codex SSOT(s) describe: the conceptual model (pricing-no-paper, mock-vs-paper, batch-paper-live-execution-only-seam)
  at `codex/04-architecture/paper-vs-live-execution-seam.md` (NEW); per-archetype paper-runnable matrix at
  `codex/12-strategies/archetype-paper-readiness.md` (NEW); per-venue paper/testnet policy at
  `codex/05-infrastructure/per-venue-paper-policy.md` (NEW); DART visualization shape at
  `codex/14-customer-journeys/dart-mode-toggle.md` (NEW or UPDATE).
- A real end-to-end paper-mode run has shipped for both `carry_staked_basis` and `leveraged_funding_arb` against real
  DeFi venues + real perp testnet (or matching engine) + real strategy + real risk + real position-balance + real
  alerting + recon green for ≥3 continuous days. Evidence in event stream + manifest.
- Master plan service-readiness checklist Group F items 17 (paper-trade smoke green) + 18 (batch-vs-live recon) updated
  to reflect actual completion (not code-shipped); new item or annotation captures "paper-vs-live recon green" if added.
- DART surface in `unified-trading-system-ui` renders the 3-way toggle on at least one archetype with real data,
  side-by-side or 3-tab; `LiveConfirmDialog` extended (or new `ManualTradeGateDialog` added) for per-trade approval if
  scope.
- `OperationalMode` (or its successor enum) is the ONLY mode SSOT — `paper_trade: bool` deleted from execution-service
  `service_config.py`, `_PAPER_VENUE_KEYS` deleted from sports routing.
- Reconciliation service handles 3-way recon (batch-paper-live) with codified per-pair tolerances + closed-set
  failure-routing policy.

## Audit findings (pre-populated 2026-05-08)

### A — Conceptual model

- **Code state**: CLAUDE.md Master Plan section + § "Batch = Live: Unified Pipeline Architecture" articulate the SSOT in
  prose. `unified-api-contracts/unified_api_contracts/internal/modes.py:69-96` declares the enum surface but does not
  pin the conceptual model (pricing-no-paper, mock-vs-paper distinction).
- **Codex state**: No dedicated codex doc found for the operational-mode conceptual model. Closest neighbors:
  `codex/04-architecture/operational-modes.md` (referenced; verify exists) and
  `codex/04-architecture/batch-equals-live-pipeline.md` (referenced; verify exists).
- **Gap**: Need a `codex/04-architecture/paper-vs-live-execution-seam.md` SSOT that pins (a) execution layer is the only
  seam, (b) pricing has no paper concept, (c) mock-data is for risk-sim + dev fixtures only, (d) the 2×2 paper/live ×
  automated/manual matrix.

### B — UAC mode-enum reconciliation

- **Code state**: `unified-api-contracts/unified_api_contracts/internal/modes.py:69-96` has
  `RuntimeMode { LIVE, BATCH }`, `OperationalMode { LIVE, MANUAL, BACKTEST, PAPER }`,
  `TestingStage { MOCK, HISTORICAL, LIVE_MOCK, LIVE_TESTNET, STAGING, LIVE_REAL }`. Used at
  `unified-api-contracts/unified_api_contracts/internal/domain/.../deployment.py:53`
  (`deploy_mode: RuntimeMode = RuntimeMode.BATCH`).
- **Anti-pattern A**: `execution-service/execution_service/service_config.py` has `paper_trade: bool` field with alias
  `PAPER_TRADE | DEFI_PAPER_TRADE` — competing surface.
- **Anti-pattern B**: `execution-service/execution_service/sports_execution/routing.py:16-25` has
  `_PAPER_VENUE_KEYS = ("paper", "betfair", "matchbook")` — string-set rather than enum.
- **Run state**: Anti-patterns A + B in active production code paths — not just legacy.
- **Gap**: Single-SSOT enum collapse + deletion of A + B. May trigger conventional-commits sweep across service repos
  that consume the bool.

### C — Archetype paper-trade maturity

- **Code state — `carry_staked_basis`**:
  `strategy-service/strategy_service/engine/strategies/v2/carry_and_yield/staked_basis.py` exists; tests include
  `test_archetype_engines_filled.py::test_carry_staked_basis_lst_as_margin_emits_four_leg_bundle`.
- **Code state — `leveraged_funding_arb`**: not located in audit grep; may be under different filename, or not
  implemented yet.
- **Run state**: No evidence of paper-mode end-to-end run for either archetype against real DeFi + perp testnet/matching
  engine + real risk + real alerting on real infra. Backtest evidence exists; paper-mode evidence does not.
- **Gap**: Per-archetype paper-runnable matrix (4-state) not populated. May-23 cutover blocked on paper-mode evidence
  for at least the lead archetype.

### D — Per-venue paper / testnet support

- **Code state — CeFi perp venues**: `execution-service/execution_service/venues/initializer.py` and `venues/deribit.py`
  reference `testnet`; **no callable testnet-mode constructor** found for Bybit, Binance, OKX, Hyperliquid, Aster.
- **Code state — DeFi**: `execution-service/execution_service/providers/base.py:~45` lists
  `TenderlyProvider: Tenderly Virtual TestNet fork (batch + paper)`. EVM coverage. Solana paper analogue: not addressed
  in audit grep.
- **Code state — Sports**: `execution-service/execution_service/sports_execution/adapters/paper/paper_betting.py` has
  full `PaperBettingAdapter` with bet placement / cancellation / settlement. Most mature paper surface in repo.
- **Gap (BIG)**: 5 of 6 perp venues lack testnet routing. `leveraged_funding_arb` paper-mode is fully blocked on this.
  `carry_staked_basis` hedge leg is partially blocked (depends on which venue carries the hedge).

### E — Per-instrument-type paper-trade

- **Run state**: No evidence of per-instrument-type paper-mode coverage matrix anywhere. Strategy-service treats all
  instrument types identically (per SSOT). Execution-service per-instrument paper plumbing varies.
- **Gap**: Matrix needs population per § Block E.

### F — Strategy instruction layer

- **Code state**: `execution-service/execution_service/strategy_instructions/gcs.py:1-50` shows instruction parquet
  schema + GCS routing — no mode field. Mode injected at execution-service boot.
- **Verdict**: Boot-time injection currently. Decision needed on whether to lift mode into the instruction envelope to
  support A/B execution lanes.

### G — DART visualization

- **Code state**: `unified-trading-system-ui/components/shell/dart-scope-bar.tsx:1-639` (cockpit),
  `components/trading/execution-mode-toggle.tsx:1-229` (live↔batch toggle, mock-only). Execution Stream paper/live
  toggle at `dart-scope-bar.tsx:552-565` with `LiveConfirmDialog` at `:338-369`.
- **Run state**: All DART surfaces are mock-data-only today (`VITE_MOCK_API=true`). No real paper / live / batch data
  wired.
- **Gap**: Three-way comparison view (batch / paper / live side-by-side) does not exist. Manual-trade-gate per-trade
  approval does not exist (master plan G23 aspirational). Automated-vs-manual per-strategy toggle does not exist.

### H — Automated-vs-manual flow

- **Code state**: No dedicated automated-vs-manual primitive found in audit. `OperationalMode.MANUAL` exists in UAC enum
  but its semantics (per-trade confirm? signal-arming? full manual trader workflow?) are not pinned in code.
- **UI reference**: `unified-trading-system-ui/docs/reference/manual-trader-workflow.md` is a design spec — not
  implemented.
- **Gap**: Closed-set policy + plumbing not implemented.

### I — Mock-vs-paper boundary

- **Code state**: `CLOUD_MOCK_MODE`, `VITE_MOCK_API`, `MOCK_STATE_MODE` are dev-mode flags per CLAUDE.md § "Local
  Development." No assertion enforcing `paper_trade ⇒ NOT CLOUD_MOCK_MODE` found in execution-service boot.
- **Gap**: Boundary enforcement absent — silent misconfiguration possible.

### J — Three-way reconciliation

- **Code state**: `batch-live-reconciliation-service/` exists with `stages/stage3_execution_recon.py`,
  `models/deviation_thresholds.py`. UTL exports `batch_live_reconciler`
  (`unified-trading-library/tests/unit/test_batch_live_reconciler.py`).
- **Run state**: Recon service code shipped; per CLAUDE.md "Plans Run To Actual Completion" check needed — has it
  actually run end-to-end against real batch + real live data, or smoke-only?
- **Gap**: No `paper-live` or `batch-paper` recon stage found. Single-pair (batch-vs-live) implementation; 3-way
  generalization not implemented.

## Operator notes / answers

- **Conceptual frame (operator, 2026-05-08 msg 1)**: "For some things, like the pricing stuff, there's no real paper
  concept, right? It's just you're using the right data. We have a mock data concept, but that's more for simulations of
  various risk simulations where you're dropping the underlying or whatever. Batch versus paper is really about
  execution in the end, because even strategy makes the same decisions: P&L, risk, all that stuff. So instead of
  executing on a fake exchange, either you're simulating what the execution would be live, or you're working on a
  testnet or forked chain, whatever gives you the most realistic API conditions without having to spend any real money."

  → captured as the conceptual model in § Intent + § Block A. Carries through to the codex SSOT NEW doc proposed in
  "What answered looks like."

- **Refined taxonomy (operator, 2026-05-08 msg 2)**: "Shouldn't it be live or paper same effectively for execution apart
  from matching api calls not real (simulation of matching) or to testnet — everything else same. Backtest and manual
  other modes — backtest same but always simulation for matching; manual is real trades and endpoints, just manual
  triggers for the execution (might be redundancy or different deployment or even account but that's up to user config
  for manual deployment)."

  → captured as the two-axis taxonomy in § Intent + § Block A5 + Block A6 + § Block B (UAC enum verdict) + § Block H.

- **Ten plan-shape forks settled (operator, 2026-05-09 msg 3)**: see § "Settled (operator decisions 2026-05-09)" at the top of this doc. Highlights:
  1. Fold into `master_to_live_defi_2026_05_23.md` Group F items 17/18 (and 21 for recon) — comprehensively spec'd; no parallel standalone plan.
  2. Enum shape: closest-to-existing-code → keep `OperationalMode` single 4-value enum, add additive `ExecutionTarget` / `ExecutionTrigger` enums + a `decompose()` derived helper. Earlier "wrong shape" verdict in B1 dropped.
  3. Per-venue policy: simulate-first (matching engine floor for every venue), testnet as fallback / upgrade where API + credentials exist.
  4. Manual gate: ships pre-cutover, executable via unified-trading-system UI hooked to backend.
  5. DART: ships pre-cutover, both views (side-by-side comparison + separate batch / paper / live), wired to real backend.
  6. `leveraged_funding_arb` is stale terminology — the archetype is `ARBITRAGE_PRICE_DISPERSION` (`funding-rate-dispersion` variant), owned by `arbitrage_price_dispersion_finalisation_2026_05_09.md`; cross-link added to `related_plans:`.
  7. `TestingStage`: merge — collapses to `(target, trigger)` derived view; deprecate as separate enum.
  8. Solana paper analogue: use Solana equivalent (devnet / localnet / surfnet); same rule for any non-EVM chain without Tenderly. UAC needs a per-chain `paper_target_registry` mapping `chain → testnet/fork primitive`.
  9. Instruction-layer mode-routing: lift `mode` into UAC instruction envelope; boot-time injection becomes default-fallback when an instruction omits the field.
  10. Mock-vs-paper boundary: no enforcement — operator-discipline only. `(paper_trade=true, CLOUD_MOCK_MODE=true)` is a legitimate combination (e.g. UI dev rendering).

## Iteration log

| Date       | Author   | Change                                                                                                                                                                                                                                                                                              |
| ---------- | -------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 2026-05-08 | agent    | Initial draft — question + 10 blocks + audit findings pre-populated from workspace audit (Explore × 2 sub-agents, parallel).                                                                                                                                                                        |
| 2026-05-08 | operator | Refined taxonomy: live and paper effectively same for execution apart from matching (real vs simulation/testnet); backtest = same code path, always simulation; manual = real trades + real endpoints + manual triggers; deployment / account / VM redundancy is operator config.                   |
| 2026-05-08 | agent    | Two-axis taxonomy folded into § Intent + Block A (A5/A6) + Block B1 (UAC enum verdict — `OperationalMode` has wrong shape, `MANUAL` is trigger axis not peer mode) + Block B3 (settled) + Block H (full re-shape: pre-execution gate canonical, manual UX channels, deployment-redundancy options). |
| 2026-05-09 | operator | Ten plan-shape forks settled in one pass — see § "Settled (operator decisions 2026-05-09)" header. Master fold-in confirmed; enum-shape pivots to single-enum-with-derived-helper; simulate-first + testnet-fallback policy; manual gate + DART 3-way both ship pre-cutover; `leveraged_funding_arb` resolved as stale terminology; TestingStage merge; Solana via native testnet; instruction envelope carries mode; no mock-vs-paper enforcement. |
| 2026-05-09 | agent    | Settled section added at top of doc; B1 verdict re-written (single-enum-with-decompose-helper closest to existing code); frontmatter `related_codex` re-flagged as NEW (neither doc on disk); `arbitrage_price_dispersion_finalisation_2026_05_09.md` cross-linked in `related_plans`; status: `audit-in-progress` → `iterating`; Plan-shape decisions section updated for master fold-in path. |
| 2026-05-09 | agent    | Plan spawned. Master plan `master_to_live_defi_2026_05_23.md` extended with "Folded paper-vs-live workflow maturity" sub-section under Group F + Group G item 23 sub-items (13 todos: pvl-p17a..d / p18a..b / p20a..c / p21a / p22a / p23a..c). 5 codex SSOT NEW stubs created (operational-modes, paper-vs-live-execution-seam, per-venue-paper-policy, archetype-paper-readiness, dart-mode-toggle). Cross-plan banners added on `defi_master_2026_05_07.md` + `arbitrage_price_dispersion_finalisation_2026_05_09.md`; 5 question-doc banners deferred (parallel-agent untracked WIP). Question doc status: `iterating` → `plan-spawned`. |

## Plan-shape decisions (settled 2026-05-09)

- **Plan extraction path**: **fold into `plans/active/master_to_live_defi_2026_05_23.md` Group F** — comprehensively spec items 17 (Backtest fidelity), 18 (2-year batch backtest run), and 21 (Reconciliation suite). Add new sub-items where this doc's blocks add scope not currently covered:
  - **17.A** — UAC enum consolidation (delete `paper_trade: bool`, delete `_PAPER_VENUE_KEYS`, add additive `ExecutionTarget` + `ExecutionTrigger` enums + `decompose()` helper, lift `mode` into UAC instruction envelope, deprecate `TestingStage` as parallel enum).
  - **17.B** — per-venue paper policy: simulate-first floor for all 6 perp venues + DeFi + sports + prediction; testnet upgrade where API + credentials exist (Deribit testnet known viable; others audit + wire). UAC `paper_target_registry: dict[chain, testnet_or_fork_primitive]` for non-EVM chains (Solana via devnet/localnet/surfnet for `carry_staked_basis` jitoSOL/mSOL/bSOL legs).
  - **17.C** — per-archetype paper-runnable matrix populated for the May-23 lead pair (`carry_staked_basis` + `ARBITRAGE_PRICE_DISPERSION:funding-rate-dispersion`); 4-state taxonomy (paper-runnable / paper-shippable / backtest-only / stub). Cross-link `arbitrage_price_dispersion_finalisation_2026_05_09.md` for the funding-arb archetype (NOT a fictional `LEVERAGED_FUNDING_ARB`).
  - **17.D** — strategy-instruction-layer mode-routing: `mode: OperationalMode` field added to UAC instruction envelope; boot-time injection becomes default-fallback.
  - **18.A** — paper-mode evidence run (≥3 continuous days) for the lead pair against real DeFi venues + Tenderly fork (EVM legs) + Solana devnet (Solana legs) + matching-engine simulation (perp hedge legs absent testnet). Event-stream verified per "no fire-and-forget VM launches" rule.
  - **21.A** — extend batch-vs-live recon to 3-way (batch ↔ paper ↔ live) with codified per-pair tolerances + closed-set failure-routing policy.
  - **23.A** (Group G — operator UX) — DART 3-way visualization in unified-trading-system-ui: side-by-side comparison view + separate per-mode views, both wired to real backend (not mock). Manual gate UI affordance executable via unified-trading-system-ui hooked to execution-service.

- **Plan type**: mixed (UAC schema additive + execution-service consolidation + UI + per-venue infra + 3-way recon + codex SSOTs).
- **Owner side**: both. Ikenna leads UAC enum work (additive change → derived helper → instruction envelope mode field → master plan re-spec) + codex SSOTs + DART UI shape decisions. Harsh leads per-venue testnet wire-up + per-archetype paper-runnable evidence runs + 3-way recon implementation.
- **Codex SSOTs touched** (4 NEW + 2 UPDATE):
  - `codex/04-architecture/operational-modes.md` — **NEW** (does not exist on disk) — pins single-enum + decomposition helper + 4-cell mode matrix + per-axis routing rules.
  - `codex/04-architecture/batch-equals-live-pipeline.md` — **NEW** (does not exist on disk) — pins SSOT that strategy / risk / P&L / position / alerting / instructions are identical across modes.
  - `codex/04-architecture/paper-vs-live-execution-seam.md` — NEW — pins the execution-only-seam, pricing-no-paper, mock-vs-paper boundary (operator-discipline, not enforced).
  - `codex/12-strategies/archetype-paper-readiness.md` — NEW — per-archetype 4-state matrix.
  - `codex/05-infrastructure/per-venue-paper-policy.md` — NEW — simulate-first + testnet-fallback policy + paper_target_registry.
  - `codex/14-customer-journeys/dart-mode-toggle.md` — NEW — DART 3-way visualization + manual gate UI shape.

- **Cross-plan dependencies + banner additions**:
  - `master_to_live_defi_2026_05_23.md` — fold-in target. Group F items 17/18/21 + Group G item 23 expand per § "Plan-shape decisions" above.
  - `arbitrage_price_dispersion_finalisation_2026_05_09.md` — paper-runnable evidence run for funding-rate-dispersion variant lands here (cross-banner on master 17.C).
  - `defi_master_2026_05_07.md` — Tenderly fork policy + per-chain paper_target_registry compose with DeFi master.
  - `promote_workflow_backtest_to_paper_to_live_2026_05_08.md` — promote workflow assumes the plumbing this plan ships; banner mutual.
  - `risk_simulations_limits_alerting_2026_05_08.md` — explicitly carves mock-data risk-sim OUT of paper scope; cross-link only.
  - `mock_data_pipeline_benchmarking_2026_05_08.md` — orthogonal; cross-link only.
  - `api_keys_wallets_accounts_readiness_2026_05_08.md` — per-venue paper credentials in scope (testnet API keys + Tenderly tokens + Solana devnet wallets); banner mutual.
  - `disaster_recovery_reconciliation_circuit_breakers_2026_05_08.md` — 3-way recon failure-routing policy composes here.

- **Estimated scope (master fold-in shape)**: ~12-18 AI-days total.
  - UAC additive enum work + decompose helper + instruction envelope mode field + TestingStage deprecation: ~1-2d (Ikenna).
  - `paper_trade: bool` + `_PAPER_VENUE_KEYS` deletion + 6 consumer file migration: ~1d (Ikenna).
  - Per-venue testnet wire-up audit + simulate-first matching engine adapter pass + Deribit testnet integration: ~3-5d (Harsh).
  - Solana devnet + paper_target_registry + non-EVM chain coverage: ~2d (Harsh).
  - DART 3-way visualization (side-by-side + per-mode + manual gate UI) wired to real backend: ~3-5d (both).
  - Per-archetype paper-runnable evidence runs (carry_staked_basis + funding-rate-dispersion variant, ≥3 days each): ~2-3d (Harsh, real-infra).
  - 3-way recon stage (batch-paper + paper-live extensions to existing batch-live-reconciliation-service): ~1-2d (Harsh).
  - 6 codex SSOT NEW docs: ~1-2d (Ikenna).

## Plan extraction record

Plan spawned 2026-05-09 — folded into `master_to_live_defi_2026_05_23.md` Group F + Group G as a sub-section "Folded
paper-vs-live workflow maturity" with 13 sub-items.

- **Plan path**: [`plans/active/master_to_live_defi_2026_05_23.md`](../active/master_to_live_defi_2026_05_23.md) §
  "Folded paper-vs-live workflow maturity (from `paper_vs_live_workflow_maturity_2026_05_08.md` question doc)" — Group F
  fold-in (items 17/18/20/21/22) + Group G sub-section under item 23.
- **Spawned commit**: TBD (this session) — PM repo: master plan fold-in + 5 codex SSOT NEW + 2 cross-plan banners +
  question doc status flip in one logical unit.
- **Codex SSOTs created** (5 NEW):
  - [`codex/04-architecture/operational-modes.md`](../../codex/04-architecture/operational-modes.md) — single-enum
    SSOT + decompose helper + 4-cell matrix.
  - [`codex/04-architecture/paper-vs-live-execution-seam.md`](../../codex/04-architecture/paper-vs-live-execution-seam.md)
    — execution-only-seam principle, pricing-no-paper, mock-vs-paper boundary.
  - [`codex/05-infrastructure/per-venue-paper-policy.md`](../../codex/05-infrastructure/per-venue-paper-policy.md) —
    simulate-first + testnet-fallback + `paper_target_registry` SSOT.
  - [`codex/09-strategy/architecture-v2/cross-cutting/archetype-paper-readiness.md`](../../codex/09-strategy/architecture-v2/cross-cutting/archetype-paper-readiness.md)
    — per-archetype 4-state taxonomy + paper-runnable gate set.
  - [`codex/14-customer-journeys/dart/mode-toggle.md`](../../codex/14-customer-journeys/dart/mode-toggle.md) — DART
    3-way visualization + manual gate UI.
- **Codex SSOTs to UPDATE during plan execution** (1):
  - [`codex/04-architecture/batch-live-architecture.md`](../../codex/04-architecture/batch-live-architecture.md) —
    extend with paper-mode positioning (batch ⊂ paper ⊂ live in code-path).
- **Cross-plan banners added** (2 mutual):
  - [`defi_master_2026_05_07.md`](../active/defi_master_2026_05_07.md) — Tenderly fork + per-chain
    `paper_target_registry`.
  - [`arbitrage_price_dispersion_finalisation_2026_05_09.md`](../active/arbitrage_price_dispersion_finalisation_2026_05_09.md)
    — funding-rate-dispersion variant pairs with `carry_staked_basis` for May-23 paper-mode evidence run.
- **Cross-plan banners deferred** (5 — parallel-agent untracked WIP in `plans/questions/`; will banner when those docs
  land on `live-defi-rollout`):
  - `promote_workflow_backtest_to_paper_to_live_2026_05_08.md`
  - `risk_simulations_limits_alerting_2026_05_08.md`
  - `mock_data_pipeline_benchmarking_2026_05_08.md`
  - `api_keys_wallets_accounts_readiness_2026_05_08.md`
  - `disaster_recovery_reconciliation_circuit_breakers_2026_05_08.md`
- **Question doc closes** (status: `closed`) when: `pvl-p18a` paper-mode end-to-end run shipped for ≥1 May-23 archetype
  pair + `pvl-p17a/b/c/d` UAC enum consolidation landed + `pvl-p23a/b/c` DART 3-way visualization + manual gate visible
  in UI with real data + `pvl-p21a` 3-way recon stage shipped.
