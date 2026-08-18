---
doc_type: issue
title: "plan_reconciler tradfi-tranche deep reconciliation run — 2026-08-18"
summary: >-
  Run-findings doc for a sharded, autonomous /plan-reconcile pass over the tradfi tranche (97 docs), dispatch
  agt-15d58e, slot 28. Phase -1 reconciles the prior 2026-08-16 findings doc against fresh state first; Phase 1
  fans out 9 size-balanced (~310KB) read-only hunter batches covering every remaining tradfi doc in full,
  adversarially verifies every candidate, auto-fixes the verified-easy, routes the hard ones.
status: open
nature: issue
asset_group: [tradfi]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan_reconciler, reconciliation, tradfi, sharded]
related: [/plans/active/tradfi_consolidated_closeout_2026_07_18.md, /plans/active/issues/plan_reconciler_findings_tradfi_2026_08_16.md]
created: 2026-08-18
author: plan_reconciler
source: agt-15d58e
parent_epic: tradfi_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline: 0.1
calibrated_ai_days: 0.1
assigned_role: backend_engineer
drift_direction: fix
resolved_by:
locked_by: plan_reconciler-agt-15d58e
depends_on: []
context_scope:
  [
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /plans/active/issues/plan_reconciler_findings_tradfi_2026_08_16.md,
    /cursor-configs/skills/plan-reconcile/SKILL.md,
  ]
---

# plan_reconciler tradfi-tranche run — 2026-08-18

Dispatch `agt-15d58e`, slot 28, tranche `tradfi`. Corpus: 97 docs under `plans/active/` + `plans/active/issues/`
tagged `asset_group: tradfi` (via `generate_tranche_doc_inventory.py --tranche tradfi`), up from 86 on 2026-08-16.

**Working-tree note**: `PM_REPO_PATH` supplied at boot pointed at the canonical ROOT clone
(`/home/ubuntu/unified-trading-system-repos/unified-trading-pm`), which RULES.md marks READ-ONLY. All work in this
doc/run happened in the slot-local clone (`.tabs/28/unified-trading-pm`, same `origin` remote) per the explicit
"never edit/commit/run work in root clones" guardrail — flagging in case the boot-variable wiring itself needs a
fix (not a tradfi-tranche finding, out of scope to chase further here).

## Phase -1 — prior findings doc reconciliation (done FIRST, before any fresh sweep)

`plan_reconciler_findings_tradfi_2026_08_16.md` existed (last touched 2026-08-17 08:14 UTC by na-eligibility-audit,
18h old at run start — outside the 12h grace window). Re-checked its 5 still-open items against fresh state:

