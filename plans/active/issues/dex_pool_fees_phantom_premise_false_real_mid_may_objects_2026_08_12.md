---
doc_type: issue
title: >-
  `dex_pool_fees` retirement premise is FALSE — 21 real subgraph-fee objects exist (day=2026-05-16..22) that the "0
  objects for its lifetime" sampling missed; the reversible-retirement flip would mislabel real data
summary: >-
  Todo 7 of `defi_pool_rate_indices_dex_pool_fees_retirement_2026_08_10.md` assumed the `dex_pool_fees` corpus was 0
  real objects for its entire lifetime (phantom manifest rows only). A live census + GCS object probe + content read
  (2026-08-12, slot 20) disprove it: all 21 `captured` `data_type=dex_pool_fees` rows are backed by 21 real parquet
  objects (~5.8KB each) at `raw_tick_data/.../day=2026-05-16..22/.../instrument_type=pool/data_type=dex_pool_fees/` for
  3 pools (CURVE x2 `0x4dece678..` / `0xbebc4478..`, BALANCER x1 `0x06df3b2b..`) on chain ETHEREUM,
  `pipeline_mode=batch_onchain_subgraph`. The objects were materialised 2026-06-21 (`available_at` column) and carry
  real `fees_usd` / `volume_usd` / `tvl_usd` (e.g. CURVE `0x4dece678..` 2026-05-16: fees_usd=371.3,
  volume_usd=7,426,451, tvl_usd=23,787,341). The manifest rows were (re)registered `captured` by the 2026-08-10 rebuild
  VM scan (`written_at=2026-08-10T23:08-23:10Z`, `service_name=market-tick-data-service`). The retirement script's own
  physical-object safety gate correctly refused to flip them (RETIRE 0 / EXCLUDE 21). Disposition is operator-gated: the
  7 BALANCER rows have a canonical `dex_pool_state` twin (`swap_fees` on all 7 days) -> retire-as-superseded is feasible
  after content-verify; the 14 CURVE rows have NO `dex_pool_state` twin on those days -> their fee data may be the only
  copy and must be migrated or kept, never flipped to `attempted_failed`.
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service, strategy-service, unified-trading-pm]
scope: [engineer, admin]
tags: [defi, dex-pool-fees, retirement, data-correctness, phantom-premise, rebuild, manifest, honest-coverage]
related:
  [
    /plans/archive/2026_08/defi_pool_rate_indices_dex_pool_fees_retirement_2026_08_10.md,
    /plans/archive/issues/defi_dex_pool_fees_retirement_recommendation_2026_08_04.md,
    /plans/active/issues/defi_pool_uppercase_recurrence_after_fold_2026_08_11.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /codex/02-data/honest-absence-downstream-handling.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
  ]
created: "2026-08-12"
last_updated: "2026-08-12"
source: >-
  Live finding by AO slot 20 (data_engineering) during todo 7 of
  defi_pool_rate_indices_dex_pool_fees_retirement_2026_08_10.md — the retirement script's dry-run census + GCS object
  probe + content read disproved the plan's "0 objects for its entire lifetime / phantom rows only" premise: 21 real
  mid-May objects back the 21 captured rows.
parent_epic: defi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: research
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.6
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
depends_on: []
context_scope:
  [
    /plans/archive/2026_08/defi_pool_rate_indices_dex_pool_fees_retirement_2026_08_10.md,
    /plans/archive/issues/defi_dex_pool_fees_retirement_recommendation_2026_08_04.md,
    /plans/archive/issues/dex_pool_fees_inverted_flip_write_race_2026_08_12.md,
    /codex/02-data/defi-canonical-naming-ssot.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    market-tick-data-service/scripts/one_offs/retire_dex_pool_fees_legacy_captured_rows_2026_08_12.py,
  ]
---

# `dex_pool_fees` retirement premise is FALSE — 21 real objects exist (2026-08-12 finding)

## What I found

