---
doc_type: issue
title: plan_reconciler run findings — infra tranche (2026-08-06)
summary: >-
  Daily deep plan-reconciliation run (sharded, infra tranche). Multi-agent read-only hunter fan-out over the infra
  corpus (asset_group: infrastructure — 64 docs: 21 top-level + 43 issues) + normative refs + codex, adversarial verify
  of every candidate (refuter + confirmer), then apply confirmed easy fixes and route the hard. Run journal + findings
  ledger. author: plan_reconciler, source: agt-eff980.
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan_reconciler, reconciliation, run-findings, infra]
related: [/plans/active/infra_consolidated_closeout_2026_07_25.md]
created: 2026-08-06
author: plan_reconciler
source: agt-eff980
parent_epic: infrastructure_master
priority: P2
assigned_vm: NA
resolved_by:
locked_by:
locked_since:
---

# plan_reconciler run findings — infra tranche — 2026-08-06

Run: dispatch `agt-eff980` · role `plan_reconciler` · slot 9 · tranche **infra** · review branch
`plan_reconciler/agt-eff980`.

- **Corpus**: 64 docs tagged `asset_group: infrastructure` (21 top-level plans + 43 issue docs) — comment-stripped
  frontmatter derivation (6 docs whose only "infrastructure" match was a retag comment were excluded as other-tranche:
  artifact_pipeline_observability→ui, deployment_api_inventory_alert_gate→ui, deployment_ui_smoke_failures→ui,
  git_health_not_clean→ao, per_venue_scope_key_provisioning→cefi, silent_wrong_answer_audit→cross-cutting). 35 in the
  12h GRACE window (read-only this run), 29 writable. Normative refs (PLAN_FORMAT.md / task_template.md / INDEX.md /
  ACTIVE_INDEX.md) + codex read corpus-wide (SSOT for every shard).
- **Method**: STEP 1 FF + hygiene sweep (4 hard / 1 soft) → STEP 3 hunter fan-out (read-only) → STEP 4 adversarial
  verify (refuter + confirmer; tiebreaker on splits) → STEP 5 apply only confirmed → STEP 6 route → STEP 7 PR + result
  POST.

## Inline pre-verified (deterministic STEP-4 results, no hunter needed)

These were verified directly by the orchestrator with commands run this turn (guardrail: "provable" = ran the check):

1. **DANGLING-REF ×3** — `infra_satellite_ao_dispatch_batch5_2026_08_01.md` moved to `plans/archive/2026_08/` (verified:
   file exists there, `ls` 2026-08-06). Citing docs still point at the old `/plans/active/` path:
   - `issues/ag_closeout_audit_infra_parked_2026_08_01.md:30` (related frontmatter) — WRITABLE → fix = repoint to
     `/plans/archive/2026_08/infra_satellite_ao_dispatch_batch5_2026_08_01.md`
   - `issues/ag_closeout_audit_infra_parked_2026_08_04.md:33` (related frontmatter) — GRACE → file only
   - `issues/ag_closeout_audit_infra_parked_2026_08_06.md:35` (related frontmatter) — GRACE → file only
   - (prose mentions at 08_01:127/130/233 are bare basenames, not link paths — not violations)
   - `infra_consolidated_closeout_2026_07_25.md:378` already cites the ARCHIVE path correctly.
