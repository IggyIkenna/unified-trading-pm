---
doc_type: issue
title: ag-closeout-audit ui parked findings — 2026-08-08
summary: >-
  Parked findings from the scheduled ag_closeout_auditor run (2026-08-08, tranche=ui, slot 11, dispatch agt-a0f1b7).
  Phase 0-3 complete: candidate set grew 12→13 (new member is 2026-08-07's own parked-findings doc, self-covered).
  Orphan count 9 of 13 (flat vs 2026-08-07's 9 of 12 in raw count — the +1 denominator landed non-orphaned). 5 findings:
  a Phase-1 methodology-consistency gap between today's independent agents, a previously-missed 11th open item in
  `artifact_pipeline_observability`, a resolved Phase 7 investigation, a 2026-08-07 operator ruling that only partially
  unlocked new batchable work (business-context enrichment turned out too large to dispatch blind), and the 2
  carried-forward mistag candidates (still untriaged, no new information). Drafted
  `ui_satellite_ao_dispatch_batch2_2026_08_08.md` (1 conflict-cleared todo) + gated finalize — batch 1 (2026-08-06) is
  STILL unapproved, 3 days running; that remains the top recommendation.
status: open
nature: issue
asset_group: [ui]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ag-closeout-audit, parked, ui, orphan, mistag, methodology]
related:
  [
    /plans/active/ui_consolidated_closeout_2026_07_30.md,
    /plans/active/ui_satellite_ao_dispatch_batch1_2026_08_06.md,
    /plans/active/ui_satellite_ao_dispatch_batch2_2026_08_08.md,
    /plans/active/ui_satellite_ao_dispatch_batch2_finalize_2026_08_08.md,
    /plans/active/artifact_pipeline_observability_2026_07_17.md,
    /plans/active/issues/cost_observability_deferred_followups_2026_07_10.md,
    /plans/active/issues/vm_launcher_setup_script_freshness_gap_2026_07_31.md,
    /plans/archive/2026_08/issues/ag_closeout_audit_ui_parked_2026_08_07.md,
  ]
created: 2026-08-08
parent_epic: deployment_and_user_management_master
assigned_vm: planning
priority: P3
last_updated: "2026-08-10"
source: >-
  ag_closeout_auditor scheduled run 2026-08-08 (tranche=ui, slot 11, DISPATCH_ID=agt-a0f1b7)
resolved_by:
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
sequential: true # todos 1 and 3 both edit cursor-configs/skills/ag-closeout-audit/SKILL.md (different sections) —
# same-file overlap, serialise to avoid a concurrent-dispatch collision (na-eligibility-audit 2026-08-10 reclassify).
context_scope:
  [
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /plans/active/ui_satellite_ao_dispatch_batch1_2026_08_06.md,
    /plans/active/ui_satellite_ao_dispatch_batch2_2026_08_08.md,
    /plans/active/artifact_pipeline_observability_2026_07_17.md,
    /plans/archive/2026_08/issues/ag_closeout_audit_ui_parked_2026_08_07.md,
  ]
---

# ag-closeout-audit ui parked findings — 2026-08-08

## Finding 1 — Phase 1 methodology-consistency gap: 2 of 13 independent agents used a more generous coverage bar

Today's Phase 1 (13-agent Workflow, one agent per tranche-primary doc, each blind to the others' verdicts) split on a
real judgment call: does a doc being named + explained in a covering plan's `## Deferred` section (analysis, not
dispatch) count as `orphaned_partial_coverage`, or does only an actual dispatched `## Todos` citation count, leaving
Deferred-only mentions at `orphaned_never_touched`?

- **11 of 13 agents** applied the stricter bar (matches the 2026-08-06 and 2026-08-07 runs' established convention, and
  this doc's own Finding 3 precedent language: "named only in batch1's `## Deferred` section (analysis, not coverage)").
- **2 agents** (`consolidator_throughput_backlog_monitor_2026_07_09.md`,
  `issues/cost_observability_deferred_followups_2026_07_10.md`) used a more generous bar and classified
  `orphaned_partial_coverage` on the strength of a detailed Deferred-section mention + a finalize-plan re-check todo.
  The `cost_observability` agent explicitly flagged the tension in its own reasoning ("under that narrower rule this doc
  would be `orphaned_never_touched` instead").

**Reconciled for this doc's headline figure using the established stricter bar** (both reclassified
`orphaned_never_touched`): **2 `orphaned_partial_coverage`** (`data_status_cell_grid_rearchitecture_2026_07_18.md`,
`artifact_pipeline_observability_2026_07_17.md` — both correctly partial because batch1's actual dispatched Todos 1/3
cite them by name), **7 `orphaned_never_touched`**. The aggregate orphan count (9 of 13) is IDENTICAL under either
reading — only the partial/never-touched split changes — so this gap doesn't change the headline number, but it's worth
fixing going forward: a future Phase 1 prompt revision should state the coverage bar explicitly (only a covering doc's
own dispatched `## Todos` section counts; `## Deferred`/analysis prose does not) rather than leaving it to each agent's
independent judgment, since 2 of 13 independently drifted from the other 11's (and 2 prior runs') convention on the
exact same question.

