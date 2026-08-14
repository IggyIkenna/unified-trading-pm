---
doc_type: issue
title: >-
  Archived Progress Log detail for sports_fast_t1_recon_oom_live_capture_outage_2026_08_01.md (2026-08-01..08-06
  entries) — split out to keep the parent doc under its 1000-line hard cap
summary: >-
  The parent doc (`plans/active/issues/sports_fast_t1_recon_oom_live_capture_outage_2026_08_01.md`) hit its
  prettier-canonical 1000-line hard cap, which blocked ANY staged edit (including a pure pointer-append) via
  `check_line_caps`. This doc is the frozen historical record of that parent's 2026-08-01..2026-08-06 Progress Log
  entries — the investigation trail for the `--league`-scoping fix, the pre-flight source-scoping fix, and the
  associated GATED/premature-dispatch cycle — moved here verbatim (no content changed) so the parent can stay under cap
  while keeping the full history retrievable. The parent doc's own `## Progress Log` section now carries a short summary
  + pointer to this doc in place of this range. Not a standalone finding; this doc resolves nothing new.
status: resolved
nature: issue
asset_group: [sports]
stage: [data, live]
repos: [market-tick-data-service, deployment-service, unified-trading-library]
scope: [engineer, admin]
tags: [sports, data-pipeline-correctness, odds-api, archive, line-cap-split]
related:
  [
    /plans/active/issues/sports_fast_t1_recon_oom_live_capture_outage_2026_08_01.md,
    /plans/active/issues/stale_service_venvs_below_declared_fastapi_floor_2026_08_11.md,
  ]
created: 2026-08-14
author: ikennaigboaka
parent_epic: sports_master
priority: P3
source: ["parent doc line-cap split — slot 20, stale_service_venvs_below_declared_fastapi_floor todo 6"]
resolved_by: sports_fast_t1_recon_oom_live_capture_outage_2026_08_01.md
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-08-14
locked_by:
locked_since:
---

# Archived Progress Log — sports fast-t1-recon OOM outage (2026-08-01..08-06 entries)

> This is a frozen excerpt of `plans/active/issues/sports_fast_t1_recon_oom_live_capture_outage_2026_08_01.md`'s
> `## Progress Log` section, covering the 2026-08-01 through 2026-08-06 entries (the `--league`-scoping fix, pre-flight
> source-scoping fix, and the GATED/premature-dispatch cycle around both). Moved here verbatim to bring the parent doc
> back under its 1000-line hard cap. The parent's own Progress Log retains a summary pointing here, plus every entry
> from 2026-08-06 (slot 8) onward.

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

  > **Owner for the stale-venv / `iter_route_contexts` ImportError**:
  > /plans/active/issues/stale_service_venvs_below_declared_fastapi_floor_2026_08_11.md

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
