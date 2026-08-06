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

## Hunter results — A (infra-satellite batch family, 10 docs) — 2026-08-06

11 findings; hunter measured grace per-doc: batch1_finalize (08-03) + batch3_finalize (~14h) writable; batch1, batch3,
batch6, batch7, hub grace (re-verified at apply). Clean docs: batch4, batch6_finalize, batch7_finalize.

1. **W** `infra_satellite_ao_dispatch_batch1_finalize_2026_07_26.md:66-67` — P2: body banner still says "`status: draft`
   — NOT ingested, NOT dispatched... flips only with parent on operator approval" vs frontmatter `status: active` (:16);
   stale since the 2026-07-30 no-double-gate ruling (233ebd614), parent batch active. → fix: replace banner with
   accurate note (draft-gate mechanism retired by ruling).
2. **W** `infra_satellite_ao_dispatch_batch3_finalize_2026_07_30.md:59-60` — P2: "⚠️ STATUS: `draft`" banner vs
   frontmatter active (:13); parent batch3 active since authoring — doubly stale. → fix: strike banner.
3. **G** `infra_consolidated_closeout_2026_07_25.md:473-478` + `batch7_2026_08_04.md:169-170` — P2: hub 08-03/08-04 +
   batch7 Deferred claim batch3's `assigned_vm` flip "landed BLANK" — FALSE per `git show dfdb0887f` (flip landed
   `planning` in valid multi-line YAML) + batch3 L39 now single-line `planning` (001112aaf). The "blank" verdicts
   misread block-scalar format. Corroborates D-2 (ag_closeout "5th day blank" claim). GRACE — report only.
4. **W** `infra_satellite_ao_dispatch_batch1_2026_07_26.md:886-887` — P2: "14 deferred items are conflict-gated" vs the
   doc's own Deferred section = 18 items, exactly 10 conflict-gated (1-10; 11-13 resolved-by-logic, 14 BLOCKED-OPERATOR,
   15-17 TOO-LARGE, 18 human-only); finalize twin (:103) + hub (:271) both say 10. → fix: 14→10.
5. **W** `infra_satellite_ao_dispatch_batch1_finalize_2026_07_26.md:70-71,77,L8` — P2: scoping text says "all 25 tasks"
   / "batch 1's 25 now-done todos" but batch1 now has 30 todos (5 added post-creation: G-TRACE, stash-pile smoke test,
   slot-git-status-report, reference-path hunter, prefix-scoped lifecycle; verified at creation commit 89469c6b2 = 25).
   A literal worker run would under-reconcile 5 todos. → fix: 25→30 with a note.
