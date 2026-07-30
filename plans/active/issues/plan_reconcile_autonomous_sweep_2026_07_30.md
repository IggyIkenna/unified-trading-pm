---
doc_type: issue
title:
  "/plan-reconcile autonomous whole-corpus sweep 2026-07-30 — parked operator decisions, one migrated prose deferral,
  and a codex-side dangling reference this run was not authorized to fix"
summary: >-
  Parking + findings doc for the 2026-07-30 `/plan-reconcile` run (whole-corpus `all` scope, autonomous mode, standing
  in for the `plan-reconciler.timer` worker). The run cleared all 4 hygiene hard-gate failures it found at entry
  (reference-path ratchet, AG-closeout linkage, terminal-status-archived, archive-candidates ratchet) and flipped one
  done-but-unchecked todo with verified cross-repo evidence. What it could NOT resolve autonomously is recorded here:
  one codex/** dangling reference (SSOT edits require an explicit operator ruling and this run was explicitly barred
  from touching codex/**), one fully-done-but-`locked_by:` plan that cannot be archived without `[unlock-plan]`, and the
  standing near-complete-plan consolidation question (where a remnant folds is a planning decision, never an autonomous
  fold). Also carries one real prose deferral migrated out of a doc that was archived mid-run by a concurrent peer
  agent, so the deferral did not evaporate with the archive.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan-hygiene, plan-reconcile, archival, reference-paths, operator-decision, codex-drift]
related:
  [
    /plans/active/issues/reference_path_convention_2026_07_23.md,
    /plans/archive/issues/qg_hardcoded_tmp_paths_false_failures_on_full_tmpfs_2026_07_26.md,
    /plans/active/cicd_mvp_ldr_to_main_pipeline_2026_06_30.md,
  ]
created: 2026-07-30
parent_epic: plan_hygiene_master
priority: P2
assigned_vm: NA
execution_scope: local-only
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.12
assigned_role: NA
drift_direction: none
source:
  "/plan-reconcile autonomous whole-corpus run, 2026-07-30, slot-3 — Phase 4 routing produced 4 live operator-gated
  items (a 5th self-resolved mid-run) and Phase 5 required one deferral migration"
depends_on: []
resolved_by:
locked_by:
supersedes:
superseded_by:
---

# /plan-reconcile autonomous sweep — 2026-07-30 parked decisions + findings

## Run context (read this before acting on anything below)

- **Scope**: whole corpus (`all`), autonomous mode, no operator reachable. Per the skill's ASK > PARK rule, everything
  below would have been a batched interactive question if anyone had been in the session — parking is the fallback, not
  the preference. **Answer these in a normal interactive session and the next run applies them.**
- **Concurrency caveat**: the corpus was being actively rewritten by at least one peer agent throughout the run (5
  upstream commits landed mid-sweep, including a peer archiving 4 of the same issue docs this run archived, which
  produced a real `AUTOSTASH_POP_CONFLICT`). Conflicts were resolved to the merged-best combination, never a blind
  take-mine/take-theirs. Any count in this doc is a measurement at the moment it was taken, not a durable number.

## Parked — operator ruling required

### P1-A. A codex SSOT carries a dangling reference introduced 2026-07-30; this run could not fix it

`/codex/02-data/is-test-run-audit-2026-04-20.md:48` links to the ARCHIVE path of
`features_calendar_is_test_run_ignored_writes_prod_2026_07_27.md` (written out in full there; deliberately NOT
reproduced verbatim here, because a broken path quoted in prose is itself counted by `check_reference_paths.py` and
would make this doc a source of the very violation it reports). **That archive path does not exist.** The calendar doc
is still live at `/plans/active/issues/features_calendar_is_test_run_ignored_writes_prod_2026_07_27.md` with 1 open
todo; the doc that actually got archived that day is its SIBLING,
`/plans/archive/issues/features_sports_is_test_run_ignored_writes_real_data_to_prod_2026_07_27.md`. The bad link landed
in `unified-trading-pm@40edd70b4` ("archive fully-resolved features_sports_is_test_run issue + correct stale codex doc")
— i.e. the archival ritual's step-5 referrer fix was applied to the wrong sibling's path. It is 1 of the 908 dangling
refs the reference-path existence ratchet counts.

Why it is parked and not fixed: any edit under `codex/**` is authority-gated (skill § "STILL ASK / PARK — blast
radius"), and this run was explicitly barred from codex edits. Strong evidence does not buy the authority.

- **A: repoint the codex line to `/plans/active/issues/features_calendar_is_test_run_ignored_writes_prod_2026_07_27.md`
  [WORKER REC]** — one-line, matches observable reality (the file is there, `os.path.exists` says so), and preserves the
  codex doc's intent of pointing at the calendar finding.
- **B: leave the codex line alone and instead archive the calendar doc**, making the existing link correct. Requires
  closing that doc's 1 open todo first, so it is strictly more work and cannot be done today.
- **C: drop the link from the codex doc entirely** if the calendar finding is no longer something the audit doc needs to
  cite.
- Other: operator can specify different wording.

### P2-B. `cicd_mvp_ldr_to_main_pipeline_2026_06_30.md` is fully done but `locked_by: live-defi-rollout`

29/29 todos `[x]`, `status: active`, no open work, no finalize-gate companion. It is excluded from
`check_archive_candidates.sh` precisely because `locked_by:` docs are unactionable for an agent. Agents MUST NEVER
unlock autonomously (`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` § 1).

- **A: `[unlock-plan]` + archive it now [WORKER REC]** — nothing in it is open; leaving it `active` pollutes the corpus
  and is exactly the "caught later, not at completion time" pattern the archival codex exists to stop.
- **B: keep it locked** because the LDR→main pipeline refactor is still considered in flight and CLAUDE.md's
  git-discipline section still cites it as the in-flight plan-of-record. If so, the lock is doing real work and the
  right follow-up is a note in the doc saying why a 0-open-todo plan is deliberately held open.
- Other.

### P2-C. Standing class question: near-complete plans (~36 docs at ≤1 open todo)

Phase-0 inventory counted 36 active plan/issue docs with exactly one open todo. Per the skill these should have the
remnant folded into a sibling under the same `parent_epic` (or the epic hub) and the shell archived — but **where live
work lives is a planning decision, so an autonomous run must never fold.** This is deliberately raised once as a class
question rather than 36 times.

- **A: authorize fold-by-default for the specific sub-case "remnant is a `[REVIEW]`/`[DOC]` item whose parent_epic has
  an obvious active sibling", listing the target per doc for confirmation [WORKER REC]** — keeps the operator in the
  loop on destination while removing 36 round-trips.
- **B: keep every fold operator-gated** (status quo) and accept that the near-complete population stays flat.
- **C: route the whole population to `/na-eligibility-audit` / `/ag-closeout-audit` instead**, since both already walk
  the same docs with a per-doc read.
- Other.

## Migrated deferral (this is real tracked work, not a decision)

- [ ] [OPS] P3. **Audit every other fleet host for the two stale-tmp cleanup crons and register them where missing.**
      Provenance: `/plans/archive/issues/qg_hardcoded_tmp_paths_false_failures_on_full_tmpfs_2026_07_26.md`'s `[OPS] P2`
      todo closed with the prose sentence "Auditing/remediating other fleet hosts the same way … is tracked separately"
      — a corpus grep this run found **no other doc tracking it**, so the claim was false and the deferral was about to
      evaporate with that doc's archival (a peer archived it mid-run). Filed here per the todos-not-prose HARD RULE
      (`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` § 2). For each fleet host (the AO
      orchestrator VM, the human-planning VM, and any laptop/slot host that runs `quality-gates.sh`), check
      `crontab -l | grep cleanup-stale`; where missing, run
      `bash unified-trading-pm/scripts/dev/install-cleanup-stale-qg-tmp-cron.sh` and
      `bash unified-trading-pm/scripts/dev/install-cleanup-stale-claude-session-tmp-cron.sh`. Note the operator had to
      run these personally on `ip-172-31-5-118` (no crontab-write permission for this account, an OS-level permission no
      cloud identity can self-serve), so any host with that same limitation is an `[OPERATOR]` ask, not a self-service
      fix. **Done-when**: a per-host table in this doc naming each fleet host and whether both crons are present, with
      no host left "unknown".

## Reported, not parked — coverage gaps this run is honest about

1. **Phase 1's multi-agent fan-out did not run as designed.** The skill specifies up to 10 parallel read-only hunter
   sub-agents (epic-cluster / topic / mechanical-adjudicator / codex-alignment / AO-dispatch-readiness /
   milestones-drift / prose-integrity). **No `Task`/`Agent` spawn tool was available in this run's harness**, so the
   contradiction sweep ran in-process and grep-driven, at materially lower breadth than a fan-out run. Cross-tranche
   contradiction coverage for this run should be treated as PARTIAL. The next run with a spawn-capable harness should
   not assume this corpus was swept at full Phase-1 depth on 2026-07-30.
2. **4 archive candidates remain** (within the ratchet baseline of 7, so not gate-blocking):
   `mtds_backfill_vm_startup_oom_rc137_2026_07_14`, `sports_batch_odds_api_capture_outage_recurrence_check_2026_07_26`,
   `tradfi_mdps_build_continuous_mismatches_2_and_4_still_open_2026_07_26`, `wsfeedconnector_phase35_gap_2026_07_06`.
   All four are large (400–1500 lines) and were not verified to the Phase-2 HARD-evidence bar this run. They are the
   obvious next-pass target — verify each todo, then archive and lower the baseline.
3. **`daily_trading_analyst_llm_job_design_2026_07_29.md` has zero checkboxes.** A design plan whose work exists only as
   prose is the exact "prose-only trap" the todos-not-prose rule names, and it is invisible to every backlog and orphan
   check. Not auto-fixed: converting a design brief into todos is authoring, not reconciliation.
4. **The 3 satellite batch plans with 0 open todos** (`prediction_satellite_ao_dispatch_batch1/batch2_2026_07_25`,
   `tradfi_satellite_ao_dispatch_batch4_2026_07_26`) are correctly NOT archive candidates — each is gated by a
   `depends_on` + `gate_on_depends: true` finalize companion, i.e. mid-chain rather than forgotten. Recorded so a future
   run does not re-investigate them.

### P2-D. A stale local agentwork clone fails the shared `repo-docs-ssot` gate and blocked this run's quickmerge

`quickmerge.sh`'s post-gate `check_repo_docs_ssot.py` reported **6 NEW violations**, all inside
`unified-trading-system-repos/.tabs/3/instruments-service-agentwork-sports-2026-07-13/` (`README.md` mirror-ref plus 5
`docs/*.md` hardcoded `central-element-323112` literals). That directory is a **stale scratch clone** — created
2026-07-13, still checked out on `agentwork/sports_residual_fix_2026_07_13`, and listed in **none** of the 9
`cursor-configs/*.code-workspace` folder sets (the `.code-workspace` repo-list drift guard passes at 25 repos without
it). It is not a repo this run owns and not one anybody registered.

The gate's own remedy line offers `--update-baseline` for pre-existing debt, and this debt IS pre-existing — but
baselining it would permanently encode a **local-only scratch directory** into a shared, fleet-enforced ratchet, which
is worse than the failure. The run therefore did NOT baseline it, and shipped its pure-`docs(plans):` change through the
documented closed carve-out for direct LDR pushes instead (`/codex/08-workflows/ci-cd-flow.md` § "Never push CODE
directly", first listed carve-out), stamping the `Quickmerge: direct-carveout-dirty-deps` trailer per the recipe ruled
2026-07-29. No code files were touched.

- **A: delete the stale `instruments-service-agentwork-sports-2026-07-13/` clone from this host [WORKER REC]** — it is
  17 days old, unregistered, and its only current effect is failing a shared gate for every agent on this host. Deleting
  another agent's leftover working tree is a destructive local op an autonomous run must not do unasked, hence the park.
  Confirm the branch has nothing unpushed first (`git -C … status --porcelain` + `git log @{u}..`).
- **B: move it out of the workspace root** (e.g. under a `_scratch/` sibling the gate does not walk) if the branch still
  holds wanted work.
- **C: fix the 6 docs in place** (repoint the mirror-ref at `unified-trading-pm/codex/…`, swap the literal for the
  `{project_id}` placeholder) — correct but pointless effort on a throwaway clone.
- Other.

### ~~P2-E~~ — SELF-RESOLVED before this run ended, kept as a record only (NOT an operator ask)

**Resolved 2026-07-30, same run.** The first exit-gate regen reported `253 plans, 5 orphans`; the confirming re-run
minutes later reported `253 plans, 0 orphans`. The 5 were all peer docs created during this run whose authors added
their epic linkage while the sweep was in flight — exactly outcome **A** below, reached without anyone being asked.
Recorded because it is a real, reproducible property of running this skill against a live corpus: **a Phase-0/exit-gate
snapshot of freshly-created peer docs will show transient orphans that are not defects**, and a future run should
re-measure before escalating rather than trusting the first reading. Nothing here needs an answer.

Original finding (5 epic-orphan plans, all created by peers within the last hour):

`regenerate_active_plan_inventory.py` (Phase-5 exit gate) reported `253 plans, 5 orphans`. CLAUDE.md calls an orphan
count >0 review-blocking. All 5 are docs a concurrent peer created during this very run, none referenced by
`master_to_live_defi` or any epic yet:

| orphan plan                                                                          | note                                  |
| ------------------------------------------------------------------------------------ | ------------------------------------- |
| `ao_consolidated_closeout_2026_07_25_finalize_2026_07_30`                            | finalize plan, 0/1, created this hour |
| `deployment_registry_firestore_migration_2026_07_14_finalize_2026_07_30`             | finalize plan, 0/1, created this hour |
| `e2e_coverage_gaps_alerting_deployment_trading_agent_2026_07_27_finalize_2026_07_30` | finalize plan, 0/1, created this hour |
| `ao_slot_capacity_policy_ci_scheduled_split_2026_07_29`                              | 7/8 done                              |
| `daily_trading_analyst_llm_job_design_2026_07_29`                                    | 0 checkboxes (see gap 3 below)        |

Not auto-fixed. The mechanical remedy is "add an epic reference", but every one of these files was written and pushed
minutes before this gate ran, and the multi-agent safety rule is explicit about not editing recently-pushed files you do
not own — an epic assignment landing on top of an in-flight author is exactly the collision that rule prevents. Three
are `*_finalize_*` companions whose authoring peer plausibly still has the epic link queued.

- **A: leave them for the authoring peer / the next reconcile pass [WORKER REC]** — the 3 finalize plans are minutes
  old; if they are still orphaned at the next run, fix them then. **This is what happened: the peers linked them
  themselves within minutes and the count went to 0.**
- **B: assign each an epic now** from its obvious parent, accepting the write collision risk — not taken, and it turned
  out to be unnecessary.

## Progress Log

- 2026-07-30 (slot-3, `/plan-reconcile` autonomous whole-corpus run): filed. Entry sweep found 4 hard failures; all 4
  were green at exit. Applied fixes: archived 5 resolved issue docs (4 of them concurrently archived by a peer — merged,
  not duplicated), repointed 21 corpus references, added one AG-closeout linkage edge, realigned one frontmatter-vs-body
  status contradiction, fixed 5 bare-`codex/` reference-format violations, and flipped one done-but-unchecked todo
  against a cross-repo sha verified reachable this run.
- **na-eligibility-audit 2026-07-30** (infra tranche, incremental run): **KEEP-NA, valid — borderline, see below.** In
  scope because the doc was created hours earlier the same day with no verdict marker. Read end-to-end;
  `grep -cE '^- \[ \]'` = **1**, matching this verdict's item count. Doc-level NA is unambiguous: P1-A, P2-B, P2-C and
  P2-D are all authority calls (a `codex/**` edit, an `[unlock-plan]`, a fold-policy ruling, deleting another agent's
  working tree) — none autonomously resolvable, and P2-E is already self-resolved and recorded as history.
- **na-eligibility-audit 2026-07-30 — RECLASSIFY candidate assessed and HELD (the one genuine judgment call this
  tranche's incremental run produced).** The sole open todo — `[OPS] P3` fleet-host stale-tmp cron audit — was taken
  through the full Phase-2 conflict-check (`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md`
  § 3) and came back **CLEAR**: no active `assigned_vm: planning` doc claims it, the only other corpus mentions are the
  archived source `qg_hardcoded_tmp_paths_false_failures_on_full_tmpfs_2026_07_26.md` (whose false "tracked separately"
  prose is exactly why the deferral was migrated here) and unrelated tmpfs incident docs; the 4 active planning plans
  under `parent_epic: plan_hygiene_master` are e2e-coverage and codex-vs-repo-docs work with zero overlap. It is also
  genuinely bounded and carries a stated done-when, which normally satisfies the dispatch-scope bar. **Held NA anyway**,
  on the doc's own recorded evidence: the remediation half needs host-level `crontab` write access, and this doc already
  records the operator having to run both installers personally on `ip-172-31-5-118` because the account lacks it — an
  OS-level permission the cloud-identity self-service rule
  (`/codex/05-infrastructure/orchestrator-cloud-identity-self-service.md`) explicitly does not cover, so a worker cannot
  reach "no host left unknown" unaided on at least one known host. Flipping the doc would also relabel an
  operator-decision parking register as an AO-dispatched plan. **Recorded here rather than silently buried so the
  operator can cheaply overrule**: if the audit half alone (report present/missing per host, flag the rest `[OPERATOR]`)
  is considered a sufficient done-when, this todo is dispatch-ready today and the flip is a one-line frontmatter change.