| # | Item | Prior status | Fresh verdict | Evidence |
| --- | --- | --- | --- | --- |
| 5 | Archive `tradfi_canonical_path_migration_design_2026_07_19.md` | archival-deferred (43 referrers) | **STILL-OPEN ORDINARY-WORK** | Already correctly extracted to `tradfi_satellite_ao_dispatch_batch15_2026_08_17.md` Todo 6 (`status: active`, `assigned_vm: planning`, unlocked) — genuine bounded AO-eligible work already queued, not re-executed here to avoid racing the dispatched batch |
| 6 | `[OPERATOR]` tag fix on `uac_data_type_validity_combinator_fragmentation_2026_07_07.md` (split-blocked) | over 1000L hard cap (1010L) | **STILL BLOCKED** — unchanged | `wc -l` now shows 1008L — still over the 1000-hard line-cap; any commit touching it is hook-rejected. Genuinely operator-gated (splitting a 1000+L doc is a planning decision) |
| 7 | Reference-path ratchet regression (batch7 refs in `tradfi_consolidated_closeout_2026_07_18.md` ×2 + `tradfi_satellite_ao_dispatch_batch8_2026_08_08.md` ×2) | grace-blocked | **RESOLVED** (done-but-unchecked) | `grep -n 'batch7_2026_08_06' plans/active/tradfi_consolidated_closeout_2026_07_18.md` → both refs (L64-65) already point to `/plans/archive/2026_08/tradfi_satellite_ao_dispatch_batch7_2026_08_06.md`(+`_finalize`), not the stale active path. The 2nd referrer doc (tradfi batch8) is itself now archived (`plans/archive/2026_08/tradfi_satellite_ao_dispatch_batch8_2026_08_08.md`) — its internal refs are historical, no longer live-corpus. **Could not flip the checkbox at its tracking location** (`tradfi_satellite_ao_dispatch_batch15_2026_08_17.md` Todo 7) — that doc is itself inside its own 12h grace window (created 2026-08-17, age 37806s/10.5h at check time). Flagged here for the next pass to flip once grace clears |
| 8 | `last_updated` bump, 4/7 remaining | grace-blocked at 2026-08-16 filing | **3/4 AUTO-FIXED this run** | `ag_closeout_audit_rollout_2026_07_25.md`, `estate_orphan_assessment_2026_07_21.md`, `defi_cefi_venue_chain_axis_contamination_2026_07_28.md` all outside grace (23-24h old) — bumped `last_updated` to each doc's real git last-touch date (`2026-08-17` for all 3, confirmed via `git log -1 --format=%ad --date=short`). `tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md` still inside grace (10.5h old) — left untouched. Same grace-blocked-tracking-doc caveat as item 7: could not flip `batch15` Todo 8 to "3/4 more done" since batch15 itself is grace-protected |
| 9 | 4 codex-alignment corrections | flagged, pending operator ruling | **RESOLVED** | Doc's own top-level todo list shows "DONE 2026-08-17" with 4 commit shas, operator-approved. No further action |

`tradfi_reconciliation_2026_08_17_findings_2026_08_17.md` is a **different** skill's output
(`/data-pipeline-reconciliation`, not `/plan-reconcile`) — not in Phase -1's scope; it's an ordinary tradfi-tranche
doc subject to the normal Phase 0-6 sweep below.

**Disposition**: `plan_reconciler_findings_tradfi_2026_08_16.md` still has 2 genuinely-open items (6 operator-gated
split, 5 AO-queued archival) plus 2 done-but-unrecorded items blocked only by `batch15`'s own grace window (7, 8) —
stays `status: open`, not archived yet. Recommend the next tradfi pass (or whichever session next legitimately
touches `batch15` after its grace clears) flips Todos 7 and 8 there.

## Mechanical fixes applied this run (Phase -1, outside Phase 2's flip-with-evidence bar — plain frontmatter hygiene)

- `plans/active/ag_closeout_audit_rollout_2026_07_25.md` — `last_updated: "2026-07-25"` → `"2026-08-17"`
- `plans/active/issues/estate_orphan_assessment_2026_07_21.md` — `last_updated: 2026-07-21` → `2026-08-17`
- `plans/active/issues/defi_cefi_venue_chain_axis_contamination_2026_07_28.md` — `last_updated: "2026-08-10"` → `"2026-08-17"`

## Coverage (hunters / batches / docs) — Phase 1 complete

9 hunter batches, 96/96 docs read in full (this findings doc's predecessor excluded — reconciled in Phase -1
above), ~310KB each, partition at `tradfi_batches.txt` (scratchpad). Roughly half the corpus was inside its own
12h grace window at hunt time (heavy concurrent na-eligibility-audit/context-scout activity this tranche) —
grace-protected findings are recorded under "Deferred (grace-protected)" below, not applied this run.

## Checkpoint 1 — applied

