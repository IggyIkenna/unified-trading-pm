---
doc_type: codex-ssot
title: Strategy Lifecycle & Maturity Model
summary:
  SSOT for the 5-dimension strategy-instance model — the 9-phase forward-only StrategyMaturityPhase staircase,
  ProductRouting, venue-set-variant upsell ladders, ShareClass, and odum-paper/odum-live client-zero; the UAC-catalogue
  vs Firestore-runtime-state split and admin lifecycle-editor flow. Instance explosion ~200-300 rows.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos:
  [
    execution-service,
    strategy-service,
    unified-api-contracts,
    unified-trading-api,
    unified-trading-pm,
    unified-trading-system-ui,
  ]
scope: [engineer, admin]
tags: [strategy, catalogue, uac, promote, reconciliation]
related:
  [
    /codex/09-strategy/architecture-v2/strategy-registry-v2.md,
    /codex/09-strategy/architecture-v2/strategy-catalogue-3tier.md,
    /codex/09-strategy/architecture-v2/performance-overlay.md,
    /codex/09-strategy/architecture-v2/dashboard-services-grid.md,
  ]
created: 2026-04-21
authoritative_for: [strategy 9-phase maturity model + 5-dim instance registry + venue-set variants]
referenced_by:
  [
    /codex/09-strategy/architecture-v2/dart-exclusive-research-fork.md,
    /codex/09-strategy/architecture-v2/performance-overlay.md,
    /codex/09-strategy/architecture-v2/promote-workflow.md,
    /codex/09-strategy/architecture-v2/strategy-catalogue-3tier.md,
    /codex/09-strategy/architecture-v2/strategy-registry-v2.md,
    /codex/14-customer-journeys/shared-core/odum-paper-client-zero.md,
    /codex/14-customer-journeys/shared-core/strategy-version-governance.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Strategy Lifecycle & Maturity Model

> **Status:** canonical (2026-04-21) **Owner:** Strategy Architecture v2 **SSOT for:**
> `unified-api-contracts/unified_api_contracts/internal/domain/strategy_service/lifecycle.py`,
> `unified-api-contracts/unified_api_contracts/internal/domain/strategy_service/registry.py` (5-dim rewrite),
> `unified-api-contracts/unified_api_contracts/registry/venue_set_variants/`. **Plan:**
> [`plans/archive/strategy_lifecycle_maturity_model_2026_04_21.plan.md`](../../../plans/archive/strategy_lifecycle_maturity_model_2026_04_21.plan.md)
> **Depends on (consumers):** [`strategy-catalogue-3tier.md`](./strategy-catalogue-3tier.md) ·
> [`performance-overlay.md`](./performance-overlay.md) · [`dashboard-services-grid.md`](./dashboard-services-grid.md) ·
> [`../../14-customer-journeys/shared-core/odum-paper-client-zero.md`](../../14-customer-journeys/shared-core/odum-paper-client-zero.md)

Every downstream allocator, catalogue, admin editor, and client view reads from this model. It answers four questions
for any single strategy instance at any point in time:

1. How mature is it? (§1 — 9-phase enum)
2. Who is allowed to see / subscribe to it? (§2 — product routing)
3. Which venues / instruments / share classes does it actually run on? (§3 — venue-set variants · §4 — share class)
4. Who is running it in paper-mode today so it can have a continuous P&L record? (§5 — `odum-paper` client zero)

---

## §1 — Maturity phase enum (9 phases + `retired`)

The nine maturity phases in `StrategyMaturityPhase` form a forward-only staircase. `retired` is an orthogonal terminal
state reachable from any phase.

| Ordinal | Phase                 | Meaning                                                           | Capital at risk | Typical dwell |
| ------- | --------------------- | ----------------------------------------------------------------- | --------------- | ------------- |
| 0       | `smoke`               | Pre-backtest. Mock/fixture data only; wiring smoke-test.          | 0               | hours-days    |
| 1       | `backtest_minimal`    | <1 year of historical backtest. Not viable yet.                   | 0               | days          |
| 2       | `backtest_1yr`        | Exactly 1 year clean backtest. Minimum viability bar.             | 0               | days-weeks    |
| 3       | `backtest_multi_year` | Multi-year backtest (≥3 years preferred).                         | 0               | weeks         |
| 4       | `paper_1d`            | First 24h running against `odum-paper` matching engine.           | $0 (sim)        | 1 day         |
| 5       | `paper_14d`           | 14 days of paper trading (first statistically meaningful window). | $0 (sim)        | 14 days       |
| 6       | `paper_stable`        | Extended paper (≥30d). Promotion-ready.                           | $0 (sim)        | 30d+          |
| 7       | `live_early`          | Initial live trading. Small capital ($100–$1,000 seed).           | Seed cap        | 14-30 days    |
| 8       | `live_stable`         | Mature live. Scaled capital.                                      | Production      | Unbounded     |
| —       | `retired`             | Terminal. Instance decommissioned; P&L history preserved.         | 0               | Terminal      |

### Transition rules

- **Forward-only** — ordinal must strictly increase, OR move to `retired` from any phase. Downgrades require explicit
  demotion via the admin editor (Plan A Phase 3) and emit a `STRATEGY_LIFECYCLE_DEMOTED` audit event.
- **`retired` is terminal** — a retired instance cannot resume. To restart, clone as a new `instance_id` (use
  `version_lineage` to preserve parentage).
- **Promotion gates** — the admin editor enforces per-transition prerequisites:
  - `paper_14d → paper_stable`: ≥30d continuous paper fills with no `STRATEGY_CIRCUIT_BREAKER` events.
  - `paper_stable → live_early`: product-routing decision + operator approval.
  - `live_early → live_stable`: ≥30d live fills + Sharpe ≥ 1.0 on live series.
- **Allocation gating** — client FOMO tearsheets may only offer an allocation CTA for instances at `paper_stable` or
  later (see [`strategy-catalogue-3tier.md`](./strategy-catalogue-3tier.md) §4.2).

### Phase-transition record

Every transition writes a `PhaseTransition{from_phase, to_phase, at, by, reason}` entry into
`StrategyInstanceLifecycle.phase_history`. The catalogue editor (Plan B) surfaces this history in the inline drawer.

---

## §2 — Product routing

`ProductRouting` declares which customer surfaces may see/subscribe to the instance. Orthogonal to maturity.

| Value           | Who sees it                                             | Used for                                  |
| --------------- | ------------------------------------------------------- | ----------------------------------------- |
| `dart_only`     | DART clients (execution-basic / execution-full)         | Self-directed trading clients             |
| `im_only`       | IM Pooled + IM SMA clients (allocation via Odum portal) | Managed-money clients                     |
| `both`          | DART + IM audiences                                     | Broad-market strategies                   |
| `internal_only` | Internal-trader / admin only                            | Research, pre-commercialisation, platform |

**Routing decides visibility, not execution.** A `dart_only` instance still runs against `odum-paper` + optionally
`odum-live` — routing gates only the **customer-facing surfaces** in Strategy Catalogue Tier 3 and Reports allocator
views.

---

## §3 — Venue-set variants (the upsell ladder)

Venue is a **list**, not a scalar. One archetype yields multiple instances differentiated by which venues the instance
executes on. The 5-dim tuple below contains a `venue_set_variant_id` pointing at a registered `VenueSetVariant`.

```python
VenueSetVariant(
    id="ely_base_3cex",
    archetype="DEFI_BASIS_ELYSIUM",
    venues=["OKX", "BINANCE", "BYBIT"],
    instrument_types=["PERPETUAL", "SPOT"],
    label="Base (3 CEX)",
    pricing_tier="base",
)
```

`pricing_tier ∈ {base, premium, top_tier, apex}` maps to commercial pricing (see
`codex/14-customer-journeys/commercial-model/`).

### Worked example — Elysium upsell ladder

The Elysium DeFi basis archetype ships as four variants so IM + DART clients can scale through pricing tiers:

| Variant id               | Venues                                           | Instruments    | Tier       | Target client                      |
| ------------------------ | ------------------------------------------------ | -------------- | ---------- | ---------------------------------- |
| `ely_base_3cex`          | `OKX, BINANCE, BYBIT`                            | PERP, SPOT     | `base`     | New DART / IM client, small ticket |
| `ely_premium_6cex`       | `OKX, BINANCE, BYBIT, COINBASE, DERIBIT, BITGET` | PERP, SPOT     | `premium`  | Upsell tier 2                      |
| `ely_multi_evm`          | 6 CEX + `UNISWAP_V3, AAVE_V3`                    | PERP, SPOT, LP | `top_tier` | EVM-native DeFi allocator          |
| `ely_multi_evm_plus_sol` | 6 CEX + EVM + `JUPITER, RAYDIUM`                 | PERP, SPOT, LP | `apex`     | Cross-chain allocator, highest fee |

Each variant is a distinct `StrategyInstance` row with its own `instance_id`, its own `odum-paper` P&L series, and its
own maturity phase. Clients upgrading from `base` to `premium` are subscribing to a **different instance**, not an
upgraded version of the same one. This enables honest FOMO tearsheets per tier.

### Registry location

`unified_api_contracts/registry/venue_set_variants/<archetype>.py` — one module per archetype declaring the variant
ladder. Public accessor:

```python
from unified_api_contracts.strategy_service import get_venue_set_variants
variants = get_venue_set_variants("DEFI_BASIS_ELYSIUM")
# → [VenueSetVariant(id="ely_base_3cex", ...), ...]
```

---

## §4 — Share class (the 5th dimension)

`ShareClass` is the collateral/quote currency of the instance:

| Value  | Meaning                            | Nullable? |
| ------ | ---------------------------------- | --------- |
| `btc`  | BTC-collateralised / BTC-quoted    | Yes       |
| `eth`  | ETH-collateralised / ETH-quoted    | Yes       |
| `usd`  | Fiat USD                           | Yes       |
| `usdt` | USDT stablecoin                    | Yes       |
| `null` | Archetype has only one share-class | —         |

When an archetype offers multiple share-classes (e.g. an Elysium basis instance in both USDT and USD share classes),
each appears as a separate `StrategyInstance` with its own `instance_id`. When the archetype has only one valid share
class (e.g. a sports betting archetype quoted in USD only), `share_class = null` and the instance tuple is effectively
4-dimensional.

### Optional grouping — `ShareClassFamily`

For aggregation surfaces (e.g. "show me all stablecoin share classes in one view"), the registry exposes
`ShareClassFamily ∈ {crypto_native, fiat, stablecoin}` mapping `{btc, eth} → crypto_native`, `{usd} → fiat`,
`{usdt} → stablecoin`. The grouping is presentational only — the canonical dimension is `ShareClass`.

---

## §5 — `odum-paper` as client zero

The paper account that runs every instance is **not special-cased**. It is a regular `Client` row in `CLIENT_REGISTRY`:

```python
Client(
    client_id="odum-paper",
    org="odum-research",
    account_type="paper",
    seed=True,
)
Client(
    client_id="odum-live",
    org="odum-research",
    account_type="live",
    seed=True,
)
```

Downstream services (`position-balance-monitor-service`, `execution-service`, `strategy-service`) treat `odum-paper`
exactly like any other client — they query positions, route orders to the matching-engine (paper) or the live venue
adapter (live), and record P&L on the same collections. The **only** difference is `account_type` which routes fills
through the execution-service matching engine (zero execution alpha — fills at requested price; see CLAUDE.md "Batch =
Live" section) instead of a real venue.

Every `StrategyInstance` has both an `odum-paper` series (from phase `paper_1d` onwards) and an `odum-live` series (from
phase `live_early` onwards). These series are the authoritative source for:

- FOMO tearsheets (Plan B client-fomo viewMode)
- Performance overlay charts (Plan C — backtest / paper / live continuous timeline)
- Admin universe "run status" badges (Plan B admin-universe viewMode)

Full rationale + lifecycle:
[`../../14-customer-journeys/shared-core/odum-paper-client-zero.md`](../../14-customer-journeys/shared-core/odum-paper-client-zero.md).

---

## §6 — UAC → UI sync (not a live read)

UI does **not** live-read UAC. The registry + lifecycle reference data is materialised into a JSON snapshot on every UAC
merge to main, and the UI reads the snapshot.

### Sync flow

```
UAC merge to main
  → semver-agent bumps version
  → propagation hook runs:
      unified-trading-pm/scripts/openapi/generate_ui_reference_data.py
  → writes:
      unified-trading-system-ui/lib/registry/ui-reference-data.json
  → UI consumers:
      lib/architecture-v2/lifecycle.ts (TS mirrors of UAC enums/dataclasses)
      components/strategy-catalogue/*
```

### What's in `ui-reference-data.json`

- `strategy_instances[]` — full 5-dim expansion (~200-300 entries post-Plan-A)
- `venue_set_variants[]` — per-archetype variant ladders
- `maturity_phases[]` — enum values + human labels + ordinals
- `product_routings[]` — enum values + audience labels
- `share_classes[]` — enum values + ShareClassFamily grouping

### What is **not** in the JSON

- Per-instance **lifecycle state** (current `maturity_phase`, `product_routing`) — this is **mutable** and lives in
  Firestore `strategy_instance_lifecycle/{instance_id}` (see §7). UAC holds the **catalogue of possibilities**;
  Firestore holds **runtime state**.

### Why the split (catalogue vs runtime state)

- UAC is **immutable per release** — a version bump is needed to alter the catalogue of instances.
- Lifecycle state (maturity + routing) changes weekly-daily (admin edits). Forcing a UAC release per edit would be
  absurd. Firestore + `LifecycleReloader` (5-min hot-reload, UTL) is the correct surface.

---

## §7 — Admin lifecycle-editor flow

The admin editor (Plan B Phase 2) is the only surface that mutates lifecycle state.

```
Admin user → /services/admin/strategy-lifecycle-editor
  → <StrategyCatalogueSurface viewMode="admin-editor" />
  → inline editor per row: [maturity_phase ▾] [product_routing ▾]
  → PATCH /api/v1/registry/strategy-instances/{instance_id}/lifecycle
      body: { maturity_phase?: StrategyMaturityPhase, product_routing?: ProductRouting, reason: string }
  → unified-trading-api:
      1. Validate transition (forward-only OR to retired)
      2. Write Firestore strategy_instance_lifecycle/{instance_id}
      3. Append PhaseTransition to phase_history
      4. Emit STRATEGY_LIFECYCLE_CHANGED event (via UTL log_event)
  → Firestore listener (UTL LifecycleReloader, 5-min hot-reload cap) pushes to:
      - strategy-service (gates live execution)
      - UI (refreshes admin-universe + client-reality views)
```

### Audit trail

Every mutation writes a `PhaseTransition` entry with
`{from_phase, to_phase, product_routing_before, product_routing_after, by, reason, at}`. The catalogue editor surfaces
the full history inline via a drawer. Audit log is mirror-persisted to the standard `audit_log` collection for
compliance reads.

### Bulk edit

The editor supports filter → select-all → apply. Typical use: "promote all Elysium base_3cex instances from `paper_14d`
to `paper_stable`". Each row still writes an individual PATCH (no batch endpoint) — keeps the audit log 1:1 with
business events.

### Undo affordance

Toast after a successful PATCH shows "Change applied. Undo (5s)". Undo POSTs the inverse transition. After the 5s
window, undo is gone — the user must manually revert via the editor (which is another auditable transition).

---

## §8 — Instance explosion math

Pre-Plan-A registry (v2 deletion of v1 families): **96 instances** flattened from 18 archetypes × representative cells.

Post-Plan-A (5-dim rewrite):

```
instances = Σ (archetypes) × venue_set_variants_per_archetype × instrument_type_sets × share_classes
```

For an archetype with 4 venue-set variants × 1 instrument-type set × 2 share classes = 8 instances. Summed across 18
archetypes (typical spread: 1-4 variants × 1-3 share classes), the expected total is **~200-300 instances**. The Plan A
Phase 1 QG step (`p1-qg-uac`) prints the exact count for visual inspection.

This is the denominator for:

- Admin universe view (~200-300 rows; virtualised grid)
- Catalogue coverage metrics (% in `paper_stable+`, % with live series, etc.)
- FOMO tearsheet pool (filtered by `product_routing ∈ {dart_only, both}` for DART clients)

---

## §9 — Cross-references

- [`strategy-registry-v2.md`](./strategy-registry-v2.md) — v2 slot-label grammar; pre-5-dim baseline.
- [`strategy-catalogue-3tier.md`](./strategy-catalogue-3tier.md) — Tier 1/2/3 surface wired to this model.
- [`performance-overlay.md`](./performance-overlay.md) — backtest+paper+live overlay using `odum-paper`/`odum-live`
  series.
- [`dashboard-services-grid.md`](./dashboard-services-grid.md) — §4.5 Strategy Catalogue as cross-cutting primitive.
- [`../../14-customer-journeys/shared-core/odum-paper-client-zero.md`](../../14-customer-journeys/shared-core/odum-paper-client-zero.md)
  — full client-zero doctrine + seeding + retention.
- [`../../06-coding-standards/config-reloader-pattern.md`](../../06-coding-standards/config-reloader-pattern.md) —
  `LifecycleReloader` implementation pattern.
