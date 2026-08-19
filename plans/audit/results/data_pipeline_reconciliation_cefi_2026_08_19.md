---
doc_type: audit-result
title: "Data-pipeline reconciliation — cefi (2026-08-19), raw-tick layer, Tier-1 only"
summary: >-
  Scheduled daily cefi spot-check (cefi_reconciliation_auditor role, dispatch agt-419a6c, slot 28). Phase 0: the
  market-data-tick-cefi consolidator is CONFIRMED stuck on a phantom lock — `latest.json` reports `error_reason=locked`
  no-ops, `consolidator_stall_state.json` streak escalated 89 -> 183, the lock object holds instance `1-b5a4d4fa` since
  2026-08-19T19:35Z, and the canonical `_index/availability_index.parquet` is byte-frozen at generation
  1787019237694916 / 2026-08-18T02:13:57.708Z (~42h stale). This is NOT a new finding — it was already root-caused and
  filed as P0 (`manifest_consolidator_market_data_cefi_stuck_lock_2026_08_19.md`), operator decision A, dispatched for
  fix; this run independently corroborates it. Because the consolidated manifest has not advanced since the 08-18
  report's own read of that same generation, the §3f census is byte-identical to 08-18 BY CONSTRUCTION (frozen data,
  not re-measured — a re-read falls back to per-VM shards, which under-counts). Two carried todos RESOLVED this run:
  (1) the 08-18 "honest-coverage rollup freeze" P1 — today's 08-19 rollup genuinely advanced (+23,507 captured,
  coverage_pct 45.51 -> 45.57), refuting the proposed consolidator-stall root cause (the freeze was a one-day timing
  artifact: the 08-18 00:49Z compute ran before the 08-18 02:13Z consolidator write); (2) the reprobe-audit cadence
  P4 — today's `reprobe_audit_latest.json` regenerated at 2026-08-19T09:01:30.9Z, confirming the ~09:00Z daily cadence.
  `phantom_audit` for cefi is now 23 days stale (escalating). No code fix shipped this run — the sole P0 is already
  dispatched; every other finding is carried-unchanged (frozen) or resolved.
status: pass
nature: record
asset_group: [cefi]
stage: [data]
repos: [unified-trading-pm, unified-api-contracts, market-tick-data-service]
scope: [engineer, admin]
tags:
  [
    reconciliation,
    canonicalisation,
    census,
    cefi,
    honest-coverage,
    consolidator-stuck-lock,
    phantom-lock-p0-corroborated,
    honest-coverage-freeze-resolved,
    reprobe-cadence-confirmed,
    bybit-futures-selfheal-stable,
    depth-of-book-10-carried,
    binance-delivery-carried,
    bare-okx-carried,
  ]
related:
  [
    four-surface-reconciliation-procedure,
    reconciliation-finding-taxonomy,
    honest-coverage-model,
    manifest_consolidator_market_data_cefi_stuck_lock_2026_08_19,
    data_pipeline_reconciliation_cefi_2026_08_18,
  ]
created: 2026-08-19
resulting_plan:
lib_version: "market-tick-data-service@HEAD (slot 28), unified-api-contracts@HEAD (audited only; no code changes shipped this run)"
doc_versions_checked:
audited_scope:
  "asset_group=cefi, layer=raw-tick, PROD (-prd-) buckets only, read-only, Phase 0 + census (Tier-1) +
  honest-coverage verification per the cefi_reconciliation_auditor role (subset of /data-pipeline-reconciliation) —
  daily scheduled spot-check, not a full campaign. Fourth consecutive daily run (prior: 2026-08-16, 08-17, 08-18)."
date: 2026-08-19
auditor: "cefi_reconciliation_auditor (scheduled role, slot 28, dispatch agt-419a6c)"
parent_epic: security_and_cross_cutting_master
severity: P0
skill: data-pipeline-reconciliation
run_date: 2026-08-19
generated_at: 2026-08-19T20:20:00+00:00
---

# Data-pipeline reconciliation — cefi (2026-08-19), raw-tick layer, Tier-1 only

**Fully read-only this run** — no GCS writes, no manifest writes, no deletes, no VM launches, no code changes.
Daily scheduled `cefi_reconciliation_auditor` spot-check: Phase 0 (reachability + freshness) + the §3f
distinct-value census + honest-coverage formula/freshness verification. Fourth consecutive daily run since the
2026-08-16 restart (predecessors: 2026-08-16, 08-17, 08-18).