**Contradiction fixed**: `data_completion_tradfi_line_cap_blocks_e7_stale_item_close_2026_08_16.md` mischaracterized
E7's closure as blocked ONLY by the line-cap mechanical gate — `data_completion_tradfi_2026_07_15.md`'s own E7 text
(GRACE-PROTECTED, not edited) says the real gate is a CF-8 RED verify result, a data-integrity condition
independent of the line-cap. Added a correction blockquote, updated "Recommended decision" point 3, and updated
Todo 1's done-when to require CF-8 GREEN separately from the split. Also fixed a self-contradiction in the same
doc: its original "What happened"/"Recommended decision" diagnosed a `>` vs `>=` boundary bug in
`check_line_caps.sh`, but the doc's own later Progress Log already live-reproduction-tested that both carve-outs
use `-ge` — independently re-verified this pass (`scripts/plan-hygiene/check_line_caps.sh:238,270`, both `-ge`).

**Flip verified**: same doc's Todo 2 ("confirm with the check_line_caps.sh owner whether precondition should be
`>=`") — HARD evidence: direct code read (confirmed `-ge` at both cited lines) + 2 real commits
(`unified-trading-pm@8f823c84a0`, `@20a9c5916d`), both independently re-verified `git merge-base --is-ancestor
<sha> origin/live-defi-rollout` this pass. Flipped `[x]`, noting the substance is resolved via live evidence
rather than a literal owner conversation.

**Hygiene fixes** (mechanical `../`-relative → leading-slash repointing, targets verified to exist before
editing):
- `instruments_remaining_work_audit_2026_07_10.md` — 2 refs: `instruments_completion_tracker_2026_07_06.md` (now
  `/plans/active/...`) and `layer1_remeasure_and_certify_2026_07_06.md` (now archived,
  `/plans/archive/2026_07/...`).
- `phantom_audit_estate_coverage_gap_2026_07_10.md` — 1 ref (`consolidator_throughput_backlog_monitor_2026_07_09.md`
  → `/plans/active/...`); also bumped stale `last_updated: 2026-07-10` → `2026-08-09` (real git last-touch date).
- `adapter_findings_gcs_manifest_deployment_api_reconciliation_gap_2026_07_08.md` — 1 frontmatter `../`-relative
  ref fixed; 1 structural fix (a closing `**` with no matching opener, "Spot-check 2-3 more findings..." lost its
  bold-open in an earlier correction); 2 stale bare-filename prose refs repointed to their real archived locations
  (`canonical_id_builder_retrofit_checklist_2026_07_08.md` → `/plans/archive/2026_08/...`,
  `plan_reconciliation_operator_decisions_2026_07_11.md` → `/plans/archive/issues/...`, both verified to exist).

## Checkpoint 2 — applied

**Flip verified**: `dp_vm_001_tradfi_bf_cme_ohlcv_1m_btc_2020_exit137_stall_relaunch_bound_page_2026_08_16.md`'s
`[OPERATOR]` todo — its own bolded lead-in ("RESOLVED-BY-REDIRECT 2026-08-17") already declared resolution but the
checkbox stayed `[ ]`. **Double-confirmed** by 2 independent hunter batches (1 and 5) before flipping.

**Contradictions fixed** (redirect-to-billing-rootcause corrections, all citing
`dp_vm_001_tradfi_bf_cme_ohlcv_1m_g01_6a_6l_2020_20260816_220209_databento_cme_billing_rootcause_2026_08_17.md`):
- `dp_vm_001_tradfi_bf_cme_ohlcv_1m_g01_6a_6l_2020_exit137_stall_relaunch_bound_page_2026_08_15.md` — 2 open todos
  (OPERATOR relaunch-decision + BACKEND run.log investigation) were investigating a shard already confirmed
  billing-caused elsewhere; added a correction + superseded-markers on both (left unflipped — the correction, not
  a flip, is the safe action here; a future pass can archive/close once the family's normal sweep picks the shard
  back up). Also fixed a cosmetic orphaned-sentence text-splice in the same doc's Progress Log.
- `tradfi_autonomous_session_operator_decisions_2026_07_25.md` item 4 — corrected: the "WHY is twin-coverage at 0%"
  question this item left unpursued WAS since investigated and answered by
  `tradfi_purge_extension_and_twin_delete_fix_ao_dispatch_2026_08_16.md` Todo 2 (canonical_twin_path() bug fixed,
  re-measured — same 900/900 rows now blocked for a different reason).
