---
doc_type: issue
title: >-
  Prediction tranche closeout-audit findings (2026-07-31) — two fresh dead-code findings are correctly operator-gated
  (not batchable), and the candidate-generation script's depends_on-resolution gap recurs for prediction's own Phase A-E
  children
summary: >-
  Filed by the scheduled `/ag-closeout-audit prediction` run 2026-07-31 (Phases 0-2, mostly read-only; 2 mechanical
  fixes from yesterday's parked findings were applied directly, see
  `issues/prediction_closeout_tag_and_batch_claim_findings_2026_07_30.md`'s Todos/Progress-Log for those). This run's
  own fresh ground: (1) two adapter dead-code findings filed the SAME DAY by
  `prediction_consolidated_native_ao_extract_2026_07_25.md` todo 1 are genuinely orphaned (no active plan claims their
  fix) but correctly non-batchable — each is an explicit, self-declared (A) delete vs (B) keep-and-document judgment
  call, independently confirmed by a fresh Phase-1 Workflow classification. (2) A confirmed NEW instance of the
  candidate-generation script's known `depends_on`-resolution gap (previously tracked only for `native_ao_extract`
  -shaped forks): prediction's 4 Phase A-E children have no `_finalize` sibling of their own, so `_covering_paths()`'s
  finalize→depends_on resolution never reaches them — they are currently only caught as "covered" by incidental
  prose-text citation matching, not structurally. This did not corrupt today's count (the prose citations happen to
  hold), but it is fragile and cross-tranche (the script is `ao`/tooling-owned).
