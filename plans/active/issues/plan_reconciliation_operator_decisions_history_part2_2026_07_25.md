---
doc_type: issue
title:
  "Plans-corpus contradiction audit 2026-07-11 — history part 2/4 (Section A P1-tail/P2/P3 tail + Section B header +
  auto-fix queue P0 + P1-partial: epics/client_isolation_and_governance_master through
  deployment_observability_expansion↔observability_master)"
summary:
  "Verbatim extraction of the remaining 25 Section A finding entries (P1 tail, P2, P3) plus the FIRST 32 of Section B's
  176 auto-fix-queue finding entries (P0 + P1-partial) from `plan_reconciliation_operator_decisions_2026_07_11.md`,
  split for line-cap compliance (`plans/active/task_template.md` §3 finding J). This is the exact seam between Section A
  and Section B — the '## B. AUTO-FIX QUEUE' heading itself falls inside this part. Every finding here was ruled on in
  the parent's §A2 OPERATOR RULINGS table (2026-07-12, Section A entries) or applied per the parent's Progress Log
  (Section B entries) — this file is the closed raw finding text only, not live tracking. Zero open todos."
status: resolved
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [plan-hygiene, contradiction-audit, reconciliation, operator-decisions, stale-drift, history]
related: [/plans/active/issues/plan_reconciliation_operator_decisions_2026_07_11.md]
created: 2026-07-25
parent_epic: plan_hygiene_master
assigned_vm: NA
execution_scope: local-only
priority: P3
source: [plan_reconciliation_operator_decisions_2026_07_11]
resolved_by:
  "extracted verbatim from the closed 2026-07-11 contradiction audit; every finding's ruling + disposition lives in the
  parent's §A2 rulings table and Progress Log, not in this file"
locked_by:
drift_direction: advance-code
depends_on: []
---

# Plans-corpus contradiction audit — history part 2/4 (Section A tail, findings 60-84 + Section B, findings 1-32)

> **Extracted verbatim 2026-07-25 →** this file, from
> `/plans/active/issues/plan_reconciliation_operator_decisions_2026_07_11.md` (line-cap remediation,
> `plans/active/task_template.md` §3 finding J — the parent was 3927 lines, over the 1000L hard cap). This is the SECOND
> of 4 history parts; see the parent doc for the full part index, the §A2 rulings table, Section C (structural gaps),
> Section D (bonus finding), and the Progress Log (which carries every currently-open todo — there are none in this
> file). Content below is byte-for-byte as it appeared in the parent, unedited, including the original '## B. AUTO-FIX
> QUEUE' section heading where it falls mid-file.

#### [P1] epics/client_isolation_and_governance_master.md (intra-doc)

- finding ids: 33
- **Epic's own P1-priority section appears twice with contradictory content** —
  `epics/client_isolation_and_governance_master.md:129-136`: “"## P1 — important; post-current-gate (was P0)" ... "F-25
  — build the FULL unified `ClientConfig` type in `unified_api_contracts.internal`"” vs
  `epics/client_isolation_and_governance_master.md:143-145`: “"## P1 — important; post-current-gate" / "_(no plans
  currently assigned at this priority)_"”
  - why: The epic has two separate '## P1 — important; post-current-gate' headers a few lines apart: the first lists a
    live, unchecked P1 task (F-25 ClientConfig dispatch) plus an archived-plan reference, the second flatly states no
    plans are assigned at P1. An agent scanning the epic for outstanding P1 work could stop at the s
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P1] epics/execution_master.md (intra-doc)

- finding ids: 367,53,316
- **May-23 critical path gating — recon-freeze kill-switch chain** — `epics/execution_master.md:54`: “## P2 —
  opportunistic / post-cutover (slot 7 dispatch 2026-06-01)” vs `epics/execution_master.md:59-61`: “- [ ] [CODE] P1.
  **G12 (execution-side) — emit per-incident recon-freeze signals** ... In-scope for May-23. Repo: execution-service.”
  - why: The same still-open todo is filed under a section header that classifies it as P2/opportunistic/post-cutover,
    while its own text tags it P1 and explicitly 'In-scope for May-23' (i.e. NOT post-cutover). This is a live-trading
    safety item: per the linked 2026-05-27 audit (active/issues/batch_live_reconciliation_service_a
- **Epic frontmatter related-list vs epic body disclaimer (intra-doc)** — `16`:
  “../active/execution_fidelity_tiers_uac_governed_2026_06_28.md,” vs `66`: “no other active plans currently declare
  `parent_epic: execution_master`”
  - why: The epic's own frontmatter `related` field (L14-18) and `related_plans` field (L27-31) both explicitly name
    execution_fidelity_tiers_uac_governed_2026_06_28.md as a related child plan, directly contradicting the epic body's
    italicized claim two sections later that no other active plans declare parent_epic: execution_ma
- **frontmatter last_updated vs body edit date (intra-doc)** — `epics/execution_master.md:32`: “last_updated:
  2026-05-21” vs `epics/execution_master.md:54`: “## P2 — opportunistic / post-cutover (slot 7 dispatch 2026-06-01)”
  - why: The F-32 operator-decision text and the 'slot 7 dispatch' heading are dated 2026-06-01, roughly two weeks after
    the frontmatter's last_updated of 2026-05-21 — the metadata field was not bumped when this content was added.
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P1] epics/mtds_mdps_master.md (intra-doc)

- finding ids: 175,328,142,329
- **epic consolidation claim vs actual live child-plan count** — `epics/mtds_mdps_master.md:133-138`: “"🔵 CONSOLIDATION
  2026-06-26 — live MTDS/MDPS work now runs through 2 themed survivors" (M-1 data_completion_to_100_all_ag, M-2
  mtds_file_size_refactor” vs `epics/mtds_mdps_master.md:713-714`: “"\_33 active plans declare parent_epic:
  mtds_mdps_master in their frontmatter (verified 2026-06-30). Workers pick up in priority order (P0 first)."”
  - why: The banner asserts all live MTDS/MDPS work now runs through only 2 named survivor plans, but the epic's own
    body says 33 active child plans (parent_epic: mtds_mdps_master) exist and are worked in priority order. All 5 of
    this batch's assigned docs (bucket_name_ssot, data_source_provenance, cefi_universe_capture_rule, m
- **workspace_qg_sweep_2026_05_23 status vs archive location** — `epics/mtds_mdps_master.md:718`: “"###
  [`workspace_qg_sweep_2026_05_23`](../archive/2026_05/workspace_qg_sweep_2026_05_23.md) — MTDS/MDPS cluster"” vs
  `epics/mtds_mdps_master.md:720-721`: “"**status**: 🟠 ACTIVE — QG sweep for market-tick-data-service +
  market-data-processing-service. Both ruff clean; run full `bash scripts/quality-gates.”
  - why: The link path places this plan under plans/archive/2026_05/ (i.e. already archived), yet the epic's own status
    line calls it '🟠 ACTIVE' and gives a live, actionable directive ('run full quality-gates.sh') with a prereq gate —
    a worker following the epic's P0 list could dispatch effort against an archived plan believing
- **Epic auto-populated child-plan index omits the epic's own designated primary survivor plan** —
  `epics/mtds_mdps_master.md:139-141`: “**M-1 · [`data_completion_to_100_all_ag_2026_06_21`]**... — backfill-to-100% +
  DeFi catalogue→per-pool capture + honest-absence swallow remediation” vs `epics/mtds_mdps_master.md:713-714`: “\_33
  active plans declare `parent_epic: mtds_mdps_master` in their frontmatter (verified 2026-06-30). Workers pick up in
  priority order (P0 first). Aut”
  - why: The epic's 2026-06-26 consolidation banner names data_completion_to_100_all_ag_2026_06_21 (parent_epic:
    mtds_mdps_master, status: active, our assigned doc) as the M-1 survivor carrying all live MTDS/MDPS work. The epic's
    own 'Assigned active plans' section, auto-populated 2026-06-30 (later than the banner) and claiming
- **live_pipeline_mtds_mdps_features_2026_05_08 status vs archive location** — `epics/mtds_mdps_master.md:729`: “"###
  [`live_pipeline_mtds_mdps_features_2026_05_08`](../archive/2026_05/live_pipeline_mtds_mdps_features_2026_05_08.md)"”
  vs `epics/mtds_mdps_master.md:731`: “"**status**: active"”
  - why: Same archived-path-but-active-status pattern as the workspace_qg_sweep entry: the plan file lives under
    plans/archive/2026_05/ yet the epic table asserts a bare 'active' status with no archival note, unlike other rows in
    the same P0/P1 lists that correctly say '✅ ARCHIVED'.
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P1] epics/sports_master.md (intra-doc)

- finding ids: 331,332,279
- **Sports bookmaker venue scope — retired venues still named in the live P0 data-correctness mandate** —
  `epics/sports_master.md:90`: “ALL 11 bookmaker × data_type combos (BET365/BETFAIR/DRAFTKINGS/FANDUEL/ODDS_API/PINNACLE
  × odds_snapshot + odds_movement)... Scope MUST cover every bo” vs `epics/sports_master.md:236-238`: “DRAFTKINGS and
  FANDUEL (US sportsbook browser-stub adapters) are DEFERRED-INDEFINITELY from the active sports universe...
  sports_master scope is now a”
  - why: The un-bannered 🔴 P0 ABSORBED mega-audit directive (dated 2026-05-20, still reads as live/authoritative — no
    SUPERSEDED marker like the other consolidated-todo blocks in this same doc got) names BET365/DRAFTKINGS/FANDUEL and
    invokes the workspace HARD RULE 'no asset_group skipped, no deadline-driven cutbacks.' But 8 da
- **Frontmatter summary bookmaker-count vs body's narrowed active venue scope** — `epics/sports_master.md:5`: “L0
  asset-group umbrella epic for the sports data pipeline (API-Football fixtures + 11 bookmaker odds combos)” vs
  `epics/sports_master.md:237`: “sports_master scope is now anchored on the 3 remaining-active sports venues: ODDS_API,
  PINNACLE, BETFAIR”
  - why: The frontmatter `summary:` (which should reflect current scope, last_updated 2026-06-24) still advertises '11
    bookmaker odds combos' as the pipeline's scope, but the body — dated more recently and never revised in the summary
    — narrows the active universe to just 3 venues, with 14 scraper bookmakers plus DRAFTKINGS/FAN
- **Epic frontmatter last_updated vs body content dates** — `epics/sports_master.md:62`: “last_updated: 2026-06-24” vs
  `epics/sports_master.md:273-288`: “## Scrapers retired 2026-07-08 per operator ... Shipped 2026-07-08: -
  `execution-service@29a888a8d` — deleted the entire `execution_service/sports_exe”
  - why: The epic's frontmatter last_updated (2026-06-24) predates substantial body content dated 2026-06-27
    (golden-window banner) and 2026-07-08 (scraper-retirement section with real commit SHAs), meaning the frontmatter
    timestamp is stale relative to the epic's own visible edits.
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P1] plans/PLAN_FORMAT.md (intra-doc)

