---
doc_type: issue
title: UAC get_venue_asset_group() silently returns "cefi" for every venue tested, including DeFi and CeFi slugs
summary: >-
  `unified_api_contracts/execution.py`'s `get_venue_asset_group()` does a lowercase lookup into
  `_VENUE_ASSET_GROUP` with a hardcoded `"cefi"` fallback. Measured 2026-08-19: it returned "cefi" for every venue
  probed — AAVE_V3-ARBITRUM, LIDO-ETHEREUM, JUPITER-SOLANA, MORPHO-BASE and BINANCE-SPOT alike. Because the miss
  path returns a real asset-group string rather than raising or returning None, every caller sees a plausible
  answer and no error. Any per-asset-group split computed through this function is wrong, silently.
status: open
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

- [ ] [BACKEND] P0. **Establish whether `_VENUE_ASSET_GROUP` is empty, wrongly keyed, or populated from a source
      that no longer matches the venue vocabulary.** The sub-agent that first hit this reported a case mismatch —
      lowercase adapter names as keys versus the registry's uppercase `PROTOCOL-CHAIN` slugs — but that does not
      by itself explain `BINANCE-SPOT` missing. Determine the real cause before fixing; do not patch the symptom
      by lowercasing more aggressively.
- [ ] [BACKEND] P0. **Make the miss path loud.** A venue whose asset group cannot be resolved must raise or return
      `None`, never a plausible default. Per the workspace's fail-closed discipline, an unknown must not silently
      become an answer. Changing the fallback will surface every existing caller that relied on it — that is the
      point, and those call sites are the real blast radius.
- [ ] [AGENT] P0. **Enumerate every caller and assess damage.** Grep the fleet for `get_venue_asset_group`. For
      each call site, determine whether a wrong asset group corrupts stored data, a published metric, or only a
      log line. Anything that wrote a per-asset-group split to GCS or a manifest needs its output re-checked.
- [ ] [REVIEW] P1. **Cross-check against the venue-count discrepancy already recorded** in
      [registry ground truth](/plans/audit/results/registry_ground_truth_2026_08_19.md): 192 venues declared in
      `VENUE_DATA_TYPE_CAPABILITIES` but only 177 appearing in asset-group buckets. Confirm whether that 15-venue
      gap and this fallback share a root cause.
- [ ] [REVIEW] P1. **Confirm the published coverage percentages are unaffected.** A peer agent verified that
      `measure_honest_coverage.py` does not read `VENUE_CHAIN_MAP`; do the equivalent check for this function. The
      per-asset-group coverage figures now published in `platform-external-api-walkthrough.html` §05 (sports
      99.26 / prediction 92.81 / tradfi 86.96 / cefi 45.57 / defi 40.94) depend on the answer — if they were split
      via this function, they are wrong and the artefact must be corrected before it is sent.

## Progress Log

**2026-08-19 — filed.** Reported by a sub-agent as DeFi-only; the orchestrating session reproduced it and found
CeFi slugs miss as well, so the scope in the original report understated it. Not yet fixed — no code touched.
