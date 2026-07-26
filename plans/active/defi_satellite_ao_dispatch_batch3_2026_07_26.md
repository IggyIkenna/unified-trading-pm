---
doc_type: plan
title: DeFi satellite AO batch 3 — residual-orphan triage after batch2
summary: >-
  Third AO-dispatch batch for defi, produced by the `/ag-closeout-audit` skill's Phase-1 (per-doc classify) + Phase-3
  (conflict-check + draft) triage over all 59 defi AG-primary docs, run AFTER batch2 landed (2026-07-26). With batch1,
  batch2, the consolidated closeout, the aggregated-sources index and the forked children (track01, track5,
  lending-writer-retire, dex-pool-symbol-fix+finalize, native-ao-extract+finalize) all counted as covering, only 17 docs
  came back orphaned (15 partial-coverage, 2 never-touched); 39 are archivable-after-planned-work (already covered), 2
  archivable-now (archive candidates), 1 a cross-cutting/infra mistag (excluded). Phase-3's conflict-check took the 8
  AO-eligible orphan docs and cleared 13 candidate todos → merged 2 read-only report todos on the same source doc into 1
  (avoids a same-file Progress-Log race) → **12 todos ship here**. It left 8 items conflict/operator-gated (notably 5
  `defi_migration_audit_log` items whose "fold into dedicated buckets" premise is STALE — the dedicated→shared
  consolidation already shipped, so drafting them would regress the architecture), 4 skip_covered (already covered, not
  re-drafted), and 9 non-batchable orphans in the Deferred sections for the next iteration or an operator ruling.
  **status: draft — NOT dispatched. Flipping to active is an operator decision (per CLAUDE.md "Plan destination" HARD
  RULE); this batch was drafted autonomously by the scheduled ag_closeout_auditor and awaits operator approval.**
status: active
nature: process
asset_group: [defi]
stage: [data]
repos:
  [
    unified-trading-pm,
    market-tick-data-service,
    market-data-processing-service,
    features-service,
    strategy-service,
    unified-api-contracts,
    agent-orchestrator,
    execution-service,
    unified-trading-library,
  ]
scope: [engineer]
tags: [defi, ao-dispatch, close-out, batch-3, satellite-docs, fresh-triage]
related:
  [
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /plans/active/defi_consolidated_closeout_aggregated_sources_2026_07_24.md,
    /plans/active/defi_satellite_ao_dispatch_batch2_2026_07_26.md,
    /plans/active/defi_satellite_ao_dispatch_batch2_2026_07_26_finalize.md,
    /plans/active/defi_satellite_ao_dispatch_batch1_2026_07_25.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-07-26"
last_updated: "2026-07-26"
parent_epic: defi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 2.4
estimate_calibrated_ai_days: 1.9
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  /ag-closeout-audit skill run 2026-07-26 (autonomous, scheduled ag_closeout_auditor, tranche=defi) — Phase 1 classified
  all 59 defi AG-primary docs via a Workflow fan-out (59 agents, sonnet), Phase 3 ran a conflict-check + candidate-todo
  draft over the 8 AO-eligible orphan docs via a second Workflow fan-out (8 agents, opus), per the skill's documented
  methodology. batch2 (also 2026-07-26) is counted as covering here — this batch is the residual after batch2.
assigned_role: data_engineering
sequential: false
drift_direction: advance-code
---

# DeFi satellite AO batch 3 — residual-orphan triage after batch2

> **🟡 status: draft — NOT INGESTED / NOT DISPATCHED.** A draft plan is inert (`plans/PLAN_FORMAT.md`); the dispatcher
> ignores it until an operator flips `status: draft` → `active`. This batch was drafted autonomously by the scheduled
> `ag_closeout_auditor` (tranche=defi, 2026-07-26). Flipping it to active is an operator decision per CLAUDE.md's "Plan
> destination — ASK BEFORE CREATING" HARD RULE. Do a fresh re-read of each todo before activating (some source docs move
> fast).
>
> **Cross-plan sequencing note (todo 5):** the LIQUIDATION_CAPTURE tick-builder edits `paper_universe.py`, which
> `defi_satellite_ao_dispatch_batch2_2026_07_26.md`'s MEV-DOCS todo (batch2 line ~197) also edits. The edits are
> non-contradictory, but todo 5 should be **sequenced after** that batch2 todo lands to avoid a same-file race. If
> batch2 is still in flight when this batch activates, hold todo 5 until batch2's paper_universe.py change is in.

