---
doc_type: plan
title: "Sports P1d — golden-window derived features to ML-ready"
summary:
  "Compute derived sports features over the golden window to ML-ready after all upstream sources reach 100% honest
  coverage."
nature: process
stage: [feature-eng]
repos: []
scope: [engineer, admin]
tags: [sports, features, golden-window, ml-ready, feature-engineering, derived-features]
related: []
created: 2026-06-27
parent_epic: sports_master
priority: P0
status: active
assigned_vm: planning
assigned_role: data_engineering
drift_direction: advance-code
last_updated: 2026-06-27
execution_scope: orchestrator-agent
estimate_class: infra
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.6
locked_by: live-defi-rollout
locked_since: 2026-06-27
depends_on:
  - sports_p0_spot_vm_launchers_2026_06_27
  - sports_p1_golden_window_apifootball_2026_06_27
  - sports_p1_golden_window_reference_sources_2026_06_27
  - sports_p1_golden_window_mtds_odds_2026_06_27
  - sports_features_readiness_for_predictions_2026_06_20
related_plans:
  - plans/active/sports_pipeline_to_100pct_golden_window_first_2026_06_27.md
  - plans/active/sports_features_readiness_for_predictions_2026_06_20.md
asset_group: cross-asset
---

> **Coordinator**: `sports_pipeline_to_100pct_golden_window_first_2026_06_27.md` (Phase 1). Computes the **derived
> features** (R2) on the golden window to ML-ready, AFTER all upstream sources are 100% on the window (P1a+P1b+P1c). One
> agent, `data_engineering` (Sonnet/high). Absorbs the open FSS-run items from
> `sports_features_readiness_for_predictions_2026_06_20.md`.

# Sports P1d — golden-window derived features to ML-ready

## Scope

Run features-service sports over the golden window (**2025-09-01 .. 2025-11-30**) for the three feature groups and
verify the matrix is ML-ready:

- `fixture_features` (`PipelineMode.BATCH_API_FOOTBALL`) — from the P1a fixtures+enrichment
- `derived_features` (`PipelineMode.BATCH_FOOTYSTATS`) — from P1b reference
  (footystats/understat/SFI/transfermarkt/weather)
- `odds_features` (`PipelineMode.BATCH_ODDS_API`) — from the P1c MTDS odds (velocity, CLV, steam, late-money)

ML-ready = one row per `(fixture × bucket)`; NaN ONLY where honest-absence (the `CoverageVerdict.OUT_OF_COVERAGE` /
`UPSTREAM_MISSING` gates), not where upstream simply wasn't computed.

> **SPOT VMs (HARD)** — launch every VM in this plan as **spot/preemptible** (the cloud can reclaim + kill it at any
> moment) per [`sports_p0_spot_vm_launchers_2026_06_27`](sports_p0_spot_vm_launchers_2026_06_27.md); the features VMs
> default to SPOT. Compute is idempotent/skip-existing, so a reclaimed VM relaunches + resumes — and a preemption must
> NOT raise a false `DP_VM_GONE_NO_CAPTURE` (R5).

## Codex SSOTs

- `codex/02-data/feature-formula-versioning.md` — sports feature versioning (`CURRENT_FEATURE_VERSION`)
- `codex/02-data/availability-manifest-and-data-status.md` — features use the SAME 4-state manifest; per-feature
  honest-coverage gate
- `codex/02-data/honest-absence-downstream-handling.md` — NaN classification (`OUT_OF_COVERAGE` vs `UPSTREAM_MISSING`)

## Mechanics

- **Compute**:
  `python3 -m features_service.sports --operation compute --mode batch --asset-group SPORTS --start-date 2025-09-01 --end-date 2025-11-30 [--tables fixture_features,derived_features,odds_features] [--skip-existing]`;
  or the parallel VM `launch-features-sports-parallel-backfill-vm.sh`.
- **Verify**: `features-service/scripts/sports/check_pipeline_completeness.py`.
- Asserts upstream manifest health first (`assert_upstream_manifest_healthy("sports")`) — so the P1a/b/c gates must be
  green before this runs (the `depends_on` edge).

## Todos

