---
doc_type: issue
title: >-
  Prediction tranche closeout-audit findings (2026-07-30) — two forks carry an inherited `cefi` tag their content does
  not earn, batch4 and batch6 both claim the same cqg re-enumeration item, and 4 prediction-tranche docs are absent from
  the consolidated-closeout aggregated-sources index
summary: >-
  Filed by the scheduled `/ag-closeout-audit prediction` run 2026-07-30 (Phases 0-2, read-only). The run's Orthogonality
  HARD CHECK found ZERO strict `<single-AG> + cross-cutting` violations corpus-wide (nothing to retag), but surfaced
  three adjacent corpus-quality findings the check's own strict class does not cover. (1) OPERATOR-DECISION —
  `prediction_cross_venue_arb_and_coverage_2026_07_24.md` and `prediction_live_clob_depth_capture_2026_07_24.md` are
  both tagged `asset_group: [prediction, cefi]`, inherited verbatim from their archived parent
  `prediction_venue_perps_and_live_clob_depth_2026_06_20.md`, but neither fork carries cefi-scoped WORK — every `cefi`
  mention in either file is an incidental cross-reference or an explicit carve-OUT ("cefi untouched per item 75-cefi
  scope"). The genuinely cefi-touching third fork (`prediction_perps_kalshi_polymarket_parked_2026_07_24.md`, the
  KALSHI-PERP contamination track) is archived. Under the skill's Phase-0.3 peer filter, the `cefi` marker excludes both
  docs from prediction's own audit population, so prediction's covering set is measured against a population that omits
  two of its most active docs. (2) DUPLICATE CLAIM — `prediction_satellite_ao_dispatch_batch4_2026_07_26.md` todo 3 and
  `prediction_satellite_ao_dispatch_batch6_2026_07_29.md` todo 7 extract the SAME "cqg partition-completeness —
  recent-window catalogue re-enumeration" item from the same source doc. (3) INDEX GAP — 4 prediction-tranche docs
  created 2026-07-26..28 are named nowhere in `prediction_consolidated_closeout_2026_07_18.md`'s aggregated-sources
  index.
status: resolved
nature: issue
asset_group: [prediction]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [prediction, ag-closeout-audit, asset-group-tagging, orthogonality, ao-dispatch, duplicate-claim, plan-hygiene]
related:
  [
    /plans/active/prediction_consolidated_closeout_2026_07_18.md,
    /plans/active/prediction_cross_venue_arb_and_coverage_2026_07_24.md,
    /plans/active/prediction_live_clob_depth_capture_2026_07_24.md,
    /plans/active/prediction_satellite_ao_dispatch_batch4_2026_07_26.md,
    /plans/active/prediction_satellite_ao_dispatch_batch6_2026_07_29.md,
    /plans/active/issues/prediction_trades_migration_concurrent_dispatch_2026_07_28.md,
    /plans/active/ag_closeout_audit_rollout_2026_07_25.md,
  ]
created: 2026-07-30
parent_epic: predictions_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.16
assigned_role: data_engineering
drift_direction: none
depends_on: []
source:
  [
    "Scheduled /ag-closeout-audit prediction run 2026-07-30 (ag_closeout_auditor), Phases 0-2 read-only audit +
    Phase-0.3 Orthogonality HARD CHECK. No operator was available during the run, so every judgment call below is PARKED
    with options + a marked recommendation rather than applied.",
  ]
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
context_scope:
  [
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /codex/11-project-management/doc-frontmatter-schema.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    /plans/active/issues/prediction_trades_migration_concurrent_dispatch_2026_07_28.md,
  ]
---

> **🟢 ARCHIVED 2026-08-03** — `status: resolved` with zero open todos; archived per
> [`/codex/11-project-management/issue-doc-lifecycle.md`](/codex/11-project-management/issue-doc-lifecycle.md)'s
> archive-on-resolve rule. All 4 findings resolved. Moved by a `cicd` escalation (agt-5c37f6) triaging the
> `check_archive_candidates` hard gate failure. No content was rewritten.

# Prediction closeout-audit findings, 2026-07-30

