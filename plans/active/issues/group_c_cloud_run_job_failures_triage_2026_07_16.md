---
doc_type: issue
title:
  "Group-C fleet triage: enumeration + root-cause of Cloud Run jobs failing TODAY on FRESH (post-2026-06-09) images —
  one shipped fix, one live cleanup, three clusters ALREADY tracked elsewhere, two NEW escalated findings"
summary:
  "Follow-up to utl_uac_skew_fleet_audit_2026_07_15.md's 'Group-C' sub-finding (jobs failing today on fresh images —
  definitionally NOT the entitlements import-skew). Enumerated ~29 candidate Cloud Run jobs (instrument-catalogue-regen,
  lifecycle-catalogue-{regen,full}-*, dp-manifest-hygiene-*, *-t1-recon family, paper-*, blrs) via `gcloud run jobs
  list` + `executions list` + `gcloud logging read`, grouped by shared root cause. Result: (1) SHIPPED FIX —
  market-tick-data-service's Dockerfile pinned a UTL base-image digest 2h stale relative to a same-day UAC addition
  (`venue_data_type_has_batch_source`), crashing `market-tick-data-service-{fast,cefi}-t1-recon` at import; bumped the
  pin, rebuilt, verified. (2) LIVE CLEANUP — an orphaned dev-tier scheduler (`uts-dev-instruments-t1-schedule`, not in
  any terraform file) was still firing the RETIRED all-AG instruments-service t1-recon job daily; paused. (3) THREE
  clusters are ALREADY TRACKED by existing issue docs (batch-live-reconciliation-service family / recon-bucket
  producer-chain gap; strategy-service-t1-recon date-arg gap; paper-stream + paper-engine-run failing as a DOWNSTREAM
  symptom of the already-escalated DeFi collection-outage doc) — cross-referenced, not re-fixed. (4) TWO NEW findings
  escalated rather than force-fixed: cefi/defi lifecycle-catalogue-regen hitting CATALOGUE_SHRINK_BLOCKED on duplicate
  perp-lineage merge-keys (added as an update to dp_catalog_not_running_sports_prediction_2026_07_15.md), and a
  cross-cutting UTL `_adapter.py::_build_io()` gap where BATCH mode has no default-date-to-today fallback (LIVE mode
  does) — plausibly the SAME root cause behind the already-tracked strategy-service date-arg failure, now also hitting
  market-tick-data-service-cefi-t1-recon. Two jobs confirmed genuinely dormant/superseded, not bugs:
  `instrument-catalogue-regen` (PAUSED scheduler since 2026-06-25) and the generic
  `uts-prod-instruments-service-t1-recon` (no scheduler at all — replaced by per-AG jobs per the terraform's own
  retirement comment)."
status: open
nature: issue
asset_group: [cefi, defi, tradfi, prediction, sports, meta]
stage: [data, meta]
repos:
  [
    market-tick-data-service,
    unified-trading-library,
    unified-api-contracts,
    deployment-service,
    instruments-service,
    strategy-service,
    batch-live-reconciliation-service,
  ]
scope: [engineer, admin]
tags:
  [
    cloud-run-jobs,
    fleet-triage,
    t1-recon,
    lifecycle-catalogue,
    dp-manifest-hygiene,
    paper-stream,
    blrs,
    import-error,
    base-image-digest,
    date-resolution,
    orphaned-scheduler,
    data-pipeline,
  ]
related:
  [
    ./utl_uac_skew_fleet_audit_2026_07_15.md,
    ./dp_catalog_not_running_sports_prediction_2026_07_15.md,
    ./recon_bucket_missing_nightly_recon_failing_2026_07_13.md,
    ./defi_scheduled_collection_outage_paused_crons_2026_07_16.md,
    ./mutable_git_sha_tag_restamping_cloudbuild_2026_07_13.md,
    ./aws_consolidator_batch_logstream_iam_gap_2026_07_16.md,
    ../tradfi_v9_stage1_finish_2026_07_06.md,
  ]
