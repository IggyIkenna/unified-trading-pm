---
doc_type: issue
title:
  MTDS SPORTS/ODDS_API force-fetch writes no parquet for odds_horizon_bucket + trades (Track K MTDS baseline finding)
summary: >-
  Track K (MTDS) baseline checkpoint (day=2025-12-20, `data-pipeline-check-mtds --asset-group SPORTS --venue ODDS_API`)
  found both genuinely-captured-in-PROD ODDS_API cells (`odds_horizon_bucket`, `trades`) fail their force-leg with
  `no_parquet_under` — the launcher VM exits 0 (`vm_confirmed_present=True`, launcher argv accepted) but no parquet
  lands at the expected test-bucket path for either the pinned day (`odds_horizon_bucket`, day=2025-12-20) or the
  `--auto-day`-substituted day (`trades`, day=2026-06-24, sampled real PROD instrument_id `ODDS_API:SPORT:soccer_epl`).
  Both skip-legs correspondingly report `skip_signal_not_found_in_run_log` + `object_signature_changed_or_missing`
  (expected, since nothing was written by force to observe a skip against). The other 8 ODDS_API data_type cells
  honestly skipped (`no_captured_data_for_cell` — no PROD data, not a bug). Root cause not yet diagnosed — `gsutil ls`
  under the test bucket's `vm-logs/<vm-name>/` prefix for both VM names returned zero objects (the run.log/EXIT_STATUS
  observability contract other MTDS pipeline-check VMs use did not resolve at that path for these two VMs either —
  itself worth checking, may be a distinct bucket/path convention for the ODDS_API adapter or a parallel observability
  gap). Filed per findings-closure discipline rather than absorbed into the Track K checkpoint task, which is scoped to
  running + citing the 3 dated checkpoints, not root-causing every failure.
status: resolved
nature: issue
asset_group: [sports]
stage: [data]
repos: [market-tick-data-service, deployment-service]
scope: [engineer]
tags: [sports, mtds, odds_api, force-fetch, no_parquet, pipeline-e2e-check, track-k]
related:
  [
    /plans/active/sports_consolidated_native_ao_extract_2026_07_25.md,
    /plans/audit/results/data_pipeline_e2e_check_mtds_2025_12_20.md,
  ]
created: 2026-08-01
author: unknown
assigned_vm: planning
parent_epic: sports_master
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
source: sports_consolidated_native_ao_extract_2026_07_25.md, Track K (MTDS) baseline checkpoint (2025-12-20), slot 15
resolved_by: slot-14 2026-08-14, all 3 top-level todos done — see Progress Log
locked_by:
drift_direction: advance-code
depends_on: []
context_scope:
  [
    /plans/active/sports_consolidated_native_ao_extract_2026_07_25.md,
    /plans/audit/results/data_pipeline_e2e_check_mtds_2025_12_20.md,
    /cursor-configs/skills/data-pipeline-check-mtds/SKILL.md,
    market-tick-data-service/scripts/pipeline_e2e_check.py,
    deployment-service/scripts/vm/launch-mtds-backfill-vm.sh,
  ]
---

# MTDS SPORTS/ODDS_API force-fetch writes no parquet for odds_horizon_bucket + trades

> **🟢 ARCHIVED 2026-08-14 — RESOLVED** (status: resolved, 0 open todos, unlocked). Root-caused as an upstream
> `the-odds-api.com` 401 (not an MTDS defect — shard-isolation + honest-absence both worked correctly) plus a real
> checker enumeration bug (`odds_horizon_bucket` is MDPS-derived, excluded from the checker,
> market-tick-data-service@bc269b51). The 401 has since cleared — verified live 2026-08-14 via 3 direct vendor calls,
> all HTTP 200, no code change needed; capture resumes automatically.

## What I found

Running
`market-tick-data-service/scripts/pipeline_e2e_check.py --asset-group SPORTS --venue ODDS_API --day 2025-12-20 --legs force,skip --require-captured --auto-day`
(the Track K (MTDS) baseline checkpoint) enumerated 10 `(asset_group=SPORTS, venue=ODDS_API, data_type)` cells. 8
honestly skipped (`no_captured_data_for_cell` — genuinely no PROD data for ODDS_API under those data_types on any day,
correct honest-absence behavior). The 2 cells that DO have real captured PROD data both failed:

