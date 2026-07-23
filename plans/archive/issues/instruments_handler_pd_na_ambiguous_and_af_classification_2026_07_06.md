---
doc_type: issue
title:
  InstrumentsHandler "boolean value of NA is ambiguous" blocks HYPERLIQUID captures + classification of 12 non-ASTER
  cefi MVP attempted_failed cells (B0 residual)
summary: |
  Surfaced 2026-07-06 while classifying the residual MVP-scoped attempted_failed cells for B0 in
  `is_catalogue_completion_2d_2026_07_06.md`. The 12 non-ASTER cefi MVP AF cells split into two classes on inspection.
  (1) FOUR HYPERLIQUID truly-missing days (2024-09-12/28, 2024-12-31, 2026-03-18) all fail the same way — a DEBUG-log
  retry (2026-07-06 15:05Z) reproduced `Handler InstrumentsHandler failed on payload 1: boolean value of NA is
  ambiguous` and "Batch complete: 0 results collected" with NO manifest write. Root class = pandas NA-in-boolean bug in
  the InstrumentsHandler process path (or a downstream pandas op the handler drives) that hits specifically on
  HYPERLIQUID payload shapes; every HL retry crashes at the same step, so this is a repeatable adapter/handler bug not
  a transient. (2) FOUR 2026-06-23 cells (BINANCE-SPOT / BITFINEX-SPOT / BITGET-SPOT / BITGET-FUTURES all
  attempted_at=2026-06-23T13:14:05.978Z — same millisecond, so a single upstream batch fault) are stale-AF rows —
  their same-cell captured rows already exist (written 2026-06-26/27); classification =
  RESOLVED_STALE_AF_KNOWN_MANIFEST_DEDUP-P2. The remaining FOUR non-truly-missing HYPERLIQUID cells (2023-12-01/13,
  2025-01-18, 2026-06-06) are also stale-AF (co-existing captured rows found) — same root class as (2). Tradfi CME
  residual = 1 AF (2026-06-20) + 6 EU sparse dates (2024-07-08, 2024-11-26, 2024-12-04, 2025-08-07, 2025-08-18,
  2026-06-24); pattern (mostly single sparse days) is consistent with market-calendar/upstream Databento gaps, needs
  per-date confirmation.
status: resolved
nature: notes
asset_group: [cefi, tradfi]
stage: [data]
repos: [instruments-service, unified-trading-library]
scope: [engineer]
tags: [instruments, adapter-bug, honest-coverage, mvp, af-classification, b0-residual, pd-na]
related:
  [
    ../is_catalogue_completion_2d_2026_07_06.md,
    ../instruments_completion_tracker_2026_07_06.md,
    ../instruments_mtds_subset_consistency_remediation_2026_06_17.md,
    ../pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md,
  ]
created: 2026-07-06
assigned_vm: planning
source:
  [
    is_catalogue_completion_2d_2026_07_06.md B0 gate — classification residual per main-agent BLK-749ae284 answer,
    live DEBUG retry of HYPERLIQUID 2024-09-12 (2026-07-06 15:05Z),
    live retry of BITFINEX-SPOT 2023-12-16 + KRAKEN-FUTURES 2023-12-16..19 (2026-07-06 15:00/15:01Z),
  ]
execution_scope: orchestrator-agent
priority: P2
drift_direction: advance-code
depends_on: []
locked_by: live-defi-rollout
locked_since: 2026-05-21
parent_epic: instruments_master
resolved_by:
  unified-trading-library@b7925334 (pd.NA fix + live-verified) + tradfi CME calendar verify (2026-07-06) + cefi stale-AF
  reconcile (2026-07-07, slot-7)
---

## What I found

### 1. InstrumentsHandler pd.NA bug — HYPERLIQUID payload shape breaks the write pipeline

Live retry of `HYPERLIQUID 2024-09-12`
(`instruments-service --operation instruments --mode batch --asset-group cefi --venues HYPERLIQUID --start-date 2024-09-12 --end-date 2024-09-12 --force --log-level DEBUG`)
reproduced the failure cleanly:

- URDI[HYPERLIQUID]: fetched 176 instruments (11 subventures 429-rate-limited on the `earliest-funding` probe — fallback
  to launch date, non-fatal).
- Date filter 2024-09-12: 109 instruments active.
- ManifestWriter GET `_index/availability_index.parquet` succeeded (existing index read OK).
- `_index/per_vm/local-*.parquet` 404 (expected — no prior shard on this host).
- `WARNING Handler InstrumentsHandler failed on payload 1: boolean value of NA is ambiguous`.
- `INFO Batch complete: 0 results collected` → no captured row written.

Repro rate = 100% on retry; every truly-missing HYPERLIQUID day has the same fingerprint. The other three (2024-09-28,
2024-12-31, 2026-03-18) share the same one-shot attempt-then-crash pattern (`attempted_at == written_at ± 6ms`,
`row_count=0`, `error_reason=UNCLASSIFIED_ADAPTER_ERROR`) so they are the same bug — the classifier didn't recognise the
pd.NA ValueError.

The BITFINEX-SPOT smoke retry hit a DIFFERENT pandas warning (`Cannot convert ['2839'…] to numeric`) which is a
non-fatal payload-1 warning and did NOT block the write ("`5 new` entries in the availability index"). So the pd.NA
ambiguity is HYPERLIQUID-shape-specific, not a global handler bug.

### 2. Four 2026-06-23 cefi cells are STALE-AF (not truly missing)

BINANCE-SPOT / BITFINEX-SPOT / BITGET-SPOT / BITGET-FUTURES all show `attempted_at = 2026-06-23T13:14:05.978Z` — the
same millisecond across four venues, so a single upstream batch fault (network / auth / Tardis-side). All four cells now
have same-day captured rows written 2026-06-26/27 → the AF rows are STALE, the data is present. Same dedup class as the
`pipeline_mode_source_batch_live_replay_standardisation_2026_06_05` finding: when the (venue,date) gets a retry into
`captured` the writer emits a new row with populated `instrument_type/pipeline_mode/source`, and the manifest dedup key
mismatch keeps the blank-shard-atom failed row alongside.

