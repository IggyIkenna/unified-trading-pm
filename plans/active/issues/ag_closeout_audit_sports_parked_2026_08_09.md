---
doc_type: issue
title: >-
  Sports tranche closeout-audit findings (2026-08-09) — 47-doc Phase-1 sweep, 28 orphans found, 4 items extracted to
  batch12, 26 docs' remaining work parked below by taxonomy; 2 doc-hygiene fixes applied directly (stale odds_api "not
  yet launched" framing); 1 mistag investigated and confirmed correctly non-sports by a same-day sibling run
summary: >-
  Filed by the scheduled `/ag-closeout-audit sports` run 2026-08-09 (Phases 0-3, dispatch agt-7a1017, slot 14).
  `generate_ag_closeout_audit_candidates.py --tranche sports` returned `total_members=62`; 15 were deterministically
  excluded as genuinely multi-AG broad-coordinator docs (peers >= 3 other real asset_groups, e.g.
  `ag_closeout_audit_rollout_2026_07_25.md`), leaving 47 for a full Phase-1 `Workflow` fan-out (one agent per doc, 0
  errors). Verdicts: 3 `archivable_now`, 13 `archivable_after_planned_work`, 3 `exclude_cross_cutting`, 9
  `orphaned_partial_coverage`, 19 `orphaned_never_touched` — 28 genuine orphans. Phase 3's conflict-check (per
  `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` §3) found only 4 source docs' remaining
  items were both bounded and conflict-clear today — extracted into `sports_satellite_ao_dispatch_batch12_2026_08_09.md`
  (`status: draft`) + a gated `_finalize` twin. A deeper read surfaced a live-VM conflict that would have made 2 more
  items look extractable by mistake (see Finding 1) — fixed directly in their source docs instead of batched. The other
  26 orphaned docs' remaining work is parked below by taxonomy category, none newly actionable from this tranche today.

  **Ledger**: 28 orphaned docs - 2 fully covered by batch12 (sports_clv_target_builder_family_route_likely_same_pit_gap,
  sports_manifest_consolidator_zero_growth_stall) = 26 parked entries below. `parked_findings=26`, `entries_written=26`
  — balanced.
status: open
nature: issue
asset_group: [sports]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [sports, ag-closeout-audit, orphan-audit, plan-hygiene]
related:
  [
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/active/sports_satellite_ao_dispatch_batch12_2026_08_09.md,
    /plans/active/sports_satellite_ao_dispatch_batch12_2026_08_09_finalize.md,
    /plans/active/issues/sports_odds_api_scattered_multiyear_gaps_2026_07_27.md,
    /plans/active/issues/sports_batch_odds_api_capture_outage_recurrence_check_2026_07_26.md,
    /plans/active/issues/sports_all_vendor_honest_coverage_convergence_2026_08_07.md,
    /plans/active/sports_prediction_mvp_writetime_precompute_2026_07_24.md,
    /plans/active/issues/sports_af_full_entity_completion_2026_08_03.md,
    /plans/active/issues/sports_odds_markets_outcomes_settlements_arbitrage_expected_since_2024_zero_captured_2026_07_24.md,
    /plans/active/issues/transfermarkt_player_values_data_discarded_2026_08_07.md,
    /plans/active/issues/sports_league_id_namespace_migration_2026_07_20.md,
    /plans/active/sports_track_h_denominator_prereqs_2026_07_28.md,
    /plans/active/issues/mtds_pipeline_check_enumerate_shards_masks_cefi_sports_mvp_2026_08_06.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: 2026-08-09
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
    "Scheduled /ag-closeout-audit sports run 2026-08-09 (ag_closeout_auditor, slot 14, dispatch agt-7a1017). Operator
    was not interactively present during the run, so all judgment-relevant items below are parked rather than guessed.",
  ]
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
context_scope:
  [
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /scripts/plan-hygiene/generate_ag_closeout_audit_candidates.py,
  ]
---

# Sports closeout-audit findings, 2026-08-09

## Finding 1 — a live-VM conflict almost produced 2 redundant batch todos (fixed directly, not batched)

