---
doc_type: issue
title:
  "api_football final re-verify (task -004): 4,268 attempted_failed (~3,116 undocumented, INJURIES-dominant) + 22,668
  blank-asset_group sports rows + 1 defi/UNISWAP_V3-BASE row mis-filed in the sports manifest under source=api_football"
summary:
  "data_engineering VERIFY (slot-5, 2026-07-14) for task sports_data_sources_canonical_completion-004 (api_football
  final re-verify) measured against the live sports canonical (instruments-store-sports, 5.76M rows). PASS: 0
  duplicate-dedup-key groups; service_name is the 3 sanctioned values (instruments-service / backfill-teams-61-leagues /
  fill-missing-player-stats). RED: (A) 4,268 api_football attempted_failed vs the todo's 0-or-documented target — ~1,152
  are the already-tracked CF11 FIXTURE_STATS/EVENTS/LINEUPS P2 class, but ~3,116 are UNDOCUMENTED (INJURIES 1,946,
  FIXTURES 612, blank-data_type 461, PLAYER_STATS 73, TEAMS 24; 2014-01-01..2026-07-06, 75 leagues, 2,141 match-days).
  (B) 22,668 api_football rows carry a BLANK asset_group (should be sports) — the consolidator's per-AG asset_group heal
  only fires for market-data-tick-{ag} buckets, never the instruments-store-sports bucket, so blank/pre-v9 rows there
  never get stamped. (C) exactly 1 row is a genuine cross-asset_group contamination: date=2026-06-26
  venue=UNISWAP_V3-BASE asset_group=defi service_name=instruments-service capture_status=attempted_failed but
  source=api_football, sitting in the SPORTS manifest — a DeFi object mislabeled as an api_football sports capture."
status: open
priority: P1
nature: notes
asset_group: [sports, defi, meta]
stage: [meta]
repos: [instruments-service, market-tick-data-service, unified-trading-library]
scope: [engineer, admin]
tags: [api_football, attempted_failed, asset_group, sports, data-correctness, reverify, manifest]
related: [../sports_data_sources_canonical_completion_2026_07_13.md]
created: 2026-07-14
parent_epic: infrastructure_master
source:
  "data_engineering VERIFY worker (slot-5, planning VM), 2026-07-14, executing AO task
  sports_data_sources_canonical_completion-004. Measured against the live sports canonical
  (instruments-store-sports-prd-central-element-323112 _index/availability_index.parquet, 5,759,085 rows) via DuckDB
  over ADC; repro scripts scratchpad/apifootball_reverify.py + apifootball_findings_char.py."
locked_by:
resolved_by:
execution_scope: orchestrator-agent
model_tier: sonnet-doable
drift_direction: advance-code
assigned_vm: planning
depends_on: []
---

## What I found

Task -004 ("api_football: final re-verify — 0 attempted_failed (or a documented operator-equivalent acceptable
residual), 0 dedup-key dup groups, correct service_name/asset_group") measured against the live sports canonical
(`instruments-store-sports-prd-central-element-323112`, `_index/availability_index.parquet`, 5,759,085 rows). Repro:
`scratchpad/apifootball_reverify.py` + `apifootball_findings_char.py`.

**PASS:**

- **0 duplicate-dedup-key groups** for api_football on the true dedup key (base + present optional dims).
- **service_name** = only the 3 sanctioned values (`instruments-service` 2,497,195 / `backfill-teams-61-leagues` 165,148
  / `fill-missing-player-stats` 8,678), all documented honest-provenance one-offs in the parent plan.

**RED (3 findings):**

### A) 4,268 attempted_failed — ~3,116 undocumented

| data_type       | attempted_failed | status                                          |
| --------------- | ---------------- | ----------------------------------------------- |
| INJURIES        | 1,946            | UNDOCUMENTED                                    |
| FIXTURES        | 612              | UNDOCUMENTED                                    |
| (blank)         | 461              | UNDOCUMENTED (blank data_type — itself suspect) |
| FIXTURE_STATS   | 408              | tracked (CF11 P2 backfill class)                |
| FIXTURE_LINEUPS | 384              | tracked (CF11 P2 backfill class)                |
| FIXTURE_EVENTS  | 360              | tracked (CF11 P2 backfill class)                |
| PLAYER_STATS    | 73               | UNDOCUMENTED                                    |
| TEAMS           | 24               | UNDOCUMENTED                                    |