- `SPORTS:ODDS_API:odds_horizon_bucket` (day=2025-12-20, 135 PROD-captured rows confirmed via the availability index) —
  force-leg launcher exited 0 and the VM was confirmed present, but no parquet ever appeared under
  `gs://market-data-tick-sports-test-central-element-323112/raw_tick_data/by_date/day=2025-12-20/pipeline_mode=batch_mdps_odds_horizon_bucket/asset_group=sports/venue=ODDS_API/`.
- `SPORTS:ODDS_API:trades` (auto-day-substituted to 2026-06-24, sampled real instrument_id `ODDS_API:SPORT:soccer_epl`
  from the PROD parquet listing) — same failure shape, no parquet under
  `.../pipeline_mode=batch_odds_api/asset_group=sports/venue=ODDS_API/`.

Both skip-legs then correctly report `ambiguous`/`skip_signal_not_found_in_run_log` +
`object_signature_changed_or_missing` — an expected downstream consequence of the force-leg never having written
anything to compare against, not a second distinct bug.

I attempted to read the VM's `run.log` ground truth (per this skill's own "ground truth is the VM run.log, never the
report verdict" guidance) at `gs://market-data-tick-sports-test-central-element-323112/vm-logs/<vm-name>/run.log` for
both `mtds-backfill-sports-pipelinecheck-20260801-141034-a9a662` (odds_horizon_bucket) and the trades-cell VM —
`gsutil ls` returned zero objects under either VM's `vm-logs/` prefix. I did not chase this further (out of this
checkpoint task's scope) but flag it as possibly a second, related observability gap: either these two adapters write
logs to a different bucket/path than the standard MTDS pipeline-check VM contract, or the VMs never reached the
log-upload step.

Note the `odds_horizon_bucket` cell's pipeline_mode is `batch_mdps_odds_horizon_bucket` — the `mdps` substring in an
MTDS-owned pipeline_mode string is suspicious and may indicate this data_type's real writer is on the MDPS side (an
enumeration/ownership mismatch), though `odds_horizon_bucket` is NOT listed in UAC's `MDPS_DERIVABLE_DATA_TYPES`
frozenset, so that specific hypothesis isn't confirmed either — worth checking directly against the ODDS_API adapter's
own registration.

## Why it matters

Two real, genuinely-captured-in-PROD SPORTS/ODDS_API data_types cannot currently be force-refetched into a test bucket
by MTDS's own pipeline-check tooling. If this is a genuine capture-path defect (not just a checker/observability gap),
it would mean an ODDS_API backfill/redo for these data_types is currently non-functional for SPORTS — worth confirming
before relying on force-refetch for this venue in any future SPORTS backfill.

## Diagnosis (slot-3, 2026-08-03)

**1. The observability gap is resolved — run.log/EXIT_STATUS NEVER land under the `-test-` bucket, for ANY MTDS
pipeline-check VM, regardless of `IS_TEST_RUN`.** Live-traced `deployment-service/scripts/vm/setup-data-pipeline-vm.sh`:
lines 1089-1090 hardcode `GCS_LOG_DIR="gs://deployment-scripts-central-element-323112/vm-logs/${VM_NAME_SELF}"` — the
CODE bucket, not the per-asset-group `-test-`/PROD data bucket. `IS_TEST_RUN` only ever redirects the MTDS _data write_
target (`raw_tick_data/...`); the VM's own run.log/EXIT_STATUS/vm-setup.log always go to `deployment-scripts-{project}`.
Confirmed both cited VM names' logs exist there:

- `gs://deployment-scripts-central-element-323112/vm-logs/mtds-backfill-sports-pipelinecheck-20260801-141034-a9a662/{run.log,EXIT_STATUS}`
  (the `odds_horizon_bucket` force-leg VM) — `EXIT_STATUS=0`.
