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
status: resolved
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
resolved_by: slot-31, 2026-08-15
locked_by:
locked_since:
drift_direction: advance-code
depends_on: []
---

# Sports raw-tick live writer still emits `data_type=trades`

> **ARCHIVED (2026-08-15) — all 4 todos done, unlocked.** Live writer fixed at both the code (accumulator) and
> deployment-parameter (shard-spec) level; the historical + orphaned-shard residuals both re-stamped to `odds` with
> independent verification showing 0 `trades` rows remaining across every manifest surface. See Progress Log below.

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
- [x] ✅ [DATA] P1. Re-stamp the ~3.2K `trades` rows written 2026-08-10 → fix-date to `odds` (GCS path + manifest, both
      surfaces) via the existing restamp tooling; verify with a fresh census showing 0 `trades` rows with `attempted_at`
      after the fix deploy time. — GCS: `restamp_sports_trades_to_odds_2026_08_12.py --apply-prod` over `--day`
      2026-08-10..2026-08-15, 714/714 objects processed, 0 failed, 0 content_mismatch. Manifest:
      `manifest_swap_trades_to_odds_2026_08_12.py --apply-prod` relabeled 3,229 rows in the merged index
      (`_index/availability_index.parquet`, 0 in the frozen legacy seed) with CAS + post-write verification re-download
      confirming 0 `trades` rows remaining on both surfaces (first attempt killed by host contention mid-CAS-retry, no
      corruption — snapshot-first ordering held, confirmed via dry-run before retrying; second attempt succeeded clean,
      exit 0). Fresh independent census via
      `read_availability_index_safe(bucket="market-data-tick-sports-prd-central- element-323112", filters=[("data_type","==","trades")])`
      (same methodology as the original 4-surface reconciliation, different code path than the swap script's own
      self-check): **0 `trades` rows in the sports manifest, period** — trivially satisfies "0 rows with `attempted_at`
      after the fix deploy time" since none remain at all.
