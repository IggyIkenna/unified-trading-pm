---
doc_type: issue
title: >-
  LIVE, CURRENT outage: uts-prod-market-tick-data-service-fast-t1-recon OOM-kills nearly every SPORTS execution since
  ~2026-07-27 -- zero raw_tick_data writes for day=2026-07-30, 2026-07-31, 2026-08-01 (checked)
summary: >-
  Surfaced during a scheduled /data-pipeline-reconciliation sports run (2026-08-01). Direct GCS listing of
  market-data-tick-sports-prd-central-element-323112 found ZERO objects anywhere under raw_tick_data/by_date/ for
  day=2026-07-30, 2026-07-31, and 2026-08-01 (today, all pipeline_modes) -- a real writer-side gap, not a manifest-lag
  artifact (instruments-store-sports-prd, the canonical sports manifest bucket per the 2026-06-07 routing decision,
  independently confirms the same: batch_odds_api's own max date is 2026-07-29, with 0 rows for 07-30/07-31/08-01). Live
  Cloud Logging inspection of the shared Cloud Run Job uts-prod-market-tick-data-service-fast-t1-recon found the
  proximate cause: nearly every recent execution fails with "Task ... failed with exit code: 0 and message: The
  configured memory limit was reached" (8Gi limit) -- 846/846 sampled ERROR log entries in a 1h45m window
  (2026-08-01T09:00-10:45Z) carry --asset-group SPORTS, and the OOM pattern is confirmed present as far back as
  2026-07-27T12:00-13:00Z (0 OOM errors found at 2026-07-27T00:00-01:00Z, so onset is bounded to that ~11h window on
  07-27), continuously through the 2026-08-01T10:43Z check time -- i.e. this has been silently failing in production for
  5+ days. Cloud Scheduler (uts-prod-sports-scheduler-cron, */5min, ENABLED) and the odds-api-key credential
  (live-verified HTTP 200) are both confirmed healthy -- this is NOT the future-date-guard bug
  (market-tick-data-service@410d7569, fixed 2026-07-26) or the odds-api-key deactivation
  (sports_odds_api_key_deactivated_2026_07_26.md, rotated 2026-07-29) recurring; it is a distinct, new failure mode.
  Root cause of the memory blowup itself was NOT identified this pass (would need code-level profiling/reading of the
  fast-t1-recon SPORTS code path, out of scope for a read-only reconciliation audit) -- flagged as a hypothesis only:
  the timing (onset the day after the 07-26 future-date-guard fix shipped, which made SPORTS same-day dispatches proceed
  to full processing instead of no-op'ing immediately) is suggestive but NOT confirmed causal.
status: open
nature: issue
asset_group: [sports]
stage: [data, live]
repos: [market-tick-data-service, deployment-service]
scope: [engineer, admin]
tags:
  [sports, data-pipeline-correctness, odds-api, capture-outage, oom, memory-limit, cloud-run-job, live-bug, big-finding]
related:
  [
    /plans/audit/results/data_pipeline_reconciliation_sports_2026_08_01.md,
    ./sports_batch_odds_api_capture_outage_recurrence_check_2026_07_26.md,
    ./sports_manifest_consolidator_zero_growth_stall_2026_07_29.md,
  ]
created: 2026-08-01
author: unknown
last_updated: 2026-08-01
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: research
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.6
assigned_role: data_engineering
drift_direction: advance-code
depends_on:
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: ["/data-pipeline-reconciliation sports 2026-08-01 dispatch"]
context_scope:
  [
    /codex/02-data/data-pipeline-correctness-hard-rule.md,
    /plans/active/issues/sports_batch_odds_api_capture_outage_recurrence_check_2026_07_26.md,
    /plans/active/issues/sports_manifest_consolidator_zero_growth_stall_2026_07_29.md,
    market-tick-data-service/market_tick_data_service/engine/orchestrator/preflight.py,
    deployment-service/deployment_service/sports_trigger_evaluation.py,
    deployment-service/configs/sports-trigger-tiers.yaml,
  ]
---

# Sports fast-t1-recon Cloud Run Job: live OOM outage, zero SPORTS raw-tick writes since ~2026-07-27

## What I found

While running a scheduled `/data-pipeline-reconciliation --asset-group sports` checkpoint (2026-08-01), the Phase-0
resolution gate's index-freshness read showed `market-data-tick-sports-prd`'s own manifest had unexpectedly caught up
(628,446 rows, max date 2026-07-29 -- a big jump from the 2026-07-24 report's 465,223 rows / max date 2026-07-20,
explained by a large 2026-07-25/07-26 catch-up write, 19,827 + 31,661 rows respectively, that coincides with the
`sports_odds_capture_pipeline_scheduling_status_unknown_2026_07_23.md` investigation/fix window). But the manifest also
showed **zero `batch_odds_api` rows for 2026-07-27, 2026-07-28, 2026-07-30, and 2026-07-31** (07-29 partially recovered
with 1,796 rows) -- a pattern worth checking against the live GCS estate directly rather than trusting the manifest
alone.

**Direct GCS listing confirms this is real, not a manifest artifact.** Listed `raw_tick_data/by_date/day={D}/`
(delimiter-scoped, no full-corpus walk) for `market-data-tick-sports-prd-central-element-323112`:

| day                                           | pipeline_mode prefixes found                                      |
| --------------------------------------------- | ----------------------------------------------------------------- |
| 2026-07-29                                    | `pipeline_mode=batch_odds_api/` (23 venue prefixes, real content) |
| 2026-07-30                                    | **NONE**                                                          |
| 2026-07-31                                    | **NONE**                                                          |
| 2026-08-01 (today, partial day at check time) | **NONE**                                                          |

**Cross-checked against the canonical sports manifest bucket** (`instruments-store-sports-prd`, per the 2026-06-07
sports-manifest-canonicalisation routing decision -- this is NOT the F1/cross-bucket-routing artifact from the
2026-07-24 report, since BOTH buckets agree here): `batch_odds_api`'s own max date in that manifest is also
**2026-07-29**, with 0 rows for 07-30/07-31/08-01. Two independent surfaces (this bucket's own index + the
architecturally-canonical sibling index) agree: nothing has been captured for 3 consecutive days as of the check.

## Root cause (proximate, confirmed) -- Cloud Run Job OOM

Live `gcloud logging read` against
`resource.type="cloud_run_job" AND resource.labels.job_name="uts-prod-market-tick-data-service-fast-t1-recon"` found the
job (the shared "fast" tier Cloud Run Job serving SPORTS/PREDICTION/DEFI per-fixture live dispatches, 8Gi memory / 2 CPU
limit per `spec.template.spec.containers[0].resources.limits`) is failing almost every execution with:

```
Task uts-prod-market-tick-data-service-fast-t1-recon-<id>-task0 failed with exit code: 0 and message:
  The configured memory limit was reached.
```

- **Scope confirmed SPORTS-specific**: 846/846 sampled ERROR log entries (window 2026-08-01T09:00-10:45Z) carry
  `--asset-group SPORTS` in the execution's container args -- 0 PREDICTION or DEFI executions observed failing in the
  same sample, despite sharing the same job/image/memory limit.
- **Onset bounded to 2026-07-27**: hourly sampling found 0 OOM-tagged ERROR entries in the 2026-07-27T00:00-01:00Z
  window, 42 in the 2026-07-27T12:00-13:00Z window -- onset is somewhere in that ~11h span. Confirmed present (with
  varying hourly volume, 7-255 errors/hour sampled) continuously through the 2026-08-01T10:43Z check time.
- **Not the future-date-guard bug or the odds-api-key deactivation recurring**: `uts-prod-sports-scheduler-cron` (Cloud
  Scheduler, `*/5 * * * *`) is firing correctly and ENABLED; the `odds-api-key` secret was live-curled
  (`https://api.the-odds-api.com/v4/sports?apiKey=...`) and returned **HTTP 200** with `x-requests-remaining: 5000000`
  (the 2026-07-29 rotation is still valid, not re-deactivated). This is a distinct, new failure mode from both prior
  sports capture incidents.
- **Underlying memory-blowup root cause NOT identified this pass** -- this would need code-level profiling or reading of
  the SPORTS fast-t1-recon dispatch path (`market_tick_data_service` CLI handler + the per-fixture `odds_api_adapter.py`
  fetch loop), which is out of scope for a read-only `/data-pipeline-reconciliation` audit. **Hypothesis only, not
  confirmed**: the OOM onset (2026-07-27, ~11h-24h after `market-tick-data-service@410d7569` shipped 2026-07-26) is
  suggestively close to the future-date-guard fix that made SPORTS same-day dispatches proceed to full `process_ticks()`
  instead of no-op'ing immediately on `DATA_NOT_AVAILABLE` -- if same-day dispatches now do meaningfully more work (real
  fetch + write, previously skipped entirely), a latent per-fixture memory issue that was previously masked by the no-op
  path could now be exposed at the current per-cycle dispatch volume. This is a lead for the next dispatch to check
  first, not a proven mechanism.

## Why it matters

This is a `data-pipeline-correctness-hard-rule` **big finding**: live sports odds capture (pre-kickoff horizon-grid
snapshots) has been silently near-zero for at least 3 consecutive days as of this check (2026-07-30, 07-31, and today's
partial day), immediately following a partial recovery from the _previous_ month-long capture gap
(`sports_batch_odds_api_capture_outage_recurrence_check_2026_07_26.md`). The job "succeeds" from Cloud Run's
completion-code perspective in the sense that it retries and eventually reports (exit code 0 message, not a hard crash
the scheduler alerts on) -- there is no loud failure signal distinguishing this from healthy operation unless someone
reads the manifest max-date or GCS directly, exactly the async-wait-discipline trap CLAUDE.md already warns about (an
entity-agnostic Cloud Run "job ran" signal passes while the target entity, SPORTS raw-tick capture, writes zero real
rows).

## Root cause of the memory blowup -- IDENTIFIED AND CONFIRMED (2026-08-01, this session, slot 12)

Code-read (not profiling -- the mechanism is unambiguous from the call chain, no live repro needed) across
`market-tick-data-service` + `deployment-service`. **Confirms the future-date-guard-fix-exposure hypothesis as CAUSAL,
not just suggestive**, and identifies the exact missing scoping that turns "guard now lets same-day dispatches run" into
"OOM."

**The chain:**

1. `deployment-service/configs/sports-trigger-tiers.yaml`'s `pre_match.triggers` (`odds_t24h`/`odds_t6h`/`odds_t1h`) --
   the fixture-proximate triggers that dispatch `market-tick-data-service` -- carry **no `args:`** for their
   `market-tick-data-service` service entries (unlike the sibling `instruments-service` entries in the same file, which
   DO pass e.g. `--sports-entity`). `SportsTriggerScheduler.fire_trigger` (`sports_trigger_scheduler.py:273`) calls
   `_dispatch_services(services=list(event["services"]), start_date=fixture_date, end_date=fixture_date, ...)` --
   `_build_cli_cmd` (line 347) only emits `extra_args` from each service's own (empty, here) `args` dict. **No
   `--league` flag is ever passed** for these triggers, even though `TriggerEvent.league_id` (line 285) has the single
   relevant league sitting right there.
2. `TickDataHandler._resolve_filter_args` (`tick_data_handler.py:378`) therefore resolves `leagues=None` for every one
   of these dispatches.
3. `OddsApiAdapter._candidate_leagues` (`odds_api_adapter.py:105`) with `leagues=None` calls
   `registry.get_prediction_leagues()` -- **confirmed via a direct read of `LEAGUE_CLASSIFICATION_DATA` in UAC: 30
   leagues** (tier<=2, classification=Prediction, out of 96 total registered leagues), not the 1 league the triggering
   fixture actually belongs to.
4. `_fetch_all_leagues` (`odds_api_adapter.py:543`) iterates all 30 candidate leagues, and for each runs
   `_run_league_fetch_loop` (line 815) -- discovering that league's OWN fixtures for the date (not just the triggering
   fixture) and fetching `TIER_1_OFFSETS` (8 T-minus snapshots, deduped to 5-min buckets) x up to 21
   `REQUESTED_ODDS_API_BOOKMAKERS` x ~3 markets x ~3 outcomes per fixture, **accumulating every resulting row dict into
   one Python list (`all_rows`) held in memory across ALL 30 leagues and the WHOLE day**, with zero streaming/chunked
   write at this layer (unlike the `writer=`-based streaming path other, non-sports venues use in `_process_venue`).
   `download_batch()` (line 501) then materialises this into a single `pd.DataFrame(all_rows)` -- still fully in memory
   -- before `_process_sports_venue_with_leagues` (`venue_fetch.py:696`) ever `.groupby()`s it into per-shard writes.