Task: todo 7 of `plans/archive/2026_08/defi_pool_rate_indices_dex_pool_fees_retirement_2026_08_10.md` — "Verify + retire
`dex_pool_fees` legacy `captured` rows if any remain", whose premise (from the archived
`defi_dex_pool_fees_retirement_recommendation_2026_08_04.md` + the distinct-values plan) was: **"the corpus itself was 0
real objects for its whole lifetime, phantom manifest rows only."**

A live census (2026-08-12, slot 20) over the fresh consolidated defi availability index
(`_index/availability_index.parquet`, 42 cols, 158,267,760 rows, last-consolidated fresh) + a direct GCS object probe +
a parquet content read found:

1. **`data_type=dex_pool_fees` `capture_status=captured` = 21 rows** (the baseline todo 1 measured 2026-08-11). The full
   status distribution is `{'captured': 21}` — no `attempted_failed` / `empty_confirmed` rows exist for this data_type.
2. **Every one of the 21 rows is backed by a real physical GCS object** (my `retire_dex_pool_fees...py` script's
   physical-object probe — an analog of delete-safety-protocol Part 1/2 — classified RETIRE 0 / EXCLUDE 21). The objects
   sit at
   `raw_tick_data/by_date/day=2026-05-16..22/pipeline_mode=batch_onchain_subgraph/asset_group=defi/venue={CURVE|BALANCER}/chain=ETHEREUM/instrument_type=pool/data_type=dex_pool_fees/{VENUE}_ETHEREUM_{short8}_2026-05-1X.parquet`,
   ~5,837–5,852 bytes each.
3. **The objects hold real, non-trivial data** (content read):
   - CURVE pool `0x4dece678ceceb27446b35c672dc7d61f30bad69e`, day 2026-05-16: `fees_usd=371.32`,
     `volume_usd=7,426,451.36`, `tvl_usd=23,787,340.92`, `source=thegraph_subgraph`.
   - CURVE pool `0xbebc4478...` and BALANCER pool `0x06df3b2bbb68adc8b0e302443692037ed9f91b42`: same real column shape
     (`fees_usd`/`volume_usd`/`tvl_usd`); BALANCER 05-16 `fees_usd=1.64`, `volume_usd=32,890.66`, `tvl_usd=35,524.84`.
   - **`available_at = 2026-06-21T22:43Z`** on the objects — they were materialised on **2026-06-21**, i.e. the
     `materialize_dex_pool_fees.py` campaign DID write real objects for a 7-day mid-May window (day=2026-05-16..22),
     before its 2026-08-04 retirement.
4. **The manifest rows were (re)registered `captured` by the 2026-08-10 rebuild VM scan**:
   `written_at=2026-08-10T23:08–23:10Z`, `service_name=market-tick-data-service`. This is the same rebuild chain
   (`canonical-migration-defi-rebuild-20260810-204358`) whose upsert-onto-existing manifest semantics were established
   in todo 3 — the rebuild scans real disk objects and registers them; it did not invent these rows. Before the rebuild
   these cells were on disk but **unregistered** (a coverage gap the rebuild honestly closed).
5. **Twin analysis** (GCS object listing, pool short-hash prefix match against canonical `dex_pool_state` objects on the
   same day/venue/chain):
   - **BALANCER** pool `0x06df3b2bbb68adc8b0e302443692037ed9f91b42`: a canonical `dex_pool_state` object exists on **all
     7 days** (`0x06df3b2bbb68adc8b0e302443692037ed9f91b42000000000000000000000063.parquet`), carrying `swap_fees`,
     `swap_volume`, `total_shares`, `instrument_id=BALANCER-ETHEREUM:POOL:0x06df3b2b...63`. The `dex_pool_fees` BALANCER
     rows are therefore content-redundant candidates (twin-verify then retire-as-superseded).
   - **CURVE** pools `0x4dece678...` (USDC-CRVUSD) and `0xbebc4478...` (DAI-USDC-USDT): the ORIGINAL twin analysis was a
     **wrong-vocabulary false negative** — it prefix-matched `dex_pool_state` FILENAMES by pool address, but CURVE state
     files are SYMBOL-named. Content-verified 2026-08-12 (slot 32): both pools HAVE canonical `dex_pool_state` objects
     on **all 7 days** (`CURVE-ETHEREUM:POOL:USDC-CRVUSD.parquet`, `CURVE-ETHEREUM:POOL:DAI-USDC-USDT.parquet`),
     carrying the SAME `volume_usd`/`tvl_usd` and `daily_supply_revenue_usd == dex_pool_fees.fees_usd` (e.g.
     `0x4dece678` 2026-05-16: volume=7,426,451.36 / tvl=23,787,340.92 / fees_usd=371.32). The 14 CURVE rows are
     content-redundant with canonical `dex_pool_state` — retiring them (reversible `captured→attempted_failed` flip, no
     object deleted) loses nothing.

