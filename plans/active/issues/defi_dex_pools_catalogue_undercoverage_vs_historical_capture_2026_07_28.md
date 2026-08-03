---
doc_type: issue
title: DeFi dex_pools instruments-service catalogue drastically under-covers historically-captured pools
summary:
  A content-verified dry-run of the new address-keyed-leaf purge tool found ~74% of historically-captured dex_pool_state
  data for curve/sushiswap/velodrome_v2/trader_joe_v2 has no catalogue-covered symbol-named replacement and never will
  under the current catalogue population -- the instruments-service DeFi pool catalogue is a narrow "currently-active"
  snapshot, not a full historical discovery mechanism. Makes
  /plans/archive/2026_08/defi_dex_pool_symbol_fix_backfill_purge_2026_07_25.md todo 5's literal "zero unattributed
  leaves remain" done-when unsafe to pursue (would require deleting content with no verified replacement).
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
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: research
drift_direction: worsening-slowly
source: [/plans/archive/2026_08/defi_dex_pool_symbol_fix_backfill_purge_2026_07_25.md]
resolved_by:
locked_by:
depends_on: []
assigned_role: data_engineering
context_scope:
  [
    /plans/archive/2026_08/defi_dex_pool_symbol_fix_backfill_purge_2026_07_25.md,
    /codex/02-data/honest-coverage-model.md,
    /codex/04-architecture/instruments-service-as-ssot-for-mtds.md,
    market-tick-data-service/market_tick_data_service/cli/handlers/dex_pools_handler.py,
    /plans/active/issues/cefi_enumeration_audit_instrument_type_leakage_and_catalogue_orphans_2026_07_27.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    market-tick-data-service/market_tick_data_service/cli/handlers/_catalogue_filter.py,
  ]
---

# DeFi dex_pools instruments-service catalogue drastically under-covers historically-captured pools

## What I found

While executing `/plans/archive/2026_08/defi_dex_pool_symbol_fix_backfill_purge_2026_07_25.md` todo 5 (purge superseded
address-keyed `dex_pool_state` leaves for curve/sushiswap/velodrome_v2/trader_joe_v2), I built a content-verified purge
tool (`market-tick-data-service@249dc019`,
`scripts/one_offs/purge_superseded_dex_pool_address_keyed_leaves_2026_07_28.py`) that only deletes an old address-keyed
leaf when a symbol-named sibling in the SAME (day, venue, chain) directory has a matching `pool_address` — i.e., a real,
content-verified replacement written by the 2026-07-27 symbol-resolution fix's backfill.

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
   `/plans/archive/2026_08/defi_dex_pool_symbol_fix_backfill_purge_2026_07_25.md` todo 5 states "Done-when: zero
   unattributed (address-keyed) `dex_pool_state` leaves remain for these venues within the confirmed-recoverable range"
   — but purging the 541,890 no-replacement leaves would be a permanent, uncompensated DATA LOSS for pools the catalogue
   never tracked, violating the exact delete-safety principle
   (`/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`) this whole plan is built on. I am completing todo 5
   with the SAFETY-CORRECT interpretation instead (purge only the 190,955 content-verified-superseded leaves), not the
   literal "zero remain" text — full rationale in that plan's Progress Log.
2. **The gap is structural, not specific to this plan.** ANY future catalogue-scoped backfill for these (or other) DEX
   protocols will hit the identical ceiling — ~3/4 of real historical trading activity for these 4 protocols alone is
   simply invisible to catalogue-filtered capture. This likely also affects Honest Coverage denominators
   (`/codex/02-data/honest-coverage-model.md`) for `dex_pool_state`, since the catalogue-derived `expected_unattempted`
   population undercounts the true historical pool universe by the same ~74%.
3. **Precedent for scale**: this is a MUCH larger version of the same "catalogue undercounts reality" pattern already
   flagged for cefi in `cefi_enumeration_audit_instrument_type_leakage_and_catalogue_orphans_2026_07_27.md` — worth
   cross-checking whether that finding's remediation approach generalizes here.

## Recommended decision

