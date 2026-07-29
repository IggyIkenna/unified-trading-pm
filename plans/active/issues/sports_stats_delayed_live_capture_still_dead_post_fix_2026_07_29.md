---
doc_type: issue
title:
  Post-match trigger lookback fix IS deployed and firing, but live Understat XG capture is STILL zero — two further,
  independent root causes found (venue-adapter-key registry gap + in-memory poller state loss)
summary: >-
  Follow-up to sports_post_match_trigger_24h_lookback_bug_2026_07_27.md's Check 4 (live re-verification todo). Confirmed
  the `deployment-service@5b5d227` lookback-window fix reached production (content-identical on `origin/main`, built
  into the `sports-scheduler:latest` Cloud Run Job image 2026-07-28T22:37:45Z, running since) and the `stats_delayed`
  trigger now genuinely fires live (1382 lifetime / 85 post-redeploy `latency_observations` rows, vs. 0 historically) —
  the original lookback bug IS fixed. But 28+ hours and 1382 real trigger fires later, the manifest still shows ZERO
  fresh (non-`batch_understat`) `data_type=XG` captures, and ZERO `first_success=True` latency confirmations (0/1382,
  all-time). Traced two independent, further causes: (1) `FirstSuccessPoller`'s pending retry state is a plain in-memory
  dict with no persistence, while the scheduler runs as a `--one-shot` Cloud Run Job re-invoked fresh every 5 minutes —
  any registered retry entry is discarded before it can ever be polled, so `first_success` can structurally never become
  `True` regardless of whether the real fetch eventually succeeds (an observability/confirmation gap, not necessarily a
  capture-blocking one). (2) `UNDERSTAT` (and 4 sibling enrichment venues: FOOTYSTATS, TRANSFERMARKT,
  SOCCER_FOOTBALL_INFO, OPEN_METEO) have ZERO entry in `unified_api_contracts/registry/venue_adapter_keys.py`, so live
  production logs repeatedly show `ERROR URDI fetch: 5 venue(s) failed with PERMANENT errors: [..., ('UNDERSTAT',
  'UNSUPPORTED'), ...]` — despite a working `UnderstatAdapter` class already registered in instruments-service's OWN
  factory (`reference_data/adapters/sports/factory.py`, key `"understat"`) and already proven capable of capturing real
  XG data (the 7,714 all-time-captured `batch_understat` rows came from a manual backfill script that presumably
  bypassed the URDI registry path). CORRECTED same-day: the working adapter class lives in a separate, architecturally
  distinct sports-only sub-factory (`BaseSportsReferenceAdapter`) than the generic URDI/master factory
  (`BaseReferenceDataAdapter`) these venues would resolve through as real keys — fixed as `NO_ADAPTER_YET` sentinels
  instead (the honest declaration), which does NOT by itself silence the recurring warning or explain the zero-XG
  residual; a new follow-up todo traces why these venues appear in the URDI fetch list at all.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [deployment-service, unified-api-contracts, instruments-service]
scope: [engineer]
tags:
  [sports, scheduler, post-match-trigger, understat, xg, urdi, adapter-registry, data-completeness, bug, live-pipeline]
related:
  [
    /plans/archive/issues/sports_post_match_trigger_24h_lookback_bug_2026_07_27.md,
    /plans/active/sports_live_availability_and_source_latency_2026_07_24.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
  ]
created: 2026-07-29
priority: P0
parent_epic: sports_master
source:
  "worker, slot 2, running the Check 4 live re-verification todo in
  sports_post_match_trigger_24h_lookback_bug_2026_07_27.md (VERIFY P1) — confirmed the lookback fix deployed and firing,
  then found the manifest still shows zero fresh XG despite that, and traced two further, independent causes"
assigned_vm: planning
execution_scope: orchestrator-agent
estimate_class: infra
drift_direction: advance-code
depends_on: []
resolved_by:
locked_by:
---

# Sports `stats_delayed`/XG live capture still dead after the lookback fix — two further root causes

## What I found

### Step 1 — confirmed the lookback fix (`5b5d227`) IS live-deployed