- [x] ✅ [OPERATOR] P0. **REOPENED 2026-08-15 (slot-19): the live writer is still emitting `data_type=trades` in
      PRODUCTION as of `attempted_at` up to 2026-08-15T10:49:54Z — after both the P0 code fix
      (`market-tick-data-service@28e2eb36d8` + `63728200`) and the P1 restamp/swap above completed.** A fresh census
      (same `read_availability_index_safe` methodology) found **1,604 NEW `trades` rows**, all `date=2026-08-15`, all
      `attempted_at` between 09:18:01Z and 10:49:54Z, spread across 32 sports venues (BETFAIR_EX_UK, SKYBET, BETFRED_UK,
      … full breakdown in the Progress Log entry below). Confirmed the CODE on current `origin/live-defi-rollout` HEAD
      is clean — `grep -n '"trades"'` across all 5 coupled call sites
      (`venue_fetch.py`/`_sports_tick_path.py`/`odds_api_ws.py`/`manifest_finalize.py`/`sentinels.py`) returns only
      comments + genuinely-unrelated tradfi/Polymarket/Kalshi `"trades"` literals, zero sports hardcodes remaining. So
      this is NOT a code-fix gap — it is a **deployment gap**: per
      `/codex/04-architecture/runtime-deployment-topology.md`
      (`market-tick-data-service (MTDH) | VM (co-located) | always-on`), the sports live writer runs as a standalone
      always-on VM process (deployed via `/codex/05-infrastructure/vm-tarball-deployment.md`'s code-tarball mechanism),
      not something a `git push` to `live-defi-rollout` auto-restarts. The running process is still executing the
      pre-fix code image. **Needs an operator decision, not a worker action**: (1) no validated safe-restart procedure
      exists for MTDS yet (`/codex/15-runbooks/safe-service-restart-procedures.md`: "No other critical service has a
      validated safe-restart procedure yet" — AO is the only one built out); (2) this VM is co-located with MDPS +
      execution-service via in_memory transport per the same topology doc, so a naive restart risks disrupting other
      live production dataflows sharing the process; (3) I do not have the specific VM identity/redeploy command for the
      sports live writer in this session. **Recommendation**: redeploy/restart the MTDS sports live-writer VM with the
      current `live-defi-rollout` HEAD (`63728200`/`6fa0dd9d` or later), then re-run the P1 restamp tooling
      (`restamp_sports_trades_to_odds_2026_08_12.py` + `manifest_swap_trades_to_odds_2026_08_12.py`) over the newly
      accumulated window once the writer is confirmed to have stopped producing new `trades` rows (a repeat census
      showing 0 NEW rows post-redeploy, not just 0 total, since restamping while the writer is still actively broken is
      pure whack-a-mole — exactly the mistake this issue's own P1 already diagnosed once for the first 3,229-row
      population). **Did NOT re-run the restamp this turn** — it would immediately go stale against the still-writing
      process. **Did NOT restart the VM** — no validated procedure + co-located blast radius + no VM identity in hand.
      **RESOLVED 2026-08-15 (slot-19): operator answered `BLK-dc9ed5f8` authorizing Option A (redeploy).** Deleted the
      stale VM (`mtds-live-sports-odds-api-trades-20260815-074026`), relaunched via the registered
      `deployment-service/scripts/vm/launch-mtds-live.sh` (auto-republished all 4 stale tarballs to current HEAD).
      **First relaunch attempt was ALSO wrong** — copied the old VM's `--shard-spec sports:ODDS_API:trades` verbatim,
      and a fresh manifest read showed the new VM (`...-111158`) still stamping `data_type=trades` despite running the
      FIXED code. Root-caused (not assumed): `parse_shard_spec()` in
      `market_tick_data_service/cli/handlers/websocket_streaming_handler.py` splits `--shard-spec` into
      `(asset_group, venue, data_type)` and threads that `data_type` straight into `LiveWebsocketRunner` — it is the
      value actually stamped into every manifest row for the run, NOT the `shard_counts` accumulator this issue's P0 fix
      touched (that accumulator governs a different call path). Verified `self._data_type` is dead-stored in
      `odds_api_ws.py`'s connector (never read) and `_resolve_connector`/`is_candle_boundary_eligible` don't branch on
      its value either, so the shard-spec's third segment is a pure manifest/routing label with no feed-selection
      side-effect — safe to correct. Deleted the mislabeled VM (~13 min old, 1,604 `trades` rows written) and relaunched
      a third time with `--shard-spec sports:ODDS_API:odds` (`mtds-live-sports-odds-api-odds-20260815-112335`) —
      confirmed via direct per-VM manifest-shard read: 325/325 rows `data_type=odds`, growing clean. The live writer is
      now genuinely fixed at the deployment-parameter level, not just the code level.

- [x] ✅ [CODE] P1. **UAC registry drift self-flagged below (slot-30 Progress Log) without a tracked todo — fixed.**
      `unified-api-contracts/unified_api_contracts/registry/market_data_categories.py`'s
      `VALID_DATA_TYPES_BY_AG_AND_INSTRUMENT_TYPE[("sports","odds")]` still declared `data_type="trades"` as canonical,
      contradicting this issue's own P0 fix + the 2026-08-08 operator ruling
      (`/plans/active/sports_taxonomy_p2_migration_2026_08_08.md`). The slot-30 finder explicitly declined to file a
      tracked todo ("small enough to fold into whoever next touches that registry file") — a HARD RULE violation (every
      follow-up must be a `- [ ]` todo, never prose); tracked+closed retroactively via
      `plans/active/issues/plan_reconciler_findings_all_2026_08_15.md`'s matching P1 bullet. **DONE 2026-08-15**: matrix
      entry flipped to `frozenset({"odds", "odds_horizon_bucket"})`, 2 dependent tests updated, full `quality-gates.sh`
      green. `unified-api-contracts@0bc2fc7c14`.
- [x] ✅ [SCRIPT] P2. **Sweep the 1,604 `trades` rows orphaned in the deleted mislabeled VM's per-VM manifest shard**
      (`_index/per_vm/mtds-live-sports-odds-api-trades-20260815-111158.parquet`, all `date=2026-08-15`) once the sports
      asset_group's manifest consolidator (hourly Cloud Scheduler cron,
      `/codex/05-infrastructure/manifest-consolidator-ssot.md`) merges that orphaned shard into the durable surfaces —
      confirmed via dry-run at fix time that BOTH durable surfaces (merged index + frozen seed) and all `2026-08-15` GCS
      objects were ALREADY clean (0 residual, 57/57 `already_present_verified` under `data_type=odds/` paths) — the gap
      is purely the transient per-VM shard, exactly the "KNOWN PHASED-STATE CAVEAT"
      `manifest_swap_trades_to_odds_2026_08_12.py`'s own docstring anticipates ("re-consolidation reintroduces trades
      rows... run this swap again"). **DONE 2026-08-15 (slot-31)**: no pre-existing background monitor was found live in
      this session (prior slot-19 monitor, if any, did not survive to this dispatch); manually triggered the sports
      `market-data` Cloud Run consolidator
      (`gcloud run jobs execute uts-prod-manifest-consolidator-market-data-sports     --region asia-northeast1 --wait`,
      per this codex SSOT's own "manual `gcloud run jobs execute` invocations during operator interventions are safe
      (CAS on canonical blob prevents double-write)" invariant) rather than wait up to an hour for the next cron cycle —
      completed clean in 5m21s. Post-consolidation dry-run confirmed the orphaned shard's 1,604 rows had landed in the
      merged index (`rows=6,156,628`, `trades to relabel=1,604`; seed unaffected). Ran
      `manifest_swap_trades_to_odds_2026_08_12.py --apply-prod --confirm-prod-write`: first attempt killed (exit 137,
      host contention — load avg ~27, matches this same issue's earlier-documented kill pattern; verified no corruption
      via a fresh dry-run still showing 1,604 pending, snapshot-first ordering held). Retried in background: succeeded
      clean (`merged: base=6,156,628 relabeled=1,604 final_rows=6,156,628`, VERIFY 0 remaining; seed unaffected, VERIFY
      0 remaining; exit 0). **Final independent verification**: fresh dry-run shows **0 `data_type=trades` rows to
      relabel on both surfaces** — the orphaned shard is fully swept. This closes the last open todo in this issue; all
      four todos (P0 code fix, P1 restamp, P0 OPERATOR redeploy, P2 sweep) are now done.

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

- **2026-08-15 (slot-19, data_engineering) — P1 COMPLETE, checkbox flipped.** Second manifest-swap apply attempt
  succeeded clean (exit 0): merged index relabeled 3,229 rows (`base=6,120,990 relabeled=3,229`, post-write verify
  re-download confirms `data_type=trades rows remaining = 0`); legacy seed relabeled 0 (unchanged, as expected, verify
  confirms 0 remaining there too). Independently confirmed with a fresh dry-run of the same script (0/0 rows to relabel
  on both surfaces) and, per this issue's own stated methodology, an independent `read_availability_index_safe` census
  (`bucket="market-data-tick-sports-prd-central-element-323112"`, `filters=[("data_type","==","trades")]`) — different
  code path than the swap script's own self-verify — returned **0 `trades` rows in the sports manifest, period**, which
  trivially satisfies "0 rows with `attempted_at` after the fix deploy time" since none remain at all. P1 checkbox
  flipped above with full evidence. Both P0 and P1 are now done — this issue is ready to archive per the
  plan-completion-and-archival-discipline SSOT (no `locked_by`, nothing blocking).

- **2026-08-15 (slot-19, data_engineering) — REOPENED: dispatched to check QG run `bd0h1ufrx` (already-landed, empty
  output — the 5 sports/tradfi test files were already shipped and the archive already reflects it, so that half of the
  instruction was a no-op) and then execute the P1 restamp. Before restamping, ran the standard pre-restamp census and
  found the population had NOT stayed at 0 — it had regrown to 1,604 rows.** Full breakdown of the new population:
  `date=2026-08-15` for all 1,604 rows; `attempted_at` range 09:18:01Z → 10:49:54Z (i.e. entirely AFTER the manifest
  swap completed and AFTER the P0 fix commits landed); 32 venues, roughly even distribution (BETFAIR_EX_UK 58, SKYBET
  58, BETFRED_UK 58, BETRIVERS 58, BOYLESPORTS 58, CASUMO 58, LEOVEGAS 58, GROSVENOR 58, FANDUEL 58, LIVESCOREBET 58,
  VIRGINBET 58, WILLIAMHILL 58, PADDYPOWER 58, SMARKETS 57, BETWAY 57, UNIBET_UK 56, BETMGM 55, LADBROKES 55, CORAL 55,
  DRAFTKINGS 55, BOVADA 54, BETONLINEAG 48, BETUS 47, LOWVIG 47, BETFAIR_SB_UK 45, BETVICTOR 41, BETANO_UK 41,
  BET888SPORT 38, FANATICS 38, WILLIAMHILL_US 28, MATCHBOOK 18, MYBOOKIEAG 10, ODDS_API 5). Re-checked the code on
  current HEAD across all 5 previously-fixed call sites (`venue_fetch.py`, `_sports_tick_path.py`, `odds_api_ws.py`,
  `manifest_finalize.py`, `sentinels.py`) — confirmed clean, no sports hardcode remains, only unrelated comments +
  genuinely-distinct tradfi/Polymarket/Kalshi `"trades"` literals. So the CODE fix holds; the gap is that the **deployed
  production VM process has not been restarted/ redeployed** with it (`market-tick-data-service` is a standalone
  always-on VM service per `/codex/04-architecture/runtime-deployment-topology.md`, not an auto-pull-on-push service).
  New P0 `[OPERATOR]` todo filed above with full reasoning + recommendation. **Deliberately did NOT re-run the P1
  restamp tooling this turn** (would immediately go stale against a still-actively-writing process — literal repeat of
  the exact "not static residue, it keeps growing" failure mode this issue was originally opened to fix) **and did NOT
  attempt to restart/redeploy the VM** (no validated safe-restart procedure exists for MTDS yet, the process is
  co-located with MDPS + execution-service live dataflows per the same topology doc, and I don't have the specific VM
  identity in this session — a blind restart of a co-located, unverified-procedure production service is outside
  AO-worker scope without operator sign-off). Task NOT marked done; slot 19 continuing to hold this task pending the
  operator redeploy decision above.

- **2026-08-15 (slot-19, data_engineering) — operator answered `BLK-dc9ed5f8`, redeploy executed, second latent bug
  found+fixed en route, writer now genuinely clean.** Operator authorized Option A (redeploy the writer now, citing the
  data-pipeline-correctness "fix in full, don't mop up around a known root cause" hard rule + the pre-live-trading
  maintenance-restart carve-out for brief downtime). Sequence:
  1. Deleted `mtds-live-sports-odds-api-trades-20260815-074026` (confirmed via 3-signal staleness check per
     `agents/infra.md` STEP 0.65 — heartbeat, `run.log` tail, manifest mtide — all showed the process ALIVE but running
     PRE-FIX code, an inverted case from what that guardrail normally guards against: verified by diffing
     `venue_fetch.py` on the VM via SSH against local HEAD, `shard_counts[(bm_str, "trades", ...)]` on the VM vs
     `"odds"` locally).
  2. Relaunched via `launch-mtds-live.sh` with the old VM's own extracted metadata verbatim
     (`--shard-spec sports:ODDS_API:trades`, same 5-league instrument-id list, `--env prod --live-source native`) —
     `lc_verify_tarball_freshness` auto-republished all 4 stale tarballs (mtds/UAC/UTL/deployment-service) to current
     HEAD before boot, confirmed via its own re-verify pass. New VM `...-111158` came up RUNNING, `run.log` showed real
     manifest-write activity within ~5 min.
  3. **Verification caught a second bug the first diagnosis missed.** Read the new VM's per-VM manifest shard directly
     (`pandas.read_parquet` over `download_from_storage`, never `gsutil`) instead of trusting "it booted" — 1250/1250
     rows still `data_type=trades`. SSH'd in and confirmed the DEPLOYED code on this new VM already has the P0 fix
     (`shard_counts[(bm_str, "odds", ...)]`) — so the code-level fix from `28e2eb36d8` is not what's driving this row's
     `data_type`. Traced the actual driver: `--shard-spec asset_group:venue:data_type` is parsed by `parse_shard_spec()`
     and its third segment is threaded straight into `LiveWebsocketRunner(data_type=...)`, which stamps every manifest
     row for the entire run — a CLI/deployment-parameter value, independent of the accumulator fix. Confirmed safe to
     correct (not a feed-selection param) by reading `_resolve_connector`'s dispatch (keyed only on `venue`),
     `odds_api_ws.py`'s `self._data_type` (write-only, never read), and `is_candle_boundary_eligible` (pure
     enum-membership check, no crash risk either value).
  4. Deleted the mislabeled `...-111158` VM (1,604 `trades` rows written in ~13 min) and relaunched a third time with
     the corrected `--shard-spec sports:ODDS_API:odds` → `mtds-live-sports-odds-api-odds-20260815-112335`. Verified
     clean: 325/325 manifest rows `data_type=odds` and growing. **Live writer is now genuinely fixed** — both the code
     accumulator (P0, `28e2eb36d8`) AND the launch-parameter label (this turn) needed to change; fixing only the code
     (as P0 did) was necessary but not sufficient, since the live-streaming CLI path stamps `data_type` from the
     shard-spec string, not from the per-tick accumulator P0 touched.
  5. **Residual sizing before restamping** (dry-run first, per this issue's own established discipline — restamping
     against a still-broken writer is exactly the failure mode this issue exists to prevent): GCS object pass
     (`restamp_sports_trades_to_odds_2026_08_12.py --day 2026-08-15`, dry-run then apply) found 57 objects, **0 copied /
     57 already_present_verified** — the physical GCS write path was never broken; every `2026-08-15` object already
     lived under `data_type=odds/`. Manifest durable-surface dry-run (`manifest_swap_trades_to_odds_2026_08_12.py`, no
     args) showed **0 rows to relabel on both surfaces** — also already clean. The entire 1,604-row residual is confined
     to the deleted mislabeled VM's now-orphaned per-VM shard file
     (`_index/per_vm/mtds-live-sports-odds-api-trades-20260815-111158.parquet`, confirmed via direct read: 1,604/1,604
     `trades`, all `date=2026-08-15`); the ORIGINAL stale VM's per-VM shard file (`...-074026.parquet`) 404s — already
     consolidated + swept by this issue's own earlier P1 apply (3,229 relabeled). New P2 todo filed above tracking the
     sweep once the hourly consolidator merges the orphaned shard; a bounded ~75min background monitor (this session) is
     polling for that and will auto-apply+verify — this is the documented "KNOWN PHASED-STATE CAVEAT" the swap script's
     own docstring anticipates, not a new defect.
  6. **Unrelated tradfi combo-casing red** mentioned in this turn's task instruction was already found, diagnosed as
     pre-existing (RULES.md §4b clean-tree reproduction), fixed, and shipped in the prior slot-19 session segment (see
     the 2026-08-15 slot-19 entry above, `market-tick-data-service@6fa0dd9d`, covering
     `test_migrate_tradfi_manifest_itype_casing_100pct_2026_07_25.py` +
     `test_venue_fetch_cefi_manifest_canonicalization.py` — both asserted a stale `combo`-stays-lowercase behavior that
     `unified_trading_library.canonical.canonicalize_manifest_instrument_type` had already correctly reversed per
     `/plans/active/issues/tradfi_instrument_type_lowercase_residual_381k_2026_08_15.md`'s live investigation); no new
     tradfi red found in this turn's redeploy work.
