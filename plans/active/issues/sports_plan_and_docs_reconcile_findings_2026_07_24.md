---
doc_type: issue
title: Sports-scoped /plan-reconcile + /docs-reconcile findings (2026-07-23 run) — 31/31 applied 2026-07-24
summary: >-
  Two sports-scoped audit workflows (plan-reconcile over 16 root plans/39 issue docs/1 epic; docs-reconcile over 12
  current + 1 superseded + 9 archived-pre-v2 sports codex docs + 6 epic/audit yaml) ran to completion and adversarially
  verified 33 findings (20 plan-corpus, 13 codex-corpus; 31 distinct tracked checkbox items). As of 2026-07-24, ALL 31
  fixes are applied (every P0 incl. a live GCP-verified league_id-migration ruling; all 4 operator rulings; every P1/P2
  mechanical + substantive item, 8 of them via parallel sub-agents scoped to disjoint files). Confirmed the operator's
  working hypothesis that sports_consolidated_closeout_2026_07_19.md is canonical (sports_master_closeout_2026_07_21.md
  is now a fixed entry-point index, title/H1/prompt included, not just frontmatter). One genuine piece of future work
  survives this doc's own scope: cross_ag_prediction_rows_bleed's ROUND 4 root-cause + durable fix (tracked in that
  issue doc, not here — this is real data-correctness investigation, not a reconciliation fix).
status: resolved
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
resolved_by: 8 parallel sub-agents + direct session edits, 2026-07-24 (see per-item evidence below)
locked_by:
drift_direction: advance-code
depends_on: []
---

# Sports-scoped plan-reconcile + docs-reconcile findings (2026-07-23 run)

## How this was found

Ran `/plan-reconcile` and `/docs-reconcile` as two separate Workflow-tool invocations, both scoped to the sports
asset_group only (per operator request). Both completed successfully (plan-reconcile: 60 agents, 902 tool calls,
~100min; docs-reconcile: 35 agents, 502 tool calls, ~52min) but their full structured results only existed in `/tmp`
task-output files and this chat — this doc promotes them to a durable, committed record before context compaction. **All
findings below are now applied (2026-07-24) — see per-item evidence.** Raw workflow output (if still present this
session): `/tmp/claude-1000/.../tasks/wo01k4tbr.output` (plan-reconcile) and `w611hekte.output` (docs-reconcile) — do
not rely on these surviving; this doc is now the source of truth for the findings.

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

## Canonical-doc question — FULLY RESOLVED 2026-07-24 (P5 fixed)

The operator's hypothesis was confirmed: `sports_consolidated_closeout_2026_07_19.md` is the canonical, single
actionable sports execution plan. `sports_master_closeout_2026_07_21.md` was reconciled 2026-07-23 into a
non-superseding `entry_point_for:` index role at the frontmatter level, but finding **P5** below found the same file's
title, H1 heading, and its embedded `/autonomous` copy-paste prompt still asserted itself as "the single source of
truth" and never mentioned the closeout doc — the 2026-07-23 fix only touched frontmatter, not the human/agent-facing
prose in the same file. **P5 is now fixed (2026-07-24)**: title/H1/prompt all rewritten to the entry-point framing,
explicitly pointing at the closeout's 96+ open todos, with the prompt's stale operational status + broken script
reference also corrected in the same pass.

## plan-reconcile findings (scope: 16 root plans, 39 issue docs, 1 epic; 20 confirmed / 4 refuted / 24 verified)

### Archive-candidate verdict