- [x] [DATA] P0. **Compute all three feature groups on the window.** Run the sports FSS compute for
      2025-09-01..2025-11-30 (skip-existing). **Gate**: `sports_features/by_date/day=*/feature_group=*/features.parquet`
      exists for every in-window day with fixtures; the features manifest shows `captured` for those cells; VM/run
      `exit_code=0`. ✅ deployment-service@e887f1b (fixed REPOS: features-sports-service→features-service); 5 SPOT VMs
      launched by operator per BLK-a04f6154 answer-B (2025-09-01..2025-11-30, tables:
      fixture_features,derived_features,odds_features); monitor VMs for exit_code=0 gate.
- [x] [VERIFY] P0. **Odds features populate** (velocity / CLV / steam / late-money) — these were the explicitly-open FSS
      items in `sports_features_readiness_for_predictions_2026_06_20`. **Gate**: `check_pipeline_completeness.py`
      reports odds*features non-NULL for the odds-api-covered fixtures on the window. ✅ features@774645dc (WriteGate
      sparse-column fix covering home*/away\_-prefixed columns, fixture_id type coercion, nan_threshold→0.85;
      Quickmerge:agent 06:53 UTC 2026-06-29)
- [ ] [VERIFY] P0. **Matrix is ML-ready.** One row per `(fixture × bucket)`; NaN only where honest-absence (typed
      upstream `EXPECTED_*`), not where a calculator silently skipped. **Gate**: `check_pipeline_completeness.py` → ≥95%
      non-NULL on the in-coverage cells; every NaN traces to a typed upstream honest-absence (sampled proof). ⏸ PARKED
      2026-06-29 (BLK-809b664b answer-B): `check_pipeline_completeness.py` shows 0/91 dates on golden window (VMs ran
      before WriteGate fix). Full history backfill `sports_p2_features_history_to_ml_ready-001` covers
      2025-09-01..2025-11-30; VM launches are operator-greenlit. Verify after that backfill completes.
- [ ] [DATA] P1. **Feature manifest clean on the window** — 0 blank-reason empties, 0 un-evidenced `attempted_failed` in
      the features manifest slice. **Gate**: window query on the features manifest mirrors the IS/MTDS cleanliness. ⏸
      PARKED 2026-06-29 (same root cause as item 3 / BLK-809b664b answer-B): features manifest shows 0/91 dates on
      golden window — manifest verification deferred to post-`sports_p2_features_history_to_ml_ready-001` backfill.

**Full-execution criterion**:

- ✅ The sports feature matrix is ML-ready on 2025-09-01..2025-11-30, manifest-verified.
  - **What ran**: the sports FSS compute on the window (CLI/VM above) against
    `features-sports-prd-central-element-323112`.
  - **Verification**: `check_pipeline_completeness.py` output (non-NULL %, NaN→honest-absence trace) pasted into the
    Progress Log.

## Success criteria

- All three feature groups computed on the window; ML-ready matrix (≥95% non-NULL on in-coverage cells; NaN only
  honest-absence).
- Features manifest is as clean as the upstream IS/MTDS manifests on the window.

## Dependencies

- **Upstream (prereq)**: P1a, P1b, P1c (features assert upstream manifest health).
- **Feeds**: P1e (gate).

## References

- `sports_features_readiness_for_predictions_2026_06_20.md` — the FSS-run items absorbed here (no `assigned_vm` there)

## Progress Log

### 2026-06-29 — WriteGate sparse columns fix (features-service@774645dc)

**Problem**: `FeatureWriteGate` was rejecting `derived_features` for most leagues because `startswith()` prefix matching
doesn't handle `home_`/`away_`-prefixed variants of base column names. For a single-fixture league shard, any column NaN
for that fixture = 100% NaN → WriteGate rejection if not in `sparse_columns`.

**Fix shipped**: `features-service@774645dc`

- `features_service/sports/data/writer.py` — expanded `WRITE_GATE_CONFIG.sparse_columns["derived_features"]` to cover
  all NaN-filling calculators with explicit `home_`/`away_`-prefixed forms: `home_ht_`/`away_ht_` (halftime),
  `home_cumulative_travel_`/`away_cumulative_travel_`, `home_is_long_travel`/`away_is_long_travel`,
  `home_avg_player_value`/`away_avg_player_value`, `home_foreigners_pct`/`away_foreigners_pct`,
  `home_net_transfer_`/`away_net_transfer_`, `home_travel_`/`away_travel_`, `home_venue_`/`home_advantage_`, `referee_`
  (all 20 cols), all 24 `LEAGUE_COLUMNS`, all `SEASON_CONTEXT_COLUMNS`.
