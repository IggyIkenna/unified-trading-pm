---
doc_type: issue
title:
  "No generic manifest-reprocessing mechanism -- 13 near-identical one-off reclassify scripts written across 3 repos in
  8 weeks (was: 11 -- see 2026-07-12 correction)"
summary:
  "When an adapter/writer bug gets fixed, nothing in the codebase automatically finds and re-attempts the
  attempted_failed or unclassified-empty shards it caused. Every incident, ASTER included, has gotten its own
  hand-written load-manifest-filter-flip-write-back script. Found 13 near-identical such scripts (was: 11 -- see
  2026-07-12 correction) across instruments-service and market-tick-data-service since 2026-05-04. The codebase own
  script-homes.md standard says a recurring need like this should graduate to a permanent tool -- it has not. One
  existing script (retry_transient_cefi_failures_2026_06_28.py) is already ~90% of the generic shape."
status: open
nature: notes
asset_group: [cross-cutting]
stage: [data, meta]
repos: [instruments-service, market-tick-data-service, unified-trading-library]
scope: [engineer, admin]
tags: [reprocessing, reclassify, honest-coverage, hygiene, script-homes, cefi, defi, sports]
related:
  [
    ../instruments_completion_tracker_2026_07_06.md,
    /plans/archive/issues/cefi_monotonicity_guard_alerting_and_dark_venues_2026_07_07.md,
    /codex/06-coding-standards/script-homes.md,
  ]
created: 2026-07-07
parent_epic: instruments_master
priority: P2
source:
  "ASTER/CEFI instrument-service data-status audit, 2026-07-07 -- prompted by the question of whether the ASTER 05-14
  base-URL fix needed a follow-up reprocessing run"
assigned_vm: planning
resolved_by:
locked_by:
execution_scope: orchestrator-agent
model_tier: sonnet-doable
thinking_tier: medium
estimate_class: infra
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.6
last_updated: 2026-07-12
supersedes:
superseded_by:
depends_on:
assigned_role: infra
drift_direction: advance-code
locked_since:
---

## What I found

13 near-identical (was: 11 -- see 2026-07-12 correction below) "load manifest → filter by predicate → flip status/reason
field → snapshot → write back" scripts, independently reinvented across 3 repos and ~2 months:

| Script                                                                   | Repo                     | Date          | Scope                                          |
| ------------------------------------------------------------------------ | ------------------------ | ------------- | ---------------------------------------------- |
| `scripts/reclassify_404_failures_to_empty.py`                            | instruments-service      | 2026-05-04    | 404s → empty (hardcoded Tardis venue prefixes) |
| `scripts/reconcile_expected_absence_reasons.py`                          | instruments-service      | 2026-05-07    | null-reason `empty_confirmed` → typed reason   |
| `scripts/reclassify_defi_orphan_eu_notlisted_2026_06_24.py`              | instruments-service      | 2026-06-24    | DeFi orphan EU rows                            |
| `scripts/reclassify_defi_postdelist_eu_2026_06_24.py`                    | instruments-service      | 2026-06-24    | DeFi post-delist EU rows                       |
| `scripts/reclassify_golden_window_fixtures_no_match_2026_06_24.py`       | instruments-service      | 2026-06-24    | Sports FIXTURES golden-window                  |
| `scripts/reclassify_oos_sports_expected_unattempted_2026_06_24.py`       | instruments-service      | 2026-06-24    | out-of-scope sports sources                    |
| `scripts/reclassify_xg_blank_league_phantoms.py`                         | instruments-service      | 2026-06-23    | XG blank-league rows                           |
| `scripts/reclassify_cefi_manifest_mvp_universe_2026_06_23.py`            | market-tick-data-service | 2026-06-23    | CeFi MVP universe                              |
| `scripts/retry_transient_cefi_failures_2026_06_28.py`                    | instruments-service      | 2026-06-28    | Tardis 500/503/timeout transients              |
| `scripts/reclassify_xg_shots_false_failed_2026_06_29.py`                 | instruments-service      | 2026-06-29    | XG_SHOTS 401-vs-404 misclassification          |
| `scripts/delete_aster_overseeded_capability_rows.py`                     | instruments-service      | 2026-06-29/30 | ASTER over-seeded book/liq rows                |
| `scripts/backfill_cefi_blank_instruments_data_type_2026_07_06.py`        | instruments-service      | 2026-07-06    | CeFi blank `data_type` → `instruments`         |
| `scripts/backfill_defi_tradfi_blank_instruments_data_type_2026_07_06.py` | instruments-service      | 2026-07-06    | DeFi/TradFi blank `data_type` → `instruments`  |