status: open
nature: issue
asset_group: [prediction]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [prediction, ag-closeout-audit, dead-code, adapter-dead-code-and-fallback-ban, script-bug, plan-hygiene]
related:
  [
    /plans/active/prediction_consolidated_closeout_2026_07_18.md,
    /plans/archive/issues/prediction_closeout_tag_and_batch_claim_findings_2026_07_30.md,
    /plans/archive/2026_08/issues/is_polymarket_dead_fixture_cross_reference_2026_07_31.md,
    /plans/active/issues/mtds_prediction_adapters_dead_rest_polling_interface_2026_07_31.md,
    /plans/active/prediction_phase_ab_residuals_2026_07_24.md,
    /plans/archive/issues/ag_closeout_audit_orphan_definition_and_digest_citation_defects_2026_07_30.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: 2026-07-31
author: unknown
parent_epic: predictions_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: refactor
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.08
assigned_role: data_engineering
drift_direction: none
depends_on: []
source:
  [
    "Scheduled /ag-closeout-audit prediction run 2026-07-31 (ag_closeout_auditor, slot 4, dispatch agt-592e74), Phases
    0-2 (+ a Phase-1 Workflow over the 2 genuinely-fresh candidates). Operator was not interactively present during the
    run, so both judgment-relevant items below are parked rather than guessed.",
  ]
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
context_scope:
  [
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /scripts/plan-hygiene/generate_ag_closeout_audit_candidates.py,
  ]
---

# Prediction closeout-audit findings, 2026-07-31

> **Context.** Side-findings of today's `/ag-closeout-audit prediction` pass, beyond what this run already fixed
> directly (see `issues/prediction_closeout_tag_and_batch_claim_findings_2026_07_30.md` for Findings 2/3's resolution).
> Headline result: of 52 raw `asset_group:[prediction]` candidates, 0 genuinely-never-triaged prediction-primary orphans
> remain after correcting one citation false-positive and excluding 11 genuinely cross-cutting multi-AG docs — the
> corpus is well-drained after 6 prior batch rounds. The 2 items below are this run's only real new ground.

## Finding 1 — 2 fresh adapter dead-code findings are orphaned but correctly non-batchable (operator-gated)

`prediction_consolidated_native_ao_extract_2026_07_25.md` todo 1 (adapter dead-code/fallback audit, done 2026-07-31)
filed two new issue docs:

- [`issues/is_polymarket_dead_fixture_cross_reference_2026_07_31.md`](/plans/archive/2026_08/issues/is_polymarket_dead_fixture_cross_reference_2026_07_31.md)
  — instruments-service's Polymarket adapter threads a real `api_football` secret into a `_cross_reference_fixture()`
  capability with zero non-test call sites.
- [`issues/mtds_prediction_adapters_dead_rest_polling_interface_2026_07_31.md`](/plans/active/issues/mtds_prediction_adapters_dead_rest_polling_interface_2026_07_31.md)
  — market-tick-data-service's Kalshi/Polymarket adapters carry a whole dead live-REST-polling method family
  (`get_markets`/`get_prices`/`parse_market`/etc.), exercised only by dedicated tests.

Both are `assigned_vm: NA`, `status: open`, cited nowhere in any active batch (confirmed via corpus-wide grep — no
batch4/batch6/finalize doc mentions either basename; both postdate batch6's 2026-07-29 drafting). A fresh Phase-1
Workflow classification (2 independent agents, one per doc) confirmed both `orphaned_never_touched` — but NOT
AO-dispatch-eligible as written: each doc's own "Recommended decision" section explicitly frames its single todo as an
unresolved (A) delete vs (B) keep-and-document-a-real-activation-path choice, self-labeled "genuine judgment call on
scope, not auto-resolved." `prediction_phase_ab_residuals_2026_07_24.md`'s A5 subsection (the audit's own reconciliation
point) already acknowledges both without fixing them inline, for the identical reason.

**Why not drafted into a batch.** This matches the skill's own "operator-gated" non-batchable taxonomy exactly — no
amount of re-triage resolves whether there's a genuine future activation path for either capability; that is a
product/architecture call, not a fact a worker can determine by reading code. Per CLAUDE.md's "Delete deprecated code
(no shims)" governance rule, option (A) is the workspace's default lean absent a concrete revival plan — and this run
found no such plan anywhere in prediction's active corpus for either capability — but a lean is not a ruling, and
drafting a same-day "just delete it" batch todo on a finding filed hours earlier, overriding its own author's explicit
"not adjudicated here," would be second-guessing a judgment call outside this skill's mandate (Phase 3 drafts
conflict-CLEARED bounded work; it does not itself rule on open design questions).

**Recommendation:** no batch action needed. Whoever next touches either adapter file (or the operator,
opportunistically) picks (A) or (B) directly on the issue doc; either branch is then a clean, bounded, single-session
fix.

## Finding 2 — candidate-script `depends_on`-resolution gap recurs for prediction's Phase A-E children (cross-tranche)

`scripts/plan-hygiene/generate_ag_closeout_audit_candidates.py::_covering_paths()` resolves a discovered `_finalize`
doc's `depends_on:` to its paired main plan (fixed 2026-07-30 per
`issues/ag_closeout_audit_orphan_definition_and_digest_citation_defects_2026_07_30.md` todo 2 — verified still present
and working in this run: `--tranche prediction --json` correctly includes
`prediction_consolidated_native_ao_extract_2026_07_25.md`/`_finalize`,
`prediction_satellite_ao_dispatch_batch4_2026_07_26.md` /`_finalize`,
`prediction_satellite_ao_dispatch_batch6_2026_07_29.md`/`_finalize` in `covering_paths` — 7 total).

**What it does NOT resolve**: the CLOSEOUT HUB doc's own `depends_on:` — only a `_finalize` doc's. Applied to
prediction: `prediction_consolidated_closeout_2026_07_18.md`'s frontmatter lists
`depends_on: [prediction_phase_ab_residuals_2026_07_24, prediction_phase_c_data_status_ui_2026_07_24, prediction_phase_d_formal_smoke_and_backfill_2026_07_24, prediction_phase_e_football_arb_live_2026_07_24]`
— but NONE of those 4 phase children have their own `_finalize` sibling doc (unlike `native_ao_extract`/batch4/batch6,
each of which does), so the only mechanism that resolves a hub's `depends_on:` (finalize→main) never fires for them.
Verified live: `--tranche prediction --json`'s `covering_paths` (7 entries) does not include any of the 4 phase
children.

