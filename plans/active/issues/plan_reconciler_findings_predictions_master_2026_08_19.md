---
doc_type: issue
title: "plan_reconciler predictions_master EPIC-scoped run findings — 2026-08-19 (interactive, epic-scoped mode)"
summary: >-
  Epic-scoped `/plan-reconcile predictions_master` pass over the 20 `parent_epic: predictions_master` docs (17 plans +
  3 issues at run start). Phase -1 reconciled all 3 prior dated prediction-tranche findings docs (2026-08-16/17/18)
  against fresh state, closing the last 2 grace-blocked carryovers (a stale `task_template.md` reference; the
  batch7+finalize archival referrer-fix) and archiving the now-fully-resolved 2026-08-17 findings doc itself (a
  checkbox flip pushed it to 0 open todos mid-run — caught via `check_archive_candidates.sh`, not left for ship time).
  Fanned out 4 read-only hunters (5th hit a global concurrency ceiling from other active sessions and never returned;
  its exact 4-doc scope — the hub, phase_c, batch12, batch12_finalize — was independently covered via a direct read
  instead, so there is no coverage gap). Applied every confirmed, hard-evidence-backed fix directly under trust mode:
  9 finding classes across 11 files, plus a full 6-step archival of `prediction_satellite_ao_dispatch_batch7_2026_08_04.md`
  + its finalize sibling. 4 findings (all on `prediction_satellite_ao_dispatch_batch6_2026_07_29.md`) are confirmed
  with hard evidence but left unfixed — that doc was touched <12h before this run's checks, both at start and at
  every re-check, so it stayed inside this corpus's established 12-hour grace window throughout. 0 refuted. DO NOT
  SHIP constraint in effect for this run — every fix landed in the working tree only, no commit/push; a separate lead
  session ships.
status: open
nature: issue
asset_group: [prediction]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan_reconciler, predictions_master, epic-scoped, reconciliation]
related:
  [
    /plans/epics/predictions_master.md,
    /plans/active/issues/plan_reconciler_findings_prediction_2026_08_16.md,
    /plans/archive/issues/plan_reconciler_findings_prediction_2026_08_17.md,
    /plans/active/issues/plan_reconciler_findings_prediction_2026_08_18.md,
  ]
created: "2026-08-19"
author: plan_reconciler
source: "interactive session, /plan-reconcile predictions_master (epic-scoped)"
locked_by:
priority: P2
assigned_vm: NA
execution_scope: local-only
parent_epic: predictions_master
resolved_by:
depends_on: []
drift_direction: advance-code
context_scope:
  [
    /plans/epics/predictions_master.md,
    /plans/active/prediction_consolidated_closeout_2026_07_18.md,
    /codex/11-project-management/epic-html-report-format.md,
  ]
---

# plan_reconciler predictions_master EPIC-scoped findings — 2026-08-19

## Phase -1 — prior findings docs reconciled first

Read all 3 dated `plan_reconciler_findings_prediction_*.md` docs (2026-08-16, 2026-08-17, 2026-08-18) in full. This
tranche has been reconciled daily for 3+ calendar days — genuinely "unusually well-audited," confirmed independently
by every hunter this run too.

- **`task_template.md:402`** (stale reference to `prediction_trades_migration_concurrent_dispatch_2026_07_28.md` at
  its pre-archive `plans/active/issues/` path) — carried forward grace-blocked since 2026-08-16. Grace cleared
  (target's last commit 2026-08-17T15:40:18Z, >12h old at this run's 2026-08-19T00:49:38Z check). **FIXED** — repointed
  to `plans/archive/issues/...`. Flipped in `plan_reconciler_findings_prediction_2026_08_16.md` and
  `_2026_08_18.md` (both cited it).
- **Hub `prediction_consolidated_closeout_2026_07_18.md` missing a `prediction_venue_e2e_batch1_2026_08_16.md`
  citation** — carried since 2026-08-16. **MOOT/CLOSED**: that plan (+ its finalize) was archived 2026-08-18 by a
  concurrent session; a hub not citing an archived plan's pre-archive path is no longer a live gap. Flipped.
- **`prediction_satellite_ao_dispatch_batch7_2026_08_04_finalize.md` todo 2** (archive batch7 + finalize) — carried
  since 2026-08-17, blocked on `plans/epics/predictions_master.md` clearing its 12h grace window (cleared >2 days
  ago) AND on the finalize doc pair's own last touch (2026-08-17T15:37:52Z) clearing theirs. Both cleared as of this
  run. **FIXED** — full 6-step archival executed (detail below). Flipped in `_2026_08_17.md` and `_2026_08_18.md`.
