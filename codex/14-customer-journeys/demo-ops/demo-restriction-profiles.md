---
doc_type: codex-ssot
title: Demo Restriction Profiles
summary:
  How a demo restriction profile (6 dimensions — commercial path, block set, venue/chain/instrument scope,
  strategy-family, maturity filter, demo mode) is built from pre-call notes and drives staging entitlements, catalogue
  filtering, and nav visibility; default profiles per path + the IM_RESERVED filter enforced via availability.ts
  slotsVisibleTo.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [strategy-service, unified-trading-system-ui]
scope: [sales, engineer, admin]
tags: [demo-ops, sales, dart, restriction-profile, entitlements, catalogue, im-reserved, staging]
related:
  [
    /codex/14-customer-journeys/demo-ops/dart-demo-modes.md,
    /codex/14-customer-journeys/demo-ops/upsell-overlays.md,
    /codex/14-customer-journeys/demo-ops/pre-demo-curation-rules.md,
    /codex/14-customer-journeys/demo-ops/demo-decision-matrix.md,
    ../commercial-model/building-block-packaging.md,
  ]
created: 2026-04-20
authoritative_for: [demo restriction profiles]
referenced_by:
  [
    /codex/14-customer-journeys/README.md,
    /codex/14-customer-journeys/commercial-model/README.md,
    /codex/14-customer-journeys/dart/dart-terminal-vs-research.md,
    /codex/14-customer-journeys/demo-ops/README.md,
    /codex/14-customer-journeys/demo-ops/dart-demo-modes.md,
    /codex/14-customer-journeys/demo-ops/demo-decision-matrix.md,
    /codex/14-customer-journeys/demo-ops/pre-demo-curation-rules.md,
    /codex/14-customer-journeys/demo-ops/staging-demo-setup.md,
  ]
owner:
last_reviewed:
code_refs:
  [unified-trading-system-ui/lib/auth/personas.ts, unified-trading-system-ui/lib/architecture-v2/availability.ts]
---

# Demo Restriction Profiles

> How a restriction profile is built from pre-call notes and how the profile drives demo user entitlements, catalogue
> filtering, and nav visibility. Cites [rule 04](../_ssot-rules/04-dart-commercial-axes.md),
> [rule 05](../_ssot-rules/05-building-block-dimensions.md), [rule 06](../_ssot-rules/06-show-dont-show-discipline.md),
> [rule 10](../_ssot-rules/10-strategy-instruction-schema-principles.md).

## What a profile is

A demo restriction profile is a set of identifiers that scopes what a demo user sees in staging. The profile lives in
the staging environment's entitlement registry and is applied when the demo user signs in. Deterministic: same profile,
same view.

A profile carries six dimensions:

1. **Commercial path** — resolved rule-04 cell. IM, Reg Umbrella, signals-only DART, full DART, combined,
   reporting-only.
2. **Block set** — which rule-05 blocks are active (see
   [`../commercial-model/building-block-packaging.md`](../commercial-model/building-block-packaging.md)).
3. **Venue / chain / instrument-type scope** — sub-scope per block 8 / 9 / 10. See
   [`../shared-core/venue-chain-instrument-scope.md`](../shared-core/venue-chain-instrument-scope.md).
4. **Strategy-family scope** — which strategy archetypes / families the prospect's intent touches.
5. **Maturity filter** — default BACKTESTED-and-later for all external demos (rule 06).
6. **Demo mode** — broader-platform / turbo / deep-dive. See [`dart-demo-modes.md`](dart-demo-modes.md).

## How a profile is built from pre-call notes

The pre-demo discovery framework (see [`pre-demo-discovery-framework.md`](pre-demo-discovery-framework.md)) produces
structured notes. The sales person composes the profile from those:

1. **Resolve the commercial path** per rule 04. If unresolved, the demo is not scheduled.
2. **Look up the standard block set** in
   [`../commercial-model/building-block-packaging.md`](../commercial-model/building-block-packaging.md).
3. **Extract scope** from the prospect's declared intent.
4. **Apply maturity filter.** Always BACKTESTED-and-later externally.
5. **Pick demo mode.** See [`dart-demo-modes.md`](dart-demo-modes.md).
6. **Save the profile** to the staging entitlement registry keyed by demo user id.

## Default profiles per commercial path

### IM allocator profile (pb3b)

- Blocks: 1 (reporting core) + 3 (IM allocator reporting) + optional 11.
- Scope: slots the allocator's mandate fits.
- Strategy-family: public + IM-reserved.
- Maturity: BACKTESTED and later.
- Mode: turbo.
- **Catalogue filter:** `lock_state ∈ {PUBLIC, IM_RESERVED}` AND `maturity ≥ BACKTESTED`.
- **HIDDEN-ENTIRELY:** DART research / promote / strategy-authoring; other allocators' data; execution-layer internals
  beyond reporting.

### Reg Umbrella profile (pb3a)

- Blocks: 1 + 2 + 7 + 8 (scoped) + 10 (scoped) + optional 11.
- Scope: firm's declared activity.
- Strategy-family: public only.
- Maturity: BACKTESTED and later.
- Mode: deep-dive (reporting is the proof point).
- **Catalogue filter:** `lock_state = PUBLIC` AND `maturity ≥ BACKTESTED` AND in firm's scope.
- **HIDDEN-ENTIRELY:** DART research / promote surfaces (unless combined); Odum-run IM strategy detail; other Umbrella
  firms' data.

### Signals-only DART profile (pb3c `(Client, downstream)`)

