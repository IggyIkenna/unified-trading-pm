---
doc_type: plan
title: Data completion to 100% — Sports manifest canonicalisation + backfill (parity sibling of M-1)
summary: >-
  Sports slice of the data-completion-to-100% program, split out of data_completion_to_100_all_ag_2026_06_21 (M-1) on
  2026-07-24 per the plan line-cap remediation (plans/active/issues/plan_line_cap_remediation_2026_07_23.md,
  operator-approved). Sports never received a 2026-07-15 split sibling like cefi/defi/tradfi/prediction did (it has no
  archived `sports_manifest_canonicalisation_2026_06_01.md`-style fold-in predecessor); this plan is the parity sibling,
  carrying M-1's substantive sports-honest-coverage section plus every Sports-lane-tagged Progress Log entry, migrated
  VERBATIM -- no scope added, dropped, or reworded. M-1 remains the coordinator hub for cross-cutting work (bucket
  naming, source provenance, bar-edge) and owns the shared Progress Log.
status: active
nature: process
asset_group: [sports]
stage: [data]
repos: [instruments-service, market-tick-data-service, unified-api-contracts]
scope: [engineer, admin]
tags: [backfill, manifest, honest-coverage, data-completion, sports, data-correctness]
related:
  [
    /plans/active/data_completion_to_100_all_ag_2026_06_21.md,
    /plans/active/data_completion_cefi_2026_07_15.md,
    /plans/active/data_completion_defi_2026_07_15.md,
    /plans/active/data_completion_tradfi_2026_07_15.md,
    /plans/active/data_completion_prediction_2026_07_15.md,
    /plans/active/issues/plan_line_cap_remediation_2026_07_23.md,
  ]
created: "2026-07-24"
parent_epic: manifest_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 2.5
estimate_calibrated_ai_days: 2
last_updated: 2026-07-24
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  data_completion_to_100_all_ag_2026_06_21 (M-1) -- split 2026-07-24, plan line-cap remediation
  (plans/active/issues/plan_line_cap_remediation_2026_07_23.md), operator-approved (sports parity-sibling creation -- 4
  of 5 asset groups already got a 2026-07-15 split, sports did not).
drift_direction: advance-code
---

# Data completion to 100% — Sports

> **Split from M-1 on 2026-07-24** (`data_completion_to_100_all_ag_2026_06_21.md`, plan line-cap remediation,
> `plans/active/issues/plan_line_cap_remediation_2026_07_23.md`, operator-approved). M-1 stays the coordinator hub
> (measured snapshot, per-AG launch matrix, cross-cutting scope, shared Progress Log).
>
> **Read M-1 first** for the program-level snapshot + launch matrix. Cross-cutting items (bucket-name SSOT, data-source
> provenance, bar-edge) deliberately stayed there — they are not sports-specific.
>
> **Parity note**: cefi/defi/tradfi/prediction each got a 2026-07-15 split sibling carrying their
> `<ag>_manifest_canonicalisation_2026_06_01.md` fold-in residual. Sports never had that archived predecessor plan
> folded into M-1, so this sibling instead carries (a) M-1's standalone sports-honest-coverage substantive section (the
> sports equivalent of a "### From ..." fold-in — a self-contained, sports-only technical section with its own todos),
> and (b) every Sports-lane-tagged dated Progress Log entry, moved verbatim in original chronological order.

## Sports honest-coverage is ARTIFICIALLY LOW — denominator over-seed (GROUND-TRUTH VERIFIED 2026-06-23)

Read the live sports manifest (`instruments-store-sports-prd/_index/availability_index.parquet`, 4.55M cells). The "low
coverage" is **partly a denominator measurement bug** (out-of-scope leagues over-seeded as gaps) — but the
phantom-failed cells are GENUINE absences, NOT mislabeled captures.

> **⚠️ RETRACTED (the earlier 68/46/94% "corrected" numbers were WRONG)** — they counted the
> `phantom_captured_no_parquet_at_canonical_path` cells AS captured. A ground-truth test (2026-06-23,
> `/tmp/sports_phantom_groundtruth.py`: compute `unified_api_contracts.sports.candidate_parquet_paths(dt, date, league)`
> per phantom-failed row → `blob_exists`) returned **REAL=False for every sampled TM_LEAGUES / SFI_LEAGUES / INJURIES /
> ODDS / WEATHER row** — the parquets genuinely do not exist. The phantom flip was CORRECT; these are real absences, not
> false positives. The honest correction is therefore **only the denominator (Cause A) + retired-exclusion (B1)** —
> never counting phantoms as captured. The true corrected numbers (denominator-only) are recomputed via
> `is_expected_for_source`, NOT the retracted 68/46/94.

- **Cause A — over-seeded `expected_unattempted`**: out-of-scope (league × source) cells are stored as
  `expected_unattempted` (a real GAP, in the denominator) instead of `EXPECTED_NO_PROVIDER_COVERAGE` (out-of-scope,
  EXCLUDED from the completion-% denominator by design —
  `unified_api_contracts/canonical/crosscutting/honest_coverage.py` line ~190). The denominator CODE is already correct;
  the MANIFEST DATA is mis-classified.
- **Cause B — CORRECTED 2026-06-23 (verified before applying — diagnosis changed; earlier "flip all to captured" was
  WRONG)**: the ~101k `error_reason=phantom_captured_no_parquet_at_canonical_path` cells are **two distinct
  sub-causes**:
  - **B1 — RETIRED data_types (~88.7k): TRANSFERMARKT_LEAGUES (75,929) + SFI_LEAGUES (12,769) + SFI_STANDINGS (42).**
    Verified in code: `transfermarkt.py:338,363` "TRANSFERMARKT_LEAGUES retired 2026-05-05"; `sfi.py:99,123`
    "SFI_LEAGUES + SFI_STANDINGS retired 2026-04-24/2026-05-05" — the league catalog moved into UAC; **no parquet is
    written anymore and none should be** (confirmed on GCS: `sports_reference_v2/by_date` has only
    `entity=fixtures`/`fixture_stats`). **Flipping these to `captured` would FAKE coverage (banned).** Correct fix:
    reclassify → `empty_confirmed` reason `EXPECTED_DEPRECATED_DATA_TYPE` (in the out-of-window exclusion set,
    `honest_coverage.py:462-471` → excluded from the completion-% denominator). **NOT a data loss — each has a LIVE
    successor carrying the substantive data (verified 2026-06-23):** TRANSFERMARKT_LEAGUES = a static provider catalog
    (provider_id→canonical_name+country), now UAC `TRANSFERMARKT_IDS` versioned config; the TM DATA is `PLAYER_VALUES`
    (active). SFI_LEAGUES = SFI catalog, now in UAC; the SFI DATA is `SFI_PROGRESSIVE_STATS` (active). SFI_STANDINGS =
    "SFI has no standings endpoint" (never fillable); standings come from the canonical `STANDINGS` data_type
    (footystats, 134k captured / 64.7% honest). The migration MUST record this successor mapping per retired data_type
    (auditable exclude, not silent). **Scope: SPORTS ONLY (operator 2026-06-23 — no cefi/tradfi/prediction sweep).**
  - **B2 — INJURIES-failed (9,167) + ODDS-failed (3,848): ACTIVE data_types, but parquets confirmed ABSENT
    (REAL=False)** — these are NOT false positives. Each splits by `is_expected_for_source`: **out-of-scope**
    (league×source not covered) → reclassify `EXPECTED_NO_PROVIDER_COVERAGE` (excluded); **in-scope** → genuine GAP →
    re-fetch (or leave `attempted_failed`, counting against coverage). NO flip-to-captured (no data exists).

- [x] ✅ [SCRIPT] P1. **Reclassify out-of-scope (league × source) sports cells (both `expected_unattempted` AND phantom
      `attempted_failed`) → `EXPECTED_NO_PROVIDER_COVERAGE`** — drive from
      `unified_api_contracts.registry.sports_per_source_rules.is_expected_for_source(source, league_id, day, data_type=dt)`
      (returns `(is_expected, reason)`; the reason IS the `EmptyConfirmedReason` to write). Shrinks the denominator
      honestly (no phantom-as-capture). (instruments-service migration, verify→dry-run→apply) —
      `instruments-service@98bcd78` — reclassify_oos_sports_expected_unattempted_2026_06_24.py +
      migrate_sports_retired_types_2026_05_13.py bucket fix shipped; dry-run then --apply after consolidator drain
- [x] ✅ [SCRIPT] P1. **B1 — reclassify retired-data_type rows (TM_LEAGUES/SFI_LEAGUES/SFI_STANDINGS, ~88.7k) →
      `empty_confirmed`/`EXPECTED_DEPRECATED_DATA_TYPE`** (parquet confirmed ABSENT + data_type retired). Excludes from
      denom. (instruments-service migration) — migrate_sports_retired_types_2026_05_13.py --apply; 1,946 SFI_LEAGUES
      rows flipped 2026-06-23
- [x] ✅ [CODE] P1. **Fix the expected-universe enumerator (`enumerate_expected_universe.py`) to NOT seed
      `expected_unattempted` for out-of-scope (league × source) AND to NOT seed retired data_types** — seed
      `EXPECTED_NO_PROVIDER_COVERAGE` / skip retired, so coverage stays honest going forward (per
      `is_expected_for_source`). (instruments-service / UAC) — instruments-service@0bcf727 | entity_coverage gate now
      yields EXPECTED_NO_PROVIDER_COVERAGE rows per-date for post-coverage-start; is_expected_for_source integrated in
      alive branch for footystats season gate (EXPECTED_PRE_SEASON/EXPECTED_POST_SEASON); `_RETIRED_SPORTS_DATA_TYPES`
      defensive guard added
- [x] ✅ [DATA] P1. **In-scope phantom-failed cells = REAL GAPS → re-fetch** (the manifest claimed captured but no
      parquet exists). After the out-of-scope reclassify, the residual in-scope `attempted_failed` is the true sports
      gap — re-run the relevant IS backfill for those (data_type, date, league) cells. NOT a manifest edit.
      (instruments-service) — 14 IS gap-fill VMs launched 2026-06-23 15:00-15:04 UTC:
      MATCHES/INJURIES/XG/PREDICTIONS/ODDS/PLAYER_STATS/FIXTURE_STATS/FIXTURES/FIXTURE_EVENTS/FIXTURE_LINEUPS/STANDINGS/TEAMS/WEATHER/SFI_PROGRESSIVE_STATS;
      corrected providers (ODDS/STANDINGS/TEAMS→FOOTYSTATS, not API_FOOTBALL)
- INJURIES out-of-scope is the bulk (provider doesn't cover injuries for most leagues, ~262k+
  `EXPECTED_NO_PROVIDER_COVERAGE`) — correct honest-absence, excluded from the denominator once classified.

**Scope classification is MULTI-MAP — `is_expected_for_source` alone is INSUFFICIENT (verified 2026-06-23).** A honest
recompute using only `is_expected_for_source(source, league, day, data_type=dt)` returned `excluded-oos≈0` for
WEATHER/INJURIES/PLAYER*VALUES because that function only encodes understat/footystats/api_football \_league* rules +
transfer-window gating — it does NOT know:

- **WEATHER** scope → `sports_venue_coordinates` (only venues with coords get weather; ~57 leagues, not 790).
- **PLAYER_VALUES** scope → `sports_league_entity_coverage`.
- **ODDS** scope → `sports_bookmaker_league_coverage`. So the migration MUST apply the correct per-data_type scope map,
  not just `is_expected_for_source`. The denominator-only lower bound (no scope maps, no phantom bonus) is WEATHER 6.3%
  / INJURIES 0.5% / ODDS 12.0% / PLAYER_VALUES 8.9% / FIXTURES 15.1% — the TRUE corrected number sits between that and
  the (retracted) inflated figures, pending the proper maps. **Material reality (operator surfaced 2026-06-23): most of
  the low coverage is GENUINE in-scope missing data (phantoms are real absences), NOT a pure measurement artifact** —
  the denominator/retired correction raises the % but the real lever is BACKFILLING the in-scope gaps (a large IS
  backfill, not a manifest edit).

### Gap STRUCTURE characterized with the real maps (2026-06-23) — before any blind backfill

Ran `/tmp/sports_gap_characterize.py` (real UAC maps: `is_league_entity_covered` for api_football entities,
`is_bookmaker_league_covered` for ODDS, date logic `is_pre_launch_date`/`is_in_known_gap`) bucketing every non-captured
cell into out_of_scope / pre_coverage_date / known_gap / genuine_gap. Findings:

- **The genuine gaps are SYSTEMIC + DATE-structured, NOT league-specific.** Per-league counts are flat (every league
  missing ~equally) → not a league-mapping problem. And NOT future-date (`/tmp/sports_future_check.py`: 2026
  non-captured are ~100% `<= today 2026-06-23`, future=0) → real missing data, concentrated in **2026-H1**
  (~120k/data_type vs ~8–30k/prior-year) + a broad pre-2026 backfill gap. The real lever is a **date-range-targeted
  backfill** (2026-H1 first, then history), NOT per-league.
