---
doc_type: issue
title: "plan_reconciler defi-tranche run findings — 2026-08-18 (dispatch agt-94f58e, slot 29)"
summary: >-
  Daily deep reconciliation pass over the defi topic tranche (131 active docs, 7-hunter fan-out, 42 raw candidates).
  Fixed 6 contradictions, 11 hygiene issues, 1 zero-checkbox conversion, and 1 mechanical codex-staleness correction
  (recursion_depth_max) this run. Routed 9 items needing judgment/live-investigation/operator awareness (2
  codex-drift, 2 missing-paired-finalize-plan gaps, 3 archive-candidate bridges, 1 formatting-convention ruling
  request, 1 stale-VM-completion-claim needing live follow-up). 1 candidate refuted (not a real finding). 12 further
  candidates deferred untouched — genuinely in today's 12h grace window. Zero blocked-questions filed (trust mode
  2026-08-15 ruling — every judgment call in this run had a defensible direct resolution). Run complete.
status: open
nature: issue
asset_group: [defi]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan_reconciler, defi, reconciliation, checkpoint]
related:
  [
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /plans/active/issues/plan_reconciler_findings_defi_2026_08_17.md,
  ]
created: "2026-08-18"
author: plan_reconciler
source: "agt-94f58e"
locked_by:
priority: P2
assigned_vm: NA
execution_scope: local-only
# was: defi_master (epic-assignment audit 2026-08-19) -- same as its 08-16/08-17
parent_epic: plan_hygiene_master
  # predecessors: a plan-reconciliation run report over the defi tranche, not defi asset-group content itself
resolved_by:
depends_on: []
drift_direction: advance-code
context_scope:
  [
    /plans/active/issues/plan_reconciler_findings_defi_2026_08_17.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
    /codex/05-infrastructure/spot-vms-for-backfill.md,
  ]
---

# plan_reconciler defi-tranche findings — 2026-08-18

Dispatch `agt-94f58e`, slot 29, tranche `defi`.

## Phase -1 — prior findings doc reconciliation

`plan_reconciler_findings_defi_2026_08_17.md` re-checked against fresh state before starting today's fan-out:

- Its "Doc-drift / routed" item 1 (`data_pipeline_check_mdps_features_2026_07_20.md`'s stale `[REVIEW] P2` split-todo,
  citing an already-resolved gating doc) — **already resolved**: the todo is now `- [x] ✅ [REVIEW] P2` (line 295 as
  of this run's FF-pulled state). No action needed.
- Its "Doc-drift / routed" item 2 (`strategy_service_centralization_fixes_2026_08_16.md`'s `sequential: true` +
  todo-1 `[OPERATOR]` gate question) — **resolved**: todo 1 is now `- [x] [OPERATOR] P0. ✅ RULED 2026-08-17`. The
  doc is also in today's 12h grace window (touched <12h ago) — read-only this run regardless.
- Its "Plans not reached" item on AO-dispatch-readiness tagging gaps — Batch G independently re-confirmed this is
  real for `solana_dex_pool_swaps_indexer_2026_08_08.md` todo 5 (see Grace-deferred below; that doc is
  status:active, not draft as the 08-17 doc assumed — the gap is live now, not pre-flip). The `batch14` half is a
  separate, DIFFERENT VM-launch todo which this run fixed directly (see Hygiene fixes).

`plan_reconciler_findings_defi_2026_08_16.md` and `_08_17.md` themselves were both read in full by their assigned
hunter batch (F and G respectively) like any other tranche doc — no action needed on either beyond what's noted
below.

## Coverage

- STEP1: FF-pulled every repo in the slot from the **slot-29 clone** (`.tabs/29/unified-trading-pm`, not the root
  clone — root-clone reads are read-only per this dispatch's boot guardrail; verified the two are genuinely distinct
  `.git` clones before proceeding). All clean except `unified-trading-ci` (not FF-clean; no STEP-4 verification this
  run depended on it).
- Tranche inventory: 131 active docs (`generate_tranche_doc_inventory.py --tranche defi`), down from 140 on 08-17
  (net -9: some archived/superseded since, some new since — not separately audited).
- 12-hour grace window computed explicitly at STEP 2 (per 08-17's own process-finding lesson): 36 of 131
  defi-tranche docs touched in the last 12h — read-only context this run, listed below. Verified via
  `git log --since="12 hours ago"` intersected against the tranche list, not inferred.
- STEP3: fanned out 7 parallel read-only hunters (batches A-G, ~19 docs each, `model=sonnet` explicit), each pasted
  `SUB_AGENT_MANDATORY_RULES.md` in full at spawn top. **131/131 tranche docs read in full** (every hunter reported
  its exact batch size read, zero missing files). Each hunter combined the epic-cluster/topic/codex-alignment/
  mechanical-adjudicator/missed-flip hunter families into one full-doc read pass per batch (the proven 08-17 shape)
  rather than a separate pass per family — batches are disjoint doc sets so no cross-batch reconciler was needed.
- STEP4: verified every candidate INLINE (orchestrator, sonnet/max, per this doc's own `model: sonnet` frontmatter +
  CLAUDE.md's 2026-08-08 opus-is-manual-only ruling) via fresh `grep`/`git log`/`gcloud` re-checks against current
  disk + git + live-infra state — not by trusting hunter prose. Every fix below cites what was independently
  re-verified before applying.

## Grace-window docs (read-only context this run, 36 of 131)

autonomous_session_operator_decisions_2026_07_25, b21_distinct_values_noncanonical_live_2026_08_18,
coverage_floor_registries_no_cross_propagation_2026_07_17, data_completion_defi_2026_07_15,
defi_archetype_universe_no_curtailment_mechanism_2026_07_23, defi_collect_schedulers_paused_since_2026_07_18_2026_08_16,
defi_dex_pool_density_drop_pool_level_followup_2026_08_14, defi_distinct_values_zero_noncanonical_dispatch_2026_08_04_finalize,
defi_gas_net_cost_partial_wiring_gap_2026_08_17, defi_kamino_lending_blazestake_regrowth_after_retirement_2026_08_17,
defi_kamino_lending_blazestake_regrowth_after_retirement_finalize_2026_08_17,
defi_legacy_data_type_names_manifest_migration_scope_2026_08_04, defi_legacy_fold_relaunch_vm_infra_flakiness_and_oom_2026_08_15,
defi_leverage_archetypes_health_factor_wrong_source_2026_08_16,
defi_lst_yields_backfill_blocked_manifest_consolidator_and_hyperliquid_perp_funding_gap_2026_08_08,
defi_manifest_allow_stale_fallback_incomplete_for_long_pause_2026_08_07, defi_migration_audit_log_2026_07_24,
defi_orphan_bucket_delete_list_includes_canonical_bucket_2026_08_15,
defi_perp_daily_ctx_hl_forward_gap_since_2026_06_02_2026_08_04_finalize_2026_08_08,
defi_pool_uppercase_recurrence_after_fold_2026_08_11, defi_satellite_ao_dispatch_batch16_2026_08_17,
defi_satellite_ao_dispatch_batch16_2026_08_17_finalize, defi_venue_e2e_batch1_deferred_followups_2026_08_17,
lst_rate_honest_coverage_2026_07_21, mdps_defi_pipeline_e2e_check_zero_captured_days_after_oom_fix_2026_08_17,
mdps_fleet_duplicate_relaunch_explosion_2026_08_15, na_eligibility_audit_defi_blocks_2026_08_17,
na_eligibility_audit_defi_blocks_2026_08_18, solana_dex_pool_swaps_indexer_2026_08_08,
solana_dex_pool_swaps_indexer_2026_08_08_finalize, strategy_service_centralization_fixes_2026_08_16,
strategy_service_centralization_fixes_finalize_2026_08_16, subgraph_health_probe_28_of_50_alerted_after_fix_2026_08_16_finalize_2026_08_17,
uac_data_type_validity_combinator_fragmentation_2026_07_07, uac_kamino_venue_reachability_cascade_regression_2026_08_15,
uac_per_venue_seed_fallback_removal_deferred_2026_07_26, vault_share_price_handler_manifest_missing_instrument_id_2026_07_31.

## Flips verified (applied this run)

None — every missed-flip candidate that survived hunter detection either (a) turned out to be a partial/multi-part
todo where only ONE sub-item had hard evidence (see `defi_satellite_ao_dispatch_batch2_2026_07_26_finalize.md` under
Hygiene fixes — annotated, not flipped, since 2 of 3 sub-items remain unverified), or (b) needed live-infra
verification this run didn't complete (see `defi_mdps_candle_backfill_fleet_outcome_2026_08_06.md` under Doc-drift /
routed). No candidate cleanly met the HARD evidence bar for a clean checkbox flip this run.

## Contradictions (confirmed) — all fixed this run

1. **[P2]** `defi_venue_lst_rates_residual_2026_07_24.md` — Success-criteria item 2 said the SUSHISWAP
   classic-vs-V3 ambiguity "remains open," directly contradicted by the Progress Log immediately below it (2026-08-11
   entry: "resolved (redirected, not left open)"). Fixed: success-criteria item 2 now states the resolution.
2. **[P1]** `estate_orphan_assessment_2026_07_21.md` — title/summary (frontmatter, what doc-retrieval's L2 step
   reads first) said "defi/cefi/tradfi blocked on multi-GB manifest download (need a VM)," stale for ~4 weeks
   against the body, which shows cefi COMPLETED 2026-07-22 and defi COMPLETED 2026-07-24 (15.8M orphan_class_E, the
   largest of any asset_group). Fixed: title/summary rewritten to reflect actual state (prediction still hung,
   tradfi status not re-confirmed this pass). HIGH VALUE — this is exactly the kind of stale-summary drift that
   misleads a future worker who trusts doc-retrieval's summary-only confirmation step.
3. **[P2]** `elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md` — §I work-surface table claimed
   `elysium_carveout_stubbed_strategy_service_2026_08_12.md` has "18/4" (open/done) todos; fresh recount
   (`grep -cE`) shows 17/5. Fixed the table cell. (Doc confirmed 962L, comfortably under the 1000L hard cap this
   time — no line-cap blocker like the 08-17 incident.)
4. **[P1]** `defi_satellite_ao_dispatch_batch3_2026_07_26_finalize.md` — the body banner directly under the H1 title
   still said "🟡 status: draft — inert until parent is operator-approved and dispatched," even though the
   frontmatter summary was already corrected 2026-08-12 (a partial fix that missed this exact body copy — a
   documented anti-pattern, see 08-17's own "Never combine..." lesson about partial fixes). A reader skipping the
   YAML (more likely for the body) would wrongly conclude this active, gating finalize plan (todo 1 still genuinely
   open) is inert. Fixed: banner now states `active` and explains the correction.
5. **[P3]** `defi_strategy_pnl_axis_index_2026_07_24.md` — a 2026-08-07 context-scout note claimed `repos:` was
   missing `strategy-service`; that gap was already closed 2026-08-17 (this same reconciler role's prior run,
   Hygiene fixes #1) but the note was never retracted. Fixed: struck the stale note with a pointer to the fix.
6. **[P3]** `pnl_interest_accrual_wrong_engine_and_banned_formula_2026_07_21.md` — summary states the
   codex-BANNED-formula problem as an unqualified current fact; body shows the FUNDING (strategy-service@aa1fcdc7)
   and STAKING (strategy-service@e93902d8) legs of `carry_staked_basis` already shipped onto real
   index-ratio/funding-rate sources (both shas independently verified reachable in strategy-service). Fixed: added
   an UPDATE note citing both shas, explicitly scoped to `carry_staked_basis` (did not assert this resolves every
   archetype — that wasn't re-verified).

## Hygiene fixes

1. `exec_tenderly_2026_08_15.md` + `e2e_defi_config_taxonomy_wizard_roundtrip_2026_06_17.md` — two separately-filed,
   un-cross-linked `[OPERATOR]` asks for the same underlying Tenderly-fork-RPC-+-API-key credential (one in
   execution-service CI, one in e2e-testing's smoke-test harness). Added reciprocal `related:` cross-links so
   provisioning the credential once surfaces both.
2. `defi_consolidated_closeout_2026_07_18.md` — the P0 "PURGE first, then seed" todo (real prod-GCS delete: 1.79M
   duplicate + ~219.5K phantom rows, then a 63.9M-row reseed) carries no `[OPERATOR]` tag or delete-safety citation,
   unlike its sibling delete todo (line ~681, which cites a verified 7-day soft-delete retention as its
   safe-idempotent justification). Self-flagged by na-eligibility-audit 2026-08-16 as "worth a follow-up look,"
   still open 2 days later. Added an explicit `[OPERATOR]` delete-safety note (conservative direction — adds a
   safety gate, doesn't remove one). Currently inert (doc gated NA on an unrelated Track-1 `depends_on`) but the tag
   gap will matter the moment that gate clears.
3. `/codex/09-strategy/architecture-v2/archetypes/carry-recursive-borrow-lending-only.md` — see "Codex corrections
   applied" below (its own section per STEP 5.f2).
4. `defi_catalog_engine_config_key_contract_drift_2026_07_23.md` — a na-eligibility-audit 2026-08-16 Progress Log
   entry was truncated mid-sentence ("...shipped SHAs;."). Closed the sentence cleanly (removed the stray
   semicolon+period, no content invented).
5. `defi_satellite_ao_dispatch_batch14_2026_08_16.md` — two fixes: (a) a citation said extraction came from
   `instruments_service_defi_golden_red_capability_drift_2026_08_14.md` "todos 1 and 3," but that doc's Todos
   section has only 2 items — corrected to "todos 1 and 2." (b) the legacy-fold VM-relaunch todo carried no
   `[OPERATOR]` tag or safe-idempotent justification (re-confirmed real and unfixed from 08-17's flag). Added a
   safe-idempotent justification (standard SPOT backfill relaunch, resumes from measured progress per
   `/codex/05-infrastructure/spot-vms-for-backfill.md`, no data deleted) — doc is still `status: draft`
   (pre-dispatch), so this is fixable now before any operator-approval flip.
6. `defi_satellite_ao_dispatch_batch2_2026_07_26_finalize.md` — a combined 3-part todo's sub-item (3) ("archive
   `mtds_perp_funding_backfill_hang_2026_07_14.md`") is unchecked with zero completion citation, even though the
   sibling `batch3_finalize` doc cites commit `bec54efeb` as having archived it. Independently verified: the file
   IS live at `plans/archive/issues/mtds_perp_funding_backfill_hang_2026_07_14.md` (34207 bytes) and `bec54efeb` is a
   real, reachable commit whose message matches ("archive 35 confirmed-resolved/superseded/complete docs"). Annotated
   sub-item (3) as done with the citation; did NOT flip the containing checkbox since sub-items (1) and (2) remain
   unverified (per STEP 5.a: flip only the shipped half).
7. `defi_turbo_api_hides_real_captured_data_2026_07_07.md` — `last_updated: 2026-07-12` was stale by 5+ weeks;
   `git log` shows the real last substantive commit is 2026-08-17 (a context-scout touch, not the hunter's guessed
   2026-08-08). Bumped to the git-verified date.
8. `defi_pyth_oracle_prices_seeded_feeds_unfetchable_2026_08_03.md` — a truncated Progress Log sentence ("...5 of 6
   original todos are closed;."). Closed cleanly.
9. `defi_track01_per_instrument_and_canon_id_2026_07_24.md` — a truncated Progress Log sentence naming "two
   2026-08-16 operator rulings (DEX-relevance no-TVL-fallback WON'T-DO;." with the second ruling never named. Closed
   HONESTLY without fabricating the missing ruling's name — pointed to the doc's own 2026-08-16 Progress Log entries
   for the full text instead of guessing. (Both this and item 8 share the same truncation shape on the same date —
   noted as a possible systemic pattern worth a future audit, not chased further this run.)
10. `solana_dex_pool_swaps_indexer_scope_2026_07_12.md` — a stray leftover "N." template token sat between a
    checkbox and its tag (`- [x] N. ✅ [DESIGN] P3.`). Removed.
11. `defi_satellite_ao_dispatch_batch11_2026_08_09.md` — summary said "12 items across 6 source docs"; the actual
    Todos list has 13 checkboxes after a mid-execution split on 2026-08-09 that never updated the prose count. Fixed
    the text (machine gating counts real checkboxes, not the prose number, so this was cosmetic-only risk).

## Codex corrections applied (mechanical, evidence-cited) — STEP 5.f2 carve-out

1. `/codex/09-strategy/architecture-v2/archetypes/carry-recursive-borrow-lending-only.md` — `recursion_depth_max`
   listed per-chain values (8 eth / 10 arb / 12 base) as the shipped spec. HARD evidence
   (`defi_catalog_engine_config_key_contract_drift_2026_07_23.md`, read in full, quotes a 2026-08-09 operator
   ruling verbatim: "keep the already-shipped `recursion_depth_max=5` for both archetypes, chain-uniform — the
   codex doc's per-chain 8/10/12 figures are explicitly NOT adopted at this time") proves the codex text is
   factually stale — a single unambiguous substitution (5, uniform), no new measurement needed (citing an existing,
   dated, recorded ruling only), doesn't touch a hard-stop governance area. Corrected the codex line to state 5
   (uniform) with the ruling citation, preserving the superseded 8/10/12 figures inline for audit-trail context.

## Zero-checkbox docs found → converted to tracked todos

1. `mtds_is_full_adapter_smoketest_findings_2026_07_07.md` — "Open question 5" (the stale TradFi catalogue
   purge/regen question) was prose-only, unlike its siblings (questions 2 and 6, already converted by the 2026-08-16
   plan_reconciler run). Converted to a tracked `- [ ] [DECISION] P3` todo matching the established sibling format
   exactly (same doc, same section).

## Doc-drift / routed (NOT auto-fixed — genuine judgment calls, needs live investigation, or formatting-convention rulings)

- **[P2, live-infra follow-up needed]** `defi_mdps_candle_backfill_fleet_outcome_2026_08_06.md` — todo checked `[x]`
  done on the strength of "VMs launched, confirmed RUNNING 2026-08-07" — never confirmed the backfill actually
  COMPLETED. Live-checked `gcloud compute instances list` this run: neither cited VM
  (`mdps-defi-2025-20260807-203541`, `mdps-defi-2026-20260807-203541`) is currently running, but a DIFFERENT,
  newer VM (`mdps-defi-2025-20260817-000343`, launched 2026-08-17) IS running now and isn't mentioned anywhere in
  the doc. This could mean the original run completed cleanly and 08-17's VM is an unrelated later cycle, OR the
  original relaunch failed/was preempted and got silently re-relaunched — genuinely ambiguous without reading VM
  logs / manifest state, which is real investigative work beyond this pass's scope. **[WORKER REC]**: a
  data-engineering follow-up should check `gcloud compute instances describe mdps-defi-2025-20260817-000343
  --zone=asia-northeast1-c` + its serial console log, and check manifest coverage counts for both `mdps-defi-2025`
  and `mdps-defi-2026`, before trusting either checkbox's done-state.
- **[P2, judgment call]** `defi_manifest_allow_stale_fallback_incomplete_for_long_pause_2026_08_07.md` vs
  `/codex/05-infrastructure/manifest-consolidator-ssot.md` — the codex SSOT frames `MANIFEST_ALLOW_STALE_FALLBACK`
  only as a memory-safety tradeoff, never mentioning the distinct data-COMPLETENESS risk the issue doc confirmed
  live (a filtered fallback read can silently return <2% of real data after a long consolidator pause). Does NOT
  qualify for the STEP 5.f2 mechanical carve-out — the correct fix requires deciding a NEW detection/warning
  mechanism (the issue doc's own open `[DESIGN] P2` todo), which is a design judgment call, not a single unambiguous
  substitution. **[WORKER REC]**: the codex doc needs a new paragraph describing the completeness risk once that
  design todo resolves — not before.
- **[P2, judgment call]** `/codex/02-data/canonical-cutover-register.md` §6d — per
  `defi_pool_uppercase_recurrence_after_fold_2026_08_11.md`'s own 2026-08-17 entry (which already found and
  documented this but explicitly left it uncorrected, "out of scope for a DIAG todo"), §6d claims the
  `processed_candles/` `instrument_type=` segment is "PENDING — no migration has run" for cefi/tradfi, contradicted
  by current code. Not independently re-verified against live code this run (would require a fresh code read,
  which STEP 5.f2 explicitly excludes as "new measurement"). **[WORKER REC]**: a follow-up should re-confirm the
  code state directly, then apply the same f2 carve-out this run used for `recursion_depth_max` if the evidence is
  equally clean.
- **[P3, formatting-convention ruling needed]** A "CANCELLED/EXTRACTED — extracted to `<doc>`" citation-marker
  pattern (no `- [ ]`/`- [x]` checkbox prefix at all) recurs across at least 4 independently-dated docs
  (`defi_adapter_dead_code_audit_2026_07_24.md`, `defi_archetype_universe_no_curtailment_mechanism_2026_07_23.md`,
  `instruments_service_defi_golden_red_capability_drift_2026_08_14.md`,
  `mtds_qg_red_morpho_url_and_sports_contract_regression_2026_08_15.md`,
  `onchain_staking_apy_bps_single_day_annualization_noise_2026_08_09.md`), and na-eligibility-audit's own findings
  doc explicitly names this as a deliberate action ("Converted both checkboxes to citation markers"). This deviates
  from `PLAN_FORMAT.md`'s stated todo format and `check_todo_format`'s malformed-line check, but looks intentional
  rather than accidental — did NOT mechanically "fix" (re-add checkboxes) these, since that would fight an
  apparently-deliberate convention. **[WORKER REC]**: `PLAN_FORMAT.md` should either formally sanction this shape or
  the na-eligibility-audit skill should stop producing it — a ruling is needed, not a guess either way.
- **[P2, real plan-authoring work]** `defi_collect_schedulers_paused_since_2026_07_18_2026_08_16.md` and
  `defi_gas_net_cost_partial_wiring_gap_2026_08_17.md` — both AO-dispatched (`assigned_vm: planning`) issue docs
  with genuine open work but no paired gated finalize plan, unlike this exact batch's own correct sibling precedent
  (`defi_kamino_lending_blazestake_regrowth_after_retirement_2026_08_17.md` + its `_finalize`). Per
  `task_template.md` §4's finalize-plan-coverage rule. Creating 2 new finalize plans is real authoring work, not a
  mechanical fix a reconciler applies inline — **[WORKER REC]**: author both finalize plans following the
  kamino-lending sibling's exact shape.

## Archive candidates (operator review)

- `defi_venue_lst_rates_residual_2026_07_24.md` and
  `features_service_clean_check_dangling_revert_of_hyperliquid_cefi_bucket_fix_2026_08_03.md` — both 100% `[x]`
  todos, unlocked, using `archive_exempt: true` as a "done but haven't run the archival ritual yet" bridge rather
  than the field's documented standing-reference-hub purpose.
- `defi_lst_oracle_timestamp_glued_instrument_id_2026_07_20.md` — same bridge pattern, bridge marker now 6+ days
  old with no evidence the follow-on archival pass has run.
- `defi_archetype_universe_no_curtailment_mechanism_2026_07_23.md` — 0 open todos, unlocked, already flagged
  archive-ready TWICE before (na-eligibility-audit 08-16, 08-17) — **NOT archived this run** (grace-window
  protected, touched <12h ago). Third consecutive flag; **[WORKER REC]**: the next non-grace-blocked pass should
  actually execute this one via the 6-step ritual rather than flag it a fourth time.
- **[WORKER REC]**: all of the above should route through `/archive-candidates-audit` rather than each reconciler
  pass re-deriving the same verdict — that skill runs the proper 6-step ritual + referrer sweep.

## Refuted (dropped by verify)

1. Hunter batch B's `defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md` archive-candidate flag — the
   doc's own Todos are 100% `[x]`/unlocked (mechanically archive-shaped), but its paired finalize plan's live
   reconciliation found the doc's actual substantive purpose (zero non-canonical axes) is NOT met (dex_pools 454K,
   dex_swaps 3.46M, uppercase POOL 1.64M rows still non-canonical). Not archived, not routed further — the paired
   finalize plan already owns this gap.

## Grace-window deferred (verified real, NOT fixed this run — genuinely touched <12h ago)

- **[P1, HIGH VALUE — prioritize next non-grace pass]** `defi_migration_audit_log_2026_07_24.md` — a 2026-06-08
  table row still says "DELETE-AFTER" for `market-data-tick-defi-prd`, the PERMANENT canonical DeFi tick-data
  bucket every live handler writes to — contradicted by a later note in the SAME doc (2026-08-16) but never
  banner-corrected. Already caused one near-miss (`defi_orphan_bucket_delete_list_includes_canonical_bucket_2026_08_15.md`
  exists because a worker nearly deleted this exact bucket per this table's guidance).
- `defi_orphan_bucket_delete_list_includes_canonical_bucket_2026_08_15.md` — a concrete follow-up ("enable GCS Data
  Access audit logging") stated only in prose inside a closed checkbox, never converted to a tracked todo.
- `data_completion_defi_2026_07_15.md` — a todo uses `[~]` instead of the two sanctioned checkbox states.
- `defi_satellite_ao_dispatch_batch16_2026_08_17.md` — duplicate YAML key `effort: high` (harmless, same value
  both times, but malformed).
- `solana_dex_pool_swaps_indexer_2026_08_08.md` — todo 5 (a VM-launch/data todo) carries no `[OPERATOR]` tag or
  safe-idempotent justification. Doc is `status: active` + `assigned_vm: planning` (already AO-dispatched) — this is
  a LIVE gap, not pre-flip, contra how 08-17's findings doc framed it.
- `strategy_service_centralization_fixes_2026_08_16.md` — `last_updated: "2026-08-17"` stale vs real last commit
  2026-08-18 01:44:50 UTC (git-verified).
- `uac_data_type_validity_combinator_fragmentation_2026_07_07.md` — `last_updated` field is malformed (holds a
  run-on annotation, not a date); git-verified real last commit 2026-08-17 15:30:24 UTC.
- `uac_kamino_venue_reachability_cascade_regression_2026_08_15.md` — `related:` uses a bare slug instead of the
  required leading-slash path; also has no `last_updated` field at all.
- `uac_per_venue_seed_fallback_removal_deferred_2026_07_26.md` — "Revisit trigger" list items 2-4 are prose-only;
  item 1 of the same list was already correctly converted to a real checkbox (precedent to follow).
- `subgraph_health_probe_28_of_50_alerted_after_fix_2026_08_16.md` — a done-when wait window elapsed ~1 day ago
  with no re-measurement Progress Log entry since. This is an operational action gap (someone needs to actually
  re-measure the alert rate), not a doc-edit — noted for operator awareness regardless of grace status.

## Coverage (hunters / batches / docs)

- 7 hunters (batches A-G), 131/131 tranche docs read in full (19/19/19/19/19/19/17 per batch, zero missing files).
- Candidates returned: 42 raw across all batches. Disposition: 6 contradictions confirmed+fixed, 11 hygiene fixes
  applied, 1 codex correction applied (mechanical, f2), 1 zero-checkbox conversion, 9 items routed (2 codex-drift
  needing judgment, 1 live-infra follow-up, 1 formatting-convention ruling request, 2 missing-finalize-plan gaps,
  3 archive-candidate bridges), 1 refuted, 12 verified-real-but-grace-protected (deferred to next pass).

## Plans not reached

None — all 131 tranche docs were read in full by the hunter fan-out, and every returned candidate was either
fixed, routed, refuted, or deferred-for-grace above. Nothing was dropped for time/context budget reasons this run.

## Progress Log

- **plan_reconciler 2026-08-18** (`agt-94f58e`, slot 29): full run complete. Boot guardrail conflicted with the
  literal `PM_REPO_PATH` session variable (pointed at the root read-only clone) — verified the slot-29 clone was
  genuinely distinct and used it for all work, per the explicit guardrail. STEP 1's hygiene-sweep side effect
  regenerated `plans/active/INDEX.md` + `active_plan_inventory_dashboard`; a mid-run branch-drift + conflicted
  autostash (unrelated concurrent commits landed on both files during recovery) required resolving both to HEAD's
  version rather than my stale local regen — no content lost, both are pure derived artifacts. Landed 3 checkpoint
  commits (`5da9ab838b`, `5c94de1d37`, `dc0038eb2e`) across 3 branch-drift retries total (this branch is under
  heavy concurrent-commit load, consistent with 08-17's own "Lessons for the next reconciler run" note — 2-4
  retries per push is expected, not a bug). Zero blocked-questions filed this run (trust mode applied throughout).
- **context-scout 2026-08-20**: populated/refreshed context_scope (4 entries)