6. **G** `infra_consolidated_closeout_2026_07_25.md:109,124-125` vs `:206-207,327` — P2: org-migration cancellation
   dated two ways — CANCELLED 2026-07-27 (citing vintage-audit §5#39, which says "still undecided") vs 2026-07-28
   (§5-RESOLVED #36, DONE `unified-trading-pm@cd5c0bde1`). Source audit records the ruling DONE 07-28 → 07-27 cites
   misattribute. GRACE — report only.
7. **W** `infra_satellite_ao_dispatch_batch1_2026_07_26.md:702` — P3: [x] REVIEW todo evidence ends with literal
   `pm@<commit-pending>`; real ship = `b555f4b86` "extend /plan-reconcile with moved-doc referrer hunter" (SKILL.md L305
   entry, landed 08-02). → fix: replace placeholder with b555f4b86 (verify reachable first).
8. **G** `infra_satellite_ao_dispatch_batch6_2026_08_02.md:162-163` — P3: garbled operator-gate sentence ("Flipped from
   `draft`... is the operator's call" — flip already happened); L116-117 "(batch is still `status: draft`)" stale after
   08-06 activation. GRACE — report only.
9. **G** `infra_satellite_ao_dispatch_batch7_2026_08_04.md:178-182` — P3: "that source doc's own finalize twin will
   citation-close them" — na-eligibility source doc has NO finalize twin (verified find); actual mechanism = batch7's
   OWN finalize twin todo 1 (:66-67). Same garbled template tail as batch6 (shared template bug). GRACE — report only.
10. **W** `infra_satellite_ao_dispatch_batch3_finalize_2026_07_30.md:28` — P3: `last_updated` "2026-07-30" vs 08-06 edit
    (7accf8ecf). → fix: bump. (batch1_finalize:28 same drift vs 08-03 edit 99ebc3137 — same fix.)
11. **G** `infra_consolidated_closeout_2026_07_25.md:31` — P3: `last_updated` "2026-08-04" vs 08-06 Progress Log entry
    (:220). GRACE — report only.

Digest extras (all grace): batch1 L974 "24/25 shipped, only agent-orchestrator remains" superseded ~26 min later by the
real flip (agent-orchestrator@89ca717, sha verified) — never annotated; batch1 L4/L12 "25 AO-eligible todos" historical
vs 30; batch3 L80 "22 open of 25" stale historical snapshot (current 30/1 open); batch3 L154 genuine open [BACKEND] P3
git-health root-cause — no missed flip.

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

## Hunter results — C (ci-adjacent infra, 6 docs) — 2026-08-06

5 of 6 docs GRACE (all but `self_hosted_runner_public_repo_revert` = 14.1h, writable). Out-of-shard note:
`artifact_pipeline_observability` is ui-tranche (retagged 2026-07-30) — its findings (s3 EMPTY-vs-populated :189 vs
:360; 4GiB vs 16GiB budget :459 vs :214; two Progress Log headings :737/:943; mangled bug numbering :260-267;
last_updated :43; "active plan not codex" mislabel :101; issue ref at wrong location :894-896; default-view banner
:411-418 vs :432-434; `_...*` markers :283; missed-flip Phase-5 issue-doc todo :652 vs DONE :939) are REPORTED for the
ui shard, not actioned here.

1. **G** `shared_ci_workflow_repo_extraction_2026_08_06.md:151-152` — **P1**: "image-build-gate.yml hand-maintained,
   referenced nowhere in rollout-workflow-templates.sh" vs `self_hosted_runner...:183-186` (hardcoded fleet-wide) + own
   todo 18 (:459-461) + revert-incident log (:615-618). Todo 3's premise is FALSE. → file (grace).
2. **W** `self_hosted_runner_public_repo_revert_2026_08_05.md:263-265` — **P1**: open todo 24 instructs editing PM's own
   copy of `python-quality-gates-v2.yml` — DELETED by shared_ci Phase 5 (`shared_ci...:434-436`). Worker executing as
   written looks for a deleted file. Real remaining target = caller-stub `with:` + allowlist. → live in-flight work;
   STEP-4 verify then decide (annotate vs file).
3. **G** `fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06.md:118-119` — **P2**: "8 files BYTE-IDENTICAL
   across every repo" vs own todo-1 findings "Distribution is NOT uniform" (:275-280, PM lacks 4 of 9). Summary :98 same
   overclaim. → file (grace).
4. **G** `shared_ci_workflow_repo_extraction_2026_08_06.md:407-415` — **P2 missed-flip candidate**: todo 15
   (agent-audit.yml @main re-point sweep) evidence = completed grep; substance executed by done todo 23 + Phase 5
   (:498-501,:518-519 zero remaining `uses:.*unified-trading-pm/.github/`). Only @main-vs-@ldr nuance may remain. →
   GRACE → file for post-grace flip verification.
5. **G** `ci_runner_fleet_split_and_vm_rightsizing_2026_08_03.md:116-117` — **P2**: `[x]` todo 1 body "PAUSED HERE...
   not proceeding until operator confirms" vs executed todos 3+ with dated evidence + no logged resume (:386-390 hold,
   :123 VM launched). Status-vs-body disagreement. → file (grace).
6. **G** `ci_runner_fleet_split_and_vm_rightsizing_2026_08_03.md:372,401` — **P2 structural**: two `## Progress Log`
   headings, entries out of chronological order (also artifact_pipeline :737/:943 same class). → file (grace).
7. **G** `ci_pipeline_speed_and_cost_redesign_2026_08_05.md:294-295` — **P2 flip-CANDIDATE only**: todo cites shipped
   SHAs (b656cb87b/23f1ad262/91ebc6584) but self-declares speedup NOT confirmed + "Do NOT roll out" — **NOT a flip**
   (completion criterion unmet). → file (grace).
8. **G** `ci_pipeline_speed_and_cost_redesign_2026_08_05.md:49` — P3 last_updated vs :331 08-06 entry. → file.
9. **G** `fleet_workflow_template_dedup...:5-6` — P3 summary "2 files" vs doc2's real 5-file surface (:125-126). → file.
10. **G** `shared_ci_workflow_repo_extraction_2026_08_06.md:423-424` — P3 45 vs 44 notify-slack consumers (vs
    fleet_workflow:140). → file.
11. **W** `self_hosted_runner_public_repo_revert_2026_08_05.md:97-99` — P3 body "Only 8 PRIVATE" vs own Correction
    banner :8-11 (PM flipped public 2026-08-06, now 18/7) — banner-corrected in-doc, body stale. → STEP-4 verify; align
    body or rely on banner.
12. **W** `self_hosted_runner_public_repo_revert_2026_08_05.md:135-137` — P3 "~96%+" cost attribution vs
    ci_pipeline:118-119 (PM = 41.0% July, "large majority" — 96% not derivable). → STEP-4 verify; fix attribution.
13. **G** `fleet_workflow_template_dedup...:242-250` — **P2**: todo 7 (delete 9 template sources) vs self_hosted_runner
    todo 24 (re-run rollout to regenerate exactly those for PM) — mechanism conflict, whichever ships first invalidates
    the other; ordering needs explicit decision. → file + route (operator).
14. **G** `shared_ci_workflow_repo_extraction_2026_08_06.md:546-548` — P3 digest: na-eligibility entry "7c/7d
    [OPERATOR]" stale — 7d done (:295-305). → file.

## Hunter results — I (AO-dispatch-readiness, 10 plans / 26 todos) — 2026-08-06

ALL findings in GRACE docs → file-only. Part B (delete/VM-launch gating): 0 infra-corpus flags (the 2 flagged docs are
sports/cefi, out of shard).

1. **G** `infra_satellite_ao_dispatch_batch6_2026_08_02.md:126` — P3: todo line-1 cites `base-service.sh:322`
   (line-number ref, goes stale) — cite by symbol (`UV_LINK_MODE=`). Todo otherwise line-1 complete + Done-when +
   bounded. → file (post-grace one-word fix).
2. **G** `infra_satellite_ao_dispatch_batch7_2026_08_04.md:148` — P3: `live_event_log/main.tf:9` line-number ref in
   read-only investigate todo — cite the inheritance comment by content. → file (post-grace one-word fix).
3. **G** `ci_runner_fleet_split_and_vm_rightsizing_2026_08_03.md:325` — **P2 delete-tagging/ops-gate**: downsize todo
   claims "pre-authorized... do now, no separate scheduling needed" vs the plan's OWN recorded hold (Progress Log
   :223-224 "wait for explicit confirmation"; body :82 "Runners migrate off i-0c9b283b31d6b5ca7 BEFORE it is
   downsized"). No `[OPERATOR]` tag; hold is prose-only + machine-unenforced. → file + ROUTE (operator) — live
   dispatch-risk class.
4. **G** `ci_pipeline_speed_and_cost_redesign_2026_08_05.md:260` — P2: warm-git-object-cache todo has NO Done-when
   ("Open mystery, NOT resolved", open-ended investigation; KEEP-NA). → file (informational).
5. **G** `fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06.md:242` — P3 ordering: hard intra-plan chain
   (todo 7 gated on 3-6; todo 8 after 3-7; todo 4 after 3) rests on prose only — `sequential:` unset, no "not
   machine-enforced" guard note; accidental NA→planning flip would dispatch 3-8 concurrently. → file (add guard note or
   sequential: true).
6. Clean reports (no findings): infra_satellite batch1 (:207) / batch3 (:154) / batch7 todos 1-2; self_hosted_runner
   todos 20/24; shared_ci todos 3/15/20/7c/7f; infra_consolidated_closeout's 3 `[REVIEW]` roll-ups (correctly
   non-dispatchable).