- finding ids: 381
- **todo placement — frontmatter YAML vs. body markdown checkboxes** — `plans/PLAN_FORMAT.md:625-637`: “## Structural
  Order (MANDATORY) ... 1. **Frontmatter** (name, overview, type, status, completion_gates, depends_on, todos with
  checkboxes) ... \*\*Rule:” vs `plans/PLAN_FORMAT.md:78-118,229-241`: “### Active plan / wrapper plan (in
  `plans/active/`) [frontmatter schema has NO `todos:` field] ... Cursor Plan Mode renders Markdown checkboxes. Every”
  - why: The same SSOT doc has a section labelled 'MANDATORY' instructing that todos live inside the frontmatter YAML
    block (matching the pre-2026-05-21 legacy `todos:` list schema shown later at lines 183-225), while the current
    'Active plan / wrapper plan' frontmatter schema has no `todos:` field at all and the 'Cursor-Friend
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P1] plans/active/bucket_env_split_rollout_2026_06.md ↔ plans/active/bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md

- finding ids: 353
- **Whether strategy-store/execution-store/features-delta-one flat (non-env-tiered) bucket names are correct end-s** —
  `plans/active/bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md:405-406`: “`strategy-store` /
  `execution-store` / `features-delta-one` flat names — yaml deliberately keeps these flat (env-split rolled back); NOT
  drift.” vs `plans/active/bucket_env_split_rollout_2026_06.md:40,51-54`: “Operator directive 2026-06-09: env-splits
  everywhere (Group A and Group B, all kinds). The temporary Group B rollback to non-env-split names is to be ”
  - why: bucket_name_ssot_legacy_dual_write_remediation (status: active, last_updated 2026-06-27 — AFTER the 2026-06-09
    operator directive) still lists these exact bucket kinds under 'Out of scope ... NOT drift', i.e. flat names are
    deliberate and correct. But bucket_env_split_rollout_2026_06.md (also active, created 2026-06-09
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P1] plans/active/canonical_id_p0_ccxt_live_batch_divergence_2026_07_08.md ↔ plans/epics/batch_live_symmetry_master.md

- finding ids: 388
- **mechanical:terminal_status_in_active_dir** — `plans/epics/batch_live_symmetry_master.md:75-82`: “### 🔴 2026-07-08
  canonical instrument_id — live≠batch findings **status**: 🔴 NEW ... -
  [`canonical_id_p0_ccxt_live_batch_divergence_2026_07_08`] ... ” vs
  `plans/active/canonical_id_p0_ccxt_live_batch_divergence_2026_07_08.md:10`: “status: complete”
  - why: The epic batch_live_symmetry_master.md still lists canonical_id_p0_ccxt_live_batch_divergence_2026_07_08 under
    its P0 'must complete before next foundation gate' section with status marker 'NEW', while the plan's own
    frontmatter (status: complete) and body (all todos [x], evidence of shipped commit instruments-service@
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P1] plans/active/canonical_id_p0_strategy_reconciliation_2026_07_08.md ↔ plans/epics/batch_live_symmetry_master.md

- finding ids: 389
- **mechanical:terminal_status_in_active_dir** — `plans/epics/batch_live_symmetry_master.md:75-85`: “**status**: 🔴 NEW
  ... - [`canonical_id_p0_strategy_reconciliation_2026_07_08`] ... depends on the plan above; live position
  reconciliation is silently” vs `plans/active/canonical_id_p0_strategy_reconciliation_2026_07_08.md:14`: “status:
  complete”
  - why: Same epic section also lists canonical_id_p0_strategy_reconciliation_2026_07_08 as part of the 🔴 NEW /
    must-complete-before-next-foundation-gate P0 block, but the plan's own frontmatter (status: complete) and body (all
    todos [x], including the P0 end-to-end reconciliation-test todo) show it already shipped. The epic wa
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P1] plans/active/defi_collateral_sizing_and_wizard_full_parameterization_2026_06_17.md ↔ plans/active/issues/e2e_defi_config_taxonomy_wizard_roundtrip_2026_06_17.md

- finding ids: 301
- **Collateral-aware down-sizing for stables-only perp venues (Aster pattern) in staked_basis.py** —
  `plans/active/issues/e2e_defi_config_taxonomy_wizard_roundtrip_2026_06_17.md:97-105`: “Collateral-aware down-sizing is
  NOT implemented ... staked_basis.py:219-229 \_derive_structure: if the LST is not in
  accepted_perp_collateral(perp_venu” vs
  `plans/active/defi_collateral_sizing_and_wizard_full_parameterization_2026_06_17.md:53-58`: “Build the
  USDC-collateral + margin-buffer down-size branch in the staked-basis (and basis-perp) engine: when
  venue_accepts_collateral(perp_venue, lst)”
  - why: Both docs are dated 2026-06-17 and defi_collateral_sizing is explicitly the operator-directed fix for the exact
    gap e2e_defi_config_taxonomy describes (commit strategy-service@6e9164b1, unit tests naming Aster/Hyperliquid by
    name). defi_collateral_sizing marks Phase A DONE/shipped, yet e2e_defi_config_taxonomy's matchi
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P1] plans/active/infra_capture_and_devops_leftovers_2026_07_06.md ↔ plans/active/sports_p2_daily_forward_catalogue_and_final_gate_2026_06_27.md

- finding ids: 357
- **SPOT vs on-demand policy for forward/daily-poll VMs** —
  `active/infra_capture_and_devops_leftovers_2026_07_06.md:64`: “`/codex/05-infrastructure/spot-vms-for-backfill.md` —
  SPOT default for backfill; live/forward stay on-demand.” vs
  `active/sports_p2_daily_forward_catalogue_and_final_gate_2026_06_27.md:53-56`: “**SPOT VMs (HARD)** — the
  sports-scheduler daemon VM launches **spot/preemptible** (the cloud can reclaim + kill it at any moment) per
  [sports_p0_spot”
  - why: infra_capture_and_devops_leftovers_2026_07_06.md (active, last_updated 2026-07-07) states as a HARD worker
    guard, citing the same spot-vms-for-backfill.md codex SSOT, that 'live/forward VMs stay on-demand ... SPOT is for
    backfill only.' The sports plan explicitly puts its 'daily-forward' scheduler daemon (launch-sports
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P2] active/codex_vs_repo_docs_ssot_audit_2026_06_01.md ↔ active/instruments_mtds_subset_consistency_remediation_2026_06_17.md

- finding ids: 369
- **Is URDI a phantom name to purge from instruments-service code, or the live production fetch-spine module name?** —
  `active/codex_vs_repo_docs_ssot_audit_2026_06_01.md:194-195`: “Follow-up: URDI still in instruments-service CODE ...
  `URDI` is a phantom name per CLAUDE.md. Audit + rename in instruments-service.” vs
  `active/instruments_mtds_subset_consistency_remediation_2026_06_17.md:1855-1856`: “"rg URDI → 0 hits" is wrong;
  `urdi_reference_provider.py` is the LIVE fetch spine. Replace with "no NEW URDI refs" + fix the stale error message”
  - why: Both plans are status: active/open with a live unchecked todo. Doc A (2026-06-01) directs an agent to 'audit +
    rename' all URDI symbols in instruments-service code because URDI is purely a phantom name (matching CLAUDE.md's own
    'URDI phantom' framing). Doc B (2026-06-17, 16 days later) explicitly corrects this framing
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P2] active/deployment_observability_parity_live_batch_paper_2026_06_22.md (intra-doc)

- finding ids: 198
- **Cloud Run job registry size (same commit, two different counts)** —
  `active/deployment_observability_parity_live_batch_paper_2026_06_22.md:89`:
  “`deployment_service/cloud_run_job_registry.py` `CLOUD_RUN_JOBS: Final[tuple[DeploymentTarget, ...]]` — 49 jobs from
  all 24 `*_scheduler.tf`” vs `active/deployment_observability_parity_live_batch_paper_2026_06_22.md:266`:
  “deployment-service@360678e (DeploymentUmbrella + classify_deployment_target + 61-job CLOUD_RUN_JOBS registry +
  unclassified guard)”
  - why: The same document attributes the SAME commit (deployment-service@360678e) to a '49 jobs from all 24
    \*\_scheduler.tf' registry in the Phase-0 todo and its first Progress-Log entry, but the later 'FINAL REPORT' /
    second Progress-Log section (also citing @360678e) calls it a '61-job CLOUD_RUN_JOBS registry.' Both cannot be
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P2] active/instruments_service_docs_consolidation_2026_07_08.md ↔ epics/instruments_master.md

