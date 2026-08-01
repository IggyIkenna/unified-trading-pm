---
doc_type: plan
title: DeFi satellite AO batch 7 — na-eligibility-audit reclassification (scheduled na_eligibility_auditor)
summary: >-
  Seventh AO-dispatch batch for defi, produced by the scheduled `na_eligibility_auditor` role running the
  `/na-eligibility-audit defi` skill (2026-08-01). Phase 0 found 34 defi-owned `assigned_vm: NA` docs, 13 in-scope after
  the incremental-diff filter (21 already verdicted-and-unchanged since 2026-07-30/31). Phase 1 classified all 13 via a
  Workflow fan-out (13 agents, sonnet); 3 docs carried a total of 6 candidate RECLASSIFY items. Phase 2's conflict-check
  against every active `assigned_vm: planning` plan in `parent_epic: defi_master` cleared 4 of the 6: the other 2 were
  found already-claimed elsewhere (the `setup-data-pipeline-vm.sh` canonical-migration `cd` bug is in-progress in
  `defi_consolidated_native_ao_extract_2026_07_25.md`; the "LOCAL QG HARNESS collects the wrong test suite" finding was
  already assessed and declined as under-evidenced by `defi_satellite_ao_dispatch_batch6_2026_07_30.md`) — both left
  KEEP-NA on their source docs with a corrected citation, not extracted here. The 4 cleared items below are each
  extracted VERBATIM from a source doc that otherwise stays `assigned_vm: NA` (each doc's OTHER open items remain
  genuine judgment/operator-gated work not eligible for a whole-doc flip) — shape (a) fresh-carve-out per
  `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` § 1, mirroring the existing batch1-6
  precedent for exactly this MIXED-verdict-source-doc situation.
