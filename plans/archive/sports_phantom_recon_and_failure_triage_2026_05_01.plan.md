---
doc_type: plan
title: Sports manifest — phantom recon + footystats failure triage
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-api, deployment-ui, instruments-service, unified-api-contracts]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-01
priority: P1
owner: Harsh
type: data
epic: data-pipeline-completion
completion_gates: { business: B3 }
repo_gates:
  - { repo: instruments-service, business: B3 }
depends_on: [instruments_and_market_tick_data_completion_2026_05_01.md]
---

## Deferred work — migrated to: `plans/active/sports_data_sources_canonical_completion_2026_07_13.md`,

`plans/active/issues/reconcile_phantom_manifest_rows_stale_read_overwrite_2026_07_12.md` — successor:
sports_data_sources_canonical_completion_2026_07_13, reconcile_phantom_manifest_rows_stale_read_overwrite_2026_07_12
(SFI_STANDINGS/open-meteo/api-football/understat coverage-window findings are closed or superseded by the 2020-06-06
data floor; the schema-modal quick-fix already shipped in `deployment-api`; the phantom-reconciler CAS/lost-update race
is the same bug class fixed at `unified-trading-library@75e59a89`, tracked resolved in the linked issue doc; the
VM-wait/relaunch items are long superseded by multiple later sports closeout runs. No `locked_by` is set on this file.)

> **2026-05-06 update — Phase 1 mechanism unblocked once UTL fix lands.** This plan's flip-to-`attempted_failed`
> approach was previously broken because `check_shard_freshness` (UTL `manifest_writer.py`) ignored `capture_status` —
> orchestrators saw `attempted_failed` rows as fresh and skipped retry, forcing the DELETE-and-refetch hack used in
> `sports_fixtures_truthset_recovery_2026_05_06`. **Architectural fix scheduled: extend `check_shard_freshness` to treat
> `ATTEMPTED_FAILED` as stale (default-on; opt-out via `retry_failed: bool = True` param).** Once UTL ships the fix,
> this plan's Phase 1 flip-and-retry semantics work as originally designed; truthset DELETE pattern becomes optional.
> Reference: `master_to_live_defi_2026_05_23.md` Risk Register row "`check_shard_freshness` ignores `capture_status`".

## Context

Spun out of the data-pipeline-completion kickoff session (2026-05-01). The canonical sports manifest
`gs://instruments-store-sports-central-element-323112/_index/availability_index.parquet` (2,332,893 rows, last written
2026-05-01T14:22:17 UTC) was inspected for the 3 footystats data types (`MATCHES`, `PREDICTIONS`, `ODDS` — per UAC
`gcs_paths.py` SSOT). Findings need to be triaged one at a time before declaring footystats coverage done and before
moving on to triage the other sports sources.

Footystats VM context: `fs-backfill-20260501-102703` (the most recent fs run) launched 2026-05-01 09:31 UTC with
`--start-date 2019-01-01 --end-date 2026-04-30 --sports-provider FOOTYSTATS`, exited rc=0 at 13:46 UTC, self-deleted.
Wrote 75,706 rows to `_index/per_vm/fs-backfill-20260501-102703.parquet`; consolidator merged them into canonical.

Other sports VMs still running as of session start: `af-backfill-test-20260501-095` (api-football, 2018→2026),
`sfi-backfill-20260501-102703` (soccer_football_info, 2020→2026), `tm-backfill-20260501-102707` (transfermarkt,
2018→2026), plus the long-lived `manifest-consolidator-20260429-162442` daemon. Findings below cover footystats only;
af/sfi/tm get their own pass after they finish.

## Footystats coverage snapshot (2026-05-01 14:22 UTC manifest)

| data_type   | captured | empty_confirmed | attempted_failed |   total | leagues | dates |
| ----------- | -------: | --------------: | ---------------: | ------: | ------: | ----: |
| MATCHES     |   30,022 |             278 |            2,125 |  32,425 |      81 | 3,052 |
| PREDICTIONS |   26,542 |          75,509 |            3,639 | 105,690 |      73 | 3,052 |
| ODDS        |   26,375 |          75,338 |            3,564 | 105,277 |      56 | 3,045 |
| **Total**   |   82,939 |         151,125 |            9,328 | 243,392 |         |       |