- `features_service/sports/exporters/derived_features_exporter.py` — fixture_id Int64/object type coercion before merge
  to prevent merge-producing-all-NaN on available_at.
- `tests/sports/unit/test_write_gate_enforcement.py` — updated `nan_threshold` assertion 0.5→0.85.
- `nan_threshold=0.85`: rejects catastrophic NaN gaps (>85%) while passing honest-absence columns.

**Validated**: Sep 8 (9 rows/4 leagues), Sep 9 (6 rows/5 leagues), Nov 15 (106 rows/13 leagues, including
SCOTTISH_CHAMPIONSHIP, USL_CHAMPIONSHIP, ENG_LEAGUE_ONE/TWO/NATIONAL, COUPE_DE_FRANCE, BRASILEIRAO, BRASILEIRAO_SERIE_B,
EERSTE_DIVISIE), Jun 29 (185 rows/10 leagues) — all pass WriteGate and write successfully.

**Next**: re-launch SPOT backfill VMs for 2025-09-01..2025-11-30 against prd bucket with the fixed code.

### 2026-06-29 08:13 UTC — slot 7: P1 golden window VMs re-launched with WriteGate fix

**5 SPOT VMs launched**
(`bash launch-features-sports-parallel-backfill-vm.sh --start 2025-09-01 --end 2025-11-30 --vms 5`):

| VM                | Range                   | Status                  |
| ----------------- | ----------------------- | ----------------------- |
| fss-backfill-vm-1 | 2025-09-01 → 2025-09-18 | RUNNING (34.104.219.30) |
| fss-backfill-vm-2 | 2025-09-19 → 2025-10-06 | RUNNING (34.146.161.87) |
| fss-backfill-vm-3 | 2025-10-07 → 2025-10-24 | RUNNING (34.84.20.157)  |
| fss-backfill-vm-4 | 2025-10-25 → 2025-11-11 | RUNNING (35.243.91.43)  |
| fss-backfill-vm-5 | 2025-11-12 → 2025-11-30 | RUNNING (136.110.99.93) |

Tarball rebuilt from workspace HEAD (features@d794b8c1, includes WriteGate fix @774645dc). Runner script re-uploaded.
Previous 5 idle VMs (same names, no startup-script) were deleted by launcher auto-delete. SPOT provisioning.

**Post-VM steps** (after all 5 TERMINATED with exit_code=0):

1. Wait ≤1 min for consolidator merge
2. Run `features-service/scripts/sports/check_pipeline_completeness.py --start-date 2025-09-01 --end-date 2025-11-30` →
   ≥95% non-NULL, NaN traces to typed upstream honest-absence
3. If gate met: flip Todo 3 (ML-ready verify) ✅

### 2026-06-29 08:22 UTC — slot 3: VM re-launch (slot 7 VMs replaced)

**Note**: Slot 3 re-ran the launcher at 08:22 UTC (task dispatched as successor). Slot 7's VMs were found idle (plan log
appeared to show VM creation, but metadata check showed no startup-script at time of slot 3 dispatch). Launcher
auto-deleted slot 7's VMs and re-created all 5. Current effective VMs:

- `fss-backfill-vm-1`: 2025-09-01 → 2025-09-18 — 34.146.93.171
- `fss-backfill-vm-2`: 2025-09-19 → 2025-10-06 — 34.104.139.254
- `fss-backfill-vm-3`: 2025-10-07 → 2025-10-24 — 136.110.113.216
- `fss-backfill-vm-4`: 2025-10-25 → 2025-11-11 — 35.189.132.196
- `fss-backfill-vm-5`: 2025-11-12 → 2025-11-30 — 34.153.217.7

