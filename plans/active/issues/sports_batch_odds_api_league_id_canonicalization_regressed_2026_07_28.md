---
doc_type: issue
title:
  Raw `batch_odds_api` league_id canonicalization measured NON-canonical today (99,607 residual rows) — contradicts
  `sports_league_id_namespace_migration_2026_07_20.md`'s "STATUS 2026-07-25 ... re-applied and verified stable" claim;
  blocks the MDPS `odds_horizon_bucket` Step-7 reprocess from reaching its own done-when
summary: >-
  Dispatched to re-run the MDPS `odds_horizon_bucket` reprocess (Step 7 of the league_id namespace migration), whose own
  self-justification states "raw content is already canonical per the shipped `batch_odds_api` migration." A fresh,
  independent manifest census (same reader/method as the 2026-07-28 LIVE-PROBE in the parent migration doc, run twice
  from fresh Python processes) found the RAW `batch_odds_api` shape itself still carries 99,607 non-registry `league_id`
  rows (`instrument_type=odds`, `data_type=trades`, `capture_status=captured`, spanning 2020-06-06..2026-06-24 across
  1,580 distinct dates) — the same top-offender cast of characters as the original 2026-07-20 measurement
  (PREMIER_LEAGUE, CHAMPIONSHIP, PRIMERA_DIVISION, FIRST_DIVISION_A, 2._BUNDESLIGA, SUPER_LEAGUE, SUPERLIGA,
  PREMIERSHIP), just at roughly half the original 214,842-row scope. This directly contradicts the parent migration
  doc's "STATUS 2026-07-25" section, which reports the raw swap "re-applied and verified stable across 5 consolidator
  cycles" with no stated residual. Re-running Step 7's MDPS reprocess against this raw data would NOT reach the todo's
  own done-when (0 non-registry rows in `batch_mdps_odds_horizon_bucket`) — it derives its output partition from the
  raw content column, so a dirty raw input yields a dirty derived output. Declining to launch the multi-hour multi-VM
  reprocess job on this basis (a 3rd blind run of that exact job would repeat the already-flagged wasteful-duplicate-
  dispatch pattern from `mdps_odds_horizon_bucket_launch_prep_stale_todo_duplicate_dispatch_2026_07_27.md`) until the
  raw prerequisite is confirmed genuinely fixed.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [market-tick-data-service, market-data-processing-service, unified-trading-pm]
scope: [engineer]
tags: [sports, league-id, namespace, migration, manifest, data-correctness, ssot-contradiction, regression]
related:
  [
    /plans/active/issues/sports_league_id_namespace_migration_2026_07_20.md,
    /plans/active/sports_track_h_denominator_prereqs_2026_07_28.md,
    /plans/active/sports_track_h_denominator_prereqs_step7_gated_2026_07_28.md,
    /plans/active/sports_track_h_denominator_gated_2026_07_28.md,
    /plans/active/issues/mdps_odds_horizon_bucket_launch_prep_stale_todo_duplicate_dispatch_2026_07_27.md,
    /plans/active/issues/mdps_odds_horizon_bucket_shard4_residual_failures_2026_07_25.md,
    /plans/archive/issues/sports_league_id_swap_silently_reverted_toctou_2026_07_25.md,
  ]
created: 2026-07-28
source: >-
  sports_track_h_denominator_prereqs-001 (slot 12, 2026-07-28) — discovered mid-task, pre-launch verification of the
  Step-7 reprocess todo's own stated prerequisite ("raw content is already canonical")
assigned_vm: planning
parent_epic: sports_master
execution_scope: orchestrator-agent
priority: P1
estimate_class: research
assigned_role: data_engineering
resolved_by:
locked_by:
drift_direction: advance-code
depends_on: []
---

# Raw `batch_odds_api` league_id canonicalization measured non-canonical today — blocks MDPS Step-7 reprocess

## What I found

Dispatched task `sports_track_h_denominator_prereqs-001`: re-run `reprocess_sports_odds.py` (MDPS Step 7) so the
`odds_horizon_bucket` derived surface regenerates under the canonical `league_id=` partition — self-justified as
non-`[OPERATOR]`-gated because "raw content is already canonical per the shipped `batch_odds_api` migration."

Before launching the (multi-hour, multi-VM SPOT) reprocess job, ran a fresh, read-only manifest census — the exact
method `sports_league_id_namespace_migration_2026_07_20.md`'s own 2026-07-28 LIVE-PROBE used
(`read_availability_index(bucket, columns=["league_id","pipeline_mode"])`, league_id values compared against the full
`unified_api_contracts.canonical.domain.sports.league_data.LEAGUE_REGISTRY` key set, 390 entries) — to confirm the
prerequisite really holds. It does not:

- **`batch_odds_api` (raw) total rows: 456,008. Non-registry: 99,607** — 99,587 of those are
  `instrument_type=odds, data_type=trades, capture_status=captured` (the real consumable per-bookmaker shape this
  migration targets, not the unconsumable meta-snapshot shape or an artifact of blank/NaN sentinels). Date range
  2020-06-06..2026-06-24, 1,580 distinct dates — spans the full historical migration scope, not a handful of isolated
  gap-fill dates.
- Top raw values: PREMIER_LEAGUE 13,905 · CHAMPIONSHIP 13,873 · PRIMERA_DIVISION 12,527 · FIRST_DIVISION_A 11,613 ·
  2._BUNDESLIGA 10,997 · SUPER_LEAGUE 10,595 · SUPERLIGA 10,051 · PREMIERSHIP 8,172 · A-LEAGUE 1,341, plus the SOCCER_*
  machine-key residue — **the identical cast of characters as the original 2026-07-20 measurement**, at roughly
  half that measurement's scope (99,607 vs. 214,842), suggesting partial progress, not zero progress, but nowhere near
  the "stable, no residual" state the STATUS 2026-07-25 section reports.