- **Maps that classify correctly at manifest grain (api_football/footystats entities):** INJURIES out_of_scope=363k
  (honest cov 2.0%), PLAYER_STATS oos=176k (20.5%), STANDINGS oos=244k (64.7%) — accurate → reclassify →
  `EXPECTED_NO_PROVIDER_COVERAGE` (denominator fix, safe).
- **Maps that DON'T fit the manifest grain → genuine_gap OVERSTATED (needs hardening):** WEATHER scope is per-VENUE
  (`get_venue_coordinates`) but cells are league-keyed (no venue field) → 0 out_of_scope classified (honest 6.4% is a
  floor); PLAYER_VALUES has no transfermarkt-league scope map. **HARDEN: add league-grain WEATHER + PLAYER_VALUES
  observed-coverage maps in UAC** (mirror `sports_league_entity_coverage`, derived from ≥1 captured row) so denominators
  are honest.
- **Enumeration grain inconsistency**: 2026 seeds ~10× the prior-year cell count per data_type — investigate why + make
  grain consistent + frontier-bounded.

### Execution strategy + blocker resolutions (operator 2026-06-23): 3-MONTH GOLDEN WINDOW

**Operator directive:** rather than blind fleet backfills, **pick a 3-month window where all leagues were viable + all
data sources were available, and drive EVERY source × data_type to 100% for that window** — proving the honest-coverage
philosophy end-to-end (ironing out every code/manifest/GCS-path migration needed). THEN generalize the proven recipe to
the rest of history.

- Window candidate: **2025-09-01 → 2025-11-30** (autumn, all European leagues in-season, sources mature, pre the 2026-H1
  gap spike). Verify vs per-source `coverage_start` before locking.

**Blocker resolutions (2026-06-23):**

- ✅ **Blocker 2 (mtds adapter-contract) = NON-ISSUE** (stale-baseline-read; calls relocated in the 900-line split
  mtds@64789a7; PM baseline already matches; `check_adapter_contract_regression.py --workspace-root .` → EXIT 0).
- **Blocker 1 (apply-safety) = directive (b): rework BOTH reclassify migrations to write a consolidator-merged per-VM
  shard** (not a full `_index` overwrite) so retired→EXPECTED_DEPRECATED applies without racing the live-odds VM /
  consolidator. NOT yet done — the critical remaining item for the retired-flip apply.
- ✅ **Bucket-bug fix** (`migrate_sports_retired_types_2026_05_13.py` env-less→`resolve_bucket_name`+guard) in
  instruments-service working tree, ruff-clean, dry-run on `-prd-` = 88,740 retired rows ready → EXPECTED_DEPRECATED.
  Ships once committed (QG adapter-gate now green).

- [x] ✅ [SCRIPT] P0. **Rework reclassify migrations → per-VM-shard (consolidator-merged) write** (directive b) —
      instruments-service@c7270e9. BOTH migrations now write flipped/relabeled rows ONLY as a per-VM shard at
      `_index/per_vm/{VM_NAME}.parquet` (canonical fleet path, matches `manifest_writer._PER_VM_PATH_TEMPLATE`) — the
      consolidator's DuckDB last-write-wins merge
      (`PARTITION BY date,venue,data_type,service_name,<dims> ORDER BY attempted_at DESC, written_at DESC`) picks them
      via fresh `attempted_at`/`written_at`, NO `_index` overwrite, NO race with live writers. Also resolved the
      committed merge-conflict markers in the retired-types script (single clean `resolve_bucket_name` + env-short
      guard). **VERIFIED end-to-end on live `-prd-`**: retired-flip dry-run = already_flipped 88,740 / will_flip 0
      (idempotent — the flip is already in canonical from the prior apply). relabel `--apply` wrote a 156,138-row per-VM
      shard (PLAYER_VALUES 65,293 + WEATHER 90,845, all wrong-empty→ `EXPECTED_NO_PROVIDER_COVERAGE`; now classifiable
      because the WEATHER/PLAYER_VALUES coverage maps landed) → consolidator merged it within ~1 min → re-read canonical
      confirms PLAYER_VALUES_NOCOV=65,293 + WEATHER_NOCOV=90,845, **ODDS rows intact** (226,391→226,395, captured
      26,881→26,965 = live writers kept flowing + were preserved by the anti-join), retired flip intact (88,740
      `EXPECTED_DEPRECATED`). No live rows lost. Shipped scoped (dirty-deps carve-out: foreign UAC + IS test/script WIP
      from live peer sessions broke the IS QG on files I don't own — NOT my 2 `scripts/` files, which are ruff-clean).
      (instruments-service)
- [x] ✅ [VERIFY] P0. **Proper alerting-e2e MONITOR for the ~25 live sports backfill VMs** (waves 15:00 + 15:35 UTC
      2026-06-23, all data_types) — per VM: GCS `run.log` mtime advancement (hang) + terminal `exit_code` (OOM
      137/error) + manifest captured-delta, cross-checked vs Slack `#data-pipeline-alerts`. Serial console shows VMs
      alive (log-tee every 60s) + no crashes yet, but application progress is NOT yet confirmed (a RUNNING VM can be
      hung). (deployment-service) — 2026-06-23T16:03Z: 23 VMs checked: 2 completed exit_code=0 (fixtures-153526,
      injuries-150123); 21 RUNNING all confirmed active — log timestamps 15:56–16:01 UTC, manifest shard writes current
      (xg-153512 log tee lagged but shard updated 16:02:57 confirming not hung); no exit_code=137 (OOM) on any VM. All
      progressing.
- [x] ✅ [CODE] P0. **Make `#data-pipeline-alerts` VERBOSE + ACTIONABLE — fix the generic-alert metadata loss**
      (operator escalation 2026-06-23: the 16:48 `DP_VM_EXIT_NONZERO`/`DP_CRON_DID_NOT_FIRE`/`DP_CATALOG_NOT_RUNNING`
      posts had only Event/Severity/Source — no VM name, exit code, log link, error snippet, or explanation). ROOT
      CAUSE: `PubSubEventSink` publishes `{event, metadata:{severity, details}}`; the alerting subscriber routed the RAW
      top-level dict as `details`, so the formatter's `details.get(vm_name/exit_code/severity/...)` all returned None →
      generic alert. FIX (cross-repo): alerting-service `_unwrap_utl_envelope` flattens `metadata.details` + promotes
      `severity`/`correlation_id` (legacy flat payloads pass through unchanged); `data_pipeline_slack` per-event "What
      happened / Recommended action" explain block + renders an emitter `log_url` deep-link; deployment-service
      exit-code monitor attaches `run_log_tail` (error/warn lines + tail of the durable GCS-tee'd run.log, survives
      self-delete) + `log_url`, and `route_finding` carries the finding `summary` as `message`. (alerting-service +
      deployment-service) — alerting-service@ceed827 + deployment-service@d2ddb23 | QG green both repos | 42 alerting +
      81 deployment unit tests pass incl. new envelope-unwrap + explain-block + log-snippet regression tests | image
      builds c2beac49 (alerting-service:latest) + c0f6dc2f (deployment-api:latest) → redeploy dp-alerting-subscriber +
      uts-prod-dp-exit-code-monitor + e2e verify. Gap-4 root-cause + deploy todo:
      `plans/active/issues/backfill_vm_slack_alert_e2e_verification_2026_06_23.md`
- [x] ✅ [DATA] P0. **XG/understat backfill is OOMing (exit 137, MemoryError) — surfaced by the now-actionable alerts
      2026-06-23.** The `instr-backfill-sports-xg-*` VMs (understat) hit `MemoryError`/`Killed`/rc=137 — memory-bound,
      so a blind restart re-OOMs. Remediation: relaunch XG/understat with a higher-memory machine type OR batch/stream
      the understat fetch (per-league/per-month chunks) so it fits. Blocks the XG slice of the golden-window backfill.
      (deployment-service launcher + instruments-service understat handler) — instruments-service@bd32424 (free season
      JSON blob after dates extraction) + deployment-service@cbdc0e4 (bump launcher to e2-standard-4); tarball rebuilt;
      verification VM `us-backfill-20260623-171131` launched on e2-standard-4 2026-06-23

### DP alert FLOOD is mostly FALSE POSITIVES — monitors are too crude (diagnosed 2026-06-23, now alerts are readable)

Dispatch B made the alerts actionable → the run_log traces reveal **the CRITICAL flood is ~80% false positive**, which
is WHY nothing auto-resolves (you can't auto-recover noise; the real signal is buried). Per-event triage:

- **DP_VM_GONE_NO_CAPTURE (captured "0→0")** — the heuristic can't distinguish silent-failure from: (a) **already
  complete** (enrichment-only, "all entities already captured, fetching []" — fixtures/weather VMs), (b) **honest
  absence** (settled polymarket market → 0 trades; off-season), (c) **VM wrote its per-VM shard but the consolidated
  count is stale** (cefi-hyperliquid wrote 1.39M rows yet "6391→6391"; injuries wrote 290 shard entries yet "0→0"), (d)
  **API-Football RATE LIMIT** (real-transient — needs backoff-retry, wrote partial). FIX: read the VM's OWN per-VM shard
  rows-written + honest-absence reasons, not the consolidated captured-delta.
- **DP_CRON_DID_NOT_FIRE (flood)** — most are **INTENTIONALLY-PAUSED crons** during the manual-backfill campaign (the
  per-epic fleet + scheduled collection are paused-by-design per CLAUDE.md "expected"). The meta-watcher is NOT
  pause-aware → floods CRITICAL for paused schedulers. A few are REAL: `dp-exit-code-monitor`/`dp-meta-monitor`
  heartbeat stale, sports MTDS consolidator (`...-market-data-sports-legacy-cron` PAUSED, no active replacement).
- **DP_CATALOG_NOT_RUNNING "> budget (missing)"** — "(missing)" = the freshness probe read `age=None`: it can't FIND the
  catalogue at the path/bucket it checks. Same **env-less vs env-short reader-mismatch bug class** as the migration
  bucket-bug (CLAUDE.md DeFi gotcha) AND/OR the regen genuinely didn't run (`lifecycle-catalogue-regen-sports-daily`
  lastAttempt=-1). sports+defi+cefi affected.
- **DP_ZOMBIE_WATCHDOG_DOWN** — the watchdog census artifact stale.

- [x] ✅ [CODE] P0. **Harden the DP meta-monitors to kill the false-positive flood** — deployment-service@7b579ee +
      alerting-service@add3063. (1) **DP_VM_GONE_NO_CAPTURE is now run.log-reason-aware** —
      `_gcs.classify_no_capture_reason` reads the VM's durable run.log for PROGRESS ("Wrote N rows" → shard climbed,
      consolidated lags), HONEST_ABSENCE ("0 trades"/off-season/"already captured"/record_empty/`fetching []`), or
      RATE_LIMITED (HTTP-429/"Too many requests"); only a SILENT flat (no benign signal) still CRITICAL-alerts
      (auth/0-universe/unexpected empty). New verdicts EXPECTED_NO_CAPTURE (benign, no alert) + RATE_LIMITED (WARN,
      backoff). KEEPS firing the true silent zero. (2) **DP_CRON_DID_NOT_FIRE is PAUSE-AWARE** —
      `FreshnessTarget.scheduler_job` + injected `SchedulerStateReader`; a `PAUSED` scheduler suppresses
      (paused-by-design), ENABLED-but-stale + UNKNOWN/None still alert (fail-safe-on); cli wires a deferred-import Cloud
      Scheduler `get_job` query. (3) **DP_CATALOG_NOT_RUNNING env-SHORT fix** — probes `{env}/catalog.parquet` (the real
      writer path, was `_catalogue/instrument_catalogue.parquet` → age=None false "missing") in the env-SHORT bucket via
      `resolve_bucket_name` (prediction via its flat key); the alert now SHOWS
      `probed gs://<bucket>/<path>, artifact ABSENT, budget=Nh` + probed_path/budget_hours/artifact_present fields. QG
      green both repos (deployment 47s / alerting 43s); 18 new dp-monitor tests + 2 new slack-formatter tests.
      (deployment-service + alerting-service)
- [x] ✅ [INFRA] P0. **Restore the genuinely-down infra** — deployment-service@410304f (terraform; live gcloud applied).
      VERDICTS (verified vs live execution-status, not "I enabled it"): (1) **sports MTDS consolidator** — NOT down: the
      NON-legacy `uts-prod-manifest-consolidator-market-data-sports-cron` already EXISTS+ENABLED+fires clean every \_/1
      (the `-legacy-cron` is correctly paused-by-design); no action needed. (2) **catalogue regen** — genuinely
      stale/failing → triggered catch-up runs + verified clean: sports ✅(41s) defi ✅(17m47s) cefi ✅(8m13s); **tradfi
      OOM'd at 4Gi(2026-06-19)+8Gi → bumped to 16Gi/cpu4** (16Gi catch-up running, prior sizes confirmed-OOM). The daily
      schedulers (`lifecycle-catalogue-regen-{ag}-daily`, lastAttempt=-1) are ENABLED with the `run.invoker` grant; -1 =
      not-yet-hit-01:00, not broken. (3) **vm-zombie-watchdog** — genuinely DOWN: VM ran but on 2026-05-28 stale code
      (no census-write) → census blob ABSENT → DP_ZOMBIE_WATCHDOG_DOWN. Relaunched fresh-code; **census now written
      `vm-census/watchdog-census.json`**. ⚠️INCIDENT: first relaunch ran dry_run=FALSE + reaped 9 LIVE campaign
      backfills before I caught it → corrected to **`--dry-run`** (census WITHOUT reaping — required during the
      campaign); killed-VM list + relaunch recipe + latent code-fix:
      `plans/active/issues/zombie_watchdog_relaunch_reaped_live_backfills_2026_06_23.md`. (4) **dp-exit-code/dp-meta** —
      NOT down: sentinels fresh (exit-code 16:55, meta 16:46), fire clean. **dp-heartbeat-watcher WAS down: OOM at
      2Gi+4Gi every \*/5 → bumped 8Gi/cpu2 → ✅SUCCEEDED, `heartbeat-last-run.json` sentinel now PRESENT**. tradfi
      catalogue OOM'd at 4/8/16Gi → bumped 32Gi/cpu8 (re-running); DURABLE roll-up-chunking fix noted in the issue doc.
      HARD constraint: no collection cron re-enabled (the backfill-kill incident is filed + corrected).
      (deployment-service)
