---
doc_type: issue
title: Sports-scoped /plan-reconcile + /docs-reconcile findings (2026-07-23 run) — 33 confirmed, unapplied
summary: Two sports-scoped audit workflows (plan-reconcile over 16 root plans/39 issue docs/1 epic; docs-reconcile over
  12 current + 1 superseded + 9 archived-pre-v2 sports codex docs + 6 epic/audit yaml) ran to completion and
  adversarially verified 33 findings (20 plan-corpus, 13 codex-corpus). NONE of the fixes below have been applied yet —
  this doc is the durable record so the findings survive past this session. Confirms the operator's working hypothesis
  that sports_consolidated_closeout_2026_07_19.md is canonical (sports_master_closeout_2026_07_21.md is an entry-point
  index only) — but finding #P5 shows master_closeout's own title/H1/`/autonomous` prompt still contradicts that framing.
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

- [ ] [DOC] P0. **P1 — league_id migration status contradiction**: closeout's Track V
      (`sports_consolidated_closeout_2026_07_19.md:1308`) says the 214,842-row historical manifest migration still needs
      scheduling; master_closeout (`sports_master_closeout_2026_07_21.md:197`) — citing the SAME source issue doc — logs
      its own league_id relocation COPY (275,136 objects, mtds@b2a49317) + manifest-swap
      `--apply-prod --confirm-prod-write` as EXECUTED 2026-07-22 (only human-only DELETE remains). Confirm: is this the
      SAME work (Track V should read COPY+SWAP done, DELETE pending) or genuinely separate NAME-FORM remapping (in which
      case both docs need explicit cross-references so nobody duplicates it)?
- [ ] [DOC] P0. **P5 — master_closeout self-contradicts on canonical status**: frontmatter/summary disclaim superseding
      the closeout (`entry_point_for:`), but the SAME file's title ("single source of truth", line 4), H1 heading (line
      74), and its `/autonomous` copy-paste prompt (line 597, labeled "copy this") all declare ITSELF sole SSOT and
      never name the closeout doc — a fresh `/autonomous` session following this file's own instructions would work from
      a ~7-item stale checklist and never touch the closeout's 96 open todos incl. its own self-described "THE single
      highest-priority item" (ODDS_API-dormancy investigation). Edit title/H1/prompt to match the entry-point framing;
      correct the closeout's decision-9 log line, which currently overstates this fix as complete.
- [ ] [DOC] P0. **Track F re-run instruction contradicts the 2020-06 floor wipe**: closeout Track F still has an open P0
      todo to re-run/regenerate `derived_features` for 2017+2018, but that exact population was already WIPED (not
      regenerated) 2026-07-21 under the data-floor ruling — which the SAME doc's Track V decision 14 already
      acknowledges. Strike/rewrite Track F to scope remaining work to post-floor residue only (2020-06-06-onward 2020
      cells + 2,821 fabricated cells in 2021-2026).
- [ ] [DOC] P0. **cross_ag_prediction_rows_bleed_into_sports_instruments_index is falsely marked resolved a 3rd time**
      (data-correctness, findings-triage HARD RULE — notify operator): doc claims "VERIFY PASSED / 0 remaining", but a
      fresh live prod read (this investigation, 2026-07-23) shows the exact same 11,727-row bleed is BACK. Do NOT flip
      checkboxes. Needs RE-TRIAGE round 3: confirm whether the consolidator is re-merging a stale per-VM shard carrying
      pre-remediation rows; purge/refresh that shard or re-run REMOVE and verify across a full consolidation cycle
      before re-closing.

### P1 — auto-fixable (mechanical, evidence-backed; not yet applied)

- [ ] [DOC] P1. Add a dated correction note to master_closeout's K1/K2 sections pointing at the closeout's Track C
      revert decision (2026-07-23) — master_closeout still says K1/K2 "ALL now complete", closeout says "SUPERSEDED,
      MUST BE REVERTED".
- [ ] [DOC] P1. Re-run `scripts/plans/populate_epic_bodies_2026_05_21.py` against `plans/epics/sports_master.md` — it
      still lists 3 archived fold-in plans as `status: active` and understates the closeout's estimate by ~4x (9.6 vs
      36.8 cal AI-days).
- [ ] [DOC] P2. Fix closeout's decision-4 count ("6 orphan plans") to "5" (line 1298) to match the correct count
      elsewhere in the same doc (line 565) — cosmetic, self-contained.
- [ ] [DOC] P2. Correct `sports_golden_window_attempted_failed_remediation_2026_06_24.md`'s 2026-07-23 RE-TRIAGE, which
      calls `sports_pipeline_to_100pct_golden_window_first_2026_06_27.md` "still active" — it was archived the same day
      under the closeout's Track X fold-in.
