---
doc_type: issue
title: na-eligibility-audit defi tranche 2026-08-17 — consolidated operator questions and carry-forward MISCLASSIFIED_LIKELY_AO_ELIGIBLE list
summary: >-
  Phase 1b consolidation artifact for the 2026-08-17 /na-eligibility-audit defi run (23 docs classified across 5
  hunters: 16 defi-owned in-scope, 7 non-owned report-only). Not a work item itself — a batchable index of the
  DISTINCT operator-decision asks found across the tranche, plus the MISCLASSIFIED_LIKELY_AO_ELIGIBLE items still
  genuinely unresolved after this run's own RECLASSIFY pass. Supersedes na_eligibility_audit_defi_blocks_2026_08_16.md.
status: superseded
superseded_by: na_eligibility_audit_defi_blocks_2026_08_18
nature: issue
asset_group: [defi]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [defi, na-eligibility-audit, operator-questions, misclassified-carry-forward]
related:
  [
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /plans/active/defi_satellite_ao_dispatch_batch16_2026_08_17.md,
    /plans/active/issues/na_eligibility_audit_defi_blocks_2026_08_16.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
created: 2026-08-17
last_updated: 2026-08-18
# was: defi_master (epic-assignment audit 2026-08-19) -- same as its 2026-08-16
parent_epic: plan_hygiene_master
  # predecessor: a na-eligibility-audit Phase 1b consolidation run report over the defi tranche, not defi
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
    /plans/active/defi_satellite_ao_dispatch_batch16_2026_08_17.md,
  ]
supersedes: na_eligibility_audit_defi_blocks_2026_08_16
source: >-
  /na-eligibility-audit defi (2026-08-17, dispatch agt-e2dde1, slot 14) — Phase 1b consolidation across all 23
  classified docs (16 defi-owned + 7 report-only from other tranches).
---

> **📦 ARCHIVED 2026-08-22 (archival pass 2) — SUPERSEDED** by the 2026-08-18 re-run of the same audit
> (`na_eligibility_audit_defi_blocks_2026_08_18.md`, itself superseded onward — see the chain). 0 open todos,
> no lock. Kept as a historical audit-run record.
> **SUPERSEDED 2026-08-18** by
> [`na_eligibility_audit_defi_blocks_2026_08_18.md`](/plans/active/issues/na_eligibility_audit_defi_blocks_2026_08_18.md)
> — that doc carries the fresh Phase-1b consolidation for today's run, including this doc's still-genuinely-open
> carry-forward items re-assessed. Kept here (not archived) as the historical record for this specific run; archival
> deferred to a dedicated hygiene pass.

# na-eligibility-audit defi tranche 2026-08-17 — blocks + carry-forward index

## Operator questions (deduped by distinct ask, not one row per doc)

1. **Elysium delivery decisions (9 distinct asks, unchanged from 2026-08-16, one doc)** —
   `elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md`: carry-archetype attestations, real risk
   thresholds for `carry_staked_basis.yaml`, ClearLoop modelling, a falsifiable "does everything we need" checklist
   for strategy-service, disclosure-repo inventory scope, transfer mechanism, accompanying documentation scope, SLA
   reissue/side-letter terms, commercial/IP treatment of client-contributed research. Still all open/unruled as of
   today — the one new dated note (operator declining to confirm RULING 3 covers the Hyperliquid un-hide ask) is a
   non-unlock. Operator-driven, in-progress; not batchable per this doc's own HARD RULE.
2. **`strategy_service_centralization_fixes_2026_08_16.md`'s `sequential: true` scope** — today's plan_reconciler
   run flagged that several of its 18 todos read as semantically independent of todo 1's `[OPERATOR]` gate (GCS
   config-loader unification, venue-literal audit, the health-factor docstring fix this run cited, a 69-candidate
   inventory task) — worth ruling whether the whole plan should stay serialized. Not this skill's call
   (plan-authoring preference, operator-gated per SKILL.md Modes § Calibration even under trust mode) — surfaced here
   for visibility since this run cited that plan's todo 1 as a conflict-check target.