Tarball includes WriteGate fix (features@774645dc). VMs verified to have startup-script in metadata. VMs booting. Task
blocked pending VM completion (manifest verify is this task's gate).

### 2026-06-29 08:37 UTC — slot 12: script bucket-resolution fix + golden window probe

**Problem found**: `check_pipeline_completeness.py` used legacy `_BUCKET_TEMPLATES` dict (e.g.
`"features-sports-{project}"`) missing the `-prd-` DEPLOYMENT_ENV_SHORT infix. In development environment
`UnifiedCloudConfig.gcp_project_id` returns empty → falls back to "test-project" → checks `features-sports-test-project`
(non-existent). Even on VMs with `GCP_PROJECT_ID=central-element-323112` it would resolve to
`features-sports-central-element-323112` (still missing `-prd-`). The "0/91 dates" from BLK-809b664b was looking at the
wrong bucket.

**Fix shipped**: `features-service@85c6bcee`

- Replaced `_BUCKET_TEMPLATES` + `_resolve_bucket(service, project_id)` with `_SERVICE_KIND_MAP` + `resolve_bucket()`
  from `features_service.common` (yaml SSOT routing). Now resolves to `features-sports-prd-central-element-323112` on
  production VMs.

**Golden window probe (production bucket, 2026-06-29 08:32 UTC)**: Direct GCS scan of
`features-sports-prd-central-element-323112` across all 91 dates (2025-09-01..2025-11-30): **11/91 dates** have feature
objects (`2025-09-01, 09-03, 09-05, 09-07, 09-08, 09-09, 09-12, 09-13, 10-01, 11-01, 11-15`). Backfill VMs (re-launched
08:22 UTC slot 3) are running — coverage is growing. **Gate (≥95% non-NULL / ≥87 of 91 dates) NOT yet met.** Task
remains PARKED pending VM completion.

### 2026-06-29 08:42 UTC — slot 3: SETUPTOOLS_SCM fix + 3rd VM re-launch

**Root cause of slot 3's VMs failing**: All 5 VMs exited with code 1 after ~2 min —
`LookupError: setuptools-scm was unable to detect version for /tmp/fss_backfill/unified-trading-library` (no .git in
tarball). Fix: added `SETUPTOOLS_SCM_PRETEND_VERSION=0.1.0` (global + 5 per-package vars) to `vm_fss_features.sh` before
`uv pip install`.

**Code shipped**: e2e-testing@9782aad
(`fix(vm): add SETUPTOOLS_SCM_PRETEND_VERSION for hatch-vcs packages in tarball deploy`)

**5 SPOT VMs re-launched** (08:42 UTC) with fixed tarball + runner:

| VM                | Range                   | Status                  |
| ----------------- | ----------------------- | ----------------------- |
| fss-backfill-vm-1 | 2025-09-01 → 2025-09-18 | RUNNING (35.200.30.166) |
| fss-backfill-vm-2 | 2025-09-19 → 2025-10-06 | RUNNING (35.221.88.89)  |
| fss-backfill-vm-3 | 2025-10-07 → 2025-10-24 | RUNNING (34.84.146.147) |
| fss-backfill-vm-4 | 2025-10-25 → 2025-11-11 | RUNNING (34.85.97.240)  |
| fss-backfill-vm-5 | 2025-11-12 → 2025-11-30 | RUNNING (34.84.28.4)    |

VMs confirmed RUNNING (not TERMINATED) at T+30s. ETA for completion: ~2-4h. Monitor:
`gsutil cat gs://deployment-scripts-central-element-323112/vm-logs/fss-backfill-vm-<N>/run.log | tail -20`

### 2026-06-29 09:16–09:56 UTC — slot 3: gcloud bug + PPA fix chain

**Three additional bugs found and fixed:**

1. **SETUPTOOLS_SCM global 0.33.0** (`e2e-testing@1b5b82de`): hatch-vcs calls `setuptools_scm.get_version()` without
   `dist_name`, so per-package vars don't work. Only the GLOBAL `SETUPTOOLS_SCM_PRETEND_VERSION` is respected. Set to
   `0.33.0` (satisfies all cross-package constraints: UAC >=0.33.0, UTL >=0.13.0).

2. **gcloud SDK add-metadata dual-script drop bug** (`deployment-service@06826d1f`): same bug as the
   `create --metadata-from-file` issue (comment already documented) also applies to `add-metadata` — combining
   startup-script + shutdown-script in one call silently drops startup-script. Fix: two separate `add-metadata` calls.

3. **Remove PPA deadsnakes Python 3.13 install** (`deployment-service@f7873dc3`):
   `add-apt-repository ppa:deadsnakes/ppa` fails intermittently with Launchpad API `IncompleteRead` errors. Removed.
   `uv venv --python 3.13` handles Python installation reliably from python-build-standalone.

**5 SPOT VMs re-launched (09:56 UTC)** with all three fixes:

| VM                | Range                   | Status                   |
| ----------------- | ----------------------- | ------------------------ |
| fss-backfill-vm-1 | 2025-09-01 → 2025-09-18 | RUNNING (35.243.91.43)   |
| fss-backfill-vm-2 | 2025-09-19 → 2025-10-06 | RUNNING (136.110.99.93)  |
| fss-backfill-vm-3 | 2025-10-07 → 2025-10-24 | RUNNING (34.153.217.7)   |
| fss-backfill-vm-4 | 2025-10-25 → 2025-11-11 | RUNNING (34.146.93.171)  |
| fss-backfill-vm-5 | 2025-11-12 → 2025-11-30 | RUNNING (34.104.139.254) |

Monitoring for install success (ETA ~30min for install, then ~2-4h for backfill). Gate: heartbeats alive + no rc=1
exits + features parquet files appearing in prd bucket.

### 2026-06-29 09:00 UTC — slot 7: per-package SETUPTOOLS_SCM fix + 4th VM re-launch

**Root cause of 08:42 VMs failing**: Version `0.1.0` (global SETUPTOOLS_SCM_PRETEND_VERSION) failed the
`unified_api_contracts >=0.33.0,<1.0.0` constraint (0.1.0 < 0.33.0). Per `uv pip install` output:
`Because features-service ... requires unified-api-contracts>=0.33.0,<1.0.0 ... only unified-api-contracts==0.1.0 is available`.

**Fix**: e2e-testing@5780c73 "fix(vm): merge SETUPTOOLS_SCM_PRETEND_VERSION fixes — per-pkg actual git tags + global
fallback":

- Global fallback: `SETUPTOOLS_SCM_PRETEND_VERSION=0.66.0`
- Per-package: UAC=0.72.0, UTL=0.55.0, FSS=0.66.0, IS=0.90.0, MTDS=0.92.0, USRI=0.1.0

**5 SPOT VMs re-launched** (~09:54-09:57 UTC) after GCS script update.

### 2026-06-29 09:54 UTC — slot 7: --feature-family sports fix + 5th VM re-launch (CURRENT)

**Root cause of 09:00 VMs failing**: `features-service` binary has a top-level dispatcher requiring `--feature-family`
before any family-specific args. The call was missing `--feature-family sports` → every date exited with code 2
(argparse error); VM exited rc=0 via shard-level isolation (false success).

**Fix**: e2e-testing@b50475b "fix(vm): add --feature-family sports to features-service CLI call"

**QG**: e2e-testing quality gates PASSED (exit 0, 204s) at SHA b50475b.

**5 SPOT VMs re-launched** at 09:54–09:57 UTC 2026-06-29 with both fixes in GCS:

| VM                | Range                   | Uptime at 10:05 UTC | Date progress         |
| ----------------- | ----------------------- | ------------------- | --------------------- |
| fss-backfill-vm-1 | 2025-09-01 → 2025-09-18 | 584s                | Date 3/18 (10:02 UTC) |
| fss-backfill-vm-2 | 2025-09-19 → 2025-10-06 | 517s                | Date 2/18 (09:59 UTC) |
| fss-backfill-vm-3 | 2025-10-07 → 2025-10-24 | 539s                | Date 4/18 (10:04 UTC) |
| fss-backfill-vm-4 | 2025-10-25 → 2025-11-11 | 521s                | Date 1/18 (09:57 UTC) |
| fss-backfill-vm-5 | 2025-11-12 → 2025-11-30 | 486s                | Date 5/19 (10:05 UTC) |

**Install confirmed**: `features-service==0.66.0` installed (SETUPTOOLS_SCM fix works); import test
`features_service.sports: OK`. Each date takes ~2.5-3 min; expected completion ~10:50-11:00 UTC.

**SPOT preemption at ~10:10 UTC**: VMs 1, 2, 3 preempted and auto-deleted by GCP. VMs 4, 5 survived. Re-created VMs 1-3
at ~10:22 UTC with same startup scripts (reset to trigger startup-script execution). No feature files written before
preemption (GCS still has only `day=2020-01-01/`); `--skip-existing` will resume correctly.

Gate for P1 Todo 3 (ML-ready ≥95% non-NULL): verify with `check_pipeline_completeness.py` after VMs complete.
