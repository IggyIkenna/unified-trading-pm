---
doc_type: plan
title: DeFi satellite AO batch 16 — per-todo RECLASSIFY-split extraction from na-eligibility-audit 2026-08-17
summary: >-
  Satellite-batch extraction from the 2026-08-17 /na-eligibility-audit defi run's per-todo RECLASSIFY split path,
  aggregating 9 conflict-cleared, bounded items from 3 source docs: defi_migration_audit_log_2026_07_24.md (4 items —
  a ruled Solana/multi-venue source-label fix, a gas net-cost wiring verify, and 2 low-priority P3 nice-to-haves),
  plan_reconciler_findings_defi_2026_08_17.md (3 items — corpus-hygiene/verification tasks the same-day plan_reconciler
  run itself filed as "Plans not reached" todos), and lst_rate_honest_coverage_2026_07_21.md (2 items — an operator-ruled
  catalogue/enumerator v2 regen and a DEX-fill shard-completion check). Every item conflict-checked against every active
  defi covering doc (consolidated closeout, satellite batch2/6/9/11/14/15, finalize pairs, track01/track5,
  defi_operator_ruling_ao_dispatch, strategy_service_centralization_fixes, defi_expected_unattempted_backlog_1m
  finalize) — zero prior claim found on any of the 9.
status: active
nature: process
asset_group: [defi]
stage: [data, meta]
repos:
  [
    unified-api-contracts,
    unified-trading-library,
    market-tick-data-service,
    strategy-service,
    execution-service,
    instruments-service,
    unified-trading-pm,
  ]
scope: [engineer]
tags: [defi, ao-dispatch, satellite-extraction, batch-16, na-eligibility-audit, reclassification]
related:
  [
    /plans/active/defi_migration_audit_log_2026_07_24.md,
    /plans/active/issues/plan_reconciler_findings_defi_2026_08_17.md,
    /plans/active/lst_rate_honest_coverage_2026_07_21.md,
    /plans/active/defi_satellite_ao_dispatch_batch16_2026_08_17_finalize.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
created: "2026-08-17"
last_updated: "2026-08-20"
parent_epic: defi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 2.0
estimate_calibrated_ai_days: 1.6
assigned_role: data_engineering
effort: high
thinking_tier: high
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /plans/active/defi_migration_audit_log_2026_07_24.md,
    /plans/active/issues/plan_reconciler_findings_defi_2026_08_17.md,
    /plans/active/lst_rate_honest_coverage_2026_07_21.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /plans/active/defi_satellite_ao_dispatch_batch16_2026_08_17_finalize.md,
    /plans/active/issues/defi_gas_net_cost_partial_wiring_gap_2026_08_17.md,
  ]
source: >-
  `/na-eligibility-audit defi` (2026-08-17). Every item below cleared the shared conflict-check
  (`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` §3) against every active defi covering
  doc. Per-item Source: citations below point at the exact originating doc + todo.
sequential: false
drift_direction: advance-code
---

# DeFi satellite AO batch 16 — 2026-08-17

## Todos

