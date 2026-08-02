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
      (`league_canonical in leagues or     _raw_league_name(league_cls) in leagues`), so the canonical-slug format the
      writer emits matches on the first arm — no format-mismatch / silent-zero-row risk. Added 3 unit tests
      (`tests/unit/test_sports_trigger_league_scoping.py`) covering: `--league` injected for market-tick-data-service,
      instruments-service's own `--sports-entity` args left untouched, and multiple market-tick-data-service entries in
      one event all scoped. quality-gates.sh green (211s, `4e0e03d`); verified on origin. (repo:
      deployment-service@418ea8f,3e42536,4e0e03d — shipped via quickmerge, landed on live-defi-rollout)
      **Live-verification leg split into the new P0 todo directly below** — this fix still needs the
      LDR→staging→main→deploy pipeline to actually roll the new image before a live fixture-proximate trigger can be
      observed running it.
- [ ] [DATA] P0. Live-verify the `--league` scoping fix (deployment-service@4e0e03d, previous todo) once it has rolled
      out to the production sports-trigger-scheduler deployment (post LDR→staging→main→deploy): confirm a real
      fixture-proximate trigger (`odds_t24h`/`odds_t6h`/`odds_t1h`) dispatches `market-tick-data-service` WITH a
      `--league=<id>` flag (check the Cloud Run Job execution's container args, or the scheduler's own dispatch log line
      `TRIGGER [...] fixture=... league=...`), that the resulting execution writes non-empty `raw_tick_data` for its own
      league under `market-data-tick-sports-prd-central-element-323112`, and that the execution completes WITHOUT an OOM
      (no "configured memory limit was reached" log entry for that execution). Done when: at least one live post-deploy
      execution is confirmed on all three counts. (repo: deployment-service, market-tick-data-service)

      **2026-08-02T16:07Z (slot 10) — 2 of 3 criteria now confirmed live; 3rd criterion FAILS, new blocker found. NOT
                                              flipping done.** The deploy-gap slot 9 found (promote stuck behind the runner-capacity crisis) has since cleared
                                              for this specific fix: `deployment-service@4e0e03d`'s content (`scope_to_leagues` call in
                                              `sports_trigger_scheduler.py::fire_trigger`) is confirmed present on `origin/main` as of promote PR #673
                                              (`7fb58f1a`, squash-merged `2026-08-02T14:47:16Z`) — **correcting slot 4's ancestry-based "NOT on main" check**,
                                              which was a false negative from squash-merge non-ancestry (exactly the trap `review.md` § "Is commit `<sha>` live"
                                              warns about — content-diff, not `git merge-base --is-ancestor`, is the valid check here). Further: the
                                              `uts-prod-sports-scheduler` / `uts-prod-market-tick-data-service-fast-t1-recon` Cloud Run Jobs reference their
                                              image by the **mutable `:latest` tag**, and Cloud Run *Jobs* (unlike Services) re-resolve that tag fresh per
                                              execution — confirmed via `gcloud run jobs executions describe`: the most recent execution's *resolved* image
                                              digest (`sha256:6709207951...`) exactly matches the `sports-scheduler` image tagged both `latest` and
                                              `7fb58f1ae6f54c67...` (built `2026-08-02T14:51:05Z`, 4 min after the PR #673 merge). **So no manual
                                              `gcloud run jobs update` was actually needed for this job** — slot 4's conclusion there doesn't hold for a
                                              `:latest`-tag job spec. Criteria (1) and (2) are live-confirmed: `gcloud run jobs executions describe
                                              uts-prod-market-tick-data-service-fast-t1-recon-bllc8` (started `16:01:35Z`) shows
                                              `args: [..., '--league', 'SLOVAKIA_SUPER_LIGA']` and `condition: Completed True ... in 1m28.22s` with zero
                                              `"memory limit"` log hits anywhere in the trailing 2h window. **Criterion (3) FAILS — new, distinct blocker**:
                                              every sampled execution for `date=2026-08-02` across a full 24h log window (`Processed date=2026-08-02: 0 venues
                                              ok, 0 failed, 0 skipped, 0 total records` — checked 8+ executions, zero exceptions) shows genuinely zero rows
                                              captured; direct GCS listing confirms `raw_tick_data/by_date/day=2026-08-02/` has **zero objects at all** (vs.
                                              `day=2026-08-01` which has real per-venue data from slot 14's earlier verification). The pre-flight log line
                                              itself is suspicious: `Pre-flight: venue=ODDS_API date=2026-08-02 — fully covered, skipping
                                              data_types=['odds_horizon_bucket']` implies prior success for that data_type, but GCS shows nothing — a possible
                                              stale/false-positive freshness-skip signal. The OTHER attempted data_types report `Odds API batch complete:
                                              date=2026-08-02 rows=0 credits_used=0` — **0 credits used** suggests no HTTP call was even attempted, not merely
                                              an empty API response. Ruled out as a today-only fixture-availability fluke (checked across many different
                                              fixtures/leagues, same pattern every time, not isolated to one league). **This is NOT the OOM bug recurring** (no
                                              OOM, no crash-loop signature) — it is a separate, new capture-path defect. Filed as a new todo below; not
                                              root-causing inline (would need a code-level read of the `odds_horizon_bucket`/data_type dispatch path in
                                              `odds_api_adapter.py`, out of scope for this live-verification pass). **Net**: 2/3 done-when criteria met, 1 new
                                              blocker found — NOT flipping this checkbox; the actual restoration of live capture (what my own gated `-003`
                                              backfill todo needs) has not happened.

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
      (`if leagues and league_canonical not in leagues and          _raw_league_name(league_cls) not in leagues: continue`)
      skips every candidate that doesn't match. Poland's TOP division (Ekstraklasa, `api_football_id=106`) IS
      registered, but `POLAND_I_LIGA` (the SECOND division, `api_football_id=107`, confirmed via
      `unified_api_contracts/canonical/domain/sports/league_data_other.py:          177-188`,
      `classification="Features"`) is NOT a key in `LEAGUE_CLASSIFICATION_DATA` at all (confirmed via direct grep of
      both `league_classification_data_a.py`/`_b.py` — 0 hits for id 107) — so EVERY one of the 96 candidates fails the
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
      `deployment-service/deployment_service/sports_trigger_evaluation.py::          evaluate_pre_match_triggers` (lines
      46-96), which fires a pre-match trigger event for `for fixture in          fixtures:` with NO filter on the
      fixture's league `classification`/`in_mvp_scope`/`data_sources.odds_api` — it dispatches an odds-fetch Cloud Run
      execution for EVERY scheduled fixture regardless of whether that fixture's league was ever declared to have
      odds_api coverage. Wasteful (a real Cloud Run execution + vendor dispatch every 5 minutes per in-window fixture,
      for leagues that structurally can never produce odds rows), but NOT a data-loss/correctness bug — these leagues
      never had capturable odds_api coverage to lose. - **Already-tracked credential/quota blocker (loud,
      correctly-classified — confirmed for `RUSSIA_PREMIER_LEAGUE` and `ELITESERIEN`, both genuinely present in
      `LEAGUE_CLASSIFICATION_DATA` with real `odds_api_league_name` mappings)**: for these, the match at line 568
      SUCCEEDS, `_discover_fixtures` fires a real HTTP call to `/v4/historical/sports/{sport_key}/odds`, and BOTH
      sampled executions' full logs show
      `Discovery call for soccer_russia_premier_league on 2026-08-02 FAILED (re-raising): 401,          message='Unauthorized' ... error_code=OUT_OF_USAGE_CREDITS`
      (same for `soccer_norway_eliteserien`) — this propagates uncaught out of `_discover_fixtures`
      (odds_api_adapter.py:590-620, its own except block only logs + unconditionally re-raises, unlike
      `_run_league_fetch_loop`'s later, more graceful `OUT_OF_USAGE_CREDITS`-specific handling at line ~881) through
      `download_batch`/`_route_sports`, and is correctly caught by the top-level per-venue shard-isolation handler
      (`market_tick_data_service/engine/orchestrator/__init__.py:810`,
      `logger.error("Venue %s: unexpected error          (shard isolated): %s", ...)`) — producing
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
- [ ] [DATA] P0. Live-verify the pre-flight source-scoping fix (market-tick-data-service@afa8eaec, previous todo) once
      it has rolled out to the production `uts-prod-market-tick-data-service-fast-t1-recon` Cloud Run Job (same
      LDR→staging→main→deploy gap already tracked for the `--league`-scoping fix's live-verify todo above — check that
      todo's precondition state first, since both fixes ship through the same pipeline and may clear together). Done
      when: a live execution for a date whose only `(venue=ODDS_API, data_type=odds_horizon_bucket)` manifest evidence
      carries a foreign `source` shows `odds_horizon_bucket` in the pre-flight's `still fetching=[...]` log line, not
      `skipping data_types=[...]`. (repo: market-tick-data-service, deployment-service)

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

- [ ] [DATA] P2. Fix the sports pre-match trigger scheduler firing odds-fetch dispatches for fixtures in leagues with no
      odds_api coverage by design:
      `deployment-service/deployment_service/sports_trigger_evaluation.py::     evaluate_pre_match_triggers` (lines
      46-96) iterates every fixture with no filter on the fixture's league
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
              before assuming this todo is unblocked.

- [ ] [DATA] P2. Check whether PREDICTION and DEFI's fast-t1-recon dispatches are at risk of the same OOM class even
      though 0/846 sampled errors this pass were non-SPORTS -- a scoped blast-radius check (same method as
      `sports_batch_odds_api_capture_outage_recurrence_check_2026_07_26.md`'s DeFi/Prediction check) rather than an
      assumption that SPORTS-only observed means SPORTS-only affected. (repo: market-tick-data-service)

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

**2026-08-02T17:44Z (slot 15, data_engineering) — re-dispatched `-008` again, ~1.5h after slot 3's last check. 5th
consecutive dispatch of this exact todo today confirming the identical unmet precondition.** Live-reverified directly
(not trusting prior verdicts blind): `gcloud run jobs executions describe` on the most recent execution
(`uts-prod-market-tick-data-service-fast-t1-recon-zmg2g`) shows `--league ROMANIA_LIGA_I` in the container args
(criterion 1 holds); a `gcloud logging read` sweep of the trailing 2h45m window (15:00Z-17:44Z) returns zero
`"memory limit"` ERROR entries (criterion 2 holds); but `gsutil ls .../raw_tick_data/by_date/day=2026-08-02/` still
returns `CommandException: One or more URLs matched no objects` (the `day=2026-08-02` prefix doesn't exist at all in
GCS), and the trailing-log sweep through 17:37:25Z still shows only
`Processed date=2026-08-02: 0 venues ok, 0 failed, 0 skipped, 0 total records` on every sampled execution — criterion 3
still fails, unchanged from slots 4/9/10/3's checks earlier today. This is the same already-root-caused zero-row bug
(pre-flight source-blind false-skip + trigger-eligibility registry gap + the separate OUT_OF_USAGE_CREDITS quota
exhaustion for registered leagues), with its two fix todos already filed above (P1 pre-flight source-scoping mirror; P2
trigger-eligibility filter) — not re-investigating it here, out of this todo's scope. Not flipping the checkbox.
Self-skipping (`reason_code: GATED`) per the same established precedent as the 4 prior dispatches today — the blocking
condition is the separate zero-row bug, not something a live-verify retry resolves, and repeatedly re-dispatching this
exact todo on a tight loop is pure waste until one of the two filed fix todos actually ships.

**2026-08-02T18:05Z (slot 2, data_engineering) — re-dispatched `-008` again, ~20min after slot 15's last check. 6th
consecutive dispatch of this exact todo today confirming the identical unmet precondition.** Live-reverified directly:
`gcloud run jobs executions describe` on the most recent execution
(`uts-prod-market-tick-data-service-fast-t1-recon-mf79q`, completed `2026-08-02T18:02:13Z`) shows
`--league GUATEMALA_LIGA_NACIONAL` in the container args (criterion 1 holds); a `gcloud logging read` sweep of the
trailing 3h window returns zero `"memory limit"` ERROR entries (criterion 2 holds); but
`gcloud storage ls .../raw_tick_data/by_date/day=2026-08-02/` returns `ERROR: One or more URLs matched no objects` (zero
GCS objects for today), and the trailing-1h log sweep shows only
`Processed date=2026-08-02: 0 venues ok, ..., 0 total records` on every sampled execution — criterion 3 still fails,
unchanged from all 5 prior checks today. Same already-root-caused zero-row bug (pre-flight source-blind false-skip +
trigger-eligibility registry gap + OUT_OF_USAGE_CREDITS quota exhaustion), fix todos already filed above (P1 pre-flight
source-scoping mirror; P2 trigger-eligibility filter) — not re-investigating, out of this todo's scope. Not flipping the
checkbox. Self-skipping (`reason_code: GATED`). **Flagging for the backlog owner**: this is now 6 consecutive same-day
dispatches of this exact todo with zero net progress toward the actual gate (the precondition can only clear once one of
the two filed fix todos ships) — recommend an explicit `prereqs.completed_tasks` gate or a priority-999 park against
this task rather than relying on auto_park's implicit GATED-skip threshold, since the repeated-dispatch pattern is now
clearly established rather than a one-off.
