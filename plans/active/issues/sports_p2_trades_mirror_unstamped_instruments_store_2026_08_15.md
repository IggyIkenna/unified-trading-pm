---
doc_type: issue
title: Sports IS-bucket cross-bucket `trades` mirror rows never re-stamped to `odds`
summary: >-
  Live census 2026-08-15 (sports_taxonomy_p2_migration_2026_08_08.md's "assert the vocabulary has collapsed to TWO
  types" REVIEW todo): the `trades`→`odds` re-stamp shipped earlier in that plan only touched the
  `market-data-tick-sports-prd` manifest. The SSOT reference manifest (`instruments-store-sports-prd`) still carries
  `data_type=trades`/`TRADES` cross-bucket-mirror rows (Axis-10b pattern,
  `instruments-service/scripts/reconcile_phantom_manifest_rows_all.py::_SPORTS_CROSS_BUCKET_DATA_TYPES`) that were never
  relabeled, so a live query against that surface still shows a third odds-family type.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [instruments-service, market-tick-data-service]
scope: [engineer]
tags: [sports, migration, canonicalisation, manifest, cross-bucket, trades, odds]
related:
  [
    /plans/active/sports_taxonomy_p2_migration_2026_08_08.md,
    /codex/02-data/four-surface-reconciliation-procedure.md,
    /plans/active/sports_odds_writer_flip_and_trades_path_retirement_2026_08_15.md,
  ]
created: "2026-08-15"
last_updated: 2026-08-17
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
source: ["sports_taxonomy_p2_migration_2026_08_08.md REVIEW todo, live census 2026-08-15 (slot-20)"]
resolved_by:
locked_by:
locked_since:
drift_direction: advance-code
depends_on: []
context_scope: [/plans/active/sports_taxonomy_p2_migration_2026_08_08.md, /plans/active/sports_odds_writer_flip_and_trades_path_retirement_2026_08_15.md, /codex/02-data/four-surface-reconciliation-procedure.md, instruments-service/scripts/restamp_sports_is_bucket_trades_mirror_to_odds_2026_08_15.py, instruments-service/scripts/reconcile_phantom_manifest_rows_all.py]
---

# Sports IS-bucket `trades` mirror rows never re-stamped

## What I found

Live census (2026-08-15, `unified_trading_library.read_availability_index`) against the two sports manifest buckets,
restricted to odds-family `data_type` values:

- `market-data-tick-sports-prd-central-element-323112` (raw+derived, batch+live — the P0 re-stamp's actual target):
  captured rows are `odds_horizon_bucket`=5,419,978, `odds`=542,879, `arbitrage_opportunity`=17,851 (untouched, as
  required), plus the already-tracked `odds_snapshot`/`odds_movement` phantoms (separate BLOCKED-OPERATOR-DECISION todo)
  and a small `trades`=1,600 residue. This surface is effectively collapsed to the intended two types modulo the
  already-tracked items.
- `instruments-store-sports-prd-central-element-323112` (the SSOT reference/routing manifest — sports routes every
  data_type through this one manifest per Axis-10b, even though `trades`/`odds_horizon_bucket` bytes physically live in
  the tick bucket): still carries `trades`=43,726 captured (122,286 all-status) + `TRADES`=32 captured (2,216
  all-status) rows. None of this plan's re-stamp todos (the P0 `trades`→`odds` todo, the 19-token lowercase todo —
  `TRADES`/`trades` was never one of the 19 tokens) actually touched this manifest's cross-bucket mirror rows.

## Why it matters

The plan's own REVIEW todo ("assert the vocabulary has collapsed to TWO types … anything outside these is incomplete")
fails on this surface: a consumer reading the IS-bucket manifest directly (the documented SSOT for sports data-type
membership) still sees a live third type, `trades`, at non-trivial volume.

## Recommended decision

Extend the existing `trades`→`odds` re-stamp tooling
(`market-tick-data-service/scripts/sports/restamp_sports_trades_to_odds_2026_08_12.py` /
`manifest_swap_trades_to_odds_2026_08_12.py`) to also relabel the IS-bucket's cross-bucket mirror rows (or confirm via a
fresh live probe whether the manifest consolidator's cross-bucket sync already carries these on its next cycle, before
assuming a code fix is needed).

## Progress Log

**2026-08-15 (slot-29) — live census + decision.** Ran a fresh, memory-bounded census against
`instruments-store-sports-prd-central-element-323112`'s canonical `_index/availability_index.parquet`
(`instruments-service/scripts/census_sports_is_bucket_trades_mirror_2026_08_15.py`, column-projected direct
`pd.read_parquet` — the naive `merge_canonical_with_outstanding_shards(columns=...)` path measured >8GB RSS on this
bucket even slim-columned, so this script bypasses it; a read-only census does not need the outstanding-per-VM-shard
merge that helper exists for). Findings corroborate + refresh this doc's original "What I found" counts (same
124,502-row all-status total: `trades`=122,286, `TRADES`=2,216):

- By `capture_status`: `captured`=43,758 (1,547,287 total row_count) / `attempted_failed`=33,629 /
  `empty_confirmed`=47,115.
- By `venue`: dominated by bookmaker venues under `pipeline_mode=batch_odds_api` (WILLIAMHILL, MATCHBOOK, BETONLINEAG,
  UNIBET, PINNACLE, …) — the same population the tick-bucket P0 re-stamp already relabeled on the OTHER surface.
- `date` range 2018-01-01 → 2026-08-15 (today); `written_at` range 2026-05-05 → **2026-08-15 06:37:30 UTC (today)**,
  with **19,992 rows written_at within the last 7 days**.

