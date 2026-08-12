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
- **Root cause is a lost-write race, NOT inverted twin-matching logic** (measured + corrected 2026-08-12, slot 7 — see
  Progress Log). Both dispatched scripts (plan todo-7 slot 14 + issue-doc todo-1 slot 20) had CORRECT twin-matching
  (twin-having rows → RETIRE, no-twin rows → EXCLUDE — verified in the committed script
  `retire_dex_pool_fees_balancer_legacy_captured_rows_2026_08_12.py` @ `market-tick-data-service@ad0db52396`). The
  transient "inverted" state came from a read-modify-write write-race: both writers rewrote the canonical
  `_index/availability_index.parquet` via plain non-CAS `upload_file`; writer 2's base read predated writer 1's write,
  so its full-blob upload silently reverted writer 1's rows while applying its own flip. The dispatcher re-derived both
  from overlapping `- [ ]` checkboxes; nothing gated them on each other.
- Non-durable in the same way as the POOL recurrence: the next full rebuild re-registers real disk objects; a flip that
  mislabels real data is both wrong now and self-healing only in the wrong direction.

## Recommended decision

1. **Slot 14 applies the corrective flip now** (reversible, exactly the operator's BLK-b118f150 disposition): restore
   the 14 CURVE rows `attempted_failed -> captured` (clear `error_reason`), retire the 7 BALANCER rows
   `captured -> attempted_failed`
   (`error_reason=superseded_by_content_verified_canonical_dex_pool_state_twin_2026_08_12`). Consolidator paused before
   write / resumed after; snapshot + `.bak`; round-trip verify to captured=14 (CURVE) / attempted_failed=7 (BALANCER).
2. **Stop / reconcile the second slot's task** (`dex_pool_fees_phantom_premise_false_real_mid_may_objects-1119d9d2c3d8`)
   -- it must NOT re-apply. (CORRECTED 2026-08-12, slot 7: the script does NOT have an inverted twin-matching bug — the
   inverted state was a non-CAS lost-write race; its logic is twin-having→RETIRE / no-twin→EXCLUDE.) The issue-doc
   todo-1 checkbox should be reconciled against the corrective result.
3. **Process gap (tracked separately)**: overlapping `- [ ]` retirement todos in the plan + the issue doc got dispatched
   to two slots concurrently. Add a coordination note (or a `depends_on`/gate) when a plan todo's execution is split
   into an issue doc, so the two don't both write the same manifest index.

## Todos

- [x] ✅ [DATA] P1. Apply the corrective flip: restore 14 CURVE `dex_pool_fees` rows to `captured` (clear
      `error_reason`) and retire the 7 BALANCER rows to `attempted_failed` per BLK-b118f150. (repo:
      market-tick-data-service) — **DONE 2026-08-12 (slot 20, data_engineering):
      `market-tick-data-service@d2014c87df`.** Live census confirmed the 7 BALANCER rows were already `attempted_failed`
      (correctly retired by a prior slot), so the flip was venue-determined: restored the 14 CURVE rows
      `attempted_failed -> captured` (error_reason cleared), retired 0 BALANCER (already in target state). Applied via
      `market-tick-data-service/scripts/one_offs/correct_dex_pool_fees_inverted_flip_2026_08_12.py --apply` (reversible
      status flip only, no row/object deleted). Round-trip verify on the rewritten `_index`: CURVE captured=14 /
      attempted_failed=0, BALANCER captured=0 / attempted_failed=7 — target disposition per BLK-b118f150 reached.
      Snapshot `_index/snapshots/pre_dex_pool_fees_correct_20260812T183039Z.parquet` + `.dex_pool_fees_correct.bak`
      written pre-write. Consolidator paused before write / resumed after (verified ENABLED). See Progress Log.
- [x] ✅ [DATA] P1. Reconcile issue-doc todo 1 (`dex_pool_fees_phantom_premise_...-1119d9d2c3d8`): its inverted script
      must not re-apply; mark the BALANCER retirement done based on the corrective result. (repo: agent-orchestrator) —
      **DONE 2026-08-12 (slot 18, data_engineering).** Verified the second slot's task
      (`dex_pool_fees_phantom_premise_false_real_mid_may_objects-1119d9d2c3d8`) is `status=done` + `orphan: true`
      (removed from backlog.yaml → the dispatcher cannot re-derive/re-dispatch it), `done_sha=ad0db52396`,
      `done_at=2026-08-12T18:09:35Z`. Its inverted script
      (`market-tick-data-service/scripts/one_offs/retire_dex_pool_fees_balancer_legacy_captured_rows_2026_08_12.py`) is
      a manual one-off `--apply` script with no cron/systemd trigger — it will not re-apply. No "stop" action was
      needed: the second slot's task already ran to completion. BALANCER retirement (7 rows) is the uncontested half of
      the disposition and is reconciled as done via the corrective flip (todo 1); the phantom-premise doc's todo-1
      checkbox now carries a reconciliation note pointing back here. See Progress Log.
- [x] ✅ [DATA] P2. Root-cause the second slot's inverted twin-matching (why it retired the no-twin CURVE rows) and add
      the coordination gate so plan + issue-doc retirement todos never dispatch concurrently to the same manifest.
      (repo: market-tick-data-service) — **DONE 2026-08-12 (slot 7, data_engineering).** ROOT-CAUSE = lost-write race,
      NOT inverted logic: both dispatched scripts have correct twin-matching (verified
      `retire_dex_pool_fees_balancer_legacy_captured_rows_2026_08_12.py` @ `market-tick-data-service@ad0db52396`:
      twin-having→RETIRE, no-twin→EXCLUDE); the transient inverted state was a non-CAS full-blob read-modify-write race
      (writer 2's base predated writer 1's 17:12Z write and silently reverted it). Coordination gate shipped
      `market-tick-data-service@6b557144` (verified at HEAD): CAS generation-match
      (`conditional_upload_file(if_generation_match=...)`) on all 4 dex_pool_fees scripts → stale-base writer REJECTED
      (exit 2, manifest UNCHANGED-SAFE); retire-all additionally HARD-ABORTs `--from + --apply`. UTL
      `conditional_upload_file` verified (None-on-PreconditionFailed, gcp.py:459). See Progress Log.
- [ ] [DATA] P3. Codify the manifest-write coordination gate in the data SSOT
      (`/codex/02-data/availability-manifest-and-data-status.md` or
      `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §5): any rewrite of a canonical consolidated `_index`
      MUST use CAS generation-match (`conditional_upload_file`) + pause the consolidator cron. Sibling one-off retire
      scripts (`retire_rate_indices_...`, `retire_pool_uppercase_...`, `retire_dex_swaps_...`, `retire_dex_pools_...`)
      predate the gate (historical, already-applied — no backfill needed; the pattern is the default for future
      retirements). (repo: unified-trading-pm)

## Progress Log

- **2026-08-12 (slot 14, data_engineering)**: Incident established (see above). Slot 14's correct apply (BALANCER
  retired @ 17:12Z, round-trip verified 14 remaining) was overwritten at 17:14:52Z by the second slot's inverted flip.
  Current live state confirmed via fresh census + row-detail read (7 BALANCER captured / 14 CURVE attempted_failed with
  the superseded reason). `/blocked` filed to the operator; corrective flip in progress.
- **2026-08-12 (slot 18, data_engineering) — todo 2 done: second slot's inverted script reconciled, will not re-apply.**
  Verified the second slot's task (`dex_pool_fees_phantom_premise_false_real_mid_may_objects-1119d9d2c3d8`) is
  `status=done` + `orphan: true` (removed from backlog.yaml → the dispatcher cannot re-derive/re-dispatch it),
  `done_sha=ad0db52396`, `done_at=2026-08-12T18:09:35Z`. Its script
  (`market-tick-data-service/scripts/one_offs/retire_dex_pool_fees_balancer_legacy_captured_rows_2026_08_12.py`) is a
  manual one-off `--apply` script with no cron/systemd trigger — it will not re-apply. No "stop" action was needed: the
  second slot's task already ran to completion. BALANCER retirement (7 rows) is the uncontested half of the disposition
  and is reconciled as done via the corrective flip (todo 1); the phantom-premise doc's todo-1 checkbox now carries a
  reconciliation note pointing back here.
- **2026-08-12 (slot 20, data_engineering) — todo 1 DONE: corrective flip applied + verified.** Fresh live census over
  the consolidated `_index` showed the 7 BALANCER rows were ALREADY `attempted_failed` (correctly retired by a prior
  slot) — only the 14 CURVE rows were still `attempted_failed` from the inverted flip. Wrote + ran
  `market-tick-data-service/scripts/one_offs/correct_dex_pool_fees_inverted_flip_2026_08_12.py --apply`
  (venue-determined: CURVE→captured, BALANCER→retired, memory-bounded row-group-at-a-time). Restored 14 CURVE rows
  `attempted_failed -> captured` (error_reason cleared), retired 0 (BALANCER already in target state). Consolidator
  paused pre-write / resumed after (verified ENABLED). Snapshot
  `_index/snapshots/pre_dex_pool_fees_correct_20260812T183039Z.parquet` + `.bak` written pre-write. Round-trip verify on
  the rewritten `_index`: CURVE captured=14 / attempted_failed=0; BALANCER captured=0 / attempted_failed=7 — the
  BLK-b118f150 target disposition. Ship: `market-tick-data-service@d2014c87df`.
- **2026-08-12 (slot 14, data_engineering) — PREMISE CORRECTION: the "CURVE is the only copy / phantom twin" claim was a
  wrong-vocabulary false negative; final disposition is retire-all-21 (0 captured / 21 attempted_failed).** Live
  content-verify (slot 14, fresh DuckDB census + GCS object + content reads over the live consolidated index) disproved
  this doc's premise: the canonical symbol-named CURVE `dex_pool_state` objects EXIST on all 7 days
  (`CURVE-ETHEREUM:POOL:USDC-CRVUSD.parquet`, `CURVE-ETHEREUM:POOL:DAI-USDC-USDT.parquet`) with content EXACTLY matching
  the legacy `dex_pool_fees` objects (day=2026-05-16 `0x4dece678`: canonical `daily_supply_revenue_usd=371.32` /
  `volume_usd=7,426,451` / `tvl_usd=23,787,340` == legacy `fees_usd=371.32` / same volume/tvl). The canonical
  ADDRESS-named path does NOT exist — the doc's "GCS object exists: False for all 14" probe was the SAME address-named
  wrong-vocabulary false negative slot 32 already corrected (see
  `dex_pool_fees_phantom_premise_false_real_mid_may_objects_2026_08_12.md` slot-32 entry). **Consequence**: todo-1's
  corrective flip (restore 14 CURVE to `captured`, `market-tick-data-service@d2014c87df`) was itself based on the false
  premise, and the 14 CURVE rows are now RE-RETIRED by plan todo-7's apply
  (`retire_dex_pool_fees_all_captured_rows_2026_08_12.py --apply`, `market-tick-data-service@9f5868e5`). Terminal state:
  **0 captured `dex_pool_fees` / 21 attempted_failed (7 BALANCER + 14 CURVE)** — the operator-confirmed BLK-9aed224f
  retire-all-21 disposition (the BLK-b118f150 partial-go predated the twin content-verification). The write-race
  coordination finding + todo-3 (root-cause the inverted twin-matching) remain valid and open. See plan
  `defi_pool_rate_indices_dex_pool_fees_retirement_2026_08_10.md` Progress Log 2026-08-12 (slot 14).
- **2026-08-12 (slot 7, data_engineering) — todo 3 DONE: root-cause established + coordination gate verified.**
  ROOT-CAUSE: the "inverted flip" was NOT inverted twin-matching logic. Both dispatched scripts have correct
  twin-matching (twin-having→RETIRE / no-twin→EXCLUDE — verified in
  `retire_dex_pool_fees_balancer_legacy_captured_rows_2026_08_12.py` @ `market-tick-data-service@ad0db52396`). The
  transient inverted state (14 CURVE retired / 7 BALANCER captured @ 17:14:52Z) was a lost-write race: both writers
  rewrote the canonical `_index` via plain non-CAS `upload_file`; writer 2's full-blob upload (base read predating
  writer 1's 17:12Z write) silently reverted writer 1's BALANCER-retire while applying its own flip. COORDINATION GATE:
  already shipped `market-tick-data-service@6b557144` (slot 20) — all 4 dex_pool_fees scripts capture the `_index`
  generation pre-download and write via `conditional_upload_file(if_generation_match=...)`; a stale-base writer's upload
  is REJECTED (exit 2, manifest UNCHANGED-SAFE), re-run applies idempotently on a fresh base; retire-all additionally
  HARD-ABORTs `--from + --apply`. Verified at HEAD in all 4 scripts + UTL `conditional_upload_file` returns None on
  PreconditionFailed (`unified_trading_library/cloud_interface/providers/gcp.py:459`). The issue doc's earlier "inverted
  twin-matching bug" framing is corrected in the body + Recommended decision #2. Dispatch-level coordination (never
  dispatch plan + issue-doc retirement todos for the same manifest concurrently) remains Recommended-decision #3 + new
  P3 follow-up.