## Context (read before dispatching any todo)

Every todo below is a conflict-checked extraction from ONE orphaned defi source doc (each ends with `Source:`). The
conflict-check (Phase 3, one opus agent per orphan doc) grepped the whole covering set for each item's target
file/mechanism before drafting — items that a covering plan already claims were skipped (see "Already covered" note),
and items needing an operator/design ruling were parked (see Deferred). Same-priority todos run CONCURRENTLY across
workers by default; the 12 below were checked for cross-todo file collisions (the two read-only report checks on
`defi_manifest_no_expected_unattempted_seeder_2026_07_26.md` were merged into todo 9 to avoid a same-file Progress-Log
race). Two todos touch code beyond defi and are flagged inline: todo 2 (cefi/tradfi/sports strategy catalogs) and todo
10 (agent-orchestrator).

## Todos

- [ ] [DATA] P1. D1 DeFi features backfill — run the features-service compute over the captured DeFi raw window
      (features read canonical raw; C0 done) to populate `features-onchain-defi` (currently ~3 rows) and
      `features-delta-one-defi` (currently no index), materialising `staking_apy_bps`/`funding_rate_apy_bps` (onchain)
      and `basis_bps`/`realized_vol_*` (delta_one, via the `funding_oi` and `returns` feature-groups respectively) for
      the in-scope DeFi instruments. **`features-volatility-defi` DROPPED from this todo's scope 2026-07-26** (slot-8
      finding, main-ruling-confirmed): the volatility feature family's `--asset-group DEFI` choice was REMOVED
      2026-07-17 (operator ruling — no DeFi options products exist, so implied-vol/skew/term-structure surfaces cannot
      be computed for DeFi; `features_service/volatility/cli/parser.py` now hard-rejects it, the corresponding bucket
      was deleted, and a unit test (`test_asset_group_choices`) enforces `ASSET_GROUP_CHOICES == ["CEFI", "TRADFI"]`).
      The original done-when's "features-volatility-defi... present and populated" leg predates that ruling and is
      structurally unsatisfiable by design — NOT a gap to chase. Safe-idempotent justification: idempotent feature
      compute, no GCS delete. Repo: features-service. Done when: `features-onchain-defi` row count ≫ 3 AND
      `features-delta-one-defi` has a populated index, both over the full captured window (2 legs, not 3). Source:
      `data_completion_defi_2026_07_15.md`

      **IN-PROGRESS 2026-07-26 (slot-8) — real bug found + fixed; 2 SPOT VMs currently RUNNING, both
              idempotent/safe to re-run if interrupted:**

              **Bug found + FIXED**: onchain's `DependencyChecker` (`features_service/onchain/app/core/dependency_checker.py`,
              `UPSTREAM_DEPS`/`UPSTREAM_DEPS_DEFI`) had every `bucket_template` missing the `-prd-` env-tier segment
              (`"market-data-tick-{asset_group_lower}-{project_id}"` instead of the canonical
              `"market-data-tick-{asset_group_lower}-prd-{project_id}"` — see
              `unified_trading_library/config_interface/paths/registry.py`'s own `-prd-`-bearing template). This made the
              checker always resolve a bucket that doesn't exist, so it unconditionally reported all 5 DeFi MTDS on-chain
              deps (vault_share_price/lst_rates/lending_indices/oracle_prices/perp_funding) as missing regardless of the
              real capture date — explains why BOTH a 2026-04-15 window AND a 2026-07-01 window failed identically with the
              same `DependencyError`. Fixed + regression-tested (`tests/onchain/unit/test_dependency_checker_bucket_templates.py`)
              + shipped: `features-service@5fb00174`.

              Two separate VMs currently RUNNING (post-fix):
              (a) `features-onchain-defi-20260726-195642` — window 2026-07-01..2026-07-25, launched with the fixed code
              (tarball republished first — an earlier launch attempt at 19:54 fetched stale pre-fix code and was deleted
              before it could waste a run).
              (b) `features-delta-one-defi-20260726-195741` — window 2026-07-01..2026-07-25 (narrowed from the original
              2026-04-15..2026-07-25). The FIRST delta_one attempt (`features-delta-one-defi-20260726-190820`, full
              2026-04-15..2026-07-25 window, `--feature-group ALL`) was OOM-killed (exit 137) shortly after logging
              "Processing 18 feature groups" — likely loading the full ~3.5-month window into memory at once across all
              DeFi instruments/18 feature groups on an e2-standard-8 (`MACHINE_TYPE` is hardcoded in
              `deployment-service/scripts/vm/launch-features-vm.sh:221`, no env override exists). Narrowing the window is
              the safer fix vs hand-patching the launcher's machine type (broader blast radius, affects every feature
              family). **If this narrower run also OOMs**: the real fix is chunking delta_one's DeFi backfill into
              several smaller-window VM runs (e.g. monthly) rather than one `--feature-group ALL` pass — try that before
              touching `MACHINE_TYPE`.

              **If both VMs are no longer RUNNING when you resume this todo**: check
              `gs://deployment-scripts-central-element-323112/vm-logs/<vm-name>/EXIT_STATUS` + `run.log` (both self-delete
              on completion per `VM_SHUTDOWN_ON_COMPLETION=true`) — if EXIT_STATUS=0 for both, run the post-backfill
              manifest rebuild the launcher printed
              (`rebuild_manifest_from_canonical_paths(resolve_bucket_name(cloud='gcp', kind='features', asset_group='defi'),
              service_name='features-service')`), verify row counts (slim manifest read, `columns=` restricted — do NOT do
              a full-column read, it triggers per-VM-shard fallback and can use 10+GB RAM on this shared host). **Note**:
              even on full success, both VMs only cover 2026-07-01..2026-07-25 — the done-when says "full captured
              window," so additional chunked runs covering back to the actual per-data-type start dates (lst_rates
              ~2026-06-14 per `data_completion_defi_2026_07_15.md`; verify others) are still needed before flipping this
              checkbox. If a VM shows non-zero EXIT_STATUS, read its `run.log` tail for the actual failure before
              relaunching — do not blindly retry the same window twice (2 prior attempts already did that and both failed
              on the now-fixed bucket-naming bug, not the date).