- **Side-effect**: flipping the batch7 item above was `plan_reconciler_findings_prediction_2026_08_17.md`'s LAST open
  checkbox — `check_archive_candidates.sh` caught the resulting 0-open-todos state mid-run (exactly the failure class
  this task was warned to watch for). **FIXED** — that findings doc itself archived via the 6-step ritual
  (`plans/active/issues/` → `plans/archive/issues/`, flat per issue-doc convention), its 2 referrers
  (`_2026_08_18.md`'s `related:` + `context_scope:`) repointed.
- **3 items re-confirmed still correctly grace-protected or ordinary-work, left untouched**: the Betfair `[INFRA]`
  tag question and `mdps_fleet_duplicate_relaunch_explosion_2026_08_15.md` mistag question (both <12h since their
  last corpus-wide touch at every check this run), and `prediction_live_clob_depth_capture_2026_07_24.md:470`'s
  event-time-keying checkbox (re-confirmed as genuine ordinary work needing a live-code check, not a doc-hygiene
  gap — unchanged classification from the original 2026-08-16 review). Note: `mdps_fleet_duplicate_relaunch_explosion_2026_08_15.md`
  is NOT a `parent_epic: predictions_master` doc (it's `prediction`-tranche-tagged but not epic-owned) — genuinely
  out of this epic-scoped run's bounds regardless of grace.
- **1 routing item unchanged**: the systemic `last_updated`-staleness tooling-gap note filed 2026-08-18 (routed to
  whoever owns `context-scout`/`na-eligibility-audit`/`plan_reconciler`'s own update logic) — not this run's job,
  left as filed.

## Phase 0/1 — inventory + hunter fan-out

`rg "^parent_epic: predictions_master$" plans/active/*.md plans/active/issues/*.md` → 20 docs (17 plans + 3 issues) at
run start, cross-verified against `epic_report_data.py --epic predictions_master --json`
(`plan_children_count: 17, issue_children_count: 3` — exact match). Corpus size (>15) called for hunter fan-out per
this run's own sizing instruction.

**5 hunters dispatched** (general-purpose, sonnet, read-only, `SUB_AGENT_MANDATORY_RULES.md` pasted in full at every
spawn), partitioned into ≤5-doc batches:

- **Hunter A** (4 docs: `prediction_live_clob_depth_capture`, `batch11`, `batch11_finalize`, `phase_e_football_arb_live`) — completed, 22 findings.
- **Hunter B** (4 docs: hub `prediction_consolidated_closeout`, `phase_c_data_status_ui`, `batch12`, `batch12_finalize`) — **dispatched but never returned a result this session** (the environment's global concurrent-subagent ceiling was repeatedly hit by other active sessions on this shared host — 2 retry attempts both rejected). Its exact 4-doc scope was independently covered via a direct full read instead (below) — no coverage gap, just a different execution path.
- **Hunter C** (batch6 doc trio: `batch6`, `batch6_finalize`, `batch6_progresslog` + the linked Betfair issue doc) — completed, 7 findings.
- **Hunter D** (4 docs: `phase_ab_residuals`, `phase_d`, `predictions_ml_walk_forward_and_arb`, `phase_c`'s sibling `cross_venue_arb_and_coverage`) — completed, 6 findings.
- **My own direct reads** (Hunter B's scope + the 3 issue docs, since the corpus's own concurrency ceiling made a
  6th hunter attempt pointless): hub, `phase_c_data_status_ui`, `batch12`, `batch12_finalize`,
  `mtds_prediction_adapters_dead_rest_polling_interface`, `prediction_batch4_deferred_residuals`,
  `prediction_betfair_lay_price_adapter_scaffold_deleted`.

**Coverage: 18/18 remaining active child docs read in full this run** (100% — the 20-doc start count minus the 2
archived mid-run), plus both newly-archived docs (batch7 pair) edited directly, plus all 3 prior findings docs for
Phase -1.

## Phase 3/4 — adversarial verification + fixes applied (all hard-evidence, auto-resolved under trust mode)

Every candidate below was independently re-verified before applying — either by re-reading the cited target directly,
running the cited `git log`/`grep -c`/`find` command myself, or (for hunter-reported commit SHAs) trusting the
hunter's own `git merge-base --is-ancestor` output where it was shown as executed, per this run's own bar.

- [x] ✅ [DOCS] P2. **Stale cross-doc open-todo count for `prediction_phase_ab_residuals_2026_07_24.md` — cited as "6
      open" in 4 places, actual live count is 4** (`grep -c '^- \[ \]'`, matching that doc's own 2026-08-18
      na-eligibility-audit marker — dropped 6→4 via the 2026-08-17 RECLASSIFY_SPLIT extraction to batch12).
      Fixed in `prediction_satellite_ao_dispatch_batch11_2026_08_13.md` (both todos) and
      `prediction_consolidated_closeout_2026_07_18.md` (snapshot table + aggregated index). Gate conclusions
      unchanged everywhere (4 > 0, same as 6 > 0).
- [x] ✅ [DOCS] P2. **`prediction_phase_ab_residuals_2026_07_24.md`'s own frontmatter `summary:` named 5 residual
      items, 4 of which had already closed** (only "the historical fixture-match-attribute backfill" of the 5 named
      items is still open; the doc's real 4 open items today are the manifest migration `--apply`, that backfill,
      the `instrument_type` casing re-verify, and the 3x-cadence top-up — 3 of 4 weren't named at all). Rewrote the
      summary's residual-work clause to name the accurate 4. (Hunter D, finding F1.)
- [x] ✅ [DOCS] P2. **LINE-1 completeness — a hard gating/scoping constraint hidden on line 2, not line 1** (task
      instruction's flagged common defect class, confirmed genuinely present in 3 places this run):
  - `prediction_satellite_ao_dispatch_batch11_2026_08_13.md` — both todos' real gate ("once the phase_ab gate
    clears") wrapped past line 1; rewrote both to front-load a bolded `**GATED — do not run until...**` clause.
  - `prediction_phase_e_football_arb_live_2026_07_24.md` E3 — the scoping fact "only gap (3) remains open" (gaps 1-2
    already shipped) sat entirely on line 2 behind a title that reads as the whole 3-gap task; reordered the bold
    clause so the scoping fact leads.
  - Reviewed and explicitly NOT rewritten: `batch11_finalize.md`'s 3 process todos (normal prose wrap matching the
    fleet-wide finalize-plan template used identically across every sibling batch's finalize doc — no hard
    constraint hidden, just an object/method continuing normally); `predictions_ml_walk_forward_and_arb_2026_06_20.md`'s
    2 remaining `(BLOCKED-ON...)` wraps (the doc's own top-level banner already states the blocker); `batch6`'s
    2 non-Betfair line-1 wraps (no functional impact — the operative tag/marker is already on line 1 in both cases).
- [x] ✅ [DOCS] P2. **Ordering stated in prose only, never machine-enforced** —
      `prediction_satellite_ao_dispatch_batch11_2026_08_13.md` had `depends_on: []` despite both todos being
      prose-gated on `prediction_phase_ab_residuals_2026_07_24` reaching 0 open todos; 2 separate dispatched workers
      (slot-29, slot-12, both 2026-08-14) independently wasted a round-trip discovering the gate live because nothing
      machine-held them. Added `depends_on: [prediction_phase_ab_residuals_2026_07_24]` + `gate_on_depends: true` —
      encodes the todos' own already-stated intent as a real gate, doesn't change it. (Hunter A.)
- [x] ✅ [DOCS] P3. **Stale `last_updated` frontmatter** (4 instances, each contradicted by a later dated body
      entry in the SAME doc — the auto-resolve class per this skill's own calibration, no new measurement needed):
      `batch11` (was 2026-08-13, contradicted by a 2026-08-17 body edit), `batch11_finalize` (same), `phase_e`
      (was 2026-08-12, contradicted by a 2026-08-18 na-eligibility-audit entry), hub (bumped after its own body
      edit this run). (Hunter A findings 1-4.)
- [x] ✅ [DOCS] P2. **Ambiguous back-reference — "same `--day` ruling as above" with the actual day value entirely
      on a prior todo, not restated** — `prediction_phase_d_formal_smoke_and_backfill_2026_07_24.md` 2 instances
      (lines 136, 170); the doc's OWN line 158 already does this correctly ("ruled 2026-08-07 same as the P0 todo
      above (`2026-08-05`, fallback `2026-06-28`)"). Restated the value inline in both, mirroring that pattern.
      (Hunter D, findings F3/F4.)
- [x] ✅ [DOCS] P2. **Wrong internal self-citation** — `predictions_ml_walk_forward_and_arb_2026_06_20.md:72-74`
      cited "line 53's walk-forward run" for its own sibling todo; live `grep -n` confirms the walk-forward todo is
      at line 65, not 53 (line 53 is this doc's own gate-banner quoting `sports_master.md`). Fixed the citation.
      (Hunter D, finding F5.)
- [x] ✅ [DOCS] P2/P3. **9 dangling/stale-format references, all in `prediction_live_clob_depth_capture_2026_07_24.md`**
      (a marquee, `archive_exempt: true` doc — confirmed still correctly exempt, 0 open todos by design): 6
      `related:` entries pointing at pre-archive paths without the leading-slash convention (repointed + reformatted,
      all 6 targets verified to exist at their corrected paths via direct `[ -f ]` checks before writing); 2
      bare-path citations in `source:`/the body banner to `plan_line_cap_remediation_2026_07_23.md`'s pre-archive
      location; 1 body citation to `mdps_features_live_streaming_aggregation_never_actually_invocable_2026_08_04.md`,
      which has since ALSO archived. (Hunter A, "Stale references" 1-5.)
- [x] ✅ [DOCS] P3. **Stale in-body prose contradicting its own `[x]` checkbox** — same doc, the
      "DEFERRED-CROSS-DEP" item (line 247) is checked `[x]` but its own 2026-08-07 annotation still narrates "stays
      `- [ ]`, NOT run." Verified the underlying fact independently: `prediction_satellite_ao_dispatch_batch10_2026_08_09.md`
      (the item's confirmed live owner per an earlier 2026-08-10 correction already in-doc) is now `status: complete`,
      archived, and its own finalize plan's text confirms this exact item flipped with a full evidence chain (live
      manifest rows, 2 commit SHAs). Struck the stale sub-claim, appended the resolution — the checkbox's own `[x]`
      state was already correct, only the prose was stale. (Hunter A, finding 5.)
- [x] ✅ [DOCS] P3. `plans/active/task_template.md:402` — see Phase -1 above.

### Archival (full 6-step ritual, both `doc_type: plan` → `plans/archive/2026_08/`)

- [x] ✅ **`prediction_satellite_ao_dispatch_batch7_2026_08_04.md` + `_finalize.md`** — both todos done (source-doc
      reconciliation 2026-08-17; the archival step itself, grace-blocked since 2026-08-17, executed once both the
      epic and the pair's own last-touch cleared 12h). Steps: (1) no DEFERRED items to migrate — both had none; (2)
      archived-banner added to both; (3-5) codex-alignment check — no new durable contract, the underlying finding
      (no separately-scoped manifest backfill needed for prediction `trades`/`book_snapshot_5`) already lives in the
      archived source issue doc, cited explicitly; (6) `git mv` both to `plans/archive/2026_08/`, `status: active` →
      `resolved`. **Referrers**: `plans/epics/predictions_master.md`'s 4 citation lines (2 `related_plans:` + 2 body
      headers) repointed with a resolved-status note mirroring the existing batch4/batch8 pattern in the same doc;
      the finalize doc's OWN `related:` self-reference to batch7's pre-archive path (a 5th referrer this todo's own
      text didn't name, caught by a fresh corpus-wide grep before closing) also repointed. Corpus-wide grep confirms
      **0 remaining live referrers** to either pre-archive path.
- [x] ✅ **`plan_reconciler_findings_prediction_2026_08_17.md`** — `doc_type: issue` → flat `plans/archive/issues/`
      (per issue-doc convention). Reached 0 open todos as a direct consequence of this run's own Phase -1 fix (see
      above); `check_archive_candidates.sh` flagged it before it could be missed. Archived-banner added; 2 referrers
      in `_2026_08_18.md` repointed (`related:` + `context_scope:`).

## Confirmed, NOT fixed — grace-protected (all on `prediction_satellite_ao_dispatch_batch6_2026_07_29.md`)

That doc's last commit was 2026-08-18T22:06:56+01:00 (21:06:56Z) at run start; re-checked immediately before each
edit decision (last check: 2026-08-19T01:08:21Z, ~4h elapsed) — still inside the corpus's established 12h grace
window at every check this run performed. All 4 are hard-evidence-confirmed by Hunter C, none applied:

- [ ] [DOCS] P1. **Stale "next step" text** (lines ~240-251) says egress from `europe-west2` still needs
      provisioning; independently verified (`git merge-base --is-ancestor 7a7e847e origin/live-defi-rollout` in
      `deployment-service` → confirmed ancestor) that it WAS provisioned 2026-08-12 and the blocker moved to a
      Betfair account state (`ACCOUNT_PENDING_PASSWORD_CHANGE`) — already correctly documented 8 days ago in the
      linked issue doc and this same plan's own split-out Progress Log, just not in this specific inline paragraph.
- [ ] [DOCS] P2. **Stale Deferred-section prose** (lines ~681-690) says `prediction_satellite_ao_dispatch_batch2_2026_07_25.md`
      is "done but not yet archived" and directs a reader to flip its finalize to active — both `batch2` and its
      finalize have been `status: complete`, archived, since 2026-07-30.
- [ ] [DOCS] P2. **LINE-1 completeness** on the Betfair `[INFRA]` P2 todo (lines 159-160) — first physical line ends
      "Remaining work is provisioning a NEW" with the actual object (`europe-west2` network egress) entirely on
      line 2.
- [ ] [DOCS] P1. **Tag mismatch, confirmed live via the actual dispatcher code** — the todo's tag is bare `[INFRA]`;
      its mirrored issue-doc item carries `[BLOCKED-CREDENTIALS][INFRA]`. Hunter C traced
      `agent-orchestrator/server/regen_backlog_from_plan.py`'s `_is_non_dispatchable()`/`_has_live_blocked_token()`
      by hand against this doc's todo block and confirmed it currently returns **False** — i.e. this todo reads as
      live-dispatchable today despite being genuinely blocked on an external, worker-unresolvable Betfair account
      state, the exact churn pattern (6+ prior dispatches) that got the ISSUE doc's own copy retagged on 2026-08-10/11.

All 4 are a single coherent fix once grace clears — a future `/plan-reconcile` pass (sharded `prediction` or
epic-scoped `predictions_master`) should apply them together in one edit to that file.

## Reviewed, no fix warranted (confirmed candidates, not routed, not refuted)

- `data_completion_prediction_2026_07_15.md` — a narrative date-ordering quirk between two closure entries; no
  underlying fact wrong, prose sequencing only (Hunter, prior-day carryover context, re-confirmed not this run's job
  regardless — not a `parent_epic: predictions_master` doc).
- `mtds_prediction_adapters_dead_rest_polling_interface_2026_07_31.md` — a soft tension between one Progress Log
  entry calling the doc "a good archive-candidates-audit candidate" and a later one saying "genuinely NOT" (it
  carries `archive_exempt: true`) — plausibly means 2 different things ("candidate for the audit to REVIEW" vs. the
  audit's actual VERDICT), not confirmed as a hard contradiction. Left as-is, matching the existing soft/unverified
  calibration already in the doc.
- `phase_e_football_arb_live`'s E3 gap-3 template file (`strategy_service/configs/prediction_arb_all_soccer.yaml`) —
  Hunter A found this exists but is explicitly `TEMPLATE ONLY`, wires Betfair not bookmaker odds, and isn't in the
  live slot registry — informational context for whoever next works E3 gap-3, not a doc defect.
- 4× "missing explicit Done-when" (batch11's 2 todos, phase_e's 2 E3 todos) — real but P3/low-urgency; not applied
  this run given the corpus's own established practice of not force-adding boilerplate to already-well-evidenced
  todos.

## Refuted

**0.** Every hunter candidate that reached verification was either confirmed-and-fixed, confirmed-and-grace-blocked,
or confirmed-with-no-fix-warranted. No candidate was found to be a misread, a parser artifact, or already-stale
itself on closer reading.

## Operator-decision list

**None new this run.** Two pre-existing, already-correctly-tagged standing operator-gated items are unchanged (not
re-litigated, just confirmed still accurate on read):

- `prediction_batch4_deferred_residuals_2026_08_16.md` — `[OPERATOR][DATA] P2`, manual manifest `--apply`
  reclassification of 38,020 out-of-lifecycle rows, reserved for human review per the delete-safety protocol.
- `prediction_betfair_lay_price_adapter_scaffold_deleted_2026_08_09.md` todo 4 — `[BLOCKED-CREDENTIALS][INFRA] P2`,
  Betfair account-holder password-change action, confirmed still the live blocker (nothing newer found this run).

## Phase 5.9 — NO-MISS LEDGER

- **(a) routed == parked**: this run routed **0** new items to the operator (everything confirmed was either
  auto-fixable with hard evidence or grace-protected, a distinct, already-established class this corpus tracks
  separately from operator-routing); parked in this doc's "Confirmed, NOT fixed" section = **4** (grace-protected,
  not operator-routed). `0 == 0` for the operator-routing ledger specifically; the 4 grace items are separately
  enumerated above, not silently dropped.
- **(b) agent skips**: all 4 hunters that returned reported explicit full coverage of their batch with 0 skips
  (Hunter A: "all 4 docs read in full — yes"; Hunter C: "all 3 docs read in full"; Hunter D: "all 4 docs read in
  full — yes"). Hunter B did not return a result — enumerated above (Phase 0/1) with the reason (global concurrency
  ceiling) and the substitute coverage path, not silently absorbed into a bare count.
- **(c) verify at HEAD**: not applicable — this session made no commits (DO-NOT-SHIP constraint). Every edit was
  re-read via the Edit tool's own post-edit file-state confirmation; `check_archive_candidates.sh` and
  `check_line_caps.sh` were re-run directly against the working tree after every batch of edits (not just planned),
  catching the 08-17 findings-doc archive-candidate regression live rather than at ship time.
- **(d) conservation on the one MOVE this run performed** (batch7 pair archival): 2 files moved
  `plans/active/` → `plans/archive/2026_08/`; referrer count before = 4 live citations in the epic + 1 self-citation
  in the finalize doc's own frontmatter = 5; referrer count after fix = 0 live citations remaining (verified via
  corpus-wide grep, both before-fix state at 5 and after-fix state at 0 captured in this doc's Phase 3/4 section
  above). Balanced — nothing orphaned.
- **(e) every count above is a fresh measurement this run** (`grep -c`, `find`, `git log`, `wc -l`, `check_*.sh`
  re-runs), not carried forward from a prior doc's own count.

## Coverage (hunters / batches / docs)

- **4 hunters completed** (A/C/D + this run's own direct-read substitute for B); **1 hunter (B) did not return** —
  substituted directly, not silently dropped.
- **18/18 remaining active child docs read in full** (100% of the post-archival corpus) + both archived-this-run
  docs + all 3 prior findings docs (Phase -1) + the epic hub itself.
- **Candidates surfaced**: ~35 across all sources. **Verified CONFIRMED and fixed**: ~24 (9 finding classes, several
  multi-occurrence, plus 2 archivals). **Confirmed, grace-blocked (not fixed)**: 4. **Reviewed, no fix warranted**:
  ~7. **Refuted**: 0.

## Verification run against every touched file

- `check_line_caps.sh` — 0 regressions (3 pre-existing SOFT violations elsewhere in the corpus, unchanged; largest
  touched-file result is `prediction_live_clob_depth_capture_2026_07_24.md` at 928L, still under the 1000L hard
  cap).
- `check_archive_candidates.sh` — 0 candidates (the mid-run regression this run itself caused via the 08-17
  findings-doc flip was caught and fixed in the same session, not left for the lead session).
- YAML frontmatter — `yaml.safe_load()` re-run against every touched file's frontmatter block, all parse clean.
- `check_todo_format.sh` — 3 pre-existing non-canonical todos corpus-wide, none in a `predictions_master` doc
  (verified via direct grep of the checker's own output).

## Progress Log

- **2026-08-19** — full epic-scoped `/plan-reconcile predictions_master` run. Phase -1 reconciled 3 prior findings
  docs, archived 1 of them mid-run after a self-caused 0-open-todos regression was caught by `check_archive_candidates.sh`.
  Phase 0/1 fanned 5 hunters (4 completed, 1 lost to host concurrency contention, substituted directly). Applied 9
  fix classes across 11 files + a full 6-step archival of batch7+finalize, all hard-evidence auto-resolved under
  trust mode — no operator ruling needed this run. 4 findings left correctly grace-protected on
  `batch6_2026_07_29.md`. 0 refuted. Working-tree only, no commit/push (do-not-ship instruction). Phase 5.95 HTML
  report built + published — see `plans/epics/predictions_master.md`'s own `## Report` section for the link.
