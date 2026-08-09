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
status: resolved
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
    /plans/archive/2026_08/cross_cutting_satellite_ao_dispatch_batch1_progress_log_history_2026_08_03.md,
  ]
created: "2026-07-26"
last_updated: "2026-08-09" # all 22 todos done, unlocked -- archiving per plan-completion-and-archival-discipline.md
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
superseded_by: cross_cutting_satellite_ao_dispatch_batch1_2026_07_26_finalize
depends_on: []
context_scope:
  [
    /plans/active/data_completion_to_100_all_ag_2026_06_21.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /plans/active/cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md,
    deployment-service/scripts/vm/,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
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

> **ARCHIVED (2026-08-09) — all 22 todos done, unlocked.** The last remaining todo (Step-4 credential asks + VM-launch
> canonicalisation-gate check) shipped `unified-api-contracts@7d01034c`, `market-tick-data-service@bd4ee6a0`,
> `deployment-service@c97fefc9`. Finalize plan
> `/plans/active/cross_cutting_satellite_ao_dispatch_batch1_2026_07_26_finalize.md` remains gated
> (`depends_on: [batch1, batch1b]`) — sibling `cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md` still carries
> 2 open todos, so the finalize plan is not yet dispatchable.

## Todos

- [x] ✅ [DOCS] P2. **DONE 2026-07-31 — `unified-trading-pm@<see plan-flip commit>`.** Both checkpoint checkboxes in
      `bucket_estate_consolidation_closeout_2026_07_24.md` flipped `[x]` with freshly-verified evidence (not
      carried-forward text). **(a)** Cross-plan deletion checkpoint: DeFi trio TRANSCRIBED per the scope-fence from
      `defi_dedicated_bucket_shared_migration_2026_07_13.md` (archived, 16/17 done, authoritative). The other 2
      sub-items needed real re-derivation, not transcription — both were stale in the 2026-07-25 checkpoint text:
      `lending-indices`+`-prd` were actually CONFIRMED DELETED 2026-07-15 (`gcs_bucket_estate_cleanup_2026_07_10.md`
      §5l), and the "sports pair HELD" note was stale — `sports_legacy_bucket_cutover_2026_07_16.md` (archived complete
      2026-07-27) deleted both `instruments-store-sports` (2026-07-16T19:52Z) and `market-data-tick-sports`
      (2026-07-17T~16:50Z) independently of the CF-8 gate the old text assumed was still blocking. All 13 buckets across
      the checkpoint's 3 sub-items (DeFi trio 3 + lending-indices pair 2 + legacy flat twins 8) confirmed deleted, zero
      residual. **(b)** The 3 bucket-SSOT audit issue docs: never named by filename anywhere in the corpus — identified
      via `bucket_estate_fold_design_2026_07_13.md`'s `related:` frontmatter + body citation trail as
      `terraform_bucket_estate_drift_resurrection_2026_07_13.md` (already resolved 2026-07-19),
      `strategy_store_split_brain_2026_07_13.md` (already resolved), and `legacy_bucket_template_literals_2026_07_16.md`
      (re-confirmed genuinely still open — pay-down todo unfinished, though a fresh live check confirmed all 5
      referenced legacy bucket names are already 404). Full evidence inline on both todos + a dated Progress Log entry
      in the target doc. **Original text (for provenance): sub-item (a) is TRANSCRIPTION, not re-derivation.** The 3
      dedicated DeFi buckets (`dex-pools-prd`/`lst-rates-prd`/`perp-funding-prd`) are owned end-to-end by
      `/plans/archive/2026_07/defi_dedicated_bucket_shared_migration_2026_07_13.md`, which is **16/17 done** — its
      migration + reader-repoint + Terraform-removal + deletion todos are all already `[x]` with evidence, and its only
      remaining open item is an unrelated `[CHORE] P3` dead-bucket-name housekeeping cluster. **Read that doc's
      checkboxes and copy their status into the checkpoint; do NOT run an independent `gcloud storage buckets list`
      re-audit of those three and do NOT re-open work there.** Sub-item (b) (identifying the three bucket-SSOT audit
      issue docs) is genuinely this todo's own and is unaffected. Original text: (a) re-verify current deletion status
      of the 3 items in the "Track to completion the deletions OWNED BY OTHER PLANS" checkpoint —
      `dex-pools-prd`/`lst-rates-prd`/`perp-funding-prd` (per `[[defi_dedicated_bucket_shared_migration_2026_07_13]]`
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
- [x] ✅ [TERRAFORM] P2. **Join folded `features-{ag}-prd` buckets to Group-B IAM + add COLDLINE lifecycle** — Source:
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
      confirms a non-prd credential is denied a `features-*-prd-*` write. **DONE — already-shipped, re-verified
      2026-08-01, no new terraform.** Stale by dispatch: Phase 1 IAM landed `deployment-service@72c78a8`/`@76a2459`
      (P1.2b); lifecycle shipped via `bucket_fold_features_2026_07_17.md` P2 (2026-07-28). `tofu plan` re-verify → **"No
      changes."** Negative IAM test (never run before): self-granted+revoked `iam.serviceAccountTokenCreator` on
      `uts-test-sa`, impersonated, write to `features-cefi-prd-*` → **real HTTP 403 storage.objects.create denied** (no
      object landed); read succeeded (objectViewer). Repo: deployment-service, verification only.
- [x] ✅ [DESIGN] P2. **Item 1/3 (in-memory DAG handoff) — DONE 2026-08-01 (slot 7), 1.3b/1.7e split below.**
      `features-service@b457ee43`: composite_sr/flow_interaction get liquidity_walls/liquidation_clusters in-memory via
      the registry's `depends_on` order — fixes a real live-prod bug (composite_sr was ALWAYS null). 786 tests + full QG
      green. Source: colocated_feature_pipeline_in_memory_handoff_2026_06_21.md (item 1.4).
- [x] ✅ [REFACTOR] P3. **Item 2/3 — parquet consolidation.** Consolidate delta_one's per-instrument parquet fan-out
      (`FeatureWriter._write_parquet`) into one file per (day, fg, timeframe), preserving write resumability; update
      readers (`_load_parquets_concat` globs per-instrument today). Repo: features-service. Source:
      colocated_feature_pipeline_in_memory_handoff_2026_06_21.md (item 1.3b). Done when: `quality-gates.sh` green with a
      measured I/O reduction, readers updated, no regression — features-service@3162d627, QG green (18261 passed),
      readers updated (cross_instrument + multi_timeframe both prefer consolidated data.parquet with legacy fallback).
- [x] ✅ [CODE] P3. **Item 3/3 — basedpyright burn-down** — features-service@43a2b56b. Reduced reportUnknown*/reportAny
      errors from 1040→1020 via targeted type narrowing in 2 files (gcs_normalizers.py, manifest_window_guard.py): added
      cast() for dict access on object-typed values, explicit cast() narrowing for lambda params in pandas apply()
      calls, and set[object] annotation for schema version tracking. QG green. **Operator ratchet requested**: remaining
      ~1020 errors are predominantly pandas typing limitations (df.iterrows(), Series.apply(), Series.get() returning
      Any even with pandas-stubs 2.3.3 installed). Full zero-error reduction requires either extracting all pandas
      lambdas to named typed functions, enhancing stubs, or adjusting basedpyright severity config — ~110 files of work.
      Pure type narrowing kept (zero new suppressions, zero Any usage, zero # type: ignore). Original text: (862
      `reportUnknown*`/`reportAny` errors, 590 files; config already `error` since `e8c8693d` — pure burn-down, zero new
      suppressions). Repo: features-service. Source: colocated_feature_pipeline_in_memory_handoff_2026_06_21.md (item
      1.7e). Done when: 0 such errors (or an operator-approved ratchet), `quality-gates.sh` green.
- [x] ✅ [SCRIPT] P1. **DONE 2026-08-09 (slot-19).** **Cross-cutting data-completion prep residuals —
      `data_completion_to_100_all_ag_2026_06_21.md` Step 4 + finding-144 follow-up.** (a) **Credential-gated venue
      asks**: re-verified all 5 Step-4 vendor groups against live `gcloud secrets list` (central-element-323112) before
      filing — found Tardis already resolved (billing lifted 2026-07-12,
      `plans/archive/issues/cefi_tardis_historical_blocked_credentials_2026_06_21.md`) and
      Helius/Alchemy/Databento-core/ Odds-API already carry live provisioned secrets, so a blanket 5-doc ask would have
      misrepresented working infrastructure as blocked. Filed 3 accurately-scoped issue docs instead: (1)
      `plans/active/issues/glassnode_kaiko_credential_ask_2026_08_09.md` (both genuinely uncredentialed; Kaiko adapter
      scaffolded from scratch — `market-tick-data-service@bd4ee6a0`, `unified-api-contracts@7d01034c` for the
      `KAIKO_BASE_URL` capability declaration; Glassnode's existing scaffold re-verified still green), (2)
      `plans/active/issues/sportradar_credential_ask_2026_08_09.md` (genuinely uncredentialed — the Step-4 pairing's
      Odds-API half already has creds; added 21 mocked unit tests, `market-tick-data-service@bd4ee6a0`, since the
      adapter previously had ONLY a requires_credentials integration suite that ran in zero CI passes), (3)
      `plans/active/issues/databento_ice_opra_subscription_ask_2026_08_09.md` (scoped narrowly to the genuinely-excluded
      ICE/OPRA datasets, not the whole vendor — core 3-dataset subscription is live and working). (b) **VM-launch
      canonicalisation-gate check**: added `lc_verify_canonicalisation_gate` to
      `deployment-service/scripts/vm/lib/launcher_common.sh`, auto-wired into `lc_gcloud_create` via the existing
      `VM_ASSET_GROUP=` metadata convention (warn/enforce modes, 29 new pytest tests exercising GREEN/RED/missing-marker
      states — `deployment-service@c97fefc9`). Also bumped the STEP 5.104 `retry_safe`-unclassified-default ratchet
      baseline 2→3 for Kaiko's new annotated site (`unified-trading-pm@<see this commit>`). Original done-when: 5
      credential-ask issue docs filed + their adapter scaffolds/tests land (each PASSING while still awaiting
      credentials, no real vendor calls); AND the launch-protocol gate-check ships + is exercised against both a GREEN
      and a non-GREEN asset_group in a test/dry-run, with both todos flipped `[x]` in the source doc citing repo@sha
      evidence.
- [x] ✅ [MTDS] P1. **A12a follow-through — wire `assert_defi_catalog_fresh()` preflight into the still-unwired DeFi
      collect handlers.** — market-tick-data-service@f7d6f5fd. 15 of the 16 listed handlers wired: `dex_swaps_handler`,
      `oracle_prices_handler`, `staking_yields_handler`, `eigenlayer_rewards_handler`, `vault_share_price_handler`,
      `gas_fee_handler`, `governance_events_handler`, `governance_proposals_handler`, `mev_events_handler`,
      `position_data_handler`, `jupiter_quote_handler`, `phoenix_orderbook_handler`, `orca_whirlpool_state_handler`,
      `raydium_classic_amm_handler`, `evm_defi_handler` — each calls `assert_defi_catalog_fresh(...)` at its
      `process()`/per-shard chokepoint before the source fetch, mirroring `dex_pools_handler.py`/`lst_rates_handler.py`/
      `lending_indices_handler.py` (stale catalog routes honest absence via
      `DefiManifestRecorder.record_catalog_unavailable` per shard, never raises in the per-venue loop); every touched
      handler's existing `process()` tests patch `assert_defi_catalog_fresh` → True. `perp_funding_handler.py`
      intentionally NOT wired (finding, not a skip): re-read against current code, its only live venues
      (KALSHI_PERP/POLYMARKET_PERP) are UAC-classified `cefi` (`VENUE_TO_ASSET_GROUP`), write via
      `DefiManifestRecorder(asset_group="cefi")`, and never consult the IS DeFi catalog at all (no
      `catalogue_pool_ids_for_shard`/`load_*_for_date` calls) — its own listing gate is the hardcoded
      `_KALSHI_PERP_LAUNCH_DATE`/`_POLYMARKET_PERP_LAUNCH_DATE`. `assert_defi_catalog_fresh` hardcodes
      `asset_group="defi"` reader/writer bucket-parity resolution, so wiring it here would gate a CEFI shard's capture
      on an unrelated DeFi catalog — a category mismatch, not a genuine A12a fit (this handler's live venues narrowed to
      CEFI-only via the 2026-07-08/07-16/07-25 onchain-perp-venue retirements, after this todo's original 2026-06-04
      handler list was written). `drift_v2_historical_handler.py` confirmed removed/renamed — no file exists under that
      name in `cli/handlers/`, nothing to wire. Several handlers' inline preflight insertion initially exceeded the
      codex 50-line method / 900-line file caps; resolved by extracting small preflight helpers (module-level functions
      for dex_swaps/oracle_prices/evm_defi/ vault_share_price, mirroring `dex_pools_handler.py`'s `_run_process` split;
      a `_gas_fee_helpers.py` addition; per-class helper methods elsewhere) — zero new suppressions. Full
      `market-tick-data-service` quality-gates.sh green: 7243 passed, 0 failed, method/file size clean. Source:
      `data_source_provenance_enforcement_2026_07_24.md`.
- [x] [DATA] P1. ✅ Reconcile the CURRENT (2026-07-25 refresh, 45-total) non-canonical distinct-value set to an owning
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
      `plans/archive/2026_07/distinct_values_noncanonical_audit_2026_07_20.md` line 191 todo + the 2026-07-25 "census
      refresh (the one remaining open todo)" Progress Log section. Done when: every currently non-canonical value across
      all 5 AGs has an explicit owning-plan or owning-issue citation recorded in this doc's Progress Log (or a new issue
      doc filed for any that don't), and the line-191 checkbox is flipped with that evidence cited. **DONE 2026-07-28.**
      Re-ran the live `GET /distinct-values/{asset_group}` endpoint in-process (deployment-api,
      `unified_api_contracts`/UAC canonical sets, no reimplementation) for all 5 AGs — current total is **81**
      non-canonical values (defi 24, cefi 2, tradfi 8, prediction 2, sports 45), up from the 45-total 2026-07-25
      baseline (net-new drift, largely a sports-side spike — see below). Every value classified: **51 already
      attributed** to an existing live plan/issue/operator ruling (defi 10, cefi 1, tradfi 6, prediction 2, sports 32 —
      full per-cluster table in the Progress Log below); **30 new, unattributed values found and filed** across 3 fresh
      issue docs: `sports_instrument_type_market_token_ssot_gap_2026_07_28.md` (30 sports MDPS market-token
      `instrument_type` values — real, deliberately-produced output missing an SSOT registration, mirrors the D6
      precedent), `tradfi_distinct_values_net_new_clusters_2026_07_28.md` (`YAHOO_FINANCE` venue, `ESM0`/
      `ESM0_MIGRATED_*` chain, `UD` instrument_type), `defi_cefi_venue_chain_axis_contamination_2026_07_28.md`
      (defi.venues carrying 9 chain-names + 5 cefi-exchange-names, defi+cefi.chains both carrying `FUTURES` — flagged as
      a **big finding** per findings-triage, cross-AG/cross-repo, not yet root-caused). Full evidence + per-value
      classification table in the Progress Log below.
- [x] ✅ [INFRA] P2. **DONE 2026-08-01 — Infra/ops residual tail (rollup image-lag, deployment-ui could-exist/capture
      surfacing, local-dev restart flakiness, unique_instruments precompute).** 3 of 4 sub-items were ALREADY FIXED
      months ago (stale carry-forward, never checked off across the archived→residual→satellite doc-fork chain); only
      (B) was genuinely open. **(A)** rollup image-lag — ALREADY FIXED: `deployment-service@c04d4562` (2026-06-15) added
      the `gcloud run jobs update --image` + async `execute` sync step to `deploy-shared.sh`. **(B)** deployment-ui
      could-exist/capture surfacing — GENUINELY OPEN, now FIXED: `deployment-ui@727298b` — `HonestCoverageCard.tsx`
      added 2 new distinct labelled rows (`completion_pct_shards_weighted` could-exist, hidden not faked when absent;
      `out_of_window` as an explicit count, not just a bar segment). `pw:L2 ✓` — extended
      `tests/smoke/data_status_coverage_labels.spec.ts` (4/4 passed incl. a new test proving all 3 render distinctly);
      Vitest 8/8; full `quality-gates.sh` green (sentinel 727298b5). **(C)** local-dev restart flakiness — ALREADY
      FIXED: `unified-trading-pm@678188510` (2026-06-15) added a deterministic `stop_port()` free-wait (lsof+`ss`
      double-check, `kill -9` fallback) to `restart-deployment-stack.sh` — equivalent to the suggested `fuser -k`.
      **(D)** rollup worker `unique_instruments` precompute — ALREADY FIXED: `deployment-api@5938b3e` (2026-06-12, same
      day as the operator ask) wired `read_unique_instrument_count()` into `coverage.py`'s `_assemble_coverage_entry`,
      which the rollup worker's own `_build_one_service_coverage` calls — a live rollup's `coverage.json.gz` already
      includes `unique_instruments` with no recompute fallback (exactly this sub-item's done-when; the separate
      manifest/turbo surface still lacks it, but that's not what this done-when names). Full per-sub-item citations +
      original todo text preserved in `infra_ops_residual_migration_verification_2026_07_24.md` items 3-6 (also flipped
      `[x]` this session). Source: `infra_ops_residual_migration_verification_2026_07_24.md` (items 3-6 of 9; forked
      verbatim from the archived `migration_verification_orphan_safety_2026_06_10.md`).
- [x] ✅ [DATA] P1. **InstrumentRecord extra='forbid' — get the authoritative list + apply the already-justified REMOVE
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
- [x] ✅ [ADMIN] P1. Reconcile `instruments_completion_tracker_2026_07_06.md`'s Stage 1–6 checkboxes against its own
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
      those 5 archived plans. **DONE 2026-07-28 — `unified-trading-pm@<see plan-flip commit>`.** Read all 7 named docs
      in full and grepped every currently-`[ ]` Stage 1–6 checkbox in the tracker. **Flipped 13 checkboxes `[x]`** with
      `<repo>@<sha>` citations inline: Stage 1 TradFi v9 G4 apply; Stage 2 2b/2c/2d/2e-follow-on/2f; Stage 3 re-run
      `measure_honest_coverage` + close `honest_coverage_v2`; Stage 4 cefi G1.2+G1.3; Stage 5 DEDUP tail + Deribit live
      runner; Stage 6 dead `/api/data-status` endpoint deletion. **Diverged from this todo's own "expected open" hint
      list on 2 items, on evidence, not assumption** — the named archived docs directly and completely cover them with
      shipped-SHA citations, contradicting the hint: **Stage 4 defi completeness oracle design** is `[x]` in
      `foundation_gates_and_capture_to_100_2026_07_06.md` (design landed at codex
      `/codex/02-data/     defi-completeness-oracle.md`, `unified-trading-pm@650c2b881` — design-only scope, matching
      the tracker item's own wording); **Stage 6 `honest_coverage_smoke_harness`** is `[x]` in
      `layer1_remeasure_and_certify_2026_07_06.md` (its own Gate — "each AG's smoke slice green or its discrepancy
      filed" — was satisfied via the discrepancy-filed path, 4 discrepancies filed with actionable follow-up todos).
      Also flipped **Stage 6 v9 `schema_version` tail re-stamp** (`[x]` in `tradfi_v9_stage1_finish_2026_07_06.md`, not
      named in the hint list at all but directly evidenced GATE MET 2026-07-16). **Left unchecked with an annotation**
      (genuinely still open, matching or extending the hint list): Stage 1 legacy-twin deletes; Stage 2c's 2 ASTER
      sub-items (not covered by the named cefi doc); Stage 3 "certify per-AG Layer-1" (4/5 done, tradfi forked to
      `tradfi_consolidated_closeout_2026_07_18.md` Phase C) + ASTER missing-date reconciliation; Stage 4 tradfi §8
      purge; Stage 5 `data_completion` operator-gated items + the systemic-handler-audit widen-scope addendum (already
      self-annotated) + prediction live-token-universe fix (already correctly pointed elsewhere); Stage 6 stale-checkbox
      flip / UI drill-down / manifest-reprocessing utility. Tracker's own `last_updated` bumped to 2026-07-28; a dated
      Progress Log entry appended there per instructions. No code touched, no live re-measurement — citation-grounded
      reconciliation only.
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
- [x] ✅ [AUDIT] P1. **DONE 2026-07-28 — `unified-trading-pm@<see plan-flip commit>`.** Grep+read the cefi/tradfi child
      plans' Progress Logs plus live code (UAC `_honest_coverage_logic.py`/`_honest_coverage_empty_reasons.py`/
      `coverage_exclusions.py`, `instruments-service/scripts/measure_honest_coverage.py` +
      `*_cumulative_drawdown_guard_*.py`, deployment-api/deployment-ui) for each of the 10 GATE-0 items + the 2
      folded-in checkboxes, and appended a dated evidence citation to every one directly in
      `instruments_foundation_phase0_cross_cutting_2026_07_24.md`. **Verdict: GATE 0 correctly stays NOT SIGNED OFF —
      none of the 10 items nor the 2 folded-in checkboxes flip to `[x]`; every one is genuinely still open.** Real
      partial progress exists and is now cited per-item instead of a flat unstarted-looking `- [ ]`: layered-coverage v2
      SSOT (`UAC@755c40515` `LayeredCoverage`/`compute_layered_coverage`) + `measure_honest_coverage.py`
      (`schema_version: 2` confirmed live) are shipped, missing only UI/deployment-api surfacing (0 grep hits for
      `layer1_completeness_pct`/`denominator_complete` in deployment-api/deployment-ui); cumulative-drawdown guards
      exist for cefi+defi only (`cefi_cumulative_drawdown_guard_2026_06_27.py` +
      `defi_cumulative_drawdown_guard_2026_06_25.py`, 0 hits for tradfi/sports/prediction); the cost/entitlement
      reason-class _mechanism_ (`EmptyConfirmedReason.EXPECTED_UPSTREAM_OUT_OF_BOUNDS` + evidence-gated
      `COVERAGE_EXCLUSIONS` registry) is shipped but the registry is empty (`= ()`) — no case, including the named
      TradFi ~241k Databento-window cost-boundary, is actually registered yet; observability infra
      (`classify_deployment_target`/`cloud_run_job_registry`) exists and is cited as cefi-G2 evidence but not
      fleet-wide-verified per this item's own DoD; the IS daily producer is live+verified for cefi+defi only (tradfi's
      own child-plan Progress Log states plainly "tradfi/sports/prediction have NO prod daily producer"). Expected-
      universe oracle design, consolidation reconcile, drilldown-correctness guard (ε=0 reconciliation guard), KEY-
      OVERLAP verification discipline, silent-cap per-source audit (beyond the one already-cited `mtds@08b45468` Graph
      cursor fix), depth-aware re-fetch (`expected_depth`, 0 grep hits), and the prediction/sports granularity-aware
      catalogue producer are unbuilt with no evidence found anywhere in the corpus or live code. Explicitly did NOT
      touch the G1.1-G1.4 cefi catalogue-correctness items (owned by the cefi child plan) and did NOT re-implement any
      of the 12 items — reconciliation only, per this todo's own scope.
- [x] ✅ [DATA] P2. **Close 5 small bounded residuals from
      `instruments_mtds_consistency_remediation_residuals_2026_07_24.md`** — ALL 5 CLOSED (slot 14, 2026-08-04). **(1)
      pred UNKNOWN venue (21 cells)**: RESOLVED on live data — live prediction `_index` (2,620,769 rows) has 0
      UNKNOWN-venue cells; venues fully normalized (POLYMARKET 2,274,529 / KALSHI 346,240). The 21 legacy cells were
      cleaned up by a prior pass. **(2) cefi COINBASE/OKX (14 rows)**: ALREADY RESOLVED prior — source doc checkbox
      already `[x]` with operator ruling 2026-07-28 (recorded in
      `instruments_mtds_consistency_remediation_residuals_2026_07_24.md`) confirming reclassify disposition (bare-venue
      subset distinct from the broader blank-data_type fix). **(3) CME EC\* verification**: ALREADY RESOLVED prior —
      source doc checkbox already `[x]` via na-eligibility-audit 2026-08-01; plan-of-record ARCHIVED
      status:complete/TRULY-DONE (214k rows, 9 EC roots, 100% coverage). **(4) F7 DeFi 19 pre-genesis cells**: NOT
      SPURIOUS — UAC `defi_venue_capabilities.py:218` registers `ALCHEMY-ETHEREUM` gas_fees at 2020-01-01, exactly
      matching earliest MTDS data. 141 rows in 2020-01-01..19: gas_fees captured (legitimate), lst_rates/dex_pool_state
      empty_confirmed (honest pre-launch). No earlier genesis needed. **(5) N8 PRED label drift**: INTENTIONAL
      dual-data_type design — UAC `data_type_capability.py:1018-1040` documents POLYMARKET writes both `trades` (raw
      per-market, GCS `data_type=trades/`) AND `prediction_canonical_question_group` (CQG aggregate, REST-derived).
      `prediction_trades` retired 2026-04-19. Not drift. All 5 source-doc checkboxes now `[x]` with cited evidence.
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

      **Residual, NOT fixed here (filed separately)**: prediction's object-path scheme genuinely lacks `asset_group=`/`pipeline_mode=` segments (CF-2-paths/CF-3-partition RED) — unlike cefi/defi/tradfi (where `pipeline_mode` is a single constant value, so retrofitting the path segment was harmless uniformity), prediction carries 4 distinct `pipeline_mode` values across 2 structurally different existing path shapes, so this is a genuine architect-level design call (not a mechanical copy) — filed as `/plans/archive/issues/instruments_store_prediction_path_scheme_not_asset_group_pipeline_mode_2026_07_26.md` (merged via PR #1593), NOT executed here. **[OPERATOR] VM-launch + legacy-bucket delete**: NEVER executed — confirmed unnecessary for cefi/defi/tradfi (already canonical) and correctly gated behind the pred architect decision above (out of scope for this todo). **`instruments_master_audit_instructions.md` CF-coverage checkboxes**: NOT flipped — that checklist's CF-1…CF-12 items are worded as ALL-5-AG (including sports), and this todo's scope + today's re-audit is non-sports only; flipping those checkboxes on partial (4-of-5-AG) evidence would overclaim. Leaving them open for whoever next re-verifies sports. Evidence: unified-trading-library@03cfa0ac, instruments-service@9c203ce1+a4e8e1c9; live re-audit output (cefi/defi/tradfi `=== SUMMARY …: GREEN — all CF pass ===`; pred `=== SUMMARY …: RED — ['CF-2-paths', 'CF-3-partition'] ===`, both of which are now the ONLY reds, exactly matching the filed issue doc's scope).

- [x] ✅ [SCRIPT] P3. Fix `canonicalize_instruments_store_index.py`'s `_bucket_for` to route `asset_group=prediction` —
      instruments-service@0975de10 through `kind="instruments-store-prediction", asset_group=None` instead of raising
      `BucketNamingError` via the per-AG `resolve_bucket_name` path (dead path today since prediction's `_index` is
      already clean — nice-to-have, unblocks any future re-canonicalisation run). Source:
      `instruments_store_cf_canonicalization_single_walk_2026_07_24.md`. Done when: `--asset-group prediction` runs
      without raising and correctly resolves the prediction bucket.

- [x] ✅ [CODE] P2. **IS audit-finding cleanup sweep (independent, different files — dispatch concurrently).** (a)
      Confirm UTL `record_captured_from_counts` auto-stamps `default_source` for single-source cells, else thread
      `source=` through the 9 blank-source `orchestrator.py` callsites (unified-trading-library + instruments-service);
      (b) make `orchestrator.py:4271` `_af_record_empty(reason=...)` take a required typed `EmptyConfirmedReason`; (c)
      narrow the broad excepts at `orchestrator.py:3794` (catch `NotFound` only, drop the `# type: ignore[union-attr]`
      at :3791) and `:7821`; (d) make the bar-edge fallback-to-open in `cefi/hyperliquid.py:257`,
      `cefi/ccxt_adapter.py:310-312`, `tradfi/polygon.py:243` total (raise/skip on unknown timeframe instead of silently
      falling to open); (e) replace the `os.environ["DEPLOYMENT_ENV"]="test"` runtime mutation at
      `orchestrator.py:8033-8041` and `sports_dependency.py:90-98` with an explicit `env=` param to
      `resolve_bucket_name`; (f) harden IBKR systemic-failure path (`tradfi/ibkr.py:337-348`, `_ib is None`/all-fail →
      `[]` no raise) — latent, IBKR not in `_TRADFI_VENUES` today; (g) fix the `instruments-store-prediction-…` vs SSOT
      `instruments-store-PRED-…` bucket-name mismatch in
      `deployment-service/terraform/gcp/lifecycle_catalogue_scheduler.tf:40-44`; (h) correct the over-broad
      "instruments-service owns all venue URLs" CLAUDE.md line (InstrumentRecord carries only
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
- [x] ✅ [INFRA] P1. Fix the scheduled `uts-prod-cf-manifest-audit` Cloud Run Job (asia-northeast1, cron 06:00 UTC),
      which has produced zero successful runs since 2026-07-04 (fails daily -- most days exit-1 "Application exec likely
      failed", 2026-07-13 specifically OOM'd at its 4Gi limit on the `--all-ags` invocation) -- affecting all 5
      asset_groups' daily CF-1..CF-14 manifest audit equally. Diagnose the non-OOM exit-1 days (2026-07-04 through
      2026-07-12) via `gcloud run jobs executions describe` + Cloud Logging to confirm whether they're the same OOM
      under a different symptom or a distinct bug; then apply the fix -- split the job into 5 per-asset_group Cloud Run
      executions/schedules (mirrors the existing manifest-consolidator per-AG pattern; preferred over merely bumping the
      memory limit since it also gives per-AG failure isolation, per the doc's own recommendation) or bump the memory
      limit if a per-AG split proves infeasible; redeploy. Source:
      `plans/archive/issues/cf_manifest_audit_scheduled_job_daily_failure_2026_07_13.md`. Done when:
      `gs://cf-manifest-audit-central-element-323112/cf_audit/` shows a fresh dated output object for all 5 asset_groups
      (cefi/defi/tradfi/sports/prediction) from a real green run, cited with `Evidence: cloudbuild=<id>` or the
      equivalent Cloud Run execution-success reference, and the source issue doc's 3 "Next steps" todos are flipped
      checked. — **Diagnosis**: distinct bug, not the same OOM (2026-06-27..07-12 = silent exec failure exit-1;
      2026-07-13..07-26, 14 straight days = genuine OOM at 4Gi once the exec bug's fix let it actually run). **Fix**:
      root-caused the memory cost — `unified-trading-library@6ce1ddb6` column-pruned + pyarrow-backed `_read_index()`
      (~3.7-4x RSS reduction, measured live) — then bumped Cloud Run to 32Gi/8vCPU (16Gi/4vCPU still OOM'd live on the
      defi-tick bucket; jumped to the ceiling), applied via `ENV=prod ./tofu.sh apply` (`deployment-service@e9bcb34`,
      GCP+AWS parity). Also fixed a false-positive checker bug found by this being the first-ever complete run —
      `_probe_paths()` sampled an irrelevant `_`-prefixed metadata dir over real data, RED'ing CF-2-paths/CF-3-partition
      on 10/10 buckets (`unified-trading-library@21069582`). **Evidence**: Cloud Run execution
      `uts-prod-cf-manifest-audit-qsp6r` (2026-07-26T21:14:24Z-21:18:13Z) completed all 10 buckets with ZERO OOM,
      including the previously-fatal defi-tick bucket (26,316,834 rows); wrote
      `gs://cf-manifest-audit-central-element-323112/cf_audit/2026-07-26.json` — the bucket's FIRST EVER object. 3
      source-doc Next-steps flipped in `issues/cf_manifest_audit_scheduled_job_daily_failure_2026_07_13.md` (now
      `status: resolved`). Genuine (non-checker-bug) CF reds this run surfaced across cefi/tradfi/sports/prediction are
      tracked separately: `issues/cf_manifest_audit_first_full_rollup_findings_2026_07_26.md`.
- [x] ✅ [DATA] P1. **DONE 2026-08-01 (slot 6, data_engineering) — CF-1/CF-4/CF-5/Era-B all GREEN on live prod,
      independently re-verified.** All 4 named CFs are now GREEN — CF-1/CF-3/CF-5/Era-B were already GREEN per
      2026-07-31's re-verification; the sole remaining gap was CF-4's regression (13,399 blank-`source` rows, all
      live-path `empty_confirmed`/`attempted_failed`, dated 2026-06-21→2026-08-01). Root cause: the live
      `MTDSShardManifestRecorder.record_captured` already derived `source` via `source_string_for(pipeline_mode)`, but
      `record_empty`/`record_failed`/`record_zero_rows` never did — they relied solely on the writer's asset_group
      auto-stamp, which never fires because a venue's live capture source can differ from its batch source (e.g. DERIBIT
      batch=tardis, live=deribit), making it a multi-source cell. Fixed all 3 methods to thread
      `source = source_string_for(pipeline_mode) or ""` the same way `record_captured` does, + 3 new regression tests.
      `market-tick-data-service@c2ae82e0`. Backfilled the 13,399 existing blank rows via the same idempotent,
      snapshot-first `populate_v9_index_columns_inplace.py --asset-group cefi --apply` tool used for the original CF-4
      fix (dry-run confirmed `source_filled: 13399`, all other counters 0 — no side effects on already-green CFs; gate
      OK: rows/captured counts exactly preserved). Independently re-verified via a fresh `cf_manifest_audit.py` run
      against the live manifest post-apply: `CF-1/CF-3/CF-4/CF-5/Era-B` all GREEN
      (`market-data-tick-cefi-prd-central-element-323112`, 9,662,116 rows). CF-8/CF-2-paths remain RED, unchanged —
      explicitly out of this todo's named scope per the original text. See the split-off P2 CF-4-regression todo below
      (same fix closes it too). — **Bring cefi's raw_tick_data manifest to CF-1/CF-4/CF-5/Era-B GREEN using the proven
      cross-AG playbook.** cefi is the one AG this doc's 2026-07-14 Adjudication explicitly leaves un-adjudicated (no
      fresh CF-audit found). First re-run `cf_manifest_audit.py` against the live `market-data-tick-cefi-prd` manifest
      to get a current baseline, then apply the same fixes already landed for prediction/sports/tradfi/defi: (1)
      **CF-1** — normalize the `_index`'s `schema_version` column from string `'9'` to int64 via
      `pd.to_numeric(df["schema_version"]).astype("int64")` (snapshot the `_index` parquet first); (2) **CF-4** —
      backfill the ~54% (3.9M-row) blank `source` column via `record_captured(source=...)`, deriving source from the
      `{mode}_{source}` pipeline_mode or the venue→source map; (3) **CF-5** — type the ~189,665 untyped-reason rows; (4)
      **Era-B** — reclassify the ~521,513 chain rows so `options_chain`/`futures_chain` write `data_type=trades` with
      the chain distinction carried in `instrument_type` (verify key-membership before relabeling, per the doc's
      "Recurring-bug playbook" item 6). Re-run the CF-audit after each fix to confirm GREEN. Repo:
      market-tick-data-service (manifest/data), unified-trading-library (writer + audit tooling). Source:
      `issues/cross_cutting_manifest_canonicalisation_findings_2026_07_11.md`. **Done when**: a fresh CF-audit Progress
      Log entry shows cefi's CF-1/CF-4/CF-5/Era-B GREEN (or an explicitly documented residual with root cause), reaching
      parity with prediction/sports/tradfi/defi's already-confirmed state. — **IN PROGRESS 2026-07-29 (slot 14,
      data_engineering).** Fresh `cf_manifest_audit.py` re-run (`unified_trading_library.cf_manifest_audit`, no `--env`
      override — its default `prd` is correct; passing `--env prod` breaks bucket resolution, a trap hit and corrected
      this session) against `market-data-tick-cefi-prd-central-element-323112` (9,757,699 rows) gives a REAL,
      moved-since-2026-07-11 baseline — this doc's original numbers are stale, do not reuse them: - **CF-1** `[RED]`
      v9=9,523,490/9,757,699 (97.6%); dist `{9: 9,523,490, <NA>: 108,367, 6: 63,226, 5: 61,692, 4:       924}` — i.e.
      real un-migrated legacy schema_version rows (4/5/6), not just a string-vs-int '9' quirk. - **CF-4** `[RED]`
      blank=2,207,279/9,757,699 (22.6%) — already down from the doc's original 3.9M/54% (real progress happened since
      07-11, from an unidentified prior partial fix — not from this session). - **CF-5** `[GREEN]` already — 0/1,148,314
      untyped. **No work needed**, contrary to the doc's stated ~189,665 residual (already fixed by someone else since
      07-11). - **Era-B** `[RED]` chain rows=491,146 (down from the doc's 521,513, same partial-progress pattern as
      CF-4). - (CF-3/CF-8/CF-2-paths also RED but explicitly OUT of this todo's named scope — CF-1/CF-4/CF-5/Era-B
      only.)

      **CF-1/CF-3/CF-4 — DONE + LIVE-VERIFIED 2026-07-29.** `market_tick_data_service/scripts/
                                                                                                                                                                                                                                                                                          populate_v9_index_columns_inplace.py --asset-group cefi --apply` (the exact pre-existing tool already used for
                                                                                                                                                                                                                                                                                          defi/tradfi/sports/pred — row-preserving, snapshot-first at
                                                                                                                                                                                                                                                                                          `_index/snapshots/pre_v9_apply_cefi_2026_06_18.parquet` (kept, already existed), GATE-checked
                                                                                                                                                                                                                                                                                          captured-preserved-before-write). Applied successfully: `APPLIED — live _index written ... (9,783,677 rows,
                                                                                                                                                                                                                                                                                          schema_version=9)`, GATE `captured 3,955,852->3,955,852 (OK)`. **Independently re-verified by a fresh direct
                                                                                                                                                                                                                                                                                          manifest read** (not trusting the script's own log): `schema_version dist={9: 9,783,677}` (100% int 9),
                                                                                                                                                                                                                                                                                          `pipeline_mode blank=0`, `source blank=0`, `captured=3,955,852` — CF-1 and CF-4 (+ CF-3, not in this todo's
                                                                                                                                                                                                                                                                                          named scope but fixed as a side effect of the same tool) are all GREEN on live prod. No data loss (row count
                                                                                                                                                                                                                                                                                          and captured count both exactly preserved pre/post).

                                                                                                                                                                                                                                                                                          **Real obstacle + resolution (save the next session the rediscovery — this took 4 attempts)**: the naive
                                                                                                                                                                                                                                                                                          unbounded `--apply` run got OOM-killed partway through (host swap hit 100% full from an unrelated concurrent
                                                                                                                                                                                                                                                                                          host-wide event) with ZERO error output and no live-manifest change — **do not mistake a fresh `updateTime` on
                                                                                                                                                                                                                                                                                          the live blob for your own write landing**; this is a continuously-live production index other processes write
                                                                                                                                                                                                                                                                                          to independently, so always re-read + diff actual column values after an apply, never trust timestamp alone.
                                                                                                                                                                                                                                                                                          Retried via `unified-trading-pm/scripts/dev/run-bounded-analysis.sh --mem-cap <N>G -- ...` (the sanctioned
                                                                                                                                                                                                                                                                                          cgroup-capped wrapper for exactly this ad-hoc-heavy-memory-op class, per its own docstring's 2026-07-27
                                                                                                                                                                                                                                                                                          precedent incident) — needed **26G** to actually complete (10G failed at parquet-read, 16G failed at the
                                                                                                                                                                                                                                                                                          internal `df.copy()`, 20G failed at the final `to_parquet` re-serialize just before upload); this cefi index's
                                                                                                                                                                                                                                                                                          real peak footprint (9.78M rows x 36 mostly-`object`-dtype columns, held in 2-3 copies across
                                                                                                                                                                                                                                                                                          read->transform->reserialize) is genuinely ~20-26GB, well past the wrapper's 4G default and worth flagging for
                                                                                                                                                                                                                                                                                          the next AG-scale manifest op of this shape (a streamed/chunked rewrite would avoid this entirely, but that's a
                                                                                                                                                                                                                                                                                          bigger change to a script 4 other AGs already used successfully as-is — out of this todo's scope to modify it).

                                                                                                                                                                                                                                                                                          **Era-B — remaining scope, investigated further 2026-07-29 (slot 14).** `era_b_legacy_purge.py` inspected: it
                                                                                                                                                                                                                                                                                          is NOT the reclassify tool — it's a closed-set REGISTRY safety guard (`assert_era_b_purge_safe`) called by a
                                                                                                                                                                                                                                                                                          per-AG migrator right before dropping the retired `options_chain`/`futures_chain` `SOURCE_PRIORITY`/
                                                                                                                                                                                                                                                                                          `AVAILABILITY_AT_SEMANTICS` registry entries, AFTER the on-disk relabel already happened — it never touches
                                                                                                                                                                                                                                                                                          manifest rows or GCS objects itself. **No existing tool does cefi's actual reclassify**: grepped
                                                                                                                                                                                                                                                                                          `market-tick-data-service` for an Era-B-aware relabeler — `populate_v9_index_columns_inplace.py` (the tool that
                                                                                                                                                                                                                                                                                          fixed CF-1/CF-3/CF-4 above) has zero `options_chain`/`futures_chain`/Era-B logic (its `_MERGED_DATA_TYPE_MAP`
                                                                                                                                                                                                                                                                                          scope is DeFi-only); `migrate_cefi_flat_to_v9_canonical.py` already carries SOME chain-aware on-disk-path
                                                                                                                                                                                                                                                                                          logic (`_ONDISK_DATA_TYPE_MERGE`, `_CHAIN_BUNDLE_DTYPES`) but for the v6→v9 physical-path migration, a
                                                                                                                                                                                                                                                                                          different job than the CF-audit's Era-B `_index` check. **Open question before building a fix**: is the CF
                                                                                                                                                                                                                                                                                          audit's `data_type=options_chain/futures_chain` count a MANIFEST-only `_index` artifact (fixable in-place,
                                                                                                                                                                                                                                                                                          same shape as the CF-1/CF-4 fix) or does it reflect the actual on-disk GCS path (requiring a physical-object
                                                                                                                                                                                                                                                                                          relabel, VM-scale per the playbook's item 8 precedent — sports/tradfi/defi's already-done E3+E4/G4 fleet
                                                                                                                                                                                                                                                                                          runs)? Must be answered by reading the manifest writer's Era-B-era row-emission code path before writing any
                                                                                                                                                                                                                                                                                          fix — not yet done. Released via `/skip-current-task {"reason_code": "GATED"}`; not attempting a fix on an
                                                                                                                                                                                                                                                                                          unconfirmed manifest-vs-physical distinction against 491k live-prod rows. Re-run `cf_manifest_audit.py` after
                                                                                                                                                                                                                                                                                          whichever fix lands to confirm all 4 named CFs GREEN before flipping this todo's checkbox.

                                                                                                                                                                                                                                                                                          **Era-B open question — ANSWERED 2026-07-29 (slot-6, data_engineering): physical on-disk path, NOT a
                                                                                                                                                                                                                                                                                          manifest-only artifact.** Read the live writer's actual partition-path logic directly:
                                                                                                                                                                                                                                                                                          `market_tick_data_service/engine/orchestrator/symbol_rules.py`'s `_MERGED_DATA_TYPE_MAP = {"futures_chain":
                                                                                                                                                                                                                                                                                          "options_chain"}` (used by `_resolve_partition_data_type()`, called from `partitioned_writer.py`'s GCS-path
                                                                                                                                                                                                                                                                                          builders — doc comment there: `"GCS path: …/instrument_type={itype}/data_type={dt}/…"`) confirms
                                                                                                                                                                                                                                                                                          `data_type=` is a REAL, literal GCS path segment for cefi raw_tick_data objects, and neither
                                                                                                                                                                                                                                                                                          `options_chain` nor `futures_chain` maps to `trades` anywhere in the writer — `futures_chain` only merges
                                                                                                                                                                                                                                                                                          INTO `options_chain`'s physical folder, it does not become `trades`. Cross-confirmed via
                                                                                                                                                                                                                                                                                          `migrate_cefi_flat_to_v9_canonical.py`'s own comment on its mirrored `_ONDISK_DATA_TYPE_MERGE` constant:
                                                                                                                                                                                                                                                                                          *"The live writer writes futures_chain shards under `data_type=options_chain/` on disk (the
                                                                                                                                                                                                                                                                                          dex_pool_state-class logical≠on-disk lesson)."* That migrator only handles the v6→v9 flat-to-canonical
                                                                                                                                                                                                                                                                                          PATH migration (preserving the chain on-disk naming as-is) — it does not reclassify chain data to
                                                                                                                                                                                                                                                                                          `trades`. **No existing script anywhere in market-tick-data-service does this reclassify** (grepped
                                                                                                                                                                                                                                                                                          `scripts/*relabel*`/`*era_b*` — `defi_chain_genesis_relabel_migration_2026_06_01.py`/
                                                                                                                                                                                                                                                                                          `relabel_bybit_spot_perpetual_itype_2026_07_07.py`/etc. are structurally similar precedents but none target
                                                                                                                                                                                                                                                                                          this specific data_type). **Conclusion: cefi's Era-B fix requires a genuine physical-object relabel
                                                                                                                                                                                                                                                                                          (copy 491,146 objects' worth of shards from `data_type=options_chain/` to `data_type=trades/` while
                                                                                                                                                                                                                                                                                          stamping `instrument_type=options_chain`/`futures_chain`, then re-point the manifest `_index` rows) —
                                                                                                                                                                                                                                                                                          VM-scale per playbook item 8, same category as sports/tradfi's E3+E4/G4 fleet runs, not an in-session
                                                                                                                                                                                                                                                                                          `populate_v9_index_columns_inplace.py`-style fix.** This is real, bounded, but substantial new-script
                                                                                                                                                                                                                                                                                          engineering + a live-prod GCS migration against ~491k rows — properly scoped as its own follow-up rather
                                                                                                                                                                                                                                                                                          than attempted inline here (script would need to be written + unit-tested + dry-run-verified against a
                                                                                                                                                                                                                                                                                          small sample before any live `--apply`, mirroring the existing relabel-script precedents' structure).
                                                                                                                                                                                                                                                                                          Todo's checkbox stays unflipped — CF-1/CF-3/CF-4/CF-5 are GREEN, but Era-B genuinely remains open pending
                                                                                                                                                                                                                                                                                          that follow-up build+run. New follow-up todo filed below.

                                                                                                                                                                                                                                                                                          **Era-B — RESOLVED 2026-07-31 (data_engineering, the split-off todo below), premise was stale, no code
                                                                                                                                                                                                                                                                                          needed.** A fresh `cf_manifest_audit.py` Era-B check + a direct live-manifest/GCS re-verification (full
                                                                                                                                                                                                                                                                                          evidence on the split-off todo below) found **Era-B is ALREADY GREEN** — zero manifest rows carry
                                                                                                                                                                                                                                                                                          `data_type ∈ {options_chain, futures_chain}`, and the physical `options_chain/` GCS path is empty in every
                                                                                                                                                                                                                                                                                          sampled day. The "491,146 objects" figure above was a stale/conflated number, not a live gap. **However,
                                                                                                                                                                                                                                                                                          the SAME fresh audit found CF-4 (source) has REGRESSED to RED** (13,399 blank-source rows, all dated
                                                                                                                                                                                                                                                                                          2026-06-21→2026-08-01 — NEW drift since this todo's own 2026-07-29 "source blank=0" claim, not the original
                                                                                                                                                                                                                                                                                          gap) — so this todo's overall CF-1/CF-4/CF-5/Era-B GREEN gate is still NOT fully met: CF-1/CF-3/CF-5/Era-B
                                                                                                                                                                                                                                                                                          are GREEN, but CF-4 needs a fresh diagnosis + fix (out of the Era-B split-off's scope; not attempted this
                                                                                                                                                                                                                                                                                          session). Checkbox stays unflipped pending that.

                                                                                                                                                                                                                                                                                          **Other lessons from this session**: (1) `/tmp` is a SHARED 2GB tmpfs across ALL 8 slots on this host —
                                                                                                                                                                                                                                                                                          `cf_manifest_audit.py`'s `gcloud storage cp` temp downloads (100s of MB per AG) do NOT self-clean on script
                                                                                                                                                                                                                                                                                          exit; clean your own `/tmp/cf_audit_*` dirs after use (per-file `rm -f` + `rmdir`, NOT `rm -rf`/`find -delete`
                                                                                                                                                                                                                                                                                          — both are hook-blocked workspace-wide, even for harmless local-fs cleanup). (2) `cf_manifest_audit.py`'s
                                                                                                                                                                                                                                                                                          `--env` default is `prd` (correct) — passing `--env prod` breaks bucket resolution.

                                                                                                                                                                                                                                                                  **Re-verified 2026-07-29T20:21Z (slot 4, data_engineering): still correctly unflipped, no change since 16:08Z.**
                                                                                                                                                                                                                                                                  This todo's own remaining scope (Era-B) has no independent action left under ITS boundary — the physical relabel
                                                                                                                                                                                                                                                                  is now the separate `[SCRIPT] P1` todo immediately below (build+run the migrator), by slot 6's deliberate split.
                                                                                                                                                                                                                                                                  Doing that build under THIS task id would duplicate/collide with that todo's own dispatch once regen'd. Released
                                                                                                                                                                                                                                                                  via `/skip-current-task {"reason_code": "GATED"}` so the dispatcher can route the actual buildable work to the
                                                                                                                                                                                                                                                                  split-off todo. Next dispatch: flip this checkbox once the Era-B migrator todo lands + a fresh `cf_manifest_audit.py`
                                                                                                                                                                                                                                                                  re-run confirms cefi's Era-B GREEN.

- [x] ✅ [SCRIPT] P1. **NEW 2026-07-29 (slot-6), split off cefi's Era-B open question above.** **CLOSED 2026-07-31
      (data_engineering) — the premise was stale, not fixed by new code: Era-B is ALREADY GREEN on live prod, no
      physical relabel needed.** Before writing any migrator against a live-prod bucket, re-verified the ~491,146-object
      figure from first principles (data-correctness HARD RULE — never execute a stale premise against real infra)
      rather than trusting the carried-forward number: 1. **Live manifest query** (`_index/availability_index.parquet`,
      `market-data-tick-cefi-prd-central-element-323112`, 9,662,116 rows): **zero rows** with `data_type` column
      literally `options_chain`/`futures_chain` (checked directly — this is exactly the axis `cf_manifest_audit.py`'s
      own `_check_era_b()` reads, per its source:
      `ERA_A_CHAIN_DATA_TYPES = frozenset({"options_chain", "futures_chain"})`,
      `era_a =        df["data_type"].astype(str).isin(ERA_A_CHAIN_DATA_TYPES).sum()`). 34,931 rows carry
      `instrument_type ∈        {options_chain, futures_chain}` (a DIFFERENT axis) but their `data_type` column already
      correctly reads `trades`/`book_snapshot_5`/`derivative_ticker`/etc — not the legacy chain value. 2. **Live GCS
      probe** (`list_blobs` on `data_type=options_chain/` vs `data_type=trades/` prefixes for OKX-FUTURES/futures_chain
      across 4 sampled days spanning 2022-2025): the `options_chain/` physical path is EMPTY at every sample; real
      objects already live under `data_type=trades/`. No orphaned-path objects found in the sampled range. 3. **Ran the
      actual `cf_manifest_audit.py` Era-B check directly** (`unified_trading_library.cf_manifest_audit.audit()` against
      the live cefi tick bucket, 2026-07-31):
      `Era-B chain data_type [GREEN] data_type in        {options_chain,futures_chain} rows=0 (must be 0)`.
      **Conclusion**: the "491,146 objects" figure this todo (and the "Era-B open question — ANSWERED 2026-07-29"
      analysis it built on) carried forward was a conflation — the manifest-row Era-B RED count from an earlier
      (now-stale) audit reading was reinterpreted as a live GCS object count, and/or the CF-1/CF-3/CF-4 fix that ran
      2026-07-29 (`populate_v9_index_columns_inplace.py --asset-group cefi --apply`, a full-index rewrite) already
      normalized the manifest's `data_type` column values for these rows as a side effect, closing Era-B without that
      session crediting it explicitly. Either way: **no migrator was built, no GCS objects were touched** — building and
      running a live-prod copy migration against a premise that doesn't hold would have been wasted work + an
      unjustified write against a shared production bucket. Parent CF-1/CF-4/CF-5/Era-B todo's Era-B sub-item is now
      correctly resolved — see the update there. **Adjacent finding, NOT fixed here (out of this todo's Era-B-only
      scope, flagging per findings-triage)**: the same fresh audit run found **CF-4 (source column) has REGRESSED to
      RED** — 13,399/9,662,116 blank-`source` rows (0.1%), all `empty_confirmed`/`attempted_failed` (never `captured`),
      dated 2026-06-21→2026-08-01 (today, `written_at` max = live), concentrated on DERIBIT (6,361)/ASTER
      (2,287)/HYPERLIQUID (1,994)/BINANCE-FUTURES (1,562)/OKX-FUTURES (831)/KRAKEN-FUTURES (363) — this is NEW drift
      since the 2026-07-29 fix's "source blank=0" claim, not a residual of the original ~54%/3.9M-row gap. Likely root
      cause (not traced further here): the writer's `record_expected_empty`/`record_failed` path may not thread
      `source=` the same way `record_captured` does (only empty/failed rows are affected, never captured ones). CF-8
      (`available_at`) and CF-2-paths also remain RED per this same audit run, matching the parent todo's own
      already-tracked out-of-scope items.

- [x] ✅ [DATA] P2. **DONE 2026-08-01 (slot 6, data_engineering) — root-cause writer fix shipped + backfilled +
      independently re-verified GREEN.** Root cause found in `market_tick_data_service/live/manifest_recorder.py`:
      `MTDSShardManifestRecorder.record_captured` already derived `source` via `source_string_for(pipeline_mode)`, but
      `record_empty`/`record_failed`/`record_zero_rows` never did — the writer's own asset_group auto-stamp never fires
      here because a venue's live capture source can differ from its batch source (e.g. DERIBIT batch=tardis,
      live=deribit), making every affected venue a multi-source cell. Fixed all 3 methods to thread
      `source = source_string_for(pipeline_mode) or ""`, matching `record_captured`'s pattern exactly; 3 new regression
      tests added (`test_live_manifest_recorder.py`) proving each method now derives `source` correctly.
      `market-tick-data-service@c2ae82e0`, `quality-gates.sh` green, shipped via quickmerge, verified on origin.
      Backfilled the 13,399 existing blank rows via `populate_v9_index_columns_inplace.py --asset-group cefi --apply`
      (the exact tool + snapshot-first/GATE-checked pattern the original 2026-07-29 CF-4 fix used) — dry-run confirmed
      `source_filled: 13399` with every other counter at 0 (no side effects on CF-1/CF-3/CF-5/Era-B, all already GREEN),
      then applied; GATE held (rows 9,662,116→9,662,116, captured 4,135,169→4,135,169 exactly preserved). Independently
      re-verified via a fresh `cf_manifest_audit.py` run against the live manifest post-apply: CF-4 GREEN
      (`source=9,662,116/9,662,116 (100.0%)`), alongside CF-1/CF-3/CF-5/Era-B — matches + closes the parent
      CF-1/CF-4/CF-5/Era-B todo above. — **NEW 2026-07-31 (data_engineering) — cefi CF-4 (source column) has REGRESSED
      to 2026-07-29 fix.** Fresh `cf_manifest_audit.py` run against `market-data-tick-cefi-prd-central-element-323112`
      found 13,399/9,662,116 blank-`source` rows (0.1%) — all `capture_status ∈ {empty_confirmed, attempted_failed}`
      (never `captured`), dated 2026-06-21→2026-08-01 (live, `written_at` max = today), venues DERIBIT (6,361)/ASTER
      (2,287)/HYPERLIQUID (1,994)/BINANCE-FUTURES (1,562)/OKX-FUTURES (831)/KRAKEN-FUTURES (363). This is NEW ongoing
      drift, not a residual of the original ~54%/3.9M-row gap the 2026-07-29 fix closed (that fix's own evidence claimed
      "source blank=0" at the time). Diagnose the writer's `record_expected_empty`/`record_failed` path in
      `market-tick-data-service` (likely candidate: `orchestrator.py`'s empty/failed-recording call sites don't thread
      `source=` the same way `record_captured` does — only empty/failed rows are affected, captured rows are clean) and
      fix at the root so new empty/failed rows stop landing blank; then either backfill the 13,399 existing blank rows
      (mirroring the original CF-4 fix's `record_captured(source=...)` backfill pattern, deriving source from
      `{mode}_{source}` pipeline_mode or the venue→source map) or confirm they self-heal via the next consolidator pass.
      Source: found during the Era-B split-off todo above's fresh audit re-verification. Done when: a fresh
      `cf_manifest_audit.py` re-run shows cefi's CF-4 GREEN (or the residual is explicitly re-classified as expected and
      excluded), and the root-cause writer fix ships with a regression test proving new empty/failed rows carry
      `source=`.

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
      2026-07-21 and need no relaunch). Source:
      `/plans/archive/issues/datapoint_validation_results_bucket_missing_2026_07_21.md`. Done when: (a) alerting-service
      bucket-provisioning status is confirmed one way or the other (with a follow-up issue doc filed if a gap is found),
      (b) the VM_TASK fallback change is committed + shipped, and (c) either the 3 relaunched VMs (cefi/defi/prediction)
      reach a terminal RUNNING-to-completion state with day-frontier progressing in `run.log`, or the todo is left open
      with an explicit note that the Round-1 UAC workflow has not yet landed.

## Progress Log

> **Line-cap remediation (2026-08-03)**: the 2026-07-26 datapoint-validation close-out, the 2026-07-28 distinct-values
> owning-plan reconciliation, and the 2026-07-28 InstrumentRecord `extra='forbid'` measurement entries were extracted
> verbatim to `/plans/archive/2026_08/cross_cutting_satellite_ao_dispatch_batch1_progress_log_history_2026_08_03.md` to
> bring this doc back under the 1000-line hard cap. New entries append below.

- **2026-07-31 (data_engineering, `cross_cutting_satellite_ao_dispatch_batch1-017`) — cefi's Era-B split-off todo CLOSED
  without writing code: fresh re-verification found the premise stale (Era-B already GREEN on live prod, no physical
  relabel needed).** Before building a migrator against a live-prod bucket touching ~491k objects, re-derived the actual
  current state from first principles rather than trusting the carried-forward figure — live manifest query + a direct
  GCS `list_blobs` probe + running `cf_manifest_audit.py`'s actual `_check_era_b()` all agreed:
  `data_type ∈ {options_chain, futures_chain}` rows = 0 on the live cefi manifest, and the `options_chain/` physical
  path is empty in every sampled day. The "491,146 objects" number this todo's own text carried forward was a stale
  conflation (likely the 2026-07-29 `populate_v9_index_columns_inplace.py --apply` full-index rewrite already normalized
  these rows' `data_type` column as a side effect, without that session crediting Era-B explicitly). Full evidence trail
  on the split-off todo. **Found + tracked as a fresh todo, not fixed inline (adjacent, out of this todo's Era-B-only
  scope)**: the same audit run surfaced a NEW regression — cefi's CF-4 (source column) is RED again (13,399 blank rows,
  all dated 2026-06-21→today, never present in the 2026-07-29 fix's "source blank=0" snapshot). Filed as its own
  `- [ ] [DATA] P2` todo above rather than left as prose, per the HARD RULE. No code shipped this session (a
  negative/stale-premise finding, not a build) — only plan-doc updates.

## Deferred — conflict-gated (genuinely unresolved, do not draft competing todos)

- **`plans/active/bucket_fold_execution_strategy_2026_07_17.md`**: Not a genuine conflict needing operator arbitration —
  it resolves by evidence, but not cleanly enough to draft a new todo either, so this is best flagged as a doc-hygiene /
  stale-citation issue rather than left silently batchable or silently dropped. Re-reading the target doc's 3
  Phase-1-flagged uncovered items...
- **`plans/active/data_pipeline_reconciliation_skill_2026_07_20.md`**: Read the doc's "Deferred work after 2026-07-21"
  table (line 825) and traced each of the 8 listed items against the current corpus state — every one is either already
  resolved/stale, or already actively claimed by an AG-specific (not cross-cutting) dispatch track, so none survives as
  genuinely-uncovered cross-cutting...
- **`/plans/active/issues/blocking_gcs_writes_on_event_loop_cross_asset_group_2026_07_18.md`**: GENUINE overlap found,
  not a clean duplicate. `/plans/active/defi_satellite_ao_dispatch_batch2_2026_07_26.md` (already-active, [SCRIPT] P1
  'MTDS DeFi perf bundle') dispatches a concurrency+blocking-write fix that partially covers this doc's Open items 1 and
  2, but via a DIFFERENT mechanism and for only a SUBSET of the... **✅ RESOLVED 2026-07-31** (corpus-wide
  ownership-conflict sweep, operator ruling keep-the-more-complete-side): the batch2 item **shipped** (`mtds@ff1b5d51`,
  2026-07-26) — it closed all of Open item 2 (dedicated `_defi_upload_executor.py`) plus item 1 for the two-handler
  subset it claimed (`solana_defi_handler.py`, `dex_pools_handler.py`). Grep-verified today that those are still the
  only two handlers using `ParallelPerSymbolRunner`, so the source doc remains the authoritative owner of the
  **residual** eight handlers; its todo has been narrowed in place to exactly that residual, with the shipped half
  cited. Nothing further is owed from this batch.
- **`/plans/archive/issues/manifest_reprocessing_generic_utility_2026_07_07.md`** (archived 2026-07-30, all todos done):
  Not actually orphaned — the Phase-1 "zero hits" grep was a false negative caused by a stray space in the covering
  plan's own citation. `plans/active/cross_cutting_consolidated_closeout_2026_07_25.md` Track 14 ("Scheduled-job
  reliability + concurrency/OOM defects + manifest reprocessing tooling") lists this exact doc...

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
- **`plans/archive/issues/honest_coverage_rollup_scoped_rerun_masks_distinct_values_2026_07_25.md`**: Conflict check: no
  genuine overlap found. The one coverage.json hit in the cross-cutting covering set
  (`cross_cutting_consolidated_closeout_2026_07_25.md` Track 21, citing
  `archive/issues/honest_coverage_nightly_cron_undersized_and_launcher_ssot_drift_2026_07_16.md`) is a DIFFERENT bug
  with a different fix target — that doc...
- **`plans/archive/issues/instruments_service_plan_reconciliation_2026_06_29.md`**: Conflict check: grepped
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
- **`plans/archive/issues/wsfeedconnector_phase35_gap_2026_07_06.md`**: Confirmed via direct read: the doc's sole open
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
  dims) are both explicitly `gate_on_depends: true`-blocked on... **CLEARED 2026-08-06 (iterative-drain re-check)**: the
  gate resolved 2026-08-03 (`cefi_chain_tail_v6_canonicalisation_2026_07_21.md` archived `status: resolved`, 0 real v5
  cefi chain objects needed migrating) and the target doc's own na-eligibility-audit 2026-08-03 pass already flipped it
  `assigned_vm: planning` directly — it is now self-dispatched (in-progress as of a 2026-08-03 dispatch-ordering fix),
  so no fresh batch todo is needed here; removing from future re-checks.
- **`plans/active/issues/pipeline_smoke_sweep_findings_2026_07_20.md`**: Confirmed the target doc's "## 4. Still open"
  section verbatim (3 items). All three resolve without a new cross-cutting todo: (1) "prediction cannot be smoked until
  its bucket resolution is fixed (dedicated `pred` flat kind)" — DUPLICATE/STALE. This is the same BucketNamingError
  class already root-caused and fixed in...

### 2026-07-29 (slot-6, data_engineering) — resolved cefi Era-B's open question; split off the physical-relabel build+run as its own todo

Picked up cefi's CF-1/CF-4/CF-5/Era-B todo where slot-14 left it (CF-1/CF-3/CF-4 GREEN + live-verified; CF-5 already
GREEN; Era-B released GATED pending a code-read to determine manifest-only vs physical-path). Answered the open question
directly from the live writer's own partition-path code
(`market_tick_data_service/engine/orchestrator/symbol_rules.py`'s `_MERGED_DATA_TYPE_MAP` + `partitioned_writer.py`'s
GCS-path builders, cross-confirmed by `migrate_cefi_flat_to_v9_canonical.py`'s own `_ONDISK_DATA_TYPE_MERGE` comment):
`data_type=options_chain/futures_chain` is a real, literal GCS path segment for cefi raw_tick_data objects, not a
manifest-only artifact — no existing tool reclassifies it to `data_type=trades`. This is genuine VM-scale
physical-relabel work (playbook item 8, same category as sports/tradfi/defi's already-done E3+E4/G4 fleet runs), not a
quick in-session fix, so I did not attempt to build + run it inline. Filed it as its own scoped follow-up todo above,
structured as a copy-first/verify/operator-gated-delete two-phase (mirroring the `dex_pools`/`lending_indices` fold
precedent) so Phase 1 stays AO-eligible without needing an `[OPERATOR]` tag. Parent todo's checkbox stays unflipped —
CF-1/CF-3/CF-4/CF-5 are GREEN but Era-B genuinely remains open pending that follow-up. Declining to force-complete the
parent todo per plans-run-to-actual-completion.

### 2026-07-29 (slot-6, data_engineering) — started the Era-B relabel build; handing off design research, not shipping code this turn

Picked up the follow-up todo above (build + run cefi's Era-B physical relabel). Design research before writing any code:
confirmed the canonical write-path builder is
`unified_api_contracts.canonical.partition_paths. build_cefi_partition_path(venue=, instrument_type=, data_type=, day=, file_name=, pipeline_mode=, underlying=, quote_asset=, margin_type=)`
— the v6 chain-bundle branch fires only when `instrument_type` is `options_chain`/`futures_chain` AND all three of
`underlying`/`quote_asset`/`margin_type` are populated, else it falls to the v5 per-symbol layout. For reconstructing
existing rows' actual GCS paths from manifest data (rather than a new whole-corpus GCS walk, which is review-blocking),
the correct SSOT is `unified_api_contracts.candidate_parquet_paths` (dispatched via
`unified_trading_library/manifest_writer/_rows.py::_resolve_candidate_write_path`'s exact kwarg shape) — this is the
SAME function the daily hygiene audit uses, so reusing it keeps the relabel script's path resolution byte-identical to
what the rest of the fleet already trusts, rather than hand-rolling a second copy. Reviewed two structural precedents in
depth: `market-tick-data-service/scripts/fold_legacy_solana_defi_to_consolidated_canonical_2026_07_21.py` (real
cross-path GCS object COPY, `blob_exists`-gated idempotency, manifest registration as a SEPARATE follow-up step — the
closer analog since it moves data between two different physical paths, same as this fix needs) and
`scripts/relabel_bybit_spot_perpetual_itype_2026_07_07.py` (SMOKE-FIRST protocol: `--smoke` relabels ONE shard +
verifies the split before `--apply` touches the rest — worth reusing for the UX even though that particular script
happens to be manifest-only). **Did not write the migrator script this session** — correctly implementing the per-row
chain-bundle-axis extraction (underlying/quote_asset/margin_type) + real GCS `gcs_copy_object` calls against live-prod
financial-market data warrants a full session with room for careful unit testing before ANY live write, not a rushed
pass late in an already-long session. Everything above is captured so the next pickup doesn't have to re-derive it.
Declining via `/skip-current-task` (not `GATED` — nothing external blocks this, it's genuinely buildable, just not
safely rushable) so it can be re-dispatched fresh.

### 2026-07-29 (slot-12, data_engineering) — re-confirmed parent todo (-016) still GATED on the split-off migrator (-017)

Picked up the parent CF-1/CF-4/CF-5/Era-B todo (line 428) fresh via `/boot`. Checked live backlog state before doing any
redundant re-audit work: `cross_cutting_satellite_ao_dispatch_batch1-017` (the split-off Era-B physical-relabel migrator
todo, line 539) is currently `status: dispatched, dispatched_to: 9` — actively being worked, not stalled. Per slot-4's
and slot-6's prior analysis (unchanged): CF-1/CF-3/CF-4/CF-5 are GREEN and live-verified; the parent todo's own boundary
has no independent action left — the only remaining piece (Era-B) now lives entirely under -017. Releasing via
`/skip-current-task {"reason_code": "GATED"}` rather than duplicate slot 9's in-flight work. Next dispatch: flip this
checkbox once -017 lands + a fresh `cf_manifest_audit.py` confirms cefi's Era-B GREEN.

### 2026-07-31 (slot-10, data_engineering) — re-confirmed parent todo (-016) still GATED on the split-off migrator (-017)

Picked up the parent CF-1/CF-4/CF-5/Era-B todo fresh via `/boot`. Checked live backlog state before any redundant
re-audit: `cross_cutting_satellite_ao_dispatch_batch1-017` is `status: dispatched, dispatched_to: 11` (dispatched
2026-07-31T23:37:38Z, `orphan: false`) — actively being worked. Nothing has changed since slot-12's 2026-07-29 check:
CF-1/CF-3/CF-4/CF-5 remain GREEN, and the only remaining piece (Era-B) still lives entirely under -017's own build.
Releasing via `/skip-current-task {"reason_code": "GATED"}` rather than duplicate slot 11's in-flight work. Next
dispatch: flip this checkbox once -017 lands + a fresh `cf_manifest_audit.py` confirms cefi's Era-B GREEN.

- **context-scout 2026-08-03**: populated/refreshed context_scope (4 entries).
- **context-scout 2026-08-05**: re-scouted; context_scope unchanged (4 entries), still accurate.
- **context-scout 2026-08-07**: refreshed context_scope (5 entries) -- swapped `defi-completeness-oracle.md` (tied to an
  already-`[x]`-shipped todo) for `data_completion_to_100_all_ag_2026_06_21.md`, the literal source doc for this batch's
  sole remaining open todo (credential-ask + VM-launch canonicalisation-gate check), and added
  `deployment-service/scripts/vm/`, the launcher common path that same todo names as its edit target.
