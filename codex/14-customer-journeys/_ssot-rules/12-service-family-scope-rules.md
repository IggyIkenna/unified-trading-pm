---
doc_type: codex-ssot
title: Rule 12 — Service-family scope rules
summary:
  "Rule 12 — the six-family closed enum (IM, RegUmbrella, DART, DART_reporting_only, admin, IM_desk) with
  surfaces/excludes/route_allowlist, enforced as a short-circuit pre-check in G1.6 access_control(); machine YAML at
  12-service-family-scope-rules.yaml, validated + Playwright dev/staging/prod parity."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-api-contracts, unified-trading-system-ui]
scope: [engineer, admin]
tags: [customer-journey, sales, uac, ui, registry]
related:
  [
    /codex/14-customer-journeys/_ssot-rules/04-dart-commercial-axes.md,
    /codex/14-customer-journeys/_ssot-rules/03-same-system-principle.md,
    /codex/14-customer-journeys/_ssot-rules/11-codex-scope-registry.md,
  ]
created: 2026-04-20
authoritative_for: [service-family scope rules (six-family route-allowlist enforcement)]
referenced_by:
  [
    /codex/02-data/questionnaire-axes.md,
    /codex/04-architecture/commercial-service-families.md,
    /codex/14-customer-journeys/_ssot-rules/04-dart-commercial-axes.md,
    /codex/16-strategy-playbooks/infra-spec/stage-3e-g2-env-split.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Rule 12 — Service-family scope rules

> **Purpose.** Codify hard service-family scope constraints as machine-readable rules, enforced as a pre-check inside
> G1.6's `access_control` formula. Matching YAML lives at
> [`12-service-family-scope-rules.yaml`](./12-service-family-scope-rules.yaml). Validator:
> [`_tools/validate_scope_yaml.py`](./_tools/validate_scope_yaml.py).

> **Rule-number lineage.** Stage 3E §1.11's initial draft pencilled this in as "rule 11". Slot 11 was taken by
> [`11-codex-scope-registry.md`](./11-codex-scope-registry.md) (G1.9, shipped 2026-04-20). This rule takes slot 12.

---

## 1. Why this rule exists

Today the rules "IM clients don't see observability", "DART clients don't touch the strategy-catalogue admin toggle",
"Reg Umbrella clients don't see research/promote" live scattered across UI route-gating, demo-ops docs, and implicit
audience assumptions.

G1.11 lifts those constraints into a single YAML table with three properties:

1. **Machine-readable.** Parsed at UAC module load by
   `unified_api_contracts.internal.architecture_v2.service_family_scope`.
2. **Enforced.** Wired into G1.6's `access_control()` formula as a short-circuit pre-check (drops to `deny` before the
   generic gate).
3. **Audience-driven, not ACL-driven.** Scope is a commercial-reality boundary (see rule 04 `dart-commercial-axes`), not
   a per-user permission list. That's what lets `admin` and `IM_desk` share the same table with only `excludes: []`
   overrides.

---

## 2. The six service families (closed enum)

| Family                | Surfaces                                             | Excludes                                                   | Use case                                                           |
| --------------------- | ---------------------------------------------------- | ---------------------------------------------------------- | ------------------------------------------------------------------ |
| `IM`                  | reporting, client_portal                             | observe, research, promote, strategy_catalogue_admin       | Odum-run funds; client sees reporting + capital statements.        |
| `RegUmbrella`         | reporting, compliance_overlay                        | observe, research, promote, strategy_catalogue_admin       | Emerging manager under Odum's FCA permissions. Compliance-centric. |
| `DART`                | reporting, observe, research, promote, trading, data | strategy_catalogue_admin                                   | Full DART subscriber. Operates the full lifecycle.                 |
| `DART_reporting_only` | reporting                                            | observe, research, promote, strategy_catalogue_admin, data | DART-reporting-only sub-family sharing the IM reporting tool.      |
| `admin`               | everything, strategy_catalogue_admin                 | —                                                          | Odum internal admin.                                               |
| `IM_desk`             | strategy_catalogue_admin, reporting                  | —                                                          | Odum IM desk operator — locks/unlocks demo slots.                  |

