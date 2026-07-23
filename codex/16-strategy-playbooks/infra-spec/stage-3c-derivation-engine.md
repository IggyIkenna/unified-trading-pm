---
doc_type: codex-ssot
title: Stage 3C — Derivation engine (one registry, four derivations)
summary:
  Spec for the side-effect-free derivation engine that reads the Stage 3B combo registry and produces four pure
  functions — combo(), cost(tier×integration_depth), demo_universe(persona×flavour), prod_restrictions(),
  access_control(phase) — from one read with no drift; recommends shipping into strategy-service/availability/ (not a
  new micro-service).
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [execution-service, strategy-service, unified-api-contracts, unified-trading-system-ui]
scope: [engineer, admin]
tags: [uac, strategy, execution, ui, registry, docspec]
related:
  [
    /codex/16-strategy-playbooks/infra-spec/stage-3b-uac-combo-rules.md,
    /codex/16-strategy-playbooks/infra-spec/stage-3b-instruction-schema-contract.md,
    /codex/16-strategy-playbooks/infra-spec/stage-3b-downstream-analytics-capability-matrix.md,
    /codex/16-strategy-playbooks/infra-spec/stage-3e-refactor-plan.md,
    /codex/16-strategy-playbooks/infra-spec/stage-3a-current-infra-audit.md,
  ]
created: 2026-04-20
authoritative_for:
  [
    Stage 3C one-registry-four-derivations engine spec (combo / cost / demo_universe / prod_restrictions /
    access_control),
  ]
