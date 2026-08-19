---
doc_type: issue
title: Three chain registries disagree and none is authoritative — ChainKind 23 (missing plasma), KNOWN_CHAINS 10, VENUE_CHAIN_MAP 4
summary: >-
  The same concern — which chains the platform supports — is declared in three separate registries that give three
  different answers, and every one of them is incomplete. ChainKind has 23 members but omits plasma, which has live
  venues in production. KNOWN_CHAINS carries 10 and omits scroll and starknet, both of which have live venues.
  VENUE_CHAIN_MAP carries 4 across 15 venues against 192 declared. Anything deriving chain coverage picks one of
  the three and silently under-reports by a different amount depending on which.
status: open
nature: issue
asset_group: [cross-cutting, defi]
stage: [meta]
repos: [unified-api-contracts]
scope: [engineer, admin]
tags: [uac, chain-registry, ssot, duplication, under-declaration]
related:
  [
    /plans/audit/results/registry_ground_truth_2026_08_19.md,
    /plans/active/issues/uac_get_venue_asset_group_silently_returns_cefi_for_all_venues_2026_08_19.md,
    /plans/epics/system_readiness_master.md,
  ]
created: 2026-08-19
last_updated: "2026-08-19"
parent_epic: system_readiness_master
assigned_vm: NA
locked_by:
locked_since:
resolved_by:
execution_scope: local-only
priority: P0
severity: P0
source: >-
  Surfaced across three independent sub-agents expanding the client artefacts on 2026-08-19, each of which had to
  pick a chain source and found the candidates disagreed. Consolidated by the orchestrating session.
---

# Three chain registries, three answers, none complete

| Registry          | Chains | Known omissions                                    |
| ----------------- | -----: | -------------------------------------------------- |
| `ChainKind`       | **23** | `plasma` — has live venues (AAVE-PLASMA, FLUID-PLASMA) |
| `KNOWN_CHAINS`    | **10** | `scroll`, `starknet` — both have live venues        |
| `VENUE_CHAIN_MAP` |  **4** | covers 15 venues against 192 declared               |

`ChainKind` is the closest to authoritative and is what the client artefacts now use — but it is **not** complete,
so "use ChainKind" is a better answer than the other two rather than a correct one.

## Why this is P0

This is the workspace's own no-duplication rule broken at the registry layer: one concern, three homes, three
answers. The consequences are not cosmetic.

- **Silent, source-dependent under-counting.** A consumer reading `VENUE_CHAIN_MAP` sees 4 chains; one reading
  `KNOWN_CHAINS` sees 10; one reading `ChainKind` sees 23. None errors. Each looks plausible.
- **It already produced a wrong number in this session.** An initial chain count was derived by grepping string
  literals rather than reading a registry, giving 19 — it missed 8 real chains and counted 3 transport variants
  (`hyperliquid_api`/`_rest`/`_testnet`) as chains. That the grep looked as credible as the registries is a symptom
  of there being no obvious authority to read.
- **Live production chains are missing from every candidate.** `plasma` is absent from `ChainKind`; `scroll` and
  `starknet` are absent from `KNOWN_CHAINS`. A chain can be in production and in none of the lists a consumer
  would think to check.

## Todos

- [ ] [BACKEND] P0. **Declare ONE authoritative chain SSOT and make the others derive from it or die.** Per the
      workspace's centralisation rule the answer is a single registry with the others importing it — not three
      hand-maintained lists that drift. `ChainKind` is the natural candidate. State the decision in the surviving
      registry's docstring so the next reader does not re-derive it.
- [ ] [BACKEND] P0. **Add `plasma` to the authoritative registry** — it has live venues (`AAVE-PLASMA`,
      `FLUID-PLASMA` via `DEFI_VENUE_TO_PROTOCOL`) and a mainnet chain ID in `chain_env.MAINNET_CHAIN_IDS`, so its
      absence is a straight omission, not a scoping decision.
- [ ] [BACKEND] P0. **Add `scroll` and `starknet` to `KNOWN_CHAINS`** or delete `KNOWN_CHAINS` in favour of the
      authoritative registry. Both have live venues today (`AAVE_V3-SCROLL`, `COMPOUND_V3-SCROLL`,
      `EXTENDED-STARKNET`).
- [ ] [AGENT] P0. **Enumerate every consumer of each of the three registries** and determine which number each one
      is currently getting. Anything that wrote a chain-scoped split to GCS, a manifest, or a published metric needs
      its output re-checked — the under-count is silent, so nothing will have flagged itself.
- [ ] [REVIEW] P1. **Resolve the 13-vs-14 discrepancy**: two independent agents counted chains-with-live-venues
      today and got 13 and 14. Both derived it from registries rather than guessing, so one of the two filters is
      subtly wrong. Settle it and record the correct filter, since this number now appears in client artefacts.
- [ ] [REVIEW] P1. **Check whether the published coverage denominators read any of these three.** A peer verified
      `measure_honest_coverage.py` does not read `VENUE_CHAIN_MAP`; the equivalent check for `KNOWN_CHAINS` and
      `ChainKind` has not been done. If a denominator reads the 10-chain or 4-chain list, published coverage is an
      under-count.

## Progress Log

**2026-08-19 — filed.** Consolidated from three independent sub-agent findings during the client-artefact
expansion; each agent independently hit the problem of having no single defensible chain source.