2. **ARCHIVE CANDIDATE (LOCKED — suggest only)** — `issues/pm_scripts_typecheck_debt_2026_06_11.md`: all 6 todos `- [x]`
   with strong evidence; cited shas verified reachable on origin/LDR + messages match: `unified-trading-pm@22b2f89d7`
   ("fix(qg): PM basedpyright is WARN-ONLY...") and `unified-trading-pm@0db8ec5f2` ("fix(cicd): fully exclude scripts/
   from PM basedpyright scan"). BUT `locked_by: live-defi-rollout` → **NEVER auto-archive; suggest + alert operator** to
   unlock-and-archive. Cross-tranche check: only infra-shard + archived docs reference it — no other ACTIVE tranche
   cites it.
3. **AG-CLOSEOUT ORPHANS ×2 (both GRACE → file only)** —
   `issues/ao_deepseek_provider_model_telemetry_mislabeled_2026_08_06.md` and
   `issues/ao_worker_context_thrash_no_recycle_escape_2026_08_06.md`: asset_group=[infrastructure] with no path (graph
   or mention) to the infra closeout family (check_ag_closeout_linkage.py, 75 corpus-wide vs baseline 69).
4. **INDEX.md drift** — `infra_consolidated_closeout_2026_07_25.md` missing as INDEX row (only prose mention at
   INDEX.md:829); `infra_satellite_ao_dispatch_batch5_2026_08_01.md` STALE row at INDEX.md:846 (archived). Fix =
   `regenerate_active_plan_inventory.py` at Phase 5 (sanctioned tooling, never hand-sync). Issues/ are NOT indexed
   (expected structure — not drift).
5. **NO terminal-status docs in infra corpus** (grep of `^status:` across all 64 — none resolved/done/complete/
   superseded in active/).
6. **ZERO-CHECKBOX sweep (infra shard): 0 docs** — no infra doc lacks checkboxes entirely.
7. **CORPUS DERIVATION LESSON** — the frontmatter asset_group value must be comment-stripped (`sed 's/#.*//'`):
   `deployment_ui_smoke_failures_daily_costs_nav_mobile`, `artifact_pipeline_observability`,
   `deployment_api_inventory_alert_gate_ondemand_only` (→ui), `git_health_not_clean` (→ao),
   `per_venue_scope_key_provisioning` (→cefi), `silent_wrong_answer_audit` (→cross-cutting) each matched
   "infrastructure" only in a retag comment ("was [infrastructure]") — all retagged by the 2026-07-30 ui launch /
   ag-closeout orthogonality fixes. Real corpus = 64 docs (21 plans + 43 issues), 35 grace / 29 writable.

## Flips verified

(none yet — populated in STEP 5)

## Contradictions

(none yet)

## Doc-drift

(none yet)

## Hygiene fixes

(none yet)

## Filed

(none yet)

## Archive candidates (operator review)

1. `issues/pm_scripts_typecheck_debt_2026_06_11.md` — every todo `[x]` with verified shas; **LOCKED**
   (`locked_by: live-defi-rollout`) → needs `[unlock-plan]` + archive (6-step ritual). Suggested, NOT archived (hard
   stop).

## Refuted (dropped by verify)

(none yet)

## Hunter results — B (governance legacy, 6 docs) — 2026-08-06

All verified quotes by hunter B (line-precise); orchestrator re-verify pending/confirming — items marked **W** are in
writable docs, **G** in grace (file-only).

1. **W** `repo_scripts_governance_audit_2026_06_18.md:26-27` — P2 frontmatter: `assigned_vm: NA` +
   `execution_scope: orchestrator-agent` (invalid pairing per task_template; sibling doc
   codex_violations_ratchet_to_five:20 corrected 2026-07-14 to `local-only`). → fix: execution_scope → local-only.
2. **W** `repo_scripts_governance_audit_2026_06_18.md:394-396` vs :346-349 — P2 same-doc contradiction: 08-02 Progress
   Log marker repeats pre-measurement "11+ repos unstamped" while the doc's own 2026-08-02 measurement says 2 files in 2
   repos. → fix: correct the marker text (measurement is authoritative, same doc).
3. **W** `repo_scripts_governance_audit_2026_06_18.md:88,93` — P3 structural: `\*\*` literal-escaped bold spans
   (mismatched openers/closers in Decision 6). → fix: unescape to `**`.
4. **W** `codex_violations_ratchet_to_five_2026_06_10.md:16` — P2 frontmatter: `related:` names
   `plans/active/ci_local_qg_parity_2026_06_08.md` + `cicd_contract_hardening_2026_06_01.md` — both archived (verified:
   only under plans/archive/2026_06/). → fix: repoint both to archive paths.
5. **W** `codex_violations_ratchet_to_five_2026_06_10.md:570` — P3: success criterion says "the four > 4,000-line files"
   then lists FIVE monoliths (registry/orchestrator/data_status/seed/server, sizes at :56-58). → fix: "four"→ "five" (or
   reword to enumerate).
6. **W** `codex_violations_ratchet_to_five_2026_06_10.md:619-621` vs :630-631,:647 — P3: standing verdict "batch2 does
   not exist as of this pass" vs own 07-30/08-02 entries saying it exists (verified: existed 2026-07-27, archived to
   plans/archive/2026_08/, covered none of the 3 items — "stay open here" outcome correct, text stale). Also stray space
   in filename "batch2_ 2026_07_27" at :631. → fix: refresh standing verdict + typo.