`git merge-base --is-ancestor 5b5d227 origin/main` reads NO (the LDR→main promote flow squash/rebases, so the exact SHA
isn't preserved) — but a direct content diff proves the fix landed anyway: `origin/live-defi-rollout`'s and
`origin/main`'s current `deployment_service/sports_trigger_scheduler.py` + `sports_trigger_state.py` are byte-identical,
and `git merge-base --is-ancestor c988d1c origin/main` (the commit that carried `5b5d227`'s content into `main`,
2026-07-27T20:40:55Z) → YES against main HEAD `252792f`.

The deployed Cloud Run Job `uts-prod-sports-scheduler` runs image `sports-scheduler:latest`. Resolved that tag's digest
(`sha256:317ac71...`) to the SHA-tagged image `252792fcfbeb13805c5a5e0d8d7cf7eecf96525c` — exactly `main` HEAD —
built/pushed **2026-07-28T22:37:45Z**. The job's `latestCreatedExecution` at query time was `2026-07-29T00:40:01Z`, i.e.
running that image. **Redeploy cutoff for all checks below: `2026-07-28T22:37:45Z`.**

### Step 2 — the trigger now genuinely fires live (lookback bug confirmed fixed)

Queried `instruments-store-sports-prd-central-element-323112/_index/latency_observations/` (columns `trigger_name`,
`recorded_at_utc`, `first_success`, `fetched_rows`, `source`):

- `stats_delayed` total (all-time): **1382** rows, first at **2026-07-27T20:46:17Z** (44 min after the fix commit was
  authored) — this trigger had **ZERO** observations ever before the fix (per the parent doc's original finding).
- Post-redeploy-cutoff (`>2026-07-28T22:37:45Z`): **85** fresh rows, most recent `2026-07-29T00:41:15Z`.
- Day-by-day count: 710 (07-27) / 618 (07-28) / 54 (07-29, partial day at query time).

This structurally confirms the lookback-window fix works: the trigger's fire window (`kickoff+25.25h..26.25h`) is no
longer being missed by `get_upcoming_fixtures()`'s old `<=2h` cutoff.

### Step 3 — but ZERO genuine success confirmations, ever, and ZERO fresh XG manifest captures

- `first_success` value_counts on ALL 1382 `stats_delayed` rows: `{False: 1382}` — **not one `True`, ever**, in 28+
  hours of live firing.
- `fetched_rows` on all 1382 rows: constant `-1` (the "first-attempt sentinel" per `sports_latency_observation.py`'s
  `build_observations_for_fire` docstring — never a real fetched-row count).
- `source` on all 1382 rows: `understat` (100%) — consistent, not a data-quality issue.
- Manifest `data_type=XG`, `capture_status=captured`, filtered to `written_at > 2026-07-28T22:37:45Z` AND
  `pipeline_mode != batch_understat` (i.e. excluding the known 2026-07-13..22 one-shot historical backfill): **0 rows**.
  All 7,714 all-time-captured XG rows remain 100% `pipeline_mode=batch_understat` from that same backfill window —
  unchanged since the parent doc's original finding.

Per the parent doc's Check-4 todo's own done-when: "if none appears after a full day-plus of live operation
post-redeploy, escalate — that would mean a second, still-undiagnosed issue." That condition is met. Traced two
independent candidate causes below.

### Root cause A (confirmed structural, code-level) — `FirstSuccessPoller._pending` cannot survive `--one-shot`

`deployment_service/sports_latency_observation.py`'s `FirstSuccessPoller` (lines ~382-570) maintains its retry state in
a plain in-process `dict` (`self._pending: dict[str, FirstSuccessPendingEntry] = {}`, line 402) with **no persistence
mechanism** — no read/write to the state bucket that `PeriodicTierState`/`last_run[tier]` DOES use
(`resolve_state_bucket()`, `sports_trigger_scheduler.py:126-165`).

`register_from_event()` is called on trigger fire (`sports_trigger_scheduler.py:422`), setting `next_poll_utc` 15
minutes in the future (`next_poll_utc_for_attempt(0, now)`, `FIRST_SUCCESS_EARLY_INTERVAL_MIN=15`). `poll()` is called
once per invocation (`sports_trigger_scheduler.py:844`) to retry any DUE pending entries and write the confirming
`first_success=True` row on `rc==0`.

But the deployed Cloud Run Job runs `--one-shot` (confirmed: terraform `sports_scheduler_cron.tf` args
`["python", "-m", "deployment_service", "sports-trigger", "run", "--one-shot", ...]`, invoked by a 5-minute Cloud
Scheduler cron) — **a fresh container/process per invocation**, exiting almost immediately after its one pass. Any entry
`register_from_event()` creates is gone the moment that process exits; the NEXT invocation 5 minutes later starts with
an empty `_pending` dict. `poll()` therefore can never see an entry that was registered in a PRIOR invocation, and the
entry registered THIS invocation isn't due for 15 more minutes — so it's structurally impossible for `poll()` to ever
confirm a `first_success=True` row in this deployment model, independent of whether the underlying Understat fetch would
have succeeded. This is the same class of design/deployment mismatch as the original lookback bug (a mechanism designed
assuming a long-lived process, deployed as a stateless one-shot job).

**This explains finding #1 (0/1382 first_success=True) but does NOT by itself explain finding #2 (0 fresh XG captures)**
— the real production dispatch (`_dispatch_services`, `sports_trigger_scheduler.py:412`) fires independently of
`FirstSuccessPoller` and does NOT depend on it for the actual fetch attempt.

### Root cause B (confirmed code-level, likely the real blocker) — `UNDERSTAT` has no registered URDI adapter key

Live Cloud Run Job logs (`uts-prod-instruments-service-sports-fixtures`, `gcloud logging read`, last 24h) repeatedly
show, on the order of every ~5 minutes:

```
WARNING No URDI adapter for 5 venue(s) — register a key (or NO_ADAPTER_YET sentinel) in
         unified_api_contracts/registry/venue_adapter_keys.py: ['FOOTYSTATS', 'UNDERSTAT', 'TRANSFERMARKT',
         'SOCCER_FOOTBALL_INFO', 'OPEN_METEO']
ERROR   URDI fetch: 5 venue(s) failed with PERMANENT errors: [('FOOTYSTATS', 'UNSUPPORTED'), ('UNDERSTAT',
         'UNSUPPORTED'), ('TRANSFERMARKT', 'UNSUPPORTED'), ('SOCCER_FOOTBALL_INFO', 'UNSUPPORTED'), ('OPEN_METEO',
         'UNSUPPORTED')]
```

Confirmed via direct grep: `unified_api_contracts/registry/venue_adapter_keys.py` has **zero** entries for any of these
5 venues (neither a real key nor the explicit `NO_ADAPTER_YET` sentinel the file's own docstring says every
canonical-but-adapterless venue MUST carry). Yet `instruments_service/reference_data/adapters/sports/factory.py` (the
`_ADAPTERS` table) **already has a working `"understat": UnderstatAdapter` entry** — and the 7,714 all-time XG
`captured` manifest rows (100% `pipeline_mode=batch_understat`, all written in the 2026-07-13T23:48..2026-07-22T05:23
window) prove that adapter genuinely works when invoked directly (presumably by
`scripts/backfill_understat_xg_epl_2025_2026_06_29.py`, which does not appear to go through the URDI registry path).

**Not fully isolated**: the one full execution log I read end-to-end for an XG-entity dispatch
(`uts-prod-instruments-service-sports-fixtures-r5jz5`, 2026-07-29T00:47Z) showed
`Per-fixture enrichment: 46 fixtures x 0 entities = 0 calls queued` — i.e. it never even reached a fetch attempt,
because none of that date's fixtures were in Understat's covered-league set (`_UNDERSTAT_LEAGUE_COVERAGE` in
`unified_api_contracts/canonical/domain/sports/provider_league_ids.py` — 5 European top flights; this filtering is BY
DESIGN, not a bug). The specific "URDI fetch: 5 venue(s) failed" error I traced to one execution
(`uts-prod-instruments-service-sports-fixtures-tbb2z`) was itself entity-scoped to `LINEUPS`, not `XG` — so it may be a
shared, entity-agnostic "venue universe" completeness check (`Date filter <date>: N instruments active`) rather than
something that fires ONLY on (or blocks) the XG-specific dispatch path. **I did not confirm whether an XG-entity-scoped
execution, on a date/league that DOES fall inside Understat's coverage, also hits this exact adapter-key error** — that
would require watching live executions across enough days to catch a top-5-league fixture inside the `stats_delayed`
window, which is out of scope for this read-only verification pass.

Regardless of that gap, the missing registry entries are an objective, confirmed code fact and a real live-production
error recurring every ~5 minutes — independently worth fixing, and the most likely explanation for why Understat/XG (and
FootyStats/Transfermarkt/SFI/open-meteo) enrichment has never worked via ANY live/URDI-mediated path, only via one-off
manual backfill scripts that bypass the registry.

**Correction (2026-07-29, same-day, slot-2): the initial fix (real adapter keys) was WRONG — corrected to
`NO_ADAPTER_YET` sentinels.** `instruments_service/reference_data/adapters/sports/factory.py`'s `_ADAPTERS`
(`BaseSportsReferenceAdapter` — fixture/league/team/odds-shaped methods) is a SEPARATE, architecturally-distinct factory
from THIS registry's actual consumer, `instruments_service/reference_data/factory.py`'s `_ADAPTERS`
(`BaseReferenceDataAdapter` — generic `get_instruments()`), which is what `get_adapter_for_canonical_venue()` (what a
real `VENUE_TO_ADAPTER_KEY` entry resolves through) actually knows about. A real key pointing at `"understat"` etc.
would raise `ValueError` (unresolvable class) the moment `urdi_reference_provider._fetch_one_venue` tried to instantiate
it — caught live by the PRE-EXISTING `test_every_uac_adapter_key_resolves_to_a_class` regression test in
instruments-service, which is exactly the "key→class closure" gate it exists for. Registered these 5 as `NO_ADAPTER_YET`
instead (honest declaration: these venues are never meant to flow through the generic URDI/master- factory path at all —
real capture is entirely the sports orchestrator's own per-fixture entity-scoped dispatch, `sports_fixtures.py`, which
calls the sports sub-factory directly, not `get_adapter_for_canonical_venue`).

**Important residual: this does NOT silence the "No URDI adapter for N venue(s)" warning in production.** Both a missing
key and an explicit `NO_ADAPTER_YET` land in the same `unsupported` bucket in
`urdi_reference_provider.fetch_instruments_for_all_venues` (`adapter_key is None or adapter_key == NO_ADAPTER_YET`) — so
the warning/error will keep firing exactly as before. The sentinel fixes the REGISTRY's honesty (declared vs.
silently-missing) and unblocks the `VENUES_BY_ASSET_GROUP`/factory-closure test invariants, but does NOT stop the noisy
log line, and (per the league-coverage finding above) was likely never the actual reason XG captures are zero either.
**The real open question — why do these 5 enrichment-provider names appear in `fetch_instruments_for_all_venues`'s
`venues` argument at all, when they aren't even in `VENUES_BY_ASSET_GROUP["sports"]`** — is unresolved; tracing
`active_venues`'s construction for a sports dispatch is the next step, tracked as a new todo below rather than solved
here (this pass already went one level deeper than its original mechanical scope; that trace is a genuinely separate
investigation).

## Why it matters

Sports XG/advanced-stats (Understat/FootyStats) and 4 other enrichment sources have apparently NEVER been captured via
any live/URDI-registry-mediated dispatch path, only via manual backfill scripts — a live-pipeline data-completeness gap
on real production sports data, same severity class as the original lookback bug this doc follows up on.

## Recommended decision

Two independently scoped, mechanically-determinable fixes (neither is a design call — do NOT bundle):

1. **Register the 5 missing venue keys** in `unified_api_contracts/registry/venue_adapter_keys.py`
   (FOOTYSTATS/UNDERSTAT/TRANSFERMARKT/SOCCER_FOOTBALL_INFO/OPEN_METEO), mapping each to its existing
   `instruments_service/reference_data/adapters/sports/factory.py` `_ADAPTERS` key (confirmed `"understat"` exists;
   verify the other 4 factory keys before registering). Add a regression test asserting `venue_adapter_keys.py` declares
   an entry (real key or `NO_ADAPTER_YET`) for every venue that ALSO has a live `_ADAPTERS` factory registration, so
   this class of drift can't silently recur. Then re-run the manifest query (Step 3 above) after a full day-plus of live
   operation post-fix to confirm the registration alone closes the gap, or surfaces a further residual.
2. **Persist `FirstSuccessPoller._pending`** across `--one-shot` invocations (e.g. alongside `PeriodicTierState` in the
   same state bucket) so `first_success=True` confirmations become structurally possible again — this is
   observability/confirmation only, does not gate the real dispatch, so it can ship independently and at lower urgency
   than #1.

## Todos

- [x] ✅ [INFRA] P0. Register `FOOTYSTATS` / `UNDERSTAT` / `TRANSFERMARKT` / `SOCCER_FOOTBALL_INFO` / `OPEN_METEO` in
      `unified_api_contracts/registry/venue_adapter_keys.py` as `NO_ADAPTER_YET` sentinels (NOT real keys — see the
      2026-07-29 correction above: they resolve through a DIFFERENT, architecturally-incompatible factory than their
      working `_ADAPTERS` entry lives in). Added to `EXPECTED_SENTINEL_VENUES` in
      `unified-api-contracts/tests/unit/test_venue_adapter_keys.py`'s `test_sentinel_set_is_exactly_the_declared_one`
      (the pre-existing regression guard already covers "don't let this venue silently drop out of the registry" going
      forward — no new cross-repo test needed; an initial attempt at one incorrectly targeted the wrong (`master`, not
      `sports`) factory dict and was reverted). **Done when**: the fix ships and instruments-service's full
      `quality-gates.sh` is green (was RED on the initial real-key attempt via the pre-existing
      `test_every_uac_adapter_key_resolves_to_a_class` + `test_adapter_data_sources_covers_all_adapters` gates — both
      now pass with the sentinel correction). `unified-api-contracts@6186be5a`, full `quality-gates.sh` green (335s),
      shipped via quickmerge to `live-defi-rollout`.
- [ ] [INFRA] P1. **NEW, opened by the correction above.** Trace why `FOOTYSTATS`/`UNDERSTAT`/`TRANSFERMARKT`/
      `SOCCER_FOOTBALL_INFO`/`OPEN_METEO` appear in the `venues` argument passed to
      `urdi_reference_provider.fetch_instruments_for_all_venues()` for a live sports dispatch at all, given they are NOT
      in `VENUES_BY_ASSET_GROUP["sports"]` — find the call site that builds `active_venues` for sports (likely a "core
      entity"/"Date filter" completeness pass, given the one execution log I traced this to was entity-scoped to
      `LINEUPS`) and either exclude these 5 enrichment-provider names from that list (they were never meant to be
      URDI-fetchable "venues") or confirm there's a reason they're intentionally included that this pass didn't surface.
      **Done when**: a fresh day-plus of live Cloud Run Job logs for `uts-prod-instruments-service-sports-fixtures`
      shows zero `URDI fetch: N venue(s) failed with PERMANENT errors` lines mentioning any of these 5. Repo:
      instruments-service.
- [ ] [VERIFY] P1. **Depends on the todo above landing + redeploying (or on confirming no fix is needed).** After a full
      day-plus of live operation post-that-fix, re-run this doc's Step 3 manifest query (`data_type=XG`,
      `capture_status=captured`, `written_at` > the new redeploy cutoff, `pipeline_mode != batch_understat`) — confirm a
      fresh row appears (closes this issue) or, if still zero, escalate further (a fourth cause would remain). Repo:
      instruments-service / market-tick-data-service (read-only). — **Checked 2026-07-29T03:50Z-04:00Z (slot 5,
      data_engineering): premature, both this todo's own gates are still open, not the "confirming no fix is needed"
      escape hatch.** (1) Item-2 (the `active_venues` trace above) has NOT landed — grepped `instruments-service` for
      any commit since `2026-07-29T00:00Z` touching `urdi_reference_provider`/`active_venues`: none. (2) Only ~2h20m
      elapsed since the item-1 sentinel fix shipped (`unified-api-contracts@6186be5a`, `2026-07-29T01:30:49Z`) vs. the
      "day-plus of live operation" this todo requires — re-running Step 3 now is a checkpoint, not a verdict, either
      way. **Attempted the escape hatch anyway** (confirm item-2's fix isn't needed by checking whether a real
      XG-entity-scoped dispatch ever hits the adapter-key error) — **inconclusive, do not treat as resolved**: a single
      direct execution trace (`03:51:33-03:51:50Z`, `Sports entity filter from CLI: XG`) showed ZERO
      `No URDI     adapter`/`URDI fetch...failed` lines — that execution instead logged
      `Per-fixture enrichment: 39 fixtures x 0     entities = 0 calls queued` (same "0 calls queued" pattern the parent
      doc's Step-3 investigation already flagged). But a bulk nearest-preceding-line correlation over the last ~10h of
      logs (137 `No URDI adapter` occurrences) attributed 48/137 to a preceding `XG` entity-filter line — the two
      signals conflict because the Cloud Run Job runs multiple entities as CONCURRENT subprocesses whose log lines
      interleave (e.g. `XG` and `FIXTURE_STATS` entity-filter lines land within the same second in the combined log), so
      "nearest preceding line" is not a valid per-execution correlation without a trace/PID discriminator — exactly the
      gap item-2's own scope already flagged ("out of scope for this read-only verification pass"). **New finding for
      whoever picks up item-2**: one clean, non-interleaved trace (`03:26:21-03:26:42Z`) DOES show the error firing
      directly after `LEAGUES`/`INJURIES`/ `TRANSFERS` entity-filter lines, immediately followed by
      `Date filter <date>: N instruments active (from URDI     fetch)` — confirms the doc's own hypothesis that this is
      a shared "core entity"/venue-universe completeness check, not something scoped to a single specific entity; worth
      using a trace/PID discriminator (not nearest-preceding-line) to nail down definitively whether XG ever hits it.
      **Step 3 manifest re-check (checkpoint, not final)**: still 0 fresh non-`batch_understat` XG captures since the
      `2026-07-28T22:37:45Z` cutoff; all 7,714 captured XG rows remain 100% `batch_understat`, max `written_at` still
      `2026-07-22T05:23:36Z` — unchanged from the parent doc's original finding, as expected this early. Not completable
      this turn (both gates — item-2 landing and day-plus elapsed — still open). Releasing via
      `/skip-current-task {"reason_code": "GATED"}`. Next dispatch: once item-2 lands AND a day-plus has elapsed since
      ITS redeploy (not item-1's), re-run Step 3 for the real verdict; if item-2 is deprioritized/not attempted, wait
      out the day-plus from item-1's `01:30:49Z` cutoff instead (i.e. not before `2026-07-30T01:31Z`) before
      re-checking. — **Checked 2026-07-29T05:02Z (slot 10, data_engineering): still premature, both gates open, no full
      re-verification attempted (would be redundant with the 03:50Z-04:00Z checkpoint above)**. Confirmed item-2 has NOT
      landed: `git log --since="2026-07-29T00:00:00Z" -- '*urdi_reference_provider*' '*active_venues*'` in
      instruments-service returns zero commits. Current time (`05:02Z`) is well before the day-plus fallback gate
      (`2026-07-30T01:31Z`). Releasing via `/skip-current-task {"reason_code": "GATED"}` without re-running Step 3 — the
      checkpoint 65min ago already established "unchanged, as expected this early" and neither gate condition has moved
      since. Next dispatch: same condition as above (item-2 lands, or `2026-07-30T01:31Z` passes) — until then, a bare
      item-2-landed check (no manifest re-query) is enough to confirm still-gated. — **Checked 2026-07-29T09:06Z (slot
      14, data_engineering): still premature, both gates open, bare check only (no manifest re-query, per the prior
      check's own guidance)**. Confirmed item-2 still NOT landed:
      `git log --since="2026-07-29T00:00:00Z" -- '*urdi_reference_provider*' '*active_venues*'` in instruments-service
      (HEAD `f3cd7dd11`) returns zero commits. Current time (`09:06Z`) still well before the day-plus fallback gate
      (`2026-07-30T01:31Z`, ~16h away). No change since the 05:02Z check. Releasing via
      `/skip-current-task {"reason_code": "GATED"}`. Next dispatch: same condition as above. — **Checked
      2026-07-29T14:12Z (slot 6, data_engineering): still premature, both gates open, bare check only (no manifest
      re-query, per the prior check's own guidance)**. Confirmed item-2 still NOT landed:
      `git log --since="2026-07-29T00:00:00Z" --all -- '*urdi_reference_provider*' '*active_venues*'` in
      instruments-service (HEAD `0dfe61e5`) returns zero commits. Current time (`14:12Z`) still well before the day-plus
      fallback gate (`2026-07-30T01:31Z`, ~11h away). No change since the 09:06Z check. Releasing via
      `/skip-current-task {"reason_code": "GATED"}`. Next dispatch: same condition as above.
- [ ] [INFRA] P2. Persist `FirstSuccessPoller._pending` across `--one-shot` invocations (state-bucket-backed, same
      pattern as `PeriodicTierState`) so `first_success=True` / genuine `fetched_rows` confirmations become structurally
      possible. Lower urgency than the two todos above (observability/confirmation only — does not gate the real
      dispatch). Add a regression test proving a pending entry registered in one `SportsTriggerScheduler` instance is
      picked up and resolved by a FRESH instance reading the same persisted state (simulating the one-shot restart).
      Repo: deployment-service.