- finding ids: 118
- **The real starting doc-count for the instruments-service docs consolidation (17 vs 18)** —
  `epics/instruments_master.md:457`: “"DONE, `instruments-service@10ad69a4` — 18→7 docs (real count was 18, not 17)."”
  vs `active/instruments_service_docs_consolidation_2026_07_08.md:4`: “"Consolidate instruments-service's 17 docs into 7
  — one setup guide, one adapter-architecture guide, one doc per asset group"”
  - why: The epic asserts the corrected/real count was 18 docs (explicitly framing '17' as wrong), but the consolidation
    plan itself — the same doc the epic is citing as DONE — consistently uses 17 throughout its own title, summary ('17
    markdown files, 6,529 lines'), and Phase-1 todos ('Read all 17 existing docs'), and its own
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P2] active/issues/archetype_venue_universe_cefi_vs_registry_no_cefi_cells_2026_06_30.md ↔ active/issues/capability_wizard_analysis_findings_2026_06_11.md

- finding ids: 299
- **CARRY_STAKED_BASIS CeFi hedge-venue set: leg-spec (F22, shipped 2026-06-11) includes binance; the new flat-reg** —
  `active/issues/capability_wizard_analysis_findings_2026_06_11.md:285`: “CeFi (binance/bybit/deribit/okx) + DeFi
  (hyperliquid/gmx_v2/drift) hedge venues are now differentiated per-leg.” vs
  `active/issues/archetype_venue_universe_cefi_vs_registry_no_cefi_cells_2026_06_30.md:78-80`: “`CARRY_STAKED_BASIS` —
  new `CEFI` / `perp` cell, `venue_ids: [deribit, bybit, okx]` (matches the codex venue matrix...)”
  - why: F22's already-shipped ARCHETYPE_LEG_STRUCTURES leg-spec lists binance as one of the four CeFi hedge venues for
    CARRY_STAKED_BASIS, but the 2026-07-10 fix that added the flat ARCHETYPE_CAPABILITY_REGISTRY CEFI cell for the same
    archetype only lists [deribit, bybit, okx] — a fresh instance of the known dual-representatio
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P2] active/issues/batch_live_reconciliation_service_audit_2026_05_27.md ↔ epics/batch_live_symmetry_master.md

- finding ids: 25
- **Finality of BLRS D2/D3/D4 design decisions** — `epics/batch_live_symmetry_master.md:91-98`: “D2 — BLRS calls
  strategy-service position query API for the canonical position baseline (not a BLRS-local recomputation)... D3 — build
  all 3 recon gre” vs `active/issues/batch_live_reconciliation_service_audit_2026_05_27.md:391-422`: “### 7.2 ❓ Needs
  operator input (material...) — D2 — Canonical position baseline: query strategy-service/position vs ratify event
  archives. → ROUTED TO”
  - why: The epic (the designated SSOT board per the doc's own 2026-06-01 banner, last_updated 2026-07-08) records
    D2/D3/D4 as single, decided, imperative action items still awaiting implementation. But the BLRS audit doc's own
    '§7.2 Needs operator input' decisions-ledger section — the doc's stated authoritative decision tracke
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P2] active/issues/empty_output_category_count_ssot_contradiction_2026_07_03.md (intra-doc)

- finding ids: 346
- **empty-output shard classification: 3-category vs 4-category decision tree (which codex doc is authoritative)** —
  `active/issues/empty_output_category_count_ssot_contradiction_2026_07_03.md:44`:
  “/codex/04-architecture/shard-level-failure-isolation.md — claims
  `authoritative_for: [... three-category empty-output decision tree]`; body documents 3” vs
  `active/issues/empty_output_category_count_ssot_contradiction_2026_07_03.md:46`:
  “/codex/06-coding-standards/validation-and-errors.md — the newer merged write-side SSOT; documents a **four-category**
  decision (adds path D: zero-activ”
  - why: This filed issue (status: open, unresolved, priority P2) documents that two live codex SSOTs disagree on the
    category count for the same per-shard empty-output classification decision (3 vs 4, the zero-activity-bar path D),
    with neither doc's authoritative_for scoped to disambiguate — matching the workspace's own contr
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P2] active/issues/polymarket_book_snapshot_5_dead_stream_2026_06_26.md (intra-doc)

- finding ids: 242
- **Issue frontmatter claims resolved while its own resolution section's last step is still pending** —
  `active/issues/polymarket_book_snapshot_5_dead_stream_2026_06_26.md:5`: “status: resolved” vs
  `active/issues/polymarket_book_snapshot_5_dead_stream_2026_06_26.md:93`: “3. T+10 verification pending (VMs booting).”
  - why: The doc's frontmatter and resolved_by field assert the issue is fully resolved, but the Resolution section's
    final numbered step admits the T+10 post-relaunch verification was still pending (VMs booting) at time of writing —
    the resolved-status claim outruns the doc's own evidence.
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P2] active/mvp_backfill_cefi_tick_v10_2026_06_27.md (intra-doc)

- finding ids: 30
- **Whether residual Deribit per-strike trades/book5 rows (cap=536) block the G4 honest-complete gate** —
  `active/mvp_backfill_cefi_tick_v10_2026_06_27.md:269`: “The v10 capture universe excludes them ... Scope-exclusion
  cleanup can be tracked separately; they do NOT block G1–G4.” vs
  `active/mvp_backfill_cefi_tick_v10_2026_06_27.md:1066`: “DERIBIT/OPTION/trades cap=536 ... plan G0 marks as pre-v10
  artifact ('DO NOT BLOCK G4'), but G4 gate text says '0 per-strike trades/book5 cells'. Ambi”
  - why: Intra-doc conflict: the plan's own G0 gap analysis explicitly states Deribit per-strike trades/book5 residuals
    do NOT block G4, but the G4 gate's own todo text literally requires '0 per-strike trades/book5 cells' present. The
    doc's own 2026-07-06 Progress Log entry flags this as an unresolved ambiguity needing an opera
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P2] active/scripts_lifecycle_marker_rollout_2026_06_18.md (intra-doc)

- finding ids: 74
- **This plan's own `assigned_vm` value (frontmatter NA vs body harsh_pc)** —
  `active/scripts_lifecycle_marker_rollout_2026_06_18.md:15`: “assigned_vm: NA” vs
  `active/scripts_lifecycle_marker_rollout_2026_06_18.md:39`: “`assigned_vm: harsh_pc` so the local orchestrator backend
  (running as `harsh_pc`, STANDALONE) ingests it via the reconciler”
  - why: The plan's frontmatter (the field an orchestrator/reconciler actually reads for dispatch) says
    `assigned_vm: NA`, but the plan's own body explicitly asserts `assigned_vm: harsh_pc` as its dispatch target and
    dual-purpose rationale (AO fleet-test). Per CLAUDE.md, valid `assigned_vm` values are strictly `{planning, NA}`
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P2] active/sports_pipeline_to_100pct_golden_window_first_2026_06_27.md (intra-doc)

- finding ids: 264,265
- **corrupted duplicate frontmatter block** — `active/sports_pipeline_to_100pct_golden_window_first_2026_06_27.md:11`:
  “asset_group: [sports]” vs `active/sports_pipeline_to_100pct_golden_window_first_2026_06_27.md:64`: “asset_group:
  cross-asset”
  - why: The file contains a second, garbled YAML-looking block mid-body (after the real closed frontmatter) declaring
    asset_group: cross-asset, repos: [], tags: [] -- directly conflicting with the real frontmatter's asset_group:
    [sports] and populated repos/tags lists in the same file. This looks like a merge/edit artifact tha
- **coordinator doc's own assigned_vm/execution_scope pairing** —
  `active/sports_pipeline_to_100pct_golden_window_first_2026_06_27.md:26`: “assigned_vm: planning” vs
  `active/sports_pipeline_to_100pct_golden_window_first_2026_06_27.md:27,75-76`: “execution_scope: local-only ... This
  file is `execution_scope: local-only` -- the orchestrator does NOT ingest it.”
  - why: Per CLAUDE.md's documented two-track plan model, assigned_vm: planning means AO-dispatched while
    execution_scope: local-only + assigned_vm: NA is the human/never-ingested track -- this doc mixes the AO-dispatched
    assigned_vm value with the local-only/never-ingested execution_scope, an internally inconsistent frontmatte
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P2] active/utl_uac_reuse_consolidation_remediation_2026_06_10.md (intra-doc)

- finding ids: 64
- **Frontmatter repos: list includes a repo the body explicitly marks do-not-touch** — `9`: “repos: [agent-orchestrator,
  alerting-service, batch-live-reconciliation-service, client-reporting-api, deployment-api, deployment-service]” vs
  `47-49`: “Clean repos (audit found nothing actionable — do not touch): ... batch-live-reconciliation-service,
  greeks-service”
  - why: batch-live-reconciliation-service is listed in the plan's frontmatter `repos:` scope (implying it is
    in-scope/touched by this plan) while the body's 'Clean repos' section explicitly says the audit found nothing
    actionable there and instructs 'do not touch' — with no corresponding Phase item anywhere in the doc mentioni
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P2] epics/client_isolation_and_governance_master.md ↔ epics/execution_master.md

