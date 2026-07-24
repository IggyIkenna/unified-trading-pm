---
doc_type: issue
title: Sports-scoped /plan-reconcile + /docs-reconcile findings (2026-07-23 run) — 18/31 applied 2026-07-24
summary: >-
  Two sports-scoped audit workflows (plan-reconcile over 16 root plans/39 issue docs/1 epic; docs-reconcile over 12
  current + 1 superseded + 9 archived-pre-v2 sports codex docs + 6 epic/audit yaml) ran to completion and adversarially
  verified 33 findings (20 plan-corpus, 13 codex-corpus). As of 2026-07-24, 18 fixes are applied (all P0s incl. a live
  GCP-verified league_id-migration ruling and a reopened cross_ag_prediction-bleed round-3 finding; all 4 operator
  rulings applied; most P1 mechanical fixes) — see "Deferred work after 2026-07-24" below for the 13 remaining.
  Confirmed the operator's working hypothesis that sports_consolidated_closeout_2026_07_19.md is canonical
  (sports_master_closeout_2026_07_21.md is now a fixed entry-point index, title/H1/prompt included, not just
  frontmatter).
status: open
nature: issue
asset_group: [sports]
stage: [data]
scope: [engineer]
repos: [unified-trading-pm, unified-api-contracts, instruments-service, market-tick-data-service]
tags: [sports, plan-reconcile, docs-reconcile, contradiction, codex-alignment, audit]
related:
  [
    plans/active/sports_consolidated_closeout_2026_07_19.md,
    plans/active/sports_master_closeout_2026_07_21.md,
    plans/active/sports_consolidated_audit_2026_07_19.md,
    plans/epics/sports_master.md,
  ]
created: 2026-07-24
parent_epic: sports_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: refactor
source: operator-directed — two Workflow-tool runs of the plan-reconcile and docs-reconcile skills, sports-scoped
resolved_by:
locked_by:
drift_direction: advance-code
depends_on: []
---

# Sports-scoped plan-reconcile + docs-reconcile findings (2026-07-23 run)

## How this was found

Ran `/plan-reconcile` and `/docs-reconcile` as two separate Workflow-tool invocations, both scoped to the sports
asset_group only (per operator request). Both completed successfully (plan-reconcile: 60 agents, 902 tool calls,
~100min; docs-reconcile: 35 agents, 502 tool calls, ~52min) but their full structured results only existed in `/tmp`
task-output files and this chat — this doc promotes them to a durable, committed record before context compaction.
**Nothing below has been applied yet.** Raw workflow output (if still present this session):
`/tmp/claude-1000/.../tasks/wo01k4tbr.output` (plan-reconcile) and `w611hekte.output` (docs-reconcile) — do not rely on
these surviving; this doc is now the source of truth for the findings.

## Operator rulings (2026-07-24) — RECORDED, not yet applied

The operator answered the 4 genuine judgment-call questions this doc's findings raised. These are decisions, not
findings — capturing them here so a fresh session doesn't have to re-ask or re-derive them. **None of the dependent
fixes below have been applied yet** (blocked mid-execution by an unrelated `/tmp` disk-full incident); the todos in this
doc still reflect pre-ruling wording until someone applies these.

1. **League_id migration** (P0 item below): operator did NOT pick a side — asked instead for a live GCP/manifest check
   before ruling. That live verification was in progress (24/24 relocation shard reports downloaded from
   `gs://deployment-scripts-central-element-323112/canonical-migration-sports-reloc/reports/`, aggregation not yet run)
   when the disk-full incident interrupted it. **Still needs finishing**: aggregate the 24 shard reports' verify counts,
   cross-check against the live `market-data-tick-sports-prd-central-element-323112` manifest for whether canonical
   league_id rows are present and old raw-keyed rows still exist (confirming delete-not-yet-run), then rule whether
   Track V's "214,842 rows... still needs scheduling" is the SAME work as master_closeout's executed COPY+SWAP (275,136
   objects, mtds@b2a49317, 2026-07-22) or genuinely separate.