3. **Non-defi-owned, reported only** (infra/cefi tranches own these — surfaced here because this run's hunters also
   read them per the multi-tranche membership overlap):
   - `mdps_fleet_duplicate_relaunch_explosion_2026_08_15.md` (cefi-owned): its own Progress Log's final
     na-eligibility-audit entry (2026-08-16) says "2 items remain genuinely NA" but a direct grep today confirms only
     1 checkbox is actually `[ ]` open — the tally itself is stale (found by this run's report-only hunter, not
     fixed — cefi's job).
   - `defi_legacy_fold_relaunch_vm_infra_flakiness_and_oom_2026_08_15.md` (infra-owned): todo 1 (relaunch fold VM,
     `--workers 12`) reads as MISCLASSIFIED_LIKELY_AO_ELIGIBLE on its own — a sibling doc explicitly calls this exact
     relaunch "harmless (additive/idempotent, blob_exists-gated)" — but the whole-doc verdict is held back by todos
     2/3 (contingent/standing-instruction work). infra's call whether to per-todo-split this.
   - `estate_orphan_assessment_2026_07_21.md` (cefi-owned): todo 6's boundedness remains a genuinely unresolved
     2-1 contested split across 4 prior tranche passes (cefi/defi/sports disagree) — doc's own text: "Operator/
     next-toucher: rule on todo 6's boundedness, then flip deliberately." Still unruled.

## Credential/access asks

None new this run. Yesterday's TARDIS_API_KEY ask (`mtds_is_full_adapter_smoketest_findings_2026_07_07.md`,
cefi-owned) is now STALE — that doc's own live content shows the item already closed 2026-08-16
(`tardis_options_chain_credential_and_dispatch_gap_2026_08_16.md` live-verified the secret is genuinely resolvable).

## MISCLASSIFIED_LIKELY_AO_ELIGIBLE — carry-forward for the NEXT defi run only

Per the skill's close-the-loop rule, every `MISCLASSIFIED_LIKELY_AO_ELIGIBLE` tag from this run that was NOT promoted
to a real RECLASSIFY verdict is a mandatory Phase-1 input for the next `/na-eligibility-audit defi` run.

**Resolved 2026-08-17 dispatch agt-e2dde1** (promoted to RECLASSIFY, extracted to
`defi_satellite_ao_dispatch_batch16_2026_08_17.md`, or converted to a KEEP-NA-STALE citation): the Solana/multi-venue
source-label fix and gas net-cost consumer (`defi_migration_audit_log_2026_07_24.md`), the 3 plan_reconciler
corpus-hygiene items (`.tabs/2` check, batch3-finalize text, 4-doc cross-link), the LST catalogue/enumerator v2 regen
and DEX-fill shard-3 check (`lst_rate_honest_coverage_2026_07_21.md`), the subgraph-health-probe alert triage
(whole-doc RECLASSIFY), the HYPERLIQUID k-prefix casing citation-fix, and the health-factor docstring citation-fix.

**Resolved 2026-08-17 dispatch agt-f4fef7 (same-day incremental pass)**: (1)
`defi_kamino_lending_blazestake_regrowth_after_retirement_2026_08_17.md` — a NEW doc filed the same day (by
`defi_distinct_values_zero_noncanonical_dispatch_2026_08_04_finalize.md`'s own reconciliation pass), never on this
carry-forward list before; promoted to a full whole-doc RECLASSIFY (conflict-check clear against all 4 required
surfaces), extracted to its own `..._finalize.md`. (2) `defi_migration_audit_log_2026_07_24.md` line ~412
(collection-gaps retag) — re-read fresh: the doc's OWN existing text (its 2026-08-08 inline correction) already
carries the exact narrowing this carry-forward item was asking for (native_staking per-validator sub-feature,
CREDENTIAL_BLOCKED on a free-tier `helius-api-key`); no further edit was needed — the "needs narrowing" framing
carried on this list was itself stale. Closed off the list, not re-carried.

**Still genuinely open, for the next run to re-assess:**

- `defi_migration_audit_log_2026_07_24.md` line ~406 (FOLD-3-orphan-data_types) — **narrowed with live code
  evidence this run (2026-08-17, agt-f4fef7), not yet closable.** Verified live: the bucket-fold premise is moot,
  same class as the already-resolved REDIRECT todo — `risk_params_handler.py:414` and
  `vault_share_price_handler.py:261` both already call `get_write_bucket_name("market_data","defi")` (the SAME
  shared canonical bucket every migrated data_type uses, not an orphan) and both already stamp per-row
  `pipeline_mode_for_source(...)` (the same v9 source-aware pattern the 8 already-migrated data_types use). Real
  residual, still open: whether pre-existing HISTORICAL rows for these 3 data_types (written before the source-aware
  writer went live) are still legacy-shaped and need a v8→v9 backfill — needs a live `schema_version`/`pipeline_mode`
  manifest distribution check, not a code read. Correction applied inline on the source doc's own todo text this
  pass; next run (or a dispatched worker) should run that live check — if clean, this todo closes as fully moot.
- `defi_legacy_fold_relaunch_vm_infra_flakiness_and_oom_2026_08_15.md` (infra-owned) todo 1 — unchanged since the
  first 2026-08-17 pass; still infra tranche's job to promote via a per-todo split, not re-touched here (primary-owner
  rule).