### 3. Four "stale-AF" HYPERLIQUID cells co-exist with captured data

HYPERLIQUID 2023-12-01, 2023-12-13, 2025-01-18, 2026-06-06 all show co-existing captured rows in the same (venue,date) —
classification = same stale-AF class as (2). Only the four (2024-09-12/28, 2024-12-31, 2026-03-18) are TRULY missing (no
matching captured row), and all four hit the pd.NA handler bug on retry.

### 4. Tradfi CME residual — market-calendar / Databento sparse gaps

`CME 2026-06-20` AF (1 cell) + `CME` EU on 2024-07-08 / 2024-11-26 / 2024-12-04 / 2025-08-07 / 2025-08-18 / 2026-06-24
(6 cells). Pattern is single-day sparse gaps — 2024-11-26 sits adjacent to US Thanksgiving 2024 (Thanksgiving = Nov 28),
2024-07-08 immediately post-July-4-observed. Consistent with market-calendar edges or Databento missing-day gaps. Not
the same class as the HL adapter bug; needs per-date confirmation against the Databento CME calendar / TradFi v9 apply
completion (in-flight via `tradfi_v9_stage1_finish_2026_07_06.md`).

## Why it matters

- The pd.NA handler bug is the ROOT class of 4 truly-missing MVP HYPERLIQUID cells — every retry crashes at the same
  point, so this is on the honest-coverage critical path (cefi Layer-1 for HYPERLIQUID cannot go 100% until the handler
  write step accepts the payload shape).
- The classification unblocks B0's "0 missing MVP" gate per the main-agent BLK-749ae284 answer: 40 ASTER = Stage-2c
  in-flight (accepted); 24 cefi EU 2023-12-16..19 = historical service outage floor (accepted, document); 12 cefi AF now
  classified into the two named classes above (accept 8 as RESOLVED_STALE_AF, accept 4 as KNOWN_HANDLER_BUG_PD_NA with a
  fix TODO); 7 tradfi CME residual = market-calendar/Databento gap (accept, verify post-tradfi-v9-apply).
- Follow-on: TRUE 0-missing requires (a) the pd.NA fix so HL truly-missing days clear on retry, (b) the manifest dedup
  fix (already tracked P2 in `pipeline_mode_source_batch_live_replay_standardisation_2026_06_05`) so stale-AF rows
  collapse, and (c) the tradfi v9 apply chain completing (already tracked in `tradfi_v9_stage1_finish`). None of these
  are in scope for B0's flip — they're separate tracked items.

## Recommended decision

Accept the classification and flip B0. Track the pd.NA fix + tradfi CME verify as the P1/P2 todos below.

- [x] ✅ [CODE] P1. Reproduce + fix the InstrumentsHandler "boolean value of NA is ambiguous" on HYPERLIQUID payloads;
      first reproduce with
      `.venv/bin/python -m instruments_service --operation instruments --mode batch --asset-group     cefi --venues HYPERLIQUID --start-date 2024-09-12 --end-date 2024-09-12 --force --log-level DEBUG`,
      capture the full traceback (raise `logger` in `cli/instruments_handler.py` to log the exception's traceback not
      just the "failed on payload" one-liner), narrow to the pandas op that receives a pd.NA in a boolean context, guard
      with `pd.isna(…)` or `.fillna(False)`. Verify by re-running the 4 truly-missing HYPERLIQUID days (2024-09-12/28,
      2024-12-31, 2026-03-18) and confirming `capture_status=captured` in the manifest. (repo: instruments-service)
      **DONE 2026-07-07 07:11 UTC — unified-trading-library@b7925334 (slot-9 planning).** Root-caused NOT in
      instruments-service but in **UTL `manifest_writer/_writer_io.py`**: three call sites (`_b`, `_s`, and
      `_coerce_bool`) guarded pd-NA only via `isinstance(value, float) and pd.isna(value)`, which catches float NaN but
      MISSES `pd.NA` (nullable BooleanDtype). When the manifest carried a `pd.NA` in `expected`/`available` (the payload
      shape HYPERLIQUID 2024-09-12 hit), `bool(pd.NA)` raised `TypeError: boolean value of NA is ambiguous` and the
      handler crashed at payload 1 → "Batch complete: 0 results collected" → no manifest write. **Fix:** switched to
      `pd.isna(value)` unconditionally (handles float NaN, pd.NA, pd.NaT); introduced a local `_is_na` scalar-safe
      helper. Also added `exc_info=exc` on the UTL adapter's per-payload failure log so a `--log-level DEBUG` retry
      surfaces the full traceback (was a bare one-liner). New regression:
      `tests/unit/test_manifest_writer_capture_status.py::test_merge_survives_pd_na_in_nullable_bool_column` exercises
      both `_merge_dataframes` and `lookup` with `pd.array([pd.NA], dtype="boolean")`. **Live verify (per the task Gate,
      all 4 truly-missing HL dates):** 2024-09-12 → 106 records + Shard completeness OK; 2024-09-28 → 112 records + OK;
      2024-12-31 → 128 records + OK; 2026-03-18 → 174 records + OK. Every run: no "failed on payload" warning;
      ManifestWriter wrote availability_index rows with `capture_status=captured` (default per `add()` path); EU seeding
      also landed pre-launch `empty_confirmed` rows for out-of-universe venues on each date. Full UTL quality-gates.sh
      green (385s), sentinel `b7925334c74a1a1682bc98ef34c6ec1187cd2c99`. Shipped:
      `unified-trading-library@b7925334c74a1a1682bc98ef34c6ec1187cd2c99` via `quickmerge --agent --files`.