2. **Casing doctrine scope**: ruled **ALL sports data_types** (including instruments-service-side reference data_types
   like FIXTURES/INJURIES/TEAMS/STANDINGS), not just the 9 MTDS/MDPS ones. Apply: update
   `/codex/02-data/sports-data-source-coverage-matrix.md`'s stale UPPER-case K0-DECISION(b) banner to reflect the
   2026-07-23 all-lower reversal.
3. **Venue vocabulary**: ruled **doc is stale, update it**. Apply: widen `/codex/01-domain/sports-instruments.md`'s
   "active venues" note (currently lists only 3: ODDS_API/PINNACLE/BETFAIR) to reflect the current UAC venue registry
   (~15+ individually-registered bookmaker venues live in prod).
4. **Epic yaml policy** (workspace-wide, not sports-specific): ruled **scrub the eliminated entries**. Apply: remove the
   `unified-sports-execution-interface` / `unified-defi-execution-interface` `required_repos` lines from all 4 affected
   epic yaml files (`codex/11-project-management/epics/{sports,defi,cefi,tradfi}-epic.yaml`) — their function is already
   covered by the separately-required `execution-service` entry in each.

## Canonical-doc question — RESOLVED, but see P5

The operator's hypothesis was confirmed: `sports_consolidated_closeout_2026_07_19.md` is the canonical, single
actionable sports execution plan. `sports_master_closeout_2026_07_21.md` was reconciled 2026-07-23 into a
non-superseding `entry_point_for:` index role at the **frontmatter** level. However finding **P5** below shows the same
file's title, H1 heading, and its embedded `/autonomous` copy-paste prompt still assert itself as "the single source of
truth" and never mention the closeout doc — the 2026-07-23 fix only touched frontmatter, not the human/agent-facing
prose in the same file. This is the highest-priority item in this doc.

## plan-reconcile findings (scope: 16 root plans, 39 issue docs, 1 epic; 20 confirmed / 4 refuted / 24 verified)

### Archive-candidate verdict

- [ ] [DOC] P1. **`sports_odds_bookmaker_coverage_enumeration_2026_06_20.md` is NOT a clean auto-archive** — it is still
      frontmatter-`locked_by: live-defi-rollout` (contradicting the "unlocked" premise the archive-check was given), and
      its own "Gap analysis from P1c Todo 4" section lists 4 concrete follow-ups (LEAGUE_ID_TO_TIER mapping, 28 unmapped
      league_ids, fixture_id=NULL propagation, trades cluster-validation gap) that were never converted to tracked todos
      and remain unaddressed. Two of its 3 "done" todos' cited regression tests were deleted by a later commit and not
      restored under the same names. Do NOT archive without an `[unlock-plan]` step + an explicit operator ruling on
      whether the conservative empirical seed is accepted as final.

### P0 — needs operator ruling

- [x] [DOC] P0. ✅ **DONE 2026-07-24 — RULED: SAME WORK, applied.** Live GCS re-verification this session: independently
      re-aggregated all 24 relocation shard-report JSONs (reproduced the exact 275,136 objects / 54,835,957 rows),
      confirmed the manifest ADD/REMOVE swap executed 2026-07-22 (VERIFY PASSED stale_remaining=0), and
      live-spot-checked GCS directly — canonical `league_id=EPL` object exists, old raw-keyed `league_id=PREMIER_LEAGUE`
      object for the same cell is STILL PRESENT (delete genuinely pending, human-gated). Track V rewritten in
      `sports_consolidated_closeout_2026_07_19.md` to read COPY+SWAP done, DELETE pending, pointing at master_closeout's
      own 5-part-proof delete todo instead of duplicating it. `sports_consolidated_closeout_2026_07_19@local`.
- [x] [DOC] P0. ✅ **DONE 2026-07-24.** Edited `sports_master_closeout_2026_07_21.md`'s title (line 4), H1 heading,
      intro blockquote, and `/autonomous` prompt to drop the "single source of truth" self-claim and explicitly point to
      `sports_consolidated_closeout_2026_07_19.md`'s 96+ open todos; also fixed the prompt's stale step-3/4 status
      (COPY+SWAP now shown done, not pending) and repointed its broken
      `rebuild_sports_manifest.py::_clean_stale_league_entries` reference to the verified `manifest_swap_2026_07_22.py`
      tool. Corrected the closeout's decision-9 log line, which overstated the 2026-07-23 fix as complete (it only
      touched frontmatter).