> **Context.** These are the side-findings of a read-only `/ag-closeout-audit prediction` pass. The audit's own headline
> result (11 orphaned docs of 18 prediction-primary docs audited) is not repeated here — this doc carries only the
> corpus-quality items that need a decision or a mechanical fix outside the audit's own output.

## Finding 1 — `[prediction, cefi]` inherited-tag class (RULED 2026-07-30 → option A, APPLIED 2026-08-02)

**What was measured.** `plans/archive/2026_07/prediction_venue_perps_and_live_clob_depth_2026_06_20.md` was
line-cap-split 2026-07-24 into three forks. All three inherited the parent's `asset_group: [prediction, cefi]` verbatim:

| Fork                                                                                                                           | cefi-scoped work in its content?                                                                                                                                                                                                        |
| ------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `prediction_perps_kalshi_polymarket_parked_2026_07_24.md` (ARCHIVED)                                                           | **YES** — the KALSHI-PERP / POLYMARKET-PERP track that contaminated the cefi catalogue with 25,473 fake `PERPETUAL` rows.                                                                                                               |
| [`prediction_cross_venue_arb_and_coverage_2026_07_24.md`](/plans/active/prediction_cross_venue_arb_and_coverage_2026_07_24.md) | **NO** — 5 `cefi` tokens total, all incidental: the frontmatter tag itself, an archetype-availability aside, a tradfi/cefi parity comparison, a "cross-AG cefi blast radius" caution, and a launcher-name list. Zero cefi deliverables. |
| [`prediction_live_clob_depth_capture_2026_07_24.md`](/plans/active/prediction_live_clob_depth_capture_2026_07_24.md)           | **NO** — 9 `cefi` tokens, and two of them are explicit carve-OUTs: "cefi untouched per item 75-cefi scope" and "cefi `(cefi, book_snapshot)` entries deliberately preserved pending a separate cefi-handler audit".                     |

**Why it matters.** Under the `/ag-closeout-audit` Phase-0.3 peer filter, a `cefi` marker on a prediction doc makes it a
"deterministic cross-cutting candidate" excluded from **prediction's own** audit. Both docs are among the most active in
the tranche (9 open + 2 in-progress; 2 open + 2 prose items respectively) and are the direct source docs for 5 of
`prediction_satellite_ao_dispatch_batch6_2026_07_29.md`'s 13 todos. Every prediction audit that trusts the deterministic
filter measures prediction's covering set against a population missing them. This is the same mechanism as the skill's
documented "fork inherits its parent's tag" pattern, with `cefi` in place of `cross-cutting`.

**Why it was NOT auto-applied.** The skill's Orthogonality HARD CHECK authorizes an on-sight retag only for the
`<single-AG> + cross-cutting` class (the one that falls through BOTH audits). `[prediction, cefi]` is a different,
less-dangerous class — both docs ARE currently visible to cefi's audit — so dropping `cefi` is a scope judgment, not a
mechanical fix, and it would remove two docs from a sibling tranche's population mid-sweep.

**Options:**

- **A [WORKER REC]** — Drop `cefi` from both forks (`asset_group: [prediction]`), leaving the archived perps fork's
  `[prediction, cefi]` untouched since its cefi scope is real. Rationale: the tag should describe the fork's own
  content, which is what the line-cap split was FOR; both docs' own text explicitly excludes cefi. Pair the retag with a
  re-run of `scripts/plan-hygiene/check_ag_closeout_linkage.py` (currently 0 orphans, baseline 0) to confirm neither doc
  becomes newly orphaned inside prediction.
- **B** — Keep both tags as-is and instead amend the skill's Phase-0.3 filter so a doc whose filename is
  `<ag>_`-prefixed is always treated as `<ag>`-primary regardless of a second peer marker. Broader blast radius (changes
  every tranche's population), but fixes the class rather than two instances.
- **C** — Keep as-is and accept the exclusion; rely on each audit's Phase-1 content re-check to catch it (which is what
  this run did manually — both docs were audited as supplementary targets).
- **Other:** operator may specify a different tag set per doc.

**RULING (operator, 2026-07-30 interactive session): option A.** Drop the inherited `cefi` from both active forks; the
archived perps fork keeps `[prediction, cefi]` (its cefi scope is real). **Applied 2026-08-02** — see the Todos section
below for the verification evidence. Note the third `[prediction, cefi]` doc in the tranche,
`prediction_capture_incident_remediation_2026_07_06.md`, is deliberately OUT of this ruling's scope: it is not one of
the three line-cap-split forks, so its dual tag was never assessed here and stays untouched.

