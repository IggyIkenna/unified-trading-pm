---
doc_type: plan
title:
  Data completion to 100% — historical Progress Log record part 2 (12h-sharding strategy, asset_group writer-bug saga,
  bucket-estate cleanup)
summary: >-
  Second archive-bound record of fully-completed historical content extracted VERBATIM from
  data_completion_to_100_all_ag_2026_06_21.md (M-1) during the 2026-07-24 plan line-cap remediation
  (plans/active/issues/plan_line_cap_remediation_2026_07_23.md) follow-up pass (M-1 was still ~1820 lines after the
  first history extraction). Covers four fully-closed cross-cutting threads: (1) the 2026-06-21 12-hour mass-parallel
  sharding strategy note, (2) the 2026-06-21 Wave-1 no-fire-and-forget verify findings (bucket/CLI-arg/venv launcher
  bugs), (3) the full 2026-06-22 asset_group-blank-on-captured-rows writer-bug saga (root cause, UTL fix, per-AG
  re-stamp, MDPS-shard-column variant, tarball-deploy race), and (4) the 2026-07-13/07-14 GCS bucket-estate cleanup
  narrative (terraform-drift fixes, defi schema_version/instrument_count dtype fix, cefi CF-1..CF-14 audit,
  features-onchain-defi/config-store/ml-models-store/dex-pools-test legacy bucket migrate-verify-delete sessions). The 3
  still-open todos originally interleaved in the bucket-estate narrative (CAST-BIGINT hardening, CF-2/CF-3 cell-diff-gap
  backfill, cf-manifest-audit scheduled-job fix) were NOT moved here — they remain active in M-1's "Open follow-ups
  (bucket-estate CF audit, 2026-07-13/14)" section. No open todos are contained in this file — every checkbox below is
  already [x]. This is a read-only historical record, not an active work surface.
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    agent-orchestrator,
    alerting-service,
    client-reporting-api,
    deployment-api,
    deployment-service,
    deployment-ui,
    instruments-service,
    market-tick-data-service,
    unified-trading-library,
  ]
scope: [engineer, admin]
tags: [backfill, manifest, honest-coverage, data-completion, mtds, instruments, live-trading, history, archive-bound]
related:
  [
    /plans/active/data_completion_to_100_all_ag_2026_06_21.md,
    /plans/archive/2026_07/data_completion_to_100_all_ag_history_2026_07_24.md,
    /plans/archive/issues/plan_line_cap_remediation_2026_07_23.md,
  ]
created: "2026-07-24"
parent_epic: mtds_mdps_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0
estimate_calibrated_ai_days: 0
assigned_role: docs_reconciler
last_updated: "2026-07-24"
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  data_completion_to_100_all_ag_2026_06_21 (M-1) -- extracted 2026-07-24, plan line-cap remediation
  (plans/active/issues/plan_line_cap_remediation_2026_07_23.md) follow-up pass, fully-completed historical material with
  zero open todos, moved verbatim to relieve the parent's line-cap breach (parent was ~1820 lines against the 1000-line
  cap after the first 2026-07-24 history extraction alone was insufficient).
drift_direction: advance-code
---

# Data completion to 100% — historical record part 2 (sharding strategy, asset_group writer-bug saga, bucket-estate cleanup)

> **🟢 2026-07-24 history extraction (follow-up pass)** — this file holds content moved VERBATIM out of
> `data_completion_to_100_all_ag_2026_06_21.md` (M-1) to bring that plan under its 1000-line cap; the first 2026-07-24
> extraction (`data_completion_to_100_all_ag_history_2026_07_24.md`, now archived at `plans/archive/2026_07/`) was not
> sufficient on its own. Every section below already existed in M-1 unchanged — no content was altered, only relocated
> (and, for the bucket-estate section, the 3 still-open todos originally interleaved in that narrative were left behind
> in M-1 rather than moved here, so this file stays 100% closed). See `data_completion_to_100_all_ag_2026_06_21.md` for
> the live program (measured snapshot, per-AG launch matrix, current Progress Log, cross-cutting open work).

## Deferred work — migrated to: N/A (no open deferrals)

This file's one "DEFERRED" mention (the hard no-blank-`asset_group` QG ratchet, in the asset_group writer-bug saga
section below) describes a 2026-06-22 design decision, not a currently-open deferral — the deferred item itself was
already built and shipped (`pm@7a7346084`, STEP 5.96) and its own checkbox is `[x]` immediately below the mention.
Nothing in this closed historical record needs migrating anywhere.

## 12-HOUR TARGET — mass-parallel sharding (operator 2026-06-21)

Goal: ALL data downloaded within **12h** via fan-out, not serial single-VMs. Quota is NOT the constraint —
asia-northeast1 **CPUS 50,532 / E2_CPUS 600 / PREEMPTIBLE 60,000** (used ~19) → room for ~75 e2-standard-8 (or hundreds
preemptible) in parallel. Shard model (from `launch-mdps-sharded-backfill.sh`): **one VM per (asset_group × data_type ×
year)**; per-VM manifest shards merge cleanly (UTL ManifestWriter `MANIFEST_PER_VM_SHARDS`). 7yr × ~5 AG × ~N data-types
→ a few-hundred-VM fan-out; each VM does ONE year → wall-clock collapses from weeks → ~1yr-of-runtime (hours).

**Ordering (HARD — raw before merge):** (1) **MTDS raw** year-sharded FIRST (the actual download) → (2) **MDPS**
`launch-mdps-sharded-backfill.sh` (merge, ~30 VMs, one cmd) AFTER raw lands → (3) **live runners**. Launching MDPS
before raw is complete merges incomplete raw — gate it.

**Sharding mechanism per layer:**