~1,152 (FIXTURE_STATS/LINEUPS/EVENTS) are the already-filed CF11 `CF11_MATCH_DAY_EMPTY_GUARANTEED_TYPE` P2 backfill
(parent plan). The other **~3,116 (INJURIES-dominant) are not covered by any existing todo** and span 2014-01-01..
2026-07-06, 75 leagues, 2,141 match-days.

### B) 22,668 blank-asset_group api_football rows (should be `sports`)

Every one is an api_football sports data_type (INJURIES 8,042 / FIXTURE_EVENTS 6,791 / STANDINGS 3,360 / FIXTURES 2,311
/ TEAMS 770 / … both `empty_confirmed` and `captured`) whose `asset_group` column is BLANK. Root cause: the
consolidator's asset_group self-heal (`manifest_consolidator._asset_group_for_market_data_bucket` → REPLACE-coalesce
blank→bucket AG) only recognises `market-data-tick-{ag}` / prediction buckets; it returns `None` for the
`instruments-store-sports` bucket, so blank/pre-v9 rows in the sports manifest are never stamped `sports`. This
undercounts sports in any `GROUP BY asset_group` coverage rollup.

### C) 1 cross-asset_group contamination row

`date=2026-06-26 venue=UNISWAP_V3-BASE data_type='' asset_group=defi service_name=instruments-service capture_status=attempted_failed source=api_football`
— a DeFi (UNISWAP_V3-BASE) object sitting in the SPORTS manifest, mislabeled `source=api_football` with a blank
data_type. Wrong on venue/asset_group/source simultaneously; low volume (1 row) but a real mis-route.

## Why it matters

Data-pipeline correctness is the heartbeat. Finding A means real api_football INJURIES/FIXTURES/etc. failures are frozen
un-recovered; Finding B undercounts sports coverage on every asset_group rollup; Finding C is a cross-asset_group leak
that should never happen. None are blocked on credentials.

## Recommended decision + todos

- [x] [DATA] P1. **Re-fetch backfill the ~3,116 UNDOCUMENTED api_football attempted_failed** (INJURIES 1,946, FIXTURES
      612, blank-data_type 461, PLAYER_STATS 73, TEAMS 24) via the existing per-fixture/per-entity recovery path
      (`instruments-service` `_fetch_sports_reference_data`, same pattern as
      `api_football_attempted_failed_residual_closer_2026_07_13.py`). Whatever genuinely re-fetches to 0 rows with a
      clean 2xx `FetchEvidence` → relabel `empty_confirmed(SOURCE_RETURNED_ZERO)`; the rest must capture. Investigate
      the 461 blank-data_type failures first (a blank data_type is itself suspect — likely a writer/enumerator bug).
      (repo: instruments-service) — **STALE CHECKBOX, corrected 2026-07-24**: the "Update 2026-07-15" section below
      already states "Finding A (undocumented attempted_failed): CLOSED... no action needed on this todo beyond what's
      already landed" (`instruments-service@493393c8` + `21591e54` + `9b4f7655`). This checkbox was never flipped to
      match; flipping now, no new work performed.