## Finding 2 — batch4 and batch6 both claim the same cqg re-enumeration item

- [`prediction_satellite_ao_dispatch_batch4_2026_07_26.md`](/plans/active/prediction_satellite_ao_dispatch_batch4_2026_07_26.md)
  (`status: active`) todo 3: "**cqg recent-window catalogue re-enumeration with the already-fixed classifier**" —
  `Source: prediction_cross_venue_arb_and_coverage_2026_07_24.md` (P2 "cqg partition-completeness — recent-window
  catalogue re-enumeration"), still `[ ]`.
- [`prediction_satellite_ao_dispatch_batch6_2026_07_29.md`](/plans/active/prediction_satellite_ao_dispatch_batch6_2026_07_29.md)
  (`status: draft`) todo 7: "**cqg partition-completeness — recent-window catalogue re-enumeration (operational run,
  already-fixed classifier)**" — same `Source:` doc, same underlying item, also `[ ]`.

Same source doc, same source item, same repo (instruments-service), same operational run. batch6's Phase-3 conflict
check enumerated batch4 in its covering set but did not catch this overlap. If batch6 is flipped `active` as-is, the
backlog can dispatch the identical re-enumeration to two workers — the exact duplicate-dispatch class already filed as
[`prediction_trades_migration_concurrent_dispatch_2026_07_28.md`](/plans/active/issues/prediction_trades_migration_concurrent_dispatch_2026_07_28.md).

**Recommendation (mechanical, no judgment):** before flipping batch6 to `active`, delete batch6 todo 7 and cite batch4
todo 3 in its place. Not applied here — editing a batch plan's todo list is Phase-3 work, which this run was scoped out
of.

## Finding 3 — 4 prediction-tranche docs absent from the aggregated-sources index

[`prediction_consolidated_closeout_2026_07_18.md`](/plans/active/prediction_consolidated_closeout_2026_07_18.md)'s
"Aggregated source docs (referenced, not duplicated)" section names none of these (all created after the index's last
completeness re-verification, 2026-07-24):

| Doc                                                                                        | Open work                                                             |
| ------------------------------------------------------------------------------------------ | --------------------------------------------------------------------- |
| `issues/kalshi_execution_credential_secret_name_mismatch_2026_07_26.md`                    | 2 open (`[SCRIPT] P1` secret reshape, `[DATA] P1` paper-order verify) |
| `issues/kalshi_mass_attempted_failed_unclassified_adapter_error_2026_07_27.md`             | 3 open (`[DIAG] P1` ×2, `[CODE] P2` contingent backoff)               |
| `issues/features_delta_one_dependency_checker_prediction_bucket_token_wrong_2026_07_27.md` | 3 open `P3` (self-dispatching, `assigned_vm: planning`)               |
| `issues/prediction_trades_migration_concurrent_dispatch_2026_07_28.md`                     | 2 prose-only recommended fixes, no checkboxes                         |

`check_ag_closeout_linkage.py` does not catch this (all 4 are reachable via batch6's `related:` graph, so the check
reports 0 orphans, baseline 0 — re-verified this run). The gap is discoverability in the human-readable index only.

**Recommendation (mechanical):** add one `[text](path)` markdown-link line per doc to the closeout's aggregated-sources
index. Use real markdown links, not bare backticked filenames — prettier can wrap a long bare filename across a line
break and silently break the substring match the linkage check relies on. Not applied here: the closeout doc is a shared
file and this run was concurrent with 8 sibling tranche audits, so an unsolicited edit to it risked a merge collision
for no urgency (the linkage check is green either way).

## Finding 4 — the tranche's one genuinely never-touched orphan belongs to `ao`, not `prediction`

