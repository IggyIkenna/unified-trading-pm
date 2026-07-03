---
doc_type: plan
title: DeFi expected_unattempted backlog ≥1M cells — enumerator halt-safety trips on scan; seeding never applied
summary:
  "enumerate_expected_universe --asset-group defi (scan-only) halts with ENUMERATOR_FAILED reason=max_writes_exceeded:
  would-write 1,000,001 > the 1M halt-safety cap. The backlog is PRE-EXISTING (identical count when bounded --end-date
  2026-06-29, i.e. against the pre-incremental catalogue's coverage), meaning ≥1M (shard_key, day) tuples in the defi
  expected universe have NO manifest row at all — the Phase-3.D backward-fill apply-write was evidently never run (or
  never completed) for defi. Until seeded, defi coverage denominators (data-status honest-coverage) silently exclude
  these cells. The enumerator's own halt message gates the fix on operator review of the write volume."
status: active
nature: issue
asset_group: [defi]
stage: [data]
repos: [instruments-service]
scope: [engineer, admin]
tags: [manifest, expected-unattempted, enumerator, honest-coverage, defi, backlog]
related: [plans/active/instruments_catalogue_incremental_rollup_2026_06_29.md]
created: 2026-07-03
parent_epic: instruments_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.8
assigned_role: data-pipeline-engineer
drift_direction: advance-code
depends_on: []
last_updated: 2026-06-27
locked_by: live-defi-rollout
locked_since: 2026-05-21
---

# DeFi expected_unattempted backlog ≥1M — enumerator halt-safety (found 2026-07-03)

## Evidence

Discovered during the incremental-catalogue plan's Phase 4 consumer verification (slot-2, 2026-07-03):

- `enumerate_expected_universe.py --asset-group defi` (scan-only) →
  `ENUMERATOR_FAILED reason=max_writes_exceeded candidates=1000001 cap=1000000` (run_id
  `enum-universe-defi-20260703-152718`); the counter short-circuits at cap+1, so the true backlog is **≥ 1,000,001** and
  unquantified.
- **Pre-existing, NOT caused by the 2026-07-03 incremental catalogue**: re-run with `--end-date 2026-06-29` (restricting
  the expected universe to exactly what the OLD, pre-incremental catalogue covered) trips the identical
  `candidates=1000001` halt.
- Mechanically the enumerator consumed the fresh incremental catalogue fine (manifest 11.77M rows loaded + present-set
  11.23M computed + catalogue cross-join ran) — the halt is the volume guard, not a read failure.

## Why it matters

`expected_unattempted` rows ARE the "remaining to be downloaded" denominator (honest-coverage). ≥1M defi cells with no
manifest row at all means the data-status defi denominators are silently understated — the rollup-vs-drilldown
divergence class the Phase-3.D backward-fill exists to close.

## Fix path (operator-gated by design)

The enumerator's halt message is explicit: "Increase `--max-writes-per-run` after operator review." Steps:

- [x] [VERIFY] P1. ✅ Quantify the true backlog: run scan-only with the cap lifted enough to COUNT (still no writes),
      report per-(venue, data*type, year) distribution so the operator can review what's being seeded. — 2026-07-03 run
      `enum-universe-defi-20260703-154354` (scan-only, cap 50M): **1,380,376 candidates**, report CSV
      `/tmp/enum-universe-defi-20260703-154354.csv` (slot-2 host). Distribution: **99.95% is 2018 (695,830) + 2019
      (683,862)** — pre-launch/pre-genesis days for protocols that did not exist yet (AAVE_V3 / PANCAKESWAP_V3 /
      YEARN_V3 / BEEFY etc. all launched years later), i.e. HONEST-ABSENCE documentation rows
      (`record_expected_empty(reason=EXPECTED*\*)`), NOT download work. Only **684 cells across 2021–2025** are     potentially actionable "remaining to download" rows. Even spread across data_types (~80k each); top venues BEEFY     96k / BALANCER 86k / PANCAKESWAP_V3 64k. (First attempt hit a transient consolidator read race — 404 on a     replaced `\_index`
      generation — retry succeeded; not a defect.)
- [ ] [INFRA] P1. Operator-approved apply: `MANIFEST_PER_VM_SHARDS=true VM_NAME=enum-universe-defi-<ts>`
      `--apply-write --max-writes-per-run <approved>` (chunked runs are fine — the enumerator is idempotent per tuple);
      verify manifest row-count delta + a data-status defi denominator refresh afterwards.
- [ ] [VERIFY] P2. Check the other AGs for the same never-applied backlog (tradfi/cefi/prediction scan-only counts).

## Progress log

- 2026-07-03: Issue filed from the incremental-catalogue plan's Phase 4 verification; pre-existence proven via the
  `--end-date 2026-06-29` bounded re-run. Operator notified in-session.