- Same doc, item 10 — added a closing note: this P0 recommendation was never converted to a tracked todo and had
  no closing entry; its target was independently resolved the next day
  (`plans/archive/issues/tradfi_legacy_bucket_deleted_without_also_legacy_migration_2026_07_26.md`, RESOLVED
  2026-07-26).

**Hedge-pointer resolved**: `tradfi_fred_forward_capture_and_backfill_gap_2026_08_13.md` Finding 2 — identified the
doc making the "self-sufficient to completion" claim
(`plans/archive/2026_08/issues/macro_micro_econ_data_capture_audit_2026_06_05.md:515`, already in this doc's own
`related:` list but never explicitly connected) and rewrote the hedge into a direct citation.

**AO-dispatch-readiness fixes**:
- `databento_ice_opra_subscription_ask_2026_08_09.md` — todo cited "wherever the allowlist module lives... confirm
  before editing" despite the exact file already being in `context_scope`; rewrote to cite it directly
  (`unified-api-contracts/unified_api_contracts/registry/databento_subscription_allowlist.py`, independently
  confirmed to exist at that path this pass).
- `dp_vm_001_mdps_tradfi_2021_exit_nonzero_stale_tarball_rootcause_2026_08_16.md` — retagged an open design
  question ("consider whether...") from `[SCRIPT]` to `[DESIGN]`.
- `mtds_pipeline_e2e_check_driver_vm_oom_full_mvp_sweep_2026_08_14.md` — added a missing todo tracking the new
  <13.5min VM silent-death signature discovered 2026-08-17 (previously prose-only in the Progress Log, HARD RULE
  violation).

## Checkpoint 3 — applied

**Contradictions fixed** (`instruments_tradfi_g1_g5_gate_execution_2026_07_24.md`, both P1, both independently
re-verified against external evidence before applying):
- Internal contradiction between the doc's own "na-eligibility-audit log" section (stale: "P2 residual purge needs
  separate operator confirmation") and its own "Progress Log" section (accurate: "operator extended the go-ahead,
  extracted to `tradfi_purge_extension_and_twin_delete_fix_ao_dispatch_2026_08_16.md`") — added a citation to the
  actual todo pointing at the extraction target, retired the stale framing.
- "Concerning zero-capture finding" for ES CME futures framed as needing "adapter-level investigation" — its own
  cited archived doc (`tradfi_es_cme_ohlcv_zero_capture_2026_07_30.md`) actually resolved this via 2 infra bugs +
  1 manifest-write bug (independently re-verified the exact resolution text this pass). Corrected the framing.

**Countable corrections applied** (AUTO-RESOLVE per skill calibration — both independently re-verified via direct
code/live checks before writing):
- `tradfi_registry_coverage_and_ao_readiness_2026_07_25.md` — Databento tradfi's ~33-day billing tier corrected
  L3→L2 in 2 places (independently verified against live
  `unified-api-contracts/.../databento_subscription_allowlist.py`: `mbp-10`→`L2`, confirmed `mbo` is the real L3
  schema). Also bumped stale `last_updated: "2026-07-30"` → `"2026-08-16"` (real git last-touch date).
- `tradfi_consolidated_closeout_2026_07_18.md` — digest child-plan open-todo counts were stale in 2 sections
  (claimed 3/2 open for 2 child plans; live `grep -c` this pass shows 1/1, and phase_d's remaining item is a
  DIFFERENT todo than either one named in the stale text). Added correction notes with the live counts rather
  than surgically rewriting the dense historical bullet text (lower risk of a worse mismatch in a 900L doc).

