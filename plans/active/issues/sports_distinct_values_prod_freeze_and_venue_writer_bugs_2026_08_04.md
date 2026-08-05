---
doc_type: issue
title:
  "Sports distinct-values panel: 4-day-frozen prod deploy (44→3 non-canonical count) — root-caused + fixed today; 3
  venues (FOOTBALL/LADBROKES_UK/SPORT888) need a historical re-stamp, not more code"
summary: >-
  Operator flagged the deployment-ui Distinct Values panel (sports) still showing ~44 non-canonical values across
  venues/instrument_types/data_types despite prior sessions already having landed the fixes in UAC + deployment-api.
  Root cause was NOT a code gap for most of them: `uts-shared-deployment-api` production traffic had been frozen on a
  pre-2026-07-31 revision for ~4 days — every automatic `deploy-shared.sh` cutover attempt since then had silently
  failed (same signature as `deployment_api_cloud_run_coldstart_flaky_exit0_blocks_prd_sa_cutover_2026_07_31.md`,
  cross-referenced there with fresh evidence this session). Recovered via a direct `gcloud run services update-traffic`
  retry (confirmed live, serving correctly). That alone dropped the count from 44→12. Root-caused + fixed the remaining
  genuine gaps: (1) 5 legitimate-but-unregistered instrument_type values (bare `ASIAN_HANDICAP`/`OVER_UNDER`,
  `exchange_odds`/`fixed_odds`/`odds`) added to UAC's accepted-exceptions registry — instrument_types now 0
  non-canonical (was 37); (2) two real writer bugs found and fixed at the source: `market-tick-data-service`'s
  `venue_fetch.py` bypassed the already-existing `SPORTS_VENUE_FOLD` (raw `.upper()` instead of folding
  `ladbrokes_uk`/`sport888` to canonical `LADBROKES`/`BET888SPORT` first) and `market-data-processing-service`'s
  `live_workers.py` did a raw `instrument_id.split(":")[0]` that grabbed the SPORT token ("FOOTBALL") instead of the
  bookmaker for sports' `SPORT:BOOKMAKER:MARKET:...` id shape (mirrors an already-fixed sibling bug class,
  `_venue_token_from_canonical_id`, that just hadn't been applied at this one call site). Both writer fixes stop future
  pollution but do NOT retroactively fix already-captured rows — venues stays at 3 non-canonical
  (FOOTBALL/LADBROKES_UK/SPORT888) until a historical re-stamp runs; see Todos.
status: open
nature: issue
asset_group:
  [sports] # was [sports, cross-cutting] -- retagged 2026-08-04 by /ag-closeout-audit sports tranche
  # (Orthogonality HARD CHECK): every detail (SPORTS_VENUE_FOLD, sports distinct-values panel endpoint, MTDS/MDPS
  # sports-only writer bugs) is single-AG-specific; the general cross-cutting deploy-freeze root cause is already
  # tracked separately in deployment_api_cloud_run_coldstart_flaky_exit0_blocks_prd_sa_cutover_2026_07_31.md (related:
  # above), and the sibling per-AG pattern (defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md) confirms
  # this class is tracked one-doc-per-AG, not as one cross-cutting doc.
stage: [data]
repos:
  [
    unified-api-contracts,
    market-tick-data-service,
    market-data-processing-service,
    deployment-api,
    deployment-service,
    unified-trading-pm,
  ]
scope: [engineer, admin]
tags:
  [
    sports,
    distinct-values,
    canonicalisation,
    venues,
    instrument-types,
    honest-coverage,
    cloud-run,
    deploy-freshness,
    writer-bug,
  ]