- [ ] [DOC] P2. Flip `sports_odds_ownership_registry_split_brain_and_bogus_api_football_denominator_2026_07_15.md` line
      323's DEFERRED PURGE checkbox to done — the purge already ran via `sports_legacy_bucket_cutover_2026_07_16.md`
      T3.1 (2026-07-16T13:09Z, 123,149 rows), independently re-verified 0 rows remain in prod. Also flip the adjacent
      line-319 VERIFY todo (T3.2 confirms it). Also correct closeout line 802-803, which still calls this open. Note: do
      NOT cite the MTDS@e9d9dec0 wipe as the completing evidence — it targeted a different bucket entirely.

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
- [ ] [DOC] P2. Fix closeout Track H's misattribution of the rejected 180-240s staleness-budget value to
      `sports_manifest_read_staleness_budget_missing_2026_07_15.md` (that doc actually recommends 1800s, matching the
      closeout's own earlier correct attribution at line ~748). Citation-accuracy fix only.
- [ ] [DOC] P1. `sports_master_closeout_2026_07_21.md`'s `/autonomous` prompt (step 4, line 638) still tells a fresh
      agent to reuse `rebuild_sports_manifest.py::_clean_stale_league_entries` for the pending manifest-swap+delete —
      the SAME doc's fifth-wave Progress Log proves this script is broken (wrong partition-key pattern) and would delete
      the entire 1.78M+-row sports MTDS manifest if run in write mode. Repoint to the verified
      `manifest_swap_2026_07_22.py` tool (already documented elsewhere in the same file). Mechanical, no judgment needed
      — correct tool name already exists in-doc.
- [ ] [DOC] P1. `sports_live_writer_instrument_type_casing_never_fixed_2026_07_22.md` is `status: resolved` with a
      same-day RE-TRIAGE declaring K1/K2 UPPER-casing correct — but the closeout's later same-day reconciliation
      reverses that (LOWER-case canonical, K1/K2 "MUST BE REVERTED", not yet executed). Add a correction banner; the
      closeout's revert decision is later same-day and evidenced.
- [ ] [DOC] P1. **Venue-vocabulary scope** (needs operator ruling) — `/codex/01-domain/sports-instruments.md`
      (last_reviewed 2026-05-22) declares only 3 active sports venues, but current measurements show ~15+
      individually-registered bookmaker venues live in prod. Ambiguous whether these are legitimate sub-identities
      within the ODDS_API feed or genuine doc staleness — this doc was NOT included in the closeout's 2026-07-23 6-doc
      codex-alignment pass that fixed the identical bug class in sibling docs, and isn't cited in either plan's
      Codex-SSOTs list.

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

- [ ] [DOC] P1. Casing doctrine has NO single current-truth doc: `sports-data-source-coverage-matrix.md` (stale,
      predates reversal) says UPPER via K0-DECISION(b); `sports-batch-live.md` says the 2026-07-23 reversal covers ALL
      sports data_types but points to `sports-data-types-catalog.md` for "most current" — which is scoped only to its 9
      MTDS/MDPS data_types, never mentioning FIXTURES/INJURIES/TEAMS/STANDINGS. Rule whether the "ALL types" reversal
      includes instruments-service-side reference data_types, then fix whichever doc is wrong.
- [ ] [DOC] P1. `sports-epic.yaml` still lists eliminated `unified-sports-execution-interface` (merged into
      execution-service 2026-03-26) as a `required_repos` gate — permanently unsatisfiable. **Not sports-specific**:
      `defi-epic.yaml`/`cefi-epic.yaml`/`tradfi-epic.yaml` share the identical pattern for
      `unified-defi-execution-interface` (same elimination date). Recommend a workspace-wide PM ruling (scrub vs.
      annotate-satisfied), not a sports-only point fix.

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
- [ ] [DOC] P1. `sports-data-source-coverage-matrix.md`'s casing banner (lines 41-44) still points to the closeout doc
      for "current truth" without noting the plan's headline decision has since reversed twice more (2026-07-22 partial,
      2026-07-23 full reversal to lower-case). This exact gap is already an open Track D P2 todo inside the closeout
      itself — this finding confirms that todo is real and unaddressed.
- [ ] [DOC] P2. `sports-instruments.md` has 3 dead reference links (lines 27, 472-474): a nonexistent sibling repo
      (`sports-betting-services/docs/INSTRUMENT_KEY.md`) and 2 nonexistent codex paths — one of which
      (`sports-data-sources.md`) has a real target (`sports-data-source-coverage-matrix.md`) the SAME doc already links
      correctly elsewhere.

### P2 — needs a substantive fix, no operator authority question

- [ ] [DOC] P2. `sports-data-types-catalog.md` cites 2 `EmptyConfirmedReason` enum values that don't exist in UAC:
      `EXPECTED_SOURCE_COVERAGE_START` (typo of `EXPECTED_PRE_SOURCE_COVERAGE_START` — mechanical fix) and
      `EXPECTED_FIXTURE_STARTED_EARLY` (needs a decision: mint a real member, or map onto an existing one — then update
      `sports-batch-live.md`'s closed-set §4 list to match).
- [ ] [DOC] P2. `sports-data-source-coverage-matrix.md`'s worked Transfermarkt coverage example (2014-2026, verified
      2026-07-08) predates the 2020-06-06 floor ruling (2026-07-21) and isn't reconciled to it. Re-run the verification
      against the post-floor manifest, or banner the example as historical-only.

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