- [ ] [STRATEGY] P1. **[CROSS-AG: touches cefi/tradfi/sports strategy code]** Sweep `archetype_slots_cefi.py`
      (CEFI_SLOTS), `archetype_slots_tradfi.py` (TRADFI_SLOTS), and `archetype_slots_sports.py` (SPORTS_SLOTS) — the v5
      slot-table construction surfaces parallel to the already-swept `archetype_slots_defi.py` DEFI_SLOTS (where 7/28
      rows were broken) — for catalog-emitted-config-key vs engine-param-read drift, using this doc's proven technique:
      construct the real registered engine (`get_archetype_engine_class` / factory.py ARCHETYPE_ENGINE_REGISTRY) from
      each slot's `initial_config`, call `on_tick` with realistic per-row features, and confirm a non-`[]` instruction.
      Fix unambiguous mechanical key rename/add drift in place (ADD the engine's real keys alongside — do not drop keys
      a real second consumer reads); for design-gated archetypes (RULES_DIRECTIONAL_CONTINUOUS /
      RULES_DIRECTIONAL_EVENT_SETTLED / ML_DIRECTIONAL_EVENT_SETTLED / MARKET_MAKING_EVENT_SETTLED / VOL_TRADING_OPTIONS
      — already xfail'd) leave them `xfail(strict=True)` with a one-line reason, do NOT force-fix. Extend
      `tests/unit/engine/strategies/v2/test_all_catalogued_archetypes_construct_and_fire.py` to parametrize
      CEFI_SLOTS/TRADFI_SLOTS/SPORTS_SLOTS (mirroring its DEFI_SLOTS coverage). Repo: strategy-service. Done when: every
      CEFI/TRADFI/SPORTS slot row either fires a real non-empty instruction or is explicitly
      xfail(strict=True)/allow-listed with a reason, the extended guardrail is green under
      `bash scripts/quality-gates.sh --no-fix` (0 unexpected failures, 0 XPASS), mechanical fixes shipped via quickmerge
      scoped to touched files. Source: `defi_catalog_engine_config_key_contract_drift_2026_07_23.md`

- [ ] [DATA] P1. D2 MDPS `swaps_ohlcv` reprocess of the stale chain-column `attempted_failed`/`SCHEMA_VALIDATION_FAILED`
      rows on the consolidated `market-data-tick-defi` `_index` (processed_candles layer) — ONE reprocess pass (NOT a
      one-venue VM racing the migration) covering UNISWAP_V3-ETHEREUM (28,634) + companions
      UNISWAP_V2-ETHEREUM/AAVEV3-OPTIMISM/EIGENLAYER/CURVE-ETHEREUM/MAKER/FRAX/DRIFT-SOLANA/KAMINO/JITO/MARGINFI. No
      code change (fix live mdps@7f1a5b5+3799c8d); rerun now that C0 canonicalises the source. Safe-idempotent
      justification: idempotent candle reprocess, no GCS delete. Repo: market-data-processing-service. Done when:
      post-reprocess `attempted_failed` for all listed venues → 0 (rows now `captured` or legit `empty_confirmed`),
      verified against the live `_index`. Source: `data_completion_defi_2026_07_15.md`

- [ ] [STRATEGY] P2. Build the interest-PnL A2 staking leg in strategy-service: wire the `carry_staked_basis`
      `STAKING_REWARD`/`CARRY` accrual leg to the `lst_yields` `exchange_rate`/`prev_rate` index ratio keyed off
      `cfg['lst_asset']`, mirroring the already-shipped E1 FUNDING-leg pattern (additive new param defaulting to None so
      all other callers stay byte-for-byte; quote-only existing path, no schema change). Explicit-zero the Aave-lending
      mismodel, keep honest-absence visible, add a real passive-parity test, run the 3-lens money-path review and
      hold-not-force-ship if anything is uncertain. Repo: strategy-service. Done when: the STAKING leg computes accrual
      from real `lst_yields` exchange-rate rows, the passive-parity test passes, all pre-existing callers are preserved
      byte-for-byte, `bash scripts/quality-gates.sh` is green, and the change ships to LDR via scoped
      `quickmerge.sh --agent --files` (prod-NAV recompute stays operator-gated, out of scope). Source:
      `lst_rate_honest_coverage_2026_07_21.md`

- [ ] [BACKEND] P2. Phase 5 — wire the LIQUIDATION_CAPTURE archetype's paper-replay tick builder in strategy-service,
      mirroring the already-shipped Phase 3/4a/4b pattern. FIRST run the mechanical catalog-key-vs-engine pre-check
      (catalog `initial_config` keys emitted for LIQUIDATION_CAPTURE vs
      `LiquidationCaptureEngine.on_tick`/`REQUIRED_PARAMS`, per
      `defi_catalog_engine_config_key_contract_drift_2026_07_23.md`) and confirm the engine `on_tick` actually emits
      instructions (not a stub). IF buildable: add `_load_liquidation_capture_ticks()` in
      `strategy_service/cli/handlers/paper_run_handler.py` reading real per-day on-chain
      `liquidation_events`/`health_factor` feature data (`health_factor_trigger` threshold sourced from catalog config,
      not invented), add LIQUIDATION_CAPTURE to `_ENGINE_DRIVABLE_ARCHETYPES` behind a new satisfiability gate in
      `paper_universe.py` with a typed honest-skip reason on data absence, add unit tests (satisfiability gate,
      honest-absence, determinism). Repo: strategy-service. Done when: EITHER LIQUIDATION_CAPTURE is in
      `_ENGINE_DRIVABLE_ARCHETYPES`, its tick loader reads real liquidation_events/health_factor GCS features with
      per-row honest-skip, and `quality-gates.sh --no-fix` is green with new tests; OR, if the pre-check finds the
      engine is a stub/no-op or requires an undecided health-factor-trigger design decision, the todo lands a documented
      held-finding in the issue doc naming the exact blocker with zero fabricated wiring. **Sequence after batch2's
      paper_universe.py MEV-DOCS todo (same file).** Source:
      `defi_archetype_universe_no_curtailment_mechanism_2026_07_23.md`

- [ ] [DATA] P2. C6 Pyth `oracle_prices` historical backfill — launch a SPOT backfill VM running MTDS Pyth Hermes-API
      collection for the 2026-04-15→present gap window, writing ONLY into the canonical
      env-split/`pipeline_mode=`/`asset_group=defi` layout (never the legacy layout; C0 canonical structure is live).
      Safe-idempotent justification: SPOT + idempotent re-fetch, no GCS delete. Repo: market-tick-data-service. Done
      when: the consolidated `market-data-tick-defi` `_index` shows Pyth `oracle_prices` rows `captured` (or legit
      `empty_confirmed`) across the full 2026-04-15→present window with zero remaining gap days. Source:
      `data_completion_defi_2026_07_15.md`

- [ ] [VERIFY] P2. Grep-then-READ whether DeFi arb/carry net-of-gas cost (gas_price × gas_units — execution
      `estimate_gas` gas_units × the captured per-chain `gas_fees` price) is actually wired in any consumer: search
      strategy-service, execution-service, features-service and unified-trading-library for a gas_price × gas_units
      net-cost computation and READ each candidate consumer to confirm (0-hit ≠ absent). Repo: strategy-service
      (cross-repo audit — do NOT build the consumer inline). Done when: a written verdict with file:line evidence states
      definitively whether net-of-gas is wired; if absent, a `plans/active/issues/` findings-triage doc is filed for the
      strategy/PnL axis naming the missing gas_price × gas_units computation. Source:
      `defi_migration_audit_log_2026_07_24.md`

- [ ] [SCRIPT] P3. Regenerate the stale `adapter_contract_baseline.yaml` entries for the 2026-07-26 MTDS DeFi
      code-motion splits, two independently-verified sub-parts committed together: (a) `dex_pools_handler.py` (9→5) +
      new `_dex_pools_subgraph.py` (2→6) from the perf-bundle facade extraction — already grep-confirmed pure
      code-motion, zero calls lost (5+6=11=pre-split total), safe to regen; (b) `_defi_manifest.py` (43→42) + new
      `_defi_catalog_freshness.py` (6 calls, no prior baseline entry) from the merged sibling-slot
      `assert_defi_catalog_fresh` extraction (commit `08439787`) — FIRST verify via `git show 08439787` that the 6 calls
      moved out of `_defi_manifest.py` rather than being silently lost/duplicated (reconcile the −1 net drop against the
      6 in the new file before blessing); if any sub-part shows real lost calls, do NOT regen it — file a P1/P2
      regression issue and leave that WARN in place. Then run `check_adapter_contract_regression --regenerate-baseline`
      (quality-gates.sh 5.70/6 flow) scoped to `market-tick-data-service`, keeping the regen limited to these four
      confirmed-safe defi files (do NOT blanket-bless unrelated cefi/tradfi/solana_defi_drift entries in the shared YAML
      — coordinate/sequence with `defi_satellite_ao_dispatch_batch2_2026_07_26.md` line ~495's sibling solana_defi_drift
      regen since both rewrite the same file). Repo: unified-trading-pm (baseline YAML edit + commit) +
      market-tick-data-service (verification reads). Done when: `bash scripts/quality-gates.sh --no-fix` on
      `market-tick-data-service` no longer prints the ⚠️ "Adapter contract-call regression" for `dex_pools_handler.py`
      or `_defi_manifest.py`, the YAML diff is committed, and this issue doc's `status:` is flipped to `resolved` (or a
      regression issue filed for any unconfirmed sub-part). Source:
      `mtds_dex_pools_adapter_contract_baseline_stale_2026_07_26.md`

