---
doc_type: issue
title: "plan_reconciler daily run findings — defi tranche, 2026-08-09"
summary:
  Run-findings doc / progress journal for the plan_reconciler defi-tranche sharded run, dispatch agt-2d9a32. DETECT
  (multi-agent fan-out) -> VERIFY (adversarial) -> APPLY (confirmed only) -> ROUTE (hard findings), scoped to
  defi-tranche primary docs (asset_group defi, single/first-listed tag) plus the corpus-wide normative refs and codex.
status: open
nature: issue
asset_group: [defi]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan_reconciler, reconciliation, plan-hygiene, findings, defi]
related: []
created: "2026-08-09"
parent_epic: defi_master
priority: P2
estimate_class: research
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 1.2
assigned_role: review
assigned_vm: planning
execution_scope: orchestrator-agent
locked_by: plan_reconciler
locked_since: "2026-08-09"
supersedes:
superseded_by:
resolved_by:
source: "slot 26, plan_reconciler agt-2d9a32, 2026-08-09"
context_scope:
  [
    unified-trading-pm/scripts/plan-hygiene/run_hygiene_sweep.sh,
    unified-trading-pm/agents/plan_reconciler.md,
    unified-trading-pm/cursor-configs/skills/plan-reconcile/SKILL.md,
    unified-trading-pm/plans/epics/defi_master.md,
    unified-trading-pm/plans/active/defi_consolidated_closeout_2026_07_18.md,
  ]
drift_direction: advance-code
depends_on: []
---

# plan_reconciler daily run findings — 2026-08-09 (defi tranche)

Dispatch `agt-2d9a32`, slot 26. Tranche: **defi**. Review branch: `plan_reconciler/agt-2d9a32`.

Scope per `cursor-configs/skills/plan-reconcile/SKILL.md` § "Topic-scoped (sharded) runs": primary defi docs
(asset_group contains `defi` as the first-listed / sole competing-AG tag — see Coverage section for the exact rule +
counts) + corpus-wide normative refs (`PLAN_FORMAT.md`, `task_template.md`, `INDEX.md`, `ACTIVE_INDEX.md`) + codex
(evidence only, never edited).

## Flips verified

1. `defi_pipeline_mode_source_desync_yearn_v3_2026_07_21.md` Todo 5 (F10 register-append) —
   `unified-trading-pm@ad8d3e1ba`. F10 verified present at `/codex/02-data/canonical-cutover-register.md:136`, shipped
   `unified-trading-pm@0c4172c31` (2026-07-26, `git merge-base --is-ancestor`-verified). Last open todo — doc now fully
   done, marked `archive_exempt: true` (2 of 10 corpus referrers are grace-window-locked this run; see Archive
   candidates).
2. `defi_cefi_venue_chain_axis_contamination_2026_07_28.md`'s "IS data gap hypothesis DISPROVED" todo —
   `unified-trading-pm@de7449df5`. Investigation concluded (root cause redirected to
   `cefi_fwd_backfill_vm_deleted_by_sa_within_10min_2026_08_08.md`), item already absent from the doc's own "Deferred
   after 2026-08-08" list.
3. `mtds_qg_red_uac_capability_declaration_drift_2026_08_05.md`'s sole follow-up todo — `unified-trading-pm@82e4f4dcc`.
   Not a status flip — a markdown-syntax fix: the todo was wrapped in stray backticks, making the line start with a
   backtick instead of `[`, invisible to `count_open_tasks.py`'s regex and every other mechanical checker. Restored
   valid syntax; no content changed.

## Contradictions

**Applied (HARD-evidenced, fixed this run):**

1. **Fabricated ruling-date + unfilled `<sha>` placeholder** —
   `over_cap_live_plan_is_permanently_unverdictable_2026_08_02.md` Todo 1/2 claimed a 2026-08-06 operator ruling +
   unfilled `<sha>` for a 2026-08-07 implementation. `git log` on `check_line_caps.sh` shows the real commit
   (`d4f7fab9d`) landed 2026-08-02, matching the doc's OWN 2026-08-04 Progress Log entry (which already said "operator
   ruling 2026-08-02"). The underlying work was genuinely done — only the citation was wrong. Fixed
   `unified-trading-pm@7660255fd`. **Flagged for operator awareness** (not just a typo — a `[x]` DONE checkbox with a
   fabricated evidence citation on a HARD-RULE-governed policy gate shipped into the corpus and survived 4+ subsequent
   audit passes unnoticed).