## Hunter results — G (missed-flip + zero-checkbox sweep, 69 docs / 186 open todos) — 2026-08-06

Zero-checkbox: **1 doc** — `issues/client_reporting_api_promote_wedge_backmerge_dead_2026_08_06.md` (0 open / 0 checked,
prose-only, status: open, P1, created today from escalation agt-57645a; promotion wedge UNRESOLVED) → needs
convert-to-todos or stay-as-is (orchestrator call; doc is GRACE). All 47 issues `status: open` — no resolved-unclosed in
shard. FLIP candidates (all but #4 need STEP-4 verify):

1. **P0** `codex_violations_ratchet_to_five_2026_06_10.md:373` — todo "Reconcile UAC defi_position.py STALE threshold"
   carries "**MIGRATED 2026-07-27**" + target todo DONE: `infra_satellite_ao_dispatch_batch1:436`
   `- [x] ✅ [CODE] P3 ... unified-api-contracts@194f3f7f ... test_defi_position.py pinning 1.15` (batch1:441). **W**
   doc. Flip candidate — verify sha 194f3f7f reachable.
2. **P0** `na_docs_validity_and_ao_eligibility_audit_2026_07_26.md:312` — `[DOC] P2` lst_rate A2 flip VERIFIED DONE
   (`strategy-service@e93902d8`, cited defi_satellite_ao_dispatch_batch3:191) but mechanically BLOCKED by 1000L line cap
   (target doc 1017L; the scoped-mode exception requires zero-deletion diffs). **G** → route: cap-waiver / long-form
   flip (operator) — ALSO the flip target is a defi doc (out of shard).
3. **P1** `shared_ci_workflow_repo_extraction_2026_08_06.md:407` — todo 15 done-when subsumed by done todo 23's sweep
   (:498-530, zero remaining refs, dependents listed). **G** → file for post-grace flip verification.
4. **P1** `stash_pile_workspace_cleanup_2026_06_03.md:126` — smoke-test todo **DONE 2026-08-04
   `unified-trading-pm@1fa747856`** per `infra_satellite_ao_dispatch_batch1:661-675` (ran audit-stash-pile.sh, 76
   stashes, 1 true-positive hand-verified — only 1 redundant call existed so ≥3 done-when variance explained; report
   `stash_audit_reports/stash-audit-ip-172-31-5-118-20260804.md`; no stash dropped). **W** doc — but cross-doc evidence;
   verify sha 1fa747856 + batch1 evidence line, then flip (the todo is the ORIGIN doc for the batch1 todo — flipping =
   noting MIGRATED-DONE). Careful: task says "no `--apply`" was run — the todo's own done-when (≥3 hand-verified) not
   fully met; report + leave open OR flip with DEFERRED annotation. → STEP-4 decide.
5. Out-of-shard echo: `deployment_ui_smoke_failures_daily_costs_nav_mobile_2026_07_21.md` (0 open / 3 checked) and
   `pm_scripts_typecheck_debt_2026_06_11.md` (0 open / 6 checked) flagged as archive-candidate shapes — the former is
   ui-tranche (ui shard owns), the latter is the LOCKED archive candidate already listed above.

## Hunter results — D (infra issues batch 1, 14 docs) — 2026-08-06

16 findings; hunter reported the ENTIRE batch grace — orchestrator re-measured individually: 13 of 14 are grace,
`ag_closeout_audit_infra_parked_2026_08_01.md` is WRITABLE (14h) — its findings stay report-only anyway (same-day
in-flight audit-family doc, collision risk). Root cause of same-day staleness: governance sweep `de1d795de1` (21 files,
2026-08-06 ~15:04 UTC) landed after docs' carried-forward sections were drafted.

1. **G** `ag_closeout_audit_infra_parked_2026_08_06.md:157-159` vs `:208-211` — P1 internal contradiction: carried item
   4 claims all 4 draft batches "still `status: draft`, zero flipped" vs todo 4 RESOLVED (sweep
   `unified-trading-pm@de1d795de1`). Live-verified: batch4/6/7 active, batch5 archived — the F14 register is stale, todo
   4's flip is accurate. Same stale claim carried in _08_04:157-159.
2. **G** `ag_closeout_audit_infra_parked_2026_08_06.md:148-151` — P1: F10 carried item 2 + [OPERATOR] P1 todo 1 claim
   batch3:39 is still blank `assigned_vm:` (5th consecutive day); live grep = `assigned_vm: planning` (fixed 08-02,
   _08_03:273-274 verified). Stale operands → the [OPERATOR] P1 "re-apply" todos at _08_06:198-200 and _08_04:161-163
   are flip candidates (verify at STEP 4).
3. **G** `cloud_run_traffic_pin_silent_freeze_alert_wiring_2026_08_05.md:203-209` — P2: 08-06 archive-audit note says
   the (a)(b)(c) Slack-routing items "have no separate `- [ ]` todos" but the Follow-ups section has exactly that open
   `[INFRA] P2` todo (both added same commit 0acf56a54). Also contradicts _08_06:95's F15 "zero open checkboxes" claim.
4. **G** `bucket_iam_p2_tier_sa_scope_gap_and_default_compute_sa_overprivilege_2026_07_30.md:301-310` — P2:
   archive-audit note asserts the 30-launcher follow-up "never converted to a `- [ ]` todo" (follow-up-must-be-todo
   violation) but the doc's Follow-ups section contains exactly that open `[CODE] P3` todo (:301-303). Premise false;
   doc correctly NOT archive-ready.
5. **G** `ao_self_pull_wedged_by_main_inbox_untracked_file_2026_07_30.md:227` vs ag_closeout docs — P2: doc 7 says the
   tranche-level mistag deadlock "no longer applies" (owning_tranche() fallback fixed 08-02, `--tranche ao` now includes
   it) but ag_closeout _08_04:117-119/_08_06 still frame F6 as "BLOCKED-OPERATOR-DECISION with 3 unresolved options"
   (option C = change the fallback). Mistag itself (line 23) persists so the retag todo stays legitimately open; the
   deadlock framing is stale. Report-only.
6. **G** `ag_closeout_audit_infra_parked_2026_08_01.md:199-212` — P2 false-complete flip: todo 6 [x] CLOSED 2026-08-06
   while its body still asserts "The retag half of this todo is still open and undone" (undigested 08-03 STALE note);
   retag itself IS done (live `asset_group: [ao]` verified). Dangling fragments :191/:216, backtick glitches :102. Doc
   is WRITABLE but same-day in-flight → file-only (collision risk).
7. **G** `bucket_iam_p2_god_sa_removal_before_runtime_rewire_2026_07_30.md:149-152` — P2 **AO-DISPATCH candidate**: open
   `[TERRAFORM] P2` carries 08-06 note — operator ruled APPROVED in sibling doc P2.1b
   (bucket_iam_write_protection_per_tier :297, `[OPERATOR]` tag removed), gate satisfied (P2.2e [x] 08-04 @ :593; P2.3
   [x] 08-02 @ :604). Execution itself NOT done (plan P2.1b still `- [ ]`) → dispatch candidate, not a close. → ROUTE
   (STEP 6).
8. **G** `ao_deepseek_provider_model_telemetry_mislabeled_2026_08_06.md:10-11` — P2 dead ref: cites
   `ao_deepseek_model_flag_misalignment_2026_08_05` — no such file anywhere in plans/. No `last_updated` field.
9. **G** `ao_worker_context_thrash_no_recycle_escape_2026_08_06.md:11-12` — P2 dead ref: cites
   `cefi_tardis_derivative_ticker_historical_gap_ao_context_pct_stuck_post_compact_2026_08_06` — nonexistent; `related:`
   empty (:27) despite the cross-ref. No `last_updated`.
10. **G** `cve_affected_pinned_deps_remediation_2026_06_18.md:358-394` — P2 resolved-but-unclosed candidate: sole open
    todo documented twice (07-31) as inherently unbounded, intentionally left unflipped with reason PARKED; CVE exercise
    fully complete (all ignores dropped, 21-repo cryptography sweep) → close/convert-to-standing-check candidate
    (operator). + whitespace corruption (230-291, 302-304, 332-340, 361-394 — hundreds of lead spaces), truncated
    summary table, last_updated 07-30 vs 08-05 body, `issues/fleet_fastapi...` cite to archived doc.
11. **G** `client_reporting_api_promote_wedge_backmerge_dead_2026_08_06.md:95` — P2 zero-checkbox escalation record
    (status open, assigned_vm: planning): 4-step Recommended resolution is prose-only; "fleet recovery" tracker (:103)
    names no doc/todo; no `last_updated`. Same doc as G-hunter zero-checkbox finding — orchestration decision pending
    (convert-to-todos vs stay-as-is).
12. **G** `cloud_run_traffic_pin_silent_freeze_alert_wiring_2026_08_05.md:174` — P2 unresolved evidence placeholder: [x]
    todo 3 cites `unified-trading-pm@<SHA>`; todo 1 [x] false-complete (body lists NOT-DONE (a)(b)(c)) — mitigated only
    by the open Follow-ups todo (:203-205).
13. **G** last_updated drift cluster — `ag_closeout_audit_infra_parked` _07_31:36 (07-31 vs 08-02/08-06), _08_01:40,
    _08_03:49, _08_04:46, `bucket_iam_p2_god_sa_removal...:42`, `bucket_iam_p2_tier_sa_scope_gap...:48`,
    `cve_affected_pinned_deps...:35`; docs 6/8/11/12 (ci_registry_drift, ao_deepseek, ao_worker_context_thrash,
    client_reporting) lack `last_updated` entirely.
14. **G** `ag_closeout_audit_infra_parked_2026_08_06.md:143-148` — P3 day-count inconsistency: F6 "4th consecutive day"
    (flagged 07-31, 5 runs by audit record) vs F10 "5th consecutive day" (flagged 08-02, 3 runs) — counts wrong both
    ways.
15. **G** `ag_closeout_audit_infra_parked_2026_07_31.md:166-169` — P2: finding-3 retag todo open + 08-06 entry still
    frames ao_self_pull as "owning-tranche deadlock, BLOCKED-OPERATOR-DECISION" (contradicts doc 7:227, same as #5).
16. **G** `bucket_iam_p2_god_sa_removal...:127-137,159-172` +
    `ci_registry_drift_uac_utl_stale_tag_version_conflict_2026_07_26.md:122-148` — clean-pass notes: retag addenda
    consistent; ci_registry todo 3 correctly open (3-consecutive-green done-when unmet), todo 4 CONCLUSIVE [x]. No
    findings beyond the above.

## Hunter results — E (infra issues batch 2, 20 docs) — 2026-08-06

19 findings; hunter over-marked grace — orchestrator re-measured: deployment_service_live_event_log,
na_doc_tranche_inventory, docs_reconcile_autonomous_sweep, na_eligibility_incremental_diff are WRITABLE (14h), so
E-5/E-14 become fixes; E-8/9/E-15 stay report/route (content-level, STEP-4-decided). Two flip-candidate-INVERSES ([x] on
not-fixed work) + one spurious-lock discovery (unlocks an archival candidate). Out-of-shard flags routed, not actioned.

1. **G** `defi_gas_fees_legacy_purge_manifest_step_blocked_vm_infra_flakiness_2026_08_05.md:120-127` — P1 flip-inverse:
   `- [x]` on "DID NOT RECUR 2026-08-06 — inconclusive, not fixed" + "Left open as a real latent risk" (unbounded gsutil
   code unchanged). Box [x] while text says not-fixed → must stay open or latent risk needs its own tracker. GRACE —
   report only. (:46 bare source ref, P3.)
2. **G** `deployment_api_cloud_run_coldstart_flaky_exit0_blocks_prd_sa_cutover_2026_07_31.md:158` vs `:236-237,252` — P1
   flip-inverse: [x] INFRA P3 "DONE 2026-08-04 (operator-forced cutover)" while Progress Log says "leaving P3 open
   (SIGABRT root cause still unresolved... not a clean resolution)"; 08-06 archive audit agrees. Follow-up [INFRA] P1
   open at :247. GRACE — report only. (:41 last_updated stale, P3.)
3. **G** `deployment_registry_dualwrite_flag_not_propagated_to_vm_launchers_2026_07_30.md:170-212` — P2 structural:
   soak-evidence block has runaway leading whitespace (lines 855-932 chars; :178 starts with ~170 spaces) — renders as a
   giant code block; exact class fixed in plan_quality_four_line (739c7411b) but never here. GRACE — report only. (:178
   bare dead cite of archived setup_data_pipeline doc, P3.)
4. **G** `deployment_scripts_bucket_soft_delete_retention_drift_2026_07_31.md:104-110` — P2: [x] "Final drain
   confirmation on/after 2026-08-09" admits its own done-when (≤9% bloat) NOT met — "This flip records the 08-06
   verification cycle, NOT the final drain"; duplicate-titled `- [ ]` sibling (:114-121) is the honest tracker. GRACE —
   report only. (:106 "byte-identical" vs 3 differing totals; :29 last_updated stale — both P3.)
5. **W?** `deployment_service_live_event_log_disconnected_tofu_root_2026_08_03.md:32` — P3: last_updated 08-03 vs 08-06
   entries. No material contradiction; [OPERATOR] P3 legitimately open (batch7 holds the bounded read-only half). → bump
   (verify grace at apply).
6. **G** `deployment_ui_smoke_failures_daily_costs_nav_mobile_2026_07_21.md:34` — P2 **spurious lock**:
   `locked_since: 2026-05-21` PREDATES `created: 2026-07-21` by 2 months (copy-paste artifact) — the `locked_by` lock
   may be invalid, unblocking archival. OUT OF SHARD (ui-tranche, retagged 07-30) — ROUTE to ui shard.
7. **G** `deployment_ui_smoke_failures_daily_costs_nav_mobile_2026_07_21.md:9` — P2 resolved-unclosed: all 3 todos [x]
   (:59,70,77), Progress Log "all 3 items... now done" (:113-114), `status: open` — archival candidate blocked only by
   the suspect lock (#6). OUT OF SHARD — ROUTE to ui shard (this matches G-hunter's archive-candidate shape flag).
8. **G** `docs_reconcile_autonomous_sweep_2026_07_30.md:228` vs `:367-368` — P1: P0-A [x] "RESOLVED 2026-08-02, option A
   applied" vs the doc's OWN 08-03 end-to-end audit listing P0-A among "2 survivors" still-open authority calls; no
   Progress Log entry records the flip. Irreconcilable in-doc. GRACE — report only.
9. **G** `docs_reconcile_autonomous_sweep_2026_07_30.md:236-238` — P2: P0-A resolution's only shipped-SHA evidence "does
   not resolve in any local clone, most likely a transcription typo" — a P0 outage-class (08-15 cliff) resolution with
   unresolvable evidence. Orchestrator should re-verify the `grep -rl "last_reviewed: 2026-05-17"` zero-match claim
   (:232-233) rather than trust the typo'd SHA. GRACE — report only + route.
10. **W** `host_root_disk_full_transient_2026_07_13.md:42` — P2: `related:` cites qg_host_governor_severe_contention at
    non-existent ACTIVE path + missing leading slash; `context_scope:` (:35) cites the ARCHIVED path correctly. → fix:
    repoint related to /plans/archive/issues/ path.
11. **G** `issue_docs_remediation_sweep_2026_06_02.md:263-268,437-445` — P2: mid-sentence "CLOSED 2026-08-06
    (na-eligibility-audit)" insertions mangle D8 + G-TRACE todos (original sentences broken, lone "_provider name_"
    remnant); both boxes `- [x] ✅` while inserted text says "checkbox never flipped" — direct self-contradiction.
    CLOSED claims themselves backed (batch1:444/:722 verified contain the ships). GRACE — report only.
12. **G** `issue_docs_remediation_sweep_2026_06_02.md:22-47` — P2: related/source list 8+ bare-path refs at ACTIVE
    locations for docs that are ARCHIVED (gcs_hive_partition, alerting_fp_rate [archived per own body :334],
    softdelete_log_churn, api_host_chronic_impairment, cefi_processed_candles, mdps_state_adapter,
    running_vm_fleet_status, uniswap_v3_28k); context_scope cites them correctly. GRACE — report only.
13. **W** `legacy_bucket_template_literals_2026_07_16.md:28-33` — P2: `related:` uses BANNED `../`-relative refs
    (`../sports_legacy_bucket_cutover...`, `../../epics/sports_master.md`) resolving to dead ACTIVE paths; context_scope
    cites the same targets archived+slash-correct. → fix: repoint to /plans/archive/2026_07/ + /plans/epics/ forms. (:36
    last_updated 07-16 stale — bump, P3.)
14. **W?** `na_doc_tranche_inventory_stale_citation_membership_cross_contamination_2026_07_29.md:52` — P3: last_updated
    "2026-07-30" vs 08-06 KEEP-NA entry. → bump (verify grace at apply).
15. **G** `na_eligibility_incremental_diff_false_positive_on_frontmatter_only_backfills_2026_08_03.md:166-168` — P1:
    Progress Log 08-06 parks BLOCKED-OPERATOR-DECISION on premise "batch7 `status: draft`" — FALSE: batch7 is
    `status: active` (frontmatter :18), already holds BOTH claims as open `- [ ]` todos, finalize twin exists → option
    (A) appears to have happened; this doc's 2 open todos may be double-tracked with batch7. → ROUTE: operator
    re-adjudication needed.
16. **G** `na_inventory_counts_fenced_code_block_checkboxes_as_open_todos_2026_08_02.md:97` vs
    `gate_on_depends_wiring_gap_defi_dex_pool_finalize_2026_07_25.md:351` — P2: doc-18 table claims gate_on_depends has
    "Real: 0" open todos ("both real todos `- [x]`") but the target has a REAL open `[BACKEND] P1` outside any fence
    (:351, added 08-02, reinforced 08-06) → misclassified as 0-open archival candidate. (Fence analysis itself correct —
    the 5 phantom todos ARE fenced.) GRACE — report only.
17. **G** `plan_quality_four_line_defense_architecture_2026_07_23.md:189,263` — P3: cites
    `plan_line_cap_remediation_2026_07_23.md` as "still `status: open`" / "the tracked owner" — now ARCHIVED with
    `status: resolved`; 5 cites all bare filenames. GRACE — report only. POSITIVE: claimed 08-06 whitespace fix VERIFIED
    applied (739c7411b; no >40-space lines) — do NOT re-fix.
18. **G** `per_venue_scope_key_provisioning_incomplete_2026_07_23.md:57` — P3: body cite missing leading slash (target
    exists archived). OUT OF SHARD (cefi-tranche) — report only.
19. Clean docs (no findings): deployment_api_inventory_alert_gate (ui, single open [HUMAN] P2 KEEP-NA),
    e2e_login_persona_handoff_helper, git_health_not_clean (citations live — batch3:154 open todo matches),
    gitignore_sync_script (todo 1 [x] pm@78a3740bf real), lc_verify_tarball_freshness.

## Hunter results — F (infra issues batch 3, 13 docs) — 2026-08-06

19 findings; 2 docs clean (production_readiness_checklist_file_missing, silent_wrong_answer_audit). No true missed-flip
candidates (no open todo cites a sha/PR/build); closest analogs are flipped-[x]-with-placeholder + unverified done-when.

1. **W** `s5_7_required_docs_gaps_2026_07_29.md:4,9` vs `:60-76` — P2 contradiction: title+summary claim "9 of 17" repos
   miss required docs but the doc's own table lists 8 missing + 9 OK rows. → fix: correct to 8/17 (table is the truth) +
   summary line 9.
2. **G** `vm_launcher_class_b_no_stall_kill_gap_2026_07_27.md:4-5,118` vs `:107-116` — P2 contradiction: "6 of the 8"
   have no protective layer but the table marks 7 of 8 False; 08-03 NOTE (:153-155) dropped gcs-migration-bundle without
   reconciling the count. GRACE — report only.
3. **G** `plan_reconcile_autonomous_sweep_2026_07_30.md:11-12` vs `:71,89-90` — P2 contradiction: summary lists the
   codex dangling-ref as unresolvable but body shows P1-A RESOLVED with option A APPLIED by the same run. GRACE — report
   only.
4. **G** `plan_reconcile_autonomous_sweep_2026_07_30.md:101-105` — P2 contradiction: P2-B parks
   `cicd_mvp_ldr_to_main_pipeline` as locked-unarchivable; it was operator-unlocked + archived 2026-07-31 (banner at
   archive path :64-66). Parked question already acted on. GRACE — report only.
5. **G** `plan_reconcile_autonomous_sweep_2026_07_30.md:201-209` — P3: P2-D presents stale-agentwork-clone deletion as
   open, no cross-ref to the 07-30 ruling (option A, bundle-then-delete) + gate fix in sibling doc 10
   (stale_agentwork_scratch_clone:93-101). GRACE — report only.
6. **G** `pm_scripts_typecheck_debt_2026_06_11.md:119` vs `:32` — P2: body cites
   `plans/active/issues/plan_reconciliation_operator_decisions_2026_07_11.md` at ACTIVE path; file lives at
   `plans/archive/issues/` (dangling). Also second confirmation this doc was MISSED by the 07-31 "7 fully-done locked
   docs" unlock sweep (all 6 todos [x], status open). LOCKED — annotate only, no edit.
7. **G** `pm_scripts_typecheck_debt_2026_06_11.md:108` — P2: evidence cite `active/issues/uv_pin_fleet_drift...`
   dangling (file archived) + missing /plans/ prefix. LOCKED — annotate only.
8. **G** `pm_scripts_typecheck_debt_2026_06_11.md:121` — P3: bare `orchestrator_self_healing_hardening_2026_06_21.md`
   ref (resolves only at plans/archive/2026_06/). LOCKED — annotate only.
9. **W** `prod_terraform_drift_backlog_reconcile_2026_07_24.md:193-195` vs `:202-204` — P2: [x] P2 ignore_changes todo's
   done-when ("fresh tofu plan shows 0 changes") explicitly NOT verified at flip ("no `tofu apply` run" — code-only
   deployment-service@f57c96e). → fix: DEFERRED/partial annotation on the [x] line (do NOT unflip — code did ship).
10. **W** `prod_terraform_drift_backlog_reconcile_2026_07_24.md:37` — P2: frontmatter `source` cites
    `plans/active/issues/plan_line_cap_remediation_2026_07_23.md` (archived). → fix: repoint to /plans/archive path.
11. **W** `prod_terraform_drift_backlog_reconcile_2026_07_24.md:197-205` — P3 structural: lines 198-205 carry 390
    leading spaces each (runaway whitespace, same class doc-1 fixed 2026-08-06) — breaks markdown rendering of the DONE
    block. → fix: de-indent.
12. **W** `reference_path_convention_2026_07_23.md:133-135` — P2: open todo targets
    `plans/active/sports_satellite_ao_dispatch_batch2_2026_07_24.md` (premise: 1000L at cap); file is ARCHIVED (999L,
    bare `issues/fss_bookmaker...` ref still at its :399); 08-03 na-elig marker (:209) also treats it as active. → fix:
    stale-premise annotation on the todo + marker.
13. **W** `reference_path_convention_2026_07_23.md:67,69,117,158` — P2: 4 [x] DONE todos carry `pm@<commit-pending>`
    placeholder evidence — flips without real shas. → fix: verify each against git log; replace with real shas or
    annotate.
14. **W** `reference_path_convention_2026_07_23.md:207-208` vs `:195-196` — P3: 08-03 marker calls backlogs "large" (109
    format / 1,286 existence) while same-day entry records live counts 88 vs baseline 87; magnitude jump 901→87
    incoherently narrated. → fix: correct the marker counts.
15. **W** `shared_host_home_filesystem_full_2026_07_26.md:90` vs `:148,340` — P2: [x] MOOT todo's "145G total" matches
    no other measurement (290G→484G→678G) and its own slot-9 entry (:148) declares the MOOT resolution STALE
    (RECURRENCE). → fix: STALE-annotate the [x] MOOT line (claim false-as-written).
16. **W** `shared_host_home_filesystem_full_2026_07_26.md:242` — P3: relative markdown link
    `sit_validated_tree_treadmill_blocks_breaking_promotes_2026_07_20.md` resolves nowhere (target archived). → fix:
    repoint to /plans/archive/issues/ path.
17. **G** `vm_launcher_setup_script_freshness_gap_2026_07_31.md:141-142` vs `:149-150` — P2: open todo records
    "DEFAULT-RULED 2026-08-06, option (a)" on a decision the same todo calls "not a worker-determinable fact"; 08-04
    Progress Log (:201,206) still calls it `[OPERATOR]`. GRACE — report only (retag happened TODAY; may be another
    slot's in-flight work — do NOT touch).
18. **G** `vm_launcher_setup_script_freshness_gap_2026_07_31.md:120-121` vs
    `session_bound_vm_monitoring_reliability_gap_2026_07_26.md:117-119` — P2 cross-doc: doc 13 declares af-backfill
    PREEMPTED-marker gap RESOLVED (self-contained baked-in); doc 7 records 2 fresh af-backfill preemptions (08-03/04)
    with marker STILL absent after the hardened helper. Doc 13 GRACE — report only. Doc 11's [x] todo
    (vm_billing_waste:350-355, deployment-service@b4503ef) is the same claim doc 7 refutes → STEP-4 decide
    stale-annotation on that [x] line.
19. **W** `stale_agentwork_scratch_clone_not_deletable_unpushed_stashes_2026_07_30.md:147` — P3: bare
    `issues/ag_closeout_audit...` ref (format violation). → fix: prefix /plans/.
20. **W** `vm_billing_waste_first_audit_and_preflight_gate_design_2026_07_24.md:12,141,264,408` — P3: 4 bare references
    (no leading slash; all resolve when slash-prefixed; format-only). → fix: prefix /plans/ (ratchet-relevant).
21. **G** `vm_launcher_class_b_no_stall_kill_gap_2026_07_27.md:154` — P3: bare
    `bucket_iam_write_protection_per_tier_2026_06_09.md` ref. GRACE — report only.
22. **W** `prod_terraform_drift_backlog_reconcile_2026_07_24.md:107,112` — P3: bare refs (2 archived, 1 active —
    format-only). → fix: prefix /plans/.
23. **G** `vm_launcher_setup_script_freshness_gap_2026_07_31.md` — P3: `assigned_vm: planning` with no na-eligibility
    verdict recorded. GRACE — report only.

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