## 0. Phase-0 reachability + freshness

| bucket | reachable | consolidator lock | last write to `availability_index.parquet` | verdict |
| --- | --- | --- | --- | --- |
| `market-data-tick-cefi-prd-central-element-323112` | yes | **HELD** since 2026-08-19T19:35:23.24Z (instance `1-b5a4d4fa`) | 2026-08-18T02:13:57.71Z (generation `1787019237694916`, size 443,800,429 bytes — **byte-frozen ~42h**) | **STUCK on phantom lock — P0, already filed** |
| `instruments-store-cefi-prd-central-element-323112` | yes | not locked | 2026-08-19T20:01:13.43Z (1 shard scanned, 0 changed, `no_op`) | healthy, consistent with every prior run |

**AWS cross-check**: both AWS-side mirror buckets (`market-data-tick-cefi-prd-427895769566`,
`instruments-store-cefi-prd-427895769566`) confirmed reachable via the **AWS client** (provider=aws, credentials from
`~/.aws/credentials`) and **completely empty** (`top_level_prefixes=0` for both) — unchanged from every prior run. (A
first-pass probe this run used the GCP client against the AWS bucket names and got a spurious 404; re-checked with the
correct client, empty-and-reachable stands.)

### Consolidator — the phantom lock is now a CONFIRMED, ALREADY-FILED P0 (this run corroborates it)

The carried "consolidator stall-streak" P1 from the 08-18 report has been **root-caused and escalated to P0** between
runs: `/plans/active/issues/manifest_consolidator_market_data_cefi_stuck_lock_2026_08_19.md` (filed 08-19, operator
decision A, `assigned_vm: planning`, dispatched for fix). This run's independent Phase-0 reads corroborate every leg of
that diagnosis, with the streak now **escalated further**:

- `_index/latest.json`: `last_run_at=2026-08-19T20:01:39.8Z`, `success=true`, `verdict=empty`, `shards_scanned=0`,
  `rows_in=0`, `rows_out=0`, `no_op=true`, **`error_reason="locked"`** — the hourly Cloud Run cycle is still
  short-circuiting on a "fresh lock present (sibling cron still running)" and doing ZERO work while exiting success.
- `_index/consolidator_stall_state.json`: **`streak=183`** (`baseline_shards=7851`) — **escalated 89 -> 183** since
  the 08-18 report, consistent with one more full day of hourly locked no-ops incrementing the counter.
- `_index/consolidator.lock`: `{"started_at": "2026-08-19T19:35:23.24Z", "instance": "1-b5a4d4fa"}` — a live lock
  held by a sibling-cron instance that never clears.
- Canonical blob (measured directly via `gcs_describe_object`): `generation=1787019237694916`,
  `last_modified=2026-08-18T02:13:57.708Z`, `size=443,800,429`, `metadata=null` — **byte-frozen since the 08-18
  report's own read of this exact generation** (~42h vs the 24h loud-fail budget).

This is the single headline of the run, and it is **not a new finding** — it is already tracked, root-caused, and
dispatched for fix in the P0 issue doc (lock acquire/release TTL gap + a zombie-execution check as the two candidate
explanations). This role's Tier-1 read-only scope does not fix it; see §6 for the carry/citation, not a re-file.

`phantom_audit_latest.json`: `phantom_count=0`, `generated_at=2026-07-27T17:38:18Z` — **now 23 days stale** (was 22 on
08-18), carried, escalating by 1 day, zero remediation for 3+ weeks.

`_index/reprobe_audit_latest.json` (market-data): **REGENERATED TODAY** — `generated_at=2026-08-19T09:01:30.9Z`,
`day=2026-08-19`, `new_empties=0`, `disagreements=0`, `proven=0` — this **RESOLVES** the carried "daily-cadence not
confirmable" P4 (see §6). The cadence is anchored ~09:00 UTC daily; prior runs kept landing at ~02:3x UTC, ~6.5h
before the next expected generation, which is why they could never confirm it.

`instruments-store-cefi` still has **no** `phantom_audit_latest.json` / `reprobe_audit_latest.json` (both 404,
confirmed via direct read) — standing declared coverage gap, unchanged.

## 1. Census — venue axis (frozen, byte-identical to 08-18 BY CONSTRUCTION)

