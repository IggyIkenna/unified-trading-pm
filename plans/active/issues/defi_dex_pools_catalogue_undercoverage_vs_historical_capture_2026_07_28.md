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
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: research
drift_direction: worsening-slowly
source: [plans/active/defi_dex_pool_symbol_fix_backfill_purge_2026_07_25.md]
resolved_by:
locked_by:
depends_on: []
assigned_role: data_engineering
context_scope:
  [
    /plans/active/defi_dex_pool_symbol_fix_backfill_purge_2026_07_25.md,
    /codex/02-data/honest-coverage-model.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    market-tick-data-service/market_tick_data_service/cli/handlers/_catalogue_filter.py,
    market-tick-data-service/market_tick_data_service/cli/handlers/dex_pools_handler.py,
  ]
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

## Todos

- [ ] [DATA] P2. Quantify the same catalogue-vs-historical-capture gap for the OTHER 12 default protocols the standing
      `mtds-dex-pools-backfill` VM covers (not just the 4 in this plan) — reuse the same per-shard-directory
      batch-verification technique (list symbol-named siblings, compare pool_address coverage) against each protocol's
      own catalogue population. Done-when: a per-protocol SAFE/FLAGGED breakdown table, matching this doc's numbers for
      curve/sushiswap/velodrome_v2/trader_joe_v2. (repo: market-tick-data-service)
- [ ] [DATA] P2. **RETAGGED 2026-07-28 (was `[OPERATOR]`) — RULED, see "Recommended decision" above.** Expand the
      instruments-service DeFi pool catalogue via a full historical-discovery backfill covering every ever-captured pool
      for EVERY default DEX protocol (not just the 4 sampled) — full completion, no partial rollout, no MVP-only subset,
      cost pre-approved under the <$100 tier. Done-when: the catalogue's pool population per venue/chain matches (or a
      documented, address-level reconciliation explains any residual gap against) the true historical address-keyed
      capture corpus for every default protocol, and Honest Coverage's `expected_unattempted` denominator is re-derived
      from the expanded catalogue. (repo: instruments-service, market-tick-data-service)

## Progress Log

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
