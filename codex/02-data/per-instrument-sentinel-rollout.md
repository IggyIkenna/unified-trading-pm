---
doc_type: codex-ssot
title: "MTDS per-instrument sentinel rollout (3-tier: MVP → Expanded → Full)"
summary: >-
  MTDS Tier-3 per-instrument sentinel rollout SSOT (Phase 8E) — the --per-instrument-sentinel-cap thresholds (MVP=50 /
  Expanded=200 / Full=10000), the MVP -> Expanded -> Full promotion criteria, the per-tier observability gates, and the
  rollback paths (incl. cap=0 emergency Tier-3 disable); the cap bounds manifest fan-out and stays identical
  writer<->reader via get_expected_instruments_for_venue.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [deployment-api, deployment-service, instruments-service, market-tick-data-service, unified-api-contracts]
scope: [engineer, admin]
tags: [mtds, manifest, honest-coverage, backfill, observability]
related: [/codex/02-data/mtds-data-source-coverage-matrix.md, /codex/02-data/availability-manifest-and-data-status.md]
created: 2026-04-21
authoritative_for: [MTDS per-instrument sentinel cap thresholds, sentinel tier-promotion gates]
referenced_by: [/codex/02-data/mtds-data-source-coverage-matrix.md]
owner:
last_reviewed: 2026-05-17
code_refs:
---

# MTDS per-instrument sentinel rollout (3-tier: MVP → Expanded → Full)

**Phase 8E SSOT.** This document is the canonical spec for the rollout of MTDS Tier-3 per-(venue, data_type,
instrument_id) sentinels: the cap thresholds per tier, the promotion criteria between tiers, the observability gates the
human operator must check before promoting, and the rollback path if telemetry regresses.

Scope: the CLI flag `--per-instrument-sentinel-cap` on `market-tick-data-service/market_tick_data_service/cli/main.py`
and the matching `per_instrument_sentinel_cap` parameter on `process_ticks` (orchestrator). Values live HERE, not as
magic numbers in code — code only holds the MVP fallback (`_DEFAULT_PER_INSTRUMENT_SENTINEL_CAP = 50`).

Prerequisite reading:

- `/codex/02-data/mtds-data-source-coverage-matrix.md` — honest-coverage denominator model, § 2 / § 4 / § 8.
- `/codex/02-data/availability-manifest-and-data-status.md` — v5 shard schema (`instrument_id` column, `capture_status`
  enum).
- `plans/archive/mtds_per_instrument_sentinels_2026_04_21.plan.md` — Phase 8 execution DAG (Waves 8B-8F).

## 1. Why cap the Tier-3 fan-out?

The per-instrument shard data_types (`trades`, `book_snapshot_5`, `derivative_ticker`, `options_chain`, `futures_chain`,
plus DeFi per-pool / per-market and PREDICTION per-conditionId equivalents) have a natural denominator
`N instruments × M expected_dates` per (venue, data_type). Uncapped, a 4-year backfill across 11 CEFI venues × 5
per-instrument dts × 1460 days × unbounded instruments-service output produces an unbounded manifest-row count — the
pathological case is an adapter bug that fans out thousands of non-tradable contracts as empty sentinels, or an
instruments-service parquet with 10k+ rows (full options chain) inflating the denominator beyond anything the aggregator
can meaningfully count.

The cap bounds `manifest_rows <= cap × len(expected_dts) × len(venues) × len(expected_dates)`. Honest coverage remains
honest because the denominator is taken from the SAME capped list the orchestrator writes — the aggregator uses the same
UAC accessor (`get_expected_instruments_for_venue(venue, data_type, *, as_of_date, cap=N)`) so the cap never diverges
between writer and reader.

## 2. Rollout tiers

| Tier         | Cap   | Target venues                                                                  | Backfill window                                                            | Max manifest rows per 4-year backfill                             |
| ------------ | ----- | ------------------------------------------------------------------------------ | -------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| **MVP**      | 50    | `VenueMapping.spot_mvp_filtered_venues` (UPBIT, COINBASE) + 21 MVP base assets | First 90 days of Phase 8 rollout                                           | ~4M rows (11 CEFI venues × 5 per-instrument dts × 1460 days × 50) |
| **Expanded** | 200   | All CEFI + PREDICTION venues                                                   | Day 91 onward, after 30-day MVP bake                                       | ~16M rows (same fan-out with cap=200)                             |
| **Full**     | 10000 | All CEFI + PREDICTION + DeFi (per Wave 8G seed)                                | Only after manifest write-rate telemetry confirms <10M object budget holds | Hard ceiling; never uncapped. Adapter-bug guard-rail.             |

**MVP fallback in code.** The module-level `_DEFAULT_PER_INSTRUMENT_SENTINEL_CAP = 50` in
`market_tick_data_service/engine/orchestrator.py` is the MVP tier default that applies when the CLI flag is absent. This
is the ONLY cap value hardcoded anywhere; Expanded and Full are operator-driven.

