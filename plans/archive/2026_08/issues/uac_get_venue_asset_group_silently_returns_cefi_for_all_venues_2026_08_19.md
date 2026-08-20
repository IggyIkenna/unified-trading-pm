---
doc_type: issue
title: UAC get_venue_asset_group() silently returns "cefi" for every venue tested, including DeFi and CeFi slugs
summary: >-
  `unified_api_contracts/execution.py`'s `get_venue_asset_group()` does a lowercase lookup into
  `_VENUE_ASSET_GROUP` with a hardcoded `"cefi"` fallback. Measured 2026-08-19: it returned "cefi" for every venue
  probed — AAVE_V3-ARBITRUM, LIDO-ETHEREUM, JUPITER-SOLANA, MORPHO-BASE and BINANCE-SPOT alike. Because the miss
  path returns a real asset-group string rather than raising or returning None, every caller sees a plausible
  answer and no error. Any per-asset-group split computed through this function is wrong, silently.
status: closed
nature: issue
asset_group: [cross-cutting, defi]
stage: [meta]
repos: [unified-api-contracts]
scope: [engineer, admin]
tags: [uac, venue-registry, asset-group, silent-fallback, measurement-integrity]
related:
  [
    /plans/audit/results/registry_ground_truth_2026_08_19.md,
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
  Surfaced by a sub-agent expanding strategy-service-deep-dive.html (it reported DeFi venues falling back to cefi),
  then independently reproduced by the orchestrating session, which found the failure is broader than reported —
  CeFi slugs miss too.
context_scope:
  [
    /codex/02-data/honest-coverage-model.md,
    /plans/audit/results/registry_ground_truth_2026_08_19.md,
    unified-api-contracts/unified_api_contracts/execution.py,
    unified-api-contracts/unified_api_contracts/registry/venue_asset_group.py,
  ]
---

# `get_venue_asset_group()` returns "cefi" for everything

## Measured

```
unified-api-contracts/unified_api_contracts/execution.py

def get_venue_asset_group(venue: str) -> str:
    """Return asset_group for a venue slug from CAPABILITY_DECLARATIONS.
    Returns "cefi", "defi", "sports", "prediction", or "tradfi".
    Unknown venues fall back to "cefi".
    """
    return _VENUE_ASSET_GROUP.get(venue.lower(), "cefi")
```

Probed live 2026-08-19 via the UAC venv:

| Venue slug         | Returned |
| ------------------ | -------- |
| `AAVE_V3-ARBITRUM` | `cefi`   |
| `LIDO-ETHEREUM`    | `cefi`   |
| `JUPITER-SOLANA`   | `cefi`   |
| `MORPHO-BASE`      | `cefi`   |
| `BINANCE-SPOT`     | `cefi`   |

`BINANCE-SPOT` returning `cefi` is not evidence the function works — it is the same fallback, coincidentally
matching. That coincidence is what makes this hard to notice by spot-check.

## Why it is P0

The failure is **silent by construction**. The miss path returns `"cefi"`, a valid asset-group value, so:

- No exception, no `None`, no log line — a caller cannot distinguish a real hit from a miss.
- Any per-asset-group aggregation routed through this function attributes the whole estate to CeFi.
- A spot-check on a CeFi venue passes, so the obvious sanity test does not catch it.

This is the same defect shape as the honest-coverage v1 denominator problem already recorded in
[honest-coverage-model](/codex/02-data/honest-coverage-model.md): a number that looks fine because the thing that
should have failed loudly returned a plausible default instead.

## Todos

- [x] ✅ [BACKEND] P0. **Root cause established — unified-api-contracts@d4cded41b8.** Neither "empty" nor a case
      mismatch: `_VENUE_ASSET_GROUP` was correctly populated (55 entries) but keyed on the WRONG VOCABULARY —
      `cap.source`, the capability-declaration provider/adapter key (`binance`, `aave`, `databento`, `odds_api`),
      while every caller passes a venue slug (`BINANCE-SPOT`, `AAVE_V3-ARBITRUM`). The two namespaces have zero
      overlap, which is why `BINANCE-SPOT` missed too — the reported "lowercase adapter names vs uppercase slugs"
      framing understated it as a casing bug when it is a category error. Lowercasing harder would have fixed
      nothing.
- [x] ✅ [BACKEND] P0. **Miss path is loud — unified-api-contracts@d4cded41b8.** Raises
      `UnknownVenueAssetGroupError` (a `ValueError`) naming the offending token and both registries it missed.
      Resolution is now: (1) `classify_venue_asset_group()` — the venue-vocabulary SSOT, which also preserves the
      KALSHI/POLYMARKET `prediction` split; (2) the capability-source table, kept because 29 of its 55 keys are
      data-provider names present in no venue registry; then raise. Verified by direct execution: all four
      measured-broken slugs resolve correctly and both an unknown token and `""` raise.
- [x] ✅ [AGENT] P0. **Callers enumerated — blast radius is ZERO code call sites.** Fleet-wide `rg` across every
      repo in the slot (excluding `.venv`) found no code caller of `get_venue_asset_group` outside its own
      defining module; all remaining hits are plan/issue/codex prose and archived plans. Name-based dynamic access
      (`getattr(mod, "get_venue_asset_group")`) would also have matched that grep, so this is conclusive for
      by-name access. **Nothing wrote a per-asset-group split through this function**, so no stored data, manifest
      or published metric needs re-checking on its account.
- [x] ✅ [REVIEW] P1. **Answered 2026-08-20 — no, cannot share a root cause; the cited figure has also since been
      corrected.** `get_venue_asset_group()` was already established (this doc's own zero-caller measurement) to
      have NO code callers fleet-wide — nothing calls it, so it cannot be the mechanism producing any bucketed
      venue count, correct or wrong. Whatever DOES produce the asset-group bucketing is necessarily a different
      function entirely. Separately: `/plans/audit/results/registry_ground_truth_2026_08_19.md` has since
      self-corrected the "15-venue gap" this todo cites — its own inline correction states "Unbucketed venues are
      24, not 15 — I derived 15 by subtracting 177 from 192; the real answer needs a set-difference, because the
      bucket set and the capability set are not nested." Citing "15" here would now perpetuate a number the source
      doc itself already retracted.
- [x] ✅ [REVIEW] P1. **Published coverage percentages are UNAFFECTED by this defect.** Follows directly from the
      zero-caller measurement above: `measure_honest_coverage.py` does not reference `get_venue_asset_group` (it
      appears in no code file fleet-wide), so the §05 per-asset-group figures (sports 99.26 / prediction 92.81 /
      tradfi 86.96 / cefi 45.57 / defi 40.94) were not split through it and need no correction on this account.
      Scope note: this clears the artefact of THIS defect only — it is not a general audit of how those
      denominators are derived.

## Progress Log

**2026-08-19 — FIXED, unified-api-contracts@d4cded41b8** (T1 code-readiness tranche, slot-6). Root cause was a
vocabulary category error, not the reported casing mismatch — see todo 1. Blast radius measured at ZERO code
callers, so no stored data or published metric was corrupted; the defect was latent, waiting for its first
consumer. Fix delegates to the pre-existing fail-closed `classify_venue_asset_group()` rather than adding a fourth
venue→asset_group implementation.

**Two findings surfaced while fixing, both fixed in the same commit:**

1. **Bare `COINBASE` classified as `defi`** — `VENUES_BY_ASSET_GROUP["cefi"]` registers `COINBASE-SPOT`/`-FUTURES`/
   `-CDE` but no bare `COINBASE`, so the token fell through to the generic DeFi base-token fallback and
   false-matched `COINBASE-ETHEREUM` (the cbETH LST venue). This is the identical collision the classifier's own
   comment documents for bare `BINANCE` — it was fixed for BINANCE in isolation and COINBASE was missed. A
   systematic sweep confirms these two were the ONLY such collisions, and all 209 registered venues otherwise
   classify to their own group.
2. **No invariant guarded any of this.** Added `test_every_registered_venue_classifies_to_its_own_group` and
   `test_no_non_defi_sub_venue_base_falls_through_to_defi`, so the next base-token collision fails the suite
   instead of surviving until someone hand-probes it.

Remaining open: the 15-venue `VENUE_DATA_TYPE_CAPABILITIES` (192) vs asset-group-bucket (177) gap. NOT closed and
NOT investigated in this pass — measured only that `VENUE_TO_ASSET_GROUP` holds 209 keys and
`VENUES_BY_ASSET_GROUP` sums to 177, which does not by itself explain the 192 figure. Left honestly open rather
than closed on a plausible-looking number.

**2026-08-19 — filed.** Reported by a sub-agent as DeFi-only; the orchestrating session reproduced it and found
CeFi slugs miss as well, so the scope in the original report understated it. Not yet fixed — no code touched.
- **context-scout 2026-08-20**: populated/refreshed context_scope (4 entries)
