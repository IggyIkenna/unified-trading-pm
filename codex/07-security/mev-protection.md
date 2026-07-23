---
doc_type: codex-ssot
title: MEV Protection (redirect)
summary:
  Redirect stub — MEV-protection SSOT moved 2026-05-10 to `04-architecture/mev-protection.md` (mechanism +
  implementation) and `09-strategy/architecture-v2/cross-cutting/mev-protection.md` (strategy policy); kept only for
  backwards-compat links, add no new content here.
status: superseded
nature: ssot
asset_group: [meta]
stage: [meta]
repos: []
scope: [engineer, admin]
tags: [defi, mev, execution, migration, ssot-audit]
related: [/codex/04-architecture/mev-protection.md, /codex/09-strategy/architecture-v2/cross-cutting/mev-protection.md]
created: 2026-04-03
authoritative_for:
referenced_by:
owner:
last_reviewed:
code_refs:
---

# MEV Protection (redirect)

> **MOVED 2026-05-10** per `cross_asset_group_catalogue_audit_2026_05_10` Phase 4 codex consolidation.
>
> **Canonical location**: [`/codex/04-architecture/mev-protection.md`](/codex/04-architecture/mev-protection.md).
>
> The implementation detail (MEVProtectionConfig + provider factory + protected RPC URLs SSOT + provider
> implementations + operational run-book + threat model + testing) was folded into the canonical
> `04-architecture/mev-protection.md` so there's a single SSOT instead of three drifting docs.
>
> Strategy-side policy narrative (per-strategy MEV policy YAML + per-chain rules + monitoring) lives at
> [`/codex/09-strategy/architecture-v2/cross-cutting/mev-protection.md`](/codex/09-strategy/architecture-v2/cross-cutting/mev-protection.md)
> and cross-references the canonical for the protection mechanism itself.
>
> This file is kept as a 1-page redirect for backwards-compatibility with prior workspace links.

## Why this redirect exists

The 2026-05-08 catalogue audit
([`plans/questions/defi_readiness_catalogue_2026_05_08.md`](../../plans/questions/defi_readiness_catalogue_2026_05_08.md))
flagged 3 mev-protection.md docs at risk of content drift:

- `/codex/07-security/mev-protection.md` (this file; was implementation-focused)
- `/codex/04-architecture/mev-protection.md` (was system-architecture-focused)
- `/codex/09-strategy/architecture-v2/cross-cutting/mev-protection.md` (was strategy-policy-focused)

`cross_asset_group_catalogue_audit_2026_05_10` Phase 4 consolidated these:

1. Canonical = `/codex/04-architecture/mev-protection.md` (most comprehensive system-architecture overview; absorbed the
   implementation detail from this file).
2. This file → 1-page redirect (kept for link backwards-compat; do not add new content here).
3. `09-strategy/architecture-v2/cross-cutting/mev-protection.md` → scope-narrowed strategy-side narrative with explicit
   cross-link to the canonical.

## Where to find what

If you came here looking for:

- **MEV threat model + protection mechanisms** (slippage / private mempool / gas strategy / L2 / Tenderly pre- flight) →
  [`04-architecture/mev-protection.md`](/codex/04-architecture/mev-protection.md) sections "Threat Model" + "How the
  System Protects Against MEV".
- **MEVProtectionConfig + provider factory + protected RPC URLs SSOT** → same canonical doc, section "Implementation:
  MEVProtectionConfig + Provider Factory".
- **Provider implementations** (NoProtection / PrivateMempool / Flashbots / Jito) → same canonical doc, section
  "Provider Implementations".
- **Operational run-book** → same canonical doc, section "Operational Run-Book".
- **Per-strategy MEV policy YAML + per-chain rules + monitoring** →
  [`09-strategy/architecture-v2/cross-cutting/mev-protection.md`](/codex/09-strategy/architecture-v2/cross-cutting/mev-protection.md).
- **Per-chain RPC + MEV endpoint + Tenderly + gas oracle matrix** →
  [`05-infrastructure/chain-rpc-mev-tenderly.md`](/codex/05-infrastructure/chain-rpc-mev-tenderly.md).
