---
doc_type: plan
title: CeFi satellite AO batch 7 — iterative-drain extraction over the batch6 residual
summary: >-
  Seventh AO-dispatch batch for cefi, produced by the `/ag-closeout-audit` skill run 2026-08-03 (scheduled autonomous
  dispatch, tranche=cefi, slot 7). Phase 0 re-derived the covering-plan set via
  `generate_ag_closeout_audit_candidates.py` (95 cefi-tagged AG-primary docs total; 18 real covering docs — batch6 + its
  finalize now count, having landed 2026-08-02; 12 "never cited" candidates) UNIONED with 2 additional docs
  `check_ag_closeout_linkage.py` independently flagged as self-dispatched with zero real graph/mention path to the cefi
  closeout family — 14 docs deep-audited this run via a Workflow (one agent per doc, all 18 active + 8 archived covering
  docs passed as context). Verdicts: 5 exclude_cross_cutting (all genuinely multi-AG in scope — 2 carry real AO-eligible
  content, flagged below for whichever tranche owns them, not drafted here), 3 archivable_now (2 pure archival-hygiene
  housekeeping already flagged by a prior na-eligibility-audit pass, no AO content; 1 — a candle- manifest
  reconciliation doc — is content-complete and already correctly archived elsewhere in the corpus, but a stray duplicate
  copy was accidentally resurrected into `plans/active/issues/` by an unrelated commit and needs deleting), 6
  orphaned_never_touched (4 correctly non-AO-eligible — design/operator-gated per 2-3 independent prior audit passes
  each, unchanged; 2 carry real AO-eligible bounded work, one of them a materially-new-evidence re-derivation of a todo
  two prior audit passes explicitly declined, now revisited because the specific external gate that justified declining
  it has since cleared). Phase 3 conflict-checked all 3 AO-eligible candidates against the full 26-doc active+archived
  covering set (zero overlap, confirmed per-doc by each Phase-1 agent) AND a corpus-wide grep for each candidate's
  target files/topics (zero overlap); 2 of the source docs' internally-sequential 3-step Phase 1 work is combined into
  ONE todo per the shared conflict-check protocol's no-fan-out-racing-steps rule. 3 todos below, zero genuine conflicts
  found, zero items parked BLOCKED-OPERATOR-DECISION this run.