created: 2026-07-16
last_updated: 2026-07-16 # was: 2026-07-16 — task -003 RESUME-runbook session confirmed Cluster 5 also breaks the 11 DeFi mtds-collect-* jobs
parent_epic: infrastructure_master
priority: P1
source:
  "utl_uac_skew_fleet_audit_2026_07_15.md § 'SEPARATE operational findings' #2 (Group-C) — operator-directed production
  job-failure investigation under /autonomous, 2026-07-16"
assigned_vm: NA
resolved_by:
  "market-tick-data-service@205b7e3e (partial — fast/cefi-t1-recon ImportError only); unified-trading-library@3485c4d0 +
  market-tick-data-service@b8365c9d (Cluster 5 — batch-mode date-default gap)"
locked_by:
execution_scope: local-only
model_tier: opus-required
thinking_tier: max
estimate_class: research
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 1.2
supersedes:
superseded_by:
depends_on: []
assigned_role: infra
drift_direction: advance-code
locked_since:
---

> **NOTIFY-OPERATOR class finding.** Two NEW, unfixed data-correctness / cross-cutting findings below (cefi/defi
> catalogue duplicate-merge-key shrink; UTL batch-mode missing date default) need an operator/owner decision before
> anyone codes a fix — see each section's "Decision needed."

## Method