- finding ids: 340
- **Tier classification of strategy_master / execution_master / trading_agent_master (labeled 'L0 asset-group' vs ** —
  `epics/client_isolation_and_governance_master.md:95-97`: “Enforces on: ALL L0 asset-group epics (every
  transfer/order/strategy-emit respects client isolation + jurisdiction) - `strategy_master` +
  `execution_m”  vs  `epics/execution_master.md:21`: “tier: L2”
  - why: client_isolation_and_governance_master labels strategy_master, execution_master, and trading_agent_master as
    'L0 asset-group epics', but all three self-declare tier: L2 in their own frontmatter (execution_master:21,
    strategy_master:31 'tier: L2', trading_agent_master:18 'tier: L2'), and README's canonical 20-epic tier
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P2] epics/deployment_and_user_management_master.md (intra-doc)

- finding ids: 314,385
- **assigned-active-plan count vs actual plan list (intra-doc)** — `epics/deployment_and_user_management_master.md:72`:
  “_1 active plans declare `parent_epic: deployment_and_user_management_master` in their frontmatter. Workers pick up in
  priority order (P0 first)._” vs `epics/deployment_and_user_management_master.md:87`: “**status**: ✅ ARCHIVED
  2026-05-23 — Code half shipped (deployment-api reader repointed to env-tiered bucket names)”
  - why: The auto-populated banner claims 1 active child plan exists, but every plan actually listed across P0/P1/P2/P3
    (both gap_2_4_d_deployment_api_reader_repoint and deployment_ui_lifecycle_tabs) is marked ✅ ARCHIVED — zero active
    plans are shown, so the count is stale/wrong and a worker following 'pick up in priority order
- **Epic's declared repo scope (frontmatter) vs its own ownership/gate claims (body) re: user-management-ui** —
  `epics/deployment_and_user_management_master.md:12`: “repos: [deployment-api, deployment-ui,
  unified-trading-system-ui]” vs `epics/deployment_and_user_management_master.md:32,41`: “**Owns**: deployment-api +
  deployment-ui + user-management-service + user-management-ui ... All active plans under this epic that touch any UI
  repo (`”
  - why: This active epic's frontmatter `repos:` field — the field dispatch/scoping tooling reads — omits
    user-management-ui and user-management-service entirely, while its own body 'Owns' line and its UI Verification
    Contract both name user-management-ui as an actively owned, playwright-gated UI repo. Same doc, same status:act
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P2] epics/predictions_master.md (intra-doc)