```yaml
execution:
  owner: MTDS sentinel maintainer (Ikenna for MVP→Expanded design call; Harsh for the run-and-verify step)
  cadence: one-shot per tier promotion (MVP → Expanded planned for day-91 gate; Expanded → Full observability-gated)
  verifier: |
    Per § 4 "Observability gates" checklist below — each promotion gate requires evidence from telemetry that the
    prior tier's manifest-write-rate / object-budget / phantom-audit cadence are within tolerance.
    Records last-promotion timestamp + cap value in `plans/active/issues/sentinel_rollout_history.md` (TBD).
  last_executed: NEVER (MVP tier is the default; first Expanded promotion gated on day-91 bake)
```

(Added per codex audit IN-14 2026-05-12 — Runbook Execution-Owner SSOT HARD RULE compliance for tier-promotion operator
decisions.)

## 3. Promotion criteria (MVP → Expanded → Full)

Each promotion is a deliberate human decision informed by telemetry from the prior tier. No autonomous promotion —
agents may propose, humans approve.

### 3.1 MVP → Expanded (day 91 gate)

All of the following must be true for 30 consecutive days:

- **Manifest row-count drift < 5%/day.** Daily `record_empty` + `record_failed` row counts for per-instrument dts trend
  flat (no accidental 10× fan-out from an adapter bug or instruments-service seed change).
- **Honest-coverage stable.** The deployment-api `/data-status` aggregator returns a coverage % for CEFI + PREDICTION
  within ±2pp of the steady-state baseline observed at day 30 of MVP. A single sudden drop >5pp is the rollback signal.
- **No new `INSTRUMENT_PROVIDER_FAILED` events.** Shard-level failure isolation (D10) on the orchestrator emits this
  when `instruments_provider` raises; any uptick beyond the MVP baseline blocks promotion until root-caused.
- **Manifest-writer latency < p99 2s** on the `record_empty` / `record_failed` batch path. The ManifestWriter in UTL is
  cap-sensitive: Expanded-tier (cap=200) is 4× the write volume, so verifying p99 stays under 2s before promotion avoids
  tripping MDPS's 60-second staleness threshold downstream.

### 3.2 Expanded → Full (no fixed date — observability-gated)

All of the above, PLUS:

- **GCS object-count budget.** Manifest bucket total object count must be projected under 10M across the full 4-year
  backfill window even at Full-tier (cap=10000). Projection = `current_rate × 4 × 365 / days_elapsed_at_expanded_tier`.
  Fails → stay at Expanded and investigate per-dt top talkers.
