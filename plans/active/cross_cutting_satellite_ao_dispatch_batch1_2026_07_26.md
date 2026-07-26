---
doc_type: plan
title:
  Cross-cutting satellite AO batch 1 — first Phase-1/Phase-3 triage of the cross-cutting closeout-orphan corpus (part 1
  of 2)
summary: >-
  First AO-dispatch batch for the cross-cutting tranche (genuinely cross-asset-group data-pipeline work — never audited
  before this session), produced by the `/ag-closeout-audit` skill's full Phase-1 (per-doc classify) + Phase-3
  (conflict-check + draft) triage over all 59 cross-cutting AG-primary docs not covered by any existing AO batch (none
  existed before this run) or claimed by the sibling `ao`/`ci`/`infra` tranches (36 docs excluded as belonging to those
  tranches instead). 50 docs came back orphaned (2 partial coverage, 48 never touched — expected, since no dispatch
  mechanism existed for this tranche until now); 7 were mistags (2 genuinely single-AG — `defi`, `cefi` — and 5
  genuinely `infra`-scoped, not retagged here, flagged below); 2 were fully done (archivable_now, not actioned here).
  Phase 3 cleared 31 of the 50 orphans into fresh AO-dispatch todos with zero cross-todo file collisions beyond one
  coordinated `smoke_matrix.py` sequencing note (both todos carry inline coordination text); split across two sibling
  batch docs (16 here, 15 in `cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md`) to stay under the workspace's
  1000-line hard cap after prettier reformatting (31 todos at this corpus's todo-density would breach it in one file, a
  confirmed failure mode from this session's defi batch2 draft). Left 4 conflict-gated, 13 operator-gated, and 2
  time-gated items in the Deferred sections below (this doc only — batch1b defers to this doc's sections, not a
  duplicate) for the next iteration or an explicit operator ruling.
status: active
nature: process
asset_group: [cross-cutting]
stage: [data]
repos:
  [
    unified-trading-pm,
    instruments-service,
    market-tick-data-service,
    market-data-processing-service,
    features-service,
    unified-api-contracts,
    unified-trading-library,
    deployment-api,
    deployment-service,
  ]
scope: [engineer]
tags: [cross-cutting, ao-dispatch, close-out, batch-1, satellite-docs, fresh-triage]
related:
  [
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /plans/active/cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-07-26"
last_updated: "2026-07-26"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 4.0
estimate_calibrated_ai_days: 3.2
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  /ag-closeout-audit skill run 2026-07-26 (interactive, operator-approved scope) — Phase 1 classified all 59
  cross-cutting AG-primary docs not already claimed by a covering plan or the ao/ci/infra tranches via a Workflow
  fan-out (59 agents), Phase 3 ran a conflict-check + candidate-todo draft over the 50 orphaned docs via a second
  Workflow fan-out (50 agents, 1 retried individually after a StructuredOutput retry-cap failure), per the skill's
  documented methodology.
assigned_role: data_engineering
sequential: false
drift_direction: advance-code
---

# Cross-cutting satellite AO batch 1 (part 1 of 2) — fresh triage extraction

> **Status: draft.** Per CLAUDE.md's plan-destination rule and the ag-closeout-audit skill's autonomous-mode guidance, a
> skill-drafted AO batch is never auto-shipped to `active` — flip this frontmatter's `status` to `active` only after
> operator review. This doc + its sibling `cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md` should be
> approved/flipped together (both cover the same conflict-checked pass, split only for the line cap). All 16 todos below
> are same-priority-independent and touch distinct files/docs, except the `smoke_matrix.py` pair (todo citing
> `silent_wrong_answer_audit_candidates_2026_07_20.md`) which carries inline coordination text with its sibling in
> batch1b — do not strip that text if editing before dispatch.

## Todos

- [ ] [DOCS] P2. **Reconcile the two bookkeeping-only residuals in
      `bucket_estate_consolidation_closeout_2026_07_24.md`** (cross-cutting, first AO batch for this doc): (a) re-verify
      current deletion status of the 3 items in the "Track to completion the deletions OWNED BY OTHER PLANS" checkpoint
      — `dex-pools-prd`/`lst-rates-prd`/`perp-funding-prd` (per `[[defi_dedicated_bucket_shared_migration_2026_07_13]]`
      todos 6-9), `lending-indices`/`-prd` (gated on VM `mtds-lending-indices-20260712-112557`), and the legacy flat
      tick+instruments twins (per `data_completion_to_100_all_ag_2026_06_21.md` M-1 L6) — query current bucket existence
      (`gcloud storage buckets list` / `aws s3api head-bucket`) and the cited owning plans' latest status, then update
      the checkpoint's checkbox/text to reflect what's actually still pending vs. closed; (b) identify the "three
      bucket-SSOT audit issue docs" this doc's DOCS-P3 todo references (not named by filename anywhere in the corpus —
      search `plans/active/issues/` for GCS hardcoded-bucket-literal / bucket-naming audit docs dated around the
      2026-07-13→07-17 fold window, e.g. `legacy_bucket_template_literals_2026_07_16.md` is a strong candidate;
      cross-check against `bucket_estate_fold_design_2026_07_13.md`'s "hardcoded-name sweeps in the three audit issue
      docs" citation trail), then for each identified doc re-verify its current status against the now-DONE
      ml/features/execution/portfolio-state folds and close it (or explicitly re-confirm still-open with a reason) —
      flip this doc's DOCS-P3 checkbox once all 3 are accounted for. Source:
      `bucket_estate_consolidation_closeout_2026_07_24.md`. Done when: both checkboxes reflect a freshly-verified status
      (not carried-forward text) with cited evidence (bucket-existence probes, owning-plan status quotes, or issue-doc
      close commits), and the 3 audit-issue docs are named explicitly in this doc's evidence trail.
- [ ] [TERRAFORM] P2. **Join folded `features-{ag}-prd` buckets to Group-B IAM + add COLDLINE lifecycle** — Source:
      `bucket_fold_features_2026_07_17.md`'s open P2 "IAM + lifecycle" todo. (a) Once
      `bucket_iam_write_protection_per_tier_2026_06_09.md` Phase 1 (P1.1-P1.3: per-tier SAs + per-suffix IAM bindings)
      has landed, extend that plan's Phase-2 Group-B terraform to bind
      `features-{cefi,defi,tradfi,sports,pred}-prd-central-element-323112` to the `-prd-` write-scope SA and
      `features-*-test-*` to the test-tier SA (the Wave-3 fold precondition — env-tiered `-{env}-` naming — is already
      met, so this is unblocked the moment Phase 1's SA/binding structure exists; if Phase 1 has not yet landed, do the
      lifecycle half below now and leave the IAM half `[ ]` with a note citing the blocking Phase-1 status, do not
      silently skip it). (b) Independently of (a), add a `STANDARD→COLDLINE@60d` whole-bucket lifecycle rule for the 5
      `features-{ag}-prd` buckets (+ `-test-` twins) in the derived-from-yaml terraform (`canonical_buckets.tf` /
      `setup-buckets.py`, same mechanism as the other folded families). Done when: `terraform plan` shows the new IAM
      bindings + lifecycle rules with zero unrelated bucket create/destroy, and (if (a) landed) a negative IAM test
      confirms a non-prd credential is denied a `features-*-prd-*` write.
- [ ] [DESIGN] P2. **Land colocated feature pipeline in-memory DAG handoff + parquet consolidation + basedpyright
      strictness restore** — (1) pass derived feature frames between calculators in-process instead of round-tripping
      through parquet, so a colocated run computes the dependency DAG once; (2) consolidate the per-instrument parquet
      fan-out into a single file per (day, feature_group, timeframe) to cut object count + selective-read list cost; (3)
      restore features-service `pyrightconfig.json`/`pyproject.toml`
      `reportUnknownMemberType`/`reportUnknownVariableType`/`reportUnknownArgumentType` (+6 more) severities from
      `"none"` back to `error` (or a downward-only ratchet) and burn down the ~574 masked errors, adding no new
      suppressions. Repo: features-service. Source: colocated_feature_pipeline_in_memory_handoff_2026_06_21.md (items
      1.4, 1.3b, 1.7e — item 1.5b read-time column pruning intentionally excluded, still gated behind
      `features_service_e2e_pipeline_test_2026_05_26.md` reaching end-to-end green). Done when: features-service
      `quality-gates.sh` is green with a measured I/O reduction (object count / read bytes) shown for a sample (day, fg,
      tf) covering items 1-2, and basedpyright `reportUnknown*` severities are `error` (or a stated downward-only
      ratchet) with the prior ~574 errors resolved and zero new suppressions for item 3.
- [ ] [SCRIPT] P1. **Cross-cutting data-completion prep residuals — `data_completion_to_100_all_ag_2026_06_21.md` Step
      4 + finding-144 follow-up.** Two independent, bounded items from the target doc that no active cross-cutting/AG
      closeout batch currently claims: (a) **Credential-gated venue asks (Step 4, L786-787)** — file BLOCKED-CREDENTIALS
      ask docs (one per vendor, under `plans/active/issues/`) for Helius/Alchemy, Glassnode/Kaiko, Tardis (historical
      billing), Databento, and Sportradar/Odds-API, each naming the exact capability blocked and the specific credential
      needed; per the external-data-always-available HARD RULE, also scaffold the adapter/handler code path + unit tests
      for each vendor now (status `BLOCKED-CREDENTIALS`, no live backfill until creds land — do not wait on the ask to
      start scaffolding). (b) **VM-launch canonicalisation-gate check (L139-140)** — add a gate-check step to the
      VM-launch protocol (`deployment-service/scripts/vm/` launcher common path) so a launcher refuses/warns when the
      target asset_group's canonicalisation gate is not GREEN; recurrence-prevention follow-up from finding 144
      (`plans/active/issues/plan_reconciliation_operator_decisions_2026_07_11.md` §A2). Confirmed distinct from
      `infra_consolidated_closeout_2026_07_25.md` Track 2's billing-waste pre-flight gate (different mechanism: billing/
      preemption, not canonicalisation-state). Source: `data_completion_to_100_all_ag_2026_06_21.md`. Done when: 5
      credential-ask issue docs filed + their adapter scaffolds/tests land (each PASSING with BLOCKED-CREDENTIALS
      status, no real vendor calls); AND the launch-protocol gate-check ships + is exercised against both a GREEN and a
      non-GREEN asset_group in a test/dry-run, with both todos flipped `[x]` in the source doc citing repo@sha evidence.
- [ ] [MTDS] P1. **A12a follow-through — wire `assert_defi_catalog_fresh()` preflight into the still-unwired DeFi
      collect handlers.** Re-verified against current code (2026-07-26): of the doc's original 23-handler list, several
      are already wired (progress since 2026-06-04) — `lending_indices_handler`, `liquidations_handler`,
      `liquidation_events_handler`, `bridge_events_handler`, `token_transfers_handler`, `aggregator_route_handler`,
      `flash_loan_events_handler`, `solana_defi_handler` all already call `assert_defi_catalog_fresh` (that subset is
      instead covered by `defi_satellite_ao_dispatch_batch1_2026_07_25.md`'s separate "thread `mode=`" todo — do not
      re-wire those). The genuinely still-unwired handlers in
      `market-tick-data-service/market_tick_data_service/cli/handlers/`: `dex_swaps_handler.py`,
      `perp_funding_handler.py`, `oracle_prices_handler.py`, `staking_yields_handler.py`,
      `eigenlayer_rewards_handler.py`, `vault_share_price_handler.py`, `gas_fee_handler.py`,
      `governance_events_handler.py`, `governance_proposals_handler.py`, `mev_events_handler.py`,
      `position_data_handler.py`, `jupiter_quote_handler.py`, `phoenix_orderbook_handler.py`,
      `orca_whirlpool_state_handler.py`, `raydium_classic_amm_handler.py`, `evm_defi_handler.py` (confirm
      `drift_v2_historical_handler` still exists under its current name before wiring; skip if renamed/removed). For
      each: call `assert_defi_catalog_fresh(...)` at the handler's `process()` chokepoint before the source fetch,
      mirroring the exact pattern already shipped in
      `dex_pools_handler.py`/`lst_rates_handler.py`/`lending_indices_handler.py` (import + wrap + route honest absence
      via `record_failed` per shard, never raise in the per-venue loop); patch `assert_defi_catalog_fresh` → True in
      each handler's existing `process()` tests. Source: `data_source_provenance_enforcement_2026_07_24.md`. Done when:
      every listed still-unwired handler calls `assert_defi_catalog_fresh` at its chokepoint, each handler's test suite
      is green with the patch applied, and `market-tick-data-service` quality gates pass.
- [ ] [DATA] P1. Reconcile the CURRENT (2026-07-25 refresh, 45-total) non-canonical distinct-value set to an owning
      plan/issue per value, since the original 175-finding per-cluster JSON needed to re-verify the 22 prior category-1
      owning-plan citations was deleted in the 2026-07-21 pre-compact sweep (that JSON being un-recoverable is not a
      blocker — work off live data instead). Run the live `_axis_census.py`/`_distinct_values.py` endpoints per
      asset_group (same mechanism already used for the 175→115→45 refresh) to enumerate the actual current non-canonical
      VALUES (not just per-axis counts) across all 5 AGs × 4 axes. For each value: (a) if it maps to one of the
      already-attributed cat-1 clusters (the 22 documented in the Progress Log / classification framework), confirm the
      citation still resolves to a live owning plan/todo; (b) for any value with no existing attribution (including
      net-new drift surfaced since 2026-07-20, e.g. defi `HYPERLIQUID` chain, cefi `volatility_index`, prediction
      `instrument_types`/`data_types` growth noted in the 2026-07-25 Progress Log entry), attribute it to an in-flight
      plan if one owns it, or file a new `plans/active/issues/<slug>_<date>.md` if none does. Source:
      `plans/active/distinct_values_noncanonical_audit_2026_07_20.md` line 191 todo + the 2026-07-25 "census refresh
      (the one remaining open todo)" Progress Log section. Done when: every currently non-canonical value across all 5
      AGs has an explicit owning-plan or owning-issue citation recorded in this doc's Progress Log (or a new issue doc
      filed for any that don't), and the line-191 checkbox is flipped with that evidence cited.
- [ ] [INFRA] P2. **Infra/ops residual tail — bounded fixes (rollup image-lag, deployment-ui could-exist/capture
      surfacing, local-dev restart flakiness, unique_instruments precompute).** Four independent, self-contained fixes
      carried unfixed from the archived migration-verification harness; do all four in one pass: **(A)** Make
      `deployment-service/scripts/cloud-run/deploy-shared.sh` (or the cloud-build-router deploy dispatch) also bump the
      `uts-prod-data-status-rollup` Cloud Run Job's `deployment-api` image tag (or pin both to the same digest) so a
      code deploy auto-refreshes the rollup — Done when: a `deploy-shared.sh` run updates both the
      `uts-shared-deployment-api` service AND the rollup Job to the same image digest, verified via
      `gcloud run jobs describe uts-prod-data-status-rollup`. **(B)** deployment-ui `DataStatusTab`/`HonestCoverageCard`
      — surface shards-weighted could-exist completion_pct, manifest-capture ratio, and `out_of_window` as three
      distinct labeled values (not one ambiguous card) — Done when: `[UI]` + `pw:L2 ✓` regression spec confirms all
      three render distinctly. **(C)** Make the local-dev restart helper (`restart-deployment-stack`-style script)
      deterministically port-clear `:8004` before relaunch (e.g. `fuser -k` built in) instead of relying on manual
      workaround — Done when: repeated restarts no longer race on bind. **(D)**
      `deployment_api/scripts/data_status_rollup_worker.py` — add the catalogue read for `unique_instruments` to the
      LIVE (non-beta) fast path and redeploy the Cloud Run job — Done when: a live rollup run's coverage summary
      includes `unique_instruments` without the recompute fallback. Source:
      `infra_ops_residual_migration_verification_2026_07_24.md` (items 3-6 of 9; forked verbatim from the archived
      `migration_verification_orphan_safety_2026_06_10.md`).
- [ ] [DATA] P1. **InstrumentRecord extra='forbid' — get the authoritative list + apply the already-justified REMOVE
      dispositions.** On a branch, flip `model_config = ConfigDict(extra="forbid")` on
      `unified_api_contracts/internal/reference/instrument.py::InstrumentRecord` and run the FULL UAC +
      instruments-service suites (not a `-k` subset); collect every `extra_forbidden` field name + its adapter/call-site
      into the plan's Progress Log as the authoritative complete list (supersedes the 2026-07-18 partial measurement +
      static scan). Apply the operator's three-part test (code-usage / business-reason / not-already-exists) to each
      newly-surfaced field the same way the pre-analysis already did for the four confirmed kwargs. For fields where the
      test is unambiguous REMOVE (this already covers `symbol`→zero usage, covered by `raw_symbol`; `is_active`→zero
      usage, covered by `status`; `updated_at`→zero usage, no consumer — plus any newly-surfaced field from the
      full-suite run or the static-scan defi/deribit candidates
      (`spot_asset`/`debt_symbol`/`onchain_symbol`/`contract_address`/`decimals`/`borrow_symbol`/`capability`) that
      scores zero-usage the same way), drop the undeclared kwarg from every adapter call site the run surfaced. Do NOT
      touch `min_order_size` (already flagged operator-judgment: semantically distinct from `min_size`, execution-sizing
      use unclear) or any other field where the three-part test is genuinely ambiguous — leave those with their evidence
      in the Progress Log for a follow-up operator ruling, and do NOT permanently flip `extra='forbid'` on main (that
      requires every surfaced field resolved, including the judgment-call ones). Source:
      instrument_record_schema_completeness_extra_forbid_2026_07_18.md (todos 1-2, partial 3-4 for the REMOVE-only
      subset). Done when: the branch run's authoritative field list + per-field verdicts are recorded in the plan's
      Progress Log; every REMOVE-verdict kwarg is dropped from its caller(s) with UAC + IS suites green on that subset;
      `min_order_size` and any other ambiguous-verdict field(s) are left explicitly open with their evidence, distinct
      from the resolved set; `extra='forbid'` is NOT merged to main yet (still gated on the remaining judgment calls).