7. **W** `codex_violations_ratchet_to_five_2026_06_10.md:638-639` — P3: 08-02 marker "7 at entry… now 6" vs current grep
   = 5 open todos. → fix: correct the count or annotate the 7th close.
8. **W** `codex_violations_ratchet_to_five_2026_06_10.md:25` — P3: `last_updated: 2026-06-27` vs body dated 08-03. →
   fix: bump last_updated.
9. **G** `codex_vs_repo_docs_ssot_audit_2026_06_01.md:60-73` vs :192-211 — **P2 contradiction**: standing GATE-1 banner
   mandates full execution of Phases 3/4; both phases CANCELLED 2026-07-29 (main, BLK-3b8233e0) as redundant with
   per-repo satellite tasks; banner never amended (the banner itself warns stale claims would be the exact contradiction
   this gate exists to catch). → GRACE → file + operator review (banner edit is a judgment call, or mechanical amendment
   after grace).
10. **G** `codex_vs_repo_docs_ssot_audit_2026_06_01.md:31` — P3: last_updated 2026-07-28 vs body dated 08-06. → file.
11. **G** `codex_vs_repo_docs_ssot_audit_2026_06_01_finalize_2026_07_27.md:26` — P3: last_updated "2026-07-30" vs own
    banner "fixed 2026-08-06". → file. (Positive: its "3 open todos in parent" claim VERIFIES exactly.)
12. **G** `na_docs_validity_and_ao_eligibility_audit_2026_07_26.md:141-144` vs :151-153 — **P2 same-doc contradiction**:
    standing Phase-1 text asserts "~314 of ~451 NA docs never got individual attention" (444−356); the doc's own DONE
    todo (2026-07-27) says "~314 was an arithmetic error: 444−356=88". Standing text never corrected. → file (grace).
13. **G** `na_docs_validity_and_ao_eligibility_audit_2026_07_26.md:82-84` vs :437-438 — P3: "just apply" instruction for
    v2_engine stale DECOMMISSIONED checkbox vs Progress Log "deliberately left open, do not fix" — doc-internal tension,
    explicitly not-a-bug per its own note. → file as note (no action).
14. **G** `na_docs_validity_and_ao_eligibility_audit_2026_07_26.md:77-79` — P3: 451−444=7 non-live but "~2 explained". →
    file (self-flagged moving numbers).
15. **G** `na_docs_validity_and_ao_eligibility_audit_2026_07_26.md:312-322` — P2 missed-flip candidate: `[DOC] P2`
    "lst_rate_honest_coverage line 381 A2 staking leg verified DONE (strategy-service@e93902d8, cited
    defi_satellite_ao_dispatch_batch3_2026_07_26.md:191)" — flip blocked by 1000L line cap (doc is 1017L). NOTE: the
    flip TARGET is a defi-tranche doc (out of shard) → route to operator/defi shard; grace anyway.
16. **G** `na_docs_validity_and_ao_eligibility_audit_2026_07_26.md:35` — P3: last_updated "2026-07-26" vs 08-06 entry. →
    file.
17. **W** `stash_pile_workspace_cleanup_2026_06_03.md:31` — P2 frontmatter: `source:` cites
    plans/active/issues/shared_stash_pile_archive_cleanup_2026_06_01.md; file is at plans/archive/issues/. → fix:
    repoint to archive path.
18. **W** `stash_pile_workspace_cleanup_2026_06_03.md:175` — P3: Phase-4 purge todo's confirmation window target
    2026-06-10 long elapsed, never executed or re-dated. → fix: re-date/annotate (operator judgment on the purge).
19. **W** `stash_pile_workspace_cleanup_2026_06_03.md:74` — P3: unannotated prose "10 epic VMs + orchestrator VM" vs
    finding-73 note (per-epic-VM topology retired). → fix: annotate this line too (reader-verifiable).
20. **W** `stash_pile_workspace_cleanup_2026_06_03.md:23` — P3: last_updated 2026-06-27 vs 08-02/08-03 entries. → fix:
    bump.

STEP-4 verification state: items 1,4,8,10,11,16,17,20 are mechanical frontmatter/date facts — re-verifiable by grep
(quotes provided); items 2,5,6,7,9,12,15 need the quote-pair re-location + authority judgment — refuter/confirmer pass
in STEP 4. Items 18,19 need care (stash_pile purge = destructive-ish, operator-flavored; annotate only).

