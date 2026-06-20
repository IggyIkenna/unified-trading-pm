---
title: expected_unattempted — prediction cqg-grain + full-history scalable materialisation (all AGs)
parent_epic: mtds_mdps_master
assigned_vm: vm-prediction
estimate_class: infra
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 3.2
created: 2026-06-19
author: ikennaigboaka [slot-6·laptop]
locked_by: live-defi-rollout
locked_since: 2026-06-19
---

# expected_unattempted — prediction cqg-grain + full-history scalable materialisation

> **Provenance.** Operator dispatch 2026-06-19: complete `expected_unattempted` properly — (1) prediction at the
> **cqg-bundle grain** (decision 338); (2) **FULL-HISTORY** materialisation all AGs (the ~190M-row scale call —
> design a scalable representation). Supersedes/closes the two `**DEFERRED**` todos
> `master_data_canonicalisation_migration_catalogue_2026_06_07.md` § "G1.run-prediction" (P1) + "G1.run-full-history" (P2).

## Brief — current state (audited 2026-06-19)

Live `_index` `expected_unattempted` (EU) counts (this session's audit):

| AG         | rows      | EU        | captured  | cov%  | EU window |
| ---------- | --------- | --------- | --------- | ----- | --------- |
| cefi       | 3,872,296 | 482,114   | 1,311,984 | 33.9% | 120d bounded |
| defi       | 6,162,717 | 2,307,358 | 367,567   | 6.0%  | 120d bounded |
| tradfi     | 1,938,910 | 818,311   | 102,936   | 5.3%  | 120d bounded |
| sports     | 3,990,486 | 1,027,396 | 659,693   | 16.5% | 120d bounded |
| prediction | 20,269    | **0**     | 16,918    | 83.5% | **NONE — gated** |

- The recurring `expected_universe_v2_scheduler.tf` job (01:30 UTC per-AG, `--start-date 2026-02-20`, ~120 d) seeds
  defi/cefi/tradfi/sports EU over a **bounded recent window** only. prediction EU=0 (was gated decision 338).
- Catalogue empirical roll-up (this session): prediction catalogue = **45 cqg-bundle rows**
  (`data_type=prediction_canonical_question_group`, `instrument_id=<cqg>`) + **870,942 per-conditionId rows** (435,471
  conditionIds × {`trades`,`market_lifecycle`}). The writer DOES emit `canonical_question_group=` in the GCS path now
  (45 distinct cqg, 574 distinct days 2025-03-13→2029-01-20) — so the cqg-grain catalogue rows materialise; the stale
  code comment "writer does not emit cqg in the current venue=/market= layout" is OUTDATED.
- The captured prediction `_index` grain is per-conditionId `trades`/`prediction_trades` — **0** captured
  `prediction_canonical_question_group` rows. A per-conditionId v2 seed = the >50M-row false-EU explosion.

## DESIGN DECISIONS

### Part 1 — prediction EU at cqg-bundle grain (decision 338)

The v2 prediction enumerator MUST seed EU at the **cqg-bundle grain ONLY** (`data_type=prediction_canonical_question_group`,
`instrument_id=<cqg>`), NEVER per-conditionId. Mechanism: filter the prediction catalogue to its cqg-bundle rows before
enumeration (the catalogue carries both grains; the per-conditionId rows are excluded). Sized: 45 cqgs × ~574 days
≈ ≤26K EU candidates — manifest-scale, NOT 50M. A cqg-grain EU row is an HONEST "this cqg bundle existed but the
`prediction_canonical_question_group` data_type was never captured" (the bundle data_type genuinely has 0 captured rows).

### Part 2 — full-history scalable representation: RANGE-ENCODED EU companion artifact

**The naive full-history per-instrument-day EU is ~190M rows fleet-wide (~100× index blow-up).** Options evaluated:
- (a) **range / run-length encoding** — one row per contiguous `(shard-key, reason)` date-span (`date_start`/`date_end`)
  vs one-row-per-day. EU spans are almost entirely contiguous (an alive-no-data instrument is owed EVERY day in
  `[available_from, today]`). Collapses ~190M day-rows → ~per-(instrument×data_type×reason-span) ≈ 1–3M rows (~100×).
  Denominator stays EXACT: expand `days_in_span` to recover the per-day count.
- (b) separate `_index/expected_universe/` artifact — keeps main `_index` lean but forks the SSOT (drift risk).
- (c) year-partition — still 190M rows; doesn't fix whole-corpus read perf.
- (d) accept 190M — read-perf risk: UTL `read_availability_index` loads the WHOLE parquet on every consumer.

**CHOSEN: (a)+(b) hybrid — range-encoded EU in a dedicated `_index/expected_universe_ranges.parquet` companion.**
Justification: keeps the main `_index` at per-day grain (recent window — unchanged reader perf, no schema migration on
the hot path) AND gives an honest FULL-HISTORY denominator that the coverage consumer reads ADDITIVELY. The companion is
range-encoded so it stays ~1–3M rows fleet-wide (not 190M). The denominator becomes
`captured / (captured + empty + failed + EU_per_day_window + Σ range.days_outside_window)` — honest over 2018→today
without the 190M index. Single SSOT shape: each range row carries the SAME shard-key columns + `date_start`/`date_end` +
`capture_status=expected_unattempted` + `reason`. Recent-window per-day EU rows (already in `_index`) are SUBTRACTED from
the ranges at read time so cells are never double-counted (the companion is the COMPLEMENT of the bounded window).

## Phases

- [ ] [CODE] P0. Part 1 — prediction cqg-grain filter in `_enumerate_v2_prediction` + `--data-types` CLI override.
- [ ] [CODE] P0. Part 2 — `--full-history` mode + `_emit_ranges` range-encoder + companion-artifact writer in
      `enumerate_expected_universe.py`; reader-side denominator add in UTL/deployment-api consumers.
- [ ] [DATA] P0. Materialise prediction cqg-grain EU (verify ~26K, sane).
- [ ] [DATA] P0. Materialise full-history range-EU all 5 AGs (snapshot first; per-VM-shard; captured-preserved).
- [ ] [VERIFY] P0. Full-timeframe coverage% per AG; QG-green; quickmerge; codex doc update.

## Codex SSOT updates

- `codex/02-data/availability-manifest-and-data-status.md` § "expected_unattempted (F4)" — add the range-encoded
  full-history companion representation + the prediction cqg-grain rule.

## Progress Log

- 2026-06-19 — plan created. Audited live state (table above). Confirmed Part-1 code path exists (catalogue emits cqg
  grain since the writer path-partitions by `canonical_question_group=`); the gap is the enumerator does not FILTER to
  cqg-grain so it would seed per-conditionId. Designed range-encoded full-history companion for Part 2.