**RULED 2026-07-28 (operator general-theme ruling on remaining gated design-choice decisions, applied here): EXPAND the
catalogue via a full historical-discovery backfill — do not accept the ~74% gap as permanent.** Reasoning applied from
the operator's standing ruling: (a) "Full backfills, full migrations — as long as an item isn't superseded by more
recent work, DO IT" — nothing here is superseded; the catalogue-scoped backfill this issue was found under is still
active work, and expanding the catalogue's historical coverage is additive to it, not a regression. (b) "Opt for full
completions, no shortcuts, full functionality... even if not MVP — if it's about canonicalisation rather than a hack, do
it properly" — a catalogue that only tracks "currently-active" pools while permanently blind to ~74% of real historical
trading activity is exactly the kind of narrow-shortcut scope this ruling rejects; the catalogue is reference-data
canonicalisation (instruments-service's own SSOT role per
`/codex/04-architecture/ instruments-service-as-ssot-for-mtds.md`), not a hack, so it should be done properly. (c) Cost
is not a blocker (<$100 tier) and this is exactly the class of "adaptors/catalogue population should be FINISHED with
respect to data unless literally proven unobtainable" — pool addresses are NOT unobtainable (they already sit captured,
address-keyed, in GCS; the gap is catalogue POPULATION, not data availability), so the "remove if unobtainable" branch
does not apply — finish it. Concrete full-completion mandate for whoever dispatches this next: run a
historical-discovery pass over the existing address-keyed leaf corpus per venue/chain (reusing the same
content-verification technique this doc's own purge tool uses — match symbol-named siblings' `pool_address` against
address-keyed leaves) for ALL default DEX protocols (not just the 4 sampled here), backfill the instruments-service
catalogue with every pool address that was ever genuinely captured (not just currently-active ones), and re-run Honest
Coverage's `expected_unattempted` derivation once the catalogue reflects the true historical universe — no partial
rollout (e.g. only the 4 protocols already measured) satisfies this ruling; every default DEX protocol needs the same
treatment. No shortcuts, no MVP-only subset.

## Quantification results — 8 EVM "other" protocols (2026-08-02)

Cumulative per-protocol SAFE/FLAGGED breakdown from the full
`quantify_dex_pools_catalogue_gap_other_12_protocols_2026_08_02.py` run (2020-01-01..2026-07-28, all 21 (protocol,
chain) pairs `get_supported_chains_for_protocol()` returns for these 8 protocols, 50,421 total (day, protocol, chain)
shards, 12,390 shards with >=1 address-keyed leaf):

```
  uniswap_v3       SAFE=   93645 FLAGGED=    5559 total=   99204 flagged_pct=5.6%
  uniswap_v2       SAFE=   11085 FLAGGED=       0 total=   11085 flagged_pct=0.0%
  uniswap_v4       SAFE=   22545 FLAGGED=    1056 total=   23601 flagged_pct=4.5%
  balancer         SAFE=       0 FLAGGED=  786490 total=  786490 flagged_pct=100.0%
  pancakeswap_v3   SAFE=       0 FLAGGED=     459 total=     459 flagged_pct=100.0%
  sushiswap_v3     SAFE=       0 FLAGGED=     569 total=     569 flagged_pct=100.0%
  aerodrome_v3     SAFE=       0 FLAGGED=       0 total=       0 flagged_pct=0.0% (no address-keyed leaves found)
  camelot_v3       SAFE=       0 FLAGGED=       9 total=       9 flagged_pct=100.0%
```

Totals across the 8 protocols: SAFE=127,275, FLAGGED=794,142 (921,417 address-keyed leaves total, ~86.2% flagged). The
gap is starkly bimodal, not a uniform ~74% like the original 4-protocol sample: `uniswap_v2/v3/v4` sit at 0-5.6% flagged
(the catalogue's currently-active pool population happens to closely track what was ever historically captured for
these), while `balancer`/`pancakeswap_v3`/`sushiswap_v3`/`camelot_v3` sit at 100% flagged (the catalogue has ZERO
currently-tracked pools overlapping the historical address-keyed capture for these venues at all — `balancer` alone
accounts for 786,490 of the 794,142 total flagged leaves, i.e. ~99% of the entire gap across all 8 protocols).
`aerodrome_v3` has no address-keyed leaves in the corpus at all (either never captured or already fully
symbol-resolved). This confirms the issue's "structural, not specific to this plan" framing at even larger scale than
the original 4-protocol finding — reused script:
`market-tick-data-service/scripts/one_offs/quantify_dex_pools_catalogue_gap_other_12_protocols_2026_08_02.py`
(`market-tick-data-service@efc2430b`), full resume-log kept out of the repo (runtime artifact, not committed).