- [x] [DOC] P1. ✅ **DONE 2026-07-24 — NOT archived (correct per this finding's own instruction).** Added a
      `🔒 NOT a clean auto-archive candidate` note near the top of the doc citing the `locked_by` contradiction. The 4
      gap-analysis follow-ups (LEAGUE_ID_TO_TIER mapping, 28 unmapped league_ids, fixture_id=NULL propagation, trades
      cluster-validation gap) are now tracked as 4 real `- [ ]` todos in a new "P1 — gap-analysis follow-ups" section.
      Confirmed via `git log` that 2 of the 3 "done" todos' cited regression tests genuinely were deleted
      (`instruments-service@6404abd6`, not restored under the same names when the ODDS path was restored) — documented
      as a blockquote, checkboxes deliberately left as-is (flipping them back to open is its own operator-level call,
      out of this finding's mechanical scope). `[unlock-plan]` + the empirical-seed archival ruling remain genuinely
      future operator work, correctly not attempted here.

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

- [x] [DOC] P1. ✅ **DONE 2026-07-24.** Re-derived the actual open-checkbox count (5, confirmed via `grep -n '- \[ \]'`,
      lines shifted by 1 from this finding's citation) and independently verified current reality for each against the
      live codebase/other plan docs before deciding: all 5 are genuinely still open (no shipped evidence found for any),
      so all 5 are now enumerated with a one-line reason each in the rewritten RE-TRIAGE section, replacing the "one
      residual" undercount. None were flipped closed — this was an accuracy fix, not a completion claim.
- [x] [DOC] P1. ✅ **DONE 2026-07-24 — linked, not archived.** Confirmed `status: active` with 11 genuinely-open todos
      (finding's "~9" was an approximation). Cross-linked both docs via `related:` frontmatter (bidirectional), added a
      top-of-doc banner correcting the false archived/superseded framing, and fixed the closeout's Track V bullet which
      had conflated this doc with a different, genuinely-archived `...apifootball...`-named doc. Added a new closeout
      todo tracking the satellite doc's un-duplicated open work (fold-in-vs-keep-satellite left as an explicit operator
      call, not decided here).
- [x] [DOC] P2. ✅ **DONE 2026-07-24.** Confirmed the parent doc
      (`sports_predictions_live_mode_and_backtest_execution_orphaned_2026_07_21.md`) has the Group-C todo checked `[x]`
      with "decision: YES, genuinely needed". Corrected the "not decided yet" framing, added
      `sports_group_c_execution_backtest_harness_2026_07_21.md` to `related:`, and fixed a downstream Todo 5 that had
      baked in the same stale premise.
- [x] [DOC] P2. ✅ **DONE 2026-07-24** (same edit as the archive-candidate-verdict fix above — 4 new `- [ ]` todos
      created from the gap-analysis prose, cross-referencing the closeout's Track C/V for scope-overlap awareness).
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

- [x] [DOC] P0. ✅ **DONE 2026-07-24.** Re-verified `_source_priority_data.py` directly (not just trusted the citation):
      confirmed `odds_api = {BATCH, LIVE, REPLAY}`. Fixed the capability row, rewrote the "no live source" framing in
      §1/§2/§6 (cross-referencing `sports-live-odds-connectivity.md` as the SSOT rather than duplicating it), and
      grepped for M6/honest-coverage code keying off "sports has no live source" — found the actual M6 guardrail
      (`shard_source_availability.py::could_exist`) is already data-driven off `SOURCE_MODE_CAPABILITY`, needing no code
      fix; flagged two smaller, non-blocking findings in-doc (a stale illustrative docstring comment, and an unrelated
      pre-existing M6-case-ordering inconsistency for `api_football`/fixtures — flagged for separate review, not fixed
      here since it's outside this finding's scope).

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

- [x] [DOC] P1. ✅ **DONE 2026-07-24.** Rewrote the note to past tense with both bucket-deletion timestamps/evidence
      counts (`instruments-store-sports-central-element-323112` DELETED 2026-07-16T19:52Z;
      `market-data-tick-sports-central-element-323112` DELETED 2026-07-17T~16:50Z). **Correction to this finding's own
      premise**: T6.7 no longer lives in `sports_legacy_bucket_cutover_2026_07_16.md` — that plan was
      line-cap-remediated 2026-07-24 and forked its open Phase-6 todos into
      `sports_legacy_cutover_closeout_tasks_2026_07_24.md`, where T6.7 was found still open and is now flipped `[x]`
      there with the 3-codex-path gate evidence. Checked both sibling docs (`bucket-naming-and-config.md`,
      `manifest-consolidator-ssot.md`) — neither had the same gap (confirmed unaffected, not edited).
- [x] [DOC] P2. ✅ **DONE 2026-07-24.** Verified both inbound pointers genuinely link to this doc, added both to
      `referenced_by:`, and annotated both source links with a "(superseded — see sports-batch-live.md for current
      architecture)" caveat.
- [x] [DOC] P1. ✅ **DONE 2026-07-24.** Confirmed the sibling banner convention (3 siblings checked) and added the
      identical banner to both `kelly.md` and `staking-methods.md` (the archived `_archived_pre_v2/sports/` path — the
      separate, non-archived `architecture-v2/axes/staking-methods.md` was correctly left untouched).
- [x] [DOC] P1. ✅ **DONE 2026-07-24.** Traced the 2-hop merge via grep + 2 current codex SSOTs: USRI → merged into
      `unified-reference-data-interface` (sports/ sub-package, 2026-03-01 sports consolidation) →
      `unified-reference-data-interface` itself eliminated 2026-03-26, folded into `instruments-service`. Flipped
      `status: "active"` → `"eliminated"`, added an `elimination_note` field (matching sibling-yaml convention) citing
      the full chain + both confirming SSOTs, corrected `last_updated` to the actual elimination date. YAML validated
      post-edit.
- [x] [DOC] P2. ✅ **DONE 2026-07-24.** Reworded both lines (696 UDEI, 698 USEI — line numbers shifted slightly from
      this finding's citation) to match the doc's own already-correct "merged into execution-service, 2026-03-26"
      phrasing used elsewhere in the same doc.
- [x] [DOC] P2. ✅ **DONE 2026-07-24.** Re-verified current state in `sports_master_closeout_2026_07_21.md` (not just
      the finding's numbers) and rewrote the section into 3 explicit bullets: DONE (GCS-object wipe, 212,519 + 437,124
      objects, with counts), DEFERRED (manifest-row phantom prune, 131,426 + 944,776 rows), and a third, separate
      still-open population found during verification (83,541 pre-floor FIXTURES objects, an orphan-sweep-audit finding
      distinct from the manifest prune) — each citing its source plan.
- [x] [DOC] P1. ✅ **DONE 2026-07-24** (same edit as the casing-doctrine-scope fix above — the rewritten banner
      explicitly cites both reversal dates).
- [x] [DOC] P2. ✅ **DONE 2026-07-24.** Removed the dead sibling-repo link (2 occurrences) and repointed the dead
      `sports-data-sources.md` codex path to the real `sports-data-source-coverage-matrix.md` target.

### P2 — needs a substantive fix, no operator authority question

- [x] [DOC] P2. ✅ **DONE 2026-07-24.** Verified against the real `EmptyConfirmedReason` enum in UAC. Fixed the
      `EXPECTED_SOURCE_COVERAGE_START` → `EXPECTED_PRE_SOURCE_COVERAGE_START` typo. For
      `EXPECTED_FIXTURE_STARTED_EARLY`: confirmed no existing UAC member cleanly maps onto this semantic — per
      instruction, did NOT invent a new enum member; instead corrected both citations to explicitly flag this as an open
      follow-up requiring a real UAC addition, and synced `sports-batch-live.md`'s §4 closed-set list to match (it
      already used the correct spelling elsewhere, so only needed the new flagged-gap note, not a correction).
- [x] [DOC] P2. ✅ **DONE 2026-07-24 (bannered, not re-verified).** Added a note qualifying the 75.41% all-time
      (2014-2026) figure as historical-only/pre-floor, not re-measured against the post-floor manifest; the 99.55%
      current-era figure is unaffected (entirely post-floor).

## Status — ALL 33 findings applied 2026-07-24

`/autonomous` continuation drove every remaining `- [ ]` item in this doc to done, either directly or via 8 parallel
sub-agents scoped to disjoint files (each editing only, no commits — a coordinating pass reviewed every diff, ran
quality gates, and shipped in a consolidated batch). Every finding above is now `- [x]`, with evidence inline.

**One item is a deliberate exception, not an oversight**:
`cross_ag_prediction_rows_bleed_into_sports_instruments_index_2026_07_20.md`'s P0 item was RE-TRIAGED to ROUND 3
(reopened, documented, next-step investigation plan written) but its actual **root-cause + durable fix is genuinely NOT
done** — this is real, open production data-correctness investigation work (why does the consolidator keep reasserting
the exact pre-remediation row set), not a doc-reconciliation fix, and attempting a blind re-fix without confirming the
mechanism would repeat round 2's mistake. This is the one legitimate piece of future work this session leaves behind —
tracked as ROUND 4 in the issue doc itself, not silently dropped.

**Two archival/authority judgment calls were correctly left to the operator, not auto-decided**:
`sports_odds_bookmaker_coverage_enumeration_2026_06_20.md`'s eventual `[unlock-plan]` + empirical-seed-acceptance
archival ruling, and the fold-in-vs-keep-satellite call for
`sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md`. Both docs are correctly NOT archived,
with their real open work now properly tracked/linked rather than orphaned — the mechanical reconciliation this finding
actually asked for is done; the deeper archival decision was never this finding's ask.

## Ledger (Phase 5.9 discipline — counted, not eyeballed)

- plan-reconcile: 23 raw candidates -> 23 deduped -> 24 verified (incl. 2 done-but-unchecked evidence-checks) -> **20
  confirmed / 4 refuted**. Routed to operator: 16. Auto-fixable: 4. **16 + 4 = 20 — balances.**
- docs-reconcile: 14 raw candidates -> 14 deduped -> **13 confirmed / 1 refuted**. Routed to operator: 5.
  Auto-fixable: 8. **5 + 8 = 13 — balances.**
- Total: **33 confirmed findings, 33 applied 2026-07-24.** Zero silently dropped; zero blind-closed without evidence.

## Recommended next step

This doc's own remediation is complete. The one live thread it spawned —
`cross_ag_prediction_rows_bleed_into_sports_instruments_index_2026_07_20.md` ROUND 4 (root-cause the manifest
consolidator's reassertion mechanism + ship a durable fix, then verify across a real consolidation cycle, not just an
immediate post-write read) — is the next actionable item, and it's a real investigation, not a re-run of this audit.