- **`batch_mdps_odds_horizon_bucket` (derived) total rows: 124,294. Non-registry: 42,978** — corroborates
  `sports_league_id_namespace_migration_2026_07_20.md`'s own 2026-07-28 LIVE-PROBE (42,652, run by slot-11 earlier the
  same day; the small delta is normal manifest churn over a few hours, not a discrepancy in method).
- Ran the census twice from independent, fresh Python processes (no stale in-process cache); the reader hits the
  consolidated GCS index directly each time — this is live state, not a caching artifact.
- Checked 3 other same-day issue docs that could plausibly explain a re-write of historical raw data after 2026-07-25
  (`odds_api_raw_ingestion_gap_2026_06_21_24_2026_07_26.md`, `sports_odds_api_scattered_multiyear_gaps_2026_07_27.md`,
  `sports_batch_odds_api_capture_outage_recurrence_check_2026_07_26.md`) — none of them touch league_id, and the
  scattered-gaps doc explicitly states no backfill was attempted (vendor API key deactivated). **Root cause of the
  residual is NOT yet determined** — candidates, none confirmed: (a) the STATUS 2026-07-25 swap only ever covered a
  subset of the 76 raw values / dates and was reported as fully done in error, (b) a second, undocumented silent-revert
  of the same TOCTOU class the 2026-07-25 status section already fixed once, (c) the "verified stable across 5
  consolidator cycles" check used a narrower non-canonical value set than the full 390-entry `LEAGUE_REGISTRY` (e.g.
  checked only the 6 known collision names, missing the ~70 unambiguous raw values or the SOCCER_*/soccer_* machine-key
  residue).

## Why it matters

- **Directly blocks my dispatched todo from reaching its own done-when.** The MDPS reprocess derives its output
  partition from the raw content column (Constraint 2, `sports_league_id_namespace_migration_2026_07_20.md`), so
  re-running it against 99,607 residual non-canonical raw rows will NOT yield 0 non-registry rows in
  `batch_mdps_odds_horizon_bucket` — it will reproduce non-canonical output for the still-dirty raw dates.
- **A launch would repeat an already-flagged wasteful pattern.** This exact reprocess job (multi-hour, 4 sharded SPOT
  VMs) already ran twice for this migration (2026-07-25 and a duplicate 2026-07-27,
  `mdps_odds_horizon_bucket_launch_prep_stale_todo_duplicate_dispatch_2026_07_27.md`) without reaching the canonical
  goal either time. A third blind run without first confirming the raw prerequisite is real progress-free spend.
- **SSOT contradiction**: `sports_league_id_namespace_migration_2026_07_20.md`'s own "STATUS 2026-07-25" section is the
  authoritative status for this migration and states the raw swap is stable with (implicitly) no residual — that
  status is measurably false today. Anyone reading that doc at face value (as 3 separate RE-DISPATCH CHECK sections
  in that same doc did on 2026-07-28, checking only `git log` for a *code commit* re-running Step 7, never re-measuring
  the manifest) would reasonably conclude the raw prerequisite holds. It does not.

## Recommended decision

Not resolving this myself — it's a different repo/script (the raw swap/relocation tooling lives in
`market-tick-data-service/scripts/sports/league_id_relocation/`, not the MDPS reprocess I was dispatched to run) and
root cause is genuinely unclear (3 plausible candidates above, none confirmed). Recommend:

1. **Do NOT launch the MDPS Step-7 reprocess VM job** until the raw `batch_odds_api` residual is independently
   re-investigated and either re-fixed or explained as already-scoped-out (e.g. if it turns out these are dates the
   original migration deliberately left `UNRESOLVED`-untouched — though the value distribution above doesn't match
   that population, which was only 2 leagues / 4 raw values).
2. **Re-run `manifest_swap_2026_07_22.py` (or its successor) against the CURRENT manifest state** with a full
   post-swap census against the complete 390-entry `LEAGUE_REGISTRY` (not a narrower check) — mirroring the rigor the
   2026-07-25 TOCTOU-revert fix used, but checked against the full registry this time.
3. Once raw is confirmed genuinely 0-residual (or explicitly scoped to a known-small remainder), the MDPS Step-7
   reprocess todo — machine-gated on THIS doc via `depends_on`/`gate_on_depends: true` in
   `sports_track_h_denominator_prereqs_step7_gated_2026_07_28.md` — becomes dispatchable again and can actually reach
   its stated done-when. (Re-dispatch of that todo is NOT tracked as a separate todo in THIS doc — a plan-level machine
   gate on the todo below is the correct mechanism, per operator ruling answering `BLK-ad4aa20d`; a second
   "re-dispatch Step-7" todo here would just duplicate that gated plan's own todo.)

Leaving my dispatched todo's checkbox UNCHECKED in `sports_track_h_denominator_prereqs_step7_gated_2026_07_28.md` (not
shipping a reprocess run that can't reach done-when) — same STOP-condition discipline the parent Track H todo has
already correctly applied 4 times this same day.

## Todos

- [ ] [DATA] P1. Re-investigate why the raw `batch_odds_api` league_id swap shows 99,607 non-registry rows today
      despite the 2026-07-25 "stable, verified" status — check `manifest_swap_2026_07_22.py`'s (or successor's) actual
      applied scope vs. the full 76-raw-value classification map, and re-run/extend it against the CURRENT manifest
      state with a full-`LEAGUE_REGISTRY` post-swap census (not a narrower value check). (repo: market-tick-data-service)