`sports_odds_api_scattered_multiyear_gaps_2026_07_27.md`'s P1 and
`sports_batch_odds_api_capture_outage_recurrence_check_2026_07_26.md`'s P0 both read, on their own text, as "gates
cleared, ready to launch the odds_api backfill VM" — Phase 1 correctly flagged both as `orphaned_never_touched`. But a
direct read of `sports_all_vendor_honest_coverage_convergence_2026_08_07.md` (dispatched to a sub-agent given the
blast-radius of a wrong call here — duplicate VM launches burn real compute and risk a manifest-write race) showed the
guard-respecting single-VM launch already happened the same day as the first doc's "ready" note (`mtds-backfill-odds-1`,
2026-08-07T11:0XZ) and has since relaunched through a recurring silent-hang bug 9 times (`smallchunk`→`smallchunk9`),
live as of 2026-08-09T04:13Z at chunk 26/451.

**Action taken**: added a dated doc-hygiene note to both source docs (2026-08-09) pointing to the live tracker and
explicitly warning against a second launch; did NOT flip either checkbox (the reconciliation itself isn't done, only the
launch). No operator action needed — this was resolved by evidence, not a judgment call.

## Finding 2 — a likely mistag, investigated, confirmed correct by a same-day sibling run

`sports_prediction_mvp_writetime_precompute_2026_07_24.md` is filenamed with a `sports_` prefix but tagged bare
`asset_group: [cross-cutting]` — the Phase 0.3 filename-prefix heuristic flagged it as a likely "fork inherited the
parent's cross-cutting tag" mistag. Read in full: the doc's own design explicitly frames the schema bump as spanning
"every asset_group and every producer service" (not sports-specific), and
`plans/active/issues/ag_closeout_audit_prediction_parked_2026_08_09.md` (the prediction tranche's own same-day run)
independently read the same doc and concluded "confirmed genuinely cross-cutting... not a mistag." Deferring to that
finding rather than re-litigating or retagging — no action taken.

## Batch 12 — what was extracted (4 items, 4 source docs)

See `sports_satellite_ao_dispatch_batch12_2026_08_09.md` for full detail. Headline: prod-apply a shipped manifest
reconciliation script (1,298 `PLAYER_STATS` cells), re-run a features-service export to confirm a fix on real data, an
investigation todo (23 unexplained missing odds_api days), and the safe prep half of a legacy-GCS-delete (register a
launcher category + run a real dry-run census — the actual delete stays operator-gated).

## Parked — operator-gated (10 docs, no evidence-based tiebreaker available)

- **`sports_fixtures_schedule_wrong_schema_day_2026_04_14.md`** — decide whether to register 35 leagues with no
  canonical UAC registry entry as `LeagueDefinition`s, or rule to leave them unmapped. Options: (a) register all 35, (b)
  leave unmapped + document why, (c) triage per-league. No recommendation — genuinely needs someone with league
  ownership context.
- **`sports_odds_markets_outcomes_settlements_arbitrage_expected_since_2024_zero_captured_2026_07_24.md`** — the
  retire-vs-scaffold fix for 4 UAC capability entries is explicitly `BLOCKED-OPERATOR-DECISION` (`BLK-c545ae54`) —
  **filed 2026-07-24, still unanswered as of today (16 days)**. Recommend surfacing this one specifically — the root
  cause is already diagnosed and the fix is ready to execute the moment the ruling lands; it's aging on `/blocked` queue
  visibility alone, not genuine difficulty.
- **`transfermarkt_player_values_data_discarded_2026_08_07.md`** — pick a disposition for the PLAYER_VALUES write path
  silently discarding all value data before persistence: (a) persist per-player `market_value_eur`, (b) persist a
  team-level aggregate only, (c) rename the entity to reflect it's actually a roster index, (d) park. No recommendation
  stated in the source doc.
- **`mtds_sports_odds_api_force_fetch_no_parquet_2026_08_01.md`** — the-odds-api.com historical-endpoint key hit a clean
  401/quota-exhaustion cutover 2026-08-01T12:40:24Z; needs an operator credential check + quota top-up or key rotation.
- **`sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md`** (residual after batch12's prep todo)
  — once the real dry-run census in batch12 measures Part-5's twin-coverage proof, the actual `--drop-stale`/`--apply`
  firing for legacy sports GCS objects needs final operator sign-off (hard-stop #2, reversibility-qualified per §3a but
  not yet exercised for this specific population).
- **`sports_track_h_denominator_prereqs_2026_07_28.md`** todo 1 — undecided design fork on the MDPS
  `odds_horizon_bucket` reprocess: path A (canonicalize `league_id` pre-dedup via a cross-repo map-sourcing decision)
  vs. path B (wait for the separately-tracked raw-object delete). Filed `/blocked` by a prior session; no ruling yet.
- **`sports_odds_bookmaker_coverage_enumeration_2026_06_20.md`** — 2 forks: (a) extend `EXPECTED_BOOKMAKER_MARKET_SETS`
  to 28 unmapped `league_id`s vs. add a `tier_3_global`/no-expectation tier; (b) restore equivalent regression tests for
  a flagged test-deletion discrepancy vs. accept current coverage. Doc is `locked_by: live-defi-rollout` with an
  explicit do-not-archive-without-ruling banner.
- **`sports_features_layer_findings_sweep_2026_07_18_part2_2026_07_26.md`** §M — already-running api-football fleet VMs
  don't dynamically re-throttle when the fleet grows mid-flight; `sports_satellite_ao_dispatch_batch9_2026_08_04.md`
  already acknowledged this as deferred/operator-gated, not newly actionable.
- **`sports_predictions_live_mode_activation_readiness_2026_07_21.md`** todo 6 — the permanent human go/no-go for
  real-capital sports/prediction live trading. Reaffirmed by a dated 2026-08-08 operator banner; standing hard-stop, not
  a new finding.
- **`sports_fast_t1_recon_oom_live_capture_outage_2026_08_01.md`** — the AF-classification decision (`attempted_failed`
  vs. `empty_confirmed` for in-coverage expected-but-empty shards), filed `BLOCKED-OPERATOR-DECISION` 2026-08-06 (3 days
  aging).

## Parked — time-gated (5 docs, waiting on a clock or an in-flight process, not a decision)

- **`sports_odds_api_scattered_multiyear_gaps_2026_07_27.md`** P2 (census re-verify) +
  **`sports_batch_odds_api_capture_outage_recurrence_check_2026_07_26.md`**'s granularity-restoration residual +
  **`sports_all_vendor_honest_coverage_convergence_2026_08_07.md`**'s convergence confirmation +
  **`mdps_odds_horizon_bucket_shard4_residual_failures_2026_07_25.md`**'s Follow-up re-run — all 4 wait on the SAME live
  chain (`sports_all_vendor_honest_coverage_convergence_2026_08_07.md`'s `mtds-backfill-odds-*` VM, chunk 26/451 as of
  2026-08-09) reaching a genuine 0-gap terminal state. Re-check all 4 together once that chain finishes — do not
  re-triage individually before then.
- **`sports_stats_delayed_live_capture_still_dead_post_fix_2026_07_29.md`** — waits on the 2026-27 European season
  starting for BUNDESLIGA/EPL/LA_LIGA/LIGUE_1/SERIE_A (20+ prior re-checks, structurally unchanged since 2026-08-06).

## Parked — dependency-gated (5 docs, blocked on a specific other in-flight item, not a design call)

- **`footystats_matches_predictions_fetch_gaps_2026_07_08.md`** — blocked on the sibling fix in
  `footystats_matches_predictions_odds_pending_fetch_universe_expansion_2026_07_27.md` (itself
  `archivable_after_planned_work` — already covered elsewhere; re-check once that lands).
- **`sports_track_h_denominator_gated_2026_07_28.md`** + **`sports_track_h_denominator_prereqs_2026_07_28.md`** todo 2 —
  the honest-coverage denominator work is blocked on the prereqs plan, whose own todo 2 (footystats copy+swap,
  data-correctness already done) is blocked on an UNRELATED `market-tick-data-service` QG-red repo-blocker
  (`RB-166e706f`, empty-string-fallback ratchet). Checked live: a same-day-declared fix commit
  (`market-tick-data-service@69738677`, 2026-07-28) exists but this run could not confirm from the repo alone whether it
  actually cleared the ratchet baseline — needs a direct QG re-run on `market-tick-data-service` to confirm, not assumed
  here.
- **`mdps_sports_honest_absence_writes_fail_fetchevidence_gate_2026_08_01.md`** — its `[SCRIPT] P3` relaunch-and-confirm
  todo is explicitly sequenced after its own `[DATA] P2` fix, which is itself already claimed by an active
  `sports_satellite_ao_dispatch_batch9_2026_08_04.md` todo. Re-check once batch9 lands.
- **`mtds_odds_backfill_watchdog_kill_after_silent_hang_2026_08_08.md`** todo 4 — gated on batch11's timeout audit
  (already dispatched) landing first; its todo 1 (opportunistic live-hang catch via SSH/py-spy) isn't a clean bounded
  batch item either way (only actionable if someone happens to be watching at the right moment).
- **`sports_predictions_live_mode_activation_readiness_2026_07_21.md`** todo 5 — gated on the still-unshipped
  `sports_group_c_execution_backtest_harness_2026_07_21.md` (already `assigned_vm: planning`, in progress).

## Parked — too-large-or-risky for a batch todo (needs its own scoped pass) (2 docs)

- **`sports_halftime_odds_sfi_vs_inplay_2026_07_16.md`** — the 2,436-T-0-shard manifest reconciliation's stated blocker
  (an in-flight bucket cutover) is confirmed stale (cutover completed 2026-07-17), but that same doc's own
  `na-eligibility-audit 2026-08-09` entry (a sibling run, same day) explicitly recommends a scoped implementation plan
  before dispatch, citing 2 prior regressions of the same manifest/consolidator machinery in
  `sports_cf8_available_at_backfill_regression_2026_07_13.md`. Deferring to that caution.
- **`canonical_player_stats_fixture_events_quality_2026_07_16.md`** (residual after batch12's prod-apply todo) — Finding
  2's fixture_events schema-heterogeneity remediation is a 3-part effort (an idempotent player_stats dedup rewrite over
  ~13,964 cells, folding fixture_events re-fetch into a separate "OR-1 campaign" this run didn't investigate, and a new
  writer-side de-dup/schema-conformance gate) — prose-only, no single bounded "Done when," not a clean batch todo.
  Defect 3 (deciding the ONE `instrument_count` semantic across writer eras) is a genuine systemic design ruling the
  doc's own text says explicitly should NOT be resolved piecemeal by a per-plan agent.

## Parked — self-progressing (not a gap; already covered by its own live dispatch) (1 doc)

- **`/plans/archive/2026_08/issues/sports_manifest_2026_h1_vs_2025_h1_enumeration_grain_persists_2026_07_27.md`** —
  `assigned_vm: planning`, actively worked under its own steam (continuous Progress Log entries through 2026-08-08). A
  new batch todo here would duplicate its own already-live dispatch. Re-check on a future run if its Progress Log goes
  stale. **Update 2026-08-09: this doc completed its final todo and was archived same-day (all todos `[x]`, ratio
  confirmed resolved 3.13x→0.95x) — no further re-check needed.**

## Parked — not this tranche's write (2 docs, reported for the record; the fix belongs to a different tranche)

- **`mtds_pipeline_check_enumerate_shards_masks_cefi_sports_mvp_2026_08_06.md`** — `asset_group: [cefi, sports]`,
  `parent_epic: infrastructure_master`. Confirmed still-live bug: `pipeline_e2e_check.py`'s `enumerate_mtds_shards()`
  silently drops 110 real SPORTS MVP shards (and all CEFI ones) from an unfiltered `--mvp-only` sweep. Per the
  primary-owner-via-`parent_epic` rule, this is `infra`-tranche-owned, not sports' or cefi's write to make — reporting
  the orphan verdict here (it IS orphaned, no covering doc claims it), but NOT drafting a batch todo, to avoid two
  tranches racing the same file. Flagging for the `infra` tranche's own run to pick up.
- **`sports_league_id_namespace_migration_2026_07_20.md`** — its tracked remaining work (MDPS reprocess, footystats
  swap, Track H denominator) is already covered by the `sports_track_h_denominator_*` pair above (same gates). The
  genuinely NEW, untracked item is "the still-untracked human-gated final delete of ~256,954 old non-canonical objects"
  — a bulk delete at this scale needs the same reversibility-qualified treatment as the canonical-universe E8 item, not
  a casual batch todo; flagging for explicit operator awareness rather than silently leaving it untracked. Recommend:
  fold into a dedicated delete-safety pass once Track H's gates clear (the objects are the same migration's legacy
  remainder).

## Parked — special finding, worth direct operator attention (1 doc)

- **`sports_af_full_entity_completion_2026_08_03.md`** — `assigned_vm: planning`, so mechanically "self-dispatched" and
  not counted as an orphan by the tooling's own definition, but a real read shows it has been stalled ~24h+ (last
  Progress Log tick 2026-08-08T06:24Z) AND the doc itself is now at 1,001 lines — at/over the standard 1,000-line hard
  cap (`check_line_caps.sh`), which may be structurally blocking further self-driven Progress Log commits. Remaining
  work: launch the INJURIES all-leagues API-Football backfill (62,709 shards, never started) + a final P0 re-census.
  Recommend: a line-cap remediation split (extract the remaining Todos into a fresh, smaller doc, mirroring the pattern
  `sports_prediction_mvp_writetime_precompute_2026_07_24.md` used) before expecting further progress here — not done in
  this run (scoping which content to extract is itself a judgment call).