- [ ] [DATA] P3. Two read-only reconciliation checks for `defi_manifest_no_expected_unattempted_seeder_2026_07_26.md`,
      combined into ONE todo (both append findings to that doc's Progress Log — must not race): (a) reconcile the three
      independent `_DEFAULT_PROTOCOLS` lists in market-tick-data-service (`lending_indices_handler.py:176`,
      `risk_params_handler.py:107`, `liquidations_handler.py:149`) against each other and against `SUBGRAPH_IDS`
      (`unified-api-contracts/unified_api_contracts/registry/capability_declarations/_defi.py:62-217`) — produce a
      written mismatch report (which protocol appears in which list vs SUBGRAPH_IDS); (b) confirm whether
      `vault_share_price_handler.py` has actually run/been scheduled for FRAX-ETHEREUM (`_VAULTS["sFRAX"]`) by reading
      the live defi manifest (scoped read, no new whole-corpus walk) for FRAX-ETHEREUM under
      `data_type=vault_share_price` — genuine absence = a scheduling gap, not an enumeration gap. READ-ONLY: do NOT add
      `fluid` or any protocol to a handler without also wiring a real collector (would write dishonest zero-row manifest
      stamps). Repo: market-tick-data-service. Done when: both findings (the cross-list mismatch inventory + the
      FRAX-ETHEREUM vault_share_price row-count/`attempted_at` classification) are appended to the source doc's Progress
      Log with no handler code changed. Source: `defi_manifest_no_expected_unattempted_seeder_2026_07_26.md`

- [ ] [INFRA] P3. **[CROSS-AG: targets agent-orchestrator, not defi code]** Add an M3 `/done` verification exception in
      agent-orchestrator: when a cross-repo plan commit converts a referenced `- [ ]` todo into a non-checkbox
      `CANCELLED`/`SUPERSEDED` marker (per `task_template.md`'s remove-a-todo convention) within the verification
      window, accept `/done` (or an equivalent explicit-cancellation close) instead of hard-rejecting with
      `cross_repo_pm_file_touched_no_checkbox_flip` — which today forces a `/skip-current-task` with no way to record
      disposition. Repo: agent-orchestrator. Done when: the M3 check accepts a commit converting the referenced todo
      `- [ ]` → non-checkbox CANCELLED/SUPERSEDED marker without a `[x]` flip, with a regression test covering both the
      accepted-cancellation case and the still-rejected plain-no-flip case; `quality-gates.sh` green. Source:
      `defi_manifest_no_expected_unattempted_seeder_2026_07_26.md`

- [ ] [REGISTRY] P3. Tighten the defi POOL data-type validity grain from union-across-protocols to per-protocol in UAC
      `registry/capability_declarations/_defi.py` PROTOCOL_CAPABILITIES, so
      `valid_data_types_for_instrument_type("defi","POOL")` no longer seeds expected_unattempted
      `perp_funding`/`lending_indices`/`liquidations` for a pure-DEX pool (e.g. UNISWAP_V3) while still granting those
      data_types to perp-capable pools that legitimately produce them. Repo: unified-api-contracts. Done when:
      `valid_data_types_for_instrument_type("defi","POOL")` is protocol-scoped (a UNISWAP_V3 POOL yields only
      `dex_pool_state`/`dex_pool_swaps`; a perp-capable POOL still yields `perp_funding`), a new unit test proves the
      tightened per-protocol set, no impossible-combo regression, quality-gates.sh green. Source:
      `defi_migration_audit_log_2026_07_24.md`

- [ ] [SCRIPT] P3. Gate the `migrate_defi_full_v9_canonical.py:570` L1 `_safe_find(fs, {base}/{dir_name})` on a cheap
      prefix-existence probe (or drop it) so the migrator stops issuing a whole-bucket enumeration per
      `day=`-partitioned source bucket that has no top-level L1/raw_tick_data tree — but KEEP a fallback so a bucket
      that genuinely has an L1 tree is never silently skipped (data-loss guard). Repo: market-tick-data-service. Done
      when: the L1 find is guarded by an existence probe; a unit test proves both (a) a `day=`-only bucket skips the
      expensive scan and (b) a bucket with a real L1 tree still enumerates it; a date-scoped dry-run still completes
      0-errors; quality-gates.sh green. Source: `defi_migration_audit_log_2026_07_24.md`

## Deferred — operator decision needed (BLOCKED-OPERATOR-DECISION, not batchable)

- **`issues/defi_turbo_api_hides_real_captured_data_2026_07_07.md`**: Declare HYPERLIQUID/ASTER in UAC
  `ALL_DEFI_VENUES` + `DEFI_VENUE_DATA_TYPE_CAPABILITIES`. batch2 (line ~341) dispatched this doc's OTHER todos
  (EULER_V2/Plasma) and explicitly excluded this one. The `honest_coverage_shard_dimension_model` confirmation only
  resolves the CLASSIFICATION intent (dual CEFI+DEFI listing is intentional), NOT whether declaring into UAC
  `ALL_DEFI_VENUES` double-counts the same on-chain rows across system-wide CEFI+DEFI denominators — an open
  UAC-registry-level axis ruling the operator must make. The doc's own last word (2026-07-21) still flags it as "a real
  follow-up."
- **`defi_migration_audit_log_2026_07_24.md` items 3, 5, 7, 8, 10 (STALE/INVERTED PREMISE)**: all five prescribe giving
  orphan data_types / handler writes DEDICATED buckets, but the dedicated→**shared** consolidation already SHIPPED
  (`defi_consolidated_closeout_2026_07_18.md`:194-195 — all kinds resolve `kind="tick-data"` on the single
  `market-data-tick-defi-prd`; the foundational v9 migration ran 2026-06-18). Drafting these as-is would RE-INTRODUCE
  the divergence the consolidation removed. They need an operator reconciliation of the item text against the shipped
  shared-bucket architecture, not a fresh migrate todo. (item 5's "gas in the could-exist denominator" sub-part is also
  an open design call — gas is chain-grain, not the instrument-universe grain of Track-3's 63.9M seed; item 10 folds the
  already-EXCLUDED item-2 Solana-source ruling, and DefiLlama's status as a canonical on-chain source is itself
  contested — batch2:143 migrated AaveRateImpact OFF the DefiLlama borrow field.)
- **`defi_migration_audit_log_2026_07_24.md` item 2 (SOURCE_PRIORITY Solana source) + item 9 (delete legacy buckets)**:
  item 2 is an operator "which Solana source is canonical" ruling (solana_rpc/helius/defillama); item 9 is a destructive
  legacy-bucket delete requiring operator sign-off per the GCS delete-safety HARD RULE. Item 1 (Era-B legacy retirement)
  is a large cascade-coupled UAC+MTDS registry+test drop — technically AO-eligible now its cefi+tradfi G4-apply gate
  cleared, but sizeable enough it warrants its OWN dedicated plan, not a batch todo.

## Deferred — conflict-gated / sequence-gated (re-check next iteration)

- **`lst_rate_honest_coverage_2026_07_21.md` E3 recursive-staking borrow leg**: builds ON TOP of todo 4 (A2 staking leg)
  in the SAME strategy-service `carry_staked_basis` accrual mechanism — drafting it as a sibling would race on the same
  file. Also still needs its own scoping step (Aave-oracle unblock alone is insufficient per the doc). Re-extract as a
  batch4 todo once todo 4 lands.
- **`data_completion_defi_2026_07_15.md` G6 Jupiter historical reconstruction**: GATED on G1 (Orca+Raydium pool-state
  backfill), which is operator-launched long-wall-clock and not scheduled by any covering plan; and the reconstruction
  approach itself (simulate Jupiter routing vs pool states, "algorithmically nontrivial") is an undecided
  research/design call. Unblock once G1 lands and the approach is ruled.

## Deferred — non-batchable orphans from Phase 1 (report only; need direct human action, not another batch)

These 9 orphaned docs carry ONLY non-batchable-taxonomy remaining work (per the per-doc Phase-1 classification) —
re-running the audit against them will keep reporting the same until a human acts:

- **`defi_venue_lst_rates_residual_2026_07_24.md`** — operator-gated: bare-`SUSHISWAP` classic-vs-V3 alias is a
  data-semantics ruling (same class as the already-made SUSHISWAP/UNISWAP factory-version call).
- **`defi_expected_unattempted_seeder_design_2026_07_26.md`** — operator-gated: IS the standing human plan (assigned_vm:
  NA) batch2 designated as successor to cancelled C8; P0 is an [OPERATOR] capability-vs-collectibility reconciliation,
  P1-P3 BLOCKED-OPERATOR. Becomes AO-eligible only after the operator resolves P0.
- **`issues/architecture_v2_drift_leg_specs_and_manifest_residue_2026_07_16.md`** — human-only/too-large:
  CARRY_STAKED_BASIS delete-vs-re-leg is a strategy-domain judgment; the generator/UI structural-skew item "needs its
  own plan"; the UI resync is blocked on both.
- **`issues/defi_morpho_lending_indices_never_wired_2026_07_12.md`** — time-gated: sole remaining item (re-run G2 gate)
  is blocked on `defi_onchain_v10_universe_v2_seed_or_backfill_progressed` (owned by
  `data_completion_defi_2026_07_15.md`); 13 dispatches already bounced on it. Already in batch2's time-gated Deferred.
- **`issues/defi_five_never_captured_venues_fix_2026_07_22.md`** — human-only: correcting/deleting MORPHOVAULTS
  `GTUSDCP.parquet` garbage share_price row is a prod-bucket data mutation, operator-gated per the GCS
  delete/mutate-safety protocol.
- **`issues/defi_pipeline_mode_source_desync_yearn_v3_2026_07_21.md`** — human-only: Todo 4 is a `[DECISION]`
  remediation ruling (accept legacy artifact vs targeted manifest correction), conditionally gated on todo 1's
  now-covered outcome.
- **`issues/defi_upstream_instruments_catalog_stale_2026_07_15.md`** — human-only: `[DESIGN] P3`
  IS-catalogue-completion-signal retry-sweep is a design call (pub/sub vs sentinel-file vs other; which service owns
  it). Needs a design session first, then a scoped todo.
- **`issues/deployment_ui_capability_bundle_stale_drift_pacifica_2026_07_16.md`** — human-only: regenerating/reconciling
  the 57 `unified-api-contracts/openapi/prospectus/*.md` generator outputs spans many axes unrelated to DRIFT removal —
  needs a human design decision on how to reconcile generator vs committed copies before any worker todo is
  determinable.
- **`issues/onchain_manifest_dishonest_and_recompute_blocked_2026_07_21.md`** — human-only: steps 2-4 (new MTDS
  chain-field collectors for ltv/liquidation_threshold/reward_rate/health-factor inputs + recompute) are "genuinely new
  scope (upstream collection)... size them as their own work" per the doc author. Already in batch2's human-only
  Deferred.

## Note — items already covered (skip_covered, NOT re-drafted)

Phase-3 conflict-check confirmed these 4 items are already claimed by a covering plan (would be duplicates):

- `defi_manifest_no_expected_unattempted_seeder_2026_07_26.md` item 4 (MORPHO absence intentional-check) → owned by
  `defi_expected_unattempted_seeder_design_2026_07_26.md`'s [OPERATOR] P0.
- `data_completion_defi_2026_07_15.md` C5 phantom-grid delete → subsumed by the C0/track01 canon walk + data-status
  dedicated-index repoint.
- `data_completion_defi_2026_07_15.md` instruments-store-defi canonical-form walk → owned by the active cross-cutting
  `instruments_manifest_canonicalisation` plan.
- `data_completion_defi_2026_07_15.md` FLAG2 `_BUCKET_CATEGORY_OVERRIDES` → already RESOLVED at
  `defi_dedicated_bucket_shared_migration_2026_07_13.md`:257-268 ([x] ✅ deployment-api).

## Note — archival candidates (archivable_now — a separate archival todo, not a batch candidate)

- `issues/e2e_defi_strategy_funding_apr_gas_correctness_2026_06_17.md` — Final report (2026-06-17) declares done state;
  all 6 BUGs fixed; sole open item self-migrated to `perp_funding_data_semantics_and_cadence_2026_06_16.md`. Archive.
- `issues/mtds_perp_funding_backfill_hang_2026_07_14.md` — all 6 todos [x] with evidence; residual spun to
  `mtds_retry_safe_default_audit_2026_07_14.md`. Archive (batch2 already flagged this one archivable_now).

## Note — 1 mistag (exclude_cross_cutting)

- `issues/mtds_empty_string_fallback_codex_gate_blocking_pushes_2026_07_08.md` — tagged `asset_group: [defi]` but real
  content is a fleet-wide QG STEP 5.101 infra/CI issue, not defi-specific. Should be retagged `cross-cutting` or `infra`
  (batch2 already flagged this as a mistag Note).

## Deferred work — migrated to: N/A (this plan itself is not deferred/migrated)

This plan's own `## Deferred — ...` sections each cite their source issue doc directly as the successor reference; no
part of this plan was migrated elsewhere.

## Progress Log

- **2026-07-26** — Drafted autonomously by the scheduled `ag_closeout_auditor` (slot 15, tranche=defi) via the
  `/ag-closeout-audit` skill. Phase 1: 59 defi AG-primary docs classified by a 59-agent Workflow (sonnet) → 39
  archivable-after-planned-work, 15 orphaned_partial, 2 orphaned_never_touched, 2 archivable_now, 1 exclude. Phase 3: 8
  AO-eligible orphan docs conflict-checked by an 8-agent Workflow (opus) → 13 draft / 4 skip_covered / 8 conflict_park;
  merged 2 same-source read-only report todos into todo 9 → **12 todos**. `status: draft` — awaits operator approval to
  flip to `active`.