**Verdict: LIVE PRODUCER, not a stale historical mirror.** The sports odds_api writer is still actively stamping
`data_type=trades`/`TRADES` on new captures into this surface as of today. This matches the KNOWN PHASED-STATE CAVEAT
`manifest_swap_trades_to_odds_2026_08_12.py` already documented for the sibling tick-bucket surface: writers keep
emitting the old token until the writer itself is flipped. **Correction (2026-08-15, later same day)**:
`sports_taxonomy_p3_consumers_2026_08_08` does NOT actually own the writer-side fix — confirmed via a full read, its
todos are panel/ML/arb/catalogue/Betfair consumer wiring only, no `venue_fetch.py`/`_build_sports_shard_path()` todo
anywhere in it. The writer-side fix is tracked in the new
`/plans/active/sports_odds_writer_flip_and_trades_path_retirement_2026_08_15.md` instead — that plan is the tracked
scope, not duplicated here. Consequently a one-time metadata relabel is not durable by itself (new `trades` rows will
keep appearing until P3 lands), but it is still the correct immediate action — same posture already accepted for the
tick-bucket sibling script — so the relabel was drafted + locally validated (synthetic in-memory frame, no GCS calls)
this session: `instruments-service/scripts/restamp_sports_is_bucket_trades_mirror_to_odds_2026_08_15.py`. Execution
against prod needs a dedicated VM launch (15.7M-row manifest, matches the already-executed 19-token casing-restamp's own
VM-launch requirement on this exact bucket) — split to the new `[OPERATOR]` todo below rather than run inline on the
shared host, per the memory-bounding + heavy-I/O HARD RULES.

- [x] ✅ [DATA] P2. Census the `instruments-store-sports-prd` manifest's `trades`/`TRADES` rows' `capture_status`/
      `venue`/`date` distribution, confirm whether they are stale historical mirrors of already-migrated tick-bucket
      shards (safe metadata-only relabel) or reflect a live producer still writing the old label into this surface, then
      re-stamp or fix the writer accordingly. §3a does not apply (no object delete, manifest-only). Re-run this doc's
      census after the fix; 0 remaining `trades`/`TRADES` rows on this surface closes the parent plan's "assert the
      vocabulary has collapsed to TWO types" REVIEW todo. (repo: instruments-service or market-tick-data-service,
      whichever owns the write path found) — **CENSUS + DECISION DONE 2026-08-15 (slot-29),
      instruments-service@97c98a986b: LIVE PRODUCER confirmed (see Progress Log), relabel drafted + locally validated.
      Execution split to the new `[OPERATOR]` todo below** (mirrors this plan's own 2026-08-14 precedent of checking off
      a draft-only todo separately from its execute-todo) — the "0 remaining" re-verify is that new todo's own
      done-condition, not this one's.
- [ ] [OPERATOR] P2. **Execute the drafted manifest relabel against prod, via a dedicated VM launch** (this manifest is
      15.7M rows — too large for an inline interactive CAS write per the memory-bounding + heavy-I/O HARD RULES,
      `unified-trading-pm/agents/RULES.md` §1; the already-executed 19-token casing restamp on this exact bucket
      required its own VM-launcher category, `sports_taxonomy_p2_migration_2026_08_08.md` Progress Log 2026-08-14, for
      the same reason). Script:
      `instruments-service/scripts/restamp_sports_is_bucket_trades_mirror_to_odds_2026_08_15.py` (drafted + locally
      validated against a synthetic in-memory frame this session — NOT yet run against prod). Manifest-only relabel
      (merged `_index/availability_index.parquet` + every non-empty `_index/per_vm/*.parquet` shard), no GCS object
      touched, §3a n/a. Reuse (or extend) the `sports-19token-restamp` VM-launcher category. After apply: re-run
      `census_sports_is_bucket_trades_mirror_2026_08_15.py`; 0 remaining `trades`/`TRADES` closes the todo above.
      **KNOWN PHASED-STATE CAVEAT**: the live odds_api writer keeps stamping `data_type=trades` on new captures until
      the writer itself is flipped — tracked in
      `/plans/active/sports_odds_writer_flip_and_trades_path_retirement_2026_08_15.md` (NOT
      `sports_taxonomy_p3_consumers_2026_08_08`, corrected above) — a re-run after that plan's Phase 0 lands may be
      needed if fresh `trades` rows reappear (same caveat already accepted for the sibling tick-bucket restamp,
      `manifest_swap_trades_to_odds_2026_08_12.py`).
- [ ] [DATA] P3. **Update UAC's stale `data_type="trades"` canonical declaration for sports odds.**
      `unified-api-contracts/unified_api_contracts/registry/market_data_categories.py:1565-1591`'s
      `VALID_DATA_TYPES_BY_AG_AND_INSTRUMENT_TYPE[("sports","odds")]` still declares `data_type="trades"` as the
      CONFIRMED canonical value (with a comment describing a 2026-07-27 reversion that restored lowercase `"trades"` as
      "the sole canonical form again"), directly contradicting the 2026-08-08 operator ruling +
      2026-08-12/13/14/15-executed `trades`->`odds` restamp migration
      (`/plans/active/sports_taxonomy_p2_migration_2026_08_08.md`). Confirmed (2026-08-15 session,
      `sports_p2_raw_tick_live_writer_still_emits_trades_2026_08_15.md`) this table is NOT consulted anywhere in the
      live write/sentinel path (0 references in
      `market-tick-data-service/market_tick_data_service/engine/orchestrator/`), so it does not affect write-path
      correctness today, but it is a stale doc/registry entry that will mislead the next reader who trusts it as the
      canonical source. (repo: unified-api-contracts)
- **context-scout 2026-08-17**: populated/refreshed context_scope (5 entries).