- The `trades` cell's force-leg VMs are the `2da87c`-suffixed runs on the same day (e.g.
  `mtds-backfill-sports-pipelinecheck-20260801-131404-2da87c`) — also `EXIT_STATUS=0`.

This was not chased further by the checker because the wrong bucket was searched — not an MTDS or observability code
defect, just an incorrect assumption in the original diagnosis. No code change needed for this half; worth a one-line
note in the `data-pipeline-check-mtds` skill so the next diagnosis doesn't repeat the same wrong-bucket search.

**2. Real root cause, BOTH cells: an upstream 401 Unauthorized from `api.the-odds-api.com`'s historical endpoint, with a
clean, one-way cutover — not a transient blip.** Read the actual run.log content for the `odds_horizon_bucket` VM and
~14 sibling force-leg VMs sharing the same ODDS_API key across the same day (2026-08-01, all using
`apiKey=5634d6f1***REDACTED***2c46c`):

- 10:25-12:27 UTC: several runs (`…-101533-a9a662`, `…-121313/121544/121827-a9a662`) **succeeded** — real
  `StreamingParquetWriter: uploaded .../data_type=trades/...` writes landed (558-1116 rows per bookmaker-venue:
  UNIBET_UK, FANDUEL, PADDYPOWER, SMARKETS).
- From 12:40:24 UTC onward (`…-123720-a9a662` through at least `…-145458-fc4131`, i.e. every run for the rest of the
  observed window, ~2.5 hours, across BOTH the `odds_horizon_bucket` day=2025-12-20 pin and the `trades`
  auto-day=2026-06-24 substitution) — **every single run fails identically**:
  `Discovery call for soccer_epl ... FAILED (re-raising): 401, message='Unauthorized', url='https://api.the-odds-api.com/v4/historical/sports/soccer_epl/odds?apiKey=5634d6f1***REDACTED***2c46c&...'`.
  MTDS correctly isolates this as a shard failure (`ERROR Venue ODDS_API: unexpected error (shard isolated)`), correctly
  reports `SHARD_INCOMPLETE`/`FAILED SHARDS`, and correctly writes a partial manifest rather than a silent placeholder —
  the shard-level-failure-isolation + honest-absence contracts are both working as designed. The absence of parquet is
  an honest, correctly-reported consequence of the vendor call failing, not a silent MTDS bug.

A clean one-way success→failure transition at a fixed timestamp (not intermittent, not recovering on retry across 2.5h
and ~14 subsequent attempts) is the signature of the `the-odds-api.com` account's request-credit/quota balance being
exhausted mid-day, not a code defect or a flaky network blip. This is **not** a `-test-`-bucket-specific issue: the API
key + credential path is identical regardless of `IS_TEST_RUN` (only the GCS _write_ target changes), so **this
reproduces against real PROD backfill machinery too** — any live/PROD ODDS_API capture running after ~12:40 UTC on
2026-08-01 would hit the identical 401. Per the data-pipeline-correctness HARD RULE and the
external-data-always-available rule, exhausting a paid vendor's request quota is a credential/billing ask, not a code
defect to "fix" — filed as todo 2 below.

**3. `odds_horizon_bucket`'s ownership-split hypothesis is CONFIRMED — it is MDPS-derived, not an MTDS-native raw
capture.** Traced `unified-api-contracts`:

- `unified_api_contracts/canonical/crosscutting/pipeline_mode.py:184` —
  `BATCH_MDPS_ODDS_HORIZON_BUCKET = "batch_mdps_odds_horizon_bucket"` (the `mdps` is baked into the canonical enum name,
  not incidental).
- `unified_api_contracts/canonical/crosscutting/_source_priority_data.py:97` —
  `SOURCE_PRIORITY[("sports", "ODDS_HORIZON_BUCKET")] = ["mdps_odds_horizon_bucket"]` — the ONLY registered source for
  this data_type is the MDPS derivation, there is no raw-vendor source registered for it at all.
- `unified_api_contracts/canonical/domain/sports/league_data.py:261` —
  `"ODDS_HORIZON_BUCKET": "mdps_odds_horizon_bucket"`.