- [x] ✅ [VERIFY] P2. Per-date confirm the 7 tradfi CME residual cells (2024-07-08 / 2024-11-26 / 2024-12-04 /
      2025-08-07 / 2025-08-18 / 2026-06-20 AF / 2026-06-24 EU) against the Databento CME trading-calendar. Cross-check
      whether each is a real market-closure day (holiday / session-end / no ohlcv-1m tick coverage) vs a fetch gap that
      needs a re-fetch. Post-`tradfi_v9_stage1_finish` completes, re-measure. (repo: instruments-service) — **Verified
      2026-07-06 via `exchange_calendars.get_calendar("CMES")` (XCMES, the same source
      `instruments_service/reference_data/adapters/tradfi/databento/sessions.py` consults via `_get_xcal`). 1
      REAL-CLOSURE + 6 FETCH-GAP split (evidence in issue-doc Verification results below).**
- [x] ✅ [DATA] P2. **STALE-AF cefi reconcile SUBSTANTIALLY DONE — verified 2026-07-07 slot-7 opus/max.** Verified
      against `gs://market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet`: 7 of the 8
      originally-flagged stale-AF cefi rows have already been collapsed by the deployed dedup fix (the §9.2b
      consolidator + writer NULL-vs-`''` semantic equivalence from `unified-trading-library@f5ec2291f`, verified in the
      understat plan's task 003 as taken-effect). Concretely: 0 remaining HL attempted_failed on 2023-12-01, 2023-12-13,
      2026-06-06 (was 3 rows); 1 remaining HL AF on 2025-01-18 (blank data_type + blank pipeline_mode +
      `error_reason=phantom_captured_no_parquet_at_canonical_path` — same aggregate-phantom-marker class as the tradfi
      CF-7 5,541 rows tracked in `plans/active/issues/tradfi_manifest_cf4_source_and_cf7_phantom_gaps_2026_07_07.md`); 0
      remaining batch AF venues on 2026-06-23 (was 4). The 1 remaining HL row rolls up as part of the cross-AG
      aggregate-phantom-marker cleanup todo in the tradfi CF-4/CF-7 issue doc (P1 CF-7 aggregate-phantom-marker deletion
      — expand the filter to also cover the cefi bucket); no separate cefi-only reconcile is needed. Coverage rollup no
      longer double-counts these cells. Verification-only, no code shipped. (repo: unified-trading-library — but no UTL
      code change needed on this task; the §9.2b fix already landed and the reconcile fell out naturally)

## Verification results — 7 CME residual cells (2026-07-06)

Cross-checked each of the 7 (venue=CME, date) cells against the Databento GLBX.MDP3 trading calendar
(`exchange_calendars.get_calendar("CMES")` v4.13.2 — the SAME XCMES source the IS Databento adapter consults via
`_get_xcal("CME") → _XCAL_MAPPING["CME"]="CMES"` in
`instruments_service/reference_data/adapters/tradfi/databento/sessions.py`). Session duration checked for early-close
anomaly (<20h) — none of the 7 dates fall on an early-close session; the adjacent Thanksgiving-2024 early-closes are Thu
2024-11-28 (19h) + Fri 2024-11-29 (19h), NEITHER of which is in the residual list.

| Cell (venue, date)  | Weekday   | XCMES session?  | Duration | Classification                                                           |
| ------------------- | --------- | --------------- | -------- | ------------------------------------------------------------------------ |
| CME, 2024-07-08     | Monday    | SESSION         | 24.0h    | **FETCH-GAP** — valid trading day; not a market-closure edge             |
| CME, 2024-11-26     | Tuesday   | SESSION         | 24.0h    | **FETCH-GAP** — valid trading day (Thanksgiving early-close is Thu/Fri)  |
| CME, 2024-12-04     | Wednesday | SESSION         | 24.0h    | **FETCH-GAP** — valid trading day                                        |
| CME, 2025-08-07     | Thursday  | SESSION         | 24.0h    | **FETCH-GAP** — valid trading day                                        |
| CME, 2025-08-18     | Monday    | SESSION         | 24.0h    | **FETCH-GAP** — valid trading day                                        |
| **CME, 2026-06-20** | **Sat.**  | **NON-SESSION** | **—**    | **REAL MARKET CLOSURE** — weekend; expected non-session (Sat=CME closed) |
| CME, 2026-06-24     | Wednesday | SESSION         | 24.0h    | **FETCH-GAP** — valid trading day                                        |

**Split: 1 REAL-CLOSURE (`2026-06-20`) + 6 FETCH-GAP (2024-07-08 / 2024-11-26 / 2024-12-04 / 2025-08-07 / 2025-08-18 /
2026-06-24).**

The initial framing (2024-11-26 near Thanksgiving; 2024-07-08 post-July-4-observed) is **not borne out** by the CMES
calendar — the immediate holiday-adjacent CME session anomalies (Nov 28 & 29 early-closes; July 4 close + July 3
early-close) are NOT in the residual list. So there is no market-calendar edge behind the 6 EU cells; they are ordinary
trading days awaiting the tradfi v9 apply-chain to reach them.

### Follow-up actions (unblocked)

1. **2026-06-20 AF misclassification** — the cell landed as `attempted_failed` on a Saturday.
   `is_non_trading_day("CME", 2026-06-20)` returns True per the CMES calendar (weekend), so the writer / pre-flight
   should have marked it `expected_unattempted`. This is a small mislabel and does NOT invalidate any downstream count —
   the manifest dedup-fix item already tracked (`pipeline_mode_source_batch_live_replay_standardisation_2026_06_05` P2)
   sweeps stale-AF vs new EU/captured collisions. No new issue-doc needed; the reconcile in item 3 of this doc absorbs
   it.

2. **6 FETCH-GAP re-measure after tradfi v9 completes** — per this issue-doc's summary,
   `tradfi_v9_stage1_finish_2026_07_06` is DONE for 2020–2025 + 2026 as of 2026-07-06 15:14 UTC. The 6 cells should
   convert to `captured` once the manifest rebuild + tradfi_v9 downstream reads land. Re-measure via the
   `data-freshness` skill (READ the availability manifest, NEVER a whole-corpus walk) after v9 downstream chain closes —
   that step is already tracked in `tradfi_v9_stage1_finish_2026_07_06.md` (manifest rebuild + IS could-exist seed) and
   does not need a new todo here.

### B0 acceptance

Classification stands: 7 cells = 1 REAL-CLOSURE (accept as EU semantics; small AF-label rewrite folded into item 3) + 6
FETCH-GAPs pending tradfi v9 downstream (accept as EU semantics; will re-classify at re-measure). B0 gate flip remains
valid — no correctness blocker uncovered by this verification.

## Progress log

- **2026-07-10** — **Status-flip note**: all 3 todos confirmed `[x]` with cited evidence (UTL pd.NA fix live-verified
  against all 4 truly-missing HL dates; tradfi CME residual cross-checked against the XCMES calendar; cefi stale-AF
  reconcile verified 7/8 already collapsed + the 1 remaining row rolled into the tradfi CF-4/CF-7 cross-AG cleanup).
  Flipped `status: open` → `resolved`.
- **2026-07-07** — **Item 3 RE-DISPATCHED 18TH TIME — PREREQ STILL NOT MET** (`BLK-b9131a80`, slot-13 planning /
  data_engineering worker). Identical pattern to the 17 prior PARKs on 2026-07-06/07. Verified at PM tip `db66ae462` —
  line 638 of `pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md` is still `- [ ] [CODE] P2` (dedup
  fix has NOT landed on LDR); latest UTL commit touching `_merge_dataframes` remains `f5ec2291` (partial NULL==empty
  normalization + no-venue asset_group stamp, NOT the v6–v9 shard-atom dedup this reconcile depends on). Newest
  `manifest_writer/` commits (`b7925334` slot-9's pd.NA-in-nullable-Boolean guard, `16513404`/`6c090bb9` write-side
  dtype coercion, `39eccc9c` memory-safe slim reads) are all UNRELATED to the shard-atom dedup key. Task body forbids
  the only action outside the prereq (`"NOT a naive add"` / `"Do NOT hand-edit the dedup machine"`). `/blocked` with
  `can_continue: false` awaiting `/skip-current-task`. **Systemic ask (18× cumulative, ~180 min of slot boot windows
  consumed across two days on the identical finding)**: operator to either (a) set `priority: 999` + add a `conditions:`
  gate keyed on the LDR-landing of the dedup fix in `backlog.yaml`, OR (b) escalate the AO backlog schema NL-prereq
  parsing to an epic.
- **2026-07-07** — **Item 3 RE-DISPATCHED 17TH TIME — PREREQ STILL NOT MET** (`BLK-7690f906`, slot-12 planning).
  Identical pattern to the 16 prior PARKs (10 on 2026-07-06 + 6 earlier today: `BLK-42bb5889` slot-10, `BLK-e2ff1535`
  slot-10, `BLK-e959c3a7` slot-9, `BLK-dfce4f07` slot-5, `BLK-d02f687e` slot-4, plus slot-12 earlier today). Verified at
  PM tip `60006b47e` — line 638 of `pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md` is still
  `- [ ] [CODE] P2` (the dedup fix has NOT landed on LDR; the current plan explicitly says "NOT a naive add"). Verified
  in UTL LDR clone: latest commit touching `_merge_dataframes` remains `f5ec2291` (partial NULL==empty normalization +
  no-venue asset_group stamp, NOT the v6–v9 shard-atom dedup this reconcile depends on); the newest `manifest_writer/`
  commits are `b7925334` (slot-9's Item 1 P1 pd.NA-in-nullable-Boolean guard — unrelated to the shard-atom dedup key),
  `16513404`/`6c090bb9` (write-side dtype coercion — unrelated), and `39eccc9c` (memory-safe slim reads — unrelated).
  Task body forbids the only action outside the prereq (`"NOT a naive add"` / `"Do NOT hand-edit the dedup machine"`).
  `/blocked` with `can_continue: false` awaiting `/skip-current-task`. **Systemic ask (17× cumulative, ~170 min of
  slot-planning boot windows consumed across two days on the identical finding)**: operator to either (a) set
  `priority: 999` + add a `conditions:` gate keyed on the LDR-landing of the dedup fix in `backlog.yaml`, OR (b)
  escalate the AO backlog schema NL-prereq parsing to an epic. Every re-dispatch is a pure waste of a slot boot window
  on an item whose task body already says "NOT a naive add" and whose prereq is trivially checkable against LDR.
- **2026-07-07** — **Item 3 RE-DISPATCHED 16TH TIME — PREREQ STILL NOT MET** (`BLK-d02f687e`, slot-4 planning).
  Identical pattern to the 15 prior PARKs (10 on 2026-07-06 + 5 earlier today: `BLK-42bb5889` slot-10, `BLK-e2ff1535`
  slot-10, `BLK-e959c3a7` slot-9, plus slot-12/slot-6/slot-11 and `BLK-dfce4f07` slot-5). Verified at PM tip `60006b47e`
  — line 638 of `pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md` is still `- [ ] [CODE] P2` (the
  dedup fix has NOT landed on LDR; the most-recent PM commit is literally logging the 15TH PARK of the same item).
  Verified in UTL LDR clone: latest commit touching `_merge_dataframes` remains `f5ec2291` (partial NULL==empty
  normalization + no-venue asset_group stamp, NOT the v6–v9 shard-atom dedup this reconcile depends on); the newest
  `manifest_writer/` commits are `b7925334` (slot-9's pd.NA-in-nullable-Boolean guard from Item 1 P1 — unrelated to the
  shard-atom dedup key), `16513404`/`6c090bb9` (write-side dtype coercion — also unrelated), and `39eccc9c` (memory-safe
  slim reads — unrelated). Task body forbids the only action outside the prereq (`"NOT a naive add"` /
  `"Do NOT hand-edit the dedup machine"`); regression
  `test_manifest_writer_capture_status::test_failed_then_captured_last_write_wins` documents the naive add was reverted
  2026-06-16. `/blocked` with `can_continue: false` awaiting `/skip-current-task`. Slot-4 planning also already PARKed
  this same item once today via `BLK-0316d90e` — the same slot re-encountered it, which underscores the
  dispatcher-visibility gap. **Systemic ask (16× cumulative, ~160 min of slot-planning boot windows consumed across two
  days on the identical finding)**: operator to either (a) set `priority: 999` + add a `conditions:` gate keyed on the
  LDR-landing of the dedup fix in `backlog.yaml`, OR (b) escalate the AO backlog schema NL-prereq parsing to an epic.
  Every re-dispatch is a pure waste of a slot boot window on an item whose task body already says "NOT a naive add" and
  whose prereq is trivially checkable against LDR.
- **2026-07-07** — **Item 3 RE-DISPATCHED 15TH TIME — PREREQ STILL NOT MET** (`BLK-dfce4f07`, slot-5 planning).
  Identical pattern to the 14 prior PARKs (10 on 2026-07-06 + 4 earlier today: `BLK-42bb5889` slot-10, `BLK-e2ff1535`
  slot-10, `BLK-e959c3a7` slot-9, plus slot-12/slot-6/slot-11/etc. earlier today). Verified at PM tip `c8f9e5c13` — line
  638 of `pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md` is still `- [ ] [CODE] P2` (dedup fix
  has NOT landed on LDR). Verified in UTL LDR clone: latest commit touching `_merge_dataframes` remains `f5ec2291`
  (partial NULL==empty normalization + no-venue asset_group stamp, NOT the v6–v9 shard-atom dedup this reconcile depends
  on); the newest `manifest_writer/` commit `b7925334` is slot-9's pd.NA-in-nullable-Boolean guard from earlier today
  (Item 1 P1 fix — unrelated to the shard-atom dedup key surface). Task body forbids the only action outside the prereq
  (`"NOT a naive add"` / `"Do NOT hand-edit the dedup machine"`). `/blocked` with `can_continue: false` awaiting
  `/skip-current-task`. **Systemic ask (15× cumulative, ~150 min of slot-planning boot windows consumed across two days
  on the identical finding)**: operator to either (a) set `priority: 999` + add a `conditions:` gate keyed on the
  LDR-landing of the dedup fix in `backlog.yaml`, OR (b) escalate the AO backlog schema NL-prereq parsing to an epic.
  Every re-dispatch is a pure waste of a slot boot window on an item whose task body already says "NOT a naive add" and
  whose prereq is trivially checkable against LDR.
- **2026-07-07** — **Item 3 RE-DISPATCHED 14TH TIME — PREREQ STILL NOT MET** (`BLK-e2ff1535`, slot-10 planning). Same
  pattern as the 13 prior PARKs (10 on 2026-07-06 + 3 earlier today, incl. slot-10's own `BLK-42bb5889` from earlier
  today). Verified at PM tip `cbab2d1e6` — line 638 of
  `pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md` is still `- [ ] [CODE] P2` (dedup fix has NOT
  landed on LDR). Verified in UTL LDR clone: latest commit touching `_merge_dataframes` remains `f5ec2291` (partial
  NULL==empty normalization + no-venue asset_group stamp, NOT the v6–v9 shard-atom dedup this reconcile depends on); the
  newest `manifest_writer/` commit `b7925334` is a separate pd.NA-in-nullable-Boolean guard (unrelated to the shard-atom
  dedup key). Task body forbids the only action outside the prereq (`"NOT a naive add"` /
  `"Do NOT hand-edit the dedup machine"`). `/blocked` with `can_continue: false` awaiting `/skip-current-task`.
  **Systemic ask (14× cumulative, ~140 min of slot-planning boot windows consumed across two days on the identical
  finding)**: operator to either (a) set `priority: 999` + add a `conditions:` gate keyed on the LDR-landing of the
  dedup fix in `backlog.yaml`, OR (b) escalate the AO backlog schema NL-prereq parsing to an epic. Every re-dispatch is
  a pure waste of a slot boot window on an item whose task body already says "NOT a naive add" and whose prereq is
  trivially checkable against LDR.
- **2026-07-07** — **✅ Item 1 [CODE] P1 FIXED + SHIPPED — pd.NA HYPERLIQUID crash CLOSED**
  (`unified-trading-library@b7925334`, slot-9 planning). Root-caused, fixed, tested, and live-verified in a single
  session. Bug lived in UTL `manifest_writer/_writer_io.py` (`_b`, `_s`, `_coerce_bool` — three parallel sites) not IS:
  each guarded pd-NA via `isinstance(value, float) and pd.isna(value)`, which silently let `pd.NA` (nullable
  BooleanDtype) fall through to `bool(value)` → `TypeError`. Fixed by switching to `pd.isna(value)` unconditionally
  (float NaN + pd.NA + pd.NaT), via a local scalar-safe `_is_na` helper. Also `exc_info=exc` on the UTL adapter's
  per-payload failure log so the traceback surfaces on `--log-level DEBUG` retry (was a bare one-liner). New regression
  `test_merge_survives_pd_na_in_nullable_bool_column` covers both `_merge_dataframes` and `lookup`. Live verify — all 4
  truly-missing HL dates cleared cleanly: 2024-09-12 (106 rows) · 2024-09-28 (112) · 2024-12-31 (128) · 2026-03-18
  (174); every run "Batch complete: 1 results collected" + "Shard completeness OK" + EU seeding landing pre-launch
  `empty_confirmed`, no "failed on payload" warnings. UTL `quality-gates.sh` green (385s, sentinel
  `b7925334c74a1a1682bc98ef34c6ec1187cd2c99`). Downstream: the 4 KNOWN_HANDLER_BUG_PD_NA HL cells now flip from
  `attempted_failed` to `captured` on their next retry — the fix is the classifier's precondition. Task Gate satisfied
  (`capture_status=captured` in the manifest). Item 3 (stale-AF reconcile) remains PARKED on the same UTL
  `_merge_dataframes` dedup fix in `pipeline_mode_source_batch_live_replay_standardisation_2026_06_05` per the 13 prior
  BLK rulings; my fix here does NOT touch that dedup surface.
- **2026-07-07** — **Item 3 RE-DISPATCHED 14TH TIME — PREREQ STILL NOT MET** (`BLK-e959c3a7`, slot-9 planning). Same
  pattern as the 13 prior PARKs. Verified at PM tip — line 638 of
  `pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md` is still `- [ ] [CODE] P2`; latest UTL commit
  touching `_merge_dataframes` remains `f5ec2291` (partial NULL==empty normalization only, NOT the v6-v9 shard-atom
  dedup this reconcile depends on). My session shipped Item 1 (`unified-trading-library@b7925334`) but touched only
  `_b`/`_s`/`_coerce_bool` NA-guard — not the dedup key surface. `/blocked` + `/skip-current-task`. **Systemic ask (14×
  cumulative, ~140 min of slot-planning boot windows on the identical finding across two days)**: operator to either (a)
  `priority: 999` + `conditions:` gate keyed on the LDR-landing of the dedup fix in `backlog.yaml`, OR (b) NL-prereq
  parsing epic. Every re-dispatch is a pure waste of a slot boot window.
- **2026-07-07** — **Item 3 RE-DISPATCHED 13TH TIME — PREREQ STILL NOT MET** (slot-12 planning). Same pattern as the 12
  prior PARKs (10 on 2026-07-06 + 2 earlier today). Verified at PM tip `a332aa5c0` — line 638 of
  `pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md` is still `- [ ] [CODE] P2` (dedup fix has NOT
  landed on LDR). Verified in UTL LDR clone: latest commit touching `_merge_dataframes` remains `f5ec2291` (partial
  NULL==empty normalization + no-venue asset_group stamp, NOT the v6-v9 shard-atom dedup this reconcile depends on); no
  fresh `manifest_writer/_writer_io.py` commits addressing the dedup key in the last 24 h (most recent manifest_writer
  commit is `16513404` — bool/float write-side schema coercion, unrelated). Task body forbids the only action outside
  the prereq (`"NOT a naive add"` / `"Do NOT hand-edit the dedup machine"`). /blocked with `can_continue: false`
  awaiting /skip-current-task. **Systemic ask (13× cumulative, ~130 min of slot-planning boot windows consumed across
  two days on the identical finding)**: operator to either (a) set `priority: 999` + add a `conditions:` gate keyed on
  the LDR-landing of the dedup fix in `backlog.yaml`, OR (b) escalate the AO backlog schema NL-prereq parsing to an
  epic. Every re-dispatch is a pure waste of a slot boot window on an item whose task body already says "NOT a naive
  add" and whose prereq is trivially checkable against LDR.
- **2026-07-07** — **Item 3 RE-DISPATCHED 12TH TIME — PREREQ STILL NOT MET** (slot-6 planning). Same pattern as the 11
  prior PARKs (10 on 2026-07-06 + 1 earlier today `BLK-42bb5889` slot-10). Verified at PM tip `69d48bf7e` — line 638 of
  `pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md` is still `- [ ] [CODE] P2` (dedup fix has NOT
  landed on LDR). Verified in UTL LDR clone: latest commit touching `_merge_dataframes` remains `f5ec2291` (2026-07-06
  12:57 UTC — partial NULL==empty normalization + no-venue asset_group stamp, NOT the v6-v9 shard-atom dedup this
  reconcile depends on); no `manifest_writer/` commits in the last 4 h. Task body forbids the only action outside the
  prereq (`"NOT a naive add"` / `"Do NOT hand-edit the dedup machine"`). /blocked with `can_continue: false` awaiting
  /skip-current-task. **Systemic ask (12× cumulative, ~120 min of slot-planning boot windows consumed across two days on
  the identical finding)**: operator to either (a) set `priority: 999` + add a `conditions:` gate keyed on the
  LDR-landing of the dedup fix in `backlog.yaml`, OR (b) escalate the AO backlog schema NL-prereq parsing to an epic.
- **2026-07-07** — **Item 3 RE-DISPATCHED 11TH TIME — PREREQ STILL NOT MET, NOW SPILLING INTO A SECOND DAY**
  (`BLK-42bb5889`, slot-10 planning). Identical pattern to the 10 prior PARKs from 2026-07-06 — the systemic ask (either
  `priority: 999` + a `conditions:` gate on the dedup-fix LDR-landing, OR NL-prereq parsing in the AO backlog schema)
  has NOT been actioned, so this task auto-re-dispatched on the new day. Verified at PM tip `e29810623` — line 638 of
  `pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md` is still `- [ ] [CODE] P2` (dedup fix has not
  landed). Verified in UTL LDR clone: latest commit touching `_merge_dataframes` remains `f5ec2291` (2026-06-16 partial
  NULL==empty normalization, NOT the v6-v9 shard-atom dedup this reconcile depends on) — no fresh activity in
  `unified_trading_library/manifest_writer` in the last 6 h. Task body forbids the only action available outside the
  prereq (`"NOT a naive add"` / `"Do NOT hand-edit the dedup machine"`). `/blocked` with `can_continue: false` awaiting
  `/skip-current-task`. **Systemic ask (cumulative 11×, ~110 min of slot-planning boot windows consumed on the identical
  finding, now across two days)**: operator to either (a) set `priority: 999` + add a `conditions:` gate keyed on the
  LDR-landing of the dedup fix in `backlog.yaml`, OR (b) escalate the AO backlog schema NL-prereq parsing to an epic.
  Every re-dispatch is a pure waste of a slot boot window on an item whose task body already says "NOT a naive add" and
  whose prereq is trivially checkable against LDR.
- **2026-07-06** — **Item 3 RE-DISPATCHED 10TH TIME — PREREQ STILL NOT MET** (`BLK-c77f7c92`, slot-8 planning).
  Identical pattern to the 9 prior PARKs today
  (BLK-b81e4231/2e75351f/f96a851f/b2595413/d5ac4b5b/3803f4fa/b7280ba5/0316d90e/3a65c6c0). Verified against PM tip
  `8a8c91ae8` — line 638 of `pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md` is still
  `- [ ] [CODE] P2` (dedup fix has not landed on LDR). Verified latest UTL commit touching `_merge_dataframes` is
  `f5ec2291` (partial NULL==empty normalization only, NOT the v6-v9 shard-atom dedup this reconcile depends on). Task
  body forbids the only action available outside the prereq (`"NOT a naive add"` /
  `"Do NOT hand-edit the dedup machine"`). /blocked with `can_continue: false` awaiting /skip-current-task. **Systemic
  ask (10× today, ~100 min of slot-planning boot windows consumed on the identical finding)**: operator to either (a)
  set `priority: 999` + add a `conditions:` gate keyed on the LDR-landing of the dedup fix in `backlog.yaml`, OR (b)
  escalate the AO backlog schema NL-prereq parsing to an epic. Every re-dispatch is a pure waste of a slot boot window
  on an item whose task body already says "NOT a naive add" and whose prereq is trivially checkable against LDR.
- **2026-07-06** — Issue filed. Root-caused HL InstrumentsHandler failure to a repeatable pd.NA-in-boolean bug via a
  DEBUG-log retry of 2024-09-12 (`is@LDR`). Classified the 12 non-ASTER cefi MVP AF cells into KNOWN_HANDLER_BUG_PD_NA
  (4) + RESOLVED_STALE_AF (8), plus the tradfi CME 7 as MARKET_CALENDAR_OR_DATABENTO_GAP-pending-verify. Unblocks
  `is_catalogue_completion_2d` B0 gate flip.
- **2026-07-06** — [VERIFY] P2 closed (slot 10). Cross-checked all 7 tradfi CME residual cells against the XCMES
  calendar (the SSOT source the IS Databento adapter uses via `_get_xcal`). Result: 1 real closure (2026-06-20 Sat =
  weekend) + 6 valid CMES sessions (fetch gaps awaiting tradfi v9 downstream). Written up in "Verification results"
  above. No new correctness finding requires a separate issue doc — the AF-on-Sat mislabel is absorbed by the existing
  P2 dedup-reconcile item 3.
- **2026-07-06** — **Item 3 RE-DISPATCHED 9TH TIME — PREREQ STILL NOT MET** (`BLK-3a65c6c0`, slot-6 planning). Same
  pattern as the 8 prior PARKs today. Verified line 638 of
  `pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md` is still `- [ ] [CODE] P2`. Latest UTL commit
  touching `_merge_dataframes` is `f5ec2291` (partial NULL==empty normalization only, NOT the v6-v9 shard-atom dedup
  this reconcile depends on). /blocked with `can_continue: false` awaiting /skip-current-task. Systemic ask escalated
  further — 9 slot-planning boot windows wasted today. Operator action to unblock: (a) `priority: 999` + `conditions:`
  gate keyed on LDR-landing of the dedup fix in `backlog.yaml`, OR (b) NL-prereq parsing in AO backlog schema.

- **2026-07-06** — **Item 3 RE-DISPATCHED 8TH TIME — PREREQ STILL NOT MET** (`BLK-0316d90e`, slot-4 planning). Same root
  cause as the seven prior PARKs today (`BLK-b81e4231` slot-9, `BLK-2e75351f` slot-3, `BLK-f96a851f` slot-5,
  `BLK-b2595413` slot-7, `BLK-d5ac4b5b` slot-10, `BLK-3803f4fa` slot-2, `BLK-b7280ba5` slot-11): dispatcher lacks
  natural-language prereq visibility so item 3 keeps auto-routing to slots by priority=50 despite the explicit "NOT a
  naive add" / "Do NOT hand-edit the dedup machine" clauses. Verified against PM tip `f515c2100` — line 638 of
  `pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md` is still `- [ ] [CODE] P2` (dedup fix has not
  landed on LDR). Also verified via `git log -S _merge_dataframes` in unified-trading-library: most recent touching
  commit is `f5ec2291 fix(manifest): dedup NULL == '' for unset optional dims` — a related but PARTIAL fix (from the
  2026-06-16 revert lineage), NOT the full v6–v9 shard-atom dedup this task's prereq requires;
  `git log --since='4 hours ago' -- unified_trading_library/manifest_writer` is EMPTY (no fresh commits). Recommendation
  to main = PARK (same as the seven prior rulings). Slot-4 idle-parks pending release via /skip-current-task. **Systemic
  ask (now 8×, ~80 min of worker context budget consumed today on the identical finding)**: operator to either (a) set
  `priority: 999` + add a `conditions:` gate keyed on the LDR-landing of the dedup fix in `backlog.yaml`, OR (b)
  escalate the AO backlog schema NL-prereq parsing to an epic. Every re-dispatch is a pure waste of a slot boot window
  on an item whose task body already says "NOT a naive add" and whose prereq is trivially checkable against LDR.
- **2026-07-06** — **Item 3 RE-DISPATCHED 7TH TIME — PREREQ STILL NOT MET** (`BLK-b7280ba5`, slot-11 planning). Same
  root cause as the six prior PARKs today (`BLK-b81e4231` slot-9, `BLK-2e75351f` slot-3, `BLK-f96a851f` slot-5,
  `BLK-b2595413` slot-7, `BLK-d5ac4b5b` slot-10, `BLK-3803f4fa` slot-2): dispatcher lacks natural-language prereq
  visibility so item 3 keeps auto-routing to slots by priority=50 despite the explicit "NOT a naive add" / "Do NOT
  hand-edit the dedup machine" clauses. Verified against PM tip `60cf17af0` — line 638 of
  `pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md` is still `- [ ] [CODE] P2` (dedup fix has not
  landed on LDR). Recommendation to main = PARK (same as the six prior rulings). Slot-11 idle-parks pending release via
  /skip-current-task. **Systemic ask (now SEVERE — 7× today; single item has consumed 7 slot-planning boot windows)**:
  operator to either (a) set `priority: 999` + add a `conditions:` gate keyed on the LDR-landing of the dedup fix in
  `backlog.yaml`, OR (b) escalate the AO backlog schema NL-prereq parsing to an epic. Every additional re-dispatch is a
  pure waste of a slot boot window on an item whose task body already says "NOT a naive add" and whose prereq is
  trivially checkable against LDR.
- **2026-07-06** — **Item 3 RE-DISPATCHED 6TH TIME — PREREQ STILL NOT MET** (`BLK-3803f4fa`, slot-2 planning). Same root
  cause as the five prior PARKs today (`BLK-b81e4231` slot-9, `BLK-2e75351f` slot-3, `BLK-f96a851f` slot-5,
  `BLK-b2595413` slot-7, `BLK-d5ac4b5b` slot-10): dispatcher lacks natural-language prereq visibility so item 3 keeps
  auto-routing to slots by priority=50 despite the explicit "NOT a naive add" / "Do NOT hand-edit the dedup machine"
  clauses. Verified against PM tip 1f278500c — line 638 of
  `pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md` is still `- [ ] [CODE] P2` (dedup fix has not
  landed on LDR). Recommendation to main = PARK (same as the five prior rulings). Slot-2 idle-parks pending release via
  /skip-current-task. Systemic ask (now CRITICAL — 6× today): operator to either set `priority: 999` + add a
  `conditions:` gate on this issue-doc item in `backlog.yaml`, OR the AO backlog schema needs NL-prereq parsing
  (epic-level). SIX slot-planning boot windows wasted on this item today.
- **2026-07-06** — **Item 3 RE-DISPATCHED 5TH TIME — PREREQ STILL NOT MET** (`BLK-d5ac4b5b`, slot-10 planning). Same
  root cause as the four prior PARKs today (`BLK-b81e4231` slot-9, `BLK-2e75351f` slot-3, `BLK-f96a851f` slot-5,
  `BLK-b2595413` slot-7): dispatcher lacks natural-language prereq visibility so item 3 keeps auto-routing to slots by
  priority=50 despite the explicit "NOT a naive add" / "Do NOT hand-edit the dedup machine" clauses. Verified against PM
  tip 16cac6cf — line 638 of `pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md` is still
  `- [ ] [CODE] P2` (dedup fix has not landed on LDR). Recommendation to main = PARK (same as the four prior rulings).
  Slot-10 idle-parks pending release via /skip-current-task. Systemic ask (now critical — 5× today): operator to either
  set `priority: 999` + add a `conditions:` gate on this issue-doc item in `backlog.yaml`, OR the AO backlog schema
  needs NL-prereq parsing (epic-level). FIVE slot-planning boot windows wasted on this item today.
- **2026-07-06** — **Item 3 RE-DISPATCHED 4TH TIME — PREREQ STILL NOT MET** (`BLK-b2595413`, slot-7 planning). Same root
  cause as the three prior PARKs today (`BLK-b81e4231` slot-9, `BLK-2e75351f` slot-3, `BLK-f96a851f` slot-5): dispatcher
  lacks natural-language prereq visibility so item 3 keeps auto-routing to slots by priority=50 despite the explicit
  "NOT a naive add" / "Do NOT hand-edit the dedup machine" clauses. Verified against PM tip 8b2ae89ff — line 638 of
  `pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md` is still `- [ ] [CODE] P2` (dedup fix has not
  landed on LDR). Recommendation to main = PARK (same as the three prior rulings). Slot-7 idle-parks pending release via
  /skip-current-task. Systemic ask (now urgent — 4× today): operator to either set `priority: 999` + add a `conditions:`
  gate on this issue-doc item in `backlog.yaml`, OR the AO backlog schema needs NL-prereq parsing (epic-level). FOUR
  slot-planning boot windows wasted on this item today.
- **2026-07-06** — **Item 3 RE-DISPATCHED 3RD TIME — PREREQ STILL NOT MET** (`BLK-f96a851f`, slot-5 planning). Same root
  cause as `BLK-b81e4231` (slot-9) and `BLK-2e75351f` (slot-3) earlier today: dispatcher lacks natural-language prereq
  visibility so item 3 keeps auto-routing to slots by priority=50 despite the explicit "NOT a naive add" / "Do NOT
  hand-edit the dedup machine" clauses. Verified line 638 of
  `pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md` is still `- [ ] [CODE] P2` (dedup fix has not
  landed on LDR). Recommendation to main = PARK (same as the two prior rulings). Slot-5 idle-parks pending release via
  /skip-current-task. Systemic ask (unchanged): operator to either set `priority: 999` + add a `conditions:` gate on
  this issue-doc item in `backlog.yaml`, OR the AO backlog schema needs NL-prereq parsing (epic-level). THREE
  slot-planning boot windows wasted on this item today.
- **2026-07-06** — **Item 3 RE-DISPATCHED 2ND TIME — PREREQ STILL NOT MET** (`BLK-2e75351f`, slot-3 planning). Same root
  cause as `BLK-b81e4231` (slot-9 earlier today): dispatcher lacks natural-language prereq visibility so item 3 keeps
  auto-routing to slots by priority=50 despite the explicit "NOT a naive add" / "Do NOT hand-edit the dedup machine"
  clauses. Verified line 638 of `pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md` is still
  `- [ ] [CODE] P2` (dedup fix has not landed). Recommendation to main = PARK (same as the prior ruling). Slot-3
  idle-parked. Systemic ask: operator to either set `priority: 999` + add a `conditions:` gate on this issue-doc item in
  `backlog.yaml`, OR the AO backlog schema needs NL-prereq parsing (epic-level). Two slot-planning boot windows wasted
  on this item today.
- **2026-07-06** — **Item 3 PARKED — PENDING-DEDUP-FIX** (`BLK-b81e4231`, slot-9 planning). Task -003 was dispatched by
  priority=50; verified the natural-language prereq is not met — the `_merge_dataframes` dedup fix in
  `pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md` is still `- [ ] [CODE] P2.` on LDR tip (a prior
  2026-06-16 naive re-add was reverted; that plan explicitly says "NOT a naive add"). Task body forbids hand-editing the
  dedup machine ("Do NOT hand-edit the dedup machine (per `instruments_mtds_subset` P2 finding)"). Main-agent answer
  (`BLK-b81e4231`): **PARK — do NOT run the reconcile now.** Slot-9 to idle-park pending release via /skip-current-task.
  Item 3 stays queued until the `_merge_dataframes` dedup fix reaches LDR.