**Why this didn't corrupt today's orphan count.** The script's SEPARATE citation-matching path (`_cited_basenames()`, a
basename regex over every covering doc's raw text) accidentally catches all 4 — their filenames appear verbatim in the
closeout hub's own "Split notice" table and "Per-child open-todo snapshot" prose. So they read `cited_somewhere`, not
`never_cited`, and the practical count was correct today. But this is incidental (prose-text matching, not structural
graph resolution) and carries the exact fragility already demonstrated live in this same run: the
`mtds_prediction_adapters_dead_rest_polling_interface_2026_07_31.md` citation in
`prediction_consolidated_native_ao_extract_2026_07_25.md`'s Progress Log was ALSO present in raw text, yet the regex
still missed it — a prettier line-wrap had inserted a stray space mid-filename (fixed this run, same commit as the rest
of today's mechanical fixes). A closeout hub's own `depends_on:` failing to structurally resolve is one
missing-citation-away from silently mis-reporting a genuinely-active Phase child as orphaned.

**Why not fixed here.** `generate_ag_closeout_audit_candidates.py` is `ao`/tooling-owned
(`parent_epic: agent_operating_framework_master` on its tracking issue,
`ag_closeout_audit_orphan_definition_and_digest_citation_defects_2026_07_30.md`, `asset_group: [cefi]`) — editing it is
outside the prediction tranche's file ownership for today's concurrent-sharded-worker run (per the skill's own
"primary-owner rule for multi-tranche docs" safety rule — a shared/cross-tranche artifact's WRITE belongs to its owning
tranche, to avoid N workers racing the same file). Flagging here for that tranche/the operator to fold in.

**Recommendation (mechanical, no judgment):** extend `_covering_paths()` to also resolve the closeout hub doc's OWN
`depends_on:` (not just each discovered `_finalize` doc's) to real `plans/active/` files, unioning them into the
covering set — mirrors the fix already applied for the finalize→main direction. A minimal repro: any AG whose
line-cap-split children were forked directly off the closeout hub (via `depends_on:`) rather than getting their own
paired `_finalize` sibling will show the same gap; prediction is a confirmed live instance.

## Todos

- [ ] [DOC] P3. No action needed on Finding 1 unless/until an operator or the next worker touching either adapter file
      picks (A) or (B) on the two named issue docs directly — this finding is informational (explains why neither was
      batched), not itself an actionable task. (repo: unified-trading-pm)
- [x] ✅ [SCRIPT] P2. Extend `generate_ag_closeout_audit_candidates.py::_covering_paths()` to resolve the closeout hub
      doc's own frontmatter `depends_on:` (not just each discovered `_finalize` doc's) to real files, unioning them into
      the covering set — same pattern as the existing finalize→main resolution. **Done when**:
      `--tranche prediction --json`'s `covering_paths` includes all 4 Phase A-E children structurally (not just via
      incidental text citation), a regression test asserts this for a hub-depends_on-only fork (no paired finalize), and
      the existing `test_finalize_doc_depends_on_pulls_in_its_line_cap_fork_as_covering` test (or a sibling) still
      passes. Cross-reference `issues/ag_closeout_audit_orphan_definition_and_digest_citation_defects_2026_07_30.md`
      before starting (same function, avoid duplicate/conflicting edits) — this is a distinct, additive extension of
      that doc's already-shipped todo 2, not a re-open of it. (repo: unified-trading-pm) **DONE 2026-08-01 —
      `unified-trading-pm@be7269449` ("fix(plan-hygiene): resolve closeout doc's own depends_on for finalize-less
      forks"), shipped by the `ag-closeout-audit` tradfi-tranche run (not prediction's), same shared cross-tranche
      script per the primary-owner rule — found and verified stale-unchecked here by the 2026-08-04
      `/ag-closeout-audit     prediction` run. Verified live 2026-08-04**: `--tranche prediction --json`'s
      `covering_paths` now returns 11 entries INCLUDING all 4 Phase A-E children
      (`prediction_phase_ab_residuals_2026_07_24.md`/`_c_data_status_ui_`/`_d_formal_smoke_and_backfill_`/`_e_football_arb_live_`,
      all 2026-07-24) structurally, not via incidental text citation (was 7 entries on 2026-07-31, pre-fix). The named
      regression test `test_closeout_doc_depends_on_pulls_in_a_fork_with_no_finalize_pair` exists in
      `tests/unit/test_generate_ag_closeout_audit_candidates.py`, and the pre-existing
      `test_finalize_doc_depends_on_pulls_in_its_line_cap_fork_as_covering` is still present alongside it (both, not a
      replacement). `be7269449` confirmed an ancestor of `origin/live-defi-rollout`.

## Codex SSOTs

- `/cursor-configs/skills/ag-closeout-audit/SKILL.md` § Phase 0.2 path (b) — the `depends_on:`/`related:` resolution
  requirement Finding 2 shows is only half-implemented.
- `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "Dispatch-scope eligibility" — why Finding
  1's two items are not yet bounded todos.
- `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` § "Running as one of N concurrent
  sharded tranche workers" — the primary-owner rule behind not editing the (cefi/ao-owned) tracking issue directly.

## Progress Log

- **na-eligibility-audit 2026-08-02 (prediction tranche, autonomous)**: KEEP-NA, valid — 2 open, unchanged from the
  2026-07-31 marker (re-counted live: 2). The only intervening commits to this file (`5f4d33007`, `e89cdd5eb`, both
  2026-07-31) are append-only re-verification records from the same day's 2nd/3rd `/ag-closeout-audit prediction`
  re-dispatches — no todo was added, closed, or re-scoped. Both items re-confirmed on their own standing citations, not
  re-derived: Finding 1's todo is self-declared informational (it exists to explain why the two adapter dead-code docs
  were NOT batched); Finding 2's todo carries an explicit redirect — its own text says the target script
  (`generate_ag_closeout_audit_candidates.py`, `parent_epic: agent_operating_framework_master`) is `ao`/tooling-owned
  and it is "flagging here for that tranche/the operator to fold in". Per this skill's Phase-1 rule (a), a body sentence
  routing the work to a different owner is KEEP-NA on that citation alone even though the todo's own `Done when` reads
  as cleanly bounded — flipping `assigned_vm` here would let backlog-regen dispatch a prediction-scoped worker at an
  `ao`-owned file. Doc stays NA.

- **na-eligibility-audit 2026-07-31 (prediction tranche)**: KEEP-NA, valid — 2 open. Both findings were ASSESSED, not
  defaulted, by the same-day sibling `/ag-closeout-audit prediction` run that filed this doc: Finding 1's todo is
  explicitly informational (no action needed unless an operator/future worker picks A-vs-B on the two linked adapter
  dead-code docs); Finding 2's todo is bounded/mechanical but targets an `ao`/tooling-owned script
  (`generate_ag_closeout_audit_candidates.py`, `parent_epic: agent_operating_framework_master`) outside this doc's own
  `predictions_master` file-ownership — the doc's own text already says it is "flagging here... to fold in," i.e. routed
  to the `ao` tranche/operator, not a defaulted-NA item this run should reclassify. Doc stays NA.

- **2026-07-31 (slot 4, ag_closeout_auditor, dispatch agt-592e74):** Filed by the scheduled
  `/ag-closeout-audit prediction` run. Phase 0-2 read-only for both findings above; Phase 1 ran a real 2-agent Workflow
  (`wf_a447329e-21a`, 0 errors) confirming Finding 1's non-batchable verdict independently. Phase 3 conflict-check
  concluded no new batch warranted (both Finding-1 items non-batchable; Finding 2 is a tooling gap, not prediction
  content work). Mechanical Findings 2/3 from yesterday's sibling doc
  (`issues/prediction_closeout_tag_and_batch_claim_findings_2026_07_30.md`) were fixed directly in this same run — see
  that doc's own Todos/Progress-Log, not repeated here. parked_findings ledger: 2 findings this doc (Finding 1,
  Finding 2) == 2 entries written to this doc. Balanced.

- **2026-07-31T20:45Z (slot 3, ag_closeout_auditor, dispatch agt-7ae586):** Re-dispatched
  `/ag-closeout-audit prediction` ~14.5h after the same-day agt-592e74 run above (cause of the re-fire not diagnosed —
  the AO scheduling/dispatch mechanism is `ao`-tranche/orchestrator-owned, out of this run's file-ownership scope per
  the skill's primary-owner rule; flagging the observation in this run's `/done` evidence for the operator/main agent,
  not investigating agent-orchestrator internals here). Per the skill's iterative-drain step 1, verified the prior run's
  state before considering any fresh Phase-1 triage: live re-run of
  `generate_ag_closeout_audit_candidates.py --tranche prediction --json` returned an IDENTICAL corpus fingerprint to the
  morning run — `total_members=52`, `never_cited_count=11` (spot-checked 3 of the 11 basenames: all still carry 4-5
  `asset_group` tags each, confirmed genuinely cross-cutting, not a fresh mistag), `covering_paths=7` unchanged.
  `git log --since="2026-07-31 06:08:26" --diff-filter=A` across `plans/active/*.md` + `plans/active/issues/*.md` found
  ~30 new docs created workspace-wide since the morning run; none carry `asset_group: [..., prediction, ...]` (checked
  every one). The two Finding-1 issue docs are untouched (still `status: open` / `assigned_vm: NA`);
  `prediction_consolidated_closeout_2026_07_18.md`,
  `prediction_consolidated_native_ao_extract_2026_07_25.md`(+finalize), and
  `prediction_satellite_ao_dispatch_batch4_2026_07_26.md`(+finalize) have zero commits since 06:08. The ONLY in-corpus
  activity was normal AO worker churn on `batch6`'s own todos (todo `batch6-008` fixture-pairing closed 18:51Z per main
  ruling `BLK-a1613863`, plus a prettier re-wrap) — expected progress on an already-covering plan, not an
  orphan-relevant change. **Verdict: state is confirmed unchanged from the morning run — 0 new orphans, no new batch
  warranted.** Did NOT re-run a full Phase-1 Workflow fan-out over all 52 candidates given the fingerprint was confirmed
  identical to the morning run; re-litigating an unchanged, hours-old, already-thoroughly-audited corpus would reproduce
  the same result at real token cost for zero new information. parked_findings ledger: 0 new findings this run (this
  entry is a re-verification record, not a new parked finding — nothing else appended).

- **2026-07-31T21:36Z (slot 11, ag_closeout_auditor, dispatch agt-c2a8bd):** THIRD same-day dispatch of
  `/ag-closeout-audit prediction` — only **51 minutes** after the agt-7ae586 re-dispatch above (vs. ~14.5h between the
  first two runs). The re-fire interval shrinking from 14.5h to 0.85h across two consecutive re-dispatches is a stronger
  signal than either run alone that the AO scheduling/dispatch mechanism for this role+tranche may be misconfigured
  (e.g. firing on a tick far more frequent than the intended daily cadence), not independent noise — still not diagnosed
  here (same `ao`-tranche/orchestrator-owned file-ownership boundary as the prior entry; not investigating
  agent-orchestrator internals from a prediction-scoped dispatch). Flagging with the sharper interval data point in this
  run's `/done` evidence for the operator/main agent. Per the skill's iterative-drain step 1, re-verified before
  considering any fresh Phase-1 triage: live re-run of
  `generate_ag_closeout_audit_candidates.py --tranche prediction --json` returned an IDENTICAL corpus fingerprint to
  BOTH prior runs today — `total_members=52`, `never_cited_count=11` (same 11 basenames, byte-identical list),
  `covering_paths=7` (same 7 paths, byte-identical list). `git log --since="2026-07-31 20:45:00"` against all 7 covering
  docs + the 2 Finding-1 issue docs found **zero commits**; both Finding-1 docs remain `status: open`/`assigned_vm: NA`,
  untouched. Corpus-wide, only 3 new docs were created workspace-wide since 20:45Z
  (`ao_satellite_ao_dispatch_batch2_2026_08_01.md`, `manifest_consolidator_inline_unbounded_memory_cli_2026_07_31.md`,
  `unified_trading_sa_live_iam_drift_vs_terraform_2026_07_31.md`) — none carry `prediction` in `asset_group` (consistent
  with `total_members` staying at 52). No `prediction_*batch7*` (or later) exists, committed or not. Independently
  spot-checked 6 of the 11 `never_cited` basenames myself (double the prior run's 3, no overlap avoided —
  `ag_closeout_audit_rollout_2026_07_25.md`, `candle_feature_canonical_path_divergence_2026_07_20.md`,
  `mtds_is_full_adapter_smoketest_findings_2026_07_07.md`, `uac_per_venue_seed_fallback_removal_deferred_2026_07_26.md`,
  `estate_orphan_assessment_2026_07_21.md`, `mdps_features_deadcode_consolidation_2026_07_20.md`): all 6 carry 4-6
  `asset_group` tags spanning multiple/all 5 AGs, confirmed genuinely cross-cutting, not a fresh mistag. **Verdict:
  state confirmed unchanged for the third consecutive dispatch today — 0 new orphans, no new batch warranted.** Did not
  re-run a full Phase-1 Workflow fan-out for the same token-cost-for-zero-new-information reason as the prior entry.
  parked_findings ledger: 0 new findings this run (re-verification record only, nothing else appended).

- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
- **context-scout 2026-08-03**: re-scouted; context_scope unchanged (4 entries), still accurate.

- **2026-08-04 (slot-11, ag_closeout_auditor) — `/ag-closeout-audit prediction` scheduled run.** Per the skill's
  iterative-drain step 1, re-checked this doc's own open items before fresh triage. **Finding 2's todo was stale `[ ]`**
  — live-verified the fix actually shipped 2026-08-01 (`unified-trading-pm@be7269449`, by the tradfi-tranche sibling
  run, same shared script) and is genuinely on `origin/live-defi-rollout`: `--tranche prediction --json` now returns 11
  `covering_paths` (was 7), including all 4 Phase A-E children structurally; the named regression test exists alongside
  the pre-existing one. Flipped `[x]` with full evidence (see Todos). Finding 1 remains correctly open (informational,
  no operator action taken on the two adapter dead-code docs since 2026-07-31). Live re-run of
  `generate_ag_closeout_audit_candidates.py --tranche prediction --json`: `total_members=48` (was 52 — 5 previously
  `cited_somewhere` prediction docs archived/resolved since 07-31, net corpus shrink), `never_cited_count=12` (was 11 —
  the 11 prior `never_cited` basenames are ALL still present unchanged, still genuinely cross-cutting multi-AG-tagged
  per a fresh frontmatter check today; +1 new: `mtds_prediction_backfill_targets_wrong_data_type_scope_2026_08_02.md`,
  single-tagged `[prediction]`, created 2026-08-02, 1 remaining open P3 todo — genuinely orphaned, real Phase-1
  classification + Phase 3 batch-eligibility assessment in progress, full result in this run's own
  `ag_closeout_audit_prediction_parked_2026_08_04.md` / batch7 (if drafted)). Also confirmed
  `prediction_mdps_live_depth_history_not_accumulating_2026_08_04.md` (today's data-correctness FAIL-verdict finding,
  `parent: predictions_master`) is `assigned_vm: planning` + actively worked (3/5 todos closed today by other slots) —
  self-dispatched, not an orphan, no action needed from this audit.

- **na-eligibility-audit 2026-08-04 (prediction tranche)**: KEEP-NA, valid — 1 open (Finding 1's `[DOC] P3`
  informational item; Finding 2 was independently flipped `[x]` DONE earlier today by the sibling
  `/ag-closeout-audit prediction` run, cited above). Finding 1 remains purely explanatory ("No action needed...
  unless/until an operator or the next worker... picks (A) or (B)") — no operator action taken on either linked adapter
  dead-code doc since 2026-07-31, re-confirmed via direct read of both. Not reclassifiable: the doc's own text is the
  citation (redirect + explicit non-actionable framing). Doc stays NA.
- **na-eligibility-audit 2026-08-07 (prediction tranche, autonomous)**: KEEP-NA, valid — re-verified, 1 open, unchanged
  since the 2026-08-04 marker. Finding 1 remains a self-declared judgment call (delete vs keep-and-document on 2 linked
  adapter dead-code docs, both still `assigned_vm: NA` with their own open decision todo, live-confirmed today). Finding
  2 stays `[x]` DONE — independently re-verified live: `be7269449` is confirmed an ancestor of current HEAD via
  `git merge-base --is-ancestor`, and the named regression test
  `test_closeout_doc_depends_on_pulls_in_a_fork_with_no_finalize_pair` is confirmed present in
  `tests/unit/test_generate_ag_closeout_audit_candidates.py`. Doc stays NA.
- **context-scout 2026-08-05**: re-scouted; context_scope unchanged (4 entries), still accurate.
- **context-scout 2026-08-09**: re-scouted; context_scope unchanged (4 entries), still accurate.
- **na-eligibility-audit 2026-08-09 (prediction tranche)**: KEEP-NA, valid — re-verified, 1 open, unchanged since the
  2026-08-07 marker (only intervening commit is today's context-scout refresh, no content change). Finding 1's
  `[DOC] P3` item remains informational-only; today's sibling `/ag-closeout-audit prediction` run's own parked-findings
  doc (`ag_closeout_audit_prediction_parked_2026_08_09.md` Finding 2) independently confirms Finding 1's wait-condition
  on the 2 linked adapter dead-code docs is now satisfied (both operator-ruled DELETE 2026-08-07, extracted to
  `prediction_satellite_ao_dispatch_batch10_2026_08_09.md` todos 3/4) but folds the reconciliation into
  `batch10_finalize` rather than this doc directly. Doc stays NA.
