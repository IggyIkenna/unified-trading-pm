---
doc_type: issue
title:
  /ag-closeout-audit's Phase-0 pre-filter misses line-cap-split closeout forks as covering docs (sports never-cited
  inflated 3 -> 18, a 6x false-positive rate), and the sports P0 derived_features fabrication todo is false-unchecked in
  two places
summary: >-
  Found during a full `/ag-closeout-audit sports` run (2026-07-30, Phases 0-2). TWO independent findings. (1) TOOLING:
  `scripts/plan-hygiene/generate_ag_closeout_audit_candidates.py::_covering_paths()` selects covering docs by the
  filename regex `(dispatch_batch|satellite|_finalize)`, which structurally cannot match the line-cap-split closeout
  forks the SKILL's own Phase 0.2 path (b) says MUST be counted as covering — for sports those are
  `sports_closeout_track_x_hygiene_2026_07_25.md`, `sports_closeout_track_s2_foldin_2026_07_25.md`,
  `sports_closeout_exchange_fixed_odds_fork_2026_07_25.md` and `sports_consolidated_native_ao_extract_2026_07_25.md`
  (all four are named in the consolidated closeout's own `depends_on:`/`related:`). With the 17-doc covering set the
  script builds, sports reports 18 never-cited candidates; with the skill-correct 21-doc set it reports 3 — the other 15
  are false positives that would each draw a real agent read on a re-audit. (2) FALSE-UNCHECKED P0: the sole open
  `[DATA] P0` in `issues/sports_derived_features_fabricated_corpus_scope_2026_07_20.md`, and the matching PURGE `[DATA]
  P0` in `sports_consolidated_closeout_2026_07_19.md`, are both provably closed by the already-archived
  `sports_derived_features_postfloor_residue_purge_2026_07_27.md` (both its todos `[x]`; exhaustive Tier-2 SPOT census
  of 2400/2400 in-scope days over 26,891 objects returned `total_delete=0`) plus the pre-floor wipe
  (`deployment-service@78a0aa4`) that moots 2017/2018. Neither checkbox was flipped, so an ML-blocking P0 reads as open
  when it is done.
status: open
nature: issue
asset_group: [sports]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [plan-hygiene, ag-closeout-audit, tooling-gap, false-unchecked, sports, audit-findings]
related:
  [
    /plans/active/issues/sports_derived_features_fabricated_corpus_scope_2026_07_20.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/archive/2026_07/sports_derived_features_postfloor_residue_purge_2026_07_27.md,
    /plans/active/ag_closeout_audit_rollout_2026_07_25.md,
    /plans/archive/issues/ag_closeout_audit_asset_group_comment_grep_blindspot_2026_07_26.md,
  ]
created: "2026-07-30"
last_updated: "2026-07-30"
parent_epic: plan_hygiene_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.2
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
source: >-
  Full `/ag-closeout-audit sports` run, 2026-07-30 (Phases 0-2 only, read-only; Phase 3 deliberately not run). Both
  findings are measured from the live corpus at `unified-trading-pm@58fa82c71`, not inferred.
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
---

# `/ag-closeout-audit` sports run — pre-filter covering-set gap + a false-unchecked P0

## Finding 1 — the Phase-0 pre-filter under-counts the covering set (tooling defect)

`scripts/plan-hygiene/generate_ag_closeout_audit_candidates.py::_covering_paths()` builds a tranche's covering-doc set
as: the `*_consolidated_closeout_*` glob, plus every `plans/active/<prefix>_*.md` whose filename matches
`re.search(r"(dispatch_batch|satellite|_finalize)", name)`.

That regex is filename-pattern-only — it is exactly the Phase 0.2 **path (a)** the skill describes. The skill then adds
**path (b)** (the dependency-graph path) precisely because path (a) alone misses a real class:

> "this catches plans FORKED OUT of the consolidated closeout itself during a line-cap split ... whose filenames
> describe their CONTENT (a Track/phase name), not the `ao_dispatch`/`satellite`/`batch` pattern — path (a) alone
> silently misses these, which would misclassify an already-covering, already-AO-readiness-scrubbed plan as an orphan
> needing a fresh draft."

The script implements path (a) and never path (b). Measured for sports:

| covering fork (all `status: active`, `assigned_vm: planning`) | matches the regex? | named in the closeout's `depends_on:`/`related:`? |
| ------------------------------------------------------------- | ------------------ | ------------------------------------------------- |
| `sports_closeout_track_x_hygiene_2026_07_25.md`               | no                 | yes (8 refs)                                      |
| `sports_closeout_track_s2_foldin_2026_07_25.md`               | no                 | yes (6 refs)                                      |
| `sports_closeout_exchange_fixed_odds_fork_2026_07_25.md`      | no                 | yes (7 refs)                                      |
| `sports_consolidated_native_ao_extract_2026_07_25.md`         | no                 | yes (7 refs)                                      |

All four are genuine batch-extraction plans (each carries `source:` text naming the line-cap split, and 4/12/11/28 real
todos respectively; the native_ao_extract one cites `Source: sports_consolidated_closeout_2026_07_19.md:<lines>` per
todo). Three of the four are literally in the closeout's `depends_on:` list.

**Effect**: with the script's 17-doc covering set, sports reports **18** never-cited candidates. With the skill-correct
21-doc set, it reports **3**. The 15-doc delta is pure false positive — docs that ARE cited by a real covering plan,
each of which would draw a full agent read on every future re-audit of this tranche. The same defect applies to every
tranche that has been through the 2026-07-25 consolidated-plan line-cap split (per the skill, that is all 5 AGs).

This is the same failure family as `issues/ag_closeout_audit_asset_group_comment_grep_blindspot_2026_07_26.md` (a
discovery-step defect that silently changes the candidate set), just on the covering-set axis rather than the membership
axis.

- [ ] [SCRIPT] P2. Extend `generate_ag_closeout_audit_candidates.py::_covering_paths()` to implement the skill's Phase
      0.2 path (b) alongside the existing path (a): parse the tranche's `*_consolidated_closeout_*` frontmatter
      `depends_on:` + `related:`, resolve each entry to a `plans/active/*.md` path, and UNION those into the covering
      set (path (a) results stay). Keep the existing `aggregated_sources`/`_history_` exclusions. **Done when**:
      `--tranche sports` reports 21 covering docs and 3 never-cited (down from 17/18), and every other tranche's
      never-cited count is re-reported in this doc's Progress Log so the fleet-wide blast radius of the correction is
      recorded rather than assumed. (repo: unified-trading-pm)

## Finding 2 — an ML-blocking P0 is false-unchecked in two separate docs

`issues/sports_derived_features_fabricated_corpus_scope_2026_07_20.md` carries exactly one open todo:

> `- [ ] [DATA] P0. Remediate the corpus-wide §Z fabrication — extend the re-run to 2017+2018 (never in scope), purge (not just overwrite) every derived_features parquet still carrying a pre-fix creation timestamp, and re-verify by census, not sampling.`

All three clauses are provably satisfied by later, already-landed work:

1. **2017+2018** — moot, not re-run: both years are 100% pre-floor (before the 2020-06-06 sports data floor) and their
   26,089 fabricated objects were deleted by the pre-floor GCS wipe (`deployment-service@78a0aa4`, 2026-07-21). The
   consolidated closeout already carries this as its own `[x]` ("RESOLVED VIA PRE-FLOOR WIPE, not a re-run").
2. **Purge the post-floor remainder** — done by `sports_derived_features_postfloor_residue_purge_2026_07_27.md`, now
   archived with `status: complete` and both todos `[x]`. Its Todo 1 ran the exhaustive Tier-2 SPOT census (2400/2400
   in-scope days, Jun-Dec 2020 + 2021-2026, 26,891 objects); Todo 2 resolved as a verified no-op because that census
   returned `total_delete=0` — every in-scope object already carries a `last_modified` on/after the 2026-07-19 cutoff.
3. **Re-verify by census not sampling** — that same exhaustive census IS the census-based re-verification the clause
   asks for, and it is decidable from object metadata alone exactly as the clause requires.

The matching PURGE todo in `sports_consolidated_closeout_2026_07_19.md`
(`- [ ] [DATA] P0. PURGE the fabricated POST-FLOOR remainder (Jun-Dec 2020 + 2021-2026 only)...`) is stale-unchecked for
the identical reason.

**Why this matters beyond a checkbox**: the source doc states this P0 "freezes downstream ML work on sports until the
corpus is clean" per `/codex/02-data/data-pipeline-correctness-hard-rule.md`'s foundation-completion-gate. A
false-unchecked foundation gate keeps a layer-N+1 freeze nominally armed after the underlying condition has cleared.

Flipping these is `/plan-reconcile`'s job, not `/ag-closeout-audit`'s (this skill's own scope note: "Run
`/plan-reconcile` first if the corpus might have stale/false-unchecked state — this skill's classification is only as
good as the frontmatter `status` it reads"), so this run recorded it rather than flipping it.

- [x] ✅ [DOC] P2. **DONE 2026-07-30 (`/na-eligibility-audit`, sports tranche).** Both checkboxes flipped `[x]` with the
      evidence cited inline, exactly as specified: (a)
      `issues/sports_derived_features_fabricated_corpus_scope_2026_07_20.md`'s sole `[DATA] P0` — all three of its
      clauses addressed individually (2017/2018 moot via the pre-floor wipe; post-floor purge = verified no-op;
      census-based re-verification = the same exhaustive census); (b) `sports_consolidated_closeout_2026_07_19.md`'s
      PURGE `[DATA] P0`. Evidence re-verified live this pass before flipping (not taken from this doc's own claim):
      `/plans/archive/2026_07/sports_derived_features_postfloor_residue_purge_2026_07_27.md` exists at that path, is
      `status: complete`, both its todos are `[x]`, and its census figures read `days_scanned=2400`, `total_delete=0`,
      `total_keep=26891`, `total_unparseable=0`. **Residual NOT flipped, filed as the follow-up todo below**: the
      closeout's SEPARATE `[DATA] P0` "Re-verify by CENSUS, not sampling" checkbox (immediately after the PURGE one) is
      satisfied by the same census artifact by inference, but this doc's Finding 2 named only the PURGE checkbox, so it
      was left open rather than closed on an unnamed inference. Original text: Flip
      `issues/sports_derived_features_fabricated_corpus_scope_2026_07_20.md`'s sole `[DATA] P0` and
      `sports_consolidated_closeout_2026_07_19.md`'s PURGE `[DATA] P0` to `[x]`, each citing
      `/plans/archive/2026_07/sports_derived_features_postfloor_residue_purge_2026_07_27.md` (exhaustive census
      2400/2400 days, 26,891 objects, `total_delete=0`) + `deployment-service@78a0aa4` (pre-floor wipe) as evidence;
      then archive the fabricated-corpus-scope issue doc if it has no other open work. **Done when**: both checkboxes
      are `[x]` with the evidence cited inline and `check_todo_regression.sh` is green. (repo: unified-trading-pm)
- [ ] [DOC] P3. **Follow-up split out 2026-07-30 (`/na-eligibility-audit`, sports tranche) — two residuals from the todo
      above, deliberately NOT actioned in that pass.** (1) `sports_consolidated_closeout_2026_07_19.md` carries a
      SECOND, separate `[DATA] P0` ("Re-verify by CENSUS, not sampling, only after the PURGE todo above is done") whose
      terminal check — "zero pre-fix-dated POST-FLOOR `derived_features` objects remain" — is satisfied by the very same
      `sports_derived_features_postfloor_residue_purge_2026_07_27.md` census (`total_delete=0` over 2400/2400 days,
      decidable from object metadata alone, exactly the form the clause requires); it was left open only because Finding
      2 above named the PURGE checkbox and not this one. Confirm and flip it, or state why the census does not satisfy
      it. (2) `issues/sports_derived_features_fabricated_corpus_scope_2026_07_20.md` now has ZERO open todos and is
      unlocked (`locked_by:` empty) — per the archive-immediately HARD RULE it is an archival candidate; run the
      standard 6-step ritual (`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`), including fixing
      every corpus referrer, rather than leaving it sitting `status: open`. **Done when**: the closeout's census
      checkbox is resolved either way, and the fabricated-corpus-scope doc is archived or a stated reason it should not
      be is recorded here. (repo: unified-trading-pm)

## Finding 3 (recorded, no todo) — a skill-text ambiguity worth an operator ruling

`cursor-configs/skills/ag-closeout-audit/SKILL.md` § "Also NOT `/na-eligibility-audit`" states: _"An `assigned_vm: NA`,
`status: active`/`open` doc is by definition NOT orphaned (it has an owner: itself)"_. Read literally that makes the
orphan question vacuous — every doc in `plans/active/` is `active`/`open` by construction, since the discovery step
already excludes `resolved`/`archived`/`superseded`. It also contradicts the shipped pre-filter, which treats only
`assigned_vm: planning` + `active`/`open` as self-dispatched (`self_dispatched` in
`generate_ag_closeout_audit_candidates.py`) and correctly leaves `NA` docs in the orphan population.

This run applied the pre-filter's reading (`planning` = self-dispatched and therefore covered; `NA` = not dispatched by
anything, so orphaned unless a covering doc's OPEN todo claims its remaining work), which is the only reading under
which the audit answers a non-trivial question. Flagging the SKILL.md wording as the side that should change — but that
is a codex/skill edit requiring an operator ruling, so no edit was made.

## Progress Log

- **na-eligibility-audit 2026-07-30**: RECLASSIFY-CANDIDATE but CONFLICT -> PARKED, `assigned_vm` NOT flipped. Its
  `[DOC] P2` was executed in this pass (both false-unchecked P0s flipped with evidence; a P3 residual follow-up filed
  here). Its remaining `[SCRIPT] P2` — extend `generate_ag_closeout_audit_candidates.py::_covering_paths()` with
  SKILL.md Phase 0.2 path (b) — is a near-verbatim duplicate of the open `[SCRIPT] P2` in
  `/plans/active/issues/ag_closeout_audit_orphan_definition_and_digest_citation_defects_2026_07_30.md` (also
  `assigned_vm: NA`, `status: open`, also filed 2026-07-30). Two NA docs claiming the same one-function fix is a genuine
  CONFLICT under the shared protocol step 3 (not the step-4 stale-checkbox case, which requires the extractor to be an
  active `planning` doc), so neither side was silently preferred. Needs an operator ruling on which doc owns it; then
  that one flips and the other cites it.
