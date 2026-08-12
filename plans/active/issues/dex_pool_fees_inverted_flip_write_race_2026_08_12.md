---
doc_type: issue
title: >-
  Write-race + inverted flip on the dex_pool_fees retirement -- a second slot (issue-doc todo 1) overwrote the correct
  BALANCER-retire/CURVE-keep state with the OPPOSITE flip (14 CURVE retired, 7 BALANCER kept), a data-correctness
  incident
summary: >-
  On 2026-08-12 two AO slots executed overlapping `dex_pool_fees` retirements against the same canonical defi
  availability index. Slot 14 (plan todo 7, authorized by the BLK-b118f150 operator partial-go) applied the CORRECT flip
  at ~17:12Z -- retire the 7 content-verified BALANCER rows, keep the 14 CURVE rows captured -- and round-trip-verified
  14 remaining captured. A second slot working the issue-doc todo 1
  (`dex_pool_fees_phantom_premise_false_real_mid_may_objects_2026_08_12.md`) then overwrote the index at ~17:14:52Z with
  the INVERTED flip: the 14 CURVE rows (which have NO real `dex_pool_state` twin -- their canonical manifest rows are
  phantom, GCS-verified) were flipped `captured -> attempted_failed` with
  `error_reason=superseded_by_content_verified_canonical_dex_pool_state_twin_2026_08_12`, and the 7 BALANCER rows (which
  ARE content-verified redundant) were left `captured`. This is the exact opposite of the operator's authorized
  disposition and marks the only copy of CURVE pool-day fee data (fees_usd/volume_usd/tvl_usd, day=2026-05-16..22) as
  attempted-and-failed -- an honest-coverage accounting corruption. Fully reversible (status flips only, no rows/objects
  deleted). Recovery in progress: slot 14 applies a corrective flip (restore 14 CURVE -> captured, retire 7 BALANCER ->
  attempted_failed).
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service, agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags: [defi, dex-pool-fees, retirement, data-correctness, write-race, coordination, honest-coverage]
related:
  [
    /plans/active/defi_pool_rate_indices_dex_pool_fees_retirement_2026_08_10.md,
    /plans/active/issues/dex_pool_fees_phantom_premise_false_real_mid_may_objects_2026_08_12.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /codex/12-agent-workflow/host-concurrency-and-commit-provenance.md,
  ]
created: "2026-08-12"
last_updated: "2026-08-12"
source: >-
  Live finding by AO slot 14 (data_engineering) 2026-08-12 while executing plan todo 7 (dex_pool_fees verify+retire).
  Overlapping dispatch of the plan todo and the issue-doc disposition todo caused two concurrent writers to the same
  canonical index; the second writer's flip was inverted.
parent_epic: defi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: research
estimate_baseline_ai_days: 0.25
estimate_calibrated_ai_days: 0.3
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
    /plans/active/issues/dex_pool_fees_phantom_premise_false_real_mid_may_objects_2026_08_12.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
---

# Inverted `dex_pool_fees` flip from a write race (2026-08-12)

## What I found

Two AO slots executed overlapping `dex_pool_fees` retirements on the same canonical index
(`_index/availability_index.parquet`, `market-data-tick-defi-prd-central-element-323112`):

1. **Slot 14 (me, plan todo 7)**, authorized by the operator partial-go on BLK-b118f150, applied the CORRECT flip at
   ~17:12Z: retired the 7 BALANCER rows (content-verified redundant with the canonical `dex_pool_state` twin,
   `swap_fees` present on all 7 days), kept the 14 CURVE rows captured. Round-trip verify at 17:13:25Z confirmed **14
   remaining captured**. Snapshot + `.bak` written (`pre_dex_pool_fees_balancer_retire_20260812T170747Z` @ 17:09:17Z,
   `.dex_pool_fees_balancer_retire.bak` @ 17:10:46Z).

2. **A second slot** working issue-doc todo 1 (`dex_pool_fees_phantom_premise_false_real_mid_may_objects_2026_08_12.md`)
   overwrote the index at **17:14:52Z** (blob last_modified) with the **INVERTED flip**. Its own pre-write snapshots
   (`pre_dex_pool_fees_retire_20260812T170017Z` @ 17:01:59Z, `pre_dex_pool_fees_retire_20260812T171003Z` @ 17:11:33Z)
   bracket the window.

Live census + row-detail reads of the CURRENT index (2026-08-12, slot 14) show:

- `data_type=dex_pool_fees` `captured` = **7** (all BALANCER `0x06df3b2b`, day 2026-05-16..22) -- the rows that SHOULD
  be retired.
- `data_type=dex_pool_fees` `attempted_failed` = **14** (all CURVE `0x4dece678`/`0xbebc4478`, day 2026-05-16..22) with
  `error_reason=superseded_by_content_verified_canonical_dex_pool_state_twin_2026_08_12`.

The 14 CURVE rows are the ONLY record of their pool-day fee data: the CURVE `dex_pool_state` manifest rows for those 2
pools on those days are **phantom** (14 rows, `captured`, but **GCS object exists: False** for all 14 -- verified live
2026-08-12). So the second slot's flip marked the only copy of real financial data as attempted-and-failed, and left the
content-redundant BALANCER rows `captured`. Exact opposite of the operator's BLK-b118f150 partial-go ("retire the 7
BALANCER rows ... Do NOT touch the 14 CURVE rows").

## Why it matters

- **Honest-coverage accounting corruption**: 14 cells that genuinely hold captured fee data are now reported as
  attempted-and-failed (real coverage under-reported as a gap). The distinct-values / axis-census panel will mislabel
  them until corrected.
- **The CURVE fee data may be unique**: `fees_usd` / `volume_usd` / `tvl_usd` for those pool-days with no canonical
  `dex_pool_state` twin -- the flip labels it failed even though it is captured. Reversible (flip back), but a
  data-correctness violation of the kind the delete-safety protocol exists to prevent.
- **Root cause is a coordination gap**: two AO-eligible todos (the plan's P2 and the issue-doc P1) were dispatched for
  the SAME logical retirement, and the issue-doc slot's script inverted the twin logic (retired the no-twin rows). The
  dispatcher re-derived both from overlapping `- [ ]` checkboxes; nothing gated them on each other.
- Non-durable in the same way as the POOL recurrence: the next full rebuild re-registers real disk objects; a flip that
  mislabels real data is both wrong now and self-healing only in the wrong direction.

## Recommended decision

1. **Slot 14 applies the corrective flip now** (reversible, exactly the operator's BLK-b118f150 disposition): restore
   the 14 CURVE rows `attempted_failed -> captured` (clear `error_reason`), retire the 7 BALANCER rows
   `captured -> attempted_failed`
   (`error_reason=superseded_by_content_verified_canonical_dex_pool_state_twin_2026_08_12`). Consolidator paused before
   write / resumed after; snapshot + `.bak`; round-trip verify to captured=14 (CURVE) / attempted_failed=7 (BALANCER).
2. **Stop / reconcile the second slot's task** (`dex_pool_fees_phantom_premise_false_real_mid_may_objects-1119d9d2c3d8`)
   -- its script has an inverted twin-matching bug (it retired the no-twin rows). It must NOT re-apply. The issue-doc
   todo-1 checkbox should be reconciled against the corrective result.
3. **Process gap (tracked separately)**: overlapping `- [ ]` retirement todos in the plan + the issue doc got dispatched
   to two slots concurrently. Add a coordination note (or a `depends_on`/gate) when a plan todo's execution is split
   into an issue doc, so the two don't both write the same manifest index.

## Todos

- [ ] [DATA] P1. Apply the corrective flip: restore 14 CURVE `dex_pool_fees` rows to `captured` (clear `error_reason`)
      and retire the 7 BALANCER rows to `attempted_failed` per BLK-b118f150. (repo: market-tick-data-service) — in
      progress (slot 14)
- [ ] [DATA] P1. Reconcile issue-doc todo 1 (`dex_pool_fees_phantom_premise_...-1119d9d2c3d8`): its inverted script must
      not re-apply; mark the BALANCER retirement done based on the corrective result. (repo: agent-orchestrator) —
      operator/main: stop or re-scope the second slot's task
- [ ] [DATA] P2. Root-cause the second slot's inverted twin-matching (why it retired the no-twin CURVE rows) and add the
      coordination gate so plan + issue-doc retirement todos never dispatch concurrently to the same manifest. (repo:
      market-tick-data-service)

## Progress Log

- **2026-08-12 (slot 14, data_engineering)**: Incident established (see above). Slot 14's correct apply (BALANCER
  retired @ 17:12Z, round-trip verified 14 remaining) was overwritten at 17:14:52Z by the second slot's inverted flip.
  Current live state confirmed via fresh census + row-detail read (7 BALANCER captured / 14 CURVE attempted_failed with
  the superseded reason). `/blocked` filed to the operator; corrective flip in progress.