- Blocks: 1 + 4 + 5 + 7 + 8 + 9 + 10 + optional 11. **Block 6 LOCKED-VISIBLE** with "available in full DART".
- Scope: declared instruction-flow scope; rule 10 fit-check resolved.
- Strategy-family: public only.
- Maturity: BACKTESTED and later.
- Mode: broader-platform or turbo per prospect.
- **Catalogue filter:** `lock_state = PUBLIC` AND `maturity ≥ BACKTESTED` AND in scope.
- **LOCKED-VISIBLE:** `/services/research/*` research-phase surfaces; promote-pipeline.
- **HIDDEN-ENTIRELY:** Admin, ops, other clients' data, pre-BACKTESTED slots, Odum IP depth.

### Full DART profile (pb3c `(Client, full-pipeline)` / `(Odum, full)`)

- Blocks: everything signals-only plus 6 plus expanded 11.
- Scope: broader; prospect iterates during engagement.
- Strategy-family: public; no CLIENT_EXCLUSIVE of others.
- Maturity: BACKTESTED-and-later externally; CODE_AUDITED-and-later for full-DART build-surface evaluators.
- Mode: broader-platform (first look) or deep-dive.
- **HIDDEN-ENTIRELY:** Admin, ops, other clients' CLIENT_EXCLUSIVE, pre-CODE_AUDITED slots.

### Combined profile (Reg Umbrella + signals-only DART)

- Block set = union, block 1 counted once.
- Scope = union of both paths.
- Nav composes both; research/promote LOCKED-VISIBLE.

### Reporting-only

- Blocks: 1 + 3 (IM) or 1 + 2 (Reg Umbrella). No execution, no strategy-service.
- Routes to IM or Reg Umbrella demos, not DART.

### IM_RESERVED filter — applies to ALL DART prospect profiles

Every DART prospect profile (signals-only DART, full DART, combined) applies a catalogue-level filter at render time:

- **Filter rule:** `entry.lockState !== "INVESTMENT_MANAGEMENT_RESERVED"` — unless the prospect is an authorised
  per-client override (e.g. Elysium or Desmond) who may see specific IM_RESERVED cells granted by entitlement.
- This is the runtime enforcement of the rule-06 HIDDEN-ENTIRELY discipline stated in the experience playbooks
  ([`../experience/dart-briefing.md`](../experience/dart-briefing.md) §7 +
  [`../experience/dart-demo.md`](../experience/dart-demo.md) §7).
- The `prospect-platform` fixture in `unified-trading-system-ui/lib/auth/personas.ts` maps to audience
  `trading_platform_subscriber`, which (per `unified-trading-system-ui/lib/architecture-v2/availability.ts`
  `slotsVisibleTo`) filters out `INVESTMENT_MANAGEMENT_RESERVED` automatically — no per-route filter logic needed in
  individual catalogue pages.
- **Per-client override** (Elysium, Desmond): their personas / entitlements include explicit `allowed_cells` that
  override the IM_RESERVED default for their specific scope. See
  [`../shared-core/strategy-allocation-lock-matrix.md`](../shared-core/strategy-allocation-lock-matrix.md) §Special
  cases for the per-client allowlists, and
  [`../implementation-mapping/persona-and-user-prototype-mapping.md`](../implementation-mapping/persona-and-user-prototype-mapping.md)
  for the persona-to-entitlement mapping.
- Effect on the three DART profiles above: the IM_RESERVED filter composes with each profile's existing
  `lock_state ∈ {PUBLIC, ...}` filter. Prospect demos render only PUBLIC slots plus any per-client-override IM_RESERVED
  slots; they never render IM_RESERVED slots that belong to another client or to Odum's forward plan.

## Profile → registry → runtime

Stored in Stage 3B's UAC combo registry keyed by profile_id. Stage 3C's derivation engine resolves
`access_control(user, route, item, phase)` by looking up the profile, expanding to (blocks, scope, maturity_filter,
locked_visible_set, hidden_entirely_set), and returning `visible | locked-visible | hidden`.

See [`../infra-spec/stage-3b-uac-combo-rules.md`](../../16-strategy-playbooks/infra-spec/stage-3b-uac-combo-rules.md)
and
[`../infra-spec/stage-3c-derivation-engine.md`](../../16-strategy-playbooks/infra-spec/stage-3c-derivation-engine.md).

## What a profile does not do

- Does not bypass authentication. Demo user still signs in via Firebase staging.
- Does not grant admin / ops access. Those are always HIDDEN-ENTIRELY for demo users.
- Does not grant access to other clients' data. Enforced at the data-query level.
- Does not change the component tree. UI is rule-03 same-system; what changes is what renders.

## Cross-references

- [rule 04](../_ssot-rules/04-dart-commercial-axes.md), [rule 05](../_ssot-rules/05-building-block-dimensions.md),
  [rule 06](../_ssot-rules/06-show-dont-show-discipline.md),
  [rule 10](../_ssot-rules/10-strategy-instruction-schema-principles.md)
- [dart-demo-modes.md](dart-demo-modes.md)
- [upsell-overlays.md](upsell-overlays.md)
- [pre-demo-curation-rules.md](pre-demo-curation-rules.md)
- [../commercial-model/building-block-packaging.md](../commercial-model/building-block-packaging.md)
- [../shared-core/venue-chain-instrument-scope.md](../shared-core/venue-chain-instrument-scope.md)
- [../shared-core/strategy-origin-vs-stack-depth.md](../shared-core/strategy-origin-vs-stack-depth.md)
- [../infra-spec/stage-3b-uac-combo-rules.md](../../16-strategy-playbooks/infra-spec/stage-3b-uac-combo-rules.md)
- [../infra-spec/stage-3c-derivation-engine.md](../../16-strategy-playbooks/infra-spec/stage-3c-derivation-engine.md)