status: active
nature: process
asset_group: [defi]
stage: [data]
repos: [instruments-service, market-tick-data-service, execution-service, deployment-service, unified-trading-pm]
scope: [engineer]
tags: [defi, ao-dispatch, na-eligibility-audit, reclassification, batch-7, satellite-docs]
related:
  [
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /plans/active/issues/mtds_gas_fees_migration_script_unbounded_memory_2026_07_30.md,
    /plans/active/defi_consolidated_native_ao_extract_2026_07_25.md,
    /plans/active/defi_satellite_ao_dispatch_batch6_2026_07_30.md,
    /cursor-configs/skills/na-eligibility-audit/SKILL.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
created: "2026-08-01"
last_updated: "2026-08-01"
parent_epic: defi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.8
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  `/na-eligibility-audit defi` run 2026-08-01 (autonomous, scheduled na_eligibility_auditor, tranche=defi) — Phase 1
  classified 13 in-scope `assigned_vm: NA` docs via a Workflow fan-out; Phase 2 conflict-checked all 6 candidate
  RECLASSIFY items against every active `parent_epic: defi_master` `assigned_vm: planning` plan, clearing 4.
assigned_role: data_engineering
sequential: false
drift_direction: advance-code
---

# DeFi satellite AO batch 7 — 2026-08-01

**status: active — conflict-cleared, dispatching.** Drafted autonomously by the scheduled `na_eligibility_auditor`
running `/na-eligibility-audit defi`; every todo below cleared the shared conflict-check
(`ao-dispatch-batch-naming-and-conflict-check.md` § 3) against the live `defi_master` backlog before being drafted here.

## Todos

- [x] ✅ [BACKEND] P2. **Audit defi adapters for dead code, runtime-fallback masking, and duplicate implementations**
      (gate-audit §1, 2026-07-24) across instruments-service `.../adapters/defi/`, MTDS
      `market_interface/adapters/{defi,defi_live,onchain,onchain_perps}/`, and execution-service
      `adapters/defi_adapter.py`, per `/codex/06-coding-standards/adapter-dead-code-and-fallback-ban.md`. Repos:
      instruments-service, market-tick-data-service, execution-service. Done when: a written finding per module
      (kept/fixed/removed + reason) is recorded. Source: `defi_consolidated_closeout_2026_07_18.md:548`. — DONE
      2026-08-01 (slot-6): this exact audit already existed at
      `plans/active/issues/defi_adapter_dead_code_audit_2026_07_24.md` (per-module findings for all ~100 files across
      the 3 repos, 2026-07-24), the source closeout todo's checkbox just hadn't been flipped since several findings
      stayed FLAGGED/open rather than fully resolved. Diffed the 3 scoped dirs for drift since that audit (7 new
      instruments-service files, no MTDS/execution-service changes besides the audit's own prior fix) and added a § 7
      addendum re-verifying the new files (all KEPT, clean) + spot-checking no regression on the still-open findings —
      see that doc's § 7 for the incremental evidence. `unified-trading-pm@<see quickmerge sha below>`.

- [x] ✅ [CONFIG] P2. **DONE 2026-08-01 (slot-8).** Wired `curve_adapter.py`'s `_ensure_web3` to resolve the RPC URL
      per-chain via `AlchemyBaseClient(chain=self.chain, project_id=self.project_id).get_rpc_url()` (already imported
      for `_ensure_alchemy_client`) instead of hardcoding `https://eth-mainnet.g.alchemy.com` regardless of `self.chain`
      — that client resolves ETHEREUM/ARBITRUM/POLYGON/etc via UAC `CHAIN_CONFIGS` (`arb-mainnet`/`polygon-mainnet`
      templates confirmed present in `_defi_chain_data.py`), falling back to `CHAIN_TO_ALCHEMY_NETWORK`. Added 3
      regression tests to `test_defi_adapters_boost.py::TestCurveAdapter`
      (`test_ensure_web3_resolves_per_chain_rpc_url_for_arbitrum`, `..._for_polygon`,
      `test_ensure_web3_unsupported_chain_leaves_web3_none`) — the arb/polygon tests assert the resolved URL contains
      the per-chain Alchemy network name and NOT `eth-mainnet`, and would fail against the old hardcoded code (it never
      called `AlchemyBaseClient` at all). Full `quality-gates.sh` green (sentinel-verified on the shipped SHA); shipped
      `market-tick-data-service@1f58a127`. Source: `defi_consolidated_closeout_2026_07_18.md:554-561`.

- [x] ✅ [DATA] P2. **Re-verify the 21 glued-id `dex_pool_state` rows are now 0 — VERIFIED 2026-08-01 (slot-11): stale
      premise corrected, NOT achievable via the retry this todo named; re-routed to the already-tracked P0 purge.** The
      todo's own premise ("9 ORCA cells still need the migration retry") was already stale — that retry completed
      2026-07-24 with 0 residual errors (`issues/mtds_defi_migration_cell_stall_untimed_gcs_read_2026_07_22.md` tick-3
      addendum, confirmed by reading the archived doc). Ran a fresh
      `scripts/one_offs/verify_defi_glued_ids_2026_07_24.py` (memory-bounded, `ANALYSIS_MEM_CAP=16G` — `ulimit -v` needs
      headroom beyond RSS for pyarrow's scan allocator, a 6G cap OOM'd on the parse step): **19 glued rows found** (down
      from 21 on 2026-07-24 — 2 cleared on their own), 9 `ORCA/SOLANA dex_pool_state` + 10 `liquidations` (AAVE_V3 4,
      COMPOUND_V3 4, FLUID 1, SPARK 1, all `date=2026-07-22`, `_20260723_013349`-suffixed — the same cron batch
      `f2e3ad41` already root-caused). **New finding this pass**: dry-ran the single-day (2026-07-22) targeted rebuild
      the sibling issue doc's own open todo recommended for the 10 liquidations rows — it is a NO-OP. Direct GCS check
      confirms all 10 source markers are ALREADY retired to `_migrated_aave_v3_ARBITRUM_20260723_013349.parquet` etc.
      (no per-instrument twins — genuine 0-row empty markers, nothing to reshard), so `rebuild_defi_manifest.py`'s
      R3-defect-A `_`-prefix guard will never rediscover them; the manifest's append/upsert-only index (confirmed by
      reading `rebuild_defi_manifest.py`: `ManifestWriter.add()` per object found, never a delete) simply cannot retract
      a row whose source object is gone. **All 19 remaining rows are now confirmed the SAME phantom-row class as the
      closeout plan's `:401` P0 purge todo** — not fixable by any retry/rebuild, only by that purge. Corrected the two
      source docs' now-proven-wrong "just retry/rebuild" framing:
      `issues/defi_lst_oracle_timestamp_glued_instrument_id_2026_07_20.md` (its own open todo) and
      `defi_consolidated_closeout_2026_07_18.md:644` (updated count 21→19 + phantom-row diagnosis), so no future agent
      re-attempts the same no-op fix. **The literal "0 glued-ids" outcome is NOT reached — this genuinely requires the
      P0 phantom-row purge (`defi_consolidated_closeout_2026_07_18.md:401`, VM-scale, ~1.79M dup + ~219.5K phantom rows,
      sequenced/gated separately) — out of this task's scope to build.** The `delete_migrated_defi_markers --apply` gate
      below therefore STAYS BLOCKED (0 not confirmed) — do not run it until the P0 purge lands and a fresh verify
      reports 0. Repo: market-tick-data-service (read-only this pass; no code change — the writer-side fix was already
      correct, the remaining gap is a manifest-row retraction the writer can't produce). Source:
      `defi_consolidated_closeout_2026_07_18.md:644-653`.

- [ ] [DATA] P2. **Audit `market-tick-data-service/scripts/` (and sibling repos' `scripts/`) one-offs for any OTHER
      direct `ManifestWriter(...)` construction missing `per_vm_shards=True`** against a populous bucket
      (defi/cefi/sports) — the same failure mode has now recurred independently 3 times in ~36 hours across different
      call sites (`scripts/migrate_legacy_gas_fees_venue_2026_07_30.py@8016c7e4`,
      `market_tick_data_service/cli/handlers/_defi_manifest.py`'s `DefiManifestRecorder@77738598`, and the
      `expand_defi_pool_catalogue` script) — each found ad hoc, no one has yet run the systematic sweep this todo asks
      for. Repos: market-tick-data-service, instruments-service, market-data-processing-service. Done when: a written
      inventory of every direct `ManifestWriter(...)` construction site in the 3 repos' `scripts/` trees exists, each
      marked safe (already passes `per_vm_shards=True` or `MANIFEST_PER_VM_SHARDS=true`-guaranteed) or fixed. Source:
      `issues/mtds_gas_fees_migration_script_unbounded_memory_2026_07_30.md:159-161`.

## Deferred — conflict-found, NOT extracted (parked on the source doc, no operator ruling needed — unambiguous)

- **`defi_consolidated_closeout_2026_07_18.md:422`** ("fix the `canonical-migration` `VM_TASK` mtds-hardcoded `cd` bug")
  — already claimed and IN PROGRESS in `defi_consolidated_native_ao_extract_2026_07_25.md`'s Track-1 Progress Log
  (2026-07-26/27, slot-4): the fix is code-complete (`scripts/vm/setup-data-pipeline-vm.sh` + a new
  `TestCanonicalMigrationServiceKeyedWorkspaceDir` regression test) but blocked on shipping by a shared-host `pytest`
  I/O stall, not abandoned. Verbatim/near-verbatim duplicate claim on an active `assigned_vm: planning` doc in the same
  `parent_epic` — per the conflict-check protocol this stays with its current owner, not re-drafted here.
- **`defi_migration_audit_log_2026_07_24.md:567`** ("LOCAL QG HARNESS collects the WRONG test suite") — already
  evaluated by `defi_satellite_ao_dispatch_batch6_2026_07_30.md`'s own Operator-gated/Deferred section:
  "bounded-sounding but under-evidenced (zero coverage found anywhere) — needs a scoping read before it's draftable." An
  established prior assessment, not re-litigated here; stays KEEP-NA on the source doc pending that scoping read.

## Progress Log

- 2026-08-01 (slot-7, scheduled `na_eligibility_auditor`, tranche=defi): Drafted alongside its finalize twin, both
  `status: active` (dispatching immediately — na-eligibility-audit's autonomous mode applies auto-fixable classes
  without a pause, per the skill's calibration; every todo here cleared its own conflict-check, no genuine ambiguity to
  park). Source docs (`defi_consolidated_closeout_2026_07_18.md`,
  `issues/mtds_gas_fees_migration_script_unbounded_memory_2026_07_30.md`) stay `assigned_vm: NA` — only these 4 items
  were extracted; each source doc's own checkbox gets annotated to cite this batch in the same commit.
- 2026-08-01 (slot-6, todo 1): Dispatched task defi_satellite_ao_dispatch_batch7-001 found this exact audit already done
  at `issues/defi_adapter_dead_code_audit_2026_07_24.md` (the source closeout todo's checkbox was simply never flipped
  after that audit shipped, since several findings there stayed FLAGGED rather than fully resolved — that's why the
  na-eligibility-audit's diff-based scan re-surfaced it as apparently-open). Added a § 7 addendum to that doc
  incrementally re-verifying the 7 instruments-service adapter files added since 2026-07-24 (all clean/KEPT) and
  spot-checking no regression on the still-open findings. Flipped this todo + the parent closeout checkbox by citation —
  no new code fix needed (nothing new was found broken).
- 2026-08-01 (slot-8, todo 2): Fixed `curve_adapter.py::_ensure_web3`'s hardcoded ETH-mainnet Alchemy URL — replaced
  with `AlchemyBaseClient(chain=self.chain, ...).get_rpc_url()` (already imported in the file for
  `_ensure_alchemy_client`), which resolves per-chain via UAC `CHAIN_CONFIGS` (verified `arb-mainnet`/`polygon-mainnet`
  templates present in `_defi_chain_data.py`). Added 3 regression tests. Full QG green, shipped
  `market-tick-data-service@1f58a127`.
- 2026-08-01 (slot-11, todo 3): Re-verified the glued-id count (memory-bounded, `ANALYSIS_MEM_CAP=16G` — a 6G
  `ulimit -v` cap OOM'd pyarrow's parquet scan; the manifest is now 1.14GB, up from 982MB on 2026-07-24). Result: 19
  rows (down from 21), 9 ORCA + 10 liquidations. Dry-ran the single-day rebuild the sibling issue doc recommended for
  the 10 liquidations rows — confirmed via direct GCS listing it is a no-op (all 10 already retired to `_migrated_*`
  with no per-instrument twins), so both sub-populations are now the SAME phantom-row class as the 9 ORCA rows —
  `rebuild_defi_manifest.py`'s append/upsert-only `ManifestWriter.add()` (read the source; confirmed no delete path
  exists) cannot retract a row whose source object is gone. Corrected the two source docs' now-disproven "retry/rebuild
  fixes it" framing (`issues/defi_lst_oracle_timestamp_glued_instrument_id_2026_07_20.md`,
  `defi_consolidated_closeout_2026_07_18.md:644`) so a future agent doesn't re-attempt the same no-op. Literal "0" not
  reached — genuinely requires the closeout plan's `:401` P0 phantom-row purge (VM-scale, ~1.79M dup + ~219.5K phantom
  rows), out of this task's scope. `delete_migrated_defi_markers --apply` stays correctly gated/blocked.