- **Aggregator fairness.** `/codex/02-data/sports-data-source-coverage-matrix.md` denominator fairness checks pass — the
  aggregator does not penalise low-activity venues (e.g. a DeFi pool with 3 swaps/day would otherwise show 0.03%
  coverage if we didn't `empty_confirmed`-mark the empty days).
- **Wave 8G DeFi seed tables landed.** Full-tier assumes UAC MVP seed tables cover DeFi pools (`UniswapV3` top-20 by
  TVL, `Aave` top-10 reserves) and PREDICTION per-conditionId seeds. Without Wave 8G, Full-tier on DeFi/PREDICTION
  degrades to no-op per the Wave 8C guardrail (empty seed → skip Tier-3, no regression on the Tier-2 aggregator).

## 4. Observability gates (checklist per tier change)

Before flipping from one tier to the next, a human operator must confirm each gate. Each gate is a telemetry query on
the research-and-development GCP project (doubles as staging — no dedicated staging project exists). Capture the numbers
in the plan's Wave log before setting the new cap.

| Gate                               | Query                                                                                                                                                                           | Pass threshold                  | Rollback trigger                                      |
| ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------- | ----------------------------------------------------- |
| Manifest row-count drift           | `bq query 'SELECT COUNT(*) FROM market-data-manifest WHERE capture_status IN ("empty_confirmed", "attempted_failed") AND data_type IN UNNEST(...) GROUP BY DATE(attempted_at)'` | <5% daily drift over 30 days    | >10% day-over-day spike                               |
| Honest-coverage %                  | deployment-api `/data-status/summary?category=CEFI&days=30`                                                                                                                     | Within ±2pp of steady-state     | >5pp drop                                             |
| `INSTRUMENT_PROVIDER_FAILED` count | Event explorer filter on `event_name=INSTRUMENT_PROVIDER_FAILED`                                                                                                                | <5 events/day across full fleet | >50 events/day or any venue showing 100% failure rate |
| `record_empty` p99                 | Cloud Monitoring `metric.type="custom.googleapis.com/manifest_writer/record_empty_latency"`                                                                                     | <2s p99                         | >5s p99 for >15min                                    |
| GCS manifest object count          | `gcloud storage ls --recursive gs://market-data-manifest-<project>/instrument_availability/` piped to `wc -l`                                                                   | Projected <10M at 4-year window | Projected >15M                                        |

The operational smoke `bash market-tick-data-service/scripts/smoke_matrix.py --per-instrument-sentinel-cap $N` asserts
`manifest_rows_emitted <= cap × len(expected_dts) × len(venues)` for a single-day run — this is the build-time guardrail
that catches a code-path regression before it hits production.

## 5. Rollback path

Each tier has a documented rollback. Rollbacks are ALWAYS safe to execute — they only change the cap value on subsequent
runs; already-written manifest rows remain valid (they are honest within their cap).

### 5.1 From Expanded → MVP

1. Edit the live-pipeline VM launcher that passes `--per-instrument-sentinel-cap` (or omit the flag to fall back to the
   module default 50).
2. Restart MTDS on the next scheduled batch window. No data migration, no manifest rewrite; the new cap applies to
   shards written FROM THIS POINT FORWARD.
3. Legacy shards with the Expanded-tier cap remain in the manifest. The deployment-api aggregator treats them as-is; the
   denominator contribution is capped by the cap used AT WRITE TIME, so history stays honest.
4. File a follow-up to investigate the observability-gate failure before any new promotion attempt.

### 5.2 From Full → Expanded

Same as 5.1 with cap=200.

### 5.3 Emergency rollback (adapter bug producing unbounded fan-out)

If a code-path regression is producing >10M manifest rows/day (identified via the GCS object-count gate):

1. Set `--per-instrument-sentinel-cap=0` on the next launch (zero = Tier-3 branch no-ops; Tier-2 per-venue sentinel
   still fires). This is the "Tier-3 disabled" escape hatch.
2. Investigate the root cause (likely an `instruments_provider` returning a too-large list, or a UAC accessor bug).
3. Ship the fix; re-enable at MVP tier (cap=50); re-run the 30-day bake before promoting back to Expanded.

## 6. Launcher invocation examples

VM launcher invocations for each tier. These sit in `deployment-service/scripts/vm/launch-mtds-*.sh`; the flag is
forwarded through to the MTDS CLI inside the tarball.

```bash
# MVP tier (default; omitting the flag also works — falls back to module-level default 50)
python -m market_tick_data_service.cli.main \
  --operation download \
  --mode batch \
  --asset-group CEFI \
  --start-date 2026-04-21 \
  --end-date 2026-04-21 \
  --per-instrument-sentinel-cap 50

# Expanded tier
python -m market_tick_data_service.cli.main \
  --operation download \
  --mode batch \
  --asset-group CEFI \
  --start-date 2026-04-21 \
  --end-date 2026-04-21 \
  --per-instrument-sentinel-cap 200

# Full tier (requires Wave 8G DeFi seeds to be useful; otherwise no DeFi gain)
python -m market_tick_data_service.cli.main \
  --operation download \
  --mode batch \
  --asset-group CEFI \
  --start-date 2026-04-21 \
  --end-date 2026-04-21 \
  --per-instrument-sentinel-cap 10000

# Emergency rollback — Tier-3 fan-out disabled
python -m market_tick_data_service.cli.main \
  --operation download \
  --mode batch \
  --asset-group CEFI \
  --start-date 2026-04-21 \
  --end-date 2026-04-21 \
  --per-instrument-sentinel-cap 0
```

Backfill VMs go via `bash deployment-service/scripts/vm/launch-tradfi-backfill-vm.sh` (analogous launcher for CEFI
exists). Both wrap the CLI invocation in a singleton-locked systemd unit so the cap persists across VM restarts.
Refreshing tarballs after any code change:
`bash deployment-service/scripts/vm/create-code-tarballs.sh --asset-group CEFI` (see
`/codex/05-infrastructure/vm-tarball-deployment.md`).

## 7. Cross-references

- `market-tick-data-service/market_tick_data_service/cli/main.py` § `--per-instrument-sentinel-cap` flag definition (MVP
  default fallback via `None` sentinel).
- `market-tick-data-service/market_tick_data_service/engine/orchestrator.py` § `_DEFAULT_PER_INSTRUMENT_SENTINEL_CAP`
  module constant + `process_ticks(per_instrument_sentinel_cap=...)` parameter.
- `unified-api-contracts/unified_api_contracts/registry/market_data_categories.py` §
  `get_expected_instruments_for_venue(venue, data_type, *, as_of_date, instruments_provider, cap)` accessor —
  cap-sensitive, consumed by both orchestrator (writer) and deployment-api aggregator (reader).
- `deployment-api/deployment_api/services/data_status_service.py` § `_mtds_honest_coverage_for_venue` — reader side of
  the cap contract.
- `/codex/02-data/mtds-data-source-coverage-matrix.md` § 8 Open questions — this rollout closes the ⏳ "Instrument-level
  expected" bullet once Wave 8F ships.

## 8. Changelog

- **2026-04-21** — Initial SSOT. Authored as Phase 8E of `mtds_per_instrument_sentinels_2026_04_21`. Wires the
  `--per-instrument-sentinel-cap` CLI flag through to the orchestrator's `_DEFAULT_PER_INSTRUMENT_SENTINEL_CAP`
  fallback. MVP tier (cap=50) matches the code default; Expanded (cap=200) and Full (cap=10000) are operator-driven and
  require observability-gate sign-off per § 3.