`gcloud run jobs list --region=asia-northeast1 --project=central-element-323112` (115 jobs) filtered to the Group-C name
patterns named in the source audit; for each candidate, `gcloud run jobs executions list --limit=3` for last-execution
status + `gcloud logging read` (bounded to the failing execution's time window) for the actual error; cross-checked
against `deployment-service/terraform/gcp/*.tf` for scheduler state / job ownership / retirement comments. Read-only
except where noted (one Dockerfile fix shipped + verified; one orphaned scheduler paused).

## Cluster 1 — SHIPPED FIX: MTDS base-image digest stale by ~2h relative to a same-day UAC addition

**Jobs**: `uts-prod-market-tick-data-service-fast-t1-recon` (failing today, 2026-07-16 02:5x UTC) and almost certainly
`uts-prod-market-tick-data-service-cefi-t1-recon` too (masked — see Cluster 5, it hits a DIFFERENT bug first).

**Root cause (confirmed)**: `market-tick-data-service/cli/handlers/onchain_perp_batch_handler.py` →
`_onchain_perp_batch_live_only.py:60` imports `from unified_api_contracts import venue_data_type_has_batch_source`. This
repo's own commit `mtds@0f0cc598` (2026-07-15T18:26:59Z) added that import; UAC added the symbol itself at
`uac@5d0569c3` (2026-07-15T18:35:18Z) — ~8 min LATER. MTDS's `Dockerfile` pins its UTL base image by digest
(`BASE_IMAGE_DIGEST`), last refreshed 2026-07-15T16:45Z (`sha256:b7c57243...`) — i.e. **before both** commits landed.
Confirmed live:
`docker run --rm --entrypoint python <deployed :latest> -c "import unified_api_contracts; hasattr(unified_api_contracts, 'venue_data_type_has_batch_source')"`
→ `False` on the old pin. The current UTL `:latest` (`sha256:e75610578e...`, published 2026-07-15T23:58:17Z, built from
a backmerge past both commits) → `True`.

**Fixed**: bumped `market-tick-data-service/Dockerfile`'s `ARG BASE_IMAGE_DIGEST` to `sha256:e75610578e...` with a dated
provenance comment (matching the repo's established rebuild-trigger-comment convention).
`market-tick-data-service@205b7e3e` (quickmerge, quality gates green). Triggered a fresh Cloud Build
(`gcloud builds triggers run market-tick-data-service-live-defi-rollout --branch=live-defi-rollout`, build
`388e21ca-0e64-4827-ad6c-81ff928e6d5c`) — see Evidence below for the terminal build status + post-fix job re-run.

- [x] [INFRA] P0. Bump MTDS `BASE_IMAGE_DIGEST` to the current UTL `:latest` (post-2026-07-15T18:35Z) —
      market-tick-data-service@205b7e3e, quality gates green. Repo: market-tick-data-service.
- [x] [OPS] P1. Verify build `388e21ca-0e64-4827-ad6c-81ff928e6d5c` reaches SUCCESS, docker-confirm the new `:latest`
      resolves `venue_data_type_has_batch_source`, then re-run `uts-prod-market-tick-data-service-fast-t1-recon` —
      **VERIFIED, ImportError CONFIRMED FIXED**: build `388e21ca` → SUCCESS; new digest `sha256:a47967baed26...` →
      `hasattr(unified_api_contracts, 'venue_data_type_has_batch_source')` → `True` (was `False` on the pre-fix digest).
      Re-ran the job for real (`gcloud run jobs execute --wait`, execution
      `uts-prod-market-tick-data-service-fast-t1-recon-tmmw8`): it now bootstraps fully, initializes 158-venue API key
      validation across 6 data sources (aster/databento/hyperliquid/odds_api/tardis/thegraph) — i.e. it gets MUCH
      further than the instant import-time crash before — proving the ImportError itself is gone. **The job still does
      not reach overall SUCCESS**, but for the SEPARATE, ALREADY-KNOWN reason in Cluster 5 below
      (`Date range validation failed: Invalid date format ''`) — confirming Cluster 5's date-default gap affects
      `fast-t1-recon` too, not just `cefi-t1-recon` (raises that finding's urgency; see Cluster 5). This import fix is
      complete and verified for what it targeted; the job's remaining failure is Cluster 5's, tracked separately below.
      Repo: market-tick-data-service.

## Cluster 2 — LIVE CLEANUP: orphaned dev-tier scheduler firing a retired job

**Job**: `uts-dev-instruments-service-t1-recon` (failing every day, confirmed back to at least several days;
`instruments-service: error: unrecognized arguments: --category=ALL`).

**Root cause (confirmed)**: `deployment-service/terraform/gcp/t1_batch_scheduler.tf:41-45`'s own comment: _"The old
all-AG 'instruments' 00:00 job (uts-prod-instruments-service-t1-recon) OOM'd at 8cpu/32Gi (signal 9)... It has been
RETIRED and replaced by per-AG jobs."_ The PROD retirement is complete (no prod scheduler targets the generic job any
more — confirmed via `gcloud scheduler jobs list | grep instruments-service-t1`). The DEV-tier mirror
(`uts-dev-instruments-t1-schedule`, `0 0 * * *`, targeting `uts-dev-instruments-service-t1-recon`) was **never migrated
alongside it** and is **NOT DECLARED IN ANY CURRENT TERRAFORM FILE**
(`grep -rn "uts-dev-instruments-t1-schedule" deployment-service/terraform/gcp/*.tf` → zero hits) — a pure state-drift
orphan, still firing daily against a CLI that no longer accepts whatever legacy invocation it's carrying.

**Action taken**: paused the orphaned scheduler
(`gcloud scheduler jobs pause uts-dev-instruments-t1-schedule --location=asia-northeast1`), verified `state: PAUSED`.
Did NOT delete it (dev-tier, zero prod blast radius either way, and deletion of an undeclared resource is more
irreversible than a pause — leaves a clean audit trail for whoever eventually reconciles the terraform state). No
terraform change needed since it was never in terraform to begin with.

- [x] [INFRA] P2. Pause the orphaned `uts-dev-instruments-t1-schedule` — verified `PAUSED` via
      `gcloud scheduler jobs describe`. No repo change (was never IaC-declared).

## Cluster 3 — ALREADY TRACKED (no new work; cross-referenced)

- **`uts-prod-batch-live-reconciliation-service` + `uts-prod-blrs-daily-determinism`**: BOTH fail with the identical
  Stage-0 `[Missing upstream data for <date>: execution config snapshot ...; ML t1-recon outputs ...]` abort — confirmed
  via live logs (`blrs-daily-determinism-clcsd`, 2026-07-16T02:30). This is the exact, already fully root-caused chain
  in `recon_bucket_missing_nightly_recon_failing_2026_07_13.md` (execution-service config-snapshot job never
  provisioned; ml-service t1-recon job never provisioned; strategy-service t1-recon fixed at the exec-bug level but
  still blocked one layer deeper). That doc correctly scopes the remaining work as genuine multi-repo feature work
  (provisioning 2 missing Cloud Run Jobs + wiring run-tag-aware `_SUCCESS`-marker writers in ml-service and
  strategy-service) — out of this triage's fixable scope, already tracked as `⏳ STILL OPEN` there. No new doc needed;
  `uts-prod-blrs-daily-determinism` is simply a second scheduled invocation of the SAME pipeline hitting the SAME gate,
  added here for completeness.
- **`uts-prod-strategy-service-t1-recon`**: fails with
  `ValueError: batch operation requires --date or --start-date/--end-date` — the exact, already-documented finding in
  `recon_bucket_missing_nightly_recon_failing_2026_07_13.md` § "2026-07-14 update (b)". See Cluster 5 below for a
  plausible SHARED root cause with the new MTDS date finding — worth the eventual owner checking both together.
- **`uts-prod-paper-stream` + `uts-prod-paper-engine-run`**: both fail with
  `RuntimeError: replay ...: no real GCS lending_rates data for window ... — refusing to emit an empty ledger (no synthetic fallback)`
  (confirmed via live logs on 3 separate executions). This is a **downstream symptom, not an independent bug**:
  `defi_scheduled_collection_outage_paused_crons_2026_07_16.md` already establishes the 11 DeFi/onchain daily collectors
  have been PAUSED since the 2026-06-08 pre-migration drain, so `lending_rates` (and most other DeFi types) simply have
  no fresh data to replay — the paper engines correctly refuse to fabricate a synthetic ledger. Resume is already
  tracked + operator-escalated in that doc (gated on the TradFi migration close-out). No new action here; noting the
  downstream blast radius (paper trading is ALSO dark, not just the raw collectors) for whoever executes that resume.

## Cluster 4 — CONFIRMED DORMANT / SUPERSEDED, NOT bugs

- **`instrument-catalogue-regen`**: scheduler `instrument-catalogue-regen-nightly` is **PAUSED** (since
  2026-06-25T01:38:45Z, `userUpdateTime`). Last execution 2026-06-21 (pre-dates the pause itself — hasn't run since).
  Runs a DIFFERENT script than the lifecycle-catalogue family
  (`unified-api-contracts/scripts/ generate_instrument_catalogue.py`, not instruments-service's
  `build_instrument_catalogue.py`) — so this is NOT simply "the old generic job the per-AG lifecycle-catalogue-regen-*
  replaced" (that retirement narrative applies to Cluster 2's `instruments-service-t1-recon`, a different job).
  Genuinely paused, not currently failing (not running at all). Reason for the 06-25 pause not confirmed this session
  (low priority — dormant, not broken; flagging for whoever owns UAC's `generate_instrument_catalogue.py` to confirm
  intentional vs forgotten).
- **`uts-prod-instruments-service-t1-recon`** (generic, no asset-group suffix): confirmed via
  `t1_batch_scheduler.tf:41-45`'s own comment (see Cluster 2) — RETIRED, replaced by the per-AG
  `instruments-service-{cefi,defi,tradfi,prediction}-t1-recon` jobs (all 4 confirmed healthy/succeeding today). No
  scheduler targets the generic job any more (`gcloud scheduler jobs list` — zero matches). Last execution 2026-07-13
  was a stale manual/leftover trigger, not a live cron. Not a bug — an already-completed retirement, just with the
  orphaned Cloud Run Job resource itself not yet deleted (cosmetic; zero risk since nothing invokes it).

## Cluster 5 — NEW, ESCALATED (CONFIRMED wider than first scoped): UTL `_adapter.py::_build_io()` has no BATCH-mode date default (LIVE mode does)

**Symptom**: `uts-prod-market-tick-data-service-cefi-t1-recon` fails with
`Date range validation failed: Invalid date format ''. Use YYYY-MM-DD format.` →
`ValueError: time data '' does not match format '%Y-%m-%d'`, thrown from
`unified_trading_library/core/date_utils.py:parse_date`, reached via
`unified_trading_library/service_framework/io_batch.py:DateRangeInput.__aiter__` → `get_date_range('', '')`. **CONFIRMED
also hits `uts-prod-market-tick-data-service-fast-t1-recon`**: after Cluster 1's ImportError fix landed, a real re-run
(`uts-prod-market-tick-data-service-fast-t1-recon-tmmw8`) got past bootstrap + 158-venue API-key validation (proving the
import fix works) and then hit this EXACT SAME error — so this is not a cefi-only edge case, it blocks every MTDS
t1-recon invocation that omits `--start-date`/`--end-date` (which is all of them per their Terraform args — see below).

**Confirmed NOT universal to every UTL batch consumer** (narrows/sharpens the finding): checked
`market-data-processing-service` (`uts-prod-market-data-processing-service-t1-recon`, succeeding today, ALSO invoked
with zero date args in its Terraform) — its own `cli/main.py:190-192` has a **per-service bridge**:
`if not start_date and not end_date: start_date = yesterday` (a legacy-argv layer that runs BEFORE the shared UTL
adapter). So the shared `_adapter.py` gap is real, but several services already work around it with their own
default-date bridge; MTDS's `cli/main.py` (whose own docstring says "Standard args ... are provided by ServiceCLI" —
i.e. it relies ENTIRELY on the shared UTL layer, no bridge of its own) does not, which is why it's the one crashing.
This makes the fix MORE tractable than a blind shared-library change: either (a) add the same "default to yesterday when
both dates are omitted" bridge to MTDS's CLI (mirroring MDPS's precedent almost exactly), or (b) fix it once in the
shared `_adapter.py::_build_io()` BATCH branch (benefits every consumer, but needs confirming no OTHER batch consumer
relies on the current no-default behavior as a deliberate "explicit dates only" gate).

**Root cause (confirmed by code read)**: `unified_trading_library/service_framework/_adapter.py::_build_io()`:

```python
if self.runtime.is_batch:
    start_date: str = cast(str, getattr(self.args, "start_date", "") or "")
    end_date: str = cast(str, getattr(self.args, "end_date", "") or "")
    return BatchIO(start_date=start_date, end_date=end_date, ...)   # NO default when both are empty

# Live mode: ... If explicit dates are provided, use them; otherwise default to today.
start_date = cast(str, getattr(self.args, "start_date", "") or "")
end_date = cast(str, getattr(self.args, "end_date", "") or "")
if not start_date:
    today = datetime.now(UTC).strftime("%Y-%m-%d")
    start_date = today
    end_date = today
```

The LIVE branch explicitly defaults to today when no date is given; the BATCH branch has no equivalent fallback at all,
so any batch invocation that omits `--start-date`/`--end-date` (deliberately, per convention — most t1-recon Terraform
args do NOT pass dates, e.g. `market-tick-data-service-cefi-t1-recon`'s args are just
`["--operation", "download", "--mode", "batch", "--asset-group", "CEFI"]`) crashes with an empty-string date instead of
defaulting to T-1/today.

**Why this matters beyond MTDS**: this is shared UTL framework code, not a per-service bug — `_build_io()` is the
generic batch-mode I/O constructor every batch-mode service handler goes through. This is plausibly the SAME mechanism
behind the ALREADY-TRACKED `uts-prod-strategy-service-t1-recon` failure
(`recon_bucket_missing_nightly_ recon_failing_2026_07_13.md` attributes that one to strategy-service's own
`_resolve_date_args()` requiring an explicit date "unlike ml-service/mdps, which self-default to T-1" — worth the
eventual fixer checking whether ml-service/mdps's apparent self-defaulting is a PER-SERVICE override sitting in front of
this shared gap, or whether they simply always receive explicit `--start-date` args from their own Terraform and have
never exercised this path).

**NOT fixed this session** — this is a shared-library (UTL) change with fleet-wide blast radius (every batch-mode
consumer), squarely the "ambiguous/large → escalate, don't force-fix" triage bucket, not a ≤30min in-scope fix. Whoever
picks this up should: (1) confirm the intended default policy for a bare `--mode batch` invocation with no date (T-1?
today? explicit-only-by-design for some services?) — this may be a deliberate design choice for OTHER batch consumers
that this triage shouldn't assume is wrong everywhere; (2) if a default is correct, mirror the LIVE branch's fallback
into the BATCH branch; (3) regression-test against every batch-mode service in the fleet, not just
MTDS/strategy-service, since `_adapter.py` is shared UTL code.

- [x] ✅ [INFRA] P1. Decide + implement a default-to-yesterday date bridge for MTDS's batch CLI — **FIXED 2026-07-16,
      shared root cause** (option b: `unified_trading_library/service_framework/_adapter.py::_build_io()`'s BATCH branch
      now defaults omitted dates to yesterday UTC). Evidence: `unified-trading-library@3485c4d0` (verified ancestor of
      `origin/live-defi-rollout`), propagated via `market-tick-data-service@b8365c9d` (base-image bump, also verified
      ancestor). See "Cluster 5 FIXED 2026-07-16" below — unblocks the 11 DeFi daily-batch collectors + MTDS
      `*-t1-recon` jobs.
- [x] [OPS] P2. Once Cluster 1's ImportError fix landed, checked whether `fast-t1-recon` also hits this date bug —
      **CONFIRMED YES** via a real re-run (`uts-prod-market-tick-data-service-fast-t1-recon-tmmw8`, 2026-07-16 06:10
      UTC): bootstraps fully past the (now-fixed) import point, then hits the identical `Invalid date format ''` crash.
      Raises this from "plausible" to "confirmed blocking every MTDS t1-recon invocation" — see the updated Cluster 5
      symptom section above.
- [x] [OPS] P1. **UPDATE 2026-07-16 (later session, dispatched to `tradfi_v9_stage1_finish` task -003, the RESUME
      runbook) — CONFIRMED this exact bug ALSO breaks the 11 DeFi daily-batch `uts-prod-mtds-collect-*` Cloud Run jobs,
      not just the `-t1-recon` family.** While executing the coordinated 48-scheduler resume, force-ran
      `uts-prod-mtds-collect-oracle-prices` and `uts-prod-mtds-collect-gas-fees` for real (`gcloud scheduler jobs run` →
      `gcloud run jobs executions describe`, watched to terminal) — both FAILED with the byte-identical trace:
      `ERROR Date range validation failed: Invalid date format ''`, `_adapter.py:80` →
      `io_batch.py:45:DateRangeInput.__aiter__` → `get_date_range('', '')` → `date_utils.py:73`. Confirmed via
      `deployment-service/terraform/gcp/defi_collection_scheduler.tf:170` that ALL 11 `defi_collect_operations` share
      the identical `args = ["--operation", "collect-${each.key}", "--mode", "batch"]` template — zero date flags for
      every one of them — so this is systemic across the whole DeFi collector fleet, not just the 2 sampled. Re-paused
      all 11 `uts-prod-mtds-collect-*-cron` schedulers immediately after confirming (do not leave broken jobs firing);
      full accounting in `tradfi_v9_stage1_finish_2026_07_06.md` task -003's Progress Log entry and
      `defi_scheduled_collection_outage_paused_crons_2026_07_16.md`. This means resuming the DeFi collector schedulers
      alone is NECESSARY BUT NOT SUFFICIENT to restore steady-state DeFi batch collection — a fix for this cluster's own
      still-open decision (mirror MDPS's date bridge into MTDS's CLI, or fix the shared `_adapter.py` BATCH branch) is a
      hard blocker for that separate, DeFi-specific deliverable, raising this finding's urgency further. The 3
      `defi-fwd-*` live-poll crons (VM-launched with `--mode live`, a DIFFERENT code path that already self-defaults to
      today per the LIVE branch shown above) are NOT affected — all 3 verified SUCCEEDED with real fresh data this same
      session.

### Decision needed (operator / next owner)

Two independent judgment calls neither this triage nor a single ≤30min fix should resolve unilaterally:

- **A**: Is the cefi/defi lifecycle-catalogue shrink (see `dp_catalog_not_running_sports_prediction_2026_07_15.md`'s
  2026-07-16 update) a legitimate corrective dedup (→ `--allow-catalogue-shrink`) or does `_merge_incremental` need a
  proper duplicate-key-aware rewrite?
- **B**: What is the CORRECT default-date policy for UTL's shared BATCH-mode `_build_io()` path — should it mirror
  LIVE's "default to today" (works for most t1-recon jobs, which want T-1/today), or is explicit-date-required actually
  intentional for some batch consumers (in which case the fix is per-job Terraform args, not a UTL change)?

## Evidence log

- `gcloud run jobs list --region=asia-northeast1 --project=central-element-323112` (115 jobs) filtered to Group-C
  patterns; `gcloud run jobs executions list --job=<name> --limit=3` per candidate for last-execution status.
- `gcloud logging read` (bounded to each failing execution's actual time window) for:
  `lifecycle-catalogue-regen-{cefi,defi}` (CATALOGUE_SHRINK_BLOCKED), `uts-dev-instruments-service-t1-recon`
  (`--category=ALL` argparse error), `uts-prod-market-tick-data-service-fast-t1-recon` (ImportError),
  `uts-prod-market-tick-data-service-cefi-t1-recon` (empty-date ValueError), `uts-prod-dp-manifest-hygiene-changed`
  (signal 9 ~19s after start — inconclusive, see below), `uts-prod-blrs-daily-determinism` +
  `uts-prod-batch-live-reconciliation-service` (Stage-0 missing-upstream-data abort), `uts-prod-paper-stream` +
  `uts-prod-paper-engine-run` (no-real-GCS-data RuntimeError).
- `docker run --rm --entrypoint python <image>@<digest> -c "..."` against both the OLD (`sha256:b7c57243`) and NEW
  (`sha256:e75610578e`) UTL base-image digests to confirm `venue_data_type_has_batch_source` presence — False / True
  respectively.
- Downloaded + re-analyzed `gs://instruments-store-{cefi,defi}-prd-central-element-323112/prod/catalog.parquet` via a
  read-only re-implementation of `_incremental_merge_keys()` — see the linked doc for the duplicate-key counts.
- `gcloud scheduler jobs list/describe` for every candidate's owning scheduler (state, schedule, `userUpdateTime`)
  cross-checked against `deployment-service/terraform/gcp/*.tf` for IaC ownership.

## Not deep-dived this session (scoped out, noted for a future pass)

- `uts-prod-dp-manifest-hygiene-changed` (fails daily, SIGKILL ~19s after "Event logging initialized" — a single Cloud
  Monitoring memory-utilization sample at time of death showed only ~2.8% utilization, NOT the classic
  near-100%-then-OOM pattern used to justify the sports/prediction memory bumps elsewhere in
  `dp_catalog_not_running_sports_prediction_2026_07_15.md` — so a blind memory bump here would be a guess, not an
  evidenced fix. `uts-prod-dp-manifest-hygiene-full` (weekly) shows the same terse 3-line signal-9 log with no further
  diagnostic detail. Needs either a closer live-triggered run with tighter log-tailing, or instrumentation in
  `e2e-testing/scripts/audit/manifest_hygiene_daily.py` to narrow down where the process dies. Flagging rather than
  guessing at a fix.
- `lifecycle-catalogue-full-defi` and `lifecycle-catalogue-full-tradfi` (weekly, last run 2026-07-11, both FAILED;
  `full-cefi`/`full-prediction` succeeded same day) — likely the SAME cluster as the cefi/defi duplicate-merge-key
  shrink above (same script, `--mode full`), but not confirmed live (log query returned too little detail for the
  5.7h-long `full-defi` execution to draw a conclusion). Low urgency: weekly cadence, next run 2026-07-18, gives time
  for Cluster 5-adjacent decision A to land first if related.

## Status

**OPEN.** One fix shipped + build in flight (Cluster 1), one live cleanup done (Cluster 2), three clusters
cross-referenced to existing tracked work (Cluster 3), two confirmed non-bugs (Cluster 4), two new findings escalated
for an operator/owner decision before further code changes (Cluster 5 + the cefi/defi catalogue shrink in the linked
doc).

## Cluster 5 FIXED 2026-07-16

MTDS batch-mode date-default gap fixed at the shared root cause: UTL `_adapter.py::_build_io()` now defaults omitted
batch dates to yesterday UTC (`unified-trading-library@3485c4d0`), propagated to mtds via base-image bump
(`market-tick-data-service@b8365c9d`, image `@b92a8680`). Unblocks the 11 DeFi daily-batch collectors (verified
SUCCEEDED) and the MTDS `*-t1-recon` jobs that hit the same crash. The cefi/defi catalogue `CATALOGUE_SHRINK_BLOCKED`
sub-finding remains a separate open owner-decision (unchanged).
