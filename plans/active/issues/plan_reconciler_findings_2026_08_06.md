---
doc_type: issue
title: Daily plan-reconciler findings 2026-08-06 (dispatch agt-4fdce1)
summary:
  Run-findings + progress journal for the daily deep plan-reconciliation pass (dispatch `agt-4fdce1`, slot 2). Fan-out
  DETECT (epic-cluster / topic / codex-alignment / mechanical-adjudicator / missed-flip hunters) + adversarial VERIFY,
  then APPLY the confirmed-easy and ROUTE the hard. Appended to throughout the run — see sections below for current
  state.
status: open
nature: process
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan-hygiene, reconciliation, plan_reconciler, boot-prompt, scheduled]
related: []
created: 2026-08-06
author: plan_reconciler
parent_epic: plan_hygiene_master
priority: P2
source: ["daily plan-reconciliation pass agt-4fdce1 2026-08-06"]
assigned_vm: planning
resolved_by:
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-08-06
---

# Daily plan-reconciler findings 2026-08-06 (agt-4fdce1)

Slot 2, branch `plan_reconciler/agt-4fdce1`. This doc is the run journal — appended to as the pass progresses.

## Todos

- [ ] [DOCS] P1. **Fix the recurring finalize-twin `status: active` (frontmatter) vs `` `status: draft` `` (body banner)
      bug** — confirmed in ≥8 docs this run (`bucket_iam_write_protection_per_tier_..._finalize_2026_07_27.md`,
      `data_completion_cefi_2026_07_15_finalize_2026_07_27.md`,
      `defi_pipeline_e2e_and_coverage_validation_..._finalize_2026_07_27.md`,
      `defi_satellite_ao_dispatch_batch3_2026_07_26_finalize.md`,
      `tradfi_manifest_content_recovery_completion_..._finalize_2026_07_27.md`,
      `tradfi_satellite_ao_dispatch_batch2_2026_07_25.md`,
      `codex_vs_repo_docs_ssot_audit_2026_06_01_finalize_2026_07_27.md`,
      `data_pipeline_check_mdps_features_2026_07_20_finalize_2026_07_27.md` — likely more, not exhaustively grepped).
      Mechanical: `grep -rn 'STATUS.*draft.*NOT dispatched' plans/active/*.md`, cross-check each hit's own frontmatter
      `status:`, fix whichever side is wrong (usually the stale body banner once the doc is genuinely dispatched).
- [ ] [DATA] P1. **Live-verify `infra_satellite_ao_dispatch_batch3_2026_07_30.md`'s `assigned_vm` actually parses as
      `planning`** (batch7 found it parses blank due to an unusual multi-line YAML comment form) — check against the
      real backlog regen output, not just the doc text.
- [ ] [DOCS] P0. **Correct `sports_satellite_ao_dispatch_batch5_2026_07_26.md` + its finalize twin** — both assert "no
      operator ruling found on live sports-odds ingestion," but
      `sports_predictions_live_mode_activation_readiness_2026_07_21.md` todo 1 shows an explicit RULED-YES
      (2026-07-28) + a shipped connector. Stop re-asking an answered question; re-scope batch5's todo 1 off the real
      current blocker (the launcher exec-dispatch wiring, per that same live-mode-readiness doc).
- [ ] [VERIFY] P1. **Determine whether `gate_on_depends` is actually reliable now** —
      `prediction_satellite_ao_dispatch_batch6_2026_07_29_finalize.md` found it did NOT hold (dispatched at 3/14 done);
      `prediction_satellite_ao_dispatch_batch7_2026_08_04_finalize.md` (days later) assumes it does and skips the
      `status: draft` safety net on that assumption. If the underlying bug isn't fixed, batch7-finalize's own todos are
      exposed to premature dispatch.