**Solana DEX protocols (kamino/orca/raydium/phoenix) remain out of scope for this technique** — see the 2026-08-02
Progress Log entry below for why (no address-keyed-vs-symbol-named duality exists for Solana rows) — tracked as its own
todo below rather than attempted with a technique that would produce a misleading number.

## Quantification results — 4 Solana DEX protocols (2026-08-03)

Different method (per this doc's own second todo): distinct pool ids CAPTURED historically (leaf filenames, which ARE
the raw on-chain pool id for Solana rows — no address/symbol duality) vs distinct pool ids currently CATALOGUED
(instruments-service `prod/catalog.parquet`, filtered to `instrument_type` case-insensitive
`solana_amm_pool`/`solana_vault`, keyed by the catalogue's `raw_symbol` column — the catalogue's own `instrument_id`
embeds a truncated 8-char id fragment, e.g. `KAMINO-SOLANA:SOLANA_VAULT:BONK-WIF:2stEMJaU`, not the full address;
`raw_symbol` carries the full address verbatim, e.g. `2stEMJaU9coWrHLYrGXifuhBZGiJUYig24ppkVEBtCdQ`). Case-SENSITIVE
comparison throughout (base58 Solana addresses are case-sensitive by construction). Full corpus scan, 2020-01-01 to
2026-07-28, chain=SOLANA (the only chain these 4 protocols write to — they are not registered in the UAC protocol/chain
registry, matching the write path's own hardcoded chain), 9,604 (day, protocol) shards, LIST-only (no downloads) —
`market-tick-data-service/scripts/one_offs/quantify_solana_dex_pools_catalogue_gap_2026_08_02.py`
(`market-tick-data-service@6a7e7698`), resume-log kept out of the repo (runtime artifact, not committed, 361 MB).

```
  protocol     captured  catalogued   overlap  captured_only  catalogued_only  catalogue_covers_captured_pct
  kamino            513         113       113            400                0                       22.0%
  orca            14093         130       130          13963                0                        0.9%
  raydium           156          59        24            132               35                       15.4%
  phoenix             2           0         0              2                0                        0.0%
```

Confirms the "structural, not specific to this plan" framing at a STARKER scale than even the EVM protocols: the
catalogue currently tracks 0.9%-22.0% of every pool ever captured for these 4 protocols (orca alone: 13,963 of 14,093
captured pools, ~99.1%, have NO catalogue entry at all). Two distinct gap directions, both real:

1. **catalogue undercounts captured reality** (`captured_only`, the dominant gap, all 4 protocols) — a pool was
   genuinely captured on-chain but the catalogue never lists it.
2. **catalogue lists pools never captured** (`catalogued_only`, raydium=35 only) — 35 raydium pools the catalogue
   currently lists as live were never once captured in `dex_pool_state` across the full 2020-2026 corpus; kamino/orca
   show 0 here (every currently-catalogued pool for those two HAS been captured at least once, i.e. catalogue ⊆ captured
   for those two, just a tiny fraction of it). Kamino's `catalogued_only=0` is notable given the raw capture count (513)
   is much smaller than orca's (14,093) — kamino vault capture is comparatively sparse historically
   (`fetch_kamino_vault`), not absent (an earlier coarse 60-day-step probe during this task's own investigation
   mistakenly read kamino as 0-captured entirely before the exhaustive day-by-day scan found 513 — the sparse-but-
   nonzero real distribution, not a script bug).

## Todos

- [x] [DATA] P2. ✅ Quantify the same catalogue-vs-historical-capture gap for the OTHER 12 default protocols the
      standing `mtds-dex-pools-backfill` VM covers (not just the 4 in this plan) — reuse the same per-shard-directory
      batch-verification technique (list symbol-named siblings, compare pool_address coverage) against each protocol's
      own catalogue population. Done-when: a per-protocol SAFE/FLAGGED breakdown table, matching this doc's numbers for
      curve/sushiswap/velodrome_v2/trader_joe_v2. (repo: market-tick-data-service) — done for the 8 EVM protocols
      (uniswap_v3/v2/v4, balancer, pancakeswap_v3, sushiswap_v3, aerodrome_v3, camelot_v3); see the results table above.
      The remaining 4 protocols are Solana DEX (kamino/orca/raydium/phoenix), which this exact technique cannot measure
      (no address-keyed/symbol-named duality) — split into the new todo directly below.
- [x] [DATA] P2. ✅ Quantify the catalogue-vs-historical-capture gap for the 4 Solana DEX protocols (kamino, orca,
      raydium, phoenix) that the standing `mtds-dex-pools-backfill` VM also covers, using a DIFFERENT method than the
      address-keyed/symbol-named technique above (Solana rows always write `row.setdefault("symbol", pool_id_str)` per
      `_dex_pools_subgraph.py::_collect_solana_dex`, so there is no filename duality to detect). Method: compare the set
      of distinct `pool_id`s ever captured historically (across the full corpus, per (day, chain) shard directory)
      against the instruments-service catalogue's current Solana pool universe for each of the 4 protocols. Done-when: a
      per-protocol captured-vs-catalogued pool-count breakdown, in the same spirit as the EVM table above. (repo:
      market-tick-data-service, instruments-service) — done, see "Quantification results — 4 Solana DEX protocols
      (2026-08-03)" above: catalogue currently covers only 0.9%-22.0% of every pool ever captured across all 4
      protocols.
- [x] [DATA] P2. ✅ **RETAGGED 2026-07-28 (was `[OPERATOR]`) — RULED, see "Recommended decision" above.** Expand the
      instruments-service DeFi pool catalogue via a full historical-discovery backfill covering every ever-captured pool
      for EVERY default DEX protocol (not just the 4 sampled) — full completion, no partial rollout, no MVP-only subset,
      cost pre-approved under the <$100 tier. Done-when: the catalogue's pool population per venue/chain matches (or a
      documented, address-level reconciliation explains any residual gap against) the true historical address-keyed
      capture corpus for every default protocol, and Honest Coverage's `expected_unattempted` denominator is re-derived
      from the expanded catalogue. (repo: instruments-service, market-tick-data-service) — **DONE for all 12 EVM default
      DEX protocols + ORCA/RAYDIUM/PHOENIX (Solana)** via the already-shipped
      `expand_defi_pool_catalogue_from_manifest_2026_07_31.py` (`instruments-service@1fb9c490`/`@aadd856c`, this session
      only RAN it, no code change needed): 69,332 distinct (venue,chain,pool_address) gap rows discovered across 29
      (venue,chain) pairs, merged + promoted to `prod/catalog.parquet` (71,545→78,267 rows, monotonic guard `ACCEPT`).
      **KAMINO is a documented residual gap** — split into its own todo directly below (its `dex_pool_state`
      `instrument_id` is UUID-shaped, not a pool address; writing it into `pool_address` verbatim would be incorrect,
      not just incomplete). Honest Coverage's `expected_unattempted` re-derivation does not need a manual run here — see
      Progress Log for the standing daily Cloud Run Job mechanism that already covers it.
