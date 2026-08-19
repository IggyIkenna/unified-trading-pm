---
doc_type: issue
title: "2026-08-19 plan_reconciler sports tranche — daily deep reconciliation run"
summary: >-
  Sharded daily deep plan-reconciliation pass over the sports tranche. Phase -1 reconciled the 2026-08-18 prior sports
  findings doc's own "next pass" action items — most notably completing
  `sports_consolidated_native_ao_extract_2026_07_25_finalize.md` todo 1 (reconcile 5 still-open
  `sports_consolidated_closeout_2026_07_19.md` checkboxes with HARD evidence from the now-fully-done extract plan) and
  catching a duplicate-dispatch (a satellite batch re-drafted already-shipped work). Also found and worked around a
  `check_line_caps.sh` bug (a "whitespace-only repair" exemption that doesn't actually verify `git diff -w` is empty).
  A separate, recent interactive epic-scoped `/plan-reconcile sports_master` run (slot-5·laptop, commit `a481f6357a`,
  ~03:18 UTC+1 today) had already landed substantial fixes hours before this dispatch — this run avoided
  re-discovering that work and instead covered ground it didn't reach.
status: open
nature: issue
asset_group: [sports]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan_reconciler, reconciliation, sports, plan-hygiene, sharded]
related:
  [
    /agents/plan_reconciler.md,
    /cursor-configs/skills/plan-reconcile/SKILL.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/active/sports_consolidated_native_ao_extract_2026_07_25_finalize.md,
    /plans/active/issues/plan_reconciler_findings_sports_2026_08_18.md,
  ]
created: "2026-08-19"
parent_epic: plan_hygiene_master
priority: P2
estimate_class: research
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.6
assigned_role: review
assigned_vm: NA
execution_scope: local-only
locked_by: plan_reconciler (agt-07473e) since 2026-08-19T18:40:03Z
locked_since: "2026-08-19T18:40:03Z"
supersedes:
superseded_by:
resolved_by:
author: plan_reconciler
source: "Sharded daily /plan-reconcile sports-tranche sweep, dispatch agt-07473e, slot 4, 2026-08-19."
drift_direction: advance-code
depends_on: []
context_scope:
  [
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/active/sports_consolidated_native_ao_extract_2026_07_25_finalize.md,
    /plans/active/issues/plan_reconciler_findings_sports_2026_08_18.md,
  ]
---

# plan_reconciler findings — sports — 2026-08-19

Dispatch `agt-07473e`, slot 4, tranche `sports`. Deep reconciliation pass per `agents/plan_reconciler.md` STEPs 1-8.
This doc is the run journal + final report surface.

**Corpus**: 109 docs (Phase-0 inventory, `generate_tranche_doc_inventory.py --tranche sports`; 1 header-line artifact
in the raw output, 108 real docs). 8 in the 12h grace window (read-only context this run). 100 non-grace docs are the
actionable working set.

**Slot-health pre-check**: the boot heartbeat surfaced stale FF-pull-starvation / git-status-red nudges for this slot
(unified-trading-pm behind by up to 38 commits with blocking dirty issue-doc files; deployment-api AHEAD=1). Both
verified ALREADY RESOLVED by the time this run started (`git status` clean, `ahead=0`/`behind=0` on both repos) —
no action needed, noted for the record per "verify current state before acting on stale info."

## Phase -1 — reconciling the 2026-08-18 prior sports findings doc

The 2026-08-18 run (`agt-57336e`, slot 31) completed cleanly (locked_by cleared, "Plans not reached: None") and named
concrete **"Action for the next sports pass"** items. Checked each against current state:

1. **Fix the broken link in `sports_consolidated_closeout_2026_07_19.md` pointing at
   `sports_fixtures_schedule_wrong_schema_day_2026_04_14.md`, then archive it.** — **ALREADY DONE** by a separate,
   more recent interactive epic-scoped run (`a481f6357a`, slot-5·laptop, ~03:18 UTC+1 2026-08-19, "plan-reconcile
   sports_master — Track V authorization-gap safety fix, 1 archival, line-1 fixes, new infra gap issue, HTML report").
   That run archived the doc to `plans/archive/2026_08/issues/sports_fixtures_schedule_wrong_schema_day_2026_04_14.md`
   and repointed the closeout's own reference. Verified live — no further action.
2. **Work `sports_consolidated_native_ao_extract_2026_07_25_finalize.md` todos 1-3, then todo 4.** — **Substantially
   advanced this run** (todo 1: see Flips verified below; todo 2/3: see Contradictions/Coverage; todo 4 not yet safe —
   see Archive candidates).
3. **Filed docs from 2026-08-18**: `plan_reconciler_boot_pm_repo_path_points_at_root_clone_2026_08_18.md` —
   **ALREADY ARCHIVED** (resolved, confirmed live at `plans/archive/issues/`). This dispatch's own boot message
   confirms the fix holds — `$PM_REPO_PATH` correctly pointed at the slot-4 clone, not the root clone.
   `pipeline_e2e_check_declared_violations_sports_stale_exemption_2026_08_18.md` — still open, not re-triaged this
   pass (outside today's scope), left as-is.
4. **3 "Recommended but not executed" fold candidates** from 2026-08-18 — not re-actioned this pass (lower priority
   than the finalize-plan work below); still valid recommendations, re-listed in Coverage for the next pass.

## Flips verified

5 missed-flip todos in `sports_consolidated_closeout_2026_07_19.md` flipped `[ ]` → `[x]`, reconciling
`sports_consolidated_native_ao_extract_2026_07_25.md`'s already-DONE work back into the hub
(`sports_consolidated_native_ao_extract_2026_07_25_finalize.md` todo 1) — commit `e6e455f6c2`. **Important
methodology note**: the extract plan's own `Source: sports_consolidated_closeout_2026_07_19.md:<line>` citations have
DRIFTED and no longer point at matching content (the closeout doc has been trimmed/restructured multiple times since
those citations were written) — every match below was found by CONTENT/topic search against the closeout's own
17-then-12 open checkboxes, not by trusting the stale line numbers. This citation-drift is itself worth a future
pass's attention (not fixed here — see Coverage).

1. **Track S — Finding C correction** (cutover runbook's canonical-is-a-superset premise) — `unified-trading-pm@af8355cac`,
   verified reachable on `origin/live-defi-rollout` via `git merge-base --is-ancestor`.
2. **Track S — `sports_reference_v2/by_date/` post-floor cull** (16 day-dirs, 2024-12-24..2026-04-20) —
   `deployment-service@1b63863`, verified reachable. **Also caught a duplicate-dispatch**: `sports_satellite_ao_dispatch_batch16_2026_08_17.md`
   re-drafted this exact population as unclaimed work on 2026-08-17, 13 days after it shipped — struck in the same
   commit (see Contradictions #1).
3. **Track V — catalogue re-roll** (`build_instrument_catalogue.py --asset-group sports --since 2019-01-01`) — HARD
   evidence is GCS generation state (`instruments-store-sports-prd` gen `1785892158728886`, idempotent re-roll, no
   code commit to verify), not a git sha — accepted per the "manifest/runtime state showing completion" evidence
   class; not independently re-probed against live GCS this pass (would be a NEW measurement, out of scope for a
   bookkeeping reconciliation — flagged, not fabricated).
4. **Track V — catalogue player grain upgrade** (`entity=injuries`→`entity=fixture_lineups`) — cited sha `f858edb2`
   does **NOT** resolve as an ancestor of `origin/live-defi-rollout` (checked, failed) — the corpus's known
   squash-merge SHA-orphaning trap (per the 2026-08-18 report's own experience). **Verified instead by direct content
   read**: `SPORTS_PLAYER_SOURCE_ENTITY = "fixture_lineups"` is live at
   `instruments-service/scripts/build_instrument_catalogue.py:238` — confirms the claim independent of the
   unresolvable sha.
5. **Track V — launcher-used determination** (serial vs. parallel features backfill launcher) — audit conclusion
   (neither launcher's VM logs/`LAUNCH_PARAMS.json` exist), not a code change; accepted as HARD evidence (manifest/log
   state), same class as item 3.

**Line-cap discipline**: `sports_consolidated_closeout_2026_07_19.md` was at exactly 1000/1000 lines (hard cap)
before this pass. Flipping the 5 checkboxes (replacing verbose "Done when:" trailers with concise "DONE — citation"
text) grew it to 1002L — **over cap**. Trimmed the 3 newest additions (Track V trio) to bring it back to 998L,
re-verified via `check_line_caps.sh` before committing. See Doc-drift below for a related tooling finding this
surfaced.

## Contradictions

**Fixed this run** (commit `e6e455f6c2`):

1. **P1 (duplicate-dispatch prevention)** — `sports_satellite_ao_dispatch_batch16_2026_08_17.md`'s
   "snapshot-then-cull the 16 remaining post-floor day dirs" todo duplicates work already shipped 2026-08-04
   (`deployment-service@1b63863`) — the batch was drafted 13 days after the fact without checking
   `sports_consolidated_native_ao_extract_2026_07_25.md`'s already-DONE todo for the same population. Struck with a
   clear note (not silently deleted), matching the 2026-08-18 run's precedent for this exact failure class.

## Doc-drift

**Not auto-applied — routed** (tooling bug, outside `plans/**`, not this skill's write scope):

- **`scripts/plan-hygiene/check_line_caps.sh`'s "whitespace-only repair" exemption appears broken.** When this run's
  edit pushed `sports_consolidated_closeout_2026_07_19.md` to 1002L (2 over the hard cap), the script printed
  `SOFT ... 1002L ... (over cap pre-existing; allowed — whitespace-only repair, git diff -w empty, operator ruling
  2026-08-15)` and exited 0 (pass). **Independently verified this claim was FALSE for this specific diff**:
  `git diff -w -- <file>` was NOT empty (75 lines of non-whitespace diff, `--stat` showed 29 insertions/27 deletions).
  The script granted an exemption that does not hold under direct measurement — a real gap in a HARD gate (the
  2026-07-24 ruling states line caps have "no exceptions"). Did not rely on the exemption; trimmed the edit back
  under cap instead and did not investigate/fix the script itself (outside `plans/**`, and root-causing a bash
  line-counting bug is genuinely new scoped work, not a same-file mechanical fix this pass should improvise — same
  reasoning the 2026-08-19 `check_line_caps.sh` full-corpus-glob-gap issue doc used for a sibling bug in the same
  script). **Filed below.**
- **Extract-plan citation drift** (noted under Flips verified): `sports_consolidated_native_ao_extract_2026_07_25.md`'s
  `Source: sports_consolidated_closeout_2026_07_19.md:<line>` citations no longer resolve to matching content for at
  least the 5 items reconciled this run (spot-checked; not exhaustively re-verified for all 33 todos — out of this
  pass's time budget). Not auto-corrected (would require re-deriving all 33 citations, itself a bounded but
  non-trivial follow-up); flagged as a real, if minor, doc-quality gap.

## Hygiene fixes

None beyond what's captured above. Corpus-wide mechanical hygiene (frontmatter, todo-format, `depends_on` DAG,
reference-paths) was green for the sports tranche per the Phase-0 `run_hygiene_sweep.sh --ci --no-regen` pass — the
only hard failure was the pre-existing, corpus-wide `assigned_vm:NA` ratchet (owned by `/na-eligibility-audit`, not
this tranche specifically).

## Codex corrections applied (mechanical, evidence-cited)

None — no finding this run met the narrow mechanical carve-out bar.

## Filed

1. **`check_line_caps_sh_whitespace_only_exemption_false_positive_2026_08_19.md`** (P2) — the `check_line_caps.sh`
   bug described under Doc-drift above (see Progress Log for filing confirmation).

## Archive candidates (operator review)

- **`sports_consolidated_native_ao_extract_2026_07_25.md`** — 33/33 todos verified `[x]` (confirmed both in the
  2026-08-18 run and independently re-confirmed this run: `grep -c` shows 0 open / 33 done). NOT archived this pass —
  its finalize plan's todo 1 (reconcile into the hub) is only partially complete (5 of an estimated ~10-15 genuinely
  outstanding reconciliation items found and flipped; several other closeout-doc open items were investigated and
  found to be either genuinely separate scope or already covered by other satellite extractions — see Coverage).
  Finalize todo 4 (archive the extract plan) explicitly must run LAST, after todos 1-3 — not yet safe.
- **This doc's own predecessor** (`plan_reconciler_findings_sports_2026_08_18.md`) — NOT archived; it still carries
  genuinely-open recommendations (the 3 fold candidates, noted above) not yet executed by any pass. Leaving it active
  per its own "next pass" framing until those are resolved or explicitly superseded.

## Refuted (dropped by verify)

None this run.

## Coverage (hunters / batches / docs)

- **Phase -1**: reconciled the 2026-08-18 findings doc's 2 filed issues (1 confirmed archived/resolved, 1 confirmed
  still-open-and-out-of-scope) and its "next pass" action items (1 confirmed already done by a concurrent interactive
  run, 1 substantially advanced this run).
- **Finalize-plan execution** (`sports_consolidated_native_ao_extract_2026_07_25_finalize.md`): read both the extract
  plan (1001L) and the closeout hub (998-1002L) in full — no hunter fan-out used for this sub-task (26-candidate count
  is within this orchestrator's own inline-verification bar per the skill's Calibration section; sonnet-5/effort-max).
  Of the closeout's 17 open checkboxes pre-run, 5 were confirmed DONE-but-unflipped and fixed; 1 duplicate-dispatch
  caught; the remaining ~11 were checked against the extract's 33 todos by topic and found to be either (a) genuinely
  separate/unrelated scope (7 items: legacy `entity=fixtures/` write path, phantom `league_id=soccer_*` prune, honest-
  coverage atom regrade, CAS safety mechanism design, CF-8 maintenance window, `sports_p2_history_apifootball`
  residual work + its tracking pointer), (b) already extracted to an owning satellite/gated plan and appropriately
  left there rather than flipped here (Track H's registry-aware denominator → `sports_track_h_denominator_gated_2026_07_28.md`;
  Track V's league_id DELETE → `sports_venue_vocab_and_league_id_delete_ao_dispatch_2026_08_16.md`, actively executing
  today per a same-day operator commit), or (c) too entangled with a live, separately-tracked contradiction to safely
  touch this pass (the venue-vocabulary cleanup item at line 532, which carries its own `STALE 2026-08-14` pointer to
  a footystats-mislabel contradiction doc — deferred, not investigated this run).
- **This run did NOT fan out the full corpus-wide hunter sweep (Phase 1/STEP 3)** described in the skill for the
  remaining ~95 non-grace sports-tranche docs outside the finalize-plan chain — time/turn budget this run went
  primarily into the finalize-plan reconciliation above, which was both the highest-confidence, best-evidenced,
  most-overdue work (explicitly requested by the prior run) and touches the tranche's own hub document. **This is a
  real coverage gap, named honestly**: the broader tranche (satellite batches, issue docs, non-`sports_master`-epic
  docs tagged into this tranche) was not independently hunted for NEW contradictions/missed-flips this pass. Recommend
  the next sports-tranche dispatch run the standard Phase 1 fan-out over the full non-grace corpus.

## Plans not reached

The ~95 non-grace sports-tranche docs outside the `sports_consolidated_closeout`/`sports_consolidated_native_ao_extract`/
`_finalize` chain and `sports_satellite_ao_dispatch_batch16` were not read this pass. See Coverage above.

## Progress Log

- **2026-08-19T18:40Z (plan_reconciler, dispatch agt-07473e, slot 4)**: Phase -1 + finalize-plan todo-1 reconciliation
  complete. 5 flips + 1 duplicate-dispatch strike landed, commit `e6e455f6c2`, verified on `origin/live-defi-rollout`.
  Proceeding to finalize-plan todos 2-3, then the corpus-wide Phase 1 fan-out for remaining coverage.