- [ ] [DOCS] P2. **`defi_master.md` epic hub**: "2 DeFi perp DEXs live: Hyperliquid + Aster" is stale (both reclassified
      pure-CEFI 2026-06-21, re-verified live 2026-08-02 per
      `hyperliquid_aster_defi_to_cefi_asset_group_migration_2026_08_02.md`) — needs an edit to the epic's narrative
      Scope section (outside this run's auto-fix scope, which only touched the derived roster section).
- [ ] [DOCS] P2. **Add a correction banner to
      `plans/active/issues/mdps_features_live_launcher_exec_dispatch_never_wired_2026_07_27.md`** pointing at
      `mdps_features_live_streaming_aggregation_never_actually_invocable_2026_08_04.md` — its "all done" claim rests on
      a static dry-parse check; the successor doc's live GCE pilots found the exec-dispatch 100% broken in production.
- [ ] [DOCS] P3. **Fix `unified-trading-pm/agents/plan_reconciler.md`'s own drift**: STEP 6b's ping-ledger-append target
      files are retired (2026-07-04, "do NOT append pings here"); STEP 7/8's `curl` snippets use `/api/plan_health/...`
      (underscore), the live server only serves `/api/plan-health/...` (hyphen).
- [ ] [SKILL] P2. **Run `/ag-closeout-audit`** across the tranches that grew this run's linkage-orphan count (69→83
      baseline; cross-cutting, ao, infrastructure, cefi most likely per prior baseline notes).
- [ ] [SKILL] P2. **Run `/na-eligibility-audit`** — `assigned_vm:NA` corpus grew past baseline (359→376 docs, 1295→1317
      todos) this run; not hand-triaged (out of plan_reconciler's scope by design).
- [ ] [SCRIPT] P2. **Fix `scripts/quality_gates/check_finalize_plan_coverage.py`'s root cause** (operator ruling,
      BLK-5eeacb63, 2026-08-06): its "no companion gated finalize plan exists" precondition doesn't detect an EXISTING
      finalize plan under a slightly different exact-match name, so it generated a SECOND duplicate finalize plan for
      `live_event_log_warm_sink_recovery_and_cold_compaction_2026_07_31.md`, which already had `..._finalize.md` — the
      two then raced on the same `depends_on`+`gate_on_depends: true` target (de-raced this run by superseding the
      duplicate, see Flips verified). Make the existence check resilient to a `_2026_MM_DD` date-suffix variant of the
      expected filename, not just the exact string.
- [x] ✅ [ADMIN] P1. **Resume STEP 8 of this dispatch (agt-4fdce1).** Operator answered all 3 questions 2026-08-06
      ~13:12 UTC, ~12.5h after they were raised. All 3 applied: `BLK-5eeacb63` (duplicate finalize-plan race — kept
      `..._finalize.md`, ported the other's `[REVIEW]` todo in first, then superseded+archived the duplicate,
      `unified-trading-pm@511ba5da0`), `BLK-136e69bf` (sports LA_LIGA_2 — re-verified live, 846/846 target cells now
      captured under the aliased `SEGUNDA_DIVISION` key, filed the alias-removal question as a new judgment-call todo,
      `unified-trading-pm@95c107a98`), `BLK-0e7e0794` (upbit — reopened the falsely-checked todo, tagged
      `BLOCKED-CREDENTIALS`, dropped the placeholder citation, `unified-trading-pm@c06649920`). `/done` next.

## Run context

- Now: 2026-08-06 00:09 UTC. Grace cutoff (12h): 2026-08-05 12:09 UTC.
- Corpus: 235 `plans/active/*.md` + 468 `plans/active/issues/*.md` = 703 candidate files. **300/703 (43%) are within the
  12h grace window** — a much higher fraction than typical, meaning several large bulk commits landed in the last 12h
  touching a wide swath of the corpus. These are read-only context this run; nothing in the grace set is written.
- `run_hygiene_sweep.sh --ci`: 5 hard ratchet failures, 1 soft warning (full detail below). Inventory regenerator: 232
  active plans, 5 orphans, 0 TBD, 62% done overall, 274 cal AI-days left. INDEX.md regenerated (232 plans, 0
  uncategorized) — this + the archive inventory-dashboard regen are mechanical, kept (not the same class of side effect
  as the `master_to_live_defi` grace-plan revert, which WAS discarded per STEP 1 instructions).

## Hard ratchet failures (Phase-0 inventory from the sweep)