2. **5 stale finalize-doc gating-todo counts** — `defi_satellite_ao_dispatch_batch{2,3,6,9}_..._finalize.md` +
   `defi_jupiter_venue_registration_and_live_connector_wireup_finalize_2026_08_07.md` each cited the wrong total todo
   count for their `depends_on`/`gate_on_depends` source plan (independently recounted via `grep` on the live source
   docs). Jupiter's was the highest-risk (6 vs actual 8 — the 2 uncounted todos' evidence would never have been
   re-verified once the gate releases). Fixed `unified-trading-pm@f7d8680d2`.
3. **2 stale sub-items in `defi_satellite_ao_dispatch_batch2_2026_07_26_finalize.md` Todo 3** — one archival target
   already archived (`unified-trading-pm@bec54efeb`), one retag target moved to archive with its mistag still
   uncorrected. Annotated in place (action still valid, just needs the new path) — `unified-trading-pm@f7d8680d2`.
4. **Census undercount + stale HYPERLIQUID citation** — `defi_cefi_venue_chain_axis_contamination_2026_07_28.md`'s
   title/summary said "14 non-DeFi tokens / 5 CeFi names"; the doc's own 2026-07-30 root-cause entry already found
   BINANCE was undercounted (real: 15/6). Separately, its "2 already-known/tracked" line cited a doc for HYPERLIQUID
   that the doc's own 2026-08-04 self-correction already found has zero HYPERLIQUID mentions. Fixed
   `unified-trading-pm@de7449df5`.
5. **17 dangling refs in `defi_master.md` epic (LOCKED)** — 5 in frontmatter, 2 routing-table rows citing superseded
   plans without naming their real successor (`superseded_by:` field points at
   `data_completion_to_100_all_ag_2026_06_21`, never otherwise referenced in the epic), 8 in the "Assigned active
   plans"/"Referenced sub-plans" sections, 1 corpus-wide manifest-schema version claim ("v5", codex says v9), 1
   within-doc contradiction (critical-path table's tail-chain row vs. the doc's own later "DIAGNOSIS COMPLETE... no
   action needed" entry). `locked_by:` blocks archival/auto-unlock only, not general content correction — all
   HARD-evidenced (git `superseded_by`/`status` fields, `ls`-verified new paths, codex cross-check). Fixed
   `unified-trading-pm@5c54e737e`. Also fixed an unrelated pre-existing gap the file's own pre-commit scan surfaced (an
   "operator ruling" citation with no traceable doc pointer, 300+ chars away from any `/plans/`/`/codex/` reference) —
   found the real source (`plan_reconciliation_operator_decisions_2026_07_11.md:117`) and cited it.
6. **`execution_scope`/`assigned_vm` frontmatter mismatch** —
   `deployment_ui_capability_bundle_stale_drift_pacifica_2026_07_16.md`'s 2026-08-08 deliberate flip (`assigned_vm: NA`
   → `planning`) never updated `execution_scope` (still `local-only`). Fixed `unified-trading-pm@86f48eeda`.

**Confirmed but NOT applied (grace-protected or genuinely ambiguous — routed below, see "Filed"):**

7. `defi_pipeline_e2e_and_coverage_validation_2026_06_20.md`'s **E3 ambiguity** — two docs both use the label "E3" for
   what may or may not be the same "recursive-staking borrow leg": `defi_strategy_pnl_axis_index_2026_07_24.md` claims
   SHIPPED (`strategy-service@23bd8b76`, independently verified reachable) while
   `lst_rate_honest_coverage_2026_07_21.md` Phase 6's own E3 says "Not started".
   `lst_rate_honest_coverage_2026_07_21.md` is in the 12h grace window — cannot verify/fix this run. Genuinely
   unresolved; needs a same-run read of both docs' full E3 context to disambiguate.
8. `defi_strategy_pnl_axis_index_2026_07_24.md`'s own internal tension — claims E3 "SHIPPED" then, 2 paragraphs later,
   frames it as still-Phase-1-pending ("check its result first, then continue Phase 2"). Same doc is
   `archive_exempt: true` (standing reference hub) so its checkbox state isn't itself misleading, but the prose
   contradiction is real.

## Doc-drift (plan vs codex — flagged only, per HARD RULE never auto-fixed)

**Codex-vs-codex drift (routed as a big finding, see "Filed"):**

