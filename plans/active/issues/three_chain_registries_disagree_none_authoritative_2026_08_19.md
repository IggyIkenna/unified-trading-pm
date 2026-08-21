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
    /plans/archive/2026_08/issues/uac_get_venue_asset_group_silently_returns_cefi_for_all_venues_2026_08_19.md,
    /plans/epics/system_readiness_master.md,
  ]
context_scope:
  [
    /plans/audit/results/registry_ground_truth_2026_08_19.md,
    /plans/archive/2026_08/issues/uac_get_venue_asset_group_silently_returns_cefi_for_all_venues_2026_08_19.md,
    unified-api-contracts/unified_api_contracts/canonical/crosscutting/defi.py,
    unified-api-contracts/tests/unit/test_chain_registry_ssot.py,
    unified-api-contracts/unified_api_contracts/registry/chain_env.py,
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

- [x] ✅ [BACKEND] P0. **`ChainKind` declared the vocabulary SSOT — unified-api-contracts@27ebc544b2.** Chose
      "derive from it" over "or die", because measurement showed the three are NOT three answers to one question —
      they own different concerns (see Progress Log). The decision is stated in `ChainKind`'s own docstring naming
      the other two and what each owns, and in `KNOWN_CHAINS`'s docstring naming the concern it owns, so the next
      reader does not re-derive it.
- [x] ✅ [BACKEND] P0. **`ChainKind.PLASMA` added — unified-api-contracts@27ebc544b2.** Confirmed a straight
      omission exactly as described: `MAINNET_CHAIN_IDS["PLASMA"] = 9745` and a `CHAIN_GENESIS_DATES` entry
      (2025-09-25) have both existed since the 2026-07-27 onboarding, so the chain was live everywhere EXCEPT the
      canonical enum. `test_chainkind_covers_every_mainnet_chain_id` now blocks the repeat.
- [x] ✅ [BACKEND] P0. **`SCROLL` added to `KNOWN_CHAINS`; `starknet` deliberately NOT added — this todo's premise
      was wrong.** MEASURED: `EXTENDED-STARKNET` is a `VENUES_BY_ASSET_GROUP["cefi"]` member and does **not** appear
      in `ALL_DEFI_VENUES`. `KNOWN_CHAINS` is a DeFi venue-string token-recognition set, so a CeFi venue cannot
      justify an entry in it, and adding `starknet` would have been cargo-culted from a mis-stated premise.
      (`ChainKind` already carries `starknet` — that is the right home for it.) `SCROLL` *was* justified and added,
      **plus `PLASMA`, which this todo missed**: `AAVE-PLASMA`/`FLUID-PLASMA` had the identical defect.
      `KNOWN_CHAINS` also held **12** entries at measurement, not the 10 stated in this doc's table.
- [x] ✅ [AGENT] P0. **Consumers enumerated; the silent under-count is REAL and now named.** `ChainKind` — 6 UAC
      modules + MTDS `adapters/umi_tick_provider.py`. `KNOWN_CHAINS` — instruments-service
      `engine/orchestrator/writers.py` and `catalogue.py`, MTDS `scripts/rebuild_mtds_manifest.py`, each doing
      `if chain in KNOWN_CHAINS:` and therefore **silently taking the else-branch for all four SCROLL/PLASMA
      venues** until this fix. `VENUE_CHAIN_MAP` — UAC-internal only (no cross-repo consumer). The code side is
      fixed; **whether any already-written chain-scoped GCS/manifest output needs re-checking is data verification
      in T2-owned repos** — filed on T2's plan as `[FROM-T1]` rather than assumed clean. (Also found: several
      instruments-service scripts hand-roll their OWN `KNOWN_CHAINS` literal instead of importing UAC's — a
      duplicate-vocabulary risk in a repo this tranche does not own; included in the same T2 request.)
- [ ] BLOCKED-OPERATOR-DECISION [REVIEW] P1. **Resolve the 13-vs-14 discrepancy — still genuinely blocked, same
      operator decision, re-verified 2026-08-20 not re-solved.** `chain_env.py:655-656` still reads "ONCHAIN
      pseudo-chain — Alchemy Infrastructure data, not a real L1/L2; pending operator decision on whether to keep or
      remove this venue" — unchanged since this doc was filed. The two counts are precisely characterized (not
      newly re-derived, confirming the earlier finding still holds): naive `venue.split("-", 1)[1]` over
      `ALL_DEFI_VENUES` = 14 (includes `ONCHAIN` and the `native-solana` split artifact); `parse_defi_venue()`
      correctly resolves both, and whether `ONCHAIN` counts as a "chain" is exactly the pending decision — keep it
      → 13 real chains + `ONCHAIN` as a declared pseudo-chain; remove it → 13 real chains, full stop, no separate
      count needed. **Retagged from `[REVIEW]` — nothing left to review, this is purely waiting on the operator
      call `chain_env.py` itself already names.**