related:
  [
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/active/issues/deployment_api_cloud_run_coldstart_flaky_exit0_blocks_prd_sa_cutover_2026_07_31.md,
    /plans/archive/2026_07/distinct_values_noncanonical_audit_2026_07_20.md,
    /plans/active/defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md,
    /plans/active/issues/honest_coverage_cron_run_job_sa_missing_actas_uts_prd_sa_2026_08_03.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
created: "2026-08-04"
author: unknown
last_updated: "2026-08-05"
parent_epic: manifest_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.24
source: >-
  Operator live screenshot of the deployment-ui Distinct Values panel (sports asset_group), 2026-08-04 interactive
  session — "the fix may already have rolled out and not be visible yet but double check", "why is venue, instrument
  type... not canonical still", "trigger one [rollup] to refresh", "code needs fixing, uac needs fixing, everything
  deployed... manifest purged and re-rolled up".
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
depends_on: []
context_scope:
  [
    /plans/active/issues/deployment_api_cloud_run_coldstart_flaky_exit0_blocks_prd_sa_cutover_2026_07_31.md,
    deployment-api/deployment_api/routes/data_status/_distinct_values.py,
    unified-api-contracts/unified_api_contracts/registry/market_data_categories.py,
    market-tick-data-service/market_tick_data_service/engine/orchestrator/venue_fetch.py,
    market-data-processing-service/market_data_processing_service/app/core/live_workers.py,
  ]
---

# Sports distinct-values panel — 44→3 non-canonical (2026-08-04)

## What was live when this session started (verified via the raw endpoint, not just the screenshot)

`GET /api/data-status/distinct-values/sports`: venues 4/14 non-canonical (FOOTBALL, KALSHI, LADBROKES_UK, SPORT888),
instrument_types 37/37 (every ASIAN_HANDICAP*/OVER_UNDER*/MATCH_ODDS* variant plus bare forms and
exchange_odds/fixed_odds/odds), data_types 3/10 (ODDS/ODDS_MOVEMENT/ODDS_SNAPSHOT uppercase residue). Total 44.

## Cause 1 (the majority, 33 of 44) — production deploy frozen since 2026-07-31

`uts-shared-deployment-api` had 100% traffic pinned to revision `00374-4pd` (built 2026-07-31T18:39, pre-`uts-prd-sa`)
continuously since then. UAC's accepted-exceptions for KALSHI / ODDS-uppercase-residue / the original 30-value
ASIAN_HANDICAP/OVER_UNDER/MATCH_ODDS/SPORT set had already been correctly written and wired into deployment-api's
`_ACCEPTED_EXCEPTIONS` days ago (`uac` commit 2026-07-30, `deployment-api@7988451` 2026-08-03) — the code was right,
production just never received it. Confirmed via direct Cloud Run inspection: every revision built since 07-31
(`00375`..`00428`) was either never traffic-routed, or (from `00419` onward) was a recurring `IAM-FIX-RETEST` diagnostic
probe (`python3 -c "..."` command override, no real app) deployed repeatedly onto this SAME production service —
unrelated to this investigation, cross-referencing the cold-start deploy issue linked above (same doc this session added
fresh evidence to: the freeze wasn't a forgotten manual pin, it was that doc's cold-start bug silently no-op'ing every
automatic cutover attempt for 4 days straight). Recovered by building fresh (`deploy-shared.sh`) and manually forcing
`gcloud run services update-traffic` after the automatic cutover again silently failed — see that doc's Progress Log for
the full blow-by-blow. Confirmed live and stable afterward (multiple 200s across `/api/health` + two `distinct-values`
asset_groups).

## Cause 2 (5 values) — legitimate MTDS/MDPS output never registered as accepted-exception

Bare `ASIAN_HANDICAP`/`OVER_UNDER` (real: `canonical_ids.py::build_instrument_id` only appends the point suffix when
`outcome.point is not None` — a null point from the vendor legitimately produces the bare token) and
`exchange_odds`/`fixed_odds`/`odds` (real: the deliberate 2026-07-27 venue-based split,
`market-tick-data-service/scripts/sports/exchange_fixed_odds_fork/`, already a registered UAC `CONTRACT_REGISTRY` key —
just never added to the distinct-values accepted-exceptions set). Added to
`SPORTS_MARKET_TOKEN_ACCEPTED_NONCANONICAL_INSTRUMENT_TYPES` (`unified-api-contracts@cb545bef`).

## Cause 3 (2 real writer bugs, still-open historical residue) — venues

- `LADBROKES_UK`/`SPORT888` (real captured data: 12,164 + 18,882 = 31,046 rows, `data_type=trades`,
  `instrument_type=odds`): `market-tick-data-service/engine/orchestrator/venue_fetch.py`'s per-league sports batch
  writer computed `bm_str = bm_raw.upper()` directly — bypassing the already-existing `SPORTS_VENUE_FOLD` dict
  (`{"ladbrokes_uk": "LADBROKES", "sport888": "BET888SPORT"}`) that two SIBLING writers (`odds_api_adapter.py`,
  `odds_api_ws.py`) already correctly apply. Fixed to `SPORTS_VENUE_FOLD.get(bm_raw, bm_raw).upper()`
  (`market-tick-data-service@edfa0615`). **CORRECTION (2026-08-05, this doc's own earlier text was wrong)**: this is NOT
  a narrow "written between 2026-07-27 and today" delta — a direct manifest census
  (`scripts/sports/census_track_c_venue_restamp_targets_2026_07_27.py`) shows LADBROKES_UK spans 990 distinct dates
  (2023-03-31..2026-07-26) and SPORT888 spans 1,824 distinct dates (2020-06-06..2026-07-26), i.e. essentially the SAME
  historical range as the ORIGINAL pre-2026-07-27 backlog that `restamp_sports_bookmaker_venue_2026_07_27.py` +
  `manifest_swap_venue_restamp_2026_07_27.py` already fixed once (that closeout's own numbers: 24,268+37,722 GCS objects
  / 8,859+13,997 manifest rows, verified 0 stale rows 2026-07-27). Today's counts (12,164 / 18,882 manifest shards) are
  HIGHER than that closeout's manifest-row counts — the most likely explanation is a full historical
  backfill/reprocessing job re-ran across the whole date range SOMETIME AFTER 2026-07-27 using the still-broken
  `venue_fetch.py`, re-polluting the entire range the July closeout had just cleaned. No currently-RUNNING VM was found
  repeating this (checked 2026-08-05: only the live producer was active), so this is a closed, bounded backlog to
  re-stamp, not an actively-growing one — but it is the FULL historical range, not a 1-2 day window. The candle-shape
  sibling data (arbitrage_opportunity/odds_movement/ odds_snapshot/odds_horizon_bucket) for both venues is confirmed
  CLEAN (0 residual, 2026-08-05 fresh rollup read) — only the raw-tick shape needs the re-stamp.
- `FOOTBALL` (all `attempted_failed`, 0 captured — 75 odds_movement + 69 arbitrage_opportunity + 50 odds_snapshot = 194
  rows, no real GCS objects at risk): `market-data-processing-service/app/core/live_workers.py`'s
  `_eager_preprocess_and_recover_metadata` did `input_venue = instrument_id.split(":")[0]` unconditionally — correct for
  every other asset_group's `VENUE:TYPE:SYMBOL` id shape, wrong for sports' `SPORT:BOOKMAKER:MARKET:...` shape (position
  0 is the sport). The already-existing, asset_group-aware `_venue_token_from_canonical_id` helper (built for this exact
  bug class, `sports_closeout_batch1_ao_ready_2026_07_24.md` todo 2) was two lines away and already imported, just not
  called at this one site. Fixed (`market-data-processing-service@595a1ff`).

Both writer fixes stop NEW pollution immediately but do not touch already-written rows — the panel will keep showing
these 3 venues until either a new capture cycle produces enough correctly-stamped rows to dominate, or (for
LADBROKES_UK/SPORT888's real captured data) a historical re-stamp runs. `FOOTBALL`'s rows are all `attempted_failed`
phantoms (no real GCS content) — may simply clear on the next natural retry now that the writer is fixed; worth
confirming before scoping a re-stamp for it.

## Shipped this session

- `unified-api-contracts@cb545bef` — 5 accepted-exception values.
- `market-tick-data-service@edfa0615` — `venue_fetch.py` SPORTS_VENUE_FOLD fix.
- `market-data-processing-service@595a1ff` — `live_workers.py` `_venue_token_from_canonical_id` fix.
- `unified-trading-pm@d211c01be` — QG baseline line-pointer correction (unrelated 1-line shift from the MTDS fix; since
  superseded/removed cleanly by `unified-trading-pm` slot-12's real fix to the underlying call site, 2026-08-05 — no
  action needed, noted for the record only).
- `uts-shared-deployment-api` — fresh build + deploy, live traffic confirmed on `uts-prd-sa` + today's code.
- Fresh honest-coverage rollup triggered same day (2026-08-04) — **confirmed 2026-08-05**: `generated_at` has advanced
  every day since (most recently `2026-08-05T14:42:13Z`), panel stable at venues 3/13, instrument_types 0/0, data_types
  0/0 for a full 24h+ with zero regression — the code fixes are holding correctly in production.
- **2026-08-05**: found the live capture VM (`mtds-live-sports-odds-api-trades-20260803-172841`, running continuously
  since 2026-08-03, i.e. BEFORE this session's `venue_fetch.py` fix) was still executing pre-fix code and would have
  kept writing new LADBROKES_UK/SPORT888 rows indefinitely. Stopped it and relaunched via
  `deployment-service/scripts/vm/launch-mtds-live.sh` with its exact original parameters (read from its own instance
  metadata:
  `--asset-group sports --shard-spec sports:ODDS_API:trades --instrument-ids "ODDS_API:SPORT:soccer_epl;...5 leagues" --live-source native --env prod`)
  — now running as `mtds-live-sports-odds-api-trades-20260804-131449`, confirmed picking up today's fix (see traps below
  for the 2 real gotchas hit getting this right).

## Todos

- [x] ✅ [DATA] P2. Confirm the fresh honest-coverage rollup completed and re-read the live panel — **DONE,
      2026-08-05**: confirmed venues 3/13 non-canonical (FOOTBALL/LADBROKES_UK/SPORT888 only, unchanged for 24h+),
      instrument_types 0/0, data_types 0/0. FOOTBALL did **NOT** clear naturally — still present after a full day +
      fresh rollup, so its own todo below stays open (the "may self-heal" hope in the original write-up did not pan
      out).
- [ ] [DATA] P1. Restart the live capture VM to verify the fix — **DONE, 2026-08-05** (see Shipped above) but leaving as
      a checked-off record with the 2 traps hit, since the SAME traps will bite the next person who relaunches any
      `mtds-live-*` VM after a code fix: 1. `launch-mtds-live.sh`'s tarball-freshness check is a WARN, not a hard block,
      by default (`LC_TARBALL_FRESHNESS` unset) — it launched the VM anyway with a stale `market-tick-data-service`
      tarball TWICE in a row (once because the local checkout had unrelated dirty test-artifact files that made
      `create-code-tarballs.sh` skip the repo entirely with only a warning, no error; once because another slot pushed a
      new LDR commit in the ~40s window between tarball-build and VM-launch, which the local `slot-cron-ff-pull`
      auto-pulled). Neither is a bug in the launcher — but **this WARN-not-ENFORCE default is very plausibly HOW the
      original bug persisted through multiple "fixed and closed" remediations**: a live producer can keep running
      provably-stale/buggy code indefinitely with only an easy-to-miss WARNING, never an error. Worth a follow-up issue
      doc proposing `LC_TARBALL_FRESHNESS=enforce` as the default for `mtds-live-*` relaunches specifically (live
      producers, unlike batch/backfill VMs, run for weeks — a stale launch is not self-correcting). 2. **Near-miss**:
      initially tried to reuse the OLD (now-stopped) VM by just `gcloud compute instances start`-ing it back up,
      forgetting its `VM_MODE=live` startup-script re-runs on every boot (GCE startup-scripts are not one-shot) — this
      would have created a SECOND concurrent live producer for the same shard, exactly the `mtds-live-{ag}-{shard}`
      singleton-lock race the launcher's own docs warn about ("thrash on the WS feed + race on the Redis Stream consumer
      group"). Caught and re-stopped within ~30-60s, before confirmed harm, but this is a real trap: a `mtds-live-*` VM
      is stateful and its boot disk should never be casually restarted like a stateless one — always launch a genuinely
      fresh instance via the launcher script instead.
- [ ] [DATA] P2. Historical re-stamp for LADBROKES_UK→LADBROKES / SPORT888→BET888SPORT — **scope corrected 2026-08-05,
      see Cause 3 above: this is the FULL historical range (990 / 1,824 distinct dates), not a narrow window.** Tools
      already exist and are proven (0 failures in their original 2026-07-27 run) —
      `market-tick-data-service/scripts/sports/restamp_sports_bookmaker_venue_2026_07_27.py` (GCS content-rewrite;
      **never deletes the source** — a pure additive read/transform/write to the new path, so no delete-safety-protocol
      citation is actually needed for this half, correcting this doc's own earlier claim) then
      `manifest_swap_venue_restamp_2026_07_27.py` (manifest CAS relabel, ADD+REMOVE — this half DOES touch the
      manifest's own REMOVE path, mirror that script's existing safety shape, not a fresh design). Exact day-lists for
      `--days-file` were extracted once (2026-08-04, via
      `scripts/sports/census_track_c_venue_restamp_targets_2026_07_27.py` filtered to
      `pipeline_mode=batch_odds_api & capture_status=captured`) but lived only in this session's scratchpad, which did
      not survive a session interruption — cheap to regenerate (the census script run takes seconds; see reproduction
      command below). Given the object count (comparable to the original 24,268+37,722-object migration), this is
      a >few-hundred-object operation — heavy-I/O HARD RULE applies, must run on a VM in-region, never from a local
      session. No ready-made VM launcher exists for this specific one-off script (the existing `mtds-live-*`/
      `mtds-backfill-*` launchers are for the MTDS CLI's own task dispatch, not for running an arbitrary standalone
      script) — needs either a minimal generic VM + SSH, or a small wrapper launcher. [OPERATOR] tag pending — confirm
      AO-dispatch vs human-run before executing (this doc currently `assigned_vm: NA`; flip to `planning` if AO should
      pick this up). Reproduction for the day-lists:
      `GCP_PROJECT_ID=central-element-323112 DEPLOYMENT_ENV=prod .venv/bin/python3 scripts/sports/census_track_c_venue_restamp_targets_2026_07_27.py`
      then filter its `read_availability_index` output by venue/pipeline_mode/capture_status as above. (repo:
      market-tick-data-service)
- [ ] [DATA] P3. Confirm FOOTBALL's 194 `attempted_failed` rows either clear naturally on a future retry or, if not
      after another few days, scope why they're still failing post-fix (may be an unrelated failure cause, not just the
      venue mis-stamp) before deciding whether they need a manifest phantom-row cleanup or are a separate live bug.
      **Still open as of 2026-08-05** (confirmed NOT self-healed after 24h+). (repo: market-data-processing-service)
- [ ] [INFRA] P3. File (or fold into an existing infra doc) a proposal to default `mtds-live-*` VM relaunches to
      `LC_TARBALL_FRESHNESS=enforce` — see the trap noted in the VM-restart todo above; a live producer silently running
      stale code for days-to-weeks is a plausible root cause worth closing off generally, not just patching for this one
      incident. (repo: deployment-service)

## Progress Log

- **2026-08-04 (interactive session)**: shipped all 3 code fixes + fresh deploy + fresh rollup (see Shipped above).
  Session interrupted mid-scoping of the historical re-stamp (checkpoint before any GCS/manifest writes were made —
  nothing partial was left in a bad state).
- **2026-08-05 (interactive session, same operator, continued after a ~26h gap)**: re-verified all 2026-08-04 fixes live
  and stable (traffic, live VM, panel all unchanged/correct — zero regression over 24h+). Ran the manifest census for
  LADBROKES_UK/SPORT888 and found the earlier session's "narrow recent window" assumption was wrong — corrected above.
  Found + fixed the live capture VM still running pre-fix code (restarted, 2 tarball-freshness traps hit and worked
  around, documented as a follow-up todo). Extracted `--days-file` day-lists for the re-stamp but did not yet execute it
  (no ready VM launcher for this specific script; needs the minimal-VM-+-SSH path scoped in the todo above) — session
  paused here for a `/pre-compact` checkpoint before continuing.

## Deferred work after 2026-08-05

| Item                                                              | State              | Blocked on                                                                                                                                                                              |
| ----------------------------------------------------------------- | ------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Historical GCS+manifest re-stamp (LADBROKES_UK/SPORT888)          | Not done           | Nobody — real work. Day-lists regenerate in seconds (recipe above); needs a clean VM (no ready-made launcher for this one-off script — build a minimal one, or SSH a fresh generic VM). |
| FOOTBALL 194 `attempted_failed` phantom rows                      | Not done           | Nobody — confirmed NOT self-healing after 24h+; needs a short investigation into why the retry hasn't cleared them.                                                                     |
| `LC_TARBALL_FRESHNESS=enforce` default proposal for `mtds-live-*` | Not done           | Nobody — a scoping/design todo, small.                                                                                                                                                  |
| LDR→main promotion of today's 5 shipped commits                   | Cannot be done yet | Time — auto-drains on the standing 15-30min cron; nothing to do but let it run.                                                                                                         |

**Recommended next item**: the historical re-stamp (P2, real user-visible data-correctness gap, tooling already proven
safe) — the VM-launch mechanics are the only remaining unknown, everything else (day-lists, scripts, safety shape) is
already worked out above.