[`issues/prediction_trades_migration_concurrent_dispatch_2026_07_28.md`](/plans/active/issues/prediction_trades_migration_concurrent_dispatch_2026_07_28.md)
(`asset_group: [prediction, ao]`, `parent_epic: orchestrator_master`) is the single `orphaned_never_touched` verdict of
this run: 0 checkboxes, 2 prose-only recommended fixes (a durable task-id-keyed checkpoint location for resumable AO
scripts; a dispatcher-side in-flight/live-heartbeat check before re-assigning a dispatched todo). Nothing in
prediction's covering set claims it. `prediction_satellite_ao_dispatch_batch6_2026_07_29.md` deliberately deferred it as
"agent-orchestrator dispatch/checkpoint architecture, not prediction data work — flagging for the `ao`-tranche's own
closeout audit", but a flag in a `## Deferred` section is not ownership.

The failure it predicts has since recurred at least twice more (2026-07-29 Progress Log entries in
`prediction_satellite_ao_dispatch_batch4_2026_07_26.md`: three slots dispatched the same resumable migration, then five
stranded per-slot checkpoints nobody reconciled). This is a live, worsening gap.

**Recommendation:** the `ao` tranche's `/ag-closeout-audit` sibling run claims this doc. Its two prose fixes each need a
scoping decision first (where the shared checkpoint lives; the heartbeat-staleness threshold), so it is a design-plan
candidate, not a batch todo.

## Todos

- [x] ✅ [DOC] P2. **DONE 2026-08-02 — `unified-trading-pm@(this commit)`.** Rule on Finding 1 (A / B / C above) —
      whether `prediction_cross_venue_arb_and_coverage_2026_07_24.md` and
      `prediction_live_clob_depth_capture_2026_07_24.md` drop their inherited `cefi` tag. **Done when**: the ruling is
      recorded here and, if A, both docs' `asset_group` is `[prediction]` with `check_ag_closeout_linkage.py` re-run
      green immediately after. (repo: unified-trading-pm) **Operator RULED option A** in the 2026-07-30 interactive
      session (recorded under Finding 1 above); both docs retagged `asset_group: [prediction]` in this commit.
      **Verified**: `check_ag_closeout_linkage.py` run immediately before and after the retag — 67 orphan(s) both times
      (baseline 69, green), and a sorted diff of the two full ORPHAN lists is byte-identical, so neither retagged doc
      became newly orphaned and no third doc was disturbed. Retagged `[OPERATOR]` → `[DOC]` in this same edit per the
      CLAUDE.md stale-tag rule.
- [x] ✅ [DOC] P2. **DONE 2026-07-31** — `unified-trading-pm@(this commit)`. Resolve Finding 2 before
      `prediction_satellite_ao_dispatch_batch6_2026_07_29.md` is flipped `status: active`: delete batch6 todo 7 and cite
      batch4 todo 3 in its place, so the cqg recent-window re-enumeration has exactly one owner. **Adapted execution**
      (batch6 was already `status: active` and live-dispatching by the time this ran, changing the premise): rather than
      deleting the todo line — which would shift every subsequent todo's positional task-ID on an actively-dispatching
      plan (per the fleet's own live warning that `regen_backlog_from_plan.py` IDs are position-derived, not
      content-stable) — checked batch6's copy `[x]` IN PLACE with a "DUPLICATE — not independently executed" resolution
      note citing batch4 todo 3 as sole owner. Same outcome (exactly one owner, duplicate-dispatch risk closed), safer
      mechanism given the changed premise. **Citation relocated 2026-08-02**: the operator's 2026-07-30 ruling asked
      specifically for the batch4-todo-3 citation to live in batch6's **Deferred** section, so that section now exists
      (`## Deferred — duplicate extraction, sole owner is batch4 todo 3`) naming batch4 todo 3 as sole owner and
      recording why the deletion half of the ruling was not performed. The deletion remains deliberately NOT done for
      the same live-plan positional-ID reason — re-verified 2026-08-02 that batch6 is still `status: active` with 13
      open todos, and that batch4 todo 3 is still present and `[ ]`.
- [x] ✅ [DOC] P3. **DONE 2026-07-31** — `unified-trading-pm@(this commit)`. Resolve Finding 3: add the 4 named docs to
      `prediction_consolidated_closeout_2026_07_18.md`'s aggregated-sources index as proper `[text](path)` markdown
      links with their open-todo counts. All 4 added, plus 2 fresh 2026-07-31 adapter dead-code findings discovered by
      this same run (bonus, same fix shape) and a stale-entry correction for `kalshi_live_capture_regression_and_drift`
      (was citing 3 long-resolved prose items). `check_todo_format.sh` and `check_ag_closeout_linkage.py` both green (10
      orphans corpus-wide, baseline 32, zero `[prediction]`-tagged).