- [ ] [ADMIN] P1. Reconcile `instruments_completion_tracker_2026_07_06.md`'s Stage 1–6 checkboxes against its own
      now-**archived/complete** AO children — `plans/archive/issues/cefi_layer1_denominator_gaps_2026_07_03.md`
      (resolved, Stage 2a/2b/2c/2f all `[x]`), `plans/archive/2026_07/tradfi_v9_stage1_finish_2026_07_06.md` (resolved),
      `plans/archive/2026_07/is_catalogue_completion_2d_2026_07_06.md` (complete, Stage 2d),
      `plans/archive/2026_07/layer1_remeasure_and_certify_2026_07_06.md` (complete),
      `plans/archive/2026_07/foundation_gates_and_capture_to_100_2026_07_06.md` (complete, Stage 4/5) — plus the
      still-active `plans/active/infra_capture_and_devops_leftovers_2026_07_06.md` (Stage 5 Deribit options_chain
      live-runner already `[x]` there) and the resolved
      `plans/archive/issues/instruments_service_data_status_endpoint_dead_code_2026_07_07.md` (Stage 6 dead-endpoint
      item, deleted `is@650dd4b7`). For each currently-unchecked tracker checkbox, grep the corresponding archived-child
      plan's own checkboxes/Progress Log for shipped-SHA evidence: if genuinely done, flip to `[x]` with a
      `<repo>@<sha>` citation; if the archived child only partially covers it, annotate with what remains; if still
      genuinely open (this is expected for: Stage 3 re-measure — explicitly blocked on tree-quiescence per the doc's own
      2026-07-10 notes, do not force a live re-run as part of this todo — Stage 4 tradfi §8 retirement purge —
      OPERATOR-CONFIRM gated — Stage 4 defi oracle design, Stage 5 credential/operator-gated items and the prediction
      live token-universe item, and Stage 6's manifest-reprocessing-utility and smoke-harness/UI-drill-down items, which
      stay open and are separately tracked under `cross_cutting_consolidated_closeout_2026_07_25.md` Track 14/Track 7),
      leave unchecked. Append one dated Progress Log entry summarizing what flipped vs what's confirmed still-real.
      Source: `instruments_completion_tracker_2026_07_06.md`. Done when every Stage 1–5 checkbox reflects its archived
      child's actual shipped state (with citations) and the doc's own Snapshot/open-count is no longer stale relative to
      those 5 archived plans.
