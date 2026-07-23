---
doc_type: codex-ssot
title: UAC `internal/*.py` Module Docstring Rule (G-15 codification)
summary: >-
  G-15 rule: every public `unified_api_contracts/internal/*.py` module consumed by a cross-cutting service surface must
  cite its consumer(s), cross-reference the canonical codex SSOT for that surface, and cite the introducing plan/issue
  in its module docstring (`manual_audit_paths.py` is the reference impl).
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [deployment-api, deployment-ui, unified-api-contracts, unified-trading-library]
scope: [engineer]
tags: [uac, docspec, ssot-audit, refactor]
related: [/codex/02-data/contracts-scope-and-layout.md, /codex/13-codex-governance/SSOT-BOUNDARY.md]
created: 2026-05-12
authoritative_for: [UAC internal module docstring rule (G-15 consumer-citation)]
referenced_by:
owner:
last_reviewed: 2026-05-12
code_refs:
source: plans/archive/issues/codex_audit_governance_2026_05_12.md G-15
---

# UAC `internal/*.py` Module Docstring Rule (G-15 codification)

## TL;DR

Every `unified-api-contracts/unified_api_contracts/internal/*.py` module that ships a contract / schema / helper
**consumed by cross-cutting service surfaces** (not a UAC-internal-only utility) MUST:

1. Cite the **consumer(s)** by name in the module docstring (which service / repo / surface depends on this module).
2. Cross-reference the **corresponding codex doc** that is the canonical SSOT for the consumer surface (e.g.
   `/codex/02-data/availability-manifest-and-data-status.md` for manifest-shape modules).
3. Cite the **plan or issue doc** that introduced the module (provenance citation).

Why: UAC internal modules are the workspace-wide contract surface for inter-service comms. Without the consumer
citation, UAC contracts drift into orphaned-spec status — the original consumer evolves, the contract stagnates, and
downstream readers can't tell which is authoritative. This rule turns every new internal module into a self-documenting
bidirectional link.

## When to apply

This rule applies to **public** internal-module additions whose surface is referenced by:

- ≥1 service repo (`*_service`, `*-service`, `*-api`)
- ≥1 cross-cutting library (`unified-trading-library`, `unified-cloud-interface`, etc.)
- ≥1 UI / deployment-api / ops surface

It does NOT apply to:

- Private helpers used only within `unified_api_contracts/canonical/` or `unified_api_contracts/external/`
- One-off internal types narrowly scoped to a single canonical schema's normalize layer
- Test-only fixtures under `unified_api_contracts/testing/`

When uncertain: apply the rule (the cost of an extra docstring is trivial; the cost of an orphaned contract is not).

## Required docstring shape

```python
"""<one-line module purpose>.

Consumers:
- <repo>/<file>: <what it consumes from this module>
- <repo>/<file>: <what it consumes from this module>

Cross-reference:
- codex SSOT: `<codex/XX-area/doc-name.md>` § "<section name>"
- introduced by: `<plans/active/...md>` or `<plans/active/issues/...md>` <finding-id>
"""
```

## Reference: `manual_audit_paths.py` (G-15 reference impl)

The 2026-05-12 slot 8 ship of `unified_api_contracts/internal/manual_audit_paths.py` is the canonical reference
implementation of this rule. Its docstring cites:

- **Consumers**: position-balance-monitor-service (manual-trade-booking audit-log surface), deployment-ui (manual trade
  UI surface).
- **Cross-reference**: `/codex/07-security/audit-logging.md` (canonical audit-path SSOT) +
  `/codex/14-customer-journeys/manual-trade-booking/manual-trade-booking.md`.
- **Provenance**: `plans/active/manual_trade_booking_2026_05_07.md` Phase X.

When extending UAC `internal/` with a new consumer-facing module, mirror this shape exactly.

## Enforcement

Today: reviewer-discipline only. Code review for any PR adding a `unified_api_contracts/internal/*.py` file MUST verify
the docstring follows the shape above.

**Future ratchet** (P2 backlog): a QG STEP that walks `unified-api-contracts/unified_api_contracts/internal/*.py`,
checks each for `^Consumers:` + `^Cross-reference:` + `^codex SSOT:` headers in the module docstring, fails the build if
missing. Filed against `plans/archive/issues/codex_audit_governance_2026_05_12.md` G-15 (this codex doc is the design
half; the QG ratchet is the enforcement half).

## Composes with

- `/codex/02-data/contracts-scope-and-layout.md` (the canonical → internal scope-boundary rule)
- `/codex/13-codex-governance/SSOT-BOUNDARY.md` (codex vs PM placement rules)
- `cursor-configs/CLAUDE.md` § "Post-Plan-Phase Codex Audit" (the broader codex-update HARD RULE)

## Anti-patterns

- **Module docstring that only says "Internal contract for X"** — useless without naming the consumer.
- **Docstring citing the canonical codex doc but no consumer** — operator can't tell if anyone actually uses it.
- **Bumping the module's contents without updating Consumers list** — stale citation is worse than no citation.
- **Citing a plan that's already archived without migrating provenance to a successor doc** — provenance chain breaks.