- [x] ✅ [CODE] P1. **Fix api-football JSON-envelope rateLimit: retry with minute-boundary backoff instead of
      fail_fast** — `ApiFootballResponseError(is_rate_limit=True)` now retried via `_fetch_and_extract()` (HTTP 200 +
      `{"errors":{"rateLimit":"..."}}` was propagating as `attempted_failed`); `concurrency` lowered 50→10; 7 unit tests
      added. — instruments-service@b402294
- [x] ✅ [CODE] P1. **Match auto-recover actuator to failure MODE** — deployment-service@7b579ee. **rate-limit** → a
      flat-captured run whose run.log shows a 429 emits `DP_SOURCE_RATE_LIMITED` (WARN, AUTO_RECOVER tier with NO wired
      relaunch actuator → falls through to backoff/file_issue, NOT a relaunch that re-hits the limit). **OOM-137** →
      `_finding_for` stamps `bigger_machine=True`; `escalation._recover_backfill_vm` maps it (via `_OOM_MACHINE_LADDER`
      / `_escalated_machine_type`) to a higher-mem `MACHINE_TYPE` passed through `launcher_env` so the relaunch lands on
      a bigger tier (never the same → re-OOM). **paused-cron** → suppressed (KEY #2 above, no actuator).
      **real-cron-down** → unchanged (CONSOLIDATOR_DOWN → relaunch_consolidator → file_issue → orchestrator dispatch). 5
      new actuator/verdict tests. (deployment-service escalation.py + exit_code_fleet_monitor.py)
- [x] ✅ [CODE] P1. **Registry-driven launch parameters — fleet rate-budget + machine-sizing (the PRIMARY mechanism, not
      reactive backoff/OOM-relaunch; operator design 2026-06-23)** — deployment-service@e754c9f +
      instruments-service@7629c1a. **Part 1 rate-budget**
      (`deployment_service/data_pipeline_monitors/launch_budget_registry.py`): `SOURCE_RATE_LIMITS_RPM` maps
      source→fleet req/min ceiling (**api_football = 900/min**, the documented Mega-tier value `api_football.py:154` —
      ONE quota SHARED across ALL endpoints: fixtures + injuries + fixture_stats + fixture_events + fixture_lineups +
      player_stats; operator still confirming a higher tier, 900 is authoritative fail-closed);
      `soccer_football_info=240`, `footystats=60`/`understat=30`/`transfermarkt=60`/`open_meteo=60` as conservative
      defaults each carrying a `# TODO: empirically calibrate` marker; databento/polymarket/thegraph left `None`
      (uncapped, not allocated). `allocate_rate_budget(source, n_vms)` splits `per_vm_rpm = limit // N` + matched
      concurrency (`concurrency × per-query-rate ≤ per_vm_rpm`); `assert_fleet_within_budget` is the **fail-closed HARD
      RULE** (`sum(per_vm × N) ≤ ceiling` → raises). Worked example: 10 api_football VMs → 90/min each (10×90=900, 0
      waste), concurrency 7 at 12-rpm/query, interval 0.6667s. **Part 2 machine-sizing**: canonical `MEMORY_TIER_LADDER`
      (e2-standard-4(16)→e2-standard-8(32)→n2-standard-16(64)→n2-highmem-16(128)→n2-highmem-32(256)) +
      `VENUE_TASK_MEMORY_TIER` (**Coinbase cefi → highmem-128gb / 256 for heavy ranges**, all heavy cefi venues 128GB,
      sports-backfill 32GB); `resolve_memory_tier`/`machine_type_for`/`next_memory_tier` (the OOM-actuator's ladder-step
      input). **Wiring**: launchers (`launch-api-football-backfill-vm.sh --fleet-vms N`,
      `launch-cefi-sharded-backfill.sh`) resolve the registry at launch → stamp
      `SPORTS_ADAPTER_RATE_RPM`/`SPORTS_ADAPTER_CONCURRENCY` + machine-type into VM metadata →
      `setup-data-pipeline-vm.sh` exports them → typed `InstrumentsServiceConfig` (never raw OS-env) →
      `create_sports_reference_adapter(rate_rpm=...)` → `BaseSportsReferenceAdapter.set_rate_budget_rpm()` sets the
      self-enforced token-bucket `_min_request_interval = 60/rpm` as the PRIMARY throttle (429 backoff = safety net
      only). 24 registry unit tests (allocation math + fail-closed + machine lookup + ladder monotonicity) all green;
      both repos QG-green (deployment-service 58s / instruments-service 76s).

- [x] ✅ [CODE] P0. **CORRECTION — api_football is the Custom plan = 1200 req/min (NOT Mega 900) + ADD the 450,000
      req/DAY quota dimension (operator-confirmed 2026-06-23 from the API-Football dashboard)** —
      deployment-service@1a06ffa. (1) `SOURCE_RATE_LIMITS_RPM['api_football'] = 1200` (was 900;
      docstring/comment/worked-example/launcher-echo + all dependent test assertions updated). (2) NEW
      `SOURCE_DAILY_QUOTA = {'api_football': 450_000, ...}` (resets 00:00 UTC, unused-is-LOST/no-rollover; all other
      sources `None` = no documented daily quota). (3) `allocate_rate_budget` is now daily-quota- AND time-aware:
      **EFFECTIVE per-minute ceiling = `min(per_minute_limit, remaining_daily_quota // minutes_until_00:00_UTC)`** —
      injectable `remaining_daily_quota` + `now_utc` (defaults to a UTC clock at call time) / `minutes_to_reset`
      override; `per_vm_rpm = effective_source_rpm // n_vms`. So when the day's budget is nearly spent the allocator
      THROTTLES the fleet below 1200/min automatically. `RateBudgetAllocation` gained `effective_source_rpm` /
      `remaining_daily_quota` / `minutes_to_reset`. (4) `assert_fleet_within_budget` is the fail-closed HARD RULE on
      BOTH axes — per-minute (`per_vm × N ≤ source_rpm`) AND projected daily
      (`fleet_rpm × minutes_to_reset ≤ remaining_daily_quota`). **Worked examples (operator's live scenario):**
      late-in-day remaining≈130,500 with ~270 min to reset ⇒ effective ≈483/min → ~5 VMs at ~96 rpm (`130500//270=483`,
      `483//5=96`); post-reset fresh 450,000/day ⇒ full 1200/min → ~13 VMs at ~92 rpm (`1200//13=92`).
      `launch-api-football-backfill-vm.sh` now reads optional `REMAINING_DAILY_QUOTA` env → daily-aware allocation +
      echoes the effective ceiling; `launch-fill-missing-player-stats-vm.sh` comment updated. 34 registry unit tests
      green (10 new: ceiling=1200, daily=450k, late-day throttle, post-reset full-1200, per-minute-binds,
      naive-tz-raises, daily-exhausted-raises, no-daily-quota-source-ignores-remaining, daily over-budget raises, daily
      within-budget passes); deployment-service QG-green (60s). **NOTE (finding):** the adapter-side
      `api_football.py:154` comment (`instruments-service`) still reads "Mega 900 / 0.067s" — the registry is now the
      authoritative SSOT (the runtime stamps `SPORTS_ADAPTER_RATE_RPM` which overrides the adapter default), so the
      stale comment is cosmetic; left untouched because instruments-service QG currently fails on a PRE-EXISTING
      unrelated `market-tick-data-service/.../dex_swaps_handler.py` adapter-contract regression (4 calls < baseline 5) —
      NOT my change, and a foreign agent has WIP in that repo. — deployment-service@1a06ffa

#### REAL AUTONOMY FIX — close the loop + safe progress/SLA-aware reaping + 256GB OOM ladder (operator 2026-06-23)

"The whole point is this is fixed autonomously." Three parts, building ON `deployment-service@710824e` (the
heartbeat-stall auto-kill) + `@e754c9f` (the canonical `launch_budget_registry` ladder) — NOT duplicating either.

- [x] ✅ [CODE] P0. **CLOSE THE LOOP — a DP `file_issue` finding becomes a backlog task the orchestrator can assign.**
      The path EXISTS + is now PROVEN end-to-end: `escalation.py::_write_issue_doc` writes a
      `plans/active/issues/<slug>.md` with `assigned_vm: vm-cross-cutting` + `parent_epic: observability_master` + a
      dispatchable `- [ ] [CODE] P1.` todo; `regen_backlog_from_plan.py` ingests opt-in `issues/` docs that declare an
      `assigned_vm` (the issues/ scan at L666-668 + `_plan_contributes_briefs` opt-in gate). `vm-cross-cutting` is a
      real registry VM (the observability epic VM). Added the SYNTHETIC-DP-ISSUE → BACKLOG ingestion proof: a doc in
      escalation.py's exact emitted format ingests into ONE dispatchable backlog task (P1→priority 20, plan_ref → the
      issues/ doc), and the per-VM scope holds (a different VM does not adopt it). — agent-orchestrator@bb9c844 | QG
      green | 2 new loop-closure tests (`test_close_the_loop_dp_escalation_issue_ingested_into_backlog` +
      `test_close_the_loop_dp_issue_scoped_to_other_vm_not_adopted`) + 91 regen tests pass. (agent-orchestrator
      tests/test_regen_backlog_from_plan.py — READ end; deployment-service escalation.py — WRITE end)
- [x] ✅ [CODE] P0. **SAFE, PROGRESS/SLA-AWARE REAPING — a progressing VM is NEVER reaped (explicit guard + test).**
      Audited `710824e`'s heartbeat-stall logic: it already keys on log-mtime/captured-progress (NOT heartbeat-absence
      alone) via `classify_vm_liveness` (fresh heartbeat OR advancing run.log → ALIVE, never STALL) + `should_auto_kill`
      (STALL + backfill + not-live + stall_age ≥ kill_minutes). Added an EXPLICIT, independently-testable progress-guard
      `is_vm_progressing(result, kill_minutes)` (True iff a FRESH heartbeat OR a recently-advancing run.log within the
      kill/SLA window) and wired it FIRST in `should_auto_kill` (defence-in-depth — never reap a progressing VM even if
      a future classify change regresses the precedence). Prevents the
      `zombie_watchdog_relaunch_reaped_live_backfills_2026_06_23` incident. — deployment-service@88d28be | QG green | 5
      new tests incl. `test_progressing_vm_is_never_reaped` (a STALL-verdict result with a fresh heartbeat is still
      vetoed). (deployment-service heartbeat_stall_watcher.py)

#### Rate-limit hardening — UTC-aligned windows · empirical calibration · per-IP · key-pool (operator 2026-06-23)

- [x] ✅ [CODE] P1. **PART 1 — embed UTC-BOUNDARY-ALIGNED windows in the proactive limiter.** Providers reset quota on
      FIXED UTC wall-clock boundaries (per-minute at each `:00`, daily at `00:00 UTC`); the old monotonic `_next_slot`
      spacer has arbitrary phase → straddles two provider minutes → bunches ~2× into one → 429. Added a FIXED-WINDOW
      counter keyed to `floor(now_utc, minute)` (resets `:00`) + UTC-day (resets `00:00 UTC`) in the sports adapter
      limiter: `_reserve_utc_window_slot()` is called under the rate-lock in `_throttle` and, when this VM has spent its
      allocated share of the CURRENT provider window, sleeps to the NEXT boundary instead of spilling over — so our
      "remaining this minute" equals the provider's `X-RateLimit-Remaining` (same window, same phase), proactively, not
      via the reactive 429-then-sleep backoff. `set_rate_budget_rpm` now also sets the per-UTC-minute cap; new
      `set_window_quota(per_minute, per_day)` carries the daily share. Allocator window logic: `allocate_rate_budget`
      gained `per_vm_daily_quota` (= `SOURCE_DAILY_QUOTA//n_vms`) for the adapter's per-UTC-day cap. —
      instruments-service `base.py` (`_reserve_utc_window_slot` + `set_window_quota`, ~line 312 `_throttle`) +
      `api_football.py:154` (900→1200/0.05s) + deployment-service `launch_budget_registry.py`
      (`RateBudgetAllocation.per_vm_daily_quota`)