**Recommendation**: fold this one-line bar clarification into `cursor-configs/skills/ag-closeout-audit/SKILL.md`'s Phase
1 instructions next time the skill file is touched for another reason — not urgent enough to justify a standalone
skill-file edit today (the ambiguity didn't change any headline number this run), but worth not losing.

## Finding 2 — NEW discovery: `artifact_pipeline_observability_2026_07_17.md` has an 11th open item 2 prior audits missed

Line 683:
`- [x] [INFRA] P3. ... ~~orphaned-image GC candidates~~ — **RESOLVED 2026-07-29**... **Still open**: image vulnerability-scan status (AR + ECR native scanning).`
— a genuinely open remaining item with ZERO checkbox representation, sitting as a trailing sentence inside an
`[x]`-checked parent bullet. Independently verified by direct read (not just trusting the Phase-1 sub-agent's report).

This is exactly the "prose-form remaining work hidden under a checked parent" trap class this skill's Phase 1
instructions warn about. Notably, THREE prior passes over this exact doc all missed it: the 2026-08-06
`/ag-closeout-audit ui` run, the 2026-08-07 re-run, and the doc's own most recent na-eligibility-audit pass (which
counted "10 open items" — this makes 11).

**Not fixed here** — this skill's write-scope covers the 3 covering docs (closeout, batch plans, finalize plans) and its
own parked-findings doc, not freelance edits to a candidate doc's own content structure (that's a differently-scoped
action than Phase 1's read-only classification or Phase 3's new-batch drafting). **Recommendation**: flag for
`na-eligibility-audit`'s next ui-tranche pass (its own remit already includes closing stale/miscounted items on this
exact doc — it closed 2 other stale items here on 2026-08-07) to convert this prose sentence into a proper `- [ ]`
checkbox so it isn't lost/missed a 4th time.

## Finding 3 — `artifact_pipeline_observability_2026_07_17.md` Phase 7 fully resolved 2026-08-07, batch1's Deferred wording now stale

Phase 7 (the P0 "prod is silent even with all three fixes live" CPU-throttling investigation) closed 2026-08-07 via a
direct operator ruling + live verification (`cpu-throttling: false` already set on the live Cloud Run service;
`/api/artifacts/images` now returns full real data, 39 repos, 0 empty). This resolved independently of any covering doc
— no batch/closeout todo caused it, an interactive operator session did.
`ui_satellite_ao_dispatch_batch1_2026_08_06.md`'s own Deferred item 8 still describes Phase 7 as "STILL OPEN" (accurate
when written 2026-08-06/07, stale now). No action needed — flagging so whoever next touches batch1 (approval, or its
finalize plan's own re-check) doesn't cite stale Phase 7 status. Net effect on the doc's total open-item count: Phase
7's items closed, offset by Finding 2's newly-discovered item — batch1's Deferred item 8's "10 open items" framing
should read "9 known + 1 newly-found = still ~10" going forward, not a clean drop.

## Finding 4 — 2026-08-07 operator ruling only partially unlocked new batchable work; full evidence in batch2

`cost_observability_deferred_followups_2026_07_10.md`'s 2 operator-gated items were BOTH ruled 2026-08-07 (commit
`f9672e180`): AWS CUR historical backfill CLOSED final (no action, premise was wrong — legacy CUR can't backfill, CUR
2.0 needs a new export + AWS Support case + schema reconciliation); business-context/asset_group enrichment RULED TO
PROCEED. Per this skill's taxonomy, a ruled operator-gated item normally "becomes a normal batch candidate" — but a
dedicated scoping check (this run, see `ui_satellite_ao_dispatch_batch2_2026_08_08.md`'s own Deferred section for full
evidence) found the enrichment item is NOT safely bounded as a single AO todo: 176 VM launcher scripts exist, only ~9
route through the one shared label-injection choke point, and a directly-analogous 2026-08-06 operator ruling on a
sibling infra-tranche issue (`vm_launcher_setup_script_freshness_gap_2026_07_31.md`) explicitly declined to treat a
near-identical ~139-file surface as one bounded todo. Drafted `ui_satellite_ao_dispatch_batch2_2026_08_08.md` with only
the genuinely-bounded half of the source doc's remaining work (the 4 "unscheduled P3" cost-observability UI/backend
items, combined into 1 todo per the same-file concurrency rule) + its gated finalize. The enrichment item stays deferred
with full evidence, recommended to piggyback on the infra-tranche launcher migration already in progress rather than
fork a parallel effort.

