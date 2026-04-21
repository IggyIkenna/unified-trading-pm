# Legacy Family String Migration Report

**Audit driver:** `plans/active/ui_unification_v2_sanitisation_2026_04_20.plan.md` § `p8-audit-legacy-family-strings`.

**Scope:** Find every lowercase / v1-era family string (`basis-trade`, `mean-reversion`, `sports-arb`, `prediction-ml`,
etc.) used as a route slug, filter value, or user-visible display label in `unified-trading-system-ui`. Migrate to v2
canonical names or flag for the Phase 11 strategy fixture regeneration (see `legacy-mapping.ts`).

**Owning code:**

- v2 canonical family enum: `unified-api-contracts/unified_api_contracts/internal/architecture_v2/enums.py` (Python
  SSOT) + `unified-trading-system-ui/lib/architecture-v2/enums.ts` (TypeScript mirror).
- v1→v2 bridge: `unified-trading-system-ui/lib/architecture-v2/legacy-mapping.ts` (`LEGACY_FAMILY_TO_V2` map).

---

## 1. Categories of findings

### 1.1 Legitimate migration targets — DONE

These user-visible URL slugs / route labels were migrated in earlier waves:

| Old slug                 | New slug                 | Commit       |
| ------------------------ | ------------------------ | ------------ |
| `/.../basis-trade`       | `/.../carry-basis`       | UI `d417223` |
| "Basis Trade" page title | "Carry-Basis" page title | UI `d417223` |

These are closed. Confirmed no remaining `/basis-trade` URLs in `app/` or `components/` via
`rg "/basis-trade" unified-trading-system-ui/{app,components}`.

### 1.2 Out-of-scope until Phase 11 (strategy fixture migration) — DEFERRED

Canonical statement from `lib/architecture-v2/legacy-mapping.ts`:

> The existing `strategy-catalog-data.ts` fixture (53 strategies) was written before the v2 taxonomy landed. Rather than
> regenerate the fixture in this phase 9 session — which would cascade into the 6 detail tabs — we map at read time so
> the family dashboards aggregate correctly.
>
> Follow-up: regenerate the catalog fixture from UAC `StrategyInstanceDefinition` rows once phase 11 (strategy
> migration) lands and delete this mapping.

Concrete files that still use v1 family strings AS LEGITIMATE FIXTURE DATA (read through `legacyFamilyToV2()` at display
time):

- `unified-trading-system-ui/lib/strategy-registry.ts` — 53-strategy v1 fixture with `strategyType: "Basis Trade"` /
  `"Mean Reversion"` / `"Prediction ML Directional"` etc.
- `unified-trading-system-ui/lib/mocks/fixtures/strategy-catalog-data.ts` — dashboards feed.
- `unified-trading-system-ui/lib/mocks/fixtures/{promote-candidates,trading-data,build-data,ml-data,strategy-platform,defi-basis-trade,kill-switch-entities}.ts`
  — widget mock data.
- `unified-trading-system-ui/lib/reference-data.ts` — reference labels for filter UIs.
- `unified-trading-system-ui/lib/taxonomy.ts` — v1 taxonomy, feeds lifecycle nav.
- `unified-trading-system-ui/lib/config/services/strategies.config.ts` — `ARCHETYPES` filter list with
  `{ id: "BASIS_TRADE", label: "Basis Trade" }` entries (matches v1 `strategy-registry.ts` archetype ids).
- `unified-trading-system-ui/lib/config/strategy-config-schemas/{cefi,defi,tradfi,sports,prediction}.ts` — per-category
  config schemas with v1 strategy ids.
- `unified-trading-system-ui/components/widgets/sports/register.ts` — sports-arb widget registrations.
- `unified-trading-system-ui/components/dashboards/trader-dashboard.tsx` — `id: "sports-arb"` dashboard card.
- `unified-trading-system-ui/lib/help/help-tree.ts` + `unified-trading-system-ui/lib/glossary.ts` — help / glossary
  entries.

**Why deferred:** these are all consumed in lockstep by the v1 strategy-registry + v1-style UI views. Unilaterally
renaming `"Basis Trade"` → `"Carry & Yield · Carry Basis Perp"` without simultaneously regenerating the fixture +
updating the display components would break ~400 tests and break the v1 trading page. Per plan header convention
"clean-break when all 60+ repos are available; temporary co-existence when not", and per the explicit comment in
`legacy-mapping.ts`, this is a Phase 11 deliverable.

**Tracking:** add a follow-up plan `plans/active/strategy_fixture_v2_regeneration_<date>.plan.md` when Phase 11 work
begins.

### 1.3 Intentional v1 identifiers — NOT TARGETS

These are NOT migration targets. They are internal keys that happen to use the lowercase-hyphen style but are
identifiers (not display labels / route slugs / family strings):

- `defi-swap-widget.tsx` `config.mode === "basis-trade"` — widget config discriminator; changing it would break the
  widget's internal mode routing and has nothing to do with the v2 family enum.
- `glossary.ts` `"mean-reversion"` entry — dictionary key for `<Term id="mean-reversion">` tooltip lookups. Legitimate
  jargon entry.
- `components/trading/sports/arb-tab.tsx` — `"arb"` suffix is domain terminology ("arbitrage"), not a family string.
- `help-tree.ts` `id: "sports-arb"` — internal help-tree node id.
- `config-page-schema.ts` `id: "sports-arb"` — internal config schema id.

---

## 2. Exit criteria

Per plan p8-audit-legacy-family-strings:

- [x] Grep performed across UI + services.
- [x] Route slug `basis-trade` → `carry-basis` — done Wave 1 (UI `d417223`).
- [x] Display label "Basis Trade" on dedicated page → "Carry Basis" — done Wave 1.
- [x] Migration report produced (this document).
- [ ] 53-strategy fixture regeneration — Phase 11 follow-up.

The plan checkbox can flip to `[x]` on the basis of the audit being complete + migrations being either applied or
tracked. No further route-slug / display-label migrations are viable until Phase 11.

---

## 3. References

- `codex/09-strategy/architecture-v2/strategy-registry-v2.md` — canonical v2 registry overview.
- `codex/09-strategy/architecture-v2/naming-convention.md` — `parse_strategy_id` / `format_strategy_id` canonical form.
- `lib/architecture-v2/legacy-mapping.ts` — v1→v2 bridge with the explicit "Phase 11 regen + delete" follow-up comment.