- [x] [DATA] P1. **Extend the consolidator asset_group heal to the instruments-store-sports bucket** so blank/pre-v9
      sports rows are stamped `asset_group=sports` at consolidation (mirror `_asset_group_for_market_data_bucket` for
      the `instruments-store-{ag}` bucket family, OR a one-off repair pass over the 22,668 blank rows). Fixes the sports
      coverage-rollup undercount. (repo: unified-trading-library) — **CODE FIX DONE + durable:
      `unified-trading-library@86f3da96`** (`_asset_group_for_instruments_store_bucket` + combined
      `_asset_group_for_per_ag_bucket` resolver; blast-radius verified zero regression on `market-data-tick-*`, new heal
      confirmed on `instruments-store-*`; tests added; QG green; shipped). **One-off repair pass DONE and now confirmed
      DURABLE**: `instruments-service@e1f36eed` (`scripts/backfill_asset_group_blank_repair_2026_07_15.py`) applied
      twice against `instruments-store-sports-prd` (969,066 then 973,459 rows repaired, CAS-safe, row count unchanged
      both times); both initial applies reverted within ~1-10 minutes because the LIVE `market-tick-data-service` Cloud
      Run consolidator image (last built `2026-07-15T12:41:20Z`, ~2 min BEFORE the code fix landed) was still running
      the PRE-FIX consolidator code — but the normal CI/CD pipeline caught up on its own shortly after (see the "Update
      2026-07-15 (final)" section below): 0 blank rows remain, confirmed holding stable.
- [x] [DATA] P1. **Redeploy `market-tick-data-service`'s Cloud Run Job image against
      `unified-trading-library>=86f3da96`, then re-run
      `instruments-service/scripts/backfill_asset_group_blank_repair_2026_07_15.py --apply` once more.** — **DONE,
      2026-07-15, no manual redeploy actually needed**: a different concurrent agent's unrelated fix
      (`unified-trading-library@c47273c1`) landed downstream of `86f3da96` and got digest-pinned into
      `market-tick-data-service`'s Dockerfile for its own reasons, carrying this fix along for free. Confirmed 2
      successful rebuilds against that pin already happened; re-ran the repair dry-run and found **0 blank rows** — the
      consolidator's own merge cycle had already retroactively healed the entire backlog. Verified via direct gcsfs read
      (`sports: 5,432,770 / cefi: 1 / defi: 1`, the 2 non-sports rows already tracked as Finding C) and held stable
      across a re-check ~90s later. See the "Update 2026-07-15 (final)" section below for full evidence.
- [x] ✅ [DATA] P2. **DONE 2026-07-27 (slot-11)** — **Remove/relabel the 1 defi/UNISWAP_V3-BASE row mis-filed in the
      sports manifest under source=api_football** (date=2026-06-26). Trace the writer that emitted a UNISWAP_V3-BASE row
      with source=api_football into the sports bucket; delete the phantom row (CAS-safe) and fix the mis-route at source
      if reproducible. (repo: market-tick-data-service / instruments-service) — **bonus finding 2026-07-15**: a SECOND,
      previously-undocumented mislabeled row was found in the same live probe:
      `source=instruments_service asset_group=cefi capture_status=captured` (no venue/data_type distinguishing detail
      captured in the probe) sitting in the sports manifest — same bug class (wrong non-blank value, not blank), not
      fixed, folded into this todo's scope rather than filed separately. **Both rows deleted CAS-safe (snapshot-first)
      via `instruments-service@3e08f7d2` (`scripts/delete_cross_ag_phantom_rows_sports_manifest_2026_07_27.py`); root
      cause found + fixed for the captured-row class (`_is_all_run` in `process_write.py` now also triggers on a genuine
      multi-value `--asset-group` list, not just the literal "ALL" sentinel, with a regression test); the
      attempted_failed row's class is a separate, still-open structural gap in `process_completeness.py`, filed as a new
      scoped follow-up todo below rather than fixed inline (out of this cleanup's scope). Full evidence: "Update
      2026-07-27" section below.**

## Update 2026-07-15 — Finding A closed; Finding B grown (37x), Finding C unchanged, still root-caused

Live re-check against the current canonical (`instruments-store-sports-prd`, 5,432,276 rows) as part of this session's
final whole-plan re-verify:

- **Finding A (undocumented attempted_failed): CLOSED.** INJURIES and FIXTURES both now `0` (fixed
  `instruments-service@493393c8` + `21591e54` + `9b4f7655`, independently verified live). Total api_football
  `attempted_failed` is now **766** (was 4,268) — 305 is the already-tracked CF11 class (`PLAYER_STATS` 87,
  `FIXTURE_STATS` 80, `FIXTURE_EVENTS` 65, `FIXTURE_LINEUPS` 49, `TEAMS` 24), 461 is the blank-data_type residual
  (root-caused this session — see the sports plan's Progress Log 2026-07-15 entry — a genuinely separate class from
  finding A, not a re-fetch target). Both remaining classes are already tracked elsewhere; no action needed on this todo
  beyond what's already landed.
- **Finding B (blank asset_group): NOT closed, and much bigger than recorded here.** Re-measured 2026-07-15:
  api_football alone now has **844,209** blank-`asset_group` rows (was 22,668 on 2026-07-14 — a ~37x increase). This is
  the SAME root cause already documented above (the consolidator's asset_group heal never covers
  `instruments-store-sports`), not a new bug — the count grew because this session's own write volume was unusually
  large (a 328K-row pre-launch purge, multiple multi-hundred-thousand-row reconciliations/migrations, several
  residual-closer backfill rounds — none of these paths stamp `asset_group` explicitly, so they all landed as blank,
  same as every pre-v9 write always has). Also newly confirmed the SAME blank-asset_group pattern exists on every other
  sports source, not just api_football: footystats 99,048 / soccer_football_info 360 / transfermarkt 45 / open_meteo
  1,804 (`odds_api` and `mdps_odds_horizon_bucket` show **0** blank — those writers already stamp asset_group
  explicitly). The P1 todo above (extend the consolidator heal to `instruments-store-{ag}`) is the correct fix and
  should be scoped to ALL sports sources, not just api_football, given this — updating title/summary would be reasonable
  next time this doc is touched, but left as-is here to avoid rewriting another slot's filed finding without a fix in
  hand.
- **Finding C (defi/UNISWAP_V3-BASE contamination row): unchanged, still exactly 1 row, still open.**
- **Bonus, smaller finding**: a proper dedup-key check (including `instrument_id`, which the original PASS verdict's key
  did not — worth noting since it changes the "0 duplicate-dedup-key groups" PASS from 2026-07-14) finds exactly **2**
  duplicate groups, both `odds_api`/`trades`/`instrument_id∈{soccer_epl, soccer_italy_serie_a}` on `date=2026-06-21` —
  each is the same `instrument_id` captured twice with identical `row_count` at two different `written_at` timestamps (a
  benign double-write-event, not obviously corrupted underlying data) — small enough (2 groups, one date) not to warrant
  its own todo, noting here for completeness.

## Update 2026-07-15 (later) — Finding B: code fix shipped + durable; one-off repair applied but NOT yet durable (redeploy-gated)

- **Finding B — code fix landed**: `unified-trading-library@86f3da96` extends the consolidator's v9 asset_group
  self-heal to `instruments-store-{ag}` buckets (previously `market-data-tick-{ag}` only). Blast-radius verified zero
  regression on every `market-data-tick-*` bucket; every `instruments-store-*` bucket now correctly resolves its AG.
  Tests added, QG green, shipped.
- **Finding B — one-off repair applied twice, reverted both times, root cause confirmed (not guessed)**:
  `instruments-service@e1f36eed` (`scripts/backfill_asset_group_blank_repair_2026_07_15.py`) repaired 969,066 then
  973,459 blank-`asset_group` rows in `instruments-store-sports-prd` via a CAS-safe direct canonical rewrite (row count
  unchanged both times — a pure column mutation, same established pattern as
  `reconcile_mdps_odds_horizon_bucket_venue_grain_2026_07_14.py`). Both repairs were reverted within 1-10 minutes. Root
  cause, confirmed via `gcloud artifacts docker images list`: the live `market-tick-data-service:latest` Cloud Run image
  (shared by ALL 10 per-AG consolidator cron jobs) was last built `2026-07-15T12:41:20Z`, ~2 minutes BEFORE the code fix
  landed (`12:43:32Z`) — so the deployed consolidator is still running pre-fix code, and its ~60s merge cycles keep
  re-picking a freshly-reseeded blank-`asset_group` enumerator shard over the repaired canonical row (recency tie-break;
  `asset_group` is not a dedup key). Full evidence chain (generations, timestamps, exact counts per re-read) in the
  sports plan's Progress Log, 2026-07-15 entry. **Deliberately did not** attempt a 3rd apply (confirmed-losing race) or
  trigger a Cloud Run image redeploy myself (shared production infra beyond this task's scope — new todo added above for
  an operator-timed redeploy + one final repair re-run, which should hold permanently once the live image includes the
  fix).
- **Finding C**: one additional MISLABELED (non-blank wrong-value, not blank) row found —
  `source=instruments_service asset_group=cefi capture_status=captured` — folded into the existing Finding C todo's
  scope above, not fixed in this pass.

## Update 2026-07-27 — Finding C RESOLVED: both phantom rows deleted, root cause found + fixed (partially)

Worked the outstanding Finding C todo (`sports_satellite_ao_dispatch_batch3_2026_07_25.md`). Live re-verify against the
current canonical (`instruments-store-sports-prd`, 6,841,125 rows before / 6,841,123 after) confirmed both rows still
present exactly as described:

1. `date=2026-06-26 venue=UNISWAP_V3-BASE source=api_football asset_group=defi service_name=instruments-service capture_status=attempted_failed error_reason=UNCLASSIFIED_ADAPTER_ERROR`
   (written_at 18:13:50Z).
2. `date=2026-06-26 venue=BITGET-FUTURES source=instruments_service asset_group=cefi service_name=instruments-service capture_status=captured instrument_type=PERPETUAL row_count=39`
   (written_at 18:56:40Z) — a REAL CeFi capture with real data (`row_count=39`), not a diagnostic stamp.

**Root cause, confirmed via code read (not guessed):** `_write_all_venues()`
(`instruments_service/engine/orchestrator/process_write.py`) resolves ONE primary bucket per run and only switches to
per-venue bucket routing when its `_is_all_run` discriminator is True. Before this session's fix, `_is_all_run` checked
ONLY `asset_groups[0] == "ALL"` — it never checked `len(asset_groups) > 1`. The service's own shared CLI
(`unified_trading_library.service_cli`) defines `--asset-group` with `nargs="+"` (confirmed: genuine multi-value
invocations like `--asset-group SPORTS CEFI` are a real, currently-supported shape — the choices list is the 5
individual asset_groups, "ALL" is not even a listed choice, it only arises via the `cli_asset_groups or ["ALL"]`
no-flag-passed fallback). So an explicit multi-value, non-"ALL" `--asset-group` invocation silently left `_is_all_run`
False, forcing EVERY venue in that run — including row 2's real CEFI capture — into the single SPORTS-primary bucket.
**This class is now fixed** in `instruments-service` (`process_write.py`'s `_is_all_run` now also triggers on
`len(asset_groups) > 1`), with a new regression test (`TestMultiAssetGroupListTriggersPerVenueBucketRouting` in
`tests/unit/test_orchestrator_gaps.py`) that fails without the fix (proved via a stash/pop before-fix run:
`_get_instruments_bucket` was called with only `['SPORTS']`, never `'cefi'`) and passes with it.

Row 1 (a DIAGNOSTIC honest-coverage write from `process_completeness.py`'s missing-shards fallback,
`_finalize_completeness()` lines ~595-649) is a SEPARATE, still-open structural gap, NOT fixed in this pass: that
module's `ManifestWriter` instances (`_failed_manifest`, `_empty_ok_manifest`) are always constructed with the single
`bucket` param passed into `_completeness_and_retry()` — they never gained the per-venue bucket routing
(`_get_venue_bucket()`) that the main write loop has. So ANY combined multi-AG run — including the ALREADY-correctly
-detected "ALL" sentinel case — can still misroute a missing/adapter-failed non-primary-AG venue's honest-coverage row
into the primary bucket. Deliberately NOT fixed inline here: it requires threading a bucket resolver through
`_completeness_and_retry()` → `_finalize_completeness()` (a larger change to the sports daily producer's shared
completeness-check, a high-blast-radius hot path used by every instruments-service run, touching a file already at 716
lines) — out of scope for this cleanup todo. **New follow-up todo filed below** for a future dispatch.

Neither row shows evidence of an ACTIVE ongoing leak: the `asset_group` value_counts on the live manifest showed exactly
these 2 non-sports rows out of 6.84M total (both dated the same day, 2026-06-26), with 0 new phantom rows appearing
since. Treated as 2 one-off writes from a historical manual/ad-hoc multi-AG invocation, now closed off for row 2's class
going forward.

**Remediation applied**: `instruments-service/scripts/delete_cross_ag_phantom_rows_sports_manifest_2026_07_27.py`
(dry-run confirmed exactly 2 matching rows; snapshot taken first via server-side GCS copy to
`_index/snapshots/pre_cross_ag_phantom_delete_2026_07_27.parquet`; CAS-safe direct rewrite applied on attempt 1/30,
generation `1785185026081616` → `1785185292923233`, row count 6,841,125 → 6,841,123 — exactly -2, no other column
touched). Fresh re-read immediately after, and again ~1 minute later, both confirm **0 rows matching either predicate**.
Caution (per `remediate_cross_ag_prediction_bleed_round3_2026_07_24.py`'s documented precedent, where a similar delete
reverted ~30h43m later via a stale per-VM-shard re-merge): these 2 specific rows are historical one-off writes, not part
of an actively-changing daily-write population like that prior incident's blank-asset_group backlog, so the reversion
risk is lower here — but a future audit re-touching this manifest should re-confirm 0 rows matching these 2 exact
predicates before assuming this stays permanently closed.

**Both parts of the todo's Done-when are satisfied**: (a) both rows confirmed removed via a fresh re-read, snapshot
taken first; (b) the mis-routing writer is fixed with a regression test for row 2's class (multi-value `--asset-group`
list bucket routing); row 1's class is a documented, scoped, NEW follow-up todo (not "not reproducible" — genuinely
reproducible and root-caused, just deliberately out-of-scope for this cleanup pass per findings-triage: audit-scope
discoveries beyond the immediate ask get their own tracked todo, not unplanned scope absorbed inline).