The consolidated manifest has **not advanced** since 2026-08-18T02:13:57Z (generation 1787019237694916 — the exact
generation the 08-18 report read as **30,001,825 rows**). A fresh `read_availability_index` re-read this run
auto-fell-back to per-VM shards (consolidated blob age 151,352s > 86,400s threshold) and then waited on the live
phantom lock — a per-VM-shard fallback **silently under-counts** per the skill's §2d, so those numbers were discarded
rather than reported as authoritative. The correct statement is: **the census is unchanged from 08-18 by construction
because the data has not moved.** Every 08-18 census figure stands verbatim:

- **C − M (orphaned declarations)**: still **empty** — all 25 UAC-declared cefi venues have manifest presence.
- **M − C (drift)**: the **same 7 entries**, byte-identical (frozen): `BYBIT-FUTURES` (10,268, 100% `empty_confirmed`),
  `OKX` bare (5,225, 100% `attempted_failed`), `BINANCE-DELIVERY` (4,838), `OKEX-FUTURES` (36, 100% `empty_confirmed`),
  `CRYPTOFACILITIES` (10, 100% `empty_confirmed`), `OKX-OPTIONS` (2, 100% `attempted_failed`), `KALSHI_PERP` (2, 100%
  `attempted_failed`).

## 2. Census — instrument_type + data_type + chain axes (frozen, unchanged)

All §2 findings from the 08-18 report are carried unchanged (frozen manifest), not re-measured:

- **instrument_type** case-only variants (C2a `migration_pending`, suppressed): `PERPETUAL` 19,193,915 / `SPOT_PAIR`
  8,257,788 / `COMBO` 31,557 / `FUTURE` 1,663,935 / `OPTION` 282,535. Lowercase variants: `perpetual` 38,083 /
  `future` 1,191 / `spot_pair` 12. NULL = 162,190 / `""` = 157,337. Case-insensitive drift `index` 3,910 (DERIBIT
  `volatility_index` registry gap, carried P4).
- **data_type** (vs 9 canonical): 5 stray `ohlcv_{15m,15s,1d,1h,5m}` @ 2 `captured` each (10 total); `depth_of_book_10`
  39,120 rows (11,914 `captured`, self-heal confirmed durable, carried P2); `perp_daily_ctx` 7 `captured` (carried P4).
- **chain**: 100% blank (the 2026-07-28 chain-axis heal holds).

## 3. Honest-coverage — the 08-18 "rollup freeze" is RESOLVED; the rollup genuinely advanced

- **Today's (2026-08-19) `coverage.json` EXISTS** — `by_asset_group.cefi`: `captured=9,866,487`,
  `empty_confirmed=6,392,460`, `attempted_failed=892,679`, `expected_unattempted=10,894,199`, `total=28,045,825`,
  published `coverage_pct=45.57`, `storage_bytes_tb_mtds=47.7842`.
- **The 08-18 "rollup byte-identical / freeze" finding is RESOLVED** — vs 08-18 (`captured=9,842,980`, `total=
  28,022,318`, `coverage_pct=45.51`), today advanced **+23,507 captured** (and +23,507 total, coverage_pct 45.51 ->
  45.57) with `empty_confirmed`/`attempted_failed`/`expected_unattempted` all unchanged. **This also REFUTES the
  08-18 report's proposed root cause** (that the consolidator stall was feeding a stale snapshot into the coverage
  compute): the rollup advanced today *despite* the consolidator stall worsening (streak 89 -> 183). The freeze was a
  one-day **timing artifact** — the 08-18 coverage job computed at ~00:49 UTC, *before* the 08-18 02:13Z consolidator
  write, so it read the 08-17 snapshot; the 08-19 job (reading per-VM shards via the same fallback the census hits)
  picked up the newer capture. The two findings were coincident, not causal.
- **Formula re-verified** (per role scope) against the fresh 08-19 file:
  `9,866,487 / (9,866,487 + 892,679 + 10,894,199) = 9,866,487 / 21,653,365 = 45.566…%` — matches published `45.57`
  exactly. **No formula drift.**
- `instrument_gates_download=true` → coverage is a **lower bound** (Layer-2). `layer1_completeness_pct=94.52`
  (unchanged). `denominator_complete=false` / `denominator_status=INCOMPLETE` (unchanged).

## 4. What this run does NOT cover (declared, per the role's Tier-1 scope)

- No machine-oracle path-structure sweep, no id-form/schema Tier-1 sampled check or Tier-2 VM validation, no
  orphan-object sweep / delete suggestions — never this role.