**Prose→todo conversion** (HARD RULE — "every follow-up is a todo, never prose"):
- `tradfi_canonical_path_migration_design_2026_07_19.md` — this doc is archive-ready (all displayed todos `[x]`,
  archival already queued via `tradfi_satellite_ao_dispatch_batch15_2026_08_17.md` Todo 6) but its own
  "Deferred work" table named 2 items of real, substantial undone work (a 207,438-object combo_chain migration +
  a short-code→display-name migration) tracked only as prose — converted both into canonical `- [ ] [DATA] P2.`
  todos so they survive the pending archival instead of silently disappearing.

**AO-dispatch-readiness / hygiene**:
- `retirement_completeness_pollutant_reverify_ice_still_live_2026_08_15.md` — added the missing
  `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` citation to an `[OPERATOR]` todo that stated the need
  for one but never included it. Also flagged (not resolved — needs a live remeasurement, see "Filed" below) that
  this doc's own BARCHART row-count contradicts a same-day sibling doc.
- `nick_ai_audit_data_quality_findings_2026_08_16.md` — added a duplicate-tracking cross-reference to
  `b21_distinct_values_noncanonical_live_2026_08_18.md` (both independently track the identical sports
  FOOTBALL-venue/lowercase-bookmaker column-swap bug, zero cross-reference either direction; `b21` itself is
  grace-protected so only this side could be fixed this pass).

## Refuted (dropped by verify)

- **`mtds_is_full_adapter_smoketest_findings_2026_07_07.md` hedge-pointer finding (batch-5 hunter, "Open question
  5" candidate-owner update)** — direct re-read this pass found the fix ALREADY LANDED by a concurrent session
  (dated 2026-08-18, near-identical content to what was planned). Skipped to avoid a race; no action needed.

- **`honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md` missing `stage:`/`repos:`/`scope:`
  frontmatter** (batch-2 hunter finding) — direct re-read this pass shows all 3 fields ARE present and populated.
  Likely fixed by a concurrent session between the hunter's read and this verification pass (this tranche saw
  heavy concurrent activity — see grace-window notes throughout). No action needed; textbook case of why every
  candidate gets adversarially re-verified before acting.

## Doc-drift (routed, NOT auto-applied — filed via `/blocked` BLK-3867b41d)

1. **[P2]** `/codex/02-data/tradfi-databento-sourcing-ssot.md` — stale on the 2026-08-10/12 Databento billing
   incident's blast radius (frames account-wide; `tradfi_databento_account_billing_suspended_2026_08_09.md`'s own
   2026-08-16 correction shows it's dataset-scoped). New content needed, outside the mechanical carve-out.
2. **[P2]** `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` — never absorbed the tradfi GOLD/WTI/
   combo_chain near-miss (2026-08-11/12) as its own worked example, despite
   `tradfi_canonical_path_migration_design_2026_07_19.md` explicitly framing it as the same failure class as the
   codex's existing defi `dex_pools/` example.
3. **[P1]** `tradfi_satellite_ao_dispatch_batch16_2026_08_17.md` reflex-sets `sequential: true` for its whole
   8-todo plan over a single colliding pair (Todo4+Todo8) — should SPLIT per CLAUDE.md, not serialize the whole
   plan. Treated conservatively (routed, not restructured) given the plan is `status: active`/`assigned_vm:
   planning` and may be mid-dispatch.

## Filed (grace-protected this run — deferred to the next tradfi pass, enumerated per Phase 5.9)

**Corrections needed once grace clears** (doc, finding, why deferred):
- `plan_reconciler_findings_tradfi_2026_08_16.md` — flip Todo 7 (reference-path fix, already done-but-unchecked)
  + Todo 8 (3 more `last_updated` bumps landed directly on target docs) in
  `tradfi_satellite_ao_dispatch_batch15_2026_08_17.md` once THAT doc's own grace clears (was ~10.5h old at run
  start).
- `canonical_path_oracle_blind_to_filename_stem_2026_07_20.md` — no actionable finding this pass (grace, ~0s old).
- `tradfi_scope_ruling_possible_violation_legacy_fleet_relaunched_2026_08_09.md` — `status: open` but 0 open
  checkboxes + its blocked question already answered 2026-08-17; gates real P1 work in
  `tradfi_year_shard_backfill_launcher_missing_source_self_deletes_2026_08_09.md`. Needs a status-semantics check
  (does dispatch key off `status:` or todo-count?) before closing.