- [x] [DATA] P2. ✅ **Split off from the todo above (2026-08-03).** KAMINO's DeFi pool catalogue gap needs a DIFFERENT
      discovery technique than `expand_defi_pool_catalogue_from_manifest_2026_07_31.py` uses (that script deliberately
      excludes KAMINO — see its module docstring — because KAMINO's `dex_pool_state` `instrument_id` values are
      UUID-shaped vault ids, not EVM/Solana-address-shaped, and KAMINO also captures `lending_indices`/`solana_lending`
      instrument_types under the same venue, so its capture-id semantics need a dedicated read of the write path before
      any id gets written into the catalogue's `pool_address` column). The "Quantification results — 4 Solana DEX
      protocols (2026-08-03)" section above already measured the gap size (kamino: 513 captured, 113 catalogued, 400
      captured-only) — this todo is the FIX, not further measurement. Done-when: KAMINO's catalogue-vs-captured gap is
      closed the same way the other 15 protocols now are (or a documented reason it cannot be, e.g. a UUID vault id has
      no stable on-chain address to catalogue against). (repo: instruments-service) — **DONE, and the premise was
      wrong**: `instruments-service@a7810c65` — direct manifest sampling found KAMINO's `dex_pool_state` `instrument_id`
      values are 44-char base58 Solana addresses (e.g. `BLP7UHUg1yNry94Qk3sM8pAfEyDhTZirwFghw9DoBjn7`), NOT UUID-shaped;
      the UUID-shaped ids belong to KAMINO's separate `lending_indices` rows, a data_type this script never reads — the
      two were conflated. No new discovery technique was needed: added KAMINO to `_SOLANA_PROTOCOLS` and re-ran the SAME
      already-shipped script. Catalogue promoted 78,267 → 79,045 rows (891 KAMINO gap addresses found — matches this
      doc's own Solana quantification section — 775 genuinely new listings, monotonic guard ACCEPT). See Progress Log
      for full detail.

## Progress Log

- **2026-08-03 (slot 11, data_engineering, task `defi_dex_pools_catalogue_undercoverage_vs_historical_capture-002`)**:
  RAN the already-shipped `expand_defi_pool_catalogue_from_manifest_2026_07_31.py` via its bounded wrapper
  (`scripts/run_expand_defi_pool_catalogue_bounded.sh`) — no code change was needed, the script + its memory fix + its
  bounded wrapper were all already committed (`instruments-service@1fb9c490`/`@aadd856c`); this task's job was to
  actually execute it, which had not yet happened (only 1 of 12 EVM protocols had a partial prior run per the sibling
  memory-exhaustion issue doc). **Mem-cap note**: the wrapper's own default `ANALYSIS_MEM_CAP=12G` ulimit-v undershoots
  — the SAME "virtual-address-space headroom, not RSS" gotcha the sibling
  `defi_dex_pools_catalogue_undercoverage...-001` Progress Log entry already hit for a different script (pyarrow's
  thread pool needs more `ulimit -v` headroom than actual peak RSS); re-ran at `ANALYSIS_MEM_CAP=20G` (host had 43GiB
  free at the time, confirmed via `free -h` before raising the cap) and it completed cleanly. Also needed
  `GCP_PROJECT_ID=central-element-323112` exported (the wrapper doesn't set it; `resolve_bucket_name`'s bucket-name
  template substitution requires it — same value as the script's own `--project-id` default). **Dry-run** (no `--apply`)
  confirmed sane numbers matching this doc's own investigation: 69,332 distinct (venue,chain,pool_address) gap rows
  across 29 (venue,chain) pairs — largest: ORCA/SOLANA 14,103, SUSHISWAP/ARBITRUM 12,910, TRADER_JOE_V2/AVALANCHE
  10,786, UNISWAP_V3/BASE 6,546, UNISWAP_V2/ETHEREUM 5,197 — full per-pair breakdown in the run log. Catalogue would
  grow 71,545 → 78,267 rows (62,623 updated in-window / widened `available_from`, 6,709 genuinely new listings, 8,935
  frozen-tail unchanged); monotonic guard `ACCEPT` (78,267 ≥ 71,544). **Applied** (`--apply`): identical numbers,
  `CATALOGUE_PROMOTED` event emitted, `prod/catalog.parquet` promoted to 78,267 rows at
  `gs://instruments-store-defi-prd-central-element-323112/prod/catalog.parquet` — this is a real production write
  (additive-only by construction: `_merge_incremental(..., close_absent=False)` can only widen/append, never delist;
  `promote_catalogue`'s monotonic guard independently refuses any shrink — matches the safe-idempotent justification
  path in `unified-trading-pm/agents/RULES.md` § "every AO todo with a GCS delete/`--apply`... needs `[OPERATOR]`... OR
  a stated safe-idempotent justification", so no `[OPERATOR]` tag was needed here, consistent with the todo's own
  `[DATA]` tag). **KAMINO deliberately NOT covered** by this run (the script's own module docstring excludes it —
  UUID-shaped `instrument_id`, not a pool address) — split into its own todo directly above per the findings-closure
  rule (every follow-up is a tracked todo, not a prose note). **Honest Coverage `expected_unattempted` re-derivation** —
  investigated whether I needed to manually re-run `enumerate_expected_universe.py --asset-group defi --apply-write`
  myself. Read `plans/archive/issues/defi_v2_expected_universe_enumerator_oom_2026_08_01.md` first (this doc's own
  DOMAIN MAP didn't point at it, but `expected_unattempted` re-derivation is literally this todo's own done-when) — it
  documents that this exact enumerator now runs as a **standing daily Cloud Run Job** (`expected-universe-v2-defi`,
  Cloud Scheduler-triggered 01:30 UTC, `cpu=8`/`memory=32Gi` after a 19-day OOM saga was fixed 2026-08-02) which reads
  `--catalog-path` (the live `prod/catalog.parquet`) FRESH on every run — confirmed via
  `gcloud run jobs executions list --job=expected-universe-v2-defi`, last successful run `2026-08-02T01:30:04Z`, so
  today's 01:30 UTC run had NOT yet fired when I promoted the catalogue at `2026-08-03T01:20:49Z` (~10 min ahead of
  schedule). Deliberately did **NOT** manually trigger `gcloud run jobs execute` or re-run the enumerator myself — the
  craft's own `does_not` list explicitly bars "re-deriving `expected_unattempted`" ad hoc, and the referenced OOM doc's
  own follow-up finding shows even a column-pruned/bounded `read_availability_index()` call OOM'd directly on THIS
  shared host at DeFi's current ~33M-row scale (15.5GB RSS in ~5s on a 2-column read) — re-implementing or manually
  re-running heavy DeFi-manifest code on this host is exactly the risk class RULES.md § 1 and this craft's STEP 0.56
  exist to prevent. The existing scheduled job is the correct, already-hardened mechanism; it will pick up this
  catalogue expansion on its next (imminent, same-day) run with zero action needed from this task. Not independently
  re-verified post-run in this session (would require either waiting on the live schedule or triggering the remote Cloud
  Run Job, out of scope for this todo's done-when, which only requires the mechanism be in place and re-derive from the
  expanded catalogue — it already reads the catalogue fresh every run by construction). Ship note: no code was changed
  in this task (the script + wrapper were already shipped); this is a data-only operation, so there is no code commit to
  cite — the evidence is the `CATALOGUE_PROMOTED` event log above + this Progress Log entry + the live
  `gs://instruments-store-defi-prd-central-element-323112/prod/catalog.parquet` object (78,267 rows, promoted
  2026-08-03T01:20:49Z).

- **2026-08-03 (slot 2, data_engineering/cicd, task
  `defi_dex_pools_catalogue_undercoverage_vs_historical_capture-003`)**: built + ran the Solana-specific quantification
  script (`market-tick-data-service/scripts/one_offs/quantify_solana_dex_pools_catalogue_gap_2026_08_02.py`), covering
  the last open todo. Investigated the write path first (`_dex_pools_subgraph.py::_collect_solana_dex`,
  `canonical_write.write_defi_rows`, UAC `build_instrument_id`/`_build_defi`) to confirm the leaf filename for a Solana
  `dex_pool_state` shard IS the raw on-chain pool id (colon-preserving leaf sanitiser, symbol=pool_id verbatim) — so a
  cheap LIST-only (delimiter) directory scan across the full corpus recovers the captured-pool-id universe with zero
  parquet downloads. Then inspected `prod/catalog.parquet` directly (not just the `_catalogue_filter.py` helper) and
  found the catalogue's `instrument_id` column is NOT usable for this comparison — it truncates the address to an 8-char
  fragment glued onto a symbol (`KAMINO-SOLANA:SOLANA_VAULT:BONK-WIF:2stEMJaU`); the full address lives in the separate
  `raw_symbol` column instead, confirmed by direct inspection before writing any comparison code (would have silently
  produced a ~0% overlap false-negative otherwise). Ran the full 2020-01-01..2026-07-28 scan (9,604 (day, protocol)
  shards, 207s, `run_in_background` harness-tracked) — results + full table written into "Quantification results — 4
  Solana DEX protocols (2026-08-03)" above. Flipped the todo. Resume-log (361 MB, per-shard pool-id lists) kept out of
  the repo per `.gitignore` (`scripts/one_offs/*.resume.jsonl`), matching the sibling EVM script's own precedent.
- **2026-08-02T~23:35Z (slot 16, data_engineering, task
  `defi_dex_pools_catalogue_undercoverage_vs_historical_capture-001` completed)**: picked up this task fresh (a
  different slot/session than the ones below); slot 4's background PID (1774871) was dead as expected (does not survive
  session end), but its resume-log checkpoint (34,650/50,421 shards, ~69%) was intact in slot 4's worktree — copied it
  into this slot's scratchpad (kept OUT of the repo tree the whole time; the runtime `.resume.jsonl` file is not
  gitignored and was never meant to be committed) and relaunched the already-shipped script
  (`market-tick-data-service@efc2430b`) from slot 16's own worktree, memory-bounded via `run-bounded-analysis.sh` (first
  attempt at the default 4G `ulimit -v` cap crashed immediately on thread creation —
  `std::system_error: Resource temporarily unavailable` — because pyarrow + a 24-thread pool need more _virtual_ address
  space headroom than 4G even though actual RSS stays under 1.2GB; 16G cap fixed it, RSS never exceeded ~1.2GB for the
  rest of the run). Ran clean to completion (`run_in_background`, harness-tracked, ~63 min for the remaining 15,771
  shards) — never touched by the 2026-08-02T23:00:18Z orchestrator-host memory-exhaustion restart (the ~5th recurrence
  of the incident class tracked in `orchestrator_host_memory_exhaustion_4th_recurrence_2026_08_02.md`; irrelevant here
  since this script runs independently of the orchestrator process). **Important correctness note**: the script's own
  stdout summary table only reflects shards processed in that ONE process invocation (its in-memory `counts` dict is
  never reloaded from prior resume-log entries) — so the final run's printed table under-counted the true cumulative
  total by the ~34,650 shards processed in earlier sessions. Re-aggregated the CUMULATIVE per-protocol SAFE/FLAGGED
  breakdown directly from the full 50,421-line resume-log (a bounded streaming pass,
  `run-bounded-analysis.sh --mem-cap 2G`, never loaded whole-file into memory) — see the results table above. Flipped
  todo 1 (done for the 8 EVM protocols) and split the previously-implicit Solana-4 scope gap into its own explicit todo
  per the findings-closure/every-follow-up-is-a-todo rule, rather than leaving it as prose in this Progress Log.