- `estate_orphan_assessment_2026_07_21.md` (cefi-owned) todo 6 — not in today's defi Phase-0 in-scope set (unchanged
  since last seen); still cefi tranche's job, still contested per the first 2026-08-17 pass's note.

## Progress Log

- **2026-08-17 (na-eligibility-audit, defi tranche, dispatch agt-e2dde1)**: drafted as the Phase 1b consolidation
  artifact for this run's 23-doc classification pass (16 defi-owned + 7 report-only). See
  `defi_consolidated_closeout_2026_07_18.md` for the tranche's own AG closeout tracker.
- **2026-08-17 (na-eligibility-audit, defi tranche, dispatch agt-f4fef7, slot 14 — same-day incremental pass)**:
  Phase 0 found only 10 of 60 defi-tranche docs in scope (already-verdicted-and-unchanged the rest); 7 defi-owned
  in-scope docs classified (1 RECLASSIFY — `defi_kamino_lending_blazestake_regrowth_after_retirement_2026_08_17.md`,
  new same-day doc, whole-doc conflict-clear, paired finalize authored; 6 KEEP-NA/KEEP-NA-STALE re-confirmations,
  dated markers written), 3 non-owned report-only docs read + reported (no writes, primary-owner rule), 2 mandatory
  carry-forward MISCLASSIFIED items on `defi_migration_audit_log_2026_07_24.md` re-assessed (line ~412 closed as
  already-adequately-narrowed; line ~406 narrowed with fresh live code evidence, correction applied inline, real
  residual re-carried forward — see above). Ratchet checked at run end (see plan-flip evidence in this run's
  `/done` payload).
- **2026-08-17 (na-eligibility-audit, defi tranche, dispatch agt-4b4e7b, slot 9 — third same-day incremental
  pass)**: Phase 0 found only 6 of 60 defi-tranche docs in scope (54 already-verdicted-and-unchanged). Of those 6:
  1 defi-owned doc with real content — `defi_venue_e2e_batch1_deferred_followups_2026_08_17.md` (brand new, both
  todos cleanly `[OPERATOR]`-tagged with rationale already in its own text) — verdicted KEEP-NA, valid, marker
  written, shipped `unified-trading-pm@8d01dab9f5`; 2 defi-owned zero-open-todo report artifacts (this doc and its
  2026-08-16 predecessor) — outside the verdict rubric's "≥1 open todo" population, no action needed; 3 non-owned
  docs read + reported only per the primary-owner rule (`defi_legacy_fold_relaunch_vm_infra_flakiness_and_oom_2026_08_15.md`
  and `defi_manifest_allow_stale_fallback_incomplete_for_long_pause_2026_08_07.md`, both infra-owned, checkbox
  counts verified via grep, verdicts unchanged from prior passes; `mdps_fleet_duplicate_relaunch_explosion_2026_08_15.md`,
  cefi-owned — confirmed the stale-tally flagged by the first 2026-08-17 pass above is now resolved, cefi's own
  same-day marker already reaffirms the single genuinely-open item). Mandatory carry-forward item
  `defi_migration_audit_log_2026_07_24.md` line ~406 deliberately NOT re-touched this pass — its `[body-hash:…]`
  and marker are already current as of agt-f4fef7's own pass earlier today (content unchanged since), so
  re-opening it would duplicate same-day work rather than reflect new information; still carried forward for the
  next calendar-day run (or a dispatched worker) to execute the live schema_version/pipeline_mode
  manifest-distribution check its own text calls for. No new operator questions or MISCLASSIFIED_LIKELY_AO_ELIGIBLE
  items surfaced this pass. Ratchet checked at run end (see this run's `/done` evidence).
- **context-scout 2026-08-17**: refreshed context_scope (2 entries).
- **context-scout 2026-08-20**: refreshed context_scope (3 entries)
- **2026-08-21 (dedup verification pass)**: attempted to formalize the doc's own prose `SUPERSEDED 2026-08-18` banner
  into `status: superseded` frontmatter — reverted: `check_terminal_status_archived.py` (pre-commit `plan-hygiene`
  hook) treats `status: superseded` as unconditionally TERMINAL for an issue doc and requires it already `git mv`'d to
  `plans/archive/`, which contradicts this doc's own banner (archival deliberately deferred). No open `- [ ]` todos
  exist either way. Flagging for archive instead: content-superseded, 0 open todos, successor confirmed present and
  `status: open` (active).