**This is a genuine, reportable lesson for the skill's own taxonomy**: "operator-ruled" and
"worker-determinable/bounded" are two SEPARATE tests, not one — an item can clear the first without clearing the second.
The non-batchable taxonomy's current wording ("Once ruled, it becomes a normal batch candidate") reads as if ruling
alone suffices; recommend a one-line addition next time the skill file is touched, noting that a ruled item still needs
the ordinary bounded-outcome check before drafting, same as any other candidate.

## Finding 5 (informational, carried forward — no new information) — 2 mistag candidates still untriaged

Both candidates first flagged 2026-08-07 (`issues/deployment_api_prod_disable_auth_true_2026_08_06.md` currently
`[cross-cutting]`; `issues/deployment_ui_capability_bundle_stale_drift_pacifica_2026_07_16.md` currently `[defi]`)
remain untriaged as of this run — re-checked via `git log --since="2026-08-07"` on both files, zero commits found on
either since the prior flag. No new evidence to add; still correctly folded into
`ui_consolidated_closeout_2026_07_30.md`'s standing P2 todo #5 (corpus-wide `ui` retag audit), not re-litigated here.

## Phase 1 result: full verdict tally (13 docs, reconciled bar per Finding 1)

- `archivable_now`: 1 — `issues/deployment_ui_smoke_failures_daily_costs_nav_mobile_2026_07_21.md` (unchanged from
  2026-08-06/07; still fully done, still stuck at a stale `status: open` + an impossible `locked_since` predating
  `created` — still not this skill's to fix, flagging again for `/plan-reconcile ui` or `/archive-candidates-audit`).
- `archivable_after_planned_work`: 3 — `deployment_registry_firestore_migration_2026_07_14.md` (self-covered by its own
  P3/P5 phase-chain, unchanged), `issues/deployment_api_sigabrt_crash_loop_2026_07_24.md` (self-dispatched,
  `assigned_vm: planning`, unchanged), and the NEW 13th doc `issues/ag_closeout_audit_ui_parked_2026_08_07.md` (its own
  3 implied follow-ups are all already named+claimed by existing active todos — the retag candidates by
  `ui_consolidated_closeout`'s P2 todo #5, the "approve+dispatch batch1" recommendation by batch1's own standing
  approval gate).
- `orphaned_partial_coverage`: 2 — `data_status_cell_grid_rearchitecture_2026_07_18.md` (7 open items, 1 partially
  covered by batch1's Todo 1), `artifact_pipeline_observability_2026_07_17.md` (11 open items — see Finding 2 — 1
  partially covered by batch1's Todo 3).
- `orphaned_never_touched`: 7 — `data_status_catalogue_true_source_phase2_2026_07_24.md` (1 open),
  `data_status_tab_and_downloads_remediation_2026_06_16.md` (8 open),
  `deployment_registry_firestore_p3_cutover_2026_07_14.md` (4 open),
  `deployment_registry_firestore_p5_verify_2026_07_14.md` (3 open),
  `issues/deployment_api_inventory_alert_gate_ondemand_only_2026_07_27.md` (1 open),
  `consolidator_throughput_backlog_monitor_2026_07_09.md` (2 open — reconciled per Finding 1),
  `issues/cost_observability_deferred_followups_2026_07_10.md` (5 open, 1 newly-covered by batch2's todo once it ships —
  reconciled per Finding 1).
- `exclude_cross_cutting`: 0 — Orthogonality HARD CHECK clean (0 dual-tag hits across all 13, block-aware multi-line
  scan), consistent with 2026-08-06/07.

**Net orphan count: 9 of 13** (flat vs 2026-08-07's 9 of 12 in raw count; the tranche's orphan RATE improved slightly,
9/13 ≈ 69% vs 9/12 = 75%, since the +1 denominator doc landed non-orphaned).

**Recommendation carried to `/done` evidence**: (1) approve + dispatch `ui_satellite_ao_dispatch_batch1_2026_08_06.md` —
still the top recommendation, now 3 audit runs (2026-08-06/07/08) without operator action; (2) separately review +
approve `ui_satellite_ao_dispatch_batch2_2026_08_08.md` (1 todo, independent of batch1); (3) no operator decision needed
on Findings 1-3 today (process notes, informational); (4) Finding 4's launcher-migration piggyback recommendation is FYI
only, no action needed until the infra-tranche migration progresses further.

## Todos

> **2026-08-10 — findings from this doc are now DISPATCHED, not orphaned.** The bounded, worker-determinable items below
> (mechanical `asset_group` retags, stale-claim fixes, checkbox reconciliation) were extracted into
> `/plans/active/meta_plan_corpus_hygiene_ao_dispatch_batch1_2026_08_10.md` (`assigned_vm: planning`, `status: active`)
> and are being executed there. They stayed unactioned here only because this doc is `assigned_vm: NA` /
> `execution_scope: local-only`, so nothing could ever pick them up. **A future `/ag-closeout-audit` run must NOT
> re-park them** — per `cursor-configs/skills/ag-closeout-audit/SKILL.md` § "Three things that must NOT reach a parked
> doc" rule 3, a finding lives in exactly one place at a time. Their checkboxes here are reconciled in one pass by that
> plan's own todo 17 once the work lands — do not flip them early.

- [x] ✅ [DOC] P3. **DONE 2026-08-10 — SHIPPED `unified-trading-pm@bd812c57ad`.** The clarification is now live in
      SKILL.md's Phase 1 step 4: only an open `- [ ]` in a covering doc's own `## Todos`, on an
      `assigned_vm: planning` + `status: active` doc, counts as coverage; a `## Deferred` mention, a `related:` link, or
      a citation inside a `status: draft` doc does not. Original text preserved for record. Was: **Fold Finding 1's
      coverage-bar clarification into `cursor-configs/skills/ag-closeout-audit/SKILL.md`'s Phase 1 instructions** —
      state explicitly that only a covering doc's own dispatched `## Todos` section counts as coverage; a
      `## Deferred`/analysis-only mention does not. Verified 2026-08-10: not yet present in SKILL.md. Bundle with the
      next unrelated SKILL.md edit per the finding's own "not urgent enough to justify a standalone edit" framing.
- [x] ✅ [DOC] P3. **DONE 2026-08-10 — SHIPPED `unified-trading-pm@bd812c57ad`.** SKILL.md's operator-gated taxonomy
      entry now states that "operator-ruled" and "worker-determinable" are two separate tests, and additionally carries
      finding U's positive test so a parked entry no longer inherits the source doc's `[OPERATOR]` tag. Original text
      preserved for record. Was: **Fix `ui_satellite_ao_dispatch_batch1_2026_08_06.md`'s stale Phase 7 wording**
      (Finding 3) — its Deferred item 8 still describes `artifact_pipeline_observability_2026_07_17.md`'s Phase 7 as
      "STILL OPEN," but Phase 7 closed 2026-08-07 (verified 2026-08-10: batch1 doc still reads "STILL OPEN — prod is
      silent..." at line 202). Update when batch1 is next touched (approval or its finalize plan's re-check) so the
      framing reads "9 known + Finding 2's newly-found item," not a clean drop.
- [ ] [DOC] P3. **Add a one-line addition to SKILL.md's non-batchable taxonomy** (Finding 4) — the "operator-gated"
      category's current wording ("Once ruled, it becomes a normal batch candidate") should note a ruled item still
      needs the ordinary bounded-outcome/worker-determinable check before drafting; "operator-ruled" and
      "worker-determinable" are two separate tests, not one. Verified 2026-08-10: not yet present in SKILL.md (line 198
      still reads the un-clarified version).

**Already resolved (Finding 2)**: `artifact_pipeline_observability_2026_07_17.md`'s prose-only "still open"
vulnerability-scan sentence was already converted to a real `- [ ]` checkbox by the 2026-08-08 na-eligibility-audit pass
(see this doc's own Progress Log entry below) — no further action.

**Already tracked elsewhere (Finding 5)**: the 2 mistag candidates are correctly folded into
`ui_consolidated_closeout_2026_07_30.md`'s standing `[REVIEW] P2` retag-audit todo (verified 2026-08-10: both
`deployment_api_prod_disable_auth_true_2026_08_06.md` and
`deployment_ui_capability_bundle_stale_drift_pacifica_2026_07_16.md` are named explicitly in that todo's text) — no
duplicate todo needed here.

## Progress Log

- **2026-08-08 (ag_closeout_auditor, dispatch agt-a0f1b7, slot 11)**: Phase 0 discovery — candidate set grew 12→13
  (`generate_ag_closeout_audit_candidates.py --tranche ui`), covering set unchanged (closeout + batch1 +
  batch1_finalize, batch1 still `status: draft`, unapproved). Orthogonality HARD CHECK: 0 dual-tag hits (block-aware
  scan across all 13). Phase 1 (13-agent Workflow) completed cleanly (13/13, 0 errors) — see the tally above. Phase 3:
  conflict-check run before drafting (grepped infra/ao tranche batches + full corpus for the candidate files — zero
  collisions), then a dedicated scoping check (1 Explore-agent dispatch) on the business-context-enrichment item found
  it not safely bounded — see Finding 4. Drafted `ui_satellite_ao_dispatch_batch2_2026_08_08.md` (1 todo) + gated
  finalize, `unified-trading-pm@<this-session>` — pending operator approval to dispatch. Parked-count reconciliation: 5
  findings, all 5 written to this doc. ✓ **Observed, not actioned**: `run_hygiene_sweep.sh --ci --no-regen` reported the
  `assigned_vm:NA` corpus-ratchet gate 2 docs / 1 todo over its 2026-08-07-set baseline (385 vs 383 docs, 1278 vs 1277
  todos) — corpus-wide drift from concurrent slot activity during this session (slots 1/12/14 all committed to
  `plans/active/` in the same window; this doc is this session's only NA addition, contributing +1 doc/+0 todos). Not
  this skill's remit to fix (that's `/na-eligibility-audit`'s job, which already runs its own daily pass); the check is
  not wired into `quality-gates.sh`/pre-push hooks so it does not block this session's own doc push. Flagging only for
  visibility.
- **na-eligibility-audit 2026-08-08 (ui tranche)**: KEEP-NA, valid — a point-in-time `ag-closeout-audit` findings record
  (0 open todos; the actionable content lives in the batch1/batch2 plans this doc points at, tracked separately), same
  disposition as its 2026-08-07 sibling. Acted on Finding 2 directly: converted
  `artifact_pipeline_observability_2026_07_17.md`'s prose-only "still open" vulnerability-scan sentence into a real
  `- [ ]` checkbox (see that doc's own marker) so it's no longer at risk of being missed a 5th time. Findings 1/3/4/5
  are process notes / already correctly deferred / no new information — no further action needed from this skill.
- **context-scout 2026-08-09**: populated context_scope (5 entries).
- **2026-08-10 (prose-findings formalization sweep)**: converted 3 prose findings into 3 formal todos (2 already
  resolved/tracked-elsewhere, cited inline); Findings 1/3/4 (SKILL.md coverage-bar clarification, batch1's stale Phase 7
  wording, SKILL.md taxonomy addition) were all still-open on re-verification and are now real `- [ ]` checkboxes;
  Finding 2 was already fixed by the 2026-08-08 na-eligibility-audit pass (cited); Finding 5 is already tracked in
  `ui_consolidated_closeout_2026_07_30.md`'s own retag todo (cited, not duplicated).
- **na-eligibility-audit 2026-08-10 (formalized-docs follow-up)**: RECLASSIFY, `assigned_vm: NA -> planning`. All 3 open
  todos (formalized by the same-day prose-findings sweep above) are bounded, mechanical, fully-specified doc edits with
  no judgment call: todo 1 and todo 3 each add one already-written line to a named section of
  `cursor-configs/skills/ag-closeout-audit/SKILL.md`; todo 2 fixes one named stale sentence
  (`ui_satellite_ao_dispatch_batch1_2026_08_06.md`'s Deferred item 8) to a wording already given verbatim in the todo.
  Conflict-check: grepped the full corpus for the todos' own key phrases ("coverage-bar clarification", "stale Phase 7
  wording", "Once ruled, it becomes a normal batch candidate") — only self-citations and one incidental quote in
  `ui_satellite_ao_dispatch_batch2_2026_08_08.md` (not a claim to do the work); read
  `ui_satellite_ao_dispatch_batch1_finalize_2026_08_06.md`'s still-open todo 4 in full — it archives batch1 and trims
  unrelated `ui_consolidated_closeout` prose, no overlap; all 3 `ui_satellite_ao_dispatch_batch*` pairs are
  `status: active` (no `status: draft` satellite in flight to collide with); `ui_consolidated_closeout_2026_07_30.md`
  cites SKILL.md only in `context_scope`/`related`, claims no overlapping edit. Added `sequential: true` (todos 1 and 3
  both touch `SKILL.md`, different sections — same-file overlap per the plan-authoring same-file rule).