## Hunter results — J (mechanical adjudicator, 16 flags) — 2026-08-06

All verdicts: **real** (no parser artifacts).

1. **A** — 3 batch5 danglings CONFIRMED real (matches orchestrator inline check): 08_01:30 (W → repoint), 08_04:33 +
   08_06:35 (G → file). Prose mentions at 08_01:127/130/233 are bare basenames — not violations.
2. **B** — 2 orphans CONFIRMED real (both created 2026-08-06, grace → file; fix at next audit after grace = add
   `related:` link to `infra_consolidated_closeout_2026_07_25`). `ao_worker_context_thrash` also cited by
   governance_sweep_deferred_followups (cross-cutting, itself orphaned) — NOT a parser-artifact path.
3. **C** — INDEX.md: both real. Stale batch5 row at :846; missing closeout row at :829 (no bullet). Fix = REGEN via
   `python3 scripts/plans/regenerate_active_plan_index.py` (wired into run_hygiene_sweep.sh; auto-drops archived + adds
   every `doc_type: plan` — never hand-edit between AUTO-INDEX markers).
4. **D** — todo-format NON_CANONICAL ×15 (leading ordinal `N.`/`Nc.` before `[TAG]`, priority parsed OK):
   `fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06.md` lines 214/221/229/238/242/251/258/264 (GRACE →
   file), `self_hosted_runner_public_repo_revert_2026_08_05.md` lines 257/276 (W → strip ordinals),
   `shared_ci_workflow_repo_extraction_2026_08_06.md` lines 201/265/306/407/473 (GRACE → file). `fix_todo_format.sh`
   does NOT handle this pattern (dry-run 0) — manual strip or fixer extension.
5. **E** — clean in-shard (3 corpus violations all non-infra). Awareness: `plans/active/issues/stash_audit_reports/*` (2
   docs, `status: resolved`, `nature: record`) sit outside the checker's glob — not corpus, not violations.

## Coverage (hunters / batches / docs)

- 10 hunters launched 2026-08-06 ~22:05 UTC (model=sonnet): A infra-satellite family (10 docs), B governance legacy (6),
  C ci-adjacent (6), D issues-batch-1 (14), E issues-batch-2 (20), F issues-batch-3 (13), G missed-flip + zero-checkbox
  (whole corpus), H codex-alignment (24 plans), I AO-dispatch-readiness (10 plans), J mechanical adjudicator. Corpus =
  64 infra docs (21 plans + 43 issues) + normative refs + codex.
- Status at checkpoint: hunters still in flight (harness notifies on completion).

## Plans not reached

(none — full corpus assigned to hunters)

## RESUME HERE (post-compaction)

1. Collect the 10 hunter results (harness re-invokes on completion notifications).
2. STEP 4: dedup + adversarial verify (refuter/confirmer per candidate; tiebreaker on splits). Flips need HARD evidence:
   sha reachable on origin/LDR, artifact live (READ it), or gcloud builds describe SUCCESS.
3. STEP 5: apply confirmed on review branch `plan_reconciler/agt-eff980`:
   - repoint 08_01 batch5 ref (dangling #1 — the ONLY writable fix of the 3)
   - archive `pm_scripts_typecheck_debt` ONLY if operator unlocks (STEP 6 alert); otherwise leave + record
   - flips from hunter G + batch hunters after verify; hygiene via fix_frontmatter.py / fix_todo_format.sh
   - Phase 5 exit: regenerate inventory (fixes INDEX.md drift), re-run `run_hygiene_sweep.sh --ci --no-regen`, 0 hard
     failures gate (NOTE: the 4 hard failures are corpus-wide ratchet breaches — several non-infra; report but the shard
     only fixes its own)
4. STEP 6: POST /blocked for locked-archive + any undecidable; append lines to both `_agent_pings.md` ledgers.
5. STEP 7: prettier touched .md, commit by name, push branch, `gh pr create` (base live-defi-rollout), POST
   /api/plan_health/result with pr_url.
6. STEP 8: poll /messages, apply answers, POST /done with one_shot_complete.

Key files: findings doc = this file; corpus lists were in /tmp (recreate: `awk` frontmatter comment-stripped asset_group
match, see "CORPUS DERIVATION LESSON" above); grace set = `git log --since="12 hours ago" --name-only -- plans/active`.