- finding ids: 238
- **Intra-epic contradiction: adapter migration status** — `epics/predictions_master.md:408`: “Polymarket adapter
  migration (data_type rename) | NOT started | same” vs `epics/predictions_master.md:480`: “**SHIPPED mtds@`7643a5c`**
  "feat(predictions): Polymarket adapter per-market lifecycle gating + tests"”
  - why: The epic's own Critical Path table (line 408-409) claims Polymarket/Kalshi adapter migration is NOT started,
    while the epic's own later Consolidated-todos section documents both as SHIPPED (mtds@7643a5c, mtds@e8a6903). This
    table isn't covered by the section's own SUPERSEDED banner (which only covers the Consolidated-t
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

#### [P2] plans/PLAN_FORMAT.md ↔ plans/active/task_template.md

- finding ids: 382
- **valid `status:` enum values** — `plans/PLAN_FORMAT.md:86`: “status: draft | active | blocked | paused | complete |
  cancelled | superseded” vs `plans/active/task_template.md:71`: “status: active # active | draft (NOT ingested) | done
  | blocked”
  - why: PLAN_FORMAT.md's canonical frontmatter schema enumerates 7 status values with 'complete' as the terminal state
    (no 'done'); task_template.md's copy-paste block for new AO-dispatched plans instead lists 'done' as a valid value
    and omits paused/cancelled/superseded/complete entirely. A grep of all 134 active plans' `stat
- **DECISION NEEDED**: options TBD (P1/P2 drafting wave — next tick)

## B. AUTO-FIX QUEUE — 176 doc-pairs (hard-evidence reconciliation, applied autonomously)

#### [P0] active/canonical_id_p0_ccxt_live_batch_divergence_2026_07_08.md ↔ epics/batch_live_symmetry_master.md

- finding ids: 19,363,13
- **Status of CCXT instrument_id live=batch divergence bug** — `epics/batch_live_symmetry_master.md:83`: “the CCXT live
  adapter stores bare ccxt-native symbols; batch (Tardis) produces a differently-shaped canonical id for the same real
  instrument, across ” vs `active/canonical_id_p0_ccxt_live_batch_divergence_2026_07_08.md:10`: “status: complete”
  - why: Epic still lists this as an unresolved 🔴 NEW P0 finding, but the child plan is status:complete with all 13
    venues verified converged against real Tardis batch-mode ids (instruments-service@8544273d) and a 2026-07-10
    progress-log entry confirming the flip. Same class of risk as the sibling finding above: dispatch off th
- **canonical instrument_id live=batch divergence — is this P0 still open?** —
  `epics/batch_live_symmetry_master.md:75-87`: “### 🔴 2026-07-08 canonical instrument_id — live≠batch findings
  **status**: 🔴 NEW ... these 2 findings are direct live=batch determinism violations.” vs
  `active/canonical_id_p0_ccxt_live_batch_divergence_2026_07_08.md:10 and :65-80`: “status: complete ... all four todos
  [x] checked, e.g. 'Ship via quickmerge, quality-gates green ... instruments-service@8544273d, quickmerge landed on”
  - why: The epic (last_updated 2026-07-08) still marks this as '🔴 NEW' and lists it under 'P0 — must complete before
    next foundation gate' with unchecked bullets, implying it is an open blocking determinism violation. But both child
    plans it points to (canonical_id_p0_ccxt_live_batch_divergence_2026_07_08.md AND canonical_id_p
- **canonical instrument_id live≠batch P0 findings status** — `epics/batch_live_symmetry_master.md:73-80`: “## P0 — must
  complete before next foundation gate ... **status**: 🔴 NEW — from `canonical_instrument_id_audit_2026_07_08` ...
  these 2 findings are dir” vs `active/canonical_id_p0_ccxt_live_batch_divergence_2026_07_08.md:10`: “status: complete”
  - why: The epic (`last_updated` 2026-07-08, same day) frames both canonical_id_p0\_\* findings as '🔴 NEW' P0 work
    that 'must complete before next foundation gate', with no acknowledgement they are done. But both child docs are
    frontmatter `status: complete` (canonical_id_p0_ccxt_live_batch_divergence_2026_07_08.md:10 and canonica

- planned fix: Sync batch_live_symmetry_master P0 section: CCXT divergence RESOLVED
  (canonical_id_p0_ccxt_live_batch_divergence complete, instruments-service@8544273d, 13 venues verified).

#### [P0] active/canonical_id_p0_strategy_reconciliation_2026_07_08.md ↔ epics/batch_live_symmetry_master.md

- finding ids: 18,342
- **Status of CCXT live-vs-batch reconciliation defeat bug** — `epics/batch_live_symmetry_master.md:86`: “live position
  reconciliation is silently defeated for every CCXT venue because the canonical-vs-raw string comparison never
  matches.” vs `active/canonical_id_p0_strategy_reconciliation_2026_07_08.md:172`: “All 7 todos fixed + shipped.
  Operator-authorized execution per the blanket "execution on the 4 P0 fix plans" instruction.”
  - why: Epic's P0 section (last_updated 2026-07-08) still frames this as an active, unresolved live-trading safety bug
    ('is silently defeated', present tense, no checkbox/closure), but the linked child plan is status:complete with all
    7 todos shipped (strategy-service@0c407b57, deployment-api@c8eeee2) as of 2026-07-08/07-10. A
- **Status of the strategy-service live-reconciliation P0 fix (canonical_id_p0_strategy_reconciliation)** —
  `epics/batch_live_symmetry_master.md:75-87`: “### 🔴 2026-07-08 canonical instrument_id — live≠batch findings
  **status**: 🔴 NEW ... `canonical_id_p0_strategy_reconciliation_2026_07_08` — depends on” vs
  `active/canonical_id_p0_strategy_reconciliation_2026_07_08.md:9,172-174`: “status: complete ... **All 7 todos fixed +
  shipped.** ... strategy-service@0c407b57e1aa92afb430fc818f91abeb7b186c13, deployment-api@c8eeee2e67910c3cb9”
  - why: The epic (last_updated 2026-07-08, same day) lists this plan with no completion checkmark under a live '🔴 NEW'
    bug description ('silently defeated ... never matches'), reading as still-open/blocking work — unlike its own
    sibling entry pattern used elsewhere in the same epic family (instruments_master.md marks the paire

- planned fix: Sync batch_live_symmetry_master P0 section: reconciliation-defeat finding RESOLVED
  (canonical_id_p0_strategy_reconciliation complete, strategy-service@0c407b57 + deployment-api@c8eeee2).

#### [P0] active/issues/defi_perp_funding_mvp_scope_contradiction_2026_06_29.md ↔ active/mvp_backfill_defi_onchain_v10_2026_06_27.md

- finding ids: 43
- **DeFi perp_funding MVP-scope status for the DRIFT-Solana backfill** —
  `active/mvp_backfill_defi_onchain_v10_2026_06_27.md:158`: “✅ RESOLVED 2026-06-29 — OUT OF MVP SCOPE (provisional,
  pending Ikenna confirm). Per UAC SSOT is_mvp(), DRIFT perp_funding is NOT MVP” vs
  `active/issues/defi_perp_funding_mvp_scope_contradiction_2026_06_29.md:38`: “the ‘Resolution status’ /
  ‘Recommendation’ sections below (provisional Option 1, ‘out of MVP scope’) are SUPERSEDED... resolves this as Option
  2”
  - why: The v10 backfill plan (status: active, last_updated 2026-06-27) has its G1.5 item checked ✅ done with the
    resolution 'out of MVP scope' and explicitly says 'Reopen if Ikenna rules perp_funding IS in scope'. The sibling
    issue doc (last_updated 2026-07-09, more recent) records that a broader operator ruling has since fli

- planned fix: Apply the LATER operator ruling recorded in defi_perp_funding_mvp_scope_contradiction (Option 2:
  perp_funding IS MVP, UAC v13 unified-api-contracts@89b16943): update v10 plan G1.5 resolution text + un-resolve the
  424 DRIFT cells item, citing the issue doc.

#### [P0] active/issues/github_billing_dashboard_access_2026_07_09.md ↔ archive/2026_07/cost_observability_ui_2026_07_08.md

- finding ids: 48
- **GitHub billing on /ops/costs — pending credential ask vs already-shipped-and-live** —
  `active/issues/github_billing_dashboard_access_2026_07_09.md:12`: “status: open — summary: "The /ops/costs GitHub
  panel is a hardcoded placeholder because GitHub billing ... is owner-only and no credential we hold can” vs
  `archive/2026_07/cost_observability_ui_2026_07_08.md:697`: “GitHub real billing is LIVE (token landed, verified
  end-to-end). Operator (Ikenna) minted the Plan-scoped fine-grained PAT ... stored it as Secret Man”
  - why: This open issue doc's entire ask (mint a fine-grained PAT with Plan:Read, store as Secret Manager
    `github-billing-token`, swap the dummy provider, drop the placeholder note — see its unchecked Resolution checklist
    at lines 148-155) was fully completed and verified live on 2026-07-10 per the (now-archived) parent plan a

- planned fix: Close github_billing_dashboard_access issue doc as resolved (archived cost_observability plan + successor
  UI plan record PAT minted, stored as Secret Manager github-billing-token, verified end-to-end 2026-07-10) - after I
  verify the secret exists + provider code is non-placeholder.

#### [P0] active/issues/instrument_id_format_canonicalization_2026_07_08.md ↔ epics/instruments_master.md

- finding ids: 93,94
- **CeFi live=batch instrument-id convergence status** — `epics/instruments_master.md:466-467`:
  “canonical_id_p0_ccxt_live_batch_divergence_2026_07_08 — DONE, instruments-service@8544273d — all 13 canonical CeFi
  venues verified converged live=batc” vs `active/issues/instrument_id_format_canonicalization_2026_07_08.md:1065-1069`:
  “MTDS's own live CeFi WS connectors (raw-tick construction layer) were never retrofitted... mismatches are silently
  dropped. Confirmed in production GC”
  - why: Epic asserts live=batch convergence for all 13 CeFi venues is DONE/verified; the issue doc (updated through
    2026-07-10) found MTDS's live WS connectors were never retrofitted to the canonical id scheme and were silently
    dropping ticks (real data loss) until fixed 2026-07-10 — an agent trusting the epic's DONE claim wou
- **CBOE/VX combo-leg canonicalization completion status** — `epics/instruments_master.md:468-469`:
  “canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08 — P1, real InstrumentLeg/COMBO infrastructure exists
  (proven for CME), just not wired up ” vs `active/issues/instrument_id_format_canonicalization_2026_07_08.md:349-357`:
  “Confirm the revised TradFi combo fix — DONE 2026-07-09 (finding 7...) — reuse the existing
  InstrumentLeg/InstrumentType.COMBO infrastructure (already ”
  - why: Epic still describes CBOE/VX combo-leg wiring as not-yet-done; the child plan's own tracking issue doc records
    it as DONE 2026-07-09 with code shipped and landed. Epic text is stale and could cause an agent to re-dispatch
    already-completed work.

- planned fix: Annotate instruments_master's DONE line: convergence claim was builder-level; MTDS live WS connectors
  were retrofitted separately (fixed 2026-07-10 per instrument_id_format_canonicalization issue doc) - epic line gets
  the caveat + pointer.

#### [P0] active/issues/plan_hygiene_precommit_and_agentic_resolution_2026_06_10.md ↔ epics/plan_hygiene_master.md

- finding ids: 227
- **Whether the daily plan-hygiene Cloud Run cron actually works and notifies on failure** —
  `epics/plan_hygiene_master.md:93`: “Implemented as Cloud Run Job `uts-prod-plan-hygiene-sweep` + Cloud Scheduler.
  Failures append `## [hygiene-cron]` notification to both orchestrator in” vs
  `active/issues/plan_hygiene_precommit_and_agentic_resolution_2026_06_10.md:53`: “Cloud Run
  `uts-prod-plan-hygiene-sweep` (05:00 UTC) ENABLED but failing ~every other day with `Container called exit(1)` and
  ZERO stdout in Cloud Logg”
  - why: The epic (last_updated 2026-05-23, never revised) marks this cron infra done and claims it appends a failure
    notification to both orchestrator inboxes. The open issue doc (last_updated 2026-06-27, still has 2 open follow-up
    todos to eventually delete this same job) documents that it has been silently dying with zero lo

- planned fix: Annotate plan_hygiene_master's cron line: the Cloud Run job has been failing silently (exit 1, zero
  stdout) since ~2026-06-12 per the open issue doc - epic claim corrected with pointer; the fix itself stays tracked in
  the issue doc.

#### [P0] active/mvp_backfill_defi_onchain_v10_2026_06_27.md ↔ epics/defi_master.md

- finding ids: 37,41
- **DeFi vs CeFi asset_group classification of Lighter / Extended / Pacifica** — `epics/defi_master.md:282`: “Plus
  historical-replay backfill for Lighter / Extended / Pacifica (originally scoped under CeFi venue expansion but they
  are DeFi by asset_group).” vs `active/mvp_backfill_defi_onchain_v10_2026_06_27.md:74`: “LIGHTER / EXTENDED / PACIFICA
  are CeFi, NOT DeFi (v10 decision #4) — do NOT backfill them here. Any older plan treating them as DeFi is stale and
  SUBO”
  - why: The epic's still-current, un-bannered 'Scope' section asserts these 3 venues are settled DeFi-by-asset_group
    work (and repeats this in its 'Current state' and critical-path table), with no acknowledgment of any
    reclassification. The newer v10 MVP canonical-scope plan explicitly declares them CeFi and calls ANY older pl
- **Epic's 'Assigned active plans' body list is missing an active P0 child plan** — `epics/defi_master.md:1672`:
  “Auto-populated by `scripts/plans/populate_epic_bodies_2026_05_21.py` — it keeps the list in sync from frontmatter.”
  vs `active/mvp_backfill_defi_onchain_v10_2026_06_27.md:14`: “parent_epic: defi_master”
  - why: mvp_backfill_defi_onchain_v10_2026_06_27.md declares parent_epic: defi_master, is status: active, priority: P0,
    and is a heavily-worked in-flight plan (huge Progress Log through 2026-06-29); it appears in the epic's frontmatter
    related/related_plans lists (L18, L54) but is entirely absent from the epic body's '## Assig

- planned fix: Sync defi_master's Lighter/Extended/Pacifica asset_group classification to the v10 backfill plan's
  UAC-SSOT-backed classification, with pointer.

#### [P0] active/predictions_other_bucket_and_ui_drilldown_2026_06_20.md (intra-doc)

- finding ids: 239,240
- **3-level hierarchy prerequisite: ticked-done vs 'not yet ticked' in the same plan** —
  `active/predictions_other_bucket_and_ui_drilldown_2026_06_20.md:85`: “[x] ✅ [SCRIPT][UI] P0. **deployment-ui 3-level
  hierarchy + per-shard parquet download**. ... — deployment-ui@319075e” vs
  `active/predictions_other_bucket_and_ui_drilldown_2026_06_20.md:97`: “[BLOCKED-PLAYWRIGHT 2026-06-24 slot-21]\*\*:
  PREREQUISITE (3-level hierarchy above) not yet ticked; this VERIFY > cannot run until”
  - why: The 3-level hierarchy P0 item is checked off [x]✅ as shipped, but the VERIFY todo directly beneath it (itself
    unticked) explicitly states the same prerequisite is 'not yet ticked' and blocks the VERIFY on it. The two todos in
    the same plan directly disagree on whether the prerequisite is complete — an agent could eithe
- **UI todos ticked done despite the plan's own note that the required playwright gate never ran** —
  `active/predictions_other_bucket_and_ui_drilldown_2026_06_20.md:72`: “[x] ✅ [SCRIPT][UI] P0. Data-status panel
  renders `OTHER` as a normal canonical-question-group bucket (NOT "out of scope").” vs
  `active/predictions_other_bucket_and_ui_drilldown_2026_06_20.md:75`: “before ticking. — deployment-ui@d5b7dd3 |
  [BLOCKED-PLAYWRIGHT] fleet VM has no dev server; pw:L2 gate pending UI-capable slot”
  - why: This todo (and the two others in the same P0 block, lines 79-84 and 85-92) are marked [x]✅ done, but each
    carries its own '[BLOCKED-PLAYWRIGHT] ... pw:L2 gate pending' annotation on the same line — meaning the mandatory
    pw:L2 ✓ playwright verification (required by CLAUDE.md's UI hard rule before any tick) never actuall

- planned fix: Fix predictions_other_bucket intra-doc drift: 3-level-hierarchy prerequisite ticked done in one section,
  'not yet ticked' in another - align to the checked state with evidence.

#### [P0] active/sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md ↔ active/sports_p1_golden_window_apifootball_2026_06_27.md

- finding ids: 269
- **Golden-window API-Football enrichment coverage: 100%-for-94-leagues claim vs still-open 94-league enrichment g** —
  `active/sports_p1_golden_window_apifootball_2026_06_27.md:124`: “✅ Every API-Football data_type reads 100% honest
  coverage on 2025-09-01..2025-11-30 for the 94 leagues, manifest-verified.” vs
  `active/sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md:166`: “**94-league enrichment
  backfill** — the residual golden-window gap is now GENUINE missing enrichment (XG_SHOTS 0% / XG 13% / PLAYER_STATS 21%
  / MATCHE”
  - why: P1a's own Progress Log audit (same doc, line 164: "UAC universe (get_all_league_ids) = 33 leagues; all present
    in window") shows the verification actually ran against only 33 registered leagues, not the 94-league curated
    trading universe defined by the sibling plan. The sibling plan (same asset_group=sports, updated th

- planned fix: Sync sports golden-window enrichment coverage claim between the two sports plans (100%-for-94-leagues vs
  still-partial) to the later-dated evidence.

#### [P0] active/sports_pipeline_to_100pct_golden_window_first_2026_06_27.md ↔ epics/orchestrator_master.md

- finding ids: 349
- **AO dispatch model: multi-VM epic-fleet vs single-VM role-based dispatch** — `epics/orchestrator_master.md:64-65`:
  “**Owns**: agent-orchestrator multi-VM stack (central/orchestrator VM `planning` + human planning VM
  `human-planning` + 9 epic VMs — human/central SPLI” vs
  `active/sports_pipeline_to_100pct_golden_window_first_2026_06_27.md:208-209`: “Role-based dispatch — NO epic VM
  (single-VM architecture, 2026-06-27)...epic VMs deprecated per CLAUDE.md; there is no `vm-sports` to start”
  - why: orchestrator_master.md is status:active (not archived) and its core 'Owns' description plus its own frontmatter
    `assigned_vm: vm-orchestrator` (line 32) still present a live 9-epic-VM multi-VM fleet with per-VM backends as the
    current architecture. The 2026-06-27 sports plan (also active, and corroborated by `active/\_a

- planned fix: Extend orchestrator_master's partial-supersede notice: the 9-epic-VM fleet description in 'Owns' is
  superseded by the single-VM role-based architecture (2026-06-27, CLAUDE.md + AO plans); notice points to
  agent-orchestrator-single-vm-architecture codex doc.

#### [P0] active/tradfi_multisource_backfill_2026_06_22.md ↔ active/tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md

- finding ids: 304
- **VIX cash-index sourcing decision — open question vs already-decided-and-executed** —
  `active/tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md:128`: “Blocked on operator decision: route VIX
  through existing Barchart/Yahoo MTDS path or add a new VIX-specific data source. Status: **BLOCKED-OPERATOR-DE” vs
  `active/tradfi_multisource_backfill_2026_06_22.md:93`: “DELETE the VIX **cash index\*\* entirely (not leave as
  empty_confirmed clutter): not tradable, derivable from the futures, trades less often over a shor”
  - why: sp500_ml (provenance dated slot-23 2026-06-24, one day AFTER the multisource_backfill's 2026-06-23 operator
    decision) frames CBOE VIX cash-index sourcing as an UNRESOLVED question requiring an operator pick between routing
    via Barchart/Yahoo or adding a new source. But the operator already decided the opposite (2026-06

- planned fix: Update tradfi_sp500_ml's BLOCKED-OPERATOR-DECISION VIX item: decision already made + executed 2026-06-23
  (VIX cash index DELETED, derive from VX futures) per tradfi_multisource_backfill L93 - replace the open ask with the
  recorded ruling + pointer.

#### [P0] archive/2026_05/workspace_qg_sweep_2026_05_23.md ↔ epics/features_and_ml_master.md

- finding ids: 54
- **workspace_qg_sweep_2026_05_23 status/ownership** — `epics/features_and_ml_master.md:886-889`: “###
  [`workspace_qg_sweep_2026_05_23`](../archive/2026_05/workspace_qg_sweep_2026_05_23.md) — features/ML cluster
  **status**: 🟠 ACTIVE — QG sweep for f” vs `archive/2026_05/workspace_qg_sweep_2026_05_23.md:5,14`: “status: complete
  ... parent_epic: infrastructure_master”
  - why: The epic's own 'Assigned active plans' P0 section lists this plan as 🟠 ACTIVE features/ML-cluster work
    assigned to vm-ml, but the plan's own frontmatter (which the epic links to directly) says status: complete and
    parent_epic: infrastructure_master, not features_and_ml_master. An agent trusting the epic roster would be

- planned fix: Sync features_and_ml_master's workspace_qg_sweep status/ownership line to the plan's actual state.

#### [P0] epics/README.md ↔ epics/agent_operating_framework_master.md

- finding ids: 308,309
- **Epic registry completeness — README's canonical 20-epic table omits live epics** — `epics/README.md:164`: “## 20
  epics in 5 tiers” vs `epics/agent_operating_framework_master.md:23`: “tier: L5”
  - why: README.md (L14: 'This file is the SSOT for what epics are... how they map to VMs') presents a closed registry
    of exactly 20 epics across 5 tiers (L164-188), with the only L5 row being orchestrator_master.
    agent_operating_framework_master.md is a currently active (status: active, L8), P0-priority (L24), tier-L5 epic cre
- **assigned_vm dispatch model — epic-level VM ownership vs strict per-plan matching** — `epics/README.md:93`:
  “assigned_vm: vm-<id> # registry-resolved VM that owns this epic” vs `epics/agent_operating_framework_master.md:129`:
  “D2. assigned_vm is a mandatory per-plan field; epic-to-VM delegation is DROPPED for matching”
  - why: README.md's canonical epic frontmatter schema (no supersession banner, last_updated 2026-05-21) still documents
    assigned_vm as an epic-owning field resolved against a 'VM topology (10 VMs serving 20 epics)' registry
    (README.md:192-208, e.g. vm-defi/vm-cefi/vm-cross-cutting), and 5 other epics in this cluster still popu

- planned fix: Banner epics/README.md: registry table (20 epics, 2026-05-21) is missing
  agent_operating_framework_master + escalation_and_disaster_recovery_master; banner points to the live epic set until
  the table is regenerated. Full table rewrite = separate Q (see B-queue).

#### [P0] epics/agent_operating_framework_master.md ↔ epics/escalation_and_disaster_recovery_master.md

- finding ids: 338
- **Whether escalation_and_disaster_recovery_master (and its W9 broker hard-dependency) is live/dispatchable or pa** —
  `epics/agent_operating_framework_master.md:62-66`: “DEFER to next quarter: W7 ... W8 ... W9 (message broker /
  (role,domain) routing / POST /api/messages) ... and the role/escalation pilots (...
  `escalat”  vs  `epics/escalation_and_disaster_recovery_master.md:7`: “status: active”
  - why: agent_operating_framework_master's 2026-06-26 operator re-scope banner explicitly names 'the
    escalation_and_disaster_recovery_master epic' itself (plus its W9 broker dependency) as deferred to next quarter and
    slated for pausing. escalation_and_disaster_recovery_master's own frontmatter (created/last_updated 2026-06-25

- planned fix: Mark escalation_and_disaster_recovery_master status: paused + banner citing the AOF 2026-06-26 operator
  DEFER-to-next-quarter decision (W9 broker dependency deferred).

#### [P0] epics/batch_live_symmetry_master.md ↔ epics/instruments_master.md

- finding ids: 337
- **Status of canonical_id_p0_ccxt_live_batch_divergence_2026_07_08 (CCXT live vs batch instrument-id divergence a** —
  `epics/instruments_master.md:465-467`: “✅ canonical_id_p0_ccxt_live_batch_divergence_2026_07_08 — DONE,
  `instruments-service@8544273d` — all 13 canonical CeFi venues verified converged live=” vs
  `epics/batch_live_symmetry_master.md:77-84`: “status: 🔴 NEW ... canonical_id_p0_ccxt_live_batch_divergence_2026_07_08
  — the CCXT live adapter stores bare ccxt-native symbols; batch (Tardis) produc”
  - why: Both epics reference the identical child plan slug
    (../active/canonical_id_p0_ccxt_live_batch_divergence_2026_07_08.md — confirmed frontmatter status: complete,
    parent_epic: batch_live_symmetry_master). instruments_master marks it DONE with a resolving commit and 'all 13
    venues verified converged live=batch'. batch_liv

- planned fix: Cross-epic view of #19: batch_live_symmetry epic sync brings it in line with instruments_master's DONE
  entry.

#### [P1] ../cursor-configs/CLAUDE.md ↔ active/stash_pile_workspace_cleanup_2026_06_03.md

- finding ids: 72,73
- **Whether the `tab/<op>/N` branch model still exists for parking/inheriting WIP** —
  `active/stash_pile_workspace_cleanup_2026_06_03.md:83`: “**surface in report → owner confirms** (drop, or
  inherit-and-commit onto its own `tab/<op>/<N>` branch)” vs `cursor-configs/CLAUDE.md:126`: “the `tab/<op>/N` model is
  RETIRED — any such instruction is STALE”
  - why: This active P3 plan (last_updated 2026-06-27, same date CLAUDE.md's per-tab-worktrees rule cites) still
    instructs agents/owners to inherit orphaned WIP onto a `tab/<op>/<N>` branch. CLAUDE.md's HARD RULE says this exact
    branch model is retired workspace-wide and any instruction referencing it is stale. An agent executi
- **Existence of per-epic VMs (vm-defi/vm-cefi/vm-tradfi/etc.) to dispatch work to** —
  `active/stash_pile_workspace_cleanup_2026_06_03.md:117`: “Run stash audit + conservative sweep on **vm-defi**; commit
  report. — owner: vm-defi” vs `cursor-configs/CLAUDE.md:314`: “N slot workers, role-based dispatch (no per-epic VMs;
  single-VM architecture 2026-06-27)”
  - why: Phase 3 of this active plan dispatches 10 separate per-host todos to named epic VMs (vm-defi, vm-cefi,
    vm-tradfi, vm-sports, vm-prediction, vm-ml, vm-trading-core, vm-operator-ops, vm-cross-cutting, vm-orchestrator).
    CLAUDE.md's system map states the per-epic-VM model was retired in favor of a single central orchestrat

#### [P1] active/canonical_id_builder_retrofit_checklist_2026_07_08.md ↔ active/issues/instruments_docs_audit_outstanding_items_2026_07_08.md

- finding ids: 124
- **Whether the Deribit combo-leg builder retrofit (checklist's todo 5) is done or still unexecuted** —
  `active/issues/instruments_docs_audit_outstanding_items_2026_07_08.md:507-511`: “Still needs: the actual retrofit of
  `deribit_combo_adapter.py:310` to call it — tracked as its own todo in
  `canonical_id_builder_retrofit_checklist_20”  vs  `active/canonical_id_builder_retrofit_checklist_2026_07_08.md:112-116`: “Fix the real `:TYPE:`segment bug in Deribit's combo-leg builder — DONE 2026-07-09,`instruments-service@ca2f44e5`. New `\_classify_deribit_leg_instrum”
  - why: instruments_docs_audit_outstanding_items explicitly names the checklist's 'todo 5' as tracked-but-unexecuted,
    but that exact todo (the 5th checkbox, immediately after the on-chain-perp retrofit item) is checked [x] DONE with a
    real commit hash and evidence in the checklist itself. An agent trusting the audit doc could

#### [P1] active/capability_wizard_and_manifest_2026_06_11.md ↔ active/carry_staked_basis_funding_scan_experiment_2026_06_16.md

- finding ids: 291
- **Carry plan treats CarryStakedBasisRankAllocator/staked_basis.py as the authoritative batch==live production re** —
  `active/capability_wizard_and_manifest_2026_06_11.md:907-909`: “F27 — carry entry-emission was never the empty
  registry; strategy-service \_derive_structure calls accepted_perp_collateral with lowercase venue ids ag” vs
  `active/carry_staked_basis_funding_scan_experiment_2026_06_16.md:43`: “production path is `strategy-service`
  `CarryStakedBasisRankAllocator` + `engine/strategies/v2/carry_and_yield/ staked_basis.py`, batch == live”
  - why: The wizard plan documents (2026-06-12, still unresolved as of its last entry at
    capability_wizard_and_manifest_2026_06_11.md:1024) that the production staked-basis collateral-acceptance code has a
    case-mismatch bug making it ALWAYS return no accepted collateral for every venue — i.e. the live engine can never
    actually

#### [P1] active/capability_wizard_and_manifest_2026_06_11.md ↔ epics/strategy_master.md

- finding ids: 287,288
- **StrategyArchetype enum member count (55 vs 57, later 58)** — `epics/strategy_master.md:140-144`: “operator decision
  2026-06-01: the 28 implemented archetype engines are the intended May-23 rollout subset (NOT a regression vs the
  55-member
  `Strategy”  vs  `active/capability_wizard_and_manifest_2026_06_11.md:131`: “`extract_architecture_v2_capability_registry()`.
  Verified output: StrategyArchetype 57 values (count grew from audited 53 — 4 new archetypes landed)”
  - why: The epic carries a still-open (unchecked) P1 todo (F-34) directing whoever picks it up to fix a docstring/count
    from '53' to '55', premised on a 2026-06-01 operator decision that the enum has 55 members. The sibling
    capability_wizard plan, on the very same day the epic was last updated (2026-06-11), audited the actual
- **Epic's auto-populated active-plan index is missing this plan (and the carry plan) from its P0-P3 priority list** —
  `epics/strategy_master.md:99`: “\_8 active plans declare `parent_epic: strategy_master` in their frontmatter. Workers
  pick up in priority order (P0 first). Auto-populated by
  `scripts/”  vs  `active/capability_wizard_and_manifest_2026_06_11.md:19`: “parent_epic: strategy_master”
  - why: The epic's 'Assigned active plans' section claims to be auto-populated and lists exactly 8 plans across P0-P3,
    generated by a script last run 2026-05-21. Neither capability_wizard_and_manifest_2026_06_11.md nor
    carry_staked_basis_funding_scan_experiment_2026_06_16.md (both created after 2026-05-21, both declaring `pare

#### [P1] active/cefi_deribit_binance_futures_bundle_verification_2026_06_20.md ↔ active/mvp_backfill_cefi_tick_v10_2026_06_27.md

- finding ids: 28
- **Whether BINANCE-FUTURES/DERIBIT futures_chain gap is a fixable genuine-gap (needs VM relaunch) or a structural** —
  `active/cefi_deribit_binance_futures_bundle_verification_2026_06_20.md:77`: “futures_chain for BINANCE-FUTURES: 0
  captured, 13,334 attempted_failed (100% gap)... Backfill relaunch required” vs
  `active/mvp_backfill_cefi_tick_v10_2026_06_27.md:819`: “futures_chain Tardis channel absence confirmed —
  availableChannels shows NO futures_chain for: binance-futures, bybit, deribit, kraken-futures, bitfin”
  - why: The bundle-verification plan (status active, checked P0 items DONE 2026-06-12/06-24) diagnosed the
    BINANCE-FUTURES futures_chain gap as a genuine, capturable gap and marked its VM-relaunch action ✅ complete (14
    DERIBIT + 7 BINANCE-FUTURES VMs launched). The later mvp_backfill plan (2026-07-03) discovered via direct Tar

#### [P1] active/cefi_manifest_canonicalisation_2026_06_01.md ↔ archive/2026_06/instruments_manifest_canonicalisation_2026_06_01.md

- finding ids: 150
- **Owner-of-record for the cefi instruments-store v9 single-walk todo** —
  `active/cefi_manifest_canonicalisation_2026_06_01.md:1864-1868`: “Owner = the **cefi slice** of
  `instruments_manifest_canonicalisation_2026_06_01.md`; `--apply` **GATED on coordinator G0**” vs
  `archive/2026_06/instruments_manifest_canonicalisation_2026_06_01.md:26-28`: “✅ ARCHIVED 2026-06-26 — folded into
  instruments_mtds_subset_consistency_remediation_2026_06_17 (survivor I-2)...Lock cleared.”
  - why: cefi_manifest_canonicalisation (active, last_updated 2026-06-27 — one day AFTER the archival) still has an open
    [ ] P1 todo naming the archived/completed instruments_manifest_canonicalisation_2026_06_01.md as the live 'Owner',
    with no acknowledgment that its 8 open todos were folded into instruments_mtds_subset_consist

#### [P1] active/cicd_mvp_ldr_to_main_pipeline_2026_06_30.md ↔ active/issues/aws_codebuild_pr_approval_status_noise_2026_06_25.md

- finding ids: 347,86
- **Is the pipeline currently LDR→staging→main (staging live) or LDR→main direct (staging dormant/bypassed)?** —
  `active/issues/aws_codebuild_pr_approval_status_noise_2026_06_25.md:29`: “`staging→main` / `LDR→staging` promote PRs
  (observed on UTL #475, head `53852d11`)” vs `active/cicd_mvp_ldr_to_main_pipeline_2026_06_30.md:7`: “Staging is
  DORMANT (reversible switch kept). The promote gate set is exactly THREE things: SIT-green + quality-gates-v2 ...”
  - why: doc_b (created 2026-06-30, frontmatter/body explicitly declares itself 'the single SSOT for the simplified
    pipeline' and supersedes the whole prior CI/CD plan family) asserts staging is DORMANT and the only path is
    LDR→SIT→main direct. doc_a is an OPEN, unresolved issue (status: open, last_updated 2026-06-27) whose ent
- **promote-pipeline shape — staging-routed vs staging-dormant MVP** —
  `active/issues/aws_codebuild_pr_approval_status_noise_2026_06_25.md:28`: “The commit-status
  `AWS CodeBuild ap-northeast-1 (<repo>)` shows **`failure`** on automated `staging→main` / `LDR→staging` promote PRs
  (observed on UTL” vs `active/cicd_mvp_ldr_to_main_pipeline_2026_06_30.md:7`: “Staging is DORMANT (reversible switch
  kept).”
  - why: The still-open aws_codebuild issue (last_updated 2026-06-27) frames 'LDR→staging'/'staging→main' promote PRs as
    the live pipeline needing an AWS-side fix; three days later the operator-reaffirmed cicd_mvp plan (same parent_epic,
    active) declares staging DORMANT with LDR→main direct as the MVP default. The open issue ne

#### [P1] active/data_eng_role_vertical_pilot_2026_06_25.md ↔ epics/agent_operating_framework_master.md

- finding ids: 7
- **Dispatch state of the Data-Eng vertical pilot: epic says dispatched to harsh_pc, plan frontmatter says NA (nob** —
  `epics/agent_operating_framework_master.md:235`: “role `data_eng_role_vertical_pilot_2026_06_25` | W6 instance —
  Data-Eng (first full vertical; **dispatched harsh_pc**)” vs `active/data_eng_role_vertical_pilot_2026_06_25.md:15`:
  “assigned_vm: NA”
  - why: Per the epic's own locked dispatch rule D1/D3 (strict assigned_vm==backend matcher; NA -> dispatched to
    nobody), the plan's current frontmatter assigned_vm:NA means the pilot is NOT actually being executed by any
    backend, contradicting both the epic's summary table ('dispatched harsh_pc') and the plan's own body narrat

#### [P1] active/data_feed_sla_registry_and_active_self_healing_2026_06_19.md ↔ epics/observability_master.md

- finding ids: 202
- **data_feed_sla_registry_and_active_self_healing completion status** — `epics/observability_master.md:195`:
  “status\*\*: active — NEW 2026-06-19 from the "Operation Blue Flame" SLA-architecture comparison (operator). Two gaps
  where the external reference is tig” vs `active/data_feed_sla_registry_and_active_self_healing_2026_06_19.md:225`:
  “DONE. Both gaps from the Blue Flame comparison are closed and shipped; the plan's success criteria are met”
  - why: The epic hub (last_updated 2026-06-19) still describes the plan's two Blue-Flame gaps as open P1 work to be
    closed, but the plan's own body carries a 2026-06-20 final report declaring both gaps DONE and shipped end-to-end.
    An agent reading only the epic would treat already-completed work as live/pending.

#### [P1] active/data_pipeline_hardening_self_monitoring_2026_06_22.md (intra-doc)

- finding ids: 191,194
- **Whether Telegram is still a live alerting transport in alerting-service** —
  `active/data_pipeline_hardening_self_monitoring_2026_06_22.md:2063-2066`: “Slack is now the PRIMARY alerting transport
  — Telegram RETIRED (operator decision 2026-06-23) ...
  `_deliver_message`/`send_telegram`/deprecated-`slack”  vs  `active/data_pipeline_hardening_self_monitoring_2026_06_22.md:2081-2083`: “there is NO `alerting-slack-webhook-url`secret, but`alerting-telegram-bot-token`+`alerting-telegram-chat-id`
  DO exist → the generic path's PRIMARY”
  - why: One checked-done entry states `send_telegram` was REMOVED and Telegram fully RETIRED as of 2026-06-23; a second
    entry in the same doc, dated the same day, diagnoses the generic incident path as still using Telegram as its
    PRIMARY channel (driven by existing SM secrets). If send_telegram was truly removed, the incident
- **Completion status of the 8th C6 reader-bucket-env bug fix** —
  `active/data_pipeline_hardening_self_monitoring_2026_06_22.md:303-304`: “[~] [CODE] P1. **Fix the 8 C6
  reader-bucket-env bugs** the parity check found — **7 of 8 SHIPPED on origin/LDR** ... **8th site —
  `live/websocket_runn”  vs  `active/data_pipeline_hardening_self_monitoring_2026_06_22.md:1216-1223`: “**FOLLOW-UP (C6 / DP-ENV-001, non-prediction) — SHIPPED ON LDR (verified 2026-06-22 resume-run)\*\*: `websocket_runner._read_is_parquet_sync`
  now resolv”
  - why: The todo checkbox is left in partial state `[~]` claiming 1 of 8 sites remains deferred, while a later entry in
    the same document confirms all 8 sites (including the exact deferred one) are shipped and verified on LDR with 'No
    further action.' The stale `[~]` marker could cause a worker to re-attempt already-completed

#### [P1] active/data_pipeline_hardening_self_monitoring_2026_06_22.md ↔ active/issues/dp_event_pubsub_delivery_gap_2026_06_22.md

- finding ids: 192
- **Whether the DP\_\* PubSub→subscriber→Slack relay was actually delivering alerts on 2026-06-22** —
  `active/issues/dp_event_pubsub_delivery_gap_2026_06_22.md:120-122`: “**RELAY NOW LIVE END-TO-END (2026-06-22
  18:27Z)**: emit (mode=live → lifecycle-events) → subscriber consumes lifecycle-events-sub (no 403) → route_eve” vs
  `active/data_pipeline_hardening_self_monitoring_2026_06_22.md:961-963`: “the alerting subscriber IS running ... the
  messages DO land ... YET 0 DP events routed in 14 min. Root cause: UTL PubSubEventSink.write_event publishe”
  - why: The issue doc declares the relay definitively 'LIVE END-TO-END' at 18:27Z and later (still open, `last_updated`
    2026-06-27) lists only cosmetic/durability items as remaining ('NOT blocking the relay — it is live'). The related
    plan (same day) subsequently proves DP\_\* events were silently dropped before Slack due to an un

#### [P1] active/defi_collateral_sizing_and_wizard_full_parameterization_2026_06_17.md ↔ active/issues/e2e_defi_config_taxonomy_wizard_roundtrip_2026_06_17.md

- finding ids: 296
- **Drift LST collateral haircut values for SOL/mSOL/JitoSOL: 0.05/0.10/0.10 (e2e doc) vs updated real 0.15/0.20/0** —
  `active/issues/e2e_defi_config_taxonomy_wizard_roundtrip_2026_06_17.md:91-92`: “USDC(0), SOL(0.05), **mSOL(0.10
  `# PLACEHOLDER`)**, JitoSOL(0.10) — `venue_collateral.py:112-125`. NOT stables-only.” vs
  `active/defi_collateral_sizing_and_wizard_full_parameterization_2026_06_17.md:187`: “a F28 live-probe (UAC@bc45549,
  ~2026-06-17) updated Drift haircuts to real on-chain initialAssetWeight (SOL/mSOL/JitoSOL = 0.15/0.20/0.20, were 0.10
  p”
  - why: Both docs are dated 2026-06-17 and cite the same venue_collateral.py source, but the e2e-taxonomy issue
    (status: open, still presented as current fact) never got the F28 live-probe update noted in the sibling plan — a
    reader of the still-open e2e doc would use the wrong (stale/placeholder) haircut numbers for a data-co

#### [P1] active/defi_manifest_canonicalisation_2026_06_01.md ↔ active/issues/cefi_hl_aster_batch_data_gaps_2026_06_22.md

- finding ids: 156
- **ASTER CeFi funding-carrier (derivative_ticker) capture status — 100% failed vs 62% captured/ok** —
  `active/defi_manifest_canonicalisation_2026_06_01.md:1462-1463`: “E1 CeFi `derivative_ticker` (funding carrier) fetch
  failures: OKX-FUTURES + ASTER 100% attempted_failed; refresh to current (stale ~3–5 weeks).” vs
  `active/issues/cefi_hl_aster_batch_data_gaps_2026_06_22.md:40`: “**ASTER** ... | derivative_ticker (funding) | 62% |
  ok |”
  - why: defi_manifest_canonicalisation's still-open P0 item E1 (unchanged since the plan's 2026-06-01 creation) asserts
    ASTER's derivative_ticker (the funding carrier the DeFi-hybrid hedge leg needs) is 100% attempted_failed and stale
    3-5 weeks. The newer cefi_hl_aster_batch_data_gaps issue doc's 2026-06-22 runtime/manifest au

#### [P1] active/defi_manifest_canonicalisation_2026_06_01.md ↔ active/solana_defi_legacy_migration_2026_05_27.md

- finding ids: 155
- **Solana pool data_type: merged into one dex_pool_state vs still-separate dex_pools+SOLANA_AMM_POOL** —
  `active/defi_manifest_canonicalisation_2026_06_01.md:1601-1605`: “canonical Solana types per that plan are
  `dex_pools`+`SOLANA_AMM_POOL` ... vs the MVP's `DEX_POOL_STATE` ... — **complementary, not conflicting** (dif” vs
  `active/solana_defi_legacy_migration_2026_05_27.md:42-46`: “**NEW — `dex_pool_state` is now the UNION of EVM + Solana
  pool state under ONE data_type** (operator 2026-06-01) ... `SOLANA_AMM_POOL`/`SOLANA_VAULT` ”
  - why: defi*manifest_canonicalisation's own A11g item (same file, L854-864, operator-decided 2026-06-05) explicitly
    states the union is lossless and 'no second data_type is warranted (the solana_defi_legacy_migration G-note
    "complementary" view is superseded by the union being a superset)', and the sibling solana_defi_legacy*

#### [P1] active/defi_pipeline_e2e_and_coverage_validation_2026_06_20.md ↔ epics/defi_master.md

- finding ids: 47
- **Lighter/Pacifica historical-replay backfill required start-date vs actual verified data range** —
  `epics/defi_master.md:330`: “Lighter + Pacifica OHLCV non-empty 2024-08-01+ / 2025-06-01+ respectively; Extended
  pending Phase 0 empirical research before any VM launch” vs
  `active/defi_pipeline_e2e_and_coverage_validation_2026_06_20.md:80-82`: “GCS verified 2026-06-16: LIGHTER-ZKSYNC 1590
  parquets (BTC/ETH/HYPE/SOL/TON × 319 days, 2025-05-01→2026-05-06); PACIFICA-SOLANA 1408 parquets (ETH/HYP”
  - why: The epic's Critical Path table (unsuperseded — header carries no '— SUPERSEDED 2026-06-20' marker, unlike the
    frozen sections below it) sets the success gate as OHLCV non-empty from 2024-08-01 (Lighter) and 2025-06-01
    (Pacifica). The child plan's own P0 todo, checked done (✅) on the strength of a 2026-06-16 GCS verific

#### [P1] active/deployment_observability_expansion_2026_07_08.md ↔ active/deployment_observability_parity_live_batch_paper_2026_06_22.md

- finding ids: 196
- **Deployments-page UI architecture (tabs vs merged table)** —
  `active/deployment_observability_parity_live_batch_paper_2026_06_22.md:122`: “A **Deployments** page at `/deployments`
  mirroring RepoCi grade: umbrella tabs (**Live / Batch / Paper**), each a matrix of VMs+Cloud-Run-jobs” vs
  `active/deployment_observability_expansion_2026_07_08.md:52`: “Merged Deployments tab — SHIPPED. live/batch/paper
  collapsed into ONE flat all-modes table (Mode is a filter, not tabs); 3 cockpit tabs + 3 health til”
  - why: Parity plan (status active, last_updated 2026-06-27) checked off and still presents a Live/Batch/Paper-TAB
    Deployments page as the shipped architecture (deployment-ui@051c255). The newer expansion plan (created 2026-07-08)
    explicitly collapsed that exact tab design into ONE flat table with Mode as a filter (deployment-

#### [P1] active/deployment_observability_expansion_2026_07_08.md ↔ epics/observability_master.md

- finding ids: 324
- **observability_master active-child-plan count** — `epics/observability_master.md:99-100`: “"13 active plans declare
  parent_epic: observability_master in their frontmatter...Auto-populated by
  scripts/plans/populate_epic_bodies_2026_05_21.py."” vs
  `active/deployment_observability_expansion_2026_07_08.md:11,27`: “status: active / parent_epic: observability_master
  (last_updated 2026-07-08)”
  - why: Epic claims 13 active children; grep shows 24 currently exist (including deployment*observability_expansion,
    deployment_obs_ui_popover_health, phantom_captures*_ issue docs, manifest*hygiene_red*_ — all dated
    2026-06-2x/07-0x), none of which appear anywhere in the epic body's P0/P1/P2 sections (only 1 P0 item + 1 P1 it