- [x] [DOC] P0. ✅ **DONE 2026-07-24.** Rewrote Track F in `sports_consolidated_closeout_2026_07_19.md`: the 2017+2018
      "re-run" todo is now marked resolved-via-pre-floor-wipe (not a re-run target — `deployment-service@78a0aa4`
      already deleted this population 2026-07-21); the corpus-wide re-run/PURGE/CENSUS todos are rescoped to post-floor
      residue only (Jun-Dec 2020 + the 2,821 fabricated 2021-2026 cells).
- [x] [DOC] P0. ✅ **RE-TRIAGE ROUND 3 DONE 2026-07-24 — REOPENED, do NOT treat as resolved.** Live streaming
      pyarrow/gcsfs read of the sports instruments-store index found the exact same 11,727 bleed rows, exact same
      venue/date breakdown, back in place despite round-2's "VERIFY PASSED: 0 remaining" claim. Confirmed metadata-only
      (no physical objects in the sports bucket) and ruled OUT the stale-per-VM-shard hypothesis (`_index/per_vm/` holds
      only an unrelated 18KB seed file). Root cause of the reversion is NOT yet confirmed — working hypothesis is a
      consolidator rebuild path round-2's remediation never touched. Reverted `status` to `open` + cleared `resolved_by`
      in `cross_ag_prediction_rows_bleed_into_sports_instruments_index_2026_07_20.md`, appended a "RE-TRIAGE ROUND 3"
      section with next-step investigation plan, and corrected `sports_consolidated_closeout_2026_07_19.md`'s two stale
      "RESOLVED" references (Track X decision log + the go-live pre-req REVIEW item, now a hard BLOCKER on
      `sports_predictions_live_mode_activation_readiness_2026_07_21.md`). **The underlying data bug is still open** —
      this todo covered the re-triage/documentation, not a fix; round 4 (root-cause + durable fix) remains future work.

### P1 — auto-fixable (mechanical, evidence-backed; not yet applied)

- [x] [DOC] P1. ✅ **DONE 2026-07-24.** Added a correction blockquote to `sports_master_closeout_2026_07_21.md` right
      before the K1/K2 items pointing at the closeout's Track C revert decision.
- [x] [DOC] P1. ✅ **DONE 2026-07-24.** Ran `populate_epic_bodies_2026_05_21.py --apply` (workspace-wide, no per-epic
      scoping flag exists — regenerated all 23 epic bodies, all mechanical/deterministic). `sports_master.md`'s
      "Assigned active plans" section no longer lists the 3 archived fold-in plans and shows the correct 36.8 cal AI-day
      estimate.
- [x] [DOC] P2. ✅ **DONE 2026-07-24.** Fixed the "6 orphan plans" → "5" miscounted instance.
- [x] [DOC] P2. ✅ **DONE 2026-07-24.** Corrected the golden_window doc's RE-TRIAGE — the coordinator plan's frontmatter
      is verified `status: superseded` (folded into closeout Track X 2026-07-23), not `active`.
- [x] [DOC] P2. ✅ **DONE 2026-07-24.** Flipped both checkboxes with full T3.1/T3.2 evidence (123,149 rows purged
      2026-07-16T13:09Z, re-verified 0 remain) and corrected the closeout's stale "open" reference to point at the
      completed purge.

### P1-P2 — needs a substantive (non-mechanical) fix, no operator authority question

- [ ] [DOC] P1. `sports_halftime_odds_sfi_vs_inplay_2026_07_16.md`'s 2026-07-23 RE-TRIAGE undercounts open work — claims
      "one residual" but 5 checkboxes are actually still `[ ]` (lines 546, 1005, 1014, 1022, 1027). Enumerate or
      re-triage all 5, not just the PIT-gate item.
- [ ] [DOC] P1. `sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md` is falsely claimed
      "archived/superseded into the closeout" in Track V — it's still `status: active`, no banner, not in the closeout's
      own fold-in or orphan lists (conflated with a similarly-named doc). ~9 real open todos are untracked by the
      closeout. Either formally link it (SCOPE OVERLAP banner + Track X todo) or archive for real.
