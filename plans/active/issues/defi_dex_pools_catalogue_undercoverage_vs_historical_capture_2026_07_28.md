---
doc_type: issue
title: DeFi dex_pools instruments-service catalogue drastically under-covers historically-captured pools
summary:
  A content-verified dry-run of the new address-keyed-leaf purge tool found ~74% of historically-captured dex_pool_state
  data for curve/sushiswap/velodrome_v2/trader_joe_v2 has no catalogue-covered symbol-named replacement and never will
  under the current catalogue population -- the instruments-service DeFi pool catalogue is a narrow "currently-active"
  snapshot, not a full historical discovery mechanism. Makes defi_dex_pool_symbol_fix_backfill_purge_2026_07_25.md todo
  5's literal "zero unattributed leaves remain" done-when unsafe to pursue (would require deleting content with no
  verified replacement).
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service, instruments-service]
scope: [engineer]
tags: [defi, dex-pools, catalogue, instruments-service, honest-coverage]
related:
  [
    defi_dex_pool_symbol_fix_backfill_purge_2026_07_25,
    defi_dex_pools_subgraph_query_missing_input_tokens_2026_07_25,
    cefi_enumeration_audit_instrument_type_leakage_and_catalogue_orphans_2026_07_27,
  ]
created: 2026-07-28
author: slot-16
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: research
drift_direction: worsening-slowly
source: [plans/active/defi_dex_pool_symbol_fix_backfill_purge_2026_07_25.md]
resolved_by:
locked_by:
---

# DeFi dex_pools instruments-service catalogue drastically under-covers historically-captured pools

## What I found

While executing `defi_dex_pool_symbol_fix_backfill_purge_2026_07_25.md` todo 5 (purge superseded address-keyed
`dex_pool_state` leaves for curve/sushiswap/velodrome_v2/trader_joe_v2), I built a content-verified purge tool
(`market-tick-data-service@249dc019`, `scripts/one_offs/purge_superseded_dex_pool_address_keyed_leaves_2026_07_28.py`)
that only deletes an old address-keyed leaf when a symbol-named sibling in the SAME (day, venue, chain) directory has a
matching `pool_address` — i.e., a real, content-verified replacement written by the 2026-07-27 symbol-resolution fix's
backfill.

A full dry-run across the confirmed-recoverable range (2020-01-01..2026-07-28, curve ETHEREUM+AVALANCHE / sushiswap
ARBITRUM / velodrome_v2 OPTIMISM / trader_joe_v2 AVALANCHE) found:

- **190,955 leaves SAFE** (content-verified superseded — a genuine symbol-named replacement exists)
- **541,890 leaves FLAGGED_NO_MATCHING_REPLACEMENT** (no replacement — the catalogue-scoped backfill never touched this
  exact pool+day)

That is, **~74% of all historically-captured address-keyed `dex_pool_state` data for these 4 protocols has NO
catalogue-covered replacement and never will under the current catalogue population**, because `dex_pools_handler.py`'s
catalogue-filter (`_catalogue_filter.py`) only queries the subgraph for pool addresses the `prod/catalog.parquet`
instruments-service catalogue currently lists in-window — a deliberately narrow "expected pool universe," NOT a full
historical discovery mechanism. A concrete example that first surfaced this: sushiswap/ARBITRUM's catalogue lists
exactly 4 pools, but the historical address-keyed data (written by the OLD, catalogue-agnostic pre-fix code path, still
running today via the standing `mtds-dex-pools-backfill` VM's own discovery mechanism for the other 12 default
protocols) shows well over 100 distinct pool addresses captured historically for that same venue/chain.

## Why it matters

1. **This todo's own done-when is unsatisfiable as originally written.**
   `defi_dex_pool_symbol_fix_backfill_purge_2026_07_25.md` todo 5 states "Done-when: zero unattributed (address-keyed)
   `dex_pool_state` leaves remain for these venues within the confirmed-recoverable range" — but purging the 541,890
   no-replacement leaves would be a permanent, uncompensated DATA LOSS for pools the catalogue never tracked, violating
   the exact delete-safety principle (`/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`) this whole plan is
   built on. I am completing todo 5 with the SAFETY-CORRECT interpretation instead (purge only the 190,955
   content-verified-superseded leaves), not the literal "zero remain" text — full rationale in that plan's Progress Log.
2. **The gap is structural, not specific to this plan.** ANY future catalogue-scoped backfill for these (or other) DEX
   protocols will hit the identical ceiling — ~3/4 of real historical trading activity for these 4 protocols alone is
   simply invisible to catalogue-filtered capture. This likely also affects Honest Coverage denominators
   (`/codex/02-data/honest-coverage-model.md`) for `dex_pool_state`, since the catalogue-derived `expected_unattempted`
   population undercounts the true historical pool universe by the same ~74%.
3. **Precedent for scale**: this is a MUCH larger version of the same "catalogue undercounts reality" pattern already
   flagged for cefi in `cefi_enumeration_audit_instrument_type_leakage_and_catalogue_orphans_2026_07_27.md` — worth
   cross-checking whether that finding's remediation approach generalizes here.

## Recommended decision

An operator/architecture judgment call, not a mechanical fix: should the instruments-service DeFi pool catalogue be
backfilled/expanded to include every historically-address-captured pool (a discovery pass over the existing
address-keyed leaf corpus per venue/chain), so future catalogue-scoped backfills and Honest Coverage denominators
reflect the true historical universe? Or is the catalogue's current "currently-active pool" scope intentional and the
74% gap acceptable (i.e., the old, now-unattributed data for delisted/inactive/never-catalogued pools is treated as
permanently out-of-scope going forward)?

## Todos

- [ ] [DATA] P2. Quantify the same catalogue-vs-historical-capture gap for the OTHER 12 default protocols the standing
      `mtds-dex-pools-backfill` VM covers (not just the 4 in this plan) — reuse the same per-shard-directory
      batch-verification technique (list symbol-named siblings, compare pool_address coverage) against each protocol's
      own catalogue population. Done-when: a per-protocol SAFE/FLAGGED breakdown table, matching this doc's numbers for
      curve/sushiswap/velodrome_v2/trader_joe_v2. (repo: market-tick-data-service)
- [ ] [OPERATOR] P2. Decide catalogue scope policy per the "Recommended decision" above — expand the catalogue via a
      historical-discovery backfill, or formally accept the ~74% gap as permanent/ out-of-scope. Done-when: a documented
      ruling in this issue doc, driving whichever follow-up plan the decision implies.