## Why it matters

- **The plan's retirement premise is false.** The "0 objects for its entire lifetime" claim came from the 2026-08-04
  recommendation's sampling of `day=2026-06..2026-08` paths — it never probed `day=2026-05-16..22`, where the 21 real
  objects actually live. A measurement gap, now closed by the census. This is the same "CLAIM ≤ MEASUREMENT" class that
  bit the POOL/rate_indices retirements.
- **The reversible `captured → attempted_failed` flip is UNSAFE only where no canonical twin exists.** The original
  finding flagged a silent-orphaning risk for the 14 CURVE rows under the (now-disproven) "no twin / only record"
  premise — that premise was a wrong-vocabulary false negative (see the corrected twin analysis above). Content-verified
  canonical `dex_pool_state` twins cover all 14 CURVE rows, so the flip loses no data. The delete-safety protocol's Part
  1/2/5 (twin must resolve + content-verify + legacy-COPIED-not-MOVED invariant) is exactly why the retirement script's
  probe gate caught the missing-twin case before any write — and why the corrected script content-verifies the twin
  before flipping.
- **Flipping would also be non-durable**: the next full manifest rebuild re-registers real objects it finds on disk (as
  this rebuild did), silently resurrecting the rows — the same "fixed, then silently reverted" cycle the POOL recurrence
  issue doc warns about.
- The distinct-values / axis-census panel will keep showing `dex_pool_fees` as a non-canonical `captured` data_type
  until a real disposition lands. That is CORRECT until the disposition is decided — the rows describe real data.

## Recommended decision

Disposition is operator-gated (it touches the 2026-08-04 `dex_pool_fees` retirement ruling, whose empty-corpus premise
is now partially false). Options:

- **A (safe stopgap)**: content-verify the 7 BALANCER `dex_pool_fees` rows against the canonical `dex_pool_state` twin
  (`swap_fees`), then retire them as superseded (reversible flip, no row/object removed). Keep the 14 CURVE rows
  `captured` pending their canonical migration. Partial done-when (14 remain).
- **B (complete, bigger scope)**: migrate the CURVE fee data into canonical `dex_pool_state` for day=2026-05-16..22 (the
  `dex_pool_fees` column shape `fees_usd`/`volume_usd`/`tvl_usd` matches the canonical CURVE `dex_pool_state` schema),
  then retire all 21 legacy rows. Full done-when, but a real data-migration decision + work.
- **C (re-scope)**: treat the corpus as real; leave all 21 `captured`; reconsider whether the 2026-08-04 retirement
  ruling should apply to a non-empty corpus at all (the panel keeps flagging `dex_pool_fees` as non-canonical until
  either a migration or an accepted-exception).
- **D (NOT recommended)**: flip all 21 to `attempted_failed` anyway (retire the concept regardless of real data). This
  is the data-correctness violation the finding exists to prevent.

Worker recommendation: **A for all 21** — the corrected twin analysis (slot 32, content-verified) shows BOTH CURVE pools
have canonical `dex_pool_state` twins on all 7 days, so the 14 CURVE rows are content-redundant exactly like the 7
BALANCER rows. Options B (migrate — data already canonical) and C (keep as only record — premise false) are both moot.
Operator confirmed **A** on BLK-9aed224f (2026-08-12): retire all 14 CURVE rows via the reversible flip.

## Todos