> **(2026-07-12, finding 122, §A2 B-queue ruling)**: count corrected 11 → 13 (was: 11) — this audit's own filing date
> (2026-07-07) postdates two more scripts matching this exact recurring shape, shipped one day earlier at
> `instruments-service@40bdfe1d` and `instruments-service@523d427`
> (`plans/active/issues/is_cefi_manifest_blank_data_type_since_2026_06_29_2026_07_06.md`), which were absent from the
> original enumeration. The "Recommendation" and "Todos" sections below are unaffected — a 13th/14th instance only
> strengthens the case for the generic utility, it doesn't change the proposed shape.

None import a shared "reclassify" or "retry-window" library primitive — grepped `unified-trading-library`,
`unified-api-contracts`, and both service repos for `def.*reclassify`, `def.*replay_failed`, `def.*retry_attempted`,
`ShardReplay`: zero hits outside these one-offs. The closest thing to a generic mechanism is `check_shard_freshness()`
(`unified-trading-library/unified_trading_library/manifest_writer/_queries.py:63`), whose `retry_failed=True` default
means a plain backfill VM re-run over a date range _will_ naturally re-attempt `attempted_failed` shards it touches —
but only by date range, not by error reason, and only if a human remembers to relaunch a backfill covering the right
venue and window. It does nothing on its own when a fix lands.

**Codex already flags this as the recurring-need pattern it's supposed to prevent:**
`/codex/06-coding-standards/script-homes.md:62-66`: _"If the script encodes a recurring need, it has a named successor
(a service CLI subcommand / deployment-service job) and is retired the moment that lands — never left as a parallel
path."_ 11 scripts in 8 weeks is exactly that recurring need, and it hasn't graduated.

**ASTER itself is the proof, not a one-off exception**: per `cefi_hl_aster_batch_data_gaps_2026_06_22.md`, ASTER
accumulated three _more_ distinct attempted*failed-causing bugs after the 2026-05-14 base-URL fix (book_snapshot_5
misclassification, a catalog-reader small-universe cap, NOT_LISTED over-seeding), each needing its own diagnosis and its
own bespoke remediation. That doc's own line 173-176 is a smoking gun: the launcher that \_did* exist for ASTER's re-run
deliberately excludes `liquidations` from its `DATA_TYPES`, so even an existing recovery mechanism silently skipped part
of its own backlog — undetected until someone happened to notice.

## Recommendation

Build one generic utility rather than continuing to write one-off scripts per incident — the risk isn't hypothetical,
it's 11 independently-implemented (and independently-audited) safety gates: per-VM shard isolation, dry-run defaults,
snapshot-before-write, captured-count invariants, each re-solved from scratch.

**Concrete shape:** a function
`select_shards_for_reprocess(df, *, asset_group=None, venue=None, capture_status=ATTEMPTED_FAILED, date_start=None, date_end=None, error_reason_predicate)` +
a generalized flip-and-write helper, living in
`unified-trading-library/unified_trading_library/manifest_writer/_queries.py` (sibling to `check_shard_freshness`, which
already has half the needed logic) or a new `manifest_reprocess.py` module next to `manifest_migrations/`. Best existing
template to generalize from: `instruments-service/scripts/retry_transient_cefi_failures_2026_06_28.py` — its
`_is_transient`, `_identify_transient_rows`, and `_flip_to_expected_unattempted` functions are already ~90% of the
generic shape; they just need the hardcoded pattern list and hardcoded bucket resolver replaced with CLI args.

**Where it should surface:** per `/codex/06-coding-standards/script-homes.md`'s decision rule ("production verb →
service CLI subcommand"), as a permanent instruments-service CLI subcommand — e.g.
`instruments-service --operation reprocess-shards --asset-group cefi --venue ASTER --capture-status attempted_failed --error-reason-contains "404" --date-start 2024-10-01 --date-end 2026-05-14 [--apply]`
— backed by the UTL library function so market-tick-data-service and any future consumer get it for free.

## Todos

- [ ] [DESIGN] P2. Design `select_shards_for_reprocess()` + the flip-and-write helper signature; confirm placement
      (`unified-trading-library/manifest_writer/_queries.py` vs. a new `manifest_reprocess.py`).
- [ ] [CODE] P2. Implement it, generalizing `retry_transient_cefi_failures_2026_06_28.py` as the template; port its
      existing safety gates (dry-run default, snapshot-before-write, captured-count invariant checks).
- [ ] [CODE] P2. Wire it as an instruments-service CLI subcommand (`--operation reprocess-shards`) per
      `script-homes.md`'s production-verb rule.
- [ ] [SCRIPT] P3. Retire the 13 one-off scripts above (was: 11 — verify-rerun-2 finding 151, 2026-07-14: title/summary
      were corrected 2026-07-12 to 13, but this todo's count was never updated) once the generic tool covers their use
      cases (or leave the already-run ones as historical record — they don't need deletion if inert, just no new ones
      going forward).

## Progress Log

- **2026-07-07** — Filed from the ASTER/CEFI instrument-service data-status audit, prompted by the operator asking
  whether the 2026-05-14 ASTER base-URL fix needed a follow-up reprocessing run. No files edited.