- No batch-layer GCS-vs-manifest delimiter-descent spot-check this cycle (same as every prior run).
- **No census re-measure** — the consolidated manifest is frozen (P0), so §1-§2 are carried verbatim from the 08-18
  report rather than re-derived from an under-counting per-VM-shard fallback.
- Did not chase the consolidator lock's root cause (already dispatched via the P0 issue doc) nor any of the carried
  venue/data_type drift items (frozen, no new information).

## 5. No code fix this run

The single P0 (consolidator phantom lock) is already root-caused and dispatched for fix in
`manifest_consolidator_market_data_cefi_stuck_lock_2026_08_19.md` — it is not a "narrowly-scoped, well-understood"
fix this role's carve-out covers, and re-doing it here would collide with the already-dispatched engineer. Every other
finding is carried-unchanged (frozen) or resolved.

## 6. Todos

- [ ] [INFRA] P0. **Market-data-tick-cefi consolidator phantom lock — CORROBORATED this run, already filed +
      dispatched.** Streak escalated 89 -> 183, lock instance `1-b5a4d4fa` since 08-19T19:35Z, canonical index
      byte-frozen ~42h at generation 1787019237694916. **This is NOT a re-file** — the active P0 is
      `manifest_consolidator_market_data_cefi_stuck_lock_2026_08_19.md` (operator decision A, `assigned_vm: planning`);
      cite that doc. This run adds the fresher streak figure (183) and the frozen-generation confirmation as
      corroborating evidence only.
- [ ] [DATA] P2. **BINANCE-DELIVERY venue drift (4,838 rows, carried, frozen)** — includes 578 `attempted_failed` +
      5 `captured` + 4,255 `empty_confirmed`. Still needs the launcher/registry grep to confirm which config still
      probes it. Repo: market-tick-data-service / unified-api-contracts.
- [ ] [DATA] P2. **`depth_of_book_10` data_type registry gap (39,120 rows, 11,914 `captured`, carried, self-heal
      durable)** — produced by `bybit_futures_book_ticker_ws.py`, undeclared in `DATA_TYPES_BY_ASSET_GROUP["cefi"]`.
      Decide add-vs-document; an addition needs downstream consumers checked in the same change. Repo:
      unified-api-contracts.
- [ ] [INFRA] P3. **`phantom_audit` for cefi now 23 days stale** (was 22 on 08-18, zero remediation for 3+ weeks) —
      carried, escalating by 1 day. Repo: instruments-service.
- [ ] [DATA] P3. **CRYPTOFACILITIES (10) / OKEX-FUTURES (36)** — benign (100% `empty_confirmed`), frozen. Candidate for
      the accepted-exception list. Repo: unified-api-contracts.
- [ ] [DATA] P4. **`instrument_type=index` (3,910 rows, DERIBIT/volatility_index, carried, frozen)** — still undeclared
      in any cefi registry. Repo: unified-api-contracts.
- [ ] [DIAG] P4. **`perp_daily_ctx` data_type (7 `captured` rows, carried, frozen)** — confirm in-scope or
      expected-pilot. Repo: unified-api-contracts.

**Resolved this run (closed, not carried):** the 08-18 "honest-coverage rollup freeze" P1 (rollup advanced +23,507
captured today, refuting the consolidator-stall causal hypothesis — one-day timing artifact) and the "reprobe daily
cadence not confirmable" P4 (today's `reprobe_audit_latest.json` regenerated at 09:01Z, cadence confirmed).

## Progress Log

- **cefi_reconciliation_auditor 2026-08-19** [dispatch agt-419a6c, slot 28]: Phase 0 + freshness + honest-coverage
  verification complete, read-only. Headline: the market-data-tick-cefi consolidator phantom lock is CORROBORATED
  (streak 89 -> 183, canonical index byte-frozen ~42h at generation 1787019237694916) but already filed as P0
  (`manifest_consolidator_market_data_cefi_stuck_lock_2026_08_19.md`) and dispatched — not re-filed. Census carried
  verbatim (frozen manifest, §3f fallback read discarded as under-counting). Two carried todos resolved: the 08-18
  honest-coverage "rollup freeze" (today's rollup advanced +23,507 captured / coverage 45.51 -> 45.57, refuting the
  consolidator-stall causal link) and the reprobe daily-cadence P4 (regenerated 08-19T09:01Z). No code fix shipped.