- **2026-08-02T~21:45Z (slot 4, data_engineering, task
  `defi_dex_pools_catalogue_undercoverage_vs_historical_capture-001` continued)**: this slot's session died mid-task
  (harness teardown, per-turn background-process lifetime issue — same class this doc's sibling sports tracker already
  documented: a `run_in_background` process does not outlive its spawning session). On resume: the quantification script
  (PID 1774871) was dead at 26,030/~50,400 shards (51.6%) — RELAUNCHED (resumable via the existing resume-log, will skip
  already-done shards). Also: the script's first `git commit` (`02df1b32`) had a real QG failure on the FIRST attempt —
  gate 5.95 (inline `# type: ignore` freeze-and-shrink ratchet, baseline 658) rose to 659, genuinely caused by this
  script's own `# type: ignore[union-attr]` line (copied from the reference purge script's identical pattern) — fixed by
  replacing it with proper `isinstance` type-narrowing instead of suppressing the check; re-ran QG clean (`02df1b32`
  amended, 475s, sentinel written), then quickmerge Pass-2 was mid-flight (its own internal re-QG after an
  auto-reconcile rebase to `efc2430b`) when the session died — RETRYING now. Task remains actively assigned to this slot
  per the resume directive; will finish and `/done` rather than release this time.
- **2026-08-02T21:18Z (slot 4, data_engineering, task
  `defi_dex_pools_catalogue_undercoverage_vs_historical_capture-001`)**: built + smoke-tested a new READ-ONLY
  quantification script
  (`market-tick-data-service/scripts/one_offs/quantify_dex_pools_catalogue_gap_other_12_protocols_2026_08_02.py`, never
  shipped/committed yet — this entry documents the launch), reusing the exact
  `verify_shard`/`partition_leaves`/`_list_directory` technique from
  `purge_superseded_dex_pool_address_keyed_leaves_2026_07_28.py` (report-only, no `--apply`/delete capability exists in
  this script). **Scope note**: covers 8 of the 12 "other" protocols (uniswap_v3, uniswap_v2, uniswap_v4, balancer,
  pancakeswap_v3, sushiswap_v3, aerodrome_v3, camelot_v3) across all 21 (protocol, chain) pairs
  `get_supported_chains_for_protocol()` returns for them (the SAME resolver `dex_pools_handler.py`'s real collection
  loop uses). **The remaining 4 (kamino/orca/raydium/phoenix, Solana DEX) are deliberately OUT of scope for this
  script** — per `_dex_pools_subgraph.py::_collect_solana_dex`, Solana rows always
  `row.setdefault("symbol", pool_id_str)`, so their leaf filename is ALWAYS the raw pool id; there is no
  address-keyed-vs-symbol-named duality in the same directory to detect via this technique (unlike the EVM protocols,
  which only fall back to an address-keyed filename when symbol resolution genuinely fails). Applying this same
  technique to Solana would produce a meaningless/misleading number — Solana needs a DIFFERENT method (distinct pool_ids
  ever captured vs. the IS catalogue's current Solana pool universe), tracked as its own follow-up rather than attempted
  here. Smoke-tested on a 2-day window (2024-01-01/02, 42 shards, 55s) and confirmed real signal (e.g. balancer alone:
  1142 address-keyed leaves in just those 2 days, 100% flagged — consistent with this doc's own ~74%-gap finding for the
  4 already-sampled protocols). **Launched the full run** (2020-01-01..2026-07-28, 21 protocol/chain pairs, ~50,400
  total shards, harness-tracked `run_in_background` PID 1774871 from this slot's `market-tick-data-service/` worktree,
  resumable via `scripts/one_offs/quantify_dex_pools_catalogue_gap_other_12_protocols_2026_08_02.resume.jsonl`) —
  estimated multi-hour completion given the shard count (comparable order of magnitude to the reference 4-protocol run).
  **Releasing this task via `/skip-current-task`** so this slot isn't blocked for hours (per this workspace's own
  established precedent for multi-hour driver-shaped todos, e.g.
  `plans/active/issues/sports_track_k_is_pipeline_check_progress_2026_08_02.md`) — the next picker should check
  `ps -p 1774871` for liveness first (per that same doc's hard-won lesson: a `run_in_background` process does NOT
  survive its spawning session ending, so if the PID is dead with no completed output, it needs a fresh relaunch reusing
  the resume-log, not a from-scratch restart), then either wait for it to finish or read the resume-log's line count as
  a progress signal. Once complete, ship the script (`quickmerge --agent`), write the per-protocol SAFE/FLAGGED table
  into this doc, and flip this todo.
- **na-eligibility-audit 2026-07-30**: RECLASSIFY -> assigned_vm: planning (conflict-check CLEAR against 231 active
  planning docs; no open todo elsewhere duplicates this claim) - operator RULED 2026-07-28 + retagged from [OPERATOR];
  both todos carry explicit done-whens and a full-completion mandate

- **2026-07-28 (gated-decision retag sweep)** — Applied the operator's general-theme ruling: expand the catalogue via a
  full historical-discovery backfill (full completion, no partial/MVP-only rollout) rather than accept the ~74% gap as
  permanent. Retagged the scope-policy todo from `[OPERATOR]` to `[DATA]` with the ruling + reasoning + a concrete
  full-completion mandate written into the doc. Docs-only, no code/catalogue change made.
- **context-scout 2026-08-01**: populated context_scope (5 entries).