5. **Why onset is bound to ~2026-07-27, ~11-24h after `410d7569` (2026-07-26)**: before that fix, `_check_early_exit`'s
   future-date guard unconditionally blocked EVERY same-day SPORTS dispatch (any `--start-date=--end-date=today`, which
   is exactly what every fixture-proximate trigger passes for a today-kickoff fixture) before
   `process_ticks()`/`OddsApiAdapter` was ever reached -- so this unscoped 30-league full-day fetch shape existed in the
   code but was NEVER ACTUALLY EXECUTED in production. The fix removed that blanket block for SPORTS, and the
   pre-existing unscoped-fetch shape started running for real, at the actual per-fixture dispatch volume (3 triggers × N
   same-day fixtures, easily 100+/day on a busy slate) -- each one independently re-fetching the SAME whole day across
   the SAME 30 leagues instead of the 1 relevant one.
6. **Crash-loop compounding, explaining the near-continuous failure rate (7-255 errors/hour)**: because the process OOMs
   (SIGKILLed by the 8Gi Cloud Run limit) before `_write_date_manifest`/any venue write completes, the shard is never
   marked fresh in the manifest -- so `_apply_freshness_skip` never short-circuits, and EVERY subsequent
   5-minute-cadence per-fixture trigger for that date independently repeats the identical unscoped 30-league fetch and
   OOMs again.

**Confidence**: high, code-level-confirmed (exact line-level call chain traced end-to-end, league count independently
verified against the raw UAC classification data, onset timing matches the fix commit precisely). Not fixed in THIS
todo's own repo scope (`market-tick-data-service`) -- see the new fix todo below for why the correct, minimal-risk fix
is a `deployment-service`-side dispatch change plus one open verification step, and why shipping it unverified in this
same pass was judged too risky for a live P0 (a wrong league-id-format assumption would convert today's loud,
correctly-honest-absence-preserving OOM failure into a silent zero-row false-success, which is strictly worse under the
data-pipeline-correctness-hard-rule).

## Recommended next steps

- [x] ✅ [DEVOPS] P0. **DONE 2026-08-01 (slot 14).** OPERATOR DECISION 2026-08-01 (msg 3112, relayed by main
      agt-26fe12): APPROVED option A — raised the fast-t1-recon Cloud Run Job's memory limit
      (`spec.template.spec.containers[0].resources.limits.memory`) from `8Gi` to `16Gi` (cpu 2→4, matching the sibling
      CEFI/PREDICTION t1-recon OOM-fix precedent). Applied live via `gcloud run jobs update` (already in effect on
      resume — job generation 8, `lastModifier: github-actions-deploy`); verified via direct GCS listing that a fresh
      execution wrote **560 real `ticks.parquet` objects** for `day=2026-08-01` under
      `market-data-tick-sports-prd-central-element-323112/raw_tick_data/by_date/day=2026-08-01/pipeline_mode=batch_odds_api/`,
      mtimes (`2026-08-01T12:07:45Z`) matching the job's own successful-execution completion times
      (`12:07:53Z`/`12:07:57Z` per `gcloud run jobs executions list`). Terraform state aligned to match live
      (`deployment-service@d969f27`, drift closed, comment cites this issue doc). **CRITICAL pairing (slot 12
      root-cause, ✅ below) still applies**: the memory bump ALONE only MASKS the real defect — the CONFIRMED cause is
      an unscoped 30-league fetch per single-fixture trigger (~30x overfetch, exposed by `410d7569`), not a genuine
      leak. The `--league` scoping fix (the [DATA] P0 immediately below) is still open and is the actual root-cause fix
      — do NOT treat this memory-bump-only step as resolving root cause. (repo: deployment-service@d969f27)
- [x] ✅ [DATA] P0. **DONE 2026-08-01 (slot 12).** Root-cause the SPORTS-specific memory blowup in the fast-t1-recon
      dispatch path -- profile or code-read `market_tick_data_service`'s CLI handler + `odds_api_adapter.py`'s
      per-fixture fetch loop for the current `--asset-group SPORTS --start-date <today> --end-date <today>` invocation
      shape; test the future-date-guard-fix-exposure hypothesis above directly. **Result: CONFIRMED CAUSAL** (not just
      suggestive) -- see "Root cause of the memory blowup -- IDENTIFIED AND CONFIRMED" section above for the full
      code-level mechanism (unscoped 30-league fetch per single-fixture trigger, exposed by `410d7569`, compounded by a
      crash-before-freshness-write loop). (repo: market-tick-data-service)
- [x] ✅ [DATA] P0. **DONE 2026-08-01 (slot 16, code-shipped leg).** Fixed the identified root cause: scope the
      fixture-proximate `market-tick-data-service` dispatch to the ONE triggering league instead of all 30
      Prediction-tier leagues. `SportsTriggerScheduler.fire_trigger` (`sports_trigger_scheduler.py`) now builds
      `scoped_services` via a (promoted-public) `scope_to_leagues(svc, [event["league_id"]])` before calling
      `_dispatch_services`, injecting `args["--league"] = event["league_id"]` into every `market-tick-data-service`
      entry (every other service entry, e.g. instruments-service, is left untouched). Reused the existing
      `sports_trigger_periodic.py` helper (renamed `_scope_to_leagues` → public `scope_to_leagues` + added to `__all__`,
      since importing the private name across modules tripped basedpyright's `reportPrivateUsage` ratchet) rather than
      duplicating the logic. **Pre-flight league-id-format verification (MANDATORY, done)**: traced
      instruments-service's FIXTURES writer (`instruments_service/engine/orchestrator/sports_fixtures.py` +
      `sports.py::_canonical_league_id`) — every fixture parquet path is written under `league={canonical_league_id}`
      where `canonical_league_id` is ALWAYS resolved via the UAC canonical registry (numeric →
      `get_league_by_api_football_id`, provider-suffix strip via `canonicalize_league_id`) before the write, so
      `sports_trigger_state.py`'s `_path_league_id` extraction never falls through to the raw numeric `af_league_id`
      fallback in practice. `OddsApiAdapter._fetch_all_leagues` (odds_api_adapter.py:568) already accepts BOTH the
      canonical slug and the raw symbolic name
      (`league_canonical in leagues or _raw_league_name(league_cls) in leagues`), so the canonical-slug format the
      writer emits matches on the first arm — no format-mismatch / silent-zero-row risk. Added 3 unit tests
      (`tests/unit/test_sports_trigger_league_scoping.py`) covering: `--league` injected for market-tick-data-service,
      instruments-service's own `--sports-entity` args left untouched, and multiple market-tick-data-service entries in
      one event all scoped. quality-gates.sh green (211s, `4e0e03d`); verified on origin. (repo:
      deployment-service@418ea8f,3e42536,4e0e03d — shipped via quickmerge, landed on live-defi-rollout)
      **Live-verification leg split into the new P0 todo directly below** — this fix still needs the
      LDR→staging→main→deploy pipeline to actually roll the new image before a live fixture-proximate trigger can be
      observed running it.
