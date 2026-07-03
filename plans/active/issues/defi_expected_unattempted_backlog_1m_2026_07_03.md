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
last_updated: 2026-07-03
locked_by: live-defi-rollout
locked_since: 2026-07-03
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

## OPERATOR DECISION REQUIRED (Ikenna) — approve the manifest seeding

The apply-write mutates the availability manifest (~1.38M new rows) and the enumerator gates it on operator review by
design. **What the write actually is**: `record_expected_empty(reason=EXPECTED_*)` honest-absence rows — typed "no data
could ever exist here" documentation. It triggers **zero downloads**; only the 684 recent cells surface as real
outstanding work in data-status afterwards.

**A (RECOMMENDED): approve the FULL apply — all 1,380,376 rows, one run.** The designed Phase-3.D backward-fill;
idempotent per tuple; per-VM-shard isolated (the consolidator merges it); the only option that makes the defi
denominator fully honest AND stops every future scan from tripping the 1M halt. The consolidator already handles a
75M-row cefi canonical — 1.4M metadata rows is well within its envelope.

```bash
cd instruments-service
MANIFEST_PER_VM_SHARDS=true VM_NAME=enum-universe-defi-$(date +%s) \
GCP_PROJECT_ID=central-element-323112 \
python scripts/enumerate_expected_universe.py \
    --asset-group defi --apply-write --max-writes-per-run 1500000
```

Post-apply verification (executor does all three): (1) manifest row-count delta ≈ +1.38M
(`_index/availability_index.parquet` after the next consolidator cycle); (2) a fresh scan-only run reports ~0
candidates; (3) the data-status defi denominator/remaining counts refresh.

**B: seed only 2021→today (684 rows) now, defer the 2018–2019 block.** Smaller manifest, but deep-history denominators
stay dishonest (contradicts the honest-absence model) and every future defi scan keeps halting at the 1M cap. Not
recommended.

**Other**: any custom slice (per-venue / per-year via `--start-date`/`--end-date` chunked runs — idempotent, safe to
split arbitrarily).

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
- [ ] [INFRA] P1. Operator-approved apply per the **OPERATOR DECISION REQUIRED** section above (exact command +
      post-apply verification there). BLOCKED-OPERATOR-DECISION until Ikenna picks A / B / Other; then the executor runs
      the apply + all three verification steps and flips this box with the run_id + manifest delta.
- [ ] [VERIFY] P2. Check the other AGs for the same never-applied backlog (tradfi/cefi/prediction scan-only counts).

## Progress log

- 2026-07-03: Issue filed from the incremental-catalogue plan's Phase 4 verification; pre-existence proven via the
  `--end-date 2026-06-29` bounded re-run. Operator notified in-session.
