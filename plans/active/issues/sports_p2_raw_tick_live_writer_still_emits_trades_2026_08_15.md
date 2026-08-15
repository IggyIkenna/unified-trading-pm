---
doc_type: issue
title: Sports raw-tick live writer hardcodes `data_type=trades` — actively regenerating the retired type post-restamp
summary: >-
  Four-surface reconciliation (sports_taxonomy_p2_migration_2026_08_08.md's "Four-surface reconciliation after the
  migration" REVIEW todo) found the raw-tick `market-data-tick-sports-prd` manifest's residual `trades` population is
  NOT static pre-migration residue as the plan assumed — it grew from 1,600 rows (measured 2026-08-15 slot-20, same day)
  to 3,229 rows within hours, 3,209 of them (99.4%) `attempted_at >= 2026-08-14`, max `attempted_at` literally minutes
  before this census (2026-08-15T08:26:41Z). Root cause READ, not grepped: `_build_sports_shard_path()` in
  `market-tick-data-service/market_tick_data_service/engine/orchestrator/venue_fetch.py:889,898` hardcodes the literal
  path segment `data_type=trades/` on every sports shard write — the `trades`->`odds` re-stamp migration relabeled the
  historical corpus but never touched this live write path, so it keeps writing new `trades`-labeled objects (+
  presumably matching manifest rows via the `shard_counts[(bm_str, "trades", league_str, "odds", fixture_str)]`
  accumulator at the same lines) every day the writer stays unfixed.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [sports, migration, canonicalisation, manifest, live-writer, regression, data-correctness, trades, odds]
related:
  [
    /plans/active/sports_taxonomy_p2_migration_2026_08_08.md,
    /plans/active/issues/sports_p2_trades_mirror_unstamped_instruments_store_2026_08_15.md,
    /codex/02-data/four-surface-reconciliation-procedure.md,
  ]
created: "2026-08-15"
last_updated: 2026-08-15
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
source:
  [
    "sports_taxonomy_p2_migration_2026_08_08.md 'Four-surface reconciliation' REVIEW todo, live census 2026-08-15
    (slot-9)",
  ]
resolved_by:
locked_by:
locked_since:
drift_direction: advance-code
depends_on: []
---

# Sports raw-tick live writer still emits `data_type=trades`

## What I found

Four-surface reconciliation (S3 manifest census, `read_availability_index_safe` against
`market-data-tick-sports-prd-central-element-323112`, columns+filters pushdown, no walk):

- `data_type=trades` rows: **3,229** (3,199 `captured`, 30 `empty_confirmed`).
- `attempted_at` range: 2026-08-10T23:59:01Z → **2026-08-15T08:26:41Z** — the max is inside the hour this reconciliation
  ran.
- 3,209 of 3,229 rows (99.4%) carry `attempted_at >= 2026-08-14` — i.e. the population is dominated by FRESH writes
  landing after the P0 `trades`->`odds` restamp (which completed 2026-08-12/13 per this plan's own todo), not
  pre-migration residue.
- This directly contradicts a same-plan sibling finding from earlier today (slot-20,
  `sports_p2_trades_mirror_unstamped_instruments_store_2026_08_15.md`), which measured this exact bucket's `trades`
  count at 1,600 and characterized it as "effectively collapsed... modulo the already-tracked items" — the population
  grew ~2x in the few hours between that census and this one.

**Root cause (READ, not grepped)** —
`market-tick-data-service/market_tick_data_service/engine/orchestrator/venue_fetch.py`:

- `_build_sports_shard_path()` (lines 871-899) hardcodes the literal path segment `data_type=trades/` in BOTH its
  fixture-scoped and league-scoped return branches (lines 889, 898) — there is no reference to `odds` anywhere in the
  function.
- The caller (around line 780) is a genuinely live write path: it groups fetched sports records by
  `(bookmaker_key, league_id, fixture_id)`, builds the GCS path via the function above, and writes real bytes via
  `_orch.StreamingParquetWriter(...).write_chunk(shard_df)` — not dead/unreachable code.
- The same caller also stamps `shard_counts[(bm_str, "trades", league_str, "odds", fixture_str)]` (lines 796-797) with
  the literal `"trades"` as the data_type component of the accumulator key used to drive the eventual manifest
  `record_captured` call — the manifest row's `data_type` almost certainly inherits this same literal (not traced to the
  exact `record_captured` call site in this session; the GCS path evidence alone is sufficient root-cause proof that new
  writes land under the retired shape).

## Why it matters

This is an ACTIVE regression on a P0 data-migration plan, not incomplete-but-stable residue: every day the writer stays
unfixed, more `trades`-labeled objects + manifest rows land on top of a migration that was supposed to have retired that
type. The plan's "vocabulary has collapsed to TWO types" REVIEW todo (line ~623 of the parent plan) will never close
while this writer is live, and re-running the restamp/purge tooling against historical data is pure churn if the live
writer keeps repopulating the same population behind it.

## Recommended decision

Fix `_build_sports_shard_path()` to emit `data_type=odds/` (matching the post-restamp canonical form), verify the
`shard_counts` accumulator + its downstream `record_captured`/manifest-write call also stamp `odds`, ship, then re-run
this census to confirm the `trades` count stops growing (a fixed writer should show 0 new `attempted_at` rows post-fix;
the pre-fix 3,229 rows still need the same `trades`->`odds` re-stamp tooling this plan already built
(`market-tick-data-service/scripts/sports/restamp_sports_trades_to_odds_2026_08_12.py` /
`manifest_swap_trades_to_odds_2026_08_12.py`) run again over the fresh window). [OPERATOR] not required for the code fix
itself (no delete, no VM launch); the follow-up re-stamp of the ~3.2K rows is small enough to fold into the fix todo
rather than a dedicated VM launch, per proportionality.

## Todos

- [x] ✅ [DATA] P0. Fix `_build_sports_shard_path()`
      (`market-tick-data-service/market_tick_data_service/engine/orchestrator/venue_fetch.py:871-899`) to emit
      `data_type=odds` instead of the hardcoded `data_type=trades` literal in both branches; trace the
      `shard_counts[(bm_str, "trades", ...)]` accumulator (lines 796-797) through to its `record_captured` call site and
      confirm/fix the manifest `data_type` value it stamps matches. Ship + QG green. —
      `market-tick-data-service@28e2eb36d8` (`origin/live-defi-rollout`, post-push ancestry verified). Blast radius was
      larger than this todo's own text: the `shard_counts` tuple's `data_type` slot doubled as the
      is-this-a-sports-shard DETECTOR in 8 other coupled call sites (`manifest_finalize.py`'s
      `_write_shard_counts_to_manifest`, `sentinels.py`'s `_build_captured_shard_sets` + Tier-2/v1 sentinel emitters),
      plus a separate live-mode twin (`live/_sports_tick_path.py::sports_live_tick_blob_path`, wired via
      `connectors/odds_api_ws.py`) that independently hardcoded the same literal — all moved to `"odds"` together in one
      commit (see Progress Log) since changing only the write path would have broken sports-shard routing (captured rows
      would fall through to the generic non-sports branch) and left captured-vs-sentinel rows permanently split under
      different `data_type` values. 9 existing unit tests updated to assert the new canonical value; full
      `quality-gates.sh` green (10,796+ passed).
- [ ] [DATA] P1. Re-stamp the ~3.2K `trades` rows written 2026-08-10 → fix-date to `odds` (GCS path + manifest, both
      surfaces) via the existing restamp tooling; verify with a fresh census showing 0 `trades` rows with `attempted_at`
      after the fix deploy time.

## Progress Log

- **2026-08-15 (slot-30, data_engineering) — P0 live-writer fix shipped, `market-tick-data-service@28e2eb36d8`.**
  Investigation before editing (per the "AO-eligible = outcome determinable, but resolve genuine ambiguity first" rule)
  found this todo's own framing understated the true fix scope in two ways:
  1. **The `shard_counts` tuple's `data_type` slot is a coupled write/detect pair, not just a stamped value.**
     `manifest_finalize.py:416` (`if itype_key == "odds" and data_type_key == "trades":`) and `sentinels.py:129`
     (`_build_captured_shard_sets`'s identical check) both use the literal `"trades"` to recognize "this is a sports
     shard" and route it to sports-specific source/pipeline_mode/fixture_id handling. Fixing only the write side
     (`venue_fetch.py`) would have made new captured rows carry `data_type=odds` while these detectors kept looking for
     `"trades"` — captured rows would silently fall through to the GENERIC (non-sports) branch, which routes the fixture
     id into the wrong manifest column (`underlying` instead of `fixture_id`) per the
     `sports_odds_af_shard_reconciliation_defect_2026_08_09.md` failure mode already documented in that code's own
     comments. Also updated `sentinels.py`'s Tier-2/v1 sentinel emitters (5 more `"trades"` row_key literals + one
     `_resolve_pipeline_mode_for_sentinel` call) — leaving those on `"trades"` would have permanently split captured
     (`odds`) vs. expected/failed/empty (`trades`) manifest rows for the same shard, since they'd never share a
     `data_type` value to dedup/reconcile against.
  2. **A second, independent live-write path**
     (`market_tick_data_service/live/_sports_tick_path.py::sports_live_tick_blob_path`, wired via
     `connectors/odds_api_ws.py`, real-time WS ingestion rather than the batch orchestrator loop) hardcoded the
     identical `instrument_type=odds/data_type=trades/` leaf — not mentioned in this issue's root-cause section at all.
     Fixed in the same commit. Ruled OUT as in-scope (via a research sub-agent trace, not just a grep):
     `betfair_adapter.py`'s `"trades"` literal is a genuinely distinct data axis (matched-volume/turnover, not
     odds/price — confirmed against UAC's own `VENUES_BY_ASSET_GROUP["sports"]["trades"]` entry) on a 2026-08-09
     scaffold not yet wired into any dispatch table; `sports_catalog_reader.py`'s `"trades"` literal is a dead field
     (`CatalogRow.data_type` has zero consumers in this repo — only `.instrument_id` is read downstream). **Separately
     discovered, NOT fixed here (filed as a follow-up elsewhere, not this doc's scope):** UAC's own
     `VALID_DATA_TYPES_BY_AG_AND_INSTRUMENT_TYPE[("sports","odds")]` registry
     (`unified-api-contracts/unified_api_contracts/registry/market_data_categories.py:1565-1591`) still declares
     `data_type="trades"` as the CONFIRMED canonical value, with a comment describing a 2026-07-27 reversion that
     restored lowercase `"trades"` as "the sole canonical form again" — this predates and directly contradicts the
     2026-08-08 operator ruling + 2026-08-12/13/14 executed restamp migration
     (`sports_taxonomy_p2_migration_2026_08_08.md`) that is this issue's own premise. Confirmed this table is NOT
     consulted anywhere in the live write/sentinel path fixed here (0 references in `engine/orchestrator/`), so it does
     not affect this fix's correctness, but it is a stale doc/registry that will mislead the next reader — worth a small
     follow-up todo to update it to `"odds"` (not created as a separate issue doc; small enough to fold into whoever
     next touches that registry file). QG: full `quality-gates.sh` green (10,796 passed, 0 sports-related failures after
     updating 9 tests that asserted the old `"trades"` literal — all CeFi/TradFi/prediction `"trades"` usages elsewhere
     in those same test files were left untouched, confirmed genuinely unrelated).

- **2026-08-15 (slot-19, data_engineering) — dispatched onto the P1 todo, found P0 already independently shipped by
  slot-30 mid-flight.** Had authored the identical P0 fix myself before discovering slot-30's `28e2eb36d8` had already
  landed on origin — `git pull --rebase --autostash` auto-deduplicated the byte-identical hunks, leaving a small
  residual commit (`market-tick-data-service@63728200`, LOCAL — not yet pushed, pending QG below) that fixes 2 test
  files slot-30's sweep missed: `tests/unit/test_manifest_bucket_per_asset_group_routing.py` (2 stale `"trades"`
  shard_key fixtures) and `tests/unit/engine/test_manifest_finalize_coverage.py`'s
  `test_write_shard_counts_preserves_instrument_type_all_asset_groups` (1 more). All currently pass regardless (the
  stale fixtures don't happen to exercise the renamed branch's failure mode), so this is hygiene, not a live bug.
  **Separately found this branch red for an UNRELATED reason** while chasing full `quality-gates.sh` green: 2
  `market-tick-data-service` tests (`test_migrate_tradfi_manifest_itype_casing_100pct_2026_07_25.py`,
  `test_venue_fetch_cefi_manifest_canonicalization.py`) asserted the OLD `combo`-stays-lowercase behavior that
  `unified_trading_library.canonical.canonicalize_manifest_instrument_type` no longer has — someone very recently
  shipped the correct reversal (bare `combo` now maps to `InstrumentType.COMBO`, per
  `/plans/active/issues/tradfi_instrument_type_lowercase_residual_381k_2026_08_15.md`'s live investigation) and these 2
  consumer-side tests hadn't caught up yet, so EVERY commit on this branch was failing QG regardless of content.
  Verified pre-existing via clean-tree reproduction (RULES.md § 4b) before fixing; both tests updated
  (`market-tick-data-service@6fa0dd9d`, LOCAL, same as above — small+clear+unrelated, fixed inline per the findings
  triage rule rather than filing a repo-blocker). **Status at write time**: both commits local-only (`ahead=2` on
  `live-defi-rollout`), full `quality-gates.sh` re-running now (this branch is extremely high-churn — 5+ rebases in one
  session — QG has been legitimately re-queued/re-run repeatedly by newly-landed peer commits, plus this shared host is
  under heavy fleet-wide memory/load contention causing several backgrounded QG attempts to die mid-queue before this
  one). **P1 itself (the actual ~3.2K-row GCS+manifest restamp) has NOT been started yet** — next action once QG is
  green: quickmerge ship these 2 commits, then run `scripts/sports/restamp_sports_trades_to_odds_2026_08_12.py` +
  `manifest_swap_trades_to_odds_2026_08_12.py` over `--day` 2026-08-10..2026-08-15 (the writer-fix deploy window),
  verify with a fresh census (0 `trades` rows with `attempted_at` after the fix), then flip P1's checkbox.

- **2026-08-15 (slot-19, data_engineering) — residual test-fix commits shipped; GCS-side restamp complete; manifest-side
  swap in progress.** `market-tick-data-service@6fa0dd9d99` landed on `origin/live-defi-rollout` (both local commits,
  `ahead=0` verified post-push). Then ran the P1 restamp:
  1. **GCS object pass** (`restamp_sports_trades_to_odds_2026_08_12.py`, per-day, dry-run then
     `--apply-prod --confirm-prod-write`): dry-run over 2026-08-10..2026-08-15 found 107 objects (08-10), 0 (08-11/12/13
     — gap), 550 (08-14), 57 (08-15) = 714 total (this is a GCS-object count, not the manifest's 3,229-row count — the
     two surfaces have different grain; ~30 of the manifest rows are `empty_confirmed` with no backing object, and a
     manifest row doesn't map 1:1 to a GCS object). Applied per day: **714/714 processed, 0 failed, 0 content_mismatch**
     (107 `already_present_verified` on 08-10 — pre-existing target from an earlier partial attempt; 550+57=607 freshly
     `copied` on 08-14/08-15). This satisfies the manifest-swap script's own GATING requirement (GCS pass 100% clean
     before touching the manifest).
  2. **Manifest-side swap** (`manifest_swap_trades_to_odds_2026_08_12.py --apply-prod --confirm-prod-write`): dry-run
     confirmed 3,229 rows to relabel in the merged index (`_index/availability_index.parquet`, 6,119,572 rows), 0 in the
     frozen legacy seed (expected — seed predates this residual population). **First apply attempt was killed by the
     environment** (background-task kill, same pattern as the QG runs earlier this session under host contention — load
     avg ~11-12, not this script's own defect) mid-retry on a CAS generation conflict (the merged index is a LIVE write
     target — a concurrent writer/consolidator bumped it from 6,119,572 to 6,120,990 rows between snapshot and write,
     which is exactly the generation-conflict case the script's 6-attempt retry loop exists for). **Verified no
     corruption**: a fresh dry-run after the kill still shows exactly 3,229 rows pending in the merged index and 0 in
     the seed — the script's snapshot-first ordering means a killed mid-retry leaves the source state untouched, nothing
     partially written. Retrying now (backgrounded again). **P1 checkbox NOT flipped yet** — pending: manifest-swap
     apply completes clean (0 rows left to relabel on both surfaces), then a fresh census matching this issue's own
     methodology (`read_availability_index_safe` against `market-data-tick-sports-prd-central-element-323112`) showing 0
     `trades` rows with `attempted_at` after the fix deploy time, per the task's own done-definition.
