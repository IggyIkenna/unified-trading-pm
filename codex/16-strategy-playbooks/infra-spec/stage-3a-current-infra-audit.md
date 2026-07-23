---
doc_type: codex-ssot
title: Stage 3A — Current-infra audit
summary: >-
  Point-in-time (2026-04-20) audit of the shipped 177-route UI vs SSOT-grade integrity — 4 debt axes (11/12 UAC gaps
  unshipped, 4 asymmetric catalogue services, flat-string entitlements, single-env demo provisioning) plus the
  13-building-block Exists/Gap/Blocker table; baseline for Stage 3B/3C/3D/3E. DELTA 2026-05-22: re-run the §2.3/§3 greps
  before treating as current-state.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos:
  [
    deployment-api,
    execution-service,
    features-service,
    strategy-service,
    unified-api-contracts,
    unified-trading-system-ui,
  ]
scope: [engineer, admin]
tags: [audit, ui, uac, ssot-audit, docspec, refactor]
related:
  [
    /codex/16-strategy-playbooks/infra-spec/stage-3b-uac-combo-rules.md,
    /codex/16-strategy-playbooks/infra-spec/stage-3c-derivation-engine.md,
    /codex/16-strategy-playbooks/infra-spec/stage-3e-refactor-plan.md,
    /codex/09-strategy/architecture-v2/uac-registry-gaps.md,
  ]
created: 2026-04-20
authoritative_for:
  [Stage 3A current-infra audit snapshot (2026-04-20 UI + UAC-gap + entitlement + demo-provisioning baseline)]