## Codex SSOTs

- `/cursor-configs/skills/ag-closeout-audit/SKILL.md` — this run's procedure (Phase 0-3), the non-batchable taxonomy,
  and the "parked findings always get a durable issue doc" rule this doc satisfies
- `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` §3 — the conflict-check protocol behind
  Finding 1 and every "Parked — dependency-gated"/"time-gated" entry above

## Progress Log

- **round-9 RECLASSIFY+satellite sweep 2026-08-09**: KEEP-NA, valid — reviewed same-day. This doc is a findings/triage
  ledger (0 checkboxes of its own by design — every referenced item's actual dispatchable work already lives as a
  tracked todo in its own named source doc; this doc records only the disposition). No new information surfaced this
  pass that would change any entry's taxonomy bucket. Cross-referenced against this sweep's own candidate docs: the
  operator-gated/dependency-gated verdicts recorded here for `footystats_matches_predictions_fetch_gaps_2026_07_08.md`,
  `mtds_odds_backfill_watchdog_kill_after_silent_hang_2026_08_08.md`, and
  `sports_predictions_live_mode_activation_readiness_2026_07_21.md` were independently confirmed still current when
  those docs were read directly this pass. Stays `assigned_vm: NA`.
- **2026-08-10 (prose-findings formalization sweep)**: full read for unconverted actionable prose — none found. Both
  named findings are already self-resolved within this doc's own text: Finding 1's "Action taken" already fixed the
  live-VM-conflict risk directly (a doc-hygiene note added to the 2 source docs, not a deferred recommendation) and
  Finding 2 concluded "no action needed" on its own evidence (mistag confirmed NOT a mistag by a same-day sibling
  run). Every entry in the "Parked —" taxonomy sections below either explicitly states "no recommendation" (the
  genuinely operator-gated design forks) or points at an already-tracked gate/doc elsewhere in the corpus — none
  contains a distinct, unconverted actionable claim of its own that isn't already one of those two states. 0 prose
  findings converted to new todos; 0 new already-resolved citations needed beyond what the doc already states.
- **na-eligibility-audit 2026-08-10 (formalized-docs follow-up, group 1 of 2)**: KEEP-NA, valid — not an ARCHIVE
  candidate. Standing triage ledger for 26 parked orphan docs across 6 taxonomy categories (operator-gated, time-gated,
  dependency-gated, too-large-or-risky, self-progressing, not-this-tranche's-write); 0 checkboxes by design (every
  item's actual dispatchable work lives at its own source doc). Reconfirmed unchanged by the same-tranche round-9
  RECLASSIFY sweep. Not locked. Doc stays `assigned_vm: NA`.