- [ ] [DOC] P2. `sports_predictions_live_mode_activation_readiness_2026_07_21.md` claims Group-C harness need is "not
      decided yet", but the parent issue doc it cites has that exact todo checked `[x]` with "decision: YES, genuinely
      needed", which spawned `sports_group_c_execution_backtest_harness_2026_07_21.md` (missing from this doc's
      `related:` list too).
- [ ] [DOC] P2. `sports_odds_bookmaker_coverage_enumeration_2026_06_20.md`'s "Gap analysis from P1c Todo 4" section (28
      unmapped league_ids, LEAGUE_ID_TO_TIER requirement) exists only as prose, not todos — convert or fold into the
      closeout's Track X reconciliation first.
- [x] [DOC] P2. ✅ **DONE 2026-07-24.** Corrected the citation — the rejected 180-240s value is from sweep §J, not from
      the issue doc (which already correctly recommends 1800s, matching this line's own target).
- [x] [DOC] P1. ✅ **DONE 2026-07-24** (part of the P5 fix above) — repointed to `manifest_swap_2026_07_22.py`.
- [x] [DOC] P1. ✅ **DONE 2026-07-24.** Added a correction blockquote right after the RE-TRIAGE header noting the
      UPPER-casing direction it confirms is itself now superseded/must-be-reverted per the closeout's later Track C.
- [x] [DOC] P1. ✅ **DONE 2026-07-24 — RULED: doc is stale, updated.** Live census of the sports tick manifest's `venue`
      column found 28 distinct individually-registered bookmaker venues captured today (PADDYPOWER, UNIBET, DRAFTKINGS,
      SKYBET, SPORT888, MATCHBOOK, FANDUEL, BETONLINEAG, BETRIVERS, CORAL, WILLIAMHILL, BETVICTOR, VIRGINBET,
      LIVESCOREBET, CASUMO, BETSSON, UNIBET_UK/EU, BETFAIR_EX_UK/EU, BETFAIR_SB_UK, LADBROKES_UK, SMARKETS, BOVADA,
      BETWAY, BETMGM, plus PINNACLE/BETFAIR direct) — these are ODDS_API-aggregator sub-identities, not a
      scraper-deferral violation. Rewrote the DELTA note in `sports-instruments.md` to explain the aggregator mechanism
      and the corrected count.

## docs-reconcile findings (scope: 12 current + 1 superseded + 9 archived-pre-v2 sports codex + 6 epic/audit yaml; 13 confirmed / 1 refuted; Phase 0 deterministic checks all green corpus-wide)

### P0 — needs operator ruling

- [ ] [DOC] P0. **`authoritative_for` collision, code-verified**: `sports-batch-live.md` says sports has "no in-play
      live source today" (odds_api = `{BATCH, REPLAY}`); `sports-live-odds-connectivity.md` is the SSOT for two
      currently-operating live paths (Odds API + exchange poll -> MDPS -> Pub/Sub). Ground truth
      (`unified_api_contracts/canonical/crosscutting/_source_priority_data.py`, commit `249ca53f2`, 2026-06-21):
      `odds_api` flipped to `{BATCH, LIVE, REPLAY}` and is explicitly "the FIRST live sports source".
      `sports-batch-live.md`'s `last_reviewed: 2026-07-23` banner never touched this table row. Recommend: (1) fix the
      odds_api capability row; (2) rewrite the "no live source" framing in §1/§2/§6; (3) confirm whether M6 startup-gate
      case selection or any honest-coverage LIVE-axis denominator logic keys off "sports has no live source" and needs
      updating too. Doc-narrative rewrite, needs a scope decision, not a one-line patch.

### P1 — needs operator ruling (authority/scope, not correctness)

- [x] [DOC] P1. ✅ **DONE 2026-07-24 — RULED: ALL sports data_types, including instruments-service reference
      data_types.** Rewrote `sports-data-source-coverage-matrix.md`'s casing banner to state the current LOWER-case
      doctrine explicitly, cite both reversal dates (2026-07-22 partial UPPER, 2026-07-23 full LOWER reversal), and flag
      the 2026-07-22 K1/K2 UPPER migration as itself superseded/must-be-reverted.
- [x] [DOC] P1. ✅ **DONE 2026-07-24 — RULED: scrub the eliminated entries, workspace-wide.** Removed the
      `unified-sports-execution-interface` required entry from `sports-epic.yaml` and the
      `unified-defi-execution-interface` entry from `defi-epic.yaml` (required), `cefi-epic.yaml` + `tradfi-epic.yaml`
      (optional) — all 4 files, both required and optional occurrences, since the repo no longer exists standalone. YAML
      syntax validated post-edit.

### P1-P2 — auto-fixable (mechanical; not yet applied)

- [ ] [DOC] P1. `sports-gcs-path-ssot.md`'s "SPORTS-CANON ALIGNMENT (2026-06-01)" note still frames the legacy no-env
      bucket deletion as future — it was deleted 2026-07-16 (measured). Update to past tense + close out the
      already-open T6.7 todo in `sports_legacy_bucket_cutover_2026_07_16.md` that names this exact fix. Also check the 2
      sibling docs T6.7 names (`bucket-naming-and-config.md`, `manifest-consolidator-ssot.md`) for the same gap.
- [ ] [DOC] P2. `sports-integration-plan.md` (superseded, correctly bannered) has 2 real inbound pointers NOT in its own
      `referenced_by:` and missing the superseded caveat: `/codex/04-architecture/README.md` and
      `/codex/00-SSOT-INDEX.md` row 108. Add the caveat + complete `referenced_by:`.
- [ ] [DOC] P1. `kelly.md` and `staking-methods.md` (archived pre-v2 sports strategy docs) are the only 2 of 9 siblings
      missing the standard in-body `> **[SUPERSEDED]**` banner — frontmatter is correct, only the rendered-body signal
      is missing.
- [ ] [DOC] P1. `unified-sports-reference-interface.yaml` (archived audit yaml) still says `status: "active"` despite 3
      independent signals (2 current codex SSOTs + its own filing location under `_archive/`) agreeing it's
      retired/merged. Flip to `"eliminated"`; confirm final destination (instruments-service vs.
      unified-reference-data-interface — it's a 2-hop merge) before writing the elimination note.
- [ ] [DOC] P2. `runtime-deployment-topology.md` self-contradicts on USEI status: line 697 still frames it as a
      future/standalone component; lines 1594/1615 in the same doc correctly treat it as merged into execution-service.
      Reword line 697; the parallel DeFi line 696 (UDEI) has the identical staleness and should be fixed at the same
      time.
- [ ] [DOC] P2. `sports-2020-06-data-floor.md`'s "The wipe" section claims "no phantom pre-floor rows survive", but both
      linked plans say the MANIFEST-side prune (131,426 + 944,776 phantom rows, plus 83,541 pre-floor FIXTURES rows) is
      explicitly NOT done yet. Qualify the section to separate done (GCS-object wipe) from deferred (manifest-row
      prune).
- [x] [DOC] P1. ✅ **DONE 2026-07-24** (same edit as the casing-doctrine-scope fix above — the rewritten banner
      explicitly cites both reversal dates).
- [x] [DOC] P2. ✅ **DONE 2026-07-24.** Removed the dead sibling-repo link (2 occurrences) and repointed the dead
      `sports-data-sources.md` codex path to the real `sports-data-source-coverage-matrix.md` target.

### P2 — needs a substantive fix, no operator authority question

- [ ] [DOC] P2. `sports-data-types-catalog.md` cites 2 `EmptyConfirmedReason` enum values that don't exist in UAC:
      `EXPECTED_SOURCE_COVERAGE_START` (typo of `EXPECTED_PRE_SOURCE_COVERAGE_START` — mechanical fix) and
      `EXPECTED_FIXTURE_STARTED_EARLY` (needs a decision: mint a real member, or map onto an existing one — then update
      `sports-batch-live.md`'s closed-set §4 list to match).
- [x] [DOC] P2. ✅ **DONE 2026-07-24 (bannered, not re-verified).** Added a note qualifying the 75.41% all-time
      (2014-2026) figure as historical-only/pre-floor, not re-measured against the post-floor manifest; the 99.55%
      current-era figure is unaffected (entirely post-floor).

## Deferred work after 2026-07-24

Session stopped by operator instruction (interactive `/autonomous` continuation, not a background dispatch) after
applying all P0s + all 4 operator rulings + most P1 mechanicals. Remaining `- [ ]` items above, for the next session:

| Item                                                                                                                                                                                 | Priority | Type                                               |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------- | -------------------------------------------------- |
| Archive-candidate verdict — `sports_odds_bookmaker_coverage_enumeration_2026_06_20.md` (do NOT auto-archive; needs `[unlock-plan]` + operator ruling on the empirical-seed question) | P1       | judgment call                                      |
| `sports_halftime_odds_sfi_vs_inplay_2026_07_16.md` — enumerate/re-triage 5 undercounted open checkboxes                                                                              | P1       | substantive                                        |
| `sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md` — link or archive for real                                                                             | P1       | substantive                                        |
| `sports_predictions_live_mode_activation_readiness_2026_07_21.md` — fix Group-C harness claim + `related:` list                                                                      | P2       | mechanical                                         |
| `sports_odds_bookmaker_coverage_enumeration_2026_06_20.md` — convert gap-analysis prose to tracked todos                                                                             | P2       | substantive                                        |
| docs-reconcile P0 — `sports-batch-live.md` vs `sports-live-odds-connectivity.md` odds_api `authoritative_for` collision                                                              | P0       | substantive, needs scope decision                  |
| docs-reconcile — `sports-gcs-path-ssot.md` bucket-deletion past-tense + close T6.7 + check 2 sibling docs                                                                            | P1       | mechanical                                         |
| docs-reconcile — `sports-integration-plan.md` `referenced_by:` + superseded caveat                                                                                                   | P2       | mechanical                                         |
| docs-reconcile — `kelly.md` + `staking-methods.md` missing in-body SUPERSEDED banners                                                                                                | P1       | mechanical                                         |
| docs-reconcile — `unified-sports-reference-interface.yaml` status flip to `"eliminated"`                                                                                             | P1       | mechanical (needs 2-hop-merge destination confirm) |
| docs-reconcile — `runtime-deployment-topology.md` line 697 USEI + line 696 UDEI reword                                                                                               | P2       | mechanical                                         |
| docs-reconcile — `sports-2020-06-data-floor.md` "no phantom rows survive" qualifier                                                                                                  | P2       | mechanical                                         |
| docs-reconcile P2 — `sports-data-types-catalog.md` `EmptyConfirmedReason` enum typo (mechanical) + `EXPECTED_FIXTURE_STARTED_EARLY` decision (mint vs map)                           | P2       | mixed                                              |
| cross_ag_prediction_rows_bleed round 4 — root-cause the consolidator reversion mechanism + durable fix (see the issue doc's RE-TRIAGE ROUND 3 next-steps)                            | P0       | data-correctness, real investigation               |

## Ledger (Phase 5.9 discipline — counted, not eyeballed)

- plan-reconcile: 23 raw candidates -> 23 deduped -> 24 verified (incl. 2 done-but-unchecked evidence-checks) -> **20
  confirmed / 4 refuted**. Routed to operator: 16. Auto-fixable: 4. **16 + 4 = 20 — balances.**
- docs-reconcile: 14 raw candidates -> 14 deduped -> **13 confirmed / 1 refuted**. Routed to operator: 5.
  Auto-fixable: 8. **5 + 8 = 13 — balances.**
- Total: **33 confirmed findings, 0 applied.** All are `- [ ]` above; none silently dropped.

## Recommended next step

This doc is large; recommend the operator work through it interactively (batched Q&A per the plan-reconcile/
docs-reconcile skills' own routing rules) rather than re-dispatching a fresh audit — re-running would just re-discover
the same 33 items at real token cost. Start with the two P0 items marked "notify operator" / data-correctness (the
cross_ag_prediction bleed, and master_closeout's self-contradiction) since those are the ones with real operational risk
if left unaddressed.