- [x] ✅ [DATA] P1. Content-verify the 7 BALANCER `dex_pool_fees` rows are redundant with the canonical `dex_pool_state`
      twin (same pool `0x06df3b2b...42`, day=2026-05-16..22, `swap_fees` vs `fees_usd`), then retire them as superseded
      via the reversible `captured→attempted_failed` flip. (repo: market-tick-data-service) — gated on operator Option
      A. **DONE 2026-08-12 (slot 20, data_engineering): `market-tick-data-service@ad0db52396`.** Content-verified all 7
      BALANCER cells against their canonical `dex_pool_state` twin (poolId `0x06df3b2b...63`) — legacy `fees_usd` vs
      canonical `swap_fees` logged per day (05-16..22); BALANCER `swap_fees` is cumulative, so comparison is
      presence-of-fee-data. Applied via `retire_dex_pool_fees_balancer_legacy_captured_rows_2026_08_12.py --apply`
      (reversible `captured→attempted_failed`, no row/object deleted): RETIRED 7 / EXCLUDED 14 (CURVE, retired
      separately by todo 2's script). Round-trip verify: 7 BALANCER rows `attempted_failed`, live index confirm 21 total
      `attempted_failed` (7 BALANCER + 14 CURVE). Script renamed `*_balancer_*` to coexist with the CURVE-scoped sibling
      (same original filename collided add/add with slot 32's todo-2 script). Consolidator paused pre-write / resumed
      after. See Progress Log 2026-08-12 (slot 20, todo-1) entry. **Reconciled 2026-08-12 (slot 18, data_engineering)
      against the corrective result — see `/plans/archive/issues/dex_pool_fees_inverted_flip_write_race_2026_08_12.md`.**
      The concurrent-write race between this todo's slot and the plan-todo-7 slot produced a transient inverted index
      state (~17:12–17:14:52Z); this todo's task
      (`dex_pool_fees_phantom_premise_false_real_mid_may_objects-1119d9d2c3d8`) is now `status=done` + `orphan: true`
      (removed from backlog.yaml, cannot re-dispatch) and its script is a manual one-off — it will not re-apply. The
      7-row BALANCER retirement (the uncontested half of the disposition) is authoritative via the corrective flip in
      the inverted-flip issue doc (todo 1).
- [x] ✅ [DATA] P1. Decide the disposition of the 14 CURVE `dex_pool_fees` rows (2 pools, no `dex_pool_state` twin):
      migrate fee data into canonical `dex_pool_state` (Option B) or keep `captured` as the only record (Option C).
      Operator decision; then execute. (repo: market-tick-data-service) — **DONE 2026-08-12 (slot 32, data_engineering):
      `market-tick-data-service@0e9de0cb`.** Disposition = **A (retire-as-superseded)**, operator confirmed
      BLK-9aed224f. The "no `dex_pool_state` twin" premise was a wrong-vocabulary false negative (CURVE state files are
      SYMBOL-named: `CURVE-ETHEREUM:POOL:USDC-CRVUSD.parquet` / `DAI-USDC-USDT.parquet`, not address-named).
      Content-verified both pools' canonical `dex_pool_state` twins on all 7 days (volume/tvl identical;
      `fees_usd == `daily_supply_revenue_usd`). Applied via `retire_dex_pool_fees_legacy_captured_rows_2026_08_12.py
      --apply` (reversible`captured→attempted_failed`, no row/object deleted): RETIRED 14, EXCLUDED 0. Round-trip verify: 0 remaining captured `dex_pool_fees`CURVE rows. Consolidator was already PAUSED (precondition met), left as-is (the later "Resume the consolidator" todo owns it). Snapshot`_index/snapshots/pre_dex_pool_fees_retire_*.parquet`+ `.dex_pool_fees_retire.bak`
      written pre-write.
- [ ] [DATA] P2. Correct the now-disproven "0 objects for its entire lifetime / phantom rows only" claim in the current
      plan's todo-7 premise + the archived `defi_dex_pool_fees_retirement_recommendation_2026_08_04.md` (the 2026-08-04
      sample covered day=2026-06..08 only; the mid-May objects were never probed). (repo: unified-trading-pm)

## Progress Log

- **2026-08-12 (slot 20, data_engineering)**: Finding established via the retirement script's dry-run census + a
  targeted GCS/object-content probe (see above). `retire_dex_pool_fees_legacy_captured_rows_2026_08_12.py` written
  (mirrors the rate_indices pattern, with a physical-object probe safety gate) — dry-run measured 21 captured rows,
  RETIRE 0 / EXCLUDE 21, no write made. The script is the template for whatever disposition lands; it must be extended
  with the twin-verify logic (Option A) or a migration path (Option B) before `--apply`. `/blocked` filed to the
  operator with options A/B/C/D.
- **2026-08-12 (slot 32, data_engineering) — CURVE-twin premise CORRECTED: both CURVE pools have content-verified
  `dex_pool_state` twins on all 7 days.** The original twin analysis prefix-matched `dex_pool_state` FILENAMES by pool
  address and concluded "no CURVE twin" — a wrong-vocabulary false negative, because CURVE state files are SYMBOL-named
  (`CURVE-ETHEREUM:POOL:USDC-CRVUSD.parquet`, `CURVE-ETHEREUM:POOL:DAI-USDC-USDT.parquet`), not address-named. A content
  scan of the `pool_address`/`instrument_id` columns of CURVE `dex_pool_state` objects across day=2026-05-16..22 (plus
  adjacent days 05-15/05-23/05-30/06-01/06-10/06-21/07-01/07-13/08-01/08-05) found BOTH pools present on all 7 window
  days, with values that EXACTLY cross-match the `dex_pool_fees` objects: pool `0x4dece678` 2026-05-16
  volume=7,426,451.36 / tvl=23,787,340.92 (identical in both corpora) and `fees_usd=371.32` == the state object's
  `daily_supply_revenue_usd`. The manifest independently confirms 14 captured `dex_pool_state` rows (bare-address
  instrument_ids) for both pools on all 7 days. **Options B (migrate) and C (keep as only record) are both MOOT — the 14
  CURVE rows are content-redundant superseded duplicates, exactly like the 7 BALANCER rows.** Wrote
  `market-tick-data-service/scripts/one_offs/retire_dex_pool_fees_legacy_captured_rows_2026_08_12.py` (the slot-20
  script never landed — it was dry-run only) extending the rate_indices pattern: legacy short8
  `{VENUE}_{CHAIN}_{short8}_{date}` id → full `pool_address` read from the legacy object → twin-verify against captured
  `dex_pool_state` ids on the same (venue, chain, date). `/blocked` BLK-9aed224f → operator confirmed **A** (retire all
  14 CURVE rows, reversible flip). Disposition for the full 21-row corpus is now retire-as-superseded.
- **2026-08-12 (slot 20, data_engineering) — todo 1 DONE: 7 BALANCER rows content-verified + retired.** Extended the
  original slot-20 script with twin-verify (BALANCER poolId `0x06df3b2b...63` vs legacy `short8`) and applied
  `retire_dex_pool_fees_balancer_legacy_captured_rows_2026_08_12.py --apply`: RETIRED 7 / EXCLUDED 14, round-trip verify
  = 7 BALANCER `attempted_failed`. **Coordination finding (same-turn): the BALANCER script and slot 32's CURVE script
  were authored under the SAME filename `retire_dex_pool_fees_legacy_captured_rows_2026_08_12.py`, causing an add/add
  conflict on quickmerge.** Resolved by renaming mine to `*_balancer_*` (peer's CURVE script kept the original name) —
  both ship as distinct files. Also observed a transient stale-read: an in-flight consolidated-index read momentarily
  showed 14 CURVE still `captured` after my upload (the two scripts rewrite the same blob non-atomically), but a fresh
  DuckDB verify confirms the terminal state is **21 `attempted_failed`** (7 BALANCER + 14 CURVE) — the full
  operator-confirmed disposition. Consolidator resumed (ENABLED). Ship: `market-tick-data-service@ad0db52396`.
**context-scout 2026-08-17**: populated/refreshed context_scope (5 entries)
- **context-scout 2026-08-20**: populated/refreshed context_scope (6 entries)