- MTDS raw: each per-data-type launcher takes `START END`; wrap as `for y in 2020..2026: launch … $y-01-01 $y-12-31` →
  one VM per (data_type × year). Data-types: defi {lst-rates, dex-pools, dex-swaps, lending-indices, liquidations,
  vault-share, pyth, gas-fees, jito/marinade}; tradfi {DBEQ-nasdaq, DBEQ-nyse, CFE/XCBF}; sports {odds}; pred
  {kalshi(bulk-seed=1 VM, can't shard the 33GB download but convert is year-internal), polymarket}.
- **Wave-1 caveat (2026-06-21):** the first single-VM launches (lst-rates/odds/pred-fwd) defaulted to a SINGLE DAY
  (2026-06-20) — inadequate for full history; the loop RE-LAUNCHES them year-sharded.
- `backfill-cluster.sh --cluster <name> --start-date --end-date --asset-group` = generic date-range cluster fan-out.
- Use `--preview`/`--dry-run` on each sharded launcher before the real fan-out; cap concurrent at the E2 quota (≤~70
  e2-standard-8) — overflow → preemptible or stagger.

## Wave-1 verify findings (2026-06-21) — fix before the sharded fan-out

The no-fire-and-forget verify caught real blockers (do NOT mass-shard into these):

- [x] **Manifest consolidator HEALTHY** — cefi/defi/tradfi/prediction market-data consolidator Cloud Run Jobs all
      executed 13:45 (crons ENABLED). NOT a global blocker. (sports/instruments-tradfi-legacy crons PAUSED — expected.)
- [x] **kalshi converter bug FIXED** — `_slice_day` filter type-mismatch (corpus `timestamp[s]` vs tz-aware-ns) →
      ArrowNotImplementedError; now adapts to the column type + timestamp[s] regression test (mtds, QG-green).
- [x] [SCRIPT] P0. ✅ **`launch-mtds-lst-rates-backfill-vm.sh` bucket bug FIXED** — `get_write_bucket_name("lst-rates")`
      → `get_write_bucket_name("market_data", asset_group="DEFI")` at 4 sites in `lst_rates_handler.py`. Now resolves
      canonical `market-data-tick-defi-prd-central-element-323112`. Repo: market-tick-data-service — mtds@4c85340
- [x] ✅ [SCRIPT] P0. deployment-service — **`launch-mtds-sports-odds-backfill-vm.sh` passes `--tier 1`** which the MTDS
      CLI rejects (`unrecognized arguments: --tier 1`). Drop/fix the arg. Repo: deployment-service. —
      deployment-service@b51729b: root cause = `setup-data-pipeline-vm.sh` mtds-backfill handler assembled
      `--tier $VM_TIER`, but the MTDS download CLI has NO `--tier` flag ("Tier-1=Odds API" is an ARCHITECTURE label,
      selected by asset_group→venue auto-routing; the Odds-API paid-plan tier is encoded in the SM API key). Removed the
      bad arg; VM_TIER now logged informational-only. Fixed handler uploaded to
      `gs://deployment-scripts-…/vm/setup-data-pipeline-vm.sh`; broken `mtds-backfill-odds-1` VM (was erroring every
      chunk ~1.5h) deleted; odds backfill relaunching on the fixed handler.
- [x] [SCRIPT] P0. deployment-service — **`launch-tradfi-bf-nasdaq-ohlcv-1m.sh` runs local UAC enumeration without a
      venv** (`ModuleNotFoundError: pydantic`) → no VM created. Invoke via the workspace venv. Repo: deployment-service.
      ✅ — `python3` → `"${WORKSPACE_ROOT}/.venv-workspace/bin/python3"` — deployment-service@e31817b
- [x] ✅ [DATA] P1. prediction forward-poll returns **0 instruments** (Kalshi/Polymarket IS-enum gap) — IS prediction
      enumeration must precede the MTDS poll (same IS→MTDS ordering as the Kalshi seed). Repo: instruments-service. — VM
      `instr-backfill-pred` launched 2026-06-21 16:57 UTC, confirmed RUNNING + writing Kalshi instruments (log:
      `date=2026-06-14: 1 stale + 1 missing venues/entities — will re-fetch (stale=['POLYMARKET'], missing=['KALSHI'])`).
      IS prediction index will have Kalshi rows after this run (prior state: 1944 POLYMARKET rows, 0 KALSHI rows).
- [x] ✅ [DATA] P1. **sports — FootyStats ODDS source↔pipeline_mode mismatch (fail_fast)** [SPORTS-lane finding
      2026-06-21]: footystats fwd-poll fetches odds fine (29 snapshots/date) but the write FAILS validation — "Batch
      manifest row `source='footystats'` disagrees with `pipeline_mode='batch_odds_api'` (expects source='odds_api')".
      FootyStats odds are written under the odds_api pipeline_mode instead of a footystats-source-consistent mode.
      **This is the source-provenance / pipeline_mode surface** (UAC `source_priority.py`/`pipeline_mode.py` — the
      in-flight provenance lane's files). Fix belongs there: either footystats odds use `pipeline_mode=batch_footystats`
      (source=footystats) or the writer derives pipeline_mode from source. footystats fixtures/predictions/matches DO
      write OK; only ODDS fail. Repo: market-tick-data-service / unified-api-contracts (provenance lane). DO NOT fix
      from SPORTS lane (collision). — unified-api-contracts@b843863b (pipeline_mode.py line 428 + test line 324)
- [x] [DATA] P1. ✅ **sports — ODDS coverage OVER-COUNTS failures: live-instrument guard mislabels genuine
      "book-doesn't-price-this-fixture" as `attempted_failed`** — market-tick-data-service@050a091 | venue_fetch.py:
      exclude prediction-market venues (Kalshi/Polymarket/Novig/BetOpenly/ProphetX) from Odds-API bookmaker scope;
      sentinels.py: route uncovered (book, league) pairs → record_empty(EXPECTED_BOOKMAKER_NO_LEAGUE_COVERAGE) instead
      of record_zero_rows(was_expected=True); tests updated (2 new coverage-branch tests) | QG ✅ --no-fix [SPORTS-lane
      finding 2026-06-21, measured]: the MTDS odds expected-universe (sentinel fan-out) enumerates **every bookmaker ×
      every fixture** (BETFAIR, KALSHI, PROPHETX, NOVIG, BETOPENLY, POLYMARKET, ONEXBET…). For a 2024-02-17 soccer
      fixture only a few books price it; the rest return zero. The writer tries `record_empty(SOURCE_RETURNED_ZERO)` but
      the manifest **live-instrument guard REJECTS it** ("instruments-service catalog says 'trades' was ALIVE on
      KALSHI/2024-02-17 → use record_failed, EmptyFromLiveInstrumentError") → marks `attempted_failed`. Result: odds
      shard reads **~72% attempted_failed** (1,260/1,758 on the sampled date) while 128k odds rows DID land — coverage
      looks far worse than reality. Root: the odds expected-universe is too broad (a niche US book ≠ a valid venue for
      EPL) AND/OR the live-instrument guard is too coarse for per-(bookmaker,league,fixture) odds — a bookmaker not
      pricing a fixture is **honest absence** (empty_confirmed), not a fetch failure. Fix belongs in MTDS odds-writer +
      the odds expected-universe enumeration (scope to valid book×league pairs) + possibly relax the
      EmptyFromLiveInstrumentError guard for odds. Repo: market-tick-data-service / unified-api-contracts. Same class as
      the IS fixtures silent-empty fix (is@0db2450) but INVERTED (genuine-empty forced to failed). DO NOT fix from
      SPORTS-IS lane. **CANONICAL-COVERAGE DESIGN (operator 2026-06-21):** record genuine non-coverage as honest
      absence, not failure, via OBSERVED-coverage rules (so honest-cov reflects reality + existing mislabels migrate):
      (1) **Source separation** — Kalshi/Polymarket are PREDICTION MARKETS (asset_group=prediction; sourced via
      polymarket_clob/kalshi connectors), NOT Odds-API bookmakers. Remove KALSHI/POLYMARKET from the Odds-API book set;
      their prices flow through the prediction pipeline into canonical format; pred-vs-book dispersion is a
      FEATURE-layer join, not a source merge. (2) **(bookmaker × league) observed-coverage map** = the 80/20:
      `covered := observed odds-count > 0 across history`. A book that NEVER priced a league doesn't cover it → all
      (book, league, \*) cells are NOT-EXPECTED / `empty_confirmed(reason=BOOKMAKER_NO_LEAGUE_COVERAGE)`, never
      attempted_failed (handles regional books: a UK book ≠ Brazil Série B; Pinnacle≈global; DraftKings≈US). (3) **(book
      × league × season)** rolling window — coverage changes per season (book adds/drops leagues). (4) **per-fixture
      big-vs-small** (finest, optional) — within a covered league a book may skip minor fixtures; conservative:
      covered-league + both-teams-top-tier ⇒ expect, else allow empty_confirmed. **Where:** observed-coverage registry →
      UAC canonical (DERIVED from captured odds, refreshed periodically); odds expected-universe (sentinel fan-out,
      MTDS) reads it → only enumerates in-coverage; relax the EmptyFromLiveInstrumentError guard for odds so
      in-coverage-but-unpriced ⇒ empty_confirmed. **Migration:** reconcile script re-labels existing `attempted_failed`
      → `empty_confirmed(BOOKMAKER_NO_COVERAGE)` where (book,league) observed-out-of-coverage → the ~72%-failed
      collapses to genuine absence + honest-cov reads healthy. Repo: UAC + market-tick-data-service (coordinate with
      provenance lane).
- [x] ✅ [DATA] P1. **sports — manifest DOUBLE-COUNTING: consolidated FIXTURES inflated ~1.16× by pipeline_mode
      dedup-key drift** — UAC@40751840 (footystats_odds BATCH_FOOTYSTATS→BATCH_ODDS_API, test aligned) + IS@9273508
      (canonicalize script: ArrowInvalid handler broadened, no-op write guard added); migration script is idempotent —
      existing data already canonicalised by v9 populate run. The consolidated `availability_index` has 2 rows for the
      same (date, league, fixture) cell — e.g. EPL 2019-08-09 (1 real game) has a
      `pipeline_mode=batch_instruments_service` row (older runs, fixture_id=None) AND a
      `pipeline_mode=batch_api_football` row (current runs). The consolidator dedups "last-write-wins BY MANIFEST KEY",
      but pipeline_mode is IN the dedup key → the same logical cell under two pipeline_modes survives as 2 rows →
      inflates captured counts (76,087 raw → 65,521 distinct-by-fixture_id, ~16%). Root = the source-aware pipeline_mode
      standardization is MID-FLIGHT (old = generic `batch_instruments_service`, new = `batch_api_football`); historical
      rows not yet migrated to the canonical source-aware mode. **This is the provenance/pipeline_mode lane's domain**
      (they are editing `pipeline_mode.py` / `source_priority.py` now). Fix = (a) standardize sports IS-fixtures
      pipeline_mode to ONE canonical value + (b) migrate historical `batch_instruments_service` sports rows → canonical,
      so the dedup-key collapses the dups. Repo: unified-api-contracts + unified-trading-library (manifest_consolidator)
      — coordinate with provenance lane. DO NOT fix from SPORTS-IS lane (collision with active pipeline_mode edits).
- [x] ✅ [SCRIPT] P1. **sports — IS `_write_team_mapping` GCS-429 redundant-write FIXED** (instruments-service, this
      lane): the STATIC team-mapping table (UAC EPL/Bundesliga constants, byte-identical every call) was re-written to
      the SAME GCS blob on EVERY backfill date (~1.1k writes/run/VM → GCS hot-object 429s, ~16% rejected, no retry; the
      blob was still correct since 84% succeeded — waste + 429-spam, not data loss). Now write-once-per-process. The
      operator's transfer-window point: the canonical source
      `unified_api_contracts.canonical.domain.sports.transfer_windows.is_transfer_window_open()` ALREADY gates
      `transfer_records` (sports_per_source_rules.py) — applies to roster/transfer data, NOT this static table nor
      per-fixture match stats. Repo: instruments-service.
- [x] ✅ [DATA] P3. **sports — TYPE the ~296k legacy blank-reason `empty_confirmed` cells (escaped the typed-reason
      gate) + verify the leak is closed** (instruments-service, this lane, 2026-06-24). FINDING: the live `-prd-` sports
      `_index` carried **296,212** `empty_confirmed` cells with a BLANK `error_reason` — a SINGLE bulk write
      2026-04-21..29 that PRE-DATES the `record_empty` blank-reason gate (`LegacyBlankErrorReasonError`, landed
      2026-05-07). Blank reason → `is_out_of_coverage_window("")`=False → mis-counted as in-window gaps. **PART 2 (leak)
      = ALREADY CLOSED in code**: the UTL `record_empty` writer gate HARD-RAISES `LegacyBlankErrorReasonError` on blank
      (`unified_trading_library/manifest_writer/_writer_record.py:214`) AND every sports orchestrator callsite passes a
      typed reason (`record_empty(reason=EXPECTED_NO_FIXTURE / EXPECTED_NO_PROVIDER_COVERAGE / ...)` in
      `engine/orchestrator/{process_zero_records,sports_reference_fixtures,footystats,understat,process_preflight}.py`);
      these 296k are purely legacy, no live path makes new blanks. **PART 1 (type) = SHIPPED + VERIFIED LIVE**:
      `scripts/reconcile_sports_blank_empty_reason_2026_06_24.py` — data-type-aware: api_football entities
      (`is_league_entity_covered`→`EXPECTED_NO_PROVIDER_COVERAGE`; in-coverage → fixture-existence index from captured
      FIXTURES `af_league_id`→canonical → `EXPECTED_NO_FIXTURE` / `SOURCE_RETURNED_ZERO`); understat XG
      (`does_understat_cover`); footystats PREDICTIONS/ODDS/MATCHES + SFI fixture-pin. Consolidator-safe per-VM shard
      (`_index/per_vm/`, snapshot to `_index/snapshots/pre_blank_reason_typing_2026_06_24.parquet` first, NO
      full-`_index` overwrite). Applied → consolidator merged on first tick: **blank-reason `empty_confirmed` in
      canonical `_index` = 0**. Typed-reason distribution: `EXPECTED_NO_FIXTURE` 269,819 (91% — legacy rows for every
      (league,date) incl. no- match days, out-of-window) + `SOURCE_RETURNED_ZERO` 26,393 (in-coverage + fixture
      existed). Golden-window RESOLVED% unchanged 98.6% (cells now correctly typed). **FINDING (big — operator
      notified):** the parallel slot-5 script `scripts/backfill_fixture_lineups_blank_reason.py` (landed at LDR tip
      `74755fe`) is **superseded** by mine + has 2 bugs — (a) reads/writes the STALE env-LESS bucket
      `instruments-store-sports-central-element-323112` (not `-prd-`; the exact gotcha class that froze defi at 6%), (b)
      `from google.cloud import storage` direct SDK (violates `resolve_bucket_name`/UCI cloud-agnostic-I/O), and it is
      FIXTURE_LINEUPS-only (~5.7k of 296k) with a coarse in-coverage→`SOURCE_RETURNED_ZERO` (no fixture split). It
      should be deleted/retired in favour of the comprehensive `-prd-`-correct reconcile. **SHIPPED:** the reconcile
      script landed on instruments-service LDR `6c86c3d` (`Quickmerge: agent` provenance trailer; QG-green via an
      isolated clean-LDR worktree — the shared clone was QG-red on slot-5's in-flight WIP, so I shipped from a clean
      worktree WITHOUT stomping foreign WIP). Tier-C drain (≤15min) promotes LDR→staging→main.
- [x] [TERRAFORM] P0. ✅ **deployment-service terraform bucket-name audit complete** —
      `manifest_consolidator_scheduler.tf` confirmed correct (canonical `${local.deployment_env_short}` throughout for
      all Group A AG buckets; legacy entries intentional for MDPS Phase 0f); deleted deprecated
      `launch-manifest-consolidator-vm.sh` (should have been deleted 2026-05-20 per codex); fixed stale
      `market-data-tick-defi-central-element-323112` echo in `launch-mtds-dex-swaps-backfill-vm.sh` →
      `market-data-tick-defi-prd-${PROJECT_ID}`. No terraform apply needed (scheduler already correct). —
      deployment-service@164e21d
- [x] ✅ [TERRAFORM] P0. **add `roles/run.invoker` IAM for the enumerator SA to `expected_universe_v2_scheduler.tf`** —
      the missing IAM that caused Cloud Scheduler to get HTTP 403 when invoking Cloud Run Jobs via OAuth token. Added
      `google_project_iam_member "expected_universe_v2_run_invoker"` (project-scoped, matching canonical pattern from
      `t1_batch_scheduler.tf`). — deployment-service@f77d76a

## Asset_group MDPS-shard-column write bug (2026-06-22, folded from M-1 "Codex SSOT updates" section)

- [x] ✅ [DATA] P1. **Manifest writer omits `asset_group` column on some shards → blank `asset_group` on CAPTURED rows
      after consolidation (writer bug, NOT a migration)**. Canonical-form session-scoped audit 2026-06-22 (consolidated
      `-prd-` `_index`, all 5 AGs, vs `written_at|attempted_at == 2026-06-22`): every OTHER canonical field on this
      session's captured writes is GREEN — `schema_version=9` 100%, `pipeline_mode` 0-blank, `source` 0-blank, no glued
      `PROTOCOL-CHAIN` venue. The ONE real defect: captured rows with `asset_group=None`. **defi 61,989** captured rows
      (`swaps_ohlcv_{15s..1d}`, venues UNISWAP_V3/V4/V2/BALANCER/CURVE/…, `pipeline_mode=batch_onchain_subgraph`,
      `source=onchain_subgraph`, `row_count>0` real data) — origin = the MDPS defi per-VM shard
      `_index/per_vm/mdps-defi-2025-20260622-074035.parquet` which **has NO `asset_group` column at all** (its
      `df.columns` lacks it), so on consolidation those rows merge as `asset_group=NaN`. **cefi 1,515** captured rows
      (HYPERLIQUID `derivative_ticker`/`book_snapshot_5`, `batch_hyperliquid`) — same class from an earlier in-session
      HL backfill shard; the FRESH cefi-hyperliquid shards (20:27Z) correctly stamp `asset_group=cefi`, so cefi
      self-heals as new shards consolidate, defi does NOT (the column-less shard persists in `_index/per_vm/`). **An
      index-only re-stamp is NON-DURABLE** — the live consolidator re-merges the column-less shard every tick and
      re-blanks. **Durable fix = the writer**: MDPS swaps_ohlcv manifest-write path must emit the `asset_group` column
      on the per-VM shard (`io/writer.py` passes `asset_group=self.asset_group` to its record calls — find the
      swaps_ohlcv shard-write path that drops it; `app/adapters/defi/swap_adapter.py` +
      `app/core/canonical_writer_shaping.py` are the candidates). After the writer fix lands + a fresh defi MDPS shard
      consolidates, the blank-ag count drops to 0 (verify via the CF audit). If the operator wants the existing 61,989
      rows fixed immediately rather than waiting for re-consolidation, a one-shot index re-stamp is safe ONLY paired
      with the writer fix + after deleting/superseding the column-less `mdps-defi-2025-…` shard (else it re-blanks).
      Repo: market-data-processing-service (writer) + market-tick-data-service (verify via
      `market_tick_data_service/scripts/audit_canonical_form.py`). Provenance: canonical-form audit Progress Log
      2026-06-22. **FIXED 2026-06-23**: Investigation confirmed MDPS code correctly passes `asset_group` at every call
      site (`candle_write_mixin.py:621` → `write_candle_parquet` → `canonical_writer.py:523` → `record_captured`). Root
      cause was UTL `ManifestWriterIngestMixin` missing `_resolve_asset_group` — fixed at
      `unified-trading-library@2b0ba65e`. Tarball rebuilt + deployed; continuous-verify 18:31Z all 5 AGs blank=0 ✅. No
      MDPS code change needed.

## Asset_group-blank-on-captured-rows writer-bug saga (2026-06-22)

### 2026-06-22 ~14:36 — Per-AG re-stamp COMPLETE (all 5 AGs, guarded) + deploy-gap pinned (writer fix not yet on VMs)

**RESUMED** the rate-limit-killed asset_group-fix session. Verified the UTL writer fix is SHIPPED + on LDR:
`unified-trading-library@2b0ba65e` is an ancestor of LDR HEAD; `_resolve_asset_group` lives in
`manifest_writer/_writer_ingest.py:502`, `MissingAssetGroupError` in `_schema.py:375`, wired into all 5 captured/record/
add/zero-fill call sites, exported from `__init__.py` — UTL tree clean. UTL = DONE.

**Per-AG re-stamp DONE** (was the open `[DATA] P1`). instruments-service@00f73c6
(`scripts/stamp_asset_group_manifest_rows_2026_06_22.py`). `--apply` ran all 5 AGs; per-AG snapshot
`_index/snapshots/pre_asset_group_stamp_{ag}_2026_06_22.parquet` written FIRST; guards held EVERYWHERE (rowcount +
captured preserved exactly, `nonblank_mismatch=0`). Stamped: cefi 242 / defi 7,938 / tradfi 26,317 / sports 5 /
prediction 42,234 blanks → bucket AG. Post-stamp `blank_after=0` on every bucket at write-time. The live `_index` had
already been largely canonicalised since the stale plan figures (1.23M etc.), so residuals were far smaller.

**Deploy gap (filed as new `[DEPLOY] P1`):** a dry-run ~40s after apply showed captured-blanks RE-ACCRUING (cefi +37 /
defi +498 / tradfi +1368) — the ~20+ RUNNING live+backfill VMs (`mtds-live-cefi-*`, `mdps-defi-*`,
`mdps-backfill-tradfi`, `cefi-hyperliquid-resume`, `fs-backfill`) bake the PRE-fix UTL from their tarball, so new
captures keep leaking blank `asset_group`. A one-shot stamp cannot win a race against stale producers; the durable
closure is `create-code-tarballs.sh` from clean LDR + relaunch (NOT a mass mid-flight kill). Stamp tool is idempotent +
guarded → interim re-run mitigation. Ship: direct-to-LDR (quickmerge blocked by a peer's dirty UAC dep I do not own;
ruff-clean `scripts/` one-off, no source gate).

### 2026-06-22 ~14:15 — UTL asset_group writer fix COMPLETED + SHIPPED (resolver layered on peer baseline)

**SHIPPED (unified-trading-library):** `ManifestWriterIngestMixin._resolve_asset_group` + `MissingAssetGroupError` + the
resolver wired into all 5 captured/record/add/zero-fill call sites. Full UTL QG green (`--no-fix`, 6293 tests).

**Reconciliation (semantic conflict — two agents, same task):** mid-ship a peer landed
`4bd9487e feat(manifest): add asset_group as first-class AvailabilityRecord field` on LDR — the SIMPLER half (field +
serializer + raw `asset_group=` pass-through, NO resolver / self-heal / error). Per the merge-the-best-version rule I
reset to the peer baseline and LAYERED my superior resolver on top: caller kwarg (normalised + closed-set-validated
against `POSSIBLE_MANIFEST_ASSET_GROUPS`) → UAC `VENUE_TO_ASSET_GROUP` venue self-heal (exact / upper / DeFi
`{PROTOCOL}-{CHAIN}`) → `""`. Both test files kept (peer's `*_column.py` + my resolver-focused `*_asset_group.py`). The
peer's version left new captures BLANK whenever the caller omitted the kwarg; mine self-heals from the venue → genuinely
closes the bug.

**Design change vs the original todo (verified-blast-radius downgrade — AUTONOMOUS rule 11):** the todo said RAISE
`MissingAssetGroupError` on a captured-market-data blank. A hard runtime raise broke **40 existing writer tests** across
10 files (DeFi `{protocol}` rows like `AAVE_V3`/`UNISWAP_V3` without `-CHAIN`, CeFi `BINANCE` without `-SPOT/-FUTURES` —
non-canonical legacy spellings real writers still pass) → it would CRASH live writers fleet-wide. So the unresolvable-
blank case STAYS `""` (fleet-safe, same as the source-blank tail); the ONLY runtime raise is the mis-stamp guard on an
EXPLICIT non-blank kwarg outside the closed set (no real caller hits it). The DeFi `{venue}-{chain}` self-heal recovers
the `AAVE_V3`+`chain=ETHEREUM` class. The HARD no-blank-captured-market-data gate is DEFERRED to a baselined QG ratchet
(below) — a counts-only ratchet, not a runtime crash.

- [x] ✅ [SCRIPT] P2. **DEFERRED — hard no-blank-asset_group QG ratchet (UTL).** Add a baselined ratchet
      (`scripts/quality_gates/*_baseline.yaml` pattern) that counts CAPTURED market-data manifest rows serialized with a
      blank `asset_group` and only lets the count go DOWN — the hard no-silent-blank gate, replacing the rejected
      runtime raise (which crashed 40 writer tests + real legacy-venue writers). Target: unified-trading-library.
      **Provenance:** reconciliation of the asset_group writer-fix ship 2026-06-22; the runtime raise was downgraded to
      fleet-safe `""` per AUTONOMOUS rule 11 (blast-radius), so the no-blank invariant needs a counts-ratchet home
      instead. — pm@7a7346084 | STEP 5.96 in base-library.sh + check_no_blank_asset_group.py +
      no_blank_asset_group_baseline.yaml (25-repo baseline seeded at 0); UTL QG verified ✅ STEP 5.96 passes

### 2026-06-22 ~13:45 — P1 fix DRAFTED-BUT-INCOMPLETE (preserved to branch) + P0 scheduler PAUSED

**P0 (DONE — re-poison blocked):**
`gcloud scheduler jobs pause expected-universe-v2-defi-daily --location=asia-northeast1` → PAUSED. The `30 1 * * *` UTC
job ran a STALE image (pre IS@42dd37c — the canonical-venue enum fix is on LDR/staging, NOT main/:latest) that re-seeds
~1.44M legacy-venue (`PROTOCOL-CHAIN`/blank-chain) phantom empties nightly (drops honest_cov_defi 18.66%→~7.5%). Pausing
stops it definitively; the legacy-venue DELETE (IS@7b6512c) is re-runnable interim mitigation.

- [x] [DEPLOY] P0. **Resume `expected-universe-v2-defi-daily`** once IS@42dd37c is on `main` + the
      `expected-universe-v2-defi` Cloud Run image is rebuilt past it (VERIFY deployed image SHA post-dates 42dd37c
      first).
      `gcloud scheduler jobs resume expected-universe-v2-defi-daily --location=asia-northeast1 --project=central-element-323112`.
      Currently PAUSED 2026-06-22. ✅ — IS PR#523 merged 2026-06-22T14:21Z; image rebuilt (sha256:0b7f3f7a = 0.35.0
      :latest, built 14:31Z); scheduler ENABLED — instruments-service@22398eb
- [x] [DATA] P2. Audit cefi/tradfi/sports/prediction enum output for the same legacy-venue phantoms (shared enumerator);
      pause+delete+canonical-reseed per-AG if found. ✅ — 22,826 phantoms flipped (sports:5509 cefi:69 prediction:16267
      tradfi:981); 8 consolidator schedulers paused/resumed; local enumerator reseeded all 4 AGs (Cloud Run containers
      broken — UAC import error in new instruments-service:latest image, see
      plans/active/issues/expected_universe_cloud_run_uac_import_failure_2026_06_23.md); post-fix dry-run: sports:348
      cefi:34 prediction:698 tradfi:4 (all transient live-pipeline writes, legacy rows gone) —
      instruments-service@slot5·human-planning-vm 2026-06-23

**P1 (DRAFTED, NOT shipped — INCOMPLETE):** the UTL writer fix was started (asset_group field on `AvailabilityRecord`,
`MissingAssetGroupError`, serializer + call-site wiring) but the agent died (transient API rate-limit) BEFORE writing
the `_resolve_asset_group` IMPLEMENTATION — `_core.py` has only the abstract `raise NotImplementedError`, so all 193
captured-write tests fail with `NotImplementedError`. NOT shippable as-is (would break every capture fleet-wide). **WIP
preserved + pushed: `origin/wip-preserve/asset-group-writer-fix-2026-06-22` (unified-trading-library).** UTL LDR tree
restored clean (the broken WIP is NOT on the integration branch). Manifest is currently correct for defi (441k existing
blanks already stamped); new captures still leak blank until this ships — re-run the per-AG stamp as interim mitigation.

- [x] ✅ [LIBRARY] P1. **Complete + ship the UTL asset_group writer fix.** — SHIPPED unified-trading-library@2b0ba65e
      (resolver `_resolve_asset_group` + `MissingAssetGroupError` + venue self-heal incl. DeFi `{PROTOCOL}-{CHAIN}` +
      closed-set validation + resolver test, layered on peer baseline 4bd9487e; full UTL QG green 120s/6293 tests).
      Design downgrade per AUTONOMOUS rule 11 (blast-radius): unresolvable-blank stays `""` (a hard runtime raise broke
      40 writer tests + real legacy-venue writers) — hard no-blank gate deferred to a baselined QG ratchet (the P2 todo
      in the 14:15 Progress Log entry). Original spec: Resume from
      `origin/wip-preserve/asset-group-writer-fix-2026-06-22`. Write `_resolve_asset_group` in
      `ManifestWriterIngestMixin` (per the `_core.py` docstring): caller `asset_group` kwarg → UAC
      `VENUE_TO_ASSET_GROUP[venue]` self-heal → blank; features/ML/strategy/service rows EXEMPT (stay ""). Target:
      unified-trading-library (T0 — all 5 AGs benefit). **RECON DONE (2026-06-22):** `VENUE_TO_ASSET_GROUP` EXISTS — UAC
      `registry/market_data_categories.py:391` (`{venue: ag for ag, venues in VENUES_BY_ASSET_GROUP...}`), importable
      from `unified_api_contracts`. The `_resolve_asset_group` impl belongs in `ManifestWriterIngestMixin`
      (`manifest_writer/_writer_ingest.py`) per the `_core.py` abstract docstring. **RECONCILE RISK:** the 193 failures
      are all `NotImplementedError` (impl missing), NOT raise-logic — once the method exists they resolve IFF the venue
      self-heals. Failing `*_does_not_raise` tests use venues `CME`/`BINANCE-SPOT`; confirm these are keys in
      `VENUES_BY_ASSET_GROUP` (`BINANCE-SPOT` likely needs normalization → `BINANCE`). If a venue doesn't resolve,
      either normalize the venue lookup in `_resolve_asset_group` or add the `asset_group=` kwarg to that test. Iterate
      `quality-gates.sh --no-fix` until the 193 pass; UTL QG ~80s/run.
- [x] ✅ [DATA] P1. **Per-AG backfill-stamp existing blank-asset_group rows** — DONE 2026-06-22 ~14:36,
      instruments-service@00f73c6 (`scripts/stamp_asset_group_manifest_rows_2026_06_22.py`, ruff-clean one-off).
      `--apply` ran all 5 AGs, snapshots `_index/snapshots/pre_asset_group_stamp_{ag}_2026_06_22.parquet` written FIRST;
      guards held everywhere (rowcount + captured preserved EXACTLY, `nonblank_mismatch=0` → no cross-AG contamination).
      Stamped blanks→AG: cefi 242 (161 cap) / defi 7,938 (7,932 cap) / tradfi 26,317 (13,583 cap) / sports 5 (2 cap) /
      prediction 42,234 (0 cap, all honest-absence denominator rows). NOTE — the live `_index` had ALREADY been
      substantially re-stamped/canonicalised since the plan figures above were taken (the 1.23M/933k/179k/74k/12k
      figures were stale), so the residual blank counts at apply-time were far smaller. **DEPLOY GAP found (NEW
      captured-blank leak):** a fresh dry-run ~40s post-apply showed blanks RE-ACCRUING (cefi +37, defi +498, tradfi
      +1368) because the ~20+ RUNNING live/backfill VMs (mtds-live-cefi-_, mdps-defi-_, mdps-backfill-tradfi,
      cefi-hyperliquid-resume, fs-backfill) still bake the PRE-fix UTL from tarball — the writer fix is on LDR but not
      yet in their image. A one-shot stamp can't win a race against stale producers; the durable no-new-blank closure is
      the tarball rebuild + relaunch (next todo). The stamp tool is idempotent + guarded → re-runnable as interim
      mitigation any time. instruments-service@00f73c6.
- [x] ✅ [DEPLOY] P1. **Rebuild VM code tarball from clean LDR (≥ unified-trading-library@2b0ba65e) + relaunch the
      market-data producers** so NEW captures stamp `asset_group` at write-time (the `_resolve_asset_group` writer fix
      is on LDR but the ~20+ RUNNING live/backfill VMs bake the pre-fix UTL from their tarball → keep leaking blank
      `asset_group` on new captured rows — verified 2026-06-22: blanks re-accrued cefi +37/defi +498/tradfi +1368 within
      ~40s of the re-stamp). Recipe: `bash deployment-service/scripts/vm/create-code-tarballs.sh` from a clean LDR
      clone, then relaunch via the standard MTDS launchers (do NOT mass-kill live producers mid-flight — relaunch on the
      normal cadence, drain+verify per VM). Until then, re-run
      `instruments-service@00f73c6 stamp_asset_group_manifest_rows... --apply` as interim mitigation (idempotent,
      guarded). Provenance: deploy gap surfaced finishing the per-AG re-stamp 2026-06-22. Target: deployment-service.
      Continuous-verify: dry-run the stamp tool → captured-blank delta == 0 across two consecutive runs. — Tarballs
      rebuilt from clean LDR (UAC d9b4e8480a94 + UTL 091774f0c9bd [includes 2b0ba65e] + MTDS 0eee1ab51e29 + IS
      5312b2ff6853 + all service repos) uploaded to GCS 2026-06-22T18:16Z. Live producers (mtds-live-cefi-\*) NOT killed
      — relaunch on normal cadence. Interim stamp `--apply` run 2026-06-22T18:31Z: cefi 4882→0 blanks (3079 captured),
      defi 97521→0 (97521 captured), tradfi 135170→0 (82297 captured), sports 0, prediction 7054→0 (3054 captured).
      Continuous-verify check at 18:31Z: all 5 AGs blank_asset_group_before=0 ✅.

### 2026-06-22 — P1: LIVE manifest-writer `asset_group`-not-stamped bug — ROOT CAUSE PINNED + fleet audit

Operator dispatch (autonomous): defi captures write manifest rows with BLANK `asset_group`; a prior one-off stamped 441k
existing defi rows but NEW captures keep arriving blank; suspected fleet-wide.

**ROOT CAUSE (layer a = the WRITER, UTL).** `AvailabilityRecord` (`unified-trading-library/.../manifest_writer/_rows.py`
line 284 dataclass + line 93 `_ROW_KEY_COLUMNS`) has **NO `asset_group` field**, and the serializer
`_records_to_dataframe` (`manifest_writer/_writer_io.py` line 413) **never emits an `asset_group` column** — the
explicit comment at `_writer_io.py:408` says "asset_group is NOT an AvailabilityRecord field — it is derived from the
GCS hive-partition key at consolidation/read time, so there is nothing to serialize here." **But that derivation is
UNIMPLEMENTED**: the consolidator (`manifest_consolidator.py`) has ZERO `asset_group` references (DuckDB unions per-VM
shard columns by name; per-VM shards are flat blobs, not hive-partitioned by asset_group). So nothing ever computes
asset_group at consolidation. Meanwhile every `record_captured`/`record_empty`/`record_failed`/`add()` ALREADY receives
`asset_group` as a kwarg (used only to resolve source/pipeline_mode, then discarded). NOT a call-site bug — call sites
pass it; the writer drops it. Fix layer = UTL (all 5 AGs benefit).

**FLEET AUDIT (consolidated v9 `_index`, prd, GCS-read 2026-06-22) — blank `asset_group` per AG:**

| AG         | rows  | blank     | populated | recent-2026-06 blank/total |
| ---------- | ----- | --------- | --------- | -------------------------- |
| cefi       | 3.88M | 179,330   | 3.70M     | 48,296/1,671,530           |
| defi       | 3.86M | 12,142    | 3.85M     | 12,142/2,456,144           |
| tradfi     | 2.85M | 933,550   | 1.91M     | 927,135/2,712,867          |
| sports     | 1.76M | 1,231,203 | 528,852   | 1,231,203/1,231,223        |
| prediction | 113k  | 74,165    | 39,215    | 72,711/96,608              |

Confirmed fleet-wide (every AG has recent-2026-06 blanks). Bucket names: market-data-tick-{cefi,defi,tradfi,sports}-prd

- market-data-tick-pred-prd. FIX (next): add `asset_group` field to `AvailabilityRecord` + thread the existing kwarg
  into every record-construction site + serialize it; raise `MissingAssetGroupError` when a market-data row can't
  resolve it (mirror `source`/`MissingSourceError`); QG ratchet + unit test. Then backfill-stamp existing blanks per-AG
  (the bucket IS the AG; snapshot-first; reuse the `populate_is_index_v9` stamp pattern).

## GCS bucket-estate cleanup — 2026-07-13/07-14 (terraform-drift, defi dtype fix, cefi CF-audit, legacy-bucket migrate/verify/delete sessions)

### 2026-07-13 (defi lane, slot-3) — legacy bucket terraform-drift fix + defi schema_version/instrument_count string→int landed; CF-2/3 gaps confirmed + deferred

Picked up a prior VERIFIED (read-only, live-checked) investigation's findings for `asset_group: defi`:

- [x] [CODE] P0. **Terraform-drift fix — 5 recreated-empty-shell legacy DeFi buckets re-deleted + config
      decommissioned.** 5 of the "14 legacy DeFi buckets deleted 2026-07-12" (`evm-defi`, `solana-defi`, `gas-fees`,
      `gas-fees-prd`, `oracle-prices-prd`) had been silently recreated as empty shells (0 objects,
      `creation_time=2026-07-13T00:52:06Z` identical across all 5 — one out-of-band `tofu apply` event) because their
      `google_storage_bucket` resource blocks were still declared in `deployment-service/terraform/gcp/main.tf` after
      the physical buckets were deleted via raw gcloud. Fixed both source-of-truth AND live state (mirrors the
      prediction-bucket decommission precedent, `deployment-service@eb5f660`): removed the 5 resource blocks from
      `main.tf` (replaced with dated REMOVED-decommission comments; `evm_defi_test`/`solana_defi_test`/`gas_fees_test`
      left untouched — those are separate, still-live test buckets), removed the 3 matching import blocks
      (`evm_defi`/`solana_defi`/`gas_fees`) from `_imports_reconcile.tf`, removed the `"gas-fees"` entry from
      `manifest_consolidator_buckets_extended` in `manifest_consolidator_scheduler.tf`. Live-state reconciliation via
      gcloud (no terraform apply run — no accessible tfvars, per this session's prior finding): deleted the live
      `uts-prod-manifest-consolidator-gas-fees-cron` Cloud Scheduler job + `uts-prod-manifest-consolidator-gas-fees`
      Cloud Run Job (confirmed live before delete), then re-confirmed all 5 buckets empty (`gcloud storage ls` → 0
      objects each) and re-deleted them via `gcloud storage buckets delete` (all 5 confirmed 404 after).
      `terraform fmt -check` clean on the 3 touched files; `quality-gates.sh` full green (122s). Evidence:
      `deployment-service@a596b62efdd7695f8283ca3b2b106c5e1d6a4135`.
- [x] [DATA] P0. **defi canonical `_index` — `schema_version` + `instrument_count` STRING→int64 fix, re-run + landed.**
      The whole `schema_version` column in defi's `-prd-` `_index/availability_index.parquet` was stored as STRING (not
      just the known 988 v6 rows — confirmed by dry-run: `{'9': 27445027, '6': 988}`, quoted keys = string dtype).
      Re-ran the existing `populate_v9_index_columns_inplace.py --asset-group defi` (code already shipped `ffefb02c`) —
      dry-run confirmed the 988 v6→v9 rows, gate OK (rows/captured preserved). Additionally found `instrument_count`
      ALSO stored as string (6,862,072/27,446,015 rows) and NOT covered by the existing populator; added the same
      cast-to-int64 logic (small, contained change —
      `df["instrument_count"] = pd.to_numeric(..., errors="coerce").fillna(0).astype("int64")`, mirroring the existing
      `schema_version` cast) and re-ran `--apply` so both landed in one pass. GATE held: rows 27,446,015→27,446,015
      (unchanged), captured 3,011,728→3,011,728 (unchanged, no regression), `schema_version` 100% int `9` post-apply,
      `pipeline_mode`/ `source`/`asset_group` 100% non-blank post-apply. Independently re-read the live `_index`
      post-apply to verify: `schema_version dtype=int64, unique=[9]`, `instrument_count dtype=int64`, `rows=27446015` —
      confirmed, not just trusting the script's own report. Evidence:
      `market-tick-data-service@5011aea10edd6e415f4b38db61a561ce3316a73d`. **Deferred (not done, flagged for the
      plan)**: the "optional hardening" suggestion — explicit `CAST AS BIGINT` for `schema_version`/`instrument_count`
      in `unified-trading-library/unified_trading_library/manifest_consolidator.py` `_duckdb_merge_payload`'s
      incremental-merge + full-rebuild `COPY` projections (~lines 1926/1942-1952) — was **not implemented this pass**:
      that SQL is shared cross-AG infra (cefi/tradfi/sports/pred all flow through the same merge), out of this session's
      defi-only scope, and a `SELECT *`→explicit-cast rewrite of a live merge path used by every asset group's
      consolidator needs its own reviewed change + test pass, not a same-session bolt-on. Flagging as a follow-up todo
      (see the dedicated `[CODE] P2` item immediately below).

- [x] [DATA] P0. **VM check — `mtds-lending-indices-20260712-112557` still RUNNING** (not yet shut down/complete;
      `VM_SHUTDOWN_ON_COMPLETION=true` means absence = completion, and it is still present). No action taken per
      instructions (report only) — lending-indices buckets untouched.
- [x] [DATA] P0. **Honest CF-audit status report (defi, this session) — NOT full C-GREEN.** After items above land,
      defi's `schema_version`/`instrument_count` dtype hygiene is now clean (100% int64) and the 5 terraform-drift
      legacy buckets are gone from both config and live state, but defi will **NOT** reach full C-GREEN in this pass:
      the CF-2/CF-3 partition-path gaps above (~703 dates, real, confirmed) need a physical relabel/backfill migration
      that is out of scope for this session — reported honestly, not overstated as resolved.

### 2026-07-13 (cefi lane, slot-3) — first-ever post-apply CF-1..CF-14 audit recorded; cefi is the LEAST-ready of the 3 AGs worked this session

Recording a prior VERIFIED (real execution, live-checked) investigation's findings for `asset_group: cefi`. This was the
**first-ever post-apply CF-1..CF-14 audit run for cefi** — a real execution of
`unified-trading-library/unified_trading_library/cf_manifest_audit.py` against live data (had to be run manually; see
the cross-cutting scheduled-job finding below for why). Reported honestly: **cefi is NOT close to ready**, and is the
least-ready of the asset_groups worked this session (cf. defi's honest "not full C-GREEN" report immediately above).

- [x] [DATA] P0. **Real REDs found on BOTH cefi manifest surfaces — recorded, NOT fixed, NOT checked off.**
  - `instruments-store-cefi-prd`: **L6-legacy-only is RED at 18,076 cells.** This CORRECTS the stale "23 legacy-only
    cells" figure this plan carried at the `cefi instruments-store _index v8→v9 single-walk` todo above (now annotated
    inline with a `[2026-07-13 CORRECTION]` note pointing back here) — that number was wrong/stale; the real,
    freshly-measured figure is 18,076, roughly 785x larger than previously believed.
  - `market-data-tick-cefi-prd`: multiple CFs RED, all tied to already-tracked open todos in this same doc — the E4
    orphan sweep, E5 rebuild-with-`pipeline_mode`/`source`-via-`ManifestWriter.add()`, E7 verify-loop, and E8 legacy
    delete sequence (the `- [ ] [DATA] P0/P1 …` block folded in from `bucket_name_ssot_legacy_dual_write_remediation_…`
    / `cefi_manifest_canonicalisation_2026_06_01.md`, this doc's "orphan sweep" / "E4 remaining work" / "E7 Verify" /
    "E8 ⚠️ IRREVERSIBLE" todos above). These findings are consistent with — not new discoveries beyond — that existing
    open work; they are **deliberately left OPEN/unchecked** here. This pass does NOT attempt the E4-E8 remediation
    (correctly out of scope — multi-day, irreversible-adjacent work already gated on its own dry-run + coordinator G0
    prerequisites per the existing todos).
  - **No cefi decommission/legacy-bucket-delete checkbox flipped.** Cefi legacy buckets
    (`market-data-tick-cefi-central-element-323112`, `instruments-store-cefi-central-element-323112`) remain untouched,
    per instructions.
- [x] [CODE] P2. **Additive polish — `measure_honest_coverage.py` merge-degradation now logs explicitly.** Confirmed
      live (read-only) that `instruments-service/scripts/measure_honest_coverage.py`'s manifest-merge already degrades
      gracefully to primary-only when a legacy/secondary bucket is missing/404 (verified for all 5 asset_groups) — no
      crash-safety fix was needed. Added one explicit `logger.warning` in `_read_manifest`, right after the
      accessible-set is built, firing when `merge=True` and a candidate's legacy bucket is present in `candidates` but
      absent from `accessible` (secondary unreachable) —
      `"MERGE DISABLED for <ag>: legacy bucket(s) unreachable (<names>), expected_unattempted skeleton may be incomplete"`.
      Low-risk, additive-only (7 lines), no behavior change to the merge logic itself. Evidence:
      `instruments-service@80b5a9e992572db53a76cc4386cc8e36c1b4a222`.
- [x] [DATA] P0. **N1b + DIVERGENT_EMPTY — reported per instructions, NOT re-measured/resolved this pass.** Per the
      prior investigation: N1b (`UNCLASSIFIED_ADAPTER_ERROR` reconciliation) sits roughly in the 698k→1.72M range, and
      recurring `DIVERGENT_EMPTY` findings persist. Not re-confirmed with a fresh count this pass (out of scope per
      instructions — report only); flagging so the range is not silently lost.
- [x] [DATA] P0. **Honest CF-audit status report (cefi, this session) — cefi is NOT close to ready, the least-ready AG
      worked this session.** Both cefi manifest surfaces show real REDs (18,076 legacy-only cells on instruments-store,
      multiple CFs red on market-data-tick tied to the E4-E8 sequence); none of it was fixed or checked off in this pass
      — only the ⑦ additive polish item above landed. Reported honestly, not overstated: cefi legacy bucket decommission
      (`bucket_name_ssot…` L6/L7) remains correctly blocked on the existing E4→E5→E7→E8 sequence, which is genuinely
      multi-day, irreversible-adjacent work, not something to rush in this pass.

### 2026-07-14 (defi lane, slot-3) — `features-onchain-defi-prd` legacy bucket: real gap found, migrated, bucket deleted

A prior read-only audit (dispatched from this plan's cross-references into `gcs_bucket_estate_cleanup_2026_07_10.md`)
had flagged `features-onchain-defi-prd-central-element-323112` as `NEEDS_MIGRATION_FIRST` — contradicting that plan's
own §5f/§6 "ALREADY MIGRATED" classification for the same bucket (which was based on date-range containment alone). This
session re-verified the finding live end-to-end rather than trusting either prior claim, per the workspace's "never
trust looks-empty/looks-done" hard rule.

- [x] [DATA] P0. **Re-verified the audit's finding live, independently, before acting.** Fresh
      `gcloud storage ls --recursive` on the legacy bucket: 76 real objects (223 raw lines incl. dir markers), of which
      exactly **15** are `by_date/day=.../feature_group=lst_yields/features.parquet` (2026-04-03..2026-04-19, 5.7-5.8KB
      each). Cross-checked all 15 corresponding days directly against canonical
      (`features-onchain-defi-central-element-323112`): canonical had all 6 _other_ feature_groups
      (flash_loan_availability/health_factor/lending_rates/liquidation_events/rewards/risk_params) for every one of
      those 15 days, but **zero** `lst_yields` objects anywhere in canonical's full 118-day history — confirming the
      audit's finding, not just re-stating it. Versioning re-confirmed `Suspended` on both buckets (no
      noncurrent-version risk). Live-infra sweep (fresh, not reused from the audit): zero terraform references
      workspace-wide; the one superficially-matching live Cloud Scheduler job
      (`uts-prod-manifest-consolidator-features-onchain-defi-cron`, ENABLED, `*/1 * * * *`) targets the **canonical**
      flat bucket by its own description text and `manifest_consolidator_scheduler.tf`'s explicit mapping
      (`"features-onchain-defi" = "features-onchain-defi-${var.project_id}"` — no `-prd` variant declared anywhere);
      zero matching Compute instances; the live BigQuery external table `uts_feature_external.defi_onchain_features`
      also points at the canonical bucket (`sourceUriPrefix: gs://features-onchain-defi-central-element-323112/...`).
      All 4 hard-rule conditions for a bucket delete were independently satisfied.
- [x] [DATA] P0. **Migrated the 15 real `lst_yields` files, server-side, scoped to exactly the unique data (no
      whole-corpus walk).** New one-off driver `e2e-testing/scripts/defi/copy_lst_yields_prd_to_canonical_2026_07_14.py`
      (`gcs_copy_object`, idempotent skip-if-exists, dry-run by default) — dry-run confirmed 15/0/0
      (would_copy/skip/fail), `--apply` run copied 15/15, 0 failures. Evidence:
      `e2e-testing@d1f0a484fee011a2f7a6e53369e7dfffb4edede5`.
- [x] [DATA] P0. **Re-verified the migration by TWO independent methods before touching the legacy bucket.** (1)
      Per-object `gcloud storage objects describe` on all 15 canonical twins: size + `crc32c_hash` byte-identical to the
      legacy source for every single file (e.g. `day=2026-04-03`: 5729 bytes / `bnVMew==` on both sides). (2) A fresh
      full recursive `gcloud storage ls --recursive` on the canonical bucket's `by_date/` tree: 30 matching lines (15
      dir headers + 15 files) for `lst_yields`. Note: the _very first_ recursive-listing attempt immediately post-copy
      returned 0 lst_yields hits — read correctly as GCS list-index eventual-consistency lag (not a failed copy),
      re-confirmed via the per-object `describe` check (always consistent, unlike a bucket-wide list) and then
      re-confirmed again via a second full recursive listing ~2 min later, which showed all 15. Did not proceed on the
      flaky first read.
- [x] [DATA] P0. **Deleted the legacy bucket — version-aware (Suspended ⇒ live-object delete was sufficient), final
      pre-delete snapshot diffed byte-identical to the pre-migration snapshot (no drift).** `gcloud storage rm -r` (76
      objects) + `gcloud storage buckets delete`, both exit 0. Independently re-verified: `buckets describe` now 404s,
      absent from `buckets list`, and the canonical `lst_yields` twin spot-checked intact post-delete (unaffected, as
      expected for a cross-bucket copy).
- [x] [DATA] P1. **Filed the plan-drift correction in place, per findings-triage (plan claims done, real gap existed).**
      `gcs_bucket_estate_cleanup_2026_07_10.md`'s §5f/§6 "ALREADY MIGRATED" call for this bucket was wrong for the
      reason stated above (date-range containment ≠ feature_group content parity) — added a dated correction entry there
      (§5j) rather than leaving the stale claim standing, consistent with that plan's own established self-correction
      pattern (§5d, §5f). No terraform cleanup was needed: the workspace-wide grep found zero
      `.tf`/launcher/service-code references to this bucket, before or after — it was never terraform-declared.
      Evidence: `e2e-testing@d1f0a484fee011a2f7a6e53369e7dfffb4edede5`, `unified-trading-pm@<see this commit>` (this
      doc + the §5j correction).

### 2026-07-14 (infra lane, slot-3) — `config-store-central-element-323112` (flat) legacy bucket: already deleted by a concurrent session mid-dispatch; near-miss documented, remaining literal/config repoint completed

A prior read-only audit had flagged `config-store-central-element-323112` (flat) as `NEEDS_MIGRATION_FIRST` —
parity-verified byte-identical to `config-store-prd-central-element-323112` for all durable config content, but blocked
on a live GCE VM (`cefi-bitget-futures-2024-heavy-20260713-231539`) actively holding/renewing a Tardis concurrency-lease
object in the bucket every ~300s, plus 2 known flat literal defaults. This session was dispatched to execute the
migrate-then-delete sequence but found, on live re-verification (per the workspace's "never trust looks-done" hard
rule), that the delete had ALREADY happened — by a concurrent session/agent working the same dispatched instructions in
parallel.

- [x] [DATA] P0. **Re-verified live, found the bucket already gone.**
      `gcloud storage buckets describe gs://config-store-central-element-323112` and `gsutil ls` both independently 404
      (`BucketNotFoundException`); confirmed via Cloud Audit Logs this was a deliberate `storage.buckets.delete` at
      `2026-07-14T01:40:07Z` by `ikenna@odum-research.com` (the shared operator account all agent sessions authenticate
      as), preceded by 151 `storage.objects.delete` events (version-aware — covers all 10 known live objects across
      every historical generation) and ONE `storage.objects.create` on
      `config-store-prd-central-element-323112/_tardis_concurrency_lease/lease.json` at `01:40:03Z` (4 seconds before
      the delete) — a server-side copy of the final lease snapshot into canonical, exactly matching this task's
      instructed migrate-then-delete sequence, just executed by someone else first.
- [x] [DATA] P0. **Documented the near-miss the prior audit's own gate was meant to prevent.** Cloud Logging shows the
      Tardis lease was still being actively renewed every ~300s up to `01:35:22Z` — only ~4.7 min (one renewal cycle)
      before the `01:40:07Z` bucket delete — while the holding VM (`cefi-bitget-futures-2024-heavy-20260713-231539`) did
      not itself terminate until `01:47:33`/`01:48:25Z`, ~7-8 min AFTER the bucket was gone. The delete therefore ran
      ahead of the plan's own documented gate ("wait for VM completion, then delete"). Read
      `tardis_concurrency_lease.py` end-to-end to assess real impact: the design is explicitly fail-open (a lost renewal
      just lets the daemon renewer thread die silently; the caller proceeds without the lock, degrading to the pre-fix
      concurrent-IP 403 contention, never a crash). Combined with the VM's own clean self-termination ~7 min later (the
      normal one-shot-backfill completion pattern in this workspace), there is no evidence of a crash or lost work — but
      the sequencing was NOT the documented safe order, and is recorded here rather than glossed over.
- [x] [DATA] P0. **Re-verified canonical currently holds everything real.** Fresh `gcloud storage ls -r` on
      `config-store-prd-central-element-323112`: all 9 previously-verified durable config objects still present, PLUS
      the copied `_tardis_concurrency_lease/lease.json` (content-identical to the flat bucket's final snapshot — same
      embedded `holder`/`acquired_at`/`expires_at` fields, confirming it's a byte-copy, not a fresh acquisition).
      `config-store-test-central-element-323112` unchanged (still 0 objects, versioning Suspended). No terraform
      declarations found for this bucket (fresh grep, `.tf` files workspace-wide) — nothing to clean up there.
- [x] [CODE] P1. **Closed the 2 known dangling flat literals + 1 newly-discovered provisioning-yaml entry** (the real
      "migration" work still outstanding after the premature delete):
      `instruments-service/scripts/generate_domain_config.py`'s `--bucket` default (`f"config-store-{args.project_id}"`
      → `resolve_bucket_name(cloud=get_cloud_provider(), kind="config-store")`);
      `system-integration-tests/tests/smoke/test_cloud_infra_smoke.py`'s live CI-gated
      `test_core_infra_buckets_accessible` core_buckets list (same fix — this test would otherwise have started failing
      against a 404 bucket on its next real run); and a NEW finding not in the prior audit —
      `deployment-service/configs/bucket_config.yaml`'s `infrastructure_buckets.gcp` still registered
      `config-store-{project_id}` (flat), which its
      `setup-buckets.py`/`provision-test-buckets.sh`/`setup-dev-project.sh` consumers would use to silently RECREATE the
      deleted bucket on next invocation (the exact stale-config-resurrection incident pattern this workspace has hit
      before) — removed with a dated retirement comment mirroring the file's existing pattern (this edit merged cleanly
      on top of a concurrent, much larger same-file rewrite by another session executing
      `bucket_estate_consolidation_to_sub100_2026_07_13.md`'s Deferred #8). All 3 changes verified `quality-gates.sh`
      green (full run, not just the touched file) before commit.
- [x] [DOCS] P1. **Flipped the owning plan's tracking items** rather than leaving them stale:
      `bucket_estate_consolidation_to_sub100_2026_07_13.md`'s P1 "config-store split-brain" todo and its Deferred-table
      item #3 both updated to DONE with this evidence (see that plan for the cross-reference).

Evidence: `instruments-service@0782f9af`, `system-integration-tests@36d7654`, `deployment-service@7485657`,
`unified-trading-pm@<see this commit>` (this doc + the `bucket_estate_consolidation_to_sub100_2026_07_13.md` flip).

### 2026-07-14 (infra lane, slot-3) — `ml-models-store-central-element-323112` (flat) legacy bucket: fresh re-verification confirms the prior audit exactly; 0 unique data (nothing to copy) but 3 hardcoded live infra references fixed, bucket NOT deleted (redeploy unconfirmed)

A prior read-only audit had flagged `ml-models-store-central-element-323112` (flat) as `NEEDS_MIGRATION_FIRST` —
byte-size-parity-verified against the canonical `ml-models-store-prd-central-element-323112`, blocked on 3 hardcoded
consumers that still resolved the flat name directly (deployment-service's `catalog.py` + `manifest_reader.py`,
ml-service's `dependency_checker.py`). This session was dispatched to migrate the real unique data, re-verify, and
delete if the gate cleared. Per the workspace's "never trust looks-done" hard rule, every audit claim was re-run live
from scratch rather than taken on faith.

- [x] [DATA] P0. **Fresh live re-verification reconfirmed every audit number exactly.** `gcloud storage ls -l -r`
      (today, not reused from the audit): flat=38 objects, prd=157 objects, test=0 objects
      (`ERROR: ... matched no     objects` — genuinely empty). Versioning `Suspended` (disabled) on all 3, confirmed via
      `gsutil versioning get` (not just `buckets describe`, which returned an empty `versioning` block that could
      otherwise be misread). Flat bucket's own newest object timestamp is `2026-04-17T20:10:45Z` — no writes to flat at
      all since well before the 2026-07-10 migration date the audit cited, i.e. the "verify no new writes since"
      condition in `bucket_estate_consolidation_to_sub100_2026_07_13.md`'s P1 "ml legacy variants" todo is independently
      satisfied.
- [x] [DATA] P0. **Re-derived the byte-size parity diff myself (not reused from the audit) — confirms ZERO unique
      data.** Normalized both bucket listings to (relative-path, size) pairs and ran `comm -23 flat prd`: completely
      EMPTY (every one of flat's 38 objects has an identical-path+identical-byte-size twin already in prd); `comm -13`
      shows prd has 119 MORE objects than flat (the `legacy_football` migration, 38+119=157, exact arithmetic match).
      **Conclusion: there was no unique data to migrate — the "migrate the real unique data" step of this task is a
      confirmed no-op**, since the full 38-object migration already happened 2026-07-10 and is independently re-verified
      here, not merely re-read from the prior audit's own numbers.
- [x] [DATA] P0. **Terraform re-verified clean — nothing to clean up.** Fresh grep of
      `deployment-service/terraform/gcp/` found no live resource for the flat bucket (only a dated removal-comment in
      `outputs.tf`); `canonical_buckets.tf`'s `for_each` + `cloud-providers.yaml` line 98 only know the env-tiered
      (`-prd-`/`-test-`) form. The terraform cleanup this task's instructions asked for (if any stale declarations were
      found) was already done 2026-07-13, before this session started.
- [x] [CODE] P0. **Fixed the 3 live hardcoded flat-bucket references the audit found — the actual gate blocking
      deletion.** All 3 re-verified live-in-repo (not assumed from the audit) before editing:
      `deployment-service/deployment_service/catalog.py`'s `SERVICE_GCS_CONFIGS["ml-service"]["bucket_template"]`
      (imported live by the served `/state` route, `api/routes/state.py:221-224`) and
      `deployment-service/deployment_service/cli/utils/manifest_reader.py`'s `BUCKET_TEMPLATES["ml-service"]` both added
      `"ml-service": "ml-models-store"` to their existing `_SERVICE_TO_CANONICAL_KIND` dispatch maps — the exact same
      established, already-proven-safe pattern used today for `market-tick-data-service`/
      `market-data-processing-service` (this makes `_resolve_service_bucket()`/`_resolve_bucket()` call
      `resolve_bucket_name(kind="ml-models-store")` instead of formatting the dead flat template).
      `ml-service/ml_service/training/app/core/dependency_checker.py`'s `OUTPUT_BUCKETS` (CEFI/TRADFI/DEFI, consumed by
      the live `train_handler.py` CLI via `BaseDependencyChecker.get_output_bucket()`) repointed from
      `ml-models-store-{project_id}` to the literal `ml-models-store-prd-{project_id}`, mirroring this same file's own
      pre-existing `OUTPUT_BUCKETS_TEST` literal `-test-` tier convention (its base-class `get_output_bucket()` only
      does `template.format(project_id=...)` — no kind-based resolver hook exists there today, so a literal-tier fix is
      the minimal, in-pattern change; a full `resolve_bucket_name()` migration is a separate, larger follow-up per the
      `ml_artefact_path_resolver` issue already noted in this file's comments).
      `resolve_bucket_name(kind="ml-models-store")` was independently confirmed already-proven-safe in production before
      use here (`unified_trading_library/ml/model_registry.py`, `config_interface/ml_config.py` both already call it;
      `bucket_naming.py` confirms `ml-models-store` is a flat/cross-cutting kind — `asset_group` is ignored). All 3
      edits verified `quality-gates.sh` green (full run, both repos, not just the touched files) before commit —
      including recovering from a self-inflicted QG false-positive (STEP 5.11 protocol-symbol scan matched the literal
      substring `gcs_bucket` inside a comment citing the `gcs_bucket_estate_cleanup_2026_07_10.md` plan filename;
      reworded to cite the plan by description instead of verbatim filename).
- [x] [DATA] P0. **Did NOT delete the bucket — the task's own stated gate is not met.** The task's explicit condition
      for deletion is "0 remaining unique data AND no live infra references." The first half is true (verified above);
      the second half is NOT: the 3 fixes just shipped repoint the **source code**, but the **currently-deployed**
      `deployment-service` and `ml-service` instances still run the pre-fix code until their next redeploy — no Cloud
      Run revision / redeploy check was performed in this session, so I cannot claim the live-serving processes have
      actually stopped reading the flat bucket. Deleting now, before that's confirmed, would repeat exactly the
      premature-delete-ahead-of-completion pattern this same file's own 2026-07-14 `config-store` near-miss entry
      documents (a bucket deleted ~4.7 min ahead of its own gate's VM-completion condition). Per the task's explicit
      instruction ("if re-verification finds anything unexpected, STOP and report rather than deleting"), this is
      reported honestly as a real gate failure, not forced through.
- [x] [DOCS] P1. **Cross-referenced (did not edit) the sibling tracking plan.**
      `bucket_estate_consolidation_to_sub100_2026_07_13.md`'s P1 "ml legacy variants" todo and its Deferred-table item
      #2 both independently track this same bucket (worded as "resolver fixed §5h — verify no new writes since, then
      delete" / "UTL PATH_REGISTRY ml rows still resolve the flat names (live deployment-api data-status readers)").
      That plan's own gate is about a DIFFERENT consumer set (UTL `PATH_REGISTRY`-based readers feeding
      `deployment-api`, already repointed via `utl@8cec8786` per this file's earlier 2026-07-14 entry) than the one this
      session fixed (deployment-service's own local dicts + ml-service's own local dict, neither of which route through
      UTL `PATH_REGISTRY` at all). Left that plan's checkboxes un-flipped rather than guess at wording that conflates
      the two gates — flagging here for whoever next executes that todo that BOTH gates (this session's 2 repos + that
      plan's `deployment-api` redeploy) must clear, with a no-new-writes re-check, before the flat bucket is actually
      safe to delete.

**Next step (not done here, explicitly deferred per the gate above)**: confirm `deployment-service` + `ml-service` have
redeployed onto commits `deployment-service@3af067b` / `ml-service@83ea9f9` (or later), re-confirm zero new writes to
the flat bucket since `2026-04-17T20:10:45Z`, confirm `deployment-api`'s own redeploy gate
(`bucket_estate_consolidation_to_sub100_2026_07_13.md` Deferred #2) has also cleared, THEN delete
`ml-models-store-central-element-323112` (no version-aware handling needed — versioning confirmed `Suspended`/off).

Evidence: `deployment-service@3af067b`, `ml-service@83ea9f9`, `unified-trading-pm@<see this commit>` (this doc entry).

### 2026-07-14 (infra lane, slot-3) — `dex-pools-test-central-element-323112` legacy test-tier bucket: DELETED after fresh live re-verification confirmed the prior audit exactly; no terraform footprint existed to clean up

A prior read-only audit (`gcs_bucket_estate_cleanup_2026_07_10.md`) had verdicted
`dex-pools-test-central-element-323112` `SAFE_TO_DELETE_NOW` — 0 live objects (3 independent methods), not versioned, no
terraform resource, no live infra reference. This session was dispatched to re-verify from scratch (not trust the prior
audit) and, if the gate held, execute the delete + any terraform cleanup. Per the workspace's "never trust
looks-done/looks-empty" hard rule, every claim was re-run live rather than taken on faith.

- [x] [DATA] P0. **Fresh live re-verification reconfirmed every audit number exactly.** `gcloud storage ls -l`,
      `gcloud storage du --summarize`, and `gcloud storage objects list | wc -l` (all run today, not reused from the
      audit) → 0 objects / 0 bytes, all 3 ways. `gcloud storage buckets describe --format=json` shows no
      `versioning_enabled` field at all (absent = disabled) — matches the prior audit's `versioning_enabled: false`
      finding. Bucket `creation_time: 2026-07-10T21:19:12Z`, `soft_delete_policy.retentionDurationSeconds: 604800`
      (irrelevant to bucket deletion — soft-delete only retains deleted _objects_, and there were none).
- [x] [DATA] P0. **Terraform re-verified clean — no resource ever existed for this bucket (not just "already
      removed").** Grepped every `.tf` file in `deployment-service/terraform/gcp/` for `dex-pools`: all hits are either
      dated removal-comments, Cloud Scheduler _operation_ names (`collect-dex-pools`), or the live-event-log warm-sink
      Pub/Sub topic/BigQuery-external-table (`persist_defi_dex_pools`, which writes to the shared `var.warm_gcs_bucket`,
      not a dedicated dex-pools bucket) — zero `resource "google_storage_bucket"` blocks for `dex-pools` in any tier.
      Read the exact precedent commit `deployment-service@f04cc39`
      (`fix(config): retire     dex-pools/lst-rates/perp-funding bucket kinds`) diff directly:
      `canonical_excluded_kinds` dropped `dex-pools` from its set entirely on 2026-07-13, and only
      `lst-rates`/`perp-funding` ever had dedicated `google_storage_bucket` resource blocks (both already deleted in
      that same commit) — `dex-pools` was only ever a `for_each`-exclusion, never its own resource, in either the `-prd`
      or `-test` tier. **Conclusion: there was no terraform declaration to clean up — the task's "remove the resource
      block(s)" step is a confirmed no-op**, unlike the `evm-defi`/`solana-defi`/`lst-rates-prd`/`perp-funding-prd`
      precedents this session's pattern was modeled on, which did have real blocks to delete.
- [x] [DATA] P0. **Re-verified no live infra references this specific bucket.**
      `gcloud scheduler jobs list     --location=asia-northeast1` + `gcloud run jobs list --region=asia-northeast1` +
      `gcloud compute instances list     --filter="name~dex-pools"` grepped for `dex-pools`: only PROD-tier entities
      exist (`uts-prod-mtds-collect-dex-pools`, `uts-prod-mtds-collect-dex-pools-cron`, `defi-fwd-dex-pools-prd`) — zero
      test-tier scheduler/Cloud-Run/VM entities, zero compute instances of any kind matching `dex-pools`. Workspace-wide
      `grep -rln` for the literal bucket name across every repo (excl. `.git`/`node_modules`) hit only the source plan
      doc itself (`gcs_bucket_estate_cleanup_2026_07_10.md`) and its own worktree copies — no code, config, or script
      anywhere resolves this literal name.
- [x] [DATA] P0. **Deleted the bucket.**
      `gcloud storage buckets delete gs://dex-pools-test-central-element-323112     --quiet` → exit 0. Confirmed via a
      live re-`describe` immediately after: `ERROR: ... not found: 404` — the bucket is genuinely gone, not just "looks
      deleted."
- [x] [DOCS] P1. **No terraform commit shipped** (nothing to remove, per the P0 finding above) and no other repo's tree
      was touched — this session's only change is this plan-doc entry, direct-pushed per the PM-doc carve-out.

Evidence: `gcloud storage buckets delete gs://dex-pools-test-central-element-323112` exit 0 +
`gcloud storage buckets describe gs://dex-pools-test-central-element-323112` → 404 (both run live this session,
2026-07-14); `deployment-service@f04cc39` (precedent commit read, confirming no resource block ever existed for
`dex-pools`, no new commit needed there); `unified-trading-pm@<see this commit>` (this doc entry).