- [x] ✅ [DOC] P3. Resolve Finding 4: have the `ao` tranche adopt
      `issues/prediction_trades_migration_concurrent_dispatch_2026_07_28.md` — name it in
      `ao_consolidated_closeout_2026_07_25.md`'s own sources list so it stops reporting `orphaned_never_touched` from
      prediction's audit. **Done when**: that doc is cited by an `ao`-tranche covering doc. (repo: unified-trading-pm)
      **Re-confirmed still open 2026-07-31** — out of prediction-tranche scope to fix directly (would write to an
      `ao`-owned file); still correctly parked, not stale.

      **DONE (na-eligibility-audit 2026-08-03)** — the named target doc,
                          `plans/archive/2026_07/ao_consolidated_closeout_2026_07_25.md`, archived 2026-07-30 as a "pure reachability
                          digest"; its own archived text explicitly redirects `ao`-tranche live coverage to
                          `ao_open_issues_consolidated_close_out_2026_07_17.md` (+ `ao_satellite_ao_dispatch_batch1_2026_07_26.md`/its
                          finalize). `issues/prediction_trades_migration_concurrent_dispatch_2026_07_28` IS now named there — it appears in
                          `ao_open_issues_consolidated_close_out_2026_07_17.md`'s "Operator-gated (needs a ruling, not another audit)" table
                          (line 159) and is also cross-referenced in `ao_satellite_ao_dispatch_batch2_2026_07_30.md` (line 269, "dual-tagged
                          `[prediction, ao]`"). The done-when condition ("cited by an `ao`-tranche covering doc") is satisfied via the
                          current live covering doc, even though the specific archived file this todo originally named is no longer that
                          doc.

## Codex SSOTs

- `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` § 3 — the shared conflict-check protocol
  Finding 2 shows was not fully applied between batch4 and batch6.
- `/codex/11-project-management/doc-frontmatter-schema.md` § 5 — the `asset_group` enum Finding 1 turns on.
- `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "Dispatch-scope eligibility" — why Finding
  4's two prose fixes are not yet bounded todos.

## Progress Log

- **na-eligibility-audit 2026-08-02 (prediction tranche, autonomous)**: KEEP-NA, valid — **1 open** (was 2 at the
  2026-07-31 marker). Finding 1's `[DOC] P2` tag-scope todo closed 2026-08-02 by the sibling `ao-fix-prediction` ruling
  pass, not by this run — the operator's 2026-07-30 option-A ruling was applied (both forks retagged
  `asset_group: [prediction]`, `check_ag_closeout_linkage.py` 67 orphans before and after with byte-identical sorted
  ORPHAN lists). That is a real -1 against this doc's open-todo count, so the corpus shrank here without this run
  touching it. The 1 remaining item (Finding 4 — have the `ao` tranche adopt
  `issues/prediction_trades_migration_concurrent_dispatch_2026_07_28.md` by naming it in
  `ao_consolidated_closeout_2026_07_25.md`'s sources list) is re-confirmed genuinely gated: its `Done when` is
  satisfiable ONLY by writing to an `ao`-owned file, which is outside this doc's `predictions_master` ownership under
  the primary-owner rule. Not a defaulted-and-never-assessed item. Doc stays NA.

- **2026-08-02 (slot 3, worker `ao-fix-prediction`) — operator ruling execution pass.** Executed the two 2026-07-30
  interactive-session rulings against the CURRENT corpus (verified before each change; the corpus has moved a lot since
  the audit). **Finding 1 → RULED option A, APPLIED**: both forks retagged `asset_group: [prediction]`;
  `check_ag_closeout_linkage.py` 67 orphans before and 67 after (baseline 69), full ORPHAN lists byte-identical when
  sorted — zero new orphans, neither retagged doc appears in either list. **Finding 2 → verified already resolved, plus
  the Deferred-section citation the ruling asked for**: batch6 is already `status: active` (the ruling's flip half was
  done 2026-07-30/31, so nothing to flip), its duplicate cqg todo is already `[x]` in place, and batch4 todo 3 is still
  present and `[ ]` as sole owner; added the explicit `## Deferred — duplicate extraction, sole owner is batch4 todo 3`
  section to batch6 so the citation lives where the ruling specified. **Deliberate non-execution, reported honestly**:
  the ruling's "delete batch6 todo 7" half was NOT performed — batch6 has been live-dispatching since 2026-07-31 with 13
  open todos and `regen_backlog_from_plan.py` derives task IDs positionally, so deleting the line would renumber every
  subsequent open todo on a plan with in-flight work. The outcome the ruling targeted (exactly one owner, no duplicate
  dispatch) is fully achieved without it. **Precondition re-check the ruling asked for** ("verify the bug is still live
  before flipping"): the Kalshi CQG mis-bucketing bug is **NO LONGER LIVE** — read
  `instruments-service/instruments_service/engine/orchestrator/prediction.py` at HEAD, the Kalshi branch now does
  `ticker = instrument_key.rsplit(":", 1)[-1]` before calling `classify_kalshi_to_canonical_group`, shipped as
  `instruments-service@e0f7aaad` ("fix(prediction): extract bare Kalshi ticker before CQG classification"). The flip
  already happened and the P0 fix already dispatched and landed; the ruling's purpose was served.

- **na-eligibility-audit 2026-07-31 (prediction tranche)**: KEEP-NA, valid — 2 open (was 4 at the 2026-07-30 marker;
  Findings 2 and 3 were mechanically resolved 2026-07-31 by the sibling `/ag-closeout-audit prediction` run, see the
  Todos section above). The 2 remaining items are re-confirmed still genuinely gated, each on its own citation: Finding
  1's todo is explicitly `[OPERATOR]`-tagged (an `asset_group` tag-scope ruling); Finding 4's todo requires editing an
  `ao`-owned file (`ao_consolidated_closeout_2026_07_25.md`), out of prediction-tranche file ownership per the
  primary-owner rule. Neither is a defaulted-and-never-assessed item. Doc stays NA.

- **na-eligibility-audit 2026-07-30 (prediction tranche)**: KEEP-NA, valid — 4 open. Filed EARLIER TODAY by the sibling
  `/ag-closeout-audit prediction` run, whose own `source:` records that every item was deliberately PARKED with
  options + a marked recommendation because no operator was reachable. That is an assessed NA, not a defaulted one, so
  it fails this skill's RECLASSIFY bar ("simply defaulted to NA and never assessed") even though Findings 2/3/4 are
  mechanically executable. Finding 1 is a genuine `[OPERATOR]` tag-scope ruling. Deliberately NOT flipped 6 hours after
  a sibling skill parked it. Finding 2 (batch4 todo 3 and batch6 todo 7 both claiming the same cqg re-enumeration) is
  independently re-confirmed by THIS run's conflict-check and escalated in its report — it is a live duplicate-dispatch
  hazard the moment batch6 goes `active`.
- **2026-07-31 (slot 4, ag_closeout_auditor, dispatch agt-592e74) — `/ag-closeout-audit prediction` scheduled run.**
  Re-checked all 4 findings per the skill's iterative-drain rule (step 1: re-check the prior run's parked items before
  fresh triage). Findings 2 and 3 were mechanical with no judgment call and batch6 had by now gone `status: active`
  (raising real duplicate-dispatch stakes for Finding 2) — fixed both, see the Todos section above for exact commits and
  the adapted approach on Finding 2 (checked in place rather than deleted, to protect positional task-ID stability on
  the now-live plan). Findings 1 and 4 re-confirmed still genuinely open (operator ruling / cross-tranche adoption
  respectively) — not stale, no action taken on either. This run's own fresh Phase 0-2 pass found 0 new never-triaged
  prediction-primary orphans beyond 2 same-day dead-code findings (both correctly non-batchable, operator-gated A-vs-B
  judgment calls) and confirmed a new instance of the candidate-script's `depends_on`-resolution gap (prediction's 4
  Phase A-E children, not just `native_ao_extract`-shaped forks) — full detail in
  `issues/ag_closeout_audit_prediction_parked_2026_07_31.md`.

- **context-scout 2026-08-03**: populated context_scope (4 entries).