referenced_by:
  [
    /codex/14-customer-journeys/commercial-model/pricing-building-blocks.md,
    /codex/14-customer-journeys/demo-ops/README.md,
    /codex/14-customer-journeys/demo-ops/demo-restriction-profiles.md,
    /codex/14-customer-journeys/implementation-mapping/route-mapping.md,
    /codex/14-customer-journeys/presentations/target-experience-post-refactor.md,
    /codex/16-strategy-playbooks/infra-spec/stage-3a-current-infra-audit.md,
    /codex/16-strategy-playbooks/infra-spec/stage-3b-downstream-analytics-capability-matrix.md,
    /codex/16-strategy-playbooks/infra-spec/stage-3b-instruction-schema-contract.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Stage 3C — Derivation engine (one registry, four derivations)

> **Purpose.** Specify the pure-function derivation engine that consumes the Stage 3B UAC combo registry and produces
> four operational artefacts — cost quotes, demo universes, production restrictions, and phase-aware access control —
> from a single registry read. The engine is side-effect-free, idempotent, and cachable. This doc is the spec; the
> implementation is a Stage 3E G1 refactor item.
>
> **Parent plan:**
> [`plans/ai/playbook_ssot_stage_3_infra_spec_2026_04_19.plan.md`](../../../plans/ai/playbook_ssot_stage_3_infra_spec_2026_04_19.plan.md)
> § Phase 3C.
>
> **Inputs:**
>
> - [`stage-3a-current-infra-audit.md`](stage-3a-current-infra-audit.md) — what exists today + gap list
> - [`stage-3b-uac-combo-rules.md`](stage-3b-uac-combo-rules.md) — 15 dimensions + 22 blocker predicates
> - [`stage-3b-combo-rules-schema.yaml`](stage-3b-combo-rules-schema.yaml) — registry shape
> - [`stage-3b-instruction-schema-contract.md`](stage-3b-instruction-schema-contract.md) — rule 10 engineering
>   projection
> - [`stage-3b-downstream-analytics-capability-matrix.md`](stage-3b-downstream-analytics-capability-matrix.md) —
>   per-integration-mode analytics coverage
> - `_ssot-rules/03-same-system-principle.md` through `_ssot-rules/10-strategy-instruction-schema-principles.md`
>
> **Out of scope:** actual service implementation, real cost numbers, UAC code changes. This doc specifies; Stage 3E G1
> items ship the spec.

---

## 0. Executive one-screen summary

Four pure functions. One registry. Four consumers. No drift.

```
         ┌────────────────────────── Stage 3B UAC combo registry ──────────────────────────┐
         │  15 dimensions · 22 blocker predicates · 13 entitlement blocks · 4 lock states  │
         └────────────┬──────────────────────────────────────────────────────────┬─────────┘
                      │                                                          │
                      ▼                                                          ▼
         ┌────── Derivation engine (pure functions) ──────┐          ┌── Pricing registry (Stage 2) ──┐
         │  combo(dimensions)                              │◀─reads──│  pricing-building-blocks.md    │
         │  cost(combo, tier, integration_depth)           │          │  (numbers populate later)      │
         │  demo_universe(persona, flavour)                │          └────────────────────────────────┘
         │  prod_restrictions(client, package)             │
         │  access_control(user, route, item, phase)       │
         └────┬───────┬───────┬───────┬───────┬────────────┘
              │       │       │       │       │
              ▼       ▼       ▼       ▼       ▼
        billing · demo · prod entitlement gate · UI visibility · codex scope
```

All four derivations are pure `registry × input_context → result`. No side state. No per-invocation mutation. A given
`(registry_version, input_context)` always produces the same output — the engine is safely cachable and safely diffable
(same inputs across environments produce the same outputs, so staging + prod agree on what a given prospect sees).

---

## 1. The four formulas

### 1.1 `combo(dimensions)` — valid-combo membership

Returns the subset of the Cartesian dimension space that is both mechanically supported and policy-allowed.

```
combo(dimensions) = { d ∈ dimensions :
      valid_cartesian(d)              # mechanical — archetype + venue + instrument_type align
    ∧ ¬ blocked(d)                    # Stage 3B BL-1..BL-22 disjunction
}
```

#### Inputs

| Input        | Type               | Source                                                                     |
| ------------ | ------------------ | -------------------------------------------------------------------------- |
| `dimensions` | `FrozenSet[Tuple]` | Explicit set or enumerated from Stage 3B registry                          |
| `registry`   | `ComboRegistry`    | `unified-api-contracts` loader reading `stage-3b-combo-rules-schema.yaml`  |
| `today`      | `date` (optional)  | Used by time-sensitive blockers (e.g. BL-10 representative-future pending) |

#### Outputs

`FrozenSet[ComboCell]` where each `ComboCell` is a fully-tagged dimension tuple plus the list of blockers it cleared.

#### Worked examples

**Example 1 — canonical DEFI stat-arb PUBLIC slot.**

Input: `{(archetype=STAT_ARB_PAIRS_FIXED, category=DEFI, venue=uniswap_v3, chain=ethereum, instrument_type=spot)}`.

Resolution:

- `valid_cartesian`: ✅ archetype accepts `(DEFI, spot)`; uniswap_v3 supports `spot`.
- Blockers checked: BL-1 (DeFi options) — ignored (not option); BL-8 (DeFi cross-sectional) — archetype is
  `STAT_ARB_PAIRS_FIXED`, not `STAT_ARB_CROSS_SECTIONAL`; BL-20 (bridge latency) — single-chain, no bridge leg.
- **Result:** 1 cell, clears all blockers.

**Example 2 — blocked DeFi options.**

Input: `{(archetype=VOL_TRADING_OPTIONS, category=DEFI, venue=uniswap_v3, chain=ethereum, instrument_type=option)}`.

Resolution:

- `valid_cartesian`: ✅ archetype accepts `option`; uniswap_v3's `supported_instruments` does NOT include `option`.
- `valid_cartesian` fails first. No blocker check needed.
- **Result:** empty set. Rejected for mechanical reason ("venue does not support option"), not a BL-\* rule.

**Example 3 — DeFi perp MM.**

Input:
`{(archetype=MARKET_MAKING_CONTINUOUS, category=DEFI, venue=hyperliquid_dex, chain=hyperliquid, instrument_type=perp)}`.

Resolution:

- `valid_cartesian`: ✅ archetype accepts `(DEFI, perp)`; venue supports `perp`.
- Blockers: BL-7 fires — `archetype==MARKET_MAKING_CONTINUOUS ∧ category==DEFI ∧ instrument_type==perp`.
- **Result:** empty set. `blocked_by = [BL-7]`.

**Example 4 — dated-future rolling slot pending service.**

Input:
`{(archetype=ML_DIRECTIONAL_CONTINUOUS, category=CEFI, venue=deribit, instrument_type=dated_future, slot_label="eth-dated")}`.

Resolution:

- `valid_cartesian`: ✅.
- Blockers: BL-10 fires (`slot_label matches -dated-` ∧ `representative_future_service == not_deployed`).
- **Result:** empty set, with advisory "use `-fixed-{contract}-` label until BL-10 resolves (UAC gap #11)."

#### Owning service

`restriction-profile-service` (new, G1 Stage 3E) OR extension of `strategy-service/availability/`. **Recommendation:
extend `strategy-service/availability/`** — see §5.

#### UI consumption pattern

```typescript
// unified-trading-system-ui/lib/architecture-v2/combo-client.ts
import { useQuery } from "@tanstack/react-query";

export function useValidCombos(filters: DimensionFilter) {
  return useQuery({
    queryKey: ["combo", filters],
    queryFn: () => fetch(`/api/restriction-profile/combo?${params(filters)}`).then((r) => r.json()),
    staleTime: 60_000, // registry read is deterministic per version; 60s cache is safe
  });
}
```

Strategy Catalogue master-matrix page (Phase 10) today uses client-side filtering against a static TS mirror
(`lib/architecture-v2/coverage.ts`). Target: the same page reads from `useValidCombos()`; the TS mirror becomes a
build-time fixture generated from the registry.

---

### 1.2 `cost(combo, tier, integration_depth)` — pricing derivation

Returns the priced line items for a given combo at a given tier, with an optional integration-depth modifier from
rule 10.

```
cost(combo, tier, integration_depth) =
      Σ_{b ∈ combo.blocks} block_price(b, tier, integration_depth)
    + Σ_{p ∈ combo.premiums} premium_price(p, tier)     # Tier B only per rule 08
    - discount_if_applicable(combo, client_contract)     # negotiation outcome, logged
```

where:

```
block_price(b, tier, integration_depth) =
      base(b, tier)
    + integration_depth_uplift(b, integration_depth)
    × sub_scope_multiplier(b, combo.sub_scope)
```

#### Tier enum

Per rule 08 (`_ssot-rules/08-pricing-principles.md`):

| Tier                 | Structure                   | Exclusivity allowed? | Typical use                             |
| -------------------- | --------------------------- | :------------------: | --------------------------------------- |
| `internal`           | Odum-internal cost column   |          —           | Finance / board decks only              |
| `tier_a` (cost-plus) | Usage-variable, thin margin |          ❌          | Prospects ramping, marginal venue packs |
| `tier_b` (fixed)     | Upfront + monthly fixed     |          ✅          | Institutional, core blocks              |

**Rule 08 enforcement:** `cost(...)` returning the `internal` column is only callable by services holding the
`pricing.read_internal` capability claim (Odum finance dashboards, board exports). Any attempt to surface `internal`
column to a client-facing endpoint is a rule-08 violation and gets logged to compliance per rule 07 §#6 enforcement
pattern.

#### Integration-depth extension (rule 10)

Integration depth is a sub-dimension inside blocks 5 (instructions integration) and 7 (execution layer):

| Integration depth               | Meaning                                                                                        | Uplift applies to |
| ------------------------------- | ---------------------------------------------------------------------------------------------- | ----------------- |
| `basic_instruction_integration` | Rule 10 minimal schema — the 8 required fields and little more                                 | Blocks 5, 7       |
| `richer_execution_constraints`  | Rule 10 standard schema — adds scheduling, parent/child grouping, venue restrictions           | Blocks 5, 7       |
| `custom_allocator_handling`     | Rule 10 rich schema — bespoke lifecycle states, proprietary risk dimensions, custom directives | Blocks 5, 7       |

**Depth uplift pattern (Tier A example, illustrative numbers pending finance):**

```yaml
block: 5_instructions_integration
tier_a:
  basic_instruction_integration: 1.0 × base
  richer_execution_constraints: 1.4 × base
  custom_allocator_handling: 2.2 × base # plus block 13 (custom premium) required
```

Rule 08 §"Per-block tier mixability" means a client can sit at `richer_execution_constraints` on block 5 Tier A while
carrying block 7 (execution layer) on Tier B at `custom_allocator_handling` — depth × tier is orthogonal.

#### Inputs

| Input               | Type                                | Source                                                               |
| ------------------- | ----------------------------------- | -------------------------------------------------------------------- |
| `combo`             | `ComboCell`                         | Output of `combo(dimensions)`                                        |
| `tier`              | `Literal[internal, tier_a, tier_b]` | Commercial decision per rule 08                                      |
| `integration_depth` | `IntegrationDepth \| None`          | Rule 10 — applies to blocks 5 & 7 only                               |
| `pricing_registry`  | `PricingRegistry`                   | Stage 2 `commercial-model/pricing-building-blocks.md` once populated |
| `client_contract`   | `ClientContract \| None`            | Optional — for discount application                                  |

#### Outputs

```
PriceQuote:
  lines: list[QuoteLine]        # one per block, sub-scoped
  premiums: list[QuoteLine]     # exclusivity + custom premium if present
  totals:
    upfront: Decimal
    monthly_fixed: Decimal
    monthly_variable_baseline: Decimal
  licensing_constraints: list[LicensingConstraint]   # rule 07 BL-12 warnings
  rule_08_violations: list[Violation]                 # empty if quote is compliant
```

#### Worked examples

**Example 1 — DeFi stat-arb signals-only, hybrid tier.**

Input:
`(combo=signals-only DeFi stat-arb, tier={core: tier_b, marginal_venue: tier_a}, depth=richer_execution_constraints)`.

Blocks in scope (per rule 10 §"Package boundaries"):

- Block 1 (reporting core) @ Tier B
- Block 4 (strategy-service entry) @ Tier B
- Block 5 (instructions integration, depth=richer) @ Tier B — 1.4× base
- Block 7 (execution layer, depth=richer) @ Tier B — 1.4× base
- Block 8 (venue packs × 3: uniswap_v3, aave_v3, hyperliquid_dex — marginal 2 on Tier A, primary on Tier B)
- Block 9 (chain packs: ethereum Tier B, arbitrum Tier A)
- Block 10 (instrument-type packs: perp Tier B, spot Tier B)
- Block 11 (execution-quality analytics on Tier A)

Blocker check: BL-11 passes (signals-only does not include block 6). BL-19 passes (no raw-data framing in the quote).

**Result:** 11 `QuoteLine`s plus a `MixedTierAdvisory` note. Totals roll up correctly.

**Example 2 — IM allocator, reporting-only.**

Input: `(combo=IM reporting-only, tier=tier_b)`.

Per rule 04, this is routed to IM not DART. Blocks in scope:

- Block 1 (reporting core) Tier B
- Block 3 (IM allocator reporting) Tier B
- Block 11 (allocator-specific analytics pack) Tier B

No block 6 / 7 / 8 / 9 / 10 (allocator doesn't operate strategies or execute). Block 2 (regulatory umbrella) excluded —
IM client is not a Reg Umbrella. Block 12 (exclusivity) not requested.

**Result:** 3 `QuoteLine`s. Compact, rule-04-compliant.

**Example 3 — Full DART with exclusivity on Tier A (rule-08 violation).**

Input: `(combo=full DART DeFi, tier=tier_a, premiums=[exclusivity])`.

Resolution: BL-19 check fires — wait, BL-19 is raw-data framing, not exclusivity. Exclusivity violation surfaces via
`rule_08_violations`:

- Rule 08 §"Exclusivity and custom premiums — Tier B only" — `premiums.includes(exclusivity) ∧ tier == tier_a`.

**Result:** `PriceQuote` with empty `lines` + `rule_08_violations = [Rule08Violation("exclusivity_on_tier_a")]` + an
advisory: "Upgrade the covered blocks to Tier B, or drop the exclusivity premium."

**Example 4 — Internal cost leakage guard.**

Input: `(combo=anything, tier=internal)`, caller = client-facing endpoint.

Resolution: caller context lacks `pricing.read_internal` capability → `cost(...)` raises `InternalCostLeakageError`
before reading the registry. Audit log entry created. Per rule 08 §"Internal cost column is codex-private".

**Result:** exception raised, no data surface to the caller. A compliance event fires.

#### Owning service

`pricing-engine-service` (new, Stage 3E G3). Reads `stage-3b-combo-rules-schema.yaml` (dimensions + blockers) +
`commercial-model/pricing-building-blocks.md` (numbers). Access-control layer enforces the `pricing.read_internal` gate.

Until the dedicated service exists, quotes are generated manually from `commercial-model/pricing-building-blocks.md`.
Stage 3E G3 item "pricing-engine service" moves this from doc-lookup to service call.

#### UI consumption pattern

Currently: no UI surface exposes `cost()`. Target (post-Stage-3E G3):

- Internal-only `/admin/pricing/quote-builder` surface for sales ops — calls `cost(combo, tier)` with their
  authenticated token, renders line items, exports PDF.
- Client-facing proposal templates pull priced lines via `cost(combo, tier_a | tier_b)` with client-scoped token; the
  `internal` column is inaccessible from this caller.
- Billing service reconciles monthly against `cost(combo, tier)` output.

---

### 1.3 `demo_universe(persona, flavour)` — visibility-sliced catalogue for demos

Returns the subset of combos + routes a demo prospect sees, keyed off the prospect's persona and the demo flavour
(broader platform / turbo / deep-dive per rule 06).

```
demo_universe(persona, flavour) = combos ∩ demo_restriction_profile(persona, flavour)
```

where:

```
demo_restriction_profile(persona, flavour) =
      default_profile_for(persona.commercial_path)       # rule 06 defaults per path
    ⊕ flavour_overlay(flavour)                            # broader / turbo / deep-dive
    ⊕ explicit_overrides(persona.assigned_profile)        # sales-specified per prospect
```

#### Personas recognised

| Persona            | Commercial path                                     | Default flavour  | Source file                         |
| ------------------ | --------------------------------------------------- | ---------------- | ----------------------------------- |
| `prospect-dart`    | `(Client, downstream)` or `(Client, full-pipeline)` | broader_platform | Stage 3E G1 persona (missing today) |
| `prospect-im`      | IM (Odum, reporting-only)                           | turbo            | ✅ exists in `personas.ts`          |
| `prospect-reg`     | Reg Umbrella                                        | turbo            | Stage 3E G1 persona (missing today) |
| `client-full`      | Post-call full DART                                 | deep_dive        | ✅ exists (Alpha Capital)           |
| `client-data-only` | Post-call data-limited                              | deep_dive        | ✅ exists (Beta Fund)               |
| `client-premium`   | Post-call premium DART                              | deep_dive        | ✅ exists (Vertex Partners)         |
| `admin`            | Odum internal                                       | —                | ✅ exists                           |
| `internal-trader`  | Odum internal                                       | —                | ✅ exists                           |

**Gap:** `prospect-dart` + `prospect-reg` are the two warm-prospect personas Stage 3E G1 must add. Without them there is
no demo coverage for pb3a (Reg Umbrella demo) or pb3c (DART demo).

#### Demo restriction profile structure

```yaml
profile: signals_only_downstream_broader_platform
commercial_path: client_downstream
flavour: broader_platform
visible_blocks:
  - reporting_core # block 1 — fully shown
  - strategy_service_entry # block 4 — restricted view
  - instructions_integration # block 5 — schema surface shown
  - execution_layer # block 7 — shown
  - venue_packs # block 8 — shown for demo-venue subset (binance, uniswap_v3)
  - chain_packs # block 9 — ethereum + arbitrum only
  - instrument_type_packs # block 10 — perp + spot
  - analytics_packs # block 11 — exec quality + reconciliation only
locked_visible_blocks:
  - research_promote_pipeline # block 6 — LOCKED-VISIBLE per rule 06 + rule 10
hidden_blocks:
  - regulatory_umbrella_reporting # block 2 — HIDDEN-ENTIRELY (not the prospect's path)
  - im_allocator_reporting # block 3 — HIDDEN-ENTIRELY
  - exclusivity_premium # block 12 — HIDDEN-ENTIRELY (commercial negotiation)
  - custom_solution_premium # block 13 — HIDDEN-ENTIRELY
visibility_modes:
  - LOCKED_VISIBLE # show with padlock badge, click shows upgrade path
  - HIDDEN_ENTIRELY # not in nav, not reachable
demo_data:
  strategy_slots: [] # filtered below
  slot_filter:
    maturity_floor: BACKTESTED # rule "external visibility ≥ BACKTESTED"
    lock_state_in: [PUBLIC] # prospects never see IM_RESERVED or CLIENT_EXCLUSIVE
    data_license_tier_max: odum_proprietary # rule 07 — no institutional_only raw
```

#### Inputs

| Input              | Type                                                  | Source                                          |
| ------------------ | ----------------------------------------------------- | ----------------------------------------------- |
| `persona`          | `Persona` (id + commercial_path + explicit overrides) | JWT claims (Stage 3E G2) or persona fixture     |
| `flavour`          | `Literal[broader_platform, turbo, deep_dive]`         | Sales-configured per prospect                   |
| `profile_registry` | `DemoProfileRegistry`                                 | Stage 2 `demo-ops/demo-restriction-profiles.md` |

#### Outputs

```
DemoUniverse:
  visible_combos: FrozenSet[ComboCell]
  locked_visible_combos: FrozenSet[ComboCell]    # rendered with padlock chip
  hidden_combos: FrozenSet[ComboCell]            # not in nav
  visible_routes: list[RouteDescriptor]
  locked_visible_routes: list[RouteDescriptor]
  hidden_routes: list[RouteDescriptor]
  demo_data_filter: SlotFilter                   # applied to catalogue queries
  rule_06_violations: list[Violation]            # e.g. leak of CLIENT_EXCLUSIVE into prospect view
```

#### Worked examples

**Example 1 — DART warm-prospect, broader-platform flavour.**

Input: `persona=prospect-dart`, `flavour=broader_platform`.

Resolution:

- Default profile for `(Client, downstream)` applied — blocks 1/4/5/7/8/9/10/11 visible.
- `flavour_overlay(broader_platform)` — exposes wider route surface (adds `/services/trading/terminal`,
  `/services/observe/health` read-only).
- Block 6 (research/promote) → LOCKED-VISIBLE per rule 06 × rule 10 (BL-13).
- Slot filter: maturity ≥ BACKTESTED, lock_state ∈ {PUBLIC}, data_license_tier ≤ odum_proprietary (so no
  institutional-only raw surfaces even if the slot is PUBLIC).

**Result:** ~85 of ~130 representative slots visible, ~10 LOCKED-VISIBLE (research/promote cells), ~35 hidden
(exclusivity/custom/ Reg Umbrella / IM paths).

**Example 2 — IM prospect, turbo flavour.**

Input: `persona=prospect-im`, `flavour=turbo`.

Resolution:

- Default profile for IM reporting-only — blocks 1 + 3 + 11 visible.
- `flavour_overlay(turbo)` — narrow surface, deep; exposes `/services/reports/overview` +
  `/services/reports/executive` + `/services/reports/pnl-attribution` only. `/services/strategy-catalogue`,
  `/services/data`, `/services/research` all hidden.
- Slot filter: maturity = LIVE_ALLOCATED only (allocators see live, not research).

**Result:** ~6 routes visible, 0 LOCKED-VISIBLE, rest hidden. ~30 Odum-run live strategies visible as aggregate (no
per-client attribution).

**Example 3 — Reg Umbrella prospect, turbo flavour.**

Input: `persona=prospect-reg`, `flavour=turbo`.

Resolution:

- Default profile for Reg Umbrella — blocks 1 + 2 + 7 + 8 + 10 visible (reporting core + regulatory umbrella reporting +
  execution layer — Reg Umbrella clients DO operate execution under Odum's permissions — + venue packs for their
  regulated activity + instrument-type packs).
- `flavour_overlay(turbo)` — deep-focus on `/services/reports/reconciliation`, `/services/reports/best-ex`,
  `/services/reports/transaction-reporting`.
- Blocks 3 (IM allocator) + 6 (research/promote) → HIDDEN-ENTIRELY (not a plausible next step for Reg Umbrella).
- Block 12 (exclusivity) → HIDDEN-ENTIRELY.

**Result:** ~12 routes visible, mostly reporting-focused. Regulatory-filing surfaces get pride of place.

**Example 4 — admin persona (no demo profile applies).**

Input: `persona=admin`, `flavour=None`.

Resolution: `admin` is not a demo persona; `demo_restriction_profile(admin, *) = ALL_COMBOS` by short-circuit. Admin
sees everything including `CLIENT_EXCLUSIVE` and `CODE_NOT_WRITTEN` maturities. Rule 06 §"Enforcement rules" #6:
production entitlements enforce — admin's entitlement is `*`.

**Result:** full universe. Used for Stage 3D "admin view" screenshot.

#### Owning service

Same service as `combo()` (§5 recommendation: `strategy-service/availability/` extension). The
`demo_restriction_profile(persona, flavour)` lookup comes from Stage 2 `demo-ops/demo-restriction-profiles.md` parsed
into a registry; the intersection with `combo(dimensions)` is a pure set operation at the same service.

#### UI consumption pattern

Today: UI relies on a 12-line hardcoded cascade in
[`components/shell/lifecycle-nav.tsx:102-113`](../../../../unified-trading-system-ui/components/shell/lifecycle-nav.tsx#L102-L113).

Target:

```typescript
// unified-trading-system-ui/components/shell/use-demo-universe.ts
export function useDemoUniverse() {
  const { persona, flavour } = useDemoContext();
  return useQuery({
    queryKey: ["demo-universe", persona.id, flavour],
    queryFn: () => fetchDemoUniverse(persona.id, flavour),
    staleTime: 300_000,
  });
}

// Usage in nav / page guards:
const { data: universe } = useDemoUniverse();
const isVisible = universe?.visible_routes.some((r) => r.path === currentPath);
const isLocked = universe?.locked_visible_routes.some((r) => r.path === currentPath);
if (!isVisible && !isLocked) redirectTo404();
```

`LOCKED-VISIBLE` is rendered via a new `<ServiceTile variant="locked">` component that shows a padlock chip +
explanatory tooltip ("Available in full DART — contact sales") — Stage 3E G1 refactor item.

---

### 1.4 `prod_restrictions(client, package)` — paying-client entitlement gate

Returns the production catalogue a paying client actually has access to, based on their signed package.

```
prod_restrictions(client, package) = combos ∩ paid_entitlements(client, package)
```

where:

```
paid_entitlements(client, package) =
      included_blocks(package)                  # Per rule 05 composition per commercial path
    × sub_scopes(package)                        # venue / chain / instrument-type sub-scoping
    × tier(package)                              # Tier A or Tier B per block
    × rule_04_axis(package)                      # resolved (strategy_origin × stack_depth)
    ∩ (if client.lock_state == CLIENT_EXCLUSIVE: { slot.exclusive_client_id == client.id })
    ∩ (slot.maturity ≥ EXTERNAL_VISIBILITY_THRESHOLD if client.audience_in_{saas, im, reg})
```

#### Inputs

| Input                   | Type                           | Source                                                                    |
| ----------------------- | ------------------------------ | ------------------------------------------------------------------------- |
| `client`                | `ClientContext`                | JWT claims: `org_id`, `client_id`, `fund_id`, `business_unit`, `audience` |
| `package`               | `ClientPackage`                | Signed contract state — blocks, sub_scope, tier per block                 |
| `availability_registry` | `StrategyAvailabilityRegistry` | UAC gap #12 shipped (Phase 10.5) — already live                           |

#### Outputs

```
ProductionRestrictions:
  entitled_combos: FrozenSet[ComboCell]
  entitled_routes: list[RouteDescriptor]
  entitled_analytics: list[AnalyticsCapability]  # per stage-3b-downstream-analytics matrix
  denials: list[DenialReason]                    # if any combo rejected with reason
  licensing_violations: list[LicensingViolation] # rule 07 BL-12 / BL-19 hits
```

#### Worked examples

**Example 1 — signals-only client, routine allocator call.**

Input: `client=(org_id=beta_fund, audience=trading_platform_subscriber, business_unit=saas)`,
`package=(blocks=[1,4,5,7,8(uniswap+aave+hl),9(eth+arb),10(perp+spot),11(exec_quality)], tier=tier_b_core, integration_depth=richer)`.

Resolution:

- Included blocks per package: 1/4/5/7/8/9/10/11 ✓; block 6 not in package → BL-11 firing avoided because the client
  cannot even request block-6-backed slots.
- Combo set: all DEFI stat-arb cells venue ∈ {uniswap, aave, hyperliquid_dex}, chain ∈ {eth, arb}, instrument_type ∈
  {perp, spot}, with maturity ≥ BACKTESTED and lock_state = PUBLIC. ~42 cells.
- BL-14 (CLIENT_EXCLUSIVE mismatch): no CLIENT_EXCLUSIVE slots in this client's entitlement → no hits.
- BL-22 (org-scope mismatch on exclusive allocation): no CLIENT_EXCLUSIVE in scope → no hits.
- BL-17 (LIVE_TINY cap): any LIVE_TINY slots in scope apply the notional cap automatically.

**Result:** 42 entitled combos, 19 routes, 9 entitled analytics (exec quality subset of block 11). Clean `denials` list.

**Example 2 — IM desk member querying across funds.**

Input: `client=(org_id=odum_internal, audience=im_desk, business_unit=im_desk, fund_id=<null>)`,
`package=<internal, all-blocks>`.

Resolution:

- Audience `im_desk` → sees all IM-reserved slots across all funds.
- Per MEMORY `validate_allocation_authorised(slot, fund_id, business_unit)` — `business_unit=im_desk` authorises reads
  across all IM fund_ids.
- CLIENT_EXCLUSIVE slots: IM desk sees them (they're an Odum-internal observer on behalf of the client).

**Result:** full universe with IM_RESERVED + CLIENT_EXCLUSIVE visible. Allocation actions still gated per-fund by
`business_unit` check.

**Example 3 — Reg Umbrella client operating under Odum FCA permissions.**

Input:
`client=(org_id=emerging_mgr_1, audience=reg_umbrella_client, business_unit=saas, reserving_business_unit_id=ru_fund_7)`,
`package=(blocks=[1,2,7,8(ibkr,cme),10(spot,dated_future)], tier=tier_b)`.

Resolution:

- Block 2 (regulatory umbrella reporting) IN SCOPE — regulatory filing surfaces entitled.
- No block 3 → IM allocator reporting hidden.
- No block 6 → research/promote pipeline hidden.
- Slot filter: maturity ≥ BACKTESTED, lock_state = PUBLIC. Per rule 04 §"Hybrid engagements" — Reg Umbrella CAN combine
  with signals-only DART; tracked as separate commercial engagement.

**Result:** ~14 entitled combos (narrow, TradFi + reporting), ~11 entitled routes. Regulatory filing surfaces prominent.

**Example 4 — retired slot allocation attempt (BL-15).**

Input: `client=(<existing>, package=<existing>)`, action request = `allocate(slot_label=retired_slot)`.

Resolution:

- Slot `retired_slot.lock_state == RETIRED` → BL-15 fires in `allocate(...)` wrapper.
- `ProductionRestrictions.denials.append(DenialReason("LOCK_STATE_RETIRED", slot_label))`.
- Existing positions wind down; no new capital flow.

**Result:** allocation rejected; `denials` populated.

#### Owning service

Same service as §1.1 and §1.3 (see §5 recommendation). The `paid_entitlements` map comes from the billing /
contract-management layer (Stage 3E G2 "contract management" — not yet scoped); until then it is read from a fixture
file per-client.

#### UI consumption pattern

Client reporting tool (`/services/reports/overview`) filters its queries by
`prod_restrictions(current_client, their_package)`; catalogue pages filter listings similarly. The derivation is
server-side (trust boundary) — the UI renders what the API returns and never makes its own restriction decisions.

---

### 1.5 `access_control(user, route, item, phase)` — phase-aware route gate

Decides whether a given `user` can reach a given `route` rendering a given `item` in a given lifecycle `phase`. This is
the per-request gate that runs on every navigation.

```
access_control(user, route, item, phase) =
      visible(user, combo(item))
    ∧ phase ∈ allowed_phases(user.entitlements)
    ∧ ¬ rule_06_explicit_hide(user, route, item)
```

where:

```
visible(user, combo) =
      if user.audience == admin:
          True
      elif combo ∈ prod_restrictions(user.client, user.package):
          True
      elif combo ∈ demo_universe(user.persona, user.flavour).visible_combos:
          True
      elif combo ∈ demo_universe(user.persona, user.flavour).locked_visible_combos:
          "LOCKED_VISIBLE"
      else:
          False

allowed_phases(entitlements) =
      {live} always                                                         # every paying user sees live
    ∪ ({research} if entitlements.includes(block_6_research_promote))
    ∪ ({paper}    if entitlements.includes(block_6_research_promote) ∨ entitlements.includes(paper_surface))
```

#### Why phase-aware

Rule 03 sub-claim (b–e) requires: `research ≡ live` infrastructure, terminal as live/batch toggle, catalogue rows carry
phase tags, paper has same look-and-feel as live. This collapses into: **there is no `/research/backtests` or `/paper/*`
fork; phase is a data-source binding, not a URL prefix.** `access_control(..., phase)` is where that policy is
mechanically enforced — a researcher persona with block-6 entitlement can flip `phase=research` on
`/services/trading/terminal` and see the component tree rebind to historical data; a trader without block 6 gets
`phase=live` only.

#### Inputs

| Input   | Type                             | Source                                                             |
| ------- | -------------------------------- | ------------------------------------------------------------------ |
| `user`  | `UserContext`                    | JWT claims (audience, entitlements, persona)                       |
| `route` | `str` (path)                     | Request URL                                                        |
| `item`  | `ComboCell \| None`              | If the route renders a specific slot/instrument/chain; else `None` |
| `phase` | `Literal[research, paper, live]` | Query param / session default / user preference                    |

#### Outputs

```
AccessDecision:
  status: Literal[allow, locked_visible, deny, deny_phase]
  reason: str              # e.g. "BL-14: slot.lock_state=CLIENT_EXCLUSIVE, mismatch org_scope"
  upgrade_hint: str | None # e.g. "Block 6 (research/promote) required for research phase"
```

#### Worked examples

**Example 1 — DART signals-only client requests research phase on their own slot.**

Input: `user=(audience=trading_platform_subscriber, entitlements=[block_1,4,5,7,8,9,10,11])`,
`route=/services/strategy-catalogue/strategies/STAT_ARB_PAIRS_FIXED/eth-usdc`, `item=<that slot>`, `phase=research`.

Resolution:

- `visible(user, combo)` ✓ (entitled).
- `allowed_phases(entitlements)`: block 6 NOT in entitlements → allowed_phases = {live}.
- `phase=research ∉ {live}` → **status=`deny_phase`**.
- `upgrade_hint = "Research phase requires block 6 (research/promote pipeline) — upgrade to full-DART."`

**Result:** 403 with actionable error. UI renders a LOCKED-VISIBLE chip on the phase selector rather than hiding it
(rule 06 preferred mode).

**Example 2 — Researcher persona on a LIVE_ALLOCATED slot.**

Input: `user=(audience=im_desk, entitlements=[*])`,
`route=/services/strategy-catalogue/strategies/CARRY_BASIS_PERP/btc`, `item=<slot maturity=LIVE_ALLOCATED>`,
`phase=research`.

Resolution:

- `visible` ✓ (im_desk sees everything).
- `allowed_phases = {live, research, paper}` (im_desk entitlement includes block 6).
- `phase=research ∈ allowed_phases` → **status=`allow`**.
- Terminal / catalogue / reports components rebind to historical data source — NO fork in component tree.

**Result:** allow; UI renders the same slot view with `phase=research` binding.

**Example 3 — Demo prospect hits LOCKED-VISIBLE block-6 surface.**

Input: `user=(persona=prospect-dart, flavour=broader_platform)`, `route=/services/strategy-catalogue/promote`,
`item=None`, `phase=live`.

Resolution:

- `visible(prospect-dart, research_promote_combo)` — combo is in `locked_visible_combos` per §1.3 example 1.
- → **status=`locked_visible`**.
- UI renders the nav item with a padlock chip; clicking shows the upgrade-path explanation.

**Result:** not 403; LOCKED-VISIBLE rendering. The prospect knows the surface exists and what it would cost.

**Example 4 — CLIENT_EXCLUSIVE slot accessed by wrong org.**

Input: `user=(org_id=beta_fund, audience=trading_platform_subscriber)`, `route=/services/strategy-catalogue/...`,
`item=<slot lock_state=CLIENT_EXCLUSIVE, exclusive_client_id=alpha_capital>`, `phase=live`.

Resolution:

- BL-14 fires:
  `slot.lock_state=CLIENT_EXCLUSIVE ∧ viewer.org_scope=beta_fund ≠ slot.exclusive_client_id=alpha_capital ∧ viewer.org_scope ≠ odum_internal`.
- `visible(...) = False`.
- → **status=`deny`**. `reason = "BL-14: CLIENT_EXCLUSIVE slot not in viewer scope"`.

**Result:** 404 (HIDDEN-ENTIRELY — per rule 06, out-of-audience CLIENT_EXCLUSIVE is hidden not locked, to avoid leaking
that Alpha Capital has an exclusive).

**Example 5 — Paper-phase access.**

Input: `user=(audience=trading_platform_subscriber, entitlements=[..., paper_surface])`,
`route=/services/trading/terminal`, `item=None`, `phase=paper`.

Resolution:

- `visible` ✓.
- `allowed_phases = {live, paper}` (paper_surface entitlement; no block 6 → no research).
- `phase=paper ∈ allowed_phases` → **status=`allow`**.
- Terminal rebinds to current live data + simulated fills via execution-service matching engine. Same UI as live mode.

**Result:** allow; component tree unchanged, phase chip reads "PAPER".

#### Owning service

Same service (see §5). Implemented as a middleware running on every authenticated request; returns `AccessDecision` in
~2ms (P99) backed by a cached registry read.

#### UI consumption pattern

Middleware runs in the API layer; UI reads `AccessDecision` from the response envelope and renders accordingly. A
`<PhaseToggle>` component shows all three phases, greying out / LOCKED-VISIBLE-ing any phase the user isn't entitled to.

---

## 2. Registry shape — what Stage 3B feeds into Stage 3C

The four functions all read from the same logical registry:

```
ComboRegistry = {
  dimensions: {
    category: {enum}
    venue: {per-venue object with capability flags}
    chain: {enum}
    instrument_type: {enum}
    strategy_archetype: {enum × valid_pairs × supported_venues}
    feature_group: {string opaque}
    model_family: {string opaque}
    exec_algo: {string opaque}
    entitlement: {13 blocks × sub_scope}
    lock_state: {4 values}
    maturity: {8 values}
    lifecycle_phase: {3 values — research / paper / live}
    org_scope: {string}
    fund_structure: {POOLED | SMA}
    data_license_tier: {3 values}
    instruction_schema_fit: {3 values × schema_depth sub-dim}
  }
  blockers: [BL-1 … BL-22]
  price_table: {block × tier × integration_depth} → {upfront, monthly, usage_variable}  # Stage 2
  demo_profiles: {persona × flavour} → {visible_blocks, locked_visible_blocks, hidden_blocks}  # Stage 2
  slot_index: {slot_label → ComboCell + lock_state + maturity + exclusive_client_id}  # Phase 10.5 shipped
}
```

Loaded from `unified-api-contracts/unified_api_contracts/registry/combo_registry.py` (not yet written; Stage 3E G1
item). A YAML fixture version lives at `stage-3b-combo-rules-schema.yaml` for tests.

---

## 3. Input feeds — where each formula reads from

| Formula             | Reads                                                                                                        |
| ------------------- | ------------------------------------------------------------------------------------------------------------ |
| `combo`             | Stage 3B dimensions + blockers                                                                               |
| `cost`              | Stage 3B (blocks + rule-07/08 gates) + Stage 2 `pricing-building-blocks.md` numbers + integration_depth tier |
| `demo_universe`     | Stage 3B (combos + block structure) + Stage 2 `demo-restriction-profiles.md` + persona registry              |
| `prod_restrictions` | Stage 3B + Phase 10.5 `StrategyAvailabilityRegistry` + contract-management paid_entitlements                 |
| `access_control`    | Outputs of the above 3 + JWT claims + route metadata                                                         |

---

## 4. Output consumers — where each result flows

| Consumer                          | Reads                                                    |
| --------------------------------- | -------------------------------------------------------- |
| Billing service                   | `cost(combo, tier, depth)` — Tier A/B columns            |
| Odum finance dashboards           | `cost(combo, tier=internal, depth)`                      |
| Demo-provisioning service         | `demo_universe(persona, flavour)`                        |
| Production entitlement middleware | `prod_restrictions(client, package)`                     |
| UI visibility / route-gate layer  | `access_control(user, route, item, phase)`               |
| Codex documentation surfaces      | `combo(all_dimensions) ∩ codex_scope(audience)`          |
| Compliance audit trail            | Rule 07 / Rule 08 violation events from any of the above |

---

## 5. Owning-service recommendation

### Option A — Extend `strategy-service/availability/`

**Pro:**

- `StrategyAvailabilityRegistry` (UAC gap #12) already shipped here — the closest existing code to the derivation
  surface.
- Already has thread-safe store + audit-event emission (5 UTL events).
- `validate_allocation_authorised()` already does audience-+-business_unit gating.
- Single-service ownership avoids a micro-service proliferation.

**Con:**

- `strategy-service` scope broadens from "run strategies" to "run strategies + answer meta-questions about combos and
  pricing and demo universes". Arguably becomes a god-service.
- Pricing logic (`cost()`) reads finance-sensitive data; mixing that into a runtime service increases the blast radius
  of any strategy-service bug.

### Option B — New `restriction-profile-service`

**Pro:**

- Single-responsibility: own the derivation registry + the four functions. Small surface, testable.
- Pricing-engine logic isolates cleanly from strategy-execution logic.
- Can be horizontally scaled independently (the four functions are pure reads; a restriction service can handle much
  higher RPS than strategy-service).

**Con:**

- Another service to run / deploy / monitor.
- `strategy-service/availability/` already covers part of the surface — duplicating or migrating costs.
- Cross-service calls for every `access_control(...)` decision; adds latency (mitigatable with cache).

### Recommendation

**Extend `strategy-service/availability/` — NOT a new micro-service.**

Reasoning:

1. The Phase 10.5 work (2026-04-19, `strategy-service 7e0b6a4`) already commits to `strategy_service/availability/` as
   the home for registry + audience filters + lock-state enforcement. Moving it breaks that recent shipping decision.
2. Pricing (`cost()`) is the only function with an arguable separation case. Ship it as a distinct sub-package
   (`strategy_service/availability/pricing/`) with its own capability-gated API, not a distinct service. That isolates
   pricing internals without a new deployment.
3. The CLAUDE.md "system-first architecture" rule explicitly prohibits inventing new services when an existing one
   covers the domain. `strategy-service/availability/` is the existing one.
4. Future mitigation if the service becomes too broad: split THEN, when load and team patterns justify it. Don't
   pre-split.

### Concrete target sub-package layout

```
strategy-service/
└── strategy_service/
    └── availability/
        ├── store.py                     # Phase 10.5 shipped
        ├── watchdog.py                  # Phase 10.5 shipped
        ├── audience_filters.py          # Phase 10.5 shipped
        ├── events.py                    # Phase 10.5 shipped (5 UTL events)
        ├── combo.py                     # NEW: valid_combo + blocker evaluation (§1.1)
        ├── pricing/                     # NEW: cost() — capability-gated
        │   ├── __init__.py
        │   ├── engine.py                # cost(combo, tier, depth)
        │   ├── integration_depth.py     # rule 10 depth uplift
        │   └── compliance.py            # rule 07 / 08 violation logging
        ├── demo_universe.py             # NEW: demo_universe() (§1.3)
        ├── prod_restrictions.py         # NEW: prod_restrictions() (§1.4)
        └── access_control.py            # NEW: access_control() phase-aware middleware (§1.5)
```

### API surface

Internal Python API (called from other services):

```python
from strategy_service.availability import (
    valid_combos,
    cost,
    demo_universe,
    prod_restrictions,
    access_control,
)
```

HTTP surface for UI + billing (new `strategy-service/api/restriction_profile_router.py`):

```
GET  /api/restriction-profile/combo?archetype=&category=&venue=&chain=&instrument_type=
GET  /api/restriction-profile/cost?combo_id=&tier=&depth=          # capability-gated for tier=internal
GET  /api/restriction-profile/demo-universe?persona_id=&flavour=
GET  /api/restriction-profile/prod-restrictions                     # reads authenticated client from JWT
POST /api/restriction-profile/access-control                        # body: {route, item, phase}
```

All endpoints are pure reads; responses are cachable per `(registry_version, input)`.

---

## 6. Cachability model

All four functions are side-effect-free. Cache key: `sha256(registry_version || input_context)`.

| Cache level             | TTL                        | Invalidation                          |
| ----------------------- | -------------------------- | ------------------------------------- |
| In-process LRU (Python) | 300 s                      | Registry version bump                 |
| Redis (per org_id)      | 600 s                      | `STRATEGY_AVAILABILITY_CHANGED` event |
| UI (React Query)        | 60 s (combo), 300 s (demo) | Page navigation + manual refetch      |

Registry version bump = new `stage-3b-combo-rules-schema.yaml` release OR new `StrategyAvailabilityEntry` mutation.
Every mutation emits a UTL event that propagates to cache invalidation.

---

## 7. Verification matrix — how Stage 3C integration tests prove soundness

| Property                                                    | Test approach                                                                     |
| ----------------------------------------------------------- | --------------------------------------------------------------------------------- |
| Four functions read the same registry                       | Shared fixture; mutate fixture, assert all four outputs change consistently       |
| Idempotent                                                  | Call × N with same input → same output                                            |
| BL-1..BL-22 blockers fire exactly when predicate holds      | Parameterised test per blocker                                                    |
| Integration-depth uplift applies to blocks 5 + 7 only       | Property-test: other blocks unaffected by depth param                             |
| Rule 08 internal-cost leakage guard                         | Test: caller without `pricing.read_internal` claim → exception                    |
| Rule 07 raw-data framing guard                              | Test: BL-19 fires on any Tier A quote with framing=`raw_data_feed`                |
| Phase-aware access control                                  | Test: researcher persona with block 6 can flip phase=research                     |
| LOCKED-VISIBLE vs HIDDEN-ENTIRELY                           | Test: CLIENT_EXCLUSIVE → hidden; block 6 for signals-only → locked_visible        |
| External-visibility maturity threshold                      | Test: BACKTESTED visible to SaaS, CODE_WRITTEN hidden                             |
| Same-system: phase changes data binding, not component tree | UI smoke test: `/services/trading/terminal?phase=research` renders same component |

---

## 8. Cross-references

- [`stage-3a-current-infra-audit.md`](stage-3a-current-infra-audit.md) — the gap surface this engine fills
- [`stage-3b-uac-combo-rules.md`](stage-3b-uac-combo-rules.md) — dimensions + blockers
- [`stage-3b-combo-rules-schema.yaml`](stage-3b-combo-rules-schema.yaml) — registry shape
- [`stage-3b-instruction-schema-contract.md`](stage-3b-instruction-schema-contract.md) — rule 10 schema integration
- [`stage-3b-downstream-analytics-capability-matrix.md`](stage-3b-downstream-analytics-capability-matrix.md) — analytics
  availability by integration mode
- [`stage-3e-refactor-plan.md`](stage-3e-refactor-plan.md) — G1 item "derivation engine — ship to
  `strategy-service/availability/`"
- [`../_ssot-rules/03-same-system-principle.md`](../../14-customer-journeys/_ssot-rules/03-same-system-principle.md) —
  phase-aware access control rationale
- [`../_ssot-rules/06-show-dont-show-discipline.md`](../../14-customer-journeys/_ssot-rules/06-show-dont-show-discipline.md)
  — LOCKED-VISIBLE vs HIDDEN-ENTIRELY semantics
- [`../_ssot-rules/08-pricing-principles.md`](../../14-customer-journeys/_ssot-rules/08-pricing-principles.md) —
  `cost(...)` tier structure
- [`../_ssot-rules/10-strategy-instruction-schema-principles.md`](../../14-customer-journeys/_ssot-rules/10-strategy-instruction-schema-principles.md)
  — integration-depth uplift extension
- [`../../09-strategy/architecture-v2/cross-cutting/strategy-availability-and-locking.md`](../../09-strategy/architecture-v2/cross-cutting/strategy-availability-and-locking.md)
  — availability registry spec