- `uac_data_type_validity_combinator_fragmentation_2026_07_07.md` — still 1008-1009L, over the 1000 hard cap;
  the `[OPERATOR]` tag-fix (lines ~975,983) stays split-blocked, unchanged from the 2026-08-16 finding.
- `tradfi_cme_expected_coverage_narrow_ao_dispatch_2026_08_16.md`, `tradfi_purge_extension_and_twin_delete_fix_ao_dispatch_2026_08_16.md`
  (Todo1 `[DATA]`/Todo3 VM-launch — both need `[OPERATOR]` tag or explicit safe-idempotent justification),
  `tradfi_satellite_ao_dispatch_batch15_2026_08_17_finalize.md`, `tradfi_satellite_ao_dispatch_batch16_2026_08_17_finalize.md`
  — AO-readiness gaps, all grace-protected, all P1-P3.
- `uac_per_venue_seed_fallback_removal_deferred_2026_07_26.md:96` — cites "G4 OPEN" for CEFI catalogue
  completeness; live-checked, actual open gate is G1 not G4 (doesn't invalidate the doc's overall ruling).
- `tradfi_phase_d_terminal_gate_2026_07_24.md:514-518` — stale 2026-08-09 inline note on an open P3 todo,
  contradicted by the SAME doc's own later 2026-08-16 entry (todo correctly stays open, just the annotation is
  stale). Also has a backtick-code-span hiding an already-`[x]` item at :388-389 (cosmetic, no undercounting).
- `tradfi_satellite_ao_dispatch_batch9_2026_08_16_finalize.md` Todo1 — chases flipping a target
  (`tradfi_volatility_no_perp_fx_underlyings_code_gap_2026_08_06.md` todo2) that's already archived/resolved
  independent of its stated gate.
- `mdps_features_deadcode_consolidation_2026_07_20.md:155-156` todo8 — tagged `[SCRIPT]` but repeatedly
  self-described as operator/design adjudication over 7+ passes; should be `[DESIGN]`/`[OPERATOR]`.
- `tradfi_legacy_bucket_delete_ao_dispatch_2026_08_16.md:99-101` — a re-verify-then-delete follow-up tracked only
  in prose ("Next step (tracked, not this todo)"), no actual todo exists for it once CF-8 clears.
- `tradfi_bf_cme_ohlcv_1m_relaunch_dispatch_budget_hit_2026_08_16.md` — `escalation_dedup.py` repo misattribution
  (context_scope/repos say deployment-service; a todo says "repo: agent-orchestrator" — file only exists in
  deployment-service, live-verified by the hunter).
- `tradfi_volatility_options_groups_empty_confirmed_missing_fetch_evidence_2026_08_17.md` — todo1/todo2 real
  dependency not machine-enforced (`depends_on: []`), same-file concurrent-dispatch risk.
- `tradfi_within_bounds_source_zero_shard_atom_mismatch_2026_07_28.md` — 2 multi-line backtick spans hide
  commit-message text as apparent bullets (:176-180); a table row-sum doesn't reconcile with its stated Total
  (gap ~14-19%, possibly intentional imprecision per a disclosed caveat) — worth a future check against the
  underlying script's real output. Possible unmerged overlap with the now-resolved
  `tradfi_es_cme_ohlcv_zero_capture_2026_07_30.md` population (3,048/4,855 rows share the same error_reason) —
  worth confirming whether this doc's still-open P0 migration already subsumes it.
- `tradfi_satellite_ao_dispatch_batch12_2026_08_10.md` Todo2 — VM-launch lacks explicit safety wording (may be
  an accepted tranche convention for bounded/typed backfills, not necessarily a hard violation).