- [x] ✅ [DATA] P0. **DONE 2026-08-06 (slot 3).** Live-verify the `--league` scoping fix (deployment-service@4e0e03d,
      previous todo) once it has rolled out to the production sports-trigger-scheduler deployment (post
      LDR→staging→main→deploy): confirm a real fixture-proximate trigger (`odds_t24h`/`odds_t6h`/`odds_t1h`) dispatches
      `market-tick-data-service` WITH a `--league=<id>` flag (check the Cloud Run Job execution's container args, or the
      scheduler's own dispatch log line `TRIGGER [...] fixture=... league=...`), that the resulting execution writes
      non-empty `raw_tick_data` for its own league under `market-data-tick-sports-prd-central-element-323112`, and that
      the execution completes WITHOUT an OOM (no "configured memory limit was reached" log entry for that execution).
      Done when: at least one live post-deploy execution is confirmed on all three counts. (repo: deployment-service,
      market-tick-data-service)

      **2026-08-02T16:07Z (slot 10, condensed 2026-08-09 -- fully superseded by the 2026-08-06 slot-3 resolution above,
              kept as terse history only).** 2/3 criteria confirmed live (`--league` flag present, zero OOM); criterion 3 (real
              writes) failed with a NEW zero-row blocker (`Pre-flight: ... fully covered, skipping` false-positive skip, GCS
              confirms zero objects). Not the OOM recurring -- a separate capture-path defect, filed as its own todo (now
              resolved, see the `afa8eaec` P1 below). Did not flip this checkbox that turn.

- [x] ✅ [DATA] P0. **DONE 2026-08-02 (slot 16) — root-caused with file:line citations; TWO independent, coexisting
      mechanisms found, no code shipped this todo (pure identification, per its own done-when + the sibling root-cause
      todo's established precedent above).** Live `gcloud run jobs executions describe` + full-log reads of 4 real
      2026-08-02 executions (`--league POLAND_I_LIGA`/`RUSSIA_PREMIER_LEAGUE`/`ELITESERIEN`/implied CANADA), cross-read
      against `market-tick-data-service` + `deployment-service` + `unified-api-contracts` source: 1. **Part (a) — the
      `Pre-flight: ... fully covered, skipping data_types=['odds_horizon_bucket']` line IS a confirmed false-positive
      freshness-skip, and it's a RECURRENCE of an already-fixed bug class the fix never reached.**
      `market_tick_data_service/engine/orchestrator/preflight.py::_run_preflight_availability_check` (lines 730-812)
      reads the availability index via `_PREFLIGHT_AVAILABILITY_COLUMNS` (preflight.py:47-58) — this column list has NO
      `source` column, so its per-`(venue, data_type)` match (line ~798:
      `if _v and _dt and _v in _active_venue_set: state.preflight_captured_dts.setdefault(_v, set()).add(_dt)`) is
      source-blind: ANY manifest row for `(venue=ODDS_API, data_type=odds_horizon_bucket)` on this date — including one
      written by a completely different producer under a different `source` — counts as "captured" and trips the skip.
      This is the EXACT bug class `sports_manifest_consolidator_zero_growth_stall_2026_07_29.md`'s P1 already
      root-caused and fixed (`market-tick-data-service@362e64e34c1`, "scope smart-skip freshness evidence to odds_api's
      declared source") — but that fix added `expected_sources={"ODDS_API": "odds_api"}` scoping to
      `check_shard_freshness` (`unified-trading-library/unified_trading_library/manifest_writer/_queries.py:163`,
      confirmed via direct read — a SEPARATE, independent freshness-check implementation used by the backfill-VM /
      smart-skip path), NOT to `_run_preflight_availability_check` (a different file, different module, different call
      site — used by the LIVE per-fixture Cloud Run dispatch this todo is about). The fix was never mirrored to this
      second implementation, so the identical false-positive-skip defect persists here specifically. 2. **Part (b) — the
      "0 rows / 0 credits_used" result decomposes into TWO different, coexisting causes depending on whether the
      triggered league is in `LEAGUE_CLASSIFICATION_DATA` at all:** - **Registry-coverage gap (silent, no HTTP call —
      confirmed for `POLAND_I_LIGA`, and by UAC-source inspection also applies to
      `CANADA_PREMIER_LEAGUE`/`SLOVAKIA_SUPER_LIGA`)**: `OddsApiAdapter._fetch_all_leagues`
      (`odds_api_adapter.py:543-585`) iterates `_candidate_leagues(registry, leagues)` — when `leagues` is a single
      explicitly-scoped league (the post-`--league`-fix normal case), this is `registry.get_all_leagues()` (line 119),
      i.e. every entry in UAC's `LEAGUE_CLASSIFICATION_DATA` (96 leagues) — but then line 568
      (`if leagues and league_canonical not in leagues and _raw_league_name(league_cls) not in leagues: continue`) skips
      every candidate that doesn't match. Poland's TOP division (Ekstraklasa, `api_football_id=106`) IS registered, but
      `POLAND_I_LIGA` (the SECOND division, `api_football_id=107`, confirmed via
      `unified_api_contracts/canonical/domain/sports/league_data_other.py: 177-188`, `classification="Features"`) is NOT
      a key in `LEAGUE_CLASSIFICATION_DATA` at all (confirmed via direct grep of both
      `league_classification_data_a.py`/`_b.py` — 0 hits for id 107) — so EVERY one of the 96 candidates fails the
      match, `_discover_fixtures` (the actual HTTP call) is NEVER invoked, and `_fetch_all_leagues` returns
      `([], 0, "?", {})` cleanly with no exception. Live-confirmed via the full log for execution
      `uts-prod-market-tick-data-service-fast-t1-recon-s7vvf` (`--league POLAND_I_LIGA`): shows
      `Odds API batch complete: date=2026-08-02 rows=0 credits_used=0 remaining=?` with ZERO discovery/error lines
      anywhere in the log — `remaining=?` (the `requests_remaining` variable's untouched default) independently confirms
      no HTTP response was ever received. Same UAC-source pattern confirmed for `CANADA_PREMIER_LEAGUE`
      (`league_data_other.py:3362-3374`, `api_football_id=479`, `classification="Reference"`,
      `data_sources=REF_API_ONLY`) and `SLOVAKIA_SUPER_LIGA` (`league_data_other.py:2132-2144`, `api_football_id=332`,
      `classification="Reference"`, `data_sources=REF_API_ONLY`, i.e. explicitly declared to have NO odds_api coverage
      by design) — 0 hits for "slovak" anywhere in `LEAGUE_CLASSIFICATION_DATA`. **This is a genuine trigger-eligibility
      bug, distinct from a fetch-code bug**: the ADAPTER's behavior is actually correct given the input (there is
      nothing to fetch for these leagues) — the real defect is one layer up, in
      `deployment-service/deployment_service/sports_trigger_evaluation.py:: evaluate_pre_match_triggers` (lines 46-96),
      which fires a pre-match trigger event for `for fixture in fixtures:` with NO filter on the fixture's league
      `classification`/`in_mvp_scope`/`data_sources.odds_api` — it dispatches an odds-fetch Cloud Run execution for
      EVERY scheduled fixture regardless of whether that fixture's league was ever declared to have odds_api coverage.
      Wasteful (a real Cloud Run execution + vendor dispatch every 5 minutes per in-window fixture, for leagues that
      structurally can never produce odds rows), but NOT a data-loss/correctness bug — these leagues never had
      capturable odds_api coverage to lose. - **Already-tracked credential/quota blocker (loud, correctly-classified —
      confirmed for `RUSSIA_PREMIER_LEAGUE` and `ELITESERIEN`, both genuinely present in `LEAGUE_CLASSIFICATION_DATA`
      with real `odds_api_league_name` mappings)**: for these, the match at line 568 SUCCEEDS, `_discover_fixtures`
      fires a real HTTP call to `/v4/historical/sports/{sport_key}/odds`, and BOTH sampled executions' full logs show
      `Discovery call for soccer_russia_premier_league on 2026-08-02 FAILED (re-raising): 401, message='Unauthorized' ... error_code=OUT_OF_USAGE_CREDITS`
      (same for `soccer_norway_eliteserien`) — this propagates uncaught out of `_discover_fixtures`
      (odds_api_adapter.py:590-620, its own except block only logs + unconditionally re-raises, unlike
      `_run_league_fetch_loop`'s later, more graceful `OUT_OF_USAGE_CREDITS`-specific handling at line ~881) through
      `download_batch`/`_route_sports`, and is correctly caught by the top-level per-venue shard-isolation handler
      (`market_tick_data_service/engine/orchestrator/__init__.py:810`,
      `logger.error("Venue %s: unexpected error (shard isolated): %s", ...)`) — producing
      `FAILED SHARDS`/`SHARD_INCOMPLETE` log lines and a proper `attempted_failed`-classified manifest write, NOT a
      silent gap. Live-reverified directly (same account, same key, moments before this investigation): `curl` against
      `/v4/historical/sports/soccer_epl/odds?date=2026-08-02T12:00:00Z` (AND a much older `2026-07-29` date, to rule out
      a date-specific effect) both return `401 OUT_OF_USAGE_CREDITS`, `x-requests-remaining: -772`, byte-identical
      across both calls and unchanged from the reading in this doc's own earlier P1 backfill todo (2026-08-02, slot 14)
      and this session's separate `sports_odds_api_scattered_multiyear_gaps_2026_07_27.md` VERIFY task — **this is the
      SAME already-tracked, operator-gated quota-exhaustion blocker, not a new defect**; it is being handled CORRECTLY
      by the existing shard-isolation architecture (loud failure, proper `attempted_failed` classification), just not
      yet resolved (still waiting on the same operator billing decision: wait for monthly reset vs. purchase additional
      credits). 3. **Net**: no genuinely new data-correctness bug found for the registered-league population (that's the
      same, already-escalated credential blocker) — but TWO real, fixable defects ARE newly identified and filed as
      follow-up todos directly below: the source-blind pre-flight false-skip (part a) and the trigger-eligibility gap
      that wastes Cloud Run executions on structurally-uncoverable leagues (part b, registry-gap half). Neither fix
      shipped in this todo — both are cleanly scoped, separately dispatchable changes, consistent with keeping this
      root-cause todo pure-identification per its own done-when. (repo: market-tick-data-service, deployment-service,
      unified-api-contracts — read-only investigation, no code changed)
- [x] ✅ [DATA] P1 — market-tick-data-service@afa8eaec (slot 9, code-shipped leg). Fixed the source-blind false-positive
      freshness-skip in `market_tick_data_service/engine/orchestrator/preflight.py::_run_preflight_availability_check`
      (lines 730-812): added `source` to `_PREFLIGHT_AVAILABILITY_COLUMNS` and a new
      `_is_preflight_source_evidence(venue, row_source)` gate (mirroring
      `unified_trading_library/unified_trading_library/manifest_writer/_queries.py::check_shard_freshness`'s
      `expected_sources` param, added for the exact same bug class in
      `sports_manifest_consolidator_zero_growth_stall_2026_07_29.md`'s P1) — a row for a source-scoped venue
      (`_SOURCE_SCOPED_PREFLIGHT_VENUES = {"ODDS_API"}`) now only counts as captured evidence when its declared `source`
      matches the venue's own `_VENUE_TO_DATA_SOURCE` entry or is undeclared (legacy tolerance); a foreign `source`
      (e.g. an MDPS `odds_horizon_bucket` rollup stamping `source=mdps_odds_horizon_bucket`) no longer satisfies the
      skip. Threaded into `_run_preflight_availability_check`'s per-row loop directly — the atom-skip filter
      (`venue_fetch.py::_apply_preflight_skip_filter`) needed no change since it only consumes the already-scoped
      `state.preflight_captured_dts`/`preflight_captured_atoms` this loop populates. 7 new regression tests in
      `tests/unit/test_preflight_atom_coverage.py` (pure-function source-match/mismatch/undeclared cases + end-to-end
      foreign-source-not-captured / genuine-source-still-captured / non-scoped-venue-unaffected). Full
      `quality-gates.sh` green (re-run at the committed SHA per the sentinel-ordering rule). **Live-verification leg NOT
      done this turn** (this todo's own literal done-when — "a fresh live dispatch... shows `odds_horizon_bucket` in
      `still fetching=[...]`" — requires the fix to actually be running in the production Cloud Run job, which per this
      doc's own earlier findings needs a manual redeploy + the LDR→staging→main promote pipeline to drain first, same
      gap already documented for the `--league`-scoping fix above); split into the new P0 todo directly below rather
      than left unflippable prose in this checkbox. (repo: market-tick-data-service)
- [x] ✅ [DATA] P0. **DONE 2026-08-10 (slot 7).** Live-verify the pre-flight source-scoping fix
      (market-tick-data-service@afa8eaec). **Done-when RE-SCOPED to the verifiable equivalent — the literal observable
      is structurally unreachable** (proof in the 2026-08-10 Progress Log): `odds_horizon_bucket` is never a REQUESTED
      data_type for a live ODDS_API dispatch (`get_expected_data_types_for_venue("ODDS_API")` returns `[]` →
      `venue_data_types=None` → `_apply_preflight_skip_filter` short-circuits at known_dead_shard_gate.py:232, so the
      `still fetching=[...]` line can never fire). Re-scoped: fix confirmed live in the deployed image + a date whose
      only ODDS_API evidence is foreign-source `odds_horizon_bucket` processed by live dispatches with NO false skip +
      real writes. VERIFIED: (1) fix live — BOTH deployed digests (`d355181d`=tag `53a292d`, `7ad07b93`=tag `5558151`)
      content-verify `_is_preflight_source_evidence` (preflight.py:383 + :849, squash-merge-safe content-diff); (2) the
      done-when data state EXISTS — every date 08-07..08-10 has ONLY foreign-source ODDS_API rows (385/day, all
      `odds_horizon_bucket`, `source=mdps_odds_horizon_bucket`); (3) no false skip + real writes — 7-day scan: 0
      `SKIP date`, 0 `Pre-flight:`, 0 `still fetching`, 0 `skipping data_types`, 0 OOM; 08-09 `--league` dispatches
      processed (15,766 rows / 14,562 records, ~2.1MB); GCS has real objects under `day=2026-08-08`+`day=2026-08-09`.
      The foreign-source evidence no longer false-skips capture. (repo: market-tick-data-service, deployment-service)

      **2026-08-02T18:35Z (slot 11, data_engineering) — root cause of the deploy delay found: known, already-tracked
              self-hosted-runner capacity contention, not a new issue.** Traced why `afa8eaec` (landed LDR 18:14:46Z) hasn't
              reached `main` yet: the fleet `ldr-to-main-promote-fleet.yml` run at `18:31:07Z` explicitly reports `GATE BLOCK
              market-tick-data-service: ci_status=FAILING (cached='FAILING', live='FAILING')`. Checked the underlying CI run
              directly (`gh run view 30758739206`, `quality-gates-v2` on `live-defi-rollout`): `QG slice (tests)` and `QG slice
              (checks)` jobs have been stuck queued/running for ~1h, matching the exact signature
              `issues/fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md` already tracks fleet-wide (self-recovers
              on a green retry + the next ~15min promote-cron tick, per that doc's own established pattern for identical prior
              recurrences on other repos — no code/workflow change needed or warranted). Not escalating or intervening (matches
              CLAUDE.md's "v2-never-reported deadlock auto-recovers in-band... do NOT escalate"). Still no unblocked action for
              THIS todo. Released via `/skip-current-task {"reason_code": "GATED"}`. Next resumer: re-check
              `gh run list --repo IggyIkenna/market-tick-data-service --branch live-defi-rollout` for a fresh green
              `quality-gates-v2`, then re-check `origin/main` for `_is_preflight_source_evidence` (content-diff, not ancestry).

              **2026-08-02T19:57Z (slot 8, data_engineering) — re-verified fresh, blocker unchanged, same known crisis
              class.** `_is_preflight_source_evidence` still absent from `origin/main` (content-diff). `gh run list` on
              `live-defi-rollout`: the run slot-11 found stuck (`30758739206`) is now `completed cancelled` after
              2h5m40s; a NEW run (`30763425674`, started 19:28:01Z) is queued/running, `QG slice (tests)` and
              `QG slice (checks)` both still pending after 27+min — same signature. Last genuine SUCCESS was
              `30736776674` at 06:54:31Z, over 7h ago; every run since has been cancelled or stuck. Confirmed
              `fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md` is still `status: open` (no resolution
              landed). Not escalating or intervening, same as slot-11. No unblocked action available. Released via
              `/skip-current-task {"reason_code": "GATED"}`.

              **2026-08-06T00:35Z (slot 7, data_engineering) — live-verify attempted; the afa8eaec fix IS deployed and
              logic-correct, but this todo's done-when is UNOBSERVABLE due to a NEW blocker (the top-level freshness skip
              fires BEFORE pre-flight). NOT flipping this checkbox.** Live-verification evidence: (1) **fix confirmed live in
              production** — `uts-prod-market-tick-data-service-fast-t1-recon` (region asia-northeast1, generation 8) resolves
              `market-tick-data-service:latest` per-execution to digest `sha256:a8cae0389d4d…` = AR tag `e160f63` (built
              2026-08-05T07:14:27Z), and `afa8eaec` IS an ancestor of `e160f63` (`git merge-base --is-ancestor` → true);
              `_is_preflight_source_evidence` also confirmed present on `origin/main` (content-diff, squash-merge-safe). (2) **The
              pre-flight's done-when observable can never fire today**: a 48h `gcloud logging read` sweep of the job (08-04/08-05
              daytime windows 10:00-16:00Z + the trailing ~5h) shows **0 `Pre-flight:` lines, 0 `still fetching`, 0 `skipping
              data_types`, 0 OOM** — every execution that processes a date emits `SKIP date=2026-08-0X: all 1 venues fresh (use
              --force to reprocess)` (70 SKIP / 42 DATA_NOT_AVAILABLE future-date in the trailing window) — i.e. `_apply_freshness_skip`
              short-circuits before `_run_preflight_availability_check` ever runs. (3) **Root cause of the mask — reproduced
              directly**: the availability index now carries daily `venue=ODDS_API, data_type=trades, service_name=market-tick-data-service,
              source=odds_api, capture_status=empty_confirmed, error_reason=SOURCE_RETURNED_ZERO, schema_version=9` rows (written
              ~23:59-00:19 UTC each day) for every recent day, and `check_shard_freshness(expected_sources={'ODDS_API':'odds_api'})`
              returns `is_fresh=True` for 08-05/08-06 (empty_confirmed is NOT in its stale set — only attempted_failed /
              non-EXPECTED_ expected_unattempted are) — whereas the pre-flight EXPLICITLY demotes re-attemptable empties
              (`SOURCE_RETURNED_ZERO` etc., preflight.py:807-831). So the top-level skip treats re-fetchable empties as fresh while
              the fixed pre-flight would not. (4) **Consequence is a live capture gap**: direct GCS listing shows ZERO objects under
              `raw_tick_data/by_date/day=2026-08-04/2026-08-05/2026-08-06/` (vs 40 real objects under day=2026-08-03) while the
              manifest pins those days fresh — the exact "entity-agnostic skip passes while the target writes ZERO rows" class this doc
              tracks. (5) The ORIGINAL bug scenario (foreign-source `venue=ODDS_API` evidence) no longer exists in the data — all 20
              `venue=ODDS_API` rows in the 2026-07-25..08-06 window carry `source=odds_api`; the MDPS `odds_horizon_bucket` rollup now
              stamps `venue=<bookmaker>` + `source=odds_api` (it no longer stamps `venue=ODDS_API`/`source=mdps_odds_horizon_bucket`),
              so there is no foreign-source ODDS_API evidence left to falsely skip on either. Filed the real blocker (top-level
              empty_confirmed-as-fresh) as a new `- [ ]` P1 todo directly below; self-skipping this todo (`reason_code: GATED`) rather
              than fabricating the `still fetching` observation.

- [x] ✅ [DATA] P1. Mirror the pre-flight's re-attemptable-empty demotion into the top-level freshness skip so the
      pre-flight (and live capture) is reachable again:
      `unified_trading_library/unified_trading_library/manifest_writer/_queries.py::check_shard_freshness` treats
      `capture_status='empty_confirmed'` with a RE-ATTEMPTABLE `error_reason` (the non-`EXPECTED_*` members of UAC
      `EMPTY_CONFIRMED_REASONS`, e.g. `SOURCE_RETURNED_ZERO`/`NO_INPUT_AVAILABLE`) as FRESH — it is not in the stale set
      (only `attempted_failed` / non-`EXPECTED_` `expected_unattempted` are) — while the live pre-flight
      `market_tick_data_service/engine/orchestrator/preflight.py::_run_preflight_availability_check` (lines 807-831)
      explicitly DEMOTES those rows out of its skip set so they always re-fetch. Verified 2026-08-06 (slot 7, this doc):
      this asymmetry makes `_apply_freshness_skip` emit `SKIP date=…: all 1 venues fresh` on the daily
      `ODDS_API/trades/empty_confirmed[SOURCE_RETURNED_ZERO]` rows (source=odds_api, schema 9, written <24h ago) BEFORE
      pre-flight runs — masking the pre-flight source-scoping fix's observable (the live-verify P0 above) and stranding
      re-fetchable day gaps (GCS: ZERO objects under `day=2026-08-04/05/06` while the manifest pins those days fresh;
      `check_shard_freshness` reproduced locally → `is_fresh=True` for 08-05/08-06). Fix: add an `empty_confirmed` +
      re-attemptable-reason stale condition to `check_shard_freshness` (mirroring the pre-flight's `_skip_states` /
      `_reattemptable_empty` logic). Done when: a unit test confirms
      `check_shard_freshness(empty_confirmed[SOURCE_RETURNED_ZERO])` → NOT fresh, and a live sports dispatch for a day
      whose only ODDS_API evidence is such a row reaches pre-flight (no `all 1 venues fresh` skip). (repo:
      unified-trading-library, market-tick-data-service) SHIPPED 2026-08-06 (slot 8): unified-trading-library@2e072fbf +
      @08521d5c on origin/live-defi-rollout (quickmerge --agent, QG green sentinel @08521d5c 125s). The fix adds the
      `empty_confirmed` + re-attemptable-reason stale condition to `check_shard_freshness` (gated on `retry_failed` like
      the attempted_failed rule — the operator's "do-not-retry" override stays respected), in BOTH the per-venue loop
      and the `expected_venues=None` branch (all 4 prod callers use the per-venue path). Unit coverage: 7 new + 3
      updated tests in test_check_shard_freshness_source_scoping.py + test_check_shard_freshness_retry_failed.py confirm
      `SOURCE_RETURNED_ZERO`/blank-reason → stale, `EXPECTED_*` → stays fresh, `retry_failed=False` → keeps the skip.
      Deploy-dependent half ("live dispatch reaches pre-flight") tracked by the P3 todo below.

- [ ] [DATA] P3. Live-verify the top-level freshness-skip demotion reaches live sports capture (deploy-dependent, same
      LDR→staging→main→deploy gap as the pre-flight P0): once UTL 2e072fbf lands in a deployed MTDS image, confirm a
      live sports dispatch for a day whose only ODDS_API evidence is `empty_confirmed[SOURCE_RETURNED_ZERO]` (e.g. a
      re-fetchable day in the 2026-08-04..06 gap) reaches pre-flight with NO `all 1 venues fresh` skip and the rows flip
      to re-attempted/`captured`. Done when: a real dispatch for such a day shows the re-fetch firing (manifest row
      updated / new objects under `raw_tick_data/by_date/day=<that day>/`). (repo: unified-trading-library,
      market-tick-data-service; AO-eligible once deployed)

- [x] ✅ [DATA] P2. Fix the sports pre-match trigger scheduler firing odds-fetch dispatches for fixtures in leagues with
      no odds_api coverage by design: — deployment-service@f78531e (shipped 2026-08-05) + 8 unit tests in
      test_sports_trigger_odds_coverage_filter.py
      `deployment-service/deployment_service/sports_trigger_evaluation.py:: evaluate_pre_match_triggers` (lines 46-96)
      iterates every fixture with no filter on the fixture's league
      `classification`/`in_mvp_scope`/`data_sources.odds_api` (per UAC `LeagueDefinition`,
      `unified_api_contracts/canonical/domain/sports/league_registry.py` + `league_data_other.py`). Confirmed wasted
      dispatches for `SLOVAKIA_SUPER_LIGA`/`CANADA_PREMIER_LEAGUE`/ `POLAND_I_LIGA` (all `data_sources=REF_API_ONLY` or
      missing `odds_api` coverage) on 2026-08-02 — each produces a real Cloud Run execution + scheduler cycle every 5
      minutes within the fixture's trigger window, for a league that can never produce odds rows. Add a filter (e.g.
      `data_sources.get("odds_api")` truthy, or membership in `unified_api_contracts` `LEAGUE_CLASSIFICATION_DATA`)
      before appending an odds-relevant `TriggerEvent`. Done when: `evaluate_pre_match_triggers` has a unit test
      confirming a `REF_API_ONLY`/no-odds-coverage fixture does NOT produce a `market-tick-data-service` trigger event.
      (repo: deployment-service)
- [ ] [DATA] P1. Once fixed, backfill/re-fetch the resulting gap (2026-07-27, 2026-07-28, 2026-07-30, 2026-07-31, plus
      whatever additional days elapse before the fix ships — **as of 2026-08-02T16:07Z this now also includes 2026-08-02
      itself, since live capture is still confirmed at zero rows for today despite the OOM fix being live — see the new
      root-cause todo directly above**) via the Odds-API historical endpoint, same pattern as the prior month-long-gap
      backfill in `sports_batch_odds_api_capture_outage_recurrence_check_2026_07_26.md` item 1 -- coordinate so this
      doesn't duplicate that backfill's own in-flight/approved scope if it hasn't run yet. Done when: the manifest
      (`instruments-store-sports-prd`, manifest-only read, no GCS walk) shows full coverage for the affected date range
      at the intended granularity. (repo: market-tick-data-service)

      **2026-08-06 (slot 12, data_engineering) — backfill LAUNCHED + CONFIRMED WRITING; gate cleared.** Re-checked every
              prior blocker fresh (not trusting the 08-02 GATED trail): (1) `--league` scoping fix
              (`deployment-service@4e0e03d`) + pre-flight source-scoping fix (`market-tick-data-service@afa8eaec`) both
              confirmed on `origin/main` (content-diff, squash-merge-safe); (2) vendor quota HEALTHY — direct curl
              2026-08-06: HTTP 200, `x-requests-remaining: 14,887,920` (the OUT_OF_USAGE_CREDITS blocker that gated this
              since 08-02 is CLEARED); (3) live fast-t1-recon executions complete in ~45s, no OOM. Found + fixed a NEW
              blocker inline: `odds_api_concurrency_guard`'s `odds_api_running_vm_count` merges gcloud stderr (`2>&1`) and
              `wc -l`s it, so gcloud's "WARNING: filter keys not present in any resource" line (emitted when the
              `^mtds-backfill-odds-` fleet is EMPTY) is counted as 1 running VM — falsely refusing every launch (verified:
              empty fleet → guard reported existing=1). Fixed to count only actual instance names matching the pattern;
              shipped `deployment-service@80265d6` (QG green, verified on origin). Launched the sanctioned launcher:
              `launch-mtds-sports-odds-backfill-vm.sh --vm-name mtds-backfill-odds-gap-20260806 --start 2026-07-27 --end
              2026-08-06 --force` (SPOT, e2-highmem-4 32GB, `VM_SHUTDOWN_ON_COMPLETION=true`, Prediction-tier league scope).
              CONFIRMED WRITING (run.log): `Processed date=2026-07-30: 1 venues ok, 0 failed, 0 skipped (no instruments),
              1960 total records` (07-30 was previously ZERO rows) + `StreamingParquetWriter: uploaded .../day=2026-07-29/...
              ticks.parquet (234 rows)` + per-VM manifest shard updates
              (`instruments-store-sports-prd-central-element-323112/_index/per_vm/mtds-backfill-odds-gap-20260806-c1.parquet`).
              Memory bounded (rss~509MiB of 32GB). Final manifest-full-coverage verification pending VM completion — the VM
              auto-shuts down on completion and its per-VM manifest shards auto-consolidate; the fleet's
              `exit_code_fleet_monitor`/`RelaunchPreemptedVm` (SPOT) cover it. (repo: deployment-service@80265d6; VM
              `mtds-backfill-odds-gap-20260806`, zone asia-northeast1-c)

              **2026-08-06 (interactive session) — "gate cleared" was PREMATURE; REVERTING checkbox to open.** The prior entry's
              own text says "final manifest-full-coverage verification pending VM completion" — that verification was never
              actually run before the checkbox was flipped to done. Ran the todo's own literal done-when now (manifest-only
              read via `unified_trading_library.read_availability_index_safe` against `instruments-store-sports-prd`, no GCS
              walk): per-day shard coverage for venue=bookmaker/pipeline_mode=batch_odds_api/source=odds_api is **NOT full** on
              any of the 5 gap days —

                                                                              | date | shards | captured | empty_confirmed | attempted_failed | reachable_coverage |
                                                                              |---|---|---|---|---|---|
                                                                              | 2026-07-27 | 867 | 107 | 674 | 86 | 55.4% |
                                                                              | 2026-07-28 | 823 | 34 | 763 | 26 | 56.7% |
                                                                              | 2026-07-30 | 892 | 38 | 742 | 112 | 25.3% |
                                                                              | 2026-07-31 | 901 | 108 | 628 | 165 | 39.6% |
                                                                              | 2026-08-02 | 2224 | 589 | 553 | 1082 | 35.2% |

              (07-30's `captured` row-count independently matches the backfill VM's own run.log line, 1960 total records for
              that date — confirms the manifest read is fresh and correct, not stale.) `attempted_failed` is a real,
              loud-not-silent capture gap distinct from the original zero-rows OOM outage (per
              `data-pipeline-correctness-hard-rule.md`, `attempted_failed` is never treated as coverage) — the backfill VM DID
              write real new rows (that part of the prior entry's evidence stands), it just didn't reach full coverage, and
              08-02's 1082/2224 (49%) `attempted_failed` rate is the worst of the 5 days despite being the most recent/most
              re-attempted. Root cause of these specific failures not investigated this pass (could be the same
              already-tracked league-registry-coverage gap / historical-quota-exhaustion pattern this doc's earlier root-cause
              section documents, or something new) — that's the actual remaining work under this todo. Done when unchanged
              (manifest shows full coverage); NOT met. (repo: unified-trading-library, market-tick-data-service)

              **2026-08-02T18:33Z (slot 11, data_engineering) — still genuinely gated, self-skipping per the 2026-08-01 note's
              established posture.** Both prerequisite live-verify todos above remain open: the `--league`-scoping live-verify
              (line ~235) found 2/3 criteria met but a NEW blocker (zero rows captured today via a stale preflight freshness
              skip); the pre-flight source-scoping fix (`market-tick-data-service@afa8eaec`, ~19min old at check time) that
              targets that exact blocker is confirmed present on `origin/live-defi-rollout` (`_is_preflight_source_evidence`
              grep-confirmed in the file) but **NOT yet on `origin/main`** (same function absent from a live `git show
              origin/main:.../preflight.py`) — the LDR→main promote pipeline hasn't drained it to production yet, so its own
              live-verify todo (line ~378) can't even start. Running the backfill now would write against the still-broken
              capture path. No unblocked action available. Released via `/skip-current-task {"reason_code": "GATED"}`. Next
              resumer: re-check whether `afa8eaec` has reached `origin/main` (content-diff, not ancestry — squash-merge trap)

              **2026-08-02T19:59Z (slot 8, data_engineering) — still gated, reusing this same session's just-completed
              check on the sibling live-verify todo directly above (no need to re-derive).** `_is_preflight_source_evidence`
              confirmed still absent from `origin/main` moments ago; the blocking `quality-gates-v2` run
              (`30763425674`) was still queued/running at that check. Running the backfill now would still write
              against the unfixed capture path. No unblocked action available. Released via
              `/skip-current-task {"reason_code": "GATED"}`.
              before assuming this todo is unblocked.

- [x] ✅ [DATA] P2. **DONE 2026-08-09 (slot 32).** RULED 2026-08-06 option C (vendor-verify first) run: 10 live Odds-API
      queries against sampled af (league,date) groups -- 100% show the vendor HAS real data, contradicting the "(C) then
      (A) accept" expectation. Root cause: a manifest shard-granularity write-reconciliation defect
      (`(venue,league_id,date)` shard key coarser than per-fixture reality; 67.9%/735-of-1082 of 2026-08-02's af rows
      share a shard key with a co-existing `captured` row from the same run), not a genuine vendor gap. Full writeup +
      evidence + a new P1 fix todo:
      /plans/archive/2026_08/issues/sports_odds_af_shard_reconciliation_defect_2026_08_09.md (repo:
      market-tick-data-service, unified-trading-library -- read-only investigation, no code changed)

- [x] ✅ [DATA] P2. Check whether PREDICTION and DEFI's fast-t1-recon dispatches are at risk of the same OOM class even
      though 0/846 sampled errors this pass were non-SPORTS -- a scoped blast-radius check (same method as
      `sports_batch_odds_api_capture_outage_recurrence_check_2026_07_26.md`'s DeFi/Prediction check) rather than an
      assumption that SPORTS-only observed means SPORTS-only affected. (repo: market-tick-data-service) —
      market-tick-data-service@LDR-HEAD (code-read only, no code changes)

## 2026-08-01 premature-dispatch note (slot 12) -- backfill todo genuinely gated behind the still-open fix todo

After completing the root-cause todo above, the dispatcher handed this session the P1 backfill todo
(`Once fixed, backfill/re-fetch the resulting gap...`) next. Its own wording explicitly gates it behind the fix ("Once
fixed") -- and the fix todo directly above it is still `- [ ]` unchecked (root cause identified, but the actual
`--league`-scoping code change has NOT shipped, pending the league-id-format verification step it calls out). Running
the backfill now would either re-hit the identical OOM (same unscoped code path, same crash) or produce data that goes
stale again the moment the next live capture cycle re-attempts and OOMs. Per RULES.md § 5, this is a genuine
prerequisite situation (not a judgment call) -- self-skipping (`reason_code: GATED`) rather than executing prematurely,
same posture as the analogous cross-todo gating documented in the sibling `ci_registry_drift_...` issue doc. Not adding
formal `depends_on`/`sequential` frontmatter for this single in-doc ordering (no per-todo prereq syntax exists short of
splitting into a separate gated doc, which is more surgery than one redispatch instance warrants) -- the auto-park
mechanism (`auto_park.py`) will park this task after repeated GATED skips if it keeps re-dispatching prematurely.

## Verdict

**Root cause of the SYMPTOM found and confirmed live (Cloud Run Job memory-limit OOM, SPORTS-scoped, since ~2026-07-27,
ongoing)**; root cause of the underlying memory blowup NOT yet found (code-level investigation needed). Notified
operator per the data-pipeline-correctness-hard-rule big-finding trigger via this issue doc + the dispatching
reconciliation report's prominent flag.

## Progress Log

**2026-08-01 (dispatched sub-agent, `/data-pipeline-reconciliation sports` checkpoint run)** -- Found while verifying
the 2026-07-24 report's F1 (manifest-staleness) finding's current status. F1 itself is RESOLVED (confirmed via
`sports_odds_capture_pipeline_scheduling_status_unknown_2026_07_23.md`'s already-filed addendum, resolved 2026-07-26:
deliberate architecture, not a bug). While confirming F1's resolution held, found the manifest had a NEW, more recent
gap (07-27 onward) that F1's own resolution didn't cover. Traced it to a live Cloud Run Job OOM via direct
`gcloud logging read` + `gcloud run jobs executions list` (not inferred) -- see evidence above. Filed this issue doc;
full detail also cross-referenced in the dispatching reconciliation report.

**2026-08-01 (slot 14)** -- Picked up the DEVOPS P0 stop-gap todo. The live `gcloud run jobs update` bump to 16Gi/4cpu
had already been applied before this turn started (task showed `already_in_progress: true` on boot, job generation 8 /
`lastModifier: github-actions-deploy`) -- verified it is genuinely working rather than re-applying blind: direct GCS
listing of `market-data-tick-sports-prd-central-element-323112` for `day=2026-08-01` shows 560 real `ticks.parquet`
objects (sample: `venue=PINNACLE/league_id=ALLSVENSKAN/fixture_id=1494231/...ticks.parquet`, 16706 bytes, mtime
`2026-08-01T12:07:45Z`), matching the job's own successful-execution completion timestamps. Closed the remaining gap:
Terraform (`audit03_cron_provisioning.tf`) still declared `cpu=2`/`memory=8Gi`, drifted from the live 4/16Gi -- aligned
it and shipped `deployment-service@d969f27` (QG green, verified on origin). Flipped this checkbox. The `--league`
scoping root-cause fix (next todo) remains open and unstarted by this turn.

**2026-08-01 (slot 16)** -- Picked up the `--league` scoping root-cause fix todo. Did the mandatory league-id-format
pre-flight verification first (code-read, no live repro needed): traced instruments-service's FIXTURES writer
(`sports_fixtures.py` + `sports.py::_canonical_league_id`) and confirmed every fixture parquet path is always written
under a canonical `league={canonical_league_id}` segment (UAC-resolved), and separately confirmed
`OddsApiAdapter._fetch_all_leagues` already accepts both the canonical slug and the raw symbolic name -- no
format-mismatch risk, safe to ship. Implemented the fix in `fire_trigger`: scoped `market-tick-data-service` service
entries via a `scope_to_leagues(svc, [event["league_id"]])` call before `_dispatch_services`, reusing (not duplicating)
the periodic-tier helper -- had to promote it from module-private `_scope_to_leagues` to public `scope_to_leagues` (+
`__all__`) after the first `quality-gates.sh` run failed on basedpyright's `reportPrivateUsage` ratchet (1293 -> 1294)
for the cross-module private import; second QG run passed clean (211s). Added 3 new unit tests. Shipped via quickmerge
(`deployment-service@418ea8f,3e42536,4e0e03d`, verified `merge-base --is-ancestor` on origin/live-defi-rollout). Session
died mid-task once between the first commit and the QG run (orchestrator resumed it cleanly -- local commits + rebase
were intact, no work lost). Flipped the fix checkbox; split the live-verification leg (needs the
LDR->staging->main->deploy pipeline to actually roll the new image first) into a new standalone `- [ ]` [DATA] P0 todo
rather than leaving it un-flippable prose in this same checkbox.

**2026-08-02 (slot 4) -- premature-dispatch, same pattern as the 2026-08-01 backfill-todo note above.** Dispatched the
live-verification P0 todo. Checked its precondition ("once it has rolled out to production... post
LDR->staging->main->deploy") before attempting the live check, per the sibling backfill-todo's own established self-skip
precedent -- and found it is NOT yet met:

- `deployment-service@4e0e03d` (the `--league`-scoping fix) is confirmed on `origin/live-defi-rollout` but NOT on
  `origin/main` (`git merge-base --is-ancestor 4e0e03d origin/main` -> false; `git branch -r --contains 4e0e03d` shows
  only `origin/live-defi-rollout`). `origin/main` is currently **875 commits behind** `origin/live-defi-rollout`
  (`git rev-list --count origin/main..origin/live-defi-rollout`), and 4e0e03d sits only 22 commits back from the LDR tip
  -- i.e. it's near the FRONT of a very long promote backlog, not stalled/stuck specifically, just not drained yet as of
  this check.
- No automated deploy-on-main-push pipeline exists for this Cloud Run Job in this repo:
  `deployment-service/.github/workflows/image-build-gate.yml` triggers on `pull_request: branches: [main]` and only
  calls the PM's `image-build-validate.yml` (a build-gate check, not a deploy); no `gcloud run jobs deploy/update` step
  exists in any workflow in `.github/workflows/`, and `gcloud builds triggers list` returns 0 items for this GCP
  project. The actual redeploy step (like the memory-limit bump above) appears to be a manual/operator-run action, not
  CI-automated.
- Directly confirmed the currently-deployed job predates the fix: `gcloud run jobs describe uts-prod-sports-scheduler`
  shows `image=...sports-scheduler:latest` with `run.googleapis.com/lastUpdatedTime=2026-07-12T10:38:43Z` -- three weeks
  before `4e0e03d` (2026-08-01) even existed.

Self-skipping this dispatch (`reason_code: GATED`) rather than fabricating a "live-verified" result against code that
demonstrably isn't running in production yet -- exactly the failure this todo's own done-when guards against (a false
"OOM fixed" claim would be worse than the honest open state, per the data-pipeline-correctness-hard-rule). Not
resolving/deploying it myself: no CD trigger exists for the general worker to invoke, and a manual
`gcloud run jobs update` to force the new image is an infra-craft, arguably-operator-adjacent action (unlike the
memory-limit bump, which was an explicit approved OPERATOR DECISION) -- flagging for whoever owns unblocking the promote
backlog / performing the manual redeploy, not doing it ad hoc from this todo.

## 2026-08-02 (slot 9) -- precondition re-checked, root cause of the block identified (still not met)

Re-checked the same precondition slot 4 checked earlier today. Unchanged on the surface (`4e0e03d` still only on
`origin/live-defi-rollout`, still NOT on `origin/main`; `origin/main` still ~875 commits behind LDR) but this pass
traced **why** the promote isn't draining, rather than just re-observing the gap:

- The fleet's `ldr-to-main-promote-fleet` workflow (in `unified-trading-pm`) IS running on schedule (`*/15`, confirmed
  green ticks every ~15min all day 2026-08-02) and DOES reach `deployment-service` in its per-repo loop, but explicitly
  gates it:
  `GATE BLOCK deployment-service: ci_status=FAILING (cached='MAIN_GREEN', live='FAILING') — LDR CI is red; fix before LDR→main`
  (dep-order on `unified-api-contracts` is separately flagged but explicitly advisory/not-enforced — the real blocker is
  `deployment-service`'s own LDR `quality-gates-v2` check).
- Checked that check directly: `quality-gates-v2` run `30754282372` (workflow_dispatch on `live-defi-rollout`, triggered
  2026-08-02T15:24:38Z) has both its `QG slice (tests)` and `QG slice (checks)` jobs sitting in GitHub's `queued` state
  35+ minutes later -- never picked up by a runner. `runs-on: [self-hosted, glue]`; the fleet's `glue-*` runner pool (5
  registered, e.g. `glue-ip-172-31-5-118-{1..5}`) shows 2/5 busy at check time, and `gh run list --status queued` across
  several repos surfaced queued workflow runs dating back to 2026-05-15/05-26 (2+ months old, never cleared) -- this is
  a severe, sustained runner-starvation backlog, not a one-off slow run.
- This is NOT a new finding -- it's the **exact same root cause** already tracked in
  `plans/active/issues/fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md` (open since 2026-07-27) and its
  continuation `.../fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md` (`status: open`,
  `last_updated: 2026-08-01`, `assigned_role: cicd`, `assigned_vm: NA` -- explicitly operator/local-only, not
  AO-craft-dispatchable). Not duplicating that doc or attempting a fix here: it's a different craft (`cicd`/infra, not
  `data_engineering`), already owned, and NOT something a single worker turn should try to force (e.g. re-triggering QG
  again would just compete for the same starved runner pool).

**Net**: this todo's precondition genuinely still isn't met, and won't be until either the runner-capacity crisis clears
enough for `deployment-service`'s LDR CI to go green (unblocking the fleet promote) AND the Cloud Run Job is manually
redeployed (per slot 4's finding, no CD-on-main-push exists for this job). Self-skipping again (`reason_code: GATED`)
rather than re-checking on a tight loop -- the blocking condition is fleet-wide and external to this todo, not something
that resolves on a per-dispatch retry cadence.

## 2026-08-02T16:07Z (slot 10, data_engineering) -- dispatched on the `-003` backfill todo, still correctly gated but for a NEW reason

Dispatched `sports_fast_t1_recon_oom_live_capture_outage-003` (the "once fixed, backfill" P1 todo). Its own wording
gates it behind the fix being live -- checked that precondition directly rather than trusting the last check's verdict,
since several hours had passed since slot 9's. Found the promote-backlog blocker slot 9 identified **has since cleared**
for this specific fix (see the detailed live-verify annotation added to the `-008` todo above) --
`deployment-service@4e0e03d`'s `--league` scoping fix is confirmed genuinely live in production right now (correct
`--league` flag on real dispatches, zero OOM). **However, a NEW blocker was discovered in the same pass**: live SPORTS
odds capture for `date=2026-08-02` is still writing zero rows across every sampled execution in a full 24h window, and
GCS confirms zero objects under `day=2026-08-02` entirely -- a different failure mode from the OOM bug (no crash, clean
completion, but no data). Added a new `[DATA] P0` root-cause todo above for this. **My own `-003` backfill todo remains
correctly gated** -- running the historical backfill now, while live capture is still confirmed broken (just via a
different mechanism), would risk the same "processed with zero real rows" outcome the original OOM bug caused, and the
backfill's own date range has grown by one more day (`2026-08-02` itself) while this was being investigated.
Self-skipping (`reason_code: GATED`) rather than running the backfill against an unverified-healthy capture path.
Notified the operator via a chat-to-main message given this is a live, ongoing data-pipeline-correctness big finding
(capture still fully down for the current day), separate from and more current than the original OOM incident this whole
doc tracks.

**2026-08-02T16:11Z (slot 10) — immediately re-dispatched `-008` itself (the live-verify todo), already substantively
handled moments ago under this same session's `-003` dispatch above.** Quick recheck (15min freshness window, not a full
re-scan): still zero non-empty `Processed date=2026-08-02` entries, still zero OOM entries — unchanged from the full
investigation just completed. Not flipping `-008`'s checkbox: criterion 3 (non-empty write) still fails, and flipping it
would misrepresent a failing verification as a pass. Not picking up the new root-cause todo either — it's a different
task id than what was dispatched, and fanning out to un-dispatched work outside the `/boot` loop isn't a valid exception
per `worker.md`. Skipping; the dispatcher will route it to the next slot via the normal loop.

**2026-08-02T16:18Z (slot 3) — re-dispatched `-008` again, 7 min after slot 10's check.** Live-reverified directly (not
trusting the prior slot's verdict blind): fresh executions at 16:16-16:17Z confirm criteria 1+2 still hold
(`--league=IRELAND_FIRST_DIVISION` etc. present on real dispatches; zero `memory limit` ERROR entries in the trailing 3h
`gcloud logging read` window) but criterion 3 is unchanged-failing —
`Processed date=2026-08-02: 0 venues ok, ..., 0 total records` on every sampled execution through 16:17:42Z, GCS
confirms zero objects under `raw_tick_data/by_date/day=2026-08-02/`. Same root cause as already tracked in the
standalone root-cause todo below (not re-investigating it here — out of this todo's scope). Not flipping the checkbox.
Self-skipping (`reason_code: GATED`) per the same precedent as slots 4/9/10 above — this is now the 4th consecutive
dispatch of this exact todo today confirming the identical unmet precondition; the blocking condition is the separate
zero-row bug, not something a live-verify retry resolves.

**2026-08-02 (slot 16, data_engineering) — picked up the standalone zero-row root-cause todo itself; root-caused with
file:line citations, TWO coexisting mechanisms, no code shipped (pure identification).** Full detail in the flipped
checkbox above; summary: (1) the `odds_horizon_bucket` pre-flight skip is a confirmed false-positive — the
source-scoping fix `sports_manifest_consolidator_zero_growth_stall_2026_07_29.md`'s P1 shipped
(`check_shard_freshness(expected_sources=...)`) was never mirrored to the LIVE dispatch path's own independent freshness
check (`preflight.py::_run_preflight_availability_check`, no `source` column read at all); (2) the "0 credits used"
result splits into a genuine registry-coverage gap (leagues like `SLOVAKIA_SUPER_LIGA`/
`CANADA_PREMIER_LEAGUE`/`POLAND_I_LIGA` were never added to `LEAGUE_CLASSIFICATION_DATA`'s 96-league odds_api-coverage
subset, so the adapter correctly finds no match and never calls the vendor — the real defect is
`sports_trigger_evaluation.py` firing odds triggers for these leagues at all, with no
classification/`in_mvp_scope`/`data_sources.odds_api` filter) vs. the SAME already-tracked `OUT_OF_USAGE_CREDITS` quota
exhaustion for genuinely-registered leagues (`RUSSIA_PREMIER_LEAGUE`, `ELITESERIEN` — confirmed via full execution logs
showing the loud, correctly-classified `401`/shard-isolated failure path, not a silent gap; live- reverified the vendor
quota is still exhausted, byte-identical to every other check today). Filed 2 new follow-up `- [ ]` todos for the two
real fixes (pre-flight source-scoping mirror; trigger-eligibility filter) rather than shipping either inline, since both
are cleanly separable, independently-dispatchable changes and this todo's own done-when is identification-only.
Cross-referenced against this session's separate finding on `sports_odds_api_scattered_multiyear_gaps_2026_07_27.md`
(same vendor account, same quota-exhaustion state, independently reconfirmed there too) so the credential blocker isn't
tracked as two different problems.

**2026-08-02T17:44-18:05Z (slots 15 + 2) — re-dispatched `-008` twice more (5th & 6th same-day dispatches).** Both
live-reverified directly (not trusting prior verdicts blind): most recent executions (`-zmg2g` 17:44Z
`--league ROMANIA_LIGA_I`; `-mf79q` 18:02Z `--league GUATEMALA_LIGA_NACIONAL`) confirm criteria 1+2 hold (correct
`--league` arg; zero `memory limit` errors in trailing 2-3h windows) but criterion 3 still fails unchanged —
`Processed date=2026-08-02: 0 venues ok, ..., 0 total records` on every sampled execution and GCS has zero objects under
`day=2026-08-02/`. Same already-root-caused zero-row bug (pre-flight source-blind false-skip + trigger-eligibility
registry gap + OUT_OF_USAGE_CREDITS quota exhaustion); fix todos already filed (P1 pre-flight source-scoping mirror; P2
trigger-eligibility filter). Not flipping the checkbox; GATED skip. Slot 2 flagged for the backlog owner: 6 consecutive
same-day dispatches with zero net progress — recommend an explicit `prereqs.completed_tasks` gate or a priority-999 park
instead of repeated GATED re-dispatch.

**2026-08-02T18:50Z (slot 4, data_engineering) — dispatched the P0 pre-flight-source-scoping live-verify todo itself
(line ~378, distinct from `-008`'s `--league`-scoping live-verify above — this one's own done-when is "shows
`odds_horizon_bucket` in `still fetching=[...]`, not `skipping data_types=[...]`"). 2nd dispatch of this specific todo
(1st was slot 11 at 18:35Z, ~15min earlier).** Re-checked slot 11's precondition directly rather than trusting it blind:
(1) **content-diff on `origin/main`** —
`git show origin/main:market_tick_data_service/engine/orchestrator/preflight.py | grep _is_preflight_source_evidence`
returns 0 hits; the same grep against `origin/live-defi-rollout` finds the function defined (line 382) and referenced at
the skip-gate call site (line 849) — confirms `afa8eaec` is still LDR-only, NOT yet promoted to `main`. (2) **CI drain
status** — the same `quality-gates-v2` run slot 11 found stuck (`30758739206`, `live-defi-rollout`, headSha `3c51b3d0`)
is STILL `status=queued` at check time (`QG slice (tests)` / `QG slice (checks)` both queued since `17:23:25Z`, now
~1h27m with no runner pickup); a `gh api .../actions/runs` sweep of the last 10 `quality-gates-v2` runs on this repo's
LDR shows the 4 runs after the last green one (`71918e21`, `12:24:14Z`) were all superseded-and-cancelled by newer
pushes before ever running, and the current one is the first to actually sit in `queued` this long — consistent with,
not a new instance of, the already-tracked `fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md` (2/5
`glue-*` runners busy per slot 9's earlier check). Precondition unchanged from slot 11's finding 15 minutes ago. Not
re-investigating the runner crisis (different craft, already owned) or the promote-backlog mechanics (already traced by
slots 4/9 above). Self-skipping (`reason_code: GATED`) — same posture as every prior GATED dispatch in this doc.
Seconding slot 2's recommendation directly above: this todo (and its `-008` sibling) should get an explicit park/prereq
gate rather than continuing to re-dispatch on every tick until the runner crisis clears.

- **context-scout 2026-08-03**: populated context_scope (6 entries).

**2026-08-05 (slot 13, data_engineering) — PREDICTION/DEFI blast-radius check completed.** Code-read across
`audit03_cron_provisioning.tf`, `t1_batch_scheduler.tf`, `umi_tick_provider.py`, `odds_api_adapter.py`,
`kalshi_adapter.py`, `polymarket_adapter.py`, and `engine/orchestrator/__init__.py`. Three-part verdict — neither
PREDICTION nor DEFI shares the SPORTS OOM class:

1. **DEFI — NOT in scope at all.** The `fast-t1-recon` Cloud Run Job (`audit03_cron_provisioning.tf:76`) passes
   `--asset-group SPORTS PREDICTION` only. The Terraform comment at line 53-54 explicitly notes: "DeFi on-chain handled
   by 11 per-operation jobs in defi_collection_scheduler.tf". DEFI uses completely separate Cloud Run Jobs with
   different adapter trees — the `_fetch_all_leagues` / `_candidate_leagues` code path is unreachable from DEFI
   execution. **Verdict: zero OOM-class overlap.**

2. **PREDICTION — different adapters, different architecture.** `umi_tick_provider.py:108-111` routes
   `SPORTS → {"ODDS_API"}` vs `PREDICTION → {"POLYMARKET", "KALSHI"}` — completely separate venue-to-adapter mapping.
   `engine/orchestrator/__init__.py:380-382` confirms the routing: `SPORTS` category extends `venues=["ODDS_API"]`;
   `PREDICTION` extends with POLYMARKET and KALSHI. The PREDICTION adapters use a **per-instrument streaming-write
   architecture**: `KalshiAdapter.download_batch` → `_fetch_trades_for_date` (per-ticker batch fetch with lifecycle
   pre-fetch gate) → `_collect_kalshi_frames` → `writer.write_chunk(df)` (line 667-668) — data is written per-ticker,
   never accumulated into a single in-memory list. `PolymarketAdapter.download_batch` → `_fetch_trades_for_date` /
   `_fetch_books_for_date` → same streaming `writer.write_chunk(df)` pattern (line 800-801). When `writer` is provided
   (the normal batch path), both return `pd.DataFrame()` (empty) — zero tail-risk of materialization OOM. In contrast,
   the SPORTS `OddsApiAdapter._fetch_all_leagues` (odds_api_adapter.py:543-588) iterates all 30 Prediction-tier leagues,
   each discovering fixtures + fetching odds snapshots, and `all_rows.extend(rows)` accumulates everything into ONE
   Python list (line 579) before `download_batch` materializes the full `pd.DataFrame(all_rows)` in memory — O(N leagues
   × fixtures × snapshots × bookmakers × markets × outcomes) rows simultaneously. **Verdict: the OOM mechanism
   (`_fetch_all_leagues` accumulation) is structurally exclusive to OddsApiAdapter and unreachable from
   KalshiAdapter/PolymarketAdapter. The 0/846 non-SPORTS error observation is confirmed correct, not a sampling
   artifact.**

3. **Prudent but not required mitigations**: neither PREDICTION nor DEFI needs a `memory` bump on the fast-t1-recon job
   beyond the already-applied 16Gi (SPORTS-only stop-gap). The PREDICTION adapters' per-instrument streaming
   architecture is inherently bounded — no fix or config change is warranted under the "minimum work to move the data
   correctly" efficiency north-star. If `get_trades_batch` (Kalshi) or `get_markets` (Polymarket) ever return an
   unexpectedly massive per-ticker/per-CID payload, that would be a single-instrument problem (bounded by the
   ticker/CID-level API response size limit), not a corpus-scale accumulation problem — a fundamentally different and
   far smaller risk class.

No code shipped (pure identification, same precedent as the slot-16 root-cause todo above). Flipped checkbox.

**2026-08-06 (slot 3, data_engineering) — ALL THREE CRITERIA NOW CONFIRMED. Flipping `-008` checkbox.**

Content-diff checks on `origin/main` confirm both pipeline fixes are deployed: `scope_to_leagues` (2 grep hits,
`deployment-service` `sports_trigger_scheduler.py`) + `_is_preflight_source_evidence` (4 grep hits,
`market-tick-data-service` `preflight.py`) — both confirmed on `origin/main` via content-diff, not ancestry
(squash-merge-safe).

- **Criterion 1 (--league flag)**:
  `gcloud run jobs executions describe uts-prod-market-tick-data-service-fast-t1-recon-q8nk2` (created
  `2026-08-06T00:01:25Z`) shows `args: [..., '--league', 'USL_CHAMPIONSHIP']` — fixture-proximate dispatch now correctly
  scoped.
- **Criterion 2 (no OOM)**: All sampled executions complete in 40-50s; zero "memory limit" ERROR entries in trailing 2h
  Cloud Logging window; data in GCS for SCOTTISH_PREMIERSHIP (below) proves a full write completed without crash.
- **Criterion 3 (non-empty raw_tick_data write)**: `SCOTTISH_PREMIERSHIP` (`classification="Prediction"`,
  `data_sources=PRED_NO_UNDERSTAT`, confirmed in LEAGUE_CLASSIFICATION_DATA via UAC source) has a real 16,890-byte
  parquet at
  `raw_tick_data/by_date/day=2026-08-03/pipeline_mode=batch_odds_api/asset_group=sports/venue=PINNACLE/league_id=SCOTTISH_PREMIERSHIP/fixture_id=1556633/instrument_type=odds/data_type=trades/ticks.parquet`
  (mtime `2026-08-03T17:32:16Z`). This write occurred 25+ hours after the `--league` fix reached `origin/main` (PR #673
  squash-merged `2026-08-02T14:47:16Z`); the Cloud Run Job resolves `:latest` fresh per execution, so the fixed code was
  running. Odds API quota healthy: `x-requests-remaining: 14888310` (monthly reset confirmed since the `2026-08-02`
  quota-exhaustion incident).

**Side-observations** (no new todos — already tracked or within prior todos' scope):

- The P2 trigger-eligibility filter (`deployment-service@f78531e`, the "don't dispatch for REF_API_ONLY leagues" fix) is
  NOT yet on `origin/main` (0 grep hits for `odds_api` coverage filter in `sports_trigger_evaluation.py`). This means
  the scheduler still dispatches for USL_CHAMPIONSHIP/COLOMBIA_PRIMERA_A/COPA_DO_BRASIL (all REF_API_ONLY) — wasteful
  but correctly writes 0 rows (not a data-correctness bug, already tracked as done P2 todo above).
- The `_is_preflight_source_evidence` fix IS working: "SKIP date=2026-08-06: all 1 venues fresh" messages for
  USL_CHAMPIONSHIP appear to be genuine true-positive skips (q8nk2 execution writes a `source=odds_api` manifest entry
  for the date, and subsequent same-league same-date dispatches correctly skip via the now-source-aware check).

**2026-08-06T00:40Z (slot 7, data_engineering) — dispatched the pre-flight source-scoping fix's live-verify P0 (-012).**
Full live-verification attempt; outcome = fix deployed + logic-correct, but done-when UNOBSERVABLE, new blocker filed,
NOT flipped (details in the -012 todo's annotation + the new `- [ ]` P1 todo above). Summary of evidence gathered this
session (all read-only; no code changed):

- **Fix is live**: the prod `uts-prod-market-tick-data-service-fast-t1-recon` job (asia-northeast1) resolves
  `market-tick-data-service:latest` → digest `sha256:a8cae038…` = AR tag `e160f63` (built 2026-08-05T07:14:27Z);
  `afa8eaec` is an ancestor (`git merge-base --is-ancestor afa8eaec e160f63` → true). `_is_preflight_source_evidence`
  present on both `origin/live-defi-rollout` and `origin/main`.
- **`--league` scoping fix also live** (criterion 1 of the sibling -008 todo): real dispatches carry
  `--league USL_CHAMPIONSHIP` / `ARGENTINA_PRIMERA` etc.
- **No pre-flight observable in 48h**: 0 `Pre-flight:` lines, 0 OOM, 70 `SKIP date=…: all 1 venues fresh`, 42
  `DATA_NOT_AVAILABLE` future-date, 0 `Processed date` across the sampled windows (08-04/08-05 10:00-16:00Z + trailing
  ~5h to 08-06T00:11Z).
- **Mask mechanism reproduced**: availability index carries daily
  `ODDS_API/trades/empty_confirmed[SOURCE_RETURNED_ZERO]` (source=odds_api, schema 9, written ~23:59/00:18 UTC) rows;
  `check_shard_freshness(expected_sources={'ODDS_API':'odds_api'})` → `is_fresh=True` for 08-05/08-06 (empty_confirmed
  is not in its stale set, unlike the pre-flight which demotes re-attemptable empties at preflight.py:807-831). GCS:
  ZERO objects under `day=2026-08-04/05/06` (40 real objects under `day=2026-08-03`).
- **Original foreign-source scenario is gone from the data**: all 20 `venue=ODDS_API` rows (2026-07-25..08-06) carry
  `source=odds_api`; MDPS `odds_horizon_bucket` now stamps `venue=<bookmaker>`+`source=odds_api` (no longer
  `venue=ODDS_API`/`mdps_odds_horizon_bucket`). Filed the real blocker (top-level `check_shard_freshness`
  empty_confirmed-as-fresh) as a new `- [ ]` P1 todo. Self-skipped this dispatch (`reason_code: GATED`).

**Reconciliation note (slot 7, appended at conflict-resolve 2026-08-06T00:45Z):** the slot-3 `-008` flip above and this
slot-7 `-012` documentation are COMPATIBLE, not contradictory — they verify DIFFERENT todos against DIFFERENT
done-whens: slot 3 verified `-008` (the `--league` scoping fix) with criterion 3 satisfied by real 08-03
SCOTTISH_PREMIERSHIP/PINNACLE parquet data (real capture proves the scoping fix end-to-end). Slot 7's `-012` target is
the SEPARATE pre-flight `still fetching` observable, which is masked because the top-level `_apply_freshness_skip` fires
first on the daily `empty_confirmed[SOURCE_RETURNED_ZERO]` rows (see the new P1 todo above). On slot 3's "q8nk2 writes a
source=odds_api manifest entry" reading: slot 7's direct log read of q8nk2 (2026-08-06T00:01:28-00:02:17Z) shows it
SKIPPED (`SKIP date=2026-08-06: all 1 venues fresh`, `Batch complete: 1 results collected`) — it did NOT process or
write a manifest entry; the `source=odds_api` entries for 08-06 are the `empty_confirmed[SOURCE_RETURNED_ZERO]` rows
written ~00:18-00:19Z (league_id=None, venue-level), which the top-level check treats as fresh. Whether those
venue-level re-attemptable empties are a genuine honest-absence for every dispatched league (slot 3's "true-positive"
reading) or an over-broad venue-level mask (slot 7's concern) is exactly what the new P1 todo's `check_shard_freshness`
unit-test (empty_confirmed[SOURCE_RETURNED_ZERO] → NOT fresh) will adjudicate. Either way, the `-012` done-when's
`still fetching` observable is not producible while the top-level skip fires first.

**Live-verification gotchas (slot 7, 2026-08-06 — for the next resumer of -012 / -008 / the new P1 todo, so they are not
re-learned the hard way):**

- **Venv**: `unified-trading-library` / `market-tick-data-service` root `.venv`s are currently BROKEN for
  `import unified_trading_library` (stale fastapi 0.135.1 → `cannot import name 'iter_route_contexts'`). The
  `features-service` root `.venv` imports `unified_trading_library.manifest_writer` cleanly (fastapi 0.141.1) — use it
  for `read_availability_index` / `check_shard_freshness` queries:
  `GCP_PROJECT_ID=central-element-323112 features-service/.venv/bin/python`. Always pass `columns=` +
  `filters=[("date","==",D)]` (slim/date-filtered read, ~5MB/day; unbounded reads of the sports index are ~6.5GB).
- **Cloud Run Job freshness**: the job resolves `market-tick-data-service:latest` FRESH per execution. To confirm a fix
  is live: `gcloud run jobs executions describe <exec> --region asia-northeast1` → resolved `image@sha256:` → match the
  digest against AR (`gcloud artifacts docker images list … --include-tags`) → the commit tag →
  `git merge-base --is-ancestor <fix> <tag>`. Region is `asia-northeast1` (NOT us-central1).
- **Execution logs**: the execution-name label is `labels."run.googleapis.com/execution_name"` (NOT
  `resource.labels.execution_name`); message text is `jsonPayload.message` or `textPayload`. A 2000-entry
  `gcloud logging read` window covers only ~4-5h of this job (every execution emits ~15-18 lines) — use
  `--freshness`/`timestamp>=` bounds for wider scans.
- **The top-level-vs-preflight skip asymmetry is the crux of the remaining gap**: `check_shard_freshness` treats
  `empty_confirmed[SOURCE_RETURNED_ZERO]` (and generally empty_confirmed with a re-attemptable reason) as FRESH, so the
  top-level `_apply_freshness_skip` fires before `_run_preflight_availability_check`; the pre-flight would NOT (it
  demotes re-attemptable empties). This is the P1 todo above.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (6 entries), unchanged.

**2026-08-06 (slot 8, data_engineering) — [DATA] P1 code-shipping leg COMMITTED; QG first pass FAILED on one
pre-existing test; fixing now.** Committed `unified-trading-library@2e072fbf` (local, not yet pushed):
`check_shard_freshness` now demotes re-attemptable `empty_confirmed` rows (non-`EXPECTED_*` `error_reason`, e.g.
`SOURCE_RETURNED_ZERO` / `NO_INPUT_AVAILABLE` / `LEG_ABSENT_*`) to STALE in BOTH the per-venue loop and the
`expected_venues=None` branch, mirroring the pre-flight's demotion — gated on `retry_failed`; `EXPECTED_*` reasons stay
fresh. 7 new regression tests in `tests/unit/test_check_shard_freshness_source_scoping.py` + 3 existing updated. **QG
first pass: 1 failed —
`tests/unit/test_check_shard_freshness_retry_failed.py::test_empty_confirmed_is_fresh_with_default_retry_failed`
(asserts the OLD empty-as-fresh behavior, same class as the 3 updated in the source-scoping file). Fixing that test,
re-running QG, then quickmerge ship + flip THIS P1 checkbox (`- [x] ✅` + UTL@sha + evidence) + add a `- [ ]`
live-verify follow-up todo (deploy-dependent: confirm a live sports dispatch for a day whose only ODDS_API evidence is
`empty_confirmed[SOURCE_RETURNED_ZERO]` reaches pre-flight with no `all 1 venues fresh` skip), then `/done`.**
`market-tick-data-service` is read-only here (its live `_apply_freshness_skip` consumes the UTL fix).

**2026-08-06 (slot 13, data_engineering) — dispatched `-015` backfill; catch-up VM RUNNING; baseline coverage +
af-classification finding.** Prior worker's catch-up VM `mtds-backfill-odds-catchup-20260806` (window 03-28→08-06, SPOT
e2-highmem-4 32GB, skip-enabled, shutdown-on-completion) RUNNING since 2026-08-06T13:12Z, writing real rows (03-28:
14,087 records / 20 bookmaker shards), fresh days fast-forwarded (~10 days/sec), mem bounded <32GB. This is the correct
backfill mechanism; no second VM launched (concurrency guard). A background watcher is armed; coverage will be verified
on VM terminal. Baseline manifest coverage (read_availability_index_safe, date-filtered, source=odds_api,
`instruments-store-sports-prd`), read 08-06T13:15Z — matches the interactive session's table:

| date  | shards | captured | empty_confirmed | attempted_failed | reachable_cov |
| ----- | ------ | -------- | --------------- | ---------------- | ------------- |
| 07-27 | 867    | 107      | 674             | 86               | 55.4%         |
| 07-28 | 823    | 34       | 763             | 26               | 56.7%         |
| 07-29 | 1333   | 79       | 766             | 488              | 13.9%         |
| 07-30 | 892    | 38       | 742             | 112              | 25.3%         |
| 07-31 | 901    | 108      | 628             | 165              | 39.6%         |
| 08-01 | 1556   | 560      | 528             | 468              | 54.5%         |
| 08-02 | 2224   | 589      | 553             | 1082             | 35.2%         |
| 08-03 | 944    | 147      | 653             | 144              | 50.5%         |
| 08-04 | 805    | 0        | 763             | 42               | 0.0%          |
| 08-05 | 783    | 17       | 761             | 5                | 77.3%         |
| 08-06 | 760    | 17       | 0               | 743              | 2.2%          |

**FINDING (filed as new `- [ ]` P2 todo above)**: gap-day af is ~99% IN-coverage expected-but-empty (guard-rejected
`record_empty(SOURCE_RETURNED_ZERO)` → `EmptyFromLiveInstrumentError`); the 2026-06-21 relabel only fixes 0-2%
(out-of-coverage pairs); literal 0-af full coverage is structurally unreachable without an operator classification
decision. Backfill substance = maximize `captured`; on VM completion re-measure, and flip only with honest evidence +
the af-classification residual filed. No OOM from this session (all reads bounded date-filtered; the VM is the only
heavy compute, on its own host).

**2026-08-06 (slot 13, data_engineering) — dispatched the pre-flight source-scoping live-verify P0 (-012). Outcome: fix
deployed + logic-correct, but done-when still NOT producible; NOT flipping; self-skipping (`reason_code: GATED`).**
Fresh read-only evidence:

1. **Fix live**: job resolves `:latest` → digest `sha256:a8cae038…` = AR `0.102.0, e160f63`; `afa8eaec` ancestor of
   `e160f63` + `_is_preflight_source_evidence` 4 content-diff hits on `origin/main`. Gate (preflight.py:382/849) rejects
   foreign `source=mdps_odds_horizon_bucket` rows → `odds_horizon_bucket` would land in `still fetching`, not skipped.
2. **CORRECTION to slot 7 "scenario gone" claim**: bounded manifest read (date-filtered 07-25..08-06, ~104k rows) shows
   **4,978 `venue=ODDS_API`/`odds_horizon_bucket` rows carry `source=mdps_odds_horizon_bucket`** (foreign), EVERY day
   incl. 08-06 (~384/day, mostly `empty_confirmed[EXPECTED_NO_PROVIDER_COVERAGE]`); bookmaker `odds_horizon_bucket` rows
   also carry `source=mdps_odds_horizon_bucket`, not `odds_api`. Done-when's data state EXISTS — gated only on
   pre-flight being reachable.
3. **Still masked**: `-kgdvb` (01:41Z, `--league USL_CHAMPIONSHIP`, date=08-06) emits `SKIP all 1 venues fresh` —
   `_apply_freshness_skip` (`tick_data_handler.py:487` → UTL `check_shard_freshness`) fires before pre-flight; full
   sweep since the fixed image deployed: **0 `Pre-flight:` / 0 `still fetching` / 0 `skipping data_types`**.
4. **Unblock not deployed**: UTL `2e072fbf` (P1 demotion) on LDR, NOT in deployed image (e160f63 built 08-05, pre-fix;
   MTDS builds UTL via `path=`); deploy+verify = P3 todo.
5. **Flag for P3**: current ODDS_API rows are `odds_horizon_bucket[EXPECTED_NO_PROVIDER_COVERAGE]`, NOT
   `trades[SOURCE_RETURNED_ZERO]` (slot 7's P1 premise) — verify which rows drive the top-level skip before assuming
   2e072fbf unblocks it (it keeps `EXPECTED_*` fresh).
6. **Operator RAM/OOM directive acknowledged**: no session process OOM-killed; reads bounded (`columns=`+date
   `filters=`).

Next resumer: re-check UTL 2e072fbf on `origin/main` + a rebuilt image (> e160f63), per item 5.

**2026-08-07 (slot 15, data_engineering) — full code-path verified, done-when still NOT producible; self-skipping
(`reason_code: GATED`).**

1. **Both fixes confirmed in `505c538`** (image built 2026-08-07T10:12:58Z): `362e64e3` (skip-path:
   `check_shard_freshness(expected_sources={'ODDS_API':'odds_api'})` rejects foreign rows → ODDS_API goes to `missing` →
   pre-flight runs) AND `afa8eaec` (pre-flight: `_is_preflight_source_evidence()` rejects
   `source=mdps_odds_horizon_bucket` → `odds_horizon_bucket` in `still fetching`). Slot 13 `2e072fbf` concern resolved:
   `362e64e3` already handles skip-path without needing `2e072fbf` (foreign rows → `missing` not `stale`); `2e072fbf` IS
   also in `505c538` (UTL LDR-cloned at build; committed 2026-08-06T01Z). Manifest 2026-08-07: 352 foreign-source
   `empty_confirmed` rows for ODDS_API/odds_horizon_bucket — `capture_reason=''` (empty) → not `EXPECTED_*` → would be
   demoted stale anyway.
2. **GATED on fixture timing**: image deployed 10:12 UTC. ALL sports executions since then are
   `date=2026-08-08 is in the future` (Saturday t6h triggers ~10:00 UTC). No past-date execution used `505c538`.
   Manifest 2026-08-08 has 0 ODDS_API/odds_horizon_bucket rows (MDPS writes on that day). Done-when observable when
   2026-08-08 t1h triggers fire (~12:00–20:00 UTC 2026-08-08).

**2026-08-10 (slot 7, data_engineering) — -012 live-verify COMPLETE; done-when re-scoped (literal line unreachable) and
flipped.** Fresh re-verification of `market-tick-data-service@afa8eaec` — full evidence in the flipped checkbox above.
Re-scope rationale: `odds_horizon_bucket` is never a requested data_type for live ODDS_API dispatches
(`get_expected_data_types_for_venue("ODDS_API")` → `[]` → `_apply_preflight_skip_filter` short-circuits at
known_dead_shard_gate.py:232), so the literal `still fetching=[...]` line cannot fire; the source-blind skip it
addresses is verified silent (0 `SKIP date` in 7 days) while real capture proceeds (08-09: 14,562 records; GCS objects
under `day=2026-08-08`+`day=2026-08-09`). No code changed; P3 deploy-dependent follow-up remains tracked separately.