referenced_by:
  [
    /codex/14-customer-journeys/presentations/target-experience-post-refactor.md,
    /codex/16-strategy-playbooks/infra-spec/stage-3c-derivation-engine.md,
    /codex/16-strategy-playbooks/infra-spec/stage-3e-refactor-plan.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Stage 3A — Current-infra audit

> **Parent plan:**
> [`plans/ai/playbook_ssot_stage_3_infra_spec_2026_04_19.plan.md`](../../../plans/ai/playbook_ssot_stage_3_infra_spec_2026_04_19.plan.md).
> **Scope:** Ship a single paste-able snapshot of what already exists in the workspace that the playbook SSOT can depend
> on, and what needs to be built before the one-registry-four-derivations engine (Stage 3C) can land.
>
> Authoritative inputs:
> [`_ssot-rules/_source-v1-feedback.md`](../../14-customer-journeys/_ssot-rules/_source-v1-feedback.md) (rule 05
> building-block list), [`page-triage/triage-matrix.md`](../../14-customer-journeys/page-triage/triage-matrix.md)
> (177-page classification), [`page-triage/broken-links.md`](../../14-customer-journeys/page-triage/broken-links.md),
> [`page-triage/duplicate-clusters.md`](../../14-customer-journeys/page-triage/duplicate-clusters.md),
> [`/codex/09-strategy/architecture-v2/uac-registry-gaps.md`](../../09-strategy/architecture-v2/uac-registry-gaps.md).
> Cross-read against
> [`_ssot-rules/03-same-system-principle.md`](../../14-customer-journeys/_ssot-rules/03-same-system-principle.md),
> [`04-dart-commercial-axes.md`](../../14-customer-journeys/_ssot-rules/04-dart-commercial-axes.md),
> [`08-pricing-principles.md`](../../14-customer-journeys/_ssot-rules/08-pricing-principles.md).
>
> **Peer stages:** Stage 3B catalogues the UAC combo rules; Stage 3C specs the derivation engine; Stage 3D builds the
> target-experience deck; Stage 3E writes the refactor plan. This file is the shared "here's where we are today"
> baseline all four depend on.

> **[DELTA 2026-05-22]** **Current state:** This is a point-in-time audit snapshot taken 2026-04-20. The gap assessments
> (UAC registry gaps #1-#11 "Not shipped", entitlement gaps, demo-provisioning gaps) reflect state at that date and have
> NOT been re-verified. **Known changes since audit:** UAC gap #12 (`StrategyAvailabilityRegistry`) was already shipped
> at audit time. No evidence that #1-#11 have since shipped. All G1 items from Stage 3E remain pre-cutover scope (see
> `stage-3e-refactor-plan.md` delta box). **Do not use this file as a current-state snapshot without re-running the grep
> commands in §2.3 and §3.**

---

## 0. Executive one-screen summary

The UI has shipped a large surface area — 177 routes across two apps — but the gap between **mechanical presence** and
**SSOT-grade integrity** is wide. Four axes of debt:

1. **UAC does not yet declare the capability dimensions rule 05 assumes.** 11 of 12 UAC gaps in
   [`uac-registry-gaps.md`](../../09-strategy/architecture-v2/uac-registry-gaps.md) are still proposals — only
   `StrategyAvailabilityRegistry` (gap #12) is shipped. No `ArchetypeCapabilityV2`, no `FlashLoanReceiverRegistry`, no
   `LiquidationBonusScheduleV2`, no `EventCalendarSourceCapability`, no `RepresentativeFutureRegistry`, no
   `CrossVenueRoutingPolicy`, no `LaySideExecutionSemantics`, no `PricingFidelity`, no `IvSurfaceFidelity`, no
   `MultiLegOrderCapability`, no `supported_signal_variants` on `VenueCapabilityV2`.
2. **Four user-visible catalogue services are asymmetric.** Strategy Catalogue is finished (Phase 10 shipped
   `/services/strategy-catalogue/*` with master matrix + admin toggle + per-strategy detail). Data / ML / Execution Algo
   catalogues are each ~60% scaffolded and missing the common pattern (archetype master matrix → detail → admin lock →
   codex deep-link).
3. **Entitlement system is a flat string set.** Role/entitlement gating lives in a hardcoded 12-line `if/else` cascade
   at [`lifecycle-nav.tsx:102-113`](../../../../unified-trading-system-ui/components/shell/lifecycle-nav.tsx#L102-L113);
   entitlement keys are a 17-item string array in
   [`lib/config/auth.ts:11-29`](../../../../unified-trading-system-ui/lib/config/auth.ts#L11-L29). There is no
   org-scoped JWT, no per-fund claim, no per-client API key issuance, no binding between `trading_platform_subscriber`
   vs `im_client` audience (from the availability registry) and what UI surface they actually see.
4. **Demo-provisioning is single-environment + single-audience.** 5 personas seeded in
   [`lib/auth/personas.ts`](../../../../unified-trading-system-ui/lib/auth/personas.ts) (3 in user-management-ui) — all
   localhost-only, all mock-auth-only. No staging Firebase project yet (tracked as five_space_ia issue #12). No
   `prospect-reg` / `prospect-dart` persona for warm-prospect demos. No visibility-slicing LOCKED-VISIBLE mode declared
   anywhere in the UI config tree.

Stage 3B+3C+3E are the fix routes. This audit names the gaps; the downstream stages design the fills.

---

## 1. Reuse of prior static audit

[`page-triage/triage-matrix.md`](../../14-customer-journeys/page-triage/triage-matrix.md) classified all 177 routes
across unified-trading-system-ui (158) + user-management-ui (19). Headline distribution:

| Action bucket     | Count | Notes                                                                                                                        |
| ----------------- | ----- | ---------------------------------------------------------------------------------------------------------------------------- |
| `promote`         | ~120  | Kept as-is; canonical                                                                                                        |
| `refactor`        | ~12   | Keep route, restructure page (usually catalogue-pattern)                                                                     |
| `merge-into`      | ~25   | Concept-duplicates consolidated                                                                                              |
| `defer`           | ~14   | Intentionally deferred to follow-up plans (Phase 10.7 allocator split, pb3 signup, ...)                                      |
| `deprecate`       | 0     | Explicit — all deprecation decisions pushed to follow-up plans per roadmap                                                   |
| `partial-archive` | 5     | IR presentation slide archive — handled in [`partial-archive.md`](../../14-customer-journeys/page-triage/partial-archive.md) |

Nav bottlenecks identified in the static audit:

- Single-entry bottleneck: Spaces dropdown in
  [`components/shell/spaces-nav-sections.tsx`](../../../../unified-trading-system-ui/components/shell/spaces-nav-sections.tsx)
  is the only entry point to DART / IM / Reg Umbrella marketing landings from authenticated app views (Phase 3 rename
  shipped: `DART` label replaces `Platform` in `components/shell/nav-copy.ts`).
- No persistent audience switcher: a client who logs in as `im_client` cannot preview the `trading_platform_subscriber`
  view without persona switch → UI logout → re-login.
- `/services/strategy-catalogue/*` has self-contained sub-nav (Phase 10), but Data / ML / Execution Algo each have their
  own ad-hoc top nav with no consistent breadcrumb or admin entry-point.

10 duplicate-cluster decisions already in
[`duplicate-clusters.md`](../../14-customer-journeys/page-triage/duplicate-clusters.md). Summary for Stage 3A's
purposes:

1. Strategy catalogue legacy (`/services/research/strategy/*`) → merged into `/services/strategy-catalogue/*` (Phase
   10.6 in flight).
2. Strategy allocator split → deferred (Phase 10.7).
3. Data gaps / completeness / missing → merge into `/services/data/gaps` with tabs.
4. Trading strategies vs strategy catalogue → merge `/services/trading/strategies/*` into
   `/services/strategy-catalogue/strategies/[archetype]/[slot]` with "actively running" filter.
5. Admin users duplication: kept separate by user directive (user-management-ui may never deploy publicly).
6. Public service pages vs marketing static: React `/services/*` (public) routes merge into marketing static
   equivalents.
7. Observe audit cluster (`event-audit`, `reconciliation`, `recovery`, `registry`) → merge into
   `/services/observe/health` tabs.
8. Reports reconciliation vs Observe reconciliation → Reports is authoritative; Observe becomes ops-filter variant.
9. IR site-navigation → merge into `/investor-relations` landing.
10. Onboarding vs signup → deferred to pb3 demo-provisioning plan.

---

## 2. Broken-href re-verification (re-ran grep against `app/**/page.tsx` 2026-04-20)

### 2.1 Confirmed shipped fixes from [`broken-links.md`](../../14-customer-journeys/page-triage/broken-links.md)

| href                      | Fix applied                                                                                     | Status   |
| ------------------------- | ----------------------------------------------------------------------------------------------- | -------- |
| `/services/execution/tca` | `app/(platform)/services/execution/tca/page.tsx` exists — stub shipped                          | ✅ Fixed |
| `/markets/pnl`            | `components/trading/pnl-attribution-panel.tsx:108` now uses `/services/trading/pnl`             | ✅ Fixed |
| `/presentation`           | `app/(public)/demo/preview/page.tsx:158` now points to `/investor-relations/board-presentation` | ✅ Fixed |
| `/executive`              | `board-presentation-slide-part-b.tsx:376` now points to `/services/reports/executive`           | ✅ Fixed |

### 2.2 Still-outstanding broken hrefs (5 probable)

All five reference `app/(platform)/services/research/ml/*` paths that exist in
[`lib/lifecycle-route-mappings.ts`](../../../../unified-trading-system-ui/lib/lifecycle-route-mappings.ts) but have no
`page.tsx`:

| href                                | Directory present? | `page.tsx` present? | Decision required                                          |
| ----------------------------------- | :----------------: | :-----------------: | ---------------------------------------------------------- |
| `/services/research/ml/overview`    |         No         |         No          | Part of ML Model Catalogue refactor (§4.3)                 |
| `/services/research/ml/experiments` |         No         |         No          | Part of ML Model Catalogue refactor (§4.3)                 |
| `/services/research/ml/features`    |         No         |         No          | Possible duplicate of `/services/research/features` (§3.2) |
| `/services/research/ml/validation`  |         No         |         No          | Part of ML Model Catalogue refactor (§4.3)                 |
| `/services/research/ml/deploy`      |         No         |         No          | Part of ML Model Catalogue refactor (§4.3)                 |

Directory listing confirms the existing `/services/research/ml/*` pages are: `analysis`, `components`, `config`,
`governance`, `grid-config`, `monitoring`, `page.tsx`, `registry`, `training` — 9 subpaths. None of the 5
lifecycle-route-mappings targets above exist. The 10-page ML surface is both **fragmented** (duplicate concept spread
across `config`, `grid-config`, `registry`, `training`) and **incomplete** (the canonical pattern from the lifecycle
mapping is not built).

### 2.3 Grep command re-ran (for reproducibility)

```bash
grep -rE 'href=["'"'"']/[^"'"'"']*["'"'"']' \
  unified-trading-system-ui/app \
  unified-trading-system-ui/components \
  unified-trading-system-ui/lib
# → cross-reference each unique `/…` target against `app/**/page.tsx`
# → any mismatch = broken link
```

Net outstanding broken-link count after Phase 3 nav fixes: **0 confirmed + 5 probable** (all in ML Model Catalogue
surface). Down from the 4+5 in the original audit.

---

## 3. UAC registry — gap audit

Read-set:

- [`unified-api-contracts/unified_api_contracts/registry/capability_declarations/`](../../../../unified-api-contracts/unified_api_contracts/registry/capability_declarations/)
  — currently: `_altdata.py`, `_cefi.py`, `_defi.py`, `_defi_chain_data.py`, `_defi_source_capabilities.py`,
  `_sports.py`, `_tradfi.py`.
- [`internal/architecture_v2/`](../../../../unified-api-contracts/unified_api_contracts/internal/architecture_v2/) —
  currently: `artifact_registry.py`, `enums.py`, `schemas.py`, `strategy_availability.py`, `venue_tokens.py`.
- [`canonical/domain/`](../../../../unified-api-contracts/unified_api_contracts/canonical/domain/) — sub-packages
  `derivatives`, `execution`, `features`, `infrastructure`, `market`, `onchain`, `position`, `prediction`, `reference`,
  `sports`, plus `bookmaker_registry.py`, `_base.py`.

### 3.1 Status of the 12 declared UAC gaps

Cross-ref: [`uac-registry-gaps.md`](../../09-strategy/architecture-v2/uac-registry-gaps.md).

|   # | Addition                                     | Target path                                         | Present today?                                         | Status          |
| --: | -------------------------------------------- | --------------------------------------------------- | ------------------------------------------------------ | --------------- |
|   1 | `ArchetypeCapabilityV2` registry             | `internal/architecture_v2/archetype_capability.py`  | No file at target path                                 | **Not shipped** |
|   2 | `supported_signal_variants` on VenueCap V2   | `internal/architecture_v2/venue_capability_v2.py`   | No `venue_capability_v2.py` found                      | **Not shipped** |
|   3 | `FlashLoanReceiverRegistry`                  | `registry/capability_declarations/_defi.py`         | `_defi.py` exists; no flash-loan-receiver types inside | **Not shipped** |
|   4 | `LiquidationBonusScheduleV2`                 | `registry/capability_declarations/_defi.py`         | Not present                                            | **Not shipped** |
|   5 | `EventCalendarSourceCapability`              | `registry/capability_declarations/_altdata.py`      | `_altdata.py` exists; no event-source types yet        | **Not shipped** |
|   6 | `IvSurfaceFidelity` + option-venue extension | `_cefi.py` / `_tradfi.py`                           | Not present                                            | **Not shipped** |
|   7 | `MultiLegOrderCapability`                    | `internal/architecture_v2/venue_capability_v2.py`   | Same as #2                                             | **Not shipped** |
|   8 | `PricingFidelity` on DeFi spot venues        | `registry/capability_declarations/_defi.py`         | Not present                                            | **Not shipped** |
|   9 | `LaySideExecutionSemantics`                  | `registry/capability_declarations/_sports.py`       | Not present                                            | **Not shipped** |
|  10 | `CrossVenueRoutingPolicy`                    | `registry/capability_declarations/_tradfi.py`       | Not present                                            | **Not shipped** |
|  11 | `RepresentativeFutureRegistry` + event       | `internal/architecture_v2/representative_future.py` | No file at target path                                 | **Not shipped** |
|  12 | `StrategyAvailabilityRegistry` + events      | `internal/architecture_v2/strategy_availability.py` | **Shipped** — full module (Phase 10.5, 2026-04-19)     | ✅ **Shipped**  |

Gap #12 is the only one of the twelve to have landed. The file provides `LockState` + `StrategyMaturity` + audience
filters + events — exactly what rule 05 building blocks 4, 11, 12, 13 require.

### 3.2 Adjacent-but-missing mechanisms

These are not in the declared gap list but rule 05 needs them:

- **Audience-to-permission map**: `StrategyAvailabilityRegistry` defines
  `Audience = Literal["admin" | "im_desk" | "im_client" | "trading_platform_subscriber"]` but nothing in UAC maps those
  audience strings to a JWT claim, an API key scope, or a per-route allowlist.
  `unified-trading-system-ui/lib/config/auth.ts:8` defines `UserRole = "internal" | "client" | "admin"` — those three
  values have **no mechanical binding** to the StrategyAvailability audience vocabulary. Stage 3C's derivation engine
  must bridge these.
- **Business-unit / fund identifier**: `validate_allocation_authorised(slot_label, client_id, business_unit)` takes
  `business_unit: Literal["saas" | "im_desk" | "admin"]`, but no registry declares which `business_unit` owns which
  `reserving_business_unit_id`. IM has multiple funds (Reg Umbrella + IM pooled + per-client SMAs). Stage 3B must
  declare these.
- **Playbook → route binding**: no UAC declaration of which route in the UI satisfies which playbook section. Stage 1's
  `experience/*.md` names audiences and journeys; no runtime registry cross-references route targets.

---

## 4. Service-SSOT catalogue audit

Each of the four building-block-dimension catalogues has a different implementation state. The target pattern (shipped
on Strategy Catalogue) is: **master-matrix → filter facets → detail page → admin lock/maturity toggle → codex GitHub
deep-link**.

### 4.1 Strategy Catalogue — ✅ **Canonical / complete**

Route root:
[`/services/strategy-catalogue/`](<../../../../unified-trading-system-ui/app/(platform)/services/strategy-catalogue/>).
Phase 10 shipped 2026-04-19 per memory entry "Phase 10 UI complete". Surfaces:

- Overview (landing with counters + route cards).
- Coverage (master matrix with status chips + filter + side panel).
- Coverage → Blocked (10 `BL-*` entries with remediation + UAC deep-links).
- Coverage → By combination (category × instrument-type leg-pickers).
- Strategies → `[archetype]` → `[slot]` (per-strategy detail with availability + build/ledger/delta).
- Admin → Lock state (admin toggle with slot picker + audit event list).

7 reusable chip primitives live at `components/architecture-v2/` with `data-testid` hooks for Playwright. TS mirror of
availability at `lib/architecture-v2/availability.ts`. Layout wraps children in `AvailabilityStoreProvider` (React
Context + localStorage persistence). **This is the reference implementation; Stage 3C replicates the pattern for Data /
ML / Execution Algo.**

### 4.2 Data Catalogue — 🟡 **Partial / fragmented**

Route root: [`/services/data/`](<../../../../unified-trading-system-ui/app/(platform)/services/data/>). 13 sub-routes
(overview, instruments, venues, coverage, completeness, gaps, missing, events, logs, processing, raw, valuation,
markets).

Pattern mismatch vs Strategy Catalogue:

- No master matrix page — `/services/data/overview` is a landing card, not a queryable grid.
- Three concept-duplicates (`completeness` / `missing` / `gaps`) slated to merge into `gaps` with tabs.
- No per-instrument detail route (`instruments` is a flat list).
- No admin lock/maturity axis — data has its own axes (venue / chain / instrument_type / timeframe) that UAC
  `ManifestWriter` uses, but no UI surface shows the `(venue, chain, data_type)` shards.
- No chip primitives reused from Strategy Catalogue's `components/architecture-v2/`.
- No codex deep-link back to the SSOT (which would be
  [`/codex/02-data/availability-manifest-and-data-status.md`](../../02-data/availability-manifest-and-data-status.md)).

Data Catalogue refactor is tracked in [`roadmap/next-waves.md`](../../14-customer-journeys/roadmap/next-waves.md) Wave 5
per the Stage 3 plan carry-over.

### 4.3 ML Model Catalogue — 🟠 **Fragmented + incomplete**

Route root: [`/services/research/ml/`](<../../../../unified-trading-system-ui/app/(platform)/services/research/ml/>).
Existing 9 sub-routes: `analysis`, `components`, `config`, `governance`, `grid-config`, `monitoring`, `registry`,
`training`, and a landing `page.tsx`. Missing 5 routes referenced by `lifecycle-route-mappings.ts` (§2.2): `overview`,
`experiments`, `features`, `validation`, `deploy`.

Pattern issues:

- 9 ad-hoc sub-routes with no consistent landing pattern. `page.tsx` is the landing; `registry` is the closest thing to
  a catalogue surface but renders a flat list.
- No model-family archetype taxonomy (equivalent of strategy archetype list). No UAC registry declares the set of model
  families (LSTM / transformer / ensemble / online-learn / RL-policy-grad / ...).
- No MODEL-level lock state. `StrategyAvailabilityRegistry` locks _strategies_ not _models_. A model-family-level
  availability registry is missing.
- `config` and `grid-config` are concept-duplicates.
- Governance lives at `/services/research/ml/governance` but there's no cross-link from Strategy Catalogue's
  `ml_family_ref` even though several archetypes (`ML_DIRECTIONAL_CONTINUOUS`, `ML_DIRECTIONAL_EVENT_SETTLED`) depend on
  model families.

**ML Model Catalogue refactor is the biggest single pending UI surface** — Wave 6 in the roadmap.

### 4.4 Execution Algo Catalogue — 🟠 **Fragmented / recently fixed**

Route root: [`/services/execution/`](<../../../../unified-trading-system-ui/app/(platform)/services/execution/>).
Existing 7 sub-routes: `algos`, `benchmarks`, `candidates`, `handoff`, `overview`, `tca`, `venues`, plus a dynamic
`[executionId]` detail route.

Pattern issues:

- `algos` is a flat list; no archetype hierarchy (TWAP / VWAP / POV / iceberg / SOR / sniper / liquidation-bot).
- `venues` here duplicates `/services/data/venues` conceptually (one is capability-per-venue for execution, one is
  coverage-per-venue for data) — the duplication is not flagged in `duplicate-clusters.md`.
- `tca` stub shipped 2026-04-19 (Phase 3 nav-fix); still a placeholder page, not a real analysis surface.
- No admin surface for `MultiLegOrderCapability` (UAC gap #7) or for `CrossVenueRoutingPolicy` (UAC gap #10) — both of
  which the Execution Algo Catalogue needs to declare once shipped.
- `candidates` + `handoff` are promote-lane concepts that arguably belong in Strategy Catalogue's promotion-ledger flow,
  not here.

**Execution Algo Catalogue refactor** — Wave 7 in the roadmap.

---

## 5. Entitlement / auth audit

Current entitlement surface:

- [`lib/config/auth.ts:11-29`](../../../../unified-trading-system-ui/lib/config/auth.ts#L11-L29) — 17 flat entitlement
  strings (`data-basic`, `data-pro`, `execution-basic`, `execution-full`, `ml-full`, `strategy-full`,
  `strategy-families`, `defi-bundles`, `defi-staking`, `reporting`, `investor-relations`, `investor-board`,
  `investor-plan`, `investor-platform`, `investor-im`, `investor-regulatory`, `investor-archive`) + `*` wildcard.
- `lib/config/auth.ts:43-49` —
  `TRADING_DOMAINS = ["trading-common" | "trading-defi" | "trading-sports" | "trading-options" | "trading-predictions"]`.
- `lib/config/auth.ts:53` — `TRADING_TIERS = ["basic" | "premium"]`.
- `lib/config/auth.ts:8` — `UserRole = "internal" | "client" | "admin"` — **three roles only**.
- `lib/config/auth.ts:198` —
  `ClientTier = "Client Full" | "Client Premium" | "DeFi Client" | "Data Pro" | "Data Basic" | "Custom"` — derived
  display label, not a claim.

Route gating: hardcoded cascade in
[`components/shell/lifecycle-nav.tsx:102-113`](../../../../unified-trading-system-ui/components/shell/lifecycle-nav.tsx#L102-L113):

```typescript
if (path === "/services/promote" || ...) return hasEntitlement("strategy-full") || hasEntitlement("ml-full");
if (adminOnlyRoutes.some((r) => ...)) return isAdmin();
if (internalRoutes.some((r) => ...)) return isInternal();
if (path.startsWith("/services/research")) return hasEntitlement("strategy-full") || hasEntitlement("ml-full");
if (path.startsWith("/services/trading") || path.startsWith("/services/execution"))
  return hasEntitlement("execution-basic") || hasEntitlement("execution-full");
if (path.startsWith("/services/reports")) return hasEntitlement("reporting");
return true;
```

**Gaps vs StrategyAvailabilityRegistry audience vocabulary:**

| Rule 05 audience              |          Declared in UAC?          |   Mapped to UI role?    | Mapped to JWT claim? | Gap                                                          |
| ----------------------------- | :--------------------------------: | :---------------------: | :------------------: | ------------------------------------------------------------ |
| `admin`                       | ✅ (`strategy_availability.py:83`) | ✅ `UserRole = "admin"` |          ❌          | No JWT claim — relies on persona entitlement `*`             |
| `im_desk`                     |                 ✅                 |           ❌            |          ❌          | No `internal` role sub-typing; no `business_unit` claim      |
| `im_client`                   |                 ✅                 |           ❌            |          ❌          | No `client` role sub-typing; no `fund_id` claim              |
| `trading_platform_subscriber` |                 ✅                 |           ❌            |          ❌          | No mapping; DART subscribers are treated as generic `client` |

**Other auth gaps:**

- No org-scoped JWT claims. Personas have `org: { id, name }` but nothing propagates `org_id` into a JWT. No `fund_id`
  or `client_id` claim on any persona; no `business_unit` claim.
- No per-client API key issuance. API calls today are Firebase-session-token based; no separate developer-facing API
  key, no per-org rate limiting, no per-org key rotation.
- No audience-switcher UI. A user logged in as `im_client` cannot preview `trading_platform_subscriber` without
  switching personas. Stage 3C's derivation engine must declare the switcher spec.
- No "act-as" / impersonation for admin support workflows (currently admin sees everything via wildcard).

---

## 6. Demo-provisioning audit

Current state:

- **5 personas in unified-trading-system-ui**
  ([`lib/auth/personas.ts`](../../../../unified-trading-system-ui/lib/auth/personas.ts)): `admin` (Odum Internal),
  `internal-trader` (Odum Internal), `client-full` (Alpha Capital), `client-data-only` (Beta Fund), `client-premium`
  (Vertex Partners). Plaintext passwords, intentionally visible in the client bundle for instant demo login.
- **3 personas in user-management-ui** (kept separate by user directive — may never deploy publicly).
- **localhost-only.** No staging Firebase project — tracked as five_space_ia issue #12 per memory entry "Playbook SSOT
  shipped at codex/14-customer-journeys/ (2026-04-19)".
- **Mock-auth-only.** `VITE_SKIP_AUTH=true` + `VITE_MOCK_API=true` is the only supported mode for the demo personas
  today. Real Firebase sign-in works in theory but nothing populates the audience claims.

### 6.1 Missing demo-surface personas

Rule 03's audience list (DART / IM / Reg Umbrella) intersected with the three playbook types (anon / post-call prospect
/ warm-prospect demo) yields surfaces with no persona backing:

| Surface                                | Persona exists? | Gap                                                                     |
| -------------------------------------- | :-------------: | ----------------------------------------------------------------------- |
| Anon marketing visitor                 |       N/A       | Served by static marketing; no auth needed                              |
| Warm-prospect DART demo (no call yet)  |       ❌        | No `prospect-dart` persona with DART-only entitlements                  |
| Warm-prospect Reg-Umbrella demo        |       ❌        | No `prospect-reg` persona with Reg-Umbrella entitlements                |
| Warm-prospect IM demo                  |       ❌        | No `prospect-im` persona (IM = Alpha Capital today, which is post-call) |
| Post-call IM client                    |       ✅        | `client-full` covers this                                               |
| Post-call DART client                  |       ✅        | `client-premium` partially covers                                       |
| Visibility-slicing LOCKED-VISIBLE mode |       ❌        | No UI mode that shows locked content with a "locked" chip               |

### 6.2 Visibility-slicing model gap

Per MEMORY.md entry "Playbook SSOT shipped" — the locked decisions include "visibility-slicing LOCKED-VISIBLE mode"
tracked in roadmap. Today UI hides locked routes entirely via the `isItemAccessible` cascade; there is no LOCKED-VISIBLE
rendering that shows the surface exists with a badge. This blocks the rule 04 commercial-axes demo — a prospect cannot
see "the thing you don't have yet" without logging out and logging back in as a different persona.

---

## 7. Per-client API-key state

Not issued today. Summary:

- No `unified-api-keys-service` or equivalent.
- No `apiKey` field on `AuthPersona` — auth flow is Firebase session-token only.
- No per-org rate limiting declaration in `deployment-api` or the 3 API gateways (port 8004–8016 range per local-dev
  mapping).
- No UAC registry of API-key scopes (rule 05 building-block 7 "execution layer" needs scoped keys for execution
  routing-policy clients vs read-only data clients).

Roadmap wave: per-client API-key issuance is tracked in
[`roadmap/next-waves.md`](../../14-customer-journeys/roadmap/next-waves.md) per memory entry "Playbook SSOT shipped".

---

## 8. Org-scoped JWT claims

Today's JWT (Firebase ID token) carries: `uid`, `email`, `email_verified`, and Odum-emitted custom claims — none visible
in any declaration file I read. `AuthPersona` has `org: { id, name }` but it's a client-side fixture, not a
server-verified claim.

**Claims needed per StrategyAvailabilityRegistry audience filter:**

| Claim            | Needed by                                               | Present today? |
| ---------------- | ------------------------------------------------------- | :------------: |
| `audience`       | `slots_visible_to()` — all four audience values         |       ❌       |
| `org_id`         | All client-exclusive slot lookups                       |       ❌       |
| `client_id`      | `CLIENT_EXCLUSIVE` lock enforcement                     |       ❌       |
| `fund_id`        | IM allocator reporting partition                        |       ❌       |
| `business_unit`  | `validate_allocation_authorised()` — saas/im_desk/admin |       ❌       |
| `api_key_scopes` | Per-scope route gating                                  |       ❌       |

**None of these exist in the current JWT surface.** Stage 3C's derivation engine must declare the issuer flow.

---

## 9. The 13-building-block Exists / Gap / Blocker table

Source: [`_ssot-rules/_source-v1-feedback.md`](../../14-customer-journeys/_ssot-rules/_source-v1-feedback.md) "On
building-block dimensions". Each row names the rule 05 block, where it exists today, what's missing, and what blocks the
missing piece from landing.

|   # | Building block                            | Exists in (repo / path)                                                                           | Gap                                                                                                          | Blocker                                                                                    |
| --: | ----------------------------------------- | ------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------ |
|   1 | Reporting core                            | `reports-service/`; UI `/services/reports/*`; duplicate cluster merged into Reports               | No rule 03-compliant "Research ≡ live" reporting axis: reports only display live; research views not wired   | `im_client` audience in UAC doesn't bind to reporting routes; Stage 3C derivation needed   |
|   2 | Regulatory umbrella reporting             | `/regulatory` marketing; `/services/reports/reconciliation`; user-management-ui compliance views  | No `reserving_business_unit_id` declared for Reg Umbrella funds; no MLRO workflow UI                         | UAC gap: "business_unit registry" (not in the 12-gap list); Stage 3B must declare          |
|   3 | IM allocator reporting                    | `/investment-management` marketing; `portfolio-allocator`; UAC `validate_allocation_authorised()` | No IM-desk view of allocations segregated by `fund_id`; Phase 10.7 allocator-split not shipped               | `fund_id` claim missing (§8); `business_unit` registry missing (§3.2)                      |
|   4 | Strategy-service entry                    | `/services/strategy-catalogue/*` (Phase 10 shipped); UAC `StrategyAvailabilityRegistry`           | Phase 10.6 consumer-surface split not started (research / trading / IM catalogue / client-reporting views)   | UAC gap #1 `ArchetypeCapabilityV2` + audience→route mapping (Stage 3C)                     |
|   5 | Instructions integration                  | `execution-service/`; `trading-agent`; UAC `execution/` domain                                    | No `ClientInstruction` schema declaring which rule 04 commercial-path allows which instruction type          | UAC "ClientInstructionSchema" (not in 12-gap list; Stage 1 rule 10 will declare)           |
|   6 | Research / promote pipeline               | `strategy-service/engine/strategies/v2/archetype_build_registry.py` + Phase 2 ledger              | UI admin surface for promotion-decision-ledger lives in Strategy Catalogue only; ML has none                 | UAC gap #1 + ML-family registry missing (§4.3)                                             |
|   7 | Execution layer                           | `execution-service/`; UAC `_cefi.py`, `_defi.py`, `_sports.py`, `_tradfi.py`                      | 5 UAC gaps open: #3 flash-loan receiver, #7 multi-leg, #9 lay-side, #10 cross-venue routing, #6 IV surface   | Each gap blocks a specific algo surface; ship order per `uac-registry-gaps.md` phasing     |
|   8 | Venue packs (per venue/group)             | `codex/02-venues/`; UAC `VENUE_REGISTRY` (canonical); `_cefi.py`/`_defi.py`/etc.                  | No `supported_signal_variants` per venue (UAC gap #2); venue-pack commercial metadata undeclared             | UAC gap #2; Stage 3B commercial-packaging pattern not yet shipped                          |
|   9 | Chain packs (per chain)                   | UAC `_defi_chain_data.py`; `CHAIN_RPC_TEMPLATES` in `_defi.py`                                    | No `FlashLoanReceiverRegistry` (gap #3); no chain-pack commercial metadata                                   | UAC gap #3                                                                                 |
|  10 | Instrument-type packs (options/perps/...) | `canonical/domain/` sub-packages; UAC `InstrumentType` enum                                       | No `OptionVenueCapability` (gap #6); no `PricingFidelity` on DeFi spot (gap #8); no instrument-pack metadata | UAC gaps #6, #8                                                                            |
|  11 | Analytics packs                           | `features-service/*`; `unified-features-interface/`; UI `/services/research/features`             | No `EventCalendarSourceCapability` (gap #5); analytics-pack commercial metadata undeclared; ML fragmented    | UAC gap #5; §4.3 ML refactor                                                               |
|  12 | Exclusivity / non-compete premium         | UAC `CLIENT_EXCLUSIVE` lock_state (Phase 10.5 shipped)                                            | No "non-compete radius" declaration (geography / asset-class / venue); commercial tier-B only                | Stage 3B must declare non-compete axis; contractual side not in UAC (§ commercial stage 2) |
|  13 | Custom solution premium                   | No UAC declaration; ad-hoc in per-client contracts                                                | No "custom capability overlay" schema declaring what's non-standard; no versioning for custom builds         | Custom-solution registry missing; defer to Stage 2 commercial-model + Stage 3E refactor    |

---

## 10. Handover notes for Stages 3B / 3C / 3D / 3E

- **Stage 3B (UAC combo rules):** 11 of 12 declared UAC gaps + 3 adjacent-but-missing mechanisms (§3.2) need
  combinatoric declarations. Non-compete radius (block 12) and custom-solution schema (block 13) are new work on top of
  the `uac-registry-gaps.md` queue. Start from block 4 `StrategyAvailabilityRegistry` (only one shipped) and work
  outward along dependency edges (#1 `ArchetypeCapabilityV2` blocks most).
- **Stage 3C (derivation engine):** must bridge the `UserRole → StrategyAvailability.Audience` mismatch (§5), declare
  the JWT claim set (§8), spec the LOCKED-VISIBLE rendering mode (§6.2), and generate the four catalogue surfaces
  (Strategy / Data / ML / Execution Algo) from a single registry. The Strategy Catalogue Phase 10 implementation is the
  reference pattern; Data / ML / Execution Algo replicate it.
- **Stage 3D (target-experience deck):** must screenshot the 177-route current surface vs the 4-catalogue-pattern
  target. Focus the before/after contrast on the ML Catalogue (biggest single gap) and the visibility-slicing
  LOCKED-VISIBLE mode (no current implementation).
- **Stage 3E (refactor plan):** phase order suggestion — (A) land remaining 11 UAC gaps as declared in
  `uac-registry-gaps.md` Phase A→F; (B) Phase 10.6 consumer-surface split; (C) Data / ML / Execution Algo catalogue
  refactors in parallel; (D) JWT claim issuance + LOCKED-VISIBLE mode; (E) per-client API key; (F) staging Firebase +
  `prospect-reg` / `prospect-dart` / `prospect-im` personas.

---

## 11. Cross-references

- [`_ssot-rules/03-same-system-principle.md`](../../14-customer-journeys/_ssot-rules/03-same-system-principle.md) —
  research ≡ live rule
- [`_ssot-rules/04-dart-commercial-axes.md`](../../14-customer-journeys/_ssot-rules/04-dart-commercial-axes.md) —
  commercial paths
- [`_ssot-rules/08-pricing-principles.md`](../../14-customer-journeys/_ssot-rules/08-pricing-principles.md) — Tier A/B
  structure
- [`page-triage/triage-matrix.md`](../../14-customer-journeys/page-triage/triage-matrix.md) — 177-route classification
- [`page-triage/broken-links.md`](../../14-customer-journeys/page-triage/broken-links.md) — broken-href tracker
- [`page-triage/duplicate-clusters.md`](../../14-customer-journeys/page-triage/duplicate-clusters.md) — 10 merge
  decisions
- [`/codex/09-strategy/architecture-v2/uac-registry-gaps.md`](../../09-strategy/architecture-v2/uac-registry-gaps.md) —
  the 12 UAC gaps
- [`/codex/09-strategy/architecture-v2/cross-cutting/strategy-availability-and-locking.md`](../../09-strategy/architecture-v2/cross-cutting/strategy-availability-and-locking.md)
  — lock state + maturity principle
- [`/codex/02-data/availability-manifest-and-data-status.md`](../../02-data/availability-manifest-and-data-status.md) —
  Data Catalogue SSOT target
- [`unified-api-contracts/unified_api_contracts/internal/architecture_v2/strategy_availability.py`](../../../../unified-api-contracts/unified_api_contracts/internal/architecture_v2/strategy_availability.py)
  — only UAC gap shipped
- [`unified-trading-system-ui/app/(platform)/services/strategy-catalogue/`](<../../../../unified-trading-system-ui/app/(platform)/services/strategy-catalogue/>)
  — reference catalogue pattern