- [x] ✅ [SCHEMA] P0. **DONE 2026-07-26 (slot-7) — `unified-api-contracts@1407b7f`.** Landed
      `CompletenessProbe`/`CompletenessProbeStatus`/`CompletenessProbeKind` in
      `canonical/crosscutting/honest_coverage.py` per design doc §2, plus `factory_address_by_chain` on
      `_ProtocolCapability` populated with WEB-VERIFIED on-chain addresses (cross-referenced against 2+ block explorers
      each) for all 10 listed DEX protocols — uniswap_v2 (ETHEREUM), uniswap_v3 (ETHEREUM/ARBITRUM/
      BASE/OPTIMISM/POLYGON, same address per Uniswap's deterministic deployment), uniswap_v4 (ETHEREUM PoolManager),
      balancer (6 chains, single Vault), curve (AddressProvider, 3 chains), pancakeswap_v3 (BSC/ ETHEREUM/BASE),
      sushiswap_v3 (ETHEREUM/BASE — AVALANCHE honestly omitted, unverified this pass), aerodrome_v3 (BASE), velodrome_v2
      (OPTIMISM), camelot_v3 (ARBITRUM). New `tests/unit/test_completeness_probe.py` exercises the §1 semantic table
      (complete/gap/over_enumerated/undefined/probe_failed) via direct dataclass construction + asserts factory-address
      population/shape. QG green (exit 0, 411s). Schema-only per scope — no probe implementations, no
      `--use-defi-oracle` wiring. **Land the DeFi completeness-oracle `CompletenessProbe` schema in UAC (first
      implementation slice of the already-designed oracle).** The design SSOT
      (`/codex/02-data/defi-completeness-oracle.md`, status: current, 2026-07-06) fully specifies the on-chain
      `poolCount`-cross-check oracle answering "do we have ALL DeFi instruments?" (Source:
      instruments_foundation_completeness_2026_06_24.md P0 DeFi-completeness-oracle item, lines 190-201) — its §9
      rollout section was never actually filed as a plan todo anywhere in the active corpus (confirmed via grep: zero
      hits for `CompletenessProbe`/`probe_registry`/`use-defi-oracle` across `plans/active/`, including the named
      landing plan `defi_pipeline_e2e_and_coverage_validation_2026_06_20.md`). Implement the §9 P0 schema step only: add
      `CompletenessProbe` + `CompletenessProbeStatus` + `CompletenessProbeKind` to `unified-api-contracts`
      `canonical/crosscutting/honest_coverage.py`, plus `factory_address_by_chain: Mapping[str, str]` (default empty
      dict) on UAC `_ProtocolCapability`, populated for the top-10 DEX protocols (uniswap_v2/v3/v4, sushiswap_v3,
      balancer, curve, pancakeswap_v3, aerodrome_v3, velodrome_v2, camelot_v3 — NOT gmx, removed 2026-07-25 per
      `/plans/archive/2026_07/defi_gmx_venue_removal_2026_07_25.md`). Unit tests exercise the semantic table in the
      codex doc's §1. Repo: unified-api-contracts. Done when:
      `CompletenessProbe`/`CompletenessProbeStatus`/`CompletenessProbeKind` types exist and are QG-green with passing
      unit tests, and `factory_address_by_chain` is populated for the 9 listed protocols on `_ProtocolCapability` — this
      is schema-only (no probe implementations, no `--use-defi-oracle` wiring), matching exactly the design doc's own P0
      rollout step.
- [ ] [AUDIT] P1. **Reconcile GATE 0's 10 Phase-0 cross-cutting checklist items against what cefi/tradfi child plans
      already shipped, then flip only what's genuinely done.** Phase-1 orphan evidence confirmed all 10 items in
      `instruments_foundation_phase0_cross_cutting_2026_07_24.md` §"Phase 0 — cross-cutting foundations" still read
      `- [ ]` and GATE 0 is recorded NOT signed off — but a cross-check against
      `instruments_cefi_g1_g5_gate_execution_2026_07_24.md`'s Progress Log shows several of the SAME cross-cutting
      mechanisms already shipped per-AG (UAC layered-coverage SSOT `compute_layered_coverage`/`LayeredCoverage` @UAC
      755c40515; `instruments-service/scripts/measure_honest_coverage.py` exists in-repo; cefi canonical-form audit
      done; cefi deployment-observability verified BUILT) — the cross-cutting doc's own checkboxes are simply stale, not
      necessarily the underlying work. For EACH of the 10 items (observability wiring, Honest-Coverage v2 layered SSOT,
      cumulative-drawdown metric, expected-universe oracle design, consolidation reconcile, drilldown-correctness guard,
      verification discipline, silent-cap audit, depth-aware re-fetch, cost/entitlement reason class) and the 2
      folded-in checkboxes (IS daily definition producer rebuild; prediction/sports granularity-aware catalogue
      producer): grep+read the cefi (`instruments_cefi_g1_g5_gate_execution_2026_07_24.md`), tradfi
      (`instruments_tradfi_g1_g5_gate_execution_2026_07_24.md`), and defi (`defi_consolidated_closeout_2026_07_18.md` /
      DONE-exemplar canonical-form migration) plans plus the live code (UAC `honest_coverage.py`,
      `instruments-service/scripts/measure_honest_coverage.py`, `deployment_api`/`deployment_service` observability
      registries) to determine the item's TRUE current state. Flip a checkbox to `[x]` ONLY with a
      commit-sha/prod-verification citation; leave genuinely-unbuilt items (e.g. the reused-cross-AG generalization to
      sports/prediction, the expected-universe oracle Tier-B truth) open. Do NOT re-implement anything already shipped
      elsewhere — this is reconciliation, not a rebuild. Explicitly do NOT touch the G1.1-G1.4 cefi
      catalogue-correctness items (those are owned + mostly DONE in the cefi child plan already). Source:
      `instruments_foundation_phase0_cross_cutting_2026_07_24.md`. Done when: every one of the 10 GATE-0 checkboxes +
      the 2 folded-in checkboxes carries an accurate state with an evidence citation (shipped-elsewhere sha, or
      confirmed still-open), and the GATE-0 banner line is updated to reflect the reconciled true state (still correctly
      "not signed off" if any item remains genuinely open).
- [ ] [DATA] P2. **Close 5 small bounded residuals from
      `instruments_mtds_consistency_remediation_residuals_2026_07_24.md`** (Source:
      plans/active/instruments_mtds_consistency_remediation_residuals_2026_07_24.md). (1) Recover the true POLYMARKET
      venue for the 21 captured `UNKNOWN`-venue prediction `_index` `trades` cells (2025-03-14..) by joining to the
      same-day `pipeline_mode=batch_polymarket_clob/venue=POLYMARKET` object, or route to honest-absence if no match —
      market-tick-data-service. (2) Diagnose the writer that emitted 14 blank-`data_type`/`instrument_type` CEFI
      `_index` rows tagged bare `COINBASE`(7)/`OKX`(7) (real per-market data lives under the suffixed
      `COINBASE-SPOT`/`OKX-SPOT`/`OKX-SWAP` venues) and reclassify them — market-tick-data-service. (3) Verify
      (verify-only, do NOT launch a new backfill) that all 9 CME EC* event-contract series
      (ECES/ECNQ/ECRTY/ECYM/ECGC/ECCL/ECNG/EC6E/ECBTC) land in the v9 `_index` and are explicitly checked by v9 final
      certification — the execution plan-of-record `tradfi_cme_event_contract_backfill_2026_06_20` is already ARCHIVED
      status=complete/TRULY-DONE (100% coverage confirmed 2026-06-30), so this item is a certification-check, not new
      work — market-tick-data-service/instruments-service. (4) Confirm whether the 19 pre-instruments-genesis
      (2020-01-01..19) Ethereum DeFi MTDS cells warrant an earlier instruments-service genesis date, or mark them
      spurious — instruments-service. (5) Reconcile the PRED `_index` `data_type` label drift
      (`prediction_canonical_question_group` vs the GCS-observed label), composing with item (1)'s venue recovery.
      **Done when**: each of the 5 sub-items has a recorded disposition
      (recovered/reclassified/confirmed-spurious/verified-present) with cited evidence (object path or index diff), and
      the corresponding checkboxes in the source doc are flipped.
- [x] ✅ [DATA] P0. **Instruments-store CF-1…CF-12 single-walk (C0→E3→E4→E5→E6), sequential.** RECONCILED + CLOSED
      2026-07-26 — the VM-launched bulk single-walk this todo assumed was NOT needed. Live re-audit
      (`cf_manifest_audit_2026_06_01.py`, read-only, no whole-corpus walk) against all 4 non-sports instruments-store
      prod buckets showed cefi/defi/tradfi were ALREADY CF-1/CF-2/CF-3/CF-6/CF-9/CF-13 GREEN (the C0 path/partition
      migration this todo describes already landed for those 3 AGs via the doc's own earlier
      `populate_is_index_v9_     2026_06_19.py` work — the todo's own "reconcile scope before running" caution was
      correct). The ONLY real residual was CF-4 (blank `source`, 134 rows total across the 4 buckets) + CF-8 (null
      `available_at`, 1,884 rows total) — an ACTIVE writer gap, not a migration gap:
      `record_expected_empty`/`record_expected_unattempted` (unified-trading-library
      `manifest_writer/_writer_record.py`) never threaded an `available_at` parameter at all. Fixed at the root —
      unified-trading-library@03cfa0ac (added `available_at` to both, forwarded through `record_expected_empty`'s
      internal `record_empty` call) + instruments-service@9c203ce1 (threaded `available_at` at the 2 tradfi
      non-trading-day callsites + the cefi/defi/tradfi venue-pre-launch + expected_unattempted EU-seed callsites in
      `process_write.py`, plus a new CAS-safe manifest-backfill script
      `scripts/backfill_is_source_blank_and_available_at_null_2026_07_26.py` for the rows already written before the
      fix). Backfill applied (`--apply`) against all 4 prod buckets same session; **re-audit confirms cefi/defi/tradfi
      now fully GREEN, pred GREEN on CF-4/CF-8** (see below). New unit tests added in
      `test_manifest_writer_record_empty_reason.py` for both signature changes.

      **Residual, NOT fixed here (filed separately)**: prediction's object-path scheme genuinely lacks
                                  `asset_group=`/`pipeline_mode=` segments (CF-2-paths/CF-3-partition RED) — unlike cefi/defi/tradfi (where
                                  `pipeline_mode` is a single constant value, so retrofitting the path segment was harmless uniformity),
                                  prediction carries 4 distinct `pipeline_mode` values across 2 structurally different existing path shapes, so
                                  this is a genuine architect-level design call (not a mechanical copy) — filed as
                                  `plans/active/issues/instruments_store_prediction_path_scheme_not_asset_group_pipeline_mode_2026_07_26.md`
                                  (merged via PR #1593), NOT executed here.

                                  **[OPERATOR] VM-launch + legacy-bucket delete**: NEVER executed — confirmed unnecessary for cefi/defi/tradfi
                                  (already canonical) and correctly gated behind the pred architect decision above (out of scope for this todo).

                                  **`instruments_master_audit_instructions.md` CF-coverage checkboxes**: NOT flipped — that checklist's CF-1…CF-12
                                  items are worded as ALL-5-AG (including sports), and this todo's scope + today's re-audit is non-sports only;
                                  flipping those checkboxes on partial (4-of-5-AG) evidence would overclaim. Leaving them open for whoever next
                                  re-verifies sports.

                                  Evidence: unified-trading-library@03cfa0ac, instruments-service@9c203ce1+a4e8e1c9; live re-audit output (cefi/defi/tradfi
                                  `=== SUMMARY …: GREEN — all CF pass ===`; pred `=== SUMMARY …: RED — ['CF-2-paths', 'CF-3-partition'] ===`, both
                                  of which are now the ONLY reds, exactly matching the filed issue doc's scope).

- [ ] [SCRIPT] P3. Fix `canonicalize_instruments_store_index.py`'s `_bucket_for` to route `asset_group=prediction`
      through `kind="instruments-store-prediction", asset_group=None` instead of raising `BucketNamingError` via the
      per-AG `resolve_bucket_name` path (dead path today since prediction's `_index` is already clean — nice-to-have,
      unblocks any future re-canonicalisation run). Source:
      `instruments_store_cf_canonicalization_single_walk_2026_07_24.md`. Done when: `--asset-group prediction` runs
      without raising and correctly resolves the prediction bucket.

- [ ] [CODE] P2. **IS audit-finding cleanup sweep (independent, different files — dispatch concurrently).** (a) Confirm
      UTL `record_captured_from_counts` auto-stamps `default_source` for single-source cells, else thread `source=`
      through the 9 blank-source `orchestrator.py` callsites (unified-trading-library + instruments-service); (b) make
      `orchestrator.py:4271` `_af_record_empty(reason=...)` take a required typed `EmptyConfirmedReason`; (c) narrow the
      broad excepts at `orchestrator.py:3794` (catch `NotFound` only, drop the `# type: ignore[union-attr]` at :3791)
      and `:7821`; (d) make the bar-edge fallback-to-open in `cefi/hyperliquid.py:257`, `cefi/ccxt_adapter.py:310-312`,
      `tradfi/polygon.py:243` total (raise/skip on unknown timeframe instead of silently falling to open); (e) replace
      the `os.environ["DEPLOYMENT_ENV"]="test"` runtime mutation at `orchestrator.py:8033-8041` and
      `sports_dependency.py:90-98` with an explicit `env=` param to `resolve_bucket_name`; (f) harden IBKR
      systemic-failure path (`tradfi/ibkr.py:337-348`, `_ib is None`/all-fail → `[]` no raise) — latent, IBKR not in
      `_TRADFI_VENUES` today; (g) fix the `instruments-store-prediction-…` vs SSOT `instruments-store-PRED-…`
      bucket-name mismatch in `deployment-service/terraform/gcp/lifecycle_catalogue_scheduler.tf:40-44`; (h) correct the
      over-broad "instruments-service owns all venue URLs" CLAUDE.md line (InstrumentRecord carries only
      `source_archive_url_template`); (i) fix `instruments_master_audit_instructions.md` item (g)'s stale "`rg URDI` → 0
      hits" claim + the stale error message at `urdi_reference_provider.py:116`; (j) investigate the 16%-of-shards
      multi-row schema-drift dup (`scripts/dedupe_manifest_schema_drift.py`) and fix writer-side row-key idempotency +
      `instrument_type` normalisation; (k) cloud-agnostic sweep of ~60 scripts (`google.cloud`/`boto3` →
      `get_storage_client()`) + ~30 inline bucket literals → `resolve_bucket_name` + the `/tmp/` hardcode in
      `enumerate_expected_universe.py:1381`; (l) delete the orphaned static-snapshot catalogue path
      (`reference_data/catalogue/catalogue_builder.py` `CatalogueBuilder` + `orchestrator.py refresh_catalogue`,
      superseded by `build_instrument_catalogue.py`, no live caller). Source:
      `instruments_store_cf_canonicalization_single_walk_2026_07_24.md`. Done when: each sub-item's fix lands with a
      passing regression test/verification and the corresponding checkbox in
      `instruments_store_cf_canonicalization_single_walk_2026_07_24.md` flips.
- [ ] [INFRA] P1. Fix the scheduled `uts-prod-cf-manifest-audit` Cloud Run Job (asia-northeast1, cron 06:00 UTC), which
      has produced zero successful runs since 2026-07-04 (fails daily -- most days exit-1 "Application exec likely
      failed", 2026-07-13 specifically OOM'd at its 4Gi limit on the `--all-ags` invocation) -- affecting all 5
      asset_groups' daily CF-1..CF-14 manifest audit equally. Diagnose the non-OOM exit-1 days (2026-07-04 through
      2026-07-12) via `gcloud run jobs executions describe` + Cloud Logging to confirm whether they're the same OOM
      under a different symptom or a distinct bug; then apply the fix -- split the job into 5 per-asset_group Cloud Run
      executions/schedules (mirrors the existing manifest-consolidator per-AG pattern; preferred over merely bumping the
      memory limit since it also gives per-AG failure isolation, per the doc's own recommendation) or bump the memory
      limit if a per-AG split proves infeasible; redeploy. Source:
      `plans/active/issues/cf_manifest_audit_scheduled_job_daily_failure_2026_07_13.md`. Done when:
      `gs://cf-manifest-audit-central-element-323112/cf_audit/` shows a fresh dated output object for all 5 asset_groups
      (cefi/defi/tradfi/sports/prediction) from a real green run, cited with `Evidence: cloudbuild=<id>` or the
      equivalent Cloud Run execution-success reference, and the source issue doc's 3 "Next steps" todos are flipped
      checked.
- [ ] [DATA] P1. **Bring cefi's raw_tick_data manifest to CF-1/CF-4/CF-5/Era-B GREEN using the proven cross-AG
      playbook.** cefi is the one AG this doc's 2026-07-14 Adjudication explicitly leaves un-adjudicated (no fresh
      CF-audit found). First re-run `cf_manifest_audit.py` against the live `market-data-tick-cefi-prd` manifest to get
      a current baseline, then apply the same fixes already landed for prediction/sports/tradfi/defi: (1) **CF-1** —
      normalize the `_index`'s `schema_version` column from string `'9'` to int64 via
      `pd.to_numeric(df["schema_version"]).astype("int64")` (snapshot the `_index` parquet first); (2) **CF-4** —
      backfill the ~54% (3.9M-row) blank `source` column via `record_captured(source=...)`, deriving source from the
      `{mode}_{source}` pipeline_mode or the venue→source map; (3) **CF-5** — type the ~189,665 untyped-reason rows; (4)
      **Era-B** — reclassify the ~521,513 chain rows so `options_chain`/`futures_chain` write `data_type=trades` with
      the chain distinction carried in `instrument_type` (verify key-membership before relabeling, per the doc's
      "Recurring-bug playbook" item 6). Re-run the CF-audit after each fix to confirm GREEN. Repo:
      market-tick-data-service (manifest/data), unified-trading-library (writer + audit tooling). Source:
      `issues/cross_cutting_manifest_canonicalisation_findings_2026_07_11.md`. **Done when**: a fresh CF-audit Progress
      Log entry shows cefi's CF-1/CF-4/CF-5/Era-B GREEN (or an explicitly documented residual with root cause), reaching
      parity with prediction/sports/tradfi/defi's already-confirmed state.
- [x] ✅ [INFRA] P1. **DONE 2026-07-26 (slot-7) — all 3 items closed, evidence in the Progress Log below + the source
      issue doc (now `status: resolved`).** Close the 3 residual items on
      `datapoint_validation_results_bucket_missing_2026_07_21.md`: **(a)** verify or refute the suspected
      `alerting-service` sibling gap — check whether its declared bucket `kind:` row in `configs/cloud-providers.yaml`
      has a physically-provisioned GCS bucket (`gcloud storage buckets describe`); if confirmed missing, provision it
      (or file the provisioning as its own P1 issue doc) and consider a QG check pairing a new `kind:` row with
      bucket-existence verification. **(b)** Harden `deployment-service/scripts/vm/setup-data-pipeline-vm.sh`'s generic
      `elif [ -n "$VM_TASK" ]` fallback to fail loud/early on an unrecognized `VM_TASK` (this is the 3rd
      silent-fallthrough crash: 2026-07-12 sports-v9-migration, 2026-07-13 defi-paper, 2026-07-21 datapoint-validation)
      — detect `VM_BACKFILL_CMD` metadata present-but-unused and prefer it, or at minimum WARN loudly instead of
      crashing deep in a task-specific `--operation` argparse. **(c)** Check whether the concurrent Round-1
      `unified-api-contracts` writer-fix workflow (R3 cefi-v6 + UAC oracle candle-extension) has landed cleanly; once it
      has, republish the instruments-service code tarball
      (`bash scripts/vm/create-code-tarballs.sh --include instruments-service`, NOT `--allow-dirty-tarball`) and
      relaunch the cefi/defi/prediction `datapoint-validation-{ag}-*` VMs (tradfi/sports already ran to completion
      2026-07-21 and need no relaunch). Source: `issues/datapoint_validation_results_bucket_missing_2026_07_21.md`. Done
      when: (a) alerting-service bucket-provisioning status is confirmed one way or the other (with a follow-up issue
      doc filed if a gap is found), (b) the VM_TASK fallback change is committed + shipped, and (c) either the 3
      relaunched VMs (cefi/defi/prediction) reach a terminal RUNNING-to-completion state with day-frontier progressing
      in `run.log`, or the todo is left open with an explicit note that the Round-1 UAC workflow has not yet landed.

## Progress Log

- **2026-07-26 (slot-7) — DONE, all 3 items closed.** Worked the
  `datapoint_validation_results_bucket_missing_2026_07_21.md` 3-item close-out todo (source issue doc flipped to
  `status: resolved`, `resolved_by: deployment-service@b0e158d`, all 7 of its own todos now `[x]`).
  - **(a) DONE — sibling gap REFUTED.** `alerting-service`'s bucket kind (`configs/cloud-providers.yaml` line 194,
    `alerting-service-${GCP_PROJECT_ID}`) resolves to `gs://alerting-service-central-element-323112`, which
    `gcloud storage buckets describe` confirms EXISTS (location ASIA-NORTHEAST1) and is actively written to (`_index/`,
    `alerting/` prefixes present). No provisioning gap — no follow-up issue doc needed.
  - **(b) DONE + shipped.** Added a guard at the top of `setup-data-pipeline-vm.sh`'s generic `elif [ -n "$VM_TASK" ]`
    fallback: if `VM_BACKFILL_CMD` instance metadata is present (which, by construction, only happens when a launcher
    expected a dedicated dispatch branch that doesn't exist), it now fails LOUD + immediately with a diagnostic naming
    the missing branch and the exact fix, instead of silently building an unrelated `--operation` CLI call that crashes
    minutes later deep in a different service's argparse (the same bug class hit 3 times: 2026-07-12
    sports-v9-migration, 2026-07-13 defi-paper, 2026-07-21 datapoint-validation). `deployment-service@b0e158d`
    (`bash -n` + `shellcheck -S error` clean, full `quality-gates.sh` green, sentinel `d6576d4`). Shipped via
    quickmerge.
  - **(c) DONE.** Confirmed the Round-1 blocker cleared: both named UAC commits are ancestors of the current
    `unified-api-contracts` HEAD — `9a92cf4f` (R3 cefi-v6 chain-tail canonicalisation) and `6329fc04` (oracle
    `processed_candles/` extension) — and UAC/instruments-service/UTL are all clean (no dirty WIP). Republished the
    instruments-service tarball on the clean tree (`instruments-service-code@4d6c2109be9a`, uploaded 2026-07-26T20:58
    UTC — this needed (b) shipped FIRST since `create-code-tarballs.sh` also bundles deployment-service itself and
    hard-blocks on ANY dirty repo in its set, not just the `--include` target). Checked the prior 2026-07-22 relaunch's
    `run.log`s (cefi/defi/prediction) before relaunching: all three end mid-stream with no termination marker (classic
    SPOT-preemption signature, not genuine completion) — cefi reached day 2021-02-05 (178k rows validated) after a ~16h
    run, defi reached day 2021-06-26 (60.5k rows), prediction reached day 2025-01-04 (644k rows) — real forward
    progress, just interrupted, and safe to resume via the launcher's presence-skip idempotency. **Relaunched all 3 at
    2026-07-26 21:00-21:01 UTC**: `datapoint-validation-cefi-20260726-210047`,
    `datapoint-validation-defi-20260726-210104`, `datapoint-validation-prediction-20260726-210124` (all confirmed
    RUNNING, SPOT, e2-standard-4, zone asia-northeast1-c). **T+10min watchdog verified (2026-07-26 21:10-21:11 UTC)**:
    all 3 still RUNNING with active day-frontier advancement in `run.log` — cefi → 2020-01-02 (2000 validated), defi →
    2020-10-07 (5889 validated), prediction → 2021-10-02 (5313 validated). No fire-and-forget; genuine forward progress
    confirmed, matching the same bar todo 2 in the source issue doc was accepted against (tradfi/sports). SPOT
    preemption is expected/acceptable (idempotent, safe to just relaunch the same asset_group again, which will resume
    via presence-skip). Once confirmed, flip this todo's checkbox with the day-frontier evidence.

## Deferred — conflict-gated (genuinely unresolved, do not draft competing todos)

- **`plans/active/bucket_fold_execution_strategy_2026_07_17.md`**: Not a genuine conflict needing operator arbitration —
  it resolves by evidence, but not cleanly enough to draft a new todo either, so this is best flagged as a doc-hygiene /
  stale-citation issue rather than left silently batchable or silently dropped. Re-reading the target doc's 3
  Phase-1-flagged uncovered items...
- **`plans/active/data_pipeline_reconciliation_skill_2026_07_20.md`**: Read the doc's "Deferred work after 2026-07-21"
  table (line 825) and traced each of the 8 listed items against the current corpus state — every one is either already
  resolved/stale, or already actively claimed by an AG-specific (not cross-cutting) dispatch track, so none survives as
  genuinely-uncovered cross-cutting...
- **`plans/active/issues/blocking_gcs_writes_on_event_loop_cross_asset_group_2026_07_18.md`**: GENUINE overlap found,
  not a clean duplicate. `plans/active/defi_satellite_ao_dispatch_batch2_2026_07_26.md` (already-active, [SCRIPT] P1
  'MTDS DeFi perf bundle') dispatches a concurrency+blocking-write fix that partially covers this doc's Open items 1 and
  2, but via a DIFFERENT mechanism and for only a SUBSET of the...
- **`plans/active/issues/manifest_reprocessing_generic_utility_2026_07_07.md`**: Not actually orphaned — the Phase-1
  "zero hits" grep was a false negative caused by a stray space in the covering plan's own citation.
  `plans/active/cross_cutting_consolidated_closeout_2026_07_25.md` Track 14 ("Scheduled-job reliability +
  concurrency/OOM defects + manifest reprocessing tooling") lists this exact doc...

## Deferred — operator decision needed (BLOCKED-OPERATOR-DECISION, not batchable)

- **`plans/active/bigquery_feature_ml_compute_engine_option_2026_06_08.md`**: No conflict:
  cross_cutting_consolidated_closeout_2026_07_25.md Track 10 only passively cites this doc ("Sources (pipeline)")
  without dispatching any todo against it, and no other AG satellite batch or the ao/ci/infra closeout docs reference
  `bigquery_feature_ml_compute_engine_option_2026_06_08.md`,...
- **`plans/active/bucket_fold_portfolio_state_2026_07_17.md`**: Read the target doc and confirmed the Phase-1 evidence,
  but the conflict check overturns 2 of the 3 "uncovered" items as stale/already-done, and the 3rd is a genuine
  operator/dependency gate — so nothing is batchable. (1) "Provision + yaml/registry scaffold" (line 107) —
  DUPLICATE/STALE. The doc's own Cutover todo...
- **`plans/active/features_service_e2e_pipeline_test_2026_05_26.md`**: Confirmed Phase-1 evidence: the doc carries an
  unresolved "Open Track-1 todos" section (7 unchecked items: Phase A features-onchain staked-basis e2e
  dry-run+IS_TEST_RUN validation, Phase B CeFi MDPS top-up + delta_one funding_oi/realized_vol, Drift/Orca DeFi coverage
  confirm, Phase C strategy read-back, perf...
- **`plans/active/infra_capture_and_devops_leftovers_2026_07_06.md`**: Confirmed via full read: exactly 4 open items
  remain, matching Phase-1 evidence precisely, and all 4 are explicitly and currently BLOCKED on operator action with no
  AO-executable path: (1) ASTER live-VM launch — BLOCKED-OPERATOR-DECISION on `BLK-4f52080e` (2026-07-25 ruling: HOLD,
  do not launch, pending the operator's...
- **`plans/active/is_catalogue_g1_root_audit_log_2026_07_24.md`**: Read the full doc and confirmed the Phase-1 evidence,
  then ran the conflict check before drafting anything, which changed the verdict. Per-item disposition of the doc's
  "genuinely open" G1 lifecycle items: 1. **G1.code / G1.dry-run "defi pending"** — this line is STALE inside the doc
  itself....
- **`plans/active/issues/backfill_vm_slack_alert_e2e_verification_2026_06_23.md`**: All 4 open todos in this doc turn
  out to be provably superseded/duplicate once checked against the broader active-plan corpus (not just the
  cross-cutting closeout's own reference list, which is what Phase 1 correctly flagged as insufficient evidence on its
  own): - Gap 1 (P0 redeploy deployment-api heartbeat-watcher):...
- **`plans/active/issues/fleet_audit_triad_deferred_followups_2026_06_01.md`**: Two layers block a candidate todo here.
  (1) CONFLICT — 2 of the 7 open items are stale/duplicate, not actually orphaned: (a) the P2 "log-archive crons never
  tofu apply'd" item is FALSE as of today — `plans/active/infra_capture_and_devops_leftovers_2026_07_06.md` (status:
  active) has this checked ✅ DONE 2026-07-07:...
- **`plans/active/issues/honest_coverage_rollup_scoped_rerun_masks_distinct_values_2026_07_25.md`**: Conflict check: no
  genuine overlap found. The one coverage.json hit in the cross-cutting covering set
  (`cross_cutting_consolidated_closeout_2026_07_25.md` Track 21, citing
  `issues/honest_coverage_nightly_cron_undersized_and_launcher_ssot_drift_2026_07_16.md`) is a DIFFERENT bug with a
  different fix target — that doc...
- **`plans/active/issues/instruments_service_plan_reconciliation_2026_06_29.md`**: Conflict check: grepped
  plans/active/cross_cutting_consolidated_closeout_2026_07_25.md — it cites this doc only under Track 7 ("Sources") and
  its own stated "close-out criterion" for Track 7 is passive ("both reconciliation docs unlock once their few remaining
  items resolve"), explicitly naming the SAME remainders (C5...
- **`plans/active/issues/recon_bucket_missing_nightly_recon_failing_2026_07_13.md`**: No genuine conflict found. Grep of
  cross_cutting_consolidated_closeout_2026_07_25.md's own Track 13 confirms it already cites this exact doc and
  explicitly states the remaining work "needs NEW multi-repo feature work across 4 services and is explicitly NOT
  AO-eligible as-is — needs an operator ASK for a...
- **`plans/active/issues/silent_wrong_answer_bucket_resolution_class_2026_07_20.md`**: Confirmed via full read: §6
  "Open" carries exactly two unresolved items, both of which resolve to gates rather than a fresh batchable todo. (1)
  Stray empty bucket `market-data-tick-prediction-test-{pid}` (0 objects, created by the string-mangling smoke harness
  that instance #5 documents). The doc's own text is...
- **`plans/active/issues/wsfeedconnector_phase35_gap_2026_07_06.md`**: Confirmed via direct read: the doc's sole open
  checkbox is the ICE WSFeedConnector build item (P1, CODE) - Databento supports ICE datasets but is BLOCKED-CREDENTIALS
  on the Real-Time key per the Databento connector docstring; once the credential arrives, ICE gets wired under the
  existing databento_tradfi_ws.py factory...
- **`plans/active/mtds_file_size_refactor_2026_06_08.md`**: Confirmed Phase-1 evidence by full read: doc is
  `status: paused`, carries a top-of-doc "⏸️ DEFERRED 2026-06-26 (operator) — non-essential, parked" banner, and an
  explicit in-body gate — "GATED: do NOT start until the per-AG data migrations (`--apply`) are complete" — because
  touching...

## Deferred — time-gated (re-check on the next batch iteration)

- **`plans/active/issues/manifest_v6_batch3_residual_orphaned_work_2026_07_21.md`**: No genuine conflict found, and
  nothing is stealthily duplicating this doc's ground — but the doc's two remaining open todos ((1) deployment-api
  data-status API: add quote_asset/margin_type for cefi chain shards; (2) deployment-ui heatmap: filterable by those
  dims) are both explicitly `gate_on_depends: true`-blocked on...
- **`plans/active/issues/pipeline_smoke_sweep_findings_2026_07_20.md`**: Confirmed the target doc's "## 4. Still open"
  section verbatim (3 items). All three resolve without a new cross-cutting todo: (1) "prediction cannot be smoked until
  its bucket resolution is fixed (dedicated `pred` flat kind)" — DUPLICATE/STALE. This is the same BucketNamingError
  class already root-caused and fixed in...