- `tradfi_satellite_ao_dispatch_batch16_2026_08_17.md` Todo6 (phantom audit) — no cited script/symbol, unlike
  every sibling todo in the same plan.

**Needs a live remeasurement, not a doc edit** (flagged in-place already, repeated here for visibility):
- BARCHART manifest row-count/timestamp: `retirement_completeness_pollutant_reverify_ice_still_live_2026_08_15.md`
  says 4,655 rows / stamp 2026-05-07; `tradfi_satellite_ao_dispatch_batch16_2026_08_17.md` Todo7 (sourced from
  `tradfi_reconciliation_2026_08_17_findings_2026_08_17.md`) says 9,119 rows / stamp 2026-07-07. Off by ~2x /
  ~2mo, neither doc cross-references the other. Both docs already carry a note pointing at this discrepancy.

**Premise changed since filing, needs re-flagging once grace clears**:
- `tradfi_autonomous_session_operator_decisions_2026_07_25.md` item 8 (a queued operator-decision item, "RECOMMEND
  OPTION B" — keep `tradfi_consolidated_closeout_2026_07_18.md` as the tranche coordination index rather than
  fold+archive) frames its premise as "near-complete, exactly 1 open todo (line 234)". **Live-verified this pass**:
  `tradfi_consolidated_closeout_2026_07_18.md` now has **0 open top-level checkboxes** (both `[x]`, the line-234
  item VERIFIED 2026-08-04, plus a second item since closed) — the doc moved from "near-complete" to "fully-done at
  the top level" (its digest-tracked child-plan work, fixed in Checkpoint 3, is separate from its OWN checkboxes).
  This doesn't answer the decision, but the operator should re-read it against current state — "fully-done, keep as
  archive-exempt index" is a different framing than "near-complete, decide whether to fold." Could not fix directly
  — this doc is grace-protected (Checkpoint 2 touched it this same run).

**Observational, not a doc-edit** (for the operator/next pass's awareness):
- `tradfi_vm_resource_utilization_downsize_2026_08_10.md` — sole open todo (well-specified) stale-in-queue,
  released `GATED` 3x on 2026-08-10, no Progress Log entry since (8 days as of this run). Worth a fresh look —
  either the OHLCV fleet stopped running or this todo is starved.
- `tradfi_consolidated_closeout_2026_07_18.md` — file-level unpaired `` ** `` (559 = odd count via grep); exact
  offending line not isolated within budget (many legitimate 2-line-wrapped bold spans make bisection expensive
  relative to this P3 cosmetic finding).

## Archive candidates (operator review)

_(pending Phase 1-4)_

## Plans not reached

_(pending — updated at Phase 6)_

## Phase-0 hygiene sweep (corpus-wide, informational — NOT tradfi-tranche-specific, out of scope for this shard)

**Entry (`--ci --no-regen`)**: 2 hard failures, 1 soft warning:

- `assigned_vm:NA corpus size ratchet` — corpus-wide, `/na-eligibility-audit`'s remit, not a tradfi-tranche
  contradiction (consistent with the 2026-08-16 run's own scoping of this same check).
- `Silent-default-effort plans (ratchet)` — 341/343 active plans corpus-wide rely on the silent Sonnet default
  instead of declaring `model_tier`; 89 heuristic opus-candidates flagged, 2 of which are tradfi
  (`tradfi_consolidated_closeout_2026_07_18.md`, `tradfi_phase_d_terminal_gate_2026_07_24.md`). Given CLAUDE.md's
  2026-08-08 ruling that `opus-required` is now ZERO categories (opus is manual-only), this heuristic's own
  "⬅ OPUS?" framing may itself be stale tooling — worth a follow-up check on whether the checker's candidate logic
  still reflects the current model-tier policy. Not fixed here: corpus-wide (343 plans across all 10 tranches),
  well outside a single-shard's scope.
- `Delete/VM-launch todo tagging` (soft WARN) — candidate signal only, adjudicated per-doc during Phase 1 if any
  tradfi doc is flagged.