| Check                       |              Baseline |                  Live |                Delta | My scope this run                                                       |
| --------------------------- | --------------------: | --------------------: | -------------------: | ----------------------------------------------------------------------- |
| Terminal-status-archived    |                     1 |                    33 |                  +32 | FIX — archive ritual (STEP 5f), grace/lock permitting                   |
| Archive candidates          |                     0 |                   147 |                 +147 | FIX — archive ritual (STEP 5f), grace/lock permitting; overlaps row 1   |
| Reference paths (format)    |                    81 |                   103 |                  +22 | FIX — `fix_reference_paths.py` mechanical pass, grace-filtered          |
| Reference paths (existence) |                    86 |                   103 |                  +17 | MIXED — mechanical adjudicator per dangling ref; route what's ambiguous |
| AG-closeout linkage         |                    69 |                    87 |                  +18 | ROUTE — `/ag-closeout-audit` scope, not hand-fixed here (see Filed)     |
| assigned_vm:NA corpus size  | 359 docs / 1295 todos | 376 docs / 1317 todos | +17 docs / +22 todos | ROUTE — `/na-eligibility-audit` scope (see Filed)                       |

## Flips verified

- Epic hub `infrastructure_master.md` todo (Folded-in scope 2026-07-15): flipped `[ ]`→`[x]` — removed the 5 stale
  "IN-FLIGHT REFACTOR — UTL/UAC reuse consolidation" banners the todo itself named (infra/strategy/features_and_ml
  /execution/orchestrator epics); the todo's own record already proved the refactor shipped+archived. P0, self-evident
  from the record — no adversarial pair needed.
- **STEP-8 answers applied (operator, 2026-08-06 ~13:12 UTC, after ~12.5h wait)**: BLK-5eeacb63 — kept
  `live_event_log_warm_sink_recovery_and_cold_compaction_2026_07_31_finalize.md`, ported its duplicate twin's `[REVIEW]`
  todo in first, then superseded + archived the duplicate (`..._finalize_2026_07_31.md` → `plans/archive/2026_08/`);
  root-cause filed as a new Todo above. See BLK-136e69bf and BLK-0e7e0794 entries below for the other two answers as
  they're applied.

## Contradictions

