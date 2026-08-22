---
doc_type: issue
title: >-
  Sports tranche closeout-audit findings (2026-08-16) — 77-doc Phase-1 sweep, 24 genuine orphans found, 10 items
  extracted to batch14, 27 findings parked below (25 residual-work items + 2 investigation notes); 2 mistags
  investigated (1 fixed in-run, 1 left genuinely uncertain); 1 mechanical checkbox reconciled on sight
summary: >-
  Filed by the scheduled `/ag-closeout-audit sports` run 2026-08-16 (Phases 0-3, dispatch agt-6704de, slot 24).
  `generate_ag_closeout_audit_candidates.py --tranche sports` returned `total_members=77`; 18 were deterministically
  excluded as genuinely multi-AG broad-coordinator docs (3+ real peer tranches besides sports), 2 borderline dual-tag
  docs were resolved by direct read without spawning an agent (1 genuinely dual-scope and self-dispatched, 1 whose
  sports-relevant work is already done), leaving 57 for a full Phase-1 `Workflow` fan-out (one agent per doc, 0
  errors, 0 empty results — though 1 result's `reasoning` field was the literal string "test", independently
  re-verified by direct read; its verdict happened to be correct). Verdicts: 4 `archivable_now`, 19
  `archivable_after_planned_work`, 3 `exclude_cross_cutting`, 5 `orphaned_partial_coverage`, 26
  `orphaned_never_touched` — 31 orphan-shaped verdicts, of which 7 are formally self-dispatched
  (`assigned_vm: planning`, status active/open) and excluded from the orphan count per the tooling's own definition,
  leaving **24 genuine orphans**. Phase 3's conflict-check (per
  `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` §3) found 10 source docs' remaining
  items were both bounded and conflict-clear today — extracted into
  `sports_satellite_ao_dispatch_batch14_2026_08_16.md` (`status: draft`) + a gated `_finalize` twin. The other items
  are parked below by taxonomy category.

  **Ledger**: 24 genuine orphans - 6 fully closed by batch14 (footystats_matches_predictions_fetch_gaps,
  sports_catalogue_reroll_2019_corpus_scale_killed, sports_cf8_available_at_backfill_regression,
  sports_odds_horizon_bucket_reader_writer_path_mismatch_defeats_zombie_purge, sports_track_o_attempted_at_keys_extinct,
  sports_taxonomy_p2_consumer_inventory) = 18 docs with residual/untouched work, several split into multiple parked
  items. Plus 7 self-dispatched-but-stalled docs, 1 stalled sibling-skill run, and 2 mistag-investigation notes.
  `parked_findings=27`, `entries_written=27` — balanced (25 taxonomy-tagged residual-work entries + 2 investigation
  notes; 2 further findings were resolved in-run and are recorded as prose only, not counted in this tally per the
  skill's "informational/fixed-in-run is not a todo" rule).
status: superseded
nature: issue
asset_group: [sports]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [sports, ag-closeout-audit, orphan-audit, plan-hygiene]
related:
  [
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/active/sports_satellite_ao_dispatch_batch14_2026_08_16.md,
    /plans/active/sports_satellite_ao_dispatch_batch14_2026_08_16_finalize.md,
    /plans/archive/2026_08/issues/ag_closeout_audit_sports_parked_2026_08_09.md,
    /plans/active/issues/sports_af_completion_pass_2026_08_10.md,
    /plans/active/issues/prediction_betfair_lay_price_adapter_scaffold_deleted_2026_08_09.md,
    /plans/active/issues/sports_fixtures_object_wrong_schema_instrument_catalog_contamination_2026_08_09.md,
    /plans/active/issues/sports_fast_t1_recon_oom_live_capture_outage_2026_08_01.md,
    /plans/active/issues/sports_odds_api_scattered_multiyear_gaps_2026_07_27.md,
    /plans/active/sports_track_h_denominator_gated_2026_07_28.md,
    /plans/active/sports_track_h_denominator_prereqs_2026_07_28.md,
    /plans/active/issues/plan_reconciler_findings_sports_2026_08_18.md,
    /plans/archive/2026_08/issues/ao_park_wiring_dropped_repeats_premature_gated_dispatch_2026_08_11.md,
    /plans/active/issues/dp_vm_001_expected_universe_halt_safety_false_page_2026_08_07.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: 2026-08-16
author: unknown
parent_epic: sports_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.12
assigned_role: data_engineering
drift_direction: none
depends_on: []
source:
  [
    "Scheduled /ag-closeout-audit sports run 2026-08-16 (ag_closeout_auditor, slot 24, dispatch agt-6704de). Operator
    was not interactively present during the run, so all judgment-relevant items below are parked rather than
    guessed.",
  ]
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by: ag_closeout_audit_sports_parked_2026_08_21
context_scope: [/cursor-configs/skills/ag-closeout-audit/SKILL.md, /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md, /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md, /scripts/plan-hygiene/generate_ag_closeout_audit_candidates.py]
---

> **📦 ARCHIVED 2026-08-22 (archival pass 2) — SUPERSEDED** by the 2026-08-21 re-run of the same audit
> (`ag_closeout_audit_sports_parked_2026_08_21.md`, itself already archived —
> `plans/archive/issues/ag_closeout_audit_sports_parked_2026_08_21.md`). 0 open todos, no lock. Kept as a
> historical audit-run record.
# Sports closeout-audit findings, 2026-08-16

## Finding 1 — one mistag fixed in-run, one left genuinely uncertain

**`ao_park_wiring_dropped_repeats_premature_gated_dispatch_2026_08_11.md` was a confirmed mistag — retagged in-run.**
Tagged `asset_group: [sports, meta]` but its content is 100% agent-orchestrator dispatch/`auto_park` internals
(`parent_epic: infrastructure_master`, `context_scope` = `agent-orchestrator/server/{auto_park,dispatch}.py`, and its
own `tags:` field already listed `ao`) — "sports" reflected only the triggering symptom (a sports todo's 3rd
premature dispatch), not real scope. Retagged to `asset_group: [ao]` directly (mechanical, evidenced, per the skill's
"fix in-run" rule) — `unified-trading-pm` uncommitted as of this doc; ships in the same turn as this report.

**`dp_vm_001_expected_universe_halt_safety_false_page_2026_08_07.md` is a LIKELY mistag, NOT fixed — genuinely
uncertain which tranche it belongs to.** Tagged `asset_group: [meta, sports]`, `parent_epic: observability_master`.
Content is a fleet-wide `exit_code_fleet_monitor.py` alert-routing carve-out (the VM that triggered it happened to be
`expected-universe-v2-sports-*`, but the fix and the underlying mechanism are asset-group-agnostic — its own
`related:` list cites a sibling DeFi doc with the same alert-class problem). Candidate replacement tag is `ao` or
`infrastructure`, but this run could not confidently pick between the two from `observability_master`'s scope alone.
**Not retagged — flagging for the `ao` or `infra` tranche's own run to investigate and correct**, rather than
guessing wrong.

## Finding 2 — one Phase-1 agent result was malformed; independently re-verified by direct read

The agent auditing `mdps_sports_e2e_checker_measured_root_mismatch_odds_horizon_bucket_2026_08_10.md` returned a
structurally valid but content-empty result: `"reasoning": "test"`. Did not trust it — read the doc directly. All 3
todos are `[x]`, and the doc's own frontmatter already carries `archive_exempt: true # all todos done; archival
follows after /done (worker.md combine rule)`. **The `archivable_now` verdict was independently confirmed correct**
despite the garbage reasoning field — noting this for the record as a Workflow-tool reliability data point, not
because it changed the outcome.

## Finding 3 — one mechanical checkbox reconciled in-run (2-day-old shipped fix, missed by 2 subsequent audit passes)

`sports_odds_bookmaker_coverage_enumeration_2026_06_20.md`'s P1 Todo 2 (`EXPECTED_BOOKMAKER_MARKET_SETS` 28-league
extension) was still `- [ ]` and described by 2 prior audit passes (na-eligibility-audit 2026-08-08, ag-closeout-audit
2026-08-09) as "a genuine unresolved either/or design fork." Verified: `unified-api-contracts@6d72669b`
(2026-08-06T23:41:40Z, confirmed ancestor of `origin/live-defi-rollout`) already resolved it — via a hybrid of BOTH
named options (6 leagues extended into `tier_1_domestic`, 2 into `tier_2_domestic`, 13 zero-coverage leagues into a
new `no_expectation` tier), predating both audit passes that still called it open. Flipped in-run with full evidence
(see that doc's own Progress Log / todo text). The doc's OTHER open todo (P2, `trades` cluster-validation gap) is
still a genuine unresolved fork — untouched, still parked below (see "Parked — operator-gated").

## Batch 14 — what was extracted (10 items, 11 source docs)

See `sports_satellite_ao_dispatch_batch14_2026_08_16.md` for full detail. Headline: adjudicate a footystats
fetch-gap; relaunch a rightsized VM for a scale-killed catalogue rebuild; execute an already operator-authorized CF-8
targeted backfill; fix a checker/export mismatch for 3 named dates; repair Track O `attempted_at` keys; fix a
ml-service venue-misclassification bug; fix an instruments-service `league_id`-resolution bug; run a live manifest
census; close 3 bounded honest-coverage items; harden the MDPS SPORTS staleness guard.

## Self-dispatched but effectively stalled (7 docs, NOT orphan-counted, NOT batch candidates)

These are formally `assigned_vm: planning` / status active-or-open — the tooling's own definition says a
self-dispatched doc covers itself, so none of these count toward the 24-orphan headline and none were considered for
batch14 (drafting a new todo would duplicate their own live dispatch). Surfacing because each Phase-1 agent
independently found real evidence of staleness or blockage worth operator awareness:

- **`sports_af_completion_pass_2026_08_10.md`** — dense Progress Log through 2026-08-11, but the doc's own newest
  entry (2026-08-16, today) states verbatim "no worker has checked in on this task in 5 days." Remaining: verify
  current live state (STANDINGS VM + chain automator), complete the ~716-object tail, re-census, unpark the archived
  predecessor gate.
- **`prediction_betfair_lay_price_adapter_scaffold_deleted_2026_08_09.md`** — genuinely `[BLOCKED-CREDENTIALS]`, not
  stalled-by-neglect: the Betfair account is in `ACCOUNT_PENDING_PASSWORD_CHANGE`; needs the account holder to change
  the password via betfair.com, then update the GSM `betfair-password` secret, before any worker can proceed.
- **`sports_fixtures_object_wrong_schema_instrument_catalog_contamination_2026_08_09.md`** — gated on
  `sports-schema-census-instruments-store-20260809-224053`, a VM whose own stated ETA (~8h) passed 7 days ago.
  Remaining: check the VM's actual terminal state (likely already `NOT_FOUND`/dead), download or re-launch, fold
  results into the enumerate-scope + remediate checkboxes.
- **`sports_fast_t1_recon_oom_live_capture_outage_2026_08_01.md`** — self-dispatch gone quiet since 2026-08-10.
  Remaining: P3 live-verify a freshness-skip demotion reaches live capture (deploy-dependent); P1 backfill the
  2026-07-27/28/30/31(+08-02+) gap — last measured at only 25.3%-56.7% reachable coverage, explicitly "NOT met."
- **`sports_odds_api_scattered_multiyear_gaps_2026_07_27.md`** — an intense ~2-week campaign (635→277 missing days)
  went quiet 2026-08-12T01:09Z; the VM fleet (`mtds-backfill-odds-*`) has been empty since, unactioned for ~4 days as
  of today. Remaining: relaunch to a genuine 0-gap terminal state (277/2258 days still missing), then re-run the
  gap census.
- **`sports_track_h_denominator_gated_2026_07_28.md` + `sports_track_h_denominator_prereqs_2026_07_28.md`** — same
  underlying blocker, **CARRIED from the 2026-08-09 report, now 18 days unresolved (2026-07-29 →)**: an
  `[OPERATOR]`-tagged design fork on the MDPS `odds_horizon_bucket` reprocess (Path A — teach
  `reprocess_sports_odds.py` to canonicalize `league_id` inline, needing a cross-repo sourcing decision — vs. Path B
  — wait for the raw `batch_odds_api` old-object delete to land first). No ruling yet; both docs' own dispatch is
  machine-held on this fork, not neglected.

## Parked — operator-gated (8 items, no evidence-based tiebreaker available)

- **`sportradar_credential_ask_2026_08_09.md`** — decide Sportradar's intended scope (schedule/results vs. odds
  cross-check redundant with existing Odds-API/footystats) before subscribing; registration work itself is further
  `BLOCKED-CREDENTIALS` (needs `sportradar-api-key`) behind that decision.
- **`sports_cf8_out_of_window_mechanism_reconciliation_2026_08_16.md`** — remediation policy for the 2026-07-13
  cluster's "blank from birth" gap (14,656 `odds_horizon_bucket` rows never captured by the old v8-index-blind
  rebuild): accept as-is (safe to leave) vs. commission a real backfill recovering true timeframe from source data.
- **`data_completion_sports_2026_07_24.md` item 2** — API-Football daily-quota bump to 1.5M/day: the branch is
  already RULED (2026-07-28), but the vendor account-tier upgrade + spend itself is unexecuted, appearing only in
  Deferred/time-gated sections of batch9/batch10 with no dispatchable claim anywhere.
- **`sports_odds_data_type_casing_wider_than_odds_api_2026_08_15.md` item 2** — operator ruling on whether to fully
  rewrite every remaining uppercase `data_type` writer vs. accept the ecosystem's existing case-insensitive
  normalization as sufficient (item 1, the live census informing this decision, IS extracted — batch14 todo 8).
- **`sports_honest_coverage_gap_closure_2026_08_14.md` item 5** — operator decision needed on 72,955 genuine-gap
  `api_football` cells from the FIXTURES_OUTCOMES backlog dry-run (items 1/2/4 ARE extracted — batch14 todo 9).
- **`sports_league_id_namespace_migration_2026_07_20.md`** — Track H (same blocker as the self-dispatched pair
  above, CARRIED) + STEP 9's human-gated delete of ~256,954 old non-canonical `league_id` objects (its live-writer
  pre-check is now dispatched via today's `sports_venue_vocab_and_league_id_delete_ao_dispatch_2026_08_16.md` — the
  2026-08-09 report's own recommendation to fold this in appears to have already been acted on; the delete itself
  stays human-gated). Only the doc's independent per-fixture `league_id`-resolution bug is extracted (batch14 todo
  7).
- **`sports_predictions_live_mode_activation_readiness_2026_07_21.md` item 6** — the permanent human go/no-go for
  real-capital sports/prediction live trading. Standing hard-stop, not a new finding.
- **`sports_odds_bookmaker_coverage_enumeration_2026_06_20.md` — P2 Todo 4** — decide+implement the `trades`
  cluster-validation gap (register `trades` in `BUNDLED_DATA_TYPES` for live enforcement vs. formally accept the
  static-audit-only gate). **CARRIED, still genuinely open** — this is the doc's OTHER fork, distinct from the one
  Finding 3 above resolved today. Doc stays `locked_by: live-defi-rollout`, do-not-archive-without-ruling.

## Parked — time-gated (2 items, waiting on a clock or an in-flight process, not a decision)

- **`mtds_odds_backfill_watchdog_kill_after_silent_hang_2026_08_08.md`** — **CARRIED**: item 1 (opportunistic
  live-SSH/py-spy capture of a hang in progress) isn't a clean bounded batch item — only actionable if someone
  happens to be watching at the right moment; item 2 (decide a `PREFIX_IDLE_THRESHOLDS` override vs. a fetch-timeout
  fix) is self-gated on a still-unconfirmed root cause, less settled after the 2026-08-15/16 entries found a possibly
  distinct zero-log-output failure variant.
- **`sports_cf8_captured_backfill_timeframe_dropped_2026_08_15.md`** — the full CF-8 captured-row backfill (MDPS
  ~285K rows, IS ~458K rows) + bundled CF-3/CF-4 cleanup (3,833 rows) is deliberately deferred pending a dedicated,
  reviewed maintenance window — not extracted as a casual batch todo given the scale.

## Parked — dependency-gated (1 item, blocked on a specific other in-flight item)

- **`sports_live_arb_strategy_and_execution_routing_2026_08_14.md`** — all 16 items are machine-gated
  (`gate_on_depends: true`) on `venue_capability_route_axis_and_cross_ag_declarations_2026_08_14` and
  `mtds_sports_live_arb_feeds_sharpapi_oddsapiio_unity_2026_08_14` (itself parked below, too-large), neither landed
  as of this doc's own 2026-08-14 Progress Log.

## Parked — too-large-or-risky for a batch todo (3 items, needs its own scoped pass)

- **`sports_halftime_odds_sfi_vs_inplay_2026_07_16.md`** — **CARRIED from 2026-08-09**: the 2,436-T-0-shard manifest
  reconciliation's stated blocker is confirmed stale, but a sibling `na-eligibility-audit` finding recommends a
  scoped implementation plan first, citing 2 prior regressions of the same manifest/consolidator machinery. Still
  no scoped plan exists.
- **`mtds_sports_live_arb_feeds_sharpapi_oddsapiio_unity_2026_08_14.md`** — 16 open P0-P2 items describing a
  coherent new-feature build (UAC schema, connector base classes, provider-preference resolver, live-axis flip,
  launcher). This reads as standalone multi-step architecture work, not a grab-bag of residual fixes — recommend
  the operator consider a deliberate `assigned_vm: planning` flip of the whole doc (with `sequential:`/`depends_on`
  as needed) rather than cherry-picking pieces into a future batch.
- **`sports_features_calculator_correctness_audit_2026_08_12.md`** — the doc itself is `status: draft` (11 todos,
  a systematic ML-calculator correctness audit). Extracting pieces from an unreviewed draft plan is premature;
  needs operator review to decide whether/how to activate it first.

## Parked — bounded but not extracted this round (5 items, good future-batch candidates)

- **`sports_predictions_live_mode_activation_readiness_2026_07_21.md` item 1** — relaunch the sports live-odds MTDS
  VM (measured DOWN 2026-08-15, warm-sink >4h stale) + re-verify a live poll cycle. Bounded (a relaunch pattern), not
  included in this batch's cut for volume reasons — a clean batch15 candidate.
- **`sports_predictions_live_mode_activation_readiness_2026_07_21.md` item 2** — execute the promote-workflow CLI
  chain (>=7 days paper, then live). Recommend explicit operator kickoff rather than an autonomous batch todo, given
  it is a real promote-pipeline entry point (even though paper, not live-capital) and this run could not confirm
  staffing/monitoring readiness for a week-long unattended run.
- **`sports_features_layer_findings_sweep_2026_07_18_part2_2026_07_26.md` item 1 (§M)** — api-football fleet
  runtime/mid-flight rate re-division. Design-gated per `sports_satellite_ao_dispatch_batch9_2026_08_04.md`'s own
  Deferred ledger; not newly actionable (CARRIED framing from batch9).
- **`sports_features_layer_findings_sweep_2026_07_18_part2_2026_07_26.md` item 3 (G-ops)** — per-launcher
  `lc_write_launch_params` rollout for exact venue-scope replay + `VM_FORCE` persistence. Bounded, simply not
  selected for this batch's cut — a clean batch15 candidate.
- **`sports_odds_writer_flip_and_trades_path_retirement_2026_08_15.md`** — Phase 1's regression-verify is
  narratively declared "100% complete" but never independently evidenced in-doc; Phases 2-3 (6 more items, including
  1 `[OPERATOR]`-gated delete) are sequenced behind it. This run could not independently re-verify Phase 1's claim
  without a live deploy-state check outside its scope — recommend that check first, then re-triage.

## Special finding — a sibling skill's own run never concluded

- **`plan_reconciler_findings_sports_2026_08_16.md`** — this is not sports CONTENT work; it's an incomplete
  `/plan-reconcile sports` run (Wave-1 hunter findings dispatched but never aggregated back; doc still `status: open`,
  `resolved_by` empty, `locked_by: agt-2be768` with no release/summary). Not a batchable content fix — recommend
  re-running `/plan-reconcile sports` to conclude it, not folding into this skill's batch.

## Codex SSOTs

- `/cursor-configs/skills/ag-closeout-audit/SKILL.md` — this run's procedure (Phase 0-3), the non-batchable taxonomy,
  and the "parked findings always get a durable issue doc" rule this doc satisfies
- `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` §3 — the conflict-check protocol
  behind every "Conflict-check findings" note in `sports_satellite_ao_dispatch_batch14_2026_08_16.md` and every
  dependency-gated entry above

## Progress Log

- **ag-closeout-audit sports 2026-08-16 (dispatch agt-6704de, slot 24)**: Phase 0-3 run. 77 candidates, 21 covering
  docs, 18 broad multi-AG docs deterministically pre-excluded, 2 dual-tag docs resolved by direct read, 57 sent to a
  Phase-1 `Workflow` (0 errors). 24 genuine orphans found (31 orphan-shaped verdicts minus 7 self-dispatched). 10
  items extracted into `sports_satellite_ao_dispatch_batch14_2026_08_16.md` (draft) + gated finalize. 1 mistag fixed
  in-run (`ao_park_wiring...` → `[ao]`), 1 left uncertain for a future run. 1 stale checkbox reconciled in-run
  (`sports_odds_bookmaker_coverage_enumeration_2026_06_20.md` P1 Todo 2, 2-day-old shipped fix missed by 2 prior
  audit passes). 25 taxonomy-tagged residual-work entries + 2 investigation notes parked below (`parked_findings=27`,
  `entries_written=27` — balanced).
- **context-scout 2026-08-17**: populated/refreshed context_scope (4 entries)
- **na-eligibility-audit 2026-08-17** [body-hash:e84253640409296d]: KEEP-NA, valid — 0 open todos (this is a
  findings/parked-work ledger doc, not a checkbox-tracked plan); independently reconfirmed via a fresh full read,
  consistent with the doc's own self-framing ("informational/fixed-in-run is not a todo"). One secondary note (not
  this doc's own fix): Finding 1 names a likely `ao`/`infra`-tranche mistag on a different doc
  (`dp_vm_001_expected_universe_halt_safety_false_page_2026_08_07.md`) that needs that tranche's own future run to
  directly re-read and correct — flagged here for visibility, not actioned by this pass.
