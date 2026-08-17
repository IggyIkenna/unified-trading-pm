---
doc_type: issue
title: na-eligibility-audit defi tranche 2026-08-17 — consolidated operator questions and carry-forward MISCLASSIFIED_LIKELY_AO_ELIGIBLE list
summary: >-
  Phase 1b consolidation artifact for the 2026-08-17 /na-eligibility-audit defi run (23 docs classified across 5
  hunters: 16 defi-owned in-scope, 7 non-owned report-only). Not a work item itself — a batchable index of the
  DISTINCT operator-decision asks found across the tranche, plus the MISCLASSIFIED_LIKELY_AO_ELIGIBLE items still
  genuinely unresolved after this run's own RECLASSIFY pass. Supersedes na_eligibility_audit_defi_blocks_2026_08_16.md.
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
    /plans/active/defi_satellite_ao_dispatch_batch16_2026_08_17.md,
    /plans/active/issues/na_eligibility_audit_defi_blocks_2026_08_16.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
created: 2026-08-17
last_updated: 2026-08-17
parent_epic: defi_master
assigned_vm: NA
execution_scope: local-only
priority: P3
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
resolved_by:
context_scope: [/cursor-configs/skills/na-eligibility-audit/SKILL.md]
supersedes: na_eligibility_audit_defi_blocks_2026_08_16
source: >-
  /na-eligibility-audit defi (2026-08-17, dispatch agt-e2dde1, slot 14) — Phase 1b consolidation across all 23
  classified docs (16 defi-owned + 7 report-only from other tranches).
---

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

**Resolved this run** (promoted to RECLASSIFY, extracted to `defi_satellite_ao_dispatch_batch16_2026_08_17.md`, or
converted to a KEEP-NA-STALE citation — excluded from the list below): the Solana/multi-venue source-label fix and
gas net-cost consumer (`defi_migration_audit_log_2026_07_24.md`), the 3 plan_reconciler corpus-hygiene items
(`.tabs/2` check, batch3-finalize text, 4-doc cross-link), the LST catalogue/enumerator v2 regen and DEX-fill
shard-3 check (`lst_rate_honest_coverage_2026_07_21.md`), the subgraph-health-probe alert triage (whole-doc
RECLASSIFY), the HYPERLIQUID k-prefix casing citation-fix, and the health-factor docstring citation-fix.

**Still genuinely open, for the next run to re-assess:**

- `defi_migration_audit_log_2026_07_24.md` line ~406 (FOLD-3-orphan-data_types) — premise now inverted per the
  retired-dedicated-bucket-architecture finding; needs rewording toward the narrower v9-shape/manifest-coverage
  verification before a clean extraction is possible. Flagged, not edited this run (same disposition as
  2026-08-16's pass — a low-confidence edit given the long cross-referenced text).
- `defi_migration_audit_log_2026_07_24.md` line ~412 (collection-gaps retag) — mostly-resolved (eigenlayer_rewards
  scheduling confirmed live), needs narrowing to its residual scope (native_staking per-validator sub-feature,
  CREDENTIAL_BLOCKED on a free-tier `helius-api-key`). Same flagged-not-edited disposition as 2026-08-16.
- `defi_legacy_fold_relaunch_vm_infra_flakiness_and_oom_2026_08_15.md` (infra-owned) todo 1 — see operator-questions
  §3 above; infra tranche's job to promote via a per-todo split.
- `estate_orphan_assessment_2026_07_21.md` (cefi-owned) todo 6 — see operator-questions §3 above; cefi tranche's
  job, still contested.

## Progress Log

- **2026-08-17 (na-eligibility-audit, defi tranche, dispatch agt-e2dde1)**: drafted as the Phase 1b consolidation
  artifact for this run's 23-doc classification pass (16 defi-owned + 7 report-only). See
  `defi_consolidated_closeout_2026_07_18.md` for the tranche's own AG closeout tracker.