status: draft
nature: process
asset_group: [cefi]
stage: [data]
repos: [unified-trading-pm, market-tick-data-service, strategy-service, instruments-service]
scope: [engineer]
tags: [cefi, ao-dispatch, close-out, batch-7, satellite-docs, iterative-drain]
related:
  [
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /plans/active/cefi_consolidated_closeout_aggregated_sources_2026_07_24.md,
    /plans/active/cefi_satellite_ao_dispatch_batch6_2026_08_02.md,
    /plans/active/cefi_satellite_ao_dispatch_batch6_2026_08_02_finalize.md,
    /plans/active/hyperliquid_aster_defi_to_cefi_asset_group_migration_2026_08_02.md,
    /plans/active/issues/mdps_cefi_candle_manifest_orphan_reconciliation_2026_07_26.md,
    /plans/active/issues/no_active_paper_run_blocks_p1_2_determinism_recheck_2026_07_31.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
created: "2026-08-03"
last_updated: "2026-08-03"
parent_epic: cefi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: data_engineering
sequential: false
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  /ag-closeout-audit skill run 2026-08-03 (scheduled autonomous dispatch, agent-orchestrator slot 7, tranche=cefi) —
  Phase 0 used `scripts/plan-hygiene/generate_ag_closeout_audit_candidates.py --tranche cefi` (95 total members, 12
  never-cited) UNIONED with a `scripts/plan-hygiene/check_ag_closeout_linkage.py` cross-check (+2 self-dispatched docs
  with zero real graph/mention linkage), Phase 1 ran a `Workflow` (14 parallel agents over the union set), Phase 3
  conflict-checked every AO-eligible candidate against the full covering-doc set and a corpus-wide grep for each
  candidate's target files before drafting.
context_scope:
  [
    /plans/active/cefi_satellite_ao_dispatch_batch6_2026_08_02.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
  ]
---

# CeFi satellite AO batch 7 — iterative-drain extraction

> **Status: draft — NOT dispatched.** Per CLAUDE.md's plan-destination HARD RULE and the ag-closeout-audit skill's
> autonomous-mode guidance, a skill-drafted AO batch is never auto-flipped to `active`. This run was a scheduled
> autonomous dispatch (no operator present), so the flip is explicitly reserved for operator review. Flip this
> frontmatter's `status` to `active` only after that review.

> **Cross-todo file-collision check: PASS.** The 3 todos touch, respectively: (1) `market-tick-data-service/scripts/` —
> a NEW migration script (`migrate_hyperliquid_aster_defi_asset_group_2026_08_0X.py`) plus a NEW audit output parquet
> under `_index/audit/`, reading (not writing) the existing `audit_aster_cefi_in_defi_bucket_scope_2026_07_13.py`
> pattern and `migration_common.py` helpers, plus a read-only `resolve_bucket_name()` parity check; (2)
> `plans/active/issues/mdps_cefi_candle_manifest_orphan_reconciliation_2026_07_26.md` — a single `git rm` of a stray
> duplicate, no other file touched; (3) `strategy-service/strategy_service/cli/handlers/paper_universe.py` +
> `.../engine/strategies/v2/target_universe/catalog_trading.py` — READ-ONLY tracing (no code edit), plus a doc update to
> `no_active_paper_run_blocks_p1_2_determinism_recheck_2026_07_31.md` and a conditional doc update to
> `live_event_log_warm_sink_recovery_and_cold_compaction_2026_07_31.md` only if the DIAG finding is positive. No file is
> written by more than one todo. Note: several unrelated DeFi-tranche plans (`defi_satellite_ao_dispatch_batch2/3`,
> `defi_archetype_universe_no_curtailment_mechanism_2026_07_23.md`,
> `citadel_paper_batch_live_reconciliation_2026_06_19.md`) also reference `paper_universe.py`/`catalog_trading.py`, but
> only as read/cite targets for their own gated design decisions (none is mid-edit) — todo 3 here is itself read-only,
> so there is no write collision even under concurrent execution. Safe to dispatch concurrently; `sequential: false`.

> **Every claim below was re-verified against live corpus/code state on 2026-08-03**, not carried over from the source
> docs' own prose without a fresh check.

## Todos

- [ ] [DATA] P1. **HYPERLIQUID/ASTER `asset_group=defi→cefi` migration — Phase 1 (audit + parity-check + script
      authoring, combined).** This source doc's own Phase 1 is 3 hard-ordered todos in ONE worker's remit (script
      authoring in step (c) needs step (a)'s object-count findings and step (b)'s canonical-path confirmation as inputs,
      so this is bundled as one todo per the shared conflict-check protocol's no-fan-out-racing-steps rule, not 3
      concurrent todos). **(a)** Run the full day-by-day, data_type-by-data_type object-count audit for the frozen
      HYPERLIQUID + ASTER `asset_group=defi` corpus in `gs://market-data-tick-defi-prd-central-element-323112` (targeted
      per-day parallel prefix listing, reusing the pattern from
      `market-tick-data-service/scripts/audit_aster_cefi_in_defi_bucket_scope_2026_07_13.py` — NOT a whole-bucket scan).
      **(b)** Confirm the canonical CEFI-bucket target path shape for HYPERLIQUID/ASTER via
      `resolve_bucket_name(asset_group='cefi')` and run a `(size, crc32c)` parity check — never existence-only — for any
      pre-existing canonical twin of this frozen corpus. **(c)** Write
      `market-tick-data-service/scripts/migrate_hyperliquid_aster_defi_asset_group_2026_08_0X.py` (dry-run default,
      `--apply` to mutate, idempotent parity-checked skip, reuse `migration_common.py` helpers). **Never deletes the
      `asset_group=defi` source** — deletion is Phase 4 of the source doc, separately `[OPERATOR]`-gated and explicitly
      NOT part of this todo (no reversibility shortcut applies to that permanent delete per the source doc's own text).
      Source: `hyperliquid_aster_defi_to_cefi_asset_group_migration_2026_08_02.md` (Phase 1, all 3 todos). **Done
      when**: the audit output parquet exists with exact first/last day-with-data per venue + full data_type list; the
      canonical target path + twin-parity verdict is recorded; the migration script exists, is committed, and a
      `--dry-run` run against a sample day/venue produces a correct copy plan with zero source mutations/deletes; and
      the source doc's Phase 1 todos 1-3 are flipped `[x]` citing this run. Repo: market-tick-data-service.

- [ ] [SCRIPT] P3. **Delete the stray, accidentally-resurrected active-tree duplicate of an already-archived, fully
      -resolved doc.** `plans/active/issues/mdps_cefi_candle_manifest_orphan_reconciliation_2026_07_26.md` was properly
      archived 2026-08-02 (commit `ff619d49f`, following flip `64ef0b9e3` + plan-reconcile batch `a04f74e1c`) to
      `plans/archive/issues/mdps_cefi_candle_manifest_orphan_reconciliation_2026_07_26.md`, which carries an explicit
      "🟢 ARCHIVED 2026-08-02" banner and is the ONLY path every corpus referrer (10 grep hits across 5 files) cites —
      zero referrers cite the active-tree path. An unrelated commit `8f01b82a4` ("flip OmniRoute INFRA P3 type-level
      registration...", slot-1·laptop, 2026-08-02 23:56 — 61 minutes after the legitimate archive-move) re-added this
      exact file as a "new file" in its diff, almost certainly a stale/dirty local working-tree copy swept into an
      unrelated quickmerge. **Do NOT re-run the 6-step archival ritual on this active-tree copy** — it lacks the
      ARCHIVED banner the real twin has, and re-processing risks clobbering the already-correct, already-referrer-fixed
      archived twin. Just remove the stray duplicate. Source:
      `mdps_cefi_candle_manifest_orphan_reconciliation_2026_07_26.md` (content already fully resolved; this is a pure
      corpus-hygiene fix, not a reopening). **Done when**:
      `git rm plans/active/issues/mdps_cefi_candle_manifest_orphan_reconciliation_2026_07_26.md` is committed and pushed
      via quickmerge; a corpus-wide grep for the basename shows zero remaining references to the `plans/active/issues/`
      path (only `plans/archive/issues/` remains); `regenerate_active_plan_inventory.py` /
      `check_terminal_status_archived` report the active-tree path no longer present. Repo: unified-trading-pm.

- [ ] [DIAG] P2. **Re-check whether any active paper run trades BINANCE-FUTURES/ASTER/OKX-FUTURES, now that the sibling
      P1.2 time-gate has cleared.** Two prior passes (na-eligibility-audit 2026-08-01, batch6 2026-08-02) each
      considered and explicitly declined splitting this off, reasoning the answer "only serves the gated DECISION" and
      has "no standalone value" — correct at the time. **Materially new fact since**: the sibling
      `live_event_log_warm_sink_recovery_and_cold_compaction_2026_07_31.md` P1.2 todo's own 24h time-gate (since the
      2026-07-31T21:14Z P1.1 redeploy) has now ELAPSED as of today (2026-08-03), so a positive finding today has
      **immediate** value — it could unblock P1.2 directly, both gates now clear — rather than only feeding a
      hypothetical future `[OPERATOR]` decision as it did when the prior two passes reasoned there was no standalone
      value. This re-derives the same item fresh against new evidence, mirroring batch6's own convention for revisiting
      a declined verdict. **If the reviewer disagrees this now has standalone value, park instead of dispatching** —
      this is a judgment call about timing/value, not a technical unknown. Read the live paper-run spec/universe wiring
      (`strategy_service/cli/handlers/paper_universe.py` +
      `strategy_service/engine/strategies/v2/target_universe/catalog_trading.py` — neither currently greps a literal
      BINANCE-FUTURES/ASTER/OKX-FUTURES match, but trace the actually-active spec/archetype indices referenced in
      `citadel_paper_batch_live_reconciliation_2026_06_19.md` around `PAPER_RUN_SPEC_INDICES`, not just a static grep)
      and re-run a instance/service listing broader than VM-name-only (per the parent plan's own slot-6 precedent).
      Source: `no_active_paper_run_blocks_p1_2_determinism_recheck_2026_07_31.md` (the `[DIAG] P2` todo only — its
      `[DECISION] P2` `[OPERATOR]` todo stays untouched, correctly NA). **Done when**: a definitive yes/no is recorded
      in the source doc's `[DIAG] P2` checkbox with the config/API evidence cited, and if yes,
      `live_event_log_warm_sink_recovery_and_cold_compaction_2026_07_31.md`'s P1.2 is updated with the correct
      `paper_ledger_root`/`batch_ledger_root` pointer. Repo: strategy-service (read-only), unified-trading-pm (doc
      updates).

## Cross-tranche notes (informational — out of cefi scope, not drafted here)

- **`issues/backfill_smoke_write_path_canonical_audit_2026_07_20.md`** —
  `asset_group: [cefi, defi, tradfi, sports, prediction]`, genuinely cross-AG (infrastructure-audit scope,
  `parent_epic: infrastructure_master`). Carries 2 genuinely open todos (a `[DOCS] P2` stale-comment fix + a `[DATA] P3`
  scope-decision item), the DOCS one is AO-eligible bounded work, uncovered by anything currently active. For whichever
  tranche's own `/ag-closeout-audit` run picks up cross-cutting/infra-parented docs.
- **`issues/honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md`** —
  `asset_group: [cefi, defi, tradfi, prediction]`, genuinely cross-AG (`parent_epic: instruments_master`, a Decision
  Gate D6 candidate). Carries 2 AO-eligible `[VERIFY] P3` checkbox-reconciliation items (re-verify DERIBIT-COMBO
  venue-key retirement looks already done but was never cross-referenced/flipped; determine whether the now-shipped
  `--operation reprocess-shards` CLI already covers a stated backfill need). Same routing note as above.
- **Stray-duplicate resurrection pattern is not isolated to cefi.** The same bad commit (`8f01b82a4`) that resurrected
  `mdps_cefi_candle_manifest_orphan_reconciliation_2026_07_26.md` (fixed in todo 2 above) also resurrected a
  DEFI-tranche doc, `plans/active/issues/features_service_defi_backfill_vm_oom_unexplained_2026_07_26.md`, into
  `plans/active/issues/` as a stray duplicate of an already-archived doc. Verified: of the other 9 docs deleted in the
  same 2026-08-02 archive-move batch (`ff619d49f`), only these 2 are currently stray-resurrected — an isolated
  2-document incident from one commit, not a systemic corpus problem. Flagging for the defi tranche's own audit to apply
  the identical `git rm` fix; not drafted here (out of cefi scope).

## Archival-hygiene housekeeping (informational — not AO-eligible batch content)

Two docs this run confirmed `archivable_now` with **zero** AO-eligible content — their remaining action is purely the
mechanical 6-step archival ritual (status stale vs. real completion, or a doc-split appendix with zero forward-looking
work), both already flagged by a prior na-eligibility-audit pass. Not batch items; noted here for traceability only:

- `issues/cefi_content_migration_fleet_half_incomplete_progress_log_archive_2026_07_31.md` — a verbatim Progress-Log
  extraction appendix, zero checkboxes, zero prose todos. Ready to archive independent of its still-open parent.
- `issues/cefi_content_migration_shard17_default_bump_2026_07_31.md` — both todos independently re-verified complete (VM
  relaunch confirmed via telemetry; a codex runbook carve-out confirmed by direct read) even though `status:` itself was
  never flipped off `open`.

## Re-checked from batch6's Deferred section (iterative-drain step 1 — neither gate cleared)

Per the skill's iterative-drain methodology, batch6's own Deferred items were re-checked before running fresh Phase 1
triage (both confirmed still blocked, unchanged from batch6 — not re-listed as new batch7 Deferred items since batch6
itself remains active and still owns them):

- **Schema v10 `instrument_id_form` backfill (Stage 2)** —
  `issues/fail_hard_canonical_enforcement_design_2026_07_20.md`'s `[DESIGN] P1` "close the three §5 gaps" todo
  (line 147) is still `[ ]` open. Transitive gate NOT cleared.
- **`issues/estate_orphan_assessment_2026_07_21.md` todo 6** — cross-tranche boundedness disagreement (cefi/sports
  KEEP-NA vs. defi RECLASSIFY). Line 549's "Operator/next-toucher: rule on todo 6's boundedness" note is still present,
  unresolved. Still no operator ruling as of 2026-08-03.

## Reconciliation

Once a todo here ships, flip the corresponding checkbox in its named source doc, citing this plan's commit as evidence.
This plan's own reconciliation-then-archive step is machine-gated via the companion
`cefi_satellite_ao_dispatch_batch7_2026_08_03_finalize.md` (`depends_on` + `gate_on_depends: true`), mirroring the
batch1 through batch6 finalize pattern.

## Codex SSOTs

- `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` — the 6-step archival ritual this batch's
  finalize plan executes (and which the archival-hygiene housekeeping section above still needs, separately from this
  batch).
- `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "Dispatch-scope eligibility" — the
  bounded-vs-judgment-call test applied to every Phase-1/Phase-3 verdict above.
- `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` — the shared conflict-check protocol
  this batch's Phase 3 ran before drafting, including the no-fan-out-racing-steps rule applied to todo 1.
- `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` § 3a — confirms todo 1 stays inside the safe-idempotent
  path (dry-run default, parity-checked skip, no delete of the `asset_group=defi` source); the actual permanent delete
  stays `[OPERATOR]`-gated in the source doc's own Phase 4, not drafted here.