- [ ] [DATA] P2. **Fix `process_completeness.py`'s honest-coverage `ManifestWriter` instances (the missing-shards
      `record_failed`/`record_expected_empty` loop and the empty-ok-venues `record_zero_rows` loop in
      `_finalize_completeness()`/`_completeness_and_retry()`) to route each venue to its OWN asset_group bucket,
      mirroring `_write_all_venues()`'s existing `_get_venue_bucket()` per-venue routing** — today these diagnostic
      writers always use the single `bucket` param passed into `_completeness_and_retry()`, so a combined multi-AG run
      (even the correctly-detected "ALL" sentinel case) can still misroute a missing/adapter-failed non-primary -AG
      venue's honest-coverage row into the primary bucket (the same bug class as Finding C's row 1, still live). Needs a
      bucket-resolver threaded through `_completeness_and_retry()`'s signature (repo: instruments-service). **Done
      when**: a regression test proves a non-primary-AG venue's `record_failed`/`record_zero_rows` call resolves that
      venue's OWN bucket (not the run's primary bucket) during a combined multi-AG run; `quality-gates.sh` green.
      Source: this doc's 2026-07-27 update.

## Update 2026-07-15 (final) — Finding B FULLY RESOLVED, no redeploy needed after all

Operator chose to expedite the redeploy this doc flagged as a follow-up. Before triggering anything, checked whether the
normal CI/CD pipeline had already caught up — **it had**, via a different concurrent agent's unrelated fix
(`unified-trading-library@c47273c1`, landed after `86f3da96` in the same linear history) whose digest happened to get
pinned into `market-tick-data-service`'s Dockerfile for an unrelated reason, carrying this fix along for free (a
digest-pinned base image, not a versioned wheel — any commit downstream of the fix that gets pinned picks it up).
Confirmed via `gcloud builds list` that `market-tick-data-service` had already rebuilt twice against the new pin. Re-ran
`backfill_asset_group_blank_repair_2026_07_15.py --dry-run`: **0 blank rows remain** — the consolidator's normal merge
cycle had already retroactively healed the entire ~969K-row backlog on its own once the fixed image went live (the heal
runs on every merge for all rows, not just new writes). Independently verified via direct gcsfs read:
`instruments-store-sports-prd` shows `asset_group` value_counts `sports: 5,432,770 / cefi: 1 / defi: 1` — the 2
non-sports rows are the already-tracked Finding C rows, not a new gap. Held stable across a re-check ~90s later.
**Finding B is closed. Both todos above (the heal + the redeploy follow-up) are DONE — no manual Cloud Build/redeploy
action was actually required.** Full evidence:
`unified-trading-pm/plans/active/sports_data_sources_canonical_completion_2026_07_13.md` Progress Log, 2026-07-15 entry.