- [x] ✅ [UAC] [SCRIPT] P2. **Solana + multi-venue DeFi source-label fix — RULED 2026-07-28 (canonicalisation, not a
      hack).** — unified-trading-library@40f9c5678e, market-tick-data-service@2895991771 (unified-api-contracts
      needed NO change — see Progress Log below). `SOURCE_PRIORITY(defi, dex_pool_state|lending_indices)` resolves `onchain_subgraph` for ALL chains, but
      `solana_defi_handler` actually fetches ORCA/RAYDIUM/KAMINO pools + Kamino/Marginfi/Solend lending via Solana
      RPC/Helius/DeFiLlama (not The Graph) — a provenance-label mislabel (data is correct, `source` column is wrong).
      Separately, `SOURCE_PRIORITY(defi, perp_funding)=[hyperliquid]` (single) makes ASTER/DRIFT/PACIFICA perp venues
      also resolve to `batch_hyperliquid`/`source=hyperliquid`, wrong for non-Hyperliquid venues. Adopt the full ruled
      per-venue mapping: ORCA/RAYDIUM/PHOENIX/KAMINO/MARINADE/JITO→`solana_rpc`; DRIFT→`helius`; MARGINFI/SOLEND→
      `defillama`; ASTER→`aster`; PACIFICA→`pacifica`. Add the missing `BATCH_SOLANA_RPC`/`BATCH_HELIUS_RPC`/
      `BATCH_DEFILLAMA`/`BATCH_ASTER`/`BATCH_PACIFICA` (+ `LIVE_`/`REPLAY_` siblings) enum members to UAC
      `pipeline_mode.py`, wire `source_string_for` + `default_transport_for_source` for each, add the venue overrides to
      UTL `_VENUE_OVERRIDES`, drop the handler hardcodes so `derive_pipeline_mode_for_row` is the single SSOT, update the
      closed-set symmetry tests. No partial rollout — every venue in the mapping, not a sample. Repos:
      unified-trading-library, unified-api-contracts, market-tick-data-service. Source:
      `defi_migration_audit_log_2026_07_24.md` todos at (grep-current) lines ~320 and ~663 (the same ruling, the second
      extending the first to ASTER/DRIFT/PACIFICA). Done when: every venue in the mapping resolves its ruled source via
      `derive_pipeline_mode_for_row` with no handler hardcode remaining, closed-set symmetry tests green.
- [x] ✅ [STRATEGY] [EXECUTION] P2. **VERIFIED 2026-08-17 (slot-7, data_engineering) — genuinely mixed, not a clean
      "wired" or "absent" answer.** The `gas_fees`
      DATA layer (per-chain gas PRICE) exists and is captured, but a grep of strategy-service/execution-service/
      features-service/UTL as of 2026-07-24 found no `gas_price × gas_units` net-of-gas cost computation
      (`estimate_gas` × `gas_fees`) wired into DeFi arb/carry profitability. Grep-then-READ to confirm current state; if
      still missing, wire it. Repos: strategy-service, execution-service. Source: `defi_migration_audit_log_2026_07_24.md`
      todo at line ~552. Done when: a live DeFi arb/carry strategy's profitability calc is confirmed to net out real
      `gas_price × gas_units`, or the wiring is added and unit-tested. **Grep-then-read (Explore sub-agent, 29 tool
      calls) found real `gas_price × gas_units` netting IS wired and gates trades in `ARBITRAGE_MEV_LIQUIDATION_BUNDLE`
      (`liquidation_bundle.py`), execution-service's DeFi cost aggregator, and the realized-PnL pipeline — satisfying
      this todo's literal done-when. BUT four other live strategy engines (`LIQUIDATION_CAPTURE`, `CARRY_STAKED_BASIS`,
      `JIT_LIQUIDITY`, `BACKRUN`) either read a feature/config value nothing produces (silently 0 in real runs) or
      have a documented gas-gate that was never implemented — a genuine correctness gap, not just missing wiring.
      Full citations + severity + 5 concrete follow-up todos filed as
      `/plans/active/issues/defi_gas_net_cost_partial_wiring_gap_2026_08_17.md` rather than a rushed multi-engine fix
      under this todo's 1-hour data_engineering-scoped estimate (the fix is quant_dev/features craft work, not
      data_engineering).**
- [ ] [UAC] P3. **NICE-TO-HAVE — tighten the defi G1-ENUM matrix `POOL` row (currently union-coarse).**
      `valid_data_types_for_instrument_type("defi","POOL")` is today the UNION across all POOL-declaring protocols
      (`{dex_pool_state, dex_pool_swaps, gas_fees, lending_indices, liquidations, perp_funding}`), so a pure-DEX pool
      seeds `expected_unattempted` for data_types it never produces (a perp-DEX like the removed GMX legitimately needed
      them; a pure spot-DEX pool doesn't). Not an impossible-combo (no `odds`/`oracle_prices` leak into POOL, gate (a)
      still passes) — a per-protocol grain would tighten the denominator. Repo: unified-api-contracts
      (`registry/capability_declarations/_defi.py` `PROTOCOL_CAPABILITIES`). Source: `defi_migration_audit_log_2026_07_24.md`
      todo at line ~772. Done when: `valid_data_types_for_instrument_type("defi","POOL")` is derived per-protocol
      instead of unioned, verified against the live PROTOCOL_CAPABILITIES declarations with no regression in the
      existing G1-ENUM matrix tests.