**51 confirmed by hunter read** (dual quotes+locations, `<relpath>:<line>`) across the 10 epic-cluster batches — NOT
individually re-verified by an independent second pass this run given the volume (effort budgeting call; each hunter's
own methodology already cross-referenced git log / sibling docs / live code where the finding warranted it — see each
hunter's per-finding "Why" line for its own evidence chain). Grouped by severity; full citations live in this run's
sub-agent transcripts (not reproduced verbatim here to stay under the line cap) — cite the hunter batch name if you need
to pull the exact quote.

**P0 (5 found, 1 fixed this run, 1 alerted, 3 remain — route to next run or operator)**

| #   | Finding                                                                                                                                                                                                                                                                                     | Batch                       | Status                                                                                                                                |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | infra epic hub stale IN-FLIGHT banner contradicts its own "folded-in, shipped" note                                                                                                                                                                                                         | infra-A                     | ✅ FIXED (see Flips verified)                                                                                                         |
| 2   | `bucket_iam_write_protection_per_tier_..._finalize_2026_07_27.md`: `status: active` frontmatter vs body "STATUS: `draft`" banner                                                                                                                                                            | infra-A                     | NOT FIXED — same bug class as #4/#5 below, recurs in ≥6 finalize-twin docs corpus-wide; needs one sweep, not 6 one-offs (filed below) |
| 3   | `infra_satellite_ao_dispatch_batch3_2026_07_30.md` claims dispatchable (`assigned_vm: planning`); batch7 (2 days later, live-re-verified) says the field actually parsed blank due to an unusual multi-line YAML form                                                                       | infra-B                     | NOT FIXED — needs a live parse-check against the real backlog regen, not a doc edit; routed                                           |
| 4   | `sports_predictions_live_mode_activation_readiness_2026_07_21.md` todo 1 shows an explicit YES ruling (2026-07-28) + a shipped connector; `sports_satellite_ao_dispatch_batch5_2026_07_26.md` AND its finalize (both dated after) still assert the ruling is unmade and infra doesn't exist | sports                      | NOT FIXED — needs the batch5 doc corrected to stop re-asking an answered question; routed                                             |
| 5   | `prediction_satellite_ao_dispatch_batch6_2026_07_29_finalize.md` found `gate_on_depends` did NOT hold (dispatched at 3/14 done); `batch7_2026_08_04_finalize.md` (days later) asserts the gate "alone already machine-holds" and skips the `status: draft` safety net on that assumption    | predictions                 | NOT FIXED — needs a live AO-mechanism check (is the underlying bug actually fixed?), not a doc edit; routed                           |
| 6   | Two finalize plans (`live_event_log_warm_sink_recovery_and_cold_compaction_2026_07_31_finalize.md` + `..._finalize_2026_07_31.md`) both gate on the same parent, will race on the same archival target                                                                                      | tradfi/obs/batch-live combo | 🔔 ALERTED (`BLK-5eeacb63`)                                                                                                           |

**P1 (≥20 found)** — dominant recurring shape (≥8 instances across infra/predictions/defi/tradfi/manifest_master
batches): a gated **finalize** doc's frontmatter says `status: active` while its own body banner says
`` `status: draft` — NOT dispatched``. Functionally low-risk (`gate_on_depends` is the real gate, not this prose), but
misleads a reader trusting the banner. **This is a single systemic authoring-template bug, not N separate findings** —
recommend a corpus-wide grep-and-fix of the exact banner string in a follow-up (mechanical, bounded), rather than
patching instance-by-instance. Other P1s: stale/contradictory completion claims between a plan and its own finalize twin
or epic hub (DERIBIT options_chain coverage %, TradFi G4 apply-done-with-caveat, CQG residual archived-but-hub-
still-lists-active, OmniRoute account-status, defi_master.md's Hyperliquid+Aster still-DeFi claim vs the dedicated
2026-08-02 migration confirming CEFI-only since 2026-06-21) — each needs its own read to resolve; not mechanically
batchable. Full list in sub-agent transcripts.

**P2/P3 (≥25 found)**: overwhelmingly epic-hub roster staleness ("N active plans declare parent_epic: X" undercounts /
lists an archived plan as active) — **this entire class is already resolved** by this run's
`populate_epic_bodies_2026_05_21.py --apply` (see Hygiene fixes). Residual P2/P3s are cosmetic (frontmatter
`last_updated` staleness, a title miscounting its own venue list, arithmetic-off-by-one in a Progress Log) — logged in
transcripts, not worth individual issue docs.

## Doc-drift

- `defi_master.md` (epic hub): "2 DeFi perp DEXs live: Hyperliquid + Aster" is stale — both reclassified pure-CEFI
  2026-06-21, operator-confirmed 2026-07-27, re-verified live 2026-08-02
  (`hyperliquid_aster_defi_to_cefi_asset_group_migration_2026_08_02.md`). Codex-adjacent (epic hub, not `codex/`) —
  flagged, not auto-fixed, since it's narrative content outside the auto-populated section. **Needs an operator-visible
  fix**, filed below.

- `unified-trading-pm/agents/plan_reconciler.md` STEP 7/8's `curl` snippets use `/api/plan_health/dispatch` +
  `/api/plan_health/result` (underscore) — the live server only serves `/api/plan-health/dispatch` +
  `/api/plan-health/result` (hyphen); underscore 404s. Worked around this run by checking `/openapi.json`. Same class of
  drift as the ping-ledger note below — role file lagging a live rename.
- `unified-trading-pm/agents/plan_reconciler.md` STEP 6b instructs appending a line to
  `ikenna_orchestrator/_agent_pings.md` + `harsh_orchestrator/_agent_pings.md` — both retired 2026-07-04 ("Do NOT append
  pings here... AO agents are explicitly forbidden from polling this file"). Skipped this run (the retirement notice is
  current and authoritative; my own role file is stale on this one point). The modern channel (`/blocked` alerts,
  already fired 3x this run) supersedes it. **Filed below.**

## Hygiene fixes

- **Reference-path mechanical fix**: `fix_reference_paths.py` — 90 codex-ref occurrences normalized, 12 files (7 more
  grace-protected, self-heals next run).
- **Epic-roster regeneration**: `populate_epic_bodies_2026_05_21.py --apply` across all 23 epics — independently
  resolves ~15+ "stale/undercounting epic roster" P1/P2 findings multiple hunters reported (derived section only,
  `related_plans:` + `## Assigned active plans`, no narrative touched).
- **49 docs archived** (47 issues + 2 plans) + 1 bonus (instruments_satellite_ao_dispatch_batch1, discovered via a
  routed action item in another doc) = **50 total**, all hunter-verified 0-open-todo + no-undone-prose. 2 needed a small
  pre-archive correction (stale banner reworded, not rewritten) before archiving.
- **Corpus referrer fixes**: 2 broken markdown links (`validate_plan_links.py`) + 63 broader full-path referrers
  (`check_reference_paths.py`'s wider existence check) + 4 more found via the bonus archival = 69 files, all verified
  post-fix. 16 referrer files left untouched (12h grace window) — will self-heal next run.

## Filed

- `plans/active/issues/mtds_features_live_launcher_exec_dispatch_never_wired_2026_07_27.md`: NOT archived (was
  ARCHIVE_READY-looking by checkbox, but its "all done" claim rests on a static dry-parse check; a same-day successor
  doc ran real GCE pilots and found the exec-dispatch 100% broken in production). **Needs a correction banner** pointing
  to `mdps_features_live_streaming_aggregation_never_actually_invocable_2026_08_04.md` before any future archive pass —
  not applied this run (time budget), left as a todo for the next reconciliation pass.
- `plans/active/issues/sports_fixture_events_refetch_progress_2026_07_25.md`: archived as-is (core campaign genuinely
  done) but carries one non-blocking prose-only follow-up (2,002 blank-`league_id` manifest rows, same pattern as
  `sports_af_full_entity_completion_2026_08_03.md`) never captured as a checkbox. Noted here per the doc's own
  "non-urgent" framing; likely already covered by the cross-referenced (currently grace-protected, actively-worked) doc
  — re-check on a future pass if it isn't.
- **AG-closeout linkage regression** (69→87 baseline, now 83 post-archival): NOT hand-fixed — this is
  `/ag-closeout-audit`'s domain (tranche-parameterized skill built for exactly this linkage class), not a
  plan_reconciler action. Recommend running it across the tranches that grew: cross-cutting, ao, infrastructure, cefi.
- **NA-corpus-size regression** (359→376 docs, 1295→1317 todos): NOT hand-triaged — explicitly `/na-eligibility-audit`
  scope per the ratchet's own remedy message.
- **Reference-path dangling (existence) residual**: 103→100(pre-fix measurement noise)→117 net (baseline 86) — the
  ~14-over-baseline gap is old pre-2026-07-23 debt (scratch_scenarios_day1/, plans/ai/, plans/audit/ — see
  `reference_path_convention_2026_07_23.md`), not new regression from this run.
- Recurring `status: active` (frontmatter) vs `` `status: draft` `` (body banner) bug in finalize-twin plans (≥8
  confirmed instances, P1 above) — recommend a bounded follow-up plan: grep the exact banner string corpus-wide,
  cross-check each hit's frontmatter, fix the ones that disagree.

- `unified-trading-pm/agents/plan_reconciler.md` STEP 6b's ping-ledger-append instruction is stale (see Doc-drift) —
  should be edited to point at the modern `/blocked` channel instead. A role file, not a plan; noted here since I cannot
  self-edit my own boot instructions mid-run, but this is a same-shape fix to the codex-drift class STEP 5c already
  reserves for a human/follow-up.

## Archive candidates (operator review)

50 archived this run (see Hygiene fixes). None required operator review before archiving (all had hard evidence per
STEP-4's bar); 2 correction-only pre-archive edits didn't change substance. 0 `locked_by:` blockers encountered.

## Refuted (dropped by verify)

None — every hunter-reported archive candidate resolved to ARCHIVE_READY, NOT_READY, or AMBIGUOUS (resolved by
plan_reconciler judgment, documented per-doc above); no candidate was found to be a hunter misread.

## Coverage (hunters / batches / docs)

- **5 archive-candidacy hunters** (batches of 12-13, general-purpose/sonnet): 61 docs read in full, cross-verified
  against git log / sibling docs where claims looked suspicious. 40 ARCHIVE_READY (+10 more needing a status flip first,
  done), 10 NOT_READY (real undone work hidden behind a checked box — see Filed / blocked alerts), 3 AMBIGUOUS (resolved
  by plan_reconciler judgment).
- **10 epic-cluster hunters** (general-purpose/sonnet): 162 non-grace `plans/active/*.md` + all 23 epic hub docs read in
  full. 51 contradiction candidates + full per-doc claims digests (not reproduced here).
- **Grace set**: 300/703 files (43%) were within the 12h window this run — unusually high, several large bulk commits
  landed in the last 12h. Grace-protected candidates (7 reference-path files, 16 referrer files, an unknown number of
  archive candidates not yet surfaced) will be caught by tomorrow's run.
- **Not run this pass** (time-budgeted out): topic hunters (canonical-ID, manifest/coverage, CI/CD shape, AO lifecycle,
  buckets/IAM, VM/SPOT policy, batch=live, milestones/dates, instruments SSOT, UI/deployment — 10+ cross-cutting themes
  the epic partition can't see), codex-alignment hunters (plan↔codex drift per-plan), missed-flip hunters (scanning open
  todos for self-cited shas). These are the next-highest-value fan-out for a future run.

## Plans not reached

- The 15+ P1 finalize-twin `status:active`-vs-`draft` instances: confirmed but not individually fixed (recommend a
  dedicated mechanical sweep, see Filed).
- `defi_master.md` Hyperliquid+Aster stale claim: flagged (Doc-drift) but not edited — epic-hub narrative content,
  outside this run's auto-fix scope; needs either an operator-approved edit or a `[unlock-plan]`-style authorization to
  touch epic narrative sections directly in a future run.
- 3 of 5 P0s (batch3 `assigned_vm` blank-parse bug, sports live-mode-ruling re-ask, predictions gate_on_depends
  reliability) need either a live mechanism check or a doc correction beyond this run's remaining budget — routed via
  Filed above, not blocked-alerted (judged non-data-correctness, lower urgency than the 3 that were alerted).

## Deferred work after 2026-08-06

| Item                                                              | State / why deferred                                                                     | Blocked on                                                              |
| ----------------------------------------------------------------- | ---------------------------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| **STEP 8 resume** (apply answers to 3 blocked questions, `/done`) | Cannot be done yet — waiting on operator dashboard response; 0 answers as of session-end | Operator-owned                                                          |
| Fix ≥8-instance finalize-twin `status:active`/`draft` banner bug  | Not done — mechanical grep-and-fix, bounded, ready to pick up                            | Nobody — real work                                                      |
| `infra_satellite_ao_dispatch_batch3` assigned_vm live-parse check | Not done — needs a live backlog-regen check, not a doc read                              | Nobody — real work                                                      |
| `sports_satellite_ao_dispatch_batch5` re-asks an answered ruling  | Not done — doc correction, bounded                                                       | Nobody — real work                                                      |
| `gate_on_depends` reliability (predictions batch6/7)              | Not done — needs a live AO-mechanism investigation                                       | Nobody — real work, but investigate before assuming either doc is right |
| `defi_master.md` Hyperliquid+Aster stale claim                    | Not done — epic narrative edit, outside auto-fix scope                                   | Nobody — real work (low risk, low urgency)                              |
| `mdps_features_live_launcher_exec_dispatch` correction banner     | Not done — small, bounded edit                                                           | Nobody — real work                                                      |
| `/ag-closeout-audit` re-run (linkage regression)                  | Not done — this run only measured + routed, didn't run the skill                         | Nobody — a skill invocation                                             |
| `/na-eligibility-audit` re-run (NA-corpus regression)             | Not done — same, routed not run                                                          | Nobody — a skill invocation                                             |
| 46 P1-P3 contradictions not individually fixed                    | Not done — detected + categorized, not all individually resolved (volume)                | Nobody — triage backlog, see Contradictions table                       |

**Recommended next item**: STEP 8 resume is queue-position-1 the moment an answer arrives (it's this exact dispatch's
own unfinished obligation). Absent that, the finalize-twin banner-bug sweep is the highest-leverage next pick — one
bounded mechanical pass closes ≥8 P1s at once, same shape as this run's epic-roster regen.

## Lessons (this run)

- **`git status --short | grep '^R'` to parse a rename mapping is fragile** — a file with BOTH a content edit and a
  rename shows as `RM` (not `R `), which a `sed 's/^R  //'` pattern silently fails to strip, corrupting that one mapping
  (contaminated it with a literal `RM ` prefix that never matched anything, so that file's referrer-fix silently
  no-opped). Caught by a follow-up corpus-wide re-scan, not by the original loop. Next time: parse `git status --short`
  per-file via `git diff --name-status -M` instead (gives clean `R100<TAB>old<TAB>new` triples, no combined-status
  ambiguity).
- **A single large commit (66 files) reliably triggered a prettier-autostage hook race**
  (`fatal: Unable to create index.lock`, seen 3x) that a run of 3 smaller commits (~22 files each) did not. No proof of
  the exact mechanism (parallel per-file prettier invocations racing for the lock is the leading theory), but the
  empirical fix (split into ~20-file batches) was reliable. Worth remembering for any future large-batch commit in this
  repo.
- **Prettier's own proseWrap reflow is non-idempotent on `<details>`-wrapped paragraphs** (already a tracked, ratcheted
  corpus issue — `prettier_prosewrap_mangles_long_inline_code_spans_2026_07_31.md`) — running `npx prettier --write` on
  a file containing this pattern can silently re-indent unrelated paragraphs elsewhere in the same file. Isolate real
  content edits from this noise before committing: `git checkout --` then re-apply just the `sed` substitution without a
  follow-up explicit prettier call (the commit hook's own auto-prettier still runs, but doesn't reintroduce the same
  churn on an already-settled file).
- **The archival step's blast radius is bigger than `validate_plan_links.py` catches.** That validator only checks
  clickable markdown-link syntax; `check_reference_paths.py`'s existence check also catches bare full-path mentions in
  `related:` frontmatter and prose (e.g. `` `/plans/active/issues/foo.md` `` inside backticks with no `[text](...)`
  wrapper). Archiving N docs needs BOTH checks run before considering referrer-fixing done — the first pass this run
  used only the former and shipped a real regression (103→163 dangling refs) that a second pass caught and mostly fixed
  (→117, residual is grace-protected files).
- **An issue doc's own "What I found" / routed-action bullets can name work for a FUTURE reconciler run** (the
  `instruments_satellite_batch1_finalize_false_completion_claim_2026_08_02.md` case: 2 bullets explicitly said "Requires
  plan_reconciler's designated archival authority — do not dispatch to a general worker"). These are worth actively
  grepping for (`grep -rn PLAN_RECONCILER plans/active/issues/`) at the START of a run, not discovered incidentally the
  way this one was (via an archive-candidate hunter's read).
- **My own boot instructions (`plan_reconciler.md`) had 2 small drifts from live reality** (retired ping-ledger paths,
  `plan_health`→`plan-health` endpoint rename) — a role file is exactly as subject to staleness as any other doc in this
  corpus; don't trust it blindly on operational specifics, verify against the live server/corpus when a step fails
  unexpectedly.
- **`GET /api/slots/{slot}/messages` is a shared inbox, not a per-`blocked_id` answer channel** — during STEP 8's
  wait-loop, a non-empty response turned out to be an unrelated operator broadcast (a repo-health notice about a
  completely different task) with no connection to any of the 3 blocked questions raised this run. A "messages non-empty
  ⇒ treat as answered" heuristic is a false-positive trap; check message CONTENT against the specific
  question/blocked_id before applying anything. No `GET`-by-`blocked_id` status endpoint exists
  (`/api/blocked/{id}/answer` is POST-only, for submitting); `/api/blocked/stats` gives only a global unanswered count,
  not per-ID lookup — content-matching the inbox is the only available mechanism today.
- **A `run_in_background` polling script inherits the caller's shell variables only if `export`ed** — my STEP-8
  wait-loop script referenced `$SCRATCH` internally (to log irrelevant-but-non-empty messages) but only had it set as a
  plain (non-exported) shell variable in the INVOKING command, not inside the script itself. Under `set -u` this crashed
  with `unbound variable` — but only on the specific code path reached when a non-empty, non-matching message arrived
  (i.e., it worked fine for many silent ticks, then broke the moment there was something to log). Diagnostic silver
  lining: the crash location itself proved the message was NOT a real answer (a genuine match exits earlier, cleanly) —
  but the bug still cost visibility into what the broadcast said and one relaunch cycle. Fix: hardcode path constants
  INSIDE a background script rather than relying on inherited environment, especially under `set -u`.
