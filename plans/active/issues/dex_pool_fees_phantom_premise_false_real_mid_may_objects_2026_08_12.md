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
    /plans/active/defi_pool_rate_indices_dex_pool_fees_retirement_2026_08_10.md,
    /plans/archive/issues/defi_dex_pool_fees_retirement_recommendation_2026_08_04.md,
    /plans/active/issues/defi_pool_uppercase_recurrence_after_fold_2026_08_11.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /codex/02-data/honest-absence-downstream-handling.md,
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
    /plans/active/defi_pool_rate_indices_dex_pool_fees_retirement_2026_08_10.md,
    /plans/archive/issues/defi_dex_pool_fees_retirement_recommendation_2026_08_04.md,
    /codex/02-data/defi-canonical-naming-ssot.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
---

# `dex_pool_fees` retirement premise is FALSE — 21 real objects exist (2026-08-12 finding)

## What I found

Task: todo 7 of `plans/active/defi_pool_rate_indices_dex_pool_fees_retirement_2026_08_10.md` — "Verify + retire
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
   - **CURVE** pools `0x4dece678...` and `0xbebc4478...`: **NO `dex_pool_state` object exists on any of the 7 days** for
     either pool (the CURVE `dex_pool_state` cell listings for those days contain no object whose address starts with
     either pool's address). Their `fees_usd`/`volume_usd`/`tvl_usd` may be the **only** record of that pool-day fee
     data. They must NOT be flipped to `attempted_failed` without a canonical home for the data.

## Why it matters

- **The plan's retirement premise is false.** The "0 objects for its entire lifetime" claim came from the 2026-08-04
  recommendation's sampling of `day=2026-06..2026-08` paths — it never probed `day=2026-05-16..22`, where the 21 real
  objects actually live. A measurement gap, now closed by the census. This is the same "CLAIM ≤ MEASUREMENT" class that
  bit the POOL/rate_indices retirements.
- **The reversible `captured → attempted_failed` flip is UNSAFE for these rows.** It would mark 21 cells that genuinely
  hold captured data as "attempted and failed" — an honest-coverage accounting corruption (real coverage under-reported
  as a gap) and, for the 14 CURVE rows, a silent orphaning of possibly-unique financial data from coverage accounting.
  The delete-safety protocol's Part 1/2/5 (twin must resolve + content-verify + legacy-COPIED-not-MOVED invariant)
  exists precisely to prevent this class of mistake; the retirement script's probe gate is what caught it before any
  write.
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

Worker recommendation: **A**, then a follow-up migration decision for the 14 CURVE rows (B or C).

## Todos

- [ ] [DATA] P1. Content-verify the 7 BALANCER `dex_pool_fees` rows are redundant with the canonical `dex_pool_state`
      twin (same pool `0x06df3b2b...42`, day=2026-05-16..22, `swap_fees` vs `fees_usd`), then retire them as superseded
      via the reversible `captured→attempted_failed` flip. (repo: market-tick-data-service) — gated on operator Option A
- [ ] [DATA] P1. Decide the disposition of the 14 CURVE `dex_pool_fees` rows (2 pools, no `dex_pool_state` twin):
      migrate fee data into canonical `dex_pool_state` (Option B) or keep `captured` as the only record (Option C).
      Operator decision; then execute. (repo: market-tick-data-service)
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
