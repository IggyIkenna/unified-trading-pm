---
doc_type: codex-ssot
title: Strategy Architecture v2 — Block List
summary:
  Narrative + remediation SSOT for every architecture-v2 coverage cell that resolves to CoverageStatus=BLOCKED (entries
  BL-1..BL-10, plus BL-12) — each with affected archetypes, affected cells, rationale, remediation, UAC gap refs, and
  owner team; kept in sync with the UI block-list.ts runtime mirror.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [execution-service, features-service, strategy-service, unified-api-contracts, unified-trading-system-ui]
scope: [engineer, admin]
tags: [strategy, catalogue, defi, execution, uac, data-quality]

  [
    /codex/09-strategy/architecture-v2/category-instrument-coverage.md,
    /codex/09-strategy/architecture-v2/restriction-policy.md,
    /codex/09-strategy/architecture-v2/README.md,
  ]
created: 2026-04-20
authoritative_for: [architecture-v2 coverage BLOCKED-cell remediation registry (BL-N entries)]
referenced_by:
  [
    /codex/09-strategy/README.md,
    /codex/09-strategy/architecture-v2/category-instrument-coverage.md,
    /codex/09-strategy/architecture-v2/restriction-policy.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Strategy Architecture v2 — Block List

> **Purpose:** Every (archetype × venue category × instrument type) tuple in the coverage matrix that resolves to
> `CoverageStatus = BLOCKED` refers here for the _why_ and the _remediation_. This file is the narrative-and-remediation
> side of the `BLOCKED` cells in [`category-instrument-coverage.md`](category-instrument-coverage.md).
>
> **Runtime mirror:** `unified-trading-system-ui/lib/architecture-v2/block-list.ts` — the UI reads from this TypeScript
> module to render block-list entries on `/services/strategy-catalogue/coverage/blocked`. The two are kept in sync
> manually; when an entry changes, update both in the same PR.
>
> **How new entries get added:**
>
> 1. A coverage cell flips to `BLOCKED` (either new combo declared blocked, or an existing SUPPORTED / PARTIAL cell
>    regresses).
> 2. Author a new `BL-N` section here with cells, rationale, remediation, and owner.
> 3. Mirror the entry into `block-list.ts` (`id`, `summary`, `archetypesAffected`, `explanation`, `remediation`,
>    `uacGapRefs`, `affectedCells`).
> 4. Add the `BL-N` token to the `blockListRefs: [...]` array on each affected coverage cell in the auto-generated
>    `coverage.ts` (ultimately regenerated from the UAC `archetype_capability_manifest.json`).
> 5. Link the upstream remediation (UAC gap issue, venue-integration ticket, etc.) in the `uacGapRefs` array.

## Canonical enums used in this file

Cross-references use the canonical v2 enum names from
`unified-api-contracts/unified_api_contracts/internal/architecture_v2/enums.py`:

- **`StrategyFamily`** (8): `ML_DIRECTIONAL`, `RULES_DIRECTIONAL`, `CARRY_AND_YIELD`, `ARBITRAGE_STRUCTURAL`,
  `MARKET_MAKING`, `EVENT_DRIVEN`, `VOL_TRADING`, `STAT_ARB_PAIRS`.
- **`StrategyArchetype`** (18): `ML_DIRECTIONAL_CONTINUOUS`, `ML_DIRECTIONAL_EVENT_SETTLED`,
  `RULES_DIRECTIONAL_CONTINUOUS`, `RULES_DIRECTIONAL_EVENT_SETTLED`, `CARRY_BASIS_DATED`, `CARRY_BASIS_PERP`,
  `CARRY_STAKED_BASIS`, `CARRY_RECURSIVE_STAKED`, `YIELD_ROTATION_LENDING`, `YIELD_STAKING_SIMPLE`,
  `ARBITRAGE_PRICE_DISPERSION`, `LIQUIDATION_CAPTURE`, `MARKET_MAKING_CONTINUOUS`, `MARKET_MAKING_EVENT_SETTLED`,
  `EVENT_DRIVEN`, `VOL_TRADING_OPTIONS`, `STAT_ARB_PAIRS_FIXED`, `STAT_ARB_CROSS_SECTIONAL`.
- **`VenueCategoryV2`** (5): `CEFI`, `DEFI`, `SPORTS`, `TRADFI`, `PREDICTION`.
- **`InstrumentTypeV2`** (8): `spot`, `perp`, `dated_future`, `option`, `lending`, `staking`, `lp`, `event_settled`.

## Entries

### BL-1: No supported DeFi options venue

**Archetypes affected:** `ML_DIRECTIONAL_CONTINUOUS`, `RULES_DIRECTIONAL_CONTINUOUS`, `ARBITRAGE_PRICE_DISPERSION`,
`MARKET_MAKING_CONTINUOUS`, `VOL_TRADING_OPTIONS`.

**Affected cells:**

- `(ML_DIRECTIONAL_CONTINUOUS, DEFI, option)`
- `(RULES_DIRECTIONAL_CONTINUOUS, DEFI, option)` — also covered by BL-4
- `(ARBITRAGE_PRICE_DISPERSION, DEFI, option)`
- `(MARKET_MAKING_CONTINUOUS, DEFI, option)`
- `(VOL_TRADING_OPTIONS, DEFI, option)`

**Rationale:** Lyra and Dopex were archived 2026-03. No replacement DeFi options venue is currently declared in UAC.

**Remediation:** Evaluate Aevo, Premia, or Hegic as a replacement — or formally accept DeFi options as out-of-scope and
remove the associated cells.

**UAC gap refs:** #6 (options-expression policy)

**Owner team:** Data / Strategy (venue evaluation) + UAC maintainers (capability declaration).

---

### BL-2: No DeFi dated-future venue

**Archetypes affected:** `ML_DIRECTIONAL_CONTINUOUS`, `CARRY_BASIS_DATED`.

**Affected cells:**

- `(ML_DIRECTIONAL_CONTINUOUS, DEFI, dated_future)`
- `(CARRY_BASIS_DATED, DEFI, spot + dated_future)` — basis leg requires both

**Rationale:** Deribit is CeFi. No on-chain dated-future venue is currently supported; perps protocols have not added
dated-expiry instruments at scale.

**Remediation:** Track emerging on-chain dated-future venues (e.g. perps protocols adding expiry). Not currently a
priority — revisit if venue-level volume justifies adapter work.

**UAC gap refs:** (none — cannot declare a capability a venue doesn't offer)

**Owner team:** Strategy (venue watch) + Data (market-data integration if/when added).

---

### BL-3: CeFi lending out-of-scope

**Archetypes affected:** `YIELD_ROTATION_LENDING`.

**Affected cells:**

- `(YIELD_ROTATION_LENDING, CEFI, lending)`

**Rationale:** Binance Earn / Bybit lending have withdrawal lockups + counterparty-risk concentration that violate
Odum's risk policy. Not a gap we intend to close.

**Remediation:** Decision: excluded from the product. Revisit only if a credible clearing / custody model emerges for
CeFi lending that addresses lockup + counterparty risk.

**UAC gap refs:** (none — deliberate exclusion, not an integration gap)

**Owner team:** Risk / Strategy.

---

### BL-4: CeFi / TradFi directional options via rules (degenerate case)

**Archetypes affected:** `RULES_DIRECTIONAL_CONTINUOUS`.

**Affected cells:**

- `(RULES_DIRECTIONAL_CONTINUOUS, CEFI, option)`
- `(RULES_DIRECTIONAL_CONTINUOUS, TRADFI, option)`

**Rationale:** Directional options via hand-coded rules is a degenerate case — there is no coherent product intent that
this archetype + instrument combo serves. Alternatives fully cover the use case.

**Remediation:** Use `VOL_TRADING_OPTIONS` for vol-metric rules, or `ML_DIRECTIONAL_CONTINUOUS` with
`expression=atm_call` (delta-as-expression axis) for directional options expression.

**UAC gap refs:** #6 (options-expression policy — covered by the alternative path)

**Owner team:** Strategy (taxonomy guidance).

---

### BL-5: Kalshi execution adapter pending

**Archetypes affected:** `ML_DIRECTIONAL_EVENT_SETTLED`, `RULES_DIRECTIONAL_EVENT_SETTLED`,
`MARKET_MAKING_EVENT_SETTLED`.

**Affected cells:**

- `(ML_DIRECTIONAL_EVENT_SETTLED, PREDICTION, event_settled)` via Kalshi
- `(RULES_DIRECTIONAL_EVENT_SETTLED, PREDICTION, event_settled)` via Kalshi
- `(MARKET_MAKING_EVENT_SETTLED, PREDICTION, event_settled)` via Kalshi

**Rationale:** Kalshi data + pricing feeds are integrated, but the execution adapter is not built — orders cannot be
routed. Polymarket fills the PREDICTION slot today.

**Remediation:** Build the Kalshi execution adapter following the interface-credential convention (see
`execution-service` codex / `interface-credential-convention.md`). Standard adapter work — no architectural blockers.

**UAC gap refs:** (none — adapter work, not a capability-declaration gap)

**Owner team:** Execution.

---

### BL-6: Unity cannot quote (Feed Connector is place-only)

**Archetypes affected:** `MARKET_MAKING_EVENT_SETTLED`.

**Affected cells:**

- `(MARKET_MAKING_EVENT_SETTLED, SPORTS, event_settled)` via Unity

**Rationale:** Unity's Java Feed Connector accepts `PLACE_BET` / `CANCEL` orders but does not expose a quoting API.
Unity's child books quote internally; we cannot add our own bids/offers through Unity.

**Remediation:** Permanent architectural constraint — Unity remains place-only. Quote on venues that expose a quoting
API (Betfair Exchange, Smarkets, Matchbook, BetDAQ).

**UAC gap refs:** (none — venue architectural limitation)

**Owner team:** Execution (documentation) — no further action.

---

### BL-7: DeFi perp MM not exposed as third-party role

**Archetypes affected:** `MARKET_MAKING_CONTINUOUS`.

**Affected cells:**

- `(MARKET_MAKING_CONTINUOUS, DEFI, perp)`

**Rationale:** Hyperliquid has protocol-level market-making incentives; there is no third-party-MM role comparable to
CLOB MM on a CEX. Protocol-level MM is inaccessible to us by design.

**Remediation:** Not a product gap — pursue CeFi perp MM (`MARKET_MAKING_CONTINUOUS, CEFI, perp`) instead, which is
already `SUPPORTED`.

**UAC gap refs:** (none — design constraint of the protocols)

**Owner team:** Strategy — documentation only.

---

### BL-8: DeFi cross-sectional basket (multi-leg gas efficiency)

**Archetypes affected:** `STAT_ARB_CROSS_SECTIONAL`.

**Affected cells:**

- `(STAT_ARB_CROSS_SECTIONAL, DEFI, spot)`

**Rationale:** Atomic multi-token basket trade on DeFi is gas-prohibitive on EVM. A 50–500-leg basket (typical for
cross-sectional strategies) would cost more in gas than the expected edge.

**Remediation:** Requires a specialised router (1inch Pathfinder-style) not currently declared in UAC. Track EVM gas
evolution + L2 adoption; revisit when gas / batch-call primitives are cheap enough to make the strategy profitable.

**UAC gap refs:** #7 (multi-leg order capability)

**Owner team:** Execution / Strategy (router evaluation).

---

### BL-9: TradFi cross-sectional on futures basket

**Archetypes affected:** `STAT_ARB_CROSS_SECTIONAL`.

**Affected cells:**

- `(STAT_ARB_CROSS_SECTIONAL, TRADFI, dated_future)`

**Rationale:** Multi-leg cross-sectional on a CME-futures basket requires batch-order capability that is not declared
for the CME adapter. The adapter supports single-contract orders today.

**Remediation:** Extend the CME adapter with `MultiLegOrderCapability` (UAC gap #7). Medium-effort adapter work — CME
supports combo orders natively; adapter needs to expose the wire-level primitives.

**UAC gap refs:** #7 (multi-leg order capability)

**Owner team:** Execution.

---

### BL-10: Dated-future auto-roll + combo creation not yet live

**Archetypes affected:** `ML_DIRECTIONAL_CONTINUOUS`, `RULES_DIRECTIONAL_CONTINUOUS`, `STAT_ARB_PAIRS_FIXED`,
`STAT_ARB_CROSS_SECTIONAL`, `ARBITRAGE_PRICE_DISPERSION`, `EVENT_DRIVEN`, `CARRY_BASIS_DATED`.

**Affected cells:** Any `-dated-` slot, any category, `dated_future` — functional but requires manual roll. Present in
`PARTIAL` cells across TradFi (CME / ICE) and CeFi (Deribit) dated-future combinations, plus any dated-bearing strategy
that spans a contract expiry.

**Rationale:** The end-to-end flow (features-service liquidity measure → representative-future-service state transition
→ `REPRESENTATIVE_FUTURE_CHANGED` event → strategy-service roll emission → execution-service combo resolution with
synthetic-price guardrails) is specced but not yet implemented. Until it ships, dated-future strategies run on
fixed-contract slot labels only (`-fixed-{contract}-`), and ops manually rotate to the next expiry. Workable for a
handful of strategies; does not scale.

> **[DELTA 2026-05-22]** **Current state:** Not yet implemented; dated-future strategies run fixed-contract slot labels
> only with manual expiry rotation. **Planned delta:** `plans/epics/strategy_master.md` Phase 11. **Target
> architecture:** Automated roll via representative-future-service + FUTURES_ROLL instruction.

**Remediation:** Phase 11 of the active architecture-v2 finalization plan:

- `RepresentativeFutureRegistry` in UAC
- `representative-future-service` scaffold
- `REPRESENTATIVE_FUTURE_CHANGED` event in UTL lifecycle events
- `FUTURES_ROLL` instruction in strategy-service
- execution-service combo auto-creation + circuit breakers

**UAC gap refs:** #11 (representative-future registry)

**Owner team:** Strategy + Execution + UAC (spans four repos).

### BL-12: DeFi perp liquidation capture — no venue

**Archetypes affected:** `LIQUIDATION_CAPTURE`.

**Affected cells:** `(LIQUIDATION_CAPTURE, DeFi, perp)`.

**Rationale:** `gmx_v2` was the sole DeFi perp-liquidation venue for this cell (perp liquidations have different
economics than lending liquidations, which is why this was never merged with the Aave/Kamino lending-liquidation cells).
GMX was removed platform-wide 2026-08-04 for unreliable historical funding data — the entire captured `perp_funding`
history turned out to be a synthetic OI-imbalance proxy, not real per-market observations (see
`/plans/archive/2026_07/defi_gmx_venue_removal_2026_07_25.md`). Removing GMX leaves this cell with no remaining venue,
so it flips from `PARTIAL` to `BLOCKED`.

**Remediation:** Onboard a replacement DeFi perp DEX with a working, verified liquidation-capture feed (native
per-market funding/liquidation data, not a fallback proxy).

**UAC gap refs:** none.

**Owner team:** Strategy + Execution + UAC (spans four repos).

## See also

- [`README.md`](README.md) — architecture-v2 taxonomy + axes.
- [`category-instrument-coverage.md`](category-instrument-coverage.md) — full coverage matrix; BL refs live in
  `blockListRefs` on each cell.
- [`uac-registry-gaps.md`](uac-registry-gaps.md) — UAC gap numbers cross-referenced above (#6, #7, #11).
- [`restriction-policy.md`](restriction-policy.md) — how BLOCKED cells interact with lock-state + questionnaire
  filtering.
- `unified-trading-system-ui/lib/architecture-v2/block-list.ts` — runtime mirror.