1. **`/codex/09-strategy/architecture-v2/archetypes/carry-staked-basis.md`** (SSOT for the May-23 LEAD DeFi archetype,
   `implementation_status: code-shipped`) still lists `DRIFT` as a live `perp_venue` in its frontmatter
   `venue_universe`, its "Today's matrix" table (2 of its claimed "4 live slots"), and its config-schema example — but
   `/codex/02-data/instrument-pipeline-defi.md` and `/codex/02-data/defi-data-types-catalog.md` both explicitly document
   DRIFT + PACIFICA as "REMOVED 2026-07-16" (adapters deleted). The flagship archetype doc's own claimed live slot count
   is a ~50% overstatement (really 2 live slots, not 4). This is codex-vs-codex, not plan-vs-codex — I cannot edit
   either side without an operator ruling on which is authoritative (though the removal doc is dated later and cites a
   concrete deletion commit, so it looks like the stronger side).
2. **`/codex/02-data/defi-data-types-catalog.md`** self-contradicts its own DeFi-adapter count in 3 places within the
   SAME doc: "49 DeFi adapters" (summary), "47 DeFi adapters total" (pipeline-stages diagram), "50 DeFi adapters" (Key
   Files section).
3. **`/codex/02-data/instrument-pipeline-defi.md`** was touched as recently as 2026-07-16 (added a drift/pacifica
   removal note) but was never updated for the EARLIER 2026-07-11 Lighter-ZKSYNC/Extended-Starknet reclassification
   (DeFi → CeFi) — still lists `lighter` in its DEX adapter list with no annotation.
4. **`defi_oracle_family_empty_path_exception_classification_2026_08_09.md`** (grace-protected, context-only) treats
   Aave as a 3rd `oracle_prices` source sharing `oracle_prices_handler.py`'s context; `defi-data-types-catalog.md` §13
   documents only 2 (Chainlink + Pyth). Unclear which side is stale without reading the handler directly — flagged, not
   resolved.