The enum is closed. Adding a family requires an operator-approved plan + rule-12 YAML extension + new rule-12 test
cases. Do NOT add families ad-hoc.

---

## 3. Route-allowlist vs surfaces

Each family has two fields that must both allow for a route to be in scope:

- `surfaces`: the audience-semantic vocabulary. Human-readable; used by sales-ops docs + codex doc cross-refs. Values
  match the pretty names in rule 04 `dart-commercial-axes.md`.
- `route_allowlist`: glob-style patterns matched by `check_service_family_scope(user, route)`. Negation with `!` prefix
  is supported. Matches are case-sensitive.

**Why both?** `surfaces` is the vocabulary humans think in ("DART gets research"). `route_allowlist` is what the code
enforces ("`/services/research/**`" allows matching URLs). They're kept separate so a doc can talk about a surface
without pinning the URL layout, and a URL change doesn't require editing the audience vocabulary.

---

## 4. Composition with `access_control`

G1.6's `access_control(user, route, item, phase)` adds a pre-check:

```python
def access_control(user, route, item, phase, *, availability_registry=..., capability_registry=...):
    # G1.11 pre-check (rule 12)
    scope_decision = check_service_family_scope(user, route)
    if scope_decision.status == "deny":
        return AccessDecision(
            status="deny",
            reason=scope_decision.reason,
            upgrade_hint=scope_decision.upgrade_hint,
        )

    # ... existing G1.6 body ...
```

Scope deny short-circuits; visibility + phase gates never run. Scope allow falls through to the full `access_control`
body. Admin audience short-circuits at the `access_control` level (before scope), so admin never hits the scope check.

---

## 5. Dev / staging / prod parity (rule-03 hard requirement)

Identical YAML + identical enforcement across environments. Only the user-identity source differs (mock-provider seed vs
Firebase). Any divergence (e.g. enabling a family in dev-only) is a rule-03 violation and gets caught by the Playwright
spec at `tests/e2e/playbooks/refactor/refactor-g1-11-service-family-scope.spec.ts` dev-vs-staging parity assertion.

---

## 6. Cross-references

- [`04-dart-commercial-axes.md`](./04-dart-commercial-axes.md) — commercial axes that generate the service families.
- [`03-same-system-principle.md`](./03-same-system-principle.md) — dev/ staging/prod parity rationale.
- [`../shared-core/client-reporting-demo-walkthrough.md`](../shared-core/client-reporting-demo-walkthrough.md) — shared
  reporting surface between IM + DART_reporting_only + RegUmbrella.
- [`../shared-core/org-fund-client-entity-model.md`](../shared-core/org-fund-client-entity-model.md) — org/fund/client
  entity shape underlying scope claims.
- [`../cross-cutting/sma-vs-pooled.md`](../playbook-concepts/sma-vs-pooled.md) — SMA vs Pooled axis (applies to IM +
  RegUmbrella, not DART).
- [`../../09-strategy/TIER_ZERO_UI_DEMO_AND_PARITY.md`](../../09-strategy/TIER_ZERO_UI_DEMO_AND_PARITY.md) — tier-zero
  UI demo parity story.
- UAC:
  [`unified_api_contracts/internal/architecture_v2/service_family_scope.py`](../../../../unified-api-contracts/unified_api_contracts/internal/architecture_v2/service_family_scope.py)
- UAC:
  [`unified_api_contracts/internal/architecture_v2/derivation.py`](../../../../unified-api-contracts/unified_api_contracts/internal/architecture_v2/derivation.py)
  (pre-check wiring).
- Playwright:
  [`tests/e2e/playbooks/refactor/refactor-g1-11-service-family-scope.spec.ts`](../../../../unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g1-11-service-family-scope.spec.ts)

---

## 7. Ownership

- **YAML + validator**: edit via an operator-approved plan. Any family add/rename requires a rule-12 amendment commit +
  new test cases.
- **Enforcement**: `service_family_scope.py` in UAC; any behaviour change requires the unit test suite to pass + a
  derivation integration test.
- **Cross-refs**: rule 04 carries a pointer to this rule — do NOT duplicate the table in rule 04.