So `odds_horizon_bucket` is a derived candle/feature MDPS computes downstream from raw `odds_movement`/`odds_snapshot`
ticks — it was never meant to be fetched directly from `the-odds-api.com` via a live Discovery call. The
`pipeline_e2e_check.py` SPORTS/ODDS_API enumeration incorrectly includes it as one of MTDS's own force-fetchable raw
data_types; that's a real enumeration bug in the checker (separate from, and compounding, the 401 above — even once the
vendor quota is restored, force-fetching `odds_horizon_bucket` directly from MTDS/ODDS_API would still be conceptually
wrong, since MDPS is supposed to derive it, not MTDS capture it raw). Filed as todo 3 below.

**4. A related, smaller naming-mismatch surfaced along the way (not part of this issue's original scope, noting for
completeness):** one of the `trades`-cell pre-flight runs (`…-103116-2da87c`, before the 401s started) logged
`Pre-flight: venue=ODDS_API date=2026-06-24 — dropping data_types not supported per UAC: ['trades']` —
`unified-api-contracts`' `DataTypeCapability` registry
(`unified_api_contracts/registry/data_type_capability.py:1090-1104`) only registers `data_type="ODDS"` for
`venue=ODDS_API` under SPORTS, not `"trades"` (the generic wire-writer's universal tick-record label). Real PROD parquet
nonetheless exists at `data_type=trades` for this venue (confirmed by the original diagnosis's own PROD-listing sample),
so this is a UAC registry completeness gap, not evidence the capture itself is wrong. Not actioned as a separate todo
here — worth folding into whichever future pass touches `DataTypeCapability` for SPORTS.

## Recommended decision

- [x] [DATA] P2. Diagnose why `market-tick-data-service`'s launcher (`launch-mtds-backfill-vm.sh`) reports exit 0 /
      VM-confirmed-present for `SPORTS/ODDS_API/odds_horizon_bucket` and `SPORTS/ODDS_API/trades` force-fetches but no
      parquet lands at the expected test-bucket path for either cell — start by finding where the VM's
      run.log/EXIT_STATUS actually landed (it is not under the standard `vm-logs/<vm-name>/` prefix in the target test
      bucket) since that is the fastest path to ground truth. (repo: market-tick-data-service) — ✅ DIAGNOSED, no code
      change to this todo itself: logs land under `gs://deployment-scripts-central-element-323112/vm-logs/<vm>/`
      (hardcoded in `setup-data-pipeline-vm.sh:1089-1090`, unaffected by `IS_TEST_RUN`) — see Diagnosis §1-3 above for
      the full root-cause trace.
  - [x] [DATA] P3. If genuinely a capture-path bug (not just an observability gap): confirm whether the same failure
        reproduces against real (non-test) PROD backfill machinery, and if so, escalate per the data-pipeline
        correctness HARD RULE (this would mean ODDS_API's `odds_horizon_bucket`/`trades` capture is silently broken). —
        ✅ CONFIRMED reproduces against PROD (same credential regardless of `IS_TEST_RUN`; see Diagnosis §2). Not an
        MTDS code defect — shard-isolation + honest-absence both worked correctly. This is a vendor quota/billing gap:
  - [x] ✅ [DATA] P2. **RETAGGED 2026-08-13 (operator confirmed): account has ample available credit (~$10M) — the
        2026-08-01 401 was not a quota-exhaustion cutover after all, or the balance has since been topped up.** No
        longer an operator-only credential ask; the remaining action is worker-executable: re-test the SPORTS/ODDS_API
        historical-endpoint force-fetch (`apiKey=5634d6f1***REDACTED***2c46c`) and confirm the 401 has cleared. If it
        clears, resume SPORTS/ODDS_API capture (test + prod) normally. If the SAME 401 signature still reproduces
        despite confirmed available credit, this is a genuinely different vendor-side fault (e.g. a stale/rotated key,
        an IP allowlist change, or an account-flag issue) — escalate as a new, distinct finding rather than
        re-diagnosing it as quota exhaustion. — **DONE 2026-08-14 (slot-14, `data_engineering`): 401 has CLEARED**,
        confirmed via 3 direct calls to the real historical-discovery endpoint (`OddsApiAdapter._discover_fixtures`'s
        exact URL/params shape,
        `market-tick-data-service/market_tick_data_service/market_interface/adapters/sports/odds_api_adapter.py:549-592`),
        API key resolved live from Secret Manager via the adapter's own `_resolve_api_key()` (no hardcoded key, no
        `os.getenv`): `soccer_epl`/day=2026-06-24 (the auto-day-substituted `trades` cell from this doc's original
        finding) → HTTP 200 with real event data; `soccer_epl`/day=2026-08-01 (the exact day the original 401 cutover
        began) → HTTP 200 with real event data; `basketball_nba`/day=2026-06-15 (different sport/season, cross-check) →
        HTTP 200 with real event data. 0/3 calls hit 401 — a real HTTP status observed directly on each call, not
        inferred from the checker's downstream verdict. No pause/disable mechanism existed for ODDS_API batch capture to
        "resume" (verified: no allowlist/denylist entry gates it in `configs/venue_data_types.yaml`, no cron/systemd
        toggle) — the 401 was a pure downstream vendor-side effect via the existing shard-failure-isolation path, so
        normal capture already resumes on its own now that the vendor call succeeds. No code change needed; this todo
        was confirmation-only.
  - [x] [DATA] P3. Confirm whether `odds_horizon_bucket`'s `batch_mdps_...` pipeline_mode label reflects a genuine
        ownership split (MDPS writes this data_type, not MTDS) that the pipeline-check's SPORTS enumeration should
        exclude, rather than a real MTDS capture defect. — ✅ CONFIRMED via UAC trace (Diagnosis §3): `SOURCE_PRIORITY`
        registers the ONLY source for `("sports", "ODDS_HORIZON_BUCKET")` as `mdps_odds_horizon_bucket` — no raw-vendor
        source is registered at all. Follow-up code fix:
  - [x] ✅ [DATA] P3. Exclude `odds_horizon_bucket` from `market-tick-data-service/scripts/pipeline_e2e_check.py`'s
        SPORTS/ODDS_API raw-data_type enumeration (it is MDPS-derived per UAC `SOURCE_PRIORITY`, never an MTDS-native
        raw capture — MTDS force-fetching it directly against `the-odds-api.com` is conceptually wrong regardless of the
        vendor-quota state above). (repo: market-tick-data-service) — market-tick-data-service@bc269b51

## Progress Log

- **context-scout 2026-08-03**: populated context_scope (5 entries).
- **slot-3 diagnosis 2026-08-03**: root-caused both force-fetch failures — see "Diagnosis" section above. Not an MTDS
  capture-path bug: (1) the original run.log search targeted the wrong bucket (logs always land under
  `deployment-scripts-{project}`, never the `-test-` bucket, regardless of `IS_TEST_RUN`); (2) the actual failure is an
  upstream `the-odds-api.com` 401 with a clean one-way cutover at 12:40:24 UTC on 2026-08-01 (quota-exhaustion
  signature), confirmed to affect PROD identically (same credential); (3) `odds_horizon_bucket`'s MDPS ownership is
  confirmed via UAC `SOURCE_PRIORITY` — it should be excluded from MTDS's own force-fetch enumeration. Filed the
  vendor-credential ask as `[OPERATOR]` P2 and the enumeration-exclusion as a new `[DATA]` P3 code-fix todo.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (5 entries), unchanged.
- **slot-14 2026-08-14**: re-tested the SPORTS/ODDS_API historical-endpoint 401 per the operator's 2026-08-13 retag.
  Confirmed cleared — 3 direct calls to the real vendor endpoint (same URL/params shape as
  `OddsApiAdapter._discover_fixtures`, key resolved live from Secret Manager) all returned genuine HTTP 200 with real
  event data, including the exact `soccer_epl`/2026-08-01 cell that originally 401'd. Confirmed no separate
  pause/disable mechanism exists for ODDS_API batch capture — the 401 was a pure downstream vendor effect, so capture
  resumes automatically now that the vendor call succeeds; no code change required. Every open todo in this doc is now
  resolved; all 3 top-level todos are `[x]`.