Window 2018-01-01 → 2026-05-12. Real source gaps (no football that day in a league) live in `empty_confirmed` per the v5
manifest contract — those are correct, not action items. The 9,328 `attempted_failed` rows are what this plan triages.

## attempted_failed breakdown

| error_reason                                    | count |     % | notes                                                                                  |
| ----------------------------------------------- | ----: | ----: | -------------------------------------------------------------------------------------- |
| `phantom_captured_no_parquet_at_canonical_path` | 9,067 | 97.2% | All flipped at one timestamp 2026-04-29T13:05:57 UTC — single recon sweep              |
| `TooManyRequests`                               |   252 |  2.7% | RapidAPI 429s spread across 2018-08 → today                                            |
| `RuntimeError`                                  |     9 |  0.1% | All `attempted_at` 2026-05-01 (early fs VMs `fs-backfill-20260501-012417` / `-014139`) |

## Tooling caveat — recon overwrite race (must fix or work around)

`instruments-service/scripts/reconcile_phantom_manifest_rows.py` does a **read → process → full overwrite** of canonical
`_index/availability_index.parquet` with no compare-and-swap, no `if_generation_match`, no sentinel-lock. The
consolidator daemon writes to the same file every 60s using a sentinel-lock. Running recon non-dry-run while the
consolidator (or any per-VM merge) is active risks losing whatever the consolidator just merged (see
[vm-tarball-deployment.md § Manifest consolidator daemon](../../codex/05-infrastructure/vm-tarball-deployment.md) for
the consolidator's lock pattern).

**Options to fix:**

1. Add sentinel-lock acquisition to recon script (matches consolidator pattern).
2. Use `if_generation_match` on the upload + retry on mismatch.
3. Stop the consolidator daemon for the recon window only (operational workaround).

Dry-run is always safe (read-only).

## Execution

### Phase 0 — Safe diagnostics (run any time, no writes)

- [x] [AGENT] P0. Dry-run recon — DONE 2026-05-01 23:16 UTC (~2 min wall clock for 869,174 candidates / 3,630 days /
      635k blobs cached). **Result: 36,770 rows would be flipped to `attempted_failed`** (vs the 9,328 already at
      attempted_failed in the manifest). Detail by data_type:

      | data_type             | new phantoms | currently captured | phantom%   |
              | --------------------- | -----------: | -----------------: | ---------: |
              | INJURIES              |        9,872 |             10,559 |  **48.3%** |
              | PLAYER_VALUES         |        3,814 |                979 |  **79.6%** |
              | STANDINGS             |       13,022 |            183,709 |       6.6% |
              | PLAYER_STATS          |        3,053 |             20,758 |      12.8% |
              | FIXTURE_LINEUPS       |        2,842 |             30,997 |       8.4% |
              | FIXTURE_STATS         |        2,629 |             36,685 |       6.7% |
              | FIXTURE_EVENTS        |          555 |             35,045 |       1.6% |
              | TEAMS                 |          383 |            103,138 |       0.4% |
              | SFI_LEAGUES           |          207 |             13,006 |       1.6% |
              | ODDS                  |          204 |             26,171 |       0.8% |
              | PREDICTIONS           |          189 |             26,353 |       0.7% |
              | (others)              |            0 |                  — |       0.0% |

              **Critical interpretation: 79.6% of `PLAYER_VALUES` and 48.3% of `INJURIES` "captured" rows are lying.** These
              manifest entries claim parquet exists; recon's bulk GCS list says it doesn't. This is a much bigger problem than
              the initial 9k flagged failures.

- [x] [AGENT] P0. Per-source breakdown of ALL 6 sports sources (api-football / footystats / understat / transfermarkt /
      sfi / open-meteo) — see "Per-source findings" section below.
- [x] [AGENT] P0. Investigate empty-league_id phantoms. Result: 2,458 rows confirmed phantoms with empty league_id (in
      footystats data types alone — wider problem affects every data type). Most are 2018-2019 dates with
      `instrument_count > 0`, `expected=True`, `written_at=2026-04-14 to 2026-04-29` from the legacy
      `rescan_sports_manifest.py` (per the recon script docstring). These are the canonical "schema violation" phantoms
      the recon script was written to detect. All flipped at the single 2026-04-29T13:05:57 UTC sweep. **Comparison
      rows:** 4,984 footystats rows have empty league_id AND `capture_status=captured` — these are at a different
      (newer-layout) parquet path which the recon script CAN find via `candidate_parquet_paths` SSOT, so they don't get
      flipped. Conclusion: the empty-league_id phantoms are real artefacts of the legacy rescan, not a current pipeline
      bug.
- [x] [AGENT] P0. Pull the 13 `RuntimeError` rows' actual exceptions. **Root cause identified**: GCS API rate-limit
      (HTTP 429) on the `central-element-323112-events` bucket. Both fs VMs flooded GCS Pub/Sub-events writes faster
      than the bucket's per-second limit. Trace from `fs-backfill-20260501-014139`:
      `application error in instruments-service.footystats_matches_fetch: HTTP 429 from https://api.football-data-api.com/todays-matches after 10 attempts (recovery=fail_fast)`
      — i.e. the FootyStats API itself returned 429s 10 times in a row, the adapter exhausted its retry budget, raised
      RuntimeError, the row recorded as `attempted_failed`. Distinct from the 478 `TooManyRequests` rows which are the
      same condition but caught earlier by the venue error classifier. Both buckets need the same fix: longer backoff or
      a singleton-lock on FootyStats VMs (per the workspace rule on rate-limited adapters).
- [x] [AGENT] P1. TooManyRequests distribution check. Footystats: 478 rows spread across 2018-08 → 2026-05, max 2 per
      date in the top 15 dates — confirmed thin spread, transient. SFI: 4 rows. No quota-exhaustion clusters.

### Phase 0.4 — `[FLAG-FOR-PHASE-0-OWNER]` View Schema modal broken for cefi/tradfi/defi/prediction (instruments)

Investigation 2026-05-01: User reported "schema is showing up for most of the sports instruments but not for any other;
for defi I don't even see the schema button in instruments; for cefi and tradfi I see the button but it's not showing
the schema."

**Root cause:** instruments-service writes manifest rows for cefi/tradfi/defi at `schema_version=4` with empty
`instrument_type` and empty `data_type` columns (rows are keyed by `(venue, date)` only — see manifest snapshots
2026-05-01 18:14 UTC). The `lookup_contract` call in
[`get_schema_for_shard`](deployment-api/deployment_api/services/data_status_drilldown.py#L342) hits the UAC
SchemaContract registry keyed on `(asset_group, instrument_type, data_type)` and raises `SchemaContractNotFoundError`.
Old fallback path returned `{registered: False, columns: []}` with no projection — UI rendered blank modal.

Sports works because instruments-service writes sports rows at `schema_version=6` with populated `instrument_type`
(`EXCHANGE_ODDS` etc.) + `data_type` (`INJURIES` etc.) and the registry has matching contracts.

Prediction is half-migrated — `data_type` column populated with sub-categories (BTC/ETH/FOOTBALL/OTHER) but
`instrument_type` empty. Same fallback to "no contract" applies.

**Quick fix shipped (2026-05-01) — `[REVIEW-NEEDED]`:**

- [ ] [HUMAN] P0. Review and merge: `deployment-api` changes to
      [`get_schema_for_shard`](deployment-api/deployment_api/services/data_status_drilldown.py#L342) +
      [`/schema` route](deployment-api/deployment_api/routes/data_status.py#L569). New behaviour: when no contract is
      registered, project actual parquet column names from a sample shard via the new
      `_project_columns_from_sample_parquet` helper. Returns
      `{source: "PARQUET_PROJECTION", columns: [...],     sample_uri: ...}`. Cheap (parquet footer only, no row read).
      Falls back to the original empty response when no sample exists or projection fails. - Backwards compat: existing
      `(asset_group, instrument_type, data_type, venue)` callers unaffected (new params are optional kwargs). - Tests
      added: `test_unregistered_falls_back_to_parquet_projection`,
      `test_unregistered_without_service_context_returns_empty`. All 8 schema tests pass; ruff clean. - UI side: needs
      to send `service` and `day` query params in the existing `/schema` request (already in the UI's shard-detail
      context). Without those, behaviour is unchanged.
- [ ] [HUMAN] P1. Decide whether to do the proper fix in addition to the quick fix:
  1. Register a per-asset-group `instrument_catalogue` SchemaContract in
     [`unified-api-contracts/.../contracts.py`](../../../unified-api-contracts/unified_api_contracts/internal/schemas/contracts.py)
     keyed by `(asset_group, "instrument_catalogue", "instrument_catalogue")` for cefi/tradfi/defi/prediction. Source of
     column list: instruments-service `reference_data/schemas.py` Pydantic models. Quick fix gives you the same visible
     columns; the proper fix gives you typed dtypes + descriptions + nullability.
  2. Re-scan the cefi/tradfi/defi/prediction manifests to populate `instrument_type` + `data_type` (manifest v5
     migration that was done for sports). Bigger lift — separate plan.

### Phase 0.5 — Critical findings to flag now (added 2026-05-01)

- [ ] [HUMAN] P0. **SFI_STANDINGS is 100% failed (42/42 rows).** All flipped to phantom on 2026-04-29; ALL have empty
      `league_id`; `written_at` ranges 2026-04-14 → 2026-04-29 from the legacy rescan; covers dates 2020-04-24 →
      2026-04-14. The currently-running `sfi-backfill-20260501-102703` VM may or may not be writing this data type —
      check what data_types its CLI invocation covers. If SFI_STANDINGS is in scope but still failing after the VM
      finishes, the SFI adapter for the standings endpoint is broken. If out of scope, we need a separate launch.
- [ ] [HUMAN] P0. **`written_at` for `open-meteo` is 2026-04-29 13:22 UTC** — has not written anything in 2 days. All
      other sources wrote in the last hour. Possible no open-meteo VM has been launched recently. Confirm whether this
      is in scope for the current epic; weather endpoint is rarely-changing reference data so might be intentional.
- [ ] [HUMAN] P0. **api-football date range starts 2015-01-01** — but
      `SOURCE_COVERAGE_START['api_football'] = 2018-01-01` per UAC SSOT. Either the cutoff is being violated (fetching
      pre-2018 dates that will never have data) or there are legacy rows in the manifest pre-cutoff. Confirm whether
      2015-2017 rows are all `empty_confirmed` (legitimate "tried anyway") or contain captured data (would indicate
      deeper provider history than UAC declares).
- [ ] [HUMAN] P0. **understat date range starts 2014-01-01** — UAC declares `understat=2015-01-16`. Same issue as
      api-football — 2014 → 2015-01-15 rows shouldn't exist if cutoff is enforced. Probably 1 year of unnecessary
      `empty_confirmed` rows in the denominator.

### Phase 1 — Wait for non-fs VMs, then flip phantoms cleanly

Phantom flip races with the consolidator. Don't run until either (a) all sports VMs are done AND consolidator paused, or
(b) recon script has lock acquisition fix.

- [ ] [HUMAN] P0. Wait for `af-backfill-test-20260501-095`, `sfi-backfill-20260501-102703`,
      `tm-backfill-20260501-102707` to exit. Verify with
      `gcloud compute instances list --filter='name~"^(af|tm|sfi|fs)-"' --format='table(name,status,zone)'`.
- [ ] [AGENT] P1. Decide between:
  1. Patch `reconcile_phantom_manifest_rows.py` to acquire the same sentinel-lock the consolidator uses (or use
     `if_generation_match` on upload). Pre-audit: search workspace for other writers to canonical
     `_index/availability_index.parquet`.
  2. Operational workaround — stop the consolidator daemon, run recon, restart consolidator. Documented in
     [vm-tarball-deployment.md § Manifest consolidator daemon](../../codex/05-infrastructure/vm-tarball-deployment.md).
- [ ] [HUMAN] P0. Run real recon (scoped to footystats first):
      `     cd instruments-service     .venv/bin/python scripts/reconcile_phantom_manifest_rows.py \       --data-types MATCHES,PREDICTIONS,ODDS     `
      Re-run with `--dry-run` afterwards; should report 0 phantom flips (idempotent).

### Phase 2 — Targeted relaunch for residual real failures

After Phase 1, residual `attempted_failed` rows are real (not phantoms). Relaunch fs scoped to the affected (date,
league) pairs.

- [ ] [AGENT] P1. Build the residual list — query manifest for
      `(data_type, capture_status='attempted_failed', error_reason ∈ {TooManyRequests, RuntimeError, ...})` after recon.
      Group by date and league.
- [ ] [HUMAN] P1. Relaunch fs scoped to residual dates with `--force`. Pass dates as a comma-separated list or a
      date-range narrowed enough that the run is short (under 1 hour).
- [ ] [AGENT] P1. Verify post-relaunch: re-snapshot manifest, footystats `attempted_failed` should be near zero.
      Anything left after a second relaunch is a real source-side gap that the venue/source confirms doesn't exist —
      worth a separate finding.

### Phase 3 — Generalise to other sports sources

After footystats lands, repeat the same triage on api-football, transfermarkt, soccer_football_info once their VMs
finish. Each source has its own data_types; reuse the breakdown query.

- [ ] [AGENT] P2. Repeat Phase 0 dry-run + breakdown for api-football data types (`FIXTURES`, `FIXTURE_EVENTS`,
      `FIXTURE_LINEUPS`, `FIXTURE_STATS`, `INJURIES`, `LEAGUES`, `STANDINGS`, `TEAMS`, `VENUES`, `WEATHER`, `XG`,
      `PLAYER_STATS`).
- [ ] [AGENT] P2. Same for transfermarkt (`PLAYER_VALUES`, `TRANSFERMARKT_LEAGUES`).
- [ ] [AGENT] P2. Same for sfi (`SFI_LEAGUES`, `SFI_PROGRESSIVE_STATS`, `SFI_STANDINGS`).
- [ ] [AGENT] P2. Roll the per-source findings up into the parent epic plan
      `instruments_and_market_tick_data_completion_2026_05_01.md` Phase 1 verification.

## Success criteria

- B3 (Data pipeline KPI — completeness ≥ 99.9%): Footystats `captured + empty_confirmed` ≥ 99.9% under the
  secondary-cutoff denominator (excluding `attempted_failed` for legitimate non-source-side reasons).
- Zero residual phantoms after recon (idempotent dry-run reports 0 flips).
- Residual `attempted_failed` rows have a documented per-row reason (genuine source-side gap, source-API outage with
  date evidence, or known issue ticket).
- Recon script either has concurrency-safe write OR a documented procedure for "safe to run when".

## Out of scope

- Phase 0 deployment-ui drilldown work (handled by separate workstream — drilldown will reflect these manifest changes
  automatically once it's available).
- Re-fetching footystats data older than 2019-01-01 (`SOURCE_COVERAGE_START['footystats'] = 2019-01-01` per UAC SSOT —
  pre-2019 dates must stay `empty_confirmed` per cutoff).
- VIX futures, mbp_10, and other deferred items from the parent epic plan.
- Architectural decision on `ODDS_LIVE` vs `ODDS_HIST` split (see
  [sports-data-source-coverage-matrix.md §4](../../codex/02-data/sports-data-source-coverage-matrix.md)) — design
  question, not data-quality work.
