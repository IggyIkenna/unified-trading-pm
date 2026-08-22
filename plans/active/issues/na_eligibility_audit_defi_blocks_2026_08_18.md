---
doc_type: issue
title: na-eligibility-audit defi tranche 2026-08-18 — consolidated operator questions and carry-forward MISCLASSIFIED_LIKELY_AO_ELIGIBLE list
summary: >-
  Phase 1b consolidation artifact for the 2026-08-18 /na-eligibility-audit defi run (4 docs classified: 4 defi-owned
  in-scope, plus 1 mandatory carry-forward re-assessment on an incremental-skip doc). Not a work item itself — a
  batchable index of the DISTINCT operator-decision asks found across the tranche, plus the
  MISCLASSIFIED_LIKELY_AO_ELIGIBLE items still genuinely unresolved after this run's own RECLASSIFY pass. Supersedes
  na_eligibility_audit_defi_blocks_2026_08_17.md.
status: open
nature: issue
asset_group: [defi]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [defi, na-eligibility-audit, operator-questions, misclassified-carry-forward]
related:
  [
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /plans/active/issues/na_eligibility_audit_defi_blocks_2026_08_17.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
created: 2026-08-18
last_updated: 2026-08-18
# was: defi_master (epic-assignment audit 2026-08-19) -- same as its 2026-08-16/17
parent_epic: plan_hygiene_master
  # predecessors: a na-eligibility-audit Phase 1b consolidation run report over the defi tranche, not defi
  # asset-group content itself
assigned_vm: NA
execution_scope: local-only
priority: P3
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
resolved_by:
context_scope:
  [
    /cursor-configs/skills/na-eligibility-audit/SKILL.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
  ]
supersedes: na_eligibility_audit_defi_blocks_2026_08_17
source: >-
  /na-eligibility-audit defi (2026-08-18, dispatch agt-9095fb, slot 26) — Phase 1b consolidation across all 4
  classified in-scope docs (4 defi-owned) plus 1 mandatory carry-forward re-assessment on an otherwise
  incremental-skip doc (defi_migration_audit_log_2026_07_24.md's FOLD-3 residual).
---

> **SUPERSEDED 2026-08-19** by
> [`na_eligibility_audit_defi_blocks_2026_08_19.md`](/plans/active/issues/na_eligibility_audit_defi_blocks_2026_08_19.md)
> — that doc carries the fresh Phase-1b consolidation for today's run, including this doc's still-genuinely-open
> carry-forward items re-assessed. Kept here (not archived) as the historical record for this specific run; archival
> deferred to a dedicated hygiene pass.

# na-eligibility-audit defi tranche 2026-08-18 — blocks + carry-forward index

## Headline this run: a full whole-set KEEP-NA-STALE closure

`defi_leverage_archetypes_health_factor_wrong_source_2026_08_16.md` had 8 open `[AGENT]`/`[OPERATOR]` todos left
after the 2026-08-18 (same-day, interactive) P0 reconciliation landed. Checked every one against
`/plans/active/strategy_service_centralization_fixes_2026_08_16.md` (`status: active`, `assigned_vm: planning`,
`sequential: true`) — that plan was deliberately authored by extracting this exact issue doc's findings on
2026-08-16, and every one of the 8 remaining todos turned out to already be a verbatim/near-verbatim duplicate
there. Closed all 8 by citation marker (same treatment the P2 docstring todo already received from a prior pass).
The issue doc now carries **zero** open todos and stays `assigned_vm: NA` — it remains the evidence/investigation
record the plan's own text explicitly defers to, not archived, since the underlying execution work is still
in-flight in the wrapper plan.

## Operator questions (deduped by distinct ask, not one row per doc)

1. **Elysium delivery decisions (9 distinct asks, unchanged since 2026-08-16/17, one doc)** —
   `elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md`: carry-archetype attestations, real risk
   thresholds for `carry_staked_basis.yaml`, ClearLoop modelling, a falsifiable "does everything we need" checklist
   for strategy-service, disclosure-repo inventory scope, transfer mechanism, accompanying documentation scope, SLA
   reissue/side-letter terms, commercial/IP treatment of client-contributed research. Not in this run's in-scope
   set (incremental_skip=true, unchanged) — carried forward unverified against fresh state; still all open/unruled
   per the 2026-08-17 run's own account. Operator-driven, in-progress; not batchable per this doc's own HARD RULE.
2. **`strategy_service_centralization_fixes_2026_08_16.md`'s `sequential: true` scope** — unchanged from 2026-08-17:
   several of its 18 todos read as semantically independent of todo 1's `[OPERATOR]` gate; worth ruling whether the
   whole plan should stay serialized. Not this skill's call (plan-authoring preference, operator-gated even under
   trust mode) — surfaced here again since this run cited that plan's todos as conflict-check/citation targets 8
   more times (the leverage-archetypes closure above).
3. **Non-defi-owned, reported only — NOT re-verified this run** (none of these appeared in today's defi Phase-0
   in-scope set, so they are carried forward exactly as the 2026-08-17 run left them, per the primary-owner rule —
   infra/cefi tranches own these):
   - `mdps_fleet_duplicate_relaunch_explosion_2026_08_15.md` (cefi-owned) — per the 2026-08-17 run, cefi's own
     same-day marker already reaffirmed its single genuinely-open item; no update available this run.
   - `defi_legacy_fold_relaunch_vm_infra_flakiness_and_oom_2026_08_15.md` (infra-owned) — todo 1 still reads
     MISCLASSIFIED_LIKELY_AO_ELIGIBLE per the first 2026-08-17 pass (a sibling doc calls the relaunch "harmless");
     still infra tranche's job to promote via a per-todo split.
   - `estate_orphan_assessment_2026_07_21.md` (cefi-owned) — todo 6's boundedness still contested across prior
     tranche passes (cefi/defi/sports disagree); still unruled per the doc's own text.

## Credential/access asks

None new this run.

## MISCLASSIFIED_LIKELY_AO_ELIGIBLE — carry-forward for the NEXT defi run only

Per the skill's close-the-loop rule, every item below is a mandatory Phase-1 input for the next
`/na-eligibility-audit defi` run.

**Resolved 2026-08-18 (dispatch agt-9095fb)**: the 8-todo leverage-archetypes closure above (not itself a
MISCLASSIFIED-tagged item from a prior run, but the same close-the-loop spirit — fully resolved by citation, drops
off every future carry-forward list). `defi_venue_e2e_batch1_deferred_followups_2026_08_17.md` reconfirmed KEEP-NA
valid (no change).

**Re-assessed, NOT promoted (mandatory carry-forward item from 2026-08-17, now redirected)**:
`defi_migration_audit_log_2026_07_24.md` line ~406 (FOLD-3-orphan-data_types residual — whether pre-existing
HISTORICAL rows for `vault_share_price`/`risk_params`/`utilization` are still legacy/non-v9-shaped). Re-assessed
against the primary RECLASSIFY bar this run: found a likely-overlapping open NA item,
`data_completion_defi_2026_07_15.md` C4 ("schema v4–v8 → v9 re-version across the dedicated DeFi buckets. Same
walk.", same `parent_epic: manifest_master`, also `assigned_vm: NA`). Did NOT extract as an independent satellite
batch — that risked dispatching a duplicate schema-reversion walk against C4's eventual scope. Instead: added a
cross-reference note on C4 itself flagging that its "dedicated DeFi buckets" scoping phrase is now stale (dedicated
buckets retired 2026-08-14) and must explicitly include these 3 data_types' legacy-row check when C4 executes, so
the residual isn't silently dropped by C4's stale scoping. **Still genuinely open** — carried forward until C4 (or
a dedicated live manifest check) resolves it. Not this skill's job to execute the live
`schema_version`/`pipeline_mode` manifest-distribution check itself (that's C4's/a dispatched worker's job once C4
or an equivalent is promoted); this run's job was classification + duplicate-avoidance, both done.

**Unchanged, not re-touched this run** (primary-owner rule — not defi's job, or not in today's in-scope set):

- `defi_legacy_fold_relaunch_vm_infra_flakiness_and_oom_2026_08_15.md` (infra-owned) todo 1 — still infra tranche's
  job to promote via a per-todo split.
- `estate_orphan_assessment_2026_07_21.md` (cefi-owned) todo 6 — not in today's defi Phase-0 in-scope set; still
  cefi tranche's job, still contested.

## Progress Log

- **2026-08-18 (na-eligibility-audit, defi tranche, dispatch agt-9095fb, slot 26)**: Phase 0 found only 4 of 60
  defi-tranche docs in scope (56 already-verdicted-and-unchanged). All 4 defi-owned: 2 report-only artifacts (this
  doc's predecessor and its own 2026-08-16 predecessor, both 0-open-todo, outside the verdict rubric's population,
  no action needed beyond superseding); `defi_leverage_archetypes_health_factor_wrong_source_2026_08_16.md`
  (KEEP-NA-STALE, all 8 remaining todos closed by citation to `strategy_service_centralization_fixes_2026_08_16.md`
  — full whole-set closure, see headline above); `defi_venue_e2e_batch1_deferred_followups_2026_08_17.md`
  (KEEP-NA, valid, reconfirmed unchanged). Plus 1 mandatory carry-forward re-assessment outside the incremental
  scope: `defi_migration_audit_log_2026_07_24.md`'s FOLD-3 residual, redirected (not extracted) to a cross-reference
  with `data_completion_defi_2026_07_15.md` C4 — see above. Zero conflicts required operator escalation this run
  (the one overlap found was resolved by cross-referencing, not by a competing RECLASSIFY draft, so the shared
  conflict-check's "park as BLOCKED-OPERATOR-DECISION" path was not needed). Ratchet checked at run end (see this
  run's `/done` evidence).
- **na-eligibility-audit 2026-08-18 (dispatch agt-72629d, slot 18 — duplicate concurrent dispatch)**: a second
  worker was independently dispatched for the same defi tranche at the same time and reached the same verdicts on
  all 4 in-scope docs, but initially extracted the FOLD-3 residual into a standalone
  `defi_satellite_ao_dispatch_batch17_2026_08_18.md` before discovering this doc's own (earlier-landed) C4
  cross-reference treatment. Retracted that extraction on discovery (batch17 + its finalize deleted, never
  committed) and deferred to this doc's analysis as the correct one — it alone identified the C4 overlap via a
  read of `data_completion_defi_2026_07_15.md`, which the second worker's own conflict-check grep had surfaced as a
  hit but not followed up by reading. No corpus content lost: this doc had been blind-`Write`-overwritten by the
  second worker's own duplicate draft and is restored here to its original, correct 2026-08-18 content verbatim.
- **context-scout 2026-08-20**: refreshed context_scope (2 entries)
- **2026-08-21 (dedup verification pass)**: attempted to formalize the doc's own prose `SUPERSEDED 2026-08-19` banner
  into `status: superseded` frontmatter — reverted: `check_terminal_status_archived.py` (pre-commit `plan-hygiene`
  hook) treats `status: superseded` as unconditionally TERMINAL for an issue doc and requires it already `git mv`'d to
  `plans/archive/`, which contradicts this doc's own banner (archival deliberately deferred). No open `- [ ]` todos
  exist either way. Flagging for archive instead: content-superseded, 0 open todos, successor confirmed present and
  `status: open` (active, not itself further superseded as of this check).
