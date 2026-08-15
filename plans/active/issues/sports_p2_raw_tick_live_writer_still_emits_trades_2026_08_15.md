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
