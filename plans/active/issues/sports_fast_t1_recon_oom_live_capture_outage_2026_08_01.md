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

- [ ] [DATA] P0. Root-cause why live SPORTS odds captures for `date=2026-08-02` write ZERO rows despite the `--league`
      scoping fix being confirmed live (no OOM, correct `--league` flag) — see the finding directly above. Check (a)
      whether the `Pre-flight: ... fully covered, skipping data_types=['odds_horizon_bucket']` line is a false-positive
      freshness-skip (no matching GCS/manifest evidence for that claim), and (b) why the other attempted data_types
      report `rows=0 credits_used=0` (0 API credits implies the call itself never fired, not an empty response) — likely
      in `odds_api_adapter.py`'s per-league fetch loop or the freshness-check it consults before dispatching a fetch.
      Done when: the specific code path causing the zero-row/zero-credit result is identified with a file:line citation,
      distinguishing genuine honest-absence (no odds available yet for these leagues) from a real bug. Repo:
      market-tick-data-service.
- [ ] [DATA] P1. Once fixed, backfill/re-fetch the resulting gap (2026-07-27, 2026-07-28, 2026-07-30, 2026-07-31, plus
      whatever additional days elapse before the fix ships — **as of 2026-08-02T16:07Z this now also includes 2026-08-02
      itself, since live capture is still confirmed at zero rows for today despite the OOM fix being live — see the new
      root-cause todo directly above**) via the Odds-API historical endpoint, same pattern as the prior month-long-gap
      backfill in `sports_batch_odds_api_capture_outage_recurrence_check_2026_07_26.md` item 1 -- coordinate so this
      doesn't duplicate that backfill's own in-flight/approved scope if it hasn't run yet. Done when: the manifest
      (`instruments-store-sports-prd`, manifest-only read, no GCS walk) shows full coverage for the affected date range
      at the intended granularity. (repo: market-tick-data-service)
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