**Parent_epic mechanical-adjudicator verdicts (10 sweep-flagged candidates, judged by hunter H7, none auto-applied
except #1):**

- **RECLASSIFY** (applied — see Hygiene fixes): `defi_archetype_universe_no_curtailment_mechanism_2026_07_23.md` →
  `defi_master` (asset_group is `defi`-sole; ~60% of the doc is DeFi archetype build-execution content the epic's own
  Codex-SSOTs section claims as in-scope).
- **KEEP** (9 of 10 — heuristic false positives, following a consistent corpus convention of routing
  pipeline/manifest/CI bugs to `infrastructure_master` and cross-AG syntheses to `instruments_master` regardless of
  asset_group headline): `instruments_remaining_work_audit_2026_07_10.md`,
  `defi_onchain_dep_check_blazestake_lstrates_stalls_2026_08_06.md` (grace),
  `defi_oracle_family_empty_path_exception_classification_2026_08_09.md` (grace),
  `defi_pipeline_mode_source_desync_yearn_v3_2026_07_21.md`,
  `defi_sushiswap_uniswap_bare_version_factory_gap_2026_07_21.md` (grace),
  `defi_turbo_api_hides_real_captured_data_2026_07_07.md`, `mtds_is_full_adapter_smoketest_findings_2026_07_07.md`,
  `mtds_pipeline_check_enumerate_shards_masks_cefi_sports_mvp_2026_08_06.md` (clear false-positive, doc's own
  asset_group doesn't even include defi), `mtds_qg_red_uac_capability_declaration_drift_2026_08_05.md`.

## Hygiene fixes

- `defi_cefi_venue_chain_axis_contamination_2026_07_28.md`: fixed a wrong script-path citation
  (`market-tick-data-service/scripts/rebuild_defi_manifest.py` → real path adds the `market_tick_data_service/` package
  segment), 2 occurrences — `unified-trading-pm@de7449df5`.
- `defi_archetype_universe_no_curtailment_mechanism_2026_07_23.md`: `parent_epic` corrected `strategy_master` →
  `defi_master` per the mechanical-adjudicator verdict above.

## Filed (durable — routed for operator/future-run attention)

1. **[BIG FINDING — codex-vs-codex SSOT drift]** `carry-staked-basis.md` overstates its own live venue-slot count by
   ~50% (still lists removed venue DRIFT as live) — see Doc-drift #1. Needs an operator ruling on which side is
   authoritative before any codex edit (this run never edits codex per HARD RULE). **Filed via `/blocked` this run —
   `BLK-93641898`** (options A/B/C, recommendation A, `can_continue: true`).
2. **[Contradiction, currently latent]** `defi_morpho_lending_indices_never_wired_2026_07_12.md`'s
   `depends_on`/`gate_on_depends` chain watches `data_completion_defi_2026_07_15`'s own todo completion, but that plan's
   own text says the real signal moved (twice) to a doc that didn't exist when this gate was authored
   (`defi_track5_coverage_mvp_backfill_2026_07_24.md`, itself gated on `defi_consolidated_closeout_2026_07_18`).
   `assigned_vm: NA` today so it hasn't misfired — but is structurally wrong and would misfire if/when promoted. Needs
   the `depends_on` target corrected to the real current gate.
3. **[Contradiction]** E3 ambiguity between `defi_strategy_pnl_axis_index_2026_07_24.md` (claims shipped) and
   `lst_rate_honest_coverage_2026_07_21.md` Phase 6 (claims not started) — see Contradictions #7. Blocked on
   `lst_rate_honest_coverage`'s grace window this run.
4. **[Archive-ready, referrer-blocked]** `defi_pipeline_mode_source_desync_yearn_v3_2026_07_21.md` — all 5 todos now
   done, unlocked, but 2 of 10 corpus referrers (`defi_satellite_ao_dispatch_batch10_2026_08_06.md`,
   `defi_consolidated_closeout_2026_07_18.md`) are grace-window-locked this run. Marked `archive_exempt: true`
   (temporary) — a future pass should archive once those referrers clear grace.
5. **[Doc-drift]** `defi-data-types-catalog.md`'s self-contradicting adapter count (49/47/50) — see Doc-drift #2.
6. **[Doc-drift]** `instrument-pipeline-defi.md` never updated for the 2026-07-11 Lighter reclassification — see
   Doc-drift #3.
7. **[Under-evidenced, cross-hunter]** `defi_satellite_ao_dispatch_batch10_2026_08_06.md` (grace-protected) claims (via
   checkbox citation-close) the DeFi MVP backfill is 100% done, but its OWN cited source doc
   (`defi_track5_coverage_mvp_backfill_2026_07_24.md`) has that exact todo still open with an explicit "unresolved... no
   cell can be called PROVEN" status in a separate section. Neither doc cross-references the other's contradicting
   claim. Cannot fix this run (batch10 is grace-protected); needs a real re-verify once grace clears.
8. **[Minor, low-confidence]** `features_onchain_featureless_shards_and_vocabulary_split_2026_07_20.md` (open, P0) vs
   `features_service_manifest_coverage_gap_2026_08_03.md` — possible reconciliation on a specific `perp_funding_rates`
   feature-group object; hunter explicitly flagged this as unconfirmed (needs a parquet column-content check, not just
   manifest presence), not asserting a contradiction.
9. **[AO-dispatch-readiness]** `instruments_service_defi_golden_red_capability_lockstep_gap_2026_08_05.md`'s open OPS
   todo references a stale AO-backlog ID (`sports_consolidated_native_ao_extract-022`) not found in the current live IDs
   (which now run through -028/-029) — worth a live backlog check before this todo dispatches.
10. **[AO-dispatch-readiness]** `defi_catalog_engine_config_key_contract_drift_2026_07_23.md` carries
    `assigned_vm: planning` but both remaining open todos are `[OPERATOR]`-tagged design decisions — zero
    worker-dispatchable todos remain. Not urgent (workers correctly escalate `[OPERATOR]` items rather than misfire),
    but worth confirming whether it should revert to `NA`.

## Archive candidates (operator review)

- `defi_pipeline_mode_source_desync_yearn_v3_2026_07_21.md` — fully done (0 open, 5 done), unlocked, non-grace. **NOT
  archived**: 2 of 10 corpus referrers are grace-window-locked this run (see Filed #4). `archive_exempt: true` set as a
  temporary marker.
- `defi_strategy_pnl_axis_index_2026_07_24.md` — 0 open native checkboxes, but carries `archive_exempt: true`
  (pre-existing, well-evidenced: standing reference hub aggregating pointers to still-live linked docs). Confirmed
  correct — NOT an archive candidate despite the zero-open-todo signal.
- `ag_closeout_audit_defi_parked_2026_08_06.md` + `_08_07.md` — per hunter H3's classification, both fully subsumed by
  `ag_closeout_audit_defi_parked_2026_08_08.md`'s re-verification; good archival candidates for a future pass (not
  archived this run — zero-checkbox docs need the CONVERT-vs-ARCHIVE decision to be deliberate, not bundled into an
  already-large batch).

## Refuted (dropped by verify)

- None of the 8 hunters' candidates were refuted on independent re-check this run — every HARD-evidence claim I
  spot-verified (dangling-ref target existence, commit-sha reachability, git-log dates, grep-recounted todo totals)
  matched the hunter's report. (This does not mean every hunter finding was actioned — see Filed for the ones routed
  instead of applied.)

## Coverage (hunters / batches / docs)

- **8 hunters dispatched** (general-purpose, sonnet, `SUB_AGENT_MANDATORY_RULES.md` pasted in full at each spawn): H1
  epic-cluster (`defi_master.md` solo, 1832L), H2 satellite-dispatch-batch cluster (14 docs), H3 zero-checkbox + small
  process docs (13 docs), H4 venue/adapter/archetype issue docs (4 docs, ~3100L), H5 pipeline/manifest/instruments
  - `data_completion_defi_2026_07_15.md` (6 docs), H6 features/instruments/deployment cluster (7 docs), H7 mechanical
    adjudicator (10 parent_epic candidates) + codex-alignment (4 codex docs opened), H8 topic hunter (corpus-wide grep
    sweep across defi venue/provider/completion-claim themes, 8 grep passes).
- **Docs read in full this run**: 47 non-grace primary defi docs (all of them, across the 8 batches) + `defi_master.md`
  epic + `defi_consolidated_closeout_2026_07_18.md` (966L, grace, read-only context) + 4 codex docs (H7 Part C) + the 34
  grace-window docs were available as read-only context to hunters that needed them for cross-checking (not
  independently full-read by every hunter).
- **Primary defi tranche**: 81 docs total, 34 in the 12h grace window (READ-ONLY this run), 47 actionable.
- **9 checkpoint commits** landed on the review branch (`plan_reconciler/agt-2d9a32`), each pushed immediately.
- **Verified/refuted tally**: every hunter-reported HARD-evidence claim I independently spot-checked (dangling-ref
  targets via `ls`/`find`, commit shas via `git merge-base --is-ancestor`, dated git-log entries, grep-recounted totals)
  confirmed on re-check — 0 refuted.

## Plans not reached

- The 34 grace-window primary defi docs were not independently re-verified this run (by design — read-only). Their
  content was used as context where a hunter cited it, but no hunter was assigned a full independent read-and-verify
  pass over the full grace set (would be the natural target once their 12h window clears).
- 25 SECONDARY (multi-AG) docs where defi is present but not the primary/first-listed tag were not read this run (out of
  scope — belongs to their primary tranche or the cross-cutting shard), except where a hunter's grep swept them
  incidentally (H8's corpus-wide topic grep) or where fixing a defi-primary doc's dangling ref happened to touch one
  (`defi_cefi_venue_chain_axis_contamination_2026_07_28.md` is itself `asset_group: [defi, cefi, tradfi, cross-cutting]`
  — edited anyway since the fixes were mechanical/low-risk regardless of tranche ownership nuance).

## No-miss ledger (Phase 5.9)

- **routed_to_operator == parked_in_issue_doc**: 10 == 10 (every item in "Filed" above is a confirmed finding this run
  could not or should not auto-fix; nothing was routed verbally/in-chat-only). Big finding #1 (codex-vs-codex drift)
  additionally alerted via `/blocked` (see STEP 6 below).
- **agent_skips == enumerated**: N/A this run — no apply-sub-agent was spawned in STEP 5 (all fixes applied inline by
  the orchestrator given the manageable candidate count), so there is no skip list to reconcile.
- **Conservation on moves**: N/A — no fold/consolidation moves performed this run (only in-place edits + one
  `archive_exempt` marker, no content relocated between docs).
- **Verified-at-HEAD**: every commit's actual landed content was checked via the post-commit `git diff --stat` +
  targeted `grep`/`wc -l` shown in-session before moving to the next fix, not assumed from the commit message alone.

## Phase-0 inventory snapshot (2026-08-09, via scratch script — see run findings for the exact rule)

- Corpus scanned: 724 docs (`plans/active` + `plans/active/issues` + `plans/epics`)
- PRIMARY defi docs: 81 (defi is the sole or first-listed competing-AG tag in `asset_group`)
- SECONDARY (multi-AG, defi present but not primary — context-only, NOT edited this run): 25
- GRACE-WINDOW primary defi docs (<12h old, READ-ONLY this run): 34
- FULLY-DONE candidate (non-grace): 1 — `defi_strategy_pnl_axis_index_2026_07_24.md`
- NEAR-COMPLETE candidate (non-grace, exactly 1 open): 1 — `defi_satellite_ao_dispatch_batch3_2026_07_26_finalize.md`
- ZERO-CHECKBOX docs: 5
- Locked primary defi docs (never auto-archived/unlocked): 7 (incl. `plans/epics/defi_master.md`)
- Over-soft-cap (>500L non-epic): 17; over-hard-cap (>1000L): 2 (`data_completion_defi_2026_07_15.md`=1005L,
  `lst_rate_honest_coverage_2026_07_21.md`=1009L)
- Primary defi checkbox totals: open=230 done=439