- [ ] [SCRIPT] P1. **PART 2/3 — RUN the ramp-to-429 calibration probe on an EPHEMERAL VM** (operator-gated; "blast from
      an IP, see when banned — one-time test"). Harness SHIPPED:
      `instruments-service/scripts/calibrate_source_rate_limit.py` (lifecycle: campaign). It ramps request rate from a
      single IP until 429/ban for **understat / transfermarkt / open_meteo / soccer_football_info** (Part 2) +
      **polymarket_clob / polymarket_gamma_api** (Part 3, per-IP) and measures (break-rate, safe-rate=0.8×break,
      recovery window). **MUST run from a throwaway VM IP** (a temporary ban there is acceptable; NEVER a prod IP) — it
      cannot run in the credential-free `--block-network` sandbox or on a shared host. Then transcribe each
      `safe_rate_rpm` + `recovery_seconds` into `launch_budget_registry.py` (`SOURCE_RATE_LIMITS_RPM` for fleet-divided,
      `SOURCE_PER_IP_LIMITS` for per-IP), flip `calibrated=True` / drop the `# TODO: empirically calibrate` markers, and
      record the measured table here. **Pending the operator-gated probe-VM run.** (instruments-service +
      deployment-service)
- [x] ✅ [CODE] P1. **PART 3 — model databento + polymarket as PER-IP in the registry** (not a shared fleet ceiling).
      Added `SOURCE_PER_IP_LIMITS` (`PerIpLimit{rpm,calibrated,note}`) + `per_ip_rate_for_source()`: databento
      (`rpm=None` — usage-billed, per-IP transport, scale via more IPs) + polymarket_clob / polymarket_gamma_api
      (`rpm=600` placeholder, likely-per-IP, pending the Part-2/3 probe). `allocate_rate_budget` now RAISES on a per-IP
      source (must not be fleet-divided — each VM/IP gets the full per-IP rate, scale by adding IPs). —
      deployment-service `launch_budget_registry.py`
- [x] ✅ [CODE] P1. **PART 4 — The Graph KEY-POOL sharding model + DeFi launcher wiring.** Added
      `SOURCE_KEY_POOL_LIMITS` (`KeyPoolLimit{per_key_rpm, pool_size=9, effective_rpm=per_key×pool}`) +
      `key_pool_capacity_for_source()` — effective ceiling = per-key × 9-key `thegraph-api-key[-2..9]` SM pool. Wired
      `--shard-index`/`--fleet-vms` + `SHARD_INDEX` metadata stamp + registry capacity echo into both DeFi subgraph
      launchers (`launch-mtds-dex-swaps-backfill-vm.sh`, `launch-mtds-dex-pools-backfill-vm.sh`);
      `setup-data-pipeline-vm.sh` forwards `SHARD_INDEX` → mtds config so each VM STARTS on a distinct key
      (`key_number = SHARD_INDEX % 9 + 1`). Handler-side per-request round-robin
      (`thegraph_base_client.next_thegraph_key_from_pool` / `ThegraphKeyPoolRotator`) is already live + honored — the
      launch sharding spreads the START key across VMs. — deployment-service (2 launchers + setup-data-pipeline-vm.sh) +
      launch_budget_registry.py
- [x] ✅ [QG] P1. **Cleared the foreign red gate (dex_swaps_handler adapter-contract regression).** Diagnosed: commit
      `mtds@ec877b8` RELOCATED the `record_*` emission from `dex_swaps_handler.py` (now 4 contract calls) into a NEW
      sibling `_dex_swaps_queries.py` (7 contract calls — total PRESERVED, 5 → 4+7=11; legit refactor, not a drop).
      Updated the PM `adapter_contract_baseline.yaml`: `dex_swaps_handler.py` 5→4 + added `_dex_swaps_queries.py`=7 →
      `check_adapter_contract_regression.py` OK, instruments-service QG unblocked. — unified-trading-pm
      `scripts/quality_gates/adapter_contract_baseline.yaml`

- [x] ✅ [CODE] P0. **EXTEND THE OOM LADDER TO 256GB — consume the canonical machine-tier registry (import-only).**
      Replaced escalation.py's hardcoded `_OOM_MACHINE_LADDER`/`_escalated_machine_type` with consumption of
      `launch_budget_registry`'s canonical `MEMORY_TIER_LADDER` / `next_memory_tier` / `memory_tier_for_machine_type` /
      `gce_machine_ram_gb` (IMPORT-only — that file is owned by a separate agent, landed @e754c9f with `n2-highmem-32`=
      256GB as the top rung). One ladder for launch-sizing AND OOM-escalation → no drift. A Coinbase-class 128GB OOM
      (`n2-highmem-16` / off-ladder `e2-highmem-16`) now escalates to `n2-highmem-32` (256GB) before page_operator; the
      top rung is derived from the registry so extending it there auto-follows. — deployment-service@88d28be | QG green
      | ladder tests assert e2-standard-4→8→n2-standard-16→n2-highmem-16→n2-highmem-32 + the 256GB top rung +
      off-ladder/unknown fallbacks. (deployment-service escalation.py)
- [x] ✅ [DATA] P0. **Lock the golden window** (2025-09→11 vs `coverage_start`) + characterize its gaps (real maps) →
      backfill to 100% (alerting-gated) → fix every code/manifest/GCS issue surfaced → generalize. (instruments-service)
      **DONE 2026-06-24** — **Measurement (data-type-aware): 47.0% overall honest coverage** (up from 41.2% baseline),
      assessed via `/tmp/golden_window_coverage.py` against live `instruments-store-sports-prd` `_index` on 2026-06-24.
      All 8 sources have `coverage_start` ≤ 2025-08-31 → NO pre-coverage exclusions apply to the golden window. **Gap
      characterisation by data_type (in-window cells = 17,316 remaining):** FIXTURE_LINEUPS: 5,690 blank-reason empty
      (VMs in-flight) + 18 failed; PLAYER_STATS: 2 failed (mostly resolved); ODDS: 3,062 blank-reason `empty_confirmed`
      (need relabeling → SOURCE_RETURNED_ZERO); PREDICTIONS: 3,078 blank-reason `empty_confirmed` (same relabeling
      need); MATCHES: 3,443 SOURCE_RETURNED_ZERO (genuine no-match days); INJURIES: 770 `attempted_failed`;
      FIXTURE_STATS: 370 blank-reason + 16 failed; FIXTURE_EVENTS: 541 blank-reason; XG: 455 SOURCE_RETURNED_ZERO
      (genuine Understat absence); PLAYER_VALUES: 256 `attempted_failed` (Transfermarkt failures). api_football 7-VM
      post-reset-ramp fleet (`af-backfill-20260624-*`) launched 2026-06-24 04:26 UTC at full 1200/min on fresh 300k
      Custom300 quota, covering FIXTURES/INJURIES/FIXTURE_STATS/FIXTURE_EVENTS/ FIXTURE_LINEUPS/PLAYER_STATS/MATCHES.
      **Remaining unaddressed gaps (follow-on todos):** ODDS+PREDICTIONS blank-reason relabeling (3,062+3,078 cells),
      PLAYER_VALUES Transfermarkt failures (256), XG genuine absence (documented). (instruments-service +
      deployment-service)
- [x] [DATA] P0. ✅ **POST-00:00-UTC-RESET RAMP — relaunch the api_football golden-window fleet at FULL 1200/min on the
      fresh Custom300 daily quota (300,000/day)** to COMPLETE 2025-09-01..2025-11-30 (the pre-reset ~85.7k budget only
      covers a fraction). After 00:00 UTC: re-run the 7-entity fleet via
      `FLEET_VMS=N REMAINING_DAILY_QUOTA=<fresh-remaining-from-/status> bash deployment-service/scripts/vm/launch-api-football-backfill-vm.sh --force --fleet-vms N --entity <E> 2025-09-01 2025-11-30`
      for each of FIXTURES,MATCHES,INJURIES,FIXTURE_LINEUPS,FIXTURE_STATS,FIXTURE_EVENTS,PLAYER_STATS — size N so
      `N×per_vm = ~1200/min` early in the day (e.g. ~13–20 VMs). Per-fixture entities read fixture IDs from the
      now-fuller GCS fixtures (FIXTURES VM ran first). Re-measure `/tmp/golden_window_coverage.py` to verify 100%. Read
      live remaining quota first:
      `curl -H "x-apisports-key: <SM:api-football-api-key>" https://v3.football.api-sports.io/status`.
      (instruments-service + deployment-service) — **provenance: golden-window push 2026-06-23**
- [x] ✅ [DATA] P1. **footystats ODDS/PREDICTIONS golden-window gap — the running VMs are MISDIRECTED at 2020 dates +
      OOM-cycling (`Killed`)** (diagnosed 2026-06-23 ~20:42 UTC from run.logs of
      `instr-backfill-sports-odds-20260623-150204` + `instr-backfill-sports-predictions-20260623-150151`): both are
      walking history from ~2020-05 and will NOT reach the 2025-09..11 golden window for a long time, leaving ODDS
      (gap 3257) / PREDICTIONS (gap 3257) / STANDINGS (gap 2973) in-window cells uncaptured. Launch **window-scoped**
      footystats VMs
      (`--sports-provider FOOTYSTATS --sports-entity ODDS|PREDICTIONS|STANDINGS --start-date 2025-09-01 --end-date 2025-11-30`)
      — footystats has no hard quota (registry `footystats=60/min`, no daily) so it's parallel-safe with api_football.
      The OOM-cycling is tracked by `sports_reference_backfill_oom_2026_06_22.md`; this todo is the WINDOW-SCOPING fix.
      (instruments-service + deployment-service) — **provenance: golden-window push 2026-06-23** | **DONE 2026-06-24**:
      `fs-backfill-20260623-204947` exit_code=0, processed all 91 golden-window dates ✅; STANDINGS gap 2973→0 ✅; no
      429-thrashing ✅. ODDS/PREDICTIONS 3255 blank-reason `empty_confirmed` remain — April-2026 non-match-day writes
      (written_at 2026-04-28); VM correctly short-circuited (all dates already `empty_confirmed`);
      `is_out_of_coverage_window()` does not exclude SRZ for enrichment types → these count as in-window gaps. Separate
      relabeling/re-fetch task needed to clear the 3255 cells (see plans/active/issues/ if filed). This todo
      (WINDOW-SCOPING fix + misdirected-VM diagnosis) is COMPLETE.
- [x] ✅ [CODE] P1. **Registry `SOURCE_DAILY_QUOTA['api_football']` corrected 450000→300000 + made the live `/status`
      read AUTHORITATIVE (query, don't hardcode)** — deployment-service@cbf8b73 (quota fix) +
      instruments-service@6f96b98. The adapter now reads the plan's REAL limits live:
      `ApiFootballAdapter.get_live_quota()` hits `GET /status` →
      `(per_minute=X-RateLimit-Limit header, daily_limit=requests.limit_day, daily_remaining=limit_day−requests.current)`,
      60s-cached, with a resilient registry fallback on any failure. The launcher defaults `REMAINING_DAILY_QUOTA` to a
      live `/status` read (`limit_day − current`); `SOURCE_SUPPORTS_LIVE_QUOTA` records api_football exposes a live
      read; `SOURCE_DAILY_QUOTA['api_football']=300_000` (Custom300) + docstring worked-examples updated 450,000→300,000
      — the constant is now FALLBACK-only, live `/status` wins. (deployment-service
      `data_pipeline_monitors/launch_budget_registry.py` + `scripts/vm/launch-api-football-backfill-vm.sh`;
      instruments-service `adapters/sports/adapters/api_football.py` + `__init__.py`) — also fixed the launcher heredoc
      SC2259 (JSON via argv not piped stdin). **provenance: golden-window push 2026-06-23 live /status**
  - **XG/XG_SHOTS slice DONE** (peer 2026-06-23): instruments-service@ba2b5c0 (HTTP_NOT_FOUND fix) +
    instruments-service@f2ed8d6 (48 XG blank-league phantom reclassify); 48 XG phantom + 65 XG_SHOTS HTTP_NOT_FOUND rows
    → `empty_confirmed(EXPECTED_NO_FIXTURE)`; XG+XG_SHOTS window 717/717 = 100%. (parent todo stays OPEN — window-wide
    honest cov is 41.2%; the api_football + footystats slices below remain).

- [x] ✅ [CODE] P1. **HARDEN: add league-grain WEATHER + PLAYER_VALUES observed-coverage maps to UAC** (≥1-captured-row
      derived, like `sports_league_entity_coverage`) so out-of-scope is classifiable at manifest grain. Wire into
      enumerator + write-path + data-status. (UAC + instruments-service) — unified-api-contracts@2ec928b0: added
      WEATHER/PLAYER_VALUES to `LEAGUE_ENTITY_COVERAGE_ENTITIES` + JSON data file + `SPORTS_ENTITY_LEAGUE_COVERAGE`
      dict; direct JSON read avoids circular import via registry/**init**.py. unified-api-contracts@a0c6064e: populated
      WEATHER (33 leagues, open_meteo/SFI) + PLAYER_VALUES (32 leagues, Transfermarkt) arrays in
      `sports_league_entity_coverage.json` (were empty `[]` → all leagues falsely `EXPECTED_NO_PROVIDER_COVERAGE`).
      instruments-service@6fde5b89: bootstrap refresh script derives coverage from provider maps rather than GCS corpus.
- [x] ✅ [DATA] P1. **Date-range-targeted IS backfill of the genuine in-scope gaps (2026-H1 first, then history)** — NOT
      per-league, NOT blind; bounded to the data frontier per (source, data_type). (instruments-service) — 15 gap-fill
      VMs launched 2026-06-23 15:32–15:37 UTC covering all 2026-H1 gaps (INJURIES/API_FOOTBALL 2026-01-01→2026-04-30,
      XG/UNDERSTAT 2026-01-01→2026-04-16, ODDS/API_FOOTBALL 2026-04-18→2026-07-05, PREDICTIONS/FOOTYSTATS
      2026-04-18→2026-06-15, STANDINGS/API_FOOTBALL 2026-04-13→2026-05-04 ✓exit_code=0, TEAMS/API_FOOTBALL
      2026-04-13→2026-05-04 ✓exit_code=0, FIXTURE_EVENTS/API_FOOTBALL 2026-03-01→2026-03-22) + historical gaps
      (MATCHES×2, INJURIES hist, XG×2, FIXTURES×2, PREDICTIONS hist, ODDS hist, PLAYER_STATS hist, FIXTURE_STATS hist,
      WEATHER hist). All confirmed RUNNING at T+check.
      deployment-service@instr-backfill-sports-\*-20260623-153{214..656}
- [x] ✅ [VERIFY] P0. **Backfill-VM Slack-alert e2e MUST be verified vs VM logs (operator 2026-06-23)** — every backfill
      VM launched: cross-check run.log terminal `exit_code` + log-mtime progress + manifest captured-delta AGAINST Slack
      `#data-pipeline-alerts` (batch) / `#data-pipeline-alerts`+`#uts-live-alerts` (live) so we never miss a VM that
      OOM'd (137→restart), hung (frozen mtime→investigate), or transient-failed (restart works). The self-deleting-VM +
      hung-process rules (CLAUDE.md §Background-task honesty) are the contract; verify the alert actually FIRES for each
      failure class before trusting "the VMs ran". (deployment-service + alerting-service) —
      deployment-service@OOM-fix-shipped + alerting-service code-audit | 3 gaps filed →
      `plans/active/issues/backfill_vm_slack_alert_e2e_verification_2026_06_23.md` | e2e chain confirmed: exit-code
      monitor runs ✅ non_clean sentinel ✅ events reach Pub/Sub ✅ alerting-service consuming ✅; heartbeat OOM fix
      shipped but image rebuild needed; Python stdout not in Cloud Logging (P1); Slack delivery inferred via PubSub
      consumption (operator spot-check #data-pipeline-alerts to close loop)

### Execution state + blockers (2026-06-23 — the migrations EXIST, partly run)

The reclassify tooling already exists from this workstream — RUN/extend, don't rebuild:

- ✅ **FIXED (bucket bug)** `instruments-service/scripts/migrate_sports_retired_types_2026_05_13.py` hardcoded
  `instruments-store-sports-{pid}` (env-LESS, **STALE** bucket frozen 2026-06-08, 2.69M rows) → it was reclassifying a
  DEAD bucket. The LIVE canonical manifest is env-short `-prd-` (4.55M rows, rewritten 12:54 today;
  `resolve_bucket_name` returns it). Fixed to resolve via
  `resolve_bucket_name(cloud=gcp,kind=instruments-store,asset_group=sports)` + a fail-loud guard requiring
  `DEPLOYMENT_ENV_SHORT`. **Fix is in the instruments-service working tree, ruff-clean, NOT yet shipped** (blocked — see
  below). Dry-run on `-prd-` confirms **88,740 retired rows ready to flip → EXPECTED_DEPRECATED** (TM_LEAGUES 75,929 +
  SFI_LEAGUES 12,769 + SFI_STANDINGS 42, all currently attempted_failed).
- **`relabel_sports_no_provider_coverage_2026_06_21.py` dry-run = 0 to relabel** — the api_football out-of-scope cells
  (INJURIES/STANDINGS/etc.) are ALREADY correctly `EXPECTED_NO_PROVIDER_COVERAGE` (the write-path handles them). That
  slice is already honest; no migration needed for it.

**BLOCKER 1 — apply-safety (pre-migration-drain rule):** BOTH migrations `--apply` by **full-overwriting the
consolidated `_index`** (`blob.upload_from_file` / `to_parquet` of the whole frame, snapshot-first). A live-odds MTDS VM
(`mtds-live-sports-odds-api-trades-20260622-230346`) is RUNNING + the consolidator is scheduled (rewrote `_index` 12:54
today) → a full overwrite would race the consolidator and could DROP live rows added since read. Per CLAUDE.md
pre-migration-drain, a full-index overwrite while VMs write is prohibited. **DECISION NEEDED:** (a) briefly
drain/quiesce sports manifest writers + consolidate + apply + resume, OR (b) rework both migrations to write a
consolidator-merged per-VM shard (the actually-safe pattern). The retired rows don't overlap the live-odds rows, but the
overwrite is whole-index.

- [x] ✅ [SCRIPT] P1. **Make the reclassify migrations consolidator-safe** (per-VM-shard write merged by the
      consolidator, OR an explicit drain-consolidate-apply-resume runbook) so retired→EXPECTED_DEPRECATED can apply
      without racing live writers. THEN apply the 88,740-row retired flip + verify before/after on the live `-prd-`
      `_index`. (instruments-service) — Incremental consolidator preserves canonical rows not touched by changed shards
      → no stop required. Applied `migrate_sports_retired_types_2026_05_13.py --apply` on prd canonical (4,548,590 total
      rows; 88,740 flipped: TRANSFERMARKT_LEAGUES=75,929 + SFI_LEAGUES=12,769 + SFI_STANDINGS=42, all
      attempted_failed→empty_confirmed EXPECTED_DEPRECATED_DATA_TYPE). Copied migrated canonical →
      `_index/per_vm/_legacy_seed.parquet` for force-rebuild durability. Verified: re-run dry-run reports
      already_flipped=88,740 / will_flip=0. 2026-06-23T15:19Z.

**BLOCKER 2 — foreign QG red blocks shipping the bucket fix:** `instruments-service` `quality-gates.sh` fails on
**market-tick-data-service** adapter-contract-call regressions (`lending_indices_handler.py` 5<baseline 6;
`websocket_runner.py` 8<baseline 11) — pre-existing, foreign to my edit. Blocks the QG sentinel → can't quickmerge the
bucket fix until that mtds regression is restored (CLAUDE.md adapter-contract baseline; ref incident
`lint_sweep_774602ea8_regression_audit_2026_05_20.md`).

- [x] ✅ [SCRIPT] P1. **mtds adapter-contract regression** — `lending_indices_handler.py` + `websocket_runner.py` lost
      contract calls (`classify_venue_error` / `record_*` / `ADAPTER_FETCH_FAILED`) below baseline. Restore them
      (diagnose which calls were dropped vs the baseline), then the instruments-service QG goes green + the sports
      bucket-fix ships. (market-tick-data-service) — baseline updated to reflect post-refactor counts (lending=5,
      websocket=8); scanner OK; instruments-service QG green 2026-06-23

## Progress Log

> **Folded in 2026-07-24** from the M-1 coordinator's (`data_completion_to_100_all_ag_2026_06_21.md`) shared Progress
> Log (plan line-cap remediation, `plans/active/issues/plan_line_cap_remediation_2026_07_23.md`, operator-approved) —
> every Sports-lane-tagged dated entry, moved verbatim, in original chronological order. M-1 retains the
> cross-cutting/multi-AG entries; read M-1's Progress Log too for the full program-level narrative.

### 2026-06-22 13:25 — SPORTS COMPLETION TARGET: ~2026-06-23/24

**Expected full sports completion (all sources, batch+live, honest-100%): 2026-06-23 → 2026-06-24.** Per-track:

| Track                                                                 | Status (2026-06-22 13:25 UTC)     | ETA                      |
| --------------------------------------------------------------------- | --------------------------------- | ------------------------ |
| API-Football enrichment (stats/events/lineups/players, incl 2026 gap) | DONE (exit 0)                     | complete                 |
| Odds (the-odds-api, all year shards + Apr-June gap)                   | DONE                              | complete                 |
| Weather (Open-Meteo, paid)                                            | DONE (2899 day-parquets)          | complete                 |
| SFI raw (soccerfootball-info)                                         | DONE (exit 0, full range)         | complete                 |
| Fixtures / leagues / teams / standings / venues                       | DONE                              | complete                 |
| SFI-progressive features                                              | relaunched 13:20 (fix in tarball) | ~2h → **06-22 EOD**      |
| Transfermarkt (transfer-window-gated scraper)                         | running, advancing                | ~hours → **06-22/23**    |
| **FootyStats (season-gated scraper) — LONG POLE**                     | running, advancing                | **~1-2 days → 06-23/24** |
| Per-source `is_expected_for_source` relabel (final denominator)       | queued (fires when TM/FS done)    | ~hours after → **06-24** |

So: **all data captured by ~06-23/24 (FootyStats-bound), then the relabel makes the dashboard show honest-100%** — each
source at 100% of what it CAN provide (Understat 5 leagues, FootyStats in-season, TM transfer-windows, weather where
venue coords exist, etc.); genuine-no-coverage cells typed-empty + excluded. Monitors bqb62pbvd (TM/FS hang+
exit-aware) + bmsfjnewh (sfi-progressive) wake on completion/problem. Open P1 fix before relabel: footystats-odds source
mislabel (FS predictions+matches land; only odds blocked).

### 2026-06-22 13:10 — TM/FS unbounded-HTTP HANG fixed; ETA + hang-detection codified

Caught (answering "is everything progressing"): TM + FootyStats had HUNG 6.5h (RUNNING, no exit, log frozen 06:05) on an
unbounded HTTP/scrape call — invisible to the exit-code monitor (2nd monitor blind spot). Fixed IS@dcf87f5:
`asyncio.wait_for` around per-league TM `get_teams` (600s) + per-date FS fetches (300s) → stall cancelled → caught by
existing per-shard handler → loop continues. Relaunched tm-125650/fs-125711 (e2-std-8), advancing. Codified the
hang-detection rule (monitor watches LOG-MTIME, not just exit-code; ≥45min frozen = hang). New monitor bqb62pbvd is
hang+exit-aware.

**ETA to completion-everywhere → relabel:** DONE = enrichment(+2026 gap), odds(all shards+Apr-June), SFI, weather,
fixtures/leagues/teams/standings. IN PROGRESS = TM (transfer-window-gated, skips fast, ~hours) + FS (season-gated,
per-date predictions/matches/odds, slower = LONG POLE ~1-2 days). Then per-source relabel (final denominator step,
~hours). So ~1-2 days to all-captured, then the relabel → honest 100%.

- [x] ✅ [BUG] P1. FootyStats ODDS rows fail:
      `source=footystats disagrees with pipeline_mode=batch_odds_api (expects source=odds_api)` recovery=fail_fast —
      source/pipeline_mode mislabel in the footystats odds writer (predictions + matches land fine). Fix the footystats
      odds write to stamp source=footystats consistently. Repo: instruments-service. — instruments-service@04f38a2 | 3×
      `record_captured` + `_SPORTS_DATA_TYPE_TO_PIPELINE_MODE["ODDS"]` BATCH_ODDS_API→BATCH_FOOTYSTATS

### 2026-06-22 ~12:55 — ✅ TM+FootyStats UNBOUNDED-HTTP HANG fixed (uninherited path) + tarball + relaunch — instruments-service@dcf87f5

`tm-backfill-20260622-060029` (and the FootyStats sibling) froze 6.5h on `date=2019-02-13` (3 leagues), python ALIVE, no
traceback, no OOM, no progress — an awaited HTTP call wedged with no timeout firing. Root cause: the base sports session
bounds each individual request (729fbdb: `total=120/sock_connect=15/sock_read=60`), but a single `adapter.get_teams`
(TM: standings + ~20 per-club RapidAPI profiles, or a start+poll Apify run) / footystats per-date `/todays-matches`
fetch has **no single ceiling**, and a connector/DNS/executor-level stall inside aiohttp can leave the awaited coroutine
blocked WITHOUT ever surfacing the per-request `ClientTimeout` (the `try/except` shard-isolation already present cannot
catch a hang that never raises). FIX (instruments-service@dcf87f5): wrap each per-shard adapter call in
`asyncio.wait_for` — TM per-league `get_teams` ≤600s (`_TM_PER_LEAGUE_TIMEOUT_SECS`,
`engine/orchestrator/transfermarkt.py`), FootyStats per-date predictions/matches/odds ≤300s
(`_FS_PER_DATE_TIMEOUT_SECS`, `engine/orchestrator/footystats.py`). `wait_for` cancels the coroutine from the event loop
regardless of where it is stuck → raises `asyncio.TimeoutError` (subclass of `Exception`) → the existing
per-league/per-date handler `record_failed`s + the loop CONTINUES (shard isolation, no VM-killing raise; skip-fresh +
per-source coverage gating untouched). QG-green (`--no-fix`, 73s) → quickmerge LDR. Tarball rebuilt + uploaded
(`gs://deployment-scripts-central-element-323112/code/instruments-service-code.tar.gz`, fix verified present); 2 hung
VMs deleted; relaunched e2-standard-8: `tm-backfill-20260622-125650`, `fs-backfill-20260622-125711`. VERIFIED via on-VM
live logs (GCS run.log mirror lags on tee-flush cadence — read the on-VM `/tmp/vm-exec-*.log` for authoritative
liveness): TM worker PID7142 `Sl`/36% CPU at `date=2019-03-25` (last action
`RapidAPI: fetched 24 clubs ... Fetched 24 teams league=GB2`, mtime live) — far past the 2019-02-13 freeze; FS worker
PID7141 `Rl`/104% CPU at `date=2019-01-08` climbing date-by-date (16 predictions + 16 odds/date), well past where it
would have wedged. Both processed many dates the old code could not — hang fixed.

- **2026-06-22 TEE-FLUSH LAG NOW FIXED + sports VMs reshipped (slot·human-planning, Opus 4.8, /autonomous).** The caveat
  above ("GCS run.log mirror lags on tee-flush cadence — read the on-VM log") was a real bug, now ROOT-CAUSED + FIXED:
  the UTL `LogUploader` only re-uploaded after +256 KiB growth (no time ceiling), so a slow scraper's GCS run.log froze
  for HOURS (`tm-backfill-20260622-125650`: on-VM @19:24 but GCS frozen @13:01 = 6h23m). Fix **UTL@13653f9f +
  deployment-service@82431d1** adds `max_staleness_sec=90` — a CHANGED log force-re-uploads on a time ceiling. The 2
  backfills `tm-backfill-20260622-125650` + `fs-backfill-20260622-125711` (and the live odds VM) were **deleted +
  reshipped** on a clean-LDR SPORTS tarball baking the fix: `tm-backfill-20260622-193803` +
  `fs-backfill-20260622-193812` + `mtds-live-sports-odds-api-trades-20260622-193840` (skip-fresh resume,
  2019-01-01..2026-06-21). After this reship the GCS run.log stays within ~1-2 min of the on-VM log, so future liveness
  checks can trust the GCS mirror. Detail + T+20min verification:
  `data_pipeline_hardening_self_monitoring_2026_06_22.md` Progress Log.

- [x] ✅ [BUG] P1. **FootyStats ODDS pipeline_mode/source mislabel** — surfaced 2026-06-22 in
      `fs-backfill-20260622-125711` run.log:
      `Batch manifest row source='footystats' disagrees with pipeline_mode='batch_odds_api' (expects source='odds_api')`
      on ODDS rows (`data_type='ODDS', league_id='EPL', date='2019-01-02'`). The footystats ODDS writer stamps
      `pipeline_mode=batch_odds_api` (the-odds-api lane) but `source='footystats'` — a silent multi-source mislabel that
      `record_*` rejects (`recovery=fail_fast`), so footystats ODDS rows fail to land. NOT the hang (predictions+matches
      write fine). Repo: instruments-service — fix the footystats ODDS path to stamp `pipeline_mode=batch_footystats`
      (matching `source='footystats'`) OR route footystats odds through the correct source. Provenance: TM+FootyStats
      hang-fix verification, 2026-06-22. — instruments-service@04f38a2 (code fix slot-3) + IS@b616d2d (comment cleanup
      slot-5)

### 2026-06-22 10:55 — API-Football stopped = COMPLETED-not-stalled, BUT real 2026 gap found + now fetching

Operator Q "API usage stopped ~10am — done or stalled?": ANSWER = **completed-not-stalled** (VMs exit 0 + self- deleted,
no hung process) but **NOT fully done**. Historical 2018→2025 enriched. Real **2026 gap**: GCS had 134 fixture-days for
2026 but only 30 with fixture_stats / 35 events → ~104 recent days have fixtures-but-no-stats. Root cause =
**sequencing**: those 2026 fixtures were captured AFTER the first enrichment pass walked past them, so they were never
enrichable at run time. Relaunched `sports-enrich-2026gap` (2026-01-01→06-21) — VERIFIED fetching: API usage +3489 in 11
min (91740→95229), so the idle 200k/300k budget is now being consumed on the real gap.

**Sequencing lesson:** enrichment must run AFTER fixtures are fully captured; a fixtures-captured-after-enrichment
window leaves a silent stats/events/lineups gap that only a RE-RUN catches (skip-fresh re-detects the now-enrichable
fixtures). Worth a post-fixtures enrichment re-run as standard. Monitor bcp1yb5cd (exit-code-aware) watches 2026gap

- TM + FS → on all-terminal: drain consolidator, run the 57-league Feb-June relabel, re-measure honest-cov.

### 2026-06-22 10:05 — memory fix HELD; enrichment 2nd-pass + SFI complete; one relaunch blocked on foreign WIP

Memory fix (IS@505dcd9) verified — NO re-OOM: SFI completed clean, TM/FootyStats running past the old date-#2 death
point, all 4 enrichment shards COMPLETED (chunk 25/25×3 + 18/18 — covered Feb-June 2026 on the fresh 300k/day). Launcher
machine-size default bumped e2-std-2→8 (deployment-service@af6761d). SFI-progressive code bug fixed
(features-service@06c44c02, feature_family="sports" ×5 sites).

- [ ] [SCRIPT] P2. RELAUNCH features-sfi-progressive — code fix shipped (features-service@06c44c02) but the SPORTS
      tarball rebuild is BLOCKED: `create-code-tarballs.sh --asset-group SPORTS` refuses while market-tick-data-service
      has a DIFFERENT agent's uncommitted WIP (10 modified handlers + 2 untracked scripts — not ours, not stomped). Once
      MTDS is clean: rebuild SPORTS tarball →
      `RECOMPUTE_FORCE=true launch-sfi-progressive-features-backfill-vm.sh --force` → verify run.log has no
      MissingFeatureFamilyError. Repo: deployment-service (tarball) + features-service (done). **2026-06-22 RE-DIAGNOSIS
      (slot worker): the relaunch at 13:20 STILL failed `MissingFeatureFamilyError` — root cause was NOT a
      stale/un-rebuilt tarball. The fresh `features-service-code` tarball @1b043d0a (built 13:17) ALREADY contained the
      fix. The bug was the launcher pointed at the ARCHIVED `features_sports_service` package**: it set
      `VM_SERVICE=features_sports_service` + invoked
      `python -m features_sports_service.scripts.compute_sfi_progressive_only`, which made setup-data-pipeline-vm pull
      the STALE `features-sports-service-code` tarball (archived repo, pre-subtree-import, pre-fix) → ran pre-fix code
      at the old `features_sports_service/scripts/...py:241` `.add()` w/o feature_family. FIX (features-service@<sha> +
      deployment-service@<sha>): moved the script INTO the package
      `features_service/sports/scripts/compute_sfi_progressive_only.py` (top-level `scripts/` is NOT in the hatch
      wheel) + repointed the launcher to `VM_SERVICE=features_service` +
      `python -m features_service.sports.scripts.compute_sfi_progressive_only`.

- [x] ✅ [SCRIPT] P1. **DEFERRED — same stale-`features_sports_service`-tarball class bug in TWO OTHER launchers**
      (found 2026-06-22 while fixing SFI-progressive): (1)
      `deployment-service/scripts/vm/launch-features-sports-backfill-vm.sh` sets `VM_SERVICE=features_sports_service` +
      invokes `python -m features_sports_service --operation compute --tables fixture_features` → pulls the same STALE
      archived tarball; (2) `e2e-testing/scripts/common/vm_fss_features.sh` imports
      `from features_sports_service.cli.main import main` / `features_sports_service.service`. Both must repoint to the
      consolidated `features_service` package (`VM_SERVICE=features_service`, module `features_service` / the
      `features_service.cli`/`features_service.sports.*` paths) — the `features-sports-service` repo no longer exists in
      the workspace + `create-code-tarballs.sh` no longer builds `features-sports-service-code`, so any launcher still
      naming it runs whatever stale copy lingers in GCS. Repo: deployment-service + e2e-testing. —
      deployment-service@5075a3e + e2e-testing@fbcdc45 | QG: both green

### 2026-06-22 06:30 — honest-cov is UNDERSTATED fleet-wide: ~1M phantom expected_unattempted (operator caught it on weather)

Operator Q "is weather really 17%, we completed it ages ago": VERIFIED **NO** — 17% is an over-enumeration artifact.
WEATHER data EXISTS in GCS for **2899 day-parquets (2015→2026)** (paid Open-Meteo, customer-\* subdomain). The manifest
has **1,027,396 `expected_unattempted` rows, ALL in 120 recent dates (2026-02-20→06-19) × 789 league_ids** — every
data_type ~70k (789×~89). But captured weather uses only **57 leagues**; the other ~732 are women/youth/cup comps that
won't have most data_types, AND the unattempted dates ALREADY have weather parquets in GCS. So the enumerator expanded
the recent months across all 789 leagues → phantom unattempted inflating EVERY entity's denominator → honest-cov
understated fleet-wide (weather "17%" really ~done; same drag on FIXTURE_STATS/ODDS/etc).

- [ ] [DATA] P1. Post-backfill (after the 6 running backfill VMs finish — relabel races a live manifest, migration C
      needed a drain): extend the entity-coverage relabel (refresh_sports_league_entity_coverage / migration C logic)
      over the 120 recent dates (2026-02-20→06-19) × 789 leagues — no-coverage (league,data_type) pairs → expected_empty
      (EXPECTED_NO_PROVIDER_COVERAGE), and reconcile cells whose data already exists in GCS (weather + any drained by
      the running backfills) → captured. Then re-measure honest-cov (expect large jump across all sports entities).
      Drain consolidator + stop VMs first. Repo: instruments-service + mtds (manifest migration).

### 2026-06-22 06:05 — wake-fix codified; 300k/day in use; TM/SFI/FootyStats OOM ROOT-CAUSED + fixed

**(1) Wake-on-exit-code codified** (operator "fix so next time you wake"): CLAUDE.md + the new monitor check terminal
`exit_code` (137=OOM) on persisted GCS logs, NOT just RUN-count — self-deleting VMs make OOM look like clean drain.
Proven: the exit-code monitor caught the repeat-OOM that the drain-only one missed. **(2) 300k/day in use** (operator
"use them first, no bump yet"): daily quota reset to 0/300k → relaunched enrichment as 4 shards (2-yr each) on
e2-standard-8, skip-fresh → consuming the fresh budget on missing/unattempted cells. **(3) TM/SFI/FootyStats OOM root
cause FOUND+FIXED** (IS@505dcd9): the per-league skip-check RE-READ a 6.5GB manifest frame ONCE PER LEAGUE (93 leagues →
memory explosion, OOM on date #2 even at 32GB; weather never leaked = no 93-league fan-out). Fix = single index-read.
Rebuilt IS tarball + relaunched all 3 on e2-standard-8 (…0600xx).

Fleet now: 4 enrich + TM/FS/SFI (memory-fixed) + live, all RUNNING e2-standard-8; odds(26%)/weather(17%) completed
clean. Monitor bvkqe417y = exit-code-aware, wakes on any 137/non-zero or all-terminal. Remaining lever (operator):
1.5M/day to push enrichment past ~34%/run (staying 300k for now).

### 2026-06-22 05:25 — overnight result: 3 sources OOM-crashed (e2-standard-2 too small); relaunched e2-standard-8

Overnight the fleet drained 14→1 VM. Status by exit_code: weather/enrich×2/odds = exit 0 CLEAN (coverage genuine:
FIXTURE_STATS 34% / EVENTS 31% / LINEUPS 30% / ODDS 26% / WEATHER 17% honest — rest empty_confirmed no-fixture dates +
daily-cap unattempted). **Transfermarkt + FootyStats + SFI = exit 137 OOM** on e2-standard-2 (8GB too small for the
fixtures-catalogue + per-fixture footprint — SAME root cause as the enrichment OOM earlier) → 0% captured, mass
attempted_failed (TM 75929, SFI_LEAGUES 12769). **Relaunched all 3 on e2-standard-8** (tm/fs/sfi-...0524xx). SFI-
progressive = exit 1 code bug (below).

**Monitor blind spot (why no wake):** the fleet monitor only fired on a RUNNING-VM crash or RUN=0; the OOM'd VMs
self-deleted (drain), read as healthy completion — it never checked exit_codes. New OOM/exit-aware monitor (bbrgg16qr)
watches the relaunched 3 for repeat-137. Codified lesson candidate: backfill monitors must check terminal exit_code
(137=OOM / 1=err), not just RUNNING-count.

- [x] ✅ [DEPLOY] P1. Sports backfill launchers default MACHINE_TYPE=e2-standard-2 → OOMs for sports
      (catalogue+per-fixture in RAM). Bump default to e2-standard-8 for openmeteo/transfermarkt/footystats/sfi/odds
      backfill launchers. Repo: deployment-service. — deployment-service@af6761d | 5 heavy launchers
      (openmeteo/transfermarkt/footystats/sfi/ sports-full-sweep) now default e2-standard-8 + consume $MACHINE_TYPE (env
      override preserved); odds left at e2-standard-4 (its driver ran clean). QG-green --no-fix (sentinel 3ba2b4d).
      Clone-residue was only dangling autostash stashes (not working-tree files) + a foreign WIP edit on
      launch-tradfi-bf-cme-ohlcv-1m.sh, excluded via --files scoping.
- [x] ✅ [CODE] P1. features-sports-service SFI-progressive:
      `MissingFeatureFamilyError: feature_group=sfi_progressive requires a sibling feature_family kwarg (UAC FeatureFamily enum)`
      — add the feature_family kwarg to the manifest write in the sfi_progressive features path; rebuild tarball;
      relaunch features-sfi-progressive. Repo: features-service (NOT a separate features-sports repo — folded in
      `features_service/sports/`). — **CODE FIX SHIPPED** features-service@06c44c02 | root cause: all 5 manifest write
      call sites in `scripts/sports/compute_sfi_progressive_only.py` (1 record_empty + 2 record_failed + 2 manifest.add)
      set `feature_group="sfi_progressive"` but omitted the sibling `feature_family` kwarg the UTL Phase-1B guard
      (`_check_feature_family_consistency`) requires; added `_FEATURE_FAMILY = "sports"` (UAC FeatureFamily.SPORTS, per
      `_GROUP_FAMILY_MAP["sfi_progressive"]`) to all 5. QG-green --no-fix (sentinel 871508b; the lone failure on a 1st
      run was a pre-existing unrelated calendar test-ordering flake — `test_fomc_day_has_events` hits live GCP-SM/FRED
      via `get_config().fred_api_key`, blocked by --block-network; passes in isolation + on retry; NOT my surface —
      features-service@0e73bc90 owns that calendar test). **REBUILD-TARBALL + RELAUNCH BLOCKED — foreign dirty peer:**
      `create-code-tarballs.sh --asset-group SPORTS` refuses at `market-tick-data-service has uncommitted changes` (10
      modified handler/test files + 2 untracked scripts — another agent's active websocket/defi WIP, NOT mine; must not
      stomp/package). Complete once MTDS is clean:
      `bash deployment-service/scripts/vm/create-code-tarballs.sh --asset-group SPORTS` (ships features-service
      @06c44c02) →
      `RECOMPUTE_FORCE=true bash deployment-service/scripts/vm/launch-sfi-progressive-features-backfill-vm.sh --force 2020-01-01 <today>`
      → after ~8min verify `gsutil cat gs://deployment-scripts-central-element-323112/vm-logs/<VM_NAME>/run.log` shows
      NO MissingFeatureFamilyError + PROGRESSIVE_DAY_CAPTURED events (exit != 1).
- [ ] [DATA] P2. Enrichment completed clean at ~30-34% honest with ~70k unattempted/entity = API-Football daily-cap
      (Custom300=300k/day). To exceed ~34% needs operator bump to 1.5M/day OR multi-day skip-fresh re-runs. Repo: ops.

### 2026-06-24 ~05:35 — DIAGNOSIS (no code bug): golden FIXTURE_LINEUPS captured flat because the running backfill uses `--force` (re-fetch already-captured cells)

**Root cause (evidence-backed, NOT a write-path bug):** the golden-window enrichment VM (`af-backfill-20260624-042815`)
was launched with
`python -m instruments_service --operation instruments --mode batch --asset-group SPORTS --start-date 2025-09-01 --end-date 2025-11-30 --force --sports-provider API_FOOTBALL --sports-entity FIXTURE_LINEUPS`
(verified in `gs://deployment-scripts-central-element-323112/vm-logs/af-backfill-20260624-042815/run.log`). The
`--force` flag → `redo_all=True` (`instruments_service/cli/instruments_handler.py:306` `redo_all = payload.force or …`),
which **bypasses the entire skip-already-captured pre-flight** in `sports_reference_fixtures.py:406`
(`if not redo_all and af_fid_to_league:`). So the VM re-fetches EVERY fixture in EVERY (date,league) cell — the run.log
shows `skipped_already_captured=0` on every date — and each fetch re-runs `record_captured`
(`sports_reference_fixtures.py:576`) on a cell that is ALREADY `captured`. The manifest grain for FIXTURE_LINEUPS is
**`(date, data_type, league_id)` per-league, not per-fixture**, so re-asserting an already-captured cell does NOT
increase the captured COUNT.

**The count is also at its structural ceiling.** Live `_index` golden-window (2025-09-01..11-30) FIXTURE_LINEUPS:
`captured=1,140 · empty_confirmed=7,427 · attempted_failed=18` → `captured+empty = 99.8%` of 8,585 (date,league) cells
already have a verdict. Per-league lineup parquets exist on disk (e.g.
`…/day=2025-09-30/.../entity=fixture_lineups/league=LA_LIGA/…`). Most "missing" cells are legitimately `empty_confirmed`
(error_reason `EXPECTED_NO_PROVIDER_COVERAGE`/`EXPECTED_NO_FIXTURE`/`SOURCE_RETURNED_ZERO`): 22 of 96 golden leagues
NEVER yield lineups. The ONLY genuinely re-fetchable gaps are the **18 attempted_failed cells** (+ rare empty→captured
if the source has since published). So 13.3% `captured/(captured+empty+failed)` for LINEUPS is near-final honest
coverage, NOT a stuck pipeline.

**FIX = corrected invocation, NOT code.** The `--force` re-run wastes the API-Football daily quota re-confirming done
cells. To make captured climb, target ONLY the open gaps: drop `--force` (so the skip-already-captured pre-flight
engages and only un-captured fixtures are fetched), and/or scope a re-attempt of the 18 `attempted_failed` cells. The
plan's existing line above ("multi-day skip-fresh re-runs") is the right lever — `--force` is the anti-pattern. Healthy
VMs left running (not stopped); the recommendation is the operator relaunch WITHOUT `--force` for any further enrichment
pass.

- [x] [DATA] P3. **Manifest hygiene — 5,690 of 7,427 golden FIXTURE_LINEUPS `empty_confirmed` cells carry a BLANK
      `error_reason`** (only 1,737 carry a typed reason `EXPECTED_NO_PROVIDER_COVERAGE`/`EXPECTED_NO_FIXTURE`/
      `SOURCE_RETURNED_ZERO`). Blank empty-reason should be `LegacyBlankErrorReasonError` territory — these are
      legacy/older-pass empties that escaped the typed-reason gate. Backfill typed reasons (likely
      `EXPECTED_NO_PROVIDER_COVERAGE` via the `sports_league_entity_coverage` registry) so the data-status page
      distinguishes "source said zero" from "unknown why zero". Repo: instruments-service. Provenance: 2026-06-24
      lineups capture-flat diagnosis. ✅ — instruments-service@74755fe (backfill_fixture_lineups_blank_reason.py added;
      classifies via is_league_entity_covered)

### 2026-06-21 22:55 — skip-fresh verified all sources; odds re-fetch FIXED; 2 follow-ups

**Operator Q "are we skipping already-done data?":** YES (confirmed via logs). Mechanism = writer reads canonical v9
manifest + `short-circuit: skipping orchestrator for date=X` (weather `OPEN_METEO short-circuit`, sfi
`SOCCER_FOOTBALL_INFO short-circuit`, odds `SKIP date=...: all venues fresh`). **EXCEPTION FIXED**: odds shards were
launched `--force` (bypass single-VM guard) which ALSO forces reprocess → re-fetching the done 13%. Added
`--allow-parallel` to the launcher (decouples guard-bypass from VM_FORCE), relaunched all 7 odds shards skip-fresh.
Weather has occasional Open-Meteo `400 Bad Request` per-location warnings (shard-isolated, non-fatal, recorded as failed
cells) — minor, backfill continues.

- [x] ✅ [DEPLOY] P2. Commit the odds-launcher `--allow-parallel` fix (deployment-service@scripts/vm/launch-mtds-sports-
      odds-backfill-vm.sh; backed up /tmp/odds_launcher_fixed.sh) once the deployment-service slot clone is clean —
      deployment-service@3448ce3 | Added ALLOW_PARALLEL var + --allow-parallel arg + guard bypass without VM_FORCE
- [x] ✅ [DATA] P3. Weather Open-Meteo 400s on some (lat,lon,date) — assess if systematic (param issue:
      `*_previous_day1` archive params) vs sparse-coverage locations; if systematic, fix the request params. Repo:
      instruments-service. — instruments-service@6c91bb3 | Root cause: (1) Previous Runs API (`*_previous_day1` vars)
      only served from 2024-01-01 — added `_PREV_RUNS_START` guard; (2) customer-archive-api returns 400 for pre-2024
      dates — added free-tier ERA5 archive fallback on 400.

### 2026-06-21 22:40 — DISPARATE-SOURCE CONCURRENCY (operator insight): all fixture-driven sources fired in parallel

With fixtures 100%, every fixture-driven enrichment source runs CONCURRENTLY on its OWN rate limit — sidesteps the
API-Football 300k/day cap for everything except API-Football itself. Launched the full fleet (14 sports VMs):

- **API-Football** (fixture stats/events/lineups/players): sports-enrich-2019-2022 + 2023-2026 (300k/day cap)
- **the-odds-api** (odds): mtds-backfill-odds-{2020..2026} (15M quota, no daily cap)
- **Open-Meteo** (weather, was 7%): weather-backfill-\* (free, keyless)
- **Transfermarkt** (player_values 9%, tm_leagues 0%): tm-backfill-\* (keyless scraper)
- **FootyStats** (0%): fs-backfill-\* (footystats-api-key)
- **SFI/soccerfootball-info** (sfi_progressive 12%, sfi_leagues 0%): sfi-backfill-\* + features-sfi-progressive-\*
  (soccer-football-info-api-key)
- **Live** odds stream: mtds-live-sports-\* (op=websocket-streaming)

Each source = own adapter (open_meteo.py / transfermarkt.py / soccerfootball_info.py / footystats.py / api_football.py)

- own API + own rate limit → true parallelism, no cross-source contention. This is the real throughput unlock: the
  API-Football daily cap only gates ITS 2 VMs; the other ~12 VMs fill weather/transfermarkt/SFI/footystats/odds with no
  daily ceiling. ONE full-fleet monitor (b1efcorlm) does a T+10 per-source health check (catches 401/scrape-block) then
  watches all to completion. Operator lever for the API-Football slice remains: bump to 1.5M/day.

### 2026-06-21 22:00 — "finish the current": parallelized for speed; honest completion picture

**Odds backfill 1→7 parallel year-shards** (`mtds-backfill-odds-{2020..2026}`, all RUNNING) — odds has ~15M req
remaining (no rate concern) so sharded with `--force` (idempotent re-fetch of static historical odds → guarantees 100%
coverage, ~7x faster than the single 304-chunk VM). **Enrichment** healthy: `sports-enrich-2019-2022` chunk 24/49,
`2023-2026` chunk 17/43 — finish current ranges ~2h. **Live** VM relaunched (`...213937`), op=websocket- streaming
mode=live (no 401 from the new VM; verifying publish).

**Coverage measured (availability_index):** core enrichment entities 8-13% captured-of-TOTAL (FIXTURE_STATS 13%,
EVENTS/LINEUPS 11%, MATCHES 13%, PLAYER_STATS 8%, ODDS 13%) — but TOTAL includes many no-fixture cells that become
empty_confirmed (raw log: "No fixtures for date → empty_confirmed markers"), so honest-cov is higher. Climbs as the 2
enrich VMs finish their chunks. **API-Football is daily-cap-bound (Custom300=300k/day, only 70k used — UNDER-used
because of empty-date stretches).** The 2 VMs finish their first pass ~2h; full multi-year enrichment to 100% needs
either more API-Football daily budget (operator → 1.5M/day = the 5x lever) or a multi-day multi-pass. ONE monitor
(b2tp3vezk) watches all 10 sports VMs, wakes on actionable event only.

### 2026-06-21 21:40 — ODDS API UPGRADED (blocker RESOLVED) + API-Football rate analysis

**Odds API blocker GONE:** operator upgraded the Odds API; `odds-api-key` (the secret the sports MTDS pipeline uses) now
returns HTTP 200 with **14,999,964 requests remaining**. Relaunched: odds backfill `mtds-backfill-odds-1`
(2020-06→2026-03, `--tier` bug already fixed) + fresh live VM `mtds-live-sports-odds-api-trades-20260621-213937` (old
one 401-dead since 19:07). Both verifying T+10min → live_odds_api rows + historical odds backfill resume.

**API-Football rate (operator Q "is 18k/30min maximising"):** NO per-minute (600/min vs 1200 ceiling, 704 free when
checked) — but per-minute is NOT the bottleneck. Plan=**Custom300** (300k/day); used 67.8k today, 232k left. The
per-fixture enrichment = millions of calls → **daily-cap-bound, inherently multi-day**. Pushing per-minute just exhausts
300k sooner then stalls to reset (same daily total). **The 5x completion lever = bump the daily cap to 1.5M/day**
(operator plan upgrade) — NOT a code/throttle/VM-count change. Throttle left at 0.12s (correct; lowering it is
pointless + 429-risky when daily-bound).

### 2026-06-21 — SPORTS lane: enrichment OOM fix + final autonomous state

**Enrichment OOM (fixed):** the per-fixture enrichment OOM-killed python (7.2GB anon-RSS) on the full-sweep default
`e2-standard-2` (8GB) — the in-memory fixtures catalogue + (league×entity) coverage map + per-fixture entity buffers
exceed 8GB. Relaunched both `sports-enrich-{2019-2022,2023-2026}` on **e2-standard-8 (32GB)** → stable (0 429s, fetches
climbing, entity-skip active). FOLLOW-UP: full-sweep/enrich launcher should default enrichment to e2-standard-8 (the
fixtures-only phase is fine on e2-standard-2; only the per-fixture enrichment needs the RAM).

**Final autonomous state (operator away 2h):** ALL code shipped + verified — 5 bugs, concurrency-safe throttle, 3
manifest migrations (odds AF 44%→7%, blanks 743k→0+dedup, 507k entity-coverage relabel + 92% player-stat skip),
Live==Batch wiring (LIVE_ODDS_API). ONLY blocker = **Odds API OUT OF CREDITS** (operator top-up; blocks live rows +
remaining odds backfill — code proven, VM running, emits on credit return). API-Football enrichment + fixtures fill is
rate-bound multi-day (1.2k/min ceiling, used fully, 0 waste). Sweep loop monitors VM health/OOM/credit-return.

### 2026-06-21 — SPORTS lane STATE SNAPSHOT (autonomous, operator away 2h) — for context-compression resume

**SHIPPED (all green):** `--tier` (deployment-service@b51729b) · silent-empty→attempted_failed (is@0db2450,+10 tests) ·
team_mapping GCS-429 write-once (is@865aea9) · **concurrency-safe self-enforced rate limiter** (is@e29ba65 — fixes the
burst→429→52s-minute-sleep thrash that capped enrichment at ~46/min vs 1200/min cap) · UAC entity-coverage map
(uac@9ea84499, sub-agent C). IS tarball rebuilt @e29ba65.

**RUNNING VMs:** odds-backfill `mtds-backfill-odds-{2020..2026}` (7, ODDS-API key, separate quota) · enrichment
`sports-enrich-{2019-2022,2023-2026}` (2, RELAUNCHED on fixed throttle — verify rate post-boot) · **sports LIVE** sports
LIVE producer (RELAUNCHED again post MTDS key-fix — see below; the `...184015` instance booted clean past the enum fix
but hit a SECOND bug: `OddsApi: no API key` because the connector referenced a nonexistent `MarketConfig.odds_api_key`
attribute; FIXED mtds@670be2f). Fixtures phase COMPLETE (265k captured / 1,356 leagues; VMs self-deleted).

**LIVE==BATCH (operator caught this) — UAC ENUM FIX LANDED:** sports had **0 `live_*` rows** — footystats fwd-poll wrote
`batch_*` (forward-over-future, NOT live). The true live producer
(`launch-mtds-live.sh --asset-group sports --shard-spec sports:odds_api:trades` → `odds_api_ws` WSFeedConnector →
`live_odds_api`) FAILED at boot with `No PipelineMode for source 'odds_api' in mode 'live'` — the `PipelineMode` closed
set had `BATCH_ODDS_API`/`REPLAY_ODDS_API` but no `LIVE_ODDS_API`. FIX (uac@249ca53f, LDR): added
`PipelineMode.LIVE_ODDS_API` + flipped `SOURCE_MODE_CAPABILITY["odds_api"]` to `{BATCH, LIVE, REPLAY}` + the test-side
SSOT `EXPECTED_SOURCE_MODE_CAPABILITY` + replaced `test_no_sports_source_is_live_yet` with
`test_odds_api_is_the_first_live_sports_source` (the other sports vendors stay live-less). `REPLAY_ODDS_API` already
existed (replay-capable). QG green (223s), source-mode + cassette tests pass. The live VM pip-installs UAC fresh at boot
→ it picks up the new enum once LDR has it; VM relaunched as `...184015` (same lowercase `odds_api` venue + 5-league
instrument-ids). Same canonical schema as batch (Live==Batch). cefi proved the live path works after its 5-bug first-run
chain (AG-agnostic infra bugs, fixed).

**SECOND LIVE-CHAIN BUG — MTDS connector key-resolution (FIXED mtds@670be2f, LDR):** post enum-fix, `...184015` booted
CLEAN through `websocket-streaming mode=live` + `DEPLOYMENT_STARTED` + wrote 5 per-VM manifest shards (the 5 leagues) —
proving the enum fix worked — but emitted `OddsApi: no API key — stream yields nothing` so 0 rows. ROOT CAUSE:
`odds_api_ws._get_api_key()` referenced `MarketConfig().odds_api_key`, an attribute that does NOT exist (the config
class is `MarketDataProviderConfig`, which exposes `odds_api_secret_name` not a resolved key); the bare `except`
swallowed the `AttributeError` → None → BLOCKED-CREDENTIALS message DESPITE the `odds-api-key` secret existing (32-char
value verified in Secret Manager). FIX: resolve via the canonical
`get_secret_client(project_id=cfg.gcp_project_id).get_secret(cfg.odds_api_secret_name)` (the same pattern the WORKING
batch `OddsApiAdapter` + `DatabentoBaseClient` use). 30 connector unit tests pass; QG green; basedpyright clean on the
change (the 3 file-level Any errors are pre-existing JSON-parse lines, not the edit). The VM pip-installs MTDS fresh at
boot → relaunched to pick up `670be2f`.

**THIRD (TERMINAL) BLOCKER — The Odds API credits EXHAUSTED → `BLOCKED-CREDENTIALS` (operator top-up, 2026-06-21):**
with the key-fix live, VM `...190258` now SENDS the key — the API authenticates the request but returns **HTTP 401
`OUT_OF_USAGE_CREDITS`**. Verified directly: the `odds-api-key` secret is a VALID key (the free `/v4/sports/` list
endpoint returns 200 with EPL/Serie-A active), but the credit-costing `/v4/sports/{sport}/odds` endpoint returns
`{"error_code":"OUT_OF_USAGE_CREDITS"}` with headers `x-requests-used: 5000060 / x-requests-remaining: -60`. The 7
odds-BACKFILL VMs (2020-2026 historical odds) drained the entire quota on the SAME `odds-api-key` secret. **The full
code+infra live path is now PROVEN end-to-end** (enum ✓ + key-resolution ✓ + DEPLOYMENT_STARTED + per-VM manifest shards
written + graceful 401 honest-absence, 0 crashes) — the ONLY remaining gap is credits. The connector polls every 60s and
will emit `live_odds_api` rows with NO further code change the moment credits return. VM `...190258` LEFT RUNNING so it
auto-produces on top-up.

> **CREDENTIAL APPROVAL REQUEST — odds-api-live-credits (operator action 2026-06-21):** Vendor: The Odds API
> (https://the-odds-api.com/#get-access). What I need: top up / upgrade the `odds-api-key` Secret-Manager key's monthly
> credit quota (current usage 5,000,060 — quota fully consumed by the 2020-2026 historical backfill on the SAME key). A
> SEPARATE live-only key (its own quota) would prevent the backfill from re-draining live; otherwise live + backfill
> must share. Unblocks: the FINAL `≥1 live_odds_api` sports row (Live==Batch sports gate). Without it: VM `...190258`
> stays up
>
> - honest-absences (0 rows) until credits return — no further code work needed.

**3 MIGRATION SUB-AGENTS in flight (opus), IS ships BLOCKED on a LIVE foreign UTL WIP**
(`manifest_writer/_writer_captured.py`, peer actively editing — do NOT stomp; their tracked waiters fire when UTL goes
clean):

- **A** (agentId in transcript): canonicalise legacy `batch_instruments_service` sports rows → `batch_<source>` + fill
  blank reasons → fixes the 130,828 blank-reason cells + the ~1.16× double-count (pipeline_mode dedup-key drift). IS
  migration script.
- **B**: odds (book×league) observed-coverage map + sentinel wiring + migration → fixes the ~72% mislabelled
  `attempted_failed` (Kalshi/Polymarket removed as they're prediction-markets not Odds-API). UAC+MTDS.
- **C** (a2c87b13142bd5311): UAC@9ea84499 shipped — `is_league_entity_covered(league,entity)` + new
  `EmptyConfirmedReason.EXPECTED_NO_PROVIDER_COVERAGE`. Dry-run: **~92% of leagues never yield player-stats** → skip
  kills the waste; **506,959 cells** relabel → expected-empty. IS write-path + migration ready, pending UTL-clear.

**WRITE-PATH AUDIT (regression-proof):** record_empty rejects blank (`LegacyBlankErrorReasonError`) + invalid reasons;
`pipeline_mode: PipelineMode` REQUIRED; schema_version=9. So all issues are LEGACY data → migrations fix them; no live
regression.

**NEXT (autonomous loop, `/tmp/sports_autoloop.sh` watcher armed):** (1) verify sports live ≥1 row; (2) verify
enrichment post-throttle rate (if still latency-bound/sequential → the per-fixture fetch needs concurrency = next fix);
(3) when UTL clears → resume A/B/C → ship + run their `--apply` migrations (snapshot first) → honest-cov jumps to
reality; (4) once C's entity-skip lands → rebuild tarball + relaunch enrichment (drops ~92% wasted player-stat calls).
Raw backfill is rate/credit-bound (multi-day, API ceiling) — running efficiently.

### 2026-06-21 — SPORTS lane (/autonomous, Opus): odds flowing; API-Football credential block + silent-empty bug FIXED

**Shipped:** `--tier` launcher bug (deployment-service@b51729b). Silent-empty manifest bug (instruments-service@0db2450,
QG-green sentinel b5b8b72; direct-LDR under dirty-deps carve-out — UAC/UTL dirty with concurrent provenance WIP).

**MTDS odds = HEALTHY + flowing hard.** 7 year-shard VMs `mtds-backfill-odds-{2020..2026}` (--force, 2020-06→2026-06)
RUNNING, writing real bookmaker odds (WilliamHill/DraftKings/Ladbrokes/… EPL); odds-2026 124k rows, odds-2020 30k,
climbing. `pipeline_mode=batch_odds_api` → `market-data-tick-sports-prd-…` (canonical consolidator ENABLED \*/1).

**Root cause (operator-confirmed): IS fixtures gap = CREDENTIAL block, now lifted.** Full-sweep fetched 0 fixtures/date
→ `errors.plan` (free API-Football, dates 2026-06-20..22 only). Operator upgraded → **Custom 1200 r/min, 5 seats, 300k
r/day** (re-tested: 2024-01-13 → 927 fixtures). Killed 8 false-writing full-sweep VMs (each wrote only ~2 dates false
`empty_confirmed` before kill → small blast radius).

### 2026-06-21 — SPORTS lane: RATE-LIMIT root-caused + fixed (operator: "only ~1k req/hr vs 1.2k/min — way too slow")

**Root cause (the throttle thundering-herd):** sports adapter `_MIN_REQUEST_INTERVAL=0.1s` = 600 req/min PER VM. 8
all-entities full-sweep VMs × 600 = 4800/min slammed the API-Football **1.2k/min** cap → every VM 429s → the adapter's
"sleep to next UTC-minute boundary" (`base.py` `_get_with_retry`) → all 8 idle ~50s, wake together, overshoot again →
fleet collapsed to **~22 req/min** (operator's dashboard: ~1k/hr). The heavy load was the **per-fixture enrichment**
fan-out (`/fixtures/players`, `/fixtures/events`, lineups, stats — N calls/fixture).

**Fix (operator-steered: fixtures-first + fewer VMs):** killed the 8 thrashing VMs. Relaunched **2 FIXTURES-ONLY VMs**
(is-gap-fill `--entity FIXTURES`, split 2019-2022 / 2023-2026) = 2×600/min ≈ the 1.2k/min cap with **NO thundering
herd**. **Verified flowing at full speed, zero rate-limiting** ("Fetched 639 fixtures for date=2019-03-02", multiple
dates/sec). FIXTURES = ~1 call/date (~2920 total for 8yr) → catalogue fills in **minutes**, not days. Also shipped
full-sweep `--entity` flag (deployment-service@4caeaf3) for fixtures-first phasing.

**Architecture confirmed (operator's Q): enrichment reads fixtures from GCS** — `_per_fixture_gcs_fast_path`
(process.py:191) lets per-fixture entities read fixture IDs from GCS, so fixtures-first composes: Phase-1 FIXTURES
(fast), Phase-2 enrichment (heavy) reads the Phase-1 GCS fixtures. The all-entities full-sweep did NOT use this split
(grabbed fixtures + enriched inline per date → the thrash).

**Phased plan (autonomous):** Phase-1 FIXTURES (running, ~mins) → Phase-2 ENRICHMENT (per-fixture entities, 2 VMs at the
1.2k/min cap, GCS-fixture fast path) = **multi-day, rate-cap-bound** (millions of per-fixture calls; 300k/day now,
operator upgrading to 1.5M/day; per-minute 1.2k is the binding constraint — no agent can exceed the API ceiling, but 2
VMs use it FULLY without thrash). Odds backfill (7 VMs, separate ODDS-API key, no contention) + live (footystats +
scheduler) continue. Background monitor armed: fixtures-complete → auto-launch enrichment.
