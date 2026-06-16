---
title: "16-strategy-playbooks — domain strategy + infra playbooks"
type: codex-section-readme
status: active
created: 2026-05-08
scope: [engineer]
related:
  - codex/14-customer-journeys/README.md
  - codex/15-runbooks/README.md
  - codex/09-strategy/README.md
  - codex/04-architecture/README.md
  - codex/05-infrastructure/README.md
---

# 16-strategy-playbooks

This section is the SSOT for **domain-specific strategy + infrastructure playbooks** — the long-form architectural and
operational documents that describe how a particular asset_group / archetype / infra-stage is supposed to work, end-to-
end. Unlike `15-runbooks/`, the documents here are NOT primarily on-call procedures — they are the design + operational
playbooks the implementer reads BEFORE building, and the operator reads to understand what the system is supposed to do.

## What lives here

- **`defi/`** — DeFi-specific runbooks. Currently includes the venue-collateral playbook for Aave + Uniswap +
  Hyperliquid hedge-leg orchestration. Future additions: per-protocol operational notes, custody-flow playbooks,
  cross-chain bridging procedures.
- **`strategy/`** — Per-archetype strategy playbooks. Currently includes the CME ↔ Polymarket arbitrage archetype
  design doc. Future additions: per-archetype playbooks for each strategy in `09-strategy/architecture-v2/archetypes/`.
- **`ml/`** — ML lifecycle playbooks. Currently includes the CeFi ML live-serving playbook. Future additions: feature-
  engineering playbooks per asset_group, model-promotion procedures, drift-detection runbooks.
- **`infra-spec/`** — Multi-stage infrastructure refactor specs (the Stage 3a-3e series). Captures the canonical infra
  audit + schema design + derivation engine + g2-env split + refactor plan. These are design specs, not on-call
  runbooks.

## What does NOT live here

- **Customer-facing flows + onboarding** → [`codex/14-customer-journeys/`](../14-customer-journeys/README.md).
  Investment-management demo, fund-org hierarchy, page-triage, role-based audiences.
- **Live-trading on-call runbooks** → [`codex/15-runbooks/`](../15-runbooks/README.md). Per-alert procedures, T+1 audit
  runbook, smoke testing, backfill completion.
- **Strategy architecture + capability declarations** → [`codex/09-strategy/`](../09-strategy/README.md). Archetype
  definitions, strategy-catalogue 3-tier model, cross-cutting strategy mechanics. The `strategy/` sub-dir here is for
  per-archetype operational playbooks, not the canonical architecture surface.
- **Cross-cutting infrastructure topology** → [`codex/05-infrastructure/`](../05-infrastructure/README.md). Live-
  deployment monitoring, runtime tiers, AWS/GCP cloud-parity model. The `infra-spec/` sub-dir here is for the multi-
  stage refactor specs, not the steady-state topology.

## Cross-link conventions

Every playbook in this section MUST:

1. Cite the canonical architecture surface in `09-strategy/architecture-v2/` (for strategy playbooks),
   `04-architecture/` (for cross-cutting architectural concerns), or `05-infrastructure/` (for infra-stage docs) as the
   upstream SSOT. The playbook here is the operational walkthrough; the architecture doc is the contract.
2. If a playbook references an alert code or runbook trigger, link to the corresponding runbook in
   [`codex/15-runbooks/`](../15-runbooks/README.md).
3. If a playbook describes a customer-visible flow (onboarding, demo, restriction-profile), link to the corresponding
   flow in [`codex/14-customer-journeys/`](../14-customer-journeys/README.md).
4. For DeFi playbooks, cross-link to the master plan readiness items in
   [`plans/active/master_to_live_defi_2026_05_23.md`](../../plans/active/master_to_live_defi_2026_05_23.md) so the
   playbook ties to the May-23 cutover criterion.

## How to add a new playbook

1. Place under the appropriate sub-dir (`defi/`, `strategy/`, `ml/`, `infra-spec/`). Add a new sub-dir for a new domain
   only if 3+ playbooks would live there; otherwise extend an existing sub-dir.
2. Cross-link upstream architecture / capability declarations in the frontmatter `related:` block.
3. If the playbook is workspace-critical (e.g. blocks a master plan readiness item), add a row to
   `codex/00-SSOT-INDEX.md` § strategy-playbooks.

## History

This section was carved out of the legacy `14-customer-journeys/` directory in 2026-05-08 per
[`plans/active/codex_refactor_2026_05_08.md`](../../plans/active/codex_refactor_2026_05_08.md) Phase E.2 step 3. The
parent dir was renamed to `14-customer-journeys/` and split into three: `14-customer-journeys/` (audience flows),
`15-runbooks/` (on-call runbooks), `16-strategy-playbooks/` (this dir, domain strategy + infra playbooks).