- [x] ✅ [REVIEW] P1. **Answered 2026-08-20 — No, none of the three denominators feed published coverage; no
      under-count risk from this doc's finding.** Checked `instruments-service/scripts/measure_honest_coverage.py`
      directly (the peer's earlier check only covered `VENUE_CHAIN_MAP`): its ONLY UAC import is
      `OUT_OF_COVERAGE_WINDOW_REASONS`/`EmptyConfirmedReason` — no `KNOWN_CHAINS`, `VENUE_CHAIN_MAP`, or `ChainKind`
      import anywhere in the file. `KNOWN_CHAINS` appears exactly once, in a docstring explaining WHY
      `_normalise_chain_series()` doesn't need case-migration handling ("chains are UPPERCASE wire tokens") — not
      as a denominator. The function groups by whatever chain STRING VALUES actually appear in the data (data-driven),
      never against a fixed/complete registry list — so this doc's chain-registry disagreement cannot silently
      under-count published coverage, regardless of which of the three registries (or none) is "authoritative."

## Progress Log

**2026-08-19 — filed.** Consolidated from three independent sub-agent findings during the client-artefact
expansion; each agent independently hit the problem of having no single defensible chain source.

**2026-08-19 — FIXED, unified-api-contracts@27ebc544b2** (T1 code-readiness tranche, slot-6).

**The framing in this doc's title and table is partly a category error, and the fix reflects the measurement, not
the framing.** These are not three competing answers to "which chains does the platform support":

| Registry | Concern it actually owns | Verdict |
| --- | --- | --- |
| `ChainKind` | the chain VOCABULARY (lowercase canonical values) | promoted to SSOT |
| `KNOWN_CHAINS` | UPPERCASE token recognition for SPLITTING `<PROTOCOL>-<CHAIN>` venue strings | kept, now derives |
| `VENUE_CHAIN_MAP` | venue→chain for DeFi shared-wallet routing | kept, values must be `ChainKind` |

`VENUE_CHAIN_MAP` covering "4 chains / 15 of 192 venues" is therefore its correct SCOPE (only wallet-sharing venues
belong in it), not the under-count the table implies. Merging the three would have destroyed real distinctions.

**But the underlying defect was real, and worse than "under-reporting".** Four live `ALL_DEFI_VENUES` entries —
`AAVE_V3-SCROLL`, `COMPOUND_V3-SCROLL`, `AAVE-PLASMA`, `FLUID-PLASMA` — parse (via `parse_defi_venue()`) to chain
tokens `SCROLL`/`PLASMA` that `KNOWN_CHAINS` did not contain, so every `if chain in KNOWN_CHAINS:` consumer took
the else-branch for them, silently. That is a live data-path defect, not a cosmetic registry-count disagreement.

**Three claims in this doc corrected by measurement** (each re-measured, not reasoned):

1. `KNOWN_CHAINS` held **12** entries, not 10.
2. `starknet` has **no** DeFi venue justifying a `KNOWN_CHAINS` entry — `EXTENDED-STARKNET` is a CeFi venue and is
   absent from `ALL_DEFI_VENUES`. Not added, deliberately.
3. `PLASMA` was missing from `KNOWN_CHAINS` too — this doc named only `scroll`/`starknet`.

**What now prevents the drift recurring** (`tests/unit/test_chain_registry_ssot.py`, 7 tests): `ChainKind` ⊇/⊆
`MAINNET_CHAIN_IDS`, `ChainKind` ⊇ `CHAIN_GENESIS_DATES`, every live DeFi venue's parsed chain token is recognised
by `KNOWN_CHAINS`, every `KNOWN_CHAINS` member is a `ChainKind` or one of two explicitly-allowlisted venue-as-L1
tokens (`HYPERLIQUID`, `ASTER`), and every `VENUE_CHAIN_MAP` value is a `ChainKind` value. All 7 pass; the six
containment properties were also executed standalone as direct probes.

**Still open**: the 13-vs-14 count (see todo — partially diagnosed, blocked on the pending `ONCHAIN` pseudo-chain
decision) and the coverage-denominator check. Neither closed on a plausible-looking number.
- **context-scout 2026-08-20**: populated/refreshed context_scope (6 entries)
- **na-eligibility-audit 2026-08-21** (defi tranche, wave 2): KEEP-NA, valid — re-confirmed; sole open item (the 13-vs-14 chain-count discrepancy) remains explicitly `BLOCKED-OPERATOR-DECISION` pending the ONCHAIN pseudo-chain keep/remove ruling named in `chain_env.py:655-656`; not worker-determinable. Doc stays `assigned_vm: NA`.