- [ ] [SCRIPT] P3. **NICE-TO-HAVE — gate the defi migrator's `_list_objects` L1 find on a cheap existence probe.**
      `migrate_defi_full_v9_canonical.py:570`'s L1-layout find always issues a full-bucket `_safe_find` even though all
      6 dedicated source buckets are `day=`-partitioned (no top-level tree to find) — wastes wall-clock per bucket on
      every `--apply` run (non-blocking, previously triaged as a deferred speed optimisation, not a correctness issue).
      Gate the find on a cheap existence probe (or drop it), validated against the whole corpus on a VM first so a
      bucket with a genuine L1 tree is never silently skipped. Repo: market-tick-data-service. Source:
      `defi_migration_audit_log_2026_07_24.md` todo at line ~780. Done when: the L1 find no longer performs a
      whole-bucket scan on a `day=`-partitioned bucket, verified via a timed dry-run before/after.
- [ ] [DIAG] P3. **Verify (and correct if stale) `operator_action_items_consolidated_2026_08_08.md`'s `.tabs/2`
      stash-cleanup claim.** As of 2026-08-08 it claims a live unresolved 3-way git merge conflict in slot-2's working
      tree; 9+ days of subsequent Progress Log entries never re-verified it. Confirm slot-2 is dead first (per
      multi-agent-safety rules — never touch a live slot's tree), then check its current git state and update the
      claim in the source doc. Repo: unified-trading-pm. Source: `plan_reconciler_findings_defi_2026_08_17.md` "Plans
      not reached" item 1 (line ~163). Done when: `operator_action_items_consolidated_2026_08_08.md`'s `.tabs/2` claim
      reflects the actually-verified current state, cited with evidence.
- [ ] [DOC] P3. **Correct `defi_satellite_ao_dispatch_batch3_2026_07_26_finalize.md`'s stale `sequential: true`
      justification.** It says "todo 4/archival must run last," but todo 4 already ran and archived batch3 on
      2026-08-06 while todo 1 (source-doc reconciliation) is still open ~3 weeks later — the declared process order was
      violated in practice with no apparent ill effect. Low-risk cosmetic text fix. Repo: unified-trading-pm. Source:
      `plan_reconciler_findings_defi_2026_08_17.md` "Plans not reached" item 3 (line ~173). Done when: the doc's
      `sequential: true` justification text matches its own actual execution history.
- [ ] [DOC] P3. **Complete cross-link asymmetry among the 4 `dex_swaps` row-count-conflict docs.**
      `defi_dex_swaps_gap_rootcause_ao_dispatch_2026_08_16.md` and `defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md`
      carry no reciprocal cross-link note; the 2 that do have one disagree on membership (one lists only 2 of the other
      3 docs). Add/complete 4 cross-reference notes so a worker landing on any one of the 4 sees the others. Does NOT
      resolve the underlying ~3.26M-row count conflict itself (needs a fresh live manifest read — separate,
      data-engineering work). Repo: unified-trading-pm. Source: `plan_reconciler_findings_defi_2026_08_17.md` "Plans
      not reached" item 4 (line ~273). Done when: all 4 docs' `related:`/inline cross-links name all 3 siblings.
- [x] ✅ [IS] P1. **Execute the LST catalogue + expected-universe v2 regen (operator-ruled 2026-08-12, reconfirmed
      2026-08-15) — enumerator half only, catalogue half already ran.** Ran `enumerate_expected_universe.py --full-history
      --apply-write` (v2) against real prod infra — `instruments-service@fd0d12a9`-era catalogue already regenerated
      2026-08-15; the enumerator half was the remaining stale artifact. Full detail (candidate-volume OOM discovery,
      operator-directed code fix, scan-only calibration, the calibrated 350M-cap `--apply-write` launch) is tracked in
      `/plans/archive/issues/defi_expected_universe_full_history_candidate_volume_2026_08_17.md` — read that doc for the complete
      trail, not repeated here. **DONE 2026-08-17 — instruments-service, VM
      `expected-universe-v2-defi-20260817-092709`, `run_id=enum-universe-defi-20260817-093209`**: `EVENT
      ENUMERATOR_COMPLETED {candidates: 294144873, range_rows: 267499, eu_days: 288659526, written: 267499,
      full_history: true}`. Verified live (downloaded + read the actual parquet, not just the completion log):
      `_index/expected_universe_ranges.parquet`'s GCS `last_modified` moved from the stale `2026-07-03T23:31:06Z` to
      `2026-08-17T10:24:24.054Z` — past both 2026-08-12 and 2026-08-17.
      **Target-cell finding, with a terminology correction**: both named cells resolve honestly, but NOT to
      `expected_unattempted` — the literal `capture_status` is `empty_confirmed[<typed reason>]`
      (`(CHAINLINK, ETHEREUM, oracle_prices)` → `empty_confirmed / EXPECTED_INSTRUMENT_NOT_LISTED`, the honest
      pre-Chainlink-mainnet-launch dead window `2018-01-01→2019-12-31`, every later day already captured; `(AAVE,
      oracle_prices)` → `empty_confirmed / EXPECTED_INSTRUMENT_NOT_LISTED` (chain ETHEREUM) + `empty_confirmed /
      EXPECTED_PRE_GENESIS_CHAIN` (chain PLASMA) — the live catalog's actual venue for the AAVE reserve `spot_asset`
      rows is `AAVE_V3`, not bare `AAVE`; querying `AAVE_V3`/`ETHEREUM`/`spot_asset`/`oracle_prices` directly shows 36
      rows, all `empty_confirmed` per-reserve pre-listing windows, zero `expected_unattempted`). Per
      `/codex/02-data/availability-manifest-and-data-status.md`, `expected_unattempted` is a distinct
      downstream-service pre-flight status (`record_expected_unattempted`, IS-listed + post-genesis), not what this
      enumerator's own range artifact writes — this file's status column uses `empty_confirmed[reason]` for exactly
      this "not expected to ever be captured" case, so the plan's own "Done when" wording used the wrong status name.
      Cross-checked the enumerator CAN still produce `expected_unattempted` for defi oracle_prices generally (2 real
      rows exist for `EIGENLAYER-ETHEREUM` `GOVERNANCE_TOKEN`/`SPOT_PAIR` `EIGEN`) — not a broken enumerator. The
      substantive intent (both cells honestly resolve to not-capturable/already-captured rather than silently missing
      or wrongly counted) is fully satisfied — `lst_rate_honest_coverage_2026_07_21.md` Phase 5's real AAVE-oracle +
      Chainlink-LST backfill (completed 2026-07-22, before this regen ran) already closed the gap the original todo
      wording (written 2026-07-21/2026-08-12) assumed would still be open.
- [ ] [MTDS] P3. **Confirm shard `-3`'s dex_pool_swaps deep-backfill completion (last checked 2026-08-09).** Per the
      2026-08-09 status update, 2 of 3 shards (`-1`/`-2`) were confirmed complete; shard `-3` was relaunched
      (SPOT, `SHARD_INDEX=6`, `--start 2025-12-15 --end 2026-07-21`) and health-verified running at T+10min
      (95,236 swap rows in the first shard) — completion not independently re-verified since. Check
      `gcloud compute instances list` + the shard's manifest row count against its target window; if complete, close
      the citing todo in the source doc with evidence; if still running or failed, report state. Repo:
      market-tick-data-service. Source: `lst_rate_honest_coverage_2026_07_21.md` todo at line ~382. Done when: shard
      `-3`'s completion state (done / still running / failed) is confirmed live and cited back into the source doc.

## Progress Log

- **2026-08-17 (na-eligibility-audit, defi tranche)**: drafted via the per-todo RECLASSIFY-split path across 3 source
  docs. Every item conflict-checked (§3 protocol) against the full active-defi covering set — zero prior claims found.
  2 items from `defi_migration_audit_log_2026_07_24.md` (lines ~406 FOLD-3-orphan-data_types, ~412 collection-gaps
  retag) were assessed but NOT extracted — flagged in that doc's own marker as needing a doc-correction pass first
  (stale/inverted premise per the retired-dedicated-bucket-architecture finding), not a clean extraction as worded.
  Paired with `defi_satellite_ao_dispatch_batch16_2026_08_17_finalize.md` (`depends_on` + `gate_on_depends: true`,
  `status: active`) in the same turn.

### Todo 1 — code-complete, blocked on cross-repo QG red — 2026-08-17 (slot-6)

Root cause found: `market-tick-data-service/.../solana_defi_handler.py`'s `_SOLANA_PROTOCOL_SOURCE_OVERRIDES` had no
entry for 9 of 10 Solana protocols, so their manifest `source=` was stamped empty. Fixed per the ruled mapping
(ORCA/RAYDIUM/PHOENIX/KAMINO/MARINADE/JITO -> `solana_rpc`; MARGINFI/SOLEND -> `defillama`) — committed locally
(mtds@460db09f, tests updated + verified). The DeFi-perp-venue half of the ticket (ASTER/DRIFT/PACIFICA) is STALE
against the current registry — DRIFT purged 2026-07-16, PACIFICA/ASTER reclassified DeFi->CeFi 2026-07-06, no live
DeFi perp venue exists — nothing to fix there.

**Discovered the two repos are load-bearing together, not independent**: `write_defi_rows`'s actual GCS upload-path
pipeline_mode derivation goes through UTL `resolve_pipeline_mode(venue=...)`, which consults `_VENUE_OVERRIDES` —
NOT just the MTDS manifest-recorder fix alone. Verified directly: with only the MTDS fix present, the write path still
mis-resolves `batch_onchain_subgraph` for these venues; with the companion UTL `_VENUE_OVERRIDES` additions ALSO in
the working tree, both regression tests pass. So the real fix is the pair of changes together.

**Blocked from shipping**: `unified-trading-library` has a pre-existing, unrelated QG-red test
(`test_manifest_writer_v6.py::TestManifestWriterRecordEmptyV6::test_record_empty_with_v6_key` — see
`plans/archive/issues/utl_manifest_writer_v6_record_empty_options_chain_path_2026_08_17.md`), so the UTL half can't be
committed under the green-tree HARD RULE, and MTDS's own quickmerge pre-flight refuses to ship while a path dependency
carries uncommitted changes. A second, independent session (interactive slot-27, different feature) hit the exact same
UTL red and was told by the operator to park locally and wait for AO to clear it — same resolution applies here.
**State left**: MTDS fix committed locally (unpushed, `460db09f`); UTL fix present in the working tree, uncommitted.
Nothing lost. Releasing this todo `GATED` on `RB-36315e6e` (unified-trading-library qg_red) — resume once that clears:
commit + ship UTL first, then re-verify + ship MTDS.

### Todo 8 ([IS] P1 expected-universe regen) — done — 2026-08-17 (slot-19)

Picked up the `[IS] P1` regen todo. Found it already had a rich in-flight trail from slots 3/15/17/21 in
`/plans/archive/issues/defi_expected_universe_full_history_candidate_volume_2026_08_17.md` (OOM discovery, operator-directed
streaming fix, scan-only calibration measuring 294,144,873 true candidates). Live-reverified before acting (no other
slot had landed a write since, no VM currently running), launched the calibrated `--apply-write` run
(`--max-writes-per-run 350000000`, `MACHINE_TYPE=e2-highmem-16`) → VM `expected-universe-v2-defi-20260817-092709`,
watched to completion. **Completed cleanly**: `_index/expected_universe_ranges.parquet` timestamp moved to
2026-08-17T10:24:24Z. Verified the 2 target cells directly against the downloaded parquet — full finding in this
plan's own todo checkbox above and in the issue doc's final Progress Log entry: both cells are now fully **captured**
(Phase 5's real backfill already ran 2026-07-22), not `expected_unattempted` gaps — the todo's "confirm
expected_unattempted" wording predates that backfill completing. Flipped both this todo and the issue doc's
corresponding todo to done.

### Todo 1 — shipped, done — 2026-08-17 (fresh session, different worktree from slot-6)

slot-6's prior session (see the "Todo 1 — code-complete, blocked on cross-repo QG red" entry above) left this GATED on
`RB-36315e6e` (a pre-existing UTL QG-red test) in an unpushed local commit in a worktree not accessible to this
session. Re-derived the fix from scratch against current live code rather than trusting the described diff verbatim.

**Re-verified against live code**: `unified-trading-library`'s QG is GREEN today — `RB-36315e6e` is resolved (ran
`quality-gates.sh` fresh, full pass, no `test_manifest_writer_v6` failure). No corresponding UTL repo-blocker issue
doc was found under `plans/active/issues/utl_manifest_writer_v6*` — it appears to have cleared without leaving a
citable doc.

**unified-api-contracts needed NO change**: confirmed live that `BATCH_SOLANA_RPC`/`BATCH_HELIUS_RPC`/`BATCH_DEFILLAMA`
+ `LIVE_`/`REPLAY_SOLANA_RPC` + `LIVE_`/`REPLAY_HELIUS_RPC` enum members already exist in `pipeline_mode.py`, and
`SOURCE_MODE_CAPABILITY` already correctly declares `defillama` as BATCH-only (`solana_rpc`/`helius_rpc` as
BATCH+LIVE+REPLAY) — `source_string_for`/`default_transport_for_source` are generic (derived from the enum value
string, not per-source wired), so no UAC commit was needed or made this session (repo confirmed clean, HEAD unchanged
at `fb7ff3b0`). The ASTER/DRIFT/PACIFICA perp-venue half of the ticket is confirmed STALE, same finding as slot-6:
live-grepped `unified_api_contracts/registry/venue_adapter_keys.py` — DRIFT has zero live entries (purged 2026-07-16,
no reversal), and PACIFICA-SOLANA (re-authorized 2026-08-14, "jupiter and pacifica please") is explicitly classified
`asset_group=cefi` (`canonical/quarantine.py` line 212, `mvp_scope.py`, `pipeline_mode.py` comments — "Solana on-chain
CeFi perp CLOB") — no live DeFi perp venue exists in this mapping today. Left un-actioned as originally assessed.

**Root cause + fix (MTDS + UTL, load-bearing together, confirmed independently)**: `solana_defi_handler.py`'s
`_SOLANA_PROTOCOL_SOURCE_OVERRIDES` only had `kamino_oracle→kamino`; every other Solana protocol's manifest `source=`
stamped empty AND (separately) `write_defi_rows`'s actual GCS-path pipeline_mode derivation
(`_resolve_pipeline_mode`→UTL `derive_pipeline_mode_for_row`, since the handler passed no explicit `pipeline_mode=`)
fell through to `SOURCE_PRIORITY(defi, dex_pool_state)=onchain_subgraph` — a genuine mislabel, verified against the
manifest AND the write path both mis-resolving without the pair of fixes. Extended
`_SOLANA_PROTOCOL_SOURCE_OVERRIDES` to cover all 12 protocols (kamino/orca/raydium/phoenix/meteora/lifinity/marinade/jito
→ `solana_rpc`; kamino_lending/marginfi/solend → `defillama`, confirmed via each protocol's actual
`_collect_defillama_lending`/native-API call site, not assumed from the ruling text alone — kamino_lending in
particular is DeFiLlama-sourced, not `solana_rpc`, contradicting a naive reading of the ruled per-venue mapping).
Added matching UTL `_VENUE_OVERRIDES` entries (ORCA/RAYDIUM/PHOENIX/METEORA/LIFINITY→`BATCH_SOLANA_RPC`,
MARGINFI/SOLEND→`BATCH_DEFILLAMA`) plus `_VENUE_DT_OVERRIDES` for KAMINO's 3 distinct data_types (dex_pool_state/
lending_indices/oracle_prices — a venue-only override would have wrongly forced all 3 onto one source).

**Regression caught + fixed before shipping (not in slot-6's notes)**: a blanket MARINADE/JITO venue-level UTL
override broke `test_lst_rates_handler.py` — `lst_rates_handler.py` ALSO writes the SAME `(MARINADE/JITO, lst_rates)`
shard atom via a genuinely different collector (a 3-tier RPC/TheGraph archival path), so a venue-level override there
would have mislabeled that OTHER handler's rows. Resolved by deliberately NOT adding MARINADE/JITO to UTL's
`_VENUE_OVERRIDES` (documented the ambiguity in-line) and instead having `solana_defi_handler.py` pass
`pipeline_mode=` EXPLICITLY at its own `write_defi_rows` call site (new `_solana_write_pipeline_mode` helper),
matching the pattern already used by `orca_whirlpool_state_handler`/`raydium_classic_amm_handler`/
`phoenix_orderbook_handler` (explicit `pipeline_mode=PipelineMode.BATCH_ONCHAIN_RPC`). This is a stronger, handler-scoped
fix than a blanket UTL table entry would have been for this specific pair of venues.

Updated `test_solana_defi_handler.py`'s KAMINO dex_pool_state path assertion (`batch_onchain_subgraph`→`batch_solana_rpc`)
and added closed-set symmetry tests to `test_pipeline_mode_resolver.py` (`test_orca_venue_override`,
`test_raydium_derive_pipeline_mode_for_row_not_onchain_subgraph`, `test_phoenix_meteora_lifinity_venue_overrides`,
`test_marginfi_solend_venue_overrides_are_defillama`, `test_kamino_per_data_type_overrides_not_forced_onto_one_source`,
`test_marinade_jito_deliberately_not_venue_overrides`).

**Shipped** (2 UTL commits — first pass then a correction after the lst_rates_handler regression was caught, both
green-tree quickmerge): `unified-trading-library@86f3eed0a0` (initial fix), `unified-trading-library@40f9c5678e`
(scoped MARINADE/JITO out of the blanket table + explicit-pipeline_mode correction, tests updated to match) — cite
`40f9c5678e` as the current state. `market-tick-data-service@2895991771` (source overrides + explicit
`pipeline_mode=` write path + test updates; two intermediate line-cap/method-size QG failures on the same commit were
fixed in-place before the final green run, not shipped separately). `unified-api-contracts`: no commit, confirmed
clean at `fb7ff3b0` (no code change needed — see above). QG: UTL green, MTDS green, UAC untouched/already-green.
Todo 1 flipped to done above; superseding the earlier slot-6 GATED entry (that session's local unpushed commits were
never reachable from this worktree and are treated as abandoned).

### Gas net-cost consumer todo — verified (mixed result), 2026-08-17 (slot-7, data_engineering)

Grep-then-read (not grep-only) across strategy-service/execution-service/features-service via an Explore sub-agent.
Real `gas_price × gas_units` netting IS wired for `ARBITRAGE_MEV_LIQUIDATION_BUNDLE`, execution-service's DeFi cost
aggregator, and the realized-PnL pipeline. Four other live engines (`LIQUIDATION_CAPTURE`, `CARRY_STAKED_BASIS`,
`JIT_LIQUIDITY`, `BACKRUN`) either read a feature/config value nothing produces (silently defaults to 0 in real
paper/live runs) or have a documented gas-gate never implemented in code — a genuine strategy-correctness gap with
real-money implications, flagged per the cross-cutting big-finding triage rule rather than closed quietly. Filed
full citations + 5 concrete follow-up todos as `/plans/active/issues/defi_gas_net_cost_partial_wiring_gap_2026_08_17.md`
(assigned_vm: planning, quant_dev/features craft scope) rather than attempting a rushed multi-engine strategy-math
fix here (out of data_engineering craft scope, and bigger than this todo's 1-hour estimate). Flipped this todo's
checkbox — the verification itself is complete and its literal done-when is satisfied (at least one strategy
confirmed netting real gas cost); the newly-discovered partial-wiring gap is tracked forward, not left unactioned.

- **context-scout 2026-08-17**: refreshed context_scope (5 entries) -- swapped the AG-wide closeout hub, the
  canonical-naming SSOT, and the na-eligibility-audit skill doc (none needed to execute a specific remaining todo)
  for the 3 actual per-todo source docs every still-open item cites by name+line-number; kept the naming/
  conflict-check codex (cited in this doc's own `source:` field) and added the gated finalize sibling.
- **context-scout 2026-08-20**: populated/refreshed context_scope (6 entries)
